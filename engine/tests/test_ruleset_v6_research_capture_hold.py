"""V6 E2: the capture-hold research Ruleset
(``bytefray-rules-6-research-capture-hold-k2``) -- policy, identity,
registration, evaluation plumbing, product isolation, and serialization.

docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec J.2 and J.5; the
gameplay semantics themselves are covered by
``test_e2_capture_hold_semantics.py`` and the K=1 byte-identity freeze by
``test_v4_k1_capture_byte_identity.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine import agent_test, cli, evaluation_cli, tournament_cli
from battle_engine.agent_evaluation import (
    EvaluationConfigurationError,
    EvaluationRequest,
    EvaluationService,
)
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.evaluation_cli import main as evaluate_main
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    IDENTITY_VERSION_V4,
    SCHEMA_VERSION_V4,
    STANDARD_V4_ARENA_SIZE,
    arena_alignment_mode_for_ruleset,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_capture_hold_methodology,
    is_ruleset_v6_research_scale_methodology,
    is_ruleset_v6_research_scale_move_methodology,
    is_ruleset_v6_research_scale_move_proportional_methodology,
    resolve_evaluation_ruleset_id,
    resolved_arena_alignment_mode,
    resolved_identity_version,
    resolved_schema_version,
)
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    OverlappingCoreError,
    canonical_match_id,
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import (
    KillDeathEvent,
    MatchResult,
    ReplayHeader,
    RuntimeEvent,
    TickSnapshot,
    iter_replay,
)
from battle_engine.rules import BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID as RULES_E2_ID
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    ACTIVE_RESEARCH_RULESET_IDS,
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    HISTORICAL_READONLY_RULESET_IDS,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    PUBLIC_STABLE_RULESET_IDS,
    RETIRED_RESEARCH_RULESET_IDS,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2,
    RULESET_V6_RESEARCH_SCALE,
    RulesetPolicy,
    resolve_omitted_ruleset_for_agents,
    resolve_omitted_ruleset_id,
    resolve_ruleset_policy,
)

from app.services.ruleset_options import (
    DESIGNER_RULESET_OPTIONS,
    EVALUATION_RULESET_OPTIONS,
    SIMPLE_RULESET_OPTIONS,
)

E2_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
RS_ID = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
E2 = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2
RS = RULESET_V6_RESEARCH_SCALE

IDLE_AGENT_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, 0)


def create_agent():
    return Agent()
"""

# CompetentGlobalSniperProbe (test_v4_exploit_characterization.py): under E2
# its mirror completes a capture on tick 2 (review Sec D.3), so a match run
# with it exercises onset, completion, and onset-attributed kill credit.
PROBE_AGENT_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.context = context
        self.step = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="sniper", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        if not obs.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.READ, operand=0)
        target = (obs.visible_enemy_anchor_addresses[0] + self.step) % self.context.arena_size
        self.step = (self.step + 1) % 8
        return AgentAction(ActionKindV2.WRITE, operand=target, value=1)


def create_agent():
    return Agent()
"""


def _write_agent(root: Path, name: str, source: str = IDLE_AGENT_SOURCE) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_bytes(
        json.dumps(
            {
                "name": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ).encode()
    )
    (agent_dir / "agent.py").write_bytes(source.encode())


def _match_request(
    root: Path,
    ruleset_id: str,
    *,
    names: tuple[str, str] = ("probe_a", "probe_b"),
    run_label: str,
    starts: tuple[int, int] | None = None,
    max_ticks: int = 50,
) -> MatchRequest:
    seed = 42
    resolved_starts = starts or resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=512,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    return MatchRequest(
        config=Config(seed=seed, arena_size=512, instr_per_tick=8),
        entrants=tuple(
            MatchEntrant.python(seat, name, start, resolve_agent(root, name))
            for seat, name, start in zip(("A", "B"), names, resolved_starts, strict=True)
        ),
        max_ticks=max_ticks,
        replay_path=root / "runs" / run_label / "replay.jsonl",
        verbose=False,
        ruleset_id=ruleset_id,
    )


def _evaluation_request(
    root: Path, *, arena_size: int | None, ruleset_id: str = E2_ID, out: str = "eval-out"
) -> EvaluationRequest:
    return EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=["opponent"],
        seeds=(1,),
        ticks=5,
        arena_size=arena_size,
        ruleset_id=ruleset_id,
        output_dir=root / out,
        data_root=root,
    )


def _ruleset_choices(parser: argparse.ArgumentParser) -> list[str]:
    (action,) = [item for item in parser._actions if "--ruleset" in item.option_strings]
    assert action.choices is not None
    return list(action.choices)


# ---------------------------------------------------------------------------
# Policy field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [0, -1, True, False, 2.0, "2", None])
def test_capture_hold_ticks_rejects_non_integers_bools_and_values_below_one(value: Any) -> None:
    with pytest.raises(ValueError, match="capture_hold_ticks"):
        RulesetPolicy(ruleset_id="test-only", capture_hold_ticks=value)


@pytest.mark.parametrize("value", [1, 2, 3, 1000])
def test_capture_hold_ticks_accepts_integers_from_one(value: int) -> None:
    assert RulesetPolicy(ruleset_id="test-only", capture_hold_ticks=value).capture_hold_ticks == value


def test_capture_hold_ticks_defaults_to_one() -> None:
    assert RulesetPolicy(ruleset_id="test-only").capture_hold_ticks == 1


def test_every_registered_policy_keeps_k1_except_e2() -> None:
    assert {ruleset_id: policy.capture_hold_ticks for ruleset_id, policy in _RULESET_POLICIES.items()} == {
        ruleset_id: (2 if ruleset_id == E2_ID else 1) for ruleset_id in _RULESET_POLICIES
    }


# ---------------------------------------------------------------------------
# Ruleset definition and registration
# ---------------------------------------------------------------------------


def test_identity_string_and_single_source() -> None:
    assert E2_ID == "bytefray-rules-6-research-capture-hold-k2"
    assert RULES_E2_ID is E2_ID


def test_e2_differs_from_research_scale_control_in_exactly_one_gameplay_field() -> None:
    differing = {
        field.name
        for field in fields(RulesetPolicy)
        if getattr(E2, field.name) != getattr(RS, field.name)
    }
    assert differing == {"ruleset_id", "capture_hold_ticks"}
    assert (RS.capture_hold_ticks, E2.capture_hold_ticks) == (1, 2)
    assert replace(E2, ruleset_id=RS.ruleset_id, capture_hold_ticks=RS.capture_hold_ticks) == RS
    # An independent literal, not the control object itself.
    assert E2 is not RS


def test_e2_is_registered_and_executable_on_the_process_runtime() -> None:
    assert resolve_ruleset_policy(E2_ID) is E2
    assert E2_ID in PROCESS_RULESET_IDS
    assert E2.supported_runtime_kinds == frozenset({"python"})
    assert E2.supported_python_api_versions == frozenset({2})


def test_lifecycle_sets_partition_every_executable_policy() -> None:
    executable_lifecycles = {
        "public_stable": PUBLIC_STABLE_RULESET_IDS,
        "active_research": ACTIVE_RESEARCH_RULESET_IDS,
        "retired_research": RETIRED_RESEARCH_RULESET_IDS,
    }
    for ruleset_id in _RULESET_POLICIES:
        memberships = [name for name, ids in executable_lifecycles.items() if ruleset_id in ids]
        assert len(memberships) == 1, (ruleset_id, memberships)
    # ...and no executable lifecycle names an identity that is not executable.
    assert set().union(*executable_lifecycles.values()) == set(_RULESET_POLICIES)
    assert HISTORICAL_READONLY_RULESET_IDS.isdisjoint(_RULESET_POLICIES)
    assert E2_ID in ACTIVE_RESEARCH_RULESET_IDS


def test_same_request_under_control_and_e2_has_distinct_match_ids(tmp_path: Path) -> None:
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name, PROBE_AGENT_SOURCE)
    control = _match_request(tmp_path, RS_ID, run_label="same")
    treatment = _match_request(tmp_path, E2_ID, run_label="same")
    # Precondition: the two requests differ in nothing but the Ruleset.
    assert replace(treatment, ruleset_id=RS_ID) == control
    assert canonical_match_id(control) != canonical_match_id(treatment)


def test_overlapping_seeded_cores_fail_closed_under_e2(tmp_path: Path) -> None:
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name, PROBE_AGENT_SOURCE)
    for ruleset_id in (RS_ID, E2_ID):
        request = _match_request(
            tmp_path, ruleset_id, run_label=f"overlap-{ruleset_id}", starts=(100, 104)
        )
        with pytest.raises(OverlappingCoreError):
            NativeMatchService().run(request)
        assert request.replay_path is not None and not request.replay_path.exists()


# ---------------------------------------------------------------------------
# Product isolation
# ---------------------------------------------------------------------------


def test_e2_is_never_automatic() -> None:
    assert E2_ID not in OMITTED_RULESET_CANDIDATES
    assert E2_ID not in PUBLIC_STABLE_RULESET_IDS
    roster = [{"agent_id": "x", "kind": "python", "api_version": 2}]
    assert resolve_omitted_ruleset_for_agents(None, roster) == BYTEFRAY_RULESET_V4_ID
    assert resolve_omitted_ruleset_id(None, ["python"]) == BYTEFRAY_RULESET_V4_ID
    assert resolve_evaluation_ruleset_id(None) == BYTEFRAY_RULESET_V4_ID


def test_e2_is_not_selectable_from_product_run_surfaces(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _ruleset_choices(agent_test._parser()) == [BYTEFRAY_RULESET_V4_ID]
    assert _ruleset_choices(tournament_cli._parser()) == [BYTEFRAY_RULESET_V4_ID]
    # `bytefray run` builds its parser inside parse_args.
    with pytest.raises(SystemExit) as excinfo:
        cli.parse_args(["--ruleset", E2_ID])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_e2_is_absent_from_every_designer_ruleset_option() -> None:
    for options in (SIMPLE_RULESET_OPTIONS, EVALUATION_RULESET_OPTIONS, DESIGNER_RULESET_OPTIONS):
        assert [option.ruleset_id for option in options] == [BYTEFRAY_RULESET_V4_ID]


def test_e2_is_explicitly_selectable_from_agents_evaluate() -> None:
    assert E2_ID in _ruleset_choices(evaluation_cli._parser())


# ---------------------------------------------------------------------------
# Evaluation plumbing
# ---------------------------------------------------------------------------


def test_methodology_predicates_classify_e2() -> None:
    assert is_ruleset_v6_research_capture_hold_methodology(E2_ID)
    for other in (BYTEFRAY_RULESET_V4_ID, RS_ID, *RETIRED_RESEARCH_RULESET_IDS):
        assert not is_ruleset_v6_research_capture_hold_methodology(other)
    assert is_ruleset_v4_derived_methodology(E2_ID)
    assert not is_ruleset_v4_methodology(E2_ID)
    assert not is_ruleset_v6_research_scale_methodology(E2_ID)
    assert not is_ruleset_v6_research_scale_move_methodology(E2_ID)
    assert not is_ruleset_v6_research_scale_move_proportional_methodology(E2_ID)


def test_alignment_label_is_distinct_and_identity_schema_are_seven() -> None:
    label = arena_alignment_mode_for_ruleset(E2_ID)
    assert label == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2
    assert label == "ruleset_v6_research_capture_hold_k2_seeded_placements"
    assert label not in {
        EVALUATION_ARENA_ALIGNMENT_MODE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    }
    assert (
        resolved_arena_alignment_mode(False, is_v6_research_capture_hold_methodology=True)
        == label
    )
    assert (
        resolved_identity_version(False, is_v6_research_capture_hold_methodology=True)
        == IDENTITY_VERSION_V4
        == 7
    )
    assert (
        resolved_schema_version(False, is_v6_research_capture_hold_methodology=True)
        == SCHEMA_VERSION_V4
        == 7
    )


def test_capture_hold_flag_cannot_be_passed_positionally() -> None:
    # Keyword-only by design: a positional call can never set it by accident.
    for resolver in (resolved_arena_alignment_mode, resolved_identity_version, resolved_schema_version):
        with pytest.raises(TypeError):
            resolver(False, False, False, False, False, False, True)  # type: ignore[misc]


def test_omitted_arena_resolves_to_512_not_the_config_default(tmp_path: Path) -> None:
    request = _evaluation_request(tmp_path, arena_size=None)
    assert Config().arena_size == 4096  # the silent-fallback trap this guards (F-4)
    assert request.resolved_arena_size == STANDARD_V4_ARENA_SIZE == 512
    assert request.is_v6_research_capture_hold_methodology
    assert request.resolved_arena_alignment_mode == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2


def test_omitted_arena_evaluation_runs_under_e2_at_512(tmp_path: Path) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    EvaluationService().run(_evaluation_request(tmp_path, arena_size=None))

    data = json.loads((tmp_path / "eval-out" / "evaluation.json").read_text(encoding="utf-8"))
    assert (
        data["schema_version"],
        data["identity_version"],
        data["rules_compatibility_id"],
        data["arena_alignment_mode"],
        data["effective_conditions"]["arena_size"],
    ) == (7, 7, E2_ID, EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2, 512)
    starts = resolve_direct_match_starts(
        ruleset_id=E2_ID, arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=1
    )
    # Seeded placement with the paired orientation swap (the shared v4-derived branch).
    assert [
        (cell["orientation"], cell["placement_id"], cell["subject_start"], cell["opponent_start"])
        for cell in data["cells"]
    ] == [
        ("candidate_first", "seeded-1", starts[0], starts[1]),
        ("opponent_first", "seeded-1", starts[1], starts[0]),
    ]
    # Each cell really executed under E2, not merely under an E2 label.
    for cell in data["cells"]:
        assert cell["status"] == "completed"
        result = json.loads(
            (tmp_path / "eval-out" / cell["artifact_dir"] / "result.json").read_text(encoding="utf-8")
        )
        assert result["ruleset_id"] == E2_ID


@pytest.mark.parametrize("arena_size", [63, 65537])
def test_out_of_range_arena_is_rejected(tmp_path: Path, arena_size: int) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    with pytest.raises(EvaluationConfigurationError, match="outside the"):
        EvaluationService().run(_evaluation_request(tmp_path, arena_size=arena_size))
    assert not (tmp_path / "eval-out" / "evaluation.json").exists()


@pytest.mark.parametrize("arena_size", [64, 65536])
def test_research_range_boundaries_are_accepted(tmp_path: Path, arena_size: int) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    EvaluationService().run(_evaluation_request(tmp_path, arena_size=arena_size))
    data = json.loads((tmp_path / "eval-out" / "evaluation.json").read_text(encoding="utf-8"))
    assert data["effective_conditions"]["arena_size"] == arena_size


def test_evaluation_ids_differ_between_control_and_e2(tmp_path: Path) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    control = EvaluationService().run(
        _evaluation_request(tmp_path, arena_size=512, ruleset_id=RS_ID, out="rs")
    )
    treatment = EvaluationService().run(_evaluation_request(tmp_path, arena_size=512, out="e2"))
    assert control.evaluation_id != treatment.evaluation_id


def test_evaluate_cli_selects_e2_explicitly_with_default_arena(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    base = ["candidate", "--opponents", "opponent", "--ruleset", E2_ID, "--seeds", "1", "--ticks", "5"]

    assert evaluate_main([*base, "--output", str(tmp_path / "ok")]) == 0
    data = json.loads((tmp_path / "ok" / "evaluation.json").read_text(encoding="utf-8"))
    assert data["effective_conditions"]["arena_size"] == 512
    assert data["arena_alignment_mode"] == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2

    assert evaluate_main([*base, "--arena-size", "65537", "--output", str(tmp_path / "bad")]) != 0
    assert not (tmp_path / "bad" / "evaluation.json").exists()
    capsys.readouterr()


# ---------------------------------------------------------------------------
# Determinism and serialization (Sec J.5)
# ---------------------------------------------------------------------------


def _run_probe_mirror(root: Path, ruleset_id: str, label: str) -> tuple[Path, Any]:
    for name in ("probe_a", "probe_b"):
        if not (root / "agents" / name).exists():
            _write_agent(root, name, PROBE_AGENT_SOURCE)
    request = _match_request(root, ruleset_id, run_label=label)
    result = NativeMatchService().run(request)
    assert request.replay_path is not None
    return request.replay_path, result


def _key_shapes(value: Any) -> Any:
    """Every JSON key path in one record, values ignored."""

    if isinstance(value, dict):
        return {key: _key_shapes(item) for key, item in value.items()}
    if isinstance(value, list):
        shapes = [_key_shapes(item) for item in value]
        return sorted({json.dumps(shape, sort_keys=True) for shape in shapes})
    return None


def _replay_shapes(replay_path: Path) -> list[Any]:
    lines = replay_path.read_bytes().decode("utf-8").splitlines()
    return sorted({json.dumps(_key_shapes(json.loads(line)), sort_keys=True) for line in lines})


def test_same_e2_request_twice_is_byte_identical(tmp_path: Path) -> None:
    first_path, first = _run_probe_mirror(tmp_path / "one", E2_ID, "run")
    second_path, second = _run_probe_mirror(tmp_path / "two", E2_ID, "run")

    first_bytes = first_path.read_bytes()
    assert first_bytes == second_path.read_bytes()
    assert b"\r" not in first_bytes
    assert first.result_id == second.result_id
    assert first.match_id == second.match_id
    assert first.replay_sha256 == hashlib.sha256(first_bytes).hexdigest()
    # The match really exercised a held capture: onset on tick 1,
    # completion (attributed to the onset capturer) on tick 2.
    assert (first.winner, first.ticks_run, first.termination_reason.value) == (
        "A",
        2,
        "last_agent_standing",
    )


def test_e2_replay_is_read_by_the_current_reader_with_no_new_vocabulary(tmp_path: Path) -> None:
    replay_path, _ = _run_probe_mirror(tmp_path, E2_ID, "run")

    records = list(iter_replay(replay_path))
    header = records[0]
    assert isinstance(header, ReplayHeader)
    assert (header.ruleset_id, header.schema_version) == (E2_ID, 4)
    assert isinstance(records[-1], MatchResult)
    events = [
        (record.tick, event)
        for record in records
        if isinstance(record, TickSnapshot)
        for event in record.events
    ]
    assert events == [(2, KillDeathEvent("kill", "B", "A"))]
    assert all(isinstance(event, (KillDeathEvent, RuntimeEvent)) for _, event in events)
    result = json.loads((replay_path.parent / "result.json").read_text(encoding="utf-8"))
    assert result["ruleset_id"] == E2_ID
    assert [entrant["termination_reason"] for entrant in result["entrants"]] == [
        None,
        "core_captured",
    ]
    assert [entrant["statistics"]["kills"] for entrant in result["entrants"]] == [1, 0]


def test_e2_replay_and_result_have_exactly_the_control_shape(tmp_path: Path) -> None:
    # No replay, event, or result field is added: every record of an E2
    # replay (and its result.json) has the same key structure as the
    # research-scale control's for the same request. Both runs end in a
    # capture (tick 1 under the control, tick 2 under E2), so kill events
    # are present on both sides.
    control_path, _ = _run_probe_mirror(tmp_path / "rs", RS_ID, "run")
    treatment_path, _ = _run_probe_mirror(tmp_path / "e2", E2_ID, "run")

    assert _replay_shapes(treatment_path) == _replay_shapes(control_path)
    control_result = json.loads((control_path.parent / "result.json").read_text(encoding="utf-8"))
    treatment_result = json.loads(
        (treatment_path.parent / "result.json").read_text(encoding="utf-8")
    )
    assert _key_shapes(treatment_result) == _key_shapes(control_result)
    assert treatment_result["schema_version"] == control_result["schema_version"]
