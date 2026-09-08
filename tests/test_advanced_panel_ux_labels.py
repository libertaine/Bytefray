"""Phase 1 RC2->final UX polish: terminology/label coverage for Simple and
Advanced match setup, the Replay Browser, and Agent Params.

Pins that the GUI-facing wording changed (Arena Size, Survival/Kill/Territory
Weight, Territory Bucket Size, Random Seed, View Last Match, Choose Replay...,
View Replay) while every underlying identifier a match/replay/config
consumer depends on -- ``RunConfig`` field names, widget attribute names,
numeric ranges/defaults, and signal wiring -- stayed exactly as it was
before this pass. See docs/specs (Phase 1 completion report) for the
semantics that justified each label.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _row(agent_id: str, kind: str = "python", api_version: int | None = 1):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": agent_id, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(agent_id, f"/agents/{agent_id}", None, meta, agent_id=agent_id)


def _label_text_for(panel, control) -> str:
    """The QFormLayout/addRow-created label bound to ``control`` as its buddy."""

    from PySide6.QtWidgets import QLabel

    for label in panel.findChildren(QLabel):
        if label.buddy() is control:
            return label.text()
    raise AssertionError(f"no label found with buddy={control!r}")


# ---------------------------------------------------------------------------
# Simple panel: UX-01, UX-02
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_simple_panel_uses_arena_size_terminology_and_view_last_match():
    _make_app()
    from app.views.simple import GRID_PRESETS, SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        assert _label_text_for(panel, panel.gridSize) == "Arena Size"
        assert panel.btnOpen.text() == "View Last Match"
        # Internal preset mapping (consumed by _emit_run) is unchanged.
        assert GRID_PRESETS == {
            "Small (256)": 256,
            "Medium (512)": 512,
            "Large (1024)": 1024,
        }
        assert "arena size" in panel.btnRun.accessibleDescription().lower()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_simple_panel_run_still_produces_same_run_config_shape():
    _make_app()
    from app.views.simple import SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        panel.setAgents([_row("alpha"), _row("beta")])
        captured = []
        panel.runRequested.connect(captured.append)
        panel.gridSize.setCurrentText("Large (1024)")
        panel._emit_run()

        assert len(captured) == 1
        cfg = captured[0]
        assert cfg.arena == 1024
        assert cfg.a_type == "alpha"
        assert cfg.b_type == "beta"
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Advanced panel: UX-01, UX-02, UX-03..UX-08
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_panel_scoring_labels_and_tooltips(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        expected_labels = {
            "arena": "Arena Size",
            "alive_w": "Survival Weight",
            "kill_w": "Kill Weight",
            "territory_w": "Territory Weight",
            "territory_bucket": "Territory Bucket Size",
            "seed": "Random Seed (0 = default)",
        }
        for attr, label_text in expected_labels.items():
            control = getattr(panel, attr)
            assert _label_text_for(panel, control) == label_text
            assert control.toolTip().strip() != "", f"{attr} has no tooltip"

        # The seed tooltip must not overclaim: 0 does not randomize.
        assert "not" in panel.seed.toolTip().lower()
        assert "default seed" in panel.seed.toolTip().lower()

        # Territory weight tooltip explains the bucket relationship without
        # leaking the internal identifier as the whole story.
        assert "bucket" in panel.territory_w.toolTip().lower()

        assert panel.btnOpen.text() == "View Last Match"
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_panel_numeric_ranges_match_engine_defaults(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        assert (panel.arena.minimum(), panel.arena.maximum(), panel.arena.value()) == (
            64,
            8192,
            512,
        )
        assert (panel.ticks.minimum(), panel.ticks.maximum(), panel.ticks.value()) == (
            1,
            100000,
            600,
        )
        # Phase 5B: the starting scoring values are the engine's own
        # defaults, asserted against ``Weights()`` rather than restated as
        # literals here -- if the engine ever retunes them, this test
        # follows automatically instead of pinning a stale GUI copy.
        from battle_engine.config import Weights

        engine_defaults = Weights()
        for spin, expected in (
            (panel.alive_w, engine_defaults.alive),
            (panel.kill_w, engine_defaults.kill),
            (panel.territory_w, engine_defaults.territory),
        ):
            assert (spin.minimum(), spin.maximum(), spin.value()) == (
                0.0,
                1000.0,
                expected,
            )
        assert (
            panel.territory_bucket.minimum(),
            panel.territory_bucket.maximum(),
            panel.territory_bucket.value(),
        ) == (1, 4096, engine_defaults.territory_bucket)
        assert (panel.seed.minimum(), panel.seed.maximum(), panel.seed.value()) == (
            0,
            1_000_000,
            0,
        )
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_panel_emit_run_keeps_underlying_config_keys(tmp_path):
    """Renaming GUI labels must not rename the RunConfig/CLI contract."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents([_row("alpha"), _row("beta")])
        panel.alive_w.setValue(2.5)
        panel.kill_w.setValue(7.0)
        panel.territory_w.setValue(3.0)
        panel.territory_bucket.setValue(48)
        panel.seed.setValue(42)

        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()

        assert len(captured) == 1
        cfg = captured[0]
        assert cfg.alive_w == 2.5
        assert cfg.kill_w == 7.0
        assert cfg.territory_w == 3.0
        assert cfg.territory_bucket == 48
        assert cfg.seed == 42
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Replay Browser: UX-11, UX-12, UX-13
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_replay_browser_labels_and_explanation(tmp_path):
    _make_app()
    from PySide6.QtWidgets import QLabel

    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        assert panel.btnChooseReplay.text() == "Choose Replay…"
        assert panel.btnOpenReplay.text() == "View Replay"

        replay_tab_index = panel.tabs.indexOf(panel.btnOpenReplay.parentWidget())
        assert panel.tabs.tabText(replay_tab_index) == "Replay Browser"

        # The tab has word-wrapped explanatory copy so a first-time user
        # isn't left guessing what to select.
        replay_tab = panel.tabs.widget(replay_tab_index)
        intro_texts = " ".join(label.text() for label in replay_tab.findChildren(QLabel))
        assert "replay" in intro_texts.lower()
        assert any(
            label.wordWrap()
            for label in replay_tab.findChildren(QLabel)
            if label is not panel.lblReplay
        )
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_replay_browser_open_replay_still_invokes_same_launcher(tmp_path, monkeypatch):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        replay_path = tmp_path / "replay.jsonl"
        replay_path.write_text("{}")
        panel.lblReplay.setText(str(replay_path))

        captured = []
        monkeypatch.setattr(
            "app.services.engine.open_pygame_client_direct",
            lambda root, path: captured.append((root, path)),
        )
        panel.btnOpenReplay.click()

        assert captured == [(panel._paths.root, replay_path)]
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_choose_replay_dialog_still_filters_jsonl(tmp_path, monkeypatch):
    _make_app()
    from app.views import advanced as advanced_module
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        captured_filter = {}

        def fake_dialog(parent, caption, directory, filter_):
            captured_filter["caption"] = caption
            captured_filter["filter"] = filter_
            return "", ""

        monkeypatch.setattr(
            advanced_module.QFileDialog, "getOpenFileName", staticmethod(fake_dialog)
        )
        panel.btnChooseReplay.click()

        assert captured_filter["caption"] == "Choose Replay"
        assert "*.jsonl" in captured_filter["filter"]
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Agent Params: UX-09, UX-10
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_agent_params_tab_explains_itself_and_does_not_fabricate_param_names(tmp_path):
    _make_app()
    from PySide6.QtWidgets import QLabel

    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        params_index = panel.tabs.indexOf(panel.editorA.parentWidget())
        assert panel.tabs.tabText(params_index) == "Agent Params"
        params_tab = panel.tabs.widget(params_index)
        intro_texts = " ".join(
            label.text() for label in params_tab.findChildren(QLabel)
        )
        assert "optional" in intro_texts.lower()
        assert "agent" in intro_texts.lower()

        # The placeholder must not present made-up field names ("speed",
        # "aggression") as if they were a real, Bytefray-defined contract.
        placeholder = panel.editorA.text.placeholderText()
        assert "speed" not in placeholder.lower()
        assert "aggression" not in placeholder.lower()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_json_editor_still_produces_same_underlying_representation():
    _make_app()
    from app.widgets.json_editor import JsonEditor

    editor = JsonEditor(title="Agent A Params (JSON)")
    try:
        editor.text.setPlainText('{"stride": 17, "target": 0}')
        assert editor.get_data_or_none() == {"stride": 17, "target": 0}

        editor.text.setPlainText("")
        assert editor.get_data_or_none() is None
    finally:
        editor.deleteLater()
