"""K1 supplied observations, native witnesses, source/input trust and copy safety."""

from __future__ import annotations

import json
import random
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from battle_client.sensing import PhasePosition, SensingCursor, SensingView
from battle_client.session import ReplaySession
from battle_engine import sensing_demo
from battle_engine.agent_api import ActionKindV2, MatchContextV2, ObservationV2
from battle_engine.agent_capabilities import AgentCapabilityMismatchError
from battle_engine.agent_parameters import AgentParameterError, resolve_parameters
from battle_engine.agent_scaffold import AgentScaffoldError, create_agent
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.data.starter_agents.v6_watchful_keeper.agent import WatchfulKeeperAgent
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID as ALPHA
from battle_engine.rules import BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID as PASSIVE
from battle_engine.sensing_playback import (
    ArtifactIntegrityError,
    ExchangePhase,
    ExchangeReconstructionError,
    evaluate_keeper_policy,
    reconstruct_sensing_playback,
    verify_demonstration,
    verify_keeper_scenario,
)
from battle_engine.starters import (
    CURRENT_STARTER_DIGESTS,
    STARTER_AGENT_NAMES,
    starter_content_digest,
)

ROOT = Path(__file__).resolve().parents[2]
KEEPER = sensing_demo.resolve_teaching_agent_dir("v6_watchful_keeper", resource_root=ROOT)
FIXTURE = sensing_demo.resolve_teaching_agent_dir("v6_encroaching_opponent", resource_root=ROOT)


def _keeper(**params):
    agent = WatchfulKeeperAgent()
    agent.reset(MatchContextV2("A", 0, 512, 100, random.Random(0), params, sensing_window=27))
    return agent


def _obs(core=0, **changes):
    obs = ObservationV2(1, 0, 0, "main", core, 128, core, 8, (), False, None, None)
    return replace(obs, **changes)


@pytest.mark.parametrize("core", [0, 133, 509])
def test_core_relative_inspection_and_exact_cadence(core):
    agent = _keeper()
    expected = [0, 1, 2, None, 3, 4, 5, None, 6, 7, 0, None]
    for offset in expected:
        action = agent.act(_obs(core))
        assert action.kind == (ActionKindV2.SENSE if offset is None else ActionKindV2.READ)
        assert action.operand == (core + (27 if offset is None else offset)) % 512
    assert agent.declare_processes()[0].reach == 128
    assert agent.declare_processes()[0].share == 1


@pytest.mark.parametrize("owner", ["B", None])
def test_delivered_read_repairs_only_sampled_core_cell_and_then_inspects(owner):
    agent = _keeper()
    assert agent.act(_obs(509)).operand == 509
    repair = agent.act(_obs(509, previous_action_applied=True, previous_read_value=0, previous_read_owner=owner))
    assert (repair.kind, repair.operand, repair.value) == (ActionKindV2.WRITE, 509, 0x4B)
    # Even a repeated READ-looking payload after WRITE cannot cause a retry.
    following = agent.act(_obs(509, previous_action_applied=True, previous_read_value=0, previous_read_owner=owner))
    assert (following.kind, following.operand) == (ActionKindV2.READ, 510)


@pytest.mark.parametrize("applied,value,owner", [(False, 1, "B"), (True, None, "B"), (True, 1, "A"), (False, None, None)])
def test_missing_refused_and_own_read_do_not_invent_repair(applied, value, owner):
    agent = _keeper()
    agent.act(_obs())
    action = agent.act(_obs(previous_action_applied=applied, previous_read_value=value, previous_read_owner=owner))
    assert (action.kind, action.operand) == (ActionKindV2.READ, 1)


def test_repair_outranks_due_scan_and_illegal_repair_falls_through():
    agent = _keeper()
    for _ in range(3):
        agent.act(_obs())
    action = agent.act(_obs(previous_action_applied=True, previous_read_value=3, previous_read_owner="B"))
    assert (action.kind, action.operand) == (ActionKindV2.WRITE, 2)
    agent.reset(MatchContextV2("A", 0, 512, 100, random.Random(0), sensing_window=27))
    agent.act(_obs())
    action = agent.act(_obs(self_anchor=200, previous_action_applied=True, previous_read_value=3, previous_read_owner="B"))
    assert action.kind == ActionKindV2.READ


@pytest.mark.parametrize("sample,applied,target", [((), True, None), (None, False, None), (None, True, None), ((400, 27, 10), True, 10)])
def test_scan_feedback_distinctions_and_one_attempt(sample, applied, target):
    agent = _keeper()
    for _ in range(4):
        scan = agent.act(_obs())
    assert scan.kind == ActionKindV2.SENSE
    action = agent.act(_obs(current_tick=9, previous_action_applied=applied, previous_sense_anchors=sample))
    assert agent.callbacks == 5  # Suppressed time adds no synthetic callbacks.
    if target is None:
        assert action.kind == ActionKindV2.READ
    else:
        assert (action.kind, action.operand, action.value) == (ActionKindV2.WRITE, target, 0x4B)
    history = list(agent.sample_history)
    again = agent.act(_obs(previous_action_applied=True, previous_sense_anchors=sample))
    assert again.kind == ActionKindV2.READ
    assert agent.sample_history == history
    if sample is not None and applied:
        assert history == [(5, sample)]


def test_stale_coordinate_is_one_attempt_even_when_anchor_might_have_moved():
    agent = _keeper()
    for _ in range(4):
        agent.act(_obs())
    assert agent.act(_obs(current_tick=30, previous_action_applied=True, previous_sense_anchors=(27,))).operand == 27
    assert agent.act(_obs(current_tick=30, previous_action_applied=True)).kind == ActionKindV2.READ
    assert agent.sample_history == [(5, (27,))]


def test_unavailable_or_illegal_scan_falls_back_and_reset_clears_history():
    agent = _keeper()
    agent.sensing_window = None
    assert [agent.act(_obs()).kind for _ in range(8)] == [ActionKindV2.READ] * 8
    agent = _keeper()
    for _ in range(4):
        action = agent.act(_obs(self_reach=10))
    assert action.kind == ActionKindV2.READ
    agent = _keeper()
    for _ in range(4):
        agent.act(_obs())
    agent.act(_obs(previous_action_applied=True, previous_sense_anchors=(27,)))
    agent.reset(MatchContextV2("A", 0, 512, 100, random.Random(0), sensing_window=27))
    assert agent.sample_history == [] and agent.callbacks == 0 and agent.previous_action is None
    assert agent.act(_obs()).operand == 0


@pytest.mark.parametrize("params", [{"scan_interval": 1}, {"scan_interval": 17}, {"scan_interval": True}, {"scan_interval": "four"}, {"perimeter_offset": -1}, {"perimeter_offset": 129}])
def test_parameter_rejection_uses_canonical_schema(params):
    spec = agent_spec_from_dir(KEEPER)
    with pytest.raises(AgentParameterError):
        resolve_parameters(spec.parameter_schema, overrides=params)


@pytest.mark.parametrize("interval,offset", [(2, 0), (16, 128)])
def test_inclusive_parameter_bounds(interval, offset):
    spec = agent_spec_from_dir(KEEPER)
    params = resolve_parameters(spec.parameter_schema, overrides={"scan_interval": interval, "perimeter_offset": offset})
    agent = _keeper(**params)
    for _ in range(interval):
        action = agent.act(_obs(509))
    assert (action.kind, action.operand) == (ActionKindV2.SENSE, (509 + offset) % 512)


def test_personal_copy_manifest_and_source_retention_and_overwrite_refusal(tmp_path):
    result = create_agent("my_keeper", data_root=tmp_path, resource_root=ROOT, template="watchful_keeper")
    original = json.loads((KEEPER / "agent.yaml").read_text())
    copied = json.loads(result.manifest_path.read_text())
    assert copied.pop("name") == "my_keeper"
    assert copied.pop("display") == "my_keeper (Watchful Keeper copy)"
    original.pop("name")
    original.pop("display")
    assert copied == original
    assert result.source_path.read_bytes() == (KEEPER / "agent.py").read_bytes()
    with pytest.raises(AgentScaffoldError, match="already exists"):
        create_agent("my_keeper", data_root=tmp_path, resource_root=ROOT, template="watchful_keeper")
    assert "v6_encroaching_opponent" not in STARTER_AGENT_NAMES
    assert STARTER_AGENT_NAMES == ("v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer")
    assert starter_content_digest(KEEPER) == CURRENT_STARTER_DIGESTS["v6_watchful_keeper"]


def test_passive_ruleset_mismatch_precedes_import_and_artifacts(tmp_path):
    create_agent("keeper", data_root=tmp_path, resource_root=ROOT, template="watchful_keeper")
    source = tmp_path / "agents/keeper/agent.py"
    source.write_text("raise AssertionError('must not import before capability preflight')")
    spec = agent_spec_from_dir(source.parent)
    with pytest.raises(AgentCapabilityMismatchError):
        NativeMatchService().run(MatchRequest(
            config=Config(arena_size=512), entrants=(MatchEntrant.python("A", "keeper", 0, spec),),
            max_ticks=1, replay_path=tmp_path / "replay.jsonl", trace_path=tmp_path / "trace.jsonl",
            ruleset_id=PASSIVE,
        ))
    assert not any((tmp_path / name).exists() for name in ("replay.jsonl", "trace.jsonl", "result.json"))


@pytest.fixture(scope="module")
def campaign(tmp_path_factory):
    root = tmp_path_factory.mktemp("keeper_campaign")
    original_root = sensing_demo.get_resource_root
    original_resolve = sensing_demo.resolve_teaching_agent_dir
    sensing_demo.get_resource_root = lambda: root
    sensing_demo.resolve_teaching_agent_dir = lambda name, **kw: original_resolve(name, resource_root=ROOT)
    try:
        runs = {}
        for seat in ("A", "B"):
            for repeat in (1, 2):
                runs[seat, repeat] = sensing_demo.run_keeper_demo(root / f"runs/v6_alpha_m2/keeper/{seat}/{repeat}", keeper_seat=seat)
        yield runs
    finally:
        sensing_demo.get_resource_root = original_root
        sensing_demo.resolve_teaching_agent_dir = original_resolve


@pytest.mark.parametrize("seat", ["A", "B"])
def test_native_both_seats_reproduction_and_independent_witnesses(campaign, seat):
    first, second = campaign[seat, 1], campaign[seat, 2]
    a = verify_keeper_scenario(first.demo_path, keeper_seat=seat)
    b = verify_keeper_scenario(second.demo_path, keeper_seat=seat)
    assert a.is_complete and b.is_complete and a == b
    assert a.repair_points[0][0] == (3 if seat == "A" else 1)
    assert a.defensive_points[0][0] == 1
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
def test_both_delivered_views_hide_pending_contacts_and_rewind(campaign, seat):
    run = campaign[seat, 1]
    session = ReplaySession()
    session.load(run.replay_path)
    cursor = SensingCursor.from_paths(session, run.replay_path, run.trace_path, seat, result_path=run.result_path)
    request = cursor.seek(PhasePosition(1, 4, ExchangePhase.ACTION))
    assert isinstance(request, SensingView) and request.contacts == ()
    receipt = cursor.seek(PhasePosition(1, 5, ExchangePhase.OBSERVATION))
    assert receipt.contacts[0].address == 27
    assert receipt.opponent_activity == "Unobserved"
    assert cursor.seek(PhasePosition(1, 4, ExchangePhase.ACTION)) == request
    other = "B" if seat == "A" else "A"
    cursor = cursor.switch_view(other)
    view = cursor.seek(cursor.positions[-1])
    assert isinstance(view, SensingView) and view.contacts == ()


@pytest.mark.parametrize("mutation", ["wrong_seat", "params", "source", "drift", "false_success", "claim", "binding", "missing_source"])
def test_scenario_rejects_false_provenance_and_success(campaign, tmp_path, mutation):
    target = tmp_path / "copy"
    shutil.copytree(campaign["A", 1].demo_path.parent, target)
    demo = target / "demo.json"
    payload = json.loads(demo.read_text())
    if mutation == "params":
        payload["entrants"][0]["parameters"]["scan_interval"] = 2
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
        verify_keeper_scenario(demo, keeper_seat="B" if mutation == "wrong_seat" else "A")
    if mutation != "binding":
        # The ordinary pair remains usable independently of optional sidecar.
        reconstruct_sensing_playback(target / "replay.jsonl", target / "trace.jsonl", result_path=target / "result.json")


def test_valid_prefix_without_repair_and_tampered_read_cannot_prove_completion(campaign):
    run = campaign["A", 1]
    playback = reconstruct_sensing_playback(run.replay_path, run.trace_path)
    prefix = tuple(f for f in playback.facts if f.tick <= 1)
    repairs, defenses = evaluate_keeper_policy(prefix, keeper_id="A")
    assert not repairs and defenses
    # A false READ-owner narrative must fail independent sample reconstruction.
    facts = list(playback.facts)
    index = next(i for i, f in enumerate(facts) if f.actor_id == "A" and f.phase == ExchangePhase.OBSERVATION and f.read_value is not None)
    facts[index] = replace(facts[index], read_owner="B")
    with pytest.raises(ExchangeReconstructionError, match="READ receipt"):
        evaluate_keeper_policy(tuple(facts), keeper_id="A")


@pytest.mark.parametrize("seat", ["A", "B"])
def test_nonzero_seeded_core_policy_does_not_use_absolute_zero(tmp_path, seat):
    spec, fixture = agent_spec_from_dir(KEEPER), agent_spec_from_dir(FIXTURE)
    starts = resolve_direct_match_starts(ruleset_id=ALPHA, arena_size=512,
        entrant_count=2, supplied_starts=(None, None), seed=27)
    core = starts[0 if seat == "A" else 1]
    assert core != 0
    entrants = [MatchEntrant.python(identity, "keeper" if identity == seat else "fixture", start,
                spec if identity == seat else fixture) for identity, start in zip(("A", "B"), starts)]
    entrants.sort(key=lambda e: e.agent_id)
    NativeMatchService().run(MatchRequest(config=Config(arena_size=512, seed=27), entrants=tuple(entrants), max_ticks=1,
        replay_path=tmp_path / "replay.jsonl", trace_path=tmp_path / "trace.jsonl", ruleset_id=ALPHA))
    decisions = [json.loads(line) for line in (tmp_path / "trace.jsonl").read_text().splitlines() if '"decision_v2"' in line]
    own = [d for d in decisions if d["agent_id"] == seat]
    assert [d["action"]["operand"] for d in own[:4]] == [(core + offset) % 512 for offset in (0, 1, 2, 27)]


def _feedback_match(root, *, third_action, ticks):
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
        "        if self.calls == 1: return AgentAction(ActionKindV2.MOVE,-64)\n"
        f"        if self.calls == 3: return AgentAction(ActionKindV2.{third_action})\n"
        "        return AgentAction(ActionKindV2.READ,obs.own_core_base)\n"
        "def create_agent(): return Fixture()\n"
    )
    NativeMatchService().run(MatchRequest(
        config=Config(arena_size=512, seed=0), ruleset_id=ALPHA,
        entrants=(MatchEntrant.python("A", "keeper", 0, agent_spec_from_dir(KEEPER)),
                  MatchEntrant.python("B", "scripted", 91, agent_spec_from_dir(fixture))),
        max_ticks=ticks, replay_path=root / "replay.jsonl", trace_path=root / "trace.jsonl",
    ))
    return reconstruct_sensing_playback(root / "replay.jsonl", root / "trace.jsonl", result_path=root / "result.json")


@pytest.mark.parametrize("ticks", [1, 2])
def test_native_suppression_delays_same_process_receipt_or_terminal_withholds_it(tmp_path, ticks):
    playback = _feedback_match(tmp_path, third_action="WRITE,0,0x45", ticks=ticks)
    requests = [f for f in playback.facts if f.actor_id == "A" and f.action_kind == "sense"]
    assert requests[0].sensed_anchors == (27,)
    receipts = [f for f in playback.facts if f.actor_id == "A" and f.phase == ExchangePhase.OBSERVATION and f.sensed_anchors is not None]
    if ticks == 1:
        assert receipts == []
    else:
        assert receipts[0].tick == 2 and receipts[0].sensed_anchors == (27,)
        action = next(f for f in playback.facts if f.phase == ExchangePhase.ACTION and f.decision_index == receipts[0].decision_index)
        assert (action.action_kind, action.operand) == ("write", 27)


def test_native_stale_receipt_does_not_track_hidden_move(tmp_path):
    playback = _feedback_match(tmp_path, third_action="MOVE,64", ticks=1)
    receipt = next(f for f in playback.facts if f.actor_id == "A" and f.phase == ExchangePhase.OBSERVATION and f.sensed_anchors == (27,))
    assert receipt.world_state.get_anchor("B", "main") == 91
    action = next(f for f in playback.facts if f.phase == ExchangePhase.ACTION and f.decision_index == receipt.decision_index)
    assert (action.action_kind, action.operand) == ("write", 27)
    assert ("B", "main") not in action.world_state.disrupted_processes


@pytest.mark.parametrize("relative", ["engine/escape", "runs/v6_alpha_m2/research/escape", "runs/v6_alpha_m2/e9_private/escape"])
def test_keeper_runner_rejects_unsafe_output_before_source_access(tmp_path, monkeypatch, relative):
    monkeypatch.setattr(sensing_demo, "get_resource_root", lambda: tmp_path)
    def unexpected_source(*args, **kwargs):
        raise AssertionError("unsafe output reached source capture")
    monkeypatch.setattr(sensing_demo, "resolve_teaching_agent_dir", unexpected_source)
    with pytest.raises(ValueError):
        sensing_demo.run_keeper_demo(tmp_path / relative)
    assert not (tmp_path / relative).exists()


def test_keeper_runner_preserves_existing_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(sensing_demo, "get_resource_root", lambda: tmp_path)
    out = tmp_path / "runs/v6_alpha_m2/retained"
    out.mkdir(parents=True)
    (out / "demo.json").write_bytes(b"retained evidence")
    with pytest.raises(FileExistsError):
        sensing_demo.run_keeper_demo(out)
    assert (out / "demo.json").read_bytes() == b"retained evidence"
