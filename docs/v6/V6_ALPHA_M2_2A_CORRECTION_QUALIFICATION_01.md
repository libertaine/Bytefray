# Bytefray V6 — M2-2A correction and qualification 01

2026-10-15, America/Indianapolis. **Qualification evidence complete; recommendation
PASS WITH CONDITIONS (§Acceptance).** M2-2 technical acceptance remains HOLD until
the project lead explicitly accepts this package. M2-3 is not authorized.

The authorized correction permits explicit Alpha 1 in Development Test through
the existing supervised service. Stable V4 omission, whole-roster capability
preflight, retired refusal, execution semantics and error contracts are preserved.
The governing investigation, implementation record, Scope Revision03 and
Checkpoint B01 remain byte-identical. This report records the subsequent grant;
it does not rewrite their historical approval language.

## Entry and exact correction boundary

Verified checkout/branch: `D:/Projects/BATTLE2/work/v6-m2-clean` / `v6-m2-clean`.
HEAD `f79a74be1d486f042d260bea672305b9abb27aa5`, tree
`d4f2c73cbd3965762e61316567537e173503ff8a`. Index SHA-256 remains
`b77a600d7e0c4e5679798a787e0b392b9994a5ae95a5b8841c4f0192bf6ee00b`;
the staged diff is empty. Recorded upstream remains `origin/v6-research` at
HEAD. No fetch or current live-remote parity is claimed.

All 23 investigation entry inputs matched before editing. The new entry receipt
preserves 26 files, including the investigation report and the two previously
unchanged CLI files. Final preservation checks permit changes only to the three
authorized paths below. The other 23 entry files, all prior diagnosis and
implementation evidence, product refs and historical manifest bodies remain
unchanged. Three entry ref differences were reconciled as automatic
`refs/codex/turn-diffs/*` capture/checkpoint bookkeeping; no product ref moved.

| Exact changed path in this correction | Change |
| --- | --- |
| `engine/src/battle_engine/agent_test.py` | Import the existing Alpha 1 constant; parser choices exactly V4 and Alpha 1; stable-default/explicit-experimental help and corrected adjacent comment. No execution-service change. |
| `engine/tests/test_agent_test.py` | Real supervised command acceptance for personal Keeper/Scout and explicit Keeper opponent; stable artifact identity; both-seat preflight sentinels; malformed/retired/incompatible refusal; exact parser/help surface. The help case is renamed and strengthened. |
| `tests/test_v6_alpha_m1_5_designer.py` | Retain both Keeper seat cases; verify Test's canonical result/defaults/trace/replay association and prior Advanced results. Add native Scout Test regression. All GUI cases remain GUI-marked. |
| `docs/v6/V6_ALPHA_M2_2A_CORRECTION_QUALIFICATION_01.md` | This completion package. |

No other repository source/test file was changed by this correction. Inherited
Keeper implementation and unrelated work remain separate from this change list.
No worker, sensing mechanic, policy, registry, schema, reference opponent or second
ruleset-selection mechanism was changed.

The [exact correction-only diff](evidence/m2_2/qualification/correction_only.diff)
(published byte copy of local `runs/v6_alpha_m2/m2_2a_20261015_correction/correction_only.diff`)
compares the three source/test files with their preserved entry bodies, including
the pre-existing Keeper GUI additions. `candidate_full.diff` separately records
the entire tracked dirty candidate against HEAD. Raw source hashes and exact
post-correction bodies are retained in `corrected_source_manifest.json` and
`corrected_files/`.

## Campaigns and commands

Evidence root:
`runs/v6_alpha_m2/m2_2a_20261015_correction/`.
Each pytest campaign retains a distinct log, JUnit and `*_command.json`, with
expanded argv, cwd, interpreter, environment, result and elapsed time. The local
`run.py` executes `python -m <tool>`, records and propagates the real exit code.
Windows pytest invocations were sequential. Every invocation uses a fresh,
absolute checkout-local basetemp/cache outside runs/evidence. No retained
scratch was reused as a new pytest input; pytest.ini is unchanged.

| Final campaign / artifact prefix | Selection | Result |
| --- | --- | --- |
| `m2_2a_focused_final` | `pytest engine/tests/test_agent_test.py @runs/v6_alpha_m2/m2_2_20261015_review/qualification/m2_2_focused_selection.txt` | **619 passed, 4 GUI deselected**, 57.53s; Windows/Python 3.13.7 |
| `m2_2a_windows_gui_final` | Both Keeper native GUI seat cases, new Scout native Test, existing Windows window/parameters case; explicit `-m gui` | **4 passed**, 9.61s; native Qt windows and real QProcess children |
| `m2_2a_m1_gui` | Existing Scout authoring/repeat case plus M1 adversarial Designer module; `-m gui` | **5 passed**, 3.89s; offscreen supplemental state evidence |
| `m2_2a_windows_broad` | Exact retained 137-module product selection in `m2_2_broad_selection.txt` | **3,374 passed, 20 skipped, 5 GUI deselected**, 315.79s; native process-observation context |
| `m2_2a_windows_supplement` | `pytest @docs/v6/evidence/m1_6a_windows/supplemental_nodes.txt` | **328 passed**, 97.98s; separate compatibility campaign |
| `m2_2a_linux_focused` | Same 23-module focused selection as Windows, including the CLI module | **619 passed, 4 GUI deselected**, 331.91s; Ubuntu/WSL2/Python 3.12.3 |
| `m2_2a_linux_gui_x11` | Both Keeper native GUI seat cases and Scout Test; explicit `-m gui` | **3 passed**, 31.43s; native Qt xcb on X11 |
| `m2_2a_ruff` | `ruff check .` | **PASS** |
| `m2_2a_mypy_engine` | `mypy engine/src/battle_engine --cache-dir=.pytest-cache/m2_2a_mypy_engine` | **PASS**, 104 source files |
| `m2_2a_mypy_client` | `mypy client/src/battle_client --cache-dir=.pytest-cache/m2_2a_mypy_client` | **PASS**, 19 source files |

Counts overlap and are not added. No unrestricted repository-wide or all-platform
broad-suite claim is made. The Windows broad campaign has 3,394 executed/skip
nodes. Relative to the original failed campaign, the ledger identifies 39 added
names and one replaced help-test name: net +38, comprising 34 new CLI cases and
four previously focused-only Keeper output-safety cases. No substantive prior
node was removed. All 20 skip nodes/reasons are unchanged after normalizing only
their fresh scratch-directory labels. The five GUI deselections remain explicit.
The prior M1-to-M2 selection ledger remains preserved and still explains the
inherited baseline changes.

Focused anchors cover M1 capabilities, Scout, sensing/provenance/core capture,
starter/scaffold/validation/refresh, V4 equivalence/historical readers and client
session/playback/perspective/adversarial filtering. Negative CLI cases assert
that both entrants' import/reset sentinels and output directories remain absent.
Positive cases use actual workers and inspect result2/replay4/trace2, integrity,
ruleset, canonical defaults and legitimate completion. No successful integration
case mocks the service. Existing death/loss/forfeit/init-failure exit checks pass.

## Worker disposition and preservation

Worker production and tests are byte-identical to the clean HEAD export. The
investigation's original full native worker module remains **16 passed**; its
native candidate and baseline isolated node each passed. Original sandbox
candidate/baseline failures retain the pre-kill liveness assertion and denied
`tasklist` observation. Those failures are not relabeled as successful execution.

The corrected-candidate broad native campaign independently passes all **16
unchanged worker cases**, including the hard-parent-kill regression. No new
native evidence contradicts the diagnosis. The specific Windows service/ACL
responsible for sandbox denial remains unidentified. No timeout increase,
worker patch, skip, xfail or assertion replacement was used to clear that gate.

The static preservation audit rechecks **293 implementation plus 36 qualification
raw pins** at preserved `b948540aa9ef34134ff7e3c633c3acfc9f97da96`. It does not
require evolved product source to match that historical scientific instrument.
All old starter raw files and current/superseded digests match the HEAD export;
old ordering and terminal `v5_dual_team` are retained. Focused refresh tests
also preserve customized copies. No scientific controller, entropy operation,
source-pin reseal or private-evidence modification occurred.

## Native scenarios, controls and platform comparison

The original four complete Windows Keeper demonstrations remain unchanged and
are reused: a parser-only correction changes none of their captured agent/fixture,
runtime, verifier or fixed inputs. Four new Linux demonstrations completed,
twice per Keeper seat, at arena512/Q8/seed0/100 ticks, fixed starts0/91 with full
role reversal and default parameters4/27. Each retains replay/trace/result,
common demo-v1 sidecar and both executed source snapshots.

`cross_platform_comparison.json` independently verifies Keeper completion on all
eight bodies and equality within each seat across repeats/platforms: every parsed
replay record, ordered trace excluding only `wall_time_ms`, and declared result
gameplay/stable-identity fields. Occurrence UUIDs/completion timestamps remain
separate provenance. Every raw body is independently hashed; no raw result/trace
or cross-engine equality is inferred. Both entrants remain alive at tick100.
Keeper repair/defensive witnesses agree: seatA `(3,24)` / `(1,8)`, seatB `(1,6)` /
`(1,10)` in `(tick, zero-based global decision index)` coordinates.

### Complete native authoring and external replay workflow

`native_workflow.py` drives, per Keeper seat, the real Designer: New Agent Keeper
copy, stable-V4 Validate capability refusal, explicit Alpha 1 Validate, edited
parameters 3/64, full 100-tick Advanced match and result verification, then the
actual external viewer from that result; then manifest-default Development Test
(4/27, Alpha 1, prior Advanced result retained) and the actual viewer through the
Development tab's Open Test Replay button. Real QProcess children, launcher and
SDL windows; input is Win32 messages or XTest via `xdotool` with explicit
`windowfocus`. Per viewer it verifies: launch target, initial reconstruction
(first draw), unknown/empty contacts at Home, phase step forward/back, speed
+/-, play/pause, keyboard (`1`, `v`, `2`) and mouse perspective switching, End
terminal state, wheel scroll, resize to 900x650/1000x700/1100x750, mouse
timeline seek, Home restart and Escape with exit status 0. The passive draw
witness (`observer/sitecustomize.py`) records rendered state only.

| Run | Viewers | Result | Initial reconstruction (first draw) | View switch | End |
| --- | --- | --- | --- | --- | --- |
| `windows_native_complete` | A/B Advanced, A/B Test | **PASS**, both seats' authoring and all four viewers; exit 0 each | Advanced 3.2–3.7s; Test 40.0/41.9s | Advanced 0.5–0.7s; Test 5.8–6.4s | 0.09–0.18s |
| `linux_native_complete` | A Advanced PASS; A Test **INCOMPLETE** | Harness AssertionError at End (below); seat B not reached | Advanced 3.6s; Test 31.8s | Test 4.6–4.9s, all four completed | no state change in 120s |
| `linux_end_probe_01` | Retained A Test replay, Designer's exact argv, direct launch | **PASS**, full sequence; exit 0 | 30.4s | 4.3–4.5s | 0.19s |
| `linux_native_complete_02` | A/B Advanced, A/B Test | **PASS**, both seats' authoring and all four viewers; exit 0 each | Advanced 3.3/3.4s; Test 30.3/30.6s | Advanced 0.4–0.6s; Test 4.3–4.6s | 0.07–0.17s |

Linux: Ubuntu WSL2 kernel 6.6.87.2, Python 3.12.3, PySide6 6.12.0 (xcb),
pygame-ce 2.5.8/SDL 2.32.10 (x11) on WSLg `DISPLAY=:0`, viewer font DejaVu Sans
Mono. Windows: Python 3.13.7, native Qt/SDL `windows`, viewer font Consolas.
Linux key witness records 17 delivered keys per viewer in both later runs. Test
replays end at index 3396, "Recorded end: winner B; tick_limit", on both
platforms. Frames are rendered Qt widget grabs or Pygame surfaces (Linux) and
`grabWindow` captures (Windows; desktop pixels outside the DPI-scaled client
area appear at the right/bottom edge and are a capture-region artifact).
Reconstruction cost (30–42s Test load, 4–6s per Test perspective switch,
dominated by `copy.deepcopy` in `sensing.py` per retained stacks) is latency
under the accepted M1 rewind-reconstruction limitation, not malfunction.

## Original and subsequent failures retained

The original implementation's failed broad/GUI campaigns and investigation's
sandbox/baseline/native evidence remain untouched, with entry-to-exit raw hashes.
New attempts remain separate:

- `m2_2a_cli_01`: 121 passed/7 failed. New test-harness errors used a second
  positional integrity argument and expected kind rejection instead of manifest
  rejection for the invalid literal kind `vm`. Expectations were corrected to
  the existing API and established diagnostic; production rejection was intact.
- `m2_2a_cli_02`: 125 passed/3 failed. New tests used `ticks_run` instead of the
  canonical result field `ticks`. The corrected focused run validates that field.
- `m2_2a_windows_gui`: 3 passed/1 failed. Scout test omitted Advanced-tab/ruleset
  setup before inspecting its parameter controls. Corrected native GUI run passes.
- Linux setup logs retain a stale apt URL404, missing local libraries and failed
  Xvfb keyboard initialization; the first Linux GUI process aborted before test
  outcomes. X11 qualification uses existing WSLg with Qt xcb/SDL x11 instead.
  Dependencies were installed/extracted under ignored `work/`; no system packages
  were installed to force the failed isolated display to work.
- `windows_native_01` through `windows_native_04`, resize probes and
  `linux_native_x11_01` through `linux_native_x11_03` retain harness timeouts,
  partial interaction records and authentic original frames. Windows coordinate
  conversion initially omitted desktop DPI scaling. Initial compositor grabs
  under WSLg were black and are not accepted visual evidence. Later Linux frames
  use actual Qt widget/native Pygame rendered surfaces, with capture method stated.
- `windows_native_final` / `linux_native_final` retain successful Test launches
  after longer loading waits, followed by view-switch waits expiring. The original
  all-function profiler added substantial reconstruction overhead. The subsequent
  harness observes only draw returns through Python monitoring once the renderer
  starts; it supplies no input or replacement product function. Native controls
  continue to come from Win32 messages or XTest/QTest.
- `linux_native_complete` (the run open when the prior session was interrupted)
  **did not complete**. Seat A Advanced passed. The Test viewer (pid 457) launched
  through Open Test Replay, reconstructed (first draw 31.8s) and completed Home,
  step, speed, play/pause and all four perspective switches; the harness then sent
  `End` and raised `AssertionError: Viewer timeout` after 120s with the last state
  at index 10, Entrant view, paused. Seat B was never reached. The witness writes
  only on rendered-state change, so the silence shows that End took no visible
  effect; it cannot distinguish an undelivered/unprocessed key from a stalled
  viewer. That run predates the key witness and did not record the viewer's exit
  status. When this session resumed, WSL was stopped and no harness, viewer or
  worker process remained on either platform. End is a single seek to the last
  position and cost 0.07–0.19s in all ten other latency-measured viewers (six
  Linux, four Windows), including the same replay and argv in
  `linux_end_probe_01`; earlier Linux Advanced runs also passed End. The
  non-response was not reproduced and its cause is **unidentified**; it is
  retained as a qualified nonblocking observation, not relabeled as a PASS.
- `linux_view_diagnosis` (prior session, 11:14): bounded load/perspective probe
  on that replay with periodic `faulthandler` stacks; loaded, switched Omni and
  Entrant, exited 0. Stacks place load and switch time in `copy.deepcopy`.

Local audit tooling also retained two reconciliation corrections: the replaced
help-test name and dynamic scratch text in two unchanged symlink skip reasons.
Read-only historical Git inspection used a command-local safe-directory exception,
without changing global Git configuration. No product assertion was weakened.

## Resumption audit (interrupted session)

The prior session ended while `linux_native_complete` was open. On resumption no
broad campaign was relaunched. Two new bounded runs were added under new labels:
`linux_end_probe_01` (`linux_end_probe.py/.sh`) and `linux_native_complete_02`
(`linux_native_complete_02.sh`, unchanged `native_workflow.py`). Both used
`timeout` bounds and the passive observer as it stood after the prior session's
final edit, which added only a delivered-key record and opt-in `faulthandler`
stacks; Windows `windows_native_complete` ran with the earlier observer body.

`resume_readonly_verify.py` recomputes, without writing to the repository:
HEAD/branch/index SHA-256 and empty staged diff; all 26 manifest bodies; the 23
non-correction entry files unchanged; changes since entry limited to the three
authorized paths; `candidate_full.diff`, `correction_only.diff` and
`corrected_files/` byte-identical to the current tree; prior diagnosis (102) and
implementation (161) evidence bodies unchanged; worker files equal to the clean
HEAD export; only `refs/codex/turn-diffs/*` refs moved; 329 historical pins at
preserved `b948540...`; 23 old starter files unchanged; and no pre-resume
evidence file written after 11:15. All pass (`resume_readonly_verification.json`).
Its single FAIL line is scope-only: this completion record is not in the source
manifest by design.

Final candidate mtimes order every retained PASS campaign after the bodies it
qualifies: `agent_test.py` 10:41:57 and `test_agent_test.py` 10:45:19 precede
focused-final (start 10:45:50); `tests/test_v6_alpha_m1_5_designer.py` 10:49:16,
module-level `gui`, appears in no focused/broad selection and precedes
`m2_2a_windows_gui_final` (10:49:19), Linux GUI and M1 GUI runs; Ruff/mypy
(11:02:49) follow all edits. No source has changed since, so Ruff, mypy and
pytest campaigns were not rerun.

The 27 dirty paths (14 tracked modified, 13 untracked) are: the 16-file Keeper
candidate, which includes `tests/test_v6_alpha_m1_5_designer.py`; the seven
inherited files; the investigation report; the two previously unchanged CLI
files; and this record. Only the three authorized paths differ from entry.
Sensing playback/demo changes belong to the unchanged Keeper candidate; the
correction touches no sensing, ruleset, worker or policy module.

## Acceptance mapping and recommendation

| Gate | Disposition / evidence |
| --- | --- |
| B2-01 / affected AC01 | PASS: explicit Alpha 1 CLI/native Test; stable defaults; both-seat capability/manifest preflight, unsupported/retired/parser refusal |
| B2-02/03 / affected AC02/04 | PASS: unchanged 48 Keeper behavior/negative cases and both-seat native scenario witnesses |
| B2-04 / affected AC05/10 | PASS: four retained Windows plus four Linux complete demonstrations and same-build/cross-platform logical comparisons |
| B2-05 / affected AC05 | PASS: existing provenance/false-success/fallback/Scout/capture coverage in both focused selections |
| B2-06 / affected AC06 | PASS: native GUI nodes (Windows 4, Linux 3) plus complete unmocked authoring and external replay-control workflow, both seats, `windows_native_complete` and `linux_native_complete_02`. `linux_native_complete` INCOMPLETE retained |
| B2-07 / AC09 | PASS: final product and separate compatibility campaigns; exact node/skip ledger and starter preservation |
| B2-08 / AC12 | PASS: Ruff, separate mypy, source/index/ref/input/evidence preservation and 329 historical pins; rechecked read-only at resumption |
| B2-09 | OPEN: project-lead acceptance of this package; no automatic M2-3 entry |

**Recommendation: PASS WITH CONDITIONS** for M2-2 technical acceptance, effective
only on explicit project-lead acceptance (B2-09). Conditions:

1. The unreproduced `linux_native_complete` End non-response stays an open,
   unidentified nonblocking observation. M2-5 Linux platform qualification
   keeps the delivered-key witness active and records viewer exit status on
   timeout; any recurrence is treated as a potential product defect.
2. Arena-panel historical-sample marker labels overlap into illegible text in
   long Test replays at terminal state on both platforms (`*_test_terminal`,
   `*_test_900` frames); the history column remains readable. This is
   existing renderer behavior outside the M2-2/M2-2A boundary and is carried to
   M2-4/M2-5 under M2-AC08, not fixed here.
3. Acceptance covers the Keeper slice only: no M2-wide technical PASS, no M2-3
   entry, and no human-comprehension claim (AC11/M2-6 remain unexecuted).

M2-wide A/B/Omni selector/layout work remains M2-4/M2-5; human comprehension
remains M2-6. Accepted M1 history/footer overlap and rewind reconstruction cost,
Windows COM `0x8001010d`, the unidentified Windows ACL behind the sandbox
`tasklist` denial, Linux focus assistance and teaching-only Python threat model
limitations remain disclosed. Linux qualification is WSL2/WSLg X11 with
user-local libraries; Xvfb was attempted and failed keyboard initialization. No
Wayland-client, bare-Xorg, other Linux distribution, full Python matrix,
installer, release or human-evaluation PASS.

No staging, commit, merge, push or release occurred. M2-3 was not started.
Original E9 remains execution LOCKED; Requirement C is NOT ESTABLISHED.
