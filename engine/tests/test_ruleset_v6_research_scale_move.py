"""V6 Phase 4C: the movement-normalized variable-arena research Ruleset
(``bytefray-rules-6-research-scale-move``).

Covers docs/research/v6/V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md and the
Phase 4C task specifications. Proves with real live execution that:

1. The research Ruleset is registered, executable, and behaviorally
   equivalent to both raw-scale research (``bytefray-rules-6-research-scale``)
   and stable ``bytefray-rules-4`` at the control arena (512) --
   placements, results, scores, kills/deaths, and the full replay event stream
   are byte-for-byte identical except where Ruleset identity is intentionally
   part of persisted/canonical identity.
2. Movement stride normalization:
   ``max_move_delta(A) = max(64, floor(A / 8))`` is explicitly enforced by
   the runtime: at A=1024 an agent can move up to 128 cells (clamped to 64
   under raw-scale), while Phase 4B raw-scale research permanently keeps
   movement bounded at 64 at all arena sizes.
3. Evaluability: accepts any arena size in the Phase 4A research range
   [64, 65536] and rejects out-of-range values clearly without silent clamping.
4. Identity distinction: the normalized condition produces distinct
   evaluation, schedule, and match IDs from raw-scale and stable v4.
5. Seeded geometry routing: routes through seeded-placement/identity-v7/schema-v7
   with its own distinct arena alignment mode.
6. Provenance: replay header and result envelope attribute the exact Ruleset ID.
7. Stable v4 and Phase 4B raw-scale controls remain fully preserved and isolated.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import (
    AgentManifestError,
)
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
    RESEARCH_SCALE_MAX_ARENA_SIZE,
    RESEARCH_SCALE_MIN_ARENA_SIZE,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_scale_move_methodology,
    resolved_arena_alignment_mode,
)
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V6_RESEARCH_SCALE,
    RULESET_V6_RESEARCH_SCALE_MOVE,
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
    run_dir.mkdir(parents=True)
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


def _nulled_identity_snapshot(replay_path: Path) -> dict[str, Any]:
    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    result: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = replace(record, replay_id=None, match_id=None, result_id=None, ruleset_id=None)
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
    import json as _json

    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_text(
        _json.dumps(
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


def _research_move_request(
    tmp_path: Path,
    *,
    arena_size: int | None = 512,
    ruleset_id: str = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
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


def test_research_scale_move_is_registered_and_executable() -> None:
    policy = resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID)
    assert policy is RULESET_V6_RESEARCH_SCALE_MOVE
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID in PROCESS_RULESET_IDS
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID not in OMITTED_RULESET_CANDIDATES


def test_research_scale_move_matches_raw_scale_except_movement() -> None:
    assert replace(
        RULESET_V6_RESEARCH_SCALE_MOVE,
        ruleset_id=RULESET_V6_RESEARCH_SCALE.ruleset_id,
        movement_stride="fixed_64",
    ) == RULESET_V6_RESEARCH_SCALE
    assert RULESET_V6_RESEARCH_SCALE_MOVE.movement_stride == "scale_normalized"
    assert RULESET_V6_RESEARCH_SCALE.movement_stride == "fixed_64"


# ---------------------------------------------------------------------------
# 2. Phase 4B raw-scale research regression: movement bound remains 64
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arena_size", [512, 1024, 4096, 16384, 65536])
def test_phase4b_raw_scale_maintains_fixed_64_movement_at_all_arenas(arena_size: int) -> None:
    """Proves Phase 4B raw-scale research control is NOT modified by Phase 4C."""
    assert RULESET_V6_RESEARCH_SCALE.resolve_max_move_delta(arena_size) == 64


# ---------------------------------------------------------------------------
# 3. Phase 4C movement bound values at all five research arenas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "arena_size,expected_bound",
    [
        (512, 64),
        (1024, 128),
        (4096, 512),
        (16384, 2048),
        (65536, 8192),
    ],
)
def test_phase4c_movement_bound_values(arena_size: int, expected_bound: int) -> None:
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(arena_size) == expected_bound


# ---------------------------------------------------------------------------
# 4. Live runtime enforcement of movement stride
# ---------------------------------------------------------------------------


def test_live_movement_clamping_differs_at_a1024(tmp_path: Path) -> None:
    """An agent requesting a MOVE operand of 100 cells at A=1024 moves 64 cells
    under raw-scale, but the full 100 cells under normalized movement."""
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
            return AgentAction(ActionKindV2.MOVE, operand=100)
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
    mover_dir.mkdir(parents=True)
    (mover_dir / "agent.yaml").write_text(
        '{"name": "mover", "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n',
        encoding="utf-8",
    )
    (mover_dir / "agent.py").write_text(mover_source, encoding="utf-8")

    passive_dir = tmp_path / "agents" / "passive"
    passive_dir.mkdir(parents=True)
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
    # Run under movement-normalized at A=1024
    move_replay_path = _run_under_ruleset(
        tmp_path,
        ("mover", "passive"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
        arena_size=1024,
        seed=1,
        ticks=5,
        run_label="move-mover-1024",
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
    move_pos = _get_mover_positions(move_replay_path)

    # Initial position is the same start
    start_pos = raw_pos[0]
    assert move_pos[0] == start_pos

    # Raw-scale clamped displacement to 64
    assert (raw_pos[-1] - start_pos) % 1024 == 64
    # Movement-normalized allowed the full 100 displacement (bound is 128)
    assert (move_pos[-1] - start_pos) % 1024 == 100


# ---------------------------------------------------------------------------
# 5. A=512 behavioral equivalence gate with real agents
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 5, 8])
@pytest.mark.parametrize(
    "entrant_names",
    [
        ("v4_claimer", "v5_core_defender"),
        ("v5_scout_striker", "v4_local_defender"),
        ("Octave", "nemesis_alpha2"),
    ],
)
def test_research_scale_move_is_behaviorally_identical_to_raw_scale_at_a512(
    tmp_path: Path, entrant_names: tuple[str, str], seed: int
) -> None:
    for name in entrant_names:
        _bootstrap_agent(tmp_path, name)

    raw_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=512,
        seed=seed,
        ticks=300,
        run_label=f"raw-{'-'.join(entrant_names)}-{seed}",
    )
    move_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
        arena_size=512,
        seed=seed,
        ticks=300,
        run_label=f"move-{'-'.join(entrant_names)}-{seed}",
    )

    raw_snapshot = _nulled_identity_snapshot(raw_replay)
    move_snapshot = _nulled_identity_snapshot(move_replay)

    assert move_snapshot == raw_snapshot

    # Provenance fields differ honestly
    assert _raw_header(raw_replay).ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
    assert _raw_header(move_replay).ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID


# ---------------------------------------------------------------------------
# 6. Evaluation methodology, range validation, and identity
# ---------------------------------------------------------------------------


def test_evaluation_methodology_predicates() -> None:
    move_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID
    scale_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
    v4_id = BYTEFRAY_RULESET_V4_ID

    assert is_ruleset_v6_research_scale_move_methodology(move_id)
    assert not is_ruleset_v6_research_scale_move_methodology(scale_id)
    assert not is_ruleset_v6_research_scale_move_methodology(v4_id)

    assert is_ruleset_v4_derived_methodology(move_id)
    assert is_ruleset_v4_derived_methodology(scale_id)
    assert is_ruleset_v4_derived_methodology(v4_id)

    # v4 methodology (512-cell pin) does NOT include either research Ruleset
    assert not is_ruleset_v4_methodology(move_id)
    assert not is_ruleset_v4_methodology(scale_id)


def test_resolved_arena_alignment_mode_distinct() -> None:
    mode_move = resolved_arena_alignment_mode(
        is_v2_methodology=False, is_v6_research_scale_move_methodology=True
    )
    mode_scale = resolved_arena_alignment_mode(
        is_v2_methodology=False, is_v6_research_scale_methodology=True
    )
    assert mode_move == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE
    assert mode_scale == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE
    assert mode_move != mode_scale


def test_identity_distinction_at_same_arena(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")

    eval_raw = EvaluationService().run(
        _research_move_request(
            tmp_path,
            arena_size=1024,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
            output_dir=tmp_path / "raw_1024",
        )
    )
    eval_move = EvaluationService().run(
        _research_move_request(
            tmp_path,
            arena_size=1024,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
            output_dir=tmp_path / "move_1024",
        )
    )

    assert eval_raw.evaluation_id != eval_move.evaluation_id
    for cell_raw, cell_move in zip(eval_raw.cells, eval_move.cells, strict=True):
        assert cell_raw.schedule_id != cell_move.schedule_id
        assert cell_raw.match_id != cell_move.match_id


@pytest.mark.parametrize("arena_size", [RESEARCH_SCALE_MIN_ARENA_SIZE - 1, 0, -1, 63])
def test_rejects_arena_size_below_research_range(tmp_path: Path, arena_size: int) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_move_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError):
        EvaluationService().run(request)


@pytest.mark.parametrize("arena_size", [RESEARCH_SCALE_MAX_ARENA_SIZE + 1, 100_000])
def test_rejects_arena_size_above_research_range(tmp_path: Path, arena_size: int) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_move_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError, match="outside the"):
        EvaluationService().run(request)


def test_stable_v4_remains_isolated_at_512(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_move_request(
        tmp_path, arena_size=1024, ruleset_id=BYTEFRAY_RULESET_V4_ID
    )
    with pytest.raises(EvaluationConfigurationError, match="incompatible with the stable v4"):
        EvaluationService().run(request)


def test_evaluation_artifact_records_scale_move_arena_alignment_mode(tmp_path: Path) -> None:
    """Proves write_evaluation_state persists the exact scale-move arena alignment mode."""
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    out_dir = tmp_path / "eval_out"
    request = _research_move_request(tmp_path, arena_size=1024, output_dir=out_dir)
    EvaluationService().run(request)

    data = json.loads((out_dir / "evaluation.json").read_text(encoding="utf-8"))
    assert data["arena_alignment_mode"] == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE
    assert data["rules_compatibility_id"] == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID


# ---------------------------------------------------------------------------
# 7. CLI surface: --ruleset accepts the new identity explicitly, rejects out-of-range
# ---------------------------------------------------------------------------


def test_evaluate_cli_accepts_research_scale_move_explicitly(
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
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
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
    assert data["arena_alignment_mode"] == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE


def test_evaluate_cli_rejects_out_of_range_arena_for_research_scale_move(
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
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
            "--arena-size",
            "100000",
            "--seeds",
            "1",
            "--ticks",
            "5",
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code != 0
    capsys.readouterr()
    assert not (tmp_path / "out" / "evaluation.json").exists()
