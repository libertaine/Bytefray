from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _pythonpath() -> str:
    paths = [ROOT / "engine" / "src", ROOT / "client" / "src", ROOT]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        paths.append(Path(existing))
    return os.pathsep.join(map(str, paths))


def _run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=_pythonpath())
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_python_agent(root: Path, name: str, *, api_version: int) -> None:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(
        json.dumps(
            {
                "kind": "python",
                "api_version": api_version,
                "entrypoint": "agent.py:create_agent",
                "name": name,
                "version": "1.0",
            }
        ),
        encoding="utf-8",
    )
    (directory / "agent.py").write_text(
        "from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration\n"
        "class Agent:\n"
        "    def reset(self, context): pass\n"
        "    def declare_processes(self): return [ProcessDeclaration('main', 1, 1.0)]\n"
        "    def act(self, observation): return AgentAction(ActionKindV2.READ, 0)\n"
        "def create_agent(): return Agent()\n",
        encoding="utf-8",
    )


def _scaffold(root: Path, name: str) -> None:
    from battle_engine.agent_scaffold import create_agent

    create_agent(name, data_root=root, resource_root=ROOT, api_version=2)


def test_engine_cli_starts_and_displays_current_help():
    result = _run("-m", "battle_engine.cli", "--help")
    assert result.returncode == 0
    assert "usage: bytefray run" in result.stdout
    assert "--list-agents" in result.stdout
    assert "--quota" in result.stdout
    assert "--ruleset {bytefray-rules-4}" in result.stdout
    for retired_surface in (
        "--mode",
        "redcode94",
        "--red-a",
        "--red-b",
        "--core-size",
        "--max-cycles",
        "--max-processes",
        "--max-len",
        "--min-dist",
        "--rounds",
        "bytefray-rules-1",
        "bytefray-rules-2",
        "bytefray-rules-4-alpha1",
        "bytefray-rules-4-alpha2",
    ):
        assert retired_surface not in result.stdout


def test_cli_creates_current_replay_and_summary_json(tmp_path):
    replay = tmp_path / "match" / "replay.jsonl"
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ticks",
        "3",
        "--arena",
        "128",
        "--seed",
        "7",
        "--a-type",
        "v4_claimer",
        "--b-type",
        "v4_scout",
        "--b-start",
        "64",
        "--replay",
        str(replay),
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for line in replay.read_text().splitlines()]
    summary = json.loads((replay.parent / "summary.json").read_text())
    canonical = json.loads((replay.parent / "result.json").read_text())
    assert records[0]["schema"] == "battle2.replay"
    assert records[0]["schema_version"] == 4
    assert records[0]["record_type"] == "header"
    assert records[0]["ruleset_id"] == "bytefray-rules-4"
    assert records[-1]["record_type"] == "result"
    assert canonical["schema"] == "battle2.result"
    assert canonical["ruleset_id"] == "bytefray-rules-4"
    assert canonical["replay"]["sha256"]
    assert summary["version"] == 2
    assert summary["mode"] == "b2"
    assert summary["seed"] == 7
    assert summary["params"]["ticks_requested"] == 3
    assert summary["agents"] == {"A": "v4_claimer", "B": "v4_scout"}
    assert set(summary["score"]) == {"A", "B"}


def test_run_omitted_ruleset_resolves_current_v4_for_api_v2_agents(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    _scaffold(tmp_path, "v2_alpha")
    _scaffold(tmp_path, "v2_beta")
    replay = tmp_path / "match" / "replay.jsonl"
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ticks",
        "5",
        "--arena",
        "128",
        "--seed",
        "7",
        "--a-type",
        "v2_alpha",
        "--b-type",
        "v2_beta",
        "--b-start",
        "64",
        "--replay",
        str(replay),
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    canonical = json.loads((replay.parent / "result.json").read_text())
    assert canonical["ruleset_id"] == "bytefray-rules-4"


def test_run_omitted_ruleset_rejects_api_v1_without_artifacts(tmp_path, monkeypatch):
    """API-v1 package metadata stays readable, but it cannot execute."""

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    _write_python_agent(tmp_path, "v1_alpha", api_version=1)
    _write_python_agent(tmp_path, "v1_beta", api_version=1)
    replay = tmp_path / "match" / "replay.jsonl"
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ticks",
        "3",
        "--arena",
        "128",
        "--a-type",
        "v1_alpha",
        "--b-type",
        "v1_beta",
        "--b-start",
        "64",
        "--replay",
        str(replay),
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert result.stderr.startswith("ERROR:")
    assert "No Bytefray Ruleset supports" in result.stderr
    assert "Traceback" not in result.stderr
    assert not replay.exists()
    assert not (replay.parent / "result.json").exists()


@pytest.mark.parametrize(
    "retired_id",
    (
        "bytefray-rules-1",
        "bytefray-rules-2",
        "bytefray-rules-4-alpha1",
        "bytefray-rules-4-alpha2",
    ),
)
def test_retired_ruleset_flags_fail_at_argument_parsing(tmp_path, retired_id):
    replay = tmp_path / retired_id / "replay.jsonl"
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ruleset",
        retired_id,
        "--replay",
        str(replay),
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert "Traceback" not in result.stderr
    assert not replay.exists()


def test_ruleset_flag_explicit_v4_python_succeeds(tmp_path, monkeypatch):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    _write_python_agent(tmp_path, "alpha_agent", api_version=2)
    _write_python_agent(tmp_path, "beta_agent", api_version=2)
    replay = tmp_path / "match" / "replay.jsonl"
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ticks",
        "3",
        "--arena",
        "128",
        "--seed",
        "7",
        "--a-type",
        "alpha_agent",
        "--b-type",
        "beta_agent",
        "--b-start",
        "64",
        "--ruleset",
        "bytefray-rules-4",
        "--replay",
        str(replay),
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    canonical = json.loads((replay.parent / "result.json").read_text())
    assert canonical["ruleset_id"] == "bytefray-rules-4"


def test_ruleset_flag_unknown_value_fails_closed(tmp_path):
    result = _run(
        "-m",
        "battle_engine.cli",
        "--ruleset",
        "bytefray-rules-99",
        "--quiet",
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_run_help_documents_the_trace_flag():
    result = _run("-m", "battle_engine.cli", "--help")
    assert result.returncode == 0
    assert "--trace TRACE" in result.stdout


def test_trace_flag_accepts_an_explicit_path():
    from battle_engine.cli import parse_args

    args = parse_args(["--trace", "/tmp/example-trace.jsonl"])
    assert args.trace == "/tmp/example-trace.jsonl"


def test_trace_flag_omitted_is_none_in_parsed_arguments():
    from battle_engine.cli import parse_args

    args = parse_args(["--a-type", "v4_claimer", "--b-type", "v4_scout"])
    assert args.trace is None
