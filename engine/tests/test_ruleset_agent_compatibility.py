"""Canonical Ruleset/runtime/Agent-API compatibility coverage."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    RulesetAgentUnsupportedError,
)
from battle_engine.rules import BYTEFRAY_RULESET_ID
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
    UnknownRulesetError,
    agent_supported_by_ruleset,
    resolve_ruleset_policy,
)


@pytest.mark.parametrize(
    ("metadata", "ruleset_id", "expected"),
    [
        ({"kind": "builtin"}, BYTEFRAY_RULESET_ID, True),
        ({"kind": "blob"}, BYTEFRAY_RULESET_ID, True),
        ({"kind": "blob"}, BYTEFRAY_RULESET_V2_ID, False),
        ({"kind": "python", "api_version": 1}, BYTEFRAY_RULESET_ID, True),
        ({"kind": "python", "api_version": 1}, BYTEFRAY_RULESET_V2_ID, True),
        ({"kind": "python", "api_version": 2}, BYTEFRAY_RULESET_ID, False),
        ({"kind": "python", "api_version": 2}, BYTEFRAY_RULESET_V2_ID, False),
        ({"kind": "python"}, BYTEFRAY_RULESET_V2_ID, False),
        ({"kind": "python", "api_version": True}, BYTEFRAY_RULESET_V2_ID, False),
        # v4.0.0-rc1 Phase 2: the permanent stable identity -- VM/blob +
        # stable v4 rejected, API v1 + stable v4 rejected, API v2 + stable
        # v4 accepted.
        ({"kind": "blob"}, BYTEFRAY_RULESET_V4_ID, False),
        ({"kind": "python", "api_version": 1}, BYTEFRAY_RULESET_V4_ID, False),
        ({"kind": "python", "api_version": 2}, BYTEFRAY_RULESET_V4_ID, True),
    ],
)
def test_agent_supported_by_ruleset_uses_runtime_and_api_metadata(
    metadata: dict[str, object], ruleset_id: str, expected: bool
) -> None:
    assert agent_supported_by_ruleset(metadata, ruleset_id) is expected


# ---------------------------------------------------------------------------
# V6 Phase 2B.10 Scope B: bytefray-rules-4-alpha1/-alpha2 were retired from
# executable registration. Before retirement, both accepted exactly the
# metadata rows the stable-v4 rows above accept (they share its identical
# supported_runtime_kinds/supported_python_api_versions fields) -- this is
# the execution-vs-recognition negative counterpart: the same metadata that
# used to resolve True against either alpha now resolves False against
# both, because agent_supported_by_ruleset catches UnknownRulesetError and
# fails closed, never falling back to the stable identity's answer.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ruleset_id", [BYTEFRAY_RULESET_V4_ALPHA1_ID, BYTEFRAY_RULESET_V4_ALPHA2_ID])
@pytest.mark.parametrize(
    "metadata",
    [
        {"kind": "python", "api_version": 2},
        {"kind": "python", "api_version": 1},
        {"kind": "blob"},
    ],
)
def test_agent_supported_by_ruleset_fails_closed_for_retired_alpha_identities(
    metadata: dict[str, object], ruleset_id: str
) -> None:
    assert agent_supported_by_ruleset(metadata, ruleset_id) is False
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(ruleset_id)


@pytest.mark.parametrize(
    ("ruleset_id", "api_version"),
    [
        (BYTEFRAY_RULESET_ID, 2),
        (BYTEFRAY_RULESET_V2_ID, 2),
        (BYTEFRAY_RULESET_V2_ID, True),
        # v4.0.0-rc1 Phase 2: a real NativeMatchService.run rejection under
        # the stable identity too -- "API v1 + Ruleset v4 must fail
        # clearly" (task Sec 10), proven at the actual execution boundary,
        # not only through the predicate above.
        (BYTEFRAY_RULESET_V4_ID, 1),
        (BYTEFRAY_RULESET_V4_ID, None),
    ],
)
def test_native_match_service_rejects_api_mismatch_before_runtime(
    tmp_path, ruleset_id: str, api_version: object
) -> None:
    entrants = tuple(
        MatchEntrant.python(
            slot,
            f"agent-{slot.lower()}",
            start,
            SimpleNamespace(kind="python", api_version=api_version),
        )
        for slot, start in (("A", 0), ("B", 32))
    )
    replay = tmp_path / "doomed" / "replay.jsonl"
    request = MatchRequest(
        config=Config(arena_size=128, instr_per_tick=8),
        entrants=entrants,
        max_ticks=1,
        replay_path=replay,
        verbose=False,
        ruleset_id=ruleset_id,
    )

    with pytest.raises(RulesetAgentUnsupportedError) as caught:
        NativeMatchService().run(request)

    assert caught.value.ruleset_id == ruleset_id
    assert [agent[0] for agent in caught.value.unsupported_agents] == [
        "A",
        "B",
    ]
    assert not replay.parent.exists()


# ---------------------------------------------------------------------------
# V6 Phase 2B.10 Scope B: before retirement, a bytefray-rules-4-alpha1
# request with a mismatched Agent API version reached the same
# RulesetAgentUnsupportedError the stable-identity rows above still do
# (alpha1 was a known, compatible-but-mismatched Ruleset). Now the Ruleset
# itself is unknown, so NativeMatchService.run must fail earlier and
# differently -- UnknownRulesetError, before any agent-compatibility
# question is even asked, and (T-12) never silently substituting the
# stable identity's answer.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ruleset_id", [BYTEFRAY_RULESET_V4_ALPHA1_ID, BYTEFRAY_RULESET_V4_ALPHA2_ID]
)
def test_native_match_service_rejects_retired_alpha_identity_before_agent_compatibility(
    tmp_path, ruleset_id: str
) -> None:
    entrants = tuple(
        MatchEntrant.python(
            slot,
            f"agent-{slot.lower()}",
            start,
            SimpleNamespace(kind="python", api_version=2),
        )
        for slot, start in (("A", 0), ("B", 32))
    )
    replay = tmp_path / "doomed" / "replay.jsonl"
    request = MatchRequest(
        config=Config(arena_size=128, instr_per_tick=8),
        entrants=entrants,
        max_ticks=1,
        replay_path=replay,
        verbose=False,
        ruleset_id=ruleset_id,
    )

    with pytest.raises(UnknownRulesetError) as caught:
        NativeMatchService().run(request)

    assert caught.value.ruleset_id == ruleset_id
    assert not replay.parent.exists()
