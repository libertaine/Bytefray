"""Receipt-only V6 knowledge and phase navigation over M1-3 verified facts.

The cursor is a trusted adapter, not a renderer payload. Entrant consumers get
only SensingView: no replay state, global indices, binding, or raw facts. Tick
agreement and teaching verification are separate control-plane checks.
"""

from __future__ import annotations

import bisect
import copy
import hashlib
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.sensing_playback import (
    ExchangePhase,
    SensingPlayback,
    SubTickWorldState,
    VerificationStatus,
    reconstruct_sensing_playback,
    verify_demonstration_artifacts,
)

from battle_client.session import ReplaySession


class SensingProjectionError(ValueError):
    """Generic failure safe to present without hidden evidence details."""


class SampleStatus(str, Enum):
    ABSENT = "ABSENT"
    PENDING = "PENDING"
    REFUSED = "REFUSED"
    EMPTY = "EMPTY"
    POSITIVE = "POSITIVE"


@dataclass(frozen=True)
class PhasePosition:
    """Entrant-local callback ordinal (one based), never a global index."""

    tick: int
    callback: int | None
    phase: ExchangePhase


@dataclass(frozen=True)
class KnowledgePoint:
    tick: int
    callback: int
    process_id: str


@dataclass(frozen=True)
class SensingSample:
    center: int
    half_width: int
    status: SampleStatus
    addresses: tuple[int, ...]
    sampled_at: KnowledgePoint
    received_at: KnowledgePoint


@dataclass(frozen=True)
class HistoricalContact:
    address: int
    sampled_at: KnowledgePoint
    received_at: KnowledgePoint
    age_ticks: int
    age_callbacks: int
    not_present_in_newer_sample: KnowledgePoint | None = None


@dataclass(frozen=True)
class DeliveredRead:
    address: int
    value: int
    owner: str | None
    sampled_at: KnowledgePoint
    received_at: KnowledgePoint


@dataclass(frozen=True)
class OwnProcess:
    process_id: str
    anchor: int
    reach: int


@dataclass(frozen=True)
class KnowledgeEvent:
    position: PhasePosition
    process_id: str
    kind: str
    address: int | None = None
    operand: int | None = None
    value: int | None = None
    cost: int = 0
    status: str | None = None
    sample_status: SampleStatus = SampleStatus.ABSENT
    message: str = ""


@dataclass(frozen=True)
class SensingView:
    entrant_id: str
    label: str
    position: PhasePosition
    arena_size: int
    own_core_base: int | None
    own_core_size: int | None
    own_processes: tuple[OwnProcess, ...]
    contacts: tuple[HistoricalContact, ...]
    samples: tuple[SensingSample, ...]
    reads: tuple[DeliveredRead, ...]
    events: tuple[KnowledgeEvent, ...]
    receipt_status: SampleStatus
    # Constant pacing per permitted phase; hidden callbacks never add pauses.
    presentation_units: int = 1
    opponent_activity: str = "Unobserved"


@dataclass(frozen=True)
class OmniscientView:
    label: str
    tick: int
    global_decision_index: int | None
    phase: ExchangePhase
    anchors: tuple[tuple[str, str, int], ...]
    memory: bytes
    owners: tuple[str | None, ...]
    alive_entrants: tuple[str, ...]
    disrupted_processes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class VerificationSummary:
    """Operator report, deliberately absent from entrant execution payloads."""

    artifact_pair_consistent: bool
    exchange_reconstructed: bool
    teaching_steps: tuple[tuple[str, VerificationStatus], ...]
    teaching_complete: bool
    knowledge_projected: bool


@dataclass(frozen=True)
class _Frame:
    position: PhasePosition
    point: KnowledgePoint | None = None
    anchor: int | None = None
    event: KnowledgeEvent | None = None
    sample: SensingSample | None = None
    read: DeliveredRead | None = None


def _order(tick: int, index: int | None, phase: ExchangePhase) -> tuple[int, int, int]:
    return tick, index if index is not None else 2**63, list(ExchangePhase).index(phase)


class SensingCursor:
    """Rebuild a permitted prefix on seek; synchronize the canonical tick cursor.

    Construct with an M1-3 verified model and its matching loaded ReplaySession,
    or use from_paths for validation. No agent or independent simulation runs.
    """

    def __init__(
        self, playback: SensingPlayback, session: ReplaySession, entrant_id: str | None = "A"
    ) -> None:
        if (
            playback.ruleset_id != BYTEFRAY_RULESET_V6_ALPHA1_ID
            or session.header is None
            or session.header.match_id != playback.match_id
            or session.header.ruleset_id != playback.ruleset_id
            or session.header.config.arena_size != playback.arena_size
            or entrant_id is not None
            and entrant_id not in playback.binding.entrant_identities
        ):
            raise SensingProjectionError(
                "Exchange playback unavailable: evidence could not be verified."
            )
        # M1-3's frozen dataclasses contain mutable dictionaries. Retain no
        # caller-owned evidence that a later view switch could reconsume.
        self._playback = copy.deepcopy(playback)
        playback = self._playback
        self._session = session
        self._entrant = entrant_id
        self._orders: list[tuple[int, int, int]] = []
        self._frames: list[_Frame] = []
        self._worlds: list[SubTickWorldState] = []
        self._boundaries: dict[int, SubTickWorldState] = {}
        source_tick = session.current_tick
        try:
            replay_path = playback.binding.replay_path
            if any(
                part.lower() == "research"
                or part.lower().startswith(("research_", "e9_", "e8_", ".pytest_e9_"))
                for part in replay_path.resolve().parts
            ):
                raise SensingProjectionError(
                    "Exchange playback unavailable: evidence could not be verified."
                )
            if (
                hashlib.sha256(replay_path.read_bytes()).hexdigest()
                != playback.binding.replay_sha256
            ):
                raise SensingProjectionError(
                    "Exchange playback unavailable: evidence could not be verified."
                )
            canonical = ReplaySession()
            canonical.load(replay_path)
            if (
                hashlib.sha256(replay_path.read_bytes()).hexdigest()
                != playback.binding.replay_sha256
            ):
                raise SensingProjectionError(
                    "Exchange playback unavailable: evidence could not be verified."
                )
            initial = session.seek(session.recorded_ticks[0])
            expected = canonical.current_state
            if (
                session.header != canonical.header
                or initial.processes != expected.processes
                or {key: a.region for key, a in initial.agents.items()}
                != {key: a.region for key, a in expected.agents.items()}
            ):
                raise SensingProjectionError(
                    "Exchange playback unavailable: evidence could not be verified."
                )
            pending = None
            last_order: tuple[int, int, int] | None = None
            for fact in playback.facts:
                order = _order(fact.tick, fact.decision_index, fact.phase)
                if last_order is not None and order <= last_order:
                    raise SensingProjectionError(
                        "Exchange playback unavailable: incomplete evidence."
                    )
                last_order = order
                identity = (fact.tick, fact.decision_index, fact.actor_id, fact.process_id)
                if fact.phase == ExchangePhase.OBSERVATION:
                    if pending is not None or None in identity:
                        raise SensingProjectionError(
                            "Exchange playback unavailable: incomplete evidence."
                        )
                    pending = identity
                elif fact.phase == ExchangePhase.ACTION:
                    if pending != identity:
                        raise SensingProjectionError(
                            "Exchange playback unavailable: incomplete evidence."
                        )
                    pending = None
                if fact.phase == ExchangePhase.TICK_END:
                    if pending is not None or fact.world_state is None:
                        raise SensingProjectionError(
                            "Exchange playback unavailable: incomplete evidence."
                        )
                    self._check_boundary(fact.world_state)
                    self._boundaries[fact.tick] = replace(
                        fact.world_state, anchors=dict(fact.world_state.anchors)
                    )
            if pending is not None:
                raise SensingProjectionError("Exchange playback unavailable: incomplete evidence.")
            if tuple(self._boundaries) != session.recorded_ticks:
                raise SensingProjectionError("Exchange playback unavailable: incomplete evidence.")
        except SensingProjectionError:
            raise
        except Exception:
            raise SensingProjectionError(
                "Exchange playback unavailable: evidence could not be verified."
            ) from None
        finally:
            session.seek(source_tick)
        initial = session.seek(session.recorded_ticks[0])
        self._initial_processes = tuple(
            OwnProcess(p.process_id, p.anchor, p.reach)
            for key, p in sorted(initial.processes.items())
            if key[0] == entrant_id
        )
        own = initial.agents.get(entrant_id) if entrant_id is not None else None
        self._core_base = own.region[0] if own and own.region else None
        # Product alpha1 has the contracted fixed eight-cell core.
        self._core_size = 8 if self._core_base is not None else None
        try:
            self._build_frames()
        except Exception:
            session.seek(source_tick)
            raise SensingProjectionError(
                "Exchange playback unavailable: incomplete evidence."
            ) from None
        self._index = 0
        self._sync()

    @classmethod
    def from_paths(
        cls,
        session: ReplaySession,
        replay_path: Path,
        trace_path: Path,
        entrant_id: str | None = "A",
        *,
        demo_path: Path | None = None,
        result_path: Path | None = None,
    ) -> SensingCursor:
        try:
            for path in (replay_path, trace_path, demo_path, result_path):
                if path is not None and any(
                    part.lower() == "research"
                    or part.lower().startswith(("research_", "e9_", "e8_", ".pytest_e9_"))
                    for part in path.resolve().parts
                ):
                    raise SensingProjectionError(
                        "Research inputs are outside product playback scope."
                    )
            if demo_path is not None:
                verify_demonstration_artifacts(demo_path)
            playback = reconstruct_sensing_playback(
                replay_path, trace_path, result_path=result_path, demo_path=demo_path
            )
            return cls(playback, session, entrant_id)
        except Exception:
            # Neither filenames nor verifier's hidden world contradictions are UI text.
            raise SensingProjectionError(
                "Exchange playback unavailable: evidence could not be verified."
            ) from None

    def _check_boundary(self, world: SubTickWorldState) -> None:
        state = self._session.seek(world.tick)
        if (
            state.arena != world.memory
            or state.owners != world.owners
            or {key: p.anchor for key, p in state.processes.items()} != world.anchors
            or frozenset(key for key, p in state.processes.items() if p.disrupted)
            != world.disrupted_processes
            or frozenset(key for key, a in state.agents.items() if a.alive) != world.alive_entrants
        ):
            raise SensingProjectionError(
                "Exchange playback unavailable: evidence could not be verified."
            )

    def _build_frames(self) -> None:
        points: dict[tuple[int, int], KnowledgePoint] = {}
        prior: dict[str, tuple[KnowledgePoint, KnowledgeEvent]] = {}
        callback = 0
        for fact in self._playback.facts:
            if self._entrant is not None and fact.actor_id not in (None, self._entrant):
                continue
            order = _order(fact.tick, fact.decision_index, fact.phase)
            if self._orders and order <= self._orders[-1]:
                raise SensingProjectionError("Exchange playback unavailable: incomplete evidence.")
            if fact.world_state is None:
                raise SensingProjectionError("Exchange playback unavailable: incomplete evidence.")
            if self._entrant is None:
                self._orders.append(order)
                self._worlds.append(
                    replace(fact.world_state, anchors=dict(fact.world_state.anchors))
                )
                continue
            position = PhasePosition(fact.tick, None, fact.phase)
            frame = _Frame(position)
            if fact.phase != ExchangePhase.TICK_END:
                if fact.process_id is None or fact.decision_index is None:
                    raise SensingProjectionError(
                        "Exchange playback unavailable: incomplete evidence."
                    )
                if fact.phase == ExchangePhase.OBSERVATION:
                    callback += 1
                position = PhasePosition(fact.tick, callback, fact.phase)
                point = KnowledgePoint(fact.tick, callback, fact.process_id)
                points[(fact.tick, fact.decision_index)] = point
                sample = None
                read = None
                status = SampleStatus.ABSENT
                previous = prior.get(fact.process_id)
                if fact.delivery_point is not None:
                    sampled_at = points.get(fact.sample_point) if fact.sample_point else None
                    if previous is None or previous[1].kind != "sense" or sampled_at is None:
                        raise SensingProjectionError(
                            "Exchange playback unavailable: incomplete evidence."
                        )
                    addresses = fact.sensed_anchors
                    status = (
                        SampleStatus.REFUSED
                        if addresses is None
                        else SampleStatus.POSITIVE
                        if addresses
                        else SampleStatus.EMPTY
                    )
                    center = previous[1].address
                    if center is None:
                        raise SensingProjectionError(
                            "Exchange playback unavailable: incomplete evidence."
                        )
                    sample = SensingSample(center, 27, status, addresses or (), sampled_at, point)
                if (
                    fact.phase == ExchangePhase.OBSERVATION
                    and previous is not None
                    and previous[1].kind == "read"
                    and previous[1].address is not None
                    and fact.detail.get("previous_action_applied") is True
                    and fact.read_value is not None
                ):
                    read = DeliveredRead(
                        previous[1].address, fact.read_value, fact.read_owner, previous[0], point
                    )
                if fact.phase == ExchangePhase.OBSERVATION:
                    event = KnowledgeEvent(
                        position,
                        fact.process_id,
                        "observation",
                        sample_status=status,
                        message="Delivered observation",
                    )
                    anchor = fact.world_state.get_anchor(self._entrant, fact.process_id)
                else:
                    # Never transfer action-time READ/SENSE results or world consequences.
                    address = fact.normalized_address
                    if (
                        address is None
                        and fact.operand is not None
                        and fact.action_kind in {"sense", "read", "write"}
                    ):
                        address = fact.operand % self._playback.arena_size
                    event = KnowledgeEvent(
                        position,
                        fact.process_id,
                        fact.action_kind or "attempt",
                        address,
                        fact.operand,
                        fact.value,
                        fact.cost,
                        fact.status,
                        SampleStatus.PENDING
                        if fact.action_kind == "sense"
                        else SampleStatus.ABSENT,
                        "Search requested; 1 action spent; result pending"
                        if fact.action_kind == "sense"
                        else "Recorded own action",
                    )
                    prior[fact.process_id] = point, event
                    anchor = (
                        address if fact.action_kind == "move" and fact.status == "APPLIED" else None
                    )
                frame = _Frame(position, point, anchor, event, sample, read)
            self._frames.append(frame)
            self._orders.append(order)

    @property
    def positions(self) -> tuple[PhasePosition, ...]:
        """Only permitted phases; there are no blank opponent steps."""
        if self._entrant is None:
            return tuple(PhasePosition(w.tick, w.decision_index, w.phase) for w in self._worlds)
        return tuple(frame.position for frame in self._frames)

    @property
    def at_end(self) -> bool:
        return self._index == len(self._orders) - 1

    @property
    def current_view(self) -> SensingView | OmniscientView:
        if self._entrant is None:
            world = self._worlds[self._index]
            return OmniscientView(
                "Omniscient — full world state",
                world.tick,
                world.decision_index,
                world.phase,
                tuple((e, p, a) for (e, p), a in sorted(world.anchors.items())),
                world.memory,
                world.owners,
                tuple(sorted(world.alive_entrants)),
                tuple(sorted(world.disrupted_processes)),
            )
        processes = {p.process_id: p for p in self._initial_processes}
        samples: list[SensingSample] = []
        reads: list[DeliveredRead] = []
        events: list[KnowledgeEvent] = []
        callback = 0
        receipt = SampleStatus.ABSENT
        for frame in self._frames[: self._index + 1]:
            receipt = frame.event.sample_status if frame.event else SampleStatus.ABSENT
            if frame.point:
                callback = frame.point.callback
                if frame.anchor is not None and frame.point.process_id in processes:
                    old = processes[frame.point.process_id]
                    processes[old.process_id] = replace(old, anchor=frame.anchor)
            if frame.sample:
                samples.append(frame.sample)
            if frame.read:
                reads.append(frame.read)
            if frame.event:
                events.append(frame.event)
        contacts: dict[int, HistoricalContact] = {}
        position = self._frames[self._index].position
        # Sample chronology controls occupancy, even when sibling receipts arrive out of order.
        for sample in sorted(samples, key=lambda s: s.sampled_at.callback):
            if sample.status == SampleStatus.REFUSED:
                continue
            for address, contact in list(contacts.items()):
                distance = min(
                    (address - sample.center) % self._playback.arena_size,
                    (sample.center - address) % self._playback.arena_size,
                )
                if distance <= sample.half_width and address not in sample.addresses:
                    contacts[address] = replace(
                        contact, not_present_in_newer_sample=sample.sampled_at
                    )
            for address in sample.addresses:
                contacts[address] = HistoricalContact(
                    address,
                    sample.sampled_at,
                    sample.received_at,
                    position.tick - sample.sampled_at.tick,
                    callback - sample.sampled_at.callback,
                )
        contacts = {
            address: replace(
                c,
                age_ticks=position.tick - c.sampled_at.tick,
                age_callbacks=callback - c.sampled_at.callback,
            )
            for address, c in contacts.items()
        }
        return SensingView(
            self._entrant,
            f"Agent {self._entrant} — delivered information",
            position,
            self._playback.arena_size,
            self._core_base,
            self._core_size,
            tuple(processes[key] for key in sorted(processes)),
            tuple(contacts[key] for key in sorted(contacts)),
            tuple(samples),
            tuple(reads),
            tuple(events),
            receipt,
        )

    def _sync(self) -> None:
        tick, _, phase = self._orders[self._index]
        boundary = tick if phase == 2 else max(t for t in self._boundaries if t < tick)
        self._session.seek(boundary)
        if phase == 2:
            self._check_boundary(self._boundaries[tick])

    def seek(self, position: PhasePosition) -> SensingView | OmniscientView:
        try:
            index = self.positions.index(position)
        except ValueError:
            raise SensingProjectionError("Selected phase is unavailable.") from None
        self._index = index
        self._sync()
        return self.current_view

    def step_forward(self) -> SensingView | OmniscientView:
        self._index = min(self._index + 1, len(self._orders) - 1)
        self._sync()
        return self.current_view

    def step_backward(self) -> SensingView | OmniscientView:
        self._index = max(0, self._index - 1)
        self._sync()
        return self.current_view

    def restart(self) -> SensingView | OmniscientView:
        self._index = 0
        self._sync()
        return self.current_view

    def switch_view(self, entrant_id: str | None) -> SensingCursor:
        """Map internal global order to the last permitted phase in the new view."""
        target = self._orders[self._index]
        cursor = SensingCursor(self._playback, self._session, entrant_id)
        cursor._index = max(0, bisect.bisect_right(cursor._orders, target) - 1)
        cursor._sync()
        return cursor

    def verification_report(self) -> VerificationSummary:
        verification = self._playback.teaching_verification
        return VerificationSummary(
            True,
            True,
            tuple((s.name, s.status) for s in verification.steps) if verification else (),
            verification.is_verified if verification else False,
            self._entrant is not None,
        )
