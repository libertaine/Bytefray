# Bytefray 5.1 Pre-RC Remediation 01 — Unsafe Spectator Export Replacement

**Task ID:** P1 Remediation 01

**Affected Component:** `client/src/battle_client/spectator_export.py` (`bytefray spectator export --replace` / `export_presentation(..., replace_existing=True)`)

**Remediation Worktree:** `D:\Projects\BATTLE2-worktrees\p1-remediation-01-spectator-replace`

**Remediation Branch:** `v6-p1-remediation-01-spectator-replace`

**Base Commit:** `08638463fdb3c655892a44c494c860af14005786` (`0863846`, on `v6-m2-5-identity-integration`)

**Independent Review Status:** Initial conversation review returned **HOLD** with three findings. Corrections, required verification and focused current-model review are complete: **PASS WITH CONDITIONS — no remaining blocking defects** within P1 Remediation 01. On 2026-10-19 the project lead waived the separate Gemini Argon handoff and assigned review to the current model; no separate independent approval is claimed.

---

## 1. Root Cause Analysis

In `client/src/battle_client/spectator_export.py` at base commit `0863846`, `_is_presentation_dir(path)` (`lines 715-718`) implemented only a 3-line filename-subset check:

```python
def _is_presentation_dir(path: Path) -> bool:
    names = {entry.name for entry in path.iterdir()}
    allowed = {MANIFEST_FILENAME, *PRESENTATION_FILES.values()}
    return names <= allowed and all((path / name).is_file() for name in names)
```

When `export_presentation(source, out_dir, replace_existing=True)` (`bytefray spectator export --replace`) was invoked against an existing directory:

1. `_check_output` (`lines 721-738`) accepted any non-empty directory whose entry names were a subset of `{"manifest.json", "broadcast.json", "agent_a.json"}` without verifying that all three required files were present, that `manifest.json` was a valid Bytefray Spectator manifest (`bytefray.spectator.manifest` v2), or that the presentation documents matched their recorded sizes and SHA-256 digests.
2. `export_presentation` (`line 788`) called `Path(out_dir).expanduser().resolve()` before checking for symlinks, Windows junctions, or reparse points, allowing link traversal on `out_dir`.
3. `_check_output` only checked canonical separation against `(result_path.parent,)` rather than both lexical and canonical separation across `source`, `result.json`, `replay.jsonl`, and `trace.jsonl`.
4. `_install` (`lines 750-771`) moved `out_dir` to `aside`, re-ran the weak `_is_presentation_dir(aside)` filename check, and called `shutil.rmtree(aside, ignore_errors=True)` (`line 768`), permanently deleting unrelated user files whenever their filenames were a subset of `{"manifest.json", "broadcast.json", "agent_a.json"}`.

By contrast, the earlier P1 cache-pruning remediation (`d0dc955`) had hardened `_cache_owned(path, key)` (`lines 924-950`) for Designer's cache directory, but left `_is_presentation_dir(path)` and `_install` on the `export --replace` path using the original filename-subset check.

---

## 2. Corrective Design

A minimal, fail-closed replacement policy was implemented in `client/src/battle_client/spectator_export.py`:

### A. Positive Destination Verification (`_is_presentation_dir` & `verify_presentation`)

- `_is_presentation_dir(path)` now requires:
  1. `_is_real_dir(path)`: `path` exists, is a directory, and is not a symbolic link, Windows junction, or reparse point (`stat.S_ISLNK` and `stat.FILE_ATTRIBUTE_REPARSE_POINT` via `lstat()`).
  2. Exact closed file-set equality: `{entry.name for entry in path.iterdir()} == PRESENTATION_DIR_FILES` (`frozenset({"manifest.json", "broadcast.json", "agent_a.json"})`). Missing required documents, extra files, dotfiles (including `.bytefray-spectator-cache.json`), or subdirectories immediately disqualify the directory.
  3. Every member in `PRESENTATION_DIR_FILES` must satisfy `_is_regular_file(path / name)` (existing regular file, not a symlink/junction/reparse point via `lstat()`).
  4. Full `verify_presentation(path)` validation must succeed.
- `verify_presentation(directory, ...)` was strengthened to enforce:
  - Regular non-link directory and regular non-link files (`manifest.json`, `broadcast.json`, `agent_a.json`).
  - Exact top-level manifest key set (`MANIFEST_KEYS`), schema `("bytefray.spectator.manifest", 2)` (rejecting v1 and unknown schemas), and exporter identity `{"name": "battle_client.spectator_export", "version": int >= 1}`.
  - Structural validity of `bytefray`, `match` (`MATCH_KEYS`), and `sources` (3 source records including `result.json` and `trace.jsonl` with 64-hex SHA-256 and positive integer byte counts).
  - Exact `verification` key set (`VERIFICATION_KEYS`), `provenance == "bytefray_match"`, all 6 verification flags `is True`, and integer `tick_end_boundaries_checked >= 1` matching the actual count of `TICK_END` frames in `broadcast.json`.
  - Exact `presentation` entry key set (`PRESENTATION_ENTRY_KEYS`), document schema/version bindings, exact byte-size and SHA-256 digest matches for `broadcast.json` and `agent_a.json`, frame count equality, and `check_agent_allowlist` on `agent_a.json`.

### B. Path, Link, and Source Separation Safety (`_reject_link_path`, `_check_separation`, `_source_directories`)

- `_reject_link_path(out_dir)` walks both the un-collapsed lexical path components and the `os.path.abspath`-normalized ancestors of `out_dir` using `os.path.lexists` and `_is_link` (`lstat()`), refusing with `OUTPUT_UNSAFE` before `.resolve()` can follow any symlink, Windows junction, or reparse point at `out_dir` or along its path.
- `_source_directories(source, verified)` collects the lexical source directory and the lexical and strictly resolved parent directories of every preflight-verified result, replay and trace artifact. Resolution failures return `output_unsafe` before staging. This includes the independently corrected trace target described in section 7.
- `_check_separation(target, source_dirs)` enforces 4-way disjointness (lexical-lexical, canonical-canonical, lexical-canonical, canonical-lexical) so neither direct overlaps nor symlink/junction aliases nor split replay directories can overlap `out_dir`.

### C. Safe Staging Verification and Non-Recursive Installation (`_export_into`, `_install`, `_remove_verified_aside`)

- `_export_into` now runs `verify_presentation(staging, sources=before, require_current_exporter=True)` immediately after `_write_presentation(staging, before, documents)`, ensuring staged output is completely verified before `out_dir` is touched.
- `_install(staging, out_dir, *, replace_existing=True)` verifies `_reject_link_path(out_dir)` and `_is_presentation_dir(staging)` before touching `out_dir`.
- When `out_dir` exists, `_install` verifies it is either an empty real directory or (when `replace_existing=True`) a verified presentation directory before moving it to `aside`, re-verifies `aside` after the rename, attempts restoration of `aside` to `out_dir` if eligibility or installation fails, and removes `aside` only after successful installation via `_remove_verified_aside` — which unlinks only the three verified regular files in `PRESENTATION_DIR_FILES` and calls `aside.rmdir()` (never `shutil.rmtree`).

---

## 3. Before / After Reproduction Summary (Disposable Synthetic Data Only)

### Before Remediation (at `0863846`)

A disposable temporary directory containing a synthetic 20-tick V6 match (`match/`) and a synthetic user directory (`unrelated_user_dir/`) holding only `manifest.json` (`sha256: ac0385570350b518b2fa8876e088956e0fef211e48b0c6fc9fc892a5eece5638`) and `agent_a.json` (`sha256: 5c370e198a2d478b73eae793bb0c796c826090fe17eae276d9088342f567404d`) was tested with:

```text
sx.main(['export', '--source', str(match_dir), '--out', str(victim), '--replace'])
```

Observed result on `0863846`:
- `EXIT_CODE: 0`
- `USER_MANIFEST_SURVIVED: False`
- `USER_AGENT_A_SURVIVED: False`
- Both user files were permanently deleted and overwritten with a 3-file Spectator presentation.

### After Remediation

Running the identical disposable synthetic reproduction against the remediated `spectator_export.py`:

```text
spectator export failed (output_unsafe): ...\unrelated_user_dir holds files that are not a Spectator presentation
BEFORE: {'agent_a.json': 'be404846e3be512e5f486850d9f2551117176b5974d6aed3aa2f58e9bbe4f5aa', 'manifest.json': 'f9080719153053c417ae1713d6f3d5298f9b41d0dfc29b7428f874205f68f18a'}
EXIT_CODE: 1
AFTER:  {'agent_a.json': 'be404846e3be512e5f486850d9f2551117176b5974d6aed3aa2f58e9bbe4f5aa', 'manifest.json': 'f9080719153053c417ae1713d6f3d5298f9b41d0dfc29b7428f874205f68f18a'}
USER_MANIFEST_SURVIVED: True
USER_AGENT_A_SURVIVED: True
LEFTOVERS: []
```

---

## 4. Historical Test Evidence — Initial Remediation

### A. Focused Bytefray Suites

1. `client/tests/test_spectator_export.py` + `engine/tests/test_spectator_viewer_service.py` + `engine/tests/test_command.py` + `engine/tests/test_component_identity.py` + `engine/tests/test_release_compatibility_record.py`:
   - **Result:** `239 passed, 1 skipped` (exit code `0`; the single skip is the POSIX-only `chmod` test on Windows in `test_spectator_viewer_service.py`).
   - Includes `client/tests/test_spectator_export.py` (`121 passed`), covering all 14 required positive and adversarial replacement scenarios:
     1. Valid new export into non-existent directory.
     2. Valid export into empty directory.
     3. Valid `--replace` of a real, unmodified exported presentation (API and CLI).
     4. Refusal of the original reproduction directory (`manifest.json` + `agent_a.json` with arbitrary content).
     5. Refusal when all three presentation filenames exist with arbitrary, corrupted, or forged content (`10` parametrized variants).
     6. Refusal when any required presentation document (`manifest.json`, `broadcast.json`, `agent_a.json`) is missing.
     7. Refusal when any presentation document hash or byte size mismatches the manifest (`4` parametrized variants).
     8. Refusal when an extra file, hidden dotfile, cache owner marker, empty subdirectory, or populated subdirectory is present alongside a valid presentation (`5` parametrized variants).
     9. Refusal when manifest schema or schema version is unsupported, including v1 (`("bytefray.spectator.manifest", 1)`).
     10. Refusal when target, parent, child, or contained presentation file is a symlink, Windows junction, or reparse point.
     11. Refusal when target overlaps the source match directory, parent, child, canonical junction alias, or split replay/trace directory.
     12. Refusal when `--replace` is omitted for an existing valid presentation.
     13. Simulated staging write `OSError`, corrupted staged output, and `_install` `os.replace` failure during `--replace`, verifying the original valid presentation remains intact with zero leftovers.
     14. Normal Designer `prepare_presentation` cache workflow reuse and owned-entry pruning.
2. `tests/test_agent_designer_spectator.py -m gui`:
   - **Result:** `10 passed in 7.52s` (exit code `0`).

### B. Cross-Repository Spectator Verification

Executed from `D:\Projects\Bytefray-Spectator-integration-20261017\spectator` (`14089a7`) with:
- `BYTEFRAY_PRODUCTION_ROOT=D:\Projects\BATTLE2-worktrees\p1-remediation-01-spectator-replace`
- `BYTEFRAY_ROOT=D:\Projects\BATTLE2-worktrees\spectator-pin-9c81718`

- **Result:** `68 passed in 628.52s (0:10:28)` (`0 skipped`, `0 failed`, exit code `0`), confirming:
  - Frozen showcase and `production_sample` presentation documents are reproduced byte-for-byte.
  - Fresh V6 matches export cleanly and pass headless Godot 4.7.2 playback and Agent A isolation verification.

### C. Static & Compatibility Verification

- `python -m ruff check .`: `All checks passed!` (exit code `0`).
- `python -m mypy engine/src/battle_engine`: `Success: no issues found in 107 source files` (exit code `0`).
- `python -m mypy client/src/battle_client`: `Success: no issues found in 20 source files` (exit code `0`).
- `python tools/release_compatibility.py --check docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json`: passed (exit code `0`).

---

## 5. Compatibility Confirmation

- Application version remains `5.0.0`.
- Ruleset IDs (`bytefray-rules-6-alpha1`, `bytefray-rules-4`), Agent API v2, replay schema (`battle2.replay` v4), result schema (`battle2.result` v4), and Spectator manifest schema (`bytefray.spectator.manifest` v2) and document schemas (`bytefray.spectator.broadcast` v1, `bytefray.spectator.agent_view` v1) are unchanged.
- No changes were required in the Spectator Godot repository (`D:\Projects\Bytefray-Spectator-integration-20261017\spectator`).

---

## 6. Historical Independent Review Attempt & Original Closure Steps

- **Codex CLI Review Attempt:** Invoked `codex.exe exec -s read-only -C "D:\Projects\BATTLE2-worktrees\p1-remediation-01-spectator-replace"`. Because the background runner provides an open non-TTY stdin pipe, `codex exec` blocked at `Reading additional input from stdin...` without producing output and was canceled/terminated without affecting any other process or worktree.
- **Historical Status Before the Conversation Review:** **INCOMPLETE** — per project lead direction, automatic retries of the hung Codex CLI were stopped so a separate bounded independent review can be conducted using **Gemini Argon**.
- **Original Remaining Steps Before Closure (superseded by section 7):**
  1. Complete the bounded independent adversarial review of the uncommitted diff in `D:\Projects\BATTLE2-worktrees\p1-remediation-01-spectator-replace` (`client/src/battle_client/spectator_export.py`, `client/tests/test_spectator_export.py`, and this report).
  2. Address any actionable findings from that review (and re-run affected focused tests if code changes).
  3. Update the Independent Review section of this report with the review outcome and create the local commit on `v6-p1-remediation-01-spectator-replace`.


---

## 7. Focused Review Corrections — 2026-10-19

### Scope and review authority

The reviewed HEAD remains the reconciled baseline `08638463fdb3c655892a44c494c860af14005786` until the authorized local commit. The inherited remediation and historical evidence above are preserved. Corrections are confined to `client/src/battle_client/spectator_export.py`, `client/tests/test_spectator_export.py`, and this report. No tracked files in another worktree are edited, and no merge, push, tag, version change, or research qualification campaign is authorized or performed.

The initial conversation review found three actionable issues. The lead authorized their correction and subsequently instructed the current model to take control instead of waiting for Gemini Argon. The final focused review in this section is current-model review of its corrections, not a separately obtained independent approval. No Codex CLI subprocess or Gemini subprocess is launched.

### Review delta: findings and corrections

| Finding | Before correction | Correction and functions |
|---|---|---|
| P1: incomplete documents accepted for destructive replacement | Correct schema labels, sizes, hashes and frame counts could authorize deletion of incomplete, non-presentation documents. | `_verify_document()` validates the exact document-v1 fields, types, nested frame/receipt structures, ownership rows, address ranges, finite scores, phase codes, chronological boundaries and required identities emitted by `_broadcast()` / `_agent()`. `verify_presentation()` also binds Agent A's core to the broadcast entrant. `_is_presentation_dir()` retains its exact file-set and link checks and now inherits these structural checks before replacement or legacy-cache retirement. |
| P2: resolved trace location missing from separation | `_source_directories()` approximated sources from result metadata and omitted a linked trace's actual directory. | `export_presentation()` runs source preflight before staging. `_source_directories()` derives lexical and strict resolved parents from every verified `_Sources` artifact, including trace, and fails closed on resolution errors. The early output rejection and all later safety rechecks are retained. |
| P2: failed restoration concealed recovery location | A second rename failure masked the installation failure and omitted the original's `.old-*` path. | `_install()` handles installation/post-rename rejection and restoration separately. Failed restoration reports both errors and the complete retained recovery path; it never calls aside deletion on this path. Export/install docstrings now describe attempted restoration rather than an unconditional guarantee. |

Authoritative structure was checked against the existing production `_broadcast()` / `_agent()` serializers, `SensingView` records and `SampleStatus`, `ActionKindV2`, and Spectator's `fixture_loader.gd`, `broadcast_model.gd`, and `agent_model.gd`. The existing Spectator loader verifies schema labels and digests but has no complete reusable Python structural validator. Validation uses the existing typed projections and enums; no new presentation format or schema version is introduced. Production manifest v2 remains eligible; prototype manifest v1 remains outside production replacement eligibility, as before. Spectator's v1/v2 readers are unchanged.

Structural validity and self-consistent digests do not authenticate ownership or prove that an adversary actually ran a match. Complete presentation impersonation remains possible and is explicitly outside this guarantee.

### New regression tests

- `test_replace_refuses_structurally_invalid_documents_with_consistent_hashes`: 27 adversarial variants with correct schema labels and recomputed hashes/counts, including the minimal forged pair, missing document/frame fields, malformed nested records/rows, incorrect types, nonfinite score, incorrect identities/core, invalid phase codes/order and missing boundaries. Both API and CLI must reject with `output_unsafe` / nonzero status while preserving every original file byte.
- `test_export_refuses_child_of_resolved_trace_directory`: real file symlink to a valid bound trace; an empty child output under its resolved directory is rejected with and without replacement. A separate output succeeds first, establishing source usability. Source hashes remain unchanged. Windows lacks native file-symlink privilege here, so the two cases are explicitly skipped there and exercised using actual symlinks in the existing Ubuntu environment.
- `test_export_fails_closed_when_trace_location_cannot_resolve`: filesystem and resolution failures return `output_unsafe`, preserve sources and create no output/staging.
- `test_failed_restore_reports_and_preserves_original`: API/CLI installation and post-rename eligibility failures combined with restoration failure preserve original bytes, report both causes and the absolute recovery path, and remove only the export staging directory.
- `test_files_added_after_final_check_are_retained`: entries added after custody rename cause rejection/restoration; entries added after installation preserve the entire aside rather than being deleted.
- `test_aside_cleanup_failure_keeps_installed_output_and_original`: a cleanup permission failure preserves the valid installed presentation and retained original.

### Verification ledger

Evidence is retained under `work/p1-review-corrections-20261019-01/`. Every pytest invocation uses its own new `.pytest-tmp/p1-review-...` directory; earlier evidence is retained.

- Before correction: selected regressions produced **5 failed, 2 skipped** (`before.log`): the minimal document bypass and four recovery-reporting cases failed as expected; native trace symlinks were unavailable on Windows.
- The first correction run exposed a new test selecting an empty initial event list. The test was corrected to select an actual event; this was a test setup error, not an accepted product failure. Ruff also identified the adjacent-pair iterator style, corrected to Python-3.10-compatible `itertools.pairwise`.
- Windows focused exporter/viewer/command/component/compatibility suites: **275 passed, 3 skipped**, final logical correction (`focused-01.log`). Two skips are native file-symlink privilege; one is POSIX execute-bit behavior.
- Ubuntu real trace symlink regressions: **2 passed** (`linux-trace-01.log`). These overlap the exporter module and are not added to its count.
- Ubuntu final exporter module: **160 passed, 0 skipped** (`linux-exporter-01.log`), including real symlinks. This is a separate platform ledger, not an additive count.
- Display-backed Designer Spectator tests: **10 passed** (`gui-01.log`), using the real prepare subprocess. This verifies the test scenarios, not broader native release qualification.
- Ruff: **clean** (`ruff.log`). Engine mypy: **107 source files clean** (`mypy-engine.log`). Client mypy: **20 source files clean** (`mypy-client.log`).
- Release compatibility: **passed**, exit 0, with `PYTHONPATH` explicitly bound to the remediation checkout (`compatibility-02.log`). The initial invocation without that binding imported the shared environment's original checkout and failed; its output remains in `compatibility.log` and is not counted as validation of this worktree.
- Spectator cross-repository suite: **68 passed, 0 skipped, 0 failed in 427.31s** (`spectator-01.log`), restoring the accepted baseline and confirming byte-identical showcase/sample presentation documents and fresh-match Godot playback. Spectator HEAD remains `14089a7bf624a5974346306a277e307ea8f48c07`; pinned Bytefray HEAD remains `9c81718d057c8cd021f6d1cc7938ea19881b78e1`.
- Final allowlisted diff and current-model focused review: **complete, no actionable blocking defect found**. The exact reviewed production/test hashes are retained in `focused-review.json`. Before/after SHA-256 snapshots confirm all **304 Spectator tracked files** and **142 pinned Bytefray source-tree files** remain byte-identical; both protected checkouts remain clean (`protected-before.json`, `protected-after.json`). `git diff --check` is clean.

### Remaining filesystem limitations

Static aliases, ordinary collisions, and the tested interleavings above are checked. An active hostile process can still replace filesystem entries between path-based checks and operations; this is not an OS isolation boundary. Staging cleanup assumes the exporter-created temporary namespace remains under its custody. Abrupt termination between renames can leave the original under `.old-*`; no crash-atomic transaction is claimed. Restoration can fail, in which case the original is retained and its full recovery location is reported. Cleanup after successful installation is best effort and can leave an intact or partially cleaned aside; it does not invalidate the installed presentation. Unknown additional entries prevent aside deletion when observed by its final eligibility check.

### Focused review result and disposition

All three reported findings are corrected and their focused regressions pass. The current-model review re-traced document eligibility through aside deletion, verified source protection before staging, both rollback rejection/install paths, retained recovery handling, late additions and cleanup. No actionable release-blocking defect remains in this bounded remediation. Existing safety rechecks remain in place.

**PASS WITH CONDITIONS — no remaining blocking defects.** Conditions are the documented filesystem/authentication limits above. Review independence is not claimed; the lead explicitly assigned this focused review to the current model. This disposition applies only to P1 Remediation 01, not overall Bytefray 5.1 release qualification. The verified three-file correction is authorized for a local commit; retained evidence is kept under the ignored work root and no publication is performed.
