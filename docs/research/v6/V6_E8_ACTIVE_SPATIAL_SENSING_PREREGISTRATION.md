# Bytefray V6 E8 — Active Spatial Sensing: Pre-Registration

**Status: APPROVED FOR FREEZE by the research lead on 2026-09-30**, after revision 1 and two precision edits made at the freeze review: the bootstrap wording, and delivery after suppression. **Revision 2**, which corrects and disambiguates the registered semantics before any transcription or code, **Revision 3**, a narrow correction of when initial acquisition ends, **Revision 4**, a narrow registration of when the E8 trace fields are present, and **Revision 5**, which makes its SENSE status mapping explicit, were approved by the research lead on the same day. **Revision 5 governs; revisions 1 (`28925fd`), 2 (`090d11e`), 3 (`00fb420`) and 4 (`ae37cf9`) are historical provenance** (below).
- **Its standing.** This markdown is the authoritative registered wording.
- **What comes next.** The E6-style transcription and freeze phase, still before any seed or matrix cell:
  - the machine-readable pre-registration;
  - the totality and invariant tests;
  - the implementation plan;
  - the experiment identities.
- **What exists.** No Ruleset, code, agent, seed list, match or probe.
- **What approval does.** Once approved, this text becomes the E8 registration boundary. At implementation it is transcribed into `tools/research/v6/e8/preregistration.json`, and a test asserts that the two agree. That JSON is digest-pinned and frozen with the analysis instrument before any matrix cell runs.
- **Which wording governs.** This markdown is the authoritative wording.

**Revision 1 (2026-09-30)**, after the research lead's first review:
- **R-9's 1/20 is deleted.** The seat criterion is redesigned as two layers that use sign and stability only (§6.2).
- **H8-CHANNEL's five members** are defined as a frozen acquisition-policy candidate set, with the full eleven-member field as opponents (§3.1).
- **ADAPT8's k = 2 is derived structurally,** as one complete scheduler-phase cycle. Appendix A.4 becomes a validation. *(That rationale is withdrawn in Revision 2; see R-8.)*
- **D8-3's equality is defined exactly.**
- **Trace roles are exact.** `sensed_anchors` is authoritative, `previous_sense_anchors` only reflects it, and the registered window is recorded per match (§10, D8-15).
- **The research answer's four outcomes are defined explicitly**, and requirement C is kept separate (§7.4).

**Revision 2 (2026-09-30)**, approved by the research lead before any transcription or code. **It corrects the registered member semantics, and disambiguates them and the analyzer's labels.** These are substantive corrections, not transcription clarifications, so revision 2 superseded revision 1. It is itself superseded by revision 3. No hypothesis, threshold, set, condition or cell count changes. R-8's value stands, and its rationale is replaced.
- **Its history.** Revision 1 was registered at `28925fd` with SHA-256 `6d50dae648dbdb0def2bcb94644e0705b4d62d4e818f7288190df4f8fac4efbb`, and is preserved there as historical provenance. This revision was drafted on `v6-research` at `eb60a11`. **Its own digest is recorded in the machine-readable pre-registration and its freeze record**, because a document cannot contain its own digest.
- **Re-acquisition precedence** (§3.2). A re-acquisition search in progress takes precedence over the posture steps until it terminates. Under revision 1's order of an offer, the search could not pass its first window (§14, item 9).
- **ADAPT8's count** is of consecutive verification observations, and a tick with no verification is unobserved. k = 2 is re-derived as the minimum repeated confirmation, and revision 1's scheduler-cycle rationale is withdrawn [R-8].
- **Knowledge is exact** (§2.5, §3.2):
  - the known set is defined for each mode, inside the family policy only;
  - the last-known anchor is set from it as E6 set it from visibility;
  - knowledge updates, missing addresses and matching follow registered rules;
  - the `once` row is aligned, and **a channel difference is registered**.
- **STRESS8's repair** writes the core beacon (§3.2).
- **Appendix A.4** is scoped to a scripted evader that does not disrupt ADAPT8.
- **The census is re-derived** under these semantics (§3.5).
- **KC8-6's label is total** over any number of universal A8 members (§8). §7.2's H8-CHANNEL qualifier names them the same way.
- **R8-NO-CHOICE's H8-TAX qualifier texts are registered** (§7.1).
- **D8-3's matched pairs exclude LURK8 and GREED8 as opponents**, which leaves nine literal same-opponent comparisons (§5.1).
- **Three conventions that were cited by reference are now stated in full:** the callback index (§3.2), the quantile rule (§6.2), and O-BOOT's draws and their joint application (§4).
- **The records cited by abbreviation are resolved** in the governing records below.

**Revision 3 (2026-09-30)**, approved by the research lead before any engine or agent code. **It is narrow.** No hypothesis, threshold, set, condition, cell count or registered outcome criterion changes. It is itself superseded by revision 4.
- **Its history.** Revision 2 was registered at `090d11e` with SHA-256 `0c6d0b741a4584ac10bc5f2aa3837bbc83213b8a608352d86949bdf809737286`, and is preserved there as historical provenance, as is revision 1. This revision was drafted on `v6-research` at `7974e2a`. **Its own digest is recorded in the machine-readable pre-registration and its freeze record.**
- **Initial acquisition ends once the enemy core is confirmed** (§3.2), in the research lead's words. Under revision 2, SPLIT8's sensor resumed sweeping under the controls whenever the visible set emptied, even after its entrant knew the enemy core, which departed from E6. Re-acquisition stays a separate state, with revision 2's precedence. The guard-posture channel difference is unchanged.
- **The census is re-derived** under these semantics (§3.5).
- **DR is defined** in the governing records.
- **Appendix A.2 is corrected** to 17 READs under E6's verification order.

**Revision 4 (2026-09-30)**, approved by the research lead after the parent goldens were pinned (phase I8-1) and before any engine code. **It is narrow: it registers when each E8 trace field is present** (§10). No hypothesis, threshold, set, condition, cell count, member semantics or registered outcome criterion changes. It is itself superseded by revision 5.
- **Its history.** Revision 3 was registered at `00fb420` with SHA-256 `a822bd15d9be8f968facb2f7b9c7e228d0e59b65ce34b790ae2a9e3538583a5a`, and is preserved there as historical provenance, as are revisions 1 and 2. This revision was drafted on `v6-research` at `2cfd4e8`. **Its own digest is recorded in the machine-readable pre-registration and its freeze record.**
- **Why it was needed.** The I8-1 parent goldens pin C8 and C8L traces in which no E8 field appears, and D8-15 said that every C8 and C8L `ResetRecord.sensing_window` is `null`. An absent field and a field present as `null` are different serialized states, so both could not hold.
- **Absent and `null` are distinct** (§10). Under the controls, the E8 fields are omitted, never serialized as `null`, so the parent goldens stand unchanged. Under T8 and T8L, each field is present exactly where its semantics apply. An empty SENSE result is an explicit empty list, and a refused SENSE is an explicit `null`.
- **The gates check presence both ways, on every cell, and fail closed** (§5.1). D8-1, D8-13 and D8-15 check it, and for presence D8-1 and D8-13 are also evaluated on the controls. D8-3's equality compares it. No rule reads an absent field as `null` except where §10 says so.
- **Serialization compatibility is registered** (§10).
- **It changes no member semantics**, so no input of §3.5's census changes.

**Revision 5 (2026-09-30)**, approved by the research lead before Revision 4 was published and before any engine code. **It makes one point of Revision 4 explicit: the status mapping of a SENSE record** (§10). No hypothesis, threshold, set, condition, cell count, member semantics or registered outcome criterion changes. **This revision governs.**
- **Its history.** Revision 4 was registered at `ae37cf9` with SHA-256 `8a9971a0630f85291e41034a07940cdf915e97cde4c87fb133dcb6bca8ae63fa`, and is preserved there as historical provenance, as are revisions 1 to 3. This revision was drafted on `v6-research` at `4b3a212`. **Its own digest is recorded in the machine-readable pre-registration and its freeze record.**
- **Why it was needed.** Revision 4 said that a SENSE record's `sensed_anchors` is `null` "if it was not applied". The trace's status vocabulary also includes `EXCEPTION`, so that phrase let a `null` stand for an integrity failure as well as an ordinary refusal.
- **Each status is mapped explicitly** (§10). `null` means only that there is no applied sensing result, and the status says why. Only `REJECTED_OUT_OF_REACH` is an ordinary refused SENSE.
- **D8-14 covers every status other than `APPLIED` and `REJECTED_OUT_OF_REACH`** (§5.1, §12). Revision 4's D8-14 named only `REJECTED_INVALID`, so `EXCEPTION` is now a hard stop too.

**Branch:** `v6-research` at `ae6c7f7` ("docs(v6): add the E8 active spatial sensing design review"), pushed.
**Date:** 2026-09-30
**Governing records:**
- [`V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md`](V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md) (**E8-DR**), the E8 design boundary: GO WITH CONDITIONS, with the rulings in its §N–§O;
- [`V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md`](V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md) (**E8-MF**), §N;
- [`V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md) (**SYN6**): invariants E8-I1 to E8-I5, and §H's lessons;
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR6**), whose operationalizations, blindness protocol and evidence rules are reused where stated.
- **Records cited by abbreviation** [Revision 2]:
  - **PA** is [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md), the E6 post-hoc factorial audit;
  - **E6-R** is [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md), the E6 results record;
  - **A1, in §3.2**, is [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md), E6's first amendment, with its corrections C-1 to C-3. **It is distinct from A1 containment** (§13), E8-DR's research-containment option;
  - **the E6 implementation plan** is [`V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md`](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md);
  - **DR** is [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md), the E6 priced-sensing design review, cited in §9 and Appendix A.1 [Revision 3].

**The boundaries carried forward unchanged** (the research lead, 2026-09-30):

| # | Boundary | Where |
|---|---|---|
| B-1 | Whole-tick disruption is the primary parent | §2 |
| B-2 | λ = 1 is the companion only: a status comparison, never a verdict | §2, §6.6 |
| B-3 | No T8+ | §2 |
| B-4 | No purpose-built relocator | §3.1 |
| B-5 | The H8-REPEAT census is fixed from frozen behavior, before outcomes | §3.5 |
| B-6 | Requirement C is scoped to that census if it collapses to one defender stratum | §3.5, §7.3 |
| B-7 | The acting callback's `decision_v2` record is authoritative for the sensing result | §10 |
| B-8 | The window of ±27 and its traversal semantics are frozen together | §2.4, §2.5 |
| B-9 | A1 research containment, with incompatible pairings rejected before the match | §13 |
| B-10 | A3 is required before any product promotion | §13 |
| B-11 | The seat criterion is designed afresh on principle, not copied from E6 | §6.2 |
| B-12 | The product-level closure of seed inference remains a promotion prerequisite | §9, §13 |

---

## 0. Registration Decisions

**The research lead's first review (2026-09-30)** approved R-1 to R-8 and R-10 to R-12, R-8 with the structural derivation below, and rejected R-9's 1/20, which is revised below. **The freeze review (2026-09-30) approved revision 1, with the two precision edits noted in the status line.** Revision 2 replaces R-8's rationale, keeping its value, and changes no other decision in this table. Revisions 3 to 5 change none. Markers **[R-n]** in the text refer to this table.

| # | Decision | Drafted value | Rationale |
|---|---|---|---|
| **R-1** | Experiment identity | **E8.** Tooling under `tools/research/v6/e8/`. | Continues the V6 numbering. E7 is closed, with no experiment (SYN6 §C.3). |
| **R-2** | Window half-width *w* | **27** | Price-matched to E6's MOVE sweep: at most 7 actions, expected 4 against 1537/385 ≈ 3.99 (E8-DR §C.2). Frozen with R-3. |
| **R-3** | Coverage and traversal semantics | As in §2.4–§2.5 | The expected costs depend on the traversal order (E8-DR §C.2) |
| **R-4** | Tolerance ε | **1/16** | PR6 O-3, reused unchanged |
| **R-5** | Bootstrap | **1000** resamples, with a stability bar of **9/10**, from `random.Random(42)` | PR6 O-4, reused unchanged |
| **R-6** | Forced-line tick bound | **≤ 3** | PR6 O-5, reused. Discovery still completes within tick 1 at worst (7 ≤ 8), exactly as under E6's sweep (E8-DR §C.5). |
| **R-7** | Seeds per cell | **32** | As in E2–E6 |
| **R-8** | ADAPT8's run of consecutive confirming verification observations before it stops verifying [Revision 2] | **k = 2** | **The minimum repeated confirmation** [Revision 2]: one verification observation establishes the anchor's current location, and a second, later one confirms that it persists. **A tick with no verification is unobserved and ignored.** Revision 1's rationale, that two consecutive ticks form one complete scheduler-phase cycle covering both seat orders, **is withdrawn.** Under whole-tick disruption a re-hit process acts only on ticks of its own seat's parity for stretches of a match (PA §8), so two successful verifications can fall on the same parity. Appendix A.4 **validates** the value against a scripted responsive evader; that validation is not its derivation. Freeze tests cover both seat roles and all suppression patterns (§3.2). |
| **R-9** | The family seat-shift status | **No magnitude threshold.** Sign, plus the 9/10 stability convention (§6.2). The magnitude is reported. | A cutoff such as 1/20 would be a new effect-size boundary with no causal or design reason. **Revised at the research lead's direction (2026-09-30).** |
| **R-10** | The members | **Eleven.** No evading attacker is added. | An evading attacker would widen the H8-REPEAT census beyond one defender archetype, but adding a member to widen a census risks engineering it. The predicted census is therefore one archetype, and C is scoped accordingly (§3.5). The alternative, a twelfth member (RUSH8 with evasion on), is for the research lead. |
| **R-11** | Evasion magnitude | *m* uniform on the integers **[8, 64]**, with a seeded sign | PR6 §12, item 8 (E6 plan decision P-2), reused |
| **R-12** | The trace field names | As in §10, including `ResetRecord.sensing_window` | They must be frozen here (B-7). `sensing_window` records the registered window actually used (D8-15). |

---

## 1. Research Question and Claim Scope

**The question**, in the research lead's words (E8-MF §N):

> **Can an explicit spatial-sensing action, competing directly for the per-tick action opportunity, create repeated opponent-dependent acquisition choices without collapsing into a universally dominant search strategy?**

**The registered form of the question** (§7.4). E8 answers it as **exactly the conjunction of three registered components**:
- **H8-SUB**, an opponent-dependent choice under the treatment;
- **H8-REPEAT**, re-acquisition that pays against the census, which is the repeated choice;
- **H8-CHANNEL**, no universally dominant acquisition policy.

**Requirement C is a separate registered conclusion** (H8-ADAPT, §7.3). A repeated opportunity to re-acquire is not by itself an adaptive policy that recognizes state and changes behavior.

**What E8 manipulates.** One Ruleset field, `sensing_mode`, on an E6 treatment parent. It is **a mechanism substitution**: passive enemy-anchor visibility is replaced by a paid sensing action (E8-MF §N, ruling 2). **Every registered reading claims only what that substitution did, under that parent and this family** (§7).

**The claim's scope**, in the research lead's words (E8-DR §H.2), and carried verbatim into every reading of H8-REPEAT:

> If H8-REPEAT succeeds under the whole-tick parent, E8 demonstrates repeated adaptation in an ecology where disruption makes reacquisition valuable. It does not establish that active sensing creates repeated adaptation independently of disruption economics.

**Parenthood confers no candidate status on E6** (E8-MF §N, ruling 3). E6's REJECT stands.

Every registered reading is reachable, including "no registered interpretation row applies", "not evaluable" and the rejection outcomes of §8.

---

## 2. Treatment and Conditions

### 2.1 The treatment field

`RulesetPolicy.sensing_mode` takes the value **`"passive"`** or **`"active"`**.
- **`"passive"`** is the default. It reproduces every existing Ruleset byte for byte, including both E6 treatment Rulesets.
- **`"active"`**, set only on E8's treatment Rulesets:
  - `visible_enemy_anchor_addresses` is **empty at every callback**;
  - the sensing action of §2.3 is **available**;
  - the half-width *w* = 27 [R-2] is a Ruleset constant.

`detection_radius` keeps its value in each Ruleset. Under `"active"` it is inert, because passive visibility is off.

### 2.2 The conditions

| Condition | Ruleset | Parent | Only difference |
|---|---|---|---|
| **C8** | `bytefray-rules-6-research-sensing-r32`, T-E6's Ruleset, **unchanged** | — | — (the primary control; whole-tick disruption) |
| **T8** | provisional `bytefray-rules-6-research-sensing-active-w27` | C8 | `sensing_mode = "active"` |
| **C8L** | `bytefray-rules-6-research-disruption-slot1-sensing-r32`, T-E6L's Ruleset, **unchanged** | — | — (the companion control; λ = 1) |
| **T8L** | provisional `bytefray-rules-6-research-disruption-slot1-sensing-active-w27` | C8L | `sensing_mode = "active"` |

- **Fixed across all four conditions:** arena 512, tick limit 1000, Q = 8, chunk 2, rotation, K = 1, seeded placement, `core_base` spawn and forward pass order. C8 and T8 use whole-tick disruption. C8L and T8L use λ = 1.
- **The arms.** The primary arm is C8 → T8 [B-1]. The companion arm is C8L → T8L. **It is a status comparison, never a verdict** [B-2] (§6.6).
- **No T8+** [B-3]. Passive visibility together with the sensing action is not a condition. E8-DR §H.1 gives the reason: its passive layer is predicted near-inert, so it cannot isolate automatic from paid sensing.
- **The provisional Ruleset identifiers** are fixed at implementation, and recorded in the freeze record before any seed exists.

### 2.3 The sensing action (a Ruleset invariant)

| Property | Registered semantics |
|---|---|
| Form | `ActionKindV2.SENSE`, with wire value **`"sense"`** and one integer operand, the target *t*. It carries no `value`. |
| Normalization | *t* mod 512 |
| Reach | **Applied** if and only if the circular distance from *t* to the acting process's anchor is ≤ that process's declared reach. Otherwise it is **rejected**, with status `REJECTED_OUT_OF_REACH` and `previous_action_applied` false, as for READ. |
| Result | The **ascending tuple of distinct positions** *p* of the processes of every *other live* entrant, such that the circular distance from *p* to *t* is ≤ 27. Positions are taken at the instant the action executes. Co-located anchors appear once. |
| Circular distance | *d*(*x*, *y*) = min(*r*, 512 − *r*), with *r* = \|*x* − *y*\| mod 512. **The comparison is inclusive**, so the window is 55 cells. |
| Price | One offer, charged in the quota exactly as a READ |
| Effect on match state | **None**: no memory write, no position change, no disruption, no territory |
| Exposure | **None.** The sensed entrant learns nothing (E8-DR §B.4, X0). |
| Delivery | At the **acting process's next callback**, `ObservationV2.previous_sense_anchors` holds the tuple. It is `None` if that process's previous action was not an applied SENSE. After a SENSE, `previous_read_value` and `previous_read_owner` are `None`. |
| Under `"passive"` | SENSE is not accepted. In the matrix it cannot occur, because the pre-match compatibility gate of §13 refuses every pairing in which it could. |
| Suppression | No new rule. A suppressed process gets no callback, so it cannot sense (E8-DR §B.3). |

### 2.4 Coverage semantics (frozen with *w*) [R-2, R-3]

A window centered on *c* covers exactly the 55 cells *x* with *d*(*x*, *c*) ≤ 27.

### 2.5 Traversal semantics (member semantics, frozen with *w*) [R-3]

These are the orders in which the family's acquiring members spend sensing actions under `"active"`. They are registered here because the expected costs depend on them (Appendix A).

- **The discovery traversal.**
  - While no enemy anchor is known, the member's successive sensing actions are centered on *c_k* = (`own_core_base` + σ · (91 + 55*k*)) mod 512, for *k* = 0, 1, …, 6.
  - σ ∈ {+1, −1} is drawn once per match from the member's seeded stream, as E6's search direction was.
  - The seven windows tile the 385-cell arc [own + 64, own + 448] exactly.
  - The traversal **stops at the first result containing an enemy anchor**.
  - If all seven are empty, the traversal restarts at *k* = 0. That can happen only if every enemy anchor has left the arc.
- **The re-acquisition traversal** (members with `reacquire` of `repeat` or `adaptive`). Given the address *a* of a known enemy anchor, the successive windows are centered on *a*, then *a* + τ · 46, then *a* − τ · 46. Under `"passive"` the member MOVEs toward the same centers (§3.2). [Revision 2: revision 1 said "the last known address", a phrase now reserved for E6's last-known anchor, §3.2.]
  - τ ∈ {+1, −1} is drawn per traversal from the member's seeded stream.
  - The traversal stops at the first result containing an enemy anchor. **The missing *a* is then replaced under the matching rule below** [Revision 2].
  - **If all three are empty, the anchor becomes unknown.** The member then continues with its no-anchor behavior (§3.2).
- **Verification** is a sensing action centered on *a*. It is the re-acquisition traversal's first window.
- **Knowledge updates and matching** [Revision 2]. These rules distinguish "not observed, because the member did not look there" from "looked there, and it is gone":
  - **A SENSE result updates knowledge only within the circular window actually sensed:** the 55 cells within 27 of its target (§2.4).
  - **Every address the result returns becomes known.**
  - **A previously known address inside that window which is absent from the returned result becomes missing.**
  - **A known address outside that window is unchanged.**
  - **Under `"passive"`, the tracked set at each callback is the visible set of the entrant's previous callback.** A tracked address absent from the current visible set becomes missing.
  - **If more than one missing address requires re-acquisition, they are serviced in ascending numeric-address order.**
  - **A missing address is replaced by the returned address at minimum circular distance from it, the lower numeric address on a tie.** Under `"passive"`, the returned addresses are the visible set.
  - **When verification needs a single anchor and several are known, it is centered on the lowest numeric address.**
  - Wherever "lowest" orders a set of addresses, the order is ascending numeric address. These rules are registered so that behavior stays deterministic, even where the frozen family may never exercise them under T8 or T8L.

---

## 3. Population

### 3.1 Members [R-10]

**One policy source, parameterized.** Each member is an **allocation policy**, not an action stream. Under each condition it acquires through that condition's own channel (§3.2).

| Member | `acquire` | `reacquire` | `posture` | `evade` | `processes` | Role |
|---|---|---|---|---|---|---|
| **RUSH8** | spatial-fast | once | attack | off | 1 | The high-acquisition baseline |
| **REACQ8** | spatial-fast | repeat | attack | off | 1 | **The H8-REPEAT twin:** it differs from RUSH8 only in `reacquire` |
| **PACED8** | spatial-paced | once | attack | off | 1 | A lower-acquisition twin: it differs only in `acquire` |
| **STEALTH8** | ownership | once | attack | off | 1 | The channel contrast: READ only |
| **LURK8** | none | — | attack | off | 1 | The no-acquisition twin: it differs only in `acquire` |
| **SPLIT8** | spatial-fast (sensor) | once | attack | off | 2 (sensor 1/4, striker 3/4) | Division of labor |
| **GUARD8** | spatial-fast | once | guard | off | 1 | The stationary defender |
| **EVADE8** | spatial-fast | once | guard | **on-hit** | 1 | **The naturally evading defender.** It differs from GUARD8 only in `evade`. |
| **GREED8** | none | — | paint | off | 1 | Greed |
| **ADAPT8** | spatial-fast | **adaptive** | attack | off | 1 | Requirement C (secondary to the main rows; §5.3) |
| **STRESS8** | none | — | guard | off | 1 | **The tick- and callback-keyed stress member** (E8-I4). It is separate from ADAPT8 (E8-DR O-9). |

- **Which sets are used where.**
  - **Π_F**, the candidate best responses, is every member except ADAPT8, as in PR6 §3.1.
  - **Π**, the opponent set, is every member.
  - **A8, the frozen acquisition-policy candidate set**, is {RUSH8, REACQ8, PACED8, STEALTH8, LURK8}. It is used by H8-CHANNEL.
    - **Why these five.** They are the comparable single-process policies whose relevant strategic difference is **how and when they acquire information**: posture, processes and evasion are fixed across them.
    - **What the restriction does.** It is methodological: defenders cannot become a universal best response for reasons unrelated to the acquisition-channel question.
    - **Its opponents are the complete eleven-member field Π.**
    - **The set is frozen with the family, and never changed after outcomes exist.**
- **No purpose-built relocator** [B-4]. EVADE8's evasion is role-justified under the primary parent. A hit there costs its victim 6 or 8 offers, and the evasion costs one (E8-DR §C.4).
- **Members sensitive to callback or tick phase.** These must stay in the family and be reported as a stratum (§6.3). They are never excluded (E8-I4):
  - PACED8, which paces on callback index;
  - EVADE8, which infers hits from callback counts;
  - ADAPT8, whose verification timing follows the rotation;
  - STRESS8, whose check is keyed to tick and callback index.

### 3.2 Registered parameter semantics

**The order of an offer.** For each posture, an offer goes to the first applicable step:
- **attack:** disrupt a known enemy anchor not yet written this tick; then write the enemy core by the cyclic cursor; then a verification READ; then **acquisition**; then paint.
- **guard:** disrupt a known enemy anchor not yet written this tick; then **acquisition**; then repair its own core by the cyclic guard cursor.
- **paint:** paint.

An offer is **acquisition-eligible** when the acquisition step is reached, no enemy anchor is known, and the entrant has not confirmed the enemy core (discovery) [Revision 3]. **Re-acquisition does not wait for the acquisition step:** it takes precedence over the posture steps (below) [Revision 2].

**Initial acquisition and re-acquisition** [Revision 3]. The research lead's rule, verbatim:

> **Initial acquisition ends once the enemy core is confirmed. Loss of current passive visibility alone does not restart initial acquisition.**
>
> **Re-acquisition is a separate state.** If a previously tracked anchor becomes missing under the registered knowledge rules, a member that supports re-acquisition begins the registered re-acquisition search. Once started, that search retains the precedence established in Revision 2 and continues until replacement or exhaustion.
>
> **SPLIT8:** its sensor performs the initial passive sweep until acquisition/core confirmation. After that it does not resume generic sweeping merely because the visible set is empty. It moves again only when a registered missing-anchor event starts re-acquisition. The striker remains non-moving.

How it applies:
- **The eligibility rule above carries it.** Discovery requires that the entrant has not confirmed the enemy core, by E6's confirmation as corrected by A1 C-2, or by A1 C-1's unverified adoption.
- **Before the enemy core is confirmed, initial acquisition has not ended.** Discovery then applies whenever no enemy anchor is known.
- **The members that support re-acquisition** are those with `reacquire` of `repeat` or `adaptive`. Their search starts as RP-3 below registers.
- **SPLIT8's `reacquire` is `once`** (§3.1), so no missing-anchor event starts a search for it. Once its entrant confirms the enemy core, its sensor does not move again.
- **No other member's behavior changes.**
  - In the attack posture, acquisition follows the core write in the order of an offer. With 8 offers a tick and 8 core cells, a core write is always available once the core is confirmed, so acquisition is never reached then.
  - The guard-posture members confirm no enemy core. They make no verification READ, and A1 C-1's adoption cannot fire at their first callback: under `"passive"` nothing is visible then (D8-7), and under `"active"` nothing is yet known. **So the registered channel difference below stands for GUARD8 and EVADE8.**
  - Under `"active"`, remembered knowledge already ended SPLIT8's discovery.

**Known enemy anchors** [Revision 2]. "A known enemy anchor", here and in §2.5, is an address in the member's entrant-wide **known set**. **It is family-policy knowledge, not engine visibility:**
- **Under `"passive"`, the known set is the current visible-anchor set** (`visible_enemy_anchor_addresses`). An address that leaves the visible set is no longer known.
- **Under `"active"`, it is the remembered result of SENSE, under §2.5's knowledge-update rules.** An address becomes known when an applied SENSE returns it, at delivery (§2.3), and remains remembered until a later applied SENSE replaces that knowledge. A refused SENSE changes nothing.
- **The substitution exists only inside the E8 policy.** For E8 family-policy decisions that E6 based on the visible-anchor set, the policy uses the mode-specific known-anchor set. **The actual observation field remains actual visibility:** under `"active"`, `visible_enemy_anchor_addresses` stays empty at every callback (D8-2).
- **The last-known anchor stays separate.** E6 keeps current visibility and a remembered last-known anchor apart, and centers its verification READs on the remembered one. E8 does not collapse the two. **E8 sets the policy's `last_known_anchor` from the mode-specific known set in the same circumstances in which E6 set it from visibility.** In the E6 family source, it is set to the lowest address at each callback whose set is nonempty, kept when the set empties, and cleared when the verification READ window is exhausted without an enemy core cell.
- **A passive `once` member may disrupt currently visible anchors, but never disrupts or moves toward a stale last-known address** that has left the visible set.

**A registered channel difference** [Revision 2]. **Under `"passive"`, losing current visibility can cause acquisition behavior to resume**, because, before the enemy core is confirmed, discovery applies whenever the known set, which is the visible set, is empty [Revision 3]. In C8 and C8L, GUARD8 and EVADE8, whose guard order puts acquisition before repair, therefore resume sweeping whenever they lose sight of the opponent, EVADE8 included after its own evasions. **Under `"active"`, remembered SENSE information persists under the knowledge-update rules, so a `once` policy does not automatically re-acquire merely because there is no current passive visibility.** This is a genuine channel difference, not an implementation artifact. It is stated beside the readings (§7.4).

**Re-acquisition precedence** [Revision 2], for members with `reacquire` of `repeat` or `adaptive`:
- **Once a re-acquisition search is in progress, its next acquisition action takes precedence over the posture steps until the search terminates:** the next SENSE under `"active"`, or the next MOVE under `"passive"` (§2.5).
- **While re-acquisition is in progress, the first offer of a later tick continues that search** rather than restarting verification of the stale address.
- **When it starts.** A search starts when a known address (under `"passive"`, a tracked one) becomes missing and the result that showed it missing gives no replacement under the matching rule (§2.5).
- **Termination.** A search ends when the missing anchor is replaced under the registered matching rule, or when the registered search sequence is exhausted, after which the anchor is unknown (§2.5). Under `"passive"`, the search's result at each of its callbacks is that callback's visible set, and the sequence is exhausted when the visible set on reaching the last center shows no enemy anchor.
- **The precedence is over posture actions only.** It does not override a separately registered member-level step, such as a pending evasion or damage-response action; those keep their registered priority. No member that re-acquires in the frozen family has such a step.
- **Why.** Under revision 1's order, the core write or the verification READ took every offer of a member that had found the enemy, so the search could not pass its first window, contrary to E-3 and Appendix A.3. **With precedence, re-acquisition consumes offers that could otherwise have attacked, defended or repaired.**
- **A consequence, recorded rather than hidden.** Under C8 and C8L, REACQ8 and ADAPT8 can chase a passive anchor that leaves visibility. O-REACQ reports every re-acquisition by cause.

**The callback index** [Revision 2] is the **1-based count of that entrant's callbacks within the current tick, reset when `current_tick` changes.** An entrant's first callback of a tick has index 1, and the count includes the callbacks of all its processes. This is the frozen E6 family's convention.

The posture, verification and core-cursor semantics are **E6's, as corrected by A1** (the E6 implementation plan §5.2, and A1 C-1 to C-3). Only the acquisition, re-acquisition, evasion, adaptive and stress semantics below are new. The implementation plan must transcribe all of them without change. Engine-level behavior tests against scripted non-family opponents verify them before the freeze (A1 §2; SYN6 §H, item 4).

| Parameter | Under `"passive"` (C8, C8L) | Under `"active"` (T8, T8L) |
|---|---|---|
| `acquire` = spatial-fast | E6's fast MOVE sweep (MOVE 64 · σ on every acquisition-eligible offer) | The next discovery-traversal SENSE on every acquisition-eligible offer (§2.5) |
| `acquire` = spatial-paced | E6's paced sweep: acquisition only on odd callback indexes, paint otherwise | The same pacing, with SENSE |
| `acquire` = ownership | E6's READ stride search | The same |
| `acquire` = none | No acquisition | The same |
| `reacquire` = once | Never re-acquires. It disrupts only known anchors, which under `"passive"` are the currently visible ones, **never a stale last-known address** [Revision 2]. | Never re-acquires. It disrupts its known anchors, the addresses its SENSE results returned. |
| `reacquire` = repeat | When a tracked enemy anchor becomes missing (§2.5), it MOVEs toward the re-acquisition centers of §2.5, in order, at most 64 per MOVE, **with precedence over the posture steps** [Revision 2] | **At its first offer of each tick after first discovery, before the posture steps, it verifies** (a SENSE centered on *a*), **unless a re-acquisition search is in progress.** A result showing *a* missing, with no replacement, starts the search, which continues on its next offers **with precedence over the posture steps** [Revision 2]. |
| `reacquire` = adaptive (ADAPT8) | As `repeat`, until **k = 2 consecutive verification observations** confirm the enemy anchor at *a* with no observed relocation; then as `once` for the rest of the match [R-8, Revision 2]. **A tick in which ADAPT8 receives no applicable verification callback is unobserved: it neither advances nor resets the count.** A first callback at which a search is in progress, or no anchor is known, is not an applicable verification callback. An observed relocation, meaning *a* found missing at a verification or at any other callback, resets the count to 0. Here a verification observation is the visible set at its first offer of the tick, which confirms the lowest tracked address if it contains it. | The same, but a verification observation is the result of its first-offer verification SENSE |
| `evade` = on-hit (EVADE8) | **At its first callback of a tick, it infers a hit** if either (i) `current_tick` > `last_callback_tick` + 1, meaning a whole tick passed with no callback, or (ii) it received fewer than 8 callbacks in the most recent tick in which it received any. On an inferred hit, that callback is a MOVE of σ_e · *m*, with *m* on [8, 64] and σ_e drawn from its seeded stream, fresh for each evasion [R-11]. **It repeats on every inferred hit.** | The same |
| `stress` (STRESS8) | At callback index 1 of each tick, before anything else, it READs own-core cell (*t* − 1) mod 8 (E6 ADAPT's P-4 schedule). If that cell's owner is not itself, **its next action repairs that cell with the normal core beacon value, identical to the guard posture's repair write** [Revision 2]. The value is semantic, since READ-based inference depends on it. Otherwise it follows the guard posture. | The same |
| **Condition detection** | `MatchContextV2.sensing_window` is `None`, so the member never returns SENSE | `sensing_window` = 27 |

**No member returns SENSE when `sensing_window` is `None`.** This is **a correctness requirement**, because an invalid v2 action makes the entrant forfeit (`process_runtime.py:1189–1212`). It is checked statically and dynamically (§5.1, D8-9; §5.2, CQ8-1).

**Freeze tests for ADAPT8's rule [R-8].** These are engine-level behavior tests, run before the freeze.
- **The cases they cover:**
  - ADAPT8 **in Seat A and in Seat B**;
  - against a scripted **static** opponent and a scripted **responsive evader**;
  - **under both parents**;
  - with hits placed at **every chunk position of both seat orders**, so that every suppression pattern PA §8 characterizes is exercised;
  - **with ticks in which ADAPT8 itself receives no callback** [Revision 2].
- **What they assert:** the count of consecutive confirming verification observations; **that an unobserved tick neither advances nor resets it**; the reset on observed relocation; and the switch at the second consecutive confirmation [Revision 2]. **Never an outcome.**

### 3.3 Packages and identities

These are as PR6 §3.2:
- a primary and a twin package per member;
- opaque package identifiers;
- one byte-identical policy source, with parameters supplied through `MatchContextV2.parameters`;
- entrants identified at runtime by seat label only.

**Each package is statically classified** for the containment gate of §13 as *SENSE, gated by context*: it returns SENSE only when `sensing_window` is not `None`.

### 3.4 Fields and counts

- **F1:** every ordered pair of distinct members × 32 seeds [R-7].
- **F2:** every twin mirror, in both orientations, × 32 seeds.
- **The seeds.** The same ordered seed list is used for every cell and every condition, so cells pair exactly across all four.

| Members | F1 cells per condition | F2 cells per condition | Per condition | All four conditions |
|---|---|---|---|---|
| 11 | 110 × 32 = 3,520 | 11 × 2 × 32 = 704 | 4,224 | **16,896** |

### 3.5 The H8-REPEAT eligible census [B-5, B-6]

**When and how it is computed.** At the family freeze, **from the frozen parameters and source, before any seed exists.** A static, tested procedure computes it, and it is committed in the freeze record. No outcome of any kind enters it.

**The units are opponents *Y* ∈ Π**, for the contrast REACQ8 against RUSH8. An opponent is eligible if and only if all three hold:

| # | Criterion | How it is decided (statically) |
|---|---|---|
| **E-1** | *Y* can relocate after being located or disrupted | *Y*'s frozen parameters include `evade` = on-hit |
| **E-2** | That relocation stales the anchor information that is of use | [ARITH] Every evasion moves the anchor by *m* ≥ 8 ≥ 1. A disruption is a WRITE to the exact anchor address (E6 semantics), so a WRITE to the pre-relocation address no longer lands on *Y*'s anchor. |
| **E-3** | The opponent has an economic reason to re-acquire | REACQ8 and RUSH8 disrupt known anchors (the attack posture). Under the **primary** parent, a hit costs *Y* at least 6 offers (PA §8), which exceeds the worst-case re-acquisition cost of 3 SENSE actions (Appendix A.3). |

**The census is defined under the primary parent's economics only.**
- Under λ = 1 a hit costs 1 offer, which is less than the re-acquisition expectation of 225/114, so E-3 fails there by construction.
- **The companion evaluates the same census**, as a status comparison (§6.6).

**Re-derived under Revision 2's semantics** (the research lead, 2026-09-30), rather than carried forward from revision 1. Re-acquisition precedence changes what the policies actually do, so each criterion is re-checked:
- **E-1** is decided by its registered rule, `evade` = on-hit. Revision 2 changes no member parameter, and EVADE8 alone has it. Under `"active"` no other member's anchor moves at all: acquisition, verification and re-acquisition are SENSE actions there, and only an evasion is a MOVE.
- **E-2** is arithmetic, and unchanged.
- **E-3 now describes what REACQ8 actually does.** With precedence, its re-acquisition takes at most 3 SENSE actions (Appendix A.3), and is no longer starved by core writes. The comparison with a hit's cost of at least 6 offers therefore applies to the policy's actual behavior.
- **The frozen census is still the tested static procedure's output at the family freeze** (above). This re-derivation is its prediction.

**Re-derived again under Revision 3** (the research lead, 2026-09-30), not carried forward from revision 2's freeze. Revision 3 changes only when initial acquisition ends:
- **E-1** is still decided by `evade` = on-hit, which Revision 3 does not change: EVADE8 alone has it. Revision 3 removes movement (SPLIT8's sensor stops sweeping under `"passive"` once its entrant confirms the enemy core) and adds none.
- **E-2** is arithmetic, and unchanged.
- **E-3** is unchanged. REACQ8 and RUSH8 are attack-posture members, whose behavior Revision 3 does not change (§3.2), so REACQ8's re-acquisition still takes at most 3 SENSE actions.
- **The frozen census is still the tested static procedure's output at the family freeze.** This re-derivation is its prediction.

**The predicted census, re-derived from §3.1's table under Revisions 2 and 3: {EVADE8}. That is one defender archetype.** By the research lead's rule [B-6]:

> **Requirement C is scoped to the EVADE8 stratum. H8-REPEAT and H8-ADAPT are read as claims about re-acquisition against a naturally evading defender, not about the whole family.**

**If the frozen census is empty,** H8-REPEAT and H8-ADAPT are **NOT EVALUABLE**, and the pre-seed halt of §12 applies.

---

## 4. Operationalizations

All arithmetic is exact (`Fraction`), and every comparison is closed exactly as written.

**Reused from PR6 §4 unchanged**, with the E8 member sets:
- **O-VALUE:** win 1, tie 1/2, loss 0.
- **O-PAYOFF:** p_s(*i*, *j*), then u(*i*, *j*) over 32 seeds, and u(*i*, *i*) = 1/2.
- **O-EPS:** ε = 1/16 [R-4].
- **O-BR:** BR_ε(*j*) ⊆ Π_F, universality, and P_none.
- **O-BOOT:** 1000 resamples of the ordered seed list, 32 draws with replacement from `random.Random(42)`, **applied jointly to every cell and every condition** [R-5].
  - **Joint** means that **one resampled seed multiset is used to recompute the control and the treatment metrics alike**, and any cross-condition predicate is evaluated **within that draw**.
  - **stab(P) ≥ 9/10** means that P holds in **at least 900 of the 1,000 registered resamples**.
  - **The draws** [Revision 2] are E6's `payoff.resample_positions` convention exactly: `rng = random.Random(42)`, and each of the 1,000 resamples is `tuple(rng.randrange(32) for _ in range(32))`, a tuple of positions in the ordered seed list, drawn in sequence from that one generator. **Wherever a paired or control–treatment quantity is computed, the same resampled seed-position multiset recomputes both sides, within the draw.**
- **O-CLASS:** E3's `outcome_class`, and "decided by capture".
- **O-EARLY:** a forced-line capture is a capture of *d* at a tick ≤ 3 [R-6].
- **O-SEAT:** E4's `pairing_seat_metrics` and `mirror_seat_metrics` (SDI, GSB, SDom, SCD), with mirrors per seed.
- **O-CONTACT:** hostile core contact, from replay memory diffs.
- **O-EVIDENCE:** n_distinct beside every figure; every unit included; rates with fixed denominators.

**New, or adapted:**
- **O-NEUTRAL.** A unit is **seat-neutral** if and only if SDom < 9/10 **and** \|GSB\| ≤ 1/10. This is the neutrality predicate inside PR6's PF-4, now used only as a measurement predicate.
- **O-ACQ** (descriptive only, derived from the §10 trace fields). It covers:
  - each entrant's first-discovery tick, meaning its first SENSE result or visible set containing an enemy anchor;
  - the number of SENSE actions before and after first discovery;
  - READ probes;
  - per-pairing counts of cells with no discovery by either entrant.
- **O-REACQ** (descriptive only). A **re-acquisition event** is a SENSE result, or passive re-sighting, that shows an enemy anchor at an address other than the missing one it replaces (§2.5) [Revision 2]. It is classified by cause:
  - **evasion**, if that enemy anchor moved since it was last known, according to the replay's tick-boundary snapshots and the traces;
  - **own movement**, if the member's own anchor moved and the enemy's did not.
- **O-VERIF** (for ADAPT8). **V(*j*)** is the median, over the 32 seeds, of ADAPT8's mean per-match verification count against *j* across the two orientations.

---

## 5. Hypotheses

### 5.1 E8-D: the manipulation and integrity gate

**E8-D is a hard stop, and it reads no gameplay outcome.** Each clause is labelled a **Ruleset invariant**, a **family characterization** (true of this frozen family, not guaranteed by the Ruleset) or a **protocol** check.

| Clause | Kind | Condition | Evaluated on |
|---|---|---|---|
| **D8-1** Sensing exactness | Ruleset invariant | **Every applied SENSE's authoritative tuple** (§10) equals the set of live enemy anchor positions within ≤ 27 of *t* at execution. That set is **re-derived independently** from the trace's ordered action stream: tick-0 anchors, the normalized results of every MOVE, and disruption hits under the condition's λ. **Presence** [Revision 4]: every SENSE record carries `applied_result.sensed_anchors`, and no other record does (§10). An applied SENSE record that omits it fails D8-1: its absence is never read as an empty result. | T8 and T8L, all cells; for presence, all four conditions [Revision 4] |
| **D8-2** No free sensing | Ruleset invariant | `visible_enemy_anchor_addresses` is empty at every traced callback | T8 and T8L, all cells |
| **D8-3** No-information identity | Family characterization | **A negative control for information leakage.** Take every matched pair of T8 cells, and every matched pair of T8L cells: the same opponent, seed, orientation and seat, one cell with LURK8 and one with GREED8. **The opponent ranges over the nine members of Π other than LURK8 and GREED8** [Revision 2], which gives 9 × 2 orientations × 32 seeds = 576 matched pairs in each condition. Excluding those two keeps every comparison literally against the same opponent, so **the gate never depends on twin equivalence.** Twin identity is not assumed here; it is tested on its own terms (§3.3, D8-11). The entrant's ordered `decision_v2` records must be equal, record for record, in `action` (`kind`, `operand`, `value`) and in the observation's **information fields** (`visible_enemy_anchor_addresses`, `previous_sense_anchors`, `previous_read_value`, `previous_read_owner`). **A field is equal only if both records omit it, or both carry the same value** [Revision 4]. **Excluded:** package identity and metadata (package IDs, `wall_time_ms`, diagnostics). **Why equality is expected.** Both packages share one policy source and draw from the same seat- and slot-keyed stream in the same fixed order (PR6 §3.2), so their RNG state is identical by construction. With no information, both fall to the same paint routine. **So a divergence detects information reaching one of them, not an incidental artifact difference.** | T8 and T8L |
| **D8-4** Action charging | Ruleset invariant | Every SENSE record occupies exactly one offer. In every tick, each entrant's traced callbacks, SENSE records included, number at most its per-tick quota of 8, and no SENSE is followed by an extra, uncharged offer. | T8 and T8L, all cells |
| **D8-5** No match-state change | Ruleset invariant | For every tick and entrant, the replay's memory writes equal the traced applied WRITEs. No write, position change or disruption is attributable to a SENSE. | T8 and T8L, all cells |
| **D8-6** Parent identity | Ruleset invariant | With `sensing_mode = "passive"`, the parent byte-identity goldens reproduce byte for byte. C8 and C8L run T-E6's and T-E6L's Rulesets unchanged. | The parent freeze; C8 and C8L provenance |
| **D8-7** Initial invisibility | Ruleset invariant | Under C8 and C8L, in the initialized state, every opposing default-spawn anchor is more than 32 from every family sensor (PR6 D-2) | C8 and C8L, all cells |
| **D8-8** No early blind strike | Family characterization | In ticks 1–2, no family member writes a cell of the opponent's core before its entrant has had an **information event**: a SENSE tuple or a visible set containing an opponent anchor, or a READ returning an opponent-owned core cell (PR6 D-4) | All four conditions |
| **D8-9** Discipline and containment | Family characterization, checked statically | Every package passes PR6 D-5's static gate: imports only `battle_engine.agent_api` and whitelisted standard-library modules, never reads `context.seed`, contains no package-ID literal, and calls none of `open`, `exec`, `eval`, `compile` or `__import__`. **In addition, every path that returns SENSE is guarded by `sensing_window is not None`.** | All packages, at freeze |
| **D8-10** Seed commitment | Protocol | PR6 D-6, unchanged in form: at reveal, the list's SHA-256 equals the commitment, the execution matrix identity recomputes, and every cell's seed is on the list (§9) | After the frozen analysis, **before** interpretation |
| **D8-11** Mirror relabeling | Ruleset invariant | Every twin mirror's two orientations have byte-identical replay tick records (PR6 D-7) | All F2 cells |
| **D8-12** Trace completeness | Protocol | Every cell has a `bytefray.agent_trace` schema-2 trace. Every callback has a `decision_v2` record, and the trace's `BindingRecord.replay_sha256` equals the cell's replay digest. | All four conditions |
| **D8-13** Delivery consistency | Ruleset invariant | For every authoritative SENSE record, **if its process ever receives another callback**, its next `decision_v2` record's `previous_sense_anchors` must equal the authoritative tuple. That holds **even when the next callback comes on a later tick, after suppression.** **Suppression alone never excuses it:** under whole-tick disruption a process may miss the rest of its tick and be called again later. **No later reflection is required only if there is genuinely no later callback** before the entrant is eliminated or the match ends. In that case **the authoritative record still stands.** **Presence** [Revision 4]: the field is present on exactly the callbacks with a delivery obligation (§10). Absent where one exists, it is a D8-13 failure, and present where none exists, it is one too. Absence is read as no prior result only where no delivery obligation exists. It is a consistency gate only (§10). | T8 and T8L; for presence, all four conditions [Revision 4] |
| **D8-14** No invalid action or exception | Protocol | **Every `decision_v2` record's `applied_result.status` is `APPLIED` or `REJECTED_OUT_OF_REACH`** [Revision 5]. So no cell records an `agent_action_invalid` forfeit (`REJECTED_INVALID`), which would be a containment breach, or an `EXCEPTION`, which would be an integrity failure. Any other status, or a record without one, fails D8-14 too. | All four conditions |
| **D8-15** Window fidelity | Ruleset invariant | **Configuration.** Every T8 and T8L `ResetRecord` carries `sensing_window` = **27**, and one that omits it fails. Every C8 and C8L `ResetRecord` omits `sensing_window`, and D8-15 reads that absence as null; one that carries it, even as `null`, fails [Revision 4]. **D8-15 is not the sole proof of the window used.** The reset record establishes the configured window. D8-1's independent re-derivation, which uses exactly that recorded value and must reproduce every returned tuple, demonstrates the behavior. **Both must hold.** | All four conditions |

**E8-D = PASS** if and only if every clause passes. **Its status is final only after D8-10.** No registered interpretation or disposition is issued before the seed reveal (§9, step 7).

### 5.2 CQ8: control qualification, before any treatment cell exists

| # | Check | Condition |
|---|---|---|
| **CQ8-1** | Containment on controls | **Zero SENSE records** in every C8 and C8L trace, and D8-14 holds on the controls |
| **CQ8-2** | Twin identity until the first trigger | In every matched C8 and C8L cell, RUSH8 and REACQ8 produce identical action streams **up to REACQ8's first re-acquisition trigger**: the first callback at which a previously visible enemy anchor is absent from its visible set, that is, at which a tracked address becomes missing (§2.5). GUARD8 and EVADE8 are identical up to EVADE8's first inferred hit. |
| **CQ8-3** | The census is committed | The H8-REPEAT census (§3.5) is in the freeze record, committed **before any seed exists** |
| **CQ8-4** | Control-against-control | With C8 in the treatment slot, the frozen analyzer must read: H8-SUB's status equal to H8-PAR's; H8-TAX SUPPORTED (A = B = 1); PF8-1 to PF8-4 not raised, with no unit flagged; **H8-SEAT REFUTED**, since ΔG = 0 at the point estimate and in every resample; and the interpretation row the equality implies |
| **CQ8-5** | The seat strata are committed | The reporting strata of §6.2 (C8-neutral and C8-non-neutral, by O-NEUTRAL at the C8 point estimate) are computed on control data and committed **before any treatment cell exists** |

**If any CQ8 check fails, halt before any treatment.** Fixes to the family, with a re-freeze, stay blind to the treatment.

### 5.3 The hypotheses

Each is SUPPORTED, REFUTED, NEITHER or, where stated, NOT EVALUABLE. The conditions are exhaustive and mutually exclusive. Every predicate below is evaluated at the point estimate, and its stability is taken under O-BOOT.

| ID | Statement | SUPPORTED if and only if | REFUTED if and only if |
|---|---|---|---|
| **H8-SUB** | The best response under T8 is not constant | P_none on T8, and stab(P_none) ≥ 9/10 | not P_none, and stab(not P_none) ≥ 9/10 |
| **H8-PAR** | The best response under C8 is not constant | The same, computed on C8 | The same, on C8 |
| **H8-CHANNEL** | No acquisition policy is universal among single-process attackers under T8 | Q_none: no *i* ∈ A8 lies in BR^A_ε(*j*) for every *j* ∈ Π; and stab(Q_none) ≥ 9/10 | not Q_none, and stab(not Q_none) ≥ 9/10 |
| **H8-LESS** | Lower acquisition can win under T8 | P_win over L8, and stab(P_win) ≥ 9/10 | P_never over L8, and stab(P_never) ≥ 9/10 |
| **H8-REPEAT** | Re-acquisition pays against the census under T8 | Some *Y* ∈ 𝒞 has Δ^R_Y ≥ ε, and stab(∃*Y* ∈ 𝒞: Δ^R_Y ≥ ε) ≥ 9/10 | Every *Y* ∈ 𝒞 has Δ^R_Y ≤ 0, and stab(∀*Y* ∈ 𝒞: Δ^R_Y ≤ 0) ≥ 9/10 |
| **H8-ADAPT** | Adaptation pays under T8 | U(ADAPT8) ≥ max(U(RUSH8), U(REACQ8)), and the stability of that ≥ 9/10 | U(ADAPT8) ≤ max(U(RUSH8), U(REACQ8)) − ε, and the stability of that ≥ 9/10 |
| **H8-FL** | A delayed forced line defeats every defender under T8 | Some attacker *a* has min over *d* of FL(*a*, *d*) ≥ 9/10 | Every attacker has min over *d* of FL(*a*, *d*) ≤ 1/10 |
| **H8-TAX** | Delay only: the substitution merely delays | A ≥ 9/10 and B ≥ 9/10 | A ≤ 2/3 |
| **H8-SEAT** | The substitution worsens seat bias across the whole family | ΔG > 0, and stab(ΔG > 0) ≥ 9/10 | ΔG ≤ 0, and stab(ΔG ≤ 0) ≥ 9/10 |

**Anything else is NEITHER.**

**NOT EVALUABLE:**
- **H8-REPEAT** is NOT EVALUABLE if and only if 𝒞 is empty.
- **H8-ADAPT** is NOT EVALUABLE if and only if 𝒞 is empty. If 𝒞 is not empty but its preconditions fail, it is **NOT INTERPRETABLE** (§7.3).

**Definitions:**
- **BR^A_ε(*j*)** = { *i* ∈ A8 : u(*i*, *j*) ≥ max over *k* ∈ A8 of u(*k*, *j*) − ε }.
  - A8's five members differ only in `acquire` and `reacquire`, so Q_none asks whether any **one acquisition policy** is always among the best, holding posture and processes fixed.
  - It is computed over A8 so that members sharing an acquisition setting across postures cannot jointly cover every opponent's best-response set. That would inflate universality.
- **L8** = { (LURK8, RUSH8), (PACED8, RUSH8) }. Δ_j(lo, hi) = u(lo, *j*) − u(hi, *j*). P_win and P_never are defined exactly as in PR6 §4.6.
- **Δ^R_Y** = u(REACQ8, *Y*) − u(RUSH8, *Y*), for *Y* ∈ 𝒞, the census of §3.5.
- **U(*i*)** = the mean, over *j* ∈ Π, of u(*i*, *j*): the score against the mixed field.
- **ΔG** is defined in §6.2 (ii).
- **FL(*a*, *d*)** is the share of the 64 F1 matches of *a* against *d* that are forced-line captures of *d*.
  - The attackers are the attack-posture members of Π_F: {RUSH8, REACQ8, PACED8, STEALTH8, LURK8, SPLIT8}.
  - The defenders are {GUARD8, EVADE8, STRESS8}.
- **H8-TAX's A and B** are exactly PR6 §5.3's E6-H0 definitions, over the paired F1 cells of C8 and T8:
  - **A** is the share whose outcome class is unchanged;
  - **B** is taken **over exactly the cells counted by A**: the share whose final tick under T8 is ≥ the final tick under C8.
  - There is no empty-denominator convention. If A = 0, H8-TAX is REFUTED through A ≤ 2/3.

**The primary evidence** is H8-SUB with H8-PAR. H8-CHANNEL, H8-LESS and H8-TAX qualify it. **The repeated-choice evidence** is H8-REPEAT, and **the requirement-C evidence** is H8-ADAPT, read only under §7.3.

**Threshold rationale.**
- 9/10, 2/3 and 1/10 are PR6's, reused.
- ε and the tick bound are PR6's, reused.
- k = 2 is the minimum repeated confirmation [R-8, Revision 2].
- **No new threshold is introduced.** The family seat status uses sign and the 9/10 convention only [R-9].
- **None was derived from any E8 data, and none exists.**

---

## 6. Pathology Flags, the Seat Criterion and Registered Reporting

### 6.1 Pathology flags

These are computed on F1 of the primary arm, and **recorded whatever else holds**.

| Flag | Raised if and only if |
|---|---|
| **PF8-1** Stalling | The tick-limit share under T8, minus the share under C8, is ≥ 1/10 |
| **PF8-2** Loss of contact | The share of matches with no hostile core contact (O-CONTACT) under T8, minus that under C8, is ≥ 1/10 |
| **PF8-3** New immunity | Some member of Π_F is never core-captured in any of its F1 matches under T8, although it is captured in at least one under C8 |
| **PF8-4** Stable seat destabilization | §6.2 (i) |
| **PF8-5** Family seat worsening | H8-SEAT is SUPPORTED (§6.2 (ii)) |

### 6.2 The seat criterion, designed afresh [B-11, R-9]

**Its principles.** Each layer addresses a failure E6 and E7 exposed:
- **Instability.** E6's PF-4 was a point-estimate flag that any single unit could raise. In E7's resampling it separated the arms in only 177 of 1000 resamples (PA §6). So the unit layer keeps the existing bounds, where they already have a meaning, and **adds a stability requirement.**
- **Broad effects.** A family-wide seat shift can occur without any single unit crossing a bound. So a **family-level status** is registered over the entire frozen family.
- **No invented magnitude.** The family status uses **sign and the 9/10 stability convention only.** Its magnitude is reported, with **no magnitude floor**. A new effect-size cutoff would have no causal or design reason [R-9].
- **Phase-sensitive members.** E8-I4 forbids excluding them. So the strata of §6.3 are reported, **never used to exempt a unit.**

**The units.** 66 units: the 55 F1 pairings, meaning unordered member pairs whose two orientations are E4's pairing unit, and the 11 F2 mirrors.

**(i) The unit layer, PF8-4.**

> **A new unit-level seat artifact exists only when a unit is neutral in its matched control, non-neutral in treatment under the existing SDom/|GSB| bounds, and the neutral→non-neutral transition occurs in at least 900 of the 1,000 registered joint seed resamples (stability ≥ 9/10).**

- **How it is computed.**
  - Neutrality is O-NEUTRAL, at the point estimate in both conditions.
  - For each of O-BOOT's 1,000 draws, **the same resampled seed multiset recomputes the unit's C8 and T8 metrics**, and the transition is evaluated within that draw.
  - The unit's stability is the number of draws in which the transition occurs, divided by 1,000.
- **When it is raised.** If and only if at least one unit meets that condition.

**(ii) The family layer, H8-SEAT.**
- **The quantity.** **ΔG** = the mean, over **all 66 units**, of (\|GSB_T8(*u*)\| − \|GSB_C8(*u*)\|). That is the change in mean absolute seat bias between control and treatment.
- **SUPPORTED, a stable family-wide worsening,** if and only if ΔG > 0 at the point estimate, and stab(ΔG > 0) ≥ 9/10.
- **REFUTED** if and only if ΔG ≤ 0 at the point estimate, and stab(ΔG ≤ 0) ≥ 9/10.
- **NEITHER** otherwise.
- **Reported beside it:**
  - ΔG's magnitude, with its resampled 2.5%, 50% and 97.5% points. **Each is `sorted(xs)[int(q * (n - 1) + 0.5)]`** over the *n* = 1,000 resampled values [Revision 2], which gives **indices 25, 500 and 974** for *q* = 0.025, 0.5 and 0.975;
  - ΔG over the committed C8-neutral and C8-non-neutral strata (CQ8-5). **These are descriptive only.** They expose floor effects (PA §5.1, stratum (ii)) and never change the status.

**Both layers can kill** (KC8-5): a stable unit artifact (PF8-4), or a stable family-wide worsening (H8-SEAT SUPPORTED, which raises PF8-5).

### 6.3 Strata and mechanism tables (registered reporting)

- **Phase-sensitive stratum.** Every seat quantity in §6.2 is also reported separately for units **containing** a phase-sensitive member (PACED8, EVADE8, ADAPT8, STRESS8) and for units **not containing** one.
- **Decisive-tick parity.** Each unit's decisive outcomes are split by the parity of the decisive tick. Seat A moves first on odd ticks, so this separates first-mover from second-mover decisions.
- **Mechanism tables** (the PA-7 pattern). For every flagged unit, and for every unit in 𝒞, they report the per-cell mechanics:
  - callbacks per tick and per seat;
  - hits received and inferred;
  - evasions;
  - SENSE actions, before and after first discovery;
  - re-acquisition events by cause (O-REACQ).

  These are **required before any seat flag is read causally.** They never change a flag.

### 6.4 The payoff tables

Reported in full for both arms: u(*i*, *j*) with its n_distinct, every BR_ε and BR^A_ε set, the universal members, every Δ_j over L8, every Δ^R_Y, and U(*i*), each with its stability.

### 6.5 Descriptive telemetry

These are never inputs to a hypothesis:
- O-ACQ, including per-pairing no-discovery counts. Detection is kept distinct from hostile core contact (SYN6 §F.3).
- O-REACQ, by cause.
- O-VERIF.
- E4's cell metrics, FMA and FPS, for every F1 cell of all four conditions.
- Δ^R_j for every *j* ∉ 𝒞, as the expected cost of verification against opponents that do not relocate.

### 6.6 The companion arm [B-2]

- **Everything is also computed on the companion.** Every quantity in §5–§6 is computed on C8L → T8L with identical code. **The census 𝒞 is the primary's** (§3.5).
- **The companion reading is registered** as **"agrees"**, when H8-SUB, H8-CHANNEL, H8-LESS, H8-REPEAT, H8-FL and every kill criterion (§8) have the same status in both arms, or as the list of what differs.
- **Its a-priori expectation, registered:** H8-REPEAT's status differs from the primary's, and is not SUPPORTED. Under λ = 1 a hit costs one offer (E8-DR §C.4).
- **The companion never replaces a primary verdict, never triggers a kill, and cannot answer an interaction** (SYN6 §H, item 2).

---

## 7. Registered Interpretation (primary arm)

### 7.1 The structural reading

**The rule.** A row applies if and only if E8-D has the row's status and the pair (H8-SUB, H8-PAR) is among the row's listed combinations.
- **The rows cover every combination exactly once**, and none is impossible. A negated hypothesis is never written: NEITHER and REFUTED are listed separately.
- **A test must show** that every (E8-D, H8-SUB, H8-PAR) triple maps to exactly one row. A triple that maps to none, or to two, **fails closed** as an invariant violation.

| Row | E8-D | (H8-SUB, H8-PAR) | Registered reading |
|---|---|---|---|
| **STOP** | FAIL | all nine | **STOP.** No gameplay reading: the treatment, the family or the protocol is defective. |
| **R8-PRESERVES** | PASS | (SUPPORTED, SUPPORTED) | **Under the whole-tick parent, no fixed policy is a best response to every opponent, whether spatial information is acquired incidentally through movement (C8) or bought with an explicit sensing action (T8). For this family, the channel substitution preserves an opponent-dependent choice.** |
| **R8-CREATES** | PASS | (SUPPORTED, REFUTED) | **Under movement-acquired sensing (C8) one fixed policy is a best response to every opponent. Under the explicit sensing action (T8) none is. For this family, the substitution creates an opponent-dependent choice.** |
| **R8-REMOVES** | PASS | (REFUTED, SUPPORTED) | **The substitution removes an opponent-dependent choice present under movement-acquired sensing.** |
| **R8-NO-CHOICE** | PASS | (REFUTED, REFUTED) | **A fixed policy is a best response to every opponent under both channels.** Qualified by H8-TAX, as E6's R-NO-CHOICE was by E6-H0, with the registered texts below. |
| **R8-T-ONLY** | PASS | (SUPPORTED, NEITHER) | **No fixed policy is a best response to every opponent under T8. Under C8 the evidence is indeterminate.** |
| **R8-T-DOMINANT** | PASS | (REFUTED, NEITHER) | **A fixed policy is a best response to every opponent under T8. Under C8 the evidence is indeterminate.** |
| **NONE** | PASS | (NEITHER, SUPPORTED), (NEITHER, REFUTED), (NEITHER, NEITHER) | **"No registered interpretation row applies" is itself the registered outcome.** |

**R8-NO-CHOICE's H8-TAX qualifier** [Revision 2]. It distinguishes delay-only from restructuring, without changing the row's reading:

| H8-TAX | Qualifier |
|---|---|
| SUPPORTED | "the substitution acts only as a delay: outcomes are preserved and delayed" |
| REFUTED | "a dominant policy under both channels, with outcomes restructured" |
| NEITHER | "a dominant policy under both channels; delay-only is neither established nor excluded" |

### 7.2 Qualifiers, on every PASS row

| Hypothesis | Status | Qualifier |
|---|---|---|
| H8-CHANNEL | SUPPORTED | "and no single acquisition policy is universal among the single-process attackers" |
| | REFUTED | "but one acquisition policy is universal among the single-process attackers", naming every universal member of A8 and giving KC8-6's label [Revision 2] |
| | NEITHER | "the acquisition-policy structure is indeterminate" |
| H8-LESS | SUPPORTED | "and spending less on acquisition beats spending more against at least one opponent" |
| | REFUTED | "but the registered lower-acquisition contrasts never win" |
| | NEITHER | "whether less acquisition can win is indeterminate" |

### 7.3 The repeated-choice and requirement-C readings

**H8-REPEAT's reading.** Every reading carries §1's scope sentence verbatim, and is scoped to 𝒞, predicted to be {EVADE8} [B-6].

| H8-REPEAT | Registered reading |
|---|---|
| SUPPORTED | "Against the census {𝒞}, re-acquiring a relocated anchor beats not re-acquiring: spatial information is valuable more than once in this whole-tick ecology." |
| REFUTED | "Against the census, re-acquisition never pays." |
| NEITHER | "Whether re-acquisition pays against the census is indeterminate." |
| NOT EVALUABLE | "The frozen census is empty, so there is no repeated-choice claim." |

**H8-ADAPT's interpretability.** It is interpretable if and only if all of these hold (E8-MF §N, ruling 4):
- H8-SUB is SUPPORTED;
- H8-REPEAT is SUPPORTED;
- **the allocation-variation check holds**: min over *Y* ∈ 𝒞 of V(*Y*) > max over *j* ∈ S of V(*j*).
  - **S** is the set of opponents in Π_F \ 𝒞 whose anchors do not move after being located, **by frozen semantics** under `"active"`: every member with `evade` = off.
  - In words, ADAPT8 verified more against every census opponent than against every such static one.

| Interpretable? | H8-ADAPT | Registered reading, scoped to 𝒞's stratum |
|---|---|---|
| Yes | SUPPORTED | "Within the {𝒞} stratum, an agent that observes whether a located anchor moves, and adapts its re-acquisition, does at least as well as either fixed allocation against the mixed field." |
| Yes | REFUTED | "Within the {𝒞} stratum, the adaptive allocation does worse than the better fixed allocation." |
| Yes | NEITHER | "Within the {𝒞} stratum, whether adaptation pays is indeterminate." |
| No | — | **"NOT INTERPRETABLE."** There was no demonstrated repeated choice to adapt to. **It is never read as a refutation of adaptation.** |
| 𝒞 empty | — | "NOT EVALUABLE" |

- **An inconsistent record fails closed.** A status recorded for H8-ADAPT while the table says it is not interpretable is an invariant violation, not a reading.
- **Mapping tests cover every combination** of (H8-SUB, H8-REPEAT, check, H8-ADAPT).

### 7.4 The answer to the research question

**The research question is registered as exactly the conjunction of three components** (§1): H8-SUB, H8-CHANNEL and H8-REPEAT. **Its answer has four outcomes**, defined explicitly and applied in the order listed:

| Core answer | Definition |
|---|---|
| **NOT EVALUABLE** | A registered gate or census condition makes the question unevaluable. Either E8-D FAILs, or no component is REFUTED and H8-REPEAT is NOT EVALUABLE because 𝒞 is empty. |
| **NO** | E8-D PASSes, and at least one required component is REFUTED |
| **YES** | All three required components are SUPPORTED. The reading carries §1's scope sentence. |
| **INDETERMINATE** | Otherwise: no required component is REFUTED, but at least one is NEITHER |

- **Why the order.**
  - A failed gate voids every reading.
  - Otherwise, one refuted component falsifies the conjunction, whether or not the others can be evaluated.
- **Every combination maps to exactly one outcome.** The four are mutually exclusive in this order, and a mapping test covers every (E8-D, H8-SUB, H8-CHANNEL, H8-REPEAT) combination.
- **YES does not by itself establish requirement C.** C additionally requires H8-ADAPT to be interpretable and SUPPORTED (§7.3). A repeated opportunity to re-acquire is not an adaptive policy that recognizes state and changes behavior. The mechanic result and the adaptive fixture's performance are **separate registered conclusions**.
- **The registered channel difference** (§3.2) is stated beside every reading [Revision 2]. Under `"passive"`, losing visibility can resume acquisition. Under `"active"`, remembered SENSE knowledge persists, so a `once` member does not re-acquire for lack of visibility.

**Recorded alongside every row, but never inputs to it:** H8-FL, H8-TAX (except as R8-NO-CHOICE's qualifier), PF8-1 to PF8-5, the §6.3 strata, and the companion reading.

---

## 8. Kill Evaluation and Disposition

These are evaluated on the primary arm.

| ID | Fires if and only if | Label |
|---|---|---|
| **KC8-1** Constant best response | H8-SUB is REFUTED | **Search race** if every universal member has `acquire` ≠ none; **greed dominance** if GREED8 is universal; otherwise **other dominance**, naming the members |
| **KC8-2** Greed dominance | GREED8 is universal at the point estimate, and stab(GREED8 universal) ≥ 9/10 | A special case, reported even when other members are universal too |
| **KC8-3** Stalling or loss of contact | PF8-1 or PF8-2 is raised | — |
| **KC8-4** Delayed forced line | H8-FL is SUPPORTED | — |
| **KC8-5** Seat | PF8-4 is raised (a stable unit artifact), or H8-SEAT is SUPPORTED (a stable family-wide worsening, PF8-5) | Which layer, ΔG's magnitude, and every flagged unit with its §6.3 stratum and mechanism table |
| **KC8-6** Acquisition dominance | H8-CHANNEL is REFUTED | Over **the universal members of A8** at the point estimate: each *i* ∈ A8 in BR^A_ε(*j*) for every *j* ∈ Π. There is at least one, since H8-CHANNEL is REFUTED. The label is **channel race** if every one has `acquire` ≠ none; **information dominated** if LURK8 is the sole one; otherwise **mixed dominance**, naming every one [Revision 2] |

**The disposition is exhaustive:**
- **VOID** if E8-D fails.
- Otherwise **REJECT as a gameplay candidate** if any KC8 fires.
- Otherwise **CANDIDATE, for a further design phase**, if the row is R8-PRESERVES or R8-CREATES, H8-LESS is SUPPORTED, and the core answer is YES.
- Otherwise **NOT ESTABLISHED**.

**CANDIDATE does not establish requirement C.** That is H8-ADAPT's separate conclusion (§7.3). **CANDIDATE never means promotion.** Promotion additionally requires A3 (§13) and a product-level closure of seed reconstruction [B-10, B-12]. PF8-3 is recorded, not a kill.

**A REJECT, a NOT ESTABLISHED or a NOT EVALUABLE is a successful result of the method.**

---

## 9. Seed-Set Blindness Protocol

**PR6 §9 is adopted unchanged in every step**, with E8's names:

1. **Family first.** The complete family, primary and twin packages, is implemented, tested (including A1-style engine-level behavior tests), fingerprinted and committed **first**. The structural matrix identity `v6-e8-matrix-v1-<12 hex>` is frozen with no seed values, and **the census (§3.5) and the seat strata inputs are committed with it.** Seeds are generated only after that. **No seed is generated while this pre-registration is written.**
2. **Generation.** 32 [R-7] unique integers from `secrets.randbelow(2**53)`, by committed tooling, **exactly once**. They are never regenerated because of an operational hiccup. If the private list is lost or altered before execution, that needs a new commitment and a new execution identity before any control cell.
3. **Canonical encoding and commitment.** Decimal ASCII, one per line, LF endings with a trailing LF, in UTF-8. The commitment is the SHA-256 of those bytes.
4. **Two identities.** The structural identity is fixed before the seeds. The execution identity `v6-e8-exec-v1-<12 hex of SHA-256(structural digest hex, LF, commitment hex, LF)>` is fixed once the seeds exist.
5. **Commitment only.** The commitment and the execution identity, and nothing else, are committed before the first matrix cell, controls included. Every cell's provenance carries both identities and the commitment. The list stays git-ignored, outside every package.
6. **Blindness.** D8-9 forbids filesystem and introspection access. **Every output before the reveal passes a value-based seed filter**, because artifact paths embed seeds (E6-R §I.1).
7. **Order.**
   1. Treatment execution;
   2. the treatment gates;
   3. the frozen analysis;
   4. **the seed reveal and D8-10**;
   5. E8-D's final status;
   6. the interpretation and disposition;
   7. the results record.

   **If D8-10 fails, the disposition is VOID.**
8. **Push each approved boundary before the next exposure.**

**The protocol is research methodology.** A product-level closure of seed reconstruction remains a promotion prerequisite [B-12] (DR §E.2; E8-I5).

---

## 10. Trace Requirements (exact) [B-7, R-12]

**Traces:** `bytefray.agent_trace`, schema version **2** (`TRACE_SCHEMA_VERSION_V2`), are required for **every cell of all four conditions** (D8-12). **The analysis reads sensing facts only from the fields named here. No other telemetry is equivalent.**

**The fields frozen here.** They are all additive and optional. The trace policy says readers ignore unknown keys, so they need no trace schema-version change (`agent_trace.py:18–31`). **When each is present is registered below** [Revision 4].

| Surface | Field | Type, and its JSON form |
|---|---|---|
| `ObservationV2` | `previous_sense_anchors` | `tuple[int, ...] \| None`, ascending |
| `TraceObservationV2` | `previous_sense_anchors` | A mirror of the above: a JSON list of integers, or `null`. It is present only where a delivery is due (below) [Revision 4]. |
| `TraceResultV2` | `sensed_anchors` | `tuple[int, ...] \| None`, as a JSON list of integers ascending, or `null`. It is present only on SENSE records (below) [Revision 4]. |
| `TraceActionV2` | `kind` | `"sense"` for the sensing action |
| `MatchContextV2` | `sensing_window` | `int \| None`: **the registered half-width actually in effect for the match**, 27 under `"active"`, `None` under `"passive"` |
| `ResetRecord` | `sensing_window` | The same value, recorded at each entrant's `reset()`. It is **match configuration**: it records the window in effect (D8-15). The window's *behavior* is demonstrated by D8-1's re-derivation. It is a JSON integer, present under `"active"` and absent under `"passive"` (below) [Revision 4]. |

**Presence** [Revision 4]. **An absent field and a field present as `null` are different serialized states.** Each E8 field is present exactly where its semantics apply, and absent everywhere else. The research lead's rule, verbatim:

> C8 / C8L controls: E8-only optional trace fields are omitted when not applicable, not serialized as `null`.
> - `ResetRecord.sensing_window` is absent.
> - `sensed_anchors` is absent because no SENSE action exists.
> - `previous_sense_anchors` is absent because no SENSE result exists to deliver.
>
> D8-15: for the control-side semantic check only, absence of `sensing_window` means the registered value is None/null. For T8/T8L, absence is not acceptable: the reset record must explicitly contain `sensing_window = 27`.
>
> `sensed_anchors`: on an applied SENSE decision, the field is mandatory even when the result is empty. Empty result must be represented explicitly as the registered empty collection; omission means “this record was not a SENSE result,” not “SENSE returned nothing.”
>
> `previous_sense_anchors`: on the first later callback that has a delivery obligation from a prior SENSE, the field is mandatory and must equal that authoritative result—even when the result was empty. If no SENSE has ever produced a result for that process, the field is omitted.
>
> D8-13: therefore treats absence as null/no-prior-result only when no delivery obligation exists. Once a SENSE result exists and a later callback occurs, absence is a gate failure.

**The research lead's rulings** (2026-09-30), on three points the rule leaves open:
- **A refused SENSE is an explicit `null`** in both fields: its own record's `sensed_anchors`, and the next callback's `previous_sense_anchors`. This keeps the refused row of the authoritative-record table (below) and D8-13's reflection of a refusal, so a dropped delivery after a refusal is still caught.
- **A delivery obligation falls on exactly one callback:** the same process's next callback after a SENSE record, applied or refused, even on a later tick after suppression. Every other callback omits `previous_sense_anchors`, including a callback after an earlier SENSE whose result was already delivered.
- **Presence is checked both ways, on every cell, and fails closed.** A field absent where it must be present, or present where it must be absent, fails the gate that reads it: D8-15 for `sensing_window`, D8-1 for `sensed_anchors` and D8-13 for `previous_sense_anchors` (§5.1).

| Field | Present, with its value | Absent |
|---|---|---|
| `ResetRecord.sensing_window` | Under `"active"` (T8, T8L): **27** | Under `"passive"` (C8, C8L). D8-15 reads the absence as null. |
| `applied_result.sensed_anchors` | On every record whose action is SENSE, as its status maps it (below) [Revision 5]: the ascending list if `APPLIED`, empty if nothing was found, and otherwise `null` | On every other record. Its absence means that the record is not a SENSE record, never that a SENSE found nothing. |
| `observation.previous_sense_anchors` | On the callback with a delivery obligation: equal to the prior SENSE record's `sensed_anchors`, whether a list, an empty list or `null` | On every other callback, including every callback before the process first senses |

**The status mapping of a SENSE record** [Revision 5]. **`null` means only that there is no applied sensing result. The status says why**, so a `null` never erases the difference between an ordinary refusal and an integrity failure.

| `applied_result.status` | `sensed_anchors` | What the record is |
|---|---|---|
| `APPLIED` | The ascending list, possibly empty | An applied SENSE (D8-1) |
| `REJECTED_OUT_OF_REACH` | `null` | **The only ordinary refused SENSE** |
| `REJECTED_INVALID` | `null` | A containment breach: D8-14 fires |
| Any other status, `EXCEPTION` included | `null` | An integrity failure: D8-14 fires. It is never read as a refused SENSE because its value is `null`. |

In the existing engine, a forfeit record (`REJECTED_INVALID` or `EXCEPTION`) carries no action, because an action is recorded only once it is accepted (`process_runtime.py:1159–1262`). Such a record is then not a SENSE record and carries no `sensed_anchors`, and D8-14 fires on its status all the same. A forfeit ends its entrant, so no delivery follows it.

**Serialization compatibility** [Revision 4]. The research lead's rule, verbatim: Additive E8 trace fields must not change canonical serialized bytes for pre-E8/control records when their semantics are inapplicable. D8-6's parent goldens check it on the parent freeze.

**The authoritative record** [B-7]. For each sensing action, **the acting callback's `decision_v2` record is authoritative for both the action and its returned result.** Its `applied_result.sensed_anchors` **is** the result. `previous_sense_anchors` is only the later reflection of that result, in the observation state of the same process's next callback, if there is one.

| Fact | Established by, on that one record |
|---|---|
| A sensing action was taken | `action.kind` = `"sense"`, with `action.operand` as returned by the agent |
| It was applied | `applied_result.status` = `"APPLIED"`, and `applied_result.normalized_address` = *t* mod 512 |
| It was refused | `applied_result.status` = `"REJECTED_OUT_OF_REACH"`, and `applied_result.sensed_anchors` = `null` |
| What it returned | `applied_result.sensed_anchors`, the complete ascending tuple. An empty list means sensed and found nothing. |

- **Correctness never depends on a later record.** A later callback may come only after suppression, or never, if the entrant is eliminated or the match ends.
- **The consistency gate** (D8-13). *If* the same (`agent_id`, `process_id`) **ever** has another `decision_v2` record, even on a later tick after suppression, the next such record's `observation.previous_sense_anchors` must equal the authoritative `sensed_anchors`: the tuple if applied, `null` if refused. A mismatch is a D8-13 failure, and so is an absent field [Revision 4]. **Only a genuinely absent later record**, because the entrant was eliminated or the match ended first, **requires no reflection.**
- **The delivery tests, before the freeze.** Engine-level tests with scripted, non-family agents, under both parents, must cover:
  - sense, then the next offer in the same chunk;
  - sense, then the next tick;
  - **sense, then suppressed for the remainder of the tick, then a later callback.** The later record must reflect the authoritative result.
  - **the genuinely terminal cases:** sense as the process's last callback before its entrant is eliminated, and before the match ends at the tick limit.
  - They assert delivery semantics only, never an outcome. This corrects E8-DR §J's P-9, which listed suppression among the cases with no next callback.
- **The trace belongs to the cell** if and only if `BindingRecord.replay_sha256` equals the cell's replay digest (D8-12).
- **Correctness** is D8-1's independent re-derivation.

---

## 11. Evidence and Analysis Rules

1. **Every frozen unit is counted, and none is dropped.** n_distinct is reported beside every figure. A rate needs n_distinct ≥ 8; below that, a value is a characterization.
2. **Payoffs weight every seed equally** (O-PAYOFF). Tick metrics are computed per match, and the unit value is the median over seeds. No ticks are pooled across matches.
3. **O-BOOT resamples seeds jointly across every cell and every condition.** Every stability in §5–§6 uses the same 1000 resamples.
4. **Control-against-control** (CQ8-4) runs before any treatment exists.
5. **The strata and the census are committed before exposure:** the census before any seed (CQ8-3), and the seat strata before any treatment (CQ8-5).
6. **The companion never replaces a primary verdict** (§6.6). **ADAPT8 is never a condition** of §7.1's rows or of a kill; it enters only H8-ADAPT and §7.3.
7. **Nothing changes after any matrix cell exists**: no threshold, set, operationalization, row, rule, census or stratum.
   - **An analyzer defect** found after exposure means a stop and a new analysis-freeze identity. The matrix identity is kept.
   - **A defect found before treatment** is fixed by a narrow blind amendment, with v1 preserved.
8. **Before the reveal, every printed or saved output passes the value-based seed filter** (§9, step 6).

---

## 12. Hard Stops

**Before seeds:**
- engine-level family behavior tests fail, **including ADAPT8's freeze tests** (§3.2) **and the delivery tests** (§10);
- D8-9 (static discipline and containment) fails;
- **the census is empty**;
- the family's fingerprints are not committed.

**Before treatment:**
- a parent golden fails (D8-6);
- a fixture fingerprint drifts, or a request override is not `None`;
- CQ8-1 to CQ8-5 fail;
- the seed commitment or the execution identity is missing before the first cell;
- the source manifest changes, or the tree is dirty, during execution.

**During and after treatment:**
- E8-D fails on D8-1, D8-2, D8-3, D8-4, D8-5, D8-11, D8-12, D8-13, D8-14 or D8-15;
- an analyzer or telemetry disagreement: the re-derivation and the authoritative record disagree beyond D8-1's own check, or an analyzer fails;
- **any `REJECTED_INVALID` forfeit**, which is a containment breach, **or `EXCEPTION`**, which is an integrity failure, or any other status D8-14 refuses [Revision 5];
- a recurring `evaluation.json` `PermissionError`: quarantine, relaunch and byte-check once, then stop;
- **at reveal, D8-10 fails.** The disposition is then **VOID**.

---

## 13. A1 Containment and Promotion Prerequisites [B-9, B-10]

**A1**, approved for the E8 research experiment (E8-DR §F.3). Each requirement is verified by the gate noted:

| Requirement | Verified by |
|---|---|
| Only E8's research Rulesets, T8 and T8L, accept SENSE | A Ruleset-policy test. S-5 of E8-DR is a qualification test. |
| E8 packages are statically identified as requiring SENSE, **gated by context** | D8-9 |
| **The E8 harness rejects an incompatible package and Ruleset pairing before a match starts** | A pre-match gate. It passes a *context-gated SENSE* package only on C8, T8, C8L or T8L; an *ungated SENSE* package only on T8 or T8L; and **refuses every other pairing before execution**. |
| Existing product and stable Rulesets remain unchanged | Parent and stable goldens (D8-6) |
| Ordinary v2 agents remain valid | The existing Agent API test suite is unchanged and passes |
| The action stays off normal product-facing surfaces | It is not documented as a product feature, and no product Ruleset, starter agent or Designer path offers it. It is recorded in AGENT_API_V2.md only as a research-only extension. |

**Before any product promotion:**
- **A3 is required:** capabilities are declared, and incompatibility is rejected before execution.
- **A2, a new generation, is used only if implementation reveals an actually incompatible contract.**
- **The product-level closure of seed reconstruction** [B-12].

These are promotion prerequisites, not experiment gates, except for the containment rows above.

---

## 14. Differences from the Design Review

Each is recorded, and none changes a research-lead ruling.

1. **H8-CHANNEL's candidates are A8, the frozen acquisition-policy candidate set.** These are the five comparable single-process policies that differ only in how and when they acquire. Their opponents are the full eleven-member field. Computing it over every member sharing an acquisition setting would let defenders become universal for reasons unrelated to the channel question (§3.1, §5.3).
2. **H8-TAX is added.** It is E6-H0's delay-only null, which qualifies R8-NO-CHOICE, for comparability with PR6 §7.
3. **The census is defined under the primary parent's economics** (E-3). The companion evaluates the same census as a status comparison (§3.5, §6.6).
4. **EVADE8's hit inference is made exact**, as callback counting (§3.2). This makes EVADE8 phase-sensitive by construction (E8-DR §C.4).
5. **ADAPT8's switch rule is new.** k = 2 is the minimum repeated confirmation, counted in consecutive verification observations [R-8]. Revision 2 withdrew revision 1's scheduler-cycle rationale. Appendix A.4 validates the value against a scripted evader, and freeze tests cover both seat roles and all suppression patterns. STRESS8 has no evasion, so it is not in the census.
6. **D8-3, LURK8 ≡ GREED8 under T8**, is a new negative control for information leakage, with its equality defined exactly. **D8-13 and D8-14** implement the trace and containment rulings. **D8-15** checks the configured window, and D8-1's re-derivation demonstrates its behavior. The delivery tests of §10 correct E8-DR §J's P-9: suppression alone does not mean there is no later callback.
7. **The seat criterion is redesigned in two layers** [R-9]: a unit artifact with the existing bounds plus 9/10 stability, and a family-level status, H8-SEAT, set by sign and 9/10 stability. **No magnitude floor is introduced. R-9's earlier 1/20 was rejected.**
8. **The members are eleven, with no evading attacker** [R-10]. So the census is predicted to be {EVADE8}, and C is scoped to that stratum.
9. **Re-acquisition precedence** [Revision 2]. E8-DR §C.4's find → hit → evade → re-find loop, E-3 and Appendix A.3 all assume that the re-acquisition search runs. Under revision 1's order of an offer it could not pass its first window. It now takes precedence over the posture steps (§3.2). **Under C8 and C8L, REACQ8 and ADAPT8 can therefore chase a passive anchor that leaves visibility.**
10. **A channel difference is registered** [Revision 2] (§3.2). Under `"passive"`, losing visibility can resume acquisition. Under `"active"`, remembered SENSE knowledge persists.
11. **SPLIT8's initial acquisition ends once the enemy core is confirmed** [Revision 3] (§3.2). Under the controls, its sensor no longer resumes a generic sweep after confirmation. E6's SPLIT did not resume one either.
12. **Appendix A.2's count is corrected** [Revision 3]: 17 READs under E6's verification order, not E8-DR Appendix A.2's 16.
13. **When each E8 trace field is present is registered** [Revision 4] (§10). An absent field and a field present as `null` are distinct, the controls omit the fields, and the gates check presence both ways (§5.1).
14. **A SENSE record's status mapping is explicit, and D8-14 covers every status other than `APPLIED` and `REJECTED_OUT_OF_REACH`** [Revision 5] (§10, §5.1).

---

## 15. What This Pre-Registration Does Not Claim

- **No result.** No E8 data of any kind exists.
- **No prediction presented as a result.** E8-DR's expectations, including the companion expectation and the predicted census, are priors.
- **No product claim.** Every disposition is a research disposition. CANDIDATE is not promotion.
- **No claim beyond what E8 manipulates.** The readings concern the channel substitution under the whole-tick parent, for this family. The repeated-choice reading holds only where disruption makes re-acquisition valuable (§1).
- **No generalization of requirement C beyond the census stratum.**
- **No status for E6.** Its REJECT stands, and parenthood confers nothing.

---

## Appendix A. Arithmetic

### A.1 The discovery traversal

The windows *c_k* = own + σ(91 + 55*k*), for *k* = 0 … 6, cover [own + 64 + 55*k*, own + 118 + 55*k*]. Their union is [own + 64, own + 448], which is the 385-cell arc exactly (448 ≡ −64 mod 512).
- **The expectation.** With the enemy base uniform over the arc, E = 55 × (1 + … + 7) / 385 = **4**. The worst case is **7**.
- **E6's sweep, for comparison:** 1537/385 ≈ 3.99, at worst 7 (DR §G.1).

### A.2 Finding a core whose anchor left it

With *m* on [8, 64] and an unknown sign, the core cells lie in [anchor − 64, anchor − 1] or in [anchor + 8, anchor + 71]. **Under E6's verification order, at most 17 READs hit one of them** [Revision 3].
- **The order** (A1 C-2): anchor + 1 first, then anchor + 1 − 8*k* and anchor + 1 + 8*k*, for *k* = 1 to 8.
- **Why 17.** The first READ, at anchor + 1, lies in neither span. The worst case, a core 58 to 64 cells above the moved anchor, is found by the 17th READ, at anchor + 65.
- **The correction.** Revision 2 said 16, after E8-DR Appendix A.2, which counts a READ schedule chosen over the two spans.

### A.3 Re-acquisition

- **The positions after an evasion.** The new anchor lies in [*a* − 64, *a* − 8] ∪ [*a* + 8, *a* + 64], 114 cells.
- **The windows** are centered on *a*, then *a* ± 46, and cover 40, then 37, then 37 of them. So **the worst case is 3**, and E = 225/114 ≈ 1.97, taking positions as uniform.
- **Against the economics** (PA §8):
  - under whole-tick, a hit costs 6 or 8 offers, which is more than 3, so E-3 holds;
  - under λ = 1 it costs 1, which is less than 225/114, so E-3 fails.

### A.4 Validating k = 2

**The derivation** [R-8, Revision 2]: k = 2 is the minimum repeated confirmation. One verification observation establishes the anchor's current location, and a second, later one confirms that it persists. **This appendix checks that the value behaves correctly. It is not the reason the value was chosen.**

**Its scope** [Revision 2]. **The worked example assumes that the scripted validation evader does not itself attack or disrupt ADAPT8.** It validates the timing rule for that scenario, and **is not a trace of EVADE8's complete matchup behavior.** EVADE8's guard posture disrupts a known anchor (§3.2), so in the matrix ADAPT8 can receive no callback in some ticks, which are then unobserved.

**The worst case under whole-tick disruption** (PA §8), in the steady state of the loop, for such an evader:
1. Suppose the evader is hit after its first chunk, in its own first-mover tick *t*. It loses the rest of *t*. **In the steady state it evaded at offer 0 of *t***, so ADAPT8's first-offer verification in *t* has just seen **movement**, and the count is 0.
2. In tick *t* + 1 ADAPT8 moves first. Its first-offer verification sees the anchor **unmoved**, so the count is 1, and its second offer re-hits the evader, which therefore gets no callback in *t* + 1.
3. The evader's next callback is offer 0 of tick *t* + 2, its own first-mover tick, where it infers the hit and evades.
4. ADAPT8 moves second in *t* + 2. Its first-offer verification comes after that evasion and sees **movement**, which resets the count to 0.

**What this validates:**
- **Against a responsive evader,** the run of consecutive confirming verifications never exceeds 1, so k = 2 never stops verifying.
- **Against a static opponent that does not disrupt ADAPT8,** it stops at its second consecutive confirming verification.

**This is a validation of the independently derived value.** It is also exercised by the freeze tests of §3.2, in both seat roles and every suppression pattern.
