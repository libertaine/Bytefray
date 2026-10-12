"""Same-attempt canonical evidence validation and disposable offline diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from battle_engine.agent_trace import DecisionRecordV2, read_trace_v2
from battle_engine.replay import KillDeathEvent, RuntimeEvent
from battle_engine.result_model import read_result, stable_id, verify_replay_digest
from battle_engine.spectator_derivation import derive_events, verify_pair
from battle_engine.spectator_events import load_schema4_replay

from tools.research.v6.e8 import gates, rederive, traces

from .behavior import audit, context_for, variant_for
from .protocol import Cell, IntegrityError, canonical, digest, file_digest, read_json, write_once

ARTIFACTS = ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")
TERMINATIONS = frozenset({"last_agent_standing", "tick_limit", "all_agents_dead"})


def payoff(winner: str, seat: str) -> int:
    """Exact doubled payoff; a termination string never determines a tie."""
    if seat not in ("A", "B") or winner not in ("A", "B", "tie"):
        raise IntegrityError("invalid authoritative terminal winner")
    return 1 if winner == "tie" else 2 * int(winner == seat)


def diagnostic(path: Path, cell: Cell, protocol: dict[str, Any], *, seed: int,
               package_names: tuple[str, str], expected_match_id: str | None = None) -> dict[str, Any]:
    cell.validate(protocol)
    result_path, replay_path, trace_path = (path / name for name in ARTIFACTS[:3])
    raw_result = read_json(result_path)
    result = read_result(result_path)
    loaded = load_schema4_replay(replay_path)
    bound = verify_pair(replay_path, trace_path)
    derive_events(bound)  # independently checks replay/trace state and events
    trace = read_trace_v2(trace_path)
    raw_trace = list(traces.iter_trace(trace_path))
    kinds = [item.get("record_type") for item in raw_trace]
    if (not kinds or kinds[0] != "header" or kinds[-1] != "binding"
            or kinds.count("header") != 1 or kinds.count("binding") != 1
            or any(kind not in {"header", "reset", "declaration", "decision_v2", "binding"}
                   for kind in kinds)):
        raise IntegrityError("trace is incomplete or contains misplaced/unknown records")
    expected_rules = protocol["effective_t8"]["policy"]["ruleset_id"]
    if (raw_result.get("status") != "completed" or result.ruleset_id != expected_rules
            or loaded.header.ruleset_id != expected_rules or bound.ruleset_id != expected_rules
            or trace.header.match_seed != seed or loaded.header.config.seed != seed
            or dict(trace.header.agents) != dict(zip(("A", "B"), package_names))
            or tuple(e["agent_id"] for e in result.entrants) != ("A", "B")
            or tuple(e["name"] for e in result.entrants) != package_names
            or trace.header.agent_call_timeout is not None or trace.header.supervised
            or (expected_match_id is not None and result.match_id != expected_match_id)):
        raise IntegrityError("cell artifact identities/effective environment disagree")
    config = asdict(loaded.header.config)
    config.pop("seed")
    if config != protocol["effective_t8"]["config_without_seed"]:
        raise IntegrityError("effective T8 config drift")
    reproduction = {"seed": seed, "arena_size": 512, "tick_limit": 1000, "action_budget": 8,
                    "win_mode": config["win_mode"], "weights": config["weights"], "entrant_order": ["A", "B"]}
    if (dict(result.reproducibility) != reproduction
            or dict(loaded.header.reproducibility) != reproduction):
        raise IntegrityError("effective limits/defaults/reproducibility drift")
    verify_replay_digest(result, replay_path)
    terminal = loaded.result
    if (result.match_id != loaded.header.match_id or result.result_id != terminal.result_id
            or result.match_id != terminal.match_id or result.winner != terminal.winner
            or result.ticks != terminal.ticks or dict(result.score) != dict(terminal.score)
            or result.termination_reason != terminal.termination_reason
            or result.termination_reason not in TERMINATIONS
            or not 1 <= result.ticks <= 1000 or loaded.ticks[-1].tick != result.ticks
            or (result.termination_reason == "tick_limit" and result.ticks != 1000)):
        raise IntegrityError("result/replay terminal disagreement or unregistered termination")
    for entrant in result.entrants:
        metadata = entrant.get("metadata", {})
        if (entrant.get("termination_reason") not in (None, "normal_halt", "core_captured")
                or entrant.get("diagnostic") is not None
                or metadata.get("local_source_fingerprint") != metadata.get("local_source_fingerprint_final")):
            raise IntegrityError("non-retryable entrant termination")
    expected_result_id = stable_id("result", {"match_id": result.match_id, "winner": result.winner,
        "termination_reason": result.termination_reason, "ticks": result.ticks,
        "score": dict(result.score), "entrants": [dict(e) for e in result.entrants]})
    if (result.result_id != expected_result_id or loaded.header.result_id != result.result_id
            or result.replay is None or result.replay.replay_id != loaded.header.replay_id
            or result.replay.filename != "replay.jsonl"):
        raise IntegrityError("canonical result/replay identity does not recompute")
    if any(isinstance(event, RuntimeEvent) for tick in loaded.ticks for event in tick.events):
        raise IntegrityError("runtime/containment failure is outside payoff encoding")
    start, replay_log = traces.replay_facts(replay_path)
    extracted = traces.extract(raw_trace, arena=512, start=start, replay_log=replay_log)
    rows, summary = extracted.rows, extracted.summary
    failures, reflections, _ = gates.delivery(rows)
    if (gates.presence_sensed(rows) or gates.statuses(rows) or failures or reflections
            or any(windows != [27] for windows in summary["reset_windows"].values())
            or not rederive.rederive_cell(rows, summary, ticks_run=result.ticks,
                                         arena=512, slot_limit=None).passed):
        raise IntegrityError("independent callback/SENSE/feedback audit failed")
    focal = [r for r in trace.records if isinstance(r, DecisionRecordV2) and r.agent_id == cell.seat]
    behavior = (audit(focal, context_for(cell.seat, seed), variant_for(cell.row, protocol), cell_identity=cell.identity)
                if cell.row in {"A", "MEDIUM", "SPARSE", *protocol["groups"]["S"]} else None)
    pressure: dict[str, bool] = {}
    captures: dict[str, bool] = {}
    for victim in ("A", "B"):
        core = {(start.core_base[victim] + i) % 512 for i in range(8)}
        counts: Counter[int] = Counter()
        for row in rows:
            if (row[traces.COLUMN["kind"]] == "write" and row[traces.COLUMN["status"]] == "APPLIED"
                    and row[traces.COLUMN["entrant"]] != victim
                    and row[traces.COLUMN["address"]] in core):
                counts[row[traces.COLUMN["address"]]] += 1
        pressure[victim] = all(counts[address] >= 2 for address in core)
        captured = next(e for e in result.entrants if e["agent_id"] == victim).get("termination_reason") == "core_captured"
        captures[victim] = captured and any(isinstance(event, KillDeathEvent) and event.victim == victim
                                           for tick in loaded.ticks for event in tick.events)
    trajectory = [{"tick": tick.tick, "memory_diffs": [asdict(d) for d in tick.memory_diffs],
                   "processes": [asdict(p) for p in tick.processes],
                   "events": [asdict(e) for e in tick.events]} for tick in loaded.ticks]
    return {"schema": "bytefray.v6.e9.cell_diagnostic", "version": 1,
            "cell": asdict(cell), "cell_identity": cell.identity,
            "source_digests": {name: file_digest(path / name) for name in ARTIFACTS[:3]},
            "payoff_doubled": payoff(result.winner, cell.seat),
            "terminal": result.termination_reason, "ticks": result.ticks,
            "pressure": pressure, "captures": captures, "behavior": behavior,
            "trajectory_digest": digest(canonical({"ticks": trajectory, "callbacks": rows,
                "terminal": {"winner": result.winner, "reason": result.termination_reason,
                             "ticks": result.ticks, "score": dict(result.score)}}))}


def validate(path: Path, cell: Cell, protocol: dict[str, Any], *, seed: int,
             package_names: tuple[str, str], expected_match_id: str | None = None) -> dict[str, str]:
    rebuilt = diagnostic(path, cell, protocol, seed=seed, package_names=package_names,
                         expected_match_id=expected_match_id)
    target = path / "diagnostic.json"
    if target.exists():
        if canonical(read_json(target)) != canonical(rebuilt):
            raise IntegrityError("completed diagnostic is inconsistent; no reconstruction")
    else:
        # An interrupted derived publication can be reconstructed once, never
        # a result/replay/trace. The marker permanently records the absence.
        write_once(path / "diagnostic-reconstruction.json", {
            "schema": "bytefray.v6.e9.derived_reconstruction", "version": 1,
            "original_absent": True, "algorithm": "same-qualified-instrument",
            "source_digests": rebuilt["source_digests"]})
        write_once(target, rebuilt)
    return {name: file_digest(path / name) for name in ARTIFACTS}
