"""E8 phase I8-1: byte-identity goldens for the two exact E8 parents.

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md §1 (I8-1)
and pre-registration clause D8-6. E8's controls are T-E6's and T-E6L's
Rulesets, unchanged:

* C8, ``bytefray-rules-6-research-sensing-r32`` (whole-tick disruption);
* C8L, ``bytefray-rules-6-research-disruption-slot1-sensing-r32`` (λ = 1).

These goldens are recorded against the engine **before** any E8 engine, API
or trace change, so that the later implementation must reproduce every
scenario byte for byte while active sensing is off. Only existing engine
behavior and existing tracked fixtures are used: E6's family packages, two
E2 fixtures and the ``v4_scout`` starter agent. No E8 family, no SENSE, no
new field.

**What each case pins** (``describe``):

* ``replay_sha256``: the replay's exact bytes;
* ``trace_sha256``: the agent trace's exact bytes, with only the value of
  ``wall_time_ms`` masked, because it is the one nondeterministic field, and
  line endings normalized to LF, because the engine writes the trace with the
  platform's. Key sets, key order and ``null`` fields are pinned as written, so
  an optional field later serialized as ``null`` changes this digest;
* one digest per trace record type (header, reset, declaration,
  decision_v2, binding), to localize a change;
* per entrant, the digest of the D8-3 comparison surface: each
  ``decision_v2`` record's ``action`` and the observation's information
  fields, in order;
* ``result_id``, ``match_id``, and the outcome (winner, ticks, reason);
* coverage statistics, derived from the trace (action kinds, applied
  statuses, visibility, short and skipped ticks, first movers).

**The record** (``parent_goldens.json``) also pins the scenario definitions,
the golden seeds, each Ruleset's identity and policy snapshot, every
fixture's file digests, and the source commit and engine tree used to
generate it. ``--write <commit>`` regenerates it from this committed tool,
deterministically.

**The golden seeds are infrastructure, not experiment seeds.** ``GOLDEN_SEEDS``
are small fixed integers, as E6's parent freeze used. The E8 experiment seed
set does not exist yet, and when it does it is 32 values from
``secrets.randbelow(2**53)`` (PR8 §9).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from battle_engine.agent_test import DevelopmentTestOutcome, test_agent
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e6 import family as e6_family
from tools.research.v6.experiment_harness import (
    find_tracked_agent_source,
    prepare_benchmark_data_root,
)

RECORD_PATH = Path(__file__).with_name("parent_goldens.json")
SCHEMA = "bytefray.v6.e8.parent_goldens"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

ARENA_SIZE = 512
MAX_TICKS = 1000
QUOTA = 8

#: Infrastructure seeds for the goldens, not E8 experiment seeds (module docstring).
GOLDEN_SEEDS: tuple[int, ...] = (1, 2, 3)

#: The two E8 parents, by condition.
PARENTS: Mapping[str, str] = {
    "C8": BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    "C8L": BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    first: str
    second: str
    exercises: str


def _e6(member: str, role: str = "primary") -> str:
    return e6_family.package_id(member, role)


#: Each runs in both orientations, at every golden seed, under both parents.
SCENARIOS: tuple[Scenario, ...] = (
    Scenario("rush-vs-guard", _e6("RUSH"), _e6("GUARD"),
             "MOVE search, visibility at 32, disruption, verification READs, core writes, captures"),
    Scenario("stealth-vs-evader", _e6("STEALTH"), _e6("EVADER"),
             "READ stride search, a first-callback evasion MOVE, guard repair writes"),
    Scenario("split-vs-adapt", _e6("SPLIT"), _e6("ADAPT"),
             "two processes of one entrant sharing its offers, ADAPT's own-core check READ"),
    Scenario("paced-vs-lurk", _e6("PACED"), _e6("LURK"),
             "paced search on odd callback indexes, a non-searching attacker"),
    Scenario("greed-mirror", _e6("GREED"), _e6("GREED", "twin"),
             "a primary-against-twin mirror of two painters, with no search or disruption"),
    Scenario("scout-vs-repair", "v4_scout", "e2_repair_guard",
             "bounded reach 8, below the radius of 32, searching by movement"),
)


def cases() -> tuple[tuple[str, Scenario, str, str, int], ...]:
    """The fixed matrix: (condition, scenario, seat A, seat B, seed)."""
    return tuple(
        (condition, scenario, seat_a, seat_b, seed)
        for condition in PARENTS
        for scenario in SCENARIOS
        for seat_a, seat_b in ((scenario.first, scenario.second), (scenario.second, scenario.first))
        for seed in GOLDEN_SEEDS
    )


def case_label(condition: str, scenario: str, seat_a: str, seat_b: str, seed: int) -> str:
    return f"{condition}:{scenario}:{seat_a}-vs-{seat_b}:s{seed}"


# ---------------------------------------------------------------------------
# Fixtures and Rulesets
# ---------------------------------------------------------------------------


def package_names() -> tuple[str, ...]:
    return tuple(sorted({name for scenario in SCENARIOS for name in (scenario.first, scenario.second)}))


def source_dir(name: str) -> Path:
    if name in e6_family.PACKAGES:
        return e6_family.FIXTURE_DIR / name
    found = find_tracked_agent_source(name)
    if found is None:
        raise FileNotFoundError(f"no tracked source for fixture {name!r}")
    return found


def fixture_fingerprint(name: str) -> dict[str, str]:
    """SHA-256 of every tracked file of a fixture, by path relative to its directory (LF-normalized)."""
    directory = source_dir(name)
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def _plain(value: Any) -> Any:
    if isinstance(value, (frozenset, set)):
        return sorted(_plain(item) for item in value)
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def ruleset_snapshot(ruleset_id: str) -> dict[str, Any]:
    """Every field of the Ruleset's policy as it stands now."""
    policy = resolve_ruleset_policy(ruleset_id)
    return {field.name: _plain(getattr(policy, field.name)) for field in fields(policy)}


def prepare(root: Path, names: Sequence[str]) -> None:
    e6_family.prepare_data_root(root, [name for name in names if name in e6_family.PACKAGES])
    others = [name for name in names if name not in e6_family.PACKAGES]
    if others:
        prepare_benchmark_data_root(root, others)


# ---------------------------------------------------------------------------
# Running and describing one case
# ---------------------------------------------------------------------------

_WALL_TIME = re.compile(r'"wall_time_ms": (?:-?[0-9][0-9.eE+-]*|null)')
MASK = '"wall_time_ms": "<masked>"'
TRACE_RECORD_TYPES: tuple[str, ...] = ("header", "reset", "declaration", "decision_v2", "binding")
D8_3_OBSERVATION_FIELDS: tuple[str, ...] = (
    "visible_enemy_anchor_addresses", "previous_sense_anchors", "previous_read_value", "previous_read_owner")


@dataclass(frozen=True)
class Artifacts:
    replay_path: Path
    trace_path: Path | None
    result_id: str
    match_id: str
    winner: str | None
    ticks: int
    reason: str


def run_case(root: Path, ruleset_id: str, seat_a: str, seat_b: str, seed: int, *, traced: bool = True) -> Artifacts:
    """Run one golden case with existing engine behavior only.

    It uses the development-test path with the arguments E6's traced cells
    passed (``tools/research/v6/e6/traces.py``), which resolves each package's
    manifest parameter defaults and the seeded starts, as the E8 harness will.
    """
    prepare(root, [seat_a, seat_b])
    cell = root / "cells" / f"{ruleset_id}-{seat_a}-vs-{seat_b}-s{seed}-{'t' if traced else 'u'}"
    outcome = test_agent(
        seat_a, opponent=seat_b, seed=seed, ticks=MAX_TICKS, timeout=None, trace=traced, run_dir=cell,
        data_root=root, ruleset_id=ruleset_id, agent_start=None, opponent_start=None, arena_size=ARENA_SIZE,
        instr_per_tick=None, locality_reach=None, kill_weight=None, scheduler_chunk_size=None,
        scheduler_rotate_start=None)
    if not isinstance(outcome, DevelopmentTestOutcome):
        raise RuntimeError(f"{ruleset_id} {seat_a} vs {seat_b} s{seed} did not complete: {outcome!r}")
    result = outcome.match_result
    if result.result_id is None or result.match_id is None:
        raise RuntimeError(f"no result or match identity for {ruleset_id} {seat_a} vs {seat_b} s{seed}")
    return Artifacts(cell / "replay.jsonl", outcome.trace_path, result.result_id, result.match_id, result.winner,
                     result.ticks_run, result.termination_reason.value)


def masked_trace_lines(trace_path: Path) -> list[str]:
    """The trace's lines, byte for byte except for the masked ``wall_time_ms`` values.

    The engine writes the trace in text mode, so its line endings are the
    platform's (CRLF on Windows), unlike the replay, which it writes with LF.
    Line endings are therefore normalized to LF, so that a golden is the same on
    every platform. Every other byte of every line is kept.
    """
    lines = trace_path.read_bytes().decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [_WALL_TIME.sub(MASK, line.removesuffix("\r")) for line in lines]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def coverage(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """What a case exercises, from its decision records."""
    decisions = [record for record in records if record.get("record_type") == "decision_v2"]
    kinds: dict[str, int] = {}
    statuses: dict[str, int] = {}
    per_tick: dict[tuple[str, int], int] = {}
    first_mover: dict[int, str] = {}
    visible = 0
    for record in decisions:
        kinds[record["action"]["kind"]] = kinds.get(record["action"]["kind"], 0) + 1
        status = record["applied_result"]["status"]
        statuses[status] = statuses.get(status, 0) + 1
        tick = record["observation"]["current_tick"]
        per_tick[(record["agent_id"], tick)] = per_tick.get((record["agent_id"], tick), 0) + 1
        first_mover.setdefault(tick, record["agent_id"])
        visible += bool(record["observation"]["visible_enemy_anchor_addresses"])
    short = sum(1 for count in per_tick.values() if count < QUOTA)
    skipped = 0
    for agent in sorted({agent for agent, _ in per_tick}):
        ticks = sorted(tick for who, tick in per_tick if who == agent)
        skipped += sum(1 for tick in range(ticks[0], ticks[-1] + 1) if tick not in ticks)
    return {
        "decisions": len(decisions),
        "action_kinds": dict(sorted(kinds.items())),
        "statuses": dict(sorted(statuses.items())),
        "visible_decisions": visible,
        "short_ticks": short,
        "skipped_ticks": skipped,
        "first_movers": dict(sorted({agent: sum(1 for who in first_mover.values() if who == agent)
                                     for agent in set(first_mover.values())}.items())),
    }


def describe(artifacts: Artifacts) -> dict[str, Any]:
    """Every pinned fact of one case."""
    if artifacts.trace_path is None:
        raise ValueError("a golden case is always traced")
    lines = masked_trace_lines(artifacts.trace_path)
    records = [json.loads(line) for line in lines]
    by_type = {kind: "\n".join(line for line, record in zip(lines, records, strict=True)
                               if record.get("record_type") == kind) for kind in TRACE_RECORD_TYPES}
    unknown = sorted({str(record.get("record_type")) for record in records} - set(TRACE_RECORD_TYPES))
    surface = {
        agent: _sha(json.dumps([[record["action"], {name: record["observation"].get(name, "<absent>")
                                                    for name in D8_3_OBSERVATION_FIELDS}]
                                for record in records
                                if record.get("record_type") == "decision_v2" and record["agent_id"] == agent],
                               sort_keys=True))
        for agent in ("A", "B")
    }
    return {
        "winner": artifacts.winner,
        "ticks": artifacts.ticks,
        "reason": artifacts.reason,
        "result_id": artifacts.result_id,
        "match_id": artifacts.match_id,
        "replay_sha256": hashlib.sha256(artifacts.replay_path.read_bytes()).hexdigest(),
        "trace_sha256": _sha("\n".join(lines) + "\n"),
        "trace_lines": len(lines),
        "trace_record_sha256": {kind: _sha(text) for kind, text in by_type.items()},
        "unknown_record_types": unknown,
        "d8_3_surface_sha256": surface,
        "coverage": coverage(records),
    }


def compare(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> list[str]:
    """Every pinned fact that differs (empty when the case reproduces)."""
    return [f"{key}: golden {expected.get(key)!r} != observed {observed.get(key)!r}"
            for key in sorted(set(expected) | set(observed)) if expected.get(key) != observed.get(key)]


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def definition() -> dict[str, Any]:
    """Everything the record pins except the per-case facts and the provenance."""
    return {
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "quota": QUOTA,
        "golden_seeds": {"values": list(GOLDEN_SEEDS),
                         "standing": "infrastructure seeds for these goldens; not the E8 experiment seed set, "
                                     "which does not exist"},
        "parents": {condition: {"ruleset_id": ruleset_id, "policy": ruleset_snapshot(ruleset_id)}
                    for condition, ruleset_id in PARENTS.items()},
        "scenarios": [{"name": s.name, "first": s.first, "second": s.second, "exercises": s.exercises}
                      for s in SCENARIOS],
        "orientations": "both",
        "fixtures": {name: fixture_fingerprint(name) for name in package_names()},
        "masked": {"field": "wall_time_ms", "as": MASK},
        "trace_line_endings": "normalized to LF (the engine writes the trace with platform line endings)",
    }


def generate(source_commit: str) -> dict[str, Any]:
    """Run every case against the live engine and build the record."""
    records = []
    with tempfile.TemporaryDirectory(prefix="e8-parent-goldens-") as tmp:
        for index, (condition, scenario, seat_a, seat_b, seed) in enumerate(cases()):
            artifacts = run_case(Path(tmp) / f"case{index:03d}", PARENTS[condition], seat_a, seat_b, seed)
            records.append({"condition": condition, "ruleset_id": PARENTS[condition], "scenario": scenario.name,
                            "seat_a": seat_a, "seat_b": seat_b, "seed": seed, "golden": describe(artifacts)})
    return {
        "schema": SCHEMA,
        "version": 1,
        "phase": "I8-1",
        "clause": "D8-6",
        "provenance": {"source_commit": source_commit,
                       "engine_tree": _git("rev-parse", f"{source_commit}:engine/src"),
                       "tool": "tools/research/v6/e8/parent_goldens.py",
                       "tool_sha256": hashlib.sha256((REPOSITORY_ROOT / "tools/research/v6/e8/parent_goldens.py")
                                                     .read_bytes().replace(b"\r\n", b"\n")).hexdigest()},
        "definition": definition(),
        "cases": records,
    }


def load_record(path: Path = RECORD_PATH) -> dict[str, Any]:
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema") != SCHEMA or record.get("version") != 1:
        raise ValueError(f"{path} is not an E8 parent-golden record, version 1")
    return record


if __name__ == "__main__":  # pragma: no cover - the recording step, run once at I8-1
    if len(sys.argv) != 3 or sys.argv[1] != "--write":
        raise SystemExit("usage: python -m tools.research.v6.e8.parent_goldens --write <source commit>")
    if _git("status", "--porcelain"):
        raise SystemExit("the goldens are recorded from a clean tree only")
    if _git("rev-parse", "--short", "HEAD") != sys.argv[2]:
        raise SystemExit(f"HEAD is not {sys.argv[2]}; record at the commit you name")
    record = generate(sys.argv[2])
    RECORD_PATH.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(record['cases'])} cases written to {RECORD_PATH}")
