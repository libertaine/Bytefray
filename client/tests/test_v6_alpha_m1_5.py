"""M1-5 renderer contract, native launches and real Pygame event handling."""

from __future__ import annotations

from dataclasses import asdict

import pytest
from battle_client import cli
from battle_client.renderers.sensing_renderer import SensingReplayRenderer
from battle_client.sensing import SensingView
from battle_client.sensing_presentation import (
    SensingPresentation,
    entrant_scene,
    load_sensing_presentation,
)
from battle_engine.sensing_playback import ExchangePhase
from test_v6_alpha_sensing import _pair


def _presentation(tmp_path, script=(("sense", 91), ("move", 64), ("write", 91, 7)), **kwargs):
    cursor, session, playback = _pair(tmp_path, script, **kwargs)
    return SensingPresentation(cursor, "Recorded end", interval=.05), session, playback


def test_actual_adapter_request_receipt_move_write_and_historical_age(tmp_path):
    presentation, _, _ = _presentation(tmp_path)
    positions = presentation.controller.positions
    scenes = {}
    for callback, phase in [(1, ExchangePhase.ACTION), (2, ExchangePhase.OBSERVATION), (2, ExchangePhase.ACTION), (3, ExchangePhase.ACTION)]:
        position = next(p for p in positions if p.tick == 1 and p.callback == callback and p.phase == phase)
        presentation.controller.seek_to(position)
        view = presentation.current_view
        assert isinstance(view, SensingView)
        scenes[(callback, phase)] = entrant_scene(view)
    request = scenes[(1, ExchangePhase.ACTION)]
    assert any(m.kind == "request" and m.address == 91 and m.half_width == 27 for m in request.markers)
    assert not any(m.kind == "historical" for m in request.markers)
    assert "1 action spent" in " ".join(request.lines)
    receipt = scenes[(2, ExchangePhase.OBSERVATION)]
    assert any(m.kind == "receipt" for m in receipt.markers)
    assert any(m.kind == "historical" and m.address == 91 for m in receipt.markers)
    assert not any(m.kind == "request" for m in receipt.markers)
    assert any(m.kind == "move" and m.origin == 0 and m.address == 64 for m in scenes[(2, ExchangePhase.ACTION)].markers)
    assert any(m.kind == "write" and m.text == "WRITE APPLIED" for m in scenes[(3, ExchangePhase.ACTION)].markers)
    assert "age 0 ticks / 2 own callbacks" in " ".join(scenes[(3, ExchangePhase.ACTION)].lines)


@pytest.mark.parametrize("center,status", [(0,"empty"),(256,"refused"),(91,"positive")])
def test_receipt_outcomes_are_observable_and_no_premature_receipt(tmp_path, center, status):
    presentation, _, _ = _presentation(tmp_path, [("sense", center)])
    presentation.step_forward()
    assert "absent" in " ".join(entrant_scene(presentation.current_view).lines)
    presentation.step_forward()
    assert "pending" in " ".join(entrant_scene(presentation.current_view).lines)
    presentation.step_forward()
    assert status in " ".join(entrant_scene(presentation.current_view).lines)


def test_adapter_no_tracking_future_state_or_hidden_pacing(tmp_path):
    a, _, _ = _presentation(tmp_path / "a", [("read",0),("sense",91)], b=[("move",8)])
    b, _, _ = _presentation(tmp_path / "b", [("read",0),("sense",91)], b=[("read",91)])
    for presentation in (a,b):
        presentation.seek_index(7)
    assert entrant_scene(a.current_view) == entrant_scene(b.current_view)
    before = a.current_view
    a.switch(False)
    a.switch(True)
    assert a.current_view == before
    a.restart()
    assert not entrant_scene(a.current_view).markers or all(m.kind == "own" for m in entrant_scene(a.current_view).markers)
    assert a.terminal_text is None
    a.jump_to_end()
    assert a.terminal_text == "Recorded end"
    a.restart()
    assert a.terminal_text is None
    assert "opponent" not in asdict(entrant_scene(a.current_view))


def test_pair_success_without_teaching_success_and_bad_optional_sidecar(tmp_path):
    _, session, _ = _presentation(tmp_path, [("read",0)])
    bad = tmp_path / "demo.json"
    bad.write_text('{"private": "DO NOT DISPLAY"}', encoding="utf-8")
    presentation, reason = load_sensing_presentation(session, tmp_path / "replay.jsonl", tmp_path / "trace.jsonl", demo=bad)
    assert not reason and presentation is not None
    assert presentation.verification.artifact_pair_consistent
    assert presentation.verification.exchange_reconstructed
    assert presentation.verification.knowledge_projected
    assert not presentation.verification.teaching_complete
    assert not presentation.sidecar_verified
    assert "DO NOT DISPLAY" not in presentation.notice


def test_complete_demo_sidecar_keeps_teaching_verification_separate(tmp_path):
    from battle_client.session import ReplaySession
    from battle_engine.sensing_demo import run_sensing_demo

    run_sensing_demo(tmp_path / "demo", ticks=3)
    replay = tmp_path / "demo/replay.jsonl"
    session = ReplaySession()
    session.load(replay)
    presentation, reason = load_sensing_presentation(
        session, replay, replay.with_name("trace.jsonl"),
        result=replay.with_name("result.json"), demo=replay.with_name("demo.json"),
    )
    assert not reason and presentation is not None
    assert presentation.sidecar_verified
    assert presentation.verification.teaching_complete
    scene = entrant_scene(presentation.current_view)
    assert "verified" not in " ".join(scene.lines).lower()
    assert presentation.terminal_text is None


def test_missing_invalid_trace_and_wrong_result_fallback(tmp_path):
    _, session, _ = _presentation(tmp_path)
    for trace, result in [(None,None),(tmp_path / "missing.jsonl",None),(tmp_path / "trace.jsonl",tmp_path / "missing_result.json")]:
        presentation, reason = load_sensing_presentation(session, tmp_path / "replay.jsonl", trace, result=result)
        assert presentation is None
        assert "Omniscient" in reason and "disabled" in reason
        assert str(tmp_path) not in reason
        assert session.loaded


def test_cli_alpha_routes_to_filtered_adapter_and_auto_associates(tmp_path, monkeypatch):
    _presentation(tmp_path)
    seen = {}
    class Renderer:
        def run(self, session, **kwargs):
            seen.update(kwargs)
    monkeypatch.setattr(cli, "_resolve_renderer", lambda name: Renderer)
    def forbidden(*args, **kwargs):
        raise AssertionError("passive projection must not load for alpha1")
    monkeypatch.setattr("battle_client.perspective.PerspectiveManager", forbidden)
    assert cli.main(["--renderer","pygame","--replay",str(tmp_path / "replay.jsonl"),"--paused"]) == 0
    assert isinstance(seen["sensing_presentation"].current_view, SensingView)
    assert seen["start_paused"]
    assert seen["sensing_presentation"].verification.artifact_pair_consistent


@pytest.mark.gui
def test_pygame_surface_events_navigation_switching_and_rewind(tmp_path):
    pg = pytest.importorskip("pygame")
    pg.init()
    try:
        renderer = SensingReplayRenderer()
        renderer.pg = pg
        renderer.screen = pg.Surface((1100,750))
        renderer.font = pg.font.SysFont("consolas",15)
        presentation, _, _ = _presentation(tmp_path)
        def key(value, mod=0):
            renderer.handle_event(pg.event.Event(pg.KEYDOWN,key=value,mod=mod), presentation)
            renderer.draw(presentation)
        key(pg.K_RIGHT)
        key(pg.K_RIGHT)
        assert any(m.kind == "request" for m in renderer.last_markers)
        key(pg.K_RIGHT)
        assert any(m.kind == "historical" for m in renderer.last_markers)
        receipt_pixels = pg.image.tobytes(renderer.screen, "RGB")
        key(pg.K_1)
        assert renderer.last_lines == ()
        key(pg.K_2)
        assert pg.image.tobytes(renderer.screen,"RGB") == receipt_pixels
        key(pg.K_HOME)
        assert not any(m.kind == "historical" for m in renderer.last_markers)
        key(pg.K_PLUS)
        assert presentation.speed == 2
        key(pg.K_SPACE)
        presentation.controller.update(.05)
        assert presentation.index == 2
        key(pg.K_SPACE)
        presentation.controller.update(100)
        assert presentation.index == 2
        renderer.draw(presentation)
        renderer.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=(1080,660)),presentation)
        assert presentation.at_end
        key(pg.K_HOME)
        assert presentation.terminal_text is None
    finally:
        pg.quit()


def test_renderer_entrant_boundary_has_no_session_or_world_arguments():
    import inspect
    assert tuple(inspect.signature(SensingReplayRenderer.draw_entrant).parameters) == ("self","view")
    assert tuple(inspect.signature(entrant_scene).parameters) == ("view",)


def test_private_input_refused_before_read(tmp_path, monkeypatch):
    _, session, _ = _presentation(tmp_path)
    private = tmp_path / "research_v6_e9" / "trace.jsonl"
    presentation, reason = load_sensing_presentation(session,tmp_path / "replay.jsonl",private)
    assert presentation is None
    assert "research_v6_e9" not in reason


@pytest.mark.gui
def test_real_sdl_sensing_loop_with_queued_interaction(tmp_path, monkeypatch):
    """Bounded real window/event/render loop, not a mock graphical proof."""
    pg = pytest.importorskip("pygame")
    _presentation(tmp_path)
    draw = SensingReplayRenderer.draw
    keys = iter([pg.K_RIGHT, pg.K_RIGHT, pg.K_RIGHT, pg.K_RIGHT,
                 pg.K_RIGHT, pg.K_RIGHT, pg.K_1, pg.K_2, pg.K_HOME,
                 pg.K_PLUS, pg.K_SPACE, pg.K_SPACE, pg.K_END])
    frames = []
    def bounded_draw(renderer, presentation):
        draw(renderer, presentation)
        frames.append((presentation.position, renderer.last_markers))
        if any(m.kind == "receipt" for m in renderer.last_markers):
            pg.image.save(renderer.screen, str(tmp_path / "receipt.png"))
        if any(m.kind == "request" for m in renderer.last_markers):
            pg.image.save(renderer.screen, str(tmp_path / "request.png"))
        if any(m.kind == "write" for m in renderer.last_markers):
            pg.image.save(renderer.screen, str(tmp_path / "write.png"))
        key = next(keys, None)
        pg.event.post(pg.event.Event(pg.QUIT) if key is None else pg.event.Event(pg.KEYDOWN, key=key, mod=0))
    monkeypatch.setattr(SensingReplayRenderer, "draw", bounded_draw)
    assert cli.main(["--renderer","pygame","--replay",str(tmp_path / "replay.jsonl"),"--paused"]) == 0
    assert len(frames) >= 13
    assert (tmp_path / "receipt.png").is_file()
    assert (tmp_path / "request.png").is_file()
    assert (tmp_path / "write.png").is_file()
