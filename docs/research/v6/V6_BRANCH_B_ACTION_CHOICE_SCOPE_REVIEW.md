# Bytefray V6 Branch B — Action-Choice Mechanic: Scope and Candidate Review

**Status:** Scope and design review only. No Ruleset, implementation, pre-registration, probe or matrix. It selects one candidate mechanism family for a full design review and sets the others aside. Nothing is registered.
**Branch:** `v6-research` at `3019bc7`. The tracked tree was clean before this review, and this file is its only change.
**Date:** 2026-09-25
**Governing record:** [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md): the seven requirements of §G, and Branch B in §H.

**Evidence tiers.**

| Tier | Meaning |
|---|---|
| [SOURCE] | Current source at `3019bc7`, cited by file and line. |
| [DOC] | A committed research record, cited by file and section. |
| [INFERENCE] | Reasoning from the tiers above. Every claim that a mechanic *would* create a choice is in this tier. None is a result. |

**No probe was run.** Probing any candidate means prototyping it inside the controller, which is implementation in all but name, and this review's scope excludes it. §G.2 says when a probe becomes appropriate.

---

## Verdict in brief

**The question.** What is the smallest mechanic that gives an agent a genuine choice between competing uses of its limited actions, such that the better choice depends on what the opponent is doing?

**Recommendation.**

1. **Select priced sensing for a full design review.** A fixed detection radius limits passive enemy-anchor visibility independently of action reach. Extending the area searched requires process movement, which competes for the same action budget as attack and defense. The minimal form is one Ruleset field: a detection radius that replaces each process's declared reach as its sensing radius, with action reach unchanged (§D.1, variant I-a).
2. **Hold contestable valuable cells in reserve.** They are the strongest candidate on interaction and explainability. But by construction they inherit the surviving second-response privilege, and they cannot be tested without first removing the forced line some other way (§D.2).
3. **Reject investment (action banking) and deployment (mid-match process creation) as first mechanics.** Both cross known structural boundaries, and deployment has the largest footprint of any candidate (§D.3).
4. **Branch A stays open.** The evaluation method that any Branch B mechanic needs, a strategy-family test (§F), also answers Branch A's question for the chosen parent Ruleset as a by-product.

**Key findings.**

- **F1. The forced line runs on free information, and only priced sensing acts upstream of it.** The stable-V4 tick-1 capture needs the first mover to know the enemy core at its first callback. Today that knowledge is free: reach is free, visibility follows reach, and every process spawns on its core cell 0. Capture needs all 8 enemy core cells written in one tick, which is the whole budget of Q = 8. Priced sensing therefore removes the canonical guaranteed tick-1 capture line for discovery-dependent play: once at least one action is spent acquiring the enemy location, fewer than eight actions remain for an eight-cell capture (§D.1). It does not make every conceivable tick-1 capture impossible, and the full design review must audit for bypasses. Every other candidate would sit on top of the forced line, and would need a parent Ruleset that removes it first.
- **F2. V4's own design history chose priced discovery, and free reach undid it.** R4b accepted disruption's severity on the explicit condition that information would be costly. Stage 5 selected local detection at action reach. The pre-RC study then accepted free reach as a disclosed limitation, and ranked "Detection radius distinct from READ/WRITE reach" first among post-4.0 reach directions (§C, K4).
- **F3. A single contested cell sampled once per tick inherits the second-response privilege.** That is a combined reading of E4 and E5. When both sides contest such a cell, it alternates by tick parity (§C, K1). This is the main structural objection to valuable cells.
- **F4. Letting an entrant act more than 8 times in a tick crosses the Q = CORE_SIZE boundary.** Above it, an informed attacker can capture a non-reacting victim within one action block (V3). Investment that pays in actions does exactly this (§C, K2).
- **F5. Deployment adds little that the free fixed roster does not already provide.** R2 found process economies had zero irreducible capability under the old global-reach model. Under the spatial model a deployed process does buy a location. But any number of locations is already free at declaration, and one shared budget means extra processes buy locations, not actions (§D.3).
- **F6. No candidate can be judged with the frozen scripted fixtures.** Those fixtures never choose. Any Branch B mechanic needs a strategy-family evaluation with at least one adaptive agent (§F).
- **F7. Priced sensing has three named ways to fail**, each written as a kill criterion for its design review: a search race, a tilt to greed, and loss of contact (§D.1, §G.1).

This review revises one reading in the synthesis. Synthesis §I.2 called replication and deployment "more promising" as a catalogue entry. Two things weigh against it as a *first* mechanic: the source-level analysis here, and the V4 R2 record, which the synthesis did not consult.

---

## A. Baseline

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `3019bc7` ("docs(v6): correct stale ROADMAP and FUTURE_PLANS status lines") |
| Tree | Clean before the review; this file is the only change. No test was run, because no code changed. |
| State | E2–E5 closed and synthesized (`3cc80c3`). No Branch B record, Ruleset, tooling or specification exists. |
| Records read | The E2–E5 synthesis; E3-R, E4-R and E5-R, and the E4 and E5 design reviews, where cited; the Phase 4A methodology (§1, §11, §14, addendum); V3 closeout (§1, §17–§19); V4 R2 dynamic-process economics; V4 R4b disruption (§K–§R); V4 Stage 5 visibility (§B–§E, §H, §N–§O); the V4 pre-RC gameplay study (§A, §C.1, §D.4–§D.5, §E) |
| Source read | `agent_api.py` (the v2 contract); `process_runtime.py` (declaration validation, visibility, quota, action execution, the tick loop); `ruleset_policy.py` (`RulesetPolicy` fields); `scoring.py`; `config.py`; `placement.py` (minimum separation); `replay.py` (event decoding); `spectator_derivation.py` (detection events); the `e2_sniper` fixture |

---

## B. The Question, Made Testable

### B.1 What counts as a genuine choice

A mechanic creates a genuine choice when five conditions hold together. Each maps to a synthesis requirement:

| # | Condition | Synthesis requirement |
|---|---|---|
| C1 | **Competition.** At least two uses of actions draw on the same finite per-tick budget, Q. | B, opportunity cost |
| C2 | **Positive value.** Each use has positive marginal value in some reachable game state. | B |
| C3 | **Opponent dependence.** The ranking of the uses depends on what the opponent does: no fixed split is best against every opponent. | A |
| C4 | **Observability.** The agent can learn enough about the opponent, directly or by paying, to act on C3 during the match. | C, adaptation |
| C5 | **Interaction preserved.** The choice is not resolved by avoiding contact, by immunity, or by running out the clock. | D |

Requirements E (topology), F (explainability) and G (testability) are judged separately in §E.

**What would show it.** This is a sketch for a later pre-registration, not a registration. Take a family of policies Π(θ) that are identical except for θ, the way they split actions among the uses. The choice is genuine if, in the empirical payoff table over Π:

- no θ weakly dominates every other;
- the best response to an opponent's θ′ changes as θ′ changes;
- the same table under the parent Ruleset is degenerate: the choice does not exist there, or one θ dominates.

§F develops this *strategy-family test*.

### B.2 Why the current rules do not already provide one

**The ingredients exist.** [SOURCE] An Agent API v2 offer must return exactly one of READ, WRITE or MOVE; v2 has no pass (`process_runtime.py:957–970`). Those actions already serve several uses: attacking the enemy core, disrupting an enemy anchor (a WRITE to its address), repairing one's own core, claiming territory, moving, and reading. Phase 4A §11.5 made the same observation [DOC].

**Information is free.** [SOURCE]
- Reach is declared once, as any integer in `[1, arena_size − 1]`, at no cost (`process_runtime.py:281–290`).
- Each callback sees every enemy anchor within the *declared reach* of any unsuppressed friendly process (`process_runtime.py:786–826`; the radius is `observer.reach` at `:818`).
- Under every Ruleset except the E5 research pair, every default-spawned process sits on its own core cell 0 (`process_runtime.py:739–750`).
- So an agent that declares reach `arena_size // 2` sees every enemy anchor at its first callback, and the first anchor it sees is the enemy's core base. The E2–E5 fixtures do exactly that: `e2_sniper` declares `reach = arena // 2` and takes the first single visible anchor as the enemy core (`tools/research/v6/e2/fixtures/agents/e2_sniper/agent.py:40–45`).

**Free information enables the forced line.** [DOC] The Phase 4A addendum records a deterministic tick-1 Seat-A core capture under competent global-reach play. On any parent where that line exists, the game ends before a choice can matter.

**The research parents that remove the forced line carry their own properties.** [DOC]
- The E3 primary (K = 2, λ = 1) makes continuous repairers provably uncapturable (E3-D9, E4-D9′, E5-D9).
- The E3 companion (K = 1, λ = 1) has no such immunity. Its companion reading of D7, draw-ification, is SUPPORTED (+0.131), and its last-mover skew is sharp.

**The current rules may already contain part of a choice.** [DOC] The pre-RC study measured an inverted-U win curve over declared reach at arenas 256–1024. Travelling mid-reach probes (35.4%) beat stationary maximum-reach probes (25.8%) there (§D.4). But the maximum-reach probe won only when it read the enemy core on its first callback, 49.5% of those matches against 0 of 184 otherwise. The record says that read was "decided by scheduling order, and it is 52.1%" (§D.5). That is the same seat and order effect later identified as the forced line. The current rules therefore contain a partial local-versus-global tradeoff, entangled with the forced line. This is Branch A's best existing evidence, and it is not disproven.

### B.3 What "smallest" means here

Size has six separate dimensions, and the candidates differ on each:

| # | Dimension | What is counted |
|---|---|---|
| S1 | Concept | New ideas an agent author must learn |
| S2 | Agent API | New action kinds, observation fields or context fields. Precedent: research-only additive members have never bumped `AGENT_API_VERSION` (`MatchContext.locality_reach`, `MatchContextV2.parameters`, and the v1 `MOVE` / `LOCAL_*` members; `agent_api.py:107–113, 157–173, 203–217`) |
| S3 | Engine | Modules whose behavior changes |
| S4 | Replay and result schema | New event types or header fields. The replay reader rejects an unknown event type (`replay.py:359`). |
| S5 | Distance from the stable control | Ruleset fields between the treatment and `bytefray-rules-6-research-scale`, the stable-equivalent research control |
| S6 | Instrument burden | New agents and analyzers the evaluation needs |

---

## C. Constraints Every Candidate Inherits

These come from committed records and current source. Each candidate in §D is checked against them.

| ID | Constraint | Source | Consequence for a new mechanic |
|---|---|---|---|
| **K1** | **The second-response privilege.** In an opening-pass contest, the tick's second mover responds after the first mover and neither writes the cell again that tick. So the second mover holds the cell at the single end-of-tick sample. Under forward order it is also the later responder in every pass. | [DOC] E5-R §E (`R-H2-PRIME`); E4-R §F.3 (H3); E4-DR §D.3 | [INFERENCE] Any new single-cell objective whose value is sampled once per tick goes to the tick's second mover when both sides contest it. Rotation then makes it alternate by tick parity. |
| **K2** | **The Q = CORE_SIZE boundary.** At `instr_per_tick ≥ 8`, a perfectly informed attacker can capture an earlier-scheduled, non-reacting victim within one action block. | [DOC] V3 closeout §1 (Q3) | A mechanic that lets an entrant act more than 8 times in one tick moves play above the boundary. |
| **K3** | **Hold × slot-limit immunity.** Under K = 2 with λ = 1, continuous repairers are provably uncapturable. | [DOC] E3-D9, E4-D9′, E5-D9 | A mechanic stacked on that parent inherits the immunity, against synthesis requirement D. |
| **K4** | **Free information is an unexcluded upstream cause.** | [DOC] E3-R §G.7; R4b §R ("The 12.5% D=1 maintenance figure excludes discovery cost and therefore depends on perfect information"); Stage 5 §O (Decision B, local detection); pre-RC §E.3(1) and §E.4(1) | Priced discovery was the premise of V4's disruption design (R4b) and of its detection decision (Stage 5). V4 shipped Stage 5's local detection, but at each process's freely declared reach. Sensing priced separately from action reach has never been tested as a Ruleset. |
| **K5** | **Monolith equivalence.** A process-level mechanic is strategic only if a monolithic controller paying the same cost cannot reproduce it. | [DOC] R2 §D, §J, §M (Decision A) | This is the test any deployment or process-economy mechanic must pass. |
| **K6** | **Bounded action reach disarms.** Bounded reach produced the "bulldozer effect". A blunt reach cap raised the tick-limit rate from 46.8% to 90.5%. | [DOC] Phase 4A §1.1 and §11.4 (V3 Phase 2); pre-RC §E.4(3) | Any information mechanic must leave action reach alone, or it becomes the "simple hard reach-cap fog" the synthesis does not resurrect. |
| **K7** | **Greed dominance.** Pure territorial expansion won 98.4% of 1v1 matches in V2 alpha 10. V3 found offense payoff "structurally opposed to defense viability with no compensating lever". | [DOC] Phase 4A §1.1; V3 closeout §1 (Q4) and §18 | A mechanic that taxes attack but not expansion, or pays in score, can tilt play toward greed. |
| **K8** | **Compatibility surfaces.** Research-only additive API members exist without a version bump. The replay reader rejects unknown event types. Ruleset field values are immutable once artifacts exist. | [SOURCE] `agent_api.py:107–113, 157–173, 203–217`; `replay.py:359`; the registrations' permanent obligations | A mechanic that needs a new event type needs replay-schema work. Every new action kind must be rejected under every other Ruleset. |

---

## D. Candidates

Each candidate is described at the level needed to judge it. None is specified. The format for each is: mechanism, the choice it creates, the case for opponent dependence, the requirements, inherited constraints, failure modes, footprint and verdict.

### D.1 Priced sensing (information and scouting)

**Mechanism.** Separate what a process can *see* from what it can *reach*.

- **Unchanged:** action reach stays as declared, and global READ/WRITE reach remains legal and free.
- **Changed:** a fixed detection radius limits passive enemy-anchor visibility, independently of action reach. Sensing itself stays passive and free. What costs actions is extending the area searched: that requires process movement, and MOVE competes for the same action budget as attack and defense.

Three variants:

| Variant | Mechanism | The price |
|---|---|---|
| **I-a: Ruleset detection radius** | `visible_enemy_anchor_addresses` uses one Ruleset-owned radius *d*, the same for every process, in place of each observer's declared reach. This is Stage 5's local-detection model, except that the radius is a Ruleset constant: Stage 5 set it equal to each process's action reach. | MOVE actions (sensors travel), and exposure: detection is symmetric at equal radius, so a sensor that sees an enemy anchor is itself seen. |
| **I-b: I-a plus a SCAN action** | A new research-only `ActionKindV2` member. For one action, it reveals enemy anchors beyond *d*. | One action per scan, independent of geometry |
| **I-c: Priced reach** | The declared reach reduces the process's share of the budget. | Throughput, fixed at declaration time |

I-b contains I-a: a scan is only worth buying if passive sensing is limited. So I-a is the minimal form. I-a already creates an opportunity cost, because every MOVE spent searching is an action not spent attacking or defending; SCAN is not needed to manufacture one. Stage 5 also rejected an explicit scan action as unjustified *given* local detection (Stage 5 §O). I-b is therefore held in reserve, for use only if movement-based discovery collapses into a search race or proves too dependent on geometry. It is not a starting point. I-c is a declaration-time choice with no in-match adaptation, so it fails C4 (§D.4).

**The choice it creates.** Spend actions on finding and tracking the opponent (moving sensors, or scanning under I-b), or on acting: attacking, disrupting, repairing, painting. Two secondary choices follow from it:
- where to station friendly processes as sensors;
- whether to move one's own anchors off the core, which is worth something once the opponent must re-find them.

**Why the better choice would depend on the opponent.** [INFERENCE; a hypothesis for the design review, not a finding]

- A static opponent needs finding once. Cores never move, so a core once found stays found.
- A mobile or evasive opponent must be found again and again to be disrupted.
- An approaching attacker is visible only within *d*, so early warning has to be bought.
- At equal radius, the sensor that finds the enemy is found too, so scouting exposes the scout.

No fixed scouting budget is obviously best against all four behaviors.

**Why it acts upstream of the forced line.** [SOURCE + INFERENCE]

- **What capture takes.** Capture requires the victim to own zero core cells at the end of a tick (`python_runtime.py:218`), and every core has 8 cells (`process_runtime.py:725`). A tick-1 capture therefore needs 8 WRITEs to the enemy core, the anchor hit on core cell 0 among them. That is the entire budget of Q = 8 (`config.py:21`).
- **What finding the core takes.** Seeded placement keeps cores at least 64 cells apart at arena 512 (`placement.py:52, 129`). With *d* below that separation, no enemy anchor is visible at spawn, and an Agent API v2 declaration cannot choose a starting position. Discovery-dependent play must then spend at least one action acquiring the enemy location: a MOVE, a SCAN under I-b, or a READ.
- **So priced sensing removes the canonical guaranteed tick-1 capture line for discovery-dependent play.** Once at least one action is spent acquiring the enemy location, fewer than eight actions remain for an eight-cell capture, whatever the disruption, capture or scheduler rules.
- **It does not make every conceivable tick-1 capture impossible.** WRITEs to unseen addresses stay legal, so a blind or lucky eight-write guess could in principle hit the core without discovering it first. The full design review must audit whether any free information channel, deterministic placement inference, or blind-targeting policy can bypass discovery.
- **What that makes possible.** Priced sensing can be tested **one Ruleset field** away from the stable-equivalent control. Valuable cells and investment cannot (§D.2, §D.3).

Whether a *delayed* form of the forced line reappears is open. Once an attacker has found a core, a victim still stationed on it can be hit by the same dual-purpose write. That is failure mode 5 below.

**Requirements.**

| | Assessment |
|---|---|
| A: opponent-dependent value | Plausible (above). The main risk is a search race (failure mode 1). |
| B: opportunity cost | Yes. An action spent moving a sensor to search is not spent attacking or defending. |
| C: adaptation | Yes by construction. The choice is how much observation to acquire, made during the match. |
| D: interaction | At risk of non-contact, but mitigated: action reach stays global, so once located, contact is available from anywhere. Must be measured. |
| E: topology | Aims at who beats whom through information advantage (scouting, evasion). Untested. |
| F: explainable | Yes: "you see enemy processes within *d* cells of your own." The spectator pipeline already derives `DETECTION_GAINED` and `DETECTION_LOST` from traced observations (`spectator_derivation.py:499–540`). |
| G: testable | I-a is one Ruleset field, with no new action kind and no change to the observation's shape. |

**Inherited constraints.**

- **K4:** it addresses the constraint directly.
- **K6:** action reach is not bounded, so this is not reach-cap fog. But if movement-priced search proves too expensive, I-a would behave like fog in effect. That is exactly what I-b exists to prevent.
- **K7:** the greed-tilt risk (failure mode 2).
- **K1:** it creates no new contested cell. The privilege stays in base contests once a core is found.

**Failure modes**, most serious first. [INFERENCE] Each becomes a design-review question or a kill criterion (§G.1).

1. **Search race.** If each side's best search policy is the same whatever the opponent does, the choice collapses into a geometry-and-seat race and fails requirement A.
2. **Greed tilt.** Painting territory needs no information about the opponent. Pricing sensing taxes attack but not expansion, so greedy painting may come to dominate (K7).
3. **Non-contact or stasis.** The pre-RC study found short-reach play "engagement without decision": in 95.8% of short-reach-only matches no core was ever touched, and 99% were draws (§E.1, H8). That finding concerned short *action* reach, which I-a leaves alone, but the analogous flag must be carried: tick-limit share, and matches with no hostile core contact.
4. **One-shot discovery.** Cores never move. If the scouting choice exists only until each side has found the other's core, the choice may be real but short-lived. The design review must check whether tracking anchors, for disruption, keeps it alive.
5. **A delayed forced line.** On a parent with whole-tick disruption (the stable-equivalent control), a victim that stays on its core after being found can still lose to the dual-purpose write, one or more ticks later. Moving off the core then has a price. That is the choice working, but it has to be verified, not assumed. This is the argument for also running a λ = 1 companion arm (§G.2, decision 3).
6. **The READ side channel.** READ returns the value and owner of any cell within action reach (`process_runtime.py:1245–1267`). A searcher reading every 8th cell will hit a contiguous 8-cell core within 64 reads at arena 512 (arithmetic). Core discovery thus stays priced but bounded, which protects C5. Since READ also reveals the owner, a defender can plant decoy `0xCE` cells. The design review must decide whether this channel is acceptable as part of the price.
7. **The fixtures go blind.** Every E2–E5 fixture takes the enemy core from the first single visible anchor. Under I-a none of them can find it, so a new agent family is required (§F).
8. **New seat artifacts.** Detection is re-evaluated before every callback, and the first mover of a tick acts first. Whether the second mover gains from seeing the first mover's scout must be measured with seat metrics.

**Footprint.**

| | I-a | I-b |
|---|---|---|
| S1 concept | One: a sensing radius separate from reach | Two: the radius, and scanning |
| S2 Agent API | None required. *d* can be exposed in `MatchContextV2` additively, as `locality_reach` was in the v1 context. | A new `ActionKindV2` member, research-only, rejected under every other Ruleset (K8) |
| S3 engine | A `RulesetPolicy` field and its validation; the radius used in `_visible_enemy_anchors` | Also `_validate_v2_action`, action execution and the trace vocabulary |
| S4 schema | None. Anchors are already in the replay, and *d* belongs to Ruleset identity. | None if the scan result stays inside the observation |
| S5 distance | 1 | 2 fields, or 1 if bundled as one mode |
| S6 instruments | A new agent family (the fixtures are blind), a strategy-family analyzer, and detection telemetry, largely derivable from the trace | The same, plus scan accounting |

**Verdict: SELECT the family, with I-a as the minimal form.** I-b is the design review's fallback if I-a's price proves too geometry-bound.

### D.2 Contestable valuable cells

**Mechanism.** A small set of neutral cells, at positions both entrants know, whose ownership pays the owner every tick. There are two payout variants:

- **V-a:** the payout is score;
- **V-b:** the payout is extra actions.

**The choice it creates.** Taking and holding the cells, attacking, and defending all compete for the same actions. This makes Phase 4A §11.5's greed / rush / defense triangle explicit.

**Why the better choice would depend on the opponent.** [INFERENCE]
- Against an opponent that never contests a cell, holding it is nearly free: one write keeps it until someone overwrites it.
- Against an opponent that does contest it, holding it costs actions every tick.
- Attacking is worth more against an opponent that has spent its actions on cells.

**Requirements.**

| | Assessment |
|---|---|
| A | Plausible. |
| B | Yes. |
| C | Yes: the positions are public, and READ reveals who owns a cell. |
| D | Strong: it adds a contact point that is not a core. |
| E | Possible. |
| F | Very explainable: highlighted cells. |
| G | Needs several parameters: count, placement and payout. |

**The objections that make it the reserve, not the first choice.**

1. **K1 applies by construction.** [INFERENCE from E4/E5]
   - **What happens.** If both entrants write a valuable cell every tick, the second mover holds it at every end-of-tick sample. Rotation then gives it to each side on alternate ticks, so a fully contested cell splits evenly, and the actions spent contesting it buy nothing.
   - **What still works.** Value flows only from contests one side declines. That is still a choice (C3), but the mechanic's dynamics would largely be the surviving mechanism under a new name.
   - **The cost of avoiding it.** Payout rules that avoid a single end-of-tick sample, such as "held for a whole tick", add a second ownership rule.
2. **It needs a parent without the forced line.** On the stable-equivalent parent, a tick-1 capture ends the match before any cell pays out. Testing valuable cells therefore means stacking them on a research parent that removes the forced line: the E3 companion's λ = 1, say. That puts the treatment 2 fields from stable, one of them itself unpromoted (S5 = 2). The parent also brings its own properties (K3, or the companion's draw-ification).
3. **The payout currency has no good option.**
   - **Score (V-a)** pays only at the tick limit and cannot change a capture outcome, which invites stasis. It is the synthesis §G.5 warning in miniature: it changes how matches resolve, not who wins them. It also feeds the greed channel (K7).
   - **Actions (V-b)** push play above the Q = CORE_SIZE boundary (K2), and they snowball: the leader earns more actions.
4. **Placement fairness.** Seeded cores are not symmetric. The cells must be placed fairly for both seats, which needs a new placement rule and carries a seat-artifact risk.

**Footprint.**
- `RulesetPolicy` fields for count, placement and payout;
- a placement rule;
- a scoring or quota hook;
- a context field for the positions (additive);
- a replay header field, or a documented derivation;
- a contest analyzer.

This is S5 = 2 at best, and it is broader in S3 and S4 than I-a.

**Verdict: RESERVE.** It is the best candidate on requirements D and F, and it composes naturally with priced sensing. Public cells are, however, free information about where the opponent will be, so that interaction must be designed, not assumed. It is not a first mechanic, because of K1, the forced-line dependency and the payout dilemma.

### D.3 Investment and deployment

**N-a: Action banking or interest.** Give up actions now to have more later.

- **The choice:** investing against acting, the classic greed-versus-rush split.
- **Objections:**
  - A banked burst lets one entrant act more than 8 times in a tick, which is K2. It rewards whoever banks and then strikes first.
  - Interest compounds into a snowball.
  - On any parent with the forced line, rushing dominates outright.
  - v2 has no pass action, so banking needs a new action kind (S2). Q stops being constant per tick, which changes every per-tick budget guarantee the E3–E5 instruments relied on, such as the λ = 1 minimum of executed actions (S3).
- **Verdict: REJECT as a first mechanic.**

**N-b: Deployment, or replication.** Create a process during the match, at a cost.

- **What R2 found.** [DOC] Under the model then current, with global reach and no spatial anchors, R2 found that dynamic process economies "offer exactly zero irreducible strategic capability". A monolith paying the same cost can reproduce them (§J). R2 rejected them (§M, Decision A).
- **What the spatial model changes.** Processes now have anchors, so a deployed process would buy a *location*: a new sensing origin and a new, separate disruption target. [SOURCE] But the fixed roster already provides any number of locations at declaration, for free, and all processes share one budget of Q = 8. So deployment buys locations, not actions (`process_runtime.py:853–866`).
- **What locations have been worth.** [DOC] Extra locations were an exploit under whole-tick denial (E2-R §J; E2-H3e, "unchanged from V4"). They stopped paying under λ = 1 (E3-D5 REFUTED; E3-R §F.6).
- **What a real choice would take.** The free roster would have to be restricted, for example to one process at start. That is a breaking change to declaration semantics for every agent under that Ruleset.
- **Footprint: the largest of any candidate.** It needs a new action kind, lifecycle and activation timing, the scheduler cursor, quota rounding, and a process list in the replay that changes mid-match. R2 §K warns of "spawn storms, quota rounding exploits" and visualizer burden.
- **Verdict: REJECT as a first mechanic; keep it catalogued.** If priced sensing succeeds, locations become worth paying for, since sensors would then have real value, and deployment could be reconsidered on that footing.

### D.4 Considered and set aside

| Mechanism | Why it is not a Branch B candidate | Residual use |
|---|---|---|
| Delayed or degraded initial visibility (pre-RC §E.4(2)) | Imposed, not chosen; it fails requirement B | **Use it as a control arm for D.1.** It removes the tick-1 read of the enemy core without creating any choice, so it separates "the forced line removed" from "a choice created". |
| A hard reach cap | Disarms play (K6) | None; not resurrected |
| Priced reach (I-c, pre-RC §E.4(3)) | Fixed at declaration, so there is no adaptation during the match (C4). The pre-RC study ranked it below a separate detection radius. | None as a first mechanic |
| Fortified or hardened cells, where ownership needs several writes | Creates immunity (requirement D). V3 found no lever that compensated defense. It would be a new core-ownership rule. | None |
| Immutable special cells (Phase 4A §11.1) | Immunity | None |
| Anti-stasis mechanisms: shrinking arena, environmental sweep, territory decay | Act on how matches end (requirement E), not on choice | Later, once a mechanic with real choices exists |

### D.5 The null alternative: Branch A

This is no mechanic: study adaptive or searched agents under the current rules. It remains legitimate for two reasons: the current rules' partial information tradeoff (§B.2), and the E5 design review's untested inference about re-contesting a cell within a tick (synthesis §H).

The strategy-family method of §F serves both branches. Run on the chosen parent Ruleset as a control, it measures whether that parent already contains a choice. That is Branch A's question, answered for one Ruleset as a by-product of Branch B.

---

## E. Comparison

"Open" means plausible but untested, and "risk" means a named failure mode that must be measured. "No" means that on the records and source the candidate does not meet the requirement.

| | I-a detection radius | I-b + SCAN | V-a cells, score | V-b cells, actions | N-a banking | N-b deployment | Branch A |
|---|---|---|---|---|---|---|---|
| A: opponent-dependent value | open (risk: search race) | open (risk: search race) | open (K1 parity split) | open (K1) | open | open | open |
| B: opportunity cost | yes | yes | yes | yes | yes | yes | exists, entangled with the forced line |
| C: adaptation | yes | yes | yes | yes | yes | yes | yes, if the agents adapt |
| D: interaction | risk (non-contact) | better than I-a | risk (stasis) | yes | risk (burst) | open | as now |
| E: topology | open | open | risk (resolution only) | risk (snowball) | risk (snowball) | open | as now |
| F: explainable | yes | yes | yes | yes | moderate | poor (lifecycle) | as now |
| G: testable | yes, 1 field | 1–2 fields and a new action | 2+ fields and placement | 2+ fields and placement | new action, variable Q | largest | no Ruleset change |
| K1 (parity) | not created | not created | inherited by construction | inherited by construction | — | — | — |
| K2 (Q > 8) | no | no | no | **crosses** | **crosses** | no | no |
| Forced line | **removes the guaranteed, discovery-dependent tick-1 line** | removes the guaranteed, discovery-dependent tick-1 line | needs a parent that removes it | needs a parent that removes it | needs a parent that removes it | needs a parent that removes it | present |
| S2 Agent API | none | new action kind | context field | context field | new action kind | new action kind and lifecycle | none |
| S5 distance from stable | 1 | 1–2 | 2+ | 2+ | 2+ | 2+ | 0 |
| **Verdict** | **SELECT (minimal form)** | fallback within D.1 | **RESERVE** | reserve variant, weaker | REJECT (first) | REJECT (first) | open |

The decisive column is the forced line. Priced sensing is the only candidate that can be tested against the stable-equivalent control with one field changed, because it removes the free information the canonical forced line depends on. Every other candidate must first borrow a research parent that removes it. That doubles the distance from stable and imports that parent's own properties (K3, or draw-ification).

---

## F. The Evaluation Every Branch B Mechanic Needs

**This is a requirement on the next design review, not a pre-registration. It sets no threshold.**

**Why the frozen fixtures cannot judge a choice.** The E2–E5 fixtures never choose. When E5 made a full disrupt-plus-sweep cost one extra action, the cost appeared as lost coverage, not as a decision (E5-R §F.2, §J; synthesis §G.3). A choice mechanic judged only against those fixtures would repeat that.

**The strategy-family test.** It has five parts:

1. **Policy family.** Agents identical in everything except a declared allocation parameter θ over the mechanic's uses. For priced sensing, θ might be a scouting budget per tick, a sensor placement, or whether anchors leave the core. θ is exposed through agent parameters, the existing `MatchContextV2.parameters` channel, so one agent source yields the whole family.
2. **Opponent styles.** A fixed set of styles the family is scored against: static, mobile, rushing, greedy.
3. **At least one adaptive agent.** It sets θ from what it observes of its opponent. This is what tests C4: adapting should pay.
4. **Controls.**
   - The parent Ruleset, where the choice should be absent or degenerate.
   - For D.1, a delayed-initial-visibility arm (§D.4). It removes the tick-1 read of the enemy core without adding a choice.
5. **Signatures, to be made exact before any freeze:**
   - no θ dominates;
   - the best response to an opponent's θ′ changes with θ′;
   - the adaptive agent does at least as well as every fixed θ against the mixed field;
   - pathology flags recorded whatever else holds: stasis, non-contact, new immunity, seat artifacts, greed dominance, and the reappearance of the forced line.

**Evidence rules carried forward** (synthesis §G.8; E5 Revision 1 §R5–§R6; E5-R §B, O-MIN-SB):
- report n_distinct beside every count;
- compute each metric per seed, then take the unit median;
- require a minimum number of independent units before a census means anything;
- define every band and threshold exactly, before the freeze;
- make the interpretation table exhaustive, with explicit NEITHER rows and a "none" outcome.

The policy family must include agents whose behavior varies with the seed. Otherwise most units rest on one trajectory, as they did in E4 and E5.

**One tool for both branches.** The same family, run on the parent Ruleset, answers Branch A's question for that parent.

---

## G. Recommendation and Open Decisions

### G.1 Recommendation

**Take priced sensing (§D.1) to a full design review, in its minimal form (I-a).** That review, like this one, implements nothing, and it too ends in a verdict. It must keep these outcomes reachable:
- priced sensing is rejected;
- the reserve candidate is taken up;
- Branch B returns "no mechanic yet", which sends the program toward Branch A.

**Kill criteria.** The design review must write these as reachable ABANDON conditions. Any one, established under the eventual frozen instrument, rejects the candidate:

1. **Search race:** the best-response map over the policy family is constant (§D.1, failure mode 1).
2. **Greed dominance:** a sensing-free painting policy dominates the family (failure mode 2).
3. **Non-contact or stasis:** tick-limit endings, or matches without hostile core contact, rise materially over the parent (failure mode 3).
4. **The forced line returns in a delayed form**, against a victim that stays on its core (failure mode 5).
5. **A new seat artifact** (failure mode 8).

A clean negative under these criteria is a successful result of the method, not a failure of the program.

### G.2 Decisions for the research lead, before the design review

The recommended option is listed first in each case.

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| 1 | Candidate family | Priced sensing | Contestable valuable cells now; or no Branch B mechanic yet, and Branch A instead |
| 2 | Variant | I-a (a fixed detection radius, with search priced through movement); I-b only if movement-based discovery collapses into a search race or proves too geometry-bound | Start from I-b |
| 3 | Parent Ruleset | Primary arm on `bytefray-rules-6-research-scale`: one field from stable, testing directly whether priced sensing removes the forced line. A companion arm on the λ = 1 research parent (`bytefray-rules-6-research-disruption-slot1`), one field from its parent, to separate failure mode 5 from whole-tick denial, as E3–E5 used companions. | A single arm on either parent |
| 4 | How the radius *d* is chosen | Fixed a priori from geometry, below the 64-cell minimum core separation at arena 512, and never tuned against outcomes. This follows the research-integrity rule that discovering a parameter is kept separate from testing it. | Characterize *d* on control data first, as its own disclosed step |
| 5 | Arena | 512: the E2–E5 arena and the Designer default. The mechanic's sensitivity to arena size is characterized as its own disclosed step, not assumed. Pre-RC found the reach win curve changes shape with arena size: an inverted U up to 1024, monotone at 4096 (§D.5). | Several arenas from the start |
| 6 | Agents | A new parameterized family and at least one adaptive agent (§F). The E2–E5 fixtures stay unchanged as historical instruments; they are blind under I-a. | Adapted copies of the E2–E5 fixtures |
| 7 | When to probe | Only after the design review fixes the variant and parent: a scratch probe at non-matrix seeds, with its values disclosed as priors, as in E2–E5 | Probe during the design review |
| 8 | Whether to expose *d* to agents | Yes, as an additive `MatchContextV2` field (precedents: `MatchContext.locality_reach`, `MatchContextV2.parameters`), so agents can plan search instead of discovering the rule by trial | Document it in the Ruleset only |

### G.3 What the reserve and the rejected candidates need to come back

- **Valuable cells (§D.2)** come back if priced sensing is rejected on the search-race or greed criteria, since contested cells directly target interaction. They also come back, in combination, if priced sensing succeeds. In either case the design must first answer K1: a payout rule that does not simply reproduce the second-response privilege.
- **Deployment (§D.3)** comes back if priced sensing succeeds and sensors become valuable. It would still need a monolith-equivalence argument (K5), and a decision on whether to restrict the free roster.
- **Banking (§D.3)** stays out while K2 holds. It would need an explicit argument that play above the one-block capture boundary is healthy.

---

## H. What This Review Does Not Claim

- **No result.** Every statement that a mechanism would create an opponent-dependent choice is [INFERENCE]. No match, probe or prototype was run.
- **Not a pre-registration.** No threshold, population or interpretation row is set.
- **No promise that priced sensing works.** It is the best-placed candidate to test first, with reachable kill criteria.
- **No permanent rejection.** Valuable cells, deployment and banking are set aside as *first* mechanics only.
- **No change to any E2–E5 conclusion.** K1–K3 are quoted and read as constraints, not reinterpreted.
- **No disproof of Branch A.**
- **No selection of *d*, the parent or the variant.** These are the research lead's decisions in §G.2.

---

## Appendix. Sources

**Committed records** (`docs/research/v6/` unless stated):

- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) §G, §H, §I.2
- [`V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md) §D, §F.6, §F.8, §G.7
- [`V6_E4_MIRRORED_PASS_ORDER_RESULTS.md`](V6_E4_MIRRORED_PASS_ORDER_RESULTS.md) §D, §F.3
- [`V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md) §D.3
- [`V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md`](V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md) §B, §E, §F.2, §H.8, §J
- [`V6_E5_DESIGN_REVIEW_REVISION_1.md`](V6_E5_DESIGN_REVIEW_REVISION_1.md) §R5–§R6
- [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md) §1.1, §1.2, §11, Research Integrity Addendum
- [`docs/archive/v3/V3_RESEARCH_CLOSEOUT.md`](../../archive/v3/V3_RESEARCH_CLOSEOUT.md) §1, §17–§19
- [`docs/archive/v4/V4_DYNAMIC_PROCESS_ECONOMICS_RESEARCH.md`](../../archive/v4/V4_DYNAMIC_PROCESS_ECONOMICS_RESEARCH.md) (R2) §D, §J, §K, §M
- [`docs/archive/v4/V4_PROCESS_DISRUPTION_RESEARCH.md`](../../archive/v4/V4_PROCESS_DISRUPTION_RESEARCH.md) (R4b) §K, §M, §R
- [`docs/archive/v4/V4_PROCESS_VISIBILITY_RESEARCH.md`](../../archive/v4/V4_PROCESS_VISIBILITY_RESEARCH.md) (Stage 5) §B–§E, §H, §N, §O
- [`docs/archive/v4/V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md`](../../archive/v4/V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md) §A, §C.1, §D.4–§D.5, §E

**Source at `3019bc7`:**

- `engine/src/battle_engine/agent_api.py:107–113, 157–173, 194–246`: the v2 contract and the additive precedents
- `engine/src/battle_engine/process_runtime.py:281–290` (reach validation), `:725` (core size), `:786–826` (visibility), `:828–866` (quota), `:957–970` (v2 action validation), `:1245–1311` (READ, WRITE, disruption)
- `engine/src/battle_engine/python_runtime.py:218` (core capture)
- `engine/src/battle_engine/config.py:21` (Q = 8), `scoring.py` (alive, territory, kill)
- `engine/src/battle_engine/placement.py:52, 129` (minimum core separation)
- `engine/src/battle_engine/replay.py:359` (unknown event types rejected)
- `engine/src/battle_engine/spectator_derivation.py:499–540` (detection events)
- `tools/research/v6/e2/fixtures/agents/e2_sniper/agent.py:40–45` (global reach; core inferred from the first visible anchor)
