# E9 first-raw and generation return (01)

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**STOP BEFORE ENTROPY: frozen procedure and requested derivation differ. REAL
entropy calls: 0. First-raw marker, raw input and generation package: ABSENT.**
G remains consumed exactly once; the original producer remains registered;
authority remains T2. Requirement C remains **NOT ESTABLISHED**.

The current request authorizes first raw and generation but also requires
generation to be deterministic from the retained first raw input and frozen
inputs. The accepted G and sealed instrument instead prescribe successive
independent OS-CSPRNG candidates until 1,412 unique values are accepted. The
first eight-byte value cannot determine those later independent values.
There is no sealed expansion function from that first value. Satisfying the
requested derivation would require changing the frozen scientific procedure
and implementation. The request expressly makes required source changes and
recipe ambiguity mandatory stop conditions. Consequently no first-raw action
was entered, and no partial scientific start was made while seeking disposition.

## A. Baseline

The following results were freshly verified with entropy sources blocked.

| Check | Result |
| --- | --- |
| Branch / HEAD | `v6-research` / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Upstream / live remote | `origin/v6-research`; live `git ls-remote` matches HEAD; ahead/behind 0/0 |
| Tracked tree / index | Empty diffs |
| Seal 08 | **329/329 unchanged**, including exact manifest pins |
| Preservation | **1607/1607 unchanged** |
| P/I/Q/O/V/A/R/B/G | Exact original RecordRefs, canonical records, raw/body hashes and dependencies verified |
| Adopted rules / Draft 3 | Exact adopted contract pins, original Draft 3 pin and adoption review verified |
| Original private evidence | **1357/1357 files byte-identical** to the completed G-consumption accounting |
| B input manifest | 4392 rows; 4391 current matches; the sole historical authority-marker row reproduces exact B-certified T0 |
| Bound ArtifactRefs | 2420 occurrences / 1874 distinct evidence-ID/content bindings resolved and rehashed |
| CONSUME | Exactly one valid original event, sequence 3, binding original G, recorder and producer registry |
| Producer | Original Actor/root/registry verifies; root contains zero entries |
| Authority | Exact T2, sequence 3, epoch 0; original tuple active, unheld, unrevoked, nonterminal |
| First raw | Marker and retained marker copy absent; no boundary, intent, audit or raw value |
| Downstream | No generated output, W, salt, native execution or publication in the accounted study state |

The B historical-marker difference is the previously accepted authority
transition, not frozen-input drift. No B or G bytes were rewritten.

## B. Frozen first-raw procedure

Normative inputs are adopted
[P](../../../tools/research/v6/e9/protocol_freeze_v2_adopted_02.json), its pinned
[PG rules](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md), inherited
[Draft 3](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md), exact
[G](../../../tools/research/v6/e9/v2_generation_authorization_study_01.json)
and the qualified sources
[generation.py](../../../tools/research/v6/e9/v2/generation.py) and
[authority.py](../../../tools/research/v6/e9/v2/authority.py).

The pre-execution checklist was reconstructed and retained privately. It is
**blocked at the procedure/scope agreement check**, before any marker or entropy:

1. Verify baseline, exact original tuple/K/E/L, consumed operation and original
   producer; never call `consume_generation` again.
2. Resolve the task's first-input deterministic-derivation requirement against
   G's successive independent draws. This check failed; all following items
   describe the frozen procedure and were not executed.
3. Establish independently verifiable trustworthy pre-first-draw instant and
   ordering evidence required by G/PG-R4. A locally generated timestamp alone
   is not asserted here to satisfy that requirement.
4. Enter unchanged `Generator.draw_one` with exact current tip and required
   durable-instant metadata. Its exclusive `raw_draw` action rechecks sources,
   bindings, operation, consumed G and producer under the authority lock.
5. Within that action, create/read back the deterministic first-raw marker;
   retain its canonical bytes and the REAL entropy declaration; create/read
   back canonical `GenerationBoundary` with original dependencies, recorder,
   producer evidence, current tip, instant and fence epoch; validate boundary.
6. Create/read back ordinal-1 intent containing operation, authority tip and
   prior audit tip. Only then invoke exactly `os.urandom(8)`.
7. Require `bytes` of length eight; interpret unsigned big-endian and encode
   sixteen lowercase hexadecimal digits. Apply original-K/duplicate rejection
   and retain the canonical audit envelope, then reread/verify its chain.
8. Continue only as the resolved authorized frozen scope permits. The existing
   instrument requests fresh eight-byte candidates, not expansion of draw 1.
   Later complete-package sealing also requires its separately identified salt.

The marker precedes entropy, inside the first protected action. The action
does not expose a supported pause after marker creation. Sequential durable
writes are not an atomic multi-file transaction; precreating an orphan marker
would make the frozen first-draw routine fail closed.

## C. Entropy-source authorization/procedure

The current lead request explicitly authorizes REAL entropy. Frozen REAL mode
accepts no injected stream and selects **`os.urandom`**. Each candidate is one
API invocation requesting **8 bytes**, constituting one raw draw. No batching,
splitting, alternate PRNG or model-selected value is prescribed.

G's `sampling` and inherited Draft 3 require fresh uint64 candidates, rejecting
original-K equality and previously accepted duplicates, until N=1412 unique
accepted positions exist. This conflicts with the requested deterministic
derivation from the first retained value. No alternative was implemented.

## D. First-raw marker

**ABSENT; not created.** Its frozen canonical object is
`FIRST_RAW_BOUNDARY_V2`, binding study ID, exact G RecordRef and original
producer-registry ArtifactRef. Canonical UTF-8 JSON plus LF is written at
`authority/first-raw/<G body digest>.json` and retained under the authority
evidence store. No placeholder/raw bytes belong in that marker.

The audit computes its prospective deterministic SHA-256 only to verify the
retained copy is absent. This is an absence check, not an established marker
or scientific raw identity.

## E. Raw evidence identity and durability

**No raw value was obtained; no raw identity, length or digest is established.**

The frozen raw representation is the lossless sixteen-character hex field
`raw_bytes_hex` in each private `draw-<ordinal>.audit.json`. The audit-entry
identity is SHA-256 of canonical entry bytes; its envelope includes that digest
and is written as canonical JSON plus LF. The entry binds ordinal, disposition,
accepted position, current authority tip and prior-entry digest. The chain
starts at the GenerationBoundary body digest, whose evidence binds marker,
registered producer, REAL source and the P-through-G tuple.

`durable_bytes` uses exclusive creation, write, flush, file `os.fsync`, and exact
readback. The sealed helper contains no separate parent-directory fsync; none
was added or claimed. Raw capture becomes retained evidence through the audit
write after validation/representation/rejection calculation. An interruption
between source return and durable audit therefore remains an ambiguous draw;
the intent cannot prove its unknown value or justify a redraw.

## F. Entropy call count

**Actual REAL source invocations: 0. Attempted source invocations: 0.**

The first frozen draw would make one `os.urandom(8)` invocation. For accepted
list completion, let D be the number of candidate draws: D=1412 plus K and
duplicate rejections. D is data-dependent and cannot be fixed exactly before
execution. Full frozen `Generator.complete` adds one `os.urandom(32)` salt
invocation, giving D+1 calls, minimum 1413. This count describes existing
code; it grants no salt or draw authorization beyond the current request.
An unexpected call outside the prescribed sequence requires a stop.

The guard blocked `os.urandom` and `os.getrandom` where available before
repository imports. No Generator was imported/constructed, no protected action
was invoked, and no entropy probe was made. The count concerns scientific
source invocations in this task, not unobserved interpreter/OS internals.

## G. Generation procedure

No generation executed. The frozen functions are `draw_one`, `read_audit`,
`complete`, `seal_payload` and `generation_receipt` in exact Seal-08 instrument
I `v6-e9-instrument-v2-3c692f23d2d9`, bound to P
`v6-e9-prereg-v2-539a60806eab` and original G
`v6-e9-generation-authorization-v2-0ea6d2043fbd`.

Original O-bound K/E/L and every P/I/Q/O/V/A/R/B/G input are unchanged. Candidate
rejection and accepted ordering reproduce deterministically **from the complete
retained raw-draw sequence**. They do not generate that sequence from the first
value. REAL mode deliberately prohibits synthetic injected-stream substitution.

Frozen full-package sealing requires a separate 32-byte CSPRNG salt: `complete`
creates it before payload/S; `seal_payload` and `generation_receipt` require it.
Draft 3 defines this as commitment salt. The task's exception for salt explicitly
defined in the scientific package and its prohibition of operational commitment
salt require an exact scope disposition before any future `complete` call.
No salt was generated here, and the salt question is not needed to establish
the independent first-input derivation blocker above.

## H. Generated package identities/counts

**Actual generated scientific artifacts: 0.** No fabricated output identity or
completion receipt was created.

The existing full producer-root output set is boundary.json, D draw intents,
D draw audits, salt.intent.json, salt.bin, audit.json, payload.json and
receipt.json: **2D+6 files**, minimum 2830, excluding authority-retained copies.
The payload records N/domain, operation, ordered positions, original K/E/L,
boundary and preceding authority tip. S binds accepted count, rejection counts,
audit/payload/salt ArtifactRefs, boundary, operation and completion authority tip.
ArtifactRefs use exact raw bytes/length/SHA-256; record identities use the frozen
canonical-body digest and RecordRef including raw SHA-256. These are expected
recipes only. Approved producer placement was verified without generating files.

## I. Deterministic verification

**Not performed: no retained raw input or generated package exists.**
Frozen `read_audit` reproduces each rejection/acceptance, position, intent and
chain digest from the complete stored raw sequence. It is not a deterministic
generator of independent later draws from draw 1. No new synthetic boundary,
alternate package, experimental analysis or REAL redraw was used as verification.

## J. Authority-state result

No authority event was appended. Current tip remains exactly:

```text
T2 = 765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485
```

The original CONSUME is
`v6-e9-authority-event-v2-765e7f4471ab`, raw SHA-256
`6c1b60409a9ff29553821774418c5020eb3d6e10742cf1d17c49455b94e046e3`.
The chain has three events and exactly one CONSUME. Original recorder
`v6-e9-producer-01`, its appointment, registered root and registry remain unchanged.

The sealed `protected` raw_draw/salt_creation/payload_seal paths do not append
authority events; commitment publication has a separate U-consumption path,
which was not entered. No T3 or HOLD event was fabricated to document this stop.

## K. Recovery/interruption history

No scientific interruption occurred because the entropy procedure never started.
The restricted interpreter launch was unavailable; the scoped elevated audit
succeeded. The restricted remote lookup failed to connect; elevated live lookup
succeeded. Neither failure entered the scientific procedure or attempted entropy.

| Crash/recovery state | Frozen handling |
| --- | --- |
| Definitely before first procedure/source call, no marker/boundary/intent | Preserve original consumed G; future first action needs resolved scope, fresh baseline and trustworthy instant; never consume G again |
| Marker/source receipt created but boundary absent/corrupt | Frozen draw routine rejects orphan first-raw state; preserve artifacts and stop for integrity disposition |
| Boundary/intent exists but source call/value cannot be accounted for | Intent/audit count mismatch fails closed; no assumption of zero calls and no redraw |
| Exact raw audit durably retained and valid | Value/order/disposition remain permanent; reconstruct prefix with `read_audit`; never replace an accepted position |
| Marker, boundary, receipt or audit malformed/binding-mismatched | Preserve all bytes; stop; no fabricated repair, alternate raw value or backdating |
| Later generation interrupted after a durable prefix | Preserve prefix; no deterministic full-package continuation from draw 1 exists; further original-operation draws require valid authorization and applicable integrity gates |
| Incomplete/uncertain salt or write-once payload/S material | Preserve all files; complete rejects previously attempted salt; sealed write-once outputs cannot be overwritten; no entropy retry as an infrastructure repair |

G's boundary procedure explicitly requires uncertain boundary, interrupted draw
or ordering ambiguity to stop for `INTEGRITY_HOLD_PENDING_ADJUDICATION`.
PG-R7/PG-R8 release/continuation conditions are separate lead/independent gates;
this task does not manufacture those events. A protocol mismatch detected before
first raw is recorded here as an administrative stop, not an already-established
scientific integrity hold or terminal cancellation.

## L. Privacy/evidence placement

Only administrative evidence was added beneath the approved private study root,
in `first_raw_generation_01/`: the exact lead request, guarded audit procedure,
baseline verification, and pre-execution checklist. Final integrity evidence is
retained separately there. These files are not operational records or generation
outputs. No private values or detailed census/path map appear in this public return.

The baseline verification raw SHA-256 is
`da5cf9708f20d509524074f75d8503df375d44a54bf3c4fd2c6ac2293cf49f0e`;
procedure SHA-256 is
`72b389764ce3f09a9b4e3f935b9d62258d7d9203ed0733a20438447d023e33ab`;
lead request SHA-256 is
`5d45ef0f93990a2545e72afaa14dcc913f880536b1591135f7f7e15284b7c798`.
Administrative evidence is flushed/fsynced/read back with the sealed helper.
No private material was staged, committed or published.

## M. Integrity verification

Final verification rechecks Seal 08 329/329, preservation 1607/1607, original
P-through-G RecordRefs, original CONSUME/producer/authority bytes, the complete
1357-file inherited private map, empty producer root and exact unchanged T2.
All additions are accounted administrative evidence only. No source/test/schema/
seal modification, W, salt, native execution, publication, U or C was produced.
No synthetic qualification, pytest, lint, mypy or payoff analysis was run or
claimed; this is a frozen-procedure/integrity audit with no code changes.

| State | Result |
| --- | --- |
| Gate 8 / Q / O | ESTABLISHED |
| V / A / R / B | PASS / APPROVED / ACCEPTED / PASS–ESTABLISHED |
| Gate 7 / G / producer | ESTABLISHED / CONSUMED exactly once / REGISTERED |
| Authority execution | Original authorization consumed; original operation admitted at T2 |
| Scientific raw / generation | NOT BEGUN / ABSENT |
| First-raw marker / REAL calls | ABSENT / **0** |
| W / salt | ABSENT / ABSENT |
| Native experiment | NOT STARTED |
| Integrity stage | BEFORE_GENERATION; pre-entropy administrative stop |
| Later execution / Requirement C | LOCKED / **NOT ESTABLISHED** |

Historical completeness remains NOT ESTABLISHED. The preserved 357 gaps,
DEP-01–DEP-05 and H-unknown limitation retain their prior dispositions.

## N. Exact next gate

**Lead disposition of the requested procedure before first raw.** Clarify whether
the intended scope is the existing repeated uint64 OS-CSPRNG rejection-sampling
procedure, with verification from its complete retained sequence, and resolve
the exact salt boundary. No replacement G or second CONSUME is needed or allowed
as a convenience. Trustworthy pre-first-draw instant/ordering evidence and fresh
baseline verification remain required before entering the original first action.

If deterministic expansion from one retained raw input is intended, that is a
different scientific recipe requiring the applicable prospective protocol/
instrument/qualification/downstream gate decisions. It cannot be implemented
under this task's prohibition on source changes or silently applied to consumed G.
Operational W and all later study gates remain outside this task.

## O. Git status

Branch/HEAD/upstream/live remote remain the baseline above; tracked working-tree
and index diffs remain empty. This return is the sole new public repository file.
Inherited untracked work and local-only settings were preserved. Private additions
remain under the ignored approved study root. No staging, commit, push or
publication occurred. No automatic approval rejection occurred.
