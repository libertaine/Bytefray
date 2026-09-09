# Bytefray V5 Alpha 1 — Phase F Final Qualification

## Verdict

    ALPHA 1 QUALIFICATION INCOMPLETE — ENVIRONMENT/TOOLING BLOCKED

Qualification stopped at the mandatory starting-precondition gate. No source,
test, build, packaging, installer, CI, or Linux qualification evidence from an
earlier candidate has been reused. No product defect was established in this
run.

## A. Candidate identity

- Branch observed: `v5-research`
- HEAD observed: `bfc8097ec61eb098efdc787fa0a2a8d642974d16`
- `origin/v5-research` observed: `bfc8097ec61eb098efdc787fa0a2a8d642974d16`
- HEAD equals `origin/v5-research`: YES
- Candidate source SHA frozen: NO — section 4 did not pass, so section 5 was
  not entered.
- Expected product version: `5.0.0a1`
- Canonical version audit: NOT RUN due mandatory stop.
- Environment: Windows PowerShell workspace at `D:\Projects\BATTLE2`.

### Starting Git and index health

The required command was run exactly as:

```powershell
git --no-optional-locks status --short --untracked-files=all
git --no-optional-locks diff --check
```

Both commands emitted:

```text
warning: unable to access 'C:\Users\rasat/.config/git/ignore': Permission denied
```

- Working tree clean: NOT CERTIFIED
- Complete untracked-file inspection: NO
- `diff --check`: no whitespace-error lines were emitted, but the command also
  reported the permission warning and therefore did not satisfy the gate.
- `.git/index.lock` exists: NO (`Test-Path` returned `False`)
- `.git/index` size: `95,387` bytes
- `.git/index` last-write time: `2026-09-09 16:03:58` local time
- Git/index precondition result: FAIL — ENVIRONMENT/TOOLING

The prompt requires an immediate stop if Git reports permission errors or
untracked inspection is incomplete. No attempt was made to change Git
configuration, ignore behavior, permissions, or repository state.

## B. Remediation provenance

The three remediation commits are ancestors of the observed HEAD:

| Round | Commit | Subject | Present |
|---|---|---|---|
| F1 | `45ccc3462cf95686846bd6c4a2f5af31869c0cdb` | `fix(packaging): include API v2 scaffold resources` | YES |
| F2 | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` | `fix(packaging): exclude bytecode from frozen artifacts` | YES |
| F3 | `bfc8097ec61eb098efdc787fa0a2a8d642974d16` | `fix(ci): harden cross-platform alpha qualification` | YES |

Their prior reports and artifacts remain historical remediation evidence only.
They were not reused as qualification evidence. Artifacts from the original
blocked Phase F, F1, and F2 remain invalid for publication.

## C. Source qualification

- Separator/path regression: NOT RUN
- No-Git-history fixture regression: NOT RUN
- Python 3.11 compatibility: NOT RUN
- Current-development-Python compatibility: NOT RUN
- Focused source qualification: NOT RUN
- Full pytest: NOT RUN
- GUI/app tests: NOT RUN
- Ruff: NOT RUN
- mypy engine: NOT RUN
- mypy client: NOT RUN

All were skipped because section 4 required qualification to stop before the
candidate could be frozen.

## D. Stable gameplay

- Stable V4 equivalence: NOT RUN
- R1/R2 production hygiene: NOT RUN
- V4 agent compatibility: NOT RUN
- V5 starter qualification: NOT RUN
- Parameter/preset qualification: NOT RUN
- Starter-refresh qualification: NOT RUN

## E. CI

- CI contract audit: NOT RUN
- Exact-candidate CI status: NOT QUERIED
- Required CI green: NOT ESTABLISHED

No unknown CI job is represented as passing.

## F. Windows build orchestration

- `build_win.ps1`: NOT RUN
- Exit status: NOT APPLICABLE
- Generated artifact list: NONE

## G. Frozen artifacts

- Frozen artifact count: 0 current-candidate artifacts built or qualified
- Payload bytecode hygiene: NOT RUN
- Expected resource inspection: NOT RUN
- Frozen artifact hashes: NONE

## H. F1 regression

- API-v1 frozen scaffold: NOT RUN
- API-v2 scaffold A creation/validation: NOT RUN
- API-v2 scaffold B creation/validation: NOT RUN
- Source-tree fallback excluded: NOT ESTABLISHED

## I. F2/F3 regression

- Post-build bytecode guard: NOT RUN
- Contaminated-payload negative control: NOT RUN
- Slash/backslash classification: NOT RUN

## J. Wheel

- Wheel filename, size, and SHA-256: NONE
- Wheel content audit: NOT RUN
- Clean-install qualification: NOT RUN

## K. Sdist

- Sdist filename, size, and SHA-256: NONE
- Separate sdist-install qualification: NOT RUN

## L. Installer

- Installer filename, size, and SHA-256: NONE
- Installer build: NOT RUN
- Fresh-install workflow: NOT RUN
- Pristine-upgrade workflow: NOT RUN
- Customized-upgrade workflow: NOT RUN
- Starter-refresh idempotence: NOT RUN

## M. Designer

- Schema and preset UX: NOT RUN
- Explicit override validation: NOT RUN
- Randomize Seed: NOT RUN
- Ruleset synchronization: NOT RUN
- API-v1 and A/B/C entrant paths: NOT RUN

## N. First-user workflow

- Packaged first-user workflow: NOT RUN

## O. Author workflow

- Documentation-driven API-v2 workflow: NOT RUN

## P. Legacy compatibility

- API-v1 workflow: NOT RUN
- V4 compatibility: NOT RUN
- Replay/result compatibility: NOT RUN

## Q. Headless

- Minimal dependency boundary: NOT RUN
- Security/sandbox sanity: NOT RUN

## R. Linux qualification

- Linux environment: NOT ENTERED
- Wheel hash match: NOT RUN
- Wheel qualification: NOT RUN
- Sdist hash match: NOT RUN
- Sdist qualification: NOT RUN
- Linux headless result: NOT RUN

Linux packaged qualification is required. PUBLICATION NOT PERFORMED.

## S. Artifact inventory

No current-candidate publication artifacts were built or qualified, so there
are no artifact hashes to report.

## T. Known limitations

- The managed environment denied access to
  `C:\Users\rasat\.config\git\ignore` during both required Git health
  commands. Consequently, the clean/untracked state could not be certified.
- The initial `Get-CimInstance Win32_Process` process-health inventory returned
  `Access denied`. The non-CIM `Get-Process` fallback worked. An intermediate
  observation saw only the short-lived Git processes belonging to concurrent
  read-only Git checks, and a final sequential observation returned
  `NO_MATCHING_PROCESSES`.

## U. Publication blockers

1. Starting Git inspection did not satisfy section 4 because Git reported a
   permission error and complete untracked inspection could not be certified.
2. Because of the mandatory stop, all source, CI, Windows, wheel, sdist,
   installer, and Linux gates remain unqualified.

These are environment/tooling blockers. No candidate/product remediation need
was established.

## V. Final verdict

    ALPHA 1 QUALIFICATION INCOMPLETE — ENVIRONMENT/TOOLING BLOCKED

## W. Exact next action

Rerun Phase F from section 4 in an environment that can read the user-level Git
ignore file, using the same observed HEAD only if branch, remote equality, and
a complete clean-tree check still pass.

## End-of-run safety record

- Product source changed: NO
- Files created by qualification: this report only
- Release-note draft changed: NO
- Git mutation command run: NO
- Publication action run: NO
- Background/detached process launched: NO
- All task-created processes terminated: YES
- Candidate remediation required: NO — no product defect established
- Final status: only
  `?? docs/research/v5/V5_ALPHA1_PHASE_F_FINAL_QUALIFICATION.md` was listed,
  along with the same user-level Git-ignore permission warning.
- Final `diff --stat`: no tracked changes reported.
- Final `diff --check`: no whitespace errors reported, but not certified due
  the repeated Git-ignore permission warning.
- Final `.git/index` size: `95,387` bytes; last-write time unchanged at
  `2026-09-09 16:03:58` local time.
- Final `.git/index.lock` exists: NO.
- Final matching-process check: `NO_MATCHING_PROCESSES`.
