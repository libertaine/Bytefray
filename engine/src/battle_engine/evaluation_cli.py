"""``bytefray agents evaluate <candidate-id>`` -- command-line parsing,
input resolution, and result presentation.

This module owns everything about *running and presenting* an evaluation
from the command line: argument parsing, preset/explicit-override
precedence, dry-run and live output (both the human-readable text summary
and the ``--json`` structured form), and the methodology-disclosure lines
Designer's own history views reuse. It coordinates an evaluation by calling
``battle_engine.evaluation_service.EvaluationService`` directly -- it does
not reimplement orchestration, and lower layers (contracts, identity,
planning, cell execution, the worker, the artifact) remain unaware this
module exists. See ``docs/specs/agent_evaluation.md`` for the full design
rationale.

``battle_engine.agent_evaluation`` re-exports this module's ``main`` (and a
handful of other CLI/Designer-facing helpers) as a permanent compatibility
facade; nothing here imports that facade back.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from battle_engine.agent_test import DEFAULT_TICKS
from battle_engine.config import Config
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE,
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_MODE_BOTH,
    ORIENTATION_OPPONENT_FIRST,
    STANDARD_V4_ARENA_SIZE,
    STANDARD_V4_SEEDS,
    ComparisonEntry,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationRequest,
    EvaluationResult,
    SubjectAggregate,
    resolved_arena_alignment_mode,
)
from battle_engine.evaluation_planning import (
    build_matrix,
    enumerate_seat_assignments,
    standard_layouts,
    standard_placements,
)
from battle_engine.evaluation_presets import (
    ORIENTATION_BOTH as _PRESET_ORIENTATION_BOTH,
)
from battle_engine.evaluation_presets import (
    EvaluationPreset,
    EvaluationPresetError,
    load_preset,
)
from battle_engine.evaluation_service import EvaluationService
from battle_engine.paths import get_data_root
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)


def rerun_command(
    subject_id: str,
    opponent_id: str,
    seed: int,
    ticks: int,
    orientation: str = ORIENTATION_CANDIDATE_FIRST,
) -> str:
    """The exact ``agents test`` invocation that reproduces one cell (Sec 8/10).

    v0.9 Phase 6 (Phase 5 spec Sec H.1): an ``opponent_first`` cell's real
    physical match ran with roles swapped
    (``test_agent(opponent_id, opponent=subject_id, ...)``) -- the printed
    command mirrors that exactly, so it reproduces the cell byte for byte
    rather than silently reproducing the opposite orientation.
    """

    if orientation == ORIENTATION_OPPONENT_FIRST:
        first_id, second_id = opponent_id, subject_id
    else:
        first_id, second_id = subject_id, opponent_id
    return f"bytefray agents test {first_id} --opponent {second_id} --seed {seed} --ticks {ticks}"


# ---------------------------------------------------------------------------
# Seed/opponent parsing shared by the CLI and Designer (Sec 12/13)
# ---------------------------------------------------------------------------


def parse_opponents(text: str) -> tuple[str, ...]:
    opponents = tuple(chunk.strip() for chunk in text.split(",") if chunk.strip())
    if not opponents:
        raise EvaluationConfigurationError("--opponents requires at least one agent id.")
    return opponents


def parse_seed_list(text: str) -> tuple[int, ...]:
    seeds: list[int] = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            seeds.append(int(chunk))
        except ValueError as exc:
            raise EvaluationConfigurationError(f"Invalid seed value {chunk!r}.") from exc
    if not seeds:
        raise EvaluationConfigurationError("--seeds requires at least one seed.")
    return tuple(seeds)


def parse_seed_range(text: str) -> tuple[int, ...]:
    start_text, sep, end_text = text.partition(":")
    if not sep:
        raise EvaluationConfigurationError(
            f"--seed-range must be START:END, got {text!r}."
        )
    try:
        start, end = int(start_text.strip()), int(end_text.strip())
    except ValueError as exc:
        raise EvaluationConfigurationError(
            f"--seed-range values must be integers, got {text!r}."
        ) from exc
    if end < start:
        raise EvaluationConfigurationError(
            f"--seed-range end must be >= start, got {text!r}."
        )
    return tuple(range(start, end + 1))


def _default_output_dir(root: Path, evaluation_id: str) -> Path:
    return root / "runs" / "evaluations" / evaluation_id


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bytefray agents evaluate",
        description=(
            "Run a deterministic Python-agent evaluation matrix: a candidate "
            "(and optional baseline) against explicit opponents and seeds, "
            "through the exact 'bytefray agents test' execution boundary. "
            "See docs/specs/agent_evaluation.md."
        ),
    )
    parser.add_argument(
        "candidate_id",
        nargs="?",
        default=None,
        help="candidate agent's discovery id (may instead be set by --preset)",
    )
    parser.add_argument(
        "--preset",
        default=None,
        help=(
            "name of a bytefray.evaluation_preset (see 'bytefray agents "
            "evaluation-presets') supplying default values for any option not "
            "explicitly given below; an explicit option always overrides the "
            "preset. Never affects evaluation_id or any per-cell result -- see "
            "docs/V1_6_PHASE3_EVALUATION_PRESETS.md."
        ),
    )
    parser.add_argument(
        "--baseline", default=None, help="baseline agent's discovery id to compare against"
    )
    parser.add_argument(
        "--ruleset",
        choices=[BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID],
        default=None,
        help=(
            f"gameplay Ruleset identity. {BYTEFRAY_RULESET_V4_ID} is selected "
            "automatically when this flag is omitted (and no --preset "
            f"supplies one). {BYTEFRAY_RULESET_V4_ID} runs Agent API v2 "
            "process entrants through the same production match service "
            "under the stable v4 seeded-placement methodology: arena pinned "
            f"to {STANDARD_V4_ARENA_SIZE}, {len(STANDARD_V4_SEEDS)} "
            "deterministic placement samples by default, both orientations "
            "paired over the same seat-bound geometry. See "
            "docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md and "
            f"docs/research/v4/V4_RC1_PHASE1_EVALUATION_METHODOLOGY.md. "
            f"{BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID} is the V6 Phase 4B "
            "variable-arena research identity: behaviorally identical to "
            f"{BYTEFRAY_RULESET_V4_ID} (same scheduler, seeded placement, "
            "process selection, scoring, quota, and termination), but "
            "--arena-size may be set to any value in the Phase 4A research "
            "range instead of being pinned to the stable-v4 control arena. "
            "Not selected automatically for any request; must be named "
            "explicitly. See "
            "docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md."
        ),
    )
    parser.add_argument(
        "--opponents",
        default=None,
        help="comma-separated opponent discovery ids (may instead be set by --preset)",
    )
    parser.add_argument(
        "--group",
        action="store_true",
        help=(
            "retired compatibility flag: new group evaluations can no longer be "
            "created because their Ruleset 2 methodology is retired; historical "
            "group artifacts remain readable"
        ),
    )
    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument("--seeds", default=None, help="comma-separated explicit seeds")
    seed_group.add_argument(
        "--seed-range", default=None, help="inclusive seed range START:END"
    )
    parser.add_argument(
        "--ticks",
        type=_positive_int,
        default=None,
        help=f"tick budget per cell (default: {DEFAULT_TICKS}, unless set by --preset)",
    )
    parser.add_argument(
        "--arena-size",
        type=_positive_int,
        default=None,
        help=(
            f"arena size in cells (default: {Config().arena_size}, unless set by "
            "--preset). A controlled experimental variable: it changes the standard "
            "placement/layout coordinates (which are fractions of arena size) and "
            "therefore the evaluation_id, but is NOT a Ruleset change. See "
            "docs/V3_PHASE0_RESEARCH_BASELINE.md."
        ),
    )
    parser.add_argument(
        "--instr-per-tick",
        type=_positive_int,
        default=None,
        help=(
            f"per-entrant action budget per tick (default: {Config().instr_per_tick}, "
            "unless set by --preset). A controlled experimental variable, not a "
            "Ruleset change -- see docs/V3_PHASE0_RESEARCH_BASELINE.md."
        ),
    )
    parser.add_argument(
        "--kill-weight",
        type=float,
        default=None,
        help=(
            f"score awarded per attributed core capture (default: {Config().weights.kill}). "
            "A controlled experimental variable, per-match configuration rather than a "
            "Ruleset change -- see docs/V3_PHASE3_OFFENSE_PAYOFF_CHARACTERIZATION.md."
        ),
    )
    parser.add_argument("--output", type=Path, default=None, help="evaluation artifact directory")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the matrix and exit without running anything"
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "print the result as JSON instead of the human-readable summary -- the same "
            "analysis/behavior/capture/group_analysis structure 'bytefray agents "
            "evaluations show --json' produces, over the artifact this run just wrote, so "
            "no second command is needed to get structured output for a run just executed. "
            "Replaces the human summary entirely (never mixed with it); --quiet still "
            "suppresses it. See docs/V3_PRODUCT_SCOPE.md Phase 3."
        ),
    )
    orientation_group = parser.add_mutually_exclusive_group()
    orientation_group.add_argument(
        "--single-orientation",
        action="store_true",
        default=None,
        help=(
            "opt out of the both-entrant-orientations methodology; candidate_first "
            "only, matching pre-v0.9 behavior and matrix size. Overrides --preset. "
            "Does not generalize across entrant order -- see docs/AGENT_LAB.md."
        ),
    )
    orientation_group.add_argument(
        "--both-orientations",
        action="store_true",
        default=None,
        help=(
            "force the both-entrant-orientations methodology, overriding a "
            "--preset that requested single-orientation. Redundant with the "
            "ordinary default when no --preset is given."
        ),
    )
    parser.add_argument(
        "--workers",
        type=_positive_int,
        default=1,
        help=(
            "number of evaluation cells to execute concurrently, via a pool of "
            "long-lived worker subprocesses (default: 1, serial). Never affects "
            "evaluation_id or any per-cell result -- only wall-clock speed. Never "
            "settable by --preset -- execution machinery, not experiment content. "
            "See docs/V1_6_PHASE2_PARALLEL_EVALUATION.md."
        ),
    )
    return parser


def _resolve_seeds(args: argparse.Namespace) -> tuple[int, ...]:
    if args.seeds is not None:
        return parse_seed_list(args.seeds)
    if args.seed_range is not None:
        return parse_seed_range(args.seed_range)
    return (Config().seed,)


def methodology_lines(
    orientation_mode: str, *, arena_alignment_mode: str = EVALUATION_ARENA_ALIGNMENT_MODE
) -> tuple[str, str]:
    """Shared human-readable methodology disclosure (Phase 5 spec Sec O.1/AA.5).

    Takes the same ``orientation_mode`` string vocabulary
    (``ORIENTATION_MODE_BOTH``/``ORIENTATION_MODE_CANDIDATE_FIRST_ONLY``)
    identity/provenance already use, rather than a bare bool, so both the
    live-run CLI (``request.orientation_mode``) and the historical-read
    path (``evaluation_history``'s recovered/recorded
    ``EvaluationSummary.orientation_mode.value``) can call this one shared
    function -- never two independently authored copies of the same
    wording (Designer reuses it too, via
    ``app.services.designer_workflows``). Must never describe a
    both-orientations evaluation as "fully unbiased"/"fully robust": it
    discloses entrant-orientation coverage and, separately, that arena
    alignment is always fixed in v0.9 (translation robustness is not
    evaluated -- Sec AA.1/AA.2).
    """

    orientation_line = (
        "Entrant orientation: both"
        if orientation_mode == ORIENTATION_MODE_BOTH
        else (
            "Entrant orientation: candidate-first only -- does not generalize "
            "across entrant order"
        )
    )
    alignment_line = (
        f"Arena alignment: {arena_alignment_mode} -- translation robustness not evaluated"
    )
    return orientation_line, alignment_line


def _print_v2_methodology(request: EvaluationRequest, matrix: Sequence[EvaluationCell]) -> None:
    """Phase 1S: make an expanded v2 matrix's size/conditions obvious up front.

    Never left to be inferred from a final win rate -- a permanent-v2
    evaluation multiplies every opponent's cell count by
    ``len(standard_placements()) * (2 if both_orientations else 1)``, which
    a user must see stated plainly, not reverse-engineer from ``matches:``.
    """

    print(f"ruleset: {request.resolved_rules_compatibility_id}")
    print(f"seeds: {', '.join(str(seed) for seed in request.seeds)}")
    if request.group:
        _print_group_methodology(request)
        return
    placements = standard_placements(request.resolved_arena_size)
    orientations = 2 if request.both_orientations else 1
    cells_per_opponent = len(request.seeds) * len(placements) * orientations
    print(f"placements: {len(placements)} ({', '.join(p.placement_id for p in placements)})")
    print(f"scheduler orders: {'balanced' if request.both_orientations else 'candidate-first only'}")
    print(f"cells/opponent: {cells_per_opponent}")


def _print_group_methodology(request: EvaluationRequest) -> None:
    """v2.0.0-beta2 Phase 2: multi-entrant matrix disclosure, mirroring
    the 1v1 disclosure above exactly -- ruleset/seeds are already printed
    by the caller; roster/layout/permutation/cell-count are this mode's
    own additional dimensions.
    """

    roster = request.roster_agent_ids
    layouts = standard_layouts(len(roster), request.resolved_arena_size)
    seat_assignments = enumerate_seat_assignments(roster)
    cells = len(request.seeds) * len(layouts) * len(seat_assignments)
    print(f"roster: {', '.join(roster)} ({len(roster)} entrants)")
    print(f"layouts: {len(layouts)} ({', '.join(layout.layout_id for layout in layouts)})")
    print(f"seat assignments: {len(seat_assignments)}")
    print(f"cells: {cells}")


def _print_experimental_conditions(request: EvaluationRequest) -> None:
    """Disclose any non-default v3 Phase 0 experimental condition.

    Prints nothing at all when both are at their ordinary defaults, so
    every existing evaluation's human-readable output is unchanged
    character-for-character.
    """

    defaults = Config()
    if request.resolved_arena_size != defaults.arena_size:
        print(f"arena size: {request.resolved_arena_size} (non-default)")
    if request.resolved_instr_per_tick != defaults.instr_per_tick:
        print(f"action budget/tick: {request.resolved_instr_per_tick} (non-default)")
    if request.resolved_kill_weight != defaults.weights.kill:
        print(f"kill weight: {request.resolved_kill_weight} (non-default)")
    # v3 Phase 2: only ever non-None for the experimental locality Ruleset,
    # so this line is absent from every non-locality evaluation's output.
    if request.resolved_locality_reach is not None:
        print(
            f"locality reach: {request.resolved_locality_reach} "
            "(EXPERIMENTAL bounded locality)"
        )


def _print_matrix(
    request: EvaluationRequest,
    matrix: Sequence[EvaluationCell],
    preset: EvaluationPreset | None = None,
) -> None:
    if preset is not None:
        print(f"preset: {preset.name}  (content_digest={preset.content_digest})")
    print(f"candidate: {request.candidate_id}")
    print(f"baseline: {request.baseline_id if request.baseline_id else 'none'}")
    print(f"opponents: {', '.join(request.opponent_ids)}")
    if request.is_v2_methodology:
        _print_v2_methodology(request, matrix)
    else:
        print(f"seeds: {', '.join(str(seed) for seed in request.seeds)}")
    print(f"ticks: {request.ticks}")
    # v3 Phase 0D: disclose the two controlled experimental variables
    # whenever they are NOT at their ordinary defaults. Printed
    # unconditionally would add two noise lines to every ordinary
    # evaluation's output; omitted when non-default, a reader would have no
    # way to tell a 1024-cell arena run from a 4096-cell one -- exactly the
    # "omission would be misleading" case. Same conditional-disclosure
    # discipline `preset:` above already uses.
    _print_experimental_conditions(request)
    # v2.0.0-beta2 Phase 2: "subjects: N opponents: M" and the 2-value
    # "Entrant orientation: both/candidate-first only" line both describe
    # 1v1 methodology's own axes (subject_role, orientation) -- neither is
    # a meaningful description of a group evaluation's roster/seat-
    # assignment axes, and printing them anyway would misrepresent group
    # semantics as if a 2-value orientation were still the scheduler-order
    # axis (Phase 2 design-audit finding). `_print_group_methodology`
    # already discloses roster/layouts/seat assignments above; only the
    # arena-alignment line (still correct and useful for group -- it names
    # the resolved group methodology identifier) is kept.
    if not request.group:
        subjects = [request.candidate_id] + ([request.baseline_id] if request.baseline_id else [])
        print(f"subjects: {len(subjects)}  opponents: {len(request.opponent_ids)}  seeds: {len(request.seeds)}")
    print(f"matches: {len(matrix)}")
    _, alignment_line = methodology_lines(
        request.orientation_mode,
        arena_alignment_mode=resolved_arena_alignment_mode(
            request.is_v2_methodology,
            request.group,
            request.is_v4_methodology,
            request.is_v6_research_scale_methodology,
        ),
    )
    if not request.group:
        orientation_line, _ = methodology_lines(request.orientation_mode)
        print(orientation_line)
    print(alignment_line)


def _matrix_to_json(
    request: EvaluationRequest, matrix: Sequence[EvaluationCell], preset: EvaluationPreset | None
) -> dict[str, Any]:
    """v3.0 Phase 3: ``--dry-run --json``'s structured counterpart to
    ``_print_matrix`` -- kept a minimal preview (no cells enumerated), since
    the matrix itself is already fully described by ``request``/its size.
    """

    return {
        "preset": preset.name if preset is not None else None,
        "candidate_id": request.candidate_id,
        "baseline_id": request.baseline_id,
        "opponent_ids": list(request.opponent_ids),
        "seeds": list(request.seeds),
        "ticks": request.ticks,
        "matrix_size": len(matrix),
        "group": request.group,
        "orientation_mode": request.orientation_mode,
        "arena_alignment_mode": resolved_arena_alignment_mode(
            request.is_v2_methodology,
            request.group,
            request.is_v4_methodology,
            request.is_v6_research_scale_methodology,
            request.is_v6_research_scale_move_methodology,
        ),
    }


def _result_to_json(result: EvaluationResult, request: EvaluationRequest) -> dict[str, Any]:
    """v3.0 Phase 3: the live ``agents evaluate`` command's structured-output
    counterpart to ``evaluations show --json`` -- the same top-level
    ``analysis``/``behavior``/``capture``/``group_analysis`` keys, computed
    the identical way ``_print_result`` computes them for its own text
    presentation, layered onto the artifact this run just wrote (read back
    from ``result.state_path`` rather than re-derived, so this can never
    drift from what was actually persisted). No second command is needed to
    get structured output for a run just executed.
    """

    data: dict[str, Any] = json.loads(result.state_path.read_text(encoding="utf-8"))

    analysis = None
    if request.baseline_id is not None:
        from battle_engine.evaluation_analysis import analyze as _analyze_evaluation

        analysis = _analyze_evaluation(request.candidate_id, request.baseline_id, result.cells)
    data["analysis"] = analysis.to_json() if analysis is not None else None

    behavior = None
    capture = None
    group_analysis = None
    if request.group:
        from battle_engine.evaluation_group_analysis import (
            analyze_group,
            group_cell_ref_from_evaluation_cell,
        )

        group_scored_refs = [
            group_cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored
        ]
        if group_scored_refs:
            group_analysis = analyze_group(request.roster_agent_ids, group_scored_refs)
    else:
        from battle_engine.evaluation_behavior import (
            analyze_behavior,
            cell_ref_from_evaluation_cell,
        )

        scored_refs = [cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
        behavior = analyze_behavior(request.candidate_id, request.baseline_id, scored_refs)
        if request.is_v2_methodology:
            from battle_engine.evaluation_capture import analyze_capture

            capture = analyze_capture(request.candidate_id, request.baseline_id, scored_refs)

    data["behavior"] = behavior.to_json() if behavior is not None else None
    data["capture"] = capture.to_json() if capture is not None else None
    data["group_analysis"] = group_analysis.to_json() if group_analysis is not None else None
    return data


def _fmt_optional_g(value: float | None) -> str:
    return f"{value:g}" if value is not None else "n/a (group)"


def _fmt_optional_pct2(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "n/a (group)"


def _print_aggregate(aggregate: SubjectAggregate) -> None:
    print(f"[{aggregate.subject_role}] {aggregate.subject_id}")
    print(f"  win rate: {aggregate.win_rate_display}")
    print(
        f"  wins={aggregate.wins} losses={aggregate.losses} ties={aggregate.ties} "
        f"played={aggregate.matches_played}"
    )
    print(
        f"  score_avg={aggregate.score_avg:g} "
        f"score_differential_avg={_fmt_optional_g(aggregate.score_differential_avg)} "
        f"ticks_avg={aggregate.ticks_avg:g}"
    )
    print(
        f"  territory_avg={aggregate.territory_avg:.2f}% "
        f"territory_differential_avg={_fmt_optional_pct2(aggregate.territory_differential_avg)}"
    )
    if aggregate.subject_init_failures or aggregate.opponent_init_failures or aggregate.failed:
        print(
            f"  subject_init_failed={aggregate.subject_init_failures} "
            f"opponent_init_failed={aggregate.opponent_init_failures} failed={aggregate.failed}"
        )


def _print_orientation_breakdown(subject_aggregates: Sequence[SubjectAggregate]) -> None:
    """K.2: a compact per-orientation win-rate line alongside the pooled block.

    Never averages an orientation split away -- printed only alongside the
    pooled aggregate, so a regression hidden by pooling (candidate wins
    every candidate-first cell but loses every opponent-first cell) stays
    visible in the ordinary, non-verbose CLI output.
    """

    candidate_first = next(
        (a for a in subject_aggregates if a.orientation_scope == ORIENTATION_CANDIDATE_FIRST), None
    )
    opponent_first = next(
        (a for a in subject_aggregates if a.orientation_scope == ORIENTATION_OPPONENT_FIRST), None
    )
    if candidate_first is not None and opponent_first is not None:
        print(
            f"  candidate_first: {candidate_first.win_rate_display}   "
            f"opponent_first: {opponent_first.win_rate_display}"
        )


def _print_comparison_entry(entry: ComparisonEntry, ticks: int) -> None:
    placement_suffix = f" placement={entry.placement_id}" if entry.placement_id != "fixed" else ""
    print(
        f"  opponent={entry.opponent_id} seed={entry.seed} orientation={entry.orientation}"
        f"{placement_suffix}"
    )
    print(f"    candidate: {entry.candidate_outcome}  baseline: {entry.baseline_outcome}")
    if entry.reason:
        print(f"    reason: {entry.reason}")
    if entry.candidate_score is not None and entry.baseline_score is not None:
        print(f"    score: candidate={entry.candidate_score:g} baseline={entry.baseline_score:g}")
    print(
        "    rerun candidate: "
        f"{rerun_command('<candidate>', entry.opponent_id, entry.seed, ticks, entry.orientation)}"
    )
    if entry.baseline_outcome is not None:
        print(
            "    rerun baseline:  "
            f"{rerun_command('<baseline>', entry.opponent_id, entry.seed, ticks, entry.orientation)}"
        )


def _print_evidence(analysis: Any) -> None:
    """v1.6 Phase 4 (docs/V1_6_PHASE4_EVALUATION_ANALYSIS.md Sec 12): a
    concise Wilson-interval + exact paired evidence block -- magnitude and
    sample size shown before any p-value, never a bare
    SIGNIFICANT/NOT SIGNIFICANT verdict. ``analysis`` is an
    ``evaluation_analysis.EvaluationAnalysis``, typed as ``Any`` here only
    to avoid a top-level circular import (``evaluation_analysis`` imports
    from this module); see the deferred import at each call site.
    """

    from battle_engine.evaluation_analysis import EvidenceState

    def _rate_line(label: str, estimate: Any) -> str:
        interval = estimate.win_interval
        if interval is None:
            return f"  {label}: insufficient data (0 scored matches)"
        pct = 100.0 * (estimate.observed_win_rate or 0.0)
        return (
            f"  {label}: {estimate.wins}/{estimate.matches_played} ({pct:.0f}%)  "
            f"{round(interval.confidence_level * 100)}% CI "
            f"[{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]"
        )

    print("evidence:")
    print(_rate_line(f"candidate ({analysis.candidate_id})", analysis.candidate_overall))
    if analysis.baseline_overall is not None:
        print(_rate_line(f"baseline ({analysis.baseline_id})", analysis.baseline_overall))
    paired = analysis.overall_paired
    if paired is not None:
        if paired.state == EvidenceState.NO_MATCHED_CONDITIONS:
            print("  paired: no matched candidate/baseline conditions")
        elif paired.state == EvidenceState.NO_DISCORDANT_PAIRS:
            print(
                f"  paired: {paired.paired_count} matched conditions, no discordant pairs "
                "(all unchanged/inconclusive) -- interval/exact test not meaningful"
            )
        else:
            interval = paired.better_interval
            assert interval is not None and paired.exact_p_value is not None
            print(
                f"  paired: candidate better in {paired.improved}/{paired.discordant} discordant "
                f"conditions ({100.0 * (paired.better_proportion_of_discordant or 0.0):.0f}%)  "
                f"{round(interval.confidence_level * 100)}% CI "
                f"[{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]  "
                f"exact two-sided p={paired.exact_p_value:.3g}"
            )
        print(f"  {analysis.opponent_consistency}")
        print(f"  {analysis.orientation_consistency}")


def _fmt_fraction_pct(value: float | None) -> str:
    return f"{100.0 * value:.0f}%" if value is not None else "n/a"


def _fmt_percent(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "n/a"


def _fmt_rate(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def _print_behavior(analysis: Any) -> None:
    """v1.6 Phase 5 (docs/V1_6_PHASE5_BEHAVIOR_ANALYSIS.md Sec 18): a concise
    behavior-profile block -- survival, write activity, territory
    occupancy/retention, kill interaction -- describing *how* the
    candidate played, deliberately kept separate from the evidence: block
    above (which describes outcome) and never derived from it. ``analysis``
    is an ``evaluation_behavior.BehaviorAnalysis``, typed ``Any`` here only
    to avoid a top-level circular import (mirrors ``_print_evidence``'s
    existing pattern -- ``evaluation_behavior`` imports from this module).
    """

    from battle_engine.evaluation_behavior import largest_bounded_differences

    overall = analysis.candidate_overall
    if overall.sample_count == 0:
        return
    survival = overall.dimension("survival_fraction")
    writes = overall.dimension("writes_per_tick")
    last = overall.dimension("territory_last_pct")
    peak = overall.dimension("territory_max_pct")
    avg = overall.dimension("territory_avg_pct")
    retention = overall.dimension("territory_retention")
    kills = overall.dimension("kills_per_match")
    deaths = overall.dimension("deaths_per_match")
    print("behavior:")
    print(
        f"  survival: {_fmt_fraction_pct(survival.mean)} (n={survival.n})   "
        f"writes/tick: {_fmt_rate(writes.mean)}"
    )
    print(
        f"  territory: last={_fmt_percent(last.mean)}  peak={_fmt_percent(peak.mean)}  "
        f"avg={_fmt_percent(avg.mean)}  retention={_fmt_fraction_pct(retention.mean)}"
    )
    print(f"  kills: {_fmt_rate(kills.mean)}/match   deaths: {_fmt_rate(deaths.mean)}/match")
    orientation_largest = largest_bounded_differences(analysis.candidate_orientation_deltas, limit=2)
    if orientation_largest:
        print(f"  orientation-sensitive dimensions: {', '.join(orientation_largest)}")
    if analysis.candidate_vs_baseline_largest:
        print(
            "  largest candidate-vs-baseline behavioral differences: "
            + ", ".join(analysis.candidate_vs_baseline_largest)
        )


def _print_capture_aggregate(aggregate: Any) -> None:
    print(f"  captures caused: {aggregate.captures_caused}/{aggregate.available_count}")
    print(f"  captures suffered: {aggregate.captures_suffered}/{aggregate.available_count}")
    print(
        f"  capture rate: caused={_fmt_fraction_pct(aggregate.capture_rate_caused)} "
        f"suffered={_fmt_fraction_pct(aggregate.capture_rate_suffered)}"
    )
    print(f"  survival rate (capture-avoidance): {_fmt_fraction_pct(aggregate.survival_rate)}")
    if aggregate.capture_ticks:
        print(
            f"  capture tick: mean={_fmt_rate(aggregate.mean_capture_tick)} "
            f"median={_fmt_rate(aggregate.median_capture_tick)}"
        )


def _print_capture(analysis: Any) -> None:
    print("capture/core evidence:")
    print(f"[candidate] {analysis.candidate_id}")
    _print_capture_aggregate(analysis.candidate_overall)
    if analysis.baseline_overall is not None:
        print(f"[baseline] {analysis.baseline_id}")
        _print_capture_aggregate(analysis.baseline_overall)


def _fmt_rate_stat(stat: Any) -> str:
    if stat.trials == 0:
        return "n/a (0 matches)"
    interval = stat.interval
    pct = 100.0 * (stat.rate or 0.0)
    ci = (
        f"  {round(interval.confidence_level * 100)}% CI [{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]"
        if interval is not None
        else ""
    )
    return f"{stat.successes}/{stat.trials} ({pct:.0f}%){ci}"


def _print_entrant_summary(label: str, summary: Any) -> None:
    print(f"  {label}:")
    print(f"    winner: {_fmt_rate_stat(summary.winner)}")
    print(f"    survival: {_fmt_rate_stat(summary.survival)}")
    if summary.score.n:
        print(f"    score: mean={summary.score.mean:.2f} (n={summary.score.n})")
    if summary.capture_suffered.trials:
        print(
            f"    captured: {_fmt_rate_stat(summary.capture_suffered)}   "
            f"caused: {_fmt_rate_stat(summary.capture_caused)}"
        )


def _print_group_analysis(result: EvaluationResult, request: EvaluationRequest) -> None:
    """v2.0.0-beta2 Phase 3: entrant-symmetric group analysis, presented
    candidate-first for CLI familiarity (Sec 22) -- ``evaluation_group_
    analysis.analyze_group`` itself never receives a candidate id (Sec 6/
    21's symmetry invariant), so this is pure presentation-time selection
    over an already-computed, already-symmetric result.
    """

    from battle_engine.evaluation_group_analysis import (
        analyze_group,
        candidate_focused_view,
        group_cell_ref_from_evaluation_cell,
    )

    scored_refs = [group_cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
    print("group analysis:")
    if not scored_refs:
        print("  no scored cells")
        return
    analysis = analyze_group(request.roster_agent_ids, scored_refs)
    view = candidate_focused_view(analysis, request.candidate_id)
    if view.legacy_subject_outcome_ambiguous:
        print(
            "  candidate logical outcome: ambiguous in legacy cell summaries; "
            f"{view.candidate_multiplicity} physical candidate instances occupy each cell"
        )
        print("  rates below use physical entrant instances as their denominator")
    if view.candidate is not None:
        label = f"candidate ({request.candidate_id}) overall"
        if view.candidate_multiplicity > 1:
            label += " [per physical entrant instance]"
        _print_entrant_summary(label, view.candidate)
    if view.candidate_seat_sensitivity is not None:
        print("  by seat:")
        for seat_summary in view.candidate_seat_sensitivity.by_seat:
            print(f"    {seat_summary.scope_label}: winner={_fmt_rate_stat(seat_summary.winner)}")
        seat_range = view.candidate_seat_sensitivity.winner_rate_range
        if seat_range is not None:
            print(f"    seat sensitivity (winner-rate range): {100.0 * seat_range:.0f} pp")
    if view.candidate_layout_sensitivity is not None:
        print("  by layout:")
        for layout_summary in view.candidate_layout_sensitivity.by_layout:
            print(f"    {layout_summary.scope_label}: winner={_fmt_rate_stat(layout_summary.winner)}")
        layout_range = view.candidate_layout_sensitivity.winner_rate_range
        if layout_range is not None:
            print(f"    layout sensitivity (winner-rate range): {100.0 * layout_range:.0f} pp")
    if view.other_entrants:
        print("  other entrants:")
        for other in view.other_entrants:
            _print_entrant_summary(other.agent_id, other)
    matrix = analysis.interaction_matrix
    if matrix.pairs or matrix.unattributed_captures:
        print("  captures (captor -> victim):")
        for pair in matrix.pairs:
            rate_pct = 100.0 * (pair.rate or 0.0)
            print(f"    {pair.captor_agent_id} -> {pair.victim_agent_id}: {pair.count} ({rate_pct:.0f}%)")
        if matrix.unattributed_captures:
            print(f"    unattributed: {matrix.unattributed_captures}")


def _print_result(result: EvaluationResult, request: EvaluationRequest) -> None:
    print(f"evaluation: {result.evaluation_id}")
    # v2.0.0-beta2 Phase 2: skip the 1v1-only "Entrant orientation:" line
    # for a group evaluation -- see _print_matrix's identical guard.
    orientation_line, alignment_line = methodology_lines(
        request.orientation_mode,
        arena_alignment_mode=resolved_arena_alignment_mode(
            request.is_v2_methodology,
            request.group,
            request.is_v4_methodology,
            request.is_v6_research_scale_methodology,
            request.is_v6_research_scale_move_methodology,
        ),
    )
    if not request.group:
        print(orientation_line)
    print(alignment_line)
    for aggregate in result.aggregates:
        if aggregate.orientation_scope != "all":
            continue
        if request.group and request.roster_agent_ids.count(aggregate.subject_id) > 1:
            print(f"[{aggregate.subject_role}] {aggregate.subject_id}")
            print(
                "  legacy candidate outcome aggregate: suppressed because this logical "
                "agent occupies multiple physical seats"
            )
            continue
        _print_aggregate(aggregate)
        # v2.0.0-beta2 Phase 2: orientation is not a meaningful axis for a
        # group cell (seat assignment is the generalized scheduler-order
        # axis instead, per-cell, never pooled into an evaluation-wide
        # orientation breakdown) -- every group cell defaults to
        # "candidate_first" (EvaluationCell.orientation's own sentinel),
        # so printing this breakdown for a group evaluation would show a
        # misleading "opponent_first: 0" rather than "not applicable".
        if request.both_orientations and not request.group:
            subject_aggregates = [
                a
                for a in result.aggregates
                if a.subject_role == aggregate.subject_role and a.subject_id == aggregate.subject_id
            ]
            _print_orientation_breakdown(subject_aggregates)
    # v2.0.0-beta2 Phase 2: evaluation_behavior/evaluation_capture's Tier-2
    # readers resolve the subject's physical match slot via `cell.
    # orientation` (a 2-value candidate_first/opponent_first axis) --
    # meaningless for a group cell, whose subject occupies whichever seat
    # `cell.subject_seat` says, not a fixed slot "A". They stay deferred
    # for group cells for exactly that reason; v2.0.0-beta2 Phase 3 adds
    # `evaluation_group_analysis`, an entrant-symmetric sibling built for
    # this axis instead -- see docs/V2_0_BETA2_PHASE3_MULTI_ENTRANT_
    # ANALYSIS.md.
    if request.group:
        _print_group_analysis(result, request)
    else:
        from battle_engine.evaluation_behavior import (
            analyze_behavior,
            cell_ref_from_evaluation_cell,
        )

        scored_refs = [cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
        _print_behavior(analyze_behavior(request.candidate_id, request.baseline_id, scored_refs))
        if request.is_v2_methodology:
            from battle_engine.evaluation_capture import analyze_capture

            _print_capture(analyze_capture(request.candidate_id, request.baseline_id, scored_refs))
    if request.baseline_id is not None:
        regressed = [entry for entry in result.comparison if entry.classification == "regressed"]
        improved = [entry for entry in result.comparison if entry.classification == "improved"]
        unchanged = [entry for entry in result.comparison if entry.classification == "unchanged"]
        inconclusive = [entry for entry in result.comparison if entry.classification == "inconclusive"]
        print(
            f"comparison: {len(improved)} improved, {len(regressed)} regressed, "
            f"{len(unchanged)} unchanged, {len(inconclusive)} inconclusive "
            f"(of {len(result.comparison)} matched cells)"
        )
        from battle_engine.evaluation_analysis import analyze as _analyze_evaluation

        _print_evidence(
            _analyze_evaluation(request.candidate_id, request.baseline_id, result.cells)
        )
        if regressed:
            print("regressions:")
            for entry in regressed:
                _print_comparison_entry(entry, request.ticks)
        if inconclusive:
            print("inconclusive:")
            for entry in inconclusive:
                _print_comparison_entry(entry, request.ticks)
    failed = result.failed_cells
    corrupted = result.corrupted_cells
    if failed:
        print("failed cells:")
        for cell in failed:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    if corrupted:
        print("corrupted cells (rerun with --retry-failed to reconcile):")
        for cell in corrupted:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    drifted = result.drift_cells
    if drifted:
        print(
            "SOURCE DRIFT DETECTED -- evaluation aborted; matrix execution stopped "
            "before completion. Start a fresh evaluation to evaluate the changed agent:"
        )
        for cell in drifted:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    print(f"evaluation artifact: {result.state_path}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    # v1.6 Phase 3: resolution layering is (1) ordinary defaults, (2) the
    # --preset (if any), (3) an explicit CLI option -- explicit always wins.
    # This is the one authoritative resolution path: a preset only ever
    # supplies values into the same variables an explicit invocation would
    # set directly below, so nothing downstream of this block (preflight,
    # EvaluationRequest, evaluation_id) can tell a preset was involved. See
    # docs/V1_6_PHASE3_EVALUATION_PRESETS.md.
    preset: EvaluationPreset | None = None
    if args.preset is not None:
        try:
            preset = load_preset(get_data_root(), args.preset)
        except EvaluationPresetError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    candidate_id = args.candidate_id
    if candidate_id is None and preset is not None:
        candidate_id = preset.candidate_id
    if candidate_id is None:
        print(
            "ERROR: candidate is required (supply it as a positional argument, "
            "or set 'candidate' in the --preset).",
            file=sys.stderr,
        )
        return 2

    baseline_id = args.baseline
    if baseline_id is None and preset is not None:
        baseline_id = preset.baseline_id

    try:
        if args.group and (args.single_orientation or args.both_orientations):
            raise EvaluationConfigurationError(
                "--single-orientation/--both-orientations cannot be combined with --group; "
                "group mode enumerates seat assignments instead of the pairwise orientation axis."
            )
        if args.opponents is not None:
            opponent_ids = parse_opponents(args.opponents)
        elif preset is not None and preset.opponent_ids is not None:
            opponent_ids = preset.opponent_ids
        else:
            raise EvaluationConfigurationError(
                "opponents are required (supply --opponents, or set 'opponents' "
                "in the --preset)."
            )

        # v2.0.0-beta2 Phase 1 / v4.0.0-rc1 Phase 1 (F.6 remediation):
        # resolved before seeds -- the standard v2/v4 seed default (below)
        # depends on which methodology this evaluation resolves to. Same
        # three-tier resolution as every other option (explicit CLI >
        # --preset > ordinary default). Moved after opponent_ids above
        # (F.6): a metadata-aware omitted-Ruleset resolution needs the
        # whole roster's real declared Agent API version, not just
        # candidate/baseline, so opponents must already be known here.
        ruleset_id = args.ruleset
        if ruleset_id is None and preset is not None:
            ruleset_id = preset.ruleset_id
        if ruleset_id is None:
            ruleset_id = BYTEFRAY_RULESET_V4_ID

        if args.seeds is not None or args.seed_range is not None:
            seeds = _resolve_seeds(args)
        elif preset is not None and preset.seeds is not None:
            seeds = preset.seeds
        elif preset is not None and preset.seed_range is not None:
            seeds = tuple(range(preset.seed_range[0], preset.seed_range[1] + 1))
        else:
            # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 2): the
            # stable v4 methodology's own standard sample set -- an
            # explicit --seeds/--seed-range or --preset seed selection
            # always overrides this (see the branches above, checked
            # first).
            seeds = STANDARD_V4_SEEDS
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.ticks is not None:
        ticks = args.ticks
    elif preset is not None and preset.ticks is not None:
        ticks = preset.ticks
    else:
        ticks = DEFAULT_TICKS

    # v3 Phase 0D: the identical three-tier resolution `--ticks` above uses
    # (explicit CLI > --preset > ordinary default), with "ordinary default"
    # expressed as `None` rather than a literal so `EvaluationRequest`
    # remains the single place `Config()`'s defaults are resolved.
    if args.arena_size is not None:
        arena_size = args.arena_size
    elif preset is not None and preset.arena_size is not None:
        arena_size = preset.arena_size
    else:
        arena_size = None

    if args.instr_per_tick is not None:
        instr_per_tick = args.instr_per_tick
    elif preset is not None and preset.instr_per_tick is not None:
        instr_per_tick = preset.instr_per_tick
    else:
        instr_per_tick = None

    # v3 Phase 3: `--kill-weight` follows the identical "no --preset field"
    # shape locality_reach uses below -- explicit CLI or ordinary default,
    # since a reweighting experiment has no business being a reusable
    # product-facing preset shape.
    kill_weight = args.kill_weight

    # v3 Phase 2's experimental bounded-locality Ruleset was never reachable
    # from this product CLI, and V6 Phase 2B.9 retired it from execution
    # entirely -- `EvaluationService._validate` now rejects any non-`None`
    # `EvaluationRequest.locality_reach` unconditionally. Always `None` here.
    locality_reach = None

    if args.single_orientation:
        both_orientations = False
    elif args.both_orientations:
        both_orientations = True
    elif preset is not None and preset.orientation is not None:
        both_orientations = preset.orientation == _PRESET_ORIENTATION_BOTH
    else:
        both_orientations = True

    service = EvaluationService()
    try:
        _specs, evaluation_id = service.preflight(
            candidate_id=candidate_id,
            opponent_ids=opponent_ids,
            seeds=seeds,
            baseline_id=baseline_id,
            ticks=ticks,
            both_orientations=both_orientations,
            ruleset_id=ruleset_id,
            group=args.group,
            arena_size=arena_size,
            instr_per_tick=instr_per_tick,
            locality_reach=locality_reach,
            kill_weight=kill_weight,
        )
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    root = get_data_root()
    output_dir = (
        args.output.expanduser().resolve()
        if args.output is not None
        else _default_output_dir(root, evaluation_id).resolve()
    )
    request = EvaluationRequest(
        candidate_id=candidate_id,
        opponent_ids=opponent_ids,
        seeds=seeds,
        output_dir=output_dir,
        baseline_id=baseline_id,
        ticks=ticks,
        retry_failures=args.retry_failed,
        both_orientations=both_orientations,
        workers=args.workers,
        ruleset_id=ruleset_id,
        group=args.group,
        arena_size=arena_size,
        instr_per_tick=instr_per_tick,
        locality_reach=locality_reach,
        kill_weight=kill_weight,
    )
    matrix = build_matrix(request, evaluation_id)
    if args.dry_run:
        if args.json:
            if not args.quiet:
                print(json.dumps(_matrix_to_json(request, matrix, preset), indent=2, sort_keys=True))
        else:
            _print_matrix(request, matrix, preset)
        return 0
    if not args.quiet and not args.json:
        _print_matrix(request, matrix, preset)

    try:
        result = service.run(request)
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        if args.json:
            print(json.dumps(_result_to_json(result, request), indent=2, sort_keys=True))
        else:
            _print_result(result, request)
    return 1 if (result.failed_cells or result.corrupted_cells or result.drift_cells) else 0


if __name__ == "__main__":
    raise SystemExit(main())
