# Bytefray V6 E3 (proposed): Whole-Tick Disruption, Causal Design and Adversarial Review

Design review only. **No repository file was modified.** The working tree was clean before and after. All probe code ran from the session scratchpad.

**Evidence tiers.**

- **[SOURCE]** current source at `9d34b01`.
- **[RUN]** unmodified repo executed.
- **[CORPUS]** a descriptive read of the preserved E2 corpus. This corpus is the *control* for the proposed experiment, and no threshold was taken from it.
- **[PROBE]** a scratch-only patch of the real controller. Exploratory priors, not results (Appendix).
- **[DOC]** prior research records.

## Verdict

- **The working hypothesis is half right.** Whole-tick disruption is what makes *first-mover initiative* decisive. Against a stacked opponent, one early write makes the whole tick belong to one entrant: the second mover executes 0 of 8 actions. That turns the chunked scheduler into strictly alternating 8-action turns. Chunk size then has no causal effect: chunk 1 reproduces every traced E2 outcome, down to identical scores [PROBE].
- **It is probably not the cause of scheduler-*****locked*****&#xA0;play as such.** The probe limited a hit to the victim's next slot. Both sides then execute 7 of 8 actions every tick, but the canonical stalemate is still a period-2 deterministic tie. **Every change in core balance now favors the tick's&#xA0;*****last*****&#xA0;mover:** 0 of 999 swings favor the first mover [PROBE]. Capture is evaluated at the end of the tick, and rotation always gives the second mover the tick's final chunk. Parity locking survives, inverted.
- **The causal question therefore has two sides:** *does removing whole-tick denial remove parity-determined control, or only move it from the first action to the last?*
- **Recommendation: a disruption-duration experiment next (Path A).** The treatment is E2 + `disruption_slot_limit = 1`.
  - The scheduler path is refuted as the lever, by source and probe.
  - Narrowing scope is a null intervention for every agent in the 610 stalemates.
- **Strongly recommended companion arm:** the same field on research-scale (K = 1). With a one-slot limit, K = 2 and rotation together make continuous repairers *provably uncapturable* (§G.5). That is a predictable confound on exactly the stalemate outcomes.
- **The pre-registration must be two-sided on parity.** E2's one-sided H3b (≥ 0.95) would read an inverted lock as "unlocked".

---

## A. Repository Baseline

| Item                                 | Value                                                                                                                                                                     |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Branch / HEAD                        | `v6-research` @ `9d34b01ee53c11ba1f40945e211dd7a91cca07ac`, the E2 results commit. It is current HEAD.                                                                    |
| Upstream                             | `origin/v6-research` = `24fac67`. After `git fetch --all`: **49 ahead, 0 behind**, so nothing has been pushed since Phase 2.                                              |
| Tree                                 | Clean (`git status --porcelain` empty) before and after                                                                                                                   |
| Python / platform                    | 3.13.14 (MSC v.1944, 64-bit), `Windows-11-10.0.26120-SP0`, repo `.venv`                                                                                                   |
| Focused tests [RUN]                  | 123 passed. Files: V4 exploit characterization, K=1 byte identity, E2 semantics, E2 Ruleset, Ruleset policy. This is a focused subset, not the suite.                     |
| Rulesets (ruleset_policy.py:638-660) | Stable: `bytefray-rules-4`. Active research: `-6-research-scale`, `-6-research-capture-hold-k2`. Retired but still executable: `-scale-move`, `-scale-move-proportional`. |
| E2 corpus                            | `runs/research_v6_e2/v6-e2-matrix-v1-9048907fdc3b/{C-V4,C-RS,T-E2}`, preserved                                                                                            |

## B. E2 Evidence Relevant to This Question

From the frozen results (freeze v2):

- **Stalemates.** Phase-lock ≥ 0.95 for 610 of 610 stalemate entrants; agent level 0.994–0.9995.
- **Captures of disrupt-first defenders.** All 64 come from the three-location spread sniper, and every onset falls on the victim's *own* first-mover tick.
- **Pure repair guard.** 64 onsets, 0 recoveries and 64 captures against the sniper.
- **Seat determination.** 0 of 45 SDI changes. Guarded-painter mirror: A 54 / B 10 → **B 64 / 64**, with roughly 170 onsets per entrant per match.
- **The H2 residual procedure** counted 6 and 8 residuals in the V4 control, so it cannot separate treatment from control.

New [CORPUS] facts from T-E2, the would-be control:

- **Exclusive ticks.** In F1, **62.6%** of ticks with both entrants alive are exclusive, meaning one entrant executes 0 actions (1,002,240 of 1,602,067). The second mover averages **2.75 of 8** executed actions per tick. F2: 59.1% and 0.91.
- **Hits.** **All 2,880 F1 cells** contain at least one disruption hit. 64 of 640 F2 cells contain none.
- **Executed actions are derivable without a schema change.** The replay's per-tick `cpu_used` gives them. Its sum equals `result.json` `statistics.cpu_total`: 4,000 = 4,000 in sniper v disrupt guard, seed 1, whose sequence is 8/0, 0/8, … .

## C. Current Disruption Semantics (source-derived)

**Scheduler** (scheduler.py:54-95, ruleset_policy.py:268-289):

- Each live entrant is offered Q = 8 slots per tick, in chunks of 2 (4 passes).
- The start seat is rotated by `(t−1) mod 2`, so Seat A moves first on odd ticks: `AA BB AA BB AA BB AA BB`.
- Every offer is made. The scheduler knows nothing about disruption.
- **The second mover always owns the tick's final chunk, for any chunk size**, because every pass ends with it.

**Disruption** (process_runtime.py):

```
per process p: disrupted_until_tick (0 at reset)                          :111, :120
HIT (:1251-1265): an applied WRITE by X to address a at tick t
    for every live enemy entrant Y and every p in Y with anchor(p) == a:
        p.disrupted_until_tick = t + 1        # assignment; a re-hit never extends it
disrupted(p,t) := t < p.disrupted_until_tick  # D = 1 tick, hardcoded at :648, not policy
EACH OFFER to Y (:1039-1057):
    eligible = processes not disrupted                                     :809
    quotas   = largest-remainder split of Q over eligible by share         :813-826
    select   = round-robin cursor over eligible with remaining quota       :899-910
    none     -> offer forfeited; cursor untouched; cpu_used not incremented :1056-1057
SENSING: disrupted processes are not observers                             :769-773
REPLAY: snapshot "disrupted" = disrupted(p,t) at publish = "hit during t"  :932-943

```

Answers to the semantic questions:

- **Trigger.** Any applied WRITE to an enemy anchor. There is no special action.
- **Target.** A *location*: every live enemy process anchored there. Friendly processes are immune.
- **Duration.** It starts with the victim's next offer and ends at the tick boundary.
- **Selection.** A disrupted process is absent from the quota table and is passed over without consuming its round-robin turn.
- **Quota.** It is redistributed to eligible siblings (R4b "Q2").
- **When an offer is actually lost.** For positive-share processes, the eligible processes' remaining allocations always sum to at least the remaining offers. So an offer is lost **if and only if every process of the entrant is disrupted**. Lost offers are never deferred, refunded or given to the other entrant.
- **Multiple locations.** One write disrupts one location, and the survivors absorb the quota.

**Co-location.** Every process spawns on its core base (:728-738). At spawn an entrant is therefore one location, *and that location is core cell 0*. A competent attacker's first write is both a capture write and a whole-entrant disruption.

| Variable          | Value                              | Controls                                                                 |
| ----------------- | ---------------------------------- | ------------------------------------------------------------------------ |
| **Duration**      | rest of tick                       | how many of the victim's remaining offers one hit removes (all of them)  |
| **Scope**         | all enemy processes at the address | how many processes one write removes                                     |
| **Co-location**   | spawn at core base                 | whether one write reaches the whole entrant                              |
| **Chunk size**    | 2                                  | how many locations the opener can hit before the opponent's first action |
| **Rotation**      | on                                 | which seat is first and which is last in each tick                       |
| **Process count** | declared by the agent              | irrelevant while co-located; gives surviving origins when spread         |
| **Selection**     | `round_robin`                      | which eligible process acts; never changes eligibility or quota          |

**History [DOC].**

- V4_PROCESS_DISRUPTION_RESEARCH.md (R4b) compared only whole-tick durations {0, 1, 2}.
- Its §K named single-process fragility, "loses 70/80 callbacks for 10 writes", as "the mechanic's sharpest risk". It accepted that risk on the condition that information would be costly (§R) and that the victim could escape by moving.
- V4 then made reach free and anchors visible. E2 is that flagged risk realized.
- **Sub-tick durations were never evaluated.**

## D. Causal Assessment

**The mechanism** [SOURCE + PROBE]:

1. The first mover's first action precedes the opponent's first action, for any chunk size ≥ 1.
2. If it lands on a stacked opponent's anchor, the opponent forfeits every remaining offer, and the tick becomes exclusive.
3. With exclusive ticks, the scheduler degenerates into alternating 8-action turns, and interleaving becomes irrelevant. [PROBE] Chunk 1 with stock disruption reproduces every traced outcome. The guarded-painter mirror's scores are identical: 4219/4382, 4212/4466, 4302/4523.
4. End-of-tick state is then the first mover's intent. Rotation period 2 equals K = 2, which gives either phase-locked zero/recovery alternation or, when the victim does not repair, a forced capture.

**How each E2 observation arises:**

- **The disrupt guard survives a single-location sniper.** Its turn opens with one write that silences the attacker for the rest of the tick, followed by 7 uncontested repairs.
- **The pure repair guard fails.** It gets exactly one chunk of 2 repairs. The attacker's next write hits the guard's anchor (also core cell 0) and silences the remaining 6 slots.
- **The spread sniper beats the stacked disrupt guard.** The guard's opening chunk can silence at most 2 locations, and one surviving write silences the whole stacked guard.
- **The guarded-painter mirror flips.** Exclusive alternation plus K = 2 non-completion turns the match into a strictly alternating territory race, which turn order decides for Seat B. I did not derive the exact territory accounting. E2 ruled out tick-limit parity (299–1001).
- **The 610 phase-locked stalemates.** Step 4 exactly.
- **Seat determination is unchanged.** E2 acts after step 4; steps 1–3 are intact.

**Qualitative causal confidence (not desirability):**

| E2 observation                       | Rotation | Duration | Scope | Co-location / count | Chunk | Repair threshold | K=2  |
| ------------------------------------ | -------- | -------- | ----- | ------------------- | ----- | ---------------- | ---- |
| Disrupt guard survives single sniper | High     | High     | Low   | High                | None  | Low (restores 7) | High |
| Pure repair fails                    | Med      | High     | Low   | High                | Low   | None             | Med  |
| Spread sniper beats stacked guard    | Med      | High     | Med   | High                | High  | None             | Med  |
| Guarded-painter mirror → Seat B      | High     | High     | Low   | Med                 | None  | Low              | High |
| 610 stalemates phase-locked          | High     | High     | Low   | High                | None  | Med (min guard)  | High |
| Seat determination unchanged         | High     | High     | Low   | Med                 | None  | None             | None |

**Competing explanation (medium confidence; the experiment must separate it).** Remove exclusivity and both entrants act every tick. The evaluation instant still follows the second mover's final chunk, and that position alternates by parity.

- [PROBE] In sniper v disrupt guard, 0 of 999 swings favor the first mover.
- [PROBE] The repair guard's 125 zero-core ticks all fall on its own first-mover ticks.

Whole-tick disruption decides *which* position dominates (the first, through denial) and makes that dominance total. End-of-tick evaluation plus rotation may be what makes *some* position dominate.

**Modulators.**

- **Repair threshold.** It decides whether the alternation ends in capture, not whether it is phase-locked. Any threshold ≤ 7 gives the disrupt guard the same stalemate. Changing it would be a new core rule, which is out of scope.
- **Free global information.** This is R4b's unmet precondition and a plausible upstream cause. It is out of scope, and E3 cannot exclude it.

## E. Candidate Interventions

**Candidate A: shorter duration.** It can be represented cleanly only if "opportunity" means **an offer to the victim process's own entrant**:

| Reading of "next action"                                       | Verdict                                                                                                                                                   |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The next global slot in the tick sequence                      | Rejected. It depends on the scheduler: at chunk 2, a hit in the attacker's slot 1 would expire at the attacker's own slot 2, so the victim loses nothing. |
| The process's next round-robin selection                       | Rejected. It needs cursor bookkeeping inside `_select_active_process`, which breaks that method's contract that eligibility is decided upstream.          |
| **The victim entrant's next λ offers, capped at the tick end** | **Accepted.** One integer per process. Scheduler, quota, selection and cursor are untouched, and λ = None is literally the stock rule.                    |

- It varies one thing: the length of the inert window. Trigger, scope, redistribution and the tick cap are unchanged.
- Disruption stays meaningful: a hit still trades one action for one of a stacked victim's offers, still removes a spread origin for that offer, and still captures the anchor cell.
- At λ < chunk it **provably ends whole-tick denial** (§G.4). λ = 2 would still allow full denial at 4 hits per tick, so **λ = 1 is chosen a priori as the only value below chunk 2**.

**Candidate B: narrower scope.**

- **Which process would be hit?** Choosing one needs a new deterministic selection surface, and R4b already rejected it as "C2".
- **It changes nothing for single-process entrants.** That is 8 of 10 fixtures, including every agent in the 610 stalemates and the guarded-painter mirror.
- It would reward stacking extra co-located processes, so it tests process-count economics rather than tick control. **Reject.**

**Candidate C: entrant-level suppression.** It is identical to A for single-process agents. For spread agents it moves scope from process to entrant and cancels Q2 redistribution, which is two variables at once and more artificial than A. **Reject.**

**Candidate D variants.**

- **Ablation** (the `disruption_duration > 0` guard already exists at :1254). It removes the mechanism rather than its leverage, and it removes the disrupt guard's only defense. A useful bracket, but not the question.
- **Tick-based D = 2.** Increases leverage, and R4b already rejected it.
- **ABBA order or per-chunk capture evaluation.** Either would attack the last-mover mechanism directly, but they are a new scheduler design and a new core rule, both out of scope. They are the natural successor if D8 is confirmed.

**Path A vs Path B (§21):**

|                | Path A: slot-limited disruption                            | Path B: smaller chunks / interleaving                                                                  |
| -------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Causal purity  | Acts on the link that creates exclusivity; one field       | Inert while ticks are exclusive. Denial needs only one first action, and any chunk size ≥ 1 gives one. |
| Implementation | New policy field plus a small runtime change               | None; the field already exists                                                                         |
| Probe          | Changes the mechanism in every traced stalemate and mirror | Every traced outcome identical to chunk 2; second mover still executes 0                               |
| Confounds      | K×λ immunity (§G.5); last-mover inversion                  | Chunk 1 *strengthens* location count: the opener silences 1 location, so 2 spread locations suffice    |
| Value now      | High: separates first-position from last-position control  | Low: a predicted near-null on the stalemates                                                           |

**A should come first.** If D8 then confirms last-mover control, the scheduler variable that matters is in-tick *order*, not chunk size.

## F. Recommended Next Experiment

**E3: Slot-Limited Disruption.** One causal variable (disruption duration), with two arms that each differ from their own parent by exactly one field.

| Arm                             | Parent (control)                                 | Only difference                   |
| ------------------------------- | ------------------------------------------------ | --------------------------------- |
| **T-E3 (primary)**              | C-E2 `bytefray-rules-6-research-capture-hold-k2` | `disruption_slot_limit: None → 1` |
| T-E3K1 (companion, recommended) | C-RS `bytefray-rules-6-research-scale`           | `disruption_slot_limit: None → 1` |

**Choosing the parent (challenging the default):**

- **Duration can be measured under K = 1.** The claim that "K = 1 captures before the defender responds" is itself a product of whole-tick denial. Under λ = 1 the defender always acts inside the tick, and as second mover it takes the tick's last action.
- **E2 stays the primary parent anyway.** The phenomena under test exist only at K = 2, and cell-level pairing against the frozen E2 corpus is available.
- **K = 2 confounds the stalemate outcome** (§G.5). The companion arm is the minimal deconfounder.
- **If the companion is declined,** pre-register that stalemate persistence under T-E3 cannot be attributed between λ and λ×K.
- **V4 as parent is rejected.** It is two fields away from E2 and serves as historical context only.

## G. Formal Treatment Semantics

**G.1 Policy value.** λ = `disruption_slot_limit` ∈ {None} ∪ ℤ≥1. An *offer* is one `execute_slot(entrant, slot)` call the unchanged scheduler makes for a live entrant.

**G.2 State.** Per process: the existing `disrupted_until_tick`, plus a new runtime-only `disruption_slots_left: int`, set to 0 at construction and reset.

**G.3 Transition.**

```
HIT at tick t (unchanged trigger and scope):
    p.disrupted_until_tick = t + 1
    if λ is not None: p.disruption_slots_left = λ          # assignment, never +=
SUPPRESSED(p, t) := t < p.disrupted_until_tick and (λ is None or p.disruption_slots_left > 0)
OFFER to entrant Y at tick t:
    S = [p for p in Y.processes if SUPPRESSED(p, t)]       # fixed at the start of the offer
    quota / selection / cursor / forfeit exactly as today, with eligible = Y.processes minus S
    finally (every exit path): if λ is not None: for p in S: p.disruption_slots_left -= 1
SENSING: observers = processes that are not SUPPRESSED
REPLAY "disrupted": unchanged, t < disrupted_until_tick ("hit during t")

```

Answers to §11:

- **On a hit:** the two fields above change.
- **Opportunity:** an offer to the process's own entrant. It is consumed even if a sibling would have been selected anyway, and in that case the entrant loses nothing.
- **Who sits out:** every suppressed process. The offer is lost only when all processes are suppressed. It then counts as one of the entrant's Q offers and is not refunded.
- **Stacking:** none. Two hits before the next offer cost one offer. Hit, offer, hit, offer costs two.
- **Across ticks:** never. A stale counter is irrelevant because the tick test fails.
- **Recovery:** after λ offers. At λ = 1 that is the entrant's next offer, possibly in the same chunk.
- **Quota:** migrates to eligible siblings as today.
- **All processes suppressed:** the offer is forfeited and the counters decrement.
- **Cursor:** unchanged. A suppressed process is passed over without consuming its turn, and a forfeit leaves the cursor untouched.
- **λ = None:** `SUPPRESSED ≡ disrupted` and the counter is never read, so V4, RS and E2 stay byte-identical by construction.

**G.4 Bound (λ = 1, Q = 8, chunk 2, two entrants, positive shares).** Every entrant alive throughout a tick executes **≥ 5 actions as first mover and ≥ 4 as second mover**, whatever the opponent does.

- *Proof.* Suppression is set only by enemy writes. A victim chunk's two offers are contiguous, so any hit is consumed by the chunk's first offer and the second offer is always eligible. The first mover's opening chunk precedes every enemy action in the tick. ∎
- The second mover's final offer therefore always executes, and it is the tick's last action.
- [PROBE] A pure jammer holds a repair guard to exactly 5.0 and 4.0 executed actions. Under the stock rule the figures are 2.0 and 0.0.

**G.5 Immunity (G.4 plus K = 2).** Take an entrant whose final executed action, on every tick where it is second mover, writes its own core. It owns at least one core cell at every such evaluation. Its zero-core evaluations can therefore only fall on its own first-mover ticks, which are never consecutive, so its streak never reaches 2. ∎

- This holds for `e2_repair_guard` and for `e2_disrupt_guard`: facing at most 3 enemy locations with at least 4 actions, the guard's last action is always a repair [SOURCE fixtures].

## H. Policy Design

| Aspect              | Decision                                                                                                                                                                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Field               | `RulesetPolicy.disruption_slot_limit: int \| None = None`. "Slot" is the codebase's term (`execute_slot`, forfeit `action_slot`).                                                                                                                          |
| Valid               | `None`, or an `int` ≥ 1, with `bool` rejected (the `capture_hold_ticks` style, :178-188). No upper bound: any value ≥ Q behaves like `None`, but they stay distinct because Q is per-match config.                                                         |
| Default / treatment | `None` everywhere / `1`                                                                                                                                                                                                                                    |
| Runtime state       | `ProcessInstance.disruption_slots_left` (runtime-only, never serialized) and a controller predicate that reads `self.ruleset_policy`. No Ruleset-ID comparison anywhere.                                                                                   |
| IDs                 | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` (primary) and `bytefray-rules-6-research-disruption-slot1` (companion). Each ID names every gameplay difference from V4; research-scale's arena methodology is omitted, as in E2's precedent. |
| Objects             | Independent literal copies, never `replace()`. The one-field difference is verified by a test.                                                                                                                                                             |
| Lifecycle           | `ACTIVE_RESEARCH_RULESET_IDS`. Not in stable, omitted-candidates, Designer, `run`, `agents test` or tournament.                                                                                                                                            |
| Identity            | `ruleset_id` already separates `canonical_match_id`. No `MatchRequest` override (the scheduler overrides remain asserted `None`). The field values are immutable once artifacts exist, and a retired ID must stay resolvable.                              |
| Artifacts           | No replay or result schema change. The replay `disrupted` flag keeps its meaning. Historical artifacts are unaffected (λ = None path).                                                                                                                     |

## I. Mechanical Trace Predictions (seed 42, arena 512; [PROBE])

A's core is 485 and B's is 203. `–` means a lost offer. "Exec" means actions executed per tick.

**Single-location sniper (A) v disrupt guard (B)**

```
E2  t1 A-first: A:W203 A:W204|B:– B:–|A:W205 A:W206|B:– B:–|...  exec 8/0  B ends 0/8 (onset)
    t2 B-first: B:W485 B:W203|A:– A:–|B:W204 B:W205|A:– A:–|...  exec 0/8  B ends 7/8 (recovery)
λ=1 t1 A-first: A:W203 A:W204|B:– B:W485|A:– A:W205|B:W203 B:W204|A:W206 A:W207|B:W205 B:W206|A:W208 A:W209|B:W207 B:W208  exec 7/7  B 7/8
    t2 B-first: B:W485 B:W203|A:– A:W203|B:– B:W204|A:W204 A:W205|...                             exec 7/7  B 3/8

```

- **The endless zero/recovery alternation disappears:** B never reaches zero.
- **The period-2 tie remains,** and every swing favors the last mover (first-mover swing share 0.0). The reversed orientation behaves the same way.

**Pure repair guard v sniper**

- **E2:** B repairs 203 and 204; `A:W203` silences B's remaining 6 slots; B is captured at tick 2.
- **λ = 1:** B executes 7 of 8 actions every tick. It is at zero on 125 ticks, **all its own first-mover ticks**, never two in a row. The result is a tie at 1000.
- **Pure repair becomes viable, but through G.5 (last position plus K = 2), not because disruption became "too weak"** in isolation. The companion arm tests this.

**Three-location spread sniper v disrupt guard**

- **E2:** A wins at tick 3, as in §D.6.
- **λ = 1:** B loses exactly one slot per tick, its core settles at 4 of 8, and the result is a tie at 1000. **Location count stops being decisive.**

**Probe mirror**

- **E2:** A wins at tick 2 at zero core, 32 of 32.
- **λ = 1:** both cores reach 1 of 8 by the end of tick 1 and both zero by the end of tick 2; both complete at tick 3, giving `all_agents_dead`, a tie.
- The sniper mirror becomes a tie at 1000, with both cores at 1 of 8 forever. **Seat determination disappears in both; the result is symmetric mutual elimination or a draw.**

**Guarded-painter mirror (seeds 1–4 and 42)**

- **E2:** B wins on score in all 5 seeds; the second mover executes 0 on every tick.
- **λ = 1:** decisive captures at ticks 48, 72, 159, 58 and 93, won by A, A, A, B and B. **The Seat-B inversion disappears and outcomes become seed-dependent.** Yet the first-mover swing share is 0.0 in all 5 seeds.
- **So outcome seat determination (SDI) and tick-level parity locking come apart.** Both must be measured.

**Other traces**

- **Guarded painter v sniper, both seats:** E2, the painter wins at 154/155 after 77 zero-core ticks. λ = 1, the painter wins at 93 with **0** zero-core ticks. The reversal survives; the zero-core winner does not.
- **Min guard v sniper:** a tie under both, with no zero-core ticks under λ = 1.
- **Sniper v greedy painter:** identical under both (A at tick 2). A non-defending victim is unaffected.
- **Jam sniper v repair guard:** E2, A wins at tick 3; λ = 1, a tie.

## J. Pre-Registered Hypotheses

Populations are defined in C-E2 before any treatment data exists.

- **Exposed:** cells with at least one tick in which a live entrant lost an offer.
- **Stalemate:** C-E2 tick-limit cells containing a recovery; this should reproduce the 610 F1 + 64 F2.

| ID     | Statement                             | Supported if                                                                                                                                                                    | Refuted if            | Probe prior           |
| ------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | --------------------- |
| D0     | No structural change                  | Outcome class unchanged in ≥ 0.90 of exposed cells **and** D2 refuted                                                                                                           | < 0.90                | Fails                 |
| D1     | Parity lock decreases                 | Median two-sided PD ≤ 0.5 in the stalemate population                                                                                                                           | Median PD ≥ 0.9       | Fails                 |
| D2     | Seat determination decreases          | At least half of the C-E2 seat-determined units (3 F1 pairings + probe, sniper and guarded-painter mirrors) fall below SDI 0.9, no new unit reaches it, and 1000 and 1001 agree | None falls            | Supported             |
| D3     | Defense no longer needs disrupt-first | At least half of the repair guard's C-E2 capture losses to {probe, sniper, spread sniper, counter} become non-losses                                                            | None do               | Supported, via G.5    |
| D4     | First-mover control persists          | Median first-mover swing share ≥ 0.9 and D2 refuted                                                                                                                             | Median ≤ 0.5          | Fails                 |
| D5     | Location/process-count exploit        | Spread agents' win-or-draw rate against the 8 stacked agents rises ≥ 0.10 in both seat tables                                                                                   | Falls                 | Fails                 |
| D6     | Re-disruption recreates control       | The jam sniper decisively beats a repair, disrupt or min guard in both seats                                                                                                    | No such win           | Fails                 |
| D7     | Draw-ification                        | Tick-limit share in exposed F1 rises ≥ 0.10 absolute                                                                                                                            | Rises < 0.10 or falls | Likely                |
| **D8** | **Last-mover inversion**              | Median PD ≥ 0.9 **and** median first-mover share ≤ 0.1                                                                                                                          | Median PD ≤ 0.5       | **Supported**         |
| **D9** | **Hold × order immunity**             | T-E3: 0 completions against repair and disrupt guards (a theorem, so also a stop check); T-E3K1: > 0                                                                            | T-E3K1 also 0         | Supported by analysis |

**Pre-registered interpretation:**

| Result          | Conclusion                                                                                                                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 ∧ D2         | Whole-tick disruption is load-bearing for scheduler-locked play                                                                                                                                       |
| D2 ∧ D8         | Load-bearing for *first-mover outcome* determination, but parity control persists through the last position. The next study is in-tick order or the evaluation instant, which needs a scope decision. |
| (D4 ∨ D8) ∧ ¬D2 | Not load-bearing; the disruption line closes                                                                                                                                                          |
| D7              | Recorded as a pathology whatever else holds                                                                                                                                                           |

**A clean negative is reachable.**

**Threshold rationale:**

- 0.9 for SDI is kept for comparability with E2.
- The PD bands are symmetric and interpretable: 0.9 means at most 5% of swings go against the dominant parity.
- The 0.10 absolute bands are practical-significance floors.

Per your standing rule that discovery and test stay separate, none of these thresholds was derived from probe or corpus outcomes.

## K. Metrics

**Primary**

- **PM-1: two-sided parity dependence.**
  - Per match, FMS = the share of ticks where core balance (A own-core minus B own-core) changed and the change favored that tick's first mover.
  - PD = |2·FMS − 1|, with the sign reported separately.
  - Scored only with ≥ 10 swing ticks. Otherwise the cell is reported as "not scoreable", never dropped.
  - FMS is defined even when cores never reach zero.
- **PM-2: E2 capture phase-lock.** The frozen analyzer's definition, read two-sided, with an explicit category **"no zero-core ticks"**. Under λ = 1 the canonical stalemate has none, so the E2 metric would otherwise simply vanish.
- **PM-3: paired outcome transitions,** cell by cell C → T, over {A win, B win, tick-limit tie, mutual elimination}.
- **PM-4: SDI and mirror seat bias,** paired, at 1000 and 1001 ticks.

**Manipulation checks (a gate, not findings, because they hold by construction)**

- **MC-1: executed actions per live entrant per tick** (`cpu_used`): the second mover's mean, the exclusive-tick share (must be 0 under T) and the G.4 bound.
- **MC-2: Action Denial Fraction** = (Q − executed) / Q, for entrants alive at tick end with no forfeit in that tick.
  - This is exactly "lost to disruption" for positive-share agents (proof in §C).
  - Cross-check: Σ executed = `result.json` `statistics.cpu_total`.

**Secondary.** Tick-limit share, recovery rate, completions, zero-core winner rate, decisive-tick distribution, agent seat records, and seat-conditioned Bradley–Terry (subordinate).

**Telemetry.**

- **No schema change and no research-only runtime telemetry.** Everything comes from existing replay fields.
- Memory diffs coalesce contiguous same-owner writes (vm.py:68-77), so per-action order cannot be recovered. Tick-level `cpu_used` is enough.

## L. Experiment Matrix

| Field | Composition                                                    | Per condition |
| ----- | -------------------------------------------------------------- | ------------- |
| F1    | The E2 F1 round robin, unchanged (45 pairs × 32 seeds × 2)     | 2,880         |
| F2    | The 10 E2 mirrors                                              | 640           |
| F2-P  | F2 at **1001** ticks                                           | 640           |
| F4    | `e3_jam_sniper` × 10 E2 agents, plus the jam mirror (11 pairs) | 704           |

- **Total:** 4,864 per condition. The primary study (C-E2, T-E3) is **9,728 matches**; with the companion (C-RS, T-E3K1) it is **19,456**.
- **Cost:** about 40 or 80 minutes single-worker and about 6 or 12 GB, at the measured 0.25 s and 0.6 MB per match.
- **Fixed settings:** arena 512, 1000 ticks, both orientations, all four request overrides asserted `None`. F3 is dropped (reference agents, never pooled, not causal).
- **Why F2-P:** at 1000 ticks the final tick is B-first. Under the stock rule B owns it; under λ = 1, A acts last. That can create a spurious seat effect in mirrors decided on score.
- **Seeds 1–32, justified from E2's n_distinct:**
  - Pairing requires the exact E2 cells.
  - 46 of the 90 ordered F1 cells were single-trajectory characterizations, where more seeds add nothing.
  - The 17 rate-eligible cells are the rng-bearing painter, counter and spread pairings. They needed 26–30 of 32 seeds to reach ≥ 8, and the probe shows the guarded-painter mirror becoming seed-dependent there.
- **Only one new agent is essential: `e3_jam_sniper`,** which alternates anchor hit and core write within each tick.
  - Every existing fixture hits each enemy anchor at most once per tick (per-tick `done` sets) [SOURCE].
  - So without the jammer, the maximal-denial regime, and with it D6, would never be exercised.
  - A pure jammer is needed only as a scripted test.

## M. Statistical and Evidence Rules

1. **Paired cell transitions are primary.** The unit is the distinct transition (C key, T key). Rate claims need n_distinct ≥ 8; everything else is a labelled deterministic characterization.
2. **Denominators are the exposed or stalemate populations**, never all cells.
3. **Parity metrics are two-sided,** with direction reported.
4. **Bradley–Terry residuals are secondary.** A residual counts only if all of these hold: n_distinct ≥ 8, the bootstrap CI excludes 0, **|R| ≥ 1/8**, and the same pairing's C-E2 residual (same frozen code) does not also count.
   - 1/8 is the resolution of the smallest eligible pairing, so the value comes from the eligibility rule, not from E2's data.
   - Pairings where one side wins every distinct trajectory are reported as dominance, not as residual evidence.
5. **Seat conditioning, SDI, mirror bias and n_distinct labels are retained.** The pooled table is subordinate.
6. **Every hypothesis metric is computed on the control too,** pre-registered this time rather than supplementary.
7. **Mirror claims must agree between 1000 and 1001 ticks.** If they disagree, the claim is reported as tick-limit-parity dependent.

## N. Qualification and Freeze Plan

**Sequence** (the E2 discipline):

1. **Freeze-first digests.** Before any runtime change, commit replay SHA-256, `result_id` and `match_id` for a small E2 set: sniper v disrupt guard, repair guard v sniper, spread sniper v disrupt guard, probe mirror and guarded-painter mirror, seeds 1–3, both orientations.
2. **Implement** the Ruleset(s) and runtime (§Q).
3. **Build tooling:** the jam fixture and twin, and an action/parity analyzer. The capture analyzer v2 is reused **unchanged**; its K comes from the registry.
4. **Qualify the analyzers on control data only** (historical T-E2 and C-RS): 0 failures, 0 cross-check mismatches.
5. **Freeze two identities,** kept separate: matrix `v6-e3-matrix-v1-<digest>` and analysis `v6-e3-freeze-v1-<digest>`.
6. **Run controls, then the parent reproduction gate:** the new C-E2 (and C-RS) must equal the historical T-E2 (and C-RS) in every F1/F2 cell, by deep replay comparison.
7. **Run the treatment** (separately authorized), then the treatment gates.
8. **Run the frozen analysis.**

**Hard stops (halt; never patch and continue):**

1. A frozen V4, K = 1 or E2 golden fails, or the new E2 identity digests fail.
2. **Parent reproduction mismatch.**
3. Fixture fingerprint drift.
4. The one-field-difference test fails, or any request override is not `None`.
5. Any T replay violates G.4, or any live entrant has a zero-action tick.
6. The prefix check fails: T and C replays must be identical up to C's first hit tick, and the 64 hit-free F2 cells must be identical entirely.
7. Σ `cpu_used` ≠ `statistics.cpu_total`.
8. A capture-analyzer disagreement.
9. **A D9 violation in T-E3.** It is a theorem, so a violation means the implementation is wrong.
10. The source manifest changes, or the tree is dirty, during execution.
11. An analyzer defect after treatment exposure. Stop interpretation; do not re-freeze under the same identity.

## O. Adversarial Findings

| #    | Finding                                                                                                                        | Evidence            | Disposition                                                |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------- | ---------------------------------------------------------- |
| O-1  | **Parity lock can survive inverted**; E2's one-sided H3b would call it "unlocked"                                              | PROBE               | Two-sided PD; D8                                           |
| O-2  | **λ = 1 × K = 2 × rotation makes continuous repairers uncapturable**                                                           | SOURCE proof, PROBE | Companion arm, or a pre-registered limitation              |
| O-3  | Denial reduction holds by construction                                                                                         | SOURCE              | A manipulation check only                                  |
| O-4  | The existing fixtures never re-disrupt within a tick                                                                           | SOURCE              | Jam sniper                                                 |
| O-5  | Chunk size is inert while ticks are exclusive                                                                                  | SOURCE, PROBE       | Path B deprioritized                                       |
| O-6  | Scope narrowing changes nothing for single-process agents and reopens R4b's C2                                                 | SOURCE, DOC         | Rejected                                                   |
| O-7  | Phase-lock becomes undefined when zero-core ticks vanish                                                                       | PROBE               | "No zero-core ticks" category plus FMS                     |
| O-8  | No F1 cell is hit-free, and first hits mostly land at tick 1–2, so the prefix gate is weak                                     | CORPUS              | Parent reproduction is the strong implementation gate      |
| O-9  | `ProcessMatchController.__init__(**kwargs)` (:642) silently swallows unknown kwargs                                            | SOURCE              | Implementation trap: set semantics only through the policy |
| O-10 | Free global information (R4b's precondition) is an upstream cause E3 cannot rule out                                           | DOC                 | Conclusions stated conditional on it                       |
| O-11 | Competence gap: the fixtures are tuned for whole-tick semantics                                                                | SOURCE              | Claims limited to this corpus plus the jammer              |
| O-12 | The bound and immunity results are specific to 2 entrants, Q = 8, chunk 2 and rotation                                         | SOURCE              | No external-validity claim                                 |
| O-13 | Spamming processes or writes cannot restore total denial: co-located processes share fate; spread evasion is unchanged from V4 | SOURCE, PROBE       | D5/D6 test it                                              |
| O-14 | `disruption_duration = 1` is a gameplay constant outside `RulesetPolicy` (:648)                                                | SOURCE              | LOW/DEFERRED; do not touch in E3                           |

**Architecture (§22).**

- One research ID touches about 54 references in 9 files. Most of that is positional-boolean fan-out in `evaluation_contracts.py` (E2's F-13), and two more IDs repeat it.
- **No cleanup is required before E3.** E2's keyword-only precedent is auditable and its traps are tested.
- The right cleanup would be a table-driven methodology registry. It is **not tiny**, because it touches identity and schema-version resolution for historical evaluation artifacts. It stays DEFERRED; if ever done, it gets its own commit with evaluation-ID byte-identity tests and is never folded into E3.

## P. Recommendation

**The disruption-duration experiment should come next.**

- It is the only candidate that acts on the link that creates exclusive ticks, as one field, for every agent in the stalemate population.
- The scheduler path is a predicted near-null for this pathology (§E), and scope is a null intervention.
- The expected result is informative whichever way it falls. The probe leans toward D2 + D8 + D7: first-mover *outcome* determination collapses, parity locking persists through the last position, and draws rise. That would partly falsify the working hypothesis and point to in-tick order or the evaluation instant as the successor question.

## Q. Implementation Handoff (for the implementing agent; implementation only, do not run the matrix)

1. **Freeze first:** the E2 identity digests from §N step 1, committed only when instructed.
2. **Policy** in `ruleset_policy.py`:
   - add `disruption_slot_limit: int | None = None`, validated in `__post_init__`;
   - add two literal policy objects;
   - register them in `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS` and `__all__`;
   - add the ID constants in `rules.py`.
3. **Runtime** in `process_runtime.py`:
   - add `ProcessInstance.disruption_slots_left`, reset in `reset()`;
   - set it by assignment at the hit (:1262);
   - add a controller `_is_suppressed(p, tick)`, used in `_effective_process_quotas` (:809) and `_visible_enemy_anchors` (:769-773);
   - snapshot the suppressed set at the start of `execute_entrant_slot` and decrement it in a `try/finally` that covers every return path;
   - leave `_process_snapshots` on `is_disrupted`.
   - **Do not touch** `scheduler.py`, `_select_active_process`, `disruption_duration`, or the replay and result schemas. No ID branching.
4. **Plumbing** (E2 precedent): the core-placement guard, the evaluation allow-list and arena-range check, CLI choices, and a distinct alignment label with a keyword-only flag. **Trap F-4:** an omitted arena must resolve to 512.
5. **Tests.** Every sequence asserted by value:
   - policy validation;
   - the one-field difference;
   - λ = None byte identity (V4 and E2, unedited);
   - G.3 cases: single hit, double hit, hit–offer–hit, hit after the final offer, co-located and spread multi-process, quota and cursor, sensing, the replay flag;
   - the G.4 bound with a scripted jammer;
   - G.5 immunity;
   - determinism;
   - no product exposure.
6. **Validation:** the focused modules, then `python -m pytest`, `mypy`, `ruff check .`, reported with exact counts.

The research tooling is a separate follow-up task: the jam fixture, analyzer, matrix, pre-registration and gates.

**Appendix: the probe.**

- `scratchpad/probe.py` monkeypatches `ProcessInstance.disrupted_until_tick` and `is_disrupted`, wraps `RulesetPolicy.run_scheduler`'s slot callback to decrement and log each offer, and logs `VM._wr8`. Scheduler variants use the existing `MatchRequest` overrides.
- **Validity:** at λ = None it reproduces E2 §D.2–D.6 action for action.
- **Exposure was deliberately limited to about 45 named-scenario matches** (all in §I), with no grid run, so the matrix stays blind.
- The probe also changes the replay `disrupted` flag. The recommended implementation does not.

---

If you want this recorded, I can write it to `docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md` once you authorize file changes.

Separately, the claude.ai Google Drive connector needs authorization in your claude.ai connector settings before it can be used. This review didn't need it.