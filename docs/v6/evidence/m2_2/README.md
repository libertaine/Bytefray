# M2-2 Watchful Keeper curated evidence

This is the published subset of the M2-2 and M2-2A qualification evidence
accepted in [M2-2 Closure 01](../../V6_ALPHA_M2_2_CLOSURE_01.md). The reports
are [Implementation Record 01](../../V6_ALPHA_M2_2_IMPLEMENTATION_RECORD_01.md)
and the [M2-2A correction and qualification](../../V6_ALPHA_M2_2A_CORRECTION_QUALIFICATION_01.md).

The full evidence collection is not published. It stays in the git-ignored
local root `runs/v6_alpha_m2/`: 1,115 files and 208,029,705 bytes in five
campaign directories, of which the M2-2A correction root is 177,375,999 bytes.
Paths written as `runs/v6_alpha_m2/...` or as `origin` values in
[`evidence_index.json`](evidence_index.json) refer to that local root. They are
identifiers, not links.

## Contents

| Path | Kind | Content |
| --- | --- | --- |
| `keeper/seat_A/`, `keeper/seat_B/` | Byte copies | Complete `keeper-K1` runs from Windows repeat 1, one per Keeper seat: replay, trace, result, demo-v1 sidecar and both executed source snapshots |
| `keeper/cross_platform_comparison.json` | Byte copy | Raw hashes of all eight Keeper runs (two seats, two repeats, Windows and Linux) and the per-seat logical-equality verdict |
| `qualification/windows_summary.json`, `qualification/linux_summary.json` | Sanitized summaries | Each pytest, Ruff and mypy campaign: JUnit counts, argv, interpreter, exit code, duration, and hashes of the unmodified local XML, log and command record. Includes native authoring and replay workflow summaries |
| `qualification/correction_only.diff` | Byte copy | Exact M2-2A correction diff: three paths, compared with their preserved entry bodies |
| `qualification/corrected_source_manifest.json` | Byte copy | The 26 entry-file bodies after the correction |
| `qualification/old_starter_preservation.json` | Byte copy | Old starter names, digests and 23 files unchanged |
| `qualification/m2_2_focused_selection.txt`, `qualification/m2_2_broad_selection.txt` | Byte copies | The pytest `@` selection files the campaigns used |
| `qualification/historical_pins_publication_check.json` | Generated | 329 historical pins rechecked at preserved `b948540…` before publication |
| `failures/retained_attempts.json` | Generated | Ledger of every retained JUnit body (34) with counts and hashes, the failed or incomplete non-JUnit attempts, and the C2 baseline frames |
| `failures/c2_baseline_linux_A_test_terminal.png` | Byte copy | C2 baseline: Linux rendered Pygame surface of the Agent A Test replay at terminal state |
| [`evidence_index.json`](evidence_index.json) | Generated | Size and SHA-256 of every other file here, its local origin and the origin's SHA-256 |

Byte copies have the same SHA-256 as their local originals. The sanitized
summaries replace the checkout prefix with `<checkout>`, the preserved M1-1
worktree with `<preserved-m1_1-baseline>` and the Windows font directory with
`<windows-fonts>/`. Nothing else is changed. The bodies they summarize remain
local, bound by the hashes recorded in each summary.

The `.gitattributes` file here disables end-of-line conversion. The Keeper
bodies use CRLF line endings, and `demo.json` and the comparison file bind those
raw bytes. LF normalization would break those hashes.

## Watchful Keeper runs

Profile: `bytefray-rules-6-alpha1`, arena 512, Q=8, seed 0, 100 ticks, starts 0
(Keeper) and 91 (`v6_encroaching_opponent`), default parameters
`scan_interval` 4 and `perimeter_offset` 27, with whole-role seat reversal. Both
entrants are alive at tick 100. Witnesses are given as `(tick, zero-based global
decision index)`:

| Keeper seat | Match | First repair WRITE | First defensive WRITE |
| --- | --- | --- | --- |
| A | `match_e4e25c84e37b1993a96e1413` | (3, 24) | (1, 8) |
| B | `match_d3c0288bf634e01feb9c90b7` | (1, 6) | (1, 10) |

`demo.json` keeps `status: "unverified"` and has no `teaching_exchange` block,
as Scope Revision 03 §7 requires. The `keeper-K1` predicate is checked
separately. To recheck the curated copies from the repository root:

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -c "from battle_engine.sensing_playback import verify_keeper_scenario as v; [print(s, v('docs/v6/evidence/m2_2/keeper/seat_' + s, keeper_seat=s)) for s in 'AB']"
```

Both seats report consistency, reconstruction, source capture and completion as
`True`. This check was run against the accepted candidate before publication.

## Qualification summary

Counts overlap between campaigns and are not summed.

| Platform | Campaign | Result |
| --- | --- | --- |
| Windows 11 AMD64, Python 3.13.7 | Focused (23 modules) | 619 passed, 4 GUI deselected |
| Windows | Native GUI, explicit `-m gui` | 4 passed |
| Windows | M1 Designer GUI supplement | 5 passed |
| Windows | Product selection (137 modules) | 3,374 passed, 20 skipped, 5 GUI deselected |
| Windows | Compatibility supplement | 328 passed |
| Windows | Ruff; engine mypy; client mypy | PASS; PASS (104 files); PASS (19 files) |
| Windows | Native authoring and replay workflow, both seats | PASS (`windows_native_complete`) |
| Ubuntu on WSL2, Python 3.12.3 | Focused (23 modules) | 619 passed, 4 GUI deselected |
| Linux, WSLg X11, Qt xcb | Native GUI, explicit `-m gui` | 3 passed |
| Linux | Native authoring and replay workflow, both seats | PASS (`linux_native_complete_02`); `linux_native_complete` INCOMPLETE (C1) |

## Reproduction

Run from the checkout with `.venv`, using a new output directory each time
(reuse is refused):

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario keeper-K1 --keeper-seat A --output-dir runs/v6_alpha_m2/repro_A_01
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario keeper-K1 --keeper-seat B --output-dir runs/v6_alpha_m2/repro_B_01
& '.\.venv\Scripts\python.exe' -m pytest engine/tests/test_agent_test.py "@docs/v6/evidence/m2_2/qualification/m2_2_focused_selection.txt" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest "@docs/v6/evidence/m2_2/qualification/m2_2_broad_selection.txt" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest "@docs/v6/evidence/m1_6a_windows/supplemental_nodes.txt" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
```

A fresh run should match the curated replay and the logical trace and result
facts. Raw trace and result bytes differ because they contain `wall_time_ms`,
occurrence IDs and timestamps. The original runs used the selection files under
`runs/v6_alpha_m2/m2_2_20261015_review/qualification/`, which are byte-identical
to the copies here. The native workflow harness (`native_workflow.py`), the
passive observer and the read-only resume verifier are local test tooling. They
are not published.

Sources: the accepted product files and their raw hashes are listed in
[Closure 01 §3](../../V6_ALPHA_M2_2_CLOSURE_01.md#3-accepted-source-manifest).
The bundled starter is
[`v6_watchful_keeper`](../../../../engine/src/battle_engine/data/starter_agents/v6_watchful_keeper/agent.py),
the fixture is
[`v6_encroaching_opponent`](../../../../engine/src/battle_engine/data/teaching_fixtures/v6_encroaching_opponent/agent.py),
and the `keeper-K1` verifier is `verify_keeper_scenario` in
[`sensing_playback.py`](../../../../engine/src/battle_engine/sensing_playback.py).

## Retained failures and limitations

Every failed attempt keeps its original name and is listed with its hash in
`failures/retained_attempts.json`. None is relabeled as a pass.

| Attempt | Outcome | Classification |
| --- | --- | --- |
| `m2_2_focused_01` | 17 setup errors | Missing temp parent; harness |
| `m2_2_anchors_01` | 5 failed | Three child-dependency errors and two catalog expectations, updated for the authorized addition |
| `m2_2_broad_01` | 1 failed | Worker hard-kill liveness test; `tasklist` access denied in the sandbox. Passes 16/16 natively and in the final broad run; the specific Windows ACL is unidentified |
| `m2_2_keeper_gui_01`–`04` | 2 failed each | Development Test parser blocker (01, 04, a product defect fixed by M2-2A) and test-harness mistakes (02, 03) |
| `m2_2a_worker_*` (diagnosis) | 1 failed each, sandbox | The same environment limitation; native bodies pass |
| `m2_2a_cli_01`, `m2_2a_cli_02` | 7 and 3 failed | Test expectations corrected to the existing API and the canonical `ticks` field |
| `m2_2a_windows_gui` | 1 failed | Scout test lacked Advanced-tab and ruleset setup |
| `windows_native_01`–`04`, `linux_native_x11_01`–`03`, `*_native_final` | Timeouts | Harness: profiler overhead, wait windows, DPI conversion |
| Linux setup (`linux_xvfb.log`, apt logs, `m2_2a_linux_gui.log`) | Failed | Environment: Xvfb keyboard initialization, stale apt URL, missing libraries |
| `linux_native_complete` | INCOMPLETE | **C1**: End key had no effect for 120 s. The cause is unresolved and it was not reproduced in `linux_end_probe_01` or `linux_native_complete_02` |

Conditions carried forward, as stated in
[Closure 01 §7](../../V6_ALPHA_M2_2_CLOSURE_01.md#7-conditions-carried-forward):

- **C1.** Intermittent Linux End-key non-response. M2-5 Linux qualification
  must keep the delivered-key witness and each viewer's exit status.
- **C2.** Arena-map historical-sample marker labels overlap at terminal state in
  long Test replays, on both platforms. `failures/c2_baseline_linux_A_test_terminal.png`
  is the Linux baseline. The Windows baseline frames are bound by hash only,
  because their window captures include desktop pixels outside the client area.
  This is carried to M2-4 under M2-AC08.
- **C3.** Linux qualification covers WSL2/WSLg X11 only. Automated GUI execution
  is technical evidence and does not establish human usability.

This evidence covers the Keeper slice only. It is not an M2-wide, Alpha 1,
human-evaluation or release acceptance. Original E9 remains operationally
blocked, with execution LOCKED, and Requirement C remains NOT ESTABLISHED.
