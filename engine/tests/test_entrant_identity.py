"""Characterization tests for v1.5 Phase 5's entrant-identity/execution-state split.

See ``docs/archive/v1/V1_5_PHASE5_ENTRANT_IDENTITY_EXECUTION_STATE.md``. These tests
protect the specific structural risk that refactor introduced -- that
``EntrantIdentity`` is the sole authoritative store on ``MatchEntrant``
rather than a value duplicated alongside flat ``agent_id``/``name``
fields, and that per-entrant identity distinctness survives end-to-end.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
removed this file's VM-execution cases (``Kernel``, ``battle_engine.core``'s
opcode re-exports, ``builtins.build_agent``) and its Agent API v1
cases (``PythonEntrantController``, ``PythonEntrantState``) along with the
runtime code they exercised. What remains is the identity-value-object
behavior that never depended on either: it is exercised the same way by
the retained ``bytefray-rules-4`` process runtime.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from battle_engine.entrant_identity import EntrantIdentity
from battle_engine.match_service import MatchEntrant
from battle_engine.python_runtime import derive_agent_seed


def test_entrant_identity_is_frozen_hashable_and_value_comparable():
    identity = EntrantIdentity(agent_id="A", name="Alpha")
    with pytest.raises(FrozenInstanceError):
        identity.agent_id = "B"  # type: ignore[misc]
    assert identity == EntrantIdentity(agent_id="A", name="Alpha")
    assert hash(identity) == hash(EntrantIdentity(agent_id="A", name="Alpha"))


def test_match_entrant_agent_id_and_name_derive_from_identity_not_duplicated_storage():
    entrant = MatchEntrant.python("A", "Alpha", 0, object())
    assert entrant.identity == EntrantIdentity(agent_id="A", name="Alpha")
    assert entrant.agent_id == "A"
    assert entrant.name == "Alpha"
    # `identity` is the sole authoritative store: no separate `agent_id`/
    # `name` instance attribute exists alongside it (both are read-only
    # properties derived from `identity`, not stored fields).
    assert "agent_id" not in vars(entrant)
    assert "name" not in vars(entrant)


def test_match_entrant_python_classmethod_builds_the_same_identity_shape():
    entrant = MatchEntrant.python("B", "Beta", 32, object())
    assert entrant.identity == EntrantIdentity(agent_id="B", name="Beta")
    assert entrant.kind == "python"


def test_duplicate_display_names_remain_distinct_entrant_identities():
    first = EntrantIdentity(agent_id="A", name="Same")
    second = EntrantIdentity(agent_id="B", name="Same")
    assert first != second
    assert first.name == second.name
    assert first.agent_id != second.agent_id


def test_derive_agent_seed_golden_vectors():
    """Pin the entrant-seed derivation to literal expected integers,
    computed once (offline) from the currently shipping algorithm. This
    must fail immediately if the formula (prefix, field order, separators,
    hash, byte selection, or endianness) ever drifts, not just if two
    calls stop agreeing with each other.

    These particular vectors use ``api_version=1`` -- preserved even though
    Agent API v1 no longer executes (V6 Phase 2B.12,
    docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md), because
    ``api_version`` participating in the hash material (trap N-1) means
    every historical Ruleset-1/-2 entrant's recorded seed was derived this
    way, and a historical replay/result reader that recomputes a seed for
    comparison must still get the same value it always did.
    """

    assert derive_agent_seed(71, 0, "A", 1) == 69379702161355071673401689362214398906
    assert derive_agent_seed(71, 1, "B", 1) == 162330885650030089838522377773947429270
    assert derive_agent_seed(1337, 0, "A", 1) == 281274714441147123573529567979375554366
    assert derive_agent_seed(1337, 2, "C", 1) == 213243685613712157156274405999378198566
    assert derive_agent_seed(0, 0, "A", 1) == 58770878450558924688994560674375508955
    assert (
        derive_agent_seed(999999, 5, "candidate", 1)
        == 328925147824341361150750412572932710975
    )
