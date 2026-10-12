"""Tools: Determinism and Negative Failure Cases Qualification Witness.

Executes repeatable determinism checks and negative failure/fallback cases
for M1-6A Windows Qualification.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile

from battle_client.sensing_presentation import load_sensing_presentation
from battle_client.session import ReplaySession
from battle_engine.agent_validation import (
    AgentValidationFailedError,
    validate_agent,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_ALPHA1_ID,
)
from battle_engine.sensing_demo import (
    run_sensing_demo,
)


def run_determinism(tmp_path: pathlib.Path) -> dict:
    dir1 = tmp_path / "det1"
    dir2 = tmp_path / "det2"
    dir1.mkdir(parents=True, exist_ok=True)
    dir2.mkdir(parents=True, exist_ok=True)

    res1 = run_sensing_demo(output_dir=dir1, ticks=100, seed=0)
    res2 = run_sensing_demo(output_dir=dir2, ticks=100, seed=0)
    assert res1.is_verified and res2.is_verified, "Both runs must be verified"
    assert res1.match_result.winner == res2.match_result.winner, "Winners must match"

    rep1_bytes = (dir1 / "replay.jsonl").read_bytes()
    rep2_bytes = (dir2 / "replay.jsonl").read_bytes()
    rep1_sha = hashlib.sha256(rep1_bytes).hexdigest()
    rep2_sha = hashlib.sha256(rep2_bytes).hexdigest()

    assert rep1_sha == rep2_sha, "Replay sha256 mismatch"
    rep_lines = (dir1 / "replay.jsonl").read_text(encoding="utf-8").splitlines()

    trace1_records = [
        json.loads(line)
        for line in (dir1 / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    trace2_records = [
        json.loads(line)
        for line in (dir2 / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert len(trace1_records) == len(trace2_records), "Trace record count mismatch"

    # Verify all records match ignoring wall_time_ms
    for r1, r2 in zip(trace1_records, trace2_records):
        c1 = {k: v for k, v in r1.items() if k != "wall_time_ms"}
        c2 = {k: v for k, v in r2.items() if k != "wall_time_ms"}
        assert c1 == c2, f"Trace record logical difference: {c1} != {c2}"

    print(f"[Determinism] Verified identical replay SHA256: {rep1_sha}")
    print(f"[Determinism] Verified {len(rep_lines)} replay lines and {len(trace1_records)} trace records.")

    return {
        "replay_sha256": rep1_sha,
        "replay_lines": len(rep_lines),
        "trace_records": len(trace1_records),
        "winner": res1.match_result.winner,
        "is_verified": res1.is_verified,
    }


def run_negative_cases(tmp_path: pathlib.Path) -> None:
    demo_dir = tmp_path / "neg_demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    run_sensing_demo(output_dir=demo_dir, ticks=20, seed=0)

    replay_path = demo_dir / "replay.jsonl"
    trace_path = demo_dir / "trace.jsonl"
    result_path = demo_dir / "result.json"

    session = ReplaySession()
    session.load(replay_path)

    # 1. Missing Trace
    pres, reason = load_sensing_presentation(session, replay_path, None, result=result_path)
    assert pres is None, "Missing trace must yield None presentation"
    assert "Trace unavailable" in reason, f"Unexpected reason: {reason}"
    print("[Negative Case 1] Missing trace: safe fallback to omniscient verified.")

    # 2. Corrupt Trace
    corrupt_trace = tmp_path / "corrupt_trace.jsonl"
    corrupt_trace.write_text("not json\n", encoding="utf-8")
    pres, reason = load_sensing_presentation(session, replay_path, corrupt_trace, result=result_path)
    assert pres is None, "Corrupt trace must yield None presentation"
    assert "Exchange evidence invalid" in reason, f"Unexpected reason: {reason}"
    print("[Negative Case 2] Corrupt trace: safe fallback to omniscient verified.")

    # 3. Invalid Demonstration Sidecar
    bad_demo = tmp_path / "bad_demo.json"
    bad_demo.write_text(json.dumps({"invalid": True}), encoding="utf-8")
    pres, reason = load_sensing_presentation(
        session, replay_path, trace_path, demo=bad_demo, result=result_path
    )
    assert pres is not None, "Valid trace + bad demo sidecar still presents factual view"
    assert not pres.sidecar_verified, "Invalid sidecar must have sidecar_verified=False"
    assert "Optional demonstration invalid" in pres.notice
    print("[Negative Case 3] Invalid sidecar: factual replay preserved without false teaching claim.")

    # 4. Capability Mismatch
    try:
        validate_agent("v6_window_scout", ruleset_id=BYTEFRAY_RULESET_V4_ID)
        raise AssertionError("Expected AgentValidationFailedError on ruleset v4")
    except AgentValidationFailedError as exc:
        assert exc.diagnostic.code == "agent_capability_unsupported"
        print("[Negative Case 4] Capability mismatch: SENSE correctly rejected on ruleset v4.")

    # 5. Compatible Capability Selection
    validation_res = validate_agent("v6_window_scout", ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID)
    assert validation_res.api_version == 2
    print("[Verification 5] Window Scout confirmed compatible under bytefray-rules-6-alpha1.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="bytefray_m1_6a_det_neg_") as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        run_determinism(tmp_path)
        run_negative_cases(tmp_path)
    print("[SUCCESS] All determinism and negative failure cases verified!")
