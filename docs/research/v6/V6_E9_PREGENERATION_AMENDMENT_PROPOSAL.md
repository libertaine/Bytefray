# E9 pre-generation amendment proposal — AM-E9-PG-01 / REV03

**DRAFT FOR REVIEW, 2026-10-03. Not accepted or frozen.** The current Draft 3
lock remains in force. The 163-entry exclusion proposal is not adopted.
Seed generation, experimental seed-commitment publication and payoff execution
remain unauthorized. Requirement C remains **NOT ESTABLISHED**.

**Revision:** `AM-E9-PG-01-REV03`, parent REV02 machine raw SHA-256 `480b5bf712260d3b36deec97681e2da4ee1c07fab206c8bc20d39fc204a29916`;
parent REV02 human raw SHA-256 `a2f3ff997a64ad372ee351b08fadcfc046b6467ada5440762ae157b882a81dd9`.
REV02, packet 05, packet 04 and the original proposal byte streams are preserved. This revision
is proposal drafting only and records no acceptance or operational approval.
The packet-04 resolutions are retained; only the two stage ambiguities are revised in §6.1. Its verified
packet/frozen bindings and 505 abstract arithmetic cases remain the prior
findings; private derivation and membership remain agent-reported. No historical
recovery is repeated and no useful numerical unknown-history reuse bound exists.

The research lead has authorized closing the finite targeted recovery pass
with incomplete coverage recorded. The additive
[closure record](../../../tools/research/v6/e9/historical_targeted_pass_closure.json)
records that procedural decision without resolving DEP-01–DEP-05 or any of
the 357 original gap IDs. The shared records were reviewed for internal
consistency; the research lead has **not independently reproduced private
derivations or membership checks**. The next review packet includes the exact
[agent verification receipt](../../../tools/research/v6/e9/historical_targeted_verification.json)
and its [validation record](../../../tools/research/v6/e9/historical_targeted_validation.json).
Receipt inclusion supplies the reported checks and bindings, rather than the
private inputs needed to reproduce them independently.

## 1. Existing requirement and proposed alternative

[Frozen Draft 3 §7](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md)
requires exclusion of the E6 and E8 experimental match seeds and **all prior
qualification match seeds**, including harness defaults and derived selections.
Generation stays locked if completeness cannot be established. The
[historical scope decision](V6_E9_HISTORICAL_SCOPE_DECISION.md) supplies the
scope interpretation, including failed/partial executions and pre-migration,
other-workspace/tool and CI qualification. It supplies no retained-record cutoff.

| Decision | A — retain the existing lock | B — proposed verified known exclusions with unresolved history |
|---|---|---|
| Required coverage | Complete in-scope historical exclusion inventory, or equivalent proved finite covering set | Independently verified and separately approved known-exclusion set, with E6/E8 membership and all evidenced in-scope qualification values covered; complete unresolved-history ledger |
| Treatment of DEP-01–DEP-05 | Missing coverage blocks generation | Missing history stays unresolved and disclosed; a specific research-lead acceptance of that residual uncertainty would be an additional prerequisite |
| Non-reuse claim after private generation verification | Disjoint from all historical match seeds within the frozen scope, conditional on the approved completeness evidence | Disjoint from the approved known set and unique within E9; project-wide historical non-reuse remains NOT ESTABLISHED |
| Residual unknown-history collision risk | No draws while coverage is incomplete | Numerically unidentified with current evidence; no nontrivial project-specific upper bound is supported |
| Current outcome | Generation LOCKED | Proposal only; generation LOCKED |
| Required adoption | Existing requirement already governs | Separate amendment acceptance, new freeze, instrument implementation/requalification, inventory approval and explicit generation authorization |

B is a weakening of historical non-reuse assurance. Finishing the recovery
queue does not establish its missing history or justify calling the remaining
risk negligible. B is reviewable only as an explicit acceptance of unquantified
history risk. If the research lead requires a numerical risk ceiling, current
evidence does not meet that condition; an evidenced bound must be supplied or
generation remains locked.

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

## 4. Conditional residual-risk calculation

Let \(D=2^{64}\), \(K\) be the approved exclusion set, \(k=|K|\),
\(M=D-k\), and \(N=1,412\). Let \(H\) be the number of **distinct in-scope
historical match-seed values outside K**. Repeated executions of the same value
contribute once to H. Require \(M\ge N\) and \(0\le H\le M\).

Under the assumptions below, the accepted seed list is a uniformly sampled
ordered list without replacement from the M allowed values. The probability
of at least one unknown-history overlap is

\[
P(\mathrm{overlap}\mid H,K)
=1-\frac{\binom{M-H}{N}}{\binom{M}{N}}.
\]

The numerator is zero when \(M-H<N\). Otherwise an equivalent expression is
\(1-\prod_{j=0}^{N-1}(1-H/(M-j))\). This is the zero-overlap complement of
the [hypergeometric distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.hypergeom.html).
Counting the uniformly sampled N-element subsets establishes the ratio;
the successive conditional avoidance probabilities establish the product.

Each accepted position has marginal overlap probability H/M. Therefore
\(E[\mathrm{overlaps}]=NH/M\), and the union/expectation bound gives

\[
P(\mathrm{overlap}\mid H,K)\le\min(1,NH/M).
\]

| Assumption or input | Basis and limitation |
|---|---|
| N and domain D | Already specified by frozen §7; B proposes retaining them |
| k | Exact cardinality only after approval and read-back of K; 163 is a pending proposal count |
| Uniform, independent raw draws | An ideal model of correct OS-CSPRNG draws, independent of prior history and frozen study choices; not a property proved by a checksum or by the recovery receipt |
| Rejection procedure | Exact known-set rejection and duplicate rejection, with no further analyst-dependent acceptance criterion, yields uniform sampling without replacement under that raw-draw model |
| Fixed historical set | All relevant prior use is fixed before generation; every intervening qualification execution must be accounted for before K is sealed |
| Historical seed distribution | No uniformity or independence assumption about historical seeds is needed; history may contain defaults, deterministic generators and repeated values |
| H or a useful upper bound | UNKNOWN; no evidenced global upper bound below M was established |

Python documents OS random bytes as suitable for cryptographic use, rather
than proving exact mathematical independence for this particular future run.
[Python OS random-byte documentation](https://docs.python.org/3/library/os.html#os.urandom)
supports the implementation choice; the uniform-draw calculation remains a
conditional model. RNG/platform faults, discretionary selection, hidden
overrides and history-dependent generation invalidate its assumptions and
have no quantified failure probability here.

There is consequently **no supported numeric estimate of this project's
unknown-history collision risk**. With H unrestricted by the available
evidence, the only justified worst-case upper bound is 1. A large domain alone
does not bound H. The 357 ledger rows, 1,491 no-seed records, retained file/run
counts and five worktree registrations are not counts or bounds on distinct
unrecorded match seeds. Assigning a Bayesian prior to H would introduce an
unsupported assumption and is not proposed.

If a later complete scope argument establishes \(H\le H_{\max}\), the exact
formula at \(H_{\max}\), or \(\min(1,NH_{\max}/M)\), is a usable conditional
bound. A predeclared tolerance \(\delta\) could require that bound to be at
most \(\delta\). Neither an H bound nor a tolerance is selected by this draft.
B's present review decision is whether to accept an **unquantified** limitation,
not whether current evidence has passed an unstated numerical threshold.

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

### 6.1 Review of bound REV02 — necessary stage edits only

The parent human and machine raw SHA-256 values in the revision header are
the supplied bound REV02 bytes, preserved with packet 05. This review records
no lead choice. Exact original clause texts are retained in the machine review.

**Issue 1: existing clauses partially resolve the boundary.** PG-R6 states:

> “Once the first cell starts, proven historical overlap SHALL make the full registered result NOT EVALUABLE under historical integrity”

PG-R7 instead says “before collection or NOT EVALUABLE after collection.”
That wording does not explicitly cover closure during incomplete collection.
PG-R6 applies to proven overlap, so it cannot silently repair PG-R7's unresolved
suspicion case. PG-R9 already makes historical integrity failures ineligible
for C. Edit PG-R7 only to state the exact boundary: closure once the first
cell starts is **NOT EVALUABLE: UNRESOLVED_HISTORICAL_INTEGRITY**, including
incomplete collection. Before first-cell start, closure is
**CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY**, result **NOT PRODUCED**.
The active hold does not automatically become closure or exoneration.
Retain all attempts/counts and append terminal authority revocation; no subset
payoff promotion. If already public, append a correction linked to the immutable
original. PG-R6's proven-overlap rule and PG-R9's C rule remain unchanged.

**Issue 2: existing clauses do not resolve partial generation.** PG-R8 requires
a supplement “bound to the original immutable payload and commitment” and
forbids “reapprove a different K for the same generated study.” PG-R1 says
“no earlier digest SHALL depend on a later record that depends on it.”
PG-R4 uses “an accepted experimental position”; PG-R5 says “During partial
generation this applies to already accepted positions.” These fix equality,
immutability and dependency constraints, but provide no prefix continuation
contract before S/c/W/U/C exist. REV03 adds only that missing stage case.

Stop/fence the producer; retain all raw/rejected draws and seal a byte-exact
ordered-prefix snapshot with count and acceptance/audit position. Bind original
P/I/Q/O/V/A/R/B/G, generation boundary, stop evidence, prior authority tip,
exact raw/rejection audit tip and new-history evidence to independent
scope/prior-use/equality/original-K verification. The supplement and separate
lead continuation depend only on these existing records. Later audits, S and
private W bind the preceding supplement/continuation chain forward. Earlier
G and original inventory/approvals never incorporate later digests.

Prefix disjointness proves **only the retained prefix**, not any future list.
Resume the same paused operation only if every newly evidenced prior-use value
is independently verified already in exact original K and all original bindings
remain valid, after a separate lead continuation/release. The original K and
duplicate rejection then already exclude these values during remaining draws,
without a new rejection criterion. Preserve uint64 OS-CSPRNG, endian, accepted
order, N and every accepted position. Final private verification independently
checks the completed list against original K, supplemented prior-use evidence
and the full chain; the prefix receipt never authorizes publication or dispatch.

With zero prefix overlap but any verified new prior-use value **outside K**,
terminate as **CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K**,
result **NOT PRODUCED**. Filtering such a value would change original rejection;
silently accepting it supplies no prospective non-overlap assurance. This
proposal elects cancellation rather than add a new abort-on-future-hit procedure.
There are no remaining draws or final experimental seed-verification gate for
that cancelled study; audit integrity checks remain permissible. Stop salt
creation and experimental publications. Retain all records and append terminal
revocation making G and unused U/D unusable; publication is an integrity notice.
Only separately authorized PG-R10 new-study work can follow, with no automatic
restart, replacement or size change. Actual prefix overlap takes PG-R5 priority.
Unverifiable scope/time/equality/K or prefix/audit integrity stays on PG-R7 hold
and uses its explicit closure rule. Original K/E/L and approvals remain immutable;
the original conditional-risk formula and sampling procedure do not change.
Historical coverage remains NOT ESTABLISHED.

## 7. Requirement C interpretation and exact reporting — proposed

The governing definition is [E2–E5 synthesis §G.3](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md):
a capable agent must observe enough to change policy according to opponent or
game state; its evaluation implication requires agents that actually choose.
[E2–E6 §D.3](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md) retains C as NOT ESTABLISHED
without a registered demonstration that within-match adaptation pays.
[E2–E8 §8](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md) separates action revision
from fixed choice and repeated sensing. [E9 design §§4–6](V6_E9_BRANCH_A_ADAPTATION_DESIGN_REVIEW.md)
requires shared tactical capability, matched fixed/disabled/schedule comparisons
and lawful observation-driven revision. Frozen Draft 3 §§4–6, 8–10 supply the
acceptance predicates; `instrument.assemble` presently maps priority 7 to
“ESTABLISHED in the registered bounded scope.” This is an inspected existing
mapping, not a new finding.

Historical non-reuse is not part of the defining strategic property. It is a
separate, currently mandatory Draft 3 §7 assurance protecting the inference.
It may be explicitly revised without silently changing what adaptation means.
Recommend **C-LIMITED**: retain all scientific/causal predicates and allow a
valid priority-7 amended result to establish C only in the registered bounded
scope, carrying the history limitation permanently. This is a substantive
amendment of assurance and result eligibility and requires explicit lead
acceptance; original Draft 3 compliance is never claimed. No authoritative
definition is missing, but the lead's decision to accept that assurance change
is outstanding. If the lead regards exhaustive non-reuse as essential evidence
for C, use **E9-KNOWN-HISTORY** instead. Neither profile establishes C now.

**Retained predicates:** all integrity and complete-rectangle requirements;
legal causal action realization at at least two distinct positions and at least
one in each seat; guarded simultaneous intervals with r at least 0.05; F/D/S
support at lower bound at least 0.10, refutation at upper bound strictly below
0.10; no severe interaction constraint. H remains an independent historical
*policy comparator* finding (not the H counting unknown seed values in §4).
Primary support plus H support is required for broader “outperforms the best
fixed policy” wording. Timing reproduction uses the existing upper bound at
most rho=0.10 and never substitutes for S or the primary table. Scope, exposure,
insufficient-opportunity and timing qualifiers remain as registered. Continuing
adaptation beyond early commitment is not inferred from a single revision.

Store the unchanged scientific row/contrast statuses separately from historical
integrity, effective classification, claim profile and Requirement C eligibility.
The following is exact proposed reporting text; conditions retain the original
ordered first-match priority. “C” in Draft 3's table is a refuted-contrast flag,
not Requirement C. Integrity includes the proposed historical rule.

| Priority | Registered condition | Effective primary classification | Required reporting text | Requirement C |
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

Every valid numerical finding SHALL also carry this permanent limitation:

> E9 used prospectively collected OS-CSPRNG draws, unique within the study and verified disjoint from the approved known-use exclusion inventory. Complete prior qualification history and exhaustive historical non-reuse were NOT ESTABLISHED; reuse of an unrecorded historical match-seed value cannot be ruled out. No useful numerical bound on that unknown-history reuse risk was established.

Under C-LIMITED, row 7's machine field would read “ESTABLISHED in the registered
bounded scope with permanent historical non-reuse limitation”, with eligibility
true only after the complete integrity and accepted-profile gates pass. Rows
1–6 have eligibility false and C NOT ESTABLISHED. Historical failure has
eligibility false regardless of any stored numerical row. A cancellation has
no numerical row; suspected integrity prohibits promotion while adjudication
is pending. Always report F/D/S and H statuses separately, the exact row and
qualifiers, complete counts, approved K/evidence boundary and remaining scope.
Do not translate NEITHER to refutation or absence of evidence to non-overlap.

Exact alternative if the lead declines C-LIMITED:

> Under claim profile E9-KNOWN-HISTORY, priority row 7 reports SUPPORTED bounded adaptation under known-history exclusions. This is a separately named amended-protocol finding and does not establish Requirement C as originally governed. Requirement C SHALL remain NOT ESTABLISHED for every row and integrity disposition. All scientific predicates and qualifiers remain unchanged; the permanent historical limitation SHALL accompany every finding. Accepting this profile requires a new rule freeze and qualified final-record interpretation; it is not a prose-only relabeling.

## 8. Complete qualification and unchanged design — proposal only

No executable contract is implemented in this revision. Later work must cover
the complete amended instrument: new schema readers and graph/authority checks,
known-set versus completeness separation, independent generation/private
commitment verification with injected synthetic byte streams, every overlap
stage and suspected/no-overlap path, stale/mixed/revoked authorities and worker
fencing. Use a distinct protocol/identity, payload/commitment/final-record
version, preserve v1 readers and records, and qualify new deterministic
reference vectors. Verify all unchanged engine, E8, package and capability pins.
Qualification matches, if separately authorized, must finish and supply seeds
before sealing inventory; no qualification fixture becomes experimental data.
If later match-producing qualification changes the accepted qualification
evidence boundary Q, renew Q and all operational bindings as well; synthetic
PASS never authorizes those matches.

Retain N=1,412, uint64 OS-CSPRNG eight-byte big-endian draws, exact known-value
and duplicate rejection, accepted order, 29 physical rows, 11 opponents, two
seats, 16 schedules and 900,856 physical cells; 20,000 block-bootstrap resamples,
comparator reselection, fixed scientific thresholds, guarded intervals,
rho=0.10, and automatic outcome-blind infrastructure-only recovery with at most
one additional identical-cell attempt remain unchanged. All original failures
and attempts are retained. No gameplay, replay/product schema, selector
capability or tuning change is proposed. Identity changes affect reference
streams as §5 states; scientific rules stay fixed.

## 9. Decision register and acceptance boundary

| Decision | Exact research-lead choice | Recommendation |
| --- | --- | --- |
| D1 | Select A to retain the original completeness lock, or accept B as an explicit weakening with unquantified residual-history risk | Recommend B only if the lead accepts the unquantified limitation; otherwise A. No numerical assurance is supplied |
| D2 | Accept PG-R1–PG-R3 and R0–R14 as the acyclic approval/identity contract, including operational-only reapproval and stale-binding rejection | Recommend exact graph and identity effects; later records remain absent until separately authorized |
| D3 | Accept PG-R4–PG-R8 and PG-R10, including unresolved-suspicion closure at first-cell start and prefix-bound partial-generation continuation only when every new value is already in K; otherwise terminal cancellation | Recommend explicit first-cell boundary and exact original sampling/K; no prefix-only completion claim or outside-K continuation |
| D4 | Choose C-LIMITED (PG-R9 and the seven-row reporting table), or E9-KNOWN-HISTORY alternative wording | Recommend C-LIMITED because historical non-reuse is supporting assurance, not intrinsic to the defining strategic requirement; explicit substantive acceptance of assurance and eligibility change is required |

### D1–D4 lead decision form — UNRECORDED

- **D1:** A: retain Draft 3 completeness lock / B: known exclusions with unquantified residual-history risk. Accept/reject exact REV03 human/machine digests; this is amendment choice only.
- **D2:** Accept PG-R1–PG-R3 / R0–R14 and existing-prefix supplement dependencies / Reject contract. No later record inside an earlier digest; no future payload/commitment prerequisite for prefix release.
- **D3:** Accept REV03 PG-R7/PG-R8 stage dispositions and PG-R4–PG-R8 / PG-R10 / Reject stage dispositions. Post-first-cell unresolved closure is NOT EVALUABLE; partial-generation continuation only for independently proved already-in-K values, otherwise terminal cancellation.
- **D4:** C-LIMITED with permanent history limitation / E9-KNOWN-HISTORY with C NOT ESTABLISHED. Explicit substantive assurance/eligibility choice; alternative needs revised exact bytes before freeze.

All choice fields are unset. Exact proposal acceptance is separate from later
protocol freeze, implementation authorization, independent qualification,
private K/E/L verification/adoption, operational residual-risk acceptance,
pre-generation verification and generation/publication/payoff authorization.
No such acceptance, approval, qualification or authorization is recorded here.

The exact proposed normative text is below; the machine proposal contains
these same IDs and byte-equivalent text strings. Tables in §§5–7 are part of
the proposed contract, not merely examples.

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

Outstanding evidence and acceptance prerequisites:

- Exact REV03 acceptance/rejection and the four lead choices; acceptance evidence is not supplied by this draft.
- A separately frozen amended rule contract, scoped implementation authorization and independent complete instrument qualification; any match-producing qualification needs separate authorization and known-seed incorporation.
- Independent reproduction of private derivations and membership using exact inputs; packet 04 and its agent receipt do not supply that reproduction.
- Exact K/E/L bytes, E6/E8 coverage, provenance and custodian inspection-boundary attestation; all 357 unresolved IDs and DEP-01–DEP-05 preserved. The 163-entry candidate remains symbolic/unapproved.
- Separate lead inventory approval and specific unquantified residual-risk acceptance, plus independently verified materialized-artifact and pre-generation bindings.
- Separate generation and experimental commitment-publication authorization; no fresh seed or salt draws in drafting or synthetic qualification.
- Independent private payload/commitment verification and later separate payoff authorization; no experimental or Requirement C evidence exists now.

To reject REV03, select A and record rejection of AM-E9-PG-01-REV03; Draft 3
and the original generation lock continue. To accept it for later adoption,
record explicit acceptance of the exact REV03 human and machine digests,
select B with unquantified risk, accept D2 and D3's exact rules, and choose
C-LIMITED or the exact E9-KNOWN-HISTORY alternative. Choosing the alternative
requires a revised proposal before freeze so no unresolved profile is frozen.
Acceptance does not freeze P, approve K, qualify I, issue risk acceptance R or
authorize generation/publication/payoff execution. Those remain separate
versioned decisions with the prerequisites above.

Current status: AM-E9-PG-01 **DRAFT_NOT_ACCEPTED**; Draft 3 **governs**;
163-entry candidate **UNADOPTED**; finite recovery **CLOSED_INCOMPLETE**;
historical coverage **NOT ESTABLISHED**; generation **LOCKED**; experimental
commitment publication and payoff execution **UNAUTHORIZED**; Requirement C
**NOT ESTABLISHED** under every proposed option. Changes remain uncommitted.
