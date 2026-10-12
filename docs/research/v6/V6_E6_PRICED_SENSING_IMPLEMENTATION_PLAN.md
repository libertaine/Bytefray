# Bytefray V6 E6 — Priced Sensing: Implementation Plan

**Status: APPROVED PLAN (research lead, 2026-09-25).** Implementation phases I-0 to I-6 are authorized, stopping at Checkpoint A. At this commit nothing is implemented, and no Ruleset, agent, seed list, match or probe exists. The plan maps every requirement of the registered pre-registration ([`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md), **PR**) to the smallest change that meets it, and orders the work into commits and checkpoints.
**Branch:** `v6-research` at `9d43cac`, the priced-sensing design boundary.
**Date:** 2026-09-25
**Governing records:** the PR; [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**); AGENTS.md (architecture boundaries, testing, compatibility).

---

## 0. Ground Rules

- **The PR and this plan are approved.** Implementation runs through phases I-0 to I-6 (§2) and stops at Checkpoint A.
- **Generating seeds, running controls and running the treatment are each a separately authorized step.** No step here generates a seed or runs a family agent under a treatment Ruleset.
- **Commits.** Each phase is its own commit or commits, with exact test counts. At the end of implementation: the full suite, `mypy` and `ruff`, reported as run.
- **Probes.** No gameplay probe. Agent behavior is verified with synthetic observations (§5.4). Engine semantics under the treatment are verified with scripted test agents that are not family members (§4). The only matches the family plays before authorization are control-Ruleset smoke tests that assert no invalid action and record no outcome.

**Forbidden changes**, following the E-series pattern:
- `scheduler.py`, `python_runtime.py` (capture), `vm.py`, `placement.py`;
- `telemetry.py` and the replay and result schemas;
- `agent_api.py`, except the one additive context field (§3.4);
- every existing fixture;
- all E2–E5 tooling, freezes, pre-registrations and corpora;
- `client/` and `app/`.

---

## 1. Traceability: Each Registered Requirement to Its Change

| PR requirement | Change | Where | Verified by |
|---|---|---|---|
| §2 treatment field and semantics | `RulesetPolicy.detection_radius`; `resolve_sensing_radius(reach)`; one visibility line | `ruleset_policy.py`, `process_runtime.py:818` | §4 engine tests |
| §2 validation in two layers | Policy: `None` or a positive integer. Match: 2*d* < `arena_size`. | `RulesetPolicy.__post_init__`; controller `__init__` | §4 |
| §2 conditions | Two research Ruleset identities, as independent literal copies of their parents | `rules.py`, `ruleset_policy.py`, lifecycle sets, evaluation allow-list and CLI choices | §4 one-field and isolation tests |
| DR decision 3: a public radius | `MatchContextV2.detection_radius`, additive | `agent_api.py`; 3 construction sites; worker protocol | §4 |
| §3 population | 18 packages (9 members × primary and twin), sharing one policy source | `tools/research/v6/e6/fixtures/agents/` | §5.4 behavior tests; fingerprints |
| §3.2 opaque IDs; D-5 discipline | Static AST gate | `tools/research/v6/e6/discipline.py` | Negative controls must fail (§5.5) |
| D-1 visibility | An independent re-derivation of every callback's visible set from the trace's action stream | `tools/research/v6/e6/rederive.py` | Scripted scenarios, and a mutation that uses declared reach |
| D-2 initial invisibility | Distances in the tick-0 replay snapshot | `gates.py` | Unit test on seeded layouts |
| D-3 parent identity | A parent byte-identity freeze, committed **before** any engine change (I-0); controls reproduce it | `engine/tests/test_v6_e6_parent_byte_identity.py`; runner | Goldens |
| D-4 no early blind strike | A trace scan over ticks 1–2 | `gates.py` | A planted-leak negative control |
| §9 two matrix identities | The structural digest (I-6, no seeds); the execution identity from the structural digest and the seed commitment (I-7); both carried in every cell's provenance | `matrix.py`, `seeds.py`, `run_e6.py` | §8 tests; the runner refuses a mismatch |
| D-6 seed commitment | Generate, encode, commit, verify; reveal before interpretation | `tools/research/v6/e6/seeds.py`, `run_e6.py` | §8 tests; the interpret command refuses without a passing D-6 |
| D-7 mirror relabeling | E4's relabel gate, reused | `analyze_e4` / `gates.py` | Reused tests, plus E6 wiring |
| CQ-1 search inertness | Action streams compared across the search variants under the controls | `gates.py` | A mutation where search leaks into control play must fail |
| §4 and §5 metrics and hypotheses | Payoffs, BR_ε, universality, bootstrap, Δ, H0 A/B, FL, PF-1 to PF-4 | `payoff.py`, `analyze_e6.py` | §7 unit and mutation tests |
| §6.2 alternation | E4 `cell_metrics` (FMA, FPS), reused | `analyze_e6.py` | Reused qualification |
| §6.6 traces | A per-cell trace path in the E6 runner; compression; an extractor | `run_e6.py`, `telemetry.py` | §6 |
| §7 and §8 interpretation and disposition | Row and disposition tables with exhaustive mapping tests | `interpretation.py` | Every triple maps to exactly one row; invariant violations fail closed |
| §9 seed protocol | The seed tool; the runner refuses to run without a matching commitment | `seeds.py`, `run_e6.py` | §8 |
| §10.3 control-against-control | A runner command | `run_e6.py` | Required readings (PR §10.3) |
| §11 hard stops | An unlock chain like E5's: freeze, gates, execution-source check, confirmations | `run_e6.py` | Runner tests |

---

## 2. Phases, Commits and Checkpoints

| Phase | Content | Ends with |
|---|---|---|
| **I-0** | **A parent byte-identity freeze** for `research-scale` and `disruption-slot1`: named scenarios with existing fixtures, at non-matrix seeds 1–3, both orientations. **Committed before any engine file changes.** | The goldens commit |
| **I-1** | The `detection_radius` field, both validation layers, the resolver, the one visibility line, the two Ruleset identities, lifecycle registration, and §4 tests | Focused tests pass; parent goldens unchanged |
| **I-2** | The context field and plumbing: direct execution, the worker, validation, and the worker protocol field; tests under both executors | Tests pass |
| **I-3** | The family: 18 packages, the shared policy source, manifests with parameters, and opaque IDs; the discipline gate; behavior tests with synthetic observations; control-Ruleset smoke tests | Fingerprints recorded |
| **I-4** | Trace capture in the runner, compression, the extractor, and size accounting | Tests pass |
| **I-5** | The analyzer, re-derivation, gates, payoffs and interpretation; unit, exhaustive and mutation tests | Tests pass |
| **I-6** | The **structural matrix identity** (conditions, population, fields, counts, parameters; **no seeds**), `preregistration.json` (a test checks it against the PR), the analysis freeze, and a freeze record with slots for the seed commitment and the execution matrix identity; ROADMAP and FUTURE_PLANS entries worded as a question | **CHECKPOINT A: the research lead reviews the implementation.** |
| **I-7** | *Separately authorized.* Generate the seeds (§8). Commit **only** the seed commitment and the execution matrix identity into the freeze record, **before the first control cell** | The commitment commit |
| **Q** | *Separately authorized.* Controls C-E6 and C-E6L, one worker per field; D-3 control reproduction; CQ-1; control-against-control (PR §10.3); measured trace size (§6.3) | **CHECKPOINT B: authorization for the treatment** |
| **T** | *Separately authorized.* Treatments; treatment gates (D-1, D-2, D-4, D-7); the frozen gameplay analysis; **the seed reveal and D-6**; E6-D's final status; the registered interpretation and disposition; the results record. If D-6 fails: VOID, and no gameplay interpretation. | Reveal, interpretation and results commits |

---

## 3. Engine Changes: The Exact Surface

### 3.1 `RulesetPolicy.detection_radius` (`ruleset_policy.py`)

- **The field.** `detection_radius: int | None = None`, placed after `initial_anchor_placement`, with a docstring in the style of the E3–E5 fields. It must say:
  - `None` is the historical rule;
  - an integer *d* limits passive visibility to min(reach, *d*), inclusive;
  - action reach, capture, disruption and scheduling are unaffected.
- **Policy validation**, in `__post_init__` alongside the existing checks: `None`, or an `int` that is not a `bool` and is ≥ 1. Anything else raises `ValueError`.
- **The resolver.** `resolve_sensing_radius(self, reach: int) -> int` returns `reach` if the field is `None`, and otherwise `min(reach, self.detection_radius)`.

### 3.2 `process_runtime.py`

- **The visibility line.** `_visible_enemy_anchors`, line 818: `radius = observer.reach` becomes `radius = self.ruleset_policy.resolve_sensing_radius(observer.reach)`. Nothing else in the function changes.
- **Match validation**, in the controller `__init__`: if the policy's radius is not `None` and `2 * radius >= arena_size`, raise `ValueError`.

### 3.3 Ruleset identities

This follows E5's registration pattern: independent literal copies, never `replace()`, with every field spelled out.

- **Primary:** `bytefray-rules-6-research-sensing-r32`, copying `RULESET_V6_RESEARCH_SCALE` (`:621–631`) with `detection_radius=32`.
- **Companion:** `bytefray-rules-6-research-disruption-slot1-sensing-r32`, copying `RULESET_V6_RESEARCH_DISRUPTION_SLOT1` (`:746–759`) with `detection_radius=32`.
- **Registration:** constants and docstrings in `rules.py`; `PROCESS_RULESET_IDS`; `_RULESET_POLICIES`; `ACTIVE_RESEARCH_RULESET_IDS`; `__all__`.
- **Explicit selection only:** the evaluation allow-list and CLI choices, as E5 did.
- **Kept out of** the stable surfaces, the Designer, `run`, `agents test` and the tournament.

### 3.4 `MatchContextV2.detection_radius` (`agent_api.py`)

- **The field.** `detection_radius: int | None = None`, additive and last, with a default. It is **not** an Agent API version change: the same precedent as `parameters` (`agent_api.py:203–217`).
- **Where it is filled in:**
  - direct execution, `process_runtime.py:406–419`: the policy's value;
  - the worker: an additive `detection_radius` key in the reset request, sent from `process_runtime.py:490–498` through `AgentWorkerHandle.reset` and read at `agent_worker.py:444–451`, defaulting to `None` when absent;
  - validation, `agent_validation.py:118`: `None`.

### 3.5 Expected size

About 10–20 changed lines in `ruleset_policy.py`, `process_runtime.py`, `agent_api.py`, `agent_worker.py` and `agent_validation.py`, plus the Ruleset constants and registrations. No schema changes.

---

## 4. Engine Tests (I-1, I-2)

**Policy:**
- The default is `None`.
- Validation accepts `None` and 1, 32 and 255. It rejects 0, −1, `True`, 32.0 and `"32"`.
- Match validation rejects *d* = 256 at A = 512 and accepts 255.

**Identity:**
- Each new Ruleset differs from its parent in `detection_radius` alone (a field-by-field comparison).
- The existing Rulesets all read `None`.

**Byte identity.** The parent goldens of I-0 reproduce unchanged. With `None`, every E2–E5 golden still passes.

**Visibility semantics.** These use scripted **non-family** test agents with explicit positions, following the E4 `manipulation_gate` precedent:
- **Inclusive boundary:** an enemy anchor at distance 32 is visible; at 33 it is not.
- **Wrap:** an observer at 500 sees an enemy at 20 (circular distance 32).
- **min(reach, *d*):** at reach 10, distance 11 is invisible and 10 is visible. At reach 256, distance 33 is invisible.
- **The restriction property:** over an enumerated grid of positions and reaches, visible under the treatment ⊆ visible under the parent.
- **Unchanged rules:** a suppressed observer does not sense; a dead enemy's anchors are excluded; sharing is entrant-wide.
- **Action reach is unaffected:** a READ or WRITE at distance 200 still applies under the treatment.

**Initial invisibility, geometry only.** For seeded layouts at A = 512 over a range of seeds, every pair of core bases is ≥ 64 apart, which is more than 32. This is a pure placement call; no match is run.

**Context.** Under the treatment, both the direct and the worker executor deliver `detection_radius == 32`. Everywhere else they deliver `None`.

**Isolation.** Neither new ID appears in the Designer, `run`, `agents test` or the tournament choices, and both are in the active research set.

**Mutation tests**, each of which must fail the suite:
- `<` in place of `<=`;
- *d* used in place of min(reach, *d*);
- declared reach used, ignoring *d*;
- *d* applied to READ or WRITE reach;
- *d* applied when the field is `None`.

---

## 5. The Matched Family (I-3)

### 5.1 Packages

- **Location.** `tools/research/v6/e6/fixtures/agents/<id>/` holds `agent.py` and `agent.yaml`.
- **IDs.** 18 opaque package IDs, `e6_q01` to `e6_q18`, assigned to (member, primary or twin) at I-3 and recorded in the freeze record. At runtime every entrant is its seat label, `"A"` or `"B"`, so package IDs never appear in a match (PR §3.2).
- **One policy source.** Every `agent.py` is **byte-identical**, and a test asserts it.
- **Parameters.** Each `agent.yaml` declares the parameter schema, with that package's values as defaults (the V5 parameter mechanism, `AGENT_API_V2.md` §parameters):
  - `search`: string; `none`, `fast`, `paced` or `read`;
  - `posture`: string; `attack`, `guard` or `paint`;
  - `evade`: boolean;
  - `processes`: integer, 1 or 2;
  - `adaptive`: boolean.
- **Declarations.** Every member declares reach `arena // 2` for each process. Single-process members declare one process with share 1. SPLIT declares `sensor` with share 0.25 and `striker` with share 0.75.

### 5.2 Shared semantics: the specification to freeze

One agent instance serves all of an entrant's processes, so knowledge is entrant-wide.

**Knowledge:**
- the enemy anchors currently visible;
- the last-known enemy anchor, as an (address, tick) pair;
- the confirmed enemy core base, or unknown;
- the per-tick "written" set;
- the search cursor.

**Callback index.** The member counts its own callbacks within the current tick, restarting whenever `current_tick` changes. Odd and even indexes give its position within a chunk (DR §E.1, row 7).

**Information event:** a non-empty visible set, or a READ that returns value `0xCE` with an owner that is neither itself nor `None`.

**Core inference:**
- **Unverified adoption**, the E2–E5 fixture convention. At the entrant's first callback of the match, if exactly one enemy anchor address is visible and it lies at circular distance ≥ 64 from the entrant's own core base, it is adopted as the enemy core base.
  - This lets the family play the parent's documented forced line.
  - Under the treatment it never fires: at a first callback every visible anchor lies within 32 of the entrant's own core, and therefore cannot be a core base, since cores are ≥ 64 apart.
- **Otherwise, verification.** Starting from the last-known anchor *a*, READ at a stride of 8 across [*a* − 64, *a* + 64] until a hit (`0xCE`, owned by the opponent). Then READ downward until the value or owner changes. The base is the last hit.

**The `search` routine** runs only when no enemy anchor is visible, none is remembered and the core is unknown. Under each control that never happens after the first callback, which is what CQ-1 checks.

| `search` | Behavior |
|---|---|
| `fast` | On every callback: MOVE by 64 × *dir*, with *dir* = ±1 drawn from `context.rng` at reset. For SPLIT, only the sensor moves. |
| `paced` | MOVE only on odd callback indexes. On even indexes, take the idle action. |
| `read` | READ at `own_core_base + dir × (64 + 8m)`, for m = 0 to 48 in order. That arc covers every allowed enemy core position, whichever the direction. Never MOVE. |
| `none` | Take the idle action. |

**The postures:**

| `posture` | Each callback, in priority order |
|---|---|
| `attack` | (1) WRITE any visible enemy anchor not yet written this tick; (2) if the core is known, WRITE the next cell of the enemy core not yet written this tick; (3) if the core is unknown but an anchor is known, take the next verification READ; (4) otherwise, the idle action |
| `guard` | (1) WRITE any visible enemy anchor not yet written this tick; (2) otherwise, WRITE the next own-core cell with the value `0xCE`, keeping the core beacon, with a cyclic cursor over cells 0 to 7 carried across ticks |
| `paint` | Always the idle action |

**The idle action** is to paint: WRITE the next cell of an outward sequence from the entrant's own core, alternating sides (base+8, base−1, base+9, base−2, …), with a fixed value. Which side it starts on is drawn from `context.rng`.

**Evasion** (`evade = on`): at the first callback, before anything else, MOVE once by a sign and a magnitude in [8, 64], both drawn from `context.rng`. Eight is the smallest symmetric displacement that guarantees an anchor on core cell 0 leaves the 8-cell core in either direction, and 64 is the maximum MOVE.

**SPLIT.** The sensor runs `search`, and otherwise disrupts visible anchors or idles. The striker runs `attack`, and never moves.

**ADAPT.** These transitions are fixed in advance:

| From | Trigger | To |
|---|---|---|
| (start) | — | Paint mode |
| Paint mode | An enemy anchor is visible | Guard mode, returning to paint mode 8 ticks after an anchor was last visible |
| Paint or guard mode | Its one own-core READ, at the first callback of tick *t*, of own-core cell (*t* − 1) mod 8 (a deterministic scan of the whole core every 8 ticks), returns an owner other than itself | Evade (at most once per match), then guard mode, returning to paint mode 8 ticks after damage was last seen |
| Paint mode | No information event and no detected own-core damage by tick 16 [PR O-6] | Fast search and attack, permanently |

**Randomness** comes only from `context.rng`, drawn at reset in a fixed order by every member: *dir*, the paint side, the evade sign, the evade magnitude. There is no other state and no wall clock.

Under the harness, the stream is keyed to seat and slot, not to the package (PR §3.2). So members sharing a seat and seed draw identical values, and any randomized behavior they share is identical. That is what lets CQ-1 hold by construction.

### 5.3 Why these choices, without tuning

- Every behavior is a direct transcription of DR §I and §H.2.
- The only numbers are:
  - the 64-cell stride, the maximum;
  - the stride-8 READ, the core size;
  - the evade range [8, 64]: the smallest displacement that always leaves the core, up to one maximum MOVE;
  - SPLIT's shares, a quarter to sensing;
  - ADAPT's 8 and 16 [PR O-6].

  Each is fixed here, before any E6 data exists (plan decisions P-2 to P-5, §11).
- The idle action is painting, so that search always competes with a productive alternative. Otherwise PACED's non-search actions would simply be wasted.

### 5.4 Behavior tests: synthetic observations, no matches

The policy object is driven with constructed `ObservationV2` sequences:
- the fast searcher's MOVE pattern and direction;
- the paced searcher moves only on odd indexes;
- the READ probe's addresses;
- both cases of the unverified-adoption rule, including rejection at distance < 64;
- the verification READs and base finding;
- guard priorities;
- evasion exactly once;
- SPLIT's roles by `self_process_id`;
- every ADAPT transition, at its exact tick;
- RNG draw order;
- identical behavior between primary and twin packages.

**Smoke tests under the control Rulesets only:** one match per member against a trivial opponent, asserting no forfeit and no invalid action. **No outcome is recorded or asserted.**

### 5.5 The static discipline gate (D-5)

An AST check over every package's `agent.py`:

| Check | Rule |
|---|---|
| Allowed imports | `battle_engine.agent_api`, plus a standard-library whitelist: `__future__`, `dataclasses`, `typing`, `enum`, `math`, `collections`, `itertools`, `functools`. Nothing else. |
| Forbidden attribute access | `.seed` on any object |
| Forbidden names | `open`, `exec`, `eval`, `compile`, `__import__`, `globals`, `locals`, `vars`, `breakpoint`, `input` |
| Forbidden literals | Any family package ID. This is defensive: at runtime entrants are seat labels. |

**Negative controls**, which the gate must fail: planted files that import `battle_engine.placement`, read `context.seed`, call `open`, or contain `"e6_q03"`.

---

## 6. Traces and Telemetry (I-4)

### 6.1 Capture

- **The trace itself.** The E6 runner sets `MatchRequest.trace_path` for each cell, writing `trace.jsonl` in the cell directory. This is additive in the tooling; the engine's trace writer (`match_service.py:784`) already exists and is qualified.
- **Compression.** When a cell completes, the runner gzips the trace atomically, to `trace.jsonl.gz`, and removes the plain file.
- **Executor.** The same `EvaluationService` path and executor mode the E2–E5 runners use, with one worker per field.

### 6.2 Determinism and privacy

- **Not byte-reproducible.** Trace records carry `wall_time_ms`, so traces are not byte-reproducible, and byte identity of traces is **not** a gate.
- **Deterministic fields only.** The analysis reads only deterministic fields.
- **The compact telemetry is deterministic**, and its per-cell SHA-256 is recorded.
- **Privacy.** The trace header records the raw `match_seed`. Traces, replays and results stay under git-ignored `runs/` until the reveal (PR §9.5). That is also DR §E.1 row 12.

### 6.3 Size, and a rule fixed now

| Quantity | Estimate |
|---|---|
| Size of a `decision_v2` record, from its schema: about 16 fields including the nested observation, sorted keys | About 0.5–0.7 KB |
| Callbacks per match | At most 16,000 (8 per entrant per tick, × 2 entrants, × 1000 ticks) |
| Raw trace per match | About 8–11 MB |
| Compressed (repetitive JSON, typically 8–15× with gzip) | About 1 MB |
| For 11,520 matches | About 10–13 GB compressed, plus about 8 GB of replays (at the E5 design review's estimate of about 0.7 MB per match) |

**The rule, fixed before any data.** Measure the real compressed size on the first control field.
- If the projected total is **above 40 GB**, keep the compact telemetry (§6.4) for **every** cell, and keep raw traces only for a registered subset: every cell whose seed is in positions 1–4 of the ordered list.
- Otherwise, keep raw traces for every cell.

Either way, PR §6.6's "callback-level telemetry for every cell" is met.

### 6.4 The E6 extractor (`telemetry.py`)

**One row per callback**, in execution order:

> (tick, entrant, process_id, callback index, visible tuple, action kind, operand, value, applied status, normalized address)

**Per-cell summaries:**
- first-detection tick per entrant, and which entrant saw first;
- pre-detection MOVEs, probe READs and off-core MOVEs;
- information events by tick;
- the inputs to D-4.

This also feeds D-1's independent re-derivation (§7.2).

---

## 7. The Analysis Instrument (I-5)

### 7.1 Modules (`tools/research/v6/e6/`)

| Module | Content |
|---|---|
| `matrix.py` | Conditions, members, packages, fields and parameters; the **structural digest** and identity (`v6-e6-matrix-v1-…`); the **execution identity** (`v6-e6-exec-v1-…`), computed from the structural digest and the seed commitment (PR §9, step 4). It refers to the seeds only by their commitment. |
| `preregistration.json`, `preregistration.py` | The frozen PR transcription and its loader. A test compares every threshold, set and row with the PR's tables. |
| `telemetry.py` | The trace extractor (§6.4) |
| `rederive.py` | D-1: reconstructs every process's position and suppression at each callback, and so the visible set, from tick-0 anchors, the normalized results of every MOVE, and WRITEs to enemy anchor addresses. It applies the condition's λ exactly as `_is_suppressed` does. Independent of the engine. |
| `discipline.py` | D-5 (§5.5) |
| `gates.py` | D-1, D-2, D-4, D-7 and CQ-1; the control-against-control readings |
| `payoff.py` | O-VALUE, O-PAYOFF, BR_ε, universality, bootstrap, Δ. Exact `Fraction`s, and a jointly resampled seed multiset. |
| `analyze_e6.py` | E6-H0, H1T, H1C, H2 and H3; PF-1 to PF-4; the descriptive sections (PR §6.2–§6.7); the companion |
| `interpretation.py` | PR §7 rows and §8 disposition, as tables with the fail-closed rule |
| `seeds.py` | §8 |
| `run_e6.py` | `plan`, `execute` (with confirmations), `telemetry`, `gates`, `qualify`, `control-vs-control`, `analyze`, `reveal` and `interpret`, in that order, behind an unlock chain like E5's. `execute` refuses unless the private seed file's commitment and the execution identity match the freeze record, and writes both identities and the commitment into every cell's provenance. `interpret` refuses unless D-6 has passed. |
| `analysis_freeze.py` | The analysis identity (`v6-e6-freeze-v1-<digest>`), separate from the matrix identity |

**Reused unchanged, and pinned by hash:**
- `experiment_harness`: cells, `trajectory_key`, `cell_seat_result`;
- `analyze_e3.outcome_class`;
- `analyze_e4`: `is_capture`, the seat metrics, the relabel gate;
- `e4/cell_metrics`: FMA and FPS.

### 7.2 Tests

- **Metric units.** Every metric is tested on small hand-built tables with known answers: u, BR_ε with ties, universality when members are identical (the control case), Δ, A and B (B computed over exactly the cells A counts), and FL.
- **The ε boundary.** A difference of exactly ε counts as ≥ ε; ε − 1/128 does not.
- **Bootstrap.** The fixed RNG gives a fixed result, and resampling is joint across cells.
- **Exhaustive mapping.**
  - All 18 (E6-D, H1T, H1C) triples map to exactly one row.
  - The H2 qualifier inside R-CREATES, and the H0 qualifier inside R-NO-CHOICE, each cover all three statuses.
  - The disposition covers every combination of E6-D, the kill criteria, the row and E6-H2.
  - A deliberately corrupted table fails closed.
- **D-1 re-derivation.** It agrees with the engine on scripted scenarios under both λ values, including suppression and wrap.
- **D-4.** Fails on a planted early core write without an information event.
- **CQ-1.** Fails when a search parameter is made to leak into control play.

**Mutation tests**, each of which must fail:
- ε applied strictly;
- the best response taken over Π rather than Π_F, so ADAPT is included;
- u(*i*, *i*) not forced to 1/2;
- seeds weighted unequally;
- a separate resample per cell;
- P_never using `< 0`;
- B computed over capture-only cells (the superseded definition), or over all cells;
- an interpretation or disposition issued before D-6 passes;
- a provenance record missing either matrix identity;
- FL counting `< 3`;
- PF-4 using `> 9/10`;
- "not SUPPORTED" read as REFUTED;
- the companion overriding the primary;
- D-4 checking ticks 1–3;
- D-1 using declared reach;
- CQ-1 comparing outcomes instead of action streams.

---

## 8. Seed Tooling (§9 of the PR; run only at I-7)

**`seeds.py` functions:**

| Function | Behavior |
|---|---|
| `generate(n=32)` | `secrets.randbelow(2**53)`, rejecting duplicates |
| `encode(seeds) -> bytes` | Decimal ASCII, one per line, LF, a trailing LF |
| `commitment(seeds) -> str` | SHA-256 hex of the encoded bytes |
| `verify(seeds, commitment)` | Checks the list against the commitment |

**Storage.** `runs/research_v6_e6/seeds.private.txt`. The `runs/` directory is git-ignored (`.gitignore:23`), and the file lies outside every agent package.

**Commitment.** The freeze record receives only the commitment, the generation time and the tool's commit SHA. This is committed **before any matrix cell**.

**The runner** loads the private file, recomputes the commitment, and refuses to execute if it differs.

**Reveal**, after the frozen gameplay analysis and **before** interpretation (PR §9, step 7). The list is committed (for example as `tools/research/v6/e6/seeds_revealed.txt`), and D-6 runs: the commitment matches, the execution identity recomputes, and every recorded cell seed is on the list. Only then does `interpret` run.

**Execution identity.** `execution_identity(structural_digest_hex, commitment_hex)` returns `v6-e6-exec-v1-` followed by the first 12 hex of the SHA-256 of the UTF-8 bytes of *structural digest hex*, LF, *commitment hex*, LF.

**Tests**, run before I-7 on a fixed **test** list that is never used for the matrix:
- golden encoded bytes;
- a golden commitment, and a golden execution identity from a fixed structural digest;
- duplicates rejected;
- the upper bound respected;
- `verify` fails on a reordered list and on a changed value;
- the runner refuses when the seed file's commitment or the execution identity differs from the freeze record;
- `interpret` refuses before D-6 has passed.

---

## 9. Qualification and Execution, for Later Authorization

1. **I-7.** Generate the seeds; commit the seed commitment and the execution matrix identity, before the first control cell.
2. **Controls.** Run C-E6 and C-E6L, both fields, one worker per field.
3. **Qualification.** It must pass all of:
   - D-3: the parent goldens still pass on the executing commit, and the controls ran the unmodified parent Rulesets from a clean tree;
   - CQ-1;
   - control-against-control, with PR §10.3's required readings;
   - D-2 and D-7 on the controls;
   - the trace-size rule (§6.3).

   **Any failure is a hard stop, and every fix is blind to the treatment.**
4. **CHECKPOINT B:** the research lead authorizes the treatment.
5. **Treatments.** T-E6 and T-E6L, then the treatment gates D-1, D-2, D-4 and D-7.
6. **Frozen gameplay analysis**, with the seeds still hidden.
7. **Seed reveal and D-6.** E6-D's status becomes final. If D-6 fails, the disposition is VOID and no gameplay interpretation is issued.
8. **The registered interpretation and disposition.**
9. **The results record**, in three layers.

---

## 10. Cost Estimate

| Item | Estimate |
|---|---|
| Matches | 11,520 |
| Rate | E5 ran about 0.64 s per match with one worker (T-E5 F1: 1,344 cells in about 14 minutes; E5-R §A). Traces add unmeasured overhead; assume up to 2×. |
| Wall time | About 1–1.5 hours per condition on one worker. With F1 and F2 run in parallel, about 3–4 hours for all four conditions. |
| Storage | About 8 GB of replays and 10–13 GB of compressed traces (§6.3) |

---

## 11. Decisions

The research lead decided these on 2026-09-25, together with the pre-registration's O-1 to O-8 (PR §0).

| # | Decision | Decided |
|---|---|---|
| **P-1** | The trace-retention threshold | 40 GB, with the subset of seed positions 1–4 (§6.3). Callback telemetry stays complete for every cell. |
| **P-2** | The evade range | [8, 64], sign and magnitude drawn from the seeded RNG (§5.2) |
| **P-3** | SPLIT's shares | 0.25 sensor, 0.75 striker |
| **P-4** | ADAPT's damage check | One cyclic own-core READ per tick: at the first callback of tick *t*, own-core cell (*t* − 1) mod 8 |
| **P-5** | The idle action | Outward alternating painting, starting side drawn from the seeded RNG |
| **P-6** | Unverified adoption at the first callback (§5.2) | Kept. It lets the family play the parent's forced line, following the E2–E5 fixture convention, and by geometry it never fires under the treatment. |

Implementation I-0 to I-6 is authorized and stops at Checkpoint A. Seed generation, controls and the treatment each need separate authorization.
