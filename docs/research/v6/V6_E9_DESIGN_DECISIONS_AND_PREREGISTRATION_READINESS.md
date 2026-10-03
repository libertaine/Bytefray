# Bytefray V6 — E9 Design Decisions and Preregistration Readiness

**Date:** 2026-10-02. **Design status: comparator/analysis design complete →
READY FOR PREREGISTRATION DRAFTING.** The ten choices below are adopted from
the research lead's supplied request. This means ready to prepare the
prospective protocol;
it does not mean a complete protocol is frozen or experimental execution is
authorized. The original outstanding protocol inputs are listed in §4;
their subsequent acceptance and current readiness boundary are recorded below.
Requirement **C remains NOT ESTABLISHED**.

This addendum supersedes the earlier review's readiness assessment and the
capability record's comparator-design hold for this documentation scope. It
preserves those documents as historical records. It creates no preregistration,
analysis implementation, experimental seeds, payoff data or execution matrix.

**Subsequent drafting pass:** The research lead accepted this boundary and
authorized the [E9 preregistration draft](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md).
That draft carries §4 forward as nine explicit decision IDs. Its existence
does not satisfy protocol freeze or authorize payoff execution.

**2026-10-02 acceptance update:** The complete Q1/Q2 proposal is incorporated
in **Draft 3**, and **P9-1–P9-9 are formally ACCEPTED** under the research
lead's instruction to incorporate, check and record acceptance. This includes
`N=1,412`, simultaneous guarded row intervals, timing allowance `rho=0.10`
with the interval-width caveat, and the complete one-recovery/two-start cap,
external-infrastructure allowlist and outcome-blind recovery predicates.
The draft's §13 check records **READY FOR PREREGISTRATION FREEZE** and closes
the missing-proposal hold. Timing reproduction can lead to strict S
refutation or unresolved benefit at the `0.10` upper-bound boundary; it does
not force one primary label. Preregistration remains **NOT FROZEN**; the
analysis/collection instrument is not implemented/qualified; payoff execution
is unauthorized; Requirement C remains **NOT ESTABLISHED**.

## 1. Established baseline and claim

The starting boundary is `d3c97ba077e9019a69f46c1509210862d5c52f1f` on
`v6-research`, with a clean working tree before this addendum. The approved
[policy specification](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md)
and subsequent [capability qualification](V6_E9_CAPABILITY_QUALIFICATION.md)
already supply the bounded allocator. The committed qualification record
reports Q-C1–Q-C15 PASS, 53/53 focused checks, and a clean complete headless run
with 6,912 passed, 18 skipped and 3 deselected. These are existing qualification
results, not newly executed checks or evidence of competitive benefit.

The sealed E8 result and the copied E9 tactical source were rehashed for this
addendum and match the recorded raw-byte digests:

| Artifact | SHA-256 |
|---|---|
| [Sealed E8 result](../../../tools/research/v6/e8/final_registered_result.json) | `9b93c488af11c53220c63dc5407bffbab31fcb64721701a648918c9fd8fd2a3e` |
| [E9 tactical copy](../../../tools/research/v6/e9/tactics.py) | `369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc` |

> E9 asks whether legally observation-driven allocation changes produce
> benefit that competent fixed allocations and credible precommitted timing
> schedules cannot explain.

E6 established scoped opponent-dependent fixed choices; E8 showed that the
strategic distinctions survive its cleaner mechanic family. Neither result
establishes useful within-match revision. E9 addresses that remaining C gap
on unchanged T8 mechanics, for one qualified controller and the frozen E8
ecology. A positive result would remain bounded to that scope; a negative
would not establish that useful adaptation is structurally impossible.

## 2. The ten adopted design choices

| ID | Decision | Binding consequence for preregistration |
|---|---|---|
| D9-1 | **Any useful within-match revision** is the claim boundary. | One realized observation-conditioned revision can satisfy the behavioral concept. Repeated or continuing revision is a later question; an early-commit comparator is outside this study. Repeated sensing alone never counts as allocation adaptation. |
| D9-2 | Use a **prospectively selected 16-schedule panel**. | Cover both clocks, both initial modes, single changes and repeated changes. Freeze canonical identities before payoff exposure. The conclusion concerns this panel, not the best of all 1,334 schedules or every possible timer. Exact panel identities are now accepted in Draft 3 §4. |
| D9-3 | Weight the **eleven frozen E8 opponents equally**. | Matched fixed/scheduled controls answer causal attribution. Frozen nonadaptive references answer competitive context. Report both layers separately under the same objective. |
| D9-4 | Use a **rectangular, paired design**. | Every evaluated row faces the same eleven opponents at the same seed positions in both seat orientations. Explicitly execute historical twin/self cells. Consolidate OFF/RUSH8, DENSE/REACQ8 and disabled-DENSE rows only after prospective equivalence verification for the exact evaluation artifacts. |
| D9-5 | Require **causal action consequence**. | Audit legal observation → allocation request → committed revision → a subsequent eligible action whose availability or choice differs because of that revision. Record masked revisions separately; selector state alone does not satisfy the behavioral gate. |
| D9-6 | Use a **prospective practical benefit margin and joint seed-block uncertainty**. | Choose the margin and uncertainty procedure before data. Resample complete paired seed blocks and recompute the strongest comparator within each resample. Keep behavioral evidence and payoff benefit as separate gates; E8's epsilon and 9/10 convention do not transfer. |
| D9-7 | Adopt the **four-way classification structure**. | Use SUPPORTED beneficial adaptation; Behavior demonstrated; benefit NEITHER; REFUTED bounded benefit claim; NOT EVALUABLE. Add the separate qualifier timing explanation unresolved when scheduled policies reproduce the gain. The precise ordered table is now accepted in Draft 3 §10; freeze it before implementation. |
| D9-8 | Treat **seat and interaction pathologies as interpretation constraints**. | Prospectively define severe seat dependence, stalling, immunity and phase artifacts. Ordinary opponent heterogeneity is reportable structure. A positive aggregate cannot override a severe concentration or artifact, and a valid pathology flag is not automatically a protocol-integrity failure. |
| D9-9 | Use **fixed sample size, no adaptive stopping and fresh E9 payoff data only**. | E6/E8 and qualification corpora may justify capability or design, but contribute no prospective payoff observations. Missing/corrupt cells require integrity handling; they never become synthetic ties or losses. |
| D9-10 | Keep **T8-only, frozen E8 ecology, one adaptive controller, four constants, 16 schedules and the historical reference layer**. | Hold mechanics, arena, shared tactics and opponents fixed. Exclude T8L, new mechanics, agent redesign, production/UI work and a focal-policy round robin. |

The allocator retains initial DENSE, confirmation threshold C=2, cooldown
L=2, revision budget B=4 and adaptive cadences 1/4. The four constant
allocations are OFF, DENSE, MEDIUM and SPARSE. The qualified schedule contract
retains its activation, parity, cooldown and skipped-wall-boundary semantics;
selecting a smaller panel changes the comparison scope, not these semantics.

The historical nonadaptive reference class is the ten frozen E8 members
other than ADAPT8. ADAPT8 remains one of the eleven opponents and a historical
adaptive reference if reported; it is never a fixed or nonadaptive comparator.
Neither the ten reference rows nor duplicate aliases receive extra opponent
weight. The eleven opponent identities remain intact after row consolidation.

## 3. Requirements for the prospective protocol and instrument

### Common payoff objective and comparator selection

The protocol must state the per-match payoff encoding and use one objective
for every row: average over the same seed positions, both seats with equal
weight, and all eleven opponents with weight 1/11 each. No per-opponent
hindsight selector is a primary comparator. No historical E8 diagonal value
or payoff estimate substitutes for a newly executed cell.

Report adaptive payoff and its gaps to the strongest matched constant,
strongest member of the 16-schedule panel, and strongest frozen nonadaptive
reference separately. The initial-DENSE disabled control supplies the direct
adaptation-disabled comparison, while all four constants protect against
manufacturing an advantage through a weak disabled default. The wording
“outperforms the best fixed policy” additionally requires the competitive
comparison with the strongest frozen nonadaptive reference; that broader
claim must remain distinct from matched causal attribution.

In each uncertainty resample, the seed position is the block: keep every
policy row, opponent and seat associated with that position together, use
the same sampled positions for all contrasts, and reselect each benchmark's
strongest member inside the resample. The observed winning comparator must
not be held fixed across resamples. The protocol must define the interval or
decision construction, joint treatment of required contrasts, ties and exact
margin inequalities before the instrument is implemented.

### Realized behavior

For each claimed realized revision, retain the legal delivered verification
receipt, selector prestate, request and its observation provenance, cooldown
and budget state, committed mode, and the action consequence. A delayed
commit must refer to the earlier request that caused it. Attribute the action
difference to allocation using the common executor and a declared diagnostic
comparison; selector diagnostics must never become additional policy inputs.

Distinguish eligible actions from suppressed callbacks and absent future
callbacks. Changing cadence does not change an already-running search's
traversal. A revision masked by that search, another tactical priority,
suppression or termination is recorded but does not count until an eligible
action actually differs. Scripted capability traces establish possibility;
the prospective E9 traces must establish realization in the evaluated field.

### Classification and interpretation

The following meanings are adopted; the exhaustive numerical mapping remains
a preregistration input, not an analysis rule created by this addendum.

| Classification | Meaning to preserve |
|---|---|
| **SUPPORTED beneficial adaptation** | Realized observation-driven action change and practical payoff benefit pass their separately registered gates, with matched fixed/disabled and scheduled controls excluding the declared alternatives. Apply interaction constraints and name the bounded ecology/policy/panel. |
| **Behavior demonstrated; benefit NEITHER** | Realized behavior passes, but uncertainty does not resolve the registered bounded benefit claim. A point estimate alone cannot upgrade it. |
| **REFUTED bounded benefit claim** | Valid prospective evidence meets the registered refutation rule for the specified practical benefit. This is not a claim of impossibility for other controllers or mechanics. |
| **NOT EVALUABLE** | Required integrity or evaluability conditions fail under the registered rules. Missing/corrupt evidence cannot be converted into an ordinary payoff outcome. |

**Timing explanation unresolved** is a separate qualifier when a scheduled
policy reproduces the gain under the registered comparison. It prevents a
timing-compatible gain from being presented as an attributed observation
benefit. The protocol must define “reproduces,” the qualifier's exact trigger,
and its interaction with the four labels. It must also explicitly classify
valid data with no realized revision, rather than confusing absent behavior
with missing evidence.

Report seat-specific and opponent-specific results, contact and capture
behavior, tick-limit/stalling outcomes, immunity evidence and relevant phase
patterns. Predefine when they narrow or prevent the aggregate claim. Preserve
distinct-trajectory counts so deterministic duplication does not imply extra
independent evidence. A valid finding concentrated in particular opponents
does not automatically fail the study. No D/F upgrade or product promotion
follows from a C result.

## 4. Original protocol inputs — now resolved by accepted Draft 3

At the initial design-direction pass, the supplied request omitted the exact
entries below and no panel was found in the checkout. This table preserves
that original checklist. The subsequently supplied complete proposal resolves
every entry in accepted Draft 3 §§3–11; its §13 verification supplies the
current freeze-readiness assessment. No missing rule was invented or inferred
from payoff data.

| Entry | Required prospective completion |
|---|---|
| Schedule panel | List sixteen distinct canonical identities: clock, initial mode and complete boundary tuple. Verify membership in the qualified class and the approved coverage of clocks, modes and single/repeated changes. |
| Evaluation roster and aliases | Bind exact package/default bytes, historical primary/twin usage, equivalence evidence, row alias mapping and the handling of self/twin cells to the rectangular design. |
| Payoff and benefit | Fix per-match encoding, practical margin(s), the required causal and competitive contrasts and exact support/refutation inequalities. |
| Uncertainty | Fix confidence or decision level, resample count, deterministic resampling convention, joint contrast rule and comparator tie handling. |
| Sample and seed protocol | Fix the number of fresh seed positions, their prospective generation/commitment and exposure sequence, independence from prior corpora and complete-cell accounting. No seed is generated here. |
| Behavioral gate | Fix the diagnostic action-consequence method, denominator and minimum realization requirement; define outcomes when valid data show no realized adaptation. |
| Interpretation constraints | Define severe seat dependence, stalling, immunity and phase artifacts quantitatively, including denominators and exactly how each limits a claim. |
| Decision table | Map all gate combinations to the four labels; define timing reproduction, qualifier precedence, integrity failure and unevaluable cases without overlap or gaps. |
| Integrity handling | Fix missing/corrupt/duplicate-cell detection, halt/disposition rules and any prospectively permitted recovery. No discretionary replacement or silent imputation is allowed. |

These entries were protocol completion requirements, not reasons to reopen
mechanic design. They are now incorporated and accepted. Issuing the protocol
freeze identity remains a separate step before instrument implementation
and independent qualification.

## 5. Remaining technical gate and stop boundary

After the preregistration fixes estimands and classification rules, implement
and independently qualify the E9 analysis instrument **before experimental
data generation**. Qualification must cover complete-block pairing and
comparator reselection, the behavioral action-consequence gate, both seats,
explicit self/twin and alias handling, integrity rejection, decision-table
boundaries and timing/pathology qualifiers. Synthetic instrument fixtures
must remain separate from fresh E9 payoff estimates. The existing Q-C1–Q-C15
qualification does not qualify this future analysis instrument.

The sequence is: complete and freeze the prospective protocol; implement and
qualify its instrument; only then pass the execution boundary under explicit
research authorization. This documentation pass stops before those stages.
No experiment, new qualification match, bootstrap analysis or payoff
selection was run. Frozen E8 files, the approved policy specification, the
capability record, executable/test files and local settings remain unchanged.
This addendum is left uncommitted for review.

## 6. Source map

| Source | Use |
|---|---|
| Research lead's ten-decision request supplied on 2026-10-02 | Adopted design choices and remaining instrument sequence; exact missing values are identified in §4 |
| Complete Q1/Q2 proposal and authorized procedural acceptance pass, 2026-10-02 | Exact P9-1–P9-9 rules incorporated and accepted in Draft 3; current freeze-readiness check, with no freeze or execution authorization |
| [Branch A′ review](V6_E9_BRANCH_A_ADAPTATION_DESIGN_REVIEW.md) | Original causal/comparator scope and historical readiness assessment |
| [Approved policy specification](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md) | Unchanged allocator, tactical contract, clocks and canonical schedule class |
| [Capability qualification](V6_E9_CAPABILITY_QUALIFICATION.md), [machine record](../../../tools/research/v6/e9/qualification_record.json) | Existing capability evidence and limitations; no payoff qualification |
| [E8 family freeze](V6_E8_FAMILY_FREEZE.md), [E8 preregistration](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md), [E8 results](V6_E8_RESULTS.md) | Frozen ecology/mechanics and historical evidence; no transfer of E8 numerical rules or diagonal values |
| [E2–E8 synthesis](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md) | Scoped research chain and unchanged Requirement C / D / F boundaries |
