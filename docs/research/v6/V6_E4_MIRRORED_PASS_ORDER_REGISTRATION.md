# Bytefray V6 E4 — Mirrored Pass Order: Registration

**Status:** Research Rulesets implemented and qualified. **No E4 experiment matrix has been run**, and nothing here is a gameplay result.
**Branch:** `v6-research`
**Semantic authority:** [`V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md), preserved verbatim at `b4d6024` (SHA-256 `5d9290c0cf5ebbd85d80956e504f9cd3f1f7e1e1ef9a811dae7e2fec87990cc0`) **before** any E4 freeze, scheduler, policy or Ruleset change. This phase implements the review's §U handoff; the research tooling in its §R steps 4–9 is a later, separately authorized phase.

## The question E4 asks

E3 removed whole-tick first-mover exclusivity but left a moderate, last-mover-leaning order dependence ([E3 results](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md)). The E4 design review found that "last-action position" and "end-of-tick evaluation" cannot be separated by any scheduler-only or evaluation-only treatment (§E.1, §G). It reframes the residual in terms of which entrant responds last within each pass, and where in the pass structure a contest sits (§D, §E.2–E.3).

E4 therefore varies one thing: **the pass-level response order within the tick**. The stock order makes the tick's second mover the later responder in all four passes. The mirrored order makes it the later responder in the first two passes and the first mover in the last two. The research question is:

> **Does balancing pass-level response order neutralize the multi-pass residual while leaving opening-pass anchor contests unchanged?**

That is a question, not a promised outcome. A null result, or a result in which the privilege follows the final chunk instead, is equally reachable (review §N). This phase implements and qualifies the Rulesets only. It does not claim that mirrored passes improve gameplay, and it draws no E4 conclusion.

## Identities and policy

| Item | Primary treatment | Companion treatment |
|---|---|---|
| Ruleset ID | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes` | `bytefray-rules-6-research-disruption-slot1-mirrored-passes` |
| Constant | `rules.BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID` | `rules.BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID` |
| Policy object | `RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES` | `RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES` |
| Parent | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` (historical T-E3; K = 2, λ = 1) | `bytefray-rules-6-research-disruption-slot1` (historical T-E3K1; K = 1, λ = 1) |
| Only gameplay difference | `scheduler_pass_order`: `"forward"` → `"mirrored"` | `scheduler_pass_order`: `"forward"` → `"mirrored"` |
| Lifecycle | `ACTIVE_RESEARCH_RULESET_IDS` | `ACTIVE_RESEARCH_RULESET_IDS` |

Both policy objects are independent literals with every field spelled out, never `dataclasses.replace` of their parents. Tests verify the one-field difference: the only fields that differ from each parent are `ruleset_id` and `scheduler_pass_order`. Between the two treatments, the only differences are `ruleset_id` and the inherited `capture_hold_ticks` (2 and 1).

**The policy field.** `RulesetPolicy.scheduler_pass_order: str = "forward"`, with `RulesetPolicy.SCHEDULER_PASS_ORDER_MODES = {"forward", "mirrored"}`, in the codebase's string-mode style (`core_placement`, `process_selection`). Validation in `__post_init__`:

- `"forward"` is accepted for every scheduler mode;
- `"mirrored"` is accepted only when `scheduler_mode == "chunked"`: a single-pass scheduler has no second half, so the policy would misstate itself;
- any other value, including non-strings, `None`, other spellings and other cases, raises `ValueError`. Nothing is coerced.

Every other registered Ruleset keeps `"forward"`. There is no `MatchRequest` override, and no runtime state.

**Permanent obligation.** Artifacts carry only the Ruleset ID, and the pass order is recovered from it through `_RULESET_POLICIES`. Once E4 artifacts exist, neither policy's field values may change, and retiring either identity must keep it resolvable.

## Scheduler semantics as implemented

All of it is in `scheduler.run_chunked_quota`, behind a keyword-only `mirror_second_half: bool = False`:

```python
order = rotate(states, (tick - 1) mod n)        # unchanged
P     = ceil(Q / chunk)                          # unchanged
for p in 0 .. P-1:
    pass_order = reversed(order) if (mirror_second_half and 2p >= P) else order
    for state in pass_order:                     # liveness checks unchanged
        for slot in p*chunk .. min((p+1)*chunk, Q) - 1:
            execute_slot(state, slot)
```

`RulesetPolicy.run_scheduler` passes `mirror_second_half=(self.scheduler_pass_order == "mirrored")`. It reads the policy field and nothing else: there is no Ruleset-ID branch. `run_sequential_quota` and `run_interleaved_quota` are untouched.

For the E4 configuration (two entrants, Q = 8, chunk 2, rotation on) each tick's offers are:

| Order | Tick 1 (Seat A first) | Chunk owners |
|---|---|---|
| Forward (parent) | `A0 A1 B0 B1 A2 A3 B2 B3 A4 A5 B4 B5 A6 A7 B6 B7` | `F L F L F L F L` |
| Mirrored (treatment) | `A0 A1 B0 B1 A2 A3 B2 B3 B4 B5 A4 A5 B6 B7 A6 A7` | `F L F L \| L F L F` |

- **P1 Opportunity.** Each live entrant still receives exactly 8 offers, its own slots `0..7` in order, one chunk per pass.
- **P2 Rotation.** The first mover is still seat `(tick − 1) mod 2`. Rotation stays on; E4 introduces no fixed-seat scheduler.
- **P3 Final chunk.** The first mover owns the tick's final chunk under the mirrored order; the second mover owns it under the forward order.
- **P4 Response balance.** The entrant acting second in each pass is `(L, L, F, F)` under the mirrored order, against `(L, L, L, L)`.
- **P5 Stream equivalence.** The mirrored global action stream is the stock stream shifted by exactly four chunks, with the same total actions, per-entrant quota, run structure (one 4-action run per tick) and alternation count (7 per tick). This characterizes the manipulation; it is not a claim of gameplay equivalence, because the tick boundary, and with it the evaluation instant and every tick-scoped rule, moves with the shift.
- **P6 / G.4′.** Under λ = 1, an entrant alive throughout a tick executes at least **5** actions in **both** roles, and the bound is tight; the stock order gives (5, 4).
- **P7 / G.5′.** Under K = 2, an entrant whose final executed action on each of its first-mover ticks repairs its own core is never at zero core at two consecutive evaluations.
- **P8 Default identity.** `"forward"` sets `mirror_second_half=False`: every existing Ruleset schedules exactly as before.

Everything outside the scheduler is unchanged: `process_runtime.py` and `python_runtime.py` are not modified, so capture evaluation (once, at the end of the tick), `capture_hold_ticks`, `disruption_slot_limit`, `disruption_duration`, `_select_active_process`, quota redistribution, sensing, process round-robin and scoring are exactly as in E3. There is no new capture checkpoint and no scheduler-order replay event.

## Compatibility

- **Forward-path byte identity.** Before any scheduler change, `test_v6_e4_parent_byte_identity.py` (`b144e1d`) froze the review's §R step-2 corpus against the unmodified scheduler at `e52b5aa`: both E4 parents × 8 pairings (sniper v disrupt guard, repair guard v sniper, spread sniper v disrupt guard, sniper v min guard, the probe, guarded-painter and disrupt-guard mirrors, jam sniper v min guard) × both orientations × seeds 1–3, arena 512, 1000 ticks: **96 matches**. Each row pins winner, ticks, reason, score, per-seat actions and silenced ticks, kill/death events, digests of the per-tick `cpu_used` sequence and of the in-tick ordered write stream, and replay SHA-256, `result_id` and `match_id`. All 96 rows also equal the preserved historical T-E3/T-E3K1 corpus cells (`v6-e3-matrix-v1-634132ec3c15`) in replay SHA-256, `result_id` and `match_id`. All 96 reproduce byte for byte after the change, as do the unedited V4, E2 and E3-parent freezes (`test_v4_k1_capture_byte_identity.py`, `test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`, `test_v6_e3_parent_byte_identity.py`).
- **Artifacts.** No replay, result or client schema change; no new key anywhere. `scheduler_pass_order` is never serialized. The canonical `match_id` payload is unchanged, including the research scheduler-override block, which keeps exactly its historical `mode`/`chunk_size`/`rotate_start` keys; `_effective_ruleset_policy`'s `replace()` carries the pass order through generically.
- **Identity.** The new Ruleset IDs give distinct `match_id`s, and distinct `result_id`s wherever the order changes play; the same E4 request reproduces byte-identical replay and result identity. The scheduler introduces no randomness.

## Evaluation methodology

Both treatments inherit the research-scale methodology unchanged, as E2 and E3 do:

- seeded placement with the paired orientation swap;
- identity and schema version 7;
- arena range `[64, 65536]`;
- an omitted `--arena-size` resolves to **512**, never `Config().arena_size` (4096) (review §K trap F-4);
- the core-overlap guard applies.

Each has its own arena-alignment label:

- `ruleset_v6_research_capture_hold_k2_disruption_slot1_mirrored_passes_seeded_placements`;
- `ruleset_v6_research_disruption_slot1_mirrored_passes_seeded_placements`.

The single-member predicates are `is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology` and `is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology`; they do not widen the E3 predicates. Their resolver flags are **keyword-only**. The deferred methodology-registry refactor was not undertaken.

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
| Parent freeze before any scheduler change | `test_v6_e4_parent_byte_identity.py`; see Compatibility. |
| Policy, one-field differences, registration, lifecycle, product isolation, evaluation plumbing, identity, determinism, schema shape | `test_ruleset_v6_research_mirrored_passes.py`. |
| Exact scheduler sequences | `test_e4_mirrored_pass_order_semantics.py` drives `run_chunked_quota` directly and asserts every offered (entrant, slot) sequence by value: rotation on (ticks 1–4) and off; one, two and three entrants; chunk 1, 2, 3 and ≥ Q; a partial final chunk; dead entrants; entrants forfeiting mid-chunk. The forward path is compared with a verbatim copy of the pre-E4 function over a 3,600-configuration grid, and the mirrored path is checked to reorder only the later passes. |
| P1–P5 | The same module, through each Ruleset's own `run_scheduler`, and the runtime order `FFLLFFLLLLFFLLFF` through a directly constructed `ProcessMatchController`. |
| Everything outside the scheduler unchanged | The same module: the one-tick disruption window; a hit still costs the victim's *next own* offer (which the mirrored order can place later in the tick); a late hit does not carry into the next tick; process round-robin and quota redistribution. |
| G.4′ | The same module, by exhaustive enumeration of every jam over the victim's anchors, for a single-process, co-located and spread victim in both scheduler positions, under both treatments: minimum **(5, 5)**, attained, and never 0; the stock parents give **(5, 4)** on the same jams. The full jam is also checked offer by offer. |
| G.5′ / D9′ | The same module. Under K = 2 and the mirrored order, a repair guard and a disrupt-first guard, in both seats, face an omniscient re-disrupting jammer, an omniscient eraser, a chunk jammer and 20 seeded random jammers for 24 ticks. Neither is captured, neither accumulates two consecutive zero-core evaluations, and on every first-mover tick the guard takes the tick's final offer with an own-core repair. A guard that satisfies *only* the premise is at zero after every second-mover tick and is never captured; the forward parent captures the same guard at tick 2, and the K = 1 companion at its first zero. The real-fixture D9′ gate is deferred to the tooling phase. |
| Mechanic characterizations | The same module: tracked fixtures at seed 42 (outside matrix seeds 1–32) under historical T-E3 and the primary treatment, from the canonical replay alone. They pin the review's §L traces, never a rate or a balance outcome: sniper v disrupt guard (the guard's end-of-tick core settles at 5 from tick 1, one initial swing, against 7, 3, 7, 3 and 999 swings); sniper v repair guard (125 zero-core ticks on the guard's own first-mover ticks become 0; under K = 1 a tick-8 capture becomes a 1000-tick tie); the guarded-painter mirror (opening passes identical, the second mover owns both bases at every tick end before the onset, every swing favours the second mover under both orders, capture at tick 93); jam sniper v min guard (capture at tick 4; the guard's actions per tick 4, 5, 4, 5 become 5, 5, 5, 5); the probe mirror (mutual elimination at tick 3); spread sniper v disrupt guard (zero core inside 998 ticks, never at a tick end); and sniper v min guard and the disrupt-guard mirror (identical end-of-tick states under both orders). |
| Mutation checks | Fifteen deliberate breakages were each applied to the committed code (`4d4ede7`), run against the relevant E4 test modules (and, for the forward-path drift, both parent freezes), and restored byte for byte from `HEAD`, with the tree verified clean afterwards. None was committed. Every one is detected; the number of failing tests is in brackets. <ul><li>Mirrored passes begin one pass too early (35) or one pass too late (34).</li><li>Rotation disabled under mirroring (29).</li><li>Slot numbering restarting after the reversal (56).</li><li>The final chunk left with the second mover (52, including G.4′ and G.5′).</li><li>Rotating instead of reversing, identical for two entrants (9, all three-entrant cases).</li><li>The scheduler flag defaulting to `True` (1, the pre-E4 oracle grid).</li><li>Forward K = 2 Rulesets mirrored (49: 48 E4-parent freeze rows and the scheduler-mapping test; the E3-parent freeze's whole-tick E2 rows do not move under pass order, which is why the E4 freeze was needed).</li><li>The primary treatment differing from its parent in `disruption_slot_limit` too (2).</li><li>`"mirrored"` accepted for a non-chunked scheduler (3).</li><li>`run_scheduler` no longer passing the flag, so G.4′ falls to (5, 4) (40).</li><li>A hit suppressing two offers, which breaks the G.5′ premise (33).</li><li>E4 leaking into omitted-Ruleset resolution (1) or the Designer options (1).</li><li>An omitted arena resolving to the `Config` default instead of 512 (6).</li></ul> |

## E3 record addenda (separate commit `e52b5aa`)

Two items from the review (§B, §S-7, §S-8) were independently re-verified against the preserved E3 corpus and recorded as a dated addendum to the [E3 results](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md), with the original text unchanged:

- **Erratum.** The guarded-painter mirror went 19 Seat-A / 13 Seat-B seeds under T-E3 (38/26 matches), not 20/12; the quoted +0.1875 bias was already the 19/13 value. No registered E3 verdict changes.
- **Methodology clarification.** Twin-mirror orientation swaps are pure relabellings (352/352 pairs with byte-identical tick records in each of C-E2, T-E3 and T-E3K1), so historical mirror SDI is 1.0 by construction on decisive seeds. This is prospective only; no historical calculation is altered.

## Reconciliation against the review's §U

- **Matches.**
  - **§U-1.** The §R step-2 freeze was committed before any scheduler change.
  - **§U-2 / §K.** Field, mode set, validation (unknown → `ValueError`; `"mirrored"` requires `"chunked"`), `run_scheduler` wiring, two literal policies, registration in `PROCESS_RULESET_IDS`, `_RULESET_POLICIES`, `ACTIVE_RESEARCH_RULESET_IDS` and `__all__`, and the ID constants in `rules.py`.
  - **§U-3 / §J.** A keyword-only `mirror_second_half`; passes with `2p ≥ P` reversed; docstring updated; nothing else in the scheduler changes.
  - **§U-4.** None of the listed surfaces is touched, and there is no ID branching.
  - **§U-5.** The E3 plumbing precedent, including trap F-4.
  - **§U-6.** Every listed test family (table above).
  - **§L.** Every named trace the tests pin reproduces the review's probe.
- **Intentional clarifications.**
  - `SCHEDULER_PASS_ORDER_MODES` is a class attribute of `RulesetPolicy`, like the other mode sets.
  - Non-string values are rejected with `ValueError` rather than failing as an unhashable lookup.
  - With an odd pass count the mirrored order reverses the later ⌊P/2⌋ passes, exactly as §J's `2p ≥ P` states; the E4 configuration has P = 4.
- **Observation, no conflict.** §L-3's shorthand writes the second mover's opening chunk as `B485 –`; the replay shows the lost offer is the first of that chunk (`B– B485`), as §L-1's notation has it. Nothing depends on it.
- **Deferred (by design).** §R steps 4–9 and the real-fixture D9′ gate.
- **Conflicts: none.**

## Qualification

Qualified at `4d4ede7`, the code-complete commit, on Windows 11 (`Windows-11-10.0.26120-SP0`) with Python 3.13.14 in the repository `.venv`:

| Check | Result |
|---|---|
| `python -m pytest` (the repository suite: `_legacy/tests`, `engine/tests`, `client/tests`) | **4014 passed, 18 skipped, 3 deselected, 0 failed** (464.6 s) |
| `python -m ruff check .` | All checks passed |
| `python -m mypy engine/src/battle_engine` | No issues in 97 source files |
| `python -m mypy client/src/battle_client` | No issues in 16 source files |

- The 3 deselected tests are the `gui`-marked display tests that `pytest.ini` excludes. The 18 skips are environmental only: symlink creation without elevation, NTFS colon names, POSIX-only symlink semantics, and frozen-executable smokes that need a built `bytefray.exe`.
- 272 of the passing tests are new in this phase: 98 in the parent freeze, 94 in the semantics module and 80 in the Ruleset module. The four extended inventory modules keep their test counts.
- `HEAD`, a clean tree and SHA-256 digests of the scheduler, policy, rules, match-service, evaluation, process-runtime and Python-runtime modules and the three new test modules were recorded before the run and were identical after it. The run was the only pytest process.
- Research tooling (`tools/`) is unchanged in this phase, so mypy was not widened beyond the two package invocations.

This record is committed after that run and changes documentation only.

## Not done here (next phase)

- the E4 analyzer (FMA, FPS from the registry, the census, seat metrics, the G.4′ check, the relabel gate);
- the prospective seat metrics and the a-priori contest-class table;
- the E4 pre-registration (§N–§P, digest-pinned);
- the E4 matrix (F1, F2, F2-P, F4; C-E4, T-E4, C-E4K1, T-E4K1);
- the parent reproduction controls and the P-PAR/P-STALE population freeze;
- the matrix and analysis freeze identities;
- the D9′ real-fixture gate;
- separate authorization to run the treatment.

**No E4 experimental matrix has been run in this phase, and no E4 gameplay conclusion may be drawn from it.**
