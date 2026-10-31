"""R1 supplied observations, native witnesses, source/input trust and copy safety."""

from __future__ import annotations

import ast
import io
import json
import random
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from battle_client.sensing import PhasePosition, SampleStatus, SensingCursor, SensingView
from battle_client.session import ReplaySession
from battle_engine import sensing_demo
from battle_engine.agent_api import ActionKindV2, MatchContextV2, ObservationV2
from battle_engine.agent_capabilities import AgentCapabilityMismatchError
from battle_engine.agent_parameters import AgentParameterError, resolve_parameters
from battle_engine.agent_scaffold import AgentScaffoldError, create_agent
from battle_engine.agent_validation import AgentValidationFailedError, validate_agent
from battle_engine.agent_worker import (
    AgentWorkerHandle,
    WorkerCallStatus,
    _handle_load,
    _WorkerState,
    agent_spec_to_payload,
)
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.data.starter_agents.v6_roaming_reacquirer.agent import (
    HOLD,
    SEARCH,
    SEARCH_AFTER_ABSENCE,
    RoamingReacquirerAgent,
)
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID as ALPHA
from battle_engine.rules import BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID as PASSIVE
from battle_engine.sensing_playback import (
    ArtifactIntegrityError,
    ExchangePhase,
    ExchangeReconstructionError,
    evaluate_reacquirer_policy,
    reconstruct_sensing_playback,
    verify_demonstration,
    verify_keeper_scenario,
    verify_reacquirer_scenario,
)
from battle_engine.starters import (
    CURRENT_STARTER_DIGESTS,
    STARTER_AGENT_NAMES,
    starter_content_digest,
)

ROOT = Path(__file__).resolve().parents[2]
REACQUIRER = sensing_demo.resolve_teaching_agent_dir("v6_roaming_reacquirer", resource_root=ROOT)
FIXTURE = sensing_demo.resolve_teaching_agent_dir("v6_relocating_opponent", resource_root=ROOT)
# Predicted section 7 witnesses, (tick, zero-based global decision index).
PREDICTED = {
    "A": {"sense91": 0, "contact": 1, "rescan": 8, "absence": 9, "sense155": 12, "response": 13, "relocation": 7},
    "B": {"sense91": 2, "contact": 3, "rescan": 10, "absence": 11, "sense155": 14, "response": 15, "relocation": 5},
}
IDENTITY_WORDING = ("same", "moved", "reacquired", "identity", "ttl", "expired", "notif", "tracking", "lost")


def _agent(**params):
    agent = RoamingReacquirerAgent()
    agent.reset(MatchContextV2("A", 0, 512, 100, random.Random(0), params, sensing_window=27))
    return agent


def _obs(anchor=0, core=None, **changes):
    obs = ObservationV2(1, 0, 0, "main", anchor, 128, anchor if core is None else core, 8, (), False, None, None)
    return replace(obs, **changes)


def _receipt(sample, anchor=0, core=None, tick=1, **changes):
    return _obs(anchor, core, previous_action_applied=True, previous_sense_anchors=sample,
                previous_action_tick=tick, **changes)


def _triple(action):
    return (action.kind, action.operand, action.value)


def _hold_contact(agent, base=0):
    """R1 SENSE, R2 positive receipt and its first paid READ."""
    assert _triple(agent.act(_obs(base))) == (ActionKindV2.SENSE, (base + 91) % 512, None)
    return agent.act(_receipt(((base + 91) % 512,), base))


def _after_absence(agent):
    """Drive R1..R6 with supplied feedback; the agent is then searching after absence at anchor 64."""
    _hold_contact(agent)
    agent.act(_obs(previous_action_applied=True))
    agent.act(_obs(previous_action_applied=True))
    assert _triple(agent.act(_obs(previous_action_applied=True))) == (ActionKindV2.SENSE, 91, None)
    assert _triple(agent.act(_receipt((), tick=1))) == (ActionKindV2.MOVE, 64, None)
    assert _triple(agent.act(_obs(64, core=0, previous_action_applied=True))) == (ActionKindV2.SENSE, 155, None)


# ---------------------------------------------------------------------------
# Supplied observations: every section 5 row, I1-I3, direction and bounds
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("base", [0, 133, 509])
def test_r1_supplied_sequence_is_anchor_relative_one_action_per_callback(base):
    agent = _agent()
    def at(offset):
        return (base + offset) % 512
    script = [
        (_obs(base), (ActionKindV2.SENSE, at(91), None)),
        (_receipt((at(91),), base), (ActionKindV2.READ, base, None)),
        (_obs(base, previous_action_applied=True), (ActionKindV2.READ, base, None)),
        (_obs(base, previous_action_applied=True), (ActionKindV2.READ, base, None)),
        (_obs(base, previous_action_applied=True), (ActionKindV2.SENSE, at(91), None)),
        (_receipt((), base), (ActionKindV2.MOVE, 64, None)),
        (_obs(at(64), core=base, previous_action_applied=True), (ActionKindV2.SENSE, at(155), None)),
        (_receipt((at(155),), at(64), core=base), (ActionKindV2.WRITE, at(155), 0x52)),
        # Entering HOLD after the response WRITE starts the paid wait next callback.
        (_obs(at(64), core=base, previous_action_applied=True), (ActionKindV2.READ, base, None)),
        (_obs(at(64), core=base, previous_action_applied=True), (ActionKindV2.READ, base, None)),
        (_obs(at(64), core=base, previous_action_applied=True), (ActionKindV2.READ, base, None)),
        (_obs(at(64), core=base, previous_action_applied=True), (ActionKindV2.SENSE, at(155), None)),
        (_receipt((at(155),), at(64), core=base), (ActionKindV2.READ, base, None)),
    ]
    for observation, expected in script:
        action = agent.act(observation)
        assert _triple(action) == expected
        if action.kind == ActionKindV2.MOVE:
            assert abs(action.operand) <= min(agent.move_step, 64)
    assert agent.callbacks == len(script)
    assert agent.findings == [("absent_in_newer_sample", at(91)), ("new_anonymous_contact", at(155))]
    process, = agent.declare_processes()
    assert (process.id, process.reach, process.share) == ("main", 128, 1.0)


def test_rescan_with_old_address_records_newer_sample_and_restarts_paid_wait():
    agent = _agent(rescan_wait=1)
    assert _hold_contact(agent).kind == ActionKindV2.READ
    assert _triple(agent.act(_obs(previous_action_applied=True))) == (ActionKindV2.SENSE, 91, None)
    action = agent.act(_receipt((80, 91), tick=4))
    assert _triple(action) == (ActionKindV2.READ, 0, None)
    assert agent.mode == HOLD and agent.target == 91 and agent.findings == []
    assert agent.samples == [(1, 91, (91,)), (4, 91, (80, 91))]


def test_absent_rescan_records_only_absence_and_keeps_other_addresses_as_samples():
    agent = _agent()
    _hold_contact(agent)
    for _ in range(3):
        agent.act(_obs(previous_action_applied=True))
    action = agent.act(_receipt((70,), tick=2))
    # No WRITE to 70 and no claim that 70 is the old contact.
    assert _triple(action) == (ActionKindV2.MOVE, 64, None)
    assert agent.mode == SEARCH_AFTER_ABSENCE and agent.target is None
    assert agent.findings == [("absent_in_newer_sample", 91)]
    assert agent.samples[-1] == (2, 91, (70,))
    assert _triple(agent.act(_obs(64, core=0, previous_action_applied=True))) == (ActionKindV2.SENSE, 155, None)


@pytest.mark.parametrize("contact,move_step,first_move", [(300, 64, 64), (250, 10, 10), (320, 64, 64), (376, 64, -64)])
def test_response_direction_bounds_and_single_write(contact, move_step, first_move):
    agent = _agent(move_step=move_step)
    _hold_contact(agent)
    for _ in range(3):
        agent.act(_obs(previous_action_applied=True))
    agent.act(_receipt(()))
    anchor = move_step
    assert _triple(agent.act(_obs(anchor, core=0, previous_action_applied=True))) == (
        ActionKindV2.SENSE, (anchor + 91) % 512, None)
    action = agent.act(_receipt((contact,), anchor, core=0))
    # 320 is an exact tie from anchor 64 (256 either way): forward wins.
    assert _triple(action) == (ActionKindV2.MOVE, first_move, None)
    assert agent.findings[-1] == ("new_anonymous_contact", contact)
    while action.kind == ActionKindV2.MOVE:
        assert abs(action.operand) <= move_step
        anchor = (anchor + action.operand) % 512
        action = agent.act(_obs(anchor, core=0, previous_action_applied=True))
    assert _triple(action) == (ActionKindV2.WRITE, contact, 0x52)
    assert agent.act(_obs(anchor, core=0, previous_action_applied=True)).kind == ActionKindV2.READ


def test_in_reach_new_contact_selects_smallest_address_and_writes_once():
    agent = _agent()
    _after_absence(agent)
    assert _triple(agent.act(_receipt((170, 155), 64, core=0))) == (ActionKindV2.WRITE, 155, 0x52)
    for _ in range(3):
        assert agent.act(_obs(64, core=0, previous_action_applied=True)).kind == ActionKindV2.READ
    assert _triple(agent.act(_obs(64, core=0, previous_action_applied=True))) == (ActionKindV2.SENSE, 155, None)


def test_i1_empty_first_search_stays_in_discovery_without_inventing_a_target():
    agent = _agent()
    assert agent.act(_obs()).kind == ActionKindV2.SENSE
    assert _triple(agent.act(_receipt(()))) == (ActionKindV2.MOVE, 64, None)
    assert (agent.mode, agent.target, agent.findings) == (SEARCH, None, [])
    assert agent.samples == [(1, 91, ())]
    # Empty search alternates with forward MOVE; it is not a sensor error.
    assert _triple(agent.act(_obs(64, core=0, previous_action_applied=True))) == (ActionKindV2.SENSE, 155, None)
    assert _triple(agent.act(_receipt((), 64, core=0))) == (ActionKindV2.MOVE, 64, None)
    assert _triple(agent.act(_obs(128, core=0, previous_action_applied=True))) == (ActionKindV2.SENSE, 219, None)
    # A later positive receipt in discovery is an initial contact: HOLD, no WRITE.
    assert _triple(agent.act(_receipt((219,), 128, core=0))) == (ActionKindV2.READ, 0, None)
    assert (agent.mode, agent.target, agent.findings) == (HOLD, 219, [])


@pytest.mark.parametrize("applied,sample", [(False, None), (True, None), (False, (91,)), (False, ())])
def test_i2_refused_null_or_absent_rescan_infers_nothing_and_keeps_original_age(applied, sample):
    agent = _agent()
    _hold_contact(agent)
    for _ in range(3):
        agent.act(_obs(previous_action_applied=True))
    history = list(agent.samples)
    action = agent.act(_obs(current_tick=9, previous_action_tick=9, previous_action_applied=applied,
                            previous_sense_anchors=sample))
    # A fresh anchor-relative search; no absence, relocation or refreshed sample.
    assert _triple(action) == (ActionKindV2.SENSE, 91, None)
    assert (agent.mode, agent.target, agent.findings) == (SEARCH, None, [])
    assert agent.samples == history == [(1, 91, (91,))]
    # A following positive receipt is discovery again, never a new-contact WRITE.
    assert _triple(agent.act(_receipt((91,), tick=10))) == (ActionKindV2.READ, 0, None)
    assert agent.findings == []


def test_i2_refused_search_after_absence_keeps_that_search_mode():
    agent = _agent()
    _after_absence(agent)
    action = agent.act(_obs(64, core=0, previous_action_applied=False))
    assert _triple(action) == (ActionKindV2.SENSE, 155, None)
    assert agent.mode == SEARCH_AFTER_ABSENCE
    assert agent.findings == [("absent_in_newer_sample", 91)]


def test_i3_fallback_is_counted_once_per_emitting_callback_and_never_a_scan():
    agent = _agent()
    agent.sensing_window = None
    actions = [agent.act(_obs(previous_action_applied=True, previous_sense_anchors=(91,))) for _ in range(5)]
    assert [_triple(a) for a in actions] == [(ActionKindV2.READ, 0, None)] * 5
    assert agent.fallbacks == 5 and agent.samples == [] and agent.findings == [] and agent.pending is None
    # Illegal search center: one fallback, then SEARCH is retried next callback.
    agent = _agent()
    assert _triple(agent.act(_obs(self_reach=50))) == (ActionKindV2.READ, 0, None)
    assert agent.fallbacks == 1
    assert _triple(agent.act(_obs(previous_action_applied=True))) == (ActionKindV2.SENSE, 91, None)
    assert agent.fallbacks == 1
    # Own core out of reach: MOVE(0), still one fallback and no search MOVE.
    agent = _agent()
    agent.sensing_window = None
    assert _triple(agent.act(_obs(300, core=0, self_reach=50))) == (ActionKindV2.MOVE, 0, None)
    assert agent.fallbacks == 1 and agent.findings == []


def test_illegal_rescan_center_resumes_search_without_absence():
    agent = _agent()
    _hold_contact(agent)
    for _ in range(2):
        agent.act(_obs(previous_action_applied=True))
    # The remembered address and the search center are out of current reach at
    # rescan time: discovery resumes through the legal fallback, with no absence.
    action = agent.act(_obs(previous_action_applied=True, self_reach=60))
    assert _triple(action) == (ActionKindV2.READ, 0, None) and agent.fallbacks == 1
    assert (agent.mode, agent.target, agent.findings) == (SEARCH, None, [])
    assert _triple(agent.act(_obs(previous_action_applied=True))) == (ActionKindV2.SENSE, 91, None)


def test_unrelated_feedback_is_never_a_scan_receipt():
    agent = _agent()
    _hold_contact(agent)
    history = list(agent.samples)
    action = agent.act(_obs(previous_action_applied=True, previous_read_value=0, previous_read_owner="B",
                            previous_sense_anchors=(300,)))
    assert _triple(action) == (ActionKindV2.READ, 0, None)
    assert agent.samples == history and agent.findings == []


def test_reset_clears_state():
    agent = _agent()
    _after_absence(agent)
    agent.reset(MatchContextV2("A", 0, 512, 100, random.Random(0), sensing_window=27))
    assert (agent.callbacks, agent.mode, agent.target, agent.wait, agent.pending) == (0, SEARCH, None, 0, None)
    assert agent.samples == [] and agent.findings == [] and agent.fallbacks == 0
    assert _triple(agent.act(_obs())) == (ActionKindV2.SENSE, 91, None)


@pytest.mark.parametrize("params", [
    {"search_offset": -1}, {"search_offset": 129}, {"move_step": 0}, {"move_step": 65},
    {"rescan_wait": 0}, {"rescan_wait": 9}, {"rescan_wait": True}, {"move_step": "sixty-four"},
])
def test_parameter_rejection_uses_canonical_schema(params):
    spec = agent_spec_from_dir(REACQUIRER)
    with pytest.raises(AgentParameterError):
        resolve_parameters(spec.parameter_schema, overrides=params)


@pytest.mark.parametrize("offset,step,wait", [(0, 1, 1), (128, 64, 8)])
def test_inclusive_parameter_bounds(offset, step, wait):
    spec = agent_spec_from_dir(REACQUIRER)
    params = resolve_parameters(spec.parameter_schema,
                                overrides={"search_offset": offset, "move_step": step, "rescan_wait": wait})
    assert params == {"search_offset": offset, "move_step": step, "rescan_wait": wait}
    agent = _agent(**params)
    assert _triple(agent.act(_obs(509))) == (ActionKindV2.SENSE, (509 + offset) % 512, None)
    agent.act(_receipt(((509 + offset) % 512,), 509))
    reads = 1
    while (action := agent.act(_obs(509, previous_action_applied=True))).kind == ActionKindV2.READ:
        reads += 1
    assert reads == wait and action.kind == ActionKindV2.SENSE


def test_source_audit_uses_only_delivered_observation_and_own_state():
    forbidden = {"seed", "rng", "random", "os", "sys", "time", "open", "Path", "importlib", "eval", "exec",
                 "__import__", "visible_enemy_anchor_addresses", "previous_read_value", "previous_read_owner"}
    for directory, allowed_imports in ((REACQUIRER, {"__future__", "battle_engine.agent_api"}),
                                       (FIXTURE, {"battle_engine.agent_api"})):
        tree = ast.parse((directory / "agent.py").read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert imports == allowed_imports and not any(isinstance(n, ast.Import) for n in ast.walk(tree))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert not names & forbidden
    manifest = json.loads((REACQUIRER / "agent.yaml").read_text())
    assert manifest["capabilities"] == {"version": 1, "required": ["sense"]}
    assert manifest["presets"]["standard"]["values"] == {"search_offset": 91, "move_step": 64, "rescan_wait": 3}
    assert "capabilities" not in json.loads((FIXTURE / "agent.yaml").read_text())


# ---------------------------------------------------------------------------
# Registration, personal copies and capability preflight routes
# ---------------------------------------------------------------------------


def test_personal_copy_manifest_source_retention_overwrite_and_registration(tmp_path):
    result = create_agent("my_reacquirer", data_root=tmp_path, resource_root=ROOT, template="roaming_reacquirer")
    original = json.loads((REACQUIRER / "agent.yaml").read_text())
    copied = json.loads(result.manifest_path.read_text())
    assert copied.pop("name") == "my_reacquirer"
    assert copied.pop("display") == "my_reacquirer (Roaming Reacquirer copy)"
    original.pop("name")
    original.pop("display")
    assert copied == original
    assert result.source_path.read_bytes() == (REACQUIRER / "agent.py").read_bytes()
    with pytest.raises(AgentScaffoldError, match="already exists"):
        create_agent("my_reacquirer", data_root=tmp_path, resource_root=ROOT, template="roaming_reacquirer")
    assert "v6_relocating_opponent" not in STARTER_AGENT_NAMES
    assert STARTER_AGENT_NAMES == ("v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer")
    assert starter_content_digest(REACQUIRER) == CURRENT_STARTER_DIGESTS["v6_roaming_reacquirer"]


def test_passive_ruleset_mismatch_precedes_import_and_artifacts_on_every_route(tmp_path):
    create_agent("reacquirer", data_root=tmp_path, resource_root=ROOT, template="roaming_reacquirer")
    marker = tmp_path / "imported"
    source = tmp_path / "agents/reacquirer/agent.py"
    # Module-level import evidence after the bundled body (its __future__ import stays first).
    source.write_text(source.read_text() + f"\nfrom pathlib import Path as _Path\n_Path({str(marker)!r}).touch()\n")
    spec = agent_spec_from_dir(source.parent)
    with pytest.raises(AgentCapabilityMismatchError):
        NativeMatchService().run(MatchRequest(
            config=Config(arena_size=512), entrants=(MatchEntrant.python("A", "reacquirer", 0, spec),),
            max_ticks=1, replay_path=tmp_path / "replay.jsonl", trace_path=tmp_path / "trace.jsonl",
            ruleset_id=PASSIVE,
        ))
    assert not any((tmp_path / name).exists() for name in ("replay.jsonl", "trace.jsonl", "result.json"))
    with pytest.raises(AgentValidationFailedError) as error:
        validate_agent("reacquirer", data_root=tmp_path, trace_path=tmp_path / "validate.jsonl", ruleset_id=PASSIVE)
    assert error.value.diagnostic.code == "agent_capability_unsupported"
    assert not (tmp_path / "validate.jsonl").exists()
    out = io.StringIO()
    _handle_load(_WorkerState(), {"spec": agent_spec_to_payload(spec), "agent_id": "A", "ruleset_id": PASSIVE}, out)
    assert json.loads(out.getvalue())["diagnostic"]["code"] == "agent_capability_unsupported"
    assert not marker.exists()
    handle = AgentWorkerHandle(agent_id="A", slot=0)
    handle.start()
    try:
        assert handle.load(spec, timeout=30.0, ruleset_id=PASSIVE).status is WorkerCallStatus.FAILED
        assert not marker.exists()
        assert handle.load(spec, timeout=30.0, ruleset_id=ALPHA).status is WorkerCallStatus.OK
    finally:
        handle.close()
    assert validate_agent("reacquirer", data_root=tmp_path, ruleset_id=ALPHA).dry_run_action.kind.value == "sense"


# ---------------------------------------------------------------------------
# Native both-seat scenario, entrant views and trusted verification
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def campaign(tmp_path_factory):
    root = tmp_path_factory.mktemp("reacquirer_campaign")
    original_root = sensing_demo.get_resource_root
    original_resolve = sensing_demo.resolve_teaching_agent_dir
    sensing_demo.get_resource_root = lambda: root
    sensing_demo.resolve_teaching_agent_dir = lambda name, **kw: original_resolve(name, resource_root=ROOT)
    try:
        runs = {}
        for seat in ("A", "B"):
            for repeat in (1, 2):
                runs[seat, repeat] = sensing_demo.run_reacquirer_demo(
                    root / f"runs/v6_alpha_m2/reacquirer/{seat}/{repeat}", reacquirer_seat=seat)
        runs["keeper"] = sensing_demo.run_keeper_demo(root / "runs/v6_alpha_m2/keeper/A/1", keeper_seat="A")
        yield runs
    finally:
        sensing_demo.get_resource_root = original_root
        sensing_demo.resolve_teaching_agent_dir = original_resolve


@pytest.mark.parametrize("seat", ["A", "B"])
def test_native_both_seats_reproduce_predicted_witnesses(campaign, seat):
    first, second = campaign[seat, 1], campaign[seat, 2]
    a = verify_reacquirer_scenario(first.demo_path, reacquirer_seat=seat)
    b = verify_reacquirer_scenario(second.demo_path, reacquirer_seat=seat)
    assert a.is_complete and b.is_complete and a == b
    assert (a.artifact_consistent, a.reconstruction_valid, a.source_capture_valid) == (True, True, True)
    p = PREDICTED[seat]
    w = a.witnesses
    assert w.contact_points[0] == (1, p["contact"])
    assert w.absence_points == ((1, p["absence"]),)
    assert w.reacquisition_points == ((1, p["response"]),) and w.response_points == ((1, p["response"]),)
    assert w.fallback_points == ()
    playback = reconstruct_sensing_playback(first.replay_path, first.trace_path, result_path=first.result_path)
    actions = {f.decision_index: f for f in playback.facts if f.phase == ExchangePhase.ACTION and f.tick == 1}
    def emitted(key):
        fact = actions[p[key]]
        return (fact.actor_id, fact.action_kind, fact.operand, fact.value, fact.sensed_anchors)
    fixture = "B" if seat == "A" else "A"
    assert emitted("sense91") == (seat, "sense", 91, None, (91,))
    assert emitted("rescan") == (seat, "sense", 91, None, ())
    assert emitted("absence") == (seat, "move", 64, None, None)
    assert emitted("sense155") == (seat, "sense", 155, None, (155,))
    assert emitted("response") == (seat, "write", 155, 0x52, None)
    assert emitted("relocation") == (fixture, "move", 64, None, None)
    assert actions[p["relocation"]].world_state.get_anchor(fixture, "main") == 155
    end = playback.facts[-1]
    assert end.tick == 100 and end.world_state.alive_entrants == frozenset({"A", "B"})
    # Fixture core 91..98 is never written by the Reacquirer.
    writes = [f for f in playback.facts if f.actor_id == seat and f.action_kind == "write"]
    assert writes and all(f.operand not in range(91, 99) for f in writes)
    assert first.replay_path.read_bytes() == second.replay_path.read_bytes()
    def logical_trace(path):
        return [{k: v for k, v in json.loads(line).items() if k != "wall_time_ms"} for line in path.read_text().splitlines()]
    assert logical_trace(first.trace_path) == logical_trace(second.trace_path)
    for run in (first, second):
        payload = json.loads(run.demo_path.read_text())
        assert payload["status"] == "unverified" and "teaching_exchange" not in payload
        with pytest.raises(ExchangeReconstructionError):
            verify_demonstration(run.demo_path)


@pytest.mark.parametrize("seat", ["A", "B"])
def test_trusted_verifiers_never_award_each_other(campaign, seat):
    with pytest.raises(ArtifactIntegrityError):
        verify_keeper_scenario(campaign[seat, 1].demo_path, keeper_seat=seat)
    with pytest.raises(ArtifactIntegrityError):
        verify_reacquirer_scenario(campaign["keeper"].demo_path, reacquirer_seat=seat)


@pytest.mark.parametrize("seat", ["A", "B"])
def test_entrant_views_record_absence_and_new_contact_without_identity_claims(campaign, seat):
    run = campaign[seat, 1]
    session = ReplaySession()
    session.load(run.replay_path)
    cursor = SensingCursor.from_paths(session, run.replay_path, run.trace_path, seat, result_path=run.result_path)
    rescan = cursor.seek(PhasePosition(1, 5, ExchangePhase.ACTION))
    assert isinstance(rescan, SensingView)
    assert [(c.address, c.not_present_in_newer_sample) for c in rescan.contacts] == [(91, None)]
    assert rescan.events[-1].sample_status == SampleStatus.PENDING
    absent = cursor.seek(PhasePosition(1, 6, ExchangePhase.OBSERVATION))
    assert absent.receipt_status == SampleStatus.EMPTY
    old, = absent.contacts
    assert old.address == 91 and old.sampled_at.callback == 1
    assert (old.not_present_in_newer_sample.tick, old.not_present_in_newer_sample.callback) == (1, 5)
    found = cursor.seek(PhasePosition(1, 8, ExchangePhase.OBSERVATION))
    assert [c.address for c in found.contacts] == [91, 155]
    assert found.contacts[0].not_present_in_newer_sample is not None
    assert found.contacts[1].not_present_in_newer_sample is None and found.contacts[1].age_ticks == 0
    assert found.opponent_activity == "Unobserved"
    text = " ".join([found.label, *(e.message for e in found.events)]).lower()
    assert not any(word in text for word in IDENTITY_WORDING)
    assert cursor.seek(PhasePosition(1, 6, ExchangePhase.OBSERVATION)) == absent
    # The fixture's own delivered view gains nothing from the Reacquirer's scans.
    other = cursor.switch_view("B" if seat == "A" else "A")
    view = other.seek(other.positions[-1])
    assert isinstance(view, SensingView) and view.contacts == () and view.samples == ()


@pytest.mark.parametrize("mutation", ["wrong_seat", "params", "source", "drift", "false_success", "claim", "binding", "missing_source"])
def test_scenario_rejects_false_provenance_and_success(campaign, tmp_path, mutation):
    target = tmp_path / "copy"
    shutil.copytree(campaign["A", 1].demo_path.parent, target)
    demo = target / "demo.json"
    payload = json.loads(demo.read_text())
    if mutation == "params":
        payload["entrants"][0]["parameters"]["rescan_wait"] = 2
    elif mutation == "source":
        with (target / "sources/A/agent.py").open("a") as file:
            file.write("\n# edited copy cannot inherit scenario completion\n")
    elif mutation == "drift":
        payload["entrants"][0]["loaded_final_fingerprint"] = "0" * 64
    elif mutation == "false_success":
        payload["status"] = "reproducible"
    elif mutation == "claim":
        payload["teaching_exchange"] = {"sequence_verified": True}
    elif mutation == "binding":
        with (target / "trace.jsonl").open("a") as file:
            file.write("\n")
    elif mutation == "missing_source":
        (target / "sources/A/agent.yaml").unlink()
    demo.write_text(json.dumps(payload))
    with pytest.raises((ArtifactIntegrityError, ExchangeReconstructionError)):
        verify_reacquirer_scenario(demo, reacquirer_seat="B" if mutation == "wrong_seat" else "A")
    if mutation != "binding":
        # The ordinary pair remains usable independently of the optional sidecar.
        reconstruct_sensing_playback(target / "replay.jsonl", target / "trace.jsonl", result_path=target / "result.json")


def test_valid_prefix_without_reacquisition_and_tampered_receipt_cannot_complete(campaign):
    run = campaign["A", 1]
    playback = reconstruct_sensing_playback(run.replay_path, run.trace_path)
    prefix = tuple(f for f in playback.facts if (f.tick, f.decision_index or 0) < (1, PREDICTED["A"]["response"]))
    witnesses = evaluate_reacquirer_policy(prefix, reacquirer_id="A")
    assert witnesses.contact_points and witnesses.absence_points
    assert not witnesses.reacquisition_points and not witnesses.response_points
    # A false "old address still present" receipt contradicts the emitted MOVE.
    facts = list(playback.facts)
    index = next(i for i, f in enumerate(facts) if f.actor_id == "A" and f.phase == ExchangePhase.OBSERVATION
                 and f.decision_index == PREDICTED["A"]["absence"])
    facts[index] = replace(facts[index], sensed_anchors=(91,))
    with pytest.raises(ExchangeReconstructionError, match="Reacquirer decision"):
        evaluate_reacquirer_policy(tuple(facts), reacquirer_id="A")
    # A refused-looking receipt is not a positive or absent transition either.
    facts = list(playback.facts)
    facts[index] = replace(facts[index], sensed_anchors=None, detail={**facts[index].detail, "previous_action_applied": False})
    with pytest.raises(ExchangeReconstructionError, match="Reacquirer decision"):
        evaluate_reacquirer_policy(tuple(facts), reacquirer_id="A")


@pytest.mark.parametrize("seat", ["A", "B"])
def test_nonzero_seeded_start_policy_is_anchor_relative(tmp_path, seat):
    spec, fixture = agent_spec_from_dir(REACQUIRER), agent_spec_from_dir(FIXTURE)
    starts = resolve_direct_match_starts(ruleset_id=ALPHA, arena_size=512,
        entrant_count=2, supplied_starts=(None, None), seed=27)
    core = starts[0 if seat == "A" else 1]
    assert core != 0
    entrants = [MatchEntrant.python(identity, "reacquirer" if identity == seat else "fixture", start,
                spec if identity == seat else fixture) for identity, start in zip(("A", "B"), starts)]
    NativeMatchService().run(MatchRequest(config=Config(arena_size=512, seed=27), entrants=tuple(entrants), max_ticks=1,
        replay_path=tmp_path / "replay.jsonl", trace_path=tmp_path / "trace.jsonl", ruleset_id=ALPHA))
    decisions = [json.loads(line) for line in (tmp_path / "trace.jsonl").read_text().splitlines() if '"decision_v2"' in line]
    own = [d for d in decisions if d["agent_id"] == seat]
    assert own[0]["action"]["kind"] == "sense" and own[0]["action"]["operand"] == (core + 91) % 512


def _delayed_match(root, *, ticks):
    """With rescan_wait 2 the rescan SENSE is R4, the second of its chunk; the
    fixture's third callback WRITEs at the Reacquirer's anchor and suppresses R5."""
    fixture = root / "fixture"
    fixture.mkdir(parents=True)
    (fixture / "agent.yaml").write_text(json.dumps({"kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent"}))
    (fixture / "agent.py").write_text(
        "from battle_engine.agent_api import AgentV2, AgentAction, ActionKindV2, ProcessDeclaration\n"
        "class Fixture(AgentV2):\n"
        "    def reset(self, context): self.calls = 0\n"
        "    def declare_processes(self): return [ProcessDeclaration('main',128,1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 3: return AgentAction(ActionKindV2.WRITE,0,0x45)\n"
        "        return AgentAction(ActionKindV2.READ,obs.own_core_base)\n"
        "def create_agent(): return Fixture()\n"
    )
    NativeMatchService().run(MatchRequest(
        config=Config(arena_size=512, seed=0), ruleset_id=ALPHA,
        entrants=(MatchEntrant.python("A", "reacquirer", 0, agent_spec_from_dir(REACQUIRER),
                                      parameters={"rescan_wait": 2}),
                  MatchEntrant.python("B", "scripted", 91, agent_spec_from_dir(fixture))),
        max_ticks=ticks, replay_path=root / "replay.jsonl", trace_path=root / "trace.jsonl",
    ))
    return reconstruct_sensing_playback(root / "replay.jsonl", root / "trace.jsonl", result_path=root / "result.json")


@pytest.mark.parametrize("ticks", [1, 2])
def test_native_suppression_delays_same_process_receipt_or_terminal_withholds_it(tmp_path, ticks):
    playback = _delayed_match(tmp_path, ticks=ticks)
    own = [f for f in playback.facts if f.actor_id == "A" and f.phase == ExchangePhase.ACTION]
    assert [(f.action_kind, f.operand) for f in own[:4]] == [("sense", 91), ("read", 0), ("read", 0), ("sense", 91)]
    rescan = own[3]
    assert rescan.tick == 1 and rescan.sensed_anchors == (91,)
    receipts = [f for f in playback.facts if f.actor_id == "A" and f.phase == ExchangePhase.OBSERVATION
                and f.sample_point == (1, rescan.decision_index)]
    if ticks == 1:
        # Terminal non-delivery: the sample was taken but never reached the entrant.
        assert receipts == [] and len(own) == 4
        return
    receipt, = receipts
    assert receipt.tick == 2 and receipt.sensed_anchors == (91,)
    action = next(f for f in playback.facts if f.phase == ExchangePhase.ACTION and f.decision_index == receipt.decision_index)
    # The delayed rescan receipt keeps its tick-1 sample point and is processed once:
    # the old address is present, so HOLD restarts with a paid wait READ.
    assert (action.action_kind, action.operand) == ("read", 0)


@pytest.mark.parametrize("relative", ["engine/escape", "runs/v6_alpha_m2/research/escape", "runs/v6_alpha_m2/e9_private/escape"])
def test_reacquirer_runner_rejects_unsafe_output_before_source_access(tmp_path, monkeypatch, relative):
    monkeypatch.setattr(sensing_demo, "get_resource_root", lambda: tmp_path)
    def unexpected_source(*args, **kwargs):
        raise AssertionError("unsafe output reached source capture")
    monkeypatch.setattr(sensing_demo, "resolve_teaching_agent_dir", unexpected_source)
    with pytest.raises(ValueError):
        sensing_demo.run_reacquirer_demo(tmp_path / relative)
    assert not (tmp_path / relative).exists()


def test_reacquirer_runner_preserves_existing_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(sensing_demo, "get_resource_root", lambda: tmp_path)
    out = tmp_path / "runs/v6_alpha_m2/retained"
    out.mkdir(parents=True)
    (out / "demo.json").write_bytes(b"retained evidence")
    with pytest.raises(FileExistsError):
        sensing_demo.run_reacquirer_demo(out)
    assert (out / "demo.json").read_bytes() == b"retained evidence"
