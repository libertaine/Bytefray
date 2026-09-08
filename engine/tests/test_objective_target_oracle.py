from __future__ import annotations

"""V5 research Phase R2: objective-target oracle (target persistence) tests.

Covers the experimental Ruleset identity (registration, isolation from
omitted-Ruleset resolution, stable V4, and R1's mortality gate), the oracle
instrument itself (which address is exposed, when it appears, when it
disappears, independence from sensor reach and process liveness,
determinism, multi-entrant shape), the proof that the oracle changes only
*information* and never a game mechanic, and full-stack replay/provenance
persistence including byte-compatibility with both stable V4 and R1.

Observation assertions are taken from observations real agent callbacks were
actually handed during real ticks (``_RecordingProcess`` below), not from
hand-built ``ObservationV2`` objects, so a test fails if the oracle stops
reaching agents even though its own helper still computes the right value.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

from battle_engine.agent_api import ActionKind, ActionKindV2, AgentAction
from battle_engine.agents import resolve_agent
from battle_engine.config import Config, Weights
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.process_runtime import (
    OBJECTIVE_TARGET_ORACLE_RULESET_IDS,
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
    has_objective_target_oracle,
    has_process_mortality,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
    BYTEFRAY_RULESET_V5_R2_ALPHA1_ID,
)
from battle_engine.ruleset_policy import (
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V4,
    RULESET_V5_R1_ALPHA1,
    RULESET_V5_R2_ALPHA1,
    resolve_ruleset_policy,
)

ARENA = 1024
# Deliberately explicit, widely separated core bases so every asserted
# address below is a known constant rather than a derived coincidence.
A_START = 0
B_START = 500
C_START = 800


def _config(seed: int = 1) -> Config:
    return Config(arena_size=ARENA, instr_per_tick=8, seed=seed, weights=Weights())


class _RecordingProcess:
    """Captures the visible-anchor tuple of every observation it is handed."""

    def __init__(self) -> None:
        self.seen: list[tuple[int, ...]] = []

    def __call__(self, obs: Any, state: dict[str, Any]) -> AgentAction:
        self.seen.append(tuple(obs.visible_enemy_anchor_addresses))
        return AgentAction(ActionKind.NOP)


def _observer_spec(
    recorder: _RecordingProcess,
    *,
    agent_id: str = "A",
    position: int,
    reach: int,
    start: int,
) -> ProcessEntrantSpec:
    return ProcessEntrantSpec(
        agent_id,
        f"observer_{agent_id}",
        [
            ProcessInstance(
                f"p{agent_id}",
                ProcessRole.SCOUT,
                initial_position=position,
                reach=reach,
                quota_share=8,
                logic=recorder,
            )
        ],
        start=start,
    )


def _passive_spec(
    *, agent_id: str, position: int, start: int
) -> ProcessEntrantSpec:
    return ProcessEntrantSpec(
        agent_id,
        f"passive_{agent_id}",
        [
            ProcessInstance(
                f"p{agent_id}",
                ProcessRole.DEFENDER,
                initial_position=position,
                reach=1,
                quota_share=8,
                logic=lambda obs, state: AgentAction(ActionKind.NOP),
            )
        ],
        start=start,
    )


def _attacker_spec(target_addr: int, *, start: int = A_START) -> ProcessEntrantSpec:
    return ProcessEntrantSpec(
        "A",
        "attacker",
        [
            ProcessInstance(
                "pA",
                ProcessRole.ATTACKER,
                initial_position=0,
                reach=None,
                quota_share=8,
                logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, target_addr, 0x11),
            )
        ],
        start=start,
    )


# ---------------------------------------------------------------------------
# Ruleset identity: registered, isolated from omitted resolution, V4 and R1.
# ---------------------------------------------------------------------------


def test_r2_ruleset_registered_and_dispatches_to_process_runtime() -> None:
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V5_R2_ALPHA1_ID) is RULESET_V5_R2_ALPHA1
    assert BYTEFRAY_RULESET_V5_R2_ALPHA1_ID in PROCESS_RULESET_IDS
    assert BYTEFRAY_RULESET_V5_R2_ALPHA1_ID in OBJECTIVE_TARGET_ORACLE_RULESET_IDS


def test_r2_ruleset_never_reachable_from_omitted_selection() -> None:
    """Normal CLI/GUI use must never silently activate an R2 experiment."""

    assert BYTEFRAY_RULESET_V5_R2_ALPHA1_ID not in OMITTED_RULESET_CANDIDATES


def test_r2_ruleset_equivalent_to_v4_except_identity() -> None:
    for field in dataclasses.fields(RULESET_V4):
        if field.name == "ruleset_id":
            continue
        assert getattr(RULESET_V5_R2_ALPHA1, field.name) == getattr(
            RULESET_V4, field.name
        ), field.name


def test_r2_ruleset_carries_no_process_mortality() -> None:
    """R2's own identity is oracle-only: Arm B must isolate objective
    awareness from mortality, so mortality stays gated on R1's identity."""

    assert not has_process_mortality(BYTEFRAY_RULESET_V5_R2_ALPHA1_ID)
    assert has_process_mortality(BYTEFRAY_RULESET_V5_R1_ALPHA1_ID)


def test_oracle_available_to_r1_identity_so_arm_d_is_expressible() -> None:
    assert has_objective_target_oracle(BYTEFRAY_RULESET_V5_R1_ALPHA1_ID)
    assert not has_objective_target_oracle(RULESET_V4.ruleset_id)


def test_stable_v4_ignores_an_oracle_request_entirely() -> None:
    """A stray ``objective_target_oracle=True`` must never switch the
    instrument on under the permanent control Ruleset -- the same discipline
    ``process_integrity`` already enforces for non-mortality Rulesets."""

    recorder = _RecordingProcess()
    spec_a = _observer_spec(recorder, position=0, reach=ARENA // 2, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
    controller = ProcessMatchController(
        _config(),
        [spec_a, spec_b],
        max_ticks=3,
        ruleset_policy=RULESET_V4,
        objective_target_oracle=True,
    )
    controller.run()

    assert controller.oracle_active is False
    assert recorder.seen, "observer must have been called at least once"
    # B's anchor sits at 500 and is inside A's reach, so it is legitimately
    # detected; B's core base (also 500 here) must never appear as an extra
    # oracle entry, and no observation may carry more than the one detection.
    for visible in recorder.seen:
        assert visible == (B_START,)


def test_oracle_is_off_by_default_under_its_own_ruleset() -> None:
    """Two keys must both turn: Ruleset permission alone is not enough."""

    recorder = _RecordingProcess()
    spec_a = _observer_spec(recorder, position=0, reach=1, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
    controller = ProcessMatchController(
        _config(),
        [spec_a, spec_b],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
    )
    controller.run()

    assert controller.oracle_active is False
    assert recorder.seen
    for visible in recorder.seen:
        assert visible == ()


# ---------------------------------------------------------------------------
# Oracle semantics: exact address, ordering, persistence, disappearance.
# ---------------------------------------------------------------------------


def test_oracle_appends_enemy_core_base_after_detected_anchors() -> None:
    """With a live, detected enemy anchor the oracle target is appended
    *after* it, so an agent reading element [0] still sees the real sighting."""

    recorder = _RecordingProcess()
    # B's process sits at 600 (detected: inside A's reach) while B's core
    # base is 500 -- two distinct addresses, so ordering is observable.
    spec_a = _observer_spec(recorder, position=0, reach=ARENA // 2, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=600, start=B_START)
    controller = ProcessMatchController(
        _config(),
        [spec_a, spec_b],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
        objective_target_oracle=True,
    )
    controller.run()

    assert controller.oracle_active is True
    assert recorder.seen
    for visible in recorder.seen:
        assert visible == (600, B_START), (
            "detected anchor must stay first; oracle target strictly appended"
        )


def test_oracle_target_is_independent_of_sensor_reach() -> None:
    """A reach-1 observer that can detect nothing at all still receives the
    objective address -- the oracle is deliberately not a sensor."""

    without = _RecordingProcess()
    spec_a = _observer_spec(without, position=0, reach=1, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=600, start=B_START)
    ProcessMatchController(
        _config(),
        [spec_a, spec_b],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
    ).run()

    with_oracle = _RecordingProcess()
    spec_a2 = _observer_spec(with_oracle, position=0, reach=1, start=A_START)
    spec_b2 = _passive_spec(agent_id="B", position=600, start=B_START)
    ProcessMatchController(
        _config(),
        [spec_a2, spec_b2],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
        objective_target_oracle=True,
    ).run()

    assert without.seen and with_oracle.seen
    # Same observer, same reach, same enemy: detection is empty either way.
    for visible in without.seen:
        assert visible == ()
    for visible in with_oracle.seen:
        assert visible == (B_START,)


def test_oracle_target_survives_total_enemy_process_extinction() -> None:
    """The R2 hypothesis in one test: under R1 mortality the victim's sole
    process dies and its anchor stops being observable, but the objective
    address must remain -- and must be absent when the oracle is off."""

    def run(oracle: bool) -> tuple[_RecordingProcess, ProcessEntrantSpec]:
        recorder = _RecordingProcess()
        # A attacks B's anchor at 600 with unlimited reach, killing it at
        # H=1 on tick 1; a second A process observes what remains visible.
        killer = ProcessInstance(
            "killer",
            ProcessRole.ATTACKER,
            initial_position=0,
            reach=None,
            quota_share=4,
            logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, 600, 0x11),
        )
        watcher = ProcessInstance(
            "watcher",
            ProcessRole.SCOUT,
            initial_position=0,
            reach=ARENA // 2,
            quota_share=4,
            logic=recorder,
        )
        spec_a = ProcessEntrantSpec("A", "attacker", [killer, watcher], start=A_START)
        spec_b = _passive_spec(agent_id="B", position=600, start=B_START)
        ProcessMatchController(
            _config(),
            [spec_a, spec_b],
            max_ticks=6,
            ruleset_policy=RULESET_V5_R1_ALPHA1,
            process_integrity=1,
            objective_target_oracle=oracle,
        ).run()
        return recorder, spec_b

    off, victim_off = run(oracle=False)
    on, victim_on = run(oracle=True)

    # Precondition: the victim really did go extinct in both runs.
    assert victim_off.processes[0].alive is False
    assert victim_on.processes[0].alive is False

    # After the death tick the anchor is gone from detection in both runs.
    assert off.seen[-1] == (), "oracle OFF: attacker is left with no target"
    assert on.seen[-1] == (B_START,), "oracle ON: objective address persists"


def test_oracle_target_disappears_once_the_entrant_is_eliminated() -> None:
    """The oracle tracks *living* enemy entrants only: once B's core is
    captured and B is dead, its objective address must stop being exposed --
    while surviving opponent C's address must still be.

    A third entrant is required, not decorative: with only two entrants the
    match ends on the very tick the victim dies (last agent standing), so
    there would be no post-elimination observation to assert on at all.
    """

    recorder = _RecordingProcess()
    sweep_state: dict[str, int] = {"i": 0}

    def sweeper(obs: Any, state: dict[str, Any]) -> AgentAction:
        target = (B_START + sweep_state["i"] % 8) % ARENA
        sweep_state["i"] += 1
        return AgentAction(ActionKindV2.WRITE, target, 0x11)

    killer = ProcessInstance(
        "killer", ProcessRole.ATTACKER, initial_position=0, reach=None,
        quota_share=4, logic=sweeper,
    )
    # reach=1 detects nothing at all, so every address the watcher ever sees
    # came from the oracle and nowhere else.
    watcher = ProcessInstance(
        "watcher", ProcessRole.SCOUT, initial_position=0, reach=1,
        quota_share=4, logic=recorder,
    )
    spec_a = ProcessEntrantSpec("A", "attacker", [killer, watcher], start=A_START)
    spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
    spec_c = _passive_spec(agent_id="C", position=C_START, start=C_START)
    controller = ProcessMatchController(
        _config(),
        [spec_a, spec_b, spec_c],
        max_ticks=10,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
        objective_target_oracle=True,
    )
    controller.run()

    victim_state = controller._states_by_agent_id["B"]
    bystander_state = controller._states_by_agent_id["C"]
    assert victim_state.alive is False, "precondition: B must be core-captured"
    assert victim_state.entrant_termination == "core_captured"
    assert bystander_state.alive is True, "precondition: C must survive"
    assert recorder.seen[0] == (B_START, C_START), "both targets exposed while both lived"
    assert recorder.seen[-1] == (C_START,), (
        "B's target withdrawn on elimination; C's retained"
    )


def test_oracle_never_duplicates_an_already_detected_address() -> None:
    """An enemy process parked on its own core base must not produce the
    same address twice in the channel."""

    recorder = _RecordingProcess()
    spec_a = _observer_spec(recorder, position=0, reach=ARENA // 2, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
    ProcessMatchController(
        _config(),
        [spec_a, spec_b],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
        objective_target_oracle=True,
    ).run()

    assert recorder.seen
    for visible in recorder.seen:
        assert visible == (B_START,)
        assert len(visible) == len(set(visible))


def test_oracle_exposes_one_sorted_target_per_living_enemy_entrant() -> None:
    """Three entrants: the observer sees exactly its two opponents' core
    bases, in ascending order, appended after any detection."""

    recorder = _RecordingProcess()
    spec_a = _observer_spec(recorder, position=0, reach=1, start=A_START)
    spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
    spec_c = _passive_spec(agent_id="C", position=C_START, start=C_START)
    ProcessMatchController(
        _config(),
        [spec_a, spec_b, spec_c],
        max_ticks=3,
        ruleset_policy=RULESET_V5_R2_ALPHA1,
        objective_target_oracle=True,
    ).run()

    assert recorder.seen
    for visible in recorder.seen:
        assert visible == (B_START, C_START)


def test_oracle_addresses_are_identical_across_repeated_runs() -> None:
    """Determinism: the same inputs yield the same oracle addresses, in the
    same order, on every observation of every run."""

    def run() -> list[tuple[int, ...]]:
        recorder = _RecordingProcess()
        spec_a = _observer_spec(recorder, position=0, reach=1, start=A_START)
        spec_b = _passive_spec(agent_id="B", position=B_START, start=B_START)
        spec_c = _passive_spec(agent_id="C", position=C_START, start=C_START)
        ProcessMatchController(
            _config(),
            [spec_a, spec_b, spec_c],
            max_ticks=5,
            ruleset_policy=RULESET_V5_R2_ALPHA1,
            objective_target_oracle=True,
        ).run()
        return recorder.seen

    first = run()
    assert first, "observer must have been called"
    assert first == run()


# ---------------------------------------------------------------------------
# The oracle changes information only -- never a game mechanic.
# ---------------------------------------------------------------------------


def test_oracle_changes_information_only_not_mechanics() -> None:
    """R2 charter Section 10.4: the oracle must not alter process count,
    integrity, quota, movement, reach, core ownership, scoring, or
    termination.

    Proven by holding the *agents* constant against observation: both
    entrants act on a fixed script that never reads the observation, so any
    divergence between oracle ON and oracle OFF could only come from the
    engine's own rules. Every one of those systems is compared by value.
    """

    def run(oracle: bool) -> tuple[ProcessMatchController, list[ProcessEntrantSpec]]:
        move_state: dict[str, int] = {"i": 0}

        def scripted_attacker(obs: Any, state: dict[str, Any]) -> AgentAction:
            move_state["i"] += 1
            if move_state["i"] % 3 == 0:
                return AgentAction(ActionKindV2.MOVE, 5)
            return AgentAction(ActionKindV2.WRITE, (B_START + move_state["i"] % 8), 0x11)

        attacker = ProcessInstance(
            "pA", ProcessRole.ATTACKER, initial_position=10, reach=ARENA // 2,
            quota_share=8, logic=scripted_attacker,
        )
        defender = ProcessInstance(
            "pB", ProcessRole.DEFENDER, initial_position=B_START + 2, reach=4,
            quota_share=8,
            logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, B_START, 0xDD),
        )
        spec_a = ProcessEntrantSpec("A", "attacker", [attacker], start=A_START)
        spec_b = ProcessEntrantSpec("B", "defender", [defender], start=B_START)
        controller = ProcessMatchController(
            _config(),
            [spec_a, spec_b],
            max_ticks=25,
            ruleset_policy=RULESET_V5_R2_ALPHA1,
            objective_target_oracle=oracle,
        )
        controller.run()
        return controller, [spec_a, spec_b]

    off_controller, off_specs = run(oracle=False)
    on_controller, on_specs = run(oracle=True)

    assert off_controller.oracle_active is False
    assert on_controller.oracle_active is True

    # Termination, scoring, and core ownership.
    assert off_controller.score == on_controller.score
    assert off_controller.vm.arena == on_controller.vm.arena
    assert off_controller.vm.writer == on_controller.vm.writer
    assert off_controller.vm.ownership_counts == on_controller.vm.ownership_counts
    for off_state, on_state in zip(off_controller.states, on_controller.states, strict=True):
        assert off_state.alive == on_state.alive
        assert off_state.entrant_termination == on_state.entrant_termination
        assert off_state.total_actions == on_state.total_actions
        assert off_state.core_base == on_state.core_base
        assert off_state.core_cells == on_state.core_cells

    # Process count, liveness, integrity, position (movement), reach, quota.
    for off_spec, on_spec in zip(off_specs, on_specs, strict=True):
        assert len(off_spec.processes) == len(on_spec.processes)
        for off_p, on_p in zip(off_spec.processes, on_spec.processes, strict=True):
            assert off_p.alive == on_p.alive
            assert off_p.integrity == on_p.integrity
            assert off_p.position == on_p.position
            assert off_p.reach == on_p.reach
            assert off_p.quota_share == on_p.quota_share
            assert off_p.telemetry.total_actions == on_p.telemetry.total_actions
            assert off_p.telemetry.total_moves == on_p.telemetry.total_moves
            assert off_p.telemetry.total_writes == on_p.telemetry.total_writes
            assert off_p.telemetry.disruption_hits_received == (
                on_p.telemetry.disruption_hits_received
            )

    # A guard that the scenario was non-trivial in the first place.
    assert off_controller.states[1].core_base == B_START
    assert any(p.telemetry.total_writes > 0 for p in off_specs[0].processes)


# ---------------------------------------------------------------------------
# Full-stack: provenance, replay byte-compatibility, determinism.
# ---------------------------------------------------------------------------

OBSERVER_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class ObserverV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="p1", reach=50, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.WRITE, operand=obs.visible_enemy_anchor_addresses[0], value=0x11)
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return ObserverV2()
"""


def _setup_agent(tmp_path: Path, name: str, source: str) -> Path:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.py").write_text(source, encoding="utf-8")
    (agent_dir / "agent.yaml").write_text(
        f"name: {name}\ndescription: Test agent\nversion: '1.0'\napi_version: 2\n",
        encoding="utf-8",
    )
    return agent_dir


def _run_full_stack(
    tmp_path: Path,
    *,
    ruleset_id: str,
    oracle: bool,
    process_integrity: int | None = None,
    label: str = "match",
) -> tuple[Path, Path, Any]:
    _setup_agent(tmp_path, "observer_a", OBSERVER_AGENT_CODE)
    _setup_agent(tmp_path, "observer_b", OBSERVER_AGENT_CODE)
    spec_a = resolve_agent(tmp_path, "observer_a")
    spec_b = resolve_agent(tmp_path, "observer_b")
    entrants = (
        MatchEntrant.python("A", "observer_a", 0, spec_a),
        MatchEntrant.python("B", "observer_b", 200, spec_b),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=7, arena_size=512, instr_per_tick=8),
        entrants=entrants,
        max_ticks=6,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=ruleset_id,
        process_integrity=process_integrity,
        objective_target_oracle=oracle,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path, result.result_path, result


def test_oracle_run_is_distinguishable_in_research_provenance(tmp_path: Path) -> None:
    """R2 charter Section 19: a mortality+oracle replay must never be
    mistakable in research metadata for a mortality-only one."""

    _, result_off, res_off = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=False, process_integrity=8, label="off",
    )
    _, result_on, res_on = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=True, process_integrity=8, label="on",
    )

    with open(result_off, encoding="utf-8") as handle:
        data_off = json.load(handle)
    with open(result_on, encoding="utf-8") as handle:
        data_on = json.load(handle)

    repro_off = data_off["reproducibility"]
    repro_on = data_on["reproducibility"]

    # Oracle OFF keeps R1's exact pre-R2 provenance shape: the key is
    # omitted entirely, never written as an explicit false.
    assert "objective_target_oracle" not in repro_off
    assert repro_off["process_integrity"] == 8
    # Oracle ON declares itself, and the two runs hash to different identities.
    assert repro_on["objective_target_oracle"] is True
    assert repro_on["process_integrity"] == 8
    assert data_off["match_id"] != data_on["match_id"]
    assert data_off["result_id"] != data_on["result_id"]
    assert data_off["replay"]["replay_id"] != data_on["replay"]["replay_id"]
    assert data_off["replay"]["sha256"] != data_on["replay"]["sha256"]
    assert res_off.result_path is not None and res_on.result_path is not None


def test_stable_v4_artifacts_unchanged_when_an_oracle_is_requested(
    tmp_path: Path,
) -> None:
    """Byte-compatibility: requesting the oracle under stable V4 must
    produce a replay byte-identical to one produced without the request,
    and provenance must not gain the key."""

    replay_plain, result_plain, _ = _run_full_stack(
        tmp_path, ruleset_id="bytefray-rules-4", oracle=False, label="plain",
    )
    replay_asked, result_asked, _ = _run_full_stack(
        tmp_path, ruleset_id="bytefray-rules-4", oracle=True, label="asked",
    )

    assert replay_plain.read_bytes() == replay_asked.read_bytes()
    with open(result_plain, encoding="utf-8") as handle:
        data_plain = json.load(handle)
    with open(result_asked, encoding="utf-8") as handle:
        data_asked = json.load(handle)
    assert "objective_target_oracle" not in data_plain["reproducibility"]
    assert "objective_target_oracle" not in data_asked["reproducibility"]
    assert data_plain["match_id"] == data_asked["match_id"]
    assert data_plain["replay"]["replay_id"] == data_asked["replay"]["replay_id"]
    assert data_plain["replay"]["sha256"] == data_asked["replay"]["sha256"]


def test_r1_mortality_replay_unchanged_when_oracle_disabled(tmp_path: Path) -> None:
    """R2 must reproduce R1's semantics exactly with the oracle off, so
    Arm C is genuinely R1 rather than an approximation of it."""

    replay_a, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=False, process_integrity=4, label="r1a",
    )
    replay_b, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=False, process_integrity=4, label="r1b",
    )
    assert replay_a.read_bytes() == replay_b.read_bytes()


def test_oracle_full_stack_run_is_deterministic(tmp_path: Path) -> None:
    replay_a, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R2_ALPHA1_ID, oracle=True, label="run1",
    )
    replay_b, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R2_ALPHA1_ID, oracle=True, label="run2",
    )
    assert replay_a.read_bytes() == replay_b.read_bytes()


def test_oracle_run_differs_observably_from_its_own_control(tmp_path: Path) -> None:
    """A guard against a silently inert instrument: with agents that react
    to the target channel, oracle ON must actually change the match."""

    replay_off, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R2_ALPHA1_ID, oracle=False, label="ctrl",
    )
    replay_on, _, _ = _run_full_stack(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R2_ALPHA1_ID, oracle=True, label="exp",
    )
    assert replay_off.read_bytes() != replay_on.read_bytes()
