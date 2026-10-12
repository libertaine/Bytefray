"""Offline receipt, selector and action-consequence audit on authoritative callbacks.

Detached branches consume recorded feedback only while their actions agree.
They stop at the first difference; they never simulate a divergent live world.
"""

from __future__ import annotations

import random
from collections import Counter
from copy import deepcopy
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, MatchContextV2, ObservationV2
from battle_engine.agent_trace import ABSENT, DecisionRecordV2
from battle_engine.python_runtime import derive_agent_seed

from .oracle import Expected, advance
from .policy import Agent, Pending, Variant
from .protocol import IntegrityError, canonical, digest
from .selectors import Adaptive, Mode, Receipt, State


def normalized(action: Any) -> tuple[str, int | None, int | None]:
    if action is None or action.kind not in tuple(ActionKindV2):
        raise IntegrityError("missing or illegal focal action")
    operand = action.operand
    if type(operand) is not int:
        raise IntegrityError("invalid focal operand")
    kind = ActionKindV2(action.kind)
    if kind == ActionKindV2.MOVE:
        operand = max(-64, min(64, operand))
    else:
        operand %= 512
    value = action.value
    if kind == ActionKindV2.WRITE:
        if type(value) is not int:
            raise IntegrityError("invalid focal WRITE value")
        value %= 256
    elif value is not None:
        raise IntegrityError("unexpected action value")
    return kind.value, operand, value


def observation(record: DecisionRecordV2) -> ObservationV2:
    values = {name: getattr(record.observation, name) for name in ObservationV2.__dataclass_fields__}
    if values["previous_sense_anchors"] is ABSENT:
        values["previous_sense_anchors"] = None
    return ObservationV2(**values)


def _set_mode(agent: Agent, mode: Mode) -> None:
    state = agent.selector.state
    agent.selector.state = State(mode, state.c, state.target, state.request,
                                 state.changes, state.last_revision)
    agent.selector.disabled = True


def _choose_tail(agent: Agent, obs: ObservationV2) -> AgentAction:
    action = Agent._choose(agent, obs)
    pending = agent.pending.get("main")
    if action.kind == ActionKindV2.SENSE and pending is not None and pending[0] == "verify":
        agent.verification = Pending("main", pending[1], obs.current_tick)
    agent.first_callback = False
    return action


def audit(records: list[DecisionRecordV2], context: MatchContextV2,
          variant: Variant | None = None, *, cell_identity: str = "qualification-fixture") -> dict[str, Any]:
    """Check a reconstructed policy against every actual action, then audit A.

    The qualified policy supplies detached tactical states; its selector is
    checked independently by the literal-contract oracle. No engine is run.
    """
    variant = variant or Variant()
    agent = Agent(variant)
    agent.reset(context)
    expected = Expected(mode=int(agent.selector.mode))
    decisions: list[dict[str, Any]] = []
    revisions: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    history: list[tuple[int, int, tuple[tuple[int, int, bool], ...]]] = []
    history_start = expected
    receipt_ids: dict[tuple[int, int], str] = {}
    receipt_records: list[dict[str, Any]] = []
    issuance_records: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    request: dict[str, Any] | None = None
    phase_differences: Counter[int] = Counter()
    phase_exposure: set[int] = set()
    callback = -1

    def clone() -> Agent:
        # Instance hooks must not be copied into detached branches.
        boundary_hook = agent.selector.__dict__.pop("boundary", None)
        choose_hook = agent.__dict__.pop("_choose", None)
        try:
            return deepcopy(agent)
        finally:
            if boundary_hook is not None:
                agent.selector.boundary = boundary_hook
            if choose_hook is not None:
                agent._choose = choose_hook  # type: ignore[method-assign]

    def boundary(epoch: int, tick: int, receipts: tuple[Receipt, ...]) -> Any:
        nonlocal expected, history, history_start, active, request
        before = clone()
        used = tuple((r.issued_tick, r.target, r.present) for r in receipts
                     if tick - r.issued_tick <= 1)
        old = expected
        predicted = advance(old, epoch, tick, used, disabled=variant.kind != "adaptive")
        decision = Adaptive.boundary(agent.selector, epoch, tick, receipts)
        got = Expected(int(decision.after.mode), decision.after.c, decision.after.target,
                       decision.after.request, decision.after.changes, decision.after.last_revision)
        if got != predicted:
            raise IntegrityError("independent selector reconstruction disagrees")
        history.append((epoch, tick, used))
        expected = predicted
        consumed = [receipt_ids[(issue, target)] for issue, target, _ in used]
        decisions.append({"callback": callback, "epoch": epoch, "tick": tick,
                          "receipts": consumed, "before": tuple(old), "after": tuple(predicted)})
        # Independently determine demand before cooldown/budget application.
        demand = advance(old._replace(changes=0), old.last_revision + 2, tick, used)
        wanted = demand.mode if predicted.mode == old.mode else predicted.mode
        if request is not None and wanted == old.mode:
            request.update({"disposition": "cancelled", "resolution_callback_ordinal": callback + 1})
            request = None
        if variant.kind == "adaptive" and wanted != old.mode and request is None:
            withheld = history_start
            for e, t, _ in history:
                withheld = advance(withheld, e, t, (), disabled=variant.kind != "adaptive")
            # No verification evidence means no observation-driven demand.
            if withheld.mode != history_start.mode or withheld.request or withheld.c >= 2:
                raise IntegrityError("receipt withholding did not remove revision demand")
            request = {"cell_identity": cell_identity, "ordinal": len(requests) + 1,
                       "requested_mode": wanted, "origin_callback": callback,
                       "origin_tick": tick, "cause": "missing" if wanted == 1 else "confirmations",
                       "trigger_receipt_ids": [receipt_ids[(i, t)] for _, _, rs in history
                                               for i, t, _ in rs], "withholding_passed": True,
                       "withheld_selector_state": tuple(withheld), "disposition": "pending",
                       "resolution_callback_ordinal": None}
            requests.append(request)
        if old.mode != predicted.mode:
            if request is None:
                raise IntegrityError("committed revision has no causal request")
            if active is not None:
                active["record"]["end_callback_exclusive"] = callback
            prior, committed = before, deepcopy(before)
            for branch in (prior, committed):
                branch.receipts.clear()
                branch.selector.state = decision.after
                branch.selector.last_epoch = epoch
            _set_mode(prior, Mode(old.mode))
            _set_mode(committed, Mode(predicted.mode))
            revision = {"ordinal": len(revisions) + 1, "callback": callback, "tick": tick,
                        "epoch": epoch, "prior_mode": old.mode, "committed_mode": predicted.mode,
                        "cell_identity": cell_identity, "request_ordinal": request["ordinal"],
                        "selector_prestate": tuple(old), "budget_remaining_before": 4 - old.changes,
                        "cooldown_elapsed_before": epoch - old.last_revision, "realized": False,
                        "first_difference_callback": None, "end_callback_exclusive": len(records)}
            revisions.append(revision)
            active = {**revision, "record": revision, "prior": prior, "committed": committed}
            request.update({"disposition": "satisfied", "resolution_callback_ordinal": callback + 1,
                            "revision_ordinal": revision["ordinal"]})
            history, history_start, request = [], predicted, None
        return decision

    def choose(obs: ObservationV2) -> AgentAction:
        if (variant.kind == "adaptive" and agent.callback_index == 1 and agent.discovered
                and agent.known and agent.search_address is None and agent.activation_epoch is not None):
            phase = (agent.epoch - agent.activation_epoch) % 4
            if phase in (1, 2, 3):
                dense, sparse = clone(), clone()
                _set_mode(dense, Mode.DENSE)
                _set_mode(sparse, Mode.SPARSE)
                if normalized(Agent._choose(dense, obs)) != normalized(Agent._choose(sparse, obs)):
                    phase_differences[phase] += 1
                    phase_exposure.add(phase)
        return Agent._choose(agent, obs)

    adaptive_selector = isinstance(agent.selector, Adaptive)
    if adaptive_selector:
        agent.selector.boundary = boundary
    else:
        from .oracle import schedule_command
        from .selectors import Scheduled

        def scheduled_boundary(epoch: int, tick: int, wall: int) -> Any:
            nonlocal expected
            assert variant.schedule is not None
            moment = epoch if variant.schedule.clock == "opportunity" else wall
            predicted = schedule_command(int(variant.schedule.initial), variant.schedule.edges,
                                         moment, epoch, expected)
            decision = Scheduled.boundary(agent.selector, epoch, tick, wall)
            got = Expected(int(decision.after.mode), decision.after.c, decision.after.target,
                           decision.after.request, decision.after.changes, decision.after.last_revision)
            if got != predicted:
                raise IntegrityError("independent schedule reconstruction disagrees")
            expected = predicted
            return decision

        agent.selector.boundary = scheduled_boundary
    agent._choose = choose  # type: ignore[method-assign]
    for callback, record in enumerate(records):
        if record.agent_id != context.agent_id or record.process_id != "main":
            raise IntegrityError("foreign callback entered focal reconstruction")
        obs = observation(record)
        pending = agent.verification
        if pending is not None:
            key = pending.tick, pending.target
            if key in receipt_ids:
                raise IntegrityError("verification evidence consumed more than once")
            identity = {"cell_identity": cell_identity, "entrant": context.agent_id, "process": "main",
                        "issuance_callback_ordinal": callback, "issue_tick": pending.tick,
                        "target": pending.target % 512, "delivery_callback_ordinal": callback + 1}
            receipt_ids[key] = digest(canonical(identity))
            if not issuance_records or issuance_records[-1]["issuance_callback_ordinal"] != callback:
                raise IntegrityError("verification delivery lacks its authoritative issuance ordinal")
            issuance_records[-1]["delivery_callback_ordinal"] = callback + 1
            receipt_records.append({"identity": receipt_ids[key], **identity,
                "fresh": 0 <= obs.current_tick - pending.tick <= 1,
                "outcome": "refused" if not obs.previous_action_applied else (
                    "confirm" if obs.previous_sense_anchors is not None and pending.target in obs.previous_sense_anchors
                    else "missing")})
        action = agent.act(obs)
        if agent.verification is not None:
            issuance_records.append({"cell_identity": cell_identity, "entrant": context.agent_id,
                "process": "main", "issuance_callback_ordinal": callback + 1,
                "issue_tick": agent.verification.tick, "target": agent.verification.target % 512,
                "delivery_callback_ordinal": None})
        actual = normalized(record.action)
        if normalized(action) != actual:
            raise IntegrityError("offline policy disagrees with authoritative action history")
        if variant.kind == "adaptive" and active is not None and not active["record"]["realized"]:
            committing = active["record"]["callback"] == callback
            left, right = active["prior"], active["committed"]
            prior_action = _choose_tail(left, obs) if committing else left.act(obs)
            committed_action = _choose_tail(right, obs) if committing else right.act(obs)
            if normalized(committed_action) != actual:
                raise IntegrityError("committed detached branch disagrees before first difference")
            if normalized(prior_action) != actual:
                active["record"]["realized"] = True
                active["record"]["first_difference_callback"] = callback
                active.pop("prior")
                active.pop("committed")
        # After a first difference both branches are discarded for this interval.
    if active is not None:
        active["record"]["end_callback_exclusive"] = len(records)
    return {"callbacks": len(records), "receipts": len(receipt_ids), "receipt_records": receipt_records,
            "verification_issuances": issuance_records, "requests": requests,
            "selector_decisions": decisions, "revisions": revisions,
            "committed_revisions": len(revisions),
            "realized_revisions": sum(r["realized"] for r in revisions),
            "phase_differences": {str(p): phase_differences[p] for p in (1, 2, 3)},
            "phase_exposure": sorted(phase_exposure)}


def context_for(seat: str, seed: int, tick_limit: int = 1000) -> MatchContextV2:
    rng = random.Random(derive_agent_seed(seed, 0 if seat == "A" else 1, seat, api_version=2))
    return MatchContextV2(seat, seed, 512, tick_limit, rng, sensing_window=27)


def variant_for(row: str, protocol: dict[str, Any]) -> Variant:
    from .selectors import Schedule
    if row == "A":
        return Variant()
    if row in ("MEDIUM", "SPARSE"):
        return Variant(kind="fixed", mode=Mode[row])
    plan = next((s for s in protocol["schedules"] if s["id"] == row), None)
    if plan is None:
        raise IntegrityError("not a prospective policy row")
    return Variant(kind="schedule", schedule=Schedule(Mode[plan["initial"]],
                                                      tuple(plan["edges"]), plan["clock"]))
