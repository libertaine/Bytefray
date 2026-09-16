# Bytefray V5 — Phase 5: Replay History Discovery

**Status:** Discovery/architecture only. Read-only investigation. No production,
test, packaging, gameplay, agent, replay-schema, replay-writer, replay-loader,
Replay Viewer, CLI, or Designer file was modified. The only file this phase
adds is this report. A temporary, read-only measurement script was used
against the real local `runs/` corpus (Section L) and deleted after use; it
was never staged or committed.

---

## A. Starting state

| Item | Value |
|---|---|
| Branch | `v5-research` |
| HEAD SHA | `ce23af74b2f52099792570700b7b9ed8a2c5ae69` |
| Upstream/tracking branch | `origin/v5-research`, exactly up to date (`0`/`0` ahead/behind) |
| Working tree at start | **Not clean** — see below |
| Bytefray version | `5.0.0a1` (`pyproject.toml`); `bytefray --version` last verified (Phase 0) as `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14` |

### Pre-existing uncommitted Phase 4 work — preserved, not touched

The working tree at the start of this phase already carried **uncommitted
documentation changes from Phase 4** (`V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md`),
left uncommitted at the end of that phase's own session:

```text
 M CHANGELOG.md
 M README.md
 M docs/AGENT_AUTHORING.md
 M docs/AGENT_LAB.md
 M docs/COMPATIBILITY.md
 M docs/V5_STARTER_AGENTS.md
?? docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md
```

This is exactly the "Final `git status --short`" the Phase 4 report itself
records, six modified Markdown files (+104/−15 lines total) and one untracked
report — confirmed by diffing each file against HEAD and finding only the
prose changes Phase 4's own "Section L: Current documentation corrections"
and "Section K: CHANGELOG.md" describe (a new `[5.0.0a1]` changelog entry,
ruleset-terminology corrections in README/AGENT_AUTHORING/AGENT_LAB/
COMPATIBILITY, and a command-name fix in V5_STARTER_AGENTS.md). None of these
six files is executable source, a test, a schema, a manifest, or a packaging
input. **Phase 5 leaves this working-tree state completely untouched** — it
is Phase 4's own deliverable, not Phase 5's to commit, discard, or fold in.
Phase 5's own new file (this report) is the only addition this phase makes.

### Confirming Phase 4 is present

Phase 4's own report records its HEAD as this exact SHA (`ce23af7...`) and
states Phase 3 ("harden starter refresh and installer hygiene") was already
committed as that same HEAD. Phase 4's work itself is the uncommitted
documentation diff described above — i.e. "Phase 4 is present" as an
uncommitted-but-completed deliverable sitting on top of a committed Phase 3
HEAD, not as its own commit. This matches `git log`'s five most recent
commits (`ce23af7`, `9a95e81`, `7ee0e2f`, `562fd96`, `198a94e`) with nothing
newer.

### Relationship to the published Alpha 1 artifact

As Phase 0 established and Phase 4 reconfirmed, current HEAD is not the
published `b5.0.0-alpha1` tag (`28a10b8`); it is 10+ commits ahead, including
two post-publication behavior changes (`e67787e`, parameter-consistency fix;
`0d94d6a`, Replay Viewer capture-presentation change) that are already
qualified and out of this phase's scope to revisit.

---

## B. Current replay lifecycle (end to end)

```
Match configuration
  CLI args (bytefray run / tournament / agents test / agents evaluate)
  or Designer form (Simple/Advanced/Development/Evaluation)
        │
        ▼  builds MatchRequest (entrants, Config: seed/arena/ticks/weights,
        │  resolved or explicit ruleset_id, resolved Agent Params)
Match execution
  NativeMatchService.run() dispatches to:
    - VM Kernel (bytefray-rules-1 VM/blob entrants), or
    - Python runtime, single-actor or process/v4 (bytefray-rules-1/2/3*/4*),
    - or, for --mode redcode94, an entirely separate pMARS/Redcode backend
      that produces NO battle2.replay artifact at all (see Section C)
        │
        ▼  live per-tick capture: telemetry.py's raw v0.1-shaped JSONLSink
        │  writes an unfinished/raw replay to a private/source temp path
        │  during execution (match_service.py's _run_python_match/_run_vm_match)
Result/replay construction (finalization)
  match_service._finalize_native_artifacts:
    - canonical_match_id(request) — a pure SHA-256 content hash over
      {mode, ruleset_id, reproducibility, entrant identities/content-digests};
      NEVER a random UUID and NEVER includes a timestamp or filesystem path
    - re-reads the raw capture via iter_replay (adapting any v0.1 shape)
    - builds typed ReplayHeader / TickSnapshot / MatchResult records, with
      replay_id = match_id = the SAME value embedded on result_id's
      dependency chain (see Section P — these are not three independent IDs)
    - schema_version 4 if the resolved ruleset is a process ruleset
      (bytefray-rules-4/-4-alpha1/-4-alpha2), else 3
        │
        ▼
Serialization
  write_replay() → serialize_record() per record, sorted-key JSON, one
  record per line (JSONL), written to a NEW tempfile.mkstemp() file, then
  atomically Path.replace()'d onto the final destination; the original raw
  capture is deleted. A sibling result.json is written atomically
  (write_json_atomic, tempfile + os.replace) in the same step, referencing
  the replay by content SHA-256 digest (ReplayReference)
        │
        ▼
Filesystem destination  (see Section D for the full table)
  --replay <path>                                  (explicit, any producer)
  <data-root>/runs/_loose/replay.jsonl              (bare `bytefray run`, FIXED name)
  <data-root>/runs/_designer/<ts>-<uuid8>/          (Designer, collision-free)
  <data-root>/runs/agents_test/<agent>/<ts>-<uuid8>-vs-<opp>/  (Development test)
  <data-root>/runs/tournaments/<agents-seed>/matches/<ordinal-round-names>/
  <data-root>/runs/evaluations/<eval_id>/matches/<cell-label>/
        │
        ▼
Later discovery/opening  (see Section M — no browser/history exists today)
  User must already know the path, OR:
    - CLI: `bytefray replay --replay <path>`
    - Replay Viewer's own bespoke Pygame directory picker, seeded at
      canonical_replay_directory() (best-guess only, never a registry)
    - Designer's single in-memory "last replay" pointer / View-Last-Match
      button, else native QFileDialog
        │
        ▼
Replay Viewer loading
  ReplaySession.load(path) — ONE full linear pass through iter_replay,
  buffering every TickSnapshot into memory (O(total replay size)); no
  shortcut exists today to read only the header/terminal result without
  buffering everything in between (see Section L)
        │
        ▼
Replay interpretation
  PlaybackController/PygameRenderer step/seek on the buffered model;
  replay_status.py / analysis.py derive core status, territory, events,
  entrant statuses from the reconstructed ReplayState, honoring
  runtime_kind semantics and ruleset-family membership tables that live in
  CURRENT source, not in the replay file itself (see Section U)
```

---

## C. Replay producers

| Producer | Replay created? | Automatic/manual | Default destination | Naming rule | Metadata differences |
|---|---|---|---|---|---|
| `bytefray run` (native VM/Python) | Yes, always | Automatic, no opt-out flag exists | `<data-root>/runs/_loose/replay.jsonl` unless `--replay PATH` given (`engine/src/battle_engine/cli.py:45,89-93`, `DEFAULT_REPLAY_RELATIVE_PATH`) | **Fixed filename** — overwritten on every bare invocation | None — this is the canonical writer itself |
| `bytefray run --mode redcode94` (pMARS) | **No** — no `battle2.replay` at all | Automatic (this mode never writes one) | writes `summary.json`+`result.json` only; `result.json.replay` is `null` | Any stale `replay.jsonl`/`result.json` at the resolved path is explicitly deleted first | `ResultEnvelope.replay = None`; still schema `battle2.result` |
| `bytefray tournament` | Yes, per **completed** match only | Automatic per scheduled pairing | `<output-dir>/matches/<label>/replay.jsonl` (default output dir under `runs/tournaments/...`) | `f"{ordinal:06d}-r{round}-{safe(a)}-vs-{safe(b)}"` | Identical writer/schema to `bytefray run`; a failed/rejected match gets **no** replay |
| `bytefray agents test` (Development test) | Yes, via the same `NativeMatchService`/finalize path | Automatic | `<data-root>/runs/agents_test/<agent_id>/<ts>-<uuid8>-vs-<opponent>/` | UTC timestamp + 8-hex random + opponent name in the **directory** | Docstring: "same canonical `replay.jsonl`/`result.json`/`summary.json`" as any native match |
| `bytefray agents test` — init failure | **No** | Automatic (skipped) | N/A | N/A | CLI prints `"result: none"` / `"replay: none"` |
| `bytefray agents evaluate` (pairwise/group) | Yes, per scored cell, reusing `agent_test.test_agent`/`test_agents` verbatim | Automatic per matrix cell | `<data-root>/runs/evaluations/<evaluation_id>/matches/<cell-label>/` | Ordinal + role/subject/opponent/seed(+placement/orientation) in the directory | The additive `evaluation.json` (schema `bytefray.evaluation`) is a **separate index**; it references cells by `artifact_dir`, never inlines match data |
| `agents evaluate` cell — init failure | **No** replay for that cell | Automatic (skipped) | N/A | N/A | Cell recorded `outcome="subject_init_failed"`/`"opponent_init_failed"` in `evaluation.json`; no underlying replay |
| Designer GUI ("Run Match") | Yes, spawns `bytefray run` as a subprocess — same canonical path | Manual trigger, automatic once triggered | `<data-root>/runs/_designer/<ts>-<uuid8>/replay.jsonl` (`app/services/designer_workflows.py:341-355`, `new_match_run_directory`) | UTC timestamp + random 8-hex, **no agent names** in the directory | Also writes a sibling `trace.jsonl` automatically, but only for v4-family rulesets (`DESIGNER_AUTO_TRACE_RULESET_IDS`) |
| `evaluation_capture.py` (capture/kill analysis) | No — reads only | N/A | N/A | N/A | Reads only each cell's already-written `result.json`; explicitly "No replay reconstruction" |
| `benchmarks.py`, `reference_agents.py` | No — never run a match | N/A | N/A | N/A | Manifest/fingerprint verification and reference-resource definitions only |
| Research/tooling scripts (`tools/benchmark_platform_scaling.py`, frozen `run_sweep.py` under `runs/research_*`) | Yes, via the canonical `write_replay`/`agent_test.test_agent` path | Manual (developer-run) | Script-specific, under the data root | Sample/cell-derived label | Uses the canonical serializer, never hand-rolled JSON |
| `engine/tests/fixtures/replay/*.json` (5 files) | Synthetic, hand-authored, not producible by the current writer | Manual/static, test-only | `engine/tests/fixtures/replay/` | Static per legacy schema shape | Exercises the *reader's* backward-compatibility/error paths only |

### Answers

- **One common writer?** Yes. Exactly one low-level writer, `battle_engine.replay.write_replay`, called from exactly one place in the production pipeline, `match_service._finalize_native_artifacts`. Every production entry point (`bytefray run`, tournament, Development test, and — transitively, since it calls `agent_test.test_agent`/`test_agents` — pairwise/group Evaluation) funnels through `NativeMatchService.run()` → `_finalize_native_artifacts` → `write_replay`. No production path hand-rolls its own replay JSON.
- **Multiple replay formats/serializers?** No — one wire format (`battle2.replay`, schema version 3 or 4 selected by ruleset family) in current production output. The 0.1/0.2 "legacy" shapes exist only as reader-compatibility fixtures, never as writer output today.
- **Can a match finish without a replay?** Yes: pMARS/Redcode mode (by design, always), a Python-entrant initialization failure in Development test/Evaluation (short-circuits before finalization), and a tournament match that raises during execution (`"failed"`/`"rejected"`, no artifacts).
- **Can replay generation be disabled?** No — there is no `--no-replay` flag or equivalent anywhere in any parser for a native (VM/Python) match; it is unconditional.
- **Temporary replays?** Yes, but never purely discarded without a result: every native match writes a raw/temp capture first, then `_finalize_native_artifacts` rewrites a *second* temp file via `tempfile.mkstemp`, atomically replaces the final path, and deletes the original temp source. If any step fails before completion, the `finally` block deletes the published replay/result/summary too — a failed finalize leaves **zero** artifacts, never a stale partial one.
- **In-memory-only replays?** No genuinely in-memory-only case was found for a completed native match; the closest is the discarded raw/temp capture above, which is still a real (if short-lived) file on disk, not memory-only.
- **Filenames/timestamps/seeds/compression:** Extension is always `.jsonl` for replays, `.json` for `result.json`/`summary.json`/`evaluation.json`. No compression anywhere. The replay *filename* itself never embeds identity — identity comes from the *directory* (fixed for `_loose`; timestamp+random for `_designer`; timestamp+random+opponent-name for `agents_test`; ordinal+names(+seed) for tournaments/evaluations).

---

## D. Filesystem/storage behavior

`engine/src/battle_engine/paths.py` is the single authority for the writable
data root:

- **Resolution order** (`get_data_root`): explicit `BYTEFRAY_ROOT` env var →
  frozen-application executable directory → source-checkout root (detected
  by the fixed structural suffix `.../engine/src/battle_engine/paths.py`,
  deliberately *not* an unbounded ancestor walk, per the module's own
  documented incident where that would have been wrong) → platform default
  (`%LOCALAPPDATA%\Bytefray` on Windows, XDG data home or `~/.local/share/bytefray`
  on Linux, else CWD).
- **`canonical_replay_directory(data_root)`** is explicitly documented as
  "never raises and never creates a directory — this is a read-only 'where
  would replays already be' lookup for a file chooser's initial location,
  not a guarantee any candidate actually contains a replay yet." It checks,
  in order: `runs/_designer` → `runs/_loose` → `runs` → the data root itself.
  **This is the closest thing to a "canonical replay directory" concept
  Bytefray has today, and it is explicitly a best-guess starting point for a
  picker, never a registry, index, or "recent replays" list.**
- **No concept exists today** of: a canonical replay directory *registry*, a
  recent-replay list, a replay registry/database, a "history" directory, or
  a user-configured replay root beyond the single `BYTEFRAY_ROOT` override
  that relocates the *entire* data root (agents, replays, config together).
- **Collision/overwrite behavior is asymmetric and producer-dependent:**
  - `runs/_loose/replay.jsonl` uses a **fixed filename** — a second bare
    `bytefray run` silently overwrites the first run's replay/result/summary.
    This is a genuine data-loss trap for a naive user, not a Phase 5 defect
    to fix, but a fact a future history browser must not assume away (the
    "loose" directory can never hold more than one match's artifacts at a
    time by construction).
  - Designer (`runs/_designer/<UTC-stamp>-<8-hex-uuid>/`), Development test
    (`runs/agents_test/<agent>/<UTC-stamp>-<8-hex>-vs-<opponent>/`),
    tournaments, and evaluations all use collision-free per-run directories
    (timestamp + random suffix, or ordinal + names + seed), so two runs
    launched in immediate succession — or a stale process racing a new one
    — can never collide.
  - `designer_workflows.new_match_run_directory`'s own docstring is explicit
    that this directory naming is **never** an input to canonical match
    identity — "safe to change this naming scheme at any time without
    affecting `match_id`" — which cuts both ways for a future browser: the
    directory is a reliable *occurrence* locator, but two occurrences with
    byte-identical inputs will still carry the *same* `match_id`/`replay_id`
    (see Section P).
- **Installer-created `replays`/`logs` top-level directories**: dead, and
  already removed in Phases 2/3 of the maintenance track — no runtime writer
  ever targeted them. Not relevant to where replays actually live.
- **No compression** anywhere in the writer path.

---

## E. Replay schema inventory

Canonical writer/reader: `engine/src/battle_engine/replay.py`. Schema name
`battle2.replay`; `SUPPORTED_SCHEMA_VERSIONS = (2, 3, 4)`; plus tolerant
adaptation of unversioned legacy v0.1/v0.2 native shapes and one-off legacy
event records (`adapt_v01_record`). Current production writer emits **version
4** (process rulesets: `bytefray-rules-4`/`-4-alpha1`/`-4-alpha2`) or
**version 3** (`bytefray-rules-1`/`-2` and the v2/v3-alpha research rulesets).

### Top-level record types

| Record | Type | Required? | Meaning | Stable metadata? | Needed for playback? |
|---|---|---|---|---|---|
| `schema` | str | always | Fixed literal `"battle2.replay"` | Yes | Format check only |
| `schema_version` | int | always | 2, 3, or 4 (or absent → legacy adapter) | Yes | Governs which fields are trusted |
| `record_type` | str | always | `"header"` \| `"tick"` \| `"result"` | Yes | Dispatch |

### `ReplayHeader` fields (`record_type: "header"`)

| Field | Type | Required? | Meaning | Stable metadata? | Needed for playback? |
|---|---|---|---|---|---|
| `config` | object | yes | `MatchConfiguration`: `arena_size`, `instr_per_tick`, `seed`, `win_mode`, `weights` | Yes, since v0.1 | Yes |
| `agents` | map id→name | default `{}` | Entrant id/name only | Yes, since v0.1 | Display only |
| `replay_id`/`match_id`/`result_id` | str\|null | v3+ | Identical content-hash value (see Section P) | Yes (v3+ only) | No |
| `runtime_kind` | `"vm"`\|`"python"`\|null | v3+ | Governs interpretation of several `AgentState` fields | Yes (v3+ only) | Yes, for correct interpretation |
| `reproducibility` | object | v3+ | Mirrors `result.json`'s block (seed, arena, ticks, action budget, win_mode, weights, entrant_order, optional `locality_reach`) | Yes (v3+ only) | Partially (config already covers playback) |
| `entrants` | array of objects | v3+ | Rich per-entrant identity/statistics/diagnostics — see Section F/H | Yes (v3+ only), richness varies by era | No, for pure state playback |
| `ruleset_id` | str\|null | additive, v0.10 Phase 4+ | Bytefray gameplay Ruleset identity | Only on current-writer output | No for playback; yes for correct semantic interpretation |

### `TickSnapshot` fields (`record_type: "tick"`)

| Field | Type | Required? | Meaning | Needed for playback? |
|---|---|---|---|---|
| `tick` | int | yes | Tick number, starting at 0 (tick 0 = pre-action initial state) | Yes |
| `agents` | array of `AgentState` | default `()` | Per-agent `pc`, `alive`, `cpu_used`, `mem_writes`, `region`, `register_a/p`, `zero_flag`, `last_read`, `termination_reason`, (v3 research) `locus` | Yes |
| `score` | map | default `{}` | Per-tick score snapshot (not a diff) | Yes |
| `memory_diffs` | array of `MemoryDiff` | default `()` | `address`, `length`, `owner`, `values` (actual bytes written) | Yes — sole mechanism for arena reconstruction |
| `events` | array (kill/death/move/spawn/territory/claim/forfeit) | default `()` | Engine-domain events | Only for event-timeline features |
| `processes` | array of `ProcessState` | schema-4 only, omitted (not null) on 2/3 | `process_id`, `entrant_id`, `anchor`, `disrupted`, `reach` | Yes, for v4-family matches |

Tick data is *not* metadata-bearing for a history browser beyond tick 0's
initial state; it is the bulk-volume payload (see Section L/Q).

### `MatchResult` fields (`record_type: "result"`)

Mirrors the header's `replay_id`/`match_id`/`result_id`/`entrants` plus
`winner` (nullable — `null` for a tie, unlike `result.json`'s `"tie"` string
sentinel), `win_mode`, `ticks`, final `score`, final `agents`,
`termination_reason`, and (schema 4) terminal `processes`.

### Validation/corrupt-file/unknown-field behavior (verified against
`engine/tests/test_replay_contract.py`, `client/tests/test_replay_session.py`)

- Unknown `schema` name, unsupported `schema_version`, or unrecognized
  `record_type` all raise `ReplayFormatError` with a specific, tested message
  (`"unsupported battle2.replay schema version 99"`, `"unsupported replay
  schema"`, `"unsupported record_type"`).
- Missing required fields raise `ReplayFormatError` at the point of the
  missing field (e.g. `config.arena_size is required`).
- Unknown/extra fields are silently tolerated (every released reader has
  never rejected an unrecognized top-level key — this is exactly how
  `ruleset_id` was added without a schema bump).
- A missing terminal `MatchResult` record is **not** an error at the
  `ReplaySession` layer — `winner`/`termination_reason` simply read as `None`.
- A missing header, a second header/result record, or a non-strictly-
  increasing tick number are rejected by `ReplaySession` (not by the raw
  `deserialize_record`/`iter_replay` reader itself) as structurally
  incomplete/inconsistent — `ReplaySessionError`, distinct from
  `ReplayFormatError`.
- A truncated/malformed-mid-stream file fails the **entire** read at the
  point of corruption (`ReplayFormatError`, with file/line context) — there
  is deliberately no partial-recovery mode anywhere in the stack.
- An **unrecognized `ruleset_id` string is never validated against any
  registry** at parse time — `deserialize_record` only checks that it is a
  string or null; `resolve_replay_ruleset` returns it verbatim with
  `"recorded"` confidence regardless of whether it names a real ruleset.
  Confirmed both by direct source inspection and by Phase 4's own isolated
  probe, which loaded all eight registered ruleset IDs plus one deliberately
  unregistered ID through identical synthetic data and found all nine loaded
  successfully.

---

## F. Metadata inventory

| History field | Present directly | Derivable | Missing | Source |
|---|---|---|---|---|
| Match date/time | **No** | No | **Yes — no embedded timestamp of any kind exists anywhere in the match/replay/result identity or content** | — |
| Replay creation date/time | No | No | Yes | — |
| Entrant names | Yes | — | — | Header `agents`/`entrants[].name` (every schema era, including v0.1) |
| Entrant count | Yes | — | — | `len(header.agents)`/`len(entrants)` |
| Agent API generation | Yes (Python, current-era writers) | — | Missing for VM entrants (not applicable) and for pre-Phase-D-era Python artifacts | `entrants[].metadata.api_version` |
| Agent source/path identity | **No, by explicit design** | No — never recorded, not even in the identity hash | Yes, deliberately (portability across checkouts) | `docs/RESULT_SCHEMA.md`: "never a filesystem path" |
| Agent content hash | Yes, per-match | — | Missing for older (pre-hash-field) writers | `entrants[].metadata.source_sha256`/`code_sha256`/`local_source_fingerprint` |
| Agent manifest identity | Partial (`agent_version` string only) | No | The richer content-addressed `agent_revision_id` is **never** on ordinary match artifacts | `entrants[].metadata.agent_version`; `agent_revision_id` only exists in the separate `evaluation_history`/agent-revision store |
| Ruleset ID | Yes, for current writers | Yes, "recovered" with caveat for schema-exactly-3 | "Unknown" for schema 2 and any header missing it outside that one recoverable case | `header.ruleset_id`; `resolve_replay_ruleset` |
| Ruleset display name | No (only the ID string) | Yes, via a static lookup table in current source | — | Not persisted; resolved from current code |
| Seed | Yes, essentially always a concrete int | — | Only null for reader-tolerance of malformed/legacy input | `config.seed`/`reproducibility.seed` |
| Agent Params | Yes, resolved **values only**, non-empty only for API-v2/process entrants | No | Original user-entered (pre-resolution) values are never recorded | `entrants[].metadata.parameters` |
| Preset name | **No** | **No — not even externally recoverable in general** | Yes, entirely | Never persisted anywhere (see Section J) |
| Winner | Yes, when a result record exists | — | Missing if the result record is absent (possible for a truncated/partial capture) | `result.json.winner` / terminal `MatchResult.winner` |
| Draw/tie status | Yes | — | — | `result.json.winner == "tie"`; replay terminal `winner == null` (two different sentinels — see Section K) |
| Termination reason | Yes | — | — | `termination_reason` |
| Final score | Yes | — | — | `score` |
| Final territory/core state | No (not without tick-level reconstruction) | Yes, from `memory_diffs`/ownership reconstruction | — | Requires full replay parse (Tier 3/4, Section Q) |
| Cycle/tick/round count | Yes | — | — | `ticks` |
| Match duration (wall-clock) | **No** | **No** | Yes, entirely — only tick *count* is recorded, never real elapsed time | — |
| Entrant elimination information | Partial (`alive`, `termination_reason`) | Yes, richer, from event/tick reconstruction | — | `entrants[].alive`/`.termination_reason`; full detail needs Tier 3/4 |
| Bytefray product version | **No** | No | Yes — genuinely absent from every ordinary match artifact (contrast: the separate `evaluation.json` execution-context concept **does** record `bytefray_version`) | — |
| Engine version | **No** | No | Yes | — |
| Replay schema version | Yes | — | — | `schema_version` |
| Core/arena size | Yes | — | — | `config.arena_size` |
| Match mode | Partial (`result.json.mode`: `"b2"`/`"redcode94"`) | — | Not present on the replay header itself (only `runtime_kind`) | `result.json.mode` |
| Evaluation/development context | **No** (nothing inside the artifact says "this came from `agents test`/tournament/bare CLI") | Yes, **only** from the containing directory path (`runs/agents_test/...` vs `runs/_loose/...` vs `runs/tournaments/...`) | Fragile if the file is moved/copied out of its producing directory | Directory location only — a purely filesystem/external fact |
| Replay filename | Yes | — | — | Filesystem |
| Replay absolute path | Yes | — | — | Filesystem |
| Replay file size | Yes | — | — | Filesystem |
| File modification time | Yes | — | Fragile (see Section G) | Filesystem |

### Category definitions used above

- **Embedded metadata**: actually recorded inside the replay/result JSON.
- **Derived replay metadata**: deterministically computable from embedded
  content (e.g. territory from `memory_diffs`, or a ruleset display name
  from a static current-code lookup table keyed by the embedded ID).
- **Filesystem metadata**: path, size, mtime — real, but never a fact about
  the match itself, only about this particular file on this particular disk.
- **External metadata**: requires something *outside* the artifact and
  outside current-code static tables — the original agent source tree, a
  live/still-matching manifest, the `agent_revisions` store, or a database
  that isn't the replay/result file itself.

A future browser must not present these four categories with equal
confidence — a "recorded" ruleset ID and a filesystem mtime are both
"available," but only one is a fact about the match.

---

## G. Timestamp findings

**Bytefray does not record a true match timestamp anywhere.** Verified
directly: `canonical_match_id`/`_finalize_native_artifacts` (the entire
identity/artifact construction path in `match_service.py`) contains no
`datetime`/`time.time()`/timestamp field of any kind, and neither
`ReplayHeader`, `TickSnapshot`, `MatchResult`, nor `ResultEnvelope` has a
timestamp field. There is no match start time, match finish time, or
replay-write time embedded anywhere in the canonical artifacts.

**This is a deliberate omission, not a technical limitation** — the
sibling `evaluation.json` artifact (a different artifact type, written by
the same codebase) *does* record `created_at`/`updated_at`/`finished_at` UTC
lifecycle timestamps (`ARCHITECTURE.md`'s "Evaluation History (v0.7)"
section). The same team, in the same codebase, has already built and
shipped timestamp bookkeeping for one artifact type and chose not to extend
it to ordinary match/replay/result artifacts. A future Phase 6 schema
proposal should treat this as a precedent to follow, not a novel ask.

**Only filesystem mtime is available today**, and it is explicitly
unreliable for match-history ordering:

- **Copying a replay** preserves mtime with most tools (`cp -p`, most GUI
  copy operations) but not all (a plain re-download, some archive tools, or
  a naive script can reset it to copy time).
- **Restoring from backup** typically sets mtime to restore time, not
  original write time, unless the backup tool explicitly preserves it.
- **Downloading from another system** frequently resets mtime to download
  time (many transfer protocols/browsers do this by default).
- **Git checkout** sets file mtime to checkout time, not any time recorded
  in the commit — and replays are gitignored in this repository anyway
  (`.gitignore` has a bare `*.jsonl` pattern), so this mostly applies to
  hypothetical future tracked fixtures, not real user replay directories.
- **Archive extraction** (zip/tar) usually preserves the archived mtime, but
  extraction tools vary, and this cannot be relied on universally.
- **File synchronization** tools (Dropbox/OneDrive/etc.) have inconsistent
  mtime-preservation behavior across sync direction and conflict resolution.

**Conclusion:** a history browser can display "file modified" as a soft,
explicitly-labeled hint (exactly as `evaluation_history`'s own
`ArtifactLocation.file_modified_at` field is already named — never
`created_at` — see Section W), but it cannot claim this is "when the match
was played" without a caveat, and it cannot be used as a stable sort key
across copied/restored/synced replay collections without acknowledging the
above failure modes.

---

## H. Entrant identity/reproducibility findings

Entrant metadata is built once, in `match_service._finalize_native_artifacts`
(and mirrored by `canonical_match_id`'s own independent identity-hash
payload), and embedded on both the replay header/terminal result and
`result.json`.

- **Is only display name recorded?** No — display name (`name`) plus a
  content digest are both recorded for every current-writer artifact.
- **Is filesystem path recorded?** **No, never, by explicit design** —
  `docs/RESULT_SCHEMA.md` states directly that entrant metadata "carries
  content digests... never a path," so that `match_id` stays identical
  across different checkout locations. Confirmed structurally: no
  `path`/`dir`/`source_path` key exists in any entrant-dict literal in
  `match_service.py`.
- **Is manifest metadata copied?** Only narrowly — `agent_version` (the
  manifest's declared version string) and `entry_point`. No manifest hash
  and no copy of the parameter *schema* (types/bounds/descriptions/presets)
  — that "stays with the agent package and is deliberately never copied
  into an artifact" (comment in `match_service.py`).
- **Is Agent API version recorded?** Yes, for Python entrants
  (`entrants[].metadata.api_version`) — not applicable to VM entrants.
- **Is source code embedded?** No — content is hashed, never embedded.
- **Is source hash recorded?** Yes: `source_sha256` (entry-point file) for
  Python, `code_sha256` for VM, plus a broader whole-agent-tree
  `local_source_fingerprint`/`local_source_fingerprint_final` for Python
  entrants (covering multi-file agents and lazily-imported modules).
- **Are Agent Params recorded?** Yes, resolved values only, and only when
  non-empty (Agent-API-v2/process entrants) — see Section J for the
  preset-identity gap.
- **Are defaults vs. overrides distinguishable?** **No** — the persisted
  mapping is flat effective values; nothing marks whether a value came from
  a schema default, a preset, or an explicit override.
- **Is preset identity recorded, or only resolved values?** Only resolved
  values — see Section J.
- **Can two different agents have identical names?** Yes — `name` is a
  free-form display label, never a uniqueness-enforced identity. Nothing
  prevents two different code trees from producing entrants both named
  e.g. "Nemesis."
- **Can the same agent change after the replay is produced?** Yes, and the
  artifact would not know — the content digest is computed once, at
  execution time, from whatever bytes were on disk *then*, and is then
  frozen immutably into the finished artifact. Nothing re-reads the current
  file to compare later. Detecting such drift is exactly what the separate
  `evaluation_history`/`agent_revisions` machinery exists for (source-drift
  detection, `CONFLICTING`-confidence fields) — and that machinery **does
  not apply** to an ordinary `bytefray run`/`bytefray tournament` artifact.

### The two different guarantees, answered precisely

- **"Nemesis vs Viper"** — reliably answerable from `name` alone, for every
  supported schema era, with the caveat that name is not a uniqueness
  guarantee.
- **"This exact version of Nemesis vs this exact version of Viper"** —
  answerable, but only:
  1. for artifacts written by a codebase era that actually recorded
     `source_sha256`/`local_source_fingerprint` (v1-era `result.json`
     artifacts are documented — `ARCHITECTURE.md`'s v0.7 section — as never
     having written `api_version`/`agent_version`/`source_sha256`
     *anywhere retrievable*, so this guarantee is flatly `UNKNOWN` for those);
  2. by manually comparing that digest against a separately-obtained hash of
     "the agent believed to be Nemesis today" — nothing in the ordinary
     artifact provides a live path back to a catalog entry, since no
     filesystem path is ever stored.

---

## I. Seed findings

- `Config.seed` is a **non-optional `int`, hard-coded default `1337`** — a
  native `MatchRequest` always carries a concrete seed by construction,
  never `None`, at the config layer.
- `replay.MatchConfiguration.seed` is typed `int | None` purely for
  **reader tolerance** of historical/legacy or malformed input; no current
  writer ever emits it as null.
- **Every native `result.json`/replay carries a concrete integer seed in
  practice.** It is a first-class input to `match_id`'s content hash
  (Section P), and it is embedded in the persisted `reproducibility` block
  on both `result.json` and the replay header.
- **Seed semantics are not uniform across rulesets:**
  - v1/v2: entrant start addresses are seed-independent (fixed
    slot/`index*spacing`); only the shared match seed plus a per-slot
    derived RNG seed feed each entrant's private RNG stream.
  - v3 (locality research): the persisted `reproducibility` block
    additionally carries `locality_reach` as a second axis, only when a
    locality ruleset is in play.
  - v4/"seeded" placement rulesets: the match seed **also** determines
    entrant start/core placement geometry, not just RNG — seed is doing
    double duty as both an RNG seed and a placement-geometry input.
  - Tournament scheduling re-derives each scheduled pairing's own placement
    seed from a formula, explicitly so "the layout is reproducible from the
    scheduled match's recorded inputs alone" (comment in
    `tournament_service.py`).
- **Randomize Seed** (Designer Advanced and Development test panels) draws
  from Python's `secrets` module (not the deterministic match RNG) and
  writes a concrete, ordinary-looking integer into the visible seed field —
  it produces a normal recorded seed indistinguishable, after the fact, from
  one a user typed by hand. There is no "this seed was randomized" marker
  anywhere in the persisted artifact.
- **What "Copy Seed" or a future "Re-run Match" could actually guarantee:**
  the seed alone reproduces **nothing** if agent source, ruleset identity,
  or configuration differ. Reproducing the literal same match additionally
  requires: byte-identical entrant source content (verifiable only via the
  recorded `source_sha256`/`code_sha256` digests, never by re-downloading
  embedded source, since none is embedded), the same `ruleset_id`, the same
  full `reproducibility` block (arena size, tick limit, action budget,
  win_mode, weights, entrant order, and — where applicable —
  `locality_reach`), and the same resolved Agent Params. This is directly
  proven by the existing test suite: `test_match_id_changes_with_meaningful_config_or_code_changes`.
- **Is the replay self-contained for playback without re-running?** Yes —
  see Section U. Playback never needs the seed at all; it replays recorded
  state. The seed only matters for a hypothetical *re-execution*, never for
  viewing what already happened.

---

## J. Agent Params and preset representation

`AgentParameterSchema.resolve()` implements exactly one precedence rule:
`defaults < preset < overrides`, and returns a **flat mapping of effective
scalar values only**. This is confirmed both by the resolver's own code and
by an explicit design comment at the point resolved parameters are folded
into match metadata: "the concrete resolved parameter values this entrant
actually ran with... the authoring *schema* (types, bounds, descriptions,
**presets**) stays with the agent package and is deliberately never copied
into an artifact."

**Preset name is never persisted to any match/replay/result artifact.** A
repository-wide search for every "preset" concept confirms this for both
uses of the word in this codebase:

- **Agent Params presets** (`agent_parameters.ParameterPreset`, selected via
  `--{letter}-preset` on the CLI or the Designer's preset dropdown): only
  the resolved values ever reach `MatchEntrant`/`MatchRequest`/any artifact.
  The preset name itself is not threaded through at all.
- **Evaluation presets** (`agent_evaluation.EvaluationPreset`, an unrelated,
  differently-scoped feature — reusable CLI-flag bundles for `agents
  evaluate`): the one place a preset *name* is written anywhere is a
  `--dry-run --json` console-preview helper, which is never passed to the
  actual persisted `evaluation.json` writer. The module's own docstring
  states this is intentional: "nothing downstream of this block... can tell
  a preset was involved."

**Consequence for a future history browser:** it can always show

> aggression=0.8, scan_radius=4, ...

but it can **never** show

> Preset: Aggressive

from artifact data alone — not "not yet implemented," but structurally
unrecoverable from what is persisted today. A heuristic reconstruction
("does this resolved-value set match one of the agent's *currently* defined
presets?") is theoretically possible but unreliable: it requires the
original agent's manifest to still exist, be unchanged since the match, and
happen to define a preset with exactly these values — none of which is
verifiable from the artifact itself.

Defaults vs. explicit overrides are likewise indistinguishable in the
persisted artifact: a parameter left at its schema default and one
explicitly overridden to the identical value produce byte-identical output.

---

## K. Result metadata

Winner, draw/tie, termination reason, final score, ticks, and final
per-entrant state are all present **without decoding the full replay
timeline** — and, importantly, **without touching the replay file at all**:
`result.json` is a small, standalone JSON document (not JSONL) written
atomically alongside the replay, carrying `winner`, `mode`, `status`,
`termination_reason`, `ticks`, `score`, `entrants`, `reproducibility`,
`replay` (id + digest + filename reference), `backend`, and `ruleset_id`.

**This is the single most important architectural fact for a future history
browser's cheap-path design**: a history row's core facts do not require
opening the replay stream at all when `result.json` is present alongside it
(true for every native and pMARS match — both write one). The replay
header's own duplicated `entrants`/`reproducibility`/`ruleset_id` fields are
a *secondary* source, useful only when `result.json` is missing/deleted but
the replay survives.

**Draw/tie representation is inconsistent between the two artifacts, and a
browser must normalize it:** `result.json.winner` uses the string sentinel
`"tie"` (`WINNER_TIE_SENTINEL`, reserved so it can never collide with a real
entrant ID) for compatibility with older consumers that always expect a
non-null string; the replay's own terminal `MatchResult.winner` uses `null`
instead, since that field was newly introduced with no legacy string
convention to preserve. Both represent the identical fact.

**Quantifying "does answering 'who won?' require the full timeline":**
today, yes, *if* the only source consulted is the replay file via
`ReplaySession`/`ReplayPlayer` — `ReplaySession.load()` unconditionally
buffers every `TickSnapshot` before exposing `winner`/`termination_reason`
as post-load accessors, and `iter_replay` has no seek-to-end/reverse-read
capability, so nothing currently reads only the header + terminal record
without a full linear pass. **But this is moot in practice**, because
`result.json` already answers the exact same question for a small fraction
of the cost — see Section L for measured numbers. The architectural gap is
real (no header+result-only replay reader exists), but it is not the
binding constraint it would first appear, given `result.json`'s existence.

---

## L. Load-cost findings, with real measured data

### `ReplaySession.load()` cost (spec + code, `client/src/battle_client/session.py`)

- **Memory:** O(total replay size) — every `TickSnapshot` (with its
  `memory_diffs`/`agents`/`events`) is retained for the session's lifetime;
  no eviction, paging, or on-disk spill. Documented explicitly as an
  intentional choice for "v0.3 scale" matches (a few thousand ticks, a few
  KB of arena).
- **`load` time:** O(number of records) — one linear pass through
  `iter_replay`; the generator is fully drained into a `list`, not streamed
  to the caller.
- **Seeking:** a **forward** seek (target ≥ current position) applies only
  the intervening ticks' diffs (amortized/incremental) — this *partially
  refutes* `docs/REPLAY_SCHEMA.md`'s "Known limitations" text, which
  describes reconstruction as unconditionally "linear-scan from tick 0... no
  snapshot-at-tick-N shortcut." That text is accurate for a **backward**
  seek (which does reset to tick 0 and replay forward) but not for a forward
  one, in the current `session.py` implementation. There is still no
  persistent per-tick snapshot cache, so repeated backward seeks across a
  long replay each cost O(target tick) again.
- **No shortcut exists today** to read only the header + terminal result
  without buffering every tick in between — `ReplaySession.load()` always
  buffers everything it sees, and no other code path in the repository
  currently uses `iter_replay` directly with an early-break for this
  purpose. This *could* be trivially built on the existing public generator
  (it is a genuine Phase 6 opportunity, not a limitation of the underlying
  reader), but nothing does it today.

### Real measured data (this repository's own accumulated local `runs/` corpus)

The Phase 5 spec permits temporary, read-only discovery probes. This
repository's own `.gitignore`d, uncommitted `runs/` directory — genuine
accumulated local development/research history, not a synthetic benchmark —
was measured directly with a short, temporary, read-only Python script
(deleted after use; not staged or committed):

| Measurement | Result |
|---|---|
| Total files under `runs/` | **106,170** (44,645 `*.jsonl`, 53,458 `result.json`, the rest `trace.jsonl`/`evaluation.json`/etc.) |
| Total bytes under `runs/` | **~33.5 GB** |
| Tier 1 — recursive `os.walk` + `stat()` over every file | **~10.0 s** |
| Tier 2 — `json.loads` + read three fields, sampled 5,000 `result.json` files | **2.234 s total, 0.447 ms/file** |
| Tier 3 — full production `iter_replay()` load, sampled 25 `replay.jsonl` files (14.94 MB, 9,986 total records) | **0.792 s total, 31.7 ms/file average** |

Sample individual replay sizes observed in this corpus during the walk
ranged from tiny (a few hundred bytes for a `trace.jsonl` sidecar) to
**1.89 MB** for a single `replay.jsonl` from a long Development-test run —
confirming real replays in active local use already exceed the "a few KB
arena, a few thousand ticks" scale `ReplaySession`'s own docstring
describes as its design target, by a wide margin in file-size terms (driven
by per-tick `memory_diffs`/`AgentState` volume, not arena size itself).

**Extrapolated implication:** scanning this corpus's `result.json` files
alone (Tier 2) is roughly two orders of magnitude cheaper per file than
fully parsing the corresponding `replay.jsonl` via the production reader
(Tier 3: ~32 ms/file vs. ~0.45 ms/file) — a ~70x difference — before even
accounting for `result.json`'s dramatically smaller average size. Scanning
every `result.json` in this real corpus (53,458 files) at the measured
per-file rate extrapolates to roughly **24 seconds**; scanning every
`replay.jsonl` (44,645 files) at the measured full-parse rate extrapolates
to **tens of minutes**, not seconds — a materially different order of
magnitude that any Phase 6 persistence design must treat as a real
constraint, not a hypothetical one, since this exact corpus already exists
on a real development machine today.

This measurement is also **strictly larger in scale** than the only other
scan-cost benchmark that exists anywhere in this codebase — the
`evaluation_history` design spec's own measured 10/100/1000-synthetic-
artifact benchmark (see Section W) — by roughly two orders of magnitude, and
it is real accumulated data rather than a synthetic population.

---

## M. Existing replay-opening workflow

- **CLI (`client/src/battle_client/cli.py`):** `--replay` (required for the
  headless renderer; optional for `--renderer pygame`, which falls back to
  an empty-state picker), plus pygame-only flags (`--tick-delay`,
  `--start-tick`, `--paused`, `--speed`, `--trace`, `--perspective`,
  `--director`, `--fight-night`). A missing path calls `argparse`'s
  `p.error(...)` — clean usage message, `SystemExit(2)`, no crash.
- **GUI empty-state picker
  (`client/src/battle_client/renderers/replay_picker.py`):** a **bespoke,
  in-house Pygame directory browser** (deliberately not a native OS file
  dialog — the module's own docstring gives the rationale), restricted to
  `*.jsonl`, seeded at `canonical_replay_directory(get_data_root())`. Its
  own module docstring states plainly it has "no thumbnails, search, sort,
  or history." A failed pick re-shows the picker with an in-window error
  message rather than exiting, since a Start-Menu-launched user has no
  terminal to read a stderr message from.
- **No drag/drop, no OS file-association integration** anywhere in the
  repository (a targeted search for `dragEnterEvent`/`dropEvent`/
  `setAcceptDrops`/`QMimeData` and installer file-association hooks found
  nothing).
- **No "recent replay"/"reopen" concept in the Replay Viewer itself.** The
  picker's only "memory" is whatever `initial_directory` its caller passed
  in — not a persisted history.
- **Designer's "View Last Match"** (`app/agent_designer.py`) holds a single
  in-memory `self._last_replay` pointer, set right after a match completes,
  reused if the file still exists, else falling back to a native
  `QFileDialog` filtered to `*.jsonl`. Evaluation History has its own
  structurally identical analogous path
  (`_on_evaluation_open_replay`/`openReplayRequested`). Both launch the
  Replay Viewer as a detached subprocess via `open_pygame_client_direct` →
  `build_replay_command` (a thin `--replay <path> [extra flags]` command
  builder) — **this "current file path" concept is exactly what a future
  history browser could reuse to hand off a selected replay to the existing
  launcher**, without touching playback architecture at all.
- **Error handling is uniformly graceful, never a raw crash**, across every
  entry point examined: missing path → `argparse` usage error; malformed
  replay content on the headless CLI path → caught generic `Exception`,
  one-line stderr message, exit 1; malformed content on the interactive
  pygame path → `_load_session_or_error` catches exactly
  `(ReplaySessionError, ReplayFormatError)` and prints
  `"[battle_client] error: {error}"`; a bad pick from the empty-state picker
  stays in the picker loop with an in-window message; Designer's
  `open_pygame_client_direct` checks file existence up front
  (`FileNotFoundError`) and catches `Popen` failures
  (`OSError`), both surfaced via `QMessageBox.critical`. **One asymmetry
  worth flagging for Phase 6:** the Designer only validates file
  *existence* before launch — a present-but-corrupt replay's error only
  surfaces inside the detached child Replay Viewer process's own window, not
  back in the Designer's own UI.

---

## N. Historical replay compatibility

**No checked-in corpus of real historical replay files exists in this
repository, at any era.** `git ls-files -- '*.jsonl'` returns nothing;
`.gitignore` carries a bare `*.jsonl` pattern; `docs/archive/` and
`_legacy/` contain only Markdown/source, no replay data. All cross-version
compatibility evidence in this codebase is **generated fresh by tests at run
time**, never preserved from actual production history. This matches, and
is independently reconfirmed against, Phase 4's own identical conclusion.

The only genuinely historical artifacts on disk are five tiny, hand-authored
JSON fixtures in `engine/tests/fixtures/replay/` representing pre-v3 shapes
(a legacy one-event record, an unversioned v0.1 header, an unversioned v0.1
tick snapshot, and canonical v0.2.0 header/tick records) — deliberately
unproducible by the current writer, used solely to exercise the *reader's*
backward-compatibility path.

| Replay era/schema | Loads today? | Metadata available | Metadata missing | History indexing implications |
|---|---|---|---|---|
| Legacy one-event / unversioned v0.1 (no `schema` key at all) | Yes, via `adapt_v01_record` | `config` (arena/seed/etc.), sparse per-tick agent positions/events | No `entrants` rich metadata, no `ruleset_id`, no `replay_id`/`match_id`/`result_id`, ticks may be non-contiguous (sparse) | A browser must treat these as effectively "config + entrant names only" |
| v0.2.0 canonical (`schema_version: 2`) | Yes | Same as above, canonical field names | Same gaps as v0.1; `resolve_replay_ruleset` returns **"unknown"** for schema 2 deliberately (not recoverable — this was genuinely the pre-rename v0.2.0 wire format, proven historically but not proven to fall inside the Ruleset-v1-stable window) | Ruleset identity is unrecoverable, not merely unrecorded, for this era |
| Schema 3, pre-extension (never shipped in a tagged release) | Yes (additive fields default safely) | — | — | Not a real-world concern; no tagged release ever shipped the pre-extension shape |
| Schema 3, extended (v0.3.0+ era) | Yes | `replay_id`/`match_id`/`result_id`, `runtime_kind`, `reproducibility`, `entrants` (richness varies further by sub-era — see below), register/termination per-agent state | `ruleset_id` absent → **"recovered" as `bytefray-rules-1`** with explicit confidence labeling (exact `schema_version == 3` check, deliberately not `>=`) | Ruleset identity is recoverable with a labeled confidence, not silently assumed |
| Schema 4 (`bytefray-rules-4`/`-4-alpha1`/`-4-alpha2`) | Yes | Everything schema 3 has, plus `processes` (per-tick process anchor/reach/disruption state) | `ruleset_id` is required-and-recorded for all current writers; only a hand-edited/corrupted schema-4 header could lack it, which resolves to `"unknown"` | Fullest available metadata era |
| v1-era `result.json` (Ruleset v1, before Phase D/parameter/identity features existed) | Yes (schema `battle2.result` v1 has never bumped) | `winner`/`score`/`ticks`/`termination_reason` | **`api_version`/`agent_version`/`source_sha256` were never written anywhere retrievable** for this era (documented directly in `ARCHITECTURE.md`'s "Evaluation History (v0.7)" section, established by the v1 evaluation-history adapter's own honest `UNKNOWN` reporting) | Entrant-identity richness is genuinely, provably absent for the oldest artifacts — not just "not yet extracted" |
| Any schema version with an unrecognized `ruleset_id` string | Yes — **never blocks loading** | Displayed verbatim with `"recorded"` confidence, no registry check | Semantic interpretation (e.g. core-status display) may silently show nothing for an unrecognized ID, without erroring | A browser can safely display any string here; it must not treat an unrecognized value as corruption |

**The future browser must not silently pretend missing historical metadata
is known** — every gap above should surface as an explicit
`unknown`/`recovered`-with-confidence value, exactly the discipline
`resolve_replay_ruleset`/`resolve_result_ruleset` and the `evaluation_history`
package's `ConfidenceValue` model already establish elsewhere in this same
codebase.

---

## O. Corrupt and malformed replay behavior

Current behavior (Section E) is uniformly fail-fast and non-partial: a
malformed/truncated file fails the whole read (`ReplayFormatError`, with
file/line context); a structurally-valid-but-incomplete file (no header,
duplicate header/result, non-monotonic ticks) fails at the `ReplaySession`
layer (`ReplaySessionError`); a missing result record is tolerated, not an
error; an unrecognized ruleset ID is tolerated, not an error.

**What a History Browser should theoretically do when scanning such a
file** — options, not a decision:

- **Ignore** — silently skip; simplest, but hides real problems from the
  user (a corrupted replay they cared about disappears without a trace).
- **Show invalid entry** — list the file with a visible error/health status
  instead of extracted metadata. **This is the pattern the repository's own
  closest analog, `evaluation_history.discovery.discover()`, already uses**:
  one malformed/unsupported sibling becomes its own
  `DiscoveredEvaluation(summary=None, health=HealthReport(codes=(...)))`
  entry rather than aborting the whole scan or being silently dropped. This
  is the most directly relevant, already-proven precedent in this exact
  codebase for a "hundreds/thousands of files, one might be bad" scan.
- **Quarantine** — move/flag the file; more invasive, and risks surprising
  a user who did not ask the browser to touch their files (Phase 5's own
  read-only mandate is a strong signal this should stay opt-in at most).
- **Report error, allow locate/delete** — surface the problem and let the
  user act on it manually; least invasive of the "not silently ignore"
  options.

`evaluation_history`'s existing choice (show invalid entry, never abort,
never auto-modify) is the strongest available precedent and should be
Phase 6's starting point rather than a fresh design.

---

## P. Duplicate replay identity findings

**`replay_id` and `match_id` are not two independent identifiers — they are
the identical value.** Verified directly in
`match_service._finalize_native_artifacts`: the header is built with
`replace(record, replay_id=match_id, match_id=match_id, result_id=result_id,
...)`, and the terminal result record and `ResultEnvelope.replay` both use
the same `match_id` value as their `replay_id`. There is no separate random
UUID anywhere in this scheme.

`match_id` and `result_id` are both `stable_id(prefix, value)` — a truncated
SHA-256 over a canonical (sorted-key) JSON payload:

- `match_id` hashes **execution inputs only**: `mode`, `ruleset_id`,
  `reproducibility` (seed, arena size, tick limit, action budget, win_mode,
  weights, entrant order, optional `locality_reach`), and per-entrant
  identity (`agent_id`, `name`, content-digest metadata, conditionally
  non-default `start`/`parameters`).
- `result_id` additionally hashes the **outcome** (winner, termination
  reason, ticks, score, full entrant records minus non-deterministic
  exception text).
- **Neither hash includes any timestamp, random value, or filesystem path.**

### Consequence: content identity, not occurrence identity

Two genuinely independent executions of byte-identical inputs (same seed,
same agent content, same ruleset, same configuration) that reach the same
deterministic outcome will produce the **identical** `match_id`/`replay_id`/
`result_id` — this is intentional (it is exactly what lets resume-safety
checks detect "the same match" across two runs), but it also means
content-based identity **cannot distinguish** "the same match executed
twice" from "one match's files copied to two locations." Conversely, the
Designer's per-run directory naming (`runs/_designer/<timestamp>-<random>/`)
is explicitly documented as **never** an input to this identity — two
identical matches saved under two different Designer run directories will
carry the *same* `match_id`/`replay_id` at two different paths.

`evaluation_history`'s own `discover()` has already hit exactly this
distinction one layer up (for evaluations, not individual matches): its
`DUPLICATE_IDENTITY_LOCATION` health code and duplicate-groups reporting are
explicit that "copied directories sharing an `evaluation_id` are flagged as
duplicate *locations*, never presented as separate execution occurrences."
**A future replay history browser inherits the identical unresolved
question at the match level: is "identity" content-identity (today's
`match_id`) or execution-occurrence identity (which nothing currently
tracks)?** No current artifact answers this; a stable replay UUID distinct
from `match_id` is a real, evidenced gap (Section T).

### The `_loose` overwrite case is a related but distinct failure mode

`runs/_loose/replay.jsonl` uses a fixed filename, so a second bare
`bytefray run` invocation does not even reach the "duplicate identity"
question — it silently destroys the first run's replay/result/summary at
the filesystem level before any identity comparison could ever happen. A
history browser scanning only the current filesystem state would never see
the overwritten match at all; this is a data-loss characteristic of the
current writer's default path, not something indexing/scanning can recover.

---

## Q. Metadata extraction feasibility tiers

| Tier | Definition | Fields available at this tier |
|---|---|---|
| **Tier 1 — filesystem only** | No replay/result parsing at all | path, filename, size, mtime |
| **Tier 2 — shallow parse (header/`result.json` only, no tick timeline)** | Parse `result.json` (small, standalone) and/or the replay's first line (header) | entrant names/ids, `api_version`/source-hash/params (when present), `ruleset_id` (with confidence), seed/arena_size/tick_limit/win_mode/weights, winner/termination_reason/final score/ticks (from `result.json`, or the replay's *terminal* record — which still requires reaching the last line of the JSONL stream, since there is no seek-to-end index) |
| **Tier 3 — full replay parse** | Everything `ReplaySession.load()`/`iter_replay` fully consuming the file does today | Everything Tier 2 has, plus full per-tick `AgentState`/`ProcessState`/`memory_diffs`, ready for reconstruction |
| **Tier 4 — timeline analysis** | Requires walking the reconstructed tick sequence (`analysis.py`'s `compute_territory_history`, `collect_match_events`, `replay_status.py`'s `get_entrant_statuses`) | Territory history, event timeline, elimination detail, core-status derivation |
| **Tier 5 — external lookup** | Requires something outside the artifact: the original agent source tree, the `agent_revisions` store, or a live/still-matching manifest | Preset name (unrecoverable even here in general — see Section J), current agent-catalog cross-reference, drift detection against today's source |

**Key finding for Phase 6:** because `result.json` already exists as a
small, standalone Tier-2 artifact for essentially every completed match
(native and pMARS alike), a history browser's primary list view never needs
Tier 3/4 access at all. Tier 3/4 costs (Section L's measured ~32 ms/replay
vs. ~0.45 ms/`result.json`) only matter for a detail view or a
timeline/territory feature, not for populating rows.

---

## R. Minimum history row (no schema change)

### Minimum guaranteed fields (reliable across every supported replay era, back to unversioned v0.1)

- Entrant names (header `agents` map has existed since the unversioned v0.1
  shape).
- Seed and arena size (`config.seed`/`config.arena_size` have existed since
  the same v0.1 shape).
- Filename, path, size, mtime (Tier 1, always available, mtime caveated per
  Section G).

**Not guaranteed even at this "minimum" tier:** winner/termination reason —
a replay whose terminal result record is missing or was never captured
(possible for a truncated/partial capture, or a genuinely ancient
unversioned file) has no recoverable winner at all, at any tier.

### Modern-replay-only fields (schema 3+/current-writer only)

`replay_id`/`match_id`/`result_id`, `runtime_kind`, full `entrants[]` rich
metadata (content hashes, API version, resolved params), `ruleset_id`
(recorded with full confidence only on current writers; "recovered" with a
labeled caveat for schema-exactly-3; "unknown" otherwise).

### Optional fields (present only for some producers/eras)

`api_version`/source-hash/`parameters` on Python entrants only (never on VM
entrants, and never on pre-Phase-D-era Python artifacts); `locality_reach`
only for locality-ruleset matches; `processes` only for schema-4 matches.

### Fields unavailable without a schema change

Match/replay timestamp of any kind; stable occurrence-level replay
identity distinct from content-hash `match_id`; preset name; Bytefray
product/engine version; notes/tags of any kind. See Section T.

---

## S. Candidate detail view

**Guaranteed, from Tier 1/2 alone:** full absolute path, file size,
`schema`/`schema_version`, `ruleset_id` (with its confidence label —
never presented as unconditionally certain), entrant names, seed, arena
size, tick count, winner/termination reason/final score (when a result
record exists), and — separately, explicitly labeled as filesystem
metadata, not match metadata — file modification time.

**Optional, present only for some eras/producers:** `runtime_kind`, per-
entrant content hashes and API version, resolved Agent Params, `processes`
snapshot, `locality_reach`.

**Not available at any tier without a schema change:** true match date/time,
wall-clock match duration, preset name, product/engine version, notes/tags,
a stable occurrence-distinct replay UUID.

A detail view can, at additional (Tier 3/4) cost, also show territory/event
timeline summaries and elimination detail — these should be presented as a
"load more" or lazily-computed section, not part of the always-cheap header
facts above, given Section L's measured cost asymmetry.

---

## T. Replay-format gaps

| Missing field | User value | Could derive? | Schema change required? | Future priority |
|---|---|---|---|---|
| Stable replay/match **occurrence** UUID (distinct from content-hash `match_id`) | High — lets a browser distinguish "ran twice" from "copied once," and survive a rerun of identical inputs | No — nothing today distinguishes these cases even in principle | Yes | High |
| Match timestamp (start/finish/write) | High — the single most requested "history" field, and currently has no substitute better than fragile mtime | No | Yes | High |
| Preset identity | Medium — nicer display ("Aggressive" vs. a parameter dump), but the resolved values already convey the functional facts | No, not reliably (Section J) | Yes | Medium |
| Bytefray product/engine version | Medium — matters increasingly as the product evolves pre-1.0 and semantics can shift between versions without a ruleset ID change | No | Yes (though a direct, low-risk precedent — `evaluation.json`'s `execution_contexts` — already exists in this exact codebase) | Medium |
| Notes/tags | Low-medium — a pure UX nicety with no engine dependency; could plausibly live in an out-of-band index/database instead of the replay schema itself | N/A (deliberately not derivable — user-authored) | Only if stored *in* the replay/result file itself; not required if stored in a separate index (Section W) | Low (design choice, not a hard schema gap) |
| Producer/workflow context ("came from `agents test`" vs. bare CLI vs. Designer) | Low-medium — nice for filtering, but already derivable today from directory location as long as the file stays in its producing directory | Yes, from directory path alone, fragile if moved | Only if directory-independence is required | Low |

Each of these was checked against actual current fields (Sections E/F) —
none was assumed missing without first verifying its absence in
`replay.py`/`result_model.py`/`match_service.py`.

---

## U. "Self-contained replay" — evaluated precisely

Three distinct guarantees, evaluated separately:

### Playback self-containment — **yes**

The Replay Viewer can fully reproduce visual playback even if the original
agent files are deleted, the ruleset code has since changed, or starter
manifests have disappeared, and even if the replay is moved to another
computer entirely. `ReplaySession`/`ReplayPlayer` never load agent code or
re-invoke ruleset execution logic to step through recorded ticks — every
frame's state is reconstructed purely from `memory_diffs`/`AgentState`/
`ProcessState` already embedded in the file. This matches the uncommitted
Phase 4 documentation update to `docs/COMPATIBILITY.md` currently sitting in
the working tree (Section A): "Recorded replay playback reconstructs stored
state without re-executing agents."

### Match reproduction (exact rerun) — **not guaranteed by the replay alone**

A rerun requires the *actual* agent source files (only a content digest is
embedded, never the source itself — `docs/REPLAY_SCHEMA.md`'s "Python
Observation capture: explicitly out of scope" section is explicit that
per-callback agent reasoning is never captured, only engine-observable
state), the *same* ruleset/engine code version (ruleset semantics are
protected/frozen by policy during the Alpha 1 feedback window, but the
*replay itself* never stamps an engine/product version — Section T), and
the same resolved parameters. If the original agent files are gone, a
rerun simply cannot happen at all (there is nothing to re-execute). If
ruleset code has changed without a `ruleset_id` change (a hypothetical
future risk, not observed today) or the engine version has changed, a rerun
could silently produce a *different* result with no way for the artifact to
flag that, since no engine/product version is stamped anywhere.

### Semantic interpretation — **partially self-contained**

`runtime_kind` and `ruleset_id` are stamped on the header and are sufficient
to interpret the documented runtime-kind-dependent field table (e.g.
whether `pc` means a real VM fetch address or Python controller
bookkeeping). But some interpretation depends on ruleset-**family**
membership tables that live in **current source code**, not in the replay:
`replay_status.py`'s `has_vulnerable_core`/core-status derivation is
already documented (Phase 4's audit, P4-02) to return no core status at all
for `bytefray-rules-4-alpha2`/permanent `bytefray-rules-4` given the
identical stored state that yields a real status under `bytefray-rules-4-alpha1`
— an asymmetry rooted in which rulesets are in a hand-maintained
"vulnerable-core family" set in current code, not in anything the replay
itself asserts. **A replay's semantic meaning can therefore drift if that
current-code interpretation table changes in a later Bytefray version,
even though the replay's raw bytes never change** — this is a real,
already-documented (if narrow) limitation on the "fully self-contained"
claim, not a hypothetical one.

---

## V. Search/filter feasibility

| Filter/search | Supported now? | Reliable across history? | Notes |
|---|---|---|---|
| Agent name | Yes (Tier 2) | Yes, every era | Free-text display label only; not a uniqueness guarantee (Section H) |
| Ruleset | Yes, confidence-qualified (Tier 2) | No — "unknown" for schema-2 headers and any header missing the field outside the one schema-3 recoverable case | Must surface confidence in the UI, not silently normalize |
| Winner | Yes (Tier 2, via `result.json`) | Only if a result record/`result.json` exists | Missing for a truncated/partial capture |
| Draw | Yes (Tier 2) | Same as winner | Two different sentinel representations to normalize (`"tie"` vs. `null`) |
| Seed | Yes (Tier 2) | Yes, every era (field has existed since v0.1) | — |
| Date range | **No reliable field exists** | No | Only fragile filesystem mtime (Section G) |
| Product version | **No** | No | Not recorded on any ordinary match artifact (Section T) |
| API generation | Partial (Tier 2) | Only for current-era Python entrants | Never applicable to VM entrants; absent on pre-Phase-D Python artifacts |
| Params | Partial (Tier 2) | Only current-era, non-empty, API-v2/process entrants | — |
| Preset | **No** | No | Never persisted at all (Section J) |
| Termination reason | Yes (Tier 2) | Yes, for any artifact with a result record | — |

This is evidence of what current artifacts support, not a UX design.

---

## W. Persistence-strategy evidence (no winner chosen)

### A. Scan replay files directly

- **Metadata availability:** strong for `result.json` (Tier 2, small,
  standalone, present for essentially every completed match); weak/absent
  for anything requiring Tier 3/4 (territory, timeline, elimination
  detail).
- **Load cost:** measured directly against this repository's real local
  corpus (Section L) — Tier 1 (~10 s for 106k files), Tier 2
  (~24 s extrapolated for all 53,458 `result.json` files), Tier 3
  (tens of minutes extrapolated for all 44,645 `replay.jsonl` files at full
  parse). **A Tier-2-only scan (result.json + filesystem stat) is
  plausibly cheap even at real, already-observed local scale; a Tier-3
  scan of every replay is not.**
- **Replay-count scaling:** this repository's own developer machine already
  holds 44,645 real replay files and 53,458 real result files locally —
  "hundreds/thousands of replays" is not a hypothetical edge case for at
  least some real users of this exact product; it is the observed present
  state of one contributor's checkout.
- **Historical-format handling:** direct scanning naturally accommodates
  mixed-era files (each read independently, tolerant per-file error
  handling per Section O), unlike an index that would need explicit
  schema-version-aware ingestion logic.

### B. Rebuildable metadata index/cache

- **What could be cached:** every Tier 1/2 field (Section Q) — path, size,
  mtime, entrant names, seed, ruleset ID + confidence, winner, termination
  reason, score, tick count. Cache entries would need a
  (path, size, mtime) or content-digest invalidation key.
- **Replay files remain authoritative:** yes, straightforwardly — the
  cache would only ever store *extracted* Tier 1/2 facts, never replace the
  replay/result files themselves, and `result_model.verify_replay_digest`
  already provides an existing, tested mechanism to detect a replay that no
  longer matches what was originally recorded, if a cache needed to
  re-validate.
- **Invalidation/rebuild feasibility:** straightforward in principle
  (mtime/size change → re-extract), since Tier 2 extraction cost is already
  measured as cheap (Section L).

### C. SQLite metadata store

Capabilities that would justify it, evaluated against actual evidence
rather than assumed:

- **Filtering/sorting across thousands of entries:** this repository's real
  local corpus already has tens of thousands of files — this is not a
  hypothetical justification here, unlike a system that has never been
  observed at that scale.
- **Deduplication:** directly useful given Section P's finding that
  `match_id`/`replay_id` are deterministic content hashes — a SQL `WHERE
  match_id = ?` query is a natural fit for detecting "this exact match
  content already has an entry," something repeated directory scanning
  cannot do without maintaining its own in-memory index anyway.
- **Notes/tags, schema evolution:** would require new storage regardless of
  index-vs-scan choice (Section T), but a database naturally accommodates
  schema evolution (new columns) more gracefully than a hand-rolled JSON
  index file would.
- **Thousands of entries:** already true today for this repository (Section
  L), not merely a future-scaling hypothetical.

### Directly relevant existing precedent in this same codebase

`battle_engine.evaluation_history` (Section discussion throughout this
report) is a **fully shipped, directly analogous system** for a sibling
artifact type (`evaluation.json`), and it already made — and measured — this
exact decision: `docs/specs/evaluation_history.md` §16 and
`ARCHITECTURE.md`'s "Evaluation History (v0.7)" section both document a
**deliberate choice of on-demand scanning with no index**, justified by a
measured benchmark (10/100/1000 synthetic artifacts: ~18 ms/~182 ms/
~1,862 ms scan+adapt time) that stayed "well under two seconds even at
1000 artifacts... beyond what a typical data root accumulates," against an
explicit stated bar: "measurements demonstrate a real requirement" before
introducing an index. **This repository's own real replay corpus (44,645
files) already exceeds evaluation_history's synthetic benchmark by roughly
45x**, and a full per-file replay parse is ~70x more expensive per file than
`evaluation_history`'s own (already 5x-slower-than-raw-parse) full
typed-adaptation cost. Phase 6 should treat this precedent as directly
informative — reusing its shallow-scan, per-file-error-tolerant,
health-coded discovery pattern is very plausibly the right starting point
for a Tier-1/2-only replay scan — while explicitly re-measuring at replay
scale before assuming its "no index needed" conclusion also holds for
replays, since replay's Tier-3 cost profile is measurably worse than
evaluation's typed-adaptation cost and this repository's own replay
population is already an order of magnitude larger than evaluation_history's
benchmark population.

No option is recommended as a winner here — Phase 6's job is to weigh this
evidence, not this report's.

---

## X. Open architectural questions for Phase 6

1. Is "replay identity" for history purposes content-identity (today's
   `match_id`, which collides on identical reruns) or occurrence-identity
   (which nothing currently tracks)? (Section P)
2. If a stable occurrence UUID is added, does it live in the replay schema
   (a real schema-version bump, explicitly prohibited this phase) or
   entirely in an external index/database that never touches the replay
   file? (Sections P, T, W)
3. Is a match timestamp added to the schema (again, a real schema change),
   recorded only in an external index at first-discovery time (which is not
   "match time," only "first-seen-by-the-browser time"), or left as an
   explicitly-labeled, caveated filesystem-mtime-only feature indefinitely?
   (Section G)
4. Does Phase 6 adopt `evaluation_history`'s shallow-scan/no-index pattern
   as-is for Tier 1/2 replay facts, or does this repository's measured
   larger real-world scale (Section L/W) justify a cache/index from the
   start rather than waiting for a future measured problem?
5. Should a history browser present `runs/_loose`'s single-slot,
   overwrite-prone default path specially (e.g. a warning that only the
   most recent bare `bytefray run` survives), given it is structurally
   unable to hold history at all?
6. How should ruleset-identity confidence (`recorded`/`recovered`/`unknown`)
   and entrant-identity confidence (era-dependent field availability) be
   surfaced in a list/detail UI without overwhelming an ordinary user who
   just wants to see recent matches?
7. Should preset-name reconstruction be attempted at all (heuristic,
   unreliable, Section J), or should the browser commit to showing only
   resolved parameter values, full stop?
8. Does closing the "product/engine version" gap (Section T) belong in the
   replay/result schema, or should it follow `evaluation.json`'s existing
   `execution_contexts` precedent as a lower-risk, already-proven pattern
   in this exact codebase?
9. What is the intended behavior for a `result.json` that exists without
   its referenced replay (pruned, moved, or never verified) — is a
   history row still shown from `result.json` alone (this report's evidence
   suggests yes, since `result.json` is self-sufficient for Tier 2 facts),
   and how is that distinguished in the UI from a fully-intact pair?

---

## Y. Files changed

**Added:** this report,
`docs/research/v5/V5_REPLAY_HISTORY_PHASE5_DISCOVERY.md`.

**Modified:** none (executable source, tests, schemas, manifests, packaging
inputs, and all pre-existing Phase 4 documentation edits already present in
the working tree at the start of this phase — Section A — were left
untouched).

**Deleted:** none.

**Temporary/non-tracked:** one read-only Python probe script was written to
this session's scratchpad directory (outside the repository) to measure
scan cost against the real local `runs/` corpus (Section L); it never
touched any repository file, was never staged, and was deleted after use.

---

## Z. Recommended Phase 6 scope

**Phase 6: Replay History persistence/index architecture design (design
only, still no implementation)** — resolve the open questions in Section X
using this phase's evidence as direct inputs:

1. Decide content-identity vs. occurrence-identity for "what counts as one
   history entry," informed by Section P.
2. Decide the storage strategy (direct scan / rebuildable cache / SQLite)
   using Section W's evidence — including re-measuring Tier 1/2/3 scan cost
   at this repository's own already-observed real scale (not only a fresh
   synthetic benchmark), since that scale already exceeds every existing
   in-codebase precedent.
3. Specify exactly which fields a first history-browser slice would surface
   from Section R/S without any schema change, and which (if any) justify
   a future, separately-reviewed schema addition per Section T.
4. Specify the corrupt/unsupported-file policy (Section O) as a concrete
   decision, using `evaluation_history.discovery`'s existing pattern as the
   starting point.
5. Specify how a selected history row hands off to the *existing* Replay
   Viewer launch path (Section M's `open_pygame_client_direct`/
   `build_replay_command`) without modifying playback architecture.
6. Explicitly decide whether a timestamp/UUID schema addition is in scope
   for a near-term phase or deferred indefinitely — do not let Phase 6 drift
   into implementing one without this being a deliberate, separately
   reviewed decision (per this phase's own prohibition on schema changes).

Do not implement any browser UI, index, cache, or database in Phase 6
either, unless the user explicitly re-scopes it as an implementation phase.

---

## Validation

- `git diff --check`: clean (no whitespace-conflict-marker errors) against
  the only change this phase makes (this new file).
- `git diff --stat` / `git status --short` at completion: identical to the
  starting state in Section A, plus this one new untracked file — no
  executable source, test, schema, manifest, or packaging input was
  touched.
- No replay, result, agent, or ruleset file was created, modified, or
  deleted by this phase's own actions. (The real `runs/` corpus used for
  Section L's measurement was only *read*; nothing in it was created,
  modified, or deleted by the read-only probe script, which opened files
  strictly in read mode and performed no writes.)
- The one temporary script this phase created lived entirely outside the
  repository (this session's scratchpad directory) and was deleted after
  use — never staged, never tracked.
