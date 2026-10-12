# Bytefray V6 — M1-6B Linux Qualification Report 01

2026-10-11, America/Indianapolis.

**M1-6B LINUX — FORMALLY CLOSED**\
**Qualification disposition: PASS**\
**Windows M1-6A: CLOSED — PASS**\
**Overall M1 Alpha 1 technical acceptance: READY FOR CONSOLIDATED PROJECT LEAD REVIEW**

The authorized M1 vertical slice passed actual native Linux engine execution,
independent artifact reconstruction, deterministic completed teaching runs,
Linux Qt authoring, unmocked replay subprocess launching and confirmed X11/SDL
controls. The adopted product complement and compatibility supplement passed.
One existing GUI test failed because bare Xvfb did not activate its window;
the same unchanged test passed after real X11 window focus. Its original failure
is retained. The history-text overlap is a nonblocking usability limitation
requiring post-M1 follow-up. Neither finding required changing accepted product code.

This disposition covers the bounded M1 X11/Xvfb contract. It does not grant
Alpha 1 acceptance, post-M1 development, scientific authority or release
readiness. Only the reviewed qualification allowlist is staged; nothing was
committed or pushed. Final review inspected retained evidence and hashes without
restarting qualification or repeating passing regression campaigns.

## 1. Actual Linux environment and feasibility

| Property | Observed qualification environment |
| --- | --- |
| Distribution | Ubuntu 26.04.1 LTS, Resolute Raccoon |
| Kernel | `7.0.0-38-generic`, native Linux kernel |
| Host/virtualization | HP Pavilion Notebook; `systemd-detect-virt`, `--vm` and `--container` each report `none`; PID 1 is `systemd` |
| WSL | No WSL kernel or WSL execution; qualification ran on the native Linux host |
| Architecture | x86_64 |
| Python | CPython 3.14.4, GCC 15.2.0; `<qualification-root>/venv/bin/python` |
| Product metadata | Bytefray 5.0.0, installed editable from the separate qualification source tree |
| Dependencies | PySide6 6.11.2, pygame-ce 2.5.8, PyYAML 6.0.3, pytest 9.1.1, Ruff 0.16.6, mypy 2.3.1 |
| Qt | Qt 6.11.2; actual QPA platform `xcb`, visible native widgets |
| Pygame/SDL | pygame-ce 2.5.8 / SDL 2.32.10; actual video driver `x11` |
| Xvfb | Installed, `2:21.1.22-1ubuntu1.2`; workflow server screen 1440×1000×24 |
| X11 prerequisites | libxcb-cursor0 0.1.6-1; xdotool 3.20160805 with real XTest input |
| Font | Requested `consolas`; Pygame resolves `/usr/share/fonts/truetype/msttcorefonts/cour.ttf` on this host |
| Desktop availability | Host X11 `:0` is accessible outside the tool sandbox; `wayland-0` is advertised. Human desktop and Wayland interaction were not qualified. |
| Exercised displays | Separate Xvfb servers, with `QT_QPA_PLATFORM=xcb`, `SDL_VIDEODRIVER=x11`; dummy audio only |

Evidence: [environment](evidence/m1_6b_linux/environment.json) and
[host context](evidence/m1_6b_linux/host_context.json).

The first feasibility probe ran inside the tool's confined process namespace:
`systemd-detect-virt` reported `container-other`, desktop access failed and Qt
could not connect to Xvfb. Approved execution outside that sandbox immediately
created real Qt and SDL windows. Subsequent qualification and host inspection
established the native host context above. The initial failure was an access
limitation, not evidence of a missing Qt plugin or a container-qualified host.

No system package installation, Windows application or Windows test result was
used to establish Linux execution. Only Linux Python 3.14 was exercised here;
the supported Python 3.10–3.14 matrix remains later alpha-wide scope.

## 2. Exact baseline, checkout and isolation

The primary Linux checkout started clean on `v6-research`, at the authorized
published commit:

```text
5d6fc19e2b84805e0453da2c851f1ab0d7804f2f
```

A separate tracked-source archive was exported from that exact Git object to:

```text
work/m1_6b_linux/source (relative to the repository)
```

This is a separate archive checkout, without its own `.git` directory. Its
provenance is the explicit `git archive` input and a complete subsequent
comparison against a fresh archive of the same commit: **1,668/1,668 files
match; zero mismatches**. Six PowerShell files have their prescribed CRLF
export form rather than the LF Git-blob form, as required by `.gitattributes`;
all match the actual archive. Runtime module origins point into this source
tree. The primary checkout's existing source and Windows qualification evidence
remain unchanged.

The final location is under ignored `work/`, outside the system temporary root.
The first `/tmp` source export exposed an existing isolation-test assumption:
both a Windows-looking relative path and the checkout's parent became legal
Linux temporary destinations under the documented product output policy.
Moving the source tree corrected that test environment without changing the
policy or assertion. No clean/reset operation was performed.

A new virtual environment resides at `<qualification-root>/venv`. Its project
installation is the qualified source tree. It reuses the available Linux
dependency store through a `.pth` path to
`.venv-rc2-linux-build/lib/python3.14/site-packages`; that dependency environment
was not modified. This is isolated project/data execution with reused
libraries, not a new network-installed, self-contained dependency qualification.
Explicit source paths and recorded import origins prevent loading the primary
checkout's engine/client implementation.

Teaching outputs, writable personal agents, native matches and viewer logs were
confined to `<qualification-root>/`. Tests used fresh source-local directories
under `.pytest-tmp/`. `PYTHONDONTWRITEBYTECODE=1` protected source/revision
capture from incidental bytecode. `BYTEFRAY_ROOT` supplied the isolated data
root. No predecessor data-root variable was needed.

The contract, adopted Phase 0 packet, Windows record, M1-3 through M1-5 records,
and adopted historical-baseline disposition were reviewed. Existing specs and
architecture boundaries were preserved. Qualification adds evidence and tools;
no accepted engine, client, app, schema, fixture or test assertion was edited.

Evidence: [baseline integrity](evidence/m1_6b_linux/baseline_integrity.json),
[retained setup attempts](evidence/m1_6b_linux/attempts.json).

## 3. Linux AC1–AC11 qualification matrix

All statuses below apply to the authorized Linux M1 scope. Focused tests overlap
the product complement; rows and witness steps are not additive test totals.

| Criterion | Linux evidence | Disposition |
| --- | --- | --- |
| AC1 legality | 42 M1-1 policy/capability cases, M1-3 illegal operand/reach cases; actual Qt v4 capability rejection and alpha1 validation | PASS |
| AC2 price | Quota/exhaustion and trace-on/off tests; independent reconstruction verifies action accounting; pending viewer frame shows one action spent and no contact | PASS |
| AC3 availability | Empty passive observations and exact historical samples checked by native M1 tests and reconstruction; first sample is anonymous address 91 | PASS |
| AC4 delivery | Same-process, later-chunk/tick, suppression and terminal non-delivery cases; native observation 2 receives sample from action 1 | PASS |
| AC5 knowledge | 21 M1-4 cases plus eight hostile probes; M1-5 scene adversarial cases; native pending contacts empty, delayed receipt 91, historical age retained; no live opponent tracking | PASS |
| AC6 reconstruction | Full replay4/trace2/result2/demo binding and every tick independently checked; missing/corrupt trace disables delivered perspective; invalid optional sidecar withholds its badge | PASS |
| AC7 client agreement | Cursor/ReplaySession agreement tests; real XTest phase, seek, restart, speed and perspective transitions observed after drawing in the live SDL subprocess | PASS |
| AC8 reproduction | Two complete 1,000-tick runs: identical canonical replay, all 16,000 logical trace records equal, same match/result identity and terminal outcome; complete revision fingerprints agree | PASS |
| AC9 authoring | Visible Linux Qt window; actual New Agent dialog; edited controls; real validation/match QProcesses; result-backed unmocked replay launches; earlier-settings label and preserved first result | PASS |
| AC10 compatibility | Product complement, 328-case compatibility supplement, 32 stable-v4 historical/equivalence tests, historical readers/retirement checks and exact baseline/archive verification | PASS |
| AC11 research isolation | Product negative import/path tests pass; no research controller, private seed or authority operation; 329 original historical raw pins match Git; no accepted research/product source changes | PASS |

Detailed inventories, JUnit, native state observations and source digests are
in [the Linux evidence packet](evidence/m1_6b_linux/README.md).

## 4. Native Linux engine and teaching artifacts

Three product teaching executions used `run_sensing_demo` and the ordinary
`NativeMatchService`, with the explicit `bytefray-rules-6-alpha1` identity:

| Execution | Inputs | Canonical result |
| --- | --- | --- |
| `teaching_1000` | Seed 0, arena 512, Q=8, starts A=0/B=91, interval 4, move step 64, limit 1,000 | `match_1971f1d14781a6e8edd4dc06`; `result_a7040f4fc273e87273736dc2` |
| `teaching_1000_repeat` | Identical captured inputs and source | Same match/result IDs and complete logical gameplay |
| `teaching_windows_equivalent` | Same fixture, 100-tick limit used by the Windows witness | `match_ea7839ea9e34e1282e8ab494`; `result_feb7ef27a99b89a4ec883add` |

All finish at their recorded tick limit with a tie. The result envelope displays
`winner="tie"`; the replay viewer's recorded terminal winner is `None`, matching
the Windows terminal display. These are existing representations of the same
terminal outcome.

The actual exchange is SENSE(91), one-action cost without world mutation;
next same-process observation receives `(91,)`; MOVE(+64) changes own anchor
0→64; a subsequent legal WRITE(91) is recorded. Independent verification marks
all seven teaching facts VERIFIED. Passive enemy contacts stay empty.

`verify_demonstration` reconstructs **32,989 sub-tick states** per 1,000-tick
match and **3,289** for the 100-tick match, checking canonical tick boundaries,
ordered observations/actions, historical samples, receipt delivery and result
association. It does not execute an agent or research controller during
reconstruction. Source captures are complete, initial/final loaded fingerprints
agree, and no drift is detected.

The additional native negative witness confirms missing trace, malformed trace,
invalid optional demo, stable-v4 capability rejection and valid alpha1 selection.
A fresh data root had to bootstrap bundled starters before name-based validation;
that initial harness prerequisite failure is retained, not counted as product
capability evidence. Corruption tests operate on separate negative fixtures,
leaving the completed teaching artifacts intact.

All raw associated artifacts remain local-only in the retained artifact ZIP.
Its 22 members were independently hashed during final review. Published
[per-member hashes](evidence/m1_6b_linux/artifact_hashes.json) and
[verified associations](evidence/m1_6b_linux/final_verification.json) bind the
replay, trace, result and demo without staging generated match artifacts.

## 5. Linux Qt Designer workflow

The successful witness used visible Qt `xcb` widgets, Qt event processing and
QTest button/key events. Match and validation execution used the actual Linux
QProcess routes. Replay launching used the actual **View Last Match** button,
result association preflight and unmodified Popen launcher.

| Required workflow | Observed change/evidence |
| --- | --- |
| Launch and stable default | Window visible; Development and Advanced both select `bytefray-rules-4`; `01_designer_default.png` |
| Personal Window Scout copy | Actual New Agent dialog creates `my_window_scout/agent.py` and manifest; original bundled starter unchanged |
| Explicit alpha selection and edits | Both appropriate selectors use `bytefray-rules-6-alpha1`; interval 2 and move step 32 set through bounded controls; no parameter errors |
| Successful validation | Real child dry-run returns `Last validation: Valid`; `04_validation.png` |
| Stable-v4 mismatch | Test disabled and child validation reports unsupported `sense` capability before match execution; `02_capability_rejection.png` |
| First complete native match | Five ticks; exact alpha1 identity and effective parameters recorded; `result_228415a9fd518026efac41c4` |
| Launch/reopen correct replay | Live SDL child argv names that first result's replay/trace; Home and Right produce observed phase changes; exit 0 |
| Edit and revision separation | Interval 3 / step 16; earlier-result label appears; reopening still selects the recorded first match before rerun |
| Second complete match | `result_3f97e20f697ac0d1e82bd346`; new directory/parameters; first directory's complete file hashes unchanged |
| Reopen second and shutdown | Child argv selects second replay; exit 0; Designer closes and becomes invisible |

Three actual replay children were opened by Designer: first result, first result
again after settings edits, and second result. Each closed with exit code 0.
There was no replay-launcher mock. The recorded identifiers and effective
parameters match the two published Windows authoring results exactly.

Privacy-reviewed screenshots and post-draw state observations are retained in
[the frame provenance record](evidence/m1_6b_linux/screenshot_provenance.json) and
[native summary](evidence/m1_6b_linux/native_summary.json). Result screenshots
05/07 remain unchanged and local-only because they display absolute temporary
match paths; their hashes and workflow findings are retained. This is automated
native GUI interaction, not a human usability study. Settings separation is
proved; no claim of a new source revision is inferred from parameter edits.

## 6. Linux Pygame/SDL controls and authentic frames

The canonical 100-tick teaching replay was opened through the actual client CLI
in a separate Linux process, paused initially. The witness located its real X11
window and supplied XTest keyboard/mouse input with xdotool. A qualification-only
`sitecustomize` observer records state after the original renderer's `draw`
returns. It does not replace playback, rendering, events or launch functions,
and does not supply gameplay input. Qt's `grabWindow` captures the actual X11
window. No image generation or editing was used.

| Control | Confirmed state, not just dispatched input |
| --- | --- |
| Right / Left | Indices 0→1→2→3→4→6, then 6→5; OBSERVATION/ACTION phases change |
| Pause/play | `playing` becomes true and index advances beyond 5; next Space stops it |
| Speed | 1×→2×→1× observed independently of cursor navigation |
| Timeline seek | Actual mouse click seeks to index 850 / tick 50 and pauses |
| Home / rewind | Index 0 and empty contacts restored |
| Shift+Right | Tick 10 boundary reached, with aged contact 91 |
| 1 / 2 perspectives | Separate OmniscientView and SensingView; omniscient label present |
| Resize | Actual SDL surface becomes 950×680 |
| End | Recorded terminal text appears only at the final phase |
| Escape | Dedicated teaching viewer and all three Designer viewers exit 0 |

SDL replaces the native X11 window when this resize is processed. The external
witness initially addressed the retired window ID; rediscovering the current
window resolved it. That is an expected platform/automation difference, not a
failed resize or event-loop defect.

The retained teaching frames are:

| Frame | Demonstrated fact |
| --- | --- |
| [A_unknown](evidence/m1_6b_linux/frames/A_unknown.png), [B_observation_unknown](evidence/m1_6b_linux/frames/B_observation_unknown.png) | Unknown opponent state; contacts empty |
| [C_sense_cost_pending](evidence/m1_6b_linux/frames/C_sense_cost_pending.png) | SENSE(91), one action spent, result pending; no contact leaked |
| [D_delayed_receipt](evidence/m1_6b_linux/frames/D_delayed_receipt.png) | Anonymous 91 sampled at callback 1, delivered at callback 2 |
| [E_move](evidence/m1_6b_linux/frames/E_move.png), [F_write](evidence/m1_6b_linux/frames/F_write.png) | Recorded legal MOVE and subsequent WRITE |
| [G_historical_age](evidence/m1_6b_linux/frames/G_historical_age.png) | Contact remains at 91, age 9 ticks / 79 own callbacks; newer scans remain local |
| [H_omniscient](evidence/m1_6b_linux/frames/H_omniscient.png) | Clearly labeled full-world view and separate operator verification |
| [I_terminal](evidence/m1_6b_linux/frames/I_terminal.png) | Recorded tie/tick-limit outcome after resize |

Entrant drawing still accepts the M1-4 filtered SensingView. The native observer
records empty contacts at the pending request and contact 91 only at delivery;
source/boundary tests independently cover hidden opponent activity, switching
and prefix reconstruction. The lower history/footer overlap is recorded in §10.

## 7. Deterministic reproduction and Windows comparison

Both full 1,000-tick Linux executions have **1,003 canonical replay lines** and
**16,000 trace records**: 15,994 decision records plus six header/reset/declaration/
binding records. All replay bytes match on this platform. All ordered logical
trace records match after excluding only `wall_time_ms`; zero differences.
Match/result IDs, terminal outcome, effective parameters, starts and captured
source fingerprints agree. The replay SHA-256 is:

```text
dbe67aa534e23f055c0a43287bbed5fae9878b5c2139bd1df207d4a3dbfbf80f
```

Each pair's raw trace/replay/result binding is independently verified. Occurrence
IDs, completion timestamps, callback timings and demo Python version are not
required to be byte-identical across occurrences/platforms. No arbitrary editable
Python agent is certified deterministic.

| Comparison to closed Windows M1-6A | Linux finding / classification |
| --- | --- |
| Ruleset and capability semantics | Same published product source and selected alpha1 policy; stable v4 remains default; PASS |
| Effective parameters | Designer 2/32 then 3/16, same recorded result IDs as Windows; equivalent canonical authoring results |
| Teaching inputs/exchange | Same disclosed seed 0, A=0/B=91, 512 cells, Q=8, 4/64 defaults; request→receipt→MOVE→WRITE and historical knowledge agree |
| Windows-equivalent bounded run | 103 replay lines and 1,600 trace records at 100 ticks, tick-limit tie, same documented teaching facts |
| Python | Linux 3.14.4 vs Windows 3.13.14; expected supported-platform variation |
| Qt/SDL | Qt 6.11.2 and SDL 2.32.10 on both; xcb/x11 instead of windows; native child operation proven |
| Filesystem | Case-sensitive Linux, working symlinks, no NTFS junction/Job Object behavior; expected skips and additional passes |
| Font/window handling | Host resolves the requested font differently; SDL native-window identity changes on resize; expected variation |
| Replay/trace validation | Native bindings, independent reconstruction and negative fallbacks pass on Linux |
| Research/historical boundaries | Same frozen identifiers/defaults, unchanged research bytes and product isolation; no scientific inference |

The published Windows packet contains its results and captured input description,
but not the original complete teaching replay/trace bodies. Therefore a
record-by-record Linux-versus-Windows gameplay diff is **unverified due to artifact
availability**. Comparisons above are limited to published equivalent inputs,
reported facts and canonical Designer result identities. No Windows evidence
was regenerated, edited or treated as Linux proof. Cross-platform byte equality
is not required by the contract.

## 8. Regression qualification, exclusions and static checks

The exact adopted Windows product module selection and 328 supplemental nodes
were reused. The 123 research/experiment modules and the separately adopted
72-node historical context retain their Windows/M1-1 classification. No skip,
xfail, assertion, pytest configuration or research guard was changed. Locked E9
scientific tests/controllers were not launched.

| Run | Passed | Failed | Errors | Skipped | Deselected | Exit | JUnit time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M1-1 through M1-5 focused headless | 137 | 0 | 0 | 0 | 4 | 0 | 6.280s |
| Product complement | 3,207 | 0 | 0 | 11 | 5 | 0 | 265.133s |
| Required compatibility supplement | 328 | 0 | 0 | 0 | 0 | 0 | 114.224s |
| Existing client + Designer GUI (`client/tests tests -m gui`) | 507 | 1 | 0 | 1 | 556 | 1 | 160.911s |
| Isolated keyboard-focus reproduction | 0 | 1 | 0 | 0 | 0 | 1 | 1.109s |
| Same unchanged case with actual X11 focus | 1 | 0 | 0 | 0 | 0 | 0 | 1.797s |
| Ruff, baseline archive | — | 0 | — | — | — | 0 | All checks passed |
| Ruff, final primary checkout including new qualification tools | — | 0 | — | — | — | 0 | All checks passed |
| Engine mypy | — | 0 | — | — | — | 0 | 102 source files |
| Client mypy | — | 0 | — | — | — | 0 | 19 source files |

Console durations are 6.29s, 265.48s, 114.24s, 160.97s, 1.11s and 1.80s
respectively. JUnit and console times measure slightly different boundaries.
No counts combine overlapping focused, GUI-reproduction or assisted selections.
The original failing GUI run is not relabeled as an all-green invocation.

The product complement accounts for the same **3,218** cases as Windows.
Exact node comparison finds only three expected parameter-ID differences in
packaged-launcher tests (`.exe` suffixes); normalization of that platform suffix
leaves no case difference. The supplement's **328** nodes match exactly and
have zero overlap with the complement.

The retained Windows module list excludes the pure-GUI
`test_linux_pygame_smoke.py`; thus this exact file-list invocation deselects
five GUI cases rather than the Windows directory-based run's seven. Both omitted
GUI cases ran in the separate Linux GUI selection. That selection includes all
seven Windows client GUI nodes and 502 root `tests/` cases. Its 556 deselections
are 550 client headless cases plus six root non-GUI cases. The only GUI skip is
the explicitly Windows-only native smoke; Linux native interaction is separately
proved by the unmocked workflow.

All 11 Linux headless skips are itemized in
[skips.json](evidence/m1_6b_linux/skips.json): six unset frozen-executable checks;
one NTFS junction check; one case-insensitive-store collision check; one Windows
installed-wheel path check; and two Windows Job Object lifetime checks.
Windows's eleven symlink-privilege skips, POSIX-only symlink case and NTFS colon
case run successfully here. Windows passed five cases that skip on Linux,
explaining the net change from 3,199/19 to 3,207/11.

The complement includes native match/replay/validation, stable-v4 defaults,
immutability/equivalence, compatibility readers, worker launching, parameter and
filesystem regressions. Focused coverage includes M1-1=42, M1-2=19, M1-3=30,
M1-4=21+8 adversarial, and M1-5 headless=17. The supplement includes the unchanged
E8 parent-byte/context/sensing/trace characterizations and required lifecycle
inventories, using the same authorized synthetic compatibility inputs as Windows.
It is not a research study, payoff campaign or private-seed operation.

Commands, selections, exit status and useful logs are preserved in
[the evidence packet](evidence/m1_6b_linux/README.md). The ordinary unpartitioned
full repository suite was not run or claimed green, consistent with the adopted
product-versus-research disposition. Original setup errors and interrupted runs
are separately retained in [attempts.json](evidence/m1_6b_linux/attempts.json).

## 9. Historical integrity and research isolation

Independent read-only hashing of Git blobs at
`b948540aa9ef34134ff7e3c633c3acfc9f97da96` matches **329/329 raw manifest pins**:
293 implementation and 36 qualification members, zero failures. No line-ending
reconstruction or re-blessing was needed. The current product archive remains
a distinct instrument and is not asserted to satisfy those old product-source
pins in its present role.

The adopted M1-1 historical execution remains 71 cases plus one separate existing
plugin case. It was not rerun on Linux and is not counted as new Linux evidence.
Current Linux compatibility/golden characterizations did run; the raw historical
Git pins were independently verified. No E9 execution was inferred from the
historical disposition.

The private Windows 1,384-file study and 1,447-file backup were not present in
this separate tracked-source archive. They were not copied, inspected or altered;
this report does not claim a new Linux verification of their private custody
inventories. No Windows checkout cleanup or evidence modification occurred.

Product isolation negatives pass. Qualification uses disclosed product fixtures
only; no research controller, private E9 seed, scientific entropy generation,
G consumption or authority event occurred. E9 execution remains **LOCKED**,
Requirement C remains **NOT ESTABLISHED**. Replay4, trace2 and result2 remain
unchanged. Stable-v4 default, historical readers and retired-execution rejection
remain intact.

## 10. Separate adversarial findings and bounded proposals

A separate adversarial self-review examined the completed evidence after the
native and regression campaigns. It compared exact test identities to Windows,
checked raw archive/pin digests, reviewed binding/source capture, verified observed
SDL states and process exits, and visually inspected actual Qt/viewer frames.
It also challenged claims of full cross-platform replay equality, historical
custody verification, default/capability preservation and independence from
research. This is a separate primary-agent review pass; no independent human or
subagent review is claimed.

| Finding | Minimal reproduction and evidence | Classification / bounded proposal |
| --- | --- | --- |
| L1: window activation prerequisite | Under bare Xvfb/xcb, run `tests/test_v5_replay_history_browser.py::test_keyboard_navigation_action_tab_order_and_filter_focus -m gui`; `focusWidget()` is None and tab-target set is empty. The same unchanged case passes after `xdotool windowfocus --sync` activates its actual X11 window. | RESOLVED qualification-environment issue. Ordinary native X11 activation supplies the missing prerequisite. No reproducible product defect remains in this finding; no assertion or production method was replaced. |
| L2: lower history text overlap | Open canonical teaching replay at 1100×750; advance to callback 2 receipt or tick 10 history. The full-width historical-sample footer crosses lower right-panel history text. Native D/G frames retain it. `draw_entrant` permits history through approximately y595 and paints the footer at y500. | Usability limitation requiring follow-up; NONBLOCKING for M1 acceptance. Track after M1: confine footer text to the arena width or reserve a separate row, preserving SensingView filtering and checking both platform fonts. No renderer repair or redesign was performed. |
| X11 resize window replacement | Resize live SDL window to 950×680; the old X11 ID is no longer focusable while the new window continues drawing. | Expected platform variation. Witness now rediscovers the window; no product change needed. |
| Original Windows raw artifacts absent | Published record provides facts/inputs, but no complete replay/trace bodies for direct comparison. | Unverified comparison beyond the documented equivalent facts/identities; no invented full record equality. |

### L1 final resolution: exact failure and unchanged pass

The exact test is
`tests/test_v5_replay_history_browser.py::test_keyboard_navigation_action_tab_order_and_filter_focus`.
The original traceback ends at line 1813 with
`assert {"Open Replay", "Copy Seed"} <= reached` and
`AssertionError: assert {'Copy Seed', 'Open Replay'} <= set()`.
The row-selection assertion had passed; the 50 Tab events never populated
`reached` because QApplication had no focused widget. The original GUI campaign
still records **507 passed, 1 skipped, 1 failed**; the isolated reproduction
records **1 failed**. Both logs and both failed JUnit records are preserved.

The qualification plugin observes return from the test's existing `_opened`
helper, issues `xdotool windowfocus --sync` against that widget's native window
ID, and processes events until `isActiveWindow()` is true. Its
[focus proof](evidence/m1_6b_linux/focus_assist.json) records `xcb`,
`focus_before=None`, `active=true` and a focused QLineEdit afterward. The proof
does not independently record an inactive flag before activation; the missing
focus, reproduced failure and single added activation stimulus establish the
prerequisite. The same unchanged test then passes all tab-order, clipboard,
launch-dispatch and filter-focus assertions: **1 passed**, separate exit 0.
The test's existing launcher mock remains part of that test; this result alone
does not establish native replay launching. The independent workflow does.
Final review confirms test/product bytes at the accepted baseline are unchanged.
L1 is closed as a resolved qualification-environment issue.

### L2 final assessment: affected text, controls and platform comparison

The overlapping footer is “Historical samples stay at their recorded address;
they do not track opponents.” In D, its tail crosses the start of the detailed
`Scan positive: center 91 +/- 27; anonymous` row. In G, it crosses the start of
`addresses (); process main; sampled t10 callback`, beneath the empty-scan row.
The footer's ending and these local detail fragments lose readability. At the
retained 950×680 terminal frame, it also meets the wrapped scan-history heading
tail. This is a real presentation limitation, rather than fully cosmetic.

The one-action cost, request/pending labels, primary historical contact 91,
sample/delivery callbacks and age, `Receipt now`, current phase, perspective
buttons, timeline, keyboard-control text and terminal outcome remain readable
in their dedicated locations. No input target is covered and event handling is
independent of these text blits. The native witness confirms stepping, seeking,
play/pause, perspective switching, resize and clean exit. Source inspection and
the retained wrapped rows show ordinary wheel scrolling moves the affected
detail away from y501 (D clamps to one row; G permits three). This scrolling
workaround is source-verified, not claimed as an additional native witness.

The unchanged Windows
[receipt frame](../screenshots/v6_alpha1_windows/C_delayed_receipt.png) and
[historical frame](../screenshots/v6_alpha1_windows/F_historical_knowledge.png)
use the same footer placement: the footer ends directly beside the `Scan`
text with inadequate separation. Linux's resolved Courier font extends farther
and visibly superimposes glyphs. The layout problem is shared and font-dependent;
the stronger Linux overlap is not evidence of different gameplay or a
Linux-only rendering path. Windows evidence is unchanged.

Classification: **Usability limitation requiring follow-up — nonblocking**.
The essential teaching information remains available and controls work; no
AC1–AC11 blocker remains. Recommend a post-M1 layout issue with D/G/I and the
existing Windows frames as witnesses, bounded to footer/history separation and
both platform fonts. No post-M1 work or issue publication was begun.

The review retains all limitations rather than treating screenshots, dispatch
attempts, overlapping runs or old Windows results as additional Linux tests.
[Machine-readable review](evidence/m1_6b_linux/adversarial_review.json).

## 11. Formal Linux disposition and remaining obligations

The required native Linux engine and X11/Xvfb Qt/SDL evidence passes within the
bounded contract. L1 is resolved and L2 is retained for nonblocking post-M1
tracking. Human desktop UX, Wayland, multiple Linux distributions, the full
supported Python matrix, wheel/frozen/installer acceptance, accessibility and
later alpha-wide scope were not undertaken. No release readiness is implied.

**M1-6B LINUX — FORMALLY CLOSED**\
**Qualification disposition: PASS**\
**Windows M1-6A: CLOSED — PASS**\
**Overall M1 Alpha 1 technical acceptance: READY FOR CONSOLIDATED PROJECT LEAD REVIEW**

No Linux acceptance blocker or further M1 platform campaign remains. The
remaining overall M1 obligation is the Project Lead's consolidated review of
both closed platform records and adoption of the bounded technical acceptance.
This does not grant unrestricted public release readiness or close later
alpha-wide obligations. The teaching-only seed exception, unresolved public
seed-closure prerequisite, E9 LOCKED state and Requirement C NOT ESTABLISHED
remain in force. Commit/push requires a separate instruction.

## 12. Evidence reproduction and preservation

The reusable qualification helpers are:

```text
tools/qualification/run_linux_native_workflow.py
tools/qualification/linux_observer/sitecustomize.py
tools/qualification/linux_focus_plugin.py
```

Use a fresh isolated Linux source/data environment at the specified baseline.
Set `BYTEFRAY_LINUX_QUALIFICATION_DIR` to a fresh isolated temporary root for
the native helper. Put the observer directory on the child
PYTHONPATH; use actual `xcb`/`x11` under Xvfb. The completed run resumed from
already verified engine artifacts after the documented setup fixes; its exact
executed source remains local-only, and the reusable helper preserves that control flow.

Exact campaign and helper invocations are retained in `*_command.json` and
`additional_commands.json` with local path prefixes normalized as described in
[publication review](evidence/m1_6b_linux/publication_review.json). Exact executed
orchestration source remains local-only and hash-bound; selections can be
inspected without launching excluded tests. For the focus-assisted reproduction,
load the qualification plugin only for the named keyboard test; it supplies
real native focus and leaves test/product code unchanged.

Raw ZIP members, logs, XML, source snapshots and invalidated attempts remain
unchanged in ignored local custody. Published JUnit omits hostname/captured
streams and normalizes local paths in skip messages; identities, timings,
outcomes and original focus traceback are preserved. Export records bind back
to originals. No passing campaign was rerun during final review.

## 13. Publication manifest and final verification

Every pre-existing tracked file, including accepted product source and Windows
qualification evidence, is unchanged. The additions are this report, the three
qualification helpers, and privacy-reviewed Linux evidence. The exact
[staging allowlist](evidence/m1_6b_linux/staged_manifest.txt) names every staged
file individually. [Changed files](evidence/m1_6b_linux/changed_files.txt)
records the complete qualification inventory, including local-only exclusions.
[Evidence hashes](evidence/m1_6b_linux/evidence_hashes.json) binds staged packet
members except itself. [Publication review](evidence/m1_6b_linux/publication_review.json)
records normalization, original digests and exclusions.

All 18 frames are authentic unchanged native captures; 16 passed visual privacy
review and are staged. Result frames 05/07 expose absolute temporary match paths
and remain local-only. The generated match ZIP and five exact executed-source
snapshots also remain local-only. Their hashes and artifact associations are
retained. No generated match data, temporary workspace, private study/backup,
credentials, local settings or sensitive path belongs to the allowlist.

Final review independently verified 66 original packet hashes, 1,668 archived
source files against a fresh archive of the published baseline, 329 historical
raw pins, all 22 ZIP members, replay/result/demo/trace bindings, complete source
capture metadata, equal repeated replay bytes and 16,000 equal logical trace
records. Original and exported JUnit identities/outcomes match. The focused
137 cases overlap the product selection; the 328 supplement has no overlap
with it; the two focus reproductions are the same original GUI node. No
aggregate total is asserted. Ruff and engine/client mypy outputs and commands
were verified from retained successful executions.

The allowlist is staged against
`5d6fc19e2b84805e0453da2c851f1ab0d7804f2f` on `v6-research`; staged blobs and
manifest agree, and `git diff --cached --check` passes. No pre-existing tracked
file is changed. E9 remains LOCKED; Requirement C remains NOT ESTABLISHED;
no new G consumption, research execution or authority event occurred. Nothing
was committed or pushed. Stop after final review and staging verification.
