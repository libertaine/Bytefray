# Bytefray V6 E2 — Multi-Tick Capture Hold: Design & Adversarial Review

**Status:** Design review complete. **No implementation.** Nothing committed.
**Branch:** `v6-research`
**Baseline:** `174a640eda5a7300a348355ee1ddda12762b6b9a`
**Date:** 2026-09-23
**Predecessors:** [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md) (Research Integrity Addendum, 2026-09-22), `engine/tests/test_v4_exploit_characterization.py`

**Evidence tiers used in this report.** Every claim is labelled with one of these tiers:

- **[SOURCE]** comes from reading current source at the baseline SHA, cited by file and line.
- **[RUN]** comes from executing the unmodified repository: tests, or harness functions called directly.
- **[PROBE]** comes from a scratch-only design probe. The probe drives the real `ProcessMatchController`, with its real scheduler, disruption, visibility, quota and capture detection. For the treatment arms it replaces the module-level `apply_core_capture` reference with a K-tick hold prototype. The probe lives outside the repository and is exploratory evidence for design decisions. It is **not** qualification evidence and **not** E2 results (Appendix P describes it so it can be rebuilt).

---

## Verdict (summary)

**E2 is isolated enough and ready for implementation, but only under the refined semantics in §C.** Implementing the one-line description ("zero core ownership must persist for two consecutive ticks") literally would silently break kill attribution. The capture would then complete as an unattributed `death`, with no `+5` kill score and no evaluation `killer`, because `_attribute_core_capture` returns `None` whenever the core was already at zero before the tick began (`python_runtime.py:199-201`).

The adversarial probe answers the central scientific question in advance, at exploratory strength:

- **K=2 creates a real response window, but a narrow one.** Seat B always gets an executable two-action chunk at the start of tick 2. Disruption has expired and the scheduler rotates the first mover. That chunk decides the match only if B spends it **disrupting every attacker location first** and repairing second. Repair alone is overwritten later in the same tick, so for a pure repair guard the window is nominal.
- **The canonical probe mirror stays 100% seat-determined.** It is simply delayed to tick 2, which is H0 for the naive probe. Seat A still wins, and it finishes the match holding **zero** core cells. That state cannot occur under V4.
- **The window depends on how many locations the attacker has.** A two-action chunk can disrupt at most two locations. An attacker spread over three or more locations therefore closes the window against any defender still stacked at its spawn.
- **K=2 shifts outcomes towards draws.** In the exploratory 9-agent grid (324 matches per arm), Seat-A wins fell from 164 to 128, Seat-B wins from 98 to 94, and ties rose from 62 to 102. Most of the change is forced Seat-A wins turning into **phase-locked alternation stalemates**: the defender's core is at zero on every attacker-first tick and recovered on every defender-first tick, until the tick limit. That is H3.
- **K=2 introduces at least one new seat-determined inversion.** The guarded-painter mirror goes from 27 Seat-A / 5 Seat-B wins under V4 to **32/32 Seat-B wins** under K=2, across all 32 seeds. The result holds at tick limits of 299, 300, 301, 1000 and 1001.
- **K=3 gave the same outcome pattern as K=2** in the prototype grid; only the decision ticks moved later.

These are priors to be tested, not results. The experiment is still worth running: it isolates one variable cleanly, and its most likely result is a mixed or partly negative one, which is scientifically valuable.

There are also **harness defects** that must be fixed before the E2 matrix is interpreted (§I.4, all [RUN]-verified). The worst is that the consolidated harness's headline metrics cannot see seat determination. A field where Seat A wins every single match gets all ratings at 1500, RMSR 0.0 and zero cycles, which looks exactly like a perfectly balanced field.

---

## A. Repository Baseline

### A.1 Git and environment

| Item | Value |
|---|---|
| Branch | `v6-research` |
| HEAD | `174a640eda5a7300a348355ee1ddda12762b6b9a` — `fix(engine): ensure JSONLSink is closed explicitly in _run_v4_process_match` |
| Upstream | `origin/v6-research` = `24fac67` ("Complete V6 Phase 2 final qualification"). After `git fetch --all --prune`, local is **32 ahead, 0 behind**. The whole remediation series is unpushed. |
| Relation to `main` | `origin/main` = `82549f9`; HEAD is 55 commits ahead |
| Working tree | Clean at start (`git status --porcelain` empty). The only change this review makes is adding this report file. |
| Python | 3.13.14 (tags/v3.13.14:fd17997, MSC v.1944 64-bit AMD64), repo `.venv` |
| Platform | Windows-11-10.0.26120-SP0 |
| Focused tests [RUN] | `test_v4_exploit_characterization.py`, `test_ruleset_v6_research_scale.py`, `test_v6_experiment_harness.py`, `test_ruleset_policy.py`: **95 passed** in 3.16 s. This is a focused subset, **not** the repository suite. |

### A.2 Ruleset lifecycle definitions (`ruleset_policy.py:568-588`) [SOURCE]

| Set | Members |
|---|---|
| `PUBLIC_STABLE_RULESET_IDS` | `bytefray-rules-4` |
| `ACTIVE_RESEARCH_RULESET_IDS` | `bytefray-rules-6-research-scale` |
| `RETIRED_RESEARCH_RULESET_IDS` | `bytefray-rules-6-research-scale-move`, `bytefray-rules-6-research-scale-move-proportional` |
| `HISTORICAL_READONLY_RULESET_IDS` | `bytefray-rules-2`, `-2-alpha1`, `-2-alpha11`, `-3-alpha1`, `-4-alpha1`, `-4-alpha2` |

Executable registry `_RULESET_POLICIES` (`ruleset_policy.py:640-647`): `bytefray-rules-4`, `-6-research-scale`, `-6-research-scale-move`, `-6-research-scale-move-proportional`.

Four observations are relevant to how E2 gets classified. They are recorded here, not fixed:

1. **The lifecycle sets have no consumers.** A repository-wide search finds them referenced only at their definition and in `__all__`. Putting E2 in `ACTIVE_RESEARCH_RULESET_IDS` is therefore documentary and enforces nothing. The real exposure controls are the explicit per-surface lists:
   - `OMITTED_RULESET_CANDIDATES` (`ruleset_policy.py:772`);
   - the Designer options (`app/services/ruleset_options.py:63-65`);
   - the `--ruleset choices=[bytefray-rules-4]` lists in `cli.py:253`, `agent_test.py:1014` and `tournament_cli.py:55`;
   - the evaluation allow-list (`evaluation_service.py:112`) and `evaluation_cli.py:180`.

   §J adds a test that makes the lifecycle sets load-bearing.
2. **"Retired" research IDs can still be executed.** Both movement-line IDs remain in `_RULESET_POLICIES`, `PROCESS_RULESET_IDS`, the evaluation allow-list and the evaluation CLI choices. "Retired" is a label only. This is not an E2 blocker. It matters because retiring E2 later would, under the current pattern, likewise leave it executable.
3. **`HISTORICAL_READONLY_RULESET_IDS` omits `bytefray-rules-1`** (`rules.BYTEFRAY_RULESET_ID`), even though the policy module documents it as a retained historical-recognition identity. Low severity; deferred.
4. **`MatchRequest.scheduler_chunk_size` / `scheduler_rotate_start`** (`match_service.py:192-193`) are per-match scheduler overrides. They are folded into `canonical_match_id` when set (`match_service.py:903-917`), so identity is protected. They are still exactly the kind of research-only switch AGENTS.md warns about. E2 runs must assert both are `None`, or the claim that only one field differs is false.

### A.3 Remediation state understood

- The characterization gate `test_v4_exploit_characterization.py` is present and green. It pins the V4 winner `A`, tick 1, reason `last_agent_standing`, in both seat orientations, at seed 42 and arena 512.
- The consolidated harness `tools/research/v6/experiment_harness.py` records `git_sha`, `git_dirty` and agent fingerprints. It computes Bradley-Terry ratings, residuals, RMSR, upsets and directed 3-cycles, and resolves benchmark agents from tracked fixtures.
- ROADMAP (`docs/ROADMAP.md:21,202`) and FUTURE_PLANS (`docs/FUTURE_PLANS.md:312-314`) list E2 as Planned. **Framing defect:** ROADMAP line 202 describes E2 as "introducing multi-tick core capture hold mechanics **to eliminate** the tick-1 Seat-A forced win, **restoring** defensive counterplay". That wording assumes the outcome. The probe already suggests it is partly false. It should be reworded as a question when E2 is registered (§N).

---

## B. Current Capture Semantics (V4)

### B.1 Tick lifecycle [SOURCE]

All line references are to `engine/src/battle_engine/process_runtime.py` unless stated otherwise.

| Step | What happens | Where |
|---|---|---|
| 0 | Before tick 1: each entrant's 8 core cells (`start..start+7`, wrapping) are seeded with byte `0xCE`, owned by the entrant. Every declared process gets anchor = core base. | `696-730` |
| 1 | Clear tick diffs. Snapshot `pre_tick_core_owners` for **live** entrants only. | `1004-1012` |
| 2 | Record disruption telemetry for processes that are already disrupted. | `1017-1022` |
| 3 | Run the scheduler: `run_chunked_quota`, chunk 2, start rotated by `(tick-1) % n`. Tick 1 order is A,A,B,B,A,A,B,B,…; tick 2 order is B,B,A,A,… | `1271-1274`, `scheduler.py:52-99`, `ruleset_policy.py:246-267` |
| 4 | Each slot: `_effective_process_quotas` over **non-disrupted** processes. `_select_active_process` (round-robin cursor) returns `None` if no process is eligible, and **the slot is forfeited**. | `1042-1049`, `780-907` |
| 5 | `WRITE` sets the cell's owner to the actor, then disrupts **every enemy process whose anchor equals the target**: `disrupted_until_tick = tick + 1`. Friendly processes are immune. | `1221-1257` |
| 6 | **`apply_core_capture`**: for each live entrant, `owned_now = #core cells whose writer == self`. If zero, the entrant is dead **now**. | `1276-1285`, `python_runtime.py:218-272` |
| 7 | Statistics, `score_alive` (+1 per live entrant), `score_territory` (+1 per 64 owned cells). | `1287-1297` |
| 8 | Publish the replay tick (`events` holds `kill`/`death`/`forfeit`). | `1299-1307` |
| 9 | `resolve_termination(alive_count, tick, max_ticks)`: 0 alive → `all_agents_dead`; 1 → `last_agent_standing`; tick limit → `tick_limit`. | `1312-1317`, `ruleset_policy.py:271-305` |
| 10 | After the loop: winner is the survivor, `tie` if none, or the score fallback (`tie` on equal top scores). | `1326-1339` |

`is_disrupted(t) = t < disrupted_until_tick` (`115-116`) and `disruption_duration = 1` (`640`). A process disrupted during tick T is therefore eligible again at the start of tick T+1.

### B.2 Where capture is detected, recorded, applied and exposed

| Aspect | Current behavior |
|---|---|
| Detected | Once per tick, after every action, before scoring and termination (`python_runtime.py:245-251`). Only the board at the **end of the tick** matters, so a core that hits zero and recovers within the tick is invisible. |
| Recorded | `state.entrant_termination = "core_captured"` (`python_runtime.py:265`). `statistics_collector.record_death(victim, killer?)`. |
| Applied | `state.alive = False` in the same pass (`python_runtime.py:264`). |
| Attributed | `_attribute_core_capture` replays **this tick's** `vm.tick_diffs` from the pre-tick snapshot. The killer is the writer of the diff that removed the last self-owned cell. It returns `None` if the entrant already owned zero cells before the tick (`python_runtime.py:199-201`). |
| Kill credit | `score_kill` (+5, `config.py:13`) and a `{"type":"kill","victim","by"}` event. If the capture is unattributed, a `{"type":"death"}` event is emitted instead. |
| Replay | The events list in that tick's snapshot (`telemetry.py:103-122`), carried into canonical schema-4 replays. The reader **rejects unknown event types** (`replay.py:359`). |
| Termination reason | Match level is alive-count driven (`last_agent_standing` / `all_agents_dead`). Entrant level is `core_captured` in `result.json` `entrants[].termination_reason` (`match_service.py:943`). |
| Scores and artifacts | `result_id` hashes the winner, reason, ticks, score and entrants (`match_service.py:971`). `evaluation_capture.py:121-133` derives `capture_tick = envelope.ticks` and `killer` from `statistics.kills`. |

### B.3 Implicit cross-tick state

**Capture keeps none.** `apply_core_capture` is a pure function of the end-of-tick board, this tick's pre-tick snapshot and this tick's diffs. The only cross-tick state anywhere in the runtime is:

- the board itself;
- `alive` flags and score;
- `disrupted_until_tick`, which always expires at the next boundary;
- the match-scoped round-robin process cursor (`_process_cursor`, `651-653`).

E2 adds the **first** piece of cross-tick capture state.

### B.4 V4 state transition

```
ALIVE --[end of tick t: owned(e) == 0]--> CAPTURED (at end of tick t)
```

### B.5 Invariants E2 touches

| ID | Invariant (V4) | E2 disposition |
|---|---|---|
| I-1 | Capture is evaluated exactly once per tick, after all actions, before stats/scoring/termination. | **Preserved.** |
| I-2 | Only end-of-tick ownership matters; intra-tick zero is invisible. | **Preserved.** |
| I-3 | A captured entrant gets no alive or territory score for its capture tick. | **Preserved**, applied at the completion tick. |
| I-4 | The killer is the writer that removed the last owned cell *this tick*. | **Must change** to onset attribution (§C.5); otherwise every E2 capture becomes unattributed. |
| I-5 | Simultaneous capture: both dead → `all_agents_dead` → winner `tie`. | **Preserved** through two-phase evaluation (§C.4). |
| I-6 | An entrant's own `WRITE` always sets owner = self, so it cannot reduce its own ownership. Zero ownership is always enemy-caused. | Unchanged. It is the reason "recovery" is a single own-core `WRITE`. |
| I-7 | Disruption lasts until the next tick boundary (D = 1). | Unchanged. It is the mechanism of the E2 response window (§D). |
| I-8 | The tick-t first mover is seat `(t-1) mod 2`. | Unchanged. The rotation period (2) equals K (2); see §D.6 and §L. |
| I-9 | Independent elimination is **forfeit only** (callback exception, invalid action, timeout: `1076-1166`). There is **no per-process death** in the process runtime. | Unchanged. See §C.3 (Q6). |
| I-10 | Match termination reasons are alive-count based. | Unchanged; no new reason values. |
| I-11 | Every entrant with zero owned core cells at a tick end is dead. | **Deliberately broken** at K ≥ 2: an entrant can be alive and at zero, including as the **winner** (§C.6). |
| I-12 | `capture_tick == envelope.ticks` for a capture-terminated 1v1 match (`evaluation_capture.py:127`). | Still holds at K = 2, because completion ends the 1v1 match at that tick. |

---

## C. Proposed E2 Semantics

### C.1 Definitions

- `K = RulesetPolicy.capture_hold_ticks`, an integer ≥ 1. Stable V4 and every existing policy: `K = 1`. E2 treatment: `K = 2`.
- `owned(e)` = the number of entrant `e`'s 8 core cells whose `vm.writer == e`, read at the V4 evaluation point (after every action of the tick, before stats, scoring and termination).
- Per-entrant runtime state, valid only while `e.alive`:
  - `zero_streak(e) ∈ {0, …, K-1}`: the number of consecutive capture evaluations, ending at the latest one, with `owned(e) == 0`.
  - `onset_capturer(e) ∈ AgentId ∪ {None}`: the attributed capturer at the evaluation where the current streak began.

### C.2 Transition (evaluated exactly where V4 evaluates capture)

```python
def evaluate_core_capture(states, vm, pre_tick_owners, K, ...):
    # Phase 1: every live entrant is judged against the same end-of-tick board.
    #          Nothing in this phase changes `alive`.
    completing = []
    for e in states:                                   # seat order; order-independent (C.4)
        if not e.alive:
            continue
        if owned(e) >= 1:                              # ANY positive ownership
            e.zero_streak = 0
            e.onset_capturer = None
            continue
        if e.zero_streak == 0:                         # onset of a new streak
            e.onset_capturer = _attribute_core_capture(  # unchanged V4 function,
                e, core_addrs(e), pre_tick_owners[e], vm)  # this tick's snapshot/diffs
        e.zero_streak += 1
        if e.zero_streak >= K:
            completing.append(e)
    # Phase 2: every completion is applied together.
    for e in completing:                               # seat order: event order only
        e.alive = False
        e.entrant_termination = "core_captured"
        k = e.onset_capturer
        if k is not None and k != e.agent_id:
            scoring.score_kill(score, k)
            stats.record_death(statistics, e.agent_id, k)
            events.append({"type": "kill", "victim": e.agent_id, "by": k})
        else:
            stats.record_death(statistics, e.agent_id)
            events.append({"type": "death", "victim": e.agent_id})
```

State table for `K = 2`:

| `zero_streak` before | `owned` at tick end | Effect | `zero_streak` after | Alive after |
|---|---|---|---|---|
| 0 | ≥ 1 | none | 0 | yes |
| 0 | 0 | **onset**: attribution is recorded | 1 | yes (capture-threatened) |
| 1 | ≥ 1 | **recovery**: attribution cleared | 0 | yes |
| 1 | 0 | **completion** | — | **no** (`core_captured`, credited to `onset_capturer`) |

### C.3 Resolution of each semantic question

**Q1. When does the counter begin?** At the end of tick T, if `owned == 0` and `zero_streak == 0`, then `zero_streak := 1`. The entrant stays alive. It receives the tick-T alive and territory score, because it is alive when scoring runs. No event is emitted (see §K).

**Q2. When is capture completed?** At the capture evaluation of tick T+1, if `owned` is still 0. It takes effect immediately at that evaluation, before scoring and termination. The entrant gets no alive or territory score for T+1 (I-3 carried to the completion tick). A 1v1 match then ends at T+1.

**Q3. What resets progress?** Any `owned ≥ 1` at the next evaluation: one cell, some cells or the whole core. That fully resets the streak to 0 and clears the attribution. Reasons:

- It is the exact negation of V4's own capture predicate: V4 already treats one owned cell as fully alive.
- Any other threshold (for example "must restore k of 8") would add a second gameplay variable, a recovery threshold, which breaks the one-variable constraint.
- At K = 2 it is indistinguishable from the alternative anyway (next point).

**Reset versus decrement.** At K = 2 the only non-terminal streak values are 0 and 1. Reset maps a positive evaluation to 0 from either value. Decrement maps 1 → 0 and 0 → 0. The two rules are **identical for every possible sequence**, so the question is moot for E2. They diverge only at K ≥ 3. There the choice is a real second design variable and must be made explicitly for any K ≥ 3 arm. "Reset" is specified here because it matches the plain meaning of "consecutive".

**Q4. Zero and recovered within the same tick?** Invisible. Only the end-of-tick state matters, consistent with V4 (I-2). No intra-tick capture state is added.

**Q5. Both entrants complete at the same evaluation?** Two-phase evaluation marks both in Phase 1 and applies both in Phase 2. Both die, the match ends `all_agents_dead` and the winner is `tie`, exactly V4's simultaneous-capture outcome (I-5).

**Q5a. Staggered completion.** If A completes (streak 2) while B only reaches streak 1, A dies, B survives and B wins `last_agent_standing` **while owning zero core cells**. This is a direct consequence of the semantic, not a defect. It is measured, not ruled on (§C.6).

**Q6. No live processes but still owning core cells?** V4 has no such state (I-9). Processes are never removed; a disrupted process becomes eligible again at the next tick. The independent elimination path is **forfeit**. The three concepts stay fully separate:

| Concept | Scope | Effect | Termination label |
|---|---|---|---|
| Process disruption | one process, rest of the current tick | slots forfeited while every process is disrupted | none |
| Forfeit | entrant, immediate, mid-tick | `alive = False` | `forfeit` |
| Core capture | entrant, at K consecutive zero-ownership evaluations | `alive = False` at completion | `core_captured` |

How they interact:

- **Forfeit during a streak.** Forfeit fires mid-tick. The dead entrant is skipped by the evaluation and its streak is never read again. The capturer gets no kill credit, the same as a V4 forfeit.
- **Opponent forfeits during T+1 while self is at streak 1.** If self is still at zero at the end of T+1, self completes. Both are dead, so the result is `all_agents_dead` / `tie`, consistent with V4, where an entrant at zero at a tick end always dies.

### C.4 Determinism and freedom from seat bias

Phase 1 reads only the board, the pre-tick snapshot and the tick diffs. None of these is changed by Phase 1, and no entrant's outcome depends on another entrant's `alive` flag. The **set** of completing entrants is therefore independent of iteration order. Seat order affects only the order in which events are appended, and that order is deterministic and does not affect the outcome. State is plain per-entrant integers and strings with no dict or set iteration, so it is platform-independent.

### C.5 Attribution refinement (required)

**Problem [SOURCE].** At the completion tick T+1, `pre_tick_core_owners[e]` already has zero self-owned cells. `_attribute_core_capture` returns `None` at `python_runtime.py:199-201`. Grafting a streak counter onto the current `apply_core_capture` without this refinement would make **every** E2 capture an unattributed `death`, which has three effects:

1. The capturer loses the `+5` kill score (`config.py:13`). That changes tick-limit comparisons and `result_id` contents.
2. `evaluation_capture` records `killer = None` for every E2 capture (`evaluation_capture.py:127-134`).
3. The replay viewer's killer attribution disappears (`client/src/battle_client/replay_status.py:136-152`).

Together these amount to an accidental second variable, "kills are worth 0 under E2".

**Refinement.** Attribute at **onset**, using the unchanged V4 function on the onset tick's own snapshot and diffs, and carry the result until completion or reset. Credit it at **completion**, since an onset that never completes grants nothing. At K = 1 the onset tick and the completion tick are the same, so this is exactly V4.

A rejected alternative was crediting whoever holds the most core cells at completion. That is a new rule and could differ from V4 even at K = 1.

### C.6 New states that become reachable (measured, never ruled on)

- **Alive at zero core ("capture-threatened")** at the end of a tick.
- **Winner at zero core.** [PROBE] In the probe mirror, A wins at tick 2 holding 0/8 core cells (§D.3).
- **Tick limit reached with an entrant at streak 1.** It survives and can win on score.
- **Perpetual alternation.** The streak oscillates 1,0,1,0… in lockstep with the scheduler rotation (§D.5).

Any extra rule, such as "capture-threatened at the tick limit loses" or "a zero-core winner is a tie", would be a second mechanic and is **excluded** from E2.

### C.7 Equivalence at K = 1

With K = 1, Phase 1 marks exactly the entrants with `owned == 0`, attributed from this tick's snapshot, which is what V4 does. Phase 2 applies `alive = False` and emits the same events in the same seat order. V4's single loop sets `alive = False` as it iterates, but nothing later in that loop reads another entrant's `alive` flag, so the two-phase form is observationally identical. [PROBE] K = 1 through the prototype reproduced stock V4's winner, ticks, reason and score for the probe mirror on seeds 1–32. The implementation must prove this again against the frozen goldens (§J.1).

---

## D. Tick-by-Tick Probe Analysis

### D.1 Setup

Seed 42, arena 512, stable-V4 seeded placement: A's core base is **485** (cells 485–492) and B's is **203** (cells 203–210). Every process spawns at its own core base. Reach is 256 (global). The scheduler is `chunk=2, rotate_start=True`. Traces are [PROBE] output from the real controller; "forfeit" means `_select_active_process` returned `None`.

### D.2 V4 (K=1), probe mirror: the forced line

Tick 1, first mover A: `A:W203  A:W204 | B:forfeit ×2 | A:W205 A:W206 | B:forfeit ×2 | A:W207 A:W208 | B:forfeit ×2 | A:W209 A:W210 | B:forfeit ×2`

- A's **first** write (203) lands on B's only anchor, so B's process is disrupted until tick 2.
- Seat B gets 8 slot offers and forfeits all 8. It never executes an action.
- End of tick 1: A owns 8/8, B owns 0/8, so B is **captured on tick 1**. Score: A 6 (1 alive + 5 kill), B 0.

This matches the [RUN] characterization gate exactly.

### D.3 E2 (K=2), probe mirror: B gets a full, uncontested tick and wastes it

- **Tick 1** is identical to V4. At the end, B owns 0/8: **onset**, `streak_B = 1`, B alive.
- **Tick 2**, first mover **B**. B's disruption has expired (`disrupted_until_tick = 2`, so `is_disrupted(2)` is False). Order is B,B,A,A,… B's probe does what the probe does: `B:W485` (disrupts A for the rest of tick 2), then `W486 … W492`. **A forfeits all 8 slots.**
- End of tick 2: A owns 0/8 (onset, `streak_A = 1`). B still owns 0/8, so `streak_B = 2` and B **completes**. **A wins at tick 2 while holding zero core cells.**

The probe is given the most generous response window possible, a whole uncontested tick, and spends it on the opponent's core because it never repairs. **The probe mirror remains 100% seat-determined, delayed by one tick** [PROBE: 32/32 seeds, 1 distinct trajectory]. That is H0 for the probe itself.

### D.4 E2, Global Sniper (A) vs Pure Repair Guard (B): the nominal window

Tick 2, first mover B:

- `B:W203 B:W204`: B repairs two cells.
- `A:W203`: A retakes 203 **and disrupts B**, whose anchor is 203. `A:W204`.
- B forfeits ×2, then A writes 205–206; B forfeits ×2, A 207–208; B forfeits ×2, A 209–210.
- End of tick 2: B owns 0/8, `streak = 2`, **captured at tick 2**.

B executed two legal repair actions and both were undone within the same tick. Its other six slots were forfeited. **The window is executable but nominal.**

### D.5 E2, Global Sniper (A) vs Disrupt-Guard (B): the genuine window, and a stalemate

- **Tick 2**, B first: `B:W485` disrupts A for the rest of the tick. `B:W203 … W209` repairs 7 cells. A forfeits all 8 slots. End: A owns 7/8, B owns 7/8, so **B recovers** (streak reset).
- **Tick 3**, A first: `A:W203` disrupts B, then A rewrites 204–210. B owns 0/8 (onset).
- **Tick 4**, B first: the same as tick 2, and B recovers again.

The result is **perpetual alternation**: B is at zero on every odd tick and recovered on every even tick. In a 300-tick match that is 150 onsets and 150 recoveries, and it ends in a tie at the tick limit on equal scores [PROBE: 32/32 seeds, 1 trajectory].

The defense works only because three conditions hold together:

1. B is first mover on even ticks (rotation, I-8).
2. A's whole presence is one location, and a single WRITE disables it for the rest of the tick (co-location plus D = 1).
3. One own-core cell is enough to recover (reset at ≥ 1).

### D.6 E2, Spread Sniper (A, 3 processes) vs Disrupt-Guard (B): location count closes the window

- **Tick 1**, A first: `p0:W203` (disrupts B), `p1:MOVE+40 → 13`, `p2:MOVE−40 → 445`, then writes 204–208. B owns 2/8, so **no onset**. A deliberately used tick 1 to spread.
- **Tick 2**, B first. B sees anchors `[13, 445, 485]`:
  - `B:W13` disrupts p1 and `B:W445` disrupts p2. B's two-action chunk is spent.
  - A's p0 at 485 is still live: `A:W203` disrupts **all** of B for the rest of tick 2, then A writes 204–210.
  - B owns 0/8: **onset on B's own first-mover tick**.
- **Tick 3**, A first: `A:W203` disrupts B before B acts. B never acts, so **captured at tick 3**.

A two-action chunk can neutralize at most two locations. Seat B's processes are always stacked at tick 2, because B never acts on tick 1, so a single surviving attacker process disables all of them. And because the onset fell on B's first-mover tick, B's follow-up tick comes **second**.

### D.7 Answer: does E2 give Seat B a meaningful defense opportunity?

**What E2 guarantees.**

- After a tick-1 onset, Seat B's disruption has always expired at tick 2 and B is first mover. So Seat B **always gets two executable actions before Seat A acts on tick 2.** This is a real, unconditional executable window, which V4 never provides.
- Legal actions for B: `WRITE` to its own core cell (repair); `WRITE` to an enemy anchor (disrupt); `WRITE` to the enemy core (counterattack); `MOVE` of up to 64 cells, which ends co-location; `READ`.

**When the window is meaningful.** B survives tick 2 if its first chunk disrupts every **live attacker location**, which requires at most two distinct locations, all visible within reach, **and** at least one repair survives to the end of the tick.

- Against a single-location attacker, "disrupt, then repair" is enough.
- Against two locations, the chunk is "disrupt, disrupt", and the repair comes in B's slot 2, after the attacker's slots were forfeited.

**When the window is nominal.**

- (a) B only repairs (§D.4).
- (b) The attacker has three or more live locations while B is still stacked (§D.6).
- (c) The onset falls on B's own first-mover tick, so its follow-up tick is attacker-first and B acts only if some of its processes survive the attacker's first chunk.

**Conclusion.** E2 genuinely breaks the **canonical** V4 forced line (single-location global sniper versus a disrupt-first defender). It does **not** neutralize Seat A's structural tempo advantage. Seat A still gets a whole uncontested tick 1, in which Seat B cannot even spread, and a multi-location attacker converts that tick into a location-count lead the defender cannot overcome from a stacked spawn. The meaningful defensive action under E2 is **disruption, which is offensive**, followed by a one-cell repair. Repair alone is never sufficient against an attacker that keeps a live process.

### D.8 Exploratory aggregates [PROBE]

**9-agent grid:** agents are defined in §G. Arena 512, 300-tick limit, seeds 1–4, every ordered pair including mirrors, giving 81 cells and 324 matches per arm.

| Arm | Seat-A wins | Seat-B wins | Ties |
|---|---|---|---|
| V4 (K=1) | 164 (50.6%) | 98 (30.2%) | 62 (19.1%) |
| E2 (K=2) | 128 (39.5%) | 94 (29.0%) | 102 (31.5%) |
| K=3 (secondary probe) | 128 | 94 | 102 |

The K=2 and K=3 grids have **identical outcome columns** in all 81 cells; only the decision ticks move.

**Mirror matches** (the purest seat-bias measurement):

| Agent (both seats) | V4 | E2 (K=2) |
|---|---|---|
| V4 probe / Global Sniper | Seat A, tick 1 (32/32) | **Seat A, tick 2 (32/32)** |
| Disrupt-Guard, Minimal Guard, Spread Defender | tie (tick limit) | tie (tick limit) |
| Spread Sniper | Seat A, tick 2 | Seat A, tick 3 |
| Greedy Painter | 32 seeds: A 6 / B 8 / 18 ties (mostly simultaneous double-capture) | identical |
| Guarded Painter | A 27 / B 5 (32 seeds) | **B 32/32 (tick-limit score; mutual alternation, e.g. from tick 167 on seed 5)** |
| Spread Painter | Seat A 4/4 (kill at ticks 103–173) | Seat A 4/4 (tick-limit score) |

**Selected treatment effects**, as V4 → E2 for the pair (Seat A agent, Seat B agent):

- Sniper vs Disrupt-Guard, Minimal Guard or Spread Defender: A wins at tick 1 → **tie**.
- Sniper vs Guarded Painter or Spread Painter: A wins at tick 1 → **B wins** (the painter's front eventually overwrites the sniper's core).
- Disrupt-Guard vs Sniper: B wins at tick 2 → **tie** (V4 already lets Seat B kill at tick 2 when Seat A does not kill at tick 1).
- Guarded Painter vs Sniper: B wins at tick 2 → **A wins**.
- Sniper vs Greedy Painter, or vs Pure Guard: A wins at tick 1 → A wins at tick 2 (delay only).

**Opponent dependence under E2** (pooled across seats): Sniper beats Greedy Painter, Greedy Painter beats Spread Defender (on score), and Spread Defender ties Sniper. This near-cycle has a tie edge (0.5), so the harness's 0.55 threshold correctly reports **no** 3-cycle. Under V4 the same three agents are transitive (Sniper beats Spread Defender 0.75). This is exactly the kind of change that a threshold count cannot show and residual analysis must (§I).

---

## E. Minimal Code Surface (no implementation)

### E.1 Gameplay surface: the only behavior change (3 files)

| File | Change | Why |
|---|---|---|
| `engine/src/battle_engine/ruleset_policy.py` | Add `capture_hold_ticks: int = 1` to `RulesetPolicy`. Validate it in `__post_init__`. Add the E2 policy object. | Semantics live on the policy (AGENTS.md "Compatibility requirements"). The runtime consumes the value; it never compares IDs. |
| `engine/src/battle_engine/python_runtime.py` | `apply_core_capture(..., hold_ticks: int = 1)`: two-phase evaluation, streak and onset attribution (§C.2). `_attribute_core_capture` stays **unchanged**. | The single shared capture implementation used by the retained runtime. |
| `engine/src/battle_engine/process_runtime.py` | `EntrantState` gains `core_zero_streak: int = 0` and `core_zero_onset_capturer: str \| None = None`. Pass `hold_ticks=self.ruleset_policy.capture_hold_ticks` in the call at `1276`. | Per-entrant, per-match state. It is never serialized wholesale: `_agent_snapshot` and statistics read named attributes only (verified), so replay and result shapes are unaffected. |

None of these three files may contain a `ruleset_id` comparison.

### E.2 Identity and registration surface (follows the Phase 4C/4D precedent)

| File | Change |
|---|---|
| `rules.py` | `BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID`, with a provenance comment and an `__all__` entry. |
| `ruleset_policy.py` | Add to `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS`, `__all__`. **Not** to `OMITTED_RULESET_CANDIDATES` or `PUBLIC_STABLE_RULESET_IDS`. |
| `match_service.py:412-429` | Add to `_CORE_PLACEMENT_GUARDED_RULESET_IDS`. E2 shares seeded placement, so overlapping cores must fail closed exactly as they do for its control. |
| `evaluation_service.py:112` | Add to `_EVALUATION_ALLOWED_RULESET_IDS`. |
| `evaluation_service.py:~896-909` | Include in the research arena-range validation. **Trap:** if omitted, E2 accepts any arena size without range checking. |
| `evaluation_cli.py:180` | Add to `--ruleset` choices, with help text marking it explicit-only research. |
| `evaluation_contracts.py` | Add `is_ruleset_v6_research_capture_hold_methodology`, a distinct arena-alignment label, inclusion in `is_ruleset_v4_derived_methodology` (identity and schema version 7), an `EvaluationRequest` property, and threading through `resolved_arena_alignment_mode`, `resolved_identity_version`, `resolved_schema_version` and `arena_alignment_mode_for_ruleset`. **Trap:** `resolved_arena_size` (`~880-887`) must include E2, or an omitted `--arena-size` silently resolves to `Config().arena_size = 4096` instead of 512. |
| `evaluation_artifact.py:~943`, `evaluation_planning.py:~328` | Thread the new predicate wherever the three existing research predicates are threaded. |

Option considered and **rejected**: widening `is_ruleset_v6_research_scale_methodology` from `==` to set membership, so that E2 shares research-scale's label. It would touch about three sites instead of ten, but it silently redefines a predicate documented as "True only for `bytefray-rules-6-research-scale`". The positional-boolean fan-out is a real maintainability cost; refactoring it belongs outside E2 (DEFERRED).

### E.3 Research tooling surface (not product)

- `tools/research/v6/e2/fixtures/agents/…`: the §G agents and their mirror twins.
- `tools/research/v6/e2/capture_analyzer.py`: telemetry derived from replays (§K).
- `tools/research/v6/e2/run_e2.py`: a thin runner over `experiment_harness.run_experiment`. It asserts that `scheduler_chunk_size`, `scheduler_rotate_start`, `kill_weight` and `instr_per_tick` are all `None`, so that "one field differs" is true of what actually runs.
- `tools/research/v6/experiment_harness.py`: fix the metric defects in §I.4.

### E.4 Explicitly **not** touched

`scheduler.py`, `placement.py`, `scoring.py`, `config.py`, `vm.py`, `statistics.py`, `telemetry.py`, `replay.py` (no schema change), `result_model.py`, all of `client/`, all of `app/` (Designer options stay V4-only), the `--ruleset` choices in `cli.py` / `agent_test.py` / `tournament_cli.py` (stay V4-only), `OMITTED_RULESET_CANDIDATES`, and `MatchRequest` (**no** per-match override field).

### E.5 Domain decisions for `capture_hold_ticks`

| Question | Decision |
|---|---|
| Type | `int`. `bool` is rejected explicitly, since it is a subclass of `int`. An ordinal count rather than an enum, so that K = 1 is literally V4 and a K = 3 arm needs no new code. |
| Valid range | `K ≥ 1`. No upper bound: `K > max_ticks` makes capture impossible, which is valid if pointless. A cap would be an unmotivated policy decision. |
| Default | `1`. Every existing policy object keeps its source and its value. `test_ruleset_policy.py:100` (research-scale equals V4 field for field) stays true. |
| Validation | `ValueError` from `__post_init__`, in the same style as the four existing fields (`ruleset_policy.py:142-166`). |
| Serialization | **None.** `RulesetPolicy` is never serialized; artifacts carry `ruleset_id`, and semantics are recovered through the finite registry. This places a permanent obligation on the E2 policy object: once artifacts exist, its fields must never change, and retiring it must keep it resolvable (as the retired movement-line policies currently are). |
| Canonical match identity | `ruleset_id` is already a first-class axis of `canonical_match_id` (`match_service.py:898`), so E2 and its control can never share a `match_id`. No new identity field is needed **as long as K is never a per-match override**. If one is ever added, it must be hashed like the scheduler override (`903-917`). Recommendation: never add it. |
| Replay | No change (§K). |
| Artifacts | No new fields. Evaluation artifacts gain only the new alignment label, and `rules_compatibility_id` is already hashed into `evaluation_id`. |
| Historical compatibility | Every V4 and research-scale artifact is byte-for-byte unaffected, because the K = 1 path is identical (§C.7). |
| Home object | `RulesetPolicy`. K is a gameplay semantic. It does not belong on `Config`, which holds per-match configuration and is not identity (`docs/RULES.md`); on `MatchRequest` (per-match overrides are the anti-pattern AGENTS.md names); on `ScoringPolicy` (not Ruleset-owned); or on termination, which stays alive-count based while capture feeds the alive count. A separate `CapturePolicy` object would be premature abstraction. |

---

## F. Ruleset Definition

**Proposed identity:** `bytefray-rules-6-research-capture-hold-k2`

- It follows the `bytefray-rules-6-research-<topic>` convention (`rules.py:109-113`), with topic `capture-hold`.
- The `-k2` suffix records the single varied value, so a possible K = 3 arm would be a sibling `-k3` without any renaming.
- It deliberately omits `scale`: the topic is not arena scaling, even though the parent policy is `research-scale`. The derivation is recorded in the policy comment, the same way 4C and 4D record theirs.

**Derived from:** `bytefray-rules-6-research-scale`, the current `ACTIVE_RESEARCH` control. The E2 object is an independent literal copy, never `dataclasses.replace(...)`, following the hidden-coupling rationale at `ruleset_policy.py:459-469`.

| Field | `bytefray-rules-4` (historical control) | `bytefray-rules-6-research-scale` (research control) | **E2 treatment** |
|---|---|---|---|
| `ruleset_id` | `bytefray-rules-4` | `bytefray-rules-6-research-scale` | `bytefray-rules-6-research-capture-hold-k2` |
| `supported_runtime_kinds` | `{python}` | `{python}` | `{python}` |
| `supported_python_api_versions` | `{2}` | `{2}` | `{2}` |
| `scheduler_mode` | `chunked` | `chunked` | `chunked` |
| `scheduler_chunk_size` | 2 | 2 | 2 |
| `scheduler_rotate_start` | True | True | True |
| `core_placement` | `seeded` | `seeded` | `seeded` |
| `process_selection` | `round_robin` | `round_robin` | `round_robin` |
| `movement_stride` | `fixed_64` | `fixed_64` | `fixed_64` |
| `movement_displacement` | `literal` | `literal` | `literal` |
| **`capture_hold_ticks`** | 1 (default) | 1 (default) | **2** |

**Exactly one gameplay field differs.** The evaluation methodology is inherited from the research control: variable arena, defaulting to 512 when omitted. The E2 matrix fixes the arena at 512 by configuration and does not reopen arena scaling.

**Lifecycle placement.**

- **In:** `ACTIVE_RESEARCH_RULESET_IDS`, `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `_CORE_PLACEMENT_GUARDED_RULESET_IDS`, the evaluation allow-list and the evaluation CLI choices.
- **Out:** `PUBLIC_STABLE_RULESET_IDS`, `OMITTED_RULESET_CANDIDATES`, the Designer options, and the `run` / `agents test` / tournament choices.

Explicit selection by name through `agents evaluate` or the Python API is the only way to reach it.

---

## G. Experimental Agent Set

### G.1 Principles

- Tracked research fixtures under `tools/research/v6/e2/fixtures/agents/`, added to the harness's `TRACKED_BENCHMARK_SOURCE_DIRS` (`experiment_harness.py:63-66`) and fingerprinted. They are never product starters.
- Agent API v2 only. They read only `ObservationV2` and `MatchContextV2`, import nothing from the engine, and stay short enough (well under 100 lines each) to be read at a glance.
- **Global reach (256) for every archetype.** Reach is free and visibility is reach-gated, so a local-reach agent is incompetent rather than strategically distinct. [PROBE] A reach-48 painter could not see a sniper 230 cells away, never disrupted it, and was captured by tick 2.
- **Honest information limits.** The enemy core base is not directly observable. Its only legitimate sources are (1) the first sighting of an enemy anchor while the enemy has a single location, which is always true for Seat A at tick 1 and true for Seat B at tick 2 only if the enemy stayed home, and (2) `READ`, which returns the owner. Agents use (1). The analyzer checks every agent's inferred core base against ground truth from the replay, so an information failure is **measured, not silent**.
- **Seed sensitivity is deliberate.** [PROBE] A deterministic global agent gives **1 distinct trajectory across 32 seeds**, because placement cannot matter when reach covers the whole arena. Spread and paint agents draw their offsets and direction from `context.rng`, so seeds are genuine trials for them. The deterministic agents stay deterministic because their placement-invariance is itself a characterization; the analysis counts distinct trajectories, not seeds (§I.4, HD-2).

### G.2 Agents

| ID | Archetype | Behavior per tick | Hypothesis it discriminates |
|---|---|---|---|
| `v4_probe` | Existing exploit probe | An exact copy of `CompetentGlobalSniperProbe`'s logic: write `anchor[0] + step`, where `step` cycles 0–7. | Continuity with the V4 gate; H0 for non-defending play |
| `e2_sniper` | 1. Global Sniper | Write each visible enemy anchor once, then every enemy core cell not yet written this tick. Never repairs. | Does E2 break the forced line? When seated B, it doubles as the naive counterattacker. |
| `e2_repair_guard` | 2a. Core Guard (pure) | Rewrite its own core cells, cycling. Never disrupts. | Nominal window (§D.4); H0 control for defense |
| `e2_disrupt_guard` | 2b. Core Guard (disrupt-first) | Write each visible enemy anchor, then repair its own core. | Canonical H1 defender (§D.5); H3a/H3b |
| `e2_min_guard` | 2c. Minimal Guard | Disrupt anchors, repair **exactly one** cell, attack the enemy core with the rest. | Is a one-cell reclaim too cheap? Cost-minimal defense |
| `e2_greedy_painter` | 3a. Pressure / Painter | Paint outward from its own core. Never disrupts or repairs. | Opportunity-cost pole (H2) |
| `e2_guarded_painter` | 3b. Guarded Painter | Disrupt anchors, repair one cell, paint the rest. | H2 tradeoff; the observed mirror inversion (H3c) |
| `e2_counter` | 4. Counterattack | Paints until it detects it was attacked, then switches permanently to sniper mode and never repairs. Detection: its single process gets no callback on the previous tick (`last_callback_tick < current_tick - 1`). | Races and mutual threats; new seat pathologies |
| `e2_spread_sniper` | 1'. Multi-location attacker | Three processes. Tick 1: disrupt, two `MOVE`s with offsets drawn from `context.rng` in ±[16, 64], then attack. Afterwards: disrupt every visible anchor, then attack. | Location count closing the window (§D.6); H0 for sophisticated attack; H3e |
| `e2_spread_defender` | 2'. Multi-location defender | Three processes: `MOVE` first (rng offsets), then disrupt, repair one cell, attack. | Is spreading the dominant response (H3d)? |

**Mirror twins.** Each agent has a `*_twin` fixture with identical logic and a distinct name. This gives the triangular harness true mirror cells, which the probe mirror used by the characterization gate requires.

---

## H. Hypotheses (refined, with operational evidence)

The criteria below are **pre-registered**. They must not be re-tuned against E2 outcomes. The [PROBE] priors are recorded here only to make the predictions falsifiable, not to set thresholds.

Definitions used below:

- **Seat-determination index (SDI).** For an ordered pair and seed: 1 if the Seat-A entrant wins in both orientations, or the Seat-B entrant wins in both; otherwise 0. The pair's SDI is the mean over its distinct trajectories.
- **Mirror seat bias.** Seat-A win rate minus Seat-B win rate in a mirror cell.
- **Recovery rate.** Recoveries divided by onsets.
- **Phase-lock.** The share of an entrant's zero-core ticks that fall on the opponent's first-mover ticks.

| ID | Statement | Supporting evidence | Refuting evidence | [PROBE] prior |
|---|---|---|---|---|
| **H0** Delay only | E2 turns a tick-1 forced kill into a tick-2 forced kill with no new interaction. | V4 decisive cells keep their winner in ≥ 90% of cases, with decision tick +1; SDI and mirror seat bias unchanged; recovery rate ≈ 0 for every defender. | Any defender that survives the sniper in the orientation it lost under V4. | **Holds** for the probe mirror, the sniper mirror and the pure repair guard. **Fails** for disrupt-first defenders. |
| **H1** Defense becomes viable | A defender can reclaim ≥ 1 cell and reset progress. | Recovery rate > 0 followed by survival; a V4-lost orientation becomes a tie or win. | Recovery rate ≈ 0 against the sniper for every defender. | **Supported**, but survival yields **draws**, not wins. |
| **H2** Genuine tradeoff | Defense prevents death but costs offense or territory, producing opponent-dependent results. | Seat-conditioned residuals significantly nonzero, tested against distinct-trajectory counts; at least one pair where defending loses on score to a non-attacker while that non-attacker loses to the attacker. | Residuals within noise after seat conditioning; a single transitive order explains every seat-conditioned table. | **Weakly suggested**: Sniper > Greedy Painter > Spread Defender ≈ Sniper (tie edge). |
| **H3a** Perpetual repair stalemate | Matches end at the tick limit with continual recovery. | Tick-limit share rises versus control; ≥ 1 recovery per 2 ticks in those matches. | — | **Present**: ties 62 → 102 of 324. |
| **H3b** Phase-locked alternation | Zero-core ticks lock to scheduler parity. | Phase-lock ≥ 0.95 in stalemated matches. | Phase-lock near 0.5. | **Present**: 150/150 zero ticks on attacker-first ticks. |
| **H3c** New deterministic seat inversion | E2 creates or flips seat determination. | A mirror or pair with SDI ≥ 0.9 under E2 where V4 SDI < 0.9, or where the favoured seat flips. | — | **Present**: Guarded Painter mirror, V4 A 27 / B 5 → E2 B 32/32. |
| **H3d** Dominant always-defend | One defender never loses in either seat, mostly by drawing. | 0 losses and tie rate ≥ 50% across all opponents and seats. | — | **Candidate**: `e2_spread_defender` was never beaten by the probe's attackers, but loses to painters on score. |
| **H3e** Location-count arms race | Outcomes are decided by the number of process locations. | Multi-location agents beat every stacked agent regardless of other behavior. | — | **Present** against stacked defenders. |
| **H3f** Zero-core winners | Decisive wins by an entrant at zero core. | Share of decisive wins with the winner capture-threatened. | — | **Present**: probe mirror. |
| **H3g** Capture never resolves | Many onsets, no completions. | Matches with ≥ 10 onsets and 0 completions. | — | Same as H3a. |

**Negative-result rule (reachable ABANDON).** Suppose H0 or H3a–d explain the E2 matrix and H2 is unsupported after seat conditioning. Then E2 is recorded as a **clean negative result**: K = 2 alone does not create strategic interaction under otherwise-V4 rules. The E2 line closes and **no mechanic is added inside E2**. Any follow-up is a separately registered single-variable study (§L.3 lists candidates, but does not recommend one).

---

## I. Experiment Matrix

### I.1 Conditions

| Condition | Ruleset | Arena | Role |
|---|---|---|---|
| **C-V4** | `bytefray-rules-4` | 512 | Historical control. It is frozen and known to be exploit-bearing. |
| **C-RS** | `bytefray-rules-6-research-scale` | 512 | Structural control and E2's direct parent. It must be **cell-for-cell identical** to C-V4, in the same way Phase 4D's 448/448 equivalence check worked. Any mismatch **halts** analysis. |
| **T-E2** | `bytefray-rules-6-research-capture-hold-k2` | 512 | Treatment. |

- **No K = 3 arm in the first run.** The probe grid gave identical outcome columns for K = 2 and K = 3 (§D.8). K = 3 stays a registered secondary question, run only if T-E2 shows onset-parity effects (§L.2).
- Common settings: seeds `1..32` (the harness defaults to the eight `STANDARD_V4_SEEDS`, so 32 must be passed explicitly), both orientations, 1000 ticks (the V6 standard), and all four request overrides (scheduler ×2, `kill_weight`, `instr_per_tick`) **asserted `None`**.

### I.2 Fields

| Field | Composition | Cells per condition |
|---|---|---|
| **F1 (primary)** | The 10 §G agents, triangular round robin: 45 pairs × 32 seeds × 2 orientations | 2,880 |
| **F2 (mirrors)** | Each §G agent against its twin: 10 pairs × 32 × 2 | 640 |
| **F3 (secondary reference)** | {`v4_probe`, `e2_sniper`, `e2_disrupt_guard`, `e2_spread_defender`, `e2_guarded_painter`} × {`Octave`, `nemesis_alpha2`, `v5_core_defender`, `v4_claimer`, `v5_scout_striker`}, cross pairs only: 25 × 32 × 2 | 1,600 |

That is 5,120 matches per condition and **15,360 in total**. F3 is reported separately and **never** pooled into F1 ratings, because V6-Bench-8 was built around suboptimal V4 assumptions.

### I.3 Metrics (every rate reported with `n_distinct` alongside it)

**Outcome**

- Decisive wins, losses and ties per ordered pair.
- Seat-conditioned win rates `P(win | Seat A)` and `P(win | Seat B)`.
- **SDI** and **mirror seat bias** (§H).
- A V4 → E2 outcome transition matrix per cell, over {A-win, B-win, tie}.
- Decision-tick distribution (median, IQR) for **decisive matches only**, reported separately from tick-limit matches.
- Match termination reason, and entrant termination (`core_captured` / `forfeit`).

**Capture telemetry** (derived from replays, §K)

- Per entrant: onsets, recoveries, completions, zero-core ticks, maximum streak, and the tick of the first onset.
- Phase-lock (the parity of zero-core ticks relative to the first mover).
- Whether the winner was at zero core at match end.
- Whether kill attribution was present at completion. This must be true for every E2 capture; it validates §C.5.
- Whether each agent's inferred enemy core base was correct.

**Ratings** (computed seat-pooled for comparability with earlier phases, **and** separately for the Seat-A and Seat-B tables)

- Bradley-Terry strengths with a convergence criterion.
- Residuals `R_ij` and RMSR.
- Upsets.
- Directed 3-cycles, each listed with its edge margins. A cycle with any edge within ±0.05 of 0.5 is flagged fragile.

**Effective sample size.** Distinct trajectories per ordered pair, deduplicated on (winner, ticks, reason, final scores). Bootstraps resample distinct trajectories, not seeds.

### I.4 Harness defects to fix before interpreting E2 (verified independently, not taken from a prior report)

| ID | Severity | Defect | Evidence | Required fix |
|---|---|---|---|---|
| HD-1 | **HIGH** for E2 | `_seed_aggregated_winrate` (`experiment_harness.py:361-374`) averages both orientations inside each seed, and `analyze_experiment_condition` (`587-618`) never surfaces `seat_a_wins` / `seat_b_wins`. The headline metrics are blind to seat determination, which is the exact pathology E2 targets. | [RUN] Synthetic field where Seat A wins every match, fed through the real functions: ratings all **1500.0**, RMSR **0.0**, cycles **0**, the signature of a perfectly balanced field. | Add seat-conditioned tables, SDI and mirror seat bias to the analysis output. |
| HD-2 | MEDIUM | Seeds are treated as independent. `n_eff = #seeds` (`408`), so duplicate trajectories inflate confidence. | [RUN] `bootstrap_rmsr_over_seeds` returns SE **0.0** for 32 duplicate seeds. [PROBE] Deterministic global agents give 1 distinct trajectory per 32 seeds. | Count `n_distinct`; bootstrap over distinct trajectories. |
| HD-3 | MEDIUM | Bradley-Terry runs a fixed 50 iterations with no convergence check (`377-436`). | [RUN] Transitive blowout: rating of G = 945.9, 580.2 and 410.6 at 50, 500 and 5000 iterations. | Tolerance-based stop; report the iteration count and a convergence flag; treat ratings on near-separable data as bounds. |
| HD-4 | MEDIUM | The triangular round robin (`205-209`) has no mirror cells. | [SOURCE] | Add a twin-based mirror condition (F2). |
| HD-5 | MEDIUM | No capture telemetry at all. | [SOURCE] | Add the replay-derived analyzer (§K). |
| HD-6 | LOW | `median_decision_tick` pools tick-limit cells (`601-602`). | [SOURCE] | Report the decisive-only median separately. |
| HD-7 | LOW | The tracked fixture directories (`63-66`) do not cover an E2 fixture directory. | [SOURCE] | Add the directory. |

### I.5 Interpretation rules (pre-registered)

1. No single threshold crossing (cycle, residual or win rate) counts as evidence on its own.
2. A structural claim needs support in the Seat-A table **and** the Seat-B table, consistency between F1 and F2, and `n_distinct ≥ 8` for any rate claim. Deterministic pairs are reported as characterizations, not rates.
3. A mismatch between C-RS and C-V4 halts the analysis.
4. The [PROBE] priors in this report are predictions to be falsified. They must never be used as thresholds.

---

## J. Test Plan

### J.1 Preserving V4 (must pass without editing any existing expectation)

- `test_v4_exploit_characterization.py` stays unchanged and green: winner A, tick 1, `last_agent_standing`, in both orientations.
- `test_v4_stable_ruleset_equivalence.py` and `test_v4_historical_immutability.py` frozen goldens stay unchanged and green.
- `test_ruleset_policy.py:100` (research-scale equals V4 except `ruleset_id`) stays green. `capture_hold_ticks` defaults to 1 on both.
- **New:** a K = 1 byte-identity test. Replay and result digests for a small fixed V4 matrix (for example the probe mirror plus two starter pairs, seeds 1–3), frozen **before** the capture change and asserted identical after it.

### J.2 Policy and identity tests

| Test | Assertion |
|---|---|
| Field default | Every registered policy has `capture_hold_ticks == 1`, except E2, which has 2. |
| Validation | `0`, `-1`, `True`, `2.0` and `"2"` all raise `ValueError`. `1` and `2` are accepted. |
| One-field difference | `replace(E2, ruleset_id=RS.ruleset_id, capture_hold_ticks=RS.capture_hold_ticks) == RULESET_V6_RESEARCH_SCALE` |
| Identity separation | The same `MatchRequest` under RS and under E2 produces a different `match_id`. |
| Lifecycle partition | Every `_RULESET_POLICIES` key is in **exactly one** of PUBLIC_STABLE, ACTIVE_RESEARCH and RETIRED_RESEARCH. E2 is in ACTIVE_RESEARCH. |
| No product exposure | E2 is absent from `OMITTED_RULESET_CANDIDATES`, the Designer option tuples, and the `--ruleset` choices of `run`, `agents test` and `tournament`. It is present in the `agents evaluate` choices. |
| Omitted resolution | An Agent API v2 roster with no `--ruleset` still resolves to `bytefray-rules-4`. |
| Evaluation plumbing | With E2 and no `--arena-size`, the resolved arena is **512** (not 4096). Arena 63 or 65537 is rejected. E2's alignment label is distinct from RS's and V4's. Identity and schema version are 7. |
| Core placement guard | Overlapping cores under E2 raise `OverlappingCoreError`. |

### J.3 E2 semantic tests

These use scripted entrants on a directly constructed `ProcessMatchController` with the E2 policy. Each asserts an exact per-tick sequence taken from a real run, not a count.

| Test | Scenario | Exact assertion |
|---|---|---|
| First zero tick | Attacker zeroes the victim at T = 1 | End of T: victim alive, `core_zero_streak == 1`, no kill/death event, victim received the tick-1 alive score. |
| Recovery with 1 cell | Victim rewrites exactly one core cell at T+1 | Streak 0, onset cleared, alive. |
| Recovery with a partial core / full core | 4 cells / 8 cells | Same as the one-cell case: any ≥ 1 resets. |
| Completion | Still zero at T+1 | Dies at the end of T+1. `entrant_termination == "core_captured"`. **Kill event `by` = onset capturer, +5 to the capturer, `statistics.kills == 1`.** No alive score for T+1. |
| No leakage across cycles | Board ownership pattern 0, +, 0, +, 0, 0 | Capture only at the 6th evaluation. The streak never exceeds 1 before it. |
| Intra-tick transit | Core hits zero mid-tick and is repaired before tick end | Streak stays 0; no onset. |
| Simultaneous completion | Both at streak 1 and both still zero | Both dead, `all_agents_dead`, winner `tie`, events in seat order. The **same result with seats swapped**. |
| Staggered completion | A completes while B only reaches streak 1 | A dead, B wins `last_agent_standing`, B's core is 0/8. |
| Forfeit during a streak | Victim at streak 1 raises in `act` at T+1 | `forfeit`, no kill credit, no capture event. |
| Opponent forfeits while self is at streak 1 and zero at T+1 | | `all_agents_dead` / `tie`. |
| Tick limit at streak 1 | `max_ticks = T+0` after an onset | Survives; winner decided on score. |
| K = 1 attribution | V4 policy | Kill attribution is identical to the pre-change function on the D.2 trace. |

### J.4 E2 mechanic characterizations

Seed 42, arena 512, scripted. These pin mechanics, not desired outcomes. They are the §D traces as frozen tick-level expectations:

- **D.3, probe mirror:** A wins at tick 2; A ends at 0/8 with streak 1; B's 8 tick-1 slots are forfeited, and so are A's 8 tick-2 slots.
- **D.4, sniper vs repair guard:** B's two tick-2 writes at 203 and 204 are overwritten, and B is captured at tick 2.
- **D.5, sniper vs disrupt guard:** alternation holds for at least 6 ticks, with B's zero-core ticks exactly the odd ticks.
- **D.6, spread sniper vs disrupt guard:** B's onset at tick 2 and capture at tick 3.

### J.5 Determinism and serialization

- The same E2 request run twice gives byte-identical canonical replays and the same `result_id`.
- The replay reader accepts every E2 replay: there are no new event types (`replay.py:359` would reject one).
- No new fields exist in replay or result. Canonical replays are already LF-only (`replay.py:676-680`, `newline="\n"`). Run the E2 determinism test on both Windows and Linux CI legs.

---

## K. Replay and Artifact Implications

| Artifact | Change | Rationale |
|---|---|---|
| Replay schema 4 | **None.** No new event type and no new snapshot field. | The reader raises `unsupported event type` for anything unknown (`replay.py:359`). A `capture_threat` event would make E2 replays unreadable to every current reader, the replay viewer and the spectator derivation, unless the schema is bumped. It would also leave a permanent product-schema expansion behind a research question. |
| Replay events | Unchanged vocabulary. The capture completion still emits `kill` or `death`, now correctly attributed (§C.5). | — |
| `result.json` | No shape change. Entrant `termination_reason` stays `core_captured` or `forfeit`; `statistics.kills` is still credited. | `result_id` stays well-defined; V4 results are byte-identical. |
| Evaluation artifacts | A new arena-alignment label for E2. `rules_compatibility_id` is already hashed. | Precedent from 4B, 4C and 4D. |
| **Capture progress** | **Derived, not persisted.** A research analyzer rebuilds per-tick ownership from the tick-0 seeding diffs plus every tick's `memory_diffs`, which record owner per write. It locates each core from the entrant's recorded `region` / `pc` (both equal the core base) and reads K by resolving the replay's recorded `ruleset_id` through the registry. | Exact and deterministic, with zero schema cost. The only precondition is the §E.5 immutability obligation on the E2 policy object. |
| Research-only telemetry | Onsets, recoveries, completions, streaks, phase-lock and zero-core winners, written by the analyzer into E2 experiment JSON under `runs/`. | Experiment output, not a product artifact. |
| Client core status | Unchanged. `replay_status._core_status` shows core integrity only for `VULNERABLE_CORE_RULESET_IDS`, which contains neither V4 nor E2. | No Designer or viewer exposure. |

**Backward readability.** Every existing artifact reads exactly as before. E2 artifacts are ordinary schema-4 replays and result v2 envelopes carrying a new `ruleset_id` string. A reader that does not recognize the ID still parses them, because recognition of a Ruleset is separate from parsing.

---

## L. Adversarial Findings

### L.1 Answers to the adversarial questions

| Question | Finding |
|---|---|
| Does K = 2 solve the cause or mask it? | **It masks one symptom.** The causal chain has ten links; E2 changes only the last one (zero ownership is immediately fatal). The rest persist, and Seat A's uncontested tick 1 re-emerges as a location-count lead (§D.6) or as phase-locked alternation (§D.5). E2 is still a clean test of whether that last link is load-bearing for seat determination. The prior answer is "partly": forced wins become draws, but defenders gain no wins. |
| Does scheduler rotation become the dominant mechanic? | **Partly, yes.** The entire defense window is supplied by rotation plus D = 1 (§D.7), and stalemates are phase-locked to rotation parity (H3b). K = 2 coincides with the rotation period for two entrants. Under a non-rotating scheduler, E2 would give Seat B no window at all. |
| Can Seat B trivially counterattack into a new deterministic inversion? | **Not by naive counterattack**: the probe's counter dies first, because it cannot repair and attack in the same tick and the attacker's streak started one tick later (§D.3). **A new inversion does appear** in a non-attacking mirror: the Guarded Painter goes to Seat B 32/32 (H3c). |
| Does a one-cell reclaim make defense too cheap? | The reclaim costs one action but is never sufficient alone. The costly part is disruption. Against a single-location attacker, a full defense cycle costs about 2 actions every 2 ticks, and the attacker's re-zeroing costs about the same, so both sides have about 6 actions per tick spare. That produces stalemates settled by territory score. **GAMEPLAY FINDING**, not a defect. |
| Does constant repair create infinite stalemate? | **Yes**, against single-location attackers (§D.5; ties 62 → 102). |
| Should progress reset fully or decrement? | Irrelevant at K = 2: the two rules are provably identical (§C.3). It becomes a real second variable only at K ≥ 3. |
| Does global reach remain obviously dominant? | **Yes.** Every competent E2 behavior needs visibility to disrupt, and visibility is reach-gated with reach free. E2 does not touch this link, by design. |
| Is defending meaningful if the opponent can erase it every tick? | The attacker can erase only on **its own** first-mover ticks. On the others, the disrupt-first defender disables it. Defense therefore means "keep the streak below K", not "keep the core". The defended state is the alternation. |
| Does E2 need another mechanic before meaningful counterplay? | **Not decided here.** The prior suggests counterplay mostly appears as draws and location races, with weak H2 evidence. The E2 matrix exists to settle this. Adding a mechanic in anticipation would make the thesis true by construction. |
| Could a simpler semantic give a cleaner experiment? | See §L.3. None is simpler **and** general. K = 2 remains the minimal general form of "a response window before capture is final". |

### L.2 Theoretical onset-parity exposure (recorded, not acted on)

K = 2 gives the victim a **first-mover** follow-up tick only when the onset falls on an attacker-first tick. An attacker that times its onset to the victim's own first-mover tick leaves the victim moving second at T+1 (§D.6). K = 3 would guarantee one victim-first tick inside every hold window in a two-entrant match.

In the probe this exposure was **dominated by location count**: every case where parity mattered also involved three or more attacker locations, and K = 3 changed no outcome. This is a secondary question for the E2 analysis (the "tick of first onset and parity" metric). It justifies a `-k3` sibling **only** if T-E2 shows parity-driven outcomes.

### L.3 Alternative semantics considered and rejected for E2

| Alternative | Reason for rejection |
|---|---|
| Seat-B tick-1 immunity | A seat-specific rule that reintroduces seat semantics and does not generalize. |
| K counted in the **victim's first-mover ticks** | Guarantees a first-mover response regardless of parity, but couples scheduler state into capture semantics, making two mechanics. Candidate follow-up only if L.2 materializes. |
| Recovery requires restoring more than one cell | A second variable, the recovery threshold. |
| Decrement instead of reset | Identical at K = 2. |
| Capture-threatened entrant loses at the tick limit | A second mechanic (C.6). |
| Spawn dispersion, reach cost, or a disruption cap | Each targets a **different** link of the causal chain. They are separate single-variable experiments, not E2. |

### L.4 Findings register

| ID | Class | Finding | Disposition |
|---|---|---|---|
| F-1 | **HIGH** (design correctness) | The naive K = 2 change makes every capture unattributed, losing the +5 kill score, the evaluation `killer` and the viewer's killer. | Resolved by onset attribution (§C.5). Mandatory. |
| F-2 | **HIGH** (methodology) | The harness headline metrics are blind to seat determination (HD-1). | Fix before interpreting the E2 matrix. |
| F-3 | MEDIUM | Duplicate-seed inflation (HD-2), Bradley-Terry non-convergence (HD-3), no mirrors (HD-4), no capture telemetry (HD-5). | Fix before the matrix. |
| F-4 | MEDIUM (trap) | If E2 is left out of `resolved_arena_size`, an omitted arena silently runs at **4096**. If left out of the range check, arena validation disappears. | Mandatory evaluation tests (§J.2). |
| F-5 | GAMEPLAY FINDING | The probe mirror stays 100% Seat A, at tick 2. | Prior for H0. |
| F-6 | GAMEPLAY FINDING | Phase-locked alternation stalemates; ties +40 of 324 in the probe grid. | Prior for H3a and H3b. |
| F-7 | GAMEPLAY FINDING | The Guarded Painter mirror inverts to Seat B 32/32, robust to the tick limit (299, 300, 301, 1000, 1001). | Prior for H3c. |
| F-8 | GAMEPLAY FINDING | Attacker location count closes the window; Seat A's tick-1 tempo persists. | Prior for H3e. |
| F-9 | GAMEPLAY FINDING | Zero-core winners become reachable. | Measured, not ruled on (§C.6). |
| F-10 | GAMEPLAY FINDING (V4 baseline) | Under **V4**, when Seat A does not kill on tick 1, **Seat B** can kill on tick 2 (for example Disrupt-Guard(A) vs Sniper(B), or Guarded Painter(A) vs Sniper(B)). The V4 pathology is "whoever lands the first disrupting write on a stacked opponent wins", not literally "Seat A". The gate is correct for mirrored competent play. | Context for interpreting the V4 control. No action. |
| F-11 | LOW / DEFERRED | The lifecycle sets are unconsumed; "retired" IDs remain executable; `HISTORICAL_READONLY_RULESET_IDS` omits `bytefray-rules-1`. | A partition test (§J.2) makes the sets load-bearing for E2. The rest is deferred. |
| F-12 | LOW (docs) | ROADMAP line 202 presupposes E2's outcome ("to eliminate … restoring …"). | Reword as a question when E2 is registered. |
| F-13 | DEFERRED | Positional-boolean fan-out in the evaluation methodology code. | Out of E2 scope. |
| F-14 | NOT ACTIONABLE | K = 2 vs K = 3 parity (§L.2). | A secondary analysis question only. |

---

## M. Implementation Recommendation

**Verdict: E2 is isolated enough and ready for implementation, under the refined semantics of §C.** The one-line semantic as originally stated is **not** ready to implement literally.

Why "ready" and not "needs refinement":

- The refinements are fully specified here and leave no decision open: onset attribution, two-phase simultaneous evaluation, reset on ≥ 1, no new rules for zero-core survivors, and derived rather than persisted telemetry.
- They keep the treatment to **one policy field** whose K = 1 value is provably, and must be tested as, byte-identical to V4.
- The identity story is clean: a distinct `ruleset_id` already separates `match_id`, and no per-match override is added.

Why not "does not isolate the intended variable":

- E2 does isolate the fatality-timing variable.
- The response window it opens is supplied by **held-constant** mechanics: rotation, D = 1 and co-located spawn. That is a property to **measure and attribute correctly**, not a confound, provided the analysis reports seat-conditioned outcomes and phase-lock rather than pooled ratings.

What the probe predicts, to be tested and not assumed:

- A **mixed result that leans negative**: H1 holds narrowly (draws, not wins), H0 holds for non-defending play, and H3a, H3b, H3c and H3e are present, while H2 is weak.
- The experiment remains informative whichever way it resolves. A clean confirmation that "K = 2 converts forced wins into scheduler-locked draws" is a valuable negative result that closes this line honestly.

**Preconditions for running (not for implementing) the matrix:** HD-1 through HD-5 are fixed, the C-RS ≡ C-V4 gate passes, and the §H hypotheses and §I.5 rules are frozen before T-E2 data is seen.

---

## N. Implementation Handoff (for a coding agent)

**Scope:** implement the E2 research Ruleset and its tests. **Do not** run the experiment matrix, change any stable-V4 expectation, add a replay event or field, add a `MatchRequest` or `EvaluationRequest` override, or expose E2 on any product surface. Commit only when instructed.

1. **Freeze first.** Before touching the capture code, record replay and result digests for a small V4 matrix (J.1, K = 1 byte-identity) and commit them as a frozen fixture only when instructed.
2. **Policy.** In `ruleset_policy.py`:
   - add `capture_hold_ticks: int = 1` to `RulesetPolicy`;
   - validate it in `__post_init__` (int and not bool, ≥ 1, `ValueError`);
   - add `RULESET_V6_RESEARCH_CAPTURE_HOLD_K2`, a literal copy of `RULESET_V6_RESEARCH_SCALE`'s fields plus `capture_hold_ticks=2`, with a provenance comment naming this report;
   - register it in `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS` and `__all__`.
3. **Identity.** In `rules.py`: `BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID = "bytefray-rules-6-research-capture-hold-k2"`, with a docstring comment and an `__all__` entry.
4. **Runtime.**
   - `python_runtime.apply_core_capture` gains the keyword `hold_ticks: int = 1` and becomes two-phase with streak and onset attribution, exactly as in §C.2. `_attribute_core_capture` stays unchanged.
   - `process_runtime.EntrantState` gains `core_zero_streak: int = 0` and `core_zero_onset_capturer: str | None = None`.
   - The call at `process_runtime.py:1276` passes `hold_ticks=self.ruleset_policy.capture_hold_ticks`.
   - Add **no** `ruleset_id` comparisons.
5. **Match service.** Add the ID to `_CORE_PLACEMENT_GUARDED_RULESET_IDS`.
6. **Evaluation plumbing (4C/4D precedent).**
   - `evaluation_contracts.py`: predicate, `EvaluationRequest` property, distinct alignment label, inclusion in `is_ruleset_v4_derived_methodology`, **inclusion in `resolved_arena_size`** (trap F-4), and threading through `resolved_arena_alignment_mode`, `resolved_identity_version`, `resolved_schema_version` and `arena_alignment_mode_for_ruleset`.
   - `evaluation_service.py`: the allow-list at line 112 and **the research arena-range check** (about lines 896–909).
   - `evaluation_cli.py:180`: choices and help text.
   - `evaluation_artifact.py` and `evaluation_planning.py`: threading.
7. **Tests:** everything in §J.1–J.5.
   - New modules: `engine/tests/test_ruleset_v6_research_capture_hold.py` (policy, identity, plumbing) and `engine/tests/test_e2_capture_hold_semantics.py` (J.3 and J.4, with scripted entrants on `ProcessMatchController`).
   - Assertions compare whole per-tick sequences by value. Presence-only assertions are not accepted.
8. **Docs.**
   - Add a registration note under `docs/research/v6/` that points to this review.
   - Reword `docs/ROADMAP.md:21,202` and `docs/FUTURE_PLANS.md:312-314` as a question rather than a promised outcome.
   - Do **not** edit historical reports.
9. **Validation, reported with exact counts:** the focused modules first, then `python -m pytest` (the full configured suite, not only `engine/tests`), `mypy engine/src/battle_engine`, `mypy client/src/battle_client`, and `ruff check .`.
10. **Acceptance:**
    - the V4 characterization gate and every frozen V4 golden pass unedited;
    - the K = 1 byte-identity test passes;
    - the J.3 and J.4 E2 sequences pass;
    - E2 is unreachable from `run`, `agents test`, tournament and the Designer;
    - an omitted `--arena-size` under E2 resolves to 512.

A separate follow-up task, **not** part of this handoff, covers the research tooling: §G fixtures, the §K analyzer, harness fixes HD-1 to HD-7, and the §I matrix run.

---

## Appendix P. The design probe (how to rebuild it)

The probe is a scratch Python module, **not** in the repository. It does four things:

1. It builds `ProcessMatchController(Config(seed, 512, 8), [specA, specB], max_ticks, ruleset_policy=RULESET_V4)` directly from `ProcessEntrantSpec` and `ProcessInstance` objects, whose `logic` callables share one brain dictionary per entrant. Starts come from `resolve_direct_match_starts(ruleset_id="bytefray-rules-4", arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=seed)`.
2. For the treatment arms it rebinds `battle_engine.process_runtime.apply_core_capture` to a callable implementing §C.2 with K ∈ {1, 2, 3}. It restores the stock function afterwards.
3. It subclasses `_select_active_process` to log forfeited slots, and wraps `run_scheduler` to log the first mover of each tick.
4. **Validity check:** the prototype at K = 1 reproduced stock V4 (winner, ticks, reason, score) for the probe mirror on seeds 1–32.

**Agent brains:**

- **Sniper:** write each visible anchor once per tick, then unwritten enemy core cells.
- **Pure guard:** own core cells, cycling.
- **Disrupt guard:** anchors, then own core.
- **Minimal guard:** anchors, one own cell, then the enemy core.
- **Spread sniper and spread defenders:** three or five processes, with fixed ±40 / ±20 `MOVE` offsets. The "spread-first" variants move before disrupting.
- **Painters:** global reach, painting outward and alternating sides of their own core. The guarded variants disrupt first and repair one cell.

The probe offsets were fixed rather than rng-drawn. That is one reason the deterministic agents produce a single trajectory per pair.
