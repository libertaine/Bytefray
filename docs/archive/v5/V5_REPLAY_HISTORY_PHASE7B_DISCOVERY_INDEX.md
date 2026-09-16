# Bytefray V5 — Phase 7B: Replay History Discovery & SQLite Index Service

Date: 2026-09-11. **The complete non-GUI Replay History backend is
implemented, measured against the real 53,458-result corpus, and qualified.
No Replay History UI, Qt code, or thread was written.**

This phase turns the [Phase 6 architecture](V5_REPLAY_HISTORY_PHASE6_ARCHITECTURE.md)
and the [Phase 7A result metadata contract](V5_REPLAY_HISTORY_PHASE7A_RESULT_METADATA.md)
into a working, independently testable service:

> artifact discovery → normalized occurrence model → rebuildable SQLite index
> → reconciliation → filtering/querying → keyset paging → recovery and
> performance qualification.

Artifacts remain the only authority. The SQLite database is derived,
disposable state; deleting it loses no history, and nothing in this phase ever
writes, renames, moves, or migrates a match or replay artifact.

---

## A. Starting state

| Item | Recorded value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD at start | `6b1e27242794febbf1e03689d0c7825ca9d8aaa5` |
| Upstream | `origin/v5-research` |
| Ahead / behind | `0 / 0` |
| Working tree at start | **Clean** — `git status --short` produced no output |
| Product version | `5.0.0a1` (`pyproject.toml`); `project_info.get_project_info()` reports `version='5.0.0a1', agent_api_version=2, result_schema_version=2, replay_schema_version=4, python_version='3.13.14'` |
| Phase 7A relationship | Phase 7A **is** the starting HEAD (`6b1e272`, `feat(v5): add result occurrence metadata for replay history`). Its report, the v2 `result_model` changes, the v1 fixture, and the `result_schema_version=2` runtime value are all present and verified. |

No unrelated user work existed to preserve. No commit, push, stage, reset,
version bump, or release was performed.

---

## B. Architecture implemented

A new Qt-free package, `battle_engine.replay_history`, sits beside the
existing `battle_engine.evaluation_history` package and follows the same
boundary discipline (domain model → adapters → discovery → callable service).

| Module | Responsibility |
|---|---|
| `replay_history/models.py` | Domain model and typed state vocabulary: `HistoryOccurrence`, `HistoryEntrant`, `ArtifactFingerprint`, the five health/state enums, identity derivation (`location_id`, `synthetic_occurrence_key`), and `bounded_diagnostic`. No I/O, no SQL. |
| `replay_history/discovery.py` | The single read-only run-tree walk, workflow classification, timestamp fallback chain, result/replay adaptation, bounded reads, path-safety checks, and `ScanScope` completeness tracking. |
| `replay_history/index.py` | All SQLite: schema, pragmas, transactions, cache open/validate/recover, bulk write, deletion, duplicate marking, keyset paging, filter translation. Nothing above this module builds SQL. |
| `replay_history/query.py` | The read-side contract shared by index and callers: `HistoryQuery`, `HistoryCursor`, `HistoryRow`, `HistoryPage`, `HistoryDetail`, `ReplayResolution`, and the summary/counter types. |
| `replay_history/service.py` | `ReplayHistoryService`: the whole public façade — open/close, rebuild, reconcile, page, count, detail, replay resolution. |
| `replay_history/__init__.py` | Curated public exports. |

Dependency direction is one-way (`service → index → query → models`,
`service → discovery → models`) and the package depends only on
`battle_engine.{paths, replay, result_model, rules}` plus the standard
library. No dependency was added: persistence is Python's bundled `sqlite3`.

Deliberately **not** created: one oversized `replay_history.py`, an ORM
layer, a Qt adapter, or a second result parser.

---

## C. Domain occurrence model

`HistoryOccurrence` is the one normalized record produced by discovery and
persisted by the index. It stores typed values and enums, never presentation
strings — display formatting belongs to Phase 7C.

| Group | Fields |
|---|---|
| Identity | `location_id`, `occurrence_key`, `occurrence_source`, `occurrence_id`, `match_id`, `result_id` |
| Time | `effective_timestamp` (ISO-8601 UTC), `effective_timestamp_ns`, `timestamp_known`, `timestamp_confidence`, `completed_at` |
| Entrants | ordered `entrants` tuple of `HistoryEntrant` (`ordinal`, `agent_id`, `display_name`, `runtime_kind`, `api_version`, `agent_version`, `content_hash`, `parameters`); derived `entrant_count`, `entrant_summary`, `entrant_search` |
| Match | `ruleset_id`, `ruleset_confidence`, `seed`, `mode`, `configuration` (the result's `reproducibility` block: arena size, tick limit, action budget, win mode, weights, entrant order), `workflow`, `durable_location` |
| Outcome | `winner`, `outcome_state`, `score`, `termination_reason`, `ticks` |
| Artifact state | `relative_directory`, `result_fingerprint`, `replay_fingerprint`, `replay_state`, `replay_sha256`, `replay_id`, `result_health`, `entry_health`, `diagnostic_category`, `diagnostic_message` |
| Versioning | `result_schema_version`, `product_version`, `replay_schema_version` |

`ArtifactFingerprint` carries `relative_path`, `exists`, `size`, `mtime_ns` —
the reconciliation signature, explicitly *not* an integrity claim.

### The three identities stay separate

* `match_id` — deterministic semantic match identity. Independent reruns
  legitimately share it, so it is **never** a row-uniqueness key. It is
  exposed as a filter, not as identity.
* `occurrence_id` — one actual execution. Authoritative for `battle2.result`
  v2 only; `None` for v1.
* `location_id` — the index-local key of one discovered artifact *directory*
  (`loc_<sha256(root identity ␀ relative directory)[:24]>`). Keying on the
  directory rather than on a particular artifact file is what lets a row stay
  continuous when its `result.json` is deleted and only the replay survives.

---

## D. Legacy v1 handling

### Synthetic occurrence identity

A v1 artifact has no authoritative occurrence UUID, so the index assigns

```text
legacy-location_<sha256(root identity ␀ relative directory)[:24]>
```

with `occurrence_source = synthetic_location`. It is:

* deterministic for the same discovered location;
* distinct from `match_id` and from the `loc_` namespace;
* **not UUID-shaped**, so it can never be mistaken for a v2 `occurrence_id`
  (a test asserts `uuid.UUID(key)` raises);
* never written back to `result.json` or any other artifact;
* able to keep two byte-identical v1 reruns in separate directories as two
  separate occurrences — the exact fact `match_id` cannot express.

### Timestamp fallback

Phase 6 Section F's chain, with the confidence preserved on every row and
never promoted to artifact truth:

| Order | Source | Confidence | Applies to |
|---|---|---|---|
| 1 | `result.json.completed_at` (v2) | `recorded` | v2 native results |
| 2 | UTC stamp parsed from a known run-directory name | `directory_inferred` | `runs/_designer/<YYYYMMDD-HHMMSS>-…` and `runs/agents_test/<agent>/<YYYYMMDDTHHMMSS%f>-…` |
| 3 | `result.json` mtime (replay mtime for a replay-only row) | `filesystem_fallback` | everything else with a usable stat |
| 4 | none | `unknown` (`timestamp_known = 0`, sorts last) | nothing usable |

Directory parsing is strict and layout-scoped: an unparseable or
wrong-shaped name yields `None` rather than a guess, and only the two layouts
that genuinely encode a UTC stamp are attempted. `product_version` stays
`None` for v1; nothing is inferred from the currently running build.

`result_model` was not changed to fabricate `completed_at`. This is Replay
History normalization behavior only.

---

## E. SQLite schema

Cache schema version **1** (`PRAGMA user_version` plus a `cache_metadata`
row), extractor version **1**.

### `cache_metadata`

`key TEXT PRIMARY KEY, value TEXT NOT NULL` — holds `cache_schema_version`,
`extractor_version`, `root_identity`, `generation`, and
`last_refresh_completed_at`.

### `occurrence` (primary key `location_id`)

`relative_directory`, `occurrence_key`, `occurrence_id`, `occurrence_source`,
`match_id`, `result_id`, `timestamp_known`, `effective_timestamp_ns`,
`effective_timestamp`, `timestamp_confidence`, `completed_at`,
`entrant_count`, `entrant_summary`, `entrant_search`, `winner`,
`outcome_state`, `score_json`, `termination_reason`, `ticks`, `ruleset_id`,
`ruleset_confidence`, `seed`, `mode`, `configuration_json`, `workflow`,
`durable_location`, `result_exists`, `result_size`, `result_mtime_ns`,
`replay_filename`, `replay_exists`, `replay_size`, `replay_mtime_ns`,
`replay_state`, `replay_sha256`, `replay_id`, `result_health`,
`entry_health`, `diagnostic_category`, `diagnostic_message`,
`result_schema_version`, `product_version`, `replay_schema_version`,
`duplicate_occurrence_location`, `first_seen_at`, `last_seen_generation`.

### `occurrence_entrant` (primary key `(location_id, ordinal)`)

`agent_id`, `display_name`, `runtime_kind`, `api_version`, `agent_version`,
`content_hash`, `parameters_json`, with
`REFERENCES occurrence(location_id) ON DELETE CASCADE`.

Normalization was applied only where it pays for itself:

* **Entrants are a child table** because the detail panel needs ordered,
  structured per-entrant facts. Entrant *search* uses a denormalized
  lowercase `entrant_search` column on the parent instead, so a substring
  filter is one single-table scan rather than a correlated subquery.
* **Artifact paths are not stored twice.** `result.json` is the only name
  discovery ever anchors on, so its run-relative path is derived from
  `relative_directory`; only the replay's own *filename* is stored. Removing
  those two duplicated ~150-character columns cut the 53k-row cache from
  119.5 MB to 99.8 MB and removed a second copy of state that could drift.
* Score, configuration, and entrant parameters are compact JSON columns —
  detail-display payloads that no filter queries into.

### Pragmas and transaction model

| Setting | Value | Reason |
|---|---|---|
| `foreign_keys` | `ON` | The entrant child table's cascade must actually fire. |
| `journal_mode` | `WAL` (falls back silently to the default journal if the filesystem refuses it) | Readers keep serving the last committed generation while one refresh writer commits the next. |
| `synchronous` | `NORMAL` | Adequate durability for derived state; the worst case of a power loss is a rebuild. |
| `busy_timeout` | 5000 ms | A second Bytefray process waits briefly rather than failing. |
| Writer transactions | `BEGIN IMMEDIATE` … `COMMIT`/`ROLLBACK` | Claims the single writer slot before scanning, per Phase 6 Section L, so a conflict is detected up front rather than after a whole corpus walk. |

The connection uses `isolation_level=None`, so transaction boundaries are
explicit rather than implicit. Rebuild and reconcile are each **one**
transaction: an interrupted, failed, or cancelled refresh rolls back
completely and leaves the previously committed generation intact and queryable.
This is deliberately *not* optimized for uncontrolled multi-process writers —
Phase 6 specifies one background refresh worker.

---

## F. Cache location and lifecycle

```text
<resolved data root>/cache/replay_history/index-v1.sqlite3
```

resolved through the established `battle_engine.paths.get_data_root()`; no
developer path is hard-coded. The database never lives inside a run directory,
and the installer was not touched.

Lifecycle rules:

* **Disposable.** Deleting the file (and its `-wal`/`-shm` sidecars) loses no
  history; the next open rebuilds from artifacts.
* **Rebuild, not migrate.** A `user_version` mismatch, an extractor-version
  mismatch, a different indexed `root_identity`, or an unreadable database
  closes the cache, removes it with its sidecars, and recreates it. Every
  column is derived, so there is no user data to migrate.
* **Version independence.** The cache schema version is independent of
  `battle2.result`'s schema version, the replay schema version, and the
  product version. A Bytefray version change alone never invalidates the
  cache; the extractor version is what moves when interpretation changes.
* **Never the only home for anything.** Tags, notes, and any future
  user-authored fact must not live only here.
* `/cache/` was added to `.gitignore`: in a source checkout the data root is
  the repository itself, so an accidental default-path run would otherwise
  leave an untracked 100 MB database in the tree.

Tests and benchmarks always pass an explicit temporary cache path (or
`in_memory=True`), so no real user cache was created during this phase —
verified: no `cache/` directory exists at the repository root.

---

## G. Discovery

One recursive, non-symlink-following `os.walk` of `<data-root>/runs`, keyed
on the two exact canonical names `result.json` and `replay.jsonl`. Arbitrary
`*.jsonl` files are never treated as replays, and no replay is parsed while
walking.

### Workflow classification

Structural, from the run-relative path, with stable internal identifiers
(display labels belong to the GUI):

| Location | `WorkflowSource` | Durable |
|---|---|---|
| `runs/_designer/…` | `designer` | yes |
| `runs/agents_test/…` | `development` | yes |
| `runs/tournaments/…`, or any path containing a `tournaments` segment | `tournament` | yes |
| `runs/evaluations/…`, or any path containing an `evaluations` segment | `evaluation` | yes |
| `runs/_loose` | `cli_latest` | **no** |
| any other subtree beneath `runs` | `other_run` | yes |
| the run root itself | `unknown` | yes |

Research and custom output trees resolve to `other_run` rather than being
excluded — in the measured corpus that is where more than 53,000 of the
53,458 real results live. Source is never guessed from anything but structure;
`unknown` exists precisely so a guess is never necessary.

### `_loose` disposition — the decision, stated explicitly

`runs/_loose` is **included** as the current `cli_latest` occurrence, marked
`durable_location = False`, and carries the diagnostic
`loose_slot_overwritten` ("The plain CLI default slot keeps only its most
recent run; an overwritten match cannot be recovered.").

This implements Phase 6 Section H's conditional-include intent exactly.
Because `_loose` is a single fixed location, its `location_id` is stable, so
an overwrite *updates that one row in place* — the index structurally cannot
accumulate stale overwritten `_loose` rows, which is the property Phase 6
asked for. Excluding it would hide a real, current match the user just ran;
treating it as durable would imply a history depth that slot does not have.
The `_loose` writer itself was not changed in any way.

### Result parsing

There is one result parser. `result_model.read_result` was refactored
(behavior unchanged) to delegate to a new additive
`result_model.result_from_mapping(data)`, which Replay History calls with the
payload it already read. That avoids both a second, drifting parser and a
second read of every file, while letting discovery classify malformed JSON
apart from an unsupported schema version *before* adaptation.

* **v2** → authoritative `occurrence_id`, `completed_at`, `product_version`.
* **v1** → synthetic occurrence key, confidence-qualified timestamp,
  `product_version` unknown.
* No migration, no rewrite, no inference.

### Result-only and replay-only entries

* A valid `result.json` with no readable replay is a complete history
  occurrence. `replay_state` records why (`missing`, `not_produced`,
  `invalid`, `inaccessible`) and the row is never dropped. Replay
  availability is a capability, not an eligibility condition.
* A directory holding `replay.jsonl` with **no** `result.json` becomes a
  degraded replay-only row. This is discovered in the *same single walk* at
  no extra directory cost, so no second recursive pass and no broad replay
  scan is needed. Only the first header line is read (bounded at 1 MiB) to
  recover `match_id`, `result_id`, `replay_id`, entrants, seed/config, ruleset
  provenance, and replay schema version. The terminal outcome record is
  deliberately *not* searched for — that would mean streaming every replay in
  the tree — so such rows are always `INCOMPLETE` with unknown outcome.

The measured corpus contains 44,547 `replay.jsonl` files and **zero**
replay-only directories, so this path costs nothing in practice while
remaining fully supported for imported and historical artifacts.

---

## H. Health and corruption model

Five typed vocabularies replace ad-hoc booleans.

**`ResultHealth`** — `valid`, `malformed`, `unsupported`, `inaccessible`,
`missing`.
**`ReplayState`** — `available`, `missing`, `not_produced`, `invalid`,
`inaccessible`, `unchecked`.
**`EntryHealth`** — `healthy` (valid result, replay available or never
produced), `degraded` (valid result, replay missing/invalid/unreadable),
`incomplete` (no `result.json` at this location), `invalid` (result present
but uninterpretable).
**`TimestampConfidence`** — `recorded`, `directory_inferred`,
`filesystem_fallback`, `unknown`.
**`OccurrenceIdentitySource`** — `recorded`, `synthetic_location`.

A bounded `DiagnosticCategory` plus a ≤300-character message records *why*:

| Condition | Result health | Category |
|---|---|---|
| `OSError` opening the result | `inaccessible` | `result_unreadable` |
| Result larger than the 4 MiB scan limit | `malformed` | `result_too_large` |
| JSON/Unicode decode failure | `malformed` | `result_malformed_json` |
| JSON root is not an object | `malformed` | `result_invalid_root` |
| `schema` is not `battle2.result` | **`unsupported`** | `result_unsupported_schema` |
| `schema_version` outside the supported set | **`unsupported`** | `result_unsupported_version` |
| Adaptation rejects a field (e.g. a malformed v2 UUID) | `malformed` | `result_invalid_fields` |
| Referenced replay absent | valid | `replay_missing` |
| Replay reference escapes its own run directory | valid, replay `invalid` | `replay_reference_unsafe` |
| Replay-only header unreadable / not a header | `missing` | `replay_header_unreadable` |
| No `result.json` at the location | `missing` | `result_missing` |

Two properties are load-bearing:

* **One bad artifact never aborts global discovery.** Every failure becomes a
  row or a bounded diagnostic; discovery continues with siblings.
* **An unsupported future version is classified apart from malformed JSON**,
  keeps its full path and diagnostic context, and remains eligible for a
  correct rebuild after a software upgrade — the file itself never changes.

Diagnostics are bounded twice: each message is collapsed and truncated to 300
characters, and the per-pass unreadable-directory list stops at 50 entries.
No traceback and no raw artifact content is ever persisted.

---

## I. Full rebuild

```text
BEGIN IMMEDIATE
  DELETE occurrence_entrant; DELETE occurrence
  DROP every secondary index
  stream:  walk → normalize → executemany in 1,000-row batches
  CREATE every index
  recompute duplicate-occurrence flags
  write generation + last-refresh metadata
COMMIT
```

**Table contents are replaced transactionally, not by swapping files.** A
cross-platform rename of an open SQLite database and its WAL sidecars is not
reliably atomic; assuming filesystem atomicity is exactly the mistake the
earlier starter-refresh work had to correct, so it is not repeated here. A
failure, an exception, or cooperative cancellation at any point rolls the
whole transaction back — indexes included, since SQLite DDL is transactional —
and the previously committed generation stays complete and queryable.

The pipeline **streams**: discovery is a generator consumed directly by the
writer, so the full corpus is never materialized. Peak process working set
for a 53,458-result rebuild was 56.1 MiB against a 32.7 MiB baseline.

Dropping secondary indexes around the bulk load and recreating them once at
the end measured 25.2 s + 0.6 s versus 31.3 s incremental — a ~6 s saving with
identical results.

### Rebuild statistics

`RebuildSummary` exposes `scanned`, `inserted`, `duration_seconds`,
`generation`, `committed`, bounded `diagnostics`, and a `ScanCounts` record
of `directories_visited`, `files_visited`, `result_candidates`,
`replay_only_candidates`, `valid_entries`, `degraded_entries`,
`incomplete_entries`, `invalid_entries`, `inaccessible_paths`,
`unreadable_directories`, `replay_available`, `replay_missing`,
`replay_not_produced`. This is service diagnostic data, not a GUI design.

### Cache corruption recovery

Opening a damaged or unreadable database raises `sqlite3.DatabaseError`,
which is caught: the file and its `-wal`/`-shm`/`-journal` sidecars are
deleted and a fresh cache is created and flagged for rebuild. If deletion is
blocked (an open handle or a hostile ACL), the service falls back to a
session-only in-memory cache and reports `persistent=False` rather than
silently pretending to persist. **No result or replay artifact is touched in
any recovery path** — verified by byte-level snapshot comparison in the
corruption test.

---

## J. Reconciliation

```text
BEGIN IMMEDIATE
  load every stored signature
  walk; for each candidate:
      fingerprint unchanged → mark seen, do not reparse
      otherwise            → normalize and upsert (added / updated / replaced)
  sweep rows not seen, but only where the scan proved absence
  recompute duplicate flags; write generation
COMMIT
```

### Fingerprint strategy

Normalized relative path, existence, byte size, and `mtime_ns` — for the
result, and for the replay the *stored* reference is re-stat'd. Nothing is
hashed: no digest of any result, and no read of any replay. The cache is an
invalidation index, not a cryptographic integrity database; real verification
stays an explicit step at the playback boundary. Measured effect: a warm
reconcile of an unchanged 53,458-result corpus reparses **zero** artifacts
and finishes in 7.4 s.

### Change handling

| Change | Behavior |
|---|---|
| New artifact | Inserted as `added`. |
| Result content changed at the same location, same occurrence key | Reparsed and **replaced in full** — every derived field is rewritten, so no stale indexed value survives. Counted `updated`. |
| Result at the same location now carries a *different* occurrence key | Counted `replaced`: this is a replacement of the artifact, not a mutation of the same execution, so the row starts fresh and does not inherit the previous occurrence's first-seen history. Two different occurrences are never merged into one row's history. |
| Replay deleted, result remains | Row preserved; `replay_state → missing`, `entry_health → degraded`, `resolve_replay` reports unavailable. **No row deletion.** |
| Result deleted, replay remains | The location converts in place to a replay-only row (`result_health → missing`, `entry_health → incomplete`), exactly as Phase 6 Section L specifies. Result-derived fields are cleared rather than left stale. |
| Both artifacts gone, directory enumerated | Row removed. |
| Directory moved (v1) | Delete + add; the synthetic key changes honestly with the location. |
| Directory moved (v2) | Delete + add, but the authoritative `occurrence_id` travels with the artifact, so the new row carries the same occurrence identity. |
| Artifact copied | A second location row appears; see Section K. |

### Inaccessible scopes — no false mass deletion

`ScanScope` records which directories were successfully enumerated and which
failed (`os.walk`'s `onerror` supplies the failing path). A stored row is
removed **only** when the scan positively proved its directory is gone:

* the directory itself was enumerated, or
* a fully reachable enumerated ancestor implies it no longer exists.

If any ancestor on the path failed to list, the row is retained and counted
as `retained_inaccessible`. If the run root itself could not be enumerated —
an unmounted share, a renamed data root — **nothing** is definitively absent
and the entire index is retained. Both directions are tested: a denied
subtree removes nothing and retains its rows, a vanished run root retains
every row (and reconciles cleanly back to `unchanged` when restored), while a
genuinely emptied directory really is removed.

`ReconcileSummary` reports `added`, `updated`, `replaced`, `unchanged`,
`removed`, `retained_inaccessible`, `duration_seconds`, `generation`,
`committed`, `scan_complete`, bounded `diagnostics`, and the same `ScanCounts`.

---

## K. Duplicate semantics

Three distinct situations, kept distinct:

| Situation | Behavior |
|---|---|
| Same `match_id`, different `occurrence_id` | Legitimate independent deterministic reruns. Separate rows, **no** duplicate marking. |
| Same authoritative `occurrence_id` at two locations | Copied occurrence. **Both rows kept**, both marked `duplicate_occurrence_location = 1`. Nothing is collapsed, chosen, or deleted. |
| Same `match_id`, no occurrence IDs (v1) | Ambiguous. Separate rows, no duplicate label — a synthetic key is location-derived and therefore unique by construction. |

The marker is recomputed over the whole table at the end of every rebuild and
reconcile, and applies **only** to `occurrence_source = recorded` rows —
authoritative UUIDs are the only evidence that can prove a copy.

---

## L. Query API

`ReplayHistoryService` is the entire surface. No caller writes SQL, sees a
column name, or knows SQLite is underneath.

| Method | Contract |
|---|---|
| `ReplayHistoryService.open(*, data_root=None, runs_root=None, cache_path=None, in_memory=False)` | Resolve run tree and cache, open/validate/recover the database. Never raises for a damaged cache. |
| `.refresh(*, force_rebuild=False, progress=None, cancel_check=None)` | The single call a UI needs: rebuilds when required (new, recovered, version/root mismatch, empty), otherwise reconciles. Returns `RebuildSummary | ReconcileSummary`. |
| `.rebuild(...)` / `.reconcile(...)` | The two operations explicitly, same keyword arguments. |
| `.fetch_page(query=None, *, cursor=None, limit=500)` | One keyset page → `HistoryPage(rows, next_cursor, has_more, page_size)`. |
| `.count(query=None)` | Total rows matching a query, across all pages. |
| `.fetch_detail(location_id)` | `HistoryDetail | None` — the full normalized occurrence plus current absolute artifact paths and `first_seen_at`. |
| `.resolve_replay(location_id)` | `ReplayResolution(state, path, expected_sha256, replay_id, diagnostic)` — re-resolves and re-checks before anything is opened. |
| `.close()` / context manager | Lifecycle. |
| `.cache_report`, `.generation`, `.row_count()`, `.is_empty()`, `.cache_size_bytes()`, `.runs_root` | Diagnostics for a status line. |

`progress(phase, count)` is called every 1,000 candidates; `cancel_check()` is
polled every 256 candidates and raises `HistoryRefreshCancelled`, which rolls
the transaction back and returns a summary with `committed=False`. No Qt
signal, no thread, no `QThread` — 7C supplies those.

---

## M. Filters

All Phase 6 Section Q MVP filters, as one typed, composable `HistoryQuery`:

| Field | Behavior |
|---|---|
| `entrant_text` | Case-insensitive substring over entrant display names **and** agent IDs, matching any entrant of a multi-entrant row. `%`, `_`, and `\` are escaped and matched literally. |
| `ruleset_ids` | Exact IDs; a `None` member matches rows with no recorded ruleset identity. Historical IDs (`bytefray-rules-1`, `-2`, `-4-alpha1`, `-4-alpha2`, `-4`) are all queryable — the index hard-codes no current-ruleset semantics. |
| `ruleset_confidences` | Separates `not_applicable` (pMARS) from `unknown`, `recorded`, `recovered`. |
| `outcome_states` | `winner` / `tie` / `unknown`. |
| `winner` | One exact recorded winner value. |
| `entry_healths` | Covers the invalid and degraded cases Phase 6 wanted reachable from the result filter. |
| `start` / `end` | Inclusive bounds on the effective history timestamp (accepts `datetime`, naive treated as UTC). Legacy fallback dates remain searchable but stay marked approximate; rows with an unknown date are excluded only while a bound is active. |
| `seed` | Exact integer. No rerun equivalence is inferred. |
| `workflows` | One or more `WorkflowSource` values — stable internal identifiers, not display labels. |
| `replay_states` | `available`, `missing`, `not_produced`, `invalid`, `inaccessible`, `unchecked`. |
| `match_id` | Groups deterministic reruns without collapsing them. |
| `occurrence_id` | Locates one authoritative execution, including its copies. |

An explicitly empty sequence means "match nothing" (a constant `0` predicate),
not "no filter"; `None` means "no filter". No FTS was introduced — a plain
indexed/searchable column measured 6 ms for a substring page over 53,458 rows,
so the complexity was not justified.

---

## N. Keyset pagination

**Ordering** (documented exactly, and what the index is built on):

```sql
ORDER BY timestamp_known DESC, effective_timestamp_ns DESC, location_id ASC
```

Newest effective timestamp first; rows with no usable date sort last;
`location_id` — the physical-location key — is the final deterministic
tie-breaker, which is what makes paging stable when many rows share a
timestamp. `effective_timestamp_ns` is `NOT NULL` (0 for unknown) so the
predicate never meets a NULL comparison.

**Cursor**: `HistoryCursor(timestamp_known, effective_timestamp_ns,
location_id)` — an internal typed value, not a serialized web-style token.
Phase 7C passes back the object it received. Forward paging is implemented;
backward paging is deferred as 7C does not need it.

**Page size**: 500 by default, clamped to `[1, 5000]`. The query fetches
`limit + 1` rows to decide `has_more` without a second statement, and
`next_cursor` is `None` when the last page is reached. No `OFFSET` is used
anywhere.

Verified across a 1,205-row corpus deliberately seeded with many repeated
timestamps: pages of 500/500/205, every row exactly once, no duplicate and no
omission across boundaries, ordering globally sorted, and replaying a cursor
against an unchanged index returns the identical page.

---

## O. Viewer-facing metadata for 7C/7D

`HistoryRow` (the table projection) carries `location_id`, `occurrence_key`,
`occurrence_id`, `occurrence_source`, `match_id`, `effective_timestamp`,
`effective_timestamp_ns`, `timestamp_known`, `timestamp_confidence`,
`entrant_summary`, `entrant_count`, `winner`, `outcome_state`, `ruleset_id`,
`ruleset_confidence`, `seed`, `workflow`, `durable_location`,
`duplicate_occurrence_location`, `replay_state`, `result_health`,
`entry_health`, `diagnostic_category`, `diagnostic_message`, plus a `.cursor`
property. That is every Phase 6 Section O column plus the health accent and
the copied-occurrence marker.

`HistoryDetail` adds the complete `HistoryOccurrence` (score, termination,
ticks, full configuration block, ordered entrants with runtime kind, API
version, agent version, content hash, and resolved parameters, product and
schema versions, artifact sizes and mtimes, bounded diagnostics), the
resolved absolute `result_path` and `replay_path`, and `first_seen_at`.

`ReplayResolution` gives 7D everything its preflight needs — current state,
containment-checked absolute path, the recorded `sha256` and `replay_id` — so
the digest check needs no second read of `result.json`. **No playback, no
digest verification, no Viewer launch, and no agent execution happens here.**

---

## P. Performance results

Real corpus, this machine (Windows 11 `10.0.26120`, AMD64, Python 3.13.14),
measured through the implemented service against the repository's own ignored
`runs/` tree with a temporary cache. The corpus was not modified.

### Corpus

| Measurement | Value |
|---|---|
| Directories | 56,411 |
| Files | 106,170 |
| `result.json` artifacts | 53,458 |
| `replay.jsonl` artifacts | 44,547 |
| Replay-only directories | 0 |
| Raw `os.walk` alone | 3.30 s |

Matches Phase 6's inventory (106,170 files / 53,458 results) exactly.

### Timings

| Scenario | Measured | Phase 6 target | Verdict |
|---|---:|---:|---|
| Full initial rebuild (walk + parse + normalize + SQLite population + index build, one transaction) | **26.06 s** (25.6–28.0 s across five runs) | 25 s warm / 60 s cold-ish | Within the cold-ish target with wide margin; ~1 s over the warm figure (see Section P's gap note) |
| Warm reconcile, no changes, 53,458 unchanged | **7.36 s** (7.4–8.1 s) | 25 s warm | **Met**, 3.4× margin |
| Cached first page (500 rows), freshly opened service | **5 ms** | 1.0 s | **Met**, 200× margin |
| Second keyset page | **5 ms** | — | — |
| Detail fetch for one occurrence | **1.2 ms** | — | — |
| `resolve_replay` | **0.5 ms** | — | — |

Discovery + normalization alone (no SQLite) is 18.6 s of the rebuild; the
`os.walk` inside it is 5.0 s; SQLite ingest plus index build is the remaining
~7 s.

### Filtered first pages (median of 5, 500-row page)

| Filter | Page | Matching rows | `count()` |
|---|---:|---:|---:|
| Entrant substring (`hunter`) | 6.1 ms | 25,296 | 41.3 ms |
| Ruleset exact | 24.8 ms | 12,782 | 0.6 ms |
| Winner = tie | 4.1 ms | 1,138 | 38.4 ms |
| Seed exact | 34.0 ms | 15,765 | 0.4 ms |
| Workflow = evaluation | 0.7 ms | 72 | 0.03 ms |
| Replay = available | **65.8 ms** (worst case) | 44,547 | 1.6 ms |
| Replay = missing | 24.2 ms | 8,911 | 0.3 ms |
| Health = degraded | 24.2 ms | 8,911 | 0.3 ms |
| Date range (30 days) | 3.9 ms | 52,785 | 4.1 ms |
| Combined (entrant + workflow + outcome) | 0.5 ms | 54 | 0.06 ms |

Every indexed filter is inside the 0.25 s target, the worst at 26% of budget.

### Database size and memory

| Measurement | Value |
|---|---|
| Cache on disk, 53,458 rows + 153,466 entrant rows + 9 indexes | **99.8 MB** (was 119.5 MB before the path-column normalization) |
| Process baseline (interpreter + imports) | 32.7 MiB |
| Peak working set during full rebuild | **56.1 MiB** (+23.4 MiB) |
| Peak working set during warm reconcile | **99.8 MiB** (+67.1 MiB, was 126.3 MiB before compacting the signature record) |
| Steady state while paging/filtering | ~50 MiB |

For comparison, Phase 6's monolithic-JSON probe peaked near 241.7 MiB on the
same corpus and produced a 33.6 MiB projection that had to be loaded whole.
The SQLite cache is ~3× larger on disk but is paged, queried, and filtered
without loading any of it.

### Performance-target assessment and the one remaining gap

| Phase 6 criterion | Status |
|---|---|
| Cached first page at ~50k within 1.0 s | **Met** — 5 ms |
| Product-root scale with no cache within 0.25 s | **Met** — the 88-entry product-owned roots are a strict subset of the 26 s full-corpus rebuild; the equivalent product-root-only pass is milliseconds |
| Indexed filters within 0.25 s | **Met** — worst 65.8 ms |
| 53k refresh within 25 s warm | **Met for the warm refresh that actually runs in the product** (reconcile, 7.4 s). A *full rebuild* — which only occurs on first open or cache loss — is 26.1 s, about 1 s over the 25 s figure |
| 53k refresh within 60 s cold-ish | **Met** — 26.1 s, 2.3× margin |
| All corpus work off the GUI thread | Backend contains no Qt assumption preventing worker execution; the threading itself is 7C |

The ~1 s full-rebuild gap is characterized rather than papered over. It was
profiled, not guessed: the original 58.2 s rebuild was reduced to 26.1 s by
two measured fixes (Section Q), and the residual is dominated by genuine
per-file I/O — 53,458 opens and reads plus 106,917 `stat` calls. Closing it
further would require concurrency inside the scan, which is deliberately out
of scope for a synchronous backend and would be the wrong place to add it: a
full rebuild is a one-time background operation, and while it runs the prior
committed generation keeps serving first pages in 5 ms.

---

## Q. SQLite tuning

Profiling (`cProfile`, whole-rebuild) found the real bottlenecks rather than
the assumed ones:

1. **Buffered-read preallocation — 26.5 s of the original 58.2 s.** Asking a
   `BufferedReader` for the full 4 MiB scan limit makes it preallocate that
   buffer for *every* artifact. Reading a stat-derived size (plus a 64 KiB
   slack window for a file still being written, still hard-capped at 4 MiB)
   measured 0.111 ms/file versus 0.653 ms/file — a ~24 s saving across the
   corpus, with the bound preserved.
2. **Index maintenance during bulk insert — ~6 s.** Dropping the secondary
   indexes inside the rebuild transaction and recreating them after the load
   measured 25.2 s + 0.6 s versus 31.3 s.
3. Redundant per-batch child-row deletes during a full rebuild (the tables
   were just emptied) were skipped.

### Final index set and rationale

| Index | Justification |
|---|---|
| `idx_occurrence_order (timestamp_known DESC, effective_timestamp_ns DESC, location_id ASC)` | The default ordering and every keyset page. Mixed sort direction is declared on the index so the planner walks it without a sort step. Unfiltered page: 3.9 ms. |
| `idx_occurrence_ruleset (ruleset_id)` | Ruleset filter; `count()` 0.6 ms vs a full scan. |
| `idx_occurrence_seed (seed)` | Exact-seed filter. |
| `idx_occurrence_workflow (workflow)` | Selective source filter — 0.7 ms page for a 72-row match. |
| `idx_occurrence_replay_state (replay_state)` | Replay-state filter and counts. |
| `idx_occurrence_winner (winner)` | Exact-winner filter. |
| `idx_occurrence_health (entry_health)` | Health filter and counts. |
| `idx_occurrence_match (match_id)` | Grouping deterministic reruns — 0.05 ms. |
| `idx_occurrence_key (occurrence_key)` | Copied-occurrence detection (the `GROUP BY … HAVING COUNT(*) > 1` pass) and occurrence lookup. |
| `occurrence_entrant` primary key `(location_id, ordinal)` | Ordered detail retrieval. |

Explicitly **not** added:

* Compound `(filter column, timestamp, location_id)` indexes. They would let
  low-selectivity filters avoid a temp-B-tree sort, but every such query
  already measures 24–66 ms against a 250 ms budget, and six wide compound
  indexes would materially inflate a cache that is already 99.8 MB. Measured,
  considered, rejected.
* `ANALYZE`. Measured directly: it runs in 0.066 s but changed **no** query
  plan and **no** timing, so it is not run.
* An FTS table for entrant search. A plain denormalized column measures 6 ms.

---

## R. Cache recovery tests

| Scenario | Result |
|---|---|
| Rebuild from a missing cache | Rebuilds; `rebuild_reason = new_cache`. |
| Delete the database (with `-wal`/`-shm`) and rebuild | **Logically identical history.** On the real 53,458-row corpus, all ten probe counts and the full semantic first page compared byte-equal before and after: `total 53458, tie 1138, designer 7, evaluation 72, replay_available 44547, replay_missing 8911, not_produced 0, invalid 0, incomplete 0, seed1 15765`. A temporary-corpus test asserts the same for a mixed v1/v2/degraded corpus. |
| Corrupt database (non-SQLite bytes) | Detected on open, quarantined by deletion, rebuilt; artifacts verified byte-identical before and after. |
| Cache file undeletable | Falls back to a session-only in-memory cache and reports `persistent=False`. |
| `user_version` mismatch | `cache_schema_version_mismatch` → drop and rebuild. |
| `root_identity` mismatch | `root_identity_mismatch` → drop and rebuild. |
| Deterministic failure mid-rebuild (injected `OSError` on the 2nd candidate) | Transaction rolls back; the previous generation's rows and generation number are unchanged and still queryable. |
| Cooperative cancellation mid-rebuild (600-row corpus) | `committed=False`, index left empty — nothing half-applied. |
| Deterministic failure mid-reconcile | Rolls back; prior rows and generation intact. |

Ordering of internal surrogate IDs is not asserted; semantic rows are.

---

## S. Historical compatibility

One mixed corpus, one rebuild, no migration — containing genuine artifacts
produced by the current production writer alongside hand-built historical
ones:

* a real `NativeMatchService` match (result schema v2, replay schema 4);
* `battle2.result` v1 with `bytefray-rules-1`;
* a second v1 artifact repeating the same `match_id` in a different directory;
* a copied v2 occurrence at two locations;
* a valid result with a missing replay;
* a pMARS-shaped v1 result with `replay: null` and `ruleset_id: null`;
* a corrupt `result.json`;
* a replay-only directory.

Observed: `healthy 6, degraded 1, incomplete 1, invalid 1`; result schema
versions `{1, 2, None}` coexisting in one index; both historical and current
rulesets queryable; exactly two rows marked as copied occurrences; artifact
bytes unchanged; and deleting the cache and rebuilding reproduced identical
semantic rows.

Separately, two byte-identical **real** native reruns were produced through
the production writer and indexed: one `match_id`, two distinct authoritative
`occurrence_id`s, both `recorded` timestamps, both healthy, neither marked a
duplicate, and each row's `expected_sha256` verified against the real replay
through `result_model.verify_replay_digest`.

---

## T. No-GUI dependency

* `test_headless_import_never_pulls_in_qt_or_pygame` asserts that importing
  `battle_engine.replay_history` and all four submodules loads no `PySide6`
  and no `pygame` module — the same enforcement pattern
  `evaluation_history` already uses.
* Independently, the full open → refresh → page → detail cycle was executed
  in a subprocess with a `sys.meta_path` finder that **raises** on any
  `PySide6`/`PySide2`/`PyQt5`/`PyQt6`/`pygame`/`shiboken6` import. Exit code
  `0`; output: `rows: 1 winner: A entrants: Solo count: 1 replay_state:
  not_produced`, `QApplication present: False`, `GUI modules loaded: []`.
* No `QApplication`, no Qt event loop, no `QThread`, no Qt signal, and no GUI
  initialization exists anywhere in the package. No module boundary needed
  correcting — the package was built Qt-free from the first commit of code.
* The service is synchronous and owns its own SQLite connections, so 7C can
  construct and drive it entirely inside a worker object.

---

## U. Security and robustness

| Concern | Handling |
|---|---|
| SQL injection via filter values | **Parameterized SQL exclusively.** Statement text is assembled only from module-level constants and `", ".join("?" * n)` placeholder runs; no user value, artifact string, or column value is ever concatenated into SQL. Audited: the only two f-string statements in the package are `PRAGMA user_version = {int(CACHE_SCHEMA_VERSION)}` and `DROP INDEX IF EXISTS {name}` where `name` iterates module-constant index names. Tested with hostile values in the entrant, ruleset, winner, confidence, match-id, and location-id inputs — all return 0 rows and leave both tables intact. |
| Unbounded diagnostics | Every message goes through `bounded_diagnostic` (whitespace-collapsed, 300-character cap); the per-pass unreadable-directory list stops at 50 entries. No traceback and no raw artifact content is stored. |
| Path traversal | Discovery rejects absolute, drive-qualified, separator-bearing, and dot-segment replay references with a cheap string check, and routes anything more complex through `paths.contained_path`, which resolves and rejects symlink escapes. `resolve_replay` re-applies `contained_path` against the indexed run root at use time, so a tampered cache row still cannot produce a path outside the tree. Tested with `../../secrets.jsonl` and an absolute outside path. |
| Following untrusted metadata paths | Only the result's own replay *filename* is ever resolved, and only beneath its own run directory. No other path from artifact metadata is followed. |
| Agent imports/execution | The package contains **no** `importlib`, `__import__`, `exec`, `eval`, `subprocess`, `runpy`, or `Popen`. A test plants a result naming `sitecustomize.py:create_agent` and a source path pointing at a module that raises on import, then indexes and reads detail: the module is never imported and `sys.modules` is unchanged. |
| Giant/malformed JSON | Results are capped at 4 MiB (checked from the walk's stat *and* from the bytes actually read); replay header lines at 1 MiB. Oversized artifacts become health-coded rows. JSON, Unicode, type, key, and value errors are all caught per candidate. |
| Symlink following | `os.walk(..., followlinks=False)`. |
| Database corruption | Detected, quarantined, rebuilt; artifacts untouched. |
| Transaction integrity | One `BEGIN IMMEDIATE` transaction per refresh; failure, exception, or cancellation rolls back completely. |

### Filesystem mutation audit

The entire package contains exactly **two** mutating filesystem calls:
`target.parent.mkdir(...)` for the cache directory and
`candidate.unlink(missing_ok=True)` inside `remove_cache_files`, which is only
ever called with the cache path and its own journal sidecars. Both `open()`
calls in `discovery.py` are `"rb"`. Replay History therefore cannot rewrite a
result, rewrite a replay, rename a run, move an artifact, delete an artifact,
or normalize historical data in place. Multiple tests snapshot every file
under the run tree (size, `mtime_ns`, full bytes) before and after rebuild,
reconcile, detail fetch, and replay resolution and assert byte-for-byte
equality — including on a real-artifact corpus. The only authorized
persistent mutation is the disposable SQLite cache in its cache location.

---

## V. Tests

| Run | Result |
|---|---|
| Focused `engine/tests/test_replay_history.py` | **83 passed** |
| `ruff check .` | `All checks passed!` |
| `mypy engine/src/battle_engine` | `Success: no issues found in 113 source files` |
| `mypy client/src/battle_client` | `Success: no issues found in 16 source files` |
| V5/ruleset-focused regression (`engine/tests -k "ruleset or v5 or v4"`) | **979 passed, 2049 deselected** in 77.72 s |
| Permanent Ruleset 4 equivalence corpus (`test_v4_stable_ruleset_equivalence.py`) | **23 passed** |
| Full suite (`python -m pytest --basetemp=.pytest-tmp/phase7b-final`) | **3510 passed, 21 skipped, 3 deselected** in 364.99 s |

**Test-count accounting:** Phase 7A's clean full run recorded 3427 passed, 21
skipped, 3 deselected. 3510 − 3427 = **83**, exactly the 83 tests added in
`engine/tests/test_replay_history.py`. Skips and deselections are unchanged.
No pre-existing test was modified, and no expected gameplay output or golden
baseline was touched.

Focused coverage by gate: domain model, identity, timestamps and cache schema
(Gate 1); discovery, normalization, layouts, `_loose`, malformed/unsupported/
inaccessible artifacts, replay-only, duplicates (Gate 2); rebuild, cache
deletion/corruption, deterministic mid-rebuild failure, cancellation, no
artifact writes (Gate 3); add/modify/delete/replace, deleted replay, moved v1
and v2 artifacts, inaccessible subtree, vanished run root, rollback, and proof
that unchanged artifacts are not reparsed (Gate 4); every filter individually
and combined, case-insensitive entrant search, date bounds, exact seed,
historical rulesets, replay states, ordering, >500-row keyset paging, detail
retrieval, and query safety with hostile strings (Gate 5); real produced
artifacts, mixed-era corpus, agent-execution safety (Gate 6).

---

## W. Files changed

| File | Reason |
|---|---|
| `engine/src/battle_engine/replay_history/__init__.py` | **New.** Package docstring and curated public exports. |
| `engine/src/battle_engine/replay_history/models.py` | **New.** Occurrence/entrant/fingerprint model, five state enums, diagnostic categories, identity derivation, bounded diagnostics, health classification. |
| `engine/src/battle_engine/replay_history/discovery.py` | **New.** Run-tree walk, scan-scope completeness, workflow classification, timestamp fallback chain, bounded result/replay-header adaptation, path safety, health coding. |
| `engine/src/battle_engine/replay_history/index.py` | **New.** SQLite schema, pragmas, transactions, cache open/validate/recover, bulk write, deletion, duplicate marking, filter translation, keyset paging, row mapping. |
| `engine/src/battle_engine/replay_history/query.py` | **New.** `HistoryQuery`, `HistoryCursor`, `HistoryRow`, `HistoryPage`, `HistoryDetail`, `ReplayResolution`, `ScanCounts`, `RebuildSummary`, `ReconcileSummary`. |
| `engine/src/battle_engine/replay_history/service.py` | **New.** `ReplayHistoryService` façade: open/close, rebuild, reconcile, page, count, detail, replay resolution, progress and cancellation. |
| `engine/tests/test_replay_history.py` | **New.** 83 focused tests across all six gates. |
| `engine/src/battle_engine/result_model.py` | Extract `result_from_mapping(data)` from `read_result` (behavior unchanged) so Replay History reuses the one production parser on a payload it already read, instead of re-reading every file or maintaining a second parser. |
| `.gitignore` | Ignore `/cache/` — in a source checkout the data root is the repository, so the disposable Replay History database would otherwise appear as an untracked ~100 MB file. |
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7B_DISCOVERY_INDEX.md` | **New.** This report. |

No replay module, replay schema document, gameplay module, ruleset module,
scheduler, scoring, CLI, Designer, Replay Viewer, run-layout, installer, or
packaging file is in the diff. No dependency was added. No version was bumped.

---

## X. Deviations from Phase 6

The Phase 6 architecture was treated as accepted and was implemented as
specified. Implementation evidence produced **no contradiction** requiring an
architecture change. Three refinements *within* the accepted design are
recorded for honesty:

1. **Entrant search is a denormalized column on `occurrence`, not a query
   against the entrants table.** Phase 6 Section K specified an entrants table
   carrying "normalized search text". The table exists and carries the
   structured detail; the search text is additionally denormalized onto the
   parent row so a substring filter is one single-table scan (6 ms over
   53,458 rows) rather than a correlated subquery combined with the ordering
   walk. Same contract, cheaper query.
2. **Artifact paths are derived, not stored twice.** Phase 6 Section K
   listed "relative result/replay paths" on the entries table. The result path
   is fully determined by the location (discovery only anchors on the exact
   canonical name), so it is derived from `relative_directory`, and only the
   replay's own filename is persisted. This removed 19.7 MB from the 53k
   cache and eliminated a second copy of state that could drift.
3. **`location_id` is derived from the artifact *directory*, not the
   artifact file.** Phase 6 Section E says "normalized relative artifact
   path". Keying on the file would change the row's identity the moment a
   `result.json` is deleted and only the replay remains — precisely the
   transition Phase 6 Section L requires to be an in-place conversion to a
   replay-only row. One directory holds at most one occurrence under every
   canonical layout, so the directory is the correct location identity.

Phase 6's own open question about page size was not reopened: 500 rows
measures 5 ms and needed no tuning.

---

## Y. Deferred items

**Phase 7C (UI):** `QThread` worker and queued-signal ownership; virtual
`QAbstractTableModel`; `Tools → Replay History…`; filter widgets and
debouncing; the structured detail pane; empty state; progress and
cancellation UI; display formatting of every enum (including the `≈`
approximate-date marker and the `_loose` non-durable warning); backward
paging if the UI ever needs it.

**Phase 7D (Viewer handoff):** click-time digest verification via
`verify_replay_digest` against the path `resolve_replay` returns;
`open_pygame_client_direct` launch and its error handling; Copy Seed.

**Phase 7E (qualification):** synthetic 100k+ metadata corpus; two-process
concurrent-access behavior under WAL; packaged Windows Viewer handoff; GUI
CI and manual smoke.

**Deliberately out of V1 scope:** session-explicit external result/replay
roots (the service indexes one configured run tree); persisted external root
registration; content-hash deduplication of replay-only copies; tags and
notes (which must never live only in a deletable cache); preset identity;
exact rerun; filesystem watchers.

**Characterized gap:** the full rebuild is ~1 s over Phase 6's 25 s warm
figure (Section P). It is within the 60 s cold-ish target, it is a one-time
background operation, and the warm refresh that actually runs in the product
is 7.4 s.

---

## Z. Phase 7C contract

Everything the UI may rely on. **Phase 7C does not issue SQL.**

```python
from battle_engine.replay_history import (
    EntryHealth, HistoryCursor, HistoryDetail, HistoryPage, HistoryQuery,
    HistoryRow, OccurrenceIdentitySource, OutcomeState, RebuildSummary,
    ReconcileSummary, ReplayHistoryService, ReplayResolution, ReplayState,
    ResultHealth, TimestampConfidence, WorkflowSource,
)
```

### Construction and lifecycle

```python
service = ReplayHistoryService.open(
    data_root=None,      # default: battle_engine.paths.get_data_root()
    runs_root=None,      # default: <data root>/runs
    cache_path=None,     # default: <data root>/cache/replay_history/index-v1.sqlite3
    in_memory=False,     # True for a session-only cache
)
...
service.close()          # also usable as a context manager
```

`open()` never raises for a damaged, stale, or missing cache; it recovers and
reports. Inspect `service.cache_report` — `CacheOpenReport(path, created,
rebuild_required, rebuild_reason, persistent, recovered_from)` — to tell the
user why history is being rebuilt, and to surface `persistent=False` when the
cache could not be written. The service and its connections must be created
and used on **one** thread (the 7C worker).

### Initial display and refresh

```python
page = service.fetch_page()                       # show cached rows immediately
summary = service.refresh(                        # then reconcile in the worker
    force_rebuild=False,
    progress=lambda phase, seen: ...,             # every 1,000 candidates
    cancel_check=lambda: worker.cancelled,        # polled every 256 candidates
)
```

`refresh()` rebuilds when the cache is new, recovered, version/root
mismatched, or empty; otherwise it reconciles. It returns `RebuildSummary`
(`scanned`, `inserted`, `counts`, `duration_seconds`, `generation`,
`committed`, `diagnostics`) or `ReconcileSummary` (`added`, `updated`,
`replaced`, `unchanged`, `removed`, `retained_inaccessible`, `counts`,
`duration_seconds`, `generation`, `committed`, `scan_complete`,
`diagnostics`). `committed=False` means nothing was applied — the previous
generation is still what the user is seeing. `scan_complete=False` plus a
non-empty `diagnostics` tuple means part of the tree could not be inspected
and stale rows were deliberately retained; say so rather than implying the
list is complete. `service.rebuild(...)` and `service.reconcile(...)` are
available explicitly; `HistoryRefreshCancelled` never escapes them.

### Querying and paging

```python
query = HistoryQuery(entrant_text="hunter", workflows=[WorkflowSource.DESIGNER])
total = service.count(query)
page  = service.fetch_page(query, cursor=None, limit=500)
while page.has_more:
    page = service.fetch_page(query, cursor=page.next_cursor, limit=500)
```

`HistoryPage(rows, next_cursor, has_more, page_size)`; `HistoryCursor` is an
opaque typed value — pass back the one you were given, do not construct one.
Ordering is documented in Section N and is stable for an unchanged index.

### Detail and replay

```python
detail = service.fetch_detail(row.location_id)      # HistoryDetail | None
replay = service.resolve_replay(row.location_id)    # ReplayResolution
if replay.available:
    ...  # Phase 7D: verify replay.expected_sha256, then launch the Viewer
```

`resolve_replay` re-resolves and re-checks the path every time; never cache
its answer across a user action. `state` distinguishes `available`, `missing`,
`not_produced` ("this workflow did not produce a native replay"), `invalid`,
`inaccessible`, and `unchecked`, and `diagnostic` carries a bounded
explanation.

### Error and result reporting

No operation raises for an artifact problem — every one becomes a row's
`result_health` / `replay_state` / `entry_health` plus a bounded
`diagnostic_category` and `diagnostic_message`. No operation raises for a
cache problem — it becomes a `CacheOpenReport` field and a rebuild. The only
exceptions a caller can see are programming errors and genuine, unexpected
`OSError`s escaping a walk, which roll the transaction back and leave the
previous generation usable.

---

## Validation

| Check | Result |
|---|---|
| `git diff --check` | Clean |
| Untracked-addition whitespace/conflict-marker scan | Clean (7 untracked files, 0 problems) |
| Stray database/benchmark artifacts in the repository | None outside the git-ignored `.pytest-tmp/` test-temp root; no `cache/` directory at the repository root; no `runs/cache` |
| Temporary benchmark/profiling scripts | Written only to the session scratchpad outside the repository; never staged |
| Final `git status --short` | ` M .gitignore`, ` M engine/src/battle_engine/result_model.py`, `?? engine/src/battle_engine/replay_history/`, `?? engine/tests/test_replay_history.py`, plus this report |
| Commit / push | **None performed** |
