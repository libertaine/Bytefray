"""Schema-driven agent parameters: declaration, validation, and resolution.

One canonical model for the three concepts V5 Alpha 1 Phase D separates
deliberately (docs/research/v5/V5_ALPHA1_PHASE_D_AUTHORING_AND_PARAMETERS.md):

* **declaration** -- what an agent author says is configurable, written in
  ``agent.yaml``'s optional ``parameters``/``presets`` sections and parsed
  here into :class:`AgentParameterSchema`;
* **resolution** -- how one concrete value per parameter is obtained, by the
  single precedence rule ``schema defaults < selected preset < explicit
  overrides`` implemented once in :func:`resolve_parameters`; and
* **delivery** -- how resolved values reach the agent, which is *not* this
  module's job. Delivery reuses the existing per-match path: the resolved
  mapping travels on ``MatchEntrant.parameters`` and is handed to an Agent
  API v2 agent as ``MatchContextV2.parameters`` at ``reset()``.

The schema describes and validates configuration. It is deliberately not a
second gameplay communication channel: nothing here reads arena state, and a
resolved value is an ordinary immutable scalar the agent may consult.

Everything is optional and additive. An agent that declares no ``parameters``
section behaves exactly as it did before Phase D -- see
:func:`resolve_parameters`'s legacy branch, which preserves the historical
free-form passthrough rather than imposing the new strictness on manifests
written before the schema existed.

This is not a general JSON Schema implementation and must not grow into one.
There are no nested objects, no arrays, no conditional schemas, and no
expression language: five scalar types with type-appropriate constraints,
which is what Bytefray agents actually need.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from battle_engine.agent_api import AgentManifestError, AgentValidationError

__all__ = [
    "BOOLEAN_FALSE_WORDS",
    "BOOLEAN_TRUE_WORDS",
    "EMPTY_PARAMETER_SCHEMA",
    "MANIFEST_PARAMETERS_KEY",
    "MANIFEST_PRESETS_KEY",
    "PARAMETER_KEY_SYNTAX",
    "PARAMETER_TYPES",
    "AgentParameterError",
    "AgentParameterSchema",
    "ParameterDeclaration",
    "ParameterPreset",
    "ParameterValue",
    "parse_parameter_schema",
    "resolve_parameters",
]

#: Every value a declared parameter may resolve to. Scalars only -- a
#: parameter is a knob on an agent, not a payload channel into one.
ParameterValue = bool | int | float | str

#: The manifest sections this module owns. Both are optional.
MANIFEST_PARAMETERS_KEY = "parameters"
MANIFEST_PRESETS_KEY = "presets"

#: The supported declared types, derived from what Bytefray agents actually
#: configure: cell counts and cadences (``integer``), process shares
#: (``number``), on/off behaviour switches (``boolean``), free text such as a
#: path (``string``), and a fixed menu of named behaviours (``choice``).
PARAMETER_TYPES: tuple[str, ...] = (
    "integer",
    "number",
    "boolean",
    "string",
    "choice",
)

_NUMERIC_TYPES = frozenset({"integer", "number"})

#: Parameter keys and preset names share one lowercase snake_case syntax, so
#: a manifest cannot declare ``sweepWidth`` and ``sweep_width`` as two
#: separately-spelled knobs a reader would take for the same one.
PARAMETER_KEY_SYNTAX = (
    "lowercase letter followed by lowercase letters, digits or underscores"
)
_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

#: The explicit boolean vocabulary. A string outside these two sets is an
#: error rather than a truthiness test: ``"false"`` is a non-empty Python
#: string, and silently reading it as ``True`` is exactly the surprising
#: coercion this vocabulary exists to prevent.
BOOLEAN_TRUE_WORDS = frozenset({"true", "yes", "on", "1"})
BOOLEAN_FALSE_WORDS = frozenset({"false", "no", "off", "0"})

_DECLARATION_FIELDS = frozenset(
    {"type", "default", "description", "minimum", "maximum", "choices"}
)
_PRESET_FIELDS = frozenset({"description", "values"})


class AgentParameterError(AgentValidationError):
    """A parameter value could not be resolved for this match.

    Distinct from :class:`~battle_engine.agent_api.AgentManifestError`, which
    this module raises for a malformed *declaration*: a manifest error is the
    agent author's to fix, an ``AgentParameterError`` is the person running
    the match. Both inherit ``AgentValidationError``, so both already reach
    CLI and GUI surfaces as an ordinary presentable diagnostic rather than a
    Python traceback.
    """

    code = "agent_parameters_invalid"


def _quote(values: object) -> str:
    if isinstance(values, (list, tuple, frozenset, set)):
        return ", ".join(repr(value) for value in sorted(values, key=str))
    return repr(values)


def _type_name(value: object) -> str:
    return type(value).__name__


@dataclass(frozen=True)
class ParameterDeclaration:
    """One configurable knob an agent author has declared.

    ``minimum``/``maximum`` are populated only for ``integer``/``number`` and
    ``choices`` only for ``choice``; :func:`parse_parameter_schema` rejects a
    declaration that mixes them, so a reader never has to wonder whether a
    ``maximum`` on a ``string`` meant a length limit.
    """

    key: str
    type: str
    default: ParameterValue
    description: str | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    choices: tuple[str, ...] | None = None

    def describe_domain(self) -> str:
        """A short, user-presentable statement of what this accepts."""

        if self.type == "choice":
            return f"one of {_quote(list(self.choices or ()))}"
        if self.type == "boolean":
            return (
                f"a boolean ({_quote(BOOLEAN_TRUE_WORDS)} for true, "
                f"{_quote(BOOLEAN_FALSE_WORDS)} for false)"
            )
        if self.type in _NUMERIC_TYPES:
            bounds = []
            if self.minimum is not None:
                bounds.append(f">= {self.minimum}")
            if self.maximum is not None:
                bounds.append(f"<= {self.maximum}")
            suffix = f" ({', '.join(bounds)})" if bounds else ""
            noun = "an integer" if self.type == "integer" else "a number"
            return f"{noun}{suffix}"
        return "a string"

    def coerce(
        self, value: Any, *, origin: str, path: Path | None = None
    ) -> ParameterValue:
        """Convert one supplied value to this parameter's declared type.

        The single coercion path every surface shares. The CLI and the
        Designer both hand parameters over as text, so accepting ``"8"`` for
        an ``integer`` is a product requirement rather than a convenience --
        but only for values that genuinely denote one, which is why every
        rejection below names what was expected instead of guessing.
        """

        error = _parameter_error_factory(self.key, origin, path)
        coerced = self._convert(value, error)
        self._check_bounds(coerced, error)
        return coerced

    # -- conversion ------------------------------------------------------

    def _convert(self, value: Any, error: _ErrorFactory) -> ParameterValue:
        if self.type == "integer":
            return self._to_integer(value, error)
        if self.type == "number":
            return self._to_number(value, error)
        if self.type == "boolean":
            return self._to_boolean(value, error)
        if self.type == "choice":
            return self._to_choice(value, error)
        return self._to_string(value, error)

    def _to_integer(self, value: Any, error: _ErrorFactory) -> int:
        # ``bool`` is a Python ``int`` subclass; accepting ``True`` as ``1``
        # here would let ``verbose: true`` silently satisfy a cell count.
        if isinstance(value, bool):
            raise error(f"expected an integer, got the boolean {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value.strip(), 10)
            except ValueError:
                raise error(f"expected an integer, got {value!r}") from None
        # A float is refused even when integral: ``8.0`` for a cell count is
        # more likely a units mistake than an intent to write ``8``.
        raise error(f"expected an integer, got {_type_name(value)} {value!r}")

    def _to_number(self, value: Any, error: _ErrorFactory) -> float:
        if isinstance(value, bool):
            raise error(f"expected a number, got the boolean {value!r}")
        if isinstance(value, (int, float)):
            number = float(value)
        elif isinstance(value, str):
            try:
                number = float(value.strip())
            except ValueError:
                raise error(f"expected a number, got {value!r}") from None
        else:
            raise error(f"expected a number, got {_type_name(value)} {value!r}")
        if not math.isfinite(number):
            raise error(f"expected a finite number, got {value!r}")
        return number

    def _to_boolean(self, value: Any, error: _ErrorFactory) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            word = value.strip().lower()
            if word in BOOLEAN_TRUE_WORDS:
                return True
            if word in BOOLEAN_FALSE_WORDS:
                return False
            raise error(f"expected {self.describe_domain()}, got {value!r}")
        # Notably including ``int``: ``1``/``0`` are accepted as the *words*
        # ``"1"``/``"0"`` from a text surface, but a bare integer written in
        # a manifest is an author mistake worth reporting.
        raise error(f"expected a boolean, got {_type_name(value)} {value!r}")

    def _to_choice(self, value: Any, error: _ErrorFactory) -> str:
        if not isinstance(value, str):
            raise error(
                f"expected {self.describe_domain()}, got {_type_name(value)} {value!r}"
            )
        if value not in (self.choices or ()):
            raise error(f"expected {self.describe_domain()}, got {value!r}")
        return value

    def _to_string(self, value: Any, error: _ErrorFactory) -> str:
        if not isinstance(value, str):
            raise error(f"expected a string, got {_type_name(value)} {value!r}")
        return value

    def _check_bounds(self, value: ParameterValue, error: _ErrorFactory) -> None:
        if self.type not in _NUMERIC_TYPES or isinstance(value, (bool, str)):
            return
        if self.minimum is not None and value < self.minimum:
            raise error(f"{value} is below the declared minimum {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise error(f"{value} is above the declared maximum {self.maximum}")


@dataclass(frozen=True)
class ParameterPreset:
    """A named, schema-validated set of parameter values.

    Data only: a preset never contains code, never edits a source file, and
    may only mention parameters the same manifest declares.
    """

    name: str
    values: Mapping[str, ParameterValue]
    description: str | None = None


@dataclass(frozen=True)
class AgentParameterSchema:
    """Everything one agent declares about its configurable parameters.

    The programmatic surface Phase E's Designer consumes: it answers what
    parameters exist, in what order the author declared them, what type and
    default each has, what values are legal, what presets exist, and -- via
    :meth:`resolve` -- what one concrete configuration comes out the far end.
    """

    parameters: Mapping[str, ParameterDeclaration]
    presets: Mapping[str, ParameterPreset]

    @property
    def is_empty(self) -> bool:
        """True for an agent that declares no parameters at all."""

        return not self.parameters

    def declaration_order(self) -> tuple[str, ...]:
        """Parameter keys in the order the manifest declared them.

        Declaration order, not dictionary iteration order, is what every
        resolved mapping and every generated control is ordered by, so a
        Designer form and a printed summary always agree with the manifest.
        """

        return tuple(self.parameters)

    def defaults(self) -> dict[str, ParameterValue]:
        """The declared default for every parameter, in declaration order."""

        return {key: declared.default for key, declared in self.parameters.items()}

    def preset_names(self) -> tuple[str, ...]:
        """Declared preset names, in manifest order."""

        return tuple(self.presets)

    def resolve(
        self,
        *,
        preset: str | None = None,
        overrides: Mapping[str, Any] | None = None,
        path: Path | None = None,
    ) -> dict[str, ParameterValue]:
        """Apply ``defaults < preset < overrides`` and validate the result.

        The returned mapping always contains exactly the declared parameters,
        in declaration order, whatever order the caller's ``overrides`` were
        written in -- so two callers supplying the same values can never
        produce two different resolved mappings, and match identity cannot
        depend on a dictionary's iteration order.
        """

        resolved = self.defaults()

        if preset is not None:
            selected = self.presets.get(preset)
            if selected is None:
                known = _quote(list(self.presets)) if self.presets else "none declared"
                raise AgentParameterError(
                    f"Unknown parameter preset {preset!r}. Declared presets: {known}.",
                    path=path,
                )
            resolved.update(selected.values)

        for raw_key, value in (overrides or {}).items():
            key = str(raw_key)
            declared = self.parameters.get(key)
            if declared is None:
                raise AgentParameterError(
                    f"Unknown parameter {key!r}. This agent declares: "
                    f"{_quote(list(self.parameters))}.",
                    path=path,
                )
            resolved[declared.key] = declared.coerce(
                value, origin="override", path=path
            )

        # Declaration order, re-imposed after the overlays above.
        return {key: resolved[key] for key in self.parameters}


#: The schema every manifest without a ``parameters`` section resolves to.
EMPTY_PARAMETER_SCHEMA = AgentParameterSchema(
    parameters=MappingProxyType({}), presets=MappingProxyType({})
)

_ErrorFactory = Callable[[str], AgentValidationError]


def _parameter_error_factory(
    key: str, origin: str, path: Path | None
) -> _ErrorFactory:
    def build(detail: str) -> AgentValidationError:
        return AgentParameterError(f"Parameter {key!r} ({origin}): {detail}.", path=path)

    return build


def _manifest_error_factory(path: Path | None) -> _ErrorFactory:
    def build(detail: str) -> AgentValidationError:
        return AgentManifestError(detail, path=path)

    return build


def _require_mapping(value: Any, label: str, error: _ErrorFactory) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error(f"{label} must be an object/map, got {_type_name(value)}.")
    for key in value:
        if not isinstance(key, str):
            raise error(f"{label} has a non-string key {key!r}.")
    return value


def _require_key_syntax(name: str, label: str, error: _ErrorFactory) -> None:
    if not _KEY_PATTERN.match(name):
        raise error(
            f"{label} name {name!r} is invalid: expected a {PARAMETER_KEY_SYNTAX}."
        )


def _parse_bound(
    raw: Any, field: str, key: str, error: _ErrorFactory
) -> int | float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise error(
            f"Parameter {key!r}: '{field}' must be a number, got "
            f"{_type_name(raw)} {raw!r}."
        )
    if not math.isfinite(float(raw)):
        raise error(f"Parameter {key!r}: '{field}' must be finite, got {raw!r}.")
    return raw


def _parse_choices(raw: Any, key: str, error: _ErrorFactory) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise error(
            f"Parameter {key!r}: 'choices' must be a non-empty list of strings."
        )
    choices: list[str] = []
    for choice in raw:
        if not isinstance(choice, str) or not choice:
            raise error(
                f"Parameter {key!r}: every entry of 'choices' must be a non-empty "
                f"string, got {_type_name(choice)} {choice!r}."
            )
        if choice in choices:
            raise error(f"Parameter {key!r}: 'choices' repeats {choice!r}.")
        choices.append(choice)
    return tuple(choices)


def _parse_declaration(
    key: str, raw: Any, error: _ErrorFactory
) -> ParameterDeclaration:
    body = _require_mapping(raw, f"Parameter {key!r}", error)

    unknown = sorted(set(body) - _DECLARATION_FIELDS)
    if unknown:
        raise error(
            f"Parameter {key!r} has unsupported field(s) {_quote(unknown)}. "
            f"Supported: {_quote(sorted(_DECLARATION_FIELDS))}."
        )

    declared_type = body.get("type")
    if declared_type not in PARAMETER_TYPES:
        raise error(
            f"Parameter {key!r}: 'type' must be one of "
            f"{_quote(list(PARAMETER_TYPES))}, got {declared_type!r}."
        )

    description = body.get("description")
    if description is not None and not isinstance(description, str):
        raise error(
            f"Parameter {key!r}: 'description' must be a string, got "
            f"{_type_name(description)}."
        )

    minimum: int | float | None = None
    maximum: int | float | None = None
    choices: tuple[str, ...] | None = None

    if declared_type in _NUMERIC_TYPES:
        if "choices" in body:
            raise error(
                f"Parameter {key!r}: 'choices' is only valid for a 'choice' "
                f"parameter, not {declared_type!r}."
            )
        if "minimum" in body:
            minimum = _parse_bound(body["minimum"], "minimum", key, error)
        if "maximum" in body:
            maximum = _parse_bound(body["maximum"], "maximum", key, error)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise error(
                f"Parameter {key!r}: 'minimum' {minimum} is greater than "
                f"'maximum' {maximum}."
            )
    else:
        for field in ("minimum", "maximum"):
            if field in body:
                raise error(
                    f"Parameter {key!r}: '{field}' is only valid for an 'integer' "
                    f"or 'number' parameter, not {declared_type!r}."
                )
        if declared_type == "choice":
            if "choices" not in body:
                raise error(
                    f"Parameter {key!r}: a 'choice' parameter requires 'choices'."
                )
            choices = _parse_choices(body["choices"], key, error)
        elif "choices" in body:
            raise error(
                f"Parameter {key!r}: 'choices' is only valid for a 'choice' "
                f"parameter, not {declared_type!r}."
            )

    if "default" not in body:
        raise error(f"Parameter {key!r}: 'default' is required.")

    # Built with a placeholder default first, so the declared constraints
    # validate the real default through the very same coercion path a user
    # override takes. A default its own schema would reject is an author
    # error caught here, not a match that fails only once somebody overrides.
    skeleton = ParameterDeclaration(
        key=key,
        type=declared_type,
        default=0 if declared_type in _NUMERIC_TYPES else "",
        description=description,
        minimum=minimum,
        maximum=maximum,
        choices=choices,
    )
    try:
        default = skeleton.coerce(body["default"], origin="declared default")
    except AgentParameterError as exc:
        raise error(str(exc)) from exc

    return ParameterDeclaration(
        key=key,
        type=declared_type,
        default=default,
        description=description,
        minimum=minimum,
        maximum=maximum,
        choices=choices,
    )


def _parse_preset(
    name: str,
    raw: Any,
    declarations: Mapping[str, ParameterDeclaration],
    error: _ErrorFactory,
) -> ParameterPreset:
    body = _require_mapping(raw, f"Preset {name!r}", error)

    unknown = sorted(set(body) - _PRESET_FIELDS)
    if unknown:
        raise error(
            f"Preset {name!r} has unsupported field(s) {_quote(unknown)}. "
            f"Supported: {_quote(sorted(_PRESET_FIELDS))}."
        )

    description = body.get("description")
    if description is not None and not isinstance(description, str):
        raise error(
            f"Preset {name!r}: 'description' must be a string, got "
            f"{_type_name(description)}."
        )

    if "values" not in body:
        raise error(f"Preset {name!r}: 'values' is required.")
    raw_values = _require_mapping(body["values"], f"Preset {name!r}: 'values'", error)

    values: dict[str, ParameterValue] = {}
    for key, value in raw_values.items():
        declared = declarations.get(key)
        if declared is None:
            raise error(
                f"Preset {name!r} sets undeclared parameter {key!r}. This agent "
                f"declares: {_quote(list(declarations))}."
            )
        try:
            values[key] = declared.coerce(value, origin=f"preset {name!r}")
        except AgentParameterError as exc:
            # A preset lives in the manifest, so a bad preset value is an
            # authoring defect and is reported as one.
            raise error(str(exc)) from exc

    return ParameterPreset(
        name=name,
        values=MappingProxyType(
            {key: values[key] for key in declarations if key in values}
        ),
        description=description,
    )


def parse_parameter_schema(
    manifest: Mapping[str, Any], *, path: Path | None = None
) -> AgentParameterSchema:
    """Parse one manifest's optional ``parameters``/``presets`` sections.

    Returns :data:`EMPTY_PARAMETER_SCHEMA` for a manifest that declares
    neither, which is what every agent written before Phase D does. Fails
    closed on anything malformed: a manifest that *tries* to declare a schema
    and gets it wrong is an error, never a silently-ignored section.
    """

    error = _manifest_error_factory(path)

    raw_parameters = manifest.get(MANIFEST_PARAMETERS_KEY)
    raw_presets = manifest.get(MANIFEST_PRESETS_KEY)

    if raw_parameters is None:
        if raw_presets is not None:
            raise error(
                f"'{MANIFEST_PRESETS_KEY}' requires a "
                f"'{MANIFEST_PARAMETERS_KEY}' section: a preset may only set "
                f"declared parameters."
            )
        return EMPTY_PARAMETER_SCHEMA

    parameters_body = _require_mapping(
        raw_parameters, f"'{MANIFEST_PARAMETERS_KEY}'", error
    )
    if not parameters_body:
        raise error(
            f"'{MANIFEST_PARAMETERS_KEY}' is present but declares no parameters. "
            f"Omit the section entirely for an agent that takes none."
        )

    # Resolved parameters are delivered as `MatchContextV2.parameters`, which
    # only an Agent API v2 agent receives. Declaring a schema anywhere else
    # would be metadata that silently never arrives, so it is refused rather
    # than accepted and ignored. A VM/blob agent keeps its historical
    # free-form `defaults` + kwargs path, untouched by Phase D.
    api_version = manifest.get("api_version")
    if api_version != 2:
        raise error(
            f"'{MANIFEST_PARAMETERS_KEY}' requires 'api_version: 2'. Resolved "
            f"parameters are delivered through MatchContextV2, which an agent "
            f"declaring api_version {api_version!r} never receives."
        )

    # A schema and the legacy free-form 'defaults' block describe the same
    # thing two incompatible ways. Rather than silently pick a winner, refuse
    # the manifest and make the author choose.
    legacy_defaults = manifest.get("defaults")
    if isinstance(legacy_defaults, Mapping) and legacy_defaults:
        raise error(
            f"A manifest may not declare both '{MANIFEST_PARAMETERS_KEY}' and a "
            f"non-empty legacy 'defaults' block. Move those values into "
            f"'{MANIFEST_PARAMETERS_KEY}' defaults."
        )

    declarations: dict[str, ParameterDeclaration] = {}
    for key, raw in parameters_body.items():
        _require_key_syntax(key, "Parameter", error)
        declarations[key] = _parse_declaration(key, raw, error)

    presets: dict[str, ParameterPreset] = {}
    if raw_presets is not None:
        presets_body = _require_mapping(raw_presets, f"'{MANIFEST_PRESETS_KEY}'", error)
        for name, raw in presets_body.items():
            _require_key_syntax(name, "Preset", error)
            presets[name] = _parse_preset(name, raw, declarations, error)

    return AgentParameterSchema(
        parameters=MappingProxyType(declarations),
        presets=MappingProxyType(presets),
    )


def resolve_parameters(
    schema: AgentParameterSchema,
    *,
    legacy_defaults: Mapping[str, Any] | None = None,
    preset: str | None = None,
    overrides: Mapping[str, Any] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """The one canonical resolver every Bytefray surface calls.

    ``schema defaults < selected preset < explicit overrides``, then
    validate. CLI, Designer, tests and the match runtime all route through
    here so that no surface can grow a second, subtly different notion of
    what a parameter override means.

    **Compatibility.** When ``schema`` is empty -- every manifest written
    before Phase D -- resolution falls back to the historical behaviour:
    ``legacy_defaults`` overlaid with ``overrides``, unvalidated, unknown
    keys allowed. That is deliberate. A schema-driven surface must not accept
    a misspelled parameter name, but an agent that never opted into a schema
    must not start failing because a stricter system arrived around it.
    """

    if schema.is_empty:
        if preset is not None:
            raise AgentParameterError(
                f"Cannot select preset {preset!r}: this agent declares no "
                f"'{MANIFEST_PARAMETERS_KEY}' section, so it has no presets.",
                path=path,
            )
        merged: dict[str, Any] = dict(legacy_defaults or {})
        merged.update(overrides or {})
        return merged

    return dict(schema.resolve(preset=preset, overrides=overrides, path=path))
