"""Component identity: display names stay presentation-only; identities stay put.

See docs/COMPONENT_VERSIONING.md. These tests pin the exact spelling of every
persisted identity this codebase writes or recognises, and check that the
Ruleset display names introduced by the component-identity reset can never
leak into an artifact, be accepted as input, or name a non-product identity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from battle_client import spectator_export
from battle_engine import agent_api, agent_trace, cli, replay, result_model, rules
from battle_engine import ruleset_policy as rp
from battle_engine.agents import AgentSpec, agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.ruleset_names import (
    ACTIVE_SENSING_DISPLAY_NAME,
    CLASSIC_DISPLAY_NAME,
    RULESET_DISPLAY_NAMES,
    ruleset_display_name,
    ruleset_name_with_id,
)

from app.services import ruleset_options

# Every Ruleset identity constant in battle_engine.rules, spelled out. A
# rename of any of these would silently reinterpret persisted artifacts.
EXPECTED_RULESET_IDS = {
    "BYTEFRAY_RULESET_ID": "bytefray-rules-1",
    "BYTEFRAY_RULESET_V4_ALPHA1_ID": "bytefray-rules-4-alpha1",
    "BYTEFRAY_RULESET_V4_ALPHA2_ID": "bytefray-rules-4-alpha2",
    "BYTEFRAY_RULESET_V4_ID": "bytefray-rules-4",
    "BYTEFRAY_RULESET_V6_ALPHA1_ID": "bytefray-rules-6-alpha1",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID": "bytefray-rules-6-research-scale",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID": "bytefray-rules-6-research-scale-move",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID": (
        "bytefray-rules-6-research-scale-move-proportional"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID": "bytefray-rules-6-research-capture-hold-k2",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID": (
        "bytefray-rules-6-research-capture-hold-k2-disruption-slot1"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID": "bytefray-rules-6-research-disruption-slot1",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID": (
        "bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID": (
        "bytefray-rules-6-research-disruption-slot1-mirrored-passes"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID": (
        "bytefray-rules-6-research-capture-hold-k2-disruption-slot1-anchor-before-core"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID": (
        "bytefray-rules-6-research-disruption-slot1-anchor-before-core"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID": "bytefray-rules-6-research-sensing-r32",
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID": (
        "bytefray-rules-6-research-disruption-slot1-sensing-r32"
    ),
    "BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID": "bytefray-rules-6-research-sensing-active-w27",
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID": (
        "bytefray-rules-6-research-disruption-slot1-sensing-active-w27"
    ),
}

HISTORICAL_READONLY = {
    "bytefray-rules-2",
    "bytefray-rules-2-alpha1",
    "bytefray-rules-2-alpha11",
    "bytefray-rules-3-alpha1",
    "bytefray-rules-4-alpha1",
    "bytefray-rules-4-alpha2",
}

PRODUCT_RULESETS = rp.PUBLIC_STABLE_RULESET_IDS | rp.PUBLIC_EXPERIMENTAL_RULESET_IDS

# --------------------------------------------------------------------------
# Persisted identities are unchanged
# --------------------------------------------------------------------------


def test_every_ruleset_identity_constant_keeps_its_exact_spelling() -> None:
    constants = {name: getattr(rules, name) for name in rules.__all__ if name.endswith("_ID")}
    assert constants == EXPECTED_RULESET_IDS


def test_ruleset_lifecycle_sets_are_unchanged() -> None:
    assert rp.PUBLIC_STABLE_RULESET_IDS == {"bytefray-rules-4"}
    assert rp.PUBLIC_EXPERIMENTAL_RULESET_IDS == {"bytefray-rules-6-alpha1"}
    assert rp.OMITTED_RULESET_CANDIDATES == ("bytefray-rules-4",)
    assert rp.HISTORICAL_READONLY_RULESET_IDS == HISTORICAL_READONLY
    assert len(rp.ACTIVE_RESEARCH_RULESET_IDS) == 12
    assert rp.RETIRED_RESEARCH_RULESET_IDS == {
        "bytefray-rules-6-research-scale-move",
        "bytefray-rules-6-research-scale-move-proportional",
    }
    executable = set(rp._RULESET_POLICIES)
    assert executable == (
        rp.PUBLIC_STABLE_RULESET_IDS
        | rp.PUBLIC_EXPERIMENTAL_RULESET_IDS
        | rp.ACTIVE_RESEARCH_RULESET_IDS
        | rp.RETIRED_RESEARCH_RULESET_IDS
    )
    for ruleset_id, policy in rp._RULESET_POLICIES.items():
        assert policy.ruleset_id == ruleset_id


@pytest.mark.parametrize("ruleset_id", sorted(HISTORICAL_READONLY | {"bytefray-rules-1"}))
def test_historical_identities_are_recognised_but_never_executable_or_aliased(ruleset_id: str) -> None:
    with pytest.raises(rp.UnknownRulesetError):
        rp.resolve_ruleset_policy(ruleset_id)
    assert rules.normalize_ruleset_id(ruleset_id) == ruleset_id
    assert ruleset_display_name(ruleset_id) is None


def test_only_the_documented_historical_alias_exists() -> None:
    assert dict(rules._RULESET_ALIASES) == {"evaluation-rules-1": "bytefray-rules-1"}


def test_wire_format_identities_are_unchanged() -> None:
    assert agent_api.AGENT_API_VERSION == 2
    assert agent_api.SUPPORTED_AGENT_API_VERSIONS == frozenset({2})
    assert (replay.SCHEMA_NAME, replay.SCHEMA_VERSION) == ("battle2.replay", 4)
    assert replay.SUPPORTED_SCHEMA_VERSIONS == (2, 3, 4)
    assert (result_model.SCHEMA_NAME, result_model.SCHEMA_VERSION) == ("battle2.result", 2)
    assert result_model.SUPPORTED_SCHEMA_VERSIONS == (1, 2)
    assert agent_trace.TRACE_SCHEMA == "bytefray.agent_trace"
    assert (agent_trace.TRACE_SCHEMA_VERSION, agent_trace.TRACE_SCHEMA_VERSION_V2) == (1, 2)


def test_spectator_presentation_contract_is_unchanged() -> None:
    assert spectator_export.MANIFEST_SCHEMA == "bytefray.spectator.manifest"
    assert spectator_export.MANIFEST_SCHEMA_VERSION == 2
    assert spectator_export.DOCUMENT_SCHEMAS == {
        "broadcast": "bytefray.spectator.broadcast",
        "agent_a": "bytefray.spectator.agent_view",
    }
    assert spectator_export.DOCUMENT_SCHEMA_VERSION == 1
    assert spectator_export.PROVENANCE == "bytefray_match"
    assert spectator_export.EXPORTER_VERSION == 1
    assert spectator_export.SUPPORTED_ENTRANTS == ("A", "B")


# --------------------------------------------------------------------------
# Display names are presentation only
# --------------------------------------------------------------------------


def test_display_names_cover_exactly_the_product_offered_rulesets() -> None:
    assert dict(RULESET_DISPLAY_NAMES) == {
        "bytefray-rules-4": "Classic",
        "bytefray-rules-6-alpha1": "Active Sensing (Alpha)",
    }
    assert set(RULESET_DISPLAY_NAMES) == PRODUCT_RULESETS
    assert (CLASSIC_DISPLAY_NAME, ACTIVE_SENSING_DISPLAY_NAME) == ("Classic", "Active Sensing (Alpha)")
    assert len(set(RULESET_DISPLAY_NAMES.values())) == len(RULESET_DISPLAY_NAMES)
    with pytest.raises(TypeError):
        RULESET_DISPLAY_NAMES["bytefray-rules-4-alpha2"] = "Classic"  # type: ignore[index]


def test_experimental_names_carry_their_stability_and_stable_names_do_not() -> None:
    for ruleset_id in rp.PUBLIC_EXPERIMENTAL_RULESET_IDS:
        assert "(Alpha)" in RULESET_DISPLAY_NAMES[ruleset_id]
    for ruleset_id in rp.PUBLIC_STABLE_RULESET_IDS:
        name = RULESET_DISPLAY_NAMES[ruleset_id]
        assert "Alpha" not in name and "Beta" not in name


@pytest.mark.parametrize(
    "ruleset_id",
    sorted(rp.ACTIVE_RESEARCH_RULESET_IDS | rp.RETIRED_RESEARCH_RULESET_IDS | {"bytefray-rules-99"}),
)
def test_research_and_unknown_identities_have_no_display_name(ruleset_id: str) -> None:
    assert ruleset_display_name(ruleset_id) is None
    assert ruleset_name_with_id(ruleset_id) == ruleset_id


@pytest.mark.parametrize("name", sorted(RULESET_DISPLAY_NAMES.values()))
def test_a_display_name_is_never_accepted_as_a_ruleset_identity(name: str) -> None:
    assert not name.startswith("bytefray-rules-")
    with pytest.raises(rp.UnknownRulesetError):
        rp.resolve_ruleset_policy(name)
    assert rules.normalize_ruleset_id(name) == name
    with pytest.raises(SystemExit) as caught:
        cli.parse_args(["--ruleset", name])
    assert caught.value.code == 2


def test_name_with_id_always_reveals_the_canonical_identity() -> None:
    assert ruleset_name_with_id("bytefray-rules-4") == "Classic (bytefray-rules-4)"
    assert (
        ruleset_name_with_id("bytefray-rules-6-alpha1")
        == "Active Sensing (Alpha) (bytefray-rules-6-alpha1)"
    )


# --------------------------------------------------------------------------
# Designer and CLI selection still resolves to the same identities
# --------------------------------------------------------------------------


def test_designer_options_keep_identity_order_and_default() -> None:
    assert ruleset_options.DEFAULT_DESIGNER_RULESET_ID == "bytefray-rules-4"
    ids = lambda options: [option.ruleset_id for option in options]
    assert ids(ruleset_options.SIMPLE_RULESET_OPTIONS) == ["bytefray-rules-4"]
    assert ids(ruleset_options.EVALUATION_RULESET_OPTIONS) == ["bytefray-rules-4"]
    assert ids(ruleset_options.DESIGNER_RULESET_OPTIONS) == ["bytefray-rules-4", "bytefray-rules-6-alpha1"]


def test_designer_labels_use_the_shared_display_names() -> None:
    assert ruleset_options.RULESET_V4_OPTION.label == "Classic — Recommended"
    assert ruleset_options.RULESET_V6_ALPHA1_OPTION.label == "Active Sensing (Alpha)"
    for option in ruleset_options.DESIGNER_RULESET_OPTIONS:
        assert option.label.startswith(RULESET_DISPLAY_NAMES[option.ruleset_id])
        assert "V6" not in option.label
    description = ruleset_options.RULESET_DESCRIPTION
    assert "Classic (bytefray-rules-4)" in description
    assert "Active Sensing (Alpha) (bytefray-rules-6-alpha1)" in description
    assert "V6 alpha1" not in description


def test_cli_ruleset_choices_and_default_are_canonical_identities(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.parse_args([]).ruleset is None
    for ruleset_id in sorted(PRODUCT_RULESETS):
        assert cli.parse_args(["--ruleset", ruleset_id]).ruleset == ruleset_id
    with pytest.raises(SystemExit):
        cli.parse_args(["--help"])
    # argparse wraps at hyphens, so rejoin "bytefray-rules-6-" + "alpha1".
    text = re.sub(r"-\s+", "-", " ".join(capsys.readouterr().out.split()))
    assert "{bytefray-rules-4,bytefray-rules-6-alpha1}" in text
    assert "bytefray-rules-4 (Classic) is the default" in text
    assert "bytefray-rules-6-alpha1 is Active Sensing (Alpha)" in text
    assert "V6 alpha1" not in text


# --------------------------------------------------------------------------
# Serialized match artifacts carry identities, never display names
# --------------------------------------------------------------------------

_AGENT_SOURCE = '''
from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration
class Agent:
    def reset(self, context):
        self.context = context
    def declare_processes(self):
        return [ProcessDeclaration("p", 64, 1.0)]
    def act(self, obs):
        if self.context.sensing_window is not None:
            return AgentAction(ActionKindV2.SENSE, obs.self_anchor)
        return AgentAction(ActionKindV2.READ, obs.self_anchor)
def create_agent():
    return Agent()
'''


def _agent(root: Path, name: str, *, sensing: bool) -> AgentSpec:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.py").write_text(_AGENT_SOURCE, encoding="utf-8")
    manifest: dict[str, object] = {"kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent"}
    if sensing:
        manifest["capabilities"] = {"version": 1, "required": ["sense"]}
    (directory / "agent.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    spec = agent_spec_from_dir(directory)
    assert spec is not None
    return spec


@pytest.mark.parametrize("ruleset_id", ["bytefray-rules-4", "bytefray-rules-6-alpha1"])
def test_match_artifacts_record_the_exact_identity_and_no_display_name(tmp_path: Path, ruleset_id: str) -> None:
    sensing = ruleset_id == "bytefray-rules-6-alpha1"
    a = _agent(tmp_path, "a", sensing=sensing)
    b = _agent(tmp_path, "b", sensing=sensing)
    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8),
        entrants=(MatchEntrant.python("A", "a", 0, a), MatchEntrant.python("B", "b", 256, b)),
        max_ticks=4,
        replay_path=tmp_path / "replay.jsonl",
        trace_path=tmp_path / "trace.jsonl",
        ruleset_id=ruleset_id,
        verbose=False,
    )
    NativeMatchService().run(request)

    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert (result["schema"], result["schema_version"], result["ruleset_id"]) == (
        "battle2.result",
        2,
        ruleset_id,
    )
    header = json.loads((tmp_path / "replay.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert header["ruleset_id"] == ruleset_id
    trace_lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    trace_header, binding = json.loads(trace_lines[0]), json.loads(trace_lines[-1])
    assert (trace_header["schema"], trace_header["schema_version"]) == ("bytefray.agent_trace", 2)
    assert (binding["record_type"], binding["ruleset_id"]) == ("binding", ruleset_id)
    for artifact in ("result.json", "replay.jsonl", "trace.jsonl"):
        text = (tmp_path / artifact).read_text(encoding="utf-8")
        for name in RULESET_DISPLAY_NAMES.values():
            assert name not in text, (artifact, name)
