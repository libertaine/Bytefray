"""The V6 E6 post-hoc factorial audit (PA) tooling: ``tools/research/v6/e6_audit``.

docs/research/v6/V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md
Sec 6.1 and Sec 8.1. What is proven here:

* **Seat metrics with multiplicity (PA-2).** The re-implementation equals
  the frozen E4 ``pairing_seat_metrics`` and ``mirror_seat_metrics`` on
  random unique-seed data. A resampled seed multiset equals the same seeds
  written out with their repetitions, and hand-computed cases pin both formulas.
* **The estimands (PA-4 to PA-6).**
  - The interaction algebra, and control-against-control zero.
  - I_all over every unit and I_common_neutral over the units neutral under
    both controls only.
  - Strata that partition all 45 units by the controls alone.
  - PF-4 per arm, and resampling that is joint across conditions.
* **The decomposition (PA-3).** Every one of the 81 possible four-tuples of
  seat results maps to exactly one class, and the named patterns map as the
  review defines them.
* **The mechanism extractor (PA-7).** Checks, evasion, lockout and first
  detection, on rows in the stored telemetry format.
* **The runner.** It refuses to write under ``runs/``.
* **The frozen corpus, when it is present** (it is git-ignored). PA-1 pins
  and PA-2 identity hold, and the PACED–ADAPT outcome counts reproduce the
  review's Sec 4.2. Without the corpus these tests are skipped.
"""

from __future__ import annotations

import itertools
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e4.analyze_e4 import (
    make_field_run,
    mirror_seat_metrics,
    pairing_seat_metrics,
)
from tools.research.v6.e6 import family
from tools.research.v6.e6.telemetry import ROW_FIELDS
from tools.research.v6.e6_audit import corpus as corpus_mod
from tools.research.v6.e6_audit import decompose, estimands, mechanism, run_audit, seat
from tools.research.v6.e6_audit.corpus import CONDITIONS

A, B, TIE = harness.SEAT_A, harness.SEAT_B, harness.TIE
F = Fraction


# ---------------------------------------------------------------------------
# PA-2: seat metrics
# ---------------------------------------------------------------------------


def _cell(subject: str, opponent: str, orientation: str, seed: int, seat_result: str) -> dict[str, Any]:
    """A harness-format cell whose seat result is ``seat_result``."""

    seat_a = subject if orientation == harness.ORIENTATION_CANDIDATE_FIRST else opponent
    if seat_result == TIE:
        outcome = "tie"
    else:
        winner = seat_a if seat_result == A else (opponent if seat_a == subject else subject)
        outcome = "win" if winner == subject else "loss"
    return {"subject_id": subject, "opponent_id": opponent, "orientation": orientation, "seed": seed,
            "outcome": outcome, "status": "completed", "ticks_run": 1, "termination_reason": "tick_limit"}


def test_pairing_metrics_equal_the_frozen_e4_function_on_random_unique_seeds() -> None:
    rng = random.Random(7)
    for _trial in range(200):
        seeds = rng.sample(range(10_000), rng.randint(1, 12))
        results = [(rng.choice((A, B, TIE)), rng.choice((A, B, TIE))) for _ in seeds]
        cells = []
        for seed, (x_in_a, y_in_a) in zip(seeds, results, strict=True):
            cells.append(_cell("x", "y", harness.ORIENTATION_CANDIDATE_FIRST, seed, x_in_a))
            cells.append(_cell("y", "x", harness.ORIENTATION_CANDIDATE_FIRST, seed, y_in_a))
        frozen = pairing_seat_metrics(make_field_run("C", "F1", cells, {}), "x", "y")
        gsb, sdom = seat.pairing_metrics(results)
        assert (gsb, sdom) == (F(frozen["exact"]["gsb"]), F(frozen["exact"]["sdom"]))


def test_mirror_metrics_equal_the_frozen_e4_function_on_random_unique_seeds() -> None:
    rng = random.Random(11)
    for _trial in range(200):
        seeds = rng.sample(range(10_000), rng.randint(1, 12))
        results = [rng.choice((A, B, TIE)) for _ in seeds]
        cells = [_cell("p", "t", harness.ORIENTATION_CANDIDATE_FIRST, seed, r) for seed, r in zip(seeds, results, strict=True)]
        cells += [_cell("p", "t", harness.ORIENTATION_OPPONENT_FIRST, seed, r) for seed, r in zip(seeds, results, strict=True)]
        frozen = mirror_seat_metrics(make_field_run("C", "F2", cells, {}), "p", "t")
        assert seat.mirror_metrics(results) == (F(frozen["exact"]["gsb"]), F(frozen["exact"]["sdom"]))


def test_pairing_metrics_hand_cases() -> None:
    # The same member wins from either seat: every match decisive, no seat bias, no seat-determined seed.
    assert seat.pairing_metrics([(A, B)] * 32) == (F(0), F(0))
    # Seat A wins everything: fully seat-dominant.
    assert seat.pairing_metrics([(A, A)] * 32) == (F(1), F(1))
    # E6's PACED-ADAPT under T-E6: 30 of 32 captures from Seat A, 22 of 32 from Seat B, no ADAPT win.
    results = [(A, B)] * 20 + [(A, TIE)] * 10 + [(TIE, B)] * 2
    assert seat.pairing_metrics(results) == (F(1, 8), F(0))
    # Three consistent seeds (A, A, B) of four: SDI 3/4, p_A 2/3, SB 1/3, SDom 1/4; GSB (5 - 3) / 8.
    assert seat.pairing_metrics([(A, A), (A, A), (B, B), (A, B)]) == (F(1, 4), F(1, 4))


def test_mirror_metrics_hand_case() -> None:
    # A A B tie: GSB 1/4; decisive share 3/4, p_A 2/3, SB 1/3, SDom 1/4.
    assert seat.mirror_metrics([A, A, B, TIE]) == (F(1, 4), F(1, 4))
    assert seat.mirror_metrics([TIE, TIE]) == (F(0), F(0))


def test_a_resampled_multiset_equals_the_seeds_written_out() -> None:
    results = [(A, B), (A, A), (TIE, B), (B, B)]
    positions = [1, 1, 3, 0, 1]
    unit = "F1|e6_q01|e6_q06"
    assert seat.metrics(unit, results, positions) == seat.pairing_metrics([results[p] for p in positions])
    mirror = "F2|e6_q06|e6_q13"
    single = [A, TIE, B]
    assert seat.metrics(mirror, single, [2, 2, 0]) == seat.mirror_metrics([B, B, A])


def test_neutrality_is_closed_as_registered() -> None:
    assert seat.neutral(F(1, 10), F(0))
    assert not seat.neutral(F(7, 64), F(0))  # 7/64 > 1/10
    assert seat.neutral(F(6, 64), F(0))
    assert not seat.neutral(F(0), F(9, 10))
    assert seat.neutral(F(0), F(89, 100))


def test_the_45_frozen_units_in_the_frozen_key_format() -> None:
    keys = seat.unit_keys()
    assert len(keys) == 45 == len(set(keys))
    assert sum(k.startswith("F1|") for k in keys) == 36
    assert "F1|e6_q01|e6_q06" in keys  # PACED (primary) before ADAPT in family order
    assert seat.label("F1|e6_q01|e6_q06") == "F1|PACED|ADAPT"
    assert seat.label("F2|e6_q06|e6_q13") == "F2|ADAPT|ADAPT"
    assert sum(seat.contains_adapt(k) for k in keys) == 9


# ---------------------------------------------------------------------------
# PA-4 to PA-6: estimands
# ---------------------------------------------------------------------------


def _values(g: dict[str, dict[str, Fraction]]) -> estimands.Values:
    """Every unit given with SDom 0, so neutrality is decided by GSB alone."""

    return {c: {u: (g[c][u], F(0)) for u in g[c]} for c in CONDITIONS}


def test_the_unit_interaction_algebra() -> None:
    u = "F1|e6_q01|e6_q06"
    values = _values({"C-E6": {u: F(0)}, "T-E6": {u: F(1, 8)}, "C-E6L": {u: F(0)}, "T-E6L": {u: F(-1, 64)}})
    assert estimands.signed_interaction(values, u) == F(9, 64)
    assert estimands.unit_interaction(values, u) == F(7, 64)
    # A whole-tick control bias that sensing removes gives a negative |GSB| interaction (the floor at 0).
    values = _values({"C-E6": {u: F(31, 64)}, "T-E6": {u: F(-3, 64)}, "C-E6L": {u: F(0)}, "T-E6L": {u: F(0)}})
    assert estimands.unit_interaction(values, u) == F(-28, 64)


def _synthetic_results(rng: random.Random, seeds: int) -> dict[str, dict[str, list[Any]]]:
    out: dict[str, dict[str, list[Any]]] = {}
    for condition in CONDITIONS:
        out[condition] = {}
        for unit in seat.unit_keys():
            if unit.startswith("F1|"):
                out[condition][unit] = [(rng.choice((A, B, TIE)), rng.choice((A, B, TIE))) for _ in range(seeds)]
            else:
                out[condition][unit] = [rng.choice((A, B, TIE)) for _ in range(seeds)]
    return out


def test_control_against_control_gives_zero_for_every_estimand() -> None:
    rng = random.Random(3)
    base = _synthetic_results(rng, 8)
    results = {"C-E6": base["C-E6"], "T-E6": base["C-E6"], "C-E6L": base["C-E6L"], "T-E6L": base["C-E6L"]}
    point = estimands.values_at(results)
    sets = estimands.unit_sets(point)
    r = estimands.reading(point, sets)
    assert r["I_all"] == 0 and r["I_common_neutral"] == 0 and r["I_flag"] == 0
    assert r["pf4_primary"] == [] and r["pf4_companion"] == []


def test_i_all_uses_every_unit_and_i_common_neutral_only_the_units_neutral_under_both_controls() -> None:
    rng = random.Random(5)
    results = _synthetic_results(rng, 8)
    point = estimands.values_at(results)
    sets = estimands.unit_sets(point)
    assert sets["all"] == seat.unit_keys()
    expected_all = sum((estimands.unit_interaction(point, u) for u in seat.unit_keys()), F(0)) / 45
    assert estimands.reading(point, sets)["I_all"] == expected_all
    common = [u for u in seat.unit_keys()
              if estimands.is_neutral(point, "C-E6", u) and estimands.is_neutral(point, "C-E6L", u)]
    assert sets["common_neutral"] == common
    if common:
        expected_common = sum((estimands.unit_interaction(point, u) for u in common), F(0)) / len(common)
        assert estimands.reading(point, sets)["I_common_neutral"] == expected_common


def test_baseline_strata_partition_all_units_by_the_controls_alone() -> None:
    rng = random.Random(9)
    results = _synthetic_results(rng, 8)
    point = estimands.values_at(results)
    strata = estimands.baseline_strata(point)
    flat = [u for units in strata.values() for u in units]
    assert sorted(flat) == sorted(seat.unit_keys())
    # Changing only the treatments cannot move a unit between strata.
    shuffled = dict(results)
    shuffled["T-E6"], shuffled["T-E6L"] = results["T-E6L"], results["T-E6"]
    assert estimands.baseline_strata(estimands.values_at(shuffled)) == strata


def test_pf4_fires_only_on_a_unit_neutral_under_its_own_control() -> None:
    u, v = "F1|e6_q01|e6_q06", "F1|e6_q01|e6_q02"
    g = {"C-E6": {u: F(0), v: F(1, 2)}, "T-E6": {u: F(1, 8), v: F(1, 2)},
         "C-E6L": {u: F(0), v: F(0)}, "T-E6L": {u: F(0), v: F(0)}}
    values = _values(g)
    values = {c: {**{k: (F(0), F(0)) for k in seat.unit_keys()}, **values[c]} for c in CONDITIONS}
    assert estimands.pf4_units(values, estimands.PRIMARY_ARM) == [u]
    assert estimands.pf4_units(values, estimands.COMPANION_ARM) == []


def test_the_bootstrap_resamples_jointly_and_reads_the_registered_draws() -> None:
    draws = estimands.draws(32)
    assert len(draws) == 1000 and all(len(d) == 32 for d in draws)
    assert draws == estimands.payoff.resample_positions(32)
    rng = random.Random(13)
    results = _synthetic_results(rng, 32)
    point = estimands.values_at(results)
    sets = estimands.unit_sets(point)
    boot = estimands.bootstrap(results, sets, draws[:20], tracked=["F1|e6_q01|e6_q06"])
    assert boot["resamples"] == 20
    assert sum(boot["pf4_joint"].values()) == 20 == sum(boot["pf4_joint_non_adapt"].values())
    # Joint resampling: the identity draw reproduces the point reading exactly.
    identity = estimands.bootstrap(results, sets, [tuple(range(32))], tracked=[])
    r = estimands.reading(point, sets)
    assert identity["positive"]["all>0"] == ("1/1" if r["I_all"] > 0 else "0/1")


def test_meets_convention_is_the_9_10_bar() -> None:
    assert estimands.meets_convention("9/10") and estimands.meets_convention("967/1000")
    assert not estimands.meets_convention("899/1000") and not estimands.meets_convention(None)


# ---------------------------------------------------------------------------
# PA-3: decomposition
# ---------------------------------------------------------------------------


def test_every_four_tuple_maps_to_exactly_one_class() -> None:
    seen = []
    for combo in itertools.product((A, B, TIE), repeat=4):
        cls, sub = decompose.classify(dict(zip(CONDITIONS, combo, strict=True)))
        assert cls in decompose.CLASSES
        assert (sub is None) == (cls != decompose.INTERACTION)
        seen.append(cls)
    assert len(seen) == 81 and set(seen) == set(decompose.CLASSES)


def test_named_patterns_map_as_the_review_defines_them() -> None:
    def cls(c: str, t: str, cl: str, tl: str) -> tuple[str, str | None]:
        return decompose.classify({"C-E6": c, "T-E6": t, "C-E6L": cl, "T-E6L": tl})

    assert cls(A, A, A, A) == (decompose.INVARIANT, None)
    assert cls(A, B, A, B) == (decompose.SENSING_ONLY, None)
    assert cls(A, A, TIE, TIE) == (decompose.DISRUPTION_ONLY, None)
    # PACED-ADAPT with PACED in Seat B, tied under T-E6: both lambda-1 cells tie as well, so the
    # whole-tick control is the odd one out -- an interaction, since sensing changes the result
    # under whole-tick disruption and not under lambda = 1.
    assert cls(B, TIE, TIE, TIE) == (decompose.INTERACTION, "odd:C-E6")
    assert cls(B, TIE, B, B) == (decompose.INTERACTION, "odd:T-E6")
    assert cls(A, B, B, A) == (decompose.INTERACTION, "diagonal")


def test_every_cell_key_belongs_to_one_frozen_unit() -> None:
    order = decompose.seat_units_order()
    assert order[:9] == [family.package_id(m) for m in family.OPPONENTS]
    assert decompose.unit_of(("F1", "e6_q06", "e6_q01", "candidate_first", 5)) == "F1|e6_q01|e6_q06"
    assert decompose.unit_of(("F2", "e6_q06", "e6_q13", "opponent_first", 5)) == "F2|e6_q06|e6_q13"


# ---------------------------------------------------------------------------
# PA-7: the mechanism extractor, on rows in the stored telemetry format
# ---------------------------------------------------------------------------


def _row(tick: int, entrant: str, index: int, *, anchor: int = 0, visible: tuple[int, ...] = (), kind: str | None = "write",
         address: int | None = None, read_owner: str | None = None) -> list[Any]:
    fields = {"tick": tick, "entrant": entrant, "process": "main", "index": index, "anchor": anchor,
              "visible": list(visible), "kind": kind, "operand": address, "value": 1, "status": "APPLIED",
              "address": address, "read_value": None, "read_owner": read_owner}
    return [fields[name] for name in ROW_FIELDS]


def test_the_extractor_reads_lockout_checks_and_evasion() -> None:
    # Seat A is PACED (core 100), Seat B is ADAPT (core 300). A detects B at tick 1 and locks it
    # out of tick 1; B acts again at tick 2 (its first-mover tick), checks core cell 1 (own), sees A;
    # A-first tick 3 is silent for B; at tick 4 B checks cell 3, finds damage, and evades.
    rows = [
        _row(1, "B", 1, anchor=300, kind="read", address=300, read_owner="B"),
        _row(1, "B", 2, anchor=300, address=309),
        _row(1, "A", 1, anchor=100, kind="move", address=164),
        _row(1, "A", 2, anchor=164, visible=(300,), address=300),
        _row(2, "B", 1, anchor=300, visible=(236,), kind="read", address=301, read_owner="B"),
        _row(2, "B", 2, anchor=300, visible=(236,), address=236),
        _row(3, "A", 1, anchor=236, visible=(300,), address=300),
        _row(4, "B", 1, anchor=300, visible=(236,), kind="read", address=303, read_owner="A"),
        _row(4, "B", 2, anchor=300, visible=(236,), kind="move", address=340),
    ]
    cell = {"seat_a_id": family.package_id("PACED"), "seat_b_id": family.package_id("ADAPT"), "outcome": "tie",
            "subject_id": family.package_id("PACED"), "opponent_id": family.package_id("ADAPT"),
            "orientation": harness.ORIENTATION_CANDIDATE_FIRST, "termination_reason": "tick_limit", "ticks_run": 4}
    summary = {"arena": 512, "core_base": {"A": 100, "B": 300}}
    m = mechanism.cell_mechanics(cell, summary, rows)
    assert m.seats == {"A": "PACED", "B": "ADAPT"}
    assert m.first_detection == {"A": 1, "B": 2}
    assert m.saw_first == "A"
    assert m.first_callback_after_rival_detection == {"A": 3, "B": 2}
    assert m.silent_ticks_after_rival_detection["B"] == (3,)
    assert m.checks["B"] == (mechanism.Check(1, 0, False), mechanism.Check(2, 1, False), mechanism.Check(4, 3, True))
    assert m.evasion == {"B": 4}
    assert m.unclassified_early_moves == {"B": 0}
    assert m.first_off_core_move == {"A": 1, "B": 4}
    assert m.callbacks["B"] == {1: 2, 2: 2, 3: 0, 4: 2}


def test_a_move_that_follows_no_damaged_check_is_not_an_evasion() -> None:
    rows = [
        _row(1, "B", 1, anchor=300, kind="read", address=300, read_owner="B"),
        _row(1, "B", 2, anchor=300, kind="move", address=364),
    ]
    cell = {"seat_a_id": family.package_id("GREED"), "seat_b_id": family.package_id("ADAPT"), "outcome": "tie",
            "subject_id": family.package_id("GREED"), "opponent_id": family.package_id("ADAPT"),
            "orientation": harness.ORIENTATION_CANDIDATE_FIRST, "termination_reason": "tick_limit", "ticks_run": 1}
    m = mechanism.cell_mechanics(cell, {"arena": 512, "core_base": {"A": 100, "B": 300}}, rows)
    assert m.evasion == {"B": None}
    assert m.unclassified_early_moves == {"B": 1}


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------


def test_the_runner_refuses_to_write_under_runs(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run_audit.write({"x": 1}, corpus_mod.REPO_ROOT / "runs" / "pa_record.json")
    out = tmp_path / "record.json"
    run_audit.write({"b": 1, "a": F(1, 2).numerator}, out)
    assert out.read_bytes() == b'{\n "a": 1,\n "b": 1\n}\n'


# ---------------------------------------------------------------------------
# The frozen corpus (git-ignored; skipped when absent)
# ---------------------------------------------------------------------------

_CORPUS_PRESENT = (corpus_mod.REPO_ROOT / corpus_mod.CORPUS_ROOT / "records" / "e6_analysis.json").is_file()
needs_corpus = pytest.mark.skipif(not _CORPUS_PRESENT, reason="the git-ignored E6 corpus is not present")


@pytest.fixture(scope="module")
def frozen_corpus() -> corpus_mod.Corpus:
    corpus_mod.verify_pins()
    return corpus_mod.load_corpus()


@needs_corpus
def test_pa1_pins_and_pa2_identity_hold_on_the_frozen_corpus(frozen_corpus: corpus_mod.Corpus) -> None:
    results = {c: seat.per_seed_results(frozen_corpus.cells[c], frozen_corpus.seeds) for c in CONDITIONS}
    identity = seat.identity_check(results, corpus_mod.frozen_analysis())
    assert identity == {"compared": 180, "mismatches": [], "status": "PASS"}


@needs_corpus
def test_paced_adapt_outcomes_reproduce_the_review_sec_4_2(frozen_corpus: corpus_mod.Corpus) -> None:
    from tools.research.v6.e6_audit import review_values

    unit = "F1|e6_q01|e6_q06"
    for condition, expected in review_values.OUTCOMES.items():
        table = mechanism.unit_table(mechanism.mechanics_for(frozen_corpus, condition, unit))
        assert {seat_key: table[seat_key]["outcome_for_X"] for seat_key in ("X@A", "X@B")} == expected
