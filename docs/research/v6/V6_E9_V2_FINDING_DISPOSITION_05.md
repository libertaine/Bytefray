# E9 v2 Seal-07 disposition (05)

Recorded 2026-10-08 from the research lead's disposition of the Seal-07 independent
reproduction, supplied in conversation on 2026-10-07. The write-once machine record is
`tools/research/v6/e9/v2_finding_disposition_05.json`, raw SHA-256
`5bf0c83ba0371224a1d722f07017af7cbcb399d1e413ce365b26b814df52ae29`.
The JSON contains the complete transcribed ruling text (12,023 bytes, raw SHA-256
`75bdb70f7477982b3ff5e00a16a5d4ec7bc2f8eefc188be8322900c510711ded`) and governs this
mirror. This transcription grants no authority of its own.

| Item | Disposition |
| --- | --- |
| Seal 06 | PASS WITH FINDINGS |
| Seal 07 (`v6-e9-instrument-v2-3c2bda92b3c0`, seal raw `fe2e9a4b…`) | CREATED; preserved exactly as created |
| Candidate 30 | = final_07 (attempt_30 and final_07 manifests byte-identical; 293 + 34 files) |
| Seal-07 implementer validation | PASS (1237 collected, 1231 passed, 6 skipped) |
| Seal-07 independent reproduction | FAIL: every run passed, but S7-IQ-F1 is a demonstrated BLOCKER |
| Seal 07 operationally admissible | NO |
| S7-IQ-F1 | BLOCKER CONFIRMED; repair in Seal 08 before any operational W |
| S7-IQ-F2 | INCLUDE IN SEAL 08 |
| S7-IQ-F3 to S7-IQ-F10 | RECORD ONLY; no source-code repair without separate disposition |
| Gate-8 operational acceptance | NOT ESTABLISHED |
| Execution | LOCKED |
| Requirement C; historical coverage | NOT ESTABLISHED |
| Q | Absent |

All 327 Seal-07 manifested files were rehashed and found unchanged before recording.
Seal 07, its final manifests, its evidence, candidate 30 and every earlier record remain
unchanged. Passing all 1231 non-skipped tests in both validation runs does not override
the demonstrated blocker. The independent reproduction did what it was meant to do.

## S7-IQ-F1: blocker confirmed

The invariant is: **positive mismatch evidence takes precedence over unavailability.**
Seal 07 violates it in one combined condition: this G's registry entry is present with
wrong bytes while another registry-scan input is unavailable. In that state Seal 07
records `UNAVAILABLE`, and a later retry can reach PASS. The required result is
`FAILED_VERIFICATION`.

Historical origin, as the lead distinguished it:

- Under Seal 06's `OSError` handling, some masking already occurred when an other-G
  entry or event-file read failed during the scan.
- The masking of a wrong-bytes current-G registry entry is introduced or exposed by
  Seal 07's typed-unavailability implementation.
- Whatever its origin, Seal 07 had to satisfy the complete frozen F1 precedence rule,
  and it does not. The inherited part does not downgrade the finding.

The qualifier's probe supports this distinction. With the G-record read made
unavailable, Seal 06 gave `FAILED_VERIFICATION` and Seal 07 gives `UNAVAILABLE` then
`PASS`. With an other-G entry sorted first, or with an event file, made unavailable,
both seals give `UNAVAILABLE` then `PASS`.

**Seal-08 repair ordering** at the producer-registry / first-raw-marker boundary:

1. Gather and check every positive mismatch evidence that can still be evaluated.
2. A known current-G registry mismatch is `FAILED_VERIFICATION`.
3. A known first-raw-marker mismatch is `FAILED_VERIFICATION`.
4. These positive mismatches win even if another required registry-scan artifact is
   unavailable.
5. Deferred registry unavailability may produce `UNAVAILABLE` only after every
   available positive mismatch check has run.
6. With no positive mismatch and required registry material unavailable, the result is
   `UNAVAILABLE`.
7. Unrelated `Unavailable` exceptions elsewhere are not converted into this deferred
   mechanism.

Keep the correction narrowly to the mapped registry/marker ordering logic. A retry
after a genuine positive mismatch stays terminal under the existing rules.

**Required Seal-08 F1 qualification** (both implementer and independent tests, at least):

| Case | Expected |
| --- | --- |
| Current-G mismatch + other-G unavailable | `FAILED_VERIFICATION` |
| Current-G mismatch + event-file unavailable | `FAILED_VERIFICATION` |
| Marker mismatch + other-G unavailable | `FAILED_VERIFICATION` |
| Marker mismatch + event-file unavailable | `FAILED_VERIFICATION` |
| No mismatch + other-G unavailable | `UNAVAILABLE` |
| No mismatch + event-file unavailable | `UNAVAILABLE` |
| Current-G registry itself unavailable | Frozen availability behavior, with no manufactured mismatch evidence that could not actually be observed |
| Retry | A genuine mismatch never becomes PASS through availability recovery; a pure `UNAVAILABLE` condition may recover once the exact required evidence is available |

The independent author derives these expectations from the governing records and
this disposition, not from the implementer's new test module.

## Superseded Seal-07 provenance claim

`v2_seal07_f1_correction_provenance_01.json`
(`v6-e9-v2-seal07-f1-provenance-8f49ad314cca`, raw `b237966c…`), at
`body.implementation.not_deferred`, states that "positive mismatch evidence keeps
its frozen classification". That statement is incorrect as a description of the
implementation. The record is **not edited**. It is preserved as evidence of what was
believed at sealing time. This disposition supersedes the claim:

> Seal-07 intended to preserve positive-mismatch precedence, but independent
> qualification demonstrated that the implementation does not preserve it for all
> combined registry-unavailability states.

## S7-IQ-F2: included in Seal 08

Seal 07 records protected-entry unavailability as `UNAVAILABLE`. Planning Revision 02
specifies `REFUSED_PRECONDITION`. Seal 08 adopts the planning distinction:

- **Before** the protected verification state has been successfully entered: failure
  to establish the required protected/lease state is `REFUSED_PRECONDITION`.
  Verification has not yet reached the state in which durable scientific evidence is
  evaluated.
- **After** the protected state has been successfully entered: a required durable
  evidence artifact becoming unavailable keeps the existing `UNAVAILABLE`
  classification where F1 specifies it.

Not every `Unavailable` is translated to `REFUSED_PRECONDITION`. Both implementer and
independently authored regression coverage must prove the distinction. If the frozen
Scope/Revision text shows a narrower meaning during scope drafting, stop and return the
exact contradiction.

## S7-IQ-F3 to S7-IQ-F10: record only

Seal 08 does not expand to repair these findings, and none of them is authorized as a
source-code repair without a separate disposition. Tests whose scenarios were shaped by
the lead's wording remain a provenance limitation.

No contemporaneous repository record of the original Seal-07 implementation
authorization exists (S7-IQ-F8). That remains a documentation note. No such record may
be fabricated or backdated. A present-day record may state that the authorization
existed in conversation, but only if it is clearly marked retrospective. This
disposition creates no such record.

## Seal-08 requirements

- **Scope.** A new write-once bounded Seal-08 scope. Scope 03 and its amendment are
  not edited. The default implementation boundary is
  `tools/research/v6/e9/v2/private_verification.py` alone. If S7-IQ-F2 or the complete
  F1 repair genuinely needs another implementation file, identify the exact dependency
  and stop before freezing the scope.
- **Qualification.** Prefer the new modules
  `engine/tests/test_v6_e9_v2_gate8_seal08.py` and
  `engine/tests/test_v6_e9_v2_independent_gate8_seal08.py`. Seal-07 tests stay
  byte-identical unless a direct conflict makes an edit unavoidable. Any sealed test
  that directly asserts superseded behavior is returned before scope freeze.
- **Candidates.** Candidate 30 is sealed and immutable. The next candidate is expected
  to be 31, binding the repaired source and the new qualification bytes. Any later
  source or test edit requires candidate 32, and so on. No earlier manifest is
  overwritten.
- **Validation.** Fresh only; Seal-07 results do not qualify Seal 08. At minimum:
  - targeted F1 combined-precedence tests and targeted S7-IQ-F2 tests;
  - both complete Seal-08 focused suites;
  - all prior applicable Gate-8 tests;
  - the full applicable V2 synthetic suite, with complete counts;
  - WSL/native cases for the Windows skips;
  - Ruff, mypy engine and mypy client;
  - inherited-binding/preservation checks.

  Every failed or interrupted attempt is preserved.
- **Sealing.** Only on an exact, completely passing candidate pair:
  1. create byte-identical final manifests;
  2. rehash immediately before sealing;
  3. create Seal 08 write-once and compute the instrument identity;
  4. make no source or test change after sealing;
  5. have a fresh independent qualifier reproduce from the sealed manifests, probing
     combined positive-mismatch + unavailability states specifically.

  A post-seal blocker preserves Seal 08 and requires another disposition.

## Private evidence and repository state

The Seal-07 private provenance backup
(`D:\Projects\BATTLE2-private-evidence\v6-e9-seal07-transcript-provenance\`) is
accepted as preservation evidence. It is never committed. Its lack of an off-machine
copy is not a Seal-08 blocker, but the limitation is retained. The original
transcripts, Codex rollouts, cache evidence and the backup are not deleted.

Nothing is committed or pushed during the active Seal-08 cycle. The baseline remains
`e035def989dfc5e26ae3eb2c9ccfd16aed54b66c`. The uncommitted Seal-07/Seal-08 research
state stays intact until the Seal-08 independent reproduction result is known.

## Not authorized

REAL entropy, operational generation, operational W, salt, native matches, operational
publication, Q, Gate 7, operational O/V/A/R/B and real-study stale-lock clearance all
remain unauthorized.

Implementation may proceed after scope freeze without further confirmation, unless
scope drafting proves that another implementation file, or an edit to an existing
sealed test, is needed beyond the proposed boundary. In that case work stops before
implementation.
