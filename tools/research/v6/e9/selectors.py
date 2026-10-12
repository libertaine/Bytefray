"""Allocation commands from the approved E9 capability contract (§§3–7)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum
from itertools import product


class Mode(IntEnum):
    OFF = 0
    DENSE = 1
    MEDIUM = 2
    SPARSE = 4


CONFIRMATIONS = 2
COOLDOWN = 2
BUDGET = 4


@dataclass(frozen=True)
class Receipt:
    target: int
    issued_tick: int
    present: bool

    def __post_init__(self) -> None:
        if not 0 <= self.target < 512 or self.issued_tick < 1:
            raise ValueError("invalid verification receipt")


@dataclass(frozen=True)
class State:
    mode: Mode
    c: int
    target: int | None
    request: bool
    changes: int
    last_revision: int


@dataclass(frozen=True)
class Decision:
    epoch: int
    tick: int
    before: State
    after: State
    receipts: tuple[Receipt, ...]
    reason: str


class Adaptive:
    def __init__(self, *, disabled: bool = False, mode: Mode = Mode.DENSE) -> None:
        if not disabled and mode != Mode.DENSE:
            raise ValueError("adaptive initial allocation must be DENSE")
        self.disabled = disabled
        self.state = State(mode, 0, None, False, 0, 0)
        self.active = False
        self.last_epoch = -1

    def activate(self) -> None:
        if self.active:
            raise ValueError("duplicate activation")
        self.active = True

    @property
    def mode(self) -> Mode:
        return self.state.mode

    def boundary(self, epoch: int, tick: int, receipts: tuple[Receipt, ...]) -> Decision:
        if not self.active or epoch <= self.last_epoch or epoch < 0:
            raise ValueError("invalid allocation boundary")
        if any(r.issued_tick > tick for r in receipts):
            raise ValueError("future evidence")
        self.last_epoch = epoch
        old = self.state
        mode, c, target, request = old.mode, old.c, old.target, old.request
        used = tuple(r for r in receipts if tick - r.issued_tick <= 1)
        for r in used:
            if not r.present:
                request, c, target = True, 0, None
            elif not request:
                c = min(CONFIRMATIONS, c + 1) if target == r.target else 1
                target = r.target
        priority = request and mode == Mode.DENSE
        if priority:
            request, c, target = False, 0, None
        wanted = mode
        reason = "stay"
        if mode == Mode.SPARSE and request:
            wanted, reason = Mode.DENSE, "missing"
        elif mode == Mode.DENSE and c == CONFIRMATIONS and not priority:
            wanted, reason = Mode.SPARSE, "confirmations"
        changes, last = old.changes, old.last_revision
        if wanted != mode:
            if self.disabled:
                reason = "disabled"
            elif changes == BUDGET:
                reason = "budget"
            elif epoch - last < COOLDOWN:
                reason = "cooldown"
            else:
                mode, changes, last = wanted, changes + 1, epoch
                c, target, request = 0, None, False
        self.state = State(mode, c, target, request, changes, last)
        return Decision(epoch, tick, old, self.state, used, reason)


@dataclass(frozen=True)
class Schedule:
    initial: Mode
    edges: tuple[int, ...]
    clock: str = "opportunity"

    def __post_init__(self) -> None:
        if self.initial not in (Mode.DENSE, Mode.SPARSE):
            raise ValueError("scheduled allocations must be DENSE or SPARSE")
        if self.clock not in ("opportunity", "wall"):
            raise ValueError("invalid schedule clock")
        if len(self.edges) > BUDGET or any(b - a < COOLDOWN for a, b in
                zip((0, *self.edges), self.edges)):
            raise ValueError("invalid schedule boundaries")

    @property
    def identity(self) -> tuple[str, int, tuple[int, ...]]:
        return (self.clock if self.edges else "constant", int(self.initial), self.edges)


def schedules() -> tuple[Schedule, ...]:
    """All canonical performance controls, not an experiment matrix."""
    unique: dict[tuple[str, int, tuple[int, ...]], Schedule] = {}
    for clock, mode, start, high, low, count in product(
        ("opportunity", "wall"), (Mode.DENSE, Mode.SPARSE),
        (2, 4, 8, 16, 32, 64, 128, 256, 512), (2, 3, 4, 8), (2, 3, 4, 8), range(5)
    ):
        edges: list[int] = []
        next_edge, after = start, mode
        for _ in range(count):
            edges.append(next_edge)
            after = Mode.SPARSE if after == Mode.DENSE else Mode.DENSE
            next_edge += high if after == Mode.DENSE else low
        plan = Schedule(mode, tuple(edges), clock)
        unique[plan.identity] = plan
    return tuple(unique[key] for key in sorted(unique))


class Scheduled:
    def __init__(self, plan: Schedule) -> None:
        self.plan = plan
        self.state = State(plan.initial, 0, None, False, 0, 0)
        self.last_epoch = -1

    @property
    def mode(self) -> Mode:
        return self.state.mode

    def boundary(self, epoch: int, tick: int, wall: int) -> Decision:
        if epoch <= self.last_epoch or wall < 0:
            raise ValueError("invalid schedule boundary")
        self.last_epoch = epoch
        old = self.state
        clock = epoch if self.plan.clock == "opportunity" else wall
        passed = sum(edge <= clock for edge in self.plan.edges)
        desired = self.plan.initial
        if passed % 2:
            desired = Mode.SPARSE if desired == Mode.DENSE else Mode.DENSE
        reason = "stay"
        if desired != old.mode:
            if old.changes == BUDGET:
                reason = "budget"
            elif epoch - old.last_revision < COOLDOWN:
                reason = "cooldown"
            else:
                self.state = State(desired, 0, None, False, old.changes + 1, epoch)
                reason = "scheduled"
        return Decision(epoch, tick, old, self.state, (), reason)


def diagnostic(decision: Decision) -> dict:
    """Detached diagnostic data; never read by a policy."""
    return asdict(decision)
