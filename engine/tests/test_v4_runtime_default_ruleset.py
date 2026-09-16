from __future__ import annotations

"""An omitted direct-runtime Ruleset resolves to stable v4, not alpha1.

``ProcessMatchController`` takes an optional ``ruleset_policy``. Both of its
construction paths -- ``__init__`` and ``from_python_entrants`` -- defaulted
to ``RULESET_V4_ALPHA1`` from the moment the process runtime was written, and
were never updated when alpha2 and then the permanent stable identity
``bytefray-rules-4`` were promoted. Every *product* path
(``match_service._run_v4_process_match``) always passes an explicit policy, so
no released match was ever affected; but any direct-runtime caller that
omitted the argument -- a test, a benchmark, a research harness, a future V5
experiment -- silently received frozen alpha1 gameplay
(``core_placement="seat_spread"``, ``process_selection="priority"``) while
believing it was exercising released v4.

That is a baseline-contamination hazard for the V5 research program
specifically: a V5 experiment that omitted the policy would measure itself
against alpha1 rather than against the released control.

This module locks the corrected contract. Note what it deliberately does
*not* do: it changes no Ruleset's behaviour. ``RULESET_V4_ALPHA1``,
``RULESET_V4_ALPHA2`` and ``RULESET_V4`` are untouched, and the "historical
semantics still reproduce" tests below prove it. Only *which already-existing
policy an omitted selection receives* has changed.
"""

import inspect
from typing import Any

import pytest
from battle_engine.agent_api import ActionKind, AgentAction, ObservationV2
from battle_engine.config import Config, Weights
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    RULESET_V4,
    RULESET_V4_ALPHA1,
    RULESET_V4_ALPHA2,
    RulesetPolicy,
)

# ``ProcessMatchController`` reads exactly one of the two gameplay fields that
# differ between alpha1 and stable v4: ``process_selection``. The other
# (``core_placement``) is consumed upstream by ``placement``/``match_service``,
# so intra-entrant execution order is the observable that distinguishes the
# two policies *inside* the controller.
_ALPHA1_PRIORITY_ORDER = [
    ("A", "p1"), ("A", "p1"), ("A", "p1"), ("A", "p1"),
    ("A", "p2"), ("A", "p2"), ("A", "p2"), ("A", "p2"),
]
_STABLE_V4_ROUND_ROBIN_ORDER = [
    ("A", "p1"), ("A", "p2"), ("A", "p1"), ("A", "p2"),
    ("A", "p1"), ("A", "p2"), ("A", "p1"), ("A", "p2"),
]


def _nop(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
    return AgentAction(ActionKind.NOP)


def _single_process_entrant() -> ProcessEntrantSpec:
    return ProcessEntrantSpec("A", "probe", [
        ProcessInstance("p1", ProcessRole.GENERALIST, 0, None, 8, _nop),
    ])


def _intra_entrant_order(
    policy: RulesetPolicy | None, *, omit: bool = False
) -> list[tuple[str, str]]:
    """Run one tick and report which of entrant A's processes acted, in order.

    ``omit=True`` constructs the controller without naming a policy at all --
    the exact call shape a direct-runtime caller uses, and the one this module
    exists to pin.
    """

    trace: list[tuple[str, str]] = []

    def tracer(process_id: str):
        def act(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
            trace.append(("A", process_id))
            return AgentAction(ActionKind.NOP)

        return act

    spec_a = ProcessEntrantSpec("A", "probe", [
        ProcessInstance("p1", ProcessRole.DEFENDER, 0, None, 4, tracer("p1")),
        ProcessInstance("p2", ProcessRole.HUNTER, 0, None, 4, tracer("p2")),
    ])
    spec_b = ProcessEntrantSpec("B", "passive", [
        ProcessInstance("b1", ProcessRole.GENERALIST, 0, None, 8, _nop),
    ])
    config = Config(arena_size=1024, instr_per_tick=8, seed=1, weights=Weights())
    if omit:
        controller = ProcessMatchController(config, [spec_a, spec_b], max_ticks=1)
    else:
        controller = ProcessMatchController(
            config, [spec_a, spec_b], max_ticks=1, ruleset_policy=policy
        )
    controller.run()
    return trace


# ---------------------------------------------------------------------------
# The corrected default
# ---------------------------------------------------------------------------


def test_direct_construction_with_omitted_policy_is_stable_v4() -> None:
    """``ProcessMatchController(...)`` with no policy resolves to stable v4."""

    controller = ProcessMatchController(
        Config(arena_size=512, instr_per_tick=8, seed=3, weights=Weights()),
        [_single_process_entrant()],
        max_ticks=1,
    )

    assert controller.ruleset_policy is RULESET_V4
    assert controller.ruleset_policy.ruleset_id == BYTEFRAY_RULESET_V4_ID


def test_explicit_none_policy_also_resolves_to_stable_v4() -> None:
    """``ruleset_policy=None`` is the same omitted selection as leaving it out.

    ``__init__`` accepts ``RulesetPolicy | None``, so a caller threading an
    optional policy through can pass ``None`` explicitly; that must land on the
    same stable identity rather than on frozen alpha1.
    """

    controller = ProcessMatchController(
        Config(arena_size=512, instr_per_tick=8, seed=3, weights=Weights()),
        [_single_process_entrant()],
        max_ticks=1,
        ruleset_policy=None,
    )

    assert controller.ruleset_policy is RULESET_V4


def test_from_python_entrants_omitted_policy_default_is_stable_v4() -> None:
    """``from_python_entrants``'s own signature default is stable v4.

    Asserted on the signature rather than through a live load because that
    classmethod spawns supervised agent worker processes. The default is a
    property of the declaration itself, and it is the declaration that the
    RULE-01 defect got wrong.
    """

    default = inspect.signature(
        ProcessMatchController.from_python_entrants
    ).parameters["ruleset_policy"].default

    assert default is RULESET_V4
    assert default.ruleset_id == BYTEFRAY_RULESET_V4_ID
    assert default is not RULESET_V4_ALPHA1


def test_omitted_policy_executes_stable_v4_gameplay_not_alpha1() -> None:
    """The corrected default is observable in gameplay, not just in a field.

    An omitted policy must produce stable v4's round-robin intra-entrant
    rotation, and must not reproduce alpha1's declaration-order priority.
    """

    omitted = _intra_entrant_order(None, omit=True)

    assert omitted == _STABLE_V4_ROUND_ROBIN_ORDER
    assert omitted == _intra_entrant_order(RULESET_V4)
    assert omitted != _ALPHA1_PRIORITY_ORDER


# ---------------------------------------------------------------------------
# Historical semantics are untouched
# ---------------------------------------------------------------------------


def test_explicit_alpha1_still_executes_alpha1_semantics() -> None:
    """Naming alpha1 still reproduces its frozen declaration-order priority."""

    assert RULESET_V4_ALPHA1.process_selection == "priority"
    assert RULESET_V4_ALPHA1.core_placement == "seat_spread"
    assert _intra_entrant_order(RULESET_V4_ALPHA1) == _ALPHA1_PRIORITY_ORDER


def test_explicit_alpha2_still_executes_alpha2_semantics() -> None:
    """Naming alpha2 still reproduces its round-robin rotation."""

    assert RULESET_V4_ALPHA2.process_selection == "round_robin"
    assert RULESET_V4_ALPHA2.core_placement == "seeded"
    assert _intra_entrant_order(RULESET_V4_ALPHA2) == _STABLE_V4_ROUND_ROBIN_ORDER


@pytest.mark.parametrize(
    ("policy", "expected"),
    [
        (RULESET_V4_ALPHA1, _ALPHA1_PRIORITY_ORDER),
        (RULESET_V4_ALPHA2, _STABLE_V4_ROUND_ROBIN_ORDER),
        (RULESET_V4, _STABLE_V4_ROUND_ROBIN_ORDER),
    ],
)
def test_every_v4_identity_keeps_its_own_execution_order(
    policy: RulesetPolicy, expected: list[tuple[str, str]]
) -> None:
    """Each v4 identity stays explicitly selectable and behaviourally itself.

    Guards the direction the default fix must never leak in: correcting an
    omitted selection must not make alpha1 unreachable, nor make it execute as
    anything other than alpha1.
    """

    assert _intra_entrant_order(policy) == expected


def test_alpha1_and_stable_v4_remain_behaviourally_distinguishable() -> None:
    """The two policies the old default confused are genuinely different.

    If this ever fails, the tests above stop proving anything -- they would be
    comparing a policy against itself.
    """

    assert _ALPHA1_PRIORITY_ORDER != _STABLE_V4_ROUND_ROBIN_ORDER
    assert (
        RULESET_V4_ALPHA1.process_selection != RULESET_V4.process_selection
        or RULESET_V4_ALPHA1.core_placement != RULESET_V4.core_placement
    )
