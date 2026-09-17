"""Frozen-golden characterization of ``bytefray-rules-2``, pinning the
promotion semantics qualified against ``bytefray-rules-2-alpha11`` at
v2.0.0-beta1.

**History.** Phase 1C of docs/V2_0_BETA1_PLAN.md promoted alpha.11's
evidence-backed candidate semantics into the permanent ``bytefray-rules-2``
identity rather than inventing new gameplay. From v2.0.0-beta1 through V6
Phase 2B.8, this file proved that directly: it ran every scenario below
under both Ruleset identities and diffed the full semantic output --
winner, every per-agent statistic, final arena content, final ownership,
and every replay event.

**Phase 2B.9 conversion.** ``bytefray-rules-2-alpha11`` (and
``bytefray-rules-2-alpha1``, used by the differentiation test below) were
retired from executable registration by V6 Phase 2B.9
(docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md), per the
disposition in docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md
Sec E.2/P.5/T-15. Rather than deleting the proof that promotion preserved
alpha.11's semantics, this file was converted -- following the same
frozen-golden pattern already established by ``test_ruleset_v1_equivalence.py``
for the v1.4 ownership-accounting optimization -- into a permanent
characterization: the ``EXPECTED`` table below pins the exact semantic
snapshot (as a SHA-256 digest plus the human-readable summary fields used
to diagnose a mismatch) that ``bytefray-rules-2-alpha11`` produced for each
scenario in its last passing run before retirement, and every scenario is
now run only under stable ``bytefray-rules-2`` and compared against that
frozen snapshot.

**Provenance.** The frozen values were captured at commit
``b55b8ea49019bd3ca5f1710b79fd4dfe5b6be24c`` (the ``v6-research`` HEAD
immediately before Phase 2B.9's registry edit landed), using this file's
own pre-conversion scenario corpus and helper functions -- reproducible by
checking out that commit's version of this file (which still exercises
``bytefray-rules-2-alpha11`` directly) and rerunning it. That run first
re-confirmed the live alpha11-vs-v2 equivalence still held, then derived
these digests from the confirmed-passing alpha11 side.

**Policy, restated from the v1 file this pattern is copied from:** a
legitimate Ruleset 2 gameplay, Agent API, RNG, or schema change must
version this file's expectations deliberately; it must never refresh
``EXPECTED`` in place to make a regression pass.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.python_runtime import CORE_BEACON_BYTE, CORE_SEED_BYTE_ALPHA1, core_addresses
from battle_engine.reference_agents import reference_agent_spec
from battle_engine.replay import TickSnapshot, iter_replay
from battle_engine.rules import BYTEFRAY_RULESET_ID
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V2_ID
from battle_engine.starters import ensure_starter_agents

V1 = BYTEFRAY_RULESET_ID
V2 = BYTEFRAY_RULESET_V2_ID


def _write_agent(agent_dir: Path, agent_id: str, source: bytes) -> None:
    agent_dir.mkdir(parents=True)
    manifest = {
        "kind": "python",
        "api_version": 1,
        "entrypoint": "agent.py:create_agent",
        "name": agent_id,
        "display": agent_id.title(),
        "version": "1.0",
    }
    agent_dir.joinpath("agent.yaml").write_bytes(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    agent_dir.joinpath("agent.py").write_bytes(source)


def _scripted_entrant(root: Path, agent_id: str, source: bytes, *, slot: str, start: int) -> MatchEntrant:
    agent_dir = root / "agents" / agent_id
    _write_agent(agent_dir, agent_id, source)
    return MatchEntrant.python(slot, agent_id, start, resolve_agent(root, agent_id))


NOP_SOURCE = b"""from battle_engine.agent_api import ActionKind, AgentAction

class Agent:
    def reset(self, context):
        pass

    def act(self, observation):
        return AgentAction(ActionKind.NOP)

def create_agent():
    return Agent()
"""


def _scripted_writer_source(addresses: list[int], value: int = 0xAA) -> bytes:
    return (
        "from battle_engine.agent_api import ActionKind, AgentAction\n\n"
        f"ADDRESSES = {addresses!r}\n\n"
        "class Agent:\n"
        "    def reset(self, context):\n"
        "        self.index = 0\n\n"
        "    def act(self, observation):\n"
        "        if self.index < len(ADDRESSES):\n"
        "            addr = ADDRESSES[self.index]\n"
        "            self.index += 1\n"
        f"            return AgentAction(ActionKind.WRITE, addr, {value})\n"
        "        return AgentAction(ActionKind.NOP)\n\n"
        "def create_agent():\n"
        "    return Agent()\n"
    ).encode()


# ---------------------------------------------------------------------------
# Scenario corpus -- identical in substance to the pre-conversion
# alpha11-vs-v2 corpus; each builder is now module-level so it can be
# shared between the (removed) golden-generation step and this permanent
# test.
# ---------------------------------------------------------------------------


def _build_claimer_vs_core_tracker(root: Path) -> tuple[MatchEntrant, ...]:
    ensure_starter_agents(data_root=root)
    claimer = resolve_agent(root, "claimer")
    tracker = reference_agent_spec("core_tracker")
    return (
        MatchEntrant.python("A", "claimer", 0, claimer),
        MatchEntrant.python("B", "core_tracker", 2048, tracker),
    )


def _build_hunter_vs_core_tracker(root: Path) -> tuple[MatchEntrant, ...]:
    ensure_starter_agents(data_root=root)
    hunter = resolve_agent(root, "hunter")
    tracker = reference_agent_spec("core_tracker")
    return (
        MatchEntrant.python("A", "hunter", 0, hunter),
        MatchEntrant.python("B", "core_tracker", 2048, tracker),
    )


def _build_core_tracker_vs_core_defender(root: Path) -> tuple[MatchEntrant, ...]:
    tracker = reference_agent_spec("core_tracker")
    defender = reference_agent_spec("core_defender")
    return (
        MatchEntrant.python("A", "core_tracker", 0, tracker),
        MatchEntrant.python("B", "core_defender", 2048, defender),
    )


def _build_core_tracker_vs_reactive_core_defender(root: Path) -> tuple[MatchEntrant, ...]:
    tracker = reference_agent_spec("core_tracker")
    reactive = reference_agent_spec("reactive_core_defender")
    return (
        MatchEntrant.python("A", "core_tracker", 0, tracker),
        MatchEntrant.python("B", "reactive_core_defender", 2048, reactive),
    )


def _build_three_entrant(root: Path) -> tuple[MatchEntrant, ...]:
    ensure_starter_agents(data_root=root)
    claimer = resolve_agent(root, "claimer")
    tracker = reference_agent_spec("core_tracker")
    defender = reference_agent_spec("core_defender")
    return (
        MatchEntrant.python("A", "claimer", 0, claimer),
        MatchEntrant.python("B", "core_tracker", 1365, tracker),
        MatchEntrant.python("C", "core_defender", 2730, defender),
    )


def _build_wraparound_core(root: Path) -> tuple[MatchEntrant, ...]:
    arena_size = 128
    start = arena_size - 3  # core spans 125,126,127,0,1,2,3,4
    return (
        _scripted_entrant(root, "wrapper", NOP_SOURCE, slot="A", start=start),
        _scripted_entrant(root, "other", NOP_SOURCE, slot="B", start=60),
    )


def _build_deterministic_capture_case(root: Path) -> tuple[MatchEntrant, ...]:
    core = [start_addr for start_addr in range(20, 28)]
    return (
        _scripted_entrant(root, "victim", NOP_SOURCE, slot="A", start=20),
        _scripted_entrant(root, "attacker", _scripted_writer_source(core), slot="B", start=60),
    )


def _build_deterministic_non_capture_case(root: Path) -> tuple[MatchEntrant, ...]:
    return (
        _scripted_entrant(root, "idle_a", NOP_SOURCE, slot="A", start=20),
        _scripted_entrant(root, "idle_b", NOP_SOURCE, slot="B", start=60),
    )


def _build_diff_idle_pair(root: Path) -> tuple[MatchEntrant, ...]:
    return (
        _scripted_entrant(root, "idle_a", NOP_SOURCE, slot="A", start=20),
        _scripted_entrant(root, "idle_b", NOP_SOURCE, slot="B", start=60),
    )


@dataclass(frozen=True)
class Scenario:
    key: str
    build: Callable[[Path], tuple[MatchEntrant, ...]]
    seed: int
    arena_size: int = 4096
    max_ticks: int = 200
    instr_per_tick: int = 8


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("claimer_vs_core_tracker_seed1", _build_claimer_vs_core_tracker, seed=1),
    Scenario("claimer_vs_core_tracker_seed2", _build_claimer_vs_core_tracker, seed=2),
    Scenario("claimer_vs_core_tracker_seed3", _build_claimer_vs_core_tracker, seed=3),
    Scenario("hunter_vs_core_tracker_seed1", _build_hunter_vs_core_tracker, seed=1),
    Scenario("hunter_vs_core_tracker_seed2", _build_hunter_vs_core_tracker, seed=2),
    Scenario("core_tracker_vs_core_defender", _build_core_tracker_vs_core_defender, seed=4),
    Scenario(
        "core_tracker_vs_reactive_core_defender",
        _build_core_tracker_vs_reactive_core_defender,
        seed=5,
    ),
    Scenario("three_entrant_match", _build_three_entrant, seed=2),
    Scenario("wraparound_core", _build_wraparound_core, seed=1, arena_size=128, max_ticks=5),
    Scenario(
        "deterministic_capture_case",
        _build_deterministic_capture_case,
        seed=1,
        arena_size=128,
        max_ticks=20,
    ),
    Scenario(
        "deterministic_non_capture_case",
        _build_deterministic_non_capture_case,
        seed=1,
        arena_size=128,
        max_ticks=10,
    ),
)


def _run(root: Path, entrants: tuple[MatchEntrant, ...], *, ruleset_id: str, scenario: Scenario):
    request = MatchRequest(
        Config(arena_size=scenario.arena_size, instr_per_tick=scenario.instr_per_tick, seed=scenario.seed),
        entrants,
        max_ticks=scenario.max_ticks,
        replay_path=root / "replay.jsonl",
        verbose=False,
        ruleset_id=ruleset_id,
    )
    return NativeMatchService().run(request)


def _agent_snapshot(result) -> dict[str, tuple]:
    """Every semantically meaningful per-agent field, excluding nothing
    ruleset-identity-derived (``NativeAgentResult`` carries no such field)."""

    return {
        agent.agent_id: (
            agent.alive,
            agent.score,
            agent.alive_ticks,
            agent.kills,
            agent.deaths,
            agent.cpu_total,
            agent.mem_writes,
            agent.territory_last,
            agent.territory_max,
            round(agent.territory_avg, 9),
            agent.termination_reason,
        )
        for agent in result.agents
    }


def _final_arena_and_owners(result, arena_size: int) -> tuple[dict[int, int], dict[int, str | None]]:
    arena: dict[int, int] = {}
    owners: dict[int, str | None] = {}
    for record in iter_replay(result.replay_path):
        if not isinstance(record, TickSnapshot):
            continue
        for diff in record.memory_diffs:
            for offset, value in enumerate(diff.values):
                arena[(diff.address + offset) % arena_size] = value
            for offset in range(diff.length):
                owners[(diff.address + offset) % arena_size] = diff.owner
    return arena, owners


def _events(result) -> list[tuple[int, str, dict[str, Any]]]:
    """Every replay event, normalized to a plain, order-preserving tuple
    list -- includes the tick it occurred on so timing equivalence (not
    just event content) is part of the characterization."""

    out: list[tuple[int, str, dict[str, Any]]] = []
    for record in iter_replay(result.replay_path):
        if not isinstance(record, TickSnapshot):
            continue
        for event in record.events:
            out.append((record.tick, type(event).__name__, asdict(event)))
    return out


def _snapshot(result, arena_size: int) -> dict[str, Any]:
    arena, owners = _final_arena_and_owners(result, arena_size)
    return {
        "winner": result.winner,
        "ticks_run": result.ticks_run,
        "termination_reason": result.termination_reason.value,
        "score": dict(result.score),
        "agents": _agent_snapshot(result),
        "arena": {str(address): value for address, value in sorted(arena.items())},
        "owners": {str(address): owner for address, owner in sorted(owners.items())},
        "events": _events(result),
    }


def _snapshot_digest(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# ---------------------------------------------------------------------------
# EXPECTED -- frozen from bytefray-rules-2-alpha11's last passing run
# against this exact scenario corpus, at commit
# b55b8ea49019bd3ca5f1710b79fd4dfe5b6be24c, immediately before Phase 2B.9
# removed bytefray-rules-2-alpha11's executable registration. Each digest
# covers the complete semantic snapshot (winner, ticks, termination,
# per-agent score/stat tuple, final arena bytes, final ownership, and the
# full ordered event stream); the summary fields exist only to make a
# mismatch diagnosable without recomputing the digest by hand.
# ---------------------------------------------------------------------------

EXPECTED: dict[str, dict[str, Any]] = {
    "claimer_vs_core_tracker_seed1": {
        "digest": "9b3428a293350117fd641e3078f90cecb19ab899ff3c41a4d9b272fc5dc9bde5",
        "winner": "A",
        "ticks_run": 200,
        "termination_reason": "tick_limit",
        "score": {"A": 2448.0, "B": 1370.0},
        "agent_ids": ["A", "B"],
    },
    "claimer_vs_core_tracker_seed2": {
        "digest": "c361181c887791a0253d8c46a35eb96a968c0dbffad6b898247a06287d6fdea3",
        "winner": "B",
        "ticks_run": 144,
        "termination_reason": "last_agent_standing",
        "score": {"A": 1320.0, "B": 789.0},
        "agent_ids": ["A", "B"],
    },
    "claimer_vs_core_tracker_seed3": {
        "digest": "50641a19f31848dec13775193fae06a6dbe5afc110a250b8498d45e62587011b",
        "winner": "B",
        "ticks_run": 110,
        "termination_reason": "last_agent_standing",
        "score": {"A": 792.0, "B": 502.0},
        "agent_ids": ["A", "B"],
    },
    "hunter_vs_core_tracker_seed1": {
        "digest": "7f6b95d9695d9ad2318d5f081c1186e291d07e346428c109a8899dc4bff6b3eb",
        "winner": "A",
        "ticks_run": 200,
        "termination_reason": "tick_limit",
        "score": {"A": 2419.0, "B": 1423.0},
        "agent_ids": ["A", "B"],
    },
    "hunter_vs_core_tracker_seed2": {
        "digest": "b7b4ca74454eb5d876a75d4b16ea67e4254a4cd08455f5dcd6e046a829f4da1c",
        "winner": "B",
        "ticks_run": 158,
        "termination_reason": "last_agent_standing",
        "score": {"A": 1560.0, "B": 947.0},
        "agent_ids": ["A", "B"],
    },
    "core_tracker_vs_core_defender": {
        "digest": "55a8c88b467ddaff6c210d613909cb4dc04bd258e96518461d4a72a34fedb078",
        "winner": "B",
        "ticks_run": 200,
        "termination_reason": "tick_limit",
        "score": {"A": 1554.0, "B": 1830.0},
        "agent_ids": ["A", "B"],
    },
    "core_tracker_vs_reactive_core_defender": {
        "digest": "00a0fe226da2bd6a8361b06bc177afc472c0f13f662ade94d9dddce83951f723",
        "winner": "B",
        "ticks_run": 200,
        "termination_reason": "tick_limit",
        "score": {"A": 1558.0, "B": 1797.0},
        "agent_ids": ["A", "B"],
    },
    "three_entrant_match": {
        "digest": "40e635fb30cd623c6616f74a940e35fbeb51267133e169e6fae27aca148c3bc2",
        "winner": "A",
        "ticks_run": 200,
        "termination_reason": "tick_limit",
        "score": {"A": 2186.0, "B": 1382.0, "C": 1617.0},
        "agent_ids": ["A", "B", "C"],
    },
    "wraparound_core": {
        "digest": "a12280524c7102116a7929696dd7c930f774409a44b9bdf001dd477cbd34801e",
        "winner": "tie",
        "ticks_run": 5,
        "termination_reason": "tick_limit",
        "score": {"A": 5.0, "B": 5.0},
        "agent_ids": ["A", "B"],
    },
    "deterministic_capture_case": {
        "digest": "26fc1cc7173c5f1ea3f5f5ae6bbb756e6310844778fdd31bda50fec7d0708de2",
        "winner": "B",
        "ticks_run": 1,
        "termination_reason": "last_agent_standing",
        "score": {"A": 0, "B": 6.0},
        "agent_ids": ["A", "B"],
    },
    "deterministic_non_capture_case": {
        "digest": "46c20c353158c71a079a35c3f352a8289b6f536c2f238d38a52baeef8a4cb24a",
        "winner": "tie",
        "ticks_run": 10,
        "termination_reason": "tick_limit",
        "score": {"A": 10.0, "B": 10.0},
        "agent_ids": ["A", "B"],
    },
}


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.key for s in SCENARIOS])
def test_ruleset_v2_matches_frozen_alpha11_promotion_golden(tmp_path: Path, scenario: Scenario) -> None:
    """Stable ``bytefray-rules-2`` must still produce exactly the semantic
    output that was proven equivalent to ``bytefray-rules-2-alpha11`` at
    promotion time -- now checked against the frozen golden rather than a
    live second execution, since alpha11 is no longer executable."""

    entrants = scenario.build(tmp_path / "agents")
    result = _run(tmp_path, entrants, ruleset_id=V2, scenario=scenario)
    snapshot = _snapshot(result, scenario.arena_size)
    expected = EXPECTED[scenario.key]

    assert _snapshot_digest(snapshot) == expected["digest"]
    assert snapshot["winner"] == expected["winner"]
    assert snapshot["ticks_run"] == expected["ticks_run"]
    assert snapshot["termination_reason"] == expected["termination_reason"]
    assert snapshot["score"] == expected["score"]
    assert sorted(snapshot["agents"]) == expected["agent_ids"]


# ---------------------------------------------------------------------------
# Explicit non-equivalence check: the golden corpus above proves alpha11's
# promoted semantics persist in v2; this proves that proof is not vacuous --
# v1 and alpha1 remain genuinely, behaviorally distinct from v2, not merely
# differently labeled. v1 remains executable and is run live; alpha1 was
# retired from execution by Phase 2B.9, so its side is the frozen constant
# ``CORE_SEED_BYTE_ALPHA1`` that already governs its (still-present, shared)
# core-seeding logic in ``python_runtime.py`` -- not a value invented for
# this test.
# ---------------------------------------------------------------------------


def test_permanent_v2_still_differs_from_ruleset_v1_and_frozen_alpha1(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        _build_diff_idle_pair(tmp_path / "agents"),
        ruleset_id=V1,
        scenario=Scenario("diff_v1", _build_diff_idle_pair, seed=1, arena_size=128, max_ticks=3),
    )
    v2_result = _run(
        tmp_path / "v2",
        _build_diff_idle_pair(tmp_path / "v2" / "agents"),
        ruleset_id=V2,
        scenario=Scenario("diff_v2", _build_diff_idle_pair, seed=1, arena_size=128, max_ticks=3),
    )
    v1_arena, _ = _final_arena_and_owners(result, 128)
    v2_arena, _ = _final_arena_and_owners(v2_result, 128)
    core = core_addresses(20, 128)

    # v1: no core mechanic at all -- no diffs published, nothing seeded.
    assert not any(address in v1_arena for address in core)
    # frozen alpha1: core was seeded, but with a blank byte -- invisible to
    # search. Confirmed live before retirement (Phase 2B.9 golden capture);
    # the constant itself is still current, shared source, not a guess.
    assert CORE_SEED_BYTE_ALPHA1 == 0x00
    # permanent v2: promotes alpha.11's observable seed -- the beacon.
    assert all(v2_arena[address] == CORE_BEACON_BYTE for address in core)
