# Bytefray V6 E8 — Mechanic-Family Design Review

**Status:** A design and selection review only. **The research lead approved its direction on 2026-09-30**, with two wording changes made before commit: K-S is reframed as *active spatial sensing*, and its later choice is described as *repeated*, not *continuing*. The research lead's decisions are recorded in §N.
- **What it does.** It compares candidate mechanic families for E8 and selects a direction, only at the end (§L).
- **What it does not contain.** No Ruleset name, parameter value, matrix, seed, probe, implementation or pre-registration.
- **What it changes.** Nothing: no E2–E7 record, verdict or disposition.

**Branch:** `v6-research` at `fd01074` ("docs(v6): point the ROADMAP at the E2-E6 synthesis"). The tree was clean before this review, and this file is its only change.
**Date:** 2026-09-30
**Governing record:** [`V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md) (**SYN6**), approved at `da899e9`: the grades (§D), the liabilities (§E), invariants E8-I1 to E8-I5 (§F), the open decisions (§G), the lessons (§H) and the three families (§I). In the research lead's words, *"The synthesis has effectively become the brief."*

**Other records cited:**
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) (**SYN**), for requirements A–G
- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) (**SR**), including constraints K1–K8 and the footprint dimensions S1–S6
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**)
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**) and [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (**A1**)
- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) (**E6-R**)
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md) (**E7-DR**) and [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md) (**PA**)

**Evidence tiers:**

| Tier | Meaning |
|---|---|
| [DOC] | A committed record, cited by file and section |
| [SOURCE] | Current source at `fd01074`, cited by file and line |
| [ARITH] | Arithmetic from recorded constants, shown in the text or in Appendix A |
| [INFERENCE] | Reasoning from the tiers above. Every claim that a mechanic *would* create, remove or preserve a choice is here. None is a result. |

**No probe was run**, and none could be: probing a family means prototyping it, which is implementation.

**How to read it.** §B to §K answer the research lead's eight questions, and §J compares the candidates. The direction is selected only in §L, after the comparison. §M lists the decisions put to the research lead, and §N records the rulings.

| # | Question | Section |
|---|---|---|
| 1 | What problem is E8 actually trying to solve, now that E6 succeeded as research but failed as a candidate? | §B |
| 2 | Does Branch A offer a cleaner path than further modifying priced sensing? | §D |
| 3 | Which families produce opponent-dependent behavior, rather than another mostly solo-speed race? | §E |
| 4 | Under requirement G, can a single parent plus a companion answer the question before a two-parent factorial is considered? | §F |
| 5 | What new information, if any, enters observation and replay? | §G |
| 6 | Which E6/E7 lessons become actual pre-registration constraints? | §H |
| 7 | Which failure modes must E8 distinguish? | §I |
| 8 | What evidence would justify advancing a family to an E8 pre-registration, rather than stopping without an experiment? | §K |

---

## A. Baseline

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `fd01074`, pushed |
| State | E6 complete (`R-CREATES`; REJECT on KC-5). E7 closed at design review and audit, with no experiment. SYN6 approved. No E8 record, Ruleset, tooling or agent exists. |
| Records read | SYN6; SYN §G–§I; SR (all); DR §C.4, §E, §G, §H; PR §0–§9; A1 §2; E6-R §D–§I; E7-DR §3, §4, §5, §14; PA §5–§8, §13 |
| Source read | `agent_api.py` (`ObservationV2`, `MatchContextV2`, `AgentV2`); `process_runtime.py` (core initialization, suppression, visibility, action validation and execution, snapshots); `ruleset_policy.py` (anchor placement, the MOVE bound); `replay.py` (event vocabulary, unknown-type rejection) |

**The engine facts this review relies on** [SOURCE]:

- **Three actions.** An Agent API v2 offer returns exactly one of READ, WRITE or MOVE. Anything else is rejected (`process_runtime.py:999–1011`).
- **READ.** It returns the value and owner of any cell within the reader's declared reach, and reach can be up to half the arena (`process_runtime.py:1286–1308`; SR §B.2).
- **MOVE.** It moves the process anchor by at most 64 cells under `fixed_64` stride (`process_runtime.py:1274–1284`; `ruleset_policy.py:349–361`).
- **Visibility.** It is computed before every callback, pooled over the entrant's unsuppressed processes (`process_runtime.py:800–850`; E7-DR §3.1).
- **Cores are fixed.** Core cells are set once, at initialization (`process_runtime.py:757–763`). Under `core_base` spawn, which is the default (`ruleset_policy.py:162`), every default-spawned anchor starts on its own core cell 0.
- **What the observation carries.** `ObservationV2` holds the entrant's own geometry, `visible_enemy_anchor_addresses`, and the result of the entrant's previous READ. It carries nothing else about the enemy (`agent_api.py:232–244`).
- **What the replay carries.**
  - Snapshots record each process's anchor, disruption flag and reach, at tick boundaries only (`process_runtime.py:1013–1024`).
  - The event vocabulary is kill, death, spawn, move, territory, claim and forfeit (`replay.py:92–111`).
  - An unsupported event type is rejected (`replay.py:359`).

---

## B. Question 1 — The Problem E8 Is Solving

**What E8 is not solving.**
- **Not KC-5.** E7 closed it: a unit-level interaction, not a family-level sensing × disruption problem (SYN6 §C.3). Seat robustness is carried by E8-I4 and by the seat-criterion decision, not by a new mechanic (SYN6 §F.4, §G.2).
- **Not the promotion of E6.** REJECT stands, and no reading of "priced sensing succeeded" implies promoting an E6 Ruleset (SYN6 §I.5).
- **Not the product-level seed bypass.** E8-I5 binds a product candidate. A research experiment can close the bypass by methodology, as E6 did (SYN6 §F.5).

**What E6 left, read against the grades** [DOC; SYN6 §D, §E]:

| What E6 showed | Its limit |
|---|---|
| Opponent-dependent value of information among fixed allocations (A, B, E DEMONSTRATED) | The registered witnesses priced information through movement (SYN6 §D.2) |
| — | The price is **front-loaded**: "Finding an anchor that is still on its core costs less than one tick of budget … The choice this mechanic can create therefore lives mainly in the opening exchange, and afterwards only in re-finding anchors that move" (DR §G.1) |
| — | Adaptation within the match is NOT ESTABLISHED (C) |
| — | Interaction is PARTIAL (D): the no-detection share and EVADER's stalling |
| — | Explainability is PARTIAL (F): visibility is not in the replay |

**The problem, stated for every candidate.**

> **E8 asks whether information can be made an opponent-dependent strategic resource by a mechanism whose price is not bound to locomotion and not confined to the opening discovery, so that the choice is explicit enough to be adapted to (C) and shown in the replay (F), while it keeps E8-I1 to E8-I5.**

This is the research lead's question (SYN6, front matter), stated against E6's specific limits. It is still several properties. Requirement G allows one treatment variable, so **the selected family must name the one property its treatment manipulates**. The others are measured, not manipulated (§L).

**What sits upstream of the whole question** [SOURCE + INFERENCE]:
- **The core is fixed, and its location is the information capture needs.** Once found, it stays found, and remembered observations do not decay. So uncertainty is eventually exhausted, and any acquisition choice that repeats after discovery can live only in two places:
  - **enemy anchor positions**, which serve disruption targeting and evasion tracking;
  - **the state of one's own core**, meaning whether it is being written. No observation field carries it. It is bought by READs of one's own cells, as ADAPT's damage check did (E7-DR §4.4).
- **A candidate that prices only core discovery inherits E6's front-loading**, whatever its price unit.

---

## C. The Candidate Families

There are three mechanic families (SYN6 §I.1–§I.3) and one non-mechanic alternative, Branch A′ (§D). Each family is described here, stated as a causal hypothesis, and put through the weak-point test the research lead set for it (SYN6 §I). None is ranked before §J.

### C.1 K-D — Information decay, or uncertain last-known position

**The idea** (SYN6 §I.1). Information becomes stale when opponents move. Agents choose between spending actions to reacquire certainty and acting on uncertain information.

**Its causal hypothesis.** [INFERENCE] If the value of a sighting decays, an ongoing re-acquisition cost appears. Its size depends on how much the opponent moves, which makes the reacquire-or-act choice opponent-dependent.

**The weak-point test: is there something meaningful to become stale?**
- **Cores never go stale.** [SOURCE] Core cells are fixed at initialization. [ARITH] One sighting of an anchor still on its core cell 0 gives the core's location for the rest of the match.
- **Agents already remember.** [SOURCE] An agent is a persistent object across a match (`agent_api.py:261–264`), and E6's family already keeps state across callbacks (E7-DR §4.4). The engine cannot make an agent forget a sighting.
- **Staleness already exists under priced sensing.** [SOURCE + INFERENCE] Visibility is recomputed before every callback. A moved anchor that leaves the radius drops out of the visible set, and the agent's remembered position becomes stale. So what K-D proposes is already present, implicitly, in T-E6.
- **Anchors rarely move.** [DOC] E6's members made at most about one off-core MOVE per match on average, and four made none (E6-R §F.1).
- **What an engine-side decay could act on.** [INFERENCE] Only on what the engine delivers: intermittent visibility, or an age attached to a sighting. Expiry that must be renewed by spending actions is a priced refresh, which is K-S in another form (SYN6 §I.1).
- **Result: FAILS as an independent engine mechanic.**
  - The meaningful lever is **target mobility**, not decay. Target mobility means cores that relocate, or objectives that move, and that is a different and larger mechanic.
  - The one mobile target E6 had, EVADER's anchor, carried the stalling liability L-2.

### C.2 K-G — Graded remote information

**The idea** (SYN6 §I.2). Beyond the passive radius, an agent learns something coarse: a region, a direction, the age of a contact, or a confidence. More precise information costs actions.

**Its causal hypothesis.** [INFERENCE] Graded information turns E6's binary seen-or-unseen split into a continuous information-precision decision. The value of paying for precision would depend on the opponent. Precision is worth little against a static defender, and much against a mobile attacker whose anchor matters for disruption.

**The weak-point test: can the observation, API and replay complexity be justified, and can one strategic dimension still be isolated?**
- **The surface.** [SOURCE] `ObservationV2`'s only enemy information is `visible_enemy_anchor_addresses`. A region, bearing, age or confidence needs new observation fields. [DOC] Additive research-only fields have precedent without a version bump (SR §B.3, S2), but each one is a compatibility surface (SR §C, K8).
- **The replay.** [DOC] E6's simpler visibility already cannot be reconstructed from the replay (DR §C.4). A graded signal computed at every callback would be no easier.
- **The discovery price barely moves.** [ARITH] A free bearing turns E6's sweep into directed travel. At d = 32 and a 64-cell MOVE, a target at distance 64–256 needs at most 4 MOVEs, against at most 7, mean ≈ 3.99, for the undirected sweep (DR §G.1; Appendix A.2). So a free coarse signal lowers the price of discovery only modestly. Its main effect would fall on anchor tracking, and on how explainable the game is.
- **Isolating one dimension.** [INFERENCE] The family has at least three free parameters: what is graded, its resolution, and the price of precision. Requirement G needs one manipulated variable, so all but one must be fixed a priori, as E6 fixed *d* from geometry (SR §G.2, decision 4). No a-priori derivation for "resolution" or "precision price" exists in the records.
- **Result: PASSES CONDITIONALLY.** The complexity is justifiable only by requirement F. Isolation is possible only if the next review can derive every other parameter from geometry, and none of those derivations exists yet.

### C.3 K-S — Active spatial sensing (action-priced area sensing)

**The idea** (SYN6 §I.3). Spatial information is bought with an explicit sensing action, not through movement. The resource is the entrant's own per-tick action budget, Q.

**Why the name.** READ is already an action-priced sensing mechanism (below). So the new question cannot simply be whether "action-priced sensing" works. What is new is **an action that buys spatial information efficiently enough to compete with movement, while consuming the same action opportunity as every other behavior**.

**Its causal hypothesis.** [INFERENCE] Suppose E6's opponent-dependent allocation is a property of **priced information**, not of **movement-priced search** and its exposure. Then pricing the same information through a movement-free action should preserve E8-I1. If it does not, E6's result depended on locomotion or geometry.
- **Either outcome is informative.** It is the causal question E6 could not separate (SYN6 §D.2).
- **Its repeated choice.** Because a sensing action can be repeated, the family can create a **repeated acquisition choice** extending beyond the opening: paying again to re-locate moved anchors or to check threats, against acting. It is not a permanently recurring choice. With fixed cores and remembered observations, the uncertainty it prices is eventually exhausted.

**The weak-point test: what does the resource compete with?**
- **The competing use is built in.** [DOC + INFERENCE] If the price is one offer of the per-tick budget Q, sensing competes with attack, defense and repair by construction: SR §B.1's condition C1. That is the form that passes the test.
- **The fuel-gauge form fails B unless the resource is shared.** A separate sensing-only resource "merely meters sensing" (SYN6 §I.3), and a resource shared with another use adds a second mechanic. **So K-S is taken in its action-priced form only.**
- **READ is already an action-priced, movement-free channel** [SOURCE; DR §G.1]. But its yield is one cell per action: at most 49 READs, mean 25.4, to find a core, against a MOVE sweep of mean ≈ 3.99. **The new action differs from READ in yield: it buys spatial information over an area.** So K-S is, precisely, **a movement-free spatial channel priced between READ and the MOVE sweep.**
- **What K-S needs, and what it does not.** K-S does not need READ, MOVE-search and active scanning to be equally attractive. It does need **no universally dominant acquisition channel**. If one channel is rational in essentially every relevant state or matchup, the result is another search race, not an opponent-dependent resource decision (the research lead, §N).
- **The calibration hazard.** [ARITH + INFERENCE; Appendix A.1]
  - **Too cheap, and the choice disappears.** As the price of discovery falls toward zero, the game approaches the parent's free-information structure. There, one fixed policy is universal for this family (E6-H1C REFUTED). The only recorded price at which opponent dependence was shown is E6's MOVE sweep, at a mean of ≈ 3.99 of the 8 tick-1 actions (DR §G.1). One-action discovery is about a quarter of that.
  - **The forced line is a risk to measure, not a certainty.** Any price that completes discovery within tick 1 leaves a tick-2 capture arithmetically possible against a non-reacting victim. That was already true of E6's sweep (at most 7 actions). E6-H3 was nonetheless REFUTED against the reacting defenders (E6-R §D.1). So a delayed forced line (KC-4) is a risk to measure at any price below one tick, not an arithmetic certainty at a low price.
  - **Too cheap or too stealthy, and it dominates.** A scan that is both cheaper and less exposing than the MOVE sweep dominates it. [INFERENCE] That is a search race, KC-1's label.
- **Two semantic questions the next review must fix a priori.**
  - Whether sensing exposes the sensor. E6's MOVE sweep is mutually exposing; READ is not (DR §G.1).
  - What a suppressed process can do. It gets no callback, so it cannot sense at all (E7-DR §3.1, coupling 1).
- **Result: PASSES, with a named calibration hazard.** The competing use exists by construction. The family survives only if its yield can be derived a priori, without tuning against outcomes, so that the sensing action neither collapses discovery toward free nor dominates both existing channels.

### C.4 Considered and set aside

| Candidate | Why it is not an E8 candidate | Return condition |
|---|---|---|
| K-D in its present form | Fails its weak-point test (§C.1) | A target-mobility mechanic, scoped on its own |
| A sensing-only resource (the fuel-gauge form of K-S) | Meters sensing without a competing use: requirement B not met by construction (SYN6 §I.3) | A resource shared with another use, which is a second mechanic |
| Re-running priced sensing on the λ = 1 parent | Excluded by the research lead as an attempt to rescue E6 (SYN6 §I.4) | None |
| Contestable valuable cells | Not an information mechanic, so outside E8's question. K1 must be answered first (SR §D.2; SYN6 §I.5). | Per SR §G.3, read against research and candidate success separately (SYN6 §I.5) |
| Deployment and banking | Rejected as first mechanics (SR §D.3). Banking stays out while K2 holds. | Per SR §G.3 |

---

## D. Question 2 — Does Branch A Offer a Cleaner Path?

**Branch A takes two forms here,** and they answer different questions.

### D.1 Branch A proper: adaptive agents under the current (stable-equivalent) rules

This is SYN §H's form: no rule change.

**Why it is not cleaner for E8** [DOC]:
- **Under the parent there is nothing for this family to discover.** Visibility is complete from the first callback. Every attacker ties every other at 1/2, and SPLIT is universal (E6-H1C REFUTED; E6-R §E.1). Seat A detects first in all 2,304 C-E6 F1 cells (E6-R §F.1).
- **The forced line ends the game early.** On any parent where it exists, the game ends before a choice can matter (SR §B.2). Capture decides 0.775 of C-E6 F1 matches (E6-R §E.3).
- **The best existing Branch A evidence is entangled.** It is the pre-RC inverted-U reach curve, which is entangled with the forced line (SR §B.2).

**What it does not establish.** Branch A is **not disproven**. E6's control reading characterizes one scripted family (SYN6 §I.5).

### D.2 Branch A′: adaptive agents under an existing priced-sensing research Ruleset

The mechanic is held fixed, and the agent's adaptivity is varied.

**Its causal hypothesis.** [INFERENCE] E6 established which fixed allocation is best against each opponent. An agent that identifies its opponent from in-match observables, and switches to that allocation in time, should do at least as well as every fixed allocation against the mixed field. That is SR §F's signature.
- **E6's best-response map is the premise.** It is not the outcome being tested. What is tested is whether identification is fast and accurate enough.

**Where it is cleaner:**
- **One variable.** The mechanic is already characterized, so a negative result points at adaptation, not at the mechanic. This is the cleanest available test of requirement C.
- **Least engine work.** No engine change and no new Ruleset. [DOC] E6's analyzer and family tooling exist.

**Where it is not:**
- **It cannot answer E8's question.** It holds the mechanism fixed, so it produces no new way to turn information into a resource (§B).
- **It runs on a rejected candidate's Ruleset.** On the whole-tick form it inherits the KC-5 mechanism (E7-DR §4). On the λ = 1 form it sits close, in appearance, to the rerun the research lead excluded (SYN6 §I.4).
- **Hindsight.** E6's payoff tables are public (E6-R Appendix T). A switching rule written from them is fitted to E6's outcomes.
- **Fixture fingerprinting.** [INFERENCE] Against E6's scripted members, an adaptive agent could identify opponents by behavioral signature rather than by what the mechanic prices (§I, F-10). Held-out opponents would be needed.
- **The window is short.** DR §G.1's front-loading means the adaptation window is the opening. ADAPT's registered no-contact switch was at tick 16 (PR O-6), and its median first detection was tick 17 (E6-R §F.1).

### D.3 The answer

> **Branch A does not offer a cleaner path to E8's question.**

- **Branch A proper** meets a parent on which this family has nothing to discover.
- **Branch A′** is the cleanest path to **requirement C**, but it cannot produce a mechanism, and it carries hindsight and fingerprinting risk.
- **What follows.** Branch A′ is kept as the fallback (§L). C is carried into E8 as a decision about the population, not left to chance (§M, decision 4).

---

## E. Question 3 — Opponent-Dependent Behavior, or Another Mostly Solo-Speed Race?

**Where E6's opponent dependence came from.** [DOC] These are its descriptive sources, not registered causes:
- **Exposure.** At equal radius the sensor that sees is seen, so scouting exposes the scout (SR §D.1; DR §G.1).
- **Geometry.** The MOVE sweep finds anchors in at most 7 MOVEs, depending on placement (DR §G.1).
- **Opponent posture.** A static opponent needs finding once, and a mobile one repeatedly (SR §D.1).
- **The result.** Searchers are best against searchers, and SPLIT against passive, defensive and adaptive opponents (E6-R §E.1).

**What makes a solo-speed race.** [INFERENCE] Each side's best policy becomes "acquire at the fastest rate, then attack", whatever the opponent does. SR §D.1's failure mode 1 calls this a "geometry-and-seat race", and PR §8 registered it as KC-1's search-race label.

| Family | Pull toward a solo race | Pull toward opponent dependence |
|---|---|---|
| **K-D** | — | Not assessable: the family fails its weak-point test (§C.1) |
| **K-G** | A free coarse signal makes discovery directed, and a directed search is closer to a pure speed race (§C.2) | Paying for precision matters against mobile anchors, not against static ones |
| **K-S** | A cheap or stealthy sensing action dominates both existing channels, so everyone senses first and then rushes (§C.3) | Repeated acquisition, which is re-locating or checking again against acting, has a value that depends on whether the opponent threatens or moves. If sensing exposes the sensor, E6's exposure property survives without locomotion. |
| **Branch A′** | None added: the environment is already characterized as not a race (E6-H1T SUPPORTED) | Only if identification is fast enough (§D.2) |

**The answer.** [INFERENCE] None of the families is opponent-dependent by construction.
- **K-S** is the only family whose opponent-dependence mechanism, repeated acquisition against acting, can extend beyond the opening. It still ends once uncertainty is exhausted. The same family becomes a race if it is calibrated too cheap or too stealthy, or if any one acquisition channel dominates universally.
- **K-G** risks a race through free coarse information.
- **K-D** has nothing to act on.

---

## F. Question 4 — A Single Parent Plus a Companion, or a Two-Parent Factorial?

**The structural fact.** [SOURCE + INFERENCE]
- **Every family needs limited passive sensing somewhere.** An information price is moot where visibility is free and global (SR §C, K4). So every one of the three families either sits on a limited-passive-sensing parent, meaning an existing E6 treatment Ruleset, or replaces passive sensing as its one field against `research-scale`.
- **For K-S, both are possible:**
  - **(a)** a sensing action **on top of** E6's radius, whose parent is an E6 treatment Ruleset, so the treatment is two fields from stable;
  - **(b)** a sensing action that **replaces** passive sensing, as one mode field against `research-scale`, so it is one field from stable.

**Why a single parent plus a companion answers E8's question** [DOC + INFERENCE]:
- **The two factors act at different times.** The disruption regime acts after first contact: the first seer is the same entrant under T-E6 and T-E6L in 2,299 of 2,304 F1 cells (E7-DR §3.2). The information families act mainly on acquisition (DR §G.1).
- **So a parent-dependent reading is unlikely to be E8's primary question.** A companion on the other parent can record parent dependence as a companion reading, as E3–E6 did.
- **The interaction is closed.** The sensing × disruption question was closed by E7 (SYN6 §C.3). A two-parent factorial would re-open a closed interaction with a new mechanic, and it doubles the matrix.

**When a factorial would be justified.** Only if the next review shows that the family's mechanism cannot be separated from the disruption regime. For example, sensing under suppression is itself the lever (E7-DR §3.1, coupling 1). **Under requirement G the review must ask for a single parent plus a companion first** (SYN6 §G.1).

**Two consequences that bind the next review.**
- **Floors.** A companion's control has its own floor. C-E6L's tick-limit share is 7/12 ≈ 0.583, against 0.225 under C-E6 (E6-R §D.5, §D.2). A treatment that reduces stalling would look better on that floor. That is the control-floor failure mode (§I, F-6).
- **The companion's status.** Its registration must say whether it is a status comparison or an interaction estimand (SYN6 §H, item 2).

**The answer.** **Yes: a single parent plus a companion answers E8's primary question**, provided the selected family is not mechanistically bound to the disruption regime. The parent itself remains the §G.1 decision of SYN6, argued in the next review.

---

## G. Question 5 — What New Information Enters Observation and Replay?

| Family | Observation | Agent API | Replay |
|---|---|---|---|
| **K-D** | An age or expiry would need a field. Intermittent visibility would not. | Possibly one additive field | New facts only if the age is to be visible |
| **K-G** | **New fields:** region, bearing, age or confidence | Additive research-only fields (SR §B.3, S2) | Needs recorded facts, or the replay cannot show it (DR §C.4) |
| **K-S** | The result can arrive in `visible_enemy_anchor_addresses`, with no shape change (SR §D.1, footprint), or in a new field that separates sensed from seen | **A new `ActionKindV2` member**, research-only and rejected under every other Ruleset (SR §C, K8) | [SOURCE] No event in today's vocabulary records an information action (`replay.py:92–111`). A sensing event needs a new type, which the reader rejects today (`replay.py:359`). Otherwise the action stays trace-only, as E6's visibility did. |
| **Branch A′** | None | None | None |

**The requirement-F point.** [INFERENCE] K-S is the only family whose information acquisition is a discrete, explicit decision. That makes it the only one that could put "who looked, when" into the replay as a fact, rather than as a per-callback derivation. It pays for that with replay-schema work.

**The answer.** The review makes no choice here. It records that every mechanic family adds observation or API surface, and that K-S is the only one where the new surface buys a replay fact. **The next review must state, before implementation, which facts enter the observation and the replay** (SYN6 §G.4).

---

## H. Question 6 — Which Lessons Become Pre-Registration Constraints?

**These are proposals.** "Constraint" means a requirement the E8 pre-registration would carry. "Decision" means something the next design review must decide before pre-registration. "Practice" means a method carried forward without a registered rule. The research lead decides.

| Lesson (SYN6 §H, SYN §G.8) | Named event | Proposed status |
|---|---|---|
| n_distinct beside every count; no rate below 8 | SYN §G.8; PR §10.1 | **Constraint** |
| Mirrors analysed per seed; relabel identity as a gate | SYN §G.8; PR D-7 | **Constraint** |
| Every status combination maps to exactly one interpretation row | SYN §G.8; PR §7 | **Constraint** |
| A probe is not a registered run | SYN §G.8 | Practice: probe values disclosed as priors |
| The seat criterion | SYN6 §G.2: PF-4 fired on one threshold-crossing unit | **Decision.** Settled on methodological grounds before pre-registration, and never set from E6's values. |
| A companion is not a factorial | E7-DR §3.1 | **Constraint.** The pre-registration states whether any parent interaction is a registered question. If none is, it says companion readings cannot answer one. |
| Contrasts differ in one variable | PR O-2 (LURK added) | **Constraint** for every registered contrast |
| Engine-level family tests before any seed | A1 §2 | **Constraint:** a qualification gate before the freeze |
| Suppression governs sensing as well as acting | E7-DR §3.1, coupling 1 | **Decision.** The mechanic's semantics under suppression are specified in the design. |
| Callback-counting members couple to disruption semantics | E7-DR §3.1, coupling 2 | **Constraint:** E8-I4's stress member, and mechanism tables before any seat flag is read causally |
| Family-level quantities, with strata committed before computation | PA §5.1, §11 (I_all) | **Constraint** for any family-level seat or interaction quantity |
| Seeds redacted by value, not key name | E6-R §I.1 | **Constraint** (protocol) |
| Seed-set blindness | PR §9 | **Constraint** for the research experiment. E8-I5 binds a product candidate. |
| Parameters fixed a priori, never tuned against outcomes | SR §G.2, decision 4 | **Constraint** |
| The process sequence | SYN6 §H, item 8 | Practice: adopted as the plan (§L) |
| An adaptive member: secondary or registered | SYN6 §G.3 | **Decision** for the research lead (§M) |

---

## I. Question 7 — The Failure Modes E8 Must Distinguish

Each failure mode needs its own instrument or control, or two different failures will look alike.

| # | Failure mode | What it looks like | How E8 tells it apart | Source |
|---|---|---|---|---|
| F-1 | **Genuine mechanic failure** | No choice: a constant best response under treatment | The E6-H1T/H1C pattern: the treatment best-response map against the parent's | PR §5.3 |
| F-2 | **Search-race collapse** | A constant best response whose universal members all search | KC-1's label, registered in advance | PR §8 |
| F-3 | **A front-loaded choice** | A choice exists, but only until first discovery | Descriptive allocation timing: acquisition actions before and after first discovery, from traces | DR §G.1, §G.2 |
| F-4 | **A delayed forced line** | Discovery-dependent capture by tick ≤ 3 against defenders | E6-H3's form. Any price that completes discovery within tick 1 leaves a tick-2 capture possible by arithmetic, so the risk is registered and measured (§C.3). | PR §5.3, O-5 |
| F-5 | **Stalling or non-contact, against non-detection** | High tick-limit share, or no hostile core contact, or no detection | Detection and hostile core contact recorded separately (29.7% against 3.6% in E6). Non-detection that comes from population structure is kept apart from mechanic failure (Appendix A.3). | SYN6 §F.3; E6-R §F.1 |
| F-6 | **Control-floor effects** | A treatment "improves" a quantity only because its control sat at a floor or ceiling | Baseline strata registered in advance (PA §5.1, stratum (ii)). The companion control's own floor is recorded (C-E6L at 0.583). | PA §5.1; E6-R §D.5 |
| F-7 | **Callback or tick sensitivity** (the KC-5 class) | A seat artifact mediated by a tick-keyed member together with the parent | E8-I4's stress member, unit-level mechanism tables and a family-level seat quantity (SYN6 §G.2) | E7-DR §3.1, §4; PA §7 |
| F-8 | **A threshold realization** | A flag fires in one arm, but both arms raise it under resampling | Stabilities and joint arm patterns, as the seat-criterion decision requires | E7-DR §5 (the overall reading, "largely E"); PA §6 |
| F-9 | **Adaptation failure, against mechanic failure** | The adaptive agent loses | The fixed-allocation best-response map (the mechanic level) is read before, and separately from, the adaptive test (the agent level) | SYN6 §D.3 |
| F-10 | **Fixture fingerprinting** | An adaptive agent identifies scripted opponents by signature | Identification restricted to declared observables; held-out opponents | §D.2 [INFERENCE] |
| F-11 | **A seed-inference bypass** | Early strikes without an information event | D-4-style and D-5-style gates, and blindness | PR §5.1, §9 |
| F-12 | **Greed tilt** | Sensing-free painting dominates | KC-2's form | PR §8; SR K7 |
| F-13 | **Hindsight** | Design parameters that fit E6's public outcomes | A-priori derivations, disclosed; §H's "parameters fixed a priori" | SR §G.2, decision 4 |

---

## J. Comparison: Causal Hypotheses and Experimental Cost

"Open" means plausible but untested. The footprint dimensions S1–S6 are SR §B.3's. Every entry about what a family would do is [INFERENCE].

| | K-D decay | K-G graded information | K-S active spatial sensing | Branch A′ adaptation |
|---|---|---|---|---|
| **Causal hypothesis** | Decaying sightings create an opponent-dependent re-acquisition cost | Paying for precision creates an opponent-dependent precision choice | E6's allocation effect comes from **priced information, not movement-priced search** | In-match identification lets an agent realize E6's best-response map |
| **What it adds beyond E6** | Nothing engine-side: T-E6 already stales moved anchors (§C.1) | Gradations of information; explainability | Movement-free spatial acquisition at a price between READ and the sweep; repeatable, so repeated acquisition is possible | A test of requirement C |
| **Weak-point test** | **Fails** (§C.1) | **Conditional** (§C.2) | **Passes, with a calibration hazard** (§C.3) | Hindsight and fingerprinting (§D.2) |
| **A repeated choice beyond the opening** | Only with mobile targets | Anchor tracking | Repeated acquisition against acting, until uncertainty is exhausted (§E) | Not applicable |
| **SYN6 gaps it bears on** | None directly | F; possibly L-1 | The locomotion bound (§D.2 of SYN6), front-loading, C (an explicit, loggable decision), F (a discrete action can be a replay fact) | C only |
| **S2 Agent API** | Possibly one field | New observation fields | A new `ActionKindV2` member (K8) | None |
| **S3 Engine** | Visibility | Visibility and the graded computation | Action validation, execution, trace vocabulary and result delivery | None |
| **S4 Replay schema** | Possibly | Recorded facts needed | None if trace-only; a new event type if F requires it | None |
| **S5 Fields from stable** | 2 | 1–2 | 1 (variant b) or 2 (variant a) (§F) | That of the existing Ruleset used (1) |
| **S6 Instruments** | Needs mobile targets: a family change | A family redesign and analyzer work | A family parameter for sensing allocation, and analyzer extensions | Adaptive agents and held-out opponents |
| **Free parameters to fix a priori** | A decay rate or age | At least 3 (§C.2) | 1, the yield, plus the semantics of exposure and suppression | The identification rule |
| **Main failure risk** | Inertness | A race through free coarse information; parameter isolation | Calibration: a collapse toward free, or dominance (F-1, F-2), and KC-4 risk | F-9, F-10, F-13; runs on a rejected candidate's Ruleset |
| **Relative experimental cost** | Moderate, for little | High | Moderate | Low to moderate |

---

## K. Question 8 — Advancing to a Pre-Registration, or Stopping Without an Experiment

**The next step for a selected family is a full design review,** comparable to DR for E6. It is not a pre-registration.

### K.1 What that review must show before a pre-registration is written

Every item is needed:

1. **A source-level trace of a genuine decision point**, as in DR §H.2. The better allocation depends on the opponent, no allocation dominates by construction, and at least one decision point lies after first discovery. The last condition is what separates F-3 from a repeated choice.
2. **The weak-point test settled with arithmetic.** For K-S, the yield must be derived a priori so that the sensing action neither collapses discovery toward free nor dominates both existing channels (§C.3; Appendix A.1).
3. **One manipulated variable** against a byte-identical parent. The parent is chosen with SYN6 §G.1's argument, and a single parent plus a companion is considered first (§F).
4. **The observation and replay facts stated** (§G; SYN6 §G.4).
5. **The family specified a priori:**
   - E8-I4's tick- or callback-phase-sensitive stress member;
   - behavior that varies with the seed;
   - an adaptive member, if requirement C is registered (§M, decision 4).
6. **Reachable kill criteria that separate §I's failure modes**, an exhaustive interpretation table, and the seat criterion decided on method (SYN6 §G.2).
7. **Every parameter derived a priori** from geometry or arithmetic, never from outcomes (F-13).

### K.2 Conditions that stop the family without an experiment

Any one is enough:

- **(a) Dominance by construction.** Arithmetic shows one allocation dominates, which is a search race or a free-information collapse.
- **(b) No a-priori derivation.** The mechanic's parameter has none, and only tuning could fix it.
- **(c) Two inseparable treatment variables.** The mechanic needs two, and requirement G fails.
- **(d) An unacceptable research surface.** The observation or replay surface needs a schema change the research lead does not accept for research.
- **(e) No working blindness protocol.** The seed-inference channel cannot be closed by methodology for the family.

**A stop is a successful result of the method**, not a failure of the program (SR §G.1; PR §8). After a stop, the next candidate is the reserve or the fallback of §L.

---

## L. Selection

> **SELECTED DIRECTION: K-S, active spatial sensing (action-priced area sensing), to be taken to a full E8 design review.**

**Why K-S.**
1. **It is the only family whose weak-point test passes by construction.** Its competing use is the per-tick budget Q itself (§C.3). K-D fails its test, and K-G passes only conditionally.
2. **It asks a causal question E6 could not separate:** whether E6's opponent-dependent allocation belongs to priced information or to movement-priced search (SYN6 §D.2). Both outcomes are informative (§C.3).
3. **It is the only family that can create a repeated acquisition choice extending beyond the opening** (§E), though not a permanently recurring one. That lengthens the window in which adaptation can be tested (§D.2).
4. **It is the only family whose acquisition is an explicit decision that could become a replay fact** (§G). That serves requirement F.
5. **It can be one field from stable** (variant b), or one field on an E6 treatment parent (variant a). A single parent plus a companion answers its question (§F).

**The one property its treatment manipulates** (§B): the channel through which information is priced, **an explicit action instead of movement**. The repeated choice, adaptation and replay visibility are measured, not manipulated.

**Its gates.** The next review must pass all five, or it stops under §K.2:
- **G-1.** The yield is derived a priori (§C.3).
- **G-2.** The semantics of exposure and suppression are fixed a priori (§C.3).
- **G-3.** The variant (a or b) and the parent are chosen with SYN6 §G.1's argument (§F).
- **G-4.** The observation and replay facts are stated (§G).
- **G-5.** The family includes the stress member and seed-varying behavior, and the adaptive member follows §M, decision 4.

**The other candidates:**

| Candidate | Status | When it comes back |
|---|---|---|
| **K-G**, graded information | **RESERVE** | If K-S stops at G-1 or G-4, or if the research lead makes requirement F the primary target |
| **K-D**, decay | **SET ASIDE** | With a target-mobility mechanic, scoped separately |
| **Branch A′** | **FALLBACK** | If the research lead makes requirement C E8's primary question, or if K-S stops. It would need F-10's and F-13's controls. |
| **Branch A proper** | **OPEN, but not cleaner for E8** (§D.1) | Unchanged |

---

## M. Decisions for the Research Lead

The recommended option is listed first in each case.

| # | Decision | Recommendation | Alternatives |
|---|---|---|---|
| 1 | Direction | **K-S** (§L) | Branch A′, or K-G |
| 2 | Variant | For the next review to argue. [INFERENCE] **Variant b** isolates "action instead of movement" more directly, because in variant a movement-priced search stays available. **Variant a** keeps E6's passive-sensing structure as the parent. | Decide now |
| 3 | Parent regime | For the next review, under SYN6 §G.1. If variant a is chosen, an E6 treatment Ruleset becomes E8's parent. Its λ = 1 form would then carry the sensing action as the treatment, and is not the excluded priced-sensing rerun, but the research lead should confirm it may be used. | Decide now |
| 4 | Requirement C | **A registered hypothesis, conditional on the mechanic-level choice existing.** This keeps F-9 separable: the adaptive test is read only where the fixed-allocation map shows a choice. | Secondary, as in E6 |
| 5 | Scratch probes | **Allowed only after the next review fixes the variant and the parent**, at non-matrix seeds, with values disclosed as priors (SR §G.2, decision 7) | None before pre-registration |
| 6 | The product-level placement closure (E8-I5) | **Left to promotion.** The research experiment keeps the blindness protocol. | Scope it in the next review |

---

## N. Decisions of the Research Lead (2026-09-30)

§M is kept as it was proposed. Where a decision below differs from §F or §L, **this section governs.**

**The sharpened core question**, in the research lead's words:

> **Can an explicit spatial-sensing action, competing directly for the per-tick action opportunity, create repeated opponent-dependent acquisition choices without collapsing into a universally dominant search strategy?**

| # | Decision | The research lead's ruling |
|---|---|---|
| 1 | Direction | **K-S.** Advance it to the full E8 design review. K-G stays in reserve, Branch A′ is the fallback, and K-D is closed. *"Branch A′ answers whether agents can adapt, but right now the more fundamental unanswered question is whether there is a better mechanism worth adapting to."* |
| 2 | Variant | **Replace passive sensing** rather than layer the scan on top of it. *"The additive version risks making the new action redundant because the agent continues receiving free local information."* The replacement is to be treated **explicitly as a mechanism substitution, not as the isolated effect of adding one action.** |
| 3 | Parent | **An E6 treatment Ruleset may serve as E8's parent.** Parenthood **does not confer candidate status on E6**. It is simply the closest frozen experimental environment in which the new mechanism can be isolated, and it makes the E6 → E8 causal lineage easier to defend. The disruption regime of that parent (SYN6 §G.1) remains for the full review. |
| 3a | A conceptual companion | **The same active scan with passive sensing retained**, to separate an effect of the scan itself from an effect of removing automatic sensing, without escalating to a two-parent factorial. The full review decides whether this companion earns a cell. |
| 4 | Requirement C | **Registered as a hypothesis, interpreted only after it is established that agents actually experienced repeated meaningful choices.** First show there was something to adapt to, then ask whether allocation changed. Otherwise a fixed allocation could wrongly read as evidence against adaptation, when the mechanic never presented a usable choice. |
| 5 | Scratch probes | **Only after the parent and variant are frozen, and only for mechanism validation, never outcome optimization.** In scope: action charging, observation boundaries, replay determinism, the absence of accidental free sensing, coexistence with READ, and tick and callback behavior. Out of scope: any tuning toward attractive win rates. |
| 6 | Product placement (E8-I5) | **Left for promotion.** What becomes an observation fact and a replay fact is experimental semantics, and the full review must still settle it. How the feature might appear in a product belongs later. |

**Where these rulings differ from the text above:**
- **Variant b's footing.** §F and §L describe variant b as one mode field against `research-scale`. Under rulings 2 and 3, it is instead **a substitution of the sensing mechanism on an E6 treatment parent**, read as a substitution.
- **The companion.** It is ruling 3a's variant-a companion, not a second disruption parent.

**What the full design review must also carry:**
- **Channel balance.** K-S does not need READ, MOVE-search and active scanning to be equally attractive. It does need **no universally dominant acquisition channel**. If one mechanism is rational in essentially every relevant state or matchup, the result is another search race rather than an opponent-dependent resource decision.
- **The sequence.** The full review still stops before implementation or pre-registration.

---

## What This Review Does Not Claim

- **No result.** Every claim that a family would create, remove or preserve a choice is [INFERENCE]. No match, probe or prototype was run.
- **No specification.** No Ruleset name, parameter value, matrix, population or seed is set.
- **No promise that K-S works.** It is the best-placed family to take to a full design review, with named gates and reachable stop conditions.
- **No permanent rejection.** K-G is reserve, K-D is set aside with a return condition, and Branch A remains open.
- **No change to any record.** E6's verdicts, `R-CREATES` and REJECT stand. The E7 closure stands. SYN6 is not edited.
- **No reinterpretation of E6's no-detection share.** Appendix A.3 shows only that the frozen records are consistent with a population-structure reading. They do not separate it.

---

## Appendix A. Arithmetic

### A.1 The price of discovery and the tick-2 capture

[ARITH] The constants:
- Q = 8 actions per entrant per tick (SR §D.1).
- A core has 8 cells, and capture needs the victim to own none of them at the end of a tick (SR §D.1). So a discovery-dependent attacker needs 8 WRITEs to the core in one tick against a non-repairing victim.
- Discovery costs *k* actions: a MOVE sweep at d = 32 has *k* ≤ 7, mean ≈ 3.99; a READ stride search has at most 49 READs, mean 25.4 (DR §G.1).

What follows:
- **Discovery within tick 1** (*k* ≤ 8) leaves 8 − *k* < 8 actions in tick 1, so no tick-1 capture. Tick 2 has all 8, so a tick-2 capture is possible against a non-reacting victim, inside PR's bound of tick ≤ 3 (O-5). **This holds for any *k* ≤ 8, including E6's sweep.** E6-H3 was REFUTED against the reacting defenders.
- **As *k* → 0**, the game approaches the parent, where information is free and SPLIT is universal (E6-H1C REFUTED).

### A.2 Directed travel under a free bearing

[ARITH] A = 512 and d = 32, with a maximum MOVE of 64 (`ruleset_policy.py:349–361`). Seeded placement keeps cores at least 64 cells apart (SR §D.1). An enemy anchor on its core is therefore at circular distance *D* ∈ [64, 256].
- **With a known direction,** the MOVEs needed to come within d are ⌈(*D* − 32)/64⌉ ∈ {1, 2, 3, 4}.
- **Without one,** the recorded sweep takes at most 7, mean ≈ 3.99 (DR §G.1).

### A.3 No-detection cells and population structure

[ARITH] Five members never MOVE-search: STEALTH (search `read`), and LURK, GUARD, EVADER and GREED (search `none`) (PR §3.1). Their pairings among themselves are 5 × 4 = 20 ordered F1 pairings × 32 seeds = **640 cells**. E6 records 684 no-detection cells (E6-R §F.1).

[INFERENCE] The records are consistent with most no-detection cells coming from these pairings:
- **The member detection rates are close to a bound.** GUARD, GREED and LURK detect in 261, 258 and 258 of 512 entrant-appearances (E6-R §F.1).
- **That bound is the MOVE-searching opponents.** RUSH, PACED, SPLIT and ADAPT are 4 of each member's 8 opponents, which is 4 × 64 = 256 appearances.
- **What the records do not give** is a per-pairing detection count. This is consistency, not a separation (F-5).

---

## Appendix B. Sources

**The governing record:** [`V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md) (SYN6).

**Committed records** (`docs/research/v6/`):
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) §G, §H
- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) §B–§G
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) §C.4, §E, §G, §H
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) §0–§10
- [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) §2
- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) §D–§I, Appendix T
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md) §3, §4, §5
- [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md) §5–§7, §11, §13

**Source at `fd01074`:**
- `engine/src/battle_engine/agent_api.py:232–244` (`ObservationV2`) and `:261–264` (`AgentV2`)
- `engine/src/battle_engine/process_runtime.py:757–763` (core cells), `:800–850` (suppression and visibility), `:999–1011` (v2 action validation), `:1013–1024` (snapshots), `:1274–1308` (MOVE and READ)
- `engine/src/battle_engine/ruleset_policy.py:162` (anchor placement) and `:349–361` (the MOVE bound)
- `engine/src/battle_engine/replay.py:92–111` (event types) and `:359` (unsupported types rejected)
