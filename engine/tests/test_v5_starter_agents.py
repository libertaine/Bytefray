from __future__ import annotations

"""V5 Alpha 1 Phase C: the bundled ``v5_*`` educational starter population.

Phase C ships four Agent API v2 starters that teach one concept each --
regional offense, search-and-strike movement, READ-driven core defense, and
a two-process team. See ``docs/research/v5/V5_ALPHA1_PHASE_C_STARTER_AGENTS.md``.

These tests are deliberately behavioural rather than structural. A starter
is not qualified because its files exist, its manifest parses, or its class
defines a method: it is qualified because a real deterministic match under
stable ``bytefray-rules-4`` shows it doing the thing it claims to teach.
Every competence assertion below therefore reads its evidence out of a
replay or an agent trace produced by an actual match against an explicit,
purpose-built fixture whose own behaviour is stated in its source.

The fixtures live only in this module. They are written into ``tmp_path``
and are never installed, never discoverable, and never given information a
product starter could not legally obtain.
"""

import json
from pathlib import Path

import pytest
from battle_engine.agent_api import (
    AgentV2,
    ProcessDeclaration,
    load_python_agent,
)
from battle_engine.agents import agent_spec_from_dir, discover_agents
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.replay import MatchResult, iter_replay
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID
from battle_engine.starters import (
    STARTER_AGENT_NAMES,
    ensure_starter_agents,
    starter_agent_resource_dir,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The Phase C population. Additive: none of these replaces a ``v4_*`` ID.
V5_STARTER_NAMES = (
    "v5_region_attacker",
    "v5_scout_striker",
    "v5_core_defender",
    "v5_dual_team",
)

#: The historical population Phase C must leave untouched.
V4_STARTER_NAMES = (
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_defender_scout",
    "v4_local_defender",
    "v4_scout",
    "v4_quorum",
)

ARENA_SIZE = 512
CORE_SIZE = 8
QUOTA = 8


# --------------------------------------------------------------------------
# Fixtures: test-only opponents with explicitly stated behaviour.
# --------------------------------------------------------------------------

#: Stands still and never writes. A vulnerable, perfectly static objective:
#: whatever a starter takes from its core stays taken, so a capture here is
#: a capture the starter earned by covering the region, not one the fixture
#: handed over by forgetting to repair.
IDLE_TARGET_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class IdleTarget:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration(id="idle", reach=1, share=1.0)]

    def act(self, observation):
        return AgentAction(kind=ActionKindV2.MOVE, operand=0)


def create_agent():
    return IdleTarget()
"""

#: Walks forward three cells per action and never writes. A moving contact:
#: an agent with no memory has to re-acquire it every action, and an agent
#: with memory has to notice the memory going stale.
DRIFTING_TARGET_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class DriftingTarget:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration(id="drifter", reach=1, share=1.0)]

    def act(self, observation):
        return AgentAction(kind=ActionKindV2.MOVE, operand=3)


def create_agent():
    return DriftingTarget()
"""

#: Applies real, recurring pressure to a defender's core: it closes on the
#: nearest visible enemy anchor and then cycles writes over exactly four
#: addresses bracketing it -- offsets -3, -2, +2, +3.
#:
#: Two deliberate limits make this a *measuring instrument* rather than an
#: opponent. It touches at most four cells, so it can never capture an
#: eight-cell core and the match cannot end before detection and repair have
#: been observed many times over; and it never writes offset 0, the anchor
#: itself, so it never disrupts the defender. What is left is a clean,
#: sustained damage/repair contest, which is the mechanic under test.
#:
#: It uses only ``ObservationV2``. It is not told where the defender's core
#: is; it simply presses the ground the defender is standing on.
CORE_PRESSER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

PRESS_OFFSETS = (-3, -2, 2, 3)


class CorePresser:
    def reset(self, context):
        self.context = context
        self.arena = context.arena_size
        self.cursor = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="presser", reach=12, share=1.0)]

    def act(self, observation):
        visible = observation.visible_enemy_anchor_addresses
        if not visible:
            return AgentAction(kind=ActionKindV2.MOVE, operand=observation.self_reach)
        target = min(visible, key=lambda a: (self._distance(a, observation.self_anchor), a))
        if self._distance(target, observation.self_anchor) > observation.self_reach - 4:
            return AgentAction(kind=ActionKindV2.MOVE, operand=self._delta(target, observation.self_anchor))
        for _ in range(len(PRESS_OFFSETS)):
            offset = PRESS_OFFSETS[self.cursor % len(PRESS_OFFSETS)]
            self.cursor += 1
            address = (target + offset) % self.arena
            if self._distance(address, observation.self_anchor) <= observation.self_reach:
                return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=0x11)
        return AgentAction(kind=ActionKindV2.MOVE, operand=0)

    def _distance(self, a, b):
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _delta(self, target, anchor):
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        chosen = backward if abs(backward) < abs(forward) else forward
        return max(-64, min(64, chosen))


def create_agent():
    return CorePresser()
"""

FIXTURE_SOURCES = {
    "fixture_idle_target": IDLE_TARGET_SOURCE,
    "fixture_drifting_target": DRIFTING_TARGET_SOURCE,
    "fixture_core_presser": CORE_PRESSER_SOURCE,
}


def _write_fixture(root: Path, name: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
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
    agent_dir.joinpath("agent.py").write_text(FIXTURE_SOURCES[name], encoding="utf-8")


# --------------------------------------------------------------------------
# Match harness
# --------------------------------------------------------------------------


def _starter_spec(name: str):
    """Resolve one starter from the SHIPPED resource tree, not the catalog.

    Qualifying the packaged copy is the point: that is the file a user
    actually receives, and a repository/package divergence is exactly the
    failure ``test_v5_starters_are_packaged_byte_for_byte`` exists to catch.
    """

    spec = agent_spec_from_dir(starter_agent_resource_dir(name, resource_root=REPO_ROOT))
    assert spec is not None, name
    return spec


def _fixture_spec(root: Path, name: str):
    _write_fixture(root, name)
    spec = agent_spec_from_dir(root / "agents" / name)
    assert spec is not None, name
    return spec


class Match:
    """One completed stable-V4 match, with its replay and trace parsed."""

    def __init__(self, replay_path: Path, trace_path: Path, starts: tuple[int, int]):
        self.starts = starts
        self.records = list(iter_replay(replay_path))
        self.result = next(r for r in self.records if isinstance(r, MatchResult))
        self.trace = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def decisions(self, slot: str) -> list[dict]:
        return [
            record
            for record in self.trace
            if record.get("record_type") == "decision_v2"
            and record.get("agent_id") == slot
        ]

    def declarations(self, slot: str) -> list[dict]:
        return [
            record
            for record in self.trace
            if record.get("record_type") == "declaration"
            and record.get("agent_id") == slot
        ]

    def statuses(self, slot: str) -> set[str]:
        return {(d.get("applied_result") or {}).get("status") for d in self.decisions(slot)}

    def action_kinds(self, slot: str) -> set[str]:
        return {(d.get("action") or {}).get("kind") for d in self.decisions(slot)}

    def written_addresses(self, slot: str) -> set[int]:
        return {
            (d["action"]["operand"]) % ARENA_SIZE
            for d in self.decisions(slot)
            if d["action"]["kind"] == "write"
        }

    def core_cells(self, slot: str) -> set[int]:
        """The eight cells of one entrant's core, from its known start."""

        base = self.starts[0] if slot == "A" else self.starts[1]
        return {(base + i) % ARENA_SIZE for i in range(CORE_SIZE)}

    def termination(self, slot: str) -> str | None:
        return next(a.termination_reason for a in self.result.agents if a.agent_id == slot)

    def captured(self, slot: str) -> bool:
        return self.termination(slot) == "core_captured"


def run_match(
    tmp_path: Path,
    label: str,
    a_spec,
    b_spec,
    *,
    starts: tuple[int, int],
    seed: int,
    ticks: int,
) -> Match:
    replay_path = tmp_path / label / "replay.jsonl"
    trace_path = tmp_path / label / "trace.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=ARENA_SIZE, instr_per_tick=QUOTA),
        entrants=(
            MatchEntrant.python("A", a_spec.name, starts[0], a_spec),
            MatchEntrant.python("B", b_spec.name, starts[1], b_spec),
        ),
        max_ticks=ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    NativeMatchService().run(request)
    return Match(replay_path, trace_path, starts)


def gameplay_digest(match: Match) -> str:
    """Everything the agents did, with wall-clock timing excluded.

    Trace records carry ``wall_time_ms`` and the replay header carries
    generation timestamps, so raw file bytes differ between two identical
    runs. Determinism is a property of the decisions and the resulting
    arena, which is what this hashes.
    """

    import hashlib

    digest = hashlib.sha256()
    for record in match.trace:
        kind = record.get("record_type")
        if kind == "decision_v2":
            digest.update(
                json.dumps(
                    [
                        record["agent_id"],
                        record["process_id"],
                        record["action"],
                        record["observation"],
                        record["applied_result"],
                    ],
                    sort_keys=True,
                ).encode("utf-8")
            )
        elif kind == "declaration":
            digest.update(
                json.dumps(
                    [record["agent_id"], record["process_id"], record["reach"], record["share"]],
                    sort_keys=True,
                ).encode("utf-8")
            )
    return digest.hexdigest()


# --------------------------------------------------------------------------
# Registration, manifests and packaging
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_is_a_declared_bundled_starter(name: str) -> None:
    assert name in STARTER_AGENT_NAMES


def test_v5_starters_do_not_displace_the_v4_population() -> None:
    """Phase C is additive: every historical ID keeps its slot and order."""

    assert STARTER_AGENT_NAMES.index("v4_claimer") < STARTER_AGENT_NAMES.index(
        "v5_region_attacker"
    )
    for name in V4_STARTER_NAMES:
        assert name in STARTER_AGENT_NAMES
    assert len(set(STARTER_AGENT_NAMES)) == len(STARTER_AGENT_NAMES)


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_manifest_is_a_valid_current_schema_v2_manifest(name: str) -> None:
    manifest = json.loads(
        (starter_agent_resource_dir(name, resource_root=REPO_ROOT) / "agent.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["name"] == name
    assert manifest["kind"] == "python"
    assert manifest["api_version"] == 2
    assert manifest["entrypoint"] == "agent.py:create_agent"
    # 1.1.0 in V5 Alpha 1 Phase D: every starter gained a declared
    # ``parameters`` section and reads its resolved values. Behaviour at the
    # declared defaults is unchanged from Phase C -- proved by
    # ``test_v5_starter_defaults_reproduce_the_phase_c_gameplay_digest`` in
    # ``test_v5_agent_parameters.py``, not by this manifest literal.
    assert manifest["version"] == "1.1.0"
    assert manifest["display"].startswith("V5 ")
    assert manifest["display"].endswith("(Starter)")


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starters_are_packaged_byte_for_byte(name: str) -> None:
    """The repository catalog copy and the shipped copy must not diverge."""

    packaged = starter_agent_resource_dir(name, resource_root=REPO_ROOT)
    catalog = REPO_ROOT / "agents" / name
    packaged_files = sorted(
        p.relative_to(packaged).as_posix()
        for p in packaged.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    assert packaged_files == ["agent.py", "agent.yaml"]
    for relative in packaged_files:
        assert (catalog / relative).read_bytes() == (packaged / relative).read_bytes()


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_loads_through_the_public_agent_api(name: str) -> None:
    loaded = load_python_agent(_starter_spec(name))
    assert loaded.metadata.api_version == 2
    assert isinstance(loaded.instance, AgentV2)


def test_v5_starter_signature_bytes_do_not_collide_with_any_bundled_starter() -> None:
    """Each V5 starter's claim byte must be its own across the whole roster.

    Two agents sharing a signature cannot tell each other's ground apart,
    which matters to any starter that reads ownership before writing.

    Scoped to the bytes Phase C introduces rather than asserting global
    uniqueness: ``v4_claimer`` and the Agent-API-v1 ``claimer`` both claim
    with ``0xC1``, a pre-existing overlap between two frozen historical
    agents that Phase C must not "fix" (see the Phase C report, Section L).
    """

    import re

    resource_dir = REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents"
    signatures: dict[str, int] = {}
    for name in STARTER_AGENT_NAMES:
        source_path = resource_dir / name / "agent.py"
        if not source_path.is_file():
            continue  # native VM starters ship a manifest only
        source = source_path.read_text("utf-8")
        # Two spellings are in use: the older starters assign the literal
        # directly, the V5 starters name it as a module constant first.
        found = re.findall(
            r"^SIGNATURE = (0x[0-9A-Fa-f]+)|self\.signature = (0x[0-9A-Fa-f]+)",
            source,
            re.MULTILINE,
        )
        literals = [constant or attribute for constant, attribute in found]
        if not literals:
            continue  # agents that inline their claim byte, e.g. v4_scout
        assert len(literals) == 1, f"{name} declares {len(literals)} signature bytes"
        signatures[name] = int(literals[0], 16)

    for name in V5_STARTER_NAMES:
        assert name in signatures, f"{name} must declare exactly one signature byte"
        claimants = [other for other, value in signatures.items() if value == signatures[name]]
        assert claimants == [name], f"{name} shares its signature with {claimants}"


# --------------------------------------------------------------------------
# Declaration contract
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    (
        ("v5_region_attacker", (("attacker", 16, 1.0),)),
        ("v5_scout_striker", (("striker", 40, 1.0),)),
        ("v5_core_defender", (("defender", 12, 1.0),)),
        ("v5_dual_team", (("raider", 32, 0.5), ("keeper", 12, 0.5))),
    ),
)
def test_v5_starter_declares_exactly_the_documented_processes(
    name: str, expected: tuple[tuple[str, int, float], ...]
) -> None:
    """Reach and share are read back from the agent, never transcribed."""

    import random

    from battle_engine.agent_api import MatchContextV2

    instance = load_python_agent(_starter_spec(name)).instance
    instance.reset(
        MatchContextV2(
            agent_id="A",
            seed=1,
            arena_size=ARENA_SIZE,
            tick_limit=100,
            rng=random.Random(1),
        )
    )
    declarations = instance.declare_processes()
    assert all(isinstance(d, ProcessDeclaration) for d in declarations)
    assert tuple((d.id, d.reach, d.share) for d in declarations) == expected
    assert sum(d.share for d in declarations) == pytest.approx(1.0, abs=1e-12)


# --------------------------------------------------------------------------
# Determinism and legality
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_is_deterministic_for_one_seed(tmp_path: Path, name: str) -> None:
    """Same seed, same opponent, same start: identical decisions, twice."""

    digests = []
    for run in ("first", "second"):
        match = run_match(
            tmp_path,
            f"{name}-{run}",
            _starter_spec(name),
            _fixture_spec(tmp_path, "fixture_drifting_target"),
            starts=(0, 200),
            seed=301,
            ticks=120,
        )
        digests.append(gameplay_digest(match))
    assert digests[0] == digests[1]
    assert len(digests[0]) == 64


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
@pytest.mark.parametrize(
    "fixture", ("fixture_idle_target", "fixture_drifting_target", "fixture_core_presser")
)
def test_v5_starter_emits_only_legal_in_reach_api_v2_actions(
    tmp_path: Path, name: str, fixture: str
) -> None:
    match = run_match(
        tmp_path,
        f"{name}-legal-{fixture}",
        _starter_spec(name),
        _fixture_spec(tmp_path, fixture),
        starts=(0, 120),
        seed=302,
        ticks=200,
    )
    decisions = match.decisions("A")
    assert decisions, "the starter never got an action"
    assert match.action_kinds("A") <= {"read", "write", "move"}
    assert match.statuses("A") == {"APPLIED"}
    assert match.termination("A") in (None, "core_captured")
    assert all(d.get("diagnostic") is None for d in decisions)


@pytest.mark.parametrize("name", V5_STARTER_NAMES)
def test_v5_starter_never_exceeds_the_entrant_action_quota(
    tmp_path: Path, name: str
) -> None:
    """Q=8 applied action slots per entrant per tick, never more."""

    match = run_match(
        tmp_path,
        f"{name}-quota",
        _starter_spec(name),
        _fixture_spec(tmp_path, "fixture_idle_target"),
        starts=(0, 120),
        seed=303,
        ticks=60,
    )
    per_tick: dict[int, int] = {}
    for decision in match.decisions("A"):
        tick = decision["observation"]["current_tick"]
        per_tick[tick] = per_tick.get(tick, 0) + 1
    assert per_tick, "the starter never got an action"
    assert max(per_tick.values()) <= QUOTA


# --------------------------------------------------------------------------
# Archetype competence
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", ("v5_region_attacker", "v5_scout_striker"))
def test_offensive_starter_converts_contact_into_a_full_core_capture(
    tmp_path: Path, name: str
) -> None:
    """The whole point of the region lesson, proved on a real match.

    Against a static target the offensive starters must not merely land a
    hit: they must take every cell of the opponent's eight-cell core at the
    same time, which is what the engine's core-capture rule requires.
    """

    match = run_match(
        tmp_path,
        f"{name}-capture",
        _starter_spec(name),
        _fixture_spec(tmp_path, "fixture_idle_target"),
        starts=(0, 200),
        seed=304,
        ticks=200,
    )
    enemy_core = match.core_cells("B")
    written = match.written_addresses("A")

    # More than one address: the failure mode Phase C exists to stop.
    assert len(written) > 1
    # And more than one of them a real cell of the objective.
    assert len(written & enemy_core) >= 2
    # Simultaneous, complete, engine-adjudicated capture.
    assert written >= enemy_core
    assert match.captured("B")
    assert not match.captured("A")
    assert match.result.winner == "A"


@pytest.mark.parametrize("name", ("v5_region_attacker", "v5_scout_striker", "v5_dual_team"))
def test_offensive_starter_spreads_pressure_across_the_objective_region(
    tmp_path: Path, name: str
) -> None:
    """Regional pressure, measured against a moving contact.

    A moving target is the harder case: the point-target ancestors of these
    starters would follow it and keep rewriting one address.
    """

    match = run_match(
        tmp_path,
        f"{name}-spread",
        _starter_spec(name),
        _fixture_spec(tmp_path, "fixture_drifting_target"),
        starts=(0, 100),
        seed=305,
        ticks=200,
    )
    hostile = {
        address
        for address in match.written_addresses("A")
        if address not in match.core_cells("A")
    }
    assert len(hostile) >= CORE_SIZE


def test_scout_striker_searches_before_contact_and_then_attacks(
    tmp_path: Path,
) -> None:
    """MOVE while blind, WRITE after a legitimate detection -- in that order."""

    match = run_match(
        tmp_path,
        "striker-search",
        _starter_spec("v5_scout_striker"),
        _fixture_spec(tmp_path, "fixture_idle_target"),
        starts=(0, 256),
        seed=306,
        ticks=200,
    )
    decisions = match.decisions("A")

    blind = [d for d in decisions if not d["observation"]["visible_enemy_anchor_addresses"]]
    assert blind, "the fixture was visible from the start; nothing was searched for"
    assert {d["action"]["kind"] for d in blind} == {"move"}

    first_write = next(
        index for index, d in enumerate(decisions) if d["action"]["kind"] == "write"
    )
    # Every action before the first write was a move, and the agent could
    # legitimately see something by the time it struck.
    assert {d["action"]["kind"] for d in decisions[:first_write]} == {"move"}
    assert decisions[first_write]["observation"]["visible_enemy_anchor_addresses"]

    # Search covers ground rather than idling in place.
    anchors = {d["observation"]["self_anchor"] for d in blind}
    assert len(anchors) > 1


def test_core_defender_reads_its_core_detects_loss_and_repairs_it(
    tmp_path: Path,
) -> None:
    """Detection must be earned through READ, and acted on.

    Asserts the precondition first -- the presser really does take cells of
    the defender's core -- so this test fails if either the attack mechanic
    or the defender's response stops working, rather than passing vacuously.
    """

    match = run_match(
        tmp_path,
        "defender-repair",
        _starter_spec("v5_core_defender"),
        _fixture_spec(tmp_path, "fixture_core_presser"),
        starts=(0, 40),
        seed=307,
        ticks=300,
    )
    own_core = match.core_cells("A")

    # Precondition: the fixture genuinely damaged the defender's core.
    presser_writes = match.written_addresses("B")
    assert presser_writes & own_core, "fixture never touched the defended core"

    decisions = match.decisions("A")
    reads = [d for d in decisions if d["action"]["kind"] == "read"]
    assert reads, "the defender never inspected anything"
    inspected = {d["applied_result"]["normalized_address"] for d in reads}
    assert inspected == own_core, "the defender must inspect every cell of its core"

    # Detection: at least one READ came back owned by the opponent, and the
    # very next action was a WRITE reclaiming that exact address.
    repairs: list[int] = []
    pending: int | None = None
    for decision in decisions:
        kind = decision["action"]["kind"]
        result = decision["applied_result"]
        if kind == "read":
            owner = result.get("read_owner")
            pending = result["normalized_address"] if owner not in (None, "A") else None
        elif kind == "write" and pending is not None:
            if decision["action"]["operand"] % ARENA_SIZE == pending:
                repairs.append(pending)
            pending = None
        else:
            pending = None
    assert repairs, "the defender detected no loss, or detected one and ignored it"
    assert set(repairs) <= own_core

    # It survived, and its core was whole enough that it was never captured.
    assert not match.captured("A")


def test_core_defender_keeps_inspecting_while_an_enemy_is_visible(
    tmp_path: Path,
) -> None:
    """The ``v4_local_defender`` trap: offence must not starve defence.

    The bundled ``v4_local_defender`` abandons its patrol whenever an enemy
    is within reach, so standing next to it disarms it. This defender
    reserves inspection actions that offence cannot spend.
    """

    match = run_match(
        tmp_path,
        "defender-not-starved",
        _starter_spec("v5_core_defender"),
        _fixture_spec(tmp_path, "fixture_core_presser"),
        starts=(0, 40),
        seed=308,
        ticks=300,
    )
    under_pressure = [
        d
        for d in match.decisions("A")
        if d["observation"]["visible_enemy_anchor_addresses"]
    ]
    assert under_pressure, "the presser never became visible"
    reads = [d for d in under_pressure if d["action"]["kind"] == "read"]
    assert reads, "inspection stopped entirely while an enemy was in sight"

    # Inspection is a reserved duty, so a healthy share of the actions taken
    # under pressure are still READs rather than all being counter-attacks.
    assert len(reads) / len(under_pressure) > 0.25

    ticks_seen = {d["observation"]["current_tick"] for d in under_pressure}
    ticks_inspected = {d["observation"]["current_tick"] for d in reads}
    assert len(ticks_inspected) / len(ticks_seen) > 0.5


def test_dual_team_runs_both_processes_with_distinct_responsibilities(
    tmp_path: Path,
) -> None:
    """Two declared processes, both actually scheduled, doing different jobs."""

    match = run_match(
        tmp_path,
        "dual-roles",
        _starter_spec("v5_dual_team"),
        _fixture_spec(tmp_path, "fixture_idle_target"),
        starts=(0, 200),
        seed=309,
        ticks=120,
    )
    declarations = match.declarations("A")
    assert [(d["process_id"], d["reach"], d["share"]) for d in declarations] == [
        ("raider", 32, 0.5),
        ("keeper", 12, 0.5),
    ]
    assert sum(d["share"] for d in declarations) == pytest.approx(1.0, abs=1e-12)

    by_process: dict[str, list[dict]] = {"raider": [], "keeper": []}
    for decision in match.decisions("A"):
        by_process[decision["process_id"]].append(decision)

    # Both processes really receive action opportunities, in their declared
    # proportion: equal shares of Q=8 means four slots each per tick.
    assert by_process["raider"] and by_process["keeper"]
    assert abs(len(by_process["raider"]) - len(by_process["keeper"])) <= 1

    own_core = match.core_cells("A")
    raider_writes = {
        d["action"]["operand"] % ARENA_SIZE
        for d in by_process["raider"]
        if d["action"]["kind"] == "write"
    }
    keeper_writes = {
        d["action"]["operand"] % ARENA_SIZE
        for d in by_process["keeper"]
        if d["action"]["kind"] == "write"
    }
    # Materially different responsibilities: the keeper works the core it
    # owns, the raider works ground it does not.
    assert keeper_writes == own_core
    assert raider_writes
    assert not (raider_writes & own_core)

    # And the raider travelled while the keeper held station.
    raider_anchors = {d["observation"]["self_anchor"] for d in by_process["raider"]}
    keeper_anchors = {d["observation"]["self_anchor"] for d in by_process["keeper"]}
    assert len(raider_anchors) > len(keeper_anchors)


# --------------------------------------------------------------------------
# Strategic diversity
# --------------------------------------------------------------------------


def test_v5_starters_are_not_four_versions_of_one_strategy(tmp_path: Path) -> None:
    """Each starter must be distinguishable from the others by behaviour.

    Guards the redundancy failure Phase C was told to avoid -- ``same sweep,
    different reach``. Profiles are measured from real matches against the
    same fixture, not asserted from source.

    The static fixture is the controlled scenario: a drifting target laps
    the arena and eventually walks over the starter's own home, which would
    let an attacker's contact-centred sweep touch its own core cells by
    coincidence and blur the offence/defence axis.
    """

    profiles: dict[str, tuple] = {}
    for name in V5_STARTER_NAMES:
        match = run_match(
            tmp_path,
            f"{name}-profile",
            _starter_spec(name),
            _fixture_spec(tmp_path, "fixture_idle_target"),
            starts=(0, 160),
            seed=310,
            ticks=200,
        )
        decisions = match.decisions("A")
        own_core = match.core_cells("A")
        written = match.written_addresses("A")
        profiles[name] = (
            len({d["process_id"] for d in decisions}),
            tuple(sorted({d["observation"]["self_reach"] for d in decisions})),
            any(d["action"]["kind"] == "read" for d in decisions),
            bool(written & own_core),
            max(
                min((a - d) % ARENA_SIZE, (d - a) % ARENA_SIZE)
                for d in [match.starts[0]]
                for a in {x["observation"]["self_anchor"] for x in decisions}
            )
            > CORE_SIZE,
        )

    assert len(set(profiles.values())) == len(V5_STARTER_NAMES), profiles

    # And the specific axes the population is built around.
    assert profiles["v5_dual_team"][0] == 2
    assert all(profiles[n][0] == 1 for n in V5_STARTER_NAMES if n != "v5_dual_team")
    assert profiles["v5_core_defender"][2] is True  # only starter that READs
    assert [profiles[n][2] for n in V5_STARTER_NAMES].count(True) == 1
    # Only the defender holds station: it steps to the middle of its own
    # core and never travels further than a core width from home.
    assert profiles["v5_core_defender"][4] is False
    assert all(profiles[n][4] is True for n in V5_STARTER_NAMES if n != "v5_core_defender")
    assert profiles["v5_region_attacker"][3] is False  # pure offence, no repair
    assert profiles["v5_scout_striker"][3] is False


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def test_v5_starters_install_and_are_discovered_like_any_product_agent(
    tmp_path: Path,
) -> None:
    """A normal user reaches them through the ordinary bootstrap path."""

    result = ensure_starter_agents(resource_root=REPO_ROOT, data_root=tmp_path)
    assert result.errors == ()

    catalog = discover_agents(tmp_path)
    for name in V5_STARTER_NAMES:
        assert (tmp_path / "agents" / name / "agent.py").is_file()
        assert (tmp_path / "agents" / name / "agent.yaml").is_file()
        spec = catalog[name]
        assert spec.kind == "python"
        assert spec.api_version == 2
        assert spec.display.startswith("V5 ")

    # The historical population is still there, and still resolvable.
    for name in V4_STARTER_NAMES:
        assert catalog[name].api_version == 2


def test_v5_starter_install_leaves_the_v4_population_byte_for_byte_unchanged(
    tmp_path: Path,
) -> None:
    """Phase C must not rewrite a historical agent under its historical ID."""

    ensure_starter_agents(resource_root=REPO_ROOT, data_root=tmp_path)
    for name in V4_STARTER_NAMES:
        packaged = starter_agent_resource_dir(name, resource_root=REPO_ROOT)
        for source in packaged.rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = source.relative_to(packaged)
            assert (tmp_path / "agents" / name / relative).read_bytes() == source.read_bytes()
            assert (REPO_ROOT / "agents" / name / relative).read_bytes() == source.read_bytes()
