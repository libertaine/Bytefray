"""Offline audits of existing scripted qualification histories and masked revisions."""

import shutil
from copy import deepcopy
from dataclasses import replace

import pytest
from _e8_family_engine_harness import Plan, sigma_of
from _e9_harness import engine_history, make, observation, start
from battle_engine.agent_api import ActionKindV2, AgentAction
from battle_engine.agent_trace import DecisionRecordV2, read_trace_v2
from test_v6_e8_family_engine import decoy_opponent

from tools.research.v6.e9.artifacts import diagnostic, validate
from tools.research.v6.e9.behavior import _choose_tail, _set_mode, audit, context_for, normalized
from tools.research.v6.e9.protocol import Cell, IntegrityError, load_protocol
from tools.research.v6.e9.selectors import Mode


@pytest.mark.parametrize("seat", ["A", "B"])
def test_independent_receipt_request_commit_realization_and_no_payoff_use(tmp_path, seat):
    _, agent, _ = engine_history(tmp_path, seat, "Variant()", decoy_opponent(seat), ticks=16)
    trace = read_trace_v2(tmp_path / "legal/trace.jsonl")
    records = [r for r in trace.records if isinstance(r, DecisionRecordV2) and r.agent_id == seat]
    output = audit(records, context_for(seat, 7, 16))
    assert output["committed_revisions"] == 1
    assert output["realized_revisions"] == 1
    assert output["requests"][0]["withholding_passed"]
    assert output["requests"][0]["trigger_receipt_ids"]
    assert output["revisions"][0]["committed_mode"] == 4
    assert output["requests"][0]["requested_mode"] == 4
    assert output["requests"][0]["disposition"] == "satisfied"
    assert output["revisions"][0]["budget_remaining_before"] == 4
    for receipt in output["receipt_records"]:
        assert receipt["entrant"] == seat and receipt["process"] == "main"
        assert receipt["issuance_callback_ordinal"] + 1 == receipt["delivery_callback_ordinal"]
        issued = records[receipt["issuance_callback_ordinal"] - 1]
        assert issued.action.kind == "sense" and issued.action.operand % 512 == receipt["target"]
        assert issued.observation.current_tick == receipt["issue_tick"]
    other_cell = audit(records, context_for(seat, 7, 16), cell_identity="another-fixture")
    assert other_cell["receipt_records"][0]["identity"] != output["receipt_records"][0]["identity"]
    assert len(output["selector_decisions"]) == len(agent.diagnostics())
    assert "payoff" not in output and "winner" not in output
    corrupt = list(records)
    corrupt[-1] = replace(corrupt[-1], action=replace(corrupt[-1].action,
                                                    kind="write", operand=0, value=0))
    with pytest.raises(IntegrityError):
        audit(corrupt, context_for(seat, 7, 16))


@pytest.mark.parametrize("seat", ["A", "B"])
def test_missing_and_suppression_never_invent_feedback(tmp_path, seat):
    plan = decoy_opponent(seat, evade=(64 * sigma_of(7, seat),))
    _, agent, _ = engine_history(tmp_path, seat, "Variant()", plan, ticks=32)
    records = [r for r in read_trace_v2(tmp_path / "legal/trace.jsonl").records
               if isinstance(r, DecisionRecordV2) and r.agent_id == seat]
    output = audit(records, context_for(seat, 7, 32))
    assert output["committed_revisions"] == sum(d["before"]["mode"] != d["after"]["mode"]
                                               for d in agent.diagnostics())
    if seat == "A":
        assert [r["cause"] for r in output["requests"]] == ["confirmations", "missing"]
    else:
        assert output["committed_revisions"] == 0


def test_identical_commit_can_be_masked_then_realized_in_same_holding_interval():
    agent = make()
    start(agent)
    # Detached prestate after common observation absorption, at a phase where
    # both allocations are due. Terminating here yields a masked revision.
    agent.epoch, agent.callback_index = 4, 1
    agent.activation_epoch = 0
    agent.tick = 5
    prior, committed = deepcopy(agent), deepcopy(agent)
    _set_mode(prior, Mode.DENSE)
    _set_mode(committed, Mode.SPARSE)
    obs = observation(5)
    assert normalized(_choose_tail(prior, obs)) == normalized(_choose_tail(committed, obs))
    # The branches receive exactly the common recorded feedback until the
    # next first callback; phase 1 makes the identical commit consequential.
    issued_target = prior.verification.target
    feedback = observation(6, previous_tick=5, anchors=(issued_target,))
    assert normalized(prior.act(feedback)) != normalized(committed.act(feedback))


def test_same_attempt_validation_reconstructs_once_and_rejects_corruption(tmp_path):
    # Reuse the existing fixed qualification seed and a scripted stationary
    # opponent. This is a capability/artifact fixture, outside the E9 matrix.
    played, _, _ = engine_history(tmp_path / "fixture", "A", "Variant()", Plan(), ticks=1000)
    path = tmp_path / "artifacts"
    path.mkdir()
    source = tmp_path / "fixture/legal"
    shutil.copyfile(source / "run/result.json", path / "result.json")
    shutil.copyfile(source / "run/replay.jsonl", path / "replay.jsonl")
    shutil.copyfile(source / "trace.jsonl", path / "trace.jsonl")
    protocol = load_protocol()
    cell = Cell("A", "RUSH8", 1, "A")
    assert '"last_agent_standing"' in played.replay  # required legal terminal reached
    names = ("e9_focal", "scripted_b")
    result = diagnostic(path, cell, protocol, seed=7, package_names=names)
    assert result["behavior"]["callbacks"] > 0
    hashes = validate(path, cell, protocol, seed=7, package_names=names)
    assert hashes == validate(path, cell, protocol, seed=7, package_names=names)
    import json
    for case in ("missing_footer", "missing_callback", "false_sense", "invalid_action"):
        copied = tmp_path / case
        shutil.copytree(path, copied)
        records = [json.loads(line) for line in (copied / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        if case == "missing_footer":
            records.pop()
        elif case == "missing_callback":
            records.pop(next(i for i, r in enumerate(records) if r["record_type"] == "decision_v2"))
        else:
            target = next(r for r in records if r["record_type"] == "decision_v2"
                          and r.get("action", {}).get("kind") == "sense")
            if case == "false_sense":
                target["applied_result"]["sensed_anchors"] = []
            else:
                target["applied_result"]["status"] = "REJECTED_INVALID"
        (copied / "trace.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        with pytest.raises((ValueError, RuntimeError)):
            validate(copied, cell, protocol, seed=7, package_names=names)
    (path / "diagnostic.json").write_text('{"corrupt":true}', encoding="utf-8")
    with pytest.raises(IntegrityError):
        validate(path, cell, protocol, seed=7, package_names=names)


def test_undelivered_verification_is_retained_without_inventing_receipt(tmp_path):
    engine_history(tmp_path, "A", "Variant()", decoy_opponent("A"), ticks=16)
    records = [r for r in read_trace_v2(tmp_path / "legal/trace.jsonl").records
               if isinstance(r, DecisionRecordV2) and r.agent_id == "A"]
    full = audit(records, context_for("A", 7, 16))
    issuance = full["verification_issuances"][0]
    stop = issuance["issuance_callback_ordinal"]
    prefix = audit(records[:stop], context_for("A", 7, 16))
    assert prefix["verification_issuances"][-1]["delivery_callback_ordinal"] is None
    assert not prefix["receipt_records"]


def test_legal_action_normalization_prevents_false_realization():
    assert normalized(AgentAction(ActionKindV2.WRITE, 513, 257)) == ("write", 1, 1)
    assert normalized(AgentAction(ActionKindV2.WRITE, 1, 1)) == ("write", 1, 1)
    assert normalized(AgentAction(ActionKindV2.MOVE, 200)) == normalized(AgentAction(ActionKindV2.MOVE, 64))
    assert normalized(AgentAction(ActionKindV2.SENSE, -1)) == ("sense", 511, None)
