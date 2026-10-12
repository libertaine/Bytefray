"""The D9' real-fixture gate (design review Sec J P7, Sec N D9', Sec R step 8).

G.5': with ``disruption_slot_limit = 1``, K = 2, the rotating first mover and
mirrored passes, an entrant whose final executed action on every tick in which
it moves *first* repairs its own core can never be at zero core at two
consecutive end-of-tick evaluations, so it can never be captured. The
implementation phase proved this with scripted guards. This gate checks it on
the real, tracked ``e2_repair_guard`` and ``e2_disrupt_guard`` under the
primary treatment Ruleset, before any treatment matrix cell is run.

The scenarios are E3's D9 scenarios, reused unchanged
(``tools/research/v6/e3/d9_gate.run_hosted_match`` and its adversaries: an
omniscient re-disrupter, an anchor hammer, an alternating jammer and eight
seeded random jammers), each guard in each seat, at seeds 42, 1001 and 1002 --
outside the matrix's 1..32 -- for 1000 ticks. No adversary is a matrix entrant,
so no matrix cell is exposed.

Each canonical replay is read back with the E3 action/parity analyzer (and so
capture analyzer v2) and the E4 cell metrics. Under T-E4 the gate requires, for
the guard: zero capture completions, a maximum zero-core streak of 1, alive at
the end, every zero-core evaluation on its *second*-mover ticks (the G.5'
parity), and G.4' (at least 5 executed actions in both roles for every entrant
alive throughout a tick); and for the match: no zero-action live tick, no
exclusive tick, clean analyzer cross-checks and the first mover owning every
final chunk.

Two sensitivity checks show the gate can see a failure:

* **captures** -- the same scenarios under the whole-tick E2 Ruleset
  (``bytefray-rules-6-research-capture-hold-k2``) must capture the repair guard
  in at least one scenario (E3's D9 sensitivity);
* **parity** -- under the forward parent (historical T-E3), whose final chunk
  belongs to the second mover, at least one scenario must put a guard at zero
  core on its *own first-mover* tick, which the T-E4 check forbids.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from battle_engine.placement import resolve_direct_match_starts
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID

from tools.research.v6.e3 import d9_gate as e3_d9
from tools.research.v6.e3.action_parity import analyze_actions
from tools.research.v6.e3.entrants import prepare_data_root
from tools.research.v6.e4 import matrix
from tools.research.v6.e4.cell_metrics import cell_metrics
from tools.research.v6.e4.gates import G4_PRIME_MIN

D9_PRIME_GATE_VERSION = 1
D9_PRIME_RECORD_NAME = "d9_prime_real_fixture_gate.json"
GUARDS: tuple[str, ...] = e3_d9.GUARDS
ADVERSARY_HOST = e3_d9.ADVERSARY_HOST
ADVERSARIES: tuple[str, ...] = tuple(e3_d9.ADVERSARIES)
SEEDS: tuple[int, ...] = e3_d9.SEEDS
TICKS = e3_d9.TICKS
PRIMARY_ID = matrix.condition(matrix.PRIMARY_TREATMENT).ruleset_id
FORWARD_PARENT_ID = matrix.condition(matrix.PRIMARY_CONTROL).ruleset_id
WHOLE_TICK_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID


class D9PrimeGateError(RuntimeError):
    """The D9' real-fixture gate has not passed."""


def play_scenario(
    data_root: Path,
    out_dir: Path,
    *,
    ruleset_id: str,
    guard: str,
    guard_seat: str,
    adversary: str,
    seed: int,
    ticks: int = TICKS,
) -> dict[str, Any]:
    """One guard-vs-adversary match; returns the analyzers' reading of its replay."""
    arena = matrix.ARENA_SIZE
    adversary_seat = "B" if guard_seat == "A" else "A"
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=arena, entrant_count=2, supplied_starts=[None, None], seed=seed
    )
    guard_start = starts[0 if guard_seat == "A" else 1]
    target = e3_d9._Target(guard_seat, tuple((guard_start + i) % arena for i in range(8)), arena)
    replay = e3_d9.run_hosted_match(
        data_root, out_dir, ruleset_id=ruleset_id, seat_names={guard_seat: guard, adversary_seat: ADVERSARY_HOST},
        scripted_seat=adversary_seat, brain=e3_d9.ADVERSARIES[adversary](target), seed=seed, ticks=ticks,
    )
    # The adversary seat's executor is replaced, so no seat follows the core-inference contract.
    e3 = analyze_actions(replay, names_inferring_core=())
    e4 = cell_metrics(replay, e3)
    seat, other = e3["seats"][guard_seat], e3["seats"][adversary_seat]
    capture = seat["capture"]
    minimum = {
        role: min((value for value in (s["roles"][role]["min_executed_alive_throughout"] for s in (seat, other))
                   if value is not None), default=None)
        for role in ("first", "second")
    }
    return {
        "ruleset_id": ruleset_id,
        "guard": guard,
        "guard_seat": guard_seat,
        "adversary": adversary,
        "seed": seed,
        "ticks": e3["ticks"],
        "guard_alive_at_end": e3["ticks"] == ticks and capture["termination"] is None,
        "guard_completions": capture["completions"],
        "guard_max_streak": capture["max_streak"],
        "guard_zero_core_evaluations": seat["phase_lock"]["zero_core_evaluations"],
        "guard_zero_ticks_own_first": capture["zero_ticks_own_first"],
        "guard_zero_ticks_opponent_first": capture["zero_ticks_opponent_first"],
        "min_actions": minimum,
        "zero_action_live_ticks": seat["zero_action_live_ticks"] + other["zero_action_live_ticks"],
        "exclusive_ticks": e3["exclusive_ticks"],
        "final_chunk_owner_role": e4["final_chunk_owner_role"],
        "checks_ok": bool(e3["checks"]["ok"] and e4["checks"]["ok"]),
        "problems": [*e3["checks"]["problems"], *e4["checks"]["problems"]],
    }


def scenario_ok(row: dict[str, Any]) -> bool:
    """G.5' and G.4' on one T-E4 scenario."""
    return (
        row["checks_ok"]
        and row["guard_completions"] == 0
        and row["guard_max_streak"] <= 1
        and row["guard_alive_at_end"]
        and row["guard_zero_ticks_own_first"] == 0
        and row["zero_action_live_ticks"] == 0
        and row["exclusive_ticks"] == 0
        and all(value is not None and value >= G4_PRIME_MIN for value in row["min_actions"].values())
        and row["final_chunk_owner_role"] == "first"
    )


def run_gate(
    work_dir: Path | None = None,
    *,
    seeds: Sequence[int] = SEEDS,
    ticks: int = TICKS,
    adversaries: Sequence[str] = ADVERSARIES,
) -> dict[str, Any]:
    """Every guard x seat x adversary x seed under T-E4, the whole-tick E2 Ruleset and the forward parent."""
    if set(seeds) & set(matrix.SEEDS):
        raise D9PrimeGateError("D9' real-fixture scenarios must not use matrix seeds (1..32).")
    with tempfile.TemporaryDirectory(prefix="e4-d9-") as tmp:
        base = Path(work_dir) if work_dir is not None else Path(tmp)
        data_root = prepare_data_root(base / "env", [*GUARDS, ADVERSARY_HOST])
        rows: dict[str, list[dict[str, Any]]] = {PRIMARY_ID: [], WHOLE_TICK_ID: [], FORWARD_PARENT_ID: []}
        for ruleset_id, scenarios in rows.items():
            for guard in GUARDS:
                for guard_seat in ("A", "B"):
                    for adversary in adversaries:
                        for seed in seeds:
                            tag = f"{ruleset_id}/{guard}-{guard_seat}-{adversary}-{seed}"
                            scenarios.append(play_scenario(
                                data_root, base / "runs" / tag, ruleset_id=ruleset_id, guard=guard,
                                guard_seat=guard_seat, adversary=adversary, seed=seed, ticks=ticks))
    primary, whole_tick, forward = rows[PRIMARY_ID], rows[WHOLE_TICK_ID], rows[FORWARD_PARENT_ID]
    failures = [row for row in primary if not scenario_ok(row)]
    capture_sensitivity = sum(1 for row in whole_tick if row["guard"] == "e2_repair_guard" and row["guard_completions"])
    parity_sensitivity = sum(1 for row in forward if row["guard_zero_ticks_own_first"] > 0)
    clean = all(row["checks_ok"] for row in (*whole_tick, *forward))
    passed = bool(primary) and not failures and capture_sensitivity > 0 and parity_sensitivity > 0 and clean
    return {
        "d9_prime_gate_version": D9_PRIME_GATE_VERSION,
        "primary_ruleset": PRIMARY_ID,
        "capture_sensitivity_ruleset": WHOLE_TICK_ID,
        "parity_sensitivity_ruleset": FORWARD_PARENT_ID,
        "guards": list(GUARDS),
        "adversary_host": ADVERSARY_HOST,
        "adversaries": list(adversaries),
        "seeds": list(seeds),
        "ticks": ticks,
        "primary_scenarios": len(primary),
        "primary_guard_completions": sum(row["guard_completions"] for row in primary),
        "primary_max_guard_streak": max((row["guard_max_streak"] for row in primary), default=None),
        "primary_guard_zero_core_evaluations": sum(row["guard_zero_core_evaluations"] for row in primary),
        "primary_guard_zero_ticks_own_first": sum(row["guard_zero_ticks_own_first"] for row in primary),
        "primary_min_actions": {
            role: min((row["min_actions"][role] for row in primary if row["min_actions"][role] is not None), default=None)
            for role in ("first", "second")
        },
        "primary_failure_count": len(failures),
        "primary_failures": failures[:10],
        "sensitivity_scenarios": {"captures": len(whole_tick), "parity": len(forward)},
        "capture_sensitivity_repair_guard_captured_scenarios": capture_sensitivity,
        "capture_sensitivity_disrupt_guard_captured_scenarios": sum(
            1 for row in whole_tick if row["guard"] == "e2_disrupt_guard" and row["guard_completions"]),
        "parity_sensitivity_scenarios_with_own_first_zero": parity_sensitivity,
        "forward_parent_guard_completions": sum(row["guard_completions"] for row in forward),
        "status": "PASS" if passed else "FAIL",
        "scenarios": {"primary": primary, "capture_sensitivity": whole_tick, "parity_sensitivity": forward},
    }


def write_record(path: Path, record: dict[str, Any], *, freeze_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    full = {**record, "freeze_id": freeze_id, "provenance": provenance}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(full, indent=2, sort_keys=True), encoding="utf-8")
    return full


def require_gate(path: Path, *, freeze_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise D9PrimeGateError(f"No D9' real-fixture gate record at {path}.")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if record.get("freeze_id") != freeze_id:
        problems.append(f"freeze_id {record.get('freeze_id')!r} != {freeze_id!r}")
    if record.get("status") != "PASS":
        problems.append(f"status {record.get('status')!r}")
    if record.get("seeds") != list(SEEDS) or record.get("ticks") != TICKS or record.get("adversaries") != list(ADVERSARIES):
        problems.append("the record is not the full registered gate (seeds, ticks, adversaries)")
    if problems:
        raise D9PrimeGateError("D9' real-fixture gate does not permit treatment: " + "; ".join(problems))
    return record
