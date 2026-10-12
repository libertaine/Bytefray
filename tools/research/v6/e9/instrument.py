"""Qualification identity and complete registered result assembly; no seed generator."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .analysis import contrasts, distinct_trajectories, registered_uncertainty
from .constraints import evaluate
from .interpretation import classify
from .protocol import (
    PROTOCOL_DIGEST,
    PROTOCOL_ID,
    ROOT,
    Cell,
    IntegrityError,
    canonical,
    digest,
    file_digest,
    read_json,
    write_once,
)

MODULES = ("protocol.py", "analysis.py", "interpretation.py", "collection.py", "behavior.py",
           "artifacts.py", "constraints.py", "instrument.py", "runner.py")
QUALIFICATION = ROOT / "tools/research/v6/e9/instrument_qualification.json"


def identity() -> tuple[str, dict[str, str]]:
    manifest = {"tools/research/v6/e9/" + name: file_digest(ROOT / "tools/research/v6/e9" / name)
                for name in MODULES}
    return digest(canonical({"protocol_digest": PROTOCOL_DIGEST, "sources": manifest})), manifest


def require_qualified() -> str:
    record = read_json(QUALIFICATION)
    sha, manifest = identity()
    if (record.get("schema") != "bytefray.v6.e9.instrument_qualification" or record.get("version") != 1
            or record.get("status") != "PASS" or record.get("protocol_id") != PROTOCOL_ID
            or record.get("instrument_digest") != sha or record.get("sources") != manifest
            or record.get("record_digest") != digest(canonical({k: v for k, v in record.items() if k != "record_digest"}))
            or record.get("seed_generation") is not False or record.get("payoff_execution") is not False
            or any(file_digest(ROOT / path) != expected for path, expected in record["qualification_sources"].items())):
        raise IntegrityError("instrument lacks an unchanged independent qualification boundary")
    return sha


def deduplicate_copies(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Only copies with the same immutable execution provenance are consolidated."""
    retained: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for record in records:
        identifier = record["cell_identity"]
        if identifier not in retained:
            retained[identifier] = record
            continue
        previous = retained[identifier]
        provenance = record.get("execution_provenance", {})
        if (not provenance.get("attempt_ledger_digest")
                or set(provenance.get("artifact_digests", {})) != {
                    "result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"}
                or canonical(previous) != canonical(record)):
            raise IntegrityError("multiple executions or unproven duplicate copy")
        duplicates += 1
    return list(retained.values()), duplicates


def pair_blocks(records: Iterable[dict[str, Any]], protocol: dict[str, Any], *, n: int = 1412
                ) -> tuple[dict[str, list[int]], dict[tuple[str, str, int, str], dict[str, Any]]]:
    """Aliases never add observations; duplicate coordinates never become extra weight."""
    evidence: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    scores = {row: [0] * n for row in protocol["physical_rows"]}
    counts: Counter[tuple[str, int]] = Counter()
    for record in records:
        cell = Cell(**record["cell"])
        cell.validate(protocol)
        if cell.position > n or record["cell_identity"] != cell.identity:
            raise IntegrityError("foreign position or changed cell identity")
        key = cell.row, cell.opponent, cell.position, cell.seat
        if key in evidence:
            raise IntegrityError("duplicate physical cell; execution copies must be deduplicated with provenance")
        value = record["payoff_doubled"]
        if type(value) is not int or value not in (0, 1, 2):
            raise IntegrityError("invalid payoff evidence")
        evidence[key] = record
        scores[cell.row][cell.position - 1] += value
        counts[(cell.row, cell.position)] += 1
    expected = 2 * len(protocol["historical_members"])
    if (len(evidence) != len(protocol["physical_rows"]) * n * expected
            or any(counts[(row, position)] != expected for row in scores for position in range(1, n + 1))):
        raise IntegrityError("one unusable cell invalidates the full registered rectangle")
    return scores, evidence


def assemble(records: Iterable[dict[str, Any]], protocol: dict[str, Any], instrument_digest: str,
             collection_counts: dict[str, int]) -> dict[str, Any]:
    retained, copies = deduplicate_copies(records)
    scores, evidence = pair_blocks(retained, protocol)
    collection_counts = {**collection_counts, "duplicate_copies_consolidated": copies}
    bands = registered_uncertainty(scores, protocol, instrument_digest, PROTOCOL_DIGEST)
    gaps = contrasts(bands, protocol)
    interaction = evaluate(evidence, protocol)
    adaptive = [r for key, r in evidence.items() if key[0] == "A"]
    if any(r.get("behavior") is None for r in adaptive):
        raise IntegrityError("missing adaptive behavioral evidence")
    committed = sum(r["behavior"]["committed_revisions"] for r in adaptive)
    realized = sum(r["behavior"]["realized_revisions"] for r in adaptive)
    matches = [r for r in adaptive if r["behavior"]["realized_revisions"] > 0]
    positions = {r["cell"]["position"] for r in matches}
    seat_positions = {seat: len({r["cell"]["position"] for r in matches if r["cell"]["seat"] == seat})
                      for seat in ("A", "B")}
    decision = classify(integrity=True, realized_revisions=realized, realized_positions=len(positions),
                        seat_positions=seat_positions, statuses={g: gap.status for g, gap in gaps["gaps"].items()},
                        severe_constraints=interaction["severe"], timing_reproduced=gaps["timing_qualifier"])
    behavioral_strata = {}
    for opponent in protocol["historical_members"]:
        for seat in ("A", "B"):
            selected = [r for r in adaptive if r["cell"]["opponent"] == opponent and r["cell"]["seat"] == seat]
            behavioral_strata[opponent + "/" + seat] = {
                "committed_revisions": sum(r["behavior"]["committed_revisions"] for r in selected),
                "realized_revisions": sum(r["behavior"]["realized_revisions"] for r in selected),
                "realized_positions": len({r["cell"]["position"] for r in selected if r["behavior"]["realized_revisions"]}),
                "match_denominator": 1412}
    return {"schema": "bytefray.v6.e9.registered_result", "version": 1,
            "protocol_id": PROTOCOL_ID, "protocol_digest": PROTOCOL_DIGEST,
            "instrument_digest": instrument_digest, "collection": collection_counts,
            "means": bands.means, "row_intervals": {p: asdict(v) for p, v in bands.bands.items()},
            "interval_half_width": bands.half_width, "bootstrap_envelope": bands.bootstrap_envelope,
            "comparator_reselections": bands.comparator_changes,
            "resampled_quantity_ranges": bands.resampled_quantity_ranges,
            "contrasts": {**gaps, "gaps": {g: {**asdict(v), "status": v.status} for g, v in gaps["gaps"].items()}},
            "behavior": {"committed_revisions": committed, "realized_revisions": realized,
                         "masked_revisions": committed - realized, "realized_matches": len(matches),
                         "no_commit_matches": sum(r["behavior"]["committed_revisions"] == 0 for r in adaptive),
                         "no_realization_matches": len(adaptive) - len(matches),
                         "adaptive_match_denominator": 31064, "realized_positions": len(positions),
                         "position_denominator": 1412, "seat_positions": seat_positions,
                         "strata": behavioral_strata},
            "trajectories": distinct_trajectories([r["trajectory_digest"] for r in evidence.values()]),
            "constraints": interaction, "classification": asdict(decision),
            "requirement_C": "ESTABLISHED in the registered bounded scope" if decision.priority == 7 else "NOT ESTABLISHED"}


def seal(record: dict[str, Any], destination: Path) -> str:
    """The machine record is exclusive and sealed before any prose rendering."""
    return write_once(destination, record)
