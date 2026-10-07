# E9 amended rule contract v2 — proposed freeze review 01

**PROPOSED_NOT_FROZEN, 2026-10-03.** R0 `v6-e9-amendment-r0-v1-d1e1e0f89b83` accepts REV03 with D1=B,
D2=ACCEPT, D3=ACCEPT and D4=C-LIMITED. Draft 3 governs until separate amended-freeze authorization.
Execution is LOCKED. Historical coverage and Requirement C remain NOT ESTABLISHED.

This document, the [machine contract](../../../tools/research/v6/e9/amended_rule_contract_v2_proposed_01.json) and the
[normative typed record schemas](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_01.json) form the proposed complete amended contract.
The machine contract carries all inherited scientific/source pins and all 357 preserved gap IDs;
DEP-01–DEP-05 remain unresolved. No K/E/L version is adopted. The original 157-entry candidate is
unchanged and the private 163-entry proposal is unadopted.

## Accepted replacement and assurance

## 2. Proposed replacement requirement — not effective text

The following would replace the historical-completeness prerequisite in §7
and the corresponding prerequisite in the unlock sequence, if separately
accepted and frozen:

> After rule freeze and qualification, and before generation, seal and independently verify an explicit known-use
> exclusion inventory. It must include both complete E6/E8 revealed lists and
> every in-scope prior qualification match-seed value established by the
> approved evidence inventory, including supported defaults and derivations.
> Any conservative extra exclusions require provenance. Bind the exclusion
> list, evidence index, unresolved-history ledger and verification receipts
> by raw-byte digests.
>
> Preserve every historical coverage limitation. Record the entire project
> qualification history as NOT ESTABLISHED when it remains incomplete; do
> not relabel that state complete. Record verification of the finite known
> set separately from completeness of historical coverage.
>
> Generation requires an explicit research-lead acceptance of the weakened
> non-reuse claim and unresolved-history scope, the approved amended protocol,
> a newly qualified instrument, separately approved exclusion bytes and a
> separate generation authorization. The known-exclusion count or receipt
> alone authorizes none of these actions.
>
> Reject inventory members and previously accepted values. Keep the unsigned
> 64-bit domain, OS-CSPRNG source, eight-byte big-endian interpretation,
> accepted-draw order and fixed sample size of 1,412. Verify disjointness
> against the approved inventory privately. Claim prospective random
> collection, within-study uniqueness and non-reuse against verified known
> exclusions. Do not claim exhaustive historical non-reuse.

This text is a proposal for a new versioned research contract. It is not an
instruction to change `complete: false` to `true` in an existing record.
The retained 157-entry candidate and additive 163-entry proposal remain
unchanged and unapproved. Approval must identify exact private bytes, their
provenance and the independent verification evidence; selecting a count is
insufficient. Until that decision, write the accepted set as \(K\), with
cardinality \(k\), rather than treating 163 as the operative value.

The evidence inventory has a declared inspection boundary and a ledger of
uninspected or unavailable history. A custodian attests which retained sources
were included; that attestation must not imply those sources are an exhaustive
record of every historical execution. Each unresolved scope keeps its ID,
reason, recovery attempts, evidence and disposition.

## 3. Freshness, exposure and scientific interpretation

Under B, an eventual report would use this claim:

> E9 used prospectively collected OS-CSPRNG draws, unique within this study
> and verified disjoint from the approved known-use exclusion inventory.
> Complete prior qualification history was not established; reuse of an
> unrecorded historical match-seed value cannot be ruled out.

“Fresh random draws” would describe the collection procedure. It would not
mean that every resulting value had never appeared in earlier qualification.
Disjointness from the complete E6/E8 revealed lists remains an exact membership
obligation, as does disjointness from every approved known exclusion. No
history beyond that scope is inferred absent.

The prospective policy/comparator and decision rules remain fixed before
experimental draws or outcomes. Selectors still cannot access seeds,
identities, artifacts or hidden state. Paired seats/opponents, the fixed
rectangle, outcome-blind recovery, no optional stopping and no outcome-based
seed replacement retain their intended roles. Those controls do not prove
unrecorded historical non-reuse or erase earlier seed-specific tuning/exposure.
No numerical bound on tuning bias or scientific effect follows from a
seed-value collision bound.

An eventual positive finding under B must be identified as an amended-protocol
finding with this limitation. It cannot be certified as compliance with the
original Draft 3 freshness prerequisite. Requirement C eligibility requires
explicit acceptance of the claim-profile decision in §7; no automatic
promotion follows from a numerical label. No E9 payoff evidence exists in this proposal.

The quoted proposal's future-tense statements describe later operational adoption. Proposal
acceptance itself is now recorded by R0; its acceptance does not satisfy any operational gate.

## Exact accepted PG rules

> **PG-R1:** The amended rule contract SHALL freeze the claim profile, approval roles and required record schemas, scientific predicates, historical-overlap rules and interpretation. Its digest SHALL NOT include later inventory versions, operational approvals, risk-acceptance instances or authorizations. Each later record SHALL bind its earlier inputs; no earlier digest SHALL depend on a later record that depends on it.

> **PG-R2:** Protocol freeze SHALL precede implementation and independent qualification. Any separately authorized match-producing qualification SHALL finish before the inventory gate seals. The custodian SHALL incorporate all known in-scope values, preserve unresolved scope and supply exact inventory, evidence-index and ledger bytes for independent verification. The research lead SHALL separately approve those bytes and a versioned, specific acceptance of unquantified residual-history risk, each bound to the frozen protocol and qualified instrument.

> **PG-R3:** Before the first experimental raw draw, the complete pre-generation state SHALL be independently verified and separately authorized. Generation and experimental commitment publication SHALL each require explicit scope authorization. The privately verified generated payload and commitment SHALL precede separate payoff authorization. Each consuming operation SHALL reject absent, stale, revoked or mixed bindings; prior qualification PASS and proposal review SHALL confer no execution authority.

> **PG-R4:** The declared generation boundary SHALL be the durably recorded instant immediately before the first experimental raw draw, after the active inventory gate is sealed and verified. Historical overlap SHALL mean independently verified equality between an accepted experimental position in this study and an in-scope match-seed value actually used before that boundary, discovered later. Planned reuse across E9 cells SHALL NOT be historical overlap. A first use after the boundary SHALL NOT become prior history. Rejected raw candidates SHALL NOT be accepted experimental positions.

> **PG-R5:** Proven overlap before the first cell starts SHALL terminate the study as CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP, with result NOT PRODUCED. During partial generation this applies to already accepted positions. No further draws, salt creation, experimental commitment publication or dispatch SHALL occur. Existing commitments and records SHALL remain immutable; any public communication SHALL be an integrity cancellation notice. There SHALL be no automatic redraw, replacement, restart, position deletion or change of N.

> **PG-R6:** Once the first cell starts, proven historical overlap SHALL make the full registered result NOT EVALUABLE under historical integrity, regardless of numerical classification or which cell uses the affected position. Dispatch, retries, experimental finalization and result promotion SHALL stop; running workers SHALL be stopped or fenced with evidence, and any subsequent artifacts retained. After final publication an append-only invalidation/correction SHALL bind the immutable original record and withdraw its Requirement C and payoff-promotion eligibility without overwriting it.

> **PG-R7:** Suspected but unverified overlap SHALL place the study on INTEGRITY_HOLD_PENDING_ADJUDICATION and stop new draws, experimental publications, dispatch, retries and promotion. A verifier blinded to E9 payoffs SHALL adjudicate from private identity, accepted-position, historical execution and temporal evidence. Missing evidence SHALL NOT be treated as non-overlap. Resume SHALL require an independently verified disposition and a fresh lead release record bound to the retained history of the hold, subject to PG-R8 partial-generation conditions when new history is involved. If adjudication is unresolved at the lead decision to close the study, it SHALL terminate as CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY before the first cell starts or NOT EVALUABLE once the first cell has started, including closure during incomplete collection; it SHALL NOT promote a registered payoff result.

> **PG-R8:** Newly discovered verified pre-boundary history SHALL extend an append-only disclosure ledger and an independently verified membership supplement. During partial generation, draws SHALL stop while that history is checked. The supplement SHALL bind only existing records: study ID; P/I/Q and O/V/A/R/B/G digests; declared generation-boundary receipt; producer-stop/fencing evidence; prior authority-chain tip; exact retained raw-draw/rejection audit tip; and a sealed raw-byte snapshot of the accepted ordered prefix with its count and acceptance/audit position. It SHALL bind the new historical evidence and independent scope, prior-use, equality and original-K membership receipt. It SHALL NOT require a future S, c, W, U or C record. Prefix disjointness SHALL NOT establish disjointness of the future completed list. Prefix overlap SHALL trigger PG-R5. With a verified disjoint prefix, generation MAY resume only if every newly evidenced prior-use value is independently verified already present in original unchanged approved K, all original bindings and the same paused generation operation remain valid, and a separate lead continuation/release record binds the supplement and still-incomplete scope before any further draw. Remaining draws SHALL retain original K and duplicate rejection against the retained prefix and every subsequently accepted value, uint64 OS-CSPRNG procedure, accepted order and N; the unchanged known-value check already rejects all newly evidenced values. No accepted position SHALL be replaced. Final private verification SHALL independently recheck the completed list against original K and the supplemented prior-use evidence plus the complete supplement/continuation chain; the prefix receipt SHALL NOT substitute for that verification. Any verified newly evidenced prior-use value outside K SHALL terminate the study as CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K, result NOT PRODUCED, even with zero prefix overlap. Unverifiable original bindings or prefix/audit integrity SHALL remain on PG-R7 hold and terminate as CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY if closed before the first cell starts. No remaining draws, salt creation or experimental commitment SHALL follow terminal cancellation. Retain all prefix/audit/evidence/approval bytes and append terminal revocation making G and any unused U/D unusable; any publication SHALL be an integrity notice. A new study requires PG-R10, not an automatic restart. When a completed immutable payload or commitment exists, a no-overlap supplement SHALL bind the exact existing S/c/W/U/C records applicable at that stage, with separate lead continuation before resumed publication or dispatch. Original K/E/L and any existing payload/commitment bytes SHALL remain immutable; no different K SHALL be reapproved for the same generated study or substitute commitment resealed. Historical coverage SHALL remain NOT ESTABLISHED. Later generation receipts and private verification SHALL bind preceding supplements/continuations forward without placing them inside earlier digests.

> **PG-R9:** Under the recommended C-LIMITED profile, a valid amended-protocol result in registered priority row 7 SHALL establish Requirement C only in the registered bounded scope, with a permanent statement that complete historical non-reuse is NOT ESTABLISHED. All other registered rows, historical integrity failures and precollection cancellations SHALL leave Requirement C NOT ESTABLISHED. Primary classification and Requirement C eligibility SHALL be separate fields. Historical integrity SHALL take precedence. The narrowed assurance and this eligibility rule SHALL require explicit substantive amendment acceptance; drafting SHALL NOT make them effective.

> **PG-R10:** A new study after cancellation or invalidation SHALL require a new prospective study identity, outcome-independent lead design decision, a verified and newly approved inventory including all known prior values and the retired study accepted list as conservative exclusions, fresh risk acceptance, and separate generation, publication and payoff authorizations. The old study SHALL never resume under the new identity. Rules or source changes SHALL trigger the freeze or qualification duties below. Prior observations SHALL NOT select replacement values, reduce the rectangle or tune thresholds.

## Approval, invalidation and identity tables

## 5. Acyclic identity and approval contract — proposed

Only the rule contract is frozen first. Approval *requirements* and their
schemas belong in P; the actual K/E/L bytes and lead decisions belong in later
versioned operational records. None of these proposed records is created here.
P excludes later operational instances; I binds P and exact implementation
sources. Q binds the independently qualified I. R0 binds the proposal rather
than an as-yet nonexistent freeze. Body digests exclude their own digest fields;
raw-byte digests are used for evidence files. Versioned records SHALL use the
frozen canonical encoding and declared body/raw digest distinction.

The required order is: rule freeze; complete independent instrument
qualification; separately authorized match-producing qualification if any;
inventory/evidence/ledger seal and independent verification; exact operational
approval and specific risk acceptance; artifact binding and complete
pre-generation verification; separate generation and publication authorization;
private generated-commitment verification; separate payoff authorization.

| Record | Inputs | Digest dependencies | Approval authority | Invalidation |
| --- | --- | --- | --- | --- |
| R0 Amendment decision | Exact REV03 human/machine bytes, parent digests; A or B; claim-profile choice | REV03 digests and original Draft 3/freeze only | Research lead; not recorded by drafting | Revised proposed rules need a fresh decision; rejection retains Draft 3 |
| R1 Rule freeze P | Accepted rule text, claim profile, roles, predicates, overlap/interpretation contracts and frozen scientific pins | R0, parent freeze, rule/source specification pins; excludes all later operational instances | Research lead freezes version; recorder verifies digest | Any normative rule, claim-profile, identity rule, threshold, scope or interpretation change requires new P |
| R2 Qualified instrument Q / identity I | P and exact complete implementation/test source manifests; independent synthetic evidence | I = digest(P, implementation source manifest); Q binds P, I and qualification evidence | Independent qualifier verifies; lead accepts qualification boundary | P, implementation/qualification-source drift or changed required coverage needs new qualification; v1 PASS is context only |
| R3 Match-producing qualification receipt T | Separately authorized matches, input/attempt/artifact evidence, all consumed in-scope seeds | P, I, Q and that qualification authorization; excludes inventory approval | Lead separately authorizes matches; independent verifier checks evidence | New or changed execution/input evidence invalidates downstream inventory closure; absent authorization prohibits matches |
| R4 Sealed operational inventory O | Exact K bytes, E6/E8 membership, known-use provenance including T, evidence index E, unresolved ledger L, declared inspection/coverage boundary | P, I, Q, T when applicable; raw digests of K/E/L and custodian attestation | Custodian seals; independent verifier V checks finite membership/derivations/bindings; not completeness | Any K/E/L/provenance/coverage-boundary change or intervening qualification reopens O/V, even if K values unchanged |
| R5 Inventory verification V | O and all exact private inputs needed to reproduce known-set checks and each limitation | P, I, Q, O and exact input/evidence digests | Independent verifier; prior agent receipt alone insufficient | Any bound byte change, unreproduced derivation or omitted known value invalidates V |
| R6 Operational approval A | O, V, exact K/E/L, preserved unresolved IDs and source scope | P, I, Q, O, V and K/E/L digests | Research lead approves exact operational bytes | O/V change, revocation or intervening qualification makes A unusable |
| R7 Residual-risk acceptance R | Specific unresolved scope and narrowed assurance, H unbounded, numeric risk unidentified | P, I, Q, O, V, A and exact K/E/L digests; no future artifacts | Research lead explicitly accepts unquantified risk; generic waiver invalid | Any approved scope/evidence/ledger/inventory change or revoked A requires new R |
| R8 Pre-generation verification B | Materialized packages/defaults/T8/aliases, P/I/Q and approved O/V/A/R; no intervening unaccounted matches | P, I, Q, O, V, A, R and artifact-manifest digests | Independent verifier checks entire pre-generation state | Any input byte, identity, qualification or operational change invalidates B |
| R9 Generation authorization G | B and declared boundary procedure; fixed N and acceptance order | Study ID, P, I, Q, O, V, A, R, B and materialized-artifact digests | Research lead; separate scoped authority | Binding drift, unresolved hold, revocation, closed authorization or reuse for another generation operation rejects generation; PG-R8 release continues only the same paused operation; cannot authorize another study |
| R10 Generation receipt / payload S | Authorized draws, accepted order, rejection audit, salt/payload contract and durable boundary | R9 input tuple plus G digest, exact payload/audit digests and preceding PG-R8 supplement/continuation-chain tip when applicable; never depends on later publication approval | Authorized recorder; independent seed/commitment verifier W checks private evidence | Any mismatch or altered accepted payload invalidates S; no repair or replacement under same study |
| R11 Private commitment verification W | S, exact payload/salt and computed versioned commitment value c (not the later public record C) | P, I, Q, O/V/A/R/B/G, S, payload digest and commitment value c; excludes U and public-record C digest | Independent verifier; private seeds and salt remain private | Changed bound bytes, wrong order, overlap, duplicates or mixed versions fail closed |
| R12 Publication authorization U / public commitment C | W and commitment value c plus sanitized public-record contents/status/digests | U binds S/W/c and full active tuple; public record C binds U, W, S, c and earlier tuple; payload S and W never bind U/C record digest | Lead separately authorizes experimental commitment publication; recorder publishes approved exact bytes | Revocation, hold, cancellation, binding drift or stale W rejects publication; published record immutable |
| R13 Payoff authorization D / dispatch ledger | Verified C, W, materialized artifacts and active integrity/continuation chain | Study ID, P/I/Q, O/V/A/R/B/G, S/W/U/C and D digest at each dispatch; cell/attempt bindings | Lead separately authorizes payoff execution; workers verify before every start/retry | Any mismatched tuple, revocation/hold/terminal event or source drift rejects starts/retries/finalization |
| R14 Final result F / integrity notices J | Complete registered rectangle and diagnostics or integrity-failure evidence; outcome-blind adjudication and supplements | Full study tuple, D, artifact/attempt-ledger digests; J binds original S/C/F when present and preceding integrity event | Independent integrity verifier; authorized final recorder; lead records revocations/continuations | Historical integrity overrides numeric labels; original F retained; later invalidation is append-only, never an overwrite |

### Changes and reopened gates

| Change | Required action | Boundary |
| --- | --- | --- |
| Rule contract changes | New protocol freeze and complete affected instrument qualification; new operational records and downstream authorizations | Claim profile (C-LIMITED versus E9-KNOWN-HISTORY), scope definition, approvals, overlaps, identity/serialization contract, scientific/interpretation rules |
| Implementation or qualification-source changes | New instrument identity where implementation manifest changes and new independent qualification; new downstream operational bindings | Keep P if frozen rules are unchanged; a changed rule implementation cannot silently change P semantics |
| K/E/L or inventory provenance changes before generation | Renew O/V/A/R/B and G/publication authorization if issued; no new P or I/Q when rules and bound qualification/implementation bytes are unchanged | Even same K cardinality/values with changed evidence or unresolved-ledger bytes requires renewed approvals |
| Qualification after inventory seal, before first draw | Immediately reopen inventory gate; no generation; add consumed values or execution provenance and renew O/V/A/R/B and authorizations | Existing P/I/Q can remain only if their rules/source/evidence boundaries remain valid; matches need separate authorization |
| After first draw: evidence of prior history | Apply overlap/adjudication state machine; no substitution of original operational tuple or payload | If no overlap, append membership/disclosure supplement and lead continuation; freeze and qualification identities stay unchanged |
| Matches first used after boundary | Not retroactive prior history; retain separately for future inventories | Post-boundary qualification never rewrites original K or changes temporal overlap definition; source drift still blocks dispatch |

### Identity consequences

| Identity change | Bootstrap, root and cell effects | Operational consequence |
| --- | --- | --- |
| Protocol P changes | Changes I even with identical implementation bytes; new bootstrap stream/reference vectors, private-root token and protocol-bound cell IDs | New study namespace, materialized manifests, payload/commitment and every authorization; scientific N/algorithm retained |
| Instrument I changes with same P | Changes bootstrap stream/reference vectors and private-root token; present cell formula depends on P only, so logical cell IDs stay equal | Operational dispatch identity SHALL include study ID, P and I alongside logical cell ID; no evidence may cross roots/instruments |
| Operational O/V/A/R/B/G or inventory version changes with P/I unchanged | Does not change bootstrap reference vectors, private-root token or logical cell IDs | Changes operational tuple and later payload/commitment/authorization bindings; new study uses a distinct study namespace beneath identity root |
| Disclosure supplement / integrity event | Does not change bootstrap, root, cell IDs or original payload/commitment | Append-only active-chain digest changes; release/continuation or terminal event must be checked by each consuming operation |
| New study identity with same P/I | Same deterministic bootstrap vectors and identity-root token; same logical coordinate cell IDs | New exclusive study subdirectory, operational dispatch IDs and authorizations; immutable previous study artifacts cannot be overwritten or pooled |

The existing formulas inspected are `instrument.identity` (P plus source
manifest), `analysis.positions` (P and I), `runner.private_root` (P and I) and
`Cell.identity` (protocol identity plus row/opponent/position/seat). Retain those
dependencies under the amended version. A new study subnamespace and dispatch
binding provide isolation when logical cell IDs are equal. New domain separators
and version tags for payload/commitment/final records are later qualification
obligations; do not assert byte-identical bootstrap realizations after P or I
changes. Reference vectors are qualified with synthetic inputs, not bootstrap
analyses of experimental outcomes.

Generation, commitment verification/publication, worker starts/retries and
finalization SHALL read back the full required tuple, compare every raw/body
digest against the active authorized version, check qualification source pins,
and verify an append-only authority/integrity chain with an explicit active
tip. Unknown tips, inability to verify current authority, swapped study IDs,
mixed P/I or K/E/L versions and revocation SHALL fail closed. A generic waiver
or successful checksum cannot replace a scoped lead approval. Consuming a
generation authorization is recorded durably; producer fencing and stop
evidence prevent reuse. No approval is inserted into an earlier input digest.
Here c denotes the computed commitment value; C denotes the later published
record. W verifies c without binding U or C. If no match-producing qualification
is required, bind an explicit not-applicable T disposition. Integrity notices
bind only S/C/F records that already exist at that stage and the preceding
chain tip; they cannot require a future result.

## Exact overlap and integrity dispositions

## 6. Late-history state machine — proposed

The generation boundary is the recorded instant immediately before the first
experimental raw draw, not inventory seal or commitment publication. Equality
must concern an accepted experimental position and an in-scope historical match
used before that boundary. A value first used afterwards cannot retroactively
become prior history. Planned paired E9 reuse is not historical overlap. A raw
candidate rejected for known membership or duplication is not a position.

| Discovery stage | Immediate stop/disposition | Terminal study/result status | Immutable records and authority | Publication/new study |
| --- | --- | --- | --- | --- |
| Before generation begins | No accepted experimental list exists, so proven experimental overlap is not yet possible. Newly verified prior-use values enter K; an allegation concerning a planned value blocks the inventory gate | INVENTORY_GATE_REOPENED; no experimental result; not a cancelled generated study | Retain prior seals/receipts and append new O/V/A/R/B; mark old approvals and unused G/U unusable | Only inventory disclosure if needed; A or newly verified/approved B prerequisites plus new generation authorization |
| During partial generation | Stop draws for new verified pre-boundary history; seal exact prefix/audit and independently verify equality and original-K membership. Rejected raw candidates are not positions | Prefix overlap: CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP. Disjoint prefix with any new value outside K: CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K; result NOT PRODUCED. All new values already in K: qualified continuation only under PG-R8. Closure of unresolved integrity: CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY | Supplement binds existing P/I/Q/O/V/A/R/B/G, boundary, exact ordered-prefix bytes/count/audit position, audit and authority tips, stop evidence and independent new-history receipt; no future S/c/W/U/C. Terminal event revokes G and unused U/D; retain all bytes | Terminal publication is an integrity notice; new study under PG-R10. Same paused generation may resume only after PG-R8 all-values-in-original-K proof and separate lead continuation; unchanged rejection and final full-list private verification required |
| After generation, before commitment publication | Stop experimental publication and all dispatch preparation that could execute cells | CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP; result NOT PRODUCED | Retain full S, salt, computed commitment, W and approvals; terminal event revokes or makes G/U/D unusable | Integrity cancellation notice only; no publication as an experimental commitment; new study under PG-R10 |
| After commitment publication, before first cell | Stop dispatch and experimental result/publication promotion | CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP; result NOT PRODUCED | Retain S/W/U/C and exact published bytes; append cancellation linked to C and revoke D and unused authorities | Publish append-only integrity cancellation notice linked to C; commitment remains historical record, never overwritten; new study under PG-R10 |
| During collection | Stop new starts/retries, fence or stop active workers with evidence, stop registered payoff analysis/finalization/promotion | NOT EVALUABLE: HISTORICAL_OVERLAP if proven, or UNRESOLVED_HISTORICAL_INTEGRITY if unresolved suspicion is closed once the first cell starts, including incomplete collection; Requirement C NOT ESTABLISHED | Retain S/C, every partial/completed/failed attempt and counts, late artifacts and adjudication; terminal revocation makes all outstanding authorities unusable | Integrity NOT EVALUABLE notice/record; no subset promotion or experimental supported/refuted claim; new study under PG-R10 |
| After collection, before final publication | Stop numerical finalization and experimental result publication/promotion | NOT EVALUABLE: HISTORICAL_OVERLAP if proven, or UNRESOLVED_HISTORICAL_INTEGRITY if unresolved suspicion is closed once the first cell starts, including incomplete collection; Requirement C NOT ESTABLISHED | Retain complete corpus, any sealed draft/final machine bytes and earlier tuple; append terminal invalidation and revoke finalization/promotion authority | Publish integrity NOT EVALUABLE record/notice; already computed numbers may be retained privately without eligibility; new study under PG-R10 |
| After final publication | Stop further promotion and use of original result for Requirement C or registered payoff claims | Original result INVALIDATED_HISTORICAL_OVERLAP if proven, or append-only unresolved-historical-integrity correction if suspicion is closed unresolved; effective registered status NOT EVALUABLE; Requirement C NOT ESTABLISHED | Retain original F and all S/C/attempts; append independently verified correction binding original F digest, adjudication and revocations | Append-only public integrity invalidation/correction withdrawing prior C/payoff eligibility; never overwrite original; new study under PG-R10 |

Every terminal event is append-only, names the study and binding tuple, cites
adjudication evidence, marks each existing authorization revoked/unusable and
is checked by the coordinator and every producer/worker. Authorities that were
never issued remain absent. No intact old approval authorizes continuation of
a cancelled study. No terminal event permits silent seed replacement, restart,
dropping positions, changing N or an analysis of the remaining subset.

**Sufficient overlap evidence:** independent read-back of the immutable private
accepted list establishes the exact uint64 value and position; a canonical
match artifact with bound input/attempt evidence, or an authoritative execution
receipt plus reproducible derivation and its bound historical input/caller,
establishes actual in-scope match use; a trustworthy recorded execution boundary
establishes use strictly before generation. The independent equality receipt
binds both source digests, study tuple, generation-boundary receipt, temporal
and scope reasoning and verifier identity. A source default, generator recipe,
shared filename, count, checksum alone or uncorroborated timestamp does not
prove actual prior use. Simultaneous/uncertain temporal ordering stays suspected.
Opaque evidence IDs/digests suffice for public notices; seeds, paths and raw
records remain private. Existing agent-only private membership reports do not
satisfy this independent adjudication prerequisite.

**Suspected overlap:** enter INTEGRITY_HOLD_PENDING_ADJUDICATION immediately;
before generation this blocks the inventory gate. The verifier sees no E9
payoffs, labels or outcome-selected positions and uses a predeclared equality,
scope and temporal checklist. During a hold stop/fence active producers/workers
and retain subsequent artifacts; do not use incomplete evidence as exoneration.
No timeout automatically resolves a hold. Independently verified disproval or
non-overlap plus a fresh lead release permits the original binding to continue
only when applicable PG-R8 stage conditions also hold;
closure with unresolved suspicion follows PG-R7: before first-cell start,
CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY; once the first cell starts,
NOT EVALUABLE, including incomplete collection. Proven overlap terminates at
the applicable stage without discretionary numerical review. If an original
final result is already public, append an integrity-hold notice immediately;
later append release, unresolved-integrity correction or proven-overlap
invalidation without overwriting the original. Promotion remains on hold.

**New verified history without overlap:** before generation renew operational
verification/approvals, even if only evidence changes. During partial generation
apply PG-R8 and the bound-stage review below. After generation append
a disclosure/membership supplement binding the exact existing S/c/W/U/C
applicable at that stage, the new
historical evidence, independently verified zero intersection and the updated
inspection boundary; the lead continuation record binds that supplement.
Original K/E/L, S and C are unchanged. Public wording is: “The accepted list is
also verified disjoint from the newly evidenced pre-boundary values identified
in supplement [ID/digest]. Historical coverage remains NOT ESTABLISHED.” If F
is already public, append this disclosure rather than issue a replacement
experimental result. First-use-after-boundary records are separately identified
and do not claim an extension of pre-boundary non-reuse.

The original REV03 prefix dependency graph is copied exactly into the machine contract.
All seven stage dispositions apply also to new evidence learned during an active hold.
The first-cell boundary means any cell started, even if it failed or collection is incomplete.
Source-only defaults, uncorroborated timestamps and absent evidence never prove prior use or non-overlap.
Terminal cancellation prohibits remaining draws, salt creation, experimental commitment publication and dispatch.

## C-LIMITED exact reporting contract

The following rows and wording are copied exactly from accepted REV03. I and B in these row conditions
mean the scientific integrity and realized-behavior predicates; they are not instrument identity I or
pre-generation receipt B. Likewise scientific F/D/S/H are contrast groups, not approval record roles.
The exclusion set K differs from Draft 3's realized-position count K; use explicit field names.

| Priority | Condition | Effective classification | Required text | Requirement C |
| --- | --- | --- | --- | --- |
| 1 | I fails (including historical integrity) | NOT EVALUABLE | Registered evidence is not evaluable; identify each integrity failure. No registered payoff or Requirement C promotion. | NOT ESTABLISHED; ineligible |
| 2 | I passes; Z true | REFUTED bounded benefit claim | No realized observation-driven action revision in the registered sample. The demonstrated-benefit conjunction is refuted for this bounded study; adaptation elsewhere is not refuted. | NOT ESTABLISHED; ineligible |
| 3 | I passes; positive realization; B fails | NOT EVALUABLE | Positive realization, insufficient registered replication or seat coverage. Report intact integrity separately; no beneficial-adaptation conclusion. | NOT ESTABLISHED; ineligible |
| 4 | I and B pass; any F/D/S benefit refuted | REFUTED bounded benefit claim | Identify every refuted contrast and retain all interpretation flags. Refutation is of the registered bounded benefit conjunction. | NOT ESTABLISHED; ineligible |
| 5 | I and B pass; no F/D/S refuted; not all supported | Behavior demonstrated; benefit NEITHER | Registered action revision is demonstrated; the required benefit conjunction is unresolved. No payoff-benefit conclusion. | NOT ESTABLISHED; ineligible |
| 6 | I and B pass; F/D/S supported; severe constraint | Behavior demonstrated; benefit NEITHER | Payoff gates pass; registered interaction constraint blocks aggregate attribution. Identify the constraint; do not relabel numerical support unresolved. | NOT ESTABLISHED; ineligible |
| 7 | I and B pass; F/D/S supported; no severe constraint | SUPPORTED beneficial adaptation | Beneficial observation-driven action adaptation is supported in the registered bounded E9 scope under the amended protocol. Requirement C is established only in that scope with the permanent historical non-reuse limitation. | ELIGIBLE under accepted C-LIMITED only; eventual ESTABLISHED in registered bounded scope with permanent limitation |
| Integrity override | Proven overlap after first cell, at any numerical row | NOT EVALUABLE; prior published result invalidated if applicable | Historical integrity takes precedence over numerical classification. Retain computed values as non-promotable audit evidence, and withdraw all registered payoff and Requirement C eligibility. | NOT ESTABLISHED; ineligible |
| Precollection cancellation | Proven overlap before first cell | CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP; result NOT PRODUCED | The study was cancelled for historical overlap before collection. No experimental result exists. | NOT ESTABLISHED; ineligible |
| Unverified suspicion | Private equality or prior-use evidence not established | INTEGRITY_HOLD_PENDING_ADJUDICATION | Historical integrity is unresolved; numerical classification cannot be promoted while the hold is active. Closure before first cell start: CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY. Closure once the first cell starts, including incomplete collection: NOT EVALUABLE, with append-only correction if already published. | NOT ESTABLISHED for this study pending valid disposition; any earlier published claim is placed on hold |

Every valid numerical finding carries this exact permanent limitation:

> E9 used prospectively collected OS-CSPRNG draws, unique within the study and verified disjoint from the approved known-use exclusion inventory. Complete prior qualification history and exhaustive historical non-reuse were NOT ESTABLISHED; reuse of an unrecorded historical match-seed value cannot be ruled out. No useful numerical bound on that unknown-history reuse risk was established.

Scientific classification, historical integrity and Requirement C eligibility are separate fields.
F/D/S and H statuses, exact priority row, all qualifiers, complete denominators and remaining inspection
scope must be reported separately. H payoff superiority cannot prove historical seed non-reuse.
Row 7 is eligible only after all complete evidence/integrity and accepted-profile gates; this preparation
establishes no Requirement C evidence. Rows 1–6, cancellation, historical failure and active hold are ineligible.
No original Draft 3 freshness-compliance claim is permitted under this amendment.

## Required versioned records and encoding

| Role | Required schema | Approval role | Earlier dependencies |
| --- | --- | --- | --- |
| P | `bytefray.v6.e9.protocol_freeze` v2 | Research lead separately freezes exact reviewed body/package; recorder verifies bytes. | R0, original Draft 3/freeze |
| I | `bytefray.v6.e9.instrument_identity` v2 | Recorder manifests; independent qualifier reproduces. | P |
| Q | `bytefray.v6.e9.instrument_qualification` v2 | Independent qualifier; lead accepts exact qualification boundary. | P, I |
| T | `bytefray.v6.e9.match_qualification_receipt` v2 | Lead separately authorizes matches; independent verifier verifies receipt. | P, I, Q, specific match-producing qualification authorization |
| O | `bytefray.v6.e9.inventory_seal` v2 | Custodian seals exact private bytes. | P, I, Q, T if applicable; otherwise explicit NOT_APPLICABLE |
| V | `bytefray.v6.e9.inventory_verification` v2 | Independent verifier. | P, I, Q, O |
| A | `bytefray.v6.e9.inventory_approval` v2 | Research lead. | P, I, Q, O, V |
| R | `bytefray.v6.e9.operational_risk_acceptance` v2 | Research lead explicitly accepts specific operational uncertainty. | P, I, Q, O, V, A |
| B | `bytefray.v6.e9.pre_generation_verification` v2 | Independent verifier. | P, I, Q, O, V, A, R |
| G | `bytefray.v6.e9.generation_authorization` v2 | Research lead separately authorizes one study/operation. | P, I, Q, O, V, A, R, B |
| S | `bytefray.v6.e9.generation_receipt` v2 | Authorized recorder. | P, I, Q, O, V, A, R, B, G, preceding supplement/continuation tip if any |
| W | `bytefray.v6.e9.private_commitment_verification` v2 | Independent private verifier. | P, I, Q, O, V, A, R, B, G, S, c |
| U | `bytefray.v6.e9.commitment_publication_authorization` v2 | Research lead separately authorizes after W. | S, c, W, full earlier operational tuple |
| C | `bytefray.v6.e9.published_commitment` v2 | Authorized publisher records immutable approved bytes. | S, c, W, U, full earlier operational tuple |
| D | `bytefray.v6.e9.payoff_authorization` v2 | Research lead separately authorizes payoff. | P, I, Q, O, V, A, R, B, G, S, W, U, C |
| F | `bytefray.v6.e9.final_registered_result` v2 | Independent integrity verifier; authorized final recorder. | full study tuple through D, C, attempt/artifact ledgers, current integrity-chain tip |
| J | `bytefray.v6.e9.integrity_notice` v2 | Independent integrity verifier; lead release/continuation/revocation; authorized recorder. | only S/C/F actually existing at stage, preceding authority/integrity tip, adjudication/supplement evidence |
| GenerationBoundary | `bytefray.v6.e9.generation_boundary` v2 | Authorized recorder. | existing tuple through G |
| PrefixSnapshot | `bytefray.v6.e9.prefix_snapshot` v2 | Recorder seals; independent verifier checks. | existing tuple, GenerationBoundary, AuditTip |
| PrefixAndKVerification | `bytefray.v6.e9.prefix_membership_verification` v2 | Independent verifier blinded to payoffs. | PrefixSnapshot, NewHistoricalEvidence, existing tuple including original K |
| PartialGenerationSupplement | `bytefray.v6.e9.partial_generation_supplement` v2 | Recorder appends; independent verifier checks. | existing tuple through G, GenerationBoundary, AuditTip, PrefixSnapshot, NewHistoricalEvidence, PrefixAndKVerification, prior authority tip |
| LeadContinuation | `bytefray.v6.e9.continuation_release` v2 | Research lead separately authorizes based on independent receipt. | PartialGenerationSupplement or completed-payload membership supplement, existing tuple, prior hold/event history, current authority tip |
| CompletedMembershipSupplement | `bytefray.v6.e9.completed_membership_supplement` v2 | Independent verifier; separate lead continuation before resumed publication/dispatch. | existing S/c/W/U/C as applicable, new history, current authority tip |
| AuthorityEvent | `bytefray.v6.e9.authority_event` v2 | Explicit authorized actor for event kind. | prior active tip, applicable existing tuple |
| SeedPayload | `bytefray.v6.e9.seed_payload` v2 | Authorized recorder; independently verified by W. | earlier tuple through G, GenerationBoundary, preceding supplements/continuations |

The schema catalogue fixes exact required fields, types, role predicates, dependencies and encoding.
It is a normative review specification, with no implemented reader or PASS claim. New record bodies use
case-sensitive sorted JSON keys, compact separators, literal UTF-8 without BOM and no Unicode normalization.
Duplicate/unknown fields, mixed versions, malformed hex, unresolved refs and implicit authority are rejected.
Body digest is SHA-256 over canonical body without LF; raw-file digest includes the complete canonical
envelope and one terminal LF. Full digests decide identity, never the 12-character label suffix.
Existing LF-normalized pins retain their declared recipe. New ratios use exact reduced rational strings;
finite inherited configuration floats keep their pinned form. RecordRef binds schema/version, identity,
full body digest and complete-file raw digest. ArtifactRef uses opaque public IDs; private locations are
resolved only through private evidence. Source manifests keep public repo-relative source paths.

P binds R0, original Draft 3/freeze, rule/schema specification bytes and inherited scientific/source pins.
P excludes all later operational records, K/E/L versions, approvals, R instances and authorizations.
The proposed envelope is not authority; separate lead freeze adoption binds reviewed body/package bytes
without inserting the later attestation into P's digest. P's body identity can be retained in a later
FROZEN envelope with a new raw-file digest; no consumer may treat the proposed envelope as frozen.
Any normative edit needs a new proposed package and exact lead review; an edit outside accepted REV03
semantics needs a fresh amendment decision. Implementation requires separately scoped authorization.

I binds P plus complete implementation source bytes; Q additionally binds complete qualification/test
source bytes and independent evidence. P changes alter I, deterministic stream inputs and root tokens.
I-only changes leave logical cell coordinates equal but change roots, dispatch identity and authority.
Operational changes alone preserve deterministic streams and roots, but renew operational tuples.
Each study has an exclusive new subnamespace. No evidence crosses study/instrument roots.

Keep the inherited bootstrap and private-root domain recipes with new P/I inputs; qualify new vectors.
Logical cell and dispatch labels use v2 as specified in the machine contract. Dispatch binds study, P, I,
logical cell and attempt ordinal. New payload, commitment, final-result and authority schemas are v2.
Private commitment c = SHA256(`bytefray-e9-seed-commitment-v2` followed by LF, exact 32-byte private salt,
exact canonical payload file including LF). Payload binds only earlier tuple/boundary/supplement records;
S binds payload/audit/salt; c is computed thereafter; W binds S and c; U follows W; C follows U.
Neither S nor W depends on future U/C. U approves an exact sanitized C template with a declared U-ref
insertion slot, avoiding a U/C cycle. Publication evidence is a later receipt, never inserted into C.

An authority chain has explicit study/operation scope, predecessor digest, sequence, actor, evidence,
exact binding tuple and affected existing authorities. Exclusive durable append and active-tip checks
fence producers/workers. Each consuming operation reads back the complete tuple and exact source pins
under the authority/fencing boundary. Unknown, unavailable, stale or forked tips, mixed study/P/I/K/E/L,
unaccounted qualification, revocation and holds fail closed. Consuming G is durable and single-operation;
PG-R8 release permits only the same paused producer with retained prefix/audit. Terminal events cannot release.

Prefix supplements require only the existing tuple through G, generation boundary, raw audit tip,
sealed prefix/count/position, stop/fencing evidence, new history, independent equality and original-K
receipt, and prior authority tip. No S/c/W/U/C is required. Final S/W bind supplements forward and W
rechecks the entire completed ordered list and all supplemental prior-use evidence independently.
After completion, a no-overlap supplement instead binds all existing applicable S/c/W/U/C and independent
full-list equality evidence; lead continuation is required before publication/dispatch resumes.

## Unchanged scientific and source contract

The machine contract embeds the complete inherited sample, analysis, schedules, aliases, packages,
effective T8, engine/capability/E8 and qualified-policy pins. The following exact Draft 3 sections remain
scientifically normative. Its original §7 completeness prerequisite and §10 reporting assurance are
superseded only as stated in this proposed amendment; the scientific predicates and row ordering below
remain unchanged. Original §11 recovery rules are additionally subject to the new active integrity chain.

## 3. Environment, logical rows and identity/alias ledger — P9-2

Use unchanged T8, `bytefray-rules-6-research-sensing-active-w27`: arena 512,
1,000-tick limit, Q=8, chunk=2, rotating forward order, capture hold K=1,
active sensing half-width 27 and whole-tick disruption. Preserve the
[E8 family freeze](V6_E8_FAMILY_FREEZE.md) and
[approved tactical/controller contract](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md).

The adaptive row A retains initial DENSE, C=2, L=2, B=4 and cadences 1/4.
The selectors gain no seed, identity, artifact, terminal-outcome or hidden
engine-state input. Fixed, disabled and scheduled variants retain the common
tactical executor, contact memory, legal observations and RNG ordering.

The matched constant set F is OFF, DENSE, MEDIUM and SPARSE. D is the
initial-DENSE adaptation-disabled control; S is S01–S16; H is the ten
historical nonadaptive focal rows. ADAPT8 is an opponent, never a member
of F or H.

### Existing implementation and prospective package binding

The current repository contains qualified modules and a [scratch-package factory](../../../tools/research/v6/e9/packages.py). It does **not** contain a materialized, frozen E9 evaluation roster.

Use those existing modules without behavior changes. Bind them by the capability commit and these verified raw hashes:

| Source | SHA-256 |
|---|---|
| `policy.py` | `1e30b4b985fd726c4ffa13e424fbc795a05171d44e8b8c7c5fd381fc13516b81` |
| `selectors.py` | `541fa6fd31b874c8a48a4fa1a26ecd6988a3c36edd8a4b1a45e40da198ca2cd8` |
| `packages.py` | `a87090ec6fdda53c376ce4231af1694e3f7f6327a9e11b24128fc519845ad314` |
| `tactics.py` | `369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc` |

The prospective E9 wrappers use the existing factory’s exact template: UTF-8 without BOM, Windows CRLF, its existing import lines, manifest fields and factory body. Package names and configuration expressions are fixed below. No parameter overrides are permitted.

For schedules, the exact configuration expression is:

```text
Variant(kind="schedule", schedule=Schedule(Mode.<INITIAL>, <TUPLE>, "<CLOCK>"))
```

Use the ledger’s initial mode and clock, Python tuple formatting with a trailing comma for singletons, and spaces after tuple commas. This fixes prospective bytes without creating packages now. Materialization must reproduce these bytes and record raw hashes before execution.

### Logical-to-physical mapping

| Logical row | Qualified configuration or historical identity | Physical evaluation artifact |
|---|---|---|
| A | `Variant()` | Prospective `e9_a` wrapper |
| OFF | `Variant(kind="fixed", mode=Mode.OFF)` | Frozen RUSH8 primary, `e8_q21` |
| DENSE | `Variant(kind="fixed", mode=Mode.DENSE)` | Frozen REACQ8 primary, `e8_q19` |
| MEDIUM | `Variant(kind="fixed", mode=Mode.MEDIUM)` | Prospective `e9_medium` wrapper |
| SPARSE | `Variant(kind="fixed", mode=Mode.SPARSE)` | Prospective `e9_sparse` wrapper |
| D | `Variant(kind="disabled", mode=Mode.DENSE)` | Same physical REACQ8 row as DENSE |
| S01–S16 | Exact ledger configurations | Prospective `e9_s01`–`e9_s16` wrappers |
| Ten H rows | Frozen historical primaries below | Their unchanged historical packages |

A retains initial DENSE, C=2, L=2, B=4 and cadences 1/4. New matched variants retain the qualified tactical defaults: spatial-fast acquisition, attack posture, evasion off, stress false, one `main` process, share 1 and reach 256.

Historical artifacts are bound to the complete entries in `family_fingerprints.json`, their manifest-resolved defaults and the frozen family identity `v6-e8-family-v1-981fc8b12beb`.

### Historical references and opponents

All eleven members remain opponents, each weighted **1/11**. The H column identifies the ten nonadaptive focal reference rows.

| Member | Primary | Twin | H row? | Frozen defaults: acquire / reacquire / posture / evade / processes / stress |
|---|---|---|---|---|
| RUSH8 | `e8_q21` | `e8_q10` | Yes | spatial-fast / once / attack / off / 1 / false |
| REACQ8 | `e8_q19` | `e8_q03` | Yes | spatial-fast / repeat / attack / off / 1 / false |
| PACED8 | `e8_q09` | `e8_q05` | Yes | spatial-paced / once / attack / off / 1 / false |
| STEALTH8 | `e8_q04` | `e8_q20` | Yes | ownership / once / attack / off / 1 / false |
| LURK8 | `e8_q08` | `e8_q11` | Yes | none / none / attack / off / 1 / false |
| SPLIT8 | `e8_q07` | `e8_q17` | Yes | spatial-fast / once / attack / off / 2 / false |
| GUARD8 | `e8_q13` | `e8_q18` | Yes | spatial-fast / once / guard / off / 1 / false |
| EVADE8 | `e8_q15` | `e8_q02` | Yes | spatial-fast / once / guard / on-hit / 1 / false |
| GREED8 | `e8_q01` | `e8_q06` | Yes | none / none / paint / off / 1 / false |
| STRESS8 | `e8_q22` | `e8_q12` | Yes | none / none / guard / off / 1 / true |
| ADAPT8 | `e8_q16` | `e8_q14` | No | spatial-fast / adaptive / attack / off / 1 / false |

For historical focal h against opponent j:

- Use h’s primary as focal.
- Use j’s primary when `h ≠ j`.
- Use h’s twin as opponent when `h = j`.
- Execute both focal seat orientations.
- Apply this same self/twin mapping to OFF/RUSH8 and DENSE/D/REACQ8 aliases.

New A, MEDIUM, SPARSE and schedule rows face opponent primaries throughout. There is no focal ADAPT8 row.

Entrant IDs are the stable seat IDs A and B. Package names must not alter RNG derivation or enter selectors. SPLIT8 retains its frozen `sensor`/`striker` declarations and shares.

### Equivalence obligations

| Equivalence | Required evidence | Type | Failure disposition |
|---|---|---|---|
| OFF ↔ RUSH8 | Qualified Q-C1 evidence, unchanged source pins, correct once/repeat configuration, exact declarations, action and RNG agreement under equivalent legal histories | Behavioral; package bytes differ | Stop preparation; no payoff collection |
| DENSE ↔ REACQ8 | Same obligations, including verification delivery, search, core handling and RNG order | Behavioral; package bytes differ | Stop preparation |
| D ↔ DENSE | Qualified Q-C2 evidence; shadow requests never change actions, tactics, RNG or cadence | Behavioral; selector diagnostics differ | Stop preparation |

Byte identity of the tactical copy is necessary evidence, but does not alone establish wrapper equivalence.

The current capability evidence is reusable only because its exact source hashes match. Prospective wrapper binding must be checked against that evidence. The disabled shadow state may be reconstructed as detached diagnostics; it cannot affect the physical REACQ8 execution.

Consolidation is fixed prospectively. An equivalence failure does **not** silently switch the experiment to 32 physical rows. Resolving such a failure would require a reviewed protocol revision before seeds.

### Counts and weighting

- Logical rows: `1 + 4 + 1 + 16 + 10 = 32`.
- Alias reductions: OFF/RUSH8, DENSE/REACQ8, D/DENSE.
- Physical rows: **29**.
- Prospective new physical packages: **19**.
- Historical physical focal packages: **10**.
- Additional required equivalence/twin **match executions: 0**; existing qualified evidence plus exact artifact binding supplies these obligations. No new qualification match is authorized here.

Aliases share observations; they do not multiply opponent weight, bootstrap coordinates or independent sample count. Separately planned reciprocal cells may also duplicate deterministic trajectories; report that duplication without treating it as additional independent evidence.

### Prospective wrapper byte commitments

The following raw-byte SHA-256 commitments were calculated in memory from
the pinned factory template, accepted configuration expressions and explicit
Windows CRLF encoding. No package was materialized. Future materialization
must match both this table and the recipe; these are prospective byte
commitments, not qualification of an evaluation roster.

| Package | agent.py SHA-256 | agent.yaml SHA-256 |
|---|---|---|
| `e9_a` | `c0f92445825d2a64e0691aa5d1417ba9964d35da22a43b5be8f4844749b62c58` | `977b2292e2373b15c5fd4abc6b8fc1fa372407d1ac18a2446705238e9a0e9a70` |
| `e9_medium` | `a1d95b8dcfa097bd368693d61548b9ee87444da7f489138cdb3bb22fef9cc318` | `22b46c2cab9d856cf46cc76427b6027aacec375e806d5c0422accba0c6fd9d6b` |
| `e9_sparse` | `257498af3187f415437e34552d8883298562fa0b22b705a2f81086e1390bfd6b` | `7161118a0cee2cd5ab01111b7316f0b9b8f9dbadb2daf6cb0d00a46511d68ec3` |
| `e9_s01` | `70c5b4bf205ab5569eb93529fd48f4908d93989f830cf8da905bf214f69af672` | `3061ba77a50304719f1daf0bfea46634f3fbc0500c3f812d7a643c7b1fe1e123` |
| `e9_s02` | `83ccabef1c5c20ce46209503b8819087d19b7869d920daac3869cafaf3448099` | `346710e746f103ea149226e1a324db45ba1277d9424ea3d4afd5b2051040c265` |
| `e9_s03` | `7c09e9e7f37a76c3386e960194d54d881a9ec4e9961733855fd440ea40aa7c09` | `7d86564d82964f9fa5e81bb0d361e40572544b3b9b5855dd0a01ec63e13761a5` |
| `e9_s04` | `304e1fdb6c07c8db492a5db926035f2d1ac67253c3c03e10fa4b3e7ef907180e` | `4dcea7c2b19f16f4f2b428ca3e6c78eceb056d8de0c6e65ee43d01f9fccee0b2` |
| `e9_s05` | `2c4d3743961ee69cdfe34f49fd053ccdf9b5d90259c96047552414925b0c58ef` | `46c6eab0debd009113f6f45e9450ccf4b96af787225aeaeeb458880749e52e9f` |
| `e9_s06` | `f4469452e341dd163f20798c703fc8d3600e661fe5fc14d7cd332672a86d735c` | `3e5d055b4ecadceb17ecb84d51dde03e0ccc0d0595444f16dd27a691c16f662f` |
| `e9_s07` | `72f11ba958187d9bdc27c4c741ce7a92bdebc65596e9c9251ffc6c5b093cfc33` | `37bfb877600519b457628a44ed91216feeb7cc4cc1494d26744faa2380d53ee7` |
| `e9_s08` | `4e24f75c1a01a9a4796a5874834451c0f1b45b07471b028ce17b536c0a6af616` | `c02797e9bec107a9fc2c8cf549b1a91815ef4b88869fe6c3fd0e36410e5bb0ca` |
| `e9_s09` | `b80d21160dddedbcfeff950d89fb3d14908f40a486ecdfef89fc017b40b456b3` | `70877114fb97f01a8b92b9afa18f70d20cc4f0478c051491af9ddbf9d84fa941` |
| `e9_s10` | `bbc329d6737bc67750d21c45c2df36c894dc27766f8a419253f787b6f04c5061` | `7283cee9bbe96ee543aaef3850c545cc55cb33448375b841b246a95890a205cd` |
| `e9_s11` | `7bf3efe173e9a767d2234b99a4cacf5dfa269b000a6d9a2d25272dc4d7f2be92` | `ece545f1ce73bf402c69477bcea7946363b5c15bc27be04d08a69fa3f18b2856` |
| `e9_s12` | `2569256be84551f68f68d482a074c12db6afb9bc91598de9f0dfe56e439e4f7a` | `6307286d13e28168fbc2a0b6607b38ecc63c68af710d13bdfee2746812d7e91f` |
| `e9_s13` | `e9c81903307f225c7733a879baa205b8e01878cd4f7e76ff9187b48fd6a17da7` | `2ef595b71388ef680395007ddbbccb69ef76dac3d5d0ee0bc5a5858655f6ae48` |
| `e9_s14` | `8c431fc8dec0d3e82fc7d1c3454eda96da461d5d95d764ed6d03df818113a7c5` | `77c1dcb539b59f6c9a384f34a81f7a688837f63eb2d08b39016d8866344adb8e` |
| `e9_s15` | `981c816467530625fbee7a7354974c60817231b35faf4e7615e632e04588fe5f` | `cb92c4a0b854ccfe20313517a10ac3dae566f8804448a6d30e8138a9f6ee76e5` |
| `e9_s16` | `4eff7e70925a52b758ecf32005b0a359a40d0acfd58438ac99479c6011a17a7e` | `d76a89af8f3c0cca67826d28b0343be8c95394a6977cc9f0d179238ee4cd0202` |

## 4. The sixteen-schedule identity ledger — P9-1

Times are relative to activation, using the selected clock. Boundaries specify **planned toggles**, not guaranteed realized revisions.

| ID | Clock | Initial mode | Complete boundary tuple | Planned revisions | Inclusion rationale |
|---|---|---|---|---:|---|
| S01 | opportunity | DENSE | `(2,)` | 1 | Earliest permitted one-way downgrade |
| S02 | opportunity | DENSE | `(128,)` | 1 | Later one-way downgrade |
| S03 | opportunity | DENSE | `(2,4,6,8)` | 4 | Earliest rapid repeated cycling |
| S04 | opportunity | DENSE | `(16,24,27,35)` | 4 | Delayed cycling with unequal dwell times |
| S05 | opportunity | SPARSE | `(2,)` | 1 | Earliest permitted one-way promotion |
| S06 | opportunity | SPARSE | `(128,)` | 1 | Later one-way promotion |
| S07 | opportunity | SPARSE | `(2,4,6,8)` | 4 | Rapid cycling with reversed initial allocation |
| S08 | opportunity | SPARSE | `(16,19,27,30)` | 4 | Unequal-dwell cycling with reversed initial allocation |
| S09 | wall | DENSE | `(2,)` | 1 | Absolute-time counterpart of S01 |
| S10 | wall | DENSE | `(128,)` | 1 | Absolute-time counterpart of S02 |
| S11 | wall | DENSE | `(2,4,6,8)` | 4 | Rapid wall-time cycling |
| S12 | wall | DENSE | `(16,24,27,35)` | 4 | Delayed unequal-dwell wall cycling |
| S13 | wall | SPARSE | `(2,)` | 1 | Absolute-time counterpart of S05 |
| S14 | wall | SPARSE | `(128,)` | 1 | Absolute-time counterpart of S06 |
| S15 | wall | SPARSE | `(2,4,6,8)` | 4 | Rapid wall cycling with reversed initial allocation |
| S16 | wall | SPARSE | `(16,19,27,30)` | 4 | Unequal-dwell wall cycling with reversed initial allocation |

Membership witnesses under the [qualified schedule contract](../../../tools/research/v6/e9/selectors.py):

- Single-change plans use `a=2` or `a=128`, `k=1`.
- Rapid plans use `a=2`, `h=l=2`, `k=4`.
- Unequal-dwell plans use `a=16`, `h=3`, `l=8`, `k=4`.
- All clocks, initial modes, starts, dwells and revision counts belong to the approved domains.

The enumeration check returned **16 identities, 16 unique identities, all qualified**.

The panel includes a non-power-of-four dwell, reducing exclusive reliance on cadence-aligned timing. Opportunity and wall schedules can diverge under suppression; they remain distinct identities even when particular matches produce identical trajectories.

This is a balanced, prospectively chosen panel. It supplies credible timer alternatives, but does not cover every dwell, start time, revision count or qualified schedule. No conclusion may claim that all 1,334 schedules were beaten.

## 5. Payoffs, estimands and practical benefit — P9-3

### Per-match payoff

For a valid, fully bound terminal record:

\[
Y=\begin{cases}
1 & \text{focal entrant is the authoritative winner}\\
1/2 & \text{authoritative outcome is a tie}\\
0 & \text{opponent is the authoritative winner}.
\end{cases}
\]

This encoding is selected explicitly because its mean measures win-equivalent success. A win contributes twice a tie. It is not adopted merely because E8 used it.

| Terminal class | Handling |
|---|---|
| `last_agent_standing` | Encode its validated authoritative winner |
| `tick_limit` | Encode the unchanged T8 score-resolution outcome; tick limit does not automatically mean tie |
| `all_agents_dead` | Encode the validated authoritative terminal outcome; do not infer payoff from the reason string alone |
| Valid `normal_halt` entrant metadata | Use the resulting validated match outcome |
| Invalid action, exception, malformed forfeit or containment failure | Integrity rejection, outside payoff encoding |
| Unknown termination class, inconsistent winner, corrupt or incomplete artifacts | Integrity rejection |

Preserve the [existing result/winner contract](../../RESULT_SCHEMA.md). No E9-specific scoring or winner override is introduced.

### Objective and gaps

\[
X_{p,s}=\frac1{22}\sum_{j=1}^{11}\sum_{z\in\{A,B\}}Y_{p,j,s,z},
\qquad
U_p=\frac1N\sum_{s=1}^{N}X_{p,s}.
\]

\[
\begin{aligned}
g_F&=U_A-\max_{f\in F}U_f,\\
g_D&=U_A-U_D,\\
g_S&=U_A-\max_{q\in S}U_q,\\
g_H&=U_A-\max_{h\in H}U_h.
\end{aligned}
\]

There is no per-opponent hindsight selector in these primary estimands.

| Contrast | Role |
|---|---|
| F and D | Required matched evidence for attribution to allocation revision |
| S | Required exclusion of the declared timing alternatives |
| H | Separate competitive context; required additionally for broader “outperforms the best fixed policy” wording |

### Practical benefit

Choose a common margin:

\[
\delta_F=\delta_D=\delta_S=\delta_H=0.10.
\]

Units are mean win-equivalent payoff points. A 0.10 increase corresponds, for example, to one additional loss-to-win conversion per ten equally weighted matches, or two loss-to-tie conversions.

This is a substantive threshold for the bounded benefit claim. Smaller effects remain reportable but cannot establish that claim.

For each simultaneous interval \([L_g,U_g]\):

| Status | Exact rule |
|---|---|
| Practical benefit supported | \(L_g\ge0.10\) |
| Practical benefit refuted | \(U_g<0.10\) |
| Unresolved | Otherwise |

Thus:

- Positive statistical separation from zero does not establish practical benefit.
- A precisely estimated positive gain below 0.10 refutes this specified practical claim.
- `U = 0.10` remains unresolved unless `L ≥ 0.10`.
- `L = 0.10` supports the margin.

### Timing reproduction

Choose a noninferiority allowance \(\rho=0.10\), equal to the benefit margin, as accepted in Q1.

Schedule q reproduces or improves on A’s fixed-control gain only when:

\[
L\!\left(U_q-\max_{f\in F}U_f\right)\ge0.10
\quad\text{and}\quad
U(U_A-U_q)\le0.10.
\]

Apply **timing explanation unresolved** when F and D benefit are supported and at least one schedule satisfies both conditions.

This requires a practically beneficial schedule and an uncertainty bound establishing that it is within 0.10 of A or better. Failure to reject a difference is insufficient. Equality at either boundary qualifies.

**Accepted width caveat:** This remains a conservative interval test, not a test of observed-payoff proximity. For equal observed A/schedule means and unclipped row intervals, the upper contrast bound is 2r. Thus equal observed means satisfy the reproduction bound only at r=0.05; bootstrap widening prevents that result. Clipping at payoff endpoints can reduce effective widths, so the actual clipped bounds in §6 always govern. No exception or post-hoc widening of rho is allowed.

## 6. Joint seed-block uncertainty — P9-4

Use a **joint seed-block bootstrap envelope with a finite-sample bounded-outcome guard**.

The guard avoids treating bootstrap behavior near tied comparator maxima—or a degenerate empirical sample—as sufficient justification for narrow confidence intervals.

1. Construct the 29 physical row vectors \(X_{p,s}\) from the complete rectangle.
2. Use **20,000 resamples**, each containing N seed positions sampled with replacement.
3. Within a resample, use the same sampled position multiset for every row, opponent and seat.
4. Recompute every row mean and the strongest F, S and H comparators in every resample. Recompute D and every schedule-reproduction quantity too.
5. For resample b, calculate:
   \[
   e_b=\max_{p\in P_{\rm physical}}|U_p^{*(b)}-\widehat U_p|.
   \]
6. Sort these 20,000 values. Set c to the **19,000th value**, using one-based indexing. No quantile interpolation.
7. Set the common row half-width:
   \[
   r=\max(0.05,c).
   \]
8. Form row intervals:
   \[
   \ell_p=\max(0,\widehat U_p-r),\qquad
   u_p=\min(1,\widehat U_p+r).
   \]
9. Derive all contrast intervals from those same simultaneous row intervals.

For comparator set G:

\[
L_g=\ell_A-\max_{p\in G}u_p,\qquad
U_g=u_A-\max_{p\in G}\ell_p.
\]

For a single comparator, use ordinary interval subtraction. For schedule q’s benefit over F:

\[
L_{q-F}=\ell_q-\max_{f\in F}u_f,\qquad
U_{q-F}=u_q-\max_{f\in F}\ell_f.
\]

These bounds accommodate uncertainty in which comparator is strongest. They do not condition on the observed winner.

The bounded guard supplies simultaneous coverage of at least 95% for the 29 row means under the specified uniform seed sampling:

\[
\Pr\{\exists p:|\widehat U_p-U_p|>0.05\}
\le58e^{-2N(0.05)^2}.
\]

The underlying bounded-mean result also applies conservatively to uniform sampling without replacement. [Hoeffding’s original paper](https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830)

The bootstrap can widen these bands; it cannot remove the guard. Consequently, the decision-level guarantee does not depend on claiming exact finite-sample coverage for an ordinary bootstrap percentile interval.

### Deterministic analysis randomization

After instrument qualification, define:

```text
K = SHA256(
    UTF8("bytefray-e9-analysis-bootstrap-v1\n")
    || UTF8(protocol_digest_hex + "\n")
    || UTF8(qualified_instrument_digest_hex + "\n")
)
```

For a global counter starting at zero:

- Hash `K || uint64_be(counter)`.
- Interpret its first eight bytes as an unsigned 64-bit integer v.
- Accept when `v < floor(2^64/N) × N`; otherwise increment the counter and reject that draw.
- The accepted position is `v mod N`, indexed from zero.
- Consume accepted draws in resample-major, then draw-major order.
- Counter exhaustion is an analysis failure.

No payoff digest, experimental seed value or analyst-selected random seed enters this derivation.

### Ties and arithmetic

- Comparator maxima retain **all exactly tied members**.
- Display one representative only by ascending registered ID; this never changes estimates or decisions.
- Payoffs, means, bootstrap errors, interval bounds and inequalities use exact rational arithmetic.
- Alias rows resolve to the same rational value.
- Display decimals to six places using round-half-even; displayed rounding never controls a decision.

The independent evidence count remains **N seed positions**. Matches, callbacks, revisions, both seats and repeated trajectories are not additional independent draws.

## 8. Realized adaptation gate — P9-6

### Legal causal evidence

A triggering observation must originate from an authoritative applied **verification** SENSE:

- Correct entrant/process and pending-action association.
- Issued target normalized modulo 512.
- Canonical returned anchor tuple.
- Delivered through the corresponding callback.
- Consumed once at the qualified first-callback revision boundary.
- Freshness exactly as qualified: issue tick is the boundary tick or immediately preceding tick.

Target present gives CONFIRM; target absent, including an empty tuple, gives MISSING. Refused sensing, absent callbacks, nonverification sensing and stale selector evidence do not create a trigger.

A downgrade cites the same-target confirmations that establish C=2. A promotion cites the MISSING that establishes the pending high request.

### Request and delayed-commit identity

Assign each reconstructed request:

```text
(cell identity, request ordinal, requested mode, causal receipt identities)
```

Receipt identities include entrant, process, issuance callback ordinal, issue tick, target and delivery callback ordinal.

A request remains associated with its causal evidence while waiting for cooldown. Reconstruct cancellation, supersession and satisfaction from the qualified transition contract. A commit must cite the surviving request, its selector prestate, budget and cooldown state.

A timer expiration without such provenance cannot count as observation-driven behavior.

### Action-consequence diagnostic

For each actual committed revision:

1. Clone the focal state after common observation absorption and immediately before the mode commit.
2. Preserve identical tactics, contact/search state, callback bookkeeping and RNG state.
3. In one detached branch apply the committed mode; in the other retain the precommit mode.
4. Hold those allocations while replaying the authoritative callback history.
5. Stop at the first normalized action difference, before the next actual committed revision, or at termination.
6. Before a difference, both branches must reproduce the shared actual actions; the committed branch must reproduce the actual execution.
7. Count realization only when a legal eligible action differs because of allocation: action kind, normalized operand/value or action availability.

This is an offline diagnostic. It executes no new live match and supplies no information to the policy. Once the branches choose different actions, stop; do not feed the divergent branch invented future feedback.

The horizon is the revision’s complete holding interval: the committing callback, inclusive, through the callback before the next commit or termination. The existing 1,000-tick match limit supplies the outer bound. There is no additional arbitrary short horizon.

Revision intervals are disjoint. The first qualifying difference belongs to that interval’s revision; an action cannot realize two revisions.

An independent selector reconstruction must also verify that the request follows the causal receipt sequence. A diagnostic withholding of the triggering receipt sequence must remove that request while clocks and other selector inputs remain fixed. This intervention establishes selector dependence; it is not claimed to be another legal live-world trajectory.

### Counts and threshold

Report:

- realized revisions / all committed revisions;
- realized-match count / **31,064 A matches**;
- distinct seed positions with at least one realized revision / **1,412**;
- all counts by opponent and seat.

Let K be the distinct realized seed-position count and \(K_A,K_B\) the seat-specific counts.

The registered gate is:

\[
K\ge2,\qquad K_A\ge1,\qquad K_B\ge1.
\]

This requires minimal replication and realization in both seat orientations. It does not require repeated revisions in a match, multiple opponents or a payoff-dependent realization rate.

| Case | Treatment |
|---|---|
| No discovery | Match remains in the full incidence denominator; no realization |
| No eligible request or revision | Same; report reason |
| Search or tactical priority masks revision | Not realized unless a later action differs within its holding interval |
| Callback suppression | No invented action, observation or opportunity |
| Termination before consequence | Committed but unrealized |
| Repeated revisions | Audit separately; unique ownership by holding interval |
| Selector-state change without action difference | Unrealized |
| No committed revisions | Revision fraction is not applicable; full match/seed incidence remains zero |
| Incomplete diagnostic evidence | Integrity failure, never denominator exclusion |

Complete valid data with zero realized revisions follow the explicit refutation path in §10. Positive realization that fails the replication/seat threshold follows the insufficient-coverage path.

## 9. Interaction constraints — P9-7

These are prospective **interpretation constraints**, not new mechanics or tests that diagnose engine defects.

Evaluate each opponent/seat stratum and the equal-weight aggregates. Any qualifying stratum flag survives aggregate averaging. Report denominators and insufficient exposure.

For local payoff diagnostics, the strongest F comparator may be selected within the specified stratum. This is a registered interpretation diagnostic, not a replacement primary objective. Evaluate all tied strongest comparators.

| Constraint | Metric, denominator and comparator | Severe threshold | Minimum evidence | Consequence |
|---|---|---|---|---|
| Seat dependence | For each opponent and for the whole ecology, \(g_z=\bar Y_{A,z}-\max_F\bar Y_{f,z}\). Each opponent/seat mean uses N cells | One seat has \(g_z\ge0.10\), the other \(g_{z'}\le-0.10\) | Complete N in both seats | Block aggregate support; identify seat restriction |
| Stalling/tick-limit concentration | A tick-limit proportion τ; paired difference to strongest local F. Decompose that gap into contributions from A tick-limit and other cells, both divided by the full stratum denominator | τ≥½, gap≥0.10, and non-tick-limit contribution≤0 | Complete stratum; the majority condition supplies at least half its observations | Block support; qualify gain as tick-limit-dependent |
| Immunity/capture pathology | For each victim direction, exposed seed positions receive at least two applied hostile writes to each of the eight fixed core cells during the match. Compare capture outcomes with matched F executions at those positions | No victim captures among exposed A cells; at least half end at tick limit; some F comparator captures the corresponding victim in at least half the same positions | At least 30 distinct exposed seed positions within an opponent/seat stratum | Block support; identify pressure-resistant interaction |
| Callback/phase concentration | Count local allocation-caused action differences by activation-relative phase `r mod 4`, using detached same-prestate mode interventions. Compare exposure and positive paired payoff contributions to strongest local F | At least 95% of action differences occupy one eligible phase, and at least 95% of positive paired payoff contribution comes from cells whose differences occupy only that phase; local gap≥0.10 | At least 30 distinct contributing seed positions in the dominant phase and 30 exposed positions in each other eligible phase | Block support; identify phase-concentrated scope |

Additional binding definitions:

- **Eligible phases are 1, 2 and 3.** Phase 0 is excluded from the concentration comparison because DENSE and SPARSE are both due there.
- Phase counts use **all local action differences**, not just the first realization witness. Otherwise earliest-witness attribution could manufacture phase concentration.
- A phase exposure is an actual first callback satisfying the common verification preconditions where a same-prestate DENSE/SPARSE intervention changes the action.
- For phase diagnostics, intervene locally at each actual prestate and discard the branches after action comparison. Never continue a divergent counterfactual history.
- Positive paired payoff contribution is `max(Y_A − Y_f, 0)`; zero total positive contribution cannot satisfy the concentration rule.
- Immunity checks cover both focal-victim and opponent-victim directions. The comparison is an interaction pattern, not proof that mechanics created immunity.
- Any actual violation of K=1 capture semantics or observation/action ordering belongs to integrity rejection, not a valid pathology flag.

Thirty exposed seed positions are a minimum opportunity requirement: with zero events, the ordinary one-sided 95% binomial upper limit is below 0.10. It does not establish universal immunity.

Warning and scope rules:

- Tick-limit proportion ≥½ without the severe gain-concentration conjunction: **report-only warning**.
- Immunity exposure below 30: **insufficient exposure**, restricting any “no immunity” assertion.
- Phase concentration without sufficient alternative-phase exposure: **scope restriction**, not a demonstrated artifact.
- Ordinary opponent payoff heterogeneity alone: report it; no pathology label.
- Malformed callback attribution or missing required diagnostics: **NOT EVALUABLE**.

The 0.10 seat boundary is tied to the practical payoff scale; opposing practical effects define severe seat dependence. A majority defines dominance by stalled endings. Zero capture despite repeated complete-core pressure defines the immunity concern. The 95% phase threshold defines near exclusivity. These are explicit prospective judgments, not inherited E8 pathology conventions.

## 10. Exhaustive interpretation table — P9-8

Define:

- **I:** all required integrity and analysis conditions pass.
- **Z:** zero realized revisions in complete valid diagnostics.
- **B:** behavioral threshold passes.
- **C:** any of F, D or S practical benefit is refuted.
- **P:** all F, D and S practical benefit results are supported.
- **V:** any severe §9 interpretation constraint triggers.

Apply the first matching row:

| Priority | Condition | Primary label |
|---:|---|---|
| 1 | I fails | **NOT EVALUABLE** |
| 2 | I passes and Z is true | **REFUTED bounded benefit claim** |
| 3 | I passes, realization is positive, but B fails | **NOT EVALUABLE** |
| 4 | I and B pass; C is true | **REFUTED bounded benefit claim** |
| 5 | I and B pass; C is false; P is false | **Behavior demonstrated; benefit NEITHER** |
| 6 | I and B pass; P is true; V is true | **Behavior demonstrated; benefit NEITHER** |
| 7 | I and B pass; P is true; V is false | **SUPPORTED beneficial adaptation** |

Required qualifiers:

- Row 2: “No realized observation-driven action revision in the registered sample.” This refutes the demonstrated-benefit conjunction for this study, not the possibility of adaptation elsewhere.
- Row 3: “Positive realization, insufficient registered replication or seat coverage.” Integrity may be intact.
- Row 4: identify every refuted contrast and retain interpretation flags.
- Row 6: “Payoff gates pass; registered interaction constraint blocks aggregate attribution.” Do not imply the numerical payoff results were unresolved.

Historical H is an independent finding:

| H result | Competitive statement |
|---|---|
| Supported | Practical superiority over the declared historical nonadaptive set established |
| Refuted | Specified historical practical superiority refuted |
| Unresolved | Historical practical superiority unresolved |

Broader “outperforms the best fixed policy” wording requires **primary support and H support**. H cannot rescue a failed causal gate or independently refute the matched attribution finding.

Timing qualifier:

- Apply **timing explanation unresolved** only through §5’s reproduction rule.
- Also report schedule uncertainty separately when S is unresolved.
- Schedule uncertainty alone does not trigger reproduction.

A reproduced schedule has `U(A−q)≤0.10`, so the upper bound for \(g_S\) is at most 0.10. This no longer guarantees strict practical refutation:

- If `U(g_S)<0.10`, S is refuted and row 4 applies when I/B pass.
- If `U(g_S)=0.10` and `L(g_S)<0.10`, S is unresolved and row 5 applies when F/D are supported, I/B pass, and no other required contrast is refuted.
- The hypothetical zero-width `L=U=0.10` case would meet support under the stated inequalities; the positive guarded row widths rule that case out for timing reproduction here.

Attach the timing qualifier in every case satisfying its rule; never force a primary label merely because reproduction was established. Integrity and behavioral precedence remain unchanged.

Explicit edge cases:

| Case | Resolution |
|---|---|
| Valid data, no realized revision | Row 2 |
| Strong payoff without behavioral gate | Row 2 or 3; never support |
| Behavior present, benefit unresolved | Row 5 |
| Fixed/disabled support, S unresolved | Row 5; schedule exclusion unresolved |
| Schedule reproduces the gain | Row 4 if S is strictly refuted; row 5 at the unresolved 0.10 upper-bound boundary, subject to earlier precedence; append timing qualifier |
| Any required contrast practically refuted | Row 4 after behavioral coverage |
| Historical-reference failure | Separate H finding; no broader fixed-policy superiority claim |
| All causal payoffs supported, severe pathology | Row 6 |
| Bound equals practical margin | Apply §5’s exact inequalities |

The table is total: integrity first; then zero/positive realization; then behavioral coverage; then refutation versus no refutation; then all-supported versus unresolved; finally severe constraint versus none.

## 11. Integrity and deviations — P9-9

### Pipeline

Before collection:

1. Bind protocol, instrument, engine, packages, defaults, aliases and seeds.
2. Bind the **complete effective T8 conditions**, including scheduler fields, scoring, placement, limits and unset overrides. Existing product identity hashes alone are insufficient.
3. Create the complete 900,856-cell manifest keyed by physical row, opponent, seed position and focal seat.
4. Bind historical primary/twin selection and logical aliases.
5. Verify the seed commitment and exclusion inventory privately.

For every completed cell:

- Verify unique cell identity and package/default stability.
- Bind result, replay, trace and diagnostic artifacts through raw-byte digests.
- Verify result/replay identity and terminal agreement.
- Verify trace footer, replay digest and entrant ordering.
- Verify callback ordering, requested/applied actions and authoritative observation reflection.
- Reconstruct selector state and realization diagnostics independently.
- Check sensing semantics and completeness.

Missing callbacks are legitimate when suppressed. They are not empty sensing observations. Applied empty tuples, refused sensing, null values and absent fields retain their distinct schema meanings.

### Disposition and recovery

**Maximum recovery scope: one additional execution per eligible cell, two total started attempts.** This cap and the complete allowlist below are accepted operational details under the formal P9-9 acceptance recorded in §2. Resume of a provably unstarted cell does not consume a started attempt. Preserve every original artifact and append-only collection/attempt record.

An automatic recovery is eligible only when **all** of these mechanically checked conditions hold:

1. No authoritative completed terminal result exists, either in the durable attempt record or in any retained result artifact. Any evidence that a terminal result was completed blocks recovery even if subsequent publication or digest binding failed.
2. An external supervisor record identifies host/worker loss, platform eviction, an externally initiated infrastructure shutdown, or an infrastructure storage/I/O interruption before result completion. This is the complete allowlist. Agent/runtime exceptions, crashes of unexplained origin, wall-time limits, match timeouts, resource exhaustion, containment events and semantic failures are not infrastructure recovery evidence. Exit status or absence of an output file alone is insufficient.
3. The recovery checker uses only dispatch/attempt identity, external failure records, completion status and integrity status. It cannot read payoff, scores, winner fields, tactical traces or behavior summaries. It may reject a cell on an independently produced semantic-integrity failure flag.
4. The original worker is proven stopped or fenced from publishing further output. An uncertain live worker or late conflicting result blocks recovery.
5. Physical row, opponent primary/twin, entrant seats, seed position and value, protocol, engine, instrument, package/default bytes and effective configuration remain identical. A fresh worker may start the cell from its original initial state; no partial-state continuation is permitted.
6. All partial artifacts, supervisor evidence and attempt identities are retained without overwrite. Each attempt has a separate immutable directory and identifier.
7. Eligibility is recorded durably before redispatch. Every eligible failure is retried automatically once; there is no analyst choice, payoff inspection, seed replacement or additional retry.
8. The recovery attempt satisfies every ordinary result/replay/trace/diagnostic validation. If it fails, or a conflicting completion appears from the original attempt, the seed block is unusable and the full registered result is NOT EVALUABLE.

The recovery state machine, durable completion detection, worker fencing, failure allowlist, attempt cap and outcome-blind eligibility must be independently qualified before collection. Recovery yields one payoff observation for the planned cell; it adds no seed or sample weight.

The pipeline's completed-cell validation applies to completed candidate
evidence. An eligible interruption's retained partial attempt is not supplied
as a completed cell: its incompleteness alone does not negate the recovery
route. Any indication of terminal completion or an independently determined
semantic, containment or diagnostic failure still blocks recovery. This
distinction does not permit replacing a completed result with a missing
footer, corrupt evidence or inconsistent diagnostics.

| Failure class | Detection point | Halt? | Unusable scope | Recovery and eligibility |
|---|---|---|---|---|
| Wrong protocol, instrument or source hash | Preflight / before each dispatch | Yes | Execution locked; if discovered later, affected blocks and full result fail | Correct preparation only before collection; post-start identity changes require a new boundary |
| Package/default/ruleset/effective-condition drift | Preflight and cell finalization | Yes | Affected seed block; full registered result fails | No replacement execution |
| Seed commitment, domain, uniqueness or exclusion failure | Before unlock | Yes | Entire seed protocol | No execution; no discretionary redraw after exposure |
| Identical filesystem copy of the same execution artifact | Ingestion | No | None after provenance verification | Deduplicate the copy; one observation remains |
| Multiple started attempts for one planned cell | Attempt ledger / ingestion | Yes unless exactly the registered recovery pair | None for one eligible failed original plus one validated recovery; otherwise whole seed block/full result fail | Accept only the registered recovery attempt when the original has no completed terminal result; any conflicting completion or third start rejects the block |
| Cell never started after infrastructure interruption | Resume audit / final census | Pause | None if start status is proven | Resume the same unstarted cell under unchanged identities |
| Started cell interrupted before completion; allowlisted external infrastructure evidence present | Supervisor / attempt audit | Pause affected dispatch | None if the one automatic recovery validates; otherwise whole seed block/full result fail | Apply all recovery predicates above, retain the original and count one final observation |
| Started cell incomplete, interrupted or missing without sufficient infrastructure evidence; recovery exhausted | Finalization / census | Yes | Whole seed block; full result fails | No rerun or replacement |
| Corrupt result/replay/trace or raw digest mismatch | Cell validation | Yes | Whole seed block; full result fails | No regeneration by replay re-encoding or rerun |
| Required trace footer or callback records missing | Trace validation | Yes | Whole seed block; full result fails | Canonical replay cannot replace callback evidence |
| Observation/action, pending feedback or selector mismatch | Semantic audit | Yes | Whole seed block; full result fails | No imputation or controller repair |
| Applied SENSE with no canonical tuple; refused sensing with a result | Semantic audit | Yes | Whole seed block; full result fails | Not converted to MISSING, NONE or empty tuple |
| Valid SENSE with no later callback before termination | Semantic audit | No | None | Keep issuance record; invent no delivery or revision |
| Invalid action, agent/runtime exception, semantic crash, containment breach, unexplained crash, timeout or resource exhaustion | Collection / trace audit | Yes | Whole seed block; full result fails | No payoff encoding or retry; these cannot be reclassified through the infrastructure allowlist |
| Missing disposable derived diagnostic output, authoritative trace intact | Diagnostic finalization | Pause finalization | None if reconstruction succeeds | Reconstruct once using the unchanged qualified algorithm; preserve the original absence and derived provenance |
| Incomplete authoritative evidence needed for diagnostics | Diagnostic audit | Yes | Whole seed block; full result fails | No reconstruction from assumed knowledge |
| Analysis RNG, arithmetic or qualified-instrument conformance failure | Analysis validation | Yes | Entire registered analysis | No analyst-selected alternative method |
| Valid seat/stall/immunity/phase pattern | Interpretation | No | None | Apply §9; retain all observations |

Resume conditions require a durable attempt ledger proving the cell was never started. Absence of an output file alone is insufficient.

An unusable block makes the **full registered result NOT EVALUABLE**. No remaining-block payoff analysis may be promoted as the registered result. Report actual planned, started, completed, validated, duplicate, missing and failed counts.

No corrupt or missing cell becomes a tie or loss. A recovered cell is analysis-eligible only after complete ordinary validation and recovery-ledger validation. Report eligible failures, recovery starts, recovered completions and exhausted recoveries separately. No original artifact is overwritten or discarded.

## Later gates and stop boundary

1. Separate lead amended freeze of exact P and rule/schema package.
2. Separately scoped implementation and complete independent instrument qualification.
3. Any separately authorized match-producing qualification, finished and inventoried before sealing.
4. Exact K/E/L sealing and independent verification of known membership/provenance and limitations.
5. Lead exact inventory approval A and separate specific operational risk acceptance R.
6. Complete independent pre-generation verification B.
7. Separate single-operation generation authorization G.
8. Complete independent private payload/commitment verification W.
9. Separate publication authorization U, then publication of approved immutable C.
10. Separate payoff authorization D.

This pass stops at preparation. No freeze, implementation, qualification suite, match, bootstrap analysis,
seed/salt draw, experimental commitment, publication or payoff is authorized. Validation of this package
is document/byte validation and establishes neither finite private membership nor historical completeness.
