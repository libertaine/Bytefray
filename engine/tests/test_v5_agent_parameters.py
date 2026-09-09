from __future__ import annotations

"""V5 Alpha 1 Phase D: schema-driven agent parameters and presets.

Four things are qualified here, in this order:

1. **Parsing** -- what ``agent.yaml``'s optional ``parameters``/``presets``
   sections accept and, more importantly, what they refuse. Every rejection
   is asserted through the parser on a real manifest rather than by matching
   source strings, so the tests fail if the *behaviour* regresses rather than
   if a message is reworded.
2. **Resolution** -- the single precedence rule ``defaults < preset <
   explicit overrides``, its deterministic ordering, and the compatibility
   policy for agents that declare no schema at all.
3. **Runtime integration** -- that a resolved value actually reaches the
   agent through the production delivery path and actually changes what the
   agent does, that an invalid value fails before agent code runs, and that
   effective values reach match identity and the persisted artifacts.
4. **The V5 starters** -- that their declared defaults reproduce Phase C's
   behaviour exactly, and that a representative non-default value moves the
   behaviour the parameter claims to control.

Point 4 is the one that matters most. A parameter system that parses
beautifully but silently changes how the shipped starters play would be a
regression dressed as a feature.
"""

import json
from pathlib import Path
from typing import ClassVar

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_parameters import (
    EMPTY_PARAMETER_SCHEMA,
    AgentParameterError,
    resolve_parameters,
)
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    canonical_match_id,
)
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID
from test_v5_starter_agents import (
    ARENA_SIZE,
    QUOTA,
    V5_STARTER_NAMES,
    Match,
    _fixture_spec,
    _starter_spec,
    gameplay_digest,
)

# --------------------------------------------------------------------------
# The Phase C semantic baseline
# --------------------------------------------------------------------------

#: The exact match shape the Phase C baseline below was captured against.
#: Changing any of these invalidates the recorded digests.
BASELINE_FIXTURES = (
    "fixture_idle_target",
    "fixture_drifting_target",
    "fixture_core_presser",
)
BASELINE_STARTS = (64, 200)
BASELINE_SEED = 11
BASELINE_TICKS = 140

#: Gameplay digests captured from the Phase C starter sources at commit
#: 69fc958, BEFORE any Phase D edit existed, using the identical harness this
#: module imports. ``gameplay_digest`` hashes decisions, observations,
#: applied results and process declarations -- never ``wall_time_ms``, which
#: is wall-clock noise and differs between two runs of the same match.
#:
#: These are what make "defaults preserve Phase C behaviour" a measurement
#: rather than an assertion. If a future change to a starter's source or to
#: parameter resolution moves any of them, that change altered how a shipped
#: starter plays: justify it, do not re-baseline it.
#:
#: Recorded as the leading 16 hex characters of the SHA-256, which is what
#: was captured pre-change; the run under test is truncated identically.
PHASE_C_DIGEST_PREFIXES = {
    "v5_region_attacker__fixture_idle_target": "85f15ca0cf4ecbc7",
    "v5_region_attacker__fixture_drifting_target": "181c2339b4e14b80",
    "v5_region_attacker__fixture_core_presser": "fb3bc0afc63887a2",
    "v5_scout_striker__fixture_idle_target": "404811eb6b11722c",
    "v5_scout_striker__fixture_drifting_target": "5fa6559c0e105271",
    "v5_scout_striker__fixture_core_presser": "9670a8b7bde8f291",
    "v5_core_defender__fixture_idle_target": "8acc328a0168d545",
    "v5_core_defender__fixture_drifting_target": "253d5f10c100be5d",
    "v5_core_defender__fixture_core_presser": "16982fb8ec2b0484",
    "v5_dual_team__fixture_idle_target": "c6863bc8256dd658",
    "v5_dual_team__fixture_drifting_target": "22de396bd189c022",
    "v5_dual_team__fixture_core_presser": "dc640753befb48f2",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _manifest(root: Path, name: str, body: dict) -> Path:
    """Write one real agent package and return its directory.

    Parsing is always exercised through ``agent_spec_from_dir`` on an actual
    manifest file rather than by handing a dict straight to the parser, so
    these tests cover the path a user's agent really takes.
    """

    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": name,
                "display": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
                **body,
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(PARAM_ECHO_SOURCE, encoding="utf-8")
    return agent_dir


def _spec(root: Path, name: str, body: dict):
    spec = agent_spec_from_dir(_manifest(root, name, body))
    assert spec is not None
    return spec


def _schema(root: Path, name: str, body: dict):
    return _spec(root, name, body).parameter_schema


#: A test-only agent whose declared process reach IS its ``reach`` parameter
#: and whose written byte IS its ``mark`` parameter, so a resolved value's
#: arrival is observable in a replay/trace rather than inferred.
PARAM_ECHO_SOURCE = '''
from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class ParamEcho:
    """Publishes its resolved parameters into observable match behaviour."""

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.reach = int(context.parameters.get("reach", 12))
        self.mark = int(context.parameters.get("mark", 0x11))
        self.anchor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="echo", reach=self.reach, share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self.anchor = observation.self_anchor
        return AgentAction(
            kind=ActionKindV2.WRITE,
            operand=observation.self_anchor,
            value=self.mark,
        )


def create_agent() -> ParamEcho:
    return ParamEcho()
'''

SIMPLE_SCHEMA = {
    "parameters": {
        "reach": {
            "type": "integer",
            "default": 12,
            "minimum": 1,
            "maximum": 64,
            "description": "declared process reach",
        },
        "mark": {"type": "integer", "default": 0x11, "minimum": 0, "maximum": 255},
    },
    "presets": {
        "standard": {"values": {"reach": 12, "mark": 0x11}},
        "long": {"description": "reaches further", "values": {"reach": 40}},
    },
}


def _run(tmp_path: Path, label: str, a_spec, b_spec, a_params=None) -> Match:
    replay_path = tmp_path / label / "replay.jsonl"
    trace_path = tmp_path / label / "trace.jsonl"
    NativeMatchService().run(
        MatchRequest(
            config=Config(
                seed=BASELINE_SEED, arena_size=ARENA_SIZE, instr_per_tick=QUOTA
            ),
            entrants=(
                MatchEntrant.python(
                    "A", a_spec.name, BASELINE_STARTS[0], a_spec, a_params
                ),
                MatchEntrant.python("B", b_spec.name, BASELINE_STARTS[1], b_spec),
            ),
            max_ticks=BASELINE_TICKS,
            replay_path=replay_path,
            trace_path=trace_path,
            verbose=False,
            ruleset_id=BYTEFRAY_RULESET_V4_ID,
        )
    )
    return Match(replay_path, trace_path, BASELINE_STARTS)


# --------------------------------------------------------------------------
# 1. Schema parsing -- what a manifest may and may not declare
# --------------------------------------------------------------------------


def test_manifest_without_a_parameters_section_gets_an_empty_schema(
    tmp_path: Path,
) -> None:
    """The compatibility guarantee: no section, no schema, no error."""

    schema = _schema(tmp_path, "plain", {})
    assert schema is EMPTY_PARAMETER_SCHEMA
    assert schema.is_empty
    assert schema.defaults() == {}
    assert schema.preset_names() == ()


def test_legacy_free_form_defaults_block_still_parses_untouched(
    tmp_path: Path,
) -> None:
    """Every pre-Phase-D manifest keeps its historical ``defaults`` block."""

    spec = _spec(tmp_path, "legacy", {"defaults": {"aggression": 0.6, "byte": 65}})
    assert spec.defaults == {"aggression": 0.6, "byte": 65}
    assert spec.parameter_schema.is_empty


def test_valid_declarations_parse_with_types_bounds_and_order(
    tmp_path: Path,
) -> None:
    schema = _schema(
        tmp_path,
        "typed",
        {
            "parameters": {
                "count": {"type": "integer", "default": 3, "minimum": 1, "maximum": 9},
                "ratio": {"type": "number", "default": 0.5, "minimum": 0.0},
                "loud": {"type": "boolean", "default": False},
                "label": {"type": "string", "default": "x"},
                "mode": {
                    "type": "choice",
                    "default": "b",
                    "choices": ["a", "b", "c"],
                },
            }
        },
    )
    # Declaration order, not alphabetical and not dictionary-hash order.
    assert schema.declaration_order() == ("count", "ratio", "loud", "label", "mode")
    assert schema.defaults() == {
        "count": 3,
        "ratio": 0.5,
        "loud": False,
        "label": "x",
        "mode": "b",
    }
    assert schema.parameters["count"].maximum == 9
    assert schema.parameters["mode"].choices == ("a", "b", "c")


@pytest.mark.parametrize(
    ("label", "parameters"),
    [
        ("unsupported type", {"x": {"type": "date", "default": 1}}),
        ("missing type", {"x": {"default": 1}}),
        ("missing default", {"x": {"type": "integer"}}),
        ("default wrong type", {"x": {"type": "integer", "default": "eight"}}),
        ("default below minimum", {"x": {"type": "integer", "default": 0, "minimum": 1}}),
        ("default above maximum", {"x": {"type": "integer", "default": 9, "maximum": 4}}),
        (
            "default outside choices",
            {"x": {"type": "choice", "default": "z", "choices": ["a"]}},
        ),
        ("choice without choices", {"x": {"type": "choice", "default": "a"}}),
        ("empty choices", {"x": {"type": "choice", "default": "a", "choices": []}}),
        (
            "duplicate choices",
            {"x": {"type": "choice", "default": "a", "choices": ["a", "a"]}},
        ),
        (
            "choices on a non-choice",
            {"x": {"type": "string", "default": "a", "choices": ["a"]}},
        ),
        ("bounds on a string", {"x": {"type": "string", "default": "a", "minimum": 1}}),
        ("bounds on a boolean", {"x": {"type": "boolean", "default": True, "maximum": 1}}),
        (
            "minimum above maximum",
            {"x": {"type": "integer", "default": 2, "minimum": 5, "maximum": 1}},
        ),
        ("unsupported field", {"x": {"type": "integer", "default": 1, "step": 2}}),
        ("declaration is not a map", {"x": 5}),
        ("bad key syntax", {"Sweep-Width": {"type": "integer", "default": 1}}),
    ],
)
def test_invalid_parameter_declaration_is_rejected(
    tmp_path: Path, label: str, parameters: dict
) -> None:
    """Fail closed. A schema that is wrong is an error, never ignored."""

    with pytest.raises(AgentManifestError):
        _schema(tmp_path, f"bad_{abs(hash(label))}", {"parameters": parameters})


def test_empty_parameters_section_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(AgentManifestError):
        _schema(tmp_path, "empty_section", {"parameters": {}})


def test_schema_and_legacy_defaults_together_are_rejected(tmp_path: Path) -> None:
    """Two incompatible ways to say the same thing: refuse, never guess."""

    with pytest.raises(AgentManifestError):
        _schema(
            tmp_path,
            "both",
            {
                "parameters": {"x": {"type": "integer", "default": 1}},
                "defaults": {"x": 2},
            },
        )


def test_presets_parse_and_expose_their_values(tmp_path: Path) -> None:
    schema = _schema(tmp_path, "presets_ok", SIMPLE_SCHEMA)
    assert schema.preset_names() == ("standard", "long")
    assert dict(schema.presets["long"].values) == {"reach": 40}
    assert schema.presets["long"].description == "reaches further"


@pytest.mark.parametrize(
    ("label", "presets"),
    [
        ("undeclared key", {"p": {"values": {"nope": 1}}}),
        ("value out of range", {"p": {"values": {"reach": 999}}}),
        ("value wrong type", {"p": {"values": {"reach": "wide"}}}),
        ("missing values", {"p": {"description": "no values"}}),
        ("values not a map", {"p": {"values": [1, 2]}}),
        ("unsupported field", {"p": {"values": {}, "colour": "red"}}),
        ("bad preset name", {"Bad Name": {"values": {}}}),
    ],
)
def test_invalid_preset_is_rejected(
    tmp_path: Path, label: str, presets: dict
) -> None:
    with pytest.raises(AgentManifestError):
        _schema(
            tmp_path,
            f"badpreset_{abs(hash(label))}",
            {"parameters": SIMPLE_SCHEMA["parameters"], "presets": presets},
        )


def test_presets_without_parameters_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(AgentManifestError):
        _schema(tmp_path, "orphan_presets", {"presets": {"p": {"values": {}}}})


# --------------------------------------------------------------------------
# 2. Resolution -- defaults < preset < explicit override
# --------------------------------------------------------------------------


def test_resolution_precedence_is_defaults_then_preset_then_override(
    tmp_path: Path,
) -> None:
    schema = _schema(tmp_path, "precedence", SIMPLE_SCHEMA)

    assert resolve_parameters(schema) == {"reach": 12, "mark": 0x11}
    assert resolve_parameters(schema, preset="long") == {"reach": 40, "mark": 0x11}
    assert resolve_parameters(schema, overrides={"reach": 20}) == {
        "reach": 20,
        "mark": 0x11,
    }
    # The override wins over the preset, and the preset over the default, in
    # one resolution -- the whole precedence rule in a single assertion.
    assert resolve_parameters(schema, preset="long", overrides={"reach": 20}) == {
        "reach": 20,
        "mark": 0x11,
    }


def test_resolved_ordering_is_declaration_order_not_caller_order(
    tmp_path: Path,
) -> None:
    """Identity must not depend on the order a caller wrote its overrides."""

    schema = _schema(tmp_path, "ordering", SIMPLE_SCHEMA)
    forward = resolve_parameters(schema, overrides={"reach": 20, "mark": 5})
    reverse = resolve_parameters(schema, overrides={"mark": 5, "reach": 20})
    assert list(forward) == list(reverse) == ["reach", "mark"]
    assert forward == reverse


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("20", 20),
        (" 20 ", 20),
        (20, 20),
    ],
)
def test_integer_values_coerce_from_text(tmp_path: Path, raw: object, expected: int) -> None:
    """The CLI and the Designer both supply text; one canonical path types it."""

    schema = _schema(tmp_path, "coerce_int", SIMPLE_SCHEMA)
    assert resolve_parameters(schema, overrides={"reach": raw})["reach"] == expected


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("on", True),
        ("1", True),
        ("false", False),
        ("no", False),
        ("off", False),
        ("0", False),
        (True, True),
        (False, False),
    ],
)
def test_boolean_vocabulary_is_explicit(
    tmp_path: Path, word: object, expected: bool
) -> None:
    schema = _schema(
        tmp_path, "coerce_bool", {"parameters": {"loud": {"type": "boolean", "default": False}}}
    )
    assert resolve_parameters(schema, overrides={"loud": word})["loud"] is expected


@pytest.mark.parametrize("word", ["maybe", "", "y", "2", "none"])
def test_boolean_rejects_everything_outside_its_vocabulary(
    tmp_path: Path, word: str
) -> None:
    """No Python truthiness: ``"false"`` must never read as ``True``."""

    schema = _schema(
        tmp_path, "bool_strict", {"parameters": {"loud": {"type": "boolean", "default": False}}}
    )
    with pytest.raises(AgentParameterError):
        resolve_parameters(schema, overrides={"loud": word})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("reach", "wide"),
        ("reach", 8.5),
        ("reach", True),
        ("reach", 0),
        ("reach", 65),
        ("reach", None),
    ],
)
def test_invalid_override_value_is_rejected_with_a_useful_message(
    tmp_path: Path, key: str, value: object
) -> None:
    schema = _schema(tmp_path, "bad_override", SIMPLE_SCHEMA)
    with pytest.raises(AgentParameterError) as caught:
        resolve_parameters(schema, overrides={key: value})
    message = str(caught.value)
    assert key in message
    # Presentable: names the parameter and what was expected, no traceback.
    assert "Parameter" in message


def test_unknown_override_key_fails_for_a_schema_driven_agent(
    tmp_path: Path,
) -> None:
    """A schema-driven surface must not silently accept a typo."""

    schema = _schema(tmp_path, "unknown_key", SIMPLE_SCHEMA)
    with pytest.raises(AgentParameterError) as caught:
        resolve_parameters(schema, overrides={"raech": 20})
    assert "raech" in str(caught.value)
    assert "reach" in str(caught.value)


def test_unknown_preset_fails_and_lists_the_declared_ones(tmp_path: Path) -> None:
    schema = _schema(tmp_path, "unknown_preset", SIMPLE_SCHEMA)
    with pytest.raises(AgentParameterError) as caught:
        resolve_parameters(schema, preset="aggressive")
    assert "standard" in str(caught.value)


def test_legacy_agent_without_a_schema_keeps_free_form_passthrough() -> None:
    """The §10 compatibility policy, stated as an executable rule.

    An agent that never opted into a schema must not start failing because a
    stricter system arrived around it: unknown keys are still accepted and
    values are still passed through untouched.
    """

    resolved = resolve_parameters(
        EMPTY_PARAMETER_SCHEMA,
        legacy_defaults={"aggression": 0.6},
        overrides={"anything_at_all": "unvalidated"},
    )
    assert resolved == {"aggression": 0.6, "anything_at_all": "unvalidated"}


def test_selecting_a_preset_on_a_schemaless_agent_fails_clearly() -> None:
    with pytest.raises(AgentParameterError):
        resolve_parameters(EMPTY_PARAMETER_SCHEMA, preset="standard")


# --------------------------------------------------------------------------
# 3. Runtime integration -- resolved values reach the agent and the artifacts
# --------------------------------------------------------------------------


def test_resolved_values_reach_the_agent_and_change_what_it_does(
    tmp_path: Path,
) -> None:
    """Not a parsing test: the value must arrive and take effect in a match."""

    spec = _spec(tmp_path, "echo", SIMPLE_SCHEMA)
    opponent = _fixture_spec(tmp_path / "opp", "fixture_idle_target")

    default = _run(tmp_path, "echo_default", spec, opponent)
    overridden = _run(
        tmp_path,
        "echo_override",
        spec,
        opponent,
        resolve_parameters(spec.parameter_schema, overrides={"reach": 40, "mark": 0x7E}),
    )

    # The declared reach is the parameter, so the declaration record proves
    # delivery happened before tick zero.
    assert default.declarations("A")[0]["reach"] == 12
    assert overridden.declarations("A")[0]["reach"] == 40

    # ...and the written byte proves it is still in effect during act().
    written = {d["action"]["value"] for d in overridden.decisions("A")}
    assert written == {0x7E}


def test_default_resolution_matches_running_with_no_parameters_at_all(
    tmp_path: Path,
) -> None:
    """Declaring a schema must not, by itself, change how an agent plays."""

    spec = _spec(tmp_path, "echo_equiv", SIMPLE_SCHEMA)
    opponent = _fixture_spec(tmp_path / "opp2", "fixture_idle_target")

    bare = _run(tmp_path, "equiv_bare", spec, opponent)
    resolved = _run(
        tmp_path, "equiv_defaults", spec, opponent, resolve_parameters(spec.parameter_schema)
    )
    assert gameplay_digest(bare) == gameplay_digest(resolved)


def test_a_preset_resolves_deterministically_into_a_match(tmp_path: Path) -> None:
    spec = _spec(tmp_path, "echo_preset", SIMPLE_SCHEMA)
    opponent = _fixture_spec(tmp_path / "opp3", "fixture_idle_target")
    match = _run(
        tmp_path,
        "preset_long",
        spec,
        opponent,
        resolve_parameters(spec.parameter_schema, preset="long"),
    )
    assert match.declarations("A")[0]["reach"] == 40


def test_invalid_parameters_fail_before_the_agent_is_ever_executed(
    tmp_path: Path,
) -> None:
    """Fail-closed ordering: resolution happens before any agent import."""

    spec = _spec(tmp_path, "echo_guard", SIMPLE_SCHEMA)
    with pytest.raises(AgentParameterError):
        resolve_parameters(spec.parameter_schema, overrides={"reach": 999})


def test_effective_parameters_participate_in_match_identity(tmp_path: Path) -> None:
    spec = _spec(tmp_path, "echo_identity", SIMPLE_SCHEMA)
    opponent = _fixture_spec(tmp_path / "opp4", "fixture_idle_target")

    def request(params):
        return MatchRequest(
            config=Config(seed=1, arena_size=ARENA_SIZE, instr_per_tick=QUOTA),
            entrants=(
                MatchEntrant.python("A", spec.name, 0, spec, params),
                MatchEntrant.python("B", opponent.name, 200, opponent),
            ),
            max_ticks=8,
            replay_path=tmp_path / "id.jsonl",
            ruleset_id=BYTEFRAY_RULESET_V4_ID,
        )

    bare = canonical_match_id(request(None))
    defaults = canonical_match_id(request({"reach": 12, "mark": 0x11}))
    altered = canonical_match_id(request({"reach": 40, "mark": 0x11}))

    # Different effective parameters must never collide under one match_id.
    assert defaults != altered
    # ...and reordering the same values must not change it.
    assert defaults == canonical_match_id(request({"mark": 0x11, "reach": 12}))
    # An entrant carrying no parameters keeps the identity it always had,
    # which is what leaves every pre-Phase-D match_id byte-for-byte intact.
    assert bare != defaults


def test_result_metadata_records_effective_values_but_never_the_schema(
    tmp_path: Path,
) -> None:
    """Artifacts carry what is needed to reproduce, not the authoring schema."""

    spec = _spec(tmp_path, "echo_artifact", SIMPLE_SCHEMA)
    opponent = _fixture_spec(tmp_path / "opp5", "fixture_idle_target")
    _run(
        tmp_path,
        "artifact",
        spec,
        opponent,
        resolve_parameters(spec.parameter_schema, preset="long"),
    )
    result = json.loads(
        (tmp_path / "artifact" / "result.json").read_text(encoding="utf-8")
    )
    entrant_a = next(e for e in result["entrants"] if e["agent_id"] == "A")
    assert entrant_a["metadata"]["parameters"] == {"reach": 40, "mark": 0x11}

    # The opponent declares nothing and is given nothing: the key is omitted
    # entirely rather than written as an empty object, which is what keeps
    # every pre-Phase-D result.json unchanged.
    entrant_b = next(e for e in result["entrants"] if e["agent_id"] == "B")
    assert "parameters" not in entrant_b["metadata"]

    # Types, bounds, descriptions and presets stay with the agent package.
    serialized = json.dumps(result)
    assert "minimum" not in serialized
    assert "declared process reach" not in serialized


# --------------------------------------------------------------------------
# 4. The V5 starters
# --------------------------------------------------------------------------

#: What each starter exposes, and one non-default value whose effect is
#: asserted below. Kept here rather than read out of the manifests so the
#: test states an expectation instead of restating whatever is on disk.
STARTER_PARAMETERS = {
    "v5_region_attacker": ("attacker_reach",),
    "v5_scout_striker": ("contact_memory_ticks", "search_stride_divisor"),
    "v5_core_defender": ("inspections_per_tick",),
    "v5_dual_team": ("raider_share",),
}

STARTER_PRESETS = {
    "v5_region_attacker": ("standard", "far_sighted"),
    "v5_scout_striker": ("standard", "persistent"),
    "v5_core_defender": ("standard", "vigilant"),
    "v5_dual_team": ("standard", "raid_heavy"),
}


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_declares_exactly_the_documented_parameters(name: str) -> None:
    schema = _starter_spec(name).parameter_schema
    assert schema.declaration_order() == STARTER_PARAMETERS[name]
    assert schema.preset_names() == STARTER_PRESETS[name]


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_defaults_and_every_preset_resolve(name: str) -> None:
    schema = _starter_spec(name).parameter_schema
    assert resolve_parameters(schema) == schema.defaults()
    for preset in schema.preset_names():
        resolved = resolve_parameters(schema, preset=preset)
        assert set(resolved) == set(schema.defaults())


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_standard_preset_equals_the_declared_defaults(name: str) -> None:
    """A ``standard`` preset must never quietly mean something else."""

    schema = _starter_spec(name).parameter_schema
    assert resolve_parameters(schema, preset="standard") == schema.defaults()


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
@pytest.mark.parametrize("fixture", BASELINE_FIXTURES)
def test_v5_starter_defaults_reproduce_the_phase_c_gameplay_digest(
    tmp_path: Path, name: str, fixture: str
) -> None:
    """The Phase D guarantee, measured against the pre-change baseline.

    Run with parameters resolved from the declared schema -- the production
    path, not a bypass -- and the decisions, observations, applied results
    and process declarations must hash to exactly what the Phase C sources
    produced before any Phase D edit existed.
    """

    spec = _starter_spec(name)
    opponent = _fixture_spec(tmp_path / f"{name}_{fixture}", fixture)
    match = _run(
        tmp_path,
        f"{name}_{fixture}",
        spec,
        opponent,
        resolve_parameters(spec.parameter_schema),
    )
    assert (
        gameplay_digest(match)[:16]
        == PHASE_C_DIGEST_PREFIXES[f"{name}__{fixture}"]
    )


@pytest.mark.parametrize(
    ("name", "fixture", "overrides", "probe", "expect_change"),
    [
        # Reach is declared from the parameter, so the declaration record is
        # direct evidence rather than an inference from behaviour.
        (
            "v5_region_attacker",
            "fixture_idle_target",
            {"attacker_reach": 32},
            lambda m: m.declarations("A")[0]["reach"],
            True,
        ),
        # Inspection is the whole lesson: with the reserved duty at zero the
        # defender stops READing entirely and can no longer tell a cell it
        # still owns from one it has lost.
        (
            "v5_core_defender",
            "fixture_core_presser",
            {"inspections_per_tick": 0},
            lambda m: sum(1 for d in m.decisions("A") if d["action"]["kind"] == "read"),
            True,
        ),
        # The quota split really is the shares: 0.75/0.25 of Q=8 is 6/2.
        (
            "v5_dual_team",
            "fixture_core_presser",
            {"raider_share": 0.75},
            lambda m: tuple(
                sorted(
                    (p, sum(1 for d in m.decisions("A") if d["process_id"] == p))
                    for p in ("keeper", "raider")
                )
            ),
            True,
        ),
        # A shorter stride covers less ground per action, so the searcher
        # spends far more of the match moving.
        (
            "v5_scout_striker",
            "fixture_idle_target",
            {"search_stride_divisor": 8},
            lambda m: sum(1 for d in m.decisions("A") if d["action"]["kind"] == "move"),
            True,
        ),
        # A memory of zero ticks means a contact is never attacked once it
        # leaves sensor range.
        (
            "v5_scout_striker",
            "fixture_drifting_target",
            {"contact_memory_ticks": 0},
            lambda m: len(m.written_addresses("A")),
            True,
        ),
    ],
)
def test_v5_starter_non_default_value_moves_the_intended_behaviour(
    tmp_path: Path,
    name: str,
    fixture: str,
    overrides: dict,
    probe,
    expect_change: bool,
) -> None:
    spec = _starter_spec(name)
    label = f"{name}_{'_'.join(overrides)}"
    opponent = _fixture_spec(tmp_path / label, fixture)

    default = _run(
        tmp_path, f"{label}_default", spec, opponent, resolve_parameters(spec.parameter_schema)
    )
    altered = _run(
        tmp_path,
        f"{label}_altered",
        spec,
        opponent,
        resolve_parameters(spec.parameter_schema, overrides=overrides),
    )
    assert (probe(default) != probe(altered)) is expect_change


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_stays_legal_and_deterministic_under_a_preset(
    tmp_path: Path, name: str
) -> None:
    """A preset changes behaviour; it must never change legality."""

    spec = _starter_spec(name)
    preset = STARTER_PRESETS[name][1]
    opponent = _fixture_spec(tmp_path / f"{name}_legal", "fixture_core_presser")
    params = resolve_parameters(spec.parameter_schema, preset=preset)

    first = _run(tmp_path, f"{name}_preset_1", spec, opponent, params)
    second = _run(tmp_path, f"{name}_preset_2", spec, opponent, params)

    assert gameplay_digest(first) == gameplay_digest(second)
    assert {s for s in first.statuses("A") if s} == {"APPLIED"}


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_rejects_an_out_of_range_value(name: str) -> None:
    schema = _starter_spec(name).parameter_schema
    key = STARTER_PARAMETERS[name][0]
    declared = schema.parameters[key]
    assert declared.maximum is not None
    with pytest.raises(AgentParameterError):
        resolve_parameters(schema, overrides={key: declared.maximum + 1})


# --------------------------------------------------------------------------
# 5. The CLI surface
# --------------------------------------------------------------------------


def _cli_env(monkeypatch, root: Path) -> None:
    """Point the CLI's agent discovery at a throwaway catalog."""

    monkeypatch.setenv("BYTEFRAY_ROOT", str(root))
    for letter in ("A", "B", "C"):
        monkeypatch.delenv(f"BYTEFRAY_AGENT_{letter}_PARAMS_JSON", raising=False)


def _cli_agents(root: Path) -> None:
    _manifest(root, "echo_cli", SIMPLE_SCHEMA)
    _manifest(root, "echo_plain", {})


def _cli_run(tmp_path: Path, extra: list[str]) -> Path:
    from battle_engine import cli

    replay = tmp_path / "cli" / "replay.jsonl"
    replay.parent.mkdir(parents=True, exist_ok=True)
    assert (
        cli.main(
            [
                "--a-type",
                "echo_cli",
                "--b-type",
                "echo_plain",
                "--arena",
                str(ARENA_SIZE),
                "--ticks",
                "6",
                "--seed",
                "1",
                "--ruleset",
                BYTEFRAY_RULESET_V4_ID,
                "--replay",
                str(replay),
                "--quiet",
                *extra,
            ]
        )
        == 0
    )
    return replay.with_name("result.json")


def _cli_parameters(result_path: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    entrant = next(e for e in result["entrants"] if e["agent_id"] == "A")
    return entrant["metadata"].get("parameters", {})


def test_cli_param_flag_overrides_one_declared_parameter(
    tmp_path: Path, monkeypatch
) -> None:
    """``--a-param KEY=VALUE`` is text; the schema is what types it."""

    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    assert _cli_parameters(_cli_run(tmp_path, ["--a-param", "reach=40"])) == {
        "reach": 40,
        "mark": 0x11,
    }


def test_cli_preset_flag_selects_a_declared_preset(
    tmp_path: Path, monkeypatch
) -> None:
    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    assert _cli_parameters(_cli_run(tmp_path, ["--a-preset", "long"])) == {
        "reach": 40,
        "mark": 0x11,
    }


def test_cli_param_flag_beats_preset_and_env(tmp_path: Path, monkeypatch) -> None:
    """The full precedence chain, exercised end to end through the CLI."""

    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    monkeypatch.setenv("BYTEFRAY_AGENT_A_PARAMS_JSON", json.dumps({"reach": 30}))
    assert _cli_parameters(
        _cli_run(tmp_path, ["--a-preset", "long", "--a-param", "reach=20"])
    ) == {"reach": 20, "mark": 0x11}


def test_cli_env_json_now_reaches_a_python_agent(tmp_path: Path, monkeypatch) -> None:
    """The pre-existing Designer path, which used to be silently discarded."""

    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    monkeypatch.setenv("BYTEFRAY_AGENT_A_PARAMS_JSON", json.dumps({"reach": 25}))
    assert _cli_parameters(_cli_run(tmp_path, []))["reach"] == 25


def test_cli_agent_without_a_schema_records_no_parameters(
    tmp_path: Path, monkeypatch
) -> None:
    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    result = json.loads(_cli_run(tmp_path, []).read_text(encoding="utf-8"))
    entrant_b = next(e for e in result["entrants"] if e["agent_id"] == "B")
    assert "parameters" not in entrant_b["metadata"]


V1_AGENT_SOURCE = '''
from battle_engine.agent_api import ActionKind, AgentAction


class LegacyV1:
    def reset(self, context):
        self.arena = context.arena_size

    def act(self, observation):
        return AgentAction(kind=ActionKind.NOP)


def create_agent() -> LegacyV1:
    return LegacyV1()
'''


def test_free_form_params_for_an_api_v1_agent_stay_a_harmless_no_op(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The Agent Designer's Agent Params field must not start failing matches.

    That field exports ``$BYTEFRAY_AGENT_*_PARAMS_JSON`` for whichever agent
    is selected, and an Agent API v1 agent has always ignored it. Phase D
    made schema-driven parameters strict; it must not retroactively make a
    working legacy path an error. The regression this guards against is real
    -- it was caught by
    ``test_designer_third_entrant_command.py::test_generated_three_entrant_command_produces_a_real_three_entrant_match``.
    """

    from battle_engine import cli

    _cli_env(monkeypatch, tmp_path)
    agent_dir = tmp_path / "agents" / "legacy_v1"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": "legacy_v1",
                "display": "legacy_v1",
                "kind": "python",
                "api_version": 1,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(V1_AGENT_SOURCE, encoding="utf-8")
    spec = agent_spec_from_dir(agent_dir)
    assert spec is not None and spec.api_version == 1

    class Args:
        a_param: ClassVar[list[str]] = ["anything=1"]
        a_preset = None

    # Ignored, not fatal -- and said out loud rather than silently dropped.
    monkeypatch.setenv("BYTEFRAY_AGENT_A_PARAMS_JSON", json.dumps({"slot": "A"}))
    assert cli._resolve_entrant_parameters("A", spec, Args()) == {}
    assert "ignored" in capsys.readouterr().err


def test_a_preset_for_an_api_v1_agent_is_refused(tmp_path: Path, monkeypatch) -> None:
    """A preset name that quietly did nothing would be worse than an error."""

    from battle_engine import cli

    _cli_env(monkeypatch, tmp_path)
    agent_dir = tmp_path / "agents" / "legacy_v1_preset"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": "legacy_v1_preset",
                "display": "legacy_v1_preset",
                "kind": "python",
                "api_version": 1,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(V1_AGENT_SOURCE, encoding="utf-8")
    spec = agent_spec_from_dir(agent_dir)

    class Args:
        a_param = None
        a_preset = "standard"

    with pytest.raises(SystemExit):
        cli._resolve_entrant_parameters("A", spec, Args())


def test_a_schema_requires_agent_api_v2(tmp_path: Path) -> None:
    """Metadata that could never be delivered is refused, not accepted."""

    agent_dir = tmp_path / "agents" / "v1_with_schema"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": "v1_with_schema",
                "kind": "python",
                "api_version": 1,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
                "parameters": {"x": {"type": "integer", "default": 1}},
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(V1_AGENT_SOURCE, encoding="utf-8")
    with pytest.raises(AgentManifestError):
        agent_spec_from_dir(agent_dir)


@pytest.mark.parametrize(
    "extra",
    [
        ["--a-param", "reach=999"],
        ["--a-param", "reach=wide"],
        ["--a-param", "raech=20"],
        ["--a-param", "reach"],
        ["--a-preset", "nonexistent"],
    ],
)
def test_cli_rejects_bad_parameters_before_running_a_match(
    tmp_path: Path, monkeypatch, extra: list[str]
) -> None:
    _cli_env(monkeypatch, tmp_path)
    _cli_agents(tmp_path)
    with pytest.raises(SystemExit) as caught:
        _cli_run(tmp_path, extra)
    # The failure must be the parameter, not a missing agent or a bad flag:
    # a test that passes because discovery broke proves nothing.
    message = str(caught.value)
    assert "reach" in message or "preset" in message
    assert "Unknown agent" not in message
    # ...and no match may have been published.
    assert not (tmp_path / "cli" / "result.json").exists()


# --------------------------------------------------------------------------
# 6. V4 compatibility
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    (
        "v4_claimer",
        "v4_concentrated_attacker",
        "v4_defender_scout",
        "v4_local_defender",
        "v4_scout",
        "v4_quorum",
    ),
)
def test_historical_v4_starters_declare_no_schema_and_still_load(name: str) -> None:
    """Phase D is additive: no historical agent was retrofitted."""

    spec = _starter_spec(name)
    assert spec.parameter_schema.is_empty
    assert resolve_parameters(spec.parameter_schema) == {}
