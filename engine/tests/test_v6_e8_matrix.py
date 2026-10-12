"""V6 E8: the structural matrix identity, v1 (phase I8-4).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.2,
3.4, 3.5, 6.2, 6.3 and 9, step 1; the implementation plan Sec 1 (I8-4) and
5.8. The structure is frozen before any seed exists and names no seed value.
It binds the four conditions and their final Ruleset identifiers, the family
and its fingerprints, the two fields, the parent goldens, and the two inputs
PR8 Sec 9, step 1 commits with it: the census and the seat strata inputs.
"""

from __future__ import annotations

import json
import re
from itertools import combinations

import pytest
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e8 import decision, family, matrix

IDENTITY = "v6-e8-matrix-v1-e0d322b597da"


def test_the_structural_identity_is_pinned_and_recomputes() -> None:
    assert matrix.structural_digest() == matrix.STRUCTURAL_DIGEST
    assert matrix.matrix_id() == f"v6-e8-matrix-v1-{matrix.STRUCTURAL_DIGEST[:12]}" == IDENTITY
    matrix.verify_frozen_matrix()


def test_the_identity_has_the_registered_form() -> None:
    later = decision.REGISTRATION["seed_protocol"]["structural_identity"]
    assert later == "v6-e8-matrix-v1-<12 hex>"
    assert re.fullmatch(r"v6-e8-matrix-v1-[0-9a-f]{12}", matrix.matrix_id())


def test_the_structure_names_no_seed_value() -> None:
    definition = matrix.structural_definition()
    assert definition["seed_count"] == 32
    assert "seeds" not in definition and "seed_commitment" not in definition
    assert not re.search(r'"seeds?"\s*:\s*\[', json.dumps(definition))
    assert definition["seed_protocol"] == {
        "generator": "secrets.randbelow(2**53)",
        "bound": "2**53",
        "encoding": "decimal ASCII, one per line, LF endings with a trailing LF, in UTF-8, generation order",
        "commitment": "SHA-256 hex of the encoded bytes",
        "execution_identity": "v6-e8-exec-v1-<12 hex of SHA-256(structural digest hex, LF, commitment hex, LF)>",
    }


def test_counts_are_the_registered_ones() -> None:
    fields = decision.REGISTRATION["fields"]
    assert (matrix.F1.expected_matches, matrix.F2.expected_matches) == (3520, 704)
    assert (fields["F1"]["cells_per_condition"], fields["F2"]["cells_per_condition"]) == (3520, 704)
    assert matrix.matches_per_condition() == fields["cells_per_condition"] == 4224
    assert matrix.matches_total() == fields["cells_total"] == 16_896
    assert len(matrix.F1.pairs) * matrix.F1.orientations == fields["F1"]["ordered_pairs"] == 110
    assert len(matrix.F2.pairs) == fields["F2"]["mirrors"] == 11 and matrix.F2.orientations == 2


def test_the_fields_pair_the_registered_packages() -> None:
    primaries = tuple(family.package_id(m) for m in family.OPPONENTS)
    assert matrix.F1.agents == primaries and matrix.F1.pairing == "triangular"
    assert matrix.F1.pairs == tuple(combinations(primaries, 2))
    assert matrix.F2.pairs == tuple((family.package_id(m), family.package_id(m, "twin")) for m in family.OPPONENTS)
    assert set(matrix.F2.agents) == set(family.PACKAGES)


def test_the_conditions_and_final_ruleset_identifiers() -> None:
    assert [(c.condition_id, c.role, c.arm, c.parent, c.sensing_mode, c.sensing_window, c.disruption_slot_limit)
            for c in matrix.CONDITIONS] == [
        ("C8", "control", "primary", None, "passive", None, None),
        ("T8", "treatment", "primary", "C8", "active", 27, None),
        ("C8L", "control", "companion", None, "passive", None, 1),
        ("T8L", "treatment", "companion", "C8L", "active", 27, 1),
    ]
    # The final identifiers are the provisional ones of PR8 Sec 2.2, unchanged.
    registered = {c["id"]: c["ruleset_id"] for c in decision.REGISTRATION["conditions"]}
    assert {c.condition_id: c.ruleset_id for c in matrix.CONDITIONS} == registered == {
        "C8": "bytefray-rules-6-research-sensing-r32",
        "T8": "bytefray-rules-6-research-sensing-active-w27",
        "C8L": "bytefray-rules-6-research-disruption-slot1-sensing-r32",
        "T8L": "bytefray-rules-6-research-disruption-slot1-sensing-active-w27",
    }
    assert matrix.ARMS == {"primary": ("C8", "T8"), "companion": ("C8L", "T8L")}
    for item in matrix.CONDITIONS:
        assert resolve_ruleset_policy(item.ruleset_id).sensing_window == item.sensing_window
    matrix.verify_ruleset_registry()


def test_the_fixed_parameters_are_the_registered_ones() -> None:
    fixed = decision.REGISTRATION["fixed_across_conditions"]
    definition = matrix.structural_definition()
    assert (definition["arena_size"], definition["max_ticks"], definition["quota"], definition["chunk"]) == (
        fixed["arena_size"], fixed["tick_limit"], fixed["quota_Q"], fixed["chunk"]) == (512, 1000, 8, 2)
    assert definition["forbidden_request_overrides"] == [
        "scheduler_chunk_size", "scheduler_rotate_start", "kill_weight", "instr_per_tick"]


def test_the_census_is_committed_with_the_structure() -> None:
    census = matrix.structural_definition()["census"]
    assert census["primary"] == census["twin"] == ["EVADE8"]
    assert census["primary"] == list(decision.REGISTRATION["census"]["predicted"])
    assert census["criteria"] == ["E-1", "E-2", "E-3"]
    assert census["contrast"] == {"repeat": "REACQ8", "once": "RUSH8"}


def test_the_seat_strata_inputs_are_committed_with_the_structure() -> None:
    inputs = matrix.structural_definition()["seat_strata_inputs"]
    assert [tuple(unit) for unit in inputs["units"]] == list(decision.SEAT_UNITS)
    assert len(inputs["units"]) == 66
    assert sum(unit[0] == "pairing" for unit in inputs["units"]) == 55
    assert inputs["phase_sensitive_members"] == ["PACED8", "EVADE8", "ADAPT8", "STRESS8"]
    # 55 pairings less the 21 among the seven other members, plus four mirrors.
    assert (len(inputs["containing_phase_sensitive"]), len(inputs["not_containing_phase_sensitive"])) == (38, 28)
    sensitive = set(inputs["phase_sensitive_members"])
    for unit in inputs["not_containing_phase_sensitive"]:
        assert not sensitive & set(unit[1:])
    assert inputs["neutrality"] == {"predicate": "O-NEUTRAL", "sdom_lt": "9/10", "abs_gsb_le": "1/10"}
    assert "CQ8-5" in inputs["control_strata"]


def test_the_structure_binds_the_family_and_the_parent_goldens() -> None:
    definition = matrix.structural_definition()
    assert definition["package_fingerprints"] == family.fingerprints()
    assert definition["packages"] == {pid: list(slot) for pid, slot in sorted(family.PACKAGES.items())}
    assert definition["a8"] == list(decision.A8) and definition["opponents"] == list(decision.PI)
    assert definition["fixed_members"] == list(decision.PI_F)
    parent = definition["parent_freeze"]
    assert parent["commits"] == ["3f3f709", "2cfd4e8"] and parent["cases"] == 72
    assert parent["conditions"] == ["C8", "C8L"]


def test_a_drifted_fingerprint_changes_the_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    drifted = {pid: {**entry, "agent_py_sha256": "0" * 64} for pid, entry in family.fingerprints().items()}
    monkeypatch.setattr(family, "fingerprints", lambda: drifted)
    assert matrix.structural_digest() != matrix.STRUCTURAL_DIGEST
    with pytest.raises(matrix.MatrixDefinitionError):
        matrix.verify_frozen_matrix()


def test_a_changed_census_changes_the_identity_and_an_empty_one_halts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(family, "census", lambda role="primary": ())
    assert matrix.structural_digest() != matrix.STRUCTURAL_DIGEST
    monkeypatch.setattr(matrix, "STRUCTURAL_DIGEST", matrix.structural_digest())
    with pytest.raises(matrix.MatrixDefinitionError, match="empty or role-dependent census"):
        matrix.verify_frozen_matrix()


def test_a_drifted_ruleset_fails_the_registry_check(monkeypatch: pytest.MonkeyPatch) -> None:
    real = matrix.resolve_ruleset_policy

    def drifted(ruleset_id: str):  # type: ignore[no-untyped-def]
        policy = real(ruleset_id)
        if ruleset_id == matrix.condition("T8").ruleset_id:
            import dataclasses
            return dataclasses.replace(policy, scheduler_chunk_size=4)
        return policy

    monkeypatch.setattr(matrix, "resolve_ruleset_policy", drifted)
    with pytest.raises(matrix.MatrixDefinitionError, match="T8"):
        matrix.verify_ruleset_registry()


def test_lookups_fail_closed() -> None:
    with pytest.raises(KeyError):
        matrix.condition("T8+")
    with pytest.raises(KeyError):
        matrix.field("F3")
