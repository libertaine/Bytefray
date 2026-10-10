# Bytefray V5 Alpha 1 — Phase C: Canonical Starter Agent Population Redesign

**Date:** 2026-09-09
**Branch:** `v5-research`
**Status:** COMPLETE
**Prior phase:** Phase B — Production Engine Hygiene & Rejected-Experiment Isolation
**Next phase:** Phase D — Authoring Guidance & Parameter Schemas

Phase C is a **product** phase. It creates no ruleset, changes no gameplay
mechanic, and modifies no production engine runtime file. Its question is:

> Can Bytefray ship a small, strategically diverse, understandable starter
> population that teaches players how objective-capable stable V4 play
> actually works?

---

## A. Starting baseline

| Property | Value |
| --- | --- |
| Branch | `v5-research` |
| Starting HEAD | `f7a543dc1ed1b9528d315ae2a14941bba0dd9646` |
| HEAD matches `origin/v5-research` | Yes (identical SHA) |
| Working tree at phase start | Clean (`git status --short` empty) |
| `git diff --check` at phase start | Clean (no output) |
| Phase B in history | Yes — `f7a543d refactor(v5): remove rejected experimental mechanics` |
| Product version | `5.0.0a1` (`pyproject.toml`; installed distribution reports `5.0.0a1`) |
| Stable ruleset | `bytefray-rules-4` |
| `.git/index.lock` exists | `False` |
| `.git/index` size at phase start | 89,711 bytes (mtime 2026-09-08 23:07:30) |

Three pre-existing `.git/index.corrupt-*` files (`index.corrupt-20260908`,
`index.corrupt-backup`, `index.corrupt-phaseB`) were present at phase start.
They are **not** `index.lock`, they predate this task, and they were neither
read from nor written to. Recorded here as an observation only.

No Git mutation command was executed at any point during Phase C.

---

## B. Existing V4 population audit

The full product-agent discovery path was traced before any file was edited.

### B.1 How bundled agents are discovered

```
battle_engine/data/starter_agents/<name>/{agent.yaml, agent.py}    (shipped resource)
        │  ensure_starter_agents()  -- non-destructive copy-if-missing
        ▼
<data root>/agents/<name>/                                          (writable catalog)
        │  discover_agents() / resolve_agent() / agent_spec_from_dir()
        ▼
CLI (`bytefray agents`, `--a-type`), tournament CLI, Agent Designer catalog
```

* The authoritative roster is the tuple `battle_engine.starters.STARTER_AGENT_NAMES`.
* `ensure_starter_agents()` is called by `cli.py` (two sites), `tournament_cli.py`,
  and `app/agent_designer.py`; every one of them iterates that tuple.
* Packaging is already generic: `pyproject.toml` declares
  `battle_engine = ["data/**/*"]` as package data, with `*.py[cod]` excluded, so a
  new starter directory is packaged with **no packaging change at all**.
* `MANIFEST.in` enumerates nothing agent-specific.
* `tools/installer.iss` contains no starter or agent name.

### B.2 Are the six `v4_*` IDs load-bearing?

| Question | Finding |
| --- | --- |
| Do IDs appear in replay/result provenance? | Yes. `MatchEntrant` carries the agent name into replay headers, result JSON and agent traces. |
| Do tests assume exact IDs? | Yes — `test_v4_production_integration.py`, `test_v4_historical_immutability.py`, `test_v4_quorum_advanced_example.py`, `test_designer_workflows.py`. |
| Do tests assume exact counts or ordering? | **No.** Every roster assertion is derived from `STARTER_AGENT_NAMES` itself (`test_command.py:514`, `test_starter_agents.py:169,280`), so the tuple can grow safely. |
| Would editing an agent under its existing ID change historical meaning? | Yes. `test_v4_historical_immutability.py` pins a `v4_claimer` vs `v4_scout` match exactly, and Phase 0 / R3 / R4 corpora are all keyed to these IDs and their measured behaviour. |
| Byte-for-byte repository/package parity enforced? | Yes — `test_v4_production_integration.py::test_packaged_v4_starters_match_repository_population_byte_for_byte`. |

### B.3 Compatibility decision

> **Preserve all six `v4_*` agents unchanged. Add a new, additive `v5_*` family
> under new IDs.**

No compelling reason to modify an existing `v4_*` ID was found, so none was
modified. This is verified rather than asserted: `test_v5_starter_agents.py::
test_v5_starter_install_leaves_the_v4_population_byte_for_byte_unchanged`
compares every shipped `v4_*` file against both the repository catalog copy and
the freshly bootstrapped user catalog, byte for byte.

---

## C. The V5 starter population

Four starters. Not six: the prompt's ladder is covered by four, and a smaller
distinct population is preferable to redundant examples.

Reach and share below are **read back from each agent's actual
`declare_processes()` return value and re-verified against the declaration
records the engine wrote into the match trace** — never transcribed from
documentation. This is a direct response to R3's finding that Phase 0's
published reach table was wrong for all six canonical agents.

### C.1 `v5_region_attacker` — "the objective is a region, not a point"

| Property | Value |
| --- | --- |
| Processes | 1 — `attacker` |
| Reach / share | 16 / 1.0 |
| Movement | Drifts one reach per action while blind; closes onto a contact until the whole sweep window is in reach; then holds. |
| Target acquisition | **No memory.** Nearest visible enemy anchor, re-read from the observation on every single action. |
| Write geometry | Expanding symmetric sweep `0, +1, -1, +2, -2, …` out to one `own_core_size` either side of the contact (17 offsets). |
| Defence | None. |
| READ usage | None. |
| Internal state | One integer sweep cursor. |
| Signature byte | `0xA5` |
| Source | 197 lines including the teaching docstring. |

### C.2 `v5_scout_striker` — "search, remember, then strike"

| Property | Value |
| --- | --- |
| Processes | 1 — `striker` |
| Reach / share | 40 / 1.0 |
| Movement | Deliberate one-reach strides so consecutive actions sense adjacent, non-overlapping bands; then closes on a contact. |
| Target acquisition | Nearest sighting, stored with its tick, **expiring after 60 ticks** — it can press a contact that has left sensor range, and genuinely forgets when the memory goes stale. |
| Write geometry | Ascending linear scan of a window `contact - core_size … contact + core_size - 1` (16 offsets), low address to high. |
| Defence | None. |
| READ usage | None. |
| Internal state | Last contact address, last contact tick, strike cursor. |
| Signature byte | `0x5B` |
| Source | 188 lines. |

### C.3 `v5_core_defender` — "you can only defend what you look at"

| Property | Value |
| --- | --- |
| Processes | 1 — `defender` |
| Reach / share | 12 / 1.0 |
| Movement | One step to the middle of its own core at match start, then station-keeping. Measured max displacement from home: **4 cells**, every run. |
| Target acquisition | Its own core cells, by READ rotation; enemy anchors opportunistically. |
| Write geometry | Repair of proven-lost cells first, then blind refresh of own core cells in rotation. |
| Defence | **Primary.** |
| READ usage | **Primary — the only starter that READs.** |
| Internal state | Repair queue, inspect cursor, pending read, per-tick inspection budget. |
| Signature byte | `0xDF` |
| Source | 181 lines. |

`INSPECTIONS_PER_TICK = 4` makes inspection a **reserved duty** that offence
may not spend. This is a direct, deliberate response to two prior findings:
R3 §C.1 (the bundled `v4_local_defender` abandons its patrol whenever an enemy
is within reach, so an opponent disarms it simply by standing next to it) and
R4 §H.1 (the first `v5r4_core_warden` draft reproduced that defect by accident
and was rejected at qualification).

### C.4 `v5_dual_team` — "an entrant is a team of processes"

| Property | Value |
| --- | --- |
| Processes | 2 — `raider`, `keeper` |
| Reach / share | 32 / 0.5 and 12 / 0.5 (total exactly `1.0`) |
| Movement | Raider pursues across the arena; keeper steps to the core centre and holds. |
| Target acquisition | **One contact memory shared by both processes** — whichever sees the opponent first writes it, expiring after 90 ticks. |
| Write geometry | Raider: forward block of `own_core_size` consecutive addresses from the contact. Keeper: own core cells in rotation. |
| Defence | Secondary (blind rotation — the keeper never READs and cannot distinguish a cell it owns from one it lost). |
| READ usage | None. |
| Internal state | Shared contact address + tick; one private cursor per role. |
| Signature byte | `0x6B` |
| Source | 202 lines. |

Role dispatch is on `observation.self_process_id`; cooperation is ordinary
attributes on `self`, because all of an entrant's processes are served by the
same object. Both facts are stated explicitly in the module docstring, because
they are the lesson.

---

## D. Relationship to R3 and R4

### D.1 Lessons taken

| Source | Lesson applied |
| --- | --- |
| R3 §E.2 | An attacker is never told the enemy's core size, so a sweep envelope must be derived from something the agent legally holds. |
| R3 §K.1 | "Reach is the cap": an attacker converts only the core cells it can physically reach. Directly produced the `_press_margin` design (Section D.3). |
| R3 §K.2 | Reach couples sensing to striking. Produced the deliberate reach spread 12 / 16 / 32 / 40 across the family. |
| R3 §K.4 | Write *volume* is not progress; distinct simultaneous coverage is. |
| R4 §G | Archetype-specific admission criteria, never one uniform "must win" metric. |
| R4 §H.1 | A defender whose inspection can be starved by offence is not a defender. Produced `INSPECTIONS_PER_TICK`. |
| R4 §J | Diversity must be *measured* from real runs across many axes, not asserted from source. |

### D.2 How the production starters differ from the research agents

No research agent was renamed, copied, or promoted. Every V5 starter was
written fresh, and the differences are deliberate:

* **Instrumentation removed.** The research agents carry provenance headers,
  containment notices and experiment-control commentary. The starters carry
  teaching commentary aimed at a first-time reader.
* **Complexity cut.** `v5r4_recon_striker` (260 lines) derives targets from
  READ-based ownership evidence and longest-enemy-held-run analysis;
  `v5_scout_striker` (188 lines) uses a plain contact memory. `v5r4_siege_regional`
  forms a READ-verified core-base hypothesis; `v5_region_attacker` keeps no
  memory at all.
* **Fewer moving parts.** `v5r4_core_warden` carries a perimeter-claim
  fallback and a separate counter-attack cursor; `v5_core_defender` has one
  priority ladder and one cursor.
* **One idea each.** Every starter's docstring opens with a single sentence
  headed `THE LESSON`.

### D.3 One correction Phase C had to make to its own first draft

The first frozen implementation stopped approaching a contact as soon as the
contact itself entered reach. That is *maximum range*, and from there the far
half of the agent's own sweep window is out of reach: the sweep silently
skipped it for the rest of the match. Traced at arena 512 with `v5_scout_striker`
(reach 40) against a static target at 200: the agent parked at anchor 160,
wrote addresses 192–200, and could never touch 201–207 — nine addresses, forever.

This is exactly R3 §K.1's mechanism, reproduced by accident in the very starter
whose stated lesson is regional coverage. It was classified as a correctness
defect in the deliverable rather than a tuning preference, so the freeze was
**invalidated and restarted** (Section F). The fix is one condition, shared by
all three offensive paths:

```python
if self._distance(target, observation.self_anchor) > self._press_margin(observation):
    return self._move_toward(observation, target)
```

with `_press_margin = self_reach - own_core_size`, which makes every address in
the window provably legal from the resulting anchor. Effect on development
seeds, against opponents that stand on their own core:

| Matchup (dev seeds 201–208, both seats) | Before | After |
| --- | --- | --- |
| `v5_region_attacker` vs `v4_local_defender` | 8–0–8, 6.06 enemy core cells | **16–0–0, 8.00 cells** |
| `v5_scout_striker` vs `v4_local_defender` | 14–0–2, 7.62 cells | **16–0–0, 8.00 cells** |
| `v5_dual_team` vs `v4_local_defender` | 9–0–7, 6.50 cells | **14–0–2, 8.00 cells** |

---

## E. Qualification fixtures

Three fixtures live only in `engine/tests/test_v5_starter_agents.py`. They are
written into `tmp_path`, are never installed, never discoverable, and receive
no information a product starter could not legally obtain.

| Fixture | Behaviour | Purpose |
| --- | --- | --- |
| `fixture_idle_target` | 1 process, reach 1, share 1.0. Returns `MOVE 0` forever; never writes. | A perfectly static objective. Whatever a starter takes stays taken, so a capture is earned by covering the region rather than handed over by a failure to repair. |
| `fixture_drifting_target` | 1 process, reach 1, share 1.0. `MOVE +3` every action; never writes. | A moving contact. A memoryless agent must re-acquire it every action; an agent with memory must notice the memory going stale. |
| `fixture_core_presser` | 1 process, reach 12, share 1.0. Closes on the nearest visible anchor, then cycles writes over exactly four addresses at offsets `-3, -2, +2, +3`. | A measuring instrument, not an opponent. Four cells can never capture an eight-cell core, so the match cannot end before detection and repair are observed many times; and it never writes offset 0, so it never disrupts the defender. What remains is a clean sustained damage/repair contest. |

The presser's bounded design was itself a correction: an earlier 16-cell version
captured the defender's core in about seven ticks, ending the match before the
mechanic under test could be observed at all.

Fixture matches use explicit starts, so each test knows the opponent's core
cells exactly (`core_base … core_base + 7`) and can assert against them directly
without giving any starter that information.

---

## F. Development results (seeds 201–208)

Predeclared before implementation: **development seeds = 201–208**,
**holdout seeds = 301–308**, **sanity tournament seeds = 401–404**.

Development matrix: 4 candidates × 4 bundled fixtures × 8 seeds × 2 slot orders
= **256 matches**, arena 512, `max_ticks` 1000, `bytefray-rules-4`, Q=8.
The four fixtures (`v4_local_defender`, `v4_claimer`, `v4_concentrated_attacker`,
`v4_scout`) are pre-existing bundled agents; none was authored for this phase.

| Candidate | W–L–T | Captures dealt | Captures suffered | Legal contact | Out-of-reach | Invalid |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `v5_region_attacker` | 30–2–32 | 28 | 1 | 64/64 | **0** | **0** |
| `v5_scout_striker` | 34–0–30 | 33 | 0 | 62/64 | **0** | **0** |
| `v5_core_defender` | 0–16–48 | 0 | 0 | 38/64 | **0** | **0** |
| `v5_dual_team` | 14–16–34 | 14 | 0 | 64/64 | **0** | **0** |

Per fixture (mean enemy core cells damaged, mean max simultaneous deficit dealt):

| Candidate | vs `v4_local_defender` | vs `v4_claimer` | vs `v4_concentrated_attacker` | vs `v4_scout` |
| --- | --- | --- | --- | --- |
| `v5_region_attacker` | 16–0–0, 8.00 / 8.00 | 14–2–0, 8.00 / 7.75 | 0–0–16, 0.00 | 0–0–16, 0.00 |
| `v5_scout_striker` | 16–0–0, 8.00 / 8.00 | 16–0–0, 8.00 / 7.94 | 1–0–15, 0.62 | 1–0–15, 0.50 |
| `v5_core_defender` | 0–0–16, — | 0–16–0, — | 0–0–16, — | 0–0–16, — |
| `v5_dual_team` | 14–0–2, 8.00 / 7.88 | 0–16–0, 8.00 / 5.56 | 0–0–16, 0.00 | 0–0–16, 0.00 |

The zero column is the phase's most important honest finding and is discussed
in Section I.3.

**The freeze was invalidated once.** A first implementation was frozen, its
digests recorded, and a full holdout executed; the geometry defect of
Section D.3 was then found by a Phase C unit test and classified as a
correctness defect. The agents were fixed, re-frozen with new digests, and the
development and holdout sets were re-run from scratch. **Only the second
holdout run is reported below**; the first is discarded, and no result from it
informed any tuning decision.

---

## G. Frozen holdout results (seeds 301–308)

Executed once against the frozen implementation, same matrix: **256 matches**.

| Candidate | W–L–T | Captures dealt | Captures suffered | Legal contact | ≥2 enemy core cells | Deficit dealt > 1 | Damaged / repaired | Processes | Out-of-reach | Invalid |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :--: | ---: | ---: |
| `v5_region_attacker` | 29–3–32 | 29 | 1 | 64/64 | 32 | 32 | 16/16 | 1 | **0** | **0** |
| `v5_scout_striker` | 32–0–32 | 31 | 0 | 58/64 | 34 | 34 | 9/9 | 1 | **0** | **0** |
| `v5_core_defender` | 0–16–48 | 0 | 0 | 35/64 | 0 | 0 | **48/48** | 1 | **0** | **0** |
| `v5_dual_team` | 14–16–34 | 14 | 0 | 64/64 | 32 | 32 | 28/28 | 2 | **0** | **0** |

Holdout agrees with development throughout — no seed overfitting. Total across
development + holdout: **512 matches, 0 out-of-reach rejections, 0 invalid
actions, 0 exceptions, 0 forfeits.**

A lint-only refactor (`SIM102`, nested `if` → `and`) was applied to
`v5_core_defender` after this run. Because a lint refactor to qualified code
must be *proved* behaviour-neutral rather than assumed, the entire 256-match
holdout was re-executed against the final bytes and the resulting 256 result
rows compared: **byte-identical**. The table above therefore describes the exact
shipped source.

### Admission criteria

| Archetype | Criterion | Result |
| --- | --- | --- |
| Regional attacker | Attacks multiple distinct addresses | **PASS** — mean 140 unique write addresses; 17 distinct addresses even against a static target |
| | Produces > 1 simultaneous core deficit | **PASS** — 32/64 holdout runs; 8.00 mean deficit vs `v4_local_defender` |
| | Full core capture in some deterministic cases | **PASS** — 29 captures |
| | No illegal / out-of-reach actions | **PASS** — 0 |
| Scout / striker | Moves without contact | **PASS** — 64/64 runs; mean max displacement 190 |
| | Gains legitimate contact | **PASS** — 58/64 |
| | Transitions into attack | **PASS** — traced: every action before the first write is a MOVE, and the first write happens on an observation with a visible anchor |
| | Attacks multiple useful addresses | **PASS** — mean 118 unique addresses |
| | Remains legal | **PASS** — 0 |
| Defender | Inspects own-core cells | **PASS** — traced READs cover all 8 cells |
| | Detects damage | **PASS** — READs returning a foreign `previous_read_owner` |
| | Repairs cells | **PASS** — **48/48** damaged runs repaired |
| | Defends while an enemy is visible | **PASS** — > 25% of actions taken under pressure are READs; > 50% of pressured ticks contain an inspection |
| | Never starves defensive duty | **PASS** — reserved budget, asserted directly |
| Multi-process | Declares ≥ 2 processes | **PASS** — 2, in every run |
| | Shares sum to 1.0 | **PASS** — exactly 1.0 |
| | Multiple processes receive action opportunities | **PASS** — traced 4/4 split of Q=8 per tick |
| | Materially different responsibilities | **PASS** — keeper writes exactly its own core; raider writes only ground it does not own; the two sets are disjoint |
| | Actions remain legal | **PASS** — 0 |

---

## H. Legality and determinism

**Legality.** Across all 512 qualification matches plus the 100-match sanity
tournament, per-entrant trace status counts for the V5 starters were:

```
APPLIED                 : all decisions
REJECTED_OUT_OF_REACH   : 0
REJECTED_INVALID        : 0
EXCEPTION               : 0
```

Action kinds observed are a subset of `{read, write, move}` in every match.
Per-tick applied action slots never exceeded Q=8 (asserted directly per starter).
No diagnostic was ever emitted.

**Determinism.** Same seed + same matchup + same starts reproduces identical
behaviour. Verified over 12 paired re-runs (6 matchups × seeds 201 and 305),
comparing a SHA-256 digest of the full decision stream (agent id, process id,
action, observation, applied result, plus all declaration records) and of the
replay tick stream. **12/12 identical**, and the same property is asserted per
starter in the test suite.

One methodological note worth recording: raw file digests of replay and trace
artifacts *do* differ between two identical runs, because trace records carry
`wall_time_ms` and the replay header carries generation timestamps. Determinism
is a property of decisions and arena state, not of file bytes; hashing whole
files would have produced a false non-determinism report, and did on first
attempt.

No starter uses global randomness. `MatchContextV2.rng` is not used by any V5
starter.

---

## I. Strategic-diversity audit

### I.1 Measured profiles

Measured from real matches, not read from source. Per-starter means over the
256 holdout matches, except the last two columns which come from a controlled
identical-scenario run against `fixture_idle_target`.

| Agent | Procs | Reaches | Shares | Max displacement | Unique write addrs | Unique hostile addrs | Own-core cells written | READs | Movement class |
| --- | :--: | --- | --- | ---: | ---: | ---: | ---: | :--: | --- |
| `v5_region_attacker` | 1 | 16 | 1.0 | 234 | 140.1 | 122.7 | 2.38 | No | Drift, then hold beside contact |
| `v5_scout_striker` | 1 | 40 | 1.0 | 195 | 118.1 | 100.1 | 1.83 | No | Arena-crossing strides, then hold |
| `v5_core_defender` | 1 | 12 | 1.0 | **4** | 8.6 | 6.0 | **5.02** | **Yes** | Station-keeping |
| `v5_dual_team` | **2** | 32, 12 | 0.5, 0.5 | 223 | 139.5 | 130.4 | **7.95** | No | Raider pursues, keeper holds |

### I.2 Distinctness by axis

| Axis | `v5_region_attacker` | `v5_scout_striker` | `v5_core_defender` | `v5_dual_team` |
| --- | --- | --- | --- | --- |
| Process count | 1 | 1 | 1 | **2** |
| Reach | 16 | 40 | 12 | 32 + 12 |
| Movement | drift then hold | deliberate arena search | station-keeping only | split: pursue + hold |
| Target acquisition | **none — live observation only** | **expiring contact memory (60t)** | own core, by READ | **memory shared between processes (90t)** |
| Write geometry | expanding symmetric, `±core_size` | ascending linear, `2 × core_size` window | repair queue + core rotation | forward block of `core_size` |
| Defence | none | none | **primary** | secondary (blind) |
| READ usage | none | none | **primary — sole user** | none |
| Internal state | 1 cursor | contact + tick + cursor | queue + 2 cursors + budget | shared contact + 2 cursors |

No two starters share a profile. Target acquisition is distinct **in kind** in
all four cases — no memory, private expiring memory, own-core inspection, and
memory shared across processes. This is asserted mechanically by
`test_v5_starters_are_not_four_versions_of_one_strategy`, which builds a
behavioural profile for each starter from an identical controlled match and
requires all four to be distinct. Nothing here is "same sweep, different reach".

### I.3 Two honest limitations, reported rather than tuned away

**(1) Contact-centred attack converts only against opponents standing on their
objective.** Every V5 offensive starter takes all eight core cells against
`v4_local_defender` and `v4_claimer`, which stay on their cores — and **zero**
against `v4_concentrated_attacker` and `v4_scout`, which leave home. The reason
is structural and legal, not a defect: an attacker is never told where the enemy
core is, so it can only press ground it has legitimately sensed, and that ground
is the enemy's *anchor*, not the enemy's *objective*. This is the exact problem
that more advanced target acquisition — `v4_quorum`'s core-base hypothesis,
R4's READ-derived ownership evidence — exists to solve, and it is a natural
Phase D teaching topic. It is deliberately not solved here: doing so would make
the simplest offensive starter substantially harder to read.

**(2) `v5_region_attacker` is blind in self-play.** Two identical agents
drifting at the same constant speed in the same direction preserve their
separation forever, so they never make contact: 0/8 development seeds produce
contact and 0 addresses are written.

This is **pre-existing population behaviour, not a Phase C regression**.
Measured on the same eight seeds:

| Agent (self-play) | Seeds with contact | Total unique write addresses |
| --- | :--: | ---: |
| `v4_concentrated_attacker` (bundled, unchanged) | 0/8 | 0 |
| `v4_scout` (bundled, unchanged) | 0/8 | 0 |
| `v5_region_attacker` | 0/8 | 0 |
| `v5_scout_striker` | 3/8 | 48 |
| `v5_core_defender` | 0/8 | 32 (maintains its core) |
| `v5_dual_team` | **8/8** | 104 |

R3 §J.5 already used exactly this configuration (`v4_concentrated_attacker`
self-play) as its zero-write negative control. The V5 family is not uniformly
affected — `v5_dual_team`, whose two processes carry different reaches, makes
contact on every seed. The finding is documented as a teaching point in
`docs/V5_STARTER_AGENTS.md` rather than patched, because patching it after the
sanity tournament would be precisely the tournament-driven tuning this phase
was told not to do.

---

## J. Product sanity tournament (seeds 401–404)

Predeclared seed set, run once against the frozen implementation. Roster: the
four V5 starters plus the unchanged bundled advanced example `v4_quorum`.
5 × 5 × 4 = **100 matches**, both slot orders, self-play included.

```
cross-agent matches: 80        self-play matches: 20
ties: 44                       timeouts: 49
decisive core captures: 51
TOTAL out-of-reach rejects: 0  TOTAL invalid/exception: 0
```

| Agent | W | L | T | Win % | Captures | Zero-write runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `v4_quorum` (unchanged reference) | 29 | 0 | 3 | 90.6% | 24 | 0 |
| `v5_region_attacker` | 12 | 8 | 12 | 37.5% | 12 | 1 |
| `v5_scout_striker` | 10 | 6 | 16 | 31.2% | 10 | 0 |
| `v5_core_defender` | 0 | 23 | 9 | 0.0% | 0 | 0 |
| `v5_dual_team` | 0 | 14 | 18 | 0.0% | 0 | 0 |

Findings against the four things this tournament exists to catch:

* **Completely inert starters** — none. The single zero-write run is
  `v5_scout_striker` vs `v5_region_attacker` at seed 402, where the attacker was
  core-captured on tick 3 before it took an offensive action. `v5_core_defender`
  writes in every run; its self-play produces a stable 1000-tick draw with 4
  distinct core cells maintained, which is correct behaviour for a defender.
* **Pathological endless ties** — no. 51 of 100 matches end in a decisive core
  capture.
* **Accidental overwhelming dominance** — no new starter dominates. The
  strongest agent by a wide margin is the pre-existing `v4_quorum`, which is the
  expected and desirable ordering: a beginner starter should not out-perform the
  advanced six-process example.
* **Duplicated behaviour** — no. Head-to-head results are not symmetric between
  the two attackers (`v5_region_attacker` beats `v5_dual_team` 5/8 and
  `v5_core_defender` 7/8; `v5_scout_striker` beats `v5_core_defender` 8/8 but
  `v5_dual_team` only 1/8), which is inconsistent with them being the same
  strategy.

`v5_core_defender` and `v5_dual_team` record 0 wins. Both are qualified anyway:
the gate is "the intended strategy demonstrably functions", not "must win", and
the defender's core was never captured in the entire 256-match holdout. No
starter was tuned in response to these standings.

---

## K. Product discovery

Verified end-to-end from an empty data root, not inferred:

```
$ BYTEFRAY_ROOT=<empty dir> python -m battle_engine agents
 - v4_claimer               V4 Claimer                   [Python] blob=none
 - v4_concentrated_attacker V4 Concentrated Attacker     [Python] blob=none
 - v4_defender_scout        V4 Defender Scout            [Python] blob=none
 - v4_local_defender        V4 Local Defender            [Python] blob=none
 - v4_quorum                V4 Quorum (Advanced Example) [Python] blob=none
 - v4_scout                 V4 Scout                     [Python] blob=none
 - v5_core_defender         V5 Core Defender (Starter)   [Python] blob=none
 - v5_dual_team             V5 Dual Team (Starter)       [Python] blob=none
 - v5_region_attacker       V5 Region Attacker (Starter) [Python] blob=none
 - v5_scout_striker         V5 Scout Striker (Starter)   [Python] blob=none
```

| Surface | Change required | Why |
| --- | --- | --- |
| CLI (`bytefray agents`, `--a-type`, tournament CLI) | **None** | All bootstrap from `STARTER_AGENT_NAMES` and list via `discover_agents`. |
| Agent Designer / GUI catalog | **None** | `app/services/agent_catalog.py` calls `discover_agents_in`; `app/agent_designer.py` calls `ensure_starter_agents`. No UI code touched. |
| Packaging (wheel / sdist) | **None** | `battle_engine = ["data/**/*"]` already covers new starter directories; `*.py[cod]` already excluded. |
| Windows installer (`tools/installer.iss`) | **None** | Contains no agent names. |
| `battle_engine/starters.py` | **Four names appended to `STARTER_AGENT_NAMES`, plus a comment** | The single minimum necessary integration change. |

No Agent Designer redesign, no parameter controls, no UI work — those are
Phase D and Phase E.

---

## L. Compatibility

* **All six `v4_*` agents are unchanged.** Zero bytes modified in
  `agents/v4_*/` or `engine/src/battle_engine/data/starter_agents/v4_*/`,
  enforced by test and confirmed by `git status --short` (no `v4_*` path
  appears as modified).
* **All eleven pre-V4 starters are unchanged** (`runner`, `writer`, `seeker`,
  `spiral`, `claimer`, `strider`, `hunter`, `wanderer`, `adaptive`, `raider`,
  `sentinel`).
* **No historical ID reused or re-pointed.** The four V5 IDs are new.
* **Roster ordering preserved.** The V5 names are appended after `v4_quorum`;
  a test asserts the historical entries still precede them.
* `test_v4_historical_immutability.py` and
  `test_v4_production_integration.py` pass unchanged.

**One pre-existing observation, deliberately not fixed:** `v4_claimer` and the
Agent API v1 `claimer` both claim territory with signature byte `0xC1`. The
existing uniqueness test (`test_default_python_agents.py::
test_starter_signature_bytes_are_unique`) only covers the seven v1 Python
starters, so this overlap between two frozen historical agents was never in
scope. Phase C's own signature test is therefore scoped to the bytes Phase C
introduces — each V5 byte (`0xA5`, `0x5B`, `0xDF`, `0x6B`) must be unclaimed by
any other bundled starter — rather than asserting global uniqueness, which would
have required editing a historical agent. Recorded here so the decision is
visible rather than silent.

---

## M. Validation

All runs sequential, each with its own intentional `--basetemp`.

| Gate | Result |
| --- | --- |
| Phase C suite (`engine/tests/test_v5_starter_agents.py`) | **54 passed** |
| Starter / discovery / packaging suites | 107 passed (`test_starter_agents.py`, `test_default_python_agents.py`, `test_v4_production_integration.py`, `test_v4_quorum_advanced_example.py`, `test_v4_historical_immutability.py`, `test_command.py`) |
| Stable V4 equivalence + Phase B hygiene | 31 passed (`test_v4_stable_ruleset_equivalence.py`, `test_v5_alpha1_phase_b_engine_hygiene.py`) — **stable engine behaviour unchanged; no golden fixture was updated** |
| `python -m pytest` (full) | **3106 passed, 0 failed, 0 errors, 14 skipped, 3 deselected** in 353.19 s |
| `ruff check .` | **All checks passed** (0 errors) |
| `mypy engine/src/battle_engine` | **Success: no issues found in 106 source files** |
| `mypy client/src/battle_client` | **Success: no issues found in 16 source files** |
| Product version | `5.0.0a1` — unchanged |
| R1/R2 residue in production source | **None.** `grep` over `engine/src`, `client/src`, `app`, `agents` for `rules-5-r1`, `rules-5-r2`, `R1_ALPHA1`, `R2_ALPHA1`, `process_integrity`, `process_mortality`, `objective_target_oracle`, `has_process_mortality`, `died_tick`, `mortality_active`, `oracle_active` returned zero matches. |

Phase B's full-suite baseline was 3,052 tests. The suite is now 3,106 passing:
**+54, exactly the Phase C tests added**. No pre-existing test was weakened,
skipped, or deleted.

### One transient failure, investigated and dismissed

An intermediate full-suite run reported
`test_default_python_agents.py::test_completes_matches_against_every_other_default_agent[adaptive]`
failing with `PermissionError: [WinError 5]` from `os.replace` inside
`result_model.write_json_atomic`, on a path under the shared repo-local
`.pytest-tmp`. It was reproduced in isolation with its own `--basetemp`:
**7 passed**. The failure is Windows file-locking interference on the shared
temp root, in an Agent API **v1** starter (`adaptive`) and an evaluation-state
write that Phase C does not touch. The two full-suite runs performed with
dedicated `--basetemp` directories both passed cleanly.

---

## N. Repository health

| Check | Result |
| --- | --- |
| Git mutation commands executed | **None.** No `add`, `commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `restore`, `checkout`, `switch`, `clean`, `stash`, `cherry-pick`, `gc`, or `prune`. |
| HEAD | `f7a543dc1ed1b9528d315ae2a14941bba0dd9646` — unchanged from phase start |
| `.git/index` or `.git/index.lock` touched | No |
| Background / detached processes launched | **None.** Every command ran in the foreground and terminated normally. |
| Production engine runtime files modified | **ZERO** — `git diff --stat` over `rules.py`, `ruleset_policy.py`, `process_runtime.py`, `python_runtime.py`, `vm.py`, `scheduler.py`, `replay.py`, `match_service.py`, `scoring.py` is empty |

### Exact file scope

**Modified (1):**

```
engine/src/battle_engine/starters.py     4 names appended to STARTER_AGENT_NAMES + explanatory comment
```

**Added (11):**

```
agents/v5_region_attacker/{agent.py, agent.yaml}
agents/v5_scout_striker/{agent.py, agent.yaml}
agents/v5_core_defender/{agent.py, agent.yaml}
agents/v5_dual_team/{agent.py, agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_region_attacker/{agent.py, agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_scout_striker/{agent.py, agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_core_defender/{agent.py, agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_dual_team/{agent.py, agent.yaml}
engine/tests/test_v5_starter_agents.py
docs/V5_STARTER_AGENTS.md
docs/research/v5/V5_ALPHA1_PHASE_C_STARTER_AGENTS.md
```

**Deleted:** none.

### Frozen source digests (SHA-256, `agent.py`; packaged copies verified identical)

```
33b1ccf8c649e1f60d083ea45762bde0f05e852a1a9624fd18180c33c2ccb911  v5_region_attacker
3467f23896e6a4588bac1883798cd115f5b2d4a7667cfd96a4ddde54d0e09db1  v5_scout_striker
137848e03a64adb69ba0afd924d592e1f41ca2fea1041a3a3afc4bf9dd489b1b  v5_core_defender
db1e89dde868cb14a42b40fd9580519fe52358156382852848b4044d47df16e9  v5_dual_team
```

---

## O. Verdict

Success criteria, checked against evidence:

| Criterion | Status |
| --- | --- |
| Small coherent V5 starter population exists | Four starters |
| Each teaches a distinct useful API-v2 concept | Region offence, search/memory, READ-driven defence, multi-process roles |
| At least one simple starter shows legal objective-capable regional pressure | `v5_region_attacker`, 197 lines, 29 holdout core captures |
| Exploration, defence and multi-process concepts clearly represented | `v5_scout_striker`, `v5_core_defender`, `v5_dual_team` |
| Source understandable rather than tournament-optimised | 181–202 lines each, one strategy per agent, 0 wins accepted for two of them |
| All starters deterministic and legal | 12/12 paired digests identical; 0 illegal actions in 612 matches |
| Population strategically diverse | Distinct on 8 measured axes; asserted by test |
| `v4_*` agents historically intact | Byte-for-byte, enforced by test |
| Stable V4 engine semantics unchanged | Equivalence suite passes; zero engine runtime edits |
| No R1/R2 mechanics returned | Residue grep clean |
| Version remains `5.0.0a1` | Confirmed |
| Validation clean | 3106 passed / 0 failed; ruff clean; both mypy targets clean |
| Phase D work not begun | No parameter schemas, no presets, no Authoring Guide, no Designer changes |

### **PHASE C COMPLETE — READY FOR AUTHORING GUIDANCE & PARAMETER SCHEMAS**

The exact next phase is **Phase D — Authoring Guidance & Parameter Schemas**.
Two Phase C findings are recommended inputs to it: the structural limit on
contact-centred target acquisition (Section I.3(1)) and the constant-velocity
self-play blindness (Section I.3(2)), both of which are concrete, measured,
worked examples for the Authoring Guide.
