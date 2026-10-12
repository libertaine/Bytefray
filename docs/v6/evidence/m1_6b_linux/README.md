# M1-6B Linux qualification evidence

This packet supports [Linux Qualification 01](../../V6_ALPHA_M1_6_LINUX_QUALIFICATION_01.md).
**M1-6B LINUX — FORMALLY CLOSED; qualification disposition PASS.**
Windows M1-6A remains CLOSED — PASS. Overall M1 Alpha 1 technical acceptance is
READY FOR CONSOLIDATED PROJECT LEAD REVIEW. No unrestricted release acceptance
is implied. The reviewed allowlist is staged against
`5d6fc19e2b84805e0453da2c851f1ab0d7804f2f`; nothing is committed or pushed.

| Retained run | Original result |
| --- | --- |
| `focused.xml` | 137 passed, four GUI deselected; all 137 overlap product regression |
| `regression.xml` | 3,207 passed, 11 skipped, five GUI deselected |
| `supplemental.xml` | 328 passed; exact Windows compatibility selection; no product-selection overlap |
| `gui.xml` | 507 passed, one Windows-only skip, one focus failure; 556 deselected |
| `focus_repro.xml` | Same focus failure reproduced alone: one failed |
| `focus_assisted.xml` | Same unchanged test after ordinary native X11 activation: one passed |

No aggregate total is claimed. The original failure remains in both failed
JUnit records and logs. L1 is resolved as a qualification-environment issue;
L2 is a nonblocking usability limitation requiring post-M1 tracking. See the
report for affected rows, Windows comparison and bounded follow-up.

`environment.json` and `host_context.json` document native Linux and actual
Qt xcb/SDL x11 under Xvfb. `native_summary.json` and
`verified_viewer_states.json` record engine verification, visible Qt authoring,
actual QProcess/Popen launches, passive post-draw observations and XTest input.
The observer supplies no controls. Controls came from xdotool; Qt actions used
QTest events. This is automated native interaction, not a human usability study.

`screenshot_provenance.json` records all 18 authentic native capture hashes and
capture methods. Sixteen unchanged privacy-reviewed frames are staged. Result
frames 05/07 display absolute temporary match paths and remain local-only;
their bytes were preserved without editing. Three Designer replay captures
show the three actual result-backed child launches; duplicate-looking frames
are not counted as additional tests.

The generated `artifacts.zip` is excluded from staging and remains local-only.
`artifact_hashes.json` binds its 22 members. `final_verification.json` records
independently checked replay/result/demo/trace associations and captured source
fingerprints. The repeated 1,000-tick replay bytes match, and all 16,000 logical
trace records match after excluding only `wall_time_ms`. Raw artifact custody
and reproduction are separate from this publication packet.

`*_command.json`, `additional_commands.json`, selections and `*_output.txt`
preserve commands, outcomes and useful logs with local prefixes normalized.
`publication_review.json` documents tokens, whitespace normalization, original
digests, excluded files and unchanged local custody. Exported JUnit omits only
hostname/captured streams and normalizes paths/whitespace; case identities,
timings, outcomes and focus traceback remain. Exact executed-source snapshots
remain local-only; the three reusable reviewed helpers are staged under
`tools/qualification/`.

Reproduce only the focus finding when necessary: export the published baseline
to a source tree outside the system temporary root, select an isolated Linux
Python environment with PySide6, and use `QT_QPA_PLATFORM=xcb` under
`xvfb-run -a`. Set `PYTHONPATH` to that archive's engine/client source roots,
its repository root and this repository's `tools/qualification`. Create
`$BYTEFRAY_LINUX_QUALIFICATION_DIR/evidence/final`, then invoke the exact named
node from the report with `-m gui -p linux_focus_plugin` and a fresh source-local
`--basetemp`. The plugin activates only that test's actual X11 window and records
focus proof. No assertion or product function is replaced. Without activation,
bare Xvfb reproduced the retained failure. No such rerun was needed in final
review; no passing regression campaign was repeated.

`changed_files.txt` inventories all qualification files, including local-only
exclusions. `staged_manifest.txt` is the exact staging allowlist.
`evidence_hashes.json` binds staged packet members except itself. Original
records and pre-review exports remain unchanged in ignored local custody.
Accepted product source, schemas, fixtures, tests and Windows qualification
are unchanged. E9 remains LOCKED; Requirement C is NOT ESTABLISHED; no research
execution, new G consumption or authority event occurred.
