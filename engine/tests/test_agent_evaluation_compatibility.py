"""Extraction guards for the ``battle_engine.agent_evaluation`` facade.

These tests intentionally distinguish supported compatibility behavior from
two known defects.  The defect tests state the desired invariant and are
strict xfails while the production behavior remains unfixed.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from pathlib import Path

import battle_engine.agent_evaluation as evaluation
import battle_engine.agent_test as agent_test_module
import battle_engine.evaluation_contracts as contracts
import pytest
from battle_engine.config import Config
from battle_engine.rules import (
    BYTEFRAY_RULESET_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
)
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V2_ID

# Exact declaration at the Phase 3C baseline.  Order is retained because it
# is cheap to protect and avoids silently changing ``from ... import *``
# presentation during the extraction even though ordinary named imports do
# not depend on it.
EXPECTED_ALL = (
    "BASELINE",
    "BYTEFRAY_RULESET_ID",
    "BYTEFRAY_RULESET_V2_ID",
    "CANDIDATE",
    "EVALUATION_ARENA_ALIGNMENT_MODE",
    "EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD",
    "EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD",
    "EVALUATION_RULES_COMPATIBILITY_ID",
    "IDENTITY_VERSION",
    "IDENTITY_VERSION_V2",
    "IDENTITY_VERSION_V2_GROUP",
    "LOCAL_SOURCE_FINGERPRINT_VERSION",
    "ORIENTATION_CANDIDATE_FIRST",
    "ORIENTATION_MODE_BOTH",
    "ORIENTATION_MODE_CANDIDATE_FIRST_ONLY",
    "ORIENTATION_OPPONENT_FIRST",
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_V2",
    "SCHEMA_VERSION_V2_GROUP",
    "STANDARD_V2_SEEDS",
    "ComparisonEntry",
    "EffectiveConditions",
    "EvaluationCell",
    "EvaluationConfigurationError",
    "EvaluationLayout",
    "EvaluationPlacement",
    "EvaluationRequest",
    "EvaluationResult",
    "EvaluationSeatAssignment",
    "EvaluationService",
    "ExecutionContext",
    "SubjectAggregate",
    "agent_identity",
    "aggregate_cells",
    "all_subject_aggregates",
    "build_matrix",
    "classify",
    "compare_candidate_baseline",
    "current_execution_context",
    "effective_conditions_for",
    "enumerate_seat_assignments",
    "is_ruleset_v2_methodology",
    "local_source_fingerprint",
    "main",
    "methodology_lines",
    "parse_opponents",
    "parse_seed_list",
    "parse_seed_range",
    "physical_slots_for_orientation",
    "read_evaluation",
    "rerun_command",
    "resolve_evaluation_ruleset_id",
    "resolved_arena_alignment_mode",
    "resolved_identity_version",
    "resolved_schema_version",
    "seat_label",
    "source_digest",
    "standard_layouts",
    "standard_placements",
)

# An AST inventory of production modules under engine/src, app, and tools at
# the Phase 3C baseline found exactly these live named imports outside
# ``__all__``.  They remain facade attributes, but this test deliberately
# does not promote them into the star-import contract above.
LIVE_PRODUCTION_ATTRIBUTES_OUTSIDE_ALL = (
    "IDENTITY_VERSION_V4",
    "LIFECYCLE_STATE_FINISHED_WITH_FAILURES",
    "STANDARD_V4_SEEDS",
    "is_ruleset_v4_methodology",
    "resolve_v4_seed_geometry",
)


def test_agent_evaluation_all_is_the_exact_compatibility_declaration() -> None:
    assert tuple(evaluation.__all__) == EXPECTED_ALL


def test_live_production_imports_outside_all_remain_facade_attributes() -> None:
    assert set(LIVE_PRODUCTION_ATTRIBUTES_OUTSIDE_ALL).isdisjoint(evaluation.__all__)
    for name in LIVE_PRODUCTION_ATTRIBUTES_OUTSIDE_ALL:
        assert hasattr(evaluation, name), name


def test_every_compatibility_name_is_importable_by_name() -> None:
    names = EXPECTED_ALL + LIVE_PRODUCTION_ATTRIBUTES_OUTSIDE_ALL
    imported = __import__("battle_engine.agent_evaluation", fromlist=list(names))
    for name in names:
        assert getattr(imported, name) is getattr(evaluation, name)


CONTRACT_MODEL_TYPES = (
    evaluation.ComparisonEntry,
    evaluation.EffectiveConditions,
    evaluation.EvaluationCell,
    evaluation.EvaluationLayout,
    evaluation.EvaluationPlacement,
    evaluation.EvaluationRequest,
    evaluation.EvaluationResult,
    evaluation.EvaluationSeatAssignment,
    evaluation.ExecutionContext,
    evaluation.SubjectAggregate,
)

MOVED_CLASS_NAMES = (
    "EvaluationConfigurationError",
    *(contract_type.__name__ for contract_type in CONTRACT_MODEL_TYPES),
)


@pytest.mark.parametrize("name", MOVED_CLASS_NAMES)
def test_facade_reexports_the_canonical_contract_class_object(name: str) -> None:
    assert getattr(evaluation, name) is getattr(contracts, name)


@pytest.mark.parametrize("contract_type", CONTRACT_MODEL_TYPES, ids=lambda value: value.__name__)
def test_exported_contract_models_remain_frozen_dataclasses(contract_type: type) -> None:
    assert is_dataclass(contract_type)
    assert contract_type.__dataclass_params__.frozen is True


def test_evaluation_request_defaults_and_derived_methodology_are_stable() -> None:
    request = evaluation.EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(1,),
        output_dir=Path("out"),
    )

    assert request == replace(request)
    assert request.baseline_id is None
    assert request.ticks == agent_test_module.DEFAULT_TICKS
    assert request.resume is True
    assert request.retry_failures is False
    assert request.both_orientations is True
    assert request.workers == 1
    assert request.ruleset_id is None
    assert request.group is False
    assert request.arena_size is None
    assert request.instr_per_tick is None
    assert request.locality_reach is None
    assert request.kill_weight is None
    assert request.scheduler_chunk_size is None
    assert request.scheduler_rotate_start is False
    assert request.orientation_mode == evaluation.ORIENTATION_MODE_BOTH
    assert request.resolved_rules_compatibility_id == BYTEFRAY_RULESET_V4_ID
    assert request.is_v2_methodology is False
    assert request.is_v4_methodology is True
    assert request.resolved_arena_size == 512
    assert request.resolved_instr_per_tick == Config().instr_per_tick
    assert request.resolved_kill_weight == Config().weights.kill
    assert request.resolved_locality_reach is None
    assert request.roster_agent_ids == ("candidate", "opponent")
    assert request.canonical_roster == ("candidate", "opponent")

    with pytest.raises(FrozenInstanceError):
        request.candidate_id = "changed"  # type: ignore[misc]


def test_cell_and_result_derived_properties_survive_relocation() -> None:
    pending = evaluation.EvaluationCell(
        schedule_id="cell-1",
        subject_role=evaluation.CANDIDATE,
        subject_id="candidate",
        opponent_id="opponent",
        seed=1,
        artifact_dir=Path("matches/cell-1"),
    )
    assert pending.status == "pending"
    assert pending.orientation == evaluation.ORIENTATION_CANDIDATE_FIRST
    assert pending.rules_compatibility_id == evaluation.EVALUATION_RULES_COMPATIBILITY_ID
    assert pending.placement_id == "fixed"
    assert pending.is_group is False
    assert pending.subject_seat is None
    assert pending.is_scored is False

    scored = replace(pending, status="completed", outcome="win")
    failed = replace(pending, schedule_id="cell-2", status="failed")
    corrupted = replace(pending, schedule_id="cell-3", status="corrupted")
    drifted = replace(pending, schedule_id="cell-4", status="drift_detected")
    assert scored.is_scored is True

    result = evaluation.EvaluationResult(
        evaluation_id="evaluation-v2_contract",
        request=evaluation.EvaluationRequest("candidate", ("opponent",), (1,), Path("out")),
        cells=(scored, failed, corrupted, drifted),
        aggregates=(),
        comparison=(),
        state_path=Path("out/evaluation.json"),
    )
    assert result.failed_cells == (failed,)
    assert result.corrupted_cells == (corrupted,)
    assert result.drift_cells == (drifted,)


def test_aggregate_comparison_and_context_observable_defaults_are_stable() -> None:
    aggregate = evaluation.SubjectAggregate(evaluation.CANDIDATE, "candidate")
    assert aggregate.win_rate_display == "0/0 (n/a)"
    assert replace(aggregate, matches_played=4, wins=3).win_rate_display == "3/4 (75%)"
    assert aggregate.orientation_scope == "all"

    comparison = evaluation.ComparisonEntry("opponent", 7, "inconclusive")
    assert comparison.orientation == evaluation.ORIENTATION_CANDIDATE_FIRST
    assert comparison.placement_id == "fixed"
    assert comparison.candidate_outcome is None
    assert comparison.baseline_outcome is None

    context = evaluation.ExecutionContext(
        context_id="evaluation-context_contract",
        bytefray_version="test",
        agent_api_version=2,
        python_version="3.13",
        result_schema_version=2,
        replay_schema_version=4,
        rules_compatibility_id=BYTEFRAY_RULESET_V4_ID,
    )
    assert context.first_used_at == ""
    assert context.to_dict() == {
        "context_id": "evaluation-context_contract",
        "bytefray_version": "test",
        "agent_api_version": 2,
        "python_version": "3.13",
        "result_schema_version": 2,
        "replay_schema_version": 4,
        "rules_compatibility_id": BYTEFRAY_RULESET_V4_ID,
        "first_used_at": "",
    }


@pytest.mark.parametrize(
    (
        "ruleset_id",
        "is_v2",
        "is_v4",
        "identity_version",
        "schema_version",
        "alignment_mode",
    ),
    (
        (
            BYTEFRAY_RULESET_ID,
            False,
            False,
            4,
            4,
            evaluation.EVALUATION_ARENA_ALIGNMENT_MODE,
        ),
        (
            BYTEFRAY_RULESET_V2_ID,
            True,
            False,
            5,
            5,
            evaluation.EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD,
        ),
        (
            BYTEFRAY_RULESET_V4_ALPHA1_ID,
            True,
            False,
            5,
            5,
            evaluation.EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD,
        ),
        (
            BYTEFRAY_RULESET_V4_ALPHA2_ID,
            False,
            True,
            7,
            7,
            "ruleset_v4_seeded_placements",
        ),
        (
            BYTEFRAY_RULESET_V4_ID,
            False,
            True,
            7,
            7,
            "ruleset_v4_seeded_placements",
        ),
    ),
)
def test_methodology_version_resolution_keeps_historical_read_vocabulary(
    ruleset_id: str,
    is_v2: bool,
    is_v4: bool,
    identity_version: int,
    schema_version: int,
    alignment_mode: str,
) -> None:
    assert evaluation.is_ruleset_v2_methodology(ruleset_id) is is_v2
    assert evaluation.is_ruleset_v4_methodology(ruleset_id) is is_v4
    assert evaluation.resolved_identity_version(is_v2, False, is_v4) == identity_version
    assert evaluation.resolved_schema_version(is_v2, False, is_v4) == schema_version
    assert evaluation.resolved_arena_alignment_mode(is_v2, False, is_v4) == alignment_mode


def test_group_version_vocabulary_remains_historical_without_enabling_execution() -> None:
    assert evaluation.resolved_identity_version(True, True, False) == 6
    assert evaluation.resolved_schema_version(True, True, False) == 6
    assert (
        evaluation.resolved_arena_alignment_mode(True, True, False)
        == evaluation.EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD
    )


@pytest.mark.parametrize(
    "retired_ruleset_id",
    (
        BYTEFRAY_RULESET_ID,
        BYTEFRAY_RULESET_V2_ID,
        BYTEFRAY_RULESET_V4_ALPHA1_ID,
        BYTEFRAY_RULESET_V4_ALPHA2_ID,
        "evaluation-rules-1",
    ),
)
def test_historical_methodology_ids_are_readable_vocabulary_not_executable_choices(
    retired_ruleset_id: str,
) -> None:
    request = evaluation.EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(1,),
        output_dir=Path("out"),
        ruleset_id=retired_ruleset_id,
    )
    with pytest.raises(evaluation.EvaluationConfigurationError, match="Unsupported evaluation"):
        evaluation.EvaluationService()._validate(request)


def _write_agent(root: Path, name: str) -> Path:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(
        json.dumps(
            {
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0",
            }
        ),
        encoding="utf-8",
    )
    source = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration("main", self.arena_size - 1, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor)

def create_agent():
    return Agent()
"""
    source_path = directory / "agent.py"
    source_path.write_text(source, encoding="utf-8")
    return source_path


@pytest.fixture()
def evaluation_agents(tmp_path: Path) -> Path:
    _write_agent(tmp_path, "candidate")
    _write_agent(tmp_path, "opponent")
    return tmp_path


def _fail_match_after_request_capture(monkeypatch: pytest.MonkeyPatch, captured: list) -> None:
    def _run(_self, request):
        captured.append(request)
        raise RuntimeError("stop after MatchRequest capture")

    monkeypatch.setattr(agent_test_module.NativeMatchService, "run", _run)


def test_scheduler_overrides_propagate_to_each_cell_match_request(
    evaluation_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list = []
    _fail_match_after_request_capture(monkeypatch, captured)
    request = evaluation.EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(1,),
        output_dir=evaluation_agents / "scheduler-propagation",
        ticks=5,
        data_root=evaluation_agents,
        both_orientations=False,
        scheduler_chunk_size=1,
        scheduler_rotate_start=True,
    )

    result = evaluation.EvaluationService().run(request)

    assert len(captured) == 1
    assert captured[0].scheduler_chunk_size == 1
    assert captured[0].scheduler_rotate_start is True
    assert result.cells[0].status == "failed"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: scheduler overrides reach execution but are omitted from evaluation identity; "
        "the desired invariant is that execution-changing inputs cannot silently collide."
    ),
)
def test_scheduler_overrides_that_change_execution_must_change_evaluation_identity() -> None:
    identities = {
        "candidate": {"agent_id": "candidate", "source_sha256": "candidate"},
        "opponent": {"agent_id": "opponent", "source_sha256": "opponent"},
    }
    conditions = evaluation.EffectiveConditions(
        tick_limit=5,
        arena_size=512,
        action_budget=8,
        win_mode="score_fallback",
        weights={"alive": 1.0, "kill": 5.0, "territory": 1.0, "territory_bucket": 64},
        agent_api_version=2,
    )
    request = evaluation.EvaluationRequest(
        "candidate",
        ("opponent",),
        (1,),
        Path("out"),
        ticks=5,
        both_orientations=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=512,
    )
    overridden = replace(request, scheduler_chunk_size=1, scheduler_rotate_start=True)
    service = evaluation.EvaluationService()

    ordinary_id = service._evaluation_id(request, identities, conditions)
    overridden_id = service._evaluation_id(overridden, identities, conditions)

    assert ordinary_id != overridden_id


def test_preflight_and_run_freeze_the_same_identity_when_source_is_stable(
    evaluation_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list = []
    _fail_match_after_request_capture(monkeypatch, captured)
    service = evaluation.EvaluationService()
    _specs, preflight_id = service.preflight(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(1,),
        ticks=5,
        data_root=evaluation_agents,
        both_orientations=False,
    )
    request = evaluation.EvaluationRequest(
        "candidate",
        ("opponent",),
        (1,),
        evaluation_agents / "stable-preflight",
        ticks=5,
        data_root=evaluation_agents,
        both_orientations=False,
    )

    result = service.run(request)

    assert result.evaluation_id == preflight_id
    assert json.loads(result.state_path.read_text(encoding="utf-8"))["evaluation_id"] == preflight_id


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: run freezes source independently after preflight, so a preflight-addressed "
        "directory can receive an artifact carrying a different evaluation id."
    ),
)
def test_preflight_addressed_output_must_not_silently_accept_a_different_run_identity(
    evaluation_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list = []
    _fail_match_after_request_capture(monkeypatch, captured)
    service = evaluation.EvaluationService()
    _specs, preflight_id = service.preflight(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(1,),
        ticks=5,
        data_root=evaluation_agents,
        both_orientations=False,
    )
    output_dir = evaluation_agents / "runs" / "evaluations" / preflight_id
    candidate_source = evaluation_agents / "agents" / "candidate" / "agent.py"
    candidate_source.write_text(
        candidate_source.read_text(encoding="utf-8") + "\n# changed after preflight\n",
        encoding="utf-8",
    )
    request = evaluation.EvaluationRequest(
        "candidate",
        ("opponent",),
        (1,),
        output_dir,
        ticks=5,
        data_root=evaluation_agents,
        both_orientations=False,
    )

    try:
        result = service.run(request)
    except evaluation.EvaluationConfigurationError:
        # Refusing the stale preflight address would satisfy the invariant.
        return

    persisted_id = json.loads(result.state_path.read_text(encoding="utf-8"))["evaluation_id"]
    assert output_dir.name == result.evaluation_id == persisted_id == preflight_id
