# Bytefray V6 E9 — Operational Timing Procedure Design 01

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**PROPOSED DESIGN ONLY. Implementer and fresh independent review: NOT OPERATIONALLY PROVABLE on
the presently established original-G evidence and unchanged qualified boundary.**
Fresh adversarial design review is complete and retained in M. This conclusion
concerns the proposed procedure and available proof;
it does not establish that every possible future mechanism is impossible.
Accepted classification **B — missing operational procedure** remains the starting
lead decision. No protocol amendment has been demonstrated necessary merely by
this assessment. Execution remains **LOCKED**; Requirement C **NOT ESTABLISHED**.

The specific preferred candidate is an **independently operated Windows native
debugger that withholds continuation before the raw callable is invoked, coupled
to a separately administered durable witness journal and independent verifier**.
It is concrete enough to locate its failure points, but is not a conforming
operational solution for this consumed G. In particular, neither installing a
debugger now nor signing its observations establishes the previously unobserved
no-earlier-draw interval. No implementation or evidence acquisition is approved.

## A. Baseline and governing records

### Fresh entry verification

Read-only, entropy-denied audit reproduced exact raw hashes and canonical
P/I/Q/O/V/A/R/B/G identities using the frozen readers. The I-specific digest
recipe was used, rather than the generic body digest. It imported record,
authority and adoption readers only: no generation import, Generator or
AuthorityLog construction, registration, lock/protected action or scientific
execution. Research `os.urandom`/`os.getrandom` calls were denied before imports;
attempts were zero. This is bounded audit accounting, not independent proof of
all historical activity on the host. The repository interpreter required elevated
read-only execution because the sandbox could not launch it. No automatic
approval rejection occurred. Live remote verification succeeded separately.

| Check | Fresh result |
| --- | --- |
| Branch / HEAD / upstream / live remote | `v6-research`; all at `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Tracked tree / index | Empty diffs; inherited untracked work retained |
| Seal 08 | **329/329 unchanged**, 293 implementation plus 36 qualification files; manifest raw hashes reproduced |
| AR/B preservation map | **1607/1607 unchanged** |
| Original multi-draw inherited private map | **1362/1362 unchanged** |
| Current private files at entry | **1374**; exact entry census retained privately |
| Original tuple | Exact P/I/Q/O/V/A/R/B/G raw hashes, body recipes, dependencies and adopted review verified |
| Gate 8 / Q/O / V / A / R / B / Gate 7 | ESTABLISHED / ESTABLISHED / PASS / APPROVED / ACCEPTED / PASS–ESTABLISHED / ESTABLISHED |
| G / producer | Original G consumed exactly once; original registered producer, recorder and empty root |
| Authority | Exactly B ISSUE → G ISSUE → original CONSUME; active sequence 3, T2; no intervening event or stale lock |
| First-raw marker / retained marker copy | ABSENT / ABSENT |
| Boundary / raw transcript / salt / package / W | ABSENT / ABSENT / ABSENT / ABSENT / ABSENT |
| This audit's REAL research calls / attempts | **0 / 0** |

Administrative entry census raw SHA-256:
`a6dd9efbc0e0e686a73046a8c32fc021a38cc5daff43fb7d9ffdde3490303432`.
Exact retained design authorization raw SHA-256:
`ff7d7ab40bcb8fe4811860702699e6a97c30c152bf1a5c0722a64b97a82cb92f`.
The census covers the 1374 private files and 1638 readable tracked/nonignored
files, plus a separate local-only settings receipt when present. Git reported
inaccessible inherited pytest cache/temp directories; these were neither read nor
changed. They are not substituted for the frozen 329/1607/1362 maps. These new
administrative receipts are not timing evidence and contain no operational PASS.

### Authoritative bindings and clauses

| Record | Exact identity / controlling digest |
| --- | --- |
| P, [adopted envelope](../../../tools/research/v6/e9/protocol_freeze_v2_adopted_02.json) | `v6-e9-prereg-v2-539a60806eab`; `539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0` |
| I, [Seal-08 instrument](../../../tools/research/v6/e9/v2_instrument_identity_08.json) | `v6-e9-instrument-v2-3c692f23d2d9`; `3c692f23d2d9a7467e07b36ea97a382c1497511033767b078dc8de057033d8e0` |
| G, [original authorization](../../../tools/research/v6/e9/v2_generation_authorization_study_01.json) | `v6-e9-generation-authorization-v2-0ea6d2043fbd`; `0ea6d2043fbd7619ea724da15b6a4e106ffeaa3c929b43b9bcb3ff354c668175`; raw `21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8` |
| T2 / original CONSUME | `765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485`; raw `6c1b60409a9ff29553821774418c5020eb3d6e10742cf1d17c49455b94e046e3` |
| [Disposition 09](../../../tools/research/v6/e9/v2_finding_disposition_09.json) | Raw `53261258982fb2c962f0176cda7a0368ed87c50a03ab8b9e7c472c675e2764b5`; unchanged mandatory timing prerequisite |

Use the complete RecordRefs through G and original producer ArtifactRef from
these exact inputs in any proposed evidence; shortened identities never control
equality. Q/O/V/A/R/B statuses above are existing accepted states, not newly issued
records. See [prior resolution plan](V6_E9_TIMING_EVIDENCE_RESOLUTION_PLAN_01.md)
and [retained generation return](V6_E9_MULTI_DRAW_GENERATION_RETURN_02.md).

The adopted [rule contract](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md)
PG-R3 at line 100 requires independent complete pre-generation verification and
separate authorization. PG-R4 at line 102 fixes the durable boundary immediately
before the first experimental raw draw, after inventory sealing/verification.
The adopted [catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json)
`records.GenerationBoundary` requires trustworthy pre-first-raw evidence, current
authority/fence, durable write and verified inventory/authority before raw;
uncertain ordering is a hold. `common.independence` requires independence from
production of the implementation/evidence verified. G's `body.boundary_procedure`
requires the original protected marker/source/boundary/intent order and stops on
missing or ambiguous trust/order. Disposition 09's retained Phase A requires
independent timing PASS **before marker creation**, not merely before returned
random bytes. PG-R8/R8 and the identity/source sections govern changed operational
inputs and instrument qualification. No E9 timing procedure exists in `docs/specs/`.
Architecture and repository agent guidance were read. No implementation follows.

## B. Frozen execution boundary

Source anchors below refer to unchanged Seal-08 bytes, not a conceptual model.

| Step | Implemented behavior |
| --- | --- |
| Construction | [generation.py](../../../tools/research/v6/e9/v2/generation.py):40–72 rejects injection in REAL mode, loads original K, checks K/E/L against O, and invokes original producer registration. Even constructing Generator is an operative action, avoided here. |
| Entry | `Generator.draw_one(expected_tip, durable_instant)`, line 164; calls `AuthorityLog.protected("raw_draw", …)` at 212–213. No pre-marker independent timing verifier is built into this entry. |
| Protected entry | [authority.py](../../../tools/research/v6/e9/v2/authority.py):789–804 obtains the exclusive file lock, runs `_check`, creates Lease from actual tip/epoch, invokes the action and checks again after it returns. A post-action check cannot prevent entropy already invoked inside the action. |
| Checks | `_check`:654–755 verifies tip, hold/terminal status, exact active bindings, source pins, scoped actors, affirmative decisions, study/dependencies, K/E/L, limitations, independence and original consumed G/operation. Producer checks bind immutable registration and CONSUME evidence. |
| Pre-existing history | `draw_one`:166–178 reads and validates ordered audit; rejects complete list/salt and orphan first-raw marker/copy when original boundary is missing. `_boundary`:82–108 checks original tuple/producer/marker/source; it does not authenticate timing evidence. |
| First-raw marker | `draw_one`:177 invokes `AuthorityLog.mark_first_raw` (`authority.py`:390–397). Write-once canonical original-study/G/producer marker and retained raw copy. This marks an attempted first boundary before source invocation; it is not a receipt that entropy completed. |
| Source declaration | `draw_one`:178–180 retains exact REAL declaration naming `os.urandom` for both draw and salt. |
| Boundary | `draw_one`:181–189 creates GenerationBoundary with caller-supplied `durable_instant`, actual lease tip/fence, original tuple, producer/marker/source references; durably writes `boundary.json`, then reads it back. |
| Intent | `draw_one`:191–195 asserts original producer and writes/readbacks ordinal-1 intent bound to boundary audit tip and actual authority tip. |
| First source invocation | `draw_one`:196–197 selects `os.urandom` in REAL mode and executes **`source(8)`**. This is the point that must not be initiated early. Waiting until bytes return, or until a later OS RNG breakpoint, may already be too late. |
| Raw audit | `draw_one`:198–211 validates eight bytes, determines K/duplicate rejection or acceptance, durably writes ordered raw audit and rechecks it. Every raw candidate counts, including rejected values. |
| Salt | `Generator.complete`:242–264, salt action 247–262, checks N=1412 accepted positions under protected `salt_creation`; refuses prior salt intent/file; durable salt intent precedes **one `source(32)`** at 257, then durable `salt.bin`. Same REAL `os.urandom` API, distinct later purpose. |

`durable_bytes` (`authority.py`:100–109) uses exclusive `xb`, write, flush, fsync
and exact regular-file readback. Intent/audit linkage and authority predecessor
digests provide deterministic ordering within the recorder model. They supply
neither external event authenticity nor proof against omission/deletion outside
that model. The sealed regular-file reader expressly assumes no hostile
concurrent replacement during its check/open interval. Do not claim a stronger
host isolation or physical power-loss guarantee from these implementations.

Source search of all `v2/*.py` found two operative REAL source sites: raw at 197
and salt at 257. `draw_one` is also a subsequent-draw entry if a valid boundary
already exists; `complete` cannot create a legal first raw because it requires a
valid complete audit/list. `_boundary`, `read_audit`, integrity/prefix workflows
do not introduce another RNG site. SYNTHETIC mode uses injected callables and must
remain separate. There is no generation CLI. This is complete **static coverage
of sealed direct generation sites**, not proof of all runtime behavior: resolver
and source-check callbacks, imported Python/C code, saved aliases, another process
with study access, direct OS RNG calls, or hostile runtime substitution are not
automatically covered by finding these two lines. The timing caller is outside
the sealed function and can invoke entropy before calling it. All those paths
must be addressed by independent confinement/observation before a P5 PASS.

The recorder is the Actor passed into Generator and bound in the producer
registry; it is not an external clock or independent entropy monitor. The REAL
source is a module-global API available to the process before Generator exists.
There is no sealed capability that makes entropy inaccessible until evidence
verification. The venv configuration reports Python 3.13.14; a future debugger
must bind actual loaded image hashes/symbols, not infer them from that text.
Python documents Windows `os.urandom` via BCryptGenRandom, but API membership is
not a study identity signal. [Python OS documentation](https://docs.python.org/3.13/library/os.html#os.urandom)

## C. Required independently verifiable claims

| Claim | Required proof | Present position |
| --- | --- | --- |
| P1 boundary identity | Exact original study, operation, full consumed G, producer/recorder/registry, I/Q, actual process and boundary bytes | Static binding recipes verified; no actual boundary exists |
| P2 state validity | Fresh full inventory/tuple/source/authority checks before first procedure, then unchanged protected-entry checks and continuous custody | Retained baseline supports preparation; operational recheck and custody absent |
| P3 durable timing | Independent evidence of actual durable boundary in the required window; qualifying Phase-A evidence/PASS before marker | No such evidence; a certificate promising future observation is not the occurred boundary |
| P4 ordering | Trustworthy evidence → valid verification → marker/source/boundary/intent → first raw invocation, with no bypass | Frozen code orders local writes; external pre-invocation gate is unqualified |
| P5 no prior draw | Complete bounded historical no-draw basis plus prevention/observation of every subsequent study acquisition path | Earlier retained denied-call reports/empty root are corroboration; historical independent coverage not established |

P5 concerns raw acquisition for this original study/operation, not every random
byte used anywhere by Windows. Python startup hash secrets and transport/key
randomness must not be silently labeled study draws or silently excluded. A later
procedure must identify their provenance and non-use as scientific raw/salt
input without weakening the experiment's no-earlier-raw requirement. No such
new entropy is requested by this design. Proving absence since observer startup
does not prove absence before observer startup.

## D. Threat and trust model

The relevant adversary can submit a wrong/stale/replayed signed receipt, falsify
local dates, omit a prior invocation, substitute state between verification and
draw, invoke a saved/native RNG alias, use another process, or claim later
verification occurred earlier. Assume errors, interruption and storage loss as
well as deception. Cryptography protects bound bytes only to its stated scope.

The preferred candidate would place the generator in a debugger-controlled
Windows process, under an independently accountable observer operator; the
recorder could not resume/detach it or start another study-access process.
The observer would record process/image/frame/boundary and debug-event ordering.
A separately administered witness service would retain opaque evidence bytes in
an append-only journal and sign a durable acknowledgment containing its sequence
and prior head. A distinct verifier would read exact source/state/evidence and
trust material and return PASS/FAIL/UNAVAILABLE. Service, operator, keys,
retention policy and source access are unappointed; no deployed E9 service is
claimed available. Windows debug APIs are available mechanisms; they are not
evidence that a complete E9 observer already exists.

| Independence property | Proposed supplier and limitation |
| --- | --- |
| Independent creation | Observer under separate custody plus external witness receipt; no independence if recorder controls observer/key/service |
| Independent verification | Fresh identified reviewer/verifier checks exact inputs; different context does not make the underlying observations authentic |
| Independent process observation | Native debugger observes its attached process from another process; same machine/kernel/storage and incomplete other-process coverage remain dependencies |
| Independent human participation | Separately appointed observer operator or witness custodian; not supplied by an AI alias and not currently appointed |

Trust roots must be obtained independently of submitted receipts. The recorder
and observer share host kernel and potentially hardware administrator; independent
credentials, process-access enforcement and external journal custody would have
to be demonstrated. An administrator able to run an unobserved study producer
or rewrite observer state defeats this user-mode proposal. We do not assume an
unrelated compromise anywhere in the world; the exact approved study-access
boundary must be enumerated and justified. No prior external observation exists
to authenticate that boundary over the earlier interval.

Monotonic debug/witness sequence, stopped process custody and verified durable
acknowledgments supply the proposed order; local/remote clock text is secondary.
Historical-use comparisons still require trustworthy comparable order evidence
or time intervals; unrelated log sequence numbers are not globally comparable.
Later signing cannot make an earlier check or observation happen retroactively.

## E. Candidate procedures

Each row is evaluated alone. Combining signatures with incomplete observation
does not remove the incompleteness.

| Candidate | Boundary observation / trusted order / P5 | Trust / durability / independent replay | Instrument impact / conformity / recovery |
| --- | --- | --- | --- |
| Existing frozen durable recorder | Actual local boundary/intent readbacks; reviewed program order. No external witness and no control over out-of-path or historically omitted calls | Trust original recorder/host/storage. Flush/fsync/readback retains bytes; reconstruct hashes/chain from exact artifacts | Sealed bytes unchanged; implements local parts of PG-R3/R4 and G, fails independent trust proof alone. Orphan marker or unmatched intent stops; no redraw |
| RFC 3161 signed timestamp | Observes a submitted digest's existence, not actual boundary/source invocation. Does not prevent an earlier draw or bind a future durable write automatically | Trust TSA/key/policy/clock. Retain request/token/chain/validation material and exact imprint; durable local retention plus validated token. Offline verifier checks imprint, signature, context/freshness and trust | No sealed edit if caller supplies evidence. No frozen clause authorizes treating digest existence as P5 or occurred future boundary. Missing service/token means UNAVAILABLE; post-entropy token cannot repair timing |
| Independent observer/witness process | Observe actual process, complete boundary readback and stop before callable dispatch. Can enforce prospective ordering only within demonstrated process/host coverage | Trust observer custody and kernel; independent external journal required against local rewrite. Replay retained state/image/frame/event/durable-ack proof; video or witness recollection alone lacks complete API coverage | Candidate external supervision, no source edit; procedural/qualification impact unresolved. Starts too late or cannot map pre-call dispatch → UNAVAILABLE; any escape/early call → FAIL/hold |
| Externally attested append-only event | Signed durable inclusion can attest exact observed boundary bytes and sequence. Receipt on recorder-submitted bytes alone attests submission, not occurrence or P5 | Trust external operator, authenticated observer source, no-equivocation/retention policy. Require retained inclusion/consistency/durable-ack material; a queued upload or signed promise is not durable inclusion | Can bind an existing evidence field without editing source. Supplies retention/order only for observed events; after-draw inclusion cannot masquerade as pre-draw evidence. Lost acknowledgment/partition stops |
| Existing Windows ETW/execution audit | Observe enabled providers' events. No established provider set proves every Python/native RNG invocation, boundary readback and prior study interval, and no synchronous pre-call release gate is established | Trust OS/providers/session/operator; retain exact configuration, event-loss counters, start/end coverage and log bytes. Zero lost events does not establish omitted-provider coverage | No source edit for existing providers. No frozen clause equates generic process/file audit to P5. Incomplete session or unobservable API → UNAVAILABLE; known loss/order conflict stops |

RFC 3161 supports digest existence-time assertions; its proof does not extend to
the submitter's prior RNG behavior. This is the design's inference from the
timestamped event's scope. [RFC 3161, introduction and section 2.4](https://www.rfc-editor.org/rfc/rfc3161)
ETW uses enabled providers and buffering; Microsoft's tracing guide documents
unrecoverable lost events. No complete RNG provider coverage is established here.
[Microsoft TraceEvent guide](https://github.com/microsoft/perfview/blob/main/documentation/TraceEvent/TraceEventProgrammersGuide.md)

## F. Recommended exact procedure

**Recommend only the debugger-controlled observation candidate for further
feasibility disposition. Its exact proposed sequence below stops at unresolved
prerequisites for this study; no conforming implementation sequence is claimed.**
It uses Windows native debugging events, per-thread hardware execution
breakpoints/single stepping and an external durable witness journal. Microsoft
documents that a debug event suspends all threads in the affected process until
ContinueDebugEvent. This supports a gate for that process, not all host processes.
[Microsoft debugging events](https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events)
Hardware/debug-register control avoids writing sealed files or patching target
instructions; debugger intervention still changes the operational execution
environment and requires impact review. No breakpoint is installed here.

1. **Original identity.** Resolve exact original P-through-G, producer registry
   and retained CONSUME. Verify original root/recorder/operation, full hashes and
   image/source provenance. Never create another producer or consume G again.
2. **State validity.** Independently reverify K/E/L/source material, original
   Q/O/V/A/R/B and the T0→T1→T2 chain; account for B's retained historical T0
   marker without editing it. Require unheld/unrevoked/nonterminal epoch-0 T2,
   no marker/copy/intent/audit/salt/package/W, and preserved byte maps.
3. **Historical observation prerequisite.** Establish independently authentic
   continuous absence-of-study-raw evidence from the earliest possible authorized
   acquisition through the handoff to this observer. If confined processes were
   independently incapable of acquiring study entropy, retain that enforcement
   proof. Retained local empty-root/hash/deny reports alone do not independently
   establish this interval. **Current evidence cannot pass this step. Stop
   UNAVAILABLE; do not start an operational observed producer.**
4. **Prospective observation boundary, conditional only.** Under separately
   approved custody, start the original operation's process under a native
   debugger before its first executable study code; attaching after possible
   acquisition is insufficient. Keep the exact original registered paths/Actor.
   Account for all threads, descendants and other principals with study access.
   Pin CPython/OS/module images and demonstrate complete permitted code/callback
   coverage; deny independent study acquisition outside this process. An ordinary
   debugger does not supply that host access-control property by itself.
5. **Prove the gate is before invocation.** Map the unchanged Python code object
   for `draw_one.action` through actual CPython dispatch to the instruction
   immediately preceding invocation of the selected `source(8)` callable.
   Identify its actual callable, frame, arguments and original producer.
   Observe earlier marker/source/boundary/intent writes and successful readbacks.
   Breakpoints at BCryptGenRandom or at entry inside `os.urandom` are insufficient
   alone: the Python invocation may already have begun. Cover raw calls through
   aliases/callbacks and the later salt callable separately. Unresolvable native
   image/frame mapping, unobserved code, or an uncovered thread prevents PASS.
6. **Phase-A evidence and prescribed boundary evidence.** Before marker, retain
   the independent session/custody/coverage certificate and have its exact inputs
   independently verified. Supply only its opaque ArtifactRef/context to the
   existing `durable_instant` field. This certificate is prospective, not an
   occurred boundary. When the unchanged function later completes boundary and
   intent readbacks, keep the process stopped **before** the raw callable dispatch
   and create a distinct actual-boundary observation record binding those bytes,
   tip/fence, frame and prior certificate. Do not substitute a pre-session time
   for the actual boundary time.
7. **Durable external retention.** While stopped, independently transmit the
   actual observation to the separately administered append-only journal; require
   byte-matching durable acknowledgment and readback, then retain exact proof and
   validation inputs locally and externally. No receipt or signing operation may
   request additional study raw/salt input. Service keys/transport entropy are a
   separate scope issue, never scientific samples.
8. **Independent verification before release.** A distinct verifier checks
   actual boundary/source/intent, custody/coverage, exact original tuple and
   active authority, journal acknowledgment and source trust. Durably retain its
   exact PASS decision before ContinueDebugEvent. **This post-boundary check
   cannot satisfy Disposition 09's pre-marker Phase-A check by backdating.** A
   pre-marker certificate plus later observation has not been established to
   satisfy that requirement or the frozen `durable_instant` meaning. Stop while
   this link is unresolved, even if signatures and a later PASS validate.
9. **Permit exactly the original call, conditionally.** Only after all P1–P5,
   both timing stages and original-G compatibility are established may the
   observer release the stopped dispatch. No altered return bytes, skipped
   instructions, source substitution, extra invocation or new entropy API.
   The existing call and subsequent raw audit remain unchanged. This design
   supplies no such release authorization; as assessed, release stays disabled.
10. **Retain later observation without rewriting history.** Append the observed
    invocation/return/audit linkage and observer continuity to the external
    journal; preserve all pre-call receipts and original sealed records. A later
    signature verifies an earlier authenticated journal event only when that
    earlier event's durable acknowledgment already existed and was verified
    before release. It cannot retroactively supply missing durability or PASS.

Available debug APIs establish a real suspension primitive. They do not establish
an installed observer, loaded-image mapping, external witness service, continuous
historical custody, or complete bypass prevention. The candidate therefore cannot
currently complete steps 3, 4, 5 and the conformity obligation in step 8. Installing
new native observer logic also raises the instrument/source-manifest question in K.
Do not turn this failed feasibility sequence into an implementation checklist.

## G. Evidence format and bindings

Proposed administrative evidence layout, not a new frozen schema, record,
identity or evidence receipt. No concrete future event digest is fabricated.

| Proposed retained item | Exact contents and forward bindings |
| --- | --- |
| Context C0 | Study/operation; complete RecordRefs P-through-G; original producer registry ArtifactRef, recorder Actor/authority; K/E/L and source/qualification refs; exact CONSUME; actual T2/epoch; observer/verifier appointment refs; procedure version/raw hash |
| Coverage certificate C1 | C0 raw hash; independently sourced observer/host/image/session identities; historical coverage interval and basis; all process/thread/callback/API routes and exclusions; current no-draw claim with limits; stopped-state proof; external previous journal head/one-use deterministic session counter |
| Pre-marker verifier V1 | Exact C0/C1 bytes/trust material; PASS/FAIL/UNAVAILABLE; independent Actor/provenance; actual acquisition/verification order and durable receipt. A local creation date is not evidence of execution order |
| Field input DI | Existing `durable_instant` JSON holds approved opaque PRIVATE refs for C0/C1/V1 and the named observation session/event relationship. Generic JSON acceptance proves structure only. This proposed interpretation is not accepted as trustworthy actual instant |
| Actual observation E1 | Actual GenerationBoundary and ordinal-1 intent raw hashes/lengths; marker/source/producer evidence; actual tip/fence; target image/code/frame/instruction/arguments; all-thread stopped debug event; observer sequence/prior head; continuous no-prior-call evidence; C0/C1/V1/DI hashes |
| External durable acknowledgment D1 | Exact E1 hash/length, authenticated observer source, external durable event sequence/prior head, readback/inclusion evidence, retained signature/key/trust/certificate/policy material; no promise of future durability |
| Release decision V2 | Exact E1/D1 and trust inputs, independent checks/results, continuous stopped custody, active authority recheck, P1–P5 disposition; durable PASS strictly before release |
| Audit tail E2 | Actual release/debug sequence and first callable invocation/return/ordered audit; separately retained observer/witness evidence, referencing V2 forward |

C0/C1 cannot hash E1 before it exists. DI cannot embed a receipt that hashes the
final boundary containing that same receipt. The proposed direction is C0→C1→
V1→DI→boundary/intent→E1→D1→V2→release→E2. E1 is a separate externally retained
attestation; it cannot be silently inserted into or replace the write-once
GenerationBoundary. Referring to a future session event is not a proof that it
occurred. That remaining P3/Phase-A link is deliberately exposed.

Use canonical UTF-8 rules and raw SHA-256/length; store exact signed binary
receipt bytes separately rather than reserialize them and assume signature
equivalence. Original frozen Actor/ArtifactRef/RecordRef recipes apply only where
the frozen catalogue permits them. Private opaque IDs resolve through a retained
private map. No raw values, salt, private path map, seed-bearing diagnostics or
host memory dumps belong in public documents/external public logs. Even hashes
of raw eight-byte values are unnecessary external disclosure; attest context
and private artifact identities with confidential retention. Missing source
resolution is UNAVAILABLE, not a usable signed assertion.

## H. Durability and event-ordering guarantees

The desired proof is causal, not a comparison of potentially skewed clocks:

`independent historical coverage → pre-marker V1 → marker/source → durable actual
boundary readback → durable intent readback → stopped pre-call dispatch → durable
E1/D1/V2 → ContinueDebugEvent → source(8) invocation → raw audit`.

For a fully covered controlled process, a genuine all-thread stop before dispatch
and exclusive custody of continuation imply the dispatch cannot run while the
verifier/witness is establishing evidence. Exact external durable acknowledgment
and independently retained PASS before continuation would establish prospective
P4. This is a **conditional proof**, not evidence of actual coverage or a P5 proof
over the historical interval. Kernel debugging APIs do not automatically stop
unrelated processes, recover old events, or prevent an administrator's bypass.

E1 authenticates actual successful local boundary readback; D1 gives independent
retention before release. Local fsync/readback is the frozen recorder guarantee.
External durable acknowledgment requires a specified crash/reboot/storage
retention contract and independently controlled readback; an HTTP success, local
file signature, screenshot, queued request or eventual timestamp is insufficient.
No physical power-loss test or external retention qualification occurred here.
Windows documents buffer flushing, which alone is not an external custody proof.
[Microsoft FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

Strict order can avoid an absolute UTC requirement only when the same trusted
observation channel covers the events compared. Clock disagreement is harmless
to a demonstrated causal gate but fatal to any sole wall-time comparison whose
uncertainty overlaps the boundary. Retain clock provenance/uncertainty if used;
do not invent an accuracy/freshness threshold. The freshness rule proposed here
is exact original context plus a one-use witness session/counter, continuously
stopped custody and no authority drift. Historic-use events outside that channel
need separately trustworthy comparable timing; unrelated journals are insufficient.

The frozen no-pause function has no supported evidence-acquisition callback at
actual boundary completion. External debugger suspension preserves instruction
order but adds a new operational supervisory boundary. It does not make E1 exist
at the earlier V1 check, nor cause DI to contain a future receipt. The split
certificate/event construction therefore has unresolved P3/conformity as well as
P5. Treating a conditional future promise as the actual independently verified
instant would weaken the contract and require amendment rather than procedure.

## I. Interruption/recovery matrix

Taxonomy: **UNAVAILABLE / LOCKED** for absent proof before entry; **FAIL / LOCKED**
for positive invalid bindings/evidence before entry; actual early raw, ambiguous
started boundary or interrupted intent/audit requires **INTEGRITY_HOLD_PENDING_ADJUDICATION**
under G. These are assessment dispositions, not newly appended authority HOLDs.
Absent information never hides a present positive mismatch. Formal HOLD/release/
termination must use separately authorized frozen roles and events.

| Failure | Classification and mandatory behavior |
| --- | --- |
| Observer absent | UNAVAILABLE; do not enter draw_one or create marker |
| Observer starts too late | UNAVAILABLE for missing interval; positive evidence of an earlier study call means FAIL/hold; never redefine first draw to observer start |
| Wrong study/G/producer | FAIL; retain mismatch, prohibit entry/release; do not re-register/rebind |
| Invalid/stale/held/revoked authority | FAIL/refused operation; no entropy and no automatic release/renewal |
| Evidence created but not durably retained | UNAVAILABLE before entry; after marker/intent, hold pending adjudication; no release based on queued journal writes |
| Different evidence digest | FAIL; retain both exact versions and stop; do not normalize or replace to obtain PASS |
| Witness cannot resolve/verify source | UNAVAILABLE; unknown signature signer is not an independent source; stop |
| Entropy invocation before evidence finalized | FAIL/INTEGRITY_HOLD_PENDING_ADJUDICATION; late receipt cannot repair order; no redraw |
| Crash after certificate, before marker | No raw presumed only if independent coverage proves it; remain LOCKED. Preserve receipt; any future recheck/re-entry needs separate disposition and same-G/bindings proof; no automatic retry |
| Crash after marker/boundary/intent but before raw | Started boundary is not automatically recoverable. Orphan marker makes frozen entry refuse; unmatched intent fails audit. Preserve bytes, hold/adjudicate; no deletion, rollback or retry merely because debugger reports zero |
| Crash after initiating entropy | Interrupted raw/audit integrity hold; eight bytes may have been acquired without audit. No extra call, regenerated value or restart |
| Recorder/observer disagree about order | FAIL if positive contradiction; otherwise UNAVAILABLE; after started boundary, hold. Neither log wins by being signed |
| Clock disagreement | Use authenticated causal ordering only if independently complete; if required comparison remains ambiguous, UNAVAILABLE/hold; never choose a convenient clock |
| External trust service unavailable | UNAVAILABLE before entry; after boundary retain stopped state/fail closed and hold if custody cannot persist. Do not silently fall back to local time |
| Stale/replayed attestation | FAIL: reject used session/counter, changed context or broken custody; signature validity cannot override freshness |
| Other process submits evidence | FAIL for unauthorized source; if legitimate source cannot be resolved, UNAVAILABLE. Preserve submission, never let it release original target |
| Observer failure/detachment/thread or descendant escape | Loss of complete custody/coverage prevents release; preserve evidence. If a call may have happened, hold; no automatic debugger detach/resume |
| Verification interrupted | No durable complete PASS means UNAVAILABLE; keep gate closed; later verification cannot be dated earlier |

If a source call is known uninitiated, this does not itself authorize another
attempt after any frozen marker/intent exists. If a complete raw audit already
exists, retain that exact candidate and disposition; neither observer restart
nor a failed receipt permits resampling. Salt has its separate frozen single
intent/call rule. This design adds no recovery rule permitting entropy.

## J. Independent qualification plan

Future adversarial plan only. **No tests were implemented or executed.** Use
isolated unmistakably SYNTHETIC fixtures, deterministic byte streams, frozen
copies rather than the actual study/root/G, and denied OS entropy. An observer
test may simulate native-call dispatch without invoking any REAL RNG. A fresh
qualifier must construct cases independently, inspect complete manifests and
prove the gate is before invocation, not just before returned bytes. Model tests
of ideal events cannot qualify actual image mapping, host custody or old history.

| Challenge / deterministic construction | Expected classification | Inspect / mandatory stop |
| --- | --- | --- |
| Fabricated timestamps: edit local/claimed UTC while preserving unrelated valid signatures | FAIL if relied on as authentic event time; otherwise no timing PASS from dates alone | Signed scope, observation/journal order, clock source; deny simulated release until all actual claims proven |
| Replayed valid receipt: reuse authentic receipt with already-used session/counter | FAIL | One-use external session ledger, previous head and full context; no release |
| Valid receipt/wrong G: journal signs context for distinct fixture G | FAIL | Full G RecordRef/raw hash and CONSUME; no rebind or release |
| Valid receipt/wrong producer: same G but different fixture root/Actor/registry | FAIL | Registry/CONSUME binding and actual target provenance; no registration/release |
| Altered authority: mutate tip/epoch/dependency, or insert HOLD after preflight | FAIL | Original tuple, chain, current stopped-state check and protected-entry validation; no release |
| Timestamp/receipt acquired after simulated entropy dispatch | FAIL/hold | Trusted gate/dispatch/journal/durable-verification order; prohibit another simulated draw |
| Undetected earlier invocation: deterministic shadow source call before observer start, then clean local files and valid later receipts | UNAVAILABLE if no historical coverage; FAIL if prior call proven. Any PASS exposes unsound design | Prior independent coverage/custody, not empty root; gate remains closed |
| Incomplete coverage: alias/native fixture call, unobserved thread/child/callback, or outside study-access process | UNAVAILABLE for missing coverage; FAIL on observed escape | Exact route inventory, observer start and hardware-thread mapping; no release |
| Missing durability: valid signed promise without committed event/readback, or lost acknowledgment | UNAVAILABLE; after simulated boundary, hold | Storage/journal acknowledgment/inclusion and exact bytes; no continuation |
| Interrupted verifier: terminate after signature validation but before durable verdict | UNAVAILABLE | Durable complete V1/V2 bytes and receipt ordering; no partial PASS/release |
| Valid attestation/invalid boundary: witness signs an ordinary file or a boundary missing actual source/intent linkage | FAIL when falsely represented as observed correct boundary | Frozen boundary validation plus target/frame/readback observation; no release |
| Wrong event gate: stop at RNG implementation entry after Python callable invocation | FAIL | Native dispatch instruction/frame mapping and simulated invocation counter; stopping before returned bytes is insufficient |
| Split-certificate circularity: C1 promises future observation or DI claims future E1 receipt | UNAVAILABLE for unproved actual linkage; FAIL for fabricated/backdated event | Acyclic raw bindings, pre-marker V1 versus actual E1/V2; no release |
| Other submitter/equivocation: two journal heads or authenticated producer-initiated submission impersonating observer | FAIL on proven contradiction; otherwise UNAVAILABLE | Independently obtained key/source identity, head consistency and custody; no release |
| Crash cuts: before/after marker, intent, dispatch and raw audit with deterministic injected values | Frozen orphan-marker/interrupted-audit hold; no automatic retry | Original preserved bytes, exact initiated-call count and event coverage; no extra simulated sampling to repair missing evidence |

Qualification must separately establish P1–P5 for each supported route and prove
all negative cases fail closed under combined missing-proof/positive-mismatch
conditions. All PASS labels remain synthetic and cannot fill the actual historical
interval or authorize REAL acquisition. Native observer binaries, interpreter
mapping, environment controls and external trust need independent qualification
and manifest impact decisions before any reliance; none is frozen here.

## K. Seal and protocol-amendment impact

| Question | Assessment |
| --- | --- |
| Sealed source bytes changed by this task? | No. Only design/review and private administrative provenance may be added |
| Preferred candidate changes entropy API? | Intended no; original `os.urandom(8)` and later `(32)` remain. Native hooking, replacing functions/return values, or supplying external randomness is excluded |
| Number/order of calls? | Intended unchanged, including every rejection and one later salt. Observer/journal cryptography cannot silently add scientific calls |
| Frozen generator control flow? | No intended instruction/branch edit, but external suspension adds a supervisory pause/release condition not qualified by Seal 08; its impact cannot be waived by calling it external |
| Transcript / salt / marker recipe? | Intended unchanged; separately retain witness data, never rewrite boundary/audits/marker or regenerate salt |
| Authority transitions? | Intended no new event; T2 stays current. Any actual hold/drift invalidates this exact plan and requires frozen handling |
| New scientific input? | No intended sample/payoff input, but operative observer logic may become implementation and change I; claiming no gameplay input does not avoid manifests |
| Merely external operational attestation? | An externally retained observation alone could be. The preferred candidate additionally controls execution and checks runtime coverage, so it cannot presently be certified as merely supplying an already-permitted receipt |

No source modification has been demonstrated **necessary**; debugger feasibility
is insufficient to prove unchanged-instrument conformity. If source integration
were required, the precise candidate edit would be
`tools/research/v6/e9/v2/generation.py`, `Generator.draw_one.action`: introduce a
qualified callback after boundary/intent durable readback and **before** `source(8)`
to acquire/verify durable independent observation and reject without invoking the
source; pre-marker verification would remain a separate entry prerequisite.
That changes sealed control flow and function contract, requires new complete
implementation I, independent Q/reproduction, scope and seal; it still cannot
prove the missing historical interval. It is neither implemented nor recommended
as a routine repair for the consumed G. The old G binds old I/Q and cannot be
repurposed for that source change. A native controller added outside `v2/` likewise
cannot be excluded from complete I/Q manifests solely by its filename.

**A/B/C determination:** A is unsupported: no existing qualified complete timing
mechanism was found. The desired external attestation specification is **B in
intent**, filling an unspecified operational mechanism while preserving P1–P5.
The specific debugger/split-certificate procedure has **not established B
conformity** or unchanged B/G certification. It is not ready for scope review.
No normative change is proposed, so **C / REQUIRES PROTOCOL AMENDMENT is not
established**. Treating evidence of a prospective promise as occurred timing,
waiving historical P5 or moving required pre-marker verification to post-marker
would be C and requires formal amendment before implementation; those changes
are not accepted alternatives in this design.

Before a valid B procedure could acquire evidence: separately review exact
observer coverage and trust/retention material, decide full source/I/Q/B/G impact,
approve a procedural specification and bounded implementation/qualification scope,
independently qualify it, appoint accountable attestor/verifier, and separately
authorize actual acquisition. None of those gates is granted by this draft.

## L. Consumed-G compatibility

| Explicit question | Answer for this design |
| --- | --- |
| Can the procedure legitimately be established now? | A design may be drafted/reviewed now. A conforming operative procedure for the existing G is **not established**; current proof cannot pass historical coverage and boundary/Phase-A linkage |
| New authority event required? | Not to draft/review, nor inherently to supply a conforming future attestation. Observer/verifier appointment and operational authorization would be separate decisions; no authority event is issued here |
| Does it change T2? | No; design preserves T2. A future formal event would change the tip and require reassessment, never a fictitious assertion of unchanged T2 |
| Does it require changing G? | No G edit or replacement is proposed. If operative logic changes I/Q or certified inputs, this G cannot cover it; preserve G and seek disposition |
| New producer registration? | No. Exact existing producer/root/recorder must remain; debugger custody is not a substitute producer |
| First-raw marker recipe? | No intended change; neither marker nor retained copy is created |
| Can it operate without rewriting old evidence? | A successful external attestation could append forward. This candidate cannot currently operate conformingly; it cannot fill old observation gaps by rewriting them |
| Would implementation invalidate an existing G binding? | Mere completion of the already-declared conforming input would not inherently do so. New execution-control/verifier source or certified operational/input changes may alter I/Q/B and invalidate use of this exact G. No compatibility PASS until the complete boundary is reviewed |

The consumed state is expected by `authority._check` for this original operation;
consumption alone did not close the prospective evidence window. This design's
failure does not establish that the window has closed or cancel the operation.
It establishes that the candidate **cannot presently prove conformance for the
existing consumed G**. No replacement G, second CONSUME, forced B rewrite or
automatic new study is proposed. Seal 08 remains accepted for its original bytes.

## M. Remaining lead decisions

Do not approve implementation of this candidate on the strength of signatures
or a synthetic gate demonstration. The unresolved matters are:

1. Determine whether independently authentic retained evidence can establish the
   historical P5 interval under the exact original authorized producer boundary.
   No such complete source is currently demonstrated. New observation can prove
   future custody only; a waiver would change the claim and require amendment.
2. Determine whether any unchanged-instrument mechanism can supply actual
   boundary timing while satisfying pre-marker Phase A, avoiding circular future
   receipts and preserving the immediate protected marker/boundary/intent order.
   A split prospective certificate/post-boundary event is not accepted as that proof.
3. Resolve observer confinement, complete runtime route/image coverage, actual
   verifier/attestor independence and external durable source availability; no
   provider, key or human is appointed by this document.
4. Decide complete implementation/qualification and B/G impact before scoping
   any execution controller. If changed I/Q is required, explicitly disposition
   the preserved consumed G; do not routinely replace it or transfer authority.

These are future disposition items, not a permission question or a scope freeze.

### Fresh adversarial design review

Completed by fresh context `/root/timing_design_reviewer` with
`fork_turns=none`, without inherited author conversation or an approval target.
The [independent report](V6_E9_OPERATIONAL_TIMING_PROCEDURE_DESIGN_REVIEW_01.md)
is retained unchanged: **22412 bytes**, raw SHA-256
`c5ac6ff5c75e99aa3befb2e56bd103b7b00a56dc9d4b8850501e0a2899ea8bb8`.
It reviewed the preserved initial draft: **51455 bytes**, raw SHA-256
`4b53bea08d5cf78b4a3094782bf124aed4dba7ad2c1a5196c4f5bf546047eec3`.
This final document corrects source anchors and records the review disposition;
it does not represent its later bytes as the initial reviewed input.

The commission asked:
**“Can a conforming implementation of this design independently demonstrate that
this study's first raw invocation cannot precede its valid, durably established
timing evidence?”** It must identify uncovered paths, circular trust, historical
P5 gaps, pre-marker/post-boundary timing conflicts, and I/Q/B/G impacts; reproduce
exact source/contract inputs and preserve findings/provenance. A fresh AI context
is an independent design inspection, not a trustworthy event observer, human
witness, appointed operational verifier or timing PASS.

**Review answer: no demonstrated conforming implementation; NOT OPERATIONALLY
PROVABLE for this candidate/current evidence.** All findings are preserved:

| Finding | Severity / disposition |
| --- | --- |
| TD-R01 historical P5 | BLOCKER; independently authentic complete historical coverage is absent. The lower acquisition bound must include relevant unauthorized study-input routes, not assume authorization alone prevented them |
| TD-R02 actual source gate | HIGH; native pre-invocation mapping is unqualified, although a controlled prospective debugger gate is technically plausible |
| TD-R03 complete acquisition custody | HIGH; aliases/callbacks/threads/other processes and privileged study access are unconfined/unobserved |
| TD-R04 pre-marker evidence semantics | HIGH; credible linkage to forthcoming boundary is unestablished. A split certificate plus later corroboration is not inherently prohibited or necessarily an amendment |
| TD-R05 witness trust/durability/comparability | HIGH; no complete source/service contract or independently appointed supplier demonstrated |
| TD-R06 paused lock / observer exit | MEDIUM; stopped target retains exclusive lock; re-entering protected/exclusive verification would fail or deadlock, and formal HOLD cannot use the occupied lock |
| TD-R07 I/Q/B/G compatibility | HIGH; no complete-source/operational impact decision establishes this consumed G covers the execution controller |
| TD-R08 anchors / tooling | MEDIUM; source anchors corrected above. Debuggers not found on PATH; API availability does not demonstrate deployed observer/service feasibility |

**Controlling post-review clarifications:** pre-marker verification need not
pretend a future boundary already occurred. Independently authentic prospective
causal evidence with a qualified enforceable link and later corroboration could
preserve the frozen duties. This draft has not supplied that link; the negative
finding is not a general impossibility theorem or a necessary-amendment decision.
The proposed binding chain in section G is acyclic; the unresolved issue is authenticity/event
meaning, rather than an intrinsic hash cycle. Only embedding a receipt hashing
its own final boundary would create that cycle.

A later feasibility specification must verify the stopped state independently
and read-only without re-entering the target's held authority lock or asking a
stopped recorder callback to run. Any required formal HOLD/lock recovery needs
separately authorized frozen handling; this design grants no lock clearance or
event authority. It must bind the observer's exit policy, prohibit unsafe detach/
automatic continuation, and preserve killed/crashed target artifacts without
redraw. Windows documents default termination of attached targets on debugger
exit; changing that behavior requires explicit review and cannot be assumed safe.
[Microsoft DebugSetProcessKillOnExit](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-debugsetprocesskillonexit)
Synthetic qualification would need paused-lock recheck/deadlock, debugger death,
unsafe-detach and uncovered thread/child cases in addition to J. None was run.

The review independently matched three inspected source files against I and
the adopted contract raw pins, G/Disposition 09, and a stated present authority/
producer subset. It did **not** claim independent full 329/1607/1362 reproduction.
Those counts are the root's fresh audits. The report preserves exact input hash
identities, eight findings and shared-model/environment limits. The initial
reviewed draft, commission and exact report copy are retained privately as
administrative design provenance, not operational timing evidence.

## N. Proposed bounded implementation/qualification scope

**No implementation scope is frozen or authorized.** The proposed boundary for
a later feasibility decision is a separately isolated Windows native observation
controller, exact-runtime pre-call mapping, private context/evidence binding and
external durable witness verification, plus the independent SYNTHETIC adversarial
qualification in J. It excludes edits to frozen P/I/Q/O/V/A/R/B/G, authority
events, producer changes, actual-study marker/entropy/salt/package/W, native
matches, payoff analysis, publication, commits and pushes. No controller/service
code, new source/test file, operational receipt or synthetic test run is created
here. Any operative source/test manifest change must receive separate scope,
identity and qualification treatment before it can be relied on.

The first proposed feasibility boundary is documentary resolution of historical
coverage and actual-boundary/pre-marker conformity; do not implement the
controller merely to defer those obligations. If either cannot be established,
keep **NOT OPERATIONALLY PROVABLE**, preserve the consumed G and return for
disposition. A protocol change, if later explicitly proposed, is a distinct
amendment decision and does not retroactively cure missing event evidence.

### Completion preservation read-back

Final entropy-denied read-only audit passed: **329/329 Seal-08**, **1607/1607
preservation**, **1362/1362 inherited private** and **1374/1374 complete original
private entry files** unchanged. It also rehashed **1638/1638 readable public
entry files** and the separate local-only settings receipt. The exact original
private census has no additions outside this task's new administrative design
directory. All newly retained material is design authorization, input copies,
review commission/report, audit procedures/results and completion provenance.
No sealed or prior evidentiary bytes were amended.

Original P-through-G identities and dependencies reproduced; authority remains
exactly B ISSUE → G ISSUE → single original CONSUME, sequence 3, T2. Original
producer is registered and empty; marker and copy, boundary, raw transcript,
salt, package and W are absent. This audit's REAL research entropy calls and
attempts are **0/0**; generation was not imported and Generator/AuthorityLog were
not constructed. Branch/HEAD/upstream remain the entry values, ahead/behind 0/0,
with empty tracked/index diffs. Initial reviewed input and reviewer report raw
hashes remain exact. Administrative hash receipts do not qualify operational
timing or independently prove unobserved historical activity.

Only the two new public design/review documents and private administrative
provenance were added. No source/tests, operational timing evidence, marker,
entropy, salt, authority transition, G change/CONSUME, generation, W, commit or
push was created. **STOP: NOT OPERATIONALLY PROVABLE; execution LOCKED;
Requirement C NOT ESTABLISHED.**

Tests/mypy/ruff are not applicable to this documentation-only authorized task;
running instrument qualification is expressly outside its boundary.
