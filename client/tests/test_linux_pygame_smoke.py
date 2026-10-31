from __future__ import annotations

import pytest
from battle_client import cli
from battle_engine.cli import main as engine_main
from battle_engine.replay import TickSnapshot, iter_replay


@pytest.mark.gui
def test_pygame_renders_replay_and_exits_on_quit(tmp_path, monkeypatch):
    pygame = pytest.importorskip("pygame")

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    replay = tmp_path / "replay.jsonl"
    assert engine_main(
        [
            "--ticks", "3", "--arena", "512", "--seed", "1",
            "--ruleset", "bytefray-rules-6-alpha1", "--a-type", "v6_window_scout",
            "--b-type", "v6_watchful_keeper", "--replay", str(replay), "--quiet",
        ]
    ) == 0

    # Quit only after a real frame reaches the display: a QUIT posted
    # during window setup would exit before the first redraw/flip.
    original_flip = pygame.display.flip
    rendered_frames = 0

    def flip_then_quit():
        nonlocal rendered_frames
        assert pygame.display.get_surface() is not None
        original_flip()
        rendered_frames += 1
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    monkeypatch.setattr(pygame.display, "flip", flip_then_quit)
    assert cli.main(["--replay", str(replay), "--renderer", "pygame"]) == 0
    assert rendered_frames == 1
    assert not pygame.get_init()


@pytest.mark.gui
def test_pygame_step_and_seek_advance_a_real_replay(tmp_path, monkeypatch):
    pygame = pytest.importorskip("pygame")
    from battle_client.renderers.pygame_renderer import PygameRenderer

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    replay = tmp_path / "replay.jsonl"
    # Use the installed Active Sensing roster and deterministic seeded core
    # placement in its supported arena. Verify the replay actually reaches
    # tick 2 before testing two forward steps and one backward step.
    assert engine_main(
        [
            "--ticks", "5", "--arena", "512", "--seed", "1",
            "--ruleset", "bytefray-rules-6-alpha1", "--a-type", "v6_window_scout",
            "--b-type", "v6_watchful_keeper", "--replay", str(replay), "--quiet",
        ]
    ) == 0
    ticks = [record.tick for record in iter_replay(replay) if isinstance(record, TickSnapshot)]
    assert ticks[:3] == [0, 1, 2]

    seen_ticks: list[int] = []
    original_loop = PygameRenderer._loop

    def loop_and_record(self, controller):
        # pygame.event.get() returns every queued event in one call, so
        # posting several events upfront would deliver them all within a
        # single frame rather than spreading them across frames. Instead,
        # fake one event arriving per frame, recording the session's tick
        # before each frame's event is processed -- this drives the
        # *real* event/render loop and dispatch_key logic, proving real
        # keyboard input reaches ReplaySession through PlaybackController.
        pending = [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0),  # step to tick 1
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0),  # step to tick 2
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0),  # step back to tick 1
            pygame.event.Event(pygame.QUIT),
        ]

        def fake_get(*args, **kwargs):
            seen_ticks.append(controller.session.current_tick)
            return [pending.pop(0)] if pending else []

        monkeypatch.setattr(pygame.event, "get", fake_get)
        original_loop(self, controller)

    monkeypatch.setattr(PygameRenderer, "_loop", loop_and_record)
    # --paused: no auto-advance from PlaybackController.update() should
    # interfere with the manual stepping being verified here.
    assert cli.main(["--replay", str(replay), "--renderer", "pygame", "--paused"]) == 0
    assert not pygame.get_init()
    assert seen_ticks == [0, 1, 2, 1]
