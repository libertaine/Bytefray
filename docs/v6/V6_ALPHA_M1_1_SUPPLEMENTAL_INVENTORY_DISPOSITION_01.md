# M1-1 supplemental inventory disposition proposal

2026-10-10, America/Indianapolis. **ADOPTED — IMPLEMENTATION AUTHORIZED.**
The user explicitly answered: “Authorize the eight listed assertion updates
and complete validation.” The eight updates below are now applied; final
verification is recorded in the [M1-1 implementation report](V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md).

The adopted [Phase 0 packet K4](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md)
and the current M1-1 instruction authorize exactly three assertion updates
in `test_ruleset_v6_research_sensing_active.py`. Those three are implemented.
The current baseline has eight additional assertions whose fixed inventory
assumptions conflict with registering the approved product identity. Passing
these tests requires an explicit supplemental disposition; changing policy
classification or frozen research compatibility to accommodate stale
inventories would violate the approved mechanics and isolation boundary.

Independent reviewer: Codex subagent `/root/m1_1_independent_review`.
This is a product implementation review, not a scientific authority appointment.
The reviewer independently confirmed the following exact proposed scope.

| File under `engine/tests/` | Function / assertion | Proposed change |
| --- | --- | --- |
| `test_ruleset_policy.py` | `test_v6_research_scale_is_registered_but_never_automatic`, exact `PROCESS_RULESET_IDS` equality | Add only `bytefray-rules-6-alpha1` to the expected process identity set. Keep omitted-selection expectations unchanged. |
| `test_ruleset_v6_research_capture_hold.py` | `test_lifecycle_sets_partition_every_executable_policy` | Add `public_experimental: PUBLIC_EXPERIMENTAL_RULESET_IDS` to the lifecycle partition. Retain exactly-one membership, full union and historical exclusion checks. |
| `test_ruleset_v6_research_disruption_slot.py` | `test_lifecycle_sets_partition_every_executable_policy` | Same lifecycle addition; retain all partition and research membership assertions. |
| `test_ruleset_v6_research_mirrored_passes.py` | `test_lifecycle_sets_partition_every_executable_policy` | Same lifecycle addition; retain all partition and research membership assertions. |
| `test_ruleset_v6_research_anchor_before_core.py` | `test_lifecycle_sets_partition_every_executable_policy` | Same lifecycle addition; retain all partition, stable and research membership assertions. |
| `test_ruleset_v6_research_sensing.py` | `test_lifecycle_sets_partition_every_executable_policy` | Same lifecycle addition; retain all partition, stable and research membership assertions. |
| `test_ruleset_v6_research_sensing.py` | `test_every_registered_policy_keeps_unlimited_sensing_except_e6` | Include only alpha1 in the expected `detection_radius == 32` identity set. This is inert context metadata under active sensing, as approved; no passive channel is added. |
| `test_v6_e8_family.py` | `test_the_gate_reads_the_registered_condition_rulesets` | Scope the comparison with the frozen ungated acceptance set to registered active policies in `compatibility.CONDITION_RULESETS.values()`; explicitly assert alpha1 remains rejected by the frozen E8 compatibility gate. Retain exact C8/T8/C8L/T8L condition identities. |

Imports needed for these assertions are included in the proposed disposition.
No other functions, mechanic expectations, qualified historical artifacts,
goldens, baseline pins or integrity checks may change. No tests may be skipped
or excluded. Original qualified bytes remain at
`b948540aa9ef34134ff7e3c633c3acfc9f97da96`.

In particular, `tools/research/v6/e8/compatibility.py` stays unchanged:
context-gated E8 packages remain restricted to C8/T8/C8L/T8L and ungated
packages to T8/T8L. Alpha1 does not become an E8 scientific condition. The
existing accept/reject matrix already checks that separation.

Under this supplemental authorization, apply only these eight assertion dispositions, rerun the failures
and relevant compatibility tests, then rerun the full headless suite and
complete the independent review. Until passing checks,
M1-1's regression exit criterion remains **NOT MET**.
