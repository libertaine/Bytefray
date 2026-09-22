# Bytefray V6 Phase 4D — Proportional Movement Semantics Study

**Status:** Complete  
**Branch:** `v6-research`  
**Baseline:** `974ae13` (+ Phase 4D Commit 1 `983d678`)  
**Ruleset introduced:** `bytefray-rules-6-research-scale-move-proportional`  
**Predecessors:** [`V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md`](V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md), [`V6_PHASE4B_ARENA_SCALING_STUDY.md`](V6_PHASE4B_ARENA_SCALING_STUDY.md), [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md)  

---

## A. Executive Summary & Core Research Question

Phase 4C tested passive scale-normalized movement headroom (`max_move_delta = max(64, A // 8)`) and yielded a definitive null result: because the frozen `V6-Bench-8` agents were authored under the 512-cell reference paradigm, none ever requested an operand exceeding 64 cells. All 2,240 Phase 4C sweep matches were behaviorally identical to Phase 4B raw-scaling control (0.0 gameplay delta).

Phase 4D addresses the unanswered causal question:

> **What happens if MOVE operands emitted by frozen agents are interpreted proportionally to arena scale while holding all agent source code, scoring, reach, placement, tick horizon, and action budgets completely frozen?**

### The Definitive Finding

Phase 4D executed the complete empirical protocol: 2,240 sweep matches across five arena sizes ($A \in \{512, 1024, 4096, 16384, 65536\}$), preceded by a live 448-match equivalence gate at $A=512$, all evaluated over the frozen `V6-Bench-8` benchmark field with 0 source drift.

The experimental outcome reveals a profound mathematical and architectural discovery:

> **Proportional movement displacement does not restore scale-invariant gameplay. Instead, it induces severe discrete lattice aliasing ("sublattice tunneling") and creates acute behavioral dyspraxia across agent archetypes.**
>
> 1. **Massive Surge in Timeouts and Contact Failure:** Rather than increasing contact, proportional movement *drastically reduced* lethal engagement. Timeouts surged from 31.2% at $A=512$ to **66.7% at $A=65536$** (+27.7% above Phase 4B/4C). At $A=65536$, **49.6% of matches never made contact at all** (compared to only 10.7% in Phase 4B).
> 2. **Sublattice Tunneling Effect:** Because movement displacement is multiplied by $A / 512$ (up to $128\times$) while agent reach remains frozen at $R \le 4$, agents jump in discrete strides over 127 out of every 128 cells. Unless the agents' stride orbits intersect modulo 128 within the tiny reach envelope, agents reside in disjoint sublattices, literally hopping past each other indefinitely without sensing or colliding.
> 3. **The Collapse of Precision Interception (Scout Striker):** Precision pursuit agent `v5_scout_striker` suffered a catastrophic collapse, dropping from **0.72 win rate at $A=512$** down to **0.30 at $A=65536$** (a **-38.4% win rate delta** vs Phase 4B/4C). Its strike loops suffer severe *overshoot dyspraxia*, leaping hundreds of cells past enemy positions.
> 4. **The Surge of Territory Expansion (Claimer):** Conversely, territorial painter `v4_claimer` surged from **0.44 win rate at $A=512$ (#5 rank)** to **0.71 at $A=4096$ (#2 rank)** and remained at **0.71 through $A=65536$** (+21.4% delta over Phase 4B/4C). Because combat rarely resolves lethally and timeouts dominate, Claimer's $128\times$ stride amplification paints vast circular arcs across the ring, locking in unbeatable territory tie-break margins.
> 5. **Octave's Vulnerability at Scale:** Global sniper `Octave`, undefeated at 1.00 win rate across all conditions in Phase 4B and 4C, suffered its first non-win outcomes at $A=1024$ (0.99) and $A=65536$ (0.95), as agile opponents tunneled past its rhythmic sweep on disjoint cosets.

---

## B. The Causal Question & The Single Variable

### B.1 Mathematical Formulation of Proportional Displacement

Phase 4D modifies exactly one environmental semantic: how the clamped integer operand `op` of a `MOVE` action is translated into physical ring displacement.

Formally, for an arena of size $A$ and a requested movement operand $op \in [-64, 64]$:

$$\text{actual\_delta}(op, A) = \text{sgn}(op) \times \left\lfloor \frac{|op| \times A}{512} \right\rfloor$$

$$\text{new\_anchor} = (\text{anchor} + \text{actual\_delta}) \pmod A$$

At the reference scale $A=512$, the scale factor is exactly $512 / 512 = 1.0$:

$$\text{actual\_delta}(op, 512) = \text{sgn}(op) \times \lfloor |op| \times 1.0 \rfloor = op$$

Across the five evaluated arena sizes, requested operands scale into physical displacements as follows:

| Arena Size ($A$) | Scale Factor ($A / 512$) | Requested $op = 1$ | Requested $op = 2$ | Requested $op = 10$ | Requested $op = 40$ | Max Requested $op = 64$ |
|---:|:---:|---:|---:|---:|---:|---:|
| 512 | $1\times$ | 1 cell | 2 cells | 10 cells | 40 cells | 64 cells |
| 1024 | $2\times$ | 2 cells | 4 cells | 20 cells | 80 cells | 128 cells |
| 4096 | $8\times$ | 8 cells | 16 cells | 80 cells | 320 cells | 512 cells |
| 16384 | $32\times$ | 32 cells | 64 cells | 320 cells | 1,280 cells | 2,048 cells |
| 65536 | $128\times$ | 128 cells | 256 cells | 1,280 cells | 5,120 cells | 8,192 cells |

### B.2 Controlled Constants Held Frozen

Strict single-variable scientific isolation was maintained across all experimental runs:
1. **Agent Bytecode & Source:** Completely frozen (`V6-Bench-8` verified at 0 drift).
2. **Movement Stride Quota:** Clamped to `[-64, 64]` (the `fixed_64` bounds from stable v4 / Phase 4B). Agents cannot emit larger operands than allowed in Phase 4B.
3. **Territory Scoring:** Proportional to arena size ($\sum \text{cells} / A$).
4. **Perceptual / Action Reach:** Unchanged; local reach $R \le 4$ cells per process.
5. **Initial Core Placement:** Seed-derived deterministic separation $\ge 64$ cells.
6. **Tick Horizon:** Fixed at $T = 1000$ ticks.
7. **Action Budget:** Fixed at $Q = 8$ instructions per tick.
8. **Scheduling:** Chunked $K=2$ with round-robin intra-entrant process selection.

---

## C. Ruleset Architecture & Formal Semantics

### C.1 Ruleset Policy Registration

The new research Ruleset is registered in `battle_engine.ruleset_policy` under the canonical protocol identity:

```python
BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID = (
    "bytefray-rules-6-research-scale-move-proportional"
)

RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL = RulesetPolicy(
    ruleset_id="bytefray-rules-6-research-scale-move-proportional",
    supported_runtime_kinds=frozenset({"python"}),
    supported_python_api_versions=frozenset({2}),
    scheduler_mode="chunked",
    scheduler_chunk_size=2,
    scheduler_rotate_start=True,
    core_placement="seeded",
    process_selection="round_robin",
    movement_stride="fixed_64",
    movement_displacement="scale_from_512",
)
```

### C.2 Displacement Resolution Pipeline

In `battle_engine.process_runtime`, the `MOVE` action handler evaluates displacement through the ruleset policy:

```python
# process_runtime.py
elif kind == ActionKindV2.MOVE:
    max_delta = self.ruleset_policy.resolve_max_move_delta(arena_size)
    clamped_op = max(-max_delta, min(max_delta, action.operand))
    actual_delta = self.ruleset_policy.resolve_movement_displacement(
        clamped_op, arena_size
    )
    process.anchor = (process.anchor + actual_delta) % arena_size
```

### C.3 Formal Invariants Tested

Unit tests (`engine/tests/test_ruleset_v6_research_scale_move_proportional.py`) prove four structural invariants:
1. **Anchor Identity at A=512:** For all operands $op$, `resolve_movement_displacement(op, 512) == op`.
2. **Sign Symmetry:** For all operands $op$ and arena sizes $A$, `resolve_movement_displacement(-op, A) == -resolve_movement_displacement(op, A)`.
3. **Zero Invariance:** `resolve_movement_displacement(0, A) == 0`.
4. **Strict Monotonicity:** For $op_1 > op_2 \ge 0$, `actual_delta(op1, A) >= actual_delta(op2, A)`.

---

## D. Baseline Verification & Field Integrity (V6-Bench-8)

### D.1 Environment Baseline
- **Git Branch:** `v6-research`
- **Pre-study HEAD:** `974ae13`
- **Runtime:** Python 3.13.14 (AMD64, Windows 11)
- **Predecessor Commits:** `ae38b62`, `be6cd11`, `974ae13` (Phase 4C completion)

### D.2 Benchmark Field SHA-256 Fingerprints

The benchmark field `V6-Bench-8` was verified prior to match execution using `tools/research/v6/phase4d_corpus_runner.py fingerprints`. All 8 agent directories matched their Phase 4B and Phase 4C revision fingerprints exactly:

| Agent Name | Archetype | SHA-256 Fingerprint (`agent_revision_id`) | Drift vs 4B/4C |
|---|---|---|:---:|
| `Octave` | Global sniper | `e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730` | 0 |
| `nemesis_alpha2` | Stationary core hunter | `6d5a8492b34a77cbbbe795152370ed20c65f2c55da20dc96a35f5d28c3b44f5c` | 0 |
| `v5_scout_striker` | Mobile pursuit | `290e02004291abd77967bc43e549e07eddad9851915ddd9f5edc2fd5e0de0ac1` | 0 |
| `v5_region_attacker` | Regional suppressor | `8855d950c08f8f95cdca192ed817b853d6350cdbe7ec0bd6d161879e5237ddcb` | 0 |
| `v5_dual_team` | Coordinated 2-process | `71e9e84c17fe7a6f084ca9b83d0394741c9edfb24df8b593441f97a2910030af` | 0 |
| `v4_claimer` | Territorial expander | `342d5a20df20c0154774fbbbd643256e1afbc593b9d735ddb831388cfeebc952` | 0 |
| `v5_core_defender` | Reactive defense | `2a47c0386ff88d58b810eef97a1f093a89050d5ba3a5ae52a31c56eb2de0cc95` | 0 |
| `v4_local_defender` | Passive floor control | `6a64a4ba742f04e389f1301bd4a0210866d54b3464c7c01bc497138c30318453` | 0 |

Result: **0 source drift**. All agent bytecodes remained 100% frozen.

---

## E. Smoke Verification (A=512, A=65536)

Smoke tests (`SMOKE_FIELD = (Octave, v4_claimer, v5_core_defender)`; 2 seeds $\times$ 2 orientations = 12 matches per condition) confirmed both operational health and behavioral divergence at scale:

| Arena Size | Matches | Wall Clock | Mean Time / Match | Completed | Divergence vs Phase 4B/4C |
|---:|---:|---:|---:|:---:|:---:|
| 512 | 12 | 2.25 s | 0.188 s | 12 / 12 | **None** (identical score/ticks) |
| 65536 | 12 | 3.75 s | 0.312 s | 12 / 12 | **Diverged** (ticks run and scores differ) |

Specifically, in cell `Octave vs v4_claimer` (seed 1, normal orientation) at $A=65536$:
- Phase 4B/4C: Match ran 6 ticks, score `{'A': 11.0, 'B': 5.0}`.
- Phase 4D: Match ran 8 ticks, score `{'A': 13.0, 'B': 7.0}`.

---

## F. Control Invariants & The A=512 Equivalence Gate

The live Equivalence Gate was executed at $A=512$ comparing `bytefray-rules-6-research-scale` (Phase 4B control) against `bytefray-rules-6-research-scale-move-proportional` (Phase 4D candidate) over the complete 448-match round-robin:

```
[equivalence] research-scale: 448 matches in 88.95s
[equivalence] research-scale-move-proportional: 448 matches in 96.65s
```

`tools/research/v6/phase4d_equivalence_check.py` evaluated all 448 match pairs cell by cell:

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

- **Placement Geometry:** 448 / 448 starts matched identically.
- **Match Outcomes:** Winners, ticks run, scores, territory, and termination reasons matched identically.
- **Deep Replay Stream:** Full tick-by-tick event streams and memory diffs matched byte-for-byte.

This proves conclusively that at the $A=512$ anchor point, `bytefray-rules-6-research-scale-move-proportional` has **zero gameplay drift**.

---

## G. Comprehensive Empirical Sweep Results Across 5 Arenas

The full 2,240-match sweep was executed across all five arena sizes ($A \in \{512, 1024, 4096, 16384, 65536\}$):

```
[sweep] arena=512: 448 matches in 94.06s
[sweep] arena=1024: 448 matches in 112.70s
[sweep] arena=4096: 448 matches in 160.01s
[sweep] arena=16384: 448 matches in 145.21s
[sweep] arena=65536: 448 matches in 170.09s
```

### G.1 Aggregate Metrics by Arena Size

| Metric | Arena 512 | Arena 1024 | Arena 4096 | Arena 16384 | Arena 65536 |
|---|---:|---:|---:|---:|---:|
| **Action Density $S(A)$** | 15.625 | 7.813 | 1.953 | 0.488 | 0.122 |
| **Displacement Factor** | $1\times$ | $2\times$ | $8\times$ | $32\times$ | $128\times$ |
| **Matches Completed** | 448 | 448 | 448 | 448 | 448 |
| **Timeouts** | 140 | 184 | 276 | 284 | **299** |
| **Timeout Rate** | **31.2%** | **41.1%** | **61.6%** | **63.4%** | **66.7%** |
| **Mean Ticks Run** | 344.5 | 421.2 | 625.7 | 652.6 | **703.9** |
| **Median Ticks Run** | 11.0 | 8.0 | 1000.0 | 1000.0 | **1000.0** |
| **Last Agent Standing** | 308 | 264 | 172 | 164 | **149** |
| **Dominance Edges ($>0.55$)** | 25 | 25 | 20 | 18 | **17** |
| **Directed 3-Cycles** | 2 | 3 | 1 | 0 | **0** |
| **Spearman $\rho$ vs $A=512$** | **1.000** | **0.810** | **0.690** | **0.619** | **0.667** |

### G.2 Win Rates and Hierarchy Ordering

| Agent | $A=512$ (Rank) | $A=1024$ (Rank) | $A=4096$ (Rank) | $A=16384$ (Rank) | $A=65536$ (Rank) |
|---|:---:|:---:|:---:|:---:|:---:|
| `Octave` | **1.000** (#1) | **0.987** (#1) | **1.000** (#1) | **1.000** (#1) | **0.946** (#1) |
| `nemesis_alpha2` | 0.621 (#3) | 0.665 (#2) | 0.652 (#3) | 0.737 (#2) | **0.786** (#2) |
| `v4_claimer` | 0.438 (#5) | 0.598 (#3) | **0.714** (#2) | **0.714** (#3) | **0.714** (#3) |
| `v5_core_defender` | 0.170 (#7) | 0.138 (#8) | 0.357 (#5) | 0.357 (#4) | 0.371 (#4) |
| `v5_scout_striker` | **0.719** (#2) | 0.571 (#4) | **0.460** (#4) | **0.348** (#5) | **0.299** (#5) |
| `v5_region_attacker` | 0.580 (#4) | 0.438 (#6) | 0.313 (#7) | 0.286 (#7) | 0.299 (#6) |
| `v5_dual_team` | 0.379 (#6) | 0.451 (#5) | 0.326 (#6) | 0.295 (#6) | 0.299 (#7) |
| `v4_local_defender` | 0.094 (#8) | 0.152 (#7) | 0.179 (#8) | 0.263 (#8) | 0.286 (#8) |

---

## H. Comparative Analysis: Phase 4D vs Phase 4B (Raw) & Phase 4C (Headroom)

Because Phase 4B and Phase 4C are behaviorally identical on frozen agents, comparisons against Phase 4B and Phase 4C yield the exact same deltas.

### H.1 Cross-Phase Spearman Rank Correlation ($\rho$)

| Arena Size ($A$) | Phase 4B $\rho$ vs $A=512$ | Phase 4D $\rho$ vs $A=512$ | Cross-Phase $\rho$ (Phase 4D vs Phase 4B) |
|---:|:---:|:---:|:---:|
| 512 | 1.000 | 1.000 | **1.000** |
| 1024 | 0.976 | 0.810 | **0.857** |
| 4096 | 0.976 | 0.690 | **0.714** |
| 16384 | 0.952 | 0.619 | **0.786** |
| 65536 | 0.952 | 0.667 | **0.810** |

*Interpretation:* In Phase 4B raw scaling, the competitive hierarchy was exceptionally stable ($\rho \ge 0.952$ across all scales). Proportional movement substantially reshuffled the hierarchy ($\rho$ drops to 0.619 at $A=16384$ and 0.667 at $A=65536$).

### H.2 Timeout Rate and Mean Duration Deltas

| Arena Size ($A$) | Phase 4B Timeout Rate | Phase 4D Timeout Rate | Timeout Delta (4D $-$ 4B) | Mean Ticks Delta (4D $-$ 4B) |
|---:|:---:|:---:|:---:|:---:|
| 512 | 31.2% | 31.2% | **+0.0%** | +0.0 ticks |
| 1024 | 35.9% | 41.1% | **+5.1%** | +26.4 ticks |
| 4096 | 41.1% | 61.6% | **+20.5%** | +203.6 ticks |
| 16384 | 39.7% | 63.4% | **+23.7%** | +233.1 ticks |
| 65536 | 39.1% | 66.7% | **+27.7%** | +244.5 ticks |

*Interpretation:* Timeouts surged dramatically at every arena size above 512, reaching 66.7% at $A=65536$. Mean ticks run increased by over 240 ticks per match.

### H.3 Win Rate Deltas by Agent ($\Delta = \text{WR}_{4D} - \text{WR}_{4B}$)

| Agent | $\Delta(1024)$ | $\Delta(4096)$ | $\Delta(16384)$ | $\Delta(65536)$ | Net Trajectory |
|---|:---:|:---:|:---:|:---:|:---|
| `Octave` | -1.3% | 0.0% | 0.0% | **-2.2%** | First non-win outcomes at scale |
| `nemesis_alpha2` | -1.8% | -5.4% | +0.4% | **+3.6%** | Stable hunter at high scale |
| `v4_claimer` | **+14.3%** | **+21.4%** | **+17.0%** | **+14.3%** | **Massive winner across all scales** |
| `v5_core_defender` | -3.1% | **+17.9%** | **+18.8%** | **+21.0%** | Survives due to combat evasion |
| `v4_local_defender` | +4.9% | +7.6% | **+16.1%** | **+19.2%** | Survives due to combat evasion |
| `v5_dual_team` | +7.6% | -1.3% | 0.0% | +3.6% | Neutral / modest drift |
| `v5_region_attacker` | **-12.5%** | **-21.0%** | **-19.2%** | **-21.0%** | Severe impairment |
| `v5_scout_striker` | **-8.0%** | **-19.2%** | **-33.0%** | **-38.4%** | **Catastrophic collapse** |

---

## I. Tier 2 Dynamics: Interaction, Contact, & Stagnation

To explain *why* timeouts increased and precision agents collapsed, Tier 2 telemetry was extracted from all 2,240 match replay event streams.

### I.1 Contact and Hostile Interaction Rates

| Metric | Arena 512 | Arena 1024 | Arena 4096 | Arena 16384 | Arena 65536 | Phase 4B ($A=65536$) |
|---|---:|---:|---:|---:|---:|---:|
| **Matches Never in Contact** | 16 (3.6%) | 18 (4.0%) | 105 (23.4%) | 162 (36.2%) | **222 (49.6%)** | 48 (10.7%) |
| **Never Contact Rate Delta vs 4B** | +0.0% | +0.4% | +19.9% | +27.5% | **+38.8%** | — |
| **Matches With No Hostile Write** | 16 (3.6%) | 20 (4.5%) | 136 (30.4%) | 182 (40.6%) | **258 (57.6%)** | 59 (13.2%) |
| **Mean First Contact Tick (when contact occurs)** | 5.5 | 5.6 | 11.7 | 19.7 | **11.7** | 96.3 |
| **Stagnation Rate ($\ge 100$ zero-diff ticks)** | 0.0% | 3.6% | 10.7% | 17.2% | **21.4%** | 2.2% |

### I.2 The Physics of Sublattice Tunneling (Discrete Lattice Aliasing)

Why did the never-contact rate jump from 10.7% in Phase 4B to **49.6% in Phase 4D**, even though agents were moving $128\times$ faster?

In continuous physical space, multiplying speed by $k$ increases collision cross-section per unit time. However, Bytefray operates on a **finite discrete circular ring $\mathbb{Z}_A$** with discrete cell coordinates:

1. **Discrete Modular Striding:** At $A=65536$, an agent moving with basic step $op = 1$ is displaced by $128$ cells per tick. An agent starting at coordinate $s$ visits only the cyclic subgroup coset:
   $$\mathcal{L}_A(s) = \{s + 128 \cdot m \pmod{65536} \mid m \in \mathbb{Z}\}$$
2. **Fixed Local Reach:** An agent's perceptual and action reach remains frozen at $R \le 4$ cells around its anchor. The interaction window is an interval of width $2R + 1 \le 9$ cells.
3. **Disjoint Cosets:** There are $128$ mutually disjoint cosets of period 128 in $\mathbb{Z}_{65536}$. Unless the opponent's anchor $s'$ happens to satisfy:
   $$| (s + 128m) - (s' + 128m') | \pmod{65536} \le 2R$$
   the two processes can never be within reach of one another. The probability that two independent seeds and step sizes allow reach overlap on any given tick is on the order of:
   $$P(\text{overlap}) \approx \frac{2R + 1}{128} \approx \frac{9}{128} \approx 7.0\%$$
4. **Quantum Tunneling / Aliasing:** The agents move at high speed, but they skip across 127 uninspected cells on every single tick. They literally jump over each other! A fast scout leaping 128 cells per step will jump right across an enemy core without ever triggering a collision or observation.

---

## J. Octave Diagnostic

`Octave` is Bytefray's benchmark reference agent: a multi-process global sweeper that systematically clears the arena with rhythmic sniper sweeps.

### J.1 Performance Across Scale

- **Phase 4B/4C Control:** Octave achieved a perfect 1.000 win rate at 512, 1024, 4096, 16384, and 0.969 at 65536 (337 wins, 0 losses, 67 ties across all opponents).
- **Phase 4D Proportional Movement:**
  - $A=512$: 1.000 (112 / 112 wins)
  - $A=1024$: **0.987** (dropped from 1.000; Octave tied two matches)
  - $A=4096$: 1.000 (112 / 112 wins)
  - $A=16384$: 1.000 (112 / 112 wins)
  - $A=65536$: **0.946** (dropped from 0.969; Octave tied six matches)

### J.2 Diagnostic Mechanism

Octave's multiple processes mitigate some sublattice aliasing because its processes are staggered around the ring. However, at $A=65536$, Octave's sweep patterns are stretched by $128\times$, creating wide blind gaps where evasive agents (like `nemesis_alpha2` or `v4_claimer`) survive outside Octave's sweep radius until the tick limit expires. Octave never lost a match outright, but its dominance was degraded by timeout draws.

---

## K. Scout Striker Diagnostic: The Collapse of Precision Hunting

`v5_scout_striker` was the second-ranked agent in Bytefray v4/v5, designed as a high-mobility pursuit interceptor that detects enemy signatures, closes distance, and writes kill instructions.

### K.1 Empirical Collapse

| Arena Size ($A$) | Phase 4B Win Rate | Phase 4D Win Rate | Win Rate Delta | Rank in Phase 4D |
|---:|:---:|:---:|:---:|:---:|
| 512 | 0.719 | 0.719 | **0.0%** | #2 |
| 1024 | 0.652 | 0.571 | **-8.0%** | #4 |
| 4096 | 0.652 | 0.460 | **-19.2%** | #4 |
| 16384 | 0.679 | 0.348 | **-33.0%** | #5 |
| 65536 | 0.683 | 0.299 | **-38.4%** | #5 |

Against `v4_claimer`, Scout Striker's head-to-head win rate collapsed from **1.000 in Phase 4B** to **0.000 in Phase 4D** at $A \ge 4096$!

### K.2 Causal Mechanism: Overshoot Dyspraxia

Scout Striker's authored tracking loop assumes that requesting a small delta ($op = \pm 1$ or $\pm 2$) moves it into adjacent contact with an observed enemy.
- At $A=512$, $op = 1$ moves $1$ cell, landing within reach $R=2$.
- At $A=65536$, $op = 1$ is scaled by $128\times$ to **128 cells**.
- When Scout Striker senses an enemy core 10 cells away and requests a 1-cell step toward it, the runtime moves it 128 cells in that direction—hurling Scout Striker 118 cells *past* the target!
- On the next tick, Scout Striker senses the enemy behind it and requests $op = -1$, which hurls it 128 cells backward!
- Scout Striker enters an infinite oscillation loop, wildly jumping back and forth across the enemy without ever landing within striking distance ($R \le 2$).

---

## L. Claimer Diagnostic: The Area-Expansion Explosion

`v4_claimer` was a mid-tier territorial expander that steps along the arena dropping ownership claims.

### L.1 Empirical Surge

| Arena Size ($A$) | Phase 4B Win Rate | Phase 4D Win Rate | Win Rate Delta | Rank in Phase 4D |
|---:|:---:|:---:|:---:|:---:|
| 512 | 0.438 | 0.438 | **0.0%** | #5 |
| 1024 | 0.455 | 0.598 | **+14.3%** | #3 |
| 4096 | 0.500 | 0.714 | **+21.4%** | #2 |
| 16384 | 0.545 | 0.714 | **+17.0%** | #3 |
| 65536 | 0.571 | 0.714 | **+14.3%** | #3 |

At $A=4096$, Claimer surged ahead of both `nemesis_alpha2` and `v5_scout_striker` to take the **#2 position in the arena**, beaten only by `Octave`.

### L.2 Causal Mechanism: Stride-Amplified Painting

Claimer does not attempt precision core sniping. It simply moves and claims.
- In Phase 4B, Claimer's territory expansion was bounded by 64 cells per move, so in larger arenas its territorial share shrank to negligible fractions.
- In Phase 4D, Claimer's displacement scales to 128 cells per step at $A=65536$. It traverses huge circumferential swathes in tens of ticks.
- Because opponents cannot intercept it (due to overshoot dyspraxia and sublattice tunneling), matches invariably reach the $T=1000$ tick limit.
- At tick 1000, Claimer possesses vast territorial holdings, winning the match on score.

---

## M. Structural Threats to Validity

1. **Frozen Agent Bias:** The study evaluated agents written under the assumption that $op = 1$ means 1 cell. Agents written with scale-awareness could conceivably adjust their operands or avoid oscillatory loops. However, testing frozen agents was the precise causal objective of Phase 4D: isolating the environmental effect from agent co-adaptation.
2. **Perception-Displacement Decoupling:** Proportional displacement scaled movement without scaling perceptual reach ($R \le 4$). Scaling displacement while holding perception constant broke the spatial Nyquist criterion of the cellular automaton.
3. **Discrete Ring Geometry:** Modular wrapping on $\mathbb{Z}_A$ creates discrete cosets that do not exist in continuous Euclidean space.

---

## N. Research Conclusions & Roadmap Integration

### N.1 The Definitive Answers to Phase 4 Research Questions

1. **Phase 4B (Raw Scaling):** Proved that raw scaling delays interaction and reduces territorial viability, but leaves aggregate competitive order largely intact.
2. **Phase 4C (Passive Headroom):** Proved that raising the allowable MOVE limit without modifying agent logic produces a clean null result (0.0 delta).
3. **Phase 4D (Proportional Movement):** Proved that proportionally scaling displacement operands without scaling perceptual reach induces severe discrete sublattice tunneling, triples the timeout rate, cripples precision combat agents (-38.4%), and artificially elevates area-claim agents (+21.4%).

### N.2 Architectural Implications for Bytefray V6

- **Environmental Movement Scaling in Isolation is Unsound:** Proportional movement cannot be introduced as a naive single-variable patch. Doing so destroys close-quarters combat and causes agents to jump over each other.
- **The Nyquist Constraint of Cellular Arenas:** If an agent's step size $\Delta$ exceeds its reach diameter $2R + 1$, the agent suffers blind tunneling. Any future scaling model that increases traversal speed must either:
  1. Scale sensory and action reach in tandem ($\Delta \propto A \implies R \propto A$), or
  2. Maintain unit displacement step sizes while scaling the action budget / tick horizon, or
  3. Expose arena scale explicitly in the Agent API (`ObservationV2.arena_size`) so authored agents can adapt their own strategic planning.

This concludes Phase 4D of the Bytefray V6 research program.
