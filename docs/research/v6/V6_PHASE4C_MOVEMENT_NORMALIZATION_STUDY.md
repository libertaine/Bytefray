# Bytefray V6 Phase 4C — Movement Normalization Study

**Status:** Complete  
**Branch:** `v6-research`  
**Baseline:** `dea2390` (Phase 4B completion)  
**Ruleset introduced:** `bytefray-rules-6-research-scale-move`  
**Predecessors:** [`V6_PHASE4B_ARENA_SCALING_STUDY.md`](V6_PHASE4B_ARENA_SCALING_STUDY.md), [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md)  

---

## A. Executive Summary & Core Research Question

Phase 4B established that raw arena scaling alone does not destabilize Bytefray's aggregate competitive hierarchy, but it delays contact and causes territorial win conditions to collapse. In Phase 4B Section N, **movement stride normalization** was identified as the highest-priority single-variable candidate to test whether scaling traversal capability proportionally with arena size restores interaction frequency and increases opponent dependence.

Phase 4C isolates this single gameplay variable:

> **If traversal capability is normalized to arena scale while everything else remains raw, does Bytefray become more interactive and more opponent-dependent?**

### The Definitive Finding

Phase 4C executed the full experimental protocol: 2,240 sweep matches across five arena sizes ($A \in \{512, 1024, 4096, 16384, 65536\}$), preceded by a live 448-match equivalence gate at $A=512$, all evaluated over the frozen `V6-Bench-8` benchmark field with zero source drift.

The experimental outcome reveals an essential architectural and scientific insight:

> **Ruleset-level movement stride normalization provides environmental headroom, but is completely inert for agents authored with hardcoded stride assumptions.**
>
> On the frozen `V6-Bench-8` benchmark field, every single agent authored under the 512-cell paradigm internally clamps its displacement requests to $\le 64$ (or moves by reach $\le 1$, or remains stationary). Consequently, no agent in the frozen field ever requested an operand exceeding 64 cells. Across all 2,240 matches and all five arena sizes, **the observed gameplay deltas between Phase 4B (raw-scaling control) and Phase 4C (movement-normalized candidate) were exactly 0.0**.

Unit testing confirmed that an agent written to exploit the higher bound does indeed move up to 128 cells at $A=1024$ under Phase 4C while being clamped to 64 under Phase 4B (`engine/tests/test_ruleset_v6_research_scale_move.py::test_live_movement_clamping_differs_at_a1024`). However, within a frozen benchmark field where agent logic is fixed, changing the environmental upper bound without changing agent behavior or multiplicatively scaling executed displacement produces zero operational difference.

This negative result is scientifically decisive: it establishes that **arena scalability cannot be solved by passive environmental headroom alone**; it requires either environment-level displacement multiplication, explicit agent awareness of arena scale via API contracts, or scale-adaptive agent authoring.

---

## B. Experimental Design & The Single Variable

### B.1 The Single Variable: Proportional Movement Stride

Phase 4C changes exactly one gameplay variable from Phase 4B:

$$\text{max\_move\_delta}(A) = \max\left(64, \left\lfloor \frac{A}{8} \right\rfloor\right)$$

Across the five tested arena sizes, the environmental displacement bound evaluates to:

| Arena Size ($A$) | Phase 4B Raw Stride Bound | Phase 4C Normalized Stride Bound | Traversal Time across Arena ($A / \text{stride}$) |
|---:|---:|---:|---:|
| 512 | 64 | 64 | 8.0 ticks |
| 1024 | 64 | 128 | 8.0 ticks |
| 4096 | 64 | 512 | 8.0 ticks |
| 16384 | 64 | 2048 | 8.0 ticks |
| 65536 | 64 | 8192 | 8.0 ticks |

At $A=512$, the anchor invariant is preserved: $\text{max\_move\_delta}(512) = \max(64, 64) = 64$. At larger arenas, the bound scales linearly, preserving a constant traversal bound of 8 ticks across the entire arena circumference (assuming 1 MOVE per tick).

### B.2 Controlled Constants Held Frozen

In accordance with Phase 4 methodology and strict scientific isolation:
1. **Territory Scoring:** Unchanged; scored as raw proportion of arena cells.
2. **Reach Semantics:** Unchanged; uncapped, zero-cost reach declarations.
3. **Placement Separation:** Unchanged; minimum separation held at 64 cells.
4. **Tick Horizon:** Unchanged; fixed at $T = 1000$ ticks.
5. **Instruction Quota:** Unchanged; $Q = 8$ instructions per tick.
6. **Entrant Scheduling:** Unchanged; chunked $K=2$ with rotating start.
7. **No new gameplay mechanics:** No fog of war, terrain, hazards, or economics.

### B.3 Ruleset Policy Ownership

To eliminate hardcoded defaults in runtime controllers, movement stride policy was formalized on `RulesetPolicy`:

```python
RULESET_V6_RESEARCH_SCALE_MOVE = RulesetPolicy(
    ruleset_id="bytefray-rules-6-research-scale-move",
    supported_runtime_kinds=frozenset({"python"}),
    supported_python_api_versions=frozenset({2}),
    scheduler_mode="chunked",
    scheduler_chunk_size=2,
    scheduler_rotate_start=True,
    core_placement="seeded",
    process_selection="round_robin",
    movement_stride="scale_normalized",
)
```

The runtime (`ProcessMatchController`) resolves `max_move_delta` dynamically via `self.ruleset_policy.resolve_max_move_delta(config.arena_size)`.

---

## C. Control Invariants & The A=512 Equivalence Gate

Before executing large-arena sweeps, behavioral equivalence between the Phase 4B control (`bytefray-rules-6-research-scale`) and the Phase 4C candidate (`bytefray-rules-6-research-scale-move`) was verified live at $A=512$.

The entire `V6-Bench-8` field (28 unordered pairs $\times$ 8 seeds $\times$ 2 orientations = 448 matches) was executed under both rulesets at $A=512$ (`tools/research/v6/phase4c_corpus_runner.py equivalence`). Every paired match was compared cell by cell (`tools/research/v6/phase4c_equivalence_check.py`):

```json
{
  "total_cells_compared": 448,
  "result_mismatches": 0,
  "placement_mismatches": 0,
  "mismatch_samples": [],
  "placement_mismatch_samples": []
}
```

```
EQUIVALENCE GATE (A=512): PASS
```

- **Placement Geometry:** 448 / 448 matched identically.
- **Match Results:** Winner, ticks run, scores, territory, kills, deaths, and termination reasons matched identically.
- **Deep Replay Stream:** Full tick-by-tick event streams and memory diffs matched byte-for-byte.

This establishes that at the $A=512$ anchor point, `bytefray-rules-6-research-scale-move` introduces zero gameplay drift.

---

## D. Benchmark Field Integrity (V6-Bench-8) & Zero Source Drift

The benchmark field `V6-Bench-8` was verified before running any matches (`tools/research/v6/phase4c_corpus_runner.py fingerprints`). All 8 agent directories were resolved and their content-addressed SHA-256 fingerprints compared against Phase 4B:

| Agent Name | Archetype | SHA-256 Fingerprint (`agent_revision_id`) | Drift vs 4B |
|---|---|---|:---:|
| `Octave` | Global sniper | `e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730` | 0 |
| `nemesis_alpha2` | Stationary core hunter | `6d5a8492b34a77cbbbe795152370ed20c65f2c55da20dc96a35f5d28c3b44f5c` | 0 |
| `v5_scout_striker` | Mobile pursuit | `290e02004291abd77967bc43e549e07eddad9851915ddd9f5edc2fd5e0de0ac1` | 0 |
| `v5_region_attacker` | Regional suppressor | `8855d950c08f8f95cdca192ed817b853d6350cdbe7ec0bd6d161879e5237ddcb` | 0 |
| `v5_dual_team` | Coordinated 2-process | `71e9e84c17fe7a6f084ca9b83d0394741c9edfb24df8b593441f97a2910030af` | 0 |
| `v4_claimer` | Territorial expander | `342d5a20df20c0154774fbbbd643256e1afbc593b9d735ddb831388cfeebc952` | 0 |
| `v5_core_defender` | Reactive defense | `2a47c0386ff88d58b810eef97a1f093a89050d5ba3a5ae52a31c56eb2de0cc95` | 0 |
| `v4_local_defender` | Passive floor control | `6a64a4ba742f04e389f1301bd4a0210866d54b3464c7c01bc497138c30318453` | 0 |

Result: **0 source drift detected**. All agents ran their exact frozen bytecode from Phase 4B.

---

## E. Smoke Test Verification (A=512, A=65536)

The tier-1 smoke test (`Octave`, `v4_claimer`, `v5_core_defender`; 2 seeds $\times$ 2 orientations = 12 matches per arena) ran at the boundary conditions:

| Arena Size | Matches | Wall Clock | Mean Time / Match | Completed Status |
|---:|---:|---:|---:|:---:|
| 512 | 12 | 2.23 s | 0.186 s | 12 / 12 |
| 65536 | 12 | 2.17 s | 0.181 s | 12 / 12 |

No execution bottlenecks, unhandled exceptions, or memory leaks were detected.

---

## F. Comprehensive Sweep Results Across 5 Arenas

A full sweep was executed across all five arena sizes under `bytefray-rules-6-research-scale-move`:
- 28 pairs $\times$ 8 seeds $\times$ 2 orientations = 448 matches per arena.
- 5 arena sizes = **2,240 matches total**.
- Total wall-clock execution time: ~565 seconds (9.4 minutes).

### F.1 Aggregate Metrics by Arena Size

| Arena ($A$) | Stride Bound | Action Density $S = 8000/A$ | Matches | Timeouts | Timeout % | Mean Ticks | Median Ticks | 3-Cycles | Dominance Edges | Spearman $\rho$ vs 512 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | 64 | 15.625 | 448 | 140 | 31.2% | 344.5 | 11.0 | 2 | 25 | 1.000 |
| 1024 | 128 | 7.8125 | 448 | 161 | 35.9% | 394.8 | 18.0 | 0 | 24 | 0.976 |
| 4096 | 512 | 1.953 | 448 | 184 | 41.1% | 422.1 | 32.0 | 0 | 23 | 0.976 |
| 16384 | 2048 | 0.488 | 448 | 178 | 39.7% | 419.5 | 65.0 | 0 | 24 | 0.952 |
| 65536 | 8192 | 0.122 | 448 | 175 | 39.1% | 459.5 | 234.5 | 0 | 25 | 0.952 |

### F.2 Aggregate Leaderboard by Arena Size

| Rank | $A = 512$ | $A = 1024$ | $A = 4096$ | $A = 16384$ | $A = 65536$ |
|:---:|---|---|---|---|---|
| 1 | Octave (1.00) | Octave (1.00) | Octave (1.00) | Octave (1.00) | Octave (0.97) |
| 2 | v5_scout_striker (0.72) | nemesis_alpha2 (0.68) | nemesis_alpha2 (0.71) | nemesis_alpha2 (0.73) | nemesis_alpha2 (0.75) |
| 3 | nemesis_alpha2 (0.62) | v5_scout_striker (0.65) | v5_scout_striker (0.65) | v5_scout_striker (0.68) | v5_scout_striker (0.68) |
| 4 | v5_region_attacker (0.58) | v5_region_attacker (0.56) | v5_region_attacker (0.52) | v4_claimer (0.54) | v4_claimer (0.57) |
| 5 | v4_claimer (0.44) | v4_claimer (0.46) | v4_claimer (0.50) | v5_region_attacker (0.48) | v5_region_attacker (0.51) |
| 6 | v5_dual_team (0.38) | v5_dual_team (0.38) | v5_dual_team (0.34) | v5_dual_team (0.29) | v5_dual_team (0.26) |
| 7 | v5_core_defender (0.17) | v5_core_defender (0.17) | v5_core_defender (0.18) | v5_core_defender (0.17) | v5_core_defender (0.16) |
| 8 | v4_local_defender (0.09) | v4_local_defender (0.10) | v4_local_defender (0.10) | v4_local_defender (0.10) | v4_local_defender (0.09) |

---

## G. Direct Comparative Delta: Phase 4B (Raw-Scale) vs Phase 4C (Movement-Normalized)

A post-hoc cross-phase analysis directly compared Phase 4B and Phase 4C match by match and condition by condition (`tools/research/v6/phase4c_analyzer.py`):

| Arena Size | Cross-Phase Spearman $\rho$ (4B vs 4C) | Win Rate Deltas (All 8 Agents) | Timeout Rate Delta | Mean Ticks Delta | 3-Cycle Delta | Contact Tick Delta | Stagnation Rate Delta |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 512 | 1.000 | 0.0000 | +0.0% | 0.0 | 0 | 0.0 | 0.0% |
| 1024 | 1.000 | 0.0000 | +0.0% | 0.0 | 0 | 0.0 | 0.0% |
| 4096 | 1.000 | 0.0000 | +0.0% | 0.0 | 0 | 0.0 | 0.0% |
| 16384 | 1.000 | 0.0000 | +0.0% | 0.0 | 0 | 0.0 | 0.0% |
| 65536 | 1.000 | 0.0000 | +0.0% | 0.0 | 0 | 0.0 | 0.0% |

Across all 2,240 matches, **not a single match outcome, score, territory percentage, kill/death count, tick count, or replay event diverged between Phase 4B and Phase 4C**.

---

## H. The Agent-Authoring Constraint: Environmental Headroom vs Hardcoded Assumptions

### H.1 Root Cause Analysis

Why did relaxing the environmental stride bound produce identical results?

Inspection of the source code of the frozen benchmark agents reveals how agent authors implemented movement:

1. **Explicit Hardcoded Clamping (`MAX_MOVE_DELTA = 64`):**
   - In `v5_scout_striker/agent.py`:
     ```python
     MAX_MOVE_DELTA = 64
     # ...
     delta = max(-MAX_MOVE_DELTA, min(MAX_MOVE_DELTA, target - anchor))
     return AgentAction(ActionKindV2.MOVE, operand=delta)
     ```
   - In `Octave/agent.py`:
     Clamps calculated movement deltas to `[-64, 64]`.
   - In `v5_region_attacker/agent.py`, `v5_dual_team/agent.py`, and `v5_core_defender/agent.py`:
     All explicitly clamp move operands to $[-64, 64]$.

2. **Reach-Coupled Movement:**
   - In `v4_claimer/agent.py`: Moves by its declared reach ($1$ cell at a time).

3. **Small Bounded Shuffling:**
   - In `v4_local_defender/agent.py`: Moves by at most $\pm 2$ cells around its core.

4. **Stationary Logic:**
   - In `nemesis_alpha2/agent.py`: Does not emit `ActionKindV2.MOVE` actions (stationary artillery).

### H.2 The Dual-Clamping Paradigm

In Bytefray:

$$\text{effective\_displacement} = \text{clamp}\Big(\text{operand},\ -\text{max\_move\_delta}(A),\ \text{max\_move\_delta}(A)\Big)$$

Under Phase 4B:
$$\text{operand} \in [-64, 64] \implies \text{clamp}(\text{operand}, -64, 64) = \text{operand}$$

Under Phase 4C:
$$\text{operand} \in [-64, 64] \implies \text{clamp}\big(\text{operand}, -\text{bound}(A), \text{bound}(A)\big) = \text{operand} \quad (\text{since } \text{bound}(A) \ge 64)$$

Because $\text{bound}(A) \ge 64$ for all $A \ge 512$, the agent's internal clamping strictly dominates the environmental clamp. The environmental headroom was enlarged, but no entrant possessed the behavioral logic to step into that headroom.

### H.3 Verification of Environmental Capability

To confirm that the runtime implementation is correct and active, test `test_live_movement_clamping_differs_at_a1024` executed a custom agent requesting a stride of $100$ cells at $A=1024$:
- Under `bytefray-rules-6-research-scale`: displacement was clamped to $64$.
- Under `bytefray-rules-6-research-scale-move`: displacement executed at the full requested $100$ cells (under the $128$ bound).

The ruleset works as designed. The zero delta is an empirical characteristic of the benchmark population.

---

## I. Interaction Metrics (First Contact, Hostile Writes, Stagnation)

Because the agents did not expand their stride, their physical paths through the arena were identical to Phase 4B:

| Arena Size | Mean First-Contact Tick | Never In Contact Rate | Mean First Hostile Write Tick | Stagnation Rate ($W=100$) |
|---:|---:|---:|---:|---:|
| 512 | 5.5 | 3.6% | 7.9 | 0.0% |
| 1024 | 11.0 | 3.6% | 15.3 | 0.0% |
| 4096 | 43.8 | 3.6% | 61.2 | 0.0% |
| 16384 | 33.3 | 8.7% | 46.8 | 0.0% |
| 65536 | 96.3 | 10.7% | 135.0 | 2.2% |

All metrics match Phase 4B exactly:
- First-contact tick grows from 5.5 to 96.3 ticks.
- The proportion of matches where opposing processes never enter combined reach rises from 3.6% to 10.7%.
- Formal $W=100$ zero-mutation stagnation appears only at $A=65536$ (2.2% of matches).

---

## J. Competitive Hierarchy & Rank Stability

The hierarchy remains highly stable across arena scales:
- Spearman rank correlation against $A=512$:
  - $A=1024$: $\rho = 0.976$
  - $A=4096$: $\rho = 0.976$
  - $A=16384$: $\rho = 0.952$
  - $A=65536$: $\rho = 0.952$

The hierarchy shifts (nemesis_alpha2 swapping with v5_scout_striker, and v4_claimer overtaking v5_region_attacker at extreme scales) reflect arena geometry and fixed territorial quota, unchanged from Phase 4B.

---

## K. Transitivity, Cycles & Dominance Graphs

- **Directed 3-Cycles:** 2 cycles at $A=512$; drops to 0 at all larger arenas ($A \ge 1024$).
- **Dominance Edges ($>55\%$ win rate):** 25 at $A=512$, 24 at $A=1024$, 23 at $A=4096$, 24 at $A=16384$, 25 at $A=65536$.
- Transitivity is strong across all scales; large arenas do not introduce cyclic non-transitive ecosystems for this agent field.

---

## L. Action Density & Traversal Bounds Analysis

Action density $S = (Q \times T) / A = 8000 / A$ collapses by a factor of 128 as $A$ expands from 512 to 65,536.

Phase 4C's hypothesis was that if the maximum stride is normalized to $\lfloor A/8 \rfloor$, an agent could cross the arena in at most 8 ticks regardless of scale, countering the drop in action density.

However, because agents only move by 64 cells:
- At $A=512$: traversal requires $512 / 64 = 8$ ticks.
- At $A=65536$: traversal requires $65536 / 64 = 1024$ ticks.

At $A=65536$, crossing the arena takes more ticks than the entire match horizon ($T=1000$). Thus, for fixed-stride agents, large arenas fundamentally prevent global traversal.

---

## M. Key Findings & Answers to the Research Questions

1. **Does increasing environmental stride headroom restore interaction in a frozen benchmark field?**  
   **No.** If agents are authored with internal stride clamps matched to the standard arena size, increasing the environmental ceiling has zero effect on behavior.

2. **Is movement normalization alone sufficient to fix large-arena stagnation?**  
   **No.** Stride bounds define what an agent is *allowed* to do, not what it *chooses* to do. Without an incentive or mechanism to scale movement, agents execute the same actions.

3. **Does the competitive hierarchy change?**  
   **No.** The hierarchy is completely unchanged from Phase 4B ($\rho = 1.000$ cross-phase).

---

## N. Implications for Bytefray V6 Architecture & Future Rulesets

This experiment yields three major architectural lessons for Bytefray V6:

1. **Environmental Headroom vs Behavioral Adaptation:**  
   In simulation arenas with programmable agents, changing ruleset boundaries (e.g. max stride, max reach, max memory) only affects agents that bump against those boundaries. Agents with defensive internal bounds are unaffected.

2. **The Need for Scale Awareness in Agent API:**  
   Under Agent API v2, `ObservationV2` and match context do not currently provide a standardized way for agents to query `arena_size` or optimal stride, leading authors to hardcode constants like `64`. Future API iterations must consider whether `arena_size` should be part of the agent's observation or initialization context.

3. **Environmental Scaling vs Intrinsic Scaling:**  
   If a ruleset intends to normalize traversal across arena scales for *all* agents (including legacy or frozen agents), movement cannot simply be permitted up to a higher bound; it must be scaled multiplicatively at the runtime level (e.g. `actual_move = requested_stride * (arena_size / 512)`), or a dedicated scale-aware agent field must be benchmarked.

---

## O. Recommendations for Phase 4D

Based on the evidence from Phase 4B and Phase 4C, the following next steps are recommended:

1. **Phase 4D Candidate 1: Multiplicative Movement Scaling (Runtime-Enforced Traversal Normalization)**  
   Instead of expanding headroom via $\text{max\_move\_delta}$, evaluate a ruleset that scales movement multiplicatively:
   $$\Delta_{\text{actual}} = \Delta_{\text{requested}} \times \frac{A}{512}$$
   This would force even hardcoded 64-stride agents to cover proportional distances (e.g. 64 becomes 8192 at $A=65536$), directly testing whether actual high-speed traversal destabilizes the hierarchy.

2. **Phase 4D Candidate 2: Territory Scoring Normalization**  
   As shown in Phase 4B and 4C, territorial expanders (`v4_claimer`) suffer a 16-fold collapse in territory share because score is evaluated as raw percentage of arena size. Testing a fixed-cell territorial threshold or scale-normalized scoring would isolate the economic/territory dimension.

3. **Phase 4D Candidate 3: Agent Adaptation Study**  
   Author scale-aware revisions of the benchmark agents (e.g. `Octave_v6`, `claimer_v6`) that query arena size and request full normalized strides, comparing their performance against the frozen v4/v5 baselines.

---

## Research Integrity Addendum (2026-09-22)

Two independent research-integrity reviews have established that the Phase 4 arena-scaling and movement research line was grounded in flawed causal premises and compromised by test and benchmark defects:

1. **V4 Tick-1 Forced-Win Gate:** Shipped stable `bytefray-rules-4` contains a deterministic tick-1 Seat-A forced core capture under competent global-reach play (`CompetentGlobalSniperProbe`), winning on tick 1 before Seat B ever executes an instruction. This seat/order-driven exploit was the unacknowledged driver of apparent lethality in global probes, invalidating interpretations of global reach as balanced gameplay.
2. **Benchmark Corpus Tracking (Octave):** The V6-Bench-8 field previously depended on an untracked local `Octave` agent in the user's private `agents/` directory. Octave has now been fingerprinted (`e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730`) and permanently committed to tracked repository fixtures under `tools/research/v6/fixtures/agents/Octave/`.
3. **Territory Scoring Invariance:** Territory scoring was incorrectly described in Phase 4C as scaling with arena percentage and suffering "dilution." In reality, `ScoringPolicy` awards 1 point per 64 raw cells held ($\lfloor \text{cells} / 64 \rfloor$) independently of arena size. Scoring was always invariant to arena dimensions.
4. **Agent Context Arena Size:** Phase 4C incorrectly asserted that `ObservationV2` and match context hid `arena_size` from agents. In fact, `context.arena_size` was already supplied in `AgentContext` upon initialization.
5. **Fallacy of $\sigma^2_{\text{opp}}$ as Counterplay:** Variance of win rates across opponents is a mathematical property of intermediate ranks in a purely transitive 1D skill hierarchy, not evidence of opponent-dependent counterplay or non-transitivity. It has been replaced by 1D rating models, matchup residuals ($R_{ij} = W_{ij} - \hat{W}_{ij}$), upset reversals, and explicit tie tracking.
6. **Cycle Disappearance Artifact:** The apparent disappearance of directed 3-cycles at larger arenas was an artifact of win rates slipping below the fixed 0.55 dominance threshold, not a reversal or restructuring of competitive ordering.
7. **Line Closure & Transition to E2:** The arena-scaling and movement normalization line is closed. Active research pivots to E2 — Multi-Tick Capture Hold to address the root causal vulnerability identified in stable V4.
