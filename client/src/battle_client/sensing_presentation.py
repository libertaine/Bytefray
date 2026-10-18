"""Trusted launch/navigation adapter and receipt-only presentation primitives.

The entrant drawing function consumes SensingView only. This adapter owns the
cursor, artifact checks and terminal gate; operator verdicts are separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from battle_engine.rules import BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.ruleset_names import ACTIVE_SENSING_DISPLAY_NAME, ruleset_name_with_id
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

# Explicit perspective choices: an entrant ID selects that entrant's delivered
# view; None selects omniscience. The order is the V/P cycle and the number-key
# mapping (1 -> Omni, 2 -> A, 3 -> B); SELECTOR_ORDER is the on-screen order.
PERSPECTIVE_ORDER: tuple[str | None, ...] = (None, "A", "B")
SELECTOR_ORDER: tuple[str | None, ...] = ("A", "B", None)
DELIVERED_ENTRANTS: tuple[str, ...] = ("A", "B")
PERSPECTIVE_LABELS: dict[str | None, str] = {
    "A": "Agent A — delivered information",
    "B": "Agent B — delivered information",
    None: "Omniscient — full world state",
}
SELECTOR_LABELS: dict[str | None, str] = {"A": "A", "B": "B", None: "Omni"}


@dataclass(frozen=True)
class SensingMarker:
    kind: str
    address: int
    text: str
    origin: int | None = None
    half_width: int = 0
    # Own callback at which a historical sample was taken; orders map labels.
    sampled_callback: int = 0


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
        markers.append(
            SensingMarker("historical", contact.address, text, sampled_callback=contact.sampled_at.callback)
        )
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
        view = self.controller.current_view
        self._selected: str | None = view.entrant_id if isinstance(view, SensingView) else None
        # Most recently selected delivered entrant; the legacy switch(True) target.
        self._entrant = self._selected or "A"

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

    @property
    def selected(self) -> str | None:
        """Selected entrant ID for a delivered view, or None for omniscience."""
        return self._selected

    def select(self, entrant_id: str | None) -> None:
        """Rebuild the cursor for one explicit perspective at the mapped position.

        The new cursor keeps only the selected entrant's permitted prefix, so no
        receipt, history or scroll state from the previous perspective survives.
        """
        if entrant_id not in PERSPECTIVE_LABELS:
            raise ValueError("Unknown sensing perspective.")
        self.controller.switch_view(entrant_id)
        self._selected = entrant_id
        if entrant_id is not None:
            self._entrant = entrant_id

    def cycle(self) -> None:
        """V/P convention: Omni -> A -> B -> Omni."""
        index = PERSPECTIVE_ORDER.index(self._selected)
        self.select(PERSPECTIVE_ORDER[(index + 1) % len(PERSPECTIVE_ORDER)])

    def switch(self, entrant: bool) -> None:
        """Compatibility toggle: the last selected delivered entrant or Omni."""
        self.select(self._entrant if entrant else None)

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
        return None, "Omniscient — replay only. Trace unavailable; delivered perspectives disabled."
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
            return None, "Omniscient — replay only. Exchange evidence invalid; delivered perspectives disabled."
    # Both entrants share one availability decision: if either delivered
    # projection cannot be built, neither is offered (no partial fallback).
    # The cursor above already projects Agent A, so only B needs a rebuild.
    for entrant_id in (entrant for entrant in DELIVERED_ENTRANTS if entrant != "A"):
        try:
            cursor.switch_view(entrant_id)
        except SensingProjectionError:
            return None, "Omniscient — replay only. Exchange evidence invalid; delivered perspectives disabled."
    cursor.restart()  # re-synchronize the shared session after the probes
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


# --- Static Alpha 1 help content (M2-4 Q1/Q2) ---------------------------------
# One shared definition rendered unchanged by replay Help and the Designer's
# sensing guide. It never reads a replay, view or session, so it cannot state
# hidden or current match state, and no viewer selects or badges a card.


@dataclass(frozen=True)
class ScenarioCard:
    """A static teaching card keyed to one reviewed policy and fixture input."""

    title: str
    starter: str
    starter_digest: str
    parameters: tuple[tuple[str, int], ...]
    fixture: str
    fixture_digest: str
    predicate: str
    rule: str
    evidence: str
    paid_alternative: str
    not_proven: str
    look_for: str

    def lines(self) -> tuple[str, ...]:
        params = ", ".join(f"{name}={value}" for name, value in self.parameters)
        return (
            self.title,
            (
                f"Reviewed inputs: bundled starter {self.starter} (content digest {self.starter_digest}) "
                f"with default parameters {params}; fixture {self.fixture} (content digest "
                f"{self.fixture_digest}); predicate {self.predicate}; {ALPHA1_TEACHING_PROFILE}."
            ),
            "Policy rule: " + self.rule,
            "Evidence it receives: " + self.evidence,
            "Paid action alternative: " + self.paid_alternative,
            "What its observations do not prove: " + self.not_proven,
            "What to look for: " + self.look_for,
            CARD_SCOPE_NOTE,
        )


ALPHA1_TEACHING_PROFILE = (
    "Ruleset bytefray-rules-6-alpha1, arena 512, 8 actions per tick, seed 0, 100-tick limit"
)

CARD_SCOPE_NOTE = (
    "Scope: this card describes only the bundled revision with these inputs. A personal copy, "
    "edited parameters or an ordinary seeded match can behave differently, and opening a replay "
    "does not verify that it shows this scenario."
)

ALPHA1_SENSING_GUIDE: tuple[str, ...] = (
    f"{ACTIVE_SENSING_DISPLAY_NAME}: reading these replays (informational summary)",
    (
        "Paid active sensing: SENSE uses one ordinary action opportunity, like READ, WRITE or MOVE. "
        "It reports anonymous enemy anchor addresses within +/-27 cells of a legal center, with no "
        "identity, core, damage or notification."
    ),
    (
        "Sample and delayed receipt: a scan samples the arena when its action happens; the result is "
        "delivered later, at that process's next eligible callback. Replays show the sampled point and "
        "the received point separately."
    ),
    (
        "Anonymous locations and information age: a delivered address is a historical sample, not a "
        "tracked opponent. Each sample keeps its sampled tick, callback and age; nothing expires or "
        "refreshes by itself, and an address missing from a newer scan is absent in that sample only."
    ),
    (
        "Competing action opportunities: each callback allows one action, so a SENSE replaces a READ, "
        "WRITE or MOVE at that opportunity, and an empty scan still used it."
    ),
    (
        "Delivered versus omniscient: the Agent A and Agent B views show only what that entrant received, "
        "at its own callbacks. The Omniscient view shows the full world state, including information "
        "neither agent had."
    ),
    (
        "This summary is informational. The Ruleset and the recorded artifacts remain authoritative; "
        f"{ruleset_name_with_id(BYTEFRAY_RULESET_V4_ID)} stays the default, and "
        f"{ACTIVE_SENSING_DISPLAY_NAME} is {BYTEFRAY_RULESET_V6_ALPHA1_ID} and must be selected "
        "explicitly."
    ),
)

SCENARIO_CARDS: tuple[ScenarioCard, ...] = (
    ScenarioCard(
        title="Scenario card: Watchful Keeper",
        starter="v6_watchful_keeper",
        starter_digest="35b945ad33f34168ea4374dad05fa61fe5b20d08cc15ca2e9af293ebb0c8016e",
        parameters=(("scan_interval", 4), ("perimeter_offset", 27)),
        fixture="v6_encroaching_opponent",
        fixture_digest="42763e704cc723e435af2f2822d90ad972c4cbdea8e3ada8322d6b07f8f24456",
        predicate="keeper-K1",
        rule=(
            "each callback takes one action, in priority order: (1) if its previous READ of an own-core "
            "cell was delivered with a different owner, WRITE 0x4b to that cell (a repair attempt); "
            "(2) otherwise, if its previous SENSE delivered a nonempty receipt, WRITE 0x4b once to the "
            "smallest sampled address in reach (a defensive attempt on an old sample); (3) otherwise, "
            "when scan_interval is due, SENSE own core + perimeter_offset; (4) otherwise READ the next "
            "own-core cell."
        ),
        evidence=(
            "the delivered value and last-writer owner of the own-core cell it READ, and delayed "
            "anonymous SENSE receipts; each arrives at its next eligible callback."
        ),
        paid_alternative=(
            "a perimeter SENSE uses the opportunity that would otherwise READ the next core cell, and "
            "a repair or defensive WRITE likewise delays inspection."
        ),
        not_proven=(
            "a different owner justifies a repair attempt but does not identify any sensed process; a "
            "SENSE receipt supports a perimeter WRITE attempt without proving damage, identity or a "
            "hit; an applied WRITE proves a write, not a hit or a lasting repair."
        ),
        look_for=(
            "point to the delivered READ or SENSE receipt behind each WRITE, tell its sampled point from "
            "its received point, and name the action it displaced."
        ),
    ),
    ScenarioCard(
        title="Scenario card: Roaming Reacquirer",
        starter="v6_roaming_reacquirer",
        starter_digest="65866988dd2dfdddd9782a8040d932dc84f05cec9b5d6feab3fb6a73c9697f21",
        parameters=(("search_offset", 91), ("move_step", 64), ("rescan_wait", 3)),
        fixture="v6_relocating_opponent",
        fixture_digest="d5331833880756a98ea952b98a6c849c4c04234b46b5271a252bb771339a6ddd",
        predicate="reacquirer-R1",
        rule=(
            "SENSE own anchor + search_offset. After a positive receipt, keep the smallest address as a "
            "historical target and spend rescan_wait paid READs before rescanning it. If a delivered "
            "rescan omits that address, record only that it is absent in the newer sample, MOVE forward "
            "by move_step and search again. A later positive receipt is a new anonymous contact: WRITE "
            "0x52 once if it is in reach, otherwise MOVE toward it by at most move_step."
        ),
        evidence=(
            "delayed anonymous SENSE receipts, each with its sampled and received point, and its own "
            "anchor; its wait READs return ordinary local values, not opponent knowledge."
        ),
        paid_alternative=(
            "every wait READ, rescan, MOVE and new SENSE costs one opportunity, so waiting delays the "
            "rescan and searching delays a response."
        ),
        not_proven=(
            "an old address absent from a newer sample does not prove that the opponent moved or "
            "disappeared; a new contact is not shown to be the same process; a response WRITE answers "
            "a historical coordinate and is not tracking."
        ),
        look_for=(
            "point to the applied rescan that omits the old address, then the paid MOVE and new SENSE "
            "that find a new anonymous contact, and say which receipt each decision used."
        ),
    ),
)


def sensing_guide_lines() -> tuple[str, ...]:
    """The complete static guide: collective description, then both cards."""
    lines: list[str] = list(ALPHA1_SENSING_GUIDE)
    for card in SCENARIO_CARDS:
        lines.append("")
        lines.extend(card.lines())
    return tuple(lines)
