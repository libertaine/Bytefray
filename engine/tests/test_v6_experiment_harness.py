"""Tests for V6 experiment harness, provenance, and defensible metrics (Phases 7, 8, 9).

The Phase 9 metric tests below were updated for the E2 harness remediation
(docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec I.4): analysis
results are now grouped into seat-conditioned and per-seat/pooled tables,
the rating model reports separability instead of unstable ratings (HD-3),
and the bootstrap resamples distinct trajectories rather than seeds (HD-2).
Their original intent -- transitive vs cyclic fields, honest aggregation of
duplicated seeds -- is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.research.v6.experiment_harness import (
    ANALYZER_VERSION,
    E2_FIXTURE_SOURCE_DIR,
    HARNESS_ID,
    HARNESS_VERSION,
    TRACKED_BENCHMARK_SOURCE_DIRS,
    V6_BENCH_8,
    ResearchExperimentConfig,
    analyze_experiment_condition,
    bootstrap_rmsr_over_distinct_trajectories,
    find_tracked_agent_source,
    fingerprint_corpus,
    get_git_provenance,
    prepare_benchmark_data_root,
    run_experiment,
)


def test_tracked_benchmark_corpus_resolution_and_fingerprints(tmp_path: Path) -> None:
    """Proves all 8 agents of V6_BENCH_8 resolve from tracked repository contents."""
    for name in V6_BENCH_8:
        source = find_tracked_agent_source(name)
        assert source is not None, f"Benchmark agent {name!r} not found in tracked sources"
        assert source.is_dir()

    # Fingerprint corpus without needing local user agents/
    fps = fingerprint_corpus(V6_BENCH_8)
    assert len(fps) == 8
    for name in V6_BENCH_8:
        assert name in fps
        assert len(fps[name]["fingerprint"]) == 64
        assert fps[name]["agent_revision_id"].startswith("agent-revision_")

    # Octave fixture specifically
    octave_fp = fps["Octave"]["fingerprint"]
    assert octave_fp == "e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730"

    # Prepare data root
    dest = prepare_benchmark_data_root(tmp_path / "env", V6_BENCH_8)
    assert (dest / "agents" / "Octave" / "agent.py").is_file()
    assert (dest / "agents" / "v4_claimer" / "agent.py").is_file()


def test_provenance_metadata_structure() -> None:
    prov = get_git_provenance()
    assert "git_sha" in prov
    assert "git_dirty" in prov
    assert isinstance(prov["git_dirty"], bool)
    assert "python_version" in prov
    assert "platform" in prov
    assert "timestamp_utc" in prov
    assert prov["timestamp_utc"].endswith("Z")


def test_metrics_distinguish_transitive_from_cyclic_matchups() -> None:
    """Phase 9: Prove that 1D transitive rankings produce low RMSR,

    while cyclic matchups produce high RMSR and detect 3-cycles.
    """
    field = ["Rock", "Paper", "Scissors"]

    # 1. Cyclic RPS scenario: Rock beats Scissors, Scissors beats Paper, Paper beats Rock
    # Rock vs Paper: 0 wins for Rock, 10 wins for Paper
    # Paper vs Scissors: 0 wins for Paper, 10 wins for Scissors
    # Scissors vs Rock: 0 wins for Scissors, 10 wins for Rock
    cyclic_cells = []
    for _ in range(10):
        cyclic_cells.append({"subject_id": "Rock", "opponent_id": "Paper", "outcome": "loss", "ticks_run": 50, "orientation": "candidate_first"})
        cyclic_cells.append({"subject_id": "Paper", "opponent_id": "Scissors", "outcome": "loss", "ticks_run": 50, "orientation": "candidate_first"})
        cyclic_cells.append({"subject_id": "Scissors", "opponent_id": "Rock", "outcome": "loss", "ticks_run": 50, "orientation": "candidate_first"})

    analysis_cyclic = analyze_experiment_condition(cyclic_cells, field)["tables"]["pooled"]
    # Directed 3-cycle detected!
    assert analysis_cyclic["cycle_count"] >= 1
    assert analysis_cyclic["robust_cycle_count"] >= 1
    # Matchup RMSR must be large because 1D model predicts 50% for all equal entrants
    assert analysis_cyclic["rmsr"] > 0.4

    # 2. Purely transitive scenario: A beats B (100%), B beats C (100%), A beats C (100%)
    field_transitive = ["A", "B", "C"]
    transitive_cells = []
    for _ in range(10):
        transitive_cells.append({"subject_id": "A", "opponent_id": "B", "outcome": "win", "ticks_run": 20, "orientation": "candidate_first"})
        transitive_cells.append({"subject_id": "B", "opponent_id": "C", "outcome": "win", "ticks_run": 20, "orientation": "candidate_first"})
        transitive_cells.append({"subject_id": "A", "opponent_id": "C", "outcome": "win", "ticks_run": 20, "orientation": "candidate_first"})

    analysis_transitive = analyze_experiment_condition(transitive_cells, field_transitive)["tables"]["pooled"]
    # Zero cycles!
    assert analysis_transitive["cycle_count"] == 0
    assert len(analysis_transitive["upset_reversals"]) == 0
    # The hierarchy A > B > C is reported as an ordering: a clean blowout is
    # separable, so no finite ratings are presented as authoritative (HD-3).
    fit = analysis_transitive["bradley_terry"]
    assert fit["components"] == [["A"], ["B"], ["C"]]
    assert fit["separable"] is True and fit["ratings"] is None
    assert analysis_transitive["ratings_authoritative"] is False
    # Transitive model fits cleanly with low RMSR (< 0.10)
    assert analysis_transitive["rmsr"] < 0.10


def test_seed_honest_aggregation_and_bootstrapping() -> None:
    """Duplicate matches with identical outcomes are one distinct trajectory
    (HD-2), not independent evidence, and the bootstrap resamples distinct
    trajectories.
    """
    field = ["A", "B"]
    # 5 runs on seed 1 (all wins for A)
    # 5 runs on seed 2 (all losses for A)
    cells = []
    for _ in range(5):
        cells.append({"subject_id": "A", "opponent_id": "B", "outcome": "win", "seed": 1, "orientation": "candidate_first"})
    for _ in range(5):
        cells.append({"subject_id": "A", "opponent_id": "B", "outcome": "loss", "seed": 2, "orientation": "candidate_first"})

    analysis = analyze_experiment_condition(cells, field)
    # Two distinct trajectories, one each way: ratings are identical.
    assert analysis["effective_sample"]["n_distinct"] == 2
    ratings = analysis["tables"]["pooled"]["bradley_terry"]["ratings"]
    assert ratings["A"] == ratings["B"]
    boot = bootstrap_rmsr_over_distinct_trajectories(cells, field, n_bootstraps=20)
    assert boot["status"] == "estimated"
    assert isinstance(boot["se"], float)
    assert boot["se"] >= 0.0
    assert boot["n_distinct"] == 2


def test_e2_fixture_directory_is_a_tracked_benchmark_source() -> None:
    assert E2_FIXTURE_SOURCE_DIR in TRACKED_BENCHMARK_SOURCE_DIRS
    assert find_tracked_agent_source("e2_sniper") == E2_FIXTURE_SOURCE_DIR / "e2_sniper"


def test_smoke_experiment_runner(tmp_path: Path) -> None:
    """Run a real 2-agent smoke experiment via run_experiment and verify output."""
    out_dir = tmp_path / "exp_run"
    config = ResearchExperimentConfig(
        experiment_id="test_smoke",
        arena_sizes=(512,),
        field=("v4_claimer", "v5_core_defender"),
        seeds=(1,),
        ticks=20,
        both_orientations=False,
        output_dir=out_dir,
        provenance_extra={"frozen_definition": "smoke"},
    )
    result = run_experiment(config)

    assert (out_dir / "provenance.json").is_file()
    assert (out_dir / "experiment_result.json").is_file()

    prov = json.loads((out_dir / "provenance.json").read_text(encoding="utf-8"))
    assert prov["experiment_id"] == "test_smoke"
    assert "git_sha" in prov
    assert "v4_claimer" in prov["agent_fingerprints"]
    assert (prov["harness_id"], prov["harness_version"], prov["analyzer_version"]) == (
        HARNESS_ID,
        HARNESS_VERSION,
        ANALYZER_VERSION,
    )
    assert prov["frozen_definition"] == "smoke"
    assert prov["config"]["pairing"] == "triangular"
    assert prov["config"]["pairs"] == [["v4_claimer", "v5_core_defender"]]

    cond = result["conditions"][0]
    assert cond["arena_size"] == 512
    assert len(cond["cells"]) == 1
    only = cond["cells"][0]
    assert only["subject_id"] == "v4_claimer"
    assert only["opponent_id"] == "v5_core_defender"
    # Termination reason must be recorded from match execution
    assert only["termination_reason"] == "tick_limit"
    # Seat annotation: candidate_first puts the subject in Seat A.
    assert (only["seat_a_id"], only["seat_b_id"]) == ("v4_claimer", "v5_core_defender")
    assert only["entrant_terminations"] == {"A": None, "B": None}
    assert (out_dir / only["artifact_dir"] / "replay.jsonl").is_file()
