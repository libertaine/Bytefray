# Bytefray V5 — RC1 Blocker Remediation and Source Requalification

**Date:** 2026-09-14  
**Branch:** `v5-research`  
**Rejected candidate:** `84032674facc9c8720533f65afce00a3369cf7d6`  
**Scope:** Source remediation and source-distribution preparation only  
**Publication:** Not authorized or performed

## 1. Why the earlier verdict was rejected

The earlier `V5_RC1_READINESS_AND_QUALIFICATION.md` conclusion was invalidated
by an independent adversarial review. Candidate `84032674` had two reproduced
release blockers:

1. A Tournament match already recorded as completed silently reran when its
   canonical `result.json` was missing, without explicit retry authorization.
2. Replay History verified cached replay bytes without rereading the current
   parent result, so a result identity changed after indexing could still lead
   to Viewer launch.

The review also found that the PowerShell smoke depended on an existing user
catalog, the wheel validator omitted release-critical resources and mappings,
Tournament help contradicted the homogeneous-roster rule, and the recorded
wheel/sdist did not contain the rejected candidate's module guard. Those
archives and the earlier `RC1 READINESS PASSED` verdict are not qualification
evidence for any replacement candidate.

## 2. Remediation

### Tournament resume integrity

Every prior `completed` entry now enters canonical artifact validation even
when `result.json` is absent. Missing, malformed, foreign, or replay-invalid
completed artifacts become `corrupted`, remain excluded from standings, and do
not execute unless the existing `retry_failures`/`--retry-failed` mechanism is
explicitly selected. No new retry state or schema was introduced.

Regression coverage proves that a missing result does not call the match
service, create a result, change the retained replay, or create an occurrence;
an explicitly authorized retry still completes with a new occurrence.

### Replay History click-time authority

Result-backed History resolutions now retain their indexed result/match
identity and pass that context to `preflight_result_replay()` at click time.
The shared preflight rereads the current result, verifies its association,
resolves its current replay reference, checks its digest, and validates replay
header identity. History rejects either a canonical-preflight failure or a
result replay path that changed after indexing.

Replay-only historical entries deliberately retain the existing contained
standalone-file behavior because there is no parent result to authorize them.
The SQLite index remains disposable derived state and the filesystem work
remains on the existing worker thread.

### Release tooling and CLI documentation

- The PowerShell smoke uses a unique repo-local data root unless one is
  explicitly supplied, installs bundled starters into that root, and discovers
  the resulting catalog. It no longer uses the unsupported
  `BYTEFRAY_AGENTS_DIR` variable.
- The wheel validator requires all four API-v1/API-v2 blank/annotated scaffold
  families, all shipped starter manifests/sources, the packaged branding icon,
  exact console-script target mappings, and agreement between wheel filename,
  dist-info directory, and METADATA version.
- Tournament help now states that rosters must be homogeneous and mixed
  Python/VM rosters are rejected; production behavior was not changed.

## 3. Regression and focused qualification

The two product regressions were first observed failing on `84032674`: the
missing-result case fell through to execution and the post-index result mutation
returned `VERIFIED`. After remediation:

| Gate | Result |
|---|---:|
| New blocker regressions plus adjacent integrity controls | 7 passed |
| Tournament service and results | 55 passed |
| Replay History, concurrency, shared preflight, and presentation | 198 passed, 1 skipped |
| Tournament and Replay History GUI lifecycle/launch paths | 116 passed |
| Wheel validator and packaging/resource/scaffold gates | 166 passed, 7 skipped |
| CLI invocation/help/version and related public commands | 115 passed |
| Agent API/process/parameter/scaffold/starter gates | 248 passed, 6 skipped |
| V5 starter competence | 54 passed |
| Accessibility contracts | 7 passed |
| Permanent stable-v4 equivalence | 23 passed |
| Windows PowerShell 5.1 fresh-root smoke | passed; 21 starters discovered |
| PowerShell 7 fresh-root smoke | passed; 21 starters discovered |

The source-wide qualification observed `3667 passed, 22 skipped, 3 deselected`
from the canonical suite and `507 passed, 6 deselected` from the GUI-marked
suite. Ruff and the separate engine/client mypy gates passed. The candidate
commit is established only after this record and all source changes are present;
the exact commit ID belongs in the immutable handoff because a Git commit cannot
embed its own hash.

## 4. Manual adversarial regression evidence

For a real CLI Tournament, deleting the completed match's result and resuming
without retry exited 1, recorded `corrupted` with
`resumed_result_mismatch: result.json is not present`, left the replay hash
unchanged, and did not recreate the result. Repeating with `--retry-failed`
exited 0 and produced a distinct new occurrence.

For a real result/replay indexed by Replay History, changing only the result ID
after indexing produced History status `mismatch`, structured failure
`result_association_mismatch`, and `blocks_launch=True`. The canonical shared
preflight returned the same failure.

Separate fresh roots under Windows PowerShell 5.1 and PowerShell 7 each began
without an agent catalog, installed and discovered all 21 bundled starters, ran
the tiny CLI match, and exited 0.

## 5. Qualification boundaries

This record establishes source behavior only. Fresh wheel/sdist archives must
be built after the candidate commit, validated, inspected for the corrected
production code, and hashed. They are preparatory artifacts, not Windows or
Linux installed-package qualification.

Still open and separate:

1. Windows executable/installer build and clean installation lifecycle.
2. Linux clean-environment wheel/sdist installation and GUI checks where
   supported.
3. Tag creation, upload, and publication authorization.

No Windows installer was built, no release tag was created, and nothing was
published during this remediation.

## 6. Stage decision

The remediation found no gameplay, Agent API, schema, determinism, or product
architecture uncertainty. The fixes are narrow RC stabilization and do not
justify an Alpha 2 milestone. The replacement source may proceed to separate
package qualification only if the final exact-tree gates and fresh archive
provenance checks remain clean.
