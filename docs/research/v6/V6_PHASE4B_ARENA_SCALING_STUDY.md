# Bytefray V6 Phase 4B — Raw Arena-Scaling Study

**Status:** Complete
**Branch:** `v6-research`
**Baseline:** `803cba8` (`docs(v6): correct gameplay research methodology`)
**Ruleset introduced:** `bytefray-rules-6-research-scale`
**Predecessor:** [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md)
(Phase 4A/4A.1)

---

## A. Objective

Answer one narrow empirical question, with every other gameplay mechanic held
fixed:

> **What does the existing game become when space gets much larger?**

Not "how should Bytefray be redesigned for a large arena" — that is
Experiment B's question, deferred to Section N below. This phase varied
arena size alone (512 → 65,536 cells, the Phase 4A logarithmic progression)
and measured what happened, without compensating for it.

---

## B. Research Ruleset

### B.1 Identity and registration

`bytefray-rules-6-research-scale` (`BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID`,
`engine/src/battle_engine/rules.py`) is registered as `RULESET_V6_RESEARCH_SCALE`
in `engine/src/battle_engine/ruleset_policy.py`:

```python
RULESET_V6_RESEARCH_SCALE = RulesetPolicy(
    ruleset_id="bytefray-rules-6-research-scale",
    supported_runtime_kinds=frozenset({"python"}),
    supported_python_api_versions=frozenset({2}),
    scheduler_mode="chunked",
    scheduler_chunk_size=2,
    scheduler_rotate_start=True,
    core_placement="seeded",
    process_selection="round_robin",
)
```

Every field is a deliberate, independent literal copy of stable
`RULESET_V4`'s own values — never a live `dataclasses.replace(RULESET_V4,
...)` reference, so a future edit to `RULESET_V4` cannot silently mutate this
research identity's frozen semantics. The two objects being field-for-field
equal (`ruleset_id` aside) is instead a *verified* fact, checked permanently
by `engine/tests/test_ruleset_policy.py::test_v6_research_scale_matches_stable_v4_fields_except_id`.

### B.2 Relationship to stable V4

The research Ruleset shares every gameplay mechanic with stable v4:
scheduler (chunked, K=2, rotating start), process selection (round robin),
seeded core placement (identical `placement.seeded_seat_starts` domain
separation — its hash payload is a fixed constant, never the Ruleset ID, so
V4 and the research Ruleset draw byte-identical placements for the same
`(seed, arena_size)`), quota (Q=8, enforced as a hard engine-wide constant
unconditional on Ruleset identity), core size (8, likewise a hard engine
constant), reach (uncapped, zero cost), and scoring/termination (both route
through the identical `RulesetPolicy.resolve_termination` and
`process_runtime.py`, which the module's own docstring records has **zero
Ruleset-identity branching**).

The one and only semantic difference lives one layer up, in *evaluation
methodology*, not in `RulesetPolicy`:

| | `bytefray-rules-4` | `bytefray-rules-6-research-scale` |
|---|---|---|
| Evaluable arena size | Locked to 512 | Any value in `[64, 65536]`, explicit per request |
| Omitted `--arena-size` default | 512 | 512 (same "V4-equivalent" default) |
| `arena_alignment_mode` | `ruleset_v4_seeded_placements` | `ruleset_v6_research_scale_seeded_placements` (distinct string; same underlying mechanism) |
| `identity_version` / `schema_version` | 7 / 7 | 7 / 7 (reused, not bumped — see Section D) |

No fog, terrain, immutable cells, hazards, economic mechanics, scale-normalized
movement/placement/reach, or scaled tick limits were introduced. `max_move_delta`
(64), core size (8), minimum placement separation (64), the scheduler, reach
semantics, scoring, territory bucket behavior, and the 1000-tick horizon are
all held at their stable-v4 values throughout this phase — raw scaling only.

---

## C. V4 Equivalence Gate

Before any large-arena experiment ran, the research Ruleset's behavioral
equivalence to stable v4 at the control arena (512 cells) was proven **live**,
not by inspection: the entire frozen `V6-Bench-8` field (all 28 unordered
pairs, all 8 standard seeds, both orientations = 448 matches) was executed
under **both** `bytefray-rules-4` and `bytefray-rules-6-research-scale` at
arena 512, and every one of the 448 paired matches was diffed
(`tools/research/v6/phase4b_equivalence_check.py`):

```
{
  "total_cells_compared": 448,
  "result_mismatches": 0,
  "placement_mismatches": 0
}

EQUIVALENCE GATE: PASS
```

For every one of the 448 pairs:

* **Placement geometry** — `subject_start`/`opponent_start` were
  byte-identical between the two Rulesets (seeded placement's domain
  separation is a fixed constant, independent of Ruleset ID).
* **Full `result.json`** — winner, `win_mode`, ticks run, per-entrant score,
  territory (`_last`/`_max`/`_avg`/`_pct_*`), kills, deaths, `mem_writes`,
  `alive_ticks`, `termination_reason`, and every entrant metadata field
  (including `derived_seed`, which does not depend on Ruleset ID) — compared
  equal after nulling only `match_id`/`result_id`/`ruleset_id`/timestamps,
  the fields a *different Ruleset identity* is expected, and required, to
  change.
* **Full replay event stream** (`replay.jsonl`, all header + 1000-tick
  records) — compared equal line-by-line after nulling the same
  identity-only fields.

Gameplay was, without exception, identical. Identifiers that incorporate the
Ruleset ID (as they must) differed honestly: every research-scale artifact's
`ruleset_id` reads `bytefray-rules-6-research-scale`; every stable-v4
artifact's reads `bytefray-rules-4`.

This live 448-pair comparison additionally supersedes and extends the
narrower comparison already committed as a permanent regression test in
`engine/tests/test_ruleset_v6_research_scale.py` (2 representative pairs × 3
seeds × both orientations, run on every CI pass) — the full-field run here is
one-time research evidence for this study; the permanent test is what stops
a future regression.

---

## D. Identity

`resolve_v4_seed_geometry` (used unchanged, since `core_placement_mode`
resolves through each Ruleset ID's own registered `RulesetPolicy`, not a
hardcoded table) already produces correct, distinct seeded geometry for the
research Ruleset at any arena size. Two new evaluation-methodology predicates
were added specifically so the research Ruleset would neither literally *be*
stable v4 (and inherit its 512-cell lock) nor fall back to legacy
methodology:

* `is_ruleset_v6_research_scale_methodology` — true only for this one
  Ruleset ID.
* `is_ruleset_v4_derived_methodology` — true for stable v4 **and** the
  research Ruleset (both share the seeded-placement/identity-v7/schema-v7
  recipe); deliberately *not* folded into `is_ruleset_v4_methodology`, whose
  existing callers (the 512-cell arena lock, the omitted-arena-size default)
  specifically mean "this is stable v4."

Identity version **7** (`IDENTITY_VERSION_V4`) and schema version **7**
(`SCHEMA_VERSION_V4`) were confirmed sufficient and reused, per Phase 4A's
recommendation — no version 8 was created. This is safe because
`rules_compatibility_id` and `effective_conditions` (which carries
`arena_size`) are **unconditionally** hashed into `evaluation_id` and
`condition_fingerprint` regardless of identity version
(`evaluation_identity.build_evaluation_id`/`build_pairwise_condition_fingerprint`),
so Ruleset identity and arena size are already, independently,
identity-bearing without needing a new version number. The research
Ruleset's `arena_alignment_mode` string (`ruleset_v6_research_scale_seeded_placements`)
is deliberately distinct from stable v4's own (`ruleset_v4_seeded_placements`)
as an additional, honest self-description — a reader must never infer
"arena size is 512" from the alignment-mode label alone for a
research-scale artifact.

No semantic gap was found that identity version 7 could not represent; the
STOP condition in Section 9 of the governing task was not triggered.

---

## E. V4 Equivalence Gate Evidence — Summary

Already presented in full in Section C; restated as the specific artifact
list for reproducibility:

* Comparison script: `tools/research/v6/phase4b_equivalence_check.py`.
* Corpus runner: `tools/research/v6/phase4b_corpus_runner.py equivalence`.
* Raw artifacts: `runs/research_v6_phase4b/equivalence/{v4,research-scale}/`
  (git-ignored, reproducible byte-for-byte by rerunning the deterministic
  seeded methodology against the recorded agent revisions in Section D
  below).
* Machine-readable report: `runs/research_v6_phase4b/equivalence_check_report.json`.

---

## F. Benchmark Field

`V6-Bench-8`, verified present at the exact repository paths Phase 4A named,
each resolved through the real discovery/loading path (`resolve_agent`),
each running Agent API v2 (confirmed per-agent below), and each
content-fingerprinted via `battle_engine.agent_revisions`:

| Agent | `agent_revision_id` (SHA-256, `agent-revision_` prefix) |
|---|---|
| `Octave` | `e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730` |
| `nemesis_alpha2` | `6d5a8492b34a77cbbbe795152370ed20c65f2c55da20dc96a35f5d28c3b44f5c` |
| `v5_scout_striker` | `290e02004291abd77967bc43e549e07eddad9851915ddd9f5edc2fd5e0de0ac1` |
| `v5_region_attacker` | `8855d950c08f8f95cdca192ed817b853d6350cdbe7ec0bd6d161879e5237ddcb` |
| `v5_dual_team` | `71e9e84c17fe7a6f084ca9b83d0394741c9edfb24df8b593441f97a2910030af` |
| `v4_claimer` | `342d5a20df20c0154774fbbbd643256e1afbc593b9d735ddb831388cfeebc952` |
| `v5_core_defender` | `2a47c0386ff88d58b810eef97a1f093a89050d5ba3a5ae52a31c56eb2de0cc95` |
| `v4_local_defender` | `6a64a4ba742f04e389f1301bd4a0210866d54b3464c7c01bc497138c30318453` |

All eight resolve at `<repo>/agents/<name>`, all report `kind=python`,
`api_version=2`. Full fingerprint record:
`runs/research_v6_phase4b/v6_bench_8_fingerprints.json`. No agent had moved
or was unexecutable; no substitution was needed.

---

## G. Experimental Matrix

**Planned** (task Sec 16): `N(N-1)/2 × seeds × orientations = 28 × 8 × 2 =
448` matches per arena size; `448 × 5 = 2,240` matches total.

**Executed:** exactly 448 completed matches at every one of the five arena
sizes (512, 1024, 4096, 16384, 65536) — **2,240 matches total**, matching
the plan exactly. No discrepancy; the STOP condition on matrix-count mismatch
was not triggered.

Generation method: since `EvaluationRequest` expresses one candidate vs. N
opponents (a star topology), the full round robin was decomposed into the
triangular sequence `candidate = field[i]`, `opponents = field[i+1:]` for
`i = 0..6` — 7 requests whose union is exactly the 28 unordered pairs, each
carrying its own `opponents × 8 seeds × both orientations` cells generated
by the real production evaluation harness (`EvaluationService`/`build_matrix`),
never hand-built. Tooling: `tools/research/v6/phase4b_corpus_runner.py`.

---

## H. Runtime / Storage

**Smoke sweep** (task Sec 17; 3-agent field, seeds 1–2, both orientations, 24
matches at arenas 512 and 65536):

| Arena | Matches | Wall clock | Per match |
|---|---:|---:|---:|
| 512 | 12 | 2.66 s | 0.221 s |
| 65536 | 12 | 2.22 s | 0.185 s |

Per-match cost showed **no meaningful growth with arena size** — confirming
Phase 4A.1's plausibility argument (territory/CPU statistics are tracked
incrementally, not by scanning the arena) as a direct measurement, not merely
an assumption.

**Full sweep** (2,240 matches, all five arena sizes, 448 matches each):

| Arena | Matches | Wall clock |
|---|---:|---:|
| 512 (via equivalence run) | 448 | 83.78 s |
| 1024 | 448 | 94.46 s |
| 4096 | 448 | 98.52 s |
| 16384 | 448 | 99.73 s |
| 65536 | 448 | 112.94 s |
| **Total** | **2,240** | **489.4 s (≈ 8.2 min)** |

A mild upward trend (84 s → 113 s) appears across arena size — plausibly
memory-allocation/GC overhead for the larger arena byte array, not per-tick
gameplay cost — but nowhere near the "prohibitively expensive" territory the
Phase 4A planning estimate flagged as a risk to verify.

**Storage** (measured, not estimated):

| Arena | Artifact size (448 matches: replays + results + evaluation.json) |
|---|---:|
| 512 | 186 MB |
| 1024 | 212 MB |
| 4096 | 226 MB |
| 16384 | 224 MB |
| 65536 | 237 MB |
| **Sweep total** | **≈ 1.06 GB** |

Individual replay sizes ranged from ~4 KB (matches ending in a handful of
ticks via early kill) to ~950 KB (matches running the full 1000-tick
horizon) — confirming the Phase 4A.1 planning estimate ("replay volume
scales with `instr_per_tick × ticks`, not arena size") as a direct
measurement: the ~950 KB full-length figure matches its ~965 KB
extrapolation almost exactly. The equivalence gate's V4-side comparison run
added a further 186 MB (not part of the published sweep dataset, retained
only as the equivalence proof).

**Decision (task Sec 18):** runtime and storage were both far inside
reasonable bounds — no reduction of the research corpus and no gameplay
change were needed to make the study affordable.

---

## I. Aggregate Results

All figures below are pooled over all 28 pairs × 8 seeds × both orientations
(448 matches) at each arena size. Full machine-readable output:
`runs/research_v6_phase4b/phase4b_analysis.json`. Analysis tooling:
`tools/research/v6/phase4b_analyzer.py` (Tier 1, from `result.json`) and its
Tier 2 replay-derived pass (Section J).

| Arena | S = 8000/A | Timeout rate | Mean ticks | Median ticks | Directed 3-cycles | Dominance edges (>0.55) | Spearman ρ vs. A=512 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | 15.625 | 31.2% | 344.5 | 11.0 | 2 | 25 | 1.000 |
| 1024 | 7.8125 | 35.9% | 394.8 | 18.0 | 0 | 24 | 0.976 |
| 4096 | 1.953 | 41.1% | 422.1 | 32.0 | 0 | 23 | 0.976 |
| 16384 | 0.488 | 39.7% | 419.5 | 65.0 | 0 | 24 | 0.952 |
| 65536 | 0.122 | 39.1% | 459.5 | 234.5 | 0 | 25 | 0.952 |

Termination reasons observed across the entire 2,240-match corpus: only
`last_agent_standing` and `tick_limit` — `all_agents_dead` never occurred (no
simultaneous mutual kill was ever recorded).

**Agent aggregate ordering** (win rate, symmetrized over both roles a match
can assign an agent — every match contributes to both agents' tallies):

| Rank | 512 | 1024 | 4096 | 16384 | 65536 |
|---|---|---|---|---|---|
| 1 | Octave (1.00) | Octave (1.00) | Octave (1.00) | Octave (1.00) | Octave (0.97) |
| 2 | v5_scout_striker (0.72) | nemesis_alpha2 (0.68) | nemesis_alpha2 (0.71) | nemesis_alpha2 (0.73) | nemesis_alpha2 (0.75) |
| 3 | nemesis_alpha2 (0.62) | v5_scout_striker (0.65) | v5_scout_striker (0.65) | v5_scout_striker (0.68) | v5_scout_striker (0.68) |
| 4 | v5_region_attacker (0.58) | v5_region_attacker (0.56) | v5_region_attacker (0.52) | v4_claimer (0.54) | v4_claimer (0.57) |
| 5 | v4_claimer (0.44) | v4_claimer (0.46) | v4_claimer (0.50) | v5_region_attacker (0.48) | v5_region_attacker (0.51) |
| 6 | v5_dual_team (0.38) | v5_dual_team (0.38) | v5_dual_team (0.34) | v5_dual_team (0.29) | v5_dual_team (0.26) |
| 7 | v5_core_defender (0.17) | v5_core_defender (0.17) | v5_core_defender (0.18) | v5_core_defender (0.17) | v5_core_defender (0.16) |
| 8 | v4_local_defender (0.09) | v4_local_defender (0.10) | v4_local_defender (0.10) | v4_local_defender (0.10) | v4_local_defender (0.09) |

**Headline finding:** the aggregate hierarchy is remarkably stable under raw
scaling (Spearman ρ against the A=512 baseline stays ≥ 0.95 across every
tested arena). The only visible aggregate movement is a swap between
`nemesis_alpha2`/`v5_scout_striker` (ranks 2–3) and, at the largest two
arenas, `v4_claimer` overtaking `v5_region_attacker` (ranks 4–5) — see
Section J/K for why, despite this aggregate stability, specific *pairwise*
matchups shift far more dramatically.

---

## J. Pairwise Results — Interaction / Stagnation

Full win/draw/timeout matrices per arena are in
`runs/research_v6_phase4b/phase4b_analysis.json`
(`pairwise_win_rates`/`termination_breakdown` per condition). Representative
matrices (row's win rate against column) at the two extremes:

**A = 512:**

```
       Oct   Nem   Sct   Reg   Dua   Clm   Cor   Loc
  Oct    -  1.00  1.00  1.00  1.00  1.00  1.00  1.00
  Nem  0.00    -  0.25  0.84  0.25  1.00  1.00  1.00
  Sct  0.00  0.75    -  0.53  0.78  1.00  0.97  1.00
  Reg  0.00  0.16  0.47    -  0.66  0.94  0.84  1.00
  Dua  0.00  0.75  0.22  0.34    -  0.00  0.50  0.84
  Clm  0.00  0.00  0.00  0.06  1.00    -  1.00  1.00
  Cor  0.00  0.00  0.03  0.16  0.50  0.00    -  0.50
  Loc  0.00  0.00  0.00  0.00  0.16  0.00  0.50    -
```

**A = 65,536:**

```
       Oct   Nem   Sct   Reg   Dua   Clm   Cor   Loc
  Oct    -  1.00  0.88  0.91  1.00  1.00  1.00  1.00
  Nem  0.00    -  0.56  1.00  0.69  1.00  1.00  1.00
  Sct  0.12  0.44    -  0.50  0.91  1.00  0.91  0.91
  Reg  0.09  0.00  0.50    -  1.00  0.00  0.97  1.00
  Dua  0.00  0.31  0.09  0.00    -  0.00  0.50  0.94
  Clm  0.00  0.00  0.00  1.00  1.00    -  1.00  1.00
  Cor  0.00  0.00  0.09  0.03  0.50  0.00    -  0.50
  Loc  0.00  0.00  0.09  0.00  0.06  0.00  0.50    -
```

(`Oct`=Octave, `Nem`=nemesis_alpha2, `Sct`=v5_scout_striker,
`Reg`=v5_region_attacker, `Dua`=v5_dual_team, `Clm`=v4_claimer,
`Cor`=v5_core_defender, `Loc`=v4_local_defender.)

### Interaction / stagnation (Tier 2, replay-derived; task Sec 21)

Computed by a single forward pass over each match's own replay
(`phase4b_analyzer.analyze_replay_tier2`): `first_contact_tick` (earliest
tick any two opposing processes' anchors are within combined reach — the
exact inverse of Phase 4A's own "Disjoint Non-Interaction" stagnation
criterion), `first_hostile_write_tick` (via a full linear cell-ownership
reconstruction, not a single-field lookup), unique addresses written per
entrant, and the longest run of consecutive ticks with zero memory
mutation (checked against Phase 4A's formal stagnation window, W=100).

| Arena | Mean first-contact tick | Matches never in contact | Matches reaching W=100 zero-mutation stagnation |
|---:|---:|---:|---:|
| 512 | 5.5 | 3.6% | 0.0% |
| 1024 | 11.0 | 3.6% | 0.0% |
| 4096 | 43.8 | 3.6% | 0.0% |
| 16384 | 33.3 | 8.7% | 0.0% |
| 65536 | 96.3 | 10.7% | 2.2% |

This directly answers the search-starvation question (task Sec 23): **yes**,
raw scaling measurably delays and, at the largest tested arena, sometimes
prevents contact altogether — the never-in-contact rate roughly triples from
512 to 65,536 cells, and the formal W=100 zero-mutation stagnation window
(defined but never actually reached at any smaller arena in this corpus)
first appears at 65,536. But the effect is far smaller than the aggregate
timeout-rate numbers alone would suggest (Section I): timeout rate rises from
31% to only ~39–41% (not toward 100%), because most of this benchmark field
is not purely local — global-reach agents (Octave above all) still make
contact quickly regardless of arena size, and even local searchers usually
still resolve within the 1000-tick horizon; they are simply slower, not
paralyzed.

Tier 1 activity metrics (per-agent means, pooled across all matches; full
table `runs/research_v6_phase4b/phase4b_archetype_stats.json`) show the same
story from the memory-write side — median match length rising over 21-fold
(11 → 234.5 ticks) while overall timeout rate rises only modestly confirms
that most of the extra time is spent *travelling*, not *deadlocked*.

**Not computed this pass** (explicitly out of scope for this session, not
silently omitted): circular process-anchor displacement over a match,
spatial dispersion between an entrant's own processes, and periodic
deterministic-loop detection. These remain practical future additions to
`phase4b_analyzer.py` if Experiment B needs them.

---

## K. Transitivity / Counterplay

**Directed 3-cycles collapse to zero above the control arena** (2 at A=512,
0 at every larger arena tested) — raw scaling did **not** produce the
non-transitive "healthy ecology" a naive large-arena hypothesis might
predict; if anything, the already-sparse counterplay this benchmark field
exhibits at 512 cells weakens further as the arena grows. Dominance-edge
count (win rate > 0.55) stays essentially flat (23–25 edges out of 56
possible directed pairs) across every arena size.

Opponent-conditioned performance variance (task Sec 8.2's σ²_opp) is where
scale-sensitivity actually shows up. Octave's variance is essentially zero
at every arena (0.0000 → 0.0025): it wins by kill, not by territory
(`kills` ≈ 0.94–1.00 per match, `deaths` = 0.00 throughout — see Section L),
and that mechanism is close to scale-invariant. `v4_claimer`'s variance is
consistently the highest in the field (0.238 at 512, 0.245 at 65536) — its
performance is fundamentally opponent-dependent, and that dependence does
not meaningfully change with scale even though *which* opponents it beats
does (see below).

**A concrete, notable matchup-level rank inversion**, invisible in the
aggregate ranking but visible in the pairwise matrix: `v5_region_attacker`
vs. `v4_claimer` is won 94% of the time by the region attacker at A=512, and
**0%** of the time at A=65,536 — a complete reversal of a single directed
edge. This is consistent with Section L's finding that `v4_claimer`'s
territorial-expansion win condition becomes nearly unreachable at large
arenas (its territory share collapses from 47% to 3%), while its opponent's
regional-suppression tactic (chasing a *nearby* claimer) simply has less
absolute territory to defend before losing. One inverted edge among 56 is
not, on its own, evidence of a durable non-transitive structure — the 3-cycle
count independently confirms the ladder as a whole did not become more
cyclic — but it is genuine, specific evidence that **individual matchup
outcomes are more scale-sensitive than the aggregate leaderboard suggests**,
and is exactly the kind of matchup-conditioned effect Experiment B's
normalization candidates should be evaluated against.

**Conclusion for this question:** raw scaling did not meaningfully weaken
the transitive performance ladder in aggregate (Spearman ρ ≥ 0.95
throughout, 3-cycles at or near zero), but it did materially reshuffle a
handful of specific matchups whose underlying mechanism (territorial
coverage normalized by arena size) is intrinsically scale-sensitive.
Performance in this benchmark field remains **primarily intrinsic** under
raw scaling, with a **minority of specific matchups becoming meaningfully
more opponent/scale-dependent**.

---

## L. Archetype Effects

Per-agent Tier 1 activity means, by arena size (full table
`runs/research_v6_phase4b/phase4b_archetype_stats.json`; `n=112` matches per
agent per arena, i.e. each agent's full share of the 448-match condition):

| Agent | Archetype | 512 territory% | 65536 territory% | 512 kills | 65536 kills | 512 deaths | 65536 deaths |
|---|---|---:|---:|---:|---:|---:|---:|
| Octave | Global sniper | 4.83 | 0.02 | 1.00 | 0.94 | 0.00 | 0.00 |
| nemesis_alpha2 | Artillery / core hunter | 7.02 | 2.00 | 0.43 | 0.50 | 0.30 | 0.25 |
| v5_scout_striker | Mobile pursuit | 12.67 | 0.55 | 0.59 | 0.41 | 0.14 | 0.11 |
| v5_region_attacker | Regional suppressor | 9.98 | 0.28 | 0.41 | 0.42 | 0.16 | 0.12 |
| v5_dual_team | Coordinated 2-process | 4.71 | 0.09 | 0.17 | 0.17 | 0.27 | 0.47 |
| v4_claimer | Territorial expander | 46.91 | 2.97 | 0.15 | 0.00 | 0.55 | 0.29 |
| v5_core_defender | Reactive defense | 0.80 | 0.01 | 0.00 | 0.00 | 0.52 | 0.54 |
| v4_local_defender | Passive floor control | 0.30 | 0.00 | 0.00 | 0.00 | 0.81 | 0.67 |

* **Dynamic global hunter (Octave).** Dominant and essentially
  scale-invariant: it wins almost every match by kill (kills ≈ 0.94–1.00,
  deaths = 0.00 at every arena size, even 65,536), which directly answers
  the Phase 4A question "does global reach turn into an instant teleporting
  weapon across 65,536 cells?" — **yes, functionally**. Its mean alive-ticks
  (time-to-kill) rises 10.1 → 117.1 across the sweep — it does take
  proportionally longer to close the distance — but its kill rate barely
  degrades, since reach remains uncapped and zero-cost at every scale
  tested.
* **Territorial expansion (v4_claimer)** is the archetype raw scaling hits
  hardest. Its territory-percentage win condition is normalized by arena
  size, and its absolute expansion rate is capped by the fixed Q=8 quota —
  so its territory share collapses 16-fold (47% → 3%) as the arena grows
  128×, exactly the "does poor performance under raw scaling motivate
  Experiment B" case the methodology anticipated. Notably, its *aggregate*
  win rate does not collapse in step (0.44 at 512 rising to 0.57 at 65536)
  — it increasingly wins by opponents timing out or dying to something
  other than the claimer's own territory dominance, not by claiming
  territory itself; see the matchup-inversion in Section K.
* **Bounded/regional sniper (v5_region_attacker)** and **mobile searcher
  (v5_scout_striker)** both show moderate territory decay and a modest
  kills/deaths shift, consistent with active search taking longer at scale
  but remaining broadly effective — they retain positive aggregate win
  rates (0.48–0.68) throughout, unlike the purely territorial archetype.
* **Coordinated multi-process (v5_dual_team)** shows rising deaths
  (0.27 → 0.47) alongside falling territory (4.71% → 0.09%) — its two-process
  split (explorer + core-keeper) appears to lose effectiveness as travel
  time grows, since a larger arena stretches the raider further from its
  own keeper without any coordination-range mechanic to compensate.
* **Defenders (v5_core_defender, v4_local_defender)** are essentially flat
  across every arena size — they were never territory- or kill-competitive
  at 512 cells and remain so at 65,536; scale did not create or destroy
  their (already weak) floor-control role.

No archetype label above was retrofitted beyond what the measured
kill/death/territory/win-rate pattern directly supports.

---

## M. Conclusions

What raw scaling actually changed, from 512 to 65,536 cells, holding every
other Bytefray mechanic fixed:

1. **Contact is delayed, not prevented, for most of this field.** Mean
   first-contact tick rose roughly 17× (5.5 → 96.3), and the never-in-contact
   rate roughly tripled (3.6% → 10.7%), but full search starvation (the
   formal W=100 stagnation window) appeared in only 2.2% of matches even at
   the largest arena tested — because a majority of this benchmark's agents
   either have uncapped reach (Octave) or actively search rather than sit
   still.
2. **Timeout rate rises but plateaus, not approaching 100%.** 31% → ~39–41%,
   flattening rather than climbing linearly with the S=8000/A action-density
   collapse — action density alone does not mechanically determine the
   timeout rate for this field; agent search strategy matters more than the
   raw density number.
3. **The aggregate competitive hierarchy is scale-robust.** Spearman rank
   correlation against the A=512 baseline never drops below 0.95; directed
   3-cycles, already sparse, disappear entirely above the control arena.
   Raw scaling did not manufacture new non-transitive structure in this
   field — if anything it reduced what little existed.
4. **Individual matchups are far more scale-sensitive than the aggregate
   ranking suggests.** The clearest example, a complete 94%→0% reversal
   between `v5_region_attacker` and `v4_claimer`, shows that a mechanism
   which is intrinsically arena-size-relative (territory percentage) can
   flip a specific pairwise outcome even while the overall leaderboard
   barely moves.
5. **Territorial expansion is the archetype raw scaling breaks.** A
   fixed-quota expander's win condition, expressed as a percentage of a
   128×-larger arena, becomes nearly unreachable — territory share collapsed
   16-fold for `v4_claimer` specifically. Kill-based and search-based
   archetypes degraded far more gently.
6. **Global, uncapped, zero-cost reach is close to scale-immune.** Octave's
   kill rate and zero-death record persisted essentially unchanged from 512
   to 65,536 cells — directly confirming the Phase 4A concern that unbounded
   reach behaves like "an instant teleporting weapon" regardless of arena
   size, since nothing in raw scaling touches the cost or range of a
   declared reach.

None of the above required, or received, any runtime code change once the
sweep began (task Sec 27); every number in this document comes from the
single, unmodified `bytefray-rules-6-research-scale` implementation
qualified in Section C.

---

## N. Experiment B Recommendation

Raw scaling's own results point at two specific, evidence-justified
normalization candidates, in priority order:

1. **Movement stride / travel-time normalization
   (`max_move_delta(A)`).** The single largest driver of every degradation
   measured here — delayed contact, rising median match length, and rising
   (though plateauing) timeouts — is that a fixed 64-cell stride covers a
   shrinking fraction of the arena as it grows. Phase 4A's own
   control-equivalent proportional candidate,
   `max_move_delta(A) = max(64, ⌊A/8⌋)` (anchored to reproduce today's 64 at
   A=512), is the most direct, best-justified first test: it targets exactly
   the mechanism (Section J/L) shown here to be responsible for the
   contact-delay effect, without touching reach, scoring, or placement.
2. **Territory-normalization or a non-percentage-based scoring lever for
   expansion-oriented agents.** Section L's finding that `v4_claimer`'s win
   condition collapses specifically because territory is scored as a
   *percentage* of arena size is a distinct effect from stride/travel time,
   and would not be fixed by (1) alone — a faster claimer still claims a
   vanishing percentage of a much larger arena. This is not a "normalize
   movement" question; it is a scoring-methodology question, and should be
   scoped and tested as its own controlled variable rather than folded into
   Experiment B's geometry normalization.

Reach normalization (bounded reach ladders) is **not** recommended as the
next test in isolation: Phase 4A's own V3 Phase 2 "bulldozer effect" warning
applies unchanged, and this phase's data gives no new evidence that bounding
reach would resolve the specific effects measured here (contact delay,
territory collapse) without first addressing movement/scoring. Tick-horizon
scaling (Linear `T ∝ A`) remains a secondary, cost-gated candidate per
Phase 4A Section 5.2, not a primary recommendation — this phase's own Fixed
`T=1000` control already resolved most matches (58.9%–68.8% non-timeout)
even at 65,536 cells, so there is not yet strong evidence the fixed horizon
alone is the dominant constraint stride normalization would leave unaddressed.

Experiment B itself is **not implemented** in this phase, per the governing
task's explicit scope boundary.

---

## Research Integrity Addendum (2026-09-22)

Two independent research-integrity reviews have established that the Phase 4 arena-scaling and movement research line was grounded in flawed causal premises and compromised by test and benchmark defects:

1. **V4 Tick-1 Forced-Win Gate:** Shipped stable `bytefray-rules-4` contains a deterministic tick-1 Seat-A forced core capture under competent global-reach play (`CompetentGlobalSniperProbe`), winning on tick 1 before Seat B ever executes an instruction. This seat/order-driven exploit was the unacknowledged driver of apparent lethality in global probes, invalidating interpretations of global reach as balanced gameplay.
2. **Benchmark Corpus Tracking (Octave):** The V6-Bench-8 field previously depended on an untracked local `Octave` agent in the user's private `agents/` directory. Octave has now been fingerprinted (`e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730`) and permanently committed to tracked repository fixtures under `tools/research/v6/fixtures/agents/Octave/`.
3. **Territory Scoring Invariance:** Territory scoring was incorrectly described in Phase 4B as scaling with arena percentage and suffering "dilution." In reality, `ScoringPolicy` awards 1 point per 64 raw cells held ($\lfloor \text{cells} / 64 \rfloor$) independently of arena size. Scoring was always invariant to arena dimensions.
4. **Agent Context Arena Size:** Later reports asserted that `ObservationV2` and match context hid `arena_size` from agents. In fact, `context.arena_size` was already supplied in `AgentContext` upon initialization.
5. **Fallacy of $\sigma^2_{\text{opp}}$ as Counterplay:** Variance of win rates across opponents is a mathematical property of intermediate ranks in a purely transitive 1D skill hierarchy, not evidence of opponent-dependent counterplay or non-transitivity. It has been replaced by 1D rating models, matchup residuals ($R_{ij} = W_{ij} - \hat{W}_{ij}$), upset reversals, and explicit tie tracking.
6. **Cycle Disappearance Artifact:** The apparent disappearance of directed 3-cycles at larger arenas was an artifact of win rates slipping below the fixed 0.55 dominance threshold, not a reversal or restructuring of competitive ordering.
7. **Line Closure & Transition to E2:** The arena-scaling and movement normalization line is closed. Active research pivots to E2 — Multi-Tick Capture Hold to address the root causal vulnerability identified in stable V4.
