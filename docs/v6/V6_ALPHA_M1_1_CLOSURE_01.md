# Bytefray V6 — Milestone M1-1 Formal Project Lead Closure Record 01

2026-10-10, America/Indianapolis.

**STATUS: CLOSED AND RATIFIED BY PROJECT LEAD (MILESTONE M1-1 COMPLETE)**

---

## 1. Executive Summary and Authority Statement

This document records the formal Project Lead closure of **Bytefray V6 Milestone 1 Subtask 1 (M1-1: Policy and Capability Support)**, authorized under [Phase 0 Decision Packet 01](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md) and governed by the [V6 Alpha M1 Contract](V6_ALPHA_M1_CONTRACT_01.md).

The Project Lead evaluated the M1-1 qualification report ([V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md](V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md)), the independent implementation review ([V6_ALPHA_M1_1_IMPLEMENTATION_REVIEW_01.md](V6_ALPHA_M1_1_IMPLEMENTATION_REVIEW_01.md)), and the associated inventory and validation dispositions ([Disposition 01](V6_ALPHA_M1_1_SUPPLEMENTAL_INVENTORY_DISPOSITION_01.md), [Disposition 02](V6_ALPHA_M1_1_CONTEXT_INVENTORY_DISPOSITION_02.md), and [Disposition 03](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)).

Prior to final ratification, the Project Lead required reconciliation of an apparent discrepancy between the 25 recorded skips in the JUnit regression record and the 24 skips categorized during qualification review. Following exact verification against the JUnit XML evidence, no material qualification discrepancy was found.

**The Project Lead hereby declares Milestone M1-1 formally CLOSED.**

---

## 2. Skip Inventory Reconciliation (JUnit Evidence)

The complete headless regression execution against current product source (PID 23644, retained in `work/m1_1_archive_20261010/current_regression_final.xml`) produced:
- **8,327 passed**
- **25 skipped**
- **75 deselected** (72 frozen historical nodes executed against preserved baseline + 3 headless-excluded GUI tests)
- **0 failures, 0 errors**

### 2.1 Full Categorization of the 25 Recorded Skips

Inspection of the actual JUnit XML testcase elements and skip messages establishes the exact composition of all 25 skipped tests:

1. **Windows Unprivileged Symlink Permissions (14 tests):**
   - `engine/tests/test_agent_evaluation_revision_capture.py::test_evaluation_captures_symlink_cycle_as_revision_omissions`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_package.py::test_export_preflights_large_internal_file_symlink_before_reading_target`
     *(Message: "file symlinks are unavailable in this environment: [WinError 1314] A required privilege is not held by the client")*
   - `engine/tests/test_agent_revisions.py::test_symlink_cycle_is_reported_as_deterministic_omissions`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_revisions.py::test_external_file_symlink_is_reported_not_silently_dropped`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_revisions.py::test_internal_file_symlink_is_dereferenced_and_included`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_revisions.py::test_broken_symlink_is_reported_not_a_file`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_revisions.py::test_completeness_and_fingerprint_reflect_omissions`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_agent_revisions.py::test_verify_revision_accounts_for_recorded_omissions`
     *(Message: "Symlink creation is not permitted in this environment.")*
   - `engine/tests/test_evaluation_history_verification.py::test_resolve_contained_path_rejects_symlink_escape`
     *(Message: "symlink creation requires elevated privileges on Windows")*
   - `engine/tests/test_evaluation_history_verification.py::test_verify_cell_rejects_symlink_escape_replay_filename`
     *(Message: "symlink creation requires elevated privileges on Windows")*
   - `engine/tests/test_launchers.py::test_source_commands_do_not_resolve_a_symlinked_interpreter`
     *(Message: "POSIX symlink semantics only")*
   - `engine/tests/test_replay_integrity.py::test_replay_symlink_escape_is_rejected_where_supported`
     *(Message: "creating a test symlink is unavailable: [WinError 1314] A required privilege is not held by the client")*
   - `engine/tests/test_v6_e9_v2_gate8_seal07.py::test_s7_symlink_to_regular_target_and_read_observer`
     *(Message: "host does not authorize symlink creation")*
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py::test_regular_reader_never_caches_type_and_preserves_regular_symlinks`
     *(Message: "native symlink creation unavailable on this root: 1314")*

2. **Unbuilt Frozen Binary Smoke Tests / `BYTEFRAY_FROZEN_EXE` Unset (5 tests):**
   - `engine/tests/test_frozen_bytecode_exclusion.py::test_frozen_payload_contains_no_python_bytecode`
     *(Message: "set BYTEFRAY_FROZEN_EXE to a built executable to inspect its payload")*
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-annotated]`
     *(Message: "set BYTEFRAY_FROZEN_EXE to a built executable to run frozen smokes")*
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-blank]`
     *(Message: "set BYTEFRAY_FROZEN_EXE to a built executable to run frozen smokes")*
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_bundles_every_supported_template_directory`
     *(Message: "set BYTEFRAY_FROZEN_EXE to a built executable to run frozen smokes")*
   - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_smoke_is_not_silently_satisfied_by_the_source_tree`
     *(Message: "set BYTEFRAY_FROZEN_EXE to a built executable to run frozen smokes")*

3. **Native POSIX Special Filesystem Objects (fifo, socket, device) (4 tests):**
   - `engine/tests/test_v6_e9_v2_gate8_seal07.py::test_s7_native_posix_fifo_socket_device_and_publication`
     *(Message: "native POSIX special objects require POSIX; separately qualified via WSL")*
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[fifo]`
     *(Message: "native POSIX objects require a suitable host")*
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[socket]`
     *(Message: "native POSIX objects require a suitable host")*
   - `engine/tests/test_v6_e9_v2_independent_gate8_seal07::test_native_nonregular_objects_are_refused_in_bounded_subprocess[device]`
     *(Message: "native POSIX objects require a suitable host")*

4. **Windows NTFS Alternate Data Stream (ADS) / Colon Filename (1 test):**
   - `engine/tests/test_agent_package.py::test_export_rejects_nonportable_live_payload_name_before_read`
     *(Message: "NTFS treats colon names as alternate data streams, not enumerable files")*

5. **Inactive Qualification Guard Plugin in Standard Headless Regression (1 test):**
   - `engine/tests/test_v6_e9_v2_independent_consumers.py::test_qualification_runs_under_the_entropy_and_producer_guard`
     *(Message: "guard plugin inactive: not an audited qualification run")*

### 2.2 Reconciliation Analysis

- **Mathematical Reconciliation:** 14 (symlink) + 5 (frozen exe) + 4 (POSIX special objects) + 1 (NTFS colon ADS) + 1 (inactive qualification guard) = **25 tests**.
- **Root Cause of Discrepancy:** The earlier qualification summary categorized 24 skips by grouping the 14 symlink skips, 5 frozen executable skips, 4 POSIX special object skips, and 1 guard plugin skip, while inadvertently omitting the single Windows NTFS colon Alternate Data Stream skip (`test_agent_package.py::test_export_rejects_nonportable_live_payload_name_before_read`).
- **Qualification Verdict:** All 25 skips are confirmed to be expected, pre-existing environment and platform gates. Zero skips were introduced by M1-1 changes, and no tests were skipped or xfailed to achieve passing status. There is **no material qualification discrepancy**.

---

## 3. Formal Project Lead Ratification of M1-1 Deliverables

The Project Lead confirms and ratifies the following M1-1 achievements:

1. **Independent Product Ruleset Registration:**
   - `bytefray-rules-6-alpha1` is registered with literal T8 gameplay fields differing only in identity.
   - Stable `bytefray-rules-4` remains the default and sole candidate for omitted `--ruleset`.
   - Alpha scheduler override fields are strictly rejected.

2. **Capability Metadata Version 1 Contract:**
   - Implemented strict capability parsing (`agent_capabilities.py`): version integer 1, known capability `sense`.
   - Whole-roster capability preflight executes before agent import, agent reset, or match artifact creation/mutation.
   - Capability-aware validation is wired into `validate_agent` and CLI `bytefray agents validate --ruleset ...`.
   - Worker transport normalizes capability blocks, preserves legacy metadata, and rejects malformed manifests.
   - Injected characterization policies retain callback-loading compatibility without capability queries.

3. **Validation and Quality Gate Compliance:**
   - **Current Focused Tests:** 1,096 passed in 130.22s (including the new 42-test `test_v6_alpha_m1_policy_capabilities.py` suite).
   - **Current Regression Complement:** 8,327 passed, 25 skipped (reconciled above), 75 deselected, 0 failures, 0 errors in 4,628.11s.
   - **Preserved Baseline Matrix:** 71 passed in baseline pytest, 1 passed in isolated process with `qualification_guard` plugin (100% of the 72 historical nodes pass).
   - **Static Analysis & Type Checking:** Ruff passed clean; engine mypy passed (98 files); client mypy passed (16 files); `git diff --check` passed clean.
   - **Independent Implementation Review:** Code and scope passed with zero outstanding defects.

---

## 4. Preservation Boundaries and Research Lock Re-affirmation

The Project Lead re-affirms that:
1. All 329 sealed Final 08 research members retain byte-for-byte SHA-256 match.
2. All 15 historical policy literals, fixtures, goldens, and test baselines remain untouched.
3. Negative import guards verify product execution does not import research machinery.
4. The **E9 research lock** remains in full effect: private research authority records, author provenance materials, and local test artifacts remain strictly isolated and excluded from public Git staging.

---

## 5. Scope Boundary and Next Steps

- **Milestone M1-1 is formally CLOSED.**
- Subtasks **M1-2 through M1-6** remain pending and strictly separate.
- Implementation of **M1-2 must NOT begin** until separate Project Lead authorization is issued.
