# Bytefray V6 E4 (proposed): Order vs Evaluation Timing — Causal Design and Adversarial Review

Design review only. **No repository file was modified**, nothing was committed or pushed, and no Ruleset was created. The working tree was clean before and after. All probe code ran from the session scratchpad.

**Evidence tiers.**

- **[SOURCE]** current source at `89ced9c`.
- **[RUN]** the unmodified repository, executed.
- **[CORPUS]** descriptive reads of the preserved E2/E3 corpora and of the frozen E3 telemetry. The T-E3 and T-E3K1 corpora are the would-be E4 controls. No threshold in this review was taken from them.
- **[PROBE]** a scratch-only patch of the real controller at seed 42, which is outside matrix seeds 1–32, run on named scenarios only: about 105 matches, 86 of them full-length and 18 short traces of 3–6 ticks. Exploratory priors, not results (Appendix P).
- **[DOC]** prior research records.

## Verdict

1. **"Last-action position" and "end-of-tick evaluation" are not separable causes.** [SOURCE, PROBE-combinatorial] With two entrants, Q = 8, chunk 2 and rotation, every alternative in-tick order that keeps equal quota, rotation and the stock run structure is the *unchanged* global action stream with the tick boundary moved by 2, 4 or 6 chunks. Moving who acts last and moving when the tick is judged are therefore one manipulation. The last action only matters through a sample, and a single sample always has a last actor. No scheduler-only experiment can separate A from B.
2. **A capture-evaluation-only treatment cannot move the E3 residual.** [SOURCE] Agents never observe capture state. Any change to when or how capture is judged therefore leaves the match byte-identical until the first alive-status divergence, and PM-1 is invariant until then. Every member of that family is a new capture-strictness rule. [PROBE] Against the spread sniper, the disrupt guard's core is at zero at some chunk boundary in 998 of 1,000 ticks and at zero at no tick end.
3. **The better causal variable is last response on each contested cell**: which entrant writes a contested cell after the opponent's final write to it, before the single end-of-tick sample. The stock order makes the tick's second mover the later responder in **all four passes**. Where a contest runs across passes, that hands every contested cell to one entrant. Where a contest occurs only in the opening pass, the second mover wins it under **every** rotation-preserving order. In the opening pass, the anchor hit is itself a write to core cell 0, because every process spawns on its core base.
4. **The E3 population split is explained by where the contest sits in the pass structure.** [CORPUS + SOURCE + PROBE] Of E3's 353 last-mover-leaning or last-mover-dominated stalemate cells, 257 (73%) are opening-pass anchor contests, 96 (27%) are multi-pass sweep or drift contests, and none is a final-chunk effect. The 192 painter cells in the neutral class are incidental painting-front contests.
5. **Recommendation: a scheduler-order experiment next, using mirrored pass order (`F L F L | L F L F`), not ABBA.** It is one policy field. It holds constant Q, chunk size, rotation, the stream's run structure and alternation count, capture code, K, λ, scoring and replay schema. It balances response order 2/2 across passes and gives the final chunk to the first mover. The three candidate mechanisms therefore predict three distinguishable signatures:
   - the privilege **flips** to the final-chunk owner (final position);
   - it is **neutralized** (concentration of response order);
   - it **stays** with the second mover (opening pass).

   [PROBE] prior: sniper v disrupt guard goes from 999 swings to 1, every opening-pass matchup is unchanged, and nothing flips.
6. **Parent: the E3 primary treatment (K = 2, λ = 1), with the K = 1 companion kept as a deconfounder.** The E3 immunity theorem G.5 carries over to the mirrored order as G.5′, so K = 2 hides outcome effects that K = 1 exposes. [PROBE] Under K = 1, sniper v repair guard changes from a capture at tick 8 to a tie. Both controls are the preserved E3 treatment corpora, reproduced byte for byte.
7. **The instrument needs three fixes before any E4 verdict.**
   - Twin-mirror orientation swaps are a pure relabelling. [CORPUS] 320 of 320 orientation pairs have identical tick records in C-E2, T-E3 and T-E3K1. Mirror SDI is therefore 1.0 by construction whenever a seed is decisive.
   - PM-1's 10-swing rule hides exactly the success case: an extinguished oscillation becomes `NOT_SCOREABLE`.
   - `e2_counter` has the same outcome as `e2_greedy_painter` in 512 of 512 comparable cells under λ = 1. [CORPUS]

---

## A. Repository Baseline

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `89ced9c4a18d85a1f48fa97c5b9b3cf553313c50` ("docs(v6): record the E3 slot-limited disruption results") |
| Upstream | After `git fetch`, `v6-research...origin/v6-research` shows no ahead/behind, so it is in sync |
| Tree | Clean (`git status --porcelain` empty) before and after, including after the probe and test runs |
| Python / platform | 3.13.14, `Windows-11-10.0.26120-SP0`, repo `.venv` |
| Focused tests [RUN] | **265 passed** in 27.4 s: `test_v4_exploit_characterization`, `test_e3_slot_limited_disruption_semantics`, `test_ruleset_v6_research_disruption_slot`, `test_ruleset_policy`, `test_v6_e3_parent_byte_identity`. This is a focused subset, not the suite. |
| Rulesets (`ruleset_policy.py:700-745`) | Stable: `bytefray-rules-4`. Active research: `-6-research-scale`, `-6-research-capture-hold-k2`, `-6-research-capture-hold-k2-disruption-slot1`, `-6-research-disruption-slot1`. Retired but still executable: `-scale-move`, `-scale-move-proportional`. |
| E2 corpus | `runs/research_v6_e2/v6-e2-matrix-v1-9048907fdc3b/{C-V4,C-RS,T-E2}` plus `control_gate.json` and `freezes/`, preserved |
| E3 corpus | `runs/research_v6_e3/v6-e3-matrix-v1-634132ec3c15/{C-E2,T-E3,C-RS,T-E3K1}/{F1,F2,F2-P,F4}`, preserved. Freeze directory `freezes/v6-e3-freeze-v1-506811e78ad8/`: `e3_analysis.json`, `control_populations.json`, the treatment gates, and per-cell telemetry for all four conditions plus historical T-E2 and C-RS. |
| E4 | No implementation, Ruleset, tooling or registration exists. |
| Research state | E2 completed. E3 completed, with results at `89ced9c`. |

---

## B. E3 Findings Relevant to E4

From the frozen E3 records [DOC], verified against frozen telemetry [CORPUS]:

- **Whole-tick denial is gone.** The exclusive-tick share is 0 in both λ = 1 arms. The G.4 minimum (5 as first mover, 4 as second) is attained.
- **The residual is a mixture, not one moderate effect.** The E3 stalemate population (738 cells, defined on C-E2) under T-E3 splits into 287 strict last-mover, 66 last-leaning, 224 neutral and 161 `NOT_SCOREABLE` cells. The median PD of 0.714 describes that mixture. [CORPUS] The per-pairing composition is in §D.
- **Seat determination fell** in F1 from 3 seat-determined pairings to 0, with maximum seat bias 0.0625. The guarded-painter mirror has SDI 1.0 with bias +0.1875. §S-7 explains why mirror SDI is degenerate.
- **The companion (K = 1)** shows the same tick-level lock in the same canonical pairing. [CORPUS] Sniper v disrupt guard has FMS 0.000 with 999–1,000 swings under both T-E3 and T-E3K1. The companion's sharper exposed-population median (FMS 0.019) is partly compositional (§E.5).
- **D9 / G.5.** There are 0 completions against continuous repairers under T-E3 and 192 under T-E3K1.
- **Correction of one descriptive figure.** [CORPUS] The results record (§F.9, §G.1) says the guarded-painter mirror went to "Seat A in 20 seeds and Seat B in 12". Both the harness cell records and the frozen telemetry give **19 A-seeds and 13 B-seeds** (38 / 26 matches), with no mixed seeds in F2 or F2-P. The bias the record quotes, +0.19, is the 19/13 value (+0.1875); 20/12 would give +0.25. No registered verdict is affected. A dated erratum is recommended rather than an in-place edit (§S-8).

---

## C. Exact Current Tick Timeline (source-derived)

All line references are to `process_runtime.py` unless stated otherwise. The Ruleset is E3 primary: chunked, chunk 2, rotation on, K = 2, λ = 1.

| Step | Operation | Kind | Where |
|---|---|---|---|
| 0 | At construction: 8 core cells per entrant seeded `0xCE`, owned by self. **Every process is placed on its core base**, so its anchor is core cell 0. | State init | `714-748` |
| 1 | Tick `t` begins: clear tick diffs, snapshot `pre_tick_core_owners` for live entrants, zero `cpu_used`, record already-disrupted processes | Bookkeeping | `1044-1070` |
| 2 | First mover = seat `(t-1) mod 2`. Pass structure: 4 passes, each giving every live entrant 2 offers in rotated order. Stream: `F F L L F F L L F F L L F F L L` | Scheduler | `scheduler.py:78-95`, `ruleset_policy.py:293-315` |
| 3 | Each offer: λ = 1 wrapper snapshots the suppressed set → effective quotas over unsuppressed processes → round-robin selection → forfeit if none → decrement suppressed counters in `finally` | Scheduler/runtime | `1319-1346`, `822-949` |
| 4 | Observation built **per callback**: visible enemy anchors sensed by unsuppressed own processes | Sensing | `1093-1108`, `780-820` |
| 5 | `act()` → forfeit path on exception or invalid action (`alive = False` **mid-tick**) | Lifecycle | `1114-1208` |
| 6 | Action applied: MOVE / READ / **WRITE** (`vm._wr8`, which sets the owner). A WRITE to an enemy anchor also sets `disrupted_until_tick = t+1` and `slots_left = 1` on every enemy process there. | **State mutation** | `1227-1305` |
| 7 | **Final scheduled action**: the second mover's slot 8 (its chunk 4) | — | — |
| 8 | `apply_core_capture` phase 1: `owned_now` from `vm.writer`, streak update, onset attribution by replaying *this tick's* diffs | **Capture evaluation**, kill attribution | `1362-1372`; `python_runtime.py:273-299`, `167-215` |
| 9 | Phase 2: completion → `alive = False`, `core_captured`, +5 kill score, `record_death`, kill/death event | **Alive/dead transition**, scoring | `python_runtime.py:301-311` |
| 10 | `record_tick` (statistics), `score_alive` (+1 per live entrant), `score_territory` (+⌊owned/64⌋) | **Scoring** | `1374-1384`; `scoring.py:18-37` |
| 11 | `publish_tick`: agents (alive, `cpu_used`, termination), score, events, **this tick's `memory_diffs` in write order**, process flags | **Replay snapshot** | `1386-1394`; `telemetry.py` `build_snapshot` |
| 12 | `resolve_termination(alive_count, t, max_ticks)` | **Termination** | `1399-1404` |
| 13 | After the loop: survivor wins; `tie` if nobody is alive; otherwise the score fallback | Outcome | `1413-1426` |

**No board mutation happens after the final action.** Everything after step 7 *reads* the board: capture reads `vm.writer`, territory scoring reads `vm.ownership_counts`, and the replay snapshot carries the diffs that the analyzers use to rebuild the same instant.

**What gives "last state wins" its leverage.** Three consumers sample one instant:

- `apply_core_capture` (`python_runtime.py:278`), for onset, recovery and completion;
- `score_territory`, for tick-limit outcomes;
- the replay snapshot, for the PM-1 instrument.

Each reads the *last writer* of every cell. The entrant whose write to a contested cell comes last before that instant owns the cell as judged. Nothing else in the timeline privileges either entrant.

**The boundary straddle.** The owner of tick `t`'s final chunk is the first mover of tick `t+1`, so the same entrant acts on both sides of every sample (`… F L | L F …`). That is why E2's first-mover dominance and E3's last-mover skew belong to the same entrant, one tick apart.

**Process/runtime lifecycle.** [SOURCE] Direct and worker executors differ only in isolation. The scheduler's `action_slot` is discarded by the direct executor (`453-459`), and Agent API v2 `act(obs)` never receives it, so **agents cannot observe slot positions**. `from_python_entrants` fixes Q = 8 (`360-368`).

**Observation on the E3 review.** [SOURCE] Write order within a tick *is* recoverable from `memory_diffs`. `vm.py:68-77` coalesces only consecutive writes by the same owner to consecutive addresses, so any interleaved write starts a new diff. What is lost is the mapping from writes to offers: READ, MOVE and suppressed offers leave no diff. The E3 review's "per-action order cannot be recovered" is right about offers and slightly overstated about writes. It is recorded here and not acted on.

---

## D. Residual-Order Taxonomy

### D.1 Source roles of the fixtures (per tick, [SOURCE])

| Fixture | Writes the enemy anchor (= enemy core cell 0) | Repairs own base only | Repairs own non-base core cells | Writes enemy non-base core cells |
|---|---|---|---|---|
| `e2_sniper`, `v4_probe`* | first action | — | — | yes (sweep) |
| `e2_disrupt_guard` | first action | (cell 0 as part of 0–6) | **yes (0–6)** | — |
| `e2_min_guard` | first action | yes | — | yes |
| `e2_repair_guard` | — | — | **yes (cyclic cursor across ticks)** | — |
| `e2_guarded_painter` | first action | yes | — | — (paints outward) |
| `e2_greedy_painter` = `e2_counter`** | — | — | — | — (paints outward) |
| `e2_spread_sniper` | each visible anchor | — | — | yes |
| `e2_spread_defender` | each visible anchor | yes | — | yes |
| `e3_jam_sniper` | on every even action | — | — | yes (odd actions) |

\* The probe writes `anchor + step`, where `step` cycles 0–7 **across the match**, not per tick.
\** Under λ = 1 the counter's trigger ("a whole tick with no callback") cannot fire, because G.4 guarantees at least 4 actions per tick (at least 5 under the mirrored order). [CORPUS] Its outcomes match the greedy painter's in 512 of 512 comparable cells in T-E3 and in T-E3K1, against 256 of 512 under whole-tick C-E2.

**Contest classes, derived from the table alone.**

- **MULTI-PASS.** One side writes the other's non-base core cells and the other repairs non-base core cells, so the same cells are fought in every pass.
- **OPENING-ONLY.** No multi-pass contest exists, but one side writes the other's anchor (its core cell 0) and the other repairs its base. The fight happens once per tick, in the pass where both make those writes: pass 1.
- **INCIDENTAL.** Core cells change hands only when a painting front crosses a core.

### D.2 The E3 stalemate population by mechanism ([CORPUS] T-E3 telemetry on the frozen C-E2 stalemate cells)

| Class | Pairings (Seat A v Seat B, cells) | T-E3 PM-1 | Final action decisive? | Contest pass | Same resources? | Oscillates intra-tick? | Decided by |
|---|---|---|---|---|---|---|---|
| **MULTI-PASS sweep** | sniper v disrupt guard (32), disrupt guard v sniper (32) | FMS **0.000**, 999–1000 swings, strict last | Yes, but so is every pass | every pass | yes: the guard's cells 0–6 | yes (e.g. 7→5→7) | tie at 1000 |
| **MULTI-PASS drift** | probe v disrupt guard (32); disrupt guard v probe (32) | FMS 0.143 (= 1/7), leaning; 0.250 (= 1/4), neutral | partly | drifts with the probe's 8-step cycle against 7–8 actions per tick | yes | yes | tie |
| **OPENING-ONLY** | sniper v min guard (32+32), sniper v spread defender (31 + 1 NS), guarded painter v min guard (32+32), guarded-painter mirror (64) | FMS 0.000–0.007, strict last | **no**: the final chunks paint or attack cells nobody contests | pass 1 | only the base cells | yes: one cell per tick | ties (sniper pairings); captures (painter pairings; the mirror is decisive at ticks 30–378) |
| **OPENING-ONLY** (leaning) | repair guard v guarded painter (20), guarded painter v repair guard (14) | FMS 0.17–0.19 | no | pass 1 (the painter's hit on the guard's base); the guard's cursor sets whether its base repair comes before or after it | base only | yes | score at 1000 |
| **INCIDENTAL** | counter or greedy painter v disrupt guard or min guard, both seats (192) | FMS 0.33–0.38, about 50 swings, neutral | no | set by the painter's stroke count | only when a front crosses | rarely | **territory** at 1000 |
| **Decided early** | probe v min guard (64), probe v spread defender (32), jam v min guard (64), and 1 sniper v spread defender cell | `NOT_SCOREABLE` | — | — | — | — | captures at ticks 3–4, or few swings |

**Totals.** Of the 353 last-leaning or last-dominated cells:

- **opening-only: 257 (73%)**, 223 strict and 34 leaning;
- **multi-pass: 96 (27%)**, 64 sweep and 32 drift.

The neutral 224 are the 192 incidental painter cells plus the 32 disrupt guard v probe drift cells.

### D.3 Mechanism of each class ([SOURCE] plus the [PROBE] traces in §L)

- **Multi-pass sweep.** Both entrants walk the same cells at the same pace: the attacker writes cells 2k and 2k+1 in pass k, and the defender repairs the same pair. **In every pass, the entrant that acts second in that pass wins that pair.** The stock order makes that the same entrant (L) in all four passes, so L owns every contested cell at the sample, and rotation alternates L each tick. That produces the period-2 lock with FMS exactly 0. The final chunk matters only as one pass among four.
- **Opening-only.** The first mover's chunk 1 is "hit the enemy anchor, repair own base". The second mover's chunk 2 does the same, **after** it. The second mover therefore takes the first mover's base and keeps its own, and neither fixture writes those cells again that tick (per-tick `done` sets). The privilege is **second response in the only exchange**, not the last action. It is invariant to any order in which the first mover owns chunk 1 and does not re-contest the cell, and to any sample taken after pass 1.
- **Drift.** The contested cell, or the pass in which it is contested, moves from tick to tick because one side's cursor persists across ticks while action counts are 7 or 8. FMS then takes rational values set by the combined cycle.
- **Incidental.** Core changes come from painting fronts whose timing is set by stroke count, not parity. Outcomes are territory scores, and they are opponent-determined, not order-determined.
- **Spatial/RNG.** Deterministic global agents give 1 trajectory over 32 seeds. Parity is weakened only for RNG-bearing agents and front geometry (painters, spread agents), which is why the incidental and painter-mirror cells vary by seed.

**Answer to the split.** The population does not split by strength. It splits by **where the last write to each contested cell falls in the pass structure**. The E3 question as posed ("who acts last" versus "evaluation instant") addresses only the multi-pass minority.

---

## E. Competing Causal Explanations

### E.1 Hypothesis A (last-action position) ≡ Hypothesis B (evaluation instant)

**Stream-phase theorem.** [SOURCE; PROBE-combinatorial] Setting: n = 2, Q = 8, chunk 2, rotation. The in-tick chunk-owner orders with 4 chunks per entrant and rotation of the first mover are:

- stock `FLFLFLFL`;
- `FLFLFLLF`;
- `FLFLLFLF`;
- `FLLFLFLF`.

Each of the last three is **exactly the stock global chunk stream with the tick boundary shifted by 2, 4 or 6 chunks** (verified on the interior of a 12-tick stream). Odd shifts give unequal per-tick quota (3/5). Every other equal-quota order changes the stream's run structure (§F).

**Consequence.** In this family, changing the in-tick order *is* moving the evaluation instant relative to an unchanged action stream. All tick-scoped rules move with it: the sample, agents' per-tick `done` sets, disruption expiry and quota reset. A and B predict the same thing for any such treatment: the privilege tracks whoever acts just before the sample. **No experiment in the scheduler family can separate them, and no experiment in the evaluation family leaves capture semantics intact (§G).**

### E.2 Hypothesis C: concentration of response order (proposed)

For a tick, let the response profile be r = (r₁, r₂, r₃, r₄), where r_k is the entrant acting second in pass k.

- Stock: r = (L, L, L, L).
- For a contested cell, the judged owner is the entrant with the **last response** on it: the later writer in the last pass in which the cell is contested before the sample.
- **Concentration** means one entrant holds r_k for every pass in which contests occur.
- **Prediction.** Multi-pass contests are locked whenever r is uniform. Balancing r neutralizes them. Opening-only contests follow r₁ alone.

### E.3 Hypothesis D: opening-pass response and anchor co-location

Every process spawns on core cell 0 (step 0), so the disruption hit *is* a core write. That turns the hit-plus-repair exchange at the start of each tick into a contest that r₁ decides. By definition r₁ is the second mover under every rotation-preserving order, so no scheduler order can move it. An evaluation instant could move it only by falling inside pass 1, which would be a new capture rule. **This mechanism explains 73% of E3's last-leaning stalemate cells.**

### E.4 Hypothesis E: not order

Incidental painting fronts, territory scoring and seed geometry. Rotation already makes these parity-neutral.

### E.5 What the K = 1 companion rules out, and what it does not

- **It rules out K = 2 as the generator of the tick-level lock.** [CORPUS] Sniper v disrupt guard has FMS 0.000 under K = 1 and K = 2 alike.
- **It does not rule out K = 2 as an amplifier of outcome effects.** G.5 immunity requires K = 2.
- **It does not discriminate scheduler from evaluation.** Neither varied.
- **Its populations are not comparable.** K = 1 removes the drift class by early capture. [CORPUS] Probe v disrupt guard and sniper, probe and spread sniper v repair guard are all `NOT_SCOREABLE` in T-E3K1, each decided early with 6 swings or fewer and won by Seat A in 32 of 32, while they are leaning cells in T-E3. The companion's "sharper" median (FMS 0.019) is therefore partly **selection by survival**, not evidence that the hold dampens order.

---

## F. Candidate Scheduler Treatments

Per-tick properties for 2 entrants, Q = 8, chunk 2 and rotation. G.4 is the λ = 1 minimum of executed actions (first mover, second mover). "Response" is (r₁…r₄). FCO is the final-chunk owner.

| Order (chunks) | Response | FCO | Runs of 4 actions per tick | Alternations per tick | G.4 | Is the stream a phase shift of stock? | Verdict |
|---|---|---|---|---|---|---|---|
| Stock `FLFLFLFL` | L L L L | L | 1 (straddles the sample) | 7 | (5, 4) | — | control |
| **Mirrored `FLFL LFLF`** | **L L F F** | **F** | **1 (mid-tick)** | **7** | **(5, 5)** | **yes (4 chunks)** | **recommended** |
| `FLFLFLLF` | L L L F | F | 1 | 7 | (5, 5) | yes (2) | unbalanced 3/1; weaker contrast |
| `FLLFLFLF` | L F F F | F | 1 | 7 | (5, 5) | yes (6) | unbalanced 1/3 |
| ABBA per pass pair `FLLFFLLF` | L F L F | F | 3 | 5 | **(6, 6)** | no | rejected: changes alternation frequency, run length and jam capacity together |
| `FLLFLFFL` | L F F L | L | 3 (incl. straddle) | 5 | (6, 5) | no | rejected for the same reasons, although it keeps FCO = L |
| Chunk 1 with mirrored halves | balanced | F | — | — | — | no | rejected: chunk size is a second variable |
| No rotation | L L L L, fixed seat | B | — | — | (5, 4) | no | rejected: concentrates the privilege on a seat |

**Why the mirrored order.**

- It is the only balanced order that preserves the action stream exactly: same Q, chunk, rotation, run structure and alternation count.
- It equalizes response concentration (4:0 → 2:2) and moves the final chunk to the first mover.
- The three mechanisms therefore predict distinct signatures. Final position predicts a **flip**. Concentration predicts **neutralization**. The opening pass predicts no change (**stays**).
- Opening-only matchups are an **internal negative control**: pass 1 is unchanged.

**Risks.**

- **G.4 becomes (5, 5).** A jammer can deny one fewer action per two ticks: L's mid-tick 4-action run takes one suppression instead of two. This matters only for agents that re-hit the same location within a tick, and of the fixtures only `e3_jam_sniper` does, so only F4 can exercise the difference.
  - Every F1/F2 fixture writes each enemy location at most once per tick, in its opening actions (per-tick `done` sets). A stacked victim therefore loses at most one offer per tick under either order.
  - A spread victim loses an offer only while all its locations are suppressed at once.
  - MC-2 (action-denial fraction by role and pairing) is reported for both orders, so this is measured, not assumed.
- **The final-word seat at the tick limit flips** from A to B at tick 1000.
- **The first mover holds both the first and the final chunk.** A new first-mover advantage would show up as the H2 signature.
- **Process round-robin, quota redistribution, sensing and slot numbering are untouched.** Each entrant still receives slots 0–7 in order, one chunk per pass. Only its interleaving with the opponent in passes 3–4 changes.

**Rotation stays necessary.** Without it, one seat would own the final chunk in every tick.

---

## G. Candidate Evaluation-Timing Treatments

**The invariance that governs the whole family.** [SOURCE] Observation fields exclude capture streak and score, and `visible_enemy_anchor_addresses` depends only on `alive`. Any change confined to capture evaluation therefore reproduces the control byte for byte until the first completion that differs. PM-1, the end-of-tick balance swing, cannot change before that point.

| Candidate | What actually changes | K = 2 meaning | Early/asymmetric termination | Kill attribution | Scoring, replay | Isolates timing? |
|---|---|---|---|---|---|---|
| **B1**: evaluate after each chunk, complete mid-tick | capture predicate and alive timing | K counts chunks, so capture can occur **within one tick** (V4-like) | yes: a mid-tick death drops the remaining offers | needs a snapshot per checkpoint | alive score changes; the tick-of-death meaning blurs | **No.** [PROBE] Guards are at zero at a chunk boundary on 250–998 of 1000 ticks → immediate captures (H5) |
| **B2**: after each action | as B1, worse | — | yes | — | — | No |
| **B3**: mid-tick (after pass 2) plus tick end | two samples | changed | mid-tick if completing | — | — | **No**: every pass ends with L, so L is last before both samples and nothing is symmetrized |
| **B4 / C**: observe at "after F's final chunk" and at tick end; complete only at tick end | the zero predicate becomes f(two samples) | K counted in ticks, preserved | none | onset tick unchanged | none | **No**: f = AND makes capture strictly harder (more immunity, H6); f = OR makes it strictly easier (H5). No neutral f exists for binary samples. |

**Conclusion.** Every evaluation-timing treatment is a **capture-strictness rule**, not an isolation of timing. It cannot act on the E3 residual (PM-1) except through captures. Such a rule belongs after E4, as a separately registered capture-mechanic study, and only if E4 supports H2.

---

## H. Sequential vs Factorial Decision

**Sequential, Option 1.** A 2×2 of scheduler × evaluation is not justified:

- the single-sample evaluation family *is* the scheduler phase family (§E.1);
- the multi-sample family is a new capture rule with a built-in bias (§G);
- the "interaction" cell would therefore mix a relabelling with a mechanic change.

The one interaction that is known a priori is **order × hold**: G.5′ guarantees that K = 2 masks capture outcomes for continuous repairers under both orders. It is handled as in E3, with two single-field arms, each compared with its own parent. It is not handled as a factorial.

---

## I. Recommended E4 Experiment

**E4 — Mirrored Pass Order.** One causal variable: **the pass-level response order within the tick**. The stock order is uniform (L second in every pass). The treatment is mirrored (L second in passes 1–2, F second in passes 3–4). The evaluation instant, capture rule, K, λ, Q, chunk size, rotation, stream run structure, scoring and schema are all unchanged.

| Arm | Parent (control) | Only difference |
|---|---|---|
| **T-E4 (primary)** | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` (T-E3) | `scheduler_pass_order: "forward" → "mirrored"` |
| T-E4K1 (companion, recommended) | `bytefray-rules-6-research-disruption-slot1` (T-E3K1) | same |

If the companion is declined, pre-register that outcome-level readings under K = 2 cannot distinguish "order does not matter for outcomes" from "G.5′ masks it".

---

## J. Formal Treatment Semantics

```
run_chunked_quota(states, Q, execute_slot, *, chunk_size, rotate_start, tick, mirror_second_half=False)
  order = rotate(states, (tick-1) mod n)            # unchanged
  P     = ceil(Q / chunk)                            # unchanged
  for p in 0..P-1:
      pass_order = reversed(order) if (mirror_second_half and 2p >= P) else order
      for st in pass_order:                          # alive checks unchanged
          for slot in p*chunk .. min((p+1)*chunk, Q)-1: execute_slot(st, slot)
```

The following properties hold for n = 2, Q = 8, chunk 2, rotation on, λ = 1.

- **P1 Opportunity.** Each live entrant gets exactly 8 offers per tick, with its own slots in order 0–7. *Proof:* one chunk per entrant per pass, as today.
- **P2 Rotation.** The first mover is seat (t−1) mod 2. *Proof:* the rotated order is unchanged, and passes 0 and 1 are forward.
- **P3 Final chunk.** The first mover owns chunk 8 (stock: the second mover).
- **P4 Response balance.** r = (L, L, F, F).
- **P5 Stream equivalence.** The global stream equals the stock stream shifted by 4 chunks. Run structure (one 4-action run per tick) and alternations (7 per tick) are identical.
- **P6 (G.4′).** Every entrant alive throughout a tick executes **≥ 5 actions in both roles**, and the bound is tight. *Proof:* suppression is set only by enemy writes, and one hit suppresses one offer. The first mover has chunk 1 before any enemy action (2 actions) plus chunks 3, 6 and 8, each at least 1: 2 + 1 + 1 + 1 = 5. The second mover has chunk 2 (at least 1), its contiguous 4-offer run in chunks 4–5 (at least 3), and chunk 7 (at least 1): 5. ∎ Stock gives (5, 4).
- **P7 (G.5′, K = 2).** Consider an entrant whose final executed action, on each of its **first-mover** ticks, writes its own core. It owns at least one core cell at every such evaluation. So its zero evaluations fall only on its second-mover ticks, which are never consecutive, and it is never captured. ∎ This holds for `e2_repair_guard`, and for `e2_disrupt_guard` against at most 3 enemy locations with at least 5 actions. **This becomes a D9′ stop check.**
- **P8 Default identity.** `"forward"` sets `mirror_second_half=False`, so every existing Ruleset is byte-identical.

---

## K. Policy / Architecture Design

| Aspect | Decision |
|---|---|
| Field | `RulesetPolicy.scheduler_pass_order: str = "forward"`, with `SCHEDULER_PASS_ORDER_MODES = {"forward", "mirrored"}`. It follows the codebase's string-mode style (`core_placement`, `process_selection`). |
| Validation | Unknown value → `ValueError`. `"mirrored"` requires `scheduler_mode == "chunked"`, because with a single pass mirroring would be vacuous and the policy would misstate itself. Balance is exact only for an even pass count; the E4 configuration has 4 passes. |
| Scheduler | Keyword-only `mirror_second_half: bool = False` on `run_chunked_quota`. `run_scheduler` passes `self.scheduler_pass_order == "mirrored"`. `run_sequential_quota` and `run_interleaved_quota` are untouched. |
| Runtime state | None. There is no capture or disruption change, no new process state and no Ruleset-ID branching. |
| IDs | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes` (primary) and `bytefray-rules-6-research-disruption-slot1-mirrored-passes` (companion). Each ID names every gameplay difference from V4. |
| Objects | Independent literal copies, never `replace()`. A test verifies the one-field difference from each parent. |
| Lifecycle | `ACTIVE_RESEARCH_RULESET_IDS`. Absent from stable, omitted candidates, the Designer, `run`, `agents test` and tournament. |
| Identity | `ruleset_id` already separates `canonical_match_id`. **No `MatchRequest` override.** `_effective_ruleset_policy`'s `replace()` carries the field through unchanged. Do not add it to the override payload: that would alter historical override `match_id`s. |
| Artifacts | No replay or result schema change. Pass order is recovered through the registry from `ruleset_id`, the way K and λ are. Field values are immutable once artifacts exist. |
| Plumbing | As in E3: core-placement guard, evaluation allow-list, arena-range check, `agents evaluate` choices, distinct alignment labels, keyword-only resolver flags. **Trap F-4:** an omitted arena must resolve to 512. |
| Not in E4 | The deferred table-driven evaluation-methodology refactor, `disruption_duration`, `_select_active_process`, the capture code, `client/` and `app/`. |

---

## L. Canonical Mechanical Traces ([PROBE], seed 42, T-E3 parent vs mirrored)

Notation: `chunk: writes [A-own/B-own]` after the chunk; `–` is an offer lost to suppression. A's core is 485 and B's is 203.

**1. Sniper (A) v disrupt guard (B).** This tests response order; evaluation is unchanged.

```
stock    t1 F=A: A203 204[8/6] | B– 485[7/6] | A– 205[7/5] | B203 204[7/7] | A206 207[7/5] | B205 206[7/7] | A208 209[7/5] | B207 208[7/7]  → B ends 7
         t2 F=B: B485 203[7/7] | A– 203[7/6] | B– 204[7/6] | A204 205[7/4] | B205 206[7/5] | A206 207[7/3] | B207 208[7/4] | A208 209[7/3]  → B ends 3
mirrored t1 F=A: A203 204[8/6] | B– 485[7/6] | A– 205[7/5] | B203 204[7/7] | B205 206[7/8] | A206 207[7/6] | B207 208[7/7] | A208 209[7/5]  → B ends 5
         t2 F=B: B485 203[7/5] | A– 203[7/4] | B– 204[7/4] | A204 205[7/2] | A206 207[7/1] | B205 206[7/3] | A208 209[7/3] | B207 208[7/5]  → B ends 5
```

- Each pass fights one cell pair.
- Under the stock order, L wins all four passes, so the guard's end state is 7, 3, 7, 3 (999 swings, FMS 0.0).
- Under the mirrored order the passes split 2/2, so the end state is a constant 5. There is **1 swing in 1000 ticks**, FMS/PD are not scoreable, and the static parity gap is 0.
- There is no zero at any evaluation, so no streak update. Both orders end in a tie at 1000.

**2. Repair guard (A) v sniper (B).** Drifting sweep; tests response order.

- The guard's cursor persists across ticks.
- End-of-tick guard core: stock 2, 6, 5, 4; mirrored 4, 6, 5, 4.
- Over 1000 ticks the stock order gives 1000 swings with FMS 0.25; mirrored gives 875 swings with FMS 0.57, i.e. neutral. The reversed seating goes from FMS 0.144 to 0.402.
- Zero at tick end, with the guard as Seat B: stock 125 ticks (the E3 review §I and its reconciliation place all of them on the guard's own first-mover ticks: G.5 alternation, onset then recovery); mirrored 0.
- **K = 1 companion:** a capture at tick 8 becomes a tie at 1000. Outcome-level order dependence is visible only without the hold.

**3. Guarded-painter mirror.** Opening pass; the internal negative control.

```
t1 F=A: A203 485[8/7] | B485 –[7/7] | …   (both orders: pass 1 = A hits B-base, repairs own; B hits A-base after)
```

- The same pass-1 exchange happens every tick in both orders, so L keeps its base and takes F's base.
- FMS 0.0 under both orders. What changes is the final-chunk owner: FPS goes from 1.0 to 0.0.
- B wins by capture at tick 93 under both.
- **The privilege stayed with the second mover even though that entrant no longer acts last.**

**4. Probe mirror.** A symmetric race that order does not affect. Both cores are at 1/8 after tick 1 and 0/8 after tick 2, giving an onset for both. Both complete at tick 3 (`all_agents_dead`) under both orders.

**5. Jam sniper (A) v min guard (B).** Order does not affect it:

- the jammer re-hits B's base, its anchor, in every one of its chunks, so B's single repair of its base is overwritten each tick;
- B's final action as second mover is an attack, so the G.5 premise fails;
- an onset at tick 3 completes at tick 4 under both orders.

**6. Spread sniper (A) v disrupt guard (B).** This tests the sample, not the order:

- the guard is at **zero at a chunk boundary in 998 of 1000 ticks**, yet at the end of every tick it holds at least 4 cells;
- the end state is a static 6, 4, 4, 4 under both orders;
- a per-chunk or "zero at any checkpoint" rule would capture it at once (H5).

**7. Sniper v min guard, and the disrupt-guard mirror.** Opening pass. The only contested cells are bases. End states are identical under both orders (2/2, 2/1, … and 7/8, 8/7, …), with FMS 0.0 under both.

---

## M. Prospective Metrics (E4 onward; historical E2/E3 calculations are not altered)

### M.1 Seat metrics

These are for an F1 pairing {X, Y}, seed s, and orientations XY (X in Seat A) and YX. The seat winner is w ∈ {A, B, T} and the entrant winner is e ∈ {X, Y, T}.

| Metric | Definition |
|---|---|
| **DSC(s)** | 1 if w_XY(s) = w_YX(s) ∈ {A, B}. **SDI** = mean over seeds (the legacy E2/E3 metric, retained). |
| **EC(s)** | 1 if e_XY(s) = e_YX(s) ∈ {X, Y} (entrant consistency) |
| **OS** | Orientation sensitivity = mean over seeds of 1[e_XY(s) ≠ e_YX(s)] |
| **GSB** | Global seat bias = (#A wins − #B wins) / (2S) |
| **SCP** | p_A = the share of seat-consistent seeds won by A. **SB** = \|2p_A − 1\| |
| **SDom** | Seat dominance = SDI · SB. High only when one seat wins across seeds; this is E2's notion of "seat-determined". |
| **SCD** | Seed-conditioned determinism = SDI · (1 − SB). Each seed is seat-consistent, but the winning seat varies by seed. |

**Twin mirrors.** The orientation swap is a relabelling, so DSC ≡ 1 on decisive seeds. The mirror **unit is the seed**:

- GSB = (#A − #B) / S;
- p_A over decisive seeds;
- SDom = decisive share · SB;
- SCD = decisive share · (1 − SB).

Relabel identity is a gate, not a metric.

**F1 caveat.** Orientation swaps change seat parity, core position and the seat-derived RNG stream together, so no parity attribution is made from F1 seat metrics alone.

Example (T-E3, guarded-painter mirror): 32/32 decisive, p_A = 19/32, SB = 0.1875, **SDom 0.19 and SCD 0.81**. This is seed-conditioned, not seat-determined.

### M.2 Parity metrics

- **FMA (first-mover core advantage).** Let b(t) = (A's own-core cells) − (B's own-core cells) at the end of tick t. Over ticks at which both entrants are alive, FMA = ½ (mean over A-first ticks of b − mean over B-first ticks of b). It is measured in cells, in [−8, 8].
  - Agent asymmetry cancels, so FMA is defined **with zero swings**.
  - It requires at least 10 both-alive ticks of each parity; otherwise the cell is `DECIDED_EARLY`.
- **Five bands, fixed a priori.** Round \|FMA\| to the nearest cell: 0 → neutral, 1 → moderate, ≥ 2 → strong, each signed first or last. That is:
  - strong-first: FMA ≥ 1.5;
  - moderate-first: 0.5 ≤ FMA < 1.5;
  - neutral: \|FMA\| < 0.5;
  - moderate-last: −1.5 < FMA ≤ −0.5;
  - strong-last: FMA ≤ −1.5.

  Rationale: the integer resolution of core ownership. No band came from corpus or probe values.
- **PM-1 (FMS, PD, bands) is retained for continuity**, with `NOT_SCOREABLE` counted and never dropped.
- **FPS (final-chunk-owner share).** The share of swings that favour the tick's final-chunk owner, read from the registry. Under the stock order FPS = 1 − FMS; under the mirrored order FPS = FMS.
- **Transition classes** (matchup-level, control → treatment, on FMA bands):

| Class | Definition |
|---|---|
| NEUTRALIZED | control non-neutral → treatment neutral |
| FOLLOWS-FINAL | control last-side → treatment first-side (the new final-chunk owner) |
| STAYS | control last-side → treatment last-side, same band |
| WEAKENED / STRENGTHENED | same side, band down / up |
| NEW | control neutral → treatment non-neutral |
| UNCHANGED-NEUTRAL | neutral → neutral |
| FIRST-SIDE-CONTROL | control first-side (no discriminating prediction; reported) |
| DECIDED-EARLY | fewer than 10 both-alive ticks per parity in either arm |

### M.3 Weighting

- **Primary unit: the ordered matchup** (field, Seat-A agent, Seat-B agent), summarized by its median over seeds. Twin mirrors count as one unit.
- The census counts matchups. This prevents 32 identical deterministic cells from dominating, which was E3's mixture problem.
- Cell-weighted and distinct-transition-weighted values are secondary and always reported.
- Every matchup carries its n_distinct of (C key, T key) transitions.

---

## N. Pre-Registered Hypotheses

**Populations**, frozen from control data before any treatment exists:

- **P-PAR (primary):** standard-field (F1, F2) matchups with \|median FMA_C\| ≥ 0.5.
- **P-STALE (continuity):** E3's frozen stalemate cells within the E4 field.
- **Contest class** of each matchup, assigned **a priori from §D.1 source roles**: MULTI-PASS, OPENING-ONLY or INCIDENTAL.
- F4 is a separate stratum (G.4′).

| ID | Statement | Supported if | Refuted if | [PROBE] prior |
|---|---|---|---|---|
| **E4-H0** | No structural effect | STAYS + UNCHANGED-NEUTRAL ≥ 0.90 of P-PAR, **and** H1 refuted | < 0.90 | Fails |
| **E4-H1** | Response-order concentration is load-bearing | In MULTI-PASS P-PAR matchups, NEUTRALIZED + WEAKENED ≥ 2/3, **and** overall FOLLOWS-FINAL ≤ 1/10 | NEUTRALIZED + WEAKENED ≤ 1/10 of MULTI-PASS | Supported |
| **E4-H2** | Final pre-sample position (≡ evaluation adjacency) is load-bearing: the privilege transfers | FOLLOWS-FINAL ≥ 2/3 of MULTI-PASS P-PAR | ≤ 1/10 | Fails (0 flips in any named scenario) |
| **E4-H3** | Opening-pass response privilege | In OPENING-ONLY P-PAR matchups, STAYS ≥ 2/3 | STAYS ≤ 1/10 | Supported |
| **E4-H4** | Hold × order masking | Companion outcome-class change share in MULTI-PASS exposed F1 cells ≥ 0.10 while the primary's is ≤ 0.02 | Companion ≤ 0.02 | Supported (under K = 1, 3 named cases change outcome; under K = 2, none) |
| **E4-H5** | New early-capture pathology | Primary: ≥ 0.10 of control non-capture exposed F1 cells become captures | < 0.10 | Fails |
| **E4-H6** | Stasis / draw-ification | Exposed-F1 tick-limit share rises ≥ 0.10 (flag). Also reported: the share of NEUTRALIZED matchups with < 10 treatment swings ("static neutralization") | Rise < 0.10 | Static neutralization is present; the flag is unknown |
| **E4-H7** | Seed-conditioned seat dependence remains | \|GSB\| ≤ 0.10 in every unit, and ≥ 1 unit with SCD ≥ 0.5 at n_distinct ≥ 8 | No unit with SCD ≥ 0.5 | Likely (guarded-painter mirror) |
| **E4-H8** | Tick-limit parity artifact | Any mirror claim differs between 1000 and 1001 (`TICK_LIMIT_PARITY_DEPENDENT`) | All agree | Unknown |
| **D9′** | G.5′ immunity (theorem) | T-E4: 0 completions against repair and disrupt guards (and twins). **Also a hard stop.** | — | Theorem |

**Pre-registered interpretation.** "A clean negative is reachable" (H0).

| Result | Conclusion |
|---|---|
| H1 ∧ H3 ∧ ¬H2 | The residual has **two order mechanisms**. In multi-pass contests it is response-order concentration, which order can remove. In anchor-base contests it is the second mover's opening response, which order cannot touch. Neither the final action nor the evaluation instant is the cause. Next: co-location of anchor and core cell 0 (a spatial study, registered separately). |
| H1 ∧ ¬H3 ∧ ¬H2 | Response-order concentration causes the residual broadly |
| H2 | The privilege follows the final pre-sample chunk. Next: evaluation structure (a multi-sample capture rule, registered separately) |
| ¬H1 ∧ H3 | The residual is the opening-pass effect. The in-tick order line closes. Next: co-location |
| H0 | Order is not load-bearing. The line closes |
| H5, H6, H8 | Recorded as pathologies whatever else holds |
| none | "No registered row applies" is itself the registered outcome. The census is reported. |

**Threshold rationale.**

- 2/3 is a supermajority, 1/10 is E3's practical floor, and 0.02 means "essentially none".
- The FMA bands come from the cell resolution (M.2).
- None was derived from probe or corpus outcomes. The probe values in the prior column are predictions to be falsified.

---

## O. Experimental Matrix

| Condition | Ruleset | K | λ | Pass order | Role |
|---|---|---|---|---|---|
| C-E4 | `…-capture-hold-k2-disruption-slot1` | 2 | 1 | forward | control; must reproduce historical T-E3 |
| T-E4 | `…-capture-hold-k2-disruption-slot1-mirrored-passes` | 2 | 1 | mirrored | primary |
| C-E4K1 | `…-disruption-slot1` | 1 | 1 | forward | companion control; must reproduce historical T-E3K1 |
| T-E4K1 | `…-disruption-slot1-mirrored-passes` | 1 | 1 | mirrored | companion |

| Field | Composition | Ticks | Per condition |
|---|---|---|---|
| F1 | 9 agents (E2 set **minus `e2_counter`**, §S-9), triangular: 36 pairs × 32 seeds × 2 orientations | 1000 | 2,304 |
| F2 | 9 twin mirrors × 32 × 2. The duplicate orientation is kept only as the relabel gate; the analysis unit is the seed. | 1000 | 576 |
| F2-P | 9 twin mirrors × 32 × 1 orientation | 1001 | 288 |
| F4 | `e3_jam_sniper` × 9 agents, plus the jam mirror, × 32 × 2 | 1000 | 640 |

**Counts.** 3,808 per condition; the **primary study is 7,616** and **15,232 with the companion**.

**Size.** Cost at E3's measured rate (about 0.5 s and 0.7 MB per match per worker) is about 2 h single-worker, or about 1 h with two conditions in parallel, and about 11 GB.

**Fixed settings.** Arena 512; seeds 1–32 given explicitly; all four request overrides asserted `None`; no K = 3.

**Scope decisions.**

- **Full F1 is kept**, because every contest class lives there.
- **Mirrors are kept** for seat metrics, the relabel gate and the tick-limit flip.
- **F4 is kept** as the G.4′ manipulation signature and the re-disruption stratum. It is never pooled.
- **F2-P is kept**, because the treatment flips the final-word seat at the tick limit. One orientation suffices.
- **32 seeds are kept**, for exact pairing and rate eligibility of RNG-bearing matchups. Deterministic matchups give n_distinct = 1 regardless.

---

## P. Evidence Rules

1. The unit is the ordered matchup, with the distinct paired transition counted within it. A matchup with n_distinct = 1 is a deterministic characterization. Rate claims need n_distinct ≥ 8.
2. Population criteria are **census counts of matchup characterizations**, not medians of mixtures. E3-style cell-weighted medians are reported for continuity on P-STALE and carry no interpretive weight.
3. Parity is two-sided with direction. `NOT_SCOREABLE` and `DECIDED_EARLY` are counted categories. **Static neutralization is scored through FMA, never dropped.**
4. Every criterion is computed control-vs-control, where it must be 100% STAYS or UNCHANGED-NEUTRAL, and frozen before treatment.
5. Mirrors are analysed at the seed level. Claims must agree at 1000 and 1001 ticks.
6. F4 is never pooled with F1 or F2.
7. The companion never replaces a primary verdict; it feeds H4 only.
8. The Bradley–Terry reading and residuals are dropped as criteria. E3 showed they are saturated by dominance on this field; they may be reported descriptively.

---

## Q. Historical-Control Reuse

**Valid.** E4's parents are the E3 treatment Rulesets, and their semantics are unchanged: `"forward"` is byte-identical by P8. The conditions are:

- **Reproduction gate.** Re-run C-E4 and C-E4K1 at the E4 implementation tree over the E4 field subset. Require byte identity with the preserved T-E3 and T-E3K1 cells in replay SHA-256, `result_id`, `match_id`, `result.json` (minus `completed_at` and `occurrence_id`) and E3 telemetry. A full re-run is required because E4 changes match-generation code (the scheduler).
- **Provenance.** The E4 matrix names the historical parents: matrix `v6-e3-matrix-v1-634132ec3c15`, freeze `v6-e3-freeze-v1-506811e78ad8`, generated at `6f0fd3f`, engine tree `67b73c9a…`.
- **Identities.** New matrix identity `v6-e4-matrix-v1-<digest>` and analysis freeze `v6-e4-freeze-v1-<digest>`, kept separate. The E3 identities are never renamed. The E4 analyzer recomputes everything on the re-run control, and its PM-1 must equal the frozen E3 telemetry cell for cell.

---

## R. Qualification / Freeze Plan

1. **Governance.** Preserve this review verbatim in its own commit, and record its SHA-256.
2. **Freeze first.** Before any scheduler change, commit byte-identity digests for **both E4 parents** (the T-E3 and T-E3K1 Rulesets). Cover sniper v disrupt guard, repair guard v sniper, spread sniper v disrupt guard, sniper v min guard, the probe mirror, the guarded-painter mirror, the disrupt-guard mirror and jam v min guard, at seeds 1–3, both orientations: 96 matches. Existing V4, E2 and E3-parent freezes stay unedited.
3. **Implement** the policy, scheduler and Rulesets (§U).
4. **Tooling:**
   - the matrix and the pre-registration (verbatim from §N–§P, digest-pinned);
   - E4 analyzer v1 (FMA, FPS from the registry, the census, seat metrics, the G.4′ check, the relabel gate), importing capture analyzer v2 and E3 action/parity analyzer v1 **unchanged**, with pinned hashes;
   - the a-priori contest-class table;
   - gates.
5. **Qualify the tooling on control data only:** historical T-E3 and T-E3K1 plus the re-run controls. Required: 0 failures, PM-1 equal to the E3 telemetry, and a control-vs-control census that is 100% unchanged.
6. **Freeze** the matrix and analysis identities.
7. **Run the controls**, then the full parent reproduction gate. Freeze P-PAR, P-STALE, the contest classes and the control baseline.
8. **D9′ real-fixture gate** under T-E4: the real guards against scripted adversaries, at non-matrix seeds.
9. **Authorize the treatment separately**, run it, run the treatment gates, then the frozen analysis.

**Hard stops** (halt; never patch and continue):

1. A frozen golden fails (V4, K = 1, E2, E3-parent or E4-parent).
2. A parent reproduction mismatch.
3. Fixture fingerprint drift.
4. The one-field difference fails, or an override is not `None`.
5. A scheduler manipulation check fails: the scripted exact sequence `FFLLFFLLLLFFLLFF` is not reproduced, or F4's second-mover minimum ≠ 5 under treatment, or any G.4′ violation.
6. Σ `cpu_used` ≠ `cpu_total`, or an exclusive or zero-action live tick.
7. A capture-analyzer disagreement.
8. A D9′ violation.
9. The twin-mirror relabel identity fails.
10. The source manifest changes, or the tree is dirty, during execution.
11. The control-vs-control census is not 100% unchanged.
12. An analyzer defect after treatment exposure: stop interpretation and do not re-freeze under the same identity.

There is **no prefix gate**, because order differs from tick 1. Stops 5 and 9 replace it.

---

## S. Adversarial Findings

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| S-1 | A ≡ B within the equal-quota order family (stream phase) | SOURCE, PROBE | The E4 question is reframed as response order; no attempt to separate A from B |
| S-2 | Capture-evaluation treatments leave PM-1 invariant until the first divergence | SOURCE | The B family is rejected as a timing test |
| S-3 | Every B-family member is a capture-strictness rule; zeros at chunk boundaries are common (250–998 per 1000 ticks) | PROBE | H5/H6 risk; deferred |
| S-4 | "Last mover" ≠ "latest write": in opening-pass contests the privileged entrant is the second mover even when it does not act last | PROBE (guarded-painter mirror FPS 1.0 → 0.0) | FPS and transition classes |
| S-5 | 73% of E3's last-leaning stalemate cells are opening-pass anchor contests that no rotation-preserving order can change | CORPUS, SOURCE | Internal negative control; successor: co-location |
| S-6 | PM-1's 10-swing rule hides static neutralization | PROBE (1 swing) | FMA is primary |
| S-7 | Twin-mirror orientation swap is a relabelling, so mirror SDI is 1.0 by construction whenever a seed is decisive. E2/E3 mirror SDI measured decisiveness, not per-seed seat consistency. Mirror seat bias and the favoured seat remain valid. | CORPUS 320/320 × 3 conditions | Seed-level mirror metrics; dated addendum to the E3 results; no historical edit |
| S-8 | E3 results say 20/12 seeds where the frozen data give 19/13 | CORPUS (two sources) | Dated erratum; no verdict affected |
| S-9 | `e2_counter` ≡ `e2_greedy_painter` under λ = 1; E3's pairing and match-weighted counts double-weight the painter | SOURCE, CORPUS 512/512 | Excluded from E4 on a source proof, not on outcomes |
| S-10 | G.4 changes to (5, 5): one fewer denial per two ticks under jamming | SOURCE proof | Confined to F4 (the only multi-hit agent); a manipulation signature |
| S-11 | The final-word seat at the tick limit flips (1000: A → B) | SOURCE | F2-P; H8 |
| S-12 | K = 2 masks outcome effects (G.5′) | SOURCE, PROBE | Companion; H4 |
| S-13 | Under the mirrored order the first mover holds both the first and the final chunk, so a new first-mover edge is possible | SOURCE | This is the H2 signature, tested |
| S-14 | Neutralization may be stasis (a fixed point) with an unchanged tie, not interaction | PROBE | H6 flag; "does not make gameplay better" stated |
| S-15 | Territory scoring is also an end-of-tick sample; ⌊cells/64⌋ makes single-cell swings rarely matter | SOURCE | Tick-limit score outcomes reported separately |
| S-16 | Mirror "seat" is parity + position + RNG jointly; F1 swaps change all three | SOURCE, CORPUS | No parity attribution from seat metrics alone |
| S-17 | P-PAR is selected on control FMA, so regression to the mean is possible for RNG-bearing matchups | — | Matchup medians; P-STALE is selected on C-E2 independently |
| S-18 | `ProcessMatchController.__init__(**kwargs)` still swallows unknown kwargs (E3 O-9) | SOURCE | Semantics only through the policy |
| S-19 | Write order within a tick is recoverable from `memory_diffs` (the E3 review overstated the limit) | SOURCE | Observation; enables future contest-locus analysis |
| S-20 | Free global information, and fixtures written for earlier semantics, limit external validity | DOC | Conclusions stated conditionally |
| S-21 | The ROADMAP/FUTURE_PLANS E4 entry must be phrased as a question | DOC (E2 F-12) | At registration |

---

## T. Recommendation

**The scheduler-order experiment comes next: mirrored pass order (Option 1).**

It is the only candidate that:

- changes one causal variable with capture semantics intact;
- preserves the action stream exactly (P5);
- has theorem-backed gates (G.4′, G.5′/D9′);
- lets final position, concentration and the opening-pass effect produce three distinguishable signatures, with an internal negative control.

The expected result, to be falsified: **H1 ∧ H3 ∧ ¬H2**. Multi-pass order dependence is neutralized, often into stasis. The opening-pass majority is untouched. Nothing follows the final chunk. That result would locate the dominant residual not in order or evaluation timing but in **anchor/core-0 co-location**, which is the natural next single-variable question.

---

## U. Implementation Handoff (for the implementing agent; implementation only, do not run the matrix)

1. **Freeze first:** the §R step-2 digests for both E4 parents, committed only when instructed.
2. **Policy** (`ruleset_policy.py`):
   - add `scheduler_pass_order: str = "forward"` and `SCHEDULER_PASS_ORDER_MODES`, validated in `__post_init__` (unknown value → `ValueError`; `"mirrored"` requires `"chunked"`);
   - `run_scheduler` passes `mirror_second_half=(self.scheduler_pass_order == "mirrored")`;
   - add the two literal policy objects;
   - register them in `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS` and `__all__`;
   - add the ID constants in `rules.py`.
3. **Scheduler** (`scheduler.py`): a keyword-only `mirror_second_half: bool = False` in `run_chunked_quota`. The pass order is reversed for passes with `2p ≥ P`. Update the docstring. Nothing else changes.
4. **Do not touch:** `process_runtime.py` gameplay, `python_runtime.py` capture, `disruption_duration`, `_select_active_process`, the replay and result schemas, `MatchRequest`, `client/`, `app/`. No ID branching.
5. **Plumbing** (E3 precedent): core-placement guard, evaluation allow-list, arena range, CLI choices, alignment labels and keyword-only flags. **Trap F-4:** an omitted arena resolves to 512.
6. **Tests** (every sequence asserted by value):
   - policy validation and defaults;
   - the one-field difference from each parent;
   - scheduler exact offer sequences for rotation on and off, ticks 1–4, dead and forfeiting entrants, n = 1 and n = 3, chunk 1 and chunk ≥ Q;
   - P5 stream equivalence;
   - byte identity: every existing freeze unedited, plus the new E4-parent freeze;
   - G.4′ by exhaustive jam enumeration (5/5, tight; stock still 5/4);
   - G.5′ with scripted guards against jammers under K = 2;
   - seed-42 mechanic characterizations: sniper v disrupt guard static after tick 1; guarded-painter mirror pass 1 unchanged; jam v min guard capture at tick 4;
   - registration, lifecycle, product isolation, evaluation plumbing and determinism.
7. **Validation:** the focused modules, then `python -m pytest`, `mypy engine/src/battle_engine`, `mypy client/src/battle_client` and `ruff check .`, with exact counts.
8. **Registration note** under `docs/research/v6/` pointing to this review. Word the ROADMAP and FUTURE_PLANS entries as a question.

The research tooling (§R steps 4–9) is a separate, later task.

---

## Appendix P. The probe

- **Code.** `scratchpad/probe.py` swaps the module-level `run_chunked_quota` that `RulesetPolicy.run_scheduler` calls for a phase-aware copy, which models §J exactly: each entrant keeps slots 0–7 with one chunk per pass. It logs every `VM._wr8` together with its offer (tick, seat, slot, chunk).
- **Validity.** Phase 0 through the patch reproduced the unpatched replay SHA-256 and `result_id` exactly for sniper v disrupt guard and the guarded-painter mirror, under both E3 Rulesets.
- **Exposure.** About 105 named-scenario matches at seed 42 only (86 full-length, 18 short traces); no grid was run. Intra-tick checkpoint counts (§G, §L-6) come from the control-order trajectories, which are exact until the first divergence.
- **Scope.** The probe did not change the repository. The tree was clean before and after.
