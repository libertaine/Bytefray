# Bytefray 5.0.0 Final Linux Package Qualification — Phase 4

Phase 4 qualifies the exact final wheel and sdist already built and
Windows-qualified in Phase 3, on Linux, without rebuilding either artifact or
changing source. This report documents that qualification and a genuine,
unresolved cross-platform determinism finding that blocks the final
publication gate.

## 1. Source and gate handoff

- Final source commit: `4be33840b2845518f83a8dc3e6c659605ae2150d` ("release:
  prepare Bytefray 5.0.0").
- This session's working HEAD: `61d5abb8af5cce70f6094ce35bbfdc9520c2425b`
  ("docs(v5): record final Windows qualification"), one commit ahead of
  `4be3384`. `git diff --stat 4be3384 61d5abb` shows that commit touches only
  `docs/research/v5/V5_FINAL_TRANSITION_AND_WINDOWS_QUALIFICATION.md` (505
  insertions, one new file) — source is byte-identical to `4be3384`.
- Canonical Phase 3 report:
  `docs/research/v5/V5_FINAL_TRANSITION_AND_WINDOWS_QUALIFICATION.md`.
  Recorded gate:

      WINDOWS FINAL 5.0.0 QUALIFICATION PASSED —
      EXACT FINAL WHEEL/SDIST READY FOR LINUX QUALIFICATION

**Branch-divergence note:** the `v5-research` branch checked out at the start
of this phase (local HEAD `ed862c1`) had diverged from `origin/v5-research`
after a shared ancestor (`59c55a7`) — the local branch had continued an RC1
Linux qualification track that never merged the Windows Phase 3 work,
while `origin/v5-research` carried `4be3384`/`61d5abb` and the Phase 3 report.
Neither the final source commit nor the Phase 3 report existed on the
originally-checked-out branch. This was resolved by checking out
`origin/v5-research` (`61d5abb`) directly (detached HEAD) without moving the
local `v5-research` branch ref, so the local-only RC1 Linux qualification
commit (`ed862c1`) remains intact and unaffected. This report does not
change the final source commit and performs no rebuild.

## 2. Exact artifact handoff verification

The two final artifacts were not present on this Linux machine at the start
of Phase 4 (`dist/` is gitignored, and build artifacts are never committed);
the user transferred them to `/home/rod/bytefray-v5-final-release/`.

| Type | Filename | Windows bytes (Phase 3) | Windows SHA-256 (Phase 3) | Linux bytes | Linux SHA-256 | Match |
|---|---|---|---|---|---|---|
| Wheel | `bytefray-5.0.0-py3-none-any.whl` | 1,067,857 | `50D632C7EC2C4A939601DFF54C15BF67565C785E084672073CB8C17C1E9F47A5` | 1,067,857 | `50D632C7EC2C4A939601DFF54C15BF67565C785E084672073CB8C17C1E9F47A5` | **Exact** |
| Sdist | `bytefray-5.0.0.tar.gz` | 975,861 | `8BEE3285179468F06A33DA81067AE66A4F8B1E59FD3C79362D69C369B7D22FBB` | 975,861 | `8BEE3285179468F06A33DA81067AE66A4F8B1E59FD3C79362D69C369B7D22FBB` | **Exact** |

Both byte size and SHA-256 match Phase 3 exactly. Neither artifact was
rebuilt at any point in this phase.

## 3. Linux environment

- Distribution: Ubuntu 26.04.1 LTS (Resolute Raccoon)
- Kernel: `Linux 7.0.0-31-generic`
- Architecture: `x86_64`
- Python interpreters used:
  - `/usr/bin/python3.14` (Python 3.14.4, system) — used for the primary
    wheel and sdist qualification venvs.
  - Python 3.13.7, provisioned fresh via `pyenv install 3.13.7` specifically
    to cross-check against Windows Phase 3's recorded `Python 3.13.14`
    (see §10) — no prebuilt 3.13.x existed on this machine beforehand.
- pip: 25.1.1 (system Python), used to create isolated venvs.
- Virtual-environment state: this machine's repo checkout has its own dev
  `.venv` (Python 3.11.9) with `bytefray==4.0.0rc2` installed in **editable**
  mode from the source checkout. This venv was never used for qualification.
  All qualification commands ran with a sanitized environment
  (`env -i PATH=/usr/bin:/bin HOME=/home/rod ...`, no `VIRTUAL_ENV`/
  `PYTHONPATH`) against interpreters created fresh outside the repo, invoked
  from a working directory outside the repo (`/home/rod/bytefray-v5-final-release/`).

## 4. Clean environments

Two fresh venvs were created outside the repo, from a clean system
interpreter (never from the repo's own `.venv`):

```
/usr/bin/python3 -m venv /home/rod/bytefray-v5-final-release/wheel-env
/usr/bin/python3 -m venv /home/rod/bytefray-v5-final-release/sdist-env
```

A third venv (`wheel-env-py313`) was built from the pyenv-provisioned Python
3.13.7 for the cross-Python-version check in §10.

Each install was verified not to resolve Bytefray from the source checkout:

```
$ python3 -c "import battle_engine; print(battle_engine.__file__)"
/home/rod/bytefray-v5-final-release/wheel-env/lib/python3.14/site-packages/battle_engine/__init__.py
```

(and the equivalent `sdist-env` path for the sdist install) — never
`/home/rod/Projects/BATTLE2/...`.

## 5. Wheel clean-install result

```
pip install /home/rod/bytefray-v5-final-release/bytefray-5.0.0-py3-none-any.whl
```

**PASS.** Installed `bytefray==5.0.0` and `PyYAML` only; no resolution from
any other source.

```
$ bytefray --version
Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4, Python 3.14.4
$ bytefray --help
(usage text as documented; PASS)
$ bytefray agents
```

Note: the task's suggested `bytefray agents --list` is not a real flag —
`agents --help` and Phase 3's own precedent both confirm the bare `bytefray
agents` subcommand is the starter-listing command. This is a wording
mismatch in the runbook, not a product defect.

**Starter discovery: exactly 21 entries**, matching the canonical list
(`adaptive`, `claimer`, `hunter`, `raider`, `runner`, `seeker`, `sentinel`,
`spiral`, `strider`, `v4_claimer`, `v4_concentrated_attacker`,
`v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`,
`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`,
`v5_scout_striker`, `wanderer`, `writer`) with no missing and no unexpected
name.

## 6. Wheel core workflow qualification

All run from the installed wheel only, isolated `BYTEFRAY_ROOT`:

| Workflow | Invocation | Result |
|---|---|---|
| Pairwise Ruleset-v4 match | `run --a-type v4_quorum --b-type v4_claimer --ruleset bytefray-rules-4` | PASS — result/replay/summary produced |
| Three-entrant match | `run --a-type v4_quorum --b-type v4_claimer --c-type v5_core_defender --ruleset bytefray-rules-4` | PASS |
| Tournament | `tournament v4_quorum v4_claimer v5_core_defender --ruleset bytefray-rules-4` | PASS — 3/3 completed, 0 failed, standings reported |
| Replay creation | via `--replay` on the above | PASS |
| Headless replay playback | `replay --replay pairwise.jsonl --renderer headless` | PASS — ticks streamed, `RESULT`/`END` emitted |
| Bundled-agent validation | `agents validate` on `v4_quorum`, `v4_claimer`, `v5_core_defender`, `v5_dual_team` | PASS — all `status: valid`, `api_version: 2` |
| Bundled-agent validation (VM agents) | `agents validate` on `seeker`, `writer` | Expected `status: invalid` / `agent_kind_unsupported` — by design, validate only supports Python agents; not a defect |
| Agent create/validate/test | `agents create qual_test_agent --api-version 2 --template annotated`, then `agents validate`, then `agents test --opponent v4_quorum` | PASS — result/replay/summary/trace produced |
| Evaluation workflow | `agents evaluate qual_test_agent --opponents v4_quorum --seeds 1,2,3 --ruleset bytefray-rules-4` | PASS — 6-match matrix, evaluation artifact produced |

No source-checkout imports occurred at any point.

## 7. SDist clean-install result

```
pip install /home/rod/bytefray-v5-final-release/bytefray-5.0.0.tar.gz
```

**PASS.** Built and installed from source distribution only (not from a
locally unpacked/installed source checkout). `battle_engine.__file__`
resolved to the sdist venv's `site-packages`, never the repo.

```
$ bytefray --version
Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4, Python 3.14.4
```

## 8. SDist workflow results

| Workflow | Result |
|---|---|
| Ruleset-v4 pairwise match | PASS |
| Replay (creation + headless playback) | PASS |
| Starter validation (`v5_dual_team`) | PASS — `status: valid`, `api_version: 2` |
| Starter discovery | PASS — exactly 21/21 |
| `v5_dual_team raider_share=0.7` | PASS (execution) — see §10 for the deterministic-hash comparison |
| Deterministic fixed-seed repeat | PASS internally — byte-identical across two sdist-side runs (see §10) |
| Three-entrant match | PASS |

SDist-installed behavior matches wheel-installed behavior in every respect
checked, including the §10 finding (both artifacts affected identically).

## 9. Starter inventory

Both wheel and sdist ship exactly 21 starter manifests, matching the
canonical list byte-for-byte (see §5). Wheel zip member count: 215 (216
lines from `python -m zipfile -l`, minus the header row), matching Phase 3's
recorded 215 exactly. Sdist tar member count: 283, matching Phase 3's
recorded 283 exactly.

## 10. Process-share regression and cross-platform deterministic comparison

**Execution/validation requirement (Section F, narrow scope): PASS.**
`v5_dual_team` was exercised against `v4_quorum` under `bytefray-rules-4`
with default parameters, `raider_share=0.7`, and `raider_share=0.33`. All
three executed successfully with no exact-Fraction runtime rejection, on
both the wheel and the sdist install — the RC1 process-share crash does not
reappear.

**Deterministic cross-platform hash comparison: FAIL.** The established
fixed-seed regression command (exact Phase 3/RC1 invocation):

```
bytefray run --a-type v5_dual_team --a-param raider_share=0.7 --b-type v4_quorum \
  --ruleset bytefray-rules-4 --arena 512 --quota 8 --ticks 30 --seed 602
```

| Source | Replay SHA-256 |
|---|---|
| Windows Phase 3 (recorded; also matches RC1 report and Phase 3's frozen-exe/wheel/sdist/installed-candidate checks — 4 independent Windows confirmations) | `DCF24B4EF03BB45446B4A11774713546DD657C0CCD3429E643CD9FAB9A0A3087` |
| Linux wheel, Python 3.14.4 | `6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A` |
| Linux wheel, Python 3.13.7 (provisioned to match Windows' minor version) | `6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A` (identical) |
| Linux sdist, Python 3.14.4 | `6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A` (identical) |

Per Section F/L/J's instruction, **the expected value was not updated**, and
this is recorded as a new finding rather than a pass.

### Investigation performed (read-only, no source or artifact changes)

Ruled out:
- **Flakiness** — repeated runs on Linux (same command, same seed) are
  byte-identical every time, across both artifacts and both Python versions
  tested.
- **Python minor-version drift** — Python 3.13.7 (freshly provisioned via
  `pyenv install 3.13.7` to approximate Windows' recorded `Python 3.13.14`)
  and 3.14.4 produce the identical Linux hash.
- **Wheel vs. sdist packaging difference** — both produce the identical
  Linux hash.
- **Line-ending corruption** — no `\r` bytes in any generated replay file.
- **A fabricated/typo'd Windows value** — `DCF24B4E...` first appears in the
  RC1 qualification report and is then independently reconfirmed three more
  times across Phase 3's frozen-executable, wheel, sdist, and
  installed-candidate checks, all self-consistent. The Linux value
  (`6DEED2D6...`) is equally self-consistent across every Linux path tried.
  Both sides look like genuine, real executions — the platforms simply
  disagree.

Source-level auditing of the most obviously relevant deterministic-hash
contributors found each one **explicitly designed and documented in-source
to be platform-independent**, and none appear to be the cause:
- `ProcessMatchController._runtime_quota_shares()`
  (`engine/src/battle_engine/process_runtime.py:312`) — the
  `raider_share` → exact-`Fraction` conversion this regression is named
  after. Uses `Fraction(str(float))`; IEEE-754 double arithmetic and
  Python's float-repr algorithm are both platform-independent by
  specification, so this is not believed to be the source of the
  divergence.
- `local_source_fingerprint()` (`engine/src/battle_engine/agent_api.py:326`)
  — raw-byte SHA-256 over POSIX-sorted relative paths; the code's own
  docstring calls out "stable across platforms and directory-listing
  order."
- `derive_agent_seed()` (`engine/src/battle_engine/python_runtime.py:862`)
  — SHA-256-based, explicitly built to avoid Python's randomized `hash()`.
- Seeded core placement (`engine/src/battle_engine/placement.py:128`) —
  deliberately uses a raw SHA-256 counter stream instead of `random.Random`,
  with an in-source comment naming this exact risk: "a Windows/Linux or
  3.10/3.13 disagreement here would silently change match outcomes and
  invalidate a replay."
- No transcendental math functions (`sin`/`cos`/`exp`/`log`, whose libm
  implementations can differ in their last bit between MSVCRT and glibc)
  appear anywhere in the gameplay/scoring path; the one usage found
  (`math.sqrt` in `evaluation_analysis.py`) is IEEE-754-guaranteed
  correctly-rounded and is unrelated to match/replay content besides being
  outside the exercised path.
- No unseeded randomness or hash-order-dependent iteration was found on the
  code path this specific test exercises (and empirically, if such a thing
  were in play, the four independent Linux process invocations above would
  not have produced identical output, since Python's string-hash
  randomization is re-seeded per process by default).

**Not audited:** the full per-tick instruction-execution and
process-scheduling core (`engine/src/battle_engine/process_runtime.py` /
`vm.py`, ~1,500 lines combined). Everything upstream of that core is sound
by the checks above; if a genuine platform-dependent bug exists, it most
likely lives there, but pinning it to an exact line would require a full
line-by-line audit (or a live Windows machine to bisect against) beyond this
phase's scope.

### Release impact

- **Affected artifacts:** both wheel and sdist, identically.
- **Same behavior on Windows:** no — Windows is internally consistent on its
  own value; only Linux disagrees with it.
- **Not a regression from Phase 3** — Phase 3 never ran this case on Linux,
  so there is no prior Linux baseline this contradicts; it is new
  information surfaced for the first time by this phase.
- Practically, this means a replay recorded on Windows and one recorded on
  Linux for the identical documented match are not byte-identical, even
  though gameplay execution succeeds cleanly on both. Whether this also
  produces a different *winner/score* (not just an incidental byte
  difference such as ordering) was not established in this phase.

## 11. GUI status

**PASS**, tested via Xvfb rather than the native Wayland session present on
this machine — `docs/LINUX_INSTALL.md` states CI validates pygame-ce/Designer
startup "under X11/Xvfb," and explicitly calls native Wayland "unvalidated,"
so Xvfb is the actually-supported comparison path here. GUI extras
(`bytefray[designer,replay]`) were installed into the wheel qualification
venv via the normal supported pip-extras path (`designer` = PySide6,
`replay` = pygame-ce), per `docs/LINUX_INSTALL.md`.

| Check | Result |
|---|---|
| Agent Designer startup (`bytefray-agent-designer`, `BYTEFRAY_GUI_SMOKE_EXIT_MS=4000`) | PASS — started and auto-exited cleanly, exit code 0, no traceback |
| Replay Viewer startup (`bytefray replay --renderer pygame`, held 6s then `SIGTERM`) | PASS — no traceback/error output during the held window |

## 12. Warnings / caveats

- The originally-checked-out local branch had diverged from
  `origin/v5-research` and lacked both the final source commit and the
  Phase 3 report; resolved by checking out `origin/v5-research` directly
  without disturbing the local branch ref (see §1).
- The two final artifacts were not present on this machine at the start of
  this phase and had to be manually transferred by the user; this phase did
  not have — and does not claim — an automated transfer step.
- No prebuilt Python 3.13.x existed on this machine; 3.13.7 was provisioned
  via `pyenv install 3.13.7` solely to rule out a Python-minor-version
  explanation for §10's finding.
- This machine's repository checkout has a contaminated dev `.venv`
  (`bytefray==4.0.0rc2` installed editable from source); every qualification
  command explicitly avoided it (sanitized environment, interpreters and
  working directories entirely outside the repo).
- The task's suggested `bytefray agents --list` invocation is not a real
  CLI flag; `bytefray agents` (no flag) is correct, matching Phase 3's own
  usage.
- The §10 finding was root-caused only partially (see above) — the
  mechanism is not yet pinned to an exact source line.

## 13. New defects

One new finding, described fully in §10: **a reproducible Windows-vs-Linux
replay-hash divergence** for the established `v5_dual_team raider_share=0.7`
fixed-seed regression case, affecting both the wheel and the sdist
identically. Not seen on Windows in isolation (Windows is self-consistent);
not a flake; not explained by Python minor version, packaging format, or
line-endings. Root cause narrowed away from the process-share/Fraction
logic, source fingerprinting, and seed derivation, but not yet pinned to an
exact line in the unaudited per-tick execution core.

## 14. Final publication gate

    FINAL 5.0.0 PUBLICATION QUALIFICATION FAILED —
    CROSS-PLATFORM DETERMINISM MISMATCH IN v5_dual_team raider_share=0.7
    FIXED-SEED REGRESSION (WINDOWS DCF24B4E... vs LINUX 6DEED2D6...,
    BOTH ARTIFACTS, ROOT CAUSE NOT YET IDENTIFIED)

Per Section L, no source was modified and no artifact was rebuilt as a
result of this finding. This gate does not proceed to tagging or
publication.

## 15. Addendum (2026-09-15) — root cause identified: replay newline serialization

Subsequent byte-level comparison of the raw Windows (`DCF24B4E...`) and Linux
(`6DEED2D6...`) replay files established that the §10 mismatch is caused
**solely** by platform-native line-ending translation in the replay JSONL
writer, not by any gameplay, scheduler, or process-share nondeterminism:

- Windows replay: 23,184 bytes, 13 CRLF (`\r\n`) sequences.
- Linux replay: 23,171 bytes, 0 CRLF sequences.
- Byte-size difference (13) exactly matches the CRLF count.
- Windows bytes with every `\r\n` replaced by `\n`: 23,171 bytes, SHA-256
  `6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A` —
  **byte-identical** to the raw Linux replay.
- Both files parse to 13/13 records via the production `iter_replay`
  deserializer with **zero semantic differences**.

This confirms the §13 "new defect" was real and correctly blocked
publication — the gate's conservatism was justified — but its root cause is
now known and narrow: `write_replay()`
(`engine/src/battle_engine/replay.py`) opened its output in text mode
without pinning `newline`, so Python's universal-newline translation
silently emitted `\r\n` on Windows. It was **not** a genuine cross-platform
gameplay/simulation determinism failure; every source-level hypothesis this
report's §10 investigation ruled out (process-share/`Fraction` conversion,
source fingerprinting, seed derivation, core placement) remains correctly
ruled out.

Full root-cause proof, the fix, and re-qualification results are recorded in
`docs/research/v5/V5_FINAL_REPLAY_NEWLINE_REMEDIATION.md` (Phase 4A). The
publication gate in §14 above **remains NOT PASSED**: it is superseded only
once artifacts are rebuilt from the Phase 4A remediation commit and
requalified on both platforms, not by this addendum alone.
