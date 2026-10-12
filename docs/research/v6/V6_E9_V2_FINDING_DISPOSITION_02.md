# E9 v2 seal-04 reproduction findings and step closure

**Recorded 2026-10-06.** This page summarizes the write-once record
`tools/research/v6/e9/v2_finding_disposition_02.json`
(raw SHA-256 `793dd33bb8600bfd232cd3c2b7ac45900fa42c91657fd0d847ba564db45ba59a`).
If the two ever differ, the JSON record governs.

The record covers seal 04 (`v6-e9-instrument-v2-3c1023acb145`; seal raw SHA-256
`a716e781…0369b5`) and its independent reproduction, recorded in
`v2_synthetic_qualification_evidence_04.json` (raw SHA-256 `8ff518c9…b7be5e`).
That reproduction found nine new findings, N1–N9. Disposition 01 still governs the
seal-03 findings and the seal-04 remediation scope. This ruling does not alter seal 04,
its manifests, its evidence, disposition 01 or the reproduction records.

## Step closure

| Item | Status |
| --- | --- |
| Seal 04 | **PASS WITH FINDINGS** |
| Independent reproduction | **PASS** (582/582; ruff and mypy clean; all seven accepted fixes confirmed) |
| N1 | **Deferred mandatory Gate-8 blocker** |
| Seal 05 | Not required solely for N1 at this stage |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |

Not authorized: real entropy, generation, W production, salt creation, native
execution or study publication.

## Rulings

| ID | Recorded severity | Disposition |
| --- | --- | --- |
| N1 | MEDIUM (qualifier) | **Deferred mandatory Gate-8 blocker**; non-blocking for seal 04 |
| N2 | LOW | Recorded only; its W-producer requirement is carried into Gate 8 |
| N6 | LOW / NOT ACTIONABLE | Recorded only; its W-producer requirement is carried into Gate 8 |
| N3, N4, N5 | LOW | Recorded only |
| N7, N8 | NOT ACTIONABLE | Recorded only |
| N9 | LOW / NOT ACTIONABLE | Recorded only |

"Recorded only" means no remediation unless the finding gets its own disposition.

**Why N1 is a blocker, though not for seal 04.** The risk was shown against the actual
K candidate, not a hypothetical one. K contains small public literal seeds such as
0, 1, 2, 3, 5, 7 and 42. The M3 publication check scans the whole C record for
matching decimal digit runs. A structural integer such as `"version": 2` can
therefore block publication even though no protected value is present. A real
study could complete generation, salt creation and W and then be unable to
publish C. N1 must be resolved before any real entropy, generation, W production,
salt creation or other irreversible real-study action.

## Required in the Gate-8 revision

For N1:

1. Decide explicitly, at the protocol and design level, what M3 is meant to
   protect from decimal-representation matching.
2. Distinguish protected generated or private values from unrelated structural
   integers in C.
3. Decide explicitly whether K members that are already public literals need
   decimal-substring protection, rather than inheriting the current whole-record
   scan by accident.
4. Add sealed regression tests with a realistic K that contains small values
   such as 0, 1, 2, 3, 5, 7 and 42.
5. Show that legitimate structural fields cannot cause a false-positive refusal
   that no study could avoid.
6. Keep the intended rejection of genuinely protected values.
7. Include the fix in the Gate-8 implementation seal and its independent
   reproduction before any real-study authorization.

For the W-record producer:

- From N2: supply the complete authority chain and always pass `active_chain_tip`.
- From N6: require the REAL entropy declaration for an operational study.

## Gate ordering

The frozen plan puts Gate 7 (generation authorization) before Gate 8 (private
commitment verification). Under this ruling, the Gate-8 instrument revision must
be implemented, sealed and independently reproduced before Gate 7 is authorized
and before any irreversible real-study action. That revision covers the W-record
producer, the N1 fix and the N2/N6 requirements. Gate 8's own evidence, an
independent W over a real payload, still comes after generation. The frozen gate
order is otherwise unchanged. This reading of the ruling is the implementer's,
and the lead can correct it.

## Next boundary

The next step is Gate-8 planning and revision. Starting it requires a separately
authorized implementation scope. Nothing beyond this record is authorized.
