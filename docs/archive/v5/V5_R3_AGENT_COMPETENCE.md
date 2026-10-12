# Bytefray V5 Research Phase R3 — Agent Competence and Region-Sweep Sufficiency

**Status:** Phase R3 Blocker Investigation (Staged: R3A source audit, R3B diagnostic corpus, R3C promotion gate PASSED, R3C broad validation executed)
**Ruleset Evaluated:** `bytefray-rules-4` **only** — the permanent stable V4 identity. No experimental Ruleset was created, no engine production file was modified, and neither R1 process mortality nor the R2 objective oracle was activated at any point.
**Execution Baseline Commit:** `26e081696cd4a8be9319606c302ab3520c914a0a`
**R2 Commit:** `26e0816` (`research(v5): evaluate target persistence and objective awareness`)
**Archival Release Anchor:** `v4.0.0` (`9077b618d12a3eab498af5818a2852a841f49f5b`)

---

## A. Baseline

- **Branch:** `v5-research`.
- **Starting HEAD SHA:** `26e081696cd4a8be9319606c302ab3520c914a0a`.
- **Working-tree state at start:** clean (`git status --short` empty).
- **Upstream relationship:** `v5-research` and `origin/v5-research` both at `26e0816` at the start of R3 (`git rev-parse origin/v5-research`).
- **R2 present in branch history:** yes — `26e0816` *is* R2's commit. The branch reads `3830382 → ab24d27 (Phase 0) → 303b33f → 18e5ac6 (R1) → 26e0816 (R2)`.
- **Project version:** `4.0.0` (`pyproject.toml`), unchanged throughout R3.
- **Stable V4 identity confirmed unchanged:** `bytefray-rules-4` (`RULESET_V4` in `engine/src/battle_engine/ruleset_policy.py`) — process core size 8, Q = 8, D = 1, seeded core placement, round-robin process selection, entrant-wide sensor fusion, immortal processes, static process declarations, no replication, no objective oracle, existing scoring and victory conditions. Verified by code inspection (Section C) and proven by the regression evidence in Section P.
- **No experimental Ruleset exists.** R3 created no `bytefray-rules-5-r3-*` identity. `rules.py` and `ruleset_policy.py` were not modified; `process_runtime.py` was not modified. `git diff --stat` (Section P) shows zero engine production files changed. The only experimental object in this phase is a research-only *agent*.
- **Git discipline:** no commits, staging, rebases, resets, or history mutation were performed. All git operations were read-only (`status`, `log`, `rev-parse`, `diff`). No `runs/` artifact is tracked (`.gitignore` excludes `runs/`, unchanged).

---

## B. The blocker question

> **Is Phase 0's combat-to-victory conversion deficit a property of stable V4 mechanics, or of the bundled V4 agent population?**

R2 closed with this as a blocker finding rather than a result. Its Section L recorded that an attacker handed a permanent, perfect target against an opponent with **zero live processes and therefore zero repair capacity** still made roughly eight thousand core-targeting writes across a thousand ticks and moved the victim's core deficit from 0 to 1 of 8 — because it wrote at the one address it was given, while capture requires simultaneously owning all eight. Five of the six bundled agents write at exactly the address they are handed. The one that sweeps a region (`v4_quorum`) converted in every arm it appeared in.

Phase 0's entire 288-match corpus, and therefore the whole V5 programme's founding premise, rests on those six agents. R3 tests whether the premise survives a more competent legal attacker.

**Evidentiary standard (asymmetric, declared before execution).** Success — a legal Agent API v2 entrant under unchanged V4 that finds opponents, attacks a region, damages multiple distinct core cells, reaches an 8/8 simultaneous deficit and captures cores — is strong evidence that V4 mechanics *can* support conversion. Failure is **not** symmetric evidence that they cannot: it could equally mean the research agent's target acquisition, sweep geometry, reach, movement, or implementation was inadequate. Section K is therefore a mechanism analysis, not a verdict shortcut.

**Result, stated up front.** Region-capable legal attackers do convert under unmodified `bytefray-rules-4`, including in the exact repair-turtle matchup Phase 0 named as its primary evidence for a mechanical defect — a 1000-tick tie with 7,974 core-targeting writes and a maximum deficit of 1/8 becomes a **16-tick outright core capture**. The strong reading of Phase 0 ("V4 mechanics prevent objective conversion") is therefore **falsified**. But conversion is not universal: the minimal address-selection-only sweeper converts 5 additional matches out of 96 without a single regression, and still cannot capture a static repair turtle, for a reason Section K quantifies exactly. Agent competence materially improves conversion; it does not fully explain Phase 0.

---

## C. Stage R3A — Source-level audit of the six canonical V4 agents

The population was verified against the repository rather than assumed. It is exactly the six Phase 0 named, all Agent API v2, all present both in the writable catalog (`agents/`) and in the shipped resource tree (`engine/src/battle_engine/data/starter_agents/`), byte-identical between the two, and byte-identical to their frozen `agent_revisions/` snapshots where those exist.

### C.1 Two corrections to Phase 0's published inventory

Both were found by reading the source, and both matter to R3's interpretation.

**1. Phase 0's declared-reach column is wrong for all six agents.** Phase 0 Section 7 lists reaches of 5, 15, 8/25, 8, and 40. The actual `declare_processes()` return values, obtained by instantiating each bundled agent and calling it (arena 512):

| Agent | Phase 0 published | Actually declared |
|---|---|---|
| `v4_claimer` | `p1` reach 5 | `claimer` reach **1**, share 1.0 |
| `v4_concentrated_attacker` | `p1` reach 15 | `attacker` reach **4**, share 1.0 |
| `v4_defender_scout` | `defender` R8, `scout` R25 | `defender` reach **2** (0.5), `scout` reach **8** (0.5) |
| `v4_local_defender` | `p1` reach 8 | `defender` reach **2**, share 1.0 |
| `v4_scout` | `p1` reach 40 | `scout` reach **8**, share 1.0 |
| `v4_quorum` | six roles (no reaches given) | `oracle` **256** (0.125), `breaker` **48** (0.25), `guardian` **12** (0.25), `flank_left` **32** (0.125), `flank_right` **32** (0.125), `reserve` **24** (0.125) |

The real numbers are much smaller for the five simple agents and much larger for Quorum. This is not a cosmetic correction: reach is simultaneously the write radius *and* the sensor radius in V4 (`process_runtime._visible_enemy_anchors` and the WRITE reach check both use `process.reach`), and Section K shows the reach spread between `v4_concentrated_attacker` (4) and `v4_quorum` (up to 256) is the single largest driver of the conversion gap Phase 0 measured.

**2. `v4_local_defender` does not repair its eight core cells.** Phase 0 Section 10 describes it as an agent that "patrols its own 8 core cells and repairs overwritten cells every tick", and built the infinite-repair-churn diagnosis on that description. The source does something much narrower:

```python
self.patrol_offset = (self.patrol_offset + 1) % observation.self_reach   # reach == 2
target = (observation.self_anchor + self.patrol_offset) % self.context.arena_size
```

With `self_reach == 2` the patrol offset cycles `1, 0, 1, 0`, so the agent writes exactly **two** addresses — its own anchor and the cell after it — and never inspects or repairs the other six. Measured directly: in the flagship match its `unique_write_addresses` is **2** across the whole 1000 ticks. It also *abandons* even that when an enemy anchor is within reach 2, preferring to write the enemy's anchor. The observed "infinite repair equilibrium" was therefore never a repair race across eight cells; it was a one-cell contest between an attacker that could reach one core cell and a defender that happened to be standing on it.

### C.2 Capability audit

Write geometry below is traced from source, not inferred from outcomes. "T" denotes the address the agent takes from `visible_enemy_anchor_addresses[0]`.

| Agent | Procs (reach, share) | Target acquisition | Target persistence | Write geometry given a stable T | Address diversity for a stable T | Legal objective awareness | Classification |
|---|---|---|---|---|---|---|---|
| `v4_claimer` | 1 (R1, 1.0) | **none** — reads no enemy channel at all | n/a | alternates `MOVE(+reach)` and `WRITE(self_anchor)`; never writes an enemy address deliberately | n/a — walks the arena writing its own anchor, so it covers arbitrary sequential arena cells, none of them chosen | none; does not read `visible_enemy_anchor_addresses` | **NON-OFFENSIVE / NO TARGETING** (with incidental sequential coverage of neutral territory) |
| `v4_concentrated_attacker` | 1 (R4, 1.0) | `visible_enemy_anchor_addresses[0]` | none — re-read every action, no memory | `WRITE(T)` when `|T − anchor| ≤ 4`; else `MOVE` toward T; else drift `MOVE(+4)` | **1** | anchor address only; no inference, no memory | **POINT-TARGET ATTACKER** |
| `v4_defender_scout` | 2 — `defender` (R2, 0.5), `scout` (R8, 0.5) | `visible_enemy_anchor_addresses[0]`, both roles | none | `defender`: `WRITE(T)` if in reach, else return to core centre, else `WRITE(self_anchor)`. `scout`: `WRITE(T)` if in reach, else drift | **1** per role | anchor address only | **POINT-TARGET ATTACKER** (with a non-offensive self-anchor fallback) |
| `v4_local_defender` | 1 (R2, 1.0) | `visible_enemy_anchor_addresses[0]` | none | `WRITE(T)` if in reach; else return to core centre if >10 away; else patrol-write `anchor + (0 or 1)` | **1** offensive; **2** own-territory | anchor address only; reads its *own* `own_core_base` but never an enemy's | **POINT-TARGET ATTACKER / turtle** |
| `v4_scout` | 1 (R8, 1.0) | `visible_enemy_anchor_addresses[0]` | none | `WRITE(T)` **only if already in reach**; never approaches; otherwise drift `MOVE(+8)` | **1** | anchor address only | **POINT-TARGET ATTACKER** (opportunistic only) |
| `v4_quorum` | 6 (R256/48/12/32/32/24) | whole `visible_enemy_anchor_addresses` tuple **plus** `previous_read_owner` evidence from READs | **yes** — `contacts`, `core_candidates`, `weak_targets` persist for the whole match | `_siege_write` writes `target + _SIEGE_ORDER[i]` with `_SIEGE_ORDER = (0,7,3,4,1,6,2,5,−1,8,−2,9,−3,10,−4,11)`, five roles each carrying an independent cursor | **up to 16** per role, coordinated across five attacking roles | **infers the enemy core base**: addresses seen at first contact are stamped `core_candidates[...] = 100`, which is correct because every process starts at its entrant's `core_base` (`process_runtime`: `if p.position is None: p.position = start`). Legal — derived entirely from ordinary observations | **REGION-CAPABLE ATTACKER** |

Two observations follow directly, and neither uses the phrase "structurally incapable":

- Given a **fixed** target T, five of the six implementations repeatedly write T and do not deliberately enumerate neighbouring addresses. Against a **moving** target they do write many distinct addresses, but as a by-product of following an anchor, not as a chosen region: measured against the wandering `v4_claimer`, the baseline attacker's `unique_write_addresses` is 498 while its `unique_enemy_core_cells_targeted` is whatever the claimer happened to walk through.
- `v4_quorum`'s first eight siege offsets, `(0,7,3,4,1,6,2,5)`, are a permutation of `0..7` — exactly the eight cells of a core based at the target. Combined with its first-contact core-base inference, Quorum is not merely "region capable": it is *objective aware by legal inference* and its sweep is core-size aligned. This is entirely within Agent API v2, and it is the population's own existence proof that stable V4 permits both.

---

## D. Stage R3A — Baseline-agent selection

**Selected: `v4_concentrated_attacker`** (source fingerprint `4a2de6cacdca035e723d1256d32c618396cdcf8e8791dd66ad9b437de3932da5`, verified byte-identical between `agents/`, the shipped starter tree, and its frozen `agent_revisions/` snapshot).

It satisfies every requirement the charter sets for the paired subject, verified from source and from Phase 0 data rather than assumed:

- **Legally acquires enemy targets** — reads `visible_enemy_anchor_addresses[0]`, the only enemy channel in the bundled population.
- **Performs offensive writes, and pursues** — it is the only single-process bundled agent that *moves toward* an out-of-reach target rather than drifting past it, so it generates contact rather than waiting for it.
- **Has real contact in Phase 0's problem cases** — 7,902 core-targeting writes in the flagship `vs v4_local_defender` seed 1, and 7,974 in the reversed slot order at seed 3.
- **Exhibits exactly the insufficiency under test** — for a stable target it writes one address, forever.

The alternatives were rejected for concrete reasons: `v4_claimer` reads no enemy channel (nothing to sweep around); `v4_scout` never approaches an out-of-reach target, so a sweep would rarely activate; `v4_local_defender` and `v4_defender_scout` are defensive and mix two behaviours in one delta; `v4_quorum` already sweeps, so substituting it would test nothing. `v4_quorum` is used instead as a **behavioural comparator** on identical ground (Section J.7).

---

## E. Research-agent design

Three research-only agents live under `tools/research/v5/agents/`, deliberately **not** in the `agents/` catalog that `battle_engine.agents.resolve_agent` searches, not in `battle_engine.starters.STARTER_AGENT_NAMES`, not in the shipped starter resource tree, and not in any benchmark, GUI default, or evaluation default. They are resolved only by `r3_runner.py` and the R3 tests, through the public `battle_engine.agents.agent_spec_from_dir`. `tools/research/v5/agents/README.md` states this explicitly at the top of the directory. No bundled agent source was modified.

| Agent | Fingerprint | Role |
|---|---|---|
| `v5r3_point_control` | `c84526b5d28552ee0e5bbcf50362e9424ecb40f0db8dc001cb5f2ba8f239df70` | Behavioural clone of the bundled baseline; the paired-construction control |
| `v5r3_region_sweeper` | `576ea1d8795629ce072247cc946b8acdb1971fb567c98a39051e247ea5a64326` | **The R3 experimental agent** |
| `v5r3_region_sweeper_mobile` | `5c1ddd33d4ed254692df8a5aadf43ffa040955c7b4019fc26b559f6dab835ba6` | Secondary variant isolating the reach/movement confound |

### E.1 The exact behavioural delta (`v5r3_region_sweeper`)

Everything is copied verbatim from the baseline except one expression. Preserved: API version (2); process count (1); process id (`attacker`); declared reach (4); quota share (1.0); target acquisition channel and priority (`visible_enemy_anchor_addresses[0]`); **target lifetime — none**, the target is re-read from the observation on every single action and the agent keeps no contact memory whatsoever; the wrap-aware shortest-delta arithmetic; the approach MOVE formula `min(|Δ|, reach) · sign(Δ)`; the no-contact drift `MOVE(+reach)`; the written signature byte `0xAA`; and RNG usage (neither agent touches `context.rng`).

Changed:

```
baseline:   if |T − anchor| ≤ reach:  WRITE(T)
sweeper:    if |T − anchor| ≤ reach:  WRITE(T + offset)
```

where `offset` walks the deterministic expanding order `0, +1, −1, +2, −2, +3, −3, …` around T, advanced by a single monotonic integer cursor. The cursor is the only state the baseline does not have; it is never keyed to, reset by, or compared against any target address, so it is a sweep position, not a target memory.

**Reach handling.** An offset whose address is not within `self_reach` of the current anchor is skipped, never written. This matters in both directions: the engine *discards* an out-of-reach write but still charges the action slot (`process_runtime.run`'s WRITE branch increments the action counter before the reach check), so an implementation that "swept" by firing at unreachable offsets would silently hand itself a weaker action budget than the baseline while bypassing nothing. Skipping keeps the sweeper at exactly one applied write per action, the same as the baseline. Offset 0 — the address the baseline would have written — is always in reach at that moment, so the scan always terminates on a real address.

### E.2 Section 9 compliance — why the envelope is `2 · reach`, not 8

The sweep order is bounded at `|offset| ≤ 2 · self_reach`. The bound is derived from the engine's reach rule alone: the agent writes only while its anchor is within `reach` of T, and the engine applies a write only when the address is within `reach` of the anchor, so **no address further than `2 · reach` from T can ever be legally written from a qualifying anchor**. It is the exact reachability envelope and contains no knowledge of the victory core's size, base, or existence.

With the baseline's declared `reach = 4` that envelope holds 17 candidate addresses, which is larger than 8 by coincidence of the baseline's own declaration. The agent does not know `CORE_SIZE`, does not know any enemy `core_base`, and would sweep the same generic pattern around a target in an arena with no cores at all. Deliberately *not* implemented: anything of the form "write the known eight enemy core cells", or any offset list aligned to `core_base … core_base+7`. (For contrast, the bundled `v4_quorum` *does* use a core-aligned offset list — Section C.2 — which is legal but is precisely the design R3's experimental agent was forbidden to copy.)

A consequence worth stating before the results: because the sweeper never moves once the target is in reach, its physically writable set is exactly `[anchor − 4, anchor + 4]`, nine contiguous addresses. The T-centred order with skipping covers **all nine** of them, so this agent already achieves the maximum address diversity available to a stationary reach-4 V4 process. If it fails to cover a core, that is not a badly chosen pattern.

### E.3 The secondary variant, and why it exists separately

`v5r3_region_sweeper_mobile` runs the identical sweep order but, when the next sweep address is out of reach, spends the action **moving toward it** (using the baseline's own move formula) instead of skipping it, and does not advance the cursor until that address is actually written. This costs actions: every reposition consumes one of the ordinary Q = 8 slots and produces no write, so this agent has strictly *fewer* writes available than either the baseline or the primary sweeper. It gains no engine capability, no extra actions, no reach bypass and no privileged information.

It exists because the primary sweeper's coverage is capped at nine addresses by a movement policy it inherited, which makes "did region sweeping convert?" and "did the agent's reach let it cover a region at all?" inseparable in the primary arm. The charter warns that a changed MOVE policy is an alternative explanation; this variant makes that change **deliberate, declared and separately reported**, never merged into the primary sweeper's numbers.

---

## F. Legal-information boundary

Proven by execution, not by inspection alone (`engine/tests/test_v5_research_r3_agents.py`):

- **No experimental Ruleset.** Every R3 match's replay header records `ruleset_id: "bytefray-rules-4"`, and its `reproducibility` block contains **no** `process_integrity` key and **no** `objective_target_oracle` key — so neither R1's mortality nor R2's oracle was requested or resolved. Under stable V4 the oracle cannot be activated at all: `bytefray-rules-4` is absent from `OBJECTIVE_TARGET_ORACLE_RULESET_IDS`, so a stray request is ignored (R2 Section F, `test_stable_v4_is_immortal_even_if_process_integrity_is_passed` and its oracle counterpart).
- **Every address the sweeper was ever shown was a real live enemy anchor.** Across a 120-tick traced match, every entry of every `visible_enemy_anchor_addresses` tuple handed to the agent is asserted to match an address an enemy process actually occupied at that tick (or the tick before, since anchors move within a tick). An injected core base would appear here as an address no enemy process was standing on. It does not.
- **The agent reads nothing else.** It consumes `visible_enemy_anchor_addresses`, `self_anchor`, `self_reach`, and `context.arena_size`. It does not read `own_core_base`/`own_core_size` at all — fields the bundled `v4_local_defender` and `v4_defender_scout` both do read. It has no replay access, no engine introspection, no match metadata, no filesystem or network access, and no global randomness.
- **No engine capability was added.** Every action is one ordinary `AgentAction`; `act()` returns exactly one action per call; the traced per-tick action count never exceeds 8.
- **Ordinary reach is obeyed, not bypassed.** Across traced 200-tick matches, both sweeper variants record **zero** `REJECTED_OUT_OF_REACH`, **zero** `REJECTED_INVALID` and **zero** `EXCEPTION` results, with `APPLIED > 0`.

---

## G. Paired equivalence and control validation

**Clone control.** `v5r3_point_control` is a statement-for-statement transcription of the bundled baseline. Run against the same opponent, seed, slot order, arena and tick limit, its replay's **gameplay tick stream must be byte-identical** to the bundled agent's. Header and terminal result records legitimately differ, and only there — they carry the agent's name, source fingerprint and derived match/result ids.

- **R3B: 6 / 6 diagnostic matchups byte-identical** (SHA-256 over all `record_type == "tick"` records).
- **R3C: 96 / 96 broad-corpus cells byte-identical.**
- Independently, in every R3C cell the `point_control` arm's full analysis is identical to the `baseline` arm's on every metric: 16-19-61 win/loss/tie, 12 captures, identical mean writes, unique addresses, core writes, deficits and durations.

That is 102 independent matches proving the research agent directory, the alternate spec-resolution path (`agent_spec_from_dir` instead of `resolve_agent`), and the transcription itself change no gameplay whatsoever. Any baseline↔sweeper difference is therefore attributable to the sweep.

**Declaration equivalence.** Read back out of the replay the engine actually wrote, all three research agents declare exactly `[{process_id: "attacker", reach: 4, share: 1.0}]` — identical to the bundled baseline.

**Determinism.** A complete, independent re-execution of the 25-run R3B corpus produced a **byte-identical manifest**, including every replay SHA-256 and every metric. Both sweeper variants additionally reproduce byte-identical tick streams across repeated 300-tick runs.

**Instrument liveness.** A "no difference" result is only meaningful if the instrument is live. In R3C the sweeper's gameplay tick stream differs from the baseline's in **69 of 96** cells; the 27 identical cells are precisely those where the attacker never acquired a target, so the sweep branch never executed. Every null reported below is therefore a genuine null.

---

## H. R3 metrics

Three measurement problems had to be fixed before the comparison could be trusted. Nothing Phase 0, R1 or R2 published was renamed or recomputed — the new fields are strictly additive (`tools/research/v5/analyzer.py`).

### H.1 Run expansion — a bias pointing against the hypothesis

`vm._wr8` merges adjacent same-owner writes issued back-to-back within one tick into a single `MemoryDiff` with `length > 1`. Phase 0's `core_attack_writes` reads only `diff.address`, so:

- an agent writing `T, T, T` is counted as **three** writes;
- an agent writing `T, T+1, T+2` is counted as **one**.

That is exactly backwards for R3. In the flagship match the legacy counter reports 7,902 core-attack writes for the baseline and **988** for the sweeper, while the two agents in fact issue the *same* 7,902 physical writes. Every R3 counter expands the full `[address, address + length)` run. R3's tables never quote the legacy counter for a sweeping agent.

### H.2 Distinct cells versus flip events

`core_damage_dealt` counts ownership-*flip events*. Capture requires the victim to own **zero** of eight cells simultaneously. `unique_enemy_core_cells_damaged` (how many *different* cells were ever taken) and `distinct_own_core_cells_ever_lost` are the coverage measures; `max_core_deficit` remains the simultaneity measure. The two are reported side by side throughout, never merged.

### H.3 Fields added

**Write diversity (per attacker):** `writes_expanded`, `unique_write_addresses`, `hostile_writes_expanded`, `unique_hostile_write_addresses`, `enemy_core_writes_expanded`, `unique_enemy_core_cells_targeted`, `unique_enemy_core_cells_damaged`, `attack_episodes`, `max_distinct_core_cells_per_attack_episode`, `mean_distinct_core_cells_per_attack_episode`. An *attack episode* is a maximal run of consecutive ticks in which the entrant wrote at least one cell of some enemy's core; the per-episode measure is how many distinct enemy core cells it wrote during that run.

**Core coverage and conversion geometry (per victim):** `distinct_own_core_cells_ever_lost`, `first_own_core_hit_tick`, `tick_2_/tick_4_/tick_8_distinct_own_core_cells_lost`, `first_full_core_deficit_tick`, `ticks_first_core_hit_to_core_capture`, alongside R1's existing `max_core_deficit`, `core_deficit_area`, `full_core_return_count` and `core_capture_outcome`.

**Contact:** `first_contact_tick_by_entrant`, `first_geometric_contact_tick`, `ticks_contact_to_first_core_damage`, `visible_target_changes`. These reconstruct `process_runtime._visible_enemy_anchors`' fusion rule against replay anchors and reaches. Replay records **end-of-tick** anchors and disruption flags while the engine evaluates visibility immediately before each callback, so these are tick-resolution approximations of a within-tick fact — adequate for "when did contact begin" and "how often did the aim point move", not for exact per-callback sensor state. The approximation is conservative: R3C shows 59 cells where the attacker registers geometric contact versus 69 where the sweep demonstrably executed, so the metric under-reports contact rather than inventing it. Trace was used where exactness was required (Section F); replay bytes were not modified for any metric.

### H.4 Synthetic metric tests

`engine/tests/test_v5_research_r3_metrics.py` proves the analyzer separates the three cases, from replays real deterministic matches produced:

| Case | Construction | Asserted |
|---|---|---|
| **A** — repeated point attack | one core cell struck >100 times, passive victim | `unique_write_addresses = 1`, `unique_enemy_core_cells_damaged = 1`, `max_core_deficit = 1`, `core_capture_outcome = survived`, 2/4/8-cell milestones all `None`, 1 episode covering 1 cell |
| **B** — sequential region attack | eight different core cells struck, passive victim | 8 distinct cells targeted and damaged, milestones ordered and all reached; capture asserted **from the engine's own recorded outcome**, not inferred from coverage |
| **C** — damage and repair | cells 0–3 taken, fully repaired, then cells 4–7 taken | **8** distinct cells ever lost — identical to B on that metric alone — but `max_core_deficit = 4`, `core_capture_outcome = survived`, `first_full_core_deficit_tick = None`, `full_core_return_count = 1`, 2 episodes of 4 cells each |

Case C is the one that matters: coverage alone must never be read as progress toward capture. A fourth test proves run expansion strictly exceeds the legacy counter for a sweeping agent, and two more cover determinism and clean degeneration when no contact occurs.

---

## I. Stage R3B — Diagnostic corpus

R3 could not reuse R1's and R2's corpus verbatim: four of their seven matches contain no `v4_concentrated_attacker` at all, so the substitution would have been a no-op in more than half the set. `tools/research/v5/r3_selection.py` instead applies R1's six-category selection *shape* to the attacker-involved subset of the same frozen Phase 0 corpus (`runs/v5_phase0_corpus/stage1_metrics.jsonl`), plus two matches added by explicit name rather than by tuning a metric to reproduce them. The rule is a pure function of the corpus data, was declared before execution, and was not re-tuned afterwards.

| Category | Rule | agent_a | agent_b | seed | Phase 0 outcome |
|---|---|---|---|---|---|
| `named_reference_siege_vs_turtle` | by explicit name (Phase 0 Case 7 / R1 G.2 / R2 I) | `v4_concentrated_attacker` | `v4_local_defender` | 1 | tie @1000 |
| `conversion_failure_high_activity` | max Σ`core_attack_writes` among attacker-involved timeouts | `v4_local_defender` | `v4_concentrated_attacker` | 3 | tie @1000 |
| `disruption_heavy` | max Σ`total_disruptions_received` among attacker-involved timeouts | `v4_scout` | `v4_concentrated_attacker` | 6 | tie @1000 |
| `slow_eventual_conversion` | max `actual_ticks` among attacker-involved decisive | `v4_claimer` | `v4_concentrated_attacker` | 7 | B wins @999 |
| `healthy_decisive` | min `actual_ticks` among attacker-involved decisive | `v4_quorum` | `v4_concentrated_attacker` | 4 | A wins @5 |
| `passive_no_contact` | min Σ`total_combat_writes` among attacker-involved | `v4_concentrated_attacker` | `v4_concentrated_attacker` | 1 | tie @1000, 0 combat writes |
| `quorum_comparator` | by explicit name — same opponent, seed and slot order as the named reference | `v4_quorum` | `v4_local_defender` | 1 | A wins @7 |

The named reference is claimed **first** so the machine rules cannot consume it. Seed, slot order, arena size (512), max ticks (1000), `instr_per_tick` (8) and opponent revisions are Phase 0's, reused rather than re-chosen. Substitution seat is pre-declared as the first seat in seat order holding the baseline attacker; in the self-play negative control that is seat A only, leaving the bundled baseline as the opponent.

Two properties of the selection are worth stating plainly rather than glossing: `healthy_decisive` puts the substituted agent in the *losing* seat (it tests that the substitution does not destabilise a healthy decisive match, not that the sweeper converts), and `quorum_comparator` has no attacker to substitute, so only the control arm runs there.

**Arms** (all under `bytefray-rules-4`, mortality off, oracle off): `baseline` (bundled attacker, re-run fresh) · `point_control` · `sweeper` · `sweeper_mobile`. **25 runs**, executed in 11.3 s.

```
python -m tools.research.v5.r3_selection
python -m tools.research.v5.r3_runner --stage r3b
```

---

## J. R3B results

All figures are exact, from `runs/v5_r3_diagnostic/r3b_manifest.json`. "Atk" is the substituted seat, "Vic" the opponent. `point_control` is omitted from each table because it is identical to `baseline` on every field (Section G); its presence is the proof, not a data point. Write counts are run-expanded (Section H.1).

### J.1 `named_reference_siege_vs_turtle` — attacker vs local_defender, seed 1 (Phase 0's flagship)

| | baseline | sweeper | sweeper_mobile |
|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t |
| Atk writes (expanded) | 7,902 | 7,902 | 11 |
| Atk unique write addresses | **1** | **9** | 11 |
| Atk enemy-core writes | 7,902 | 1,756 | 6 |
| **Distinct core cells damaged** | **1** | **2** | **6** |
| **Max simultaneous deficit** | **1** | **2** | **4** |
| Core-deficit area | 988 | 1,646 | 3,945 |
| Full-core returns | 0 | 110 | 0 |
| Capture | survived | survived | survived |
| First core hit / 2 cells / 4 cells | 13 / — / — | 13 / 13 / — | 13 / 13 / 15 |
| Attack episodes (max cells each) | 1 (1) | 1 (2) | 4 (3) |
| First contact / target changes | 13 / 1 | 13 / 1 | 13 / 124 |

The baseline's `unique_write_addresses = 1` is the entire Phase 0 diagnosis in one number: 7,902 writes at one address across 1,000 ticks. The sweeper writes all nine addresses it can physically reach and doubles both coverage and simultaneous deficit; the mobile variant reaches six distinct cells and a deficit of 4. **None of them captures.** Section K explains exactly why, and the explanation is not "the sweep failed".

### J.2 `conversion_failure_high_activity` — local_defender vs attacker, seed 3

| | baseline | sweeper | sweeper_mobile |
|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | **B wins, 16t, `last_agent_standing`** |
| Atk writes (expanded) | 7,974 | 7,974 | 19 |
| Atk unique write addresses | 1 | 9 | 17 |
| Atk enemy-core writes | 7,974 | 886 | **10** |
| Distinct core cells damaged | 1 | 1 | **8** |
| Max simultaneous deficit | 1 | 1 | **8** |
| Capture | survived | survived | **captured** |
| First hit / 2 / 4 / 8 cells / full deficit | 4 / — / — / — / — | 4 / — / — / — / — | 4 / 4 / 6 / 14 / **16** |
| Attack episodes (max cells each) | 1 (1) | 111 (1) | 7 (3) |

**The decisive R3B result.** The bundled attacker spends 1,000 ticks and 7,974 core-targeting writes to move the defender's core deficit from 0 to 1 of 8. A legal Agent API v2 entrant, under the *same* Ruleset, *same* seed, *same* slot order, *same* opponent and *same* Q = 8 action budget, captures the entire eight-cell core in **16 ticks using 10 core-targeting writes**. It is an outright `last_agent_standing` core capture, not a territory-fallback win.

The primary sweeper does not convert here because the geometry of this seed puts only one of the defender's eight core cells inside its reach envelope (Section K).

### J.3 `slow_eventual_conversion` — claimer vs attacker, seed 7

| | baseline | sweeper | sweeper_mobile |
|---|---|---|---|
| Outcome | B wins, **999t** | B wins, **203t** | **A wins, 92t** |
| Atk writes (expanded) | 7,824 | 1,456 | 32 |
| Atk enemy-core writes | 118 | 10 | 0 |
| Distinct core cells damaged | 8 | 8 | 0 |
| Max simultaneous deficit | 8 | 8 | 0 |
| Core-deficit area | 64 | 10 | 0 |

The sweeper converts an existing win **4.9× faster** on 82% fewer writes. Against a *moving* target the baseline already reaches all eight cells eventually — it follows the claimer's anchor as the claimer walks through its own core — which is why this matchup was ever decisive at all; the sweeper reaches the same state in a fifth of the time. The mobile variant **loses** a match the baseline won: it repositions out of sensor range, loses the target (Section K.2), and drifts while the claimer walks into its core.

### J.4 `disruption_heavy` — scout vs attacker, seed 6

| | baseline | sweeper | sweeper_mobile |
|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | **A wins, 1000t (tick_limit)** |
| Atk writes / unique addresses | 3,992 / 1 | 2,996 / 9 | 11 / 11 |
| Atk enemy-core writes | 0 | 0 | 0 |
| Target changes | 997 | 665 | 2 |

Neither side ever reaches the other's core: `v4_scout` never approaches, so the attacker chases a perpetually-moving anchor and the sweep has nothing to convert. The sweeper is an exact outcome null. The mobile variant turns a tie into a **loss on territory fallback**, having stopped painting cells while it wanders — recorded as a regression, not a result.

### J.5 `passive_no_contact` — attacker self-play, seed 1 (negative control)

| | baseline | sweeper | sweeper_mobile |
|---|---|---|---|
| Outcome | tie, 1000t | tie, 1000t | tie, 1000t |
| Writes (expanded) | 0 / 0 | 0 / 0 | 0 / 0 |
| Max core deficit | 0 | 0 | 0 |
| First contact | none | none | none |

**Perfectly inert.** No arm manufactures contact where the game provided none. This is the single sharpest contrast with R2, whose oracle destroyed this same control (0 → 7,961 core attacks). R3's instrument changes what an agent does *after* it finds an enemy and nothing about *whether* it finds one.

### J.6 `healthy_decisive` — quorum vs attacker, seed 4

Every arm identical: Quorum wins at tick 5 by core capture; the substituted agent never gets an action's worth of offence away. Healthy matches are undisturbed.

### J.7 `quorum_comparator` — quorum vs local_defender, seed 1

Stable V4, no substitution. Same opponent, seed and slot order as the flagship in J.1.

| | `v4_concentrated_attacker` (J.1) | `v4_quorum` |
|---|---|---|
| Outcome | tie, 1000 ticks | **A wins, 7 ticks, core capture** |
| Total writes (expanded) | 7,902 | **31** |
| Enemy-core writes | 7,902 | **24** |
| Distinct core cells damaged | **1** | **8** |
| Max simultaneous deficit | 1 | **8** |
| First hit / 2 / 4 / 8 cells / full deficit | 13 / — / — / — / — | 2 / 3 / 4 / 6 / **7** |
| Max distinct core cells per episode | 1 | **8** |

Against the identical opponent on the identical seed, one bundled agent needs 7,902 core writes and a thousand ticks to reach a deficit of 1, and another needs 24 core writes and seven ticks to reach 8. Both are legal Agent API v2 entrants under unmodified `bytefray-rules-4`. Per the charter's warning about Quorum-specific inference: this explanation is grounded in Quorum's **source** (Section C.2 — a 16-offset siege order whose first eight offsets are the target-relative core cells, plus persistent first-contact core-base inference), not merely in its outcome.

---

## K. Mechanism analysis

### K.1 The primary sweeper converts every cell it can physically reach — and reach is the cap

The static-defender matchup makes this exact. Across all eight seeds of `v4_concentrated_attacker` vs `v4_local_defender` (seat A), "cells in reach" is how many of the defender's eight core cells lie within reach 4 of the attacker's parked anchor:

| Seed | Atk anchor | Def core base | Core cells in reach | Baseline cells damaged | **Sweeper cells damaged** | Sweeper max deficit |
|---|---|---|---|---|---|---|
| 1 | 260 | 263 | 2 | 1 | **2** | 2 |
| 2 | 376 | 379 | 2 | 1 | **2** | 2 |
| 3 | 383 | 387 | 1 | 1 | **1** | 1 |
| 4 | 300 | 303 | 2 | 1 | **2** | 2 |
| 5 | 138 | 142 | 1 | 1 | **1** | 1 |
| 6 | 107 | 108 | 4 | 1 | **4** | 4 |
| 7 | 164 | 167 | 2 | 1 | **2** | 2 |
| 8 | 434 | 435 | 4 | 1 | **4** | 4 |

The sweeper's distinct-cells-damaged equals its cells-in-reach in **8 of 8 seeds**, and its maximum simultaneous deficit equals it too. The baseline takes exactly one cell regardless. So:

- the sweeper is not failing to sweep — it converts **100%** of its physically reachable core cells, every seed;
- the deficit it creates is **mostly durable rather than churned away**, but not entirely: in the flagship seed the sweeper holds a mean deficit of 1.65 against its own maximum of 2 across 1,000 ticks (core-deficit area 1,646), with 110 momentary returns to a full core; the baseline holds 0.99 of its maximum 1 with zero returns. Both attackers therefore keep roughly 82–99% of whatever deficit they can create. Repair is not what separates them;
- the binding constraint is that a reach-4 process parked at distance 1–4 from a target can touch nine contiguous cells, and the intersection of that window with an eight-cell core is 1–4 cells on these seeds.

This reframes Phase 0's "infinite repair churn under zero process mortality" diagnosis. In the flagship matchup the defender is not out-repairing the attacker. The attacker simply cannot reach more than a small slice of the core, and its point-target policy could not even use the slice it had.

### K.2 Sensor reach and write reach are the same number, so covering a wider region costs contact

In V4 a process's `reach` is simultaneously its write radius (`process_runtime.run`'s reach check) and its sensor radius (`_visible_enemy_anchors`). A single-process entrant with no target memory that moves far enough to write an address beyond `reach` of its target therefore *loses sight of the target*, and — for the bundled baseline's fallback — reverts to blind drift.

That is exactly what the mobile variant does. Traced at seed 1: it makes contact at tick 13, sweeps out to `T+8` at tick 21, the target leaves its sensor radius, and it drifts a full 512-cell lap before returning. Its `visible_target_changes` is 124 versus the sweeper's 1. Where seeded placement happens to park it *on* the defender's core base (seeds 3 and 5, anchor 387 = base 387; anchor 142 = base 142) it never has to leave, and converts to a full 8/8 capture in 27 and 19 ticks respectively.

So the mechanism that limits region coverage under stable V4 is not repair, not disruption, and not core size. It is that **reach couples sensing to striking**, and the bundled attacker declares reach 4. Both halves of that are agent design choices: `v4_quorum` declares reaches up to 256 *and* carries persistent contact memory, and captures the same defender in 7 ticks.

### K.3 Why the flagship still ties for the primary sweeper

The primary sweeper preserves the baseline's movement policy by design (paired-equivalence discipline), so it inherits the nine-cell window. Removing that cap requires either more reach or target memory — both legal, both explicitly out of scope for a minimal address-selection delta, and both things the bundled Quorum already does. The flagship tie is therefore a bound on *this agent's* preserved movement policy, not evidence about V4's mechanics.

### K.4 Activity inverted into progress

Across R3C's 59 attacker-contact cells the sweeper averages **470** enemy-core writes against the baseline's **2,050** while producing a **53% higher** mean simultaneous deficit and 5 more captures. The most extreme single case is J.2: 7,974 core writes and a deficit of 1 versus 10 core writes and a capture. Phase 0's headline "1.77% combat conversion rate" measured a population that generated enormous write volume at one address; it did not measure a mechanical ceiling on conversion.

---

## L. R3C promotion decision

Evaluated against the charter's pre-declared gate, on R3B evidence only:

| Gate condition | Result | Evidence |
|---|---|---|
| Baseline repeatedly point-hammers or poorly covers | **YES** | `unique_write_addresses = 1` in J.1/J.2/J.4; 1 distinct core cell in every contact case |
| Sweeper substantially increases distinct core coverage | **YES** | 1 → 2 (J.1), 1 → 8 for the mobile variant (J.1: 6, J.2: 8) |
| Simultaneous core deficit increases | **YES** | 1 → 2 (J.1 sweeper), 1 → 4 (J.1 mobile), 1 → 8 (J.2 mobile) |
| Core captures increase in more than one case/seed | **NOT YET ESTABLISHED** on R3B | one new capture (J.2) — the exact "single lucky seed" risk the charter names |
| Passive/no-contact controls do not magically improve | **YES** | J.5 identical in all arms, 0 writes, 0 deficit |
| Success under stable V4 without privileged information | **YES** | Section F |
| Wins change only through territory fallback | **NO** (good) | J.2's win is `last_agent_standing` by core capture |
| Results dominated by an unintended behavioural change | **NO** for the primary sweeper | Section G: 102 byte-identical clone-control matches; movement change is confined to the separately-reported mobile variant |

Six of eight conditions pass outright, one passes in the desired direction, and the one unresolved condition — captures at more than one case/seed — is precisely what a broader corpus exists to answer. A repeatable geometry signal is present in every contact matchup.

### **PROMOTE TO R3C.**

---

## M. R3C — Broader validation

**Corpus, declared before execution** (`r3_runner.build_r3c_pairings`): the baseline attacker against **each of the six canonical V4 opponents**, at **each of Phase 0's eight seeds**, in **both slot orders** — 6 × 8 × 2 = **96 cells**, each re-run in all four arms = **384 matches**, arena 512, max ticks 1000, `instr_per_tick` 8, `bytefray-rules-4`. Slot order is enumerated rather than assumed symmetric because V4's chunked scheduler rotates its starting entrant (`RULESET_V4.scheduler_rotate_start`). The self-play cell is kept in both orders because substituting seat A and substituting seat B are different experiments against an unchanged bundled opponent. No seed was tuned after seeing results.

```
python -m tools.research.v5.r3_runner --stage r3c
```

### M.1 Aggregate (attacker's perspective, n = 96 per arm)

| Arm | W–L–T | Opponent cores captured | Own core captured | Attacker made contact | Mean writes | Mean unique addrs | Mean enemy-core writes | Mean distinct core cells damaged | Mean max deficit | Mean deficit area | Mean ticks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | 16–19–61 | 12 | 8 | 59 | 3,186.3 | 81.0 | 1,361.2 | 1.52 | 1.52 | 325.1 | 912.4 |
| `point_control` | 16–19–61 | 12 | 8 | 59 | 3,186.3 | 81.0 | 1,361.2 | 1.52 | 1.52 | 325.1 | 912.4 |
| **`sweeper`** | **17–19–60** | **17** | 8 | 59 | 1,880.9 | 86.6 | 304.7 | **2.36** | **2.36** | **790.9** | 774.1 |
| `sweeper_mobile` | 5–39–52 | 5 | 24 | 59 | 114.2 | 24.6 | 17.7 | **2.93** | 2.19 | **1,422.7** | 717.2 |

Restricted to the 59 cells where the attacker actually made contact:

| Arm | Mean max deficit | Mean distinct core cells damaged | Mean enemy-core writes | Mean deficit area | Captures |
|---|---|---|---|---|---|
| `baseline` | 2.39 | 2.39 | 2,050.2 | 451.9 | 12 |
| **`sweeper`** | **3.66** | **3.66** | **469.8** | **1,179.3** | **17** |
| `sweeper_mobile` | 3.34 | **4.20** | 24.2 | **2,299.6** | 5 |

### M.2 Outcome transitions versus baseline

| Arm | W→W | W→T | W→L | T→W | T→T | T→L | L→L |
|---|---|---|---|---|---|---|---|
| `sweeper` | 16 | **0** | **0** | 1 | 60 | **0** | 19 |
| `sweeper_mobile` | 0 | 0 | 16 | 5 | 52 | 4 | 19 |

**The primary sweeper never lost a match the baseline won or tied, never lost a capture the baseline achieved, and was never captured more often (8/96 in both arms).** It is a strict, regression-free improvement produced by changing one expression.

### M.3 Per-opponent (n = 16 each: 8 seeds × 2 slot orders)

| Opponent | Arm | W–L–T | Captures | Mean max deficit | Mean distinct core cells damaged |
|---|---|---|---|---|---|
| `v4_claimer` | baseline | 16–0–0 | 12 | 6.75 | 6.75 |
| | **sweeper** | 16–0–0 | **16** | **8.00** | **8.00** |
| | sweeper_mobile | 0–16–0 | 0 | 1.00 | 1.25 |
| `v4_concentrated_attacker` (no-contact control) | baseline | 0–0–16 | 0 | 0.00 | 0.00 |
| | **sweeper** | 0–0–16 | 0 | **0.00** | **0.00** |
| | sweeper_mobile | 0–0–16 | 0 | 0.00 | 0.00 |
| `v4_defender_scout` | baseline | 0–0–16 | 0 | 1.00 | 1.00 |
| | sweeper | 0–0–16 | 0 | **2.50** | **2.50** |
| | sweeper_mobile | 1–0–15 | **1** | **5.50** | **6.88** |
| `v4_local_defender` | baseline | 0–0–16 | 0 | 1.00 | 1.00 |
| | sweeper | 0–0–16 | 0 | **2.50** | **2.50** |
| | sweeper_mobile | 4–0–12 | **4** | **5.38** | **6.88** |
| `v4_quorum` | baseline | 0–13–3 | 0 | 0.31 | 0.31 |
| | sweeper | 0–13–3 | 0 | 0.69 | 0.69 |
| | sweeper_mobile | 0–13–3 | 0 | 0.81 | 2.06 |
| `v4_scout` | baseline | 0–6–10 | 0 | 0.06 | 0.06 |
| | sweeper | 1–6–9 | **1** | 0.50 | 0.50 |
| | sweeper_mobile | 0–10–6 | 0 | 0.44 | 0.50 |

### M.4 The ten new captures

Every one is an outright `last_agent_standing` core capture, never a territory-fallback win.

| Arm | Match | Baseline | With research agent | Max deficit | Distinct cells | Enemy-core writes |
|---|---|---|---|---|---|---|
| sweeper | `claimer vs attacker` seed 1 (seat B) | B wins @1000 (timeout) | B wins **@205** | 3 → **8** | 3 → 8 | 47 → 10 |
| sweeper | `claimer vs attacker` seed 3 (seat B) | B wins @1000 | B wins **@205** | 2 → **8** | 2 → 8 | 31 → 12 |
| sweeper | `attacker vs claimer` seed 4 (seat A) | A wins @1000 | A wins **@210** | 7 → **8** | 7 → 8 | 102 → 24 |
| sweeper | `attacker vs claimer` seed 6 (seat A) | A wins @1000 | A wins **@207** | 0 → **8** | 0 → 8 | 0 → 23 |
| sweeper | `scout vs attacker` seed 5 (seat B) | **tie @1000** | **B wins @10** | 1 → **8** | 1 → 8 | 3,968 → 8 |
| sweeper_mobile | `attacker vs local_defender` seed 3 (seat A) | **tie @1000** | **A wins @27** | 1 → **8** | 1 → 8 | 7,900 → 10 |
| sweeper_mobile | `attacker vs local_defender` seed 5 (seat A) | **tie @1000** | **A wins @19** | 1 → **8** | 1 → 8 | 7,936 → 10 |
| sweeper_mobile | `defender_scout vs attacker` seed 3 (seat B) | **tie @1000** | **B wins @18** | 1 → **8** | 1 → 8 | 54 → 12 |
| sweeper_mobile | `local_defender vs attacker` seed 3 (seat B) | **tie @1000** | **B wins @16** | 1 → **8** | 1 → 8 | 7,974 → 10 |
| sweeper_mobile | `local_defender vs attacker` seed 5 (seat B) | **tie @1000** | **B wins @24** | 1 → **8** | 1 → 8 | 7,938 → 10 |

Captures appear at **five distinct seeds** (1, 3, 4, 5, 6), against **four distinct opponents**, in **both slot orders**. Random lucky alignment is ruled out.

### M.5 The mobile variant's cost, reported in full

`sweeper_mobile` is a materially **worse agent** than the baseline: 5–39–52, sixteen wins converted into losses (all against `v4_claimer`), four ties converted into losses, twelve of the baseline's captures lost, and its own core captured three times as often (24/96 versus 8/96). It repositions out of sensor range, loses its target, drifts, stops painting territory, and leaves its own core undefended.

Its value is not as an agent. It is the existence proof that the reach envelope — not repair, disruption, core size, or process mortality — is what caps region coverage under stable V4, and that removing that cap converts the exact matchups Phase 0 named.

### M.6 Alternative explanations, tested

| Risk | Verdict | Evidence |
|---|---|---|
| **A. Territory farming** | **Ruled out** | All ten new captures are `last_agent_standing` core captures with a recorded 8/8 simultaneous deficit. The only territory-fallback outcome change is the mobile variant *losing* J.4 — reported as a regression. |
| **B. Accidental movement change** | **Ruled out for the primary sweeper** | 102 byte-identical clone-control matches (Section G); the MOVE branches are copied verbatim. The mobile variant's movement change is deliberate, declared in advance, and never merged into the primary arm's numbers. |
| **C. Extra effective actions** | **Ruled out** | Both variants write *fewer* times than the baseline (mean 1,881 and 114 vs 3,186). Traced per-tick action count never exceeds 8. Each `act()` returns one action. |
| **D. Reach violations** | **Ruled out** | Zero `REJECTED_OUT_OF_REACH` across traced 200-tick matches for both variants; the skip/reposition logic checks reach before every write. |
| **E. Target churn** | **Measured, and it is the mobile variant's defect** | `visible_target_changes` 1 (sweeper) vs 124 (mobile) in J.1; Section K.2. The primary sweeper's churn is *lower* than the baseline's (266 vs 468 mean over contact cells). |
| **F. Random lucky alignment** | **Ruled out** | Captures at 5 seeds, 4 opponents, both slot orders (M.4). |
| **G. Quorum-specific comparison error** | **Avoided** | The region explanation for Quorum is grounded in its source (`_SIEGE_ORDER`, `core_candidates` first-contact inference — Section C.2), not inferred from its win rate. |
| **H. Search improvement masquerading as conversion** | **Ruled out** | Attacker contact count is **identical** (59/96) in every arm, and the no-contact control is exactly inert in all 16 of its cells. R3's instrument changes what happens after contact, never whether contact happens. |

---

## N. Phase 0 reinterpretation

Phase 0 is not rewritten, and its numbers are reproduced exactly (Section P). What changes is what they support.

**What remains fully supported.** Phase 0 accurately characterised the bundled V4 population: 60.42% timeouts, 43.75% ties, 1.77% combat conversion, `v4_local_defender` winning 0 of 96, `v4_quorum` winning 87.5%. Re-analysed under R3's analyzer all 288 matches reproduce every published field bit-identically. Its *search-deficit* diagnosis (State C) is also untouched and, if anything, strengthened: R3 changed contact in exactly zero cells.

**What was confounded.** Phase 0's Section 11 State-B diagnosis — that combat fails to convert because of "infinite core repair churn under zero process mortality" — does not survive. In the flagship matchup:

- the defender never repaired eight cells, because it only ever writes two addresses (Section C.1);
- the deficit the sweeper created was durable, not churned (Section K.1);
- a legal agent captures that same defender's whole core in 16 ticks under unmodified mechanics (Section J.2).

Phase 0 measured what its six agents did. It did not measure what V4 permits.

**Three levels, kept distinct.**

| Level | Question | R3's answer |
|---|---|---|
| **Population result** | What do the bundled agents actually do? | Phase 0 is correct and reproduces exactly. Five of six write one address per target; one sweeps a core-aligned region and dominates. |
| **API / mechanical capability** | What can a legal Agent API v2 entrant do under stable V4? | Reach an 8/8 simultaneous core deficit and capture, against a repairing defender, in 16–27 ticks — demonstrated in 10 matches across 5 seeds, 4 opponents, both slot orders, with no engine change and no privileged information. `v4_quorum` demonstrates the same thing from inside the shipped population. |
| **Product-quality agent set** | Do the bundled examples adequately demonstrate the intended game? | **No.** Five of the six declare reaches of 1–8 in a 512-cell arena, keep no contact memory, and write one address per target. The gap between them and `v4_quorum` is not a difficulty curve; it is the difference between agents that can express the game's objective and agents that cannot. |

---

## O. Candidate evidence update

| Candidate | Status | Basis |
|---|---|---|
| **Agent competence / example quality** | **STRONGER SUPPORT — now the leading explanation** | Changing one expression in one bundled agent, with everything else held byte-identical, produces +5 core captures over 96 matches with zero regressions; adding the movement to use the sweep produces full 8/8 captures in 16–27 ticks in matchups the baseline could not convert in 1,000. Bundled `v4_quorum` captures the flagship defender in 7 ticks with 24 core writes on identical ground. Phase 0's corpus rests on a population that cannot express the objective. |
| **Process mortality** | **SUPPORT UNCHANGED (remains CONTRADICTED from R1) — and its motivating evidence is now separately undermined** | R3 ran no mortality experiment and adds no direct evidence. But the flagship "infinite repair churn" case that motivated mortality in Phase 0 is now shown to be a reach-coverage problem, not a repair problem: the defender repairs two addresses, and a legal attacker captures it outright without any mortality mechanic. |
| **Target persistence / objective awareness** | **WEAKER SUPPORT as a mechanic; STRONGER as an agent-design property** | R2 showed an engine-provided oracle restores pressure but not conversion, and degrades healthy matches. R3 shows `v4_quorum` obtains functionally equivalent information *legally and without any engine change*, by remembering first-contact addresses. The problem R2 tried to solve mechanically is solvable at the agent layer. |
| **V4 process core size = 8** | **WEAKER SUPPORT** | R2 newly implicated core size, reasoning that a single-address target cannot satisfy an 8-cell condition. R3 reaches 8/8 simultaneous deficit in 10 matches under unchanged mechanics, so 8 is not an unreachable bar; it is unreachable for an agent that writes one address. |
| **Process-local information / entrant-wide sensor fusion** | **SUPPORT UNCHANGED — but newly sharpened** | R3 changed neither locality nor fusion. It did surface that `reach` is simultaneously the sensor and write radius (Section K.2), which is what makes a single-process entrant's region coverage cost it contact. That coupling is a distinct, testable design axis, recorded as an observation, not a tier change. |
| **Capacity economics (Q = 8)** | **WEAKER SUPPORT** | Held constant by design, but the observed result runs against the "agents need more capacity" reading: the winning arms use dramatically *fewer* actions (10–24 core writes versus 7,900+). Quota was never the constraint. |
| **Specialization** | SUPPORT UNCHANGED | Not a controlled specialization experiment. Quorum's role split remains confounded with its reach and memory advantages. |
| **Replication / deployment** | NOT TESTED | Held constant by design. |
| **Territory incentives** | NOT TESTED | Held constant. R3 changed no scoring behaviour; the one territory-fallback outcome change is the mobile variant's regression in J.4. |
| *(new)* **Declared reach as the dominant agent-design lever** | **NEW CANDIDATE — STRONG SUPPORT FOR FURTHER STUDY** | Section K.1: the primary sweeper's distinct-cells-damaged equals its reachable core cells in 8/8 seeds. Reach determines both what an agent can strike and what it can see, and the bundled population declares 1–8 in a 512-cell arena while `v4_quorum` declares up to 256. |

---

## P. Validation

**Focused R3 tests (all new, all passing) — 15 tests:**

- `engine/tests/test_v5_research_r3_metrics.py` — **6 tests**: synthetic Cases A, B and C exactly as the charter specifies (including C's coverage-without-simultaneity proof), the run-expansion correction, R3-metric determinism, and clean degeneration with no contact. Every assertion derives from a replay a real deterministic match produced.
- `engine/tests/test_v5_research_r3_agents.py` — **9 tests**: product-path unreachability (not a starter, not in the catalog, not in the shipped starter tree), research-loader resolution, the clone control (byte-identical tick stream, differing whole-file digest), process-declaration equivalence for all three agents read back out of the replay, reach/action legality for both sweeper variants (parameterised, from trace), the legal-information boundary, determinism for both variants, and a guard that the sweeper is not an inert instrument.

**Stable V4 regression.**

- **Zero engine production files changed.** `git diff --stat` covers only `tools/research/v5/analyzer.py` and `tools/research/v5/corpus_runner.py`. `rules.py`, `ruleset_policy.py`, `process_runtime.py`, `placement.py`, `scoring.py`, `results.py` and every other engine module are untouched. No R3 Ruleset exists.
- All 288 frozen Phase 0 replays re-analysed with the R3 analyzer: **0 mismatches on every field Phase 0 published**, across all 288 matches. Aggregate reproduces exactly — timeout **60.42%**, tie **43.75%**. The only difference is the additive R1 + R2 + R3 field set.
- **R1 regression:** all 35 frozen R1B runs re-analysed — 0 analyzer-field mismatches. **R2 regression:** all 28 frozen R2B runs re-analysed — 0 mismatches.
- Pre-existing suites `test_v4_stable_ruleset_equivalence.py`, `test_v4_alpha2_placement.py`, `test_v4_alpha2_scheduler.py`, `test_v4_runtime_default_ruleset.py`, `test_ruleset_policy.py`, `test_v5_research_analyzer.py`, `test_process_mortality.py`, `test_v5_research_r1_metrics.py`, `test_objective_target_oracle.py` and `test_v5_research_r2_metrics.py` are unmodified and all pass (231 tests together with R3's 15).

**Full suite:** `python -m pytest` across all three configured `testpaths` (`_legacy/tests`, `engine/tests`, `client/tests` — the true repository suite per `pytest.ini`, not `engine/tests` alone) — **3,049 passed, 14 skipped, 3 deselected, 0 failures, 0 errors**, 342.5 s, exit code 0 (JUnit XML confirms `tests="3063" errors="0" failures="0" skipped="14"`). This is exactly R2's 3,048 plus R3's 15 new tests. The known intermittent Windows file-lock flake in `test_agent_evaluation_parallel.py` did not occur.

**Ruff:** `ruff check .` — all checks passed (one auto-fixable import-ordering finding in the new test module, fixed with `--fix` and re-verified).

**Mypy:** `mypy engine/src/battle_engine` — Success, 0 issues, 102 source files. `mypy client/src/battle_client` — Success, 0 issues, 16 source files.

**Determinism:** proven at three levels — a complete independent re-execution of the 25-run R3B corpus produced a **byte-identical manifest** including every replay SHA-256; both sweeper variants reproduce byte-identical tick streams across repeated runs; and the R3 analyzer produces identical output across repeated analyses.

**Reproduction:**

```
python -m tools.research.v5.r3_selection
python -m tools.research.v5.r3_runner --stage r3b
python -m tools.research.v5.r3_runner --stage r3c
```

---

## Q. Final verdict

### **2. AGENT COMPETENCE MATERIALLY IMPROVES CONVERSION BUT DOES NOT FULLY EXPLAIN IT**

Scoped precisely, because the two halves are about different claims.

**What is established beyond reasonable doubt.** Stable `bytefray-rules-4`, entirely unmodified, permits a legal Agent API v2 entrant to convert contact into an outright eight-cell core capture against a repairing defender — in **16 to 27 ticks**, in the exact matchups Phase 0 named as its primary evidence that mechanics prevent conversion, where the bundled attacker produced a 1,000-tick tie on 7,974 core-targeting writes and a maximum deficit of 1/8. It happens at five seeds, against four opponents, in both slot orders, with no engine change, no new Ruleset, no mortality, no oracle, no privileged information, no reach bypass, and *fewer* actions than the baseline used. A bundled agent, `v4_quorum`, does the same thing from inside the shipped population: 24 core writes, 7 ticks, on the identical opponent and seed where the baseline attacker managed one cell in a thousand ticks. **The strong reading of Phase 0 — that V4's mechanics prevent objective conversion — is falsified.**

**Why this is verdict 2 and not verdict 1.** The minimal, address-selection-only sweeper — the one whose construction is proven clean by 102 byte-identical control matches — produces 17 captures where the baseline produces 12, and still cannot capture a static repair turtle in any of 16 attempts. Its coverage is capped, exactly and measurably, at the core cells inside its inherited reach envelope (Section K.1). The variant that does capture turtles changes movement as well as address selection and is, overall, a considerably worse agent. Conversion under stable V4 is therefore demonstrably *possible* and demonstrably *not easy*: it requires a combination of reach, coverage and target memory that five of the six bundled agents lack and that the charter forbade R3 from assembling wholesale. Claiming "V4 mechanics demonstrably sufficient" would overstate 17 captures in 96 matches into a general property.

**What this means for the V5 programme.** The mechanic search — process mortality, target persistence, and everything queued behind them — has been aimed at a problem whose evidence base was measuring agent simplicity. Two of the three mechanics tested so far were rejected on their own merits (R1, R2); R3 now shows the motivating diagnosis for both was itself confounded. Further engine-mechanic research should **pause**. It should not resume against a baseline built from a population where five of six agents declare a reach of 1–8 cells in a 512-cell arena, keep no memory of anything they have seen, and write a single address per target.

### Recommended next research question (exactly one)

> **Does a bundled V4 agent population that can express the game's objective still exhibit a combat-to-victory conversion deficit?**
>
> Re-run Phase 0's 288-match corpus design with a *product-quality* canonical population — agents whose declared reach is scaled to the arena, that retain a last-known contact, and that attack a region rather than a point, at a range of competence levels rather than the current all-or-nothing gap between five point attackers and `v4_quorum`. Hold `bytefray-rules-4` fixed and change nothing but the population. If the conversion deficit largely disappears, then V5 needs no new mechanic and the real work is example quality, agent-authoring guidance, and balance — a product problem, not a design problem. If a deficit persists against competent agents, the V5 mechanic search finally has a trustworthy baseline to aim at, and Phase 0's premise is vindicated on far firmer ground than it currently rests on.
>
> This is deliberately **not** a proposal to ship the R3 research agents. They are experimental instruments, and one of them is a bad agent. Per the standing research-integrity rule, R3 reports the need for a stronger population as a finding, not as permission to build one.
