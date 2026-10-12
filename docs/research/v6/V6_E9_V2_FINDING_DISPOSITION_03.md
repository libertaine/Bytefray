# E9 v2 seal-05 disposition and Gate-8 findings

**Recorded 2026-10-06.** This page summarizes the write-once record
`tools/research/v6/e9/v2_finding_disposition_03.json`
(raw SHA-256 `3c7a21474282c5a9da98871b4736b0d901a2de330dcef1301cd83d5fb8c67171`).
If the two ever differ, the JSON record governs.

The record covers seal 05 (`v6-e9-instrument-v2-fd0b524b9712`; seal raw SHA-256
`7ecb1195…ca570f040c`) and its independent reproduction, recorded in
`v2_synthetic_qualification_evidence_05.json` (raw SHA-256 `0d8b5ace…40cefa8c`).
That reproduction found nine findings, G8-IQ-F1 to G8-IQ-F9 (F1–F9 below).
This ruling does not alter seal 05, its manifests or its evidence. Dispositions 01
and 02, both lead confirmations, the Gate-8 scope 01 and its confirmation remain in
force. All 323 seal-05 manifested files were rehashed and unchanged at recording.

## Step closure

| Item | Status |
| --- | --- |
| Seal 04 | PASS WITH FINDINGS |
| Seal 05 | **PASS WITH FINDINGS** |
| Seal-05 independent reproduction | **PASS**, 764/764 (accepted) |
| N1 | **RESOLVED** by seal 05 |
| Gate 8 operational acceptance | **NOT ESTABLISHED** |
| Seal 06 | **Required** before operational Gate 8 |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |

The reproduction was accepted because 764/764 tests passed, ruff and mypy were clean,
every identity and hash matched, the implementation stayed inside the authorized Gate-8
boundary, all 323 manifested files were unchanged, no REAL entropy or salt was consumed
and no operational action took place.

**Seal 05 must not be used for operational W production.** F1–F4 expose weaknesses in
the operational W path, so a bounded seal-06 revision is required before any operational
Gate-8 authorization.

Not authorized: seal-06 implementation (until its scope has been reviewed), Gate 7,
REAL entropy, operational generation, operational W production, salt creation,
operational publication, Q creation, O/V/A/R/B creation, or any other irreversible
real-study action.

## N1

N1 is resolved by seal 05, which discharges the N1 Gate-8 blocker. The retained
comparison of seal 04 with seal 05 shows the intended correction. A clean C template
is no longer unpublishable merely because K holds realistic small values. Actual
protected decimal and hex disclosure in the designated text fields is still refused.

## Rulings

| ID | Disposition |
| --- | --- |
| F1 | **FIX IN SEAL 06** |
| F2 | **FIX IN SEAL 06** |
| F3 | **FIX IN SEAL 06** |
| F4 | **FIX IN SEAL 06** |
| F5 | Record only |
| F6, F7, F8, F9 | Record only; no implementation change |

**F1: a missing or unreadable producer registry or first-raw marker is UNAVAILABLE.**
This applies only while nothing shows that the expected artifact's identity has changed.
It is a recoverable evidence-availability condition, not by itself a scientific failure.

| Case | Outcome |
| --- | --- |
| Expected artifact missing or unreadable | UNAVAILABLE |
| Exact expected artifact restored | Verification may resume |
| Artifact present with wrong bytes, hash or identity | FAILED_VERIFICATION |
| Restoration with substituted or inconsistent material | FAILED_VERIFICATION |

UNAVAILABLE never permits generation of replacement scientific material. It permits only
recovery of the evidence already required and continuation with the same study state.
Sealed coverage is required for the missing, unreadable, correctly restored and
mismatched cases.

**F2: unexpected log events are classified the same way in every chain shape.** The
existing W-04 semantics govern. A genuinely unexpected or forbidden log event is
FAILED_VERIFICATION, including after a completed-stage continuation. The completed-stage
special case must not turn that defect into a retryable condition. The distinction
stays: missing or unavailable evidence is potentially recoverable (UNAVAILABLE), and a
present but semantically invalid authority event is terminal (FAILED_VERIFICATION). A
sealed test must cover the previously untested completed-stage case.

**F3: W issuance, W retention and the PASS outcome move inside the protected section.**
This follows the Gate-8 scope text. The protected section must cover the whole
verification-and-write transition, so no other authority change can interleave between
a successful verification and the durable recording of its result. It must not be
widened beyond that. Sealed coverage must show that verification and the retention of
W and PASS happen under the same protected authority state.

**F4: an explicit operational W admissibility requirement.** A hand-built W appended
through the generic authority mechanism must not be enough to enter the operational
pre-U or U-issuance path. Both the pre-U template check and the dedicated U-issuance path
must require evidence that the W is the one produced by the authorized Gate-8 producer
and that its retained outcome is PASS. As applicable, the check covers at least:

- the expected study and instrument identity;
- the producer root and the first-raw marker;
- the W record identity and digest;
- the matching producer attempt and the matching retained PASS outcome;
- the authority-chain relationship and active tip;
- any receipt or attestation bindings the adopted contract already requires.

Seal 06 adds no new cryptographic trust model. The fix closes the generic-append bypass
under the existing evidence model. It does not claim to resist an attacker who can write
arbitrary files and forge every trusted on-disk artifact, unless the frozen protocol
already authenticates against that threat. Negative tests are required for:

- a hand-built W without producer evidence;
- a W without its matching PASS outcome;
- a mismatched PASS outcome;
- a W from the wrong producer root or attempt.

A valid producer W with its matching PASS outcome must still progress.

**F5 is recorded only.** An arbitrary exception must not automatically become
FAILED_VERIFICATION, because that could turn an implementation defect, parser bug or
runtime fault into an irreversible scientific failure. Genuinely unclassified exceptions
keep the existing interrupted/retry behavior. A specific deterministic malformed-input
exception that should count as a verification failure would need its own disposition.

**F6–F9 are recorded only.**

- F6: the continuation evidence-id convention is not repaired.
- F7: the marker scan is not expanded.
- F8: the evidence-id wording is not redesigned.
- F9: fullwidth and leading-zero representation matching is not added.

Any future change to F5–F9 needs its own disposition.

## Seal-06 scope

The lead authorized a write-once seal-06 scope record limited to F1–F4. It may permit
changes only to the minimum existing Gate-8 implementation and the new qualification
tests needed for those four dispositions. It must not modify:

- the adopted protocol or schemas;
- seal-04 or seal-05 records, manifests or evidence;
- prior dispositions or confirmations;
- inherited engine or source pins;
- unrelated Gate-8 behavior;
- the recorded-only findings F5–F9.

If any F1–F4 repair proves impossible without changing frozen normative text or going
outside this boundary, the implementer stops and returns the conflict. The scope is not
amended implicitly. Once written, the scope record's identity, hash and exact file
boundary go back to the lead. **Seal-06 implementation is not authorized until that scope
has been reviewed.**
