# Bytefray V5 — Phase 6: Replay History Architecture & Product Design

Date: 2026-09-11. **Architecture and product design complete; documentation
only. Replay History was not implemented.**

This report turns the measured findings in
[Phase 5](V5_REPLAY_HISTORY_PHASE5_DISCOVERY.md) into an implementation-ready
design. It also uses the compatibility constraints recorded in the
[Phase 4 release-surface audit](V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md),
the repository [architecture](../../../ARCHITECTURE.md), the
[result contract](../../RESULT_SCHEMA.md), the
[replay contract](../../REPLAY_SCHEMA.md), and the existing
[Evaluation History specification](../../specs/evaluation_history.md).

The central decision is:

> Replay History is a browser of artifact-backed **match occurrences**.
> `result.json` is the normal metadata authority, replay availability is a
> capability of an occurrence, and a rebuildable SQLite index provides fast
> access without owning or replacing any match artifact.

The planned index is disposable derived state. Deleting it must never delete,
rewrite, invalidate, or make an otherwise playable replay unusable.

## A. Starting state

| Item | Observed value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD | `95de2b4abcdb0e1e01c79a8db860a11aff8c88f7` |
| Upstream | `origin/v5-research` |
| Ahead / behind | `0 / 0`, measured from the local tracking ref; no fetch was performed |
| Working tree | Clean: `git status --short` produced no output |
| Product version | `5.0.0a1`, from `pyproject.toml` |
| Phase 4 | Committed in `7944f7b5d9e82b7448c2843141c4a6204fe32513`; commit content includes the Phase 4 report and its six related documentation updates |
| Phase 5 | Committed at HEAD, `95de2b4abcdb0e1e01c79a8db860a11aff8c88f7`; commit content is the Phase 5 discovery report only |

The commit-content checks above are authoritative even though the two local
commit subjects do not describe their contained phase files consistently.
No prior uncommitted work needed separation. No executable change was present
or authorized at the start of Phase 6.

## B. Phase 5 evidence used

Phase 6 relies on these measured or source-proven facts rather than repeating
the broad inventory:

- Every completed native VM or Python match reaches
  `match_service._finalize_native_artifacts`, which calls the one canonical
  `battle_engine.replay.write_replay` serializer and writes a sibling
  `result.json` atomically after publishing the replay.
- pMARS/Redcode writes a valid `battle2.result` envelope with `replay: null`.
  A match result can therefore be complete even when native replay playback is
  not a capability.
- `result.json` is small and carries list-level outcome, entrant, ruleset,
  seed, configuration, and replay-reference metadata. Reading it does not
  verify or require the referenced replay.
- Full replay parsing is intended for playback. Phase 5 measured about
  31.7 ms per sampled replay versus about 0.447 ms per sampled result, a
  roughly 70-fold per-file difference.
- The local `runs/` corpus already contained 106,170 files, 53,458
  `result.json` files, and tens of thousands of replays. A raw full walk took
  about ten seconds in Phase 5.
- `replay_id == match_id`. The value is a deterministic semantic identity,
  not an execution-occurrence identity. Identical independent reruns share it.
- No ordinary result or replay persists an occurrence UUID, match timestamp,
  Bytefray product version, or selected parameter-preset identity.
- `_designer` and `agents_test` directory names contain a UTC timestamp and a
  random suffix, but those names are storage conventions rather than a common
  persisted occurrence contract. `_loose` overwrites one fixed slot.
- Current replay playback reconstructs recorded state without running agent
  code. Exact rerun requires more information and live source than a seed.
- `evaluation_history.discovery` establishes the correct failure-isolation
  precedent: one malformed artifact becomes a health-coded entry and never
  aborts sibling discovery.
- Existing Viewer handoff is
  `app.services.engine_commands.open_pygame_client_direct` to
  `battle_engine.launchers.build_replay_command`; it launches the established
  Replay Viewer with `--replay <path>`.

The current-corpus Phase 6 benchmark in Section I supersedes Phase 5's
extrapolation for the exact list-building workload.

## C. History object decision

### Alternatives

| Model | Strengths | Failures against current workflows |
|---|---|---|
| A — replay file | Direct correspondence with the Viewer; easy playback action | Excludes complete pMARS and result-only matches; makes a deleted replay erase useful outcome history; treats playback storage as the product object; forces expensive parsing for replay-only metadata |
| B — completed match artifact directory | Fits Designer, Development, Tournament, Evaluation, and result-led metadata; keeps a result when replay is pruned | Cannot represent a historical or manually copied replay that lacks `result.json`; a directory is storage, not stable occurrence identity |
| C — hybrid occurrence record | A valid result normally anchors completion and cheap metadata; replay is an optional capability; replay-only historical artifacts can appear as degraded entries | Requires explicit health states and separate occurrence/location identity |

### Decision

Select **Model C**.

One normal row represents one completed match occurrence anchored by a valid
`result.json`. Its replay reference can be available, missing, absent by
design, unreadable, or invalid. A canonical `replay.jsonl` with no result can
still create a degraded replay-only entry, with outcome fields left unknown
unless the user requests a more expensive read.

The domain object must keep three concepts separate:

1. `match_id`: deterministic execution-input identity;
2. `occurrence_id`: one actual execution, when future metadata records it;
3. `location_id`: an index-local identity for one discovered artifact
   location.

Legacy rows lack `occurrence_id`; they are still real history entries. The
browser does not invent certainty from a path or deterministic hash.

Failed or cancelled execution that publishes neither a final result nor a
final replay is not a match-history entry. Temporary files and empty run
directories are ignored. This browser is not an execution-job log.

## D. Metadata authority model

`result.json` is the primary list metadata source. The replay is not parsed
when a valid result already answers the field. Replay-header fallback is used
only for replay-only or invalid-result entries, and terminal replay parsing is
lazy because it consumes the stream.

| Field | Authoritative source | Fallback | Reliability | Extraction cost |
|---|---|---|---|---|
| Occurrence timestamp | Future `result.json.completed_at` | Recognized timestamp-bearing run-directory name; then result/replay filesystem mtime; then unknown | Recorded / inferred / filesystem fallback / unknown | Cheap result parse or stat |
| Match ID | `result.json.match_id` | Replay header `match_id` | Recorded when present; absent on old replays | Cheap; first replay line only for fallback |
| Occurrence ID | Future `result.json.occurrence_id` | None; `location_id` is explicitly not a substitute | Recorded or unknown | Cheap |
| Result ID | `result.json.result_id` | Replay header `result_id` | Recorded when present | Cheap |
| Entrant names and IDs | `result.json.entrants[]` | Replay header `entrants[]`, then legacy header `agents` | Era-dependent but directly recorded | Cheap; header-only fallback |
| Entrant hashes | `result.json.entrants[].metadata` | Replay header `entrants[].metadata` | Recorded only in eras/runtime kinds that produced them | Cheap; header-only fallback |
| API and agent versions | `result.json.entrants[].metadata` | Replay header entrant metadata | Not applicable to VM; unknown for older Python artifacts | Cheap; header-only fallback |
| Ruleset ID | `result.json.ruleset_id` through `resolve_result_ruleset` | Replay header through `resolve_replay_ruleset` | Recorded, recovered, not applicable, or unknown | Cheap; header-only fallback |
| Seed | `result.json.reproducibility.seed` | Replay header config/reproducibility | Directly recorded across supported replay eras | Cheap; header-only fallback |
| Core/arena size | `result.json.reproducibility.arena_size` | Replay header `config.arena_size` | Directly recorded when present | Cheap; header-only fallback |
| Tick limit, action budget, win mode, weights, locality reach | `result.json.reproducibility` | Replay header config/reproducibility | Era- and ruleset-dependent | Cheap; header-only fallback |
| Resolved Agent Params | `result.json.entrants[].metadata.parameters` | Replay header entrant metadata | Recorded values only; absent means unknown/not used | Cheap; header-only fallback |
| Preset identity | Future per-entrant result metadata only | None; never infer from equal resolved values | Unknown until explicitly persisted | Cheap when added |
| Winner/result | `result.json.winner` | Terminal replay result, loaded lazily | Direct from result; unknown for header-only replay | Cheap from result; full replay traversal for fallback |
| Score | `result.json.score` | Terminal replay result, loaded lazily | Direct from result | Cheap from result; full replay traversal for fallback |
| Termination reason and ticks | `result.json` | Terminal replay result, loaded lazily | Direct from result | Cheap from result; full replay traversal for fallback |
| Replay reference and expected digest | `result.json.replay` | Canonical sibling `replay.jsonl` for replay-only entries | Result reference is recorded; sibling inference is location-bound | Cheap |
| Replay availability | Current filesystem state of the safely resolved replay path | None | Current existence/readability observation, not proof of validity | `stat`; digest verification is explicit and deferred |
| Replay path | Result reference resolved beneath the result directory | Canonical sibling path for replay-only entry | Location-bound; rechecked before use | Cheap |
| Product version | Future `result.json.product_version` | Unknown | Recorded or unknown | Cheap |
| Workflow/source | Path relative to `<data-root>/runs`, refined by known layout | `external` for an explicitly opened path | Derived and may become unknown after a move | Cheap string classification |
| Result/replay schema | Each artifact's own schema fields | None | Directly recorded | Cheap; header-only for replay |
| File size/mtime | Filesystem metadata | None | Exact filesystem facts but not match semantics | Cheap stat |

The index stores a derived projection of these fields. A selected row's detail
view rereads its artifact, and an Open action rechecks the replay path and
integrity. Cached values never authorize mutation or playback by themselves.

## E. Identity model

### Match identity

Keep current `match_id` semantics unchanged. It identifies deterministic
execution inputs, including the resolved ruleset, reproducibility block, and
entrant content identities. Independent deterministic reruns correctly share
the same `match_id`. The browser may group or filter by this value but must
never use it as a row-uniqueness key.

### Occurrence identity

Future writers should generate a random UUID for every completed execution
and persist it as `result.json.occurrence_id`. The UUID is generated once for
the execution, is opaque, and is independent of path, timestamp, match ID,
result ID, replay ID, and outcome. A fresh rerun gets a fresh occurrence UUID
even when every deterministic byte and `match_id` are identical.

This model provides:

- uniqueness between real reruns;
- stability when a run directory is moved;
- detection of one occurrence copied to multiple locations;
- no change to deterministic matching/resume identities;
- one implementation for native and pMARS result writers.

The occurrence UUID, completion time, and product version must **not** enter
the `match_id`, `result_id`, or `replay_id` hash recipes. Those existing IDs
must retain their semantic/deterministic purpose.

Existing Designer/Development directory UUIDs are not adopted as the
occurrence contract: they do not exist in every layout, can be lost on move,
and identify a storage directory rather than a field in the artifact.
`timestamp + path`, a run label, and a content/path composite fail the same
stability or semantic test.

### Location identity

The cache computes `location_id` from the canonical scan-root identity and
normalized relative artifact path. It is only a database primary key for a
location. It can change when a legacy directory moves and must never be shown
as if it were a persisted occurrence UUID.

## F. Timestamp model

### Future artifacts

The History `Date` means **match completion time**. A future writer captures
one UTC timestamp immediately after execution produces its final outcome and
before replay/result serialization begins, then writes it to
`result.json.completed_at` in RFC 3339 form with an explicit `Z`/UTC offset.
It is not replay-write completion, first index observation, or filesystem
creation time.

Completion time is preferable to start time for V1 because:

- the result artifact proves a completed outcome;
- both native and pMARS paths have one unambiguous completion boundary;
- only one field is needed for chronological history;
- it avoids implying that wall-clock duration can be reconstructed.

### Legacy fallback order

1. valid embedded `completed_at`: confidence `recorded`;
2. a UTC timestamp parsed from a known `_designer` or `agents_test` naming
   convention: confidence `directory_inferred`;
3. `result.json` mtime, or replay mtime for replay-only entries: confidence
   `filesystem_fallback`;
4. no usable value: confidence `unknown`.

Evaluation creation time and tournament parent-directory identity are not
substituted for a per-match completion time. Cache `first_seen_at` may be kept
for diagnostics but is never displayed as match time.

The row converts a valid timestamp to the user's local timezone. Inferred and
mtime dates receive an `≈` marker and a tooltip such as “Approximate: inferred
from run folder” or “Approximate: filesystem modification time.” Unknown dates
display `Unknown`. Sorting uses the best available instant newest-first,
places unknown values last, and uses `location_id` as the stable tie-breaker.

## G. Schema evolution decision

The browser can and should evolve through the result artifact while leaving
replay schemas 3 and 4 unchanged. Playback does not need occurrence-management
metadata, and changing every tick-stream consumer would add risk without user
value.

The current `battle2.result` v1 contract has tolerated additive fields in past
releases. The repository's current governing guidance nevertheless requires a
schema version change to be explicit. Phase 7A should therefore introduce
`battle2.result` **version 2**, update readers to accept both versions 1 and 2,
and update the result contract before the browser lands. Version-2 current
writers require the new occurrence fields; version-1 readers remain the
historical path.

| Field | Classification | Artifact | Decision and reason |
|---|---|---|---|
| Occurrence UUID | **REQUIRED BEFORE HISTORY IMPLEMENTATION** | `result.json` v2, top level | Needed to distinguish identical reruns and recognize copied locations. Unknown for v1 history. |
| Completion timestamp | **REQUIRED BEFORE HISTORY IMPLEMENTATION** | `result.json` v2, top level | Gives History an authoritative Date semantic. Existing artifacts use labeled fallbacks. |
| Product version | **SHOULD ADD WITH HISTORY** | `result.json` v2, top level | Useful compatibility/debug context and cheap to record while v2 is introduced; not required to list or play an entry. |
| Preset identity | **NICE LATER** | Future per-entrant result metadata | A preset is per entrant and represents user selection intent. It requires provenance to survive request resolution; never infer it from matching values. |

For all four fields, the replay artifact decision is **DO NOT ADD** for the
initial browser. Result-only pMARS occurrences also receive occurrence UUID,
completion time, and product version in v2. A replay copied without its result
continues to be supported as a degraded entry with these fields unknown.

Phase 7A must characterize result v1/v2 reads across tournament/evaluation
resume and every result consumer. It must also prove that adding nondeterministic
occurrence metadata leaves existing deterministic IDs unchanged.

## H. Discovery roots and eligibility

### Root policy

The automatic root is one recursive, non-symlink-following scan of:

```text
<resolved data root>/runs
```

This includes all durable current and future match workflows without a
hard-coded registry:

| Location | Policy | Reason |
|---|---|---|
| `runs/_designer` | Include automatically | Per-run durable Designer artifacts |
| `runs/agents_test` | Include automatically | Per-run Development artifacts |
| `runs/tournaments` | Include automatically | Default tournament match artifacts |
| `runs/evaluations` | Include automatically | Evaluation cell result/replay artifacts |
| Other directories beneath `runs` | Include automatically when they contain an eligible artifact | Captures research and custom outputs already kept under the canonical run tree; the measured corpus proves this is substantial real history |
| `runs/_loose` | Include conditionally when an eligible artifact currently exists | It is a real current occurrence, but Source displays `CLI latest` and detail warns that the default slot is overwritten; the index never preserves an overwritten row after reconciliation |
| User-selected path outside `runs` | Manual/open-only in V1 | No existing persistent root setting or ownership boundary exists; an explicitly selected result/replay can be shown for the session |
| External file copied beneath `runs` | Include automatically if it has a recognized canonical name/state | It has entered the user's run tree |
| Agent/resource/cache/source directories | Exclude automatically | They are not run-artifact roots |

The scanner recognizes candidate directories containing exact canonical names
`result.json` or `replay.jsonl`. It does not parse every `*.jsonl`; that would
mistake traces and research streams for replays. Explicitly opened external
replays may use another filename because the user selected the file directly.

### Eligibility and row states

| Artifact state | History behavior | Replay action |
|---|---|---|
| Valid completed result + referenced replay exists | `complete / replay present (unverified)` | Enabled after click-time path/integrity preflight |
| Valid completed result + `replay: null` | `complete / no replay produced` | Disabled; expected for pMARS |
| Valid completed result + referenced replay missing | `complete / replay missing` | Disabled; result metadata remains visible |
| Valid result + replay digest mismatch discovered by verification | `complete / replay invalid` | Block launch and show diagnostic until the file changes |
| Canonical replay without result | `replay only` | Enabled after path check; header metadata may populate degraded fields |
| Malformed/unsupported result | `invalid metadata` row for its location | A safely located sibling replay can still be offered as replay-only/degraded |
| Malformed/unsupported replay with valid result | Keep result row as `replay invalid` when known | Disabled when known invalid; otherwise the Viewer owns parser errors |
| Inaccessible candidate | Health-coded inaccessible/stale row or scope diagnostic | Disabled until accessible |
| Temporary atomic-write file only | Ignore | None |
| Directory with neither final result nor final replay | Ignore as in-progress, cancelled, or failed job | None |

Current native finalization publishes the replay and then atomically publishes
`result.json`; result appearance is therefore the normal completion signal.
A scanner that observes file size/mtime changing between its pre-read and
post-read stat treats the file as transient and retries on the next refresh.

## I. Direct-scan benchmark

### Method

A temporary read-only Python probe was created under `work/`, run against the
existing ignored `runs/` corpus, and deleted before completion. It used Python
3.13.14 on Windows 11 (`10.0.26120`, 64-bit AMD64; storage cache state was not
controlled). It did not write beneath `runs`.

For each pass the probe:

1. recursively walked the selected roots with `os.walk(...,
   followlinks=False)`;
2. selected exact `result.json` names;
3. performed `stat` and one `json.load`;
4. checked `battle2.result` v1 and required list fields;
5. built a compact in-memory projection containing paths, IDs, entrants,
   ruleset, seed, arena, outcome, workflow, replay reference/availability,
   and timestamp fallbacks;
6. sorted by result mtime newest-first;
7. ran entrant-text, ruleset, winner, and replay-availability filters 21
   times; and
8. serialized and reparsed a compact JSON representation to estimate the
   cost of a monolithic file cache.

The first full pass enabled `tracemalloc`, which materially raises allocation
and parsing cost. The immediate repeat did not track allocations and is the
better warm/repeat direct-scan result. The “cold-ish” label means first probe
pass only; the OS disk cache was not flushed.

### Results

| Measurement | Full corpus, cold-ish + allocation tracking | Full corpus, immediate repeat | Product-owned roots (`_designer`, `_loose`, `agents_test`, `tournaments`, `evaluations`) |
|---|---:|---:|---:|
| Files visited | 106,170 | 106,170 | 238 |
| Candidate `result.json` | 53,458 | 53,458 | 88 |
| Valid / invalid | 53,458 / 0 | 53,458 / 0 | 88 / 0 |
| Directory errors | 0 | 0 | 0 |
| Discovery | 5.516 s | 3.732 s | about 0.014 s |
| Parse + projection | 38.592 s | 13.993 s | about 0.039 s |
| Sort | 0.014 s | 0.014 s | under 0.001 s |
| Total through sort | **44.122 s** | **17.739 s** | **about 0.053 s** |
| Four representative filters, median | 0.231 s with allocation tracking | 0.070 s | about 0.00028 s |

The full projection encoded to **35,219,205 bytes** (about 33.6 MiB) as
compact JSON. In the allocation-tracked pass, encoding took 2.153 s, reparsing
took 1.230 s, current traced allocation after the round trip was about
158.9 MiB, and peak traced allocation was about **241.7 MiB**. This peak
includes the live projection, encoded string, and parsed round-trip copy; it is
not a steady-state cache-size claim. It nevertheless demonstrates the memory
shape of loading a monolithic JSON index and thousands of Python dictionaries.

A separate one-pass inventory found 44,547 exact `replay.jsonl` files and no
replay-only canonical directory in this corpus. Replay-only compatibility is
still required for imported and historical artifacts.

### Interpretation

- Direct result scanning is excellent at the 88-entry current product-root
  scale.
- Sorting and filtering an already-loaded 53k collection are cheap.
- Recursive discovery plus parsing is not acceptable as a blocking browser
  open at the complete real-corpus scale, even on an immediate repeat.
- Scanning only named product roots would hide more than 53,000 valid run
  results already held beneath other `runs/` directories. The architecture
  should index the complete canonical run tree rather than define “ordinary”
  history by today's folder names.
- A monolithic JSON projection is fast enough to be plausible, but it loads
  the whole collection and duplicates substantial memory during parsing. A
  paged database has concrete value here, independent of speculative future
  features.

## J. Persistence architecture comparison

All three strategies leave result/replay artifacts authoritative. “Initial
scan” is the same filesystem work; persistence changes repeat-open and query
behavior.

| Criterion | Direct artifact scan | Rebuildable JSON/file index | Rebuildable SQLite index |
|---|---|---|---|
| Implementation complexity | Low | Medium | Medium-high |
| Initial scan speed | Same measured 17.7–44.1 s at 53k | Same, plus one atomic index write | Same, plus transactional upserts |
| Repeat-open speed | Repeats full scan | Reads cached projection; measured representation is 35.2 MB | Reads only first page and query results |
| 100k+ scaling | Poor open latency; all entries materialized | Acceptable disk size but increasing parse/heap pressure | Best of the three; keyset pages and indexed filters avoid loading all rows |
| Search/filter | Fast only after full memory load | Fast after full cache load; streaming complicates arbitrary queries | Natural parameterized queries over indexed row fields/entrants |
| Rebuildability | Intrinsic | Delete and regenerate | Delete and regenerate |
| Migration burden | None | Version header; replace on mismatch | Internal schema version; drop/rebuild on mismatch, not user-data migration |
| Corruption recovery | Per-artifact only | Ignore/delete corrupt index and rescan | Close/delete corrupt database and rescan |
| Concurrent processes | Independent scans | Atomic replace prevents torn file, but last writer can publish a stale snapshot | SQLite locking/WAL gives one refresh writer with concurrent cached readers |
| Portability | Maximum | High; human-readable | High enough for derived state; artifacts, not the DB, are portable |
| Debuggability | High | Highest cache introspection | Requires SQLite inspection/log export |
| Packaging/dependency cost | None | None | `sqlite3` is Python standard library; no new dependency |
| Future tags/notes | Requires separate authoritative store | Must use a separate authoritative store because cache is deletable | Could host queries, but user-authored data still must not live only in this deletable cache |

Direct scan is retained as the rebuild mechanism, not the foreground browsing
architecture. A JSON index is simpler, but the measured 35.2 MB projection and
241.7 MiB instrumented round-trip peak show a real cost to its all-at-once
object model. SQLite is justified by observed scale, paging, and query needs,
not merely by feature possibility.

Phase 6 did not create a SQLite database. Phase 7B must measure actual database
size, ingest time, first-page latency, and filter latency before accepting the
implementation.

## K. Selected persistence architecture

Use a **rebuildable SQLite metadata index** with these invariants:

- Results/replays remain the only authority for match facts and playback.
- The database stores no replay timeline, agent source, or irreplaceable user
  content.
- Removing the database causes a background rebuild and no history loss.
- Browser open reads a small cached page immediately, then starts background
  reconciliation.
- Detail selection rereads the authoritative result/replay header as needed.
- Open Replay rechecks the path and, where available, the result's recorded
  digest before launching the existing Viewer.

### Logical cache records

The internal schema should have:

- a metadata table containing cache schema version, extractor version,
  normalized data-root identity, and last completed refresh;
- an entries table keyed by `location_id`, with relative result/replay paths,
  fingerprints, occurrence/match/result IDs, time plus confidence, outcome,
  ruleset plus provenance, seed, arena/config summary, workflow, replay state,
  health, and product version;
- an ordered entrants table keyed by `(location_id, ordinal)`, carrying ID,
  display name, API/agent version, content hash, and normalized search text;
  and
- indexes for effective time, occurrence ID, match ID, ruleset, winner, seed,
  workflow, replay state, and entrant lookup.

Rich parameters, score, and diagnostics may be stored as derived JSON columns
for quick detail display, but the selected detail view rereads the result so
cache contents cannot silently become authority.

The GUI queries a default page of 500 rows using keyset pagination over
`(timestamp-known, effective_timestamp, location_id)`, not a widget per row
and not an unbounded `OFFSET` walk. Unknown dates sort last.

## L. Refresh/invalidation model

### Browser open

1. Open/validate the cache off the GUI thread.
2. Emit the first cached page and show `Refreshing…`.
3. Claim the single refresh-writer slot.
4. Walk `<data-root>/runs` once, considering exact `result.json` and
   `replay.jsonl` names.
5. Reuse a projection when the artifact fingerprint is unchanged; parse only
   new/changed candidates.
6. Commit one coherent refresh generation.
7. Requery the visible page and clear the refresh indicator.

The result fingerprint is canonical relative path, size, and nanosecond mtime.
The replay fingerprint includes referenced relative path, existence, size, and
nanosecond mtime. These are cache-invalidation hints, not integrity claims.
Click-time digest verification remains the integrity boundary. A future
diagnostic “force rebuild” may ignore fingerprints; it is not required in the
main MVP controls because deleting a corrupt cache already rebuilds it.

### Change handling

| Change | Reconciliation behavior |
|---|---|
| New result/replay | Insert a new location row after stable read |
| Result metadata changed | Reparse and replace derived fields |
| Replay added/restored | Change replay state to present/unverified |
| Replay deleted | Keep result entry; mark replay missing |
| Result deleted, replay remains | Convert location to replay-only on refresh |
| Both artifacts deleted | Remove the location after successful enumeration of that scope |
| Directory moved | Remove old location and add new location; a recorded occurrence UUID connects duplicate/same-occurrence evidence |
| Artifact copied | Add a location; duplicate policy in Section N applies |
| File changes during read | Do not publish that extraction; retry next refresh |

V1 uses automatic reconciliation on browser open and a manual **Refresh**
button. It does not use filesystem watchers, periodic polling, or engine-writer
notifications. A CLI or external copy made while the dialog stays open appears
after Refresh. Designer-created matches appear the next time History opens;
the current History dialog is modal, so no new Designer match can start behind
it. This avoids coupling match finalization to a GUI index service.

### Multiple processes

Use SQLite WAL mode with a short busy timeout. A refresh worker obtains a
`BEGIN IMMEDIATE` writer transaction before scanning and holds it through the
generation update. Other processes continue reading the prior committed
snapshot; another refresher that cannot obtain the writer slot reports “using
cached history; another Bytefray process is refreshing” and does not fail the
browser. A crash rolls back the incomplete generation.

## M. Invalid/corrupt artifact policy

The non-negotiable rule is:

> One bad artifact must never prevent valid history from appearing.

Per-candidate errors are caught and converted to stable health codes plus a
short diagnostic. The browser never quarantines, rewrites, moves, or deletes a
run.

| Problem | Row behavior |
|---|---|
| Malformed JSON / wrong JSON root | `invalid metadata`, with path and parse diagnostic |
| Missing required result field | `invalid metadata`; use safe replay-header fallback if a canonical sibling exists |
| Unsupported result/replay schema | `unsupported artifact`; preserve path and version in detail |
| Unknown ruleset string | Display verbatim with recorded provenance; not corruption |
| Missing ruleset on supported old artifact | Use existing recovered/unknown confidence rules |
| Missing replay | Keep complete result row, replay state `missing` |
| Digest mismatch | Keep result row, replay state `invalid`, show expected/actual diagnostic without changing files |
| Unreadable file/directory | Preserve any prior cached row as stale and add an inaccessible diagnostic; continue siblings |
| Replay parser failure | Keep result metadata; mark replay invalid when the failure is known |

Normal discovery does not hash or fully parse every replay. A present replay is
initially `present / unverified`. A result-backed Open action performs digest
verification in the background. A replay-only artifact without a recorded
digest is handed to the existing Viewer after a path check; the Viewer's
existing parser/error screen remains authoritative for malformed content.

Diagnostics should include health code, artifact path, exception category,
and a bounded message. They should be visible in detail and log output without
showing a modal dialog for every bad sibling.

## N. Duplicate/occurrence policy

MVP shows all discovered artifact locations. It does not collapse rows and it
does not hash every replay during discovery.

- Same `match_id`, different recorded `occurrence_id`: legitimate independent
  deterministic reruns. Show separate rows.
- Same future `occurrence_id` at multiple paths: copied/moved occurrence
  locations. Show each row and mark `duplicate occurrence location`; do not
  choose or delete a canonical copy.
- Same `match_id`, no occurrence IDs: identity is ambiguous. Show all rows and
  do not label them duplicates solely from `match_id`.
- Replay-only copies: show all locations. Defer content-hash deduplication.
- A moved future occurrence may transiently show two locations from the stale
  cached page until reconciliation commits; the refreshed view resolves it.

This mirrors Evaluation History's “duplicate identity location” honesty while
preserving the crucial distinction that deterministic match identity is not
execution identity.

## O. MVP row specification

Use a virtualized `QTableView`/`QAbstractTableModel` with these exact columns:

| Column | Display | Source/fallback |
|---|---|---|
| **Date** | Local date and time; prefix `≈` for inferred/mtime values; `Unknown` last | Section F timestamp chain |
| **Entrants** | Ordered display names joined with `vs`; fall back to entrant IDs, then `Unknown` | Result entrants, then replay header |
| **Result** | Winner display name, `Tie`, `Unknown`, or `Invalid metadata` | Result winner; terminal replay only when already loaded |
| **Ruleset** | Exact ruleset ID, `N/A`, or `Unknown`; tooltip carries recorded/recovered confidence | Result resolver, then replay resolver |
| **Seed** | Decimal integer or `Unknown` | Result reproducibility, then replay header |
| **Source** | `Designer`, `Development`, `Tournament`, `Evaluation`, `CLI latest`, `Other run`, or `External` | Derived from location |
| **Replay** | `Available`, `Missing`, `Not produced`, `Invalid`, or `Unknown` | Result reference plus current filesystem/verification state |

Health appears as a row icon/accent and tooltip rather than an eighth text
column. It is never conveyed by color alone. The full score belongs in detail,
not the row.

Default ordering is newest effective occurrence time first, unknown dates
last, then `location_id` for deterministic ties. The initial query returns 500
rows with **Load more**/incremental fetch. It does not silently discard older
entries.

## P. Detail view specification

The detail pane is a structured presentation, not a raw JSON inspector.

### Essential

- health/status and bounded diagnostic;
- completion date/time, timezone, confidence, and fallback source;
- ordered entrant display names and IDs;
- winner/tie, per-entrant score, termination reason, and ticks run;
- ruleset ID and provenance confidence;
- seed, core/arena size, tick limit, action budget, win mode, weights, and
  locality reach when present;
- workflow/source; and
- replay state with **Open Replay** and **Copy Seed** actions when eligible.

### Useful compatibility and reproduction facts

- occurrence ID or `Unknown (legacy)`;
- match ID and result ID;
- per-entrant runtime kind, API version, agent version, content/source hash,
  start/slot metadata, and resolved Agent Params;
- product version or `Unknown (legacy)`;
- result schema/version and replay schema/version when known; and
- preset identity only in a future artifact that explicitly records selection.

### Advanced/debug

- absolute result and replay paths;
- result/replay byte size and filesystem mtime, explicitly labeled as
  filesystem metadata;
- replay ID, expected SHA-256, and verification status;
- raw mode/backend metadata;
- structured entrant diagnostics/statistics; and
- timestamp and ruleset confidence codes.

Timeline, territory, elimination, and full replay analysis remain in Replay
Viewer. History does not precompute them.

## Q. Search/filter MVP

The first browser includes these controls because each supports a concrete
history/debugging task and has metadata/index support:

| Control | Exact behavior | Metadata/index implication |
|---|---|---|
| Entrant search | Case-insensitive substring over entrant display name and agent ID | Entrants table/search text; no source loading |
| Ruleset | Exact recorded/recovered ID, plus `Unknown` and `N/A` | Indexed normalized ruleset and provenance |
| Result/winner | Any, Tie, Has winner, Unknown/invalid, or one indexed winner/entrant ID | Indexed winner/status |
| Date range | Uses best available timestamp; approximate legacy rows remain marked; unknown dates are excluded only while a range is active | Indexed effective timestamp and confidence |
| Seed | Exact integer | Indexed seed |
| Workflow/source | One or more source categories | Indexed derived workflow |
| Replay state | Available, Missing, Not produced, Invalid, Unknown | Indexed/reconciled state |

Filters compose and run as parameterized database queries in the worker
thread. Results replace/reset the table model without rebuilding widgets.
Text input is debounced. Preset search, hashes, free-text paths, tags/notes,
score ranges, and timeline facts are deferred.

## R. Replay Viewer handoff

History reuses the current path exactly:

```text
selected entry
  -> app.services.engine_commands.open_pygame_client_direct(data_root, replay_path)
  -> battle_engine.launchers.build_replay_command(replay_path, flags)
  -> existing detached Replay Viewer process
```

No playback code or Viewer UX is redesigned.

Click behavior is:

1. Resolve the replay only from the entry's current, containment-checked
   artifact path.
2. Recheck that it is a readable file.
3. If a valid result carries a replay digest, resolve its filename with
   `contained_path` and run `verify_replay_digest` against that safe path in
   the History worker thread. The current `verify_result_replay` convenience
   helper assumes the writer's documented bare filename and is therefore not
   the boundary for an untrusted, hand-edited result.
4. On success, call `open_pygame_client_direct` on the GUI side and retain its
   existing renderer/tick-delay/trace behavior.
5. Catch `FileNotFoundError` and `OSError`, show one concise Designer message,
   and update the row's session state.

Specific states:

- **Replay exists and verifies:** launch normally.
- **Replay was deleted after indexing:** do not launch; mark Missing and ask
  the user to Refresh or restore the file.
- **Result-backed replay digest fails:** keep the row, mark Invalid, show the
  integrity diagnostic, and do not launch mismatched bytes as that result's
  replay.
- **Replay-only artifact:** existence-check and launch; the Viewer's existing
  parser reports malformed/unsupported content in its own UI.
- **Complete result with no replay:** disable Open Replay and explain “This
  workflow did not produce a native replay.”
- **Process launch fails:** surface the `open_pygame_client_direct` error;
  retain the entry and replay state because a launcher failure does not imply
  artifact corruption.

## S. Re-run / Copy Seed disposition

**Re-run Match: defer.** The current artifacts do not guarantee that the
original agent source still exists or matches its recorded hash. Product
version is absent historically, preset selection is lost, and ruleset/config
availability does not restore deleted executable agent content. A button named
Re-run Match would overstate reproducibility.

**Copy Seed: include in V1** when an integer seed is available. It copies only
the decimal seed and states no exact-rerun guarantee. Disable it for unknown
seeds. Do not synthesize a command or silently load current catalog agents.

A future exact rerun feature requires an explicit contract for archived agent
content/revisions, ruleset implementation availability, all resolved match
configuration, entrant order/start values, and version provenance. That is a
separate product design.

## T. Product placement

V1 belongs in the **Agent Designer**, reachable as **Tools → Replay History…**
beside the existing Evaluation History browser. This extends the current flow
to:

```text
Design -> Battle -> History / Replay -> Analyze
```

Designer already owns data-root context, detached Viewer launch error handling,
and match/evaluation history-adjacent workflows. The existing **View Last
Match** shortcut remains useful and does not become a second history system.

Do not put V1 inside Replay Viewer: the Viewer is a playback consumer, its
Pygame picker intentionally has no history/search model, and making it own the
index would invert the clean engine/app/client boundary. Do not add a new
standalone command/application for the first slice. A later Viewer shortcut to
open the Designer-owned browser can be considered after the model is proven.

### Empty state

With no cached or discovered entry, show:

> No match history yet. Completed matches saved under `<data-root>/runs` will
> appear here.

Provide **Refresh**, **Run a Match** (return focus to Designer), and
**Open Replay File…** for one explicit external file. Explain in secondary
text that the plain CLI's default `_loose` location retains only its latest
run; History cannot recover an overwritten artifact.

### Large-history behavior

- Show the window and cached first page before reconciliation completes.
- Use a virtual table/model and 500-row keyset pages.
- Show total matching count, loaded count, refresh progress, and stale status.
- Query filters against the index; never create one Qt widget per occurrence.
- Keep the prior committed snapshot usable during refresh.
- Allow cancellation on dialog close and at file/directory boundaries.
- Do not impose a permanent “last N” data-loss limit; 500 is a view page.

## U. Responsiveness/threading requirements

The invariant is:

> History discovery, parsing, digest verification, database access, and filter
> queries must not freeze the GUI.

Use one Qt worker object on a `QThread`, following PySide queued-signal
ownership. A process is unnecessary because history reads trusted local data
and executes no agents. `QProcess` remains the boundary for match/agent
execution; it is not an I/O task abstraction.

The worker creates and owns its SQLite connections. It emits immutable row
DTOs, counts, progress, and bounded diagnostics to the GUI. The GUI thread owns
only `QAbstractTableModel` state and widgets. Cancellation is cooperative
between directories/files and before expensive verification. Closing the
dialog must not wait synchronously for a corpus-wide scan.

Existing Evaluation History currently discovers synchronously and uses
`QListWidget`; its error-isolation model is precedent, but its threading and
row-widget approach are not copied at 53k-match scale.

## V. Cache/database lifecycle

### Location and ownership

Use:

```text
<resolved data root>/cache/replay_history/index-v1.sqlite3
```

Bytefray has no separate established cache-root resolver. Keeping the index
beneath the same resolved `BYTEFRAY_ROOT` scopes it to exactly the run tree it
indexes, works for source/portable/installed layouts, and keeps it outside
individual run directories. The `cache` directory is application-derived
cache data, not user match data.

The installer does not precreate the database. History creates it lazily. It
need not be backed up or exported with matches. If uninstall preserves the
data root, leaving the cache is harmless; if the data root is removed, losing
the cache loses no match. Reinstall/open recreates it.

### Versioning and rebuild

- Use SQLite `user_version` plus a metadata/extractor version.
- A normalized data-root mismatch, unsupported cache version, corrupt header,
  or failed integrity/open check closes and rebuilds the cache.
- Prefer drop/rebuild over cache migrations because every field is derived.
- Do not invalidate solely because Bytefray's product version changed. Bump
  the extractor version only when supported artifact interpretation or cached
  projection semantics change.
- Keep WAL/journal sidecars in the same cache directory; all are disposable.
- Never store tags, notes, or any future user-authored fact only in this
  rebuildable database.

## W. Backward compatibility

- No historical result or replay is rewritten or migrated.
- The future result reader accepts `battle2.result` v1 and v2. Missing v2
  occurrence/time/version fields become unknown/fallback states.
- Existing replay reader support for unversioned v0.1, schema 2, schema 3,
  and schema 4 remains unchanged.
- A replay playable today remains playable through the same Viewer path; the
  browser adds no ruleset-execution dependency to playback.
- Ruleset and entrant identity use recorded/recovered/unknown confidence rather
  than guessed certainty.
- A schema-2/legacy replay-only row can show available header facts while
  leaving match/occurrence IDs, winner, and rich entrant metadata unknown.
- Mixed result v1/v2 and replay generations coexist in one index refresh.
- Cache schema changes rebuild only the cache, never artifacts.
- Legacy mtime/date fallback is labeled approximate and is never promoted into
  a persisted match timestamp.
- Future result v2 metadata does not enter deterministic ID recipes.

The replay schema remains unchanged. Result schema evolution is a separate,
explicit Phase 7A change with its own compatibility tests and documentation.

## X. Failure/recovery model

The general recovery direction is **rebuild/rescan from authoritative
artifacts**.

| Failure | Required recovery |
|---|---|
| Cache deleted | Open empty/progress UI and rebuild in background |
| Cache corrupt or wrong version/root | Close it, remove/rename derived files when possible, and rebuild; if removal is blocked, use an in-memory session view and report the cache problem |
| Cache stale | Show cached rows with `Refreshing…`; reconcile artifacts and commit a new generation |
| Result deleted | If replay remains, transition to replay-only; otherwise remove after a successful scan of that scope |
| Replay deleted | Keep result history, mark Missing, and disable Open |
| Run directory moved | Add new location/remove old; preserve future occurrence identity from the result; legacy location identity changes honestly |
| Permission error | Continue accessible siblings; retain prior rows under the inaccessible scope as stale rather than treating them as deleted; show one bounded scope diagnostic |
| Partial match directory | Ignore temp-only state; show health-coded result/replay if a malformed final-name artifact exists |
| Refresh interrupted or process crashes | Roll back transaction and continue using the previous committed generation |
| Concurrent refresh | One writer proceeds; the other process reads the committed cache and reports that refresh is already active |
| Database write/disk-full failure | Keep scanned rows for the current session if memory permits, retain prior committed database, and report that cache persistence failed |
| Artifact changes during parse | Discard that extraction and retry on next refresh |

Deletion cleanup is scoped to directories that were successfully enumerated.
An access failure must not masquerade as a confirmed deletion.

## Y. Security/trust considerations

History scanning treats artifacts as malformed input even though they are local.

- Never import or execute agent modules to display identity or metadata.
- Walk with `followlinks=False`; reject candidate resolutions that escape the
  configured root unless the user explicitly opened that external artifact.
- Resolve a result's replay filename beneath its own directory using the
  existing `contained_path` discipline; reject absolute, drive-qualified,
  `..`, and symlink escapes.
- Read `result.json` with a 4 MiB scan limit and a replay-header line with a
  1 MiB limit. Oversized metadata becomes a health-coded entry. Full replay
  size is not bounded for playback; it simply is not consumed by discovery.
- Catch `OSError`, Unicode/JSON errors, schema/type errors, and unexpected
  per-artifact adaptation errors without aborting siblings.
- Bound diagnostic length before storing/displaying it.
- Use parameterized SQL and treat every artifact string as data.
- Do not follow paths embedded in entrant metadata or load current catalog
  agents for search/detail.
- Digest verification reads bytes only and runs in the worker thread.

The 4 MiB and 1 MiB discovery limits are deliberately generous for the small
current result/header shapes. Phase 7B fixtures should prove ordinary maximum
artifacts remain well below them before freezing the constants.

## Z. Performance acceptance criteria

These targets are based on the measured 88-entry and 53,458-entry results.
SQLite-specific timings remain Phase 7B acceptance measurements because this
phase was prohibited from creating a database.

| Scenario | Acceptance criterion | Evidence/rationale |
|---|---|---|
| Window open | Window and controls paint without waiting for discovery; no corpus operation runs on GUI thread | Full direct scan is 17.7–44.1 s and cannot be an open-time block |
| Cached first page at ~50k | First 500 rows visible within **1.0 s** on the benchmark machine | Even the 35.2 MB JSON projection reparsed in 1.23 s with allocation tracking; paged SQLite must improve on the all-at-once shape |
| Current product roots with no cache | First useful rows within **0.25 s** | Measured full parse/sort was about 0.053 s, leaving roughly 4.7x UI overhead margin |
| Complete 53k refresh | Finish within **25 s warm** and **60 s cold-ish/instrumented** on the benchmark machine, entirely in background | Direct warm measured 17.739 s; tracked cold-ish measured 44.122 s |
| Cached sort/filter at ~50k | Updated first page within **0.25 s** after debounce | Four full in-memory filters measured 0.070 s; indexed/paged query must stay within a visible-interaction budget |
| Table memory | Qt model holds at most the loaded pages, initially 500 rows; it must not instantiate 53k row widgets | Probe's monolithic round trip peaked near 241.7 MiB |
| Progress/cancellation | Show progress when refresh exceeds 1 s; closing remains responsive and cancellation is observed between candidates | Required by measured full-scan duration |
| Replay verification | Runs off GUI thread and reports progress/cancel for unusually large files | Verification hashes full replay bytes |

Phase 7B must also report database bytes, ingest/upsert time, first-page
cold/warm latency, query latency for every MVP filter, and memory at 1k, 10k,
50k, and at least 100k synthetic metadata rows. Missing a numerical target is
an implementation blocker, not a reason to weaken the no-freeze invariant.

## AA. Recommended architecture summary

- **History object:** one artifact-backed match occurrence; valid result is
  normal, replay-only is degraded, replay is an optional capability.
- **Authority:** `result.json` for cheap match/outcome metadata, replay for
  playback and replay-only fallback, filesystem only for current location and
  explicitly labeled legacy time fallback.
- **Discovery:** recursively scan exact canonical artifacts beneath
  `<data-root>/runs`; allow one session-explicit external artifact.
- **Metadata:** parse one result; parse only the first replay record when result
  fallback is needed; never load all timelines for list discovery.
- **Identity:** keep deterministic `match_id`; add a random persisted
  `occurrence_id` in future result v2; keep index `location_id` separate.
- **Time:** persist UTC `completed_at` in result v2; directory/mtime fallbacks
  are approximate.
- **Persistence:** rebuildable SQLite cache under
  `<data-root>/cache/replay_history/`; artifacts remain authoritative.
- **Refresh:** cached first page, automatic background reconciliation on open,
  manual Refresh, no watcher/writer coupling in V1.
- **Errors:** health-code each bad artifact/scope; never abort valid siblings or
  mutate runs.
- **Duplicates:** separate identical reruns by occurrence UUID; mark copied
  UUID locations; never collapse equal match IDs.
- **Playback:** click-time path/digest preflight, then the existing
  `open_pygame_client_direct`/`build_replay_command` path.
- **Compatibility:** result v1/v2 mixed reads, current historical replay reads,
  no artifact migration, no replay-schema change.
- **GUI:** Designer Tools dialog, `QThread` worker, virtual table, 500-row
  keyset pages, indexed filters.

## AB. Implementation decomposition

### Phase 7A — result occurrence metadata contract

Land this first so every match created while the browser is being developed
already has stable occurrence/time provenance.

- Specify and implement `battle2.result` v2.
- Add required `occurrence_id` and `completed_at`, plus `product_version`, to
  native and pMARS writers.
- Read v1 and v2; preserve unknown values for v1.
- Prove existing deterministic `match_id`, `result_id`, and `replay_id` values
  do not incorporate the new fields.
- Characterize tournament/evaluation resume and all result consumers.
- Update `docs/RESULT_SCHEMA.md`; do not change replay schema.

### Phase 7B — Qt-free history discovery and index service

- Add a `battle_engine.replay_history` domain package with DTOs, health codes,
  timestamp/ruleset provenance, bounded adapters, root traversal, and SQLite
  cache ownership.
- Reuse `result_model` and replay-header adapters rather than duplicating wire
  semantics.
- Implement generation transactions, fingerprints, deletion scoping,
  concurrency, corruption rebuild, and explicit external-artifact reads.
- Add focused mixed-era/corrupt/missing/moved/copied/permission tests.
- Run the database and 1k/10k/50k/100k acceptance benchmark before proceeding.

### Phase 7C — History Browser model and UI

- Add Qt-free Designer presentation adapters plus a `QThread` worker.
- Add the virtual table, structured detail pane, exact filters, empty state,
  progress/cancellation, and 500-row keyset fetching.
- Add **Tools → Replay History…** without changing existing Evaluation History
  or View Last Match behavior.
- Use GUI-marked tests for model/wiring; keep parsing/index tests headless.

### Phase 7D — Viewer handoff and Copy Seed

- Implement click-time contained-path and background digest preflight.
- Reuse `open_pygame_client_direct` and its current error handling.
- Add Copy Seed with no rerun claim.
- Qualify missing/deleted/mismatched/replay-only/launcher-failure paths.

### Phase 7E — performance and historical compatibility qualification

- Exercise the real 53k corpus and synthetic 100k metadata corpus.
- Test cache deletion/corruption/staleness/interruption and two-process access.
- Test result v1/v2 plus unversioned/schema-2/3/4 replay fixtures.
- Run headless suite, relevant mypy/ruff, GUI CI/manual smoke, and packaged
  Windows Viewer handoff.
- Confirm no agent code executes during discovery and no run artifact changes.

## AC. Open questions

The core architecture is resolved. Two bounded questions remain for later
qualification/product work:

1. What SQLite page size and exact query/index layout give the best measured
   packaged-GUI behavior? Phase 7B starts with 500 rows and may tune the page
   size without changing authority, identity, or persistence architecture.
2. Should a later release persist user-registered external history roots or
   copy imports into a managed run area? V1 deliberately supports session-only
   external Open and does not create a new settings/ownership contract.

Tags/notes, preset search, exact rerun, filesystem watching, and Viewer-hosted
navigation are explicitly deferred features, not unresolved V1 architecture.

## AD. Files changed

Added only:

```text
docs/research/v5/V5_REPLAY_HISTORY_PHASE6_ARCHITECTURE.md
```

No production source, tests, schemas, manifests, packaging files, run
artifacts, caches, indexes, or databases were changed. The temporary benchmark
script was deleted. No Replay History implementation, schema change, version
bump, commit, or push occurred in Phase 6.
