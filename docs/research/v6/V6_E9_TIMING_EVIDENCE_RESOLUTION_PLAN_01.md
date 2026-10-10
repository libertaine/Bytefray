# Bytefray V6 E9 — Timing Evidence Resolution Plan 01

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**Planning artifact only. Classification B: missing operational procedure.**
Recommend authorizing drafting of a bounded operational timing procedure.
No concrete timing mechanism has yet been established as conforming. No timing
qualification, operational attestation, new implementation scope or execution
authorization is created by this plan. Disposition 09 remains unchanged.

## A. Baseline and integrity

Fresh read-only verification used exact retained bytes, strict duplicate-key JSON
reading, raw SHA-256 and the frozen canonical digest recipes. It did not import
the generation instrument, construct Generator, register a producer, enter an
authority lock/protected action or execute a match. Research entropy APIs
`os.urandom` and `os.getrandom` were denied/counting before audit imports.

| Boundary | Verified result |
| --- | --- |
| Branch / HEAD | `v6-research` / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Upstream / live remote | `origin/v6-research`, same HEAD; ahead/behind 0/0 |
| Tracked working tree / index | Empty diffs; inherited untracked work retained |
| Seal 08 | **329/329 unchanged**: 293 implementation and 36 qualification files |
| Preservation | **1607/1607 unchanged**, against retained AR/B preservation map |
| Inherited private evidence | **1362/1362 unchanged**, against original multi-draw entry map |
| Complete current private census | **1374/1374 unchanged**, including prior administrative additions |
| Prior public evidence | **431/431 unchanged**, against last baseline plus final additions |
| P/I/Q/O/V/A/R/B/G | Original raw hashes and canonical identities reproduced; I uses its explicit P/source recipe |
| G | Original `v6-e9-generation-authorization-v2-0ea6d2043fbd`, consumed exactly once |
| Authority | Three events: B ISSUE, G ISSUE, original CONSUME; active tip T2, sequence 3 |
| Producer | Original single registry/recorder/root; root exists with zero entries |
| First-raw marker / retained marker copy | ABSENT / ABSENT |
| Boundary / raw transcript / salt / package / W | ABSENT / ABSENT / ABSENT / ABSENT / ABSENT |
| This investigation's REAL/attempted research entropy calls | **0 / 0** |
| Timing qualification / execution / Requirement C | UNAVAILABLE / LOCKED / NOT ESTABLISHED |

Original G raw SHA-256:
`21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8`.
Original CONSUME raw SHA-256:
`6c1b60409a9ff29553821774418c5020eb3d6e10742cf1d17c49455b94e046e3`.
T2 full body digest:
`765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485`.
Disposition 09 raw SHA-256:
`53261258982fb2c962f0176cda7a0368ed87c50a03ab8b9e7c472c675e2764b5`.

Administrative census checksums, SHA-256 over canonical path-keyed receipt maps:
private `dc57c55f3a152edb36b0ace2bc5421b8fef7012bf8cb54e1445e2e72f54bd5ae`;
prior public `94f36a78216bee2673e4a9cb12b7054bff90d02aaa6b9d368a2648db84e86072`.
Private maps and scientific values are not reproduced here. These checksums
identify integrity checks, not independently trusted time or historical coverage.

The sandbox could not launch the repository interpreter. Authorized elevated
read-only execution succeeded. An initial audit assumption incorrectly applied
the generic body digest to I; it stopped before any mutation. The audit was
corrected to the frozen I-specific recipe in `records.py:435–440` and passed.
This was an audit error, not a mismatch in I. No automatic approval rejection
occurred. No tests, new qualification or scientific reproduction were conducted.

Evidence anchors: [Seal 08](../../../tools/research/v6/e9/v2_final_manifest_seal_08.json),
[instrument I](../../../tools/research/v6/e9/v2_instrument_identity_08.json),
[Disposition 09](../../../tools/research/v6/e9/v2_finding_disposition_09.json),
and [prior generation return, sections E and M](V6_E9_MULTI_DRAW_GENERATION_RETURN_02.md).
Entry and completion read-backs reproduce the same counts and census checksums.

## B. Exact frozen timing requirement

### Governing sources and status

The authoritative P is
[the adopted envelope](../../../tools/research/v6/e9/protocol_freeze_v2_adopted_02.json),
`v6-e9-prereg-v2-539a60806eab`, body digest
`539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0`,
raw SHA-256 `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4`.
Its separate [adoption attestation](../../../tools/research/v6/e9/protocol_adoption_attestation_v2_02.json)
adopts the exact reviewed package. The word PROPOSED in the pinned contract
filenames does not make their adopted contents optional.

| Authoritative clause | Exact requirement or relevant effect |
| --- | --- |
| [Rule text](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md):100, PG-R3; [machine contract](../../../tools/research/v6/e9/amended_rule_contract_v2_proposed_02.json), `normative_rules[id=PG-R3].text` | “Before the first experimental raw draw, the complete pre-generation state SHALL be independently verified and separately authorized.” Absent/stale/revoked/mixed bindings reject operations. |
| Rule text:102, PG-R4; machine contract, `normative_rules[id=PG-R4].text` | “The declared generation boundary SHALL be the durably recorded instant immediately before the first experimental raw draw, after the active inventory gate is sealed and verified.” Historical use must be strictly before that boundary; later first use and rejected candidates are different categories. |
| [Frozen catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json), `records.GenerationBoundary` | Authorized recorder; dependencies are existing tuple through G; required `durable_instant` is “trustworthy pre-first-raw-draw evidence”; required operation, active authority digest and monotonic producer fence epoch. Acceptance: “Durable write and verified inventory/authority before first raw draw; uncertain ordering is a hold.” |
| [Original G](../../../tools/research/v6/e9/v2_generation_authorization_study_01.json), `body.boundary_procedure` | “Independently verifiable trustworthy pre-first-raw-draw instant evidence is mandatory; absent or ambiguous temporal/ordering evidence prevents the first draw and requires lead disposition.” |
| Original G, same field, following sentences | Verify exact active tuple/K/E/L/sources/operation and unheld/unrevoked chain. Retain original registered recorder/root and durable single CONSUME. Inside exclusive protected action bind current tip/fence, durably write/read back marker and REAL source declaration, canonical boundary with trustworthy instant and original producer/marker evidence, then first intent before `os.urandom(8)`. Uncertain boundary/interruption/order stops without redraw, replacement or backdating. |
| Catalogue, `common.independence` | “Qualifier and each independent verifier must be identified and independent of production of the implementation or evidence they verify; read and reproduce exact bound inputs, not endorse the producing agent receipt.” |
| Catalogue, `encoding`, `common.hash_rules`, `types.Actor`, `types.ArtifactRef`, `types.RecordRef`; rule text:353–363 | Canonical UTF-8, exact body/raw digests, complete earlier bindings, identifiable scoped Actor and authority evidence; private ArtifactRefs use opaque IDs and separately resolved exact bytes. Full hashes control equality. These supply byte integrity and authority binding, not independent temporal authenticity. |
| Rule text:228–240, sufficient overlap evidence; PG-R7 at:108; machine contract, `overlap_contract.adjudication` | Actual in-scope execution, equality and trustworthy strict pre-boundary order are separate proofs. Uncertain/simultaneous ordering remains suspected; missing evidence cannot establish non-overlap. Integrity adjudicator must be independent and blinded to E9 payoffs. |
| Rule text:138–149, R8–R10; catalogue, `records.G.acceptance_predicates`; rule text:387–392 | G binds B and declared future procedure. Single durable consumption permits only this operation. Binding drift, holds and revocation reject action; append-only authority/fencing history and original records remain retained. |
| [Disposition 09 JSON](../../../tools/research/v6/e9/v2_finding_disposition_09.json), `rulings.timing`, `rulings.scope`, `remaining_blocker`; privately retained lead ruling section 3 and Phase A | Later binding lead direction preserves the requirement and requires timing qualification before marker creation or any REAL entropy. AI endorsement of local time is insufficient. No backdating, replacement G or rewriting B/history. PASS requires actual trustworthy evidence and independent verification; absence remains UNAVAILABLE. This is operational direction, not a change to P. |

The event requiring proof is the **actual durable first-generation boundary** of
this original operation, immediately before its first raw source invocation.
It is not ISSUE, CONSUME, a report creation date or a salt event. Required order is
verified inventory/authority and consumed original operation → qualifying
pre-entropy evidence/verification → protected durable boundary and first intent
→ first raw invocation. The future boundary must not be moved backwards to a
receipt collected hours earlier.

The clauses require a trustworthy recorded instant and strict event ordering.
They do **not** mandate UTC, a calendar epoch, numerical clock precision or a
particular clock technology. Pure local ordering of retained events is too weak
to meet G's trust/independence requirement. A trustworthy independent ordering
channel could potentially satisfy the temporal purpose if it ties actual
generation and relevant historical execution into a comparable timeline; this
is a conformity question for the proposed procedure, not an accepted mechanism.
Absolute time is one possible way of supplying that timeline, not an expressly
prescribed scientific field. A nominal UTC string proves neither requirement.

No reviewed frozen clause specifies a timing provider, signing key/trust root,
token format, error bound, freshness limit, independent observation channel or
complete acquisition/verification procedure. No timing-specific signature is
mandated; **authenticity and trust must nevertheless be established**, not assumed
from a digest or Actor label. Retain exact proof bytes and their validation/trust
material privately, bind them through the existing field and tuple, and preserve
the authority history. No separate timing-evidence schema or dedicated verifier
Actor ID is prescribed by P/G.

### Implementation and interpretation are distinct

[Sealed generation.py](../../../tools/research/v6/e9/v2/generation.py):164–213
receives caller-supplied `durable_instant`, serializes it into the boundary, then
calls the source in the same protected action. It acquires/authenticates no time.
[records.py](../../../tools/research/v6/e9/v2/records.py):366–372 accepts generic
non-null JSON for this field; structure validation is not a trust check.
`generation.py:82–108` checks original tuple/marker/producer/source declaration,
not the independent authority of the timing input.
[private_verification.py](../../../tools/research/v6/e9/v2/private_verification.py):254–329
checks producer, marker and REAL declaration; it supplies no independent clock.

Synthetic tests use fixture ArtifactRefs such as `artifact(b"boundary", "boundary")`
([independent generation test](../../../engine/tests/test_v6_e9_v2_independent_generation.py):70).
Seal-08 PASS does not convert these fixtures into REAL timing attestations.
The last return and retained fresh-context timing review are later assessments;
their conclusions are corroboration, not additional frozen timing clauses.
No E9 acquisition procedure was found in `docs/specs/`.

## C. Required temporal claims

| Distinct claim | Required? | Existing support and limits |
| --- | --- | --- |
| 1. G ISSUE preceded CONSUME | Yes, as valid authority ordering; no separate trusted wall-clock time for ISSUE is prescribed. | Canonical event 2 is G ISSUE; event 3 CONSUME names event 2 as predecessor and binds original G/producer. Supports protocol log order, not independently attested physical event times. |
| 2. CONSUME preceded first raw | Yes. Protected raw draw requires original G already consumed by this exact operation (`authority.py:752–755`). | CONSUME exists; first raw has not been entered in retained workflow. Sealed checks require the order prospectively. There is no actual first-raw event to compare yet. |
| 3. Qualifying evidence and required verification preceded first raw | Yes; Disposition 09 additionally puts Phase A before marker creation. | Not satisfied: evidence and verification PASS are absent. Existing review establishes UNAVAILABLE only. |
| 4. The claimed boundary occurred at a trustworthy absolute time | A trustworthy instant is required; absolute UTC/calendar time is not expressly mandated. If a procedure relies on absolute time, its source, uncertainty and event linkage must be trusted. | No boundary occurred and no trusted absolute-time receipt exists. Administrative timestamps are local assertions. |
| 5. No raw draw preceded establishment of timing evidence | Yes, for this study's original generation operation; otherwise its purported boundary is not the first draw. | Retained guarded harnesses report zero; original producer is empty, both marker forms absent, private census exact, no intents/audits/salt/package. Useful bounded evidence under the sealed producer model, not independent proof against unrecorded or out-of-band calls. No trusted external observer attests the entire historical interval. |

The proof ultimately needed is an independently checkable connection between
the trustworthy instant/order evidence and the **first** durable boundary for
the original G/producer/operation, with no earlier raw invocation, and evidence
established/verified before that invocation. Separately prove log ordering,
evidence acquisition, durable boundary ordering and actual source invocation.
Neither a local hash chain nor a timestamp token alone establishes all four.

## D. Existing evidence assessment

Examined retained authority events/active state, producer registry and retained
copy, prior pre-consumption snapshots, first/multi-draw guarded procedures and
readbacks, Phase-A timing analysis/review, file censuses and filesystem metadata.
Private paths and maps remain private. The relevant review identities are the
ones preserved by Disposition 09; no new operational evidence was acquired.

| Source | Classification for independent temporal proof | What it establishes |
| --- | --- | --- |
| T0: B authority ISSUE, event 1 | Locally asserted evidence; useful corroboration | Digest `f0da08f5ce538d3a56ddab2c06495a19bccab0f37f8df6e63b6b3897fcbbc986`; sequence 1 from genesis; accepted B authority. T0 is a state digest, not clock time. |
| T1: G ISSUE, event 2 | Useful corroboration; insufficient alone | Digest `50fe7d74d8a97be1ef5f08f01d93469193c48afffff306e4e351e827cf7616d0`; predecessor T0; original G issued before recorded CONSUME. |
| T2: original CONSUME, event 3 | Useful corroboration; insufficient alone | Exact original operation/producer and predecessor T1; no later event, hold/release/revocation or terminal transition. |
| Event logs / durable active recorder state | Locally asserted evidence with reproducible byte integrity | Exactly three canonical events; event bodies have sequence/prior digest/Actor/evidence, no trusted clock field. `active.json` records only sequence/tip. No independently anchored external log head or observer receipt. |
| Original registered producer and empty root | Useful corroboration | Same recorder, G, original tuple and root; registry raw hash `d0349b6938407587cac73d14c09507e52017543324ff65965abbf084be39e548`. Actual emptiness and absent marker/copy support unstarted sealed generation; neither authenticates historical wall-clock time. |
| Retained guarded process/harness evidence | Useful corroboration; locally asserted historical accounting | Prior procedures deny/count entropy; retained returns report zero attempts/calls. Current investigation also recorded zero attempts. No external syscall audit or signed process observation covering the historical interval is retained. |
| Prior fresh-context AI timing review | Independent inspection within disclosed context limits; insufficient attestation | It reads bound inputs and correctly distinguishes unavailable proof. It observed no actual first boundary and supplied no external temporal trust source. |
| Filesystem creation/modification times | Available; insufficient | Metadata is readable but mutable/local, unauthenticated and not bound to actual entropy invocation. Values are not promoted into proof. |
| System clock, ordinary OS logs, Git/session dates, unsourced messages | Locally asserted or insufficient; operation-bound trusted audit channel unavailable | No retained, authenticated OS audit channel ties these to this operation's first entropy call. A generic system event or Git date would not do so. No broad machine-log export was collected. |
| External timestamp, signed audit/witness receipt and external verification material | UNAVAILABLE | Prior analysis expressly retains `qualifying_evidence=ABSENT` and `external_verification_material=ABSENT`. No designated trust root/provider/channel or qualifying artifact is present in examined evidence. No conventional `.tsr/.tst/.p7s/.pem/.crt/.cer` files were found in the 1374-file census; extension absence alone is not the basis for the finding. |

**No inspected source qualifies as independently trustworthy boundary timing
evidence.** Exact rehashing proves retained bytes and finite census identity,
not historical completeness or absence of an unlogged request. “Zero REAL calls”
is the preserved research workflow accounting plus this investigation's guarded
count; it is not a claim about interpreter/OS internal entropy or an independently
attested global machine history. The existing gap ledger and unknown H remain
unchanged and are not resolved by this investigation.

## E. Open/closed evidence windows

| Window | Frozen requirement | Current status |
| --- | --- | --- |
| Before G ISSUE | Valid B and declared future boundary procedure | Closed; original evidence retained. No clause requires the actual future boundary instant/receipt to exist before ISSUE. A token made now cannot attest historical ISSUE time. |
| Before CONSUME | Original registered producer and valid single consumption prerequisites | Closed; exact registry and CONSUME retained. No clause puts first-boundary timing acquisition here. New evidence cannot backdate this interval. |
| After CONSUME, before marker / first raw | Establish legitimate timing procedure, qualifying evidence and independent Phase-A PASS before marker/entropy | Prospective window is **not shown closed** by any required ISSUE/CONSUME deadline. Remains open in the retained sealed-operation state; conformity and usability still unestablished. |
| Immediately before first raw inside protected action | Durably record actual boundary with trustworthy instant/current tip/fence/producer/marker/source, then durable first intent before invocation | Not entered. Can be reached only after pre-marker qualification; no supported pause for a human/network verifier inside existing `draw_one`. |
| After first raw | Verify retained actual sequence/package later | Cannot cure a missing pre-draw prerequisite. Later readback or timestamping is not retroactive Phase-A PASS. |

The prospective conclusion rests on all of: the exact unchanged G declaration
of a future boundary; no normative pre-ISSUE/pre-CONSUME timing deadline; exact
single original registry/consumption; unchanged source/evidence census; empty
root; absent marker/copy/boundary/intents; and retained guarded zero-call history.
It does not rest only on marker absence. It also does not establish independently
that hidden calls were impossible. A prospective witness cannot attest an earlier
interval it did not observe. Any proposed procedure must explicitly resolve the
bounded historical no-first-draw evidence under G's trust model; if the verifier
cannot establish that prerequisite, it must remain UNAVAILABLE.

Legitimate prospective acquisition would require separately approved procedure
and roles/trust source, fresh original-state verification, trustworthy evidence
with a defined link to the upcoming actual durable boundary, independent PASS
before marker/entropy, and preservation of continuous ordering/control up to
the frozen action. A stale preliminary receipt cannot be relabeled the actual
boundary. No new receipt is obtained under this plan.

## F. Candidate trusted mechanisms

These are designs for evaluation. **Available established conforming mechanisms:
none.** No provider has been selected or contacted for an operational receipt.
Independent signing proves authenticity only if the key and observation channel
are independently trusted. Proposed packaging uses existing `durable_instant`
JSON/ArtifactRef capability; it is not a new adopted schema.

| Candidate | Precise proof, binding and independent attestor | Repetition / residual trust | Can exist before first raw? Sealed implementation / protocol / approval |
| --- | --- | --- | --- |
| Independent cryptographically signed timestamp | Signature authenticates a statement about an exact prospective context digest. Trustworthy absolute time additionally needs a trusted signer clock. It does not by itself prove boundary occurrence or no earlier draw. Bind study/operation, exact tuple/G/CONSUME, registry, current tip/epoch and source manifests. | Retain exact signed bytes, signature/key provenance, policy and clock basis; another verifier can repeat signature/hash checks. Signer independence and observation remain assumptions. | Potentially yes; receipt can be caller input. Actual-boundary/freshness/order link still missing. No concrete accepted procedure; lead approval needed. A producer-generated signing key supplies no independent trust. |
| Trusted timestamp authority | A token binds the hash imprint and trusted token-creation time: proof of byte existence by that time. The TSA need not observe the program or entropy call. Same prospective context binding; requires separate actual-boundary/no-earlier-draw proof. | Preserve request/token, imprint algorithm, signer chain/trust policy, validity/revocation material and timeliness evidence. Repeat cryptographic verification. Clock/policy/CA/service remain trust assumptions. | Potentially yes, before `draw_one`. Timestamping the eventual full boundary after it is written cannot supply Phase-A PASS in this sealed synchronous path. Caller input may avoid source changes only if an approved procedure bridges this gap. No E9 acceptance of a particular TSA; lead approval needed. |
| Separately witnessed append-only event | An independent observer records the upcoming gate/context and directly observed program/recorder ordering. Can prove relative order and observed no-draw coverage; absolute time only if observer clock is trusted. A log of a producer's assertions proves only submitted-byte order. | Retain signed heads, event bytes, inclusion/consistency evidence, independent witness channel/identity and observation scope. Repeat log verification; trust observation completeness and protection against equivocation. | Potentially yes for pre-gate evidence. The design must account for actual boundary immediately before invocation without adding a pause/callback. Not a presently supported E9 independent source; separate approval required. |
| Signed external audit receipt | Attestor reports independently observed original state, bounded no-prior-draw basis and a controlled prospective handoff to the actual boundary. Bind context digest, observational scope, ordering and any time uncertainty. Only observed intervals/events can be attested. | Reverify signature, original observations, observer independence, custody and source/control continuity. A signature over an unsourced local assertion remains insufficient. | Potentially yes if full evidence/control is established before marker. No existing external receipt/channel; no assurance such observation is possible without implementation changes. Procedure and observer approval required. |
| Existing E9 AuthorityLog/producer records as independent timing source | Reproduces T0→T1→T2 and producer identity; no external time source or independent event observation. | Fully repeatable digest/readback checks, but local retained-chain trust remains. | Already present, but insufficient as sole timing mechanism. Cannot be authorized into trusted clock status by renaming it. A new external witness would be a new procedure candidate. |

Technical bounds for candidates, not additions to E9: RFC 3161 §§1, 2.1–2.4
defines signed hash-imprint/time tokens; §2.4.2 separates token time, accuracy
and token ordering. A TSA authenticates existence/time of bytes, not the
truth of statements inside them. Signature, imprint, policy, certificate and
timeliness validation are separate checks. [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161)
RFC 9162 §§1, 2.1 and 11.3 illustrates inclusion/consistency verification and
equivocation limits for externally operated append-only logs. It concerns
Certificate Transparency and is not itself an E9 audit-log protocol or an
arbitrary-data service accepted by E9. [RFC 9162](https://www.rfc-editor.org/rfc/rfc9162)
The conclusion about what these proofs cannot establish is this plan's inference
from their proof scope and the E9 event requirement.

Avoid circular binding: an external receipt cannot hash the final boundary
that embeds that same receipt. A proposed receipt could bind the earlier exact
context; the later canonical boundary would bind the retained receipt forward.
That establishes digest direction only. A separately justified observation/
ordering link must connect it to the actual boundary and source invocation.
No future boundary digest, timestamp token or attestation identity is invented.
Any client randomness required by a candidate is a separate acquisition issue;
it is not authorized as “other entropy” by this investigation or by the frozen
scientific draw/salt scope.

## G. Protocol conformity assessment

**B — Missing operational procedure**, rather than an established acquisition
method. This conclusion has contractual evidence beyond technical feasibility:

- PG-R3/PG-R4 and G fix the event, strict ordering, trust, independence and stop
  behavior; none names an acquisition service or signed evidence syntax.
- The catalogue deliberately carries `durable_instant` as evidence and the sealed
  function accepts it from the caller. It leaves semantic trust verification to
  the surrounding authorized workflow; the implementation supplies no clock.
- G explicitly declares a future boundary and later scope authorization; later
  timing evidence is not itself a required rewrite of earlier G/B bytes.
- Disposition 09 explicitly preserves the requirement and demands establishment
  of the precise procedure, independent verification and pre-entropy stop when
  unavailable. It grants no waiver and supplies no missing mechanism.

These facts justify drafting an operational procedure; **they do not demonstrate
that a satisfactory unchanged-instrument procedure exists**. The critical unresolved
design obligations are the actual-boundary linkage, pre-marker verification,
freshness/continuous order and historical no-earlier-draw proof. The field's
generic JSON acceptance must not be mistaken for substantive permission.

Classification A is unsupported: no concrete existing valid mechanism is defined
and demonstrated. C is not presently established: no necessary change to the
adopted requirements or sealed behavior has been demonstrated merely by the
underspecification. D is not established: no required deadline is shown missed,
and the operation remains unstarted in retained evidence. It remains possible
that drafting will expose a need for C or an unrecoverable evidentiary gap; that
would require a later disposition, not an assumed PASS now.

A procedure is conforming only if it fills acquisition/verification details
while preserving every required event/order/binding, and independently
establishes the proof before entering unchanged `draw_one`. Calling a remote
service, substituting a locally signed string, moving the boundary to token
issuance, trusting unexplained timestamps or accepting post-draw verification
as pre-entropy qualification does not qualify. If a pause, clock acquisition,
new callback, altered first-raw behavior, weakened temporal claim, schema change
or changed authority handling is essential, that exceeds procedural completion.
It requires separate source/scope/qualification review and, for changed normative
meaning or schema/authority rules, formal amendment review.

## H. Independent verification requirements

**Design only; not commissioned or conducted in this investigation.** A neutral
commission must identify an independently accountable verifier, exact scope and
all inputs, with no desired outcome. It must distinguish the temporal attestor
from the verifier who checks the attestor's evidence.

Provide privately: adopted P/package/attestation and original Draft-3 pins;
Seal-08 I/Q manifests and qualified evidence; original O/V/A/R/B/G, K/E/L and
limitations; T0/T1/T2 full bytes and active state; original producer appointment,
registry/copy/root; exact guarded zero-call procedures/snapshots/censuses;
proposed lead-approved timing procedure; exact candidate receipt/request/context
bytes and digests; independently sourced trust roots/key identity/policy;
clock/ordering uncertainty and freshness basis; certificate/revocation and log
proof material as applicable; observation/control provenance and no-first-draw
coverage; evidence retention/resolution map and prospective handoff criteria.
No seeds, salt or raw private path map belong in a public return.

| Outcome | Governing conditions |
| --- | --- |
| PASS | All frozen requirements plus separately approved procedure satisfied; exact original tuple/operation/producer and active unheld authority; complete source/evidence readback; authentic independent source and repeatable verification; correct context/digest; sufficient no-earlier-draw basis; qualifying evidence retained and verified before marker/entropy; trustworthy actual-boundary linkage and uninterrupted ordering established without changed sealed behavior. Every trust assumption is disclosed and accepted within scope. |
| Invalid evidence / FAIL | Present wrong/mixed digest/context/operation; invalid signature/untrusted key or contradicted source provenance; replay/stale receipt; unsupported claimed observation; actual early draw; altered source/binding; conflicting event order; retroactive attestation represented as pre-draw; present positive mismatch cannot be hidden by another missing input. |
| UNAVAILABLE | Missing/unreadable receipt or trust/clock/observation/retention material; no prescribed approved acquisition path; unverifiable no-first-draw interval; unresolved freshness/actual-boundary connection; missing means to satisfy pre-marker qualification. Absence is not an observed signature failure or evidence of non-overlap. |

The exact algorithm, success criteria, attestor identity and verifier provenance
must be retained so another independent verifier can reproduce the evaluation
from the same bytes without new entropy. Timing qualification is distinct from
later W and full package verification.

The sealed call has no supported pause after marker creation or boundary
write. Therefore a draft cannot promise to ask a human/network verifier for
the first time at that point, or require post-write independent approval before
entropy without explaining how unchanged control flow satisfies it. Pre-entropy
qualification must verify the evidence/procedure and its credible link to the
forthcoming boundary. Future observation can corroborate actual execution, but
cannot replace evidence required to exist before invocation. If this cannot be
established with the accepted path, retain UNAVAILABLE and seek disposition.

An AI context independent of producing the implementation/evidence can perform
readback, cryptographic/code/procedure review and verification of externally
trusted evidence, subject to identified provenance, disclosed same-model/shared-
environment limits and any separately required scoped Actor appointment. The
catalogue does not require a different model family or an independent human in
every verifier role. Alias IDs alone do not establish independence. This current
producing context cannot serve as the independent verifier of its own procedure.
No AI context acquires clock/event authority merely by being separate: historical
event occurrence, trusted time and absence of unobserved entropy requests need a
separate legitimate source/observation basis. Code review proves ordering of the
reviewed path, not that a historical process followed it.

## I. Seal/instrument/G implications

| Path / impact | Required handling |
| --- | --- |
| Current plan and authorization to draft | One lead decision authorizes drafting only. No write-once implementation scope, authority transition, new Q/seal or scientific action. |
| A conforming procedure using existing caller evidence and unchanged qualified behavior | Subsequent exact lead operational ruling and separately approved write-once procedure/scope; independently verify procedure and real evidence under specified roles before action. No automatic source/test/I change or new instrument seal solely for a new input receipt. Seal 08 remains applicable to its exact implementation boundary; it does not qualify the new external trust source. |
| New operational helper/verifier becomes implementation, even outside `v2/` | Assess complete implementation/qualification-source manifests, not filename or “administrative” label. New operative source changes I; changed tests/required coverage renew Q even if I is unchanged. Separate scope, fresh independent qualification and appropriate new seal are necessary before relying on changed behavior. No such change is authorized here. |
| New acquisition/verification procedure changes the certified operational boundary | R8 states operational/input changes invalidate B. Distinguish completion of G's declared future evidence input from changed certified preparation/assumptions. If new procedure contradicts B/G or changes their approved boundary, original consumed G cannot simply be reused; preserve it and obtain explicit disposition. No silent B amendment or replacement G. |
| Formal normative amendment or new P/source/I/Q | Rule text:366–375 and catalogue I/Q predicates require fresh review/adoption or qualification. Seal 08 remains immutable evidence for old P/I/Q, not qualification for changed P/I/Q. P changes I and roots; no evidence/authority transfer. `authority.py:420–471` pre-generation renewal refuses P/I/Q changes. Existing G binds old tuple and cannot authorize changed instrument/protocol; it remains retained, not repurposed. |

G consumption has not itself made G unusable for its original operation:
`authority.py:752–755` requires the already-consumed original G before raw draws;
`protected` at:789–807 validates that operation and does not consume it again.
**Future usability remains conditional, not established.** It requires an exact
conforming procedure/evidence, independent PASS and fresh unchanged-source/tuple/
authority checks. If an essential implementation change forces a new I/Q, even
an open first-raw window does not make this G cover the changed instrument.
No new seal or amendment is required to write this plan; neither is ruled out
for a later failed conformity review.

## J. Recommended resolution

**Exactly one recommended next authorized action: authorize drafting of a
bounded operational timing procedure.**

The draft must identify the exact independently trustworthy temporal claim,
attestor and trust/observation channel, repeatable verification, evidence format/
binding/retention, pre-marker acquisition and PASS ordering, actual-boundary
linkage, no-prior-draw basis, and whether the whole path preserves P/I/Q/B/G and
the sealed synchronous function. It must return an explicit conformity and
qualification-impact determination. It may not acquire a token/attestation,
create marker/raw/salt, freeze implementation scope or resume generation.

This recommendation is B, not permission to use any candidate in section F.
Protocol amendment is **not shown necessary yet**, and a conforming acquisition
mechanism has **not been established**. Seal 08 remains accepted and applicable
to its original boundary. Consumed G remains preserved and potentially usable
only for the original operation if that later procedure proves conformity.

## K. Decisions required from research lead

For the one next step, make one bounded drafting decision covering:

1. Authorize a timing-procedure draft only, preserving original study, operation,
   Seal 08, consumed G, T2 and Disposition 09; no acquisition or execution.
2. Require the draft to resolve independent event-order/trust and actual-boundary
   linkage, expressly distinguish absolute time from event order, and justify
   the bounded historical no-earlier-draw proof. No weak local-time substitute.
3. Require exact proposed attestor/verifier accountability and independence,
   trust provenance, uncertainty/freshness policy, private retention and neutral
   PASS/FAIL/UNAVAILABLE criteria. Do not appoint an operational Actor now.
4. Require a determination whether the proposal merely supplies the existing
   future evidence input or changes the certified B/G/source/qualification
   boundary. Any conflict must return for disposition; no automatic amendment,
   new seal, replacement G or implementation-scope freeze.

Provider selection, operational evidence acquisition, final procedure/scope
approval, operational verifier appointment and generation resumption are not
requested in this decision. They remain later gates after a reviewable draft.

| Final preserved state | Result |
| --- | --- |
| Seal 08 / Gate 7 / producer | ACCEPTED / ESTABLISHED / REGISTERED |
| G / authority | CONSUMED exactly once / original T2 |
| REAL research entropy calls / first-raw marker / raw transcript | 0 / ABSENT / ABSENT |
| Timing qualification | UNAVAILABLE |
| Salt / generation package / W | ABSENT / ABSENT / ABSENT |
| Execution / Requirement C | LOCKED / NOT ESTABLISHED |

Only this planning document was added. Q/O/V/A/R/B/G, prior dispositions/returns,
source/tests/seals, all private evidence and local-only settings remain unchanged.
No timing evidence for operational use, first-raw marker, entropy, salt, authority
event, producer registration, commit or push was created. Stop at this plan.
