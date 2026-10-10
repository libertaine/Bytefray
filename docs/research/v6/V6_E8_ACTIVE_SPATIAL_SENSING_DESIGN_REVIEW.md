# Bytefray V6 E8 — Active Spatial Sensing: Design and Adversarial Review

**Status:** A design and adversarial review only, after two passes. **Approved by the research lead on 2026-09-30 as the E8 design boundary: GO WITH CONDITIONS** (§N). The rulings are recorded in §O. The next step is pre-registration drafting only.
- **What it contains.** No implementation, pre-registration, probe, matrix, seed or new Ruleset identifier.
- **Values.** Values derived here are **derivations**. Actual values are frozen only in the pre-registration (§O).
- **What it changes.** No E2–E7 record, and neither synthesis.

**Branch:** `v6-research` at `dffe531`, pushed. This file is the only change in the tree.
**Date:** 2026-09-30
**Governing records:**
- [`V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md`](V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md) (**E8-MF**), with the research lead's rulings in its §N
- [`V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md) (**SYN6**)

**Other records:** SR, DR, PR, A1, E6-R, E7-DR and PA, as abbreviated in E8-MF. Also [`docs/REPLAY_SCHEMA.md`](../../REPLAY_SCHEMA.md) and [`AGENTS.md`](../../../AGENTS.md) ("Compatibility requirements").

**Evidence tiers:** [DOC], [SOURCE] (at `dffe531`), [ARITH] and [INFERENCE], as in E8-MF. Every claim that the mechanism *would* produce a behavior is [INFERENCE].

**The question**, in the research lead's words (E8-MF §N):

> **Can an explicit spatial-sensing action, competing directly for the per-tick action opportunity, create repeated opponent-dependent acquisition choices without collapsing into a universally dominant search strategy?**

**And this pass's key question**, in the research lead's words:

> **What is the minimum ordinary E8 behavior necessary for information to become valuable more than once in a match?**

### Revision 2 (2026-09-30)

**The research lead's instructions for this pass:**
- treat the relocator (a population choice) and T8+ (a mechanic choice) as separate risks;
- answer the key question above;
- keep the window as a derivation;
- make the trace semantics exact;
- make the Agent API version an explicit architecture decision.

**What changed from the first pass:**

| Item | First pass | Second pass | Where |
|---|---|---|---|
| Parent | λ = 1 recommended | **Reversed: whole-tick primary, with a λ = 1 companion.** The first pass measured whether post-contact choices are *available*. This pass measures whether they are *worth anything*. | §C.4, §E |
| The relocator (O-10) | A purpose-built relocating member was required | **Not needed under whole-tick.** An ordinary, role-justified disruption-evading defender supplies the repeated value. Under λ = 1 not even a special relocator can. | §C.4, §G.3 |
| T8+ (O-4) | Kept as a companion | **Dropped before registration.** Its passive layer is predicted near-inert, so it cannot isolate automatic from paid sensing. | §H.1 |
| Trace semantics | "A trace fact" | **The exact records named**, with no equivalent-telemetry option | §F.2 |
| Agent API version | The research-only precedent recommended | **An explicit architecture decision**, with criteria, and the precedent not used as an argument | §F.3 |
| Window | Proposed as a value | **A derivation only**, frozen at pre-registration | §C.2 |

---

## Verdict in Brief

> **GO WITH CONDITIONS** (the research lead, 2026-09-30). The conditions are listed in §N and ruled in §O. **The parent (O-3) decides whether E8 can answer its repeated-choice question at all, and the research lead ruled for the whole-tick primary.**

**Key findings.**

1. **The answer to the key question** (§C.4):

   > **Under E8's substitution, spatial information becomes valuable more than once through one ordinary behavior only: an entrant that has been located relocates its anchor to escape disruption, on a parent where a disruptive hit costs its victim materially more than the relocation. Whole-tick disruption supplies that with ordinary, role-justified members. Under λ = 1 no ordinary behavior does, and no purpose-built relocator can supply the missing value.**

   Why [SOURCE + ARITH + INFERENCE]:
   - **Anchor position matters for one thing.** Cores are fixed. Reach is free and maximal, so an anchor's position matters only as a disruption target: every READ, WRITE and sensing action reaches the whole arena from anywhere, and passive sensing is off.
   - **Under whole-tick disruption, re-finding pays.** A hit costs its victim 6 or 8 offers, against 1 under λ = 1 (PA §8). Re-finding an anchor that has evaded costs at most 3 sensing actions, about 2 in expectation (Appendix A.3).
   - **Under λ = 1, re-finding pays nothing.** A hit trades one attacker action for one victim offer, so re-acquisition buys nothing a core write would not.
2. **The substitution removes the ordinary reason E6's members moved.** Search needed movement under passive sensing; under the sensing action it does not. The treatment's only remaining ordinary source of anchor movement is evasion (§C.4).
3. **Parent: whole-tick primary (T-E6's Ruleset), with a λ = 1 companion (T-E6L's Ruleset)** (§E). This reproduces E6's primary-and-companion structure.
   - **Its costs are made mandatory controls:**
     - the lockout channel;
     - repeated choices keyed to parity;
     - an ordinary evader that is callback-phase-sensitive by construction;
     - parity-stratified seat quantities and mechanism tables.
   - **The companion carries an a-priori expectation.** H8-REPEAT is expected not to be SUPPORTED under λ = 1.
4. **T8+ is dropped** (§H.1).
   - **The passive layer would be near-inert.** At the price-matched window, the sensing action weakly dominates the sweep. Anchors are then static apart from evasion, and spawn separation (≥ 64) exceeds *d* = 32.
   - **In this population, automatic sensing carries information only through movement.** That is the searcher's own sweep, and the warning a defender gets when a sweeping searcher comes near. Both vanish with search movement, and T8+ cannot restore either. **The C8 against T8 contrast *is* the channel substitution.**
5. **The ordinary evader is callback- or tick-phase-sensitive by construction.** To evade after being disrupted, an entrant must infer the hit, from a skipped tick or from damage. It therefore overlaps E8-I4's stress class (§C.4, §G.3).
6. **Trace semantics are exact** (§F.2).
   - **The acting callback's `decision_v2` record is authoritative** for both the sensing action and its returned result, through a new optional result field.
   - Where the same process has a next callback, its observation must agree. That is a consistency gate, not the source of truth.
   - The trace's compatibility policy lets optional fields be added without a schema-version change (`agent_trace.py`).
7. **The Agent API version is an architecture decision** (§F.3).
   - **What is qualitatively new is a Ruleset-bound package.** An invalid v2 action makes the entrant forfeit (`process_runtime.py:1189–1212`). So a package that uses the new action forfeits under every other Ruleset.
   - **The options:**
     - a research-only, Ruleset-gated extension, justified by stated criteria;
     - a declared capability, refused before the match;
     - a new generation.
8. **The window stays a derivation.** Half-width 27 price-matches E6's sweep: at most 7 actions, with an expectation of 4 against 3.99. **The window and its exact coverage and traversal semantics are frozen together** in the pre-registration (§C.2).

---

## A. Baseline and Scope

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `dffe531`, pushed |
| Scope | E8-MF §N, and the research lead's instructions for this pass (Revision 2) |
| Records read | E8-MF; SYN6; DR §C, §E, §F, §G, §H, §J, §K; SR §B–§G; PR §0–§12; A1 §2–§3; E6-R §D–§I; E7-DR §3–§5, §14; PA §5–§8; REPLAY_SCHEMA.md; AGENTS.md ("Compatibility requirements") |
| Source read | `agent_api.py:14–36, 160–175, 195–244, 405–425`; `agent_trace.py:14–36, 140–215`; `agent_worker.py:540–552`; `process_runtime.py:600, 757–763, 800–860, 999–1024, 1032–1044, 1164–1212, 1274–1308`; `ruleset_policy.py:162, 177, 305–361`; `replay.py:92–111, 359`; the E6 family policy source (`tools/research/v6/e6/fixtures/agents/e6_q01/agent.py`) |
| Not done | No probe or prototype, and no gameplay match |

---

## B. The Mechanism, Stated Exactly

### B.1 What is substituted

Per E8-MF §N, ruling 2, this is **a mechanism substitution**, read as a substitution:

| | Control (the parent) | Treatment |
|---|---|---|
| Passive enemy-anchor visibility | Within min(reach, 32) of an unsuppressed friendly process (PR §2) | **Off.** `visible_enemy_anchor_addresses` is always empty. |
| The sensing action | Not available; rejected (§F.3) | **Available:** §B.2 |
| READ, WRITE, MOVE, capture, disruption, scheduling, scoring, placement, anchor spawn | Unchanged | Unchanged |

[SOURCE] Passive sensing is governed by `detection_radius` through `resolve_sensing_radius` (`ruleset_policy.py:177, 336–347`), and validation rejects values below 1 (`:305–312`). So **"off" needs a sensing-mode field**: one Ruleset-owned field whose treatment value turns passive visibility off and enables the action. AGENTS.md puts gameplay semantics on `RulesetPolicy`, not on a request override.

### B.2 The sensing action

| Property | Proposal | Why |
|---|---|---|
| Form | A new research-only `ActionKindV2` member, with one integer operand: the target address | v2 has exactly three actions (`process_runtime.py:999–1011`) |
| Reach | The target must lie within the acting process's declared reach, as for READ | Keeps acquisition independent of movement |
| Price | One offer, charged exactly as any action | The competing use is Q (E8-MF §C.3) |
| What it reveals | The addresses of **live enemy anchors** within circular distance ≤ *w* of the target. Co-located anchors collapse to one address (`process_runtime.py:823–835`). | Anchors only. Ownership stays READ's. |
| When it observes | At the instant it executes | — |
| Delivery | To the **acting process**, at its next callback, as an additive "previous sensing result", modeled on `previous_read_value`/`previous_read_owner` | The same rule as READ |
| Effect on match state | None | A trace fact, not a replay fact (§F) |
| Exposure | **Silent** (X0) | §B.4 |

### B.3 Suppression

- **No callback, no sensing.** A suppressed process gets no callback, so it cannot sense. This is existing semantics (`process_runtime.py:800–821`).
- **Delivery waits** for the acting process's next callback.
- **Coupling 1 becomes pure action denial** (E7-DR §3.1). There is no passive view left to blind.

### B.4 Exposure

| Option | What the sensed entrant learns | Cost |
|---|---|---|
| **X0, silent** (proposed) | Nothing | Removes E6's mutual-exposure property. That removal is part of the substitution, and it is disclosed. |
| X1, scanner revealed | The acting process's anchor | A new free channel: information the target did not pay for, which probe P-3 must rule out. A second rule. |
| X2, scanned flag | That it was sensed | A second rule, with an ambiguous use |

### B.5 What stays free, and what is public

- **Free, as today:** the entrant's own geometry, the previous READ result, the callback-timing fields `last_callback_tick` and `previous_action_tick`, and the context (`agent_api.py:195–244`).
- **Public:** the window half-width, as an additive `MatchContextV2` field. A member uses it to tell which condition it is in (§G.2).

### B.6 Ruleset invariants for the future qualification

- **S-1, no free sensing.** Under the treatment, no enemy anchor address ever appears in an observation except in a sensing result or a READ result.
- **S-2, exact window.** The result equals the live enemy anchors within ≤ *w* of the target at execution, re-derived independently from the trace (E6's D-1 pattern).
- **S-3, no match-state change.** Replay tick records are identical to those of a READ at the same offer.
- **S-4, parent identity.** The parent's goldens reproduce with the new fields at their defaults.
- **S-5, rejection elsewhere.** Every other Ruleset rejects the action.

---

## C. Channel Economics, the Window, and When Information Pays Twice

### C.1 The reference prices

[DOC] At A = 512, *d* = 32, a 64-cell MOVE and a minimum core separation of 64 (DR §G.1; SR §D.1):

| Channel | What it finds | Cost to find an anchor still on its core | Side effects |
|---|---|---|---|
| **MOVE sweep** (control only) | Anchors, through passive visibility | At most 7 MOVEs; mean 1537/385 ≈ 3.99 | Relocates the sensor, and is mutually exposing |
| **READ stride search** (every condition) | Core cells: value and owner | At most 49 READs, mean 25.4, plus up to 7 to locate the base | None |
| **The sensing action** (treatment only) | Anchors, inside a window | §C.2 | None under X0 |

### C.2 The window: a derivation, frozen only at pre-registration

[ARITH; Appendix A.1] An enemy core base lies in a **385-cell** arc. A window of 2*w* + 1 cells tiles it in at most ⌈385 / (2*w* + 1)⌉ sensing actions. Expectations use DR §G.1's model, in which each position is equally likely.

| Half-width *w* | Window | Worst case | Expected | Compared with the MOVE sweep |
|---|---|---|---|---|
| **27** | 55 | **7** | **1540/385 = 4** | Price-matched: the same worst case, and +0.008 in expectation |
| 32 | 65 | 6 | 1335/385 ≈ 3.47 | Footprint-matched; about 13% cheaper |

- **The comparison basis the research lead accepted:** matching the movement sweep's acquisition budget (Revision 2). **w = 27 is the derivation that achieves it.**
- **What the pre-registration freezes, together** (O-1):
  - the window;
  - its exact coverage semantics: inclusive, circular distance ≤ *w*;
  - its traversal semantics: the tiling and the order in which a member covers the arc and re-finds an evaded anchor (Appendix A.1, A.3). The expected costs depend on that order.
- **The disclosure for F-13 stands.** Price-matching is motivated by E6 being the only recorded price at which opponent dependence was shown. The number itself comes from geometry.

### C.3 Channel balance

The research lead's condition is that the channels need not be equally attractive, but none may be universally dominant (E8-MF §N). [INFERENCE + ARITH]

| State | Rational channel under the treatment |
|---|---|
| Spawn discovery against an anchor still on its core | **The sensing action** (mean 4, against READ's 25.4) |
| A core whose anchor has left it | **Sensing, then READ.** At most 16 stride-8 READs hit a core cell (Appendix A.2). |
| Damage to one's own core | **READ only.** The action reveals anchors, not ownership. |
| An anchor that moved after being located | **Sensing, again**, when it pays (§C.4) |
| Defending or painting | **Possibly none** |

The dominance risk is local to spawn discovery. H8-CHANNEL tests whether one acquisition policy is best against every opponent (§H.2).

### C.4 The key question: the minimum ordinary behavior for information to pay more than once

**Step 1. What spatial information is for, under the treatment** [SOURCE + DOC]:
- **The enemy core's location.** It is fixed at initialization (`process_runtime.py:757–763`) and needed for capture. **It pays once**, and stays known.
- **Enemy anchor positions.**
  - Reach is declared once, free, up to half the arena, and E6's members all declared 256 = A/2 (SR §B.2; PR §5.2). So READ, WRITE and the sensing action all reach the whole arena from anywhere.
  - Passive sensing was anchor-centred, and it is off.
  - **So under the treatment an anchor's position matters for one thing only: as a disruption target.**
- **The state of one's own core.** Only READ gives it. It is repeatedly valuable by nature, and it is **unchanged by the substitution**: it exists in every condition, as ADAPT's check did in E6. **It does not bear on the sensing action's repeated value.**

**Step 2. What "valuable more than once" needs.** After core discovery, the sensing action pays again only if:
- **(a)** a target anchor **relocates** after being located, and
- **(b)** a disruptive hit on it is **worth more than re-finding it**.

**Step 3. The ordinary sources of relocation, by role** [INFERENCE]:

| Behavior | Role-justified under the treatment? | Why |
|---|---|---|
| Sensor movement for search | **No** | The sensing action does not depend on location. **The substitution removes the ordinary reason E6's searchers moved.** |
| Attackers repositioning | **No** | Reach is free, and maximal reach dominates (SR §B.2). Nothing is gained by moving closer. |
| Evasion before discovery (E6's EVADER) | **Once** | The first sensing hit then gives an anchor, not a core, and a second acquisition, by READ, follows (Appendix A.2). Information pays twice, then is exhausted. |
| **Evasion after being disrupted or damaged** | **Only where disruption is costly** | Evasion cannot protect a fixed core. It only defeats disruption aimed at the old address. |
| Monitoring one's own core | Always | But by READ, in every condition (Step 1) |

**Step 4. The arithmetic of (b)** [ARITH; PA §8; Appendix A.3–A.4]:
- **What a hit costs its victim:**
  - **whole-tick:** 8 offers in a tick its opponent moves first, where it gets no callback at all, and 6 in its own first-mover tick, where it keeps offers 0 and 1;
  - **λ = 1:** exactly 1.
- **What evasion costs:** one MOVE.
- **What re-finding costs.** An anchor that evaded by 8 to 64 cells, in an unknown direction, is re-found in at most **3** sensing actions at *w* = 27, and **225/114 ≈ 1.97** in expectation.
- **Under whole-tick disruption:**
  - re-acquiring, at about 2 actions, buys hits worth 6 to 8 victim offers each;
  - evading, at 1 action, avoids them.
  - So a **find → hit → evade → re-find** loop is rational for ordinary attackers and defenders. [INFERENCE]
- **Under λ = 1:**
  - a hit trades one attacker action for one victim offer, which is no better than writing one more core cell;
  - re-acquiring a moved anchor, at about 2 actions, therefore buys nothing, and evading, at 1, avoids nothing worth more than 1.
  - **No ordinary behavior makes spatial information pay more than once.**
  - **A purpose-built relocator would create re-acquisition *opportunities* without *value***, because the value comes from disruption, not from movement. [INFERENCE]

**The answer:**

> **Under E8's substitution, spatial information becomes valuable more than once through one ordinary behavior only: an entrant that has been located relocates its anchor to escape disruption, on a parent where a disruptive hit costs its victim materially more than the relocation. Whole-tick disruption supplies that with ordinary, role-justified members. Under λ = 1 no ordinary behavior does, and no purpose-built relocator can supply the missing value.**

**What follows:**
- **For O-10, the relocator.**
  - **Under whole-tick, no purpose-built relocator is needed.** The family needs an ordinary, role-justified **disruption-evading defender**, and attackers that evade counter-disruption (§G.3).
  - **H8-REPEAT is then a field-level hypothesis.** Its evidence is reported per pairing and by the cause of each re-acquisition (§H.2). Its expected concentration in pairings where disruption occurs is shown, not hidden.
- **Under a λ = 1 primary, the answer is "none".**
  - H8-REPEAT is predicted not SUPPORTED by construction, and C's precondition could not be met.
  - A relocator would scope H8-REPEAT to its own pairings (E8-MF §N, ruling 4), without making repeated information valuable.
  - E8 would then answer only a one-shot substitution question. **That is the meaningful limitation the research lead asked to know before pre-registration.**
- **The evasion trigger is tick- or callback-phase-sensitive.**
  - To evade after a hit, an entrant must know it was hit. [SOURCE] The observation carries `last_callback_tick` and `previous_action_tick` (`agent_api.py:233–235`), so a skipped tick can be inferred. Damage can also be read.
  - Either way, **the ordinary evader is callback- or tick-phase-sensitive by construction.** It overlaps E8-I4's stress class, and its seat effects must be read with mechanism tables (§H.3).
- **A confound in the control.** Under C8, searchers' own sweeps move their anchors, so there re-acquisition also arises from search movement. Under T8 it arises only from evasion. **Re-acquisition must be reported by cause**, evasion or search movement, from the traces. Otherwise a difference between C8 and T8 would partly reflect only that searchers stop moving.

### C.5 The delayed-forced-line check

[ARITH; E8-MF Appendix A.1] At *w* = 27, discovery completes within tick 1 at worst: 7 ≤ 8. A tick-2 capture against a non-reacting victim is possible, as it was under E6's sweep. E6-H3 was REFUTED against the reacting defenders. The risk is a registered kill (KC-4's form).

---

## D. Timing, Chunks and Seats

[SOURCE] Each pass gives each entrant a chunk of two offers. Seat A moves first on odd ticks and Seat B on even ticks (SYN §A.6; PA §8).

- **Sense and hit fit in one chunk.** The result arrives at offer 1.
- **Under whole-tick disruption, a lucky first action locks out a tick.** A lucky first sensing action (1/7 at *w* = 27; the sweep's first MOVE in E6 was 33/385 ≈ 0.086) lets the first mover lock the second mover out of that tick (PA §8).
- **The loop is parity-structured.** Under whole-tick, a hit victim next acts at offers 0 and 1 of its own first-mover tick (PA §8). A disruption-evader's MOVE then comes first in that tick, before the attacker's stale re-hit. So **the loop of §C.4 runs on tick parity.**
- **Under λ = 1** the victim loses one offer per hit (PA §8).
- **Callback counting.** Delivery is per callback, and the ordinary evader infers hits from callback gaps. So callback counting couples to both delivery and disruption (E7-DR §3.1, coupling 2; §C.4).

---

## E. The Parent Regime

**This section reverses the first pass's recommendation.**
- **What the first pass argued.** λ = 1 protects the *availability* of a victim's post-contact choices: 7 of 8 offers are kept, against parity-keyed halving under whole-tick.
- **What it missed.** §C.4 shows that under λ = 1 those choices have **no ordinary value**. Spatial information after discovery pays only for disruption, and λ = 1 makes disruption a one-for-one trade. So λ = 1 protects a choice space with nothing worth choosing.
- **The reversal.** Under the research lead's own test, "first prove there was something to adapt to" (E8-MF §N, ruling 4), whole-tick disruption is **the only parent in which E8's repeated-choice question can be answered from ordinary behavior.**

| | Whole-tick parent (T-E6's Ruleset) | λ = 1 parent (T-E6L's Ruleset) |
|---|---|---|
| **Repeated value of spatial information** | **Present with ordinary roles:** hits cost 6 to 8 offers, and evading costs 1 (§C.4) | **Absent by construction:** a hit costs 1 |
| **Post-contact choices** | Fewer, and parity-keyed (PA §8) | Mostly retained, but not valuable |
| **Lineage** | The E6 primary arm | E6's companion |
| **Seat evidence** | Part of KC-5's mechanism (E7-DR §4; PA §7.1). First-mover control under E2 and E3. | Not seat-clean: 819/1000 (E7-DR §3.3). A strong last-mover skew (E3-R §F.8). |
| **Stalling floor** (E6's family) | 0.225 (E6-R §D.2) | 0.583 (E6-R §D.5) |

**Recommendation: whole-tick primary, with a λ = 1 companion** (O-3, O-12). This is E6's own structure. **Ruled by the research lead on 2026-09-30** (§O).

**Mandatory under the whole-tick primary:**
- parity-stratified seat quantities (§H.3);
- mechanism tables before any seat flag is read causally;
- E8-I4's stress member, with the ordinary evader's own phase-sensitivity recorded;
- post-contact choices reported per parity.

**The companion:**
- It applies the same substitution on T-E6L's Ruleset.
- It is **a status comparison, never a verdict.**
- Its **a-priori registered expectation:** H8-REPEAT is not SUPPORTED under λ = 1. If it is SUPPORTED there, §C.4's analysis is wrong, which is informative in itself.

**A two-parent factorial is now justifiable, but is not recommended.**
- E8-MF §F allowed a factorial only if the mechanism cannot be separated from the disruption regime. §C.4 shows that the *repeated-value* mechanism cannot.
- But requirement G asks for the single parent plus companion first. E8's primary question is answered in the primary arm, and the dependence on disruption cost is predicted by arithmetic and checked by the companion's status.
- **If the research lead wants that dependence estimated**, it must be registered as a factorial estimand. A companion cannot answer an interaction (SYN6 §H, item 2).

**What this recommendation does not rest on:**
- **Not "whole-tick looked better".** It rests on where the measured phenomenon can exist.
- **Not candidate status.** Parenthood confers none (E8-MF §N, ruling 3).
- **Not an endorsement of the KC-5 channel.** That channel is present by choice, and it is controlled, not ignored.

---

## F. Observation, Trace, Replay and the Agent API

### F.1 Observation, context and replay

| Surface | Proposal | Basis |
|---|---|---|
| **Observation** | An **additive previous-sensing result** on `ObservationV2`, empty by default and populated only for the acting process at its next callback. Under the treatment, `visible_enemy_anchor_addresses` is always empty. | Modeled on `previous_read_value`/`previous_read_owner` (`agent_api.py:242–244`) |
| **Context** | The window half-width, public, as an additive `MatchContextV2` field | The `detection_radius` precedent for *context* (`agent_api.py:220–228`) |
| **Canonical replay** | **Not a replay fact.** The action changes no match state (S-3). REPLAY_SCHEMA.md reserves per-callback history for the optional trace surface, and a replay event would need an explicit schema version (AGENTS.md; `replay.py:359`). This refines E8-MF §G. | REPLAY_SCHEMA.md ("Python Observation capture: explicitly out of scope") |

### F.2 Trace semantics: the exact records

The research lead requires the pre-registration to name the exact callback and action record that establishes a sensing action occurred, and exactly what it returned. **"Equivalent telemetry" is not an option.** [SOURCE] The trace is `bytefray.agent_trace`, and each callback writes one `DecisionRecordV2` (`record_type` `"decision_v2"`). It carries `agent_id`, `process_id`, `observation` (a `TraceObservationV2`), `action` (a `TraceActionV2`: `kind`, `operand`, `value`) and `applied_result` (a `TraceResultV2`: `status`, `normalized_address`, `read_value`, `read_owner`) (`agent_trace.py:140–203`).

**Proposed semantics**, for the pre-registration to freeze by name:

| Fact | The record that establishes it |
|---|---|
| **A sensing action occurred** | The acting callback's `decision_v2` record. `action.kind` is the new kind's wire value, `action.operand` is the target, and `applied_result.status` is the applied status. The normalized target is in `applied_result.normalized_address`. |
| **It was refused** | The same record, with `applied_result.status` set to a rejection status. The target out of reach follows READ's existing `REJECTED_OUT_OF_REACH` pattern (`process_runtime.py:1293–1299`). |
| **What it returned** | **A new optional `TraceResultV2` field on the same record:** the sorted tuple of revealed enemy anchor addresses. An empty tuple means sensed and found nothing. The field's absence means the record is not a sensing action. |
| **Which record is authoritative** | **The acting callback's `decision_v2` record is authoritative for both the sensing action and its returned result** (the research lead, 2026-09-30). No fact about a sensing action depends on any other record. |
| **Consistency with delivery** | **A consistency gate, not the source of truth.** *If* the same process has a next `decision_v2` record, its observation's additive previous-sensing field (mirrored into `TraceObservationV2`) must equal the authoritative tuple. There may be no next callback: the process may be suppressed, the entrant may be eliminated, or the match may end. The gate then has nothing to check, and the authoritative record still stands. |
| **That the trace belongs to the match** | The trace's `BindingRecord` (`replay_sha256`, `ruleset_id`) |
| **That the return was correct** | An independent re-derivation from tick-0 anchors and the ordered action stream (S-2, E6's D-1 pattern) |

- **Compatibility.** [SOURCE] The trace's policy says readers ignore unknown keys, so "a future minor addition of a new, optional field is not a breaking change". The same policy rejects any other `schema_version` (`agent_trace.py:18–31`). So the two optional fields need no trace schema-version change, **but their names must be frozen in the pre-registration.**
- **Traces are required for every control and treatment cell** (PR §6.6).

### F.3 The Agent API version: an architecture decision

The research lead ruled that this is an explicit architecture decision, and that E6's additive-context precedent is **not** an automatic argument.

**The facts** [SOURCE]:
- **What the version gates.** `AGENT_API_VERSION` is 2, and `SUPPORTED_AGENT_API_VERSIONS` is {2}. A package declares its `api_version`, and the loader refuses unsupported ones (`agent_api.py:16, 34, 417`). The version gates which contract generation a package is written against.
- **The earlier unbumped additions were of two kinds:**
  - context fields: `parameters` and `detection_radius`, both additive and defaulted;
  - the v1 `MOVE` and `LOCAL_*` members, justified because "an agent that never emitted them observed and behaved exactly as before" (`agent_api.py:160–170`).
- **An invalid v2 action makes the entrant forfeit** (`process_runtime.py:1189–1212`).
- **How actions cross the worker boundary.** The worker serializes an action's kind by value, and the engine decodes it by enum (`agent_worker.py:541–549`; `process_runtime.py:600`).

**What is qualitatively new.** The new action is **a legal return under one Ruleset family only**.
- **A package that uses it is Ruleset-bound:** it forfeits under every other Ruleset.
- **v2 has no way to declare that dependency.** A context field never had this property, because not reading it is harmless.

**The options:**

| | Option | What it does | Cost |
|---|---|---|---|
| **A1** | A research-only, Ruleset-gated extension within v2 | Documented in AGENT_API_V2.md with **stated criteria**, and detectable from the public context field | The least. The forfeit risk remains, limited to misconfiguration. |
| **A3** | A **declared capability** within v2 | A package names the extensions it requires, and the loader or harness refuses it before the match under a Ruleset that lacks one | A new, general concept, but it converts the Ruleset-bound forfeit into a refusal before the match |
| **A2** | A new generation, v3 | Packages that may return the action are v3 | A research mechanic defines a public API generation, with a new supported set, package validation, scaffold and documentation |

**Criteria that would justify A1**, stated so that the decision does not rest on precedent:
- (i) **No existing package's behavior or wire shape changes.** The observation field is additive and defaulted, and the enum member is new.
- (ii) **The member is legal only under research Rulesets**, and rejected everywhere else (S-5).
- (iii) **E8's packages are research fixtures, run only by the harness**, which fixes the Ruleset per cell.
- (iv) **A static discipline gate** (PR D-5's pattern) checks that a family package returns the action only when the public context field is present. [INFERENCE]
- (v) **Before any product Ruleset may accept the member, A2 or A3 must be decided.**

**Recommendation: A1 with criteria (i)–(v) for the research experiment, and A3 as the promotion prerequisite** (O-6). A2 is not recommended while the member is research-only.

**The research lead's ruling (2026-09-30).** A1 is approved for the E8 research experiment, **with mechanical containment**:
- only E8 research Rulesets accept the new action;
- E8 packages declare, or are statically identified as, requiring it;
- **the E8 harness rejects an incompatible package and Ruleset pairing before a match starts**;
- existing product and stable Rulesets remain unchanged;
- ordinary v2 agents remain valid;
- the action stays off normal product-facing surfaces.

**For a product Ruleset, A3 is required:** capabilities are declared, and incompatibility is rejected before execution. **A2, a new generation, is chosen only if implementation reveals an actually incompatible contract**, rather than an additive action.

---

## G. The Matched Family

### G.1 Carried over from E6

- **One policy source**, with parameters supplied through `MatchContextV2.parameters`.
- **Opaque package identifiers**, and the static discipline gate (PR §3.2, D-5).
- **Engine-level behavior tests before any seed** (A1 §2).
- **Seed-varying choices** (SR §F).
- **E6's packages cannot be reused**, because their search depends on passive visibility.

### G.2 How one member plays under each condition

A member is an **allocation policy**, not an action stream (E8-MF §N, ruling 2). Each condition supplies its own spatial channel:

| Member's parameter | Control (passive, d = 32) | Treatment (passive off, sensing on) |
|---|---|---|
| *acquire* = spatial | The MOVE sweep | The sensing action, with the tiling of §C.2 |
| *acquire* = ownership | READ stride | READ stride |
| *acquire* = none | None | None |

- **How a member knows its condition.** From the public window field, present only under the treatment.
- **The rule is fixed a priori and tested before seeds** (E6's CQ-1 in a new form).
- **This is a correctness requirement, not only a design choice** [SOURCE]. A member that returned the sensing action under the control would forfeit (§F.3), so criterion (iv)'s static gate checks it.

### G.3 The roles

This lists roles, not a roster. The count and the parameters belong to the pre-registration.

| Role | Purpose | E6 analogue |
|---|---|---|
| Fast spatial acquirer (attack) | The high-acquisition baseline | RUSH |
| Paced spatial acquirer (attack) | The lower-information contrast: it differs only in pace | PACED |
| **Re-acquiring** acquirer (attack) | **The H8-REPEAT contrast.** It differs from the fast acquirer only in re-acquiring after an anchor it has hit moves. | New |
| Ownership acquirer (attack) | The channel contrast: READ only | STEALTH |
| Non-acquirer (attack) | Pure lower information | LURK |
| Sensor–striker split | Division of labor across processes | SPLIT |
| Stationary defender | Repairs and disrupts known anchors | GUARD |
| **Disruption-evading defender** | **The ordinary, role-justified source of repeated value** (§C.4). It relocates its anchor when it infers it has been hit, from a callback gap or from damage. **This replaces the first pass's purpose-built relocator.** | EVADER, redirected from a first-callback move to evasion after a hit |
| Painter | Tests greed tilt | GREED |
| Adaptive member | Requirement C (§H.5). Its rule uses mechanism-level observables only. | ADAPT |
| **Tick- or callback-phase stress member** | E8-I4, kept deliberately. It is **separate** from the adaptive member (O-9). Note that the disruption-evading defender is phase-sensitive by construction too (§C.4). | ADAPT's check (E7-DR §4.4) |

- **One parameter per contrast.** Each registered contrast differs in exactly one parameter (PR O-2).
- **Evasion toward attackers too.** Whether attackers also evade counter-disruption is a parameter of the attack roles, fixed a priori.

---

## H. Pre-Registration Outline

This is not a registration, and it sets no thresholds.

### H.1 Conditions, and why T8+ is dropped

**The conditions** (O-3, O-4):
- **Primary**, on T-E6's Ruleset (whole-tick):
  - **C8**, the parent, run with the new family;
  - **T8**, the substitution.
- **Companion**, on T-E6L's Ruleset (λ = 1):
  - **C8L** and **T8L**, the same pair;
  - a status comparison, never a verdict (§E).

**T8+ is dropped before registration.** This answers O-4 as the research lead framed it: T8+ is treated as a possible second mechanic, not as a companion by default.
1. **The sweep would be abandoned.** At the price-matched window, the sensing action costs what the sweep costs (4 against 3.99). It does not relocate or expose the searcher. So it is **expected to weakly dominate the MOVE sweep** for discovery (§C.3). [ARITH + INFERENCE]
2. **Anchors would then be static apart from evasion.** Spawn separation is at least 64, more than *d* = 32 (PR D-2). **Passive sensing in T8+ would rarely fire:** only when an evader happens to land within *d*.
3. **So T8+ is predicted to play as T8 plus a near-inert passive layer.** T8 against T8+ cannot isolate automatic from paid sensing: the automatic channel would be present but carry almost nothing. It is also not a distinct mechanic worth its own reading, because its dynamics are predicted to be T8's.
4. **What the attribution question needs is already in C8 against T8.** In this population, automatic sensing carries information **only through movement**: the searcher's own sweep, and the incidental warning a defender gets when a sweeping searcher comes within *d*. Both vanish together when search stops needing movement. **T8+ cannot restore the warning, because in T8+ searchers no longer sweep.** Automatic sensing and movement search are inseparable here. C8 against T8 is the channel contrast, disclosed as a substitution (E8-MF §N, ruling 2).
5. **The decision: drop T8+**, the research lead's option (b), with this reason recorded.
   - **Retaining it as a separately interpreted diagnostic would spend a condition on an outcome predicted by construction.**
   - **Re-entry condition:** a design in which passive sensing carries information not bought by movement.

### H.2 The hypotheses

| ID | Statement | Role |
|---|---|---|
| **H8-SUB** | No fixed member is a best response to every opponent under T8 | The E6-H1T analogue, read against C8 |
| **H8-PAR** | The same, under C8, with the new family | Must be re-measured for the new family |
| **H8-CHANNEL** | The best-response sets under T8 are not all met by members sharing one acquisition setting (channel × pace × re-acquisition) | "No universally dominant search strategy" |
| **H8-LESS** | Lower acquisition beats higher against at least one opponent | The E6-H2 analogue |
| **H8-REPEAT** | The re-acquiring member beats its once-only twin against at least one opponent | The precondition for requirement C |
| **H8-ADAPT** | The adaptive member does at least as well as every fixed member against the mixed field | Requirement C, read only under §H.5 |

**The eligible census for H8-REPEAT** (O-10, ruled). It is defined **from frozen behavior, before any outcome exists**. A pairing is eligible only if all three hold:
1. **The target can relocate after being located or disrupted.** This follows from its frozen policy parameters and source, not from observed play.
2. **That relocation stales the useful anchor information.** The relocated anchor falls outside what the opponent already knows, under the frozen evasion rule and the frozen window semantics.
3. **The opponent has an economic reason to re-acquire it.** It is a disruption user under a parent where a hit is worth more than the re-acquisition (§C.4; Appendix A.3–A.4).

**How H8-REPEAT is reported and scoped:**
- **It is evaluated on the eligible census only**, and reported per pairing. Every re-acquisition is classified from traces by its cause: re-finding after an evasion, or re-sighting after the searcher's own movement (§C.4).
- **If the census is effectively one defender archetype, requirement C is scoped to that stratum**, not generalized to the whole family (the research lead, 2026-09-30).
- **No purpose-built relocator is used.** The census consists of naturally evading members (§G.3).

**The claim's scope**, in the research lead's words, to be carried into the pre-registration verbatim:

> If H8-REPEAT succeeds under the whole-tick parent, E8 demonstrates repeated adaptation in an ecology where disruption makes reacquisition valuable. It does not establish that active sensing creates repeated adaptation independently of disruption economics.

**The interpretation table must be exhaustive over (H8-SUB, H8-PAR):** preserved, created, removed, none, and an explicit "no row applies". H8-CHANNEL qualifies every row.

**The companion's registered expectation** (§E): the status of H8-REPEAT differs from the primary's, and is not SUPPORTED.

### H.3 Flags, the seat criterion and the kill criteria

**Flags:**
- **Stalling**, against each parent's own floor (F-6).
- **Loss of hostile core contact.**
- **No-detection, reported per pairing** (F-5).
- **New immunity.**

**The seat criterion** (SYN6 §G.2; O-8):
- **(i) A unit-level flag** counts only if its bootstrap stability meets the program's 9/10 convention (PR O-4).
- **(ii) A family-level mean change in |GSB|** over all units, with baseline strata committed before computation (PA §5.1, §11).
- **Mandatory under the whole-tick primary:** **both are also stratified by tick parity**, and mechanism tables are required before any seat flag is read causally (§E).
- Thresholds belong to the pre-registration.

**The kill criteria:**
- a constant best response, with a search-race or channel-race label;
- greed dominance;
- stalling or loss of contact against the parent's floor;
- a delayed forced line;
- the seat criterion.

The disposition rules follow PR §8's exhaustive pattern.

### H.4 The companion's reading

The companion's reading is the E6 form (PR §6.8):
- **"Agrees"**, when the registered comparison set has the same statuses in both arms;
- **otherwise, the list of what differs**, including the expected difference on H8-REPEAT.

It is never a verdict, and it cannot answer an interaction (SYN6 §H, item 2).

### H.5 Requirement C (E8-MF §N, ruling 4)

**H8-ADAPT is interpreted only if all of these hold:**
- H8-SUB is SUPPORTED;
- H8-REPEAT is SUPPORTED on its eligible census (§H.2), with C then scoped to that census's strata;
- a registered descriptive check shows the adaptive member's allocation varied with the opponent, from its allocation log.

**Otherwise H8-ADAPT is "not interpretable"**, never REFUTED by default (F-9).

---

## I. Seeds, Blindness and Bypasses

- **Seeds.** Fresh seeds, under the seed-set blindness protocol unchanged (PR §9), with value-based redaction.
- **Seed inference is more valuable here.** It stays the one zero-action bypass (DR §E.2), and under the substitution it replaces all sensing.
  - **Kept:** the static discipline gate (PR D-5), and an in-corpus "no early strike without an information event" gate. An information event is now a sensing result, or a READ result showing an enemy cell (PR D-4's pattern).
  - **Product closure** stays at promotion (E8-I5).
- **Other channels:**
  - the sensing action adds none beyond its result under X0;
  - the READ side channel is unchanged;
  - blind writes remain a lottery (DR §F);
  - the callback-timing fields reveal only one's own suppression, not the enemy's position (§B.5).

---

## J. Mechanism-Validation Probes (E8-MF §N, ruling 5)

**Only after the parent and the variant are frozen.** Mechanism validation only, never outcome optimization. No win rate is computed or read. They use scripted, non-family agents.

| Probe | What it validates |
|---|---|
| **P-1, action charging** | A sensing action costs exactly one offer, and counts in the quota |
| **P-2, observation boundary** | The window is inclusive, circular and exact at *w*, including wrap-around (S-2) |
| **P-3, no accidental free sensing** | Under the treatment, the visible set is empty at every callback, and nothing else carries enemy positions (S-1) |
| **P-4, coexistence with READ** | READ's result and reach are unchanged |
| **P-5, replay determinism** | Replays are byte-identical, whether or not traces are enabled. No memory diff comes from sensing (S-3). |
| **P-6, tick and callback behavior** | Delivery at the next callback, within and across ticks. Under suppression, in both parents: PA §8's lockout results, re-run with the sensing action in place of the scripted attacker's hit. |
| **P-7, parent identity** | The goldens reproduce with the new fields at their defaults (S-4) |
| **P-8, rejection elsewhere** | Every other Ruleset rejects the action. A package that returns it forfeits, as §F.3 records (S-5). |
| **P-9, trace records** | The §F.2 fields appear exactly as named on the acting record. Where the same process has a next callback, that record's observation equals the acting record's tuple. The probe also covers the cases with no next callback: suppression, elimination and the end of the match. |

---

## K. STOP and REDESIGN Criteria for This Design

| # | Condition | Outcome |
|---|---|---|
| K-1 | The research lead requires scanner exposure (X1 or X2) | **REDESIGN** (§B.4, §C re-derived) |
| K-2 | No a-priori window is accepted | **STOP.** Return to K-G, or to Branch A′ (E8-MF §L). |
| K-3 | The research lead keeps a **λ = 1 primary** | **Proceed only as a scoped study.** H8-REPEAT is scoped to a purpose-built relocator's pairings, is predicted not SUPPORTED, and requirement C is not generalized (§C.4, §H.2). **E8 then answers a one-shot substitution question only.** |
| K-4 | A disruption-evading defender cannot be specified as role-justified without making stalling likely by construction | **REDESIGN** the population, or keep requirement C secondary |
| K-5 | Implementation reveals an actually incompatible contract, not an additive action (O-6) | **Move to A2**, and re-scope the implementation plan. The design stands. |
| K-6 | The whole-tick primary is chosen, and parity stratification cannot separate the loop's parity structure from a seat artifact | **REDESIGN** the seat analysis before pre-registration |

**A stop is a successful result of the method** (SR §G.1).

---

## L. Gate Status (E8-MF §L)

| Gate | Status | Where |
|---|---|---|
| **G-1**, window derived a priori | **Derived:** w = 27, price-matched. **Ruled:** the window and its coverage and traversal semantics are frozen together at pre-registration. | §C.2 |
| **G-2**, exposure and suppression semantics | **Proposed:** X0. Suppression is existing semantics, now pure action denial. | §B.3–§B.4 |
| **G-3**, variant and parent | **Ruled:** replacement, on a whole-tick primary with a λ = 1 companion. T8+ is dropped. | §C.4, §E, §H.1 |
| **G-4**, observation and replay facts | **Ruled:** the acting record is authoritative, and the next callback is a consistency gate. The replay is excluded. A1 is ruled, with containment. | §F |
| **G-5**, the family | **Ruled:** no purpose-built relocator. Naturally evading members, a predeclared H8-REPEAT census, and the stress member. | §G, §H.2 |

---

## M. Findings Register

| # | Finding | Tier |
|---|---|---|
| M-1 | "Off" cannot be written through `detection_radius`, so a sensing-mode field is needed | [SOURCE] |
| M-2 | w = 27 price-matches the sweep: 7 at worst, an expectation of 4 against 3.99 | [ARITH] |
| M-3 | No acquisition channel is rational in every state. The dominance risk is local. | [INFERENCE] |
| M-4 | Under the treatment, an anchor's position matters only as a disruption target: reach is global and passive sensing is off | [SOURCE + DOC] |
| M-5 | **The substitution removes the ordinary reason members moved** | [INFERENCE] |
| M-6 | **Spatial information pays more than once only through evasion from costly disruption.** Whole-tick disruption supplies it; λ = 1 does not. | [ARITH + INFERENCE] |
| M-7 | **Under λ = 1, a purpose-built relocator creates re-acquisition opportunities without value** | [INFERENCE] |
| M-8 | The ordinary evader is callback- or tick-phase-sensitive by construction | [SOURCE + INFERENCE] |
| M-9 | Under the whole-tick parent, the repeated-value loop runs on tick parity | [SOURCE, PA §8] |
| M-10 | **T8+ is predicted to play as T8 plus a near-inert passive layer.** Automatic sensing is inseparable from movement search in this population. | [ARITH + INFERENCE] |
| M-11 | Re-acquisition in C8 also comes from search movement, so it must be reported by cause | [INFERENCE] |
| M-12 | An invalid v2 action makes the entrant forfeit. A package using the new action is Ruleset-bound. | [SOURCE] |
| M-13 | Optional trace fields need no trace schema-version change, but must be named in the pre-registration | [SOURCE] |
| M-14 | The action is callback history, so it is a trace fact and not a replay fact. This refines E8-MF §G. | [DOC + SOURCE] |
| M-15 | Scanner exposure (X1) would be a new free channel for the target | [INFERENCE] |

---

## N. Verdict

> **GO WITH CONDITIONS** (the research lead, 2026-09-30).

**The conditions**, as the research lead set them. Each is ruled in §O.
1. **A whole-tick primary, with a λ = 1 companion** (O-3).
2. **No T8+** (O-4).
3. **No purpose-built relocator** (O-10).
4. **A predeclared repeated-reacquisition eligibility census** (O-10; §H.2).
5. **Explicit tick- or callback-sensitive stress behavior** (O-9; §G.3).
6. **Exact trace semantics.** The acting record is authoritative (O-7; §F.2).
7. **A1 research containment, with compatibility gated before the match** (O-6; §F.3).
8. **A3 before product promotion** (O-6).
9. **The derived ±27 window, frozen only at pre-registration**, together with its coverage and traversal semantics (O-1).
10. **A newly justified seat criterion**, not a copy of E6's PF-4 (O-8).

**What this review is now.** The E8 design boundary. **The next step is pre-registration drafting only**: no implementation, probe, agent or seed.

---

## O. Decisions of the Research Lead (2026-09-30)

| # | Decision | Ruling |
|---|---|---|
| O-1 | Window | **The ±27 window is approved as a derivation only.** The window and its exact coverage and traversal semantics are frozen together in the pre-registration (§C.2). |
| O-2 | Exposure | **X0, silent**, as proposed (§B.4). Not revisited. |
| O-3 | Parent regime | **Whole-tick primary (T-E6's Ruleset), with a λ = 1 companion (T-E6L's Ruleset).** *"Under λ=1, reacquiring a moved anchor costs roughly what the resulting disruption is worth, so the repeated-information choice largely disappears. Whole-tick disruption gives ordinary evasion and reacquisition real strategic value."* **The claim is scoped** as in §H.2: if H8-REPEAT succeeds, E8 shows repeated adaptation where disruption makes reacquisition valuable, not independently of disruption economics. |
| O-4 | Conditions | **C8, T8, C8L and T8L. T8+ is dropped.** *"If active sensing crowds out movement, it also removes most opportunities for passive sensing to contribute. T8+ then becomes a hybrid mechanic rather than a useful companion. C8→T8 is enough for the channel-substitution test."* |
| O-5 | Result delivery | **An additive per-process previous-sensing result**, as proposed (§F.1) |
| O-6 | Agent API architecture | **A1 for the E8 research experiment, with mechanical containment (§F.3). A3 as the promotion prerequisite.** A2 only if implementation reveals an actually incompatible contract. |
| O-7 | Trace semantics | **A trace fact, not a replay fact. The acting callback's `decision_v2` record is authoritative** for both the sensing action and its returned result. A next callback, where it exists, is a consistency gate, not the source of truth (§F.2). |
| O-8 | Seat criterion | **Newly justified, not copied from E6's PF-4:** a stability-required unit flag and a stratified family-level quantity, both parity-stratified under the whole-tick primary (§H.3). Thresholds belong to the pre-registration. |
| O-9 | Stress and adaptive members | **Explicit tick- or callback-sensitive stress behavior, kept separate from the adaptive member** (§G.3) |
| O-10 | The relocator | **Dropped. Naturally evading members are used.** The H8-REPEAT eligible census is defined from frozen behavior before outcomes exist (§H.2). If it is effectively one defender archetype, C is scoped to that stratum. |
| O-11 | Next step | **Pre-registration drafting only** |
| O-12 | Companion registration | **A status companion, with the a-priori H8-REPEAT expectation** (§E, §H.4) |

---

## What This Review Does Not Claim

- **No result.** No match, probe or prototype was run. Every behavioral claim is [INFERENCE], including the §C.4 loop and T8+'s near-inertness.
- **No frozen value.** No Ruleset identifier, matrix, population count or seed is set.
- **No promise that the substitution preserves E8-I1**, or that the §C.4 loop will appear. The design makes both testable, with reachable kills and an informative companion.
- **No candidate status for any E6 Ruleset.**
- **No change** to E6's records, the E7 closure, SYN6 or E8-MF. The refinements M-14 and §C.4's qualification of E8-MF §C.3's "repeated acquisition choice" are recorded here only.

---

## Appendix A. Arithmetic

### A.1 Tiling the arc

- **The arc.** A = 512, the minimum separation is 64, and *D* ∈ [64, 256]. That is 2 × 192 + 1 = **385** positions (DR §G.1).
- **The general formula.** With W = 2*w* + 1 and *n* = ⌈385/W⌉, the expected number of actions is E = [W × (1 + … + (*n* − 1)) + (385 − W(*n* − 1)) × *n*] / 385.
- ***w* = 27, W = 55:** *n* = 7, since 7 × 55 = 385. E = 55 × 28 / 385 = **4**, and the worst case is **7**.
- ***w* = 32, W = 65:** *n* = 6. E = (65 × 15 + 60 × 6) / 385 = 1335/385 ≈ **3.47**, and the worst case is **6**.
- **The sweep** (DR §G.1): E = 1537/385 ≈ **3.99**, and the worst case is **7**.
- **First-action success:** 55/385 = 1/7, against the sweep's 33/385 ≈ 0.086.

### A.2 Finding a core whose anchor left before discovery

Take E6's evasion magnitude *m* ∈ [8, 64], with an unknown sign (PR §12.8). The core cells then lie in [anchor − 64, anchor − 1] or in [anchor + 8, anchor + 71], two 64-cell spans. **At most 16 stride-8 READs hit a core cell**, and up to 7 more locate the base.

### A.3 Re-finding an anchor that evaded after being located

- **Where the anchor can be.** Its new position is in [old − 64, old − 8] ∪ [old + 8, old + 64]: 2 × 57 = **114** cells, taken as uniform.
- **Centre-first tiling, at *w* = 27:**
  - a window on the old address covers 20 + 20 = 40 of them;
  - one window per side then covers the remaining 37 + 37;
  - so **at most 3** actions, and E = (40 × 1 + 37 × 2 + 37 × 3) / 114 = **225/114 ≈ 1.97**.
- **Side-first tiling.** It lowers the expectation to (55 × 1 + 55 × 2 + 2 × 3 + 2 × 4) / 114 = 179/114 ≈ 1.57, at a worst case of 4.
- **Either way, re-finding costs about 2 actions.**

### A.4 What a disruptive hit costs its victim

These are PA §8's tested results, with the attacker hitting at its first offer:

| Parent | Hit in a tick the attacker moves first | Hit in the victim's own first-mover tick |
|---|---|---|
| **Whole-tick** | No callback: **8 offers lost** | Offers 0 and 1 only: **6 lost** |
| **λ = 1** | **1 lost** | **1 lost** |

An evasion costs one MOVE, which is one offer.

---

## Appendix B. Sources

**Governing:** [`V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md`](V6_E8_MECHANIC_FAMILY_DESIGN_REVIEW.md) (§N), and [`V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md).

**Records** (`docs/research/v6/` unless stated):
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) §C.4, §E, §F, §G
- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) §B.2, §B.3, §C, §D.1, §F, §G.2
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) §2, §3, §5, §6, §8, §9, §12
- [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) §2
- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) §D, §F
- [`V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md) §F.8
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md) §3, §4, §14.1
- [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md) §5, §7, §8, §11
- [`docs/REPLAY_SCHEMA.md`](../../REPLAY_SCHEMA.md) ("Python Observation capture: explicitly out of scope")
- [`AGENTS.md`](../../../AGENTS.md) ("Compatibility requirements")

**Source at `dffe531`:**
- `engine/src/battle_engine/agent_api.py:14–36, 160–175, 195–244, 405–425`
- `engine/src/battle_engine/agent_trace.py:14–36, 140–215`
- `engine/src/battle_engine/agent_worker.py:540–552`
- `engine/src/battle_engine/process_runtime.py:600, 757–763, 800–860, 999–1044, 1164–1212, 1274–1308`
- `engine/src/battle_engine/ruleset_policy.py:162, 177, 305–361`
- `engine/src/battle_engine/replay.py:92–111, 359`
- `tools/research/v6/e6/fixtures/agents/e6_q01/agent.py` (`_search`, `_verification_read`, `_adapt`, `_choose`)

---

## Erratum, 2026-09-30: suppression and later callbacks (pointer)

§F.2's delivery row and §J's P-9 list suppression among the cases with no next callback. **That overstates it.** Under whole-tick disruption, a suppressed process may miss the rest of its tick and still receive a later callback. **The pre-registration at `28925fd` governs the delivery semantics** (its §10 and D8-13). This review is otherwise left as written.
