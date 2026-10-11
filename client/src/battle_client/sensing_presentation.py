"""Trusted launch/navigation adapter and receipt-only presentation primitives.

The entrant drawing function consumes SensingView only. This adapter owns the
cursor, artifact checks and terminal gate; operator verdicts are separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from battle_engine.sensing_playback import ExchangePhase

from battle_client.player import PhasePlaybackController
from battle_client.sensing import (
    OmniscientView,
    PhasePosition,
    SensingCursor,
    SensingProjectionError,
    SensingView,
    VerificationSummary,
)
from battle_client.session import ReplaySession


@dataclass(frozen=True)
class SensingMarker:
    kind: str
    address: int
    text: str
    origin: int | None = None
    half_width: int = 0


@dataclass(frozen=True)
class EntrantScene:
    label: str
    phase: str
    lines: tuple[str, ...]
    markers: tuple[SensingMarker, ...]


def entrant_scene(view: SensingView) -> EntrantScene:
    """Format facts already filtered upstream; no raw-world input is accepted."""
    markers = [SensingMarker("own", p.anchor, f"Own {p.process_id}") for p in view.own_processes]
    lines = ["Opponent state unknown outside delivered historical samples."]
    lines.append(f"Receipt now: {view.receipt_status.value.lower()}")
    lines.append("Own anchors: " + ", ".join(f"process {p.process_id} at {p.anchor} (reach {p.reach})" for p in view.own_processes))
    for contact in view.contacts:
        text = (
            f"Anonymous sample at {contact.address}; sampled t{contact.sampled_at.tick} "
            f"callback {contact.sampled_at.callback}, received t{contact.received_at.tick} callback {contact.received_at.callback}; "
            f"age {contact.age_ticks} ticks / {contact.age_callbacks} own callbacks"
        )
        if contact.not_present_in_newer_sample is not None:
            text += "; absent in newer scan"
        lines.append(text)
        markers.append(SensingMarker("historical", contact.address, text))
    lines.append("Recent recorded own events (past requests may already be delivered):")
    for event in view.events[-4:]:
        lines.append(
            f"Callback {event.position.callback}: {event.kind.upper()} {event.address if event.address is not None else ''} "
            f"{event.status or ''} "
            f"{('value=' + str(event.value)) if event.value is not None else ''}; {event.message}"
        )
    # Keep a request ring until this process receives its actual delayed sample.
    for process in view.own_processes:
        pending = next((e for e in reversed(view.events) if e.process_id == process.process_id and (e.kind == "sense" or e.sample_status.value in {"REFUSED", "EMPTY", "POSITIVE"})), None)
        if pending is not None and pending.kind == "sense" and pending.address is not None:
            markers.append(SensingMarker("request", pending.address, "SENSE: 1 action; pending", half_width=27))
    if view.events:
        event = view.events[-1]
        if event.kind == "move" and event.status == "APPLIED":
            moved_process = next((p for p in view.own_processes if p.process_id == event.process_id), None)
            if moved_process is not None and event.operand is not None:
                origin = (moved_process.anchor - event.operand) % view.arena_size
                markers.append(SensingMarker("move", moved_process.anchor, "Applied MOVE", origin=origin))
        if event.kind == "write" and event.address is not None:
            markers.append(SensingMarker("write", event.address, f"WRITE {event.status}"))
        if event.sample_status.value in {"REFUSED", "EMPTY", "POSITIVE"} and view.samples:
            sample = view.samples[-1]
            markers.append(SensingMarker("receipt", sample.center, event.sample_status.value.lower()))
            lines.append(
                f"Receipt: {sample.status.value.lower()}; window {sample.center} +/- {sample.half_width}; "
                f"process {sample.sampled_at.process_id}; sampled t{sample.sampled_at.tick} callback {sample.sampled_at.callback}, "
                f"delivered t{sample.received_at.tick} callback {sample.received_at.callback}"
            )
    lines.append("Delivered scan history (newest receipt first):")
    for sample in reversed(view.samples):
        lines.append(
            f"Scan {sample.status.value.lower()}: center {sample.center} +/- {sample.half_width}; "
            f"anonymous addresses {sample.addresses}; process {sample.sampled_at.process_id}; "
            f"sampled t{sample.sampled_at.tick} callback {sample.sampled_at.callback}; "
            f"received t{sample.received_at.tick} callback {sample.received_at.callback}"
        )
    lines.append("Delivered READ history (owners do not identify anonymous contacts):")
    for read in reversed(view.reads):
        lines.append(
            f"READ {read.address}: value {read.value}, owner {read.owner or 'none'}; "
            f"process {read.sampled_at.process_id}; sampled t{read.sampled_at.tick} callback {read.sampled_at.callback}; "
            f"received t{read.received_at.tick} callback {read.received_at.callback}"
        )
    point = view.position
    phase = f"Tick {point.tick} / own callback {point.callback or '-'} / {point.phase.value}"
    return EntrantScene(view.label, phase, tuple(lines), tuple(markers))


class SensingPresentation:
    """Navigation control plane; provides a filtered scene to entrant rendering."""

    def __init__(self, cursor: SensingCursor, terminal: str, *, interval: float):
        self.controller = PhasePlaybackController(cursor, phase_interval=interval)
        self.verification: VerificationSummary = cursor.verification_report()
        self.sidecar_verified = False
        self.notice = "Factual replay; starter strategy explanations unavailable."
        self._terminal = terminal
        self._entrant = "A"

    @property
    def current_view(self) -> SensingView | OmniscientView:
        return self.controller.current_view

    @property
    def position(self) -> PhasePosition:
        view = self.current_view
        if isinstance(view, SensingView):
            return view.position
        return PhasePosition(view.tick, view.global_decision_index, view.phase)

    @property
    def index(self) -> int:
        return self.controller.positions.index(self.position)

    @property
    def at_end(self) -> bool:
        return self.index == len(self.controller.positions) - 1

    @property
    def terminal_text(self) -> str | None:
        return self._terminal if self.at_end else None

    def seek_index(self, index: int) -> None:
        positions = self.controller.positions
        self.controller.seek_to(positions[max(0, min(index, len(positions) - 1))])

    def seek_relative(self, ticks: int) -> None:
        target = self.position.tick + ticks
        positions = self.controller.positions
        candidates = [p for p in positions if p.phase == ExchangePhase.TICK_END]
        nearest = min(candidates, key=lambda p: abs(p.tick - target))
        self.controller.seek_to(nearest)

    def jump_to_end(self) -> None:
        self.seek_index(len(self.controller.positions) - 1)

    def switch(self, entrant: bool) -> None:
        self.controller.switch_view(self._entrant if entrant else None)

    # Same keyboard contract as the existing tick playback controller.
    @property
    def speed(self) -> float:
        return self.controller.speed

    def toggle_play_pause(self) -> None:
        self.controller.toggle_play_pause()

    def step_forward(self) -> None:
        self.controller.step_forward()

    def step_backward(self) -> None:
        self.controller.step_backward()

    def restart(self) -> None:
        self.controller.restart()

    def speed_up(self) -> None:
        self.controller.speed_up()

    def speed_down(self) -> None:
        self.controller.speed_down()


def load_sensing_presentation(
    session: ReplaySession, replay: Path, trace: Path | None, *,
    result: Path | None = None, demo: Path | None = None, interval: float = 0.05,
) -> tuple[SensingPresentation | None, str]:
    if trace is None:
        return None, "Omniscient — replay only. Trace unavailable; delivered perspective disabled."
    # A broken optional sidecar cannot disable a consistent ordinary match.
    cursor = None
    sidecar_verified = False
    if demo is not None:
        try:
            cursor = SensingCursor.from_paths(session, replay, trace, result_path=result, demo_path=demo)
            sidecar_verified = True
        except SensingProjectionError:
            pass
    if cursor is None:
        try:
            cursor = SensingCursor.from_paths(session, replay, trace, result_path=result)
        except SensingProjectionError:
            return None, "Omniscient — replay only. Exchange evidence invalid; delivered perspective disabled."
    terminal_result = session.result
    terminal = (
        f"Recorded end: winner {terminal_result.winner}; {terminal_result.termination_reason}"
        if terminal_result is not None else "Recorded end reached."
    )
    presentation = SensingPresentation(cursor, terminal, interval=interval)
    presentation.sidecar_verified = sidecar_verified
    if demo is not None and not sidecar_verified:
        presentation.notice = "Optional demonstration invalid; factual replay remains available."
    return presentation, ""
