# Bytefray V6 — Milestone M1-2 Implementation Record 01

**Document ID**: `docs/v6/V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md`
**Date**: 2026-10-10
**Milestone**: Bytefray V6 Phase 1, Milestone M1-2 (Window Scout Teaching Demonstration)
**Status**: FORMALLY CLOSED AND RATIFIED BY PROJECT LEAD (MILESTONE M1-2 COMPLETE)

---

## 1. Executive Summary and Authorization

Under Phase 0 M1 authorization and governed by the V6 Alpha M1 Contract ([`V6_ALPHA_M1_CONTRACT_01.md`](file:///d:/Projects/BATTLE2/docs/v6/V6_ALPHA_M1_CONTRACT_01.md)), Milestone M1-2 delivers the complete Window Scout active sensing teaching demonstration.

The implementation provides:
1. **Teaching starter agent (`v6_window_scout`)**: Demonstrates active spatial sensing under `bytefray-rules-6-alpha1`, requiring capability `sense`, consuming quota, awaiting delayed anonymous sample receipt, and executing informed movement and interaction, before completing target engagement and resuming periodic scouting cadence. Initial SENSE(91) is strictly determined by declared teaching behavior (`search_offset = 91`), independent of hidden opponent state or placement.
2. **Stationary teaching opponent fixture (`v6_stationary_opponent`)**: Deterministic fixture entrant placed at anchor 91, legally reading its own core at every callback.
3. **Bounded demonstration runner (`sensing_demo.py`)**: Executes the match using the native match service (`NativeMatchService`), enforces authorized product output paths via `validate_output_directory`, validates demonstration artifacts and provenance via `validate_sensing_demo_artifacts`, captures entrant revisions with Python-subset fingerprints, verifies runtime loaded initial and final fingerprints for drift detection, verifies the single-shot exchange trace sequence, and emits machine-checkable `demo.json` sidecar metadata.
4. **Starter registration and invariants**: Registered in `battle_engine.starters` (`STARTER_AGENT_NAMES` and `CURRENT_STARTER_DIGESTS`) with tree digest `9d8a90ff209c2a9f13d5f3615cc67923204a095fdde6de9e183ca4ef8be10ce7` while preserving existing starter ordering invariants.
5. **Comprehensive test suite (`test_v6_alpha_m1_2_window_scout.py`)**: 19 focused unit, regression, boundary, quota/cost, cadence resumption, drift rejection, empty-scan/different-location, artifact provenance validation, and deep research-isolation tests.

---

## 2. Deliverables Inventory

| Path | Category | Role |
|---|---|---|
| `engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.yaml` | Starter Agent | Manifest declaring API v2, `capabilities.required = ["sense"]`, parameters `search_interval` (1..16, default 4) and `move_step` (1..64, default 64). |
| `engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.py` | Starter Agent | Agent logic implementing SENSE -> receipt -> MOVE -> WRITE lifecycle without private/research dependencies. Resumes periodic cadence upon sequence completion. |
| `engine/src/battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.yaml` | Teaching Fixture | Manifest declaring API v2, stationary core reader fixture. |
| `engine/src/battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.py` | Teaching Fixture | Stationary agent logic reading `observation.own_core_base`. |
| `engine/src/battle_engine/starters.py` | Engine Registry | Registered `"v6_window_scout"` and its tree digest `9d8a90ff209c2a9f13d5f3615cc67923204a095fdde6de9e183ca4ef8be10ce7`. |
| `engine/src/battle_engine/sensing_demo.py` | Runner / CLI | Native orchestrator producing `replay.jsonl`, `trace.jsonl`, `result.json`, and `demo.json`. Provides `validate_output_directory` and `validate_sensing_demo_artifacts`. |
| `engine/tests/test_v6_alpha_m1_2_window_scout.py` | Test Suite | 19 automated tests verifying manifest, logic, preflight, exchange, determinism, boundaries, AC2 cost, cadence resumption, drift rejection, empty scan / different opponent location, provenance validation, and isolation. |
| `docs/v6/V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md` | Documentation | Authoritative M1-2 implementation record. |

---

## 3. Teaching Exchange Lifecycle Verification

Under `bytefray-rules-6-alpha1`, passive enemy visibility is empty (`observation.visible_enemy_anchor_addresses == ()`). Information must be actively acquired. The verified trace sequence proves the complete teaching lesson:

1. **Incomplete Information & Active Scan (Step 1)**:
   - Window Scout begins with no initial contacts (`previous_sense_anchors` absent, visible enemy set empty).
   - On callback 1, Window Scout requests `SENSE(91)` within its declared reach (128).
   - Action consumes 1 action quota; status is `APPLIED`.
   - Engine evaluates the spatial window (half-width 27 around 91) and records sampled anchors `(91,)` for delivery at the next callback.

2. **Delayed Anonymous Receipt & Informed Move (Steps 2 and 3)**:
   - On callback 2, Window Scout receives the delivered anonymous sample in `observation.previous_sense_anchors == (91,)`.
   - Contact contains addresses only (no entrant identity, health, or core state).
   - Window Scout computes the shortest modular displacement toward 91 and executes legal clamped `MOVE(+64)`.
   - Action consumes 1 action quota; anchor updates to 64.

3. **In-Reach Interaction & Single-Shot Expiry (Step 4)**:
   - On callback 3, Window Scout is at anchor 64. Circular distance to target 91 is 27 cells (within sensing window and reach).
   - The previous sensing receipt is verified absent from `observation` (confirming single-shot delivery, not continuing vision).
   - Window Scout executes legal in-reach `WRITE(91, value=0x42)`.
   - Target is cleared, allowing Window Scout to resume its scheduled periodic search windows at callback 5.

---

## 4. Contract Boundary 1: Declared Teaching Behavior vs Hidden Opponent State

To ensure that Window Scout never leaks or depends on hidden opponent state or seed reconstruction:
1. **Initial Action Independence**:
   - Window Scout's callback 1 scan target is computed purely from own state: `(observation.self_anchor + self.search_offset) % arena`.
   - With `self_anchor = 0` and declared parameter `search_offset = 91`, `scan_target` is 91.
   - It does not inspect seed, placement RNG, or opponent position.
2. **Opponent at Different Location / Empty Window**:
   - Verified via `test_window_scout_behavior_when_opponent_at_different_location_and_window_empty`: when the opponent is placed at anchor 200 (outside sensing window [64..118] around 91), Window Scout still requests `SENSE(91)` on callback 1.
   - Engine evaluates the window and returns empty contacts `sensed_anchors = []`.
   - Callback 2 delivers `observation.previous_sense_anchors = []`.
   - Because contacts are empty, Window Scout does not move to 91; it executes legal fallback `READ(own_core_base)`.
   - On callbacks 3 and 4, it continues fallback `READ`.
   - On callback 5 (`5 % 4 == 1`), it resumes its declared search cadence and requests `SENSE(91)`.
3. **Non-Zero Start Anchor Verification**:
   - When Window Scout is placed at start anchor 100 with opponent at anchor 300, callback 1 requests `SENSE(191)` (`(100 + 91) % 512`), receives empty contacts `[]`, remains at anchor 100, and executes fallback `READ(100)` on its own core. This proves scan target derivation is strictly modular offset logic with zero coupling to opponent position.
4. **Stale Contact vs Omniscient World State**:
   - Verified via `test_delayed_receipt_with_intermediate_opponent_movement`: when opponent moves from 91 to 99 between scan and receipt, the delivered sample remains 91, proving historical snapshot semantics.

---

## 5. Contract Boundary 2: Machine-Checkable Provenance and Artifact Hashes

Demonstration artifacts generated by `sensing_demo.py` conform to machine-checkable provenance and integrity requirements:
- `schema`: `"bytefray.sensing_demo"`
- `schema_version`: `1`
- `provenance`: `"product_teaching_demo"`
- `declared_product_fixture`: `true`
- `ruleset_id`: `"bytefray-rules-6-alpha1"`
- `artifacts`: Contains exact filenames and SHA-256 digests of `replay.jsonl`, `trace.jsonl`, and `result.json`.
- Entrants captured with full tree digests, Python-subset fingerprints (`local_python_subset_fingerprint`), revision IDs, and executed loaded initial and final runtime fingerprints with zero drift.
- **Verification Function**: `validate_sensing_demo_artifacts(demo_dir_or_file)` programmatically validates that `demo.json` contains the required provenance strings and flags, and that all artifact SHA-256 digests match the files on disk.
- **Inconsistency and Corruption Guards**: Rejects malformed JSON payloads (lists, scalars), non-dictionary artifact entries, invalid filenames, path traversal attempts (`..`), missing files, and disk byte corruption / inconsistency across replay, trace, and result artifacts. Verified via comprehensive automated test cases in `test_demonstration_artifacts_contain_and_validate_provenance`.
- **Integrity Scope and Non-Claim**: In accordance with the governing M1 Contract (`V6_ALPHA_M1_CONTRACT_01.md` §Knowledge Projection & Artifacts, lines 229–230: *"Binding/digests detect inconsistency, not malicious forgery"*), mutable SHA-256 sidecars (`demo.json`) provide machine-checkable artifact binding, drift detection, and inconsistency/corruption detection. Because `demo.json` is an un-signed, mutable on-disk metadata file, it is NOT cryptographically tamper-proof against deliberate malicious modification with filesystem write access.

---

## 6. Contract Boundary 3: Strict Research Isolation & Output Confinement

The implementation strictly enforces research isolation beyond import blocking, complying fully with adopted Phase 0 Condition C-2 and Acceptance Criterion AC11:
- **No Private E9 Seed Access**: Uses only public product seeds; no calls or references to E9 seed derivations or authority files.
- **No G Consumption**: Zero interaction with `AuthorityLog.consume_generation` or G entropy pools.
- **No Research Authority Events**: Generates only product records (`demo.json`, `replay`, `trace`, `result`); no research authority records, seals, or protocol freeze events are emitted.
- **Output Confinement & Path Enforcement (Condition C-2, AC11)**:
  - Demonstration runner strictly enforces authorized product paths via `validate_output_directory(output_dir)`.
  - Rejects empty or whitespace paths with `ValueError`.
  - Rejects all research directories and private research namespaces (`tools/research`, `docs/research`, and any path component matching `research`, `research_*`, `.pytest_e9_*`, `e9_*`).
  - Confines output strictly to authorized product paths: subdirectories under the repository product runs tree (`runs/<subdir>`), subdirectories under configured data root (`<data_root>/runs/<subdir>`), or legitimate test temporary directories (`.pytest-tmp/<subdir>` and OS `tempfile.gettempdir()/<subdir>`).
  - Prohibits writing directly to the bare root of `runs`, the project repository root, or bare temporary root directories (`.pytest-tmp`, OS `tempfile.gettempdir()`).
  - Prohibits writing into repository source/tool/doc trees (`engine/`, `client/`, `app/`, `_legacy/`, `tools/`, `docs/`, `assets/`, `.git/`).
  - Prohibits writing into protected product run roots (`runs/agents_test`, `runs/evaluations`, `runs/_designer`, `runs/_loose`) and historical run directories (`v0_*`, `v2_*`, `v3_*`, `v4_*`, `v5_*`).
  - Resolves symlinks and NTFS junctions to their canonical target (`Path.resolve()`) prior to evaluation, rejecting any junction or symlink escaping into protected directories.
  - Protects existing research and product artifacts from overwrite: if the target directory or any ancestor directory under `runs/` contains non-demonstration files or subdirectories, it is rejected with `ValueError`.
  - **Contract Authorization Status**: Phase 0 Condition C-2 explicitly restricts M1 execution to product paths (*"write only to product paths (e.g. `runs/v6_alpha_m1/`)"*). The contract does not authorize unconstrained user selection of output directories across arbitrary host filesystem paths. Any future expansion permitting arbitrary external output paths would require an explicit Lead Authorization Decision amending Condition C-2.
- **Runtime Import Guards**: Verified via `test_research_isolation_and_unauthorized_output_paths` under monkeypatched import interceptors blocking any `tools.research`, E8, or E9 references during full demonstration execution.
- **Artifact Isolation Checks**: All produced text artifacts (`demo.json`, `replay.jsonl`, `trace.jsonl`, `result.json`) are scanned to guarantee complete absence of authority event strings, G consumption markers, protocol freeze directives, and research directory/namespace tokens.

---

## 7. Quality and Verification Summary

All verification gates have passed:
1. **Focused M1-2 Test Suite**:
   `python -m pytest engine/tests/test_v6_alpha_m1_2_window_scout.py` -> **19 passed in 1.34s**.
2. **Broader Product & Starter Suite**:
   `python -m pytest engine/tests/test_v6_alpha_m1_2_window_scout.py engine/tests/test_v6_alpha_m1_policy_capabilities.py engine/tests/test_starter_agents.py engine/tests/test_v5_starter_agents.py engine/tests/test_v5_alpha1_phase_e_starter_refresh.py engine/tests/test_agent_scaffold.py engine/tests/test_windows_packaging_spec.py` -> **234 passed in 13.59s**.
3. **Starter Validity Suite**:
   `python -m pytest engine/tests/test_starter_directory_validity.py` -> **18 passed in 0.70s**.
4. **Ruff Lint Check**:
   `python -m ruff check engine/src/battle_engine/sensing_demo.py engine/src/battle_engine/starters.py engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.py engine/src/battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.py engine/tests/test_v6_alpha_m1_2_window_scout.py` -> **All checks passed!**
5. **Mypy Static Typing**:
   - `python -m mypy engine/src/battle_engine` -> **Success: no issues found in 101 source files**.
   - `python -m mypy client/src/battle_client` -> **Success: no issues found in 16 source files**.
6. **CLI Demonstration Smoke**:
   `python -m battle_engine.sensing_demo --output-dir .pytest-tmp/smoke_demo --ticks 10` -> **Exit 0, Verified: True**.
7. **CLI Rejection of Research Paths**:
   `python -m battle_engine.sensing_demo --output-dir tools/research/v6/e9/test --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing into research directory is prohibited**.
8. **CLI Rejection of Historical Research Runs**:
   `python -m battle_engine.sensing_demo --output-dir runs/research_v6_e8 --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing into research namespace or directory is prohibited**.
9. **CLI Rejection of Source Code Trees**:
   `python -m battle_engine.sensing_demo --output-dir engine/src/battle_engine --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing into repository tree outside runs/ is prohibited**.
10. **CLI Rejection of Bare Runs Root**:
    `python -m battle_engine.sensing_demo --output-dir runs --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing directly to root runs directory is prohibited**.
11. **CLI Rejection of Bare Temporary Root**:
    `python -m battle_engine.sensing_demo --output-dir .pytest-tmp --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing directly to root temporary directory is prohibited**.
12. **CLI Rejection of Historical Run Subdirectory**:
    `python -m battle_engine.sensing_demo --output-dir runs/v5_r4_lineage/leak --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing into historical run directory 'v5_r4_lineage' is prohibited**.
13. **CLI Rejection of Foreign Run Root**:
    `python -m battle_engine.sensing_demo --output-dir runs/evaluations/leak --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: writing into protected run root 'evaluations' is prohibited**.
14. **CLI Rejection of Empty Output Path**:
    `python -m battle_engine.sensing_demo --output-dir "" --ticks 10` -> **Exit 2, Demo failed: Unauthorized output path: output directory cannot be empty.**

---

## 8. Formal Project Lead Closure and Staging Manifest

On 2026-10-10, following independent review, verification of all three contract boundaries, hardening of output-directory containment, and full automated test suite pass (19 focused tests, 234 broader tests, 18 starter directory validity tests), the Bytefray Project Lead formally approved closure of Milestone M1-2: Window Scout Teaching Demonstration.

**The Project Lead hereby declares Milestone M1-2 formally CLOSED.**

- Boundary 1 (Window Scout declared behavior and empty window): **VERIFIED AND CLOSED**.
- Boundary 2 (Machine-checkable provenance and SHA-256 digests): **VERIFIED AND CLOSED**.
- Boundary 3 (Research isolation and output directory containment): **VERIFIED AND CLOSED**.
- Research Execution Lock & Historical Source Integrity: **PRESERVED**.

### Exact Staging Manifest

```text
# Authorized M1-2 deliverable set (8 files/directories):
engine/src/battle_engine/starters.py
engine/src/battle_engine/sensing_demo.py
engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.yaml
engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.py
engine/src/battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.yaml
engine/src/battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.py
engine/tests/test_v6_alpha_m1_2_window_scout.py
docs/v6/V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md

# Strictly EXCLUDED from staging (Research lock preserved):
.pytest_e9_identity_q_t_20261008_01/
docs/research/v6/
tools/research/v6/e9/
```
