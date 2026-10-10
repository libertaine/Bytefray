"""V6 Phase 4B equivalence-gate checker (task Sec 13).

Compares the two full V6-Bench-8 round-robin runs
``phase4b_corpus_runner.py equivalence`` produces (stable v4 vs. the
variable-arena research Ruleset, both at arena 512, both over the standard
eight seeds and both orientations) cell by cell: placement geometry, match
outcome, winner, ticks run, score, territory, kills/deaths, memory writes,
termination reason, and the full replay event stream -- excluding only the
fields a *different Ruleset identity* is expected, and required, to change
(match_id, result_id, replay_id/sha256, ruleset_id, timestamps/occurrence
ids).

Research-only, isolated from gameplay runtime, deterministic: reads
already-written artifacts, executes nothing, and never mutates them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "engine" / "src"))

RUNS_ROOT = REPO_ROOT / "runs" / "research_v6_phase4b"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _null_result_identity(result: dict[str, Any]) -> dict[str, Any]:
    result = dict(result)
    for key in ("match_id", "result_id", "ruleset_id", "completed_at", "occurrence_id"):
        result.pop(key, None)
    replay = dict(result.get("replay") or {})
    replay.pop("replay_id", None)
    replay.pop("sha256", None)
    result["replay"] = replay
    return result


def _null_replay_line_identity(line: dict[str, Any]) -> dict[str, Any]:
    line = dict(line)
    for key in ("replay_id", "match_id", "result_id", "ruleset_id"):
        line.pop(key, None)
    return line


def _load_replay_lines(path: Path) -> list[dict[str, Any]]:
    lines = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            lines.append(_null_replay_line_identity(json.loads(raw)))
    return lines


def compare_condition(v4_root: Path, research_root: Path, *, deep_replay: bool = True) -> dict[str, Any]:
    request_dirs = sorted(p.name for p in v4_root.iterdir() if p.is_dir())
    total_cells = 0
    mismatches: list[dict[str, Any]] = []
    placement_mismatches: list[dict[str, Any]] = []

    for req_name in request_dirs:
        v4_eval = _load_json(v4_root / req_name / "evaluation.json")
        research_eval = _load_json(research_root / req_name / "evaluation.json")
        v4_cells = {cell["matrix_ordinal"]: cell for cell in v4_eval["cells"]}
        research_cells = {cell["matrix_ordinal"]: cell for cell in research_eval["cells"]}
        assert set(v4_cells) == set(research_cells), (
            f"{req_name}: matrix ordinal sets differ between v4 and research-scale runs"
        )

        for ordinal, v4_cell in v4_cells.items():
            research_cell = research_cells[ordinal]
            total_cells += 1

            # Placement geometry must be byte-identical (same seed, same
            # arena, same production seeded-placement seam).
            if (v4_cell["subject_start"], v4_cell["opponent_start"]) != (
                research_cell["subject_start"],
                research_cell["opponent_start"],
            ):
                placement_mismatches.append(
                    {
                        "request": req_name,
                        "ordinal": ordinal,
                        "v4_starts": (v4_cell["subject_start"], v4_cell["opponent_start"]),
                        "research_starts": (
                            research_cell["subject_start"],
                            research_cell["opponent_start"],
                        ),
                    }
                )

            v4_result_path = v4_root / req_name / v4_cell["artifact_dir"] / "result.json"
            research_result_path = (
                research_root / req_name / research_cell["artifact_dir"] / "result.json"
            )
            v4_result = _null_result_identity(_load_json(v4_result_path))
            research_result = _null_result_identity(_load_json(research_result_path))

            if v4_result != research_result:
                mismatches.append(
                    {
                        "request": req_name,
                        "ordinal": ordinal,
                        "v4_result": v4_result,
                        "research_result": research_result,
                    }
                )
                continue

            if deep_replay:
                v4_replay = _load_replay_lines(v4_root / req_name / v4_cell["artifact_dir"] / "replay.jsonl")
                research_replay = _load_replay_lines(
                    research_root / req_name / research_cell["artifact_dir"] / "replay.jsonl"
                )
                if v4_replay != research_replay:
                    mismatches.append(
                        {
                            "request": req_name,
                            "ordinal": ordinal,
                            "reason": "replay_event_stream_mismatch",
                        }
                    )

    return {
        "total_cells_compared": total_cells,
        "result_mismatches": len(mismatches),
        "placement_mismatches": len(placement_mismatches),
        "mismatch_samples": mismatches[:5],
        "placement_mismatch_samples": placement_mismatches[:5],
    }


def main() -> int:
    v4_root = RUNS_ROOT / "equivalence" / "v4"
    research_root = RUNS_ROOT / "equivalence" / "research-scale"
    report = compare_condition(v4_root, research_root, deep_replay=True)
    out_path = RUNS_ROOT / "equivalence_check_report.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str)[:4000])
    print(f"\nwritten: {out_path}")
    ok = report["result_mismatches"] == 0 and report["placement_mismatches"] == 0
    print("\nEQUIVALENCE GATE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
