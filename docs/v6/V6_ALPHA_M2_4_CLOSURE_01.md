# Bytefray V6 — M2-4 Replay and Usability Closure Record 01

2026-10-15, America/Indianapolis.

**Authority: Bytefray Project Lead — technical acceptance decision**

| Decision axis | Recorded disposition |
| --- | --- |
| M2-4 REPLAY AND USABILITY TECHNICAL ACCEPTANCE | **PASS WITH CONDITIONS** (§7) |
| M2-4 implementation | **ACCEPTED as reported** in [Implementation Record 01](V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md) |
| M2-AC07 (symmetric delivered views) | **ACCEPTED** on the reported technical evidence, for the M2-4 slice |
| M2-AC08 (usable text and controls) | **ACCEPTED** on the reported technical evidence at the focused M2-4 level; its native both-platform gate remains M2-5 |
| R4-01 through R4-10 | **PASS**, on the recorded evidence below |
| R4-11 project-lead review | **APPROVED** (this record) |
| D1 — shared card content | **APPROVED** (§6) |
| D2 — replay load time | **ACCEPTED AS A LIMITATION; M2-5 FOLLOW-UP REQUIRED** (§6) |
| D3 — language and accessibility | **English-only content ACCEPTED** for the experimental milestone; accessibility **UNASSESSED**; bounded M2-5 checks **REQUIRED** (§6) |
| Earlier conditions (M2-2 C1–C3, M2-3 L1–L5) | **RETAINED** with updated status (§7) |
| Documentation-only closure and publication preparation | Prepared in this record and its package |
| M2-4 publication (staging, commit, merge, push, tag) | **NOT AUTHORIZED**; authorization is requested in §10 |
| M2-5 technical and platform qualification | **NOT AUTHORIZED**; see [M2-5 Entry Decision 01](V6_ALPHA_M2_5_ENTRY_DECISION_01.md) |
| M2-6 human evaluation | **NOT AUTHORIZED** |
| Original E9 / Requirement C | **OPERATIONALLY BLOCKED** (execution LOCKED) / **NOT ESTABLISHED** |

## 1. Authority and provenance

The Project Lead stated this decision in the development session of
2026-10-15. It responds to the technical-acceptance package in
[Implementation Record 01](V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md), whose
recommendation was PASS WITH CONDITIONS (D1–D3 plus carried M2-5 obligations).
The lead accepted the implementation as reported, recorded the D1–D3
dispositions in §6, required that earlier conditions be retained, and did not
authorize publication, M2-5 or M2-6. This record transcribes that
conversational decision. It carries no signature, cryptographic approval or new
research authority. It does not record M2-5 or M2-6 acceptance and is not a
general Alpha 1 release authorization.

Earlier records keep their historical wording and bytes. The
[M2-4 entry packet](V6_ALPHA_M2_4_ENTRY_DECISION_01.md) still reads "NOT
AUTHORIZED", and Implementation Record 01 still presents a recommendation and
asks the lead to confirm D1. This record establishes the final M2-4
disposition.

No fresh M2-4 regression campaign was run for this closure. §9 instead verifies
that no tested input changed after acceptance: the closure preservation audit
is byte-identical to the implementation's final audit.

## 2. Accepted identities

| Identity | Value |
| --- | --- |
| Contract | [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md), 37,938 bytes, `1b3e507a2593919ed64d43cad0d5ce673e734333529db1e936d5880b4a916eba` |
| Closure gates | [Checkpoint B 01](V6_ALPHA_M2_CHECKPOINT_B_01.md), 22,023 bytes, `29e3883ab6a28995f1f105e9fb15f4e8091f0847930d38f2b1381a36d019f786` |
| Entry packet | [M2-4 Entry Decision 01](V6_ALPHA_M2_4_ENTRY_DECISION_01.md), 15,420 bytes, `b560a112ecdad93bd89b43495ed0633cc2b8de1b68827f61d672472021945d26` (published in `e7c0f9d`) |
| Accepted technical package | [Implementation Record 01](V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md), 31,435 bytes, `28e53b40e8d3b09254e5095409224dc1dfb142ccb6a700ce75550ea359ba36e0` |
| Checkout / branch | `D:/Projects/BATTLE2/work/v6-m2-clean` / `v6-m2-clean` |
| Baseline HEAD / tree | `e7c0f9de1f08f7c6494c36f2b4cc77850fad912f` / `0524c86e38f8def267342cf9ffaf6986f2f730ba` (published M2-3; parent `0ead52a5…`) |
| Index | No staged diff |
| Upstream | `origin/v6-research`. A live read-only `git ls-remote` during closure preparation returned `e7c0f9d…` for `refs/heads/v6-research`, equal to HEAD; ahead/behind 0/0. No fetch was performed |
| Divergent local branch (preserved, not merged) | `v6-research` at `2fc3c82e115650b515a4efab39afb172b62535ed`; 4 commits not in HEAD, 6 HEAD commits not in it; merge base `5971966` |
| Historical pins | 329 (293 implementation + 36 qualification) verified at preserved `b948540aa9ef34134ff7e3c633c3acfc9f97da96`, zero mismatches (rechecked for this closure) |
| Final source freeze | `runs/v6_alpha_m2/m2_4_20261015/source_freeze_05.json` |
| Watchful Keeper card inputs | `v6_watchful_keeper` content digest `35b945ad33f34168ea4374dad05fa61fe5b20d08cc15ca2e9af293ebb0c8016e`; `v6_encroaching_opponent` `42763e704cc723e435af2f2822d90ad972c4cbdea8e3ada8322d6b07f8f24456`; `keeper-K1` |
| Roaming Reacquirer card inputs | `v6_roaming_reacquirer` content digest `65866988dd2dfdddd9782a8040d932dc84f05cec9b5d6feab3fb6a73c9697f21`; `v6_relocating_opponent` `d5331833880756a98ea952b98a6c849c4c04234b46b5271a252bb771339a6ddd`; `reacquirer-R1` |
| Fixed C2 input (local, not published) | Keeper Development Test `replay.jsonl` `98edb90ddda6d5d28b3ff76431d6c1ed9e4b7f792b48144173408fc17d9305de`, `trace.jsonl` `47268aa8139bf676bbfa050d2c9f7ec21195a0ac047e68cb8e7bc208cbd9c7e9`, `result.json` `62003072f4280d1ed9a260bf67bdc98a3bed320ed6ee29c5f346b311dde4553f` |

## 3. Accepted change manifest

The accepted M2-4 candidate is uncommitted working-tree content on the baseline
above. Raw SHA-256 of every accepted code and test body (identical to
Implementation Record 01 §3 and `source_freeze_05.json`). The working-tree
bodies are LF, so these values are also the SHA-256 of the bytes Git would
commit.

| Path | Bytes | Raw SHA-256 | Change |
| --- | ---: | --- | --- |
| `client/src/battle_client/sensing_presentation.py` | 19926 | `445f677b63571eddf068724189688f56b71f3a5fb044ba918bafdd165b319bf2` | M2-4 |
| `client/src/battle_client/renderers/sensing_renderer.py` | 25062 | `1526b5003ea75716c47853508af625b218b74dc2e7a52132bd33679a0e8e40ab` | M2-4 |
| `client/src/battle_client/cli.py` | 17133 | `b37c41c922c639397d0cfdaf97183ba9af9b08bbffde1dc71aac24dfe7b77667` | M2-4 |
| `app/views/development.py` | 42720 | `dbb4c9ac19850968449c5832a5cb4c37b65d76edc08d87b85a3c8b2ed6c22e40` | M2-4 |
| `client/tests/test_v6_alpha_m2_4_views.py` | 29218 | `15a3c210a111127bf478e47101c454d44a42d9ef2f1707c70da0ec8a20d2e212` | M2-4 |
| `client/tests/test_v6_alpha_m1_5.py` | 10537 | `46b9e7737e41cc2e3ea1ad4956809ee3e507bd5df87f3635148ab31209ba0b50` | M2-4 |
| `client/tests/test_v6_alpha_m1_5_adversarial.py` | 8441 | `08f52080edd766796eabcef74defb433182291bbc12dfdea8e2e4bdfd7d36c4b` | M2-4 |
| `tests/test_v6_alpha_m1_5_designer.py` | 24969 | `b003347df64617cca2dc28f02d648f126fa6cb553c14dcb3c8ae6d299755d80d` | M2-4 |

Seven tracked files are modified (652 insertions, 76 deletions) and one test
module is new; the implementation record is the ninth changed path. All nine
lie inside the Entry Decision §4 boundary as amended by the Q1/Q2 grant: the
proposed `docs/v6/cards/` path was not created, because the lead placed the
cards in product surfaces with one shared definition. Unchanged, as audited by
`preservation_final.json`: the whole `engine/` tree (byte-identical to
`e7c0f9d`); `sensing.py`, `player.py`, `session.py`, `perspective.py`,
`director.py`, `fight_night.py`, `hud_layout.py` and `pygame_renderer.py`;
README, ROADMAP, packaging and pytest configuration; research and evidence
paths; every starter digest; and the catalog suffix `…, v6_window_scout,
v6_watchful_keeper, v6_roaming_reacquirer, v5_dual_team`.

## 4. Acceptance matrix

| Gate | Disposition | Primary evidence |
| --- | --- | --- |
| R4-01 explicit selection (AC07) | **PASS** | `SensingPresentation.select("A" \| "B" \| None)` through the existing `switch_view`; renderer receives only the selected view; exact labels |
| R4-02 payloads, histories, ages (AC07) | **PASS** | Both seats, Keeper and Reacquirer bodies; observation, action, tick end, before receipt, after MOVE; backward seek, scrub, restart, Omni→entrant |
| R4-03 own rows and pacing (AC07) | **PASS** | Own callback ordinals, constant pacing, no opponent rows, blank steps or suppressed-opportunity pauses; switching clears state |
| R4-04 hidden divergence (AC07) | **PASS** | Three hidden opponent scripts in both seats; identical payload and navigation; terminal only at the recorded end |
| R4-05 fallback (AC07) | **PASS** | Either seat's projection failure disables both delivered views; binding failures; sidecar-only failure keeps both views; passive features stay cleared |
| R4-06 layout (AC08 focused) | **PASS** | Three sizes; A, B, Omni; mid-match and terminal; long histories; Consolas, DejaVu Sans Mono and bundled fonts |
| R4-07 C2 labels | **PASS** | Rectangle assertions; offscreen before/after frames on both platforms (§5) |
| R4-08 controls | **PASS** | Keys, V/P cycle, mouse selector, pause/step, Home/End, speed, seek, scroll, Help, resize; CLI `--perspective B` |
| R4-09 guide and cards | **PASS**; placement **APPROVED** as D1 | One static shared definition, two cards, provenance tests |
| R4-10 regression | **PASS** | §5; no new skip; 329 pins |
| R4-11 lead review | **APPROVED** | This record |

M2-AC07 is accepted for the M2-4 slice. M2-AC08 is accepted at the focused
M2-4 level only. No M2-wide criterion is closed: M2-5 must still qualify the
frozen M2 candidate as a whole, including the native both-platform M2-AC08
gate, and M2-AC11 belongs to M2-6.

### 4.1 Accepted guarantees

**A/B/Omni selection and filtering.** The selector `Perspective: A | B | Omni`
maps keys 2/3/1 to A/B/Omni, V/P cycles Omni→A→B→Omni, and clicking a segment
selects it. Each change rebuilds the existing `SensingCursor` for exactly one
entrant (or none), so the renderer's entrant path receives only that entrant's
filtered `SensingView`. `draw_entrant(self, view)` keeps its one-argument
signature. Operator verification lines appear only in Omni, labelled "not
delivered to either agent". Every switch resets scroll, scrubbing, drawn
history and markers. A missing or corrupt trace, or a wrong replay or result
binding, disables both delivered views ("Omniscient — replay only …"), as does
a projection failure for either seat. An invalid optional `demo.json` alone
keeps both delivered views. No hidden-state, pacing or future-outcome leak and
no raw-world renderer dependency was found.

**Replay layout and sample-marker readability.** Rows are stacked from the
active font's measured pitch (every glyph the viewer draws) and measured widths.
A dedicated wrapped disclaimer row sits outside the scrollable history and the
controls, which resolves the accepted M1 history/footer overlap. Marker labels
take the first free position of eight around their marker; a label without a
free position is left off the map only, counted in "N more map labels not
shown; see history", and the history list stays the complete delivered record.

**Shared guide and scenario cards.** `ALPHA1_SENSING_GUIDE`, `SCENARIO_CARDS`
and `sensing_guide_lines()` in `sensing_presentation.py` are module constants
that never read a replay, view or session. Replay Help (`?`) and the Designer's
"V6 alpha1 sensing guide…" dialog show the same lines, outside the arena scene,
identically in A, B and Omni. Provenance tests bind each card's starter and
fixture digests, defaults, profile, ruleset and entrant names to the bundled
sources and published `demo.json` files, so a drifted input fails the suite.

## 5. Qualification evidence

Evidence lives in the git-ignored local root `runs/v6_alpha_m2/m2_4_20261015/`.
Paths below are relative to `runs/v6_alpha_m2/`, and hashes bind the retained
bodies. Counts overlap and are not summed. A curated subset is published under
[`evidence/m2_4/`](evidence/m2_4/README.md): C2 before/after probe reports and
frames, the native observation summary, the load-timing record, sanitized
Windows and Linux campaign summaries, the node/skip ledger, two source freezes,
the preservation audits, the retained-attempt ledger and a SHA-256
[evidence index](evidence/m2_4/evidence_index.json).

| Evidence | Result | Raw SHA-256 |
| --- | --- | --- |
| `m2_4_20261015/m2_4_views_05.xml` | Windows new module, `-m "gui or not gui"`: 37 passed | `b897192d91382e950e63e7a6e4e9ccca77f793512a01b8f63773597a8b4f93d3` |
| `m2_4_20261015/m2_4_linux_views_05.xml` | Linux new module: 37 passed | `df46dfecb5f7cedbb943ad2c5c82d3cd8986d5e16d206db4e34abe5ecf8f5f48` |
| `m2_4_20261015/m2_4_client_sensing_05.xml` | Windows client sensing and `test_hud_layout.py`, gui included: 163 passed | `761f8c98826f4897ac19c10f6289b23899e6bbef8ed9fee20070f8e0979014d9` |
| `m2_4_20261015/m2_4_linux_client_sensing_05.xml` | Linux client sensing: 163 passed | `42ff63d08b7e2f7945be1ea1fd8ff208be38c3275f087a595da0247fd89eaad1` |
| `m2_4_20261015/m2_4_focused_05.xml` | Windows focused: 824 passed, 10 GUI deselected | `5e890bb4a756058bb23b98e88d98d194974ea7f29ca88a3b18592ada6799b026` |
| `m2_4_20261015/m2_4_linux_focused_05.xml` | Linux focused: 824 passed, 10 GUI deselected | `67dcb9c21e5a415af05221ce67c5d76dba4ff18439fd487fb10c8713cf731126` |
| `m2_4_20261015/m2_4_broad_05.xml` | Windows product (139 modules): 3,472 passed, 21 skipped, 11 GUI deselected | `0a8b4546b5eec3bf343d832b6ce7b3dff0e9e1cb893d850e4ef522abba95ac0f` |
| `m2_4_20261015/m2_4_windows_gui_05.xml` | Windows Designer GUI, explicit `-m gui`: 8 passed | `ece93dd49c189abff407c19342884084d77024d8a2ff8add176218c9b6ec0d1d` |
| `m2_4_20261015/m2_4_linux_designer_guide_05.xml` | Linux Designer guide node (Qt xcb): 1 passed | `145654cf2760749fedb0d420285626413deeac0a61043e3d94be9545d281d21f` |
| `m2_4_20261015/m2_4_ruff_05.log` | `ruff check .`: all checks passed | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `m2_4_20261015/m2_4_mypy_client_05.log` | Client mypy: no issues (19 files) | `6b17fb6a37a46097878dda7d24d47ea3abd7a26d94efdbf8f17ad1c639872d16` |
| `m2_4_20261015/m2_4_mypy_engine_05.log` | Engine mypy: no issues (106 files) | `1860637a02ad5d8f172ae2c55355729aa92ebafe5233f2d07dcd3fca43dc3ec3` |
| `m2_4_20261015/before_windows/report.json` | C2 before, Windows, Consolas: 23 labels, 81/81/58 intersecting pairs | `981a37ed9e23fca084036eeadd3869ff6f033911e42af20d48f96ca134de148b` |
| `m2_4_20261015/linux_before/report.json` | C2 before, Linux, published `e7c0f9d` renderer: 96/81/81 pairs | `3309c781a40867896ffd18ed864148b9a4838a0baf9aca044f9f493f5f1b6d9b` |
| `m2_4_20261015/after_windows_final_05/report.json` | C2 after, Windows, freeze 05: 0 pairs, 0 escapes; `--assert` PASS | `7cc0f12f9fb9dc41c2a8638e24fc870ef5b48fdfea121e18a8c50488e598d570` |
| `m2_4_20261015/linux_after_final_05/report.json` | C2 after, Linux, freeze 05: 0 pairs, 0 escapes; `--assert` PASS | `c91682ebc148c8b3647a2256f635bfe468734f54ca03eddd2eb53fdd2dd26837` |
| `m2_4_20261015/windows_native_03/summary.json` | Windows native viewer (freeze 04): PASS; Help off not confirmed natively | `ddbf4a72e21dd1f52d9341ab2e4ddfae868e10d901a13261290d7364e4b9d625` |
| `m2_4_20261015/linux_native_04/summary.json` | Linux native viewer (freeze 05): PASS; 27 delivered key events; exit 0 | `a8d03c41e55e123cd1edfb5e0106e642edcdb024b586fcbcced3324df4500e53` |
| `m2_4_20261015/load_timing_windows.json` | In-process load on the C2 replay: A 6.08 s, B validation 5.72 s, total 11.79 s | `f319c45daa58b67ab4b43ec9fa61417c72ba33a67ac13a5c576c0b2e59da6b88` |
| `m2_4_20261015/source_freeze_05.json` | Final candidate freeze | `f3210c4f291a2f8a3ef2ee3366f2e94a8510ff13ce02b4991b2ff8ff15709fdb` |
| `m2_4_20261015/preservation_final.json` | Preservation and 329 pins: PASS | `ee5b4a6ee819e70c859b5632b1efee8fe44ffff417b13acf9dad545a2303a0f0` |

Platforms: Windows 11 AMD64, Python 3.13.7, pygame-ce 2.5.8 (SDL 2.32.10),
Consolas; Ubuntu on WSL2 (kernel 6.6.87.2), Python 3.12.3, pygame-ce 2.5.8,
PySide6 6.12.0 xcb on WSLg `DISPLAY=:0`, where `SysFont("consolas")` resolves
to DejaVu Sans Mono. The broad campaign is Windows only, as in M2-3. Compared
with `m2_3_broad_r307.xml`, it adds exactly the 31 headless nodes of the new
module, removes none, and its 21 skipped node IDs are identical. The M2-2/M2-3
scenario runs, Keeper and Reacquirer native demonstrations and the 328-node
compatibility supplement were reused, not repeated, because every engine source
is byte-identical to `e7c0f9d`.

### 5.1 Closure findings about the evidence

The closure re-read the local root and records four facts that the accepted
package does not state. None changes a disposition.

1. **Native frames are surface captures.** The passive observer saves the
   viewer's own display surface (`pygame.image.save`) inside the native
   process. Every native frame in `windows_native_03`, `linux_native_01`,
   `linux_native_03` and `linux_native_04` is byte-identical to the offscreen
   probe frame of the same freeze, view and size. They show what the native
   viewer drew, not OS compositor or DPI-scaled output. The M2-2 C2 baseline
   frames were captured the same way. M2-5 must state which capture it accepts
   for the native C2 obligation (M2-5 Entry Decision 01 decision P5).
2. **Two retained items are missing from Implementation Record 01 §9.2.**
   `m2_4_linux_dev_views_05` (exit 4, nothing collected) was a launch failure:
   `-m "gui or not gui"` was split into separate arguments. It was relaunched
   unchanged as `m2_4_linux_dev_views_05b` (58 passed). `linux_campaign_03.sh`
   was written for freeze 03 and never executed, because freeze 04 superseded
   it. No `_03` Linux campaign, probe or native run exists. Both are now listed
   in `failures/retained_attempts.json`. The implementation record is not
   edited.
3. **The Windows "before" probe has no recorded renderer hash.**
   `before_windows` predates the probe's renderer hashing. The Linux "before"
   probe binds the published `e7c0f9d` renderer (`393f29af…`), and the client
   is unchanged from `f79a74b` to `e7c0f9d`, so the retained M2-2 native frames
   show the same pre-correction renderer.
4. **Windows native key witness.** `windows_native_03` recorded 26 delivered key
   events against Linux's 27; the missing event is the Help-off Shift+/ that
   arrived as a plain `/`, as Implementation Record 01 §8 states.

## 6. Decisions D1–D3

**D1 — Shared card content: APPROVED.** The single shared card and guide
definition in `client/src/battle_client/sensing_presentation.py` is accepted.
It shall not be moved merely for documentation organization. Its static content
and the approved policy and fixture provenance checks shall be preserved: the
starter and fixture digests, defaults, profile, ruleset and entrant names stay
bound by tests, and no card or guide text may enter an entrant scene.

**D2 — Replay load time: ACCEPTED AS A LIMITATION; M2-5 FOLLOW-UP REQUIRED.**
Eager seat-B validation adds about 5.7 s to each load of the 200-tick C2 replay
on the idle Windows machine (A projection 6.1 s, total 11.8 s). This cost must
be evaluated during native qualification. The reproducible protocol, with its
interpretation fixed before any M2-5 measurement, is
[M2-5 Replay Performance Protocol 01](V6_ALPHA_M2_5_REPLAY_PERFORMANCE_PROTOCOL_01.md).
It covers initial loading, reconstruction and projection, perspective
switching, several replay lengths, Windows and Linux, responsiveness, and
repeated rebuilds. No performance-related product code change is authorized.

**D3 — Language and accessibility.** English-only Help and guide content is
accepted for this experimental milestone. Accessibility remains **unassessed**.
M2-5 shall include bounded keyboard, focus, readability and dialog-operation
checks and record any limitation honestly
([M2-5 Entry Decision 01 §7.2](V6_ALPHA_M2_5_ENTRY_DECISION_01.md#72-bounded-accessibility-checks-d3)).
M2-6 human evaluation remains necessary; neither M2-4 nor M2-5 evidence
establishes accessibility or human comprehension.

## 7. Conditions carried forward

No condition is discarded because related tests now pass. Each row separates
what M2-4 satisfied from what remains an M2-5 (or M2-6) obligation.

| Condition | Satisfied by M2-4 | Remaining obligation |
| --- | --- | --- |
| **M2-2 C1** — unexplained Linux End-key non-response | Not reproduced: End responded in `linux_native_01`, `_03` and `_04`, with 27 delivered key events and exit 0 each time | **Open, cause unexplained.** M2-5 Linux native runs shall retain the delivered-key witness and every viewer's exit status, including on timeout; any reproduction is investigated as a possible product defect before M2-5 can pass |
| **M2-2 C2** — sample-marker overlap | **Corrected.** Label placement plus automated rectangle assertions; offscreen before/after probes PASS on both platforms' fonts; supplementary native after-frames clean | Native before/after proof on both platforms remains an M2-5 obligation (Q4). The M2-2 native frames are the retained "before"; M2-5 supplies the native "after" at the frozen candidate, with the capture method decided under P5 |
| **M2-2 C3** — WSL2/WSLg X11 qualification limits | — | **Unchanged.** No Wayland, Xvfb, bare Xorg, other distribution, full Python matrix, packaging or installer claim |
| M1 history/footer overlap | **Resolved** by the dedicated disclaimer row and measured layout | Native confirmation on both platforms in M2-5 (M2-AC08) |
| **M2-3 L1** — seat-B product view | **Satisfied** at the M2-4 technical level: B by key, cycle, mouse and CLI, with symmetric guarantees | Native both-platform A/B/Omni confirmation in M2-5 |
| **M2-3 L2** — external viewer controls | Exercised natively in the supplementary runs (End, seek, resize, keys, exit) | Formal requalification of the external viewer for Keeper and Reacquirer artifacts in M2-5 |
| **M2-3 L3** — Linux coverage; wheel package-data | — | Unchanged, as C3. The v6 sensing starters remain absent from the wheel `package-data` globs; packaging is outside M2 qualification |
| **M2-3 L4** — M2-2 C1–C3 open | C2 corrected, as above | C1 and C3 open; C2's native proof open |
| **M2-3 L5** — skips | M2-4 added no skip (21 skipped IDs identical to M2-3) | The M2-3 skip `…[api2-roaming_reacquirer]` remains under its approved reason; M2-5 re-accounts every skip |
| **D2** | Measured once in-process on Windows | Protocol 01 in M2-5 on both platforms |
| **D3** | English-only accepted | Bounded M2-5 checks; human evaluation in M2-6 |

Further retained limitations: rewind reconstruction is a forward rebuild from
the beginning (no checkpoint redesign); Windows COM `0x8001010d` (unresolved
root cause, nonblocking); the X11 focus prerequisite; the teaching-only
Python/seed threat model; exact teaching success only for the declared default
fixture profiles; and no accessibility, installer, packaging or Wayland claim.
Scripted GUI and native interactions are technical evidence, not a human
result.

## 8. Retained failures

All failed attempts remain retained under their original names; none is
relabeled as a pass. The full list, with hashes and failed node IDs, is in
[`failures/retained_attempts.json`](evidence/m2_4/failures/retained_attempts.json).

| Attempt | Outcome | Classification |
| --- | --- | --- |
| `m2_4_dev_existing_01` | 2 failed | Development: tests followed the measured geometry, with assertions kept |
| `m2_4_dev_new_01` | 2 failed | Development: fixture too sparse; Help equality compared scroll windows |
| `m2_4_linux_views` and probe `linux_after_final` (freeze 01) | 3 failed; probe FAIL | **Product defect, fixed:** DejaVu Sans Mono caption ran into the history header at 900x650 |
| `m2_4_linux_views_02` (freeze 02) | 3 failed | **Product defect:** measured text taller than the line pitch |
| `m2_4_linux_views_04` (freeze 04) | 3 failed | **Product defect, fixed in freeze 05:** one probe string cannot bound Linux text height |
| `m2_4_linux_dev_views_05` | Exit 4, nothing collected | Launch failure (argument splitting); relaunched as `_05b` (§5.1) |
| `windows_native_01` | Harness failure | `.venv` launcher PID differed from the viewer PID |
| `windows_native_02` | Harness/display failure | Portrait 1080x1920 display could not return to 1100 wide |
| `windows_native_03` | PASS, one step unconfirmed | Help off: `PostMessage` did not carry Shift; viewer correctly ignored `/` |
| `linux_campaign_03.sh` | Not executed | Superseded by freeze 04 (§5.1) |

## 9. Closure validation

`runs/v6_alpha_m2/m2_4_closure_20261015/closure_validate.py` checks, read-only:
HEAD and the live remote parent; that nothing is staged; that the dirty set
equals exactly the proposed publication paths; that every accepted code and test
body still matches §3, so no relevant tested input changed after acceptance; the
implementation record's accepted bytes; the curated evidence index, its byte
copies and the absence of local absolute paths; the package's line-ending
statement; every hash cited in this record; local links and anchors in the
affected documents and that none points into a git-ignored path; UTF-8, LF and
trailing whitespace in new and edited Markdown; `git diff --check`; current
status lines; and a fresh preservation audit with the 329 historical pins. Its
outcome is reported with the publication request.

## 10. Publication manifest and proposal

The closure prepares, but does not perform, one commit on `v6-m2-clean` on top
of `e7c0f9d` (= live `origin/v6-research`), to be fast-forwarded to
`origin/v6-research` only after explicit authorization:

| Commit | Paths | Content |
| --- | ---: | --- |
| `feat(v6-alpha1): complete M2-4 Replay and Usability` | 40 | The 8 accepted code and test paths (§3); Implementation Record 01; this record; [M2-5 Entry Decision 01](V6_ALPHA_M2_5_ENTRY_DECISION_01.md); [M2-5 Replay Performance Protocol 01](V6_ALPHA_M2_5_REPLAY_PERFORMANCE_PROTOCOL_01.md); the 26 files under `docs/v6/evidence/m2_4/`; status edits to `README.md` and `docs/ROADMAP.md` |

Items for the lead to note:

- One commit follows the M2-2 and M2-3 milestone-commit precedent; no erratum
  is pending. The code, its tests, the records that cite them and the evidence
  bound to their hashes are interdependent.
- Publishing the M2-5 entry packet and performance protocol with M2-4 fixes the
  D2 interpretation publicly before any M2-5 measurement. Neither document
  authorizes M2-5.
- `README.md` and `docs/ROADMAP.md` receive status-line edits only (M2-4
  accepted with conditions; M2-5 entry review prepared, not authorized).
- The curated package adds about 1.16 MB, mostly nine C2 frames (about
  0.9 MB). The full local root (`runs/v6_alpha_m2/m2_4_20261015/`, about
  28 MB) is not published. The C2 input bodies (about 2.2 MB) stay local,
  bound by hash, as in M2-2.
- No package file is git-ignored, so no `git add -f` is needed. The package's
  `.gitattributes` (`* -text`) preserves the five CRLF byte copies.
- The local `v6-research` divergence (`2fc3c82`) stays separate and is not part
  of this proposal.
- The exact per-path manifest is generated by the closure validation after this
  record is final. It is reported with the publication request rather than
  embedded here, because this record cannot contain its own hash.

## 11. Exclusions and release limitations

This closure covers the M2-4 slice only. It does not authorize publication,
staging, commit, merge, push or tag; M2-5 or M2-6; an M2-wide technical PASS; a
human-evaluation or accessibility PASS; or a Bytefray 5.1 release. Stable
`bytefray-rules-4` remains the default, and `bytefray-rules-6-alpha1` remains
explicitly selected and experimental. No product code, test or evidence body
changed during closure. No E8/E9 harness, private input, entropy or authority
operation, reseal or scientific execution occurred, and no E8/E9 research
artifact was modified. Original E9 remains operationally blocked with execution
LOCKED, and Requirement C remains NOT ESTABLISHED.
