"""Bytefray V6 M1-3: Artifact Validation and Sensing-Exchange Reconstruction Test Suite.

Validates independent sensing-exchange reconstruction, artifact integrity,
demo.json provenance and hash bindings, pairwise consistency, cost/quota checks,
delivery ordering, and negative adversarial mutations.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_ALPHA1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)
from battle_engine.sensing_demo import (
    run_sensing_demo,
)
from battle_engine.sensing_playback import (
    DEMO_PROVENANCE,
    DEMO_SCHEMA,
    EXPECTED_RULESET_ID,
    ArtifactIntegrityError,
    ExchangeConsistencyError,
    ExchangePhase,
    ExchangeReconstructionError,
    SensingPlayback,
    VerificationStatus,
    reconstruct_sensing_playback,
    verify_demonstration,
    verify_demonstration_artifacts,
)
from battle_engine.sensing_playback import (
    main as playback_main,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scripted_pair(tmp_path: Path, label: str, script: list[str], a_start: int, max_ticks: int) -> Path:
    """Run a native v6 match of scripted entrant A against B READing its own core at 91.

    A follows ``script`` ("sense91", "move64", "write91", otherwise READ) and
    never reads its observation, so nothing it does can be caused by a receipt.
    """
    match_dir = tmp_path / label
    match_dir.mkdir(parents=True, exist_ok=True)
    specs = []
    for agent_name, agent_script in ((f"{label}_a", script), (f"{label}_b", [])):
        agent_dir = tmp_path / "agents" / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        source = (
            "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
            f"SCRIPT = {agent_script!r}\n"
            "class Scripted(AgentV2):\n"
            "    def __init__(self):\n"
            "        self.calls = 0\n"
            "    def declare_processes(self):\n"
            "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
            "    def act(self, obs):\n"
            "        step = SCRIPT[self.calls] if self.calls < len(SCRIPT) else 'read'\n"
            "        self.calls += 1\n"
            "        if step == 'sense91':\n"
            "            return AgentAction(ActionKindV2.SENSE, operand=91)\n"
            "        if step == 'move64':\n"
            "            return AgentAction(ActionKindV2.MOVE, operand=64)\n"
            "        if step == 'write91':\n"
            "            return AgentAction(ActionKindV2.WRITE, operand=91, value=0xDD)\n"
            "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
            "def create_agent():\n"
            "    return Scripted()\n"
        )
        (agent_dir / "agent.py").write_text(source, encoding="utf-8")
        (agent_dir / "agent.yaml").write_text(json.dumps({
            "name": agent_name,
            "kind": "python",
            "api_version": 2,
            "entrypoint": "agent.py:create_agent",
            "capabilities": {"version": 1, "required": ["sense"]},
        }), encoding="utf-8")
        spec = agent_spec_from_dir(agent_dir)
        assert spec is not None
        specs.append(spec)

    NativeMatchService().run(
        MatchRequest(
            config=Config(arena_size=512, instr_per_tick=8, seed=0),
            ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
            entrants=(
                MatchEntrant.python("A", f"{label}_a", a_start, specs[0]),
                MatchEntrant.python("B", f"{label}_b", 91, specs[1]),
            ),
            max_ticks=max_ticks,
            replay_path=match_dir / "replay.jsonl",
            trace_path=match_dir / "trace.jsonl",
        )
    )
    return match_dir


@pytest.fixture
def teaching_demo_artifacts(tmp_path: Path) -> Path:
    """Generate authoritative teaching demo artifacts using the native demo runner."""
    demo_dir = tmp_path / "demo_run"
    result = run_sensing_demo(output_dir=demo_dir, ticks=5)
    assert result.is_verified is True
    return demo_dir


def test_valid_demonstration_independent_reconstruction(teaching_demo_artifacts: Path) -> None:
    """Verify that a valid Window Scout demonstration is independently reconstructed."""
    demo_dir = teaching_demo_artifacts

    # 1. Artifact integrity check
    art_info = verify_demonstration_artifacts(demo_dir)
    assert art_info["payload"]["schema"] == DEMO_SCHEMA
    assert art_info["payload"]["provenance"] == DEMO_PROVENANCE
    assert art_info["payload"]["ruleset_id"] == EXPECTED_RULESET_ID

    # 2. End-to-end demonstration verification
    playback = verify_demonstration(demo_dir)
    assert isinstance(playback, SensingPlayback)
    assert playback.ruleset_id == EXPECTED_RULESET_ID
    assert playback.arena_size == 512
    assert playback.match_id.startswith("match_")

    # 3. Teaching verification findings
    verif = playback.teaching_verification
    assert verif is not None
    assert verif.is_verified is True

    assert verif.incomplete_info_before_sensing == VerificationStatus.VERIFIED
    assert verif.legal_sense_request == VerificationStatus.VERIFIED
    assert verif.one_action_sensing_cost == VerificationStatus.VERIFIED
    assert verif.historical_sample_captured == VerificationStatus.VERIFIED
    assert verif.anonymous_sample_delivered == VerificationStatus.VERIFIED
    assert verif.legal_move_informed == VerificationStatus.VERIFIED
    assert verif.optional_write_supported == VerificationStatus.VERIFIED

    # Check facts ordering
    ticks = [f.tick for f in playback.facts]
    assert ticks == sorted(ticks)

    # Check phases
    phases = [f.phase for f in playback.facts if f.tick == 1 and f.actor_id == "A"]
    assert ExchangePhase.OBSERVATION in phases
    assert ExchangePhase.ACTION in phases


def test_missing_and_corrupted_artifacts(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that missing or malformed artifacts are rejected with ArtifactIntegrityError."""
    # 1. Missing demo.json
    non_existent = tmp_path / "non_existent"
    with pytest.raises(ArtifactIntegrityError, match="not found"):
        verify_demonstration_artifacts(non_existent)

    # 2. Malformed JSON
    bad_json_dir = tmp_path / "bad_json"
    bad_json_dir.mkdir()
    (bad_json_dir / "demo.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="Malformed demonstration metadata"):
        verify_demonstration_artifacts(bad_json_dir)

    # 3. Non-dictionary JSON
    list_json_dir = tmp_path / "list_json"
    list_json_dir.mkdir()
    (list_json_dir / "demo.json").write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="must be a JSON object"):
        verify_demonstration_artifacts(list_json_dir)

    # 4. Missing referenced replay
    demo_copy = tmp_path / "missing_replay"
    shutil.copytree(teaching_demo_artifacts, demo_copy)
    (demo_copy / "replay.jsonl").unlink()
    with pytest.raises(ArtifactIntegrityError, match="not found"):
        verify_demonstration_artifacts(demo_copy)

    # 5. Missing referenced trace
    demo_copy_trace = tmp_path / "missing_trace"
    shutil.copytree(teaching_demo_artifacts, demo_copy_trace)
    (demo_copy_trace / "trace.jsonl").unlink()
    with pytest.raises(ArtifactIntegrityError, match="not found"):
        verify_demonstration_artifacts(demo_copy_trace)


def test_path_traversal_in_demo_artifacts_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that path traversal in artifact filenames is strictly rejected."""
    demo_copy = tmp_path / "traversal_demo"
    shutil.copytree(teaching_demo_artifacts, demo_copy)

    demo_json_path = demo_copy / "demo.json"
    payload = json.loads(demo_json_path.read_text(encoding="utf-8"))
    payload["artifacts"]["replay"]["filename"] = "../secret.jsonl"
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ArtifactIntegrityError, match="not found or unsafe"):
        verify_demonstration_artifacts(demo_copy)


def test_digest_and_binding_tampering_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that byte tampering in replay, trace, or result is detected and rejected."""
    # 1. Mutate replay bytes
    corrupt_replay_dir = tmp_path / "corrupt_replay"
    shutil.copytree(teaching_demo_artifacts, corrupt_replay_dir)
    replay_file = corrupt_replay_dir / "replay.jsonl"
    content = replay_file.read_bytes()
    replay_file.write_bytes(content + b"\n")
    with pytest.raises(ArtifactIntegrityError, match="Digest mismatch for 'replay'"):
        verify_demonstration_artifacts(corrupt_replay_dir)

    # 2. Mutate trace bytes
    corrupt_trace_dir = tmp_path / "corrupt_trace"
    shutil.copytree(teaching_demo_artifacts, corrupt_trace_dir)
    trace_file = corrupt_trace_dir / "trace.jsonl"
    content = trace_file.read_bytes()
    trace_file.write_bytes(content + b"\n")
    with pytest.raises(ArtifactIntegrityError, match="Digest mismatch for 'trace'"):
        verify_demonstration_artifacts(corrupt_trace_dir)

    # 3. Mutate result bytes
    corrupt_result_dir = tmp_path / "corrupt_result"
    shutil.copytree(teaching_demo_artifacts, corrupt_result_dir)
    result_file = corrupt_result_dir / "result.json"
    content = result_file.read_bytes()
    result_file.write_bytes(content + b" ")
    with pytest.raises(ArtifactIntegrityError, match="Digest mismatch for 'result'"):
        verify_demonstration_artifacts(corrupt_result_dir)


def test_false_demo_sidecar_assertions_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that false assertions in demo.json are rejected."""
    demo_copy = tmp_path / "false_demo"
    shutil.copytree(teaching_demo_artifacts, demo_copy)
    demo_json_path = demo_copy / "demo.json"

    # 1. False provenance
    payload = json.loads(demo_json_path.read_text(encoding="utf-8"))
    payload["provenance"] = "malicious_harness"
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="Unauthorized demo provenance"):
        verify_demonstration_artifacts(demo_copy)

    # 2. declared_product_fixture False
    payload["provenance"] = DEMO_PROVENANCE
    payload["declared_product_fixture"] = False
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="declared_product_fixture must be True"):
        verify_demonstration_artifacts(demo_copy)

    # 3. Wrong Ruleset ID
    payload["declared_product_fixture"] = True
    payload["ruleset_id"] = BYTEFRAY_RULESET_V4_ID
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="Unexpected demo ruleset_id"):
        verify_demonstration_artifacts(demo_copy)

    # 4. Mismatched match_id
    payload["ruleset_id"] = EXPECTED_RULESET_ID
    payload["match_id"] = "match_fabricated_id"
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="contradicts demo match_id"):
        verify_demonstration_artifacts(demo_copy)


def test_tampered_sensing_sample_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that tampering with the trace sensed_anchors sample is caught by independent reconstruction."""
    tampered_dir = tmp_path / "tampered_sample"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    trace_file = tampered_dir / "trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").splitlines()

    new_lines = []
    mutated = False
    for line in lines:
        if not mutated and '"sensed_anchors": [91]' in line:
            # Tamper the sample to [99]
            line = line.replace('"sensed_anchors": [91]', '"sensed_anchors": [99]')
            mutated = True
        new_lines.append(line)
    assert mutated is True
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update demo.json hash so file-level hash check passes, forcing reconstructor to catch the lie
    demo_json_path = tampered_dir / "demo.json"
    demo_data = json.loads(demo_json_path.read_text(encoding="utf-8"))
    demo_data["artifacts"]["trace"]["sha256"] = _sha256(trace_file)
    demo_json_path.write_text(json.dumps(demo_data), encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="trace recorded sensed_anchors .* but independent reconstruction derived"):
        verify_demonstration(tampered_dir)


def test_receipt_before_eligible_delivery_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that receiving a sensing reflection before an eligible SENSE action is rejected."""
    tampered_dir = tmp_path / "premature_receipt"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    trace_file = tampered_dir / "trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").splitlines()

    new_lines = []
    mutated = False
    for line in lines:
        if not mutated and '"record_type": "decision_v2"' in line and '"agent_id": "A"' in line:
            # Inject premature receipt on callback 1
            record = json.loads(line)
            record["observation"]["previous_sense_anchors"] = [91]
            line = json.dumps(record)
            mutated = True
        new_lines.append(line)
    assert mutated is True
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update demo.json hash
    demo_json_path = tampered_dir / "demo.json"
    demo_data = json.loads(demo_json_path.read_text(encoding="utf-8"))
    demo_data["artifacts"]["trace"]["sha256"] = _sha256(trace_file)
    demo_json_path.write_text(json.dumps(demo_data), encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="unexpected previous_sense_anchors .* when no delivery was pending"):
        verify_demonstration(tampered_dir)


def test_dropped_receipt_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that failing to deliver an owed sensing sample is rejected."""
    tampered_dir = tmp_path / "dropped_receipt"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    trace_file = tampered_dir / "trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").splitlines()

    new_lines = []
    mutated = False
    callbacks_a = 0
    for line in lines:
        if '"record_type": "decision_v2"' in line and '"agent_id": "A"' in line:
            callbacks_a += 1
            if callbacks_a == 2 and not mutated:
                # Callback 2 should receive previous_sense_anchors=[91]; drop it!
                record = json.loads(line)
                record["observation"].pop("previous_sense_anchors", None)
                line = json.dumps(record)
                mutated = True
        new_lines.append(line)
    assert mutated is True
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update demo.json hash
    demo_json_path = tampered_dir / "demo.json"
    demo_data = json.loads(demo_json_path.read_text(encoding="utf-8"))
    demo_data["artifacts"]["trace"]["sha256"] = _sha256(trace_file)
    demo_json_path.write_text(json.dumps(demo_data), encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="expected sensing delivery .* but previous_sense_anchors was ABSENT"):
        verify_demonstration(tampered_dir)


def test_receipt_refreshed_with_future_opponent_state_rejected(tmp_path: Path) -> None:
    """Adversarial check: opponent moves between sample and receipt.

    Delivered receipt MUST deliver the historical sample, NOT current truth.
    If receipt is artificially refreshed with future state, it must be rejected.
    """
    demo_dir = tmp_path / "moving_opponent_match"
    demo_dir.mkdir(parents=True, exist_ok=True)

    agent_dir_a = tmp_path / "agents" / "senser"
    agent_dir_a.mkdir(parents=True, exist_ok=True)
    source_a = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class SenserAgent(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            return AgentAction(ActionKindV2.SENSE, operand=91)\n"
        "        elif self.calls == 2:\n"
        "            return AgentAction(ActionKindV2.MOVE, operand=64)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return SenserAgent()\n"
    )
    (agent_dir_a / "agent.py").write_text(source_a, encoding="utf-8")
    (agent_dir_a / "agent.yaml").write_text(json.dumps({
        "name": "senser",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "capabilities": {"version": 1, "required": ["sense"]},
    }), encoding="utf-8")
    spec_a = agent_spec_from_dir(agent_dir_a)
    assert spec_a is not None

    agent_dir_b = tmp_path / "agents" / "mover"
    agent_dir_b.mkdir(parents=True, exist_ok=True)
    source_b = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class MoverAgent(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            return AgentAction(ActionKindV2.MOVE, operand=8)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return MoverAgent()\n"
    )
    (agent_dir_b / "agent.py").write_text(source_b, encoding="utf-8")
    (agent_dir_b / "agent.yaml").write_text(json.dumps({
        "name": "mover",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec_b = agent_spec_from_dir(agent_dir_b)
    assert spec_b is not None

    replay_file = demo_dir / "replay.jsonl"
    trace_file = demo_dir / "trace.jsonl"
    service = NativeMatchService()
    req = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
        entrants=(
            MatchEntrant.python("A", "senser", 0, spec_a),
            MatchEntrant.python("B", "mover", 91, spec_b),
        ),
        max_ticks=5,
        replay_path=replay_file,
        trace_path=trace_file,
    )
    res = service.run(req)
    assert res.ticks_run > 0
    assert replay_file.is_file()
    assert trace_file.is_file()

    # Normal independent reconstruction succeeds because delivered sample (91,) matches sample time
    playback = reconstruct_sensing_playback(
        replay_path=replay_file,
        trace_path=trace_file,
    )
    assert playback.ruleset_id == BYTEFRAY_RULESET_V6_ALPHA1_ID

    # 2. Mutate trace so receipt is refreshed to opponent's NEW position (99)
    tampered_dir = tmp_path / "refreshed_future_receipt"
    shutil.copytree(demo_dir, tampered_dir)
    tampered_trace = tampered_dir / "trace.jsonl"
    lines = tampered_trace.read_text(encoding="utf-8").splitlines()

    new_lines = []
    callbacks_a = 0
    for line in lines:
        if '"record_type": "decision_v2"' in line and '"agent_id": "A"' in line:
            callbacks_a += 1
            if callbacks_a == 2:
                # Refreshed to future position 99!
                assert '"previous_sense_anchors": [91]' in line
                line = line.replace('"previous_sense_anchors": [91]', '"previous_sense_anchors": [99]')
        new_lines.append(line)
    tampered_trace.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="delivered previous_sense_anchors .* does not match sampled anchors"):
        reconstruct_sensing_playback(
            replay_path=tampered_dir / "replay.jsonl",
            trace_path=tampered_trace,
        )


def test_missing_or_contradictory_movement_evidence_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that contradictory movement evidence between trace and replay is caught."""
    tampered_dir = tmp_path / "contradictory_movement"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    trace_file = tampered_dir / "trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").splitlines()

    new_lines = []
    mutated = False
    for line in lines:
        if not mutated and '"kind": "move"' in line:
            # Change move operand to 10
            line = line.replace('"operand": 64', '"operand": 10').replace('"normalized_address": 64', '"normalized_address": 10')
            mutated = True
        new_lines.append(line)
    assert mutated is True
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    with pytest.raises(
        ExchangeConsistencyError,
        match=r"(Tick \d+ decision \d+: .* observation self_anchor is \d+ but reconstructed anchor is \d+|reconstructed anchor .* does not match replay anchor)",
    ):
        reconstruct_sensing_playback(
            replay_path=tampered_dir / "replay.jsonl",
            trace_path=trace_file,
        )


def test_tick_end_replay_anchor_contradiction_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that tick-end reconciliation catches mismatch between reconstructed anchor and replay snapshot."""
    tampered_dir = tmp_path / "replay_anchor_mismatch"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    replay_file = tampered_dir / "replay.jsonl"
    trace_file = tampered_dir / "trace.jsonl"

    lines = replay_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    mutated = False
    for line in lines:
        if not mutated and '"record_type"' in line and '"processes"' in line:
            record = json.loads(line)
            if record.get("record_type") == "tick" and record.get("tick") == 1:
                record["processes"][0]["anchor"] = 15
                line = json.dumps(record)
                mutated = True
        new_lines.append(line)
    assert mutated is True
    replay_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update binding in trace.jsonl to match tampered replay digest
    new_replay_sha = _sha256(replay_file)
    trace_lines = trace_file.read_text(encoding="utf-8").splitlines()
    new_trace_lines = []
    for line in trace_lines:
        if '"record_type": "binding"' in line:
            record = json.loads(line)
            record["replay_sha256"] = new_replay_sha
            line = json.dumps(record)
        new_trace_lines.append(line)
    trace_file.write_text("\n".join(new_trace_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeConsistencyError, match=r"reconstructed anchor .* does not match replay anchor"):
        reconstruct_sensing_playback(
            replay_path=replay_file,
            trace_path=trace_file,
        )


def test_passive_enemy_visibility_in_active_ruleset_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that non-empty passive enemy visibility under active sensing ruleset is rejected."""
    tampered_dir = tmp_path / "passive_leak"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)

    trace_file = tampered_dir / "trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").splitlines()

    new_lines = []
    mutated = False
    for line in lines:
        if not mutated and '"visible_enemy_anchor_addresses": []' in line:
            line = line.replace('"visible_enemy_anchor_addresses": []', '"visible_enemy_anchor_addresses": [91]')
            mutated = True
        new_lines.append(line)
    assert mutated is True
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="active sensing forbids passive enemy visibility"):
        reconstruct_sensing_playback(
            replay_path=tampered_dir / "replay.jsonl",
            trace_path=trace_file,
        )


def test_truncated_sequence_reports_not_proven(tmp_path: Path) -> None:
    """Verify that a truncated sequence reports subsequent steps as NOT_PROVEN without guessing.

    SENSE(91) is A's eighth and last action of the only tick, so the tick limit
    ends the match before the receipt callback. The recording is internally
    consistent but must not count as a completed teaching exchange.
    """
    match_dir = _scripted_pair(tmp_path, "sense_last", ["read"] * 7 + ["sense91"], a_start=0, max_ticks=1)

    playback = reconstruct_sensing_playback(
        replay_path=match_dir / "replay.jsonl",
        trace_path=match_dir / "trace.jsonl",
        result_path=match_dir / "result.json",
    )
    a_actions = [f for f in playback.facts if f.phase == ExchangePhase.ACTION and f.actor_id == "A"]
    assert len(a_actions) == 8
    assert a_actions[-1].action_kind == "sense"

    verif = playback.teaching_verification
    assert verif is not None
    assert verif.incomplete_info_before_sensing == VerificationStatus.VERIFIED
    assert verif.legal_sense_request == VerificationStatus.VERIFIED
    assert verif.one_action_sensing_cost == VerificationStatus.VERIFIED
    assert verif.historical_sample_captured == VerificationStatus.VERIFIED
    assert verif.anonymous_sample_delivered == VerificationStatus.NOT_PROVEN
    assert verif.legal_move_informed == VerificationStatus.NOT_PROVEN
    assert verif.optional_write_supported == VerificationStatus.NOT_PROVEN
    assert verif.is_verified is False


def test_consistent_recording_without_required_move_is_not_verified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A digest-bound, consistent recording lacking MOVE(+64) passes integrity but is not a verified exchange."""
    demo_dir = tmp_path / "move_step_32"
    demo = run_sensing_demo(output_dir=demo_dir, ticks=5, parameters={"move_step": 32})
    assert demo.is_verified is False

    verify_demonstration_artifacts(demo_dir)
    playback = reconstruct_sensing_playback(
        demo.replay_path,
        demo.trace_path,
        result_path=demo.result_path,
        demo_path=demo.demo_path,
    )
    verif = playback.teaching_verification
    assert verif is not None
    assert verif.anonymous_sample_delivered == VerificationStatus.VERIFIED
    assert verif.legal_move_informed == VerificationStatus.NOT_VERIFIED
    assert verif.is_verified is False

    with pytest.raises(ExchangeReconstructionError, match="Demonstration verification failed"):
        verify_demonstration(demo_dir)
    assert playback_main([str(demo_dir)]) == 1

    # Pair mode accepts the consistent pair but must not present it as a teaching exchange.
    capsys.readouterr()
    assert playback_main(["--replay", str(demo.replay_path), "--trace", str(demo.trace_path)]) == 0
    pair_out = capsys.readouterr().out
    assert "Artifact pair integrity and consistency verified: True" in pair_out
    assert "Teaching exchange: NOT CLAIMED" in pair_out


def test_step_descriptions_name_evaluated_entrant_from_replay(
    teaching_demo_artifacts: Path, tmp_path: Path
) -> None:
    """Steps 1, 2 and 7 name the evaluated entrant from the replay header, not an assumed Window Scout."""
    step_names = [
        "incomplete_info_before_sensing",
        "legal_sense_request",
        "one_action_sensing_cost",
        "historical_sample_captured",
        "anonymous_sample_delivered",
        "legal_move_informed",
        "optional_write_supported",
    ]
    demo_verif = verify_demonstration(teaching_demo_artifacts).teaching_verification
    assert demo_verif is not None
    assert [s.name for s in demo_verif.steps] == step_names
    for step in (s for s in demo_verif.steps if s.step_index in (1, 2, 7)):
        assert step.status == VerificationStatus.VERIFIED
        assert step.description.startswith("Entrant A (v6_window_scout) ")

    # No entrant is named v6_window_scout, so pair mode falls back to A under its replay name.
    match_dir = _scripted_pair(
        tmp_path, "fallback", ["sense91", "move64", "write91"], a_start=0, max_ticks=1
    )
    verif = reconstruct_sensing_playback(
        match_dir / "replay.jsonl", match_dir / "trace.jsonl"
    ).teaching_verification
    assert verif is not None
    assert [s.name for s in verif.steps] == step_names
    for step in (s for s in verif.steps if s.step_index in (1, 2, 7)):
        assert step.status == VerificationStatus.VERIFIED
        assert step.description.startswith("Entrant A (fallback_a) ")
    assert all("Window Scout" not in s.description for s in verif.steps)


def test_step6_reports_receipt_consistent_movement_not_motivation(tmp_path: Path) -> None:
    """Step 6 verifies observable movement toward the delivered contact, never agent motivation.

    The scripted entrant ignores its observations, yet its artifacts show the
    same receipt-consistent MOVE as Window Scout; the verifier must not claim a
    cause. From anchor 200 the same MOVE(+64) leaves the contact and must not verify.
    """
    toward = _scripted_pair(tmp_path, "blind_toward", ["sense91", "move64"], a_start=0, max_ticks=1)
    verif = reconstruct_sensing_playback(toward / "replay.jsonl", toward / "trace.jsonl").teaching_verification
    assert verif is not None
    assert verif.is_verified is True
    step6 = next(s for s in verif.steps if s.step_index == 6)
    assert step6.status == VerificationStatus.VERIFIED
    assert (step6.evidence["anchor_before"], step6.evidence["anchor_after"]) == (0, 64)
    assert (step6.evidence["contact_distance_before"], step6.evidence["contact_distance_after"]) == (91, 27)
    assert step6.evidence["receipt_available_at_decision"] is True
    assert step6.evidence["motivation_established"] is False

    away = _scripted_pair(tmp_path, "blind_away", ["sense91", "move64"], a_start=200, max_ticks=1)
    verif_away = reconstruct_sensing_playback(away / "replay.jsonl", away / "trace.jsonl").teaching_verification
    assert verif_away is not None
    step6_away = next(s for s in verif_away.steps if s.step_index == 6)
    assert step6_away.status == VerificationStatus.NOT_VERIFIED
    assert (step6_away.evidence["anchor_before"], step6_away.evidence["anchor_after"]) == (200, 264)
    assert (step6_away.evidence["contact_distance_before"], step6_away.evidence["contact_distance_after"]) == (109, 173)
    assert verif_away.is_verified is False


def test_deterministic_verification_of_identical_artifacts(teaching_demo_artifacts: Path) -> None:
    """Verify that identical artifacts produce identical facts and verification outcomes."""
    playback1 = verify_demonstration(teaching_demo_artifacts)
    playback2 = verify_demonstration(teaching_demo_artifacts)

    assert playback1.match_id == playback2.match_id
    assert playback1.ruleset_id == playback2.ruleset_id
    assert len(playback1.facts) == len(playback2.facts)

    for f1, f2 in zip(playback1.facts, playback2.facts):
        assert f1.tick == f2.tick
        assert f1.decision_index == f2.decision_index
        assert f1.phase == f2.phase
        assert f1.actor_id == f2.actor_id
        assert f1.action_kind == f2.action_kind
        assert f1.status == f2.status
        assert f1.cost == f2.cost
        assert f1.sensed_anchors == f2.sensed_anchors
        assert f1.sample_point == f2.sample_point
        assert f1.delivery_point == f2.delivery_point

    assert playback1.teaching_verification == playback2.teaching_verification


def test_cli_interface_positive_and_negative(
    teaching_demo_artifacts: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI exit codes and behavior."""
    # 1. Valid demonstration directory -> exit 0
    exit_code = playback_main([str(teaching_demo_artifacts)])
    assert exit_code == 0
    assert "Demonstration verified: True" in capsys.readouterr().out

    # 2. Tampered demonstration directory -> exit 1
    corrupt_dir = tmp_path / "cli_corrupt"
    shutil.copytree(teaching_demo_artifacts, corrupt_dir)
    (corrupt_dir / "replay.jsonl").write_bytes(b"corrupt")
    exit_code_fail = playback_main([str(corrupt_dir)])
    assert exit_code_fail == 1

    # 3. Explicit replay and trace args -> exit 0, reporting pair integrity only
    replay_path = teaching_demo_artifacts / "replay.jsonl"
    trace_path = teaching_demo_artifacts / "trace.jsonl"
    capsys.readouterr()
    exit_code_pair = playback_main(["--replay", str(replay_path), "--trace", str(trace_path)])
    assert exit_code_pair == 0
    pair_out = capsys.readouterr().out
    assert "Artifact pair integrity and consistency verified: True" in pair_out
    assert "Teaching exchange: NOT CLAIMED" in pair_out
    assert "Demonstration verified" not in pair_out
    assert "Reconstruction verified" not in pair_out

    # 4. No args -> exit 2
    assert playback_main([]) == 2


def test_research_isolation_and_negative_imports(teaching_demo_artifacts: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify strict research isolation: M1-3 code cannot import tools.research or E8/E9 infrastructure."""
    real_import = builtins.__import__

    def strict_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if (
            "tools.research" in name
            or "tools/research" in name
            or "battle_engine.data.research" in name
            or "e9" in name
            or "e8" in name
        ):
            raise ImportError(f"Research isolation violation: blocked import of {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", strict_import)

    # Execute full verification under interceptor
    playback = verify_demonstration(teaching_demo_artifacts)
    assert playback.teaching_verification is not None
    assert playback.teaching_verification.is_verified is True


def test_incorrect_sensing_action_cost_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that incorrect action costs or discrepancies between trace and replay cpu_used are rejected."""
    # 1. Mutate replay snapshot cpu_used to disagree with trace action count
    tampered_dir = tmp_path / "tampered_cost_dir"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    replay_file = tampered_dir / "replay.jsonl"
    trace_file = tampered_dir / "trace.jsonl"

    lines = replay_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    mutated = False
    for line in lines:
        try:
            record = json.loads(line)
            if not mutated and record.get("tick") == 1 and "agents" in record:
                for agent in record["agents"]:
                    if agent["id"] == "A":
                        agent["cpu_used"] = 7
                line = json.dumps(record)
                mutated = True
        except Exception:
            pass
        new_lines.append(line)
    assert mutated is True
    replay_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update binding so trace binding matches new replay digest
    new_sha = _sha256(replay_file)
    trace_lines = trace_file.read_text(encoding="utf-8").splitlines()
    new_trace_lines = []
    for line in trace_lines:
        if '"record_type": "binding"' in line:
            b_rec = json.loads(line)
            b_rec["replay_sha256"] = new_sha
            line = json.dumps(b_rec)
        new_trace_lines.append(line)
    trace_file.write_text("\n".join(new_trace_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeConsistencyError, match="entrant A replay cpu_used 7 does not match trace actions count 8"):
        reconstruct_sensing_playback(replay_file, trace_file)


def test_action_budget_quota_exceeded_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that an entrant taking more actions than configured action_budget is rejected."""
    tampered_dir = tmp_path / "quota_exceeded_dir"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    trace_file = tampered_dir / "trace.jsonl"

    lines = trace_file.read_text(encoding="utf-8").splitlines()
    last_a_t1_idx = None
    for i, line in enumerate(lines):
        if '"record_type": "decision_v2"' in line and '"current_tick": 1' in line and '"agent_id": "A"' in line:
            last_a_t1_idx = i
    assert last_a_t1_idx is not None
    # Duplicate the 8th decision for entrant A in tick 1 to trigger quota exceed (9 > 8)
    lines.insert(last_a_t1_idx + 1, lines[last_a_t1_idx])
    trace_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="action budget exceeded for entrant A: 9 > 8"):
        reconstruct_sensing_playback(tampered_dir / "replay.jsonl", trace_file)


def test_impossible_action_ordering_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that out-of-order trace decisions (non-monotonic ticks) are rejected."""
    tampered_dir = tmp_path / "out_of_order_trace"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    trace_file = tampered_dir / "trace.jsonl"

    lines = trace_file.read_text(encoding="utf-8").splitlines()
    # Find two decision records with different ticks and swap them
    idx_t1 = None
    idx_t2 = None
    for i, line in enumerate(lines):
        if '"current_tick": 1' in line and idx_t1 is None:
            idx_t1 = i
        elif '"current_tick": 2' in line and idx_t2 is None:
            idx_t2 = i
    assert idx_t1 is not None and idx_t2 is not None

    lines[idx_t1], lines[idx_t2] = lines[idx_t2], lines[idx_t1]
    trace_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeConsistencyError, match="Impossible action ordering"):
        reconstruct_sensing_playback(tampered_dir / "replay.jsonl", trace_file)


def test_delayed_receipt_delivery_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that skipping delivery on callback 2 and delivering on callback 3 is rejected."""
    tampered_dir = tmp_path / "delayed_delivery_dir"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    trace_file = tampered_dir / "trace.jsonl"

    lines = trace_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    callbacks_a = 0
    for line in lines:
        if '"record_type": "decision_v2"' in line and '"agent_id": "A"' in line:
            callbacks_a += 1
            if callbacks_a == 2:
                # Callback 2 should receive previous_sense_anchors=[91]; remove it so delivery is missed
                rec = json.loads(line)
                rec["observation"].pop("previous_sense_anchors", None)
                line = json.dumps(rec)
            elif callbacks_a == 3:
                # Inject delayed delivery on callback 3
                rec = json.loads(line)
                rec["observation"]["previous_sense_anchors"] = [91]
                rec["observation"]["previous_action_applied"] = True
                line = json.dumps(rec)
        new_lines.append(line)
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="expected sensing delivery .* but previous_sense_anchors was ABSENT"):
        reconstruct_sensing_playback(tampered_dir / "replay.jsonl", trace_file)


def test_illegal_operands_and_values_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that non-integer or boolean operands and values are rejected with ExchangeReconstructionError."""
    tampered_dir = tmp_path / "illegal_operands_dir"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    trace_file = tampered_dir / "trace.jsonl"

    # 1. SENSE with boolean operand
    lines = trace_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if '"kind": "sense"' in line:
            line = line.replace('"operand": 91', '"operand": true')
        new_lines.append(line)
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="SENSE requires integer operand"):
        reconstruct_sensing_playback(tampered_dir / "replay.jsonl", trace_file)


def test_missing_required_result_artifact_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that a demonstration missing result.json or result entry in demo.json is rejected."""
    demo_copy = tmp_path / "missing_result_demo"
    shutil.copytree(teaching_demo_artifacts, demo_copy)

    # 1. Remove result file
    (demo_copy / "result.json").unlink()
    with pytest.raises(ArtifactIntegrityError, match="not found"):
        verify_demonstration_artifacts(demo_copy)

    # 2. Remove result entry from demo.json
    (demo_copy / "result.json").write_text("{}", encoding="utf-8")
    demo_json_path = demo_copy / "demo.json"
    payload = json.loads(demo_json_path.read_text(encoding="utf-8"))
    payload["artifacts"].pop("result", None)
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ArtifactIntegrityError, match="missing required entry for 'result'"):
        verify_demonstration_artifacts(demo_copy)


def test_false_demo_config_and_identity_assertions_rejected(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that false config, entrant identities, or result_id in demo.json are rejected."""
    demo_copy = tmp_path / "false_assertions_demo"
    shutil.copytree(teaching_demo_artifacts, demo_copy)
    demo_json_path = demo_copy / "demo.json"

    # 1. False result_id
    payload = json.loads(demo_json_path.read_text(encoding="utf-8"))
    orig_result_id = payload["result_id"]
    orig_entrants = [dict(e) for e in payload["entrants"]]
    payload["result_id"] = "result_fabricated_id"
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="contradicts demo result_id"):
        verify_demonstration_artifacts(demo_copy)

    # 2. False config arena_size
    payload["result_id"] = orig_result_id
    payload["config"]["arena_size"] = 1024
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="arena_size 1024 contradicts replay 512"):
        verify_demonstration(demo_copy)

    # 3. False entrants list
    payload["config"]["arena_size"] = 512
    payload["entrants"] = [{"agent_id": "A"}, {"agent_id": "C"}]
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="entrants .* contradict binding entrants"):
        verify_demonstration(demo_copy)

    # 4. Entrant names swapped so demo.json claims B is v6_window_scout; the replay header decides
    payload["entrants"] = orig_entrants
    for e in payload["entrants"]:
        e["name"] = {"A": "v6_stationary_opponent", "B": "v6_window_scout"}[e["agent_id"]]
    demo_json_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="name .* contradicts replay header name"):
        verify_demonstration(demo_copy)


def test_false_demo_narrative_teaching_assertions_rejected(tmp_path: Path) -> None:
    """Verify that false claims of sequence_verified=True in demo.json are caught and rejected."""
    demo_dir = tmp_path / "false_narrative_dir"
    # move_step=32 records a consistent exchange without the required MOVE(+64)
    res = run_sensing_demo(output_dir=demo_dir, ticks=5, parameters={"move_step": 32})

    demo_json = res.demo_path
    payload = json.loads(demo_json.read_text(encoding="utf-8"))
    # Crucial: demo.json falsely claims sequence_verified=True
    payload["teaching_exchange"]["sequence_verified"] = True
    payload["status"] = "reproducible"
    demo_json.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ExchangeReconstructionError, match="claims sequence_verified=True, but independent reconstruction failed"):
        verify_demonstration(demo_dir)


def test_step7_failed_write_causes_not_verified(teaching_demo_artifacts: Path, tmp_path: Path) -> None:
    """Verify that when later WRITE(91) is attempted but fails, Step 7 reports NOT_VERIFIED."""
    tampered_dir = tmp_path / "failed_write_dir"
    shutil.copytree(teaching_demo_artifacts, tampered_dir)
    trace_file = tampered_dir / "trace.jsonl"

    lines = trace_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if '"kind": "write"' in line:
            line = line.replace('"status": "APPLIED"', '"status": "REJECTED_OUT_OF_REACH"')
        new_lines.append(line)
    trace_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Reconstruct from raw pair (bypassing replay diff check for unit check of evaluate_teaching_exchange)
    from battle_engine.agent_trace import read_trace_v2
    doc = read_trace_v2(trace_file)
    from battle_engine.sensing_playback import SensingExchangeFact
    facts = []
    for idx, d in enumerate(doc.decisions):
        facts.append(
            SensingExchangeFact(
                tick=d.observation.current_tick,
                decision_index=idx,
                phase=ExchangePhase.OBSERVATION,
                actor_id=d.agent_id,
                process_id=d.process_id,
                action_kind=None,
                status=None,
                normalized_address=None,
                operand=None,
                value=None,
                cost=0,
                sample_point=(1, 0) if d.observation.previous_sense_anchors else None,
                delivery_point=(d.observation.current_tick, idx) if d.observation.previous_sense_anchors else None,
                audience=(d.agent_id,),
                sensed_anchors=tuple(d.observation.previous_sense_anchors) if isinstance(d.observation.previous_sense_anchors, (list, tuple)) else None,
                detail={"previous_action_applied": d.observation.previous_action_applied},
            )
        )
        if d.action:
            facts.append(
                SensingExchangeFact(
                    tick=d.observation.current_tick,
                    decision_index=idx,
                    phase=ExchangePhase.ACTION,
                    actor_id=d.agent_id,
                    process_id=d.process_id,
                    action_kind=d.action.kind,
                    status=d.applied_result.status if d.applied_result else None,
                    normalized_address=d.applied_result.normalized_address if d.applied_result else None,
                    operand=d.action.operand,
                    value=d.action.value,
                    cost=1,
                    sample_point=(1, idx) if d.action.kind == "sense" else None,
                    delivery_point=None,
                    audience=(),
                    sensed_anchors=(91,) if d.action.kind == "sense" else None,
                )
            )

    from battle_engine.sensing_playback import evaluate_teaching_exchange
    verif = evaluate_teaching_exchange(facts, arena_size=512)
    assert verif.optional_write_supported == VerificationStatus.NOT_VERIFIED
    assert verif.is_verified is False


def test_backward_compatibility_non_active_ruleset_rejected(tmp_path: Path) -> None:
    """Verify that passing a non-active ruleset (e.g. the passive research control) raises ExchangeReconstructionError."""
    v4_dir = tmp_path / "v4_match"
    v4_dir.mkdir(parents=True, exist_ok=True)
    replay_file = v4_dir / "replay.jsonl"
    trace_file = v4_dir / "trace.jsonl"

    agent_dir = tmp_path / "agents" / "stationary"
    agent_dir.mkdir(parents=True, exist_ok=True)
    source = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class Stationary(AgentV2):\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return Stationary()\n"
    )
    (agent_dir / "agent.py").write_text(source, encoding="utf-8")
    (agent_dir / "agent.yaml").write_text(json.dumps({
        "name": "stationary",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec = agent_spec_from_dir(agent_dir)
    assert spec is not None

    service = NativeMatchService()
    req = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        entrants=(
            MatchEntrant.python("A", "stationary", 0, spec),
            MatchEntrant.python("B", "stationary", 200, spec),
        ),
        max_ticks=2,
        replay_path=replay_file,
        trace_path=trace_file,
    )
    service.run(req)

    with pytest.raises(ExchangeReconstructionError, match="requires an active sensing ruleset"):
        reconstruct_sensing_playback(replay_file, trace_file)


def test_modular_boundary_wrapping_sensing_reconstruction(tmp_path: Path) -> None:
    """Verify independent spatial window evaluation across modular arena boundary (around address 0)."""
    boundary_dir = tmp_path / "boundary_match"
    boundary_dir.mkdir(parents=True, exist_ok=True)

    agent_dir_a = tmp_path / "agents" / "scout_boundary"
    agent_dir_a.mkdir(parents=True, exist_ok=True)
    source_a = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class BoundaryScout(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            # Anchor is 500, sensing target is 10 (circular distance = 22 <= 128)\n"
        "            return AgentAction(ActionKindV2.SENSE, operand=10)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return BoundaryScout()\n"
    )
    (agent_dir_a / "agent.py").write_text(source_a, encoding="utf-8")
    (agent_dir_a / "agent.yaml").write_text(json.dumps({
        "name": "scout_boundary",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "capabilities": {"version": 1, "required": ["sense"]},
    }), encoding="utf-8")
    spec_a = agent_spec_from_dir(agent_dir_a)
    assert spec_a is not None

    agent_dir_b = tmp_path / "agents" / "stationary_b"
    agent_dir_b.mkdir(parents=True, exist_ok=True)
    source_b = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class StationaryB(AgentV2):\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return StationaryB()\n"
    )
    (agent_dir_b / "agent.py").write_text(source_b, encoding="utf-8")
    (agent_dir_b / "agent.yaml").write_text(json.dumps({
        "name": "stationary_b",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec_b = agent_spec_from_dir(agent_dir_b)
    assert spec_b is not None

    replay_file = boundary_dir / "replay.jsonl"
    trace_file = boundary_dir / "trace.jsonl"
    service = NativeMatchService()
    req = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
        entrants=(
            MatchEntrant.python("A", "scout_boundary", 500, spec_a),
            MatchEntrant.python("B", "stationary_b", 15, spec_b),
        ),
        max_ticks=2,
        replay_path=replay_file,
        trace_path=trace_file,
    )
    res = service.run(req)
    assert res.ticks_run > 0

    # Opponent is at 15. Target is 10. Distance = 5 <= 27.
    # Independent reconstruction must correctly wrap across 0 and verify sensed_anchors = (15,)
    playback = reconstruct_sensing_playback(replay_file, trace_file)
    sense_facts = [f for f in playback.facts if f.action_kind == "sense"]
    assert len(sense_facts) == 1
    assert sense_facts[0].sensed_anchors == (15,)
    assert sense_facts[0].status == "APPLIED"
