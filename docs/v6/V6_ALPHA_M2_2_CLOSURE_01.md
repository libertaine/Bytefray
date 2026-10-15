# Bytefray V6 — M2-2 Watchful Keeper Closure Record 01

2026-10-15, America/Indianapolis.

**Authority: Bytefray Project Lead — technical acceptance decision**

| Decision axis | Recorded disposition |
| --- | --- |
| M2-2 WATCHFUL KEEPER TECHNICAL ACCEPTANCE | **PASS WITH CONDITIONS** (C1–C3, §7) |
| M2-2 TECHNICAL MILESTONE | **CLOSED** |
| B2-01 through B2-08 | **PASS**, on the recorded evidence below |
| B2-09 project-lead acceptance | **APPROVED** |
| M2-2A Alpha 1 Development Test correction | **ACCEPTED** |
| Windows native qualification | **PASS** |
| Linux qualification | **PASS within the tested WSL2/WSLg X11 environment** |
| M2-3 Roaming Reacquirer | **NOT AUTHORIZED** (separate grant required) |
| Staging, commit, merge, push, tag, publication, release | **NOT AUTHORIZED** |
| Original E9 / Requirement C | **OPERATIONALLY BLOCKED** (execution LOCKED) / **NOT ESTABLISHED** |

## 1. Authority and provenance

The Project Lead stated this decision in the development session of
2026-10-15 in response to the
[M2-2A qualification package](V6_ALPHA_M2_2A_CORRECTION_QUALIFICATION_01.md),
whose recommendation was PASS WITH CONDITIONS. This record transcribes that
conversational decision. It carries no signature, cryptographic approval or new
research authority, and it is not a general Alpha 1 release authorization.

Earlier records keep their historical wording and bytes. Their pending,
proposed or HOLD statements describe their own time; this record establishes
the final M2-2 disposition. Scope Revision 03 and Checkpoint B 01 were accepted
before implementation (Scope ACCEPT WITH CONDITIONS, Checkpoint B PASS WITH
CONDITIONS, conditional M2-2 grant), as recorded in
[Implementation Record 01 §1](V6_ALPHA_M2_2_IMPLEMENTATION_RECORD_01.md#1-entry-gate-and-authority);
their own headers still read as proposals, deliberately unedited.

## 2. Accepted identities

| Identity | Value |
| --- | --- |
| Contract | [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md), 37,938 bytes, `1b3e507a2593919ed64d43cad0d5ce673e734333529db1e936d5880b4a916eba` |
| Closure gates | [Checkpoint B 01](V6_ALPHA_M2_CHECKPOINT_B_01.md), 22,023 bytes, `29e3883ab6a28995f1f105e9fb15f4e8091f0847930d38f2b1381a36d019f786` |
| Checkout / branch | `D:/Projects/BATTLE2/work/v6-m2-clean` / `v6-m2-clean` |
| Baseline HEAD / tree | `f79a74be1d486f042d260bea672305b9abb27aa5` / `d4f2c73cbd3965762e61316567537e173503ff8a` |
| Index | No staged diff; raw SHA-256 `b77a600d7e0c4e5679798a787e0b392b9994a5ae95a5b8841c4f0192bf6ee00b` |
| Upstream | `origin/v6-research`; a read-only `git ls-remote` on 2026-10-15 returned `f79a74b…` for `refs/heads/v6-research`, equal to HEAD. No fetch was performed |
| Divergent local branch (preserved, not merged) | `v6-research` at `2fc3c82e115650b515a4efab39afb172b62535ed`; 4 commits not in HEAD, 3 HEAD commits not in it; merge base `5971966` |
| Historical pins | 329 (293 implementation + 36 qualification) verified at preserved `b948540aa9ef34134ff7e3c633c3acfc9f97da96`, zero mismatches |

## 3. Accepted source manifest

The accepted M2-2 candidate is uncommitted working-tree content on the baseline
above. Raw SHA-256 of every accepted code, data and test body:

| Path | Bytes | Raw SHA-256 | Slice |
| --- | ---: | --- | --- |
| `engine/src/battle_engine/data/starter_agents/v6_watchful_keeper/agent.py` | 3471 | `9a0dd6febdb7701ffed4537d80d4c5b2ddf57652c002919d9ec0e3d84d533649` | M2-2 |
| `engine/src/battle_engine/data/starter_agents/v6_watchful_keeper/agent.yaml` | 1030 | `e52a2467e6e65e9b20aaf84f8578ca13b900c8fa8b91e9af9b6ac20d98bf8496` | M2-2 |
| `engine/src/battle_engine/data/teaching_fixtures/v6_encroaching_opponent/agent.py` | 772 | `168d242d692885405a4c08d602b44c4a843ac0915fe55a85bfc4c0420dc268b4` | M2-2 |
| `engine/src/battle_engine/data/teaching_fixtures/v6_encroaching_opponent/agent.yaml` | 208 | `e5b7f1734e188e01bd5d86851321b21c613fc632b97ae6b70dea7f596ca2f6dc` | M2-2 |
| `engine/src/battle_engine/starters.py` | 27596 | `2f4bcf556675a73ceca1191b44e441bb51aa83d5c42b0eb338d9a07c6f4eb856` | M2-2 |
| `engine/src/battle_engine/agent_scaffold.py` | 12635 | `2d95789f7ec4105233c6386913d3aa04b5f7e9409ccbb17aeb9c723db467ffab` | M2-2 |
| `app/views/development.py` | 40975 | `cc4acde9db7a3243fdf9fa1e3eb8443c3c82bfc8f44446116e43479c241f2bf7` | M2-2 |
| `engine/src/battle_engine/sensing_demo.py` | 36758 | `012b900326f55ace67e20d7a02c7041261aca78bcb82c979962de5cf8e5e8e73` | M2-2 |
| `engine/src/battle_engine/sensing_playback.py` | 83037 | `5e5df0337a8308eefce202465fd86b43a32f50f40dbc0758dcd196015ca06dcb` | M2-2 |
| `engine/tests/test_v6_alpha_m2_keeper.py` | 19385 | `250238ba25c266fc6baa10e44f5460b6342850accec0b289ee44401cc5920727` | M2-2 |
| `engine/tests/test_agent_scaffold.py` | 21941 | `4026c8ab72aedffef4d7d8831a3fb0a4067a572f7e34fdffd4ff63a556967190` | M2-2 |
| `engine/tests/test_v6_alpha_m1_2_window_scout.py` | 46202 | `31697bf0cc023505b2c18283dd9b6139b1ce93c008d8aadcbe3c20caa8a83419` | M2-2 |
| `tests/test_v6_alpha_m1_5_designer.py` | 17336 | `d14df31c99e6747ae41d9651fb28fab89463212e5f84fc26068b00d04ebc8699` | M2-2 and M2-2A |
| `engine/src/battle_engine/agent_test.py` | 42376 | `d974fad2d1e5d3196c8025163427a85bb460062584e98d670030dc70af48f3ec` | M2-2A |
| `engine/tests/test_agent_test.py` | 46318 | `bf67aad04d40532dec81e3955e831b4dca3d1b21e5a03343739736b8f659b9e6` | M2-2A |

Reviewed Keeper and fixture revisions (normalized content / captured full tree)
are recorded in [Implementation Record 01 §3](V6_ALPHA_M2_2_IMPLEMENTATION_RECORD_01.md#3-behavior-and-acceptance-evidence).
Accepted M2-2 documentation: `docs/specs/agent_scaffold.md`,
`docs/AGENT_AUTHORING.md`, the implementation record, the
[blocker investigation](V6_ALPHA_M2_2A_BLOCKER_INVESTIGATION_01.md), the
qualification record and this closure record. The full repository inventory and
publication proposal are in §10.

## 4. M2-2A correction boundary

The authorized correction changed exactly three paths relative to the entry
bodies: `engine/src/battle_engine/agent_test.py` (import the existing Alpha 1
constant; `--ruleset` choices exactly V4 and Alpha 1; stable-default help; no
execution-service change), `engine/tests/test_agent_test.py` and
`tests/test_v6_alpha_m1_5_designer.py`. Omitted `--ruleset` still selects
`bytefray-rules-4`; whole-roster capability preflight, retired refusal and
supervised execution are unchanged. Exact diff: local
`runs/v6_alpha_m2/m2_2a_20261015_correction/correction_only.diff`
(`e1dba619f986ed2ad196f4ea83fa10557aac976d205be113b1757be287cc2c0b`), published
byte-identical as
[`evidence/m2_2/qualification/correction_only.diff`](evidence/m2_2/qualification/correction_only.diff).
No worker, sensing, ruleset, policy, schema or registry module changed.

## 5. Acceptance matrix

| Gate | Disposition | Primary evidence |
| --- | --- | --- |
| B2-01 capability / entry | **PASS** | Explicit Alpha 1 through CLI and native Test; stable default; both-seat preflight before import/reset/artifacts; malformed/unsupported/retired refusal |
| B2-02 K1 behavior | **PASS** | 48 Keeper cases; READ→repair and SENSE→defensive native witnesses in both seats |
| B2-03 feedback negatives | **PASS** | Absent, empty, refused/null, stale, suppression-delayed and terminal-undelivered cases |
| B2-04 scenario reproduction | **PASS** | Four Windows and four Linux complete 100-tick runs; per-seat and cross-platform logical equality |
| B2-05 provenance / false success | **PASS** | Separate consistency, reconstruction, capture and completion verdicts; Scout semantics unchanged |
| B2-06 authoring | **PASS** | Native GUI nodes plus complete unmocked authoring and external replay workflow, both seats, both platforms |
| B2-07 compatibility | **PASS** | 137-module product campaign and separate 328-node compatibility supplement; exact node/skip ledger; old starters preserved |
| B2-08 engineering / preservation | **PASS** | Ruff; separate engine/client mypy; source/index/ref/evidence preservation; 329 pins |
| B2-09 slice review | **APPROVED** | This record |

The affected M2-AC01/02/04/05/06/09/10/12 subset is satisfied for the Keeper
slice only. No M2-wide criterion is closed; M2-AC03 (Reacquirer), AC07/AC08
(symmetric views, layout) and AC11 (human evaluation) remain open.

## 6. Qualification evidence

Evidence lives in the git-ignored local root `runs/v6_alpha_m2/`. Paths below
are relative to it; hashes bind the retained bodies. Counts overlap and are not
summed. A curated subset is published under
[`evidence/m2_2/`](evidence/m2_2/README.md): representative Keeper bodies from
both seats, sanitized Windows and Linux campaign summaries, the correction diff,
the retained-attempt ledger and a SHA-256
[evidence index](evidence/m2_2/evidence_index.json) that binds each published
file to its local original. The full local collection is not published.

| Evidence | Result | Raw SHA-256 |
| --- | --- | --- |
| `m2_2a_20261015_correction/m2_2a_focused_final.xml` | Windows focused: 619 passed, 4 GUI deselected | `5ea2ad3c5a9b7ab24dd7f04ba845274610cc51aaa9fc105be1b91f09adb1d0e8` |
| `m2_2a_20261015_correction/m2_2a_windows_gui_final.xml` | Windows native GUI: 4 passed | `30d98cab6ffd2b666c9ce81696f6825c777347f1ca1c0578405c6b60a820c744` |
| `m2_2a_20261015_correction/m2_2a_m1_gui.xml` | M1 Designer GUI (offscreen supplement): 5 passed | `d45b9767f1b2732a19d28db89d324d1e94b512e57ab8edd06ca908d45b893728` |
| `m2_2a_20261015_correction/m2_2a_windows_broad.xml` | Windows product: 3,374 passed, 20 skipped, 5 GUI deselected | `6272c15297312826ebd81473bbac80d166cf1aa50c4250e810f9722f83384513` |
| `m2_2a_20261015_correction/m2_2a_windows_supplement.xml` | Compatibility supplement: 328 passed | `089ee0ea970b6add1201d2ea61a9e6880601e052663c0f32ab56d7612fe9312c` |
| `m2_2a_20261015_correction/m2_2a_linux_focused.xml` | Linux focused: 619 passed, 4 GUI deselected | `3b4904aa6ef543b4b7381fb8441a8410fe13c256818de5142c75cfecb17dd586` |
| `m2_2a_20261015_correction/m2_2a_linux_gui_x11.xml` | Linux native GUI (Qt xcb): 3 passed | `db4d8f9120214084c086c3a426f1135cf6947f3a04ebc12a8e911202d94d9413` |
| `m2_2a_20261015_correction/windows_native_complete/summary.json` | Windows full authoring and replay workflow, both seats: PASS | `004f7195b7dd4573a97e3f80467e5946da9acae890dc4bed71a197dcb8624b3c` |
| `m2_2a_20261015_correction/linux_native_complete.log` | Linux workflow: INCOMPLETE (C1, retained) | `225954e799ede4d47f5b1244655c7e03e0aa7fd54fd7667287528304ca859d51` |
| `m2_2a_20261015_correction/linux_end_probe_01.log` | Linux End probe on the same replay: PASS | `e74caeb086788371cc72213801f05bf02e56f42e036aba8032b01f681085cd96` |
| `m2_2a_20261015_correction/linux_native_complete_02/summary.json` | Linux full authoring and replay workflow, both seats: PASS | `2cac982f5d8f759194baa986db3f195096f13fff7d33379e567e7b4f0d81216c` |
| `m2_2a_20261015_correction/cross_platform_comparison.json` | Eight Keeper bodies complete; per-seat logical equality across repeats and platforms | `56f3f0b03fed7d2eb80dd9cf87945739a417e6dded579e52da47b6b6b43164d6` |
| `m2_2a_20261015_correction/selection_reconciliation.json` | Broad node/skip ledger: +39 / −1 replaced, skips unchanged | `4a8586adda779e2bd1c6a7c75354ddaf875512f2580f8fdb7d0b3f7b601fd645` |
| `m2_2a_20261015_correction/historical_pins.json` | 329 pins, zero mismatches | `b9f84b32d9d6990580fa6113c98eb88cb9123eedd7332953e55d96c1d17d5b31` |
| `m2_2a_20261015_correction/old_starter_preservation.json` | Old starter names, digests and 23 files unchanged | `47517d3dd225f46b354bcdc2c08ac1ec76a5fa3eb2522c07217f3a2c5988d86a` |
| `m2_2a_20261015_correction/corrected_source_manifest.json` | 26 entry-file bodies after correction | `68ca897c818b07cdc87c152ae804171a21d24dd1beda3d3860bf7fa54e524d55` |
| `m2_2a_20261015_correction/resume_readonly_verification.json` | Read-only candidate and evidence recheck | `9f7f16c59e6f45a2787cf1a4a8ff5feff631e17df3fda81b88d3b9a4701dbeaa` |

Ruff, both mypy runs and the worker-module evidence are listed in the
qualification record. Platforms: Windows 11 AMD64, Python 3.13.7, native Qt/SDL;
Ubuntu on WSL2 (kernel 6.6.87.2), Python 3.12.3, PySide6 6.12.0 xcb, pygame-ce
2.5.8/SDL 2.32.10 x11 on WSLg `DISPLAY=:0`.

## 7. Conditions carried forward

**C1 — Intermittent Linux End-key non-response (unresolved).** In
`linux_native_complete`, the seat A Development Test viewer completed loading
and four perspective switches; after the harness sent `End` its rendered state
did not change for 120 s, and the run stopped before seat B. That run recorded
neither delivered keys nor the viewer's exit status, so an undelivered or
unprocessed key cannot be distinguished from a stalled viewer. The cause is
**unresolved and is not classified as a harness defect.** It did not recur in
`linux_end_probe_01` (same replay and argv; End in 0.19 s) or in the complete
`linux_native_complete_02` workflow; End took 0.07–0.19 s in all ten other
latency-measured viewers. Obligations: M2-5 Linux qualification SHALL retain the
delivered-key witness and each viewer's exit status, including on timeout. Any
reproduction SHALL be investigated as a possible product defect before M2-5 can
pass.

**C2 — Overlapping replay sample-marker labels.** In long Development Test
replays at terminal state, arena-map historical-sample marker labels overlap
into illegible text on both platforms; the history column remains readable.
Baseline frames: `windows_native_complete/*_test_terminal.png`,
`linux_native_complete_02/*_test_terminal.png` and `*_test_{900,1000,1100}.png`.
The fixed input is the Keeper Development Test replay, byte-identical across
all five runs on both platforms: `replay.jsonl` raw SHA-256
`98edb90ddda6d5d28b3ff76431d6c1ed9e4b7f792b48144173408fc17d9305de`,
`match_2b6f25a5c79928af45e448e4`, 200 ticks, recorded end "winner B;
tick_limit". Use any of its paired traces (they differ only in `wall_time_ms`).
Carried to M2-4 under M2-AC08. Before/after acceptance check, to be implemented
in M2-4 and verified natively in M2-5:

1. Open that replay/trace pair in Agent A's delivered view, press End, and
   render at 900x650, 1000x700 and 1100x750.
2. Before (current): label rectangles in the arena panel intersect. After: no
   two rendered marker labels intersect, and none is clipped by or escapes the
   arena panel, at all three sizes. Repeat for Agent B and Omniscient once
   M2-4 adds them.
3. No delivered sample, age or receipt fact may be dropped from the entrant
   view (the history column remains the complete record), and no undelivered
   information may be added.
4. Retain before/after native frames on both platforms plus an automated
   rectangle assertion.

**C3 — Qualification limitations.** Linux qualification covers WSL2/WSLg X11
only. Xvfb was attempted and failed keyboard initialization; no Wayland client,
bare Xorg or other distribution was qualified. M2-AC08 layout evaluation remains
with M2-4/M2-5 as the contract assigns it, and M2-AC11 human evaluation remains
with M2-6. Automated GUI execution is technical evidence and does not establish
human usability or comprehension.

**Expected verifier result.** `resume_readonly_verify.py` reports two FAIL
lines by design, and every substantive check passes. `all_dirty_paths_hashed_in_manifest`
names only the qualification record, which is intentionally outside the
correction's source manifest because it is the completion document itself.
`no_pre_resume_evidence_modified_after_cutoff` names only the verifier's own
retained script and output, written after its 11:15 cutoff. Neither line is a
preservation failure, and neither may be suppressed by editing the manifests.

## 8. Resolved blockers and retained failure history

All failed attempts remain retained under their original names; none is
relabeled as a pass.

| Finding | Classification | Resolution |
| --- | --- | --- |
| Development Test rejected explicit Alpha 1 (parser allowlist inherited from HEAD) | Product defect | Fixed by the authorized M2-2A correction; native Test passes on both platforms |
| `test_worker_does_not_survive_a_hard_kill_of_its_own_parent` failed in the sandbox (`tasklist` access denied) | Environment | Unchanged worker module passes 16/16 natively and inside the final broad campaign; the original failure and unidentified ACL are retained |
| `m2_2a_cli_01` (121/7), `m2_2a_cli_02` (125/3) | Test-harness mistakes | Expectations corrected to the existing API and canonical `ticks` field; no production change |
| `m2_2a_windows_gui` Scout case (3/1) | Test-harness mistake | Advanced-tab/ruleset setup added; final native run passes |
| Windows replay-control coordinates and resize | Harness (DPI scaling) | Harness converts Qt physical pixels and SDL desktop scaling |
| Linux Xvfb keyboard initialization, stale apt URL, missing libraries | Environment | Qualified on existing WSLg X11 with user-local libraries; no system packages installed |
| `windows_native_01`–`04`, `linux_native_x11_01`–`03`, `*_native_final` timeouts | Harness (profiler overhead, wait windows) | Passive draw-return witness; longer bounded waits; reconstruction latency kept distinct from malfunction |
| `linux_native_complete` End non-response | **Unresolved** | Condition C1 |

## 9. Reproduction

From the checkout, with `.venv` and a **new** output leaf (reuse is refused):

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario keeper-K1 --keeper-seat A --output-dir runs/v6_alpha_m2/repro_A_01
& '.\.venv\Scripts\python.exe' -m battle_engine.sensing_demo --scenario keeper-K1 --keeper-seat B --output-dir runs/v6_alpha_m2/repro_B_01
& '.\.venv\Scripts\python.exe' -m battle_engine.agent_test <agent-id> --ruleset bytefray-rules-6-alpha1
& '.\.venv\Scripts\python.exe' -I runs/v6_alpha_m2/m2_2a_20261015_correction/resume_readonly_verify.py
```

The demo exits 0 only when the separate `keeper-K1` verifier reports
completion; `demo.json` stays `status: "unverified"`. The native workflow
harness is `runs/v6_alpha_m2/m2_2a_20261015_correction/native_workflow.py
<new-label>` (Linux: `linux_native_complete_02.sh` shows the environment). Use
fresh disposable pytest roots, as in the qualification record.

## 10. Repository reconciliation and publication proposal

The working tree holds 27 changed paths before this closure (14 tracked
modified, 13 untracked); this closure adds two documents and edits two
inherited ones. Nothing is staged. The `runs/` and `work/` roots are git-ignored
local evidence and environments and are not publication content.

| Origin | Paths |
| --- | --- |
| Earlier documentation and roadmap review (inherited) | `README.md`, `docs/ROADMAP.md`, `docs/v6/V6_ALPHA_M2_DESIGN_REVIEW_02.md`, `docs/v6/V6_PROJECT_DIRECTION_DECISION_20261015.md` |
| M2-1 scope and Checkpoint B | `docs/v6/V6_ALPHA_M2_SCOPE_CONTRACT_03.md`, `docs/v6/V6_ALPHA_M2_CHECKPOINT_B_01.md`, `docs/v6/V6_ALPHA_M2_1_PREPARATION_RECORD_01.md` |
| M2-2 Watchful Keeper | The 13 M2-2 code/data/test paths in §3, `docs/specs/agent_scaffold.md`, `docs/AGENT_AUTHORING.md`, `docs/v6/V6_ALPHA_M2_2_IMPLEMENTATION_RECORD_01.md` |
| M2-2A correction | `engine/src/battle_engine/agent_test.py`, `engine/tests/test_agent_test.py`, the M2-2A part of `tests/test_v6_alpha_m1_5_designer.py`, `docs/v6/V6_ALPHA_M2_2A_BLOCKER_INVESTIGATION_01.md`, `docs/v6/V6_ALPHA_M2_2A_CORRECTION_QUALIFICATION_01.md` |
| M2-2 closure (this task) | This record; `docs/v6/V6_ALPHA_M2_3_ENTRY_DECISION_01.md`; consistency edits to `README.md` and `docs/ROADMAP.md` |

Proposal: publish all 29 paths together as one M2-2 closure publication on top
of `f79a74b` (on `v6-m2-clean`, then to `origin/v6-research` by fast-forward).
The changes are interdependent: the
registry, scaffold, Designer label, tests and documents reference one another.
No changed path falls outside the M2 lineage. Items for the lead to note:

- `README.md` and `docs/ROADMAP.md` combine inherited pre-M2-1 review edits with
  this closure's consistency edits; they are publishable but not M2-2 code.
- `tests/test_v6_alpha_m1_5_designer.py` mixes M2-2 and M2-2A changes; it cannot be
  split by file.
- The qualification record links to a git-ignored local path
  (`runs/…/correction_only.diff`) that will not resolve once published, and all
  M2-2 evidence (about 178 MB) is local only. M1 published a curated evidence
  subset under `docs/v6/evidence/m1_6*/`. Whether to publish a comparable
  curated M2-2 subset is a lead decision; nothing was copied.
  *Publication addendum (2026-10-15):* the lead approved a curated subset.
  It is published under [`evidence/m2_2/`](evidence/m2_2/README.md), and the
  qualification record's link now targets the published byte copy of that diff.
- The local `v6-research` divergence (`2fc3c82`) stays separate and is not part of
  this proposal.

## 11. Exclusions and release limitations

This closure covers the Keeper slice only. It does not authorize M2-3, M2-4,
M2-5 or M2-6, an M2-wide technical PASS, a human-evaluation PASS, publication,
staging, commit, merge, push, tag or a Bytefray 5.1 release. Stable
`bytefray-rules-4` remains the default; `bytefray-rules-6-alpha1` remains
explicitly selected and experimental. Retained limitations: accepted M1
history/footer overlap and rewind-reconstruction cost; Windows COM
`0x8001010d`; the X11 focus prerequisite; the teaching-only Python/seed threat
model; exact teaching success only for the declared default fixture profile; no
full Python matrix, installer, packaging, accessibility or Wayland claim. No
E8/E9 harness, private input, entropy or authority operation, reseal or
scientific execution occurred. Original E9 remains operationally blocked with
execution LOCKED, and Requirement C remains NOT ESTABLISHED.
