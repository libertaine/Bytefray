"""V5 Alpha 1 Phase E1-E3 -- Designer parameter UX, seed control, ruleset sync.

Phase D defined the parameter contract and proved it end to end from the CLI.
It changed no Designer file at all, so the whole contract was invisible in the
product: an agent could declare typed, bounded, documented parameters with
presets and a user had nowhere to see or set them except a free-form JSON box
that named none of them.

These tests pin the Designer half of that contract:

* controls are generated from the declaration, typed to it and bounded by it;
* presets, defaults and edits resolve through the *canonical* Phase D
  resolver, never a Designer-local reimplementation;
* an agent that declares no schema keeps the free-form editor it always had,
  and Agent API v1 keeps its historical warn-and-ignore behavior;
* a value the schema rejects blocks the launch instead of failing inside a
  match several seconds later;
* randomizing the seed is an explicit action whose result stays visible and
  reproducible.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow. The Qt-free
half of the same behavior lives in
``engine/tests/test_v5_alpha1_phase_e_designer_services.py``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

BYTEFRAY_RULESET_V2_ID = "bytefray-rules-2"
BYTEFRAY_RULESET_V4_ID = "bytefray-rules-4"


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _schema(body: dict, presets: dict | None = None):
    from battle_engine.agent_parameters import parse_parameter_schema

    manifest: dict = {"api_version": 2, "parameters": body}
    if presets is not None:
        manifest["presets"] = presets
    return parse_parameter_schema(manifest)


def _row(name: str, kind: str = "python", api_version: int | None = 2, schema=None):
    from battle_engine.agent_parameters import EMPTY_PARAMETER_SCHEMA

    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(
        name,
        f"/agents/{name}",
        None,
        meta,
        agent_id=name,
        parameter_schema=schema if schema is not None else EMPTY_PARAMETER_SCHEMA,
    )


# One agent per control type, so the type -> widget mapping is asserted
# against a real parsed schema rather than against a hand-built stand-in.
ALL_TYPES_SCHEMA = {
    "reach": {"type": "integer", "default": 16, "minimum": 10, "maximum": 64,
              "description": "How far the process senses and writes."},
    "share": {"type": "number", "default": 0.5, "minimum": 0.0, "maximum": 1.0},
    "verbose": {"type": "boolean", "default": False},
    "mode": {"type": "choice", "default": "sweep", "choices": ["sweep", "hold"]},
    "label": {"type": "string", "default": "alpha"},
}
ALL_TYPES_PRESETS = {
    "aggressive": {"description": "Press harder.", "values": {"reach": 48, "mode": "hold"}},
    "quiet": {"values": {"verbose": False, "reach": 10}},
}


def _panel(tmp_path, rows):
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    panel.setAgents(rows)
    return panel


def _schema_rows():
    schema = _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS)
    return [_row("typed_a", schema=schema), _row("typed_b", schema=schema)]


# ---------------------------------------------------------------------------
# E1 -- generated controls
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_each_declared_type_gets_the_control_that_type_deserves(tmp_path):
    """A generic text box for a bounded integer is exactly the surface Phase E
    exists to replace: the schema knows the type, so the control should too."""

    _make_app()
    from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox

    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA))

        assert isinstance(form._controls["reach"], QSpinBox)
        assert isinstance(form._controls["share"], QDoubleSpinBox)
        assert isinstance(form._controls["verbose"], QCheckBox)
        assert isinstance(form._controls["mode"], QComboBox)
        assert isinstance(form._controls["label"], QLineEdit)
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_controls_start_at_declared_defaults_and_respect_declared_bounds(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA))

        assert form.effective_values() == {
            "reach": 16,
            "share": 0.5,
            "verbose": False,
            "mode": "sweep",
            "label": "alpha",
        }
        assert form._controls["reach"].minimum() == 10
        assert form._controls["reach"].maximum() == 64
        assert form._controls["share"].minimum() == pytest.approx(0.0)
        assert form._controls["share"].maximum() == pytest.approx(1.0)
        assert [
            form._controls["mode"].itemData(i) for i in range(form._controls["mode"].count())
        ] == ["sweep", "hold"]
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_controls_follow_manifest_declaration_order(tmp_path):
    """A generated form and the manifest must agree; Phase D exposes
    ``declaration_order`` precisely so this cannot drift."""

    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA))

        assert list(form._controls) == ["reach", "share", "verbose", "mode", "label"]
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_help_text_carries_description_domain_and_default(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA))

        tip = form._controls["reach"].toolTip()
        assert "How far the process senses and writes." in tip
        assert ">= 10" in tip and "<= 64" in tip
        assert "16" in tip
        assert "one of 'hold', 'sweep'" in form._controls["mode"].toolTip()
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_a_number_control_does_not_round_a_legitimate_value(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema({"share": {"type": "number", "default": 0.333333}}))

        assert form.effective_values()["share"] == pytest.approx(0.333333)
    finally:
        form.deleteLater()


# ---------------------------------------------------------------------------
# E1 -- presets, overrides, reset
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_presets_are_listed_and_selecting_one_updates_every_control(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import DEFAULTS_CHOICE, AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))

        listed = [form.presets.itemText(i) for i in range(form.presets.count())]
        assert listed == [DEFAULTS_CHOICE, "aggressive", "quiet"]

        form.presets.setCurrentIndex(form.presets.findData("aggressive"))

        # Preset values applied; parameters the preset does not name keep the
        # agent's own defaults -- the Phase D precedence rule, not a local one.
        assert form.effective_values() == {
            "reach": 48,
            "share": 0.5,
            "verbose": False,
            "mode": "hold",
            "label": "alpha",
        }
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_editing_after_a_preset_is_an_explicit_override(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))
        form.presets.setCurrentIndex(form.presets.findData("aggressive"))

        form._controls["reach"].setValue(20)

        assert form.effective_values()["reach"] == 20
        assert form.effective_values()["mode"] == "hold"  # still the preset's
        assert "preset 'aggressive'" in form.summary.text()
        assert "1 edited value" in form.summary.text()
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_changing_preset_replaces_every_value(tmp_path):
    """The documented model: a preset is a load action over the whole
    parameter set, so there is no hidden per-field override state a user has
    to reason about."""

    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))
        form.presets.setCurrentIndex(form.presets.findData("aggressive"))
        form._controls["reach"].setValue(20)

        form.presets.setCurrentIndex(form.presets.findData("quiet"))

        assert form.effective_values()["reach"] == 10
        assert form.effective_values()["mode"] == "sweep"
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_reset_to_defaults_restores_declared_values_and_clears_the_preset(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import DEFAULTS_CHOICE, AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))
        form.presets.setCurrentIndex(form.presets.findData("aggressive"))
        form._controls["reach"].setValue(20)

        form.btnReset.click()

        assert form.effective_values() == _schema(ALL_TYPES_SCHEMA).defaults()
        assert form.presets.currentText() == DEFAULTS_CHOICE
        assert form.launch_overrides() is None
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_reset_is_offered_even_when_the_agent_declares_no_presets(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA))

        assert form.btnReset.isVisibleTo(form)
        assert not form.presets.isVisibleTo(form)
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_only_values_moved_off_a_default_are_sent_to_the_match(tmp_path):
    """The identical policy Advanced already applies to scoring weights: a run
    left at defaults produces the same command a bare CLI invocation would,
    and therefore the same match identity."""

    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))
        assert form.launch_overrides() is None

        form.presets.setCurrentIndex(form.presets.findData("aggressive"))

        assert form.launch_overrides() == {"reach": 48, "mode": "hold"}
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_the_summary_states_the_effective_values_not_only_the_preset_name(tmp_path):
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed_a", _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS))
        form.presets.setCurrentIndex(form.presets.findData("aggressive"))

        text = form.summary.text()
        assert "aggressive" in text
        assert "reach=48" in text
        assert "share=0.5" in text
    finally:
        form.deleteLater()


# ---------------------------------------------------------------------------
# E1 -- validation blocks launch
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_a_value_the_schema_rejects_blocks_the_run_button(tmp_path):
    """A declared integer domain can be wider than Qt's 32-bit spin box, so
    the control clamps and the canonical resolver -- not a Designer-local rule
    -- reports the shortfall before any subprocess exists."""

    _make_app()
    schema = _schema({"huge": {"type": "integer", "default": 5_000_000_000,
                               "minimum": 4_000_000_000}})
    panel = _panel(tmp_path, [_row("huge_a", schema=schema), _row("huge_b", schema=schema)])
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        problems = panel.parameter_validation_errors()
        assert problems, "a clamped control below the declared minimum must be reported"
        assert "below the declared minimum" in problems[0]
        assert not panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_a_valid_selection_leaves_the_run_button_enabled(tmp_path):
    _make_app()
    panel = _panel(tmp_path, _schema_rows())
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        assert panel.parameter_validation_errors() == []
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_run_is_not_emitted_while_a_parameter_is_invalid(tmp_path, monkeypatch):
    _make_app()
    import app.views.advanced as advanced_module

    warned: list[tuple] = []
    monkeypatch.setattr(
        advanced_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: warned.append(args),
    )
    schema = _schema({"huge": {"type": "integer", "default": 5_000_000_000,
                               "minimum": 4_000_000_000}})
    panel = _panel(tmp_path, [_row("huge_a", schema=schema), _row("huge_b", schema=schema)])
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        panel._emit_run()

        assert emitted == []
        assert warned, "the user must be told why the match did not start"
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# E1 -- legacy compatibility
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_a_schema_agent_shows_controls_and_a_legacy_agent_keeps_its_json_box(tmp_path):
    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA)
    panel = _panel(
        tmp_path,
        [_row("typed", schema=schema), _row("legacy", api_version=1)],
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("typed"))

        assert panel.schemaA.has_schema()
        assert not panel.schemaA.isHidden()
        assert panel.editorA.isHidden()

        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))

        assert not panel.schemaA.has_schema()
        assert panel.schemaA.isHidden()
        assert not panel.editorA.isHidden()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_stale_free_form_json_never_travels_with_a_schema_agent(tmp_path):
    """Switching a slot from a legacy agent to a schema agent must not smuggle
    the previous agent's free-form JSON into a schema-validated match."""

    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA)
    panel = _panel(
        tmp_path,
        [_row("legacy", api_version=1), _row("typed", schema=schema)],
    )
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))
        panel.editorA.text.setPlainText(json.dumps({"nonsense": 1}))
        panel.agentA.setCurrentIndex(panel.agentA.findData("typed"))

        panel._emit_run()

        assert emitted and emitted[0].a_params is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_free_form_json_still_reaches_a_legacy_agent(tmp_path):
    _make_app()
    panel = _panel(
        tmp_path, [_row("legacy", api_version=1), _row("legacy2", api_version=1)]
    )
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        panel.editorA.text.setPlainText(json.dumps({"byte": 7}))

        panel._emit_run()

        assert emitted and emitted[0].a_params == {"byte": 7}
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_a_v2_agent_without_a_schema_keeps_the_free_form_path(tmp_path):
    """The six ``v4_*`` starters are Agent API v2 and declare no parameters.
    They must not be forced through a schema they never opted into."""

    _make_app()
    panel = _panel(tmp_path, [_row("v4_scout"), _row("v4_claimer")])
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        assert not panel.schemaA.has_schema()
        assert not panel.editorA.isHidden()
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# E1 -- every entrant slot
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_all_three_entrant_slots_generate_their_own_controls(tmp_path):
    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS)
    panel = _panel(
        tmp_path,
        [_row("typed_a", schema=schema), _row("typed_b", schema=schema),
         _row("typed_c", schema=schema)],
    )
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.btnAddAgent.click()

        assert panel.schemaA.has_schema()
        assert panel.schemaB.has_schema()
        assert panel.schemaC.has_schema()
        assert not panel.schemaC.isHidden()
        assert panel.editorC.isHidden()

        panel.schemaA.presets.setCurrentIndex(panel.schemaA.presets.findData("aggressive"))
        panel.schemaB._controls["reach"].setValue(11)
        panel.schemaC.presets.setCurrentIndex(panel.schemaC.presets.findData("quiet"))
        panel._emit_run()

        cfg = emitted[0]
        assert cfg.a_params == {"reach": 48, "mode": "hold"}
        assert cfg.b_params == {"reach": 11}
        assert cfg.c_params == {"reach": 10}
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_mixed_schema_and_legacy_entrants_each_use_their_own_surface(tmp_path):
    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA)
    panel = _panel(
        tmp_path,
        [_row("typed", schema=schema), _row("plain"), _row("plain2")],
    )
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("typed"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("plain"))

        assert panel.schemaA.has_schema() and panel.editorA.isHidden()
        assert not panel.schemaB.has_schema() and not panel.editorB.isHidden()

        panel.schemaA._controls["reach"].setValue(30)
        panel.editorB.text.setPlainText(json.dumps({"whatever": True}))
        panel._emit_run()

        cfg = emitted[0]
        assert cfg.a_params == {"reach": 30}
        assert cfg.b_params == {"whatever": True}
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_a_hidden_third_slot_sends_no_parameters(tmp_path):
    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA, ALL_TYPES_PRESETS)
    panel = _panel(
        tmp_path,
        [_row("typed_a", schema=schema), _row("typed_b", schema=schema),
         _row("typed_c", schema=schema)],
    )
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.btnAddAgent.click()
        panel.schemaC.presets.setCurrentIndex(panel.schemaC.presets.findData("quiet"))
        panel.btnRemoveAgentC.click()

        panel._emit_run()

        assert emitted[0].c_type is None
        assert emitted[0].c_params is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_changing_the_ruleset_does_not_discard_parameter_edits(tmp_path):
    """A Ruleset change repopulates the agent combos, which re-enters the
    parameter sync with the same selection. Rebuilding the form there would
    silently throw away values the user had already set."""

    _make_app()
    schema = _schema(ALL_TYPES_SCHEMA)
    panel = _panel(
        tmp_path, [_row("typed_a", schema=schema), _row("typed_b", schema=schema)]
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.schemaA._controls["reach"].setValue(42)

        panel.setAgents(list(panel._all_rows))  # a catalog refresh

        assert panel.schemaA.effective_values()["reach"] == 42
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_selecting_a_different_agent_rebuilds_the_controls(tmp_path):
    _make_app()
    first = _schema({"alpha": {"type": "integer", "default": 1}})
    second = _schema({"beta": {"type": "integer", "default": 2}})
    panel = _panel(
        tmp_path, [_row("first", schema=first), _row("second", schema=second)]
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("first"))
        assert list(panel.schemaA.effective_values()) == ["alpha"]

        panel.agentA.setCurrentIndex(panel.agentA.findData("second"))

        assert list(panel.schemaA.effective_values()) == ["beta"]
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# E2 -- Randomize Seed
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_randomize_seed_puts_a_visible_valid_value_in_the_field(tmp_path):
    _make_app()
    panel = _panel(tmp_path, [_row("a", api_version=1), _row("b", api_version=1)])
    try:
        returned = panel.randomize_seed()

        assert panel.seed.value() == returned
        assert 1 <= returned <= panel.seed.maximum()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_randomize_seed_never_produces_the_engine_default_sentinel(tmp_path):
    """Advanced reads 0 as "use the engine's own default seed", so generating
    0 would mean the opposite of randomizing."""

    _make_app()
    panel = _panel(tmp_path, [_row("a", api_version=1), _row("b", api_version=1)])
    try:
        assert all(panel.randomize_seed() != 0 for _ in range(200))
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_successive_randomizations_can_change_the_value(tmp_path):
    _make_app()
    panel = _panel(tmp_path, [_row("a", api_version=1), _row("b", api_version=1)])
    try:
        # Not "two draws always differ" -- they legitimately may not. Over a
        # sample this size a generator stuck on one value is the only way to
        # see a single distinct result.
        assert len({panel.randomize_seed() for _ in range(50)}) > 1
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_a_manually_entered_seed_is_untouched_when_randomize_is_not_used(tmp_path):
    _make_app()
    panel = _panel(tmp_path, [_row("a", api_version=1), _row("b", api_version=1)])
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        panel.seed.setValue(4242)
        panel._emit_run()

        assert panel.seed.value() == 4242
        assert emitted[0].seed == 4242
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_the_displayed_randomized_seed_is_exactly_what_the_match_receives(tmp_path):
    _make_app()
    panel = _panel(tmp_path, [_row("a", api_version=1), _row("b", api_version=1)])
    emitted: list = []
    panel.runRequested.connect(emitted.append)
    try:
        seed = panel.randomize_seed()
        panel._emit_run()

        assert emitted[0].seed == seed
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_the_agent_lab_test_seed_can_also_be_randomized(tmp_path):
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel(catalog=None)
    try:
        before = panel.selected_seed()
        returned = panel.randomize_seed()

        assert panel.selected_seed() == returned
        assert 1 <= returned <= panel.seedSpin.maximum()
        assert isinstance(before, int)
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# E3 -- ruleset synchronization
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_the_dead_two_combo_ruleset_wrapper_is_gone(tmp_path):
    """``sync_ruleset_choices`` had no caller anywhere in the product or its
    tests; Simple and Advanced both drive the opposite direction, filtering
    agents *by* the selected Ruleset."""

    import app.widgets.ruleset_combo as module

    assert not hasattr(module, "sync_ruleset_choices")
    assert hasattr(module, "sync_ruleset_choices_for_metadata")


@pytest.mark.gui
def test_the_designer_never_offers_a_rejected_research_ruleset(tmp_path):
    _make_app()
    panel = _panel(tmp_path, _schema_rows())
    try:
        offered = {panel.ruleset.itemData(i) for i in range(panel.ruleset.count())}
        assert offered == {
            BYTEFRAY_RULESET_V2_ID,
            BYTEFRAY_RULESET_V4_ID,
            "bytefray-rules-4-alpha2",
            "bytefray-rules-4-alpha1",
            "bytefray-rules-1",
        }
        assert not any("r1" in str(item) or "r2" in str(item) for item in offered)
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_changing_entrants_cannot_leave_an_incompatible_ruleset_selected(tmp_path):
    """Advanced's invariant: the Ruleset is the controlling selector, so the
    roster is filtered to what it supports and an agent choice can never
    invalidate it."""

    _make_app()
    panel = _panel(
        tmp_path,
        [_row("typed", schema=_schema(ALL_TYPES_SCHEMA)), _row("legacy", api_version=1)],
    )
    try:
        for index in range(panel.ruleset.count()):
            panel.ruleset.setCurrentIndex(index)
            ruleset_id = panel.ruleset.itemData(index)
            for combo in (panel.agentA, panel.agentB):
                for slot in range(combo.count()):
                    combo.setCurrentIndex(slot)
                    row = panel._row_for_slot(combo)
                    if row is None:
                        continue
                    from app.services.ruleset_options import agent_row_supported_by_ruleset

                    assert agent_row_supported_by_ruleset(row, ruleset_id), (
                        f"{row.agent_id} was offered under {ruleset_id}"
                    )
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_an_agent_api_v2_roster_offers_the_stable_v4_ruleset(tmp_path):
    _make_app()
    panel = _panel(tmp_path, _schema_rows())
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        assert panel.agentA.count() == 2
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# E4 -- effective parameters in the results table
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_the_results_table_reports_the_parameters_a_match_actually_used(tmp_path):
    _make_app()
    from app.services.designer_workflows import (
        EntrantResultPresentation,
        MatchPresentation,
    )

    panel = _panel(tmp_path, _schema_rows())
    try:
        panel.show_result(
            MatchPresentation(
                winner="A",
                termination_reason="ticks",
                result_path=Path("result.json"),
                replay_path=None,
                entrants=(
                    EntrantResultPresentation(
                        agent_id="A",
                        name="typed_a",
                        alive=True,
                        score=10.0,
                        parameters={"reach": 48, "mode": "hold"},
                    ),
                    EntrantResultPresentation(
                        agent_id="B", name="typed_b", alive=False, score=1.0
                    ),
                ),
            )
        )

        rendered = "\n".join(
            f"{panel.table.item(row, 0).text()}={panel.table.item(row, 1).text()}"
            for row in range(panel.table.rowCount())
        )
        assert "reach=48" in rendered
        assert "mode='hold'" in rendered
        # An entrant that ran with no parameters gets no row claiming it did.
        assert rendered.count("parameters") == 1
    finally:
        panel.deleteLater()
