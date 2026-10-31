# Classic retirement PR #6: CI remediation

Date: 2026-10-30. **Product CI migration defects corrected. Integration
HOLD: frozen scientific-integrity verification on the development line needs
a project-lead decision (Section D).**

Approved starting point: `feature/retire-classic-ruleset` at
`15f7139b7bde79a53248455c92a110b6ee61fad2`; target
`development/post-5.1-alpha` at `f127be70e7ed88449c1b737f4675e1453ec8de45`
(also the `v5.1.0-alpha.1` tag). This report supplements, without replacing,
[the independent approval](CLASSIC_RULESET_RETIREMENT_FINAL_APPROVAL.md).

## Baseline comparison

The target's own CI already failed: [run 40400795204](https://github.com/libertaine/Bytefray/actions/runs/40400795204)
on `f127be7` (also run 40209820059 on the `v5.1.0-alpha.1` tag) fails every
`test-linux-core` job and `build-windows-exe`. No `CI` run on the V6 lineage
has passed `test-linux-core`. Failed test identities, collapsed across the
Linux matrix, compare as follows with the PR's
[run 40615092333](https://github.com/libertaine/Bytefray/actions/runs/40615092333):

| Set | Tests | Disposition |
| --- | --- | --- |
| Failing on both | 131 | Baseline-existing; frozen-science verification (D) |
| Fixed by the PR | 17 | E2-E8 research identities absent from product ruleset choices |
| New in the PR | 26 | 25 fixture migration defects (E); 1 tool upgrade (F) |

## Failure causes and corrections

### A. Linux pygame smoke fixtures (PR-introduced; corrected)

Both Python 3.10 and 3.14 jobs in
[GUI run 40615092421](https://github.com/libertaine/Bytefray/actions/runs/40615092421)
failed before opening a replay: `v4_scout` and `v5_region_attacker` are no
longer installed starters.

`client/tests/test_linux_pygame_smoke.py` now uses Window Scout versus
Watchful Keeper, explicit Active Sensing, seed 1, arena 512 and the existing
seeded placement resolver. Each test uses its own temporary data root.
The keyboard test asserts that recorded ticks include 0, 1 and 2, then retains
the exact observed `0 -> 1 -> 2 -> 1` assertion. The rendering test sends QUIT
only after an actual display flip and asserts one rendered frame; previously,
QUIT during window setup could bypass rendering entirely. Neither renderer
nor gameplay code changed.

### B. Windows workflow references a deleted test (baseline-existing; corrected)

The Windows protection step fails identically on the baseline and the PR:
`engine/tests/test_supervised_runtime.py` does not exist. Git history
identifies `3caf143e332ce9ad627442409a7239a4e7025581` (V6 Phase 2B.12) as its
deletion, before Classic retirement; the job has therefore not reached the
EXE build on this line. That module tested the retired API-v1
`SupervisedPythonEntrantController`. API-v2 matches supervise calls through
`ProcessMatchController` and `AgentWorkerHandle`.

The workflow retains the complete containment and worker modules and selects
these existing equivalents:

| Module | Protection exercised |
| --- | --- |
| `test_process_containment.py` | Windows Job Object binding and parent-lifetime containment |
| `test_agent_worker.py` | Actual worker lifecycle, reset/action hangs, abrupt exit, recovery and parent death |
| `test_agent_validation.py` | Supervised reset/action diagnostics, successful-call parity and trace handling |
| `test_agent_test.py` | Production development-test supervision, canonical artifacts and hung-agent forfeit |
| `test_process_runtime_integration.py` | API-v2 native match integration, supervised execution and replay determinism |
| `test_v6_alpha_m1_policy_capabilities.py` | Active Sensing direct/worker parity and capability rejection before execution |

No protection was replaced by a nonexistent path, broad exclusion or test skip.

### C. Designer native abort: Qt binding defect (baseline-existing; constrained)

The original job completed 108 cases, then aborted with exit 134 in
`test_process_failed_to_start_shows_tool_failure_and_recovers`. Bounded Xvfb
diagnosis (Ubuntu WSL2, 2026-10-27) established:

- Python 3.10.22, PySide6/Shiboken 6.12.0: the full approved Designer suite
  reproduces exit 134 at the same test.
- The single test, with uncaptured stderr, reports
  `Fatal Python error: none_dealloc: deallocating None` at
  `QApplication.processEvents()`. It also aborts alone on the pre-retirement
  `f127be7` snapshot.
- A minimal process importing only Qt and calling `processEvents()` loses
  one `None` reference per call after warm-up (batches of 10/100/1,000 calls
  change the reference count by -10/-100/-1,000), without any Designer,
  agent, replay, fixture or pytest code.
- On PySide6/Shiboken 6.11.2 the minimal probe has no reference loss through
  10,000 calls, and the original Designer test passes unchanged.

This is a native binding defect, independent of test order and of Classic
retirement. The Designer CI installation is constrained to `PySide6==6.11.2`;
the full `tests/` selection remains enabled, with faulthandler, verbose
progress and tee capture. No runtime dependency declaration, Designer code or
release input changed. Removing the CI constraint requires a passing minimal
probe and full suite on the replacement binding. Python 3.10 with PySide6
6.12.0 remains an open compatibility problem outside this CI constraint.

Once the abort was bypassed, an existing Replay History keyboard test failed
because Xvfb has no window manager to activate the window, so `focusWidget()`
returned `None`; it fails alone on approved and pre-retirement source. The
test now waits for exposure, requests activation and waits for activation
before inspecting focus. Every traversal, Copy Seed, Return, filter-focus and
replay-launch assertion is preserved; product focus behavior is unchanged.

### D. Frozen scientific-integrity verification (baseline-existing; HOLD)

The E9 failures are live-tree checks of a whole-repository frozen boundary,
and that boundary was already broken on the target before this PR:

- `tools/research/v6/e9/protocol.py::load_protocol(verify=True)` checks, in
  order, frozen snapshots, four LF-pinned *governing contracts*
  (`ARCHITECTURE.md`, `docs/AGENT_API_V2.md`, `docs/REPLAY_SCHEMA.md`,
  `docs/RESULT_SCHEMA.md`), qualified E9 sources, frozen E8 sources, packages,
  the sealed E8 result and finally an LF manifest of every `engine/src` file.
  The E9 v2 records wrap any such failure as
  `inherited immutable source/package boundary failed`.
- On `f127be7` the governing contracts still match and the check fails last,
  with `the frozen engine manifest changed` (per Linux job: 15 direct
  failures, 44 wrapped).
- Commit `15f7139` edited all four governing contracts to describe the
  retirement; raw and LF SHA-256 differ (for example `ARCHITECTURE.md`
  `af92256a96b2...` to `ea179aaca222...`). The same tests now fail earlier,
  with `a governing contract changed`. The failure count is unchanged
  because the later engine-manifest check already failed, and the retirement
  necessarily changes `engine/src` further.
- The E9 v2 inherited preservation manifest pins 1,203 tracked files: 109
  already differ at `f127be7`; at the PR head 205 differ and 8 are deleted.
- Other shared failures are also baseline-existing: shallow-checkout
  `git show`/`rev-parse` of historical commits (E6/E8/E9 provenance, about 45
  cases), and E4/E8 freeze source checks with prior documented dispositions.

Nothing here alters a frozen protocol, record, digest or historical evidence;
the frozen records and E9's fail-closed behavior are intact. However, the
development tree no longer satisfies E9's frozen source boundary, and this PR
adds four governing-contract changes. Preserving files does not show that the
boundary holds. Making `test-linux-core` pass would require one of these
decisions, none of which this remediation takes:

1. **Separate frozen-science verification from product CI.** Product CI would
   stop running live-tree frozen-boundary checks that cannot hold after the
   freeze. A separate job would run them at their frozen commits with full
   history, or assert that E9 refuses to load from the development tree.
   This changes what development CI proves and needs explicit approval.
2. **Restore the four governing contracts to their frozen bytes** and record
   the retirement elsewhere. This removes the PR-introduced governing drift
   but does not make CI pass; the engine-manifest failure remains.
3. **Merge with documented red `test-linux-core`**, accepting the baseline
   comparison above. This contradicts the merge requirement that required
   product CI passes.

E9 remains LOCKED; Requirement C remains NOT ESTABLISHED. No E9 test was
modified, skipped or executed as research; no expected hash was changed.

### E. Retained v4 packages resolved from the runtime catalog (PR-introduced; corrected)

On a clean checkout, `discover_agents(REPO_ROOT)` seeds the git-ignored
`agents/` catalog from the installed starter list. Before retirement that
included `v4_quorum`, `v4_defender_scout` and `v4_scout`; now it seeds only
the three Active Sensing starters. Twenty-five cases that resolve those
retained packages through `agents/` therefore fail in CI:
`test_v5_research_r4_agents.py` (21, including the catalog assertion),
`test_v5_research_r4_population.py` (3) and
`test_process_runtime_integration.py::test_v4_production_schema4_roundtrip_determinism_and_supervision`
(1). Local review missed
them because a stale ignored `agents/` copy in the review worktree still held
the retired starters.

The retirement keeps these packages byte for byte under
`engine/src/battle_engine/data/starter_agents/` for exactly this research use,
and already migrated these tests to run under
`bytefray-rules-6-research-scale`. The corrections are test-only:

- R4 agent tests resolve `v4_quorum` from the retained package directory, and
  the catalog assertion now asserts retention without installation.
- R4 population tests point the R4 tool's canonical directory at the retained
  packages through a fixture. `tools/research/v5/r4_population.py` is
  unchanged: reproducing R4 requires `5.1.0-alpha.1`, as the retirement
  overview records.
- The schema-4 roundtrip copies the two retained packages into an isolated
  temporary data root.

The frozen Phase 0 `v4_quorum` fingerprint `d220a583...` is still asserted
and passes; no expected value, fingerprint or research record changed.

### F. `pytest` 9.2.0 and a Seal 07 test (environmental; not corrected)

`test_v6_e9_v2_gate8_seal07.py::test_s7_regular_missing_unreadable_and_opened_identity`
replaces `os.fstat` with a stub lacking `st_size`. Under unpinned `pytest`
9.2.0 (the PR run; the baseline ran 9.1.1) this raises `AttributeError`.
Locally it passes on both `f127be7` and the PR source under 9.1.1 and fails
on both under 9.2.0. It is a protected E9 test and was not edited. A CI
`pytest<9.2` constraint would address it but does not change Section D.

## Verification ledger

This is remediation self-verification, not independent approval or release
qualification. Overlapping collections are not additive.

Local runs (2026-10-30) used a disposable `--depth 1` clone of the PR branch
with the remediation applied, a dedicated Python 3.13.14 venv installed
editable from that clone (pytest 9.2.0), and external temp/cache paths.

| Check | Result |
| --- | --- |
| Corrected R4 agent/population and process-runtime modules | 54 passed, 2 pre-existing skips (Phase 0 corpus absent) |
| Windows protection selection from `ci.yml` | 224 passed |
| Windows NTFS-junction step from `ci.yml` | 59 passed, 7 skips (no local symlink privilege) |
| Approved bounded collection (K1, promotion, Phase-C, schema-7, E3 passive) | 396 passed, 1 location artefact (below), 397/397 after rerun |
| Packaging, starters, wheel, v4 historical immutability, evaluation v2/v4, `client/tests` | 888 passed, 9 skips (offline wheel build; symlink privilege) |
| Helper `run_negative_cases` direct call and module entry point | Passed |
| Ruff; engine / client / helper mypy | Passed |
| Wheel and sdist build; `tools/check_wheel.py` | Passed; exactly the three Active Sensing starters in each |
| Seal 07 test, pytest 9.1.1 / 9.2.0, baseline and PR | Pass / fail on both |

The bounded artefact: a clone under `%TEMP%` makes the test's
`Path.cwd().parent / "unauthorized_external_destination"` fall inside the
system temp directory, which the validator authorizes; rerun from the D:
worktree, with identical `engine/src`, it passes. Earlier WSL2/Xvfb evidence
for A and C (2 + 2 pygame passes on Python 3.10.22/3.14.8; complete Designer
suite 575 passed on 3.10.22/Qt 6.11.2) is retained at
`/home/rasat/.cache/bytefray-pr6-ci-5aaihqgp`; Windows evidence from that
session at `C:\Users\rasat\AppData\Local\Temp\bytefray-pr6-ci-bg225t47`.
This session's logs, JUnit, clones and wheels are at
`C:\Users\rasat\AppData\Local\Temp\bytefray-pr6-integrate-20261030`.

GitHub requalification on the exact pushed commit is authoritative for the
pygame, Designer, Windows and Linux matrix results.

## Scope

Active Sensing policy and gameplay, the Agent API, the
`ruleset_unavailable / configuration` diagnostic, Replay Viewer and Spectator
compatibility, the three-starter catalog and Classic retirement are
unchanged. No engine or application source, research tool, frozen research
evidence, competitive-agent prototype, historical approval report, installer
or release configuration was modified. Native Linux desktop, Windows
installer, the retained Windows `0x8001010d` diagnostic and the next
application version remain separate release gates.

**E9 remains LOCKED. Requirement C remains NOT ESTABLISHED.**
