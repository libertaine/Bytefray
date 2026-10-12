"""Direct coverage for ``battle_engine.evaluation_artifact`` (V6 Phase 3I).

The point of these tests is deliberately narrow: every one of them exercises
evaluation persistence, resume reconstruction, or resume *trust* without ever
constructing an :class:`~battle_engine.agent_evaluation.EvaluationService`.
That is the architectural claim Phase 3I makes -- "how is evaluation state
persisted, trusted, and resumed?" is answerable on its own -- so it is
asserted here rather than only implied.

Service-level integration behavior (checkpoint cadence, dispatch, retry
policy, lifecycle selection) is *not* re-tested here; it stays in
``test_agent_evaluation*.py`` where it already lives.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from battle_engine.agent_test import OPPONENT_SLOT, TESTED_AGENT_SLOT
from battle_engine.config import Config
from battle_engine.evaluation_artifact import (
    RevisionPlanEntry,
    checkpoint_cells,
    expected_cell_match_id,
    load_evaluation_state,
    prior_revision_by_agent_id,
    read_evaluation,
    resolve_cell_from_state,
    resumed_cell_mismatch,
    write_evaluation_state,
)
from battle_engine.evaluation_contracts import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    SCHEMA_NAME,
    SCHEMA_VERSION_V4,
    EffectiveConditions,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationRequest,
    effective_conditions_for,
)
from battle_engine.replay import MatchConfiguration, ReplayHeader, write_replay
from battle_engine.result_model import ReplayReference, ResultEnvelope
from battle_engine.rules import BYTEFRAY_RULESET_ID

ENGINE_SRC = Path(__file__).resolve().parents[1] / "src" / "battle_engine"


# ---------------------------------------------------------------------------
# Dependency direction (Sec 31)
# ---------------------------------------------------------------------------


def test_artifact_module_never_imports_the_service_or_any_upward_layer() -> None:
    """The artifact layer must sit *below* the coordinator, not beside it.

    An import of ``agent_evaluation`` here would reintroduce exactly the
    cycle Phase 3I removed, and would make resume trust unreadable without
    the whole service again.  Checked statically (AST) rather than by
    ``sys.modules`` inspection so a lazy/function-local import cannot hide.
    """

    tree = ast.parse((ENGINE_SRC / "evaluation_artifact.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = {
        "battle_engine.agent_evaluation",
        "battle_engine.evaluation_worker",
        "battle_engine.evaluation_cli",
        "battle_engine.designer",
    }
    assert imported.isdisjoint(forbidden), sorted(imported & forbidden)
    assert not any(name.startswith("battle_engine.evaluation_history") for name in imported)
    assert not any(name.startswith("battle_client") for name in imported)


def test_service_depends_downward_on_the_artifact_layer() -> None:
    tree = ast.parse((ENGINE_SRC / "agent_evaluation.py").read_text(encoding="utf-8"))
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "battle_engine.evaluation_artifact" in modules


# ---------------------------------------------------------------------------
# State loading: the resume compatibility gate (Sec 4)
# ---------------------------------------------------------------------------


def _minimal_state(**overrides) -> dict[str, object]:
    data = {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION_V4,
        "evaluation_id": "evaluation_abc",
        "cells": [],
    }
    data.update(overrides)
    return data


def test_absent_state_file_is_not_an_error(tmp_path: Path) -> None:
    assert load_evaluation_state(tmp_path / "nope.json", "evaluation_abc", SCHEMA_VERSION_V4) == {}


def test_state_load_accepts_a_matching_artifact(tmp_path: Path) -> None:
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(_minimal_state()), encoding="utf-8")
    loaded = load_evaluation_state(path, "evaluation_abc", SCHEMA_VERSION_V4)
    assert loaded["evaluation_id"] == "evaluation_abc"


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"schema": "something.else"}, "unrecognized schema"),
        ({"schema_version": SCHEMA_VERSION_V4 - 1}, "unsupported schema version"),
        ({"evaluation_id": "evaluation_other"}, "does not match this request"),
    ],
)
def test_state_load_fails_closed_on_every_incompatibility(
    tmp_path: Path, overrides: dict[str, object], fragment: str
) -> None:
    """All three gate conditions stay exactly as narrow as they were: same
    schema, the methodology-specific schema version, and an exact
    ``evaluation_id``.  None of them may be broadened into a "close enough"
    resume."""

    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(_minimal_state(**overrides)), encoding="utf-8")
    with pytest.raises(EvaluationConfigurationError) as excinfo:
        load_evaluation_state(path, "evaluation_abc", SCHEMA_VERSION_V4)
    assert fragment in str(excinfo.value)


def test_read_evaluation_accepts_any_current_methodology_version(tmp_path: Path) -> None:
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(_minimal_state()), encoding="utf-8")
    assert read_evaluation(path)["schema"] == SCHEMA_NAME

    path.write_text(json.dumps(_minimal_state(schema_version=999)), encoding="utf-8")
    with pytest.raises(EvaluationConfigurationError):
        read_evaluation(path)


# ---------------------------------------------------------------------------
# Atomic write semantics and canonical serialization (Sec 16)
# ---------------------------------------------------------------------------


def _cell(artifact_dir: Path, *, ordinal: int = 1, schedule_id: str = "sched_1") -> EvaluationCell:
    return EvaluationCell(
        schedule_id=schedule_id,
        subject_role="candidate",
        subject_id="candidate",
        opponent_id="opponent",
        seed=5,
        artifact_dir=artifact_dir,
        matrix_ordinal=ordinal,
    )


def _request(output_dir: Path) -> EvaluationRequest:
    return EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=("opponent",),
        seeds=(5,),
        output_dir=output_dir,
        ticks=12,
    )


def _identity(agent_id: str) -> dict[str, object]:
    return {"agent_id": agent_id, "source_sha256": "0" * 64}


def _write(path: Path, request: EvaluationRequest, cells, matrix, **overrides) -> None:
    conditions: EffectiveConditions = effective_conditions_for(request.ticks, 2)
    kwargs = {
        "planned_identities": {
            agent_id: _identity(agent_id) for agent_id in ("candidate", "opponent")
        },
        "revision_plan": {"candidate": RevisionPlanEntry("agent_revision_c", None)},
        "conditions": conditions,
        "created_at": "2026-01-01T00:00:00.000000Z",
        "lifecycle_state": "running",
        "execution_contexts": (),
    }
    kwargs.update(overrides)
    write_evaluation_state(path, "evaluation_abc", request, cells, matrix, **kwargs)


def test_written_artifact_is_canonically_serialized(tmp_path: Path) -> None:
    """Sorted keys, two-space indent, UTF-8, one trailing newline -- the exact
    shape every previously written ``evaluation.json`` already has."""

    path = tmp_path / "out" / "evaluation.json"
    matrix = [_cell(tmp_path / "m1")]
    _write(path, _request(tmp_path / "out"), matrix, matrix)

    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    assert b"\r\n" not in raw
    text = raw.decode("utf-8")
    data = json.loads(text)
    assert list(data.keys()) == sorted(data.keys())
    assert list(data["cells"][0].keys()) == sorted(data["cells"][0].keys())
    assert text.splitlines()[1].startswith('  "')


def test_write_replaces_in_place_and_leaves_no_temporary_behind(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    path = output_dir / "evaluation.json"
    matrix = [_cell(tmp_path / "m1")]
    _write(path, _request(output_dir), matrix, matrix)
    first = path.read_text(encoding="utf-8")

    _write(path, _request(output_dir), matrix, matrix, lifecycle_state="finished")
    assert path.read_text(encoding="utf-8") != first
    assert sorted(item.name for item in output_dir.iterdir()) == ["evaluation.json"]


def test_cell_artifact_dir_is_persisted_relative_to_the_artifact(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    path = output_dir / "evaluation.json"
    matrix = [_cell(output_dir / "matches" / "0001-cell")]
    _write(path, _request(output_dir), matrix, matrix)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["cells"][0]["artifact_dir"] == str(Path("matches") / "0001-cell")


def test_complete_flag_tracks_the_supplied_lifecycle_state_only(tmp_path: Path) -> None:
    """``complete`` means "scheduling exhausted *and* every persisted cell
    succeeded", i.e. exactly ``lifecycle_state == finished`` -- never merely
    "as many cells as the matrix has"."""

    output_dir = tmp_path / "out"
    path = output_dir / "evaluation.json"
    matrix = [_cell(tmp_path / "m1")]
    for lifecycle, expected in (
        ("running", False),
        ("finished_with_failures", False),
        ("aborted", False),
        ("finished", True),
    ):
        _write(path, _request(output_dir), matrix, matrix, lifecycle_state=lifecycle)
        assert json.loads(path.read_text(encoding="utf-8"))["complete"] is expected


def test_agent_revisions_stay_a_sibling_of_planned_identities(tmp_path: Path) -> None:
    """B1: ``planned_identities`` is persisted byte-for-byte as the identity
    hash saw it, so revision provenance must never be merged into it."""

    output_dir = tmp_path / "out"
    path = output_dir / "evaluation.json"
    matrix = [_cell(tmp_path / "m1")]
    _write(path, _request(output_dir), matrix, matrix)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["planned_identities"]["candidate"] == _identity("candidate")
    assert data["agent_revisions"]["candidate"] == {
        "agent_revision_id": "agent_revision_c",
        "agent_revision_error": None,
    }
    assert "agent_revision_id" not in data["planned_identities"]["candidate"]


# ---------------------------------------------------------------------------
# Checkpoint merge and canonical matrix ordering (Sec 14)
# ---------------------------------------------------------------------------


def test_checkpoint_merge_restores_matrix_order_from_completion_order(tmp_path: Path) -> None:
    """Parallel dispatch resolves cells in wall-clock order; a checkpoint must
    still be a canonically matrix-ordered snapshot."""

    matrix = [
        _cell(tmp_path / f"m{index}", ordinal=index, schedule_id=f"sched_{index}")
        for index in (1, 2, 3)
    ]
    resolved = {
        cell.schedule_id: replace(cell, status="completed", outcome="tie")
        for cell in reversed(matrix)
    }
    merged = checkpoint_cells(resolved, matrix, {})
    assert [cell.schedule_id for cell in merged] == ["sched_1", "sched_2", "sched_3"]


def test_checkpoint_merge_backfills_durable_cells_this_run_never_reached(
    tmp_path: Path,
) -> None:
    """B2: a retry resolves only the retried cell, but the checkpoint it
    triggers must never be *less* complete than what is already on disk."""

    matrix = [
        _cell(tmp_path / f"m{index}", ordinal=index, schedule_id=f"sched_{index}")
        for index in (1, 2)
    ]
    resolved = {"sched_1": replace(matrix[0], status="completed", outcome="win")}
    prior = {
        "sched_2": {
            "status": "completed",
            "outcome": "loss",
            "match_id": "match_prior",
            "execution_context_id": "ctx_prior",
        }
    }
    merged = checkpoint_cells(resolved, matrix, prior)
    assert [cell.schedule_id for cell in merged] == ["sched_1", "sched_2"]
    assert merged[1].outcome == "loss"
    assert merged[1].match_id == "match_prior"
    # A resumed cell's own execution provenance is preserved verbatim, never
    # rewritten to the resuming process's context.
    assert merged[1].execution_context_id == "ctx_prior"


def test_checkpoint_merge_never_fabricates_a_cell_with_no_durable_state(
    tmp_path: Path,
) -> None:
    matrix = [
        _cell(tmp_path / f"m{index}", ordinal=index, schedule_id=f"sched_{index}")
        for index in (1, 2)
    ]
    merged = checkpoint_cells({"sched_1": matrix[0]}, matrix, {})
    assert [cell.schedule_id for cell in merged] == ["sched_1"]


# ---------------------------------------------------------------------------
# Expected match identity reconstruction (Sec 6)
# ---------------------------------------------------------------------------


AGENT_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=self.arena_size - 1, share=1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor)


def create_agent():
    return Agent()
"""


def _python_agent(root: Path, name: str) -> None:
    """A real on-disk agent.

    ``canonical_match_id`` reads ``spec.source_path`` from disk at call time,
    so these tests need genuine agent directories rather than stub specs --
    the distinct trailing marker is what makes the two agents' source content
    (and therefore the derived id) differ.
    """

    directory = root / "agents" / name
    directory.mkdir(parents=True, exist_ok=True)
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
        AGENT_SOURCE + f"\n# {name}\n", encoding="utf-8"
    )


def test_expected_match_id_is_orientation_sensitive_via_physical_slot_order(
    tmp_path: Path,
) -> None:
    """``canonical_match_id`` is sensitive to entrant *positional* order, so
    an ``opponent_first`` cell must recompute a different id than a
    ``candidate_first`` one -- otherwise every completed opponent-first cell
    would resume into a false ``resumed_result_mismatch``."""

    from battle_engine.agents import resolve_agent

    _python_agent(tmp_path, "cand")
    _python_agent(tmp_path, "opp")
    candidate = resolve_agent(tmp_path, "cand")
    opponent = resolve_agent(tmp_path, "opp")
    common = {
        "seed": 7,
        "ticks": 12,
        "ruleset_id": BYTEFRAY_RULESET_ID,
        "subject_start": 0,
        "opponent_start": 0,
    }
    first = expected_cell_match_id(
        candidate,
        "cand",
        opponent,
        "opp",
        orientation=ORIENTATION_CANDIDATE_FIRST,
        **common,
    )
    second = expected_cell_match_id(
        candidate,
        "cand",
        opponent,
        "opp",
        orientation=ORIENTATION_OPPONENT_FIRST,
        **common,
    )
    assert first != second
    # Deterministic: the same inputs always reproduce the same id.
    assert first == expected_cell_match_id(
        candidate,
        "cand",
        opponent,
        "opp",
        orientation=ORIENTATION_CANDIDATE_FIRST,
        **common,
    )


def test_expected_match_id_tracks_every_identity_bearing_input(tmp_path: Path) -> None:
    from battle_engine.agents import resolve_agent

    _python_agent(tmp_path, "cand")
    _python_agent(tmp_path, "opp")
    candidate = resolve_agent(tmp_path, "cand")
    opponent = resolve_agent(tmp_path, "opp")
    base = {
        "subject_spec": candidate,
        "subject_id": "cand",
        "opponent_spec": opponent,
        "opponent_id": "opp",
        "seed": 7,
        "ticks": 12,
        "orientation": ORIENTATION_CANDIDATE_FIRST,
        "ruleset_id": BYTEFRAY_RULESET_ID,
        "subject_start": 0,
        "opponent_start": 0,
    }
    reference = expected_cell_match_id(**base)
    defaults = Config()
    for field, value in (
        ("seed", 8),
        ("ticks", 13),
        ("subject_start", 3),
        ("opponent_start", 3),
        ("arena_size", defaults.arena_size * 2),
        ("instr_per_tick", defaults.instr_per_tick + 1),
        ("kill_weight", defaults.weights.kill + 1.0),
    ):
        assert expected_cell_match_id(**{**base, field: value}) != reference, field

    # `None` means "whatever Config() itself defaults to" -- an omitted
    # parameter must reproduce the exact historical id, never a new one.
    assert (
        expected_cell_match_id(
            **{
                **base,
                "arena_size": defaults.arena_size,
                "instr_per_tick": defaults.instr_per_tick,
                "kill_weight": defaults.weights.kill,
            }
        )
        == reference
    )


# ---------------------------------------------------------------------------
# Resumed-cell trust verification (Sec 5)
# ---------------------------------------------------------------------------


def _replay(path: Path, *, match_id: str, result_id: str, ruleset_id: str | None) -> str:
    write_replay(
        path,
        [
            ReplayHeader(
                MatchConfiguration(64),
                match_id=match_id,
                result_id=result_id,
                ruleset_id=ruleset_id,
            )
        ],
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _envelope(
    *,
    digest: str,
    filename: str = "replay.jsonl",
    match_id: str = "match_x",
    result_id: str = "result_x",
    seed: int = 5,
    entrant_order: tuple[str, ...] = (TESTED_AGENT_SLOT, OPPONENT_SLOT),
    ruleset_id: str | None = BYTEFRAY_RULESET_ID,
) -> ResultEnvelope:
    return ResultEnvelope(
        result_id=result_id,
        match_id=match_id,
        mode="b2",
        winner="tie",
        termination_reason="tick_limit",
        ticks=2,
        entrants=tuple({"agent_id": slot} for slot in entrant_order),
        reproducibility={"seed": seed},
        replay=ReplayReference("r", digest, filename),
        ruleset_id=ruleset_id,
    )


def test_intact_evidence_verifies(tmp_path: Path) -> None:
    digest = _replay(
        tmp_path / "replay.jsonl",
        match_id="match_x",
        result_id="result_x",
        ruleset_id=BYTEFRAY_RULESET_ID,
    )
    assert resumed_cell_mismatch(_envelope(digest=digest), _cell(tmp_path), "match_x") is None


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"entrant_order": (OPPONENT_SLOT, TESTED_AGENT_SLOT)}, "entrant order"),
        ({"seed": 6}, "does not match the scheduled cell's"),
        ({"match_id": "match_other"}, "match ID"),
        ({"filename": "../../escape.jsonl"}, "escapes"),
    ],
)
def test_each_trust_check_is_reported_distinctly(
    tmp_path: Path, kwargs: dict[str, object], fragment: str
) -> None:
    """Every mismatch keeps its own diagnostic; none of them may collapse into
    a generic "resume failed"."""

    digest = _replay(
        tmp_path / "replay.jsonl",
        match_id="match_x",
        result_id="result_x",
        ruleset_id=BYTEFRAY_RULESET_ID,
    )
    reason = resumed_cell_mismatch(_envelope(digest=digest, **kwargs), _cell(tmp_path), "match_x")
    assert reason is not None and fragment in reason


def test_a_missing_replay_reference_is_rejected(tmp_path: Path) -> None:
    digest = _replay(
        tmp_path / "replay.jsonl",
        match_id="match_x",
        result_id="result_x",
        ruleset_id=BYTEFRAY_RULESET_ID,
    )
    envelope = replace(_envelope(digest=digest), replay=None)
    reason = resumed_cell_mismatch(envelope, _cell(tmp_path), "match_x")
    assert reason is not None and "no replay reference" in reason


def test_a_tampered_replay_fails_the_digest_check(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.jsonl"
    digest = _replay(
        replay_path, match_id="match_x", result_id="result_x", ruleset_id=BYTEFRAY_RULESET_ID
    )
    replay_path.write_bytes(replay_path.read_bytes() + b'{"type":"tampered"}\n')
    reason = resumed_cell_mismatch(_envelope(digest=digest), _cell(tmp_path), "match_x")
    assert reason is not None and "replay verification failed" in reason


def test_an_absent_replay_file_is_rejected(tmp_path: Path) -> None:
    reason = resumed_cell_mismatch(
        _envelope(digest="0" * 64), _cell(tmp_path), "match_x"
    )
    assert reason is not None


@pytest.mark.parametrize(
    ("header_match_id", "header_result_id", "fragment"),
    [
        ("match_other", "result_x", "replay header match ID"),
        ("match_x", "result_other", "replay header result ID"),
    ],
)
def test_replay_header_identity_must_agree_with_the_result_envelope(
    tmp_path: Path, header_match_id: str, header_result_id: str, fragment: str
) -> None:
    digest = _replay(
        tmp_path / "replay.jsonl",
        match_id=header_match_id,
        result_id=header_result_id,
        ruleset_id=BYTEFRAY_RULESET_ID,
    )
    reason = resumed_cell_mismatch(_envelope(digest=digest), _cell(tmp_path), "match_x")
    assert reason is not None and fragment in reason


# ---------------------------------------------------------------------------
# Persisted cell reconstruction and status reuse (Sec 7/9)
# ---------------------------------------------------------------------------


def test_a_non_terminal_persisted_status_is_rerun(tmp_path: Path) -> None:
    resolved = resolve_cell_from_state(
        _cell(tmp_path), {"status": "pending"}, {}, _request(tmp_path)
    )
    assert resolved is None


@pytest.mark.parametrize("status", ["failed", "corrupted", "drift_detected"])
def test_unsuccessful_terminal_statuses_are_reconstructed_verbatim(
    tmp_path: Path, status: str
) -> None:
    """Whether any of these is *retried* is coordinator policy; the artifact
    layer only reconstructs what was recorded, with no nested-artifact read
    (there is no scored result to verify)."""

    previous = {
        "status": status,
        "outcome": None,
        "error_code": "some_code",
        "error_message": "some message",
        "execution_context_id": "ctx_prior",
    }
    resolved = resolve_cell_from_state(_cell(tmp_path), previous, {}, _request(tmp_path))
    assert resolved is not None
    assert resolved.status == status
    assert resolved.error_code == "some_code"
    assert resolved.execution_context_id == "ctx_prior"


@pytest.mark.parametrize("outcome", ["subject_init_failed", "opponent_init_failed"])
def test_a_completed_initialization_failure_is_reusable_without_a_result(
    tmp_path: Path, outcome: str
) -> None:
    """An initialization failure never produced a ``result.json``, so demanding
    one would falsely corrupt every resumed init-failure cell."""

    assert not (tmp_path / "result.json").exists()
    resolved = resolve_cell_from_state(
        _cell(tmp_path),
        {"status": "completed", "outcome": outcome},
        {},
        _request(tmp_path),
    )
    assert resolved is not None
    assert resolved.status == "completed"
    assert resolved.outcome == outcome
    assert resolved.error_code is None


def test_a_scored_completed_cell_without_a_result_becomes_corrupted(tmp_path: Path) -> None:
    resolved = resolve_cell_from_state(
        _cell(tmp_path),
        {"status": "completed", "outcome": "win"},
        {},
        _request(tmp_path),
    )
    assert resolved is not None
    assert resolved.status == "corrupted"
    assert resolved.error_code == "resumed_result_missing"


def test_a_scored_completed_cell_with_unreadable_evidence_becomes_corrupted(
    tmp_path: Path,
) -> None:
    (tmp_path / "result.json").write_text("{not json", encoding="utf-8")
    resolved = resolve_cell_from_state(
        _cell(tmp_path),
        {"status": "completed", "outcome": "win"},
        {},
        _request(tmp_path),
    )
    assert resolved is not None
    assert resolved.status == "corrupted"
    assert resolved.error_code == "resumed_result_unreadable"


# ---------------------------------------------------------------------------
# Revision / provenance restoration (Sec 11)
# ---------------------------------------------------------------------------


def test_prior_revisions_are_recovered_by_role_position() -> None:
    """``agent_revisions`` is a role-keyed sibling of ``planned_identities``
    carrying no ``agent_id`` of its own, so recovery correlates positionally
    against the prior artifact's own id lists."""

    prior = {
        "candidate_id": "cand",
        "baseline_id": "base",
        "opponent_ids": ["opp_a", "opp_b"],
        "agent_revisions": {
            "candidate": {"agent_revision_id": "rev_c", "agent_revision_error": None},
            "baseline": {"agent_revision_id": "rev_b", "agent_revision_error": "warned"},
            "opponents": [
                {"agent_revision_id": "rev_1", "agent_revision_error": None},
                {"agent_revision_id": "rev_2", "agent_revision_error": None},
            ],
        },
    }
    recovered = prior_revision_by_agent_id(prior)
    assert recovered == {
        "cand": RevisionPlanEntry("rev_c", None),
        "base": RevisionPlanEntry("rev_b", "warned"),
        "opp_a": RevisionPlanEntry("rev_1", None),
        "opp_b": RevisionPlanEntry("rev_2", None),
    }


@pytest.mark.parametrize(
    "prior",
    [
        {},
        {"candidate_id": "cand"},
        {"candidate_id": "cand", "agent_revisions": "not-a-mapping"},
        {"candidate_id": "cand", "agent_revisions": {"candidate": {"agent_revision_id": 7}}},
        {"candidate_id": "cand", "agent_revisions": {"candidate": None}},
    ],
)
def test_revision_recovery_degrades_to_nothing_recorded_yet(prior: dict[str, object]) -> None:
    """A malformed or pre-revision artifact must archive fresh, never raise --
    persisted artifacts are untrusted input."""

    assert prior_revision_by_agent_id(prior) == {}
