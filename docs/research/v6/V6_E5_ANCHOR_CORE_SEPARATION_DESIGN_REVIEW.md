# Bytefray V6 E5 (proposed): Anchor/Core-0 Separation — Design and Adversarial Review

This is a design review only.

- **Repository.** No repository file was modified. Nothing was committed or pushed, no Ruleset was created and no E5 matrix was run. `git status --porcelain` was empty before and after.
- **Probe.** All probe code and output live in the session scratchpad.

**Evidence tiers.**

| Tier | Meaning |
|---|---|
| [SOURCE] | Current source at `ecf2769`. |
| [CORPUS] | Frozen E2–E4 figures, as recorded in the committed results, freeze and design-review records. I did not re-read the corpus files themselves. |
| [RUN] | The unmodified engine, run under the E3 primary and E4 mirrored Rulesets. The scratch harness only observed it: it wrapped `VM._wr8` and `apply_core_capture` with pass-through hooks. |
| [PROBE] | A scratch-only patch that moves every process's initial anchor to `core_base − 1` right after controller construction. It also used scratch "offset-aware" copies of the inferring fixtures, but only as an inertness check. |
| [INFERENCE] | Reasoning from the tiers above. |

**Probe exposure.**

- **Seeds.** 42, 1001, 1002 and 1003, all outside matrix seeds 1–32.
- **Runs.** About 170 full-length matches on named scenarios, plus 8 four-tick traces. No grid was run.
- **Harness check.** Under [RUN] the harness reproduces every frozen deterministic control FMA (C-E4) and every frozen deterministic T-E4 FMA that it re-ran.
- **Status of the values.** Probe values are priors to be falsified. No threshold in this review came from them.

---

## Verdict in brief

**REDESIGN.** The anchor/core question is worth asking. But the manipulation as posed cannot answer it cleanly. The posed design is an unspecified offset, applied to E4's population, with OPENING-ONLY treated as one class, MULTI-PASS used as a control, and an optional 2×2. A smaller corrected design is causally isolated.

1. **The frozen ecology encodes co-location in how it finds the enemy core.** [SOURCE]
   - The observation never exposes an enemy core address.
   - Every core-attacking fixture takes the enemy core to be at the first single enemy anchor it observes. The probe instead attacks `anchor[0] + step`.
   - Separation therefore also changes which cells the attackers write. That is an information/targeting change, not the dual-purpose-write change E5 is after.
2. **One offset, and only one, neutralizes that confound for most fixtures: `anchor = core_base − 1`.**
   - At d = −1, each list-first sweeper's wrong core window differs from the true core only in list positions that the Q = 8 budget never reaches. That is a proof (§F, P5). [PROBE] It was confirmed byte-for-byte in 37 of 37 frozen-versus-offset-aware comparisons.
   - It does **not** hold for `v4_probe` or `e3_jam_sniper`. Their co-location dependence is built into their target sets, so they must be excluded.
3. **About half of OPENING-ONLY cannot count as evidence.** In anchor-only contests, where the attacker never attacks the core except through the anchor hit, separation removes the contest *by theorem*. Those units become a manipulation check, not a hypothesis test.
4. **MULTI-PASS is not a negative control.** Separation takes the anchor hit's free core write out of every disrupt-first sweep, which shifts pass alignment and per-tick coverage. [PROBE] FMA moved −2.0 → −3.0, −3.5 → −1.5 and −1.0 → −0.75 under forward order.
5. **Unit-level FMA is the wrong primary instrument.** It mixes directed contests and sits on band boundaries under this treatment. The primary measure has to be **directed base parity (BP)**: for each victim's core cell 0, whether its second-mover ownership advantage survives.
6. **The 2×2 adds no discriminating prediction for the E5 question.** [PROBE] Mirrored + separated equals forward + separated in every opening-only unit. The design should be single-factor, with a small K = 1 companion.
7. **[PROBE] prior, to be falsified.**
   - Where the base is attacked explicitly (sweep-backed), the second mover's base privilege **survives** separation unchanged: BP 1.0 → 1.0, FMA −0.5 → −0.5 and −1.0 → −1.0.
   - Where the anchor hit was the only contact, the privilege vanishes.
   - The expected registered answer is therefore that co-location supplies *contact*, not *privilege*. That would be a clean negative for the co-location hypothesis.

---

## A. Baseline

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `ecf27693702aaca11bae014e66a6f25bc26f220e` ("docs(v6): record the E4 mirrored-pass-order results") |
| Upstream | After `git fetch origin v6-research`, 0 ahead and 0 behind |
| Tree | Clean before and after (`git status --porcelain` empty) |
| Python / platform | 3.13.14, repo `.venv`, Windows 11 (10.0.26120) |
| `ecf2769` present | Yes, as HEAD. `V6_E4_MIRRORED_PASS_ORDER_RESULTS.md` is committed. |
| E4 status | Complete: 15,232 matches, analysis `2fa52a2e…`, interpretation v3 `4a2162ce…`. No gameplay experiment follows it in history. No E5 file, Ruleset, tooling or spec exists (`docs/specs/` has none). |
| Records read | E4 results, E4 design review, E4 registration and freezes v1–v3 (via the results record and the freeze docs), E3 results and addendum, the E2 results summary, ROADMAP (the E4 entry), FUTURE_PLANS (the E4 entry), and the Phase 4 methodology outline |
| Source read | `process_runtime.py` (whole file), `ruleset_policy.py` (policy and E2–E4 Rulesets), `placement.py`, `agent_api.py` (`ObservationV2`, `MatchContextV2`), `python_runtime.apply_core_capture`, `vm._wr8`, all 11 fixture `agent.py` files and the fixture README, `e2/capture_analyzer.py` (core rebuild and inference audit), `e4/contest_classes.py`, `e3/d9_gate.py`, `client/…/replay_status.py`, `spectator_derivation._seed_state` |

---

## B. Current anchor/core semantics

### B.1 Placement and spawn [SOURCE]

- **Core base.**
  - `resolve_direct_match_starts` → `seeded_seat_starts` (`placement.py`) draws each seat's start from a SHA-256 counter stream over (seed, arena, entrant count, separation, seat, attempt).
  - The minimum separation is 64 at A = 512, and no `random` stream is involved.
  - `ProcessMatchController.__init__` sets `start = spec.start % A`, `core_cells = start … start+7`, and `EntrantState(core_base=start, pc=start, region=(start,start))`. It then seeds the 8 cells with `0xCE`, each owned by the entrant (`process_runtime.py:714–736`).
  - **Core cell 0 is `core_base`.**
- **Process anchors.**
  - `from_python_entrants` builds every declared process with `initial_position=None` (`586–601`).
  - In `__init__`, `if p.position is None: p.position = start` (`741–742`).
  - So **every process of every Agent API v2 entrant spawns on core cell 0**, whether the entrant has one process or several. There is no exception in the match or evaluation paths. Only hand-built `ProcessEntrantSpec`s with an explicit `initial_position` differ, for example E4's `manipulation_gate`.
- **Storage.** Anchors are stored directly in `ProcessInstance.position`, not derived. Only MOVE changes them (`1227–1237`), relative to the current position. The spread fixtures move `s1`/`s2` (`p1`/`p2`) once, by ±16–64. No other fixture moves.
- **RNG.** `derive_agent_seed(seed, slot, agent_id, 2)` and `MatchContextV2` are fixed before placement, and neither reads an anchor (`394–423`).

### B.2 What a WRITE does [SOURCE, `process_runtime.py:1263–1305`]

1. The reach check measures from the acting process's **position**.
2. `vm._wr8(target, v, owner=writer)`: one memory mutation. It changes ownership and records the tick diff.
3. Then, in the same code path, a **position-equality side effect** runs. Every *live enemy* process whose `position == target` gets `disrupted_until_tick = t+1` and, under λ = 1, `disruption_slots_left = 1`. Friendly processes are immune.

- **Where disruption comes from.** Disruption depends only on the target's equality with a process position. It does not depend on ownership, on the cell's value, or on whether the cell is a core cell.
- **A WRITE to core cell 0** changes ownership only, unless a process sits there.
- **Capture** (`python_runtime.py:273–311`) reads ownership of `core_addresses(core_start)`, which is anchor-independent.
- **Scoring** (alive, plus ⌊owned/64⌋) is anchor-independent.

**So today one WRITE to an enemy anchor does both jobs through two mechanisms in one call:**

- the ownership flip of enemy core cell 0;
- the disruption of every enemy process sitting there, which is all of them at spawn.

### B.3 Information [SOURCE, `agent_api.py:195–233`, `process_runtime.py:780–820, 1093–1108`]

- **`ObservationV2` fields:**
  - `self_anchor`;
  - `own_core_base` and `own_core_size`;
  - `visible_enemy_anchor_addresses` (enemy positions within reach of any unsuppressed own process, evaluated per callback);
  - the previous READ's value and owner.
- **No enemy core address** appears in any observation or context field.
  - The only free channel to it is the co-location invariant.
  - The costly channel is READ, which returns an owner, or the `0xCE` beacon value.
- **When an enemy anchor is first visible:**
  - The tick-1 first mover sees it at its first callback, before any action in the match.
  - The second mover first sees it after the first mover's chunk 1 (two actions), so after any MOVE in that chunk.
- **Anchors elsewhere.** The replay publishes every process's anchor at every tick boundary, tick 0 included (`966–977`).

### B.4 The opening pass, traced

Seed 42; Seat A's core is at 485 and Seat B's at 203. `–` is an offer lost to suppression; `[a]` marks an anchor hit and `[c0]` a write to the enemy's core cell 0. The E3 primary Ruleset: chunk 2, rotation, λ = 1, K = 2.

**Sniper (A, first mover) v min guard (B), tick 1.** [RUN] / [PROBE]

```
control   F: 203[a+c0] 204 | L: – 485[a+c0] | F: – 205 | L: 203(own base) 486 | F: 206 207 | L: 487 488 | F: 208 209 | L: 489 490
separated F: 202[a] 203[c0] | L: – 484[a]   | F: – 204 | L: 203(own base) 485[c0] | F: 205 206 | L: 486 487 | F: 207 208 | L: 488 489
```

- **The base contest.** In both arms the min guard, as second mover, retakes its base after the sniper's last write to it, and holds the base at the sample. At tick 2 the roles swap and it loses the base.
- **Both arms:** BP_B = 1.0, FMA −0.5. **Separation moves the sniper's core-0 write from its first action to its second. It does not change who wins the exchange.**

**Disrupt guard (A) v guarded painter (B), tick 1.**

```
control   F: 203[a+c0] 485(own) | L: – 485[a+c0] | F: – 486 | L: 203(own base) 202(paint) | …   → A 7/8, B 8/8; mirrored next tick
separated F: 202[a] 485        | L: – 484[a]    | F: – 486 | L: 203 202 | …                   → 8/8 and 8/8 every tick
```

- Neither fixture ever writes the enemy core except by the anchor hit.
- **Under separation the contest does not weaken. It ceases to exist.** FMA goes −1.002 → −0.009 and BP goes 0.99 → 0.0.

**Sniper (A) v disrupt guard (B), tick 2 (F = B).** This one is MULTI-PASS.

- **Control.** The disrupt guard's anchor hit takes the sniper's core cell 0, and its sweep of its own core runs one cell ahead of the sniper's. The guard ends the tick holding 3 cells. FMA −2.0.
- **Separated.**
  - The guard's hit no longer touches the sniper's core, so the sniper holds 8/8.
  - The sniper now needs 9 targets (anchor plus core 0–7) but gets 7 actions, so it sweeps core 0–5. The guard ends the tick holding 2 cells.
  - FMA −3.0.

**Guarded-painter mirror.** Control: FMA −0.989, and a capture at tick 93. Separated: 8/8 each until painting fronts arrive, FMA −0.006, and a tick-limit score win instead of a capture.

### B.5 Inventory of places that assume `anchor == core_base` [SOURCE]

| Location | Assumption | Impact of separation |
|---|---|---|
| Fixture README rule and 6 fixtures | enemy core := the first single visible enemy anchor | The attack window is shifted by d. It is inert only at d = −1 (§F, P5). |
| `v4_probe` | targets `anchor[0] + step`, with a persistent 0–7 cycle | The target set is anchor-relative, so it never hits core cell 7. Not inert. |
| `e3_jam_sniper` | attacks `core + 1 + cursor % 7`, skipping cell 0 because jam hits cover it | Its coverage policy is authored for co-location. Not inert. |
| `e4/contest_classes.py` | "writes the enemy anchor, which is enemy core cell 0" | The E4 class definition is co-location-dependent, so it cannot label treatment mechanics. |
| `e2/capture_analyzer.py` `CoreInference` | its `correct` flag compares the inferred base with the true base | Under separation it reads `False` by construction. It is **reported, never asserted** (`e3/action_parity.py:342` only passes it through). |
| `EntrantState.pc` / `region` | hold the core base (a legacy field in the replay) | The analyzers rebuild cores from `pc` plus the seeding diffs. **`pc` must stay `core_base`.** |
| Local reach | reach is measured from the anchor | At `base − 1`, core cell 7 is 8 cells away. Agents with reach < 8 would lose it. All fixtures have reach 256. |
| Client `replay_status`, spectator derivation | describe a "core-anchor", but derive the core from the tick-0 seeding diffs | Robust to separation. Only the wording is conflated. |
| Movement, seeded placement, core-overlap guard, capture, scoring, schemas, evaluation identity | none | Unaffected |

---

## C. E2–E4 evidence that constrains E5

- **E4 H3 and §F.3.** [CORPUS] All 14 OPENING-ONLY P-PAR units kept their **second-mover** swing privilege under mirrored order (FPS about 1 → about 0), and 13 of 14 STAY. The privilege therefore does not follow the final chunk.
- **E4 review §D.3 and §E.3.** [SOURCE] The opening privilege is "second response in the only exchange", and r₁ belongs to the second mover under every rotation-preserving order. Co-location is why the anchor hit *is* a core-0 write.
- **E4 review §D.2.** [CORPUS] 257 of E3's 353 last-leaning stalemate cells (73%) are opening-pass anchor contests.
- **E4 FOLLOWS-FINAL, disrupt guard ↔ min guard.** [CORPUS] This is a multi-pass pairing, and it is relevant to Challenge 5.
  - [PROBE] Under separation its forward FMA goes −3.5 → −1.5, because the min guard's base privilege disappears: the disrupt guard's hit on the min guard's base was anchor-only.
  - Its mirrored FMA stays at +0.5.
- **E4 H4, masking.** [CORPUS] K = 2 hides outcome effects that K = 1 exposes (128 of 640 against 0 of 640).
- **E3 D6.** [CORPUS] The jam sniper's capture of the min guard rests on jam hits that are *also* core-0 writes. This is the coupling in its purest form, but it can only be tested with a fixture that is excluded here (§H).
- **E4 S-9.** [SOURCE, CORPUS] `e2_counter` is identical to `e2_greedy_painter` under λ = 1.
- **E4 evidence strength.** [CORPUS] 17 of 18 MULTI-PASS units are deterministic. The 6 rate-eligible P-PAR units are all RNG-bearing (painter or spread) OPENING-ONLY units.
- **E4 §F.8.** [CORPUS] E4's own probe **mispredicted H2** (it predicted 0 flips; the matrix found 2 of 18 FOLLOWS-FINAL). Probe priors do not substitute for a registered run.

---

## D. Causal hypothesis

**Variable.** Whether the cell an entrant's processes spawn on is one of that entrant's own core cells. Equivalently: whether one WRITE can both disrupt a never-moved process and flip ownership of the victim's core cell 0.

The unit of the question is the **directed base contest**: attacker X against victim Y's core cell 0, which Y repairs.

- **Sweep-backed (SB).** X also attacks Y's core explicitly: X has an enemy-core sweep *and* X's inference of Y's core succeeded.
- **Anchor-only (AO).** X touches Y's core only through the anchor hit.

**Two competing mechanisms:**

- **H-COLOC.** The dual-purpose write carries the second mover's base privilege. Decoupling removes the privilege in SB contests too.
- **H-RESP.** The privilege is the second response in the first exchange on the base. Co-location only supplies the contact:
  - AO contests vanish (by theorem);
  - SB contests keep the privilege, because the exchange moves one action later and stays inside the second mover's early passes.

**What E5 is not asking.** It is not asking whether moving anchors changes matches. That is trivially true, through the AO theorem and through coverage shifts.

---

## E. Candidate treatment designs

| Candidate | Exact variable | Accidental changes | RNG | Agents | Multi-process | Disposition |
|---|---|---|---|---|---|---|
| **A(−1)**: `anchor = (core_base − 1) mod A` for every default-spawned process | spawn cell ∉ own core; anchor hits never flip core ownership | Anchor-to-enemy-core distances shift by 1 cell. Crossing painter fronts hit the enemy anchor one stroke earlier or later relative to core 0. The inference-correctness flag becomes False, but inert for list-first sweepers (P5). | unchanged; no draw | frozen, unmodified | all processes spawn at base − 1; movers keep their relative offsets | **Recommended** |
| A(d), d ∈ 1…7 | none: the anchor is still inside the core (on cell d) | moves the dual-purpose target to another core cell | — | — | — | Rejected: not a separation (Challenge 6) |
| A(d), any other off-core d (d ≤ −2 or d ≥ 8) | as A(−1) | The attack window [anchor, anchor+7] now contains ≥ 1 non-core cell *inside* the budget, so attackers paint phantom cells. At d = +8 the window misses the core entirely. | unchanged | frozen fixtures become incompetent | — | Rejected: localization confound (Challenge 2) |
| B: seed-derived offset | per-seed anchor offset | varies the size of the localization error across seeds, and adds a geometry factor | a new derived stream, or reuse of the placement hash | — | — | Rejected: seed variance plus confound |
| C: separate placement rule, distance and direction | direction becomes a variable | a seat-dependent direction breaks translation symmetry and the twin relabel | — | — | — | Reduces to A(−1) with a fixed direction; other choices rejected |
| D: move the core, keep the process | equivalent to A(−1) up to a global translation | breaks the byte identity of core placement (gate 2) and the recorded `pc`/core bases | — | — | — | Rejected in favour of A(−1) |
| E1: expose the enemy core base in the observation | removes the need for inference | an Agent API change, plus fixture changes | — | modified | — | Rejected: out of scope |
| E2: the anchor hit disrupts but does not flip ownership | effect-level decoupling | a special-cell rule; core 0 becomes immune while occupied, so capture becomes impossible for non-moving entrants | — | — | — | Rejected: immutable/special cells are out of scope, and it creates immunity |
| E3: offset-aware fixtures (enemy core = anchor − own spawn offset) | rule-invariant localization | new fingerprints; byte-identical under control only for some fixtures | — | new agents | — | Rejected as analyzed agents. **Kept as a test-only inertness instrument.** |

**Why −1 is special.** It is the unique off-core offset whose frozen attack window (anchor plus core cells 0–6) differs from the true core only in list positions beyond Q = 8 (P5).

It is also adjacent. That minimizes geometric change: the anchor and core form one contiguous 9-cell block.

---

## F. Recommended treatment semantics

**Field.** `RulesetPolicy.initial_anchor_placement: str = "core_base"`, with `INITIAL_ANCHOR_PLACEMENT_MODES = {"core_base", "before_core"}`.

- **The set is closed and string-valued, following `core_placement`'s style.** Every offset other than −1 is confounded, so an integer offset would invite arbitrary values.
- **Resolver.** `resolve_initial_anchor(core_base, A)` returns `core_base`, or `(core_base − 1) % A`.
- **Call site.** It is used only in `process_runtime.__init__`'s `if p.position is None` branch.
- **Unchanged.** Explicit `initial_position`s are left alone. `pc`, `region`, `core_base`, `core_cells` and the seeding are untouched.

**Properties.** These hold for n = 2, A = 512, seeded placement, Q = 8, chunk 2, rotation and λ = 1.

- **P1 Core identity.** The core bases, core cells, `pc`, `region` and tick-0 seeding diffs are byte-identical to control.
- **P2 Spawn.** Every default-spawned process is at `base − 1`, which is never in its own core. The spread movers end at `base − 1 ± [16, 64]`, also never in their own core.
- **P3 Translation.** Every anchor-to-anchor distance equals control's. Anchor-to-enemy-core distances shift by 1, which is immaterial under global reach (256 = A/2).
- **P4 No dual write.** A WRITE can both disrupt a process of V and flip one of V's core cells only if a V process sits on a V core cell. For the E5 fixtures that never happens, by P2 and their movement code, so **DUAL = 0**. ∎
  - [PROBE] DUAL was 0 in every separated run. In control, every anchor hit on an unmoved process is a DUAL write (for example 2,000 of 2,000 in sniper v min guard).
  - Scope: an agent that MOVEs onto its own core recreates dual writes. The treatment concerns the *initial* anchor only.
- **P5 Inertness.**
  - **Premise.** Take a fixture whose per-tick target list is [visible enemy anchors…, (own base), enemy_core+0 … enemy_core+7], deduplicated by a per-tick done set.
  - **Claim.** Adopting `enemy_core = anchor = base − 1` produces the same first `n_anchors + [1] + 7` unique targets as adopting the true `base`.
  - **Why.** The frozen window's first cell is the anchor, which is already done. The two lists first differ at unique position ≥ 9, and Q = 8 never reaches it. ∎
  - **Where it applies:** `e2_sniper`, `e2_min_guard`, `e2_spread_sniper`, `e2_spread_defender`, and `e2_counter` if it is triggered.
  - **Where it fails:** `v4_probe` and `e3_jam_sniper`.
  - [PROBE] 37 of 37 comparisons were byte-identical (write logs and per-tick ownership), across seeds 42 and 1001–1003.
- **P6 RNG.** No draw is added or moved. Agent seeds, contexts, placement draws and the painters' `first_side` are identical.
- **P7 Everything else unchanged.** Scheduler, quota, suppression, capture, K and scoring code are untouched.
  - G.4 still gives (5, 4).
  - G.5 immunity still holds for the repair guard and for the disrupt guard with ≤ 3 enemy locations. Their per-tick target lists are unchanged in length, and their final action still writes their own core.
- **P8 Default identity.** `"core_base"` is byte-identical for every existing Ruleset.

**Consequence of the variable itself, not a confound.** "Disrupt plus a full core sweep" costs 8 WRITEs under co-location and 9 under separation, while Q = 8.

- A disrupt-first sweeper covers one fewer core cell per tick.
- Because the fixtures restart their lists every tick, the same tail cell goes unattacked forever.
- [PROBE] Under K = 1, sniper v repair guard goes from a capture at tick 8 to a tie.
- This is registered as a pathology flag (PF-3), not excluded.

**Guard.** A match-start check should reject any layout whose default spawn anchor falls inside *any* entrant's core. Adjacent cores are possible with explicit starts. At A = 512 with seeded placement this can never trigger.

---

## G. Single-factor vs 2×2 decision

**Decision: single-factor (forward order). No 2×2.**

1. **Are the two factors independent policy dimensions?** Yes. Pass order is scheduler-only. Initial anchor placement is init-only.
2. **Would the four cells differ only in those two dimensions?** Yes, if both are separate fields.
3. **Can the E3/E4 corpora serve as the co-located arms?** Yes, through a byte-identity reproduction gate, as E4 did for T-E3.
4. **Can the separated arms be generated without regenerating historical controls?** Yes.
5. **Does the 2×2 answer materially more?** No, not for E5's question. [PROBE] Mirrored + separated equals forward + separated in every opening-only unit:
   - sniper ↔ min guard: −0.5;
   - min guard mirror: −1.0;
   - sniper v guarded painter: −0.457;
   - disrupt guard v guarded painter: 0.007.

   The sweep-backed exchange stays in passes 1–2, where the second mover responds second under *both* orders. H-COLOC and H-RESP make the same prediction in the mirrored cell.
6. **Would interaction effects be interpretable?** Only for MULTI-PASS, where the probe shows a real interaction: sniper v disrupt guard goes 0.0 under M to **+1.0** under MT. But that mixes response-order concentration with the coverage shift of P5. It is a different question and should not be attached to E5.
7. **Is the extra cost justified?** No. It would add about 3,600 matches for no discriminating prediction.

---

## H. Agent-information audit

| Fixture | Writes enemy anchor | Finds enemy core by | Co-location dependence | At d = −1 | E5 |
|---|---|---|---|---|---|
| `e2_sniper` | each visible anchor, first | first single anchor | localization | inert (P5) | **in** (SB attacker) |
| `e2_min_guard` | each, first; then own base | first single anchor | localization; its base repair was authored for anchor hits | inert | **in** (SB attacker, victim) |
| `e2_spread_sniper` | each visible anchor | first single anchor, *only if* it sees the enemy before the enemy spreads | localization | inert | **in** |
| `e2_spread_defender` | each; then own base | as above | localization | inert | **in** |
| `e2_disrupt_guard` | each, first | never attacks the enemy core | its only enemy-core damage is the co-location side effect | behaviour unchanged; enemy-core damage → 0 | **in** (AO attacker, MP victim) |
| `e2_guarded_painter` | each, first; then own base | never | as above, plus painting fronts | unchanged | **in** (AO attacker, victim) |
| `e2_repair_guard` | none | none | none | identical | **in** (victim; the G.5/D9 subject) |
| `e2_greedy_painter` | none | none | fronts only | identical | out: no directed base contest |
| `e2_counter` | — | — | identical to the greedy painter under λ = 1 | — | out (E4 S-9) |
| `v4_probe` | as step 0 of its cycle | re-reads `anchor[0]` on every callback | **its target set** | sweeps the anchor plus core 0–6 and never core 7; not inert | **out**; descriptive only |
| `e3_jam_sniper` | even actions | first single anchor | **its coverage policy** (`1 + cursor % 7`) | attacks core 0–6 and never core 7; not inert | **out**; F4 dropped |

**Verdict on the breakage.**

- **Localization.** For probe/jam-type co-location dependence, the breakage would be an **internal-validity confound**: the fixtures' encoded world model turns false, which is an information effect. At d = −1 it is provably inert for the four list-first sweepers, and the other two fixtures are excluded.
- **Anchor-only fixtures.** For the disrupt guard and guarded painter, the loss of enemy-core damage **is the treatment effect**. Their core contact existed only through co-location.
- **Seat dependence.** Whether a spread defender's core is ever inferred depends on the seat. The opponent must act before the spread. The directed class must therefore use the frozen control inference audit for each cell (§I), not source roles alone.
  - [PROBE] At seeds 1002 and 1003, spread defender v min guard goes −0.501 → −0.002, because the min guard, in Seat B, never infers the spread defender's core. It is AO.
- **No agent is modified.** The offset-aware copies are a test-only gate instrument and never enter the analyzed matrix.

---

## I. Experimental population and matrix

**Field.** Seven fixtures: `e2_sniper`, `e2_min_guard`, `e2_disrupt_guard`, `e2_repair_guard`, `e2_guarded_painter`, `e2_spread_sniper`, `e2_spread_defender`.

**Dropped:**

- `v4_probe` and `e3_jam_sniper`, which are not inert;
- `e2_counter` (S-9);
- `e2_greedy_painter`, which has no directed base contest;
- F2-P, because order is unchanged and the final-word seat does not flip;
- F4, because it depends on the jam sniper.

| Field | Composition | Per condition |
|---|---|---|
| F1 | 21 pairs × seeds 1–32 × 2 orientations, 1000 ticks, A = 512 | 1,344 |
| F2 | 7 twin mirrors × 32 × 2 (the duplicate orientation is the relabel gate) | 448 |
| **Total** | | **1,792** |

| Condition | Ruleset | Role |
|---|---|---|
| C-E5 | `…-capture-hold-k2-disruption-slot1` | control; must reproduce the preserved C-E4 (= T-E3) cells byte for byte |
| T-E5 | `…-capture-hold-k2-disruption-slot1-anchor-before-core` | primary |
| C-E5K1 | `…-disruption-slot1` | companion control; must reproduce C-E4K1 (= T-E3K1) |
| T-E5K1 | `…-disruption-slot1-anchor-before-core` | companion (feeds E5-H5 and the flags only) |

**Totals:** **7,168 matches**, 47% of E4. The controls are a full re-run, because match-generation code changes (E4 precedent). They are otherwise reusable only as reproduction targets.

**Populations**, frozen from control before any treatment exists:

- **P-BASE.** Every directed base contest (victim Y's cell 0) in an F1 ordered matchup, or in an F2 mirror (one unit), that meets three conditions:
  - control median BP_Y ≥ 1/2;
  - ≥ 10 both-alive ticks of each parity;
  - the attacker writes Y's anchor.
- **Classes**, assigned a priori by rule:
  - **SB**: the attacker has an enemy-core sweep role, *and* the frozen C-E4 `CoreInference` audit shows it inferred Y's core in more than half of the unit's seeds;
  - **AO**: the attacker has no sweep role, or never inferred Y's core;
  - **MIXED-INFERENCE**: inference succeeded in some seeds and not others. Reported, and excluded from H1 and H2.
- **Unit class (E4's OO or MP)** is kept as a secondary stratum.
- **[INFERENCE] estimate.** The E4 OPENING-ONLY units alone yield about 6 SB and about 12 AO directed contests. The whole field should yield roughly 20–30 SB. Freezing the real counts is a control-data step.
- **P-PAR-E5.** E4's frozen P-PAR restricted to the E5 field, for the continuity hypothesis (H3).

**Why not smaller.**

- The deterministic units are seed-invariant (verified at 4 seeds), so their extra seeds cost almost nothing.
- 32 seeds keeps the RNG-bearing painter and spread units rate-eligible and exactly paired.
- Trimming seeds per pairing would add a researcher degree of freedom.

---

## J. Metrics and instrumentation

**No replay or result schema change is needed.**

- `memory_diffs` keep write order. Runs coalesce only consecutive same-owner, consecutive-address writes, so every write is recoverable (E4 review §C).
- Process anchors are recorded at every tick boundary.
- `pc` plus the seeding diffs give the cores.

| Metric | Definition | Role |
|---|---|---|
| **BP_Y** (directed base parity) | P(Y owns its cell 0 at tick end ∣ Y second mover) − P(… ∣ Y first mover), over both-alive ticks | **Primary** |
| BP band | last-strong ≥ 2/3; last-moderate [1/3, 2/3); neutral \|BP\| < 1/3; first bands symmetric. Thirds of the half-range, a structural choice. | Transitions |
| **DUAL** | a hostile write to a cell that, at write time, is both a live anchor of V and a core cell of V | **The direct answer to "one write, two jobs"**: C > 0 and T = 0 |
| AMBIGUOUS-DUAL | a write in a tick in which V moved (intra-tick anchor unknown) | Counted separately |
| Anchor hits, core-0 hostile writes, overlap | per cell and per directed contest | Mechanism |
| Coverage | distinct enemy core cells written per tick, by attacker | Action-economy cost (P5 consequence) |
| First hostile interaction | the tick and action of the first hostile write | Challenge 8 |
| Front-induced hits | anchor hits made by painter fronts, and their tick | Geometry limitation |
| FMA, FPS, E4 bands | frozen E4 `cell_metrics`, unchanged | Continuity (H3) |
| Onset, recovery, capture, outcome class, tick-limit | capture analyzer v2, E3 action/parity, unchanged and hash-pinned | H4, H5, flags |
| `CoreInference` status and correctness | frozen audit | Classification input. `correct = False` under T is the expected signature. |

Only **analysis code** is new, in `tools/research/v6/e5/`. Engine telemetry stays unchanged.

---

## K. Pre-registered hypotheses

**Thresholds** reuse E4's structural constants unchanged: 2/3 is a supermajority, 1/10 the floor, 0.10 a flag, and 0.02 "essentially none". The selection threshold of 1/2 mirrors E4's \|FMA\| ≥ 1/2. None came from probe or treatment data.

**Counting.** DECIDED-EARLY-T units stay in the denominators and count toward neither numerator. NOT_SCOREABLE units are kept. A near-boundary unit (within 0.02 of a band edge) is flagged, and its class stands as computed.

| ID | Statement | Supported if | Refuted if | [PROBE] prior |
|---|---|---|---|---|
| **E5-D** | Decoupling theorem: a manipulation check and **hard stop** | T-E5 and T-E5K1: DUAL = 0 in every cell; no process on its own core at any tick boundary; every AO unit's median BP_T in the neutral band. C: DUAL > 0 in every cell with an anchor hit on an unmoved process. | any violation → STOP | holds |
| **E5-H1** | Co-location carries the base privilege | SB: NEUTRALIZED + WEAKENED + FLIPPED ≥ 2/3 | ≤ 1/10 | fails |
| **E5-H2** | Response structure carries it; co-location only supplies contact | SB: STAYS + STRENGTHENED ≥ 2/3, **readable only if E5-D passes** | ≤ 1/10 | supported (every SB unit probed: BP 1.0 → 1.0, or 0.5 → 0.5) |
| **E5-H3** | Residual-population null (E4 continuity) | P-PAR-E5 FMA-band STAYS + UNCHANGED-NEUTRAL ≥ 0.90 | < 0.90 | refuted, through the AO units |
| **E5-H4** | Outcome propagation (K = 2) | outcome-class change share in F1 ≥ 0.10 | ≤ 0.02 | uncertain (the painter pairings change) |
| **E5-H5** | Hold × separation (companion) | \|companion change share − primary change share\| ≥ 0.10 | ≤ 0.02 | likely: the two arms change *different* cells |

**H3 is continuity only.** Its refutation measures how much of the E4 residual was anchor-only contact. It is never a mechanism reading.

**Pathology flags** (recorded whatever else holds; primary arm, with the companion reported):

- **PF-1 new early captures.** ≥ 0.10 of control non-capture F1 cells capture before tick 100.
- **PF-2 stasis.** The F1 tick-limit share rises by ≥ 0.10. Static units (< 10 swings) are also reported.
- **PF-3 new immunity.** ≥ 0.10 of control capture cells become non-captures.
- **PF-4 loss of interaction.** The share of F1 cells with zero hostile core writes after tick 10 rises by ≥ 0.10.
- **PF-5 seat artifact.** Any unit newly reaches SDom ≥ 0.9, or \|GSB\| > 0.10 where control had ≤ 0.10.
- **PF-6 degenerate loop.** Deterministic period-≤ 2 trajectories that are new under T are reported by count. They are description, not a flag threshold.

---

## L. Manipulation and hard-stop gates

**Pre-treatment gates** (control data, or non-matrix seeds only):

1. **One-field difference.** Each E5 Ruleset differs from its parent only in `initial_anchor_placement` (and `ruleset_id`). All request overrides are `None`.
2. **Default identity.** Every frozen golden (V4, E2, E3-parent and E4-parent byte-identity freezes) passes, as does a **new E5-parent freeze committed before any engine change**.
3. **Reproduction.** C-E5 and C-E5K1 are byte-identical to the preserved C-E4 and C-E4K1 cells: replay SHA-256, and `result.json` minus `completed_at` and `occurrence_id`.
4. **Existing freezes.** E2, E3 and E4 freezes v1–v3 verify byte for byte. No historical file changes.
5. **Observation delta.** Using a recorder agent at non-matrix seeds: the first-callback `ObservationV2` differs from control **only** in `self_anchor` (−1) and `visible_enemy_anchor_addresses` (each −1).
6. **Inertness gate (P5).** For every E5 pairing with an inferring fixture, at seeds 101–104: the frozen fixture and the test-only offset-aware copy produce identical write logs and tick records under T-E5.
7. **D9 real-fixture gate under T-E5.** The E3/E4 scripted adversaries at non-matrix seeds must make 0 completions against the repair and disrupt guards.
8. **Tooling qualification.** 0 analyzer failures on control. The control-versus-control BP and FMA census is 100% STAYS or UNCHANGED.

**Treatment gates** (on treatment cells, before any analysis; any failure means STOP):

9. **Core placement.** It is byte-identical for every T cell: tick-0 `pc`, `region` and seeding diffs equal the paired C cell's.
10. **Spawn anchors.** Every tick-0 anchor is at `(core_base − 1) % 512`. No process is on its own core at any tick boundary.
11. **E5-D.** DUAL = 0, and the AO collapse holds.
12. **Scheduler invariants.** Σ `cpu_used` = `cpu_total`. No exclusive or zero-action live tick. The G.4 (5, 4) minimum is unchanged.
13. **Capture analyzer.** 0 capture-analyzer disagreements, and 0 completions against the repair and disrupt guards (D9).
14. **Twin relabel identity.** Orientation pairs have identical tick records.
15. **Execution integrity.** The source manifest is unchanged and the tree clean during execution. One match worker per field.

**Negative controls** (each must **fail** the gate that it targets):

- Applying the T-gate suite (10, 11) to the C-E5 corpus: co-location restored → fail.
- A test-only policy labelled as treatment but using `"core_base"` → gates 1 and 10 fail.
- A scratch placement at d = +1 (the anchor inside the core) → gate 10 fails. At d = −2 → gate 6 fails. Together these demonstrate why −1 is the only admissible value.
- A BP analyzer with first- and second-mover parities swapped → the control census reads FLIPPED.
- The disrupt guard's role table edited to "sweeps" → the classification digest mismatches.

---

## M. Adversarial findings

| # | Challenge or finding | Evidence | Disposition |
|---|---|---|---|
| Ch 1 | The anchor/core problem is an artifact of fixtures that attack anchors | [SOURCE] Every anchor-writer hits anchors first in the tick. AO contests exist only because of anchor-first authoring × co-location. | **Partly valid.** AO becomes a manipulation check. The evidence comes from SB contests only, where the base would be attacked even without anchor hits. |
| Ch 2 | Separation destroys the fixtures' core-localization assumption | [SOURCE] All inferring fixtures; the README rule | **Invalidates the naive design.** Controlled only at d = −1 (P5; [PROBE] 37 of 37 identical) and by excluding the probe and jam sniper. Registered limitation: `correct = False` by construction. |
| Ch 3 | Offset geometry variance | [SOURCE] A constant d, no RNG, and translation of all anchors | Controlled. Residual: the timing of front-induced hits, measured and registered. |
| Ch 4 | K = 2 masks outcomes | [CORPUS] E4-H4. [PROBE] The guarded-painter mirror changes only under K = 2; sniper v repair guard only under K = 1. | Controlled. The primary hypotheses are ownership-level. The companion feeds H5. Masking runs **in both directions**. |
| Ch 5 | FOLLOWS-FINAL shows co-location-independent MP mechanisms | [PROBE] Disrupt guard ↔ min guard stays at +0.5 under mirrored order, whether co-located or separated | Not invalidating. It supports directed analysis and is recorded as context. |
| Ch 6 | The attack merely moves to another address | [PROBE] Coverage drops by one cell per tick; K = 1 capture@8 → tie | Not merely moved: disrupting and taking cell 0 now cost 2 WRITEs. But the cost is **mechanical**, because the fixtures do not choose. Limitation. |
| Ch 7 | The core is derivable for free from the anchor | [INFERENCE] | **A requirement, not a threat.** Holding information constant is what isolates the action-economy variable. |
| Ch 8 | Changes come from first-contact timing or geometry | [RUN]/[PROBE] The first hostile write is at tick 1, action 1, in every scenario. Anchor-to-anchor distances are identical. | Controlled |
| AF-1 | E4's OPENING-ONLY class is *defined* through co-location | [SOURCE] `contest_classes.py` | A new directed classification is needed. E4 classes are only a secondary stratum. |
| AF-2 | MULTI-PASS is not a negative control | [PROBE] −2 → −3, −3.5 → −1.5, −1 → −0.75, −0.5 → 0 | The proposed "multi-pass control" hypothesis is dropped |
| AF-3 | Unit FMA is coarse and boundary-prone here | [PROBE] Guarded painter v min guard: −0.508 forward and −0.496 mirrored, with the same mechanism on opposite sides of a band edge | BP is primary. FMA is kept for continuity. |
| AF-4 | The AO half is a tautology | [SOURCE] P4 | Theorem gate (E5-D) |
| AF-5 | New immunity through the 9-target list, Q = 8 and per-tick restart | [PROBE] The K = 1 sniper v repair guard capture and the K = 2 jam and probe captures disappear | Registered flag PF-3 |
| AF-6 | Spread-core inference depends on the seat | [PROBE] Spread defender v min guard −0.501 → −0.002 | Class from the frozen inference audit, per cell |
| AF-7 | Local-reach agents lose core cell 7 | [SOURCE] | Compatibility note; research-only |
| AF-8 | E4's probe was wrong about H2 | [CORPUS] | Do not stop on probe priors (§Q) |
| AF-9 | `pc`/`region` hold the core base, and the analyzers depend on it | [SOURCE] | Forbidden to change |
| AF-10 | D6 (re-disruption) is the purest coupling, but it is untestable here | [SOURCE] The jam sniper is excluded | Limitation; a future fixture question |
| AF-11 | An H2 STAYS signature is also what a global null produces (E4 P-1 again) | [INFERENCE] | Registered precedence: H2 needs E5-D PASS |

---

## N. Interpretation table (registered form)

A row fires when every hypothesis it names has the required status. A plain hypothesis needs SUPPORTED; a negated one needs REFUTED; NEITHER satisfies neither.

| Result | Registered conclusion |
|---|---|
| E5-D fails | **STOP.** No gameplay reading. The treatment or the classification is defective. |
| E5-D ∧ H2 ∧ ¬H1 | **Co-location supplies contact, not privilege.** The opening privilege is the second response in the first exchange on the base, whether or not a disruption hit carries that exchange. Placement cannot remove it, and the forensic line on the basic interaction model closes. |
| E5-D ∧ H1 ∧ ¬H2 | **Co-location carries the base privilege.** The dual-purpose write is load-bearing even where the base is attacked explicitly. Separation is a candidate rule change; read H4, H5 and the flags for its costs. |
| H4 (with either row) | Separation changes outcomes. Recorded with direction (captures lost or gained). |
| H5 | The hold changes *which* outcomes separation affects. Recorded as a companion reading only. |
| H3 refuted | Continuity: the E4 residual included AO contact. **Never a mechanism reading.** |
| PF-1…PF-6 | Recorded as pathologies whatever else holds |
| none | **"No registered interpretation row applies" is itself the registered outcome.** The census is reported. |

**Precedence.**

- H1 and H2 cannot both be SUPPORTED on one census.
- H2 is never read without E5-D. That closes the E4 P-1 overlap in advance.
- **Blind checkpoint.** Before treatment, re-audit the table for every remaining pair of rows that could stand side by side, for example H2 alongside PF-3. Amend blind if needed, layered as E4 v2/v3 were.

---

## O. Research integrity and freeze plan

1. **Governance.** Preserve this review verbatim in its own commit and record its SHA-256. Word the ROADMAP and FUTURE_PLANS entries as a question.
2. **Freeze first.** Commit an **E5-parent byte-identity freeze** before touching `process_runtime.py`, covering both parents: the T-E3 and T-E3K1 Rulesets. Named scenarios at seeds 1–3, both orientations: sniper v min guard, disrupt guard v guarded painter, sniper v disrupt guard, the guarded-painter mirror, the min guard mirror, repair guard v sniper, spread defender v min guard and the disrupt guard mirror.
3. **Implement** the policy field, the resolver, the two Rulesets, the spawn guard and the plumbing. Then run the tests, the full suite, `mypy` and `ruff`, with exact counts.
4. **Tooling.** Build:
   - the matrix and its digest;
   - the directed-classification rule and table, digest-pinned;
   - BP, DUAL and coverage analyzers;
   - the gates, and mutation tests;
   - the pre-registration JSON (verbatim from §K–§N).

   Import E4 `cell_metrics`, capture analyzer v2 and E3 action/parity unchanged, with pinned hashes.
5. **Qualify on control data only.** Use the preserved C-E4 and C-E4K1 subset. Require 0 failures, a 100% unchanged control-versus-control census, and gate sensitivity (the negative controls fail).
6. **Blind checkpoint.** Surface every mechanization choice and every overlap between rows. Amend blind if needed.
7. **Freeze** the matrix identity (`v6-e5-matrix-v1-<digest>`) and the analysis identity (`v6-e5-freeze-v1-<digest>`) separately.
8. **Run the controls** (one worker per field), then the full reproduction gate. Freeze P-BASE, the classes and the control baseline.
9. **Run the non-matrix-seed gates**: inertness, observation delta and D9.
10. **You authorize the treatment separately.** Run T-E5 and then T-E5K1, followed by the treatment gates and the frozen analysis and interpretation.
11. **Write the results record in three layers**: registered verdicts, registered interpretation, descriptive synthesis.

**Hard stops** (halt; never patch and continue):

- gates 1–15 failing;
- fixture fingerprint drift;
- an analyzer defect found after exposure (a new freeze identity; the matrix id is kept);
- a recurring `evaluation.json` PermissionError (quarantine, relaunch and byte-check once, then stop).

---

## P. V6 implications

- **H2 (the probe prior).** The opening residual is intrinsic to rotation-preserving response order together with single-exchange scripted policies. E2–E5 would then have characterized the basic interaction model: hold, disruption scope, pass order and placement each move *contact* or *magnitude*, but not the second mover's early-pass privilege.
  - **The downstream question cannot be answered by more scripted-fixture forensics.** [INFERENCE] The privilege exists because the fixtures never re-contest a cell within a tick. A defender that repaired its base with its final in-tick action would own it in both roles, and agents can count their own in-tick actions.
  - So the next V6 branch is either:
    - a **policy-space study** (adaptive or searched agents under current rules), asking whether timing strategy exists; or
    - a new economic/opportunity-cost mechanic. E5's measured action-economy cost (9 > Q under separation) is concrete input for that design.
- **H1.** Co-location is a real structural coupling, and separation becomes a candidate rule. PF-3 would weigh heavily, since the probe predicts new immunity under K = 1 and lost painter captures under K = 2. Separation would then need pairing with coverage-aware agents before it could count as "better gameplay".
- **None, or NEITHER.** The directed census still says which contests depended on co-location. The recommendation would be no further forensic variant: take the census to the V6 decision.
- **E5-D fails.** This is an implementation or classification defect, with no gameplay reading. Repair it and re-freeze under new identities.
- **Skipping E5.** If you judge the source proofs plus the deterministic characterizations sufficient, you could record this review and go straight to the V6 decision. That is defensible, but it leaves the RNG-bearing painter and spread units uncharacterized. E4 showed that probes miss things.

---

## Q. Verdict

**REDESIGN.**

**Why the posed E5 is not causally isolated:**

- Any offset other than −1 confounds co-location with enemy-core localization (§E).
- The probe and the jam sniper are confounded at every offset (§H).
- Half the OPENING-ONLY population is a theorem, not evidence (AF-4).
- MULTI-PASS is not a control (AF-2).
- Unit FMA cannot isolate the base contest (AF-3).
- The 2×2 adds no discriminating prediction (§G).

**The smallest corrected design is causally isolated:**

- `initial_anchor_placement = "before_core"` (anchor = core_base − 1), with frozen fixtures;
- the four non-inert fixtures dropped;
- directed base parity as the primary metric;
- SB contests as the evidence and AO contests as the theorem gate;
- single factor, K = 2 primary plus a small K = 1 companion;
- 7,168 matches.

**Decisions for you**, before implementation or at the blind checkpoint:

1. Accept d = −1 as the only admissible offset.
2. Accept the four exclusions.
3. Accept BP as the new primary instrument.
4. Keep the companion, or instead register the masking limitation.
5. Allow the test-only offset-aware copies as a gate instrument that is never analyzed.

---

## Appendix — Blueprint for the corrected design (implementation phase; not done here)

| Item | Specification |
|---|---|
| Ruleset IDs | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-anchor-before-core` (primary; parent T-E3) and `bytefray-rules-6-research-disruption-slot1-anchor-before-core` (companion; parent T-E3K1). Each is an independent literal copy of its parent, never `replace()`. |
| Field | `initial_anchor_placement`: `"core_base"` → `"before_core"`. Validation: unknown or non-string → `ValueError`. |
| Lifecycle | `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS`, `__all__`. Kept out of stable, the Designer, `run`, `agents test` and tournament. No `MatchRequest` override; the override payload is untouched. |
| Likely affected | `ruleset_policy.py` (field, modes, resolver, policies, sets); `rules.py` (IDs); `process_runtime.py` (the one default-spawn line, 741–742); `match_service.py` (the spawn-in-core guard; the overlap-guard plumbing); `evaluation_contracts.py`, `evaluation_service.py` and `evaluation_cli.py` (allow-list, alignment labels, arena range, choices; Trap F-4: an omitted arena resolves to 512); new tests; `tools/research/v6/e5/`; docs |
| **Forbidden** | `python_runtime.py` (capture), `scheduler.py`, `vm.py`, `telemetry.py` and the replay/result schemas, `agent_api.py`, `placement.py`, the semantics of `EntrantState.pc`/`region`, every fixture `agent.py`/`agent.yaml`, all E2/E3/E4 tooling, freezes, pre-registrations, `contest_classes.json` and corpora, `client/`, `app/` |
| Tests | Policy validation and defaults; the one-field difference from each parent; spawn = base − 1, including the wrap at base 0 → 511; multi-process spawn; explicit `initial_position` untouched; P1 identity of `pc`, `region` and the seeding; P4 DUAL on scripted scenarios; P5 inertness against the test-only aware copies, with d = −2 failing; the observation delta; G.4 unchanged; G.5/D9 under T-E5; every frozen golden plus the new E5-parent freeze; lifecycle and product isolation; evaluation plumbing; determinism |
| Mutation tests | BP parity swap and off-by-one; base read from the anchor instead of `core_base` (must fail under T); DUAL using end-of-tick anchors in movement ticks, counting friendly writes, or allowing cross-victim writes; a flipped directed role; the inference audit ignored; band edges inclusive versus exclusive; `≥` versus `>` thresholds; DECIDED-EARLY dropped instead of counted; H2 read without E5-D; the relabel gate; n_distinct keying |
| Size and cost | 7,168 matches. At E4's measured rate (T-E4's 3,808 cells in about 16 minutes, with 4 fields in parallel at one worker each), that is about 30–40 minutes of wall time for all four conditions, about 5 GB (about 0.7 MB per match), plus about 300 non-matrix gate matches |

## Appendix P — Probe

- **Code.** `scratchpad/e5_probe.py` builds matches through `ProcessMatchController.from_python_entrants`, as E3's D9 gate does.
- **Hooks.** It wraps `VM._wr8` (logging the writer, address, anchor victims, core victims and DUAL) and `apply_core_capture` (logging per-tick own-core and base ownership). Both hooks pass through.
- **The treatment patch.** It sets every process's `position` to `core_base − 1` after construction, which is exactly what the proposed resolver would do.
- **Validity.** Under [RUN] the harness reproduces the frozen deterministic C-E4 FMAs (for example −0.5, −1.0, −2.0, −3.5 and −0.751) and T-E4's (0.0, +0.5, 0.0).
- **Exposure.** Seeds 42 and 1001–1003 only, on named scenarios; the tree was clean before and after.
