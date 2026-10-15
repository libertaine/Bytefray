# M2-3 Roaming Reacquirer curated evidence

This is the published subset of the M2-3 qualification evidence accepted in
[M2-3 Closure 01](../../V6_ALPHA_M2_3_CLOSURE_01.md). The technical report is
[Implementation Record 01](../../V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md),
which includes the R3-07 amendment and final qualification (§9).

The full evidence collection is not published. It stays in the git-ignored
local root `runs/v6_alpha_m2/m2_3_20261015/`; its file count and size at
curation are recorded in [`evidence_index.json`](evidence_index.json). Paths
written as `runs/v6_alpha_m2/...`, or as `origin` and `local_bodies` keys in the
JSON files here, refer to that local root. They are identifiers, not links.

## Contents

| Path | Kind | Content |
| --- | --- | --- |
| `reacquirer/seat_A/`, `reacquirer/seat_B/` | Byte copies | Complete `reacquirer-R1` runs from Windows repeat 1, one per Reacquirer seat: replay, trace, result, demo-v1 sidecar and both executed source snapshots |
| `reacquirer/cross_platform_comparison.json` | Byte copy | Raw hashes of all eight R1 runs (two seats, two repeats, Windows and Linux) and of the two Linux K1 regression runs; per-seat logical-equality and completion verdicts |
| `reacquirer/scenario_comparison.json` | Byte copy | Windows R1 verdicts and witnesses per run, and the Windows K1 regression compared with the published M2-2 bodies |
| `reacquirer/relocation_check_r307.json` | Byte copy | All eight R1 bodies: the fixture moves once, at F4, from 91 to 155; it never SENSEs or WRITEs and receives no sensed anchors |
| `qualification/windows_summary.json`, `qualification/linux_summary.json` | Sanitized summaries | Each pytest, Ruff, mypy and scenario campaign, first pass and R3-07 amendment: JUnit counts, failed node IDs, argv, interpreter, exit code, duration, and hashes of the unmodified local XML, log and command record |
| `qualification/selection_ledger_r307_summary.json` | Sanitized summary | Node/skip ledger of the amendment campaigns against M2-2A and against the failed first pass |
| `qualification/r3_07_amendment.diff` | Generated | Exact R3-07 diff of `engine/tests/test_v6_alpha_m2_keeper.py` against `4fd89bb` |
| `qualification/source_freeze_01.json`, `qualification/source_freeze_02.json` | Byte copies | Raw hashes of the candidate paths at the first-pass freeze and after the amendment |
| `qualification/preservation_02.json` | Byte copy | Preservation audit: frozen paths, unchanged Keeper/Scout/common bodies, old starter bytes and digests, catalog order, 329 pins, exact R3-07 diff |
| `qualification/m2_3_broad_selection.txt` | Byte copy | The pytest `@` selection of the 138-module product campaigns. The focused campaigns used the published [M2-2 focused selection](../m2_2/qualification/m2_2_focused_selection.txt) plus `engine/tests/test_agent_test.py` |
| `qualification/historical_pins_publication_check.json` | Generated | 329 historical pins rechecked at preserved `b948540…` during publication preparation |
| `failures/retained_attempts.json` | Generated | Every retained JUnit body (with counts, failed node IDs and hashes), the failed non-JUnit attempts, and the R3-07 conflict node with the campaigns where it failed and passed |
| [`evidence_index.json`](evidence_index.json) | Generated | Size and SHA-256 of every other file here, its local origin and the origin's SHA-256 |

Byte copies have the same SHA-256 as their local originals. The sanitized
summaries replace the checkout prefix with `<checkout>`, convert its path
separators to `/`, and replace per-campaign pytest scratch directory labels with
`<campaign>`. Nothing else is changed. The bodies they summarize remain local,
bound by the hashes recorded in each summary.

The `.gitattributes` file here disables end-of-line conversion. The two
`trace.jsonl` files and the comparison, relocation, source-freeze and
preservation JSON byte copies use CRLF line endings; the replays, results,
`demo.json` sidecars, source snapshots and the generated files use LF. `demo.json` and the comparison files bind the raw trace
bytes, so end-of-line normalization would break those hashes.

## Roaming Reacquirer runs

Profile: `bytefray-rules-6-alpha1`, arena 512, Q=8, seed 0, 100 ticks, starts 0
(Reacquirer) and 91 (`v6_relocating_opponent`), default parameters
`search_offset` 91, `move_step` 64 and `rescan_wait` 3, with whole-role seat
reversal. Both entrants are alive at tick 100. Witnesses are zero-based global
decision indices in tick 1:

| Reacquirer seat | Match | R1 SENSE91 | R2 receipt | R5 rescan | R6 absent receipt + MOVE | R7 SENSE155 | R8 WRITE155 | Fixture F4 MOVE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | `match_eba20d70f642a2c4a8a05f2d` | 0 | 1 | 8 | 9 | 12 | 13 | 7 |
| B | `match_a13192c7e888978c8b67e41d` | 2 | 3 | 10 | 11 | 14 | 15 | 5 |

Replays are byte-identical across repeats and platforms per seat (`3fa395b1…`
for seat A, `5cf6e3ce…` for seat B). `fallback_points` is empty in both seats.
`demo.json` keeps `status: "unverified"` and has no `teaching_exchange` block,
as Scope Revision 03 §7 requires. The `reacquirer-R1` predicate is checked
separately. To recheck the curated copies from the repository root:

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -c "from battle_engine.sensing_playback import verify_reacquirer_scenario as v; [print(s, v('docs/v6/evidence/m2_3/reacquirer/seat_' + s + '/demo.json', reacquirer_seat=s)) for s in 'AB']"
```

Both seats report consistency, reconstruction, source capture and completion as
`True`. This check was run against the accepted candidate before publication.

## Qualification summary

Counts overlap between campaigns and are not summed. Final results after the
R3-07 amendment:

| Platform | Campaign | Result |
| --- | --- | --- |
| Windows 11 AMD64, Python 3.13.7 | Keeper module (run first) | 48 passed |
| Windows | Reacquirer module | 56 passed |
| Windows | Focused (23 modules) | 626 passed, 4 GUI deselected |
| Windows | Product selection (138 modules) | 3,441 passed, 21 skipped, 5 GUI deselected |
| Windows | Compatibility supplement (first pass, reused) | 328 passed |
| Windows | Native GUI, explicit `-m gui` (first pass, reused) | 6 passed |
| Windows | Ruff; engine mypy; client mypy | PASS; PASS (106 files); PASS (19 files) |
| Ubuntu on WSL2, Python 3.12.3 | Keeper module | 48 passed |
| Linux | Reacquirer module (first pass, reused) | 56 passed |
| Linux | Focused (23 modules) | 626 passed, 4 GUI deselected |
| Linux, WSLg X11, Qt xcb | Native GUI, explicit `-m gui` (first pass, reused) | 5 passed |

Reuse is justified in Implementation Record 01 §9: all 16 non-amendment
candidate paths are byte-identical between the two source freezes, and the
reused selections do not contain the amended test module.

## Reproduction

Run from the checkout with `.venv`, using a new output directory each time
(reuse is refused):

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario reacquirer-R1 --reacquirer-seat A --output-dir runs/v6_alpha_m2/repro_r1_A_01
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario reacquirer-R1 --reacquirer-seat B --output-dir runs/v6_alpha_m2/repro_r1_B_01
& '.\.venv\Scripts\python.exe' -m pytest engine/tests/test_v6_alpha_m2_keeper.py engine/tests/test_v6_alpha_m2_reacquirer.py --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest engine/tests/test_agent_test.py "@docs/v6/evidence/m2_2/qualification/m2_2_focused_selection.txt" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
& '.\.venv\Scripts\python.exe' -m pytest "@docs/v6/evidence/m2_3/qualification/m2_3_broad_selection.txt" --basetemp=<fresh-dir> -o cache_dir=<fresh-dir>
```

A fresh run should match the curated replay and the logical trace and result
facts. Raw trace and result bytes differ because they contain `wall_time_ms`,
occurrence IDs and timestamps. The original runs used the selection file under
`runs/v6_alpha_m2/m2_3_20261015/`, which is byte-identical to the copy here.
The campaign runner, comparators, ledger and curation scripts are local test
tooling. They are not published.

Sources: the accepted product files and their raw hashes are listed in
[Implementation Record 01 §2](../../V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md#2-exact-m2-3-change-list).
The bundled starter is
[`v6_roaming_reacquirer`](../../../../engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.py),
the fixture is
[`v6_relocating_opponent`](../../../../engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.py),
and the `reacquirer-R1` verifier is `verify_reacquirer_scenario` in
[`sensing_playback.py`](../../../../engine/src/battle_engine/sensing_playback.py).

## Retained failures and limitations

Every failed attempt keeps its original name and is listed with its hash in
`failures/retained_attempts.json`. None is relabeled as a pass.

| Attempt | Outcome | Classification |
| --- | --- | --- |
| `m2_3_reacquirer_01` | 2 failed | Test harness: numeric-string coercion expectation and an import sentinel placed before `from __future__` |
| `m2_3_ruff_01` | 4 findings | Style findings in new code, fixed before the source freeze; every final campaign ran after the freeze |
| `m2_3_keeper_final`, `m2_3_focused_final`, `m2_3_broad_final`, `m2_3_linux_focused` | 1 failed each, same node | Obsolete Keeper catalog-suffix assertion outside the original boundary. Resolved by the lead-authorized R3-07 amendment; the node passes in every amendment campaign |
| `linux_campaign_focused.out` | Launch failure | Git Bash path conversion; nothing executed |
| First cross-platform comparison | FAIL (stdout only, overwritten) | Comparator compared the `product_version` build label; the rerun excludes it, as M2-2A did |

Conditions carried forward, as stated in
[Closure 01 §6](../../V6_ALPHA_M2_3_CLOSURE_01.md#6-conditions-carried-forward):

- **L1.** Seat B's delivered perspective is verified at code and cursor level;
  interactive A/B replay selection is M2-4 work.
- **L2.** External replay-viewer controls were not separately requalified for
  R1 artifacts.
- **L3.** Linux coverage is WSL2/WSLg X11 only.
- **L4.** M2-2 conditions C1–C3 remain open.
- **L5.** M2-3 added one skip, `…[api2-roaming_reacquirer]` (no frozen
  executable), under the existing approved reason.

This evidence covers the Reacquirer slice only. It is not an M2-wide, Alpha 1,
human-evaluation or release acceptance. Original E9 remains operationally
blocked, with execution LOCKED, and Requirement C remains NOT ESTABLISHED.
