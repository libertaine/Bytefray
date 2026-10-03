# Bytefray V6 Phase 4E — Territory Scoring Normalization Study

**Status:** Complete
**Branch:** `v6-research`
**Baseline:** `2d4a40c` (Phase 4D completion)
**Predecessors:** [`V6_PHASE4B_ARENA_SCALING_STUDY.md`](V6_PHASE4B_ARENA_SCALING_STUDY.md), [`V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md`](V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md), [`V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md`](V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md), [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md)

---

## A. Objective

Phase 4E investigates the second major scale-sensitive factor identified in earlier scaling reports: **territory scoring economics**.

The governing research question posed by Phase 4E is:

> **Does arena-size-sensitive territory scoring materially contribute to the collapse of expansion strategies and the transitive competitive hierarchy as arena size grows?**
>
> More specifically: *If the economic value of a fixed amount of useful territorial work is normalized across arena sizes, does Bytefray produce more opponent-dependent strategy without changing movement, reach, placement, or time budget?*

In accordance with Section 4 and Section 5 of the research methodology, Phase 4E first audited the end-to-end production scoring path in the source code before selecting or implementing any candidate normalization.

---

## B. Current Territory Economics

### B.1 Source Code Audit of Production Scoring

A comprehensive audit of the production match execution path (`engine/src/battle_engine/scoring.py`, `process_runtime.py`, `vm.py`, `results.py`, and `config.py`) establishes the exact mechanisms governing match scoring:

1. **VM Ownership Representation:**
   In `battle_engine.vm.VM`, ownership is maintained on a circular byte array (`self.arena: bytearray`, `self.writer: list[str | None]`). The authoritative aggregate mapping `self.ownership_counts: dict[str, int]` maintains the exact number of arena cells owned by each entrant ID in $O(1)$ time upon every write mutation via `_wr8`.

2. **Scoring Invocation Timing:**
   Scoring occurs once per tick in `battle_engine.process_runtime.ProcessMatchController.run` (lines 1292–1297):
   ```python
   self.scoring.score_alive(self.score, self.states)
   self.scoring.score_territory(
       self.score,
       self.states,
       self.vm.ownership_counts,
   )
   ```
   Scoring is evaluated sequentially at tick end, after entrant process scheduling and `apply_core_capture` have completed.

3. **Production Scoring Equations:**
   The match score is governed strictly by `ScoringPolicy` (`engine/src/battle_engine/scoring.py`):
   - **Alive Score:**
     $$\text{Score}_{\text{alive}}(t) = \text{Score}_{\text{alive}}(t-1) + \mathbf{1}_{\{\text{alive}\}} \times \text{weights.alive}$$
     Default `weights.alive = 1.0` point per tick alive.
   - **Kill Score:**
     $$\text{Score}_{\text{kill}} = \text{kills} \times \text{weights.kill}$$
     Default `weights.kill = 5.0` points per attributed kill.
   - **Territory Score:**
     $$\text{Score}_{\text{territory}}(t) = \text{Score}_{\text{territory}}(t-1) + \left\lfloor \frac{\text{cells}(t)}{\max(1, \text{weights.territory\_bucket})} \right\rfloor \times \text{weights.territory}$$
     Default `weights.territory = 1.0` point per bucket per tick, with `weights.territory_bucket = 64` cells.

4. **Winner Resolution:**
   In `battle_engine.results.resolve_winner`:
   - If exactly one entrant is alive, that entrant wins outright by survival (`len(alive) == 1`).
   - If two or more entrants survive at $T_{\max} = 1000$ (timeout) under default `win_mode = "score_fallback"`, winner eligibility is restricted to the living survivors, and the entrant with the strictly highest total score wins.

### B.2 Exact Production Scoring Properties

| Property | Reality in Production Source |
|---|---|
| **Quantity scored** | Raw integer count of cells currently owned (`self.vm.ownership_counts[agent_id]`) |
| **Scoring unit** | Fixed-cell buckets: $\lfloor \text{cells} / 64 \rfloor$ |
| **Arena size dependence** | **Zero.** The parameter `arena_size` does **not** appear in `ScoringPolicy` or `score_territory`. |
| **Sampling frequency** | Sampled on live ownership every single tick. |
| **Measurement basis** | Current instantaneous count at tick $t$, accumulated over all ticks ($\sum_{t=1}^T \lfloor C_t / 64 \rfloor$). Neither `territory_max` nor `territory_avg` affects score. |
| **Role of `territory_bucket`** | Active gameplay scoring divisor (64 cells per bucket); not merely a reporting parameter. |

### B.3 Reconciling Prior Research Claims

Prior research documents contained assertions that must now be formally reconciled against source reality:

- *Claim in Phase 4B (Line 494):* *"Its territory-percentage win condition is normalized by arena so its territory share collapses 16-fold (47% → 3%) as the arena grows."*
- *Claim in Phase 4C (Line 58 & 342):* *"Territory Scoring: Unchanged; scored as raw proportion of arena cells... territorial expanders (v4_claimer) suffer a 16-fold collapse in territory share because score is evaluated as raw percentage of arena size."*
- *Claim in Phase 4D (Line 347):* *"Decouple territorial viability from arena size via non-percentage scoring, thresholded territory buckets..."*

**Reconciliation:**
These statements conflated two entirely distinct architectural layers:
1. **Production scoring mechanics (`ScoringPolicy`):** Evaluates strictly raw, bucketed cell counts ($\lfloor \text{cells} / 64 \rfloor$). Production scoring is **already** non-percentage, **already** uses fixed-cell territory buckets, and **already** treats a cell with identical economic value across all arena sizes ($A=512$ through $A=65536$).
2. **Diagnostic reporting metrics (`results.py` / `match_service.py`):**
   ```python
   "territory_pct_last": state["territory_last"] * 100.0 / arena
   "territory_pct_max":  state["territory_max"]  * 100.0 / arena
   "territory_pct_avg":  avg_territory            * 100.0 / arena
   ```
   These diagnostic percentage fields divide cell counts by $A$ purely for presentation in telemetry and tabular summaries. **They have never participated in winner resolution, match scoring, or VM execution.**

3. **Strategic production limits vs scoring economics:**
   With $Q=8$ instructions per tick and $T=1000$ ticks, an entrant has a hard upper bound of 8,000 executed instructions. An expander like `v4_claimer` alternates MOVE and WRITE, executing at most 4,000 writes.
   - At $A=512$, 4,000 writes wraps around the 512-cell ring repeatedly, saturating at ~500 cells ($\approx 97\%$ diagnostic territory share).
   - At $A=65536$, 4,000 writes covers ~4,000 linear cells, saturating at ~4,000 cells ($\approx 6.1\%$ diagnostic territory share).
   The diagnostic percentage collapses purely because the denominator ($A$) scaled $128\times$ while the action budget remained fixed. The actual production scoring rate **increased**, because the expander did not overwrite its own cells.

---

## C. Normalization Design & Premise Evaluation

### C.1 Evaluation of Candidate Normalizations

Section 10 of the research specification proposed three candidate conceptual models:
1. *Fixed-cell territory buckets (Candidate 2):* Reward fixed quantities of controlled cells rather than fraction-of-total-world coverage.
   - **Audit finding:** Production Bytefray *already implements this exact model*. Every 64 cells yields 1.0 point per tick, invariant to $A$.
2. *Control-relative territory units (Candidate 1):* Express territorial production relative to the 512-cell reference scale.
   - **Audit finding:** If territory score were multiplied by $A/512$ to "normalize" percentage coverage, at $A=65536$ each 64-cell bucket would yield 128.0 points per tick, awarding `v4_claimer` over 3,800,000 points per match. This directly violates Section 11 ("Do not create free points / score inflation"). Conversely, dividing bucket points or scaling bucket thresholds by $A/512$ (e.g. requiring 8,192 cells per bucket) would reduce territory score to exactly 0, destroying territorial incentives.
3. *Local/active territory denominator (Candidate 3):* Score territory against a reachable spatial budget.
   - **Audit finding:** Invariant reach and literal movement leave active reach at 1 cell for claimer; creating dynamic spatial budgets violates the requirement that scoring be isolated from spatial mechanics.

### C.2 Hard STOP Condition Triggered

Section 5 and the STOP CONDITIONS of the Phase 4E specification provide explicit decision logic:

> *"If the Phase 4E premise turns out to be wrong—for example, territory scoring is already perfectly normalized and the observed collapse is solely production economics—STOP and report that rather than inventing a scoring fix."*
>
> *"STOP CONDITIONS: Stop before implementation if: source audit disproves the assumed territory-economics problem; scoring cannot be isolated from other gameplay semantics; a normalized formula cannot reproduce A=512 exactly; normalization requires movement/reach/tick changes."*

Because the production engine already scores territory via fixed-cell buckets independent of arena size, the assumed "arena-size-sensitive territory scoring problem" is disproven by source audit. In strict accordance with the governing protocol, **no artificial scoring ruleset was implemented**, preserving the integrity of the experimental methodology.

---

## D. Research Ruleset

Per Section C above, no new runtime Ruleset (`bytefray-rules-6-research-scale-territory`) was registered, as doing so would have required inventing an artificial scoring distortion to solve a non-existent scoring defect.

The control ruleset remains `bytefray-rules-6-research-scale` (from Phase 4B), whose scoring semantics are identical to stable `bytefray-rules-4`:
- Chunked scheduler ($K=2$, rotating start)
- Seeded core placement
- Round-robin intra-entrant process selection
- Literal movement ($\text{max\_move\_delta} = 64$)
- Fixed-cell territory scoring ($\lfloor \text{cells} / 64 \rfloor \times 1.0$)

---

## E. Identity & Provenance

Because no new gameplay ruleset was introduced:
- Identity version remains **7** (`IDENTITY_VERSION_V4`).
- Result and Replay schema versions remain **7** (`SCHEMA_VERSION_V4`).
- Evaluation contracts and CLI remain unmodified.
- Control artifacts under `runs/research_v6_phase4b/` remain authoritative and uncorrupted.

---

## F. Direct Score Characterization

To verify that the existing production scoring equation produces identical economic value across arena sizes for any fixed territory holding, direct deterministic evaluation yields:

$$\text{Points per tick} = \left\lfloor \frac{\text{cells}}{64} \right\rfloor \times 1.0$$

| Territory Holding | Score Contribution at $A=512$ | Score Contribution at $A=1024$ | Score Contribution at $A=4096$ | Score Contribution at $A=16384$ | Score Contribution at $A=65536$ | Economic Invariance |
|---:|---:|---:|---:|---:|---:|:---:|
| 0 cells | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | **Identical** |
| 1 cell | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | **Identical** |
| 8 cells (core) | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | 0.0 pts/tick | **Identical** |
| 64 cells | 1.0 pts/tick | 1.0 pts/tick | 1.0 pts/tick | 1.0 pts/tick | 1.0 pts/tick | **Identical** |
| 128 cells | 2.0 pts/tick | 2.0 pts/tick | 2.0 pts/tick | 2.0 pts/tick | 2.0 pts/tick | **Identical** |
| 256 cells | 4.0 pts/tick | 4.0 pts/tick | 4.0 pts/tick | 4.0 pts/tick | 4.0 pts/tick | **Identical** |
| 512 cells | 8.0 pts/tick | 8.0 pts/tick | 8.0 pts/tick | 8.0 pts/tick | 8.0 pts/tick | **Identical** |
| 1024 cells | N/A (exceeds $A$) | 16.0 pts/tick | 16.0 pts/tick | 16.0 pts/tick | 16.0 pts/tick | **Identical** |
| 2048 cells | N/A (exceeds $A$) | N/A (exceeds $A$) | 32.0 pts/tick | 32.0 pts/tick | 32.0 pts/tick | **Identical** |
| 4096 cells | N/A (exceeds $A$) | N/A (exceeds $A$) | 64.0 pts/tick | 64.0 pts/tick | 64.0 pts/tick | **Identical** |

This direct characterization mathematically proves that territory scoring is already perfectly normalized: an agent owning 64, 128, 256, or 512 cells receives **the exact same score per tick** at $A=65536$ as it does at $A=512$.

---

## G. A=512 Equivalence

Because the production scoring equation is identical across all arena sizes, $A=512$ equivalence is naturally satisfied. Under Phase 4B, the live equivalence check between `bytefray-rules-4` and `bytefray-rules-6-research-scale` across all 448 matches produced:
- **0 result mismatches**
- **0 placement mismatches**
- **0 score mismatches**

---

## H. Experimental Matrix & Benchmark Corpus

The empirical data examined in this study encompasses the complete Phase 4B benchmark dataset:
- **Benchmark Corpus:** `V6-Bench-8` (8 frozen Agent API v2 entrants)
- **Seeds:** 1–8 (8 standard seeds)
- **Orientations:** Candidate-first and Candidate-second (both seat orientations)
- **Matchups:** 28 unordered pairs $\times 16$ matches = 448 matches per arena
- **Arena Progression:** $A \in \{512, 1024, 4096, 16384, 65536\}$
- **Total Dataset:** 2,240 fully recorded matches

---

## I. Territory Economics Empirical Results

A deep empirical analysis of the 2,240 matches reveals how territory ownership and match scores actually evolved as arena size scaled:

### Table I.1: Mean Performance Metrics by Arena Size (Full V6-Bench-8 Corpus)

Generated deterministically by `tools/research/v6/phase4e_analyzer.py` across all 2,240 matches:

| Entrant | Metric | $A=512$ | $A=1024$ | $A=4096$ | $A=16384$ | $A=65536$ | Scaling Trend |
|---|---|---:|---:|---:|---:|---:|:---:|
| **`Octave`** | Pure Win Rate ($W/N$) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9375 | −6.2% (7 ties at $A=65k$) |
|  | Tournament Rate ($(W+0.5T)/N$) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9688 | −3.1% (Recorded in Phase 4B) |
|  | Mean Match Score | 23.7 | 99.9 | 178.7 | 99.4 | 121.8 | Combat-limited |
|  | Mean Owned Cells | 24.7 | 56.0 | 48.0 | 27.4 | 15.7 | Low (core + kill trajectory) |
|  | Diagnostic Territory % | 4.83% | 5.47% | 1.17% | 0.17% | 0.02% | Dilution by $A$ |
| **`nemesis_alpha2`** | Pure Win Rate ($W/N$) | 0.5446 | 0.6518 | 0.7054 | 0.7321 | 0.7500 | **+20.5% (Rise via Timeout)** |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.6205 | 0.6830 | 0.7054 | 0.7321 | 0.7500 | +13.0% (Recorded in Phase 4B) |
|  | Mean Match Score | 420.7 | 694.6 | 1,935.0 | 5,173.3 | 10,251.1 | **+2,336% (24.4× Increase)** |
|  | Mean Owned Cells | 36.0 | 56.4 | 162.3 | 557.4 | 1,313.0 | **+3,547% (36.5× Increase)** |
|  | Diagnostic Territory % | 7.02% | 5.51% | 3.96% | 3.40% | 2.00% | Persistent writing |
| **`v5_scout_striker`** | Pure Win Rate ($W/N$) | 0.5982 | 0.4821 | 0.5089 | 0.5714 | 0.5536 | −4.5% (Stable 0.50–0.60) |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.7188 | 0.6518 | 0.6518 | 0.6786 | 0.6830 | −3.6% (Recorded in Phase 4B) |
|  | Mean Match Score | 414.3 | 1,086.3 | 3,383.7 | 3,253.0 | 2,925.5 | Moderate increase |
|  | Mean Owned Cells | 64.9 | 135.3 | 393.6 | 387.5 | 358.2 | Moderate capacity |
|  | Diagnostic Territory % | 12.67% | 13.22% | 9.61% | 2.37% | 0.55% | Dilution by $A$ |
| **`v4_claimer`** | Pure Win Rate ($W/N$) | 0.4375 | 0.4554 | 0.5000 | 0.5446 | 0.5714 | **+13.4% (Monotonic Rise)** |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.4375 | 0.4554 | 0.5000 | 0.5446 | 0.5714 | **+13.4% (0 ties at all $A$)** |
|  | Mean Match Score | 2,421.5 | 5,011.4 | 13,990.0 | 14,507.0 | 16,765.0 | **+592.3% (6.9× Increase)** |
|  | Mean Owned Cells | 240.2 | 484.7 | 1,736.6 | 1,769.5 | 1,948.8 | **+711.3% (8.1× Increase)** |
|  | Diagnostic Territory % | 46.91% | 47.33% | 42.40% | 10.80% | 2.97% | −93.7% (Artifact of $A$) |
| **`v5_region_attacker`** | Pure Win Rate ($W/N$) | 0.4196 | 0.4196 | 0.4018 | 0.3571 | 0.4196 | Invariant (~0.41) |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.5804 | 0.5625 | 0.5223 | 0.4777 | 0.5089 | −7.1% (Recorded in Phase 4B) |
|  | Mean Match Score | 718.6 | 1,232.8 | 2,147.9 | 1,981.6 | 1,566.9 | Modest increase |
|  | Mean Owned Cells | 51.1 | 84.0 | 233.4 | 215.6 | 182.9 | Modest capacity |
|  | Diagnostic Territory % | 9.99% | 8.20% | 5.70% | 1.32% | 0.28% | Dilution by $A$ |
| **`v5_dual_team`** | Pure Win Rate ($W/N$) | 0.1696 | 0.1875 | 0.1875 | 0.1607 | 0.1696 | Invariant (~0.17) |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.3795 | 0.3750 | 0.3393 | 0.2946 | 0.2634 | −11.6% (Combat decay) |
|  | Mean Match Score | 692.7 | 889.4 | 961.2 | 881.1 | 722.5 | Modest plateau |
|  | Mean Owned Cells | 24.1 | 36.7 | 76.6 | 72.5 | 58.3 | Modest capacity |
|  | Diagnostic Territory % | 4.71% | 3.58% | 1.87% | 0.44% | 0.09% | Dilution by $A$ |
| **`v5_core_defender`** | Pure Win Rate ($W/N$) | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 wins across all $A$ |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.1696 | 0.1696 | 0.1786 | 0.1696 | 0.1607 | Stable ties only (~0.17) |
|  | Mean Match Score | 486.1 | 486.3 | 505.7 | 494.8 | 513.2 | Invariant alive baseline |
|  | Mean Owned Cells | 4.1 | 4.2 | 4.2 | 3.7 | 3.3 | Sub-bucket core holding |
|  | Diagnostic Territory % | 0.80% | 0.41% | 0.10% | 0.02% | 0.01% | Dilution by $A$ |
| **`v4_local_defender`** | Pure Win Rate ($W/N$) | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 wins across all $A$ |
|  | Tournament Rate ($(W+0.5T)/N$) | 0.0938 | 0.1027 | 0.1027 | 0.1027 | 0.0938 | Stable ties only (~0.10) |
|  | Mean Match Score | 220.2 | 265.5 | 356.4 | 370.1 | 415.6 | Modest alive baseline |
|  | Mean Owned Cells | 1.5 | 1.6 | 1.9 | 2.3 | 2.4 | Sub-bucket core holding |
|  | Diagnostic Territory % | 0.30% | 0.15% | 0.05% | 0.01% | 0.00% | Dilution by $A$ |

---

## J. Timeout & Score Resolution

In Phase 4B, the timeout rate increased from **31.25%** (140/448 matches) at $A=512$ to **39.06%** (175/448 matches) at $A=65536$.

When matches reach the 1,000-tick horizon without combat termination:
1. Both surviving entrants receive 1,000 alive points ($1000 \times 1.0$).
2. The match outcome is decided **exclusively by accrued territory score**.
3. Because territory score is $\sum_{t} \lfloor \text{cells}(t) / 64 \rfloor$, the entrant that accumulated more raw cells wins the score fallback.
4. Expanders and persistent writers (`v4_claimer`, `nemesis_alpha2`) accumulate 10,000–16,000+ territory points, completely overpowering passive defenders (`v4_local_defender`, `v5_core_defender`) and search-stalled hunters.

---

## K. Claimer Diagnostic

The performance of `v4_claimer` demonstrates conclusively that expansion economics did not collapse:

- **Score Growth:** Average score surged from **2,421.5** at $A=512$ to **16,765.0** at $A=65536$ (+592%).
- **Cell Retention:** Retained owned cells surged from **240.2** at $A=512$ to **1,948.8** at $A=65536$ (+711%).
- **Win Rate:** Win rate increased monotonically from **0.4375** to **0.5714**, moving Claimer from rank 5 up to rank 4 across the benchmark field. Claimer recorded 0 ties across all 2,240 matches, so its pure win rate equals its tournament score rate.
- **Why Claimer thrived:** In larger arenas, hunters experienced search delays and failed to locate Claimer. Because Claimer survived more ticks (mean alive ticks rose from 410.8 to 715.4), and because the arena did not force self-overwriting, Claimer claimed more unique cells, accrued more buckets per tick, and accumulated massive territory scores.

---

## L. Kill-Dominant Control (Octave)

Octave represents the lethal hunting archetype:
- At $A=512$, Octave achieved a **1.0000** win rate with an average match length of 10.1 ticks and average score of 23.7 (10 alive points + 5 kill points + 8 core-cell territory points).
- At $A=65536$, Octave achieved 105 wins, 7 ties, and 0 losses across 112 matches:
  - **Pure Win Rate ($W/N$):** $105 / 112 = \mathbf{0.9375}$ (93.75%).
  - **Tournament Score Rate ($(W+0.5T)/N$):** $(105 + 3.5) / 112 = \mathbf{0.9688}$ (96.875%, matching `phase4b_analysis.json`).
  - Average match length increased to 117.1 ticks as Octave spent more time navigating to locate opponents.
- In every decisive match, Octave won via single-survivor combat termination (`len(alive) == 1`), which bypasses score comparison entirely.
- Territory scoring never interfered with Octave's combat lethality; Octave's mild decay was entirely driven by spatial search time, not territory economics.

---

## M. Region Attacker vs Claimer Matchup

The matchup between `v5_region_attacker` and `v4_claimer` provides the definitive characterization of timeout scoring:

| Arena Size | Region Attacker Wins | Claimer Wins | Ties | Combat Kills | Timeouts (1000 Ticks) |
|---:|---:|---:|---:|---:|---:|
| **512** | 15 | 1 | 0 | 15 | 1 |
| **1024** | 13 | 3 | 0 | 6 | 10 |
| **4096** | 8 | 8 | 0 | 1 | 15 |
| **16384** | 3 | 13 | 0 | 1 | 15 |
| **65536** | 0 | 16 | 0 | 0 | 16 |

### Causal Attribution:
1. At $A=512$, Region Attacker located and killed Claimer in 15 out of 16 matches.
2. At $A=65536$, Region Attacker never located Claimer (0 kills, 16 timeouts).
3. In all 16 timeouts, Claimer had accumulated ~1,950 cells (~30 buckets/tick) yielding ~16,000 points, whereas Region Attacker had only ~180 cells (~2 buckets/tick) yielding ~1,500 points.
4. **Claimer won 100% of large-arena matchups against Region Attacker precisely because territory scoring rewarded its raw cell production.**
5. Territory scoring was not the obstacle to Region Attacker; spatial search failure was.

---

## N. Strategic Ecology

The competitive ecology across arena sizes exhibits high stability:
- **Spearman $\rho$ vs $A=512$:**
  - $A=1024$: 0.9524
  - $A=4096$: 0.9762
  - $A=16384$: 0.9286
  - $A=65536$: 0.8810
- Pairwise dominance remains strongly transitive. The only significant archetype movement is the gradual promotion of persistent writers (`nemesis_alpha2`, `v4_claimer`) as search-stalled hunters fail to deliver lethal combat within 1,000 ticks.

---

## O. Interaction Invariance

Because no ruleset modification was introduced, all physical interaction metrics remain byte-for-byte identical to Phase 4B:
- First-contact tick distributions
- Hostile write timing
- Traversal trajectories
- Core-capture sequences

---

## P. Conclusion

> **Does territory-score normalization materially improve strategic ecology, or merely change which archetype wins score-based matches?**

**Conclusion:**
1. **The premise of Phase 4E was disproven by source audit.** Bytefray's production territory scoring does **not** evaluate territory as a percentage or fraction of arena size; it evaluates fixed-cell buckets ($\lfloor \text{cells} / 64 \rfloor$) whose economic value is identically 1.0 pt/tick across all arena sizes.
2. **Expansion strategies did not collapse economically.** In large arenas, expanders claim more cells, score higher points, and win more matches than in small arenas.
3. The perceived "collapse" reported in earlier prose documents was an artifact of the diagnostic reporting metric `territory_pct_*` ($\text{cells} \times 100 / A$), which reflects finite action capacity (8,000 instructions max) in an expanded physical volume, not scoring dilution.
4. Altering territory scoring cannot solve the spatial search problem or restore opponent-dependent counterplay. When hunters fail to find expanders, expanders already win decisively on score under existing rules.

---

## Q. Next Recommendation

**Do not implement territory scoring normalization.**

Scoring is already invariant to arena size. Future research must address the physical and perceptual causes of spatial isolation:
1. **Perceptual / Sensor Scaling:** Sensor/radar mechanics or core-direction signals that scale with arena dimensions.
2. **Action / Tick Density:** Dynamic tick limits ($T_{\max}(A)$) or instruction scaling.
3. **Scale-Aware Entrant Architecture:** Allowing agents to query `context.arena_size` and adapt patrol radii and movement operands accordingly.

---

## R. Research Tooling

The Phase 4E analysis tool is committed under:
`tools/research/v6/phase4e_analyzer.py`

It operates deterministically without mutating engine runtime or telemetry:
- Ingests all 2,240 Phase 4B match result envelopes (`runs/research_v6_phase4b/equivalence/research-scale` and `runs/research_v6_phase4b/sweep/a*`).
- Computes exact mean match scores, mean cells owned, diagnostic territory percentages, pure win rates ($W/N$), and tournament score rates ($(W+0.5T)/N$) for all 8 benchmark entrants across all 5 arena sizes.
- Computes the head-to-head resolution of `v5_region_attacker` vs `v4_claimer`.
- Generates the direct deterministic score characterization table.

---

## S. Test Suite & Characterization Verification

A dedicated regression and characterization test suite is committed under:
`engine/tests/test_v6_phase4e_territory_scoring.py`

It validates:
1. **Bucket Floor Division:** `ScoringPolicy.score_territory` evaluates $\lfloor \text{cells} / 64 \rfloor \times 1.0$, awarding 0 points for $<64$ cells and integer-bucket multiples thereafter.
2. **Arena Size Independence:** `ScoringPolicy` and `Weights` have zero parameters or dependencies relating to `arena_size`. Scoring identical holdings yields identical points per tick across all 5 arenas.
3. **Control-Anchor $A=512$ Equivalence:** Score contribution at $A=512$ matches $A \in \{1024, 4096, 16384, 65536\}$ for all tested holdings.
4. **Diagnostic Telemetry Separation:** `build_summary` in `results.py` computes `territory_pct_*` by dividing by `arena_size`, but gameplay score is strictly the accumulated integer-bucket score.
5. **Score-Fallback Timeout Resolution:** In 1,000-tick timeouts with equal alive points, the entrant with more territory buckets wins decisively.
6. **Ruleset Isolation:** Stable `bytefray-rules-4` and research `bytefray-rules-6-research-scale` remain isolated, with no spurious ruleset registered.
7. **Live Match Execution:** End-to-end match execution with starter agents confirms live score accumulation and telemetry recording.

---

## Research Integrity Addendum (2026-09-22)

Two independent research-integrity reviews have established that the Phase 4 arena-scaling and movement research line was grounded in flawed causal premises and compromised by test and benchmark defects:

1. **V4 Tick-1 Forced-Win Gate:** Shipped stable `bytefray-rules-4` contains a deterministic tick-1 Seat-A forced core capture under competent global-reach play (`CompetentGlobalSniperProbe`), winning on tick 1 before Seat B ever executes an instruction. This seat/order-driven exploit was the unacknowledged driver of apparent lethality in global probes, invalidating interpretations of global reach as balanced gameplay.
2. **Benchmark Corpus Tracking (Octave):** The V6-Bench-8 field previously depended on an untracked local `Octave` agent in the user's private `agents/` directory. Octave has now been fingerprinted (`e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730`) and permanently committed to tracked repository fixtures under `tools/research/v6/fixtures/agents/Octave/`.
3. **Territory Scoring Invariance:** As established by this study, territory scoring awards 1 point per 64 raw cells held ($\lfloor \text{cells} / 64 \rfloor$) independently of arena size. Scoring was always invariant to arena dimensions.
4. **Agent Context Arena Size:** Earlier reports asserted that `ObservationV2` and match context hid `arena_size` from agents. In fact, `context.arena_size` was already supplied in `AgentContext` upon initialization.
5. **Fallacy of $\sigma^2_{\text{opp}}$ as Counterplay:** Variance of win rates across opponents is a mathematical property of intermediate ranks in a purely transitive 1D skill hierarchy, not evidence of opponent-dependent counterplay or non-transitivity. It has been replaced by 1D rating models, matchup residuals ($R_{ij} = W_{ij} - \hat{W}_{ij}$), upset reversals, and explicit tie tracking.
6. **Cycle Disappearance Artifact:** The apparent disappearance of directed 3-cycles at larger arenas was an artifact of win rates slipping below the fixed 0.55 dominance threshold, not a reversal or restructuring of competitive ordering.
7. **Line Closure & Transition to E2:** The arena-scaling and movement normalization line is closed. Active research pivots to E2 — Multi-Tick Capture Hold to address the root causal vulnerability identified in stable V4.
