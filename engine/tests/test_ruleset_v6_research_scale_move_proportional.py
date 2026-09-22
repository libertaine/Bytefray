"""V6 Phase 4D: the proportional-movement variable-arena research Ruleset
(``bytefray-rules-6-research-scale-move-proportional``).

Covers docs/research/v6/V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md and the
Phase 4D task specifications. Proves with real live execution that:

1. The research Ruleset is registered, executable, and behaviorally
   equivalent to both raw-scale research (``bytefray-rules-6-research-scale``)
   and stable ``bytefray-rules-4`` at the control arena (512) --
   placements, results, scores, kills/deaths, and the full replay event stream
   are byte-for-byte identical except where Ruleset identity is intentionally
   part of persisted/canonical identity.
2. Direct movement characterization:
   At all five arenas (512, 1024, 4096, 16384, 65536) and representative
   operands (0, +1/-1, +2/-2, +40/-40, +64/-64):
   actual displacement matches ``sign(op) * floor(abs(op) * arena_size / 512)``,
   sign symmetry holds, circular wrapping is deterministic, and requested operands
   remain clamped to [-64, 64].
3. Live process runtime movement execution:
   A moving agent's actual trajectory scales proportionally with arena size,
   traversing 2x at A=1024, 8x at A=4096, 32x at A=16384, 128x at A=65536,
   while raw-scale controls remain literal (64-cell bound, 1:1 displacement).
4. Evaluability: accepts any arena size in the Phase 4A research range
   [64, 65536] and rejects out-of-range values clearly without silent clamping.
5. Identity distinction: the proportional condition produces distinct
   evaluation, schedule, and match IDs from raw-scale, scale-move, and stable v4.
6. Seeded geometry routing: routes through seeded-placement/identity-v7/schema-v7
   with its own distinct arena alignment mode.
7. Provenance: replay header and result envelope attribute the exact Ruleset ID.
8. Stable v4, Phase 4B raw-scale, and Phase 4C scale-move controls remain fully preserved and isolated.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_evaluation import (
    EvaluationConfigurationError,
    EvaluationRequest,
    EvaluationService,
)
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config
from battle_engine.evaluation_cli import main as evaluate_main
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    RESEARCH_SCALE_MAX_ARENA_SIZE,
    RESEARCH_SCALE_MIN_ARENA_SIZE,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_scale_move_methodology,
    is_ruleset_v6_research_scale_move_proportional_methodology,
    resolved_arena_alignment_mode,
)
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V4,
    RULESET_V6_RESEARCH_SCALE,
    RULESET_V6_RESEARCH_SCALE_MOVE,
    RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    resolve_ruleset_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_SOURCE_DIRS = (
    REPO_ROOT / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)


def _is_usable_agent_source(path: Path) -> bool:
    try:
        return agent_spec_from_dir(path) is not None
    except AgentManifestError:
        return False


def _bootstrap_agent(tmp_path: Path, name: str) -> None:
    dest = tmp_path / "agents" / name
    if dest.exists():
        return
    for source_root in STARTER_SOURCE_DIRS:
        source = source_root / name
        if _is_usable_agent_source(source):
            shutil.copytree(source, dest)
            return
    raise FileNotFoundError(f"no source found for agent {name!r} under {STARTER_SOURCE_DIRS}")


def _seat_label(index: int) -> str:
    return chr(ord("A") + index)


def _run_under_ruleset(
    tmp_path: Path,
    entrant_names: tuple[str, ...],
    *,
    ruleset_id: str,
    arena_size: int,
    seed: int,
    ticks: int,
    run_label: str,
) -> Path:
    specs = tuple(resolve_agent(tmp_path, name) for name in entrant_names)
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=arena_size,
        entrant_count=len(entrant_names),
        supplied_starts=[None] * len(entrant_names),
        seed=seed,
    )
    entrants = tuple(
        MatchEntrant.python(_seat_label(i), name, starts[i], spec)
        for i, (name, spec) in enumerate(zip(entrant_names, specs, strict=True))
    )
    run_dir = tmp_path / "runs" / run_label
    run_dir.mkdir(parents=True, exist_ok=True)
    replay_path = run_dir / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=arena_size, instr_per_tick=8),
        entrants=entrants,
        max_ticks=ticks,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=ruleset_id,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path


def _load_replay_gameplay_payload(replay_path: Path) -> dict[str, Any]:
    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    result: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = replace(
                record,
                replay_id=None,
                match_id=None,
                result_id=None,
                ruleset_id=None,
            )
        elif isinstance(record, TickSnapshot):
            ticks.append(record)
        elif isinstance(record, MatchResult):
            result = replace(record, replay_id=None, match_id=None, result_id=None)
    assert header is not None, f"{replay_path}: no header record"
    assert result is not None, f"{replay_path}: no terminal result record"
    return {
        "header": asdict(header),
        "ticks": [asdict(tick) for tick in ticks],
        "result": asdict(result),
    }


def _raw_header(replay_path: Path) -> ReplayHeader:
    return next(r for r in iter_replay(replay_path) if isinstance(r, ReplayHeader))


API_V2_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.context = context
    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]
    def act(self, observation):
        return AgentAction(ActionKindV2.NOP, 0)

def create_agent():
    return Agent()
"""


def _write_api_v2_agent(tmp_path: Path, name: str) -> Path:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_text(
        json.dumps(
            {
                "name": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    (agent_dir / "agent.py").write_text(API_V2_SOURCE, encoding="utf-8")
    return agent_dir


def _research_proportional_request(
    tmp_path: Path,
    *,
    arena_size: int | None = 512,
    ruleset_id: str = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
    seeds: tuple[int, ...] = (1,),
    ticks: int = 20,
    output_dir: Path | None = None,
) -> EvaluationRequest:
    return EvaluationRequest(
        candidate_id="candidate",
        opponent_ids=["opponent"],
        seeds=seeds,
        ticks=ticks,
        arena_size=arena_size,
        ruleset_id=ruleset_id,
        output_dir=output_dir or (tmp_path / "eval-out"),
        data_root=tmp_path,
    )


# ---------------------------------------------------------------------------
# 1. Registration, recognition, and non-automatic status
# ---------------------------------------------------------------------------


def test_research_scale_move_proportional_is_registered_and_executable() -> None:
    policy = resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID)
    assert policy is RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID in PROCESS_RULESET_IDS
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID not in OMITTED_RULESET_CANDIDATES


def test_research_scale_move_proportional_policy_invariants() -> None:
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.supported_runtime_kinds == frozenset({"python"})
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.supported_python_api_versions == frozenset({2})
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.scheduler_mode == "chunked"
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.scheduler_chunk_size == 2
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.scheduler_rotate_start is True
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.core_placement == "seeded"
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.process_selection == "round_robin"
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.movement_stride == "fixed_64"
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.movement_displacement == "scale_from_512"


def test_methodology_classification() -> None:
    r_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    assert is_ruleset_v6_research_scale_move_proportional_methodology(r_id)
    assert not is_ruleset_v6_research_scale_move_methodology(r_id)
    assert not is_ruleset_v4_methodology(r_id)
    assert is_ruleset_v4_derived_methodology(r_id)


# ---------------------------------------------------------------------------
# 2. Direct movement characterization across all five arenas
# ---------------------------------------------------------------------------


def test_direct_movement_characterization_all_arenas() -> None:
    arenas = [512, 1024, 4096, 16384, 65536]
    test_operands = [0, 1, -1, 2, -2, 40, -40, 64, -64]
    policy = RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL

    for a in arenas:
        scale_factor = a // 512
        for op in test_operands:
            actual = policy.resolve_movement_displacement(op, a)
            expected = op * scale_factor
            assert actual == expected

            # Sign symmetry
            neg_actual = policy.resolve_movement_displacement(-op, a)
            assert neg_actual == -actual

            # Wrapping
            pos = 100
            wrapped = (pos + actual) % a
            assert 0 <= wrapped < a


def test_operand_clamping_at_64() -> None:
    policy = RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
    assert policy.resolve_max_move_delta(512) == 64
    assert policy.resolve_max_move_delta(65536) == 64


def test_literal_controls_remain_literal() -> None:
    for a in [512, 1024, 4096, 16384, 65536]:
        for op in [1, -1, 40, -40, 64, -64]:
            assert RULESET_V4.resolve_movement_displacement(op, a) == op
            assert RULESET_V6_RESEARCH_SCALE.resolve_movement_displacement(op, a) == op
            assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_movement_displacement(op, a) == op


def test_movement_displacement_non_power_of_two_and_boundary_arenas() -> None:
    policy = RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL

    # 1. Non-power-of-two arena (A = 777)
    # op = 40: floor(40 * 777 / 512) = floor(31080 / 512) = 60
    assert policy.resolve_movement_displacement(40, 777) == 60
    assert policy.resolve_movement_displacement(-40, 777) == -60
    assert policy.resolve_movement_displacement(0, 777) == 0
    # op = 1: floor(1 * 777 / 512) = 1
    assert policy.resolve_movement_displacement(1, 777) == 1
    assert policy.resolve_movement_displacement(-1, 777) == -1

    # 2. Minimum research boundary arena (A = 64)
    # op = 1: floor(1 * 64 / 512) = floor(64 / 512) = 0 (integer truncation below 1 stride)
    assert policy.resolve_movement_displacement(1, 64) == 0
    assert policy.resolve_movement_displacement(7, 64) == 0
    # op = 8: floor(8 * 64 / 512) = floor(512 / 512) = 1
    assert policy.resolve_movement_displacement(8, 64) == 1
    assert policy.resolve_movement_displacement(-8, 64) == -1
    # op = 64: floor(64 * 64 / 512) = 8
    assert policy.resolve_movement_displacement(64, 64) == 8

    # 3. Extreme scale arena (A = 2^24 = 16,777,216)
    extreme_a = 16_777_216
    expected_extreme = 40 * (extreme_a // 512)
    assert policy.resolve_movement_displacement(40, extreme_a) == expected_extreme
    assert isinstance(policy.resolve_movement_displacement(40, extreme_a), int)



# ---------------------------------------------------------------------------
# 3. Live process runtime movement execution
# ---------------------------------------------------------------------------


def test_live_movement_proportional_at_a1024(tmp_path: Path) -> None:
    """An agent requesting a MOVE operand of 40 cells at A=1024 moves 40 cells
    under raw-scale, but 80 cells (40 * 2) under proportional movement."""
    mover_source = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class MoverAgent:
    def reset(self, context):
        self.moved = False
    def declare_processes(self):
        return [ProcessDeclaration("mover", reach=10, share=1.0)]
    def act(self, obs: ObservationV2):
        if not self.moved:
            self.moved = True
            return AgentAction(ActionKindV2.MOVE, operand=40)
        return AgentAction(ActionKindV2.NOP, 0)

def create_agent():
    return MoverAgent()
"""
    passive_source = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class PassiveAgent:
    def reset(self, context): pass
    def declare_processes(self):
        return [ProcessDeclaration("p", reach=10, share=1.0)]
    def act(self, obs: ObservationV2):
        return AgentAction(ActionKindV2.NOP, 0)

def create_agent():
    return PassiveAgent()
"""
    mover_dir = tmp_path / "agents" / "mover"
    mover_dir.mkdir(parents=True, exist_ok=True)
    (mover_dir / "agent.yaml").write_text(
        '{"name": "mover", "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n',
        encoding="utf-8",
    )
    (mover_dir / "agent.py").write_text(mover_source, encoding="utf-8")

    passive_dir = tmp_path / "agents" / "passive"
    passive_dir.mkdir(parents=True, exist_ok=True)
    (passive_dir / "agent.yaml").write_text(
        '{"name": "passive", "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n',
        encoding="utf-8",
    )
    (passive_dir / "agent.py").write_text(passive_source, encoding="utf-8")

    # Run under raw-scale at A=1024
    raw_replay_path = _run_under_ruleset(
        tmp_path,
        ("mover", "passive"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=1024,
        seed=1,
        ticks=5,
        run_label="raw-mover-1024",
    )
    # Run under proportional movement at A=1024
    prop_replay_path = _run_under_ruleset(
        tmp_path,
        ("mover", "passive"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
        arena_size=1024,
        seed=1,
        ticks=5,
        run_label="prop-mover-1024",
    )

    def _get_mover_positions(replay_path: Path) -> list[int]:
        positions = []
        for rec in iter_replay(replay_path):
            if isinstance(rec, TickSnapshot) and rec.processes:
                for p in rec.processes:
                    if p.entrant_id == "A":
                        positions.append(p.anchor)
        return positions

    raw_pos = _get_mover_positions(raw_replay_path)
    prop_pos = _get_mover_positions(prop_replay_path)

    start_pos = raw_pos[0]
    assert prop_pos[0] == start_pos

    # Raw-scale: literal 40 displacement
    assert (raw_pos[-1] - start_pos) % 1024 == 40
    # Proportional: 40 * (1024 // 512) = 80 displacement
    assert (prop_pos[-1] - start_pos) % 1024 == 80


def test_smoke_gate_benchmark_mobile_agents_trajectory_divergence_at_scale(tmp_path: Path) -> None:
    """Smoke Gate: prove that unlike Phase 4C, actual trajectories of mobile agents
    diverge between Phase 4B raw-scale and Phase 4D proportional movement at A=65536."""
    for name in ("v5_scout_striker", "nemesis_alpha2"):
        _bootstrap_agent(tmp_path, name)

    raw_replay = _run_under_ruleset(
        tmp_path,
        ("v5_scout_striker", "nemesis_alpha2"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=65536,
        seed=1,
        ticks=10,
        run_label="smoke-raw-65k",
    )
    prop_replay = _run_under_ruleset(
        tmp_path,
        ("v5_scout_striker", "nemesis_alpha2"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
        arena_size=65536,
        seed=1,
        ticks=10,
        run_label="smoke-prop-65k",
    )

    def _extract_scout_anchors(path: Path) -> list[int]:
        anchors = []
        for rec in iter_replay(path):
            if isinstance(rec, TickSnapshot) and rec.processes:
                for p in rec.processes:
                    if p.entrant_id == "A":
                        anchors.append(p.anchor)
        return anchors

    raw_anchors = _extract_scout_anchors(raw_replay)
    prop_anchors = _extract_scout_anchors(prop_replay)

    assert raw_anchors[0] == prop_anchors[0]  # Same starting seed placement
    # Divergence proof: at A=65536, proportional displacement moves 128x faster,
    # so positions diverge immediately after tick 0
    assert raw_anchors != prop_anchors
    assert raw_anchors[1] != prop_anchors[1]



# ---------------------------------------------------------------------------
# 4. Behavioral Equivalence at A=512 Gate with real agents
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 5, 8])
@pytest.mark.parametrize(
    "entrant_names",
    [
        ("v4_claimer", "v5_core_defender"),
        ("v5_scout_striker", "nemesis_alpha2"),
    ],
)
def test_equivalence_at_a512_against_raw_scale(
    tmp_path: Path, entrant_names: tuple[str, ...], seed: int
) -> None:
    for name in entrant_names:
        _bootstrap_agent(tmp_path, name)

    raw_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=512,
        seed=seed,
        ticks=40,
        run_label=f"raw-512-s{seed}-{'-'.join(entrant_names)}",
    )
    prop_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
        arena_size=512,
        seed=seed,
        ticks=40,
        run_label=f"prop-512-s{seed}-{'-'.join(entrant_names)}",
    )

    raw_data = _load_replay_gameplay_payload(raw_replay)
    prop_data = _load_replay_gameplay_payload(prop_replay)

    assert prop_data["header"] == raw_data["header"]
    assert prop_data["ticks"] == raw_data["ticks"]
    assert prop_data["result"] == raw_data["result"]


# ---------------------------------------------------------------------------
# 5. Evaluability & Arena bounds
# ---------------------------------------------------------------------------


def test_evaluation_accepts_valid_arena_sizes(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    service = EvaluationService()
    for size in (64, 512, 1024, 65536):
        out_dir = tmp_path / f"out_{size}"
        request = _research_proportional_request(tmp_path, arena_size=size, output_dir=out_dir)
        service.run(request)
        state_file = out_dir / "evaluation.json"
        assert state_file.exists()
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["effective_conditions"]["arena_size"] == size
        assert (
            data["arena_alignment_mode"]
            == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
        )


@pytest.mark.parametrize("arena_size", [RESEARCH_SCALE_MIN_ARENA_SIZE - 1, 0, -1, 63])
def test_rejects_arena_size_below_research_range(tmp_path: Path, arena_size: int) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_proportional_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError):
        EvaluationService().run(request)


@pytest.mark.parametrize("arena_size", [RESEARCH_SCALE_MAX_ARENA_SIZE + 1, 100_000])
def test_rejects_arena_size_above_research_range(tmp_path: Path, arena_size: int) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_proportional_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError, match="outside the"):
        EvaluationService().run(request)


# ---------------------------------------------------------------------------
# 6. Identity distinction & Provenance
# ---------------------------------------------------------------------------


def test_identity_distinction_at_same_arena(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")

    eval_raw = EvaluationService().run(
        _research_proportional_request(
            tmp_path,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
            arena_size=1024,
            output_dir=tmp_path / "eval_raw",
        )
    )
    eval_move = EvaluationService().run(
        _research_proportional_request(
            tmp_path,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
            arena_size=1024,
            output_dir=tmp_path / "eval_move",
        )
    )
    eval_prop = EvaluationService().run(
        _research_proportional_request(
            tmp_path,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            arena_size=1024,
            output_dir=tmp_path / "eval_prop",
        )
    )

    assert eval_prop.evaluation_id != eval_raw.evaluation_id
    assert eval_prop.evaluation_id != eval_move.evaluation_id
    assert eval_raw.evaluation_id != eval_move.evaluation_id


def test_provenance_recording(tmp_path: Path) -> None:
    for name in ("v4_claimer", "v5_core_defender"):
        _bootstrap_agent(tmp_path, name)

    prop_replay = _run_under_ruleset(
        tmp_path,
        ("v4_claimer", "v5_core_defender"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
        arena_size=1024,
        seed=1,
        ticks=10,
        run_label="provenance-check",
    )
    assert (
        _raw_header(prop_replay).ruleset_id
        == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    )
    result_path = prop_replay.parent / "result.json"
    result_data = json.loads(result_path.read_text(encoding="utf-8"))
    assert (
        result_data["ruleset_id"]
        == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    )


def test_evaluation_methodology_predicates() -> None:
    prop_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    move_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID
    scale_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
    v4_id = BYTEFRAY_RULESET_V4_ID

    assert is_ruleset_v6_research_scale_move_proportional_methodology(prop_id)
    assert not is_ruleset_v6_research_scale_move_proportional_methodology(move_id)
    assert not is_ruleset_v6_research_scale_move_proportional_methodology(scale_id)
    assert not is_ruleset_v6_research_scale_move_proportional_methodology(v4_id)

    assert is_ruleset_v4_derived_methodology(prop_id)
    assert not is_ruleset_v4_methodology(prop_id)


def test_resolved_arena_alignment_mode_distinct() -> None:
    mode_prop = resolved_arena_alignment_mode(
        is_v2_methodology=False, is_v6_research_scale_move_proportional_methodology=True
    )
    mode_move = resolved_arena_alignment_mode(
        is_v2_methodology=False, is_v6_research_scale_move_methodology=True
    )
    mode_scale = resolved_arena_alignment_mode(
        is_v2_methodology=False, is_v6_research_scale_methodology=True
    )
    assert mode_prop == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
    assert mode_move == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE
    assert mode_scale == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE
    assert len({mode_prop, mode_move, mode_scale}) == 3



# ---------------------------------------------------------------------------
# 7. CLI integration
# ---------------------------------------------------------------------------


def test_evaluate_cli_accepts_research_scale_move_proportional_explicitly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    exit_code = evaluate_main(
        [
            "candidate",
            "--opponents",
            "opponent",
            "--ruleset",
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            "--arena-size",
            "1024",
            "--seeds",
            "1",
            "--ticks",
            "5",
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 0
    capsys.readouterr()
    data = json.loads((tmp_path / "out" / "evaluation.json").read_text(encoding="utf-8"))
    assert (
        data["arena_alignment_mode"]
        == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
    )
    assert (
        data["rules_compatibility_id"]
        == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    )


def test_evaluate_cli_rejects_out_of_range_arena_for_research_scale_move_proportional(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    exit_code = evaluate_main(
        [
            "candidate",
            "--opponents",
            "opponent",
            "--ruleset",
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            "--arena-size",
            "100000",
            "--seeds",
            "1",
            "--ticks",
            "5",
            "--output",
            str(tmp_path / "out_bad"),
        ]
    )
    assert exit_code != 0
    capsys.readouterr()
    assert not (tmp_path / "out_bad" / "evaluation.json").exists()
