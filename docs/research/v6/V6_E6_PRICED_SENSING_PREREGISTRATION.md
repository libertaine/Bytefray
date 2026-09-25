# Bytefray V6 E6 — Priced Sensing: Pre-Registration

**Status: REGISTERED TEXT, approved by the research lead on 2026-09-25.** Committed as the E6 registration boundary together with the implementation plan. No Ruleset, code, agent, seed list, match or probe exists. At implementation phase I-6 this text is transcribed into `tools/research/v6/e6/preregistration.json`, and a test asserts the two agree. That JSON is then digest-pinned and frozen with the analysis instrument before any matrix cell runs. This markdown is the authoritative wording.
**Branch:** `v6-research` at `9d43cac`, the priced-sensing design boundary.
**Date:** 2026-09-25
**Governing records:**
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**), including the research lead's decisions in its §A.2 and §M;
- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) (**SR**);
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) (§G.8 evidence rules).

The companion plan is [`V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md`](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md).

---

## 0. Registration Decisions

The research lead decided each of these on 2026-09-25. Markers **[O-n]** in the text refer to this table.

| # | Decision | Decided | Rationale |
|---|---|---|---|
| **O-1** | Experiment identity | **E6**, continuing the V6 numbering; tooling under `tools/research/v6/e6/` | Naming only |
| **O-2** | A ninth member, LURK (search `none`, posture `attack`) | **Added. Nine members.** | Without it the family has no clean "less information" pair (§4.6). PACED differs from RUSH in *when* it acquires information, which also changes who sees first (DR §H.2, T4), so a PACED win cannot be read purely as "less information won". LURK differs from RUSH only in never searching. |
| **O-3** | Tolerance ε for best responses | **1/16** | A tie band, so that single-seed noise cannot decide the best-response map. 1/16 equals two of 32 seeds swinging fully. |
| **O-4** | Bootstrap | **1000** resamples, stability **≥ 9/10**, `random.Random(42)` | Keeps a claim from resting on a knife edge. The same values were used for E2's residual bootstrap. |
| **O-5** | The tick bound for a forced-line capture | **≤ 3** | DR T1 predicts capture at tick 2 or 3 after sub-tick discovery. Fixed from that trace, never from outcomes. |
| **O-6** | ADAPT's no-contact switch tick | **16** | More than twice the worst READ-search time: 49 READs is about 7 ticks (DR §G.1). |
| **O-7** | Seeds per cell | **32**, as in E2–E5 | Keeps the evidence scale comparable |
| **O-8** | Instrument for stalling | **E4 cell metrics** (FMA and FPS), descriptive only | DR §J named E2's phase-lock and recovery instruments. Those count zero-core onsets and recoveries, which exist only when K ≥ 2, and both E6 parents are K = 1. This corrects the DR. |

The implementation plan's decisions P-1 to P-6 were decided at the same time (plan §11). Everything else follows decisions already made in DR §A.2 and §M.

---

## 1. Research Question

> **Does limiting passive enemy-anchor visibility to min(declared reach, 32) cells make the best allocation of actions depend on the opponent, or does it act only as a discovery tax?** Search is priced through movement, and reading is the alternative channel.

It is a question, not a promised outcome. Every registered reading in §7 is reachable, including "no registered interpretation row applies" and the rejection outcomes in §8.

---

## 2. Treatment and Conditions

**The treatment field.** `RulesetPolicy.detection_radius`: from `None` to **32**.
- Under 32, a friendly process whose declared reach is *r* sees an enemy anchor if and only if their circular distance is **≤ min(*r*, 32)**. The comparison is inclusive.
- `None` keeps the historical rule: visibility within the declared reach.
- Nothing else changes: when visibility is computed, which processes can sense, entrant-wide sharing, the output format, READ, WRITE, MOVE, capture, disruption, scheduling and scoring (DR §C.1).

**Validation, in two layers** (DR §C.3):
- the policy accepts `None` or a positive integer;
- each match requires *d* < `arena_size / 2`;
- this experiment additionally requires A = 512 and *d* = 32 exactly.

| Condition | Ruleset (IDs provisional) | Parent | Only difference |
|---|---|---|---|
| **C-E6** | `bytefray-rules-6-research-scale` | — | — (the primary control) |
| **T-E6** | `bytefray-rules-6-research-sensing-r32` | `bytefray-rules-6-research-scale` | `detection_radius = 32` |
| **C-E6L** | `bytefray-rules-6-research-disruption-slot1` | — | — (the companion control, λ = 1) |
| **T-E6L** | `bytefray-rules-6-research-disruption-slot1-sensing-r32` | `bytefray-rules-6-research-disruption-slot1` | `detection_radius = 32` |

Fixed across all four conditions: arena 512, tick limit 1000, Q = 8, chunk 2, rotation, K = 1, seeded placement, `core_base` spawn, and forward pass order.

**Arms.** The primary arm is C-E6 → T-E6. The companion arm is C-E6L → T-E6L. It asks whether the primary readings depend on whole-tick denial (DR §H.4). It is **never** a verdict (§6.8).

---

## 3. Population

### 3.1 Members

These are the matched family of DR §I, with the parameter semantics of the implementation plan §5.

| Member | `search` | `posture` | `evade` | `processes` | Role |
|---|---|---|---|---|---|
| **RUSH** | fast | attack | off | 1 | Baseline for the tax |
| **PACED** | paced | attack | off | 1 | Search pace |
| **SPLIT** | fast | attack | off | 2 (sensor 1/4, striker 3/4) | Sensor–striker split |
| **STEALTH** | read | attack | off | 1 | Search mode |
| **LURK** [O-2] | none | attack | off | 1 | Pure lower-information attacker |
| **GUARD** | none | guard | off | 1 | Stationary defense |
| **EVADER** | none | guard | on | 1 | Evasion |
| **GREED** | none | paint | off | 1 | Territory |
| **ADAPT** | adaptive | adaptive | adaptive | 1 | Adaptation (secondary evidence) |

**The fixed set Π_F** is every member except ADAPT. It is the set of candidate best responses (§4.4).

**The opponent set Π** is every member, ADAPT included.

**Why ADAPT is left out of Π_F.** If an adaptive policy were the best response to every opponent, that would show the best *fixed* allocation depends on the opponent, which is evidence *for* a choice. Counting it as a "constant best response" would read that result backwards.

### 3.2 Packages and identities

- Each member has a primary package and a twin package, the twin used only in mirrors.
- **What agents see of identity.** In matrix cells the harness runs every match through `EvaluationService`, and each entrant's runtime `agent_id` is its **seat label**, `"A"` or `"B"` (`evaluation_contracts.seat_label`; `evaluation_cell_execution.py:291`). So a READ's owner reveals only the opponent's *seat*, never its package, and `context.agent_id` tells each agent its own seat. Each entrant's random stream, `derive_agent_seed(match_seed, slot, seat label, 2)`, is keyed to seat and slot. That is why twin relabeling is byte-identical (E3-R addendum), and why members in the same seat and seed draw identical streams.
- **Package IDs are still opaque** (for example `e6_q07`), as the research lead decided (DR §M, decision 8). They matter only in artifacts. The mapping is fixed when the family is implemented, and recorded in the freeze record before any seed exists. No agent source contains any package ID (§5.1, D-5).
- All packages share one policy source, byte-identical, with parameters supplied through `MatchContextV2.parameters` from each package's manifest.

### 3.3 Fields and counts

- **F1:** every ordered pair of distinct members (Seat A, Seat B) × 32 seeds [O-7].
- **F2:** every twin mirror, in both orientations, × 32 seeds.
- **The same ordered seed list** is used for every cell and every condition, so cells pair exactly across conditions.

| Members | F1 cells per condition | F2 cells per condition | Per condition | All four conditions |
|---|---|---|---|---|
| 9 | 72 × 32 = 2,304 | 9 × 2 × 32 = 576 | 2,880 | **11,520** |

---

## 4. Operationalizations

All arithmetic is exact (`Fraction`), and every comparison is closed exactly as written.

### 4.1 Match value (O-VALUE)

For entrant *e* in one match: **v = 1** for a win, **1/2** for a tie (a tick-limit tie or mutual elimination), and **0** for a loss. The value is read from the harness's `cell_seat_result`.

### 4.2 Payoff (O-PAYOFF)

For members *i* ≠ *j* and seed *s*:

- **p_s(i, j)** is the mean of *i*'s value over the two F1 orientations at seed *s*: *i* in Seat A against *j*, and *j* in Seat A against *i*.
- **u(i, j)** is the mean of p_s(i, j) over the 32 seeds.
- **u(i, i) = 1/2** by definition. A twin mirror's orientations are pure relabelings, which gate D-7 verifies, so *i*'s mean value against its twin is exactly 1/2.

Every match contributes one bounded value, and every seed has equal weight. No ticks are pooled across matches, so the per-seed-then-median rule, which exists to stop long matches outweighing short ones in tick metrics, does not apply to match values.

### 4.3 Tolerance (O-EPS)

**ε = 1/16** [O-3].

### 4.4 Best responses and universality (O-BR)

- **BR_ε(j)** = { *i* ∈ Π_F : u(*i*, *j*) ≥ max over *k* ∈ Π_F of u(*k*, *j*) − ε }, for each opponent *j* ∈ Π.
- A fixed member *i* is **universal** if and only if *i* ∈ BR_ε(*j*) for every *j* ∈ Π.
- **P_none** is the predicate: "no member of Π_F is universal".

### 4.5 Bootstrap stability (O-BOOT)

- There are **1000** resamples of the ordered seed list: 32 draws with replacement, from `random.Random(42)` [O-4]. The resampled seeds apply jointly to every cell, which preserves the pairing.
- Each resample recomputes u, the BR_ε sets and every predicate.
- **stab(P)** is the fraction of resamples in which predicate P holds.

### 4.6 Lower-information contrasts (O-CONTRAST)

- **L** = { (LURK, RUSH), (PACED, RUSH) } [O-2].
- In each pair, the first member spends less of its per-tick budget on search: LURK spends none, and PACED at most 4 of 8 actions, against RUSH's 8. Each pair differs from RUSH in `search` alone.
- **Δ_j(lo, hi) = u(lo, j) − u(hi, j)**, for *j* ∈ Π.
- **P_win:** "some (lo, hi) ∈ L and some *j* ∈ Π have Δ_j ≥ ε".
- **P_never:** "every (lo, hi) ∈ L and every *j* ∈ Π have Δ_j ≤ 0".
- The two predicates are mutually exclusive.

STEALTH against RUSH is a *mode* contrast, not an allocation contrast. It is reported descriptively and is not part of L.

### 4.7 Outcome class (O-CLASS)

The E3 definition, reused unchanged (`analyze_e3.outcome_class`): A_WIN, B_WIN, TICK_LIMIT_TIE, MUTUAL_ELIMINATION or OTHER.

A match is **decided by capture** if its termination involves a core capture (`analyze_e4.is_capture`). Its **decision tick** is its final tick.

### 4.8 Forced-line capture (O-EARLY)

A match is a **forced-line capture of *d*** if it ends by the core capture of *d* at a tick **≤ 3** [O-5].

### 4.9 Seat metrics (O-SEAT)

E4's `pairing_seat_metrics` and `mirror_seat_metrics`, unchanged: SDI, GSB, SDom and SCD. Mirrors are analyzed seed by seed. Seat-dominant means SDom ≥ 9/10.

### 4.10 Hostile core contact (O-CONTACT)

A match has hostile core contact if some entrant writes a cell of the opponent's core at any point. This is derived from replay memory diffs, with cores taken from the tick-0 seeding.

### 4.11 Detection telemetry (O-DETECT; descriptive only)

Derived from traces (§6.6):
- each entrant's first-detection tick;
- which entrant first held the other's anchor in its visible set;
- MOVEs made before an entrant's first detection;
- probe READs;
- off-core MOVEs.

These are never inputs to a hypothesis.

### 4.12 Evidence (O-EVIDENCE)

- **n_distinct** is the number of distinct harness `trajectory_key` values among a unit's matches.
- It is reported beside every payoff entry, contrast and share.
- **Every frozen unit is included, whatever its n_distinct.** No unit is dropped or selected on realized variability.
- A **rate** is a share of matches with a fixed denominator: H0's A and B, H3's FL, and the pathology shares. Its denominator is fixed by the matrix, not by realized variability.

---

## 5. Hypotheses

### 5.1 E6-D: the manipulation and integrity gate (a hard stop; it reads no gameplay outcome)

Each clause is labelled as a **Ruleset invariant**, a **family characterization** (true of this frozen family, not guaranteed by the Ruleset), or a **protocol** check.

| Clause | Kind | Condition | Evaluated on |
|---|---|---|---|
| **D-1** Visibility | Ruleset invariant | At every callback of every treatment cell, the traced `visible_enemy_anchor_addresses` equals the set of live enemy anchors within min(reach, 32) of some unsuppressed friendly process. That set is re-derived independently from the trace's ordered action stream: tick-0 anchors, the normalized results of every MOVE, and disruption hits under the condition's λ. | T-E6, T-E6L; all cells |
| **D-2** Initial invisibility | Ruleset invariant | In the initialized state, before the first scheduled action, every opposing default-spawn anchor is more than 32 from every family sensor. This deliberately does not say "each entrant's first callback sees nothing" (DR §J). | T-E6, T-E6L; all cells |
| **D-3** Parent identity | Ruleset invariant | After the engine change, the parent byte-identity goldens reproduce byte for byte with `detection_radius = None`. Those goldens are named scenarios with existing fixtures, frozen before the change. The control conditions run the unmodified parent Rulesets. | The parent freeze; C-E6, C-E6L provenance |
| **D-4** No early blind strike | Family characterization | In ticks 1–2, no family member writes a cell of the opponent's core before its entrant has had an **information event**: the opponent's anchor in its visible set, or a READ of a cell of the opponent's core returning the opponent as owner. This detects any zero-action bypass, such as seed inference. It is limited to ticks 1–2 because no family painting front can reach a core at least 64 cells away within 16 actions. | T-E6, T-E6L; all cells |
| **D-5** Discipline | Family characterization, checked statically | Every package passes the static gate: imports only `battle_engine.agent_api` and whitelisted standard-library modules; never reads the `seed` attribute of its context; contains no family package-ID string literal; calls none of `open`, `exec`, `eval`, `compile` or `__import__` (implementation plan §5.5). | All packages, at freeze |
| **D-6** Seed commitment | Protocol | At reveal, the SHA-256 of the canonical seed list equals the committed value; the execution matrix identity recomputes from the structural digest and that commitment; and every matrix cell's seed is on the list (§9). | After the frozen gameplay analysis, **before** interpretation |
| **D-7** Mirror relabeling | Ruleset invariant | Every twin mirror's two orientations have byte-identical replay tick records. | All F2 cells |

**E6-D = PASS** if and only if every clause passes. **Its status is final only after D-6**, so no registered interpretation or disposition (§7, §8) is issued before the seed reveal (§9, step 7).

### 5.2 CQ-1: control qualification (before any treatment cell exists)

**Search is inert under each control.** Members that differ only in `search` (RUSH, PACED, STEALTH and LURK [O-2]) produce identical action streams in every matched control cell: the same opponent, seed and orientation, under both C-E6 and C-E6L.

This follows by construction. Under each control, every member declares reach 256 = A/2, so an enemy anchor is visible from each entrant's first callback. The `search` routine runs only when no opponent anchor is known (implementation plan §5.2).

**If CQ-1 fails, halt before any treatment.** Fix the family and re-freeze. Those steps remain blind to the treatment.

### 5.3 The hypotheses

Each is SUPPORTED, REFUTED or NEITHER. The conditions are exhaustive and mutually exclusive.

| ID | Statement | SUPPORTED if and only if | REFUTED if and only if |
|---|---|---|---|
| **E6-H1T** | The best response under T-E6 is not constant | P_none holds at the point estimate, and stab(P_none) ≥ 9/10 | P_none fails at the point estimate, and stab(not P_none) ≥ 9/10 |
| **E6-H1C** | The best response under C-E6 is not constant | The same, computed on C-E6 | The same, computed on C-E6 |
| **E6-H2** | Less information can win under T-E6 | P_win holds at the point estimate, and stab(P_win) ≥ 9/10 | P_never holds at the point estimate, and stab(P_never) ≥ 9/10 |
| **E6-H0** | Delay only: priced sensing is a discovery tax | A ≥ 9/10 and B ≥ 9/10 | A ≤ 2/3 |
| **E6-H3** | A delayed forced line defeats every defender | Some attacker *a* has min over defenders *d* of FL(*a*, *d*) ≥ 9/10 | Every attacker *a* has min over *d* of FL(*a*, *d*) ≤ 1/10 |

Anything else is NEITHER.

**Definitions for E6-H0**, over the paired F1 cells of the primary arm (each cell is one match, paired with its control cell by pair, seed and orientation):
- **A** is the share of paired F1 cells whose outcome class under T-E6 equals their class under C-E6.
- **B** is taken **over the cells counted by A**. It is the share whose final tick under T-E6 is greater than or equal to the final tick under C-E6.

Whenever A ≥ 9/10, B's denominator is at least nine tenths of all F1 cells, so no empty-denominator convention is needed. If A = 0, B is undefined, and E6-H0 is REFUTED through A ≤ 2/3.

A capture that becomes a same-seat score win at the tick limit still counts as "preserved and delayed". The resulting stalling is identified separately, by PF-1. E6-H0 is about competitive structure, not about termination.

**Definitions for E6-H3:**
- the attackers are the posture-`attack` members {RUSH, PACED, SPLIT, STEALTH, LURK [O-2]};
- the defenders are {GUARD, EVADER};
- **FL(*a*, *d*)** is the share of the 64 F1 matches of *a* against *d* (32 seeds × 2 orientations) that are forced-line captures of *d* (§4.8).

**Threshold rationale.**
- **9/10** is E2-H0's keep threshold, and the stability bar.
- **2/3** and **1/10** are the E4 and E5 census bounds.
- **ε** and the tick bound 3 are covered at [O-3] and [O-5].

None was derived from any E6 data, and none exists yet.

**Primary evidence of a choice is E6-H1T together with E6-H2.** ADAPT is secondary evidence. It is reported (§6.7) but never a condition of any row (DR §M, decision 9).

---

## 6. Pathology Flags and Registered Reporting

### 6.1 Pathology flags

These are computed on F1 of the primary arm and **recorded whatever else holds**. The 1/10 threshold follows E5's PF convention.

| Flag | Raised if and only if |
|---|---|
| **PF-1 Stalling** | The tick-limit share under T-E6, minus the share under C-E6, is ≥ 1/10. |
| **PF-2 Loss of contact** | The share of matches with no hostile core contact (§4.10) under T-E6, minus the share under C-E6, is ≥ 1/10. |
| **PF-3 New immunity** | Some member of Π_F is never core-captured in any of its F1 matches under T-E6, although it is captured in at least one F1 match under C-E6. |
| **PF-4 Seat artifact** | Some F1 pairing or F2 mirror has SDom < 9/10 and \|GSB\| ≤ 1/10 under C-E6, but SDom ≥ 9/10 or \|GSB\| > 1/10 under T-E6 (E5 PF-5, unchanged). |

### 6.2 Alternation (descriptive, [O-8])

E4's `cell_metrics` (FMA and FPS) are reported for every F1 cell of all four conditions. They describe the alternation that DR T2 predicts. They feed no hypothesis.

### 6.3 Seat and parity (descriptive)

- which seat first detects the other;
- for fast searchers, the parity of their arrival;
- for evaders, the rate at which they are caught still on their core, by seat (DR T2, T4).

### 6.4 The payoff tables

These are reported in full for both arms: u(*i*, *j*) with its n_distinct, every BR_ε set, the universal members, and every Δ_j(lo, hi), each with its stability.

### 6.5 Identities

The mapping from package ID to member is recorded in the freeze record. At runtime, entrants are seat labels (§3.2). D-5 checks that no agent source contains any package ID.

### 6.6 Traces

Traces, or equivalent callback-level additive telemetry, are required for **every control and treatment cell** (DR C-4). The replay format does not change.

### 6.7 ADAPT (secondary)

For each fixed member, report u(ADAPT, *j*) − u(*j*, ADAPT) against the mixed field, and whether ADAPT belongs to BR_ε(*j*) when it is added to the candidate set. **This never enters an interpretation row or a kill criterion.**

### 6.8 The companion arm

Every quantity in §5 and §6 is also computed on C-E6L → T-E6L with identical code. The companion reading is registered as either **"agrees with the primary"**, when E6-H1T, E6-H2, E6-H3 and every kill criterion (§8) have the same status in both arms, or as the list of what differs. **It never replaces a primary verdict**, and it never triggers a kill.

---

## 7. Registered Interpretation (primary arm)

**The rule.** A row applies if and only if E6-D has the row's status and the pair (E6-H1T, E6-H1C) is among the row's listed combinations. The rows cover every combination exactly once, and none is impossible. A negated hypothesis is never written: NEITHER and REFUTED are listed separately. A test must show that every (E6-D, E6-H1T, E6-H1C) triple maps to exactly one row. A triple that maps to none, or to two, fails closed as an invariant violation.

| Row | E6-D | (E6-H1T, E6-H1C) | Registered reading |
|---|---|---|---|
| **STOP** | FAIL | all nine | **STOP.** No gameplay reading: the treatment, the family or the protocol is defective. |
| **R-CREATES** | PASS | (SUPPORTED, REFUTED) | **Under the parent, one fixed policy is a best response to every opponent. Under priced sensing, none is: priced sensing creates an opponent-dependent choice of how to allocate actions.** It is qualified by E6-H2: if **SUPPORTED**, "and spending less on information beats spending more against at least one opponent: an information/action tradeoff, not a discovery tax"; if **NEITHER** or **REFUTED**, "but the registered lower-information contrast does not show less information winning, so the choice is not shown to be an information-cost tradeoff". |
| **R-PREEXISTING** | PASS | (SUPPORTED, SUPPORTED) | **An opponent-dependent choice exists under both the parent and priced sensing. Priced sensing is not necessary for it.** Recorded as relevant to Branch A. The E6-H2 status is recorded alongside. |
| **R-TREATMENT-ONLY** | PASS | (SUPPORTED, NEITHER) | **No fixed policy is a best response to every opponent under priced sensing. Under the parent the evidence is indeterminate, so creation is not established.** |
| **R-REMOVES** | PASS | (REFUTED, SUPPORTED) | **Priced sensing removes an opponent-dependent choice present under the parent.** |
| **R-NO-CHOICE** | PASS | (REFUTED, REFUTED) | **A fixed policy is a best response to every opponent under both.** It is qualified by E6-H0: if **SUPPORTED**, "priced sensing acts as a discovery tax: outcomes are preserved and delayed"; if **REFUTED**, "a dominant policy under both, with outcomes restructured"; if **NEITHER**, "a dominant policy under both; delay-only is neither established nor excluded". |
| **R-TREATMENT-DOMINANT** | PASS | (REFUTED, NEITHER) | **A fixed policy is a best response to every opponent under priced sensing. Under the parent the evidence is indeterminate.** |
| **NONE** | PASS | (NEITHER, SUPPORTED), (NEITHER, REFUTED), (NEITHER, NEITHER) | **"No registered interpretation row applies" is itself the registered outcome.** The tables in §6.4 are reported. |

**Recorded alongside every row, but never inputs to it:** E6-H3, PF-1 to PF-4, the ADAPT reading (§6.7) and the companion reading (§6.8).

**Each row claims only what E6 manipulated.** Detection radius is the only difference between the arms.

---

## 8. Kill Evaluation and Disposition (registered)

This carries the scope review's kill criteria (SR §G.1), as refined by DR §K.2, into exact form. It is evaluated on the primary arm.

| ID | Fires if and only if | Label |
|---|---|---|
| **KC-1** Constant best response | E6-H1T is REFUTED | Named after the universal set at the point estimate: a **search race** if every universal member has `search` ≠ none; **greed dominance** if GREED is universal; otherwise **other dominance**, naming the members |
| **KC-2** Greed dominance | GREED is universal at the point estimate, and stab(GREED universal) ≥ 9/10 | A special case, reported even when other members are also universal |
| **KC-3** Stalling or loss of contact | PF-1 or PF-2 is raised | Includes alternation stalemates of DR T2, described through §6.2 |
| **KC-4** Delayed forced line | E6-H3 is SUPPORTED | A forced line defeats every defender, the evasive one included |
| **KC-5** Seat artifact | PF-4 is raised | Including the parity effects of §6.3, where they produce it |

**Disposition**, exhaustive:
- **VOID** if E6-D fails.
- Otherwise **REJECT as a gameplay candidate** if any KC fires.
- Otherwise **CANDIDATE**, for a further design phase, if the row is R-CREATES and E6-H2 is SUPPORTED.
- Otherwise **NOT ESTABLISHED**.

PF-3 is recorded, not a kill. Priced sensing is expected to remove some captures by design; that is the manipulation working.

A REJECT or a NOT ESTABLISHED is a successful result of the method (SR §G.1).

---

## 9. Seed-Set Blindness Protocol (DR §E.2, C-1)

1. **Order of events.**
   - The complete family (all packages, primary and twin) is implemented, tested, fingerprinted and committed **first**.
   - The **structural matrix identity** is frozen: conditions, population, fields, counts and parameters, with no seed values.
   - Seeds are generated only after that.
   - **No seed is generated while this pre-registration is written.**
2. **Generation.** 32 [O-7] unique integers, each drawn uniformly with `secrets.randbelow(2**53)`. They stay below 2⁵³, so every JSON consumer represents them exactly, and each carries 53 bits of entropy. They are made by a committed tool (implementation plan §8).
3. **Canonical encoding.** The seeds, in generation order (which is the matrix order), written as decimal ASCII, one per line, with LF line endings and a trailing LF, in UTF-8. **The seed commitment is the SHA-256 hex of those bytes.**
4. **Two matrix identities.**
   - **Structural matrix identity** (frozen before the seeds exist): `v6-e6-matrix-v1-<first 12 hex of the structural digest>`, where the structural digest is the SHA-256 of the canonical matrix definition.
   - **Execution matrix identity** (fixed once the seeds exist): `v6-e6-exec-v1-<first 12 hex of X>`, where X is the SHA-256 of the UTF-8 bytes of *structural digest hex*, LF, *seed commitment hex*, LF.

   Together they freeze the experiment's structure before any seed exists, and bind the matrix actually executed to the hidden seed set.
5. **Commitment.** The seed commitment and the execution matrix identity, **and nothing else about the seeds**, are committed to git in the freeze record **before the first matrix cell runs**, controls included. Every control and treatment provenance record carries both matrix identities and the seed commitment. The seed list itself is kept in a git-ignored file outside every agent package directory.
6. **Blindness.** Matched agents cannot read the list. D-5 forbids filesystem and introspection access. Run artifacts that record seeds (results, replays, traces) stay git-ignored until reveal.
7. **Order of analysis and reveal.** Treatment execution, then the treatment gates, then the frozen gameplay analysis, **then the seed reveal and D-6**, then E6-D's final status, then the registered interpretation and disposition, then the results record.
   - The gameplay analysis may run while the seeds are still hidden, because execution is already complete.
   - The registered interpretation and the disposition wait for D-6.
   - At reveal, the list is committed, and D-6 verifies it against the commitment, the execution matrix identity and every cell's recorded seed.
   - **If D-6 fails, the disposition is VOID and no gameplay interpretation is issued.**

The protocol is research methodology. Closing seed inference at the product level remains a promotion prerequisite (DR §E.2).

---

## 10. Evidence Rules

1. Every frozen unit is counted and none is dropped. n_distinct is reported beside every figure. A rate needs n_distinct ≥ 8, and a value below that is a characterization (synthesis §G.8).
2. Payoffs weight every seed equally (§4.2). Tick metrics (§6.2) are computed per match, and the unit value is the median over seeds.
3. Control-against-control: before any treatment exists, the analyzer is run with C-E6 in the treatment slot. It must read **E6-H0 SUPPORTED (A = B = 1)**, **E6-H2 REFUTED** (Δ ≡ 0 by CQ-1), no PF raised, and E6-H1T equal to E6-H1C.
4. The companion never replaces a primary verdict (§6.8).
5. ADAPT is never a condition of a row or a kill (§6.7).
6. No threshold, set, operationalization, row or rule changes after any matrix cell exists. An analyzer defect found after exposure means a stop and a new analysis-freeze identity. Both matrix identities are kept.

---

## 11. Hard Stops

**Before treatment:**
- A parent golden fails, or a control fails to reproduce its parent.
- A fixture fingerprint drifts, or a request override is not `None`.
- D-5 (discipline) fails.
- CQ-1 fails.
- The control-against-control reading of §10.3 fails.
- The seed commitment or the execution matrix identity is missing from the freeze record before the first matrix cell, or a cell's provenance does not carry both matrix identities and the commitment.
- The source manifest changes, or the tree is dirty, during execution.

**During and after treatment:**
- E6-D fails on D-1, D-2, D-4 or D-7.
- An analyzer or telemetry disagreement: for example, the trace-derived visibility disagrees with the independent re-derivation beyond D-1's own check, or an analyzer fails.
- A recurring `evaluation.json` `PermissionError`: quarantine, relaunch and byte-check once, then stop.
- At reveal, which comes before interpretation (§9, step 7), D-6 fails. **The disposition is then VOID and no gameplay interpretation is issued**, because blindness cannot be verified.

---

## 12. Differences from the Design Review

Each difference is recorded and none changes a decision of the research lead.

1. **The stalling instrument** is E4's cell metrics, not E2's phase-lock instrument, which does not apply at K = 1 [O-8].
2. **u(*i*, *i*) = 1/2 by construction.** Mirrors add nothing to the payoff table. They serve the seat metrics and D-7.
3. **ADAPT is excluded from the candidate set** (§3.1), so that an adaptive winner cannot read as "no choice".
4. **LURK** is added as a ninth member (O-2).
5. **DR gate (iv)**, "a parent reproduced with detection_radius None", is D-3.
6. **DR's "no zero-action bypass" check** becomes D-4, an in-corpus integrity check on ticks 1–2, alongside the static D-5.
7. **A correction to DR §E.1 row 4 and finding 4.** In matrix cells, a READ's owner is the opponent's **seat label**, not its package ID, because the harness runs entrants as `"A"` and `"B"` (§3.2). The owner channel therefore does not reveal the opponent's identity in the experiment. Opaque package IDs are kept anyway, as the research lead decided. The DR is not edited; this record carries the correction.
8. **EVADER's evasion magnitude** is drawn from [8, 64] (plan decision P-2). Eight is the smallest symmetric displacement that guarantees an anchor starting at core cell 0 leaves the 8-cell core in either direction; 64 is the maximum MOVE.

---

## 13. What This Pre-Registration Does Not Claim

- **No result.** No E6 data of any kind exists.
- **No prediction.** The traces in DR §H.2 are priors to be falsified, not expected outcomes.
- **No product claim.** Every registered disposition is a research disposition.
- **Scope.** Claims are scoped to the matched family and to agents that do not reconstruct placement, at A = 512, *d* = 32, 1000 ticks and 32 blinded seeds.
