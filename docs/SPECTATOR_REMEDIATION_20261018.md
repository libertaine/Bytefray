# Spectator integration review remediation - 2026-10-18

Status: both findings corrected, independently reproduced as safe, and independently
reviewed. Verification complete with the known baseline failures below. Publication HOLD.

Scope: Bytefray branch v6-spectator-integration, reviewed HEAD d0dc955;
Spectator compatibility checkout designer-integration at 14089a7.
No push, research advancement, fixture edits, or unrelated tracked changes.

## Defects and corrections

P1 root cause: prepare validated the source evidence but did not enforce the
direct export path's source/output separation against the cache root. Pruning
then ranked every ordinary directory by mtime and removed older directories;
hidden folders were deleted by age alone. A successful export could therefore
be followed by deletion of the source match.

Correction: canonical cache/source roots must be disjoint in both directions,
before cache mutation and again before install. Checks include resolved
symlink/junction aliases and both apparent and canonical artifact parents.
Cache entries use a private schema/key marker, a generated-name check, and a
closed set of regular files. Windows reparse points, symlinks, extra files and
subdirectories prevent deletion. Legacy entries qualify for pruning only as
verified production presentations. Discard rechecks ownership after rename.
Only owned entries count toward the 16-presentation retention bound; only
owned, generated staging names qualify for day-old cleanup. Occupied keys are
refused rather than deleting unfamiliar contents.

P2 root cause: verify_outcome compared result.score with the bound terminal
score map, but Broadcast copied entrants[].score without comparing it.
The outcome_verified manifest flag could therefore accompany an invented score.

Correction: terminal and result maps must name exactly A and B and contain
finite JSON numbers, excluding booleans. Every serialized entrant score must
also be finite and equal the corresponding terminal value. Validation precedes
projection and staged manifest writing. No replay verifier was weakened.

Cache migration: all reuse paths share _verify_cached, requiring the new
ownership marker, current source/exporter identity and file verification.
Unmarked legacy entries are rebuilt, including when a frozen product identity
matches. If retirement fails, the concurrent-install fallback refuses the
legacy entry rather than returning its unverified scores.

Independent review also found a malformed legacy manifest exporter=null crash;
ownership now checks the exporter type before reading its name and preserves
malformed entries. Independent review caught and rechecked the legacy
non-discardable fallback described above.

## Reproductions and regression coverage

Before correction, 23 new adversarial cases failed on d0dc955. In the original
P1 case, a disposable generated match was placed beside 16 newer directories
under the chosen cache root; prepare returned success and the old source was
deleted. In P2, only a copied valid fixture's entrant score was changed;
export and prepare accepted it.

The final tests cover both original cases; equal/ancestor/descendant cache
roots; native Windows junction aliases; unrelated hidden/ordinary directories;
reparse-point entries; occupied keys, including files added during export;
source hash/mtime preservation; legitimate legacy and marked-cache retention;
corrupt owned entries; stale versus active owned staging; malformed legacy
exporter metadata; missing/malformed/mismatched/nonfinite/boolean entrant and
score-map values; positive terminal-to-Broadcast agreement; legacy cache
migration, including blocked retirement.

Both original cases were independently repeated after correction using fresh
NativeMatchService fixtures. P1 refuses output_unsafe before mutation and
preserves source hashes/mtimes and all 16 siblings. P2 refuses
outcome_unverified through both APIs, preserves sources and leaves no manifest.
The independent reviewer rechecked the malformed legacy and blocked-retirement
cases and reported no outstanding actionable findings.

## Verification ledger

Final focused exporter/cache plus viewer service: 103 passed, 1 POSIX-only skip.
Log: .remediation-focused-final-03.log; JUnit counterpart retained.
The exporter module has 84 cases versus 32 before remediation: 52 added cases.

WSL Ubuntu/Python 3.12 headless focused run on Linux-native /tmp storage:
104 passed, including real POSIX symlinks and non-executable-file behavior.
Log: .remediation-linux-native-focused-02.log. The first mounted-filesystem run
had 103 passes and one permission-bit assertion failure on /mnt/d; moving to
native Linux storage resolved it without source changes. An initial fresh-copy
harness omitted the temp parent and produced setup errors; the corrected
fresh harness passes all cases. These are separate environment/harness ledgers.
The native Linux desktop GUI remains unqualified.

Final broader client/launcher/command/viewer-service/Designer-workflow/paths/
installation documentation: 781 passed, 2 platform skips, 13 gui deselected.
Log: .remediation-broad-final-03.log.

Final Designer Spectator integration: 10 passed, Qt offscreen.
Log: .remediation-gui-final-03.log. This is automated display-backed evidence,
not human/native usability qualification.

Godot 4.7.2 cached presentation check: PRESENTATION OK, manifest v2, and
CUE BANK OK, 9 clips. Log: .remediation-cache-viewer.log.

Lint: repository source checks pass. Disposable .remediation-* and inherited
.review-spectator-* generated test roots were excluded; the literal initial
ruff check . also inspected synthetic agent.py files and reported 151
generated-artifact findings. No source lint rule was weakened.
Both package mypy invocations pass: engine 106 files, client 20 files.
git diff --check passes.

Spectator complete exporter/cross-repository/Godot suite: 68 passed in 554.42 s,
with BYTEFRAY_ROOT=spectator-pin-9c81718, BYTEFRAY_PRODUCTION_ROOT=this worktree
and GODOT=Godot 4.7.2 console. Includes frozen showcase and production-sample
document byte identity, fresh-match playback, and all existing prototype checks.
Log: D:/Projects/Bytefray-Spectator-integration-20261017/work/remediation-sp-final-01.log.

Baseline comparison: reran all 120 documented failure nodes under the supported
.pytest-tmp/remediation-baseline-compare-01 subtree. Result: 32 passed,
85 failed, 3 errors. The 88 failure/error node IDs exactly equal the retained
unmodified-10c3530 baseline set: no additions, no omissions. The 32 passing
nodes explain the custom-basetemp authorization artifacts. Existing E8/E9
freeze/pin and research-selectability failures remain open and are not
qualification evidence for this remediation.
Logs: .remediation-baseline-compare-01.log and
.remediation-baseline-comparison.json.

Complete headless audit (Windows Python 3.13.14): 8,735 passed, 95 failed,
26 errors, 34 skipped, 13 gui deselected; 4,478.08 seconds. It was launched after
the initial two corrections; final cache-reuse hardening was subsequently covered
by the final focused, broader client and Designer runs above.

All 121 failure/error nodes are accounted for: the documented 120-node list
plus one additional temp-layout case:
engine/tests/test_v6_e9_v2_independent_consumers.py::
test_production_source_checker_rehashes_real_files_and_adoption[outside_repository].
That test constructs its supposedly outside file under tmp_path. With the audit's
inside-checkout basetemp it is actually inside the repository. The exact failure
reproduces on unchanged 10c3530 with the same layout (1 failed); final code passes
with a genuinely outside-repository OS temp root (1 passed).
Together with the earlier 32 resolved temp artifacts, the audit contains 88
documented baseline failures/errors and 33 test-layout artifacts; no unexplained
or correction-attributable failures remain. No test assertion or fixture was
changed to obtain this result.
Logs: .remediation-full-01.log / .xml, .remediation-full-comparison.json,
.remediation-outside-node-baseline-01.log and
.remediation-outside-node-external-01.log.

The full audit's synthetic E9 tests do not qualify or advance E9.

## Remaining limits and publication readiness

The two reported defects are corrected and independently reproduced as safe.
Overall publication remains HOLD with the existing red research baseline and pending the
human GUI/audio usability session, native Linux desktop qualification, and a
frozen PyInstaller Bytefray build with the Spectator command. Export still has
the documented quadratic projection cost; this remediation does not change it.

Static symlinks/junctions and ordinary filesystem collisions are handled.
An active hostile process replacing filesystem entries after checks remains a
TOCTOU limitation; these path checks are not an OS isolation boundary.
Unrecognized or malformed cache directories are intentionally preserved and
can exceed the retention count; only positively owned data is reclaimed.

Frozen showcase/research artifacts and Spectator tracked files remain unchanged.
E9 and M2-6 are not advanced. Neither repository is pushed.
