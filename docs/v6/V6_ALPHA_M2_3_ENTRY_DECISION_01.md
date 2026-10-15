# Bytefray V6 — M2-3 Roaming Reacquirer Entry Decision Packet 01

2026-10-15, America/Indianapolis. **Read-only readiness review. M2-3 is NOT
AUTHORIZED; no M2-3 code, fixture, test or registry change has been made.**

**Recommendation: READY FOR AUTHORIZATION**, provided the grant confirms the
three policy-reading clarifications in §3 and the boundary in §4.

## 1. Basis

Governing contract: [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md) §5
(R1 policy), §6.2 (relocating fixture and both-seat schedule), §7 (orchestration,
provenance, scenario verification), §3 (registration and personal copies), §10
(compatibility) and the §11 M2-3 milestone row. The design finding is F04 in
[Checkpoint B 01](V6_ALPHA_M2_CHECKPOINT_B_01.md#2-finding-by-finding-resolution-matrix):
resolved in the contract, with runtime proof pending M2-3. The predecessor slice is
closed by [M2-2 Closure 01](V6_ALPHA_M2_2_CLOSURE_01.md).

Purpose: show an entrant deciding under incomplete, delayed and stale delivered
information. It holds a historical contact, pays for rescans, records that an
old address is absent from a newer sample, pays to move and search, and
responds to a new anonymous contact without claiming it is the same process.
M2-3 adds no mechanic, ruleset, wire field or research heuristic.

## 2. Readiness findings

| Area | Finding |
| --- | --- |
| Approved behavior and parameters | §5 fully specifies the R1 states (SEARCH, HOLD, RESCAN, SEARCH_AFTER_ABSENCE, RESPONSE), response byte `0x52`, forward-on-tie shortest direction, legal fallbacks, and three integer parameters: `search_offset` 91 (0..128), `move_step` 64 (1..64), `rescan_wait` 3 (1..8). |
| Observation age / staleness | Uses only delivered `previous_sense_anchors` plus stored own history; no TTL, live refresh, global negative or identity inference (§2, §5). An absent rescan is recorded only as "old address absent in newer sample". |
| Movement versus sensing cost | Every SENSE, READ wait, MOVE and WRITE costs one ordinary opportunity; substituted fallbacks do not count as SENSE, rescan, search MOVE or response witnesses (§5). |
| Legal receipts / no notifications | Engine semantics match the contract: `previous_sense_anchors` is delivered only at the same process's next callback, even after suppression; a refused SENSE yields `None`; MOVE takes a signed delta clamped to ±64. Window Scout already exercises MOVE+SENSE under Alpha 1; R1 needs no new observation field. |
| Schedule feasibility (§6.2) | Static recheck holds in both seats: R1 SENSE91 from anchor 0 (distance 91 ≤ 128) samples the fixture at 91; F4 MOVE(+64) occurs after the R2 receipt and before R5; R5 window 64..118 is empty; R6 MOVE to 64; R7 SENSE155 (distance 91); R8 WRITE155 is legal and touches neither core window. The chunk-of-2 interleaving this assumes is confirmed by M2-2's engine runs (Keeper witnesses at global indices 8 and 6). Still a prediction until R1 runs. |
| Verification infrastructure | The Keeper verifier already checks scripted fixture MOVEs and reconstructed per-decision anchors (`world.get_anchor`) through the unchanged common `reconstruct_sensing_playback`, so `reacquirer-R1` can verify the 91→155 relocation omnisciently without a new reconstruction or persisted field. |
| Both-seat filtering | `SensingCursor` already accepts entrant `"A"`, `"B"` or `None`; `SensingPresentation` is fixed to `"A"`. M2-3 verifies seat-B payload filtering at the cursor level in tests. The product A/B selector remains M2-4 (M2-AC07), so seat-B Reacquirer lessons are not yet viewable from B's side in the product viewer. |
| Replay comprehension | The existing M1 viewer already renders "absent in newer scan" history wording. M2-3 adds no viewer change. C2 marker-label overlap and the M1 history/footer overlap remain present until M2-4. |
| Keeper / Scout compatibility | R1 work is additive beside the accepted Keeper route and validator. Keeper and Scout sources, digests, validators and demo routes stay byte-identical. |

## 3. Clarifications the grant should confirm

These readings follow §5's wording and do not affect the declared §6.2 fixture
sequence. They do determine edge-case behavior and tests. Different direction
from the lead changes only tests and policy branches, not the fixture or schedule.

- **I1 — Mode after an empty initial search.** An applied empty receipt in
  SEARCH keeps the mode SEARCH (MOVE forward, then a new anchor-relative SENSE).
  SEARCH_AFTER_ABSENCE is entered only from a RESCAN whose receipt omits the
  old address. Consequently, a positive receipt in SEARCH is handled by the
  "Initial SEARCH applied positive" row (store target and HOLD, no WRITE). Only a
  positive receipt in SEARCH_AFTER_ABSENCE is a "new anonymous contact" with a
  WRITE or RESPONSE.
- **I2 — Refused, null or absent rescan feedback.** No absence or positive
  transition is recorded. The stored historical target and all samples are
  retained as history, but the active target is cleared. The agent resumes a
  fresh anchor-relative search in its prior search family: SEARCH, or
  SEARCH_AFTER_ABSENCE if that mode produced the target.
- **I3 — First-callback fallback.** If the SEARCH center is illegal or sensing
  is unavailable, the legal fallback (READ own_core_base if in reach, otherwise
  MOVE(0)) is issued and SEARCH is retried on the next callback. The fallback
  is never counted as a scan.

## 4. Proposed authorized file boundary (smallest useful slice)

The slice is the Reacquirer vertical only, mirroring Checkpoint B §3 for Keeper.
Every change to an existing file is additive. No line of the accepted Keeper or
Scout logic is modified.

| Path | Permitted change |
| --- | --- |
| `engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.py`, `agent.yaml` (new) | R1 policy, parameters, `capabilities: {version: 1, required: [sense]}`, `standard` preset |
| `engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.py`, `agent.yaml` (new) | §6.2 script: F1–F3 READ91, F4 MOVE(+64), then READ91; internal, not a starter |
| `engine/src/battle_engine/starters.py` | Insert `v6_roaming_reacquirer` after `v6_watchful_keeper` and add only its digest |
| `engine/src/battle_engine/agent_scaffold.py` | `roaming_reacquirer` template key, personal-copy name/display label, help and next-step text |
| `app/views/development.py` | "Roaming Reacquirer — personal copy" label; hint text naming the third starter |
| `engine/src/battle_engine/sensing_demo.py` | New `run_reacquirer_demo` and `--scenario reacquirer-R1` / `--reacquirer-seat`; `run_keeper_demo` and Scout bodies unchanged |
| `engine/src/battle_engine/sensing_playback.py` | New `ReacquirerScenarioVerification`, `evaluate_reacquirer_policy`, `verify_reacquirer_scenario`; Keeper, Scout and common reconstruction unchanged |
| `engine/tests/test_v6_alpha_m2_reacquirer.py` (new) | Focused policy, fixture, native, provenance, negative and output-safety cases |
| `engine/tests/test_agent_scaffold.py`, `engine/tests/test_v6_alpha_m1_2_window_scout.py` | Template set and catalog suffix expectations only |
| `engine/tests/test_agent_test.py` | Add `roaming_reacquirer` to existing explicit-Alpha 1 / stable-rejection parametrizations only |
| `tests/test_v6_alpha_m1_5_designer.py` | Reacquirer native seat A/B cases, `gui`-marked |
| `docs/specs/agent_scaffold.md`, `docs/AGENT_AUTHORING.md`, `docs/v6/V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md` (new) | Bounded documentation and implementation record |

Excluded: `agent_test.py` and other production CLIs; `rules.py`,
`ruleset_policy.py`, `agent_api.py`, simulation and worker modules; all
`client/` code (A/B selector, layout and C2 fixes are M2-4); Keeper, encroaching,
Scout and stationary sources and digests; demo-v1 schema or any new persisted
field; scenario cards; research paths; README/ROADMAP beyond status lines.
Needing any other path is a stop condition (§8), not a silent widening.

## 5. Acceptance criteria

| ID | Criterion (contract reference) |
| --- | --- |
| R3-01 | M2-AC01: valid capability block; explicit Alpha 1 success; stable-V4 mismatch before import/reset/artifacts on match, worker, validate, Development Test and direct routes; malformed blocks fail closed |
| R3-02 | M2-AC03: supplied-observation cases for every §5 table row, I1–I3, tie direction, MOVE ≤ move_step and ≤ 64, parameter bounds and range rejection, one action per callback |
| R3-03 | M2-AC04: data-source audit (no seed/RNG, host, placement or opponent access); refused/null, absent, empty, suppression-delayed and terminal-undelivered feedback; an unrelated READ is never a receipt; costs truthful |
| R3-04 | M2-AC03/05: native R1→R8 sequence in both seats, matching the §7 witness predictions, with fixture relocation verified omnisciently and no identity, notification or TTL wording in entrant history |
| R3-05 | M2-AC05: separate consistency, reconstruction, capture and completion verdicts. Completion is refused for a valid pair lacking reacquisition, a false success assertion, a wrong archetype/revision/role/input/parameters, drift, an interrupted prefix or a corrupt binding. An edited copy earns no badge. Keeper and Scout verifiers never award R1 completion, and R1 never awards theirs. `demo.json` stays `unverified` without `teaching_exchange` |
| R3-06 | M2-AC06: copy → explicit Alpha 1 Validate → parameter edit → Advanced full match → reopen; range rejection; overwrite refusal; manifest-default Development Test; earlier-settings access; native on Windows and Linux |
| R3-07 | Compatibility: Keeper's 48 cases and Scout unchanged and passing; old starter bytes and digests, including Keeper's, preserved; `STARTER_AGENT_NAMES[-1] == "v5_dual_team"`; V4 defaults, readers and retired refusal |
| R3-08 | M2-AC12: Ruff, separate engine/client mypy, 329 pins at `b948540…`, safe fresh output and pytest roots, no research operations |
| R3-09 | Lead review of the M2-3 record; no automatic M2-4 entry |

**Focused regression plan.** Run tests in this order, using fresh pytest roots
outside `runs/`:

1. The new Reacquirer module, then the Keeper module.
2. The retained 22-module focused selection plus `test_agent_test.py` (23 modules).
3. Explicit `-m gui` Reacquirer and Keeper Designer nodes.
4. Because `starters.py` and the scaffold change, the 137-module product
   selection plus additions and the 328-node supplement, with a new node/skip
   ledger.
5. Ruff and both mypy runs.
6. Keeper `keeper-K1` once per seat as a regression witness, compared logically
   with the retained M2-2 bodies. The Keeper sources are unchanged, so no new
   M2-2 repeat set is created.

Linux: the focused selection, Designer GUI nodes and the four R1 runs.

## 6. Compatibility requirements

Preserve every existing bundled starter byte and digest, now including
`v6_watchful_keeper` `35b945ad…`. Keep catalog order Scout → Keeper → Reacquirer →
`v5_dual_team`. Keep Scout's seven-event `teaching_exchange` meaning and
evaluator unchanged, as well as Keeper's accepted route, verifier and approved
revision pins. Keep stable V4 as the omitted and default ruleset, with Advanced
and Development requiring explicit Alpha 1, and keep historical readers and
retired refusal. Retain the published capture regression modules. The accepted
M1 sensing semantics, the M2-2 acceptance and its conditions C1–C3 stay as
recorded.

## 7. Expected demonstration scenarios

`reacquirer-R1` uses the declared profile: arena 512, Q=8, seed 0, 100 ticks,
starts 0 (Reacquirer) and 91 (fixture), default parameters 91/64/3, and whole
entrant-role reversal. Run two repeats per seat per platform: four Windows and
four Linux complete runs under fresh `runs/v6_alpha_m2/<campaign>/reacquirer/<seat>/<repeat>/`
leaves. Retain replay, trace, result, demo-v1 sidecar, executed sources and
fingerprints.

Predicted tick-1 witnesses (zero-based global decision index; static predictions
derived from the Keeper-confirmed ordering):

| Seat | R1 SENSE91 | R2 receipt + READ0 | R5 rescan SENSE91 | R6 empty receipt + MOVE(+64) | R7 SENSE155 | R8 receipt + WRITE155 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R=A, F=B | 0 | 1 | 8 | 9 | 12 | 13 |
| F=A, R=B | 2 | 3 | 10 | 11 | 14 | 15 |

Fixture F4 MOVE(+64) is at index 7 (seat A) or 5 (seat B). Both entrants are
expected to survive to tick 100. After R8, the agent should cycle HOLD and
RESCAN on the unchanged contact at 155 without further WRITEs. That tail is
expected, not required evidence. Seat-B entrant-view inspection uses
`SensingCursor(entrant_id="B")` in tests until M2-4.

## 8. Known risks and stop conditions

| Risk | Handling |
| --- | --- |
| Engine-run sequence differs from §6.2 (for example an empty R1, F4 after R5, illegal R7/R8) | **STOP; HOLD for design decision.** Do not tune fixture constants or parameters to force the lesson |
| Lesson needs a notification, identity, TTL, hidden state or new observation/wire field | **STOP** (contract §5/§7 stop conditions) |
| Opponent eliminated or suppressed before the sequence completes | **STOP**; no schedule rewrite without lead decision |
| Common reconstruction lacks a needed fact | **STOP**; no new persisted field or schema change without version review |
| Need to touch Keeper/Scout logic, `client/`, rules or policy modules | Outside the boundary; record why and request a scope decision |
| Seat-B delivered view not selectable in the product viewer | Accepted M2-4 dependency; verified at cursor level only |
| C1 recurrence in native viewer checks | Treat as a possible product defect, per the M2-2 closure; retain key witness and exit status |
| M2-3 built on an uncommitted M2-2 candidate | M2-3's diff must be verified against the hashed M2-2 manifest in [Closure 01 §3](V6_ALPHA_M2_2_CLOSURE_01.md#3-accepted-source-manifest). Committing M2-2 first is strongly recommended so the slices stay separately reviewable |
| Rewind reconstruction cost (30–40 s Test replay load) | Existing accepted limitation; use bounded, workload-aware waits |

## 9. Entry prerequisites

1. Explicit lead grant for M2-3, naming the §4 boundary and confirming or
   amending I1–I3.
2. Entry recheck as in M2-2: HEAD, branch and index; live remote by read-only
   query; the M2-2 accepted manifest and contract hashes; the 329 pins; fresh
   safe roots.
3. Recommended: lead decision on publishing or committing the M2-2 closure
   first ([Closure 01 §10](V6_ALPHA_M2_2_CLOSURE_01.md#10-repository-reconciliation-and-publication-proposal)).
4. Both native platforms available (Windows; Linux WSL2/WSLg X11 with the
   retained user-local environment), with the delivered-key witness enabled.

No E8/E9 activity, sealed-evidence change, M1 semantic change or Keeper redesign
is part of this entry. Original E9 remains operationally blocked with execution
LOCKED, and Requirement C remains NOT ESTABLISHED.
