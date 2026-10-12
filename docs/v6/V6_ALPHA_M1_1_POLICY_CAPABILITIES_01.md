# V6 alpha M1-1 — Policy and Capability Support

2026-10-10, America/Indianapolis. Implementation under the adopted
[Phase 0 packet](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md) and
[M1 contract](V6_ALPHA_M1_CONTRACT_01.md). Baseline:
`b948540aa9ef34134ff7e3c633c3acfc9f97da96` on `v6-research`.

## Product contract

`bytefray-rules-6-alpha1` is independently registered in the process-runtime
and public experimental lifecycle inventories. Its literal gameplay policy
matches T8 in every dataclass field except `ruleset_id`. It is never an alias
for a research identity. Stable `bytefray-rules-4` remains the omitted-match
default and sole omitted-selection candidate. Alpha1 rejects both scheduler
override fields, including explicit values equal to the fixed policy.

Agent API v2 callbacks and replay 4 / result 2 / trace 2 remain unchanged.
The optional **capability metadata version 1** manifest extension is:

```yaml
capabilities:
  version: 1
  required: [sense]
```

The block must have exactly `version` and `required`. Version must be integer
1, excluding booleans and floating point values. `required` must be a list
of unique known strings; the only initial name is `sense`. Empty requirements
are legal. Unknown versions/names, extra or missing fields, null blocks and
malformed lists fail with `agent_manifest_invalid`. An absent block means
no additional requirements and preserves existing manifests.

`RulesetPolicy.available_capabilities` exposes `sense` exactly when
`sensing_mode == "active"`. The compatibility predicate, native match service,
direct controller initialization, validation, development test and worker
load guard share the same parser and preflight operation. A missing capability
raises `agent_capability_unsupported` before agent import/reset and before
match artifact creation or replacement. Whole-roster preflight precedes the
first entrant import. Worker transport carries only validated capability
metadata, preserving unrelated legacy YAML metadata such as dates.

Library `validate_agent(..., ruleset_id="bytefray-rules-6-alpha1")` and
`bytefray agents validate ID --ruleset bytefray-rules-6-alpha1` explicitly
supply the active sensing context for a single callback dry run. An omitted
validation policy retains the established context and refuses a declared
sensing requirement. A dry run checks action structure; it does not apply
SENSE, produce a receipt, or establish full-match success. Existing optional
dry-run traces retain their prior schema and are not bound match artifacts.

An undeclared agent returning SENSE under v4 still forfeits under the existing
invalid-action contract. Capability metadata is neither a Python sandbox nor
a claim about arbitrary agent source. The alpha teaching exception establishes
no seed secrecy or research payoff claim.

The new identity can be explicitly selected through the engine and development
test APIs. General run/test CLI and Designer selection integration belongs to
M1-5; M1-1 adds only the capability-aware validate option.

## Scope and preservation

The current E8 test changes are confined to the three adopted K4 inventory
assertions: active policy membership/window, lifecycle partitioning, and
SENSE acceptance for the new identity. Stable and other passive policies
retain their SENSE forfeiture checks. Original qualified source/test bytes
remain available at the baseline commit. Existing historical policy literals,
scientific mechanic expectations, goldens, fixtures, schemas and research/seal/private files
are not revised.

The user subsequently expressly authorized the eight additional current
inventory assertion updates listed in the
[supplemental disposition](V6_ALPHA_M1_1_SUPPLEMENTAL_INVENTORY_DISPOSITION_01.md).
These update process membership, five lifecycle partitions, the inert radius
inventory and the scope of one E8 census comparison. The frozen E8 compatibility
gate is unchanged, and the census test explicitly rejects alpha1 for both
gated and ungated E8 sensing packages. No additional mechanic or golden
assertion changes are authorized or applied.

The user also expressly authorized the two context-delivery census updates
in [disposition 02](V6_ALPHA_M1_1_CONTEXT_INVENTORY_DISPOSITION_02.md), retaining
all original E6/E8 identity tuples while asserting the approved radius 32 and
window 27 for alpha1 under direct and worker execution. The complete permitted
current-inventory disposition is therefore the original three functions plus
eight and two separately adopted functions; no scientific rerun or eligibility
change is implied.

New focused tests use controlled development agents, fixed existing test inputs,
temporary directories and short synthetic matches. They do not execute E8/E9
family policies, allocation controllers, entropy producers or experimental
payoff analysis. A negative import guard verifies native product execution
does not import research machinery.

## Validation and independent review

The final focused product/regression selection passed **1,096 tests** in
130.22 seconds, including the new 42-case M1-1 module, direct/worker execution,
historical v4 characterizations, default selection and E8 compatibility
separation. Final `ruff check .` and the separate engine/client mypy checks
passed (98 and 16 source files respectively). `git diff --check` passed.

The initial unpartitioned headless run completed with 8,304 passed, 25 skipped,
3 GUI deselected, 84 failed and 3 errors. Fifteen failed cases were inventory
or worker compatibility defects subsequently resolved and covered by the
final focused run. The remaining 72 nodes enforce the unchanged frozen
research source/preservation boundary or require the original synthetic
qualification guard. This initial result is **not** a green full-suite result.

E8 and E9 guards hash the executing checkout's source and qualified tests.
The approved product changes therefore correctly cause them to reject this
checkout as the historical instrument. Their manifests, checks and expectations
remain unchanged; no mixed-source execution, hash-root redirection, resealing
or research eligibility change is used to obtain a passing result.

The 72 nodes were reproduced unchanged in an isolated detached worktree at
`b948540aa9ef34134ff7e3c633c3acfc9f97da96`: **71 passed** in 74.50 seconds in
ordinary pytest, and **1 passed** in 0.17 seconds with the existing
entropy-prohibiting `qualification_guard` plugin. The latter is a static test
which explicitly requires that plugin; it cannot pass ordinary unguarded pytest.
This run does not call the qualification publication wrapper or qualify a new
scientific instrument.

The isolated reproduction imports its own ruleset policy, match service,
controller, worker, E8 freeze and E9 protocol modules. Its own Git index lists
the original 116 engine paths, and its unchanged protocol source check passes.
The worktree reproduces preserved raw bytes as well as the Git tree: 28 files
affected by checkout line-ending filters were copied from untouched originals
only after both their frozen raw SHA-256 and LF-normalized baseline Git blob
matched. All 329 final-08 raw source/test pins pass in this isolated baseline.
Original working-tree files were not changed by that reconstruction.

The preservation audit verifies all 15 historical policy literals unchanged,
exactly 13 authorized existing test functions changed and all other statements
in those ten test modules unchanged. All 62 inherited untracked files and
local settings retain their captured hashes; the index and branch HEAD are
unchanged. No research/client/legacy tracked file or frozen manifest was edited.

The [independent implementation review](V6_ALPHA_M1_1_IMPLEMENTATION_REVIEW_01.md)
reports **CODE AND SCOPE PASS**. It accepted the technical validation matrix
subject to explicit lead acceptance under Decision B's no-exclusion clause and
completion of the current regression complement. Both conditions are now satisfied:
the lead authorized adoption of [validation disposition 03](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)
on 2026-10-10, and the final complete current headless regression run (PID 23644)
passed with 8,327 passed, 25 skipped, 75 deselected (72 frozen historical + 3 GUI),
0 failures, and 0 errors in 4,628.11s (JUnit: 8,352 tests, 0 failures, 0 errors, 25 skipped in 4,628.010s).

Combined with the 72/72 passing historical nodes against the verified preserved baseline
(71 in baseline pytest, 1 with `qualification_guard` plugin), composite M1-1 regression
PASS is verified. This partition is recorded explicitly; it does not establish an
unpartitioned current-checkout suite PASS, qualify a new scientific instrument,
or authorize broader exclusions. M1-1 verification is complete and ready for final lead sign-off.

### Skip inventory reconciliation (25 JUnit skips)

The final regression XML (`work/m1_1_archive_20261010/current_regression_final.xml`) records exactly **25 skipped tests**. A prior qualification summary categorized 24 skips by accounting for 14 symlink skips, 5 frozen executable skips, 4 POSIX special object skips, and 1 inactive guard plugin skip, omitting the single Windows NTFS colon/alternate-data-stream skip. The exact JUnit evidence reconciles all 25 skips into five standard platform/environment categories:

1. **Windows unprivileged symlink permissions (14 skips):**
   - `engine/tests/test_agent_evaluation_revision_capture.py::test_evaluation_captures_symlink_cycle_as_revision_omissions`
   - `engine/tests/test_agent_package.py::test_export_preflights_large_internal_file_symlink_before_reading_target`
   - `engine/tests/test_agent_revisions.py::test_symlink_cycle_is_reported_as_deterministic_omissions`
   - `engine/tests/test_agent_revisions.py::test_external_file_symlink_is_reported_not_silently_dropped`
   - `engine/tests/test_agent_revisions.py::test_internal_file_symlink_is_dereferenced_and_included`
   - `engine/tests/test_agent_revisions.py::test_broken_symlink_is_reported_not_a_file`
   - `engine/tests/test_agent_revisions.py::test_completeness_and_fingerprint_reflect_omissions`
   - `engine/tests/test_agent_revisions.py::test_verify_revision_accounts_for_recorded_omissions`
   - `engine/tests/test_evaluation_history_verification.py::test_resolve_contained_path_rejects_symlink_escape`
   - `engine/tests/test_evaluation_history_verification.py::test_verify_cell_rejects_symlink_escape_replay_filename`
   - `engine/tests/test_launchers.py::test_source_commands_do_not_resolve_a_symlinked_interpreter`
   - `engine/tests/test_replay_integrity.py::test_replay_symlink_escape_is_rejected_where_supported`
   - `engine/tests/test_v6_e9_v2_gate8_seal07.py::test_s7_symlink_to_regular_target_and_read_observer`
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py::test_regular_reader_never_caches_type_and_preserves_regular_symlinks`
2. **Unbuilt frozen binary smoke tests / `BYTEFRAY_FROZEN_EXE` unset (5 skips):**
   - `engine/tests/test_frozen_bytecode_exclusion.py::test_frozen_payload_contains_no_python_bytecode`
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-annotated]`
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-blank]`
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_bundles_every_supported_template_directory`
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_smoke_is_not_silently_satisfied_by_the_source_tree`
3. **Native POSIX special filesystem objects (fifo, socket, device) (4 skips):**
   - `engine/tests/test_v6_e9_v2_gate8_seal07.py::test_s7_native_posix_fifo_socket_device_and_publication`
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[fifo]`
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[socket]`
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[device]`
4. **Windows NTFS alternate data stream (ADS) / colon-in-filename test (1 skip):**
   - `engine/tests/test_agent_package.py::test_export_rejects_nonportable_live_payload_name_before_read`
5. **Qualification guard plugin inactive in standard headless regression run (1 skip):**
   - `engine/tests/test_v6_e9_v2_independent_consumers.py::test_qualification_runs_under_the_entropy_and_producer_guard`

All 25 skips are standard, expected platform/environment-gated conditions. None represent regressions or qualification defects.

### Formal Project Lead closure

On 2026-10-10, the Bytefray Project Lead formally accepted the M1-1 qualification report and closed Milestone M1-1. See the formal closure record in [V6_ALPHA_M1_1_CLOSURE_01.md](V6_ALPHA_M1_1_CLOSURE_01.md).

Retained execution logs, failure node list, import origins, JUnit results,
raw-checkout restoration list and preservation audit are under
`work/m1_1_archive_20261010/`. This record covers M1-1 only; M1-2 through M1-6,
cross-platform interactive acceptance and full M1 acceptance remain separate.
