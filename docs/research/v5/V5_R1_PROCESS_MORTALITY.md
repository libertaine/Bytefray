# Bytefray V5 Research Phase R1 — Finite Process Mortality as a Differential Gameplay Experiment

**Status:** Phase R1 Controlled Experiment (Staged: R1A control verification, R1B diagnostic subset; R1C gate NOT passed)
**Ruleset(s) Evaluated:** `bytefray-rules-4` (stable control) vs `bytefray-rules-5-r1-alpha1` (experimental, H = 8, 4, 2, 1)
**Execution Baseline Commit:** `303b33f8513a9d656031ccdb177da00cea077ea7`
**Phase 0 Baseline Commit Referenced:** `3830382` (Phase 0 corpus execution), branch history: `3830382 → ab24d27 (research: establish phase 0 baseline) → 303b33f (test: isolate empty-state replay tests)`
**Archival Release Anchor:** `v4.0.0` (`9077b618d12a3eab498af5818a2852a841f49f5b`)

---

## A. Repository Baseline

- **Branch:** `v5-research`.
- **Starting HEAD SHA:** `303b33f8513a9d656031ccdb177da00cea077ea7` (`test(replay): isolate empty-state tests from optional pygame dependency`), one commit ahead of the Phase 0 execution baseline (`3830382` per `docs/research/v5/V5_PHASE0_BASELINE_AND_MEASUREMENT.md`) via `ab24d27` (`research(v5): establish phase 0 baseline and measurement tooling`).
- **Working-tree state at start:** Clean (`git status --short` empty).
- **Upstream relationship:** `v5-research` tracked `origin/v5-research`; both pointed at `303b33f` at the start of R1 (confirmed via `git fetch` + `git log --oneline -1 origin/v5-research`).
- **Project version:** `4.0.0` (`pyproject.toml`), unchanged throughout R1.
- **Release anchor:** `v4.0.0` (`9077b618d12a3eab498af5818a2852a841f49f5b`), unchanged.
- **Stable V4 control identity confirmed unchanged:** `bytefray-rules-4` (`RULESET_V4` in `engine/src/battle_engine/ruleset_policy.py`) — process core size 8, Q=8, D=1, seeded core placement, round-robin process selection, entrant-wide sensor fusion, static process declarations, no dynamic replication, no permanent process death. Verified both by direct code inspection (Section B below) and by the R1A control-equivalence gate (Section F).
- **Git discipline:** No commits, staging, rebases, resets, or history mutation were performed during R1. All git operations were read-only inspection (`status`, `log`, `fetch`, `rev-parse`, `diff`). The working tree at the end of R1 contains only the source/test edits and new files listed in Section E and the completion report; no `runs/` artifacts are tracked (matches `.gitignore`'s existing `runs/` exclusion, unchanged from Phase 0's convention).

---

## B. Question and Hypotheses

**Primary research question (from the governing prompt, restated precisely):**

> Does finite process mortality materially improve conversion of spatial/process combat into progress against the actual victory objective, especially in repair/disruption stalemates, without merely replacing those stalemates with process-extinction pathologies or destabilizing otherwise healthy matches?

**Primary hypothesis under test:** V4's immortal processes plus D=1 temporary disruption allow defenders to repeatedly resume repair/defense indefinitely. Giving processes finite cumulative integrity may let sustained spatial combat create permanent tactical consequences and therefore increase durable pressure on the enemy core.

**Competing explanations kept alive throughout (per the governing prompt, Section 5):**

1. Mortality may merely punish low-process-count agents.
2. Mortality may make Quorum even more dominant.
3. Mortality may create inert entrants with intact cores.
4. Mortality may shorten matches without improving core-objective gameplay.
5. Repair throughput rather than immortality may be the actual cause.
6. Q=8 quota redistribution may dominate the effect.
7. Search/contact failure is unrelated to mortality.
8. Process count, specialization, or visibility may be the actual explanatory variable.

**Null-result criteria (pre-declared, per Section 11 of the governing prompt):** a finite-H variant is worth promoting to broader (R1C) validation only if it (a) reduces repair/disruption stalemate, (b) creates more durable core pressure rather than merely more activity, (c) does not win merely by deleting a lone process immediately, (d) does not replace core-capture stalemate with long zero-process/inert timeouts, and (e) does not obviously destroy healthy multi-process behavior. Failing this bar on the diagnostic subset is grounds to stop without running a larger corpus (Section I).

**Result, stated up front:** the primary hypothesis is **not supported** by the R1B diagnostic evidence. Mechanism inspection (Section H) identifies a specific, well-evidenced causal reason: this codebase's existing entrant-wide sensor-fusion rule makes a **dead** process's anchor invisible to the opponent (see Section D.3 for why, and Section K for the exact interaction). In three of the four non-Quorum, non-passive matchups tested — including the flagship `concentrated_attacker` vs `local_defender` matchup Phase 0 named as primary evidence for mortality — this converts an already-unsatisfying repair/disruption stalemate into a **different, arguably worse** stalemate: the defender's lone process dies almost immediately, the attacker loses contact entirely, and the match times out as a tie with the defender's core **fully intact and permanently undefended**. Criterion (d) fails directly and repeatedly. See Section I for the full gate decision.

---

## C. Measurement Refinement

### C.1 The problem with Phase 0's `core_health_series` / `core_damage_dealt`

Phase 0's analyzer (`tools/research/v5/analyzer.py` as it existed before R1) tracked "core health" as a **monotonically decrementing counter**: for every memory-diff whose address falls in a victim's 8 core cells and whose previous owner was that victim, `current_health[victim]` decrements by 1 and never increments back up. This conflates two very different things:

- **Transient damage**: a cell is lost and then repaired by its owner. The counter still shows it as "damaged forever."
- **Repeated transient damage on the same cell**: if a single cell is lost, repaired, and lost again, the counter decrements *twice* for what was, at every instant, never more than a 1-cell deficit.

This is exactly the ambiguity the governing prompt warned about (Section 4): "hundreds of attack events can therefore coexist with zero approach to the simultaneous 8-cell capture condition," and it is not hypothetical — R1's own synthetic test (`engine/tests/test_v5_research_r1_metrics.py::test_damage_repair_cycle_does_not_misreport_as_accumulating_progress`) constructs a real deterministic match where a single core cell cycles damage → repair → damage → repair four times. The legacy metric reports `final_core_health == 4` (looks like the defender is down to half its core, one step from elimination); the true simultaneous deficit never exceeds 1 cell and returns to 0 after every repair (`max_core_deficit == 1`, `full_core_return_count == 3`).

A second, more serious instance of this same class of bug was caught by execution, not test-writing, during R1B itself: the `v4_quorum` vs `v4_quorum` H4/H2/H1 runs showed the loser's core mis-reported as `"survived"` by an early draft of the new metric, while the engine's own `apply_core_capture` had already recorded `alive=False, termination_reason="core_captured"` for that entrant. Root cause: `battle_engine.replay.MemoryDiff` records **merged run-length diffs** (`length > 1` when several adjacent addresses are captured by the same writer within one tick), and a naive ownership tracker that reads only `diff.address` silently misses every cell in `[address+1, address+length)`. `analyze_match` now expands the full `[address, address+length)` range for the new true-ownership tracker (`tools/research/v5/analyzer.py`'s `true_cell_owners`, kept deliberately separate from the legacy `cell_owners` dict so Phase 0's published numbers remain exactly reproducible — see below). A regression test (`test_true_ownership_expands_merged_run_length_diffs`) reproduces the exact failure condition (a two-cell merged run) directly.

### C.2 What R1 adds, and what it deliberately leaves alone

Per the governing prompt's explicit instruction, **no Phase 0 metric was removed or renamed**. `core_health_series`, `final_core_health`, `core_damage_dealt`, `core_damage_events`, `combat_conversion_rate`, and `progress_density_per_100t` are computed by byte-identical code paths and are documented in `MatchAnalysis`'s own docstring as **activity-layer, cumulative ownership-*flip-event* counters — not true simultaneous ownership**. `total_combat_writes`/`core_attack_writes`/`anchor_blast_writes`/`territory_combat_writes` are also unchanged (including their pre-existing double-counting of a single physical write across categories, and their known imprecision versus trace-derived ground truth per Phase 0 Section 13 — this residual gap is unresolved by R1 and is noted again in Section M).

New fields added to `MatchAnalysis` (`tools/research/v5/analyzer.py`):

**State/progress layer** (true, recoverable, per-tick simultaneous ownership):
`core_owned_cells_series`, `core_deficit_series`, `max_core_deficit`, `final_core_deficit`, `core_deficit_area`, `full_core_return_count`, `repair_latencies_ticks`, `longest_damaged_interval_ticks`, `deficit_ever_reached_full`, `core_capture_outcome`.

**Process metrics layer** (derived from the new `ProcessState.alive`/`integrity` replay fields — Section D):
`live_process_count_series`, `process_deaths`, `process_death_events`, `process_extinction_tick`, `mutual_process_extinction`, `entrant_zero_process_ticks`, `entrant_ever_alive_with_zero_processes`, `ticks_first_process_death_to_own_core_capture`, `ticks_full_extinction_to_own_core_capture`.

### C.3 A residual, inherited limitation (disclosed, not fixed)

The new state/progress metrics are still **end-of-tick snapshots**, exactly like every other replay-derived measurement in this codebase (Phase 0 Section 13 already documents this boundary for rejected-action/sensor visibility). A cell that is captured and re-repaired **within the same tick** (possible since a process can receive multiple of its entrant's Q=8 action slots in one tick) is invisible to both the legacy and the new metric — only inter-tick recovery is observed. This was directly visible in the `v4_defender_scout` self-play diagnostic match (Section G/H): `core_deficit_area` is nearly identical between the V4 control (a genuinely cycling damage/repair pattern) and the H=1..8 variants (a single permanent loss after the repairer process dies) — `core_deficit_area` alone cannot distinguish a healthy repair cycle from a permanently unrepaired wound; only combined with `full_core_return_count`, `repair_latencies_ticks`, and the process-economy fields does the true mechanism become visible. This is exactly why Section H below reports these fields together per match rather than any single aggregate.

---

## D. Experimental Mechanic

### D.1 Semantics

Each process begins with finite integer `integrity = H`. A **hostile applied write** to that process's **current** anchor:

1. Applies V4's normal D=1 anchor-disruption effect (unchanged).
2. Decrements the process's `integrity` by exactly 1.
3. If `integrity <= 0`, the process **permanently dies**: `alive = False` forever, recorded once (`telemetry.died_tick`).

Integrity does not regenerate. Only a hostile, **applied** (not out-of-reach, not rejected/invalid), **currently-anchored** (not stale), **enemy** (not friendly) write counts — this is exactly the codebase's pre-existing V4 disruption-application block (`ProcessMatchController`'s `WRITE` branch, the `other_p.position == target_addr` check), so no new "did this write really hit the anchor" logic needed inventing; the integrity decrement was added as one extra line inside the block that already correctly implements every one of the governing prompt's exclusions (Section 6).

A dead process:
- executes no further actions (excluded from `_effective_process_quotas`'s `eligible` list, so it also never receives Q=8 share and never occupies a `_select_active_process` slot);
- performs no sensing and contributes no observation reach (excluded from `_visible_enemy_anchors`'s `observers` list);
- is **also excluded as a visible target** — `_visible_enemy_anchors`'s `enemy_positions` set only includes `process.alive` processes. This specific design choice (a dead process's last position stops being a detectable contact for the *opponent*, not only for its own team) turned out to be mechanically decisive — see Section K;
- cannot be disrupted again or accrue further integrity loss (`if not other_p.alive: continue` guards the disruption block);
- cannot revive (nothing sets `alive` back to `True` mid-match; `reset()` only runs once at match construction).

An entrant with zero live processes is **not** automatically eliminated. Core capture remains the only mechanism that kills an entrant (`apply_core_capture`, entirely untouched by R1). This was verified directly: `engine/tests/test_process_mortality.py::test_process_dies_after_h_hostile_anchor_hits_and_entrant_survives` constructs exactly this scenario and asserts `controller.states[1].alive is True` after the victim's sole process dies with its core untouched.

### D.2 Variants tested

`H ∈ {8, 4, 2, 1}` under the experimental Ruleset; `H = ∞` is literally the existing stable V4 control (no experimental code path at all) rather than a fifth "immortal" mode inside the experimental Ruleset — this was a deliberate design simplification (Section E) that also directly produces the R1A control-equivalence evidence.

### D.3 Why entrant-wide sensor fusion matters here

V4's `_visible_enemy_anchors` implements *entrant-wide* fusion: if **any** eligible friendly process can see an enemy anchor, **every** sibling process receives that contact. R1 extended the existing `not process.is_disrupted(tick)` eligibility filter with `and process.alive` on both sides of this function (the observer side and the target side) as the smallest, most literal reading of "a dead process contributes no observation reach" and "a dead process is no longer a live process for any team's purposes" — not as a deliberate design bet that this would matter to the outcome. Section K explains why this reading, not mortality's health-loss arithmetic itself, is the actual proximate cause of R1B's central negative finding, and Section N's recommended follow-up targets exactly this design axis.

---

## E. Implementation Boundary (why stable V4 is unaffected)

Following the codebase's established Ruleset-ID-gated-frozenset-predicate pattern (used three times previously — V2 vulnerable/observable core, V3 locality, V4 scheduler/placement/process-selection — and documented in each of those mechanics' own module comments):

- **New Ruleset identity:** `BYTEFRAY_RULESET_V5_R1_ALPHA1_ID = "bytefray-rules-5-r1-alpha1"` (`engine/src/battle_engine/rules.py`), spelled `-r1-alpha1` per the project's bump policy (an unproven single-phase hypothesis, never a bare `bytefray-rules-5`).
- **New `RulesetPolicy`:** `RULESET_V5_R1_ALPHA1` (`ruleset_policy.py`), every field copied verbatim from `RULESET_V4` except `ruleset_id` — asserted by `test_r1_ruleset_equivalent_to_v4_except_identity_and_mortality_gate`, which iterates `dataclasses.fields(RULESET_V4)` and compares each one.
- **Registered** in `_RULESET_POLICIES` (so `resolve_ruleset_policy` accepts it) and in `PROCESS_RULESET_IDS` (so it dispatches to `ProcessMatchController`, not the Agent-API-v1 Python runtime).
- **Never added** to `OMITTED_RULESET_CANDIDATES` — an omitted `--ruleset`/`ruleset_id=None` request still resolves Agent API v2 rosters to stable `bytefray-rules-4`, verified by both the pre-existing `test_v4_runtime_default_ruleset.py`/`test_ruleset_policy.py` suites (unmodified, still passing) and a new explicit assertion (`test_r1_ruleset_never_reachable_from_omitted_selection`).
- **Mortality mechanic** lives entirely in `battle_engine/process_runtime.py`, gated by `PROCESS_MORTALITY_RULESET_IDS`/`has_process_mortality(ruleset_id)` — a frozenset + predicate exactly mirroring `python_runtime.py`'s `VULNERABLE_CORE_RULESET_IDS`/`has_vulnerable_core`. `ProcessMatchController.mortality_active` is resolved once at `__init__` and is `False` for every other Ruleset regardless of what a caller passes as `process_integrity` (verified directly: `test_stable_v4_is_immortal_even_if_process_integrity_is_passed`).
- **New optional request parameter:** `MatchRequest.process_integrity: int | None = None` (`match_service.py`), resolved by `_resolve_process_integrity` exactly mirroring the existing `locality_reach`/`_resolve_locality_reach` pattern (`None` unless the resolved Ruleset supports mortality; defaults to `DEFAULT_PROCESS_INTEGRITY = 8` when a mortality Ruleset is selected without naming one). Folded into `_reproducibility()`'s payload (and therefore `match_id`/`result_id`/`replay_id` hashing) only when non-`None`, so no historical match identity changes.
- **Replay additivity:** `replay.ProcessState` gained `alive: bool = True` and `integrity: int | None = None`, serialized **only when non-default** (`alive` omitted unless `False`; `integrity` omitted unless not `None`) — the same discipline `AgentState.locus` already established for V3 locality. `_build_process_result`'s per-process metadata dict gains `alive`/`integrity_remaining`/`died_tick` keys **only when `controller.mortality_active`**.
- **Result:** a stable-V4 replay or result produced by the R1-modified codebase is **byte-for-byte identical** to one produced before R1 existed. This is not asserted only by inspection — it is proven in Section F.

---

## F. R1A: Control/Instrumentation Verification

Three checks, run in order, gating everything after them (per the governing prompt: "If instrumentation changes stable gameplay, stop and fix that before continuing").

**Step 1 — re-analyze all 288 frozen Phase 0 replays with the upgraded analyzer.** `runs/v5_phase0_corpus/stage1_replays/*/replay.jsonl` (untracked, on-disk from the Phase 0 run; confirmed to match Phase 0's published aggregate — 60.42% timeout, 43.75% tie — before touching anything) were re-analyzed with the post-R1 `analyze_match`.
- Outcome-field (`winner`, `result_reason`, `actual_ticks`, `is_tie`, `is_timeout`, `entrant_order`) mismatches vs. the original `stage1_metrics.jsonl`: **0 / 288**.
- Mortality-field pollution on stable-V4 data (`process_deaths != 0`, `mutual_process_extinction != False`, or `live_process_count_series` not constant at the declared count): **0 / 288**.
- New-analyzer aggregate: timeout 60.42%, tie 43.75% — **identical** to the Phase 0 doc's published figures.

**Step 2 — re-run a deterministic 5-match sample under the current (R1-modified) codebase with plain `bytefray-rules-4`, diff against the frozen Phase 0 bytes.** Sample: `v4_claimer` vs `v4_quorum` seed 6; `v4_concentrated_attacker` vs `v4_local_defender` seed 1; `v4_quorum` vs `v4_quorum` seed 1; `v4_scout` vs `v4_local_defender` seed 6; `v4_concentrated_attacker` vs `v4_concentrated_attacker` seed 1 (chosen to cover every R1B diagnostic category — Section G). **5/5 byte-identical** (13,934 B / 1,167,224 B / 134,382 B / 1,106,044 B / 680,276 B respectively).

**Step 3 — determinism.** The first sample match was re-run twice under current code; replay bytes were identical.

**Command:** `python tools/research/v5/analyzer.py <replay> --result <result.json>` per match, driven by a verification script equivalent to re-invoking `tools.research.v5.corpus_runner.run_single_match(..., ruleset_id="bytefray-rules-4")` for Step 2/3.

**R1A verdict: PASSED, all three steps.** R1 proceeded to R1B.

---

## G. R1B: Diagnostic Corpus — Selection

### G.1 Selection method (`tools/research/v5/r1_selection.py`)

Six categories are selected **machine-deterministically** from `runs/v5_phase0_corpus/stage1_metrics.jsonl` (the frozen, on-disk Phase 0 288-match corpus — same execution the Phase 0 doc's aggregate table is built from), by a pre-declared metric per category, ties broken lexicographically by `(agent_a, agent_b, seed)` so selection never depends on file iteration order. A category already claimed does not get claimed again by a later rule (the six are always distinct):

| Category | Selection rule | Rationale |
|---|---|---|
| `repair_churn` | max `Σ core_attack_writes` among **timeouts** | "High core interaction + timeout/no capture" |
| `disruption_churn` | max `Σ total_disruptions_received` among **timeouts** | "High anchor disruption + poor core conversion" |
| `passive_stagnation` | min `Σ total_combat_writes` over the whole corpus | Negative control: mortality should not "solve" a match with no contact |
| `healthy_decisive` | min `actual_ticks` among **decisive** (non-tie, non-timeout) matches | Fast core-capture control |
| `multi_process_coordination` | Quorum self-play preferred, else any Quorum match | Multi-process coordination control |
| `slow_eventual_conversion` | max `actual_ticks` among **decisive** matches | Reaches the objective, but only late |

A 7th match, `named_reference_siege_vs_turtle` (`v4_concentrated_attacker` vs `v4_local_defender`, seed 1), was added **by explicit name**, not by re-tuning the `repair_churn` formula. The pre-declared `repair_churn` metric (raw `core_attack_writes` sum) ranks `v4_defender_scout` self-play above this matchup (14,897 vs 7,902 — `defender_scout`'s dual-process mutual harassment produces roughly double the aggregate of the one-sided `concentrated_attacker`→`local_defender` siege, since `local_defender` never attacks back). Per the standing research-integrity rule against discovering a selection threshold/formula and then re-tuning it against the very result it is meant to evaluate, the formula was **not** adjusted to force this specific matchup to the top. Since the governing prompt names it explicitly as Phase 0's flagship case, it is included as a 7th, separately-labeled reference match instead.

### G.2 Selected matches, exact reproduction inputs

All seven ran under `ruleset_id="bytefray-rules-4"` (control) and `ruleset_id="bytefray-rules-5-r1-alpha1"` (H=8, 4, 2, 1), `arena_size=512`, `max_ticks=1000`, `instr_per_tick=8` — identical to every input the Phase 0 corpus already used, so the control side is directly comparable to Phase 0's published per-match data, not merely to itself.

| Category | agent_a | agent_b | seed |
|---|---|---|---|
| `repair_churn` | `v4_defender_scout` | `v4_defender_scout` | 3 |
| `disruption_churn` | `v4_scout` | `v4_local_defender` | 6 |
| `passive_stagnation` | `v4_concentrated_attacker` | `v4_concentrated_attacker` | 1 |
| `healthy_decisive` | `v4_claimer` | `v4_quorum` | 6 |
| `multi_process_coordination` | `v4_quorum` | `v4_quorum` | 1 |
| `slow_eventual_conversion` | `v4_claimer` | `v4_concentrated_attacker` | 7 |
| `named_reference_siege_vs_turtle` | `v4_concentrated_attacker` | `v4_local_defender` | 1 |

**Commands:**
```
python -m tools.research.v5.r1_selection --stage1-metrics runs/v5_phase0_corpus/stage1_metrics.jsonl
python -m tools.research.v5.r1_runner --output runs/v5_r1_diagnostic --h-values 8 4 2 1
```
The control side of each of the 7 matches was **re-run fresh** under the R1-modified codebase (not reused from Phase 0's frozen replay) for a self-consistent 35-match dataset generated in one pass; Section F already establishes that a fresh control run is byte-identical to the frozen Phase 0 run for the same inputs, so this substitution changes nothing material. 35 matches total (7 × [control + 4 H values]) executed in 13.5 seconds.

---

## H. R1B Results

All numbers below are exact, taken directly from `runs/v5_r1_diagnostic/r1b_manifest.json` (re-derivable via the commands in G.2). "B" is `agent_b` in every row of Section G.2's table.

### H.1 `named_reference_siege_vs_turtle` (concentrated_attacker vs local_defender, seed 1) — Phase 0's flagship case

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | tie, tick_limit, 1000t | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `total_combat_writes` A | 15,804 | 16 | 8 | 4 | 2 |
| `core_capture_outcome` B | survived | survived | survived | survived | survived |
| `max_core_deficit` B | 1 | 1 | 1 | 1 | 1 |
| `process_deaths` B | 0 | 1 | 1 | 1 | 1 |
| `process_extinction_tick` B | — | 14 | 13 | 13 | 13 |
| `entrant_zero_process_ticks` B | 0 | 987 | 988 | 988 | 988 |

**Mechanism:** across every finite H, B's lone process dies within 13–14 ticks. From that point, A's `total_combat_writes` collapses from 15,804 (control) to single digits — A stops attacking almost entirely for the remaining ~986 ticks (`passive_stagnation_ticks` jumps from 0 to 937–938). B's core sits at a permanent 1-cell deficit, never captured, for a defenseless entrant with zero live processes for ~988 of 1000 ticks. **Outcome does not change (still a tie); the mechanism of the stalemate changes from "infinite repair churn" to "attacker loses contact with an inert corpse."**

### H.2 `disruption_churn` (scout vs local_defender, seed 6)

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `total_combat_writes` A | 7,998 | 16 | 8 | 4 | 2 |
| `process_extinction_tick` B | — | 3 | 2 | 2 | 2 |
| `entrant_zero_process_ticks` B | 0 | 998 | 999 | 999 | 999 |
| `core_capture_outcome` B | survived | survived | survived | survived | survived |

Identical mechanism to H.1, even more pronounced: B's process dies by tick 2–3; A's activity collapses immediately; B's core (undamaged the whole match, `max_core_deficit=1` throughout, matching the control) sits untouched and undefended for essentially the entire match.

### H.3 `slow_eventual_conversion` (claimer vs concentrated_attacker, seed 7)

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | **B wins**, last_agent_standing, 999t | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `core_capture_outcome` A | captured | survived | survived | survived | survived |
| `total_combat_writes` B | 8,431 | 9 | 4 | 2 | 1 |
| `process_extinction_tick` A | — | 7 | 6 | 6 | 6 |

**This is the most important single result in R1B.** In the V4 control, B (`concentrated_attacker`) eventually — after 999 ticks of grinding — captures A's core and wins outright. Under **every** tested H, A's lone process dies by tick 6–7 (from the same early contact that, in the control, is the opening move of B's eventual siege), B loses contact and effectively stops acting, and the match ends in a **tie**. Mortality did not merely fail to help here — **it converted a decisive V4 outcome into a stalemate**, for every H value tested. This is a direct instance of failure criterion (d) ("replace core-capture stalemate with long zero-process/inert timeouts") and goes further: it destroys a matchup that was not even a stalemate to begin with.

### H.4 `passive_stagnation` (concentrated_attacker self-play, seed 1) — negative control

Identical across control and all four H values: 0 combat writes, 0 disruptions, tie at 1000 ticks. Mortality has **zero effect** when there is no contact to trigger it — exactly the expected negative-control result (Pathology D, Section 12 of the governing prompt), and evidence that mortality is not a general-purpose "fix" for the independent search-deficit problem Phase 0 also diagnosed.

### H.5 `healthy_decisive` (claimer vs quorum, seed 6)

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | B wins, 5t | B wins, 5t | B wins, 6t | B wins, 6t | B wins, 6t |
| `process_deaths` A | 0 | 0 | 1 | 1 | 1 |

Outcome is unchanged (Quorum wins outright) at every H; H=8 doesn't even trigger a death (Quorum's simultaneous multi-cell write barrage captures A's core before A's single process accumulates 8 hits). H≤4 costs A's process its life a tick or two before capture, one tick later than the control. **Mortality is harmless here** — the one criterion it clearly satisfies.

### H.6 `multi_process_coordination` (quorum vs quorum, seed 1) — the one genuinely positive signal

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | A wins, 60t | A wins, 51t | A wins, 51t | A wins, 50t | A wins, 53t |
| `core_capture_outcome` B | captured | captured | captured | captured | captured |
| `total_combat_writes` A | 492 | 85 | 48 | 25 | 18 |
| `process_deaths` B (of 6) | 0 | 6 | 6 | 6 | 6 |
| `process_extinction_tick` B | — | 14 | 7 | 5 | 3 |
| `ticks_full_extinction_to_own_core_capture` B | — | 37 | 44 | 45 | 50 |

B goes **fully extinct** (all 6 processes dead) within 3–14 ticks under every H, yet A still **completes** the core capture in every case — 7–10 ticks faster than the V4 control, using 5–27× fewer combat writes. This is the desired mechanism (combat → attrition → durable pressure → capture) actually occurring, and it is the only diagnostic match where it does. Critically, **extinction-to-capture latency is large** (37–50 ticks) even against a fully defenseless opponent — A's own Q=8 throughput, spread across its several remaining processes, is the bottleneck, not any resistance from B. This was *already a healthy, decisive V4 matchup*; mortality's contribution here is a modest efficiency gain on a case that did not need fixing, not evidence that mortality solves Phase 0's targeted stalemate problem.

### H.7 `repair_churn` (defender_scout self-play, seed 3)

| | control | H=8 | H=4 | H=2 | H=1 |
|---|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `max_core_deficit` A/B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| `core_deficit_area` A/B | 997/992 | 997/992 | 997/992 | 997/993 | 997/993 |
| `total_combat_writes` A/B | 15,376/15,412 | 17/16 | 9/8 | 4/4 | 2/2 |
| `live_process_count_final` A/B | 2/2 | 1/1 | 1/1 | 1/1 | 1/1 |

Both entrants' `"defender"` sub-process dies early (tick 4–9); both retain their `"scout"` sub-process, so **neither entrant goes fully extinct** and the invisibility pathology (H.1–H.3) does not trigger here. But the surviving `"scout"` sub-process apparently does not take over repair duty: `core_deficit_area` is nearly **identical** between control (a genuinely cycling damage/repair pattern, confirmed by `full_core_return_count=0` even in the control — Section C.3's caveat) and every H variant (a single permanent, never-repaired 1-cell loss after the defender dies). Combat collapses from ~15,400 writes to single digits either way. **Neither the control nor any mortality variant ever converts this matchup to a decisive result within 1000 ticks** — mortality changes the texture of the stalemate (permanent vs. cycling) without moving it any closer to actual capture. This is also a **specialization-fragility observation**: killing one role-specialized process can silently disable a specific function (repair) for the rest of the match without the entrant going extinct or the match outcome changing.

### H.8 Stratification by initial process count (Section 10's required "balance/structure" cut)

- **1-process agents** (`claimer`, `concentrated_attacker`, `local_defender`, `scout`, one side of `defender_scout`'s two roles): catastrophically fragile under every tested H. A single early exchange permanently disables the entire entrant's action capacity. This directly confirms competing explanation "mortality may merely punish low-process-count agents" (Section B item 1).
- **2-process agents** (`defender_scout`): partial degradation (Section H.7) — loses a *function*, not total capacity, but that function loss is permanent and produces no different match outcome.
- **6-process agents** (`quorum`): the only agent whose core capture actually completes after full extinction, purely because the *opponent's own* surviving process count remained high enough to finish the job — i.e., what matters is not the victim's process count alone but whether the *attacker* retains enough capacity and (per Section K) enough persistent knowledge of the target to finish converting.

---

## I. R1C Gate Decision

Evaluated against the five pre-declared promotion criteria (Section B / governing prompt Section 11), per matchup:

| Criterion | named_reference | disruption_churn | slow_eventual_conversion | passive_stagnation | healthy_decisive | multi_process_coordination | repair_churn |
|---|---|---|---|---|---|---|---|
| (a) reduces repair/disruption stalemate | **NO** (still tie) | **NO** (still tie) | **NO** (was a win, now a tie) | n/a (no stalemate present) | n/a | n/a (was already healthy) | **NO** (still tie) |
| (b) more durable pressure, not just activity | **NO** (deficit unchanged) | **NO** | **NO** | n/a | n/a | **YES** | **NO** (deficit unchanged) |
| (c) doesn't just win by deleting a lone process | **N/A — doesn't win at all** | N/A | N/A | n/a | yes (harmless) | yes (also converts) | N/A |
| (d) no long zero-process/inert timeouts | **FAILS** (987–988 zero-process ticks) | **FAILS** (998–999) | **FAILS** (994–995) | n/a | n/a | n/a (converts) | passes (never fully extinct) |
| (e) doesn't destroy healthy behavior | n/a | n/a | **FAILS** (destroys a healthy win) | n/a | passes | passes | n/a |

**DO NOT PROMOTE TO BROADER VALIDATION.**

Of the four matchups Phase 0 identified as evidence *for* mortality (the repair-churn, disruption-churn, and slow-conversion pathologies), **none** were improved by any tested H, and one previously-decisive matchup was actively **destroyed** into a stalemate. The single matchup where mortality clearly helped (`quorum` vs `quorum`) was not one of the matchups the hypothesis was chartered to fix. Per the governing prompt's explicit instruction ("If no finite-H variant meets that standard: STOP... Do not run a larger corpus just to obtain more data"), R1C (the full 288-match paired corpus) was **not executed**.

---

## J. R1C Results

Not applicable — the R1C gate was not passed (Section I).

---

## K. Failure Modes

- **Inert zero-process entrants (Pathology A, confirmed and generalized).** Observed in `named_reference_siege_vs_turtle`, `disruption_churn`, and `slow_eventual_conversion`: a single hostile hit sequence (occurring within the first 1–14 ticks against any single-process agent under H≤8) kills the lone process; the entrant survives (core untouched) but can never act again. The governing prompt anticipated this exact shape ("single hostile anchor hit → only process dies → entrant becomes inert → opponent eventually cleans up core") but the R1B evidence shows the second half of that sentence **does not happen** here: the opponent does *not* eventually clean up the core, in three of three cases where a single-process agent was on the attacking side. The specific, evidenced cause: `_visible_enemy_anchors` excludes dead processes from the `enemy_positions` set an opponent's observers scan (Section D.3). Once a single-process agent's sole target dies, that agent's action policy — which, based on the observed collapse in `total_combat_writes` immediately following each death, evidently depends on *continuing* to observe the opponent's anchor to choose where to write next — has nothing left to react to, and effectively goes idle for the remainder of the match. This was not independently re-derived from each bundled agent's source in this phase (a scope-preserving choice — R1's mandate is the mortality mechanic, not an agent-behavior audit); it is inferred from the direct behavioral evidence (combat activity collapsing to near-zero at the exact tick of the opponent's extinction, in lockstep, across three unrelated matchups) and is flagged here as an inference, not a verified code-level fact about each bundled agent.
- **Mutual process extinction.** Not observed in the natural 7-match diagnostic set (no matchup drove both sides to zero processes), but confirmed possible and correctly instrumented by a dedicated unit test (`test_mutual_process_extinction_detected`) using a third bystander entrant that kills two other single-process entrants simultaneously — `mutual_process_extinction: True`, `entrant_ever_alive_with_zero_processes: {both: True}`, both cores left intact. A second unit test (`test_symmetric_mutual_attack_produces_asymmetric_kill_by_schedule_order`) additionally uncovered that when two single-process entrants attack each other directly under low H, the outcome is **not** mutual extinction but a strict **first-mover kill**: the chunked round-robin scheduler executes one entrant's full action chunk before the other's, so under H≤2 the first-scheduled entrant's process kills the second before the second's process ever acts. This is a genuine, scheduler-order-dependent asymmetry worth flagging as its own follow-up concern if mortality is ever revisited (a symmetric-looking matchup can have a schedule-order-determined, not skill-determined, winner at very low H).
- **Single-process fragility.** Confirmed structurally (Section H.8): every 1-process bundled agent that took any hit at all under H≤8 lost 100% of its action capacity, permanently, usually within the first 1–14 ticks of contact.
- **Quorum amplification.** Not observed in the direction anticipated ("mortality may make Quorum even more dominant" — competing explanation #2). Quorum's control win rate against the field was already 87.5% (Phase 0); the one Quorum matchup tested here (self-play) shows mortality producing a *faster, cheaper* win for whichever side is ahead, not a change in who wins. This is a plausible amplifier of an *existing* skill gap rather than a new source of dominance, but R1B's single Quorum-involved diagnostic match (self-play, symmetric agents) cannot distinguish "Quorum specifically benefits" from "any already-superior multi-process side benefits" — recorded as an open question, not resolved.
- **Passive no-contact matches.** Confirmed completely unaffected (`passive_stagnation`, Section H.4) — mortality is inert when there is no contact, which is expected and not itself a defect.

---

## L. Candidate Evidence Update

| Candidate | Status | Basis |
|---|---|---|
| **Process mortality** | **CONTRADICTED** | Phase 0 rated this "STRONG SUPPORT" on the strength of the `concentrated_attacker`/`local_defender` siege case. R1B directly tested that exact matchup (plus two structurally similar ones) and found finite integrity does not convert any of them to decisive capture at any tested H; it converts one previously-*decisive* matchup into a stalemate. The evidentiary basis for "STRONG SUPPORT" is directly falsified by controlled experiment, not merely left untested. |
| Replication / deployment | NOT TESTED | Held constant by design (candidate-variable discipline, governing prompt Section 13). |
| Capacity economics | NOT TESTED | Held constant by design. |
| Specialization | SUPPORT UNCHANGED | R1 was not a controlled specialization experiment. The `repair_churn` observation (Section H.7 — killing a role-specialized process silently disables a specific function without eliminating the entrant) is a genuine, newly-surfaced *risk* of combining mortality with role specialization, but it is a side-observation from a mortality-focused run, not an isolated test of specialization itself; recorded as a note, not a formal update to this candidate's tier. |
| Process-local information / entrant-wide sensor fusion | SUPPORT UNCHANGED (formal tier) — **but see the explicit new candidate below** | Phase 0's "Process-Local Information" candidate was about decentralized flanking from per-process (rather than entrant-wide) sensing — a different question from the one R1B's evidence actually bears on. Per the standing instruction not to infer support merely because a topic sounds related, this tier is left unchanged; the actual new finding is recorded as its own item. |
| *(new, not in Phase 0's original table)* Opponent-visibility persistence independent of process liveness | **NEW CANDIDATE — STRONG SUPPORT FOR FURTHER STUDY** | Section K's mechanism finding: the proximate cause of R1B's central negative result is that a dead process's last-known position vanishes from the opponent's `_visible_enemy_anchors` result, not the integrity-loss arithmetic itself. This is a distinct, narrowly-scoped, directly testable variable (see Section N). |
| V4 process core size = 8 | NOT TESTED | Held constant by design. |
| Territory incentives | NOT TESTED | Held constant by design. |

---

## M. Validation

**Focused tests (all new, all passing):**
- `engine/tests/test_process_mortality.py` — 12 tests: Ruleset registration/isolation/field-equivalence, the mortality mechanic itself (death timing, entrant survival with zero processes, no re-disruption after death, quota/observation exclusion, immortality under stable V4 even with a stray `process_integrity`, configuration validation and defaulting), and full-stack replay/result persistence including a byte-compatibility proof for stable V4.
- `engine/tests/test_v5_research_r1_metrics.py` — 6 tests: the damage→repair→damage→repair misreporting proof (Section C.1), the merged-run-length ownership-tracking regression (Section C.1), real process-death/extinction/zero-process-while-alive metrics from live mortality matches, the scheduler-order first-mover finding (Section K), genuine mutual extinction via a bystander construction, and analyzer determinism with the new fields present.

**V4 regression/equivalence:** R1A (Section F) is itself the regression gate the governing prompt calls for in Section 15 — 0/288 outcome mismatches on re-analysis, 5/5 byte-identical fresh reruns against frozen Phase 0 replays, confirmed determinism. In addition, the pre-existing `test_v4_stable_ruleset_equivalence.py`, `test_v4_runtime_default_ruleset.py`, and `test_ruleset_policy.py` suites (entirely unmodified by R1) all still pass.

**Full suite:** `pytest` across all three configured `testpaths` (`_legacy/tests`, `engine/tests`, `client/tests` — the true full suite per `pytest.ini`, not `engine/tests` alone) — **3024 tests, 0 failures, 0 errors, 14 skipped**, 326.9s, exit code 0 (JUnit XML confirmed: `errors="0" failures="0" skipped="14" tests="3024"`). This grew from Phase 0's documented 2,992 by R1's ~32 new tests.

One test (`test_agent_evaluation_parallel.py::test_resume_after_coordinator_interruption_matches_uninterrupted_reference`) failed once under a separate, earlier full-suite invocation with a Windows `PermissionError` on a temp-file rename, and passed cleanly in isolation immediately after. This is a pre-existing, unrelated Windows file-locking flake (not caused by any R1 change — none of R1's edits touch that test's coordinator/evaluation-resume code path) and did not recur in the final full-suite run reported above.

**Ruff:** `ruff check .` — all checks passed (one round of auto-fixable `RUF100` unused-`noqa` findings in the new `tools/research/v5/r1_runner.py`, from an unnecessary `# noqa: E402` copied from a different file's style; fixed via `ruff check . --fix` and re-verified).

**Mypy:** `mypy engine/src/battle_engine` — 0 errors, 102 source files. `mypy client/src/battle_client` — 0 errors, 16 source files. (`tools/research/v5` is not part of the repository's established mypy gate per Phase 0's own validation section; an informational run against it hit a pre-existing, unrelated module-path-resolution quirk when invoked directly against that subdirectory outside its normal package context, not a type error in R1's code.)

**Determinism:** proven at three levels — engine-level (`test_full_stack_process_mortality_is_deterministic`, identical analyzer output byte-for-byte across two independent runs of the same H/seed/pairing), R1A-level (Section F Step 3), and the pre-existing analyzer determinism test (`test_analyzer_deterministic_output`, unmodified, still passing).

---

## N. Final Verdict

**5. MORTALITY REJECTED**

Scoped precisely: this specific mechanic (permanent process death on cumulative hostile-anchor-hit count, combined with this codebase's existing entrant-wide sensor-fusion rule that makes a dead process's anchor invisible to the opponent) does not solve — and in the majority of tested cases actively worsens — the repair/disruption stalemate problem it was designed to address. It is not merely inconclusive: the flagship matchup Phase 0 named as primary evidence, plus two structurally similar ones (including one previously-*decisive* matchup), all degrade into permanent, undefended, zero-process stalemates under every tested H. The one clearly positive result (Quorum self-play) was already a healthy matchup and does not provide evidence that the targeted problem is solved.

This verdict does **not** claim finite process integrity is inherently unworkable as a concept — Section K's mechanism analysis isolates a specific, narrow, and independently testable design interaction (opponent-visibility tied to process liveness) as the likely actual blocker, distinct from the integrity-loss arithmetic itself.

**Recommended next research question (single, per the governing prompt's instruction to name exactly one or recommend termination):**

> Does decoupling opponent-visibility from process liveness — for example, an intrinsically observable per-entrant core signal independent of any process's own sensor reach, closely analogous to this codebase's existing V2/V3 "observable core beacon" precedent (`python_runtime.has_observable_core`) — restore attacker follow-through against a mortality-disabled defender? If so, that isolates the sensor-fusion design (not mortality itself) as Phase 0's actual blocker; if the stalemate persists even with persistent visibility, that would be much stronger evidence against process mortality as a useful lever for this problem than R1 alone provides, since it would rule out the one specific confound R1B's mechanism inspection identified.

If this follow-up is not pursued, the alternative is to terminate the process-mortality research line: R1B's evidence gives no basis, as currently designed, for further investment in it.
