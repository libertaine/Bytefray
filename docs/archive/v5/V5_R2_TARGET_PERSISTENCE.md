# Bytefray V5 Research Phase R2 — Target Persistence and Objective Awareness as a Causal Experiment

**Status:** Phase R2 Controlled Experiment (Staged: R2A control verification PASSED, R2B four-arm diagnostic executed; R2C gate NOT passed)
**Ruleset(s) Evaluated:** `bytefray-rules-4` (stable control) · `bytefray-rules-5-r2-alpha1` (new, oracle-capable, no mortality) · `bytefray-rules-5-r1-alpha1` (R1's mortality identity, with and without the new oracle option)
**Execution Baseline Commit:** `18e5ac610417bf4e41bef3391c8dbe8483a7d771`
**R1 Commit:** `18e5ac6` (`research(v5): evaluate and reject finite process mortality`)
**Archival Release Anchor:** `v4.0.0` (`9077b618d12a3eab498af5818a2852a841f49f5b`)

---

## A. Baseline

- **Branch:** `v5-research`.
- **Starting HEAD SHA:** `18e5ac610417bf4e41bef3391c8dbe8483a7d771`.
- **Working-tree state at start:** Clean (`git status --short` empty).
- **Upstream relationship:** `v5-research` and `origin/v5-research` both at `18e5ac6` at the start of R2 (`git rev-parse origin/v5-research`).
- **R1 present in branch history:** yes — `18e5ac6` is R1's own commit; the branch reads `3830382 → ab24d27 (Phase 0) → 303b33f → 18e5ac6 (R1)`.
- **Project version:** `4.0.0` (`pyproject.toml`), unchanged throughout R2.
- **Stable V4 control identity confirmed unchanged:** `bytefray-rules-4` (`RULESET_V4`) — process core size 8, Q=8, D=1, seeded core placement, round-robin process selection, entrant-wide sensor fusion, static process declarations, no process mortality, no dynamic replication. Verified by code inspection (Section E) and proven by the R2A control gate (Section H).
- **Git discipline:** no commits, staging, rebases, resets, or history mutation were performed during R2. All git operations were read-only (`status`, `log`, `rev-parse`, `diff`). No `runs/` artifacts are tracked (`.gitignore` excludes `runs/`, unchanged).
- **CI/GitHub baseline:** not consulted; no web/GitHub mutation was performed, per the charter. Local validation is reported in full in Section Q.

---

## B. The R1 Finding That Motivates R2

R1 rejected finite process mortality. Its central negative result was not that mortality merely failed to help, but that it produced a *specific* and repeatable degeneration:

```
combat finds enemy
-> enemy process is permanently killed
-> dead process disappears from the opponent's observation
-> enemy entrant still has an intact core
-> attacker loses useful target information
-> attacker stops applying pressure
-> zero-process, intact-core stalemate
```

R1's Section K located the proximate mechanism in `ProcessMatchController._visible_enemy_anchors`: the `enemy_positions` set an observer scans contains only `process.alive` processes, so a dead process's last position stops being a detectable contact **for the opponent**, not merely for its own team. R1 flagged this explicitly as an *inference* from behavioural evidence (combat activity collapsing to near-zero at the exact tick of the opponent's extinction, in lockstep, across three unrelated matchups), not as a verified code-level fact about each bundled agent.

**R2 upgrades that inference to a verified fact.** Direct inspection of all six bundled V4 agents (Section G) confirms that `observation.visible_enemy_anchor_addresses` is the *only* enemy-target channel any of them reads, and that five of the six act on it directly. When that tuple empties, five of six bundled agents have nothing left to aim at.

R2 tests whether that information loss is causally responsible for the failure to convert combat into core capture.

---

## C. Hypotheses

**H1 — target persistence.** After contact, attackers fail because their target disappears. Restoring persistent target information after process removal should restore objective pressure.

**H2 — objective awareness.** Even without mortality, agents benefit from always knowing where the enemy core is.

**H0 — null.** Target visibility is not the causal blocker; restoring it changes neither pressure nor conversion.

These are kept strictly separate throughout: the four-arm design exists specifically to distinguish them, and Section K reports the deltas that separate them rather than an aggregate win rate.

**Result, stated up front.** H1 is **confirmed for pressure and rejected for conversion**. Restoring persistent target information restores post-extinction objective pressure completely and reproducibly (0 → ~8,000 core-targeting writes; 937–951 ticks of passive stagnation → 0) in every diagnostic case where target loss occurred. It does **not** produce core capture in two of the three target-loss cases: the maximum simultaneous core deficit stays at 1 of 8 and every one of those matches still ends as a 1000-tick tie. H2 is **not supported**: the oracle leaves five of seven matches' outcomes untouched, and where it does change a match it *degrades* it — collapsing the flagship siege's core damage by 99.8% and reversing the winner of a previously decisive matchup. The oracle also destroys the no-contact negative control. R2C is therefore **NOT** promoted.

---

## D. Four-Arm Design

| Arm | Ruleset | Mortality | Oracle | Role |
|---|---|---|---|---|
| **A** | `bytefray-rules-4` | OFF | OFF | Stable V4 permanent control |
| **B** | `bytefray-rules-5-r2-alpha1` | OFF | ON | Objective awareness alone (isolates H2) |
| **C** | `bytefray-rules-5-r1-alpha1`, H=8 | ON | OFF | Reproduces R1's pathology exactly |
| **D** | `bytefray-rules-5-r1-alpha1`, H=8 | ON | ON | The key causal arm (isolates H1) |

Mortality and the oracle are deliberately carried by **two different Ruleset identities**, not by one identity with two switches. Arm B requires oracle-without-mortality, and R1's identity must keep its published semantics exactly; giving R1's identity a mortality "off" switch would have changed R1's own contract. Arm C is therefore bit-for-bit R1's configuration (proven in Section H), which makes R2's own execution double as an R1 regression test.

---

## E. Mortality H\* Selection

The charter forbids picking whichever H makes R2 look best. `tools/research/v5/r2_selection.py` implements a pre-declared, mechanical rule over the **frozen R1B manifest** (`runs/v5_r1_diagnostic/r1b_manifest.json`), the same execution R1's published tables are built from:

1. **Admissibility.** Consider only the finite H values R1 tested (8, 4, 2, 1). Exclude `H = 1` outright: a process with one integrity point dies to the first hostile anchor hit it ever takes, which is precisely the "merely creates immediate first-hit deletion" case the charter excludes.
2. **Pathology reproduction.** For each admissible H, compute the set of `(match, entrant)` pairs exhibiting the *target-loss pathology*: the entrant reached zero live processes, stayed alive with an intact (non-captured) core, and remained so for at least `MIN_PATHOLOGY_ZERO_PROCESS_TICKS = 100` ticks. The tick floor keeps an incidental one-or-two-tick gap immediately before a core capture from being mistaken for the stalemate pathology.
3. **Selection.** Keep only those admissible H whose pathology set is a superset of every other admissible H's, then take the **largest** (least-extreme) survivor — a larger integrity budget absorbs more hits before dying and is therefore the least aggressive instrument that still exposes the condition.

**Applied result (`python -m tools.research.v5.r2_selection`):**

| H | Admissible | Target-loss pathology cases |
|---|---|---|
| 8 | yes | 3 — `claimer_vs_concentrated_attacker:A`, `concentrated_attacker_vs_local_defender:B`, `scout_vs_local_defender:B` |
| 4 | yes | 3 — identical set |
| 2 | yes | 3 — identical set |
| 1 | **no** (first-hit deletion) | — |

All three admissible values reproduce an identical pathology set, so step 3 is decided entirely by "largest".

**H\* = 8.**

Two supporting observations, recorded but *not* used by the rule: H=8's extinction ticks (7, 14, 3) are strictly later than H=1's (6, 13, 2), confirming it genuinely absorbs hits rather than dying on contact; and in R1's `healthy_decisive` match H=8 caused **no** process death at all where H≤4 did, further confirming it is the least aggressive admissible instrument. H\* = 8 coincidentally equals `DEFAULT_PROCESS_INTEGRITY`, but the rule, not the default, selected it.

---

## F. Oracle Semantics

The objective-target oracle is a **diagnostic instrument, not a proposed shipping mechanic.**

**What is exposed.** For each **living** enemy entrant, exactly one address: that entrant's **core base** (`EntrantState.core_base`), the lowest address of its fixed 8-cell victory core. Multiple targets (3+ entrant matches) are sorted ascending.

**When.** Evaluated immediately before every agent callback, exactly like normal visibility. The target is present while enemy processes are alive, after some die, and after *all* die. It is withdrawn the moment the enemy entrant itself is eliminated (`EntrantState.alive` is `False`).

**Independence.** The target deliberately does **not** depend on distance, sensor reach, surviving friendly processes, or surviving enemy processes. No sensing radius or normal process visibility was changed; the detected-anchor computation above it is untouched.

**What is NOT exposed.** No enemy memory, source, future movement, hidden actions, RNG, process intentions, or any other omniscient state. The oracle answers exactly one question: *where is the strategic objective I must ultimately destroy?*

**Ordering.** Oracle addresses are appended **after** the sorted live-anchor tuple, never merged into it, and never duplicate an address already detected. This is a deliberate, declared design choice with a real consequence for interpretation, recorded here *before* the results section: for an agent that reads only element `[0]` (five of the six bundled agents), the oracle acts as a strict **fallback** — it never displaces or suppresses a genuine sighting, and is reached only when real contact is unavailable. For an agent that consumes the whole tuple (`v4_quorum`), the oracle is an additional persistent contact at all times. H2 is therefore probed only weakly for the `[0]`-reading agents while real contact exists, and fully for Quorum. This asymmetry is a declared limitation of the instrument, not a finding.

**A structural constraint declared before results.** Core capture in this engine requires the victim to own **zero** of its 8 core cells (`python_runtime.apply_core_capture`). A single static target address can therefore only ever flip **one** cell. Five of the six bundled agents write at exactly the address they are given; only `v4_quorum` sweeps a region around a target (`_SIEGE_ORDER`). It follows that for most bundled agents the oracle can restore *pressure* but cannot, by construction, produce *capture*. R2's central measurement is accordingly "did the attacker resume objective pressure?", not "did it capture?" — and this limitation is a finding about the interaction of information shape and agent capability, discussed in Sections L, M and R, not a defect worked around by rewriting agents (which the charter forbids).

**Implementation boundary.** The oracle lives entirely in `ProcessMatchController._visible_enemy_anchors`, gated on two independent keys: `OBJECTIVE_TARGET_ORACLE_RULESET_IDS` / `has_objective_target_oracle(ruleset_id)` (Ruleset permission) **and** an explicit per-request opt-in `MatchRequest.objective_target_oracle` (caller intent). Stable `bytefray-rules-4` is absent from the gate set, so no amount of request-level opt-in can activate the instrument under the permanent control Ruleset. Neither new identity is in `OMITTED_RULESET_CANDIDATES`, so normal CLI/GUI use can never silently activate an R2 experiment. Nothing in `Q`, `D`, core size, movement reach, write reach, scoring, territory rules, process allocation, process count, replication, spawning, repair, or victory conditions was modified.

---

## G. Compatibility Adapter

The charter warns against adding a new `enemy_core_location` field no agent reads and then concluding the oracle has no effect. Before implementing anything, all six bundled V4 agents were inspected to determine which observation channel they actually react to:

| Agent | Processes | Enemy-target channel read | Behaviour on a target |
|---|---|---|---|
| `v4_claimer` | 1 | **none** | never reads any enemy channel; moves and paints its own anchor |
| `v4_scout` | 1 | `visible_enemy_anchor_addresses[0]` | writes if already in reach; otherwise drifts (never approaches) |
| `v4_local_defender` | 1 | `visible_enemy_anchor_addresses[0]` | writes if in reach; otherwise returns to own core |
| `v4_concentrated_attacker` | 1 | `visible_enemy_anchor_addresses[0]` | writes if in reach, **else moves toward it** |
| `v4_defender_scout` | 2 | `visible_enemy_anchor_addresses[0]` | defender writes if in reach else guards core; scout writes if in reach else drifts |
| `v4_quorum` | 6 | whole `visible_enemy_anchor_addresses` tuple | records contacts/`core_candidates` memory, moves toward, and **sweeps a region** around targets |

`visible_enemy_anchor_addresses` is the single enemy-target channel in the entire bundled population. The smallest adapter that lets unchanged agents consume the oracle is therefore to inject the objective address into that same channel.

> **R2 target-oracle adapter:** a synthetic objective address (the enemy entrant's core base) is inserted into the legacy target-address observation channel (`visible_enemy_anchor_addresses`), solely so unchanged V4 agents can react to it.

This is explicitly **not** a proposed production API semantic. A core base is not a process anchor, and the channel's normal contract is "currently occupied enemy addresses"; the adapter deliberately violates that contract for diagnostic purposes only, and says so in the code comment at the injection site. No agent source, strategy, or decision logic was modified, and no new agent strategies were added.

**A declared consequence:** `v4_claimer` reads no enemy channel at all, so the oracle is structurally incapable of reaching it. Any match in which `v4_claimer` is the attacker cannot test H1 or H2 on the attacking side. This is called out where it matters in Section J.

---

## H. R2A — Control / Equivalence / Determinism Verification

Three gates, run before any diagnostic match.

**Step 1 — stable V4 is byte-identical to frozen Phase 0.** All seven R2B diagnostic pairings were re-run fresh under the R2-modified codebase with plain `bytefray-rules-4` and diffed (SHA-256) against the frozen Phase 0 replays in `runs/v5_phase0_corpus/stage1_replays/`.

**7 / 7 byte-identical** (13,934 B · 1,167,224 B · 134,382 B · 1,106,044 B · 680,276 B · 1,691,647 B · 1,129,921 B).

**Step 2 — R1 mortality with the oracle disabled is byte-identical to frozen R1.** The same seven pairings re-run under `bytefray-rules-5-r1-alpha1`, H=8, oracle off, diffed against `runs/v5_r1_diagnostic/*/H8/replay.jsonl`.

**7 / 7 byte-identical.** Arm C is therefore literally R1, not an approximation of it.

**Step 3 — the full frozen Phase 0 corpus re-analyzed with the R2 analyzer.** All 288 Phase 0 replays re-analyzed with the R2-upgraded `analyze_match`:

- outcome-field mismatches (`winner`, `result_reason`, `actual_ticks`, `is_tie`, `is_timeout`, `entrant_order`) vs. the original `stage1_metrics.jsonl`: **0 / 288**;
- R2-field pollution on stable-V4 data (any non-zero post-extinction counter, any non-`None` interval, any `attacker_resumes_objective_pressure`): **0 / 288**;
- aggregate: timeout **60.42%**, tie **43.75%** — identical to Phase 0's published figures.

**Step 4 — the oracle changes information only, never a mechanic.** Proven by holding the agents constant against observation: `test_oracle_changes_information_only_not_mechanics` runs both entrants on a fixed script that never reads the observation, so any divergence could only come from the engine's rules. Compared by value with oracle ON vs OFF: score map, full arena bytes, full ownership map, ownership counts, per-entrant liveness / termination reason / action count / core base / core cells, and per-process liveness, integrity, position, reach, quota share, action count, move count, write count, and disruption hits. All identical.

**Step 5 — determinism.** Three levels: the oracle address stream itself is identical across repeated runs (`test_oracle_addresses_are_identical_across_repeated_runs`); a full-stack oracle replay is byte-identical across runs (`test_oracle_full_stack_run_is_deterministic`); and the **entire 28-match R2B analysis payload is byte-identical across two independent executions** of `r2_runner`, including the H\* selection record.

**Step 6 — the instrument is not silently inert.** A guard against reporting a null that is really a no-op: for every one of the seven diagnostic matches, the **gameplay tick stream** (all replay records excluding the header, whose `ruleset_id`/`match_id`/`reproducibility` legitimately differ) was compared between B and A and between D and C. **All 14 comparisons DIFFER.** Every "outcome unchanged" result in Section J is therefore a genuine null, not an oracle that failed to reach the agents.

**R2A verdict: PASSED, all six steps.** R2 proceeded to R2B.

---

## I. Diagnostic Corpus

R2 reuses **R1's exact diagnostic corpus**, by calling R1's own selection module (`tools/research/v5/r1_selection.py`) unmodified rather than re-deriving or re-tuning a new, potentially more favourable set. Agent revisions, slot ordering, seed, arena size (512), max ticks (1000) and `instr_per_tick` (8) are identical to R1 and to Phase 0.

| Category | agent_a | agent_b | seed |
|---|---|---|---|
| `repair_churn` | `v4_defender_scout` | `v4_defender_scout` | 3 |
| `disruption_churn` | `v4_scout` | `v4_local_defender` | 6 |
| `passive_stagnation` | `v4_concentrated_attacker` | `v4_concentrated_attacker` | 1 |
| `healthy_decisive` | `v4_claimer` | `v4_quorum` | 6 |
| `multi_process_coordination` | `v4_quorum` | `v4_quorum` | 1 |
| `slow_eventual_conversion` | `v4_claimer` | `v4_concentrated_attacker` | 7 |
| `named_reference_siege_vs_turtle` | `v4_concentrated_attacker` | `v4_local_defender` | 1 |

**Corpus size: 7 matches × 4 arms = 28 runs**, executed in 10.5 s.

```
python -m tools.research.v5.r2_selection
python -m tools.research.v5.r2_runner --output runs/v5_r2_diagnostic
```

---

## J. Results — Per-Match A/B/C/D

"B" denotes `agent_b` in every row. Outcome/tick figures are exact, taken from `runs/v5_r2_diagnostic/r2b_manifest.json`.

### J.1 `named_reference_siege_vs_turtle` — concentrated_attacker vs local_defender, seed 1 (Phase 0's flagship)

| | A (V4) | B (oracle) | C (H=8) | D (H=8 + oracle) |
|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `core_attack_writes` A | 7,902 | 3,987 | 8 | 7,971 |
| **`core_damage_dealt` A** | **495** | **1** | **2** | **1** |
| `max_core_deficit` B | 1 | 1 | 1 | 1 |
| `process_extinction_tick` B | — | — | 14 | 5 |
| `entrant_zero_process_ticks` B | 0 | 0 | 987 | 996 |
| `passive_stagnation_ticks` | 0 | 0 | **937** | **0** |
| **post-extinction core writes on B** | 0 | 0 | **0** | **7,960** |
| `attacker_resumes_objective_pressure` B | — | — | **False** | **True** |
| mutual disruptions A/B | 0 / 1 | 498 / 498 | 0 / 1 | 0 / 1 |

**The clearest R2 result.** Arm C reproduces R1 exactly: the defender's lone process dies at tick 14, the attacker loses its target, and 937 ticks of passive stagnation follow with zero core writes. Arm D restores the target and the attacker resumes pressure completely — 7,960 core-targeting writes after extinction, passive stagnation eliminated entirely. **And yet the outcome does not move at all**: max core deficit stays 1, no capture, still a 1000-tick tie. The attacker now writes to the one address it is given, forever, against a defenceless opponent that has no processes left to repair with.

Arm B is worse than a null: with exact coordinates the attacker abandons its pursuit of the defender's anchor and parks on the core base, where it and the defender mutually disrupt each other 498 times each. Actual core progress collapses from **495 ownership flips to 1** despite thousands of core-targeting writes — the activity-versus-progress distinction R1's measurement refinement was built to expose, now in the other direction.

### J.2 `disruption_churn` — scout vs local_defender, seed 6

| | A | B | C | D |
|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `core_attack_writes` A | 3,999 | 3,999 | 8 | 7,991 |
| `core_damage_dealt` A | 1 | 1 | 1 | 1 |
| `max_core_deficit` B | 1 | 1 | 1 | 1 |
| `process_extinction_tick` B | — | — | 3 | 3 |
| `passive_stagnation_ticks` | 0 | 0 | **949** | **0** |
| **post-extinction core writes on B** | 0 | 0 | **0** | **7,976** |
| `attacker_resumes_objective_pressure` B | — | — | **False** | **True** |

Identical shape to J.1. Arm B is a complete null (every metric identical to A). Arm D restores pressure absolutely (0 → 7,976 writes, 949 → 0 stagnation ticks) and changes nothing about the outcome.

### J.3 `slow_eventual_conversion` — claimer vs concentrated_attacker, seed 7

| | A | B | C | D |
|---|---|---|---|---|
| **Outcome** | **B wins, 999t** | **A wins, 91t** | tie, 1000t | **A wins, 91t** |
| `core_capture_outcome` | A captured | B captured | neither | B captured |
| `core_damage_dealt` A/B | 8 / 8 | 8 / 1 | 0 / 0 | 8 / 1 |
| `process_extinction_tick` A | — | — | **7** | **—** |
| `passive_stagnation_ticks` | 0 | 0 | 951 | 0 |

**The oracle reverses the winner.** In stable V4 the `concentrated_attacker` (B) grinds for 999 ticks and captures the claimer's core. Given exact objective coordinates it beelines to the claimer's core base and fixates on that single cell (689 core writes, 1 ownership flip) — and while it sits there, `v4_claimer`, which reads *no* enemy channel at all and simply wanders painting cells, walks into B's core and captures all 8. The match resolves in 91 ticks with the opposite winner.

Note also that in Arm D the attacker's diversion means it **stops hitting the claimer's anchor**, so mortality never triggers at all (`process_extinction_tick` A: 7 in C, `None` in D). Arm D here is not "the oracle rescued a stalled attacker"; it is "the oracle diverted the attacker so the R1 pathology never occurred." D is metric-identical to B.

### J.4 `repair_churn` — defender_scout self-play, seed 3

| | A | B | C | D |
|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `total_combat_writes` A/B | 15,376 / 15,412 | 15,376 / 15,412 | 17 / 16 | 15,873 / 15,910 |
| `core_damage_dealt` A/B | 497 / 499 | 497 / 499 | 1 / 2 | 1 / 2 |
| `core_deficit_area` A/B | 997 / 992 | 997 / 992 | 997 / 992 | 997 / 992 |
| `process_deaths` A/B | 0 / 0 | 0 / 0 | 1 / 1 | 1 / 1 |
| `passive_stagnation_ticks` | 0 | 0 | **942** | **0** |

Neither entrant ever goes fully extinct (each keeps its `scout` sub-process), so there is no post-extinction interval to measure. Arm B is a complete aggregate null. Arm D restores activity massively (17 → 15,873 writes, 942 → 0 stagnation ticks) with **`core_deficit_area` identical to four significant figures** and core damage unchanged at 1/2. Restored activity, zero restored progress.

### J.5 `passive_stagnation` — concentrated_attacker self-play, seed 1 (negative control)

| | A | B | C | D |
|---|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t | tie, 1000t |
| `total_combat_writes` A/B | **0 / 0** | 3,992 / 3,993 | 0 / 0 | 7,969 / 1 |
| `core_attack_writes` A | 0 | 0 | 0 | **7,961** |
| `max_core_deficit` B | 0 | 0 | 0 | 1 |
| `process_extinction_tick` B | — | — | — | **3** |
| `passive_stagnation_ticks` | **951** | **0** | **951** | **0** |

**The no-contact negative control is destroyed.** In V4 these two agents never find each other — zero combat writes for the whole match. With the oracle both beeline from their seeded spawns toward the other's seeded core, pass within reach, and (Arm B) mutually disrupt each other 500/499 times, or (Arm D) one dies to mortality at tick 3 and the survivor lands 7,961 core-targeting writes. The oracle manufactures contact where the game provided none, substituting for the independent *search* deficit Phase 0 diagnosed. This directly fails one of the charter's five promotion conditions.

### J.6 `healthy_decisive` — claimer vs quorum, seed 6

| | A | B | C | D |
|---|---|---|---|---|
| Outcome | B wins, 5t | B wins, 5t | B wins, 5t | B wins, 5t |
| `core_attack_writes` B | 14 | 20 | 14 | 20 |
| `core_deficit_area` A | 18 | 21 | 18 | 21 |

Outcome untouched at every arm. Quorum's slightly higher core-write count under the oracle confirms the instrument reaches a whole-tuple consumer; the match is over too fast for it to matter. **Mortality is harmless here and so is the oracle.**

### J.7 `multi_process_coordination` — quorum self-play, seed 1

| | A | B | C | D |
|---|---|---|---|---|
| Outcome | A wins, 60t | A wins, 60t | A wins, 51t | A wins, 51t |
| `core_capture_outcome` B | captured | captured | captured | captured |
| `process_extinction_tick` B | — | — | 14 | 14 |
| post-extinction core writes on B | 0 | 0 | **15** | **48** |
| `target_loss_interval_ticks` B | — | — | 34 | 35 |

Arm B is an exact aggregate null (every reported metric identical to A, though the gameplay stream differs). Under mortality, Quorum is the one agent that **already** resumes post-extinction pressure without the oracle (15 writes) — because it maintains its own `contacts`/`core_candidates` memory of where the enemy was last seen. The oracle triples that pressure (48 writes) without changing the outcome or the timing. This is the single most informative control in the set: an agent that already remembers its target does not need the oracle.

---

## K. Causal Deltas

Sums across both entrants unless noted. `B−A` = oracle effect without mortality; `D−C` = oracle effect with mortality; `C−A` = mortality effect without oracle (R1's own effect, reproduced); `D−B` = mortality effect when an objective signal exists.

| Match | metric | B−A | D−C | C−A | D−B |
|---|---|---|---|---|---|
| `named_reference` | post-ext core writes | 0 | **+7,960** | 0 | **+7,960** |
| | core_damage_dealt | **−494** | −1 | −493 | 0 |
| | passive_stagnation_ticks | 0 | **−937** | +937 | 0 |
| | captures | 0 | 0 | 0 | 0 |
| `disruption_churn` | post-ext core writes | 0 | **+7,976** | 0 | **+7,976** |
| | passive_stagnation_ticks | 0 | **−949** | +949 | 0 |
| | captures | 0 | 0 | 0 | 0 |
| `slow_eventual_conversion` | actual_ticks | **−908** | −909 | +1 | 0 |
| | captures | 0 | **+1** | −1 | 0 |
| | core_damage_dealt | −7 | +9 | −16 | 0 |
| `repair_churn` | passive_stagnation_ticks | 0 | **−942** | +942 | 0 |
| | core_damage_dealt | 0 | 0 | −993 | −993 |
| | captures | 0 | 0 | 0 | 0 |
| `passive_stagnation` | post-ext core writes | 0 | **+7,961** | 0 | **+7,961** |
| | passive_stagnation_ticks | **−951** | **−951** | 0 | 0 |
| | captures | 0 | 0 | 0 | 0 |
| `healthy_decisive` | every metric | ~0 | ~0 | 0 | ~0 |
| `multi_process_coordination` | post-ext core writes | 0 | **+33** | +15 | +48 |
| | captures | 0 | 0 | 0 | 0 |

**Reading the deltas.**

- **`D−C` is large and consistent for pressure, and zero for conversion.** In every case where target loss occurred, restoring the target restored objective pressure from essentially nothing to ~8,000 writes and eliminated 937–951 ticks of passive stagnation. Across the whole diagnostic set `D−C` for captures is **+1**, and that single capture (`slow_eventual_conversion`) is one where the oracle *prevented* the mortality pathology rather than rescuing an entrant from it, and reversed the winner relative to stable V4.
- **`B−A` is null or negative.** Five of seven matches show no aggregate change. The two that change get *worse*: the flagship's real core progress falls by 494 ownership flips, and a decisive matchup's winner is reversed. There is no match in which objective awareness alone improved conversion.
- **`C−A` reproduces R1 precisely** (+937/+949/+951/+942 passive-stagnation ticks, −493/−993 core damage, one decisive match destroyed into a tie), which is the expected result given Arm C is byte-identical to R1.
- **`D−B` ≈ `D−C` where extinction occurs and ≈ 0 elsewhere**, confirming that under an objective signal, mortality's remaining contribution is to remove the defender rather than to change the attacker.

---

## L. Post-Extinction Follow-Through

This is R2's central measurement, and it gives a sharp, two-part answer.

**Does the attacker resume objective pressure after the defender's last process dies? — YES, completely and reproducibly.**

| Match | extinction tick | post-ext core writes, C | post-ext core writes, D | resumes (C → D) |
|---|---|---|---|---|
| `named_reference` | 14 → 5 | 0 | 7,960 | False → **True** |
| `disruption_churn` | 3 → 3 | 0 | 7,976 | False → **True** |
| `passive_stagnation` | — → 3 | n/a | 7,961 | n/a → **True** |
| `multi_process_coordination` | 14 → 14 | 15 | 48 | True → True |

Time from extinction to the first subsequent core attack under Arm D is **1 tick** in the controlled unit-test reproduction and immediate in the corpus cases. R1's inference is therefore **confirmed as a causal fact**: attackers stopped applying pressure specifically because their target information disappeared, and restoring that information restores the pressure.

**Does the resumed pressure convert into progress against the objective? — NO.**

In `named_reference` and `disruption_churn`, Arm D delivers ~8,000 core-targeting writes against an opponent with **zero live processes and therefore zero repair capacity**, and still ends with `max_core_deficit = 1`, `core_capture_outcome = survived`, and a 1000-tick tie. `target_loss_interval_ticks` (time to the first attack that actually takes a core cell) is `None` in both — after the first flip no ownership ever changes hands again.

The reason is structural and was declared before the runs (Section F): capture requires owning **all eight** core cells; the oracle names **one** address; and five of the six bundled agents write at exactly the address they are handed. The controlled unit test makes this exact: with the oracle on, a hunter lands **312 post-extinction core writes** and achieves **1** core-damage event and a max deficit of **1** — the same 312-to-zero ratio of activity to progress, isolated in a two-agent scenario.

**The single most important qualification in this report:** the failure to convert is a property of the *joint* system of information shape and agent capability, and the two are confounded in this corpus. `v4_quorum` — the one bundled agent that sweeps a region around a target rather than writing at a point — converts in every arm it appears in. R2 cannot separate "a point target is the wrong information shape" from "the bundled agents are too simple to convert any target", and it would have required rewriting agents to try, which the charter forbids. This is a threat to the validity of the whole V5 programme's framing, and it is the basis of the single recommended next question in Section R.

---

## M. Pathologies

Assessed against the charter's six named risks.

**A. Homing-missile behaviour — CONFIRMED, severe.** `named_reference` Arm B: given exact coordinates the attacker stops pursuing the defender's anchor and parks on the core base. Core-targeting writes stay in the thousands while real core progress collapses from **495 ownership flips to 1** (−99.8%). The oracle converts varied, productive pressure into fixation on a single cell.

**B. Healthy-match collapse — CONFIRMED.** `slow_eventual_conversion` Arm B/D reverses the winner of a decisive V4 matchup and compresses it from 999 to 91 ticks. `named_reference` Arm B replaces a one-sided siege with a 498/498 mutual-disruption standoff. Per the charter, Arm B substantially changing healthy V4 matches is explicitly a **warning, not a success**.

**C. Quorum amplification — NOT OBSERVED.** Quorum's outcomes are identical across all four arms in both matches it appears in. Its post-extinction pressure rises 15 → 48 writes with no change in result or timing. If anything the finding runs the other way: Quorum already carries its own target memory and benefits least from the oracle.

**D. One-process overcorrection — NOT OBSERVED; the opposite occurred.** Single-process attackers became far more *active* under the oracle (~8,000 writes) without becoming more *effective* (0 captures, deficit still 1). No single-process attacker became unrealistically strong.

**E. Spawn-location determinism dominance — CONFIRMED.** In `passive_stagnation` both agents beeline from seeded spawn to the opponent's seeded core, making the entire match a deterministic function of placement. Combined with seeded placement, exact core knowledge trivialises the opening.

**F. Territory irrelevance — CONFIRMED.** `max_displacement_from_core` for the attacker falls from 256 (A) to 116 (B/D) in `named_reference`: agents stop roaming the arena and travel only between their spawn and the enemy core. Spatial and territorial interaction is bypassed.

**G. Negative-control destruction — CONFIRMED (not on the charter's list; recorded as new).** The no-contact control goes from 0 combat writes to 3,992/3,993 (B) and 7,961 core attacks (D). The oracle substitutes for search, which is a distinct Phase 0 problem the instrument was not chartered to address.

---

## N. R2C Gate

Evaluated against the charter's five pre-declared promotion conditions:

| Condition | Result | Evidence |
|---|---|---|
| Arm C reproducibly stalls after process extinction | **PASS** | 0 post-extinction core writes in 3 of the 4 Arm-C extinction cases (the fourth is Quorum, which carries its own target memory and manages 15); 937–951 passive-stagnation ticks in the 4 matches that stall |
| Arm D reproducibly resumes post-extinction core pressure | **PASS** | 7,960 / 7,976 / 7,961 writes; stagnation eliminated in all 4 stalling matches |
| Not limited to one seed | **PASS** | effect present at seeds 1, 3, 6 and 7 |
| Passive/no-contact controls remain appropriately unchanged | **FAIL** | control goes from 0 combat writes to 7,961 core attacks (J.5) |
| Healthy matches do not become obviously pathological | **FAIL** | winner reversed in `slow_eventual_conversion`; core progress −99.8% in `named_reference` Arm B (M.A, M.B) |

Two of five conditions fail. Additionally, the question R2C would have been broadening — whether restored target information converts combat into **core capture** — is answered **no** in two of the three target-loss cases, and the single positive case is one in which the oracle prevented the pathology and reversed the winner rather than rescuing a stalled attacker.

### **DO NOT PROMOTE.**

Per the charter ("If the oracle has no meaningful effect: STOP… If the oracle substantially changes healthy V4 matches in Arm B, treat that as a warning, not automatically as success"), the broader R2C corpus was **not executed**. Running 288 more matches would multiply data about an instrument already shown to distort the matches it touches, without addressing the confound Section L identifies.

---

## O. Broader Validation

Not applicable — the R2C gate was not passed (Section N).

---

## P. Candidate Evidence Update

| Candidate | Status | Basis |
|---|---|---|
| **Persistent target information** | **STRONGER SUPPORT** (scoped to contact/pressure) · **CONTRADICTED** as a conversion fix | The causal claim R1 inferred is now proven: restoring the target restores post-extinction objective pressure from 0 to ~8,000 writes and eliminates 937–951 stagnation ticks, reproducibly, at four seeds. But the restored pressure produces no additional capture and no additional core deficit in 2 of 3 target-loss cases, against opponents with zero repair capacity. Target loss caused the *activity* collapse; it was not the *conversion* blocker. |
| **Objective awareness** | **WEAKER SUPPORT** | `B−A` is an exact null in 5/7 matches and negative in the other 2 (−494 core-damage flips in the flagship; a reversed winner). No match improved. Always-visible cores are not merely unproven as a mechanic — as instrumented they actively degrade play. |
| **Process mortality** | **SUPPORT UNCHANGED** (remains CONTRADICTED from R1) | Arm C is byte-identical to R1, so R2 adds no new evidence for or against mortality itself. R2 does narrow *why* R1 failed: the visibility confound R1 identified is real, but removing it does not rescue mortality — Arm D still ties in both flagship pathology cases. This makes R1's rejection **stronger**, not weaker: the one confound that could have excused mortality has now been tested and does not excuse it. |
| **Process-local information / entrant-wide sensor fusion** | SUPPORT UNCHANGED | R2 changed information *persistence*, not its locality or fusion. Untested here. |
| Replication / deployment | NOT TESTED | Held constant by design. |
| Capacity economics | NOT TESTED | Held constant by design. |
| Specialization | SUPPORT UNCHANGED | R1's `repair_churn` specialization-fragility observation reproduces unchanged in Arms C/D; R2 was not a controlled specialization experiment. |
| V4 process core size = 8 | **NOT TESTED — but newly implicated** | The 8-cell simultaneous-ownership capture condition is precisely what a single-address target cannot satisfy (Section L). Recorded as an implicated variable, not as a tier change, since R2 ran no controlled core-size comparison. |
| Territory incentives | NOT TESTED | Held constant, though M.F shows the oracle bypasses territorial play entirely. |
| *(new)* **Agent conversion capability as a confound** | **NEW CANDIDATE — STRONG SUPPORT FOR FURTHER STUDY** | Five of six bundled agents write at exactly the address given and cannot capture an 8-cell core from a point target; the one that sweeps a region (`v4_quorum`) converts in every arm. Phase 0's entire corpus rests on these six agents, so the programme's "combat does not convert to victory" premise may be measuring agent simplicity rather than game mechanics. See Section R. |

---

## Q. Validation

**Focused R2 tests (all new, all passing):**

- `engine/tests/test_objective_target_oracle.py` — **20 tests**: Ruleset registration/isolation (registered, dispatches to the process runtime, absent from omitted-Ruleset resolution, field-by-field equivalence with V4, carries no mortality, available to R1's identity); the two-key gate (off by default under its own Ruleset; a stray request ignored entirely under stable V4); oracle semantics (core base appended after detected anchors in exact order; independent of sensor reach; survives total enemy process extinction; withdrawn on entrant elimination with a surviving third entrant retained; never duplicates a detected address; one sorted target per living enemy in a 3-entrant match; identical across repeated runs); the information-only/mechanics-invariance proof; and full-stack provenance, V4 byte-compatibility, R1 byte-compatibility, determinism, and a guard that the instrument is not inert.
- `engine/tests/test_v5_research_r2_metrics.py` — **4 tests**: R1's stall reproduced as a measured fact (0 post-extinction writes, `resumes = False`); the R2 hypothesis measured (312 post-extinction writes, `resumes = True`, first attack at +1 tick) together with its central limitation asserted rather than assumed (0 post-extinction ownership losses, `core_damage_dealt = 1`, `max_core_deficit = 1`); R2 fields inert under stable V4; and metric determinism.

All observation assertions derive from observations real agent callbacks were handed during real ticks, and all metric assertions derive from replays real matches produced — no hand-built records, and no non-emptiness assertions standing in for value assertions.

**Stable V4 regression:** R2A Steps 1, 3 and 4 (Section H) — 7/7 byte-identical fresh reruns against frozen Phase 0 replays, 0/288 outcome mismatches and 0/288 field pollution on re-analysis of the whole Phase 0 corpus, aggregate identical to Phase 0's published 60.42% / 43.75%. The pre-existing `test_v4_stable_ruleset_equivalence.py`, `test_v4_runtime_default_ruleset.py`, and `test_ruleset_policy.py` suites are unmodified and pass.

**R1 regression:** R2A Step 2 — 7/7 byte-identical against frozen R1 H=8 replays; `engine/tests/test_process_mortality.py` and `engine/tests/test_v5_research_r1_metrics.py` unmodified and passing; and Arm C of the live R2B run reproduces R1's published numbers exactly (extinction ticks 14 / 3 / 7, zero-process ticks 987 / 998 / 994, attacker combat writes collapsed to 16 / 16 / 9 for `named_reference` / `disruption_churn` / `slow_eventual_conversion` respectively).

**Full suite:** `python -m pytest` across all three configured `testpaths` (`_legacy/tests`, `engine/tests`, `client/tests` — the true repository suite per `pytest.ini`, not `engine/tests` alone) — **3048 tests, 0 failures, 0 errors, 14 skipped**, 334.4 s, exit code 0 (JUnit XML confirmed: `errors="0" failures="0" skipped="14" tests="3048"`). This is exactly R1's 3024 plus R2's 24 new tests. The known intermittent Windows file-lock flake in `test_agent_evaluation_parallel.py` did not occur in this run.

**Ruff:** `ruff check .` — All checks passed (no findings, no fixes required).

**Mypy:** `mypy engine/src/battle_engine` — Success, 0 issues, 102 source files. `mypy client/src/battle_client` — Success, 0 issues, 16 source files.

**Determinism:** proven at four levels — oracle address stream, full-stack replay bytes, analyzer output, and a complete independent re-execution of the 28-match R2B corpus whose entire analysis payload and H\* selection record compare byte-identical.

**Provenance:** an oracle run's `reproducibility` block carries `objective_target_oracle: true` and hashes to different `match_id`, `result_id`, `replay_id` and replay SHA-256 than the otherwise-identical non-oracle run. The key is **omitted entirely** (never written as `false`) when the oracle is off, so every pre-R2 match identity — stable V4's and R1's alike — is unchanged. Stable V4 replay bytes are unchanged even when an oracle is explicitly requested.

---

## R. Final Verdict

### **2. TARGET PERSISTENCE SUPPORTED BUT ORACLE TOO STRONG**

Scoped precisely, because the two halves of this verdict are about different things:

**Supported.** R1's causal inference is now a proven fact. Loss of target information after process removal *is* the reason attackers stop applying pressure: restoring a persistent objective address restores post-extinction core pressure from zero to ~8,000 writes and eliminates 937–951 ticks of passive stagnation, reproducibly, across four seeds and every diagnostic case where target loss occurred. The null hypothesis (H0) is rejected for pressure.

**But not sufficient, and the instrument is too strong.** Restored pressure does not become progress. In both flagship pathology cases, an attacker with permanent, perfect knowledge of an *undefended* objective — the defender having zero live processes and therefore zero repair capacity — makes roughly eight thousand core-targeting writes across a thousand ticks and moves the victim's core deficit from 0 to 1 out of 8. Meanwhile the oracle inflicts real damage where it is not needed: it collapses the flagship siege's actual core progress by 99.8%, reverses the winner of a decisive matchup, manufactures contact in the no-contact control, and makes agents abandon spatial play to beeline between seeded spawns and seeded cores. Objective awareness alone (H2) is **not** supported: five of seven matches are exact nulls and the other two are worse.

This verdict does **not** establish that persistent objective information should be a V5 mechanic, and explicitly does not endorse always-visible cores. The oracle is intentionally artificial; what it establishes is that persistent strategic objective information is causally *necessary* for sustained pressure and demonstrably *not sufficient* for conversion.

**The most consequential thing R2 found is not on its own hypothesis list.** An attacker was handed a perfect, permanent target against a defenceless opponent and still could not win, because it wrote to the one address it was given while victory requires simultaneously owning eight. The one bundled agent that sweeps a region rather than a point (`v4_quorum`) converted in every arm it appeared in. Phase 0's entire 288-match corpus — and therefore the whole V5 programme's founding premise that "combat does not convert into victory" — rests on these same six agents, five of which are structurally incapable of converting any point target into a capture. R2 cannot separate a mechanics problem from an agent-population problem, and the charter correctly forbade it from trying by rewriting agents.

### Recommended next research question (exactly one)

> **Is Phase 0's combat-to-victory conversion deficit a property of Bytefray's mechanics, or of its bundled agent population?**
>
> Hold mechanics fixed at stable `bytefray-rules-4` — no mortality, no oracle, no new Ruleset — and vary only attacker *conversion capability*, by adding a new research-only agent that is a minimal region-sweeping variant of an existing attacker (a new agent directory, never an edit to a bundled one, so the V4 population and every published Phase 0 number stay intact). Re-run the Phase 0 pairings that R1 and R2 both failed to convert. If stable V4 already yields reliable core capture given a competent attacker, then Phase 0's premise measured agent simplicity rather than a design defect, and the V5 mechanic search — mortality, target persistence, and everything queued behind them — is aimed at a problem that does not exist. If capture still fails against a repairing defender even with a region-sweeping attacker, then the conversion deficit is genuinely mechanical, Phase 0's premise is vindicated on much firmer ground than it currently rests on, and the search for a mechanic can resume with a trustworthy baseline.
>
> This question must be answered before any further V5 mechanic is designed or tested. It is cheap (one new agent, existing corpus, existing tooling), it is a strictly stronger baseline than the programme currently has, and both of its outcomes are decision-relevant. Per the standing research-integrity rule, the discovery that a scope-excluded factor may be needed to establish a trustworthy baseline is reported here as a **blocker finding**, not treated as permission to implement anything.
