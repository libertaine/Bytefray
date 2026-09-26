"""V6 Phase 2B.9 — Scope A ruleset retirement: the execution/recognition
boundary this phase's whole safety case depends on.

Phase 2B.9 (docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md,
implementing the disposition in docs/research/v6/
V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md) removed three closed-research
identities -- ``bytefray-rules-2-alpha1``, ``bytefray-rules-2-alpha11``, and
``bytefray-rules-3-alpha1`` -- from executable registration, while explicitly
requiring that historical recognition of the same three literal IDs survive
unchanged. This file pins both sides of that contract permanently, following
the precedent already established for the V5 R1/R2 retirement
(``test_v5_alpha1_phase_b_engine_hygiene.py::test_rejected_rulesets_not_recognized_in_production``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.python_runtime import (
    VULNERABLE_CORE_RULESET_IDS,
    has_vulnerable_core,
)
from battle_engine.replay import (
    MatchConfiguration,
    ReplayHeader,
    iter_replay,
    resolve_replay_ruleset,
    write_replay,
)
from battle_engine.result_model import ReplayReference, ResultEnvelope, resolve_result_ruleset
from battle_engine.rules import normalize_ruleset_id
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    BYTEFRAY_RULESET_V2_ALPHA1_ID,
    BYTEFRAY_RULESET_V2_ALPHA11_ID,
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V3_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ID,
    UnknownRulesetError,
    resolve_ruleset_policy,
)

SCOPE_A_RETIRED_IDS = (
    BYTEFRAY_RULESET_V2_ALPHA1_ID,
    BYTEFRAY_RULESET_V2_ALPHA11_ID,
    BYTEFRAY_RULESET_V3_ALPHA1_ID,
)


# ---------------------------------------------------------------------------
# New execution: rejected, and never silently redirected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("retired_id", SCOPE_A_RETIRED_IDS)
def test_retired_identity_no_longer_resolves_to_a_policy(retired_id: str) -> None:
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(retired_id)


def test_no_retired_identity_remains_in_the_executable_registry() -> None:
    assert set(SCOPE_A_RETIRED_IDS).isdisjoint(_RULESET_POLICIES)


@pytest.mark.parametrize("retired_id", SCOPE_A_RETIRED_IDS)
def test_retired_identity_is_never_silently_aliased_to_a_supported_ruleset(
    retired_id: str,
) -> None:
    """T-12: a retired ID must never resolve as, or be normalized into,
    ``bytefray-rules-2`` or ``bytefray-rules-4`` -- retirement is dispatch
    rejection, never a redirect."""

    # normalize_ruleset_id governs historical *attribution*, not dispatch --
    # it must still return the retired ID completely unchanged (see the
    # "historical recognition" block below), never rewritten to a
    # currently-supported identity.
    assert normalize_ruleset_id(retired_id) not in (
        BYTEFRAY_RULESET_V2_ID,
        BYTEFRAY_RULESET_V4_ID,
    )
    assert normalize_ruleset_id(retired_id) == retired_id
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(retired_id)


# ---------------------------------------------------------------------------
# Historical recognition: the literal identity survives, independent of the
# executable registry (proven with hand-built artifacts, mirroring
# test_ruleset_v2.py's own resume-mismatch fixture pattern -- this file has
# no engine execution dependency, so no registration is required for it to
# pass, exactly as the audit's N.1/N.2 proved for the real corpus).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("retired_id", SCOPE_A_RETIRED_IDS)
def test_retired_identity_still_recognized_by_normalize_ruleset_id(
    retired_id: str,
) -> None:
    assert normalize_ruleset_id(retired_id) == retired_id


@pytest.mark.parametrize("retired_id", SCOPE_A_RETIRED_IDS)
def test_retired_identity_replay_header_still_resolves_and_labels(
    tmp_path: Path, retired_id: str
) -> None:
    replay_path = tmp_path / "replay.jsonl"
    write_replay(
        replay_path,
        [
            ReplayHeader(
                MatchConfiguration(64),
                match_id="match_x",
                result_id="result_x",
                ruleset_id=retired_id,
            )
        ],
    )
    header = next(
        record for record in iter_replay(replay_path) if isinstance(record, ReplayHeader)
    )
    provenance = resolve_replay_ruleset(header)
    assert provenance.value == retired_id
    assert provenance.confidence == "recorded"


@pytest.mark.parametrize("retired_id", SCOPE_A_RETIRED_IDS)
def test_retired_identity_result_envelope_still_resolves(retired_id: str) -> None:
    envelope = ResultEnvelope(
        result_id="result_x",
        match_id="match_x",
        mode="b2",
        winner="tie",
        termination_reason="tick_limit",
        ticks=2,
        entrants=({"agent_id": "A"}, {"agent_id": "B"}),
        reproducibility={"seed": 5},
        replay=ReplayReference("r", "0" * 64, "replay.jsonl"),
        ruleset_id=retired_id,
    )
    provenance = resolve_result_ruleset(envelope)
    assert provenance.value == retired_id
    assert provenance.confidence == "recorded"


# ---------------------------------------------------------------------------
# Historical replay core-status display: T-9, "the most commonly mis-scoped
# item in the whole retirement" per the audit -- membership must survive
# even though the policy object is gone.
#
# V6 Phase 2B.12 removed ``OBSERVABLE_CORE_RULESET_IDS``/``has_observable_core``
# themselves (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md,
# correcting Phase 2B.8's original T-9 assumption that this table and
# ``VULNERABLE_CORE_RULESET_IDS`` were an inseparable pair): unlike the
# vulnerable-core table, no historical reader ever consulted it, so its
# membership assertions below were removed along with it. Only
# ``VULNERABLE_CORE_RULESET_IDS`` membership remains meaningful to pin.
# ---------------------------------------------------------------------------


def test_vulnerable_core_membership_survives_for_v2_alpha1() -> None:
    assert BYTEFRAY_RULESET_V2_ALPHA1_ID in VULNERABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V2_ALPHA1_ID) is True


def test_vulnerable_core_membership_survives_for_v2_alpha11() -> None:
    assert BYTEFRAY_RULESET_V2_ALPHA11_ID in VULNERABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V2_ALPHA11_ID) is True


def test_vulnerable_core_membership_survives_for_v3_alpha1() -> None:
    assert BYTEFRAY_RULESET_V3_ALPHA1_ID in VULNERABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V3_ALPHA1_ID) is True
