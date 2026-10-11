# Bytefray V6 — Milestone M1-3 Implementation Record 01

**Document ID**: `docs/v6/V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md`
**Date**: 2026-10-11
**Milestone**: Bytefray V6 Phase 1, Milestone M1-3 (Artifact Validation and Sensing-Exchange Reconstruction)
**Status**: FORMALLY CLOSED — final acceptance review complete 2026-10-11 (see §9; §§1–8 are the implementation report as submitted)

---

## 1. Executive Summary and Authorization

Under Phase 0 bounded M1 authorization and governed by the V6 Alpha M1 Contract ([`V6_ALPHA_M1_CONTRACT_01.md`](file:///d:/Projects/BATTLE2/docs/v6/V6_ALPHA_M1_CONTRACT_01.md)), Milestone M1-3 delivers independent artifact validation and sensing-exchange reconstruction for Bytefray V6 active spatial sensing demonstrations.

The implementation provides:
1. **Independent Sensing-Exchange Reconstruction Engine (`sensing_playback.py`)**: Consumes canonical `replay4` and API-v2 `trace2` artifacts, independently reconstructs fine-grained sub-tick world states (anchors, arena memory, cell ownership, process disruptions, and alive entrant sets), independently derives spatial sensing samples at the exact action sample point, verifies delayed anonymous receipt delivery ordering, reconciles reconstructed state against canonical replay tick snapshots at every tick boundary, and evaluates the authoritative teaching exchange facts without re-running whole-match simulation or trusting narrative text.
2. **Authoritative Artifact and Provenance Verifier (`verify_demonstration_artifacts`)**: Validates `demo.json` schema (`bytefray.sensing_demo`), schema version (`1`), provenance (`product_teaching_demo`), declared product fixture flag, expected ruleset (`bytefray-rules-6-alpha1`), and cryptographically verifies SHA-256 digests of all referenced artifacts (`replay.jsonl`, `trace.jsonl`, and required `result.json`).
3. **Formal Teaching Exchange Evaluator (`evaluate_teaching_exchange`)**: Characterizes the 7 canonical teaching exchange steps into structured `VerifiedExchangeStep` and `VerificationStatus` (`VERIFIED`, `NOT_VERIFIED`, `NOT_PROVEN`), proving incomplete information, legal sensing request, 1-action cost, historical sample capture, anonymous receipt delivery, informed movement, and optional in-reach interaction.
4. **Structured Error Hierarchy**:
   - `SensingPlaybackError`: Base class for playback and verification failures.
   - `ArtifactIntegrityError` (inherits `PairBindingError`): Raised for corrupted artifacts, mismatched SHA-256 digests, unreadable files, broken pair bindings, or mismatched match IDs / ruleset IDs / result IDs.
   - `ExchangeReconstructionError`: Raised when trace evidence is internally invalid (illegal actions, non-integer operands, out-of-reach operands, quota violations, incorrect sensed samples, premature or dropped receipts, refreshed future opponent state, or leaked passive enemy visibility).
   - `ExchangeConsistencyError` (inherits `PairConsistencyError`): Raised when trace decisions contradict subsequent observation anchors or when reconstructed sub-tick states disagree with canonical replay tick snapshots (including anchor mismatches, memory diff contradictions, disrupted process mismatches, alive status mismatches, CPU used discrepancies, or cumulative memory write mismatches).
5. **CLI Playback & Verification Tool (`battle_engine.sensing_playback`)**: Command-line interface accepting a demonstration directory or explicit `--replay` / `--trace` / `--result` / `--demo` paths, returning exit code 0 for verified demonstrations, 1 for verification failure, and 2 for argument errors.
6. **Comprehensive Automated Test Suite (`test_v6_alpha_m1_3_sensing_playback.py`)**: 27 focused unit, regression, reconstruction, adversarial tampering, ordering, cost/quota, cadence, and research-isolation tests.

---

## 2. Deliverables Inventory

| Path | Category | Role |
|---|---|---|
| `engine/src/battle_engine/sensing_playback.py` | Engine Reconstruction / CLI | Independent artifact validation, sub-tick world-state derivation, sensing-exchange reconstruction, teaching evaluation, and CLI entrypoint. |
| `engine/tests/test_v6_alpha_m1_3_sensing_playback.py` | Test Suite | 27 automated tests verifying artifact integrity, pairwise consistency, sub-tick reconstruction, teaching exchange steps, adversarial negative mutations, CLI, and research isolation. |
| `docs/v6/V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md` | Documentation | Authoritative M1-3 implementation record. |

---

## 3. Independent Reconstruction Architecture and Algorithm

In strict accordance with the M1 Contract:
- **No Whole-Match Simulator**: The reconstructor does not re-simulate or execute agent Python code. It reconstructs the causal timeline directly from recorded authoritative artifacts (`replay.jsonl`, `trace.jsonl`, `result.json`, `demo.json`).
- **No Trust of `demo.json` Narrative**: The reconstructor treats `demo.json` purely as an envelope defining artifact bindings and expected identifiers. It independently derives all world states and facts from the raw replay snapshots and trace decision records.
- **Wire Schema Preservation**: `replay4`, `trace2`, and `result2` wire schemas are consumed unmodified.

### 3.1 Algorithm Breakdown

1. **Artifact Integrity and Pair Binding**:
   - Reads and validates `demo.json` metadata (schema, provenance, ruleset, filenames, SHA-256 hashes).
   - Strictly requires `replay.jsonl`, `trace.jsonl`, and `result.json` artifacts.
   - Verifies replay-trace binding via `verify_pair(replay_path, trace_path)`, ensuring trace's `binding.replay_sha256` exactly matches canonical `replay.jsonl`'s actual SHA-256 digest.
   - Validates `result_envelope.replay.sha256` and reconciles `match_id`, `result_id`, and `ruleset_id` across result, replay header, and demonstration metadata.
   - Verifies ruleset policy is active sensing (`sensing_mode == "active"`) with a valid `sensing_window` (27).

2. **Sub-Tick World State Tracking**:
   - Initializes arena memory, cell ownership, process anchors, alive entrants, and disrupted processes from `replay.jsonl` Tick 0 initial state.
   - Verifies monotonic non-decreasing tick ordering of all decisions in the trace document.
   - Groups trace decisions by tick.
   - For each tick (1 to `max_tick`):
     - **Observation Verification**:
       - Checks `obs.self_anchor` against reconstructed process anchor; raises `ExchangeConsistencyError` on mismatch.
       - Enforces active sensing invariant: `obs.visible_enemy_anchor_addresses == ()`; raises `ExchangeReconstructionError` if passive enemy visibility leaks.
       - Checks pending sensing deliveries: if a delivery was pending from an earlier SENSE action, validates that `obs.previous_sense_anchors` is present and matches the historical sample derived at the sample point. If no delivery was pending, rejects any unexpected `obs.previous_sense_anchors`.
     - **Action Application & World State Transition**:
       - Enforces per-entrant action budget quota: `entrant_actions_this_tick[agent_id] <= action_budget`.
       - Validates integer types on all action operands and values (rejecting booleans or floats).
       - Validates action cost (`cost == 1`).
       - If `action.kind == "sense"`:
         - Checks operand is within process reach (`reach == 128`); raises `ExchangeReconstructionError` if out of reach.
         - Computes circular sensing window `[operand - 27 .. operand + 27]` using modular circular distance.
         - Identifies enemy process anchors currently residing within the window from current reconstructed anchors.
         - Records sample point `(tick, decision_index)` and pending delivery fact.
         - Reconciles derived sample against trace's `applied_result.sensed_anchors`.
       - If `action.kind == "move"`:
         - Updates process anchor: `(current_anchor + operand) % arena_size`.
         - Reconciles against `applied_result.normalized_address`.
       - If `action.kind == "write"`:
         - Updates memory and ownership at `(operand % arena_size)`.
         - Increments cumulative memory writes for the entrant.
         - Checks for shared-location disruption of other entrants.
     - **Tick-End Canonical Reconciliation**:
       - Compares applied memory writes this tick against replay snapshot `memory_diffs`.
       - Compares all process anchors against replay snapshot `processes`.
       - Compares process disruption set against replay snapshot `disrupted` flags.
       - Reconciles alive entrant set against replay snapshot `agents`.
       - Reconciles per-tick `agent.cpu_used` against entrant action count in trace.
       - Reconciles cumulative `agent.mem_writes` against cumulative entrant applied writes.
       - Raises `ExchangeConsistencyError` if any reconstructed state contradicts the canonical replay snapshot.

3. **Teaching Exchange Evaluation**:
   - Identifies the primary active sensing agent (`scout_id`, parameterized with fallback to entrant `"A"` or `v6_window_scout`).
   - Traverses verified facts to prove the 7-step sequence:
     - Step 1 (`incomplete_info_before_sensing`): Proves pre-sensing observation had empty passive visibility, absent receipt, and multi-entrant arena.
     - Step 2 (`legal_sense_request`): Proves legal SENSE action with operand within reach (dist <= 128) and status APPLIED.
     - Step 3 (`one_action_sensing_cost`): Proves action consumed exactly 1 quota with zero memory mutation.
     - Step 4 (`historical_sample_captured`): Proves spatial window evaluated against world state at exact sample point `(tick, decision_index)` and isolated from entrant audience.
     - Step 5 (`anonymous_sample_delivered`): Proves delayed delivery on immediate subsequent decision, delivering contact addresses only, matching sample point.
     - Step 6 (`legal_move_informed`): Proves subsequent MOVE action directed toward sensed contact (operand 64).
     - Step 7 (`optional_write_supported`): Proves optional post-MOVE in-reach WRITE interaction (operand 91), reporting `NOT_VERIFIED` on failed write attempts.
   - Steps not observed due to truncated run are marked `NOT_PROVEN` without guessing.

---

## 4. Verified Exchange Findings and Invariants

Independent reconstruction confirms the following critical invariants of Bytefray active spatial sensing:

1. **Strict Active Information Acquisition**:
   - In active sensing rulesets (`bytefray-rules-6-alpha1`), passive enemy visibility is always empty (`obs.visible_enemy_anchor_addresses == ()`). Any attempt to leak enemy positions via passive observation is caught and rejected (`ExchangeReconstructionError`).
2. **Historical Snapshot vs Future State**:
   - Sensing captures a snapshot of the arena at the sample point `(tick, decision_index)`.
   - When an opponent moves between the sample point and the receipt delivery point, the delivered receipt MUST reflect the historical sample position, NOT the opponent's current/future position.
   - Tested and proven via adversarial test `test_receipt_refreshed_with_future_opponent_state_rejected`: artificially refreshing the receipt to the opponent's post-move position is detected and rejected with `ExchangeReconstructionError`.
3. **Single-Shot Ephemeral Receipt**:
   - The delivered receipt is present only on the immediate subsequent decision callback for that process.
   - On following callbacks, `previous_sense_anchors` is absent.
   - Sensed sample delivery before an eligible SENSE action is rejected (`test_receipt_before_eligible_delivery_rejected`).
   - Dropping an owed sensing sample is rejected (`test_dropped_receipt_rejected`).
4. **Sub-Tick World State Consistency**:
   - Trace movement actions immediately constrain subsequent observation records. Mutating a move operand in the trace causes an immediate anchor contradiction on the next decision callback, caught as `ExchangeConsistencyError` (`test_missing_or_contradictory_movement_evidence_rejected`).
   - Replay snapshot anchor mutations at tick boundaries are caught during tick-end reconciliation as `ExchangeConsistencyError` (`test_tick_end_replay_anchor_contradiction_rejected`).
5. **Exact Action Quota/Cost Accountability**:
   - Every SENSE, MOVE, WRITE, and READ action consumes exactly 1 action budget. Entrant exceeding `action_budget` per tick is rejected (`test_action_budget_quota_exceeded_rejected`).
   - Replay snapshot `cpu_used` must reconcile with decision action count (`test_incorrect_sensing_action_cost_rejected`).
6. **Cumulative Memory Write Reconciliation**:
   - Replay snapshot `mem_writes` is cumulative across match ticks and must reconcile with cumulative trace writes (`test_step7_failed_write_causes_not_verified`).
7. **Modular Arena Boundary Wrapping**:
   - Circular spatial window and movement correctly wrap modulo arena size across address 0 (`test_modular_boundary_wrapping_sensing_reconstruction`).

---

## 5. Negative Adversarial Test Results

The test suite exercises 20 distinct failure, mutation, and corruption modes across all 10 M1 contract areas:

| Test Case | Tampered Evidence | Expected Exception | Result |
|---|---|---|---|
| `test_missing_and_corrupted_artifacts` | Missing or malformed demo, replay, or trace files | `ArtifactIntegrityError` ("not found" / "Malformed") | Passed |
| `test_path_traversal_in_demo_artifacts_rejected` | Relative path traversal (`../secret.jsonl`) | `ArtifactIntegrityError` ("not found or unsafe") | Passed |
| `test_digest_and_binding_tampering_rejected` | Mutated replay/trace files or bindings | `ArtifactIntegrityError` ("Digest mismatch" / "binding") | Passed |
| `test_false_demo_sidecar_assertions_rejected` | False ruleset ID or arena size in demo metadata | `ArtifactIntegrityError` ("contradicts replay") | Passed |
| `test_tampered_sensing_sample_rejected` | Sensed sample mutated from `[91]` to `[99]` | `ExchangeReconstructionError` ("trace recorded sensed_anchors .* but independent reconstruction derived") | Passed |
| `test_receipt_before_eligible_delivery_rejected` | Injected receipt on callback 1 before SENSE | `ExchangeReconstructionError` ("unexpected previous_sense_anchors .* when no delivery was pending") | Passed |
| `test_dropped_receipt_rejected` | Dropped owed receipt on callback 2 | `ExchangeReconstructionError` ("expected sensing delivery .* but previous_sense_anchors was ABSENT") | Passed |
| `test_receipt_refreshed_with_future_opponent_state_rejected` | Opponent moves 91->99; receipt refreshed to 99 | `ExchangeReconstructionError` ("delivered previous_sense_anchors .* does not match sampled anchors") | Passed |
| `test_missing_or_contradictory_movement_evidence_rejected` | Mutated move operand from 64 to 10 in trace | `ExchangeConsistencyError` ("observation self_anchor is 64 but reconstructed anchor is 10") | Passed |
| `test_tick_end_replay_anchor_contradiction_rejected` | Mutated tick 1 process anchor in replay snapshot | `ExchangeConsistencyError` ("reconstructed anchor .* does not match replay anchor") | Passed |
| `test_passive_enemy_visibility_in_active_ruleset_rejected` | Injected passive enemy visibility `[91]` into trace | `ExchangeReconstructionError` ("active sensing forbids passive enemy visibility") | Passed |
| `test_incorrect_sensing_action_cost_rejected` | Mutated replay snapshot `cpu_used` to 7 instead of 8 | `ExchangeConsistencyError` ("entrant A replay cpu_used 7 does not match trace actions count 8") | Passed |
| `test_action_budget_quota_exceeded_rejected` | Injected 9th action for entrant in single tick | `ExchangeReconstructionError` ("action budget exceeded for entrant A: 9 > 8") | Passed |
| `test_impossible_action_ordering_rejected` | Swapped decisions across ticks (non-monotonic) | `ExchangeConsistencyError` ("Impossible action ordering") | Passed |
| `test_delayed_receipt_delivery_rejected` | Receipt skipped on callback 2 and delivered on callback 3 | `ExchangeReconstructionError` ("expected sensing delivery .* but previous_sense_anchors was ABSENT") | Passed |
| `test_illegal_operands_and_values_rejected` | SENSE with boolean or non-integer operand | `ExchangeReconstructionError` ("SENSE requires integer operand") | Passed |
| `test_missing_required_result_artifact_rejected` | Demonstration missing `result.json` or result entry | `ArtifactIntegrityError` ("not found" / "missing required entry for 'result'") | Passed |
| `test_false_demo_config_and_identity_assertions_rejected` | False `result_id`, `arena_size`, or entrants | `ArtifactIntegrityError` ("contradicts demo result_id" / "contradicts replay") | Passed |
| `test_false_demo_narrative_teaching_assertions_rejected` | Demo claims `sequence_verified=True` when sequence not verified | `ExchangeReconstructionError` ("claims sequence_verified=True, but independent reconstruction failed") | Passed |
| `test_step7_failed_write_causes_not_verified` | Later WRITE(91) attempted but rejected | Reports `VerificationStatus.NOT_VERIFIED` on Step 7 | Passed |
| `test_backward_compatibility_non_active_ruleset_rejected` | Reconstructing match from passive ruleset (`bytefray-rules-4`) | `ExchangeReconstructionError` ("requires an active sensing ruleset") | Passed |

---

## 6. Strict Research Isolation and Non-Claim

- **No Research Code Imports**: Zero imports from `tools.research`, E8, or E9 infrastructure.
- **Import Interception Verification**: Verified via `test_research_isolation_and_negative_imports` under runtime monkeypatched interceptor blocking any import of `tools.research`, `e9`, or `e8`.
- **No G Entropy Consumption**: Zero calls to `AuthorityLog.consume_generation` or G pools.
- **No Research Authority Records**: Emits only product-level playback data structures.
- **Sealed Historical Immutability**: Zero modifications to historical files.
- **Integrity Scope**: Artifact integrity checking detects inconsistency, corruption, and drift between artifacts; mutable un-signed `demo.json` sidecars are not cryptographically tamper-proof against deliberate malicious filesystem forgery.

---

## 7. Verification Record

All validation gates have completed with clean passes:

1. **Focused M1-3 Test Suite**:
   `python -m pytest engine/tests/test_v6_alpha_m1_3_sensing_playback.py`
   -> **27 passed in 2.87s**
2. **Prior M1 and Historical Equivalence Test Suites**:
   `python -m pytest engine/tests/test_v6_alpha_m1_2_window_scout.py engine/tests/test_v6_alpha_m1_policy_capabilities.py engine/tests/test_v4_historical_immutability.py engine/tests/test_v4_stable_ruleset_equivalence.py`
   -> **93 passed in 7.72s**
3. **Ruff Linter**:
   `python -m ruff check engine/src/battle_engine/sensing_playback.py engine/tests/test_v6_alpha_m1_3_sensing_playback.py`
   -> **All checks passed!**
4. **Mypy Static Typing (Battle Engine)**:
   `python -m mypy engine/src/battle_engine`
   -> **Success: no issues found in 102 source files**
5. **Mypy Static Typing (Battle Client)**:
   `python -m mypy client/src/battle_client`
   -> **Success: no issues found in 16 source files**
6. **CLI Entrypoint Smoke**:
   `python -m battle_engine.sensing_playback <demo_dir>` -> **Exit 0, Verified: True**
   `python -m battle_engine.sensing_playback <corrupt_dir>` -> **Exit 1, Verification failed**
   `python -m battle_engine.sensing_playback` -> **Exit 2, Error: target required**

---

## 8. Staging Manifest

The following files constitute the exact set of newly created files under Milestone M1-3:

```text
engine/src/battle_engine/sensing_playback.py
engine/tests/test_v6_alpha_m1_3_sensing_playback.py
docs/v6/V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md
```

In accordance with Phase 0 stop conditions:
- **No files have been staged (`git add`)**.
- **No commits have been created (`git commit`)**.
- **No pushes have been made (`git push`)**.
- **Milestone M1-4 has not been started**.

---

## 9. Final Acceptance Review and Formal Closure (2026-10-11)

The project lead accepted the implementation report (§§1–8) for final review and
asked for two semantic boundaries and two scope conditions to be verified before
closure. §§1–8 are kept as submitted. Where this section differs from them, this
section supersedes them.

### 9.1 Check results

| Check | Result | Evidence |
|---|---|---|
| C1. An incomplete but internally consistent recording may pass artifact-integrity validation, but must not be classified as a completed teaching demonstration. | **CONFIRMED** (test evidence corrected, F-2) | `is_verified` requires steps 1–6 to be `VERIFIED`. `verify_demonstration` raises unless `is_verified`. A SENSE cut off by the tick limit gives steps 5–7 `NOT_PROVEN`. A digest-bound `move_step=32` demo passes `verify_demonstration_artifacts`, gives step 6 `NOT_VERIFIED`, is refused by `verify_demonstration`, and the CLI exits 1. |
| C2. The verifier distinguishes observable receipt-consistent movement from unprovable claims about the agent's motivation. | **CONFIRMED after correction F-1** | Step 6 now verifies only that a MOVE(+64) was applied on the callback whose observation carried the receipt, and that it reduced the distance to the delivered contact. Evidence records `receipt_available_at_decision` and `motivation_established: false`. |
| C3. The verifier does not use `demo.json` narrative assertions as authoritative evidence. | **CONFIRMED after correction F-3** | `teaching_exchange.sequence_verified`, `status`, entrant `drift_detected`/`capture_complete`, `config` and identifiers can only cause rejection. Removing or negating the narrative block and `status` leaves the verification identical to baseline (scratch probe, 2026-10-11). The evaluated entrant now comes from the digest-bound replay header. |
| C4. No M1-4 functionality was introduced. | **CONFIRMED** | There is no `client/` change, no `client/src/battle_client/sensing.py`, no phase cursor or knowledge view model, and no client import in either M1-3 file. The working-tree changes are only the three manifest files. |

### 9.2 Findings and corrections

All three corrections stay inside the two M1-3 code files. The scope froze at these three findings.

- **F-1 (HIGH) — step 6 overstated what the artifacts establish.**
  The step was reported as "informed by delivered observation". Its description ("toward delivered contact 91") was never checked, and its evidence carried a hard-coded `new_anchor: 64`.
  - *Reproduction:* a scripted entrant that never reads its observation, started at anchor 200, applies SENSE(91) and then MOVE(+64). The distance to contact 91 goes from 109 to 173, yet the original code reported step 6 `VERIFIED`, `new_anchor: 64` (actual: 264) and an overall `is_verified=True`.
  - *Correction:* step 6 derives `anchor_before`/`anchor_after` from the reconstructed world states and requires step 5 to be `VERIFIED` and the contact distance to decrease. It states explicitly that the artifacts do not establish the agent's reason for moving, per M1 Contract §F ("Arbitrary agents receive facts only; do not infer their intent").
  - The identifier `legal_move_informed` is kept. "Informed" means only that the receipt was present in the deciding observation.
  - *Regression test:* `test_step6_reports_receipt_consistent_movement_not_motivation`. An observation-ignoring script moving toward the contact verifies with `motivation_established: false`; the same script moving away does not verify.
- **F-2 (MEDIUM, test coverage) — the truncation test asserted nothing.**
  `test_truncated_sequence_reports_not_proven` ran `ticks=1`. That run produces a fully `VERIFIED` exchange, because the receipt, MOVE and WRITE all fall inside tick 1. Its only post-SENSE assertion was conditional and never executed.
  - *Correction:* the test was rewritten in place. A scripted SENSE(91) is now entrant A's eighth and last action under `max_ticks=1`. Reconstruction, including result association, succeeds; steps 5–7 are `NOT_PROVEN` and `is_verified` is false.
  - *Added test:* `test_consistent_recording_without_required_move_is_not_verified` covers the `demo.json` integrity path.
- **F-3 (MEDIUM) — `demo.json` entrant names selected the evaluated entrant.**
  The scout was chosen by `entrants[].name == "v6_window_scout"` in `demo.json`, which is unsigned and never checked against the digest-bound replay header that records the same names.
  - *Correction:* the scout comes from the replay header names, falling back to `A`. Any `demo.json` entrant name that contradicts the replay header raises `ArtifactIntegrityError`.
  - *Test changes:* the name-swap case moved into `test_false_demo_config_and_identity_assertions_rejected` (case 4). `test_false_demo_narrative_teaching_assertions_rejected` now places its false `sequence_verified=True` claim on a genuinely unverified (`move_step=32`) recording instead of relying on the name swap.

### 9.3 Recorded, not remediated

- **N-1 (NOTE):** the descriptions of steps 1, 2 and 7 say "Window Scout" even when a pair-mode reconstruction of an arbitrary match falls back to entrant `A`. This is an identity label only, with no motivation claim, and does not affect any status.
- **N-2 (NOTE):** CLI pair mode (`--replay`/`--trace`) prints "Reconstruction verified: True" and does not report a teaching status. It makes no teaching-demonstration claim. M1-4/M1-5 presentation should keep consistency verification and teaching verification visibly distinct.

N-1 and N-2 were corrected before commit at the lead's request; see §9.6.

### 9.4 Acceptance evidence (re-run after corrections, 2026-10-11)

All pytest runs used `-p no:cacheprovider` and a `--basetemp` outside the repository, so `.pytest-tmp/` was not cleared.

1. Focused M1-3 suite: **29 passed**. These are the 27 original tests (one rewritten in place, F-2) plus 2 added.
2. Prior M1 and historical-equivalence suites (same four modules as §7.2): **93 passed**.
3. `ruff check` on both M1-3 code files: **All checks passed!**
4. `mypy engine/src/battle_engine`: **Success: no issues found in 102 source files**.
5. `mypy client/src/battle_client`: **Success: no issues found in 16 source files**.
6. CLI smoke via `python -m battle_engine.sensing_playback`:
   - canonical demo: **exit 0**; step 6 reports anchor 0→64, distance 91→27, motivation not claimed;
   - consistent `move_step=32` demo: **exit 1**;
   - no arguments: **exit 2**.

### 9.5 Formal closure

- Milestone M1-3 is formally closed with corrections F-1 to F-3.
- The staging manifest in §8 is unchanged: the same three files, and no others.
- At closure only those three files are staged. No commit or push has been made, and M1-4 has not been started.

### 9.6 Final presentation corrections before commit (2026-10-11)

The lead accepted F-1 to F-3 and their corrections. The lead approved the stricter receipt-consistent movement check in step 6 (F-1) as a teaching-sequence certification criterion. It is not a general requirement for legal or strategically valid movement.

Before authorizing the local commit, the lead asked for N-1 and N-2 (§9.3) to be corrected. Both corrections stay inside the two M1-3 code files. Neither adds a schema or changes a step identifier, evidence key, status or exit code.

- **N-1 corrected — entrant identity in step descriptions.**
  - The VERIFIED descriptions of steps 1, 2 and 7 now name the evaluated entrant as `Entrant <id> (<replay-header name>)`, for example `Entrant A (v6_window_scout)`. They no longer hard-code "Window Scout".
  - The name comes from the digest-bound replay header, the same evidence that selects the evaluated entrant (F-3).
  - `evaluate_teaching_exchange` gained an optional keyword-only `scout_name` argument. Without it, the descriptions read `Entrant <id>`.
- **N-2 corrected — CLI pair-mode messaging.**
  - Pair mode (`--replay`/`--trace`) now prints `Artifact pair integrity and consistency verified: True` instead of `Reconstruction verified: True`.
  - That line is followed by `Teaching exchange: NOT CLAIMED (pair mode does not verify the complete teaching exchange; verify a demonstration directory or demo.json for that)`.
  - Exit codes are unchanged. Pair mode still exits 0 for a consistent pair, whether or not the pair contains a complete teaching exchange.
- **Test changes:**
  - Added `test_step_descriptions_name_evaluated_entrant_from_replay`. In the canonical demo, steps 1, 2 and 7 name `Entrant A (v6_window_scout)`. A scripted pair with no `v6_window_scout` entrant falls back to `Entrant A (fallback_a)`, and none of its step descriptions says "Window Scout". Both cases assert that the seven step identifiers are unchanged.
  - `test_cli_interface_positive_and_negative` now asserts the output lines of demonstration mode and pair mode.
  - `test_consistent_recording_without_required_move_is_not_verified` now also asserts that the `move_step=32` pair exits 0 in pair mode with `Teaching exchange: NOT CLAIMED`, while the same recording as a demonstration exits 1.
  - The `_scripted_pair` helper accepts a `write91` step.

Evidence, re-run after these corrections (2026-10-11, same pytest settings as §9.4):

1. Focused M1-3 suite: **30 passed**. These are the 29 tests of §9.4 plus 1 added.
2. Prior M1 and historical-equivalence suites (same four modules as §7.2): **93 passed**.
3. `ruff check` on both M1-3 code files: **All checks passed!**
4. `mypy engine/src/battle_engine`: **Success: no issues found in 102 source files**.
5. `mypy client/src/battle_client`: **Success: no issues found in 16 source files**.
6. `git diff --cached --check` on the restaged three-file manifest: **no whitespace errors**.
7. CLI smoke via `python -m battle_engine.sensing_playback`:
   - canonical demo: **exit 0**; steps 1, 2 and 7 name `Entrant A (v6_window_scout)`;
   - canonical pair mode: **exit 0**; prints `Teaching exchange: NOT CLAIMED`;
   - consistent `move_step=32` demo: **exit 1**;
   - consistent `move_step=32` pair mode: **exit 0**; prints `Teaching exchange: NOT CLAIMED`;
   - no arguments: **exit 2**.

The lead then authorized one local commit of the unchanged §8 three-file manifest. Nothing has been pushed, and M1-4 has not been started.
