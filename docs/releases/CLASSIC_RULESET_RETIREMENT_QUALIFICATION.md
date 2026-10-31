# Classic retirement qualification — 2026-10-26

**Assessment: PASS WITH CONDITIONS for development review. Release qualification remains HOLD.**
The published recovery point and release inputs are unchanged. This is not a release approval.

1. **Repository.** Worktree: `D:\Projects\BATTLE2\work\bytefray-post-alpha`.
   Branch: `feature/retire-classic-ruleset`, no upstream.
   HEAD and peeled `v5.1.0-alpha.1`: `f127be70e7ed88449c1b737f4675e1453ec8de45`.
   The inherited index contains staged deletions/renames and intent-to-add entries.
   No staging, commit, reset, stash, cleanup, push, merge, tag, or publication was performed.

2. **Continuation boundary.** Claude implemented the registry/default/CLI migration,
   Designer selector removal, starter packaging, compatibility records, and most
   test/documentation migrations. Codex preserved that implementation and its initial
   working/index patches; corrected empty compatibility-label visibility, H1 test
   portability, schema-form parameter forwarding tests, and tournament tie/rank/order
   expectations; restored the exact 90-row E3 golden table; disposed frozen Classic
   execution tests explicitly; and corrected the Linux packaging workflow.

3. **Runtime.** Active Sensing (`bytefray-rules-6-alpha1`) is the sole product
   Ruleset and omitted-selection default. All five CLI surfaces reject explicit
   Classic requests with a retirement diagnostic. The registry has 15 executable
   identities: one product and 14 explicit research identities (12 active, two
   retired research identities retained for reproduction). None is Classic.
   All 15 retained policy definitions compare equal to HEAD as Python ASTs.
   The Active Sensing identity and policy semantics are unchanged.

4. **Separate test ledgers.**

   | Run | Result | Scope / limit |
   | --- | --- | --- |
   | Inherited baseline | 9,062 passed; 114 failed; 3 errors; 36 skipped; 13 deselected | Complete 12-shard run in a separate checkout; missing agent inputs and frozen-source mismatches make this an imperfect baseline |
   | Inherited run3 | 8,290 passed; 81 failed; 3 errors; 36 skipped; 13 deselected | Only 11 of 12 shard summaries; remaining shard stopped and logs preserved |
   | Inherited GUI baseline | 585 passed; 6 deselected | 36 module summaries; native Windows exception diagnostic present |
   | Inherited gui2 | 557 passed; 7 failed; 6 deselected | Only 35 of 36 module summaries; lifecycle job stopped and logs preserved |
   | Codex headless | 7,393 passed; 8 failed; 76 skipped; 13 deselected | All default test roots except locked E9 modules; unique absolute external basetemp and isolated wheel metadata |
   | Codex GUI | 576 passed; 0 failed; 0 errors; 6 deselected | All 36 modules in separate sequential processes |
   | H1 focused | 17 passed | Defaults, overrides, seeded tournament replacement, expected match IDs, direct/worker delivery |
   | Validation focused | 44 passed | Shorter unique external temp paths avoid the inherited long-path diagnostic truncation |

   Do not add overlapping run totals. All 84 distinct inherited run3 failure/error
   IDs also occur in the inherited baseline, but their diagnostics are not always
   the same. Full-ID inventories and retained tracebacks are in the evidence root.
   The 84 comprise seven H1 migration failures, seven frozen R3 Classic execution
   failures, one long-path diagnostic assertion, one stale-metadata packaging
   assertion, five E8 freeze failures, and 63 locked E9 failures/errors.

   The broad run took 1,845.36 seconds and exited 1. All eight remaining failures also fail in the baseline: four analysis-freeze tests, one family-freeze test, and three runner-precondition tests. The runner failures stop at the same family freeze before their mocked later checks. No new product failure was found. The final focused run after the bounded roster/test amendments reports 96 passed and two explicit Classic skips (30 packaging tests; 66 sensing-policy tests). These replace overlapping coverage in the broad run; do not combine their totals. Runtime code did not change after the broad run. Full tracebacks are in headless-failures.json.

5. **GUI limit.** All 36 processes exited zero. The native Windows module reports
   eight passes but logs Windows exception `0x8001010d` at its event-processing
   call, as did the baseline. This is an unresolved native diagnostic, not a
   demonstrated new retirement regression or an unrestricted native stability PASS.
   Automated functional coverage includes selection, parameter editing, validation,
   agent tests, evaluation, tournament launching, match/replay launching, results,
   and Replay History. No subjective human-experience claim is made.

6. **Static checks.** `ruff check .` passes.
   `mypy engine/src/battle_engine`: 107 source files, no issues.
   `mypy client/src/battle_client`: 20 source files, no issues.
   `git diff --check` passes. Final Ruff and whitespace checks also pass.

7. **Packaging.** Built a source distribution, then a wheel from that distribution,
   in a separate snapshot. `tools/check_wheel.py` passes. Both contain exactly
   `v6_window_scout`, `v6_watchful_keeper`, and `v6_roaming_reacquirer`;
   the checker also validates all five current templates. The three frozen starter
   consumers are checked against the exact roster. The shared venv still advertises
   `5.0.0`; the isolated wheel correctly advertises `5.1.0a1`, and its real match
   records that version. No application/release version or shared installation was
   changed to silence the assertion.

   Local review artifacts, not release assets:

   | Artifact | Bytes | SHA-256 |
   | --- | ---: | --- |
   | `bytefray-5.1.0a1-py3-none-any.whl` | 1,048,446 | `67c245e7c1a8372fac0f9459ab8a9fb7cc896393bb4bbd4eabb103d6c3675f4f` |
   | `bytefray-5.1.0a1.tar.gz` | 1,007,188 | `e78571313635db6896ca69873e5e7529bd7016ae264bed653cebfe0dd153d4ea` |

   Windows spec/installer-assumption tests: 30 passed.
   No Windows executable/installer was rebuilt. Installer version/release-document
   selection remains at the published Alpha inputs pending the project-lead version
   decision. Linux workflow YAML and all shell blocks parse; its embedded result
   and replay assertions pass against the wheel smoke artifacts and reject wrong
   Ruleset/replay data. No native Linux binary or GUI run was performed.

8. **Built-wheel match/replay/Spectator.** A fresh seed-42, 512-cell, 300-tick match
   produced canonical result, replay, trace, and summary artifacts under Active
   Sensing. Result/replay verification and real headless playback passed.
   Spectator support detection, export, and verification passed with all three
   source hashes, the current exporter, both information allowlists, outcome
   agreement, and 301 tick boundaries checked. Match ID:
   `match_911ad96ccc6e9c0efc086325`; result ID:
   `result_24825fbb7d1bf3bf05143cc5`.

9. **Historical dispositions.** Claude removed the Classic starter,
   stable-equivalence, exploit, K1 capture, and quorum execution suites. Shared
   runtime/renderer/service coverage was migrated to Active Sensing. Existing
   E2 Classic-control skips remain explicit. Codex retains R3 containment tests
   and skips its seven exact Classic match cases, rather than assigning them a
   new scientific identity. All 90 original E3 golden rows and their values remain
   intact; only the 30 Classic live reproductions skip. The two E8 Classic SENSE admission cases retain their original Ruleset identity and skip live execution; no research identity is substituted for that frozen control.
   Historical replay fixtures remain in place and readable. E8/E9 frozen records,
   research packages, fixture directories, archive/research documentation, and
   retained V4/V5 agent sources are unchanged. Their live source manifests are
   not re-blessed. E8 already had qualification-source mismatches in HEAD; the
   inherited retirement migration changes one additional live qualification file.
   **E9 remains LOCKED. Requirement C remains NOT ESTABLISHED.** No E9 test or
   research execution was started by Codex.

10. **Inventory and preservation.** 175 files changed, 2937 insertions(+), 5971 deletions(-). Including the two untracked retirement/qualification documents: 177 changed files, 3,217 additions and 5,971 deletions, net 2,754 fewer lines. Python/spec/shell files: net 3,416 fewer lines. The working tree remains intentionally uncommitted with the inherited staged/unstaged state preserved.
    The complete inventory, initial inherited patches, exact commands/exit codes,
    JUnit files, original/fresh logs, source hashes, policy comparison, packaging
    hashes, and smoke artifacts are retained at:

    `C:\Users\rasat\AppData\Local\Temp\bytefray-classic-continuation-2e191bb260eb4836be417690d50bc2a7`

    See `final-changed-files.tsv`, `triage.json`, and `evidence-manifest.json`.
    The inherited staged patch is unchanged. No Argon files entered the diff.
    No existing temp/evidence directory was cleaned.

11. **Conditions.** Frozen scientific reproduction remains unavailable against
    this changed source tree; retained freeze checks fail closed rather than
    accepting new expected values. The Windows exception diagnostic remains open.
    Native Linux and new frozen binaries/installers remain unqualified. Skips also include absent git-ignored E3/E6 corpora and two native file-symlink checks lacking Windows privilege; these are evidence/platform limits, not product failures.
    The shared venv metadata remains stale; isolated installed metadata was used.
    The proposed development record's `6.0.0-alpha.1` is still a placeholder.
    These conditions prevent release approval; they do not silently promote the
    research identities, waive E9, or alter the published Alpha baseline.
