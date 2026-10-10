# Bytefray V6 E3 — Slot-Limited Disruption: Registration

**Status:** Research Rulesets implemented and qualified. **No E3 experiment matrix has been run**, and nothing here is a gameplay result.
**Branch:** `v6-research`
**Semantic authority:** `V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md` is designated as the authority for E3, but **it is not in the repository**. It was not supplied to the implementation phase, and it could not be found in the working tree, the git history, any remote branch or the published artifacts. It has therefore not been preserved, and its §F–§Q could not be read. The operative specification for this phase was the phase's implementation prompt. That prompt restates the review's semantics (§§4–22): the policy field, the per-offer suppression rule, the G.3 sequences, the G.4 bound and the G.5 immunity theorem. This record describes what was built against that restatement. Before E3 research tooling begins, the review must be committed verbatim and checked against this record; see "Open item" below.

> **Update, 2026-09-23:** the design review has since been preserved verbatim at [`V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md`](V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md) (`bfcf7e5`) and reconciled against this record, with no conflicts. See [the dated addendum](#addendum-2026-09-23-design-review-preserved-and-reconciled) at the end. The text above and below is unchanged.

## The question E3 asks

Under whole-tick disruption, one successful write to the address where an entrant's processes are anchored makes all of them ineligible, and blind, for the rest of the tick. E2 showed the consequence ([results](V6_E2_CAPTURE_HOLD_RESULTS.md)). With the co-located single-write disruption of its §D.5 conditions, each tick goes to whoever moves first: the E2 treatment turned the forced capture into delay and stalemates phase-locked to the scheduler's first-mover rotation.

E3 changes exactly one link of that chain: **how long** a disruptive hit suppresses its victim. Trigger and scope are unchanged. The question is whether bounding disruption to the victim's next action offer removes whole-tick denial, and so the first-mover-takes-all tick, without adding any new mechanic. This phase implements and qualifies the Rulesets only. It draws no gameplay conclusion.

## Identities and policy

| Item | Primary treatment | Companion treatment |
|---|---|---|
| Ruleset ID | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` | `bytefray-rules-6-research-disruption-slot1` |
| Constant | `rules.BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID` | `rules.BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID` |
| Policy object | `RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1` | `RULESET_V6_RESEARCH_DISRUPTION_SLOT1` |
| Parent | `bytefray-rules-6-research-capture-hold-k2` (E2, K = 2) | `bytefray-rules-6-research-scale` (K = 1) |
| Only gameplay difference | `disruption_slot_limit`: `None` → `1` | `disruption_slot_limit`: `None` → `1` |
| Lifecycle | `ACTIVE_RESEARCH_RULESET_IDS` | `ACTIVE_RESEARCH_RULESET_IDS` |

Both policy objects are independent literals with every field spelled out, never `dataclasses.replace` of their parents. Tests verify the one-field difference: the only fields that differ from the parent are `ruleset_id` and `disruption_slot_limit`. Between the two treatments, the only differences are `ruleset_id` and `capture_hold_ticks`.

`RulesetPolicy.disruption_slot_limit: int | None = None` is a new policy field. Every other registered Ruleset keeps the default `None`. It accepts `None` or an `int >= 1`, and it rejects `0`, negative values, `True`/`False`, floats and strings with `ValueError`, in the same strict style as `capture_hold_ticks`. There is no `MatchRequest` override. The existing one-tick disruption window, `ProcessMatchController.disruption_duration = 1`, is unchanged.

**Permanent obligation.** Artifacts carry only the Ruleset ID. Once E3 artifacts exist, neither policy's field values may change, and retiring either identity must keep it resolvable.

## Runtime semantics as implemented

All of it is in `process_runtime.py`, gated on the policy field, never on a Ruleset ID.

- **State.** Each process keeps `disrupted_until_tick` and adds a runtime-only `disruption_slots_left: int = 0`, reset by `ProcessInstance.reset`. It is never serialized.
- **Hit.** Trigger and scope are unchanged. A successful enemy `WRITE` to an address disrupts **every** live enemy process anchored there. `disrupted_until_tick = tick + 1` as before. When the limit is an integer, the runtime also sets `disruption_slots_left = limit`. It assigns the value and never adds to it, so two hits before the victim's next offer still cost one offer.
- **Predicate.** `ProcessMatchController._is_suppressed(process, tick)` is `tick < disrupted_until_tick and (limit is None or disruption_slots_left > 0)`. Under `None` it is exactly `is_disrupted`. It replaces `is_disrupted` in the two places that decide what a disrupted process cannot do:
  - process eligibility in `_effective_process_quotas`;
  - the sensing observers in `_visible_enemy_anchors`.
- **Consumption.** When the limit is an integer, each entrant offer is wrapped, and the wrapper works in three steps:
  1. It takes the set of that entrant's processes that are suppressed at offer entry.
  2. It runs the unchanged `execute_entrant_slot`: eligibility, quota redistribution, round-robin selection, the cursor, execution, and forfeiting the offer when nothing is eligible.
  3. In a `finally`, it decrements the counter of every process in the entry set.

  A hit made during an offer lands on another entrant's processes, so it is never charged to that offer.
- **Whole-tick path.** When the limit is `None`, the scheduler receives the historical `execute_entrant_slot` callback itself, not the wrapper.
- **Tick boundary.** Suppression never crosses a tick. A counter left positive by a hit after the victim's final offer is never read, because `is_disrupted` is false in the next tick. The next hit reassigns it.
- **Unchanged.** `scheduler.py`, chunk size, rotation, first-mover calculation and pass structure are untouched.

At λ = 1, a process hit before its entrant's next offer sits out that one offer and is eligible again from the following offer of the same tick. The offer is forfeited only if every one of the entrant's processes is suppressed, and it still counts as one of the entrant's Q offers. Sibling processes at other anchors keep acting with today's redistributed quota. A suppressed process is passed over without consuming its round-robin turn. It cannot act as a sensor while suppressed, and sensing returns once its suppression expires within the tick.

## Artifacts

There is no replay, result or client schema change. There are no suppression counters, offer events or action-denial metrics in any artifact.

- The replay's per-process `disrupted` flag keeps its permanent meaning, "hit during this tick" (`is_disrupted`), under every Ruleset. Under E3 a process can be flagged `disrupted` and still have acted later in the same tick. The event vocabulary is unchanged.
- The per-process result statistics (`disruption_hits_received`, `disrupted_ticks`, `distinct_disrupted_ticks`) keep their hit-based meaning.
- A future E3 analyzer is expected to derive executed actions from the existing per-tick `cpu_used`. `spectator_derivation` reconstructs disruption from the anchor-hit rule and checks it against the replay flag, and it takes detection from each decision's own observation, so it remains consistent.

## Evaluation methodology

Both treatments inherit the research-scale methodology unchanged:

- seeded placement with the paired orientation swap;
- identity and schema version 7;
- arena range `[64, 65536]`;
- an omitted `--arena-size` resolves to **512**, never `Config().arena_size` (4096);
- the core-overlap guard applies.

Each has its own arena-alignment label:

- `ruleset_v6_research_capture_hold_k2_disruption_slot1_seeded_placements`;
- `ruleset_v6_research_disruption_slot1_seeded_placements`.

The single-member predicates are `is_ruleset_v6_research_capture_hold_disruption_slot_methodology` and `is_ruleset_v6_research_disruption_slot_methodology`. Their resolver flags are **keyword-only**, as E2's is. The deferred methodology-registry refactor was not undertaken.

## Exposure

- **In:**
  - `PROCESS_RULESET_IDS`;
  - `_RULESET_POLICIES`;
  - `ACTIVE_RESEARCH_RULESET_IDS`;
  - `match_service._CORE_PLACEMENT_GUARDED_RULESET_IDS`;
  - the evaluation allow-list;
  - the `agents evaluate --ruleset` choices.
- **Out:**
  - `PUBLIC_STABLE_RULESET_IDS` and `OMITTED_RULESET_CANDIDATES`;
  - the `--ruleset` choices of `run`, `agents test` and tournament;
  - every Designer Ruleset option tuple.

  An omitted Ruleset still resolves to `bytefray-rules-4`.

## Evidence (tests)

| Requirement | Coverage |
|---|---|
| Parent freeze before any runtime change | `test_v6_e3_parent_byte_identity.py`, committed at `dd7b7b0` against the unmodified runtime at `9d34b01`. It holds 90 matches: the E2 parent, the K = 1 parent and stable V4, each over sniper vs disrupt guard, repair guard vs sniper, spread sniper vs disrupt guard, the probe mirror and the guarded-painter mirror, in both orientations, seeds 1–3, arena 512, 1000 ticks, using the tracked E2 fixtures. It pins the replay SHA-256, `result_id`, `match_id`, winner, ticks, reason, score, executed actions and whole-tick-silenced ticks. All 90 reproduce byte for byte after the change. The existing V4 freezes (`test_v4_k1_capture_byte_identity.py`, `test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`) are unedited and pass. |
| Policy, one-field differences, registration, lifecycle, product isolation, evaluation plumbing, determinism, schema shape | `test_ruleset_v6_research_disruption_slot.py` |
| G.3 per-offer semantics | `test_e3_slot_limited_disruption_semantics.py`. Scripted entrants run on `ProcessMatchController`, and the whole per-offer sequence is asserted by value: which offers were forfeited, which process took each executed offer, and what it saw. |
| G.4 action bound | The same module, by exhaustive enumeration. Every jam over the victim's anchors is tried for a single-process, co-located and spread victim, in both scheduler positions. Under λ = 1 the minimum is exactly **5** actions as first mover and **4** as second mover, and 0 never occurs. The whole-tick parent still reaches the historical 2 and 0. |
| G.5 K = 2 immunity | The same module. A repair guard and a disrupt-first guard, in both seats, face an omniscient jammer, a chunk jammer and 20 seeded random jammers for 24 ticks. Neither guard is ever at zero core at two consecutive evaluations. On every second-mover tick, the guard takes the tick's final offer with an own-core repair. Under the whole-tick parent, the same adversaries capture the repair guard. |
| Mechanic characterizations | The same module: tracked E2 fixtures at seed 42, asserted from the canonical replay. They pin mechanics, not balance outcomes. |
| Mutation checks | Eleven deliberate breakages were each applied to the committed code, run against the three E3 test modules, and restored with `git checkout`, with the tree verified clean after each. None was committed. Every one is detected; the number of failing tests is in brackets. <ul><li>Counters never decrement (53).</li><li>Hits stack (14).</li><li>Global instead of victim-offer decrement (35).</li><li>Newly hit processes charged for the hitting offer (46).</li><li>`None` using finite semantics (111, including all 90 parent-freeze matches).</li><li>Only one co-located process suppressed (4).</li><li>Sensing using `is_disrupted` (6).</li><li>The replay flag reporting suppression (6).</li><li>A forfeited offer not consuming suppression, which breaks the G.4 bound (47).</li><li>The companion (14) or the primary (2) differing from its parent in a second field.</li></ul> |

## Open item

The E3 design review must be committed verbatim at `docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md` and reconciled with this record before E3 research tooling begins. Any difference between the review's §F–§Q and the semantics above is to be resolved in favour of the review, by a separate, reviewed change.

## Not done here (next phase)

- the E3 jam fixture and its twin;
- the parity/action analyzer;
- freezing the hypotheses and the pre-registration;
- the E3 matrix (F1/F2/F2-P/F4);
- the parent reproduction gates;
- freeze qualification;
- separate authorization to run the treatment.

No E3 gameplay conclusion may be drawn from this implementation phase.

## Addendum, 2026-09-23: design review preserved and reconciled

**Chronology exception.** The Opus design review predates this implementation conceptually: it was written against baseline `9d34b01`, before any E3 code existed. It was not available to the implementing session as a repository file, so the implementation (`dd7b7b0`, `75ed578`, `a3ab15a`, `3fb9d41`) proceeded from the semantic handoff supplied in the implementation prompt. The review was subsequently preserved verbatim at `bfcf7e5`, after those commits (SHA-256 `c0d0f711942a2d73b0e4d02fe5b4b1e85334142a9560515c3c6c2b221d1a6b18`). The git history was left exactly as it happened: nothing was reordered, amended or rewritten, and the review itself was not edited. This addendum closes the "Open item" above.

**Post-preservation reconciliation.** The committed implementation and tests were then reconciled directly against the review's §F–§Q.

- **Conflicts: none.**
- **Matches.**
  - **§F.** Both arms: primary on the E2 parent, companion on research-scale.
  - **§G.1–G.3 transition.** Per-process `disruption_slots_left`. A hit assigns the count and never accumulates it. The count is consumed by offers to the victim's own entrant. The suppressed set is fixed at offer entry, and a `finally` decrements it. Scope is every enemy process at the written anchor. Quota, selection, cursor and forfeit are unchanged. Sensing uses the new predicate, and the replay flag keeps `is_disrupted`.
  - **§G.4 bound and §G.5 immunity.** Both are tested and hold.
  - **§H.** Field, validation, default, IDs, literal objects, lifecycle, the absence of an override, and unchanged artifacts.
  - **§N step 1.** The freeze was committed before any runtime change.
  - **§O-9 and §O-14.** Semantics are set only through the policy, and `disruption_duration` is untouched.
  - **§Q.1–Q.6.**
- **§I mechanical predictions reproduced exactly.** The review's named probe scenarios were rerun on the committed code with the tracked fixtures; no grid was run.
  - **Sniper vs disrupt guard:** the review's λ = 1 write sequences for ticks 1 and 2, 7/7 executed actions, and B ending ticks 1 and 2 at 7/8 and then 3/8.
  - **Repair guard vs sniper:** 125 zero-core ticks, all on its own first-mover ticks and never consecutive, and a tie at 1000.
  - **Spread sniper vs disrupt guard:** one lost offer per tick, and a core that settles at 4 of 8.
  - **Probe mirror:** mutual completion at tick 3.
  - **Guarded-painter mirror:** captures at 48 A, 72 A, 159 A, 58 B and 93 B for seeds 1–4 and 42.
  - **Painter vs sniper:** the painter wins at 93 with no zero-core ticks.
  - **Min guard vs sniper, and sniper vs greedy painter:** unchanged, as predicted.
  - **One observation on the parent side.** The review gives "77" zero-core ticks for the painter under E2, while the unchanged parent path gives 77 and 78, depending on the painter's seat. This concerns the review's summary, not the implementation.
- **Intentional deviations.** None of them is semantic.
  1. §Q.3 places the snapshot and the `try/finally` "at the start of `execute_entrant_slot`". The implementation puts them in a wrapper around the unchanged `execute_entrant_slot`. It also hands the scheduler the unwrapped callback when λ is `None`, since the review's decrement is itself conditional on λ not being `None`. The snapshot instant is the same and every exit path is covered.
  2. The §N step 1 freeze adds the K = 1 parent and stable V4 to the review's E2 set: 90 matches in all.
  3. §Q.5 asks for the V4 and E2 λ = `None` goldens to be unedited, and they are. One E2 registry-inventory assertion, which is not a golden, was extended because the primary treatment inherits K = 2.
  4. §G.5 is tested with scripted repair and disrupt-first guards against adversarial jammers. The fixture-level form (`e2_repair_guard`, `e2_disrupt_guard`) is the review's D9 stop check, a tooling-phase gate.
- **Deferred to the tooling phase, as the review assigns (§J–§N, §Q "separate follow-up task").**
  - `e3_jam_sniper` and its twin;
  - the action/parity analyzer: PM-1 to PM-4, MC-1 and MC-2, the action denial fraction, and the "no zero-core ticks" category;
  - the D0–D9 pre-registration;
  - the F1/F2/F2-P/F4 matrix;
  - the matrix and analysis freeze identities;
  - controls and the parent reproduction gate;
  - hard stops 2–11;
  - separately authorized treatment execution.

No E3 experimental matrix has been run.
