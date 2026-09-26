# V5 Alpha 1 Phase 5 — Replay and History Architecture Review

Scope: determine what Replay History, Tournament History, Evaluation History,
session replay shortcuts, and possible agent-contextual history mean inside the
current Bytefray desktop application. This is an architecture and navigation
review. It does not change gameplay, artifact schemas, history persistence,
match execution, or deterministic identities.

The decision is **Case B — clear low-risk navigation improvement**. Agent
Designer is now a hybrid that functions as Bytefray's primary desktop shell,
with agent authoring as its central context. Global history therefore belongs
in this application, but durable read-only histories are not operational tools.
A top-level **History** menu is warranted. The three history implementations
remain independent, and larger contextual-history, restoration, shared-model,
and application-shell work is deferred.

## 1. Baseline and process safety

The review began on 2026-09-13 with:

| Item | Initial state |
|---|---|
| Branch | `v5-research`, tracking `origin/v5-research` |
| HEAD | `cad229d84e1ee901c1930acaf34166031f6fc22a` (`feat(v5): complete tournament results workflow`) |
| Phase 4 | Committed at HEAD |
| Working tree | Clean (`git status --short --branch` reported only the branch/tracking line) |
| Git lock | No `.git/index.lock` |
| Process audit | No Python, pytest, Antigravity, Claude, Gemini, or other checkout-related worker was active; only the expected current Codex application process and the short-lived audit PowerShell process matched the broad process query |

No reset, clean, restore, stash, or commit was performed. The process audit was
read-only; it required an elevated CIM query because the initial sandboxed
query was denied.

## 2. Current product boundary

Agent Designer is no longer a narrow editor. The shipped `QMainWindow` owns:

- Simple and Advanced match configuration and execution;
- parameter editing, code inspection, package import/inspect/export, agent
  creation, validation, development tests, and evaluation;
- tournament launch, immediate tournament results, and tournament history;
- evaluation results, evaluation history, revision inspection/restore, and
  Agent Lab drill-down;
- global Replay History, session-local replay shortcuts, output-folder
  navigation, and Replay Viewer launch.

It is therefore the **hybrid** interpretation, leaning toward the primary
desktop-shell interpretation: one Bytefray application shell with authoring
tabs and contextual development actions. The authoring focus remains real,
but it no longer defines the boundary of every top-level command.

This conclusion follows from actual ownership. `app/agent_designer.py` owns
the process slot, the catalog, all three tabs, all three histories, tournament
and evaluation dialogs, and every Qt-to-Replay-Viewer handoff. Replay Viewer is
a purpose-built playback client, not an application shell; moving global
history into it would conflate artifact discovery with replay rendering and
would strand result-only matches. A new standalone history application would
duplicate the existing shell and packaging path without solving a demonstrated
workflow problem.

The name **Agent Designer** now understates part of the product boundary. That
is an information-architecture question, not evidence that Replay History is
misplaced. Renaming or reorganizing the application is Option E work and is
explicitly deferred.

## 3. Complete feature inventory

The table records the user-facing surface, not every internal helper. “Restore”
means reconstruction of the historical run, not merely copying a seed or
opening the same artifact.

| Surface | Launch and scope | Data and persistence | Restore / replay | Relationship to other surfaces |
|---|---|---|---|---|
| Simple **Run Match** result | Simple tab; current configured pair | New unique `runs/_designer/<timestamp>-<suffix>/result.json`, `replay.jsonl`, and summary artifacts; durable on disk | Does not restore. Successful completion enables the session **View Last Match** path and offers immediate result feedback | The occurrence is later discoverable in Replay History |
| Advanced **Run Match** result | Advanced → Match Setup; current configured entrants and Agent Params | Same unique `_designer` artifact contract as Simple | Does not restore. Updates the same session last-match pointer | The occurrence is later discoverable in Replay History |
| Simple/Advanced **View Last Match** | Buttons on both match panels; session-scoped | In-memory `_last_replay`, updated only after a completed Simple/Advanced result; before one exists, a file dialog starts in the canonical replay directory | Opens the remembered or explicitly chosen replay. It deliberately remains pointed at the previous completed match while a new match runs | Shortcut, not history. It overlaps replay launch intentionally but has no index, metadata, or durable “recent” state |
| Advanced **Replay Browser** | Advanced → Replay Browser | User-selected `.jsonl` path; ordinary filesystem picker state only | Opens any selected replay, including external files; cannot restore setup | Raw-file workflow, complementary to artifact-backed Replay History |
| **Open Last Output Folder** | File menu; session-scoped | In-memory output paths, falling back to `<data-root>/runs`; a tournament output retains priority over a later direct-match output for the session | Opens a folder, not a replay; cannot restore setup | Convenience navigation, not chronological history and not “last” across every workflow |
| Immediate tournament result | **Tools → Run Tournament…**; just-completed tournament | `battle2.tournament` v1 plus nested canonical match artifacts under a fresh `runs/tournaments/designer-…` directory | Tournament Results opens automatically; individual completed matches can open verified replays; no tournament restore | Same results presentation used by Tournament History |
| **Tournament Results** | Automatic after a run, or selected from Tournament History / external folder | Reads one `tournament.json` and its recorded match `result.json` files; artifacts are authoritative | No restore. Match **View Replay** rechecks association, containment, existence, and recorded SHA-256 at click time | Contextual parent view. Its match rows also exist as occurrences in Replay History |
| **Tournament History…** | Initially Tools; application-global | Synchronously scans direct children of `<data-root>/runs/tournaments`, reading `tournament.json`; no index; persists because artifacts persist | Opens Tournament Results, which can open a match replay. Cannot restore configuration | Independent tournament-level history; not a duplicate match-history list |
| Development **Test** | Agent Development tab; selected agent | New unique `runs/agents_test/<agent>/<timestamp>-<suffix>/` result/replay/trace artifacts | Own session-only **Open Replay** and **Inspect Trace**. No restore. Its replay state is intentionally independent of View Last Match | The completed occurrence is also discoverable in Replay History |
| Development **Evaluate…** | Agent Development tab; selected candidate plus chosen opponents/setup | New `runs/evaluations/<run>/evaluation.json`, nested cell artifacts, and optional revision records | Fresh Evaluation Results can open cell replay or launch a diagnostic Agent Lab test. It does not restore the evaluation | Evaluation cells also become Replay History occurrences |
| **Evaluation Results** | Automatic after evaluation | Reads the just-written typed evaluation artifact and cells | Cell **Open Replay** checks current file existence; pairwise **Test in Agent Lab** reconstructs a diagnostic test, not the exact historical evaluation | Concise immediate view; overlaps Evaluation History presentation but serves a distinct just-finished workflow |
| **Evaluation History…** | Initially Tools; application-global, not selected-agent scoped | Synchronously discovers one level under `<data-root>/runs/evaluations`, fully adapts each `evaluation.json`; revision store supports explicit revision inspection/restore; no index | Opens cell replays and pairwise Agent Lab tests. Revision restore is explicit, but there is no evaluation rerun/restore | Specialized analytical history, comparison, verification, and revision UI |
| **Replay History…** | Initially Tools; application-global and modeless | Recursively discovers result/replay artifacts below `<data-root>/runs`; authoritative artifacts plus rebuildable persistent SQLite projection at `cache/replay_history/index-v1.sqlite3` | Opens a click-time resolved and digest-verified replay; copies seed; does not restore or rerun | Generic match-occurrence browser across direct, development, tournament, evaluation, CLI-latest, and other run locations |
| Replay Viewer file picker | Launch `bytefray-replay-viewer` without a path | Minimal directory navigation over `.jsonl` files; no result metadata, index, or history state | Opens the selected replay only | External/file-oriented fallback, not a history implementation |
| CLI replay | `bytefray replay --replay PATH` (and renderer options) | Explicit caller-supplied replay path | Playback only | Canonical non-Designer launch path; the GUI handoffs ultimately reuse the same viewer behavior |

There is no durable “recent matches” list and no current-agent result surface.
The only recency conveniences are `_last_replay` for Simple/Advanced and
`_last_test_replay` for Development Test; both are intentionally process-local
and reset on application lifecycle or relevant agent/source changes.

## 4. Current data flows and ownership

### 4.1 Match occurrence flow

```text
Simple / Advanced / Development / Tournament cell / Evaluation cell / CLI
                                  |
                                  v
                    canonical result/replay artifacts
                                  |
              +-------------------+-------------------+
              |                                       |
              v                                       v
     contextual parent/result UI          Replay History discovery
                                                  |
                                   rebuildable SQLite projection
                                                  |
                                      paged read-only browser
                                                  |
                                      verified Replay Viewer handoff
```

The result and replay artifacts are authoritative. Replay History's SQLite
database is a disposable query projection, not a new source of truth.

### 4.2 Parent workflow flow

```text
tournament.json  ---> Tournament History ---> Tournament Results ---> match replay
evaluation.json  ---> Evaluation History ---> analysis/cell detail ---> cell replay
```

The parent histories read their own domain artifacts directly. They do not
query Replay History, and Replay History does not parse parent artifacts to
construct tournament standings or evaluation comparisons. That separation is
correct: a tournament and an evaluation are not aggregations that can be
faithfully represented by a generic replay row.

### 4.3 Thread and process boundaries

Replay History uses separate maintenance/writer and read-only query `QThread`
workers. Each creates, uses, and closes its own Qt-free service and SQLite
connection on the owning thread. The GUI receives immutable records and does
not issue SQL or parse artifacts. Cached rows arrive before background
reconciliation completes; the model pages 500 rows at a time.

Tournament and Evaluation History currently scan and adapt their shallower
parent directories synchronously on the GUI thread. Replay rendering remains a
detached Viewer process. Designer-owned match, validation, test, tournament,
and evaluation work shares one guarded `QProcess` slot; browsing Replay History
does not consume it.

## 5. Replay History audit and actual role

### 5.1 Discovery, persistence, and workflow coverage

Replay History recursively walks `<data-root>/runs` without following
directory symlinks. A directory containing the exact canonical name
`result.json` is a result candidate; `replay.jsonl` can supply a replay-only
candidate when a result is absent. Result JSON is the preferred metadata
authority. Discovery reads only the replay header where needed; it does not
scan every replay event to derive outcomes.

Structural path classification identifies:

- Designer matches under `_designer`;
- Development/Agent Test runs under `agents_test`;
- Tournament matches under `tournaments`;
- Evaluation cells under `evaluations`;
- non-durable overwritten CLI Latest output under `_loose`;
- other/custom run directories and unknown layouts.

Research/custom artifacts inside `runs` are included when they use the
canonical filenames. Arbitrary external replay files are not part of the
index; Advanced Replay Browser, the Viewer picker, and explicit CLI paths
serve that use case.

The persistent index survives restart and is reconciled transactionally from
file fingerprints. A missing, incompatible, or corrupt cache is rebuilt from
artifacts. An in-memory fallback preserves functionality when a disk cache
cannot be used, with serialized access because it cannot support the normal
independent reader connection.

### 5.2 Indexed metadata, identity, and health

The browser projects timestamp and confidence, workflow, ruleset and
provenance, seed, mode/configuration, entrants, runtime/API/version/source
hash/parameters, result status/winner/score/termination/ticks, result and
replay schema state, replay digest/path/size, durability, and diagnostic health.

Three identity concerns remain separate:

- `match_id`: deterministic semantic match identity;
- `occurrence_id`: the actual execution identity recorded by native result v2;
- `location_id`: the cache row/location identity, also used for legacy
  synthetic occurrences and duplicate-location handling.

Result health distinguishes valid, malformed, unsupported, inaccessible, and
missing data. Replay state distinguishes available, missing, not produced,
invalid, inaccessible, and unchecked. Broken rows remain visible with bounded
diagnostics. pMARS/Redcode results that legitimately do not produce a Bytefray
replay remain browseable. `_loose` rows are visibly non-durable.

### 5.3 Query, search, and sorting

The table exposes Date, Entrants, Result, Ruleset, Seed, Source, and Replay.
Queries compose parameterized filters for:

- case-insensitive entrant display/identifier substring;
- ruleset facets populated from the actual index;
- winner/tie/unknown outcome;
- workflow source;
- replay state;
- exact seed;
- inclusive date bounds.

Search is debounced. Ordering is fixed to known timestamps first, newest
effective timestamp first, then stable `location_id`; column headers are not
user-sortable. There is no full-text search, tags, notes, saved filters,
artifact hash search, path search, or parent tournament/evaluation filter.
UI filters, geometry, splitter position, and selection are not persisted.

### 5.4 Context, linkage, and replay opening

Replay History is application-global. It has no concept of the currently
selected Designer agent. Entrant substring search is useful but is not a
stable exact-agent predicate.

Tournament and evaluation child matches are classified by workflow, but no
`tournament_id`, `evaluation_id`, round, schedule position, matrix role, or
parent-link record is indexed. Conversely, the parent histories know their
artifact directories and recorded match/result identities but not Replay
History's location row. A path association can often be inferred, but there is
no public cross-history linkage contract.

Button, table double-click, and Enter all converge on one Open Replay entry
point. It re-resolves the selected contained path, checks current existence and
readability, and verifies a recorded digest before launching the established
Viewer handoff. Legacy records without a digest are allowed with the explicit
weaker guarantee. Stale or failed requests cannot launch a newly selected row.

### 5.5 Role conclusion

Replay History is **an artifact-backed, application-global match-occurrence
history browser with replay capability**. It is not:

- a raw replay browser, because result-only records and structured result
  metadata are first-class;
- a complete cross-workflow activity history, because parent tournament and
  evaluation events are not represented;
- a debugger, because it does not inspect trace or replay internals;
- only a replay library, because a replay may be absent or never produced.

It is a user-facing game/match history. Its placement in the current desktop
shell is correct; its menu category and eventual name deserve refinement.

## 6. Tournament History relationship

Tournament History and Replay History intentionally overlap only at the child
match layer.

| Question | Finding |
|---|---|
| Duplicated data | Match identity/status, entrants, winner/result, ruleset, and replay availability can appear in both surfaces |
| Tournament-only data | Tournament ID, division, ordered schedule, round/orientation context, aggregate completion/errors, standings, leaders/ties, and the tournament folder |
| Do tournament matches appear in Replay History? | Yes. Recursive discovery classifies nested canonical matches as Tournament |
| Does Replay History know the tournament? | Only structurally as workflow/path; it does not retain the parent ID or schedule position |
| Does Tournament History know the Replay History row? | No. It knows recorded match/result IDs and artifact directories, but not `location_id` |
| Should one link to the other now? | No. Tournament Results already opens the exact child replay. Jumping to a generic occurrence row adds a step without exposing new parent context |
| Are independent surfaces justified? | Yes. Users browse tournaments by run, standings, and schedule; they browse Replay History by individual occurrence and cross-workflow filters |

Tournament History is artifact-backed and restart-safe but deliberately has no
index. It scans only direct tournament children and retains stopped or damaged
runs as explicit states. It uses the same Tournament Results view for current,
historical, and externally selected folders.

## 7. Evaluation History relationship

Evaluation-produced cell results and replays are discoverable as Evaluation
occurrences in Replay History. Evaluation History itself opens a selected cell
replay directly and can launch a pairwise cell in Agent Lab.

Evaluation metadata is substantially richer than match metadata: candidate,
baseline, opponents and roles; seed/matrix plan; aggregate and comparison
statistics; execution contexts; lifecycle and methodology; compatibility;
revision records; verification; and per-cell analytical state. Replay History
does not retain the evaluation ID, opponent role, matrix coordinate,
comparison, revision, or methodology.

Evaluation History is therefore a **specialized analytical result history**,
not a filtered generic run view. It should remain independent. A jump from a
cell to Replay History would normally be inferior to its existing direct Open
Replay action. A future reverse link from Replay History to the parent
evaluation could help a user who discovers an interesting cell globally, but
only after parent association has an explicit, tested contract.

One consistency risk emerged: Replay History and Tournament Results perform a
click-time containment/existence/digest preflight, while Evaluation Results and
Evaluation History enable Open Replay primarily from current file existence and
then emit the path to the generic handler. Deep evaluation verification can
check artifacts, but it is optional and is not the same opening contract. This
is an **actual defect risk**, not evidence for merging histories. A focused
follow-on should centralize or reuse verified result-to-replay handoff semantics
without changing evaluation data models.

## 8. Current-agent contextual history feasibility

The desired loop — **Design → Battle → Replay → Analyze → Modify** — would
benefit from a small, selected-agent recent-activity view. It could remove the
need to repeat a global entrant search and could group matches, tournaments,
and evaluations around the thing being edited. The current data is only
partially sufficient, however.

| Question | Available now | Reliability |
|---|---|---|
| Recent matches involving the agent | Entrant names/identifiers and source hashes are indexed | Search is substring-based; direct results may use display/slot aliases; no durable universal catalog-agent ID |
| Recent tournaments | `TournamentHistoryEntry.entrant_ids` | Exact within the tournament's recorded roster, but no query API or shared agent identity across renamed/replaced sources |
| Recent evaluations | Candidate/opponent/roster IDs in evaluation summaries | Exact within each evaluation artifact, but discovery is global synchronous loading and has no current-agent filter API |
| Opponents, ruleset, seed, result | Present for normal match occurrences | Generally reliable; legacy and invalid entries retain confidence/availability caveats |
| Agent Params | Native result entrant metadata records non-empty parameters | Historical/legacy coverage varies; parameters do not preserve source bytes |
| Preset | Effective settings may be present | Preset name/provenance is not a general result field |
| Reopen replay | Supported when a valid replay exists | Strong in Replay/Tournament paths; evaluation preflight consistency should be fixed |

“Current agent” is itself contextual: Simple and Advanced select match
entrants, while Agent Development selects an authoring subject. The most useful
first definition is the selected Agent Development subject, not an implicit
application-wide selection.

Implementing this now would require policy decisions and new query/presentation
work, so it is not trivial Phase 5 polish. A follow-on should first define a
stable agent/reference/revision matching contract, then prototype a compact
Development-tab recent-activity surface. Name matching alone must not be
presented as exact continuity across edits or renames.

## 9. Match restoration and rerun feasibility

Current artifacts provide strong behavioral provenance but do not archive all
inputs. The classification below concerns native result v2 unless noted.

| Setup field | Classification | Reason |
|---|---|---|
| Ruleset | Fully reconstructable for current native results | Stable ruleset ID and provenance are recorded; recovered legacy values retain explicit confidence caveats |
| Entrant ordering | Fully reconstructable as recorded logical order | Entrant order/slots are part of reproducibility metadata |
| Seed | Fully reconstructable | Integer seed is recorded and already copyable |
| Arena size | Fully reconstructable | Recorded in reproducibility configuration |
| Tick limit | Fully reconstructable | Recorded as tick limit; observed ticks are separately recorded |
| Action budget | Fully reconstructable where applicable | Recorded in current native reproducibility configuration |
| Win mode | Fully reconstructable | Recorded in current native reproducibility configuration |
| Scoring weights | Fully reconstructable | Effective weights are recorded |
| Locality reach | Fully reconstructable for rulesets where relevant | Recorded with the effective ruleset configuration |
| Agent Params | Reconstructable with caveats | Current native entrant metadata records non-empty effective parameters; older artifacts and defaults may not preserve authoring intent |
| Entrant IDs/display names/runtime/API/entry point | Reconstructable with caveats | Descriptive identity is recorded, but catalog entries can be renamed, removed, or replaced |
| Agent revisions/source | Unavailable as a general restore input | Hashes/fingerprints prove identity but cannot recreate missing source bytes. Evaluation revision snapshots are workflow-specific, not a universal match contract |
| Python nonzero start / VM entry metadata | Reconstructable with caveats | Current match identity metadata carries relevant values, but a usable current entrant still has to exist |
| Preset name | Unavailable | Presets resolve to effective values; the general result artifact does not preserve the chosen preset identity |
| Development test timeout and other launcher-only controls | Unavailable or incomplete | Not all execution-envelope controls are result reproducibility fields, even when they can affect completion |
| Backend-specific external state | Reconstructable with caveats or unavailable | pMARS and legacy records have distinct schema/provenance limits |

Therefore Bytefray cannot promise safe one-click historical restoration or an
exact rerun. Copy Seed is correctly modest. Evaluation's **Test in Agent Lab**
reconstructs a useful diagnostic pairwise scenario from current sources, but it
does not pass every effective historical condition and must not be labeled an
exact rerun. A restoration feature requires an explicit source/revision archive
and persistence contract, plus honest degraded behavior when the original
revision no longer exists.

## 10. Navigation options evaluated

| Option | Assessment | Decision |
|---|---|---|
| A — keep all history in Tools | Functionally sound, but the menu now mixes one operation with three durable read-only browsing destinations. The distinction has become material after Phase 4 | Reject as the long-term organization |
| B — top-level History menu | Conventional, truthful, and low risk. It expresses application-level ownership while leaving every dialog, signal, artifact, and process path unchanged | **Implement in Phase 5** |
| C — unified History window | High complexity and poor model fit. Match occurrences, tournament parents, and analytical evaluations have incompatible metadata, integrity, loading, and actions; tabs would share a frame, not a coherent record abstraction | Defer/reject absent new evidence |
| D — contextual Designer plus global histories | Promising complement for the authoring loop, not a replacement for global histories. Stable agent matching and cross-source query APIs are prerequisites | Specify and prototype in a later phase |
| E — larger application-shell rethink | The “Designer” name understates current responsibilities, but rename, entry-point, packaging, and information-architecture consequences exceed this review | Dedicated later product phase |

### Menu decision

The implemented conceptual structure is:

```text
File
  package/file/application actions
Tools
  Run Tournament…
History
  Replay History…
  Tournament History…
  Evaluation History…
Help
  About Bytefray
```

This is not visual symmetry. The menu has three established sibling,
application-global, persistent browsing commands, while Tools has one operation
that starts work. “History” communicates read-only revisitation and scales to
future history-level actions without pretending the underlying views are one
data model. Existing action handlers and window modality remain unchanged.

## 11. Naming recommendation

The three current replay phrases describe different scopes:

- **Replay Browser**: a raw explicit-file picker in Advanced;
- **View Last Match**: a session-local shortcut to the last completed direct
  match, with file-picker fallback;
- **Replay History**: a persistent match-occurrence browser whose primary
  action is replay opening.

**Match History** is the most accurate eventual name for the indexed feature:
it includes result-only matches and treats replay availability as one field.
**Replay Library** incorrectly excludes result-only records; **Run History**
overstates coverage of parent workflows; **Battle History** introduces new
vocabulary without improving precision.

Phase 5 retains **Replay History**. The label is already documented and
recognizable, and an isolated rename would imply a broader product contract
before current-agent scoping, restoration, and parent linkage are settled. A
coordinated vocabulary follow-on may rename the feature to **Match History**
while updating window copy, documentation, accessibility labels, CLI/help
language, and the boundary with Replay Browser in one change.

## 12. Duplication audit

| Classification | Finding | Action |
|---|---|---|
| Intentional presentation reuse | Immediate result, parent history, global occurrence history, Development Test, and file browsers all provide replay-opening paths | Keep. The entry points start from different user context and converge on the existing Viewer launch service |
| Intentional presentation reuse | Tournament/Evaluation child matches appear in parent result views and in Replay History | Keep. Parent analysis and global occurrence search answer different questions |
| Intentional presentation reuse | Advanced Replay Browser and the bare Viewer picker both select external/raw replay files | Keep unless a later shell redesign removes one; their Qt/Pygame and dependency contexts differ |
| Acceptable minor duplication | View-specific labels, row summaries, and empty-state formatting | Keep local where domain meaning differs; reuse existing `ruleset_label` only where semantics are identical |
| Architectural debt | Tournament and Evaluation histories each synchronously scan/adapt their parent artifact directories | Measure separately before sharing machinery; background execution may be shared as a pattern, not a generic record model |
| Architectural debt | Fresh Evaluation Results and Evaluation History have separate presentation paths over related evaluation data | Preserve workflow distinction; consolidate typed formatting only when an observed inconsistency warrants it |
| Actual defect risk | Evaluation replay launch lacks the always-on click-time digest/association preflight used by Replay History and Tournament Results | Focused follow-on: define one Qt-free verified result-to-replay handoff and adopt it without schema changes |
| Lower-risk inconsistency | Session View Last Match trusts a path captured from the just-completed result rather than repeating the History preflight | Consider with the same focused integrity work; do not broaden Phase 5 navigation scope |

No filesystem scanner or parser should be unified merely because it reads JSON.
Tournament, evaluation, and occurrence discovery have different roots,
cardinality, damage handling, and domain objects.

## 13. Shared history architecture

Bytefray already has a sound common unit where one is needed: the canonical
match result/replay pair, identified by `match_id`, `result_id`, and for native
v2 results `occurrence_id`. Replay History adds a location identity for query
and legacy handling. Tournament and evaluation artifacts add their own parent
identity and structure.

A universal `RunRecord` or `HistoryEntry` is not justified. It would either be
a thin tagged union that adds little, or a lowest-common-denominator model that
loses standings, matrix roles, comparisons, methodology, and revision state.
The three history windows do not need a shared database to share a menu.

Useful future sharing should stay narrow:

1. a verified result-to-replay reference/preflight service;
2. an explicit parent-association descriptor for a match occurrence
   (`parent_kind`, stable parent ID, child coordinate, artifact location), if
   a demonstrated reverse-navigation workflow needs it;
3. common asynchronous task/presentation patterns where measurements show GUI
   blocking;
4. an explicit agent-reference/revision matching contract for contextual
   history.

Parent linkage must not be inferred solely from a pretty path and then exposed
as guaranteed identity. It should be derived and validated against the parent
artifact or added through a versioned persistence contract.

## 14. Scalability findings

### Replay History

The indexed/paged/read-worker design is appropriate for the current scale.
Committed qualification on a real 53,458-occurrence corpus (99.8 MB cache)
recorded cached rows on screen in 18–31 ms, a 27 ms worst GUI-thread block
during reconciliation, millisecond-scale page/detail reads, and roughly
7.5–8.5 s warm reconciliation. The browser remains usable while maintenance
runs.

Cold rebuild measurements varied substantially by session/environment: about
26 s in Phase 7B versus 279 s in Phase 7D and about 268.8 s after Phase 7E work.
The committed qualification does not attribute that difference to the reader
architecture and records no established root cause. Classification:

- cached browsing and normal warm use: **acceptable for normal expected use**;
- first open/cache loss at a 53k corpus: **approaching a practical limit** and
  open performance debt;
- response: investigate filesystem/environment sensitivity and rebuild cost;
  do not replace the existing index or change schemas in this phase.

Bulk discovery does not hash every full replay. Digest verification is deferred
to Open Replay, preventing replay size from becoming a routine query cost.

### Tournament History

Discovery is a shallow direct-child scan with synchronous JSON adaptation on
the GUI thread. This is **acceptable for normal expected usage** because one
artifact represents a tournament and typical counts are small. A very large
number of tournament folders or very large selected schedules could block the
UI. Measure before indexing; the first escalation should be background loading
and incremental presentation, not a database.

### Evaluation History

Discovery is also shallow but fully adapts and recomputes typed analytical
state. Existing measurements are approximately 18 ms for 10 artifacts, 182 ms
for 100, and 1.862 s for 1,000. This is **acceptable for expected usage but
approaching a practical UI limit near the measured 1,000-artifact case**
because it runs synchronously. A future phase should move scanning/adaptation
off the GUI thread before considering an index.

Neither parent history is loaded at Designer startup; the work begins when the
user opens the corresponding dialog.

## 15. Accessibility and usability observations

### Replay History

Replay History has the strongest explicit accessibility contract:

- filter labels have buddies and controls have accessible names;
- table selection is row-oriented and keyboard navigable;
- Enter, double-click, and the Open Replay button share one guarded action;
- text markers, not color alone, communicate approximate dates and health;
- status, empty, invalid, loading, and error states are explicit;
- technical paths are shown in selectable detail rather than truncated as the
  only source of meaning;
- Refresh/Cancel and unavailable replay states have explanatory text.

No clear Phase 5 defect warranted changing this UI.

### Tournament History and Results

The dialogs provide visible buttons as alternatives to row double-click,
single-row selection, readable empty/error states, selectable/wrapped paths,
and inline Replay unavailable explanations. Keyboard users can navigate tables
and activate focused buttons. However, several tables, status regions, and
buttons rely on visible text/default Qt semantics rather than explicit
accessible names/descriptions; row-level Enter activation and deliberate
initial focus are not consistently specified. These are later focused polish,
not reasons to redesign history.

### Evaluation History and Results

Lists have explicit action buttons rather than double-click-only behavior;
verification states use text as well as visual styling; long/detail text is
copyable. Weaknesses include sparse explicit accessible names/buddies, dense
list-row summaries whose full meaning can depend on tooltips, no search/filter
controls, synchronous scans/verification that can temporarily impede focus,
and an Open Replay enablement state that does not consistently explain all
integrity caveats. Address these in evaluation-specific accessibility and
integrity work.

### Session/file replay paths

View Last Match, Development Open Replay, Advanced Choose Replay/View Replay,
and the Viewer picker all have visible button paths and are not
double-click-only. Their similar labels reflect distinct scope, but the lack of
durable recency and the file-picker fallback should remain clear in tooltips
and documentation.

## 16. Required architecture answers

1. **Replay History's role:** application-global, artifact-backed match
   occurrence history with indexed search and verified replay opening.
2. **Designer boundary:** hybrid, effectively the main Bytefray desktop shell
   with authoring as its central context.
3. **Placement:** correct inside that shell; incorrect as an authoring-tab-only
   feature and unnecessary in Replay Viewer or a new executable.
4. **Tools:** history commands should not remain mixed with operational tools.
5. **History menu:** yes; three durable sibling browsing commands make the
   category meaningful.
6. **Separate histories:** yes. Matches, tournament parents, and analytical
   evaluations have different user questions and data contracts.
7. **Unified architecture:** no universal record/window/index is justified.
   Share only narrow identity, integrity, and asynchronous-work patterns.
8. **Current-agent history:** materially useful, especially in Agent
   Development, but current identity/query semantics are not reliable enough
   for implementation in this phase.
9. **Restore/rerun:** not safely as an exact operation. Effective settings are
   mostly recorded, but source/revision and some launcher intent are not.
10. **Deferred:** contextual activity, exact restore/revision contracts,
    parent reverse links, replay-preflight consistency, parent-history
    background loading, coordinated Match History naming, shell naming, and
    broader accessibility.

## 17. Decision and Phase 5 implementation boundary

**Decision: Case B.** The underlying placement and separation are sound, but a
clear information-architecture correction is both justified and low risk.

Phase 5 performs only:

- addition of the top-level **History** menu between Tools and Help;
- movement of the existing actions, ordered **Replay History…**, **Tournament
  History…**, **Evaluation History…**;
- retention of **Run Tournament…** as the sole Tools operation;
- focused tests for menu order, action ownership, enablement, and unchanged
  handler wiring;
- current user/architecture/manual documentation updates.

No dialog implementation, modality, signal, process gate, storage path, index,
artifact reader, viewer handoff, schema, or gameplay behavior changes.

## 18. Qualification

All Python invocations ran alone and used a fresh repo-local Windows
`--basetemp`; no pytest processes overlapped.

| Gate | Result |
|---|---|
| Direct menu/wiring nodes | **8 passed** in 1.56 s |
| Full three affected GUI modules | **118 passed** in 31.67 s |
| Complete application GUI suite: `pytest -m gui tests` | **489 passed, 6 deselected** in 146.77 s |
| Canonical headless repository suite: `pytest` | **3,639 passed, 21 skipped, 3 deselected** in 361.45 s |
| `ruff check .` | **Passed** |
| `mypy engine/src/battle_engine` | **Passed**, 113 source files |
| `mypy client/src/battle_client` | **Passed**, 16 source files |

The first sandboxed interpreter launch failed before pytest started because
Windows denied creation of `.venv/Scripts/python.exe`. The same repository
interpreter was therefore run outside the sandbox. The first external focused
invocation omitted `-m gui` and pytest correctly deselected all eight selected
GUI tests; it was rerun with the explicit marker and a different fresh temp
root. Neither event was a test failure, and neither is counted as a passing
gate above.

## 19. Deferred work and recommended follow-on phases

1. **History integrity consistency:** create/reuse a Qt-free click-time
   result-to-replay association, containment, existence, and digest preflight;
   adopt it in Evaluation Results/History and review session replay shortcuts.
2. **Contextual agent activity specification:** define “current agent,” stable
   identity/revision matching, false-positive behavior, and cross-source query
   APIs; prototype a compact Agent Development recent-activity view.
3. **Parent association/navigation:** only if user research shows value, add a
   validated tournament/evaluation parent association to match occurrences and
   a reverse “View Evaluation/Tournament” action.
4. **Parent-history responsiveness/accessibility:** move evaluation loading off
   the GUI thread first, measure tournament history, then address focus,
   accessible names/descriptions, status announcements, and action explanations.
5. **History vocabulary:** consider coordinated **Replay History → Match
   History** terminology after its contract is settled.
6. **Desktop-shell information architecture:** decide whether Agent Designer
   should retain its name or become a broader Bytefray desktop shell. Treat
   entry points, packaging, navigation, help, and migration together.
7. **Exact restoration research:** only after a versioned source/revision and
   full execution-envelope persistence contract exists. Do not infer source
   from hashes or silently rerun current code as if it were historical code.

Explicitly out of scope remain new replay/tournament/evaluation schemas,
database-backed parent history, cloud/user/sharing/leaderboard work, repository
modularization, major rename/accessibility systems, gameplay, and agent changes.

## 20. Final tree state

HEAD remains `cad229d84e1ee901c1930acaf34166031f6fc22a`; Phase 5 did not commit.
The working tree contains only the intentional Phase 5 paths:

- `app/agent_designer.py`;
- `app/views/replay_history.py`;
- `tests/test_v5_alpha1_phase2_menu_organization.py`;
- `tests/test_v5_alpha1_phase4_tournament_results.py`;
- `tests/test_v5_replay_history_browser.py`;
- `ARCHITECTURE.md`;
- `README.md`;
- `docs/MANUAL_SMOKE_TESTS.md`;
- `docs/TOURNAMENTS.md`;
- this review.

No artifact/schema/gameplay files and no local-only settings are changed.
The final `git diff --check` is clean. The final process audit found no Python,
pytest, Antigravity, Claude, Gemini, or checkout-related worker; only the
expected current Codex application process remained.
