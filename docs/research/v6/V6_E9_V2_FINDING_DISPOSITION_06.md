# E9 v2 Seal-08 acceptance disposition (06)

Recorded 2026-10-08 from the research lead ruling supplied with this request.
The write-once machine record is `tools/research/v6/e9/v2_finding_disposition_06.json`,
raw SHA-256 `02c33887f1edd9ce09838dd4cb580d8d593d413097cbf5d4d197dbaf8e5bb2e6`. It governs this readable mirror.
The machine record preserves the exact supplied ruling text (8140 UTF-8 bytes,
raw SHA-256 `e868a56a5845146bef9d68b69acee6b37c3eb15764b3c5428fc678a5f6e63a55`). Recording the ruling grants no authority of its own.

| Item | Disposition |
| --- | --- |
| seal_06 | PASS WITH FINDINGS |
| seal_07 | INDEPENDENT REPRODUCTION FAIL |
| seal_07_independent_reproduction | FAIL |
| seal_08 | PASS WITH FINDINGS |
| seal_08_independent_reproduction | PASS WITH FINDINGS |
| blockers | 0 |
| non_blocking_findings | 0 |
| S7-IQ-F1 | RESOLVED BY SEAL 08 |
| S7-IQ-F2 | RESOLVED BY SEAL 08 |
| S8-IQ-F1_to_F4 | NOTE / RECORD ONLY |
| DV8-4 | CONFIRMED |
| DV8-5 | CONFIRMED |
| gate_8 | COMPLETE AND ACCEPTED |
| gate_8_operational_acceptance | ESTABLISHED |
| requirement_C | NOT ESTABLISHED |
| execution | LOCKED |
| formal_Q_record | ABSENT |
| gate_7 | NOT YET AUTHORIZED |
| historical_coverage | NOT ESTABLISHED |

Seal 08 is accepted. Gate 8 is complete and accepted. The implementation/qualification
prerequisite previously blocking progression toward Gate 7 is satisfied.
Execution remains **LOCKED**, Requirement C **NOT ESTABLISHED**, and Q **ABSENT**.

The retained independent qualification reports 1338 collected, 1332 passed, six Windows
skips, zero failures and zero errors across 29 modules. All six skipped cases passed
under WSL. Ruff, mypy engine, mypy client and bindings passed. The qualifier additionally
compared combined adversarial states: 31 states producing UNAVAILABLE then PASS on Seal 07
produce FAILED_VERIFICATION then REFUSED_PRECONDITION on Seal 08.

Before this disposition was written, all 329 sealed files were freshly rehashed unchanged,
the candidate-31 and final-08 manifest pairs compared byte-identically, and the instrument
identity and retained record bindings verified. No source or test bytes were changed.
The qualification results are accepted retained evidence; this task did not rerun the full suite.

The JSON retains each S8-IQ-F1 through F4 qualifier observation exactly, alongside the lead's
disposition. In particular, the qualifier's then-pending backup observation remains historical;
it is not rewritten using the later cycle report. No stronger independence or provenance
claim is made. Seal 07 remains a failed independent reproduction.

The complete lead ruling below is mirrored with LF line endings. Its exact original text,
including original line endings, is retained in the JSON authority field.

---

**Lead disposition: Seal 08 and Gate-8**

Seal 08 is accepted.

Final status:

- **Seal 08: PASS WITH FINDINGS**
- **Independent reproduction: PASS WITH FINDINGS**
- **Blockers: none**
- **Non-blocking findings: none**
- **Notes: S8-IQ-F1 through F4**
- **Gate-8 operational acceptance: ESTABLISHED**

This acceptance does **not** authorize operational execution.

Execution remains LOCKED until a later gate explicitly authorizes the corresponding operational actions.

Requirement C remains NOT ESTABLISHED and Q remains absent.

---

# Seal 08 acceptance basis

Accept the independently reproduced Seal-08 results:

- full 29-module suite:
  - 1338 collected
  - 1332 passed
  - 6 skipped
  - 0 failed
  - 0 errors
- all six Windows-skipped cases passed under WSL;
- Ruff passed;
- mypy engine passed;
- mypy client passed;
- bindings passed;
- all 329 sealed files rehashed unchanged;
- no post-seal source/test change occurred;
- the independent qualifier exercised additional adversarial combined states rather than relying only on named regression tests.

The adversarial comparison is particularly important:

- in 31 combined states where Seal 07 produced `UNAVAILABLE` and later permitted PASS,
- Seal 08 produces `FAILED_VERIFICATION` and refuses every retry.

That establishes the F1 positive-mismatch-precedence repair intended by Seal 08.

Seal 07 remains preserved as a failed independent reproduction and is not retrospectively reclassified.

---

# DV8-4 — CONFIRMED

Confirm:

**After a deferred mapped registry-read unavailability, a later non-mismatch error ends the scan according to the same error behavior Seal 07 would have applied to that later error.**

The purpose of Option C was narrowly to defer mapped availability failures long enough to discover available **positive mismatch evidence**.

It was not intended to:

- suppress arbitrary later errors;
- convert arbitrary exceptions into `Unavailable`;
- make the registry scan exhaustive across states where ordinary processing itself cannot continue;
- create a new generic error-aggregation framework.

Therefore DV8-4 is accepted.

A deferred availability condition loses precedence to a later positive mismatch as required.

It does not require unrelated later exceptions to be converted into an availability result.

---

# DV8-5 — CONFIRMED

Confirm:

**When this G's own registry entry is unavailable, the remaining authorized registry scan occurs after the marker check.**

This behavior is necessary to satisfy the complete F1 ordering:

- marker mismatch must remain discoverable despite registry unavailability;
- other available registry mismatch evidence must remain discoverable;
- only when no available positive mismatch is found may deferred unavailability determine the availability result.

S8-IQ-F2 does not invalidate DV8-5.

The malformed-`G` TypeError is a separate malformed-input condition exposed because the scan now correctly continues farther than Seal 07 did.

DV8-5 therefore remains part of the accepted Seal-08 behavior.

---

# S8-IQ-F1 — RECORD ONLY

The frozen-catalogue masking behavior previously dispositioned as record-only remains unchanged.

Do not modify Seal 08 for it.

It is outside the accepted F1 registry/marker precedence boundary.

Any future proposal to change catalogue masking requires its own disposition and scope.

---

# S8-IQ-F2 — RECORD ONLY

Record the malformed-`G` behavior without a Seal-09 repair.

Accepted characterization:

- a registry record can parse structurally yet contain a `G` value whose later ordering/comparison raises an untyped `TypeError`;
- the operation fails closed;
- no W or PASS is produced;
- no scientific failure outcome is fabricated;
- retry with the same malformed evidence will encounter the same underlying defect;
- the condition therefore requires investigation/correction of the malformed retained evidence rather than scientific regeneration.

The behavior change relative to Seal 07 is acknowledged:

when this G's own entry is unavailable, DV8-5 now permits the scan to reach malformed later material that Seal 07 would not have reached.

That is an acceptable consequence of the repaired scan ordering.

It does not violate the frozen F1 precedence rule because the malformed `G` condition is not itself one of the mapped positive-mismatch cases.

Do not broadly catch `TypeError` merely to convert this state into `UNAVAILABLE` or `FAILED_VERIFICATION`.

Such a change could mask programming errors or other malformed-state defects.

If this condition occurs during future operational work, stop that study's progression and investigate the retained registry evidence. Do not redraw or replace scientific material.

---

# S8-IQ-F3 — RECORD ONLY

The mismatch-over-unavailability ordering remains limited to the frozen registry/marker F1 boundary.

A changed retained supplement being masked by another unavailable state is outside that scope.

Do not broaden Seal 08 to supplements.

A future expansion requires separate scientific justification, disposition and qualification.

---

# S8-IQ-F4 — RECORD ONLY

Retain the provenance observations exactly as recorded.

They do not invalidate Seal 08.

Do not describe the independent authorship/reproduction as stronger than the retained evidence supports.

No retrospective provenance reconstruction is required.

---

# Disposition record

Create a new write-once disposition record, following the existing sequence, expected to be:

`v2_finding_disposition_06.json`

and its readable Markdown mirror.

Record:

- Seal 08 PASS WITH FINDINGS;
- independent reproduction PASS WITH FINDINGS;
- zero blockers;
- zero non-blocking findings;
- S8-IQ-F1–F4 NOTE / RECORD ONLY;
- DV8-4 CONFIRMED;
- DV8-5 CONFIRMED;
- S7-IQ-F1 resolved by Seal 08;
- S7-IQ-F2 resolved by Seal 08;
- Gate-8 operational acceptance ESTABLISHED;
- Requirement C NOT ESTABLISHED;
- execution LOCKED;
- Q absent.

Do not modify Seal 08 or any prior disposition.

---

# Gate-8 status

With this disposition:

**Gate 8 is complete and accepted.**

That means the implementation/qualification prerequisite that previously blocked progression toward Gate 7 has been satisfied.

It does **not** mean real-study operations may begin automatically.

In particular this disposition does not itself authorize:

- REAL entropy;
- operational generation;
- operational W production;
- salt creation;
- native matches;
- operational publication;
- Q;
- O/V/A/R/B;
- Gate-7 execution.

Those remain behind their respective later authorization boundaries.

---

# Repository checkpoint

After Disposition 06 and its readable mirror are written and verified, stop research implementation work.

This is a scientifically meaningful repository checkpoint:

**Seal 08 independently reproduced and Gate 8 accepted.**

Before starting Gate-7 work:

1. audit the current working tree;
2. separate repository evidence from private/cache artifacts;
3. verify Seal 08 and all 329 manifested files;
4. verify Disposition 06;
5. commit the accumulated Seal-07/Seal-08 research state;
6. push/sync `v6-research`;
7. verify local and remote HEAD match;
8. report the new checkpoint SHA.

Do not include private transcript/provenance backups in Git.

Do not begin Gate-7 implementation or operational work in the same checkpoint task.

---

# Current scientific state after acceptance

- Seal 06: **PASS WITH FINDINGS**
- Seal 07: **INDEPENDENT REPRODUCTION FAIL**
- Seal 08: **PASS WITH FINDINGS**
- Seal-08 independent reproduction: **PASS WITH FINDINGS**
- S7-IQ-F1: **RESOLVED**
- S7-IQ-F2: **RESOLVED**
- S8-IQ-F1–F4: **RECORD ONLY**
- Gate-8 operational acceptance: **ESTABLISHED**
- Execution: **LOCKED**
- Requirement C: **NOT ESTABLISHED**
- Q: **ABSENT**
- Gate 7: **not yet authorized**

Record the disposition, then perform the repository checkpoint/sync as a separate bounded task.
