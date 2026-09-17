"""V6 Phase 2B.10 Scope B — V4 alpha retirement: the execution/recognition
boundary this phase's whole safety case depends on.

Phase 2B.10 Scope B (docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md,
implementing the disposition in docs/research/v6/
V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md) removed two identities --
``bytefray-rules-4-alpha1`` and ``bytefray-rules-4-alpha2`` -- from
executable registration, while explicitly requiring that historical
recognition of both literal IDs survive unchanged. This file pins both
sides of that contract permanently, following the precedent already
established for Phase 2B.9's three Class-1 identities
(``test_v6_phase2b9_scope_a_retirement.py``) and the V5 R1/R2 retirement
before it.

**One structural difference from the Phase 2B.9 precedent, deliberately
tested here rather than assumed:** unlike the three Scope-A identities
(all members of both core-status tables), only ``bytefray-rules-4-alpha1``
is a member of ``VULNERABLE_CORE_RULESET_IDS``/``OBSERVABLE_CORE_RULESET_IDS``
-- ``bytefray-rules-4-alpha2`` never was (it uses seed-derived placement
with no vulnerable-core mechanic, exactly like the stable control it was
promoted into). Asserting alpha2's *non*-membership is as important as
asserting alpha1's membership: silently adding alpha2 to either table
would misrepresent a real gameplay difference between the two alphas as a
uniform "all v4 identities are the same" retirement.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.python_runtime import (
    OBSERVABLE_CORE_RULESET_IDS,
    VULNERABLE_CORE_RULESET_IDS,
    has_observable_core,
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
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
    PROCESS_RULESET_IDS,
    UnknownRulesetError,
    resolve_ruleset_policy,
)

SCOPE_B_RETIRED_IDS = (
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
)


# ---------------------------------------------------------------------------
# New execution: rejected, and never silently redirected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
def test_retired_identity_no_longer_resolves_to_a_policy(retired_id: str) -> None:
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(retired_id)


def test_no_retired_identity_remains_in_the_executable_registry() -> None:
    assert set(SCOPE_B_RETIRED_IDS).isdisjoint(_RULESET_POLICIES)
    assert set(SCOPE_B_RETIRED_IDS).isdisjoint(PROCESS_RULESET_IDS)


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
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


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
def test_native_match_service_rejects_a_retired_identity_before_any_artifact_write(
    tmp_path: Path, retired_id: str
) -> None:
    """A retired id must fail closed at dispatch, before match execution,
    with the clean, specific ``UnknownRulesetError`` -- never a downstream
    engine failure, and never a written artifact for a match that never
    validly started."""

    entrants = tuple(
        MatchEntrant.python(
            slot, f"agent-{slot.lower()}", start, {"kind": "python", "api_version": 2}
        )
        for slot, start in (("A", 0), ("B", 32))
    )
    replay_path = tmp_path / "doomed" / "replay.jsonl"
    request = MatchRequest(
        config=Config(arena_size=128, instr_per_tick=8),
        entrants=entrants,
        max_ticks=1,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=retired_id,
    )
    with pytest.raises(UnknownRulesetError):
        NativeMatchService().run(request)
    assert not replay_path.parent.exists()


# ---------------------------------------------------------------------------
# Historical recognition: the literal identity survives, independent of the
# executable registry (proven with hand-built artifacts, mirroring
# test_v6_phase2b9_scope_a_retirement.py's own pattern -- this file has no
# engine execution dependency for these cases, so no registration is
# required for them to pass, exactly as the audit's N.1/N.2 proved for the
# real corpus).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
def test_retired_identity_still_recognized_by_normalize_ruleset_id(
    retired_id: str,
) -> None:
    assert normalize_ruleset_id(retired_id) == retired_id


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
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


@pytest.mark.parametrize("retired_id", SCOPE_B_RETIRED_IDS)
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
# item in the whole retirement" per the audit -- alpha1's membership must
# survive even though the policy object is gone. Alpha2's *non*-membership
# must survive too (see this file's module docstring).
# ---------------------------------------------------------------------------


def test_vulnerable_and_observable_core_membership_survives_for_v4_alpha1() -> None:
    assert BYTEFRAY_RULESET_V4_ALPHA1_ID in VULNERABLE_CORE_RULESET_IDS
    assert BYTEFRAY_RULESET_V4_ALPHA1_ID in OBSERVABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V4_ALPHA1_ID) is True
    assert has_observable_core(BYTEFRAY_RULESET_V4_ALPHA1_ID) is True


def test_v4_alpha2_was_never_a_vulnerable_or_observable_core_member() -> None:
    """Not a retirement-scoping question -- a pre-existing, unchanged
    gameplay fact this phase must not disturb. Alpha2 (and the stable
    control it was promoted into) never had vulnerable-core semantics."""

    assert BYTEFRAY_RULESET_V4_ALPHA2_ID not in VULNERABLE_CORE_RULESET_IDS
    assert BYTEFRAY_RULESET_V4_ALPHA2_ID not in OBSERVABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V4_ALPHA2_ID) is False
    assert has_observable_core(BYTEFRAY_RULESET_V4_ALPHA2_ID) is False


def test_stable_v4_control_also_stays_outside_both_core_tables() -> None:
    """The frozen control's own core-status classification is unchanged by
    this phase -- confirms Scope B touched no gameplay-observable behavior
    for bytefray-rules-4 itself, not just its retired predecessors."""

    assert BYTEFRAY_RULESET_V4_ID not in VULNERABLE_CORE_RULESET_IDS
    assert BYTEFRAY_RULESET_V4_ID not in OBSERVABLE_CORE_RULESET_IDS
    assert has_vulnerable_core(BYTEFRAY_RULESET_V4_ID) is False
    assert has_observable_core(BYTEFRAY_RULESET_V4_ID) is False
