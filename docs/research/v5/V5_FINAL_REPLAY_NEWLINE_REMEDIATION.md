# Bytefray 5.0.0 Final Replay Newline Remediation — Phase 4A

Phase 4A resolves the cross-platform replay-hash mismatch surfaced by Phase 4
Linux qualification. The mismatch is a replay JSONL **serialization** defect
(platform-native line endings), not a gameplay/simulation determinism defect.
This phase makes canonical replay JSONL serialization use LF (`\n`) on every
platform, adds permanent regression coverage, and re-runs the focused and
full qualification gates. It does not rebuild artifacts, tag, or publish.

## 1. Background

Phase 4 (`docs/research/v5/V5_FINAL_LINUX_PACKAGE_QUALIFICATION.md`) recorded
a genuine, unresolved finding: the fixed-seed regression

```
bytefray run --a-type v5_dual_team --a-param raider_share=0.7 --b-type v4_quorum \
  --ruleset bytefray-rules-4 --arena 512 --quota 8 --ticks 30 --seed 602
```

produced different replay SHA-256 digests on Windows vs. Linux, even though
gameplay executed successfully on both and Phase 4's own investigation ruled
out flakiness, Python minor-version drift, and wheel/sdist packaging
differences. That investigation checked for line-ending corruption only on
the Linux-generated replay (finding no `\r`, as expected — Linux was never
the platform producing `\r\n` in the first place) and had no Windows-side raw
replay bytes available on that machine to compare directly, so it could not
rule the hypothesis in or out from Windows evidence. Phase 4 left the
publication gate **FAILED** pending root-cause identification.

## 2. Original evidence

The two replay files recorded during/after Phase 3/4 (`windows-replay.jsonl`,
`linux-replay.jsonl`, transferred to `/home/rod/bytefray-v5-final-release/`)
were re-examined directly for this phase, independently reproducing every
figure below (not merely re-stating the task brief's numbers):

| Source | Bytes | SHA-256 | CRLF sequences | Records |
|---|---|---|---|---|
| Windows | 23,184 | `dcf24b4ef03bb45446b4a11774713546dd657c0ccd3429e643cd9fab9a0a3087` | 13 | 13 |
| Linux | 23,171 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` | 0 | 13 |

Both hashes match Phase 3's recorded Windows digest and Phase 4's recorded
Linux digest exactly.

## 3. Root-cause proof

Verified directly against the two transferred replay files (`hashlib`,
`bytes.replace`, and the production `battle_engine.replay.iter_replay`
deserializer — not a re-implementation):

- Windows CRLF count: **13**; Linux CRLF count: **0**.
- Byte-size difference: 23,184 − 23,171 = **13** (one byte saved per `\r`
  removed — internally consistent with exactly 13 CRLF sequences).
- `windows-replay.jsonl` bytes with every `b"\r\n"` replaced by `b"\n"`:
  **23,171 bytes**, SHA-256
  `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` —
  **identical** to the raw Linux bytes and digest. Byte equality: **TRUE**.
- Parsing both files through `iter_replay` (the real production reader):
  **13/13 records on each side**, **zero semantic differences** between the
  two record sequences.

This conclusively narrows the Phase 4 finding to a serialization-only
defect.

## 4. Classification

- **NOT** gameplay nondeterminism.
- **NOT** scheduler nondeterminism.
- **NOT** process-share/`Fraction` nondeterminism (Phase 4 already audited
  and ruled this out at the source level; this phase's byte/semantic proof
  independently corroborates that conclusion).
- **IS** a cross-platform replay newline serialization defect: the
  production replay writer let the host OS's text-mode newline translation
  decide the on-disk line ending instead of the writer defining it.

## 5. Source root cause

The sole production writer of the persisted `replay.jsonl` artifact is
`write_replay()` in `engine/src/battle_engine/replay.py`. Every real match
run reaches it through exactly one path:
`NativeMatchService.run()` → `_finalize_native_artifacts()`
(`engine/src/battle_engine/match_service.py:1278`) → `write_replay()` →
`temporary.replace(publish_path)`, immediately followed by
`hashlib.sha256(publish_path.read_bytes())` for the `result.json` envelope's
`replay_sha256`. `cli.py` (`bytefray run`), `agent_test.py`, and
`tournament_service.py` all go through this same `NativeMatchService`, so
there is exactly one production seam, not several.

Before this fix:

```python
def write_replay(path: str | Path, records: Iterable[ReplayRecord]) -> None:
    with Path(path).open("w", encoding="utf-8") as stream:
        stream.writelines(serialize_record(record) + "\n" for record in records)
```

`Path.open("w", encoding="utf-8")` with no `newline=` argument leaves Python
text-mode I/O's universal-newline translation active: every `"\n"` written is
translated to `os.linesep` on write, which is `"\r\n"` on Windows and `"\n"`
on Linux/macOS. The writer never explicitly decided the on-disk byte — the
host OS did.

The codebase already carried independent, undocumented-until-now evidence of
this exact hazard: `engine/tests/test_ruleset_v1_equivalence.py:120-124`
normalizes `b"\r\n"` → `b"\n"` before hashing a replay specifically because
"text-mode newline translation differs by host" — a workaround for the same
defect this phase fixes, written before this defect had a name.

A second, independent JSONL writer, `JSONLSink`
(`engine/src/battle_engine/telemetry.py:25-33`), has the same unpinned
text-mode behavior, but its output is an intermediate scratch file: all
three of its call sites (`match_service.py:874`, `:978`, `:1349`) write to a
`tempfile.mkstemp` path that is read once via `iter_replay` and then deleted
(`match_service.py:1311` and the surrounding `finally` blocks) once
`write_replay` has re-serialized the canonical artifact. Its raw bytes never
reach the persisted, hashed `replay.jsonl` a user or `result.json` ever sees,
so it is out of scope for this narrow, artifact-focused fix (see §9).

## 6. Repair

One seam, one line changed (`engine/src/battle_engine/replay.py`):

```python
def write_replay(path: str | Path, records: Iterable[ReplayRecord]) -> None:
    # newline="\n" disables universal-newline translation so the writer
    # itself defines the on-disk line ending (LF) instead of delegating to
    # the host OS, which would otherwise emit CRLF on Windows and make
    # semantically identical replays hash differently across platforms.
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.writelines(serialize_record(record) + "\n" for record in records)
```

`newline="\n"` is the standard library's documented way to disable
translation entirely (per `io.TextIOWrapper`: "if newline is `''` or `'\n'`,
no translation takes place"), so every `"\n"` written reaches disk as the
single byte `0x0A`, unconditionally, on every platform. No hash is
hardcoded into production code. `serialize_record`, record content, key
ordering (`sort_keys=True`), separators, encoding, and the trailing-newline
behavior are all unchanged.

## 7. Tests added/changed

New file: `engine/tests/test_replay_newline_canonicalization.py`, exercising
the real production `write_replay`/`iter_replay` (no re-implementation):

1. `test_write_replay_contains_no_crlf_at_the_byte_level` — asserts
   `b"\r\n" not in raw` and `b"\r" not in raw` on the actual written bytes.
2. `test_write_replay_terminates_every_record_with_a_bare_lf` — asserts
   every record (including the last) is `\n`-terminated and none end in
   `\r`, preserving the existing trailing-newline behavior.
3. `test_write_replay_preserves_semantic_record_content` — round-trips
   through `iter_replay` and asserts the deserialized records equal the
   originals.
4. `test_write_replay_pins_lf_in_the_writer_itself_not_via_host_default` —
   the stronger, platform-independent contract test: spies on `Path.open`
   to assert `write_replay` explicitly passes `newline="\n"` and
   `encoding="utf-8"`. This fails if the `newline` argument is ever dropped,
   even though the byte-level test above would still pass on Linux (where
   the OS default happens to be LF) — it is the test that would have caught
   the original defect on a Linux CI machine without needing a Windows
   runner.
5. `test_write_replay_lf_bytes_are_stable_across_repeated_writes` — two
   independent writes of the same records produce byte-identical output.

No existing test was modified. `test_ruleset_v1_equivalence.py`'s
`b"\r\n"` → `b"\n"` normalization (line 124) was left in place: after this
fix it is a no-op on every platform (nothing left to normalize), and
removing it is unrelated cleanup outside this phase's narrow scope.

## 8. Windows fixed-seed result

**Not independently reproducible in this session** — this remediation was
performed and qualified entirely on Linux; no Windows machine was available
to re-run the fixed-seed command against the patched source. This is stated
explicitly rather than assumed or fabricated.

What was verified on Linux, and why it supports (without proving) the
Windows outcome:

- Re-running the exact fixed-seed command against the **patched** source on
  Linux reproduced the Linux baseline exactly: 23,171 bytes, SHA-256
  `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a`, 0 CRLF,
  13 records — byte-identical to the pre-fix Linux replay. This confirms the
  fix is a no-op on a platform where `os.linesep == "\n"`, as expected, and
  that gameplay/serialization content is otherwise unaffected.
- `newline="\n"` is a language/standard-library guarantee documented by
  CPython's `io` module, not an observed or platform-contingent behavior:
  it disables newline translation unconditionally, independent of
  `os.linesep`. `test_write_replay_pins_lf_in_the_writer_itself_not_via_host_default`
  (§7.4) asserts the writer actually passes this argument, rather than
  relying on Linux's default coincidentally matching the desired byte.

**Recommendation:** before proceeding to artifact rebuild, re-run the exact
Phase 3/4 fixed-seed invocation on a Windows machine against this
remediation commit and confirm: zero CRLF sequences, and raw SHA-256
`6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a`. Per
Section E/H of the task brief, if that exact hash is not produced, the fix
needs further investigation before artifact rebuild — this should happen
before, not instead of, that Windows confirmation.

### 8.1 Windows verification (actual evidence, independent session)

The recommendation above was carried out. Windows remediation commit under
test: `314ccdaa1386b5cf662015c8596e553c0b5701e4` (`fix(v5): canonicalize
replay newlines across platforms`, direct child of `61d5abb` "docs(v5):
record final Windows qualification", itself descending from `4be3384`
"release: prepare Bytefray 5.0.0" — ancestry confirmed with
`git merge-base --is-ancestor`, not inferred from branch naming).

Exact fixed-seed invocation (recovered from §1 above, matching Phase 3/RC1):

```
bytefray run --a-type v5_dual_team --a-param raider_share=0.7 --b-type v4_quorum \
  --ruleset bytefray-rules-4 --arena 512 --quota 8 --ticks 30 --seed 602 \
  --replay <path>
```

**First attempt (contaminated environment) — preserved as evidence, not
discarded:** running this command against the remediation commit, using
this machine's normal writable agent catalog (`%ProgramData%\Bytefray`),
produced a replay that matched the expected byte size (23,171) and CRLF
count (0) but **did not** match the required SHA-256 — it produced
`c49eee6ab89740be42668e564180295facc5a063ee9352d4794403360f8e236a`
instead. Per the task brief's Section F this is a STOP condition, so
qualification paused for root-cause diagnosis before any further gate was
run.

Diagnosis: the mismatch was isolated to the `source_sha256` /
`local_source_fingerprint` provenance fields embedded in the replay
header, which hash the *raw bytes* of the `v5_dual_team` starter agent's
`agent.py` actually loaded at match time. This machine's persistent
writable agent catalog held a stale copy of that file from an earlier
session — `agent.py`, 9,516 bytes, 221 CRLF, SHA-256 `5bc0a8c4...` —
textually identical to the canonical bundled starter (9,295 bytes, 0 CRLF,
SHA-256 `833871d1...`) except for CRLF line endings. `starters.py`'s own
drift detection (`starter_content_digest`) normalizes newlines before
comparing, correctly judges the two content-equivalent, and by design
leaves an "equivalent" installed copy alone rather than overwriting it —
so this stale copy was never a bug, and the engine's raw-byte provenance
hashing correctly reported it as literally different bytes from the
canonical starter. This is local machine/environment state predating this
session, not a defect introduced or exposed by the newline remediation
itself, and it does not touch any tracked file in the repository.

Rather than mutate the shared, persistent `%ProgramData%\Bytefray` catalog
to work around this, the clean re-run instead used the engine's own
documented `BYTEFRAY_ROOT` environment-variable override to point at a
freshly created, empty data root, letting `ensure_starter_agents()` install
the canonical bundled starter (LF, 9,295 bytes, SHA-256 `833871d1...`) with
no contamination and no changes to the machine's real environment:

- Post-fix Windows replay (clean root): **23,171 bytes**
- CRLF count: **0**
- SHA-256: **`6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a`**
  — **exact match** to the required canonical hash and to the Linux value
  above.

**Semantic comparison:** rather than relying on the pre-fix Windows replay
recorded only in this document (the original file lives on the Linux
machine referenced in §2 and was not available in this session), the
comparison was re-derived independently: reversing the fix's transform
(replacing every bare `\n` in the clean post-fix replay with `\r\n`)
reproduced a byte sequence of exactly 23,184 bytes with SHA-256
`dcf24b4ef03bb45446b4a11774713546dd657c0ccd3429e643cd9fab9a0a3087` — an
exact match to the pre-fix hash recorded in §2 — and normalizing that
reconstruction back to LF reproduced the clean post-fix bytes exactly
(13/13 records, zero semantic differences). This independently confirms
the only difference between the pre-fix and post-fix Windows artifacts is
newline encoding.

Remaining Windows gates, all against the clean-root, uncontaminated
environment:

| Gate | Command | Result |
|---|---|---|
| Newline regression | `pytest engine/tests/test_replay_newline_canonicalization.py` | **PASS** — 5 passed |
| Focused replay/integrity/history/result/runtime suite | `pytest engine/tests -k "replay or integrity or history or result or runtime"` | **PASS** — 811 passed, 3 skipped |
| Ruleset-v4 equivalence | `pytest engine/tests/test_v4_stable_ruleset_equivalence.py engine/tests/test_v4_trace_equivalence.py` | **PASS** — 25 passed; `git status --short` clean afterward, no vector/golden files touched |
| Full source suite | `python -m pytest` | **PASS** — 3,687 passed, 22 skipped, 3 deselected, 0 failed in 380.18s (baseline 3,682 + the 5 new regression tests; no new failures) |
| Native Windows GUI suite | `$env:QT_QPA_PLATFORM='windows'; pytest tests/ -m gui` | **PASS** — 507 passed, 6 deselected in 182.50s; reproduced the known non-failing `0x8001010d` diagnostic from `test_linux_designer_smoke.py`, unchanged from the existing qualification caveat |
| `ruff check .` | — | **PASS** — all checks passed |
| `mypy engine/src/battle_engine` | — | **PASS** — no issues, 114 source files (matches Phase 3) |
| `mypy client/src/battle_client` | — | **PASS** — no issues, 16 source files (matches Phase 3) |
| `git diff --check` | — | **PASS** — clean |
| `git status --short` (final) | — | clean |

The remediation commit was independently confirmed to touch only
`engine/src/battle_engine/replay.py` (a 5-line, newline-only change),
`engine/tests/test_replay_newline_canonicalization.py`, and the two
documentation files listed in §1 — no scheduler, process-share, action-
ordering, Ruleset-v4 semantics, Agent API, starter-agent behavior,
capture-timing, process-reach, disruption-logic, or replay-schema changes.

**Gate:** REPLAY NEWLINE REMEDIATION QUALIFIED ON WINDOWS — READY FOR FINAL
ARTIFACT REBUILD AND CROSS-PLATFORM REQUALIFICATION. This is not
publication approval; artifacts have not been rebuilt, the branch has not
been merged, and nothing has been tagged or published as part of this
verification.

## 9. Audit of other replay-writing call sites

| Site | Classification | Action |
|---|---|---|
| `replay.py:679` `write_replay` | Canonical writer for the persisted artifact | Fixed (§6) |
| `telemetry.py:25-33` `JSONLSink` (3 call sites in `match_service.py`: 874, 978, 1349) | Intermediate/scratch writer; output is read once via `iter_replay` then unlinked before the run completes; never becomes the hashed, persisted `replay.jsonl` | No change — out of scope for the persisted-artifact contract this phase targets |
| `_legacy/core.py` (own `JSONLSink`) | Frozen historical code (AGENTS.md: "`_legacy/` is frozen historical code, retained as a characterized migration fixture"), excluded from lint, not part of the current `battle_engine` production package | No change |
| `tools/research/v5/corpus_runner.py` | Calls `NativeMatchService().run(request)` directly — funnels through the canonical writer | No change required |
| `tournament/scripts/btctl.py` | Invokes the `bytefray` CLI as a subprocess (`--replay` flag) — funnels through the canonical writer | No change required |
| `agent_trace.py:255,278-286` `TraceWriter` (`trace.jsonl`) | Different artifact (agent decision trace), same unpinned-newline pattern, but explicitly out of scope: the task brief and `AGENTS.md` distinguish replay serialization from traces/logs | Not touched, flagged for awareness only |
| `result_model.py:194-204` `write_json_atomic` (`result.json`, `tournament.json`, evaluation JSON) | Already binary-mode (`os.fdopen(..., "wb")`, explicit `b"\n"`) — immune to text-mode newline translation | No change — not affected by the original defect |
| `telemetry.py:36-42` `JSONSummarySink` (`summary.json`) | Legacy, reachable only through `Kernel`'s default constructor, which no production path exercises | No change |
| Spectator JSONL (`spectator_events.py`, `spectator_derivation.py`, `spectator_perspective.py`) | Writes to **stdout**, not a file | Not applicable |

No refactor was made for aesthetic consistency; every non-canonical site
above was left unchanged because its output is not part of the persisted,
hashed replay artifact the release gate depends on.

## 10. Ruleset-v4 equivalence result

Command (matching Phase 3's exact invocation):

```
pytest engine/tests/test_v4_stable_ruleset_equivalence.py engine/tests/test_v4_trace_equivalence.py
```

Result: **25 passed** in 14.04s. `git status --short` showed no
vector/golden/reference-file modification as a result of this run — no
gameplay golden data was touched by this phase.

## 11. Full source qualification

| Gate | Command | Result |
|---|---|---|
| New newline regression | `pytest engine/tests/test_replay_newline_canonicalization.py` | **PASS** — 5 passed |
| Focused replay/integrity/history/result/runtime suite | `pytest` across `test_replay_contract.py`, `test_replay_integrity.py`, `test_replay_history.py`, `test_replay_history_concurrency.py`, `test_replay_reconstruction.py`, `test_replay_dependency_metadata.py`, `test_v5_replay_history_presentation.py`, `test_ruleset_persistence.py`, `test_result_model.py`, `test_python_runtime.py`, `test_native_match_service.py` | **PASS** — 328 passed |
| Ruleset-v4 equivalence | see §10 | **PASS** — 25 passed |
| Full suite | `python -m pytest` | **3,693 passed, 14 skipped, 3 deselected, 2 failed** in 364.27s |
| Ruff | `ruff check .` | **PASS** — all checks passed |
| Engine mypy | `mypy engine/src/battle_engine` | **PASS** — no issues, 114 source files (matches Phase 3's recorded file count) |
| Client mypy | `mypy client/src/battle_client` | **PASS** — no issues, 16 source files (matches Phase 3's recorded file count) |
| `git diff --check` | `git diff --check` | **PASS** — clean |
| Windows GUI suite | — | **Not run**: no Windows machine available in this session. Flagged as an open item for Windows-side confirmation, not fabricated. |

**The 2 full-suite failures are pre-existing and unrelated to this fix:**
`test_v5_alpha1_phase_b_engine_hygiene.py::test_version_transition_5_0_0` and
`test_windows_packaging_spec.py::test_installer_versions_match_package_and_release_tag`
both assert `importlib.metadata.version("bytefray") == "5.0.0"` and instead
observe `"4.0.0rc2"`. This is the pre-existing "contaminated dev `.venv`"
condition already documented in
`docs/research/v5/V5_FINAL_LINUX_PACKAGE_QUALIFICATION.md` §3/§12 (this
machine's editable install was registered under an older version string) —
it is package-metadata/environment state, not source code, and has nothing
to do with replay serialization. Confirmed by reproducing the identical
failure with `engine/src/battle_engine/replay.py`'s fix temporarily stashed
out (`git stash push -- engine/src/battle_engine/replay.py`, re-run, restore
via `git stash pop`): both tests fail identically with or without this
phase's change, proving the failures predate and are independent of this
remediation. No new production defect was found by this phase.

## 12. Release impact

- Final artifacts must be rebuilt from this remediation commit before any
  publication candidate is qualified — the previously qualified wheel/sdist
  no longer reflect current source once this commit lands.
- The Phase 3 final wheel/sdist (`bytefray-5.0.0-py3-none-any.whl`,
  `bytefray-5.0.0.tar.gz`) remain valid **historical qualification
  evidence** for the pre-remediation source, but are **no longer
  publication candidates**.
- Next gate: rebuild wheel/sdist from this commit, re-run focused Windows
  qualification (including the fixed-seed hash check against
  `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a`) and
  Linux requalification of the newly built artifacts. No artifact rebuild,
  tagging, or publication occurred in this phase.
