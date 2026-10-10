# Bytefray V6 — Branch A′ / E9 Adaptation Design Review

**Status:** Focused design review only, 2026-10-01. The research lead approved the E2–E8 synthesis direction and authorized this review after its separate boundary was pushed. This document is not a preregistration and does not authorize implementation, qualification matches, new seeds, analysis or execution. Requirement C remains **NOT ESTABLISHED**.

**2026-10-02 readiness update:** The subsequent
[design-decision addendum](V6_E9_DESIGN_DECISIONS_AND_PREREGISTRATION_READINESS.md)
adopts the ten design directions and records **READY FOR PREREGISTRATION DRAFTING**
for protocol preparation, with exact outstanding freeze inputs and the later
analysis-instrument qualification gate. The review below retains its original
assessment; the addendum supplies the current readiness boundary.

## 1. Decision and research question

The next question should vary adaptive policy capability on the existing E8 mechanics. It should not add a mechanic merely to create opponent dependence or price information: E6 and E8 already established those properties in their scoped populations.

> With the E8 mechanic stack held fixed, can a more capable observation-driven adaptive policy outperform the best fixed policy by changing behavior within a match?

Recommend a **capability-matched, single-dimension adaptation comparison** on the whole-tick active-sensing environment T8. The dimension is allocation to verification/reacquisition versus the existing productive attack actions. A more capable controller may revise that allocation as evidence changes, rather than use ADAPT8's irreversible quiet-count switch. Acquisition geometry, contact memory, target selection, core inference, attack execution and all other tactics should be shared with its fixed comparators.

“More capable” must mean better capacity to use relevant observations to decide allocation, not an independently improved searcher, attacker, repairer or scheduler exploit. Any necessary correction or improvement to common tactics must be present in every new comparison variant before evaluation, separately disclosed, and never applied to the frozen E8 family.

For the currently authorized specification, common tactics remain the E8 tactics. Discovering that the adaptive policy struggles does not authorize a mechanic or tactical rescue: any proposed change outside allocation capability must stop for a separate scope decision. The specification must fix the allocation choices, causal observations, state variables, revision opportunities and revision bound before implementation or experimental seeds.

The recommended design is **not ready for preregistration**. This review resolves the causal scope and comparator requirements; the bounded policy class, observation-to-allocation rationale, capability qualification and generalization claim still need an approved specification. No implementation or empirical work was performed to fill those gaps.

## 2. Authorized boundary and evidential premise

| Binding | Verified state |
|---|---|
| Branch | `v6-research` |
| E8 result boundary | `191966b0c41704eb2fc86695569d72303d8eb834` |
| Approved synthesis boundary | `658da960ad252c47d96060b488180c2394b83962` |
| Synthesis commit | `docs(v6): synthesize E2-E8 and select Branch A next` |
| Publication | Local HEAD, upstream and independently queried live remote agree at the synthesis SHA |
| Tree before this review | Clean after the synthesis push |
| Changed scope here | This design-review document only |

The synthesis commit contains only [the E2–E8 review](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md). Its publication closes that synthesis boundary before this review begins. The synthesis's “no commit or push” statements record the original writing pass; the publication above is the subsequent authorized action.

The sealed E8 record remains the empirical authority. Its raw-byte SHA-256 was rechecked as `9b93c488af11c53220c63dc5407bffbab31fcb64721701a648918c9fd8fd2a3e`. E8-D PASS, R8-PRESERVES/YES, primary ADAPT NEITHER, companion ADAPT NOT INTERPRETABLE, no primary kill criterion and promotion false all stand. The new review does not recalculate or reinterpret them. [E8 results](V6_E8_RESULTS.md), [machine record](../../../tools/research/v6/e8/final_registered_result.json).

The load-bearing premise is specific: opponent-dependent fixed-policy choice and information/action costs survive explicit acquisition separated from movement, and repeating reacquisition pays against EVADE8 under whole-tick disruption. It does not establish useful within-match policy change. ADAPT8's registered test concerned one frozen controller against RUSH8 and REACQ8; its result cannot quantify over capable adaptive policies.

The earlier Branch A′ option held a priced-sensing research mechanic fixed. E8 has made that route more attractive by answering the channel question and clearing its own candidate screen. Branch A proper, on stable-equivalent rules, remains open but is not the selected scope. Earlier closed 4B–4D work supplies no supporting causal evidence. [Prior Branch A/A′ distinction](V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md), [synthesis](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md).

## 3. What must remain fixed

The primary environment is **T8**, `bytefray-rules-6-research-sensing-active-w27`, with the existing executable policy unchanged. This selects an existing environment; it does not create a Ruleset or a new experiment switch.

| Surface | Preserve |
|---|---|
| Action budget and scheduler | Q=8, chunk=2, rotating forward order, existing callback and suppression semantics |
| Arena and termination | Arena 512, existing 1,000-tick limit, capture hold K=1, current scoring and termination |
| Placement and geometry | Existing seeded placement and `core_base` spawn; owned cores remain fixed |
| Sensing | Existing silent SENSE, one-offer cost, inclusive window half-width 27, reach checks and next-callback delivery |
| Passive/active distinction | Active passive-visibility tuple remains empty; no new detection channel or alteration of the existing passive parents |
| Disruption and evasion | Existing whole-tick disruption; frozen EVADE8's relocation rule remains unchanged |
| Agent capability budget | API v2; same process declaration, reach and action opportunities among the new matched variants |
| Contact memory | Existing active knowledge-update semantics; estimation may summarize this evidence but may not invent contacts |
| Tactics | Same acquisition/search, reacquisition traversal, target ordering, core confirmation, attack/repair/paint execution where available to the matched variants |
| Frozen opponents | Existing eleven-member family, package bytes/defaults and primary/twin equivalence; retain ADAPT8, EVADE8 and STRESS8 |
| Frozen research evidence | E8 records, family, tooling, analyzer, decision logic, matrices and corpus remain untouched |

These facts come from the [E8 family freeze](V6_E8_FAMILY_FREEZE.md), [governing Revision 5](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) and [API extension](../../AGENT_API_V2.md#research-only-extension-sense). The old four-condition matrix describes E8 and is not a proposed E9 matrix.

Only **new focal policy variants** would be prospective experimental artifacts. They are not replacements for ADAPT8 or amendments to an old manifest. Freezing the opponent family preserves the reference ecology; it does not imply a new focal entrant inherits E8's flags, payoff table or qualification. Its actions can change opponents' realized behavior, particularly evasion, so it still needs its own future evidence.

No new economy, resource pool, mode action, sensing channel, disruption rule, relocation rule, engine observation or player setting is proposed. Do not combine this question with repairing the product seed-exposure contract. Research policies must respect containment; the product blocker remains separately open.

## 4. Operational meaning of fixed and adaptive

“Fixed policy” needs an operational boundary. Every deterministic controller is a fixed program mapping histories to actions; treating that mathematical sense as the comparator definition would make the question meaningless.

For this review, a **fixed allocation policy** chooses its monitoring/allocation rule before the match and does not revise that rule because of observed opponent behavior. It may still remember an anchor, search when it is missing, confirm a core and choose legal actions from current observations. Those shared tactical responses are necessary competence, not the strategic change being tested. REACQ8 illustrates the distinction: its repeated verification/search rule is stateful without changing its allocation policy.

An **adaptive allocation policy** uses observations acquired during the match to revise the monitoring/allocation rule governing those same tactics. Policy state resets for every match. It cannot select a strategy from external opponent identity, previous evaluation results or inter-match learning.

The first scope should keep attack posture and process layout fixed. Changing between offensive and defensive postures, introducing learned target tactics, or varying process declarations at the same time would add another capability difference. Such dimensions can be considered later if this narrowly matched comparison has a clear limit.

The phrase **best fixed policy** must mean the best member of a declared, bounded comparison class—not the best conceivable Bytefray agent. It must be broader than the two original ADAPT8 baselines and capable enough to represent plausible nonadaptive solutions to the chosen allocation problem.

Two reference layers serve different purposes:

- **Matched fixed class:** New fixed variants share the adaptive candidate's tactical executor, information handling and legal capability budget. This is the load-bearing causal comparator.
- **Frozen historical policies:** RUSH8, REACQ8 and the remaining frozen nonadaptive members provide context for the original ecology and for generic improvements. Their different postures/process layouts mean they cannot replace the matched comparison. ADAPT8 is a historical adaptive comparator, not a fixed baseline.

The full frozen nonadaptive family can show whether a new policy is competitive against the old reference class. To use the recommended wording “outperforms the best fixed policy,” require superiority to the strongest fixed reference across both layers under the same declared objective, not just a selected acquisition baseline. A claim about adaptation specifically also needs superiority to the strongest matched fixed allocation and loss of that advantage when observation-driven allocation is disabled. Beating only the historical agents answers a weaker question.

## 5. Comparator and attribution design

The treatment is a candidate observation-conditioned allocator using a common tactical executor. Its controls should expose alternative explanations, without granting additional information or changing engine semantics.

| Conceptual comparison | What it isolates | Essential limit |
|---|---|---|
| Adaptive allocator versus matched fixed allocations | Whether changing allocation improves payoff beyond constant allocation choices | Fixed variants must share every tactical improvement and must include credible alternatives, not deliberately weak endpoints |
| Adaptive allocator versus the same controller with allocation adaptation disabled | Incremental value of the observation-to-allocation decision | Disable strategic allocation change only; retain contact tracking, legal action selection, search and core tactics |
| Adaptive allocator versus credible precommitted schedules | Observation-driven choice versus a good timer or planned allocation sequence | Schedules cannot encode opponent identity or evaluation outcomes; absolute phase sensitivity must be disclosed |
| Reversible allocator versus an early observation-conditioned commit | Ongoing revision versus identifying a response once after discovery | The early-commit policy is also adaptive in a narrow sense; it must not be relabeled as fixed |
| New matched fixed variants versus historical RUSH8/REACQ8 and other frozen references | Generic tactical improvement | This comparison diagnoses confounding; it cannot by itself establish C |

These are comparison requirements for a future specification, not a selected roster or execution matrix. The adaptation-disabled control is not a single weak default: its possible fixed settings belong in the bounded fixed class. Otherwise a poor disabled setting could manufacture an adaptive advantage.

Keeping estimator computations and the executor shared where practical makes it easier to audit exactly which decision differs. It does not require paying fictional action costs for internal arithmetic: the engine charges actual actions, and the adaptive policy may legitimately spend fewer or more information offers. Time/resource containment must nevertheless be equivalent, so extra computational capacity cannot become an unreported advantage.

Do not remove raw observations from the fixed executor or inject false sensing results into the engine. That would weaken fixed tactics or change the information channel. Instead, prevent the strategic allocation selector from using opponent-history evidence while its common executor continues to handle real observations correctly.

Matching is causal at the **policy construction** level. Different policies naturally produce different action and observation histories, and an attacker can induce the evasion it later observes. Equal sensing counts, identical per-callback trajectories or replaying one policy's observations into another are not valid requirements for the live comparison.

Likewise, a schedule copied from the adaptive policy's successful evaluation matches would contain hindsight. A yoked or recorded schedule is not a clean primary comparator unless its provenance and information content are independently controlled. It must not smuggle knowledge of future events into a nominally fixed policy.

## 6. Capability worth testing

The recommended capability increase is **evidence-conditioned, revisable monitoring allocation**. A candidate should be able to distinguish stable observed contacts from evidence of relocation, account for its own observation gaps, and revise whether verification is worth competing with attack. This is a conceptual capability target, not an algorithm or a promise that it will improve payoff.

The bounded capability specification must make these decisions reproducible from the same observation history, including hysteresis/cooldowns and exhaustion of any revision budget. Its observation-independent schedule class must allow plausible two-way variation such as A→B→A, with the same allocation choices and revision limits; a one-way schedule would be an inadequate control for a revisable adaptive policy.

The existing structure gives a reason to test it: paying for repeated verification can restore an economically valuable disruption target against EVADE8, while lower acquisition pays against some other opponents. A successful controller would need to identify useful allocation in time, pay for its evidence, and avoid spending indefinitely when little is gained.

ADAPT8's two-confirmation switch cannot re-enter repeating mode once it has stopped. Quiet observations early in a match therefore need not constitute a reliable forecast of later relocation. This is a design limitation, not a diagnosis of individual E8 losses. The accepted startup possibility in family-freeze N8-10 remains unprobed by this review. [Family freeze](V6_E8_FAMILY_FREEZE.md), [registered results](V6_E8_RESULTS.md).

Three distinctions should guide a future policy specification:

1. **Evidence versus silence:** No callback, no applied verification and an empty applied result are different events. Suppression or termination can prevent evidence; a quiet timer must not treat missing observations as confirming a stationary opponent.
2. **Belief versus knowledge:** A contact is remembered evidence, not a guaranteed current position. Internal estimates of relocation frequency or monitoring value cannot access the true enemy state or future action stream.
3. **Target knowledge versus denial value:** Core confirmation does not settle where a relocated anchor is, but a moving anchor does not relocate its core. The decision is partly whether reacquiring a disruption target is worth the opportunity cost, not a repeated search for a moving objective.

A capable policy should also cope with observation latency and the game's existing slot/seat semantics. Improving the allocator should not sneak in faster core writes, different adoption rules or a new phase-specific attack script. If those common tactics are insufficient, disclose that as a policy-class design problem and revise all matched variants prospectively; do not repair the sealed family.

Before a future experimental claim, behavior-only qualification would need to demonstrate that relevant observation changes can cause the intended allocation changes, that the same event timing does not cause those changes without the relevant evidence, and that unobserved gaps are handled correctly in both seats. Those are future qualification needs, not tests run or authorized here. Scripted examples would demonstrate capability and legality, not competitive payoff.

Do not force a switch quota to create the appearance of adaptation. The policy must have the capacity to revise a decision, and empirical evidence must show the payoff-relevant change. A single useful observation-conditioned switch can support a narrow C claim; repeated sensing alone cannot. A stronger claim of continuing adaptation needs evidence of beneficial revision beyond early identification and commitment.

## 7. Legal evidence and opponent-knowledge containment

The agent may use its own context, legal delivered observations and memory of its own actions/results. Relevant existing signals include sensing returns, confirmed or missing remembered anchors, previous READ results, actual callback/action timing, and its own action history. Their economic interpretation can be estimated internally; no new engine signal is needed.

The API does **not** directly report opponent disruption, who attacked the agent, whether a write hit an enemy anchor, or a canonical enemy core address. A callback gap permits an inference about the agent's own suppression; it is not a newly revealed enemy-state flag. The controller must not pretend that its own WRITE's applied status confirms successful denial. [ObservationV2 and information boundary](../../AGENT_API_V2.md#e-observationv2).

The following must not drive policy selection:

- Opponent package paths, member names, manifests, role labels or fixture identities.
- `context.seed`, reconstruction of seeded placement, RNG-state prediction used as a location bypass, or future seed identities.
- Opponent source, external match artifacts, terminal winner data not available during play, or the frozen payoff table as an online lookup keyed by inferred fixture identity.
- True engine-owned enemy state or another policy's richer diagnostic history.

Public Ruleset geometry and the candidate's own core remain legitimate context. The issue is not forbidding every use of an address or a callback count; it is whether those values are used as lawful state evidence or as a shortcut to recognize a particular frozen package. Diagnostic logs may explain decisions after a match, but they must not feed additional information into the policy.

Ordinary own-state damage inspection is an available READ action with its normal cost. Adding a direct own/enemy damage oracle, a new global status field or a free identity signal would violate the fixed-mechanics scope. Existing opponent core inference and beacon assumptions must be shared by all matched variants and disclosed rather than selectively improved in the adaptive one.

## 8. Frozen ecology, hindsight and generalization

Use the unchanged E8 family as the **reference ecology**. Keep the natural evader, static opponents, phase-sensitive stress member and existing multi-process opponent. Do not remove awkward members, make EVADE8 move earlier, or add a specially convenient evader to rescue a policy. The singleton relocation census remains a strong limit on any claim about natural reacquisition.

Published E8 outcomes are now known. Reusing that ecology cannot be described as blind policy discovery, even if a future evaluation uses fresh hidden seeds. A policy chosen to fit those outcomes must disclose that exposure. Fresh seeds can prevent memorizing particular trajectories; they do not erase knowledge of deterministic opponent signatures.

There is a real tension between maximal ecology preservation and a claim beyond the frozen family:

- Keeping opponents exactly unchanged is the cleanest first capability contrast and the smallest authorized direction.
- Robustness to new opponents cannot be established from renamed/twin packages or additional seeds of the same deterministic behaviors.
- A separate, prospectively approved held-out policy ecology could address generalization with mechanics unchanged, but adding that population is a scope decision. This review does not design or create it.

The recommendation is to retain the E8 family for the initial attribution question and explicitly limit its eventual conclusion to that population. If the lead wants a wider claim, resolve held-out opponents before preregistration rather than add them after a favorable result. A family-only success could establish useful observation-driven adaptation in that ecology; it would not establish broadly learned opponent modeling or universal mechanic capacity.

Novel synthetic histories can check that the allocator responds to state changes rather than names. They cannot substitute for payoff evidence or held-out opponents, and need not become live qualification matches in this review.

## 9. What future evidence would mean

The following are design-level interpretation requirements, **not** registered hypotheses, thresholds or an exhaustive decision table.

| Possible future finding | Permitted conclusion |
|---|---|
| Adaptive policy beats historical agents, but an improved matched fixed policy performs as well | General tactical improvement; useful adaptation remains unestablished |
| Adaptive policy improves over one weak disabled setting but not the strongest matched fixed allocation | Comparator inadequacy; not a C demonstration |
| A precommitted schedule explains the gain without relevant observations | Scheduling/allocation advantage, not evidence for the claimed observation-conditioned policy change |
| Observations change allocation but no payoff advantage resolves | Behavior capability demonstrated; beneficial adaptation still unestablished, analogous to the distinction E8 preserved |
| Payoff advantage over the bounded fixed class survives matched adaptation-disabled and timing controls, with trace-supported policy changes | Supports C for the declared policy class, population and environment, subject to prospective decision rules and pathology checks |
| Early identification-and-commit explains all advantage | Supports at most the narrower within-match identification/selection claim; does not establish continuing revision |
| Advantage is only present in one seat or alongside stalled contact/immunity | A timing or interaction concern requires its own decision; payoff alone does not qualify the candidate |
| No qualified policy in the declared class gains | Limits that class; does not prove no capable agent can adapt or that a resource layer is necessary |
| Legal observable histories cannot distinguish states requiring different allocations before useful action is possible | A potential structural information/timing limit, only if demonstrated under an explicit model and competent alternatives—not inferred merely from negative payoff |

The user’s two alternatives—mechanics cannot support useful adaptation versus ADAPT8 was insufficiently capable—cannot be symmetrically settled by one failed successor agent. A positive attributed result supplies an existence witness. A negative requires competence evidence and a bounded explanation before it can support a structural limit. No finite selection of agents establishes impossibility over all policies.

For a structural explanation, future work would need to separate insufficient signal, insufficient decision time, unavoidable information costs, and a genuinely dominant fixed response in the chosen capability class. A weak estimator or badly timed implementation cannot support that claim. No such failure cause is inferred from the sealed E8 outcomes here.

## 10. Measurement and explanation requirements

The future payoff comparison should use the **same declared opponent population and aggregation** for every policy being compared. “Best fixed” could otherwise mean one globally selected fixed policy, a different hindsight best choice for each opponent, or an oracle switching by true identity. Those answer different questions. Recommend the strongest fixed policy across the matched class and frozen nonadaptive references under a common mixed-field objective as the primary conceptual benchmark; opponent-specific fixed responses explain the structure but are not a free online oracle.

A new policy is not a member of E8's original Π. Do not silently reuse E8's self-entry convention, historic diagonal values or U definition as if the focal population were unchanged. Future payoff population, mirror handling and the comparison of new versus historical policies must be explicitly defined before any new evaluation. No aggregation weights or result thresholds are selected here.

The mechanism explanation must establish a chain that can be audited:

1. The policy had particular **legally available evidence**.
2. That evidence changed the **allocation decision**, rather than only a tactical target address.
3. The changed decision produced a different use of actual offers.
4. The prospective payoff comparison attributes gain to that capability relative to competent controls.

Trace evidence supports the first three; randomized/matched prospective comparisons support the fourth. A persuasive individual trace is not a substitute for the payoff contrast. Nor does a payoff contrast alone establish the intended adaptive mechanism.

Existing authoritative SENSE action/result records and observation delivery reflections provide the physical evidence. Internal allocation/estimate state may be exposed through existing diagnostics where suitable, with a deterministic explanation of how it follows from observations. Any later diagnostic/instrument addition must be separately authorized and must not change agent inputs or engine mechanics. Canonical replay alone cannot establish callback-level knowledge. [Trace semantics](V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md), [trace specification](../../specs/v4_api_v2_trace.md), [replay boundary](../../REPLAY_SCHEMA.md#python-observation-capture-explicitly-out-of-scope).

Report evidence of spending and switching after first discovery separately from startup acquisition. Distinguish newly observed relocation, no result, missing callback, exhausted search and confirmed core. Address both seat orders and phase/callback-sensitive cases; keep detection distinct from hostile core contact.

Future statistical rules must consider uncertainty over selecting the strongest fixed comparator, not treat the observed winning fixed policy as known without uncertainty. The fixed class and its selection rule must be frozen before evaluation; evaluation results cannot become a tuning loop. Retain exact payoff/stability reporting and distinct-trajectory counts rather than convert deterministic characterizations into independent rate claims. None of E8's numerical decision thresholds is automatically adopted as an E9 adaptation threshold.

## 11. Interaction and companion discipline

An adaptive payoff gain would not upgrade D or F automatically. New policies can create different contact, capture, tick-limit, repair-immunity and seat behavior even with identical engine mechanics. These require prospective checks, together with callback/phase mechanism evidence before claiming a cause for a flag. E8's zero flagged transitions and H8-SEAT NEITHER remain historical results, not certificates for a new controller.

Keep **T8 whole-tick primary** because that is where the repeated-information premise was demonstrated. The existing T8L one-offer environment may be useful as a separately scoped diagnostic companion if the lead needs to know how dependent the new capability is on denial price. It is not necessary to create a new disruption rule or rerun the whole E8 channel experiment.

Do not require the adaptive policy to succeed under T8L to establish a scoped primary result, and do not use T8L success to rescue a primary failure. If used, the companion remains separately reported unless a new, explicitly authorized interaction question is specified. This review recommends no factorial claim and selects no companion execution plan.

Likewise, passive C8 and C8L stay intact as historical parent controls; reproducing channel substitution is not the new primary question. Any prospective use must have a stated purpose rather than expand E9 merely because the old four-condition machinery exists.

## 12. Decisions required before preregistration

| Decision | Recommendation or unresolved gate |
|---|---|
| Research variable | Change only observation-conditioned allocation capability; hold mechanics and shared tactics fixed |
| Initial adaptation dimension | Monitoring/reacquisition allocation within the existing attack posture; no new offense/defense mechanic |
| Policy class | Specify a bounded, capable fixed allocation/schedule class and the corresponding adaptive controller; presently unresolved |
| Common tactics | Declare and audit shared executor, geometry, memory and target/core logic; improvements belong to all matched variants |
| Capability evidence | Define legal behavioral qualification for observation gaps, relocation, revisable allocation and both seats; not performed here |
| Knowledge restrictions | No identity/seed/artifact bypass; distinguish state inference from fixture recognition |
| C claim | Separate early within-match identification from continuing revision; decide which is required before results exist |
| Population | Preserve frozen E8 reference family; either accept a scoped claim or prospectively authorize a separate held-out population |
| Primary benchmark | Best fixed member of a bounded class under the same mixed-field objective; historical agents are additional references |
| Instrument and attribution | Allocation-disabled and credible timing controls; binding of observed evidence to strategic decisions |
| Pathology and uncertainty rules | Specify prospectively; do not inherit candidate qualification or copy E8 thresholds without justification |
| Companion | Optional existing T8L diagnostic only if it answers an explicit question; no new rule and no implicit interaction claim |
| Freeze and exposure | Disclose published-result knowledge, fix policy/class before evaluation and prohibit tuning from evaluation results |

These are review gates rather than an implementation sequence. No seed protocol, sample size, matrix, policy pseudocode, numerical threshold, registered decision table or execution command is proposed.

The immediate next authorization, if the lead accepts this review, should be a **bounded policy/comparator specification and qualification design**, not another mechanic design and not automatic experimental execution. Implementation, qualification execution and preregistration each require their own concrete authorized scope. The resource/economic triangle remains a later hypothesis only if a specific structural shortfall is supported.

## 13. Source map and stop boundary

| Source | Use |
|---|---|
| [Approved E2–E8 synthesis](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md) | Direction change, unchanged A–G grades and narrow C gap |
| [E8 results](V6_E8_RESULTS.md), [sealed record](../../../tools/research/v6/e8/final_registered_result.json) | Preserved empirical statuses and scope; no recomputation |
| [E8 Revision 5](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) | Original ADAPT benchmark, singleton census, payoff definition and companion limitations |
| [E8 family freeze](V6_E8_FAMILY_FREEZE.md), [machine freeze](../../../tools/research/v6/e8/family_freeze.json) | Fixed environment, eleven-member ecology, shared behaviors and ADAPT8's one-way rule |
| [E8 mechanic-family review](V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md) | Branch A′, capability/fixture fingerprinting and hindsight concerns |
| [E8 active-sensing design review](V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md) | Denial-cost rationale, action-result authority and callback delivery |
| [E2–E6 synthesis](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md), [E7 audit closure](V6_E6_POST_HOC_FACTORIAL_AUDIT.md) | Previous capability limitations and scheduler/seat causal discipline |
| [Agent API v2](../../AGENT_API_V2.md), [API-v2 trace specification](../../specs/v4_api_v2_trace.md), [replay schema](../../REPLAY_SCHEMA.md), [architecture](../../../ARCHITECTURE.md) | Legal observation budget, diagnostic evidence and unchanged runtime boundaries |

The synthesis boundary was committed and pushed before this review. This new document is left for research-lead review, without a further commit or push. No runtime, agent, tooling, frozen file or result was changed; no new matches, seeds, analyses or preregistration were created. Stop here.
