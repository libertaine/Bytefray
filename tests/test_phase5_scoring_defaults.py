"""Phase 5B regression coverage: Advanced defers to the engine's scoring defaults.

Advanced used to hard-code ``kill_w = 1.0`` and ``territory_bucket = 32`` and
submit them on every run. Neither value ever matched an engine default at any
point in this repository's history (``engine/config/battle.defaults.json``
already shipped ``"kill": 5`` when the Designer was first added, and
``Weights.territory_bucket`` has been 64 since it existed), and nothing in the
README, ``docs/``, ``docs/specs/``, or any test documented them as a deliberate
Designer profile. The practical effect was that merely opening Advanced and
pressing Run scored the match differently from Simple and from a bare
``bytefray run`` -- changing scores, margins, and the derived ``match_id`` /
``replay_id`` / ``result_id`` with no user action.

The fix is not "copy the engine's numbers into the GUI" -- that would drift
again the next time the engine retunes. Advanced now *reads* the engine's
``Weights`` dataclass for what it displays, and forwards a scoring flag only
when the user has actually moved that field off the default. These tests pin
the resulting launch contract rather than the widget values alone.
"""

from __future__ import annotations

import os

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _row(name: str, kind: str = "python", api_version: int | None = 2):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(name, f"/agents/{name}", None, meta, agent_id=name)


def _panel(tmp_path):
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    panel.setAgents([_row("alpha"), _row("beta")])
    return panel


def _emit(panel):
    captured = []
    panel.runRequested.connect(captured.append)
    panel._emit_run()
    assert len(captured) == 1
    return captured[0]


@pytest.mark.gui
def test_advanced_displays_the_engine_scoring_defaults(tmp_path):
    """What Advanced shows is read from the engine, not restated in the GUI."""
    _make_app()
    from battle_engine.config import Weights

    from app.views.advanced import ENGINE_DEFAULT_WEIGHTS

    engine = Weights()
    assert ENGINE_DEFAULT_WEIGHTS == engine

    panel = _panel(tmp_path)
    try:
        assert panel.alive_w.value() == engine.alive
        assert panel.kill_w.value() == engine.kill
        assert panel.territory_w.value() == engine.territory
        assert panel.territory_bucket.value() == engine.territory_bucket
        # Guard against the specific historical drift this phase fixed.
        assert panel.kill_w.value() == 5.0
        assert panel.territory_bucket.value() == 64
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_untouched_advanced_run_omits_every_scoring_flag(tmp_path):
    """An untouched Advanced run must not override engine scoring at all."""
    _make_app()
    panel = _panel(tmp_path)
    try:
        cfg = _emit(panel)
        assert cfg.alive_w is None
        assert cfg.kill_w is None
        assert cfg.territory_w is None
        assert cfg.territory_bucket is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_untouched_advanced_builds_the_same_arguments_as_a_bare_two_agent_run(
    tmp_path,
):
    """The whole chain, not just RunConfig: no weight flag reaches the CLI.

    This is the assertion that actually pins the bug that was fixed -- the
    argument list an untouched Advanced run launches must be identical to the
    one a caller that has never heard of scoring weights produces, which is
    exactly what Simple emits.
    """
    _make_app()
    from battle_engine.launchers import build_designer_match_arguments

    panel = _panel(tmp_path)
    try:
        cfg = _emit(panel)
        built = build_designer_match_arguments(
            ticks=cfg.ticks,
            arena=cfg.arena,
            a_type=cfg.a_type,
            b_type=cfg.b_type,
            ruleset_id=cfg.ruleset_id,
            alive_w=cfg.alive_w,
            kill_w=cfg.kill_w,
            territory_w=cfg.territory_w,
            territory_bucket=cfg.territory_bucket,
            seed=cfg.seed,
        )
        # Compared against the roster the panel actually emitted: this test
        # is about which *scoring* flags appear, and the roster identity is
        # already pinned by the Phase 2/4 suites.
        assert built == [
            "--ticks", str(cfg.ticks),
            "--arena", str(cfg.arena),
            "--a-type", cfg.a_type,
            "--b-type", cfg.b_type,
            "--ruleset", cfg.ruleset_id,
        ]
        for flag in ("--alive-w", "--kill-w", "--territory-w", "--territory-bucket"):
            assert flag not in built
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_only_the_edited_weight_is_forwarded(tmp_path):
    """Editing one field must not start submitting the other three."""
    _make_app()
    panel = _panel(tmp_path)
    try:
        panel.kill_w.setValue(9.0)
        cfg = _emit(panel)
        assert cfg.kill_w == 9.0
        assert cfg.alive_w is None
        assert cfg.territory_w is None
        assert cfg.territory_bucket is None

        panel.territory_bucket.setValue(16)
        cfg = _emit(panel)
        assert cfg.kill_w == 9.0
        assert cfg.territory_bucket == 16
        assert cfg.alive_w is None
        assert cfg.territory_w is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_restoring_the_engine_default_omits_the_flag_again(tmp_path):
    """Typing the default back in returns to exact engine-default behavior."""
    _make_app()
    from battle_engine.config import Weights

    engine = Weights()
    panel = _panel(tmp_path)
    try:
        panel.kill_w.setValue(9.0)
        assert _emit(panel).kill_w == 9.0

        panel.kill_w.setValue(engine.kill)
        assert _emit(panel).kill_w is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_a_deliberate_zero_weight_is_still_forwarded(tmp_path):
    """0 is a meaningful choice (turn territory scoring off), not 'unset'.

    Guards the one falsy value the omit-when-default rule could plausibly
    swallow: ``territory_w = 0`` differs from the engine default of 1.0 and
    must reach the CLI, or the tooltip's documented "set to 0 to turn off
    territory scoring entirely" would silently do nothing.
    """
    _make_app()
    panel = _panel(tmp_path)
    try:
        panel.territory_w.setValue(0.0)
        cfg = _emit(panel)
        assert cfg.territory_w == 0.0
    finally:
        panel.deleteLater()
