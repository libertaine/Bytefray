"""The E8 family freeze (phase I8-4), v1.

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 3, 9
(step 1), 12 and 13; the implementation plan Sec 5.8 and 8 (step 2). It turns
the implemented, qualified family into an immutable experimental input. The
record pins, at the tooling commit:

* the 22 packages: their member and role, the SHA-256 of every ``agent.py``
  and ``agent.yaml``, and the one byte-identical policy source;
* the manifest parameter table as each package resolves it from disk, with the
  registered encoding, and each member's process declarations;
* the sets: Pi, Pi_F, A8 (H8-CHANNEL's frozen candidate set) and the
  phase-sensitive members;
* the census, re-derived from the manifests of both roles (CQ8-3);
* the compatibility classification: each package's static class, D8-9's
  result, and where each class may play (A1 containment, PR8 Sec 13);
* the final Ruleset identifiers of C8, T8, C8L and T8L;
* the structural matrix identity, which carries the census and the seat
  strata inputs (PR8 Sec 9, step 1);
* the RNG and behavior invariants, each with the tests that pin it;
* the qualification evidence: every E8 test file from I8-1 to I8-4, by
  digest, with its collected test count;
* the engine source the family was qualified against;
* the implementation notes the research lead asked to be recorded.

The identity is ``v6-e8-family-v1-<first 12 hex of the record digest>``, where
the digest is the SHA-256 of the canonical JSON of the record's body (sorted
keys, compact separators, UTF-8). File digests normalize CRLF to LF.

Loading fails closed unless the record's digest and identity recompute, the
pre-registration freeze loads, the structural matrix verifies, every pinned
file and package still has its pinned digest, every invariant's tests exist,
and everything else recomputes. Two facts are recorded but not recomputed on
load: the collected test counts (a function of the pinned test files) and the
engine source manifest. The engine is shared by later experiments, so, as
E6's analysis freeze did, the E8 runner checks it before execution
(``verify_engine_source``), not every load.

Nothing here generates a seed, runs a match or plays one family member against
another.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from battle_engine.agent_api import MatchContextV2

from tools.research.v6.e8 import (
    compatibility,
    decision,
    discipline,
    family,
    matrix,
    preregistration,
)
from tools.research.v6.e8 import preregistration_freeze as prereg_freeze

FREEZE_PATH = Path(__file__).with_name("family_freeze.json")
SCHEMA = "bytefray.v6.e8.family_freeze"
VERSION = 1
IDENTITY_PREFIX = "v6-e8-family-v1-"
ROOT = preregistration.REPOSITORY_ROOT
ENGINE_SOURCE_PATH = "engine/src"

#: The family's tooling, the structure and this freeze, and the D8-6 parent goldens.
PINNED_FILES: tuple[str, ...] = (
    "tools/research/v6/e8/family.py",
    "tools/research/v6/e8/discipline.py",
    "tools/research/v6/e8/compatibility.py",
    "tools/research/v6/e8/family_fingerprints.json",
    "tools/research/v6/e8/fixtures/README.md",
    "tools/research/v6/e8/matrix.py",
    "tools/research/v6/e8/family_freeze.py",
    "tools/research/v6/e8/parent_goldens.py",
    "tools/research/v6/e8/parent_goldens.json",
)
#: The qualification evidence: every E8 test file and harness, by the phase that built it. The
#: transcription, decision and freeze tests of I8-0 are pinned by the pre-registration freeze.
QUALIFICATION_FILES: Mapping[str, str] = MappingProxyType(
    {
        "engine/tests/test_v6_e8_parent_byte_identity.py": "I8-1",
        "engine/tests/_e8_sensing_harness.py": "I8-2",
        "engine/tests/test_v6_e8_sensing_semantics.py": "I8-2",
        "engine/tests/test_ruleset_v6_research_sensing_active.py": "I8-2",
        "engine/tests/test_v6_e8_sensing_context.py": "I8-2",
        "engine/tests/_e8_family_harness.py": "I8-3",
        "engine/tests/_e8_family_engine_harness.py": "I8-3",
        "engine/tests/test_v6_e8_family.py": "I8-3",
        "engine/tests/test_v6_e8_family_policy.py": "I8-3",
        "engine/tests/test_v6_e8_family_engine.py": "I8-3",
        "engine/tests/test_v6_e8_adapt8_freeze.py": "I8-3",
        "engine/tests/test_v6_e8_family_fixed_details.py": "I8-4",
        "engine/tests/test_v6_e8_matrix.py": "I8-4",
    }
)
IMPLEMENTATION_COMMITS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {"I8-1": ("3f3f709", "2cfd4e8"), "I8-2": ("e170895", "230fe71"), "I8-3": ("4b58d27", "621c95d")}
)

_FAMILY = "engine/tests/test_v6_e8_family.py"
_POLICY = "engine/tests/test_v6_e8_family_policy.py"
_ENGINE = "engine/tests/test_v6_e8_family_engine.py"
_ADAPT = "engine/tests/test_v6_e8_adapt8_freeze.py"
_FIXED = "engine/tests/test_v6_e8_family_fixed_details.py"
_SENSING = "engine/tests/test_v6_e8_sensing_semantics.py"
_CONTEXT = "engine/tests/test_v6_e8_sensing_context.py"
_ACTIVE = "engine/tests/test_ruleset_v6_research_sensing_active.py"
_PARENT = "engine/tests/test_v6_e8_parent_byte_identity.py"


def _pins(path: str, *names: str) -> list[str]:
    return [f"{path}::{name}" for name in names]


#: The RNG and behavior invariants frozen with the family, each with the tests that pin it.
INVARIANTS: tuple[Mapping[str, Any], ...] = (
    # -- RNG ---------------------------------------------------------------
    {"id": "RNG-1", "source": "plan P8-1",
     "statement": "At reset every package draws exactly two values from context.rng, in this order: "
                  "sigma = (-1, 1)[rng.randrange(2)], then the paint side = rng.randrange(2). Nothing else.",
     "pinned_by": _pins(_FAMILY, "test_reset_draws_exactly_sigma_then_the_paint_side")},
    {"id": "RNG-2", "source": "plan P8-2; PR8 Sec 2.5",
     "statement": "During play, tau = (-1, 1)[rng.randrange(2)] is drawn once, when a re-acquisition search "
                  "starts, in both modes.",
     "pinned_by": _pins(_POLICY, "test_verification_then_the_second_and_third_windows_precede_the_posture_steps",
                        "test_the_passive_search_moves_toward_each_center_and_is_exhausted_at_the_last")},
    {"id": "RNG-3", "source": "plan P8-2; PR8 R-11",
     "statement": "At each evasion, sigma_e = (-1, 1)[rng.randrange(2)], then m = rng.randint(8, 64), drawn "
                  "fresh for every evasion.",
     "pinned_by": [*_pins(_POLICY, "test_evade8_draws_fresh_for_every_evasion_and_repeats_on_every_hit"),
                   *_pins(_ENGINE, "test_evade8_evades_exactly_on_every_inferred_hit_with_fresh_draws")]},
    {"id": "RNG-4", "source": "PR8 Sec 3.3 and D8-3; PR6 Sec 3.2",
     "statement": "One policy source and one fixed draw order: a member's primary and twin packages consume "
                  "the stream identically and act identically, and no draw is made outside RNG-1 to RNG-3.",
     "pinned_by": [*_pins(_FAMILY, "test_primary_and_twin_packages_draw_and_act_identically"),
                   *_pins(_ENGINE, "test_primary_and_twin_packages_play_identically")]},
    {"id": "RNG-5", "source": "PR8 D8-9; PR6 D-5",
     "statement": "No package reads context.seed: randomness reaches the policy only through context.rng.",
     "pinned_by": _pins(_FAMILY, "test_every_package_passes_the_discipline_gate",
                        "test_the_gate_fails_every_planted_negative_control")},
    # -- Behavior ----------------------------------------------------------
    {"id": "BEH-1", "source": "plan Sec 5.1",
     "statement": "Every process declares reach arena // 2. SPLIT8 declares a sensor (share 1/4) and a "
                  "striker (share 3/4); every other member one process, share 1.",
     "pinned_by": _pins(_FAMILY, "test_declarations", "test_split8s_registered_sensor_and_shares_are_the_sources")},
    {"id": "BEH-2", "source": "PR8 Sec 3.2 and D8-9",
     "statement": "No member returns SENSE when sensing_window is None.",
     "pinned_by": _pins(_FAMILY, "test_no_member_ever_returns_sense_without_a_sensing_window",
                        "test_the_sense_helper_refuses_without_a_window")},
    {"id": "BEH-3", "source": "PR8 Sec 3.5, E-1",
     "statement": "Under active, only an inferred hit moves an anchor: EVADE8's evasion is the family's only "
                  "MOVE.",
     "pinned_by": _pins(_FAMILY, "test_under_active_only_an_inferred_hit_moves_an_anchor")},
    {"id": "BEH-4", "source": "PR8 Sec 2.5 and 3.2; judgment call 1",
     "statement": "Discovery senses c_k = own_core_base + sigma(91 + 55k), k = 0..6, stops at the first result "
                  "with an enemy anchor, and restarts at c_0 after seven empty results. Each later return to "
                  "nothing known is a new episode that restarts at c_0. PACED8 acquires on odd callback "
                  "indexes only. Under passive, acquisition is E6's MOVE 64 * sigma sweep.",
     "pinned_by": [*_pins(_POLICY, "test_the_seven_discovery_windows_tile_the_registered_arc",
                          "test_active_discovery_senses_c0_to_c6_then_restarts_at_c0",
                          "test_discovery_stops_at_the_first_result_with_an_enemy_anchor",
                          "test_a_later_discovery_traversal_starts_again_at_c0",
                          "test_paced_acquisition_only_on_odd_callback_indexes",
                          "test_passive_spatial_fast_is_e6s_full_stride_sweep"),
                   *_pins(_ENGINE, "test_active_discovery_senses_the_registered_centers_until_the_first_find",
                          "test_passive_discovery_is_the_full_stride_sweep_until_something_is_visible")]},
    {"id": "BEH-5", "source": "PR8 Sec 3.2; judgment call 2",
     "statement": "First discovery happens on the callback that delivers the SENSE result, never on the one that "
                  "issued it. If that is the entrant's first callback of a tick, repeat and adaptive members "
                  "verify there (under active, a SENSE centered on the lowest known address); otherwise "
                  "verification waits for the next tick's first callback. once members never verify.",
     "pinned_by": _pins(_FIXED, "test_a_first_discovery_delivered_at_a_ticks_first_callback_is_verified_there",
                        "test_the_delivery_callback_picks_the_lowest_of_several_found",
                        "test_adapt8s_discovery_result_is_not_a_verification_observation",
                        "test_a_once_member_does_not_verify_at_the_delivery_callback",
                        "test_a_first_discovery_delivered_at_a_later_callback_waits_for_the_next_tick",
                        "test_engine_a_first_discovery_delivered_at_tick_twos_first_callback")},
    {"id": "BEH-6", "source": "PR8 Sec 2.5 and 3.2, KU-1 to KU-9",
     "statement": "Knowledge: under passive the known set is the current visible set; under active, remembered "
                  "SENSE results updated only inside the sensed window; missing addresses are serviced in "
                  "ascending order and replaced by the nearest returned address, the lower on a tie; a refused "
                  "SENSE changes nothing.",
     "pinned_by": _pins(_POLICY, "test_ku2_every_returned_address_becomes_known",
                        "test_ku1_ku3_ku4_only_the_sensed_window_is_updated",
                        "test_ku7_a_missing_address_is_replaced_by_the_nearest_returned_one",
                        "test_ku7_a_tie_goes_to_the_lower_address",
                        "test_ku6_missing_addresses_are_serviced_in_ascending_order",
                        "test_ku8_ku9_verification_centers_on_the_lowest_numeric_address",
                        "test_ku5_passive_tracked_addresses_absent_from_view_become_missing",
                        "test_ku5_ku7_passive_a_vanished_anchor_is_replaced_by_a_visible_one",
                        "test_a_refused_sense_changes_nothing",
                        "test_passive_knowledge_is_only_the_current_visible_set",
                        "test_active_knowledge_persists_until_a_sense_replaces_it")},
    {"id": "BEH-7", "source": "PR8 Sec 3.2, Revision 3 (K-1)",
     "statement": "Initial acquisition ends once the entrant confirms the enemy core; SPLIT8's sensor never moves "
                  "again after confirmation, and its striker never moves.",
     "pinned_by": [*_pins(_POLICY, "test_split8s_sensor_sweeps_while_the_core_is_unconfirmed_and_nothing_is_visible",
                          "test_split8s_sensor_never_moves_again_once_its_entrant_confirms_the_core",
                          "test_split8s_striker_never_moves_or_acquires",
                          "test_split8s_sensor_under_active_stops_sensing_once_anything_is_known",
                          "test_attack_members_never_reach_acquisition_once_the_core_is_confirmed"),
                   *_pins(_ENGINE, "test_k1_split8s_sensor_never_moves_once_its_entrant_confirms_the_core")]},
    {"id": "BEH-8", "source": "PR8 Sec 3.2, the registered channel difference (K-4)",
     "statement": "Under passive, GUARD8 and EVADE8 resume sweeping when they lose sight; under active, a "
                  "remembered anchor is never re-sensed by a once member.",
     "pinned_by": [*_pins(_POLICY, "test_k4_passive_guard_members_resume_sweeping_when_they_lose_sight",
                          "test_k4_active_guard_members_never_re_sense_a_remembered_anchor",
                          "test_k4_evade8_sweeps_after_its_own_evasion_under_passive"),
                   *_pins(_ENGINE, "test_k4_guard_members_resweep_on_lost_sight_only_under_passive")]},
    {"id": "BEH-9", "source": "PR8 Sec 3.2, RP-1 to RP-7",
     "statement": "A re-acquisition search in progress takes precedence over the posture steps until replacement "
                  "or exhaustion, continues on a later tick's first offer, and never overrides a member-level "
                  "step. Under active its windows are a, a + 46 tau, a - 46 tau; under passive it MOVEs toward "
                  "them, at most 64 per MOVE.",
     "pinned_by": [*_pins(_POLICY, "test_verification_then_the_second_and_third_windows_precede_the_posture_steps",
                          "test_the_search_ends_on_replacement_by_the_second_window",
                          "test_rp2_a_search_continues_on_the_first_offer_of_a_later_tick",
                          "test_the_search_takes_precedence_over_core_writes",
                          "test_rp5_a_pending_evasion_keeps_its_priority_over_a_search",
                          "test_a_once_member_neither_verifies_nor_searches",
                          "test_the_passive_search_moves_toward_each_center_and_is_exhausted_at_the_last",
                          "test_the_passive_search_ends_on_the_first_visible_anchor"),
                   *_pins(_ENGINE, "test_rp2_reacq8s_search_reaches_its_third_window",
                          "test_reacq8s_search_is_exhausted_after_its_third_empty_window",
                          "test_passive_reacq8_moves_toward_the_registered_centers")]},
    {"id": "BEH-10", "source": "PR8 Sec 3.2 and R-8; judgment call 3",
     "statement": "ADAPT8 switches to once at the second consecutive verification observation confirming its "
                  "selected address a, the lowest known (active) or tracked (passive) address. An unobserved "
                  "tick neither advances nor resets the count; a found missing at any callback resets it; "
                  "another known address found missing does not, unless it is a.",
     "pinned_by": [*_pins(_POLICY, "test_adapt8_active_switches_at_the_second_consecutive_confirmation",
                          "test_adapt8_active_an_unobserved_tick_neither_advances_nor_resets_the_count",
                          "test_adapt8_active_a_verification_delivered_after_suppression_still_counts",
                          "test_adapt8_active_an_observed_relocation_resets_the_count",
                          "test_adapt8_active_a_first_callback_during_a_search_is_not_a_verification",
                          "test_adapt8_passive_the_first_offer_of_a_tick_is_the_observation",
                          "test_adapt8_passive_a_relocation_at_any_callback_resets_and_unobserved_ticks_do_nothing",
                          "test_adapt8_passive_before_its_switch_searches_like_reacq8"),
                   *_pins(_ADAPT, "test_adapt8_freeze", "test_the_freeze_matrix_covers_every_registered_case"),
                   *_pins(_FIXED, "test_adapt8_active_another_known_anchor_missing_does_not_reset_the_count",
                          "test_adapt8_active_the_selected_anchor_missing_resets_the_count",
                          "test_adapt8_active_a_higher_anchor_that_becomes_a_is_then_the_one_counted",
                          "test_adapt8_passive_another_tracked_anchor_vanishing_does_not_reset_the_count",
                          "test_adapt8_passive_the_selected_anchor_vanishing_resets_the_count")]},
    {"id": "BEH-11", "source": "PR8 Sec 3.2; plan P8-5",
     "statement": "EVADE8 infers a hit at its first callback of a tick if a whole tick passed without a callback "
                  "or it received fewer than 8 callbacks in its most recent tick with any; never at its first "
                  "callback of the match. It evades on every inferred hit.",
     "pinned_by": [*_pins(_POLICY, "test_evade8_never_infers_a_hit_at_its_first_callback_of_the_match",
                          "test_evade8_infers_a_hit_from_a_tick_without_a_callback",
                          "test_evade8_infers_a_hit_from_fewer_than_eight_callbacks",
                          "test_evade8_infers_nothing_after_a_full_tick"),
                   *_pins(_ENGINE, "test_evade8_evades_exactly_on_every_inferred_hit_with_fresh_draws")]},
    {"id": "BEH-12", "source": "PR8 Sec 3.2; plan P8-6",
     "statement": "STRESS8 READs own-core cell (t - 1) mod 8 at callback index 1 of each tick and repairs a "
                  "damaged cell with the core beacon at its next action, without moving the guard cursor; the "
                  "check's result reaches the same tick's second callback under both parents.",
     "pinned_by": [*_pins(_POLICY, "test_stress8_checks_own_core_cell_t_minus_1_mod_8_at_each_first_callback",
                          "test_stress8_repairs_a_damaged_checked_cell_with_the_core_beacon_next",
                          "test_stress8_drops_a_stale_obligation_at_a_new_ticks_first_callback",
                          "test_stress8_a_tick_without_a_callback_skips_its_cell",
                          "test_stress8_disrupts_a_known_anchor_after_its_check"),
                   *_pins(_ENGINE, "test_stress8_checks_its_core_cell_each_tick_and_repairs_damage_with_the_beacon",
                          "test_p8_6_the_checks_result_always_reaches_the_same_ticks_second_callback")]},
    {"id": "BEH-13", "source": "PR8 CQ8-2",
     "statement": "Under the controls RUSH8 and REACQ8 act identically until REACQ8's first re-acquisition "
                  "trigger, and GUARD8 and EVADE8 until EVADE8's first inferred hit.",
     "pinned_by": [*_pins(_POLICY, "test_cq8_2_rush8_and_reacq8_agree_until_the_first_trigger",
                          "test_guard8_and_evade8_agree_until_the_first_inferred_hit"),
                   *_pins(_ENGINE, "test_cq8_2_rush8_and_reacq8_are_identical_until_reacq8s_first_trigger",
                          "test_cq8_2_guard8_and_evade8_are_identical_until_the_first_inferred_hit")]},
    {"id": "BEH-14", "source": "PR8 D8-3",
     "statement": "Without information LURK8 and GREED8 act identically, and members without acquisition never "
                  "move or sense.",
     "pinned_by": [*_pins(_POLICY, "test_lurk8_and_greed8_act_identically_without_information",
                          "test_members_without_acquisition_never_move_or_sense"),
                   *_pins(_ENGINE, "test_d8_3_lurk8_and_greed8_records_are_identical_under_the_treatments")]},
    {"id": "BEH-15", "source": "PR8 Sec 3.2; E6-A1 C-1 to C-3",
     "statement": "E6's posture, verification-READ, core-cursor and adoption semantics, as corrected by E6-A1, "
                  "are carried over unchanged; under C8 and C8L, RUSH8, PACED8, STEALTH8, LURK8 and GREED8 "
                  "reproduce E6's members decision for decision.",
     "pinned_by": [*_pins(_POLICY, "test_e6_a_single_far_anchor_at_seat_as_tick_one_first_callback_is_adopted",
                          "test_e6_seat_b_and_later_callbacks_never_adopt",
                          "test_e6_verification_grows_the_run_down_and_up_and_confirms_eight",
                          "test_e6_an_overwritten_anchor_on_core_cell_0_stands_in_for_it",
                          "test_e6_the_core_cursor_rotates_the_omitted_cell_across_ticks",
                          "test_e6_guard_disrupts_on_sight_and_otherwise_repairs_cyclically_across_ticks",
                          "test_e6_paint_writes_outward_alternating_sides_and_covers_504_cells",
                          "test_e6_the_read_search_probes_the_whole_arc_in_order_and_never_moves"),
                   *_pins(_ENGINE, "test_under_the_controls_the_attack_and_paint_members_are_e6s")]},
    {"id": "BEH-16", "source": "fixed detail 14",
     "statement": "A package given no parameters, which only a validation dry run produces, behaves as GREED8.",
     "pinned_by": _pins(_FIXED, "test_a_package_without_parameters_behaves_as_greed8")},
    {"id": "BEH-17", "source": "PR8 Sec 13 (A1 containment) and D8-14",
     "statement": "Every member plays legally under all four conditions; a context-gated package is refused "
                  "before the match off C8, T8, C8L and T8L; an ungated SENSE package plays only under T8 and "
                  "T8L.",
     "pinned_by": [*_pins(_ENGINE, "test_every_member_plays_legally_and_contained",
                          "test_a_family_package_is_refused_before_any_match_off_the_four_conditions",
                          "test_an_ungated_sense_package_plays_only_under_the_treatments"),
                   *_pins(_FAMILY, "test_the_static_classes", "test_the_accept_reject_matrix_over_every_registered_ruleset",
                          "test_require_compatible_refuses_before_the_match")]},
    {"id": "BEH-18", "source": "PR8 Sec 6.3 (decisive-tick parity)",
     "statement": "Seat A moves first on tick 1 under every E8 condition.",
     "pinned_by": _pins(_ENGINE, "test_seat_a_moves_first_on_tick_one_under_every_e8_condition")},
    # -- The engine semantics the family was qualified on (I8-1, I8-2) ------
    {"id": "ENG-1", "source": "PR8 Sec 2.3 and 2.4",
     "statement": "SENSE's window is inclusive at 27 and covers 55 cells across the wrap; its result is the "
                  "ascending, distinct tuple of other live entrants' anchors; it costs one offer and changes "
                  "nothing in the match.",
     "pinned_by": _pins(_SENSING, "test_the_window_is_inclusive_at_exactly_27", "test_the_window_covers_exactly_55_cells",
                        "test_distance_is_circular_across_the_wrap",
                        "test_the_result_is_ascending_and_distinct_with_co_located_anchors_once",
                        "test_only_other_live_entrants_are_sensed", "test_one_sense_is_one_offer",
                        "test_sense_changes_nothing_in_the_match", "test_the_sensed_entrant_learns_nothing",
                        "test_under_active_the_passive_visible_set_is_empty")},
    {"id": "ENG-2", "source": "PR8 Sec 10, the delivery tests",
     "statement": "A SENSE result is delivered at the acting process's next callback, after suppression "
                  "included; with no later callback, the authoritative record stands.",
     "pinned_by": _pins(_SENSING, "test_delivery_at_the_next_offer_in_the_same_chunk", "test_delivery_at_the_next_tick",
                        "test_delivery_survives_suppression_for_the_rest_of_the_tick",
                        "test_no_later_callback_when_the_entrant_is_eliminated",
                        "test_no_later_callback_at_the_tick_limit", "test_delivery_is_per_process")},
    {"id": "ENG-3", "source": "PR8 Sec 10, presence and serialization (Revisions 4 and 5)",
     "statement": "The E8 trace fields are present exactly where registered, absent and null are distinct, and "
                  "a non-SENSE or control record's bytes are unchanged.",
     "pinned_by": [*_pins(_SENSING, "test_a_control_trace_carries_no_e8_field",
                          "test_an_out_of_reach_sense_is_an_ordinary_refusal_with_explicit_nulls",
                          "test_the_serialized_bytes_of_a_non_sense_record_are_unchanged_by_the_new_fields"),
                   *_pins(_CONTEXT, "test_every_registered_ruleset_delivers_its_own_window")]},
    {"id": "ENG-4", "source": "PR8 D8-6",
     "statement": "C8 and C8L reproduce their pre-E8 parent goldens byte for byte.",
     "pinned_by": _pins(_PARENT, "test_parent_reproduces_its_pre_e8_golden")},
)

#: The implementation facts the research lead asked to be recorded (2026-09-30), and I8-4's own.
IMPLEMENTATION_NOTES: tuple[Mapping[str, str], ...] = (
    {"id": "N8-1", "date": "2026-09-30", "phase": "I8-2",
     "text": "The arena check ProcessMatchController._sensing_window_problem (2 x 27 < arena_size) is defensive "
             "validation introduced by I8-2. It is not a registered mechanic and not an E8 finding, and it applies "
             "only under sensing_mode = \"active\". E8 runs at arena 512, so no registered cell is affected. The "
             "pre-registration is not reopened for it."},
    {"id": "N8-2", "date": "2026-09-30", "phase": "I8-2",
     "text": "A forfeit record keeps previous_sense_anchors: the reflection was delivered before the action failed."},
    {"id": "N8-3", "date": "2026-09-30", "phase": "I8-2",
     "text": "Under T8 and T8L, detection_radius = 32 is still delivered but is inert. sensing_window is the "
             "authoritative indicator of active sensing."},
    {"id": "N8-4", "date": "2026-09-30", "phase": "I8-2",
     "text": "Hand-built test entrants get a separate controller rejection of an unavailable SENSE."},
    {"id": "N8-5", "date": "2026-09-30", "phase": "I8-3", "approved": "judgment call 1",
     "text": "Each return to nothing known, with discovery required, is a new discovery episode: its traversal "
             "restarts at c_0, and no cursor is carried over from an earlier, exhausted episode."},
    {"id": "N8-6", "date": "2026-09-30", "phase": "I8-3", "approved": "judgment call 2",
     "text": "\"After first discovery\" includes the discovering callback, which is the callback on which the "
             "prior SENSE result is delivered to the agent through previous_sense_anchors, not the callback that "
             "issued the SENSE. When that delivery callback is the entrant's first callback of a tick, a repeat or "
             "adaptive member verifies there; under active, the verification is a SENSE centered on the lowest "
             "known address (PR8 Sec 3.2, KU-8). At any other delivery callback the posture steps apply."},
    {"id": "N8-7", "date": "2026-09-30", "phase": "I8-3", "approved": "judgment call 3",
     "text": "ADAPT8 tracks the lowest selected address a. Its quiet count is about the persistence of that "
             "selected anchor: another SPLIT8 anchor moving does not reset it unless it becomes the selected a. "
             "This scope is to be stated when ADAPT8 is interpreted against SPLIT8. The family is not changed."},
    {"id": "N8-8", "date": "2026-09-30", "phase": "I8-3", "approved": "P8-6 finding",
     "text": "P8-6's same-chunk rationale applies to whole-tick disruption but not universally to λ=1. "
             "Qualification establishes the intended same-tick result-delivery behavior under both parents, so no "
             "registered family behavior changes."},
    {"id": "N8-9", "date": "2026-09-30", "phase": "I8-3",
     "text": "tools/research/v6/e8/__init__.py still describes the package as it stood at I8-0. The pre-registration "
             "freeze pins it, so it is left untouched. Its wording is stale descriptive text, not family semantics."},
    {"id": "N8-10", "date": "2026-09-30", "phase": "I8-3", "approved": "accepted without action",
     "text": "A possible EVADE8 start-up effect (a scripted evader whose first evasion came after ADAPT8's second "
             "verification let ADAPT8 switch at tick 3) remains unprobed against EVADE8. The frozen experiment may "
             "discover it. Neither EVADE8 nor ADAPT8 is tuned around it."},
    {"id": "N8-11", "date": "2026-09-30", "phase": "I8-3", "approved": "accepted without action",
     "text": "A passive searcher whose first center is an anchor's last address can park on the opponent's core "
             "cell 0. That is a consequence of the registered chase geometry, not something to repair."},
    {"id": "N8-12", "date": "2026-09-30", "phase": "I8-3", "approved": "accepted without action",
     "text": "A disruption after the victim's last offer of a tick costs nothing, and under T8L a search started by "
             "a verification does not carry into another tick. Both follow from the parent scheduler and "
             "disruption semantics."},
    {"id": "N8-13", "date": "2026-09-30", "phase": "I8-3",
     "text": "The pre-match compatibility gate is compatibility.require_compatible. Calling it before every matrix "
             "match is owed by the I8-5 runner (run_e8.py)."},
    {"id": "N8-14", "date": "2026-10-01", "phase": "I8-4",
     "text": "The fixtures README says each fixed detail is pinned by a test. At the family freeze, judgment call "
             "2's first-of-tick delivery case, judgment call 3's two-anchor case and fixed detail 14 had no test of "
             "their own. test_v6_e8_family_fixed_details.py pins them. The policy source is unchanged."},
)


class FreezeError(RuntimeError):
    """The family freeze record does not recompute, or a pinned input changed."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_digest(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(body)).hexdigest()


def identity(digest: str) -> str:
    return IDENTITY_PREFIX + digest[:12]


def engine_source() -> dict[str, Any]:
    """The tracked engine source tree, as a manifest of LF-normalized file digests."""
    listed = subprocess.run(["git", "ls-files", ENGINE_SOURCE_PATH], cwd=ROOT, capture_output=True, text=True,
                            check=True).stdout.split()
    lines = "".join(f"{preregistration.file_digest(ROOT / path)}  {path}\n" for path in sorted(listed))
    return {"path": ENGINE_SOURCE_PATH, "files": len(listed),
            "sha256": hashlib.sha256(lines.encode("utf-8")).hexdigest()}


def _policy_module(pid: str) -> Any:
    spec = importlib.util.spec_from_file_location(f"e8_family_freeze_{pid}", family.FIXTURE_DIR / pid / "agent.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def declarations() -> dict[str, list[list[Any]]]:
    """Each package's process declarations at arena 512, as its manifest's parameters configure it."""
    out: dict[str, list[list[Any]]] = {}
    for pid in sorted(family.PACKAGES):
        agent = _policy_module(pid).create_agent()
        # rng and seed are inert here: declarations depend only on the parameters and the arena.
        agent.reset(MatchContextV2(agent_id="A", seed=0, arena_size=matrix.ARENA_SIZE, tick_limit=matrix.MAX_TICKS,
                                   rng=random.Random(0), parameters=MappingProxyType(family.resolved_parameters(pid)),
                                   detection_radius=matrix.DETECTION_RADIUS, sensing_window=None))
        out[pid] = [[d.id, d.reach, d.share] for d in agent.declare_processes()]
    return out


def compatibility_classification() -> dict[str, Any]:
    packages = {pid: family.FIXTURE_DIR / pid for pid in sorted(family.PACKAGES)}
    violations = discipline.check_packages(packages.values())
    classes = {pid: discipline.classify_package(path) for pid, path in packages.items()}
    return {
        "static_classes": classes,
        "d8_9_violations": {pid: [str(v) for v in found] for pid, found in sorted(violations.items()) if found},
        "accepted": {cls: sorted(compatibility.ACCEPTED[cls]) for cls in (discipline.CONTEXT_GATED, discipline.UNGATED)},
        "condition_rulesets": dict(compatibility.CONDITION_RULESETS),
        "compatible_conditions": [
            condition for condition, ruleset_id in compatibility.CONDITION_RULESETS.items()
            if all(compatibility.compatible(cls, ruleset_id) for cls in classes.values())
        ],
    }


def _test_names(path: str) -> set[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")}


def invariant_problems() -> list[str]:
    """Every invariant names at least one test, and every named test exists in a pinned qualification file."""
    problems: list[str] = []
    names = {path: _test_names(path) for path in QUALIFICATION_FILES}
    for invariant in INVARIANTS:
        if not invariant["pinned_by"]:
            problems.append(f"{invariant['id']} names no test")
        for pin in invariant["pinned_by"]:
            path, _, name = pin.partition("::")
            if path not in names:
                problems.append(f"{invariant['id']}: {path} is not a pinned qualification file")
            elif name not in names[path]:
                problems.append(f"{invariant['id']}: no test {name} in {path}")
    return problems


def collected_counts() -> dict[str, int]:
    """pytest's collected test count for each qualification file (at write time only)."""
    tests = [path for path in QUALIFICATION_FILES if Path(path).name.startswith("test_")]
    output = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", *tests], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout
    counts = dict.fromkeys(tests, 0)
    for line in output.splitlines():
        line = line.strip().replace("\\", "/")
        if "::" in line:  # one node ID per line (a single -q)
            path = line.partition("::")[0]
            if path in counts:
                counts[path] += 1
        elif ": " in line:
            path, _, number = line.rpartition(": ")  # per-file totals (-q twice; pytest.ini adds one)
            if path in counts and number.isdigit():
                counts[path] = int(number)
    if not all(counts.values()):
        raise FreezeError(f"pytest collected nothing from {[p for p, n in counts.items() if not n]}")
    return counts


def body(tooling_commit: str, *, collected: Mapping[str, int], engine: Mapping[str, Any]) -> dict[str, Any]:
    """The record's body, recomputed from the live checkout. ``collected`` and ``engine`` are recorded facts."""
    prereg = prereg_freeze.load_freeze()
    fingerprints = family.fingerprints()
    policy_sources = sorted({entry["agent_py_sha256"] for entry in fingerprints.values()})
    registration_conditions = {c["id"]: c for c in decision.REGISTRATION["conditions"]}
    return {
        "experiment": "E8",
        "phase": "I8-4",
        "tooling_commit": tooling_commit,
        "implementation_commits": {phase: list(commits) for phase, commits in IMPLEMENTATION_COMMITS.items()},
        "preregistration_freeze": {
            "identity": prereg["identity"],
            "record": "tools/research/v6/e8/preregistration_freeze_v4.json",
            "record_sha256": preregistration.file_digest(prereg_freeze.FREEZE_PATH),
        },
        "structural_matrix": {"identity": matrix.matrix_id(), "digest": matrix.STRUCTURAL_DIGEST,
                              "matches_per_condition": matrix.matches_per_condition(),
                              "matches_total": matrix.matches_total()},
        "ruleset_identifiers": {
            c.condition_id: {"ruleset_id": c.ruleset_id,
                             "registered_as_provisional": bool(registration_conditions[c.condition_id]["provisional"])}
            for c in matrix.CONDITIONS
        },
        "policy_source": {"sha256": policy_sources, "packages": len(fingerprints)},
        "packages": fingerprints,
        "parameters": {
            "registered_encoding": [[parameter, registered, manifest]
                                    for (parameter, registered), manifest in family.REGISTERED_ENCODING.items()],
            "members": {member: dict(values) for member, values in family.MEMBERS.items()},
            "resolved_from_manifests": {pid: family.resolved_parameters(pid) for pid in sorted(family.PACKAGES)},
        },
        "declarations": declarations(),
        "sets": {"pi": list(family.OPPONENTS), "pi_f": list(family.FIXED_MEMBERS), "a8": list(family.A8),
                 "phase_sensitive": list(decision.PHASE_SENSITIVE)},
        "census": {"primary": list(family.census("primary")), "twin": list(family.census("twin")),
                   "prediction": list(decision.REGISTRATION["census"]["predicted"])},
        "compatibility": compatibility_classification(),
        "invariants": [dict(invariant) for invariant in INVARIANTS],
        "qualification": {
            path: {"phase": phase, "sha256": preregistration.file_digest(ROOT / path), "collected": collected.get(path)}
            for path, phase in QUALIFICATION_FILES.items()
        },
        "files": {path: preregistration.file_digest(ROOT / path) for path in PINNED_FILES},
        "engine_source": dict(engine),
        "implementation_notes": [dict(note) for note in IMPLEMENTATION_NOTES],
        "exposure": {"seeds": "none exist", "matrix_cells": "none run",
                     "family_vs_family_matches": "none played"},
    }


def _checks(content: Mapping[str, Any]) -> list[str]:
    """What must hold of a body, beyond recomputing: the frozen facts the freeze exists to guarantee."""
    problems = invariant_problems()
    if len(content["policy_source"]["sha256"]) != 1:
        problems.append("the 22 packages do not share one byte-identical policy source")
    stored = json.loads(family.FINGERPRINTS_PATH.read_text(encoding="utf-8"))
    if stored != content["packages"]:
        problems.append("family_fingerprints.json differs from the packages on disk")
    census = content["census"]
    if not census["primary"] or census["primary"] != census["twin"]:
        problems.append(f"the census is empty or differs by role: {census}")
    if content["sets"]["a8"] != list(decision.A8) or content["sets"]["pi"] != list(decision.PI) \
            or content["sets"]["pi_f"] != list(decision.PI_F):
        problems.append("the family's sets differ from the transcription's")
    by_member: dict[str, list[dict[str, Any]]] = {}
    for pid, values in content["parameters"]["resolved_from_manifests"].items():
        by_member.setdefault(family.PACKAGES[pid][0], []).append(values)
    for member, settings in by_member.items():
        if any(values != dict(family.MEMBERS[member]) for values in settings):
            problems.append(f"{member}'s manifests do not declare its member parameters")
    compat = content["compatibility"]
    if compat["d8_9_violations"]:
        problems.append(f"D8-9 fails: {compat['d8_9_violations']}")
    if set(compat["static_classes"].values()) != {discipline.CONTEXT_GATED}:
        problems.append("a family package is not context-gated")
    if compat["compatible_conditions"] != ["C8", "T8", "C8L", "T8L"]:
        problems.append(f"the family is compatible with {compat['compatible_conditions']}, not the four conditions")
    return problems


def record(tooling_commit: str, *, collected: Mapping[str, int] | None = None) -> dict[str, Any]:
    content = body(tooling_commit, collected=collected if collected is not None else collected_counts(),
                   engine=engine_source())
    problems = _checks(content)
    if problems:
        raise FreezeError("E8 family freeze refused: " + "; ".join(problems))
    digest = record_digest(content)
    return {"schema": SCHEMA, "version": VERSION, "identity": identity(digest), "digest": digest, "body": content}


def load_freeze(path: Path = FREEZE_PATH) -> Mapping[str, Any]:
    """The frozen record, deeply immutable; fails closed on any drift."""
    if not path.is_file():
        raise FreezeError(f"No E8 family freeze record at {path}; freeze the family first (I8-4).")
    stored = preregistration.parse(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    if stored.get("schema") != SCHEMA or stored.get("version") != VERSION:
        problems.append(f"not an E8 family freeze record, version {VERSION}")
    digest = record_digest(stored["body"])
    if digest != stored["digest"]:
        problems.append(f"the record's body digest {digest} is not the stored {stored['digest']}")
    if identity(stored["digest"]) != stored["identity"]:
        problems.append(f"the identity {stored['identity']} does not follow from the digest")
    try:
        matrix.verify_frozen_matrix()
    except matrix.MatrixDefinitionError as error:
        problems.append(str(error))
    frozen_body = stored["body"]
    collected = {path: entry["collected"] for path, entry in frozen_body["qualification"].items()}
    live = body(frozen_body["tooling_commit"], collected=collected, engine=frozen_body["engine_source"])
    for key in sorted(set(live) | set(frozen_body)):
        if live.get(key) != frozen_body.get(key):
            problems.append(f"{key}: live {live.get(key)!r} != frozen {frozen_body.get(key)!r}")
    problems += _checks(live)
    if problems:
        raise FreezeError("E8 family freeze: " + "; ".join(problems))
    frozen: Mapping[str, Any] = preregistration.freeze(stored)
    return frozen


def verify_engine_source(frozen: Mapping[str, Any]) -> None:
    """Before any E8 match runs: the engine source equals the one the family was qualified against."""
    live = engine_source()
    if live != dict(frozen["body"]["engine_source"]):
        raise FreezeError(f"the engine source {live} differs from the qualified {dict(frozen['body']['engine_source'])}")


if __name__ == "__main__":  # pragma: no cover - the one-time write, at I8-4
    if len(sys.argv) != 3 or sys.argv[1] != "--write":
        raise SystemExit("usage: python -m tools.research.v6.e8.family_freeze --write <tooling commit>")
    if FREEZE_PATH.exists():
        raise SystemExit(f"{FREEZE_PATH} exists; a freeze is written once")
    FREEZE_PATH.write_text(json.dumps(record(sys.argv[2]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                           newline="\n")
    print(json.loads(FREEZE_PATH.read_text(encoding="utf-8"))["identity"])
