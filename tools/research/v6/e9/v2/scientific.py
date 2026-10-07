"""V2 coordinate and authority adapters to the immutable E9 scientific kernels.

This module never runs a match or draws entropy. Registered numerical analysis
is an authority-protected future operation; synthetic qualification exercises
only diagnostics, exact interval predicates and deterministic index recipes.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .authority import AuthorityLog
from .identities import logical_cell_id
from .records import (
    BASE,
    P_ID,
    IntegrityError,
    canonical_bytes,
    exact_keys,
    integer,
    load_protocol,
    sha256,
    validate_digest,
)

Key = tuple[str, str, int, str]
N = 1412
PHYSICAL_CELLS = 900856
# These are exact preserved implementation bytes, not replacement qualification.
INHERITED_SOURCES = {
    "analysis.py": "92d956da5c998a4ee497461016476c1e240b6a0c07cb37fccb1682909d093c76",
    "behavior.py": "2b9bba5840183a8ef62b4c6f211b9558b21616559b4bafb45dbb86b4c9c849cf",
    "collection.py": "e3f73464974d3c477eb62ebd010cb8ca13192dc6bdb2dc7cd2298eb99b16b65a",
    "constraints.py": "ad9dbe1c8adc5a22d025194644b4bb431c1b7a6b60fc198a09ff17d55c9cbdff",
    "instrument.py": "7d87137671d525c81b91b606def0d8f985b6f8359d2709cf633dc751a36f3f0d",
    "interpretation.py": "bea40e521d2a3043d855d3337efc22fc7a86a9849a095d2407aef0e468943886",
    "protocol.py": "c7a0543c9b821fa4f95b01759a51c586e1fa991f36c46e9a138ddba9ff6d7911",
    "artifacts.py": "c491f40c42fdcc972c2c8971e1ebe68d36f41b54d0c3c756439032c877323507",
}


def verify_inherited_sources() -> dict[str, Any]:
    """Read back adoption, inherited scientific contracts, packages and sources."""
    p = load_protocol()["inherited_scientific_source_pins"]
    for name, expected in INHERITED_SOURCES.items():
        if sha256((BASE / name).read_bytes()) != expected:
            raise IntegrityError("inherited scientific implementation source drift")
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    from tools.research.v6.e9.protocol import load_protocol as v1_protocol
    try:
        inherited = v1_protocol()
    except V1Error as exc:
        raise IntegrityError("inherited immutable source/package boundary failed") from exc
    if any(inherited.get(name) != value for name, value in p.items()):
        raise IntegrityError("amended scientific contract differs from inherited freeze")
    return p


def _key(record: dict, protocol: dict, n: int) -> Key:
    if type(record) is not dict or type(record.get("cell")) is not dict:
        raise IntegrityError("complete physical cell coordinates required")
    c = record["cell"]
    exact_keys(c, {"row", "opponent", "position", "seat"})
    integer(c["position"], 1, n)
    if (any(type(c[name]) is not str for name in ("row", "opponent", "seat"))
            or c["row"] not in protocol["physical_rows"]
            or c["opponent"] not in protocol["historical_members"] or c["seat"] not in ("A", "B")):
        raise IntegrityError("foreign row/opponent/seat; logical aliases add no observations")
    expected = "v6-e9-cell-v2-" + sha256(canonical_bytes(
        [P_ID, c["row"], c["opponent"], c["position"], c["seat"]]))
    if record.get("cell_identity") != expected:
        raise IntegrityError("v2 coordinate identity mismatch")
    return c["row"], c["opponent"], c["position"], c["seat"]


def _diagnostics(item: dict) -> None:
    integer(item.get("payoff_doubled"), 0, 2)
    if item.get("terminal") not in {"tick_limit", "last_agent_standing", "all_agents_dead"}:
        raise IntegrityError("authoritative terminal class required")
    for name in ("pressure", "captures"):
        predicates = item.get(name)
        if (type(predicates) is not dict or set(predicates) != {"A", "B"}
                or any(type(v) is not bool for v in predicates.values())):
            raise IntegrityError("explicit diagnostics for both victim directions required")
    behavior = item.get("behavior")
    if behavior is not None:
        if type(behavior) is not dict:
            raise IntegrityError("behavioral diagnostic object required")
        committed, realized = behavior.get("committed_revisions"), behavior.get("realized_revisions")
        integer(committed, 0, 4)
        integer(realized, 0, committed)
        phases = behavior.get("phase_differences")
        if type(phases) is not dict or set(phases) != {"1", "2", "3"}:
            raise IntegrityError("complete phase difference counters required")
        for value in phases.values():
            integer(value)
        exposures = behavior.get("phase_exposure")
        if (type(exposures) is not list
                or any(type(v) is not int or v not in (1, 2, 3) for v in exposures)
                or exposures != sorted(set(exposures))
                or any(phases[str(v)] > 0 and v not in exposures for v in (1, 2, 3))):
            raise IntegrityError("phase exposure inconsistent with causal diagnostics")


def deduplicate_copies_v2(records: Iterable[dict]) -> tuple[list[dict], int]:
    """Consolidate only byte-equivalent copies with immutable attempt provenance."""
    retained: dict[str, dict] = {}
    copies = 0
    for item in records:
        identifier = item.get("cell_identity") if type(item) is dict else None
        if type(identifier) is not str:
            raise IntegrityError("cell identity absent")
        if identifier not in retained:
            retained[identifier] = item
            continue
        provenance = item.get("execution_provenance")
        if type(provenance) is not dict:
            raise IntegrityError("duplicate copy lacks immutable provenance")
        validate_digest(provenance.get("attempt_ledger_digest"))
        hashes = provenance.get("artifact_digests")
        if type(hashes) is not dict or set(hashes) != {"result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"}:
            raise IntegrityError("duplicate copy lacks complete attempt artifact hashes")
        for value in hashes.values():
            validate_digest(value)
        if canonical_bytes(retained[identifier]) != canonical_bytes(item):
            raise IntegrityError("different executions cannot be consolidated")
        copies += 1
    return list(retained.values()), copies


def pair_blocks_v2(records: Iterable[dict], *, n: int = N) -> tuple[dict[str, list[int]], dict[Key, dict]]:
    """Complete paired rectangle. A smaller n is solely a pure synthetic fixture."""
    integer(n, 1, N)
    protocol = verify_inherited_sources()
    scores = {row: [0] * n for row in protocol["physical_rows"]}
    evidence: dict[Key, dict] = {}
    counts: Counter[tuple[str, int]] = Counter()
    for item in records:
        key = _key(item, protocol, n)
        if key in evidence:
            raise IntegrityError("duplicate coordinate invalidates the rectangle")
        _diagnostics(item)
        if key[0] == "A" and item.get("behavior") is None:
            raise IntegrityError("complete adaptive behavioral evidence required")
        evidence[key] = item
        scores[key[0]][key[2] - 1] += item["payoff_doubled"]
        counts[(key[0], key[2])] += 1
    width = 2 * len(protocol["historical_members"])
    if (len(evidence) != len(scores) * n * width or any(
            counts[(row, position)] != width for row in scores for position in range(1, n + 1))):
        raise IntegrityError("one unusable cell invalidates the complete registered rectangle")
    return scores, evidence


def evaluate_constraints_v2(evidence: Mapping[Key, dict], *, n: int = N) -> dict:
    """Preserve seat/stall/immunity/phase flags, tied comparators and seed exposure."""
    _, verified = pair_blocks_v2(evidence.values(), n=n)
    if dict(evidence) != verified:
        raise IntegrityError("diagnostic keys disagree with physical coordinates")
    from tools.research.v6.e9.constraints import evaluate
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    try:
        return evaluate(verified, load_protocol()["inherited_scientific_source_pins"], n=n)
    except V1Error as exc:
        raise IntegrityError(str(exc)) from exc


def audit_behavior(records: list, context: Any, *, row: str, opponent: str,
                   position: int, seat: str) -> dict:
    """Offline reconstruction only; never simulates a divergent world or match."""
    protocol = verify_inherited_sources()
    identity = logical_cell_id(P_ID, row, opponent, position, seat)
    if context.agent_id != seat:
        raise IntegrityError("focal context seat mismatch")
    from tools.research.v6.e9.behavior import audit, variant_for
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    try:
        return audit(records, context, variant_for(row, protocol), cell_identity=identity)
    except V1Error as exc:
        raise IntegrityError(str(exc)) from exc


def diagnostic_v2(path: Path, *, row: str, opponent: str, position: int, seat: str,
                  seed: int, expected_match_id: str) -> dict:
    """Read-only native artifact audit with v2 research coordinates/receipt IDs.

    No native match is produced. The recorded replay/result/trace wire schemas
    remain unchanged. Qualification of this adapter on native artifacts retains
    its separate match-producing coverage gate.
    """
    protocol = verify_inherited_sources()
    identity = logical_cell_id(P_ID, row, opponent, position, seat)
    integer(seed, 0, 2**64 - 1)
    if type(expected_match_id) is not str or not expected_match_id:
        raise IntegrityError("expected immutable native match identity required")
    from tools.research.v6.e9.artifacts import diagnostic
    from tools.research.v6.e9.protocol import Cell
    from tools.research.v6.e9.protocol import IntegrityError as V1Error

    class V2Cell(Cell):
        @property
        def identity(self) -> str:
            return identity

    cell = V2Cell(row, opponent, position, seat)
    try:
        result = diagnostic(path, cell, protocol, seed=seed,
                            package_names=cell.packages(protocol), expected_match_id=expected_match_id)
    except V1Error as exc:
        raise IntegrityError(str(exc)) from exc
    result["version"] = 2
    _diagnostics(result)
    return result


def recovery_eligible(facts: dict, *, cell_identity: str, binding_digest: str) -> bool:
    """Outcome-blind inherited allowlist, identical binding, one added attempt."""
    verify_inherited_sources()
    from tools.research.v6.e9.collection import RecoveryEvidence
    fields = set(RecoveryEvidence.__dataclass_fields__)
    exact_keys(facts, fields)
    validate_digest(binding_digest)
    if type(cell_identity) is not str or not cell_identity.startswith("v6-e9-cell-v2-"):
        raise IntegrityError("v2 recovery cell identity required")
    validate_digest(cell_identity.removeprefix("v6-e9-cell-v2-"))
    return RecoveryEvidence(**facts).eligible(cell_identity, binding_digest)


def registered_analysis(authority: AuthorityLog, records: Iterable[dict], *, expected_tip: str,
                        operation_id: str, instrument_digest: str,
                        collection_counts: dict[str, int], historical_integrity: str) -> dict:
    """Future final assembly: current full authority and exact 900856-cell corpus.

    This entry point performs registered resampling only after current final
    authority succeeds. It is never called during synthetic qualification.
    """
    def assemble(_lease: Any) -> dict:
        from tools.research.v6.e9.analysis import (
            contrasts,
            distinct_trajectories,
            registered_uncertainty,
        )
        from tools.research.v6.e9.constraints import evaluate

        from .records import P_DIGEST
        from .reporting import classify_report
        protocol = verify_inherited_sources()
        validate_digest(instrument_digest)
        if authority.bindings["I"]["digest"] != instrument_digest:
            raise IntegrityError("analysis instrument not bound by current authority")
        retained, copies = deduplicate_copies_v2(records)
        scores, evidence = pair_blocks_v2(retained)
        _collection_counts(collection_counts)
        for item in retained:
            _provenance(item)
        bands = registered_uncertainty(scores, protocol, instrument_digest, P_DIGEST)
        gaps = contrasts(bands, protocol)
        constraints = evaluate(evidence, protocol)
        adaptive = [r for key, r in evidence.items() if key[0] == "A"]
        committed = sum(r["behavior"]["committed_revisions"] for r in adaptive)
        realized = sum(r["behavior"]["realized_revisions"] for r in adaptive)
        matches = [r for r in adaptive if r["behavior"]["realized_revisions"] > 0]
        positions = {r["cell"]["position"] for r in matches}
        seats = {s: len({r["cell"]["position"] for r in matches if r["cell"]["seat"] == s}) for s in ("A", "B")}
        decision = classify_report(integrity=True, realized_positions=len(positions),
                                   seat_a_positions=seats["A"], seat_b_positions=seats["B"],
                                   realized_revisions=realized,
                                   statuses={g: v.status for g, v in gaps["gaps"].items()},
                                   severe_constraints=constraints["severe"],
                                   timing_reproduction=gaps["timing_qualifier"],
                                   historical_integrity=historical_integrity, gates_valid=True)
        strata = {}
        for opponent in protocol["historical_members"]:
            for seat in ("A", "B"):
                selected = [r for r in adaptive if r["cell"]["opponent"] == opponent and r["cell"]["seat"] == seat]
                strata[opponent + "/" + seat] = {
                    "match_denominator": N,
                    "committed_revisions": sum(r["behavior"]["committed_revisions"] for r in selected),
                    "realized_revisions": sum(r["behavior"]["realized_revisions"] for r in selected),
                    "realized_positions": len({r["cell"]["position"] for r in selected if r["behavior"]["realized_revisions"]}),
                }
        return {"means": bands.means, "row_intervals": {p: asdict(v) for p, v in bands.bands.items()},
                "interval_half_width": bands.half_width, "bootstrap_envelope": bands.bootstrap_envelope,
                "comparator_reselections": bands.comparator_changes,
                "resampled_quantity_ranges": bands.resampled_quantity_ranges,
                "contrasts": {**gaps, "gaps": {g: {**asdict(v), "status": v.status} for g, v in gaps["gaps"].items()}},
                "constraints": constraints, "classification": decision,
                "collection": {**collection_counts, "duplicate_copies_consolidated": copies},
                "behavior": {"committed_revisions": committed, "realized_revisions": realized,
                             "masked_revisions": committed - realized, "realized_matches": len(matches),
                             "no_commit_matches": sum(r["behavior"]["committed_revisions"] == 0 for r in adaptive),
                             "no_realization_matches": len(adaptive) - len(matches),
                             "adaptive_match_denominator": 31064, "position_denominator": N,
                             "realized_positions": len(positions), "seat_positions": seats, "strata": strata},
                "trajectories": distinct_trajectories([r["trajectory_digest"] for r in retained])}
    return authority.protected("final_assembly", expected_tip=expected_tip,
                               operation_id=operation_id, action=assemble)


def _collection_counts(counts: dict) -> None:
    exact_keys(counts, {"started", "completed", "validated", "eligible_failures", "recovery_starts", "recovered_completions"})
    for value in counts.values():
        integer(value)
    if (counts["completed"] != PHYSICAL_CELLS or counts["validated"] != PHYSICAL_CELLS
            or counts["started"] != PHYSICAL_CELLS + counts["recovery_starts"]
            or not counts["eligible_failures"] == counts["recovery_starts"] == counts["recovered_completions"]
            or counts["recovery_starts"] > PHYSICAL_CELLS):
        raise IntegrityError("attempt denominators or one-additional-attempt cap inconsistent")


def _provenance(item: dict) -> None:
    provenance = item.get("execution_provenance")
    if type(provenance) is not dict:
        raise IntegrityError("complete diagnostic attempt provenance required")
    validate_digest(provenance.get("attempt_ledger_digest"))
    hashes = provenance.get("artifact_digests")
    if type(hashes) is not dict or set(hashes) != {"result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"}:
        raise IntegrityError("same-attempt artifacts required")
    for value in hashes.values():
        validate_digest(value)
    validate_digest(item.get("trajectory_digest"))


def seal_final_protected(authority: AuthorityLog, destination: Path, body: dict, *,
                         expected_tip: str, operation_id: str) -> str:
    from .reporting import seal_final
    def seal(_lease: Any) -> str:
        verify_inherited_sources()
        return seal_final(destination, body)
    return authority.protected("final_seal", expected_tip=expected_tip,
                               operation_id=operation_id, action=seal)
