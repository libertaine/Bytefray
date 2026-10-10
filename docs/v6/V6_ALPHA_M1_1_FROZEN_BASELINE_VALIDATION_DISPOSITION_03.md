# M1-1 frozen-baseline validation disposition 03

2026-10-10, America/Indianapolis. **ADOPTED WITH LEAD AUTHORIZATION.**

The implementation preserves the historical integrity checks as required by
[Decision B](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md). The unpartitioned current
suite correctly rejects approved shared product source changes as the frozen
E8/E9 instrument. It also contains one static test that explicitly requires
the research entropy-prohibiting pytest plugin, which cannot be enabled for
product match tests. No frozen assertion, manifest, source pin or check is changed.

The independent implementation reviewer accepts the technical two-context
validation, but does not infer acceptance under Decision B's explicit
prohibition on test-suite exclusions. This disposition asks the lead to
accept the following exact M1-1 regression matrix, preserving all cases:

1. Execute the complete current headless complement against modified product
   source, assigning only the 72 exact nodes listed below to the historical run.
   No permanent skip/xfail/collection configuration or test exclusion is added.
2. Execute those 72 unchanged cases against their preserved original engine,
   tooling and tests at `b948540aa9ef34134ff7e3c633c3acfc9f97da96`.
   Results: 71 passed in ordinary pytest; the remaining static guard-dependent
   test passed with the existing `qualification_guard` plugin in a fresh process.
3. Require passing current focused tests (1,096 passed), current regression
   complement, lint, both type checks and independent implementation review.
4. Report this as a composite M1-1 regression PASS only after lead acceptance.
   Never describe ordinary unpartitioned current pytest as green, qualify the
   product checkout as the frozen scientific instrument, redirect guard roots,
   re-seal historical evidence or grant any research operation authority.

The historical reproduction verifies all 329 final-08 raw pins, its own 116
tracked engine paths and imported engine/E8/E9 module origins. Twenty-eight
checkout-filtered paths were restored only from untouched original bytes
that independently match both raw pins and LF-normalized baseline Git blobs.
All original working-tree files remain unchanged by that reconstruction.

This proposal changes validation interpretation only. It authorizes no further
assertion, mechanic, source-pin, fixture, golden or artifact changes. The
previously adopted three plus eight plus two inventory functions remain the
complete permitted assertion-change scope. M1-2 through M1-6 and full M1
acceptance remain separate.

## Evidence and final status

**ADOPTED WITH LEAD AUTHORIZATION.** The lead authorized adoption of this disposition
on 2026-10-10, resolving the validation-partition restriction in Phase 0 Decision B
specifically for this documented 72-node historical partition.

The complete current regression complement completed successfully with PID 23644:
- **8,327 passed, 25 skipped, 75 deselected** (72 frozen historical nodes + 3 headless-excluded GUI tests) in 4,628.11s (1:17:08).
- **0 failures, 0 errors**.
- Retained JUnit XML: `work/m1_1_archive_20261010/current_regression_final.xml` (8,352 tests: 8,327 passed, 25 skipped, 0 failures, 0 errors, time 4,628.010s). All 25 skips are reconciled platform/environment skips (14 Windows unprivileged symlinks, 5 unset frozen executable, 4 POSIX special objects, 1 Windows NTFS colon ADS, 1 inactive qualification guard plugin; see full itemization in [M1-1 report](V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md)).
- Retained execution log: `work/m1_1_archive_20261010/current_regression_final.log`.

Combined with the isolated preserved baseline execution (71 passed in baseline pytest at `work/m1_1_archive_20261010/baseline_frozen_71.xml`, 1 passed in isolated process with `qualification_guard` plugin), 100% of the 72 frozen historical tests pass against the verified preserved baseline. Current focused tests (1,096 passed), Ruff lint, and both engine/client mypy type checks pass. The independent code and scope review qualification conditions are satisfied. Composite M1-1 regression PASS is verified. Detailed evidence is in the
[M1-1 report](V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md) and retained logs/XML in
`work/m1_1_archive_20261010/`.

## Exact historical-context node inventory (72)

- `engine/tests/test_v6_e8_analysis_freeze.py::test_the_freeze_loads_and_its_identity_is_pinned`
- `engine/tests/test_v6_e8_analysis_freeze.py::test_it_carries_every_earlier_identity`
- `engine/tests/test_v6_e8_analysis_freeze.py::test_a_tampered_record_fails_to_load`
- `engine/tests/test_v6_e8_analysis_freeze.py::test_a_re_signed_tampered_record_still_fails_to_load`
- `engine/tests/test_v6_e8_family_freeze.py::test_the_freeze_loads_and_its_identity_is_pinned`
- `engine/tests/test_v6_e8_runner.py::test_a_failing_engine_source_check_stops_before_the_pre_match_gate`
- `engine/tests/test_v6_e8_runner.py::test_the_preconditions_run_in_order_and_gate_every_match`
- `engine/tests/test_v6_e8_runner.py::test_copied_packages_must_equal_the_family_freeze`
- `engine/tests/test_v6_e9_instrument_behavior.py::test_same_attempt_validation_reconstructs_once_and_rejects_corruption`
- `engine/tests/test_v6_e9_instrument_constraints.py::test_seat_opposing_margin_and_stall_zero_contribution_full_denominator`
- `engine/tests/test_v6_e9_instrument_constraints.py::test_immunity_both_victim_directions_and_minimum_distinct_positions[29-False]`
- `engine/tests/test_v6_e9_instrument_constraints.py::test_immunity_both_victim_directions_and_minimum_distinct_positions[30-True]`
- `engine/tests/test_v6_e9_instrument_constraints.py::test_phase_near_exclusivity_requires_alternative_opportunity_and_positive_contribution`
- `engine/tests/test_v6_e9_instrument_runner.py::test_native_adapter_exact_environment_defaults_and_self_twins[A-ADAPT8-A]`
- `engine/tests/test_v6_e9_instrument_runner.py::test_native_adapter_exact_environment_defaults_and_self_twins[A-ADAPT8-B]`
- `engine/tests/test_v6_e9_instrument_runner.py::test_native_adapter_exact_environment_defaults_and_self_twins[RUSH8-RUSH8-A]`
- `engine/tests/test_v6_e9_instrument_runner.py::test_native_adapter_exact_environment_defaults_and_self_twins[REACQ8-REACQ8-B]`
- `engine/tests/test_v6_e9_instrument_runner.py::test_native_adapter_exact_environment_defaults_and_self_twins[S16-STRESS8-B]`
- `engine/tests/test_v6_e9_instrument_runner.py::test_incomplete_rectangle_seals_not_evaluable_without_payoff_analysis`
- `engine/tests/test_v6_e9_v2_dispatch.py::test_one_original_and_one_fenced_identical_infrastructure_retry`
- `engine/tests/test_v6_e9_v2_gate8_producer.py::test_w12_producer_is_real_only_with_no_entropy_reference_or_mode_switch`
- `engine/tests/test_v6_e9_v2_independent_bindings.py::test_separate_adoption_attestation_exact_review_and_unchanged_body`
- `engine/tests/test_v6_e9_v2_independent_bindings.py::test_preserved_all_frozen_scientific_raw_and_lf_sources`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_production_source_checker_rehashes_real_files_and_adoption[outside_repository]`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_registered_recovery_pair_yields_one_usable_recovery_completion`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_conflicting_original_completion_after_recovery_makes_block_unusable_and_keeps_every_packet`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_completion_after_recorded_failure_makes_block_unusable_and_blocks_recovery`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_partial_packet_without_terminal_result_keeps_the_recovery_route_open`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_any_terminal_result_evidence_or_output_after_failure_blocks_recovery`
- `engine/tests/test_v6_e9_v2_independent_consumers.py::test_protected_final_seal_reproduces_the_row_only_under_current_final_authority`
- `engine/tests/test_v6_e9_v2_independent_dispatch.py::test_independently_verified_failure_allows_exact_second_attempt_and_never_third`
- `engine/tests/test_v6_e9_v2_independent_dispatch.py::test_stopped_original_worker_cannot_promote_late_completion_after_retry_start`
- `engine/tests/test_v6_e9_v2_independent_materialization.py::test_actual_source_checker_rehashes_implementation_qualification_and_preserved_review[None]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_independent_causal_expected_transition_and_receipt_hashes[A]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_independent_causal_expected_transition_and_receipt_hashes[B]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_complete_paired29_by11_by2_seat_rectangle_has_one_statistical_weight_per_coordinate`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_exact_infrastructure_recovery_allowlist_only[host_worker_loss]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_exact_infrastructure_recovery_allowlist_only[platform_eviction]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_exact_infrastructure_recovery_allowlist_only[external_infrastructure_shutdown]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_exact_infrastructure_recovery_allowlist_only[storage_io_interruption]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[attempt-2]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[attempt-True]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[origin-agent]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[failure_class-runtime_exception]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[before_completion-False]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[completion_known_absent-False]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[original_stopped_or_fenced-False]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[semantic_integrity_failed-True]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[cell_identity-v6-e9-cell-v2-0000000000000000000000000000000000000000000000000000000000000000]`
- `engine/tests/test_v6_e9_v2_independent_scientific.py::test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics[binding_digest-0000000000000000000000000000000000000000000000000000000000000000]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_complete_rectangle_denominator_and_logical_alias_no_extra_weight`
- `engine/tests/test_v6_e9_v2_scientific.py::test_invalid_diagnostics_fail_closed[payoff_doubled-True]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_invalid_diagnostics_fail_closed[terminal-tie]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_invalid_diagnostics_fail_closed[pressure-value2]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_invalid_diagnostics_fail_closed[behavior-None]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_duplicate_only_byte_equal_copies_with_complete_provenance`
- `engine/tests/test_v6_e9_v2_scientific.py::test_opposing_seat_margin_and_stall_preserve_tied_comparators`
- `engine/tests/test_v6_e9_v2_scientific.py::test_immunity_counts_seed_positions_in_each_victim_direction[29-False]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_immunity_counts_seed_positions_in_each_victim_direction[30-True]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_phase_concentration_retains_positive_gain_and_alternative_exposure`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed0]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed1]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed2]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed3]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed4]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed5]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_recovery_is_outcome_blind_and_first_attempt_only[changed6]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_offline_causal_revision_withholding_and_v2_receipt_provenance[A]`
- `engine/tests/test_v6_e9_v2_scientific.py::test_offline_causal_revision_withholding_and_v2_receipt_provenance[B]`
- `engine/tests/test_v6_e9_instrument_analysis.py::test_frozen_rectangle_aliases_self_twins_and_wrapper_bytes`
- `engine/tests/test_v6_e9_instrument_analysis.py::test_rho_boundary_refutation_and_unresolved_and_width_caveat`
- `engine/tests/test_v6_e9_instrument_analysis.py::test_pairing_and_alias_weighting_missing_duplicate_and_corrupt`
