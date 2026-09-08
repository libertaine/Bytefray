from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from battle_engine.paths import canonical_replay_directory, get_data_root
from battle_engine.replay import ReplayFormatError

from battle_client.player import DEFAULT_TICK_INTERVAL, SPEEDS, ReplayPlayer
from battle_client.renderers.base import RendererDependencyError
from battle_client.renderers.headless import HeadlessRenderer
from battle_client.session import ReplaySession, ReplaySessionError
from battle_client.utils import iter_jsonl, maybe_load_summary, paced

# Pygame renderer is optional; import lazily. It is intentionally *not*
# AbstractRenderer-shaped (see battle_client.player's module docstring), so
# RENDERERS/_resolve_renderer below are typed loosely (type[Any]) rather
# than falsely claiming every entry is an AbstractRenderer subclass.
_PYGAME_CLASS: type[Any] | None = None


def _get_pygame_renderer_cls() -> type[Any]:
    global _PYGAME_CLASS
    if _PYGAME_CLASS is None:
        from battle_client.renderers.pygame_renderer import PygameRenderer

        _PYGAME_CLASS = PygameRenderer
    return _PYGAME_CLASS


RENDERERS: dict[str, type[Any] | Callable[[], type[Any]]] = {
    "headless": HeadlessRenderer,
    "pygame": _get_pygame_renderer_cls,  # resolved when selected
}


def _resolve_renderer(name: str) -> type[Any]:
    if name not in RENDERERS:
        raise SystemExit(
            f"Unknown renderer '{name}'. Choose from: {', '.join(sorted(RENDERERS))}"
        )
    cls_or_factory = RENDERERS[name]
    if isinstance(cls_or_factory, type):
        return cls_or_factory
    else:
        return cls_or_factory()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="bytefray replay",
        description="Bytefray replay client -- presentation only (replay visualizer)",
    )
    p.add_argument(
        "--replay",
        required=False,
        default=None,
        help=(
            "Path to a Bytefray replay file. Omitting this with "
            "--renderer pygame opens the interactive viewer's empty state, "
            "which lets the user pick one; every other renderer still "
            "requires it up front."
        ),
    )
    p.add_argument(
        "--renderer",
        default="headless",
        choices=list(RENDERERS.keys()),
        help="Renderer to use (default: headless)",
    )
    p.add_argument(
        "--tick-delay",
        type=float,
        default=0.0,
        help=(
            "For --renderer headless: seconds to sleep between streamed "
            "records (0 = no delay). For --renderer pygame: the "
            "interactive viewer's base seconds-per-tick at 1x speed "
            f"(0 defaults to {DEFAULT_TICK_INTERVAL:g}); the viewer's own "
            "in-window speed control scales this at runtime, it does not "
            "replace it."
        ),
    )
    p.add_argument(
        "--start-tick",
        type=int,
        default=None,
        help="--renderer pygame only: open positioned at this tick "
        "(snapped to the nearest recorded tick, clamped to range)",
    )
    p.add_argument(
        "--paused",
        action="store_true",
        help="--renderer pygame only: open paused instead of playing",
    )
    p.add_argument(
        "--speed",
        type=float,
        default=None,
        help="--renderer pygame only: initial playback speed multiplier "
        f"(snapped to the nearest of {list(SPEEDS)})",
    )
    p.add_argument(
        "--trace",
        type=Path,
        default=None,
        help="--renderer pygame only: path to bound API-v2 trace JSONL for perspective viewing",
    )
    p.add_argument(
        "--perspective",
        type=str,
        default=None,
        help="--renderer pygame only: initial entrant perspective ('broadcast' or entrant ID like 'A')",
    )
    p.add_argument(
        "--director",
        action="store_true",
        help="--renderer pygame only: enable automatic Director playback pacing "
        "(requires a trace; off by default -- press G in-viewer to toggle)",
    )
    p.add_argument(
        "--fight-night",
        action="store_true",
        help="--renderer pygame only: enable Fight Night broadcast presentation "
        "(requires a trace; off by default -- press N in-viewer to toggle)",
    )
    args = p.parse_args(argv)

    if args.replay is None:
        # Only the interactive Pygame viewer has a "no replay yet" state to
        # show (UX-20/21/22) -- a one-shot streaming renderer has nothing
        # to stream without a path, so its --replay requirement stays as
        # strict as it always was.
        if args.renderer != "pygame":
            p.error("--replay is required for --renderer " + args.renderer)
        return _run_interactive_empty_state(args)

    replay_path = Path(args.replay).expanduser().resolve()
    if not replay_path.exists():
        p.error(f"Replay not found: {replay_path}")

    if args.renderer == "pygame":
        return _run_interactive(args, replay_path)
    return _run_streaming(args, replay_path)


def _run_streaming(args: argparse.Namespace, replay_path: Path) -> int:
    """The original one-shot forward-stream path: headless (and any future
    stream-only renderer registered in RENDERERS).
    """
    metadata = maybe_load_summary(replay_path)
    RendererClass = _resolve_renderer(args.renderer)
    renderer = RendererClass()  # type: ignore[call-arg]

    try:
        ReplayPlayer(renderer).play(paced(iter_jsonl(replay_path), args.tick_delay), metadata)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except RendererDependencyError as e:
        print(f"[battle_client] dependency error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[battle_client] error: {e}", file=sys.stderr)
        return 1

    return 0


def _load_session_or_error(replay_path: Path) -> tuple[ReplaySession | None, str | None]:
    """Load ``replay_path`` into a fresh ``ReplaySession``, or report why not.

    Shared by both the direct ``--replay <path>`` entry point and the
    empty-state "Open Replay..." picker (``_run_interactive_empty_state``)
    so there is exactly one replay-loading call site for the interactive
    viewer, not two subtly different ones.
    """
    session = ReplaySession()
    try:
        session.load(replay_path)
    except (ReplaySessionError, ReplayFormatError) as e:
        return None, str(e)
    return session, None


def _run_interactive(args: argparse.Namespace, replay_path: Path) -> int:
    """The interactive Pygame path: ReplaySession + PlaybackController,
    bypassing ReplayPlayer's forward-only stream entirely (see
    battle_client.player's module docstring for why).
    """
    session, error = _load_session_or_error(replay_path)
    if session is None:
        print(f"[battle_client] error: {error}", file=sys.stderr)
        return 1
    return _run_interactive_with_session(args, replay_path, session)


def _run_interactive_empty_state(args: argparse.Namespace) -> int:
    """No ``--replay`` was given: show the empty state and let the user
    pick one (UX-20/21/22), reusing the exact same loading/playback path a
    direct ``--replay <path>`` invocation uses once a path is chosen.

    Returns 0 if the user closes the picker window without choosing a
    replay -- a normal, non-error outcome, not a failure to report.
    """
    try:
        import pygame
    except ImportError as e:
        print(
            "[battle_client] dependency error: Pygame not available. "
            "Install pygame or choose --renderer headless.",
            file=sys.stderr,
        )
        raise SystemExit(2) from e

    from battle_client.renderers.replay_picker import run_empty_state

    initial_directory = canonical_replay_directory(get_data_root())
    message = ""
    while True:
        chosen = run_empty_state(
            pygame,
            title="Bytefray - Replay Viewer",
            initial_directory=initial_directory,
            message=message,
        )
        if chosen is None:
            pygame.quit()
            return 0
        session, error = _load_session_or_error(chosen)
        if session is None:
            # Stay in the empty-state loop rather than exiting, and show the
            # reason *in the reopened window* (not just stderr): a Windows
            # user launched from the Start Menu has no terminal to read a
            # stderr message from, so an invalid pick must be recoverable
            # and explained in the window itself, not silently retried.
            print(f"[battle_client] error: {error}", file=sys.stderr)
            message = f"Couldn't open {chosen.name}: not a valid Bytefray replay."
            initial_directory = chosen.parent
            continue
        return _run_interactive_with_session(args, chosen, session)


def _run_interactive_with_session(
    args: argparse.Namespace, replay_path: Path, session: ReplaySession
) -> int:
    tick_interval = args.tick_delay if args.tick_delay > 0 else DEFAULT_TICK_INTERVAL
    RendererClass = _resolve_renderer("pygame")
    renderer = RendererClass()  # type: ignore[call-arg]

    trace_path: Path | None = None
    if args.trace is not None:
        trace_path = Path(args.trace).expanduser().resolve()
    else:
        candidate = replay_path.with_name("trace.jsonl")
        if candidate.is_file():
            trace_path = candidate

    perspective_manager = None
    if trace_path is not None:
        from battle_client.perspective import PerspectiveManager

        perspective_manager = PerspectiveManager(
            replay_path,
            trace_path,
            initial_mode=args.perspective or "broadcast",
        )

    # DirectorManager is built from the PerspectiveManager's already-computed
    # SpectatorDerivation (Sec. 25/27) rather than re-running verify_pair/
    # derive_events -- it never pays that cost a second time. Constructed
    # even when --director was not passed (building a plan is a cheap single
    # pass over already-derived events, not the expensive analysis pass), so
    # the in-viewer G key can turn Director on without a restart; only the
    # *initial* enabled state depends on the flag.
    from battle_client.director import DirectorManager

    director_manager = None
    if trace_path is not None:
        director_manager = DirectorManager(
            perspective_manager.derivation if perspective_manager is not None else None,
            unavailable_reason=(
                perspective_manager.status_message if perspective_manager is not None else None
            ),
        )
    if args.director and (director_manager is None or not director_manager.available):
        reason = director_manager.status_message if director_manager is not None else (
            "no trace supplied and no companion trace.jsonl beside "
            f"{replay_path.name}."
        )
        print(f"[battle_client] Director unavailable: {reason}", file=sys.stderr)

    # Fight Night is built from the same shared SpectatorDerivation, on the
    # same terms as the Director above: constructed whenever a trace exists so
    # the in-viewer N key works without a restart, with only the *initial*
    # enabled state depending on the flag. The two features are independent --
    # neither manager is required for the other to be built or enabled.
    from battle_client.fight_night import FightNightManager

    fight_night_manager = None
    if trace_path is not None:
        fight_night_manager = FightNightManager(
            perspective_manager.derivation if perspective_manager is not None else None,
            unavailable_reason=(
                perspective_manager.status_message if perspective_manager is not None else None
            ),
        )
    if args.fight_night and (fight_night_manager is None or not fight_night_manager.available):
        reason = fight_night_manager.status_message if fight_night_manager is not None else (
            "no trace supplied and no companion trace.jsonl beside "
            f"{replay_path.name}."
        )
        print(f"[battle_client] Fight Night unavailable: {reason}", file=sys.stderr)

    # An explicitly requested perspective must never fail silently.  The viewer
    # still opens on the canonical replay -- ordinary replay never depends on a
    # trace -- but the user is told why Perspective Cam is not available rather
    # than being dropped into broadcast with no explanation.
    if args.perspective is not None or args.trace is not None:
        if perspective_manager is None:
            print(
                "[battle_client] Perspective Cam unavailable: no trace supplied and no "
                f"companion trace.jsonl beside {replay_path.name}.",
                file=sys.stderr,
            )
        elif not perspective_manager.available:
            print(f"[battle_client] {perspective_manager.status_message}", file=sys.stderr)
        elif args.perspective is not None and not perspective_manager.is_mode_valid(
            args.perspective
        ):
            available = ", ".join(("broadcast", *perspective_manager.entrants))
            print(
                f"[battle_client] Unknown perspective {args.perspective!r}; "
                f"available: {available}. Showing broadcast.",
                file=sys.stderr,
            )
        elif args.perspective is not None and perspective_manager.mode != args.perspective:
            # is_mode_valid passed (a real entrant), but the manager's own
            # attempt to select it during construction did not stick -- that
            # entrant's lazy projection load failed.
            load_error = perspective_manager.load_error_for(args.perspective)
            print(
                f"[battle_client] Perspective {args.perspective!r} unavailable: "
                f"{load_error}. Showing broadcast.",
                file=sys.stderr,
            )

    try:
        renderer.run(
            session,
            tick_interval=tick_interval,
            start_tick=args.start_tick,
            start_paused=args.paused,
            initial_speed=args.speed,
            perspective_manager=perspective_manager,
            initial_perspective=args.perspective,
            director_manager=director_manager,
            initial_director_enabled=args.director,
            fight_night_manager=fight_night_manager,
            initial_fight_night_enabled=args.fight_night,
        )
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except RendererDependencyError as e:
        print(f"[battle_client] dependency error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[battle_client] error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
