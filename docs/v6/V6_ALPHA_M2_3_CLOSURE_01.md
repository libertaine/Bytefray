# Bytefray V6 — M2-3 Roaming Reacquirer Closure Record 01

2026-10-15, America/Indianapolis.

**Authority: Bytefray Project Lead — technical acceptance decision**

| Decision axis | Recorded disposition |
| --- | --- |
| M2-3 ROAMING REACQUIRER IMPLEMENTATION | **ACCEPTED** |
| M2-3 technical acceptance recommendation | **PASS WITH CONDITIONS** (L1–L5, §6) |
| R3-01 through R3-08 | **PASS**, on the recorded evidence below |
| R3-07 amendment (Keeper catalog-suffix assertion) | **AUTHORIZED and applied**; exact diff audited |
| Rulings I1–I3 | **CONFIRMED**; I2 supersedes the entry packet's wording (§2) |
| R3-09 project-lead review | **APPROVED** |
| Documentation-only closure and publication preparation | **AUTHORIZED** (this record and its package) |
| Correction of the M2-2 evidence README erratum | **AUTHORIZED** as a separately identifiable change (§8) |
| M2-4 entry review | **AUTHORIZED, read-only**; see [M2-4 Entry Decision 01](V6_ALPHA_M2_4_ENTRY_DECISION_01.md) |
| M2-4 implementation | **NOT AUTHORIZED** |
| Staging, commit, merge, push, tag, publication, release | **NOT AUTHORIZED**; publication authorization is requested in §9 |
| Original E9 / Requirement C | **OPERATIONALLY BLOCKED** (execution LOCKED) / **NOT ESTABLISHED** |

## 1. Authority and provenance

The Project Lead stated this decision in the development session of
2026-10-15. It responds to the technical-acceptance package in
[Implementation Record 01](V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md), whose
recommendation was PASS WITH CONDITIONS after the R3-07 amendment. The lead
stated that M2-3 implementation is accepted, authorized documentation-only
closure and publication preparation, required that the uncommitted candidate
stay intact until publication preparation is complete, and did not authorize
M2-4 code work. This record transcribes that conversational decision. It
carries no signature, cryptographic approval or new research authority, and it
is not a general Alpha 1 release authorization.

The lead also stated that no fresh M2-3 regression campaign is needed solely
because this acceptance was recorded, provided no relevant tested input
changes. §10 verifies that condition: since the accepted package, only
documentation and new evidence-package files changed.

Earlier records keep their historical wording and bytes. The
[M2-3 entry packet](V6_ALPHA_M2_3_ENTRY_DECISION_01.md) still reads "NOT
AUTHORIZED", and Implementation Record 01 still presents a recommendation. This
record establishes the final M2-3 disposition.

## 2. I2 supersession

Entry packet §3 proposed that refused, null or absent rescan feedback resume a
fresh search "in its prior search family: SEARCH, or SEARCH_AFTER_ABSENCE if that
mode produced the target". The lead's approved ruling **supersedes that
wording**:

> **I2 — Refused rescan.** Return to ordinary search, not search-after-absence.
> No observation is received and no stale information becomes fresh.

The ruling is consistent with Scope Revision 03 §5 ("Refused/null/absent scan
feedback | No absence/positive transition … resume a fresh anchor-relative
search, preserving historical samples"), which names no mode. The accepted
agent and the independent `_ReacquirerModel` verifier already implemented the
approved ruling: on a refused rescan, both set the mode to SEARCH and drop the
active target, whatever search produced it. No code or test changed because of
the supersession. Implementation Record 01 §1 records the check, and its
I1/I3 rows record the other two confirmed rulings.

The ruling does not cover a refused *search* SENSE issued in
SEARCH_AFTER_ABSENCE. That case stays in its mode
(`test_i2_refused_search_after_absence_keeps_that_search_mode`), following §5's
"resume a fresh anchor-relative search". It is recorded here so that any later
contrary direction is an explicit decision.

## 3. Accepted identities

| Identity | Value |
| --- | --- |
| Contract | [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md), 37,938 bytes, `1b3e507a2593919ed64d43cad0d5ce673e734333529db1e936d5880b4a916eba` |
| Closure gates | [Checkpoint B 01](V6_ALPHA_M2_CHECKPOINT_B_01.md), 22,023 bytes, `29e3883ab6a28995f1f105e9fb15f4e8091f0847930d38f2b1381a36d019f786` |
| Entry packet | [M2-3 Entry Decision 01](V6_ALPHA_M2_3_ENTRY_DECISION_01.md), 14,962 bytes, `f068cc09c377b76768a611b1dd806709120af4a7ee9853cd7fa676bebcf6b20f` (published in `4fd89bb`) |
| Accepted technical package | [Implementation Record 01](V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md), 35,370 bytes, `9ed652f46daeb7e2798f64a3f0556dd6db3a9792125c5d3ac8faaf55cb7f1574` |
| Checkout / branch | `D:/Projects/BATTLE2/work/v6-m2-clean` / `v6-m2-clean` |
| Baseline HEAD / tree | `4fd89bbfdc6845815a0df6d4d60eab92cc3a0a94` / `109cf38b45175fdee1023fd620f0ead70384ad56` (published M2-2; parent `f79a74be…`) |
| Index | No staged diff |
| Upstream | `origin/v6-research`. A live read-only `git ls-remote` during closure preparation returned `4fd89bb…` for `refs/heads/v6-research`, equal to HEAD; ahead/behind 0/0. No fetch was performed |
| Divergent local branch (preserved, not merged) | `v6-research` at `2fc3c82e115650b515a4efab39afb172b62535ed`; 4 commits not in HEAD, 4 HEAD commits not in it; merge base `5971966` |
| Historical pins | 329 (293 implementation + 36 qualification) verified at preserved `b948540aa9ef34134ff7e3c633c3acfc9f97da96`, zero mismatches (rechecked for publication) |
| `v6_roaming_reacquirer` | Content digest `65866988dd2dfdddd9782a8040d932dc84f05cec9b5d6feab3fb6a73c9697f21`; full tree `4e96e499365083bcae2b5eca1c71471c0594e8e638235deaf7dd0403e19282b1` |
| `v6_relocating_opponent` | Content digest `d5331833880756a98ea952b98a6c849c4c04234b46b5271a252bb771339a6ddd`; full tree `62bbfa9b868a780a58a6dd3147154eb6d868a306b6988c8a97e428069239de9d` |

## 4. Accepted source manifest

The accepted M2-3 candidate is uncommitted working-tree content on the baseline
above. Raw SHA-256 of every accepted code, data, test and slice-documentation
body (identical to Implementation Record 01 §2 and `source_freeze_02.json`):

| Path | Bytes | Raw SHA-256 | Slice |
| --- | ---: | --- | --- |
| `engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.py` | 6421 | `0181c6800492c51bd8251c4219a3ea32f81a36810197896965d4ec7b4a10efcb` | M2-3 |
| `engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.yaml` | 1272 | `f71d1def1a53a5ed72de5248a12e4e585d285aa4031949805409f86cfbd55ee7` | M2-3 |
| `engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.py` | 748 | `fafe410879ebb282ca1be329ea266c6c8ca83475e0613b5e661a463b3694c86c` | M2-3 |
| `engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.yaml` | 206 | `c249143d25f7e8cd20f060e1cff02e3666048d131ca08accbc682aac4f98cd6a` | M2-3 |
| `engine/src/battle_engine/starters.py` | 27722 | `f0c0bcc0e74afb3a2de1430e5104091f0e9af1858dce89fa1e79a66c2935477c` | M2-3 |
| `engine/src/battle_engine/agent_scaffold.py` | 12880 | `129f9e0016d11fc7c1b8a2ef2773a92a51d21346d8709d199a51f78eccd69ac5` | M2-3 |
| `app/views/development.py` | 41061 | `6e7f261eca0694d051b05aad8c580d07f5753e548d17ceccb2eff350b692fa59` | M2-3 |
| `engine/src/battle_engine/sensing_demo.py` | 42378 | `37c155516aa674d6fd3df4644158e31457bbae3b6e2eff9d54e8b6309d68f6d0` | M2-3 |
| `engine/src/battle_engine/sensing_playback.py` | 97661 | `fb9be728602a3f8f425b1c9f46296a57c3bc4d19126458ea377b7ff0ec9990a4` | M2-3 |
| `engine/tests/test_v6_alpha_m2_reacquirer.py` | 33705 | `9f420050fa78302d400fe5e5bfcb1b2ecb9c014417606956a2610302f688d0a5` | M2-3 |
| `engine/tests/test_agent_scaffold.py` | 21978 | `aab50d22af076cf65919cfc0360054548ad1f8c344cb0f3a1d7c53e7a0dfa150` | M2-3 |
| `engine/tests/test_v6_alpha_m1_2_window_scout.py` | 46242 | `201625c27043b2a14b7778a1b5cc70864324c06dc475e59ebf7cd13d2b053999` | M2-3 |
| `engine/tests/test_agent_test.py` | 46567 | `d5aea1c476edd6e6c0bcaa3dae333f32186840072639c16be38ab4e3f342bf09` | M2-3 |
| `tests/test_v6_alpha_m1_5_designer.py` | 23414 | `90bbc78b6996b317b4e303539e63ac7e3b43ee77e03c558c04d70bfa82fa03ad` | M2-3 |
| `engine/tests/test_v6_alpha_m2_keeper.py` | 19425 | `f61dc39c5707d131c8ca6843fd790dedf5d2a0bf583c2fbe105d490da0ece62a` | R3-07 amendment |
| `docs/specs/agent_scaffold.md` | 48755 | `573190c173d34d42b3ea87941646ee2cde4afbe07894fc2efec478d87581ecb6` | M2-3 |
| `docs/AGENT_AUTHORING.md` | 30539 | `5d942ae20ec32e74e9d869ddd220b61a72dd6b486974ff96221819887b93edfa` | M2-3 |

The R3-07 amendment's exact diff is published as
[`evidence/m2_3/qualification/r3_07_amendment.diff`](evidence/m2_3/qualification/r3_07_amendment.diff).
Unchanged, as audited by `preservation_02.json`: `client/`, `agent_test.py`,
rules/policy/API/worker/sensing/trace/replay/result modules, Keeper, Scout,
encroaching and stationary sources and digests, packaging configuration and all
research paths. Keeper verifier, Scout evaluator, common reconstruction,
`run_keeper_demo`, `run_sensing_demo` and the resolver are AST-identical to
`4fd89bb`.

## 5. Acceptance matrix

| Gate | Disposition | Primary evidence |
| --- | --- | --- |
| R3-01 capability / entry | **PASS** | Explicit Alpha 1 through CLI, Designer and demo route; stable V4 refused before import, reset or artifacts on every route, in either slot |
| R3-02 R1 behavior | **PASS** | Every §5 row; I1–I3 as confirmed; tie direction, MOVE bounds, parameter bounds and range rejection; one action per callback |
| R3-03 data sources and feedback | **PASS** | AST source audit; refused, null, absent, empty, suppression-delayed and terminal-undelivered feedback; truthful costs |
| R3-04 native sequence | **PASS**, Windows and Linux | R1→R8 at predicted indices in both seats; omniscient 91→155 relocation at F4; no identity, notification or TTL wording |
| R3-05 provenance / false success | **PASS** | Four separate verdicts; negative and mutation cases; Keeper, Scout and R1 verifiers never award one another; `demo.json` stays `unverified` |
| R3-06 authoring | **PASS** for the Designer nodes | Windows 6 and Linux X11 5 native GUI nodes, both seats (external viewer controls: L2) |
| R3-07 compatibility | **PASS** (authorized amendment) | Keeper module 48/48 on Windows and Linux; old starters, digests and order; `[-1] == "v5_dual_team"`; V4 defaults, readers and retired refusal |
| R3-08 engineering / preservation | **PASS** | Ruff; separate engine/client mypy; 329 pins; fresh roots; no research operations |
| R3-09 slice review | **APPROVED** | This record |

The affected M2-AC01/03/04/05/06/09/10/12 subset is satisfied for the
Reacquirer slice only. No M2-wide criterion is closed. M2-AC07/AC08 (symmetric
views, layout) and AC11 (human evaluation) remain open, and M2-5 must still
qualify the frozen M2 candidate as a whole.

## 6. Conditions carried forward

- **L1 — Seat-B perspective.** Seat B's delivered perspective is verified at
  code and cursor level (`SensingCursor(entrant_id="B")`). Interactive A/B
  replay selection in the product viewer is M2-4 work (M2-AC07).
- **L2 — External replay viewer.** The viewer controls (End, seek, resize,
  reopen) were not separately requalified for R1 artifacts. The viewer code is
  unchanged. M2-5 native qualification covers them.
- **L3 — Linux coverage.** WSL2/WSLg X11 only; no Wayland, Xvfb, bare Xorg,
  other distribution, full Python matrix, packaging or installer claim. The v6
  sensing starters are absent from the wheel `package-data` globs; this
  pre-dates M2-3 and lies outside this slice.
- **L4 — M2-2 conditions C1–C3 remain open**, as stated in
  [M2-2 Closure 01 §7](V6_ALPHA_M2_2_CLOSURE_01.md#7-conditions-carried-forward):
  C1 (intermittent Linux End-key non-response, M2-5), C2 (overlapping
  sample-marker labels, M2-4/M2-5) and C3 (qualification limitations). The M1
  history/footer overlap also remains until M2-4.
- **L5 — Skips.** M2-3 added one skip,
  `test_frozen_executable_creates_every_supported_variant[api2-roaming_reacquirer]`,
  under the existing approved reason (no frozen executable). The R3-07 amendment
  added none.

No human comprehension or usability evaluation is claimed (M2-AC11 belongs to
M2-6). This is not M2-wide, Alpha 1 or release acceptance.

## 7. Qualification evidence

Evidence lives in the git-ignored local root `runs/v6_alpha_m2/m2_3_20261015/`.
Paths below are relative to `runs/v6_alpha_m2/`, and hashes bind the retained
bodies. Counts overlap and are not summed. A curated subset is published under
[`evidence/m2_3/`](evidence/m2_3/README.md): both seats' R1 bodies, the
comparison and relocation reports, sanitized Windows and Linux campaign
summaries, the node/skip ledger, the R3-07 diff, the source freezes, the
preservation audit, the retained-attempt ledger and a SHA-256
[evidence index](evidence/m2_3/evidence_index.json) that binds each published
file to its local original.

| Evidence | Result | Raw SHA-256 |
| --- | --- | --- |
| `m2_3_20261015/m2_3_keeper_r307.xml` | Windows Keeper module: 48 passed | `783b94b3a58d62dcfec5f33224dc9435aec6560b1c4e29bccf75680a676ef1ec` |
| `m2_3_20261015/m2_3_reacquirer_r307.xml` | Windows Reacquirer module: 56 passed | `bd86b441f1c2a161933cf30e6e4db4b8c4653ce167199633e8259b158033d8e3` |
| `m2_3_20261015/m2_3_focused_r307.xml` | Windows focused: 626 passed, 4 GUI deselected | `8b198d06deaa4cc8cdea5a07432178854f66c82461bd96a28bc460584c6802bd` |
| `m2_3_20261015/m2_3_broad_r307.xml` | Windows product (138 modules): 3,441 passed, 21 skipped, 5 GUI deselected | `cd0d877011735fa080d955fded648edfb6593bb3a5b1566f5a222402c6103ed4` |
| `m2_3_20261015/m2_3_supplement_final.xml` | Compatibility supplement: 328 passed (reused) | `7724d398b55f156746f59a770880c9caec40c381e8881953d8041e3cf00ac0ae` |
| `m2_3_20261015/m2_3_windows_gui_final.xml` | Windows native GUI: 6 passed (reused) | `13f377a62a4593f4f131b1deaff66514c68d32676b30cb520801558576277187` |
| `m2_3_20261015/m2_3_linux_keeper_r307.xml` | Linux Keeper module: 48 passed | `c0c58fde079c2ab4983a923acb939019d37ac835ebbc546898537585026f7102` |
| `m2_3_20261015/m2_3_linux_focused_r307.xml` | Linux focused: 626 passed, 4 GUI deselected | `d6669cc6e967b8a7a8ab5d1a376a96972a74bbb2327d01a9084a884f0a80da1f` |
| `m2_3_20261015/m2_3_linux_reacquirer.xml` | Linux Reacquirer module: 56 passed (reused) | `6f52ce707a82262cc02a449372c50f75f2d1dc72d6a6688083fd97d6646c492a` |
| `m2_3_20261015/m2_3_linux_gui_x11.xml` | Linux native GUI (Qt xcb): 5 passed (reused) | `177b0974c27cc08fd81d21a797b44434509ded010b32fb9342df75ca95179702` |
| `m2_3_20261015/cross_platform_comparison.json` | Eight R1 bodies complete; per-seat logical equality across repeats and platforms; Linux K1 equal to published M2-2 | `692225f4ea3fe7d694cc9fd8a8de567feb6a07563ea8774bf4648941d345c02e` |
| `m2_3_20261015/scenario_comparison.json` | Windows R1 witnesses; Windows K1 replay byte-equal to published M2-2 | `0513fb8e084a064c055f04f65768401d4524dad9c7b87ce47893d6140dc7d7ec` |
| `m2_3_20261015/relocation_check_r307.json` | Fixture relocation and isolation, 8 bodies | `e4eee99e949eac6349c08ad9da73e9ac321cd9bb4e5aaf5e75cd9e30f1e3f673` |
| `m2_3_20261015/source_freeze_02.json` | 16 first-pass paths unchanged plus the R3-07 path | `1ac13e17f752d51c64590129cb21ecb87817d637b790cded05f6380dd44a0dd4` |
| `m2_3_20261015/preservation_02.json` | Preservation, pins and exact R3-07 diff: PASS | `f49565d48aaa6d30e115e9324deabe62b7162f01aafcd65d5cf87a566067d77b` |
| `m2_3_20261015/selection_ledger_r307.json` | Only outcome change: the R3-07 node, failure → passed | `15bd9fb15ddccd71f04db179613372432c4a7e7749b9ec14335eacc0a4a5a44f` |

The re-executed comparison reports (`*_r307.json`) are byte-identical to the
originals above. Ruff, both mypy runs, the retained first-pass failures and the
reuse rationale are in Implementation Record 01 §§4 and 9. Platforms: Windows
11 AMD64, Python 3.13.7, native Qt/SDL; Ubuntu on WSL2 (kernel 6.6.87.2),
Python 3.12.3, PySide6 xcb on WSLg `DISPLAY=:0`.

## 8. M2-2 evidence README erratum (separate change)

[M2-2 Closure 01](V6_ALPHA_M2_2_CLOSURE_01.md) published a curated evidence
README stating that "the Keeper bodies use CRLF line endings". As
Implementation Record 01 §10 noted, that is inaccurate. Git's recorded
end-of-line state (`git ls-files --eol`) shows that only the two `trace.jsonl`
bodies are CRLF among the Keeper bodies, together with five qualification files
and the comparison report. Every `demo.json`, `replay.jsonl`, `result.json` and
source snapshot is LF.

The correction is a separately identifiable documentation change limited to
two files:

| Path | Published (`4fd89bb`) | Corrected |
| --- | --- | --- |
| `docs/v6/evidence/m2_2/README.md` | 10,062 bytes, `0d1ebd2d066b4b40028208c19b25be91d4c53e8e0d879aa3966ec112650d72b1` | 10,743 bytes, `555e6211230a9386a6d25946cc675ad16f521536cb060932c738fd6c32eaf90a` |
| `docs/v6/evidence/m2_2/evidence_index.json` | README entry binds the published hash | README entry binds the corrected hash; its note keeps the published bytes and hash |

The corrected paragraph lists the actual CRLF files and carries a dated
erratum note. No M2-2 evidence body, byte or other hash changed, and the M2-2
index again verifies all 29 entries. Local diff:
`runs/v6_alpha_m2/m2_3_closure_20261015/m2_2_erratum.diff`
(`96352cafc7d0314e8015e2732c6e22b16616453d2ec8419589805388e777aba6`). The
`.gitattributes` comment in that directory ("bind SHA-256 values of CRLF
bodies") remains accurate, because the bound traces are CRLF, and is unchanged.

## 9. Publication manifest and proposal

The closure prepares, but does not perform, two commits on `v6-m2-clean` on top
of `4fd89bb` (= live `origin/v6-research`), to be fast-forwarded to
`origin/v6-research` only after explicit authorization:

| Commit | Paths | Content |
| --- | ---: | --- |
| 1. `docs(v6-m2): correct M2-2 evidence README line-ending erratum` | 2 | `docs/v6/evidence/m2_2/README.md`, `docs/v6/evidence/m2_2/evidence_index.json` |
| 2. `feat(v6-alpha1): complete M2-3 Roaming Reacquirer milestone` | 54 | The 17 accepted paths in §4; `docs/v6/V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md`; this record; [M2-4 Entry Decision 01](V6_ALPHA_M2_4_ENTRY_DECISION_01.md); the 32 files under `docs/v6/evidence/m2_3/`; status edits to `README.md` and `docs/ROADMAP.md` |

The erratum goes first, so the M2-2 correction is reviewable and revertible on
its own and is not mixed into the M2-3 diff. Items for the lead to note:

- `README.md` and `docs/ROADMAP.md` receive status-line edits only: M2-3
  accepted, M2-4 entry review prepared and not authorized. They follow the M2-2
  closure precedent.
- The curated package adds about 2.2 MB, mostly the two R1 traces (~1 MB each).
  The full local root (`runs/v6_alpha_m2/m2_3_20261015/`) is not published.
- The repository's global `*.jsonl` ignore rule matches the four curated
  `replay.jsonl`/`trace.jsonl` bodies. As with the tracked M2-2 bodies, they
  must be added explicitly (`git add -f`), with no `.gitignore` change. The
  package's `.gitattributes` (`* -text`) preserves their raw bytes.
- The local `v6-research` divergence (`2fc3c82`) stays separate and is not part
  of this proposal.
- The exact per-path manifest (path, bytes, SHA-256, commit assignment) is
  generated by the closure validation (§10) after this record is final. It is
  reported to the lead with the publication request rather than embedded here,
  because this record cannot contain its own hash.

## 10. Closure validation

`runs/v6_alpha_m2/m2_3_closure_20261015/closure_validate.py` checks the
following read-only and writes its result and the publication manifest beside
itself:

- HEAD and the live remote parent;
- that nothing is staged;
- that the dirty set equals exactly the 56 proposed paths;
- that every accepted code, data and test body still matches §4, so no
  relevant tested input changed after acceptance;
- the M2-2 and M2-3 evidence indexes;
- the R1 verifier over the curated copies;
- every hash cited in this record;
- local links and anchors in the affected documents;
- UTF-8, LF and trailing whitespace in the new and edited Markdown;
- `git diff --check`;
- the 329 historical pins.

Its outcome is reported with the publication request.

## 11. Exclusions and release limitations

This closure covers the Reacquirer slice only. It does not authorize M2-4
implementation, M2-5 or M2-6, an M2-wide technical PASS, a human-evaluation
PASS, staging, commit, merge, push, tag, publication or a Bytefray 5.1
release. Stable `bytefray-rules-4` remains the default, and
`bytefray-rules-6-alpha1` remains explicitly selected and experimental. The
limitations retained from M2-2 still apply: the M1 history/footer overlap, the
rewind-reconstruction cost, Windows COM `0x8001010d`, the X11 focus prerequisite,
the teaching-only Python/seed threat model, exact teaching success only for the
declared default fixture profile, and no full Python matrix, installer,
packaging, accessibility or Wayland claim. No E8/E9 harness, private input,
entropy or authority operation, reseal or scientific execution occurred, and no
E8/E9 research artifact was modified. Original E9 remains operationally blocked
with execution LOCKED, and Requirement C remains NOT ESTABLISHED.
