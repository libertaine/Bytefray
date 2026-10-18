# Bytefray Spectator export and Designer viewer dispatch

Status: implemented on the `v6-spectator-integration` development branch.
Not released, and not yet independently reviewed or human-qualified.

This spec covers how Bytefray turns a completed V6 alpha1 match into a
Bytefray Spectator presentation, and how Agent Designer opens that
presentation. Bytefray Spectator is a separate Godot application
(<https://github.com/libertaine/Bytefray-Spectator>). It plays verified
presentations and never executes agents or simulates matches.

## 1. Responsibilities

| Concern | Owner |
|---|---|
| Executing matches; replay, result and trace artifacts | Bytefray |
| Verifying those artifacts and interpreting them (outcome, sensing exchange, Agent A knowledge) | Bytefray: `battle_client.spectator_export` |
| Presentation files and their manifest | Written by Bytefray, read by Spectator |
| Visualization, playback controls, perspectives, sound | Spectator |

Spectator depends only on the versioned presentation format below, never on
Bytefray's engine internals. Bytefray never depends on Spectator code.

## 2. Supported matches

The export supports a completed match when all of these hold:

* the ruleset is `bytefray-rules-6-alpha1`;
* there are exactly two entrants, with seats `A` and `B` (Spectator's
  legend, colours and qualification cover two entrants);
* `trace.jsonl` sits beside the replay that `result.json` references.
  Designer writes it automatically for V6 alpha1.

Everything else is refused with a stable code. In Designer, refused matches
keep opening in the Pygame viewer. `spectator_support(result_path)` is the
cheap eligibility check. It reads only `result.json` and authorizes nothing.

## 3. Verification (fail closed)

`export_presentation(source, out_dir)` performs these steps in order. Any
failure raises `SpectatorExportError(code, message)`, and nothing is
installed.

1. **Replay preflight.** `battle_engine.replay_integrity.preflight_result_replay`
   runs, the same check that guards every Designer replay launch. It covers
   result containment, the replay reference, the replay SHA-256 and the replay
   header identity. A failure gives `result_unverified`.
2. **Trace.** The `trace.jsonl` sibling must exist (`trace_missing`).
3. **Source snapshot.** SHA-256 and size of `result.json`, the replay and the
   trace are recorded.
4. **Eligibility.** The ruleset and roster are checked from `result.json`
   (`unsupported_ruleset`, `unsupported_roster`).
5. **Reconstruction.** `reconstruct_sensing_playback(replay, trace, result_path=…)`
   verifies the trace binding footer (replay digest, match_id, entrants) and the
   result association, and independently rebuilds every sub-tick exchange fact.
   It reconciles them with every replay tick snapshot (`evidence_unverified`).
6. **Outcome.** The winner and termination reason are re-derived from the
   reconstructed final world under the engine's rule (`process_runtime`), then
   compared with the replay's terminal record and with `result.json`. Ticks,
   tick limit, identity, score and alive flags must all agree
   (`outcome_verified`).
7. **Projection.** The broadcast view comes from `SensingCursor(entrant_id=None)`,
   one frame per verified fact. Each TICK_END step re-checks the canonical
   replay boundary. Agent A comes *only* from the receipt-only `SensingView`
   objects of `SensingCursor(entrant_id="A")`. Every key in `agent_a.json` must
   be on an explicit allowlist (`agent_view_leak`). Broadcast data is never
   used to build Agent A's view.
8. **Sources unchanged.** The three sources are re-hashed and must equal the
   snapshot from step 3 (`source_changed`).
9. **Install.** The files are written to a staging directory beside the output
   and renamed into place only when complete (`output_failed`).

The exporter never runs agent code. It never writes to the match directory,
and it refuses an output directory that is or contains the match directory
(`output_unsafe`). An existing output directory is replaced only on request
(`--replace`), and only if it holds nothing but a presentation.

## 4. Presentation format

A presentation directory holds three files, all canonical JSON: sorted keys,
no whitespace, ASCII, LF ending.

* `broadcast.json` — `schema: "bytefray.spectator.broadcast"`, `schema_version: 1`.
* `agent_a.json` — `schema: "bytefray.spectator.agent_view"`, `schema_version: 1`.
* `manifest.json` — `schema: "bytefray.spectator.manifest"`, **`schema_version: 2`**.

The broadcast and agent documents use exactly the version-1 shape that
Spectator's pinned prototype exporter writes. The production exporter
reproduces the frozen showcase's `broadcast.json` and `agent_a.json` byte for
byte from the same source artifacts.

Manifest version 2:

```json
{
  "schema": "bytefray.spectator.manifest",
  "schema_version": 2,
  "exporter": {"name": "battle_client.spectator_export", "version": 1},
  "bytefray": {"version": "5.0.0", "packages": ["battle_engine", "battle_client"],
               "files": 126, "packages_sha256": "<sha256 over the package sources>"},
  "match": {"match_id": "…", "result_id": "…", "ruleset_id": "bytefray-rules-6-alpha1",
            "arena_size": 512, "seed": 1, "tick_limit": 120, "ticks": 120,
            "termination_reason": "tick_limit", "winner": "tie",
            "entrants": [["A", "…"], ["B", "…"]], "product_version": "5.0.0"},
  "sources": {"result.json": {"sha256": "…", "bytes": 0},
              "replay.jsonl": {"sha256": "…", "bytes": 0},
              "trace.jsonl": {"sha256": "…", "bytes": 0}},
  "verification": {"provenance": "bytefray_match", "result_replay_preflight": true,
                   "artifact_pair_consistent": true, "exchange_reconstructed": true,
                   "outcome_verified": true, "sources_unchanged": true,
                   "tick_end_boundaries_checked": 121, "agent_view_allowlist_checked": true},
  "presentation": {"broadcast": {"path": "broadcast.json", "schema": "…", "schema_version": 1,
                                 "sha256": "…", "bytes": 0, "frames": 0},
                   "agent_a": {"…": "same fields"}}
}
```

**Provenance.** `bytefray_match` means the provenance is the canonical result
envelope itself. Nothing is invented after the fact: `result.json` binds the
replay by digest, the trace footer binds the same replay, and both bindings
are verified above. `bytefray` identifies the *exporting* Bytefray: its
version, plus a SHA-256 over the `battle_engine` and `battle_client` sources it
ran. That digest is `null` in a frozen build. `match.product_version` is the
version recorded by the Bytefray that *played* the match.

**Versioning.** Manifest version 1 remains the frozen contract of Spectator's
pinned prototype exporter: provenance `teaching_demo` or `showcase_match`,
bound to a pinned Bytefray commit. Spectator accepts versions 1 and 2, each
with its own required fields, and rejects any other version. A change to the
shape of either document requires a new document `schema_version`. A change
to manifest meaning requires a new manifest version.

**What the digests prove.** Spectator rejects any presentation whose files
disagree with their manifest. That check detects corruption and inconsistency.
It does not authenticate against someone replacing the files and the manifest
together.

## 5. Command line

```text
bytefray spectator export  --source <match dir | result.json> --out <dir> [--replace]
bytefray spectator prepare --source <match dir | result.json> [--cache <dir>]
bytefray spectator verify  --presentation <dir> [--source <match dir>]
```

`prepare` is the Designer entry point. It prints one JSON line per stage
(`{"status": "progress", "stage": …}`), then a final
`{"status": "ok", "presentation": …, "reused": …}` or
`{"status": "error", "code": …, "message": …}`. It exits 0 or 1.

## 6. Designer presentation cache

Designer's presentations live at
`<data root>/cache/spectator/presentations/<match_id>-<digest>/`, where the
digest covers the source digests and the exporter identity. The cache is
outside `runs/`, so Replay History never indexes it. Concurrent exports stage
separately; the first complete one is installed and the others reuse it.

A cached presentation is reused only when all of these hold:

* the replay preflight passes again;
* its manifest names exactly the current source digests;
* its files match its manifest;
* it was written by the current exporter build.

Otherwise it is discarded and exported again. The cache keeps at most 16
presentations, and abandoned staging directories are removed after an hour.
Deleting the cache loses nothing.

## 7. Designer viewer dispatch

View Last Match, the Agent Development test replay and evaluation replays all
go through `AgentDesigner._open_result_replay`:

1. The existing replay preflight runs and stays authoritative. On failure the
   existing warning is shown and nothing opens.
2. If Spectator is available (§8) and the match is supported (§2),
   `SpectatorLaunchController` runs `bytefray spectator prepare` in a
   `QProcess`, never on the GUI thread. Designer stays responsive and reports
   progress in its log.
3. On success, Spectator starts as an independent process with an argument
   list (no shell), its standard streams discarded, in a new process group or
   session:
   `<spectator> -- --fixture=<presentation> --perspective=broadcast`.
   In development mode the command is
   `<godot> --path <project> -- --fixture=<presentation> --perspective=broadcast`.
   An exit within 2.5 s with a nonzero code is reported.
4. If export or launch fails, a warning names the reason. The Pygame viewer
   then opens, after a **fresh** preflight.
5. Unsupported matches, and every match when Spectator is absent or off, open
   in the Pygame viewer exactly as before.

When a Simple or Advanced match completes, Designer prepares its presentation
quietly in the background. A View Last Match click while that runs simply
waits for it. Development-test and historical targets keep their existing
separation: preparation never changes which match a button opens. Tournament
and Replay History launches are unchanged and use the Pygame viewer.

## 8. Finding Spectator

Spectator is found in this order, and no other location is guessed:

1. `BYTEFRAY_SPECTATOR`, which can be any of:
   * an exported Spectator executable;
   * a folder containing one (`bytefray-spectator.exe` on Windows;
     `bytefray-spectator.x86_64` or `bytefray-spectator` on Linux);
   * a Spectator project folder (`project.godot`). This also needs
     `BYTEFRAY_GODOT` or `GODOT` naming the Godot 4.7.2 executable.

   The values `off`, `pygame`, `none`, `0` and `false` turn Spectator off.
   A value that names nothing usable is reported once per session and logged
   on each use.
2. `<data root>/spectator/` holding an exported executable (a portable
   unpack).
3. `bytefray-spectator` on `PATH`.

## 9. Tests

* `client/tests/test_spectator_export.py`: export contract, chronology against
  the trace, decisive and tie outcomes, determinism, differential Agent A
  isolation, tampering and missing files, unsupported rulesets and rosters,
  output safety, verification, cache reuse, concurrency and pruning, CLI.
* `engine/tests/test_spectator_viewer_service.py`: discovery, command
  construction (spaces, no shell), prepare-output parsing, launch options.
* `tests/test_agent_designer_spectator.py` (`gui`): View Last Match with the
  real prepare process; unsupported and unconfigured fallbacks; failed export,
  then fallback after a fresh preflight; a changed replay refused before
  either viewer; misconfiguration.
* Spectator's `exporter/tests/test_production_presentations.py` runs with
  `BYTEFRAY_PRODUCTION_ROOT` pointing at this checkout. It covers byte
  identity with the frozen showcase, and a fresh Bytefray match exported and
  played in Spectator, compared against the trace and result.

## 10. Known limitations

* Export cost is dominated by `SensingCursor.current_view`, which rebuilds the
  entrant view from the start on every step. That makes export quadratic in
  match length: about 1–3 s for short matches, and 50–140 s for 600-tick
  matches measured on the development machine. Background preparation on
  match completion hides much of this. The authoritative projection was
  deliberately left unchanged.
* `SensingCursor` refuses evidence under paths whose components are named
  `research`, `research_*`, `e8_*`, `e9_*` or `.pytest_e9_*`. Matches stored
  under such folders cannot be exported.
* Only Agent A has a delivered-knowledge perspective. Only two-entrant matches
  are supported.
