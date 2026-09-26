# Bytefray V6 Phase 4A — Gameplay Research Methodology Design

**Status:** Design and Specification  
**Branch:** `v6-research`  
**Anchor Baseline:** `d6bbe47` (`fix(v6): harden evaluation research integrity`)  
**Ruleset Under Control:** `bytefray-rules-4` (stable, immutable control)  
**Target Research Deliverable:** Experimental methodology, benchmark suite, and scaling roadmap  

---

## 1. Research Goals and Problem Statement

### 1.1 The Core Strategic Challenge
Across V2, V3, V4, and V5 research cycles, empirical evaluations demonstrated that under fixed spatial conditions (specifically circular arenas of 512 cells with deterministic placement or fixed reach), agent performance frequently converges toward a **strictly transitive hierarchy**:

$$\text{Agent}_1 \succ \text{Agent}_2 \succ \text{Agent}_3 \succ \dots \succ \text{Agent}_N$$

In this regime, match outcomes are overwhelmingly dominated by an agent's **intrinsic execution speed and race optimization** rather than opponent-specific counterplay:
1. In V2 Alpha 10 (`docs/archive/v2/V2_0_ALPHA10_STRATEGIC_ECOLOGY.md`), pure expansion (`claimer`) achieved a 98.4% 1v1 win rate across the entire field because territorial claiming outpaced reactive hunting regardless of scheduler orientation or placement. In contrast, specialized core tracking (`core_tracker`) won only 10.0% of 1v1 matches and 2.4% combined despite achieving the highest mean alive-ticks (197.9/200 ticks), as search cost acted as an uncompensated score tax. This produced an approximate **98-point performance spread** between pure claiming throughput and baseline floor/specialized tracking, demonstrating that territory dominance erased combat counterplay.
2. In the V3 research program:
   - **Action Density Grid** (`docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md`): Established the dimensionless action-density parameter $S = \frac{\text{instr\_per\_tick} \times \text{ticks}}{\text{arena\_size}}$ (sweeps per entrant) and aggregate pressure $P = \text{entrants} \times S$. The study demonstrated constant-density diagonals where occupancy remained stable (73–84%) across arenas from 1,024 to 65,536 cells, but critically proved that when $S \le 0.098$, matches suffered severe interaction starvation where the tick limit expired without decisive contact.
   - **The Bulldozer Effect** (`docs/archive/v3/V3_PHASE2_LOCALITY_FEASIBILITY.md`): Testing bounded locality ($R \in [8, 256]$ at arena 4096) discovered that bounded reach forced contiguous claiming ($1\text{ action/cell} + 1/(R+1)\text{ move overhead}$), causing blind expanders to sweep solid bands that incidentally obliterated stationary 8-cell cores (`local_claimer` caused 88.9% of captures at $R=8$). Search collapsed into "expansion minus 1/3 throughput spent reading", while defense suffered a 41.5% movement budget penalty, collapsing defense win rates from 47.4% down to 0.0%. Bounded reach manufactured a universal bulldozer rather than strategic diversity.
3. In V4 Alpha 1 baseline (`docs/archive/v4/V4_ALPHA2_PHASE4_GAMEPLAY_STUDY.md`), two agents (`Nemesis` and `Hydra`) achieved 100.0% and 80.1% win rates respectively by exploiting fixed opposite placement (`own_core + arena_size // 2`) with zero movement (`0` MOVE actions recorded).
4. In V4 Pre-RC evaluation at arena size 4096 (`docs/archive/v4/V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md`), maximum declared reach ($\text{arena\_size} // 2$) won 54.7% against 2.3% for short reach, creating a 52-point performance spread derived entirely from a single zero-cost declaration.
5. In V5 RC1 adversarial investigation (`docs/archive/v5/V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md`), the adversarial agent `Octave` demonstrated that unbounded reach, ownership-based core localization from `ObservationV2.previous_read_owner`, and last-mover atomic 8-cell burst capture can dismantle regional defense without engaging in spatial navigation.

Where non-transitive interactions or cycles have appeared, they have been narrow and fragile (such as Local Hunter defeating Claimer but suffering permanent disrupt-lock against Nemesis). Under current stable rules, Bytefray lacks durable strategic counterplay (e.g. Rock-Paper-Scissors dynamics or Greed-Rush-Defense economic triangles).

### 1.2 The V6 Research Objective
The goal of V6 gameplay research is to expand Bytefray's strategic dimensionality so that agent effectiveness becomes genuinely **opponent-dependent**.

Before introducing speculative gameplay mechanics (such as dynamic economies, fog of war, special cells, or shrinking fields), the primary experimental question must be answered:

> **What happens to current Bytefray gameplay as arena scale increases dramatically while gameplay rules remain otherwise unchanged?**

This document establishes the experimental methodology, mathematical rigor, benchmark controls, and reproducibility contracts required to conduct this investigation systematically.

---

## 2. Stable Control Definition

### 2.1 The Immutable Baseline: `bytefray-rules-4`
The scientific integrity of V6 research depends on maintaining an immutable control. The production ruleset **`bytefray-rules-4`** is and remains that control:

1. **Semantic Specification:** Defined in [`engine/src/battle_engine/ruleset_policy.py`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/ruleset_policy.py#L364-L374):
   - `ruleset_id`: `"bytefray-rules-4"` (`rules.BYTEFRAY_RULESET_ID`)
   - `supported_runtime_kinds`: `frozenset({"python"})`
   - `supported_python_api_versions`: `frozenset({2})`
   - `scheduler_mode`: `"chunked"`
   - `scheduler_chunk_size`: `2`
   - `scheduler_rotate_start`: `True`
   - `core_placement`: `"seeded"` (seed-derived start positions with $\ge 64$ cells separation)
   - `process_selection`: `"round_robin"`
   - `quota`: $Q = 8$ instructions per entrant per tick
   - `core_size`: 8 contiguous cells
   - `reach`: declared in $[1, \text{arena\_size} - 1]$, uncapped, zero cost
2. **Methodology Lock:** Evaluated strictly under the stable V4 evaluation methodology:
   - Arena size: **Pinned to 512 cells** (`STANDARD_V4_ARENA_SIZE = 512`, [`evaluation_contracts.py:192`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/evaluation_contracts.py#L192)).
   - Seeds: **Pinned to 8 deterministic seeds** (`STANDARD_V4_SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)`, [`evaluation_contracts.py:191`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/evaluation_contracts.py#L191)).
   - Alignment mode: `"ruleset_v4_seeded_placements"` (`IDENTITY_VERSION = 7`, `SCHEMA_VERSION = 7`).
   - Strict validation: `EvaluationService._validate` ([`evaluation_service.py:824-833`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/evaluation_service.py#L824-L833)) rejects any evaluation request specifying `--arena-size` differing from 512 for `bytefray-rules-4`.

### 2.2 Invariant Guarantees
- Stable V4 code paths will not be modified or reinterpreted as variable-arena rulesets.
- Historical golden fixtures (`test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`) remain permanent regression guards.
- All experimental variations will run under distinct, explicitly versioned research identities.

---

## 3. Benchmark Agent Methodology

### 3.1 Requirements for the Benchmark Suite
To measure strategic interactions rather than simply crowning a dominant racer, the benchmark suite must satisfy four criteria:
1. **Behavioral Diversity:** Must span aggressive snipers, mobile searchers, swarm coordinators, territorial expanders, and stationary defenders.
2. **Contract Consistency:** Every agent must run under **Agent API v2** (`battle_engine.agent_api.AgentV2`). VM and API v1 agents retired in V6 Phase 2B.12 are excluded from live benchmarking.
3. **Performance Stratification:** Must include top-tier competitors, middle-tier specialists, and baseline controls.
4. **Version Immutability:** Agents must be frozen by content digest so that future agent edits do not invalidate historical experimental comparisons.

### 3.2 Inventory of Candidate Agents

| Agent Name | Archetype / Role | Process Config | Primary Strategic Mechanism | Historical Performance Status |
|---|---|---|---|---|
| **`Octave`** | Adversarial Global Sniper | 4 processes, dynamic shares | Dispersed anchoring, ownership-based core discovery (`previous_read_owner`), last-mover atomic burst | Dominant adversarial agent (V5 RC1) |
| **`nemesis_alpha2`** | Seeded Long-Range Attacker | 3 processes (siege, disruptor, guardian) | Scans sightings and `previous_read_owner` for core signatures; persistent siege sweep | Top-tier competitor at arena 512 and 4096 |
| **`hydra_alpha2`** | Multi-Process Team Cannon | 4 processes (rover, interceptor, siege, sentinel) | Mobile rover sweeps while static artillery batteries attack acquired coordinates | Strong competitor, sensitive to round-robin order |
| **`v5_scout_striker`** | Mobile Search-and-Strike | 1 process | Bounded reach, systematic traversal, memory of last contact, aggressive closing | Active pursuit exemplar; beats stationary/passive agents |
| **`v5_region_attacker`** | Regional Area Suppressor | 1 process | Presses core-sized window around enemy sightings | Effective against clustered cores; vulnerable to dispersal |
| **`v5_dual_team`** | Coordinated Two-Process Unit | 2 processes (raider, core_keeper) | Raider explores and attacks; keeper defends core cells | Balanced team benchmark; tests intra-entrant quota sharing |
| **`v4_claimer`** | Rapid Territorial Expander | 1 process | Pure WRITE expansion; ignores combat; maximizes territory score | Dominates passive matches; easily killed if core is found |
| **`v4_quorum`** | Coordinated Swarm | 6 processes | Decentralized mailbox communication; distributed sweeping | High process overhead; tests scheduler and quota redistribution |
| **`v5_core_defender`** | Reactive Core Repairer | 1 process | High-frequency READ inspection of own core cells; immediate rewrite | Resilient against blind sweeps; powerless if enemy is undetected |
| **`v4_local_defender`** | Passive Sentry Control | 1 process | Static inspection and localized writes | Weak control (0% baseline win rate; floor control) |

### 3.3 The Frozen Benchmark Suite (V6-Bench-8)
For Phase 4 research, a standard 8-agent field (**`V6-Bench-8`**) is selected:
1. **`Octave`** (Adversarial / Global Precision)
2. **`nemesis_alpha2`** (Artillery / Core Hunter)
3. **`v5_scout_striker`** (Local Mobile Pursuit)
4. **`v5_region_attacker`** (Regional Offensive)
5. **`v5_dual_team`** (Two-Process Team)
6. **`v4_claimer`** (Territorial Expansion)
7. **`v5_core_defender`** (Reactive Defense)
8. **`v4_local_defender`** (Floor Control)

*Freezing & Provenance:* Each agent's directory snapshot is content-addressed via `battle_engine.agent_revisions.agent_revision_fingerprint` (which computes a versioned SHA-256 digest over tree entries and omissions) and `battle_engine.agent_revisions.agent_revision_id` (producing the canonical `agent-revision_<64-char-hex>` store identifier). Experimental manifests record the exact `agent_revision_id` for every entrant.

---

## 4. Experimental Variables and Arena Scaling

### 4.1 Logarithmic Arena Progression
To study spatial scaling, an exponential progression of circular arena sizes is defined:

$$A \in \{512, 1024, 4096, 16384, 65536\}$$

- **$A = 512$:** Production baseline (Designer default, stable V4 evaluation; V3 Action Density $S = 15.625$).
- **$A = 1024$:** Immediate spatial expansion ($2\times$; $S = 7.8125$).
- **$A = 4096$:** CLI default (`Config.arena_size`); regime where reach dominance begins to flatten local play ($S = 1.953$).
- **$A = 16384$:** Deep spatial regime ($32\times$ baseline); traversal time becomes a severe constraint ($S = 0.488$).
- **$A = 65536$:** Maximum architectural boundary ($128\times$ baseline); tests circular VM limits and memory-sparsity assumptions ($S = 0.122$, approaching V3 Phase 1's $S \le 0.098$ interaction-starved threshold).

### 4.2 Two Distinct Scaling Experiments

```text
+-----------------------------------------------------------------------+
|                       EXPERIMENT A: RAW SCALING                       |
|  Vary Arena Size (512 -> 65,536). Keep ALL other constants fixed.     |
|  - Reach: as declared by agent (uncapped, legal up to A - 1)          |
|  - Max Move Delta: 64 cells / MOVE action (process_runtime.py:632)    |
|  - Max Move Speed: up to 512 cells / tick (quota Q = 8)               |
|  - Placement Min Separation: 64 cells                                 |
|  - Core Size: 8 cells                                                 |
|  - Quota: Q = 8 instructions / entrant / tick                         |
|  - Tick Limit: 1,000 ticks                                            |
|  Exposes: Natural degradation of mechanics when the world grows.      |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|               EXPERIMENT B: SCALE-NORMALIZED GEOMETRY                 |
|  Scale spatial geometry coherently with arena size:                   |
|  - Placement Separation: scaled proportionally (min_sep = A / 8)      |
|  - Locality Reach: bounded ladders (R in {64, 256, sqrt(A), A / 8})   |
|  - Movement Range: evaluated under scaled max_move_delta (candidates  |
|    include A/8 and sqrt(A)*2, both anchored to equal 64 at A=512)     |
|  - Tick Horizon: evaluated under scale-aware time (Linear T~A primary;|
|    Fixed T=1000 shared control; Square-Root/Log as cost fallbacks)    |
|  Exposes: Separates inherent geometry changes from 512-tuned constants|
|  Guards: Checks for the V3 Phase 2 "bulldozer effect" under locality. |
+-----------------------------------------------------------------------+
```

#### Experiment A — Raw Scaling
- **Controlled Invariants:**
  - Action quota: $Q = 8$ instructions per entrant per tick
  - Core size: 8 cells
  - Minimum placement separation: 64 cells
  - Maximum move delta: `max_move_delta = 64` cells per `MOVE` action ([`process_runtime.py:632, 1184`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/process_runtime.py#L632))
  - Maximum declared reach: legal up to $A - 1$ (uncapped, zero cost)
  - Match duration: 1,000 ticks
- **Scientific Purpose:** Expose what happens naturally to current mechanics when spatial boundaries expand without compensation.
  - Does global reach turn into an instant teleporting weapon across 65,536 cells?
  - Do local agents ever make mutual contact before the 1,000-tick timeout?
  - Does the draw/timeout rate approach 100% for non-global agents?
  - **Surprising or poor results under raw scaling are evidence, not failures.** A high timeout rate, a collapsed leaderboard, or degenerate agent behavior at large $A$ is exactly the data Experiment A exists to produce. It must be recorded and analyzed as-is; it does not by itself justify skipping ahead to Experiment B's normalized geometry, and Experiment B's normalization candidates (§4.2 below) must not be substituted into Experiment A's controlled invariants to "fix" an unwelcome result.
  - **Stride & Traversal Dynamics:** At $A = 512$, a single 64-cell MOVE covers 12.5% of the arena circumference, and an agent dedicating all 8 actions to movement can traverse the entire arena in a single tick ($8 \times 64 = 512$). At $A = 65,536$, however, a 64-cell MOVE covers only $\frac{64}{65536} \approx 0.098\%$ ($1/1024$) of the arena. Traversing half the arena ($32,768$ cells) requires at least $\lceil 32,768 / 64 \rceil = 512$ dedicated `MOVE` actions, or 64 dedicated ticks of pure movement (with zero READ/WRITE actions). For active searchers that interleave sensing and moving (e.g. 1 READ per 1 MOVE), traversal takes $\ge 128$ ticks.

#### Experiment B — Scale-Normalized Geometry
Conducted after Experiment A to separate "large arenas inherently break gameplay" from "constants were tuned for 512 cells."
- **Candidate Scaling Parameters:**
  1. **Placement Separation:** Scale minimum separation proportionally:
     $$\text{min\_sep}(A) = \max\left(64, \left\lfloor \frac{A}{8} \right\rfloor\right)$$
     **Verified (Phase 4A.1 audit):** This satisfies the control-equivalence anchor invariant $f(512) = 64$ exactly ($\lfloor 512/8 \rfloor = 64$), scales as a constant 12.5% of arena size thereafter, and remains feasible at $A=65536$ (min_sep of 8,192 cells is well within the $A/2 = 32,768$ maximum possible separation between the two entrants placed per match) and well above `core_size` (8 cells) at every tested scale. No correction needed. Prevents two entrants in a 65,536 arena from spawning 64 cells apart (an artificial 0.1% separation).
  2. **Movement Stride / Budget:** If `max_move_delta` remains 64, relative spatial traversal slows by $128\times$. Any scale-normalized candidate intended to be control-equivalent must satisfy the anchor invariant $f(512) = 64$ (the raw-scaling control value at the base arena). Candidates satisfying this invariant:
     - **Proportional (primary):** $\text{max\_move\_delta}(A) = \max\left(64, \left\lfloor \frac{A}{8} \right\rfloor\right)$ — equivalently $64 \times (A/512)$ — preserves the control's exact 12.5%-of-arena-per-`MOVE` ratio at every scale.
     - **Sub-linear (secondary):** $\text{max\_move\_delta}(A) = \max\left(64, \lfloor \sqrt{A} \times 2 \rfloor\right)$ — the outer `max(64, ...)` floor is load-bearing here: $\lfloor\sqrt{512}\times 2\rfloor = 45 < 64$, so without the floor this candidate would *not* reproduce the control at $A=512$.

     **Correction (Phase 4A.1 audit):** An earlier candidate, $\lfloor A / 64 \rfloor$ (without a floor), does **not** satisfy the anchor invariant — $\lfloor 512 / 64 \rfloor = 8 \ne 64$ — and must not be used as a scale-normalized `max_move_delta` formula. It has been removed from the candidate list above.
  3. **Reach Normalization:** Investigate capped reach rungs ($R \in \{64, 256, \sqrt{A}, A/8\}$) to evaluate local perception.
     - *Critical Guard:* Must evaluate whether bounded reach triggers the V3 Phase 2 "bulldozer effect" (where contiguous claiming incidentally destroys cores while search collapses into slow expansion and defense is crippled by movement overhead).

---

## 5. Tick Horizon Strategy

In scaling experiments, match duration ($T_{\max}$) cannot remain an unexamined constant. Two distinct comparative regimes are established:

### 5.1 Fixed-Time Horizon ($T_{\max} = 1000$)
- Fixed computational budget of 1,000 ticks across all arena sizes ($A \in \{512 \dots 65536\}$).
- **Hypothesis:** While theoretical maximum move speed is $v_{\max} = 8 \times 64 = 512\text{ cells/tick}$ (pure blind movement), realistic search agents that interleave inspection and navigation have an effective pursuit velocity of $v_{\text{eff}} \approx 8 - 32\text{ cells/tick}$. The sweep coverage ratio directly reflects the V3 action density $S = \frac{Q \cdot T_{\max}}{A} = \frac{8000}{A}$:
  - At $A = 512$, $S = 15.6$ (dense interaction; $P(\text{contact}) \approx 1.0$).
  - At $A = 4096$, $S = 1.95$ (moderate density; $P(\text{contact}) \approx 0.5$).
  - At $A = 65536$, $S = 0.122$ (deep starvation; $P(\text{contact}) \approx 0.12$).
  Non-global agents will experience catastrophic timeout inflation as $S \ll 1$.

  **Verified (Phase 4A.1 audit):** This $S = Q \cdot T_{\max} / A = 8000/A$ formula and the five listed values (15.625, 7.8125, 1.953, 0.488, 0.122) match the historical V3 definition exactly — [`docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md:56`](file:///d:/Projects/BATTLE2/docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md#L56): "`S = (instr_per_tick x ticks) / arena_size`" — with `instr_per_tick = Q = 8` and `ticks = T_max = 1000`. No correction is required to the formula or the values in §4.1 or here.

### 5.2 Scale-Aware Time Horizon ($T_{\max}(A)$)
Four scaling models are evaluated:

| Model | Formula | $A=512$ | $A=1024$ | $A=4096$ | $A=16384$ | $A=65536$ | Rationale / Computational Feasibility |
|---|---|---:|---:|---:|---:|---:|---|
| **Linear** | $1000 \times (A / 512)$ | 1,000 | 2,000 | 8,000 | 32,000 | 128,000 | Directly traversal-normalized: preserves the same ticks-per-arena-cell ratio the control has at 512, matching Experiment A's own stride/traversal accounting (§4.2). **Prohibitively expensive** at 65k (128k ticks/match). |
| **Square-Root** | $1000 \times \sqrt{A / 512}$ | 1,000 | 1,414 | 2,828 | 5,657 | 11,314 | A sub-linear compromise between Fixed and Linear cost; computationally feasible at all five sizes. |
| **Logarithmic** | $1000 \times [1 + \log_2(A / 512)]$ | 1,000 | 2,000 | 4,000 | 6,000 | 8,000 | Moderate expansion; tests whether information scaling suffices without linear inflation. |
| **Fixed Control** | $1000$ | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | Pure computational equality baseline; the horizon already used, unchanged, throughout Experiment A. |

**Correction (Phase 4A.1 audit):** The Square-Root row was previously justified as matching "2D diffusive search and radial expansion bounds." That rationale does not apply to this engine: [`docs/RULES.md:62`](file:///d:/Projects/BATTLE2/docs/RULES.md#L62) defines the arena as a **circular, one-dimensional byte array**, not a 2D spatial field, and no V2/V3/V4/V5 archive document models search as 2D diffusion. The formula and values above are unchanged (the arithmetic was already correct), but the justification is corrected here to avoid misleading Phase 4B's interpretation.

**Methodology Recommendation:** Experiment A continues to run under **Fixed Control ($T = 1000$)** to isolate spatial effects; this is unchanged. For Experiment B, the primary traversal-normalized candidate is **Linear Scaling ($T \propto A$)**, because it is the horizon that is actually derived from this engine's 1D circular traversal mathematics (§4.2's own stride/traversal accounting: covering half the arena at fixed stride costs $\Theta(A)$ actions, not $\Theta(\sqrt{A})$). Experiment B should test **both**:
1. **Fixed Control ($T=1000$)**, shared with Experiment A, as the no-compensation baseline, and
2. **Linear ($T \propto A$)**, as the traversal-normalized candidate, understanding that its 65,536-cell cost (128,000 ticks/match) may be computationally prohibitive for the full Tier 2 sweep.

**Square-Root is retained only as a fallback candidate**, to be exercised specifically if Linear proves too expensive during Phase 4B smoke qualification — it is a practical compromise on cost, not a physically-motivated model of this engine's search dynamics. Logarithmic remains available as a third fallback for the same reason. Phase 4B should benchmark Linear's actual wall-clock cost at $A=65536$ during smoke qualification before deciding whether the full Tier 2 sweep can afford it, or must fall back to Square-Root/Logarithmic.

---

## 6. Comprehensive Metrics Inventory

Metrics are categorized by availability into three tiers:

```text
+--------------------------------------------------------------------------+
| TIER 1: ALREADY AVAILABLE                                                |
| (NativeMatchResult, ResultSummary, NativeAgentResult)                    |
| - Outcome: winner, win_mode, ticks_run, score, alive, kills, deaths      |
| - Termination: termination_reason (LAST_AGENT_STANDING, TICK_LIMIT, etc.)|
| - Activity: alive_ticks, cpu_total, mem_writes                           |
| - Territory: territory_last, territory_max, territory_avg, territory_pct |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| TIER 2: REPLAY-DERIVABLE (POST-HOC ANALYSIS)                             |
| (Replay Schema 4: TickSnapshot, processes, memory_diffs, events)         |
| - First Contact Tick: min tick where dist(anchor_A, anchor_B) <= reach   |
| - First Hostile Interaction: tick of first WRITE to enemy-owned cell     |
| - Traversal Displacement: sum of circ_dist(anchor(t), anchor(t-1))       |
| - Spatial Dispersion: mean pairwise circular distance between processes  |
| - Stagnation Runs: consecutive ticks with zero memory diffs              |
| - Unique Footprint: count of unique addresses written per entrant        |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| TIER 3: REQUIRES NEW INSTRUMENTATION                                     |
| (Engine / Telemetry Extensions)                                          |
| - Sensory Disclosure Events: tick when core_base entered opponent reach  |
| - Action Budget Efficiency: breakdown of MOVE vs WRITE vs READ vs IDLE   |
| - Wasted Quota: count of rejected actions (e.g. WRITE outside reach)     |
| - Disruption Pressure: fraction of tick quota lost to active disruption  |
+--------------------------------------------------------------------------+
```

### 6.1 Detail on Key Research Metrics
1. **Time to First Meaningful Contact ($T_{\text{contact}}$):** The earliest tick at which either entrant's process senses an opponent anchor or writes to an opponent's cell.
2. **Contact-to-Kill Latency ($\Delta T_{\text{kill}} = T_{\text{kill}} - T_{\text{contact}}$):** Differentiates instantaneous snipes from protracted tactical engagements.
3. **Spatial Efficiency Ratio ($\eta_{\text{spatial}}$):**
   $$\eta_{\text{spatial}} = \frac{\text{Unique Cells Written}}{\text{Total Memory Writes}}$$
   Measures whether an agent explores new space ($\eta \to 1$) or repeatedly bombards a static window ($\eta \to 0$).
4. **Dispersal Index ($D_{\text{process}}$):** For multi-process entrants, the mean circular separation of their active anchors.

### 6.2 Tier 2 Feasibility Verification (Phase 4A.1 audit)

Every Tier 2 metric was checked against [`docs/REPLAY_SCHEMA.md`](file:///d:/Projects/BATTLE2/docs/REPLAY_SCHEMA.md)'s actual Schema 4 field list (`processes[].anchor`, `processes[].reach`, `processes[].disrupted`, `memory_diffs[].{address,length,owner,values}`, `events`). All six are **directly replay-derivable** from Schema 4 alone, with two clarifications:

- **First Hostile Interaction** ("first WRITE to enemy-owned cell") requires a full linear reconstruction pass (per "Memory reconstruction" in `REPLAY_SCHEMA.md`) to know who owned a cell *before* a given write, not a single-field lookup — still purely replay data, no additional metadata needed.
- **Traversal Displacement** must use circular (modular) distance, not raw `abs(anchor(t) - anchor(t-1))` — corrected in the Tier 2 table above. A process whose anchor moves from address 511 to address 0 in a 512-cell arena has traversed 1 cell, not 511; the un-corrected formula would silently overcount every wraparound step.

No Tier 2 metric requires reclassification to Tier 3.

---

## 7. Operational Definition of Stagnation and Loop Behavior

### 7.1 The Stagnation Problem and Historical Grounding
Matches that reach the tick limit without decisive outcome often exhibit degenerate dynamics where "nothing interesting is happening." Prior research provides vital grounding:
1. **Low-Density Interaction Starvation:** In V3 Phase 1 (`docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md`), conditions with low action density ($S \le 0.098$) consistently ran to full duration ($T_{\max} = 400$) with zero early terminations, proving that low action-to-space ratios starve interaction by construction.
2. **False Activity / The Bulldozer Effect:** In V3 Phase 2 (`docs/archive/v3/V3_PHASE2_LOCALITY_FEASIBILITY.md`), naive write-activity counts failed to detect strategic stagnation: blind contiguous expanders (`local_claimer`) produced high memory-diff rates while executing zero combat or targeting logic.

To analyze non-resolutions quantitatively, stagnation and activity must be formally operationalized.

### 7.2 Formal Stagnation Criteria
A match state is defined as entering a **Stagnation State** if, over a sliding window of $W = 100$ consecutive ticks ($[t - W, t]$), any of the following conditions hold:

1. **Zero State Mutation:**
   $$\sum_{k = t - W}^{t} |\text{memory\_diffs}(k)| = 0$$
   Neither entrant has executed a successful WRITE anywhere in the arena.
2. **Disjoint Non-Interaction:**
   $$\forall p_A \in \text{Processes}_A, p_B \in \text{Processes}_B, \quad \text{dist}_{\text{circ}}(\text{anchor}(p_A), \text{anchor}(p_B)) > \text{reach}(p_A) + \text{reach}(p_B)$$
   Entrants are operating in mutually isolated sectors with zero probability of sensing or striking each other, reproducing the interaction starvation characterized in V3 Phase 1.
3. **Deterministic Periodic Loop:**
   The state hash sequence $H(t) = \text{hash}(\text{memory\_diffs}(t), \text{anchors}(t))$ exhibits a periodic recurrence:
   $$H(t) = H(t - p) \quad \text{for period } p \le 16, \quad \forall t \in [t_0, t_0 + W]$$
4. **Permanent Disruption Lock:**
   A single-process agent remains disrupted for $W$ consecutive ticks ($\text{disrupted} == \text{True}$) while the disruptor makes no progress toward capturing the core.

**Feasibility (Phase 4A.1 audit):** Criteria 1–3 are computable from Schema 4 replay data alone (`memory_diffs`, `processes[].anchor`, `processes[].reach`). Criterion 4 additionally needs the defending entrant's core address range to test "progress toward capturing the core." That range is not itself a per-tick replay field; it must be derived from the entrant's seeded start coordinate, which is Tier 1 data already carried in `NativeAgentResult`/`result.json` metadata (`match_service.py`'s `entrant.start`, combined with `core_addresses(start, arena_size)`). This criterion is therefore **computable now**, but only by combining the replay stream with existing Tier 1 result metadata — it does not require new instrumentation. Implementers should note that current metadata omits the `start` key entirely when it equals `0` (`match_service.py:864-865`); a missing key must be treated as `start = 0`, not as "unknown."

### 7.3 Diagnostic Classification
When a match terminates by `TICK_LIMIT`, the post-hoc analyzer classifies the non-resolution into:
- **Active Contest:** Frequent core overwrites, mutual combat, high territorial flux, but clock expired before complete 8-cell capture.
- **Incidental Bulldozer Sweep:** High write throughput and territory accumulation without mutual combat or directed search; an expander sweeps contiguous memory without opponent engagement (V3 Phase 2 failure mode).
- **Search Exhaustion:** Agents actively moved and searched, but arena scale and low action density ($S \ll 1$) prevented mutual contact before clock expired (V3 Phase 1 starvation).
- **Spatial Separation:** Agents stayed stationary in disjoint areas; no interaction attempted.
- **Mutual Deadlock:** Both agents engaged at close range, but repair rate matched attack rate perfectly (e.g. Core Defender vs weak attacker).
- **Periodic Loop:** Deterministic execution trapped in a cyclic state.

---

## 8. Matchup Dependence and Counterplay Analysis

### 8.1 Distinguishing Transitivity from Counterplay
Let $M \in \mathbb{R}^{N \times N}$ be the pairwise win-rate matrix across the $N$ benchmark agents, where $M_{ij}$ is the win rate of Agent $i$ against Agent $j$ (averaged over both orientations and all seeds).

```text
TRANSITIVE LADDER (Dominance)          COUNTERPLAY (Non-Transitive Cycle)
        A                                      A
       / \                                    ^ \
      v   v                                  /   v
     B --> C                                C <-- B
A > B, B > C, A > C                    A beats B, B beats C, C beats A
Kendall's W -> 1.0                     Kendall's W << 1.0, 3-cycles present
```

### 8.2 Quantitative Measures
1. **Transitivity Index ($T_{\text{tourn}}$):** Computed via Landau's transitivity index or the count of transitive triples vs cyclic triples in the tournament graph.
   - Let a directed edge exist from $i \to j$ if $M_{ij} > 0.55$. **This is a practical dominance threshold, not a statistically significant one** — Tier 2's 16 matches per pairing (8 seeds x 2 orientations) cannot support a "$p < 0.05$" claim at this effect size: a two-sided exact binomial test of 0.55 vs. a null of 0.5 needs several hundred trials per pairing to reach $p < 0.05$, not 16 (Tier 3's 32 per pairing is still far short). An earlier draft of this document attached "($p < 0.05$)" to this threshold; that annotation is incorrect for the planned sample sizes and has been removed. If a statistically validated edge is wanted instead of the heuristic 0.55 cut, compute a per-pairing exact binomial test (or Wilson confidence interval) against $p_0 = 0.5$ using the actual win/loss counts, and report the interval alongside the heuristic threshold rather than substituting for it.
   - Count directed 3-cycles: $i \to j \to k \to i$.
   - A healthy game exhibits non-zero 3-cycles. A purely degenerate race yields exactly 0 cycles.
2. **Opponent-Conditioned Performance Variance ($\sigma_{\text{opp}}^2$):**
   For Agent $i$, variance across opponents:
   $$\sigma_{\text{opp}}^2(i) = \frac{1}{N - 1} \sum_{j \ne i} \left(M_{ij} - \bar{M}_i\right)^2$$
   - Low variance: Agent $i$ performs identically regardless of who it faces (flat dominance or flat weakness).
   - High variance: Agent $i$'s success strongly depends on the opponent's strategy (evidence of specialized counterplay).
3. **Rank Inversion Rate across Scales:**
   Measure how the Spearman rank correlation $\rho_s(A_1, A_2)$ of the benchmark leaderboard changes between $A = 512$ and $A = 65536$. A low correlation indicates that spatial scale disrupts the baseline hierarchy.

---

## 9. Reproducibility and Identity Contract

### 9.1 The Research Identity Invariant
Every research match and evaluation must be **bit-for-bit reproducible**. Determinism must derive entirely from recorded seeds and immutable policy specifications.

### 9.2 Identity-Bearing Attributes
To prevent identity collisions (such as the scheduler collision resolved in commit `d6bbe47`), the following tuple must uniquely determine the canonical match identity (`match_id`):

$$\text{MatchIdentity} = \langle \text{RulesetID}, A, S, \text{Geometry}, \text{Scheduler}, \text{SpatialBounds}, \text{Quota}, T_{\max}, \text{EntrantDigests} \rangle$$

1. **`ruleset_id`:** Explicit research ruleset identifier (e.g. `bytefray-rules-6-research-scale`).
2. **`arena_size` ($A$):** Explicit integer cell count.
3. **`seed` ($S$):** Integer PRNG seed.
4. **`placement_geometry`:** Name of placement algorithm (`seeded`, `proportional_seeded`) and resolved coordinate tuple.
5. **`scheduler_policy`:** Mode (`chunked`), chunk size ($K=2$), rotation (`rotate_start=True`), and process selection (`round_robin`).
6. **`quota` ($Q$):** Base instruction budget per entrant.
7. **`tick_limit` ($T_{\max}$):** Horizon cap.
8. **`entrant_digests`:** SHA-256 digests of agent code (`source_digest`) and parameters.

### 9.3 Artifact Self-Sufficiency Principle
**Generator Policy vs Realized Environment:**
Relying solely on `(generator_policy, seed)` is insufficient if generator code evolves or if downstream tools (such as replay viewers) must inspect arena structures without re-executing generator algorithms.

*The Contract:*
- Replay and result headers must embed **both**:
  1. The generator policy ID and deterministic seed.
  2. The **fully realized environment configuration** (exact start coordinates, core boundaries, and arena size).

---

## 10. Research Policy and Ruleset Architecture

### 10.1 Review of Scheduler Overrides
In commit `d6bbe47`, `MatchRequest`'s `scheduler_chunk_size` and `scheduler_rotate_start` overrides were made identity-safe by folding the effective policy's scheduling parameters into `canonical_match_id` and `evaluation_id`.

**Long-Term Research Policy Recommendation:**
- While request-level scheduler overrides served as a temporary testbed, [AGENTS.md](file:///d:/Projects/BATTLE2/AGENTS.md) explicitly warns:
  > "A Ruleset's gameplay semantics belong on its `RulesetPolicy`... not on `MatchRequest`. A per-match override field that only research code can set is how a hidden experiment switch becomes accidental public API."
- Therefore, V6 research will **not** expand request-level overrides.
- Instead, research gameplay variations will be encapsulated as **explicit `RulesetPolicy` instances** or via a dedicated, immutable **`ResearchScenarioPolicy`**.

### 10.2 Research Ruleset Naming and Versioning Strategy
To prevent conflation with stable production controls:
1. **Prefix Rule:** All experimental rulesets use the prefix:
   `bytefray-rules-6-research-<topic>`
   For Phase 4:
   `bytefray-rules-6-research-scale`
2. **Promotion Gate:** An experimental ruleset never reuses a stable ID. If a research mechanic is ratified for release, it receives a new permanent identity (e.g. `bytefray-rules-6`) via a frozen promotion proof.
3. **CLI/UI Isolation:** Research rulesets are selectable via CLI `--ruleset` by explicit name, but are excluded from the default production ruleset selector in the Agent Designer until promoted.

---

## 11. Architectural Evaluation of Future Gameplay Mechanics

Before any code is written, five prospective mechanics are architecturally evaluated against the existing engine structure:

### 11.1 Immutable / Special Memory
- **Concept:** Specific memory cells that are indestructible (cannot be overwritten), hazardous, or grant action bonuses.
- **Architectural Locus:**
  - `MemoryState` in VM/Runtime: Requires a cell-attribute bitmask (`is_immutable`, `is_hazard`, `resource_bonus`).
  - `ProcessMatchController`: WRITE action checks cell attributes; attempts to write immutable cells fail with zero state change.
  - Replay Schema: Initial state record must include the special cell mask.
- **API Impact:** `ObservationV2` can optionally expose cell flags in `previous_read_owner` or a new observation field.

### 11.2 Environmental / System Agent
- **Concept:** An autonomous, neutral process that sweeps or clears cells over time.
- **Architectural Approaches Evaluated:**
  - *Option A: Synthetic Match Entrant.* Treat environment as third entrant. **Rejected:** Distorts 1v1 scoring, winner determination, and pairwise tournament matrices.
  - *Option B: Ruleset-Owned Environmental Phase.* A deterministic post-tick or pre-tick phase executed directly by `ProcessMatchController`. **Recommended:** Keeps scoring strictly 1v1, guarantees deterministic execution, and generates standard `EngineEvent` records in replay.

### 11.3 Shrinking Arena
- **Concept:** Constricting the playable area to force late-game interaction, analogous to a battle-royale ring.
- **Architectural Locus in Circular VM:**
  - Physically shrinking/reallocating the circular array breaks modulo arithmetic and existing address pointers.
  - **Cleanest Design:** An **Active Sector Mask** $[L(t), R(t)]$. Cells outside the sector become hazardous or dead. Processes anchored outside are disrupted or terminated; writes outside are rejected. Preserves global circular coordinates while dynamically constricting legal space.

### 11.4 Fog of War / Information Limits
- **Concept:** Restricting agent awareness of distant anchors and writes.
- **Architectural Locus:**
  - `Agent API v2` **already supports bounded perception!** `ObservationV2` only reveals enemy anchors within the observer process's declared `reach`.
  - The apparent "omniscience" of current agents is due to $reach$ being declared up to $A/2$ at zero cost.
  - Fog experiments can be conducted within API v2 simply by enforcing reach caps or parameterizing visibility without bumping to API v3.
- **Critical Caution from V3 Research:** Bounded reach must **not** be introduced naively. As documented in V3 Phase 2 (`docs/archive/v3/V3_PHASE2_LOCALITY_FEASIBILITY.md`), bounded reach created the catastrophic "bulldozer effect" where contiguous expanders swept solid bands that incidentally obliterated stationary cores, search collapsed into slow expansion, and defenders suffered an unsustainable 41.5% movement overhead. Any information-restriction or fog mechanism must pair reach bounds with anti-bulldozer rules (such as non-contiguous core geometry, core-hit confirmation requirements, or mobile defense advantages).

### 11.5 Economic Triangle (Greed vs Rush vs Defense)
- **Concept:** Creating strategic trade-offs where:
  - Greed (expansion) out-scores Defense.
  - Rush (fast strike) destroys Greed before it scales.
  - Defense (fortification/repair) survives Rush and counter-attacks.
- **Feasibility with Existing Mechanics:**
  - API v2 already has the necessary raw ingredients:
    - Fixed quota ($Q=8$) requires choosing between spreading processes (Greed), moving forward (Rush), or inspecting/rewriting own core (Defense).
    - Previous failures were caused by global snipers hitting on tick 1, eliminating the setup window required for Greed or Defense.
    - Increasing spatial scale and bounding reach naturally re-establishes the travel-time window needed for an economic triangle to function.

---

## 12. Staged Research Sequence: One Variable at a Time

To prevent confounding multiple unverified mechanics, V6 research will adhere strictly to a **6-stage sequential program**:

```text
+------------------------------------------------------------------------+
| STAGE 1: RAW ARENA SCALING (Phase 4B)                                  |
| - Arena size: 512, 1024, 4096, 16384, 65536                           |
| - Stable V4 rules and constants unchanged                              |
| - Benchmark: V6-Bench-8 field                                          |
| - Question: What breaks naturally? Where do timeouts dominate?         |
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
| STAGE 2: GEOMETRIC NORMALIZATION & TICK HORIZONS                       |
| - Proportional placement separation                                    |
| - Traversal-normalized tick limits (Linear T~A primary; see Sec 5)     |
| - Scaled movement strides                                              |
| - Question: Does normalized travel restore baseline dynamics?          |
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
| STAGE 3: REACH BOUNDARIES & SENSORY LIMITS                             |
| - Evaluate capped reach ladders at large scales                        |
| - Analyze requirement for active search vs blind artillery             |
| - Question: Does bounded reach create local pursuit without deadlock?  |
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
| STAGE 4: DISRUPTION & CORE RESILIENCE                                  |
| - Remediate permanent disrupt-lock                                     |
| - Dynamic repair-rate vs overwrite dynamics                            |
| - Question: Can defense survive long enough to counter-attack?         |
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
| STAGE 5: ACTIVE ARENA DYNAMICS (Shrinking Zone / Hazards)              |
| - Active sector masks / neutral environmental sweeps                   |
| - Question: Does environmental pressure eliminate late-game stagnation?|
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
| STAGE 6: MULTI-AGENT ECONOMIC EQUILIBRIUM                              |
| - Integrate validated mechanics into candidate Ruleset 6               |
| - Measure tournament transitivity, cycles, and counterplay             |
+------------------------------------------------------------------------+
```

---

## 13. Experimental Tiers and Computational Cost Estimates

### 13.1 Experimental Tiers
To manage computational expense and provide rapid feedback, experiments are structured into three standardized tiers:

1. **Tier 1: Smoke / Exploratory Matrix**
   - Roster: 4 agents (`Octave`, `v5_scout_striker`, `v4_claimer`, `v5_core_defender`).
   - Pairs: 6 pairings.
   - Repetitions: 2 seeds $\times$ 2 orientations = 4 matches per pair.
   - Total Matches per Condition: $6 \times 4 = 24$ matches.
   - Purpose: Rapid validation of new runners, sanity check on crashes, quick rejection of unworkable parameters.
2. **Tier 2: Research Field Matrix**
   - Roster: 8 benchmark agents (`V6-Bench-8`).
   - Pairs: 28 pairings.
   - Repetitions: 8 seeds $\times$ 2 orientations = 16 matches per pair.
   - Total Matches per Condition: $28 \times 16 = 448$ matches.
   - Purpose: Primary data collection for comparative analysis, leaderboard construction, and cycle detection.
3. **Tier 3: Qualification Matrix**
   - Roster: Full 10-agent suite (including `v4_quorum` and `hydra_alpha2`).
   - Pairs: 45 pairings.
   - Repetitions: 16 seeds $\times$ 2 orientations = 32 matches per pair.
   - Total Matches per Condition: $45 \times 32 = 1,440$ matches.
   - Purpose: Formal release qualification and promotion proof.

### 13.2 Scaling and Computational Cost Model
Let:
- $N$ = number of agents in roster
- $P = \frac{N(N - 1)}{2}$ = pairwise matchups
- $S$ = deterministic seeds
- $O = 2$ = both orientations (`candidate_first`, `opponent_first`)
- $A_{\text{count}}$ = number of arena sizes tested

$$\text{Total Matches} = A_{\text{count}} \times \frac{N(N - 1)}{2} \times S \times O$$

#### Cost Estimates for Stage 1 (Raw Scaling Across 5 Arenas):
Using Tier 2 (`V6-Bench-8`, $N=8$, $P=28$, $S=8$, $O=2$):
- Matches per Arena Size: $28 \times 16 = 448$ matches.
- Across 5 Arena Sizes: $5 \times 448 = \mathbf{2,240\text{ matches}}$.
- Execution Timing — **planning estimate, not a measurement of this workload (Phase 4A.1 audit).** The `bytefray-rules-6-research-scale` ruleset does not exist yet, and no 1000-tick/$Q=8$ match at $A \ge 4096$ has been run and timed under it, so "under 30 seconds" cannot be a measurement of this specific sweep. It is a projection extrapolated from smaller-scale, 512-cell `bytefray-rules-4` per-match costs, assuming per-match execution time is independent of `arena_size` (plausible, since territory/CPU statistics are tracked incrementally rather than by scanning the arena — see `match_service.py:577-604` — but not verified at $A=16384$ or $A=65536$). Treat the "$<5\text{ ms}$ at 65,536 cells" and "under 30 seconds total" figures as **planning estimates**, and **benchmark during Phase 4B smoke qualification before launching the full sweep** rather than treating them as a guarantee.
- Replay Storage and Bounded Footprint:
  - In a 2-entrant match with quota $Q = 8$, the maximum number of cell mutations per tick is bounded by $\Delta_{\text{writes}} \le 2 \times Q = 16\text{ diffs/tick}$.
  - Over a 1,000-tick match, total memory diffs cannot exceed $16,000$ entries. **This diff-count bound alone does not prove a byte-size bound (Phase 4A.1 audit)** — JSON/event serialization overhead (address, length, owner, and per-byte `values` fields, plus per-tick process/agent-state records) is not accounted for by the diff count.
  - The **"$< 1\text{ MB}$ (typically 300–600 KB)"** per-match replay-size figure at $A=65{,}536$ is therefore an **analytical estimate, not a proven guarantee**, informed by two data points that bracket rather than confirm it: (a) [`docs/specs/agent_lab.md:161`](file:///d:/Projects/BATTLE2/docs/specs/agent_lab.md#L161) measured a 200-tick, 2-agent match's `replay.jsonl` at ~193 KB under the same $Q=8$ quota; linearly extrapolating to 1,000 ticks (replay volume scales with `instr_per_tick x realized ticks`, independent of `arena_size`, per the next finding) gives ~965 KB — consistent with, but not itself proof of, the "$<1$ MB" claim. (b) [`docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md:832,840`](file:///d:/Projects/BATTLE2/docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md#L832) measured a mean `replay.jsonl` of **4,762 KB** at $A=65{,}536$ under a much higher `instr_per_tick=128` budget (16x this methodology's $Q=8$) — confirming replay size scales with `instr_per_tick x ticks`, not arena size, but also showing actual measured sizes can be several megabytes once the action budget is large, so "$<1$ MB" holds specifically *because* $Q=8$ is a low budget, not because arena size is 65,536. **Label this per-match figure as an analytical estimate pending direct benchmarking at $Q=8$, $T_{\max}=1000$, $A=65{,}536$ during Phase 4B smoke qualification**, not a guarantee.
  - Sweeps emit full replays only for representative vectors or diagnostic anomalies (the count of which Phase 4B must still decide); the entire 2,240-match evaluation produces $< 15\text{ MB}$ of **summary and result artifacts only** — this figure does not include whatever subset of full replays are retained for representative/anomalous matches, which is a separate, additive storage category sized by the per-match replay estimate above times however many replays Phase 4B chooses to retain.

---

## 14. Replay and Result Schema Implications

### 14.1 Replay Schema 4 Compatibility
The current replay schema is **`battle2.replay` Schema 4** ([`docs/REPLAY_SCHEMA.md`](file:///d:/Projects/BATTLE2/docs/REPLAY_SCHEMA.md)):
- `arena_size` is already a first-class integer on `ReplayHeader.config.arena_size`.
- `processes` in `TickSnapshot` already record absolute integer `anchor` and `reach`.
- **Sparse Memory Representation:** Memory diffs are sparse address-value tuples (`address`, `length`, `owner`, `values`), recording only mutated bytes. Since each entrant has quota $Q=8$, tick mutations are strictly capped at $\le 2 \times Q = 16$ cells/tick. Replay volume is governed by ticks and action budget, not by total arena dimension $A$ — confirmed by V3 Phase 1's own finding that "replay volume scales with `instr_per_tick x realized ticks`, not with arena size" ([`V3_PHASE1_ARENA_ACTION_DENSITY.md:840`](file:///d:/Projects/BATTLE2/docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md#L840)). A match in a 65,536 arena is expected to produce a replay on the order of the estimate in §13.2 (analytical, pending Phase 4B benchmarking — **not** an already-proven $<1\text{ MB}$ figure), parsed by readers with identical O(1)-per-diff memory delta logic regardless of arena size.
- **Conclusion:** Replay Schema 4 **requires zero modifications** to support arena sizes up to 65,536 — this is a wire-format/schema-compatibility conclusion, independent of the still-to-be-benchmarked storage-size estimate above.

### 14.2 Result Schema Compatibility
- `result.json` records final scores, winner, ticks, and agent statistics.
- Territory percentage calculations (`territory_pct_*`) dynamically divide by `arena_size` ([`match_service.py:596-604`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L596-L604)).
- **Conclusion:** Result Schema **requires zero modifications**.

### 14.3 Future Telemetry Extensions (Additive Only)
For Stage 2 and beyond, any new research metrics (e.g. `first_contact_tick`, `unique_cells_written`) will be populated in `NativeAgentResult.metadata` or as additive fields under `ReplayHeader.reproducibility`. No schema version bump is warranted.

---

## 15. Recommended First Implementation Phase: Phase 4B

### 15.1 Definition of the Smallest Next Coding Phase
The design establishes that the cleanest, lowest-risk entry into V6 gameplay experimentation requires adding **no new gameplay mechanics**.

**Phase 4B Scope:**
1. **Register Experimental Research Ruleset:**
   - Define `RULESET_V6_RESEARCH_SCALE` in `ruleset_policy.py`:
     ```python
     BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID = "bytefray-rules-6-research-scale"
     
     RULESET_V6_RESEARCH_SCALE = RulesetPolicy(
         ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
         supported_runtime_kinds=frozenset({"python"}),
         supported_python_api_versions=frozenset({2}),
         scheduler_mode="chunked",
         scheduler_chunk_size=2,
         scheduler_rotate_start=True,
         core_placement="seeded",
         process_selection="round_robin",
     )
     ```
   - Behaviorally **identical to `bytefray-rules-4` at 512 cells** — verified consistent: `RulesetPolicy` (`ruleset_policy.py`) carries only scheduler/placement/process-selection/runtime-kind fields, and the sketch above copies every one of `bytefray-rules-4`'s values unchanged. `quota`, `core_size`, and `reach` are not `RulesetPolicy` fields at all (they live elsewhere as engine-wide constants/config), so omitting them from this sketch does not risk behavioral drift.
2. **Support Variable Arena Evaluation:**
   - In `evaluation_service.py`, allow non-512 `--arena-size` specifically when `ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID`.
   - Keep `bytefray-rules-4` strictly locked to 512 cells.
   - **Additional prerequisite found (Phase 4A.1 audit):** this alone is not sufficient. `evaluation_service.py`'s existing ruleset allow-list ([`evaluation_service.py:808`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/evaluation_service.py#L808)) currently rejects *any* `--ruleset` other than `bytefray-rules-4` outright, with the explicit comment "`bytefray-rules-4` is the only Ruleset that can create a new evaluation artifact now." Phase 4B must also extend this gate to admit `BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID`, or the new ruleset will be rejected before the arena-size check is ever reached. This is a concrete implementation prerequisite Phase 4B must explicitly test (a request with the new ruleset ID and a non-512 arena size must reach and pass the arena-size check, not fail earlier at the allow-list).
3. **Execute the Experiment A Sweep:**
   - Execute the 2,240-match Tier 2 matrix across $A \in \{512, 1024, 4096, 16384, 65536\}$.
   - Record and publish the empirical findings in `docs/research/v6/V6_PHASE4B_ARENA_SCALING_STUDY.md`.

This isolates spatial scaling cleanly, protects the stable control, and grounds the next phase of gameplay development in measured empirical evidence.

---

## Research Integrity Addendum (2026-09-22)

Two independent research-integrity reviews have established that the Phase 4 arena-scaling and movement research line was grounded in flawed causal premises and compromised by test and benchmark defects:

1. **V4 Tick-1 Forced-Win Gate:** Shipped stable `bytefray-rules-4` contains a deterministic tick-1 Seat-A forced core capture under competent global-reach play (`CompetentGlobalSniperProbe`), winning on tick 1 before Seat B ever executes an instruction. This seat/order-driven exploit was the unacknowledged driver of apparent lethality in global probes, invalidating interpretations of global reach as balanced gameplay.
2. **Benchmark Corpus Tracking (Octave):** The V6-Bench-8 field previously depended on an untracked local `Octave` agent in the user's private `agents/` directory. Octave has now been fingerprinted (`e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730`) and permanently committed to tracked repository fixtures under `tools/research/v6/fixtures/agents/Octave/`.
3. **Territory Scoring Invariance:** Territory scoring was incorrectly described in Phase 4B/4C/4D as scaling with arena percentage and suffering "dilution." In reality, `ScoringPolicy` awards 1 point per 64 raw cells held ($\lfloor \text{cells} / 64 \rfloor$) independently of arena size. Scoring was always invariant to arena dimensions.
4. **Agent Context Arena Size:** Phase 4C/4D incorrectly asserted that `ObservationV2` and match context hid `arena_size` from agents. In fact, `context.arena_size` was already supplied in `AgentContext` upon initialization.
5. **Fallacy of $\sigma^2_{\text{opp}}$ as Counterplay:** Variance of win rates across opponents is a mathematical property of intermediate ranks in a purely transitive 1D skill hierarchy, not evidence of opponent-dependent counterplay or non-transitivity. It has been replaced by 1D rating models, matchup residuals ($R_{ij} = W_{ij} - \hat{W}_{ij}$), upset reversals, and explicit tie tracking.
6. **Cycle Disappearance Artifact:** The apparent disappearance of directed 3-cycles at larger arenas was an artifact of win rates slipping below the fixed 0.55 dominance threshold, not a reversal or restructuring of competitive ordering.
7. **Line Closure & Transition to E2:** The arena-scaling and movement normalization line is closed. Active research pivots to E2 — Multi-Tick Capture Hold to address the root causal vulnerability identified in stable V4.
