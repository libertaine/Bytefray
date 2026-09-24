# Bytefray Future Plans

This document catalogues architectural concepts, evaluation methodologies,
tooling, and gameplay ideas that lie beyond the currently scheduled work of the
active V6 modernization program (or were resolved during past milestones). See
[ROADMAP.md](ROADMAP.md) for the active V6 execution sequence and shipped
milestone history.

Ideas are preserved here, organized by area, so they are not lost — while being
labeled honestly by maturity so none of them is mistaken for an active commitment.

## Status Classification

Status labels used throughout this document:

- **Planned** — explicitly scoped for active or immediately upcoming scheduled work on the roadmap.
- **Candidate** — concrete, plausible design with demonstrable value; prioritised when usage or empirical evidence justifies it.
- **Research Question** — requires hypothesis-driven empirical investigation (data, prototypes, or both) before committing to a design.
- **Exploratory** — a design direction being thought through; not yet validated against evidence, and the shape could change substantially.
- **Deliberately Deferred** — evaluated and intentionally postponed to protect core priorities.
- **Completed / Absorbed** — realized in a shipped release; preserved here for architectural context and provenance.
- **Retired** — removed from active runtime support during modernization; historical records preserved.

---

## Accessible agent-authoring language / DSL

**Status: Candidate (Unscheduled).**

A small, Bytefray-specific strategy language for users who don't want to
begin by writing Agent API Python directly. The intent is a **deterministic
domain-specific language**, not ambiguous natural-language programming.

Conceptual pipeline:

```
BFScript (or similar DSL)
  → parser / AST
  → validated intermediate representation
  → Python Agent API v2 backend
```

Principles this would need to hold to, if pursued:

- Suitable for beginning users; constrained and deterministic.
- Generated Python must be inspectable, not a black box.
- Useful as a teaching path *into* Agent API programming, not a permanent
  substitute for it.
- The compiler must reject unsupported target semantics rather than
  silently changing behavior.
- Generated artifacts should retain provenance: source language, compiler
  version, source hash, target/API version, and generated-revision
  identity — following the same honesty precedent Bytefray's agent
  revision store already established for hand-written agents.
- Possible future `compile`/`explain` commands.

**Current disposition:** The earlier blocker ("do not begin until Agent API v2
exists") was resolved when Agent API v2 shipped in Bytefray 4.0.0 (`bytefray-rules-4`).
If implemented, the DSL would compile directly to Agent API v2 (`declare_processes`,
`act`, `ObservationV2`, `ActionKindV2`). However, this remains an unscheduled
candidate: bundled scaffold templates (`bytefray agents create --template ...`)
and starter examples currently meet authoring needs, and active V6 priorities
remain focused on repository diet and runtime modernization rather than new
authoring layers.

---

## Agent packaging / sharing

**Status: Foundational packaging shipped (v1.2.0, v1.3.0, v5.0.0); Ecosystem extensions remain Candidate (Unscheduled).**

See [`docs/specs/agent_package.md`](specs/agent_package.md) for the authoritative
format design. `bytefray agents export`/`agents package show`/`agents import`
package an agent revision into a self-describing portable `.bytefray-agent`
ZIP file, built as a transport wrapper around the content-addressed
`battle_engine.agent_revisions` store. Designer integration was added in v1.3.0
("Export Agent…", "Import Agent Package…") and hardened in v5.0.0.

Deferred ecosystem-facing follow-ups remain open as unscheduled candidates, to
be evaluated only if community distribution warrants them:
- Package signing and verification (PKI).
- Centralized online registry or discovery service.
- DSL-compiler provenance metadata (if a DSL compiler ships).

Do not build registry or PKI infrastructure without actual user demand that
requires it.

---

## Richer evaluation / statistical analysis

**Status: Core analytics and visualization delivered across v1.6–v5.0; Advanced metrics remain Candidate or Exploratory.**

Substantial evaluation capabilities have shipped across successive releases:
- **Statistical significance & win intervals:** Delivered in v1.6.0 Phase 4 (Wilson score intervals on win rates; exact sign/McNemar test over discordant conditions; see [`docs/archive/v1/V1_6_PHASE4_EVALUATION_ANALYSIS.md`](archive/v1/V1_6_PHASE4_EVALUATION_ANALYSIS.md)).
- **Behavior profiling:** Delivered in v1.6.0 Phase 5 (survival, write activity, territory occupancy/retention/spread, kill interaction; see [`docs/archive/v1/V1_6_PHASE5_BEHAVIOR_ANALYSIS.md`](archive/v1/V1_6_PHASE5_BEHAVIOR_ANALYSIS.md)).
- **Evaluation presets:** Delivered in v1.6.0 Phase 3 (reusable `bytefray.evaluation_preset` YAML configs; see [`docs/archive/v1/V1_6_PHASE3_EVALUATION_PRESETS.md`](archive/v1/V1_6_PHASE3_EVALUATION_PRESETS.md)).
- **Multi-entrant & group analysis:** Delivered in v2.0.0-beta2 (directed captor-to-victim interaction matrix, non-pairwise group metrics, seat/layout sensitivity; see [`docs/archive/v2/V2_0_BETA2_PHASE3_MULTI_ENTRANT_ANALYSIS.md`](archive/v2/V2_0_BETA2_PHASE3_MULTI_ENTRANT_ANALYSIS.md)).
- **Comparative visualization in GUI:** Delivered in v3.0.0 Phase 3 (win-rate intervals and behavior-profile widgets in Agent Designer's live and history dialogs; see [`docs/archive/v3/V3_PHASE3_STRATEGY_ANALYSIS.md`](archive/v3/V3_PHASE3_STRATEGY_ANALYSIS.md)).
- **Seeded-placement evaluation methodology:** Delivered in v4.0.0-rc1 (schema 7, `ruleset_v4_seeded_placements`).
- **Replay History discovery & tournament standings:** Delivered in v5.0.0.

Remaining candidates and exploratory items:
- **Global ranking systems (Elo, Glicko, TrueSkill):** **Deliberately Deferred Candidate.** Bytefray evaluations deliberately remain condition-scoped (Ruleset, arena size, action budget, seeds, opponents). Global rating systems flatten distinct experimental contexts and create misleading universal rankings; they will not be added without rigorous evidence that condition-scoped comparison is inadequate.
- **Clustering agents into behavioral archetypes:** **Exploratory (Unscheduled).** While behavior-profile vectors provide the raw data, clustering requires validating that chosen dimensions separate known strategies meaningfully without producing arbitrary groupings.
- **Behavioral distance scalar:** **Deliberately Deferred.** Phase 5 investigated composite distance metrics and found that any cross-dimensional scalar requires arbitrary weights that cannot be objectively defended.

---

## Evaluation performance and scaling

**Status: Parallel execution delivered in v1.6; indexing delivered in v5.0; Distributed evaluation remains Candidate (Unscheduled).**

- **Parallel evaluation:** Delivered in v1.6.0 Phase 2 (bounded local subprocess-worker pool via `--workers N`; see [`docs/archive/v1/V1_6_PHASE2_PARALLEL_EVALUATION.md`](archive/v1/V1_6_PHASE2_PARALLEL_EVALUATION.md)).
- **Fast artifact discovery & indexing:** Delivered in v5.0.0 via the SQLite-backed Replay History discovery engine (`battle_engine.replay_history`).

Remaining scaling candidate:
- **Distributed evaluation:** Candidate (Unscheduled) for running evaluation matrices across multiple networked machines. Currently unscheduled because local parallel execution easily handles matrices up to several thousand cells on modern developer hardware.

---

## Future simulation / combat research

**Status: Research Questions / Long-Range Candidates.**

Preserved as a distinct area because these ideas explore potential gameplay
mechanics that alter core simulation semantics and would require a newly
versioned Ruleset identity separate from `bytefray-rules-4`.

**Context for V6:** Bytefray is currently in the V6 repository diet and
architecture modernization program. Speculative gameplay changes are
deliberately **postponed** until cleanup, modularity, and technical debt reduction
are completed. None of the ideas below is a committed deliverable for the active
V6 cleanup program.

Earlier research programs systematically evaluated several of these candidates:
- The **v2.0 alpha program** (11 alphas) validated vulnerable-core mechanics and
  core observability, establishing `bytefray-rules-2` (see
  [`docs/archive/v2/V2_0_ALPHA_RESEARCH_SUMMARY.md`](archive/v2/V2_0_ALPHA_RESEARCH_SUMMARY.md)).
- The **v3 research program** (8 phases plus closeout) tested locality reach,
  arena density scaling, and defensive scoring events, concluding that no
  Ruleset change was justified and closing without creating a stable Ruleset 3
  (see [`docs/archive/v3/V3_RESEARCH_CLOSEOUT.md`](archive/v3/V3_RESEARCH_CLOSEOUT.md)).
- The **v4 program** designed and delivered the spatial multi-process model and
  spectator intelligence pipeline (`bytefray-rules-4` and Agent API v2).

Findings below reflect what these programs empirically established, retaining
rejected or deferred hypotheses for provenance.

### Core observability

**Status: Completed / Shipped (v2.0.0).**

Alpha 10 found that initializing core cells to byte `0` (indistinguishable from
untouched arena) made undefended cores invisible to search while making defended
cores the only findable target — an inverted incentive. Alpha 11 resolved this
with an owner-maintained non-blank invariant (`CORE_BEACON_BYTE = 0xCE`),
validated across a 1,316-match corpus and shipped as part of `bytefray-rules-2`.
Preserved as historical provenance.

### Territory maintenance / memory decay

**Status: Research Question (Deliberately Deferred).**

A deterministic decay/maintenance-cost mechanic for claimed territory was
designed as a contingency in Alpha 11 (Resolution B), gated on core observability
being insufficient to check territorial expansion. Because core observability
succeeded, the contingency gate never opened: no territory decay mechanic was
implemented or executed. The v3 program tested varying territory scoring weights
(Phase 4) rather than decay. Under `bytefray-rules-4`, spatial anchors, reach
limits, and disruption provide mechanical balance without requiring artificial
decay. The idea remains deferred.

### Advanced offensive mechanics

**Status: Research Question.**

Offense throughout Bytefray remains **emergent through ordinary `READ`/`WRITE`/
ownership and movement primitives**, rather than an abstract engine-level
`ATTACK` action. Both reference attackers in the v2 program (Core Seeker, Core
Tracker) and spatial attackers in v4 achieved deliberate capture using standard
actions. The v3 program independently confirmed this principle from the defense
side: explicit `ATTACK` or `DEFEND` action primitives remain rejected as
unnecessary abstractions that diminish the emergent nature of the arena.

### Arena / field-size research

**Status: Density scaling characterized in v3; Fog-of-war remains an Open Research Question.**

Phase 1 of the v3 program tested a 20-condition grid across arena sizes
128–65536 and action budgets 2–128 (~4000× density span). It proved that arena
size and action quota collapse onto a single dimensionless configured density:
`S = (instr_per_tick × ticks) / arena_size`. The default density sits at or
adjacent to the empirical optimum (see
[`docs/archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md`](archive/v3/V3_PHASE1_ARENA_ACTION_DENSITY.md)).

Fog-of-war and partial observability mechanics remain an **Open Research
Question**. A useful conceptual frame is **information density**: what fraction
of the arena can an entrant observe or influence per tick? Any future
investigation must follow the same empirical, hypothesis-driven discipline.

### Multiple execution processes / multipronged agents

**Status: Fixed spatial multi-process model SHIPPED in v4.0.0 (`bytefray-rules-4`, Agent API v2); Dynamic multi-component coordination remains an Open Research Question.**

- **Delivered in v4.0.0:** Bytefray 4.0 realized the multi-process vision
  through the spatial multi-process platform. Under `bytefray-rules-4` and Agent
  API v2, an entrant declares a fixed roster of processes before tick 0
  (`declare_processes()`). Each process has an independent arena anchor, bounded
  reach, and a shared quota (`Q=8`) distributed across processes in rotation.
  Bundled agents such as `v4_quorum` and `v5_dual_team` demonstrate coordinated
  scouts, attackers, and defenders sharing agent-level state.
- **Open Research Question:** What remains open is dynamic single-entrant
  process management (spawning, deploying, or terminating processes mid-match)
  and autonomous sub-agent communication protocols beyond shared Python memory
  and anchor positions.

### Replication / deployment

**Status: Open Research Question (Unscheduled).**

Whether entrants should be able to create additional execution centers
*during* a match: spawning a process elsewhere, copying code, paying an action/
score cost, and trading immediate offense against investment in expansion.
Deliberately kept out of scope for V4/V5 and deferred beyond the V6 diet program.

### Specialized sub-agents

**Status: Partially realized in v4.0.0; Autonomous sub-agent composition remains an Open Research Question.**

Entrants in V4 can assign specialized roles (scout, defender, attacker) across
their declared process roster. Future research into autonomous sub-agents with
private state, local communication channels, or hierarchical coordination
remains an open research direction.

### Agent API v2

**Status: Completed / Shipped (v4.0.0).**

Agent API v2 was designed, qualified, and released in Bytefray 4.0.0 as the
modern, stable contract for multi-process Python agents (`declare_processes()`,
`act()`, `ObservationV2`, `ActionKindV2`). It is the active production interface
for `bytefray-rules-4`. Agent API v1 remains frozen and is audited for execution
retirement in V6 Scope C (Phase 2B.11/2B.12).

### Agent lifecycle: mutation, evolution, and replication economics

**Status: Open Research Question (Unscheduled).**

A cluster of long-range Ruleset research candidates, requiring hypothesis-driven
qualification before any design work begins:
* Dynamic agents creating sub-agents at runtime.
* Fixed-budget multi-component entrants with variable resource allocation.
* Controlled replication economics (costs in action budget, territory, or score).
* Agent mutation mechanisms (parameter perturbation vs. strategy-family switching).
* Offline evolution between matches vs. online adaptation during a match.
* Lifecycle mechanics: birth, aging, degradation, and inheritance.

None of these mechanics has been prototyped or validated in any released
version; all remain unscheduled future possibilities.

### Execution-trace / intent semantics

**Status: Spectator trace pipeline SHIPPED in v4.0.0; Intent telemetry for defensive mechanics remains an Open Research Question.**

- **Delivered in v4.0.0:** Deterministic execution tracing (`trace.jsonl`),
  Perspective Cam, Spectator Director, and Fight Night presentation were fully
  integrated into the Replay Viewer and CLI in v4.0.0.
- **Open Research Question:** The v3 closeout
  ([`docs/archive/v3/V3_RESEARCH_CLOSEOUT.md`](archive/v3/V3_RESEARCH_CLOSEOUT.md))
  demonstrated that arena ownership changes alone cannot distinguish responsive
  defense from frequent blind rewriting. It identified observable execution
  telemetry (e.g., verifying a `WRITE` was preceded by a `READ` detecting enemy
  damage) as a conceptual path toward defensive scoring. However, this remains
  an open question requiring careful anti-gaming analysis, as self-reported
  intent is easily exploitable.

### Ruleset Status and Evolution Map

Bytefray enforces strict immutability and provenance for ruleset identities.
If new gameplay mechanics are introduced, they belong in a newly versioned
ruleset identity, never a silent modification of an existing one.

Current status across the repository:

- **`bytefray-rules-4`** — **Active Stable Production Control.** Shipped in
  v4.0.0 (promoted from alpha2). The sole executable V4 ruleset and current
  default for matches and tournaments.
- **`bytefray-rules-1`** — **Historical Stable Ruleset (shipped v1.0.0).**
  Frozen 1.0 gameplay. Audited in V6 Phase 2B.11 (Scope C) for retirement
  from active execution registration. Retained indefinitely as a permanent
  decoding, replay, and evaluation-reading identity.
- **`bytefray-rules-2`** — **Historical Stable Ruleset (shipped v2.0.0).**
  Vulnerable core mechanics. Audited in V6 Phase 2B.11 (Scope C) for
  retirement from active execution registration. Retained indefinitely as a
  permanent decoding, replay, and evaluation-reading identity.
- **`bytefray-rules-2-alpha1`, `bytefray-rules-2-alpha11`, `bytefray-rules-3-alpha1`** —
  **Retired from execution in V6 Phase 2B.9.** Closed research identities;
  historical artifacts remain fully readable and replayable.
- **`bytefray-rules-4-alpha1`, `bytefray-rules-4-alpha2`** — **Retired from
  execution in V6 Phase 2B.10.** Prerelease identities retired after proving
  that `bytefray-rules-4` reproduces alpha2's exact gameplay via frozen
  golden characterization (`engine/tests/test_v4_stable_ruleset_equivalence.py`).
  Historical artifacts remain fully readable and replayable.
- **`bytefray-rules-6-research-scale`** — **Active Research Ruleset.**
  Variable-arena baseline retained as an active research control for the upcoming
  E2 (Multi-Tick Capture Hold) causal experiment.
- **`bytefray-rules-6-research-capture-hold-k2`** — **Active Research Ruleset.**
  The E2 treatment: identical to `bytefray-rules-6-research-scale` except
  `capture_hold_ticks = 2`. Explicit selection only (`agents evaluate --ruleset`
  or the Python API); never automatic and absent from `run`, `agents test`,
  tournament, and the Designer
  ([`docs/research/v6/V6_E2_CAPTURE_HOLD_REGISTRATION.md`](research/v6/V6_E2_CAPTURE_HOLD_REGISTRATION.md)).
- **`bytefray-rules-6-research-capture-hold-k2-disruption-slot1`, `bytefray-rules-6-research-disruption-slot1`** —
  **Active Research Rulesets.** The E3 treatments: identical to
  `bytefray-rules-6-research-capture-hold-k2` and `bytefray-rules-6-research-scale`
  respectively, except `disruption_slot_limit = 1` (a disruptive hit suppresses
  its victim processes only for their entrant's next action offer). Explicit
  selection only (`agents evaluate --ruleset` or the Python API); never
  automatic and absent from `run`, `agents test`, tournament, and the Designer
  ([`docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md`](research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md)).
- **`bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes`, `bytefray-rules-6-research-disruption-slot1-mirrored-passes`** —
  **Active Research Rulesets.** The E4 treatments: identical to
  `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` and
  `bytefray-rules-6-research-disruption-slot1` respectively, except
  `scheduler_pass_order = "mirrored"` (the second half of each tick's passes
  offers the entrants in reverse order). Explicit selection only (`agents
  evaluate --ruleset` or the Python API); never automatic and absent from
  `run`, `agents test`, tournament, and the Designer
  ([`docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md`](research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md)).
- **`bytefray-rules-6-research-scale-move`, `bytefray-rules-6-research-scale-move-proportional`** —
  **Retired Research Rulesets.** Closed research identities from the Phase 4
  movement line. Retained for historical characterization test verification and
  persisted artifact readability; retired from ongoing research development.
- **Future gameplay mechanics (E2 — Multi-Tick Capture Hold):** **Completed (research-only).**
  Controlled experiment on the deterministic tick-1 Seat-A forced capture
  identified in stable V4. It asks whether delaying fatal capture for one
  additional qualifying tick creates meaningful opponent-dependent response, or
  merely transforms the original forced line into delay, scheduler-locked
  draws, or another seat pathology. The research Ruleset is implemented and
  qualified, and the research apparatus -- fixtures, capture analyzer, harness
  remediation, frozen matrix and hypotheses, control gate -- is in place; the
  experiment matrix was halted before its treatment condition on a
  capture-analyzer defect, with the controls run and the control gate passed;
  the analyzer has since been repaired, requalified on the control corpus and
  re-frozen as analysis freeze `v6-e2-freeze-v2-db6458596d82`. The treatment
  then ran under that freeze. K = 2 breaks the forced line but mainly turns it
  into delay, scheduler-locked recovery stalemates, zero-core wins and a new
  mirror seat inversion, without sufficient strategic opponent-dependence;
  the Ruleset remains research-only
  ([`docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md),
  [`docs/research/v6/V6_E2_EXPERIMENT_FREEZE.md`](research/v6/V6_E2_EXPERIMENT_FREEZE.md),
  [`docs/research/v6/V6_E2_MATRIX_EXECUTION_HALT.md`](research/v6/V6_E2_MATRIX_EXECUTION_HALT.md),
  [`docs/research/v6/V6_E2_ANALYSIS_FREEZE_V2.md`](research/v6/V6_E2_ANALYSIS_FREEZE_V2.md),
  [`docs/research/v6/V6_E2_CAPTURE_HOLD_RESULTS.md`](research/v6/V6_E2_CAPTURE_HOLD_RESULTS.md)).
- **Future gameplay mechanics (E3 — Slot-Limited Disruption):** **Completed (research-only).**
  The single-variable question after E2: does bounding a disruptive hit to the
  victim's next action offer, instead of the rest of the tick, remove
  whole-tick denial and the first-mover-takes-all tick without adding any
  mechanic? The full frozen matrix (19,456 matches) ran under analysis freeze
  `v6-e3-freeze-v1-506811e78ad8`, and every hard-stop gate passed. Registered
  verdicts: D2, D3, D6 and D9 supported; D0, D4, D5 and D7 refuted; D1 and D8
  neither. No pre-registered interpretation row applies. Descriptively, the
  intervention removes first-mover exclusivity and most seat determination
  but leaves a moderate, last-mover-leaning order dependence. Both Rulesets
  remain research-only
  ([`docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md),
  [`docs/research/v6/V6_E3_EXPERIMENT_FREEZE.md`](research/v6/V6_E3_EXPERIMENT_FREEZE.md),
  [`docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md`](research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md)).
- **Future gameplay mechanics (E4 — Mirrored Pass Order):** **Completed (research-only).**
  The single-variable question after E3, posed as a research question rather
  than a promised improvement: does balancing pass-level response order --
  reversing which entrant goes first in the second half of each tick's passes
  -- neutralize E3's multi-pass residual order dependence while leaving
  opening-pass anchor contests unchanged? Capture, K, λ, quota, chunk size,
  rotation and scoring are unchanged. The two research Rulesets are
  implemented and qualified. The research tooling (an E4 analyzer reusing
  capture analyzer v2 and E3's action/parity analyzer unchanged, and an
  a-priori contest-class table), the E4-H0–H8 and D9′ pre-registration, the
  matrix `v6-e4-matrix-v1-fc29d575dd25` and the analysis freeze
  `v6-e4-freeze-v1-101a941f5e30` are frozen. Both controls (C-E4, C-E4K1) have
  been run and reproduce the preserved E3 T-E3 and T-E3K1 corpora cell for
  cell, and the tooling is qualified on control data only. Pre-treatment
  finding P-1 (a no-effect treatment would satisfy both the "H0" and the
  "¬H1 ∧ H3" interpretation rows) was then closed, still blind to
  treatment, by an interpretation-only amendment: pre-registration v2 and
  analysis freeze `v6-e4-freeze-v2-68d262a0dbd1`, which pins freeze v1
  unchanged. A second blind amendment (pre-registration v3, analysis freeze
  `v6-e4-freeze-v3-80f21d822542`) gives "H2" precedence over the standalone
  "¬H1 ∧ H3" interpretation. Both treatments then ran under freeze v3,
  and every hard-stop gate passed. Registered verdicts: H1, H3 and H4
  supported; H0, H5, H6 and H8 refuted; H2 and H7 neither (2 of 18
  multi-pass matchups follow the final chunk, one above the ≤ 1/10
  refutation threshold); D9′ holds. No pre-registered interpretation row
  applies. Descriptively, mirrored pass order largely neutralized
  multi-pass response-order concentration while leaving opening-pass
  anchor/core-0 contests largely unchanged. Both Rulesets remain
  research-only
  ([`docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_RESULTS.md`](research/v6/V6_E4_MIRRORED_PASS_ORDER_RESULTS.md),
  [`docs/research/v6/V6_E4_EXPERIMENT_FREEZE.md`](research/v6/V6_E4_EXPERIMENT_FREEZE.md),
  [`docs/research/v6/V6_E4_ANALYSIS_FREEZE_V2.md`](research/v6/V6_E4_ANALYSIS_FREEZE_V2.md),
  [`docs/research/v6/V6_E4_ANALYSIS_FREEZE_V3.md`](research/v6/V6_E4_ANALYSIS_FREEZE_V3.md),
  [`docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md),
  [`docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md`](research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md)).

---

## Other future items

**Status: mixed — see each item.**

- **Redcode / pMARS execution — Status: Retired (V6 Phase 2B.6).**
  Bytefray is now exclusively a Python programmable-agent platform. Execution
  of Redcode warriors and external pMARS invocation were retired from the CLI,
  runtime, and installer in Phase 2B.6 (see
  [`docs/research/v6/V6_PHASE2B6_REDCODE_PMARS_RETIREMENT.md`](research/v6/V6_PHASE2B6_REDCODE_PMARS_RETIREMENT.md)).
  Historical `redcode94` match results remain readable in Replay History.
  Releases up to and including v5.0.0 remain available for historical Redcode
  functionality.
- **Agent Designer & Desktop Experience — Status: Substantially Delivered.**
  The desktop workflow was completed across v1.3, v3.0, and v5.0 (Replay
  History browser, end-to-end Tournament UX, Agent Parameterization, and
  Result-Backed Replay Integrity). Minor usability refinements remain open as
  routine candidates.
- **Richer GUI access to evaluation / history / provenance — Status: Shipped.**
  Evaluation History browser (v1.1), comparison drill-down (v1.3), visual
  analytics (v3.0), and Replay History (v5.0) are fully shipped.
- **Additional starter / reference agents — Status: Ongoing Candidate.**
  V4 bundled multi-process starters and `v4_quorum`; V5 added `v5_dual_team`.
  Phase 2B.12 will align all default starters with Agent API v2.
- **Agent ecosystem & sharing — Status: Unscheduled Candidate.**
  See "Agent packaging / sharing" above.
- **Future rules experimentation — Status: Postponed.**
  See "Ruleset Status and Evolution Map" above.

---

Long-range ideas are retained here where still valid, and updated or retired
when empirical evidence or shipped milestones have superseded them. For the
active development sequence and immediate next steps, see [ROADMAP.md](ROADMAP.md).
