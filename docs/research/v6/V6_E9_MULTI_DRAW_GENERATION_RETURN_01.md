# E9 multi-draw generation return (01)

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**STOP BEFORE ENTROPY. Exact REAL entropy invocations: 0; attempted: 0.**
The single-value assumption is superseded by Disposition 08. Two prerequisites
remain unresolved: salt scope for the frozen complete package, and independently
verifiable trustworthy pre-first-draw timing/ordering evidence required by G.
No marker, draw transcript, generated package, W or salt was created.

## A. Disposition 08

Created exclusive, flushed/fsynced/read-back
[Disposition 08](../../../tools/research/v6/e9/v2_finding_disposition_08.json)
and its [readable mirror](V6_E9_V2_FINDING_DISPOSITION_08.md).
G was already consumed once; authority remained T2; first raw had not begun;
REAL calls were zero. The lead's earlier deterministic-from-one-value expectation
was a lead-model/procedure mismatch, not a demonstrated instrument failure.
The accepted model is complete ordered raw transcript plus frozen state/procedure.
All prior records and the [previous return](V6_E9_FIRST_RAW_GENERATION_RETURN_01.md)
remain byte-identical. No new seal or source/test change was made.

## B. Baseline

Fresh audit blocked os.urandom and os.getrandom before repository imports.
No Generator was imported or constructed and no protected action was entered.

| Check | Verified result |
| --- | --- |
| Branch / HEAD | v6-research / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Upstream / live remote | origin/v6-research; exact HEAD, ahead/behind 0/0 |
| Tracked tree / index | Empty diffs |
| Seal 08 / preservation | 329/329 / 1607/1607 unchanged |
| Inherited private evidence | 1362/1362 exact files; no unexplained addition or mutation |
| P/I/Q/O/V/A/R/B/G | Canonical records, exact original raw/body hashes, RecordRefs and dependencies verified |
| Bound ArtifactRefs | 2420 occurrences / 1874 distinct evidence-ID/content bindings rehashed |
| B manifest | 4392 rows; 4391 current matches; sole historical marker reproduces exact B-certified T0 |
| CONSUME | Exact original event; sequence 3; exactly one CONSUME |
| Producer | Original Actor/root/registry verified; producer root empty |
| Authority | Original active tuple at T2; epoch 0, sequence 3, unheld/unrevoked/nonterminal |
| Adopted contract | P, Draft 3, contract pins and adoption review verified |

The B-marker difference is the previously accepted historical authority transition.
No B or G evidence was rewritten. The audit preserves the existing historical
limitations, 357 gaps, DEP-01–DEP-05 and unknown-H disposition.

## C. Frozen multi-draw procedure

Normative inputs are adopted P, G, original O-bound K/E/L, the PG rule contract,
Draft 3, and the exact Seal-08 generation/authority implementation.

| Element | Exact sealed procedure |
| --- | --- |
| Source | REAL mode uses os.urandom; injected streams are prohibited |
| Raw unit | One os.urandom(8) call, exactly eight bytes; unsigned big-endian uint64, lossless 16 lowercase hex characters |
| Request trigger | Caller enters draw_one; protected raw_draw checks original consumed G, operation, source pins, active tuple and registered producer under exclusive authority lock |
| Stopping rule | read_audit reconstructs accepted prefix; draw_one refuses further draws when accepted count reaches N=1412 or salt exists |
| Count | Data-dependent D=1412+K rejections+duplicate rejections |
| Raw order | Monotonic one-based ordinal, eight-digit filenames; distinct one-based accepted position; rejects have null accepted position |
| Rejection | REJECT_K first, otherwise REJECT_DUPLICATE against accepted prefix, otherwise ACCEPT; every candidate remains in audit |
| State | Original K/bindings/producer/operation, canonical boundary, all intents and audit envelopes; accepted order and audit tip reconstruct from retained prefix |
| Durability | Exclusive create, write, flush, file fsync, exact readback; complete chain reread after each audit before draw_one returns |
| Completion | complete obtains separate 32-byte salt, then seals audit/payload and records S; seal_payload and generation_receipt require exact 32-byte salt |

The completion requirement conflicts with the explicit current instruction
"Do not create ... salt" and completion integrity requirement "no salt exists".
The ruling supersedes only the former single-value assumption. It does not
supersede this salt prohibition. No salt-free complete-package path is sealed.
Stopping at 1412 accepted values would leave a partial package and would not
establish S. Bypassing the salt checks would require prohibited source behavior.
This is a remaining scope conflict, not a newly demonstrated instrument defect.

G.boundary_procedure separately requires independently verifiable trustworthy
pre-first-raw instant evidence and expressly prevents the first draw if absent
or ambiguous. No qualifying evidence has been established in this continuation;
a local wall-clock timestamp or document-creation timestamp alone is not claimed
to satisfy it. Neither prerequisite was bypassed to create a partial study input.

## D. First-raw-marker result

**ABSENT.** Frozen draw_one first durably writes/verifies FIRST_RAW_BOUNDARY_V2
binding study, exact G RecordRef and original producer-registry ArtifactRef;
it retains the marker and REAL declaration, writes/verifies GenerationBoundary,
and writes/verifies ordinal-1 intent before the first entropy call.
The marker is inside the protected action; no supported pause exists between
marker creation and first draw. It was not precreated as an orphan placeholder.

## E. Ordered raw-transcript identity

**ABSENT. No raw bytes, ordinal, raw digest or scientific transcript identity exists.**
Frozen per-draw files are draw-<ordinal>.intent.json and draw-<ordinal>.audit.json.
The audit envelope contains entry and SHA-256 of canonical entry bytes. Entry
contains raw_draw_ordinal, raw_bytes_hex, disposition, accepted_position,
authority_tip and prior_entry_digest. The chain starts at the boundary digest.
Boundary dependencies, producer/source evidence and intent operation bind study,
G/CONSUME/operation and generator state transitively. File byte lengths and
raw hashes are obtainable from exact retained bytes; the lossless raw field is
always eight bytes represented as sixteen hex digits. No protected value or
private evidence path map is disclosed in this return or placed into Git.

Administrative evidence is retained privately: exact lead request (13,557 bytes,
SHA-256 `287e0c3c62746df1a3e632bf781488527febb32b1a57a01c4014763af6b7b6ad`),
guarded audit procedure (SHA-256
`c8b1396a512f80d2d5ea19a3eb8fe994de06100ce7cac98e0c301fe00d711f25`),
and baseline verification (SHA-256
`1f703035c2b3c8e22877fa1b96eb33c012287229730926af49366ce29a904521`).
These are administrative receipts, not scientific-input identities.

## F. Exact entropy-call count

**REAL invocations: 0. Attempted invocations: 0. Frozen-algorithm draws consumed: 0.**
No unexpected scientific source invocation occurred. Entropy guards fail closed
and count attempted calls; all audit and recording operations left that count zero.
This accounting concerns scientific API calls, not interpreter/OS internal entropy.

Prospective accepted-list count D is data-dependent, not a predetermined 1412
invocations. Frozen full completion requests D+1 calls: D of eight bytes and one
of 32 bytes. That describes sealed behavior and does not authorize prohibited salt.

## G. Rejection/discard accounting

Actual K rejections: **0**. Duplicate rejections: **0**. Algorithmic discards: **0**.
Prospectively every REJECT_K/REJECT_DUPLICATE remains in the permanent transcript;
rejection permits the next ordinal only under the unchanged frozen rule. No draw
may be replaced, erased, repeated, cherry-picked or used to select another package.

## H. Prefix/durability verification

No scientific prefix exists. Producer-root emptiness, absent first-raw marker and
retained marker copy, and full original-private-file equality were verified.
The frozen mechanism can reconstruct a durably captured prefix: read_audit verifies
intent/audit counts, consecutive filenames/ordinals, canonical-entry digest chain,
operation/tip relationships, original-K/duplicate decisions and accepted positions.
Subsequent draw_one rereads this state before assigning the next ordinal.

A successful draw retains and rereads its audit before the next call. Generator
state need not be guessed or held only in memory. The sealed helper contains no
separate parent-directory fsync; no added power-loss guarantee is claimed. A crash
between entropy return and durable audit leaves an ambiguous input and requires
STOP without redraw. Sequential marker/boundary/intent writes are not an atomic
multi-file transaction. These are existing failure boundaries, not repaired here.

## I. Generated package identity and counts

**ABSENT. Generated scientific artifacts: 0; accepted positions: 0.**
Expected full output is boundary.json, D intents, D audits, salt.intent.json,
salt.bin, audit.json, payload.json and receipt.json: 2D+6 producer files, minimum
2830, plus authority-retained copies. Payload binds N/domain, operation, ordered
positions, original K/E/L, boundary and preceding tip. S binds accepted/rejection
counts, exact audit/payload/salt ArtifactRefs, boundary, operation and completion
authority tip. No identity/count for an uncreated package is fabricated.

## J. Replay/verification result

**Not performed: no raw transcript or package exists.**
Frozen read_audit replays acceptance/rejection, ordered positions and audit chain
from exact retained raw records, with no fresh entropy. It does not derive future
independent candidates from draw 1. No replay capability, injected REAL stream,
alternative algorithm or experimental analysis was added.

## K. Authority state

T2 remains exactly
`765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485`.
The chain has three events and exactly one original CONSUME for this G/operation.
No second G, ISSUE, CONSUME, HOLD, release or continuation event was created.
Protected raw_draw/salt_creation/payload_seal do not append authority events;
commitment publication has a separate U-consumption path. No T3 is invented.
Disposition 08 is an administrative lead-model correction, not an authority event.

## L. Interruptions/recovery

No scientific procedure began and no scientific interruption occurred. Restricted
Python launch and remote lookup were unavailable; scoped elevated audit/lookup
succeeded without entering generation. No failed entropy attempt was retried.

| State | Required handling under retained frozen procedure |
| --- | --- |
| Definitely no pending entropy call | Retry only after resolving scope/timing and freshly verifying original operation; never consume G again |
| Entropy possibly called, exact value unavailable | STOP; retain intent/evidence; no redraw |
| Raw audit durable, later processing interrupted | Permanent draw; read_audit must prove exact complete retained prefix before any next ordinal |
| Several durable draws | Retain all; continue only next legitimate ordinal after full prefix validation |
| Orphan marker/boundary or intent/audit mismatch | Preserve everything; fail closed; no convenient shorter prefix or repair |
| Salt/output interrupted | Preserve all; complete rejects prior salt attempts; write-once materialization may block retry; no fresh entropy or automatic overwrite |
| Receipt/state/output conflict | STOP; do not select a plausible version |

Formal integrity adjudication/PG-R7/PG-R8 gates remain distinct. This pre-entropy
scope stop does not fabricate an operational hold or cancellation.

## M. Integrity

Fresh baseline and final verification establish Seal 08 329/329, preservation
1607/1607, original P-through-G/CONSUME/producer/authority bytes and all 1362 inherited
private files unchanged. Only the three requested public administrative records
and separately accounted private administrative evidence were added. No source,
test, schema or seal bytes changed. No W, salt, U, C, native study match, payoff
result or publication was created. No tests/lint/mypy or new qualification were
run or claimed for this documentary continuation. No commit or push occurred.

## N. Next gate

**Resolve the complete-package salt scope and establish G-compliant independently
verifiable trustworthy first-boundary instant/ordering evidence before first raw.**
The requested multi-draw model is now accepted and recorded; it is no longer a
blocker. If the frozen package is authorized later, its required salt must be
explicitly reconciled with the current prohibition. If salt must remain absent,
full frozen-package completion cannot be achieved under this instrument; no
source change or alternate package is authorized by this task.

| State | Result |
| --- | --- |
| Gate 8 / Q / O | ESTABLISHED |
| V / A / R / B | PASS / APPROVED / ACCEPTED / PASS–ESTABLISHED |
| Gate 7 / G / producer | ESTABLISHED / CONSUMED exactly once / REGISTERED |
| Authority | Original T2 |
| First-raw marker / transcript / package | ABSENT / ABSENT / ABSENT |
| REAL entropy calls / W / salt | 0 / ABSENT / ABSENT |
| Native execution | NOT STARTED |
| Requirement C | NOT ESTABLISHED |

## O. Git status

Tracked working tree and index remain clean on the original branch/HEAD; inherited
untracked files/directories are preserved. New public additions are only this
return, the Disposition 08 JSON and its Markdown mirror. New private evidence
remains under the approved ignored study root. No staging, commit, push or
publication occurred; local-only settings were untouched.
