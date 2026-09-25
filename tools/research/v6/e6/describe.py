"""E6 descriptive reporting: pre-registration Sec 6.2 and 6.3 (never hypothesis inputs).

* **Alternation** (Sec 6.2, [O-8]): E4's ``cell_metrics`` (FMA and FPS),
  unchanged, for every F1 cell. It reads E3's ``analyze_actions`` telemetry,
  also unchanged; no E6 name is a core-inferring fixture of the E2
  contract, so ``names_inferring_core`` stays empty.
* **Seat and parity** (Sec 6.3), from the compact telemetry summaries:
  - which seat first held the other's anchor in its visible set;
  - for fast searchers (RUSH, SPLIT), the parity of the callback index at
    which they first detected, by seat (design review T1/T4);
  - for EVADER, whether its opponent detected it before its evade MOVE
    ("caught still on its core"), by EVADER's seat (T2).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e3.action_parity import analyze_actions
from tools.research.v6.e4.cell_metrics import cell_metrics
from tools.research.v6.e6 import family

FAST_SEARCHERS: tuple[str, ...] = ("RUSH", "SPLIT")


def alternation_cell(cell_dir: Path) -> dict[str, Any]:
    replay = cell_dir / "replay.jsonl"
    e3 = analyze_actions(replay, cell_dir / "result.json")
    return cell_metrics(replay, e3)


def alternation(field_root: Path, cells: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """FMA and FPS for every cell, with band and status counts."""
    rows: dict[str, Any] = {}
    bands: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for cell in cells:
        metrics = alternation_cell(field_root / str(cell["artifact_dir"]))
        rows[str(cell["schedule_id"])] = metrics
        fma = metrics.get("fma") or {}
        bands[str(fma.get("band"))] += 1
        statuses[str(fma.get("status"))] += 1
    return {"cells": rows, "fma_bands": dict(sorted(bands.items())), "fma_status": dict(sorted(statuses.items()))}


def _members(line: Mapping[str, Any]) -> dict[str, str]:
    """Seat -> member for one summary line."""
    return {"A": family.PACKAGES[line["seat_a"]][0], "B": family.PACKAGES[line["seat_b"]][0]}


def seat_and_parity(summaries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    first_seat: Counter[str] = Counter()
    parity: dict[str, Counter[str]] = {member: Counter() for member in FAST_SEARCHERS}
    caught: dict[str, Counter[str]] = {"A": Counter(), "B": Counter()}
    for line in summaries:
        summary = line["summary"]
        members = _members(line)
        first_seat[str(summary["saw_first"])] += 1
        for seat, member in members.items():
            if member in FAST_SEARCHERS:
                index = summary["first_detection_callback"][seat]
                parity[member][f"{seat}:{'none' if index is None else ('odd' if index % 2 else 'even')}"] += 1
            if member == "EVADER":
                rival = "B" if seat == "A" else "A"
                seen, moved = summary["first_detection"][rival], summary["first_move"][seat]
                on_core = seen is not None and (moved is None or seen[1] < moved[1])
                caught[seat]["caught_on_core" if on_core else "not_caught_on_core"] += 1
    return {
        "first_detection_seat": dict(sorted(first_seat.items())),
        "fast_searcher_arrival_parity": {m: dict(sorted(c.items())) for m, c in parity.items()},
        "evader_caught_on_core_by_seat": {s: dict(sorted(c.items())) for s, c in caught.items()},
    }
