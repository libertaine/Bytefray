# E9 v2 Gate-8 scope

**Recorded 2026-10-06.** This page summarizes the write-once record
`tools/research/v6/e9/v2_gate8_scope_01.json`, identity `v6-e9-v2-gate8-scope-eae9f407f5d1`.

- Body SHA-256: `eae9f407f5d1776f90d407a1364750491c0dc63ccfe7253a65fc5474916fa922`
- Raw SHA-256: `adf4d9c77fcbc377ff14aa46fd354f3a26e41ba779398728634943b65d045cb2`

If the two ever differ, the JSON record governs.

The record freezes the research lead's Gate-8 rulings (D1–D9) and two clarifications the
lead gave while it was being drafted. It binds 15 inputs by raw digest:

- the adopted protocol and its adoption attestation;
- the rule contract (human and machine) and the record schemas;
- qualification plan 02;
- seal 04, its two final manifests, and evidence 04;
- dispositions 01 and 02, with both lead confirmations;
- the [Gate-8 plan](V6_E9_GATE8_REVISION_PLAN_01.md).

**Gate-8 implementation is not authorized by this record.** It needs a separate explicit
lead authorization.

| Item | Status |
| --- | --- |
| Seal 04 | PASS WITH FINDINGS |
| Independent reproduction | PASS, 582/582 |
| N1 | Mandatory Gate-8 blocker |
| Execution | LOCKED |
| Requirement C | NOT ESTABLISHED |
| Q record | Absent |

Not authorized:

- Gate-8 implementation, or any change to the sealed instrument;
- REAL entropy, generation, W production or salt creation;
- native execution or operational publication;
- Q creation;
- Gate-7 execution or authorization;
- any operational record (T, O, V, A, R, B or later).

## Rulings

| ID | Ruling | Effect |
| --- | --- | --- |
| D1 | ADOPT | M3 checks only an explicit list of C's protected text fields. Typed, structural and derived fields are protected by schema constraints and recomputation. |
| D2 | ADOPT option A | Hex and decimal protection is kept for all K members. N1 is solved by changing *where* matching applies, not *what* is matched. |
| D3 | MANDATORY | The pre-U template check must pass before U is issued, and a failure prevents U. Clarified: the check runs before U only, after W, against all actual private values. |
| D4 | ADOPT, qualification-only | The producer's PASS path may be tested with hand-built fixtures that declare REAL over synthetic bytes, under seven constraints (below). |
| D5 | ADOPT | The producer also requires the registered producer root and the first-raw marker. |
| D6 | ADOPT, producer only | The producer rebuilds the complete chain from the durable log. The sealed verifier is unchanged. |
| D7 | ADOPT, classification preserved | A substantive verification failure on real bytes is terminal. A non-completion is not. Clarified: non-completions are handled by recorded manual retries. |
| D8 | ADOPT | Independently written tests and the seal-04 model: uncommitted changes, explicit manifests, exact-byte seal, reproduction against sealed bytes. |
| D9 | RECORD ONLY | The unpadded-hex observation, N3–N5, N7–N9 and the rest of N2 stay recorded findings. |

**No protocol amendment.** For every authorized change, the record quotes the frozen
clause it implements. Each quote was checked verbatim against the cited file's bytes
before the record was written.

The record also states two pre-existing readings rather than changing them:

- **"No salt in drafting or synthetic qualification"** prohibits real salt, as it has since
  seals 01–04. Gate-8 fixtures use literal test bytes and never call `salt_creation`.
- **The C `decision` field** is described as an "explicit role-specific enum", but no enum
  is frozen for C. It is therefore a protected text field, and no enum is introduced.

## Implementation boundary

**May add:**

- `tools/research/v6/e9/v2/private_verification.py`, containing:
  - the W producer;
  - chain derivation;
  - attempt records;
  - the pre-U template check;
  - publication-authorization issuance.
- `engine/tests/test_v6_e9_v2_gate8_*.py`, written by the implementer.
- `engine/tests/test_v6_e9_v2_independent_gate8_*.py`, written independently from the
  record before seal 05. Fixtures live inside these modules; no new helper module is added.

**May change:** `tools/research/v6/e9/v2/commitment.py`, limited to:

- the C field walk used by M3;
- helpers the pre-U check shares with publication.

The public signatures of `PrivateValues(uint64_hex, salts, paths)`, `study_private_values`,
`validate_publication_template` and `publish_commitment` are kept. These checks keep their
semantics:

- the representation set and the marker layer;
- template equality and the U insertion slot;
- the W binding and the private-evidence check;
- single-use U.

**Must not change:**

- Every other implementation file, including `generation.py`, `authority.py`,
  `integrity.py`, `inventory.py` and `records.py`.
- `verify_complete_private`.
- All 19 seal-04 test modules, and every other seal-04 qualification file: the synthetic
  records helper, `conftest.py`, `pytest.ini`, `pyproject.toml`, the reproduction script,
  the guard and the harness.
- P, the attestation, the rule contract, the schema catalogue, and every seal or
  disposition record.
- The engine, the Agent API, the Ruleset, the replay and result schemas, and all inherited
  pins.

## W producer

`produce_private_verification(authority, *, verifier, expected_tip, operation_id)`
always runs inside the `private_verification` protected operation. It has no entropy
parameter, mode, flag or allow-synthetic branch. It takes no caller-supplied chain, tips,
history, receipts or commitment. It has no command-line entry point and makes no entropy
call.

| Outcome | Meaning | Consequence |
| --- | --- | --- |
| REFUSED_PRECONDITION | Authority, tuple, source or verifier-independence check failed. No private byte was read. | No W. Recorded manual retry. |
| UNAVAILABLE | A retained artifact is missing or unreadable. | No W. Retry only after a hash-checked, byte-identical restoration. |
| INTERRUPTED | An intent exists with no outcome. | No W. Recorded manual retry. A partial W file fails closed. |
| FAILED_VERIFICATION | Verification completed with a substantive failure: entropy declaration, producer root or marker, chain or tail, history, audit, order, K overlap or c. | Write-once FAIL outcome. Later attempts are refused. With real bytes this is a terminal §11 seed-commitment failure: no result, and no other real bytes for the study. |
| PASS | The sealed verifier returned PASS. | W is written once. Later attempts are refused. |

No retry is automatic, every attempt is retained, and no attempt can change the bound
material.

W's dependencies are exactly P..G and S. Its `audit_reproduction` records REAL entropy
and historical completeness NOT ESTABLISHED. W and its outcome records carry only
digests and counts.

## N1: protected text fields of C

The fields scanned are:

- `body.decision`;
- `body.actor.actor_id`;
- `body.actor.authority_evidence.evidence_id`;
- every `body.evidence[*].evidence_id`;
- the envelope `status`, if present.

In those fields, each generated value and each K member is matched as 16 hex digits in any
letter case and as a whole decimal run. The salt is matched as hex in any case and as
standard or URL-safe base64. Private roots are matched with either path separator. The
marker layer still checks the whole record.

Every other field is classified as constant, derived or typed and is not scanned. Any
unclassified field fails closed.

`study_id` counts as derived. It is fixed at O, before any generated value exists. Public K
literals include 2 and 9, so scanning it would make any `v6`/`e9`/`v2`-style identity
unpublishable.

The record also states one residual: a deliberately forged typed value, such as a fake
digest or a `bytes` integer, is not detected.

## Pre-U template check

- **Basis.** After generation, an issued U can be revoked but never replaced.
- **The check.** `check_publication_template` runs read-only, by a registered independent
  verifier, against the actual private values. It produces a private PASS or FAIL receipt
  bound to the template digest.
- **Issuance.** `issue_publication_authorization` appends the lead's ISSUE that adds U only
  if U's evidence binds a PASS receipt for its exact template and a re-run of the check
  passes.
- **What a PASS means.** The known template content is admissible. It does not guarantee
  that every publication check will pass.
- **Residual.** The generic authority append can still issue any lead record, as today. The
  operational procedure uses the dedicated function. Publication does not also demand the
  receipt, so that the sealed publication tests stay unchanged.

## Qualification and seal 05

**D4 fixture constraints:**

- Fixtures exist only in sealed test modules and per-attempt temporary roots.
- Their provenance is recorded as synthetic, outside the frozen-shape declaration.
- They are never operational evidence, never written to the repository or any operational
  or private store, and never accepted by a real-study path.
- The producer has no bypass.
- The injected `Generator` is used only for boundary-layout parity.

The final report must state: "No REAL entropy was consumed." and "REAL was represented
only as an input declaration inside synthetic qualification fixtures."

**Required coverage:**

- N1-01–N1-10, including:
  - the realistic K {0, 1, 2, 3, 5, 7, 42} ∪ {6, 8, 9, 256, 1412} ∪ the complete E6/E8 lists;
  - an adversarial K built from C's own structure;
  - a 0..65535 sweep.
- W-01–W-14. W-14 shows that no incomplete, selective or stale chain can reach the
  verifier.
- All 19 seal-04 modules unchanged, still 582/582.

**Seal 05:**

- The manifest rule is unchanged.
- Manifest attempts are numbered NN, then the final 05 pair and seal 05.
- Seal 05 binds the scope record, dispositions 01 and 02, both confirmations and evidence 04.
- Every manifested file is rehashed before and after each run.
- All runs go through the harness.

**Independent reproduction** is done by an independent-context qualifier against the sealed
bytes:

- an item-by-item checklist;
- N1 reproduced on seal 04 and shown absent on seal 05;
- the same no-REAL-entropy statements;
- findings recorded without remediation.

## Gate ordering and transition

The ordering:

1. The Gate-8 revision is implemented, sealed, independently reproduced and accepted.
2. Gate 7 may then be authorized, but only after the Q decision, T (or NOT_APPLICABLE),
   O/V, A/R and B.
3. The revision must also come before any operational record that binds the instrument or
   its qualification.

Operational Gate 8, after generation, additionally requires:

- a separate lead authorization of W production;
- ISSUE(+S);
- a PASS W from the seal-05 producer;
- ISSUE(+W) with no intervening non-ISSUE event;
- before Gate 9, the pre-U check and issuance of U.

## Stop conditions

- **D6.** Completeness cannot be guaranteed at the producer without changing verifier
  semantics.
- **D9.** The unpadded-hex observation turns out to breach a frozen requirement.
- Any change turns out to need new normative text.
- Any change is needed outside the boundary, including to any seal-04 qualification file.
- A BLOCKER, or evidence that a seal is invalid.

The stopping rule is unchanged: one revision, seal 05 and one independent reproduction.
Later non-blocking findings are recorded, not fixed.
