"""V6 E4: the mirrored-pass-order research Rulesets -- policy, identity,
registration, evaluation plumbing, product isolation, determinism, and
serialization.

docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec I-K and
docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md. Two treatments,
each differing from its E3 parent only in
``RulesetPolicy.scheduler_pass_order``:

* primary ``bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes``,
  parent ``bytefray-rules-6-research-capture-hold-k2-disruption-slot1``
  (historical T-E3, K=2);
* companion ``bytefray-rules-6-research-disruption-slot1-mirrored-passes``,
  parent ``bytefray-rules-6-research-disruption-slot1`` (historical T-E3K1, K=1).

The scheduler semantics themselves are covered by
``test_e4_mirrored_pass_order_semantics.py`` and the ``"forward"``-path
byte-identity freeze by ``test_v6_e4_parent_byte_identity.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine import agent_test, cli, evaluation_cli, match_service, tournament_cli
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
    EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD,
    EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD,
    EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    IDENTITY_VERSION_V4,
    SCHEMA_VERSION_V4,
    STANDARD_V4_ARENA_SIZE,
    arena_alignment_mode_for_ruleset,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_capture_hold_disruption_slot_methodology,
    is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology,
    is_ruleset_v6_research_capture_hold_methodology,
    is_ruleset_v6_research_disruption_slot_methodology,
    is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology,
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
    _effective_ruleset_policy,
    canonical_match_id,
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.rules import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID as RULES_PRIMARY_ID,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID as RULES_COMPANION_ID,
)
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    ACTIVE_RESEARCH_RULESET_IDS,
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    HISTORICAL_READONLY_RULESET_IDS,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    PUBLIC_STABLE_RULESET_IDS,
    RETIRED_RESEARCH_RULESET_IDS,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES,
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
from tools.research.v6.experiment_harness import prepare_benchmark_data_root

PRIMARY_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID
COMPANION_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID
T_E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
T_E3K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
E2_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
RS_ID = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
E4_IDS = (PRIMARY_ID, COMPANION_ID)

# (treatment, parent) -- the two one-field comparisons E4 rests on.
TREATMENT_PARENT = (
    (
        RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES,
        RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
    ),
    (RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES, RULESET_V6_RESEARCH_DISRUPTION_SLOT1),
)
PARENT_ID = {PRIMARY_ID: T_E3_ID, COMPANION_ID: T_E3K1_ID}
ALIGNMENT_LABEL = {
    PRIMARY_ID: EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES,
    COMPANION_ID: EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES,
}

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
    names: tuple[str, str],
    run_label: str,
    seed: int = 42,
    starts: tuple[int, int] | None = None,
    max_ticks: int = 50,
) -> MatchRequest:
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
    root: Path, *, arena_size: int | None, ruleset_id: str, out: str = "eval-out"
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


def test_scheduler_pass_order_modes_are_exactly_forward_and_mirrored() -> None:
    assert RulesetPolicy.SCHEDULER_PASS_ORDER_MODES == frozenset({"forward", "mirrored"})


def test_scheduler_pass_order_defaults_to_forward() -> None:
    assert RulesetPolicy(ruleset_id="test-only").scheduler_pass_order == "forward"
    assert RulesetPolicy(ruleset_id="test-only", scheduler_mode="chunked").scheduler_pass_order == "forward"


@pytest.mark.parametrize(
    "value", ["", "reverse", "reversed", "mirror", "Mirrored", "FORWARD", " forward", None, 0, 1, True, ["mirrored"]]
)
@pytest.mark.parametrize("scheduler_mode", ["chunked", "sequential"])
def test_unknown_scheduler_pass_order_is_rejected_never_coerced(value: Any, scheduler_mode: str) -> None:
    with pytest.raises(ValueError, match="unknown scheduler_pass_order"):
        RulesetPolicy(ruleset_id="test-only", scheduler_mode=scheduler_mode, scheduler_pass_order=value)


@pytest.mark.parametrize("scheduler_mode", ["chunked", "sequential"])
def test_forward_is_accepted_for_every_scheduler_mode(scheduler_mode: str) -> None:
    policy = RulesetPolicy(ruleset_id="test-only", scheduler_mode=scheduler_mode, scheduler_pass_order="forward")
    assert policy.scheduler_pass_order == "forward"


def test_mirrored_is_accepted_for_the_chunked_scheduler() -> None:
    policy = RulesetPolicy(
        ruleset_id="test-only", scheduler_mode="chunked", scheduler_chunk_size=2, scheduler_pass_order="mirrored"
    )
    assert policy.scheduler_pass_order == "mirrored"


@pytest.mark.parametrize("scheduler_mode", ["sequential", "interleaved", ""])
def test_mirrored_is_rejected_for_any_non_chunked_scheduler(scheduler_mode: str) -> None:
    with pytest.raises(ValueError, match="requires scheduler_mode 'chunked'"):
        RulesetPolicy(ruleset_id="test-only", scheduler_mode=scheduler_mode, scheduler_pass_order="mirrored")
    # The default scheduler mode is sequential, so mirrored alone is rejected too.
    with pytest.raises(ValueError, match="requires scheduler_mode 'chunked'"):
        RulesetPolicy(ruleset_id="test-only", scheduler_pass_order="mirrored")


def test_every_registered_policy_keeps_forward_passes_except_e4() -> None:
    assert {ruleset_id: policy.scheduler_pass_order for ruleset_id, policy in _RULESET_POLICIES.items()} == {
        ruleset_id: ("mirrored" if ruleset_id in E4_IDS else "forward") for ruleset_id in _RULESET_POLICIES
    }


def test_run_scheduler_maps_pass_order_to_the_scheduler_flag_and_nothing_else(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Every registered Ruleset: the scheduler receives exactly the historical
    # arguments plus ``mirror_second_half``, which is True only for E4.
    calls: list[dict[str, Any]] = []

    def record(states: Any, quota: int, execute_slot: Any, **kwargs: Any) -> None:
        calls.append({"quota": quota, **kwargs})

    monkeypatch.setattr("battle_engine.ruleset_policy.run_chunked_quota", record)
    for ruleset_id, policy in _RULESET_POLICIES.items():
        calls.clear()
        policy.run_scheduler([], 8, lambda _state, _slot: None, tick=3)
        chunk = 8 if policy.scheduler_mode == "sequential" else (policy.scheduler_chunk_size or 1)
        assert calls == [
            {
                "quota": 8,
                "chunk_size": chunk,
                "rotate_start": policy.scheduler_rotate_start,
                "tick": 3,
                "mirror_second_half": ruleset_id in E4_IDS,
            }
        ], ruleset_id


def test_there_is_no_match_request_override() -> None:
    # A Ruleset's gameplay semantics live on its RulesetPolicy, never on a
    # per-match field only research code could set (AGENTS.md).
    assert not {field.name for field in fields(MatchRequest)} & {
        "scheduler_pass_order",
        "pass_order",
        "mirror_second_half",
    }


# ---------------------------------------------------------------------------
# Ruleset definitions and registration
# ---------------------------------------------------------------------------


def test_identity_strings_and_single_source() -> None:
    assert PRIMARY_ID == "bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes"
    assert COMPANION_ID == "bytefray-rules-6-research-disruption-slot1-mirrored-passes"
    assert RULES_PRIMARY_ID is PRIMARY_ID
    assert RULES_COMPANION_ID is COMPANION_ID
    # Each names every gameplay difference from V4: its parent's ID plus the new one.
    assert PRIMARY_ID == f"{T_E3_ID}-mirrored-passes"
    assert COMPANION_ID == f"{T_E3K1_ID}-mirrored-passes"


@pytest.mark.parametrize(("treatment", "parent"), TREATMENT_PARENT, ids=lambda policy: policy.ruleset_id)
def test_treatment_differs_from_its_parent_in_exactly_one_gameplay_field(
    treatment: RulesetPolicy, parent: RulesetPolicy
) -> None:
    differing = {
        field.name
        for field in fields(RulesetPolicy)
        if getattr(treatment, field.name) != getattr(parent, field.name)
    }
    assert differing == {"ruleset_id", "scheduler_pass_order"}
    assert (parent.scheduler_pass_order, treatment.scheduler_pass_order) == ("forward", "mirrored")
    assert (
        replace(treatment, ruleset_id=parent.ruleset_id, scheduler_pass_order=parent.scheduler_pass_order)
        == parent
    )
    # An independent literal, not the parent object itself.
    assert treatment is not parent


def test_the_two_treatments_differ_only_where_their_parents_do() -> None:
    primary, companion = (treatment for treatment, _ in TREATMENT_PARENT)
    differing = {
        field.name
        for field in fields(RulesetPolicy)
        if getattr(primary, field.name) != getattr(companion, field.name)
    }
    assert differing == {"ruleset_id", "capture_hold_ticks"}
    assert (primary.capture_hold_ticks, companion.capture_hold_ticks) == (2, 1)
    assert (primary.disruption_slot_limit, companion.disruption_slot_limit) == (1, 1)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_treatment_is_registered_and_executable_on_the_process_runtime(ruleset_id: str) -> None:
    policy = resolve_ruleset_policy(ruleset_id)
    assert policy in {treatment for treatment, _ in TREATMENT_PARENT}
    assert ruleset_id in PROCESS_RULESET_IDS
    assert policy.supported_runtime_kinds == frozenset({"python"})
    assert policy.supported_python_api_versions == frozenset({2})
    assert (policy.scheduler_mode, policy.scheduler_chunk_size, policy.scheduler_rotate_start) == (
        "chunked",
        2,
        True,
    )


def test_lifecycle_sets_partition_every_executable_policy() -> None:
    executable_lifecycles = {
        "public_stable": PUBLIC_STABLE_RULESET_IDS,
        "active_research": ACTIVE_RESEARCH_RULESET_IDS,
        "retired_research": RETIRED_RESEARCH_RULESET_IDS,
    }
    for ruleset_id in _RULESET_POLICIES:
        memberships = [name for name, ids in executable_lifecycles.items() if ruleset_id in ids]
        assert len(memberships) == 1, (ruleset_id, memberships)
    assert set().union(*executable_lifecycles.values()) == set(_RULESET_POLICIES)
    assert HISTORICAL_READONLY_RULESET_IDS.isdisjoint(_RULESET_POLICIES)
    assert set(E4_IDS) <= ACTIVE_RESEARCH_RULESET_IDS
    assert PUBLIC_STABLE_RULESET_IDS == frozenset({BYTEFRAY_RULESET_V4_ID})


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_same_request_under_parent_and_treatment_has_distinct_match_ids(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name)
    control = _match_request(tmp_path, PARENT_ID[ruleset_id], names=("probe_a", "probe_b"), run_label="same")
    treatment = _match_request(tmp_path, ruleset_id, names=("probe_a", "probe_b"), run_label="same")
    # Precondition: the two requests differ in nothing but the Ruleset.
    assert replace(treatment, ruleset_id=PARENT_ID[ruleset_id]) == control
    assert canonical_match_id(control) != canonical_match_id(treatment)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_scheduler_override_carries_pass_order_without_changing_the_override_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ruleset_id: str
) -> None:
    # A research scheduler override is folded onto the policy with replace(),
    # which carries scheduler_pass_order through generically. The identity
    # payload's scheduler block keeps exactly its historical keys: the pass
    # order is recovered from the Ruleset ID, never hashed separately (review
    # Sec K), so no historical override match_id can move.
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name)
    treatment = replace(
        _match_request(tmp_path, ruleset_id, names=("probe_a", "probe_b"), run_label="override"),
        scheduler_chunk_size=1,
    )
    control = replace(treatment, ruleset_id=PARENT_ID[ruleset_id])
    effective = _effective_ruleset_policy(treatment)
    assert (effective.scheduler_chunk_size, effective.scheduler_pass_order) == (1, "mirrored")
    assert _effective_ruleset_policy(control).scheduler_pass_order == "forward"

    payloads: list[dict[str, Any]] = []
    real_stable_id = match_service.stable_id

    def capture(prefix: str, payload: Any) -> str:
        if prefix == "match":
            payloads.append(payload)
        return real_stable_id(prefix, payload)

    monkeypatch.setattr(match_service, "stable_id", capture)
    assert canonical_match_id(control) != canonical_match_id(treatment)
    assert [payload["scheduler"] for payload in payloads] == [
        {"mode": "chunked", "chunk_size": 1, "rotate_start": True}
    ] * 2
    assert [payload["ruleset_id"] for payload in payloads] == [PARENT_ID[ruleset_id], ruleset_id]
    assert all("pass_order" not in json.dumps(payload) for payload in payloads)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_overlapping_seeded_cores_fail_closed(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name)
    request = _match_request(
        tmp_path,
        ruleset_id,
        names=("probe_a", "probe_b"),
        run_label=f"overlap-{ruleset_id}",
        starts=(100, 104),
    )
    with pytest.raises(OverlappingCoreError):
        NativeMatchService().run(request)
    assert request.replay_path is not None and not request.replay_path.exists()


# ---------------------------------------------------------------------------
# Product isolation
# ---------------------------------------------------------------------------


def test_e4_is_never_automatic() -> None:
    for ruleset_id in E4_IDS:
        assert ruleset_id not in OMITTED_RULESET_CANDIDATES
        assert ruleset_id not in PUBLIC_STABLE_RULESET_IDS
    assert OMITTED_RULESET_CANDIDATES == (BYTEFRAY_RULESET_V4_ID,)
    roster = [{"agent_id": "x", "kind": "python", "api_version": 2}]
    assert resolve_omitted_ruleset_for_agents(None, roster) == BYTEFRAY_RULESET_V4_ID
    assert resolve_omitted_ruleset_id(None, ["python"]) == BYTEFRAY_RULESET_V4_ID
    assert resolve_evaluation_ruleset_id(None) == BYTEFRAY_RULESET_V4_ID


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_e4_is_not_selectable_from_product_run_surfaces(
    ruleset_id: str, capsys: pytest.CaptureFixture[str]
) -> None:
    # `agents test` and the tournament CLI expose stable v4 only.
    assert _ruleset_choices(agent_test._parser()) == [BYTEFRAY_RULESET_V4_ID]
    assert _ruleset_choices(tournament_cli._parser()) == [BYTEFRAY_RULESET_V4_ID]
    for parser in (agent_test._parser(), tournament_cli._parser()):
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["x", "--ruleset", ruleset_id])
        assert excinfo.value.code == 2
    # `bytefray run` builds its parser inside parse_args.
    with pytest.raises(SystemExit) as excinfo:
        cli.parse_args(["--ruleset", ruleset_id])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_e4_is_absent_from_every_designer_ruleset_option() -> None:
    for options in (SIMPLE_RULESET_OPTIONS, EVALUATION_RULESET_OPTIONS, DESIGNER_RULESET_OPTIONS):
        assert [option.ruleset_id for option in options] == [BYTEFRAY_RULESET_V4_ID]


def test_e4_is_explicitly_selectable_from_agents_evaluate() -> None:
    choices = _ruleset_choices(evaluation_cli._parser())
    assert set(E4_IDS) <= set(choices)
    # V6 E5's two identities follow E4's (test_ruleset_v6_research_anchor_before_core.py),
    # and V6 E6's two follow E5's (test_ruleset_v6_research_sensing.py).
    assert choices[-6:-4] == [PRIMARY_ID, COMPANION_ID]


# ---------------------------------------------------------------------------
# Evaluation plumbing
# ---------------------------------------------------------------------------


def test_methodology_predicates_classify_each_treatment_alone() -> None:
    others = (BYTEFRAY_RULESET_V4_ID, RS_ID, E2_ID, T_E3_ID, T_E3K1_ID, *RETIRED_RESEARCH_RULESET_IDS)
    assert is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology(PRIMARY_ID)
    assert is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology(COMPANION_ID)
    assert not is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology(COMPANION_ID)
    assert not is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology(PRIMARY_ID)
    for other in others:
        assert not is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology(other)
        assert not is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology(other)
    for ruleset_id in E4_IDS:
        assert is_ruleset_v4_derived_methodology(ruleset_id)
        assert not is_ruleset_v4_methodology(ruleset_id)
        assert not is_ruleset_v6_research_scale_methodology(ruleset_id)
        assert not is_ruleset_v6_research_scale_move_methodology(ruleset_id)
        assert not is_ruleset_v6_research_scale_move_proportional_methodology(ruleset_id)
        assert not is_ruleset_v6_research_capture_hold_methodology(ruleset_id)
        # Never a widening of the E3 parents' own predicates.
        assert not is_ruleset_v6_research_capture_hold_disruption_slot_methodology(ruleset_id)
        assert not is_ruleset_v6_research_disruption_slot_methodology(ruleset_id)


def test_alignment_labels_are_distinct_and_identity_schema_are_seven() -> None:
    assert ALIGNMENT_LABEL == {
        PRIMARY_ID: "ruleset_v6_research_capture_hold_k2_disruption_slot1_mirrored_passes_seeded_placements",
        COMPANION_ID: "ruleset_v6_research_disruption_slot1_mirrored_passes_seeded_placements",
    }
    existing = {
        EVALUATION_ARENA_ALIGNMENT_MODE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD,
        EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD,
        EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1,
    }
    assert len(set(ALIGNMENT_LABEL.values())) == 2
    assert existing.isdisjoint(ALIGNMENT_LABEL.values())
    for ruleset_id, label in ALIGNMENT_LABEL.items():
        assert arena_alignment_mode_for_ruleset(ruleset_id) == label
    # The parents keep their own labels.
    assert arena_alignment_mode_for_ruleset(T_E3_ID) == (
        EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1
    )
    assert arena_alignment_mode_for_ruleset(T_E3K1_ID) == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1
    flags: dict[str, dict[str, bool]] = {
        PRIMARY_ID: {"is_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology": True},
        COMPANION_ID: {"is_v6_research_disruption_slot_mirrored_passes_methodology": True},
    }
    for ruleset_id, flag in flags.items():
        assert resolved_arena_alignment_mode(False, **flag) == ALIGNMENT_LABEL[ruleset_id]
        assert resolved_identity_version(False, **flag) == IDENTITY_VERSION_V4 == 7
        assert resolved_schema_version(False, **flag) == SCHEMA_VERSION_V4 == 7


def test_e4_flags_cannot_be_passed_positionally() -> None:
    # Keyword-only by design: a positional call can never set them by accident.
    for resolver in (resolved_arena_alignment_mode, resolved_identity_version, resolved_schema_version):
        for arity in (7, 8, 9, 10, 11):
            with pytest.raises(TypeError):
                resolver(*([False] * (arity - 1)), True)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_omitted_arena_resolves_to_512_not_the_config_default(tmp_path: Path, ruleset_id: str) -> None:
    request = _evaluation_request(tmp_path, arena_size=None, ruleset_id=ruleset_id)
    assert Config().arena_size == 4096  # the silent-fallback trap this guards
    assert request.resolved_arena_size == STANDARD_V4_ARENA_SIZE == 512
    assert request.resolved_arena_alignment_mode == ALIGNMENT_LABEL[ruleset_id]
    assert (
        request.is_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology,
        request.is_v6_research_disruption_slot_mirrored_passes_methodology,
    ) == (ruleset_id == PRIMARY_ID, ruleset_id == COMPANION_ID)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_omitted_arena_evaluation_runs_under_the_treatment_at_512(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    EvaluationService().run(_evaluation_request(tmp_path, arena_size=None, ruleset_id=ruleset_id))

    data = json.loads((tmp_path / "eval-out" / "evaluation.json").read_text(encoding="utf-8"))
    assert (
        data["schema_version"],
        data["identity_version"],
        data["rules_compatibility_id"],
        data["arena_alignment_mode"],
        data["effective_conditions"]["arena_size"],
    ) == (7, 7, ruleset_id, ALIGNMENT_LABEL[ruleset_id], 512)
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=1
    )
    # Seeded placement with the paired orientation swap (the shared v4-derived branch).
    assert [
        (cell["orientation"], cell["placement_id"], cell["subject_start"], cell["opponent_start"])
        for cell in data["cells"]
    ] == [
        ("candidate_first", "seeded-1", starts[0], starts[1]),
        ("opponent_first", "seeded-1", starts[1], starts[0]),
    ]
    # Each cell really executed under the treatment, not merely under its label.
    for cell in data["cells"]:
        assert cell["status"] == "completed"
        result = json.loads(
            (tmp_path / "eval-out" / cell["artifact_dir"] / "result.json").read_text(encoding="utf-8")
        )
        assert result["ruleset_id"] == ruleset_id


@pytest.mark.parametrize("ruleset_id", E4_IDS)
@pytest.mark.parametrize("arena_size", [63, 65537])
def test_out_of_range_arena_is_rejected(tmp_path: Path, ruleset_id: str, arena_size: int) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    with pytest.raises(EvaluationConfigurationError, match="outside the"):
        EvaluationService().run(_evaluation_request(tmp_path, arena_size=arena_size, ruleset_id=ruleset_id))
    assert not (tmp_path / "eval-out" / "evaluation.json").exists()


@pytest.mark.parametrize("ruleset_id", E4_IDS)
@pytest.mark.parametrize("arena_size", [64, 65536])
def test_research_range_boundaries_are_accepted(tmp_path: Path, ruleset_id: str, arena_size: int) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    EvaluationService().run(_evaluation_request(tmp_path, arena_size=arena_size, ruleset_id=ruleset_id))
    data = json.loads((tmp_path / "eval-out" / "evaluation.json").read_text(encoding="utf-8"))
    assert data["effective_conditions"]["arena_size"] == arena_size


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_evaluation_ids_differ_between_parent_and_treatment(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    control = EvaluationService().run(
        _evaluation_request(tmp_path, arena_size=512, ruleset_id=PARENT_ID[ruleset_id], out="parent")
    )
    treatment = EvaluationService().run(
        _evaluation_request(tmp_path, arena_size=512, ruleset_id=ruleset_id, out="treatment")
    )
    assert control.evaluation_id != treatment.evaluation_id


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_evaluate_cli_selects_the_treatment_explicitly_with_default_arena(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ruleset_id: str,
) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    base = ["candidate", "--opponents", "opponent", "--ruleset", ruleset_id, "--seeds", "1", "--ticks", "5"]

    assert evaluate_main([*base, "--output", str(tmp_path / "ok")]) == 0
    data = json.loads((tmp_path / "ok" / "evaluation.json").read_text(encoding="utf-8"))
    assert data["effective_conditions"]["arena_size"] == 512
    assert data["arena_alignment_mode"] == ALIGNMENT_LABEL[ruleset_id]

    assert evaluate_main([*base, "--arena-size", "65537", "--output", str(tmp_path / "bad")]) != 0
    assert not (tmp_path / "bad" / "evaluation.json").exists()
    capsys.readouterr()


# ---------------------------------------------------------------------------
# Determinism and serialization
# ---------------------------------------------------------------------------

# Tracked E2 research fixtures: a deterministic single-location pairing and a
# pairing whose spread agent draws its offsets from ``context.rng``.
DETERMINISM_PAIRINGS = (("e2_sniper", "e2_disrupt_guard"), ("e2_spread_sniper", "e2_disrupt_guard"))


def _run_fixture_pair(root: Path, ruleset_id: str, names: tuple[str, str], *, max_ticks: int = 60) -> tuple[Path, Any]:
    prepare_benchmark_data_root(root, list(names))
    request = _match_request(root, ruleset_id, names=names, run_label="run", seed=7, max_ticks=max_ticks)
    result = NativeMatchService().run(request)
    assert request.replay_path is not None
    return request.replay_path, result


@pytest.mark.parametrize("names", DETERMINISM_PAIRINGS, ids=lambda pair: "-vs-".join(pair))
@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_same_treatment_request_twice_is_byte_identical(tmp_path: Path, ruleset_id: str, names: tuple[str, str]) -> None:
    first_path, first = _run_fixture_pair(tmp_path / "one", ruleset_id, names)
    second_path, second = _run_fixture_pair(tmp_path / "two", ruleset_id, names)

    first_bytes = first_path.read_bytes()
    assert first_bytes == second_path.read_bytes()
    assert b"\r" not in first_bytes
    assert first.result_id == second.result_id
    assert first.match_id == second.match_id
    assert first.replay_sha256 == hashlib.sha256(first_bytes).hexdigest()
    assert (first.winner, first.ticks_run, first.termination_reason) == (
        second.winner,
        second.ticks_run,
        second.termination_reason,
    )
    header = next(iter(iter_replay(first_path)))
    assert isinstance(header, ReplayHeader) and header.ruleset_id == ruleset_id


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_treatment_and_parent_have_distinct_result_identities(tmp_path: Path, ruleset_id: str) -> None:
    # The sniper v disrupt guard sweep is order-dependent from tick 1 (review
    # Sec L-1), so the same request under the parent and the treatment plays
    # a different match: distinct match_id, result_id and replay bytes.
    names = ("e2_sniper", "e2_disrupt_guard")
    parent_path, parent = _run_fixture_pair(tmp_path / "parent", PARENT_ID[ruleset_id], names)
    treatment_path, treatment = _run_fixture_pair(tmp_path / "treatment", ruleset_id, names)
    assert parent.match_id != treatment.match_id
    assert parent.result_id != treatment.result_id
    assert parent_path.read_bytes() != treatment_path.read_bytes()


def _key_shapes(value: Any) -> Any:
    """Every JSON key path in one record, values ignored."""

    if isinstance(value, dict):
        return {key: _key_shapes(item) for key, item in value.items()}
    if isinstance(value, list):
        shapes = [_key_shapes(item) for item in value]
        return sorted({json.dumps(shape, sort_keys=True) for shape in shapes})
    return None


def _replay_shapes(replay_path: Path) -> tuple[list[Any], list[Any]]:
    """(record shapes with events stripped, event shapes) of one replay."""

    records, events = set(), set()
    for line in replay_path.read_bytes().decode("utf-8").splitlines():
        record = json.loads(line)
        for event in record.get("events", ()):
            events.add(json.dumps(_key_shapes(event), sort_keys=True))
            events.add(json.dumps({"event_type": event["event_type"]}))
        if "events" in record:
            record["events"] = []
        records.add(json.dumps(_key_shapes(record), sort_keys=True))
    return sorted(records), sorted(events)


@pytest.mark.parametrize("ruleset_id", E4_IDS)
def test_treatment_replay_and_result_have_exactly_the_parent_shape(tmp_path: Path, ruleset_id: str) -> None:
    # No replay, event, process-snapshot, or result field is added -- the pass
    # order is recovered from ruleset_id through the registry, never
    # serialized. The probe mirror ends in a capture under parent and
    # treatment alike, so both emit ``kill`` events.
    names = ("v4_probe", "v4_probe_twin")
    parent_path, _ = _run_fixture_pair(tmp_path / "parent", PARENT_ID[ruleset_id], names)
    treatment_path, _ = _run_fixture_pair(tmp_path / "treatment", ruleset_id, names)

    parent_records, parent_events = _replay_shapes(parent_path)
    treatment_records, treatment_events = _replay_shapes(treatment_path)
    assert treatment_records == parent_records
    assert treatment_events == parent_events
    assert json.dumps({"event_type": "kill"}) in treatment_events
    parent_result = json.loads((parent_path.parent / "result.json").read_text(encoding="utf-8"))
    treatment_result = json.loads((treatment_path.parent / "result.json").read_text(encoding="utf-8"))
    assert _key_shapes(treatment_result) == _key_shapes(parent_result)
    assert treatment_result["schema_version"] == parent_result["schema_version"]
    records = list(iter_replay(treatment_path))
    header = records[0]
    assert isinstance(header, ReplayHeader)
    assert (header.ruleset_id, header.schema_version) == (ruleset_id, 4)
    assert isinstance(records[-1], MatchResult)
    assert all(isinstance(record, TickSnapshot) for record in records[1:-1])
    tick_lines = [
        json.loads(line)
        for line in treatment_path.read_bytes().decode("utf-8").splitlines()
        if json.loads(line).get("record_type") == "tick"
    ]
    assert {tuple(sorted(process)) for line in tick_lines for process in line["processes"]} == {
        ("anchor", "disrupted", "entrant_id", "process_id", "reach")
    }
    # The pass order appears in no artifact except through the Ruleset ID.
    for artifact in (treatment_path.read_bytes(), (treatment_path.parent / "result.json").read_bytes()):
        for needle in (b"scheduler_pass_order", b"pass_order", b"mirror_second_half"):
            assert needle not in artifact
