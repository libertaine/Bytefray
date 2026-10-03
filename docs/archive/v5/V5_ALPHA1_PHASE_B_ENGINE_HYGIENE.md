# Bytefray V5 Alpha 1 — Phase B: Production Engine Hygiene & Rejected-Experiment Isolation

**Date**: 2026-09-08 / 2026-09-09  
**Branch**: `v5-research`  
**Status**: COMPLETE  
**Prior Phase**: Phase A — Research Consolidation & Product Boundary (`docs/research/v5/V5_ALPHA1_CONSOLIDATION_AND_PLAN.md`)  
**Next Phase**: Phase C — Starter Agent Population Redesign  

---

## 1. Executive Summary

Phase B is the first implementation phase of Bytefray V5 Alpha 1. Guided by the conclusions of the V5 research program (R0 through R4) and the Phase A product consolidation plan, Phase B restores complete production engine hygiene by:

1. **Purging Rejected Experiments from Production Surfaces**: Completely removing the evaluated-and-rejected experimental rulesets (`bytefray-rules-5-r1-alpha1`, `bytefray-rules-5-r2-alpha1`), process mortality mechanics (`process_integrity`, `has_process_mortality`, `died_tick`), and the diagnostic target oracle (`objective_target_oracle`, `has_objective_target_oracle`) from all production execution, request, runtime, and policy paths.
2. **Preserving Stable V4 Gameplay Semantics**: Ensuring stable `bytefray-rules-4` remains the canonical, default-resolving gameplay standard for Agent API v2 entrants, passing the 167-test equivalence gate bit-for-bit.
3. **Preserving Replay Compatibility**: Enforcing clean 5-field process serialization (`process_id`, `entrant_id`, `anchor`, `disrupted`, `reach`) for all current and future matches, while maintaining tolerant passive deserialization for historical research replay files that carry `alive` or `integrity`.
4. **Preserving Durable Measurement Assets**: Keeping the refined simultaneous core-deficit tracking and VM run-length diff expansions in `tools/research/v5/analyzer.py` along with their unit tests.
5. **Archiving Historical Research Artifacts**: Documenting historical execution harnesses (`r1_runner.py`, `r2_runner.py`) with explicit notices identifying historical git commits (`18e5ac6` for R1, `26e0816` for R2) required for re-execution.
6. **Executing Version Transition**: Updating project metadata across `pyproject.toml`, `tools/installer.iss`, and the editable environment to `5.0.0a1`.
7. **Full Verification**: Qualifying the updated codebase against the full 3,052-test pytest suite (0 failures), 0 ruff errors, and 0 mypy errors across both engine and client packages.

---

## 2. Precise Inventory of Removed Experimental Symbols

### 2.1 Rules & Policies
- **`engine/src/battle_engine/rules.py`**:
  - Removed `BYTEFRAY_RULESET_V5_R1_ALPHA1_ID`
  - Removed `BYTEFRAY_RULESET_V5_R2_ALPHA1_ID`
  - Removed corresponding exports from `__all__`
- **`engine/src/battle_engine/ruleset_policy.py`**:
  - Removed `RULESET_V5_R1_ALPHA1` policy definition
  - Removed `RULESET_V5_R2_ALPHA1` policy definition
  - Removed both ruleset IDs from `PROCESS_RULESET_IDS`
  - Removed both policies from `_RULESET_POLICIES`
  - Removed corresponding exports from `__all__`

### 2.2 Request & Match Service
- **`engine/src/battle_engine/match_service.py`**:
  - Removed imports of `DEFAULT_PROCESS_INTEGRITY`, `has_objective_target_oracle`, `has_process_mortality` from `process_runtime`
  - Removed `MatchRequest.process_integrity: int | None = None`
  - Removed `MatchRequest.objective_target_oracle: bool = False`
  - Removed `_resolve_process_integrity` helper
  - Removed `_resolve_objective_target_oracle` helper
  - Removed injection of `process_integrity` and `objective_target_oracle` into `_reproducibility` replay metadata
  - Removed `process_integrity` and `objective_target_oracle` arguments from `ProcessMatchController.from_python_entrants` invocation
  - Removed experimental process summary metadata (`alive`, `integrity_remaining`, `died_tick`) from `_build_process_result`

### 2.3 Process Runtime
- **`engine/src/battle_engine/process_runtime.py`**:
  - Removed `PROCESS_MORTALITY_RULESET_IDS` frozenset
  - Removed `DEFAULT_PROCESS_INTEGRITY = 8`
  - Removed `has_process_mortality(ruleset_id: str) -> bool`
  - Removed `OBJECTIVE_TARGET_ORACLE_RULESET_IDS` frozenset
  - Removed `has_objective_target_oracle(ruleset_id: str) -> bool`
  - Removed `ProcessTelemetry.died_tick: int | None = None`
  - Removed `ProcessInstance.alive` and `ProcessInstance.integrity`
  - Removed `process_integrity` and `objective_target_oracle` parameters from `ProcessMatchController.from_python_entrants`
  - Removed `process_integrity` and `objective_target_oracle` parameters and fields from `ProcessMatchController.__init__` (`self.mortality_active`, `self.oracle_active`, `self.process_integrity`)
  - Removed oracle target injection block in `_visible_enemy_anchors` (sensor visibility returns strictly circular-distance-detected living enemy process anchors)
  - Cleaned `_effective_process_quotas` to check eligibility solely via `not p.is_disrupted(tick)`
  - Restored clean `_process_snapshots` emitting strictly 5 canonical fields
  - Removed mortality integrity decrement and process kill logic from hostile applied write handler
  - Removed mortality fields from `proc_stats` summary construction

### 2.4 Replay Serialization
- **`engine/src/battle_engine/replay.py`**:
  - Restored clean 5-field dictionary emission in `_process_to_dict` (`process_id`, `entrant_id`, `anchor`, `disrupted`, `reach`), omitting `alive` and `integrity` from serialization
  - Retained tolerant passive ingestion in `_process_from_dict` for historical research replays

---

## 3. Preserved Architecture & Durable Invariants

### 3.1 Stable V4 Gameplay
- Canonical ruleset identity: `bytefray-rules-4` (`RULESET_V4`).
- Automatic resolution: Omitted `--ruleset` continues resolving to `bytefray-rules-4` for all Agent API v2 entrants.
- Frozen historical rulesets: `bytefray-rules-4-alpha1` and `bytefray-rules-4-alpha2` remain explicitly selectable and frozen.
- Equivalence: `test_v4_stable_ruleset_equivalence.py` confirms that `bytefray-rules-4` is bit-for-bit identical to alpha2 in core placement, process selection (round-robin), and match outcome.

### 3.2 Durable Measurement Infrastructure
- **`tools/research/v5/analyzer.py`**:
  - Retained true simultaneous core-deficit tracking (`max_core_deficit`, `core_deficit_series`, `full_core_return_count`, `repair_latencies_ticks`, `longest_damaged_interval_ticks`, `deficit_ever_reached_full`).
  - Retained multi-cell run-length expanded `MemoryDiff` handling.
- **`engine/tests/test_v5_research_r1_metrics.py`**:
  - Retained `test_damage_repair_cycle_does_not_misreport_as_accumulating_progress`
  - Retained `test_true_ownership_expands_merged_run_length_diffs`

### 3.3 Historical Research Harnesses
- **`tools/research/v5/r1_runner.py`** & **`tools/research/v5/r2_runner.py`**:
  - Marked with top-of-file historical notice headers.
  - Decoupled from production modules (`battle_engine.rules` imports replaced with local historical string constants).
  - Explicit instructions provided for checking out historical commits (`18e5ac6` for R1, `26e0816` for R2) to reproduce research benchmarks.

---

## 4. Test Suite Adjustments & Additions

### 4.1 Obsolete Tests Removed
- `engine/tests/test_process_mortality.py` (399 lines deleted): Tested finite process mortality and `BYTEFRAY_RULESET_V5_R1_ALPHA1_ID`. Preserved in Git history at commit `18e5ac6`.
- `engine/tests/test_objective_target_oracle.py` (697 lines deleted): Tested target oracle mechanic and `BYTEFRAY_RULESET_V5_R2_ALPHA1_ID`. Preserved in Git history at commit `26e0816`.
- `engine/tests/test_v5_research_r2_metrics.py` (201 lines deleted): Tested follow-through metrics under rejected ruleset and oracle configurations. Preserved in Git history at commit `26e0816`.
- Mortality-specific tests in `engine/tests/test_v5_research_r1_metrics.py` (128 lines pruned): Removed tests requiring `RULESET_V5_R1_ALPHA1` and `process_integrity`.

### 4.2 New Hygiene Test Suite Added
- **`engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py`** (8 comprehensive test functions):
  1. `test_rejected_rulesets_not_recognized_in_production`: Verifies `UnknownRulesetError` on `bytefray-rules-5-r1-alpha1`, `bytefray-rules-5-r2-alpha1`, `bytefray-rules-5`, and absence from `PROCESS_RULESET_IDS`.
  2. `test_stable_v4_ruleset_functional_and_default`: Verifies `BYTEFRAY_RULESET_V4_ID` registration and default resolution via `resolve_omitted_ruleset_for_agents`.
  3. `test_match_request_rejects_experimental_kwargs`: Verifies `TypeError` when `process_integrity` or `objective_target_oracle` is supplied to `MatchRequest`.
  4. `test_process_match_controller_rejects_experimental_kwargs`: Verifies `TypeError` on `from_python_entrants` and verifies controller and process instances lack experimental attributes (`mortality_active`, `oracle_active`, `process_integrity`, `died_tick`).
  5. `test_no_oracle_leak_in_visible_enemy_anchor_addresses`: Verifies out-of-reach enemy cores never leak into `visible_enemy_anchor_addresses`.
  6. `test_replay_serialization_canonical_fields_only`: Verifies that `_process_to_dict` emits strictly the 5 canonical fields (`process_id`, `entrant_id`, `anchor`, `disrupted`, `reach`).
  7. `test_replay_deserialization_passive_compatibility`: Verifies that `_process_from_dict` gracefully parses historical replays containing `alive` or `integrity`.
  8. `test_version_transition_5_0_0a1`: Verifies consistent versioning across `pyproject.toml`, `installer.iss`, and package distribution metadata.

---

## 5. Version Transition

- `pyproject.toml`: Updated to `version = "5.0.0a1"`.
- `tools/installer.iss`: Synchronized `#define AppVersion "5.0.0a1"` and `#define ReleaseTag "5.0.0a1"`.
- Installed package metadata in virtual environment updated to `5.0.0a1` via `pip install -e . --no-deps`.
- Qualified by `engine/tests/test_windows_packaging_spec.py` (17/17 passed).

---

## 6. Verification Results

| Verification Suite | Target Scope | Command | Result |
|---|---|---|---|
| **Phase B Hygiene** | Rejection, API, observation, replay, version | `pytest engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py` | **8 passed** (0.23s) |
| **Packaging Specs** | Installer version synchronization | `pytest engine/tests/test_windows_packaging_spec.py` | **17 passed** (0.16s) |
| **V4 Equivalence Gate** | Stable ruleset equivalence & placement | `pytest engine/tests/test_v4_stable_ruleset_equivalence.py engine/tests/test_v4_alpha2_placement.py engine/tests/test_v4_alpha2_scheduler.py engine/tests/test_v4_runtime_default_ruleset.py engine/tests/test_ruleset_policy.py` | **167 passed** (13.54s) |
| **Durable Core Deficit** | Measurement invariants & run-length diffs | `pytest engine/tests/test_v5_research_r1_metrics.py` | **2 passed** (9.50s) |
| **Lint Check** | Repository-wide formatting & imports | `ruff check .` | **All checks passed!** (0 errors) |
| **Engine Type-Check** | Simulation core and CLI types | `mypy engine/src/battle_engine` | **Success (102 files)** (0 errors) |
| **Client Type-Check** | Replay client and renderers | `mypy client/src/battle_client` | **Success (16 files)** (0 errors) |
| **Full Pytest Suite** | Repository test suites | `python -m pytest` | **3,052 passed, 14 skipped, 3 deselected** (0 failures, 7m 30s) |

---

## 7. Working Tree & Git Hygiene

- Working tree modifications are strictly confined to the targeted files:
  - `engine/src/battle_engine/match_service.py`
  - `engine/src/battle_engine/process_runtime.py`
  - `engine/src/battle_engine/replay.py`
  - `engine/src/battle_engine/rules.py`
  - `engine/src/battle_engine/ruleset_policy.py`
  - `engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py` [NEW]
  - `engine/tests/test_v5_research_r1_metrics.py`
  - `pyproject.toml`
  - `tools/installer.iss`
  - `tools/research/v5/corpus_runner.py`
  - `tools/research/v5/r1_runner.py`
  - `tools/research/v5/r2_runner.py`
  - `docs/research/v5/V5_ALPHA1_PHASE_B_ENGINE_HYGIENE.md` [NEW]
- Obsolete test files cleanly deleted from working tree:
  - `engine/tests/test_objective_target_oracle.py`
  - `engine/tests/test_process_mortality.py`
  - `engine/tests/test_v5_research_r2_metrics.py`
- Git safety invariants preserved:
  - No mutating git commands executed (`git add`, `git commit`, `git push`, etc. were NOT called).
  - Git index lock `.git/index.lock` is absent (`False`).
  - Index length is healthy (`89799` bytes).

---

## 8. Next Step: Phase C (Starter Agent Population Redesign)

With the engine restored to clean, stable `bytefray-rules-4` execution, V5 Alpha 1 moves to **Phase C: Starter Agent Population Redesign**.

Phase C will focus on:
1. Translating the architectural insights from the R3/R4 research agents (`v5r3_region_sweeper`, `v5r4_recon_striker`, `v5r4_siege_regional`, `v5r4_core_warden`) into production-grade starter agents under `agents/`.
2. Replacing incompetent legacy single-cell campers with agents that demonstrate genuine spatial maneuver, defensive patrol, and objective pressure under stable V4 mechanics.
3. Ensuring starter agents comply with Agent API v2 and provide transparent reference implementations for users.

