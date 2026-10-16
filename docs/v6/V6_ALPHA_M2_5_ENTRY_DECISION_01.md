# Bytefray V6 — M2-5 Technical and Platform Qualification Entry Decision Packet 01

2026-10-15, America/Indianapolis. **Read-only planning review. M2-5 is NOT
AUTHORIZED; no M2-5 campaign, collection, native run or measurement has been
made.**

**Recommendation: READY FOR AUTHORIZATION**, subject to two prerequisites:

1. publish M2-4 first, so that the frozen candidate is a commit (§2); and
2. the grant resolves the project-lead decisions in §14. P1–P4 are required
   before any campaign; P5–P10 may be answered with the defaults stated there.

No product code change is needed to enter or run M2-5. §13 lists amendments
that particular findings could make necessary; none is authorized.

## 1. Basis

Governing contract: [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md) §10
(compatibility, qualification and research isolation) and §11, whose M2-5
milestone row reads:

> Entry: accepted code slices, explicit campaign grant, frozen
> candidate/source/input/selection manifest and safe roots. Deliverables: AC01–10/12
> technical dispositions, approved product/compatibility partitions, integrity
> evidence and affected native Windows/Linux workflows; no missing required
> platform gate. Stop: semantic regression, mutated historical evidence, unknown
> exclusions, source/input drift, missing source/artifact bodies or unusable
> controls.

Accepted slices: [M2-2 Closure 01](V6_ALPHA_M2_2_CLOSURE_01.md),
[M2-3 Closure 01](V6_ALPHA_M2_3_CLOSURE_01.md) and
[M2-4 Closure 01](V6_ALPHA_M2_4_CLOSURE_01.md), each PASS WITH CONDITIONS.
Carried conditions: M2-2 C1–C3, M2-3 L1–L5 and M2-4 D1–D3, with status in
[M2-4 Closure 01 §7](V6_ALPHA_M2_4_CLOSURE_01.md#7-conditions-carried-forward).
Each slice closure satisfied only its affected subset of criteria. M2-5 must
give a technical disposition for M2-AC01 to AC10 and AC12 on the frozen M2
candidate as a whole. M2-AC11 belongs to M2-6.

## 2. Frozen candidate and identities

**Candidate.** The M2-4 publication commit on `v6-m2-clean`, parent
`e7c0f9de1f08f7c6494c36f2b4cc77850fad912f`, after its fast-forward to
`origin/v6-research`. Its tree must equal the tree of the validated M2-4
publication manifest, which is reported with the publication request. Code and
test bytes are those of [M2-4 Closure 01 §3](V6_ALPHA_M2_4_CLOSURE_01.md#3-accepted-change-manifest);
the commit adds only documents and the curated evidence package.

If the lead prefers to qualify before publication (P1), the candidate is
instead the uncommitted tree bound by a new source freeze, as in M2-2 to M2-4.
That works, but every M2-5 artifact would then bind a working tree rather than
a commit.

**Entry recheck (first M2-5 step).** HEAD equals the candidate; a live
read-only `git ls-remote` equals HEAD; nothing is staged; no tracked or
untracked change outside git-ignored roots; local `v6-research` still at
`2fc3c82e115650b515a4efab39afb172b62535ed`; the contract bytes below unchanged;
and the 329 historical pins verified at preserved
`b948540aa9ef34134ff7e3c633c3acfc9f97da96`.

| Identity | Value |
| --- | --- |
| Contract / gates | Scope Revision 03 `1b3e507a…16eba`; Checkpoint B 01 `29e3883a…f786` |
| Engine tree | Byte-identical to `e7c0f9d` (M2-3 accepted engine) |
| Client and Designer code | The eight M2-4 bodies in M2-4 Closure 01 §3; the rest of `client/` and `app/` as at `e7c0f9d` |
| Starter content digests | `v6_window_scout` `9d8a90ff209c2a9f13d5f3615cc67923204a095fdde6de9e183ca4ef8be10ce7`; `v6_watchful_keeper` `35b945ad33f34168ea4374dad05fa61fe5b20d08cc15ca2e9af293ebb0c8016e`; `v6_roaming_reacquirer` `65866988dd2dfdddd9782a8040d932dc84f05cec9b5d6feab3fb6a73c9697f21`; all other starters as `CURRENT_STARTER_DIGESTS` |
| Fixture content digests | `v6_stationary_opponent` `b705a7e0d08d0f5f40de84f2a49163a5e4dac07ddad09dc770212ed9ba86f513`; `v6_encroaching_opponent` `42763e704cc723e435af2f2822d90ad972c4cbdea8e3ada8322d6b07f8f24456`; `v6_relocating_opponent` `d5331833880756a98ea952b98a6c849c4c04234b46b5271a252bb771339a6ddd` |
| Published scenario bodies | `docs/v6/evidence/m2_2/keeper/seat_{A,B}/` and `docs/v6/evidence/m2_3/reacquirer/seat_{A,B}/`, bound by their evidence indexes |
| Fixed C2 input | `98edb90d…` replay, `47268aa8…` trace, `62003072…` result (local, M2-4 Closure 01 §2) |
| Selections | [`m2_3_broad_selection.txt`](evidence/m2_3/qualification/m2_3_broad_selection.txt) plus `client/tests/test_v6_alpha_m2_4_views.py` (139 modules); [`m2_2_focused_selection.txt`](evidence/m2_2/qualification/m2_2_focused_selection.txt) plus the M2-4 focused additions; the M1-6 [Windows](evidence/m1_6a_windows/README.md) and [Linux](evidence/m1_6b_linux/README.md) manifests |
| Windows environment | Windows 11 AMD64; `.venv` Python 3.13.7; pygame-ce 2.5.8 (SDL 2.32.10); PySide6 6.11.2; Consolas |
| Linux environment | Ubuntu on WSL2 (kernel 6.6.87.2); `work/m2_2a_linux_env` Python 3.12.3; pygame-ce 2.5.8; PySide6 6.12.0 xcb; user-local X11 libraries in `work/m2_2a_linux_x11`; WSLg `DISPLAY=:0`; DejaVu Sans Mono |

A change to any of these after the entry recheck is drift, and a stop condition
(§11) unless the lead disposes of it.

## 3. Acceptance criteria and required evidence

| Criterion | Evidence M2-5 must hold | Source |
| --- | --- | --- |
| **M2-AC01** capability | Valid blocks, malformed/unknown/duplicate rejection, explicit Alpha 1 success, stable-V4 mismatch before import/reset/artifacts on CLI, worker, validation, Development Test and direct routes | Reuse engine modules in the focused and broad selections (engine identical); fresh Designer-route checks in the native workflow (F-5), because `app/views/development.py` changed |
| **M2-AC02** K1 behavior | Priority, cadence, parameters, core-relative and seeded behavior; READ→repair and SENSE→defensive witnesses in both seats; negative feedback | Reuse the Keeper module (48) and the K1 runs (P2) |
| **M2-AC03** R1 sequence | Full R1→R8 sequence in both seats without identity or notification inference | Reuse the Reacquirer module (56) and the eight R1 runs |
| **M2-AC04** data sources | Source audit and trace assertions for both agents; every feedback class and cost | Reuse (engine identical) |
| **M2-AC05** verdicts | Separate consistency, reconstruction, capture, scenario and view verdicts; both predicates and negatives; four runs per new pairing per platform; Scout unchanged | Reuse (P2 for K1); plus a read-only re-verification of the curated K1/R1 copies with the trusted verifiers |
| **M2-AC06** authoring | Copy → explicit Alpha 1 validation → valid edit → full Advanced match → result-associated reopen; range/type rejection; stable-V4 rejection; overwrite refusal; earlier-settings access; safe install/refresh/customization; both starters, both seats | **Fresh native Designer workflow on both platforms** (F-5) plus the root Designer GUI suite (F-1) |
| **M2-AC07** symmetric views | A/B payload, timing, history, navigation, pacing, terminal, fallback and hidden-divergence checks | Reuse the M2-4 module results (37 nodes on both platforms at candidate bytes); **fresh native A/B/Omni confirmation** (F-4, §8) |
| **M2-AC08** usable text and controls | All three sizes, long histories, all views, both platform fonts, retained native interaction evidence; C2 native before/after; M1 overlap confirmed | **Fresh native viewer qualification on both platforms** (F-4); D3 checks (F-7) |
| **M2-AC09** compatibility | Product and compatibility selections; V4/default/reader/retired/starter/capture checks; historical artifacts and pins at their baseline | Windows broad and supplement reused; **Linux broad (F-2) and supplement (F-3) fresh**; **client and root GUI selections fresh on both platforms** (F-1); fresh pin check |
| **M2-AC10** platforms | Independent Windows/Linux execution; retained inputs, bodies, sources and environment; same-build and cross-platform logical comparisons; failures retained | Reused scenario comparisons; fresh campaigns on both platforms; logical comparison of the F-5 workflow artifacts across platforms |
| **M2-AC12** provenance | Exact source and contract provenance; safe temp and output roots; research isolation; unchanged authority; no publication or release claim | Fresh entry recheck, custody records and preservation audit |

## 4. Retained evidence eligible for reuse

**Eligibility rule.** Retained evidence may be reused only if (a) every product
source that the evidence exercises is byte-identical between its source freeze
and the frozen candidate, (b) its inputs are identical, (c) it ran on the same
platform class and environment identity as §2, (d) its bodies and hashes are
retained, and (e) no open failure or disposition rests on it. Reuse is
established by an identity check, not by rerunning. Previously accepted
campaigns are not rerun automatically.

| Evidence | Platform | Bound at | Eligible for | Basis |
| --- | --- | --- | --- | --- |
| Eight R1 runs and `cross_platform_comparison.json` (M2-3) | Windows, Linux | `e7c0f9d` engine | AC03, AC05, AC10 | Engine identical; executed sources identical |
| Eight K1 runs (M2-2) and the M2-3 K1 bridge (one repeat per seat per platform at the `e7c0f9d` engine; replays byte-equal to the published M2-2 bodies) | Windows, Linux | M2-2 engine, bridged | AC02, AC05, AC10 | **Decision P2.** Keeper and fixture sources unchanged; `sensing_demo.py` and `sensing_playback.py` gained the R1 code after the M2-2 runs |
| Scout characterization in the focused selection | Windows, Linux | M2-4 freeze 05 | AC05, AC09 | Candidate code identical |
| M2-4 `m2_4_views_05`, `m2_4_client_sensing_05`, `m2_4_focused_05` | Windows, Linux | Freeze 05 | AC01–AC05, AC07, AC09 (focused level) | Candidate code identical |
| M2-4 `m2_4_broad_05` (139 modules, 3,472 passed, 21 skipped) | Windows | Freeze 05 | AC09 | Candidate code identical |
| `m2_3_supplement_final` (328 compatibility nodes) | Windows | `e7c0f9d` engine | AC09 | Supplement exercises engine modules only; engine identical |
| M2-4 `m2_4_windows_gui_05` (8 Designer nodes) | Windows | Freeze 05 | AC06 (test level) | Candidate code identical |
| M2-4 Ruff and both mypy runs | Windows | Freeze 05 | AC12 | Candidate code identical; recheck by identity |
| M2-4 C2 offscreen probes (freeze 05) | Windows, Linux | Freeze 05 | C2 automated assertion | Candidate code identical |
| `linux_native_04` | Linux | Freeze 05 | Supporting evidence for AC07/AC08 | Supplementary by Q4; not a substitute for F-4 |
| M2-2 native "before" frames (`windows_native_complete`, `linux_native_complete_02`) | Windows, Linux | Client unchanged from `f79a74b` to `e7c0f9d` | C2 native "before" | Same pre-correction renderer |

**Not eligible**, so covered by fresh work: `windows_native_03` (freeze 04
renderer); the M2-2A native authoring workflows and M2-3 Linux Designer GUI
nodes (Designer and client changed since); the M1-6B Linux product regression
and supplement (M1 engine); any evidence whose bodies are not retained.

## 5. Required fresh campaigns

All run on the frozen candidate under a new root such as
`runs/v6_alpha_m2/m2_5_<date>/`, with fresh pytest roots (§9).

| ID | Campaign | Windows | Linux |
| --- | --- | --- | --- |
| S-0 | **Selection manifest.** Collect-only enumeration of the product complement, compatibility supplement and every `gui` node in `client/tests` and `tests/`; reconcile with the M1-6 manifests, the M2-2/M2-3/M2-4 additions and the capture-regression modules; account for every new or removed node and marker. Unexpected exclusions need a recorded disposition before any campaign | Required | Required |
| F-1 | **Explicit GUI selections:** `client/tests -m gui` and `tests/ -m gui` (root Designer suite) | Required | Required |
| F-2 | Product broad (139 modules) | Reused (`m2_4_broad_05`) | **Required (never run in M2)** |
| F-3 | Compatibility supplement (328 nodes) | Reused | **Required (last Linux run was M1-6B)** |
| F-4 | Native viewer qualification (§6.1) | Required | Required |
| F-5 | Native Designer authoring and replay workflow (§6.2) | Required | Required |
| F-6 | Replay performance ([Protocol 01](V6_ALPHA_M2_5_REPLAY_PERFORMANCE_PROTOCOL_01.md)) | Required | Required |
| F-7 | Bounded accessibility checks (§7.2) | Required | Required |
| F-8 | Integrity: entry recheck, preservation audit, 329 pins, read-only verifier recheck of the curated K1/R1 copies, Ruff/mypy identity check | Required | Linux verifier recheck only |

**Why F-1 is required on both platforms.** The product broad selection contains
no root `tests/` module. The published M1-6A record lists 7 client GUI nodes
on Windows; the 502 root-suite GUI nodes appear only in the published M1-6B
Linux record. In M2, only `tests/test_v6_alpha_m1_5_designer.py` ran, although
`app/views/development.py` changed in M2-2, M2-3 and M2-4. This is a concrete
coverage gap under Scope Revision 03 §10 ("GUI cases … are invoked explicitly,
including root tests/"), not a rerun of an accepted campaign. The X11 focus
prerequisite applies on Linux; M1-6B's activation plugin is the precedent.

## 6. Native viewer and Designer workflows

Native harness changes are test tooling, not product changes: resolve the real
viewer PID behind the `.venv` launcher; use `SendInput` with the viewer focused
for modifier keys on Windows; keep `xdotool` with explicit `windowfocus` on
X11; visit sizes in descending order from 1100x750 on the portrait Windows
display; record every viewer's exit status, including after a timeout; and
retain the delivered-key witness for every run.

### 6.1 Native viewer (F-4)

Inputs: the C2 replay (I3), the published Keeper bodies in both seats and the
published Reacquirer bodies in both seats. For each input, on each platform:

1. Launch through `battle_client.cli` exactly as the Designer does; record
   launch time to visible window (Protocol 01 P3).
2. **C1 witness:** press End; record delivered key, latency and the new state.
3. Keys 2/3/1, V/P cycle (Omni→A→B→Omni) and selector clicks.
4. At the recorded end, A, B and Omni at 900x650, 1000x700 and 1100x750:
   surface frame plus layout check (labels, omitted labels, label pairs,
   escapes, labels on glyphs, text pairs, clipping) and, per P5, an OS-level
   capture. This supplies the native C2 "after" and the M1 overlap
   confirmation.
5. Wheel scroll of the history; Help on and off by `?` and Shift+/; Help scroll.
6. Home, Left/Right, Shift+Left/Right, Space play/pause, +/- speed, timeline
   click and drag seek, window-manager resize.
7. `--perspective B` and `--perspective omniscient` launches.
8. Fallback launches on fresh copies: no trace, a corrupted trace, a mismatched
   result, and an invalid `demo.json` with a valid pair (expected: delivered
   views kept).
9. Escape; exit status 0.

### 6.2 Native Designer workflow (F-5)

For each starter (Watchful Keeper, Roaming Reacquirer) and each seat, on each
platform, in the Python-launched Designer with a fresh data root:

1. Find the starter; create "— personal copy" through New Agent.
2. Explicit `bytefray-rules-6-alpha1`; Validate; a valid parameter edit;
   range-invalid and type-invalid rejection; stable-V4 rejection before import;
   overwrite refusal.
3. Full Advanced match in the declared seat; open its replay from the result;
   Development Test; open its replay.
4. Reopen both through Replay History; confirm earlier-settings labelling and
   access to the earlier run after a parameter or source change.
5. Open and close the sensing guide dialog.
6. Scout copy and run as a regression check.

Record the produced artifacts (I4) with hashes and compare their logical facts
across platforms for identical inputs. This rehearses the M2-6 workflow
technically. It is not a human evaluation.

## 7. Replay performance and accessibility

### 7.1 Replay performance (D2)

[Protocol 01](V6_ALPHA_M2_5_REPLAY_PERFORMANCE_PROTOCOL_01.md) covers initial
loading, reconstruction and projection, perspective switching, replay lengths
of 100 to 1,000 ticks, both platforms, viewer and Designer responsiveness, and
repeated rebuilds. Its interpretation (§6 there) is fixed before measurement.
Adoption is decision P3.

### 7.2 Bounded accessibility checks (D3)

| Check | Method | Expected from code reading |
| --- | --- | --- |
| K-1 keyboard reachability of each viewer function | For each control in §6.1, record whether a keyboard path exists and works natively | Perspective, step, Home/End, speed, play/pause, Help and exit have keys. **History scroll and Help scroll are mouse-wheel only** (PageUp/PageDown change speed), and **arbitrary timeline seek is mouse-only** |
| K-2 Designer guide by keyboard | Tab to the "V6 alpha1 sensing guide…" button; open with Space/Enter; scroll with keys; close with Escape and with its close control; note where focus returns; repeated opening | Not yet observed |
| K-3 focus | Viewer receives focus at launch from the Designer and from the CLI on both platforms; X11 prerequisite recorded; focus after the viewer closes | X11 needs explicit activation (existing prerequisite) |
| K-4 readability | Measured row pitch and font pixel size at each window size and platform; no clipped or overlapping essential text (from F-4); contrast ratios of the renderer's text/background colour constants computed with the WCAG 2.x formula, for information only | Layout clean at all sizes (M2-4) |
| K-5 non-colour cues | The selected perspective is identified by text as well as fill | The title line names the selected perspective |
| K-6 dialog operation | Guide dialog: non-modal, resizable, readable at the recorded scale, no text clipping, closes cleanly | Not yet observed |

Not assessed, and recorded as such: screen readers, OS high-contrast modes,
display scales other than the recorded one (no system setting is changed),
colour-vision simulation and non-English content.

Prospective interpretation:

- **Pass:** the check works as described.
- **Limitation:** a function lacks a keyboard path but has a working mouse
  path, or a readability value falls below the informational reference. Recorded
  as a D3 limitation; M2-5 can be PASS WITH CONDITIONS, and the M2-6 protocol
  must note it.
- **Block:** a defect that prevents completing the §6.2 workflow with mouse and
  keyboard on either platform; a window or dialog that cannot be closed or traps
  focus; or clipped or overlapping essential text at 900x650. This makes M2-5
  HOLD on D3 pending a lead decision or an authorized amendment (§13).

## 8. Information boundary and historical compatibility

**A/B/Omni boundary.** Reuse the M2-4 module results on both platforms (hidden
divergence, seat crossing, fallback, card exclusion) and the M1-5 boundary and
capture-regression modules within the focused selection. Natively (F-4), for
the Keeper and Reacquirer bodies in both seats, the observer's recorded lines
and markers in A and B must contain only that seat's delivered facts: the
non-sensing seat shows no sample or contact, and READ owners are its own IDs.
Omni operator lines must be labelled "not delivered to either agent". Help and
card text must never appear in an entrant scene. The §6.1 fallback launches
confirm the shared fallback natively.

**Historical compatibility.** The 329 pins at `b948540…` (read-only); the
product and supplement selections for V4 defaults, historical replay4/trace2/
result2 readers, retired-execution refusal, starter bytes, digests and order
with terminal `v5_dual_team`, and the published capture regression modules;
read-only re-verification of the curated Keeper and Reacquirer copies with
`verify_keeper_scenario` and `verify_reacquirer_scenario`; and, in F-5, Replay
History listing and opening artifacts retained from M2-2/M2-3. The stable-V4
viewer must be unchanged (client GUI selection, F-1). The historical 72-node
qualification is not rerun automatically.

## 9. Failed-attempt retention and evidence custody

- Every attempt keeps its original label; nothing is overwritten or deleted. A
  corrected run gets a new label. Failed and invalidated attempts are listed
  with hashes in a retained-attempt ledger, including launch failures that
  collect nothing (as `m2_4_linux_dev_views_05` should have been) and scripts
  that never ran.
- Each campaign records its argv, interpreter, environment, exit code,
  duration, JUnit and log (`run.py` pattern), and the source freeze it ran on.
- Before pytest, create fresh `--basetemp` and cache directories outside
  `runs/` and evidence; record their absolute paths; confirm no retained data or
  reparse-point traversal. `pytest.ini` is not changed to evade an ACL failure.
- Inputs are read in place or copied into the run root with hash checks; no
  retained M2-2/M2-3/M2-4 evidence or historical artifact is modified.
- Native runs retain the surface frames, OS-level captures (P5), observer
  states, delivered-key witnesses and exit statuses, including after timeouts.
- No research path, ID or private input is read. Any publication follows the
  curated-package precedent with sanitized paths and a SHA-256 index.

## 10. Platform limitations

Linux evidence remains WSL2/WSLg X11 only (C3): no Wayland, bare Xorg, other
distribution or Xvfb claim, unless P7 adds a run. No full Python 3.10–3.14
matrix, installer, frozen executable or packaging qualification. Windows COM
`0x8001010d` remains a nonblocking observation unless new functional evidence
changes that. The X11 focus prerequisite remains. The Windows display is a
portrait 1080x1920 screen at its recorded scale. Results describe the recorded
machines only.

## 11. Stop conditions and disposition criteria

**Stop and report (M2-5 cannot continue without a lead decision):** semantic
regression; mutated historical evidence or pin mismatch; unknown exclusions or
unexplained node changes in S-0; source, input or environment drift from §2;
missing source or artifact bodies; unusable controls; reproduction of C1; a
delivered-view boundary violation; a Protocol 01 correctness failure (R-c); or a
need for a product code change.

| Disposition | Criteria |
| --- | --- |
| **PASS** | Every required campaign in §5 completed on both platforms; AC01–AC10 and AC12 each have a positive disposition with retained evidence; S-0 accounts for every node, marker and skip; C1 not reproduced with witnesses retained; C2 native before/after proven; D2 in class L1/I1/R-a; D3 checks all pass; no new condition |
| **PASS WITH CONDITIONS** | As PASS, except for recorded limitations that do not block the M2-6 workflow: D2 classes L2, I2 or R-b; D3 limitations; C3 and other platform limits; nonblocking observations such as COM `0x8001010d`. Each limitation is carried into the M2-6 entry |
| **HOLD** | Any stop condition; any missing required platform gate; D2 class L3 or I3; a D3 block; a C1 reproduction not explained by the evidence; or an AC without a supportable disposition. HOLD names the decision or amendment needed |

## 12. Identified risks

| Risk | Handling |
| --- | --- |
| The root Designer GUI suite (F-1) exposes M2-era regressions not seen before | Expected value of the run. Treat failures by the normal classification; a product defect stops M2-5 for an amendment decision |
| X11 focus failures in F-1 on WSLg | Existing prerequisite; use explicit activation and retain the unassisted failure, as M1-6B did |
| Perspective switches stall the event loop for several seconds (Protocol 01 §2) | Measured and classed, not fixed. Windows may flag the window "Not Responding" |
| C1 recurs | Delivered-key witness and exit status retained; investigated as a possible product defect before PASS |
| Synthetic input artefacts (dropped Shift via `PostMessage`) | `SendInput` with focus on Windows; record the input method |
| Windows and Linux runs overlapping on the shared host | Run sequentially (Protocol 01 §4) |
| Surface captures do not show compositor or DPI effects | P5 adds an OS-level capture |
| Environment drift (package updates in `.venv` or the Linux env) | Entry recheck of §2 versions; drift stops M2-5 |

## 13. Amendments that findings could require (not authorized)

- **AM-1 keyboard scrolling** of the history and Help pages, and a keyboard
  seek, if the lead treats K-1 as more than a limitation
  (`sensing_renderer.py`).
- **AM-2 projection reuse or caching**, load feedback or off-thread rebuilds,
  if Protocol 01 finds L3/I3 (see its §8; touches `sensing_presentation.py`,
  `sensing.py` or the renderer; `sensing.py` is outside the M2-4 boundary).
- **AM-3 Designer guide dialog** keyboard or focus fixes, if K-2 or K-6 block
  (`app/views/development.py`).
- **AM-4 any defect** found by F-1 in the root Designer suite.

Each needs an explicit grant, a bounded file list and focused requalification.
M2-5 would record the finding and stop rather than implement it.

## 14. Required project-lead decisions

| ID | Decision | Default if not stated |
| --- | --- | --- |
| **P1** (required) | Publish M2-4 before M2-5, so that the candidate is a commit (recommended); or qualify the uncommitted tree under a source freeze | — |
| **P2** (required) | K1 reuse: accept the eight M2-2 K1 runs plus the M2-3 bridge as satisfying AC02/AC05/AC10 (recommended: executed Keeper and fixture sources unchanged, determinism shown by byte-equal replays); or treat the R1-related engine changes as drift and run a fresh K1 set (two repeats per seat per platform, eight runs) | — |
| **P3** (required) | Adopt Performance Protocol 01, including its §6 classes, before any measurement | — |
| **P4** (required) | Adopt the §7.2 accessibility checks and their interpretation | — |
| P5 | Native frames for C2 and AC08: viewer-surface frames plus one OS-level capture per view and size on each platform | Surface frames plus OS-level captures |
| P6 | Harness input methods: `SendInput` on Windows, `xdotool` with `windowfocus` on X11 | As stated |
| P7 | Linux scope: WSLg X11 only, with C3 retained; or add an Xvfb or bare-X11 run | WSLg X11 only |
| P8 | Publish the C2 input bodies (about 2.2 MB) with M2-5 evidence, or keep them local and hash-bound | Keep local |
| P9 | Treat F-1 failures that are product defects as stop-and-amend (§13) | Stop and amend |
| P10 | M2-5 evidence publication follows the curated-package precedent, as a separate decision after M2-5 closure | As stated |

## 15. Exclusions

This packet authorizes nothing. No M2-5 campaign, collection, native run,
measurement or harness has been executed or written. No M2-6 activity,
publication, product change, E8/E9 harness, private input, entropy or authority
operation, reseal or scientific execution is part of this entry. Stable
`bytefray-rules-4` remains the default, and `bytefray-rules-6-alpha1` remains
explicitly selected and experimental. Original E9 remains operationally blocked
with execution LOCKED, and Requirement C remains NOT ESTABLISHED.
