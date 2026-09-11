from __future__ import annotations

"""``build_engine_command`` must not silently drop a requested third entrant.

``RunConfig`` grew ``c_type``/``c_params`` for the RC2 Phase 4 Advanced
multi-agent roster, and ``app/views/advanced.py`` genuinely populates them
whenever the Agent C slot is visible. ``build_engine_command`` -- the
GUI-independent command builder those configs are meant to flow through --
was never updated to read either field, so a ``RunConfig`` describing a
three-entrant match produced a two-entrant command with no error, no warning,
and a plausible-looking result artifact naming only A and B.

The live Designer path happens to escape this: ``agent_designer.py`` builds
its own command through ``build_designer_match_arguments`` and exports
``BYTEFRAY_AGENT_C_PARAMS_JSON`` itself, so no released GUI run lost an
entrant. ``build_engine_command``'s only in-repo caller was
``EngineRunner._build_engine_cmd``; that class was removed as dead code
(zero instantiations anywhere in the tree) in the V5 Alpha 1 maintenance
pass, leaving ``build_engine_command`` with no in-repo production caller at
all -- it is exercised only directly, as a unit, by the tests below.
That makes this a latent defect rather than a shipped one -- but it is an
exposed helper accepting a field it silently discards, which is exactly the
kind of quiet entrant loss a V5 experiment must never be able to hit.

The tests below pin both halves of the contract: the two-entrant command is
byte-for-byte what it always was, and a third entrant actually survives the
trip into a real match.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from app.services import engine_commands
from app.services.osutil import DefaultPaths

REPO_ROOT = Path(__file__).resolve().parents[2]

V2 = "bytefray-rules-2"

#: A minimal Agent API v1 agent that accepts (and ignores) arbitrary
#: construction params, so a params payload can be routed to it without the
#: agent itself becoming part of what these tests assert.
NOP_SOURCE = b'''
from battle_engine.agent_api import ActionKind, AgentAction


class NopAgent:
    def __init__(self, **params):
        self.params = params

    def reset(self, context):
        return None

    def act(self, observation):
        return AgentAction(ActionKind.NOP)


def create_agent(**params):
    return NopAgent(**params)
'''


def _paths(tmp_path: Path) -> DefaultPaths:
    return DefaultPaths(
        root=REPO_ROOT,
        replay_path=tmp_path / "out" / "replay.jsonl",
        summary_path=tmp_path / "out" / "summary.json",
    )


def _write_agent(agent_dir: Path, agent_id: str) -> None:
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
    agent_dir.joinpath("agent.py").write_bytes(NOP_SOURCE)


def _seed_agents(root: Path, *names: str) -> None:
    for name in names:
        _write_agent(root / "agents" / name, name)


def _c_flag_value(command: list[str]) -> str | None:
    return command[command.index("--c-type") + 1] if "--c-type" in command else None


# ---------------------------------------------------------------------------
# Two entrants: unchanged
# ---------------------------------------------------------------------------


def test_two_entrant_command_and_environment_are_unchanged(tmp_path: Path) -> None:
    """A config with no Agent C produces exactly the pre-fix command and env.

    The third-entrant support must be purely additive: a caller that has
    never heard of ``c_type`` must not be able to tell it exists.
    """

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha",
        b_type="beta",
        ruleset_id=V2,
        arena=256,
        ticks=40,
        seed=99,
        a_params={"byte": 1},
        b_params={"byte": 2},
    )

    command, env = engine_commands.build_engine_command(config, paths)

    # Ordering is part of the contract the pre-existing launcher tests pin,
    # so assert the full option list rather than membership.
    assert command[command.index("--arena"):] == [
        "--arena", "256",
        "--ticks", "40",
        "--win-mode", "score_fallback",
        "--replay", str(paths.replay_path),
        "--a-type", "alpha",
        "--b-type", "beta",
        "--ruleset", V2,
        "--seed", "99",
    ]
    assert "--c-type" not in command
    assert "BYTEFRAY_AGENT_C_PARAMS_JSON" not in env
    assert env["BYTEFRAY_AGENT_A_PARAMS_JSON"] == json.dumps({"byte": 1})
    assert env["BYTEFRAY_AGENT_B_PARAMS_JSON"] == json.dumps({"byte": 2})


@pytest.mark.parametrize("absent", [None, ""])
def test_absent_or_empty_agent_c_is_treated_as_two_entrants(
    tmp_path: Path, absent: str | None
) -> None:
    """An unset *or* empty Agent C selection stays a two-entrant match.

    ``selected_agent_name`` can yield an empty string for a combo with no
    real selection, and the CLI's own ``--c-type`` default is ``""``; both
    must mean "no third entrant" rather than "a third entrant named nothing".
    """

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha", b_type="beta", ruleset_id=V2, c_type=absent
    )

    command, env = engine_commands.build_engine_command(config, paths)

    assert "--c-type" not in command
    assert "BYTEFRAY_AGENT_C_PARAMS_JSON" not in env


def test_orphan_c_params_never_reach_a_two_entrant_match(tmp_path: Path) -> None:
    """C params without a C agent must not be exported.

    Exporting them would hand the child a construction override for a slot
    the match does not contain.
    """

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha", b_type="beta", ruleset_id=V2,
        c_type=None, c_params={"stale": True},
    )

    _command, env = engine_commands.build_engine_command(config, paths)

    assert "BYTEFRAY_AGENT_C_PARAMS_JSON" not in env


# ---------------------------------------------------------------------------
# Three entrants
# ---------------------------------------------------------------------------


def test_third_entrant_without_params_reaches_the_command(tmp_path: Path) -> None:
    """``c_type`` alone is enough to produce a three-entrant command."""

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha", b_type="beta", ruleset_id=V2, c_type="gamma"
    )

    command, env = engine_commands.build_engine_command(config, paths)

    assert _c_flag_value(command) == "gamma"
    # Emitted in the same position build_designer_match_arguments uses.
    assert command.index("--c-type") == command.index("--b-type") + 2
    assert command.index("--c-type") < command.index("--ruleset")
    assert "BYTEFRAY_AGENT_C_PARAMS_JSON" not in env


def test_third_entrant_with_params_reaches_command_and_environment(
    tmp_path: Path,
) -> None:
    """``c_params`` travels in the env var the CLI actually reads."""

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha", b_type="beta", ruleset_id=V2,
        c_type="gamma", c_params={"aggression": 0.5},
    )

    command, env = engine_commands.build_engine_command(config, paths)

    assert _c_flag_value(command) == "gamma"
    assert env["BYTEFRAY_AGENT_C_PARAMS_JSON"] == json.dumps({"aggression": 0.5})


def test_per_entrant_parameters_stay_assigned_to_their_own_entrant(
    tmp_path: Path,
) -> None:
    """A/B/C params must never be crossed between slots.

    Distinct values per slot, so a copy/paste slip between the three env
    exports cannot pass.
    """

    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="alpha", b_type="beta", ruleset_id=V2, c_type="gamma",
        a_params={"slot": "A"},
        b_params={"slot": "B"},
        c_params={"slot": "C"},
    )

    command, env = engine_commands.build_engine_command(config, paths)

    assert env["BYTEFRAY_AGENT_A_PARAMS_JSON"] == json.dumps({"slot": "A"})
    assert env["BYTEFRAY_AGENT_B_PARAMS_JSON"] == json.dumps({"slot": "B"})
    assert env["BYTEFRAY_AGENT_C_PARAMS_JSON"] == json.dumps({"slot": "C"})
    assert command[command.index("--a-type") + 1] == "alpha"
    assert command[command.index("--b-type") + 1] == "beta"
    assert command[command.index("--c-type") + 1] == "gamma"


# ---------------------------------------------------------------------------
# The command actually runs a three-entrant match
# ---------------------------------------------------------------------------


def test_generated_three_entrant_command_produces_a_real_three_entrant_match(
    tmp_path: Path,
) -> None:
    """The end-to-end proof the argument assertions above cannot give.

    ``RunConfig`` -> ``build_engine_command`` -> the exact generated command
    and environment -> a real match -> a real result artifact naming three
    entrants. Before the fix this produced a perfectly valid *two*-entrant
    result, which is precisely why nothing caught it.
    """

    data_root = tmp_path / "data"
    _seed_agents(data_root, "nop_a", "nop_b", "nop_c")
    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="nop_a", b_type="nop_b", c_type="nop_c",
        ruleset_id=V2, arena=512, ticks=20,
        a_params={"slot": "A"}, b_params={"slot": "B"}, c_params={"slot": "C"},
    )

    command, env = engine_commands.build_engine_command(config, paths)
    env = dict(env, BYTEFRAY_ROOT=str(data_root))
    completed = subprocess.run(
        command, cwd=tmp_path, env=dict(os.environ, **env),
        text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr

    envelope = json.loads(paths.replay_path.with_name("result.json").read_text())
    assert {entrant["agent_id"] for entrant in envelope["entrants"]} == {"A", "B", "C"}
    assert [entrant["name"] for entrant in envelope["entrants"]] == [
        "nop_a", "nop_b", "nop_c",
    ]
    # The CLI's own per-slot params echo: proof each payload was resolved
    # against the entrant it was addressed to, not merely that three env
    # vars were set.
    assert " C: nop_c params=" in completed.stdout


def test_generated_two_entrant_command_still_produces_two_entrants(
    tmp_path: Path,
) -> None:
    """The same end-to-end path, with no Agent C, stays a two-entrant match."""

    data_root = tmp_path / "data"
    _seed_agents(data_root, "nop_a", "nop_b")
    paths = _paths(tmp_path)
    config = engine_commands.RunConfig(
        a_type="nop_a", b_type="nop_b", ruleset_id=V2, arena=512, ticks=20
    )

    command, env = engine_commands.build_engine_command(config, paths)
    env = dict(env, BYTEFRAY_ROOT=str(data_root))
    completed = subprocess.run(
        command, cwd=tmp_path, env=dict(os.environ, **env),
        text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr

    envelope = json.loads(paths.replay_path.with_name("result.json").read_text())
    assert {entrant["agent_id"] for entrant in envelope["entrants"]} == {"A", "B"}
    assert " C: " not in completed.stdout
