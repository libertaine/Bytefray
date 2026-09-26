# Bytefray V6 E5 — Anchor/Core-0 Separation: Registration

**Status:** Research Rulesets implemented and qualified. **No E5 experiment matrix has been run**, and nothing here is a gameplay result.
**Branch:** `v6-research`
**Semantic authority:**

- [`V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md`](V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md) (SHA-256 `63d79246c4cf3e3787c10e3862cbc8fb8fefbe51517f65aa23dea066a46ac17d`), verdict REDESIGN;
- [`V6_E5_DESIGN_REVIEW_REVISION_1.md`](V6_E5_DESIGN_REVIEW_REVISION_1.md) (SHA-256 `35b9022f242207c5bd8514b5c066c1c1a86a1e8dfca7dfc0f63a438dd2451998`), the corrected design.

Both were preserved verbatim at `4fbd1d4`, **before** any E5 freeze, placement, policy or Ruleset change. The research lead's resolution of Revision 1's open choices is recorded [below](#decisions-recorded-before-implementation).

## The question E5 asks

E4 left the OPENING-ONLY contests' second-mover privilege in place under mirrored later-pass order ([E4 results](V6_E4_MIRRORED_PASS_ORDER_RESULTS.md) §F.3). Every Agent API v2 process spawns on its entrant's core cell 0, so a WRITE to a never-moved enemy anchor both disrupts the process and flips a core cell. The design review asked whether that dual-purpose write is what carries the privilege.

E5 therefore varies one thing: **where a process with no declared position spawns**. The research question is:

> **Is anchor/core-0 co-location necessary for the second mover's directed base privilege, where the base is also attacked explicitly (sweep-backed contests)?**

That is a question, not a promised outcome. The registered readings include co-location being load-bearing (E5-H1), not necessary (E5-H2), qualified versions of each, and "no registered interpretation row applies". This phase implements the Rulesets. It does not claim that separation improves gameplay, and it draws no E5 conclusion.

## Identities and policy

| Item | Primary treatment | Companion treatment |
|---|---|---|
| Ruleset ID | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-anchor-before-core` | `bytefray-rules-6-research-disruption-slot1-anchor-before-core` |
| Constant | `rules.BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID` | `rules.BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID` |
| Policy object | `RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE` | `RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE` |
| Parent | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` (historical T-E3 = C-E4; K = 2, λ = 1) | `bytefray-rules-6-research-disruption-slot1` (historical T-E3K1 = C-E4K1; K = 1, λ = 1) |
| Only gameplay difference | `initial_anchor_placement`: `"core_base"` → `"before_core"` | the same |
| Lifecycle | `ACTIVE_RESEARCH_RULESET_IDS` | `ACTIVE_RESEARCH_RULESET_IDS` |

**Independent literals.** Both policy objects are independent literals with every field spelled out, never `dataclasses.replace` of their parents.

- Tests verify the one-field difference: the only fields that differ from each parent are `ruleset_id` and `initial_anchor_placement`.
- Both keep forward pass order. E5 is single-factor, not a factorial with E4 (review §G).

**The policy field.** `RulesetPolicy.initial_anchor_placement: str = "core_base"`, with `INITIAL_ANCHOR_PLACEMENT_MODES = {"core_base", "before_core"}`.

- **Closed set.** The set is closed on purpose: only the −1 offset keeps the research fixtures' anchor-derived enemy-core targeting behaviorally inert (review §F, P5), so no general integer offset can be expressed (decision R1-1).
- **Validation.** Any other value, including non-strings, other spellings and other cases, raises `ValueError`. Nothing is coerced.
- **Everywhere else.** Every other registered Ruleset keeps `"core_base"`. There is no `MatchRequest` override.

**Permanent obligation.** Artifacts carry only the Ruleset ID, and the spawn rule is recovered from it through `_RULESET_POLICIES`. Once E5 artifacts exist, neither policy's field values may change, and retiring either identity must keep it resolvable.

## Spawn semantics as implemented

`RulesetPolicy.resolve_initial_anchor(core_base, arena_size)` returns `core_base` under `"core_base"`, and `(core_base - 1) % arena_size` under `"before_core"`. `ProcessMatchController.__init__` calls it in exactly one place, the branch that places a process with no declared position.

- **Explicit positions are kept.** A process given an `initial_position` keeps it.
- **The core is untouched.** `core_base`, the core cells, their tick-0 seeding and the recorded `pc`/`region` are identical under both values (P1). The capture analyzer rebuilds cores from `pc`, so it is unaffected.
- **A spawn rule, not a spatial rule** (Revision 1 §R3). Movement is unrestricted. A process may MOVE onto its own core afterwards; an enemy WRITE there then both disrupts it and flips the core cell, exactly as under `"core_base"`. A test proves that this remains legal.

**Ruleset invariants and corpus characterizations are kept apart:**

- **Ruleset invariants** (Revision 1 D-1, D-2): every default spawn lies off its own core, and no hostile write to a still-unmoved default anchor is also a core write.
- **E5-corpus characterizations** (D-3, D-4): for the seven research fixtures, which never move onto their own core, no hostile write is both an anchor hit and a same-victim core write (DUAL = 0), and no process ever sits on its own core. These are facts about the fixtures, not rules of the Ruleset.

**Spawn-validity guard.** `match_service.DefaultSpawnInCoreError` (code `ruleset_default_spawn_in_core`) rejects a layout before any entrant executes or any artifact exists.

- **What it rejects.** A layout whose off-core default spawn would land inside *another* entrant's core, which happens only when the two cores are adjacent. Seeded placement at A = 512 (minimum separation 64) never produces that layout.
- **Scope.** It returns at once for every `"core_base"` Ruleset, so no existing identity changes, and it constrains nothing after spawn.

## Qualification of the Rulesets

| Check | Result |
|---|---|
| E5-parent byte-identity freeze, committed at `8f6717d` before any engine change | 96 matches: both parents × 8 E5-field pairings × both orientations × seeds 1–3. All 96 rows also equal the preserved C-E4 / C-E4K1 corpus cells (replay SHA-256, `result_id`, `match_id`). After the change, **98 passed** byte for byte. |
| V4, E3-parent and E4-parent freezes, E3/E4 semantics, V4 exploit characterization | 483 passed after the change |
| New tests (`e14d215`) | 84 registration/plumbing tests and 44 spawn-semantics tests, all passing |
| Mutation check | With the resolver forced back to co-location, all 36 E5-parametrized semantics tests fail. The 8 parent-Ruleset cases are untouched. |
| Full suite at `e0a1b02` + tests | 4448 passed, 18 skipped, 3 deselected; `mypy engine/src/battle_engine`, `mypy client/src/battle_client` and `ruff check .` clean |

## Decisions recorded before implementation

The research lead approved the corrected design and resolved Revision 1's open choices before any E5 code existed:

| Item | Decision |
|---|---|
| R1-1 | Accept d = −1 only: `"before_core"` means exactly `(core_base - 1) % arena_size`. |
| R1-2 | Exclude `v4_probe`, `e3_jam_sniper`, `e2_greedy_painter` and `e2_counter`. The analyzed field is the seven fixtures. |
| R1-3 | BP is the primary instrument, calculated per seed from both-alive ticks and aggregated as the median across seeds; raw ticks are never pooled across seeds. |
| R1-4 | Keep the K = 1 companion. |
| R1-5 | The offset-aware fixture copies are test-only gate instruments proving P5. They never enter the matrix, populations, analysis or reported results. |
| O-1 | **Accepted.** One inferential unit per twin mirror: the two victims' per-seed BP values are averaged before the seed median, and both directed victim values are kept descriptively. |
| O-2 | **Accepted.** WEAKENED counts in E5-H1's numerator. |
| O-3 | **Accepted.** P-BASE selects control BP ≥ 1/3, the band edge. |
| O-4 | **Modified.** At least **6** SWEEP-BACKED inferential units are required. With fewer, halt before treatment and reassess the design. |
| O-5 | **Accepted.** MIXED-INFERENCE units are frozen, reported and excluded from E5-H1 and E5-H2. |

**Further requirements**, set with those decisions and in force for the tooling phase:

- The BP transition function and the interpretation table are frozen together.
- Tests must prove, before treatment, that:
  - every control/treatment band pair maps to exactly one transition class;
  - every (E5-D, E5-H1, E5-H2) status combination maps to exactly one interpretation outcome, including "none";
  - simultaneous H1/H2 SUPPORTED is an invariant violation, never resolved by precedence;
  - NEITHER is never read as REFUTED.
- The interpretation rows are the four explicit rows of Revision 1 §R6 (R-H2, R-H2′, R-H1, R-H1′), with no row written in terms of a negated hypothesis.

## Not in this phase

- The E5 research tooling, the pre-registration, the matrix and analysis freezes, the control reproduction, and the non-matrix manipulation gates. These follow as separately committed steps.
- Any treatment execution. No T-E5 or T-E5K1 matrix cell may be created until the research lead authorizes it at the blind checkpoint.
