# E9 v2 Gate-8 scope 02 (seal 06)

**Recorded 2026-10-07.** This page summarizes the write-once record
`tools/research/v6/e9/v2_gate8_scope_02.json`, identity `v6-e9-v2-gate8-scope-0761c4e07487`.

- Body SHA-256: `0761c4e07487529d225f4d1d393433f283b26741df2ae7335e30162a87897cce`
- Raw SHA-256: `75c1b3638d998506dcd78b4a348ac12f866c21364440542b683bad52539046b4`

If the two ever differ, the JSON record governs.

The record scopes seal 06, a bounded revision of the seal-05 Gate-8 implementation
(`v6-e9-instrument-v2-fd0b524b9712`). It covers only the four findings that disposition 03
ruled FIX IN SEAL 06 (G8-IQ-F1 to F4), and transcribes the lead's seal-06 scope rulings.
Those rulings confirmed the implementer's stop on F1, approved two legacy test-case edits,
confirmed the F2 interpretation, and kept the F3 reading and the F4 boundary.

It binds 19 inputs by raw digest:

- disposition 03;
- evidence 05, seal 05, its two final manifests and tooling attempt history 02;
- scope 01 and its lead confirmation, and the Gate-8 plan;
- dispositions 01 and 02, with both lead confirmations;
- the adopted protocol and its adoption attestation;
- the rule contract (human and machine), the record schemas and qualification plan 02.

Each digest was checked against the hash an earlier record already holds for the same file.
Before the record was created, all 323 seal-05 manifested files and the 24 seal-05 records
bound by disposition 03 were rehashed and found unchanged.

**Seal-06 implementation is not authorized by this record.** It needs lead review of this
scope and a separate explicit authorization.

| Item | Status |
| --- | --- |
| Seal 05 | PASS WITH FINDINGS |
| N1 | RESOLVED |
| F1–F4 | Seal 06 required |
| F5–F9 | Record only |
| Gate 8 operational acceptance | NOT ESTABLISHED |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |

Not authorized: seal-06 implementation, Gate 7, REAL entropy, operational generation,
operational W production, salt creation, native execution, operational publication,
Q creation, or any operational record (T, O, V, A, R, B or later). Seal 05 must not be used
for operational W production.

## File boundary

**May change:**

| File | Limit |
| --- | --- |
| `tools/research/v6/e9/v2/private_verification.py` | Only as repairs F1–F4 require |
| `engine/tests/test_v6_e9_v2_gate8_producer.py` | Only legacy edit E1, by the implementer |
| `engine/tests/test_v6_e9_v2_independent_gate8_producer.py` | Only legacy edit E2, by the independent test author |

**May add:**

- `engine/tests/test_v6_e9_v2_gate8_seal06.py`, written by the implementer;
- `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py`, written by the independent
  test author from this record and disposition 03.

No new helper module is added.

**Must not change:**

- `commitment.py` (including `verify_complete_private` and `publish_commitment`),
  `authority.py`, and every other implementation file;
- all 19 seal-04 test modules and both seal-05 publication modules;
- every line of the two seal-05 producer modules outside E1 and E2;
- the synthetic records helper, `conftest.py`, `pytest.ini`, `pyproject.toml`, the
  reproduction script, the guard and the harness;
- P, the attestation, the rule contract and the schema catalogue;
- every seal, manifest, evidence, scope, disposition and confirmation record;
- the engine, the Agent API, the Ruleset, the replay and result schemas, and all inherited
  pins.

The diff of each permitted file is taken against its sealed seal-05 bytes, which the record
lists. Copies of those bytes are kept in the seal-05 qualifier snapshot.

## Repairs

**F1: availability of the producer registry and first-raw marker.**

The expected identity of each durable artifact is the hash-checked artifact that S's
generation boundary binds. The check runs in this order:

1. The boundary content is checked first, from present evidence. It must hold exactly one
   producer root, one marker and one REAL declaration. A defect here is FAILED_VERIFICATION,
   as at seal 05, because there is nothing to restore against.
2. Each durable artifact is then compared with its expected identity.
3. If either artifact is present with the wrong bytes, the attempt is FAILED_VERIFICATION,
   even if the other is missing.
4. Otherwise, if either artifact is missing or unreadable, the attempt is UNAVAILABLE.

| Durable registry or marker | Outcome |
| --- | --- |
| Missing | UNAVAILABLE |
| Unreadable (OSError, or not a regular file) | UNAVAILABLE |
| Present with the exact expected bytes | Verification continues |
| Present with wrong bytes, including a substituted restoration | FAILED_VERIFICATION; later attempts refused |

UNAVAILABLE permits only restoring the evidence already required and starting a new attempt
on the same S, G, boundary, payload, salt, audit and K. The producer never draws, generates,
seals, registers, marks or replaces anything.

The marker carries no timing, so the W-time check proves presence and byte identity, not
write-before-first-draw. The sealed generator enforces that ordering, so F1 changes nothing
W can prove.

**F2: W-04 classification in every chain shape (interpretation confirmed).**

A completed-stage continuation is a CONTINUE or RELEASE whose tuple contains S. After one:

| Later events | Outcome |
| --- | --- |
| Any event that is not a tuple-extending ISSUE | FAILED_VERIFICATION, through the same W-04 path as every other shape; later attempts refused |
| Only tuple-extending ISSUE events | REFUSED_PRECONDITION before any private read: not terminal, but W cannot be produced under the frozen verifier |
| A mix of both | FAILED_VERIFICATION |

Only the seal-05 special case in `_preconditions` is narrowed. The sealed verifier is
unchanged (D6). The existing redundant re-ISSUE test already follows this rule and stays
unchanged.

**F3: the W/PASS writes move inside the protected section.**

Retaining W, writing `W.json` and writing the PASS outcome happen inside the
`private_verification` protected action, under the same lease as the verification. PASS is
the last write. The attempt intent and the non-PASS outcomes stay where they are, and the
lock is not widened further. `authority.py` is unchanged.

Two seal-05 classifications are preserved:

- An exception during these writes propagates with no outcome. The next attempt lists it as
  interrupted, and a partial `W.json` fails closed.
- If the unchanged post-action recheck fails after PASS is written, the error propagates and
  no second outcome is written. While the lock is held, only source drift or outside
  tampering can cause this.

**Residual:** in that case W and PASS exist although the call raised. The error must be
resolved before the lead's ISSUE(+W).

**F4: operational W admissibility.**

A new `verify_operational_w(authority)` is read-only and takes nothing but the authority.
`check_publication_template` calls it before reading private values or retaining a receipt.
`issue_publication_authorization` calls it before its template recheck. A W is admissible
only if all of these hold:

| Check | Requirement |
| --- | --- |
| A1 | W resolves exactly: role W, decision PASS, this study, dependencies equal to the active P..G and S (binding P and I), and a registered independent verifier. |
| A2 | S's boundary passes the producer's D5 check (producer root, durable marker, one REAL declaration). |
| A3 | The producer's `W.json` holds exactly the bound W's canonical bytes. |
| A4 | Exactly one PASS outcome and no FAILED_VERIFICATION. The PASS outcome names the bound W, and its intent names the bound S, W's verifier and W's active tip. |
| A5 | W's one retained verification result matches W's tip and chain, with PASS and REAL. |
| A6 | The first event holding W is the lead's ISSUE. Only tuple-extending ISSUEs come between W's tip and that ISSUE. No later event revokes W. |

Public signatures, `verify_operational_u`, `publish_commitment` and the generic append are
unchanged. No new trust model is added, and an attacker who can forge every on-disk artifact
is out of scope. Template or checker revalidation at U issuance is excluded.

The F1 order, the preserved F3 classifications and A1–A6 are recorded as the implementer's
application of the rulings, which the lead may strike or amend at review.

## Legacy test edits

Disposition 03 superseded the FAILED_VERIFICATION expectation in these two sealed cases.
Seal 05 remains a historical PASS WITH FINDINGS against its exact bytes.

| Edit | Module and case | Seal-05 lines | Editor |
| --- | --- | --- | --- |
| E1 | `test_v6_e9_v2_gate8_producer.py`, W-05 variant `marker_file_removed` | 455 (entry), 464–465 (setup), 469–471 (assertions as they apply to this variant) | Implementer |
| E2 | `test_v6_e9_v2_independent_gate8_producer.py`, W-05 case `marker_not_durable` | 1006–1009 (`w05_evidence` branch), 1030 (entry), 1040 (assertion as it applies to this case) | Independent test author only |

Changes stay within those lines, plus lines inserted among them. Every other variant or case
runs exactly as at seal 05, and every other line stays byte-identical.

The preferred form changes the case in place to assert UNAVAILABLE. The fallback removes the
case and covers it in the author's new seal-06 module. Seal-06 evidence records each editor,
its context, the attempt ids and a line diff against the sealed bytes.

## Qualification and seal 06

Required coverage:

- S6-F1-01 to S6-F1-10:
  - the registry and the marker each missing, unreadable and mismatched;
  - restoration with the exact bytes giving PASS;
  - substituted restoration giving FAILED_VERIFICATION;
  - mismatch taking precedence over a missing artifact;
  - boundary defects staying FAILED_VERIFICATION;
  - proof that recovery replaces nothing.
- S6-F2-01 to S6-F2-03: forbidden events after completed CONTINUE and RELEASE shapes,
  ISSUE-only tails, and mixed tails.
- S6-F3-01 to S6-F3-05:
  - the lock and tip at each write;
  - an append attempted between verification and PASS refused as busy;
  - both preserved classifications;
  - non-PASS outcomes still written after the lease.
- S6-F4-01 to S6-F4-08:
  - a hand-built W, a missing PASS outcome, a mismatched PASS outcome, the wrong producer
    root or attempt, and a hand W after FAILED_VERIFICATION;
  - each of A1–A6 violated on its own;
  - the valid producer path;
  - signatures and value-freedom.
- Regression: every unchanged module still passes, including all N1 coverage.

Seal 06 follows the seal-05 model:

- the manifest rule is unchanged, and manifest attempts continue from 24;
- the final 06 pair and `v2_final_manifest_seal_06.json` give a new instrument identity;
- every manifested file is rehashed before and after each run;
- all changes stay uncommitted during qualification.

An independent qualifier, who is neither the implementer nor the independent test author,
reproduces the seal and works through the checklist. The qualifier diffs the three permitted
files against the sealed bytes and confirms that `commitment.py` and `authority.py` are
unchanged. Findings are recorded in `v2_synthetic_qualification_evidence_06.json` without
remediation, unless a finding is a BLOCKER or shows the seal is invalid.

**Stopping rule:** one revision, one seal, one reproduction.

**Stop conditions:** the implementer stops and reports, without expanding the boundary, if:

- any repair needs a file or line outside the boundary;
- moving the writes exposes a different failure mode from the two preserved ones;
- F4 cannot be met by the unchanged producer-origin flows;
- any repair needs a verifier change, new normative text or a schema change;
- a BLOCKER appears, or evidence that a seal is invalid.
