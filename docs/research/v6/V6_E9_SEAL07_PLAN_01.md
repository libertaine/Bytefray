# E9 v2 seal 07: proposed bounded scope and open decisions (01)

**PROPOSED, 2026-10-07. Planning and scope drafting only.** The authority for this plan is the
research lead's seal-06 disposition of 2026-10-07. That disposition is not yet in a write-once
record (see Q7). Nothing here is implemented or authorized for implementation.

Seal 06 and every seal-06 record are unchanged. At planning time, all 325 seal-06 manifested
files were rehashed against `v2_implementation_manifest_final_06.json` and
`v2_qualification_manifest_final_06.json`, and all were unchanged. Git HEAD is `2dd8f69`.

| Item | Status |
| --- | --- |
| Protocol | `v6-e9-prereg-v2-539a60806eab` (unchanged; no amendment proposed) |
| Instrument | seal 06, `v6-e9-instrument-v2-29f12a833a09`, PASS WITH FINDINGS |
| Seal-06 independent reproduction | PASS, 877/877 |
| S6-IQ-F1 | Seal 07 required |
| S6-IQ-F2 | Seal 07, mandatory blocker for operational W |
| S6-IQ-F3, F4, F5 | Record only |
| Gate-8 operational acceptance | NOT ESTABLISHED |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |
| Gate 7, REAL entropy, operational generation, W, salt, publication | Not authorized |

Line numbers below refer to the sealed seal-06 bytes.

## 1. Purpose and proposed boundary

Seal 07 repairs exactly two findings:

- **S6-IQ-F1.** Durable-evidence reads must classify non-regular filesystem objects promptly
  and must never block while the authority lock is held.
- **S6-IQ-F2.** A crash after W.json is durable but before the PASS outcome is durable must be
  recoverable. Recovery must re-verify the existing W exactly and must never produce a
  second W.

The F3, F4 and F5 rulings stand as given:

- **F3.** `verify_operational_w` stays an internal, context-dependent helper. Seal 07 does
  not change it, except under option Q4(ii).
- **F4.** No stronger independence is claimed than the evidence supports.
- **F5.** Needs no change.

**Proposed file boundary:**

| File | Change |
| --- | --- |
| `tools/research/v6/e9/v2/private_verification.py` | F1 reader and F2 recovery only |
| `engine/tests/test_v6_e9_v2_gate8_seal07.py` | New. Written by the implementer. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py` | New. Written by a new independent test author. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py` | Legacy edit L1 only (§4). Made only by the new independent test author. |

Everything else must not change, as in scope 02:

- `authority.py`, `commitment.py` and every other implementation file;
- every other sealed test module;
- the helper, `conftest.py`, `pytest.ini`, `pyproject.toml`, the guard, the harness and the
  reproduction script;
- P, the attestation, the contract and the schemas;
- every seal, manifest, evidence, scope, disposition and confirmation record.

Q1(c) and Q3(b) would widen this boundary into `authority.py`. This plan recommends neither.

**Not in scope:**

- generic transaction or journaling machinery;
- atomic-rename writers;
- changes to `durable_bytes`;
- making `verify_operational_w` safe as a standalone API;
- template revalidation at U issuance;
- any change to what W, U or C bind.

## 2. F1: non-regular objects at durable evidence paths

### 2.1 What seal 06 does (facts)

`_durable` (lines 178–183) and `_reader` (lines 100–112) call `Path.read_bytes()` and catch
only `OSError`. Both run inside `authority.protected`, with the lock held.

| Object at the path | Seal-06 behaviour |
| --- | --- |
| Missing | UNAVAILABLE (correct) |
| Directory | `OSError` (IsADirectoryError, or PermissionError on Windows), so UNAVAILABLE (correct; both seal-06 F1 suites test this) |
| Socket (POSIX) | `open` fails with an `OSError`, so UNAVAILABLE (correct by accident) |
| FIFO (POSIX) | `open` blocks with no writer. The call hangs with the lock held and writes no outcome. |
| `/dev/null`-like character device | Reads `b""`. That is a mismatch, so FAILED_VERIFICATION, which is terminal. |
| `/dev/zero`- or `/dev/urandom`-like device | The read never ends, so the call hangs or runs out of memory |
| Block device | Reads device bytes. That is a mismatch, so FAILED_VERIFICATION. |
| Symlink to a regular file | Followed, so the target's bytes decide |

The marker's `is_file()` guard was dropped at seal 06. That is the S6-IQ-F1 trigger.

### 2.2 Classification (derived; the lead may strike)

- **R1.** Registry and marker: a non-regular object is **UNAVAILABLE**. This is verbatim
  scope 02 `repairs.F1.classification`: "unreadable (an OSError while reading, or the path is
  not a regular file): UNAVAILABLE". No new semantics are introduced. The F1 precedence is
  unchanged: if the other artifact is present with wrong bytes, the attempt is
  FAILED_VERIFICATION. The recovery constraint is also unchanged: only exact restoration
  followed by a new attempt.
- **R2.** Retained private evidence (`evidence-raw/<sha>.bin` through `_reader`): a
  non-regular object is **UNAVAILABLE**. This extends the same clause and matches `_reader`'s
  existing rule, "absence is UNAVAILABLE, changed bytes an integrity failure". It applies
  only if Q1 includes `_reader`.
- **R3.** `W.json` and the PASS attempt intent: a non-regular object takes the existing
  refusal paths, with no new outcome class.
  - In the producer, it is "a partial W file is present", so REFUSED_PRECONDITION.
  - In `verify_operational_w` (A3/A4), it is not admissible. That is a refusal, not a
    producer outcome.

### 2.3 Q1: which reads are "durable evidence paths" (open)

Reads made while the lock is held:

| Read | Module | Under the lock in | Proposed |
| --- | --- | --- | --- |
| Registry and marker (`_durable`) | private_verification | `_verify`, A2 | **In** |
| W.json and PASS intent (`_durable`) | private_verification | A3/A4, F2 recovery | **In** |
| `evidence-raw/*.bin` (`_reader`) | private_verification | `_verify`, A2/A5 | **In** (recommended) |
| Attempt outcomes (`_outcomes`) | private_verification | `_preconditions`, A4 | Residual |
| Event log (`_durable_log`) | private_verification | `_verify`, A2/A6 | Residual. `authority._state` always reads the same files first. |
| `event-*.json`, `active.json` (`_state`) | authority | every protected call | Residual (outside the boundary) |
| `evidence-records/*.json` (`resolve`) | authority | `_check`, `_verify` | Residual (outside the boundary) |
| `producer-roots/*.json` (`registered_producers`, every G) | authority | F1 registry check | Residual (outside the boundary) |

Options:

- **(a)** Registry, marker, W.json and intent only. This covers S6-IQ-F1 literally. It leaves
  the same hang and terminal-conversion defect at `evidence-raw`, which is the retained
  private evidence itself.
- **(b) Recommended.** (a) plus `_reader`: every hash-identified evidence read that
  `private_verification.py` makes. The residuals in the table are recorded explicitly.
- **(c)** (b) plus the reads in `authority.py`. This is the only option that fully meets "no
  blocking open while the lock is held" for every path under the authority root. It changes a
  sealed must-not-change module and touches every protected operation.

### 2.4 Q2: mechanism and symlinks (open)

**Recommended mechanism:**

1. Classify by `stat` (following symlinks) before opening. A non-regular object is classified
   at once and never opened.
2. Open a regular file through `Path.open`.
3. Confirm with `fstat` that the opened descriptor is a regular file.
4. Only then read.

This keeps two sealed fault-injection and spy seams working:

- the independent seal-06 `block_reads`, which patches `io.open`, `builtins.open` and
  `os.open`;
- the independent seal-05 `private_read_spy`, which patches `Path.open`.

The second seam backs the "no private read before refusal" assertions. A reader built on raw
`os.open` would bypass it silently, so those assertions would keep passing without checking
anything.

**Residual:** a concurrent writer could swap a regular file for a FIFO between `stat` and
`open`. That needs write access to the private root while the lock is held, which is outside
the scope-02 trust model ("an attacker who can forge every on-disk artifact is out of scope").

The alternative is `os.open(..., O_NONBLOCK)`. It is race-free on POSIX, but Windows does not
provide the flag. It also bypasses the `Path.open` spy, and fixing that would need a further
legacy edit of a seal-05 independent module.

**Symlinks:** the recommendation is to follow them and classify the target, because identity
is by bytes, as at seal 06. Refusing every symlink would be a new policy, and the result
would depend on the platform.

### 2.5 Recorded F1 residuals (no change)

- Every "Residual" row in the Q1 table, including a FIFO at some other G's registry, which
  `registered_producers()` reads.
- The swap race under Q2.

## 3. F2: recovery after a crash between W.json and PASS

### 3.1 Crash windows in the producer's write sequence (facts)

| # | The crash tears or interrupts | Retry today (seal 06) | In F2? |
| --- | --- | --- | --- |
| C1 | The intent write (before the lock) | Listed as interrupted; recovers | — |
| C2 | Verification (no writes) | Listed as interrupted; recovers | — |
| C3 | The verification-result blob in `_verify` (torn) | Retention collision ("immutable private evidence collision") in the verification phase, so **FAILED_VERIFICATION, which is terminal** | No. Q5. |
| C4 | Result retained, before W retention | Recovers (W is deterministic; retention is idempotent) | — |
| C5 | The retained W record (torn) | Collision in the write phase. It raises with no outcome on every retry, so the study is stranded. | No. Q5. |
| C6 | W retained, before W.json | Recovers (idempotent; W.json is then written) | — |
| C7 | W.json (torn or partial) | REFUSED_PRECONDITION on every retry, so stranded. This is the scope-02 "partial W.json fails closed" rule. | Residual (R7) |
| **C8** | **W.json complete, before PASS** | **REFUSED_PRECONDITION on every retry, so stranded** | **Yes. This is the F2 core.** |
| C9 | The PASS outcome (torn, for example zero-length after power loss) | `_outcomes` fails with "malformed private JSON", so REFUSED on every retry. A4 also fails, so stranded. | Literally, yes. Q4. |
| C10 | PASS complete, before the post-action recheck | Scope-02 residual (W and PASS exist; the error must be resolved first) | — |

**Every real crash inside the protected section (C2–C10), whether power loss or process kill,
also leaves `exclusive.lock` behind.** The `finally` clause in `AuthorityLog.exclusive` never
runs. Every protected call and every
append then fails with "authority busy or interrupted transaction". That includes recovery
and a HOLD. This is designed: the `authority.py` docstring says interrupted transactions
"are never silently repaired by this module", and the sealed independent authority test
`crash_lock` asserts it. See Q3.

**W is deterministic.**

- `make_record` digests the canonical body only; there is no time and no nonce.
- The body contains no attempt number.
- The retained verification result holds only hashes, counts and the tip.

So a complete re-verification under the same verifier and tip re-derives W byte for byte.

### 3.2 Proposed recovery rule (derived from the lead's preferred direction)

Recovery applies when W.json is present and no PASS outcome exists. All checks run inside
the existing `private_verification` protected action. The precondition steps run in order;
steps 6–8 follow, still under the lease.

**Preconditions.** None of these reads a private value. Each failure is non-terminal:

1. Every existing seal-06 precondition still applies (tuple through S, a registered
   independent verifier, no later roles, the F2 tail rule).
2. If a PASS outcome exists, the attempt is **REFUSED**, "W already produced for this S". This
   happens before any verification. Status quo (R8).
3. If FAILED_VERIFICATION exists, the attempt is **REFUSED**. Status quo.
4. W.json is read through the F1 reader. It is **REFUSED** with the existing "partial W file"
   wording (status quo, R7) if:
   - it is non-regular or unreadable; or
   - it is not a canonical W record (strict private JSON, canonical bytes, record role W).
5. W.json's verifier must equal the caller's verifier, and its `active_authority_tip` must
   equal the current durable tip. Otherwise the attempt is **REFUSED** (R5).

**Verification:**

6. Run the complete, unchanged `_verify` under the lease. It re-derives W′. The retention of
   the result blob is idempotent. Any failure is FAILED_VERIFICATION, exactly as in a first
   attempt.
7. If the canonical bytes of W′ differ in any way from W.json, the attempt is
   **FAILED_VERIFICATION** (R6).

**Write:**

8. `retain_record(W′)` (idempotent). **Do not write W.json.** Write the PASS outcome for
   **this** attempt as the last write (R4). Write nothing else. Never delete, rename or
   rewrite anything.

**Derived rulings (the lead may strike):**

- **R4.** PASS is recorded on the recovery attempt. Its intent already names the same S, the
  same verifier and W's tip, so the unchanged A4 accepts it.
  - The interrupted attempt keeps no outcome and stays INTERRUPTED (write-once, "retries are
    new, separately recorded attempts").
  - The outcome keys are unchanged; a sealed test asserts the exact key set. A recovery PASS
    puts one fixed marker in the existing `reason` field. A normal PASS keeps
    `reason: null`.
- **R5.** A caller or state mismatch is refused, not failed: it is not evidence of
  tampering, and a terminal outcome would destroy a valid study.
  - The consequence needs explicit acknowledgment. **No authority event, not even a HOLD,
    may be appended between the crash and recovery.** After any event the tip has moved.
    Exact recovery then cannot happen without a second W, so a separate lead disposition is
    needed.
- **R6.** A W.json for this S that is well-formed, matches the verifier and tip, and still
  differs from the re-derived W is evidence of replacement. This is the F1 "present with
  wrong bytes" principle, so the attempt is FAILED_VERIFICATION, which is terminal.
- **R7.** A torn, garbage or non-regular W.json stays REFUSED_PRECONDITION with the existing
  "partial W file" wording. Scope 02 preserved this classification, and two sealed tests
  depend on it. It remains a residual (C7).
- **R8.** If PASS exists, the attempt is refused before the verifier is called. A sealed test
  asserts exactly one verifier call.
- **R9.** `verify_operational_w` is unchanged. The recovered state must pass the unchanged
  A1–A6 once the lead issues W.

These rules guarantee idempotence and a single W:

- W.json is write-once and never written by recovery.
- PASS is written only when no PASS exists.
- Everything runs under the exclusive lock.
- A crash during the recovery's own PASS write leaves the C8 state again, and the next
  retry recovers.

### 3.3 Q3: the lock left by a real crash (open)

No coded or recorded procedure exists for clearing a crash-left `exclusive.lock`. Without
one, F2 recovery cannot be reached after a real crash.

- **(a) Recommended.** Clearing the lock is a manual action outside the code. It is
  authorized and recorded by the lead, for example as a write-once record. That record
  confirms that no producer process is alive and gives the lock's bytes, the tip and the
  folder listing. Then the recovery attempt runs. Seal 07 code does not touch the lock. The
  record's required content would be new normative text, supplied by the lead's ruling.
- **(b)** Coded stale-lock recovery in `authority.py`. This widens the boundary, adds generic
  machinery and contradicts the module's "never silently repaired" rule.

### 3.4 Q4: a torn PASS outcome (C9) (open)

- **(i) Recommended.** Keep it fail-closed (status quo) and record it as a residual alongside
  C7.
- **(ii)** Recognize a torn outcome file as an interrupted PASS write. That requires:
  - matching platform-dependent crash content (empty, a proper prefix, or a zero-filled
    tail) against the exact PASS outcome that attempt would have written;
  - changing the outcome reader that A4 uses.

  This is the crash-content heuristic machinery the lead asked to avoid.

**C9 is inside the literal F2 window.** Option (i) therefore needs the lead's explicit
acceptance that a torn PASS write, unlike a missing one, still strands the study.

### 3.5 Q5: pre-W crash windows found during planning (open; record only recommended)

C3 and C5 are pre-existing since seal 05 and outside F2's stated boundary.

- **C3** turns a torn write into a terminal FAILED_VERIFICATION. A blob whose bytes do not
  hash to its own file name is self-evidently torn. This is the same "filesystem condition
  becomes a terminal scientific failure" pattern the lead rejected for F1.
- **C5** strands the study with no outcome.

Under the stopping rule, both are recommended **record only**, like C7 and C9. If the lead
includes C3, it needs its own classification ruling, most naturally UNAVAILABLE with restore
and retry, and this plan would be revised.

## 4. Conflicts with sealed tests and compatibility constraints

**L1: a legacy edit is required.**

`test_v6_e9_v2_independent_gate8_seal06.py`, `test_s6_f3_03_…[outcome-1-stop]`, lines
702–709. These lines assert that after W.json is complete and PASS is missing, a retry is
refused and "never PASS". F2 overrules exactly that.

- The `[W.json-partial_then_stop]` branch shares those lines. Under R7 it stays valid.
- The edit splits off the outcome-1 case and asserts exact recovery: PASS on attempt 2,
  interrupted `[1]`, and W.json unchanged.
- The module was written by an independent author, so only a new independent test author
  may make the edit (as with E2).

No other conflicting assertion was found in a targeted sweep. The sweep covered W.json,
PASS-removal, unreadable-path and reader-patching cases in:

- both seal-06 modules;
- both seal-05 producer modules;
- both publication modules.

The S6-F4 cases that remove PASS act on an issued W, which the producer already refuses.
Before the scope record is written, the implementer repeats the sweep over every sealed
module. Any further conflict is returned to the lead, not edited.

**Constraints the implementation must keep. Breaking any of them is a stop condition:**

| Constraint | Reason |
| --- | --- |
| The refusal for a partial W keeps "partial W file", and the refusal when PASS exists keeps "already produced" | Implementer S6-F3-03 and seal-05 W-09 match these strings |
| Evidence opens still go through `Path.open` (Q2) | Sealed spies and injectors |
| `pv._reader(authority)` keeps its name and shape, returning `callable(ref)` | Three sealed tests wrap it |
| W, PASS and outcome writes still go through `pv.durable_bytes`; the outcome key set is unchanged | Write spies in both seal-06 modules; `OUTCOME_KEYS` |
| When PASS exists, the retry makes no verifier call | Seal-05 independent W-09 asserts one call |
| Directory and `PermissionError` faults stay UNAVAILABLE | Both seal-06 F1 suites |

## 5. Qualification plan (indicative coverage IDs)

Tests are synthetic and platform-independent. There is no real FIFO or device and no
platform-conditional skip, so the harness keeps 0 skipped.

**F1:**

- **S7-F1-01.** A real directory at the registry, the marker and an `evidence-raw` blob gives
  UNAVAILABLE, with no open of that path.
- **S7-F1-02.** Non-regular modes injected at the stat seam (FIFO, socket, character device,
  block device, other), at each covered path, give UNAVAILABLE without open or read.
- **S7-F1-03.** `stat` reports a regular file but `fstat` does not. The result is
  UNAVAILABLE, the descriptor is closed and nothing is read.
- **S7-F1-04.** Precedence: a non-regular artifact together with a wrong-bytes artifact gives
  FAILED_VERIFICATION.
- **S7-F1-05.** Exact restoration gives PASS. A substituted restoration gives
  FAILED_VERIFICATION. Nothing is replaced.
- **S7-F1-06.** A sentinel fails the test if any open of a non-regular object is attempted,
  including inside `verify_operational_w` (A2/A3/A4).
- **S7-F1-07.** Non-regular W.json and intent take the R3 refusal paths.

**F2:**

- **S7-F2-01.** A deliberate stop right after W.json is durable and before PASS. The retry
  recovers:
  - PASS on attempt 2, with interrupted `[1]` and the recovery marker;
  - W.json, the retained W and the result blob byte-identical;
  - exactly one complete re-verification;
  - no generator or entropy call;
  - a tree diff that shows only the attempt-2 intent and outcome added.
- **S7-F2-02.** Crash residue: W.json complete, no PASS and `exclusive.lock` left behind. The
  retry is refused, and nothing beyond its own intent and REFUSED outcome is written. After
  the Q3 clearance, recovery gives PASS.
- **S7-F2-03.** After recovery, further retries are REFUSED with "already produced", with
  no verifier call and no second PASS.
- **S7-F2-04.** Recovery, then the lead's ISSUE(+W). The unchanged `verify_operational_w`
  returns ADMISSIBLE, and the pre-U check proceeds.
- **S7-F2-05.** The recovery is refused for a different verifier, for any authority event
  since W's tip (HOLD, HOLD+CONTINUE, or a tuple-extending ISSUE), for a torn, garbage or
  non-regular W.json, for an existing PASS and for an existing FAILED_VERIFICATION.
- **S7-F2-06.** A well-formed W.json that differs from the re-derived W gives
  FAILED_VERIFICATION. This covers an altered field with its digest recomputed, and a W
  copied from another study.
- **S7-F2-07.** A crash during the recovery's own PASS write. The next retry recovers.
- **S7-F2-08.** No ordering of retries yields a second W.json or a second PASS. Recovery never
  deletes, renames or rewrites a file.

**Regression:** all 877 seal-06 tests pass, with only L1 edited.

## 6. Seal 07 and reproduction (process, as in scope 02)

- Manifests continue from attempt 25 under the unchanged manifest rule. `final_07` and
  `v2_final_manifest_seal_07.json` give a new instrument identity.
- Every manifested file is rehashed before and after each run. Everything stays uncommitted.
  Every run goes through the guarded harness.
- An independent qualifier reproduces the seal. The qualifier must be neither the
  implementer nor the independent test author.
- **F4-limited proposal (optional).** Draft the independent author's brief from the scope
  record's coverage IDs and rulings verbatim, with no scenario choices from the implementer.
  Record the brief's hash in the seal.
- **Transcript retention.** Back up the transcripts of both independent contexts privately at
  seal time, using the procedure applied to seal 06. Only hashes appear in the repository.
- **Stopping rule:** one revision, one seal, one reproduction. Later non-blocking findings are
  recorded without remediation.

## 7. Decisions requested before implementation

| # | Decision | Recommendation |
| --- | --- | --- |
| Q1 | F1 read boundary | (b): `_durable` and `_reader` in `private_verification.py`; the reads in `authority.py` and the bookkeeping and log reads are recorded residuals |
| Q2 | F1 mechanism and symlinks | `stat` first, then `Path.open`, then `fstat`; follow symlinks; the swap race is recorded as a residual |
| Q3 | Lock left by a real crash | (a): clearance is a manual record authorized by the lead; no code change to the lock |
| Q4 | Torn PASS outcome (C9) | (i): fail closed, recorded as a residual (needs explicit acceptance) |
| Q5 | Pre-W windows C3 and C5 | Record only |
| Q6 | Legacy edit L1 | Authorize it, made by a new independent test author only |
| Q7 | Records | Authorize transcribing the seal-06 disposition as write-once `v2_finding_disposition_04.json` with its mirror. After these rulings, authorize the write-once seal-07 scope record (`v2_gate8_scope_03.json`) with its mirror. |

Each of R1–R9 is derived. Each is labelled as derived, and the lead may strike or amend it at
review.

## 8. Stop conditions for implementation

The implementer stops and reports, without expanding the boundary, if:

- any repair needs a file or line outside the boundary;
- any sealed assertion other than L1 conflicts;
- any §4 constraint cannot be kept;
- recovery needs a W, outcome or verifier change beyond R4;
- a BLOCKER appears, or evidence that a seal is invalid.
