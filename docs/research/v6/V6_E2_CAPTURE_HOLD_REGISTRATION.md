# Bytefray V6 E2 — Capture-Hold Research Ruleset: Registration

**Status:** Research Ruleset implemented and qualified. **The E2 experiment has not been run**, and nothing here is a gameplay result.
**Branch:** `v6-research`
**Semantic authority:** [`V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md), in particular §C (semantics), §E (code surface), §F (Ruleset definition), §J (test plan) and §K (artifacts). This note records what was registered and where. It does not restate or change the review's findings.

## The question E2 asks

Under stable V4, competent global-reach play produces a deterministic tick-1 Seat-A forced core capture (`engine/tests/test_v4_exploit_characterization.py`). E2 changes exactly one link of that causal chain: zero core ownership stops being immediately fatal.

The experiment asks: **does delaying fatal capture for one additional qualifying tick create meaningful opponent-dependent response, or does it merely transform the original forced line into delay, scheduler-locked draws, or another seat pathology?**

The review's exploratory probe (§D) already suggests a mixed result that leans negative. Those probe numbers are priors to be falsified, not results. A clean negative result is an acceptable and informative outcome (review §H, "Negative-result rule").

## Identity and policy

| Item | Value |
|---|---|
| Ruleset ID | `bytefray-rules-6-research-capture-hold-k2` (`rules.BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID`) |
| Policy object | `ruleset_policy.RULESET_V6_RESEARCH_CAPTURE_HOLD_K2`, an independent literal, never `dataclasses.replace` of its control |
| Control (parent) | `bytefray-rules-6-research-scale` |
| Only gameplay difference | `RulesetPolicy.capture_hold_ticks`: control `1`, E2 `2` |
| Lifecycle | `ACTIVE_RESEARCH_RULESET_IDS` |

`RulesetPolicy.capture_hold_ticks` is a new policy field with default `1`, which every other registered Ruleset keeps. It must be an `int`, `bool` is rejected, and the value must be `>= 1`; anything else raises `ValueError`. There is no per-match override: E2 runs must still assert the request-level scheduler, `kill_weight` and `instr_per_tick` overrides are `None` (review §A.2 item 4, §E.3).

**Permanent obligation (review §E.5).** Artifacts carry only the Ruleset ID, so once E2 artifacts exist the E2 policy's field values must never change, and retiring E2 must keep it resolvable.

## Exposure

- **In:**
  - `PROCESS_RULESET_IDS`;
  - `_RULESET_POLICIES`;
  - `ACTIVE_RESEARCH_RULESET_IDS`;
  - the core-placement overlap guard (`match_service._CORE_PLACEMENT_GUARDED_RULESET_IDS`);
  - the evaluation allow-list;
  - the `agents evaluate --ruleset` choices.
- **Out:**
  - `PUBLIC_STABLE_RULESET_IDS` and `OMITTED_RULESET_CANDIDATES`;
  - the `--ruleset` choices of `run`, `agents test` and tournament;
  - every Designer Ruleset option tuple.

  An omitted Ruleset for an Agent API v2 roster still resolves to `bytefray-rules-4`.

## Runtime semantics as implemented

The runtime implements review §C.2 in `python_runtime.apply_core_capture(..., hold_ticks=K)`, with per-entrant state `EntrantState.core_zero_streak` and `core_zero_onset_capturer`. `process_runtime` passes `ruleset_policy.capture_hold_ticks`. No runtime code compares Ruleset IDs.

- **Where.** Capture is evaluated exactly where V4 evaluates it: once per tick, after every action, before statistics, scoring and termination. A core that reaches zero and recovers within one tick is invisible.
- **Reset.** Any positive ownership (one cell or the whole core) resets the streak to 0 and clears the attribution.
- **Onset.** The first zero evaluation of a streak attributes the capturer with the unchanged `_attribute_core_capture`, against that onset tick's own snapshot and diffs, and keeps the result.
- **Completion.** When the streak reaches K, the entrant becomes `core_captured`. Kill credit (+5, `statistics.kills`, `kill` event) goes to the onset capturer. Re-attributing at completion would always yield an unattributed `death` (review §C.5, finding F-1).
- **Two phases.** Phase 1 judges every live entrant against the same end-of-tick board and changes no `alive` flag. Phase 2 applies all completions. Simultaneous completion therefore gives `all_agents_dead` / `tie` in either seat order; iteration order affects only the order of appended events.
- **K = 1.** Onset and completion are the same evaluation, which is exactly V4.
- **Forfeit.** Forfeit stays independent. A forfeiting entrant is never evaluated again, and its capturer gets no credit.
- **Reachable states.** Alive at zero core, a zero-core winner, the tick limit at streak 1, and `1,0,1,0,…` alternation are all reachable. No rule was added for any of them (review §C.6).

One consequence follows from §C.2 literally and is recorded here so it is not mistaken for a defect. Suppose an entrant completes its hold on the tick its onset capturer forfeits. The kill is still credited to that capturer, although it is no longer alive. The match result is `all_agents_dead` / `tie` (review §C.3). V4 already credits a capturer that forfeits later in the same capture tick.

## Evaluation methodology

E2 inherits the research-scale methodology unchanged:

- seeded placement with the paired orientation swap;
- identity and schema version 7;
- arena range `[64, 65536]`;
- an omitted `--arena-size` resolves to **512**, never `Config().arena_size` (4096; review trap F-4).

It has its own arena-alignment label, `ruleset_v6_research_capture_hold_k2_seeded_placements`. The new methodology flag (`is_v6_research_capture_hold_methodology`) is **keyword-only** on `resolved_arena_alignment_mode` / `resolved_identity_version` / `resolved_schema_version`, so no call site can set it by position. The wider positional-boolean fan-out stays deferred (review F-13).

## Artifacts

There is no replay, result or client change:

- no `capture_threat` event;
- no streak field;
- the event vocabulary is still `kill` / `death` / `forfeit`;
- replay schema 4 is unchanged.

`EntrantState` is never serialized wholesale. Capture progress is research telemetry, to be derived later from replay memory diffs (review §K).

## Evidence (tests)

| Review § | Coverage |
|---|---|
| J.1 V4 preserved | `test_v4_exploit_characterization.py`, `test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`: unedited. **New:** `test_v4_k1_capture_byte_identity.py` holds 15 stable-V4 matches (probe mirror, plus `v4_claimer`/`v5_scout_striker` and `v4_local_defender`/`v5_dual_team` in both seat orders, seeds 1–3, arena 512). Their canonical replay SHA-256, `result_id` and `match_id` were frozen and committed *before* the capture change. |
| J.2 policy / identity / plumbing | `test_ruleset_v6_research_capture_hold.py` |
| J.3 semantics | `test_e2_capture_hold_semantics.py`, using scripted entrants on `ProcessMatchController`, with whole per-tick sequences asserted by value |
| J.4 mechanics (§D.3–D.6, seed 42, arena 512) | `test_e2_capture_hold_semantics.py`, run end to end through `NativeMatchService` and asserted from the canonical replay |
| J.5 determinism / serialization | `test_ruleset_v6_research_capture_hold.py`. The E2 replay and `result.json` have exactly the control's key structure. Run on Windows here; the same tests run unchanged on the Linux CI leg. |

The J.4 tests pin **mechanics**, not balance outcomes: the D.3 zero-core winner at tick 2, the D.4 nominal repair window, the D.5 parity-locked alternation, and the D.6 location-count onset at tick 2 and capture at tick 3.

## Not done here (next phase)

- the E2 research-agent fixtures (review §G);
- the replay-derived capture analyzer (§K);
- harness remediation HD-1 to HD-7 (§I.4);
- freezing the hypotheses and the matrix (§H, §I);
- qualification;
- running the E2 experiment.

No E2 gameplay conclusion may be drawn from this implementation phase.
