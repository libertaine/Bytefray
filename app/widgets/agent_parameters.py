"""Typed Agent Designer controls generated from an agent's parameter schema.

V5 Alpha 1 Phase E1. Phase D defined the contract -- optional ``parameters``
and ``presets`` sections in ``agent.yaml``, one canonical resolver, and a
programmatic surface (``AgentParameterSchema``) that answers what an agent
exposes. This widget makes that contract discoverable: it renders one control
per declared parameter, typed to the declaration, bounded by the declaration,
described by the declaration.

Three rules shape everything here.

**The schema is authoritative, and this module never second-guesses it.**
Values are resolved by ``agent_parameters.resolve_parameters`` through
``app.services.designer_workflows``; there is no coercion, no bounds check and
no precedence rule implemented locally. A control's range comes from the
declaration, so an invalid value is normally unreachable rather than merely
rejected -- but the resolver still runs before every launch, because a
declared domain can be wider than a Qt control can represent and "prevented"
is not the same as "proved".

**Manifest inspection only.** Discovering what an agent exposes reads its
parsed manifest and nothing else. No agent code is imported, executed or
evaluated to populate a control; the Designer's UI/runtime isolation is
unchanged.

**Legacy agents keep their own surface.** An agent that declares no schema is
not forced through one -- ``AdvancedPanel`` shows it the pre-existing
free-form JSON editor instead, and this widget reports ``has_schema() ==
False`` so the caller can make that choice.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from battle_engine.agent_api import AgentValidationError
from battle_engine.agent_parameters import (
    EMPTY_PARAMETER_SCHEMA,
    AgentParameterSchema,
    ParameterDeclaration,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.services.designer_workflows import (
    describe_effective_parameters,
    parameter_launch_overrides,
    resolve_agent_parameters,
)

# The preset selector's first entry: not a declared preset, but the agent's
# own declared defaults. Named rather than blank so the combo always states
# what the current values came from.
DEFAULTS_CHOICE = "Agent defaults"

# Qt's integer spin boxes are 32-bit. A schema may legally declare a wider
# integer domain; when it does the control is clamped to what it can show and
# the canonical resolver rejects the shortfall at launch with its own message,
# rather than this widget silently pretending the value is in range.
_SPINBOX_MIN = -2_147_483_648
_SPINBOX_MAX = 2_147_483_647

# Enough decimals for the process shares and fractions Bytefray agents
# actually declare, without introducing rounding a user would notice. A
# ``number`` parameter is a float; six decimals represents every default and
# preset the shipped starters use exactly.
_NUMBER_DECIMALS = 6
_NUMBER_LIMIT = 1e12


def _clamp_int(value: float | None, fallback: int) -> int:
    """One declared integer bound, expressed within Qt's 32-bit spin range."""

    if value is None:
        return fallback
    return max(_SPINBOX_MIN, min(_SPINBOX_MAX, int(value)))


class AgentParameterForm(QGroupBox):
    """One entrant slot's parameter controls, generated from its schema.

    Emits :attr:`changed` whenever the effective values change, from either a
    preset selection, a reset, or a direct edit -- the caller uses it to keep
    a launch button's enabled state and any summary in step.
    """

    changed = Signal()

    def __init__(self, title: str) -> None:
        super().__init__(title)
        self._schema: AgentParameterSchema = EMPTY_PARAMETER_SCHEMA
        self._agent_id: str | None = None
        self._controls: dict[str, QWidget] = {}
        self._updating = False

        root = QVBoxLayout(self)

        self._presetRow = QWidget()
        preset_layout = QHBoxLayout(self._presetRow)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        self._presetLabel = QLabel("Preset")
        preset_layout.addWidget(self._presetLabel)
        self.presets = QComboBox()
        self.presets.setToolTip(
            "A named set of values the agent's author declared. Selecting one "
            "loads its values into the controls below; you can then edit any "
            "of them. Resolution is always defaults, then preset, then your "
            "own edits."
        )
        preset_layout.addWidget(self.presets, 1)
        self.btnReset = QPushButton("Reset to Defaults")
        self.btnReset.setToolTip(
            "Restore every control to the value this agent's manifest declares "
            "as its default."
        )
        preset_layout.addWidget(self.btnReset)
        root.addWidget(self._presetRow)

        self._fields = QWidget()
        self._form = QFormLayout(self._fields)
        self._form.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._fields)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.presets.currentIndexChanged.connect(self._on_preset_selected)
        self.btnReset.clicked.connect(self.reset_to_defaults)

        self.set_agent(None, EMPTY_PARAMETER_SCHEMA)

    # -- public API ------------------------------------------------------

    @property
    def agent_id(self) -> str | None:
        """The agent these controls were generated for, if any."""

        return self._agent_id

    @property
    def schema(self) -> AgentParameterSchema:
        """The schema these controls were generated from."""

        return self._schema

    def has_schema(self) -> bool:
        """Whether this slot's agent declares any parameters at all."""

        return not self._schema.is_empty

    def set_agent(self, agent_id: str | None, schema: AgentParameterSchema) -> None:
        """Rebuild the controls for a newly selected agent.

        Always rebuilt rather than reused: two agents' parameters share
        nothing, and carrying a previous agent's value into a same-named
        control of a different agent is exactly the kind of invisible state
        this form exists to remove.
        """

        self._schema = schema
        self._agent_id = agent_id
        self._clear_controls()

        self._updating = True
        self.presets.clear()
        self.presets.addItem(DEFAULTS_CHOICE, None)
        for name in schema.preset_names():
            preset = schema.presets[name]
            self.presets.addItem(name, name)
            if preset.description:
                self.presets.setItemData(
                    self.presets.count() - 1,
                    preset.description,
                    Qt.ItemDataRole.ToolTipRole,
                )
        # Reset stays available for any schema agent; only the preset selector
        # itself disappears for an agent whose author declared no presets.
        self._presetRow.setVisible(not schema.is_empty)
        has_presets = bool(schema.preset_names())
        self._presetLabel.setVisible(has_presets)
        self.presets.setVisible(has_presets)

        for key in schema.declaration_order():
            declaration = schema.parameters[key]
            control = self._build_control(declaration)
            self._controls[key] = control
            label = QLabel(key)
            label.setToolTip(self._describe(declaration))
            control.setToolTip(self._describe(declaration))
            self._form.addRow(label, control)
        self._updating = False

        self._apply_values(schema.defaults())

    def effective_values(self) -> dict[str, Any]:
        """What this slot's agent will actually run with.

        The controls hold the effective configuration directly: a preset is a
        load action, not a hidden layer, so there is never an override the
        user cannot see. Passed through the canonical resolver anyway, so the
        values reported here are the values the engine would compute.
        """

        if self._schema.is_empty:
            return {}
        return resolve_agent_parameters(self._schema, overrides=self._control_values())

    def launch_overrides(self) -> dict[str, Any] | None:
        """The parameters to hand the match, or ``None`` for "send nothing".

        ``None`` rather than an empty mapping when nothing has been moved off
        the agent's defaults, so a default run exports no environment variable
        at all and its command stays identical to a bare CLI invocation.
        """

        if self._schema.is_empty:
            return None
        overrides = parameter_launch_overrides(self._schema, self.effective_values())
        return overrides or None

    def validation_error(self) -> str | None:
        """The canonical resolver's complaint about the current values, if any.

        Normally ``None``: a generated control cannot usually leave its
        declared domain. It is not always ``None`` -- an integer declared with
        bounds outside Qt's 32-bit spin box is clamped by the control and
        genuinely fails here -- which is the point. Launch is blocked on this,
        never on a locally invented rule.
        """

        if self._schema.is_empty:
            return None
        try:
            self.effective_values()
        except AgentValidationError as exc:
            return str(exc)
        return None

    def reset_to_defaults(self) -> None:
        """Return every control to its declared default and clear the preset."""

        if self._schema.is_empty:
            return
        self._updating = True
        self.presets.setCurrentIndex(0)
        self._updating = False
        self._apply_values(self._schema.defaults())

    # -- construction ----------------------------------------------------

    def _clear_controls(self) -> None:
        self._controls.clear()
        while self._form.rowCount():
            self._form.removeRow(0)

    def _build_control(self, declaration: ParameterDeclaration) -> QWidget:
        if declaration.type == "integer":
            spin = QSpinBox()
            # Clamped to what a 32-bit control can express. A wider declared
            # domain is not silently narrowed away: the resolver still sees the
            # real declaration and ``validation_error`` reports the shortfall,
            # so launch is blocked rather than run with a value out of range.
            spin.setRange(
                _clamp_int(declaration.minimum, _SPINBOX_MIN),
                _clamp_int(declaration.maximum, _SPINBOX_MAX),
            )
            spin.valueChanged.connect(self._on_value_edited)
            return spin
        if declaration.type == "number":
            spin = QDoubleSpinBox()
            spin.setDecimals(_NUMBER_DECIMALS)
            spin.setRange(
                float(declaration.minimum) if declaration.minimum is not None else -_NUMBER_LIMIT,
                float(declaration.maximum) if declaration.maximum is not None else _NUMBER_LIMIT,
            )
            spin.setSingleStep(0.05)
            spin.valueChanged.connect(self._on_value_edited)
            return spin
        if declaration.type == "boolean":
            check = QCheckBox()
            check.toggled.connect(self._on_value_edited)
            return check
        if declaration.type == "choice":
            combo = QComboBox()
            for choice in declaration.choices or ():
                combo.addItem(choice, choice)
            combo.currentIndexChanged.connect(self._on_value_edited)
            return combo
        line = QLineEdit()
        line.textChanged.connect(self._on_value_edited)
        return line

    def _describe(self, declaration: ParameterDeclaration) -> str:
        """Tooltip text: what the parameter does, what it accepts, its default.

        Assembled from the declaration's own ``description`` and
        ``describe_domain()`` -- Phase D provides both so a generated form does
        not have to re-derive a user-presentable domain string.
        """

        parts = []
        if declaration.description:
            parts.append(declaration.description)
        parts.append(f"Accepts {declaration.describe_domain()}.")
        parts.append(f"Default: {declaration.default!r}.")
        return " ".join(parts)

    # -- values ----------------------------------------------------------

    def _control_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key, control in self._controls.items():
            if isinstance(control, QCheckBox):
                values[key] = control.isChecked()
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
                values[key] = control.value()
            elif isinstance(control, QComboBox):
                values[key] = control.currentData()
            elif isinstance(control, QLineEdit):
                values[key] = control.text()
        return values

    def _apply_values(self, values: Mapping[str, Any]) -> None:
        self._updating = True
        try:
            for key, value in values.items():
                control = self._controls.get(key)
                if isinstance(control, QCheckBox):
                    control.setChecked(bool(value))
                elif isinstance(control, QSpinBox):
                    # Clamped in Python rather than handed to Qt out of range:
                    # a value outside the 32-bit control is a real state (a
                    # declared domain wider than the control) and Qt would
                    # clamp it anyway, but only after a C++ overflow warning.
                    # ``validation_error`` still reports the shortfall.
                    control.setValue(_clamp_int(value, control.minimum()))
                elif isinstance(control, QDoubleSpinBox):
                    control.setValue(float(value))
                elif isinstance(control, QComboBox):
                    index = control.findData(value)
                    if index >= 0:
                        control.setCurrentIndex(index)
                elif isinstance(control, QLineEdit):
                    control.setText(str(value))
        finally:
            self._updating = False
        self._refresh_summary()
        self.changed.emit()

    # -- reactions -------------------------------------------------------

    def _on_preset_selected(self, _index: int) -> None:
        if self._updating or self._schema.is_empty:
            return
        preset = self.presets.currentData()
        self._apply_values(
            resolve_agent_parameters(self._schema, preset=preset)
            if preset is not None
            else self._schema.defaults()
        )

    def _on_value_edited(self, *_args: object) -> None:
        if self._updating:
            return
        self._refresh_summary()
        self.changed.emit()

    def _refresh_summary(self) -> None:
        """State what the match will use, and where those values came from.

        Deliberately one sentence plus the values rather than a panel: a user
        must never have to infer the effective configuration from a preset
        name alone, but they also should not have to read a metadata dump to
        find one number.
        """

        if self._schema.is_empty:
            self.summary.setText(
                "This agent declares no parameters. Its behavior is fixed by its own source."
            )
            return
        try:
            effective = self.effective_values()
        except AgentValidationError as exc:
            self.summary.setText(f"Cannot run: {exc}")
            return

        defaults = self._schema.defaults()
        edited = sum(1 for key, value in effective.items() if defaults.get(key) != value)
        preset = self.presets.currentData()
        if preset is None and not edited:
            origin = "Using this agent's declared defaults."
        elif preset is None:
            origin = f"Using {edited} changed value{'s' if edited != 1 else ''}."
        else:
            resolved_preset = resolve_agent_parameters(self._schema, preset=preset)
            changed = sum(
                1 for key, value in effective.items() if resolved_preset.get(key) != value
            )
            origin = (
                f"Using preset '{preset}'."
                if not changed
                else f"Using preset '{preset}' with {changed} edited "
                f"value{'s' if changed != 1 else ''}."
            )
        self.summary.setText(f"{origin} Effective: {describe_effective_parameters(effective)}")
