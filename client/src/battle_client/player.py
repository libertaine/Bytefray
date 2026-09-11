"""Replay iteration and renderer lifecycle orchestration.

Two playback models coexist here, deliberately kept separate rather than
forced through one shared abstraction:

``ReplayPlayer`` is unchanged since Phase 7a Slice 1/2: a one-shot forward
stream of ``ReplayRecord``s pushed into an ``AbstractRenderer``. It fits
``HeadlessRenderer`` (and any future stream-only consumer) well, and stays
the CLI's headless-mode driver.

``PlaybackController`` is new in Phase 7a Slice 3, for the interactive
Pygame viewer. Bolting seek/restart/backward-navigation onto
``ReplayPlayer``'s forward-only iterator contract would fundamentally
fight it -- an iterator cannot be asked to "go back". Interactive playback
instead drives a ``ReplaySession`` directly: ``ReplaySession`` remains the
sole source of reconstructed state (see its module docstring);
``PlaybackController`` owns only play/pause/speed and wall-clock time
accumulation, translating elapsed real time and discrete navigation
commands into calls to the session's ``step_forward``/``seek``/
``restart``. It never reconstructs state itself and never sleeps or
blocks -- a caller (the Pygame render loop) calls
``update(elapsed_seconds)`` once per frame, so the UI stays responsive
while paused and a speed change takes effect on the very next frame.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from battle_engine.replay import ReplayRecord

from battle_client.renderers.base import AbstractRenderer
from battle_client.session import ReplaySession, ReplayState


class ReplayPlayer:
    """Deliver replay records through one explicit renderer lifecycle."""

    def __init__(self, renderer: AbstractRenderer):
        self.renderer = renderer

    def play(
        self,
        records: Iterable[ReplayRecord],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        renderer = self.renderer
        try:
            renderer.setup(metadata)
            renderer.wait_for_start()

            # Keep iteration here, separate from presentation. A one-record
            # lookahead lets completion be detected without blocking a paused
            # interactive renderer after the final record.
            iterator = iter(records)
            try:
                pending = next(iterator)
            except StopIteration:
                pending = None

            while pending is not None:
                renderer.wait_until_ready()
                renderer.on_event(pending)
                renderer.update()
                try:
                    pending = next(iterator)
                except StopIteration:
                    pending = None

            renderer.on_complete()
            renderer.hold_open()
        finally:
            renderer.teardown()


SPEEDS: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
DEFAULT_SPEED_INDEX = SPEEDS.index(1.0)
DEFAULT_TICK_INTERVAL = 0.05  # seconds per tick at 1x, if the caller supplies none


class PlaybackMovementKind(str, Enum):
    """Why the replay cursor moved between rendered frames."""

    AUTOMATIC = "automatic"
    STEP_FORWARD = "step_forward"
    STEP_BACKWARD = "step_backward"
    SEEK_FORWARD = "seek_forward"
    SEEK_BACKWARD = "seek_backward"
    RESTART = "restart"
    JUMP_TO_END = "jump_to_end"


@dataclass(frozen=True)
class PlaybackMovement:
    """One explicit cursor movement reported to presentation consumers.

    ``crossed_ticks`` contains every recorded tick actually traversed by
    continuous forward playback. It is intentionally empty for seeks and
    other discontinuous navigation: their destination is still available as
    ``to_tick``, but they did not *play through* the intervening ticks.
    """

    kind: PlaybackMovementKind
    from_tick: int
    to_tick: int
    crossed_ticks: tuple[int, ...] = ()

    @property
    def presents_forward_events(self) -> bool:
        """Whether transient event presentation may use ``crossed_ticks``."""

        return self.kind in {
            PlaybackMovementKind.AUTOMATIC,
            PlaybackMovementKind.STEP_FORWARD,
        }


class PlaybackController:
    """Play/pause/speed/navigation over a loaded ``ReplaySession``.

    Deterministic replay reconstruction stays entirely in ``ReplaySession``;
    this class only decides *when* to call it, and only ever asks it for a
    tick that is genuinely recorded -- never a guessed tick number that
    might fall in a sparse legacy replay's gap. ``update(elapsed_seconds)``
    is the sole time-driven entry point: call it once per frame with the
    real elapsed time since the previous call, and it advances at most as
    many ticks as the current speed and elapsed time justify. There is no
    ``time.sleep`` anywhere in this class.

    Every discrete navigation command (step, seek, restart, jump-to-end)
    pauses automatic playback first -- a manual navigation action while
    auto-playing would otherwise immediately be overridden by the next
    ``update()`` call, which is confusing. Playback only resumes when
    ``play()`` is called explicitly.
    """

    def __init__(
        self,
        session: ReplaySession,
        *,
        tick_interval: float = DEFAULT_TICK_INTERVAL,
        playing: bool = True,
    ) -> None:
        self.session = session
        self.tick_interval = tick_interval if tick_interval > 0 else DEFAULT_TICK_INTERVAL
        self.playing = playing and not session.at_end
        self._speed_index = DEFAULT_SPEED_INDEX
        self._accumulated = 0.0
        self._pending_movements: list[PlaybackMovement] = []

    @property
    def speed(self) -> float:
        return SPEEDS[self._speed_index]

    # ---------- play/pause ----------

    def play(self) -> None:
        """Start (or resume) automatic playback.

        Pressing play at the final tick restarts from the first tick and
        begins playing. This is an explicit, user-initiated action (not
        automatic looping): the session never resumes or restarts on its
        own without a ``play()`` call.
        """
        if self.session.at_end:
            source_tick = self.session.current_tick
            self.session.restart()
            self._record_movement(PlaybackMovementKind.RESTART, source_tick)
        self.playing = True
        self._accumulated = 0.0

    def pause(self) -> None:
        self.playing = False

    def toggle_play_pause(self) -> None:
        if self.playing:
            self.pause()
        else:
            self.play()

    # ---------- speed ----------

    def speed_up(self) -> None:
        self._speed_index = min(len(SPEEDS) - 1, self._speed_index + 1)

    def speed_down(self) -> None:
        self._speed_index = max(0, self._speed_index - 1)

    def set_speed(self, value: float) -> None:
        """Snap to the closest supported speed in ``SPEEDS``.

        There is no arbitrary floating-point speed entry; this just picks
        the nearest fixed step, so an out-of-range or off-step request
        (for example from a CLI ``--speed`` flag) degrades gracefully
        instead of being rejected.
        """
        self._speed_index = min(range(len(SPEEDS)), key=lambda i: abs(SPEEDS[i] - value))

    # ---------- discrete navigation (always pauses first) ----------

    def step_forward(self) -> ReplayState:
        """Advance exactly one recorded tick. A safe no-op at the final tick."""
        self.pause()
        self._accumulated = 0.0
        source_tick = self.session.current_tick
        if self.session.at_end:
            return self.session.current_state
        state = self.session.step_forward()
        self._record_movement(
            PlaybackMovementKind.STEP_FORWARD,
            source_tick,
            crossed_ticks=(state.tick,),
        )
        return state

    def step_backward(self) -> ReplayState:
        """Move to the previous recorded tick. A safe no-op at the first tick."""
        self.pause()
        self._accumulated = 0.0
        source_tick = self.session.current_tick
        target = self._adjacent_recorded_tick(-1)
        if target is None:
            return self.session.current_state
        state = self.session.seek(target)
        self._record_movement(PlaybackMovementKind.STEP_BACKWARD, source_tick)
        return state

    def seek_to(self, tick: int) -> ReplayState:
        """Seek to one exact recorded tick and report discontinuous movement."""

        self.pause()
        self._accumulated = 0.0
        source_tick = self.session.current_tick
        if tick == source_tick:
            return self.session.current_state
        state = self.session.seek(tick)
        kind = (
            PlaybackMovementKind.SEEK_BACKWARD
            if tick < source_tick
            else PlaybackMovementKind.SEEK_FORWARD
        )
        self._record_movement(kind, source_tick)
        return state

    def seek_relative(self, delta: int) -> ReplayState:
        """Seek by roughly ``delta`` ticks (negative for backward).

        The target tick number is clamped to the replay's recorded range
        and, for a sparse legacy replay, snapped to the nearest recorded
        tick in the requested direction -- it never calls
        ``ReplaySession.seek`` with a tick that isn't actually recorded.
        """
        self.pause()
        self._accumulated = 0.0
        target = self._nearest_recorded_tick(self.session.current_tick + delta, delta)
        return self.seek_to(target)

    def restart(self) -> ReplayState:
        self.pause()
        self._accumulated = 0.0
        source_tick = self.session.current_tick
        state = self.session.restart()
        self._record_movement(PlaybackMovementKind.RESTART, source_tick)
        return state

    def jump_to_end(self) -> ReplayState:
        self.pause()
        self._accumulated = 0.0
        source_tick = self.session.current_tick
        final = self.session.final_tick
        if final is None:
            return self.session.current_state
        state = self.session.seek(final)
        self._record_movement(PlaybackMovementKind.JUMP_TO_END, source_tick)
        return state

    # ---------- frame-driven auto-advance ----------

    def update(self, elapsed_seconds: float) -> None:
        """Advance playback by ``elapsed_seconds`` of real time, if playing.

        Call once per frame with the real elapsed time since the previous
        call (for example, a Pygame clock's tick delta in seconds). Pauses
        automatically on reaching the final tick, rather than stopping
        silently with no further indication.
        """
        if not self.playing or self.session.at_end:
            return
        source_tick = self.session.current_tick
        crossed_ticks: list[int] = []
        self._accumulated += max(0.0, elapsed_seconds) * self.speed
        interval = self.tick_interval
        while self._accumulated >= interval and not self.session.at_end:
            self._accumulated -= interval
            crossed_ticks.append(self.session.step_forward().tick)
        if crossed_ticks:
            self._record_movement(
                PlaybackMovementKind.AUTOMATIC,
                source_tick,
                crossed_ticks=tuple(crossed_ticks),
            )
        if self.session.at_end:
            self.playing = False
            self._accumulated = 0.0

    def consume_movements(self) -> tuple[PlaybackMovement, ...]:
        """Return and clear cursor movements recorded since the last call."""

        movements = tuple(self._pending_movements)
        self._pending_movements.clear()
        return movements

    def reset_accumulator(self) -> None:
        """Discard any partially-accumulated tick-advance time.

        Exists for an external pacing layer (the spectator Director, see
        ``battle_client.director``) that temporarily suspends calling
        ``update()`` -- for an impact hold, for example -- and needs to
        discard the real time that passed during that suspension so it is
        not misread as a burst of accumulated ticks once ``update()``
        resumes. Ordinary playback never needs to call this directly; every
        discrete navigation method above already resets the accumulator
        inline as part of its own pause.
        """
        self._accumulated = 0.0

    # ---------- internals: recorded-tick-aware navigation ----------

    def _record_movement(
        self,
        kind: PlaybackMovementKind,
        source_tick: int,
        *,
        crossed_ticks: tuple[int, ...] = (),
    ) -> None:
        self._pending_movements.append(
            PlaybackMovement(
                kind=kind,
                from_tick=source_tick,
                to_tick=self.session.current_tick,
                crossed_ticks=crossed_ticks,
            )
        )

    def _adjacent_recorded_tick(self, direction: int) -> int | None:
        """The previous (``direction < 0``) or next (``direction > 0``)
        recorded tick relative to the session's current tick, or ``None``
        if there isn't one (already at the first/last recorded tick).
        """
        ticks = self.session.recorded_ticks
        current = self.session.current_tick
        if direction < 0:
            index = bisect.bisect_left(ticks, current) - 1
            return ticks[index] if index >= 0 else None
        index = bisect.bisect_right(ticks, current)
        return ticks[index] if index < len(ticks) else None

    def _nearest_recorded_tick(self, target: int, direction: int) -> int:
        """Snap ``target`` to a recorded tick, biased toward ``direction``
        when ``target`` itself falls in a sparse-replay gap, and always
        clamped into the replay's recorded range.
        """
        ticks = self.session.recorded_ticks
        first, last = ticks[0], ticks[-1]
        target = max(first, min(last, target))
        index = bisect.bisect_left(ticks, target)
        if index < len(ticks) and ticks[index] == target:
            return target
        if direction >= 0:
            return ticks[index] if index < len(ticks) else ticks[-1]
        return ticks[index - 1] if index > 0 else ticks[0]
