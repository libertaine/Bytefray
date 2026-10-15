# Bytefray V6 — M2-3 Roaming Reacquirer implementation record 01

2026-10-15, America/Indianapolis. **Technical-acceptance package after the
approved R3-07 amendment. Recommendation: PASS WITH CONDITIONS (§11).**

Roaming Reacquirer R1, the relocating fixture, registration, personal copies,
Designer/demo integration and the trusted `reacquirer-R1` verifier are
implemented within the entry-packet boundary. The engine reproduces the approved
§6.2 schedule and every predicted §7 witness exactly, in both seats, on Windows
and Linux, with byte-identical replays across repeats and platforms.

The first qualification pass stopped at HOLD for a boundary conflict (§7): one
accepted Keeper test asserted the previous three-name catalog suffix. The project
lead then authorized a targeted amendment (R3-07) to correct that one assertion
and confirmed rulings I1–I3. The corrected assertion now passes on Windows and
Linux, with no other outcome change in any rerun selection (§9). All changes
remain unstaged and uncommitted. M2-4 was not started.

## 1. Entry state and authority

The project lead authorized M2-2 publication, then M2-3 implementation after
publication was verified, together with rulings I1–I3. Entry was verified as follows:

| Check | Result |
| --- | --- |
| Published M2-2 | `4fd89bbfdc6845815a0df6d4d60eab92cc3a0a94` (`feat(v6-alpha1): complete M2 Watchful Keeper milestone`), tree `109cf38b45175fdee1023fd620f0ead70384ad56`, parent `f79a74b…` |
| Remote | `origin/v6-research` = `4fd89bb…` after fetch; local `v6-m2-clean` ahead/behind 0/0 |
| Index / tree | Nothing staged; working tree clean at M2-3 entry |
| Divergent local branch | `v6-research` unchanged at `2fc3c82e115650b515a4efab39afb172b62535ed` |
| Contract | [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md) §§2, 3, 5, 6.2, 7, 10 and 11; [entry packet](V6_ALPHA_M2_3_ENTRY_DECISION_01.md) §§3–9 |
| Historical pins | 329 at preserved `b948540…`, zero mismatches |

Re-verified at the R3-07 amendment (`preservation_02.json`, all PASS): HEAD is
still `4fd89bb…` on `v6-m2-clean` (parent `f79a74be…`), nothing is staged, the
local `v6-research` is unchanged, and the 329 pins still have zero mismatches.
The candidate is the 18 paths in §2, and no path outside the amended boundary is
dirty. No reset, rebase, merge, branch switch or discard occurred.

### Approved edge-case rulings I1–I3 (lead-confirmed)

The lead's amendment confirms these rulings. Each one was checked against the
normative Scope 03 §5 text, the agent (`v6_roaming_reacquirer/agent.py`) and
the independent verifier model (`_ReacquirerModel` in `sensing_playback.py`).
**No ruling conflicts with Scope 03**, and none needed a code change.

| Ruling (as approved) | Scope 03 §5 basis | Agent and verifier behavior | Existing coverage |
| --- | --- | --- | --- |
| **I1 — Empty first search.** Move forward by `move_step`, then search again under the accepted no-contact policy. Do not invent a contact position. | "SEARCH applied empty receipt": retain the empty sample, MOVE forward, request a new anchor-relative scan; no old-address absence | The empty receipt returns `MOVE(+move_step)`. The mode stays SEARCH, no target is created, and nothing is recorded in `findings`. The next callback SENSEs `(anchor + search_offset) % arena`. A later positive receipt is an initial contact (HOLD, no WRITE). The verifier mirrors this and records no contact or absence point | `test_i1_empty_first_search_stays_in_discovery_without_inventing_a_target` (two empty searches, then a positive one) |
| **I2 — Refused rescan.** Return to ordinary search, not search-after-absence. No observation is received and no stale information becomes fresh. | "Refused/null/absent scan feedback": no absence or positive transition; resume a fresh anchor-relative search, keeping historical samples | When a rescan's feedback is not applied or carries no sample, the agent and the verifier set the mode to SEARCH and drop the active target, whatever search produced it. No sample is added and the retained samples keep their original tick. The next positive receipt is again an initial contact, never a new-contact WRITE | `test_i2_refused_null_or_absent_rescan_infers_nothing_and_keeps_original_age` (four variants: refused/None, applied/None, refused with a sample, refused/empty); `test_valid_prefix_without_reacquisition_and_tampered_receipt_cannot_complete` (verifier refuses a refused-looking receipt in place of the R6 absence) |
| **I3 — Fallback accounting.** Count a fallback decision when the designated legal fallback action is emitted. Do not classify it as a successful reacquisition, and do not count its consequences as another fallback. | "A substituted fallback does not count as a SENSE, rescan receipt, repair, search MOVE or successful response witness" | Only `_search` emits the fallback (`READ own_core_base` in reach, otherwise `MOVE(0)`). It increments `fallbacks` (agent) or appends one `fallback` point (verifier) at that emission. Nothing is added to contact, absence, reacquisition or response. The next callback is not a receipt; it retries SEARCH and adds no count unless it emits a new fallback itself | `test_i3_fallback_is_counted_once_per_emitting_callback_and_never_a_scan` (5 emissions give 5 counts; the follow-on SENSE adds none; `MOVE(0)` branch); `test_illegal_rescan_center_resumes_search_without_absence`; native `fallback_points == ()` in both seats |

Notes for the lead:

- **Entry-packet wording superseded for I2.** Entry packet §3 proposed resuming
  "the prior search family (SEARCH, or SEARCH_AFTER_ABSENCE if that mode produced
  the target)". The approved ruling, "ordinary search, not search-after-absence",
  supersedes it. The implementation already followed the approved ruling. The
  refused-rescan branch keeps no record of which search produced the target, so
  it has one path, and the existing I2 cases exercise it. No test was added.
- **Outside I2's scope, recorded for completeness.** A refused *search* SENSE
  (not a rescan) issued in SEARCH_AFTER_ABSENCE stays in that mode
  (`test_i2_refused_search_after_absence_keeps_that_search_mode`), because its
  absence came from an earlier applied receipt. This follows §5's "resume a
  fresh anchor-relative search", and the I2 ruling does not address it.
- **Seats.** The supplied-observation cases need no seat parameter: the agent
  receives no seat identity (AST data-source audit,
  `test_source_audit_uses_only_delivered_observation_and_own_state`). The
  both-seat native requirement (M2-AC03, R3-04) covers the R1→R8 sequence. In
  that sequence, I1–I3 correctly do not fire in either seat: R1 is positive,
  R5 is an applied empty rescan and `fallback_points` is empty. That is
  asserted in both seats by `test_native_both_seats_reproduce_predicted_witnesses`,
  and the verifier re-checks it over all eight retained bodies. No R3 criterion
  needs per-seat native exercise of I1–I3, so no test was added.

## 2. Exact M2-3 change list

18 paths against `4fd89bb`. Hashes are raw working-tree SHA-256. The first 16
were frozen at `source_freeze_01.json` and re-verified **byte-identical** at
`source_freeze_02.json` after the amendment. The Keeper test module is the only
new code path. This record, the 18th path, is the package itself.

| Path | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.py` (new) | 6421 | `0181c6800492c51bd8251c4219a3ea32f81a36810197896965d4ec7b4a10efcb` |
| `engine/src/battle_engine/data/starter_agents/v6_roaming_reacquirer/agent.yaml` (new) | 1272 | `f71d1def1a53a5ed72de5248a12e4e585d285aa4031949805409f86cfbd55ee7` |
| `engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.py` (new) | 748 | `fafe410879ebb282ca1be329ea266c6c8ca83475e0613b5e661a463b3694c86c` |
| `engine/src/battle_engine/data/teaching_fixtures/v6_relocating_opponent/agent.yaml` (new) | 206 | `c249143d25f7e8cd20f060e1cff02e3666048d131ca08accbc682aac4f98cd6a` |
| `engine/src/battle_engine/starters.py` | 27722 | `f0c0bcc0e74afb3a2de1430e5104091f0e9af1858dce89fa1e79a66c2935477c` |
| `engine/src/battle_engine/agent_scaffold.py` | 12880 | `129f9e0016d11fc7c1b8a2ef2773a92a51d21346d8709d199a51f78eccd69ac5` |
| `app/views/development.py` | 41061 | `6e7f261eca0694d051b05aad8c580d07f5753e548d17ceccb2eff350b692fa59` |
| `engine/src/battle_engine/sensing_demo.py` | 42378 | `37c155516aa674d6fd3df4644158e31457bbae3b6e2eff9d54e8b6309d68f6d0` |
| `engine/src/battle_engine/sensing_playback.py` | 97661 | `fb9be728602a3f8f425b1c9f46296a57c3bc4d19126458ea377b7ff0ec9990a4` |
| `engine/tests/test_v6_alpha_m2_reacquirer.py` (new) | 33705 | `9f420050fa78302d400fe5e5bfcb1b2ecb9c014417606956a2610302f688d0a5` |
| `engine/tests/test_agent_scaffold.py` | 21978 | `aab50d22af076cf65919cfc0360054548ad1f8c344cb0f3a1d7c53e7a0dfa150` |
| `engine/tests/test_v6_alpha_m1_2_window_scout.py` | 46242 | `201625c27043b2a14b7778a1b5cc70864324c06dc475e59ebf7cd13d2b053999` |
| `engine/tests/test_agent_test.py` | 46567 | `d5aea1c476edd6e6c0bcaa3dae333f32186840072639c16be38ab4e3f342bf09` |
| `tests/test_v6_alpha_m1_5_designer.py` | 23414 | `90bbc78b6996b317b4e303539e63ac7e3b43ee77e03c558c04d70bfa82fa03ad` |
| `docs/specs/agent_scaffold.md` | 48755 | `573190c173d34d42b3ea87941646ee2cde4afbe07894fc2efec478d87581ecb6` |
| `docs/AGENT_AUTHORING.md` | 30539 | `5d942ae20ec32e74e9d869ddd220b61a72dd6b486974ff96221819887b93edfa` |
| `engine/tests/test_v6_alpha_m2_keeper.py` (**R3-07 amendment**) | 19425 | `f61dc39c5707d131c8ca6843fd790dedf5d2a0bf583c2fbe105d490da0ece62a` |
| `docs/v6/V6_ALPHA_M2_3_IMPLEMENTATION_RECORD_01.md` (new) | — | this record |

Revision identities: `v6_roaming_reacquirer` content digest
`65866988dd2dfdddd9782a8040d932dc84f05cec9b5d6feab3fb6a73c9697f21`, full tree
`4e96e499365083bcae2b5eca1c71471c0594e8e638235deaf7dd0403e19282b1`;
`v6_relocating_opponent` content digest
`d5331833880756a98ea952b98a6c849c4c04234b46b5271a252bb771339a6ddd`, full tree
`62bbfa9b868a780a58a6dd3147154eb6d868a306b6988c8a97e428069239de9d`.

Change summary, in the order of entry packet §4:

- **Starter and fixture.** R1 implements every §5 row with parameters
  `search_offset` 91 (0..128), `move_step` 64 (1..64) and `rescan_wait` 3
  (1..8). It declares capability v1 `[sense]` and a `standard` preset.
  Movement uses the shortest signed direction (forward on a tie), and a MOVE is
  never larger than `move_step` or 64. The response byte is `0x52`. Inputs are
  only the delivered `previous_sense_anchors`, `previous_action_applied`,
  `previous_action_tick` and own-state fields; passive visibility and READ
  feedback are not used. The fixture issues F1–F3 `READ own_core_base`, then
  F4 `MOVE(+64)`, then READ. It moves on its own callback count only, and it
  is neither a starter nor a template.
- **Registry and copies.** `v6_roaming_reacquirer` comes after
  `v6_watchful_keeper` and before `v5_dual_team`; only its digest is added. The
  scaffold's two-name set and binary label branch became one label map, with
  identical Scout/Keeper behavior. The Designer gains the label "Roaming
  Reacquirer — personal copy" and a hint text naming the third starter.
- **Demo route.** `run_reacquirer_demo` and `--scenario reacquirer-R1
  --reacquirer-seat`. `run_keeper_demo`, `run_sensing_demo` and the resolver
  are AST-identical to `4fd89bb`.
- **Verifier.** `ReacquirerPolicyWitnesses`, `ReacquirerScenarioVerification`,
  a private independent `_ReacquirerModel`, `evaluate_reacquirer_policy` and
  `verify_reacquirer_scenario`. The Keeper verifier, Scout evaluator and common
  reconstruction are AST-identical. No persisted field, schema or enum was
  added, and `demo.json` stays v1 `unverified` without `teaching_exchange`.
- **Tests and docs.** Template set and catalog suffix (scaffold, Scout and,
  under the R3-07 amendment, Keeper modules); Reacquirer added to the
  explicit-Alpha 1 and stable-rejection CLI parametrizations; two `gui`
  Reacquirer seat cases; scaffold spec addendum and an authoring paragraph.

Unchanged, as verified by `preservation.json` and again by `preservation_02.json`:
`client/`, `agent_test.py`, rules/policy/API/worker/sensing/trace/replay/result
modules, Keeper, Scout, encroaching and stationary sources and digests,
README/ROADMAP, packaging configuration and all research paths. Apart from the
one authorized assertion, the Keeper test module is also unchanged; see §9.

## 3. Behavior evidence

### Native schedule (§6.2 / §7), both seats

Witnesses are given as zero-based global decision indices in tick 1. Each one was
observed in the engine, verified independently, and is identical across repeats
and platforms:

| Seat | R1 SENSE91 | R2 receipt + READ0 | R5 rescan SENSE91 → `()` | R6 empty receipt + MOVE(+64) | R7 SENSE155 | R8 receipt + WRITE155 `0x52` | Fixture F4 MOVE(+64) → 155 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R=A, F=B | 0 | 1 | 8 | 9 | 12 | 13 | 7 |
| F=A, R=B | 2 | 3 | 10 | 11 | 14 | 15 | 5 |

The prediction table in entry packet §7 matches exactly. Both entrants are alive
at tick 100, and WRITE155 never touches the fixture core 91..98. After R8, R1
cycles HOLD → rescan at 155 with no further WRITE, which is the expected tail.
`reacquirer-R1` verdicts: artifact consistency, reconstruction, source capture
and completion are all `True` in all runs. `fallback_points` is empty, as
expected: the search-center distance of 91 never exceeds reach 128 in the
declared profile.

### Entrant view (cursor level, both seats)

`SensingCursor(entrant_id=<R seat>)` shows only contact 91 while R5 is pending.
At R6 the receipt is `EMPTY`, and 91 is retained with
`not_present_in_newer_sample` = (tick 1, callback 5). At R8, 91 is still shown
with its absence mark, and 155 appears as a separate fresh contact. Event text
contains no same-opponent, moved, reacquired, identity, TTL or notification
wording. The fixture's own view has no contacts or samples. The seat-B product
viewer remains an M2-4 dependency.

### Supplied-observation and native feedback cases

`engine/tests/test_v6_alpha_m2_reacquirer.py` has 56 cases:

- the full R1 sequence at anchors 0/133/509;
- rescan present and rescan absent, with other addresses kept as separate samples;
- in-reach contact, using the smallest address, with one WRITE;
- out-of-reach RESPONSE with tie-forward, backward and `move_step` 10 bounds;
- I1, I2 (four refused/null/absent variants, plus a SEARCH_AFTER_ABSENCE refusal) and I3 (no sensing, illegal center, own core out of reach);
- illegal rescan center, unrelated feedback and reset;
- eight range rejections and the inclusive bounds;
- an AST data-source audit of both sources;
- copy, overwrite refusal and registration;
- stable-V4 preflight on the direct, validate, worker-load and worker-handle routes;
- native both-seat witnesses and repeat equality, cross-verifier refusal, entrant views and eight provenance/false-success mutations;
- a valid prefix without reacquisition, tampered absent and refused receipts, and seeded non-zero starts;
- native suppression-delayed delivery (tick 2, original sample point kept, processed once) and terminal non-delivery;
- unsafe-output and evidence-preservation runner checks.

## 4. Qualification campaigns (first pass, retained)

Evidence root: git-ignored local `runs/v6_alpha_m2/m2_3_20261015/`. Each campaign
keeps its log, JUnit and `*_command.json` (argv, cwd, interpreter, environment,
exit code, duration), with fresh repo-local `.pytest-tmp`/`.pytest-cache`
leaves. Counts overlap and are not summed. The R3-07 reruns are in §9. This table
is the first-pass evidence, kept unchanged, including its failures.

| Campaign | Selection | Result |
| --- | --- | --- |
| `m2_3_reacquirer_final` | New module | **56 passed** |
| `m2_3_keeper_final` | Keeper module (unchanged) | **47 passed, 1 failed**: catalog suffix, §7 |
| `m2_3_focused_final` | `test_agent_test.py` + retained 22-module selection | **625 passed, 1 failed** (same node), 4 GUI deselected |
| `m2_3_windows_gui_final` | Reacquirer A/B, Keeper A/B, Scout Test, Windows window smoke; `-m gui` | **6 passed**; native Qt windows, real QProcess children |
| `m2_3_broad_final` | Retained 137-module product selection + new module (138) | **3,440 passed, 1 failed** (same node), 21 skipped, 5 GUI deselected |
| `m2_3_supplement_final` | `docs/v6/evidence/m1_6a_windows/supplemental_nodes.txt` | **328 passed** |
| `m2_3_ruff_final` | `ruff check .` | **PASS** |
| `m2_3_mypy_engine_final` / `m2_3_mypy_client_final` | Separate invocations | **PASS**: 106 files (+2 new agent modules) / 19 files |
| `scenario_reacquirer_{A,B}_{1,2}` | CLI `--scenario reacquirer-R1` | **4 complete**; exit 0 |
| `scenario_keeper_{A,B}_1` | CLI `--scenario keeper-K1` regression witness | **2 complete**; replay byte-identical to the published M2-2 bodies, trace/result logically equal |
| Linux campaigns | See §5 | Reacquirer 56 passed; focused 625 passed / 1 failed (same node); GUI 5 passed; 4 R1 + 2 K1 complete |

Node/skip ledger (`selection_ledger.json`, against the retained M2-2A JUnit):

- **Broad selection, 3,394 → 3,462 nodes: +72 / −4.** Added: 56 Reacquirer
  cases; 10 `test_agent_test` cases (2 new explicit-Alpha 1, plus the 4
  stable-rejection nodes re-emitted for both templates, giving 8); 3
  automatic `test_frozen_scaffold_resources` template variants; 1
  `test_starter_directory_validity` starter; 2 `test_windows_packaging_spec`
  frozen-tree variants. The 4 removed names are the renamed stable-rejection
  nodes, which now carry a `template` id.
- **Skips: 20 → 21.** The new skip is
  `test_frozen_executable_creates_every_supported_variant[api2-roaming_reacquirer]`,
  with the existing approved reason (no frozen executable). The two symlink
  skips differ only in their scratch-path label.
- **Only outcome change:** the Keeper catalog node.
- **Focused selection, 619 → 626 nodes:** the same +11/−4 CLI and starter
  accounting.
- **Supplement:** identical 328 nodes.

Retained failed attempts, kept under their own names and never relabeled:

| Attempt | Outcome | Classification |
| --- | --- | --- |
| `m2_3_reacquirer_01` | 54 passed / 2 failed | Test harness: a numeric string `"64"` is legitimately coerced by the canonical resolver; an import sentinel was inserted before `from __future__`. Fixed in `_02` |
| `m2_3_reacquirer_02`, `_03`, `m2_3_focused_01`, `m2_3_keeper_01`, `m2_3_windows_gui_01`, `m2_3_ruff_01`, `m2_3_mypy_*_01` | Pre-freeze | `ruff_01` found 4 style findings in new code (two `min()` forms, one implicit concatenation, import order). The fix changed the starter bytes and its pinned digest, so every final campaign was rerun after the freeze |
| `m2_3_keeper_final`, `m2_3_focused_final`, `m2_3_broad_final`, `m2_3_linux_focused` | 1 failure each, same node | The §7 boundary conflict: an obsolete Keeper catalog assertion. Resolved by the R3-07 amendment (§9); these failed campaigns are retained unchanged |
| `linux_campaign_focused.out` | Launch failure | Git Bash path conversion rewrote `/mnt/d/…` before WSL received it, so nothing executed. Relaunched through PowerShell as `_02` |
| First `cross_platform_comparison` pass | FAIL (overwritten) | Comparator harness: it compared `result.json` `product_version`, a build label (`5.0.0` from installed metadata on Windows, `development checkout` in the user-local Linux environment). The rerun excludes that field, as M2-2A did, and finds no other difference. The overwritten output was stdout only |

## 5. Linux

Ubuntu on WSL2 (kernel 6.6.87.2), Python 3.12.3, the retained user-local
environment (`work/m2_2a_linux_env`, X11 libraries under `work/m2_2a_linux_x11`)
and PySide6 xcb on WSLg `DISPLAY=:0`. Scripts:
`runs/v6_alpha_m2/m2_3_20261015/linux_campaign.sh` and, for the amendment,
`linux_campaign_r307.sh` (same environment; Keeper module and focused selection
only, new labels). No system packages were installed.

| Campaign | Result |
| --- | --- |
| `m2_3_linux_reacquirer` | **56 passed** |
| `m2_3_linux_focused` (same 23 modules) | **625 passed, 1 failed** (the §7 Keeper catalog node), 4 GUI deselected; 316.6 s. Retained failed campaign |
| `m2_3_linux_keeper_r307` | **48 passed**, exit 0; 22.2 s |
| `m2_3_linux_focused_r307` (same 23 modules) | **626 passed**, 4 GUI deselected, exit 0; 318.0 s |
| `m2_3_linux_gui_x11` | **5 passed**: Reacquirer A/B, Keeper A/B, Scout Test; native Qt xcb, real QProcess children |
| `linux_reacquirer/{A,B}/{1,2}` | **4 complete**; witnesses identical to Windows |
| `linux_keeper_regression/{A,B}/1` | **2 complete**; logically equal to the published M2-2 bodies |

`cross_platform_comparison.json`: **PASS**. Replays are byte-identical across
repeats and platforms per seat (R1 `3fa395b1…` for seat A and `5cf6e3ce…` for
seat B; K1 replays equal the published `5c1184cf…` and `dbbbd070…`). Ordered
traces excluding only `wall_time_ms`, and results excluding occurrence ID,
completion time and the `product_version` build label, are logically equal.
Every raw body is hashed separately, and no raw cross-platform equality of
trace or result is claimed. The comparison was re-executed at the amendment
(`cross_platform_comparison_r307.json`); its report is identical to the
original, including every raw body hash.

## 6. Acceptance matrix (after the R3-07 amendment)

| ID | Disposition | Evidence |
| --- | --- | --- |
| R3-01 | **PASS** | Exact capability block; explicit Alpha 1 succeeds through the CLI (supervised personal copy and opponent), the Designer (Validate, Advanced, Test) and the demo route. Stable V4 is refused before import, reset or artifacts on the direct, validate, worker and Development Test routes, in either slot. Malformed blocks are covered by retained generic cases in the focused and broad runs, which pass again in `_r307` |
| R3-02 | **PASS** | Every §5 row, I1–I3 as approved (§1), tie direction, MOVE bounds, parameter bounds and range rejection, one action per callback |
| R3-03 | **PASS** | AST source audit; refused, null, absent and empty supplied cases; native suppression-delayed and terminal-undelivered cases; unrelated READ is not a receipt; every action costs 1 in the verifier |
| R3-04 | **PASS**, Windows and Linux | R1→R8 at predicted indices in both seats; omniscient 91→155 relocation at F4 (indices 7/5), re-checked over all 8 retained bodies (`relocation_check_r307.json`); no identity, notification or TTL wording |
| R3-05 | **PASS** | Four separate verdicts; refusal for a prefix, false success or claim, wrong source or archetype, seat, parameters, drift, binding or missing source; Keeper and R1 verifiers refuse each other; Scout `verify_demonstration` refuses R1 artifacts; `demo.json` stays `unverified` |
| R3-06 | **PASS** for the Designer nodes, Windows (6) and Linux X11 (5) | Copy → stable refusal → explicit Alpha 1 Validate → edited 64/32/2 Advanced full match → result-associated reopen → earlier-settings label → range rejection → overwrite refusal → manifest-default Test, both seats. External viewer controls were not rerun (viewer unchanged; limitation L2) |
| R3-07 | **PASS** (after the authorized amendment) | Keeper module **48/48** on Windows and Linux. Old starter bytes and digests, Keeper's `35b945ad…` included; catalog order Scout → Keeper → Reacquirer → `v5_dual_team`; `[-1] == "v5_dual_team"`; V4 defaults, readers, retired refusal and Scout all pass. The only Keeper test change is the one approved assertion, audited as exact (§9) |
| R3-08 | **PASS** | Ruff; separate engine/client mypy (rerun at `_r307`); 329 pins; fresh roots, with the runner refusing reuse of an existing leaf; no research operations |
| R3-09 | **OPEN, for lead review** | This package. No automatic M2-4 entry |

## 7. Boundary conflict (first pass) — resolved by the R3-07 amendment

First-pass finding, retained as written: `engine/tests/test_v6_alpha_m2_keeper.py:175`
asserted `STARTER_AGENT_NAMES[-3:] == ("v6_window_scout", "v6_watchful_keeper", "v5_dual_team")`.
Contract §3 and entry packet §6 require the order Scout → Keeper → Reacquirer →
`v5_dual_team`, so that assertion could not hold once M2-3 registered its
starter. Entry packet §4 permitted catalog-suffix edits only in the scaffold and
Scout test modules, and §8 made any other path a stop condition, so the file was
not edited and the candidate stopped at HOLD.

Resolution: the lead approved a targeted amendment that adds this file to the
boundary for this one assertion only. The edit and its verification are in §9.
Keeper and Scout agent logic, common reconstruction, `client/`, `agent_test.py`
and ruleset semantics were not touched.

## 8. Retained demonstration evidence (validated at the amendment)

The witness schedule and fixture are unchanged; neither was tuned. All 16 first-pass
source paths are byte-identical between `source_freeze_01.json` and
`source_freeze_02.json`. That includes the fixture, the starter, `sensing_demo.py`
and `sensing_playback.py`, so the retained bodies remain valid for the current
candidate. They were re-verified read-only, without re-execution:

| Check | Result |
| --- | --- |
| Exact approved witness schedule, both seats | `scenario_comparison_r307.json` PASS: seat A contact (1,1), absence (1,9), reacquisition and response (1,13); seat B (1,3), (1,11), (1,15); `fallback` empty; report identical to `scenario_comparison.json` |
| Fixture relocation | `relocation_check_r307.json` PASS, 8/8 bodies (Windows and Linux, both seats, both repeats): fixture actions READ, READ, READ, MOVE(+64); exactly one MOVE at (1,7) seat A or (1,5) seat B; fixture anchor 155 afterwards |
| Legal sensing and reacquisition decisions | `verify_reacquirer_scenario` complete on all 8 bodies (the independent model replays every R decision and refuses any illegal or divergent one) |
| No scan notification or hidden information | The fixture never SENSEs or WRITEs and receives no sensed anchors in any body; the entrant-view test asserts no identity/moved/TTL wording and an empty fixture view (passes in `_r307`) |
| Deterministic replay bytes | R1 replay `3fa395b1…` (seat A) / `5cf6e3ce…` (seat B), identical across both repeats on both platforms |
| Windows/Linux agreement | `cross_platform_comparison_r307.json` PASS, identical to the original report |
| Keeper compatibility | K1 regression replays byte-equal to the published M2-2 bodies (`5c1184cf…`, `dbbbd070…`), Keeper repair/defensive witnesses unchanged (A (3,24)/(1,8); B (1,6)/(1,10)); Keeper module 48/48 |
| Historical starter preservation | `preservation_02.json`: old starter bytes and digests, Keeper digest `35b945ad…`, catalog order and terminal `v5_dual_team` PASS |

## 9. R3-07 amendment: correction and final qualification

### Exact correction diff

The only edit made under the amendment, against blob `5d60a2f803ca14e79e4d67f2d1eebf1fc6141c23`
at `4fd89bb` (byte-identical to HEAD immediately before the edit):

```diff
--- a/engine/tests/test_v6_alpha_m2_keeper.py
+++ b/engine/tests/test_v6_alpha_m2_keeper.py
@@ -172,7 +172,9 @@ def test_personal_copy_manifest_and_source_retention_and_overwrite_refusal(tmp_p
     with pytest.raises(AgentScaffoldError, match="already exists"):
         create_agent("my_keeper", data_root=tmp_path, resource_root=ROOT, template="watchful_keeper")
     assert "v6_encroaching_opponent" not in STARTER_AGENT_NAMES
-    assert STARTER_AGENT_NAMES[-3:] == ("v6_window_scout", "v6_watchful_keeper", "v5_dual_team")
+    assert STARTER_AGENT_NAMES[-4:] == (
+        "v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer", "v5_dual_team",
+    )
     assert starter_content_digest(KEEPER) == CURRENT_STARTER_DIGESTS["v6_watchful_keeper"]
```

`v6_roaming_reacquirer` is the identifier actually registered in
`starters.py` (`STARTER_AGENT_NAMES` and `CURRENT_STARTER_DIGESTS`). The form
matches the Scout module's earlier suffix edit. The personal-copy, digest,
rejection, compatibility and behavior assertions, the fixture and its schedule
are untouched. `preservation_02.json` check
`r3_07_keeper_test_diff_is_catalog_suffix_only` proves the current file equals
the `4fd89bb` blob with exactly that one line replaced.

### Campaigns

Commands use the retained runner (`run.py <label> …`) with the repo `.venv`
interpreter (Windows: Python 3.13.7, Windows-11-10.0.26120) and fresh
`.pytest-tmp/<label>` and `.pytest-cache/<label>` roots.

| Campaign | Command (after `run.py <label>`) | Result |
| --- | --- | --- |
| `m2_3_keeper_r307` (run first) | `pytest engine/tests/test_v6_alpha_m2_keeper.py` | **48 passed**, exit 0 |
| `m2_3_reacquirer_r307` | `pytest engine/tests/test_v6_alpha_m2_reacquirer.py` | **56 passed**, exit 0 |
| `m2_3_focused_r307` | `pytest engine/tests/test_agent_test.py @docs/v6/evidence/m2_2/qualification/m2_2_focused_selection.txt` | **626 passed**, 4 GUI deselected, exit 0 |
| `m2_3_broad_r307` | `pytest @runs/v6_alpha_m2/m2_3_20261015/m2_3_broad_selection.txt` (138 modules) | **3,441 passed, 21 skipped, 0 failed**, 5 GUI deselected, exit 0; 300.0 s |
| `m2_3_ruff_r307` | `ruff check .` | **PASS** |
| `m2_3_mypy_engine_r307` / `m2_3_mypy_client_r307` | `mypy engine/src/battle_engine` / `mypy client/src/battle_client` | **PASS**: 106 / 19 files |
| `m2_3_linux_keeper_r307` | as Keeper, under `linux_campaign_r307.sh` | **48 passed**, exit 0 |
| `m2_3_linux_focused_r307` | as focused, under `linux_campaign_r307.sh` | **626 passed**, 4 GUI deselected, exit 0 |

Ledger `selection_ledger_r307.json`:

- Against the failed M2-3 finals (broad, focused, Keeper, Reacquirer, Linux
  focused), there are **no added or removed nodes**. The **only outcome change**
  is `test_v6_alpha_m2_keeper::test_personal_copy_manifest_and_source_retention_and_overwrite_refusal`,
  failure → passed.
- Against M2-2A, the node accounting is the same as in §4: broad 3,394 → 3,462
  (+72/−4), focused 619 → 626 (+11/−4).
- **Skips:** 21, the same set as `m2_3_broad_final`. The two symlink skips
  appear as "new/dropped" pairs only because their messages contain the
  per-campaign scratch-path label. **The amendment introduces no new skip.**
  The single skip M2-3 introduced (`…[api2-roaming_reacquirer]`, no frozen
  executable) keeps its disposition: the existing approved reason, in the same
  family as the Scout and Keeper variants. No xfail, deselection or weakened
  assertion was used.

### Reuse of unaffected first-pass results

The amendment changed only one test module. All 16 other candidate paths are
byte-identical (`source_freeze_02.json`). Following the M2-2A precedent
(retain when the captured sources, runtime, verifier and fixed inputs are
identical, after a recorded source-delta review), these first-pass results are
reused, not rerun:

| Reused result | Why no relevant input changed |
| --- | --- |
| `m2_3_supplement_final` (328 passed) | The supplement node list does not contain the Keeper module; every source it exercises is byte-identical |
| `m2_3_windows_gui_final` (6) and `m2_3_linux_gui_x11` (5) | The GUI selections are Designer nodes in `tests/test_v6_alpha_m1_5_designer.py` (unchanged); no product source changed |
| `m2_3_linux_reacquirer` (56) | Module and sources unchanged. The Windows module was rerun anyway (56 passed) |
| Windows and Linux `reacquirer-R1` and `keeper-K1` demonstrations | The demo route, starter, fixture and verifier are byte-identical, and the test file is not an input to them. Re-verified read-only (§8) |

The Keeper module, focused and broad selections, Ruff and both mypy runs were
rerun, because they contain the changed file or were cheap enough to rerun. The
first-pass failed campaigns and all earlier failed attempts remain retained
unchanged (§4).

### Artifact identity

New evidence under `runs/v6_alpha_m2/m2_3_20261015/` (SHA-256, prefix):
`m2_3_keeper_r307.xml` `783b94b3a58d62dc`, `m2_3_reacquirer_r307.xml`
`bd86b441f1c2a161`, `m2_3_focused_r307.xml` `8b198d06deaa4cc8`,
`m2_3_broad_r307.xml` `cd0d877011735fa0`, `m2_3_linux_keeper_r307.xml`
`c0c58fde079c2ab4`, `m2_3_linux_focused_r307.xml` `d6669cc6e967b8a7`,
`source_freeze_02.json` `1ac13e17f752d51c`, `preservation_02.json`
`f49565d48aaa6d30`, `selection_ledger_r307.json` `15bd9fb15ddccd71`,
`scenario_comparison_r307.json` `0513fb8e084a064c`,
`cross_platform_comparison_r307.json` `692225f4ea3fe7d6`,
`relocation_check_r307.json` `e4eee99e949eac63`. New helper scripts:
`freeze_manifest_02.py` (adds the Keeper module to the allowed set),
`preservation_02.py` (moves it from frozen to an exact-diff check),
`ledger_r307.py`, `relocation_check_r307.py`, `linux_campaign_r307.sh`. The
originals are unchanged.

## 10. Limitations and conditions carried into M2-3 technical acceptance

- **L1 — Seat-B perspective.** Seat B's delivered perspective is verified at the
  code and cursor level (`SensingCursor(entrant_id="B")`). Interactive A/B
  replay selection in the product viewer remains M2-4 (M2-AC07).
- **L2 — External replay viewer.** The viewer controls (End, seek, resize,
  reopen) were not separately requalified for R1 artifacts in M2-3. The viewer
  code is unchanged.
- **L3 — Linux coverage.** WSL2/WSLg X11 only. No Wayland, Xvfb, bare Xorg,
  other distribution, full Python matrix, packaging or installer claim. The v6
  sensing starters are absent from the wheel `package-data` globs; this
  pre-dates M2-3 (Scout and Keeper) and lies outside this boundary.
- **L4 — M2-2 conditions C1–C3 remain open**, as recorded in
  [M2-2 Closure 01 §7](V6_ALPHA_M2_2_CLOSURE_01.md#7-conditions-carried-forward):
  C1 (intermittent Linux End-key non-response, M2-5), C2 (overlapping sample-marker
  labels, M2-4/M2-5) and C3 (qualification limitations). The M1 history/footer
  overlap also remains until M2-4.
- **L5 — Skips.** M2-3 introduced one skip,
  `test_frozen_executable_creates_every_supported_variant[api2-roaming_reacquirer]`,
  dispositioned under the existing approved reason (no frozen executable). The
  R3-07 amendment introduced none.
- No human comprehension or usability evaluation is claimed (M2-AC11 belongs to
  M2-6). This is not M2-wide, Alpha 1 or release acceptance.
- The M2-2 curated-evidence README sentence "The Keeper bodies use CRLF line
  endings" is inaccurate as published. Only the traces and some summary files
  are CRLF; `demo.json`, `replay.jsonl` and `result.json` are LF. All published
  hashes and bytes are correct. Correcting the sentence needs a separately
  authorized commit.

No E8/E9 harness, private input, entropy or authority operation, reseal or
scientific execution occurred, and no E8/E9 research artifact was modified.
Original E9 remains operationally blocked with execution LOCKED, and
Requirement C remains NOT ESTABLISHED.

## 11. Recommendation

**PASS WITH CONDITIONS** for M2-3 Roaming Reacquirer technical acceptance.

R3-01 through R3-08 pass on the amended candidate. R3-07 passes only through the
lead-authorized one-assertion amendment, and its exact diff is audited. I1–I3
are confirmed against Scope 03 with no conflict. The conditions are L1–L5 in §10.
R3-09 is this lead review. Nothing is staged, committed or pushed, and M2-4 has
not started.
