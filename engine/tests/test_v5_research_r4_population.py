from __future__ import annotations

"""V5 research Phase R4: population manifest, seed discipline, and metrics.

R4's central methodological risk is overfitting: an agent population tuned
on the seeds it is later evaluated on would produce exactly the "population
confound" result R4 exists to test for. These tests pin the discipline that
prevents it, and the one additive analyzer field R4 introduced.
"""

import json
from pathlib import Path

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.r4_population import (
    ARENA_SIZE,
    DEVELOPMENT_SEEDS,
    EVALUATION_SEEDS,
    INTERPRETATION_GATE,
    MAX_TICKS,
    QUALIFICATION_FIXTURES,
    R4_POPULATION,
    R4_POPULATION_IDS,
    RULESET_ID,
    build_population_manifest,
    population_fingerprints,
)
from tools.research.v5.r4_runner import build_evaluation_pairings

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE0_CORPUS = REPO_ROOT / "runs" / "v5_phase0_corpus"


def test_development_and_evaluation_seeds_are_disjoint() -> None:
    """The freeze discipline that keeps R4 from tuning on its own test set."""

    assert set(DEVELOPMENT_SEEDS) & set(EVALUATION_SEEDS) == set()
    # Evaluation seeds reproduce Phase 0's canonical set exactly.
    assert EVALUATION_SEEDS == (1, 2, 3, 4, 5, 6, 7, 8)
    assert len(DEVELOPMENT_SEEDS) == len(EVALUATION_SEEDS)


def test_qualification_fixtures_are_not_evaluation_population_members() -> None:
    """Qualification must not be able to contaminate the evaluation."""

    assert set(QUALIFICATION_FIXTURES) & set(R4_POPULATION_IDS) == set()


def test_evaluation_corpus_matches_phase0_shape() -> None:
    """6 x 6 ordered pairings x 8 seeds = 288, self-play included."""

    pairings = build_evaluation_pairings()
    assert len(pairings) == 288
    assert len({(p["agent_a"], p["agent_b"]) for p in pairings}) == 36
    assert len({p["seed"] for p in pairings}) == 8
    self_play = [p for p in pairings if p["agent_a"] == p["agent_b"]]
    assert len(self_play) == 48
    # Every ordered pairing appears, in both slot orders.
    for a in R4_POPULATION_IDS:
        for b in R4_POPULATION_IDS:
            assert any(p["agent_a"] == a and p["agent_b"] == b for p in pairings)


def test_population_manifest_records_executed_declarations() -> None:
    """Phase 0's reach table was transcribed and wrong for all six agents.

    R4 Section C corrects that by generating the manifest from
    ``declare_processes()`` return values. This test pins the frozen values
    and the manifest's frozen match configuration.
    """

    manifest = build_population_manifest()
    assert manifest["ruleset_id"] == RULESET_ID == "bytefray-rules-4"
    assert manifest["arena_size"] == ARENA_SIZE == 512
    assert manifest["max_ticks"] == MAX_TICKS == 1000
    assert manifest["process_mortality"] is False
    assert manifest["objective_target_oracle"] is False
    assert manifest["corpus_shape"]["total_matches"] == 288

    by_id = {e["identifier"]: e for e in manifest["entrants"]}
    assert set(by_id) == set(R4_POPULATION_IDS)
    expected = {
        "v5r4_siege_regional": (1, [24]),
        "v5r4_recon_striker": (1, [40]),
        "v5r4_core_warden": (1, [12]),
        "v5r4_dual_operator": (2, [32, 12]),
        "v5r4_territory_expander": (1, [16]),
        "v4_quorum": (6, [256, 48, 12, 32, 32, 24]),
    }
    for identifier, (count, reaches) in expected.items():
        entrant = by_id[identifier]
        assert entrant["process_count"] == count, identifier
        assert [p["reach"] for p in entrant["processes"]] == reaches, identifier
        assert entrant["api_version"] == 2


def test_retained_canonical_member_is_the_unchanged_phase0_quorum() -> None:
    """``v4_quorum`` is retained, not imitated -- fingerprint must be Phase 0's."""

    fingerprints = population_fingerprints()
    assert (
        fingerprints["v4_quorum"]
        == "d220a58316c7afab1e5dbb719aa5965095b5e352ca442bab1ca109c45507ee64"
    )


def test_population_is_strategically_diverse_by_declaration() -> None:
    """Not six variants of one strategy (R4 charter Section 14)."""

    archetypes = {m["archetype"][0] for m in R4_POPULATION}
    assert len(archetypes) == len(R4_POPULATION)
    manifest = build_population_manifest()
    process_counts = {e["process_count"] for e in manifest["entrants"]}
    assert process_counts == {1, 2, 6}
    # Targeting mechanisms must differ, not just be reworded.
    targeting = {m["targeting"] for m in R4_POPULATION}
    assert len(targeting) == len(R4_POPULATION)
    defenses = {m["defense"] for m in R4_POPULATION}
    assert len(defenses) >= 4


def test_interpretation_gate_is_preregistered_against_phase0_values() -> None:
    """Thresholds must be stated as deltas from a measured Phase 0 baseline."""

    criteria = INTERPRETATION_GATE["criteria"]
    assert set(criteria) == {
        "C1_capture_rate",
        "C2_contacted_no_capture",
        "C3_timeout_rate",
        "C4_max_simultaneous_deficit",
        "C5_stagnation",
        "C6_diversity_of_winners",
    }
    for name, criterion in criteria.items():
        assert criterion["justification"].strip(), name
        assert "phase0_value" in criterion or "phase0_value_pct" in criterion, name
    # Phase 0's published headline figures, which the gate is anchored to.
    assert criteria["C1_capture_rate"]["phase0_value_pct"] == 39.58
    assert criteria["C3_timeout_rate"]["phase0_value_pct"] == 60.42
    assert "strong_population_confound" in INTERPRETATION_GATE["decision_rule"]


def test_r4_own_core_write_metric_separates_defenders_from_patrollers() -> None:
    """The one additive R4 analyzer field, measured on a real frozen match.

    R3 Section C.1 established that the bundled ``v4_local_defender`` writes
    exactly two addresses of its own core across a whole 1000-tick match.
    This asserts the metric reproduces that fact from Phase 0's frozen
    replay, so the field means what R4's defender gate assumes it means.
    """

    match_dir = (
        PHASE0_CORPUS
        / "stage1_replays"
        / "v4_concentrated_attacker__vs__v4_local_defender__seed_1"
    )
    if not (match_dir / "replay.jsonl").is_file():
        import pytest

        pytest.skip("frozen Phase 0 corpus not present in this checkout")

    analysis = analyze_match(match_dir / "replay.jsonl", match_dir / "result.json")
    # B is v4_local_defender: two own-core addresses, for a thousand ticks.
    assert analysis["distinct_own_core_cells_written"]["B"] == 2
    # A is the point-target attacker: it writes one address, none of its own.
    assert analysis["distinct_own_core_cells_written"]["A"] == 0
    assert analysis["unique_write_addresses"]["A"] == 1


def test_r4_own_core_write_metric_is_additive_to_published_phase0_fields() -> None:
    """Adding the field must not have changed anything Phase 0 published."""

    metrics_path = PHASE0_CORPUS / "stage1_metrics.jsonl"
    if not metrics_path.is_file():
        import pytest

        pytest.skip("frozen Phase 0 corpus not present in this checkout")

    rows = [
        json.loads(line)
        for line in metrics_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ][:12]
    for row in rows:
        match_dir = PHASE0_CORPUS / "stage1_replays" / row["match_label"]
        fresh = analyze_match(match_dir / "replay.jsonl", match_dir / "result.json")
        for key, value in row.items():
            if key in ("match_label", "agent_a", "agent_b"):
                continue
            assert json.loads(json.dumps(fresh[key])) == value, (
                row["match_label"],
                key,
            )
        assert "distinct_own_core_cells_written" in fresh
        assert "distinct_own_core_cells_written" not in row
