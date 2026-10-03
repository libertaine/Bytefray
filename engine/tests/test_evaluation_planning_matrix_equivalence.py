"""V6 Phase 3G: full-matrix equivalence guard for ``evaluation_planning``.

Every expected value in this module was computed from the *pre-extraction*
implementation at ``74e9d60`` (Phase 3F's HEAD), in a separate worktree,
before ``build_matrix`` and its placement geometry moved out of
``battle_engine.agent_evaluation``.  They are frozen baselines, never
regenerated from the module under test: if planning ever compiles a
different matrix -- a different size, a different order, a different value
in any ``EvaluationCell`` field, a different artifact path label, a
different schedule id or condition fingerprint -- these digests change and
this guard fails.  Do not update them to accommodate a refactor.

Coverage is deliberately whole-record.  ``_render_cell`` below serializes
every declared ``EvaluationCell`` field, so the per-case digests cover
fields no test names explicitly, and
``test_planning_leaves_every_execution_field_at_its_declared_default``
closes the other half: planning assigns exactly the coordinates it owns and
leaves every execution/outcome field untouched.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import MISSING, fields
from pathlib import Path

import battle_engine.agent_evaluation as evaluation
import battle_engine.evaluation_identity as identity
import battle_engine.evaluation_planning as planning
import pytest
from battle_engine.agents import AgentSpec
from battle_engine.evaluation_contracts import EvaluationCell, EvaluationRequest
from battle_engine.rules import BYTEFRAY_RULESET_ID, BYTEFRAY_RULESET_V4_ID
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V2_ID

OUTPUT_DIR = Path("/frozen/out")
CONDITIONS_FP = "evaluation-conditions_0123456789abcdef01234567"
ALIGNMENT = "frozen-alignment-mode"

CELL_FIELDS = tuple(f.name for f in fields(EvaluationCell))


def _spec(name: str) -> AgentSpec:
    return AgentSpec(
        name=name,
        display=name,
        dir=Path("/frozen") / name,
        blob=None,
        defaults={},
        kind="python",
        api_version=3,
        version="1.0.0",
        source_path=None,
        entry_point="agent.py",
    )


SPECS = {name: _spec(name) for name in ("cand", "base", "opp-a", "opp-b")}


def _render_cell(cell: EvaluationCell) -> str:
    """Every declared field of one cell, in declaration order.

    ``artifact_dir`` is rendered relative to the request's own output
    directory, as POSIX, so the frozen digests describe the path *label*
    planning chose rather than the host's path separator.
    """

    parts = []
    for name in CELL_FIELDS:
        value = getattr(cell, name)
        if name == "artifact_dir":
            value = Path(value).relative_to(OUTPUT_DIR).as_posix()
        parts.append(f"{name}={value!r}")
    return "|".join(parts)


def _digest(cells) -> str:
    joined = "\n".join(_render_cell(cell) for cell in cells)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _request(**kwargs) -> EvaluationRequest:
    base: dict = {
        "candidate_id": "cand",
        "opponent_ids": ("opp-b", "opp-a", "opp-a"),
        "seeds": (1, 7, 1),
        "output_dir": OUTPUT_DIR,
        "ticks": 1200,
    }
    base.update(kwargs)
    return EvaluationRequest(**base)


# The six representative requests the frozen digests below describe: unique
# inputs, duplicate opponents *and* duplicate seeds, both orientations, a
# candidate/baseline pair, the historical v2 placement expansion, and the
# historical v1 fixed alignment.
CASES: dict[str, EvaluationRequest] = {
    "v4_unique": _request(
        opponent_ids=("opp-a", "opp-b"), seeds=(1, 2, 3), both_orientations=False
    ),
    "v4_duplicate_opponents_and_seeds": _request(both_orientations=False),
    "v4_both_orientations": _request(both_orientations=True),
    "v4_candidate_and_baseline": _request(baseline_id="base", both_orientations=True),
    "v2_placements": _request(
        ruleset_id=BYTEFRAY_RULESET_V2_ID, arena_size=4096, both_orientations=True
    ),
    "v1_fixed": _request(
        ruleset_id=BYTEFRAY_RULESET_ID, arena_size=4096, both_orientations=True
    ),
}

GROUP_REQUEST = EvaluationRequest(
    candidate_id="cand",
    opponent_ids=("opp-a", "opp-b"),
    seeds=(3, 3),
    output_dir=OUTPUT_DIR,
    ticks=1200,
    ruleset_id=BYTEFRAY_RULESET_V2_ID,
    arena_size=4096,
    group=True,
)


def _matrix_for(name: str):
    request = CASES[name]
    return planning.build_matrix(
        request,
        f"evaluation-{name}",
        SPECS,
        CONDITIONS_FP,
        request.resolved_rules_compatibility_id,
        ALIGNMENT,
    )


# ---------------------------------------------------------------------------
# Frozen expectations (computed at 74e9d60 -- see the module docstring)
# ---------------------------------------------------------------------------

FROZEN_MATRICES = {
    "v4_unique": (6, "7653cead787f2c478d07be4e1ea811a06330706017c9a44b23aa9e73a45e8b62"),
    "v4_duplicate_opponents_and_seeds": (
        9,
        "f92d57e0f95d7959d5c7a2760a0be33598d58cbe264e71744351b37d2f75b205",
    ),
    "v4_both_orientations": (
        18,
        "f4988cb576cd2d4bf44c699d1ee44d4d26b0ac5983a4a9bca2a6801fc2aca7d9",
    ),
    "v4_candidate_and_baseline": (
        36,
        "eca522700711db2d043aa51a75dce005b3efd36bd9b1e3fb2ca1cc2dad35606d",
    ),
    "v2_placements": (54, "a622cb7dc9ad7391449084e1735ebf4277ecd5d02557a0ec88f7f3e9c0cb1e57"),
    "v1_fixed": (18, "d6777c25208461fb3d2c8d0296be1b617a412d5a9cefe1521690f3034dfdae3d"),
}

FROZEN_GROUP_MATRIX = (36, "2633e9017714d47efd91dc24141215ad6dcdfcee06453c67a9742ac6d9f6cff6")

# The nine cells ``("opp-b", "opp-a", "opp-a")`` x ``(1, 7, 1)`` compiles to,
# spelled out rather than digested so a duplicate-handling regression reads
# as a concrete diff.  Columns: ordinal, opponent, opponent index, seed, seed
# index, condition occurrence index, placement id, subject start, opponent
# start, path label, schedule id, condition fingerprint.
FROZEN_DUPLICATE_CELLS = (
    (
        1,
        "opp-b",
        0,
        1,
        0,
        0,
        "seeded-1",
        380,
        263,
        "0001-candidate-cand-vs-opp-b-seed1-seeded-1-candidate_first",
        "evaluation-cell_bb4c8e880ae5dc6da4177611",
        "evaluation-condition_9a865ecaca9584bf63249448",
    ),
    (
        2,
        "opp-b",
        0,
        7,
        1,
        0,
        "seeded-7",
        324,
        167,
        "0002-candidate-cand-vs-opp-b-seed7-seeded-7-candidate_first",
        "evaluation-cell_948351ecb7369db71678ce98",
        "evaluation-condition_cf7922d74d15208d05913005",
    ),
    (
        3,
        "opp-b",
        0,
        1,
        2,
        1,
        "seeded-1",
        380,
        263,
        "0003-candidate-cand-vs-opp-b-seed1-seeded-1-candidate_first",
        "evaluation-cell_3c7d2806ff8c8b1ee9338e9a",
        "evaluation-condition_ffebb3229fe59306cdb0678c",
    ),
    (
        4,
        "opp-a",
        1,
        1,
        0,
        0,
        "seeded-1",
        380,
        263,
        "0004-candidate-cand-vs-opp-a-seed1-seeded-1-candidate_first",
        "evaluation-cell_f2db1768c6254a9c6085ef85",
        "evaluation-condition_a8fdb9c43aebc6bf2f20c06b",
    ),
    (
        5,
        "opp-a",
        1,
        7,
        1,
        0,
        "seeded-7",
        324,
        167,
        "0005-candidate-cand-vs-opp-a-seed7-seeded-7-candidate_first",
        "evaluation-cell_1f78557d417a74ba89bea292",
        "evaluation-condition_ec33e718c5decf40db9184cf",
    ),
    (
        6,
        "opp-a",
        1,
        1,
        2,
        1,
        "seeded-1",
        380,
        263,
        "0006-candidate-cand-vs-opp-a-seed1-seeded-1-candidate_first",
        "evaluation-cell_d2949929d2d844bec99fb02f",
        "evaluation-condition_0a287f5c69eb4c5fea95c2d0",
    ),
    (
        7,
        "opp-a",
        2,
        1,
        0,
        2,
        "seeded-1",
        380,
        263,
        "0007-candidate-cand-vs-opp-a-seed1-seeded-1-candidate_first",
        "evaluation-cell_e589ad2b485be4317a8baa7d",
        "evaluation-condition_3afa19ec25da6d4c1fc72e93",
    ),
    (
        8,
        "opp-a",
        2,
        7,
        1,
        1,
        "seeded-7",
        324,
        167,
        "0008-candidate-cand-vs-opp-a-seed7-seeded-7-candidate_first",
        "evaluation-cell_c9c899b20953ecd99925356e",
        "evaluation-condition_b16ffc3dde56070139ecd3bc",
    ),
    (
        9,
        "opp-a",
        2,
        1,
        2,
        3,
        "seeded-1",
        380,
        263,
        "0009-candidate-cand-vs-opp-a-seed1-seeded-1-candidate_first",
        "evaluation-cell_304ecde6cb72abe37f3c9fce",
        "evaluation-condition_6e991867593a724ef4cbfe6c",
    ),
)

# ``resolve_v4_seed_geometry`` samples, including the two coordinates Phase
# 3C/3F already pin, re-frozen here so a geometry regression also surfaces
# inside the planning guard.
FROZEN_V4_GEOMETRY = {
    (BYTEFRAY_RULESET_V4_ID, 512, 1): (380, 263),
    (BYTEFRAY_RULESET_V4_ID, 512, 3): (495, 387),
    (BYTEFRAY_RULESET_V4_ID, 512, 7): (324, 167),
    (BYTEFRAY_RULESET_V4_ID, 1024, 1): (967, 306),
    (BYTEFRAY_RULESET_V4_ID, 4096, 42): (4089, 2137),
}

# Fields planning legitimately assigns; everything else must stay at the
# ``EvaluationCell`` default until execution fills it in.
PAIRWISE_PLANNED_FIELDS = frozenset(
    {
        "schedule_id",
        "subject_role",
        "subject_id",
        "opponent_id",
        "seed",
        "artifact_dir",
        "opponent_index",
        "seed_index",
        "matrix_ordinal",
        "condition_occurrence_index",
        "condition_fingerprint",
        "orientation",
        "orientation_index",
        "rules_compatibility_id",
        "placement_id",
        "subject_start",
        "opponent_start",
        "placement_index",
    }
)

GROUP_PLANNED_FIELDS = frozenset(
    {
        "schedule_id",
        "subject_role",
        "subject_id",
        "opponent_id",
        "seed",
        "artifact_dir",
        "seed_index",
        "matrix_ordinal",
        "condition_fingerprint",
        "rules_compatibility_id",
        "roster_agent_ids",
        "seat_agent_ids",
        "layout_id",
        "seat_starts",
        "seat_assignment_index",
        "layout_index",
    }
)


def _declared_default(name: str):
    field = next(f for f in fields(EvaluationCell) if f.name == name)
    if field.default is not MISSING:
        return field.default
    if field.default_factory is not MISSING:
        return field.default_factory()
    return MISSING


def _group_matrix():
    return planning._build_group_matrix(
        GROUP_REQUEST, "evaluation-group", BYTEFRAY_RULESET_V2_ID, SPECS, CONDITIONS_FP
    )


# ---------------------------------------------------------------------------
# Matrix equivalence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", tuple(FROZEN_MATRICES))
def test_full_matrix_records_match_the_pre_extraction_baseline(name: str) -> None:
    expected_length, expected_digest = FROZEN_MATRICES[name]
    matrix = _matrix_for(name)
    assert len(matrix) == expected_length
    assert _digest(matrix) == expected_digest


def test_group_matrix_records_match_the_pre_extraction_baseline() -> None:
    """Retired group planning still reconstructs its historical cells exactly.

    Reconstructable, not executable -- the public compiler still refuses a
    group request outright, asserted just below.
    """

    expected_length, expected_digest = FROZEN_GROUP_MATRIX
    matrix = _group_matrix()
    assert len(matrix) == expected_length
    assert _digest(matrix) == expected_digest


def test_building_a_group_matrix_through_the_public_compiler_stays_refused() -> None:
    with pytest.raises(evaluation.EvaluationConfigurationError) as excinfo:
        planning.build_matrix(GROUP_REQUEST, "evaluation-group")
    assert "retired" in str(excinfo.value)


def test_duplicate_opponent_and_seed_cells_keep_their_occurrence_coordinates() -> None:
    """Duplicates stay distinct cells, separated by occurrence coordinates.

    ``("opp-b", "opp-a", "opp-a")`` x ``(1, 7, 1)`` must stay nine cells --
    never deduplicated, never canonicalized -- each keeping the exact
    ordinal, occurrence index, geometry, label, schedule id and condition
    fingerprint the pre-extraction implementation gave it.
    """

    matrix = _matrix_for("v4_duplicate_opponents_and_seeds")
    actual = tuple(
        (
            cell.matrix_ordinal,
            cell.opponent_id,
            cell.opponent_index,
            cell.seed,
            cell.seed_index,
            cell.condition_occurrence_index,
            cell.placement_id,
            cell.subject_start,
            cell.opponent_start,
            cell.artifact_dir.name,
            cell.schedule_id,
            cell.condition_fingerprint,
        )
        for cell in matrix
    )
    assert actual == FROZEN_DUPLICATE_CELLS


def test_planning_leaves_every_execution_field_at_its_declared_default() -> None:
    """The other half of whole-record coverage.

    The per-case digests pin every field planning assigns; this pins that it
    assigns nothing else, so a future planning change cannot quietly start
    pre-populating an execution or outcome field.
    """

    for name in CASES:
        for cell in _matrix_for(name):
            for field_name in CELL_FIELDS:
                if field_name in PAIRWISE_PLANNED_FIELDS:
                    continue
                assert getattr(cell, field_name) == _declared_default(field_name), (
                    name,
                    cell.matrix_ordinal,
                    field_name,
                )

    for cell in _group_matrix():
        for field_name in CELL_FIELDS:
            if field_name in GROUP_PLANNED_FIELDS:
                continue
            assert getattr(cell, field_name) == _declared_default(field_name), (
                cell.matrix_ordinal,
                field_name,
            )


def test_artifact_paths_stay_under_the_requested_output_directory() -> None:
    for name in CASES:
        for cell in _matrix_for(name):
            assert cell.artifact_dir.parent == OUTPUT_DIR / "matches"


def test_dry_run_preview_omits_condition_fingerprints_but_keeps_every_coordinate() -> None:
    """A ``--dry-run``/Designer preview passes no specs and no conditions.

    Only ``condition_fingerprint`` may differ from the fully-specified
    matrix; ordering, geometry, labels and schedule ids must be identical,
    because a preview showing a different matrix than the run would be worse
    than no preview at all.
    """

    for name, request in CASES.items():
        planned = _matrix_for(name)
        preview = planning.build_matrix(request, f"evaluation-{name}")
        assert len(preview) == len(planned)
        for planned_cell, preview_cell in zip(planned, preview, strict=True):
            assert preview_cell.condition_fingerprint is None
            for field_name in CELL_FIELDS:
                if field_name == "condition_fingerprint":
                    continue
                assert getattr(preview_cell, field_name) == getattr(
                    planned_cell, field_name
                ), (name, field_name)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", tuple(FROZEN_V4_GEOMETRY))
def test_v4_seeded_geometry_resolves_to_its_pinned_coordinates(key) -> None:
    rules_id, arena_size, seed = key
    resolved = planning.resolve_v4_seed_geometry(rules_id, arena_size, seed)
    assert resolved == FROZEN_V4_GEOMETRY[key]


def test_v4_cells_share_one_seeded_geometry_across_both_orientations() -> None:
    """Orientation swaps the occupants of the two resolved seats, not the seats."""

    seats_by_seed: dict[int, set[tuple[int, int]]] = {}
    for cell in _matrix_for("v4_both_orientations"):
        low = min(cell.subject_start, cell.opponent_start)
        high = max(cell.subject_start, cell.opponent_start)
        seats_by_seed.setdefault(cell.seed, set()).add((low, high))
    assert seats_by_seed
    for seed, seats in seats_by_seed.items():
        assert len(seats) == 1, (seed, seats)


# ---------------------------------------------------------------------------
# Facade and dependency direction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    (
        "build_matrix",
        "enumerate_seat_assignments",
        "resolve_v4_seed_geometry",
        "standard_layouts",
        "standard_placements",
    ),
)
def test_facade_reexports_the_canonical_planning_function_object(name: str) -> None:
    assert getattr(evaluation, name) is getattr(planning, name)


def test_planning_does_not_import_the_facade_or_any_orchestration_layer() -> None:
    """Planning must load without the monolith, history, CLI, worker or app.

    Checked in a fresh interpreter so a sibling already imported by this test
    session cannot hide a real dependency.
    """

    code = (
        "import sys\n"
        "import battle_engine.evaluation_planning\n"
        "forbidden = sorted(\n"
        "    name\n"
        "    for name in sys.modules\n"
        "    if name == 'battle_engine.agent_evaluation'\n"
        "    or name == 'argparse'\n"
        "    or name.startswith('battle_engine.evaluation_history')\n"
        "    or name.startswith('battle_engine.agent_worker')\n"
        "    or name.startswith('battle_engine.evaluation_worker')\n"
        "    or name.startswith('app')\n"
        ")\n"
        "print(','.join(forbidden))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == ""


def test_identity_stays_below_planning() -> None:
    """``evaluation_identity`` must never reach back up into planning."""

    code = (
        "import sys\n"
        "import battle_engine.evaluation_identity\n"
        "print('battle_engine.evaluation_planning' in sys.modules)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == "False"
    assert "evaluation_planning" not in Path(identity.__file__).read_text(encoding="utf-8")
