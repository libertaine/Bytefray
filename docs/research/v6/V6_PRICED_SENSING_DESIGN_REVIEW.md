# Bytefray V6 Branch B — Priced Sensing: Design and Adversarial Review

**Status:** Design and adversarial review only. No implementation, Ruleset, pre-registration, gameplay probe or matrix. No match was run. Nothing is registered.
**Revision:** This version incorporates the research lead's corrections and decisions of 2026-09-25, made before commit: a seed-blindness protocol (§E.2), an initial-state invisibility gate in place of a first-callback gate (§J), a design-count gate in place of a pre-treatment n_distinct gate (§K.1), traces for control and treatment cells (§C.4), and STEALTH as a required eighth member (§I). §M records the decisions.
**Branch:** `v6-research` at `da39f2d`, the Branch B scope boundary. The tracked tree was clean before this review, and this file is its only change.
**Date:** 2026-09-25
**Governing records:**
- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) (the scope review, **SR**);
- the research lead's scope decisions of 2026-09-25, restated in §A.2 because they are not yet in a committed record;
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md), §G requirements.

**Evidence tiers.**

| Tier | Meaning |
|---|---|
| [SOURCE] | Current source at `da39f2d`, cited by file and line. |
| [DOC] | A committed research record. |
| [GEOM] | Direct calls to the pure placement and seed-derivation functions (`placement.seeded_seat_starts`, `python_runtime.derive_agent_seed`). No controller, agent or match was constructed, and no gameplay outcome exists. Appendix G gives the calls and outputs. |
| [ARITH] | Arithmetic on source constants, checked by script (Appendix G). |
| [TRACE] | A hand trace of source semantics for a hypothetical policy pair. It was not executed, and it is not a result. |
| [INFERENCE] | Reasoning from the tiers above. |

**No outcome probe was run, by the research lead's decision.** The semantics and the radius are chosen from source and geometry alone.

---

## Verdict in brief

**GO WITH CONDITIONS.** Priced sensing survives source-level challenge as a mechanism that *can* create opponent-dependent choices. But the review predicts two specific ways it could collapse, and it finds one bypass that must be closed before any claim can be tested.

**The mechanic, resolved to source semantics.**
- Each process sees an enemy anchor exactly when the circular distance is **at most min(its declared reach, *d*)**. The comparison is inclusive.
- Everything else about visibility is unchanged: when it is computed, which processes can sense, the entrant-wide sharing, which targets count, the output format.
- *d* = **32**, derived from geometry alone (§D).
- The rule is a pure restriction. In every game state, the treatment shows a subset of what the parent would show (§C.2).

**Findings, most serious first.**

1. **A zero-action bypass exists through seed inference.** [GEOM] Agents receive a seed derived from the match seed, and seeded placement is a public, importable function of the match seed.
   - **Route 1:** inverting the derived seed by enumeration recovered the match seed from 100,000 candidates in 0.37 s.
   - **Route 2:** on seeds 1–32, the range used throughout E2–E5, an agent's *own core base alone* pins the enemy core in 54 of 64 (seed, seat) cases.

   Either route bypasses priced sensing entirely. It can be closed by methodology, with a seed-blindness protocol and an agent-discipline gate. A product-level closure would need a placement change, so it is deferred (§E.2).
2. **The price is small and front-loaded.** [ARITH] A maximum-stride sweep finds an on-core enemy anchor within at most 7 MOVEs, and 1537/385 ≈ 3.99 on average: less than one tick of budget. The choice window is the opening exchange, plus any later re-finding of anchors that move (§G).
3. **The source predicts a search tax against stationary defenders.** [TRACE] Under the parent's whole-tick disruption, a fast searcher captures a stationary on-core defender at its own first first-mover tick after discovery: tick 2 or tick 3. That is the forced line, 1–2 ticks late (§H.2, T1). Kill criterion 4 as the scope review wrote it would therefore fire trivially, and must be rescoped (§K.2).
4. **Evasion is the most promising source of real choice, and its likely failure is stalling.** [TRACE] A defender that moves its anchor off its core makes a disruption plus a full core sweep cost 9 actions against a budget of 8. That is E5's cost, now *chosen* by the defender for one MOVE. The trace then settles into an E2-style alternation and a tick-limit draw (§H.2, T2).
5. **At least five decision points exist at source level, each opponent-dependent** (§H.3):
   - search pace;
   - search mode (movement or reading);
   - staying on the core or evading;
   - searching or painting;
   - splitting sensor and striker across two processes.

   Whether any policy other than search-first is a *best response* is empirical. That is the centerpiece question, and this review does not settle it.
6. **Naive fast search makes first sight a geometry coin flip.** [ARITH] Which side sees the other first depends on the parity of the search length, odd in 193 of 385 geometries. A searcher can remove this by pacing its moves (§H.2, T4).
7. **Detection timing cannot be recovered from replays.** [SOURCE] Replays record anchors only at tick boundaries, so the experiment needs agent traces for control and treatment cells alike (§C.4).

**What would stop it before any Ruleset work:** §K.1 lists six conditions (P-1 to P-6). None is triggered at source level. The conditions for GO are C-1 to C-5 (§M).

---

## A. Baseline and Scope

### A.1 Repository

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `da39f2d` ("docs(v6): add the Branch B action-choice scope review") |
| Tree | Clean before the review; this file is the only change. No test was run, because no code changed. |
| Parents read | `RULESET_V6_RESEARCH_SCALE` (`ruleset_policy.py:621–631`): chunked scheduler, chunk 2, rotation, seeded placement, round-robin selection, `fixed_64` stride, K = 1, whole-tick disruption, forward order, `core_base` spawn. `RULESET_V6_RESEARCH_DISRUPTION_SLOT1` (`:746–759`): the same with λ = 1. |

### A.2 Scope decisions this review works within

These are the research lead's decisions (2026-09-25), given after the scope review was committed. They are restated here so that a committed record carries them.

| Decision | Value |
|---|---|
| Mechanic family | Priced sensing |
| Variant | Radius only: passive fixed-radius detection, with the cost of search paid through MOVE. SCAN is held in reserve, and used only if movement-based discovery collapses into a search race. |
| Primary parent | `bytefray-rules-6-research-scale` at arena 512 (stable-equivalent semantics) |
| Companion | The same sensing treatment on the λ = 1 parent |
| Arena | 512 only; no scaling dimension |
| Radius | Fixed from geometry before any probe, strictly below the 64-cell minimum separation. 32 is a candidate until the boundary and wrap semantics are proven (§B, §D). |
| Agent knowledge | The radius is public |
| Probes | None while semantics and radius are selected. A later non-matrix probe may test manipulation and feasibility only. |
| Evaluation | A matched policy family, plus at least one adaptive agent |
| Branch A | Remains open. It must not become a hidden second hypothesis. |

---

## B. Exact Distance and Wrap Semantics (item 1)

Everything below is [SOURCE] at `da39f2d`.

| Element | Rule | Where |
|---|---|---|
| Arena | A ring of `arena_size` cells, 512 here | — |
| Positions are normalized | A default spawn sits at `core_base`, and `core_base = spec.start % A`. An explicit position is reduced mod A. MOVE sets `(position + delta) % A`. | `process_runtime.py:716–720, 745–753, 1240` |
| Distance | `_circular_dist(a, b) = min(|a − b|, A − |a − b|)`, for normalized a and b; range [0, A/2] | `process_runtime.py:759–761` |
| Visibility test | `_circular_dist(observer, enemy) <= radius`: **inclusive** | `process_runtime.py:822` |
| MOVE | Operand clamped to ±`max_move_delta`, which is **64** under `fixed_64` at every arena. Displacement is literal. | `process_runtime.py:1236–1240`; `ruleset_policy.py:306–317` |
| Placement | Seat 0 is drawn from a SHA-256 stream over the match seed. Each later seat is redrawn until `_circular_distance ≥ 64` from every placed seat. The minimum separation is `min(64, A // entrants)`, which is 64 at 512. If draws run out, the whole layout falls back to even spacing: 256 apart for two entrants. | `placement.py:129, 185–196, 234–253` |
| Core | Cells `base … base+7`, mod A. Anchors are single cells. | `process_runtime.py:721` |

**Semantics this review adopts.** With every position already normalized, the treatment needs no new geometry code and no wrap special case: *d* < A/2, and the existing `_circular_dist` handles the wrap. An enemy anchor *e* is visible to an observer *o* exactly when:

> `_circular_dist(o, e) ≤ r(o)`, where `r(o) = min(reach(o), d)`

**The inclusive boundary is load-bearing.** It must be preserved and tested (§D).

---

## C. Visibility Semantics and Update Timing (item 2)

### C.1 Current rule and proposed rule

| Property | Current (`process_runtime.py:786–826`) | Proposed |
|---|---|---|
| When it is computed | Immediately before every callback, when the observation is built (`:1110`). This is the only consumer (§C.3). | Unchanged |
| Observers | Every friendly process with a position that is **not suppressed** (`:809–813`) | Unchanged |
| Radius | The observer's declared `reach` (`:818`) | **min(reach, *d*)** |
| Targets | The anchors of every process of every **live** enemy entrant, suppressed or not (`:800–807`) | Unchanged |
| Aggregation | An entrant-wide union, as a sorted tuple of unique addresses, with no identity (`:814–826`) | Unchanged |
| Persistence | None: recomputed every callback. Agents keep their own memory. | Unchanged |

**Timing consequences**, all unchanged in kind:
- A MOVE earlier in the tick changes what the next callback sees.
- An enemy's move in its own chunk is visible at the observer's next callback.
- A suppressed sensor sees nothing.

With equal effective radii, detection is **mutual in distance but not in time**. Whichever entrant's callback comes next, after the geometry changes, sees first. §H.2 (T4) develops this.

### C.2 Why min(reach, *d*) and not *d*

If the radius were *d* alone, a process that declared a reach below *d* would see *more* than it does today, and the treatment would be granting information. With min(reach, *d*):

> **Restriction theorem.** In every game state, the treatment's visible set is a subset of the parent's, because min(reach, *d*) ≤ reach and every other input is identical. [SOURCE]

The manipulation therefore only removes information. The rule for agent authors reads: "each process sees enemy anchors within its reach or within *d* cells, whichever is smaller."

The theorem holds per state, not per trajectory. Once play diverges, the two conditions are in different states.

### C.3 Footprint and compatibility

- **Engine.** One `RulesetPolicy` field, `detection_radius: int | None = None`, where `None` keeps today's rule byte for byte. One line changes at `:818`. Validation belongs in two layers, because a statically constructed `RulesetPolicy` does not know the arena size of a particular match:
  - *policy validation*: `None`, or a positive integer;
  - *match validation*, at runtime: *d* < `arena_size / 2`.

  This experiment additionally requires exactly A = 512 and *d* = 32. Every existing Ruleset keeps `None`.
- **Exposure to agents.** An additive `MatchContextV2.detection_radius`, with precedents in `MatchContext.locality_reach` and `MatchContextV2.parameters`. There are three construction sites:
  - direct execution, `process_runtime.py:406–419`;
  - the worker, `agent_worker.py:444–451`, where the reset request would carry the value as an additive protocol field;
  - validation, `agent_validation.py:118`, where it is `None`.
- **Existing tooling that re-derives visibility.** `tools/research/v5/analyzer.py:616` re-implements visibility from replays using *declared reach*. Under the treatment it would be wrong, so it must not be reused unmodified.

### C.4 What the replay can and cannot show

Process snapshots record each anchor, disruption flag and declared reach only at **tick boundaries** (`process_runtime.py:972–983`). A MOVE happens inside a tick. So visibility at each callback, and the order in which two entrants first see each other, **cannot be reconstructed from the replay**.

Agent traces do record every decision's observation, including `visible_enemy_anchor_addresses`, and the spectator pipeline already derives `DETECTION_GAINED` and `DETECTION_LOST` from them (`spectator_derivation.py:499–540`).

Detection timing therefore needs traces, or equivalent callback-level additive telemetry, for every **control and treatment** matrix cell. Control traces give the direct baseline for first detection, search allocation and callback observations. They also test the claim that the search parameters are inert under the parent. The replay format does not change; traces and their analysis are the right layer. That is condition C-4.

---

## D. Deriving the Radius (item 4)

Two geometric constraints bound *d*. Both come from source constants at arena 512 under `fixed_64`, and neither reads a gameplay outcome.

| # | Constraint | Derivation | Bound |
|---|---|---|---|
| **G1** | **No enemy is visible at spawn.** | Every default-spawned anchor sits on its core base (`resolve_initial_anchor`, `core_base` mode), and core bases are at least 64 apart. With an inclusive test, a spawn-time sighting needs *d* ≥ 64. | *d* ≤ 63 |
| **G2** | **No tunneling at the maximum stride.** | A searcher moving the maximum 64 cells per MOVE samples a window of 2*d* + 1 cells at each position (inclusive). Consecutive windows leave no gap only if 2*d* + 1 ≥ 64. [ARITH] At *d* = 31, a full maximum-stride sweep of the ring covers 504 of 512 cells; at *d* = 32 it covers all 512. | *d* ≥ 32 |

**G2 is the sampling condition Phase 4D saw violated.** Proportional movement there made movers "leap over each other without ever entering mutual perceptual reach", because the stride exceeded 2R + 1 (Phase 4D §I.1) [DOC]. G2 excludes that failure by construction.

**The admissible band is 32 ≤ *d* ≤ 63.** **This review recommends *d* = 32**, the band's minimum. It is the most restrictive radius at which a maximum-stride MOVE never skips a cell. A larger *d* widens every window, which shortens search and enlarges the zone of mutual detection. Choosing the bound that keeps information most expensive, while still keeping search free of tunneling, is a principle fixed in advance, not a value tuned against outcomes.

- **The inclusive boundary is essential.** With a strict `<`, the window at *d* = 32 would be 63 cells, and the maximum stride would tunnel. The existing `<=` at `:822` must be kept, and pinned by a test.
- **Why 32 is also half the separation.** At arena 512, the maximum stride and the minimum separation are both 64, so *d* = 32 is also exactly half the minimum separation. At other arenas the two diverge: the stride stays 64, while the separation is `min(64, A // entrants)`. The derivation is therefore specific to arena 512, which the scope limits the first experiment to.
- **Wrap.** *d* = 32 is far below A/2 = 256, so no window can meet itself around the ring.

---

## E. Information Side-Channel Audit (items 3 and 8)

Every path by which an agent could learn where the opponent is falls into one of three classes:

| Class | Meaning | Status here |
|---|---|---|
| **R**, Ruleset/API | Anything a legal agent receives through its observation, its context, its actions, or public importable code | **In scope** |
| **M**, methodology | Depends on how an experiment is run: seeds, agent parameters, the fixtures | **In scope**, closed by experimental design |
| **X**, containment | Depends on how agent code executes: the same Python process, frame inspection, the filesystem | Deliberately **deferred**. Agent code runs as ordinary, unsandboxed code with the engine's privileges ([SECURITY.md](../../../SECURITY.md), "Security-sensitive areas"), so containment is a separate concern from Ruleset design. Listed, not pursued. |

### E.1 Channel register

| # | Channel | Class | What it reveals about the opponent's location | Cost to the agent |
|---|---|---|---|---|
| 1 | `visible_enemy_anchor_addresses` | R | Enemy anchors within min(reach, *d*) | Free within the radius; **this is the treated channel** |
| 2 | The other observation fields: tick counters, `self_*`, `own_core_*`, `previous_action_applied` | R | **Nothing.** `previous_action_applied` reports only whether the target was in the actor's own reach, not whether it hit anything (`:1245–1289`). A gap between callbacks tells an agent it was suppressed, meaning the opponent knows where *it* is, not where the opponent is. | — |
| 3 | `previous_read_value` and `previous_read_owner` after a READ | R | The value and last writer of the one cell read. Each core is seeded with `0xCE`, owned by its entrant (`:731–733`), and unwritten cells report owner `None` (`vm.py:29`). This finds cores (§G), shows enemy-painted territory as a rough region, and shows damage to one's own core, which reveals intent but not location, since action reach is global. | One action per cell |
| 4 | `previous_read_owner` as an **identity** | R | The opponent's `agent_id`, not its location. It matters for adaptation: an adaptive agent could key on the opponent's name instead of its behavior. | One READ of any enemy-owned cell |
| 5 | Seed inference (§E.2) | **R/M** | **The enemy core base, exactly** | **Zero actions** |
| 6 | Seat geometry | R | Given its own core, the enemy's core base is uniform over the 385 offsets at least 64 cells away [GEOM: all 385 occur, 452–584 times each over 200,000 seeds; none inside the exclusion zone]. The only prior is the 127-cell exclusion zone. | — |
| 7 | Scheduler order | R | Agents never receive slot numbers: the direct executor discards `action_slot` (`:458`). They can count their own callbacks in a tick, which reveals chunk position and the tick's first mover, but not location. This is load-bearing for pacing (§H.2, T4). | — |
| 8 | Engine objects handed to agent code | R | **None.** The direct executor passes only the frozen `ObservationV2` (`:452–459`), and the context is frozen. | — |
| 9 | `MatchContextV2.parameters` | M | Whatever the evaluator passes. The research harness must pass nothing about location, which is trivially true of the family in §I. | — |
| 10 | In-process introspection: under the direct executor, agent code shares the engine's Python process (gc, stack frames) | X | Everything | Deferred |
| 11 | The worker path sends the **raw match seed** into the worker process, where `_handle_reset` derives the agent seed (`agent_worker.py:428–443`) | X | The match seed, and so placement, if `reset()` inspects its caller's frame | Deferred |
| 12 | Replay and trace files written during the match | X | Full state, if the agent can find and read them | Deferred |
| 13 | Module state shared between two agents in one process | X | Nothing to an honest opponent; possible collusion | Deferred |

**Conclusion.** Exactly **one** in-scope channel yields the opponent's location for zero actions: row 5. Every other in-scope channel either costs actions or carries no location. §E.2 closes row 5 by methodology, and C-2 closes row 4.

### E.2 Seed inference: the one zero-action bypass

**The mechanism.** [SOURCE]
- An agent receives `seed = derive_agent_seed(match_seed, slot, agent_id, 2)` in its context (`process_runtime.py:394`). That value is a truncated SHA-256 of a known format (`python_runtime.py:552–559`).
- Seeded placement is a deterministic function of the match seed (`placement.py:185–253`).
- Both functions are public, and agent code can import them.

**Two routes, both demonstrated.** [GEOM]

| Route | How | Demonstrated |
|---|---|---|
| **R1: invert the derived seed** | Enumerate candidate match seeds and both slots until `derive_agent_seed` equals the context seed, then compute the layout | 100,000 seeds × 2 slots in **0.37 s**, recovering the planted seed exactly. The direct executor sets no reset timeout (`agent_call_timeout` is `None` unless supervised). |
| **R2: match one's own core base** | Enumerate candidate seeds, compute each layout, and keep those that put one's own core where it is | Seeds 1–32: **54 of 64** (seed, seat) cases pin the enemy core uniquely. Seeds 1–1000: 49 of 2000. Seeds 1–65,536: 0 of 131,072. |

**Why it matters.** Every E2–E5 matrix used seeds 1–32 (E2-R §C; E3 experiment freeze, fixed settings; the E4 and E5 design reviews' evidence-tier notes). R1 works whenever the match seed lies in any space an agent can enumerate, which includes every small integer and every human-chosen seed. Neither route needs introspection. Both use only public inputs and public code.

**Closure for the research question** (condition C-1):
- **Seed-set blindness.** High entropy alone is not enough. If the exact finite seed set, or a published master seed and derivation, is available to agents before execution, the candidates are enumerable again. The protocol:
  1. freeze and fingerprint the complete matched agent family **before** the matrix seeds are selected;
  2. generate unique high-entropy matrix seeds from a cryptographically strong source;
  3. before treatment execution, commit only a SHA-256 commitment to the ordered, canonical seed list, not the seeds themselves;
  4. keep the seed list unavailable to the matched agents during execution;
  5. reveal and record the complete seed list after the frozen experiment is complete, so the corpus stays reproducible and the commitment can be checked.
- **Agent discipline.** The matched family may import only `battle_engine.agent_api`, uses `context.seed` only through `context.rng`, and is checked by a static gate (C-2).
- **Scoped claim.** Every claim is scoped to agents that do not reconstruct placement, in line with the scoping rule for this line.

**Product level: deferred.** The channel exists in stable V4 today, where it does not matter, because visibility is free anyway. Under priced sensing, any promotion would first need placement that agents cannot reconstruct, for example a per-match placement salt recorded in the result but not delivered to agents. That would change placement relative to the parent, which is a second variable, so it cannot be part of this experiment. **It is a promotion prerequisite, not a research blocker.**

---

## F. Blind Writes (item 7)

**Recommendation: keep blind writes unrestricted.** [SOURCE, ARITH]

- A WRITE may target any address within action reach, which is global for the family (`:1269–1289`). Restricting writes to visible cells would bound action reach by sensing. That is the not-resurrected reach cap (SR §C, K6), and a second variable.
- **The lottery bound.** A blind tick-1 capture needs the exact enemy core base: 1 chance in 385 per eight-action attempt, since the offset is uniform (§E.1, row 6). The attempt gets no feedback: `previous_action_applied` is True whatever the target.
- **Dominated as a search method.** A blind systematic search costs 8 actions per candidate position. Sensing search finds an on-core anchor within at most 7 MOVEs in total (§G). So blind writes survive only as a lottery, never as a discovery strategy.
- **The resulting claim.** Priced sensing removes the canonical guaranteed tick-1 line for discovery-dependent play. Blind play is a lottery bounded at 1/385 per attempt. Placement inference (§E.2) is the only guaranteed bypass, and it is closed by methodology.

---

## G. What the Mechanic Prices, and What Counts as Search (item 6)

### G.1 Two kinds of information, two ways to search

The treatment prices two different things:

- **where the enemy anchors are**, which is what disruption needs, and which is also the enemy core base while an anchor still sits on its core;
- **where the enemy core is**, which is what capture needs, and which never changes during a match.

There are two ways to search [ARITH, A = 512, *d* = 32]:

| Mode | What it finds | Cost | Exposure |
|---|---|---|---|
| **MOVE sweep** at the maximum stride | Anchors | At most 7 MOVEs; mean 1537/385 ≈ 3.99. Distribution of *k* (MOVEs to detect): 1 → 33, 2–6 → 64 each, 7 → 32 geometries. | **Mutual.** At equal radius, the sensor is seen when it sees. |
| **READ stride search**: every 8th cell over the 385-cell allowed arc | A core cell (`0xCE`, enemy owner) | At most 49 READs, mean 25.4, plus up to 7 more to locate the base | **None.** The reader stays at home; action reach is global. |

**MOVE is about 6 times cheaper, but it exposes the searcher. READ is slow but stealthy**, and it is the only way to find a core whose anchors have already left it.

**The price is front-loaded.** Finding an anchor that is still on its core costs less than one tick of budget (at most 7 actions, against Q = 8). The choice this mechanic can create therefore lives mainly in the **opening exchange**, and afterwards only in re-finding anchors that move.

### G.2 Defining "search"

Search is **not inferred from movement.** The V3 closeout showed that behavior history cannot identify intent. A MOVE can serve search, evasion or approach, and the replay records no purpose. The review defines search in three layers:

1. **Primary: the policy parameter.** In the matched family (§I), the experimenter sets how each agent divides its actions. What counts as search is whatever the parameter controls.
2. **Descriptive only, derived from traces** (§C.4), never registered as measures of intent:
   - a *pre-detection MOVE* comes before the entrant's first detection of any enemy anchor;
   - a *re-acquisition MOVE* comes after a detection is lost;
   - an *off-core MOVE* takes the entrant's own anchor off its own core;
   - a *probe READ* reads a cell outside the entrant's own core.
3. **The adaptive agent's own allocation log.** Since we author that agent, its log is a design instrument. It is never a scoring input.

---

## H. The Central Question: A Choice, or a Search Tax? (item 9)

### H.1 What a search tax would look like

Priced sensing is a **pure discovery tax** if both of the following hold:

- (i) against every opponent in the family, the best response searches at full speed until it finds the opponent, and then plays the parent Ruleset's best policy;
- (ii) outcome classes equal the parent's, with decisive ticks delayed by the time discovery takes.

This is E2's H0 ("delay only") in new form. The pre-registration should register it as the null hypothesis (§H.5).

### H.2 Source traces

**These traces are hand-derived from source semantics for hypothetical policies. None was executed, and none is a result.**

**Assumptions for every trace:**
- the parent's semantics: K = 1, whole-tick disruption, forward order, chunk 2, rotation;
- arena 512, *d* = 32;
- single-process agents with global action reach;
- *x* is the enemy's offset and *k* = ⌊(*x* + 32)/64⌋.

**Offer order.** On odd ticks the order is A A B B, four times over: A acts in slots 1, 2, 5, 6, 9, 10, 13 and 14, and B in 3, 4, 7, 8, 11, 12, 15 and 16. Even ticks reverse the order.

**T0: the parent's forced line, for reference** (Phase 4A addendum):
1. At tick 1, A's first callback sees B's anchor, which is B's core base.
2. A WRITEs it. That one write disrupts B and takes core cell 0.
3. A's seven remaining writes take the rest of the core, and B is captured at tick 1.

**T1: a fast searcher S against a stationary guard G** that stays on its core, disrupts on sight, and otherwise repairs. S is Seat A.

*When k is odd*, S arrives on the first action of a chunk:

| Tick | First mover | What happens | G's core cells at tick end |
|---|---|---|---|
| 1 | S | S's second action of that chunk sees G and hits G's anchor, which is also core cell 0. G is out for the rest of the tick. S spends its remaining actions on further core cells: six when k = 1, none when k = 7. | at least 1 of 8 (alive) |
| 2 | G | G sees S, disrupts it, and repairs 7 cells. | 8 of 8 |
| 3 | S | S hits the anchor and makes 7 core writes. | 0: **captured** |

*When k is even*, S arrives on the second action of a chunk:

| Tick | First mover | What happens |
|---|---|---|
| 1 | S | G's next chunk sees S first and disrupts it. S is out for the rest of the tick. |
| 2 | G | G disrupts S again. |
| 3 | S | S hits the anchor and makes 7 core writes: **captured** |

If S is Seat B instead, the same logic ends in capture at **tick 2**. S's first-mover tick arrives one tick sooner.

→ **Against a stationary on-core defender, fast search reproduces the forced line 1–2 ticks late.** That is the search tax's shape.

**T2: a fast searcher S against an evasive guard E** that moves its anchor off its core, then disrupts on sight and repairs.
- **The cost of capture rises.** Once E's anchor is off the core, hitting it no longer writes a core cell. Disrupting E and then sweeping its whole core costs 9 actions against a budget of 8. This is exactly E5's added cost (E5-R §F.2, §J), but here the defender *chooses* it, for one MOVE.
- **The match settles into alternation, even when S already knows where E's core is.**
  - On S's first-mover ticks, S disrupts E and makes 7 core writes, so E keeps one cell.
  - On E's first-mover ticks, E disrupts S and repairs 7 cells.

  Under K = 1 a capture needs zero cells, so this alternates to a **tick-limit draw**.
- **S rarely learns where E's core is.** S learns it only by seeing E's anchor before E leaves.
  - With S as Seat A, that happens only when k = 1: 33/385 = 3/35 of geometries [ARITH].
  - With S as Seat B, it never happens: E moves first.
  - Otherwise S must search by READ (at most 49 READs).

→ **Evasion defeats the delayed forced line. But the natural continuation is an E2-style alternation**, and that is stalling (kill criterion 3).

**T3: splitting sensor and striker.** [INFERENCE; not traced in full] A two-process attacker keeps its striker out of E's sight while its sensor approaches. When E disrupts the sensor, the striker stays eligible, and quota moves to eligible processes (`:853–866`). Acting on its memory of E's last-known anchor, the striker can still hit E, which breaks T2's symmetry. **This is the source's own counter to T2's stalling.** A family without a two-process member would build a stalling result into the test itself (§I).

**T4: who sees first.** [TRACE, ARITH]
- In T1, which side sees first depends on the parity of k. Under naive fast search that is odd in 193 of 385 geometries: a seed-geometry coin flip.
- **A paced searcher** moves only on the first action of each chunk, which it can determine by counting its own callbacks in the tick (§E.1, row 7). It then always sees first, because its own second action comes next. The cost is half the speed, and the second action of each chunk is left for other uses.

### H.3 Decision points found at source level

Each point is opponent-dependent at source level. None is shown to be a best response.

| # | Decision | Better one way when… | Better the other way when… |
|---|---|---|---|
| 1 | **Search pace:** fast or paced | the opponent never disrupts on sight | the opponent disrupts on sight (T4) |
| 2 | **Search mode:** MOVE or READ | the opponent stays on its core, or doesn't punish exposure | the opponent evades or punishes exposure (G.1, T2) |
| 3 | **Stay or evade** | the opponent never searches, so evasion wastes actions | the opponent searches fast (T1 against T2) |
| 4 | **Search or paint** | attack pays against this opponent | the opponent cannot be captured cheaply (T2) |
| 5 | **Split sensor and striker** | the opponent disrupts on sight (T3) | the opponent never does, so the split only divides the budget |

### H.4 The prior, stated plainly

- **The risk of a search race is substantial.** Discovery costs at most 7 actions, and a stationary defender loses 1–2 ticks late (T1).
- **The most promising source of real choice is evasion**, and its most likely failure is stalling (T2), unless splitting sensor and striker (T3) breaks it.
- **The λ = 1 companion is essential, not optional.** Whole-tick denial is what makes the first-mover tick decisive in T1 and T2. Under λ = 1 the victim keeps acting, so T1's capture and T2's alternation both change. They are not traced here.

### H.5 Telling a tax from a choice

These are criteria for the pre-registration. None is registered here.

- **The null hypothesis, "delay only".** For every policy pair, the treatment's outcome class equals the parent's, with decisive ticks later. This is E2-H0 in new form. The comparison is reliable because under the parent every search parameter is inert: all anchors are visible at the first callback, so the family collapses by construction.
- **Primary evidence of a choice, two parts:**
  - **a best-response map that is not constant** over the family;
  - **a frozen matched contrast where less information wins.** This is the research lead's diagnostic made operational: a matched pair that differs *only* in its search allocation, where the lower-information member strictly beats the higher-information one against at least one opponent. Put plainly: does knowing more sometimes stop being worth what it costs?
- **Secondary evidence: adaptation.** The adaptive agent's performance against the fixed members is reported, but it is **not** a necessary condition. A mediocre adaptive heuristic can fail even when the payoff structure really does depend on the opponent, so "ADAPT beats every fixed policy" must not be the mechanic's pass/fail test.
- **Evidence rules.** All of these follow synthesis §G.8 and E5 Revision 1 §R5–§R6:
  - report n_distinct beside every count;
  - compute per seed, then take the unit median;
  - require a minimum number of independent units;
  - fix every band exactly, before the freeze;
  - give NEITHER its own interpretation rows.

---

## I. The Matched Agent Family (item 5)

**One agent source, parameterized** through `MatchContextV2.parameters`. Every member shares the same building blocks:
- a maximum-stride sweep, fast or paced;
- a stride-8 READ probe;
- core confirmation by READ (`0xCE` plus the enemy owner);
- anchor disruption;
- a core sweep;
- repair;
- painting;
- memory of each opponent anchor's last-known position and the tick it was seen.

Every member declares global action reach (`arena // 2`), so its effective sensing radius is exactly *d*.

| Parameter | Values |
|---|---|
| `search` | `none` (sees only within *d*) · `fast` · `paced` · `read` |
| `posture` after discovery | `attack` · `guard` (disrupt on sight, repair) · `paint` |
| `evade` | `off` · `on` (on its first callback, moves its anchor off the core by a seeded offset) |
| `processes` | `1` · `2` (a sensor and a striker) |
| `adaptive` | `off` · `on` |

**Members.** Each fixed member differs from a named neighbor in exactly one parameter, so each pair gives a diagnostic:

| Member | Search | Posture | Evade | Processes | Matched against | Isolates |
|---|---|---|---|---|---|---|
| **RUSH** | fast | attack | off | 1 | — | the tax baseline (T1) |
| **PACED** | paced | attack | off | 1 | RUSH | search pace (T4) |
| **SPLIT** | fast | attack | off | 2 | RUSH | the sensor–striker split (T3) |
| **GUARD** | none | guard | off | 1 | — | stationary defense (T1) |
| **EVADER** | none | guard | on | 1 | GUARD | evasion (T2) |
| **STEALTH** | read | attack | off | 1 | RUSH | search mode: READ rather than MOVE (G.1) |
| **GREED** | none | paint | off | 1 | GUARD | posture: territory rather than defense |
| **ADAPT** | adaptive | adaptive | adaptive | 1 | every fixed member | adaptation (secondary evidence, §H.5) |

**Rules for ADAPT, fixed in advance:**
- it starts as GREED;
- if it detects an enemy within *d*, it switches to guard and disrupts;
- if a periodic READ of its own core shows damage, it evades and guards;
- if it has had no contact by a pre-registered tick, it switches to search and attack.

**STEALTH is required, not optional.** READ is a legal, action-priced search channel that does not expose the searcher. If READ search beats movement search, that is not contamination: it is exactly the kind of strategic choice the experiment is looking for. A sensing experiment that left out one of the engine's two legal search methods would be incomplete.

**Discipline** (condition C-2):
- Members import only `battle_engine.agent_api`, a check a static gate can enforce.
- They use `context.seed` only through `context.rng`.
- **Agent IDs are opaque** and say nothing about parameters, which closes §E.1 row 4.

**Randomness:** a seeded sweep direction, evade offset and paint start, intended to give units trajectory variety. Evidence weight is judged only afterwards:
- every frozen diagnostic unit is included, whatever its realized n_distinct;
- n_distinct is reported afterwards, as evidence weight;
- no deterministic unit is silently discarded;
- any rate claim is pre-registered, with its cell-level quantity and denominator fixed independently of realized treatment variability (§K.1, P-3).

**Under the parent Ruleset** the search parameters are inert, because everything is visible from the first callback. The parent's payoff table is therefore degenerate by construction. That is expected, not a finding.

**Size.** Eight members is deliberately small. Each earns its place through a named diagnostic.

---

## J. Parents, Companion and Evaluation Outline

This carries the scope decisions (§A.2) into a structure for the experiment. It is not a pre-registration.

| Element | Design |
|---|---|
| Primary arm | `bytefray-rules-6-research-scale` + `detection_radius = 32`: one field from the stable-equivalent control |
| Companion arm | `bytefray-rules-6-research-disruption-slot1` + `detection_radius = 32`: one field from its parent. It tests whether T1 and T2 depend on whole-tick denial (§H.4). |
| Arena | 512 only |
| Seeds | Seed-set blindness protocol (§E.2, C-1). Not the E-series 1–32. |
| Field | The matched family (§I), as a round robin in both orientations, with twin mirrors where needed. Mirrors are analyzed seed by seed, with relabel identity used as a gate (synthesis §G.8). |
| Instrumentation | Traces, or equivalent callback-level additive telemetry, for every control and treatment cell (§C.4, C-4). A size and time estimate is needed before any freeze. |
| Manipulation gates | These test the manipulation only, never a gameplay outcome (the E5 Revision 1 §R2 principle): |
| | **(i)** At every callback, the visible set equals the enemy anchors within min(reach, *d*). This is a Ruleset invariant, checked from traces. |
| | **(ii) Initial-state invisibility.** In the initialized state, before the first scheduled action, every opposing default-spawn anchor is farther than *d* = 32 from every matched-family sensor. This follows from G1 and `core_base` spawn. It is deliberately **not** a first-callback gate: the first mover can MOVE before the second mover's first callback, so the second mover may legitimately see it then. Callback observations are validated against actual geometry by gate (i). |
| | **(iii)** The static family-discipline gate (C-2). |
| | **(iv)** With `detection_radius = None`, each parent is reproduced byte for byte. |
| Pathology flags | Recorded whatever else holds: stalling (including alternation stalemates, measured with E2's phase-lock and recovery instruments), loss of contact, new immunity, seat artifacts (including T4's arrival parity), greed dominance, and a delayed forced line |

---

## K. STOP and REDESIGN Criteria (item 10), and Refined Kill Criteria

### K.1 Before any Ruleset work

| ID | Condition | Outcome |
|---|---|---|
| **P-1** | The research lead requires the seed channel (§E.2) closed at the product level before research | **STOP** Branch B research, and scope a placement design first |
| **P-2** | The seed-blindness protocol (C-1) or the family-discipline gate (C-2) is not adopted | **REDESIGN.** The claim could not be tested against a known bypass. |
| **P-3** | **Design-count gate.** Before registration, the frozen family does not contain at least six independently specified diagnostic policy contrasts whose membership does not depend on treatment behavior. Realized n_distinct cannot be known before treatment without looking at treatment behavior. It is reported afterwards as evidence weight and never used to select units (§I). | **REDESIGN** the family |
| **P-4** | The delay-only null (§H.5) cannot be written with exact criteria | **REDESIGN** the instrument |
| **P-5** | Detection timing cannot be recorded at matrix scale, through traces or additive telemetry | **REDESIGN** the instrumentation |
| **P-6** | The implementation audit finds any other in-scope channel that yields location for zero actions | **STOP** until it is closed |

None is triggered at source level.

### K.2 Refinements to the scope review's kill criteria (SR §G.1)

| # | Kill criterion | Refinement |
|---|---|---|
| 1 | Search race | Unchanged: the best-response map is constant. |
| 2 | Greed dominance | Unchanged. |
| 3 | Loss of contact or stalling | **Add:** alternation stalemates of the T2 kind count as stalling, measured with E2's phase-lock and recovery instruments. |
| 4 | Delayed forced line | **Rescope.** It fires only if a delayed forced line defeats **every** defender policy in the family, the evasive one included. A stationary defender losing 1–2 ticks late is predicted by T1. That is the tax's shape, measured by the delay-only null (§H.5), and it is not by itself a kill. As written in the scope review, the criterion would fire trivially. |
| 5 | Seat artifact | **Add**, as named items to measure: T4's arrival-parity coin flip, and T2's asymmetry between Seat A and Seat B in catching an evader still on its core. |

---

## L. Findings Register

Severity follows the standing review classes.

| # | Severity | Finding | Section |
|---|---|---|---|
| 1 | **BLOCKER** (for any research claim) | Seed inference gives the enemy core for zero actions whenever the match seed can be enumerated | §E.2 |
| 2 | **HIGH** | Kill criterion 4 as written would fire trivially against stationary defenders | §H.2 T1, §K.2 |
| 3 | **HIGH** | Replays cannot show detection timing; traces are required for control and treatment cells | §C.4 |
| 4 | **MEDIUM** | A READ's owner reveals the opponent's identity; agent IDs must be opaque | §E.1 row 4 |
| 5 | **MEDIUM** | The historical v5 analyzer re-implements visibility using declared reach, and must not be reused unmodified | §C.3 |
| 6 | **GAMEPLAY FINDING** | The price is small and front-loaded: at most 7 MOVEs, mean ≈ 3.99 | §G.1 |
| 7 | **GAMEPLAY FINDING** | Evasion leads to alternation, a stalling risk; splitting sensor and striker is the source's own counter | §H.2 T2–T3 |
| 8 | **GAMEPLAY FINDING** | Naive search makes first sight a parity coin flip; catching an evader on its core differs by seat | §H.2 T2, T4 |
| 9 | **DEFERRED** | Containment channels: introspection, the raw seed in the worker process, the filesystem, shared modules | §E.1 rows 10–13 |
| 10 | **DEFERRED** | Seed inference at the product level, for user-chosen seeds: a promotion prerequisite | §E.2 |
| 11 | **NOT ACTIONABLE** | The seat-geometry prior (uniform over 385 offsets), the agent's own ID, scheduler timing | §E.1 |

---

## M. Verdict and Decisions

**Verdict: GO WITH CONDITIONS.** Priced sensing can create opponent-dependent choices at source level: there are five decision points (§H.3). The review also predicts its two most likely failure shapes: a tax of 1–2 ticks against stationary defenders (T1), and alternation that stalls against evaders (T2). Whether any policy other than search-first is rational is exactly what the experiment must decide. Nothing here settles it.

**Conditions for GO:**

| ID | Condition |
|---|---|
| **C-1** | The seed-set blindness protocol, with claims scoped to agents that do not reconstruct placement (§E.2) |
| **C-2** | A static family-discipline gate: only `agent_api` imports, `context.seed` used only through `rng`, opaque IDs (§I) |
| **C-3** | Kill criteria refined as in §K.2 |
| **C-4** | Traces, or equivalent callback-level additive telemetry, for every control and treatment cell, with a size and time estimate before any freeze (§C.4) |
| **C-5** | The research lead's decisions below |

**Decisions of the research lead (2026-09-25), recorded here:**

| # | Decision | Decided |
|---|---|---|
| 1 | Radius rule | min(declared reach, *d*), inclusive: a pure restriction (§C.2) |
| 2 | *d* | **32**, the minimum of the band fixed by G1 and G2 (§D). Exactly A = 512 and *d* = 32 for this experiment. |
| 3 | Exposure | Public: an additive `MatchContextV2.detection_radius` (§C.3) |
| 4 | Parents | Primary `bytefray-rules-6-research-scale`; companion on the λ = 1 parent (§J) |
| 5 | Blind writes | Unrestricted (§F) |
| 6 | Seeds | The seed-set blindness protocol (§E.2, C-1) |
| 7 | Family | **Eight members:** RUSH, PACED, SPLIT, STEALTH, GUARD, EVADER, GREED, ADAPT (§I). SPLIT is kept specifically so that EVADER's stalling result is not built into the field. STEALTH is required from the start. |
| 8 | Discipline | Opaque IDs and the static family-discipline gate (C-2) |
| 9 | Evidence roles | Primary: a best-response map that is not constant, and a frozen matched contrast where less information wins. ADAPT is secondary evidence, not a pass/fail test (§H.5). |
| 10 | Gates and criteria | Initial-state invisibility, not a first-callback gate (§J); the design-count gate P-3 (§K.1); the five kill criteria as refined in §K.2, including the delayed-forced-line criterion at the family level |
| 11 | Traces | For control and treatment cells (C-4) |
| 12 | Probes | No gameplay probe before registration |
| 13 | Where decisions are recorded | Here (§A.2 and this table), committed with this review |

**Next step:** registration and implementation planning — the Ruleset field and its two-layer validation, exposure plumbing, the eight-member family, instrumentation, the seed protocol and gates — still with no treatment matrix and no exploratory outcome probe.

---

## N. What This Review Does Not Claim

- **No result.** Traces T0–T4 are hand-derived from source semantics for hypothetical policies. No match, probe or prototype was run. [GEOM] and [ARITH] values describe placement geometry and search arithmetic only.
- **No claim that priced sensing creates a choice.** The decision points in §H.3 exist at source level. Whether any of them is a best response is the experiment's question.
- **No claim that every tick-1 capture is impossible.** Blind play remains a lottery (§F). Seed inference is a guaranteed bypass unless it is closed (§E.2).
- **Not a pre-registration.** No threshold, population or interpretation row is set.
- **No containment claim.** Channels of class X are listed and deferred.
- **No change to** the scope review, the synthesis or any E2–E5 record.

---

## Appendix G. Geometry and Arithmetic Computations

All of these were run with the repository's `.venv` Python at `da39f2d`, by calling pure functions. **No controller, agent or match was constructed.**

1. **Route R2** (`placement.seeded_seat_starts(2, 512, s)`). For each seed range, count the (seed, seat) cases in which the entrant's own core base maps to exactly one possible enemy core base:

   | Seeds | Cases pinned |
   |---|---|
   | 1–32 | 54 of 64 = 0.844 |
   | 1–1000 | 49 of 2000 = 0.025 |
   | 1–65,536 | 0 of 131,072 |

2. **Route R1** (`python_runtime.derive_agent_seed`). A target derived from (match seed 27, slot 1, `"some_agent"`, 2) was recovered by enumerating seeds 1–100,000 and both slots: found `[(27, 1)]` in 0.37 s.
3. **Separation and uniformity**, over seeds 1–200,000. The minimum circular core separation was 64. All 385 allowed offsets occurred, 452–584 times each (mean 519.5), and no draw fell inside the exclusion zone.
4. **Sweep arithmetic** (*d* = 32, stride 64, one direction from the entrant's own core base):
   - *k* distribution: 1 → 33, 2–6 → 64 each, 7 → 32;
   - E[*k*] = 1537/385 ≈ 3.992; maximum 7;
   - P(*k* odd) = 193/385; P(*k* = 1) = 33/385 = 3/35.
5. **Tunneling.** A full maximum-stride sweep covers 504 of 512 cells at *d* = 31, and 512 of 512 at *d* = 32.
6. **READ stride-8 search** over the allowed arc [64, 448]: at most 49 READs to hit a cell of an 8-cell core, mean 25.44.
7. **Blind-guess candidates:** 385.
