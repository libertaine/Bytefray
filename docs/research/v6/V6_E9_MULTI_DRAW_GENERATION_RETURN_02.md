# E9 multi-draw generation return (02)

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**STOP BEFORE ENTROPY: Phase A UNAVAILABLE; timing prerequisite NOT VERIFIED.**
Scientific draw calls **0**; salt entropy calls **0**; other authorized entropy
calls **0**; total REAL invocations **0**; attempted invocations **0**.
G remains consumed once at original T2. Marker, transcript, salt, package and W
remain absent. Requirement C remains **NOT ESTABLISHED**.

## A. Disposition 09

[Disposition 09](../../../tools/research/v6/e9/v2_finding_disposition_09.json),
with its [readable mirror](V6_E9_V2_FINDING_DISPOSITION_09.md), records the lead's
conditional withdrawal of the blanket salt prohibition and unchanged mandatory
timing/integrity/recovery requirements. Disposition 08 remains valid.
The administrative identity is schema `bytefray.v6.e9.v2_finding_disposition`,
version 2, sequence 9, exact file path and raw bytes. No operational authority
record/event or new catalogue identity is invented.

| Evidence | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| Disposition 09 JSON | 6249 | `53261258982fb2c962f0176cda7a0368ed87c50a03ab8b9e7c472c675e2764b5` |
| Exact retained lead ruling | 12977 | `f9a380367e995ec27e3deb73ae67b45b0af3883ae4a8944d83db004e71674b46` |
| Entropy-blocked baseline procedure | 11958 | `a82ac815541f97296a1a3b89f8f4982202c04bc3976ff22c3977abbbd1d9f0a4` |
| Baseline verification | 322342 | `326ffda4e0375c4872c1cfb7cdc9b122f0b9912c6fa474e1dd6239f8a28bf6b5` |

The salt ruling authorizes only the frozen single 32-byte generation salt,
conditionally; it supplies no timing waiver and no authority for W/U/C/native
execution. The prior prohibition prevented completion. Both earlier generation
returns and all previous dispositions remain unchanged.

## B. Exact frozen timing requirement and creation windows

Original G is `v6-e9-generation-authorization-v2-0ea6d2043fbd`, body digest `0ea6d2043fbd7619ea724da15b6a4e106ffeaa3c929b43b9bcb3ff354c668175`,
raw SHA-256 `21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8`.
Its unchanged `body.boundary_procedure` requires:

> Independently verifiable trustworthy pre-first-raw-draw instant evidence is mandatory; absent or ambiguous temporal/ordering evidence prevents the first draw and requires lead disposition.

The adopted rule text PG-R4 (line 102) requires the durably recorded instant
immediately before the first experimental raw draw, after the inventory gate is
sealed and verified. PG-R3 (line 100) requires independent complete pre-generation
verification and separate authorization before that draw. The adopted catalogue's
`GenerationBoundary.required_body_fields.durable_instant` is exactly
`trustworthy pre-first-raw-draw evidence`; its acceptance predicate requires durable
write and verified inventory/authority before first raw and treats uncertain
ordering as a hold. The original G additionally orders marker, REAL source
declaration, boundary/current tip/fence and first intent before `os.urandom(8)`.

| Evidence window | Requirement and current disposition |
| --- | --- |
| Before G issuance | Complete independent B and declared future G boundary procedure. Closed; original B/ISSUE retained. No reviewed clause requires the future boundary instant to have occurred here. |
| Before G CONSUME | Original registered producer and exact single durable CONSUME. Closed; original evidence retained. No reviewed clause places the future boundary instant in this window. |
| After CONSUME, before first raw | Trustworthy independently verifiable timing/ordering evidence must exist and pass review before marker creation/entropy. Window remains open because no marker/raw exists; prerequisite UNAVAILABLE. |
| Contemporaneously immediately before first raw | Frozen protected action durably records marker/source/boundary carrying trustworthy instant and intent, in order, before source(8). Not entered. |

CONSUME alone does **not** establish a closed first-raw timing window or make the
future instant historical. Actual fulfillment at T2 is **not established**.
No retroactive attestation, replacement G, B alteration or authority-history
rewrite was attempted. No marker was precreated to manufacture an event.

The reviewed frozen inputs state semantic trust and independence requirements.
They do **not** prescribe a clock/provider, source identity, signed evidence
format, time accuracy, synchronization/freshness rule, trust root, independent
observation channel or concrete acquisition/verification procedure. Hashes and
canonical serialization can bind evidence but cannot supply its temporal authority.

## C. Timing evidence and independent verification

**Qualifying timing evidence: ABSENT. Independent timing verification: UNAVAILABLE.**
No event has been attested. Qualifying evidence identity, source identity, exact
bytes/hash, observation time, collection time and external verification material
are absent. Administrative retention timestamps below are not boundary times.

A neutral fresh-context commission `/root/timing_verifier` independently read the
exact frozen inputs and existing private provenance. It evaluated the authority
of the available evidence to establish timing, beyond schema structure. Its
conclusion is retained verbatim privately; its exact review and the root's separate
analysis have these raw identities:

| Administrative review | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| Independent timing review | 14772 | `f51ec6c81e8bd511f1306895e956da966b19d3a43a9eb28eb827a62e80542800` |
| Requirement/window/provenance analysis | 10510 | `d823d82ff430948031e4dede504cd0196cdca49b320f78d9ca2ba5636dcdc721` |

These review artifacts bind P-through-G, original CONSUME, producer and T2, and
preserve exact source hashes/clauses. They are evidence of this assessment,
not external evidence of a first-raw instant. Separate AI context supplies process
separation from production of reviewed evidence; it is the same model family and
tool environment, supplies no trusted clock, and is not an appointed operational
Actor or W. No qualifying timing receipt or PASS was fabricated.

Exact tooling limitation: `Generator.draw_one` (`generation.py:164–185`) accepts
caller-supplied `durable_instant`, inserts it into the boundary and serializes it.
`records._field` (`records.py:366–372`) falls through to generic JSON validation
for that field. Neither acquires time nor authenticates a timing source or proves
independent observation/ordering. No qualifying existing external attestation or
verification material was found. Inventing a local timestamp, clock wrapper or
ad hoc external service would not establish the prescribed accepted path.

Phase A is **UNAVAILABLE**, not PASS and not a claim that valid evidence was tested
and failed. Retain all administrative evidence; no entropy follows. The mandatory
stop applies because trustworthy timing and its exact supported method cannot be
established with the reviewed frozen tooling/evidence. No new timing proof is
created, no scientific prefix abandoned and no formal hold/cancellation invented.

## D. Frozen 32-byte salt requirement

Draft 3 line 512 requires a separate 32-byte CSPRNG salt for the seed commitment.
The v2 domain in `commitment.py:31–38` binds exactly
`SHA256(b"bytefray-e9-seed-commitment-v2\n" + salt_raw + payload_raw)`.
The salt hides/binds the private payload and is also required for frozen package
completion; no commitment or operational W is produced here.

The source/order are exact in `generation.py:242–315`: complete accepted prefix
of **N=1412** first; exclusive protected `salt_creation`; durable/read-back
`salt.intent.json`; **one** REAL `os.urandom(32)` invocation; validate bytes/length;
exclusive flushed/fsynced/read-back `salt.bin`; then sealed audit/payload; then S
receipt and authority-retained original copies. Raw salt is 32 binary bytes;
its identity uses SHA-256 and length in PRIVATE `COMPLETE-SALT` ArtifactRef.
No salt hex value or private path map is disclosed here.

A prior salt intent or salt file makes `complete` refuse a new attempt. Existing
salt bytes may never be regenerated. Write-once materialization can block recovery;
no new random input, deletion, overwrite or convenience restart follows a failure.
This prospective source review does not authorize Phase B/C absent Phase A PASS.
**Actual salt: absent; identity/hash/durability: not applicable because uncreated.**

## E. Baseline, bindings and authority

| Check | Fresh result |
| --- | --- |
| Branch / HEAD / upstream / live remote | v6-research / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` / origin/v6-research; equal, ahead/behind 0/0 |
| Tracked tree and index | Empty diffs |
| Seal 08 | **329/329 unchanged** (293 implementation, 36 qualification) |
| Preservation | **1607/1607 unchanged** |
| Inherited private evidence | **1362/1362 unchanged**; plus all five prior-cycle administrative files, **1367/1367** exact entry census |
| P/I/Q/O/V/A/R/B/G | Exact canonical original records, raw/body hashes and dependencies verified |
| ArtifactRefs | 2420 occurrences / 1874 distinct evidence-ID/content bindings freshly hashed |
| B materialized manifest | 4392 rows; 4391 live matches; sole historical authority-marker row exactly reproduces B-certified T0 |
| CONSUME | `v6-e9-authority-event-v2-765e7f4471ab`; one CONSUME, sequence 3, exact original bytes |
| Registered producer | Original `v6-e9-producer-01`, recorder Actor, exact registry and root; root empty |
| Authority | T2 `765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485`; epoch 0, sequence 3, active original tuple, unheld/unrevoked/nonterminal |
| Adoption / contract / Draft 3 | Exact original pins and review verified |

The inherited B-marker transition remains the accepted historical T0→ISSUE→T1→
CONSUME→T2 invariant. B and G were not rewritten. Existing historical limitations,
357 gaps, DEP-01–DEP-05 and unknown H remain unchanged.

## F. First-raw state

**Marker ABSENT; retained marker copy ABSENT; GenerationBoundary ABSENT.**
Phase A has not passed. Frozen `draw_one` has no supported pause between marker
and first draw, so it was neither constructed nor entered. No orphan marker or
invented boundary identity exists.

## G. Ordered raw transcript

**ABSENT; completed scientific prefix length 0; accepted positions 0.**
No raw bytes/draw ordinal/transcript digest exists. K rejections, duplicate
rejections and other algorithmic discards are all zero. All prior private inputs
remain retained without exposing scientific values or reverse path maps.

## H. Entropy-call accounting

| Invocation class | REAL calls | Attempted calls |
| --- | ---: | ---: |
| Scientific raw draws | 0 | 0 |
| Frozen generation salt | 0 | 0 |
| Other frozen authorized entropy | 0 | 0 |
| **Total** | **0** | **0** |

`os.urandom` and `os.getrandom` were blocked/counting before repository imports in
the root audit/recorder. No generator or protected generation action was entered.
Accounting covers research entropy APIs, excluding interpreter/OS internal entropy.
Prospective full generation uses D scientific eight-byte invocations, where
D=1412+K rejections+duplicate rejections, plus one 32-byte salt invocation.
No unexplained scientific invocation occurred.

## I. Generated package

**ABSENT; generated scientific files 0; package identity/hash/bindings absent.**
Prospective frozen producer output is `boundary.json`, D intent/audit pairs,
`salt.intent.json`, `salt.bin`, `audit.json`, `payload.json`, `receipt.json`:
2D+6 files, minimum 2830, plus prescribed authority-retained copies. Every raw
candidate remains in ordered provenance. This is expected format, not actual
output. No extraneous scientific output or fabricated S/package identity exists.

## J. Recovery history

No scientific generation, entropy interruption, retry or continuation occurred.
The restricted interpreter and remote lookup were unavailable; scoped elevated
baseline checks succeeded. Those environment failures consumed no scientific
entropy and altered no original evidence. Administrative review was retained
with unavailable timing outcome; absence is never promoted to PASS.

For any later authorized procedure, a possibly returned but unrecoverable raw
value requires STOP without redraw. A durable exact prefix permits only the next
legitimate ordinal after complete frozen `read_audit` verification and applicable
recovery authority. Boundary/intents/audits must remain intact; mismatch, orphan
state or ambiguity blocks continuation. A retained salt must never be regenerated;
materialization recovery uses original bytes only where the frozen path permits.
No source workaround or new authority event was created in this continuation.

## K. Verification and Phase B/C status

Phase A requirement/provenance review completed, with **UNAVAILABLE** timing.
Phase B final checks and Phase C generation are **NOT ENTERED**. Static review
confirms normal per-draw write/flush/file-fsync/read-back and full `read_audit`
reconstruction before the next draw; it does not claim a new power-loss guarantee,
parent-directory fsync or atomic multi-file transaction. No instrument patch was
made. Any ambiguous entropy-return/durability interval must retain state and stop.

No generated package exists for deterministic replay or frozen output verification.
No reproduction entropy, injected REAL stream, new algorithm, tests/lint/mypy or
new instrument qualification was executed or claimed.

## L. Next gate and W readiness

**Next prerequisite: establish a qualifying trustworthy boundary timing source,
provenance/trust verification and valid evidence procedure under the frozen
requirements, while preserving original consumed G/T2 and the open first-raw
window. No supported method has been established here.** A new scope/tooling
change is not authorized; no replacement G or historical attestation is proposed.

Only Phase A PASS would authorize final Phase B checks and then frozen Phase C.
Operational W remains **not ready and prohibited by this task**. Its frozen
prerequisites are completed S, exact private payload/salt/audit/boundary, original
K/E/L and source/materialization evidence, complete current authority/supplement
history and independent verifier authorization. W recomputes full count/domain/
order/uniqueness/K membership/audit and commitment c, using retained bytes only;
it excludes future U/C. No W/W PASS, U, C, extra salt, native match, payoff,
collection/statistical analysis or study-result publication was produced.
Generation completion, even if later achieved, would not establish Requirement C.

## M. Integrity and Git state

Fresh entry and final read-back verify Seal **329/329**, preservation **1607/1607**,
inherited private evidence **1362/1362**, all **1367** prior private files and every
prior public record/return unchanged, exact original registry and T2 authority
chain unchanged. Prior dispositions and both generation-return documents are
preserved byte-for-byte. No source/test/schema/sealed-manifest/instrument changes.

New public files are only Disposition 09 JSON, its Markdown mirror and this return.
New private additions are explicitly accounted administrative receipts under the
existing ignored study root: baseline procedure, exact lead request, baseline
verification, recording procedure, independent review, timing analysis and final
integrity verification. They contain no new scientific input or authority event.
Tracked working-tree/index remain clean; inherited untracked work and local-only
settings are untouched. No staging, commit, push or study publication occurred.

| Final state | Result |
| --- | --- |
| Gate 8 / Q / O | ESTABLISHED |
| V / A / R / B | PASS / APPROVED / ACCEPTED / PASS–ESTABLISHED |
| Gate 7 / G / producer | ESTABLISHED / CONSUMED exactly once / REGISTERED |
| Authority / timing prerequisite | Original T2 / UNAVAILABLE, NOT VERIFIED |
| REAL calls / first-raw marker / transcript | 0 / ABSENT / ABSENT |
| Salt / generated package / W | ABSENT / ABSENT / ABSENT |
| Native execution / Requirement C | NOT STARTED / NOT ESTABLISHED |
