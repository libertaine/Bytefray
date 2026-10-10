"""M1-1 product development fixtures; fixed test inputs, no research execution."""

from __future__ import annotations

import builtins
import io
import json
from dataclasses import fields, replace
from datetime import date
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest
from battle_engine import cli
from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_capabilities import (
    AgentCapabilityMismatchError,
    parse_required_capabilities,
)
from battle_engine.agent_test import AgentTestError, GroupEntrantSpec
from battle_engine.agent_test import test_agent as run_agent_test
from battle_engine.agent_test import test_agents as run_group_test
from battle_engine.agent_validation import AgentValidationFailedError, validate_agent
from battle_engine.agent_worker import (
    AgentWorkerHandle,
    WorkerCallStatus,
    _handle_load,
    _WorkerState,
    agent_spec_to_payload,
)
from battle_engine.agents import AgentSpec, agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    OverlappingCoreError,
    UnsupportedMatchCompositionError,
    canonical_match_id,
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import ProcessMatchController, PythonEntrantInitializationError
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID as ALPHA
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    ACTIVE_RESEARCH_RULESET_IDS,
    PROCESS_RULESET_IDS,
    PUBLIC_EXPERIMENTAL_RULESET_IDS,
    PUBLIC_STABLE_RULESET_IDS,
    RULESET_V4,
    RULESET_V6_ALPHA1,
    agent_supported_by_ruleset,
    resolve_omitted_ruleset_for_agents,
    resolve_ruleset_policy,
)
from battle_engine.ruleset_policy import (
    RULESET_V6_RESEARCH_SENSING_ACTIVE_W27 as T8,
)

CAPABILITIES = {"version": 1, "required": ["sense"]}
SOURCE = '''
from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration
class Agent:
    def reset(self, context):
        self.context = context
    def declare_processes(self):
        return [ProcessDeclaration("p", 64, 1.0)]
    def act(self, obs):
        assert obs.visible_enemy_anchor_addresses == () or self.context.sensing_window is None
        if self.context.sensing_window is not None:
            assert self.context.sensing_window == 27
            return AgentAction(ActionKindV2.SENSE, obs.self_anchor)
        return AgentAction(ActionKindV2.READ, obs.self_anchor)
def create_agent():
    return Agent()
'''


def write_agent(root: Path, name: str, *, declared: bool = False, source: str = SOURCE) -> AgentSpec:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.py").write_text(source, encoding="utf-8")
    manifest = {"kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent"}
    if declared:
        manifest["capabilities"] = CAPABILITIES
    (directory / "agent.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    spec = agent_spec_from_dir(directory)
    assert spec is not None
    return spec


def request(root: Path, a: AgentSpec, b: AgentSpec, ruleset_id: str | None = ALPHA) -> MatchRequest:
    return MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8),
        entrants=(MatchEntrant.python("A", "a", 0, a), MatchEntrant.python("B", "b", 256, b)),
        max_ticks=4, replay_path=root / "replay.jsonl", trace_path=root / "trace.jsonl",
        ruleset_id=ruleset_id,
    )


def test_literal_t8_mechanics_distinct_identity_and_lifecycle() -> None:
    assert ALPHA == "bytefray-rules-6-alpha1"
    assert resolve_ruleset_policy(ALPHA) is RULESET_V6_ALPHA1
    assert RULESET_V6_ALPHA1 is not T8
    assert {f.name for f in fields(T8) if getattr(T8, f.name) != getattr(RULESET_V6_ALPHA1, f.name)} == {"ruleset_id"}
    assert RULESET_V6_ALPHA1.sensing_window == 27
    assert PUBLIC_EXPERIMENTAL_RULESET_IDS == {ALPHA}
    assert ALPHA in PROCESS_RULESET_IDS
    assert ALPHA not in ACTIVE_RESEARCH_RULESET_IDS | PUBLIC_STABLE_RULESET_IDS
    assert RULESET_V4.sensing_mode == "passive"


@pytest.mark.parametrize("block", [
    None, False, [], "sense", {}, {"version": 1}, {"required": []},
    {"version": True, "required": []}, {"version": 1.0, "required": []},
    {"version": "1", "required": []}, {"version": 2, "required": []},
    {"version": 1, "required": "sense"}, {"version": 1, "required": ("sense",)},
    {"version": 1, "required": ["sense", "sense"]},
    {"version": 1, "required": ["SENSE"]}, {"version": 1, "required": [None]},
    {"version": 1, "required": [[]]}, {"version": 1, "required": [], "extra": True},
])
def test_malformed_capability_metadata_fails_closed(tmp_path: Path, block: object) -> None:
    with pytest.raises(AgentManifestError):
        parse_required_capabilities({"capabilities": block})
    if isinstance(block, dict) and isinstance(block.get("required"), tuple):
        # JSON turns tuples into valid lists; the parser case above covers
        # malformed in-memory specs, not a malformed on-disk wire value.
        return
    spec = write_agent(tmp_path, "malformed")
    (spec.dir / "agent.yaml").write_text(json.dumps({**spec.manifest, "capabilities": block}))
    with pytest.raises(AgentManifestError):
        agent_spec_from_dir(spec.dir)


def test_optional_metadata_and_policy_owned_availability(tmp_path: Path) -> None:
    assert parse_required_capabilities({}) == frozenset()
    assert parse_required_capabilities({"capabilities": {"version": 1, "required": []}}) == frozenset()
    assert parse_required_capabilities({"capabilities": CAPABILITIES}) == {"sense"}
    agent = write_agent(tmp_path, "sensor", declared=True)
    for policy in _RULESET_POLICIES.values():
        assert policy.available_capabilities == ({"sense"} if policy.sensing_mode == "active" else set())
        assert agent_supported_by_ruleset(agent, policy.ruleset_id) == (policy.sensing_mode == "active")
        assert agent_supported_by_ruleset(agent.manifest, policy.ruleset_id) == (policy.sensing_mode == "active")
    ordinary = write_agent(tmp_path, "ordinary")
    assert resolve_omitted_ruleset_for_agents(None, (ordinary,)) == RULESET_V4.ruleset_id
    assert agent_supported_by_ruleset(ordinary, ALPHA)


@pytest.mark.parametrize("manifest", [None, [], False, "not a manifest"])
def test_nonmapping_manifests_are_rejected_at_every_preimport_seam(tmp_path: Path, manifest: object) -> None:
    marker = tmp_path / "imported"
    spec = write_agent(tmp_path, "invalid", source=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + SOURCE)
    spec.manifest = manifest
    with pytest.raises(AgentManifestError):
        parse_required_capabilities(manifest)
    with pytest.raises(AgentManifestError):
        agent_spec_to_payload(spec)
    payload = {"name": spec.name, "dir": str(spec.dir), "kind": "python",
               "api_version": 2, "entry_point": spec.entry_point, "manifest": manifest}
    out = io.StringIO()
    _handle_load(_WorkerState(), {"spec": payload, "agent_id": "A"}, out)
    assert json.loads(out.getvalue())["diagnostic"]["code"] == "agent_manifest_invalid"
    assert not marker.exists()


@pytest.mark.parametrize("timeout", [None, 30.0])
def test_mismatch_precedes_all_imports_and_artifact_mutation(tmp_path: Path, timeout: float | None) -> None:
    marker = tmp_path / "imported"
    source = f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + SOURCE
    a = write_agent(tmp_path, "ordinary", source=source)
    b = write_agent(tmp_path, "sensor", declared=True, source=source)
    req = replace(request(tmp_path, a, b, None), agent_call_timeout=timeout)
    # Existing output must survive a rejected preflight too.
    req.replay_path.write_bytes(b"prior replay")
    req.trace_path.write_bytes(b"prior trace")
    with pytest.raises(AgentCapabilityMismatchError):
        NativeMatchService().run(req)
    assert req.replay_path.read_bytes() == b"prior replay"
    assert req.trace_path.read_bytes() == b"prior trace"
    assert not marker.exists() and not (tmp_path / "result.json").exists()
    with pytest.raises(PythonEntrantInitializationError) as error:
        ProcessMatchController.from_python_entrants(req.config, req.entrants, req.max_ticks, agent_call_timeout=timeout)
    assert error.value.diagnostic.code == "agent_capability_unsupported"
    assert not marker.exists()


@pytest.mark.parametrize("timeout", [None, 30.0])
def test_validate_preflight_and_explicit_active_context(tmp_path: Path, timeout: float | None) -> None:
    spec = write_agent(tmp_path, "sensor", declared=True)
    trace = tmp_path / "invalid_trace.jsonl"
    with pytest.raises(AgentValidationFailedError) as error:
        validate_agent(spec.name, data_root=tmp_path, timeout=timeout, trace_path=trace)
    assert error.value.diagnostic.code == "agent_capability_unsupported"
    assert not trace.exists()
    result = validate_agent(spec.name, data_root=tmp_path, timeout=timeout, ruleset_id=ALPHA)
    assert result.dry_run_action.kind.value == "sense"


def test_worker_load_checks_transported_manifest_before_import(tmp_path: Path) -> None:
    marker = tmp_path / "imported"
    spec = write_agent(tmp_path, "sensor", declared=True,
                       source=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + SOURCE)
    for manifest, expected in [(spec.manifest, "agent_capability_unsupported"),
                               ({"capabilities": None}, "agent_manifest_invalid")]:
        payload = {**agent_spec_to_payload(spec), "manifest": manifest}
        out = io.StringIO()
        _handle_load(_WorkerState(), {"spec": payload, "agent_id": "A"}, out)
        assert json.loads(out.getvalue())["diagnostic"]["code"] == expected
        assert not marker.exists()
    handle = AgentWorkerHandle(agent_id="A", slot=0)
    handle.start()
    try:
        response = handle.load(spec, timeout=30.0)
        assert response.status is WorkerCallStatus.FAILED
        assert response.payload["diagnostic"]["code"] == "agent_capability_unsupported"
        assert not marker.exists()
        assert handle.load(spec, timeout=30.0, ruleset_id=ALPHA).status is WorkerCallStatus.OK
        assert marker.exists()
    finally:
        handle.close()


def test_new_identity_inherits_overlap_guard(tmp_path: Path) -> None:
    spec = write_agent(tmp_path, "ordinary")
    req = request(tmp_path, spec, spec)
    req = replace(req, entrants=(req.entrants[0], MatchEntrant.python("B", "b", 4, spec)))
    with pytest.raises(OverlappingCoreError):
        NativeMatchService().run(req)
    assert not req.replay_path.exists()


def test_seeded_placement_and_identity_are_independent_of_t8(tmp_path: Path) -> None:
    a, b = write_agent(tmp_path, "a"), write_agent(tmp_path, "b")
    req = request(tmp_path, a, b)
    assert canonical_match_id(req) != canonical_match_id(replace(req, ruleset_id=T8.ruleset_id))
    assert canonical_match_id(replace(req, ruleset_id=None)) == canonical_match_id(replace(req, ruleset_id=RULESET_V4.ruleset_id))
    def starts(ruleset_id: str) -> tuple[int, ...]:
        return resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=512, entrant_count=2,
                                          supplied_starts=(None, None), seed=Config().seed)
    assert starts(ALPHA) == starts(T8.ruleset_id) == starts(RULESET_V4.ruleset_id)


def test_repeated_matches_and_workers_have_identical_canonical_artifacts(tmp_path: Path) -> None:
    a, b = write_agent(tmp_path, "a", declared=True), write_agent(tmp_path, "b")
    outputs = []
    for index, timeout in enumerate((None, None, 30.0)):
        req = replace(request(tmp_path / str(index), a, b), agent_call_timeout=timeout)
        result = NativeMatchService().run(req)
        assert result.result_path is not None
        envelope = json.loads(result.result_path.read_text())
        assert envelope["ruleset_id"] == ALPHA
        records = [json.loads(line) for line in req.trace_path.read_text().splitlines()]
        resets = [r for r in records if r["record_type"] == "reset"]
        assert resets and all(r["sensing_window"] == 27 for r in resets)
        decisions = [r for r in records if r["record_type"] == "decision_v2"]
        assert decisions and all(r["observation"]["visible_enemy_anchor_addresses"] == [] for r in decisions)
        for record in records:
            record.pop("wall_time_ms", None)
            if record["record_type"] == "header":
                record.pop("supervised", None)
                record.pop("agent_call_timeout", None)
        outputs.append((result.match_id, result.result_id, req.replay_path.read_bytes(), records))
    assert outputs[0] == outputs[1] == outputs[2]


@pytest.mark.parametrize("override", [
    {"scheduler_chunk_size": 1}, {"scheduler_chunk_size": 2},
    {"scheduler_rotate_start": False}, {"scheduler_rotate_start": True},
])
def test_product_policy_refuses_scheduler_overrides(tmp_path: Path, override: dict) -> None:
    spec = write_agent(tmp_path, "ordinary")
    req = replace(request(tmp_path, spec, spec), **override)
    with pytest.raises(UnsupportedMatchCompositionError, match="scheduler overrides"):
        NativeMatchService().run(req)
    with pytest.raises(UnsupportedMatchCompositionError):
        canonical_match_id(req)
    assert not req.replay_path.exists() and not req.trace_path.exists()


def test_worker_payload_preserves_legacy_non_json_metadata(tmp_path: Path) -> None:
    spec = write_agent(tmp_path, "ordinary")
    spec.manifest["updated"] = date(2026, 10, 9)
    assert json.loads(json.dumps(agent_spec_to_payload(spec)))["manifest"] == {}
    handle = AgentWorkerHandle(agent_id="A", slot=0)
    handle.start()
    try:
        assert handle.load(spec, timeout=30.0).status is WorkerCallStatus.OK
        # An injected controller policy has never needed executable registry
        # membership merely to load callbacks without extra requirements.
        assert handle.load(spec, timeout=30.0, ruleset_id="test-only").status is WorkerCallStatus.OK
        projection = SimpleNamespace(**{k: v for k, v in vars(spec).items() if k != "manifest"})
        assert handle.load(projection, timeout=30.0).status is WorkerCallStatus.OK
        spec.manifest["capabilities"] = MappingProxyType(CAPABILITIES)
        assert json.loads(json.dumps(agent_spec_to_payload(spec)))["manifest"] == {"capabilities": CAPABILITIES}
        assert handle.load(spec, timeout=30.0, ruleset_id=ALPHA).status is WorkerCallStatus.OK
    finally:
        handle.close()


@pytest.mark.parametrize("group", [False, True])
def test_development_test_reports_capability_mismatch_before_output(tmp_path: Path, group: bool) -> None:
    write_agent(tmp_path, "sensor", declared=True)
    write_agent(tmp_path, "ordinary")
    output = tmp_path / "rejected"
    with pytest.raises(AgentTestError) as error:
        if group:
            run_group_test((GroupEntrantSpec("A", "ordinary"), GroupEntrantSpec("B", "sensor")),
                           data_root=tmp_path, run_dir=output)
        else:
            run_agent_test("sensor", opponent="ordinary", data_root=tmp_path, run_dir=output)
    assert error.value.diagnostic.code == "agent_capability_unsupported"
    assert not output.exists()


def test_product_execution_has_no_research_import_dependency(tmp_path: Path, monkeypatch) -> None:
    a, b = write_agent(tmp_path, "a", declared=True), write_agent(tmp_path, "b")
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert not name.startswith("tools.research"), "Product execution imported research machinery"
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    result = NativeMatchService().run(request(tmp_path / "product", a, b))
    assert result.ticks_run == 4


@pytest.mark.parametrize("explicit", [False, True])
def test_run_cli_reports_mismatch_without_import_or_artifacts(tmp_path: Path, monkeypatch, capsys, explicit: bool) -> None:
    marker = tmp_path / "imported"
    write_agent(tmp_path, "sensor", declared=True,
                source=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + SOURCE)
    write_agent(tmp_path, "ordinary")
    monkeypatch.setattr(cli, "_data_root", lambda: tmp_path)
    output = tmp_path / "rejected" / "replay.jsonl"
    args = ["--a-type", "sensor", "--b-type", "ordinary", "--ticks", "1", "--replay", str(output)]
    if explicit:
        args += ["--ruleset", RULESET_V4.ruleset_id]
    assert cli.main(args) == 2
    error = capsys.readouterr().err
    assert "required capabilities: sense" in error and "Traceback" not in error
    assert not marker.exists() and not output.exists()
