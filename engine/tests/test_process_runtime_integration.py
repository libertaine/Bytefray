"""The shared Agent API v2 process runtime, end to end.

The runtime-property tests below were written for stable ``bytefray-rules-4``
and now run under the research control ``bytefray-rules-6-research-scale``,
whose policy is a field-for-field copy of retired Classic: quota, chunked
rotating scheduling, disruption, capture/kill scoring and passive
visibility are the same shared runtime Active Sensing executes on.
``test_direct_cli_bootstraps_starters_and_product_paths_use_production_runtime``
exercises the Active Sensing product paths themselves.
"""

from __future__ import annotations

import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest
from battle_engine.agent_api import ProcessDeclaration
from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService
from battle_engine.agent_test import DevelopmentTestOutcome
from battle_engine.agent_test import test_agent as run_agent_test
from battle_engine.agent_validation import AgentValidationFailedError, validate_agent
from battle_engine.agents import resolve_agent
from battle_engine.cli import main as run_cli
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchResult,
    NativeMatchService,
)
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.python_runtime import PythonEntrantInitializationError
from battle_engine.replay import (
    MatchResult,
    ReplayHeader,
    TickSnapshot,
    iter_replay,
    write_replay,
)
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_ALPHA1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)


def _write_agent(root: Path, name: str, source: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": name,
                "display": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(source, encoding="utf-8")


def _request(
    root: Path,
    names: tuple[str, str],
    replay_path: Path,
    *,
    ticks: int,
    starts: tuple[int, int] = (0, 32),
    timeout: float | None = None,
    seed: int = 17,
    ruleset_id: str = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
) -> MatchRequest:
    specs = tuple(resolve_agent(root, name) for name in names)
    entrants = tuple(
        MatchEntrant.python(chr(ord("A") + slot), name, starts[slot], spec)
        for slot, (name, spec) in enumerate(zip(names, specs, strict=True))
    )
    return MatchRequest(
        config=Config(arena_size=64, instr_per_tick=8, seed=seed),
        entrants=entrants,
        max_ticks=ticks,
        replay_path=replay_path,
        verbose=False,
        agent_call_timeout=timeout,
        ruleset_id=ruleset_id,
    )


def _run(request: MatchRequest) -> tuple[NativeMatchResult, list[object]]:
    result = NativeMatchService().run(request)
    return result, list(iter_replay(request.replay_path))


PASSIVE_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.context = context
    def declare_processes(self):
        return [ProcessDeclaration("passive", 31, 1.0)]
    def act(self, observation):
        if not isinstance(observation, ObservationV2):
            raise TypeError("expected ObservationV2")
        return AgentAction(ActionKindV2.MOVE, 0)

def create_agent():
    return Agent()
"""


def _equal_share_declarations(count: int) -> list[ProcessDeclaration]:
    if count == 1:
        shares = [1.0]
    else:
        share = 1.0 / count
        shares = [share] * (count - 1)
        shares.append(1.0 - sum(shares))
    return [
        ProcessDeclaration(f"p{index}", 31, share)
        for index, share in enumerate(shares)
    ]


def _equal_share_source(count: int) -> str:
    return f"""
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

COUNT = {count}

class Agent:
    def reset(self, context): pass
    def declare_processes(self):
        if COUNT == 1:
            shares = [1.0]
        else:
            share = 1.0 / COUNT
            shares = [share] * (COUNT - 1)
            shares.append(1.0 - sum(shares))
        return [
            ProcessDeclaration(f"p{{index}}", 31, share)
            for index, share in enumerate(shares)
        ]
    def act(self, observation): return AgentAction(ActionKindV2.MOVE, 0)
def create_agent(): return Agent()
"""


@pytest.mark.parametrize("count", range(1, 9))
def test_accepted_process_shares_form_one_exact_runtime_partition(count: int) -> None:
    """Publicly valid shares cannot fail a stricter runtime total check."""

    declarations = _equal_share_declarations(count)
    validated = ProcessMatchController._validate_declarations(
        declarations,
        agent_id="A",
        slot=0,
        arena_size=64,
    )
    runtime_shares = ProcessMatchController._runtime_quota_shares(validated)

    assert sum(runtime_shares, start=Fraction()) == Fraction(1)
    if count in {1, 2, 4, 8}:
        assert runtime_shares == tuple(
            Fraction(str(declaration.share)) for declaration in declarations
        )


@pytest.mark.parametrize("count", (3, 5, 6, 7))
def test_non_dyadic_process_counts_validate_construct_and_run(
    tmp_path: Path, count: int
) -> None:
    """The documented derive-the-remainder pattern reaches a real match."""

    agent_id = f"equal_{count}"
    _write_agent(tmp_path, agent_id, _equal_share_source(count))
    _write_agent(tmp_path, "passive", PASSIVE_SOURCE)

    result = NativeMatchService().run(
        _request(
            tmp_path,
            (agent_id, "passive"),
            tmp_path / f"equal-{count}.jsonl",
            ticks=1,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        )
    )

    assert result.ticks_run == 1
    assert all(agent.diagnostic is None for agent in result.agents)


def test_invalid_share_total_is_presentable_in_validation_and_cli_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    invalid_source = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration
class Agent:
    def reset(self, context): pass
    def declare_processes(self):
        return [ProcessDeclaration("a", 4, 0.6), ProcessDeclaration("b", 8, 0.3)]
    def act(self, observation): return AgentAction(ActionKindV2.MOVE, 0)
def create_agent(): return Agent()
"""
    _write_agent(tmp_path, "invalid_total", invalid_source)
    _write_agent(tmp_path, "passive", PASSIVE_SOURCE)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("invalid_total", data_root=tmp_path)

    diagnostic = caught.value.diagnostic
    assert diagnostic.code == "agent_process_declaration_invalid"
    assert diagnostic.stage == "declaration"
    assert diagnostic.message == "Python agent A process shares total 0.9; expected 1."

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    exit_code = run_cli(
        [
            "--a-type",
            "invalid_total",
            "--b-type",
            "passive",
            "--arena",
            "512",
            "--quota",
            "8",
            "--ticks",
            "1",
            "--ruleset",
            BYTEFRAY_RULESET_V6_ALPHA1_ID,
            "--replay",
            str(tmp_path / "invalid-run" / "replay.jsonl"),
            "--quiet",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert diagnostic.message in captured.err
    assert "Traceback" not in captured.err
    assert "ValueError" not in captured.err


@pytest.mark.parametrize(
    "declaration",
    [
        "[ProcessDeclaration('same', 4, 0.5), ProcessDeclaration('same', 8, 0.5)]",
        "[ProcessDeclaration('a', 4, 0.6), ProcessDeclaration('b', 8, 0.3)]",
    ],
)
def test_v4_rejects_invalid_declarations_before_tick_zero(
    tmp_path: Path, declaration: str
) -> None:
    _write_agent(
        tmp_path,
        "invalid",
        f"""
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration
class Agent:
    def reset(self, context): pass
    def declare_processes(self): return {declaration}
    def act(self, observation): return AgentAction(ActionKindV2.MOVE, 0)
def create_agent(): return Agent()
""",
    )
    _write_agent(tmp_path, "passive", PASSIVE_SOURCE)
    replay = tmp_path / "invalid.jsonl"

    with pytest.raises(PythonEntrantInitializationError) as caught:
        NativeMatchService().run(
            _request(tmp_path, ("invalid", "passive"), replay, ticks=1)
        )

    assert caught.value.diagnostic.code == "agent_process_declaration_invalid"
    assert caught.value.diagnostic.stage == "declaration"
    assert caught.value.diagnostic.agent_id == "A"
    assert not replay.exists()
    assert not replay.with_name("result.json").exists()


def test_v4_production_schema4_roundtrip_determinism_and_supervision(
    tmp_path: Path,
) -> None:
    # The Classic retirement no longer installs these starters into agents/;
    # run their byte-for-byte retained packages from an isolated data root.
    retained = (
        Path(__file__).resolve().parents[2]
        / "engine" / "src" / "battle_engine" / "data" / "starter_agents"
    )
    root = tmp_path / "data"
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    names = ("v4_defender_scout", "v4_scout")
    for name in names:
        shutil.copytree(retained / name, root / "agents" / name)

    first_result, first_records = _run(
        _request(root, names, first_path, ticks=3, seed=23)
    )
    second_result, second_records = _run(
        _request(root, names, second_path, ticks=3, seed=23)
    )

    assert first_result.winner == second_result.winner
    assert first_result.ticks_run == second_result.ticks_run
    assert first_result.score == second_result.score
    assert first_result.agents == second_result.agents
    assert first_records == second_records
    assert first_path.read_bytes() == second_path.read_bytes()
    assert isinstance(first_records[0], ReplayHeader)
    assert isinstance(first_records[-1], MatchResult)
    assert all(record.schema_version == 4 for record in first_records)
    ticks = [record for record in first_records if isinstance(record, TickSnapshot)]
    initial = {(p.entrant_id, p.process_id): p for p in ticks[0].processes}
    assert initial[("A", "defender")].anchor == 0
    assert initial[("A", "scout")].anchor == 0
    assert initial[("B", "scout")].anchor == 32
    assert len(first_records[-1].processes) == 3

    roundtrip = tmp_path / "roundtrip.jsonl"
    write_replay(roundtrip, first_records)
    assert list(iter_replay(roundtrip)) == first_records

    supervised_path = tmp_path / "supervised.jsonl"
    supervised_result, supervised_records = _run(
        _request(root, names, supervised_path, ticks=1, timeout=5.0, seed=23)
    )
    assert all(agent.diagnostic is None for agent in supervised_result.agents)
    supervised_ticks = [
        record for record in supervised_records if isinstance(record, TickSnapshot)
    ]
    assert len(supervised_ticks[0].processes) == 3
    assert all(agent.metadata["api_version"] == 2 for agent in supervised_result.agents)


COUNTER_WRITER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.calls = 0
    def declare_processes(self):
        return [ProcessDeclaration("writer", 31, 1.0)]
    def act(self, observation):
        if not isinstance(observation, ObservationV2):
            raise TypeError("expected ObservationV2")
        target = 16 + self.calls
        self.calls += 1
        return AgentAction(ActionKindV2.WRITE, target, 0x41)

def create_agent():
    return Agent()
"""


def test_v4_production_enforces_q8_k2_and_rotating_start(tmp_path: Path) -> None:
    _write_agent(tmp_path, "alpha", COUNTER_WRITER_SOURCE)
    _write_agent(tmp_path, "bravo", COUNTER_WRITER_SOURCE)
    result, records = _run(
        _request(tmp_path, ("alpha", "bravo"), tmp_path / "k2.jsonl", ticks=2)
    )
    ticks = [record for record in records if isinstance(record, TickSnapshot)]

    assert [[agent.cpu_used for agent in tick.agents] for tick in ticks[1:]] == [
        [8, 8],
        [8, 8],
    ]
    assert [agent.cpu_total for agent in result.agents] == [16, 16]
    assert [
        (diff.address, diff.length, diff.owner) for diff in ticks[1].memory_diffs
    ] == [
        (16, 2, "A"),
        (16, 2, "B"),
        (18, 2, "A"),
        (18, 2, "B"),
        (20, 2, "A"),
        (20, 2, "B"),
        (22, 2, "A"),
        (22, 2, "B"),
    ]
    assert [diff.owner for diff in ticks[2].memory_diffs] == [
        "B",
        "A",
        "B",
        "A",
        "B",
        "A",
        "B",
        "A",
    ]


CORE_ATTACKER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context): self.calls = 0
    def declare_processes(self): return [ProcessDeclaration("attacker", 63, 1.0)]
    def act(self, observation):
        target = self.calls
        self.calls += 1
        return AgentAction(ActionKindV2.WRITE, target, 0xA5)

def create_agent(): return Agent()
"""


def test_v4_production_preserves_core_capture_kill_scoring(tmp_path: Path) -> None:
    _write_agent(tmp_path, "victim", PASSIVE_SOURCE)
    _write_agent(tmp_path, "core_attacker", CORE_ATTACKER_SOURCE)
    result, records = _run(
        _request(
            tmp_path,
            ("victim", "core_attacker"),
            tmp_path / "capture.jsonl",
            ticks=2,
        )
    )
    final_tick = next(
        record
        for record in records
        if isinstance(record, TickSnapshot) and record.tick == 1
    )
    by_id = {agent.agent_id: agent for agent in result.agents}

    assert result.winner == "B"
    assert result.ticks_run == 1
    assert by_id["A"].alive is False
    assert by_id["A"].deaths == 1
    assert by_id["B"].kills == 1
    assert any(
        getattr(event, "victim", None) == "A"
        and getattr(event, "killer", None) == "B"
        for event in final_tick.events
    )


VICTIM_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context): pass
    def declare_processes(self):
        return [
            ProcessDeclaration("guard", 4, 0.125),
            ProcessDeclaration("scout", 4, 0.875),
        ]
    def act(self, observation):
        if not isinstance(observation, ObservationV2):
            raise TypeError("expected ObservationV2")
        if hasattr(observation, "previous_disruption_hit"):
            raise RuntimeError("disruption-hit feedback must remain private")
        if observation.self_process_id == "guard":
            if observation.current_tick == 2:
                assert observation.last_callback_tick == 1
                assert observation.previous_action_tick == 1
                assert observation.previous_action_applied is True
            return AgentAction(ActionKindV2.MOVE, 0)
        return AgentAction(ActionKindV2.MOVE, 1)

def create_agent(): return Agent()
"""


ONE_HIT_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context): self.calls = 0
    def declare_processes(self): return [ProcessDeclaration("attacker", 63, 1.0)]
    def act(self, observation):
        self.calls += 1
        if self.calls == 1:
            return AgentAction(ActionKindV2.WRITE, 0, 0x99)
        return AgentAction(ActionKindV2.MOVE, 0)

def create_agent(): return Agent()
"""


def test_v4_production_d1_disruption_fair_redistribution_and_minimal_feedback(
    tmp_path: Path,
) -> None:
    _write_agent(tmp_path, "victim", VICTIM_SOURCE)
    _write_agent(tmp_path, "attacker", ONE_HIT_SOURCE)
    result, records = _run(
        _request(tmp_path, ("victim", "attacker"), tmp_path / "d1.jsonl", ticks=2)
    )
    ticks = [record for record in records if isinstance(record, TickSnapshot)]
    tick1 = {(p.entrant_id, p.process_id): p for p in ticks[1].processes}
    tick2 = {(p.entrant_id, p.process_id): p for p in ticks[2].processes}

    assert all(agent.diagnostic is None for agent in result.agents)
    assert next(agent.cpu_used for agent in ticks[1].agents if agent.agent_id == "A") == 8
    assert tick1[("A", "guard")].anchor == 0
    assert tick1[("A", "guard")].disrupted is True
    assert tick1[("A", "scout")].anchor == 7
    assert tick1[("A", "scout")].disrupted is False
    assert tick2[("A", "guard")].disrupted is False
    assert tick2[("A", "scout")].anchor == 14


VISIBILITY_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2, ProcessDeclaration

class Agent:
    def reset(self, context): pass
    def declare_processes(self): return [ProcessDeclaration("observer", 8, 1.0)]
    def act(self, observation):
        if not isinstance(observation, ObservationV2):
            raise TypeError("expected ObservationV2")
        if observation.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.READ, observation.visible_enemy_anchor_addresses[0])
        if (
            observation.previous_read_value is not None
            and observation.previous_read_owner == "B"
            and observation.previous_action_tick == observation.current_tick
        ):
            return AgentAction(ActionKindV2.MOVE, 1)
        return AgentAction(ActionKindV2.MOVE, 0)

def create_agent(): return Agent()
"""


FAST_MOVER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context): pass
    def declare_processes(self): return [ProcessDeclaration("mover", 8, 1.0)]
    def act(self, observation): return AgentAction(ActionKindV2.MOVE, 8)

def create_agent(): return Agent()
"""


def test_v4_production_visibility_is_current_and_read_feedback_can_be_stale(
    tmp_path: Path,
) -> None:
    _write_agent(tmp_path, "observer", VISIBILITY_SOURCE)
    _write_agent(tmp_path, "mover", FAST_MOVER_SOURCE)
    result, records = _run(
        _request(
            tmp_path,
            ("observer", "mover"),
            tmp_path / "visibility.jsonl",
            ticks=1,
            starts=(0, 8),
        )
    )
    tick = next(
        record
        for record in records
        if isinstance(record, TickSnapshot) and record.tick == 1
    )
    processes = {(p.entrant_id, p.process_id): p for p in tick.processes}

    assert all(agent.diagnostic is None for agent in result.agents)
    assert processes[("A", "observer")].anchor == 1
    assert processes[("B", "mover")].anchor == 8


def test_direct_cli_bootstraps_starters_and_product_paths_use_production_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``bytefray run``, ``agents test`` and evaluation all run Active Sensing."""

    resource_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    assert not (tmp_path / "agents").exists()

    cli_replay = tmp_path / "cli" / "replay.jsonl"
    assert (
        run_cli(
            [
                "--a-type",
                "v6_window_scout",
                "--b-type",
                "v6_watchful_keeper",
                "--arena",
                "512",
                "--quota",
                "8",
                "--ticks",
                "1",
                "--replay",
                str(cli_replay),
                "--quiet",
            ]
        )
        == 0
    )
    records = list(iter_replay(cli_replay))
    assert all(record.schema_version == 4 for record in records)
    assert isinstance(records[0], ReplayHeader)
    assert records[0].ruleset_id == BYTEFRAY_RULESET_V6_ALPHA1_ID
    for starter in ("v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer"):
        assert (tmp_path / "agents" / starter / "agent.yaml").is_file()
    assert not (tmp_path / "agents" / "v4_claimer").exists()

    test_outcome = run_agent_test(
        "v6_window_scout",
        data_root=tmp_path,
        resource_root=resource_root,
        run_dir=tmp_path / "agent-test",
        ticks=1,
        timeout=5.0,
        trace=False,
        arena_size=512,
    )
    assert isinstance(test_outcome, DevelopmentTestOutcome)
    assert test_outcome.ruleset_id == BYTEFRAY_RULESET_V6_ALPHA1_ID
    assert all(
        agent.metadata["api_version"] == 2
        for agent in test_outcome.match_result.agents
    )

    evaluation = EvaluationService().run(
        EvaluationRequest(
            candidate_id="v6_window_scout",
            opponent_ids=("v6_watchful_keeper",),
            seeds=(1,),
            output_dir=tmp_path / "evaluation",
            ticks=1,
            data_root=tmp_path,
            both_orientations=False,
            instr_per_tick=8,
        )
    )
    # The seeded-placement methodology produces one cell per orientation;
    # with both_orientations=False and one opponent/seed that is exactly one.
    assert len(evaluation.cells) == 1
    assert all(cell.status == "completed" for cell in evaluation.cells)
    assert all(
        cell.rules_compatibility_id == BYTEFRAY_RULESET_V6_ALPHA1_ID
        for cell in evaluation.cells
    )
