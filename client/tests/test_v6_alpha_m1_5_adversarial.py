"""Independent M1-5 probes using only ordinary product match fixtures."""

from __future__ import annotations

import re

import pytest
from battle_client import cli
from battle_client.sensing import PhasePosition, SensingView
from battle_client.sensing_presentation import SensingPresentation, entrant_scene
from battle_engine.sensing_playback import ExchangePhase
from test_v6_alpha_sensing import _pair


def _presentation(tmp_path, actions, **kwargs):
    cursor, _, _ = _pair(tmp_path, actions, **kwargs)
    return SensingPresentation(cursor, "Recorded end", interval=0.05)


def _observation(presentation, callback, tick=1):
    presentation.controller.seek_to(PhasePosition(tick, callback, ExchangePhase.OBSERVATION))
    view = presentation.current_view
    assert isinstance(view, SensingView)
    return view


def test_delivered_read_value_and_owner_reach_the_display(tmp_path):
    presentation = _presentation(tmp_path, [("write", 0, 237), ("read", 0)])
    view = _observation(presentation, 3)
    assert view.reads[-1].value == 237
    assert view.reads[-1].owner == "A"
    text = "\n".join(entrant_scene(view).lines)
    assert "237" in text, "The verified delivered READ value never reaches the displayed scene."
    assert re.search(r"owner\s*[:=]?\s*A\b", text, re.IGNORECASE)


def test_old_delivered_scan_samples_remain_inspectable(tmp_path):
    presentation = _presentation(tmp_path, [("sense", 91), ("sense", 0), ("sense", 91)])
    view = _observation(presentation, 7)
    assert [sample.sampled_at.callback for sample in view.samples] == [1, 2, 3]
    text = "\n".join(entrant_scene(view).lines)
    for callback in (1, 2, 3):
        assert re.search(rf"sampled[^\n;]*callback\s+{callback}\b", text), (
            f"Delivered scan sampled at callback {callback} is inaccessible after later callbacks."
        )


def test_cross_tick_receipt_labels_identify_both_ticks_and_own_process(tmp_path):
    presentation = _presentation(tmp_path, [("read", 0)] * 7 + [("sense", 91)])
    view = _observation(presentation, 9, tick=2)
    sample = view.samples[-1]
    assert sample.sampled_at.tick == 1 and sample.received_at.tick == 2
    text = "\n".join(entrant_scene(view).lines)
    assert re.search(r"(?:received|delivered)\s+(?:at\s+)?(?:t|tick\s*)2\b", text), (
        "Delayed receipt text omits the actual delivery tick."
    )
    assert re.search(r"process\s+0\b", text), "Sample/receipt points omit the own process ID."


def test_hidden_opponent_writes_do_not_change_entrant_scene_or_pacing(tmp_path):
    left = _presentation(tmp_path / "left", [("sense", 0)], b=[("write", 91, 137)])
    right = _presentation(tmp_path / "right", [("sense", 0)], b=[("write", 91, 241)])
    assert left.controller.positions == right.controller.positions
    for presentation in (left, right):
        presentation.controller.play()
        presentation.controller.update(0.275)
    assert left.index == right.index
    assert entrant_scene(left.current_view) == entrant_scene(right.current_view)
    before = left.current_view
    left.switch(False)
    left.switch(True)
    assert left.current_view == before


def test_invalid_trace_cli_fallback_disables_all_passive_perspectives(tmp_path, monkeypatch):
    _presentation(tmp_path, [("sense", 91)])
    trace = tmp_path / "trace.jsonl"
    trace.write_bytes(b"invalid ordinary product trace")
    seen = {}

    class Renderer:
        def run(self, session, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(cli, "_resolve_renderer", lambda name: Renderer)
    assert cli.main([
        "--renderer", "pygame", "--replay", str(tmp_path / "replay.jsonl"),
        "--perspective", "A", "--director", "--fight-night",
    ]) == 0
    assert seen["sensing_presentation"] is None
    assert "Omniscient" in seen["sensing_fallback_reason"]
    assert "disabled" in seen["sensing_fallback_reason"]
    assert seen.get("perspective_manager") is None
    assert seen.get("director_manager") is None
    assert seen.get("fight_night_manager") is None


def test_unavailable_alpha_perspective_has_sanitized_feedback(tmp_path, monkeypatch, capsys):
    _presentation(tmp_path, [("sense", 91)])
    seen = {}

    class Renderer:
        def run(self, session, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(cli, "_resolve_renderer", lambda name: Renderer)
    assert cli.main([
        "--renderer", "pygame", "--replay", str(tmp_path / "replay.jsonl"),
        "--perspective", "PRIVATE_OPPONENT_HINT",
    ]) == 0
    assert isinstance(seen["sensing_presentation"].current_view, SensingView)
    error = capsys.readouterr().err
    assert "Requested perspective unavailable" in error
    assert "PRIVATE_OPPONENT_HINT" not in error


@pytest.mark.gui
def test_direct_alpha_fallback_clears_untrusted_legacy_managers(tmp_path, monkeypatch):
    pytest.importorskip("pygame")
    from battle_client.renderers.pygame_renderer import PygameRenderer

    _, session, _ = _pair(tmp_path, [("sense", 91)])
    renderer = PygameRenderer()

    class ForbiddenManager:
        def set_mode(self, mode):
            raise AssertionError("Alpha fallback consumed a legacy passive perspective manager.")

        @property
        def available(self):
            raise AssertionError("Alpha fallback consumed a legacy pacing manager.")

    monkeypatch.setattr(renderer, "_configure_window", lambda: None)

    def inspect_loop(controller):
        assert renderer._perspective_manager is None
        assert renderer._director_manager is None
        assert renderer._fight_night_manager is None
        assert "Omniscient" in renderer._sensing_fallback_reason
        assert "disabled" in renderer._sensing_fallback_reason

    monkeypatch.setattr(renderer, "_loop", inspect_loop)
    manager = ForbiddenManager()
    renderer.run(
        session, tick_interval=0.05, perspective_manager=manager, initial_perspective="A",
        director_manager=manager, initial_director_enabled=True,
        fight_night_manager=manager, initial_fight_night_enabled=True,
    )


@pytest.mark.gui
def test_scroll_reaches_recorded_histories_and_rewind_removes_future_receipts(tmp_path, monkeypatch):
    pg = pytest.importorskip("pygame")
    from battle_client.renderers.sensing_renderer import SensingReplayRenderer

    presentation = _presentation(tmp_path, [("sense", 91), ("sense", 0), ("sense", 91)])
    _observation(presentation, 7)
    pg.init()
    try:
        renderer = SensingReplayRenderer()
        renderer.pg = pg
        # Smallest contract size with the bundled font: the history overflows
        # on every platform, so the wheel must be what reaches the oldest rows.
        renderer.screen = pg.Surface((900, 650))
        renderer.font = pg.font.Font(None, 24)
        captured = []
        original_text = renderer.text

        def capture(value, x, y):
            captured.append(value)
            original_text(value, x, y)

        monkeypatch.setattr(renderer, "text", capture)
        renderer.draw(presentation)
        assert not re.search(r"sampled t1 callback 1\b", " ".join(captured))
        for _ in range(30):
            renderer.handle_event(pg.event.Event(pg.MOUSEWHEEL, y=-1), presentation)
            renderer.draw(presentation)
        text = " ".join(captured)
        assert re.search(r"sampled t1 callback 1\b", text), "Oldest delivered scan cannot be reached with the wheel."
        assert "READ 0: value" in text, "Delivered READ history cannot be reached with the wheel."
        assert "Operator verification" not in text

        renderer.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_1, mod=0), presentation)
        renderer.draw(presentation)
        assert renderer.scroll_offset == 0 and renderer.last_lines == ()
        renderer.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_2, mod=0), presentation)
        renderer.draw(presentation)
        assert isinstance(presentation.current_view, SensingView)
        assert not any("Operator verification" in line for line in renderer.last_lines)
        renderer.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_HOME, mod=0), presentation)
        renderer.draw(presentation)
        assert renderer.scroll_offset == 0
        assert not presentation.current_view.samples and not presentation.current_view.reads
        assert not any(marker.kind in {"receipt", "historical"} for marker in renderer.last_markers)
    finally:
        pg.quit()
