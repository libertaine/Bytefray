# Bytefray V6 — E9 Adaptive Policy Class and Capability Specification

**Status:** Proposed policy/capability contract for research-lead review, 2026-10-01. Documentation only: no code, preregistration, experimental seeds, matches or analysis. The state transitions below are **specified**, not registered experimental hypotheses. Requirement C remains **NOT ESTABLISHED**.

## 1. Purpose and boundary

The research question remains:

> With the E8 mechanic stack held fixed, can a more capable observation-driven adaptive policy outperform the best fixed policy by changing behavior within a match?

The [Branch A′ design review](V6_E9_BRANCH_A_ADAPTATION_DESIGN_REVIEW.md) was committed and pushed as `f31256c6b581a450716de6579df7264562c7c926`, following the synthesis boundary `658da960ad252c47d96060b488180c2394b83962`. Local HEAD, upstream and the live remote were verified at the design-review SHA, with a clean tree before this specification. The design-review commit contains only that document.

This specification settles a bounded, revisable **verification-cadence allocator**, its fixed/disabled/scheduled comparators and the capability evidence needed before experimental seeds. It does not choose an experiment matrix, statistical threshold, sample size, seed protocol, analysis instrument or executable implementation. Policy constants define behavior; they are not significance or gameplay-qualification thresholds.

E8's environment, opponents and frozen artifacts remain unchanged. No mechanic rescue, stronger search tactic, new attack script, resource layer or opponent redesign is permitted if the proposed allocator struggles. A deficiency outside this contract requires a separate scope decision. Resource/economy ideas remain parked. [Approved synthesis](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md).

## 2. Fixed environment and common tactical contract

Use the existing **T8** environment, `bytefray-rules-6-research-sensing-active-w27`: arena 512, Q=8, chunk=2 rotating forward order, whole-tick disruption, K=1, fixed cores, seeded placement, `core_base` spawn, existing scoring and tick limit, and the unchanged SENSE semantics. Passive visibility remains empty. No new API field or sensing channel is introduced.

The unchanged eleven-member E8 family remains the prospective reference ecology, including ADAPT8, EVADE8, STRESS8 and SPLIT8, with original package/default bytes and twins. A new candidate cannot inherit E8's payoff table, pathology flags or qualification. No frozen agent is replaced.

Every **new matched variant** has one process `main`, share 1, reach 256, spatial-fast initial acquisition, attack posture, evasion off and stress off. Its nonallocation behavior is the behavior in the byte-identical frozen E8 source, [RUSH8's package source](../../../tools/research/v6/e8/fixtures/agents/e8_q21/agent.py), SHA-256:

`369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc`.

The reference is a behavioral contract for separate future artifacts, not permission to edit or import mutable behavior into the frozen package. Independent implementations must reproduce its tactical decisions, including:

- Tick/callback bookkeeping and per-tick written-address set.
- Spatial discovery centers, restart rules, and initial-acquisition eligibility.
- Active knowledge updates, missing-address ordering, nearest replacement and tie-breaking.
- Reacquisition traversal and its priority over posture actions.
- Disruption writes, core confirmation/probing/adoption, cyclic core cursor and paint fallback.
- The two reset RNG draws and each actual reacquisition search's direction draw, in the frozen order. The selector and schedules consume **no RNG**.

The original ADAPT8 quiet-switch hook is **inactive in all new variants**. Its frozen opponent remains unchanged. Positive-cadence variants have the original repeat-style reacquisition machinery enabled throughout; changing between their cadences never cancels a search or clears remembered contacts. A constant OFF variant has the original once-style machinery disabled throughout, matching RUSH8. There is no dynamic transition to OFF in this first adaptive class.

The only tactical decision newly gated is whether to issue the existing first-callback verification SENSE when no search is in progress. The existing search always completes according to its original replacement/exhaustion rules. No monitoring debt, deferred attack bonus, additional repair or free observation is created.

The frozen source, [family freeze](V6_E8_FAMILY_FREEZE.md) and [Revision 5](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) jointly identify the common behavior. A conflict or failure to reproduce it is a qualification blocker, not a reason to silently improve the executor.

## 3. Allocation choices and clocks

### 3.1 Allocation choices

| Label | Period p | Verification rule | Reacquisition machinery |
|---|---:|---|---|
| OFF | 0 | Never request post-discovery verification | Original once behavior |
| DENSE | 1 | Due at every opportunity epoch | Original repeat behavior |
| MEDIUM | 2 | Due every second opportunity epoch | Original repeat behavior |
| SPARSE | 4 | Due every fourth opportunity epoch | Original repeat behavior |

The **adaptive and scheduled selectors use only DENSE and SPARSE**. OFF and MEDIUM strengthen the fixed comparison class; they are not reachable adaptive states. This restriction prevents a permanent information shutdown from disabling the evidence required to reconsider allocation. It also keeps the transition independent of clearing/starting search machinery.

At a callback, verification is issued only when all frozen verification preconditions hold: active sensing, first callback of the entrant's current tick, discovery occurred, a contact is known, and no reacquisition search is in progress. If the selector's cadence is not due, continue through the original posture logic. A search in progress retains its existing priority, whatever the cadence.

### 3.2 Opportunity epoch

At the first callback ever, the absolute opportunity counter n is 0. Increment it by one whenever a later callback has a new `current_tick`; additional callbacks in that tick do not increment it. Ticks with no callback do not increment it and create no phantom decisions.

Activation occurs when the shared executor first sets `discovered` true from an applied SENSE result. Record that callback's n as n₀ and its `current_tick` as t₀. This can occur at a first or later callback. Thereafter the relative opportunity epoch is **r = n − n₀**. Before activation the selector cannot revise allocation; all variants use the same initial acquisition.

Verification is due for p>0 exactly when **r mod p = 0**, subject to the frozen preconditions above. This phase stays anchored to activation: changing mode, replacing a contact or finishing a search does not reset it. There is no catch-up SENSE for missed epochs. DENSE therefore reproduces the original repeat gate, including first-callback discovery delivery; OFF reproduces the once gate.

Revision opportunities occur **only at the first callback of an observed tick**, after absorption of its previous-action result. A discovery delivered at a later callback initializes the selector but creates no extra revision point or verification slot. Modes remain fixed for the rest of that tick.

The scheduled class also defines a wall-tick clock **w = current_tick − t₀**, sampled only at those revision opportunities. This supplies a control for absolute timing. Neither clock accesses enemy identity, and both are available from the existing API. Activation is a shared prerequisite, not a free opponent classifier.

### 3.3 Callback ordering

For every callback, use this order:

1. Perform the frozen tick/callback bookkeeping and update n if this is a new observed tick.
2. Associate any previous-action feedback with the selector's pending copy; run the common executor's absorption, including knowledge updates and search handling.
3. Run the common observation handling, including last-known contact and core-adoption logic.
4. Initialize activation if discovery has first occurred; enqueue any verification receipt. At a first callback only, consume the buffered receipts and apply the selector/schedule decision. At later callbacks, retain the mode.
5. Select the action with the common priority order, changing only the verification-due gate.
6. Record selector metadata if that action is a verification SENSE, alongside the unchanged common pending-action record; return the action.

The selector receives no extra callback and its bookkeeping is not an engine action. Activation and receipt processing never run against a pre-absorption knowledge snapshot.

## 4. Allowed observations and deterministic signal adapter

### 4.1 Selector information boundary

The selector uses only:

- Activation and first-callback bookkeeping from the common executor.
- The opportunity epoch and public callback tick for cooldown and freshness.
- Its own pending **verification** SENSE metadata: purpose, normalized target, issue tick and process.
- The corresponding delivered `previous_action_applied` and `previous_sense_anchors`.
- Its own persistent selector state below.

It does not use READ ownership/value, core location, damage, painting score, successful-write status, callback quota deficits, inferred opponent identity or the content of discovery/search returns as allocation evidence. Those values can still inform the unchanged **executor**, exactly as they do in E8. Limiting the selector avoids adding damage estimation or a second adaptation dimension.

No seed, package/member name, manifest, external artifact, opponent source, future action, true engine state or inter-match memory may enter selection. Ordinary own-state/context information may implement the common tactics but cannot bypass the declared selector inputs. The selector is deterministic and has no RNG or wall-clock access.

Selector addresses are used only for normalization, equality and presence in a delivered tuple. No branch may classify a fixture from an absolute address, address range, inferred core layout or numeric contact signature. Geometric traversal and target ordering remain common executor functions. Consistently relabeling receipt targets must preserve selector decisions.

### 4.2 Signal classification

Maintain a selector-only pending metadata copy for each issued verification. It must not alter the executor's pending-action handling. At the next callback of the same process, associate feedback with that exact issued action. A delivered result cannot be processed twice.

| Delivered feedback | Selector receipt |
|---|---|
| Applied verification SENSE; returned tuple contains its issued target a | **CONFIRM(a, issue_tick)** |
| Applied verification SENSE; returned tuple does not contain a, including an empty tuple | **MISSING(a, issue_tick)** |
| Refused SENSE, no applicable verification feedback, nonverification SENSE, READ, WRITE or other action | **NONE** |

Here a is the lowest known address selected **when the verification was issued**, normalized modulo 512. Do not substitute a new lowest address at delivery. Presence means that address was occupied at sensing time; absence does not identify which opponent moved or prove why. Other returned addresses affect common knowledge but do not change this receipt's classification.

Malformed pairings—wrong process/action, feedback inconsistent with the pending record, or a supposedly applied SENSE with no tuple—fail qualification. They are not interpreted as empty sensing. The API distinguishes an empty tuple from `None`. [ObservationV2](../../AGENT_API_V2.md#e-observationv2), [SENSE contract](../../AGENT_API_V2.md#research-only-extension-sense).

Receipts delivered later in a tick wait until its next revision opportunity. A receipt is **fresh enough for selection** at that boundary only if its issue tick is the boundary tick or immediately preceding tick. Older receipts become NONE for the selector. The executor still absorbs them under the unchanged E8 rules; this is an internal estimator restriction, not a new channel or alteration of SENSE delivery.

Use delivered receipts in issuance order, once, at the next revision opportunity, then clear the receipt buffer. With one process and the original first-callback verification gate there is ordinarily at most one; the ordering rule makes the contract explicit. If no later callback exists, no revision is invented from trace-only information.

Discovery and search SENSE outcomes are not adaptive signals even if they reveal movement. This deliberately bounds the first test to paid verification evidence. An unknown interval is not a confirmation. NONE neither advances nor resets the confirmation run; the run describes consecutive **qualifying observations**, not uninterrupted stationarity.

## 5. Adaptive selector state and transition contract

### 5.1 Proposed constants

| Constant | Value | Design rationale and limit |
|---|---:|---|
| Initial mode | DENSE | Acquires evidence rather than assuming a stationary contact |
| Confirmation run C | 2 | Reuses E8's existing confirmation hurdle; the capability addition is revisability with continuing monitoring, not a new confidence estimator |
| Cooldown L | 2 opportunity epochs | Separates revisions and bounds churn; no claim of optimal timing |
| Revision budget B | 4 actual mode changes | Allows two complete DENSE→SPARSE→DENSE cycles while bounding policy complexity |
| Cadences | 1 and 4 | Reuses every-tick verification versus a lower positive allocation; permits reacquisition to resume |

These are disclosed design choices informed by the public E8 mechanics and known research questions. They were not fitted by new probes, payoff scans or seed-specific inspection. Public E8 results have been read: do not describe this as outcome-blind policy invention or these values as empirically optimal. Changing any value after review changes the policy contract and requires a new reviewed version before evaluation.

### 5.2 Selector state

| Variable | Domain / reset value | Meaning |
|---|---|---|
| active, n₀, t₀ | false / unset | Shared discovery activation |
| mode | DENSE | Current allocation |
| c | integer 0…2; initially 0 | Consecutive qualifying confirmations of the same issued target |
| c_target | address or unset; initially unset | Target of that confirmation run |
| high_request | false | Observed missing target requests DENSE; can wait for cooldown |
| b | integer 0…4; initially 0 | Number of actual mode changes |
| last_revision | 0 at activation | Opportunity epoch of last actual change; establishes initial cooldown |
| receipt buffer / pending metadata | empty | Undelivered or unconsumed verification evidence |

All state resets per match. Selector state cannot modify common contact memory, core cursors, search state or RNG. Clocks and activation are shared across variants; c, c_target and high_request can be computed as diagnostic shadow state in fixed/scheduled variants but must not affect their allocation or tactics.

### 5.3 Receipt update and priority

At each revision opportunity, first apply fresh receipts:

- MISSING sets `high_request` true and resets c to 0 and c_target to unset.
- CONFIRM increments c, capped at 2, if its issued target equals c_target; otherwise it starts a new run with c=1 at that target.
- While high_request is already pending, CONFIRM does not advance the run or cancel the request. NONE changes neither the run nor the request.

If mode is DENSE and high_request is true, the requested allocation is already in effect: clear the request and keep c=0, c_target unset for this boundary. Thus a missing-target observation takes precedence over a quiet-run downgrade. If mode is SPARSE, retain the request until an actual promotion or the end of the match; merely waiting does not prove the target returned.

Then apply **at most one** transition:

| Current mode | Condition after receipt processing | Result |
|---|---|---|
| SPARSE | high_request, b<4, and r−last_revision≥2 | Change to DENSE |
| DENSE | no missing-target priority at this boundary, c=2, b<4, and r−last_revision≥2 | Change to SPARSE |
| Either | Any other case | Stay |

After any actual change, increment b, set last_revision=r, clear c/c_target/high_request, and use the new mode for the current tick's action selection. Do not restart the cadence phase or search. With b=4, retain the current mode for the remainder of the match; evidence may still be logged, but cannot change allocation. A failed transition due to cooldown is not a revision and consumes no budget.

Cooldown expiry alone cannot create a new request. It may release a previously observed request or a previously accumulated confirmation run. That distinction must be visible in diagnostics: a deferred observation-driven revision is not evidence-free adaptation.

The final stable mode can be DENSE or SPARSE; the contract does not force four switches, a downgrade, a promotion or a favorable ending. Revisions are allowed even while common search work is pending, but the search is not interrupted and verification still obeys the original priority. The relevant action difference can therefore be delayed until a later eligible slot.

## 6. Fixed references and adaptation-disabled twins

### 6.1 Frozen comparison class

The proposed matched constant-allocation class is **{OFF, DENSE, MEDIUM, SPARSE}** under the common executor. Each choice is fixed before reset. It can respond tactically to missing contacts or a core probe; it cannot change its cadence because of that evidence.

- Constant OFF must reproduce frozen RUSH8 on T8 decision for decision under equivalent context/RNG and legal histories.
- Constant DENSE must reproduce frozen REACQ8 on T8 under the same conditions.
- MEDIUM and SPARSE differ from DENSE only in the verification gate; common positive-cadence reacquisition remains enabled.

The additional fixed historical reference layer is the frozen nonadaptive set: RUSH8, REACQ8, PACED8, STEALTH8, LURK8, SPLIT8, GUARD8, EVADE8, GREED8 and STRESS8. ADAPT8 is retained as an opponent/historical adaptive reference, not mislabeled fixed. Different process layouts and postures make this reference layer competitive context rather than the allocation-attribution control.

“Best frozen fixed allocation” means the best of the predeclared constant-allocation choices under the future common objective—not a champion already selected here. The broader phrase “best fixed policy” must also account for the strongest frozen nonadaptive reference under that same objective. No old mixed-field diagonal, self-entry assumption or payoff number is silently assigned to a new focal policy.

### 6.2 Disabled twin

The **primary adaptation-disabled twin** starts DENSE, like the adaptive candidate, and never commits selector-requested changes. Its executor, signal adapter, state calculation and initial RNG are shared; only the commit of mode changes is disabled. Shadow requests must have no execution side effect or random draw.

On the same legal callback history, it is identical to the adaptive candidate until the first proposed mode change. At that boundary, compare the command with and without committing the change from the **same pretransition executor state**. Thereafter live histories may diverge; identical subsequent actions across different worlds are not required.

Other constant-mode twins strengthen the comparison. They reproduce the corresponding fixed references exactly, but do not necessarily match the adaptive candidate's initial DENSE actions. Their intentional allocation difference begins at initialization, not at an undisclosed tactical change. A single permanently DENSE twin is not a substitute for comparing against the best constant choice.

If implementation of the selector or diagnostics changes core tactics, RNG consumption, search handling or observation processing in the disabled twin, qualification fails. “Same codebase” alone does not establish capability matching.

## 7. Observation-independent schedule class

Schedules need the same **two-way allocation vocabulary**, cooldown and maximum revision count as the adaptive selector. They must be able to produce DENSE→SPARSE→DENSE; a one-way timed downgrade would be an insufficient attribution control.

### 7.1 Bounded performance-reference class

Define each schedule before the match by:

| Parameter | Allowed values |
|---|---|
| Clock | Opportunity r or elapsed wall-tick w |
| Initial mode | DENSE or SPARSE |
| First planned transition time a | 2, 4, 8, 16, 32, 64, 128, 256, 512 |
| DENSE dwell h | 2, 3, 4, 8 |
| SPARSE dwell l | 2, 3, 4, 8 |
| Number of planned transitions k | 0, 1, 2, 3, 4 |

Its first boundary is a. After each planned toggle, the next boundary is the prior boundary plus the dwell of the newly selected mode, until k boundaries exist. k=0 is a constant DENSE/SPARSE control. Boundaries beyond the match never fire. Parameters are fixed per policy; there is no per-opponent or per-seed selection.

Canonical schedule identity is its clock, initial mode and complete planned boundary tuple; redundant parameter encodings are one policy, not multiple independent comparators. For an empty tuple, the clock is immaterial and the identity is just the constant mode.

At each actual revision opportunity, determine how many planned boundaries are at or before the schedule clock. The desired mode is the initial mode toggled that many times. If desired differs from current mode and the shared cooldown permits, commit it and increment the actual-change count. Otherwise hold. Recompute desired mode at the next boundary; an old request does not override newer planned parity.

This explicitly handles suppressed wall ticks: crossing two planned toggles without a callback can leave the desired mode unchanged, with **no fictional actions or two instantaneous revisions**. Actual changes never exceed the planned count or four, and use the same opportunity-epoch cooldown as the adaptive selector. A wall schedule can defer a planned mode until a callback/cooldown allows it; that depends on its own action availability, not the verification signal.

Both modes use the same activation phase and common executor. Cadence phase does not restart after a scheduled transition. The schedule selector never reads CONFIRM/MISSING, the known-address tuple, READ outcomes, score or shadow adaptive requests. Initial discovery remains the common prerequisite for monitoring; schedule timing is independent of **post-discovery causal verification evidence**, not of every fact required to play legally.

This class includes plausible two-way timing, repeated cycling, early/late starts and both clock choices. It is deliberately bounded; it is not every possible open-loop sequence. Claims must name this schedule class rather than assert superiority to all conceivable nonadaptive schedules.

The class definition is settled here; which experimental procedure can affordably compare or select among it is not. Before preregistration, the lead must approve an evaluation/selection method accounting for comparator selection and uncertainty. Choosing a convenient schedule after viewing adaptive evaluation trajectories is prohibited. If only a subset is prospectively selected, the claim must explicitly narrow to that frozen subset; it cannot claim the best of the whole class was beaten.

### 7.2 Qualification-only literal schedules

For differential qualification, a **literal schedule fixture** may specify up to four ascending opportunity epochs, with first epoch at least 2 and gaps at least 2. Its command is exactly the same alternating allocation sequence, independent of observation content. It uses no empirical payoff or evaluation history.

For example, a literal schedule beginning DENSE with epochs (4,6) produces DENSE→SPARSE→DENSE, even when all delivered verification outcomes remain confirming. This demonstrates that switching and two-way variation can exist without adaptive evidence.

Such fixtures may reproduce exact synthetic adaptive command sequences to prove the tactical executor is the same. They are **not automatically additional performance comparators**. A fixture derived from a future evaluation run is a post-hoc replay diagnostic, not a preregistered control or clean payoff baseline. This distinction prevents qualification convenience from becoming a hindsight oracle.

## 8. Reproducibility examples

The following are hand-specified contract examples, not executed tests or E8 observations. S means a fresh CONFIRM of the same target; M means a fresh MISSING of the issued target; dash means NONE. Inputs shown are the receipts consumed at each revision opportunity, not privileged world state.

### 8.1 Reversible transition and cooldown

This vector assumes discovery delivery at the first callback of epoch 0 and valid verification feedback at subsequent boundaries. The first two missing-target receipts reset the run while already DENSE; the two later confirmations refer to the same issued target. Qualification must construct a legal callback/action history for these inputs, not merely inject labels.

| r | Receipt | State after processing | Allocation decision |
|---:|---|---|---|
| 0 | Activation | DENSE, c=0, b=0, last_revision=0 | Stay DENSE |
| 1 | M | c=0; request already satisfied by DENSE | Stay DENSE |
| 2 | M | c=0; request already satisfied by DENSE | Stay DENSE |
| 3 | S | c=1 | Stay DENSE |
| 4 | S | c reaches 2 | Change to SPARSE; b=1, last_revision=4, c reset |
| 5 | M | high_request=true, c=0 | Stay SPARSE: cooldown not complete |
| 6 | — | Existing request retained | Change to DENSE; b=2, last_revision=6, request reset |

The r=6 change is caused by the r=5 observation, not a new confirmation or automatic timer flip. Without that M receipt, r=6 remains SPARSE. At r=4, SPARSE may still issue verification because r is divisible by 4; the next eligible nonmultiple of 4 provides a concrete action difference. A transition label alone is insufficient behavioral evidence.

The simpler quiet-start vector S at r=1 and r=2 changes to SPARSE at r=2. It need not wait until epoch 4. Discovery delivered at a later callback cannot supply a verification from epoch 0; its expected vector must account for the actual issue/delivery history.

### 8.2 Further changes and budget exhaustion

Continue the example with confirmations at r=7 and r=8: change to SPARSE at r=8 (b=3). An M at r=9 waits for cooldown; NONE at r=10 releases its existing request and changes to DENSE (b=4). Subsequent confirmations at r=11 and r=12 may reach c=2 but cannot downgrade. The mode stays DENSE because its revision budget is exhausted.

These receipts are representable with the cadence gate: SPARSE verification at r=8 can return M for processing at r=9. The performance schedule class can reproduce the four mode changes at (4,6,8,10) using opportunity clock, initial DENSE, a=4, h=l=2 and k=4, without observing any M receipt. Synthetic realizability still needs the full pending-action/callback fixture specified in qualification; this table alone does not certify it.

### 8.3 Stay, invalid evidence and target specificity

- Fewer than two qualifying confirmations do not downgrade, regardless of time elapsed.
- An M while already DENSE resets the run and prevents a same-boundary downgrade; it consumes no revision.
- S(a), S(a), S(b) for a≠b gives c=1 at b, rather than three confirmations of one target.
- Empty applied verification yields M; absent/refused feedback yields NONE.
- A confirmation issued more than one wall tick before its consumption boundary is ignored by the selector, while common knowledge still processes it.
- Adding an unrelated returned anchor while a remains present does not change CONFIRM(a). Removing a changes it to M even if other anchors remain.
- Altering a READ byte, paint-side value or package alias cannot change selector allocation when its declared inputs and prior state are fixed. The executor may legitimately respond to a READ; that is a different assertion.

## 9. Capability qualification before experimental seeds

### 9.1 Evidence status and method

**Qualification is not performed.** This document specifies the acceptance evidence. No qualification scripts, agents, tests or synthetic matches were created or run. Approval of this document alone is not permission to implement or execute the qualification.

Future qualification must distinguish three levels:

1. **Selector conformance:** Given a valid sequence of declared inputs, independently derived expected states/commands are exact.
2. **Adapter/executor conformance:** Pending-action association, receipt timing and commanded gates produce the specified actual actions using unchanged common tactics.
3. **Legal opportunity/containment:** Scripted legal histories can realize both staying and changing allocation, with action cost and callback suppression present, without an identity/seed bypass or mechanic modification.

Use independently written expected vectors and the frozen source as the tactical reference, not only tests that call the new implementation twice or recompute expectations using its own logic. Equivalent context includes the same legal observation/action-result history and initial RNG state. Two implementations must agree on receipts, state transitions, command modes, actions and RNG consumption where the history is shared.

### 9.2 Mandatory qualification obligations

| ID | Obligation | Required evidence / failure meaning |
|---|---|---|
| Q-C1 | Frozen tactical fidelity | OFF equals RUSH8; DENSE equals REACQ8 under equivalent legal histories, both seats, including core inference, search completion and RNG draws. Any mismatch blocks qualification. |
| Q-C2 | Every fixed variant reproducible | A disabled selector forced to each constant cadence is decision-for-decision identical to that fixed reference, including MEDIUM/SPARSE. |
| Q-C3 | Both adaptive transitions | Full synthetic callback histories realize DENSE→SPARSE and SPARSE→DENSE, including cooldown-deferred promotion and repeated cycling. Exact states match §5. |
| Q-C4 | Stay branches | No activation, insufficient confirmations, no missing evidence, already-DENSE missing evidence, cooldown and exhausted budget all produce the specified stays. No forced-switch quota. |
| Q-C5 | Causal input perturbation | Pair histories with identical clock/state but CONFIRM versus MISSING of the issued verification target; the expected allocation changes where conditions permit. |
| Q-C6 | Irrelevant input invariance | Perturb READ values, unrelated contacts that preserve target presence, aliases and forbidden metadata while selector inputs remain equivalent. Allocation must not change. Malformed inputs are separately rejected. |
| Q-C7 | Feedback semantics | Empty versus absent result, refused action, delayed callback, end without another callback, circular addresses and multiple contacts are handled exactly. No double counting or invented confirmation. |
| Q-C8 | Disabled-twin attribution | Adaptive and primary DENSE twin agree up to the first allocation change; fork the same executor state at that boundary and show only the allocation commit differs. Subsequent live-world equality is not required. |
| Q-C9 | Schedule independence and expressiveness | Schedules remain allocation-identical when verification receipts change; demonstrate two-way variation, both clocks, cooldown, skipped wall boundaries and literal synthetic sequence replay. |
| Q-C10 | Real action consequence | With verification preconditions satisfied, DENSE versus SPARSE differs at a nonmultiple-of-four epoch: SENSE versus the original productive posture action, with its ordinary cost. Labels alone fail. |
| Q-C11 | Search preservation | A cadence transition cannot cancel, restart, reorder or add an in-progress reacquisition search; replacement, exhaustion and direction draws match the common contract. |
| Q-C12 | Timing and seat coverage | Both seats and all relevant within-tick hit/delivery positions; full suppression, partial callback ticks and long gaps. Preconditions must be asserted before claiming a transition was exercised. |
| Q-C13 | Containment and reset | No identity/seed/hidden-state access, selector RNG, inter-match state or external artifacts. Equal resets produce equal initial states; diagnostics cannot feed policy decisions. |
| Q-C14 | Credible opportunity | Legal static-contact and on-hit-relocation histories allow both saved monitoring expenditure and timely restored monitoring, with productive actions before termination; report lost/blocked opportunities rather than hiding them. |
| Q-C15 | Independent contract agreement | Independent expected-vector construction agrees with receipts, commands and boundary ordering; all unexplained differences are blockers, not new semantics. |

These are required capability obligations, not empirical hypotheses with SUPPORTED/REFUTED/NEITHER labels. A later qualification record must report actual coverage and counts; no “passed” status is issued here. Fixtures must check their preconditions so an unexecuted branch cannot pass vacuously.

### 9.3 Rational stay and switch possibilities

The policy has a credible **opportunity**, not a promise of competitive advantage:

- With a static known contact, continuous callback availability, no search and eligible verification slots, SPARSE spends one verification instead of four over four opportunity epochs. The other offers follow unchanged productive tactics. Quiet evidence can therefore support reducing acquisition expenditure.
- When an applied verification finds its target missing, restoring DENSE can shorten future verification gaps and support restoring a disruption target. Whole-tick denial can be valuable after an early hit, but a late hit can cost the victim nothing. Qualification must establish actual legal timing/preconditions, not assume every restored hit denies a fixed quota.
- Continuing DENSE before enough evidence, staying SPARSE without missing evidence, and staying during cooldown/budget exhaustion are genuine branches. There is no automatic success path or requirement to change mode whenever a clock threshold is crossed.

The every-fourth monitoring phase can itself alias with evasion or scheduler timing. Both clocks and timing-perturbation qualification make this limitation explicit; they do not prove its absence in payoffs. Two confirmations do not prove future stationarity, and positive sparse monitoring adds costs absent from OFF. The controller might therefore fail to beat the best fixed reference despite being correct.

Q-C14 must show actionable behavioral opportunities in legal scripts faithful to the existing mechanics and relevant opponent behavior. It cannot make a convenient new evaluation opponent, change EVADE8's timing or prolong matches through a new capture rule. Nor does a synthetic opportunity prove that it occurs often enough in the unchanged competitive ecology to yield gain.

If signals arrive only after useful decisions are gone, search prevents the allocation difference from acting, or all meaningful branches are unreachable, stop before experimental seeds. Record the limitation for review. Do not turn behavior qualification into iterative payoff tuning against the frozen field or claim that a deliberately helpful script proves C.

## 10. Causal claim and prospective reporting

The future claim requires the complete chain:

**Observation → policy revision → changed behavior → attributable payoff improvement.**

| Link | Evidence needed later | What breaks the link |
|---|---|---|
| Observation → revision | Legal verification receipt, prestate, request/confirmation update, cooldown status and resulting command | Revision independent of relevant receipt, fixture recognition or a pure schedule explanation |
| Revision → behavior | Existing gate/priority state and actual action difference, including deferred opportunity and spent offers | Different labels without changed actions; search/termination hides every difference |
| Behavior → payoff | Prospective, common-population payoff comparison and uncertainty | No resolved benefit, isolated illustrative match or inconsistent opponent aggregation |
| Attribution | Advantage over strongest fixed references, constant disabled twins and the declared schedule benchmark | Shared-tactic imbalance, equally good disabled/scheduled policy, seed/identity bypass or hindsight fitting |

A cooldown-delayed change must cite the earlier observed request. If a literal schedule reproduces one trace, that demonstrates that timing alone can generate the sequence; it does not show that schedule would obtain the same payoff across unknown trajectories. The prospective comparison, not a trace anecdote, decides whether the observation-based choice adds value.

Existing authoritative SENSE action/results and observation reflections establish physical evidence. Selector mode/counters can be explained by deterministic diagnostics of existing observations; any later instrument work requires authorization and must add no information to the agent. Canonical replay alone does not establish callback knowledge. [Replay boundary](../../REPLAY_SCHEMA.md#python-observation-capture-explicitly-out-of-scope), [API-v2 trace specification](../../specs/v4_api_v2_trace.md).

No statistical decision rule is drafted here. Future preregistration must account for choosing the strongest fixed/scheduled comparator, common opponent weighting, mirrors/self entries, seat/phase behavior, contact, captures, stalling and distinct trajectories. No original E8 status, diagonal convention, threshold or candidate qualification transfers automatically.

Even a successful study would support useful observation-driven revision **for this bounded policy class and frozen E8 ecology**. It would not prove that Bytefray generally supports adaptation, that an economic triangle exists, or that human interaction is qualified. D and F are separate gates.

A negative after real capability qualification would be more informative than another unqualified ADAPT agent losing. It would still constrain this signal, cadence class, controller and ecology. Claims of structural impossibility require evidence separating inadequate observability, inadequate time, information cost and dominant fixed responses; they cannot follow merely from a payoff loss. No resource layer is authorized by a negative result.

## 11. Readiness and stop boundary

**Policy contract specified; capability qualification not performed; E9 not preregistration-ready.**

The research lead should review the constants, sparse-monitoring cost, exact adapter/transition ordering, schedule benchmark breadth and the narrow signal/population claim. Acceptance would establish what a later implementation must conform to. It would not approve experiment execution.

Before experimental seeds or any payoff study, an authorized implementation and independent qualification record must satisfy §9. Before preregistration, the lead must also approve a feasible fixed/schedule comparison and selection method plus the separate experiment's reporting/decision conventions. A reduced schedule class or changed controller must be explicitly reviewed; no tuning from evaluation outcomes is permitted.

No code, agent package, tool, test, experiment matrix, seed or result was created here. Only this specification is added after the design-review boundary. It is left uncommitted for review; no further push occurs. Frozen E2–E8 evidence, runtime and local settings remain untouched.

## 12. Source map

| Source | Use |
|---|---|
| [E2–E8 synthesis](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md) | Changed burden of proof; unchanged A–G classifications |
| [Published E9 design review](V6_E9_BRANCH_A_ADAPTATION_DESIGN_REVIEW.md) | Scope, shared-capability controls, schedule attribution and negative-result limits |
| [E8 results](V6_E8_RESULTS.md), [sealed machine record](../../../tools/research/v6/e8/final_registered_result.json) | Existing evidence only; no fresh result derivation |
| [E8 Revision 5](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md), [family freeze](V6_E8_FAMILY_FREEZE.md) | Existing mechanics, eleven-member ecology, original ADAPT/verification/search semantics |
| [Frozen common policy source](../../../tools/research/v6/e8/fixtures/agents/e8_q21/agent.py), [fingerprints](../../../tools/research/v6/e8/family_fingerprints.json) | Tactical equality reference and byte identity |
| [Agent API v2](../../AGENT_API_V2.md), [replay schema](../../REPLAY_SCHEMA.md), [trace specification](../../specs/v4_api_v2_trace.md), [architecture](../../../ARCHITECTURE.md) | Legal information, exact action feedback, diagnostic boundaries and unchanged runtime |

This document defines prospective behavior by design judgment. It reports no implementation pass, empirical result or registered E9 conclusion.
