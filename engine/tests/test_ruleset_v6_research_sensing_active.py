"""V6 E8: the active-sensing research Rulesets -- policy, identity, registration,
evaluation plumbing, product isolation and A1 containment (phase I8-2).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.1,
2.2 and 13, and the implementation plan Sec 4.1, 4.4 and 4.5. Two treatments,
each differing from its E6 parent only in ``RulesetPolicy.sensing_mode``
(``"passive"`` -> ``"active"``):

* T8, ``bytefray-rules-6-research-sensing-active-w27``, parent
  ``bytefray-rules-6-research-sensing-r32`` (C8, whole-tick disruption);
* T8L, ``bytefray-rules-6-research-disruption-slot1-sensing-active-w27``,
  parent ``bytefray-rules-6-research-disruption-slot1-sensing-r32`` (C8L, lambda = 1).

The SENSE semantics are ``test_v6_e8_sensing_semantics.py``'s, and the parents'
byte identity is ``test_v6_e8_parent_byte_identity.py``'s. Every match here is
played by scripted test agents, never by an E8 family member, and no outcome
is asserted.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest
from _e8_sensing_harness import QUOTA, Scripted, presence_problems, process, run_traced, sense
from _hang_safety import hang_safety_timeout
from battle_engine import agent_test, cli, evaluation_cli, tournament_cli
from battle_engine.agent_api import ActionKindV2, AgentAction
from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService
from battle_engine.agent_trace import TRACE_SCHEMA_VERSION_V2, TraceHeader, TraceWriter
from battle_engine.agent_validation import AgentValidationFailedError, validate_agent
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SENSING_ACTIVE_W27,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SENSING_R32,
    IDENTITY_VERSION_V4,
    SCHEMA_VERSION_V4,
    STANDARD_V4_ARENA_SIZE,
    arena_alignment_mode_for_ruleset,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_disruption_slot_sensing_active_w27_methodology,
    is_ruleset_v6_research_disruption_slot_sensing_r32_methodology,
    is_ruleset_v6_research_sensing_active_w27_methodology,
    is_ruleset_v6_research_sensing_r32_methodology,
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
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import ProcessMatchController, PythonEntrantInitializationError
from battle_engine.rules import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID as RULES_COMPANION_ID,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID as RULES_PRIMARY_ID,
)
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    ACTIVE_RESEARCH_RULESET_IDS,
    ACTIVE_SENSING_HALF_WIDTH,
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    PUBLIC_STABLE_RULESET_IDS,
    RETIRED_RESEARCH_RULESET_IDS,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32,
    RULESET_V6_RESEARCH_SENSING_ACTIVE_W27,
    RULESET_V6_RESEARCH_SENSING_R32,
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

PRIMARY_ID = BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID
COMPANION_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID
E8_IDS = (PRIMARY_ID, COMPANION_ID)
C8_ID = BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID
C8L_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID
TREATMENT_PARENT = (
    (RULESET_V6_RESEARCH_SENSING_ACTIVE_W27, RULESET_V6_RESEARCH_SENSING_R32),
    (RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27, RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32),
)
PARENT_ID = {PRIMARY_ID: C8_ID, COMPANION_ID: C8L_ID}
ALIGNMENT_LABEL = {
    PRIMARY_ID: EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SENSING_ACTIVE_W27,
    COMPANION_ID: EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27,
}
WORKER_TIMEOUT = 30.0

IDLE_AGENT_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor)


def create_agent():
    return Agent()
"""

# Returns SENSE at every callback, whatever the Ruleset: the ungated package A1 must refuse.
UNGATED_SENSE_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.SENSE, observation.self_anchor)


def create_agent():
    return Agent()
"""

# Senses only when the context offers a window: the context-gated form (PR8 Sec 3.3).
GATED_SENSE_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.window = context.sensing_window

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        if self.window is not None:
            return AgentAction(ActionKindV2.SENSE, observation.self_anchor)
        return AgentAction(ActionKindV2.READ, observation.self_anchor)


def create_agent():
    return Agent()
"""


def _write_agent(root: Path, name: str, source: str = IDLE_AGENT_SOURCE) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_bytes(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0",
    }).encode())
    (agent_dir / "agent.py").write_bytes(source.encode())


def _ruleset_choices(parser: argparse.ArgumentParser) -> list[str]:
    (action,) = [item for item in parser._actions if "--ruleset" in item.option_strings]
    assert action.choices is not None
    return list(action.choices)


def _evaluation_request(root: Path, *, arena_size: int | None, ruleset_id: str, out: str = "eval-out"
                        ) -> EvaluationRequest:
    return EvaluationRequest(candidate_id="candidate", opponent_ids=["opponent"], seeds=(1,), ticks=5,
                             arena_size=arena_size, ruleset_id=ruleset_id, output_dir=root / out, data_root=root)


# ---------------------------------------------------------------------------
# The policy field and the window
# ---------------------------------------------------------------------------


def test_sensing_mode_defaults_to_passive_with_no_window() -> None:
    policy = RulesetPolicy(ruleset_id="test-only")
    assert policy.sensing_mode == "passive" and policy.sensing_window is None
    assert [field.name for field in fields(RulesetPolicy)][-1] == "sensing_mode"  # additive and last


def test_the_window_is_the_registered_constant_27() -> None:
    assert ACTIVE_SENSING_HALF_WIDTH == 27
    assert RulesetPolicy(ruleset_id="test-only", sensing_mode="active").sensing_window == 27


@pytest.mark.parametrize("value", ["Active", "ACTIVE", "", "none", None, True, 1, 27, ["active"]])
def test_an_invalid_sensing_mode_is_rejected_never_coerced(value: Any) -> None:
    with pytest.raises(ValueError, match="sensing_mode"):
        RulesetPolicy(ruleset_id="test-only", sensing_mode=value)


def test_every_registered_policy_is_passive_except_t8_and_t8l() -> None:
    active = {ruleset_id for ruleset_id, policy in _RULESET_POLICIES.items() if policy.sensing_mode == "active"}
    assert active == set(E8_IDS)
    for ruleset_id, policy in _RULESET_POLICIES.items():
        assert policy.sensing_window == (27 if ruleset_id in E8_IDS else None), ruleset_id


def test_there_is_no_match_request_override() -> None:
    assert not {field.name for field in fields(MatchRequest)} & {"sensing_mode", "sensing_window", "window"}


# ---------------------------------------------------------------------------
# Definitions and registration
# ---------------------------------------------------------------------------


def test_identity_strings_and_single_source() -> None:
    assert PRIMARY_ID == "bytefray-rules-6-research-sensing-active-w27"
    assert COMPANION_ID == "bytefray-rules-6-research-disruption-slot1-sensing-active-w27"
    assert RULES_PRIMARY_ID is PRIMARY_ID and RULES_COMPANION_ID is COMPANION_ID
    # Each replaces its parent's -r32 with -active-w27 (the pre-registration's provisional identifiers).
    assert PRIMARY_ID == C8_ID.removesuffix("-r32") + "-active-w27"
    assert COMPANION_ID == C8L_ID.removesuffix("-r32") + "-active-w27"


@pytest.mark.parametrize(("treatment", "parent"), TREATMENT_PARENT, ids=lambda policy: policy.ruleset_id)
def test_each_treatment_differs_from_its_parent_only_in_sensing_mode(treatment: RulesetPolicy,
                                                                     parent: RulesetPolicy) -> None:
    differing = {field.name for field in fields(RulesetPolicy)
                 if getattr(treatment, field.name) != getattr(parent, field.name)}
    assert differing == {"ruleset_id", "sensing_mode"}
    assert (parent.sensing_mode, treatment.sensing_mode) == ("passive", "active")
    assert replace(treatment, ruleset_id=parent.ruleset_id, sensing_mode="passive") == parent
    # detection_radius keeps the parent's value; under "active" it is inert (PR8 Sec 2.1).
    assert treatment.detection_radius == parent.detection_radius == 32
    assert treatment is not parent


def test_the_two_treatments_differ_only_where_their_parents_do() -> None:
    (primary, _), (companion, _) = TREATMENT_PARENT
    differing = {field.name for field in fields(RulesetPolicy)
                 if getattr(primary, field.name) != getattr(companion, field.name)}
    assert differing == {"ruleset_id", "disruption_slot_limit"}
    assert (primary.disruption_slot_limit, companion.disruption_slot_limit) == (None, 1)


@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_each_treatment_is_registered_and_executable_on_the_process_runtime(ruleset_id: str) -> None:
    policy = resolve_ruleset_policy(ruleset_id)
    assert policy in {treatment for treatment, _ in TREATMENT_PARENT}
    assert ruleset_id in PROCESS_RULESET_IDS and ruleset_id in ACTIVE_RESEARCH_RULESET_IDS
    assert policy.supported_runtime_kinds == frozenset({"python"})
    assert policy.supported_python_api_versions == frozenset({2})


def test_the_lifecycle_sets_still_partition_every_executable_policy() -> None:
    lifecycles = (PUBLIC_STABLE_RULESET_IDS, ACTIVE_RESEARCH_RULESET_IDS, RETIRED_RESEARCH_RULESET_IDS)
    for ruleset_id in _RULESET_POLICIES:
        assert sum(ruleset_id in ids for ids in lifecycles) == 1, ruleset_id
    assert set().union(*lifecycles) == set(_RULESET_POLICIES)


@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_overlapping_seeded_cores_fail_closed(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("probe_a", "probe_b"):
        _write_agent(tmp_path, name)
    request = MatchRequest(
        config=Config(seed=1, arena_size=512, instr_per_tick=8),
        entrants=tuple(MatchEntrant.python(seat, name, start, resolve_agent(tmp_path, name))
                       for seat, name, start in (("A", "probe_a", 100), ("B", "probe_b", 104))),
        max_ticks=5, replay_path=tmp_path / "runs" / "overlap" / "replay.jsonl", verbose=False, ruleset_id=ruleset_id)
    with pytest.raises(OverlappingCoreError):
        NativeMatchService().run(request)


@pytest.mark.parametrize("policy", [treatment for treatment, _ in TREATMENT_PARENT], ids=lambda p: p.ruleset_id)
def test_the_window_needs_an_arena_wider_than_54(tmp_path: Path, policy: RulesetPolicy) -> None:
    # 2 * 27 < arena_size, checked at both match layers; a policy without the
    # E6 radius isolates the window check from detection_radius's own.
    probe = replace(policy, ruleset_id="test-only", detection_radius=None)
    log: list[tuple[str, int, int]] = []

    def entrants(arena: int):
        return [("A", 0, [process("a", 1, 8, QUOTA, Scripted("A", log))]),
                ("B", arena // 2, [process("b", arena // 2 + 1, 8, QUOTA, Scripted("B", log))])]

    with pytest.raises(ValueError, match="half-width 27, which requires arena_size > 54; received 54"):
        run_traced(tmp_path, probe, entrants(54), arena=54)
    run_traced(tmp_path, probe, entrants(55), arena=55, name="fits.jsonl")
    _write_agent(tmp_path, "probe_a")
    _write_agent(tmp_path, "probe_b", UNGATED_SENSE_SOURCE)
    with pytest.raises(PythonEntrantInitializationError) as excinfo:
        ProcessMatchController.from_python_entrants(
            Config(seed=1, arena_size=54, instr_per_tick=8),
            (MatchEntrant.python("A", "probe_a", 0, resolve_agent(tmp_path, "probe_a")),
             MatchEntrant.python("B", "probe_b", 27, resolve_agent(tmp_path, "probe_b"))), 5, ruleset_policy=probe)
    assert excinfo.value.diagnostic.code == "match_configuration_invalid"
    assert excinfo.value.diagnostic.stage == "configuration"  # before any entrant is loaded or reset


# ---------------------------------------------------------------------------
# Product isolation
# ---------------------------------------------------------------------------


def test_e8_is_never_automatic() -> None:
    for ruleset_id in E8_IDS:
        assert ruleset_id not in OMITTED_RULESET_CANDIDATES and ruleset_id not in PUBLIC_STABLE_RULESET_IDS
    assert OMITTED_RULESET_CANDIDATES == (BYTEFRAY_RULESET_V4_ID,)
    assert resolve_omitted_ruleset_for_agents(None, [{"agent_id": "x", "kind": "python", "api_version": 2}]) == (
        BYTEFRAY_RULESET_V4_ID)
    assert resolve_omitted_ruleset_id(None, ["python"]) == BYTEFRAY_RULESET_V4_ID
    assert resolve_evaluation_ruleset_id(None) == BYTEFRAY_RULESET_V4_ID


@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_e8_is_not_selectable_from_product_run_surfaces(ruleset_id: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _ruleset_choices(agent_test._parser()) == [BYTEFRAY_RULESET_V4_ID]
    assert _ruleset_choices(tournament_cli._parser()) == [BYTEFRAY_RULESET_V4_ID]
    for parser in (agent_test._parser(), tournament_cli._parser()):
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["x", "--ruleset", ruleset_id])
        assert excinfo.value.code == 2
    with pytest.raises(SystemExit) as excinfo:
        cli.parse_args(["--ruleset", ruleset_id])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_e8_is_absent_from_every_designer_ruleset_option() -> None:
    for options in (SIMPLE_RULESET_OPTIONS, EVALUATION_RULESET_OPTIONS, DESIGNER_RULESET_OPTIONS):
        assert [option.ruleset_id for option in options] == [BYTEFRAY_RULESET_V4_ID]


def test_e8_is_explicitly_selectable_from_agents_evaluate() -> None:
    choices = _ruleset_choices(evaluation_cli._parser())
    assert choices[-4:] == [C8_ID, C8L_ID, PRIMARY_ID, COMPANION_ID]


# ---------------------------------------------------------------------------
# Evaluation plumbing (registered wherever E6's research Rulesets were)
# ---------------------------------------------------------------------------


def test_methodology_predicates_classify_each_treatment_alone() -> None:
    assert is_ruleset_v6_research_sensing_active_w27_methodology(PRIMARY_ID)
    assert is_ruleset_v6_research_disruption_slot_sensing_active_w27_methodology(COMPANION_ID)
    assert not is_ruleset_v6_research_sensing_active_w27_methodology(COMPANION_ID)
    assert not is_ruleset_v6_research_disruption_slot_sensing_active_w27_methodology(PRIMARY_ID)
    for other in set(_RULESET_POLICIES) - set(E8_IDS):
        assert not is_ruleset_v6_research_sensing_active_w27_methodology(other)
        assert not is_ruleset_v6_research_disruption_slot_sensing_active_w27_methodology(other)
    for ruleset_id in E8_IDS:
        assert is_ruleset_v4_derived_methodology(ruleset_id) and not is_ruleset_v4_methodology(ruleset_id)
        # Never a widening of the parents' predicates.
        assert not is_ruleset_v6_research_sensing_r32_methodology(ruleset_id)
        assert not is_ruleset_v6_research_disruption_slot_sensing_r32_methodology(ruleset_id)


def test_alignment_labels_are_distinct_and_identity_schema_are_seven() -> None:
    assert ALIGNMENT_LABEL == {
        PRIMARY_ID: "ruleset_v6_research_sensing_active_w27_seeded_placements",
        COMPANION_ID: "ruleset_v6_research_disruption_slot1_sensing_active_w27_seeded_placements",
    }
    others = {arena_alignment_mode_for_ruleset(ruleset_id) for ruleset_id in set(_RULESET_POLICIES) - set(E8_IDS)}
    assert others.isdisjoint(ALIGNMENT_LABEL.values()) and len(set(ALIGNMENT_LABEL.values())) == 2
    for ruleset_id, label in ALIGNMENT_LABEL.items():
        assert arena_alignment_mode_for_ruleset(ruleset_id) == label
    assert arena_alignment_mode_for_ruleset(C8_ID) == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SENSING_R32
    assert arena_alignment_mode_for_ruleset(C8L_ID) == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32
    flags = {PRIMARY_ID: {"is_v6_research_sensing_active_w27_methodology": True},
             COMPANION_ID: {"is_v6_research_disruption_slot_sensing_active_w27_methodology": True}}
    for ruleset_id, flag in flags.items():
        assert resolved_arena_alignment_mode(False, **flag) == ALIGNMENT_LABEL[ruleset_id]
        assert resolved_identity_version(False, **flag) == IDENTITY_VERSION_V4 == 7
        assert resolved_schema_version(False, **flag) == SCHEMA_VERSION_V4 == 7


@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_omitted_arena_resolves_to_512(tmp_path: Path, ruleset_id: str) -> None:
    request = _evaluation_request(tmp_path, arena_size=None, ruleset_id=ruleset_id)
    assert request.resolved_arena_size == STANDARD_V4_ARENA_SIZE == 512
    assert request.resolved_arena_alignment_mode == ALIGNMENT_LABEL[ruleset_id]
    assert (request.is_v6_research_sensing_active_w27_methodology,
            request.is_v6_research_disruption_slot_sensing_active_w27_methodology) == (
        ruleset_id == PRIMARY_ID, ruleset_id == COMPANION_ID)


@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_an_evaluation_runs_under_each_treatment_with_the_parents_placement(tmp_path: Path, ruleset_id: str) -> None:
    for name in ("candidate", "opponent"):
        _write_agent(tmp_path, name)
    treatment = EvaluationService().run(_evaluation_request(tmp_path, arena_size=None, ruleset_id=ruleset_id))
    data = json.loads((tmp_path / "eval-out" / "evaluation.json").read_text(encoding="utf-8"))
    assert (data["schema_version"], data["identity_version"], data["rules_compatibility_id"],
            data["arena_alignment_mode"], data["effective_conditions"]["arena_size"]) == (
        7, 7, ruleset_id, ALIGNMENT_LABEL[ruleset_id], 512)
    assert {cell["status"] for cell in data["cells"]} == {"completed"}
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=512, entrant_count=2,
                                         supplied_starts=[None, None], seed=1)
    assert starts == resolve_direct_match_starts(ruleset_id=PARENT_ID[ruleset_id], arena_size=512, entrant_count=2,
                                                 supplied_starts=[None, None], seed=1)
    parent = EvaluationService().run(_evaluation_request(tmp_path, arena_size=None, ruleset_id=PARENT_ID[ruleset_id],
                                                         out="parent-out"))
    assert parent.evaluation_id != treatment.evaluation_id


# ---------------------------------------------------------------------------
# A1 containment (PR8 Sec 13)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", sorted(_RULESET_POLICIES))
def test_only_t8_and_t8l_accept_sense(tmp_path: Path, ruleset_id: str) -> None:
    policy = resolve_ruleset_policy(ruleset_id)
    log: list[tuple[str, int, int]] = []
    run = run_traced(tmp_path, policy, [("A", 0, [process("a", 100, 64, QUOTA, Scripted("A", log, {1: sense(100)}))]),
                                        ("B", 256, [process("b", 120, 1, QUOTA, Scripted("B", log))])])
    first = run.decisions("A")[0]
    if ruleset_id in E8_IDS:
        assert first["applied_result"]["status"] == "APPLIED" and run.controller.states[0].alive
        assert presence_problems(run.records, active=True) == []
    else:
        # An invalid action: the entrant forfeits, and the record carries no action and no sensed_anchors.
        assert first["applied_result"] == {"status": "REJECTED_INVALID", "normalized_address": None,
                                           "read_value": None, "read_owner": None}
        assert first["action"] is None and first["diagnostic"]["code"] == "agent_action_invalid"
        assert "sensing_mode is 'active'" in first["diagnostic"]["message"]
        assert not run.controller.states[0].alive and len(run.decisions("A")) == 1
        assert presence_problems(run.records, active=False) == []


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("ruleset_id", [BYTEFRAY_RULESET_V4_ID, C8_ID, C8L_ID, *E8_IDS])
def test_a_loaded_ungated_sense_package_is_refused_outside_t8_and_t8l(tmp_path: Path, ruleset_id: str,
                                                                    worker: bool) -> None:
    _write_agent(tmp_path, "senser", UNGATED_SENSE_SOURCE)
    _write_agent(tmp_path, "idle")
    path = tmp_path / "trace.jsonl"
    writer = TraceWriter(path)
    writer.write_header(TraceHeader(match_seed=1, agents={"A": "senser", "B": "idle"}, supervised=worker,
                                    schema_version=TRACE_SCHEMA_VERSION_V2))
    with hang_safety_timeout(120):
        controller = ProcessMatchController.from_python_entrants(
            Config(seed=1, arena_size=512, instr_per_tick=8),
            (MatchEntrant.python("A", "senser", 0, resolve_agent(tmp_path, "senser")),
             MatchEntrant.python("B", "idle", 256, resolve_agent(tmp_path, "idle"))), 2,
            ruleset_policy=resolve_ruleset_policy(ruleset_id), agent_call_timeout=WORKER_TIMEOUT if worker else None,
            trace_writer=writer)
        try:
            controller.run()
        finally:
            controller.close()
            writer.close()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    first = next(r for r in records if r["record_type"] == "decision_v2" and r["agent_id"] == "A")
    if ruleset_id in E8_IDS:
        assert first["applied_result"]["status"] == "APPLIED" and controller.states[0].alive
        assert first["action"] == {"kind": "sense", "operand": first["observation"]["self_anchor"], "value": None}
    else:
        assert first["applied_result"]["status"] == "REJECTED_INVALID" and first["action"] is None
        assert "sensed_anchors" not in first["applied_result"]
        assert not controller.states[0].alive
    assert presence_problems(records, active=ruleset_id in E8_IDS) == []


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
def test_agents_validate_refuses_an_ungated_sense_and_accepts_a_gated_one(tmp_path: Path, worker: bool) -> None:
    # A dry run belongs to no Ruleset: it has no window, so SENSE is invalid there.
    _write_agent(tmp_path, "ungated", UNGATED_SENSE_SOURCE)
    _write_agent(tmp_path, "gated", GATED_SENSE_SOURCE)
    timeout = WORKER_TIMEOUT if worker else None
    with hang_safety_timeout(120):
        with pytest.raises(AgentValidationFailedError) as excinfo:
            validate_agent("ungated", data_root=tmp_path, timeout=timeout)
        assert excinfo.value.diagnostic.code == "agent_action_invalid"
        validate_agent("gated", data_root=tmp_path, timeout=timeout)


@pytest.mark.parametrize("action, available", [
    (AgentAction(ActionKindV2.SENSE, 5), False),
    (AgentAction(ActionKindV2.SENSE, 5, 1), True),       # SENSE carries no value
    (AgentAction(ActionKindV2.SENSE, None), True),       # one integer operand
    (AgentAction(ActionKindV2.SENSE, True), True),       # never a bool
    (AgentAction(ActionKindV2.SENSE, 5.0), True),        # type: ignore[arg-type]
])
def test_the_action_shape_is_validated(action: AgentAction, available: bool) -> None:
    with pytest.raises(ValueError):
        ProcessMatchController._validate_v2_action(action, sensing_available=available)


def test_a_well_formed_sense_is_valid_only_where_sensing_is_available() -> None:
    action = AgentAction(ActionKindV2.SENSE, -700)
    assert ProcessMatchController._validate_v2_action(action, sensing_available=True) is action
    with pytest.raises(ValueError, match="sensing_mode is 'active'"):
        ProcessMatchController._validate_v2_action(action)  # the default refuses
    # The other kinds are unaffected by availability.
    for kind in (ActionKindV2.READ, ActionKindV2.MOVE):
        ordinary = AgentAction(kind, 3)
        assert ProcessMatchController._validate_v2_action(ordinary) is ordinary
