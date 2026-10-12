"""Q-C1/2/6/7/8/10/11/13: actual policy callbacks and tactical equality."""

import hashlib
import random
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from _e8_family_harness import ACTIVE
from _e8_family_harness import make as frozen_make
from _e9_harness import context, make, observation, start
from battle_engine.agent_api import ActionKindV2

from tools.research.v6.e9.policy import Pending, Variant, receipt
from tools.research.v6.e9.selectors import Mode, Schedule


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("mode,member", [(Mode.OFF, "RUSH8"), (Mode.DENSE, "REACQ8")])
def test_qc1_frozen_callbacks_core_probes_search_and_rng(seat, mode, member):
    focal = make(Variant("fixed", mode), seat)
    frozen = frozen_make(member, mode=ACTIVE, seat=seat, rng=random.Random(0))
    for tick in range(1, 10):
        for index in range(8):
            pending = focal.pending.get("main")
            anchors, value, owner = None, None, None
            if pending and pending[0] in ("discover", "verify", "search"):
                anchors = (191,) if tick < 4 else () if pending[0] == "verify" else (237,)
            elif pending and pending[0] in ("verify-read", "probe", "scan"):
                value, owner = (0xCE, "B" if seat == "A" else "A") if 191 <= pending[1] < 199 else (0, None)
            obs = observation(tick, previous_tick=max(0, focal.tick),
                              anchors=anchors, value=value, owner=owner)
            assert focal.act(obs) == frozen.act(obs)
            assert focal.known == frozen.known and focal.enemy_core == frozen.enemy_core
            assert focal.search_centers == frozen.search_centers and focal.search_next == frozen.search_next
            assert focal.rng.getstate() == frozen.rng.getstate()
    assert focal.enemy_core is not None  # core-inference equality was exercised


@pytest.mark.parametrize("mode", list(Mode))
def test_qc2_all_disabled_twins_reproduce_fixed_variants(mode):
    fixed, twin = make(Variant("fixed", mode)), make(Variant("disabled", mode))
    start(fixed)
    start(twin)
    for tick in range(2, 12):
        for _ in range(8):
            pending = fixed.pending.get("main")
            sensed = (191,) if pending and pending[0] in ("verify", "search", "discover") else None
            obs = observation(tick, previous_tick=fixed.tick, anchors=sensed)
            assert fixed.act(obs) == twin.act(obs)
            assert fixed.rng.getstate() == twin.rng.getstate()


def test_qc7_adapter_empty_absent_refused_wrong_process_and_multiple_anchors():
    p = Pending("main", 511, 2)
    assert receipt(p, observation(3, previous_tick=2, anchors=())).present is False
    assert receipt(p, observation(3, previous_tick=2, anchors=(0, 511))).present is True
    assert receipt(p, observation(3, previous_tick=2, applied=False)) is None
    assert receipt(None, observation(3, anchors=(191,))) is None
    for bad in (observation(3, previous_tick=1, anchors=()), observation(3, previous_tick=2),
                observation(3, previous_tick=2, applied=False, anchors=()),
                observation(3, previous_tick=2, anchors=(511, 0)),
                replace(observation(3, previous_tick=2, anchors=()), self_process_id="other")):
        with pytest.raises(ValueError):
            receipt(p, bad)


@pytest.mark.parametrize("seat", ["A", "B"])
def test_qc7_activation_mid_tick_reflection_boundary_freshness_and_end(seat):
    agent = make(seat=seat)
    start(agent)
    assert agent.diagnostics() == []  # discovery at callback two creates no revision slot
    agent.act(observation(2, previous_tick=1))
    assert agent.pending["main"] == ("verify", 191)
    agent.act(observation(2, previous_tick=2, anchors=(191,)))
    assert agent.selector.state.c == 0  # receipt buffered, not a mid-tick revision
    agent.act(observation(5, previous_tick=2))
    assert agent.selector.state.c == 0 and agent.known == (191,)  # expired selector evidence only
    assert agent.verification is not None  # with no next callback, no invented return


def test_qc8_qc10_twin_same_prestate_then_real_sense_vs_productive_action():
    adaptive, twin = make(), make(Variant("disabled"))
    start(adaptive)
    start(twin)
    for tick in (2, 3):
        for _ in range(2):
            pending = adaptive.pending.get("main")
            obs = observation(tick, previous_tick=adaptive.tick,
                              anchors=(191,) if pending and pending[0] == "verify" else None)
            assert adaptive.act(obs) == twin.act(obs)
    before = deepcopy(adaptive)
    assert adaptive.selector.state.c == 1 and adaptive.epoch == 2
    # Literally fork the identical executor and disable only the commit.
    fork = deepcopy(adaptive)
    fork.selector.disabled = True
    at_boundary = observation(4, previous_tick=3)
    left, right = adaptive.act(at_boundary), twin.act(at_boundary)
    assert fork.act(at_boundary) == right
    assert fork.rng.getstate() == adaptive.rng.getstate() == twin.rng.getstate()
    assert adaptive.selector.mode == Mode.SPARSE and twin.selector.mode == Mode.DENSE
    assert left.kind != ActionKindV2.SENSE and right.kind == ActionKindV2.SENSE
    assert left.kind in (ActionKindV2.WRITE, ActionKindV2.READ)
    assert before.pending == {} and before.known == twin.known == adaptive.known


def test_qc6_qc13_irrelevant_metadata_diagnostics_reset_and_seed_poison():
    class Poison(SimpleNamespace):
        @property
        def seed(self):
            raise AssertionError("seed access")

    from tools.research.v6.e9.policy import Agent
    agent = Agent()
    agent.reset(Poison(agent_id="A", arena_size=512, sensing_window=27, rng=random.Random(0)))
    start(agent)
    twin = deepcopy(agent)
    assert agent.act(observation(2, previous_tick=1, value=99, owner="alias")) == twin.act(
        observation(2, previous_tick=1, value=17, owner="other"))
    assert agent.selector.state == twin.selector.state
    data = agent.diagnostics()
    data[0]["after"]["mode"] = 0
    assert agent.selector.mode == Mode.DENSE
    agent.reset(context())
    assert agent.diagnostics() == [] and agent.activation_epoch is None and agent.epoch == -1
    for tick in (1, 2, 3):
        for _ in range(8):
            pending = agent.pending.get("main")
            agent.act(observation(tick, previous_tick=max(0, agent.tick), anchors=() if pending else None))
    assert agent.activation_epoch is None and agent.selector.mode == Mode.DENSE
    assert agent.diagnostics() == [] and agent.selector.state.changes == 0
    with pytest.raises(ValueError):
        agent.reset(replace(context(), sensing_window=None))
    with pytest.raises(ValueError):
        agent.act(replace(observation(1), self_process_id="other"))


def test_qc11_transition_does_not_touch_inflight_search():
    agent = make()
    start(agent)
    agent.search_address, agent.search_centers, agent.search_next = 191, [237, 145], 0
    agent.selector.state = replace(agent.selector.state, c=2, target=191)
    agent.epoch = 2
    rng = agent.rng.getstate()
    action = agent.act(observation(4, previous_tick=1))
    assert agent.selector.mode == Mode.SPARSE
    assert action.kind == ActionKindV2.SENSE and action.operand == 237
    assert agent.search_address == 191 and agent.search_centers == [237, 145] and agent.search_next == 1
    assert agent.rng.getstate() == rng


def test_qc9_policy_schedule_ignores_adaptive_receipts():
    plan = Schedule(Mode.DENSE, (2, 4, 6, 8))
    a = make(Variant("schedule", schedule=plan))
    start(a)
    b = deepcopy(a)
    for tick in range(2, 12):
        for _ in range(2):
            for agent, missing in ((a, False), (b, True)):
                pending = agent.pending.get("main")
                anchors = None
                if pending and pending[0] in ("verify", "search", "discover"):
                    target = pending[1]
                    anchors = ((target + 8) % 512,) if missing else (target,)
                agent.act(observation(tick, previous_tick=agent.tick, anchors=anchors))
            assert a.selector.state == b.selector.state


def test_qc1_tactical_copy_is_byte_identical_and_qc13_selector_has_no_extra_sources():
    from tools.research.v6.e9 import tactics
    assert hashlib.sha256(Path(tactics.__file__).read_bytes()).hexdigest() == (
        "369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc")
    from tools.research.v6.e9 import selectors
    text = Path(selectors.__file__).read_text(encoding="utf-8")
    for forbidden in ("context.seed", "random", "open(", "Path(", "own_core", "previous_read", "agent_id"):
        assert forbidden not in text


def test_qc3_full_callbacks_repeated_revisions_and_deferred_request():
    agent = make()
    start(agent)
    outcomes = {1: False, 2: True, 3: True, 4: False, 6: True,
                7: True, 8: False, 10: True, 11: True}
    for tick in range(2, 14):
        for _ in range(8):
            pending = agent.pending.get("main")
            anchors = None
            if pending and pending[0] in ("verify", "search", "discover"):
                anchors = (191,)
                if pending[0] == "verify" and not outcomes.get(agent.epoch, True):
                    anchors = ()
            agent.act(observation(tick, previous_tick=agent.tick, anchors=anchors))
    rows = agent.diagnostics()
    assert [int(r["after"]["mode"]) for r in rows] == [1, 1, 1, 4, 4, 1, 1, 4, 4, 1, 1, 1]
    assert [r["epoch"] for r in rows if r["reason"] == "cooldown"] == [5, 9]
    assert rows[-1]["reason"] == "budget" and rows[-1]["after"]["changes"] == 4


def test_qc6_extra_contacts_and_circular_target_renaming():
    from tools.research.v6.e9.selectors import Adaptive, Receipt
    for target in (0, 191, 511):
        a, b = Adaptive(), Adaptive()
        a.activate()
        b.activate()
        for epoch in range(3):
            obs = observation(epoch + 1, previous_tick=epoch + 1, anchors=(target,))
            additional = tuple(sorted({target, (target + 8) % 512}))
            left = receipt(Pending("main", target, epoch + 1), obs)
            right = receipt(Pending("main", target, epoch + 1), replace(obs, previous_sense_anchors=additional))
            assert left == right == Receipt(target, epoch + 1, True)
            assert a.boundary(epoch, epoch + 1, (left,)).after == b.boundary(epoch, epoch + 1, (right,)).after
        assert a.mode == Mode.SPARSE


@pytest.mark.parametrize("seat", ["A", "B"])
def test_qc11_full_search_exhaustion_matches_frozen_order_and_rng(seat):
    focal = make(Variant("fixed"), seat)
    frozen = frozen_make("REACQ8", mode=ACTIVE, seat=seat, rng=random.Random(0))
    search_operands = []
    for tick in (1, 2):
        for index in range(8):
            pending = focal.pending.get("main")
            anchors = None
            if pending and pending[0] in ("discover", "verify", "search"):
                anchors = (191,) if tick == 1 else ()
            obs = observation(tick, previous_tick=max(0, focal.tick), anchors=anchors)
            action = focal.act(obs)
            assert action == frozen.act(obs)
            assert focal.rng.getstate() == frozen.rng.getstate()
            if focal.pending.get("main", (None,))[0] == "search":
                search_operands.append(action.operand)
    assert len(search_operands) == 2 and set(search_operands) == {145, 237}
    assert focal.search_address is None and focal.search_centers == []
    # Frozen RP-3 pops the target at search start; exhaustion makes it unknown,
    # rather than re-enqueuing it (E8 contract §3.2, Termination).
    assert focal.known == frozen.known == () and focal.missing == frozen.missing == []
    assert focal.replacements == frozen.replacements == {}
