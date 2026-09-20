from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction
from battle_engine.agent_scaffold import create_agent as scaffold_create_agent
from battle_engine.agent_validation import (
    VALIDATION_AGENT_ID,
    AgentValidationFailedError,
    ValidationResult,
    build_validation_context,
    main,
    validate_agent,
)
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.python_runtime import PythonEntrantInitializationError

ROOT = Path(__file__).resolve().parents[2]

# V6 Phase 2B.12 retired Agent API v1 execution
# (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): every
# fixture agent in this file is now Agent API v2 (reset/declare_processes/
# act), and ``_write_agent``'s default manifest declares ``api_version: 2``
# to match ``agent_scaffold.DEFAULT_API_VERSION``'s own new default. A
# dedicated test below (``test_api_v1_agent_is_rejected_before_any_code_runs``)
# pins the new Stage-2 rejection of an Agent API v1 agent explicitly.
VALID_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, 0)

def create_agent():
    return Agent()
"""

INVALID_ACTION_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.WRITE, "not-an-int", 1)

def create_agent():
    return Agent()
"""

BROKEN_RESET_SOURCE = """
class Agent:
    def reset(self, context):
        raise RuntimeError("reset boom")

    def declare_processes(self):
        return []

    def act(self, observation):
        return None

def create_agent():
    return Agent()
"""

SPY_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.seen_context = context

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        self.seen_observation = observation
        return AgentAction(ActionKindV2.READ, 0)

def create_agent():
    return Agent()
"""

# Retained verbatim: Agent API v1 is inspectable/discoverable but no longer
# validatable (validate_agent rejects it at Stage 2) or executable.
V1_SOURCE = """
from battle_engine.agent_api import ActionKind, AgentAction

class Agent:
    def reset(self, context):
        pass

    def act(self, observation):
        return AgentAction(ActionKind.NOP)

def create_agent():
    return Agent()
"""


def _write_agent(
    root: Path,
    name: str,
    *,
    manifest: dict[str, object] | None = None,
    source: str | None = VALID_SOURCE,
) -> Path:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    values: dict[str, object] = {
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "version": "1.0",
    }
    if manifest:
        values.update(manifest)
    (directory / "agent.yaml").write_text(json.dumps(values), encoding="utf-8")
    if source is not None:
        (directory / "agent.py").write_text(source, encoding="utf-8")
    return directory


def _run(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None):
    full_env = dict(os.environ) if env is None else env
    full_env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "engine" / "src"), str(ROOT / "client" / "src"), str(ROOT)]
    )
    return subprocess.run(
        [sys.executable, "-m", "battle_engine", *args],
        cwd=cwd,
        env=full_env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("timeout", [None, 5.0])
def test_agent_api_v2_validation_consumes_declarations_and_observation_v2(
    tmp_path: Path, timeout: float | None
) -> None:
    _write_agent(tmp_path, "v2_agent", source=VALID_SOURCE)

    result = validate_agent("v2_agent", data_root=tmp_path, timeout=timeout)

    assert result.api_version == 2
    assert result.dry_run_action.kind.value == "read"
    assert result.dry_run_action.operand == 0


def test_api_v1_agent_is_rejected_before_any_code_runs(tmp_path: Path) -> None:
    """V6 Phase 2B.12 retired Agent API v1 execution
    (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): a dry run
    genuinely executes the agent's reset()/act(), so validating a v1 agent
    would be running code no Ruleset can execute for real. Rejected at
    Stage 2 (discovery), before ``load_python_agent`` ever imports it.
    """

    _write_agent(tmp_path, "v1_agent", manifest={"api_version": 1}, source=V1_SOURCE)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("v1_agent", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_api_version_unsupported"
    assert caught.value.diagnostic.stage == "discovery"


# --------------------------------------------------------------------------
# Successful validation
# --------------------------------------------------------------------------


def test_scaffolded_agent_validates_successfully(tmp_path):
    scaffold_create_agent("example", data_root=tmp_path, resource_root=ROOT)

    result = validate_agent("example", data_root=tmp_path)

    assert isinstance(result, ValidationResult)
    assert result.agent_id == "example"
    assert result.api_version == 2
    assert result.dry_run_action.kind == ActionKindV2.WRITE
    assert result.dry_run_action.operand == 0
    assert result.dry_run_action.value == 0xA5


def test_custom_valid_agent_validates(tmp_path):
    _write_agent(tmp_path, "example")

    result = validate_agent("example", data_root=tmp_path)

    assert result.api_version == 2
    assert result.dry_run_action == AgentAction(ActionKindV2.READ, 0)


def test_dry_run_result_is_deterministic(tmp_path):
    scaffold_create_agent("example", data_root=tmp_path, resource_root=ROOT)

    first = validate_agent("example", data_root=tmp_path)
    second = validate_agent("example", data_root=tmp_path)

    assert first.dry_run_action == second.dry_run_action


def test_validation_context_uses_real_match_slot_identity_not_discovery_id(tmp_path):
    """The fixture must resemble a real entrant's actual environment: real
    matches only ever pass the slot letter ("A") to an agent's own
    reset()/act(), never its discovery id -- see docs/specs/
    agent_validation.md §7. A distinctively-named agent proves the
    discovery id is not leaking into MatchContextV2/ObservationV2.agent_id.
    """

    _write_agent(tmp_path, "totally_distinct_discovery_id", source=SPY_SOURCE)

    result = validate_agent("totally_distinct_discovery_id", data_root=tmp_path)

    assert result.agent_id == "totally_distinct_discovery_id"
    assert VALIDATION_AGENT_ID == "A"
    context = build_validation_context(2)
    assert context.agent_id == "A"
    assert context.agent_id != "totally_distinct_discovery_id"


# --------------------------------------------------------------------------
# Discovery / kind failures
# --------------------------------------------------------------------------


def test_unknown_agent(tmp_path):
    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("does_not_exist", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_unknown"
    assert caught.value.diagnostic.stage == "discovery"


def test_builtin_kind_is_unsupported(tmp_path):
    directory = tmp_path / "agents" / "runner"
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text('{"name":"runner","defaults":{}}', encoding="utf-8")

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("runner", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_kind_unsupported"
    assert caught.value.diagnostic.stage == "discovery"
    assert "builtin" in caught.value.diagnostic.message


def test_blob_kind_is_unsupported(tmp_path):
    directory = tmp_path / "agents" / "custom_blob"
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text('{"name":"custom_blob"}', encoding="utf-8")
    (directory / "model.blob").write_bytes(b"blob")

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("custom_blob", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_kind_unsupported"
    assert caught.value.diagnostic.stage == "discovery"
    assert "blob" in caught.value.diagnostic.message


def test_malformed_manifest_fails_at_discovery(tmp_path):
    _write_agent(tmp_path, "broken", manifest={"api_version": "1"})

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("broken", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_manifest_invalid"
    assert caught.value.diagnostic.stage == "discovery"


# --------------------------------------------------------------------------
# Load-stage failures (one indivisible call to load_python_agent)
# --------------------------------------------------------------------------


def test_unsupported_api_version(tmp_path):
    _write_agent(tmp_path, "example", manifest={"api_version": 3})

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_api_version_unsupported"
    # V6 Phase 2B.12 rejects any non-2 declared version at Stage 2
    # (discovery), before this file's own load-stage guard would have
    # fired for a version SUPPORTED_AGENT_API_VERSIONS never contained.
    assert caught.value.diagnostic.stage == "discovery"


def test_missing_source_file(tmp_path):
    _write_agent(tmp_path, "example", source=None)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_source_invalid"
    assert caught.value.diagnostic.stage == "load"


def test_import_failure_syntax_error(tmp_path):
    _write_agent(tmp_path, "example", source="def create_agent(:\n    pass\n")

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_import_failed"
    assert caught.value.diagnostic.stage == "load"
    assert "SyntaxError" in caught.value.diagnostic.message


def test_missing_factory(tmp_path):
    _write_agent(tmp_path, "example", source="VALUE = 1\n")

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_factory_failed"
    assert caught.value.diagnostic.stage == "load"


def test_factory_exception(tmp_path):
    _write_agent(
        tmp_path,
        "example",
        source="def create_agent():\n    raise LookupError('factory exploded')\n",
    )

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_factory_failed"
    assert caught.value.diagnostic.stage == "load"


def test_contract_violation_missing_lifecycle_methods(tmp_path):
    _write_agent(tmp_path, "example", source="def create_agent():\n    return object()\n")

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_contract_invalid"
    assert caught.value.diagnostic.stage == "load"


# --------------------------------------------------------------------------
# Reset-stage failure
# --------------------------------------------------------------------------


def test_reset_exception(tmp_path):
    _write_agent(tmp_path, "example", source=BROKEN_RESET_SOURCE)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    diagnostic = caught.value.diagnostic
    assert diagnostic.code == "agent_reset_failed"
    assert diagnostic.stage == "reset"
    assert diagnostic.exception_type == "RuntimeError"
    assert "RuntimeError: reset boom" in diagnostic.message
    assert "Traceback" not in diagnostic.message


# --------------------------------------------------------------------------
# Act-stage failures
# --------------------------------------------------------------------------


def test_act_exception(tmp_path):
    _write_agent(
        tmp_path,
        "example",
        source=(
            "from battle_engine.agent_api import ProcessDeclaration\n"
            "class Agent:\n"
            "    def reset(self, context): pass\n"
            "    def declare_processes(self): return [ProcessDeclaration('main', 1, 1.0)]\n"
            "    def act(self, observation): raise ValueError('act boom')\n"
            "def create_agent(): return Agent()\n"
        ),
    )

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_action_failed"
    assert caught.value.diagnostic.stage == "action"


@pytest.mark.parametrize(
    "body",
    [
        "return object()",
        "return AgentAction('future')",
        "return AgentAction(ActionKindV2.WRITE, 'bad', 1)",
        "return AgentAction(ActionKindV2.READ, 1, 2)",
    ],
)
def test_invalid_returned_action(tmp_path, body):
    source = (
        "from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration\n"
        "class Agent:\n"
        "    def reset(self, context): pass\n"
        "    def declare_processes(self): return [ProcessDeclaration('main', 1, 1.0)]\n"
        f"    def act(self, observation): {body}\n"
        "def create_agent(): return Agent()\n"
    )
    _write_agent(tmp_path, "example", source=source)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    assert caught.value.diagnostic.code == "agent_action_invalid"
    assert caught.value.diagnostic.stage == "action"


# --------------------------------------------------------------------------
# Equivalence with real runtime execution -- the load-bearing tests
# --------------------------------------------------------------------------


def test_reset_failure_diagnostic_matches_real_match_exactly(tmp_path):
    _write_agent(tmp_path, "example", source=BROKEN_RESET_SOURCE)

    validation_diagnostic = None
    try:
        validate_agent("example", data_root=tmp_path)
    except AgentValidationFailedError as exc:
        validation_diagnostic = exc.diagnostic
    assert validation_diagnostic is not None

    spec = resolve_agent(tmp_path, "example")
    entrant = MatchEntrant.python("A", "example", 0, spec)
    with pytest.raises(PythonEntrantInitializationError) as caught:
        ProcessMatchController.from_python_entrants(
            Config(arena_size=64, instr_per_tick=8), (entrant,), 1
        )
    real_diagnostic = caught.value.diagnostic

    assert real_diagnostic == validation_diagnostic


# --------------------------------------------------------------------------
# Supervised (--timeout) hang containment
# --------------------------------------------------------------------------


def test_default_call_stays_unsupervised(tmp_path):
    """validate_agent()'s own default (timeout=None) must remain exactly
    the v0.4.0 in-process, untimed call -- every caller above already
    depends on this; a hang here would hang the whole test suite with no
    external safety net, which is itself evidence the default is
    unsupervised (see docs/specs/agent_lab.md §7)."""

    _write_agent(tmp_path, "example", source=VALID_SOURCE)

    result = validate_agent("example", data_root=tmp_path)

    assert result.agent_id == "example"


def test_supervised_act_timeout_is_reported(tmp_path):
    from _hang_safety import hang_safety_timeout

    _write_agent(
        tmp_path,
        "hangy",
        source=(
            "from battle_engine.agent_api import ProcessDeclaration\n"
            "class Agent:\n"
            "    def reset(self, context): pass\n"
            "    def declare_processes(self): return [ProcessDeclaration('main', 1, 1.0)]\n"
            "    def act(self, observation):\n"
            "        while True:\n"
            "            pass\n"
            "def create_agent(): return Agent()\n"
        ),
    )

    with hang_safety_timeout(30), pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("hangy", data_root=tmp_path, timeout=1.0)

    assert caught.value.diagnostic.code == "agent_action_timeout"
    assert caught.value.diagnostic.stage == "action"


def test_supervised_reset_timeout_is_reported(tmp_path):
    from _hang_safety import hang_safety_timeout

    _write_agent(
        tmp_path,
        "hangy_reset",
        source=(
            "class Agent:\n"
            "    def reset(self, context):\n"
            "        while True:\n"
            "            pass\n"
            "    def declare_processes(self): return []\n"
            "    def act(self, observation): return None\n"
            "def create_agent(): return Agent()\n"
        ),
    )

    with hang_safety_timeout(30), pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("hangy_reset", data_root=tmp_path, timeout=1.0)

    assert caught.value.diagnostic.code == "agent_reset_timeout"
    assert caught.value.diagnostic.stage == "reset"


def test_supervised_success_matches_unsupervised_action(tmp_path):
    """Supervised and unsupervised dry runs of the identical agent/seed
    must reach the identical dry-run action -- the single-call analogue of
    the whole-match determinism proof in test_agent_lab_integration.py."""

    _write_agent(tmp_path, "example", source=VALID_SOURCE)

    unsupervised = validate_agent("example", data_root=tmp_path)
    supervised = validate_agent("example", data_root=tmp_path, timeout=5.0)

    assert unsupervised.dry_run_action == supervised.dry_run_action
    assert unsupervised.api_version == supervised.api_version


def test_supervised_trace_path_writes_a_trace(tmp_path):
    _write_agent(tmp_path, "example", source=VALID_SOURCE)
    trace_path = tmp_path / "trace.jsonl"

    validate_agent("example", data_root=tmp_path, timeout=5.0, trace_path=trace_path)

    assert trace_path.exists()
    from battle_engine.agent_trace import read_trace

    document = read_trace(trace_path)
    assert document.header.supervised is True
    assert len(document.decisions) == 1
    assert document.decisions[0].diagnostic is None


def test_cli_default_is_supervised_and_reports_timeout(tmp_path, monkeypatch, capsys):
    from _hang_safety import hang_safety_timeout

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    _write_agent(
        tmp_path,
        "hangy",
        source=(
            "from battle_engine.agent_api import ProcessDeclaration\n"
            "class Agent:\n"
            "    def reset(self, context): pass\n"
            "    def declare_processes(self): return [ProcessDeclaration('main', 1, 1.0)]\n"
            "    def act(self, observation):\n"
            "        while True:\n"
            "            pass\n"
            "def create_agent(): return Agent()\n"
        ),
    )

    with hang_safety_timeout(30):
        exit_code = main(["hangy", "--timeout", "1"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "code: agent_action_timeout" in err


def test_invalid_cli_timeout_exits_two():
    with pytest.raises(SystemExit) as caught:
        main(["example", "--timeout", "0.001"])
    assert caught.value.code == 2


# --------------------------------------------------------------------------
# Custom data root
# --------------------------------------------------------------------------


def test_validate_agent_honors_data_root_argument(tmp_path):
    scaffold_create_agent("example", data_root=tmp_path, resource_root=ROOT)

    result = validate_agent("example", data_root=tmp_path)

    assert result.agent_id == "example"


def test_cli_honors_bytefray_root_env_var(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    scaffold_create_agent("example", data_root=tmp_path, resource_root=ROOT)

    exit_code = main(["example"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "status: valid" in out


# --------------------------------------------------------------------------
# No raw tracebacks for expected failures
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("manifest", "source"),
    [
        ({"api_version": 3}, VALID_SOURCE),
        (None, "def create_agent(:\n    pass\n"),
        (None, BROKEN_RESET_SOURCE),
        (None, INVALID_ACTION_SOURCE),
    ],
)
def test_expected_failures_have_no_traceback(tmp_path, manifest, source):
    _write_agent(tmp_path, "example", manifest=manifest, source=source)

    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent("example", data_root=tmp_path)

    message = caught.value.diagnostic.message
    assert "Traceback" not in message
    assert 'File "' not in message
    assert len(message) <= 240


# --------------------------------------------------------------------------
# CLI behavior
# --------------------------------------------------------------------------


def test_cli_success_output_and_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    scaffold_create_agent("example", data_root=tmp_path, resource_root=ROOT)

    exit_code = main(["example"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    lines = captured.out.strip().splitlines()
    assert lines[0] == "agent: example"
    assert lines[1] == "status: valid"
    assert lines[2] == "api_version: 2"
    assert lines[3].startswith("dry_run_action: WRITE operand=")


def test_cli_failure_output_and_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))

    exit_code = main(["does_not_exist"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    lines = captured.err.strip().splitlines()
    assert lines[0] == "agent: does_not_exist"
    assert lines[1] == "status: invalid"
    assert lines[2] == "stage: discovery"
    assert lines[3] == "code: agent_unknown"
    assert lines[4].startswith("error: ")


def test_cli_help_exits_zero_and_mentions_agent_id(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["--help"])

    assert caught.value.code == 0
    out = capsys.readouterr().out
    assert "agent_id" in out


def test_cli_missing_positional_argument_exits_two():
    with pytest.raises(SystemExit) as caught:
        main([])

    assert caught.value.code == 2


def test_end_to_end_create_then_validate_subprocess(tmp_path):
    data_root = tmp_path / "data-root"
    env = dict(os.environ, BYTEFRAY_ROOT=str(data_root))

    created = _run("agents", "create", "example", cwd=tmp_path, env=env)
    assert created.returncode == 0, created.stderr

    validated = _run("agents", "validate", "example", cwd=tmp_path, env=env)
    assert validated.returncode == 0, validated.stderr
    assert "status: valid" in validated.stdout
    assert validated.stderr == ""


def test_agents_help_mentions_validate():
    result = _run("agents", "--help")
    assert result.returncode == 0
    assert "validate" in result.stdout


def test_bare_agents_and_agents_create_are_unchanged(tmp_path):
    """Regression: adding 'validate' must not change bare `agents` or
    `agents create` behavior."""

    data_root = tmp_path / "data-root"
    env = dict(os.environ, BYTEFRAY_ROOT=str(data_root))

    listed = _run("agents", cwd=tmp_path, env=env)
    assert listed.returncode == 0

    created = _run("agents", "create", "example", cwd=tmp_path, env=env)
    assert created.returncode == 0
    assert "agent: example" in created.stdout
