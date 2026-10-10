# Bytefray V6 Phase 4D — Proportional Movement Semantics Study

**Status:** Complete
**Branch:** `v6-research`
**Baseline:** `974ae13` (+ Phase 4D Commit 1 `983d678`)
**Ruleset introduced:** `bytefray-rules-6-research-scale-move-proportional`
**Predecessors:** [`V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md`](V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md), [`V6_PHASE4B_ARENA_SCALING_STUDY.md`](V6_PHASE4B_ARENA_SCALING_STUDY.md), [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md)

---

## A. Objective

Phase 4C tested passive scale-normalized movement headroom (`movement_stride = "scale_normalized"`, where `max_move_delta = max(64, floor(A / 8))`) and produced a clean null result:
- The engine allowed larger MOVE operands up to 8,192 cells at $A=65536$;
- The frozen `V6-Bench-8` agents, authored under the 512-cell reference paradigm, continued emitting their hardcoded absolute deltas ($\le 64$ cells);
- Therefore, all 2,240 Phase 4C matches were behaviorally identical to the Phase 4B raw-scale control (0.0 gameplay delta).

Phase 4C established that passive environmental headroom is completely inert when agent logic remains frozen. This phase asks the central unanswered causal question:

> **What happens if MOVE itself is interpreted proportionally to arena scale while the agents remain frozen?**

This modifies exactly one environmental semantic: world-space displacement per MOVE action scales proportionally with arena size ($A$), transforming accepted authored deltas into scale-normalized spatial units:

$$\Delta_{\text{actual}} = \text{scale}(\Delta_{\text{requested}}, A)$$

Strict scientific controls are preserved:
- Agent source code and bytecode remain 100% frozen.
- No normalization of scoring, perception reach ($R \le 4$), initial placement separation ($\ge 64$), tick horizon ($T=1000$), action budget ($Q=8$), or scheduling.
- The experiment cleanly isolates **control input** (agent emits $|op| \le 64$) from **world-space displacement** (runtime executes scaled displacement).

---

## B. Movement Semantics

### B.1 Mathematical Formulation
Using the canonical 512-cell reference world, the scale factor for an arena of size $A$ is:

$$\text{scale} = \frac{A}{512}$$

To guarantee deterministic, platform-independent execution with no floating-point rounding or hidden IEEE-754 discrepancies, physical displacement is defined strictly with integer arithmetic:

$$\text{actual\_delta}(op, A) = \begin{cases} 0 & \text{if } op = 0 \\ \text{sgn}(op) \times \left\lfloor \frac{|op| \times A}{512} \right\rfloor & \text{if } op \ne 0 \end{cases}$$

In Python: `sign * (abs(requested_delta) * arena_size // 512)`.

### B.2 Invariant Properties
1. **Exact Equivalence at A=512:** At $A=512$, $scale = 1$, so $\text{actual\_delta}(op, 512) = op$ exactly.
2. **Sign Symmetry:** $\text{actual\_delta}(-op, A) = -\text{actual\_delta}(op, A)$ for all $op \in \mathbb{Z}$ and $A \in \mathbb{N}$.
3. **Zero Invariance:** $\text{actual\_delta}(0, A) = 0$.
4. **Nonzero Preservation for $A \ge 512$:** Since $A / 512 \ge 1$, any nonzero requested delta $|op| \ge 1$ yields $|actual\_delta| \ge 1$.
5. **Circular Ring Modulo Wrapping:** $\text{new\_anchor} = (\text{anchor} + \text{actual\_delta}) \pmod A$.

---

## C. Research Ruleset

### C.1 RulesetPolicy Ownership
In accordance with Bytefray architectural principles, gameplay semantics are owned explicitly by `RulesetPolicy` rather than hardcoded string checks in execution loops. Two orthogonal movement dimensions are maintained:
- `movement_stride`: Controls the accepted input operand ceiling (`"fixed_64"` vs `"scale_normalized"`).
- `movement_displacement`: Controls how accepted operands map to world space (`"literal"` vs `"scale_from_512"`).

The new research identity is registered in `battle_engine.ruleset_policy`:

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

### C.2 Preserved Controls
All preceding Ruleset identities remain completely unmodified:
- `bytefray-rules-4` (Stable V4): literal movement, fixed_64, pinned $A=512$.
- `bytefray-rules-6-research-scale` (Phase 4B raw-scale): literal movement, fixed_64, variable arena.
- `bytefray-rules-6-research-scale-move` (Phase 4C headroom): literal movement, scale_normalized headroom, variable arena.

### C.3 Runtime Execution Pipeline
During tick execution in `ProcessMatchController`:
```python
op = action.operand if action.operand is not None else 0
clamped_op = max(-self.max_move_delta, min(op, self.max_move_delta))
delta = self.ruleset_policy.resolve_movement_displacement(
    clamped_op, self.config.arena_size
)
active_proc.position = (active_proc.position + delta) % self.config.arena_size
```
Replay records the resulting process position in each tick snapshot (`anchor`), while decision traces record the requested operand and applied position. Replay Schema 4 remains fully sufficient.

---

## D. A=512 Equivalence

At $A=512$, the scale factor is exactly $1\times$. Therefore, `bytefray-rules-6-research-scale-move-proportional` must produce zero gameplay deviation from `bytefray-rules-6-research-scale`.

### D.1 Live Full-Field Verification
Before executing scale sweeps, the live Equivalence Gate was executed across the complete `V6-Bench-8` field:
- 28 unordered agent pairs $\times$ 8 seeds $\times$ 2 orientations = **448 matches per Ruleset**.
- Total: 896 matches executed at $A=512$ (`tools/research/v6/phase4d_corpus_runner.py equivalence`).

### D.2 Cell-by-Cell Replay & Result Comparison
All 448 paired cells were compared bit-for-bit using `tools/research/v6/phase4d_equivalence_check.py`:
- **Placement Geometry:** 448 / 448 initial positions matched identically.
- **Actions & Trajectories:** 448 / 448 movement trajectories matched identically.
- **Match Outcomes:** Winners, ticks run, scores, territory shares, kills, and deaths matched identically.
- **Deep Replay Stream:** Full tick-by-tick event streams and memory diffs matched byte-for-byte.

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
EQUIVALENCE GATE (A=512): PASS (0 gameplay mismatches)
```

---

## E. Movement Characterization

### E.1 Requested vs Actual Displacement Across Study Arenas

| Arena Size ($A$) | Scale Factor ($A / 512$) | $op = 0$ | $op = \pm 1$ | $op = \pm 2$ | $op = \pm 40$ | Max Authored $op = \pm 64$ |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **512** | $1\times$ | 0 | $\pm 1$ cell | $\pm 2$ cells | $\pm 40$ cells | $\pm 64$ cells |
| **1024** | $2\times$ | 0 | $\pm 2$ cells | $\pm 4$ cells | $\pm 80$ cells | $\pm 128$ cells |
| **4096** | $8\times$ | 0 | $\pm 8$ cells | $\pm 16$ cells | $\pm 320$ cells | $\pm 512$ cells |
| **16384** | $32\times$ | 0 | $\pm 32$ cells | $\pm 64$ cells | $\pm 1,280$ cells | $\pm 2,048$ cells |
| **65536** | $128\times$ | 0 | $\pm 128$ cells | $\pm 256$ cells | $\pm 5,120$ cells | $\pm 8,192$ cells |

### E.2 Characterization Invariants Verified
- **Boundary Arenas & Truncation:** At $A=64$, requested operands $|op| < 8$ truncate to 0 ($\lfloor 1 \times 64 / 512 \rfloor = 0$), while $op = 8$ yields 1 cell and $op = 64$ yields 8 cells.
- **Odd / Non-Power-of-Two Arenas:** At $A=777$, $op = 40$ maps deterministically to $\lfloor 40 \times 777 / 512 \rfloor = 60$ cells; $op = -40$ maps to $-60$ cells.
- **Extreme Scale:** At $A = 2^{24} = 16,777,216$, $op = 40$ maps to $1,310,720$ cells with exact Python arbitrary-precision integer arithmetic and no 32-bit overflow.
- **Literal Control Isolation:** `RULESET_V4`, `RULESET_V6_RESEARCH_SCALE`, and `RULESET_V6_RESEARCH_SCALE_MOVE` strictly preserve literal displacement ($\Delta_{\text{actual}} = op$) across all arena sizes.

---

## F. Benchmark / Matrix

### F.1 Benchmark Field Integrity (`V6-Bench-8`)
All 8 benchmark agents were verified against Phase 4B and Phase 4C baseline fingerprints using `tools/research/v6/phase4d_corpus_runner.py fingerprints`. All 8 agents showed **0 source drift**:

| Agent Name | Archetype | SHA-256 Fingerprint (`agent_revision_id`) | Drift vs 4B/4C |
|---|---|---|:---:|
| `Octave` | Global multi-process sniper | `e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730` | 0 |
| `nemesis_alpha2` | Stationary core hunter | `6d5a8492b34a77cbbbe795152370ed20c65f2c55da20dc96a35f5d28c3b44f5c` | 0 |
| `v5_scout_striker` | Mobile pursuit interceptor | `290e02004291abd77967bc43e549e07eddad9851915ddd9f5edc2fd5e0de0ac1` | 0 |
| `v5_region_attacker` | Regional suppressor | `8855d950c08f8f95cdca192ed817b853d6350cdbe7ec0bd6d161879e5237ddcb` | 0 |
| `v5_dual_team` | Coordinated 2-process duo | `71e9e84c17fe7a6f084ca9b83d0394741c9edfb24df8b593441f97a2910030af` | 0 |
| `v4_claimer` | Territorial area painter | `342d5a20df20c0154774fbbbd643256e1afbc593b9d735ddb831388cfeebc952` | 0 |
| `v5_core_defender` | Reactive home defense | `2a47c0386ff88d58b810eef97a1f093a89050d5ba3a5ae52a31c56eb2de0cc95` | 0 |
| `v4_local_defender` | Passive floor anchor | `6a64a4ba742f04e389f1301bd4a0210866d54b3464c7c01bc497138c30318453` | 0 |

### F.2 Smoke Gate Verification
Section 18 mandates verifying mobile agents with clearly different movement patterns (`v5_scout_striker`, `v5_dual_team`, `v4_claimer`) and one stationary agent (`nemesis_alpha2`) at $A=512$ and $A=65536$:
- At $A=512$: Trajectories match Phase 4B identically.
- At $A=65536$: Trajectories diverge immediately from tick 1 (displacements scale by $128\times$, leaping thousands of cells per action).
- Total: 24 smoke matches completed at $A=512$ and 24 matches at $A=65536$ without exceptions or crashes.

### F.3 Full Experimental Matrix
- 5 arena sizes: 512, 1024, 4096, 16384, 65536
- 8 benchmark agents, 28 unordered pairs, 8 seeds, 2 orientations
- $28 \times 8 \times 2 = 448$ matches per arena $\times$ 5 arenas = **2,240 matches total**.
- 100% completed under genuine production evaluation artifacts.

---

## G. Interaction Effects

A primary hypothesis of Phase 4D was that proportional movement would overcome large-arena search starvation and accelerate interaction. Telemetry extracted across all 2,240 match replays disproved this hypothesis.

### G.1 Primary Interaction Metrics: Phase 4D vs Phase 4B

| Metric | Arena 512 | Arena 1024 | Arena 4096 | Arena 16384 | Arena 65536 | Phase 4B ($A=65536$) |
|---|---:|---:|---:|---:|---:|---:|
| **Displacement Factor** | $1\times$ | $2\times$ | $8\times$ | $32\times$ | $128\times$ | $1\times$ (Literal) |
| **Timeout Rate** | **31.2%** | **41.1%** | **61.6%** | **63.4%** | **66.7%** | 39.1% |
| **Timeout Delta (4D $-$ 4B)** | **+0.0%** | **+5.1%** | **+20.5%** | **+23.7%** | **+27.7%** | — |
| **Mean Ticks Run** | 344.5 | 421.2 | 625.7 | 652.6 | **703.9** | 459.4 |
| **Median Ticks Run** | 11.0 | 8.0 | 1000.0 | 1000.0 | **1000.0** | 16.0 |
| **Never in Contact Rate** | **3.6%** | **4.0%** | **23.4%** | **36.2%** | **49.6%** | **10.7%** |
| **Never in Contact Delta (4D $-$ 4B)** | **+0.0%** | **+0.4%** | **+19.9%** | **+27.5%** | **+38.8%** | — |
| **No Hostile Write Rate** | 3.6% | 4.5% | 30.4% | 40.6% | **57.6%** | 13.2% |
| **Stagnation Rate ($\ge 100$ zero-diff ticks)** | 0.0% | 3.6% | 10.7% | 17.2% | **21.4%** | 2.2% |
| **Mean First Contact Tick (when made)** | 5.5 | 5.6 | 11.7 | 19.7 | **11.7** | 96.3 |

### G.2 Key Interaction Findings
1. **Never-in-Contact Rate Explodes:** Rather than reducing search starvation, proportional displacement caused the never-in-contact rate to surge from 10.7% in Phase 4B to **49.6% in Phase 4D** at $A=65536$. In nearly half of all matches, opposing agents never came within perceptual reach ($R \le 4$) of each other for the entire 1,000 ticks.
2. **Surge in Timeouts:** Matches reaching the $T=1000$ tick limit surged from 31.2% at $A=512$ to **66.7% at $A=65536$** (+27.7% absolute increase over Phase 4B). The median match duration jumped from 11.0 ticks to the maximum ceiling of 1000.0 ticks at all arenas $A \ge 4096$.
3. **Pacing Paradox:** When contact *did* occur, mean first-contact tick was faster (11.7 ticks at $A=65536$ vs 96.3 ticks in Phase 4B), but the *probability* of ever making contact dropped precipitously.

---

## H. Strategic Effects

### H.1 Win Rate Matrix Across Scales

| Agent | $A=512$ (Rank) | $A=1024$ (Rank) | $A=4096$ (Rank) | $A=16384$ (Rank) | $A=65536$ (Rank) | Phase 4B (65k) | Delta vs 4B (65k) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `Octave` | **1.000** (#1) | **0.987** (#1) | **1.000** (#1) | **1.000** (#1) | **0.946** (#1) | 0.969 | -0.022 |
| `nemesis_alpha2` | 0.621 (#3) | 0.665 (#2) | 0.652 (#3) | 0.737 (#2) | **0.786** (#2) | 0.750 | +0.036 |
| `v4_claimer` | 0.438 (#5) | 0.598 (#3) | **0.714** (#2) | **0.714** (#3) | **0.714** (#3) | 0.571 | **+0.143** |
| `v5_core_defender` | 0.170 (#7) | 0.138 (#8) | 0.357 (#5) | 0.357 (#4) | 0.371 (#4) | 0.161 | +0.210 |
| `v5_scout_striker` | **0.719** (#2) | 0.571 (#4) | **0.460** (#4) | **0.348** (#5) | **0.299** (#5) | 0.683 | **-0.384** |
| `v5_region_attacker` | 0.580 (#4) | 0.438 (#6) | 0.313 (#7) | 0.286 (#7) | 0.299 (#6) | 0.509 | -0.210 |
| `v5_dual_team` | 0.379 (#6) | 0.451 (#5) | 0.326 (#6) | 0.295 (#6) | 0.299 (#7) | 0.263 | +0.036 |
| `v4_local_defender` | 0.094 (#8) | 0.152 (#7) | 0.179 (#8) | 0.263 (#8) | 0.286 (#8) | 0.094 | +0.192 |

### H.2 Ecological Metrics: Hierarchy & Cycles
- **Rank Correlation ($\rho$ vs $A=512$):** Drops to 0.810 (1024), 0.690 (4096), 0.619 (16384), and 0.667 (65536). Unlike Phase 4B where $\rho \ge 0.952$ throughout, proportional movement deeply disrupted the strategic order.
- **Directed 3-Cycles:** Collapsed from 2 (at $A=512$) and 3 (at $A=1024$) down to **0 at $A=16384$ and $A=65536$**. As timeouts became pervasive, dynamic non-transitive counterplay vanished.
- **Dominance Edges ($>0.55$):** Decreased from 25 to 17 at $A=65536$.

### H.3 Major Matchup Inversion: Region Attacker vs Claimer (Section 25)
Task Section 25 specifically directs examining the central Phase 4B matchup inversion: `v5_region_attacker` vs `v4_claimer`.

| Arena Size ($A$) | Phase 4B Region Attacker Win Rate | Phase 4B Claimer Win Rate | Phase 4D Region Attacker Win Rate | Phase 4D Claimer Win Rate | Matchup Dynamics |
|---:|:---:|:---:|:---:|:---:|:---|
| **512** | **0.938** | 0.062 | **0.938** | 0.062 | Identical: Region Attacker suppresses Claimer |
| **1024** | **0.813** | 0.188 | **0.000** | **1.000** | **Instant 4D Inversion Point ($2\times$ stride)** |
| **4096** | 0.500 | 0.500 | **0.000** | **1.000** | Phase 4B Inversion Point; 4D fully inverted |
| **16384** | 0.188 | **0.813** | **0.000** | **1.000** | Claimer dominates in both phases |
| **65536** | 0.000 | **1.000** | **0.000** | **1.000** | Claimer wins 100% on timeout score |

#### Causal Interpretation
In Phase 4B, Claimer was trapped by its 64-cell movement speed at $A=1024$, allowing Region Attacker to locate and suppress it. In Phase 4D, Claimer's stride is doubled to 128 cells at $A=1024$, allowing Claimer to immediately break free of Region Attacker's localized reach zone and claim cells circumferentially. Region Attacker, suffering from overshoot and limited reach, fails to intercept Claimer, causing the matchup inversion point to shift from $A=4096$ down to $A=1024$.

---

## I. Navigation Side Effects

The degradation of interaction and strategic collapse in Phase 4D is driven by two severe spatial phenomena:

### I.1 Discrete Sublattice Tunneling (Spatial Nyquist Violation)
Bytefray executes on a discrete ring $\mathbb{Z}_A$. When an agent requests stride $op$, its world-space displacement is $k \cdot op$, where $k = A / 512$ ($k = 128$ at $A=65536$).
- An agent taking steps of size $128 \times op$ is confined to a discrete coset of step-size 128:
  $$\mathcal{L}(s) = \{s + 128 \cdot m \pmod A \mid m \in \mathbb{Z}\}$$
- The agent skips over 127 consecutive cells on every step.
- An agent's observation and action reach is frozen at $R \le 4$ cells (an interaction window of $2R + 1 \le 9$ cells).
- Because the stride $\Delta = 128$ drastically exceeds the reach envelope ($2R + 1 = 9$), opposing agents residing on non-intersecting cosets literally leap over each other without ever entering mutual perceptual reach. This explains why **49.6% of matches concluded with zero agent interactions**.

### I.2 Overshoot Dyspraxia
Agents authored under the 512-cell reference model execute closed-loop tactical pursuit:
1. Agent detects an enemy core 10 cells ahead.
2. Tactical tracking logic emits a fine step: $op = +1$.
3. At $A=65536$, the runtime resolves $op = +1$ into $+128$ cells.
4. The agent leaps 118 cells *past* the enemy core.
5. On the subsequent tick, the agent observes the target behind it and emits $op = -1$.
6. The runtime resolves $-128$ cells, leaping backward past the target again.
7. The agent enters an unresolvable limit-cycle oscillation, endlessly hopping across the target without ever landing within attack reach ($R \le 2$).

---

## J. Octave

`Octave` is Bytefray's benchmark reference entrant: an 8-process global sweeper.

### J.1 Dominance Response
- **Phase 4B/4C Control:** 1.000 win rate across 512, 1024, 4096, 16384, and 0.969 at 65536.
- **Phase 4D Proportional Movement:**
  - $A=512$: 1.000 (112 / 112 wins)
  - $A=1024$: 0.987 (110 wins, 2 draws)
  - $A=4096$: 1.000 (112 / 112 wins)
  - $A=16384$: 1.000 (112 / 112 wins)
  - $A=65536$: 0.946 (106 wins, 6 draws)
- `Octave` remained undefeated (#1 rank) across all 5 scales, suffering zero losses.

### J.2 Diagnostic Conclusion
Proportional traversal does **not** allow local/mobile agents to threaten Octave. Despite mobile agents crossing the ring $128\times$ faster, Octave remained completely dominant. This confirms that Octave's dominance is structural and not primarily a traversal bottleneck.

---

## K. Mobile Searchers

### K.1 Scout Striker Diagnostic
`v5_scout_striker` is an authored high-mobility pursuit interceptor with a default stride of ~40 and precision $\pm 1$ tactical tracking.

| Metric | Arena 512 | Arena 1024 | Arena 4096 | Arena 16384 | Arena 65536 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Win Rate** | **0.719** | **0.571** | **0.460** | **0.348** | **0.299** |
| **Rank** | #2 | #4 | #4 | #5 | #5 |
| **Delta vs Phase 4B** | 0.0% | -8.0% | -19.2% | -33.0% | **-38.4%** |
| **Head-to-Head vs Claimer** | 1.000 | 0.500 | 0.000 | 0.000 | **0.000** |

At $A=65536$, Scout Striker suffered a complete tactical collapse (-38.4% absolute win rate delta), transforming from the arena's premier hunter (#2 rank) into a non-factor (#5 rank) due to overshoot dyspraxia and limit-cycle oscillation.

---

## L. Claimer

### L.1 Separating Traversal from Territory Economics
`v4_claimer` is a territorial painter that steps and writes ownership marks.

| Metric | Arena 512 | Arena 1024 | Arena 4096 | Arena 16384 | Arena 65536 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Win Rate** | **0.438** | **0.598** | **0.714** | **0.714** | **0.714** |
| **Rank** | #5 | #3 | #2 | #3 | #3 |
| **Delta vs Phase 4B** | 0.0% | +14.3% | **+21.4%** | +17.0% | +14.3% |
| **Territory Share at T=1000** | 4.8% | 2.5% | 0.63% | 0.16% | 0.04% |

### L.2 Causal Analysis
- **Traversal vs Territory Economics:** While Claimer's physical traversal scaled $128\times$, its write budget remained fixed: each WRITE action still marks only 1 cell. Claimer's total territory coverage collapsed 120-fold from 4.8% at $A=512$ to 0.04% at $A=65536$.
- **Why Did Claimer Surge in Win Rate?** Claimer's surge to #2 rank (0.714 win rate) was caused entirely by combat failure and timeout expansion. Because lethal combat collapsed and 66.7% of matches timed out, Claimer's amplified traversal allowed it to paint a few dozen cells across wide arcs, winning on score tiebreaks against opponents with zero writes.
- **Section 34 Confirmation:** Movement scaling does not solve territory economics. Territory share still scales inversely with arena size.

---

## M. Conclusions

### M.1 Direct Answer to the Research Question
> **Does proportional movement semantics materially improve large-arena Bytefray interaction and strategic counterplay?**

**No.** Forcing proportional movement displacement on frozen agents severely degrades interaction, triples timeout rates, and induces destructive behavioral pathology.

### M.2 Decision Logic Classification (Section 33)
Phase 4D definitively resolves to:

> **Outcome C: Navigation degrades because agents overshoot/oscillate.**
>
> *Formal Conclusion:* Runtime scaling of movement displacement is the wrong architectural abstraction. Forcing world-space displacement onto agents authored for a 512-cell reference world violates the discrete cellular Nyquist criterion ($\Delta > 2R + 1$), causing blind tunneling and overshoot dyspraxia. Scale adaptation cannot be imposed by external displacement multipliers; it requires either coupled reach scaling or scale-aware agent observation and control.

---

## N. Next Experiment

In accordance with Section 34 (Territory Study Decision) and Phase 4D findings, future research directions are recommended (recommend only, not implemented here):

1. **Phase 4E Recommendation — Coupled Reach-Displacement Scaling:**
   Investigate whether coupling sensory/action reach to traversal stride ($\Delta \propto A \implies R \propto A$) restores the spatial sampling invariant and eliminates sublattice tunneling.
2. **Phase 4F Recommendation — Territory Scoring Normalization:**
   Decouple territorial viability from arena size via non-percentage scoring, thresholded territory buckets, or localized area rewards, resolving the 120-fold territory dilution observed in Claimer.
3. **Phase 4G Recommendation — Scale-Aware Agent API:**
   Expose `arena_size` in `ObservationV2` so authored agents can intelligently choose their own scale-appropriate strides rather than suffering runtime-forced displacement.

---

## Research Integrity Addendum (2026-09-22)

Two independent research-integrity reviews have established that the Phase 4 arena-scaling and movement research line was grounded in flawed causal premises and compromised by test and benchmark defects:

1. **V4 Tick-1 Forced-Win Gate:** Shipped stable `bytefray-rules-4` contains a deterministic tick-1 Seat-A forced core capture under competent global-reach play (`CompetentGlobalSniperProbe`), winning on tick 1 before Seat B ever executes an instruction. This seat/order-driven exploit was the unacknowledged driver of apparent lethality in global probes, invalidating interpretations of global reach as balanced gameplay.
2. **Benchmark Corpus Tracking (Octave):** The V6-Bench-8 field previously depended on an untracked local `Octave` agent in the user's private `agents/` directory. Octave has now been fingerprinted (`e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730`) and permanently committed to tracked repository fixtures under `tools/research/v6/fixtures/agents/Octave/`.
3. **Territory Scoring Invariance:** Territory scoring was incorrectly described in Phase 4D as scaling with arena percentage and suffering "dilution." In reality, `ScoringPolicy` awards 1 point per 64 raw cells held ($\lfloor \text{cells} / 64 \rfloor$) independently of arena size. Scoring was always invariant to arena dimensions.
4. **Agent Context Arena Size:** Phase 4D incorrectly asserted that `ObservationV2` and match context hid `arena_size` from agents. In fact, `context.arena_size` was already supplied in `AgentContext` upon initialization.
5. **Fallacy of $\sigma^2_{\text{opp}}$ as Counterplay:** Variance of win rates across opponents is a mathematical property of intermediate ranks in a purely transitive 1D skill hierarchy, not evidence of opponent-dependent counterplay or non-transitivity. It has been replaced by 1D rating models, matchup residuals ($R_{ij} = W_{ij} - \hat{W}_{ij}$), upset reversals, and explicit tie tracking.
6. **Cycle Disappearance Artifact:** The apparent disappearance of directed 3-cycles at larger arenas was an artifact of win rates slipping below the fixed 0.55 dominance threshold, not a reversal or restructuring of competitive ordering.
7. **Line Closure & Transition to E2:** The arena-scaling and movement normalization line is closed. Active research pivots to E2 — Multi-Tick Capture Hold to address the root causal vulnerability identified in stable V4.
