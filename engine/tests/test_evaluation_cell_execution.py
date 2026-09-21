"""Guards for the canonical per-cell executor (V6 Phase 3H).

``battle_engine.evaluation_cell_execution`` owns exactly one question --
*"execute this already-planned evaluation cell exactly once"* -- and both
execution routes (serial ``EvaluationService`` dispatch and the
``evaluation_worker`` subprocess) call it.  These tests exercise the
primitive **directly**, without constructing an ``EvaluationService`` at
all, which is the architectural property the phase set out to establish.

The end-to-end behaviour these mappings feed (artifacts, aggregation,
lifecycle, resume) stays covered by ``test_agent_evaluation*.py``; nothing
here duplicates those runs.
"""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import battle_engine.evaluation_cell_execution as cell_execution
import pytest
from battle_engine.agent_test import AgentTestError, InitializationFailureOutcome
from battle_engine.evaluation_cell_execution import (
    CellExecutionResult,
    current_execution_context,
    execute_cell,
)
from battle_engine.evaluation_contracts import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationRequest,
)
from battle_engine.evaluation_identity import agent_identity
from battle_engine.evaluation_planning import build_matrix
from battle_engine.python_runtime import RuntimeDiagnostic

NOP_ACTION = "AgentAction(ActionKindV2.READ, observation.self_anchor)"


def _write_python_agent(root: Path, name: str, action: str = NOP_ACTION) -> Path:
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
    (directory / "agent.py").write_text(
        f"""
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration
class Agent:
    def declare_processes(self): return [ProcessDeclaration("main", 1, 1.0)]
    def reset(self, context): pass
    def act(self, observation): return {action}
def create_agent(): return Agent()
""",
        encoding="utf-8",
    )
    return directory


def _request(tmp_path: Path, **overrides) -> EvaluationRequest:
    defaults = {
        "candidate_id": "candidate",
        "opponent_ids": ("opponent",),
        "seeds": (1,),
        "output_dir": tmp_path / "eval-out",
        "ticks": 8,
        "data_root": tmp_path,
    }
    defaults.update(overrides)
    return EvaluationRequest(**defaults)


@pytest.fixture()
def two_agents(tmp_path: Path) -> Path:
    _write_python_agent(tmp_path, "candidate")
    _write_python_agent(tmp_path, "opponent", action="AgentAction(ActionKindV2.READ, 3)")
    return tmp_path


def _matrix(root: Path, **overrides) -> tuple[EvaluationCell, ...]:
    request = _request(root, **overrides)
    cells = build_matrix(request, "evaluation-under-test")
    for cell in cells:
        cell.artifact_dir.mkdir(parents=True, exist_ok=True)
    return cells


def _planned(root: Path) -> dict[str, dict]:
    from battle_engine.agents import resolve_agent

    return {
        agent_id: agent_identity(resolve_agent(root, agent_id))
        for agent_id in ("candidate", "opponent")
    }


def _cell_for(cells, orientation: str) -> EvaluationCell:
    return next(cell for cell in cells if cell.orientation == orientation)


# ---------------------------------------------------------------------------
# A cell executes with no EvaluationService anywhere in sight
# ---------------------------------------------------------------------------


def test_one_cell_executes_without_constructing_an_evaluation_service(two_agents: Path) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)

    result = execute_cell(cell, 8, two_agents, _planned(two_agents))

    assert isinstance(result, CellExecutionResult)
    assert result.cell.status == "completed"
    assert result.cell.outcome in {"win", "loss", "tie"}
    assert result.cell.match_id and result.cell.result_id
    assert result.cell.ticks_run is not None
    assert result.execution_context is not None
    assert result.cell.execution_context_id == result.execution_context.context_id
    # The cell's own artifacts are the canonical ones a plain `agents test`
    # writes -- referenced, never duplicated, by the evaluation artifact.
    assert (cell.artifact_dir / "result.json").is_file()
    assert (cell.artifact_dir / "replay.jsonl").is_file()


def test_execution_context_is_derived_from_the_cells_own_ruleset(two_agents: Path) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)

    result = execute_cell(cell, 8, two_agents, _planned(two_agents))

    assert result.execution_context is not None
    expected = current_execution_context(cell.rules_compatibility_id)
    assert result.execution_context.context_id == expected.context_id
    assert result.execution_context.rules_compatibility_id == cell.rules_compatibility_id


# ---------------------------------------------------------------------------
# Request construction / orientation mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("orientation", "expected_roles"),
    (
        (ORIENTATION_CANDIDATE_FIRST, ("candidate", "opponent")),
        (ORIENTATION_OPPONENT_FIRST, ("opponent", "candidate")),
    ),
)
def test_orientation_decides_which_role_is_passed_first_to_the_executor(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch, orientation: str, expected_roles
) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, orientation)
    calls: list[tuple] = []
    real = cell_execution.test_agent

    def _spy(agent_id, *, opponent, **kwargs):
        calls.append((agent_id, opponent, kwargs))
        return real(agent_id, opponent=opponent, **kwargs)

    monkeypatch.setattr(cell_execution, "test_agent", _spy)
    execute_cell(cell, 8, two_agents, _planned(two_agents))

    assert len(calls) == 1
    agent_id, opponent, kwargs = calls[0]
    assert (agent_id, opponent) == expected_roles
    # Everything the match's identity depends on is passed through verbatim.
    assert kwargs["seed"] == cell.seed
    assert kwargs["ticks"] == 8
    assert kwargs["timeout"] is None
    assert kwargs["trace"] is False
    assert kwargs["run_dir"] == cell.artifact_dir
    assert kwargs["data_root"] == two_agents
    assert kwargs["ruleset_id"] == cell.rules_compatibility_id


def test_placement_follows_the_role_not_the_physical_slot(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The subject always starts at ``cell.subject_start`` (Sec Placement)."""

    cells = _matrix(two_agents)
    cell = replace(
        _cell_for(cells, ORIENTATION_OPPONENT_FIRST), subject_start=11, opponent_start=37
    )
    captured: dict = {}

    def _spy(agent_id, **kwargs):
        captured.update(kwargs)
        raise AgentTestError(
            RuntimeDiagnostic(code="stop", stage="internal", message="captured")
        )

    monkeypatch.setattr(cell_execution, "test_agent", _spy)
    execute_cell(cell, 8, two_agents, _planned(two_agents))

    # opponent_first: the opponent occupies the first physical slot, so the
    # *tested* agent's start is the opponent's and vice versa.
    assert captured["agent_start"] == 37
    assert captured["opponent_start"] == 11


def test_execution_conditions_are_forwarded_as_explicit_scalars(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)
    captured: dict = {}

    def _spy(agent_id, **kwargs):
        captured.update(kwargs)
        raise AgentTestError(
            RuntimeDiagnostic(code="stop", stage="internal", message="captured")
        )

    monkeypatch.setattr(cell_execution, "test_agent", _spy)
    execute_cell(
        cell,
        8,
        two_agents,
        _planned(two_agents),
        arena_size=256,
        instr_per_tick=5,
        locality_reach=9,
        kill_weight=0.25,
        scheduler_chunk_size=3,
        scheduler_rotate_start=True,
    )

    assert captured["arena_size"] == 256
    assert captured["instr_per_tick"] == 5
    assert captured["locality_reach"] == 9
    assert captured["kill_weight"] == 0.25
    assert captured["scheduler_chunk_size"] == 3
    assert captured["scheduler_rotate_start"] is True


# ---------------------------------------------------------------------------
# Failure mapping
# ---------------------------------------------------------------------------


def test_agent_test_error_maps_to_a_failed_cell_not_an_exception(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)

    def _boom(*args, **kwargs):
        raise AgentTestError(
            RuntimeDiagnostic(
                code="agent_test_internal_error",
                stage="internal",
                message="injected   tool    failure",
            )
        )

    monkeypatch.setattr(cell_execution, "test_agent", _boom)
    result = execute_cell(cell, 8, two_agents, _planned(two_agents))

    assert result.cell.status == "failed"
    assert result.cell.outcome is None
    assert result.cell.error_code == "agent_test_internal_error"
    # Whitespace-collapsed, length-capped -- never the raw exception text.
    assert result.cell.error_message == "injected tool failure"
    # A tool failure still happened in *some* environment, so it is attributed.
    assert result.execution_context is not None
    assert result.cell.execution_context_id == result.execution_context.context_id


@pytest.mark.parametrize(
    ("orientation", "failed_slot_is_subject"),
    (
        (ORIENTATION_CANDIDATE_FIRST, True),
        (ORIENTATION_OPPONENT_FIRST, False),
    ),
)
def test_initialization_failure_is_a_completed_cell_attributed_by_physical_slot(
    two_agents: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
    failed_slot_is_subject: bool,
) -> None:
    """``A`` is always the first-acting slot, so which *role* it denotes
    depends entirely on the cell's orientation (Phase 5 spec Sec H.1)."""

    from battle_engine.agent_test import TESTED_AGENT_SLOT

    cells = _matrix(two_agents)
    cell = _cell_for(cells, orientation)

    def _init_failure(*args, **kwargs):
        return InitializationFailureOutcome(
            agent_id=TESTED_AGENT_SLOT,
            diagnostic=RuntimeDiagnostic(
                agent_id=TESTED_AGENT_SLOT,
                code="agent_reset_failed",
                stage="reset",
                message="deliberate initialization failure",
            ),
        )

    monkeypatch.setattr(cell_execution, "test_agent", _init_failure)
    result = execute_cell(cell, 8, two_agents, _planned(two_agents))

    # Exit-0 semantics: a fact about user agent code, not a tool failure.
    assert result.cell.status == "completed"
    expected = "subject_init_failed" if failed_slot_is_subject else "opponent_init_failed"
    assert result.cell.outcome == expected
    assert result.cell.error_code == "agent_reset_failed"
    assert result.execution_context is not None


def test_group_cell_execution_is_retired_and_raises(two_agents: Path) -> None:
    cells = _matrix(two_agents)
    cell = replace(
        _cell_for(cells, ORIENTATION_CANDIDATE_FIRST),
        roster_agent_ids=("candidate", "opponent"),
        seat_agent_ids=("candidate", "opponent"),
    )
    assert cell.is_group

    with pytest.raises(EvaluationConfigurationError, match="retired"):
        execute_cell(cell, 8, two_agents, _planned(two_agents))


# ---------------------------------------------------------------------------
# Drift
# ---------------------------------------------------------------------------


def test_pre_execution_drift_returns_before_any_match_is_attempted(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)
    planned = _planned(two_agents)
    # Frozen-plan mismatch: the plan claims different bytes than disk holds.
    planned["opponent"] = {**planned["opponent"], "source_sha256": "0" * 64}
    calls: list[object] = []

    def _never(*args, **kwargs):
        calls.append(args)
        raise AssertionError("no match may be attempted after pre-execution drift")

    monkeypatch.setattr(cell_execution, "test_agent", _never)
    result = execute_cell(cell, 8, two_agents, planned)

    assert calls == []
    assert result.cell.status == "drift_detected"
    assert result.cell.error_code == "pre_execution_source_drift"
    assert "source_sha256" in result.cell.error_message
    # Nothing executed, so nothing is attributed to an environment.
    assert result.execution_context is None
    assert result.cell.execution_context_id is None


def test_unresolvable_agent_at_dispatch_time_is_drift_not_a_crash(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)
    planned = _planned(two_agents)

    def _unresolvable(root, agent_id):
        raise EvaluationConfigurationError(f"Unknown agent {agent_id!r}")

    monkeypatch.setattr(cell_execution, "_resolve_python_agent", _unresolvable)
    result = execute_cell(cell, 8, two_agents, planned)

    assert result.cell.status == "drift_detected"
    assert result.cell.error_code == "pre_execution_agent_unresolvable"
    assert result.execution_context is None


def test_post_execution_identity_drift_is_checked_after_the_match_runs(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pre-check passes; only the executor's own recorded metadata
    disagrees, which is the ordering the TOCTOU argument depends on."""

    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)
    planned = _planned(two_agents)
    order: list[str] = []

    real_detect = cell_execution._detect_pre_execution_drift
    real_test_agent = cell_execution.test_agent
    real_post = cell_execution._post_execution_identity_drift

    def _detect(cell_arg, planned_arg, root):
        order.append("pre")
        return real_detect(cell_arg, planned_arg, root)

    def _run(*args, **kwargs):
        order.append("match")
        return real_test_agent(*args, **kwargs)

    def _post(cell_arg, match_result, planned_arg):
        order.append("post")
        assert real_post(cell_arg, match_result, planned_arg) is None
        return {
            "error_code": "post_execution_identity_drift",
            "error_message": "injected executed-identity mismatch",
        }

    monkeypatch.setattr(cell_execution, "_detect_pre_execution_drift", _detect)
    monkeypatch.setattr(cell_execution, "test_agent", _run)
    monkeypatch.setattr(cell_execution, "_post_execution_identity_drift", _post)
    result = execute_cell(cell, 8, two_agents, planned)

    assert order == ["pre", "match", "post"]
    assert result.cell.status == "drift_detected"
    assert result.cell.error_code == "post_execution_identity_drift"
    # Execution really happened here, unlike the pre-execution early return.
    assert result.execution_context is not None
    assert result.cell.execution_context_id == result.execution_context.context_id


def test_initialization_failure_re_checks_source_before_blaming_the_agent(
    two_agents: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sec 7: an initialization failure caused by a durable intervening edit
    is reported as drift, never attributed to the originally frozen agent."""

    from battle_engine.agent_test import TESTED_AGENT_SLOT

    cells = _matrix(two_agents)
    cell = _cell_for(cells, ORIENTATION_CANDIDATE_FIRST)
    planned = _planned(two_agents)
    agent_path = two_agents / "agents" / "candidate" / "agent.py"

    def _edit_then_fail(*args, **kwargs):
        agent_path.write_text(
            agent_path.read_text(encoding="utf-8") + "\n# durable edit\n", encoding="utf-8"
        )
        return InitializationFailureOutcome(
            agent_id=TESTED_AGENT_SLOT,
            diagnostic=RuntimeDiagnostic(
                agent_id=TESTED_AGENT_SLOT,
                code="agent_reset_failed",
                stage="reset",
                message="failed because of the edit",
            ),
        )

    monkeypatch.setattr(cell_execution, "test_agent", _edit_then_fail)
    result = execute_cell(cell, 8, two_agents, planned)

    assert result.cell.status == "drift_detected"
    assert result.cell.error_code == "pre_execution_source_drift"
    assert result.execution_context is not None


# ---------------------------------------------------------------------------
# Dependency direction (the cycle this phase removed)
# ---------------------------------------------------------------------------


def _code_only(source: str) -> str:
    """``source`` with every docstring and comment removed."""

    import io
    import tokenize

    tree = ast.parse(source)
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is None:
                continue
            first = node.body[0]
            doc_lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    kept = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            continue
        if token.start[0] in doc_lines:
            continue
        kept.append(token.string)
    return " ".join(kept)


def _imported_modules(module) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_cell_executor_never_imports_the_service_or_any_upper_layer() -> None:
    forbidden = {
        "battle_engine.agent_evaluation",
        "battle_engine.evaluation_worker",
        "battle_engine.evaluation_history",
        "battle_engine.cli",
        "battle_engine.tournament_cli",
    }
    imported = _imported_modules(cell_execution)
    assert forbidden.isdisjoint(imported), sorted(forbidden & imported)
    source = Path(cell_execution.__file__).read_text(encoding="utf-8")
    assert "EvaluationService" not in _code_only(source)


def test_worker_no_longer_depends_on_the_evaluation_service() -> None:
    """The Phase 3B cycle: the worker used to import ``agent_evaluation``
    (function-locally) purely to call ``EvaluationService._execute_cell``."""

    import battle_engine.evaluation_worker as worker

    imported = _imported_modules(worker)
    assert "battle_engine.agent_evaluation" not in imported
    assert "battle_engine.evaluation_cell_execution" in imported
    body = _code_only(Path(worker.__file__).read_text(encoding="utf-8"))
    assert "EvaluationService" not in body
    assert "_execute_cell" not in body


def test_both_execution_routes_resolve_the_same_canonical_function() -> None:
    import battle_engine.agent_evaluation as facade
    import battle_engine.evaluation_worker as worker

    assert facade.execute_cell is execute_cell
    assert worker.execute_cell is execute_cell


def test_the_service_keeps_no_second_cell_execution_implementation() -> None:
    """Not a delegate, not a shim, not a duplicate -- simply gone."""

    import battle_engine.agent_evaluation as facade

    assert not hasattr(facade.EvaluationService, "_execute_cell")
    assert not hasattr(facade.EvaluationService, "_detect_pre_execution_drift")
    service_source = Path(facade.__file__).read_text(encoding="utf-8")
    assert "def _execute_cell" not in service_source
    # The service no longer reaches the match boundary at all; the only
    # surviving mentions are prose in docstrings and CLI help text.
    assert "test_agent (" not in _code_only(service_source)


def test_current_execution_context_remains_a_facade_re_export() -> None:
    import battle_engine.agent_evaluation as facade

    assert "current_execution_context" in facade.__all__
    assert facade.current_execution_context is current_execution_context
