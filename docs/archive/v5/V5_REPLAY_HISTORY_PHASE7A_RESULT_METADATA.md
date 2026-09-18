# Bytefray V5 — Phase 7A: Replay History Result Metadata

Date: 2026-09-11. **The result metadata contract is implemented. Replay
History discovery, indexing, and UI remain deferred to later phases.**

This phase implements the occurrence metadata selected by
[Phase 6](V5_REPLAY_HISTORY_PHASE6_ARCHITECTURE.md) while preserving the
artifact and gameplay boundaries established by
[Phase 5](V5_REPLAY_HISTORY_PHASE5_DISCOVERY.md). The canonical contract is
documented in [RESULT_SCHEMA.md](../../RESULT_SCHEMA.md).

## A. Starting state

| Item | Recorded value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD | `31ea802d929ce197a96270fe159e84d9a6b6bb00` |
| Upstream | `origin/v5-research` |
| Ahead / behind | `0 / 0`, measured from the existing local tracking ref |
| Working tree | Clean: no staged, modified, or untracked files |
| Product version | `5.0.0a1`, from `pyproject.toml` and the installed package metadata used by `project_info.get_project_info()` |
| Phase 6 report | Present and committed at starting HEAD `31ea802d929ce197a96270fe159e84d9a6b6bb00` (`docs(v5): define replay history architecture`) |

No unrelated user changes needed separation. No commit, push, reset, staging,
release, or version bump was performed in Phase 7A.

## B. Previous contract

The pre-Phase-7A writer emitted an explicitly versioned
`battle2.result` version 1 JSON object. `ResultEnvelope.as_dict()` was the
shared envelope serializer. Native finalization and the independent
pMARS/Redcode CLI path were its two production construction sites;
`write_json_atomic()` was the file writer and `read_result()` the typed parser.

The pre-change parser required exactly schema version 1. It ignored unknown
top-level fields. It raised `KeyError` for missing core fields accessed with
`data[...]`, defaulted some older/additive fields through `data.get(...)`, and
raised `ValueError` for an unsupported schema/version pair. If `replay` was
non-null, all three nested replay-reference fields were required.

| Field | Version 1 meaning | Writer shape | Production consumer(s) |
|---|---|---|---|
| `schema` | Protocol identifier, `battle2.result` | Always present; parser-required | All typed readers |
| `schema_version` | Wire version, previously `1` only | Always present; parser-required | All typed readers, project/About metadata |
| `result_id` | Deterministic identity of the outcome | Always present; parser-required | Tournament/evaluation resume, replay cross-checks |
| `match_id` | Deterministic semantic match identity | Always present; parser-required | Tournament/evaluation resume, replay cross-checks |
| `mode` | Native `b2` or pMARS `redcode94` | Always present; parser-required | Ruleset recovery, tooling |
| `status` | Completed artifact marker | Always `completed`; parser ignored it | Raw JSON tooling |
| `winner` | Winning slot or the `tie` sentinel | Always present; parser-required | Standings, Designer, evaluation analysis |
| `termination_reason` | Match termination vocabulary | Always present; parser-required | Designer and evaluation analysis |
| `ticks` | Final executed tick count | Always present; parser-required | Analysis and presentation |
| `score` | Final score by slot | Always present; parser default `{}` | Standings and analysis |
| `entrants` | Ordered identity, outcome, statistics, diagnostics, and runtime metadata | Always present; parser default empty | Standings, evaluation analysis, Designer |
| `reproducibility` | Seed and resolved execution configuration | Always present; parser default `{}` | Resume verification and historical recovery |
| `replay` | Replay identity, digest, and portable filename, or null | Always present; parser treated absence as null | Integrity verification and Viewer handoff |
| `backend` | Backend facts; populated for pMARS | Always present; parser optional | Raw tooling |
| `ruleset_id` | Exact native Ruleset; null/not applicable for pMARS; absent in older files | Current writer always present; parser optional | Ruleset provenance and replay checks |

The identifier audit was performed before choosing the v2 name. Local source,
tests, docs, and release-tag writers at `v0.3.0`, `v0.9.0`, `v1.0.0`,
`v2.0.0`, `v3.0.0`, `v4.0.0-alpha3`, and `b5.0.0-alpha1` all persist
`SCHEMA_NAME = "battle2.result"` and version 1. The v0.3.0 tree includes an
explicit expected `result.json` using that identifier. It is therefore an
already released protocol identity rather than a new use of the retired
internal product name.

## C. v2 contract

New native artifacts retain the complete v1 envelope and identify themselves
with:

```json
{
  "schema": "battle2.result",
  "schema_version": 2,
  "occurrence_id": "95cd0104-eadf-4e63-bfe0-191d1bba37f1",
  "completed_at": "2026-09-11T19:54:50.985486Z",
  "product_version": "5.0.0a1"
}
```

The three shown metadata fields are required in v2. All v1 fields and their
representations remain unchanged. `SCHEMA_VERSION_V1` and
`SCHEMA_VERSION_V2` name the two supported contracts; `SCHEMA_VERSION` points
to current native version 2. The pMARS writer explicitly selects v1.

The historical schema identifier is retained because changing only the v2
writer to `bytefray.result` would create two active names for one continuing
payload family. `bytefray.result` is deliberately rejected by the reader. New,
unrelated public contracts should use the Bytefray name. `battle2.replay` and
every other historical identifier remain unchanged.

## D. Occurrence identity

`occurrence_id` is a canonical lowercase, hyphenated UUID string. Production
generation uses the standard-library `uuid.uuid4()` function, so it is random
and independent of seed, `match_id`, agent content, and filesystem path.

The final match outcome reaches `_finalize_native_artifacts` only after actual
execution returns. The UUID is generated once at entry to that finalizer,
before replay/result serialization, and is passed into one frozen
`ResultEnvelope`. Serialization reads the stored value and never generates a
replacement. A second execution creates another finalizer invocation and a
new UUID, even when both executions have the same `match_id`.

## E. Completion timestamp

`completed_at` means the time when a finished native execution enters artifact
finalization. Production generation uses a timezone-aware UTC `datetime` and
emits ISO-8601 with microsecond precision and `Z`, such as
`2026-09-11T19:42:31.123456Z`.

It is captured alongside the occurrence UUID after the match outcome exists
and before either canonical file is serialized. It does not depend on local
timezone, filesystem mtime, a directory name, or replay write completion. If
replay publication later fails, the value still described execution
completion; the existing atomic cleanup removes the incomplete artifact set.

## F. Product version

`product_version` is a required non-empty v2 string obtained from the existing
canonical `battle_engine.project_info.get_project_info().version` mechanism.
That function uses `importlib.metadata.version("bytefray")`, with its existing
`development checkout` fallback when package metadata is unavailable. No
version literal was duplicated and the product remains `5.0.0a1`.

The import boundary is acyclic: `match_service` imports `project_info`, which
reads result/replay schema constants; neither `project_info` nor
`result_model` imports `match_service`. Native focused tests exercise the
source-checkout path. A disposable wheel was also built, installed into an
isolated Python 3.13 environment, and imported with the working directory
outside the source tree. Its module came from `site-packages` and reported
product version `5.0.0a1`, result schema version 2, and schema name
`battle2.result`.

## G. Backward compatibility

`read_result()` accepts v1 unchanged. A representative v1 fixture retains its
existing match ID, seed, winner, entrant metadata, replay reference, and
ruleset. Its new in-memory fields are explicitly:

```text
occurrence_id = None
completed_at = None
product_version = None
```

The parser does not derive fallbacks from mtime, directory names, `match_id`,
or the currently running Bytefray version. Reading the static fixture leaves
its bytes untouched and requires no migration.

`ResultEnvelope.schema_version` defaults to v1 so existing programmatic
construction of historical envelopes remains source-compatible. Production
native writing opts into v2 explicitly with its required metadata.

## H. Forward compatibility

Unknown top-level fields are ignored for both supported versions, matching the
released reader behavior and allowing harmless additive metadata. The schema
identifier must be exactly `battle2.result`; `bytefray.result` and other names
are unsupported. Versions must be real integers (a JSON Boolean does not count)
and must be 1 or 2. Missing, malformed, or future versions are rejected rather
than guessed.

## I. Validation rules

| Field | v2 validation | Failure behavior |
|---|---|---|
| `occurrence_id` | String that parses as UUID and exactly matches its canonical string form | `ValueError` naming `occurrence_id` |
| `completed_at` | Non-empty ISO-8601 string with timezone information and an effective UTC offset of zero | `ValueError` naming `completed_at` |
| `product_version` | Non-empty, non-whitespace string; version grammar is intentionally not overconstrained | `ValueError` naming `product_version` |
| `schema_version` | Integer 1 or 2, excluding Boolean | `ValueError` listing supported versions |

The reader preserves valid field text exactly. It does not normalize values
while parsing. Existing consumer boundaries already catch `ValueError` and
`KeyError` where they treat corrupt artifacts as unavailable or corrupted.

## J. Writer integration

`match_service._finalize_native_artifacts` remains the single native writer
boundary. It now constructs a v2 envelope for every native VM or Python match.
The existing call graph covers:

- `bytefray run`;
- Simple and Advanced Designer matches;
- headless tournament matches;
- `agents test` and Designer Development workflows;
- pairwise Evaluation;
- group Evaluation;
- direct callers of `NativeMatchService` used by development and
  qualification workflows.

No workflow was added and no artifact path changed. pMARS/Redcode bypasses the
native service as before and now explicitly selects result schema v1 to pin its
unchanged behavior.

## K. Reader/consumer audit

The typed production consumers all use `read_result()` and therefore receive
the same common fields from v1 and v2:

| Consumer | Fields used / behavior checked |
|---|---|
| `tournament_service` | Match/result IDs, ordered entrants, seed, replay digest/header, ruleset, winner and score for resume/standings |
| `agent_evaluation` | Match identity, entrants, reproducibility and replay integrity during resume |
| `evaluation_behavior` | Tick count and per-entrant state/statistics |
| `evaluation_capture` | Tick count and entrant termination/kill facts |
| `evaluation_group_analysis` | Winner, termination, ticks, scores and entrant statistics |
| `evaluation_history.v1_adapter` | Historical reproducibility recovery from nested results |
| `evaluation_history.verification` | IDs, ruleset, replay reference and digest/header consistency |
| `app.services.designer_workflows` | Winner, termination, replay path, entrants and resolved parameters |
| `result_model` integrity helpers | Replay filename and digest |
| qualification/research tools | Known named keys through typed or ordinary JSON-dict access; additive keys are ignored |

The replay client does not parse `result.json`; it consumes the unchanged
replay contract. Focused tests exercised historical v1 inputs and new native
v2 artifacts through tournament, Evaluation, Evaluation History, Designer,
agent-test, and analysis paths. Three hand-built consumer fixtures were pinned
to `SCHEMA_VERSION_V1` so they continue to test historical compatibility
rather than accidentally claiming to be incomplete v2 documents.

## L. Deterministic identity proof

The metadata values enter only the result-envelope constructor after
`canonical_match_id()` and `result_id` have been computed. They are absent from
both hash payloads and from replay construction. No identity, seed, gameplay,
ruleset, scheduler, scoring, winner, or termination implementation changed.

The new native regression runs byte-identical entrants twice with the same
seed/config/ruleset while injecting different occurrence metadata. It proves
equal `match_id`, `result_id`, replay ID, replay digest, complete replay bytes,
winner, score, and ticks. The occurrences differ. Existing direct
match-identity tests, the V5/ruleset suite, and the permanent Ruleset 4
equivalence corpus also pass without any baseline update.

## M. Serialization stability

A focused test constructs one v2 `ResultEnvelope`, serializes its `as_dict()`
to two files, and compares the parsed payloads. They are equal, including the
same `occurrence_id` and `completed_at`. The factories are never called from
`as_dict()` or `write_json_atomic()`.

## N. Test coverage

New coverage includes:

- representative static v1 fixture parsing without inferred metadata or file
  mutation;
- v2 model/file/parser round trip, including schema/version, occurrence,
  completion time, product version, match ID, seed, entrants, resolved params,
  outcome and ruleset;
- stable repeated serialization of one occurrence;
- tolerated unknown fields and rejected alternate schema-family name;
- missing/malformed UUID, timestamp, product version, schema version, and
  unsupported future version cases;
- real factory output format;
- two identical native executions with distinct occurrences and unchanged
  deterministic identity, replay bytes and gameplay result;
- existing pMARS assertion that its result remains schema version 1.

The focused writer/consumer run completed with **685 passed, 4 skipped**. Its
scope included result/model/reconstruction, Python and pMARS, tournament,
agent test, pairwise/group Evaluation, behavioral analysis, Designer adapters,
and all Evaluation History compatibility modules.

## O. Real artifact smoke

The real `python -m battle_engine run` workflow ran `writer` against `runner`
with seed `20260911`, arena 128, and two ticks. The production parser read its
fresh `result.json` and verified:

- schema `battle2.result`, version 2;
- canonical UUID `95cd0104-eadf-4e63-bfe0-191d1bba37f1`;
- UTC completion time `2026-09-11T19:54:50.985486Z`;
- product version `5.0.0a1`, equal to the canonical project-info value;
- deterministic match ID `match_1f40e821491e627c82462bd0`;
- winner `B` and score `{A: 0, B: 1.0}`;
- intact replay reference/identity.

The disposable smoke directory was removed after verification.

## P. Repeated-match smoke

The identical CLI matchup was run a second time with the same agents, seed,
arena, tick limit, starts, and ruleset resolution. Both artifacts had match ID
`match_1f40e821491e627c82462bd0`, the same result ID, same replay ID,
byte-identical replay files, winner `B`, and equal scores. The second
occurrence UUID was `31e66184-e410-4aba-a764-7f7e2bd39b4a`, distinct from the
first, and its completion time was `2026-09-11T19:55:02.055651Z`, also
distinct. No sleep or timing dependency was used. Both files parsed through
`read_result()` and were then removed.

## Q. Files changed

| File | Reason |
|---|---|
| `engine/src/battle_engine/result_model.py` | Define v1/v2 constants, occurrence factories, v2 fields and validation, compatible parsing/serialization |
| `engine/src/battle_engine/match_service.py` | Capture native occurrence metadata once and write current v2 |
| `engine/src/battle_engine/cli.py` | Pin unchanged pMARS/Redcode output to v1 |
| `engine/src/battle_engine/evaluation_capture.py` | Correct consumer documentation to state v1/v2 support |
| `engine/tests/fixtures/result/battle2_result_v1.json` | Add representative immutable historical v1 fixture |
| `engine/tests/test_result_model.py` | Cover v1 compatibility, v2 round trip/validation, factories, and repeated serialization |
| `engine/tests/test_replay_reconstruction.py` | Prove repeated native-run identity/gameplay/replay isolation |
| `engine/tests/test_evaluation_behavior.py` | Keep its hand-built historical fixture explicitly v1 |
| `engine/tests/test_evaluation_capture.py` | Keep its hand-built historical fixture explicitly v1 |
| `engine/tests/test_evaluation_group_analysis.py` | Keep its hand-built historical fixture explicitly v1 |
| `docs/RESULT_SCHEMA.md` | Define the canonical v2 wire/lifecycle/compatibility contract and naming decision |
| `README.md` | Update the current artifact-version summary |
| `ARCHITECTURE.md` | Update the native artifact boundary and component diagram |
| `docs/COMPATIBILITY.md` | Record native v2 with historical/pMARS v1 retention |
| `docs/TOURNAMENTS.md` | Update the tournament result contract reference to native v2 |
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7A_RESULT_METADATA.md` | Record this implementation and evidence |

No replay module, replay schema document, gameplay module, run-layout code,
preset code, or generated artifact is in the diff.

## R. Validation

| Check | Result |
|---|---|
| Initial model/native focused tests | 37 passed |
| Focused result writers and consumers | 685 passed, 4 skipped |
| V5/ruleset-focused regression | 578 passed |
| Permanent Ruleset 4 equivalence corpus | 23 passed |
| Engine mypy | Success, 107 source files |
| Client mypy | Success, 16 source files |
| Disposable wheel build/import | Passed; installed package reported `5.0.0a1`, result v2, `battle2.result` |
| `ruff check .` | Passed: `All checks passed!` |
| Full `python -m pytest --basetemp=.pytest-tmp/phase7a-full-clean-2` | 3427 passed, 21 skipped, 3 deselected in 348.29s |
| `git diff --check` | Clean |
| Untracked-file whitespace/conflict-marker scan | Clean for the new report and v1 fixture |
| Final status | 14 modified tracked files and 2 intended untracked additions; nothing staged |

No expected gameplay output or golden baseline was changed.

Two earlier full attempts each encountered one transient Windows
`PermissionError` while atomically replacing an `evaluation.json`, in two
different tests and paths. Both match the documented repo-local Windows
temp/ACL failure class, occurred outside the changed result-artifact write,
and passed immediately when rerun alone in fresh repo-local temp directories
(1 passed each). The final complete clean-temp run above passed all 3427
selected tests.

## S. Compatibility risks and deferred items

- Historical v1 artifacts have no authoritative occurrence UUID, completion
  time, or product version. The parser intentionally reports `None`; Phase 7B
  may define explicitly labeled discovery fallbacks without changing this
  artifact truth.
- pMARS/Redcode remains v1 and has none of the new fields, as required by this
  phase's protected boundary.
- The `_loose` run location remains overwrite-prone. Phase 7A does not change
  directory layout or preservation policy.
- Product-version resolution retains the existing `development checkout`
  fallback when distribution metadata is absent. Normal source development
  and packaged installs expose `5.0.0a1`; no packaging boundary problem was
  found.
- The disposable wheel build repeated existing setuptools license-metadata
  deprecation warnings. They are unrelated to result metadata and do not
  affect the successful build/import check.
- Preset identity remains deliberately absent. Resolved Agent Params continue
  to be recorded exactly as before.

No new blocking issue was discovered.

## T. Recommended Phase 7B inputs

Phase 7B can rely on `result.json` as the authoritative occurrence record:

1. accept both `battle2.result` v1 and v2 through `read_result()`;
2. use the v2 `occurrence_id` as occurrence identity and never collapse rows
   merely because their deterministic `match_id` values match;
3. sort/filter v2 rows by authoritative `completed_at` and label any v1
   filesystem-time fallback as inferred rather than artifact truth;
4. expose `product_version` when present and `unknown` for v1;
5. preserve rows whose replay is absent while recording replay availability as
   a separate capability;
6. treat unknown schema versions and malformed v2 metadata as isolated
   per-artifact health states;
7. build only a disposable/rebuildable SQLite metadata cache whose deletion
   cannot affect source artifacts;
8. keep replay parsing lazy and use existing digest verification at playback
   or deep-verification boundaries;
9. keep preset-name inference deferred and display already recorded resolved
   parameters instead.

Phase 7B should not alter result/replay schemas, gameplay identity, replay
playback, or artifact directory layout.
