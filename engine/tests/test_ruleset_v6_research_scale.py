"""V6 Phase 4B: the variable-arena research Ruleset
(``bytefray-rules-6-research-scale``).

Covers docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md Sec 10.2
and the Phase 4B implementation task's Sec 30 test list. This file proves,
with real live execution (never a hand-built fixture), that:

1. The research Ruleset is registered, executable, and behaviorally
   equivalent to stable ``bytefray-rules-4`` at the control arena (512) --
   scheduler, seeded placement, process order, scores, and the full replay
   event stream are identical except where Ruleset identity is
   intentionally part of persisted/canonical identity.
2. It is evaluable at arena sizes stable v4 forbids, within the Phase 4A
   research range, and rejects out-of-range values clearly rather than
   clamping.
3. Arena size and Ruleset identity are genuinely identity-bearing: two
   evaluations differing only in arena size produce different
   evaluation/schedule/match identities.
4. It routes through the seeded-placement/identity-v7/schema-v7 machinery
   (never legacy identity version 2, fixed placements, or ``(0, 0)``
   coordinates), while stable v4's own 512-cell lock and identity remain
   completely untouched.

See ``test_v4_stable_ruleset_equivalence.py`` for the pattern this file's
live-comparison helpers are modeled on, and ``test_ruleset_policy.py`` for
the ``RulesetPolicy``-field-equality regression guard (checked there, not
duplicated here).
"""

from __future__ import annotations

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
from battle_engine.agent_evaluation import main as evaluate_main
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
    IDENTITY_VERSION_V4,
    ORIENTATION_OPPONENT_FIRST,
    RESEARCH_SCALE_MAX_ARENA_SIZE,
    RESEARCH_SCALE_MIN_ARENA_SIZE,
    SCHEMA_VERSION_V4,
    STANDARD_V4_ARENA_SIZE,
    is_ruleset_v4_derived_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_scale_methodology,
    resolved_arena_alignment_mode,
    resolved_identity_version,
    resolved_schema_version,
)
from battle_engine.evaluation_planning import resolve_v4_seed_geometry
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    PROCESS_RULESET_IDS,
    RULESET_V4,
    RULESET_V6_RESEARCH_SCALE,
    resolve_ruleset_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_SOURCE_DIRS = (
    REPO_ROOT / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)


# ---------------------------------------------------------------------------
# Real-agent bootstrap (mirrors test_v4_stable_ruleset_equivalence.py)
# ---------------------------------------------------------------------------


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
    """Run one real match under ``ruleset_id``; return its replay_path.

    Starts are always omitted, resolved through the identical production
    ``placement.resolve_direct_match_starts`` seam ``bytefray run`` uses --
    never precomputed and reused, so this exercises the real resolution
    path for whichever Ruleset is under test.
    """

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
    """Parse one replay into a JSON-serializable snapshot with every
    identity-bearing field (including ``ruleset_id`` itself) nulled out --
    the exact fields two runs under *different* Ruleset identities are
    expected to disagree on, so the remainder is a pure gameplay
    comparison."""

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


# ---------------------------------------------------------------------------
# Synthetic minimal API v2 agent, for fast identity/validation-only tests
# that do not need real gameplay evidence.
# ---------------------------------------------------------------------------

API_V2_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.context = context
    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]
    def act(self, observation):
        if not isinstance(observation, ObservationV2):
            raise TypeError("expected ObservationV2")
        return AgentAction(ActionKindV2.MOVE, 1)

def create_agent():
    return Agent()
"""


def _write_api_v2_agent(root: Path, name: str) -> Path:
    import json as _json

    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(
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
    (directory / "agent.py").write_text(API_V2_SOURCE, encoding="utf-8")
    return directory


def _research_request(tmp_path: Path, **overrides) -> EvaluationRequest:
    defaults = {
        "candidate_id": "candidate",
        "opponent_ids": ("opponent",),
        "seeds": (1,),
        "output_dir": tmp_path / "eval-out",
        "ticks": 5,
        "data_root": tmp_path,
        "ruleset_id": BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    }
    defaults.update(overrides)
    return EvaluationRequest(**defaults)


# ---------------------------------------------------------------------------
# 1. Registry recognition / executable status / API version
# ---------------------------------------------------------------------------


def test_research_scale_is_registered_and_executable() -> None:
    policy = resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID)
    assert policy is RULESET_V6_RESEARCH_SCALE
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID in PROCESS_RULESET_IDS
    assert policy.supported_runtime_kinds == frozenset({"python"})
    assert policy.supported_python_api_versions == frozenset({2})
    assert policy.supports_agent(kind="python", api_version=2)
    assert not policy.supports_agent(kind="python", api_version=1)
    assert not policy.supports_agent(kind="vm", api_version=None)


def test_research_scale_live_match_executes_successfully(tmp_path: Path) -> None:
    _bootstrap_agent(tmp_path, "v4_claimer")
    _bootstrap_agent(tmp_path, "v4_local_defender")
    replay_path = _run_under_ruleset(
        tmp_path,
        ("v4_claimer", "v4_local_defender"),
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=512,
        seed=1,
        ticks=100,
        run_label="live",
    )
    raw_header = _raw_header(replay_path)
    assert raw_header.ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID


# ---------------------------------------------------------------------------
# 2. Scheduler equality with V4
# ---------------------------------------------------------------------------


def test_scheduler_call_order_is_identical_to_stable_v4() -> None:
    from dataclasses import dataclass

    @dataclass
    class _FakeState:
        name: str
        alive: bool = True

    states = [_FakeState("A"), _FakeState("B"), _FakeState("C")]
    v4_calls: list[str] = []
    research_calls: list[str] = []
    RULESET_V4.run_scheduler(states, 3, lambda s, slot: v4_calls.append(f"{s.name}{slot}"), tick=1)
    RULESET_V6_RESEARCH_SCALE.run_scheduler(
        states, 3, lambda s, slot: research_calls.append(f"{s.name}{slot}"), tick=1
    )
    assert research_calls == v4_calls


# ---------------------------------------------------------------------------
# 3. Seeded placement equality at A=512 (no legacy (0, 0) placement)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6, 7, 8])
def test_seeded_placement_at_a512_matches_stable_v4_byte_for_byte(seed: int) -> None:
    v4_starts = resolve_v4_seed_geometry(BYTEFRAY_RULESET_V4_ID, STANDARD_V4_ARENA_SIZE, seed)
    research_starts = resolve_v4_seed_geometry(
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, STANDARD_V4_ARENA_SIZE, seed
    )
    assert research_starts == v4_starts
    assert research_starts != (0, 0)


def test_seeded_placement_is_deterministic_and_arena_dependent() -> None:
    # Same seed + same arena -> same starts (determinism).
    a = resolve_v4_seed_geometry(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, 1024, 3)
    b = resolve_v4_seed_geometry(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, 1024, 3)
    assert a == b
    # Different arena size may (and, for this seed, does) produce different starts.
    c = resolve_v4_seed_geometry(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, 4096, 3)
    assert c != a
    # Minimum separation remains the fixed raw-scaling constant of 64 cells
    # at every tested arena size in this test.
    for arena_size, starts in ((1024, a), (4096, c)):
        seat_a, seat_b = starts
        forward = (seat_b - seat_a) % arena_size
        circular_distance = min(forward, arena_size - forward)
        assert circular_distance >= 64


@pytest.mark.parametrize("arena_size", [512, 1024, 4096, 16384, 65536])
def test_seeded_placement_is_valid_at_every_target_arena_size(arena_size: int) -> None:
    seat_a, seat_b = resolve_v4_seed_geometry(
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, arena_size, 1
    )
    assert 0 <= seat_a < arena_size
    assert 0 <= seat_b < arena_size
    assert (seat_a, seat_b) != (0, 0)


# ---------------------------------------------------------------------------
# 4. Methodology routing / identity / schema version selection
# ---------------------------------------------------------------------------


def test_methodology_predicates_distinguish_research_scale_from_stable_v4() -> None:
    assert is_ruleset_v4_methodology(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID) is False
    assert is_ruleset_v6_research_scale_methodology(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID) is True
    assert is_ruleset_v6_research_scale_methodology(BYTEFRAY_RULESET_V4_ID) is False
    # The broader "shares v4's seeded machinery" predicate is true for both.
    assert is_ruleset_v4_derived_methodology(BYTEFRAY_RULESET_V4_ID) is True
    assert is_ruleset_v4_derived_methodology(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID) is True


def test_request_properties_route_research_scale_correctly(tmp_path: Path) -> None:
    request = _research_request(tmp_path)
    assert request.is_v4_methodology is False
    assert request.is_v6_research_scale_methodology is True
    # Omitted arena_size resolves to the V4-equivalent default (512), never
    # the unrelated Config().arena_size default (4096).
    assert request.resolved_arena_size == STANDARD_V4_ARENA_SIZE == 512


def test_identity_and_schema_version_are_both_seven_never_legacy_v2() -> None:
    assert (
        resolved_identity_version(False, False, False, True)
        == IDENTITY_VERSION_V4
        == 7
    )
    assert (
        resolved_schema_version(False, False, False, True)
        == SCHEMA_VERSION_V4
        == 7
    )
    # Never the legacy v1 identity version (4) or v2 (5).
    assert resolved_identity_version(False, False, False, True) not in (4, 5)


def test_arena_alignment_mode_is_distinct_from_stable_v4_and_from_legacy_fixed() -> None:
    research_mode = resolved_arena_alignment_mode(False, False, False, True)
    v4_mode = resolved_arena_alignment_mode(False, False, True, False)
    assert research_mode == EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE
    assert v4_mode == EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED
    assert research_mode != v4_mode
    assert research_mode != "fixed"


def test_placement_reconstructs_exactly_from_seed_via_the_production_seam(
    tmp_path: Path,
) -> None:
    """No (0, 0) legacy placement regression: every persisted start is
    exactly reconstructible from resolve_v4_seed_geometry, never the
    historical fixed-placement (0, 0) sentinel."""

    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(tmp_path, seeds=(1, 2, 3, 4), arena_size=1024)
    result = EvaluationService().run(request)
    assert len(result.cells) > 0
    for cell in result.cells:
        seat_a, seat_b = resolve_v4_seed_geometry(
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, 1024, cell.seed
        )
        if cell.orientation == ORIENTATION_OPPONENT_FIRST:
            seat_a, seat_b = seat_b, seat_a
        assert (cell.subject_start, cell.opponent_start) == (seat_a, seat_b)
        assert (cell.subject_start, cell.opponent_start) != (0, 0)
        assert cell.placement_id != "fixed"


# ---------------------------------------------------------------------------
# 5. Arena-size validation: variable acceptance, stable-v4 lock preserved,
#    research-scale out-of-range rejection (never silently clamped).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arena_size", [512, 1024, 4096, 16384, 65536])
def test_research_scale_accepts_every_phase4b_arena_size(tmp_path: Path, arena_size: int) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(tmp_path, arena_size=arena_size)
    result = EvaluationService().run(request)
    assert all(cell.status == "completed" for cell in result.cells)
    for cell in result.cells:
        assert 0 <= cell.subject_start < arena_size
        assert 0 <= cell.opponent_start < arena_size


def test_stable_v4_still_rejects_non_512_arena_after_allow_list_change(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V4_ID, arena_size=1024
    )
    with pytest.raises(EvaluationConfigurationError, match="incompatible with the"):
        EvaluationService().run(request)


@pytest.mark.parametrize("arena_size", [1, 8, 63, RESEARCH_SCALE_MIN_ARENA_SIZE - 1])
def test_research_scale_rejects_arena_size_below_the_research_range(
    tmp_path: Path, arena_size: int
) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError):
        EvaluationService().run(request)


@pytest.mark.parametrize("arena_size", [RESEARCH_SCALE_MAX_ARENA_SIZE + 1, 131072, 1_000_000])
def test_research_scale_rejects_arena_size_above_the_research_range(
    tmp_path: Path, arena_size: int
) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(tmp_path, arena_size=arena_size)
    with pytest.raises(EvaluationConfigurationError, match="outside the"):
        EvaluationService().run(request)


def test_research_scale_never_silently_clamps_out_of_range_arena(tmp_path: Path) -> None:
    """A rejected out-of-range --arena-size must never quietly execute at
    the nearest supported bound -- it must fail before any cell runs."""

    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    request = _research_request(tmp_path, arena_size=100_000)
    with pytest.raises(EvaluationConfigurationError):
        EvaluationService().run(request)
    assert not (tmp_path / "eval-out" / "evaluation.json").exists()


# ---------------------------------------------------------------------------
# 6. Arena size is identity-bearing: A=512 and A=1024 produce different
#    evaluation/schedule/match identities.
# ---------------------------------------------------------------------------


def test_arena_size_is_identity_bearing_for_evaluation_and_schedule_ids(
    tmp_path: Path,
) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    at_512 = EvaluationService().run(
        _research_request(tmp_path, arena_size=512, output_dir=tmp_path / "a512")
    )
    at_1024 = EvaluationService().run(
        _research_request(tmp_path, arena_size=1024, output_dir=tmp_path / "a1024")
    )
    assert at_512.evaluation_id != at_1024.evaluation_id
    assert len(at_512.cells) == len(at_1024.cells) > 0
    for cell_512, cell_1024 in zip(at_512.cells, at_1024.cells, strict=True):
        assert cell_512.schedule_id != cell_1024.schedule_id
        assert cell_512.match_id != cell_1024.match_id
        if cell_512.condition_fingerprint is not None:
            assert cell_512.condition_fingerprint != cell_1024.condition_fingerprint


def test_ruleset_id_is_identity_bearing_at_the_same_arena_size(tmp_path: Path) -> None:
    """A=512 under stable v4 vs. under the research Ruleset must also
    produce different evaluation ids -- Ruleset identity, not merely arena
    size, is part of MatchIdentity."""

    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    v4_result = EvaluationService().run(
        _research_request(
            tmp_path,
            ruleset_id=BYTEFRAY_RULESET_V4_ID,
            arena_size=None,
            output_dir=tmp_path / "v4",
        )
    )
    research_result = EvaluationService().run(
        _research_request(tmp_path, arena_size=None, output_dir=tmp_path / "research")
    )
    assert v4_result.evaluation_id != research_result.evaluation_id
    for v4_cell, research_cell in zip(v4_result.cells, research_result.cells, strict=True):
        assert v4_cell.schedule_id != research_cell.schedule_id
        assert v4_cell.match_id != research_cell.match_id


def test_identity_is_stable_for_the_same_arena_seed_and_config(tmp_path: Path) -> None:
    _write_api_v2_agent(tmp_path, "candidate")
    _write_api_v2_agent(tmp_path, "opponent")
    first = EvaluationService().run(
        _research_request(tmp_path, arena_size=4096, output_dir=tmp_path / "first")
    )
    second = EvaluationService().run(
        _research_request(tmp_path, arena_size=4096, output_dir=tmp_path / "second")
    )
    assert first.evaluation_id == second.evaluation_id
    for cell_a, cell_b in zip(first.cells, second.cells, strict=True):
        assert cell_a.schedule_id == cell_b.schedule_id
        assert cell_a.subject_start == cell_b.subject_start
        assert cell_a.opponent_start == cell_b.opponent_start


# ---------------------------------------------------------------------------
# 7. A=512 behavioral equivalence gate: real agents, live execution, full
#    replay/result comparison (excluding expected Ruleset-ID/header
#    identity differences).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 3, 7])
@pytest.mark.parametrize(
    "entrant_names",
    [
        ("v4_claimer", "v5_core_defender"),
        ("v5_scout_striker", "v4_local_defender"),
    ],
)
def test_research_scale_is_behaviorally_identical_to_stable_v4_at_a512(
    tmp_path: Path, entrant_names: tuple[str, str], seed: int
) -> None:
    for name in entrant_names:
        _bootstrap_agent(tmp_path, name)

    v4_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=512,
        seed=seed,
        ticks=300,
        run_label=f"v4-{'-'.join(entrant_names)}-{seed}",
    )
    research_replay = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=512,
        seed=seed,
        ticks=300,
        run_label=f"research-{'-'.join(entrant_names)}-{seed}",
    )

    v4_snapshot = _nulled_identity_snapshot(v4_replay)
    research_snapshot = _nulled_identity_snapshot(research_replay)

    # Gameplay -- placement geometry, tick-by-tick events/memory writes,
    # scoring, territory, kills/deaths, and the terminal result -- must be
    # byte-for-byte identical once Ruleset-ID/header identity fields are
    # excluded.
    assert research_snapshot == v4_snapshot

    # Ruleset-ID-bearing identity fields are expected, and required, to
    # differ: each replay must honestly attribute its own Ruleset.
    assert _raw_header(v4_replay).ruleset_id == BYTEFRAY_RULESET_V4_ID
    assert _raw_header(research_replay).ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID


# ---------------------------------------------------------------------------
# 8. CLI surface: --ruleset accepts the new identity explicitly, never
#    automatically; retired identities remain rejected.
# ---------------------------------------------------------------------------


def test_evaluate_cli_accepts_research_scale_explicitly(
    tmp_path: Path, monkeypatch, capsys
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
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
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


def test_evaluate_cli_rejects_out_of_range_arena_for_research_scale(
    tmp_path: Path, monkeypatch, capsys
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
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
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
