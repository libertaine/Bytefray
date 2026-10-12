# E9 v2 Gate-8 revision — proposed scope, design and qualification plan (01)

**PROPOSED, 2026-10-06. Planning and design review only.** Authority:
`tools/research/v6/e9/v2_finding_disposition_02_lead_confirmation.json`
(raw SHA-256 `f3e17a1929d982a1dbeda781113b5ce792571323bd7eaa350bbb0baeefa7729c`), which
confirms the gate ordering in `v2_finding_disposition_02.json` and authorizes this planning.
Nothing here is implemented or authorized for implementation. Seal 04 and every
seal-04 record are unchanged.

| Item | Status |
| --- | --- |
| Protocol | `v6-e9-prereg-v2-539a60806eab` (unchanged; no amendment proposed) |
| Instrument | seal 04, `v6-e9-instrument-v2-3c1023acb145`, PASS WITH FINDINGS |
| Independent reproduction | PASS, 582/582 |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |
| Gate 7 | Not authorized |

## 1. What the revision is and where it sits

In the frozen gate table, Gate 7 is the generation authorization G and Gate 8 is the
independent private commitment verification W. The confirmed ordering separates two
things that are both called "Gate 8":

- **The Gate-8 instrument revision.** The real W-record producer, the N1 correction, the
  N2 and N6 W-producer requirements, and their sealed qualification coverage. It must be
  implemented, sealed, independently reproduced and explicitly accepted before Gate 7
  can be authorized.
- **Operational Gate 8.** An independent W over the real payload. It still follows
  generation.

**The revision must also come before any operational record, not only before Gate 7.**
O, V, A, R and B all bind I and Q (contract R4–R8). The contract's change table says an
implementation or qualification-source change requires "new downstream operational
bindings". If the instrument changed after O was sealed, O, V, A, R and B would all
reopen. None of those records exists yet, so the safe order is: Gate-8 revision, then the
Q decision for that instrument, then Gates 3–6, then Gate 7.

**No protocol amendment is required.** Each change implements frozen text without
changing it:

| Change | Frozen text it implements | P effect |
| --- | --- | --- |
| W-record producer | R11; schema W fields and acceptance predicates; DS-W1/W2/W7 | None. All W body fields already exist in the schema. |
| N1 typed check | Schema C predicate: "no seeds, salt, private paths or raw diagnostics" | None under decision D2 option A. Option B needs an explicit interpretation ruling (§4.2.3). |
| N2 requirement | PG-R8: final private verification rechecks "the complete supplement/continuation chain" | None |
| N6 requirement | Replacement requirement: "Keep … OS-CSPRNG source"; G `sampling` | None |

The implementation manifest changes, so the instrument identity changes (seal 05). Logical
cell IDs depend on P only and stay equal. Private-root tokens and bootstrap reference
vectors depend on I and will change. The sealed vector tests use fixture sources, not the
live I, so they need no regeneration.

## 2. Proposed scope

**In scope:**

- **S1.** A W-record producer that runs the complete private verifier under the
  `private_verification` protected operation and writes W once.
- **S2.** N1: replace the whole-record M3 scan with a typed check (§4.2), resolving all
  seven required N1 items.
- **S3.** N2 for the producer: it derives the complete chain from the durable authority
  log and always passes `active_chain_tip`.
- **S4.** N6 for the producer: it requires the REAL entropy declaration.
- **S5.** Sealed qualification coverage for S1–S4, plus the existing suite unchanged.
- **S6 (derived, see D3).** A pre-authorization check of the proposed C template, run
  before U is issued.

**Not in scope:**

- N3, N4, N5, N7, N8 and N9 stay recorded only. N5 in particular is not folded into the
  N1 redesign. Supplement values outside K stay covered by the marker layer only, unless
  N5 gets its own disposition.
- The rest of N2 stays recorded only: verifier-side completeness and the fact that
  releases after W are not re-reproduced.
- Observation O-1 (§3) is recorded only.
- No changes to `generation.py`, `authority.py`, `integrity.py`, `inventory.py`,
  `records.py`, the scientific, reporting or dispatch modules, the schema catalogue, the
  rule contract, P, or any of the 19 sealed test modules.

**Stopping rule** (carried forward from disposition 01): one implementation revision,
then seal 05, then one independent reproduction. A newly discovered non-blocking finding
is recorded and does not open another implementation cycle, unless it is a BLOCKER or
shows the seal is invalid.

## 3. Facts established during planning (read-only)

These checks used only in-memory fixtures or test doubles in a scratch directory. No
entropy, no match, no repository writes other than this page and the confirmation record.

- **F1. No W producer exists.** `verify_complete_private` returns a result dictionary and
  `verify_W_bytes` checks an existing W record. Nothing builds a W record under
  `private_verification`. This is the M4 limitation.
- **F2. N1 attribution in C.** Digit runs come from three kinds of field:
  - Constant fields alone produce the runs **2, 6, 8, 9, 256 and 1412** in every possible
    C. 2 comes from record versions and `v2` prefixes. 6 and 9 come from `v6`/`e9` in schema
    tags and identity prefixes, and from `E9` in the permanent limitation. 8 comes from
    `UTF-8`, and 256 from the `sha256_raw` key and `SHA256`, both in the digest convention.
    1412 is N. A K containing any of these values blocks every C.
  - Derived fields (64-hex digests, identity suffixes, c) add short runs. Across fixtures
    they cover 63–65 of the values 0..99; the qualifier reported 65.
  - The fixture C has no free text that contains digits.
- **F3. The public part of the K candidate.** The current tracked tree has 45 literal seed
  values. All have 6 digits or fewer, 29 are below 100, and they include
  0, 1, 2, 3, 5, 7 and 42. The pinned E6/E8 lists hold 64 values of 14–16 digits. K
  members evidenced only privately were not inspected.
- **F4. Generated values are full width.** For 1412 uniform 64-bit draws, the expected
  number of values with fewer than 16 decimal digits is about 0.08. A decimal match of a
  generated value is therefore information-bearing; a decimal match of a small literal is
  not.
- **F5. An issued U cannot be replaced after generation.** This was checked with sealed
  test doubles. REVOKE of the issued U is accepted. ISSUE of a corrected U' is refused
  ("changed operational tuple requires verified no-draw reapproval"). So any M3 refusal
  after U is issued can never be fixed for that study. The same holds for an issued W.
- **F6 (observation O-1, recorded only).** The 16-hex check does not catch an unpadded hex
  form. About 1 in 16 values starts with a zero nibble (about 88 of 1412 expected). The
  padded form inside `0x…` is caught.
- **F7. Sealed chain grammar.** The chain must end at a CONTINUE or RELEASE event, and
  `active_chain_tip` is checked only when a completed-stage segment is present. An
  `ISSUE(+S)` after the last continuation sits outside the chain. Completeness of the
  chain's tail therefore has to be checked by the producer.
- **F8. Precedent for REAL-labelled fixtures.** The sealed suite already builds boundaries
  that declare REAL by hand, in
  `test_w_requires_exactly_the_expected_bound_entropy_source`. It uses them only for
  rejection.
- **F9. Compatibility.** The sealed publication tests build `PrivateValues` with three
  positional fields and place every leak in decision text. The proposed N1 design keeps
  that constructor and keeps those tests valid.

## 4. Proposed design

### 4.1 The W-record producer (S1, S3, S4)

The producer would live in a new module, `tools/research/v6/e9/v2/private_verification.py`:

```text
produce_private_verification(authority, *, verifier, expected_tip, operation_id) -> W RecordRef
```

The producer has no entropy-source parameter, takes no caller-supplied chain, tips,
history or commitment, and has no command-line entry point. Everything below runs inside
`authority.protected("private_verification", …)`.

1. **Preconditions, before any private byte is read.**
   - S is in the active issued tuple. W, U, C, D and F are not.
   - The tuple is not held, terminal or revoked, the tip is current, the source checker
     passes, and G was consumed by its own operation. The sealed `_check` enforces these.
   - `verifier` is a registered `independent_verifier`. It is not the S recorder, the O
     custodian, the lead or the publisher.
   - No W and no FAILED_VERIFICATION outcome already exists for this S.
2. **Attempt intent.** A write-once
   `private-verification/<S digest>/attempt-NNNN.intent.json` under the authority root,
   recording the S ref, lease tip and epoch, and the verifier.
3. **Read the bound bytes.**
   - Resolve S and its `generation_boundary`.
   - Read the payload, salt and audit through `authority.read_artifact`, plus the
     original K from O's K ref. All of these are retained by `generation_receipt`.
4. **Operational entropy (N6).**
   - Pass `entropy_source="REAL"` as a constant.
   - Also require that the boundary evidence contains the registered producer root for
     this G (equal to `registered_producers()[G]`) and its first-raw marker (D5, derived).
5. **Complete chain (N2).** Read the durable event log from the boundary's
   `active_authority_tip` onward and derive:
   - The chain, in the layout the sealed verifier accepts. For each CONTINUE or RELEASE,
     include the bound supplement (if any), the LeadContinuation and the event. Include
     intervening HOLD and ISSUE events in sequence.
   - The draw-time authority tips: the boundary tip, then each partial-generation
     CONTINUE or RELEASE.
   - A **tail check**: every event after the last continuation must be an ISSUE that only
     extends the tuple. Any other event fails closed.
   - `active_chain_tip`, set to the lease tip and always passed.
6. **History (PG-R8).** For every supplement in the chain, read its retained raw history
   and execution inputs. Recompute a full-list `verify_history` receipt under the W
   verifier's own identity. Supplemented history is the union of those receipts.
7. **Verify.**
   - Compute `c = commitment_value(payload, salt)`.
   - Run `verify_complete_private` with the derived chain, tips, receipts, `resolver` and
     `artifact_reader`. Only the frozen verifier decides PASS.
8. **Build and write W.**
   - Body: `dependencies` exactly P..G and S, so no T, U or C. `commitment` = c.
     `payload` and `salt` are S's PRIVATE refs. `supplement_chain` is the derived chain.
     `active_authority_tip` is the lease tip.
   - `all_position_checks` holds counts only: 1412, contiguous, strict uint64, unique,
     original-K disjoint, supplement disjoint with count, domain.
   - `audit_reproduction` holds counts, audit digest and tip, `entropy_source: "REAL"`,
     full read-back, and historical completeness NOT ESTABLISHED.
   - `evidence` holds PRIVATE refs to the retained verification result and the
     history receipts.
   - Self-check with `verify_W_bytes`, retain the record, write it once to
     `private-verification/<S digest>/W.json`, and record the outcome.

**Outcomes, retention and retry** (D7):

| Outcome | When | Effect |
| --- | --- | --- |
| REFUSED_PRECONDITION | Step 1 fails | No private bytes read and no W. Retry is permitted once the condition changes. Every attempt is recorded. |
| UNAVAILABLE | A retained artifact is missing or unreadable | No W. Retry is permitted only after byte-identical restoration that has been hash-checked against S's refs. |
| INTERRUPTED | An intent exists with no outcome, and no W file exists | Retained. The next attempt proceeds and lists it. A partial W file fails closed. |
| FAILED_VERIFICATION | Bytes are present and hash-correct but do not reproduce: entropy declaration, chain, tail, history, audit, order, K overlap or c | A write-once FAIL outcome with a sanitized reason and no private values. No W. Further attempts for this S are refused. |
| PASS | `verify_complete_private` returns PASS | W is written once. Later attempts are refused. |

- **Recommended consequence of FAILED_VERIFICATION.** This is the §11 row "Seed commitment,
  domain, uniqueness or exclusion failure … entire seed protocol; no execution; no
  discretionary redraw". The lead terminates the study. The result is NOT PRODUCED, and any
  new study follows PG-R10. No frozen label names a W failure, and none is added. The
  terminal event and integrity notice name it under the existing "cancellation"
  disposition.
- **This is why the producer must be qualified before Gate 7.** A defective producer
  discovered after generation would end the study.
- **Continuation.** Holds and continuations before W are in the chain by construction. The
  producer never re-produces W after a later continuation; that is the recorded-only
  remainder of N2.
- **Retention and privacy.** Every record and artifact stays under the private authority
  root, never in the repository. W and the outcome records carry digests and counts only.

The operational sequence, unchanged authority semantics, is:

1. The lead issues `ISSUE(+S)`.
2. The independent verifier runs the producer.
3. The lead reviews W and issues `ISSUE(+W)`.
4. The independent verifier runs the template check (S6).
5. The lead issues U, binding the check receipt.
6. The publisher publishes C.

### 4.2 N1: a typed M3 check (S2)

#### 4.2.1 What decimal matching protects (N1 item 1)

M3's decimal matching exists to catch disclosure of the study's generated values, which
are the 1412 accepted positions and the raw audit candidates. Their decimal forms are
19–20-digit numbers (F4), so a whole-run match is evidence of disclosure.

Decimal matching never applies to the salt, which is protected in hex and base64 forms, or
to private roots. Treatment of K members is decision D2.

#### 4.2.2 Separating protected values from structural integers (N1 item 2)

Every C field is classified by schema type. Only human-authored free text is scanned.
Typed fields are validated by type, equality or recomputation and are not scanned, because
they cannot carry chosen content. An unclassified field fails closed.

| Class | C fields | Validated by |
| --- | --- | --- |
| Constant | All keys. Envelope `schema`, `version`, `digest_convention` and identity prefix. `record_role`, `N`, `claim_profile`, `historical_coverage`, `permanent_limitation`. RecordRef `schema`/`version`. ArtifactRef `visibility`. `actor.role` | Exact frozen values |
| Derived | Envelope `digest` and identity suffix. `commitment`. `dependencies`. `study_id` | Recomputed from the body. c equals W and U, which already checks it. The dependencies equal the bound tuple, W and U. `study_id` equals the authority study, fixed since O and so before generation |
| Typed values | ArtifactRef `sha256_raw` (64-hex) and `bytes` (integer) | Type only. See the residual note below |
| **Free text (scanned)** | `decision`, `actor.actor_id`, `actor.authority_evidence.evidence_id`, every `evidence[].evidence_id`, and envelope `status` if present | M3 forms below |

Forms checked in free text: generated values as 16-hex in any letter case and as whole
decimal runs; K members per D2; the salt as hex in any case and as standard and URL-safe
base64; private roots with either separator. The marker layer stays a whole-record check,
and none of its markers occurs in a constant field.

**Residual, stated plainly.** A deliberately forged typed value, such as a fake digest
embedding a 16-hex seed or an integer `bytes` equal to a seed, is not caught. M3 never
claimed to stop deliberate encodings. Scanning those fields would bring back structural
refusals at about 10^-15 probability per field. That is negligible, but it is not
"cannot", which item 5 requires.

#### 4.2.3 Already-public K members (N1 item 3, decision D2)

Public K members do not need decimal protection on confidentiality grounds. That covers
the E6/E8 revealed lists and the tracked literals. However, the K and E formats carry no
public/private attribute, so the instrument cannot tell public members from members
evidenced only privately. Adding such an attribute would be inventory (W3) scope.

- **Option A (recommended).** All K members keep 16-hex and decimal protection, but only in
  free text. No protection is weakened in any field that can carry chosen content. The cost
  is that approved free text must avoid standalone digit runs equal to K members. That is
  avoidable when combined with the pre-U check (D3). No interpretation ruling is needed.
- **Option B.** K members keep 16-hex protection only. This has no K false positives at
  all. It needs an explicit ruling that "no seeds" in schema C protects study-generated
  values, with K protected in its inventory hex form. Decimal disclosure of a privately
  evidenced K member in free text would not be caught.

Under option A, generated values and K are treated the same in free text, so the change is
confined to the field walk. The `PrivateValues` constructor, `study_private_values` and
the sealed leak tests are unchanged.

#### 4.2.4 Avoidability before U (S6, decision D3, derived)

Because an issued U cannot be replaced (F5), an M3 refusal is avoidable only if it is
caught before U is issued. Proposed check:

- `check_publication_template(authority, proposed_body, *, expected_tip, operation_id)`
  runs read-only under `private_verification`, using the same typed check as publication.
- It returns a private receipt bound to the template digest, with PASS or FAIL and no
  values.
- U binds the PASS receipt in `U.evidence`. Publication requires it (D3 mandatory) and
  still re-runs the check.
- The check is deterministic over unchanged private values, so a template that passes it
  cannot be refused by M3 at publication.

#### 4.2.5 Why structural refusal becomes impossible (N1 item 5)

- Constant, derived and typed fields are never scanned, whatever K or the generated values
  contain.
- The only fields that can trigger refusal are human-authored text, and the pre-U check
  shows any such refusal before U exists.
- The tests in §5.2 demonstrate both points against adversarial inputs built from C's own
  content.

### 4.3 Carried requirements mapped to the design

| Requirement | Where met | Evidence (§5.2) |
| --- | --- | --- |
| N1-1 decide what decimal matching protects | §4.2.1 and D2 | Scope record |
| N1-2 separate protected values from structural integers | §4.2.2 | N1-02, N1-04, N1-09 |
| N1-3 public K members | §4.2.3 and D2 | N1-08 (A) or its absence (B) |
| N1-4 realistic K including 0, 1, 2, 3, 5, 7, 42 | §5.2 | N1-01 |
| N1-5 no unavoidable structural refusal | §4.2.4, §4.2.5 | N1-02, N1-03, N1-04, N1-07 |
| N1-6 genuine disclosure still refused | §4.2.2 | N1-05, N1-06, N1-10 |
| N1-7 in the Gate-8 seal and reproduction | §5.3, §5.4 | Seal 05, evidence 05 |
| N2 complete chain, `active_chain_tip` always | §4.1 step 5 | W-02, W-03, W-04 |
| N6 REAL required | §4.1 step 4 | W-05, W-11, W-12 |

### 4.4 Files expected to change

- New: `tools/research/v6/e9/v2/private_verification.py`.
- Changed: `tools/research/v6/e9/v2/commitment.py`, for the typed field walk, the template
  check and the U receipt requirement.
- New test modules matching `engine/tests/test_v6_e9_v2_*.py`. Indicative names:
  `test_v6_e9_v2_gate8_producer.py`, `test_v6_e9_v2_gate8_publication.py`, and
  independently written `test_v6_e9_v2_independent_gate8_*.py`.
- Everything else is expected to be unchanged. Any harness or reproduction-script change
  would be a recorded qualification-source change.

## 5. Qualification plan

### 5.1 Principles

- Synthetic only, under `qualification_guard` through the existing harness. No
  `os.urandom` or `secrets`, no native matches, no bootstrap analysis. Every attempt is
  recorded and failed attempts are kept.
- **The REAL boundary is neither consumed nor bypassed** (D4). The producer has no
  non-REAL path, and no test patches or weakens its REAL check. PASS-path tests use
  REAL-labelled fixture boundaries. Test code builds these directly, never through
  `Generator`, in the `synthetic-e9-v2-only` namespace, with full-width synthetic values,
  a real `AuthorityLog`, `register_producer` and `mark_first_raw`.
- Synthetic studies built by the injected `Generator` are used only to show that the
  producer refuses them.
- **Limitation.** Synthetic qualification cannot show that a REAL declaration corresponds
  to OS entropy. That rests on the sealed `Generator` REAL branch, which is never executed
  in qualification, together with producer fencing. It is first exercised at Gate 7 and
  confirmed by the operational W.
- Assertions come from frozen rules and independent reference calculations, not from the
  implementation's decision path.

### 5.2 Test inventory (indicative IDs)

**Publication (N1).** These cases use a realistic C with real fixture digests and
full-width accepted values.

| ID | Case | Expected |
| --- | --- | --- |
| N1-01 | K = {0, 1, 2, 3, 5, 7, 42} ∪ {6, 8, 9, 256, 1412} ∪ the complete pinned E6/E8 lists | Pre-U check PASS. Publication PASS, with U consumed once |
| N1-02 | Adversarial K = every decimal run and every 16-hex window in C's constant, derived and typed fields | PASS |
| N1-03 | Sweep: realistic K ∪ {k} for every k in 0..65535 | PASS for every k |
| N1-04 | Generated values whose decimal is 2, 6, 8, 9, 256 or 1412, or whose hex equals a window of a dependency digest | PASS. The same values placed in decision text are refused |
| N1-05 | Each scanned field × each form: generated hex lower/upper, generated decimal, K hex, K decimal (A), salt hex lower/upper, salt base64 standard/URL, root with `/` and `\` | Refused at the pre-U check and at publication. U not consumed |
| N1-06 | Off-by-one look-alikes | PASS |
| N1-07 | Template refused before U, corrected, then published. U issued without a PASS receipt (D3) | Correction publishes. Missing receipt is refused, U not consumed |
| N1-08 | (A) Decision "2 artifacts" with 2 in K | Pre-U FAIL. Reworded text passes |
| N1-09 | Every C field classified. An extra or unexpected field is scanned or fails closed | As stated |
| N1-10 | Marker layer, for example `value_hex` in an evidence id | Refused |

**Producer (S1, N2, N6).** These cases use REAL-labelled fixture studies unless stated
otherwise.

| ID | Case | Expected |
| --- | --- | --- |
| W-01 | No holds. The full sequence ISSUE(+S), W, ISSUE(+W), pre-check, U, C, then `worker_start` | W valid: deps exactly P..G and S, c recomputed, refs equal S, tip equals lease, chain empty, REAL recorded. `verify_W_bytes` PASS. Downstream consumers accept |
| W-02 | Every chain shape: partial CONTINUE, partial RELEASE, both, GENERATED HOLD + completed supplement + CONTINUE, GENERATED RELEASE, and combinations | Derived chain equals the hand-listed gap-free chain. Tips and receipts are correct |
| W-03 | N2 regression: a GENERATED-stage continuation exists; a retained record is deleted or out of order | Always included; deletion fails closed |
| W-04 | Tail event other than a tuple-extending ISSUE | FAILED_VERIFICATION |
| W-05 | Boundary declares SYNTHETIC; declaration absent, duplicate, mixed, or bound to another study, G or operation; producer root or marker absent (D5) | FAILED_VERIFICATION. No W |
| W-06 | Held, terminal, stale, revoked, S not issued, G not consumed, source drift, non-independent or unregistered verifier | REFUSED_PRECONDITION. A spy shows no private read |
| W-07 | Each sealed private-verifier fault reached through the producer | FAILED_VERIFICATION. Later attempts refused |
| W-08 | Missing retained artifact, then byte-identical restoration | UNAVAILABLE, then PASS |
| W-09 | Second PASS attempt; interrupted intent; partial W file | Refused; proceeds; fails closed |
| W-10 | W and outcome records scanned for every private value in every form | Nothing exposed |
| W-11 | Injected `Generator`, 1–2 draws: the boundary evidence layout matches the fixture except for mode | Layout equal. The producer refuses the SYNTHETIC study |
| W-12 | Guard active. Producer module statically has no entropy reference | `os.urandom` never called |
| W-13 | DS-W1/W2/W7 on the produced W | Primitive c. No `dependencies.c`. No U, C or T |

**Regression.** All 19 sealed modules run unchanged (582 tests). New-module runtime is
expected to be small, because the fixtures are hand-built and need no per-draw
re-verification. The full run stays at roughly 32 minutes plus a few minutes.

### 5.3 Implementer runs and seal 05

1. Focused runs through `qualification_run` with attempt records.
2. Full run, then ruff and both mypy runs.
3. Write-once `v2_{implementation,qualification}_manifest_attempt_NN.json`, then
   `*_final_05.json` and `v2_final_manifest_seal_05.json`. These bind the Gate-8 scope
   record, dispositions 01 and 02, and both lead confirmations.
4. Pre- and post-run rehash of every manifested file.

### 5.4 Independent reproduction of seal 05

An independent-context qualifier, not the implementer, reproduces the sealed state and
does not improve it:

1. Scope-record and seal binding.
2. Recomputed instrument identity.
3. Rehash of every manifested file before and after.
4. The full suite through the harness.
5. Ruff, mypy on the engine and mypy on the client.
6. An item-by-item checklist covering N1 items 1–7, N2, N6, and every outcome in §4.1.
7. A read-only reproduction of N1 on the seal-04 sources next to its absence on seal 05.
8. Confirmation that no entropy was used and no match ran.

Findings are recorded without remediation, unless one is a BLOCKER or shows the seal is
invalid. Output: `v2_synthetic_qualification_evidence_05.json`.

## 6. Gate transition

### 6.1 Gate-8 revision accepted (the precondition for considering Gate 7)

1. Write-once lead Gate-8 scope record freezing D1–D9, the scope and the stopping rule.
2. Separate implementation authorization.
3. Implementer harness runs passing, with clean static checks.
4. Write-once manifests and seal 05 with its new instrument identity.
5. Independent reproduction PASS or PASS WITH FINDINGS (§5.4), recorded in evidence 05.
6. Lead disposition of any new findings.
7. An explicit lead acceptance record stating that the Gate-8 revision is accepted.

Even after acceptance, Gate 7 still needs these steps, in order:

1. The Q decision for the seal-05 instrument.
2. T or an explicit NOT_APPLICABLE disposition.
3. O/V.
4. A/R.
5. B.

Each requires its own authorization.

### 6.2 Operational Gate 8 complete (after generation)

1. S recorded by the original producer, and the lead's `ISSUE(+S)`.
2. W produced by the seal-05 producer under `private_verification`. It must have a PASS
   outcome, REAL entropy, the producer root and marker bound, a complete chain with a clean
   tail, and an independent verifier.
3. W and its private result retained, and the lead's `ISSUE(+W)` with no intervening
   non-ISSUE event.
4. Before Gate 9: a PASS from the pre-U template check bound into U.

## 7. Decisions requiring lead approval before implementation

"Derived" means the implementer derived the item from the carried requirements or from the
planning facts. The lead may strike it.

| ID | Decision | Recommendation |
| --- | --- | --- |
| D1 | N1 rule: a typed check of free text only, with typed fields validated and not scanned, including the stated residual for forged typed values | Adopt |
| D2 | K members: A, all forms in free text only; or B, hex only, which needs an interpretation ruling | A |
| D3 (derived) | Pre-U template check: mandatory receipt in U, advisory, or none. Without it, a free-text refusal after U is unrecoverable (F5) | Mandatory |
| D4 | Qualification of the REAL-only producer: Q-A, REAL-labelled hand-built fixtures with no mode switch in code. Q-B, a mode argument plus consumer-side REAL checks. Q-C, refusal paths only, so the PASS path is first run on the real payload | Q-A |
| D5 (derived) | The producer additionally requires the registered producer root and first-raw marker in the boundary evidence, so the REAL declaration is the operational one | Adopt |
| D6 | N2: completeness derived by the producer from the durable log plus the tail check, with `verify_complete_private` unchanged; or also change the sealed verifier | Producer-side only |
| D7 | W outcomes and retry (§4.1), with FAILED_VERIFICATION treated as a §11 seed-commitment failure: lead termination, NOT PRODUCED, PG-R10 | Adopt |
| D8 | Process: independently authored `independent_gate8` modules written from the scope record before seal 05; changes stay uncommitted as for seal 04; the harness is unchanged | Adopt |
| D9 | O-1 (unpadded hex) stays recorded only, as do N3–N5, N7–N9 and the rest of N2 | Record only |

## 8. Freeze material

No protocol amendment, schema change or rule-contract change is proposed. Before any
implementation, the following is needed:

- A write-once lead Gate-8 scope record, for example `v2_gate8_scope_01.json`. It would
  bind disposition 02 and its confirmation, record D1–D9 as ruled, list the in-scope and
  out-of-scope items in §2, state the stopping rule, and name the next step (implementation)
  as separately authorized.
- If D2 option B is chosen, the same record carries the interpretation ruling for schema
  C's "no seeds".
- The record is not created by this planning pass.

Execution LOCKED. Requirement C NOT ESTABLISHED. Q absent. Gate 7 not authorized.
