from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration
from battle_engine.agent_inspect import diverge_main, inspect_main
from battle_engine.agent_scaffold import create_agent as scaffold_create_agent
from battle_engine.agent_trace import (
    ABSENT,
    TRACE_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION_V2,
    DecisionRecordV2,
    DeclarationRecord,
    ResetRecord,
    TraceActionV2,
    TraceDocument,
    TraceDocumentV2,
    TraceObservationV2,
    first_divergence_v2,
    read_any_trace,
    read_trace_v2,
)
from battle_engine.agent_validation import (
    VALIDATION_AGENT_ID,
    VALIDATION_SEED,
    AgentValidationFailedError,
    ValidationResult,
    build_validation_context,
    build_validation_observation,
    main,
    validate_agent,
)
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.python_runtime import PythonEntrantInitializationError
from battle_engine.ruleset_policy import RULESET_V6_ALPHA1, UnknownRulesetError

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
            Config(arena_size=128, instr_per_tick=8), (entrant,), 1
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
    from battle_engine.agent_trace import read_trace_v2

    # Issue #11: a new validation trace is schema 2 (schema 1 before it).
    document = read_trace_v2(trace_path)
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


@pytest.mark.parametrize("timeout", [None, 5.0])
@pytest.mark.parametrize("existing_trace", [False, True])
def test_retired_classic_precedes_capability_preflight_import_and_trace(
    tmp_path, monkeypatch, timeout, existing_trace
):
    marker = tmp_path / "imported"
    _write_agent(
        tmp_path, "sensor",
        manifest={"capabilities": {"version": 1, "required": ["sense"]}},
        source=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + VALID_SOURCE,
    )
    output = tmp_path / "rejected"
    trace = output / "trace.jsonl"
    if existing_trace:
        output.mkdir()
        trace.write_bytes(b"prior trace")

    def unexpected_preflight(*args, **kwargs):
        pytest.fail("Retired Ruleset reached capability preflight")

    monkeypatch.setattr(
        "battle_engine.agent_validation.preflight_agent_capabilities", unexpected_preflight
    )
    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent(
            "sensor", data_root=tmp_path, ruleset_id="bytefray-rules-4",
            timeout=timeout, trace_path=trace,
        )
    diagnostic = caught.value.diagnostic
    assert diagnostic.code == "ruleset_unavailable"
    assert diagnostic.stage == "configuration"
    assert diagnostic.exception_type == "UnknownRulesetError"
    assert isinstance(caught.value.__cause__, UnknownRulesetError)
    assert caught.value.__cause__.ruleset_id == "bytefray-rules-4"
    assert "'bytefray-rules-4' is retired and cannot run new matches" in diagnostic.message
    assert not marker.exists()
    if existing_trace:
        assert trace.read_bytes() == b"prior trace"
        assert list(output.iterdir()) == [trace]
    else:
        assert not output.exists()


def test_cli_retired_classic_rejects_before_agent_discovery(tmp_path):
    data_root = tmp_path / "absent-data"
    trace = data_root / "rejected" / "trace.jsonl"
    result = _run(
        "agents", "validate", "undiscovered-agent", "--ruleset", "bytefray-rules-4",
        "--trace-path", str(trace), cwd=tmp_path,
        env=dict(os.environ, BYTEFRAY_ROOT=str(data_root)),
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "'bytefray-rules-4' is retired and cannot run new matches" in result.stderr
    assert "agent_unknown" not in result.stderr
    assert "agent_capability_unsupported" not in result.stderr
    assert "Traceback" not in result.stderr
    assert not data_root.exists()


@pytest.mark.parametrize("timeout", [None, 5.0])
def test_unknown_ruleset_is_configuration_failure_before_preflight_and_import(
    tmp_path, monkeypatch, timeout
):
    marker = tmp_path / "imported"
    _write_agent(
        tmp_path, "example",
        source=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + VALID_SOURCE,
    )
    output = tmp_path / "rejected"

    def unexpected_preflight(*args, **kwargs):
        pytest.fail("Unknown Ruleset reached capability preflight")

    monkeypatch.setattr(
        "battle_engine.agent_validation.preflight_agent_capabilities", unexpected_preflight
    )
    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent(
            "example", data_root=tmp_path, ruleset_id="unregistered-ruleset",
            timeout=timeout, trace_path=output / "trace.jsonl",
        )
    diagnostic = caught.value.diagnostic
    assert diagnostic.code == "ruleset_unavailable"
    assert diagnostic.stage == "configuration"
    assert diagnostic.agent_id == "example"
    assert diagnostic.exception_type == "UnknownRulesetError"
    assert isinstance(caught.value.__cause__, UnknownRulesetError)
    assert caught.value.__cause__.ruleset_id == "unregistered-ruleset"
    assert diagnostic.message == "Unknown Ruleset ID: 'unregistered-ruleset'"
    assert not marker.exists() and not output.exists()


def test_cli_unknown_ruleset_rejects_before_agent_discovery(tmp_path):
    data_root = tmp_path / "absent-data"
    result = _run(
        "agents", "validate", "undiscovered-agent", "--ruleset", "unregistered-ruleset",
        "--trace-path", str(data_root / "trace.jsonl"), cwd=tmp_path,
        env=dict(os.environ, BYTEFRAY_ROOT=str(data_root)),
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid choice: 'unregistered-ruleset'" in result.stderr
    assert "agent_unknown" not in result.stderr
    assert "Traceback" not in result.stderr
    assert not data_root.exists()


@pytest.mark.parametrize("target, cause", [
    ("resolve_ruleset_policy", RuntimeError("orchestration failed")),
    ("resolve_ruleset_policy", LookupError("unexpected lookup failure")),
    ("preflight_agent_capabilities", UnknownRulesetError("unexpected-preflight")),
])
def test_unexpected_orchestration_failure_remains_internal(
    tmp_path, monkeypatch, capsys, target, cause
):
    _write_agent(tmp_path, "example")
    output = tmp_path / "rejected"

    def fail(*args, **kwargs):
        raise cause

    monkeypatch.setattr(f"battle_engine.agent_validation.{target}", fail)
    with pytest.raises(AgentValidationFailedError) as caught:
        validate_agent(
            "example", data_root=tmp_path, ruleset_id="bytefray-rules-6-alpha1",
            trace_path=output / "trace.jsonl",
        )
    diagnostic = caught.value.diagnostic
    assert diagnostic.code == "validation_internal_error"
    assert diagnostic.stage == "internal"
    assert diagnostic.exception_type == type(cause).__name__
    assert diagnostic.message == str(cause)
    assert caught.value.__cause__ is cause
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    assert main([
        "example", "--ruleset", "bytefray-rules-6-alpha1",
        "--trace-path", str(output / "trace.jsonl"),
    ]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "code: validation_internal_error" in captured.err
    assert "stage: internal" in captured.err
    assert "Traceback" not in captured.err
    assert not output.exists()


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


# --------------------------------------------------------------------------
# Schema-2 validation traces (issue #11)
#
# `--trace-path` writes a schema-2 trace that records what the dry run did:
# the synthetic reset (with the sensing window its context carried), the
# validated process declarations, and the one act() callback. Nothing is
# applied to an arena (applied_result is None) and no match runs (no
# binding record).
# --------------------------------------------------------------------------

TWO_PROCESS_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("scout", 3, 0.25), ProcessDeclaration("guard", 1, 0.75)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor + observation.self_reach)

def create_agent():
    return Agent()
"""

# Senses under an explicit Active Sensing Ruleset; reads when the dry-run
# context carries no sensing window.
SENSING_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.window = context.sensing_window

    def declare_processes(self):
        return [ProcessDeclaration("probe", 64, 1.0)]

    def act(self, observation):
        if self.window is None:
            return AgentAction(ActionKindV2.READ, observation.self_anchor)
        return AgentAction(ActionKindV2.SENSE, observation.self_anchor + 5)

def create_agent():
    return Agent()
"""

SENSING_MANIFEST: dict[str, object] = {"capabilities": {"version": 1, "required": ["sense"]}}

DECLARATION_RAISES_SOURCE = """
class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        raise RuntimeError("declare boom")

    def act(self, observation):
        return None

def create_agent():
    return Agent()
"""

DECLARATION_INVALID_SOURCE = """
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 0.5)]

    def act(self, observation):
        return None

def create_agent():
    return Agent()
"""

ACT_RAISES_SOURCE = """
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        raise RuntimeError("act boom")

def create_agent():
    return Agent()
"""

ACT_HANGS_SOURCE = """
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        while True:
            pass

def create_agent():
    return Agent()
"""

ACT_EXITS_WORKER_SOURCE = """
import os
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        os._exit(7)

def create_agent():
    return Agent()
"""

# Byte-for-byte what `bytefray agents validate scaffold --trace-path` wrote
# at 3e597fa, before issue #11: a historical schema-1 validation trace.
HISTORICAL_SCHEMA1_VALIDATION_TRACE = (
    '{"agent_call_timeout": 5.0, "agents": {"A": "validate"}, "match_seed": 1337, '
    '"record_type": "header", "schema": "bytefray.agent_trace", "schema_version": 1, '
    '"supervised": true}\n'
    '{"agent_id": "A", "diagnostic": null, "record_type": "reset", '
    '"wall_time_ms": 0.1278999261558056}\n'
    '{"action": {"kind": "write", "operand": 0, "value": 165}, "action_slot": 0, '
    '"agent_id": "A", "diagnostic": null, "observation": {"agent_id": "A", "alive": true, '
    '"last_read": null, "pc": 0, "register_a": 0, "register_p": 0, "tick": 1, '
    '"zero_flag": false}, "record_type": "decision", "tick": 1, '
    '"wall_time_ms": 0.12440001592040062}\n'
)

TRACE_MODES = pytest.mark.parametrize("timeout", [None, 5.0], ids=["unsupervised", "supervised"])


def _validate_with_trace(
    tmp_path: Path,
    source: str,
    *,
    timeout: float | None,
    name: str = "subject",
    manifest: dict[str, object] | None = None,
    ruleset_id: str | None = None,
    trace_name: str = "trace.jsonl",
) -> tuple[ValidationResult | AgentValidationFailedError, Path]:
    if not (tmp_path / "agents" / name).exists():
        _write_agent(tmp_path, name, source=source, manifest=manifest)
    trace_path = tmp_path / trace_name
    outcome: ValidationResult | AgentValidationFailedError
    try:
        outcome = validate_agent(
            name, data_root=tmp_path, timeout=timeout, trace_path=trace_path,
            ruleset_id=ruleset_id,
        )
    except AgentValidationFailedError as exc:
        outcome = exc
    return outcome, trace_path


def _raw_records(trace_path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]


def _assert_schema2_validation_header(document: TraceDocumentV2, timeout: float | None) -> None:
    header = document.header
    assert header.schema == "bytefray.agent_trace"
    assert header.schema_version == TRACE_SCHEMA_VERSION_V2
    assert header.match_seed == VALIDATION_SEED
    assert dict(header.agents) == {VALIDATION_AGENT_ID: "validate"}
    assert header.supervised is (timeout is not None)
    assert header.agent_call_timeout == timeout
    assert document.binding is None


@TRACE_MODES
def test_validation_trace_success_is_schema2_and_records_the_dry_run(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, VALID_SOURCE, timeout=timeout)
    assert isinstance(outcome, ValidationResult)

    document = read_trace_v2(trace_path)
    _assert_schema2_validation_header(document, timeout)
    assert [type(r) for r in document.records] == [ResetRecord, DeclarationRecord, DecisionRecordV2]

    (reset,) = document.resets
    assert reset.agent_id == VALIDATION_AGENT_ID
    assert reset.diagnostic is None
    assert document.declarations == (DeclarationRecord(VALIDATION_AGENT_ID, "main", 1, 1.0),)

    (decision,) = document.decisions
    assert decision.agent_id == VALIDATION_AGENT_ID
    assert decision.process_id == "main"
    assert decision.action == TraceActionV2(kind="read", operand=0, value=None)
    assert decision.applied_result is None
    assert decision.diagnostic is None
    assert outcome.dry_run_action == AgentAction(ActionKindV2.READ, 0)

    # No schema-1 projection and nothing fabricated on disk.
    raw = _raw_records(trace_path)
    assert [r["record_type"] for r in raw] == ["header", "reset", "declaration", "decision_v2"]
    assert raw[0]["schema_version"] == 2
    assert raw[3]["applied_result"] is None
    raw_observation = raw[3]["observation"]
    assert isinstance(raw_observation, dict)
    for field in ("register_a", "register_p", "zero_flag", "alive", "pc", "action_slot"):
        assert field not in raw[3] and field not in raw_observation
    assert "previous_sense_anchors" not in raw_observation


@TRACE_MODES
def test_validation_trace_preserves_the_api_v2_observation_supplied(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, TWO_PROCESS_SOURCE, timeout=timeout)
    assert isinstance(outcome, ValidationResult)
    document = read_trace_v2(trace_path)
    (decision,) = document.decisions

    supplied = build_validation_observation(2, ProcessDeclaration("scout", 3, 0.25))
    observation = decision.observation
    assert observation == TraceObservationV2(
        current_tick=supplied.current_tick,
        last_callback_tick=supplied.last_callback_tick,
        previous_action_tick=supplied.previous_action_tick,
        self_process_id=supplied.self_process_id,
        self_anchor=supplied.self_anchor,
        self_reach=supplied.self_reach,
        own_core_base=supplied.own_core_base,
        own_core_size=supplied.own_core_size,
        visible_enemy_anchor_addresses=supplied.visible_enemy_anchor_addresses,
        previous_action_applied=supplied.previous_action_applied,
        previous_read_value=supplied.previous_read_value,
        previous_read_owner=supplied.previous_read_owner,
    )
    # No SENSE preceded the dry-run callback, so no reflection is owed.
    assert observation.previous_sense_anchors is ABSENT
    # The agent saw its own reach: READ at anchor + reach.
    assert decision.action == TraceActionV2(kind="read", operand=3, value=None)


@TRACE_MODES
def test_validation_trace_records_every_declared_process_and_the_called_one(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, TWO_PROCESS_SOURCE, timeout=timeout)
    assert isinstance(outcome, ValidationResult)
    document = read_trace_v2(trace_path)

    assert document.declarations == (
        DeclarationRecord(VALIDATION_AGENT_ID, "scout", 3, 0.25),
        DeclarationRecord(VALIDATION_AGENT_ID, "guard", 1, 0.75),
    )
    # Validation makes exactly one callback, for the first declared process.
    (decision,) = document.decisions
    assert decision.process_id == "scout"
    assert decision.observation.self_process_id == "scout"
    assert decision.observation.self_reach == 3


@TRACE_MODES
def test_validation_trace_records_the_active_sensing_window(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(
        tmp_path, SENSING_SOURCE, timeout=timeout, manifest=SENSING_MANIFEST,
        ruleset_id=RULESET_V6_ALPHA1.ruleset_id,
    )
    assert isinstance(outcome, ValidationResult)
    document = read_trace_v2(trace_path)

    (reset,) = document.resets
    assert RULESET_V6_ALPHA1.sensing_window is not None
    assert reset.sensing_window == RULESET_V6_ALPHA1.sensing_window
    assert _raw_records(trace_path)[1]["sensing_window"] == RULESET_V6_ALPHA1.sensing_window
    (decision,) = document.decisions
    assert decision.action == TraceActionV2(kind="sense", operand=5, value=None)
    # Validation does not perform the SENSE, so there is no sensed result.
    assert decision.applied_result is None
    assert decision.observation.visible_enemy_anchor_addresses == ()


@TRACE_MODES
def test_validation_trace_without_explicit_ruleset_omits_the_sensing_window(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(
        tmp_path, SENSING_SOURCE, timeout=timeout, manifest=SENSING_MANIFEST
    )
    assert isinstance(outcome, ValidationResult)
    document = read_trace_v2(trace_path)

    # The ruleset-free dry-run context carries no sensing window, so the
    # trace field is absent (not null), as for any reset without one.
    assert build_validation_context().sensing_window is None
    (reset,) = document.resets
    assert reset.sensing_window is ABSENT
    assert "sensing_window" not in _raw_records(trace_path)[1]
    (decision,) = document.decisions
    assert decision.action == TraceActionV2(kind="read", operand=0, value=None)


@TRACE_MODES
def test_validation_trace_invalid_action(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, INVALID_ACTION_SOURCE, timeout=timeout)
    assert isinstance(outcome, AgentValidationFailedError)
    assert outcome.diagnostic.code == "agent_action_invalid"
    document = read_trace_v2(trace_path)

    _assert_schema2_validation_header(document, timeout)
    assert len(document.declarations) == 1
    (decision,) = document.decisions
    assert decision.process_id == "main"
    assert decision.action is None
    assert decision.applied_result is None
    assert decision.diagnostic is not None
    assert decision.diagnostic.code == "agent_action_invalid"
    assert decision.diagnostic.stage == "action"
    assert decision.diagnostic.tick == 1


@TRACE_MODES
def test_validation_trace_action_exception(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, ACT_RAISES_SOURCE, timeout=timeout)
    assert isinstance(outcome, AgentValidationFailedError)
    document = read_trace_v2(trace_path)

    (decision,) = document.decisions
    assert decision.action is None
    assert decision.applied_result is None
    assert decision.diagnostic is not None
    assert decision.diagnostic.code == outcome.diagnostic.code == "agent_action_failed"
    assert decision.diagnostic.exception_type == "RuntimeError"


@TRACE_MODES
def test_validation_trace_reset_failure_has_no_callback(tmp_path, timeout):
    outcome, trace_path = _validate_with_trace(tmp_path, BROKEN_RESET_SOURCE, timeout=timeout)
    assert isinstance(outcome, AgentValidationFailedError)
    assert outcome.diagnostic.stage == "reset"
    document = read_trace_v2(trace_path)

    _assert_schema2_validation_header(document, timeout)
    (reset,) = document.records
    assert isinstance(reset, ResetRecord)
    assert reset.diagnostic is not None
    assert reset.diagnostic.code == outcome.diagnostic.code
    assert document.declarations == ()
    assert document.decisions == ()


@TRACE_MODES
@pytest.mark.parametrize(
    "source", [DECLARATION_RAISES_SOURCE, DECLARATION_INVALID_SOURCE], ids=["raises", "invalid"]
)
def test_validation_trace_declaration_failure_stops_after_reset(tmp_path, timeout, source):
    outcome, trace_path = _validate_with_trace(tmp_path, source, timeout=timeout)
    assert isinstance(outcome, AgentValidationFailedError)
    assert outcome.diagnostic.stage == "declaration"
    document = read_trace_v2(trace_path)

    # Reset succeeded and is recorded; no declaration was accepted and no
    # callback was made, so neither is recorded. The diagnostic is the
    # command's own failure report (schema 2 has no declaration-failure record).
    (reset,) = document.records
    assert isinstance(reset, ResetRecord)
    assert reset.diagnostic is None


def test_validation_trace_records_supervised_act_timeout(tmp_path):
    from _hang_safety import hang_safety_timeout

    with hang_safety_timeout(60):
        outcome, trace_path = _validate_with_trace(tmp_path, ACT_HANGS_SOURCE, timeout=1.0)
    assert isinstance(outcome, AgentValidationFailedError)
    document = read_trace_v2(trace_path)

    (decision,) = document.decisions
    assert decision.process_id == "main"
    assert decision.action is None
    assert decision.applied_result is None
    assert decision.diagnostic is not None
    assert decision.diagnostic.code == outcome.diagnostic.code == "agent_action_timeout"


def test_validation_trace_records_supervised_worker_exit(tmp_path):
    from _hang_safety import hang_safety_timeout

    with hang_safety_timeout(60):
        outcome, trace_path = _validate_with_trace(tmp_path, ACT_EXITS_WORKER_SOURCE, timeout=5.0)
    assert isinstance(outcome, AgentValidationFailedError)
    document = read_trace_v2(trace_path)

    (decision,) = document.decisions
    assert decision.action is None
    assert decision.applied_result is None
    assert decision.diagnostic is not None
    assert decision.diagnostic.code == outcome.diagnostic.code == "agent_worker_exited"
    assert decision.diagnostic.stage == "action"


def test_validation_trace_supervised_and_unsupervised_callbacks_agree(tmp_path):
    _, unsupervised = _validate_with_trace(
        tmp_path, TWO_PROCESS_SOURCE, timeout=None, trace_name="unsupervised.jsonl"
    )
    _, supervised = _validate_with_trace(
        tmp_path, TWO_PROCESS_SOURCE, timeout=5.0, trace_name="supervised.jsonl"
    )
    a, b = read_trace_v2(unsupervised), read_trace_v2(supervised)
    assert len(a.decisions) == len(b.decisions) == 1
    assert first_divergence_v2(a, b) is None
    assert a.declarations == b.declarations
    assert [r.sensing_window for r in a.resets] == [r.sensing_window for r in b.resets]


@TRACE_MODES
def test_validation_trace_is_inspectable(tmp_path, capsys, timeout):
    _, trace_path = _validate_with_trace(
        tmp_path, SENSING_SOURCE, timeout=timeout, manifest=SENSING_MANIFEST,
        ruleset_id=RULESET_V6_ALPHA1.ruleset_id,
    )
    assert inspect_main([str(trace_path)]) == 0
    summary = capsys.readouterr().out
    assert "schema: bytefray.agent_trace v2" in summary
    assert "agents: A=validate" in summary
    assert "replay_binding: none" in summary
    assert "ticks: 1-1" in summary
    assert "  A/probe: reach=64 share=1" in summary
    assert f"  reset A: sensing_window={RULESET_V6_ALPHA1.sensing_window}" in summary
    assert "failures: 0" in summary

    assert inspect_main([str(trace_path), "--tick", "1", "--process", "probe"]) == 0
    detail = capsys.readouterr().out
    assert "process: probe" in detail
    assert "  action: sense operand=5 value=None" in detail
    assert "  applied: none" in detail


def test_failed_validation_trace_is_inspectable_as_a_failure(tmp_path, capsys):
    _, trace_path = _validate_with_trace(tmp_path, ACT_RAISES_SOURCE, timeout=5.0)
    assert inspect_main([str(trace_path)]) == 0
    summary = capsys.readouterr().out
    assert "failures: 1" in summary
    assert "  tick 1 A/main callback 1: agent_action_failed" in summary


def test_repeated_validation_traces_do_not_diverge(tmp_path, capsys):
    _, first = _validate_with_trace(tmp_path, TWO_PROCESS_SOURCE, timeout=5.0, trace_name="a.jsonl")
    _, second = _validate_with_trace(tmp_path, TWO_PROCESS_SOURCE, timeout=5.0, trace_name="b.jsonl")
    # Only incidental timing may differ between the two files.
    first_raw, second_raw = _raw_records(first), _raw_records(second)
    for record in first_raw + second_raw:
        record.pop("wall_time_ms", None)
    assert first_raw == second_raw

    assert diverge_main([str(first), str(second)]) == 0
    assert "status: identical" in capsys.readouterr().out


def test_validation_traces_of_different_agents_diverge(tmp_path, capsys):
    _, reader = _validate_with_trace(
        tmp_path, VALID_SOURCE, timeout=None, name="reader", trace_name="reader.jsonl"
    )
    _, scout = _validate_with_trace(
        tmp_path, TWO_PROCESS_SOURCE, timeout=None, name="scout", trace_name="scout.jsonl"
    )
    assert diverge_main([str(reader), str(scout)]) == 0
    out = capsys.readouterr().out
    assert "status: diverged" in out
    assert "callback identity differs" in out


def test_historical_schema1_validation_trace_remains_readable(tmp_path, capsys):
    trace_path = tmp_path / "historical.jsonl"
    trace_path.write_text(HISTORICAL_SCHEMA1_VALIDATION_TRACE, encoding="utf-8")

    document = read_any_trace(trace_path)
    assert isinstance(document, TraceDocument)
    assert document.header.schema_version == TRACE_SCHEMA_VERSION
    (decision,) = document.decisions
    assert decision.action is not None and decision.action.kind == "write"

    assert inspect_main([str(trace_path)]) == 0
    assert "schema: bytefray.agent_trace v1" in capsys.readouterr().out
    assert inspect_main([str(trace_path), "--tick", "1"]) == 0
    assert "  action: write operand=0 value=165" in capsys.readouterr().out
    copy = tmp_path / "historical-copy.jsonl"
    copy.write_text(HISTORICAL_SCHEMA1_VALIDATION_TRACE, encoding="utf-8")
    assert diverge_main([str(trace_path), str(copy)]) == 0
    assert "status: identical" in capsys.readouterr().out
    # Reading never rewrites a historical trace.
    assert trace_path.read_text(encoding="utf-8") == HISTORICAL_SCHEMA1_VALIDATION_TRACE


def test_historical_and_new_validation_traces_are_not_compared(tmp_path, capsys):
    historical = tmp_path / "historical.jsonl"
    historical.write_text(HISTORICAL_SCHEMA1_VALIDATION_TRACE, encoding="utf-8")
    _, current = _validate_with_trace(tmp_path, VALID_SOURCE, timeout=None)

    assert diverge_main([str(historical), str(current)]) == 2
    assert "code: trace_schema_mismatch" in capsys.readouterr().err


def test_cli_validation_trace_is_schema2_and_exit_codes_are_unchanged(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    _write_agent(tmp_path, "good", source=VALID_SOURCE)
    _write_agent(tmp_path, "bad", source=INVALID_ACTION_SOURCE)
    good_trace, bad_trace = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"

    assert main(["good", "--trace-path", str(good_trace)]) == 0
    assert f"trace: {good_trace}" in capsys.readouterr().out
    assert main(["bad", "--trace-path", str(bad_trace)]) == 2
    assert "code: agent_action_invalid" in capsys.readouterr().err

    for path in (good_trace, bad_trace):
        document = read_any_trace(path)
        assert isinstance(document, TraceDocumentV2)
        assert document.header.supervised is True
        assert document.binding is None
