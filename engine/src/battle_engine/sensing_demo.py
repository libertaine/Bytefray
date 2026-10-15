"""Bytefray V6 M1-2: Window Scout Teaching Demonstration Entrypoint.

Orchestrates the authoritative teaching demonstration match using the native
match service and the public experimental Ruleset ``bytefray-rules-6-alpha1``.
Captures agent revisions, validates teaching exchange facts from the resulting
trace, and writes the version 1 ``demo.json`` sidecar record with
machine-checkable provenance.

Isolated from research infrastructure: does not touch E9 seed generation,
payoff calculations, or private authority material.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from battle_engine.agent_api import local_source_fingerprint
from battle_engine.agent_revisions import (
    agent_revision_fingerprint,
    agent_revision_id,
    local_python_subset_fingerprint,
    walk_agent_files,
)
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchResult,
    NativeMatchService,
)
from battle_engine.paths import get_data_root, get_resource_root
from battle_engine.project_info import get_project_info
from battle_engine.result_model import utc_completed_at, write_json_atomic
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID

DEMO_SCHEMA = "bytefray.sensing_demo"
DEMO_SCHEMA_VERSION = 1
DEMO_PROVENANCE = "product_teaching_demo"

DEFAULT_ARENA_SIZE = 512
DEFAULT_ACTION_BUDGET = 8
DEFAULT_TICKS = 1000
DEFAULT_SEED = 0

WINDOW_SCOUT_STARTER_NAME = "v6_window_scout"
STATIONARY_OPPONENT_FIXTURE_NAME = "v6_stationary_opponent"

WINDOW_SCOUT_START = 0
STATIONARY_OPPONENT_START = 91

WINDOW_SCOUT_DEFAULT_PARAMS: dict[str, Any] = {
    "search_interval": 4,
    "move_step": 64,
}


@dataclass(frozen=True)
class TeachingStep:
    """One verified step in the pedagogical sensing exchange."""

    step_index: int
    tick: int
    actor_id: str
    action_kind: str | None
    description: str
    detail: dict[str, Any]


@dataclass(frozen=True)
class SensingDemoResult:
    """Artifacts and verification outcome produced by running the teaching demo."""

    demo_path: Path
    result_path: Path
    replay_path: Path
    trace_path: Path
    match_result: NativeMatchResult
    teaching_steps: tuple[TeachingStep, ...]
    is_verified: bool


def resolve_teaching_agent_dir(agent_name: str, *, resource_root: Path | None = None) -> Path:
    """Locate a teaching agent or fixture directory under bundled resources."""
    root = (resource_root or get_resource_root()).expanduser().resolve()
    candidates = (
        root / "battle_engine" / "data" / "starter_agents" / agent_name,
        root / "engine" / "src" / "battle_engine" / "data" / "starter_agents" / agent_name,
        root / "battle_engine" / "data" / "teaching_fixtures" / agent_name,
        root / "engine" / "src" / "battle_engine" / "data" / "teaching_fixtures" / agent_name,
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    checked = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(f"Teaching agent directory '{agent_name}' not found. Checked: {checked}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_and_extract_exchange(trace_path: Path) -> tuple[bool, list[TeachingStep]]:
    """Inspect trace lines to verify the approved incomplete-info -> SENSE -> receipt -> MOVE sequence."""
    steps: list[TeachingStep] = []
    has_sense_91 = False
    has_receipt_91 = False
    has_move_64 = False
    has_write_91 = False

    scout_first_obs_senses = False
    scout_callbacks = 0

    if not trace_path.is_file():
        return False, steps

    for line in trace_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        record_type = record.get("record_type")

        if record_type in ("decision", "decision_v2"):
            agent_id = record.get("agent_id")
            if agent_id == "A":
                scout_callbacks += 1
                obs = record.get("observation", {})
                tick = obs.get("current_tick", record.get("tick", 0))
                action = record.get("action", {})
                applied = record.get("applied_result", {})

                # Callback 1: incomplete knowledge, requests SENSE(91)
                if scout_callbacks == 1:
                    prev_sense = obs.get("previous_sense_anchors")
                    if (
                        prev_sense is None
                        and "previous_sense_anchors" not in obs
                        and obs.get("visible_enemy_anchor_addresses", []) == []
                    ):
                        scout_first_obs_senses = True
                    if (
                        action.get("kind") == "sense"
                        and action.get("operand") == 91
                        and applied.get("status") == "APPLIED"
                        and applied.get("sensed_anchors") == [91]
                    ):
                        has_sense_91 = True
                        steps.append(
                            TeachingStep(
                                step_index=1,
                                tick=tick,
                                actor_id="A",
                                action_kind="sense",
                                description="Window Scout requests SENSE(91) in reach; 1 action consumed; result pending.",
                                detail={
                                    "target": 91,
                                    "cost": 1,
                                    "sensed_anchors_sample": applied.get("sensed_anchors"),
                                },
                            )
                        )

                # Callback 2: delayed receipt received, executes MOVE(+64)
                elif scout_callbacks == 2:
                    prev_sense = obs.get("previous_sense_anchors")
                    if prev_sense == [91] and obs.get("previous_action_applied") is True:
                        has_receipt_91 = True
                        steps.append(
                            TeachingStep(
                                step_index=2,
                                tick=tick,
                                actor_id="A",
                                action_kind=None,
                                description="Window Scout receives delivered anonymous sample (91,) from tick 1 action 1.",
                                detail={"received_anchors": prev_sense},
                            )
                        )
                    if (
                        action.get("kind") == "move"
                        and action.get("operand") == 64
                        and applied.get("status") == "APPLIED"
                    ):
                        has_move_64 = True
                        steps.append(
                            TeachingStep(
                                step_index=3,
                                tick=tick,
                                actor_id="A",
                                action_kind="move",
                                description="Window Scout executes legal MOVE(+64) toward delivered contact 91.",
                                detail={
                                    "operand": 64,
                                    "cost": 1,
                                    "new_anchor": obs.get("self_anchor", 0) + 64,
                                },
                            )
                        )

                # Callback 3: in-reach WRITE (and previous receipt is single-shot, hence absent)
                elif scout_callbacks == 3 and not has_write_91:
                    cb3_receipt_absent = "previous_sense_anchors" not in obs
                    if (
                        cb3_receipt_absent
                        and action.get("kind") == "write"
                        and action.get("operand") == 91
                        and applied.get("status") == "APPLIED"
                    ):
                        has_write_91 = True
                        steps.append(
                            TeachingStep(
                                step_index=4,
                                tick=tick,
                                actor_id="A",
                                action_kind="write",
                                description="Window Scout executes legal in-reach WRITE(91) to sampled address.",
                                detail={
                                    "operand": 91,
                                    "value": action.get("value"),
                                    "cost": 1,
                                },
                            )
                        )

    verified = (
        scout_first_obs_senses
        and has_sense_91
        and has_receipt_91
        and has_move_64
        and has_write_91
    )
    return verified, steps


DEMO_ARTIFACT_NAMES: frozenset[str] = frozenset(
    {"demo.json", "replay.jsonl", "trace.jsonl", "result.json"}
)


def validate_output_directory(
    output_dir: Path | str,
    *,
    resource_root: Path | None = None,
) -> Path:
    """Validate that the demonstration output directory is an authorized product path.

    Enforces the research-isolation boundary and output confinement
    (Phase 0 Condition C-2, AC11):
    1. Output directory must not be empty or whitespace.
    2. Strictly rejects research directories and private research namespaces
       (e.g. tools/research, docs/research, any path component matching 'research',
       'research_*', '.pytest_e9_*', 'e9_*').
    3. Resolves all symlinks/junctions to canonical target before validation.
    4. Must resolve to an authorized product path:
       - a subdirectory under the repository product runs tree (runs/<subdir>)
       - a subdirectory under configured data_root/runs/ (when distinct)
       - a legitimate test temporary directory (.pytest-tmp/<subdir> or tempfile.gettempdir()/<subdir>)
    5. Prohibits writing directly to the bare root of 'runs', project repository root,
       or bare temporary roots (.pytest-tmp or system tempdir).
    6. Prohibits writing into repository source/doc/tool trees (engine/, client/,
       app/, _legacy/, tools/, docs/, assets/, .git/).
    7. Prohibits writing into protected product run roots (agents_test, evaluations,
       _designer, _loose) or historical run directories (v0_*, v2_*, v3_*, v4_*, v5_*).
    8. Prohibits writing into existing directories or subdirectories of existing
       directories that contain non-demonstration artifacts (protects existing research
       and product data from overwrite).
    """
    raw_str = str(output_dir).strip()
    if not raw_str:
        raise ValueError("Unauthorized output path: output directory cannot be empty.")

    resolved = Path(output_dir).expanduser().resolve()
    parts = resolved.parts

    # 1. Reject research directories and private research namespaces
    for i in range(len(parts) - 1):
        p1 = parts[i].lower()
        p2 = parts[i + 1].lower()
        if (p1 == "tools" and p2 == "research") or (p1 == "docs" and p2 == "research"):
            raise ValueError(
                f"Unauthorized output path: writing into research directory is prohibited: {resolved}"
            )

    for part in parts:
        p_lower = part.lower()
        if p_lower == "research" or p_lower.startswith(("research_", ".pytest_e9_", "e9_")):
            raise ValueError(
                f"Unauthorized output path: writing into research namespace or directory is prohibited: {resolved}"
            )

    # 2. Determine authorized product output roots
    checkout_root = (resource_root or get_resource_root()).expanduser().resolve()
    data_root = get_data_root().expanduser().resolve()
    checkout_runs = checkout_root / "runs"
    data_runs = data_root / "runs"
    pytest_temp = checkout_root / ".pytest-tmp"
    system_temp = Path(tempfile.gettempdir()).expanduser().resolve()

    # Reject bare root directories
    if resolved in (checkout_root, data_root):
        raise ValueError(
            f"Unauthorized output path: writing directly to project root is prohibited: {resolved}"
        )
    if resolved in (checkout_runs, data_runs):
        raise ValueError(
            f"Unauthorized output path: writing directly to root runs directory is prohibited; specify a subdirectory: {resolved}"
        )
    if resolved in (pytest_temp, system_temp):
        raise ValueError(
            f"Unauthorized output path: writing directly to root temporary directory is prohibited; specify a subdirectory: {resolved}"
        )

    # Check containment within authorized product roots
    is_under_runs = (
        (resolved.is_relative_to(checkout_runs) and resolved != checkout_runs)
        or (resolved.is_relative_to(data_runs) and resolved != data_runs)
    )
    is_under_pytest_temp = (
        resolved.is_relative_to(pytest_temp) and resolved != pytest_temp
    )
    is_under_system_temp = (
        resolved.is_relative_to(system_temp) and resolved != system_temp
    )

    if not (is_under_runs or is_under_pytest_temp or is_under_system_temp):
        if resolved.is_relative_to(checkout_root):
            raise ValueError(
                f"Unauthorized output path: writing into repository tree outside runs/ is prohibited: {resolved}"
            )
        raise ValueError(
            f"Unauthorized output path: path is outside authorized product output directories: {resolved}"
        )

    # 3. Protect existing historical runs, foreign subsystems, and artifacts from overwrite / pollution
    if is_under_runs:
        runs_parent = checkout_runs if resolved.is_relative_to(checkout_runs) else data_runs
        rel_parts = resolved.relative_to(runs_parent).parts
        top_name = rel_parts[0].lower()

        # Prohibit other product subsystem directories under runs/
        if top_name in {"agents_test", "evaluations", "_designer", "_loose"}:
            raise ValueError(
                f"Unauthorized output path: writing into protected run root '{rel_parts[0]}' is prohibited: {resolved}"
            )

        # Prohibit historical run directories under runs/
        if top_name.startswith(("v0_", "v2_", "v3_", "v4_", "v5_")):
            raise ValueError(
                f"Unauthorized output path: writing into historical run directory '{rel_parts[0]}' is prohibited: {resolved}"
            )

        # Check existing ancestor directories under runs/
        curr = resolved.parent
        while curr != runs_parent and curr != curr.parent:
            if curr.exists():
                if curr.is_file():
                    raise ValueError(
                        f"Unauthorized output path: ancestor path exists and is a file: {curr}"
                    )
                non_demo_ancestors = [
                    child.name
                    for child in curr.iterdir()
                    if child.name not in DEMO_ARTIFACT_NAMES
                ]
                if non_demo_ancestors:
                    raise ValueError(
                        f"Unauthorized output path: target ancestor directory contains non-demonstration files or subdirectories: {curr}"
                    )
            curr = curr.parent

    # 4. Protect existing files and directories from overwrite
    if resolved.exists():
        if resolved.is_file():
            raise ValueError(
                f"Unauthorized output path: target path exists and is a file: {resolved}"
            )
        non_demo_entries = [
            child.name
            for child in resolved.iterdir()
            if child.name not in DEMO_ARTIFACT_NAMES
        ]
        if non_demo_entries:
            raise ValueError(
                f"Unauthorized output path: target directory contains non-demonstration files or subdirectories: {resolved}"
            )

    return resolved


def validate_sensing_demo_artifacts(demo_dir_or_file: Path | str) -> bool:
    """Validate machine-checkable provenance identifiers and artifact SHA-256 digests.

    Confirms:
    1. demo.json schema is bytefray.sensing_demo v1.
    2. provenance identifier is 'product_teaching_demo'.
    3. declared_product_fixture is True.
    4. ruleset_id matches bytefray-rules-6-alpha1.
    5. replay and trace artifact files exist and their SHA-256 digests match.
    6. result artifact file (if declared) exists and its SHA-256 digest matches.

    Note:
        SHA-256 digests detect unintentional disk corruption, drift, and inconsistency.
        Because demo.json is a mutable local file, sidecars are not cryptographically
        tamper-proof against deliberate malicious modification (see V6 Alpha M1 Contract
        §Knowledge Projection & Artifacts).
    """
    target = Path(demo_dir_or_file).expanduser().resolve()
    demo_path = target / "demo.json" if target.is_dir() else target
    if not demo_path.is_file():
        return False

    try:
        payload = json.loads(demo_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    if not isinstance(payload, dict):
        return False

    if payload.get("schema") != DEMO_SCHEMA:
        return False
    if payload.get("schema_version") != DEMO_SCHEMA_VERSION:
        return False
    if payload.get("provenance") != DEMO_PROVENANCE:
        return False
    if payload.get("declared_product_fixture") is not True:
        return False
    if payload.get("ruleset_id") != BYTEFRAY_RULESET_V6_ALPHA1_ID:
        return False

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return False

    base_dir = demo_path.parent
    for key in ("replay", "trace"):
        entry = artifacts.get(key)
        if not isinstance(entry, dict):
            return False
        filename = entry.get("filename")
        expected_sha = entry.get("sha256")
        if not filename or not expected_sha:
            return False
        if not isinstance(filename, str) or not isinstance(expected_sha, str):
            return False
        if Path(filename).name != filename:
            return False
        file_path = base_dir / filename
        if not file_path.is_file():
            return False
        try:
            if _sha256_file(file_path) != expected_sha:
                return False
        except OSError:
            return False

    if "result" in artifacts:
        entry = artifacts["result"]
        if not isinstance(entry, dict):
            return False
        filename = entry.get("filename")
        expected_sha = entry.get("sha256")
        if not filename or not expected_sha:
            return False
        if not isinstance(filename, str) or not isinstance(expected_sha, str):
            return False
        if Path(filename).name != filename:
            return False
        file_path = base_dir / filename
        if not file_path.is_file():
            return False
        try:
            if _sha256_file(file_path) != expected_sha:
                return False
        except OSError:
            return False

    return True


def run_sensing_demo(
    output_dir: Path | str,
    *,
    ticks: int = DEFAULT_TICKS,
    seed: int = DEFAULT_SEED,
    parameters: dict[str, Any] | None = None,
    resource_root: Path | None = None,
) -> SensingDemoResult:
    """Execute the bounded M1-2 teaching demonstration and persist verified artifacts."""
    out_dir = validate_output_directory(output_dir, resource_root=resource_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve source directories
    scout_src_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME, resource_root=resource_root)
    opponent_src_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME, resource_root=resource_root)

    # Capture agent revisions into snapshot
    with tempfile.TemporaryDirectory(prefix="bytefray_demo_revisions_") as temp_snap:
        snap_root = Path(temp_snap)
        scout_snap = snap_root / "v6_window_scout"
        opponent_snap = snap_root / "v6_stationary_opponent"
        shutil.copytree(scout_src_dir, scout_snap)
        shutil.copytree(opponent_src_dir, opponent_snap)

        scout_walk = walk_agent_files(scout_snap)
        opponent_walk = walk_agent_files(opponent_snap)

        scout_tree_digest = agent_revision_fingerprint(scout_snap) or ""
        opponent_tree_digest = agent_revision_fingerprint(opponent_snap) or ""

        scout_rev_id = agent_revision_id(scout_tree_digest)
        opponent_rev_id = agent_revision_id(opponent_tree_digest)

        scout_py_subset = local_python_subset_fingerprint(scout_walk)
        opponent_py_subset = local_python_subset_fingerprint(opponent_walk)

        scout_capture_complete = scout_walk.complete
        opponent_capture_complete = opponent_walk.complete

        # Specs from snapshot
        scout_spec = agent_spec_from_dir(scout_snap)
        opponent_spec = agent_spec_from_dir(opponent_snap)
        if scout_spec is None or opponent_spec is None:
            raise RuntimeError("Could not resolve AgentSpec from teaching snapshot.")

        # Compare loaded fingerprint with captured Python-subset fingerprint
        scout_initial_fp = local_source_fingerprint(scout_snap)
        opponent_initial_fp = local_source_fingerprint(opponent_snap)

        scout_fp_agrees = (scout_initial_fp == scout_py_subset)
        opponent_fp_agrees = (opponent_initial_fp == opponent_py_subset)

        resolved_scout_params = dict(WINDOW_SCOUT_DEFAULT_PARAMS)
        if parameters:
            resolved_scout_params.update(parameters)

        replay_path = out_dir / "replay.jsonl"
        trace_path = out_dir / "trace.jsonl"
        result_path = out_dir / "result.json"
        demo_path = out_dir / "demo.json"

        # Construct MatchRequest reusing NativeMatchService
        match_config = Config(
            arena_size=DEFAULT_ARENA_SIZE,
            instr_per_tick=DEFAULT_ACTION_BUDGET,
            seed=seed,
        )

        request = MatchRequest(
            config=match_config,
            entrants=(
                MatchEntrant.python(
                    agent_id="A",
                    name="v6_window_scout",
                    start=WINDOW_SCOUT_START,
                    spec=scout_spec,
                    parameters=resolved_scout_params,
                ),
                MatchEntrant.python(
                    agent_id="B",
                    name="v6_stationary_opponent",
                    start=STATIONARY_OPPONENT_START,
                    spec=opponent_spec,
                    parameters={},
                ),
            ),
            max_ticks=ticks,
            replay_path=replay_path,
            trace_path=trace_path,
            ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
            verbose=False,
        )

        service = NativeMatchService()
        match_result = service.run(request)

        # Verify exchange in the trace
        exchange_verified, steps = _verify_and_extract_exchange(trace_path)

        # Verify loaded initial and final source fingerprints from match execution
        scout_agent_res = next((a for a in match_result.agents if a.agent_id == "A"), None)
        opponent_agent_res = next((a for a in match_result.agents if a.agent_id == "B"), None)

        scout_loaded_init = (
            scout_agent_res.metadata.get("local_source_fingerprint")
            if scout_agent_res else None
        )
        scout_loaded_final = (
            scout_agent_res.metadata.get("local_source_fingerprint_final")
            if scout_agent_res else None
        )

        opponent_loaded_init = (
            opponent_agent_res.metadata.get("local_source_fingerprint")
            if opponent_agent_res else None
        )
        opponent_loaded_final = (
            opponent_agent_res.metadata.get("local_source_fingerprint_final")
            if opponent_agent_res else None
        )

        scout_drift_detected = (
            scout_loaded_init is None
            or scout_loaded_final is None
            or scout_loaded_init != scout_loaded_final
            or scout_loaded_init != scout_py_subset
        )
        opponent_drift_detected = (
            opponent_loaded_init is None
            or opponent_loaded_final is None
            or opponent_loaded_init != opponent_loaded_final
            or opponent_loaded_init != opponent_py_subset
        )

        overall_verified = (
            exchange_verified
            and scout_capture_complete
            and opponent_capture_complete
            and scout_fp_agrees
            and opponent_fp_agrees
            and not scout_drift_detected
            and not opponent_drift_detected
        )

        proj_info = get_project_info()

        # Build sidecar demo.json payload
        demo_payload: dict[str, Any] = {
            "schema": DEMO_SCHEMA,
            "schema_version": DEMO_SCHEMA_VERSION,
            "provenance": DEMO_PROVENANCE,
            "declared_product_fixture": True,
            "ruleset_id": BYTEFRAY_RULESET_V6_ALPHA1_ID,
            "match_id": match_result.match_id,
            "result_id": match_result.result_id,
            "config": {
                "arena_size": match_config.arena_size,
                "action_budget": match_config.instr_per_tick,
                "max_ticks": ticks,
                "seed": seed,
            },
            "entrants": [
                {
                    "agent_id": "A",
                    "name": "v6_window_scout",
                    "start": WINDOW_SCOUT_START,
                    "parameters": resolved_scout_params,
                    "revision_id": scout_rev_id,
                    "full_tree_digest": scout_tree_digest,
                    "python_subset_fingerprint": scout_py_subset,
                    "loaded_initial_fingerprint": scout_loaded_init,
                    "loaded_final_fingerprint": scout_loaded_final,
                    "drift_detected": scout_drift_detected,
                    "capture_complete": scout_capture_complete,
                },
                {
                    "agent_id": "B",
                    "name": "v6_stationary_opponent",
                    "start": STATIONARY_OPPONENT_START,
                    "parameters": {},
                    "revision_id": opponent_rev_id,
                    "full_tree_digest": opponent_tree_digest,
                    "python_subset_fingerprint": opponent_py_subset,
                    "loaded_initial_fingerprint": opponent_loaded_init,
                    "loaded_final_fingerprint": opponent_loaded_final,
                    "drift_detected": opponent_drift_detected,
                    "capture_complete": opponent_capture_complete,
                },
            ],
            "engine": {
                "project_name": proj_info.project_name,
                "version": proj_info.version,
                "python_version": proj_info.python_version,
                "agent_api_version": proj_info.agent_api_version,
                "result_schema_version": proj_info.result_schema_version,
                "replay_schema_version": proj_info.replay_schema_version,
            },
            "artifacts": {
                "replay": {
                    "filename": replay_path.name,
                    "sha256": _sha256_file(replay_path),
                },
                "trace": {
                    "filename": trace_path.name,
                    "sha256": _sha256_file(trace_path),
                },
            },
            "teaching_exchange": {
                "sequence_verified": exchange_verified,
                "steps": [
                    {
                        "step_index": s.step_index,
                        "tick": s.tick,
                        "actor_id": s.actor_id,
                        "action_kind": s.action_kind,
                        "description": s.description,
                        "detail": s.detail,
                    }
                    for s in steps
                ],
            },
            "status": "reproducible" if overall_verified else "unverified",
            "completed_at": utc_completed_at(),
        }

        if result_path.is_file():
            demo_payload["artifacts"]["result"] = {
                "filename": result_path.name,
                "sha256": _sha256_file(result_path),
            }

        write_json_atomic(demo_path, demo_payload)

        # Machine-checkable artifact verification
        artifacts_valid = validate_sensing_demo_artifacts(demo_path)
        if not artifacts_valid and overall_verified:
            overall_verified = False
            demo_payload["status"] = "unverified"
            write_json_atomic(demo_path, demo_payload)

        return SensingDemoResult(
            demo_path=demo_path,
            result_path=result_path,
            replay_path=replay_path,
            trace_path=trace_path,
            match_result=match_result,
            teaching_steps=tuple(steps),
            is_verified=overall_verified,
        )


def run_keeper_demo(
    output_dir: Path | str, *, keeper_seat: str = "A"
) -> SensingDemoResult:
    """Run the exact 100-tick K1 fixture; v1 status stays unverified.

    Completion is evaluated separately with ``verify_keeper_scenario``. This
    entry deliberately accepts no arbitrary sources, parameters or input seeds.
    """
    if keeper_seat not in {"A", "B"}:
        raise ValueError("keeper_seat must be A or B")
    out = Path(output_dir).expanduser().resolve()
    allowed = get_resource_root().resolve() / "runs" / "v6_alpha_m2"
    if not out.is_relative_to(allowed) or out == allowed:
        raise ValueError("Keeper output must be a fresh subdirectory of runs/v6_alpha_m2")
    # Resolve containment and reject link traversal, including a redirected
    # runs root. A fresh exclusive leaf prevents overwriting retained bodies.
    raw = Path(output_dir).expanduser().absolute()
    if raw != out or any(p.is_symlink() or getattr(p, "is_junction", lambda: False)() for p in raw.parents):
        raise ValueError("Keeper output may not traverse links or junctions")
    if any(p.lower() == "research" or p.lower().startswith(("e9_", "research_")) for p in out.parts):
        raise ValueError("Keeper output may not use research namespaces")
    out.mkdir(parents=True, exist_ok=False)
    names = ("v6_watchful_keeper", "v6_encroaching_opponent")
    ordered = names if keeper_seat == "A" else names[::-1]
    captures = []
    entrants = []
    for seat, name in zip(("A", "B"), ordered):
        source = resolve_teaching_agent_dir(name)
        snapshot = out / "sources" / seat
        walk = walk_agent_files(source)
        if not walk.complete:
            raise ValueError(f"Incomplete bundled source capture: {name}")
        snapshot.mkdir(parents=True)
        for entry in walk.entries:
            target = snapshot / entry.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry.content)
        digest = agent_revision_fingerprint(snapshot)
        if digest != agent_revision_fingerprint(source) or not digest:
            raise ValueError(f"Source changed during capture: {name}")
        subset = local_python_subset_fingerprint(walk)
        spec = agent_spec_from_dir(snapshot)
        if spec is None:
            raise ValueError(f"Invalid captured agent: {name}")
        keeper = seat == keeper_seat
        params = {"scan_interval": 4, "perimeter_offset": 27} if keeper else {}
        start = 0 if keeper else 91
        entrants.append(MatchEntrant.python(seat, name, start, spec, parameters=params))
        captures.append({
            "agent_id": seat, "name": name, "start": start, "parameters": params,
            "revision_id": agent_revision_id(digest), "full_tree_digest": digest,
            "python_subset_fingerprint": subset, "capture_complete": True,
        })
    replay, trace, result, demo = (out / n for n in ("replay.jsonl", "trace.jsonl", "result.json", "demo.json"))
    config = Config(arena_size=512, instr_per_tick=8, seed=0)
    match = NativeMatchService().run(MatchRequest(
        config=config, entrants=tuple(entrants), max_ticks=100,
        replay_path=replay, trace_path=trace, ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    ))
    for capture in captures:
        agent = next(a for a in match.agents if a.agent_id == capture["agent_id"])
        initial = agent.metadata.get("local_source_fingerprint")
        final = agent.metadata.get("local_source_fingerprint_final")
        capture.update({
            "loaded_initial_fingerprint": initial, "loaded_final_fingerprint": final,
            "drift_detected": not (initial == final == capture["python_subset_fingerprint"]),
        })
    info = get_project_info()
    write_json_atomic(demo, {
        "schema": DEMO_SCHEMA, "schema_version": 1, "provenance": DEMO_PROVENANCE,
        "declared_product_fixture": True, "ruleset_id": BYTEFRAY_RULESET_V6_ALPHA1_ID,
        "match_id": match.match_id, "result_id": match.result_id,
        "config": {"arena_size": 512, "action_budget": 8, "max_ticks": 100, "seed": 0},
        "entrants": captures,
        "engine": {
            "project_name": info.project_name, "version": info.version,
            "python_version": info.python_version, "agent_api_version": info.agent_api_version,
            "result_schema_version": info.result_schema_version, "replay_schema_version": info.replay_schema_version,
        },
        "artifacts": {key: {"filename": path.name, "sha256": _sha256_file(path)}
                      for key, path in (("replay", replay), ("trace", trace), ("result", result))},
        "status": "unverified", "completed_at": utc_completed_at(),
    })
    return SensingDemoResult(demo, result, replay, trace, match, (), False)


def run_reacquirer_demo(
    output_dir: Path | str, *, reacquirer_seat: str = "A"
) -> SensingDemoResult:
    """Run the exact 100-tick R1 fixture; v1 status stays unverified.

    Completion is evaluated separately with ``verify_reacquirer_scenario``. This
    entry deliberately accepts no arbitrary sources, parameters or input seeds.
    """
    if reacquirer_seat not in {"A", "B"}:
        raise ValueError("reacquirer_seat must be A or B")
    out = Path(output_dir).expanduser().resolve()
    allowed = get_resource_root().resolve() / "runs" / "v6_alpha_m2"
    if not out.is_relative_to(allowed) or out == allowed:
        raise ValueError("Reacquirer output must be a fresh subdirectory of runs/v6_alpha_m2")
    raw = Path(output_dir).expanduser().absolute()
    if raw != out or any(p.is_symlink() or getattr(p, "is_junction", lambda: False)() for p in raw.parents):
        raise ValueError("Reacquirer output may not traverse links or junctions")
    if any(p.lower() == "research" or p.lower().startswith(("e9_", "research_")) for p in out.parts):
        raise ValueError("Reacquirer output may not use research namespaces")
    out.mkdir(parents=True, exist_ok=False)
    names = ("v6_roaming_reacquirer", "v6_relocating_opponent")
    ordered = names if reacquirer_seat == "A" else names[::-1]
    captures = []
    entrants = []
    for seat, name in zip(("A", "B"), ordered):
        source = resolve_teaching_agent_dir(name)
        snapshot = out / "sources" / seat
        walk = walk_agent_files(source)
        if not walk.complete:
            raise ValueError(f"Incomplete bundled source capture: {name}")
        snapshot.mkdir(parents=True)
        for entry in walk.entries:
            target = snapshot / entry.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry.content)
        digest = agent_revision_fingerprint(snapshot)
        if digest != agent_revision_fingerprint(source) or not digest:
            raise ValueError(f"Source changed during capture: {name}")
        subset = local_python_subset_fingerprint(walk)
        spec = agent_spec_from_dir(snapshot)
        if spec is None:
            raise ValueError(f"Invalid captured agent: {name}")
        reacquirer = seat == reacquirer_seat
        params = {"search_offset": 91, "move_step": 64, "rescan_wait": 3} if reacquirer else {}
        start = 0 if reacquirer else 91
        entrants.append(MatchEntrant.python(seat, name, start, spec, parameters=params))
        captures.append({
            "agent_id": seat, "name": name, "start": start, "parameters": params,
            "revision_id": agent_revision_id(digest), "full_tree_digest": digest,
            "python_subset_fingerprint": subset, "capture_complete": True,
        })
    replay, trace, result, demo = (out / n for n in ("replay.jsonl", "trace.jsonl", "result.json", "demo.json"))
    config = Config(arena_size=512, instr_per_tick=8, seed=0)
    match = NativeMatchService().run(MatchRequest(
        config=config, entrants=tuple(entrants), max_ticks=100,
        replay_path=replay, trace_path=trace, ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    ))
    for capture in captures:
        agent = next(a for a in match.agents if a.agent_id == capture["agent_id"])
        initial = agent.metadata.get("local_source_fingerprint")
        final = agent.metadata.get("local_source_fingerprint_final")
        capture.update({
            "loaded_initial_fingerprint": initial, "loaded_final_fingerprint": final,
            "drift_detected": not (initial == final == capture["python_subset_fingerprint"]),
        })
    info = get_project_info()
    write_json_atomic(demo, {
        "schema": DEMO_SCHEMA, "schema_version": 1, "provenance": DEMO_PROVENANCE,
        "declared_product_fixture": True, "ruleset_id": BYTEFRAY_RULESET_V6_ALPHA1_ID,
        "match_id": match.match_id, "result_id": match.result_id,
        "config": {"arena_size": 512, "action_budget": 8, "max_ticks": 100, "seed": 0},
        "entrants": captures,
        "engine": {
            "project_name": info.project_name, "version": info.version,
            "python_version": info.python_version, "agent_api_version": info.agent_api_version,
            "result_schema_version": info.result_schema_version, "replay_schema_version": info.replay_schema_version,
        },
        "artifacts": {key: {"filename": path.name, "sha256": _sha256_file(path)}
                      for key, path in (("replay", replay), ("trace", trace), ("result", result))},
        "status": "unverified", "completed_at": utc_completed_at(),
    })
    return SensingDemoResult(demo, result, replay, trace, match, (), False)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for running the bounded teaching demonstration."""
    parser = argparse.ArgumentParser(
        prog="bytefray-sensing-demo",
        description="Run Bytefray V6 Window Scout sensing teaching demonstration.",
    )
    parser.add_argument(
        "--scenario", choices=("scout", "keeper-K1", "reacquirer-R1"), default="scout",
        help="Explicit trusted product scenario (default: unchanged Scout).",
    )
    parser.add_argument("--keeper-seat", choices=("A", "B"), default="A")
    parser.add_argument("--reacquirer-seat", choices=("A", "B"), default="A")
    parser.add_argument(
        "--output-dir",
        default="runs/sensing_demo",
        help="Directory where demo artifacts (demo.json, replay, trace, result) are written.",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=DEFAULT_TICKS,
        help="Tick limit for the match run (default 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Deterministic match seed (default 0).",
    )
    args = parser.parse_args(argv)

    try:
        if args.scenario == "keeper-K1":
            from battle_engine.sensing_playback import verify_keeper_scenario

            if args.ticks != DEFAULT_TICKS or args.seed != DEFAULT_SEED:
                raise ValueError("Keeper uses fixed 100-tick, seed-0 inputs; omit --ticks/--seed")
            result = run_keeper_demo(args.output_dir, keeper_seat=args.keeper_seat)
            verification = verify_keeper_scenario(result.demo_path, keeper_seat=args.keeper_seat)
            print(f"Keeper artifacts: {result.demo_path}")
            print(f"keeper-K1 completion: {verification.is_complete}; {verification.findings}")
            print("demo v1 status: unverified (Scout teaching semantics retained)")
            return 0 if verification.is_complete else 1
        if args.scenario == "reacquirer-R1":
            from battle_engine.sensing_playback import verify_reacquirer_scenario

            if args.ticks != DEFAULT_TICKS or args.seed != DEFAULT_SEED:
                raise ValueError("Reacquirer uses fixed 100-tick, seed-0 inputs; omit --ticks/--seed")
            result = run_reacquirer_demo(args.output_dir, reacquirer_seat=args.reacquirer_seat)
            reacquisition = verify_reacquirer_scenario(result.demo_path, reacquirer_seat=args.reacquirer_seat)
            print(f"Reacquirer artifacts: {result.demo_path}")
            print(f"reacquirer-R1 completion: {reacquisition.is_complete}; {reacquisition.findings}")
            print("demo v1 status: unverified (Scout teaching semantics retained)")
            return 0 if reacquisition.is_complete else 1
        result = run_sensing_demo(
            args.output_dir,
            ticks=args.ticks,
            seed=args.seed,
        )
        print(f"Teaching Demo: {result.demo_path}")
        print(f"Match ID:      {result.match_result.match_id}")
        print(f"Result ID:     {result.match_result.result_id}")
        print(f"Verified:      {result.is_verified}")
        for s in result.teaching_steps:
            print(f"  [Step {s.step_index}] Tick {s.tick} ({s.actor_id}): {s.description}")
        return 0 if result.is_verified else 1
    except Exception as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
