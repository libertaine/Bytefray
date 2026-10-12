# E9 amended implementation and independent qualification plan — review 02

**PREPARATION ONLY, 2026-10-03.** This plan is bound to R0 `v6-e9-amendment-r0-v1-d1e1e0f89b83`
(`d1e1e0f89b83904936c10742e98a473931b738abca8a77506a6b71e4a82feefc`) and proposed P `v6-e9-prereg-v2-539a60806eab` (`539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0`).
P raw SHA-256: `c021e6713d13d3831b31f246f821ca3dfca0e3d0f10229c94efd97a0dd850a8d`. P is PROPOSED_NOT_FROZEN; Draft 3 governs.
This plan is outside P's digest and authorizes no implementation or execution. A changed normative
requirement returns to exact freeze review; changes outside accepted REV03 need a fresh R0 decision.

## Responsibilities and evidence ownership

The research lead separately freezes P, scopes implementation, accepts the independently verified Q
boundary, and issues the exact A/R/G/U/D and continuation/release/revocation decisions. The inventory
custodian seals private K/E/L with an inspection-boundary attestation. The implementer prepares a
versioned instrument with full source manifests. An independent qualifier reproduces the complete
amended instrument checks and reference vectors from exact source/test bytes. Independent inventory,
commitment and integrity verifiers read complete private inputs and reproduce checks. They cannot
substitute the producing agent's receipt for independent verification. Integrity adjudication is blinded
to E9 payoffs and uses the frozen equality, scope, actual-execution and temporal checklist. The recorder
transcribes approvals and seals append-only evidence; it cannot grant lead authority.

No independent verification is claimed by this preparation pass. The independent reviewer must be
accountable and separate from production of the implementation/evidence being verified. A future
review may use any independently authorized person or process; this pass invokes no delegated agent.

## Implementation work and independent qualification coverage

| Workstream | Proposed implementation boundary | Required independent evidence and fail cases |
| --- | --- | --- |
| W1 — records, identities and compatibility | New v2 research modules/readers alongside preserved v1 readers; exact schema catalogue, canonical encoder, manifests, P/I, study/dispatch IDs | Strict duplicate/unknown/type/version checks; raw versus body hashes; LF versus inherited LF-normalized recipes; full-digest equality despite short-label collision; noncanonical/BOM/escape/ordering/trailing-byte failures; v1 artifact read-back without rewrite; v1 approvals never authorize v2; DS-W1-01/02 accept typed primitive/artifact fields with actual RecordRef maps, reject dependencies.c (primitive or fabricated RecordRef), ArtifactRef in dependencies and RecordRef in commitment |
| W2 — approval graph and authority | Role-gated earlier-dependency readers; durable append-only authority/event log, active-tip check, operation consumption, leases/fence epochs | All R0–R14 dependencies; conditional T not-applicable; case-sensitive c versus C; U template avoids C dependency; absent/future records rejected; absent/stale/mixed study/P/I/K/E/L/source bindings; actor-role mismatch; revoked approvals; unknown/unavailable/forked tips; replayed G; race between check and draw/start/publication; all consumers fail closed; DS-W2-01 checks exact W/U/C RecordRef maps: W=P/I/Q/O/V/A/R/B/G/S, U adds W, C adds W/U; c remains a primitive input and W/U have no future C reference |
| W3 — inventory separation | New O/V/A/R/B records and known-set gate; v1 completeness semantics unchanged | Finite known verification PASS with historical completeness NOT ESTABLISHED; complete E6/E8 inclusion, all supported known prior values and conservative-exclusion provenance; missing/extra/wrong/duplicate member or unreproduced derivation failure; exact E/L change with identical K requires renewed approvals; all 357 IDs and DEP-01–DEP-05 preserved; no count-based adoption or waiver substitution |
| W4 — generation and boundary | Separate gated producer using injected deterministic synthetic byte stream for qualification; real OS-CSPRNG available only after G | Durable verified boundary before first raw draw; strict eight-byte uint64 big-endian interpretation; known/duplicate rejection only; exact accepted order and fixed N; complete rejected-candidate audit; no draws before G or after hold/cancellation; single original operation; no salt creation before accepted-list completion or after cancellation; no OS entropy calls in synthetic tests |
| W5 — prefix and continuation | Immutable ordered-prefix snapshots, raw audit/authority tips, producer fencing, independent membership receipt and append-only supplement/release | Empty/one/intermediate/last-incomplete prefix; prefix/audit/count/acceptance-position mismatch; rejected raw candidate not accepted position; private equality/prior-use/scope/temporal proof; all new values in original K + disjoint prefix + valid original tuple + separate lead continuation permits same-operation remaining draws; any verified outside-K value cancels even when prefix disjoint; overlap cancels; mixed inside/outside batch cancels; no future S/c/W/U/C prerequisite; remaining duplicate checks include retained prefix; final W independently checks full list and chain |
| W6 — all historical-integrity stages | Outcome-blind hold/adjudication, terminal revocation, full worker fencing, completed-payload supplements and correction records | Seven-stage cross-product below, positive overlap/suspicion/unresolved closure/proven disproval/no-overlap/new history/post-boundary use; first started cell, including failed first attempt, changes closure disposition; stop new draws/publication/starts/retries/promotion; retain fenced late artifacts; published F immutable; no subset, position deletion, reseal or automatic restart |
| W7 — complete private commitment and materialization | Payload/S/c/W/U/C v2; independent complete read-back; generation receipt binds earlier supplements forward | Exact 1412 positions, canonical bytes, contiguous order, strict uint64, uniqueness, original K membership, full supplemented-history disjointness, exact salt length, complete audit/rejection decisions and original operation, versioned domain, wrong salt/order/domain/source/study/tip, truncated list, prefix-only receipt and private-copy corruption; W before U/C; U-approved sanitized template and forward C binding; full materialized 41-package/82-file/default/T8/alias pins; DS-W7-01 recomputes and compares full primitive c in commitment, rejects missing/malformed/mismatched c and misplaced/mistyped payload/salt/evidence ArtifactRefs |
| W8 — reporting and scientific invariants | v2 final-record assembly and effective historical override; unchanged estimator, predicates, schedules, recovery and gameplay | Seven exact priority rows plus cancellation/hold/invalidation; independent scientific classification, historical integrity and C eligibility; separate F/D/S/H; exact permanent limitation and qualifiers; threshold equalities and timing-width caveat; full rectangle/denominators; no actual bootstrap analysis in this pass; later deterministic synthetic reference vectors only, never experimental outcomes |

Target files are new versioned research modules and focused tests under the existing E9/engine-test
locations. Final module names and entry points are implementation review choices. Do not modify the
frozen v1 instrument or replace its `complete: true` requirement with a v2 known-set PASS. Preserve
historical Draft 3/freeze, qualification records, REV02, packets, backups and original candidate bytes.
The engine dependency direction, public replay/result/Agent API versions, Ruleset semantics and selector
capability boundaries remain unchanged. Any implementation change to inherited immutable gameplay,
capability, package or E8 pins is a blocker requiring a separately reviewed scope decision.

## Stage matrix — independently qualify every row

| Discovery stage | Proven pre-boundary accepted-position overlap | Unverified suspicion and unresolved closure | Verified new history with no overlap |
| --- | --- | --- | --- |
| Before generation | No accepted list; reopen inventory, account values, renew exact O/V/A/R/B and unused authorities | Inventory gate hold; no draw; missing proof never exonerates | Reverify/reapprove changed operational evidence even if K unchanged; no new P/I/Q when rules/sources/boundaries unchanged |
| Partial generation | Stop/fence producer; seal prefix/audit; CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP, NOT PRODUCED | Hold stops raw draws; unresolved closure before any cell means CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY | Continue only independent all-values-already-in-original-K proof, disjoint retained prefix and fresh lead continuation for same paused G operation; any verified outside-K value means CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K, NOT PRODUCED |
| Generated before commitment publication | Stop publication/dispatch preparation; precollection overlap cancellation; retain S/salt/c/W | Hold; unresolved closure cancels before first cell | Full-list equality verification and existing-record supplement, then separate lead continuation; original K/E/L and payload immutable |
| Commitment public before first cell | Precollection overlap cancellation; append linked cancellation notice; retain C and revoke D/unused authorities | Immediate hold notice; unresolved closure precollection cancellation; retain published C | Bind full list and S/c/W/U/C, disclose and obtain continuation before dispatch |
| Collection, including incomplete | NOT EVALUABLE; stop starts/retries and fence running workers; retain all attempts/late artifacts | First cell started means unresolved closure NOT EVALUABLE even without complete rectangle | Bind applicable complete-payload records; independent full-list receipt and fresh lead continuation before remaining dispatch; original tuple retained |
| Complete collection before final publication | NOT EVALUABLE; stop numerical finalization/result publication and promotion | Hold; unresolved closure NOT EVALUABLE | Full-list supplement/disclosure and lead continuation before resumed finalization/publication; complete immutable corpus retained |
| Final result public | Append INVALIDATED_HISTORICAL_OVERLAP correction binding original F; effective NOT EVALUABLE; withdraw C/payoff eligibility | Append hold notice immediately; release or unresolved-integrity correction only with independent evidence/lead disposition; unresolved closure NOT EVALUABLE | Append disclosure bound to immutable F and applicable payload/commitment records; no replacement experimental result or historical-completeness claim |

For each stage also test that first use strictly after the generation boundary is separate future-inventory
history, planned paired E9 reuse is not historical overlap, simultaneous/uncertain temporal order remains
suspected, and source defaults/recipes/counts/checksums alone do not establish actual prior execution.
Never select adjudication scope or evidence from payoffs. An active hold prevents promotion of any
previously stored numerical row. Terminal closure cannot be released, reused or repaired. A new study
requires PG-R10's new identity and outcome-independent design decision, inclusion of the retired accepted
list as conservative exclusions, new verified/approved inventory, new R and separate G/U/D; old study
records remain terminal. Rules/source changes trigger new freeze/qualification as specified.

## Active authority, revocation and changes

Independent review must exercise every consuming operation: raw draw, salt creation, payload seal,
private commitment verification, commitment publication, worker start, infrastructure retry, final
assembly/seal and result promotion. Each operation resolves the applicable current authority tuple
and explicit active tip, reads back all required raw/body hashes and source pins, and holds a valid
producer/worker fencing lease across the protected action. Append-only event order and compare-and-swap
reject races and old tips; loss of current authority is fail-closed. Stop evidence identifies lease
revocation/fence epoch and retains any subsequently arriving artifacts. Prior approvals never contain
future event digests; later releases and consumers bind earlier tips forward.

Rule/profile/threshold/overlap/scope/serialization changes need new P and affected I/Q/downstream approvals.
Implementation bytes changing under unchanged P need new I and independent Q. Qualification-source or
coverage-boundary changes need new Q and operational bindings even if I bytes stay the same. Operational
K/E/L/provenance/inspection changes before generation renew O/V/A/R/B and issued downstream authorities,
without changing valid P/I/Q. Qualification after seal reopens the inventory gate before first draw;
incorporate consumed values even if already members of K and retain changed provenance. New post-first-draw
history uses the frozen state machine, never substituted operational bytes. P/I changes require new
deterministic reference vectors; operational-only changes do not change streams or logical coordinates.

## Qualification sequence and deterministic reference vectors

1. After exact amended freeze and separately scoped implementation authority, review the complete source
   and qualification manifests, static dependency boundaries and all reader/producer/worker entry points.
2. An independent qualifier runs only specifically audited synthetic tests first. Inject fixed synthetic
   byte streams/salts and prohibit OS entropy and match-service dispatch in those tests; no fixture becomes
   experimental data. Use recorded, deterministic faults for partial writes, crash-after-append, stale tip,
   revocation and late artifacts. Retain all failed attempts. Test assertions derive from frozen rules and
   independent reference calculations, rather than copying the implementation's decision path.
3. Independently derive canonical JSON/raw hashes, I, bootstrap index-stream vectors, private-root tokens,
   logical-cell/dispatch IDs, payload/commitment vectors and forward-chain digests. Cover domain/counter
   byte order and unbiased rejection; verify both unchanged dependencies and changed P/I effects. Generate
   no experimental bootstrap statistics. Public reports give opaque fixture/vector IDs and digests;
   complete private qualification inputs remain separately controlled.
4. Independently enumerate every reporting row and integrity disposition, rational support/refutation
   boundaries, guarded intervals and timing reproduction, comparator ties/reselection, scientific B/Z,
   seat/phase/pressure/stalling thresholds and denominator failures. Check immutable synthetic serialization
   against a separately derived reference record. C eligibility is true only for valid row 7 under
   C-LIMITED, never merely because a stored primary field says SUPPORTED.
5. Review preserved v1 fixtures/readers and pinned capability/engine/E8/package bytes statically. Broader
   pytest or historical suites can produce matches: identify those producers before any execution. Synthetic
   PASS does not authorize running them. If match-producing qualification is required, seek its separate
   explicit authorization and bind T, actual consumed values, all attempt evidence and any changed Q boundary
   before inventory sealing. No historical replay regeneration or re-blessing is permitted.
6. Run authorized checks serially with one fresh unique `--basetemp` under
   `D:/Projects/BATTLE2-test-temp/`, outside every `.pytest-tmp` and outside `runs/`. Do not create that directory
   in this pass. A future command template is `python -m pytest <explicitly authorized synthetic modules>
   --basetemp D:/Projects/BATTLE2-test-temp/<unique-e9-v2-qualification-run>`. Use the repository interpreter
   explicitly on Windows. Record actual collection/pass/failure counts and environmental errors. A retry,
   if separately authorized, preserves the prior attempt and uses a new unique root; no automatic retry loop.
7. Run appropriate authorized static Ruff and separate engine/client mypy checks after focused validation.
   A full headless suite follows only within any required match-producing qualification authorization.
   Independent complete Q must identify the coverage evidence and remaining limitations; focused passes,
   retained v1 evidence and document hashes alone cannot qualify the amended instrument.

## Scientific and reporting preservation

Retain N=1412; 29 physical rows; 11 opponents; two seats; 16 schedules; 900856 physical payoff cells;
logical aliases without duplicated statistical weight; 20000 paired seed-block resamples; exact rational
arithmetic; one-based order statistic 19000; half-width max(1/20, bootstrap envelope); benefit margin 1/10;
rho=1/10; comparator reselection and guarded/clipped row intervals. Support at lower bound >=1/10,
refutation at upper bound <1/10; equal upper bound remains unresolved unless lower support holds.
Timing reproduction uses the actual upper interval bound U(A-q)<=1/10 plus beneficial-schedule predicate,
never nonsignificance or observed-mean closeness. Realized adaptation needs legal causal action revision
at >=2 distinct positions and >=1 in each seat, with complete denominators and diagnostic provenance.
Keep all four severe interaction constraints, their exact thresholds/exposure rules and inherited
infrastructure-only, outcome-blind, identical-cell recovery with at most one additional attempt.

Always store scientific row/classification, historical integrity, effective status and C eligibility
separately, with F/D/S and H statuses, qualifiers, complete attempt/cell/realization counts and approved
inspection boundary. In every valid finding use the exact permanent historical limitation from the
contract. Row 7 can establish C only in the registered bounded scope with that limitation, after all
gates; rows 1–6 and historical failures/cancellation/holds leave C NOT ESTABLISHED. H superiority is
independent of exhaustive historical non-reuse. Machine final bytes are sealed and independently
reproduced completely before prose; late invalidation appends a correction linked to original F.

## Ordered later gates and current blockers

| Order | Gate | Required concrete evidence | Current disposition |
| --- | --- | --- | --- |
| 1 | Amended freeze | Exact lead authorization of proposed P body and rule/schema package | READY FOR EXACT REVIEW; not frozen |
| 2 | Implementation and independent qualification | Separate implementation scope; complete new I/Q manifests, independent evidence and reference vectors | Not authorized or performed |
| 3 | Any match-producing qualification | Separate lead authorization, input/attempt/artifact receipt T and all consumed in-scope values; explicit not-applicable disposition if not required | Not authorized or performed |
| 4 | K/E/L seal and independent verification | Complete exact private inputs, E6/E8 inclusion, known prior-use derivations, all 357 IDs/DEP-01–DEP-05 and custodian inspection attestation; O/V | Agent-only private reports insufficient; 163-entry proposal unadopted; no selected K |
| 5 | Inventory approval and operational risk acceptance | Exact lead A then specific R for those O/V/K/E/L bytes and still-unquantified scope | Absent; R0 is not R |
| 6 | Complete pre-generation verification | Exact packages/defaults/T8/aliases, qualified sources and full approved tuple; independent B | Absent |
| 7 | Generation authorization | Separate study/operation-specific G; durable boundary immediately before first raw draw | Absent; LOCKED |
| 8 | Private commitment verification | Full immutable payload/salt/audit, c and supplement/continuation chain; independent W | No generated payload; absent |
| 9 | Publication authorization | Separate U after W and exact sanitized C template; immutable approved publication | Absent; unauthorized |
| 10 | Payoff authorization | Separate D after W/U/C; current integrity/authority tip and materialized source pins | Absent; unauthorized |

The package has no drafting blocker if its validation passes. These later missing decisions/evidence
are concrete adoption/execution gates. Exhaustive coverage remains NOT ESTABLISHED permanently in this
claim profile while history remains incomplete; there is no evidenced H bound or selected numerical risk
tolerance. The original 157-entry candidate, private 163-entry proposal, all private evidence, packet
archives and immutable backups are preserved. No seed, salt, private path or session-log content is
placed in the public package. Changes remain uncommitted. Stop here for exact freeze review.
