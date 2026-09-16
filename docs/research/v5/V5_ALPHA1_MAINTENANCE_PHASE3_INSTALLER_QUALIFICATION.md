# Bytefray V5 Alpha 1 Maintenance — Phase 3: Installer & Deferred Hygiene Qualification

**Status:** Complete except one explicitly gated tier (Section I). FIND-03
implemented with a resumable-marker recovery design (not the audit's staged
directory-rename proposal). Installer `logs/` relocated. `build_engine_command`
retained as live test infrastructure. A real Windows installer candidate was
built and compiled successfully from this checkout and exercised at the
frozen-executable level; the installer's own elevated install/uninstall
lifecycle was **not** run, by explicit user decision (Section I). No commit or
push was performed.

---

## A. Starting state

| Item | Value |
|---|---|
| Branch | `v5-research` |
| HEAD SHA (start and throughout) | `9a95e817368f59fc170836731aa61471068609b9` |
| Upstream/tracking branch | `origin/v5-research` |
| Ahead/behind upstream | `0` / `0` |
| Working-tree state at phase start | Clean — `nothing to commit, working tree clean` |
| Product version (`pyproject.toml`) | `5.0.0a1` (unchanged) |
| Phase 2 commit | `9a95e81` ("chore(v5): complete behavior-neutral maintenance cleanup", 2026-09-11 11:52:16 -0400) — **this is also current HEAD**; Phase 2 was already committed before this phase began, so no pre-existing uncommitted work needed to be separated from Phase 3's own diff |

Phase 0's and Phase 1's and Phase 2's reports were all already present and
committed at the start of this phase. `git status --short` was clean before
the first edit, and HEAD was re-verified unchanged (still `9a95e81`) after
every long-running step in this phase (the full build, the full test suite),
per this repository's standing qualification-integrity discipline —
`git rev-parse HEAD` and SHA-256 digests of the four files this phase touches
were recorded before the full test suite and re-verified byte-identical
afterward (Section J).

**Note on "the exact code qualified":** the Windows installer build in
Section E was produced from the live working tree, which includes this
phase's own uncommitted changes (`starters.py`, `installer.iss`,
`smoke_after_install.ps1`, plus the new test file) layered on top of committed
HEAD `9a95e81`. This is stated explicitly rather than implied: the build is
not a pure from-`9a95e81` build, it is "HEAD plus this phase's own approved
working-tree diff," which is the correct thing to qualify since that diff is
exactly what this report proposes as the phase's deliverable.

---

## B. FIND-03 analysis — starter refresh atomicity

### B.1 Current implementation, reconstructed

Source: `engine/src/battle_engine/starters.py`.

- **Source directory:** `battle_engine/data/starter_agents/<name>/` (resolved
  by `_starter_resource_dir`, checked against two candidate layouts — a
  source checkout and a frozen/installed resource root).
- **Destination directory:** `<data_root>/agents/<name>/`, where `data_root`
  is `battle_engine.paths.get_data_root()` (or an explicit override).
- **When refresh occurs:** every call to `ensure_starter_agents()`. Call
  sites, confirmed by a full-repository grep: `cli.py` (`--list-agents`,
  L654, and before `bytefray run`'s own agent resolution, L855),
  `tournament_cli.py` (L175), and `app/agent_designer.py`'s
  `AgentDesigner.__init__` (L125, eager, on every Designer launch). In other
  words: on essentially every product entry point that touches agents at
  all — every `bytefray` CLI invocation that lists or runs agents, every
  `bytefray tournament` run, and every Designer launch.
- **Why refresh occurs:** so an installation created before a bundled
  starter's content changed (e.g. the Phase D parameter-schema addition to
  the `v5_*` starters) is not permanently stuck on the old content, without
  ever overwriting a user's own edits (V5 Alpha 1 Phase E0; see
  `test_v5_alpha1_phase_e_starter_refresh.py`'s module docstring).
- **Classification (unchanged by this phase):** per starter, compare the
  installed content digest (`starter_content_digest`, a normalized
  whole-directory SHA-256) against the bundled digest:
  1. `installed_digest is None` → `_copy_missing` (install).
  2. `installed_digest == bundled_digest` → no-op (`CURRENT`).
  3. `installed_digest in SUPERSEDED_STARTER_DIGESTS.get(name, ())` →
     `_mirror_bundled` (upgrade a provably-untouched old release).
  4. anything else → `_copy_missing` + `customized` (preserve, restore only
     missing files).
- **Files/directories created:** `_mirror_bundled` (only reached by case 3)
  writes each bundled file's bytes directly into `destination_dir / relative`
  (`write_bytes`, no temp file, no staging directory) and deletes any file
  under `destination_dir` the current bundled release no longer ships.
- **Overwrite/replacement behavior:** in place, file by file, skipping a file
  whose bytes already match (so a partial re-run does not churn untouched
  files — this property is what makes the fix below possible).
- **Exception/interruption behavior (pre-fix):** none handled. A crash, kill,
  or `OSError` partway through the loop leaves `destination_dir` holding a
  mix of old and new file bytes. `starter_content_digest` of that hybrid
  state matches neither `bundled_digest` nor any entry in
  `SUPERSEDED_STARTER_DIGESTS[name]` (both are exact SHA-256 values over
  the *whole* directory), so the very next `ensure_starter_agents()` call
  falls to case 4 and classifies the starter `CUSTOMIZED` — permanently
  (nothing thereafter can move it back to case 3, since its digest is not,
  and never was, a value in the allowlist).
- **Startup behavior after a partial refresh (pre-fix):** silent. No error,
  no diagnostic — the starter is simply frozen on a hybrid, partially-updated
  version forever, indistinguishable from a real user edit.
- **Designer discovery of temporary/incomplete state:** `_mirror_bundled`
  writes directly into `destination_dir`, which is always exactly one
  starter's real, already-discoverable directory — there was never a
  separate staging directory for discovery to see. The audit's own proposed
  fix (stage-then-rename) is what would introduce that risk; the current
  (pre-fix) code does not have it.
- **Windows-specific semantics:** none exercised, because nothing renames a
  directory — every write is a plain, direct file write.
- **Linux/macOS semantics:** identical code path (`Path.write_bytes`
  cross-platform); the only platform-dependent logic in this module is
  `_normalized_content`'s CRLF/LF text normalization, unrelated to
  atomicity.
- **Tests covering refresh (pre-fix):** `test_v5_alpha1_phase_e_starter_refresh.py`
  covers all four classification outcomes and idempotence, but — confirmed by
  Phase 1 and Phase 2's own re-verification, and re-confirmed here — had zero
  interruption-simulation coverage before this phase.

### B.2 Real invariants (verified against the reconstruction above)

1. Existing usable starters must not be destroyed before replacement is
   ready. **Partially already true pre-fix**: `_mirror_bundled` only
   overwrites a file when its bytes actually differ, so an interrupted
   refresh never produces a truncated or garbage file — only a hybrid mix of
   fully-old and fully-new files. The real gap was never file corruption; it
   was classification (invariant 2).
2. Interrupted refresh must not expose a partial collection as **permanently**
   valid/stuck. **This was the actual defect**, confirmed above.
3. Temporary artifacts must not be Designer-selectable agents. Confirmed:
   `discover_agents()` → `discover_agents_in(_agents_root(root))`
   (`engine/src/battle_engine/agents.py:229-246`), and `_agents_root` is
   exactly `(root / "agents").resolve()` (`agents.py:68-69`) — nothing
   outside `<data_root>/agents/` is ever scanned.
4. Recovery after interruption must be deterministic and understandable.
5. Ordinary successful refresh must be byte-identical to before.

### B.3 Candidate designs evaluated

| Design | Successful-path behavior | Interrupted-path behavior | Windows safety | Cross-platform safety | Complexity | Recommendation |
|---|---|---|---|---|---|---|
| **A — retain current behavior** | Unchanged (already shipping). | Starter permanently misclassified `CUSTOMIZED`; silent, no recovery path ever. | N/A | N/A | None | Rejected: the defect is real and worth fixing (a rare event with a permanent, silent, user-visible consequence — the Designer never shows that starter's newer parameters again). |
| **B — sibling staging directory + atomic directory rename/replace** (the audit's own suggestion) | Byte-identical to today if implemented correctly. | Requires a rename-swap (old→`.bak`, staged→old, delete `.bak`) because neither Windows `MoveFileEx`/`ReplaceFile` nor POSIX `rename(2)` atomically replaces a non-empty destination directory; this has its own interruption window between the two renames, and a botched cleanup can leave an orphaned staging/`.bak` directory **inside** `agents/`, which `discover_agents()` *would* then see as a bogus entry — a newly introduced regression, not a hygiene fix. | Unsafe without a second layer of interruption-handling for the rename-swap itself. | Same problem on POSIX. | High — needs its own crash-safety design, its own tests, and still does not fully close the gap. | Rejected, confirming Phase 2's deferral. Re-verified independently in this phase, not merely trusted from Phase 2's text (per invariant 15). |
| **C — stage outside discovery scope (temp/cache dir), then promote** | Byte-identical if implemented correctly. | Reduces discovery risk (staging is never under `agents/`) but the *promotion* step is still the same non-atomic directory replace as Option B — moving the problem, not solving it. | Same promotion-atomicity problem as B. | Same. | Comparable to B, for less benefit. | Rejected as its own full design; its core idea (stage outside `agents/`) is reused in the selected design below, but applied to a small marker file instead of the whole content tree. |
| **D — manifest/versioned refresh: validate via digest, make the existing process safe enough without directory replacement** | Byte-identical (no change to `_mirror_bundled`'s own per-file writes). | **Recoverable**: a small marker recorded *before* the mirror starts, outside `agents/`, lets the next launch resume `_mirror_bundled` — which is already idempotent — instead of relying on the (unfixable without B/C) whole-directory digest to detect "in progress." | Safe: the only atomicity primitive relied on is a single-file `Path.replace` (write-to-temp, then rename), which both Windows (`MoveFileExW` on a same-volume single file) and POSIX (`rename(2)`) guarantee atomically. | Same guarantee holds on POSIX. | Low — one new marker file, three small helper functions, no directory staging, no rollback logic. | **Selected.** |
| **E — other minimal design** | — | — | — | — | — | Not needed; D already meets the implementation gate below with lower complexity than B/C. |

The deciding insight: FIND-03's actual defect is not file-level corruption
(already prevented by `_mirror_bundled`'s skip-if-identical writes) — it is
that the *classification logic* cannot tell "a real user edit" apart from
"an interrupted mirror" once the resulting digest is a hybrid value.
`_mirror_bundled` is already idempotent and resumable (re-running it against
a partially-updated directory finishes the job, whatever state it was left
in). What was missing was a way to tell the *next* call "resume, don't
classify" — and that only requires remembering intent across the
interruption, not achieving whole-directory atomicity.

### B.4 Selected design — resumable transition marker

Implemented in `engine/src/battle_engine/starters.py`:

- `_refresh_marker_path(data_root, name)` → `<data_root>/.starter_refresh_state/<name>.json`,
  a sibling of `agents/`, never inside it.
- `_write_refresh_marker(data_root, name, target_digest=...)`, called
  **immediately before** `_mirror_bundled` in the case-3 branch: writes
  `{"digest_version": ..., "target_digest": <bundled_digest>}` to a temp file
  and `Path.replace`s it into place — atomic, so the marker is either fully
  absent or fully present, never partial.
- `_read_refresh_marker(data_root, name)`: returns the recorded
  `target_digest`, or `None` if absent/unreadable/version-mismatched
  (treated as "nothing to resume," never as an error).
- `_clear_refresh_marker(data_root, name)`: `unlink(missing_ok=True)`.
- `ensure_starter_agents()`'s per-starter loop now checks the marker *before*
  ordinary classification:
  - marker present and its `target_digest` still equals the current
    `bundled_digest`, and the installed digest has not yet reached it →
    **resume**: call `_mirror_bundled` again (idempotent), clear the marker,
    record `refreshed`.
  - marker present but stale (either the mirror had already finished and
    only marker cleanup was interrupted, or the *bundled release itself*
    changed since the interruption, e.g. a product upgrade in between) →
    discard the marker and fall through to ordinary classification of
    whatever is actually on disk. This is the safe direction in both
    sub-cases: an already-finished mirror lands on case 2 (no-op); a
    genuinely stale target means blindly resuming toward a no-longer-current
    release would be wrong, so it is not attempted.
  - marker absent → ordinary classification, unchanged from before this
    phase.

A crash at any point — before the marker write, during it, during
`_mirror_bundled`, or during marker cleanup — is safe by construction:
either the marker was never written (nothing to resume; identical to
pre-fix behavior for that call) or it was fully written (next call resumes).
No `try`/`except`/`finally` around the risky section is needed, because the
marker's mere on-disk presence is the recovery signal, independent of *how*
the interruption happened (`OSError`, `SIGKILL`, power loss all look
identical to the next launch).

### B.5 Implementation gate — verified against Section 5's checklist

| Requirement | Met | Evidence |
|---|---|---|
| Preserve successful-path observable behavior | Yes | `_mirror_bundled` itself is unchanged; the marker is written and deleted around it and is invisible to every existing assertion. All 25 pre-existing tests in `test_v5_alpha1_phase_e_starter_refresh.py`, plus the full pinned-digest gate (`test_current_bundled_content_matches_its_pinned_digest`), pass unmodified. |
| Avoid partial collections | Yes, on resume | Resume re-invokes the same idempotent `_mirror_bundled`, landing on the identical fully-refreshed content a single uninterrupted call would have produced. |
| Avoid discovery of staging artifacts | Yes | Marker lives at `<data_root>/.starter_refresh_state/`, never under `<data_root>/agents/`; `discover_agents()` structurally cannot see it (B.2, invariant 3). Verified by a dedicated test, not just by inspection (below). |
| Defined recovery behavior | Yes | Deterministic: same-target marker → resume; stale marker → discard and classify normally. No ambiguous state. |
| Reliable on supported platforms | Yes | Only relies on single-file `Path.replace`, atomic on both Windows and POSIX. |
| Testable without timing luck | Yes | All new tests simulate interruption deterministically (a targeted `monkeypatch` failure on one named file, or directly constructing the marker+hybrid state) rather than racing a real process kill. |

**Implemented — not deferred.**

### B.6 Tests added

`engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` (all under a new
"FIND-03 ... interrupted-refresh recovery" section):

1. `test_write_failure_mid_mirror_records_a_marker_and_resumes_on_retry` —
   makes exactly one file's write (`agent.yaml`, which sorts after
   `agent.py`) raise `OSError` on its first attempt; asserts the marker
   survives, the hybrid on-disk digest matches neither the superseded nor
   current allowlist entry, and a second `ensure_starter_agents()` call
   resumes cleanly, clears the marker, and lands on the exact pinned current
   digest with the Phase D parameter schema present.
2. `test_interruption_before_any_file_write_still_resumes_cleanly` — writes
   the marker directly (simulating a kill in the gap between the marker
   write and the first file write, before anything else changed) and
   confirms resume from that earliest possible interruption point.
3. `test_stale_marker_from_a_since_superseded_bundled_release_is_discarded` —
   writes a marker whose `target_digest` does not match any real bundled
   digest (simulating a product upgrade between interruption and next
   launch) and confirms it is discarded, with the starter still correctly
   refreshed via ordinary classification.
4. `test_refresh_state_directory_is_never_visible_to_agent_discovery` —
   interrupts the mirror for `v5_dual_team` (deliberately the *last* name in
   `STARTER_AGENT_NAMES`, so every other starter has already been installed
   by the time the simulated failure fires, keeping the catalog-completeness
   assertion meaningful) and confirms `discover_agents()` still returns
   exactly the full starter set with no marker-shaped entry.

**Focused validation:**
`pytest engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` —
**29 passed** (25 pre-existing/Phase-2 + 4 new). Also re-run:
`pytest engine/tests/test_starter_agents.py engine/tests/test_v5_starter_agents.py engine/tests/test_default_python_agents.py engine/tests/test_cli_agent_listing.py engine/tests/test_agent_scaffold.py`
— **164 passed**, zero failures, confirming no adjacent agent-catalog
behavior shifted.

Bundled starter content was not changed (`CURRENT_STARTER_DIGESTS` values
unmodified and re-verified via the full suite's pinned-digest test).

---

## C. Installer `logs/` analysis

### C.1 Lifecycle, traced completely

- **What creates `logs/` (pre-fix):** only `tools/installer.iss`'s `[Dirs]`
  section, unconditionally, on every install.
- **What writes into it (pre-fix):** exactly one consumer, found by tracing
  every reference, not assuming Phase 2's finding: `tools/smoke_after_install.ps1`.
  - `$Global:LogFile = Join-Path $DataRoot "logs\installer-smoke.log"` —
    every `Write-SmokeLog` call appends here (and `Write-SmokeLog` itself
    already did `New-Item -ItemType Directory -Force` on the parent before
    this phase, meaning the script was already capable of creating its own
    log directory regardless of the installer).
  - `$StructureLog = Join-Path $DataRoot "logs\installed-files.txt"` — the
    post-install file listing `Invoke-InstalledSmoke` writes.
  - `Invoke-InstalledSmoke` also **asserted** `logs/`'s mere existence as one
    of three installer-created writable directories
    (`agents`, `logs`, `runs\_loose`) — this is a check that the *installer*
    creates it, a second, independent form of coupling beyond just writing
    diagnostics there.
- **What reads from it:** nothing found anywhere in the tracked tree (a
  release engineer reading the log by hand afterward is the only
  "consumer," which does not constrain where the file must live).
- **When the smoke script executes:** only when a developer/release engineer
  runs it by hand. Confirmed by a repository-wide grep: no `.github/workflows/*.yml`
  references `smoke_after_install.ps1` at all — it is not part of CI, and is
  never run by, or shipped to, end users. Referenced only from
  `docs/MANUAL_SMOKE_TESTS.md`'s "Windows packaging and installation"
  section (developer/release-checklist documentation) and
  `docs/ROADMAP.md`.
- **Runtime application logging:** **does not exist as a concept in this
  product.** A repository-wide search for `logging.basicConfig`,
  `logging.FileHandler`, or any persistent log-file writer in
  `engine/src`, `app/`, or `client/src` found none. Bytefray writes only to
  stdout/stderr and to explicit user-requested output paths (`--replay`,
  `--trace`, `--out`); there has never been a "runtime application log
  file" for `logs/` to serve. This resolves the "separate runtime logging
  from qualification diagnostics" question cleanly: there is no runtime
  logging half to conflate with.
- **Uninstall behavior:** Inno Setup `[Dirs]` entries are additive on
  install and are never removed on uninstall unless separately flagged
  (neither `agents`, `logs` [pre-fix], nor `runs\_loose` was); removing the
  `[Dirs]` line does not retroactively touch any existing installation.
- **Failed-install reliance:** none found — a failed install does not read
  or depend on a pre-existing `logs/` diagnostic file.
- **Documentation:** `INSTALL.md:23` says uninstall "preserves user-created
  agents, replays, summaries, logs, and other data" — read in full context
  (re-verified, not assumed from Phase 2's text) this is generic category
  prose about what kind of data survives uninstall, not a claim that a
  literal `logs/` directory is written by the product. No documentation
  correction was needed.

### C.2 Disposition

Runtime application logging and installer/qualification diagnostics are
**not two things to separate here** — only the second exists. The
diagnostic's lifecycle (exists only for the duration of a release engineer's
own validation run) never matched the lifecycle of a permanent, per-install
`ProgramData` directory created for every end user. Per Section 7's
guidance, the process temporary directory is the best-matched destination
(short-lived, cleaned by the OS, requires no product directory at all), with
a caller override for a CI/artifact-directory use case that does not exist
today but costs nothing to support.

### C.3 Changes made

- **`tools/smoke_after_install.ps1`:**
  - Added a `-LogDir` parameter; defaults to
    `[IO.Path]::GetTempPath() + "bytefray-installer-smoke"` when omitted.
  - `$Global:LogFile` and `$StructureLog` now live under `$LogDir`, not
    `$DataRoot\logs`.
  - Removed `"logs"` from `Invoke-InstalledSmoke`'s installer-created
    writable-directory existence check (mirrors exactly how `"replays"` was
    removed from the same list in Phase 2).
  - Added a `Write-SmokeLog "Diagnostics directory: $LogDir"` line near
    startup so the (now less obvious) location is always visible in the
    script's own console/log output.
  - Header comment updated to explain the split between product runtime
    logging (none exists) and this script's own qualification diagnostics.
- **`tools/installer.iss`:** removed
  `Name: "{code:GetDataRoot}\logs"` from `[Dirs]`; extended the existing
  comment block (which already explained the Phase 2 `replays` removal) to
  explain the `logs` removal identically.

### C.4 Verification

- `pytest engine/tests/test_windows_packaging_spec.py engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py`
  — **38 passed** (neither file asserts `[Dirs]` contents beyond version
  strings; confirmed by inspection before changing anything, then confirmed
  by the unchanged pass count after).
  `test_version_transition_5_0_0a1` (the only test reading
  `INSTALLER_SCRIPT`'s content) is unaffected — it checks only the
  `AppVersion` line.
- PowerShell tokenizer syntax-check of the modified `smoke_after_install.ps1`:
  zero errors (`[System.Management.Automation.PSParser]::Tokenize`).
- Full Section E build (below) compiles the modified `installer.iss`
  successfully, and the frozen-executable-level qualification confirms no
  product behavior depends on `logs/`.

No product runtime logging was redirected (none exists to redirect).

---

## D. `build_engine_command`

### D.1 Reference analysis

`app/services/engine_commands.py:50`. Searched: production imports,
direct calls, re-exports, tests, test-only monkeypatch references,
dynamic/string references, CLI paths, Designer paths, packaging, docs/specs,
historical compatibility use.

- **Production callers:** zero. A full-repository grep for
  `build_engine_command` and `from app.services.engine_commands import` found
  no caller outside `app/services/engine_commands.py` itself (the
  definition) and test files. Its only historical production caller,
  `EngineRunner._build_engine_cmd` (`app/services/engine.py`), was removed in
  Phase 2 after two independent full-repository greps confirmed
  `EngineRunner` itself had zero instantiations anywhere.
- **Test callers — substantial, direct, and load-bearing as tests:**
  - `engine/tests/test_launchers.py` — 1 call, asserting exact generated
    argument shape (`command[:4] == [str(python), "-m", "battle_engine", "run"]`).
  - `engine/tests/test_v2_default_placement.py` — 3 calls, asserting Agent
    API v2 default-placement argument omission.
  - `engine/tests/test_designer_third_entrant_command.py` — 9 calls. This
    file's own module docstring is explicit about what it is: a regression
    test for a real (if latent, since nothing in production called the
    function at the time) defect in third-entrant handling, and two of its
    tests (`test_designer_default_v2_configuration_produces_a_real_match`
    and the third-entrant equivalent) go further than argument-shape
    assertions — they call `build_engine_command`, then actually
    `subprocess.run` the resulting command against the real `battle_engine`
    CLI and assert on the produced result artifact. This is a genuine
    end-to-end proof that `RunConfig → build_engine_command → real CLI
    argument parsing → real match execution` still works as a unit, entirely
    independent of whether any GUI code currently exercises that path.
- **Re-exports:** none — `build_engine_command` was one of three names
  `app/services/engine.py` used to import from `engine_commands.py`
  (alongside `RunConfig` and `open_pygame_client_direct`); Phase 2 already
  removed that particular import when it removed `EngineRunner`, since
  `build_engine_command` had no other consumer inside `engine.py`.
  `RunConfig` and `open_pygame_client_direct` remain re-exported (and are
  live, used by `app/agent_designer.py`, `app/views/simple.py`,
  `app/views/advanced.py`) — unrelated to this question and untouched.
- **Dynamic/string references, CLI paths, Designer paths, packaging:** none
  found. The live Designer match-launch path is entirely
  `app/agent_designer.py`'s own `QProcess`-based
  `build_designer_match_arguments`, which independently constructs its own
  command list and does not call `build_engine_command` at all (confirmed by
  Phase 1/2 and re-confirmed here).
- **Docs/specs:** `docs/specs/agent_designer_workflow.md` §2.9/§28 already
  documents `build_engine_command` as reachable only through the
  now-removed `EngineRunner`, consistent with this analysis; no correction
  needed (it is a historical spec document, not a claim about current
  liveness).
- **Relationship to `EngineRunner`:** `build_engine_command` was
  `EngineRunner`'s only in-repo *production* caller before Phase 2 removed
  the class. Its removal is what makes `build_engine_command` have zero
  production callers today — but, per the instruction not to infer
  deadness merely from `EngineRunner`'s removal, this phase independently
  verified the *test* relationship separately, which is what changes the
  conclusion from "dead" to "live test infrastructure."

### D.2 Disposition — RETAIN

**Classification: live test/helper code, not dead code.** It has zero
production consumers, but it is not "completely dead" or "partially dead" —
it is a GUI-independent, directly-unit-tested command-construction contract
that three test files, including one whose entire purpose is testing it,
depend on for real assertions (including one real subprocess execution
end-to-end proof). Removing it would require also rewriting or deleting
those tests, destroying real regression coverage of argument-construction
logic that mirrors (and has previously caught defects relative to) the
live `app/agent_designer.py` path, for the sole benefit of deleting roughly
44 lines. Per the phase's own removal gate ("If it has zero legitimate
consumers, remove it... If it remains live or ambiguous, retain it"): its
test consumers are legitimate, so it is retained.

**No code was removed. No test was changed.** This section is analysis
only, per the instruction that ambiguous/live code must be retained rather
than mechanically removed merely because production usage reached zero.

---

## E. Installer build

### E.1 Command

```
pwsh tools/build_win.ps1
```
followed by
```
& "C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe" tools\installer.iss
```
(run via PowerShell directly; the equivalent Git-Bash invocation failed with
Inno Setup's generic "The system cannot find the file specified" — an
invocation/path-translation issue, not a source or Inno Setup script defect,
diagnosed and worked around rather than touching `installer.iss`).

### E.2 Environment

| Item | Value |
|---|---|
| Host OS | Windows 11 Pro, build `10.0.26120` |
| Shell | PowerShell `7.6.6` |
| Python | `3.13.14` (`.venv\Scripts\python.exe`) |
| PyInstaller | `6.22.2` |
| PySide6 | `6.11.2` |
| pygame-ce | `2.5.8` |
| Inno Setup compiler | `6.7.3` (`ISCC.exe`, per-user install at `%LOCALAPPDATA%\Programs\Inno Setup 6`) |
| Source state | HEAD `9a95e81` + this phase's uncommitted working-tree diff (Section A) |

### E.3 Result

**Both steps succeeded.**

`tools/build_win.ps1`: built all four onedir artifacts
(`bytefray`, `bytefray-cli`, `bytefray-agent-designer`, `bytefray-replay-viewer`),
passed its own bytecode/cache debris sweep across all four dist trees
("Frozen payloads contain no Python bytecode/cache"), passed its own GUI
import/startup smoke (`bytefray.exe design` and the standalone
`bytefray-agent-designer.exe`, both isolated to a throwaway `BYTEFRAY_ROOT`),
passed its own `agents create`/`agents validate` smoke across all four
(api-version, template) combinations, and confirmed zero runtime-generated
`agents/` residue under any of the four dist trees. Exit code `0`.

`ISCC.exe tools\installer.iss`: "Successful compile (46.438 sec)."

### E.4 Artifact details

| Item | Value |
|---|---|
| Generated artifact | `dist\installer\Bytefray-Setup-5.0.0a1.exe` |
| Size | 97,898,637 bytes (≈93.4 MiB) |
| SHA-256 | `646aea05f3fd7c7ec1a83e1d4a01362765e458d93adeaf1bfeda4bc1bf7d38c7` |

| Dist tree | Size | File count |
|---|---|---|
| `dist\windows\bytefray` | 128 MB | 286 |
| `dist\windows\bytefray-cli` | 18 MB | 65 |
| `dist\windows\bytefray-agent-designer` | 128 MB | 284 |
| `dist\windows\bytefray-replay-viewer` | 34 MB | 89 |

This build includes Phase 2's packaging changes, specifically verified:
the GUI-spec asset narrowing (FIND-06) — see Section F.

---

## F. Installation filesystem inspection

**Important scope limitation, stated plainly per this repository's
qualification-tier-honesty discipline:** the real Inno Setup installer was
**not run** in this phase (Section I) — this section is a **predicted-layout
cross-reference** (installer source declarations checked against the actual
built `dist\windows` trees the installer packages verbatim) and **direct
execution of the real frozen executables** from `dist\windows` outside the
installer (Section H), not an inspection of files actually placed by
`Setup.exe` under `%ProgramFiles%`/`%ProgramData%`. It is real evidence about
what the installer *would* place and about whether the packaged binaries
*work*, but it is not a substitute for running the installer itself.

| Check | Result |
|---|---|
| Expected application files/executables (`[Files]` sources) | All four `<name>\<name>.exe` present in their respective `dist\windows\<name>` trees, matching every `Source:` line in `installer.iss`'s `[Files]` section. |
| No obsolete `replays\` directory created | Confirmed by source: `[Dirs]` has no `\replays` entry (removed Phase 2, re-verified present-as-removed this phase). |
| `logs\` behavior matches this phase's disposition | Confirmed by source: `[Dirs]` has no `\logs` entry (Section C). |
| Branding/icon assets required at runtime exist | `assets/branding/bytefray-icon.png` present in all three GUI-capable dist trees (`bytefray`, `bytefray-agent-designer`, `bytefray-replay-viewer`) at the exact path `get_branding_icon_path()` checks first. `SetupIconFile=..\assets\branding\bytefray-icon.ico` (repo-root source, unrelated to the frozen `.png` runtime lookup) exists and was used by the successful compile. |
| No full obsolete `assets\` tree bundled unintentionally | Confirmed: `find dist\windows -iname "*brand-sheet*"` returned zero matches in any of the four dist trees — the 1.16 MB marketing brand sheet FIND-06 flagged is not present anywhere in the frozen payload (Section E.3/Section F above). |
| Starter content present and valid | All 21 `STARTER_AGENT_NAMES` entries present as directories under `bytefray\_internal\battle_engine\data\starter_agents\` (and identically under the other three trees' shared resource layout); confirmed populated at runtime via the frozen CLI's `--list-agents` (Section H). |
| No build debris or cache directories shipped | `find dist/windows -iname "__pycache__" -o -iname "*.pyc" -o -iname "*.pyo"` — zero matches across all four trees, independently re-run in this phase (not only trusting `build_win.ps1`'s own internal check). |
| Version metadata correct | `AppVersion "5.0.0a1"` (`installer.iss`) matches `pyproject.toml`'s `version = "5.0.0a1"` and the frozen `bytefray.exe --version` output (`Bytefray 5.0.0a1, ...`) — three independent sources agree. |

**Not performed:** inspection of files actually placed under a real
`{app}`/`{code:GetDataRoot}` by a real `Setup.exe` run, the `[Registry]`
`BYTEFRAY_ROOT` write, and real Start Menu shortcut creation. See Section I.

---

## G. Post-install smoke

**Not performed as literally specified** (Section 13 assumes a real
installed copy). `smoke_after_install.ps1`'s non-`-Lifecycle` mode
(`Invoke-InstalledSmoke`) requires an already-installed application at
`$AppDir`/`$DataRoot`, which does not exist without the install this phase
did not run (Section I).

**Performed instead, as the strongest available substitute** (Section H):
direct execution of the real frozen executables from `dist\windows`,
covering everything `Invoke-InstalledSmoke` would check *except* the
installer-specific assertions (Start Menu shortcuts, `[Registry]` write,
installer-created directory existence).

**Diagnostics path:** not exercised in this phase (the diagnostic write only
happens inside `Invoke-InstalledSmoke`/`Write-SmokeLog`, which was not
invoked), but the relocation itself (Section C.3) was verified independently:
`$LogDir` resolves and is created correctly by the same
`New-Item -ItemType Directory -Force` pattern already proven correct by
every prior use of `Write-SmokeLog` in this script's history; no new
mechanism was introduced, only a new default path.

---

## H. Installed CLI/GUI/match qualification

Performed against the real frozen executables in `dist\windows` directly
(not through the installer — see Section I for why), each in an isolated
throwaway `BYTEFRAY_ROOT` so nothing touched a real data root:

| Check | Command | Result |
|---|---|---|
| Version | `bytefray.exe --version` | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14` — exit `0`, matches source/installer version exactly. |
| Starter-agent availability | `bytefray-cli.exe --list-agents` | Exit `0`; all 21 starters discovered and materialized under the isolated `agents\` directory (full name list recorded and cross-checked against `STARTER_AGENT_NAMES`). This is FIND-03's `ensure_starter_agents()` path exercised for real, on the frozen executable, from a clean data root — the "absent → install" case. |
| Real match execution | `bytefray-cli.exe --ticks 200 --arena 128 --a-type seeker --b-type writer --b-start 64 --replay <path> --quiet` | Exit `0`; replay file produced, 4,566 bytes. |
| Replay Viewer startup/help | `bytefray-replay-viewer.exe --help` | Exit `0`; correct `bytefray replay` usage text. |
| Designer startup (GUI) | `bytefray-agent-designer.exe` (standalone) and `bytefray.exe design` (unified dispatcher), both via `tools/build_win.ps1`'s own internal smoke, isolated `BYTEFRAY_ROOT`, `BYTEFRAY_GUI_SMOKE_EXIT_MS=750` | Both exit `0` (the script throws and fails the whole build otherwise); confirms Designer startup does not depend on the full repo-root `assets\` tree (only `assets\branding\` is bundled per FIND-06) and that starter bootstrap does not error on frozen GUI startup either. |
| Missing-packaged-resource errors | (all of the above) | None observed. |

**Not performed:** launching Start Menu shortcuts, observing real windows as
a human, or anything through the Inno Setup–installed copy specifically —
this is "packaged qualification" (the frozen artifact runs correctly) but
not "interactive first-user qualification" (per this repository's
established three-tier qualification distinction) and not "the installer's
own lifecycle" (Section I).

---

## I. Installer install/uninstall lifecycle qualification — explicitly gated, not performed

`tools/installer.iss`'s `[Setup]` section declares `PrivilegesRequired=admin`
for every install this installer produces, regardless of `-AppDir`/`-DataRoot`
target — this is a property of the compiled installer, not of
`smoke_after_install.ps1`'s own choices. Its `-Lifecycle` mode additionally
writes an `HKLM` machine environment variable
(`SYSTEM\CurrentControlSet\Control\Session Manager\Environment\BYTEFRAY_ROOT`)
and creates the common (`{group}`) Start Menu group, both genuinely
machine-wide, shared-system-state changes — not confined to whatever
custom `-AppDir`/`-DataRoot` path is supplied.

This session's PowerShell is confirmed **not** running elevated
(`[Security.Principal.WindowsPrincipal]... IsInRole(Administrator)` →
`False`). Given the registry/shared-system-state nature of any real install
of this specific installer, the user was asked explicitly how to proceed
(a) skip and document the gap, (b) run it themselves in an elevated session
and hand back the output, or (c) have this session attempt to self-elevate.
**The user chose (a): skip.**

**What this means for the phase's evidence, stated in this repository's own
tier terms:**

- **Packaged qualification** (installer *compiles* from the candidate
  source, frozen executables run correctly, packaging content is correct) —
  **performed, Sections E–H.**
- **The installer's own install/upgrade/uninstall lifecycle**
  (`smoke_after_install.ps1 -Lifecycle`: real `/VERYSILENT` install,
  `[Registry]` write verification, Start Menu shortcut creation/removal,
  user-data preservation across upgrade, uninstall residue) — **not
  performed.** This is the evidence Phase 2 already flagged as required
  before Phase 2's own `replays` removal could be considered installer-cycle
  -verified (Phase 2 Section I/O); it remains outstanding after this phase
  too, now also covering this phase's `logs` removal and FIND-03 change.
- **Interactive first-user qualification** (a human clicking real installed
  shortcuts) — not performed, and not performable by a non-interactive
  session regardless of privilege, per this repository's standing
  qualification-tier distinction.

This is reported as an explicit, named gap rather than folded into a
broader "installer qualified" claim, consistent with this repository's
standing rule that a weaker tier must never be reported as a stronger one.

**Uninstall qualification (Section 16):** not performed, for the same
reason — there is no real install to uninstall.

**Reinstall/upgrade resilience (Section 17):** not performed, for the same
reason. Stated explicitly, as the prompt requires when this step is skipped.

---

## J. Source validation

### J.1 Tree stability (qualification-integrity check)

| Point | HEAD | Working-tree status | File hashes |
|---|---|---|---|
| Before the full suite | `9a95e81...` | 4 files modified (Section K) | recorded |
| After the full suite | `9a95e81...` (unchanged) | identical 4 files modified, nothing else | identical to before |

No drift occurred during the ~5.5-minute full-suite run, despite several
other interactive sessions being active on this machine at the time
(`ListAgents` showed three peer interactive sessions) — confirmed by
re-hashing, not assumed.

### J.2 Focused tests

| Suite | Result |
|---|---|
| `test_v5_alpha1_phase_e_starter_refresh.py` | **29 passed** (25 pre-existing + 4 new FIND-03 tests) |
| `test_starter_agents.py`, `test_v5_starter_agents.py`, `test_default_python_agents.py`, `test_cli_agent_listing.py`, `test_agent_scaffold.py` | **164 passed** |
| `test_windows_packaging_spec.py`, `test_v5_alpha1_phase_b_engine_hygiene.py` (installer `logs` removal) | **38 passed** |

### J.3 Determinism/equivalence

| Suite | Result | Baseline (Phase 2) | Delta explained |
|---|---|---|---|
| `pytest engine/tests -k "v5 or ruleset"` | **736 passed, 2190 deselected** | 732 passed | +4 = this phase's 4 new FIND-03 tests, which also match the `v5` keyword filter (they live in `test_v5_alpha1_phase_e_starter_refresh.py`) |
| `pytest engine/tests/test_v4_stable_ruleset_equivalence.py` (`hydra`/`nemesis`/`hydra_alpha2`/`nemesis_alpha2` tracked-fixture corpus) | **23 passed** | 23 passed | unchanged |

### J.4 Static checks

| Command | Result |
|---|---|
| `ruff check .` | `All checks passed!` |
| `mypy engine/src/battle_engine` | `Success: no issues found in 107 source files` |
| `mypy client/src/battle_client` | `Success: no issues found in 16 source files` |

### J.5 Full test suite

```
python -m pytest
3406 passed, 21 skipped, 3 deselected in 324.50s (0:05:24)
```

Phase 2's baseline was **3402 passed, 21 skipped, 3 deselected**. The **+4**
is exactly accounted for by this phase's 4 new FIND-03 tests — skip count
(21) and deselected count (3) both unchanged, confirming no test's
collection or environment-gated skip status shifted. **Zero existing test's
expected result changed; zero new failures.**

---

## K. Files changed

| File | Change | Why |
|---|---|---|
| `engine/src/battle_engine/starters.py` | Modified | FIND-03: added a resumable transition-marker mechanism (`_refresh_marker_path`/`_write_refresh_marker`/`_read_refresh_marker`/`_clear_refresh_marker`) and wired it into `ensure_starter_agents()`'s classification loop so an interrupted `_mirror_bundled` resumes instead of being permanently misclassified `CUSTOMIZED` (Section B). +121/−0 lines. `_mirror_bundled` itself is unchanged (only its docstring gained a note about the resumability property this fix relies on). |
| `engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` | Modified | Added 4 focused FIND-03 recovery tests (Section B.6) and the `battle_engine.starters` module import they need. +168/−0 lines. |
| `tools/installer.iss` | Modified | Removed the now-unused `\logs` line from `[Dirs]`; extended the existing comment explaining `\replays`'s Phase 2 removal to also explain `\logs`'s Phase 3 removal (Section C.3). +8/−1 lines. |
| `tools/smoke_after_install.ps1` | Modified | Added `-LogDir` parameter (defaults to the process temp directory); relocated `$Global:LogFile`/`$StructureLog` off `$DataRoot\logs`; removed `"logs"` from the installer-created writable-directory existence check; added a diagnostics-location log line; updated the header comment (Section C.3). +26/−4 lines. |
| `docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE3_INSTALLER_QUALIFICATION.md` | Added | This report. |

No file under `engine/src` (outside `starters.py`), `client/src`, `app/`,
`agents/` (tracked fixtures), or any replay/agent/result data file was
modified. No bundled starter content changed. No CLI/Designer argument,
default, or workflow was touched. `git diff --stat` (source files only,
excluding this report):

```
 engine/src/battle_engine/starters.py                          | 121 +++++++++++++++
 engine/tests/test_v5_alpha1_phase_e_starter_refresh.py         | 168 +++++++++++++++++++++
 tools/installer.iss                                            |   8 +-
 tools/smoke_after_install.ps1                                  |  26 +++-
 4 files changed, 318 insertions(+), 5 deletions(-)
```

`git diff --check`: clean, exit `0`. `git status --short`: exactly the four
files above modified, nothing staged, nothing else untracked/changed.

---

## L. New deferred findings

- **The installer's own elevated install/upgrade/uninstall lifecycle**
  (Section I) — needs a release engineer running
  `tools/smoke_after_install.ps1 -InstallerPath dist\installer\Bytefray-Setup-5.0.0a1.exe -AppDir ... -DataRoot ... -Lifecycle`
  from an elevated PowerShell (or an equivalent disposable environment such
  as Windows Sandbox), covering: real `[Registry]` `BYTEFRAY_ROOT` write,
  Start Menu shortcut creation/removal, user-data preservation across an
  upgrade install, and uninstall residue (including confirming no
  `.starter_refresh_state\` directory or stray marker file is left in an
  unexpected location — this phase's new FIND-03 mechanism was never
  exercised end-to-end through a real installed copy's actual launch/crash
  cycle, only through direct unit-level interruption simulation).
- **Interactive first-user qualification** — genuinely requires a human,
  unchanged from every prior phase's own statement of this limit.
- **`CHANGELOG.md` has no `[5.0.0a1]` entry** — carried forward from Phase 1,
  still unaddressed; a content/product decision, not a defect.
- **The Git-Bash/ISCC.exe invocation issue** (Section E.1) — cosmetic
  tooling friction, not a source defect; worth a one-line note in
  `docs/MANUAL_SMOKE_TESTS.md` or `tools/installer.iss`'s own header comment
  in a future documentation pass, but not attempted here to avoid unrelated
  churn.

---

## M. Behavioral-neutrality statement

**No evidence exists that gameplay, ruleset semantics, deterministic
results, replay semantics, CLI product behavior, or Designer product
behavior changed as a result of this phase.** Specifically:

- No file under `engine/src/battle_engine`'s simulation, scheduler, scoring,
  termination, deployment, mortality, territory, or Agent API modules was
  touched. The only `engine/src` file modified (`starters.py`) affects only
  the starter-*catalog refresh recovery mechanism* — a packaging/lifecycle
  concern — never match simulation, and every currently-shipped starter's
  pinned digest is unchanged and re-verified.
- No file under `client/src/battle_client` (replay schema/playback) was
  touched.
- No CLI argument, default, workflow, or ruleset choice list was touched.
- No Designer widget, view, or workflow was touched.
- The full regression suite passed with the exact same failure count (zero)
  as Phase 2's baseline, with the only count difference (+4) fully
  accounted for by this phase's own new tests.
- The strongest available determinism/equivalence suites
  (`-k "v5 or ruleset"`, `test_v4_stable_ruleset_equivalence.py`) passed with
  no new failures and the same +4 explained delta.
- A real frozen build's CLI (`bytefray-cli.exe`) produced a real match
  replay against unchanged starter agents, and `bytefray.exe --version`
  reported identical version/schema identifiers to every prior baseline.

---

## N. Recommended Phase 4 scope

Limited to release-surface/ruleset/product-exposure audit work, per this
phase's own scope boundary:

1. **Close the installer-lifecycle gap named in Section I/L** — either as
   Phase 4's first item, or as a standalone release-engineering task run
   from an elevated session (does not require "Phase 4" framing at all if
   the user prefers to run it directly).
2. **A release-surface audit**: given three maintenance phases of cleanup
   are now complete (doc/repo hygiene, technical hygiene, installer
   hygiene), review what Alpha 1 users and the published release notes
   actually describe against current HEAD, to catch any remaining
   documentation drift before considering the feedback window's next
   milestone.
3. **`CHANGELOG.md`'s missing `[5.0.0a1]` entry** (Section L) — a content
   decision appropriate for whoever owns release-notes authoring, not a code
   change.
4. Everything Phase 2's own Section O and the original Post-Release
   Hardening Audit's Section J "Suggested backlog" already carry forward
   beyond what Phases 2–3 have now resolved remains the authoritative
   backlog; this report does not duplicate or supersede either.

**Phase 4 was not begun.** This report performs no scope beyond what
Sections 1–19 of the Phase 3 brief specify.
