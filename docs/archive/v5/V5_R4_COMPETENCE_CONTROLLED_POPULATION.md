# Bytefray V5 Research Phase R4 — Competence-Controlled Population Baseline

**Status:** Phase R4 blocker experiment (staged: R4A analyzer/baseline verification, R4B qualification and population freeze, R4C evaluation corpus). Completed.
**Ruleset Evaluated:** `bytefray-rules-4` **only** — the permanent stable V4 identity. No experimental Ruleset was created, no production engine file was modified, and neither R1 process mortality nor the R2 objective oracle was activated at any point.
**Execution Baseline Commit:** `3c37452e93c6671ae35003fd2542446304a3d457`
**R3 Commit:** `3c37452` (`research(v5): evaluate agent competence and region-sweep sufficiency`)
**Archival Release Anchor:** `v4.0.0` (`9077b618d12a3eab498af5818a2852a841f49f5b`)

---

## A. Repository baseline

- **Branch:** `v5-research`.
- **Starting HEAD SHA:** `3c37452e93c6671ae35003fd2542446304a3d457`.
- **Working tree at start:** clean (`git status --short` empty).
- **Upstream:** `v5-research` and `origin/v5-research` both at `3c37452` at the start of R4.
- **R3 present in branch history:** yes — `3c37452` *is* R3's commit. The branch reads `3830382 → ab24d27 (Phase 0) → 303b33f → 18e5ac6 (R1) → 26e0816 (R2) → 3c37452 (R3)`.
- **Project version:** `4.0.0` (`pyproject.toml`), unchanged throughout R4.
- **Git discipline:** no commits, staging, rebases, resets or history mutation. All git operations were read-only (`status`, `log`, `rev-parse`, `diff`).

**Relationship to R3.** R4 is precisely the single next research question R3 named. R3 closed by asking whether a bundled population that *can express the game's objective* still shows a conversion deficit, and explicitly declined to build one, recording the need as a finding rather than as permission. R4 builds that population as a **research control**, not as a product proposal (Section 24 of the charter; Section X below).

---

## B. Research question

> Under unchanged stable `bytefray-rules-4`, does a competence-controlled, strategically diverse population still exhibit the high timeout, tie, stagnation and failed-post-contact-conversion behaviour that Phase 0 measured?

This is a **population-level** experiment. R3 asked whether *one* legal region-capable attacker could convert better. R4 asks what the game looks like when the evaluated population as a whole contains agents capable of playing the actual objective.

The experimental factor is **population identity**. Ruleset, arena size, tick limit, quota, disruption duration, placement, scheduler, scoring, seed set and corpus shape are Phase 0's, reused rather than re-chosen.

A null, mixed or negative result was declared valid in advance.

---

## C. Historical interpretation (Phase 0 → R1 → R2 → R3)

Prior results are summarised, not rewritten. Every number below reproduces exactly (Section N).

| Phase | Question | Result |
|---|---|---|
| **Phase 0** | Does combat convert into victory under stable V4? | 288-match baseline over the six canonical agents: 39.58% decisive, 60.42% timeout, 43.75% tie, 1.77% combat conversion. Diagnosed **State B** (matchup-specific conversion failure, attributed to "infinite core repair churn under zero process mortality") and **State C** (search deficit). |
| **R1** | Does finite process mortality break the repair stalemate? | **MORTALITY REJECTED.** None of the four matchups Phase 0 cited was improved at any tested H; one previously decisive matchup degraded into a stalemate. |
| **R2** | Does persistent target information restore conversion? | **Target persistence supported for *pressure*, contradicted as a *conversion* fix.** An attacker given a perfect permanent target against an opponent with zero repair capacity made ~8,000 core-targeting writes and moved the deficit from 0 to 1 of 8. |
| **R3** | Is the deficit a property of mechanics or of the bundled population? | **Agent competence materially improves conversion but does not fully explain it.** A one-expression region-sweep change produced +5 captures over 96 matches with zero regressions; a movement-enabled variant captured a repairing defender in 16–27 ticks in the exact matchups Phase 0 named. R3 also corrected two Phase 0 factual errors. |

**R3's two corrections to Phase 0, carried forward.** Both are load-bearing for R4 and neither is silently absorbed:

1. Phase 0's published reach table was wrong for all six canonical agents. The real declared reaches are 1, 4, 2/8, 2, 8 and (Quorum) 256/48/12/32/32/24 — not 5, 15, 8/25, 8, 40.
2. `v4_local_defender` never repaired its eight core cells. With reach 2 its patrol offset cycles `1, 0`, so it writes exactly **two** addresses for a whole match.

R4 independently reconfirms correction (2) from the frozen Phase 0 replay using a new additive metric: in `v4_concentrated_attacker vs v4_local_defender` seed 1, the defender's `distinct_own_core_cells_written` is **2** across 1,000 ticks, and the attacker's `unique_write_addresses` is **1** (Section Z; `test_r4_own_core_write_metric_separates_defenders_from_patrollers`).

**Superseded interpretations are identified explicitly, not erased.** Phase 0's State-B *mechanism* ("infinite core repair churn under zero process mortality") was already confounded by R3 and is further undermined here (Section W). Phase 0's *measurements* stand unchanged.

---

## D. Stable V4 invariants — proof that no gameplay rule changed

Every R4 match ran with:

```
ruleset_id = bytefray-rules-4     arena_size = 512     max_ticks = 1000     instr_per_tick (Q) = 8
```

and unchanged stable mechanics: process core size 8, D = 1 disruption, seeded placement, chunked round-robin scheduling with rotating start (`scheduler_chunk_size=2`, `scheduler_rotate_start=True`), entrant-wide sensor fusion, immortal processes, static process declarations, no replication, existing reach/movement/scoring/territory rules, existing core-capture victory condition.

- **No R4 Ruleset exists.** No `bytefray-rules-5-r4-*` identity was created. `rules.py`, `ruleset_policy.py`, `process_runtime.py`, `placement.py`, `scoring.py`, `results.py`, `python_runtime.py` and every other engine module are untouched.
- **Zero production engine files changed.** `git diff --stat` covers exactly one tracked file: `tools/research/v5/analyzer.py`, +18 lines, strictly additive (Section Z).
- **No mortality, no oracle.** `process_integrity` and `objective_target_oracle` were left at their defaults in every call, so neither was requested. Under stable V4 the oracle cannot be activated even if requested, because `bytefray-rules-4` is absent from `OBJECTIVE_TARGET_ORACLE_RULESET_IDS`. Verified per match from the replay header: `ruleset_id == "bytefray-rules-4"` and the `reproducibility` block contains **no** `process_integrity` key and **no** `objective_target_oracle` key.
- **No canonical agent source was modified.** `v4_quorum` participates as an unchanged bundled agent; its fingerprint is Phase 0's exactly (Section I).

---

## E. Population-construction methodology

The charter's central warning (Section 5) is that a "competence-controlled" population must not become six versions of one sweeper. R4 therefore defines archetypes by **mechanism**, not by tuning, and each archetype is required to differ from the others in *how it acquires a target* and *what it does with spare actions* — not merely in constants.

Two design rules were fixed before any agent was written:

1. **Competence means a plausible legal path** from search → contact → pressure → multiple core cells affected → possible capture. It does **not** mean an agent must beat every opponent (charter Section 7).
2. **Every archetype keeps a real weakness.** Two of the six have no defence at all; one has no search at all; one abandons a winning siege on a timer; one is deliberately mediocre at everything.

Legal-information boundary (charter Section 9) applies to all of them: only ordinary `ObservationV2` fields, only `READ`/`WRITE`/`MOVE`, ordinary reach, ordinary Q = 8. Two information sources deserve explicit justification because they look like more than they are:

- **`own_core_base` / `own_core_size`** describe the agent's *own* core. The bundled `v4_local_defender` and `v4_defender_scout` both already read them. Using `own_core_size` as "the width a core has in this game" is public symmetric game knowledge; the bundled `v4_quorum` hard-codes the same constant as `_CORE_ORDER`.
- **First-contact core-base inference** (archetype A only) is an inference from a legal observation, not privileged data: every process starts the match at its entrant's core base (`process_runtime`: `if p.position is None: p.position = start`), so the first address at which an enemy is seen is *evidence* about that enemy's core. It is only evidence, and it is wrong whenever the enemy was already deployed when first sighted — which is why archetype A spends actions on READ verification and retires a hypothesis the evidence contradicts. The bundled `v4_quorum` performs exactly this inference (`core_candidates[address] = 100`).

No agent receives hidden enemy core coordinates, the R2 oracle, process integrity, future actions, opponent RNG state, engine ownership maps, special reach, extra actions, teleportation, privileged memory reads, or hard-coded opponent start coordinates. This is proven from trace and replay in Section Z, not asserted.

---

## F. Development / evaluation separation

| | Seeds | Used for |
|---|---|---|
| **Development** | 101, 102, 103, 104, 105, 106, 107, 108 | debugging, archetype development, competence qualification |
| **Evaluation** | 1, 2, 3, 4, 5, 6, 7, 8 | the frozen population corpus, run once |

The sets are disjoint by construction and asserted disjoint by test. Evaluation seeds reproduce Phase 0's canonical set exactly. Both sets are defined in exactly one place, `tools/research/v5/r4_population.py`.

**Freeze point.** All agent development and every qualification run used development seeds only; `run_qualification` asserts at runtime that it has been handed no evaluation seed. After qualification the population was frozen, fingerprints recorded, and the preregistration written to disk **before** the first evaluation match executed:

```
runs/v5_r4_population/r4_preregistration.json
sha256 = d09ceaf5f236cd9affd37f2faac3b6960fdeaf690c082490cc7e61a6d29434b3
```

**No gameplay-affecting agent edit was made after evaluation began.** The evaluation was therefore never invalidated and never restarted. Fingerprints were re-verified against the preregistration after evaluation and after a later directory move, and all six match (Section Z).

One post-freeze change was made to *file location* and nothing else: the R4 agent directories were moved from `tools/research/v5/agents/` to `tools/research/v5/r4_agents/` so that R3's containment test — which asserts its research directory holds precisely the three agents R3 created — kept holding unmodified. `agent_revision_fingerprint` is content-derived, so all six fingerprints were unchanged, and 18 deterministic reruns reproduced the frozen evaluation replays **byte-for-byte** after the move. No agent source line changed.

---

## G. Competence admission criteria

Per charter Section 12, the gate is never "must win"; it is "the intended strategy demonstrably functions under stable V4". Archetypes are scored on the criteria that make sense for them rather than forced through one identical metric.

| Criterion | Applied to | Requirement |
|---|---|---|
| `acquires_legal_contact` | all | at least one development run establishes legal enemy contact |
| `multi_address_pressure` | offensive (A, B, D, F) | regional attack produces more than one useful hostile address |
| `multi_core_cell_pressure` | offensive | demonstrates multi-core-cell pressure (≥ 2 distinct enemy core cells damaged) |
| `real_core_capture` | offensive | achieves a real core capture in at least one legal, non-contrived run |
| `actually_moves` | mobile (B, E) | moves in every run and builds a real search footprint |
| `contact_to_attack_transition` | recon (B) | converts contact into core damage |
| `defends_objective_region` | defensive (C, D, F) | writes more distinct cells of its own core than the bundled two-address behaviour |
| `responds_to_pressure` | defensive | repairs its own core in the majority of runs where it lost at least one core cell |
| `spatial_spread` | territorial (E) | meaningful spatial spread (mean unique write addresses > 32) |
| `legal_conversion_path_after_contact` | territorial | still produces enemy-core writes after contact |
| `multi_process_roles_active` | multi-process (F) | the declared multi-process configuration is present in every run |

Qualification ran every candidate against four **bundled** fixtures — `v4_local_defender`, `v4_claimer`, `v4_concentrated_attacker`, `v4_scout` — over 8 development seeds in both slot orders: 6 × 4 × 8 × 2 = **384 development runs**. Per charter Section 13, none of these fixtures is a member of the R4 evaluation population, so qualification cannot contaminate evaluation; no fixture was authored for this phase, and none is aligned to any R4 agent's attack pattern.

---

## H. Candidate agents — what was tried, and what was rejected

Five research archetypes were written and one bundled agent was retained. One candidate was **rejected at qualification and rebuilt**, which is the reason the gate exists.

### H.1 `v5r4_core_warden` v1 — REJECTED

The first draft passed a coverage-only defender check while comprehensively failing its own archetype. Its action priority put "disrupt an enemy anchor inside reach" *above* "inspect your own core", so whenever an opponent stood next to it, it spent every one of its 8 actions per tick writing the enemy anchor and never inspected or repaired anything. Measured on development seeds:

| Fixture | W–L–T | own core cells lost (mean) | **own core cells written (mean)** |
|---|---|---|---|
| `v4_claimer` | 0–16–0 | 8.00 | 8.00 |
| `v4_concentrated_attacker` | 0–0–16 | 1.00 | **0.00** |
| `v4_local_defender` | 0–0–16 | 0.00 | 0.00 |
| `v4_scout` | 0–0–16 | 1.00 | **0.00** |

It lost core cells and repaired **nothing** in the two matchups where it was actually attacked. This is precisely the defect R3 Section C.1 found in the bundled `v4_local_defender`, which likewise abandons its patrol whenever an enemy is within reach — reproduced by accident.

Two things were changed in response, both on development seeds and both before the freeze:

1. **The agent.** Inspection became a *reserved duty cycle* (`INSPECTIONS_PER_TICK = 4`) that offence may not starve, plus a perimeter-claim fallback for genuinely idle actions.
2. **The gate**, which had been too weak to catch it. A `responds_to_pressure` check was added, measured only on the runs where the agent actually lost a core cell — not on the population average, which the v1 draft had passed by way of a single fixture.

After the rebuild: mean own-core coverage **2.00 → 5.91**, and it repaired its core in **48/48** runs where it was damaged.

### H.2 Retained rather than imitated

`v4_quorum` was kept as the multi-process coordinated archetype rather than reimplemented, per charter Section 6F. It is the population's existing region-capable strategy and the one in-repository existence proof that stable V4 permits core-aligned objective play. Creating a research imitation for symmetry would have added a clone, not a strategy.

### H.3 Not reused

R3's `v5r3_region_sweeper_mobile` was **not** carried into R4, per charter Section 6B. R3 Section M.5 measured it as materially worse than the bundled baseline (5–39–52, own core captured three times as often) because it repositioned out of sensor range and lost its target. Archetype B was written fresh with the two design responses that failure implies — a large declared reach so search and strike do not fight each other, and persistent contact/ownership memory — both fixed before any evaluation seed ran.

---

## I. Final frozen population

| ID | Archetype | Procs | Reach (share) | Movement | Target source | Write geometry | Defence | Source fingerprint |
|---|---|:--:|---|---|---|---|---|---|
| `v5r4_siege_regional` | A — regional pressure attacker | 1 | 24 (1.0) | station-keeping; drifts only while unacquired | first-contact core-base hypothesis, READ-verified | core-width burst cycling `base..base+7` | **none** | `72e001f4556ea4e25d4f754a359e753bc78f765149e6c584a6f4f07d27b302c2` |
| `v5r4_recon_striker` | B — mobile reconnaissance attacker | 1 | 40 (1.0) | high — crosses the arena in reach-sized strides | **READ-derived ownership evidence**; longest enemy-held run | core-width window on the evidence run | **none** | `0bf1b348ebd07dce57ead3098ad7c8904882eeb84e180d618e83b17fc9221ba4` |
| `v5r4_core_warden` | C — objective-capable defender | 1 | 12 (1.0) | minimal — holds a station covering its own core | own core cells by READ inspection; opportunistic contact | repair of own core; local counter-pressure | **primary** | `e277b07d6c1c4a0c8969d7e71c8ae0adf698c8a404db7b1f26e5793941ea2531` |
| `v5r4_dual_operator` | D — balanced generalist | 2 | 32 (0.5), 12 (0.5) | moderate — raider pursues, keeper holds | remembered nearest contact (no core inference) | two-core-width sweep centred on contact | secondary (blind rotation) | `d67fcdd6675b6d4010252caa583057a5167a60db8ddbcb66041ce5a43e215311` |
| `v5r4_territory_expander` | E — territory / exploration | 1 | 16 (1.0) | high — strides between claim blocks | nearest contact, **bounded press window only** | contiguous claim blocks; bounded contact sweep | incidental (territory) | `8d70c20a0e9e5c5fb91c297330afeae3b09df9466e349d80911626e3dae5e267` |
| `v4_quorum` *(unchanged bundled agent)* | F — multi-process coordinated | 6 | 256, 48, 12, 32, 32, 24 | role-dependent deployment and patrol | contact memory, first-contact core candidates, READ evidence | 16-offset siege order, core-aligned first eight | guardian repairs; adaptive reserve | `d220a58316c7afab1e5dbb719aa5965095b5e352ca442bab1ca109c45507ee64` |

`v4_quorum`'s fingerprint is byte-identical to the value Phase 0 published, confirming it is the unchanged bundled agent.

Every reach and share above is read back from the agent's actual `declare_processes()` return value and re-verified against the replay the engine wrote — never transcribed from documentation. This is a direct response to R3's finding that Phase 0's published reach table was wrong for all six canonical agents.

---

## J. Strategic-diversity audit

Measured over the 384 development-seed qualification runs (admission evidence, not prediction):

| Agent | Movement (mean max displacement) | Unique write addrs | Unique hostile addrs | Own-core cells written | Procs | Captures | Contact % |
|---|---:|---:|---:|---:|:--:|---:|---:|
| `v5r4_siege_regional` | 200 | 79 | 73.1 | 1.30 | 1 | 20 | 98% |
| `v5r4_recon_striker` | 193 | 14 | 7.9 | 0.19 | 1 | 35 | 94% |
| `v5r4_core_warden` | **0** | 21 | 6.8 | **5.91** | 1 | **0** | **55%** |
| `v5r4_dual_operator` | 217 | 143 | **124.4** | **7.84** | 2 | 12 | 100% |
| `v5r4_territory_expander` | 202 | **178** | 110.3 | 5.61 | 1 | 35 | 86% |
| `v4_quorum` | 154 | 26 | 7.0 | 2.39 | **6** | **48** | 100% |

| Property | Materially used by |
|---|---|
| movement / search | B, D, E, F (A drifts only pre-contact; C never moves) |
| sensing / contact | all six |
| regional writes | A, B, D, E, F |
| territory expansion | E primarily, D and C incidentally |
| defence | C (primary), D and F (secondary), A and B **none** |
| multiple processes | D (2), F (6) |
| role specialisation | D, F |
| target memory | A, B, D, F (E only within a bounded press window) |
| sequential sweep | A, B, D, E, F |
| local reaction | C, D, F |
| **READ-derived ownership evidence** | B (primary), A (verification only), C (own core), F (weak targets) |

No two members share a profile. Targeting mechanisms are distinct in kind — anchor-inference (A), READ-ownership evidence (B), own-core inspection (C), contact-address memory (D), bounded contact press (E), and multi-role coordination (F) — and process counts span 1, 2 and 6, the same spread Phase 0's population had.

---

## K. Qualification results (development seeds only)

All six candidates were **ADMITTED**, the warden only after the rebuild described in H.1.

| Candidate | Verdict | Evidence (384 dev runs total) |
|---|---|---|
| `v5r4_siege_regional` | **ADMIT** | contact 63/64; multi-address 32/63; ≥2 core cells 29/63 (max 8); **20 captures** |
| `v5r4_recon_striker` | **ADMIT** | contact 60/64; moved 64/64 (mean displacement 192.7); contact→damage 42/60; **35 captures** |
| `v5r4_core_warden` | **ADMIT** | contact 35/64; own-core coverage max 8, **mean 5.91** vs bundled 2; **repaired in 48/48 pressured runs** |
| `v5r4_dual_operator` | **ADMIT** | contact 64/64; own-core mean 7.84; multi-address 44/64; **12 captures**; repaired 33/33 |
| `v5r4_territory_expander` | **ADMIT** | contact 55/64; moved 64/64; spread 177.5 unique addrs; conversion path 31/55; **35 captures** |
| `v4_quorum` | **ADMIT** | contact 64/64; 6 processes in every run; multi-address 58/64; **48 captures**; repaired 4/4 |

---

## L. Preregistered evaluation design

Declared before execution, in `r4_population.py` and frozen to `r4_preregistration.json`:

```
population   6 entrants
pairings     6 x 6 = 36 ordered (self-play included, both slot orders)
seeds        1..8
matches      36 x 8 = 288
arena        512          max_ticks 1000          instr_per_tick 8
ruleset      bytefray-rules-4      mortality off      oracle off
```

This reproduces Phase 0's canonical corpus shape exactly. No matchup was excluded after the fact and no seed was rerolled.

---

## M. Preregistered interpretation gate

Declared before any evaluation seed ran, anchored to Phase 0's measured values, and deliberately multi-factor: the charter notes a healthier strategic population may produce longer but more interactive matches, so duration and tie rate are read as context rather than as pass/fail criteria on their own.

| # | Metric | Phase 0 | STRONG | PARTIAL | Justification |
|---|---|---:|---:|---:|---|
| **C1** | matches with ≥1 core capture | 39.58% | ≥ 55% | ≥ 45% | +15pp makes capture the *modal* outcome, the qualitative change the hypothesis predicts |
| **C2** | contact matches never reaching a capture | 55.47% | ≤ 40% | ≤ 48% | the charter's central "failed post-contact conversion" quantity |
| **C3** | timeout rate | 60.42% | ≤ 45% | ≤ 55% | timeout is the pathology Phase 0 named; < 45% makes decisive resolution the majority |
| **C4** | mean max simultaneous core deficit | 4.125 | ≥ 5.5 | ≥ 4.6 | simultaneity, not coverage, is what capture requires |
| **C5** | mean stagnation ticks | 432.1 | ≤ 300 | ≤ 380 | < 30% of the tick cap means matches are substantively interactive |
| **C6** | winner diversity / dominance | 5 of 6 won; top 51.9% of wins | — | — | a single member taking ≥ 60% of wins routes the verdict to *balance* regardless of C1–C5 |

**Decision rule (verbatim from the preregistration).** *Strong population confound* requires C1, C2 and C3 all STRONG, **and** at least one of C4/C5 STRONG, **and** no dominance under C6. *Partial* requires C1 and C2 at least PARTIAL. *Balance is primary* if C1 passes but C6 shows dominance. *Search is primary* if C2 is STRONG while the no-contact share rises materially above Phase 0's 11.11%. *Mechanical concern remains* if C1 and C2 both fail their partial thresholds while contact is at least as frequent as Phase 0's.

---

## N. Phase 0 baseline reproduction (R4A)

Executed before anything else, against the frozen Phase 0 corpus with the current analyzer.

- **All 288 frozen Phase 0 matches re-analysed: 0 mismatches on every field Phase 0 published.** The only apparent differences were `entrant_order` serialised as a tuple rather than a list (identical after JSON round-trip) and the three labels the corpus runner attaches after analysis (`match_label`, `agent_a`, `agent_b`).
- **Aggregate reproduces exactly:** decisive **114 (39.58%)**, timeout **174 (60.42%)**, tie **126 (43.75%)**, mean duration **680.1**, mean stagnation **432.1**, mean combat writes **5,566.8**, mean core damage **98.7** — every published figure, to the digit.
- **Deterministic spot reruns: 8/8 byte-identical**, whole-replay and tick-stream, across the outcome archetypes Phase 0 named. All eight case-study outcomes reproduce (`attacker vs local_defender` seed 1 tie@1000; `quorum vs local_defender` seed 1 A@7; `claimer vs quorum` seed 6 B@5; `quorum` self-play seed 1 A@60; `claimer vs attacker` seed 7 B@999). Analyzer output identical in all 8.
- **Stable-V4 purity: 8/8.** Every rerun header records `bytefray-rules-4` with no `process_integrity` and no `objective_target_oracle` key.
- **R3 reproduces exactly.** All 25 R3B runs and all 384 R3C runs re-analysed with **0 analyzer-field mismatches**, and R3's published Section M.1 table reproduces digit-for-digit (baseline 16–19–61 / 12 captures / 1361.2 mean core writes / 1.52 mean deficit / 912.4 mean ticks; sweeper 17–19–60 / 17 / 304.7 / 2.36 / 774.1; mobile 5–39–52 / 5 / 17.7 / 2.19 / 717.2).
- **R1 and R2 reproduce exactly.** 35 R1B runs and 28 R2B runs re-analysed with 0 analyzer-field mismatches. (R2's stored rows carry two runner-added arm annotations, `mortality` and `oracle`, which are not analyzer outputs.)

**The measurement baseline has not drifted.** R4 proceeded.

---

## O. R4 evaluation corpus

```
python -m tools.research.v5.r4_runner --stage manifest
python -m tools.research.v5.r4_runner --stage qualification    # dev seeds 101-108
python -m tools.research.v5.r4_runner --stage evaluation       # eval seeds 1-8
```

**288 matches**, 36 ordered pairings × 8 seeds, arena 512, max_ticks 1000, `bytefray-rules-4`, self-play included, executed in 66.7 s. Artifacts: `runs/v5_r4_evaluation/r4_evaluation_metrics.jsonl`.

---

## P. Population-level results — Phase 0 vs R4

Both corpora are 288 matches under identical rules, arena, tick limit and seeds. **Population identity is the experimental factor.** Because the populations differ, no match has a direct causal pair; the comparison is distributional.

| Metric | Phase 0 | R4 | Δ |
|---|---:|---:|---:|
| **Decisive (`last_agent_standing`)** | 114 (39.58%) | **186 (64.58%)** | **+25.00pp** |
| **Timeout (`tick_limit`)** | 174 (60.42%) | **102 (35.42%)** | **−25.00pp** |
| **Tie** | 126 (43.75%) | **88 (30.56%)** | **−13.19pp** |
| **Matches with ≥1 core capture** | 114 (39.58%) | **186 (64.58%)** | **+25.00pp** |
| Mean duration (ticks) | 680.1 | 371.1 | −309.0 |
| Median duration (ticks) | 1000 | **19** | −981 |
| Mean stagnation ticks | 432.1 | **257.8** | −174.2 |
| — active stagnation | 347.4 | 184.2 | −163.2 |
| — passive stagnation | 84.7 | 73.7 | −11.0 |
| Mean longest no-progress interval | 418.8 | 274.0 | −144.8 |
| Mean max simultaneous core deficit | 4.125 | **5.837** | +1.712 |
| Mean distinct core cells ever lost | 4.462 | 6.021 | +1.559 |
| Mean distinct core cells damaged | 5.59 | 6.34 | +0.75 |
| Mean hostile writes (expanded) | 282.7 | 904.8 | +622.1 |
| **Mean combat writes (legacy counter)** | **5,566.8** | **944.2** | **−4,622.6** |
| Mean contact → first core damage | 161.1 | **3.5** | −157.5 |
| Mean first core hit → capture | 26.7 | 20.1 | −6.7 |
| Matches with meaningful contact | 256 (88.89%) | 263 (91.32%) | +2.43pp |
| No-contact matches | 32 (11.11%) | 25 (8.68%) | −2.43pp |

**Activity inverted into progress.** The R4 population makes roughly **one sixth** the combat writes of Phase 0's while producing **63% more** capture outcomes — the same inversion R3 measured on a single agent (Section K.4 there), now at population scale.

---

## Q. Per-agent results

**Phase 0** (162 decisive wins total):

| Agent | W | L | T | Win% | Captures made | Captures suffered | Timeout wins | Mean ticks | Share of wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `v4_quorum` | 84 | 8 | 4 | 87.5 | 72 | 8 | 12 | 179.8 | **51.9%** |
| `v4_claimer` | 24 | 72 | 0 | 25.0 | 24 | 42 | 0 | 535.6 | 14.8% |
| `v4_scout` | 22 | 15 | 59 | 22.9 | 6 | 8 | 16 | 916.7 | 13.6% |
| `v4_concentrated_attacker` | 16 | 19 | 61 | 16.7 | 12 | 8 | 4 | 912.4 | 9.9% |
| `v4_defender_scout` | 16 | 16 | 64 | 16.7 | 0 | 16 | 16 | 835.0 | 9.9% |
| `v4_local_defender` | 0 | 32 | 64 | 0.0 | 0 | 32 | 0 | 700.9 | 0.0% |

**R4** (200 decisive wins total):

| Agent | W | L | T | Win% | Captures made | Captures suffered | Timeout wins | Mean ticks | Share of wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `v4_quorum` | 84 | 8 | 4 | 87.5 | 72 | 8 | 12 | 182.4 | **42.0%** |
| `v5r4_recon_striker` | 45 | 22 | 29 | 46.9 | 45 | 16 | 0 | 405.5 | 22.5% |
| `v5r4_siege_regional` | 37 | 20 | 39 | 38.5 | 37 | 13 | 0 | 483.3 | 18.5% |
| `v5r4_territory_expander` | 24 | 37 | 35 | 25.0 | 22 | 37 | 2 | 411.0 | 12.0% |
| `v5r4_dual_operator` | 10 | 48 | 38 | 10.4 | 10 | 47 | 0 | 414.9 | 5.0% |
| `v5r4_core_warden` | 0 | 65 | 31 | 0.0 | 0 | 65 | 0 | 329.4 | 0.0% |

**Head-to-head** (row = A, column = B; winsA–winsB–ties over 8 seeds):

| A \ B | siege_reg | recon_str | core_ward | dual_oper | territory | quorum |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| **siege_regional** | 0-0-8 | 1-2-5 | 8-0-0 | 7-0-1 | 2-1-5 | 0-6-2 |
| **recon_striker** | 3-0-5 | 4-2-2 | 8-0-0 | 3-0-5 | 4-1-3 | 0-6-2 |
| **core_warden** | 0-8-0 | 0-8-0 | 0-0-8 | 0-0-8 | 0-8-0 | 0-8-0 |
| **dual_operator** | 0-8-0 | 0-4-4 | 1-0-7 | 6-0-2 | 0-1-7 | 0-8-0 |
| **territory_expander** | 0-3-5 | 0-7-1 | 8-0-0 | 3-3-2 | 0-2-6 | 0-8-0 |
| **quorum** | 8-0-0 | 8-0-0 | 8-0-0 | 8-0-0 | 8-0-0 | 5-3-0 |

---

## R. Search vs conversion decomposition

This is the decisive table. Every match is placed in exactly one bucket, using the engine's own recorded outcomes.

| Bucket | Phase 0 | R4 | Δ |
|---|---:|---:|---:|
| **no contact** (never saw an opponent) | 32 (11.1%) | 25 (8.7%) | −2.4pp |
| **contact, but enemy core never reached** (zero enemy-core writes) | 11 (3.8%) | **47 (16.3%)** | **+12.5pp** |
| **core reached, but no capture** | **139 (48.3%)** | **33 (11.5%)** | **−36.8pp** |
| **capture** | 106 (36.8%) | **183 (63.5%)** | **+26.7pp** |

Restricted to contact matches:

| Metric | Phase 0 | R4 | Δ |
|---|---:|---:|---:|
| reaching ≥ 2 simultaneous deficit | 53.91% | **81.37%** | +27.46pp |
| reaching ≥ 4 simultaneous deficit | 51.95% | **80.99%** | +29.04pp |
| reaching ≥ 8 / capture | 41.41% | **69.58%** | +28.18pp |
| contacted but never captured | 58.59% | **30.42%** | −28.18pp |
| contacted but timeout | 58.59% | **30.42%** | −28.18pp |

**Post-core-contact conversion — the sharpest single statistic.** Among matches where an attacker actually reached the victim's core (≥1 enemy-core write), how often did a capture follow?

| Victim | Phase 0 reached → captured | R4 reached → captured |
|---|---|---|
| all victims | 114 / 321 = **35.5%** | 186 / 241 = **77.2%** |
| `v4_quorum` (present in both populations, unchanged) | 8 / 29 = 27.6% | 8 / 24 = 33.3% |

**The bucket that collapses is exactly the one Phase 0 named.** "Core reached but no capture" falls from 48.3% of matches to 11.5%, and post-core-contact conversion more than doubles, from 35.5% to 77.2%.

**The residual failure mode changed character.** "Contact but core never reached" *rose* from 3.8% to 16.3%. That is a **search/approach** limitation, not a conversion limitation: those attackers saw an anchor and never located a core. It is visible most clearly against `v4_quorum`, whose 256-reach oracle sees an approaching attacker long before a reach-24 or reach-40 attacker can see it — the reach/sensing coupling R3 flagged and R4 was forbidden to change (Section 23; deferred, Section Y).

---

## S. Core-geometry analysis

| Metric | Phase 0 | R4 |
|---|---:|---:|
| mean max simultaneous deficit | 4.125 | **5.837** |
| mean distinct core cells ever lost | 4.462 | 6.021 |
| mean distinct core cells targeted | 5.59 | 6.34 |
| mean distinct core cells damaged | 5.59 | 6.34 |
| mean unique hostile write addresses | 87.8 | 16.6 |
| mean hostile writes (expanded) | 282.7 | 904.8 |

R4 attackers write **more hostile bytes into far fewer distinct addresses** — they concentrate on a core-width region and hold it, rather than smearing writes across whatever an opponent's anchor wandered through. Coverage and simultaneity converge (6.34 cells damaged, 5.84 max simultaneous deficit), which is what capture requires; in Phase 0 they also converged but at a much lower level (5.59 / 4.125), and the population could not close the last cells.

---

## T. Stagnation analysis

| Metric | Phase 0 | R4 | Δ |
|---|---:|---:|---:|
| mean stagnation ticks | 432.1 (63.5% of mean match) | **257.8** | −174.2 |
| mean active stagnation | 347.4 | 184.2 | −163.2 |
| mean passive stagnation | 84.7 | 73.7 | −11.0 |
| mean longest no-progress interval | 418.8 | 274.0 | −144.8 |

Active stagnation — fighting without converting, the Phase 0 pathology — falls by **47%**. Passive stagnation barely moves (−13%), consistent with Section R: R4 changed what agents do after they find each other far more than whether they find each other.

---

## U. Balance / dominance analysis

**No single strategy overwhelms the population.** `v4_quorum` remains the strongest member at 87.5% — identical to Phase 0, as it must be, since it is the same agent — but its **share of all decisive wins falls from 51.9% to 42.0%**, below the preregistered 60% dominance threshold. Five of six members win at least one match, the same as Phase 0. The win distribution is materially flatter: Phase 0's non-Quorum members won 16–24 matches each; R4's win 10–45.

**A leave-one-out sensitivity analysis** (declared here as post-hoc; the primary corpus remains all 288 matches, and no matchup was excluded from the reported result):

| Corpus | C1 capture | C2 contacted-no-capture | C3 timeout | C4 deficit | C5 stagnation | Gate |
|---|---:|---:|---:|---:|---:|---|
| **Phase 0 full** | 39.6% | 58.6% | 60.4% | 4.12 | 432.1 | **FAIL** |
| **R4 full (PRIMARY)** | **64.6%** | **30.4%** | **35.4%** | **5.84** | **257.8** | **STRONG** |
| R4 − siege_regional | 68.0% | 27.3% | 32.0% | 6.26 | 200.2 | STRONG |
| R4 − recon_striker | 65.5% | 26.9% | 34.5% | 5.76 | 242.6 | STRONG |
| R4 − core_warden | 60.5% | 35.5% | 39.5% | 5.39 | 333.2 | PARTIAL |
| R4 − dual_operator | 67.5% | 24.4% | 32.5% | 5.63 | 297.2 | STRONG |
| R4 − territory_expander | 64.5% | 29.9% | 35.5% | 6.07 | 226.2 | STRONG |
| R4 − quorum | 57.0% | 36.6% | 43.0% | 5.39 | 309.1 | PARTIAL |
| **R4 − core_warden AND quorum** | 50.8% | 44.1% | 49.2% | 4.73 | 423.6 | PARTIAL |
| **Phase 0 − local_defender AND quorum** | 20.3% | 82.7% | 79.7% | 3.11 | 759.8 | **FAIL** |

The result survives four of six single-agent removals at STRONG. The two that degrade — dropping the warden, or dropping Quorum — still meet C1, C2 and C3 at their **STRONG** thresholds and fail only the C4/C5 tiebreak. Phase 0 never reaches STRONG under *any* leave-one-out, and even R4's most hostile subsetting (dropping both the weakest defender and the strongest agent) leaves R4 at PARTIAL where the equivalent Phase 0 subset FAILs by a wide margin.

**One honest asymmetry, disclosed.** `v5r4_core_warden` is the most-captured member (67.7% of its matches), *more* than the two archetypes with no defence at all (siege 13.5%, recon 16.7%). Its READ-verify repair loop carries a detection latency that a one-tick 8-cell burst simply outruns, whereas `v4_quorum`'s guardian and `v5r4_dual_operator`'s keeper *proactively rewrite* their cells and survive far better. So R4's population contains one genuinely fragile defender, and it does inflate the capture rate. This is why the leave-one-out row above matters, and why the conclusion is stated as it is: the effect is robust to removing it, but the *magnitude* is not entirely independent of it.

---

## V. Mechanism interpretation — why the metrics changed

Three mechanisms account for the difference, and none of them is an engine change.

1. **Region-width writes convert; point writes do not.** Capture requires owning **zero of eight** cells *simultaneously* at end of tick. An agent that writes one address can flip at most one cell no matter how many times it writes it — Phase 0's `v4_concentrated_attacker` made 7,902 core-targeting writes at a single address across 1,000 ticks for a maximum deficit of 1/8. R4's attackers cycle a whole core-width region with Q = 8 actions against an 8-cell core, so a single tick can cover the entire objective. Mean first-core-hit-to-capture is 20.1 ticks.

2. **Reach scaled to the arena decouples striking from seeing — partially.** R3 proved reach is simultaneously the write radius and the sensor radius, and that the bundled population declares 1–8 in a 512-cell arena. R4's attackers declare 24 and 40, so they can stand off, hold a whole core inside reach, and still see. This is why "core reached but no capture" collapses. It is also why the residual failure moved to *approach*: at reach 24 against Quorum's 256, an attacker is seen long before it can see.

3. **Defence is a design property, not a mechanical guarantee.** The two defenders that survive best (`v4_quorum`, `v5r4_dual_operator`) *proactively rewrite* their own cells every rotation; the one that fails (`v5r4_core_warden`) *reads first and repairs after*, and loses the race. Under D = 1 and Q = 8 with a chunked interleaved scheduler, ownership is decided by who wrote a cell last within the tick, so a repair strategy that spends actions learning what to repair is structurally behind one that simply refreshes. This is a genuine strategic finding about V4, obtained without changing V4.

**Activity is not progress.** The R4 population makes 944 mean combat writes to Phase 0's 5,567 while producing 63% more captures. Phase 0's headline "1.77% combat conversion rate" measured a population generating enormous write volume at very few useful addresses; it did not measure a mechanical ceiling.

---

## W. Phase 0 reinterpretation

Phase 0 is not rewritten and its numbers reproduce exactly (Section N). What changes is what they support.

**What remains fully supported.**
- Every Phase 0 *measurement*: 39.58% decisive, 60.42% timeout, 43.75% tie, 432.1 stagnation ticks, 1.77% conversion, `v4_quorum` at 87.5%, `v4_local_defender` at 0 wins in 96. All reproduce bit-identically.
- Phase 0's characterisation of the **bundled population** is accurate and remains the correct description of what ships today.
- Phase 0's **State C** (search deficit) survives and is, if anything, reinforced: no-contact matches remain (8.7% in R4), and the residual R4 failure mode is an approach/discovery problem.

**What is now confounded or superseded.**
- **Phase 0's State-B mechanism is superseded.** "Combat fails to convert because of infinite core repair churn under zero process mortality" does not survive. R3 showed the flagship defender repaired only two addresses; R4 shows that with a competent population, post-core-contact conversion is 77.2%, and that the defenders which *do* resist do so by proactive rewriting, not by exploiting immortality. R1 had already rejected mortality on its own merits; R4 removes the last of its motivating evidence.
- **Phase 0's implied generalisation — that stable V4 mechanics constrain objective conversion — is confounded by population identity.** Holding every rule, seed, arena and corpus dimension fixed and changing only the population moves capture from 39.58% to 64.58% and timeouts from 60.42% to 35.42%.
- **Phase 0's reach table was factually wrong** (R3 correction, carried forward, not silently absorbed).
- **Phase 0's description of `v4_local_defender` as repairing eight cells was wrong** — independently reconfirmed here at 2 cells written across 1,000 ticks.

**Three levels, kept distinct** (following R3's framing):

| Level | Question | R4's answer |
|---|---|---|
| **Population result** | What do the bundled agents do? | Phase 0 is correct and reproduces exactly. |
| **Mechanical capability** | What does stable V4 permit? | Broad, repeatable objective play: 186 captures across 288 matches, 5 of 6 archetypes converting, no engine change and no privileged information. |
| **Product-quality agent set** | Do the shipped examples demonstrate the intended game? | **No** — unchanged from R3's answer, and now quantified at population scale. |

---

## X. Engine-research gate

### **PAUSE ENGINE-MECHANIC RESEARCH.**

Per charter Section 22 Outcome A. The competence-controlled population shows substantially higher real core-capture conversion, materially fewer contacted-but-no-capture stalls, lower timeout and tie pathology, meaningful strategic diversity, and no trivial dominant strategy. The next V5 work should concern bundled-agent quality, examples, authoring guidance, presentation, discoverability and balance — **not** a new Ruleset, and not a resumed mechanic search.

---

## Y. Candidate evidence update

| Candidate | Status | Basis |
|---|---|---|
| **Agent competence / example quality** | **STRONGER SUPPORT — now decisively the leading explanation** | Holding rules, arena, ticks and seeds fixed and changing only the population moves capture 39.58% → 64.58%, timeout 60.42% → 35.42%, post-core-contact conversion 35.5% → 77.2%, active stagnation −47%. Robust to four of six leave-one-out removals. |
| **Attack geometry** | **STRONGER SUPPORT (as an agent-design property, not a mechanic)** | Region-width writes convert where point writes cannot; R4 attackers use one sixth the combat writes for 63% more captures. No engine change was required to obtain this. |
| **Search / discovery** | **STRONGER SUPPORT** | The residual failure mode moved here: "contact but core never reached" rose 3.8% → 16.3%, while "core reached but no capture" fell 48.3% → 11.5%. |
| **Reach / sensing coupling** | **SUPPORT UNCHANGED — remains a DEFERRED MECHANICAL CANDIDATE** | Deliberately not changed in R4 (charter Section 23). R4 supplies new *observational* evidence for its importance — a reach-24 attacker is seen by a reach-256 oracle long before it can see — but ran no controlled experiment on it, so its tier is unchanged. |
| **Process mortality** | **SUPPORT UNCHANGED (remains CONTRADICTED from R1)** | R4 ran no mortality experiment. Its motivating evidence is now fully undermined: the repair-churn diagnosis is superseded (Section W) and competent populations convert without any mortality mechanic. |
| **Target persistence / objective awareness** | **WEAKER SUPPORT as a mechanic; STRONGER as an agent-design property** | Every R4 archetype that converts carries contact or ownership memory it derived legally. What R2's engine-provided oracle failed to deliver, ordinary agent memory delivers. |
| **Replication / deployment** | **NOT TESTED** | Held constant by design. |
| **Capacity economics (Q = 8)** | **WEAKER SUPPORT** | Held constant. The winning arms use dramatically *fewer* actions; quota was never the constraint. |
| **Specialization** | **SUPPORT UNCHANGED** | R4 was not a controlled specialization experiment. The 2-process and 6-process members bracket the field rather than sweeping it. |
| **Process-local information** | **SUPPORT UNCHANGED** | Neither locality nor fusion was changed. |
| **V4 process core size = 8** | **WEAKER SUPPORT** | 8 cells is reached simultaneously in 183 of 263 contact matches. It is not an unreachable bar; it is unreachable for an agent that writes one address. |
| **Territory incentives** | **SUPPORT UNCHANGED / NOT TESTED as a mechanic** | Scoring was unchanged. R4 does newly show a territory-first archetype can be competitive (`v5r4_territory_expander`, 64–18–14 against the canonical population), which Phase 0's `v4_claimer` was not — an agent-design observation, not a scoring change. |
| *(new)* **Proactive vs reactive core repair** | **NEW CANDIDATE — STRONG SUPPORT FOR FURTHER STUDY (agent-design, not mechanic)** | Section V.3: under D = 1 with a chunked interleaved scheduler, a defender that READs before repairing loses the ownership race to one that blindly refreshes. `v5r4_core_warden` is captured in 67.7% of its matches; `v4_quorum` in 8.3%. |

---

## Z. Validation

**New R4 tests — 35, all passing.**

- `engine/tests/test_v5_research_r4_agents.py` — **28 tests** (mostly parameterised across all five research agents): product-path unreachability (not starters, not in the catalog, not in the shipped starter tree), research-loader resolution, canonical agents untouched, frozen process-declaration equivalence read back out of the replay, reach/action legality from trace, the legal-information boundary, determinism, and three archetype-behaviour tests (regional multi-cell pressure, defender own-core coverage, mobile displacement).
- `engine/tests/test_v5_research_r4_population.py` — **7 tests**: development/evaluation seed disjointness, qualification fixtures disjoint from the evaluation population, Phase 0 corpus shape (288 / 36 pairings / 48 self-play cells), manifest declarations generated from execution, the retained Quorum fingerprint, declared strategic diversity, preregistered-gate structure, and both additive-metric tests.

**Legality, proven from trace rather than inspection** (200 ticks each, vs `v4_quorum`, seed 3):

| Agent | Applied | Out-of-reach | Invalid | Exception | Max actions/tick | Action kinds | Stable-V4 pure |
|---|---:|---:|---:|---:|---:|---|:--:|
| `v5r4_siege_regional` | 248 | **0** | 0 | 0 | 8 | read/write/move | yes |
| `v5r4_recon_striker` | 262 | **0** | 0 | 0 | 8 | read/write/move | yes |
| `v5r4_core_warden` | 14 | **0** | 0 | 0 | 8 | read/write | yes |
| `v5r4_dual_operator` | 300 | **0** | 0 | 0 | 8 | write/move | yes |
| `v5r4_territory_expander` | 14 | **0** | 0 | 0 | 8 | write | yes |

Every observation any R4 agent was ever handed contained only the twelve ordinary `ObservationV2` fields, and every address in every `visible_enemy_anchor_addresses` tuple was asserted to be an address a live enemy process actually occupied at that tick.

**Prior-phase regressions.** All re-analysed with the current analyzer: Phase 0 **288/288 runs, 0 published-field mismatches**; R1B **35 runs, 0**; R2B **28 runs, 0**; R3B **25 runs, 0**; R3C **384 runs, 0**. Pre-existing suites `test_v5_research_analyzer.py`, `test_v5_research_r1_metrics.py`, `test_v5_research_r2_metrics.py`, `test_v5_research_r3_metrics.py`, `test_v5_research_r3_agents.py`, `test_process_mortality.py`, `test_objective_target_oracle.py` are **unmodified** and pass.

**Stable V4 regression.** `test_v4_stable_ruleset_equivalence.py`, `test_v4_alpha2_placement.py`, `test_v4_alpha2_scheduler.py`, `test_v4_runtime_default_ruleset.py`, `test_ruleset_policy.py` unmodified and passing (266 tests together with R3's and R4's research suites).

**Analyzer change.** One strictly additive field, `distinct_own_core_cells_written` (+18 lines, `tools/research/v5/analyzer.py`). Nothing Phase 0, R1, R2 or R3 published was renamed or recomputed, proven by the 760 frozen-run re-analyses above. R4 created **no parallel analyzer** and reused `corpus_runner.run_single_match`, the shared match-execution seam.

**Full suite:** `python -m pytest` across all three configured `testpaths` — **3,098 tests, 0 failures, 0 errors, 14 skipped**, 343.5 s, exit code 0 (JUnit XML confirms `tests="3098" errors="0" failures="0" skipped="14"`). This is exactly R3's 3,063 plus R4's 35. The known intermittent Windows file-lock flake in `test_agent_evaluation_parallel.py` did not occur.

**Ruff:** `ruff check .` — all checks passed (two auto-fixable findings in the new `r4_runner.py`, an f-string without placeholders and an implicit-concatenation artifact, fixed with `--fix` and re-verified).

**Mypy:** `mypy engine/src/battle_engine` — Success, 0 issues, 102 source files. `mypy client/src/battle_client` — Success, 0 issues, 16 source files.

**Determinism.** Proven at three levels: all six frozen fingerprints identical to the preregistration after evaluation *and* after the directory move; **18/18 deterministic reruns byte-identical** to the frozen evaluation corpus (whole replay and tick stream) with identical analyzer output; and per-agent byte-identical tick streams across repeated runs (`test_r4_agent_is_deterministic`, all five agents).

**Reproduction:**

```
python -m tools.research.v5.r4_runner --stage manifest
python -m tools.research.v5.r4_runner --stage qualification
python -m tools.research.v5.r4_runner --stage evaluation
```

---

## Secondary analysis — paired role-lineage comparison

Charter Section 21. Each R4 archetype played the **same six canonical opponents, the same seeds 1–8 and both slot orders** its canonical counterpart already played in Phase 0 (n = 96 each), so the records are directly comparable. This is a secondary analysis; the primary experiment remains the population-level comparison in Section P.

| Subject | W–L–T | Captures made | Captures suffered | Contact | Mean max deficit | Mean core writes | Mean ticks |
|---|---|---:|---:|---:|---:|---:|---:|
| `v4_concentrated_attacker` (Phase 0) | 16–19–61 | 12 | 8 | 59 | 1.52 | 1,361.2 | 912.4 |
| **`v5r4_siege_regional`** (R4) | **38–26–32** | **37** | 20 | **88** | **3.65** | **25.4** | 450.4 |
| `v4_scout` (Phase 0) | 22–15–59 | 6 | 8 | 67 | 1.16 | 1,310.3 | 916.7 |
| **`v5r4_recon_striker`** (R4) | **48–23–25** | **48** | 17 | **87** | **4.74** | **41.5** | 332.2 |
| `v4_claimer` (Phase 0) | 24–72–0 | 24 | 42 | 0 | 2.01 | 6.8 | 535.6 |
| **`v5r4_territory_expander`** (R4) | **64–18–14** | **40** | **18** | **71** | **3.85** | 36.2 | 418.5 |
| `v4_defender_scout` (Phase 0) | 16–16–64 | 0 | 16 | 85 | 1.52 | 1,519.8 | 835.0 |
| **`v5r4_dual_operator`** (R4) | **43–16–37** | **29** | 16 | **92** | **3.81** | **114.5** | 548.7 |
| `v4_local_defender` (Phase 0) | 0–32–64 | 0 | 32 | 31 | 0.00 | 0.0 | 700.9 |
| **`v5r4_core_warden`** (R4) | **0–32–64** | 0 | **16** | **41** | 0.00 | 0.0 | 834.5 |

The attacker lineages convert 3–8× more often on **50× fewer** core-targeting writes. The defender lineage is the instructive null: `v5r4_core_warden` posts the *identical* 0–32–64 record as the bundled turtle, while suffering **half** as many core captures (32 → 16). Better defence did not become wins, because under stable V4 scoring a defender that claims no territory has no path to a fallback victory — an honest, archetype-consistent result and a direct illustration that R4's agents were not tuned for win rate.

---

## Final verdict

### **1. STRONG POPULATION CONFOUND — STABLE V4 OBJECTIVE PLAY IS BROADLY HEALTHY**

This is the verdict the **preregistered** decision rule returns, and it is reported on that basis rather than chosen after the fact: C1 (64.58% ≥ 55%), C2 (30.42% ≤ 40%), C3 (35.42% ≤ 45%), C4 (5.837 ≥ 5.5) and C5 (257.8 ≤ 300) all meet their STRONG thresholds, and C6 shows no dominance (top member 42.0% of wins, below the 60% threshold, with 5 of 6 members winning).

**Scoped precisely.** Holding `bytefray-rules-4` and every match parameter fixed and changing only which agents play, Phase 0's headline pathology largely dissolves: capture 39.58% → 64.58%, timeout 60.42% → 35.42%, tie 43.75% → 30.56%, active stagnation −47%. The decisive quantity is post-contact conversion — among matches where an attacker reached the enemy core, capture followed **35.5%** of the time in Phase 0 and **77.2%** of the time in R4, and the "core reached but no capture" bucket falls from 48.3% of all matches to 11.5%. Phase 0's premise that combat does not convert into victory was, to a large extent, measuring a population of agents that could not express the objective.

**Three qualifications, stated rather than buried.**

1. **The magnitude is not fully independent of population composition.** Removing `v5r4_core_warden` or `v4_quorum` drops the gate from STRONG to PARTIAL — both failing only the C4/C5 tiebreak while still meeting C1, C2 and C3 at STRONG. Phase 0 reaches STRONG under no leave-one-out at all, and R4's most hostile subsetting still lands at PARTIAL where Phase 0's equivalent FAILs badly. The direction is robust; the exact size is not.
2. **One R4 defender is genuinely weak.** `v5r4_core_warden` is the most-captured member because READ-then-repair loses the within-tick ownership race to an 8-cell burst. It inflates the capture rate, and it is the reason qualification alone is not sufficient evidence — the leave-one-out row is.
3. **The residual failure mode is now search/approach, not conversion.** "Contact but core never reached" rose from 3.8% to 16.3%. The preregistered gate defined "search" narrowly as the no-contact share (which *fell*, 11.11% → 8.68%), so this residual did not route the verdict to Outcome D — but it is the honest characterisation of what still fails, and it is where the next question points.

**What this means for the V5 programme.** Three engine mechanics have now been examined and none survived: R1 rejected mortality, R2 rejected the objective oracle, and R3 plus R4 have dismantled the diagnosis that motivated both. The evidence base for a V5 gameplay mechanic has been measuring the simplicity of six bundled agents. Engine-mechanic research should **pause**. The reach/sensing coupling stays recorded as a deferred mechanical candidate; R4's purpose was to determine whether another mechanic experiment was needed at all, and the answer is that it is not — yet.

**R4's population is a scientific control, not a product proposal.** These are the "R4 competence-controlled research population", not new bundled agents. Whether any of them should inform a shipped example, starter, or benchmark is a separate product decision that this phase does not make, and one of them (`v5r4_core_warden`) is a demonstrably poor agent retained precisely because a control population must contain real weaknesses.

### Recommended next research question (exactly one)

> **Does Bytefray's shipped agent population and authoring guidance let a player discover the objective-capable play that stable V4 already supports?**
>
> This is a product-quality question, not a mechanic question, and it is the one Outcome A directs the programme toward. R4 establishes that stable `bytefray-rules-4` supports broad, diverse, decisive objective play — 186 captures in 288 matches across five distinct archetypes with no engine change — while the six agents Bytefray actually ships produce 60% timeouts and a 1.77% conversion rate. The gap between what the game permits and what its examples demonstrate is now measured, and it is large. The work is to determine which competence properties a player must discover in order to play the real game (region-width writes rather than point writes; declared reach scaled to the arena; persistent contact memory; proactive rather than reactive core repair), whether the current starter set, documentation and Designer surface teach any of them, and what a product-quality bundled population would look like — evaluated as a product decision about examples and onboarding, with the shipped `v4_*` agents and every published Phase 0 number left intact.
>
> Per the standing research-integrity rule, R4 reports the need for a better shipped population as a **finding**, not as permission to replace the bundled agents. Deciding to ship anything is out of scope for this phase.
