from __future__ import annotations

"""V5 Alpha 1 Post-Release Hardening H1: parameter resolution and supervised
runtime consistency.

FIND-01: ``tournament_cli``/``agent_test``/``agent_evaluation`` constructed a
Python ``MatchEntrant`` without resolving its agent's declared parameter
schema, so a schema-enabled agent received ``{}`` on every one of those
paths instead of its declared defaults -- unlike an equivalent ``bytefray
run`` invocation, which always resolved them. Fixed by routing every one of
those call sites through the same canonical
``agent_parameters.resolve_entrant_parameters`` boundary ``bytefray run``
already used.

FIND-02: ``supervised_runtime.SupervisedPythonEntrantController`` built its
worker's ``reset`` request without forwarding ``entrant.parameters``, so a
supervised (timeout-bounded) match delivered ``{}`` to the agent even when
``MatchEntrant.parameters`` -- and therefore result/provenance metadata --
was non-empty. Fixed by passing ``parameters=entrant.parameters`` through,
mirroring what ``process_runtime.py``'s own worker branch already did.

See docs/research/v5/V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md for the
full investigation, root-cause analysis, and reachability notes.
"""

import json
from pathlib import Path

import pytest
from _hang_safety import hang_safety_timeout
from battle_engine.agent_evaluation import _expected_cell_match_id
from battle_engine.agent_parameters import (
    EMPTY_PARAMETER_SCHEMA,
    resolve_entrant_parameters,
)
from battle_engine.agent_test import GroupEntrantSpec, _resolve_default_parameters
from battle_engine.agent_test import test_agent as run_development_test
from battle_engine.agent_test import test_agents as run_group_development_test
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant
from battle_engine.supervised_runtime import SupervisedPythonEntrantController
from battle_engine.tournament_cli import _resolve_entrant as resolve_tournament_entrant

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_STARTER = "v5_region_attacker"
SCHEMA_STARTER_DEFAULTS = {"attacker_reach": 16}
OTHER_SCHEMA_STARTER = "v5_scout_striker"


# ---------------------------------------------------------------------------
# FIND-01: entrant parameter resolution parity
# ---------------------------------------------------------------------------


class TestResolveEntrantParametersContract:
    """Unit coverage for the new shared canonical boundary itself."""

    def test_v2_agent_with_no_overrides_resolves_schema_defaults(self) -> None:
        spec = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        resolved = resolve_entrant_parameters(
            api_version=spec.api_version,
            schema=spec.parameter_schema,
            legacy_defaults=spec.defaults,
            path=spec.dir,
        )
        assert resolved == SCHEMA_STARTER_DEFAULTS

    def test_v2_agent_explicit_override_beats_defaults(self) -> None:
        spec = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        resolved = resolve_entrant_parameters(
            api_version=spec.api_version,
            schema=spec.parameter_schema,
            legacy_defaults=spec.defaults,
            overrides={"attacker_reach": 32},
            path=spec.dir,
        )
        assert resolved == {"attacker_reach": 32}

    def test_v2_agent_preset_resolves_through_the_canonical_resolver(self) -> None:
        spec = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        resolved = resolve_entrant_parameters(
            api_version=spec.api_version,
            schema=spec.parameter_schema,
            legacy_defaults=spec.defaults,
            preset="far_sighted",
            path=spec.dir,
        )
        assert resolved == {"attacker_reach": 32}

    @pytest.mark.parametrize("api_version", [1, None, 3])
    def test_non_v2_agent_never_receives_resolved_parameters(self, api_version) -> None:
        # Mirrors the pre-Phase-D/pre-H1 compatibility rule: parameters are
        # an Agent API v2-only concept. A caller passing free-form overrides
        # for a non-v2 agent still gets {} -- it is that caller's own job to
        # warn its user the value was ignored (see cli.py's identical gate).
        resolved = resolve_entrant_parameters(
            api_version=api_version,
            schema=EMPTY_PARAMETER_SCHEMA,
            legacy_defaults={"byte": 4},
            overrides={"byte": 9},
        )
        assert resolved == {}

    def test_schemaless_v2_agent_falls_back_to_legacy_defaults_and_overrides(self) -> None:
        # A v4_* starter: api_version 2, but EMPTY_PARAMETER_SCHEMA. Must
        # keep exactly the pre-Phase-D free-form passthrough.
        resolved = resolve_entrant_parameters(
            api_version=2,
            schema=EMPTY_PARAMETER_SCHEMA,
            legacy_defaults={"byte": 4},
            overrides={"byte": 9},
        )
        assert resolved == {"byte": 9}


class TestTournamentEntrantResolution:
    def test_resolves_schema_defaults_like_bytefray_run(self) -> None:
        entrant = resolve_tournament_entrant(REPO_ROOT, SCHEMA_STARTER, start=64)
        assert dict(entrant.parameters) == SCHEMA_STARTER_DEFAULTS

    def test_schemaless_v4_starter_still_resolves_empty(self) -> None:
        # v4_* starters declare no `parameters` section -- must stay {} so
        # every historical tournament match_id is unaffected.
        entrant = resolve_tournament_entrant(REPO_ROOT, "v4_local_defender", start=64)
        assert dict(entrant.parameters) == {}

    def test_tournament_own_identity_is_now_sensitive_to_resolved_parameters(self) -> None:
        """Isolates the parameter effect from tournament's own (legitimate,
        pre-existing) agent-id-as-name identity convention, which by itself
        already makes a tournament match_id differ from an equivalent
        `bytefray run` match_id regardless of parameters -- see the H1
        report's FIND-01 root-cause section for why comparing raw
        `bytefray run` vs. `bytefray tournament` match_ids directly
        conflates two independent effects.
        """
        from battle_engine.config import Config as _Config
        from battle_engine.match_service import MatchRequest, canonical_match_id

        spec = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        resolved_entrant = resolve_tournament_entrant(REPO_ROOT, SCHEMA_STARTER, start=64)
        empty_entrant = MatchEntrant.python(
            SCHEMA_STARTER, resolved_entrant.name, 64, spec, {}
        )
        opponent = resolve_tournament_entrant(REPO_ROOT, OTHER_SCHEMA_STARTER, start=200)

        def match_id_for(entrant: MatchEntrant) -> str:
            request = MatchRequest(
                config=_Config(seed=42),
                entrants=(entrant, opponent),
                max_ticks=140,
                replay_path=Path("."),
                ruleset_id="bytefray-rules-4",
            )
            return canonical_match_id(request)

        assert match_id_for(resolved_entrant) != match_id_for(empty_entrant)

    def test_seeded_placement_reassignment_preserves_resolved_parameters(self) -> None:
        """FIND-01 sibling, discovered by an exhaustive audit of every
        ``MatchEntrant`` construction site rather than reported by the
        audit: ``TournamentService._placed_pair`` re-derives a fresh
        ``MatchEntrant`` for every "seeded" core-placement Ruleset -- which
        includes ``bytefray-rules-4``, the *permanent, default* identity an
        Agent API v2 roster resolves to -- and, before this fix, built the
        replacement without carrying ``.parameters`` forward, silently
        reintroducing ``{}`` for every real tournament match.
        """
        from dataclasses import dataclass

        from battle_engine.tournament_service import TournamentService

        @dataclass
        class _FakeRequest:
            ruleset_id: str
            config: Config

        entrant_a = resolve_tournament_entrant(REPO_ROOT, SCHEMA_STARTER, start=0)
        entrant_b = resolve_tournament_entrant(REPO_ROOT, OTHER_SCHEMA_STARTER, start=100)
        assert dict(entrant_a.parameters) == SCHEMA_STARTER_DEFAULTS  # precondition

        request = _FakeRequest(ruleset_id="bytefray-rules-4", config=Config(seed=42))
        placed_a, placed_b = TournamentService._placed_pair(request, entrant_a, entrant_b, 999)

        assert dict(placed_a.parameters) == dict(entrant_a.parameters)
        assert dict(placed_b.parameters) == dict(entrant_b.parameters)
        # The whole point of _placed_pair: starts still get re-derived from
        # the match seed, so this is a genuine replacement, not a no-op.
        assert placed_a.start != entrant_a.start or placed_b.start != entrant_b.start


class TestAgentTestEntrantResolution:
    def test_single_match_delivers_schema_defaults_to_both_slots(self, tmp_path: Path) -> None:
        outcome = run_development_test(
            SCHEMA_STARTER,
            opponent=OTHER_SCHEMA_STARTER,
            seed=42,
            ticks=20,
            data_root=REPO_ROOT,
            ruleset_id="bytefray-rules-4",
            run_dir=tmp_path / "run",
        )
        metadata_by_agent = {
            agent.agent_id: dict(agent.metadata) for agent in outcome.match_result.agents
        }
        assert metadata_by_agent["A"].get("parameters") == SCHEMA_STARTER_DEFAULTS
        assert metadata_by_agent["B"].get("parameters") == {
            "contact_memory_ticks": 60,
            "search_stride_divisor": 1,
        }

    def test_group_match_delivers_schema_defaults_to_every_seat(self, tmp_path: Path) -> None:
        entrants = [
            GroupEntrantSpec(seat="A", agent_id=SCHEMA_STARTER, start=64),
            GroupEntrantSpec(seat="B", agent_id=OTHER_SCHEMA_STARTER, start=200),
        ]
        outcome = run_group_development_test(
            entrants,
            seed=42,
            ticks=20,
            data_root=REPO_ROOT,
            ruleset_id="bytefray-rules-4",
            run_dir=tmp_path / "run",
        )
        metadata_by_agent = {
            agent.agent_id: dict(agent.metadata) for agent in outcome.match_result.agents
        }
        assert metadata_by_agent["A"].get("parameters") == SCHEMA_STARTER_DEFAULTS

    def test_identity_matches_an_equivalent_bare_run_invocation(self, tmp_path: Path) -> None:
        """`agents test` shares `bytefray run`'s own A/B slot-label identity
        convention (unlike `bytefray tournament`'s agent-name convention),
        so this is a genuine like-for-like canonical_match_id comparison.
        """
        from battle_engine.config import Config as _Config
        from battle_engine.match_service import MatchRequest, canonical_match_id

        outcome = run_development_test(
            SCHEMA_STARTER,
            opponent=OTHER_SCHEMA_STARTER,
            seed=42,
            ticks=20,
            data_root=REPO_ROOT,
            ruleset_id="bytefray-rules-4",
            run_dir=tmp_path / "run",
            agent_start=64,
            opponent_start=200,
        )

        spec_a = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        spec_b = resolve_agent(REPO_ROOT, OTHER_SCHEMA_STARTER)
        equivalent_request = MatchRequest(
            config=_Config(seed=42),
            entrants=(
                MatchEntrant.python(
                    "A", SCHEMA_STARTER, 64, spec_a,
                    _resolve_default_parameters(spec_a, role="a"),
                ),
                MatchEntrant.python(
                    "B", OTHER_SCHEMA_STARTER, 200, spec_b,
                    _resolve_default_parameters(spec_b, role="b"),
                ),
            ),
            max_ticks=20,
            replay_path=Path("."),
            ruleset_id="bytefray-rules-4",
        )
        assert outcome.match_result.match_id == canonical_match_id(equivalent_request)


class TestAgentEvaluationExpectedMatchIdMirrorsAgentTest:
    """The most important FIND-01 regression: `_expected_cell_match_id` must
    never drift from what `agent_test.test_agent` (the real per-cell
    executor) actually produces, or every schema-enabled resumed cell would
    register a false `resumed_result_mismatch`.
    """

    def test_pairwise_expected_id_matches_a_real_test_agent_run(self, tmp_path: Path) -> None:
        outcome = run_development_test(
            SCHEMA_STARTER,
            opponent=OTHER_SCHEMA_STARTER,
            seed=42,
            ticks=20,
            data_root=REPO_ROOT,
            ruleset_id="bytefray-rules-4",
            run_dir=tmp_path / "run",
            agent_start=64,
            opponent_start=200,
        )
        spec_a = resolve_agent(REPO_ROOT, SCHEMA_STARTER)
        spec_b = resolve_agent(REPO_ROOT, OTHER_SCHEMA_STARTER)
        expected = _expected_cell_match_id(
            subject_spec=spec_a,
            subject_id=SCHEMA_STARTER,
            opponent_spec=spec_b,
            opponent_id=OTHER_SCHEMA_STARTER,
            seed=42,
            ticks=20,
            orientation="candidate_first",
            ruleset_id="bytefray-rules-4",
            subject_start=64,
            opponent_start=200,
        )
        assert expected == outcome.match_result.match_id


# ---------------------------------------------------------------------------
# FIND-02: supervised runtime parameter delivery
# ---------------------------------------------------------------------------

_PROBE_AGENT_YAML = json.dumps(
    {
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "version": "1.0",
    }
)


def _write_probe_agent(root: Path, name: str, output_path: Path) -> None:
    """A minimal Agent API v2 agent that records what its own ``reset()``
    actually received on ``MatchContextV2.parameters`` -- the exact
    delivery boundary FIND-02 is about.

    Never calls ``act()`` beyond a bare v1-vocabulary ``NOP``:
    ``SupervisedPythonEntrantController``'s tick loop is a pre-existing,
    unmodified-by-H1 Agent-API-v1-shaped loop (it never calls
    ``declare_processes`` and, confirmed separately, crashes its worker
    with ``agent_worker_exited`` the moment a declared-v2 agent's
    ``act()`` is invoked at all -- even to return a bare NOP). That is a
    pre-existing structural fact about this controller's real-v2-gameplay
    support, unrelated to FIND-02's "forward parameters into reset" scope,
    so these tests stay at the ``reset()`` boundary and never call
    ``controller.run(...)``.
    """

    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(_PROBE_AGENT_YAML, encoding="utf-8")
    (directory / "agent.py").write_text(
        f'''
import json
from pathlib import Path
from battle_engine.agent_api import ProcessDeclaration

OUTPUT_PATH = Path(r"{output_path}")

class ParamProbeAgent:
    def reset(self, context):
        OUTPUT_PATH.write_text(json.dumps(dict(context.parameters)))

    def declare_processes(self):
        return [ProcessDeclaration(id="p", reach=1, share=1.0)]

    def act(self, observation):
        raise AssertionError("act() must never be called by these reset-boundary tests")

def create_agent():
    return ParamProbeAgent()
''',
        encoding="utf-8",
    )


def _passive_v1_entrant(root: Path, name: str, start: int) -> MatchEntrant:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(
        json.dumps(
            {"kind": "python", "api_version": 1, "entrypoint": "agent.py:create_agent", "version": "1.0"}
        ),
        encoding="utf-8",
    )
    (directory / "agent.py").write_text(
        """
from battle_engine.agent_api import ActionKind, AgentAction
class Agent:
    def reset(self, context): pass
    def act(self, observation): return AgentAction(ActionKind.NOP)
def create_agent(): return Agent()
""",
        encoding="utf-8",
    )
    spec = resolve_agent(root, name)
    return MatchEntrant.python(name, name, start, spec)


class TestSupervisedRuntimeParameterForwarding:
    def test_schema_default_parameters_reach_the_worker(self, tmp_path: Path) -> None:
        output_path = tmp_path / "probe_output.json"
        _write_probe_agent(tmp_path, "probe", output_path)
        spec = resolve_agent(tmp_path, "probe")
        entrant = MatchEntrant.python(
            "A", "probe", 0, spec, {"inspections_per_tick": 4}
        )
        passive = _passive_v1_entrant(tmp_path, "passive", 32)

        controller = None
        with hang_safety_timeout(30):
            try:
                controller = SupervisedPythonEntrantController(
                    Config(seed=1337), (entrant, passive), max_ticks=1, agent_call_timeout=10.0
                )
            finally:
                if controller is not None:
                    controller._close_all_handles()

        delivered = json.loads(output_path.read_text())
        assert delivered == {"inspections_per_tick": 4}

    def test_explicit_override_parameters_reach_the_worker(self, tmp_path: Path) -> None:
        output_path = tmp_path / "probe_output.json"
        _write_probe_agent(tmp_path, "probe", output_path)
        spec = resolve_agent(tmp_path, "probe")
        entrant = MatchEntrant.python(
            "A", "probe", 0, spec, {"inspections_per_tick": 0, "extra": "value"}
        )
        passive = _passive_v1_entrant(tmp_path, "passive", 32)

        controller = None
        with hang_safety_timeout(30):
            try:
                controller = SupervisedPythonEntrantController(
                    Config(seed=1337), (entrant, passive), max_ticks=1, agent_call_timeout=10.0
                )
            finally:
                if controller is not None:
                    controller._close_all_handles()

        delivered = json.loads(output_path.read_text())
        assert delivered == {"inspections_per_tick": 0, "extra": "value"}

    def test_direct_and_supervised_v4_worker_agree_and_respond_to_overrides(
        self, tmp_path: Path
    ) -> None:
        """Real production behavioral evidence, not just an object
        inspected before worker execution: v5_core_defender's
        ``inspections_per_tick=0`` override must suppress every READ
        action it would otherwise issue every tick (docs/research/v5/
        V5_ALPHA1_PHASE_D_AUTHORING_AND_PARAMETERS.md Sec J), identically
        whether the match runs fully in-process or through a timeout-
        bounded worker subprocess.

        Uses ``process_runtime.ProcessMatchController``'s own worker
        branch (``agent_call_timeout`` under the V4 Ruleset) rather than
        ``supervised_runtime.SupervisedPythonEntrantController`` directly:
        this is the actually-reachable supervised path for a real,
        schema-enabled starter -- see this module's reachability notes.
        ``SupervisedPythonEntrantController``'s own tick loop is Agent-
        API-v1-only in practice (confirmed separately: even a bare NOP
        from a declared-v2 agent crashes its worker with
        ``agent_worker_exited`` the moment ``act()`` is called), a
        pre-existing structural gap unrelated to FIND-02's "forward
        parameters into reset" scope, so it cannot run this probe.
        """
        from battle_engine.match_service import MatchRequest, NativeMatchService

        spec_defender = resolve_agent(REPO_ROOT, "v5_core_defender")
        spec_opponent = resolve_agent(REPO_ROOT, OTHER_SCHEMA_STARTER)

        def read_count(*, agent_call_timeout: float | None, inspections_per_tick: int) -> int:
            overridden = resolve_entrant_parameters(
                api_version=spec_defender.api_version,
                schema=spec_defender.parameter_schema,
                legacy_defaults=spec_defender.defaults,
                overrides={"inspections_per_tick": inspections_per_tick},
                path=spec_defender.dir,
            )
            defender = MatchEntrant.python(
                "A", "v5_core_defender", 64, spec_defender, overridden
            )
            opponent = MatchEntrant.python(
                "B",
                OTHER_SCHEMA_STARTER,
                200,
                spec_opponent,
                _resolve_default_parameters(spec_opponent, role="b"),
            )
            replay_path = tmp_path / f"replay-{agent_call_timeout}-{inspections_per_tick}.jsonl"
            trace_path = tmp_path / f"trace-{agent_call_timeout}-{inspections_per_tick}.jsonl"
            request = MatchRequest(
                config=Config(seed=42),
                entrants=(defender, opponent),
                max_ticks=15,
                replay_path=replay_path,
                trace_path=trace_path,
                ruleset_id="bytefray-rules-4",
                agent_call_timeout=agent_call_timeout,
                verbose=False,
            )
            with hang_safety_timeout(60):
                NativeMatchService().run(request)
            reads = 0
            for line in trace_path.read_text().splitlines():
                record = json.loads(line)
                if (
                    record.get("record_type") == "decision_v2"
                    and record.get("agent_id") == "A"
                    and (record.get("action") or {}).get("kind") == "read"
                ):
                    reads += 1
            return reads

        direct_default = read_count(agent_call_timeout=None, inspections_per_tick=4)
        direct_zero = read_count(agent_call_timeout=None, inspections_per_tick=0)
        supervised_default = read_count(agent_call_timeout=10.0, inspections_per_tick=4)
        supervised_zero = read_count(agent_call_timeout=10.0, inspections_per_tick=0)

        assert direct_default > 0
        assert direct_zero == 0
        assert supervised_default > 0
        assert supervised_zero == 0
        assert direct_default == supervised_default

    def test_v4_process_worker_provenance_matches_delivered_parameters(
        self, tmp_path: Path
    ) -> None:
        """Sibling regression on the path that is actually reachable in
        production for a schema-enabled agent: an Agent API v2 roster
        always resolves to a V4-family Ruleset (``supports_agent`` rejects
        API v2 under every other permanent identity), so
        ``--agent-call-timeout``/Agent Lab for a real V5 starter always
        executes through ``process_runtime.ProcessMatchController``'s own
        worker branch, not ``supervised_runtime.
        SupervisedPythonEntrantController`` -- see the H1 report's
        reachability analysis. That branch was already correct; this
        confirms the H1 changes did not disturb it, and that result.json's
        provenance agrees with what the agent actually received.
        """
        outcome = run_development_test(
            SCHEMA_STARTER,
            opponent=OTHER_SCHEMA_STARTER,
            seed=42,
            ticks=5,
            timeout=10.0,
            data_root=REPO_ROOT,
            ruleset_id="bytefray-rules-4",
            run_dir=tmp_path / "run",
            agent_start=64,
            opponent_start=200,
        )
        metadata_by_agent = {
            agent.agent_id: dict(agent.metadata) for agent in outcome.match_result.agents
        }
        assert metadata_by_agent["A"].get("parameters") == SCHEMA_STARTER_DEFAULTS
