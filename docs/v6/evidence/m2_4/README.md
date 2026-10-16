# M2-4 Replay and Usability curated evidence

This is the published subset of the M2-4 qualification evidence accepted in
[M2-4 Closure 01](../../V6_ALPHA_M2_4_CLOSURE_01.md). The technical report is
[Implementation Record 01](../../V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md).

The full evidence collection is not published. It stays in the git-ignored
local root `runs/v6_alpha_m2/m2_4_20261015/`; its file count and size at
curation are recorded in [`evidence_index.json`](evidence_index.json). Paths
written as `runs/v6_alpha_m2/...`, or as `origin`, `run` and `local_bodies`
values in the JSON files here, refer to that local root. They are identifiers,
not links.

## Contents

| Path | Kind | Content |
| --- | --- | --- |
| `c2_layout/windows_before_report.json` | Byte copy | C2 probe on Windows before M2-4: every rendered text and marker-label rectangle, per view and size |
| `c2_layout/linux_before_report.json` | Sanitized copy | C2 probe on Linux with the published `e7c0f9d` renderer (`393f29af…`) |
| `c2_layout/windows_after_report.json`, `c2_layout/linux_after_report.json` | Sanitized copies | C2 probes at the final candidate (freeze 05, renderer `1526b500…`), with the `--assert` result |
| `c2_layout/frames/` | Byte copies | Nine frames: Agent A at the recorded end at 900x650 and 1100x750, before and after, on both platforms, plus the Linux Help page at 900x650 |
| `native/native_observations.json` | Generated | All six supplementary native viewer runs: steps, delivered key events, viewer output, frame hashes and their byte equality with the offscreen probe frames, and hashes of the local bodies |
| `performance/load_timing_windows.json` | Byte copy | D2: in-process load phases on the C2 replay, idle Windows |
| `qualification/windows_summary.json`, `qualification/linux_summary.json` | Sanitized summaries | Every pytest, Ruff and mypy campaign, development and freezes 01–05: JUnit counts, failed node IDs, argv, interpreter, exit code, duration, final log line and hashes of the local XML, log and command record. The Linux summary also hashes the campaign scripts and their outputs and names the one script that never ran |
| `qualification/node_skip_ledger.json` | Generated | The final Windows product campaign against M2-3's: 31 added nodes (all from the new module), none removed, identical 21 skipped node IDs |
| `qualification/source_freeze_01.json`, `qualification/source_freeze_05.json` | Byte copies | Raw hashes of the candidate paths at the first and final freezes |
| `qualification/preservation_final.json` | Byte copy | Final preservation audit: boundary, engine identity, excluded client modules, starters, catalog order, 329 pins |
| `qualification/historical_pins_publication_check.json` | Generated | 329 historical pins rechecked at preserved `b948540…` during closure; the closure audit is byte-identical to `preservation_final.json` |
| `failures/retained_attempts.json` | Generated | Every retained JUnit body with counts, failed node IDs, hashes and classification; every C2 probe with its assertion result; the failed and unexecuted non-JUnit attempts |
| [`evidence_index.json`](evidence_index.json) | Generated | Size and SHA-256 of every other file here, its local origin and the origin's SHA-256 |

Byte copies have the same SHA-256 as their local originals. Sanitized files
replace the checkout prefix with `<checkout>` and convert its path separators to
`/`; nothing else changes, and each keeps the SHA-256 of its unmodified origin.

The `.gitattributes` file here disables end-of-line conversion. The
`windows_before_report.json`, `load_timing_windows.json`, source-freeze and
`preservation_final.json` byte copies use CRLF line endings; every other text
file here uses LF.

## C2 sample-marker labels

Input: the Keeper Development Test replay `98edb90d…` (`match_2b6f25a5…`, 200
ticks, recorded end "winner B; tick_limit") with its trace and result, as fixed
by [M2-2 Closure 01 §7](../../V6_ALPHA_M2_2_CLOSURE_01.md#7-conditions-carried-forward).
The input bodies are not published; their hashes are in
`native/native_observations.json`. Values below are Agent A at 900 / 1000 / 1100
pixels wide; "pairs" are intersecting map-label pairs.

| Probe | Font | Labels | Pairs | Escaping the map | Other |
| --- | --- | --- | --- | --- | --- |
| Windows before | Consolas | 23 / 23 / 23 | 81 / 81 / 58 | 4 / 4 / 4 | Disclaimer runs into a history line at 1000 and 1100; no seat-B view |
| Linux before | DejaVu Sans Mono | 23 / 23 / 23 | 96 / 81 / 81 | 5 / 4 / 4 | Same disclaimer overlap; in Omni, one overlapping text pair at every size and one clipped line at 900 |
| Windows after | Consolas | 6 / 8 / 10 | 0 | 0 | 17 / 15 / 13 labels counted as not shown; B and Omni clean |
| Linux after | DejaVu Sans Mono | 6 / 6 / 8 | 0 | 0 | 17 / 17 / 15 labels counted as not shown; B and Omni clean |

Both "after" probes report zero overlapping text, zero clipped text and
`--assert` PASS. Agent A's 395 delivered samples and 23 contacts are unchanged
and remain in its history list; seat B, the non-sensing reference opponent, has
none.

**About the native frames.** The native runs saved the viewer's own drawn
surface from inside the native process. Each native frame is byte-identical to
the offscreen frame of the same freeze, view and size (see
`native/native_observations.json`). They show what the native viewer drew, not
compositor or display-scaled output. The native before/after obligation for C2
remains with M2-5.

## Qualification summary

Final candidate, freeze 05. Counts overlap between campaigns and are not
summed.

| Platform | Campaign | Result |
| --- | --- | --- |
| Windows 11 AMD64, Python 3.13.7 | New module, gui included | 37 passed |
| Windows | Client sensing and `test_hud_layout.py`, gui included | 163 passed |
| Windows | Focused | 824 passed, 10 GUI deselected |
| Windows | Product selection (139 modules) | 3,472 passed, 21 skipped, 11 GUI deselected |
| Windows | Designer GUI, explicit `-m gui` | 8 passed |
| Windows | Ruff; client mypy; engine mypy | PASS; PASS (19 files); PASS (106 files) |
| Ubuntu on WSL2, Python 3.12.3 | New module, gui included | 37 passed |
| Linux | Client sensing | 163 passed |
| Linux | Focused | 824 passed, 10 GUI deselected |
| Linux, WSLg X11, Qt xcb | Designer guide node | 1 passed |

The scenario runs, the Keeper and Reacquirer native demonstrations and the
compatibility supplement were reused from M2-2/M2-3, because the engine is
byte-identical to `e7c0f9d`.

## Reproduction

From the checkout with `.venv`, using new pytest roots each time:

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -m pytest client/tests/test_v6_alpha_m2_4_views.py -m "gui or not gui" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest "@docs/v6/evidence/m2_3/qualification/m2_3_broad_selection.txt" client/tests/test_v6_alpha_m2_4_views.py --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest tests/test_v6_alpha_m1_5_designer.py -m gui --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
```

The layout tests use the published Keeper and Reacquirer bodies, so they need
no local evidence. The C2 probe, native harness, load-timing script, runner and
curation scripts are local test tooling and are not published.

## Retained failures and limitations

Every failed attempt keeps its original name and is listed with its hash in
`failures/retained_attempts.json`. None is relabeled as a pass.

| Attempt | Outcome | Classification |
| --- | --- | --- |
| `m2_4_dev_existing_01`, `m2_4_dev_new_01` | 2 failed each | Development test geometry and fixtures |
| `m2_4_linux_views` and probe `linux_after_final` (freeze 01) | 3 failed; probe FAIL | Product defect, fixed: caption width under DejaVu Sans Mono |
| `m2_4_linux_views_02`, `m2_4_linux_views_04` | 3 failed each | Product defect, fixed in freeze 05: Linux text height exceeded the row pitch |
| `m2_4_linux_dev_views_05` | Nothing collected | Launch failure (argument splitting); relaunched as `_05b` |
| `windows_native_01`, `windows_native_02` | Harness failures | Launcher PID; portrait display width |
| `windows_native_03` | One step unconfirmed | Help off: synthetic Shift was not delivered |
| `linux_campaign_03.sh` | Not executed | Superseded by freeze 04 |

Conditions carried forward are listed in
[Closure 01 §7](../../V6_ALPHA_M2_4_CLOSURE_01.md#7-conditions-carried-forward):
M2-2 C1–C3, M2-3 L1–L5 and the M2-4 decisions D2 (replay load time) and D3
(English-only; accessibility unassessed). This evidence covers the M2-4 slice
only. It is not an M2-wide, Alpha 1, accessibility, human-evaluation or release
acceptance. Original E9 remains operationally blocked, with execution LOCKED,
and Requirement C remains NOT ESTABLISHED.
