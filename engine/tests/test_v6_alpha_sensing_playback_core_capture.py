"""Sensing-playback reconstruction of the end-of-tick core-capture rule.

``reconstruct_sensing_playback`` previously removed entrants only on
forfeit, so every alpha1 match ending in ``core_captured`` failed its
tick-end alive-entrant agreement check, while a replay that falsely kept a
captured entrant alive was accepted. These native matches pin the corrected
behavior against ``python_runtime.apply_core_capture``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from battle_engine import ruleset_policy, sensing_playback
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.sensing_playback import (
    ArtifactIntegrityError,
    ExchangeConsistencyError,
    ExchangePhase,
    ExchangeReconstructionError,
    SensingPlayback,
    reconstruct_sensing_playback,
)
from battle_engine.spectator_derivation import verify_pair
from battle_engine.spectator_events import load_schema4_replay

B_CORE = tuple(range(91, 99))


def _writes(cells: tuple[int, ...] | list[int], value: int = 0xDD) -> list[tuple[Any, ...]]:
    return [("write", cell, value) for cell in cells]


def _match(
    tmp_path: Path,
    label: str,
    entrants: list[tuple[str, int, list[tuple[Any, ...]]]],
    max_ticks: int,
) -> Path:
    """Run a native alpha1 match of scripted entrants ``(id, start, script)``.

    Each script item is ``(kind, operand[, value])``; once the script is
    exhausted the entrant READs its own core, so it never repairs.
    """
    match_dir = tmp_path / label
    match_dir.mkdir(parents=True, exist_ok=True)
    match_entrants = []
    for agent_id, start, script in entrants:
        agent_name = f"{label}_{agent_id.lower()}"
        agent_dir = tmp_path / "agents" / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        source = (
            "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
            f"SCRIPT = {script!r}\n"
            "class Scripted(AgentV2):\n"
            "    def __init__(self):\n"
            "        self.calls = 0\n"
            "    def declare_processes(self):\n"
            "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
            "    def act(self, obs):\n"
            "        item = SCRIPT[self.calls] if self.calls < len(SCRIPT) else ('read', obs.own_core_base)\n"
            "        self.calls += 1\n"
            "        value = item[2] if len(item) > 2 else None\n"
            "        return AgentAction(ActionKindV2(item[0]), operand=item[1], value=value)\n"
            "def create_agent():\n"
            "    return Scripted()\n"
        )
        (agent_dir / "agent.py").write_text(source, encoding="utf-8")
        manifest: dict[str, Any] = {
            "name": agent_name,
            "kind": "python",
            "api_version": 2,
            "entrypoint": "agent.py:create_agent",
        }
        if any(item[0] == "sense" for item in script):
            manifest["capabilities"] = {"version": 1, "required": ["sense"]}
        (agent_dir / "agent.yaml").write_text(json.dumps(manifest), encoding="utf-8")
        spec = agent_spec_from_dir(agent_dir)
        assert spec is not None
        match_entrants.append(MatchEntrant.python(agent_id, agent_name, start, spec))

    NativeMatchService().run(
        MatchRequest(
            config=Config(arena_size=512, instr_per_tick=8, seed=0),
            ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
            entrants=tuple(match_entrants),
            max_ticks=max_ticks,
            replay_path=match_dir / "replay.jsonl",
            trace_path=match_dir / "trace.jsonl",
        )
    )
    return match_dir


def _result(match_dir: Path) -> dict[str, Any]:
    return json.loads((match_dir / "result.json").read_text(encoding="utf-8"))


def _reconstruct(match_dir: Path) -> SensingPlayback:
    return reconstruct_sensing_playback(
        match_dir / "replay.jsonl",
        match_dir / "trace.jsonl",
        result_path=match_dir / "result.json",
    )


def _tick_end_alive(playback: SensingPlayback) -> dict[int, frozenset[str]]:
    return {
        s.tick: s.alive_entrants
        for s in playback.sub_tick_states
        if s.phase == ExchangePhase.TICK_END
    }


def _replay_records(match_dir: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (match_dir / "replay.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _replay_final_owners(records: list[dict[str, Any]], arena_size: int) -> tuple[str | None, ...]:
    """Ownership after applying every replay memory diff, independent of the playback module."""
    owners: list[str | None] = [None] * arena_size
    for record in records:
        if record.get("record_type") != "tick":
            continue
        for diff in record["memory_diffs"]:
            for offset in range(diff["length"]):
                owners[(diff["address"] + offset) % arena_size] = diff["owner"]
    return tuple(owners)


def test_core_capture_ending_reconstructs_and_matches_replay(tmp_path: Path) -> None:
    match_dir = _match(tmp_path, "capture", [("A", 0, _writes(B_CORE)), ("B", 91, [])], 20)
    result = _result(match_dir)
    assert result["winner"] == "A"
    assert result["termination_reason"] == "last_agent_standing"
    terminations = {e["agent_id"]: e["termination_reason"] for e in result["entrants"]}
    assert terminations["B"] == "core_captured"

    playback = _reconstruct(match_dir)

    records = _replay_records(match_dir)
    final_snapshot = [r for r in records if r.get("record_type") == "tick"][-1]
    final = playback.sub_tick_states[-1]
    assert final.phase == ExchangePhase.TICK_END
    assert final.tick == final_snapshot["tick"] == result["ticks"]
    assert final.alive_entrants == frozenset(
        a["id"] for a in final_snapshot["agents"] if a["alive"]
    ) == frozenset({"A"})
    assert final.owners == _replay_final_owners(records, playback.arena_size)
    assert all(final.owners[address] == "A" for address in B_CORE)
    assert final.anchors == {
        (p["entrant_id"], p["process_id"]): p["anchor"] for p in final_snapshot["processes"]
    }

    # B stays alive at every earlier tick end and in every sub-tick state of
    # the capture tick itself: elimination happens only at TICK_END.
    for state in playback.sub_tick_states[:-1]:
        assert "B" in state.alive_entrants


def test_partial_core_damage_does_not_eliminate(tmp_path: Path) -> None:
    match_dir = _match(tmp_path, "partial", [("A", 0, _writes(B_CORE[:-1])), ("B", 91, [])], 3)
    assert _result(match_dir)["termination_reason"] == "tick_limit"

    playback = _reconstruct(match_dir)
    alive = _tick_end_alive(playback)
    assert list(alive) == [0, 1, 2, 3]
    assert all(entrants == frozenset({"A", "B"}) for entrants in alive.values())
    assert playback.sub_tick_states[-1].owners[B_CORE[-1]] == "B"


def test_core_wrapping_the_arena_end_is_captured(tmp_path: Path) -> None:
    wrapped_core = (508, 509, 510, 511, 0, 1, 2, 3)
    match_dir = _match(tmp_path, "wrap", [("A", 400, _writes(wrapped_core)), ("B", 508, [])], 5)
    assert _result(match_dir)["termination_reason"] == "last_agent_standing"
    assert _tick_end_alive(_reconstruct(match_dir))[1] == frozenset({"A"})

    partial_dir = _match(
        tmp_path, "wrap_partial", [("A", 400, _writes(wrapped_core[:-1])), ("B", 508, [])], 2
    )
    assert _result(partial_dir)["termination_reason"] == "tick_limit"
    assert _tick_end_alive(_reconstruct(partial_dir))[2] == frozenset({"A", "B"})


def test_three_entrant_capture_continues_and_captured_anchor_is_not_sensed(
    tmp_path: Path,
) -> None:
    """B is captured at tick 1; A and C play on, and A's later scan of B's anchor is empty."""
    match_dir = _match(
        tmp_path,
        "three",
        [("A", 0, [*_writes(B_CORE), ("sense", 91)]), ("B", 91, []), ("C", 300, [])],
        3,
    )
    result = _result(match_dir)
    assert result["termination_reason"] == "tick_limit"
    terminations = {e["agent_id"]: e["termination_reason"] for e in result["entrants"]}
    assert terminations["B"] == "core_captured"

    playback = _reconstruct(match_dir)
    assert _tick_end_alive(playback) == {
        0: frozenset({"A", "B", "C"}),
        1: frozenset({"A", "C"}),
        2: frozenset({"A", "C"}),
        3: frozenset({"A", "C"}),
    }
    scans = [f for f in playback.facts if f.action_kind == "sense"]
    assert len(scans) == 1 and scans[0].tick == 2
    assert scans[0].sensed_anchors == ()


def test_simultaneous_mutual_capture_eliminates_both(tmp_path: Path) -> None:
    """Both step off their cores first, so neither WRITE lands on (and disrupts) a live anchor."""
    match_dir = _match(
        tmp_path,
        "mutual",
        [
            ("A", 0, [("move", 64), *_writes(B_CORE[1:]), *_writes([91])]),
            ("B", 91, [("move", -64), *_writes(range(1, 8)), *_writes([0])]),
        ],
        5,
    )
    result = _result(match_dir)
    assert result["termination_reason"] == "all_agents_dead"
    alive = _tick_end_alive(_reconstruct(match_dir))
    assert alive[1] == frozenset({"A", "B"})
    assert alive[result["ticks"]] == frozenset()


def test_replay_falsely_keeping_a_captured_entrant_alive_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the alive flag is forged; the pair binding is pinned to the genuine pair."""
    match_dir = _match(tmp_path, "forged", [("A", 0, _writes(B_CORE)), ("B", 91, [])], 20)
    replay, trace = match_dir / "replay.jsonl", match_dir / "trace.jsonl"
    binding = verify_pair(replay, trace)
    monkeypatch.setattr(sensing_playback, "verify_pair", lambda *_args, **_kwargs: binding)

    lines = replay.read_text(encoding="utf-8").splitlines()
    genuine, forged = match_dir / "genuine.jsonl", match_dir / "forged.jsonl"
    genuine.write_text("\n".join(lines) + "\n", encoding="utf-8")
    edited = []
    for line in lines:
        record = json.loads(line) if line.strip() else None
        if record and record.get("record_type") == "tick" and record["tick"] == 1:
            for agent in record["agents"]:
                if agent["id"] == "B":
                    agent["alive"] = True
                    agent["termination_reason"] = None
            line = json.dumps(record, separators=(",", ":"))
        edited.append(line)
    forged.write_text("\n".join(edited) + "\n", encoding="utf-8")

    # Control: the pinned binding alone does not cause rejection.
    assert _tick_end_alive(reconstruct_sensing_playback(genuine, trace))[1] == frozenset({"A"})
    with pytest.raises(ExchangeConsistencyError, match="alive entrants"):
        reconstruct_sensing_playback(forged, trace)


@pytest.fixture
def alpha1_two_tick_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give alpha1 a two-tick capture hold for both the runtime and the reconstruction.

    Every active-sensing Ruleset currently holds for one tick, so this is the
    only way to exercise the reconstruction's consecutive-evaluation streak
    against the authoritative runtime.
    """
    policy = ruleset_policy._RULESET_POLICIES[BYTEFRAY_RULESET_V6_ALPHA1_ID]
    monkeypatch.setitem(
        ruleset_policy._RULESET_POLICIES,
        BYTEFRAY_RULESET_V6_ALPHA1_ID,
        dataclasses.replace(policy, capture_hold_ticks=2),
    )


@pytest.mark.usefixtures("alpha1_two_tick_hold")
def test_two_tick_hold_completes_on_the_second_zero_evaluation(tmp_path: Path) -> None:
    match_dir = _match(tmp_path, "hold", [("A", 0, _writes(B_CORE)), ("B", 91, [])], 6)
    result = _result(match_dir)
    assert result["termination_reason"] == "last_agent_standing"
    assert result["ticks"] == 2
    alive = _tick_end_alive(_reconstruct(match_dir))
    assert alive[1] == frozenset({"A", "B"})
    assert alive[2] == frozenset({"A"})


@pytest.mark.usefixtures("alpha1_two_tick_hold")
def test_two_tick_hold_streak_resets_when_the_defender_regains_a_cell(tmp_path: Path) -> None:
    """Zero at tick 1, B retakes cell 92 in tick 2, A re-zeroes it in tick 3: captured at tick 4."""
    a_script = [
        *_writes(B_CORE[1:]),
        *_writes([91]),
        *[("read", 0)] * 8,
        *_writes([92]),
    ]
    b_script = [("move", -64), *[("read", 91)] * 7, ("write", 92, 0xCE)]
    match_dir = _match(tmp_path, "hold_reset", [("A", 0, a_script), ("B", 91, b_script)], 8)
    result = _result(match_dir)
    assert result["termination_reason"] == "last_agent_standing"
    assert result["ticks"] == 4
    alive = _tick_end_alive(_reconstruct(match_dir))
    assert all(alive[tick] == frozenset({"A", "B"}) for tick in (1, 2, 3))
    assert alive[4] == frozenset({"A"})


def test_reconstruction_uses_the_ruleset_capture_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reconstruction-only two-tick hold disagrees with the recorded single-tick capture."""
    match_dir = _match(tmp_path, "hold_mismatch", [("A", 0, _writes(B_CORE)), ("B", 91, [])], 20)
    resolve = sensing_playback.resolve_ruleset_policy

    def held(ruleset_id: str) -> ruleset_policy.RulesetPolicy:
        return dataclasses.replace(resolve(ruleset_id), capture_hold_ticks=2)

    monkeypatch.setattr(sensing_playback, "resolve_ruleset_policy", held)
    with pytest.raises(ExchangeConsistencyError, match="alive entrants"):
        reconstruct_sensing_playback(match_dir / "replay.jsonl", match_dir / "trace.jsonl")


@pytest.mark.parametrize(
    "region",
    [
        pytest.param("missing", id="omitted"),
        pytest.param(None, id="null"),
        pytest.param([91], id="invalid-shape"),
        pytest.param(["not-an-address", 91], id="invalid-address"),
    ],
)
def test_missing_or_malformed_core_region_is_rejected(tmp_path: Path, region: Any) -> None:
    """Keep real pair/result verification while isolating core-region evidence errors."""
    match_dir = _match(tmp_path, "region", [("A", 0, []), ("B", 91, [])], 1)
    assert _tick_end_alive(_reconstruct(match_dir))[1] == frozenset({"A", "B"})
    replay, trace = match_dir / "replay.jsonl", match_dir / "trace.jsonl"
    records = _replay_records(match_dir)
    initial = next(r for r in records if r.get("record_type") == "tick" and r["tick"] == 0)
    defender = next(a for a in initial["agents"] if a["id"] == "B")
    if region == "missing":
        defender.pop("region")
    else:
        defender["region"] = region
    replay.write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in records) + "\n",
        encoding="utf-8",
    )

    # Ordinary tampering first fails at the actual replay/trace digest boundary.
    with pytest.raises(ArtifactIntegrityError, match="Pair binding verification failed"):
        _reconstruct(match_dir)

    # Rebind this synthetic pair explicitly; no verifier is monkeypatched out.
    replay_sha256 = hashlib.sha256(replay.read_bytes()).hexdigest()
    trace_records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    bindings = [r for r in trace_records if r.get("record_type") == "binding"]
    assert len(bindings) == 1
    bindings[0]["replay_sha256"] = replay_sha256
    trace.write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in trace_records) + "\n",
        encoding="utf-8",
    )
    result_path = match_dir / "result.json"
    result = _result(match_dir)
    if region is None or region == "missing":
        # The general schema-4 reader permits an absent region. Active-sensing
        # reconstruction must still require authoritative tick-zero core data.
        loaded = load_schema4_replay(replay)
        assert next(a for a in loaded.ticks[0].agents if a.agent_id == "B").region is None
        assert verify_pair(replay, trace).replay_sha256 == replay_sha256
        with pytest.raises(ArtifactIntegrityError, match="Result association failed"):
            _reconstruct(match_dir)
    result["replay"]["sha256"] = replay_sha256
    result_path.write_text(json.dumps(result), encoding="utf-8")

    if region is None or region == "missing":
        with pytest.raises(ExchangeReconstructionError, match="entrant B has no recorded core region"):
            _reconstruct(match_dir)
    else:
        # Malformed region shape/value is rejected by the normal pair reader.
        with pytest.raises(ArtifactIntegrityError, match=r"unusable canonical replay.*agent\.region"):
            _reconstruct(match_dir)


@pytest.mark.parametrize("hold_ticks", [1, 2])
def test_same_tick_core_loss_and_recovery_survives_until_tick_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hold_ticks: int
) -> None:
    """Native capture observes tick boundaries, including after a transient loss."""
    policy = ruleset_policy._RULESET_POLICIES[BYTEFRAY_RULESET_V6_ALPHA1_ID]
    monkeypatch.setitem(
        ruleset_policy._RULESET_POLICIES,
        BYTEFRAY_RULESET_V6_ALPHA1_ID,
        dataclasses.replace(policy, capture_hold_ticks=hold_ticks),
    )
    # Both anchors leave their cores, so writes do not suppress B's repair.
    # Tick 1 leaves only cell 91 with B. In tick 2 A takes it before B repairs
    # it with byte 0x00: ownership, rather than the beacon, keeps B alive.
    # A takes it again in tick 3; no further repair occurs.
    a_script = [
        ("move", 64),
        *_writes(B_CORE[1:]),
        *_writes([91]),
        *[("read", 0)] * 7,
        *_writes([91]),
    ]
    # Tick 2 starts with B: consume that first two-action offer before repair.
    b_script = [("move", -64), *[("read", 91)] * 9, ("write", 91, 0x00)]
    match_dir = _match(
        tmp_path, "same_tick_recovery", [("A", 0, a_script), ("B", 91, b_script)], 5
    )
    result = _result(match_dir)
    assert result["winner"] == "A"
    assert result["ticks"] == 2 + hold_ticks
    assert result["termination_reason"] == "last_agent_standing"
    playback = _reconstruct(match_dir)

    recovery_states = [s for s in playback.sub_tick_states if s.tick == 2]
    first_zero = next(
        i for i, state in enumerate(recovery_states)
        if all(state.owners[cell] != "B" for cell in B_CORE)
    )
    assert any(state.owners[91] == "B" for state in recovery_states[first_zero + 1:])
    assert all("B" in state.alive_entrants for state in recovery_states)
    assert recovery_states[-1].phase == ExchangePhase.TICK_END
    assert recovery_states[-1].owners[91] == "B"
    assert recovery_states[-1].memory[91] == 0x00

    alive = _tick_end_alive(playback)
    assert all(alive[tick] == frozenset({"A", "B"}) for tick in (0, 1, 2))
    if hold_ticks == 2:
        assert alive[3] == frozenset({"A", "B"})
    assert alive[2 + hold_ticks] == frozenset({"A"})
    # Compare every boundary against the actual runtime's canonical snapshots.
    assert alive == {
        record["tick"]: frozenset(a["id"] for a in record["agents"] if a["alive"])
        for record in _replay_records(match_dir) if record.get("record_type") == "tick"
    }
