# Bytefray V6 Phase 2 Final Qualification

## A. Executive summary

### Initial qualification — committed HEAD

**Verdict: NOT QUALIFIED.**

Phase 2 materially reduced both repository size and active runtime complexity,
but the committed post-2B.12 tree has a historical-fixture integrity defect.
Independent qualification stopped at the first correctness blocker, as required.

1. **Physical reduction:** from the Phase 0 commit
   `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` to the committed Phase 2 candidate
   `3caf143e332ce9ad627442409a7239a4e7025581`, tracked Python code fell from
   **178,156 to 152,742 LOC**, a reduction of **25,414 LOC (14.27%)**. Tracked
   files fell from **821 to 724** (97 files, 11.81%).
2. **Active-complexity reduction:** executable Rulesets fell **8 -> 1**
   (87.5%), active Agent API generations **2 -> 1** (50%), runtime dispatch
   families **3 -> 1** (66.67%), active starters **21 -> 10** (52.38%), and
   legacy Ruleset-1 fallback paths **4 -> 0** (100%). New execution is now the
   Ruleset-4 / Agent-API-v2 process model only.
3. **Historical compatibility retained:** all eight recorded Ruleset identities,
   old result/replay/trace schemas, Agent-API-v1 metadata, VM-originated artifact
   provenance, Redcode result provenance, historical evaluation methodologies,
   Replay History, and core-status presentation remain reader concerns. Exact
   old-engine reproduction belongs to historical tags/releases, not the current
   executable registry.
4. **Ruleset 4 remained frozen in the evidence reached:** the exact permanent
   eight-module control gate passed **152/152** on the committed tree, including
   the interceding-execution state-isolation regression.
5. **Phase 3 readiness:** **no**. The historical-reader gate failed 3 cases
   because a committed schema-6 group fixture records the SHA-256 of its former
   CRLF replay bytes while Git enforces and stores LF bytes. The untampered
   fixture therefore fails integrity verification. This requires an explicit
   remediation and complete requalification of the new commit before Phase 3.

The governing Phase 2 result remains valid as an architectural direction:

> **Phase 2 reduced the number of things Bytefray must actively execute and
> reason about. Phase 3 will determine whether the things that remain are
> organized around the concepts developers actually need to change.**

Phase 3 must not begin until the blocker in sections F, Y, and AB is remediated
and the full serial gate sequence passes on the resulting committed tree.

### Post-remediation closure — current working tree

**Verdict: QUALIFIED.**

The initial result above remains authoritative for committed HEAD `3caf143e`;
it has not been rewritten into a success. A narrow working-tree remediation
corrected only the stale replay digest metadata, added a raw-byte regression,
and reran the required gates. Sections AC and AD record that separate evidence
and verdict. No commit or push was performed, so this qualification applies to
the exact reviewed working tree over `3caf143e`, not to a new commit.

## B. Final repository baseline

Baseline checks were made before creating this report.

| Fact | Measured value |
| --- | --- |
| Branch | `v6-research` |
| Candidate HEAD | `3caf143e332ce9ad627442409a7239a4e7025581` |
| `origin/v6-research` after fetch | same SHA; 0 ahead / 0 behind |
| Local and remote `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` |
| Candidate divergence from `main` | 22 ahead / 0 behind |
| Initial working tree | clean |
| Initial Python/pytest processes | 0 |
| Initial `.pytest-tmp*` roots | 0 |
| Tracked files | 724 |
| Tracked `.py` files | 361 |
| Tracked Python LOC | 152,742 |
| Tracked `test_*.py` files | 153 (106 engine, 16 client, 1 `_legacy`, 30 root GUI) |
| Canonical collection recorded by committed 2B.12 report | 2,932 discovered; 2,929 selected |
| Executable Rulesets | 1: `bytefray-rules-4` |
| Active Agent API generations | 1: Agent API v2 |
| Active runtime | Python process-agent runtime |
| Bundled active starters | 10 API-v2 starters |
| Scaffold templates | 2 API-v2 directories: blank and annotated |

Source verification, rather than documentation alone, established the active
boundary:

- `ruleset_policy._RULESET_POLICIES` contains only `RULESET_V4`;
- `OMITTED_RULESET_CANDIDATES` contains only `bytefray-rules-4`;
- `SUPPORTED_AGENT_API_VERSIONS == frozenset({2})`;
- scaffold default is API v2 and the template map has only its two v2 variants;
- the starter package contains six `v4_*` and four `v5_*` manifests; and
- Simple, Evaluation, and full Designer option tuples each contain only stable
  Ruleset 4.

The committed 2B.12 report still describes its own pre-commit handoff state at
`b6d2e09c...`; that was accurate when written but is not the final baseline.
Commit `3caf143e...` is the first committed Scope-C implementation candidate and
is the object qualified here.

## C. Qualification environment

| Component | Version / value |
| --- | --- |
| OS | Windows 11 `10.0.26120`, AMD64 |
| Python | 3.13.14, MSC v.1944 64-bit |
| pytest | 9.1.1 |
| ruff | 0.16.3 |
| mypy | 2.3.1 |
| PySide6 | 6.11.2 |
| pygame-ce | 2.5.8 |
| PyYAML | 6.0.3 |
| PyInstaller | 6.22.2 |
| build | 1.6.0 |

All executed gates were serial. A first Gate-A invocation used a nested
`--basetemp` whose parent did not exist; Windows pytest created no parents and
reported 47 setup errors after 105 tests passed. No product assertion failed.
That invalid harness run was discarded, no source changed, and the identical
gate was rerun with a flat repo-local basetemp. This reproduces a Windows
basetemp caveat already documented by Phase 2B.6.

## D. Ruleset-4 frozen-control qualification

The required permanent gate ran these exact modules:

- `test_v4_stable_ruleset_equivalence.py`
- `test_v4_runtime_default_ruleset.py`
- `test_v4_historical_immutability.py`
- `test_v4_alpha2_placement.py`
- `test_v4_alpha2_scheduler.py`
- `test_v4_process_semantics.py`
- `test_v4_trace_equivalence.py`
- `test_v4_production_integration.py`

Result: **152 passed, 0 skipped, 0 failed, 0 errors in 7.20 s**.

This includes
`test_live_stable_v4_control_is_immune_to_interceding_execution`, the permanent
state-isolation regression created during the Scope-C forensic repair. No golden
was regenerated or re-blessed.

## E. Scope-C retirement-boundary qualification

The committed boundary gate covered the permanent Scope-A and Scope-B
retirement tests plus policy/default resolution, API validation, worker reset,
`agents test`, scaffolding, package inspection/import, match service, and CLI
characterizations.

Result: **391 passed, 2 skipped, 0 failed, 0 errors in 45.81 s**.

The reached evidence confirms:

- Rulesets 1/2 and all five retired alpha identities cannot execute;
- omitted resolution does not select a retired identity;
- API-v1 and VM/blob execution are rejected;
- API-v1 packages remain inspectable but cannot be imported for execution;
- worker-side API rejection remains independent of caller validation;
- `agents test` rejects API v1 before agent import and artifact creation; and
- current Ruleset-4 / API-v2 execution remains valid.

## F. Historical-reader qualification

The gate covered client replay analysis/session/status; evaluation history
adapters, comparison, verification, revisions, CLI and workflows; frozen group
methodology helpers; result/replay reconstruction; Replay History indexing and
concurrency; ruleset persistence; and history presentation.

Result: **632 passed, 2 skipped, 3 failed in 25.08 s**.

All three failures are in
`engine/tests/test_evaluation_history_verification.py`:

1. `test_frozen_schema6_group_cell_is_readable_and_deep_verifiable`
2. `test_frozen_schema6_group_cell_rejects_corrupt_entrant_order`
3. `test_frozen_schema6_group_cell_rejects_wrong_recorded_match_id`

The first is the primary failure. The latter two cannot reach their intended
checks because the same earlier replay-integrity check fails first.

The affected committed fixture is:

`engine/tests/fixtures/v6_scope_c_group_evaluation/matches/0009-group-core_seeker-claimer-hunter-seed1-spread-shifted/replay.jsonl`

Exact byte evidence:

| Form | Bytes | SHA-256 |
| --- | ---: | --- |
| Committed/checked-out LF replay | 165,919 | `2fbf7c04432467a8ab5b0204871189f8bca98f8a82978b730b6a4837844e6a56` |
| CRLF transform of the same 101 lines | 166,020 | `e9cb516d58de5233d067d4eba94951a75f917b7101648601f32d92b9b95e5504` |
| Digest recorded by `result.json` | — | `e9cb516d58de5233d067d4eba94951a75f917b7101648601f32d92b9b95e5504` |

`git ls-files --eol` reports `i/lf w/lf attr/text=auto eol=lf` for both fixture
files, and `.gitattributes` explicitly enforces LF. The result metadata was
captured from the pre-commit CRLF working-tree form, but Git normalized the
replay on commit. Thus the previous uncommitted 2B.12 run could pass while the
committed tree cannot.

This is a **BLOCKER**, not a reason to weaken digest verification. No repair was
made in this accounting phase.

## G. Current-product workflow qualification

**Not run after Gate C failed.** The phase charter requires qualification to
stop on a correctness blocker.

The pre-commit 2B.12 report records **925 passed, 5 skipped** for its current
workflow gate, covering default/explicit run, scaffold, agent test/evaluate,
Tournament, Agent Package, Designer launch paths, history, replay, and starter
discovery. That is useful inherited evidence about the source changes, but it is
not independent final qualification of commit `3caf143e...`.

## H. Canonical pytest result

**Not run.** In particular, the earlier **2,911 passed, 18 skipped, 3
deselected** run is not cited as final Phase 2 qualification: it ran before the
Scope-C fixture was committed and therefore did not test the LF-normalized bytes
now in Git.

The committed 2B.12 report's collection accounting remains the current expected
shape: 2,932 discoverable, 2,929 selected, 2,911 passing, 18 skipped, and 3 GUI
deselected. A clean canonical run must establish the actual post-remediation
result; these values must not be forced.

## I. GUI qualification

**Not run after the blocker.** The pre-commit 2B.12 result of **499 passed, 510
deselected** remains inherited evidence only. It is not promoted to this
committed candidate's final qualification record.

## J. Ruff / mypy qualification

**Not run after the blocker.** The pre-commit 2B.12 evidence was:

- ruff: all checks passed;
- engine mypy: clean across 90 source files; and
- client mypy: clean across 16 source files.

Those results should be rerun after the explicit fixture remediation and before
the replacement canonical suite.

## K. Packaging qualification

No fresh build was started after the blocker. The same source commit contains
the 2B.12 packaging boundary, whose pre-commit evidence records:

- successful wheel and sdist builds;
- all four Windows frozen applications built successfully;
- 10 current starter manifests and two current API-v2 templates where
  applicable;
- retained historical result/replay/evaluation readers; and
- zero forbidden VM executors, builtin/opcode modules, API-v1 execution
  templates/starters, retired benchmark corpora, or Redcode/pMARS payload.

That evidence was inherited, not freshly reproduced here. No installed-app
lifecycle run was performed or claimed. After remediation, package-content
inspection must be rerun; an installer lifecycle is unnecessary unless a
packaging input changes or the remediation affects packaged content.

## L. Phase 0 -> Phase 2 metric table

Counts compare Phase 0 commit `82549f9c...` with committed candidate
`3caf143e...`. Python LOC uses newline count, matching Phase 0's `wc -l`
method. `test_*.py` means tracked test modules by filename, including the root
GUI suite. Canonical cases are selected cases.

| Dimension | Phase 0 / before cleanup | Final Phase 2 candidate | Absolute change | % change |
| --- | ---: | ---: | ---: | ---: |
| Tracked files | 821 | 724 | -97 | -11.81% |
| Tracked `.py` files | 430 | 361 | -69 | -16.05% |
| Tracked Python LOC | 178,156 | 152,742 | -25,414 | -14.27% |
| Tracked `test_*.py` files | 190 | 153 | -37 | -19.47% |
| Selected canonical tests | 3,709 | 2,929 expected from committed 2B.12 accounting | -780 | -21.03% |
| Executable Ruleset identities | 8 | 1 | -7 | -87.50% |
| Active Agent API generations | 2 | 1 | -1 | -50.00% |
| Active runtime families | 3 (VM/blob, Python API v1, process API v2) | 1 (process API v2) | -2 | -66.67% |
| Runtime dispatch arms before/after Scope C | 3 | 1 | -2 | -66.67% |
| Replay schema writers | 2 (schema 3 and 4) | 1 (schema 4) | -1 | -50.00% |
| Trace schema writers | 2 (v1 and v2) | 1 (v2) | -1 | -50.00% |
| Bundled active starters | 21 | 10 | -11 | -52.38% |
| Executable reference agents | 4 | 0 | -4 | -100.00% |
| Scaffold template pairs | 2 API generations | 1 API generation | -1 | -50.00% |
| Ruleset choices on each full CLI surface | 5 | 1 | -4 | -80.00% |
| Full Designer Ruleset choices | 5 | 1 | -4 | -80.00% |
| Legacy Ruleset-1 fallback paths | 4 | 0 | -4 | -100.00% |
| Recorded Ruleset identities understood by readers | 8 (+ historical alias) | 8 (+ historical alias) | 0 | 0% |
| Distributable legacy execution payload | present | absent by package policy | qualitative removal | n/a |

The Phase 0 report incorrectly listed 18 starter directories; Git at the Phase
0 commit contains **21** starter manifests, matching the later Scope-C audit:
4 VM, 7 API v1, and 10 API v2. The table uses the directly measured 21.

## M. Physical code reduction

| Python category | Phase 0 LOC | Candidate LOC | Change | % change |
| --- | ---: | ---: | ---: | ---: |
| Production (`engine/src`, `client/src`, `app`) | 69,597 | 63,317 | -6,280 | -9.02% |
| Test modules (`test_*.py`) | 88,929 | 73,708 | -15,221 | -17.12% |
| Test support modules (for example `conftest.py`) | 818 | 818 | 0 | 0% |
| Tools/research (`tools/`) | 16,352 | 12,809 | -3,543 | -21.67% |
| Tracked root agent fixtures (`agents/`) | 1,378 | 1,008 | -370 | -26.85% |
| Frozen `_legacy` non-test source | 1,082 | 1,082 | 0 | 0% |
| **Total** | **178,156** | **152,742** | **-25,414** | **-14.27%** |

This corrects Phase 0's internally inconsistent per-directory test subtotal
while preserving its correct aggregate `test_*.py` LOC of 88,929. The category
deltas reconcile exactly to the total.

Non-Python assets should not be folded into a code-LOC percentage. They moved
in the opposite byte direction because Phase 2 added detailed reports and
committed historical fixtures:

- non-Python tracked files: 391 -> 363 (-28);
- non-Python blob bytes: 10,171,846 -> 11,050,671 (+878,825);
- Markdown: 206 -> 219 files and 5,799,679 -> 6,527,759 bytes; and
- total tracked blob bytes: 17,279,275 -> 17,142,888 (-136,387, 0.79%).

The report itself is untracked and is not included in these committed-snapshot
measurements.

## N. Active-complexity reduction

The decisive reduction is not the 14.27% Python LOC change. It is the collapse
of the active execution state space:

- 8 executable identities became 1;
- two Agent API generations became one;
- VM/blob, API-v1 Python, and API-v2 process dispatch became one process arm;
- two replay/trace writer generations became one each;
- four silent Ruleset-1 fallback routes became zero;
- five CLI/Designer choices became one; and
- 21 heterogeneous starters became 10 current API-v2 starters.

Every removed arm previously multiplied the combinations that selection,
validation, execution, evaluation, persistence, GUI, packaging, tests, and docs
had to reason about. Readers preserve old data shapes, but readers no longer
pull retired executors into the active registry. That separation is a larger
maintenance improvement than the raw line reduction suggests.

## O. Ruleset retirement ledger

| Identity | Phase 0 state | Final state | Historical recognition |
| --- | --- | --- | --- |
| `bytefray-rules-1` | executable; VM or API-v1 Python; product choice | historical only; retired in Scope C | retained in result/replay provenance and readers |
| `bytefray-rules-2` | executable API-v1 Python; product/evaluation choice | historical only; retired in Scope C | retained, including methodology/core-status interpretation |
| `bytefray-rules-2-alpha1` | executable frozen alpha, not product-selectable | historical only; retired in Scope A | retained; never aliased to a live Ruleset |
| `bytefray-rules-2-alpha11` | executable frozen alpha, not product-selectable | historical only; retired in Scope A | retained; promotion evidence is historical |
| `bytefray-rules-3-alpha1` | executable closed research identity | historical only; retired in Scope A | retained in artifact provenance/readers |
| `bytefray-rules-4-alpha1` | executable/selectable frozen prerelease | historical only; retired in Scope B | pinned fixture and historical-reader support retained |
| `bytefray-rules-4-alpha2` | executable/selectable frozen prerelease | historical only; retired in Scope B | promotion-equivalence evidence frozen, not re-blessed |
| `bytefray-rules-4` | executable stable default | sole executable frozen control | current and historically readable |

Recognition is not execution. None of the seven retired IDs is registered or
silently mapped to stable Ruleset 4.

## P. Runtime retirement ledger

### Redcode/pMARS

Phase 2B.6 removed the external executor, CLI mode, CI workflow, build tooling,
eight `.red` warriors, Windows pMARS binary/licensing payload, and dedicated
tests. Exact measured implementation totals were:

- 17 full files and 235,610 tracked bytes removed;
- 21 canonical tests removed;
- 423 net production LOC removed (`pmars.py` plus CLI branch);
- 337,050 bytes removed from the two Windows frozen trees that had bundled it;
- canonical transition 3,734 -> 3,713; and
- historical `redcode94` result/replay interpretation retained.

### Obsolete tournament harness

Phase 2B.3 removed the broken root-level developer harness, not the supported
Tournament product:

- 8 harness files, 982 LOC, 38,365 bytes;
- 1 dedicated test file, 161 LOC, 5,116 bytes, 7 tests;
- total: 9 files, 1,143 LOC, 43,481 bytes; and
- canonical transition 3,741 -> 3,734.

### Agent API v1

Scope C removed API-v1 controller and worker execution branches, two API-v1
scaffold directories, seven active API-v1 starters, four executable reference
agents, new Ruleset-2 group evaluation, and v1-specific evaluation/test/runtime
branches. Historical API-v1 datatypes and metadata remain for deserialization,
inspection, labels, and provenance.

### VM/blob

Scope C removed assembler/instruction execution, the native VM match runner,
builtin registry, blob/builtin dispatch, and four VM starter choices from all
product surfaces. `instructions.py`, `match.py`, `builtins/registry.py`, and
the executable reference-agent registry were deleted.

### Intentionally retained shared/historical pieces

- the arena/storage subset of `vm.py` (now 77 LOC), still used by the process
  runtime;
- historical Agent API datatypes and `ActionKind` shapes needed by readers;
- result/replay/trace schema readers and Ruleset ID constants;
- evaluation methodology tables and predicates used for old summaries;
- `supervised_runtime.py` diagnostic helpers used by Ruleset 4;
- vulnerable-core helpers consumed by replay status presentation; and
- `api_version` in metadata, worker protocol, and deterministic seed material.

The last item is single-valued today but behaviorally significant: deleting it
would change every Ruleset-4 entrant seed.

## Q. Starter-agent before/after

Phase 0 and the pre-Scope-C tree carried 21 active starters:

- VM: `runner`, `writer`, `seeker`, `spiral`;
- API v1: `adaptive`, `claimer`, `hunter`, `raider`, `sentinel`, `strider`,
  `wanderer`; and
- API v2: `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`,
  `v4_local_defender`, `v4_quorum`, `v4_scout`, `v5_core_defender`,
  `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker`.

Final active catalogue: the ten API-v2 starters only.

The VM and API-v1 starters were removed because no current Ruleset can execute
them. In particular, the three Ruleset-2 benchmark corpora and their five
content-addressed API-v1 members (`adaptive`, `claimer`, `hunter`, `strider`,
`wanderer`) were deliberately removed rather than kept as museum fixtures.
`raider` and `sentinel` were obsolete Ruleset-2 demonstrations. Exact historic
content remains available from Git history and releases.

## R. Test-suite before/after

The selected canonical sequence reconciles exactly:

| Checkpoint | Selected tests | Delta |
| --- | ---: | ---: |
| Phase 0 | 3,709 | — |
| Phase 2A dead exploratory test removed | 3,707 | -2 |
| Phase 2B.1 permanent starter regressions added | 3,741 | +34 |
| Obsolete tournament harness removed | 3,734 | -7 |
| Redcode/pMARS retired | 3,713 | -21 |
| Scope A retired | 3,444 | -269 |
| Scope B retired | 3,440 | -4 |
| Scope C committed candidate (initial qualification) | 2,929 | -511 |
| Post-remediation working tree | 2,930 | +1 |
| **Phase 0 -> remediated working tree** | **2,930** | **-779** |

For Scope C specifically, the committed 2B.12 accounting establishes 3,443
discoverable / 3,440 selected before and 2,932 discoverable / 2,929 selected
after. The unchanged three GUI deselections make both deltas exactly **-511**.
Whole-module retirement removed 420 cases; surviving/resource-driven
parametrization lost 106; 15 current boundary and reader tests were added or
restored: `-420 - 106 + 15 = -511`.

Fewer tests are not automatically less coverage. Tests whose subject was a
retired executor were removed. Tests whose subject was a current reader or
workflow but whose fixture generator used old execution were converted to
current execution or committed artifacts. Permanent negative-boundary,
state-isolation, methodology, and package-exclusion tests were added.

The current blocker demonstrates why collection arithmetic alone is
insufficient: the intended frozen group-reader coverage exists, but its
committed bytes do not satisfy its own digest.

The remediation adds exactly one case to
`engine/tests/test_evaluation_history_verification.py` (31 -> 32). Therefore
the post-remediation tree has 2,933 discoverable / 2,930 selected cases. The
original Scope-C committed-candidate accounting remains 3,443 -> 2,932
discoverable and 3,440 -> 2,929 selected; the final working-tree delta from the
pre-Scope-C baseline is 3,443 -> 2,933 (-510) discoverable and 3,440 -> 2,930
(-510) selected.

## S. Documentation/archive accounting

Phase 2A moved **79** closed research documents (31 V4 and 48 V5; 2,347,799
bytes at audit time) from active research to the historical archive without
deleting them. Current compatibility, Ruleset, authoring, packaging, and
architecture docs were updated throughout the retirement phases, while
archived research was deliberately not rewritten for present-day terminology.

The pMARS sidecar estimate was corrected by direct blob measurement: the five
orphaned sidecars removed in Phase 2A total **138,681 bytes**, not the Phase 1
rough estimate of about 276 KB. The abandoned Linux-package workflow did not
have a pull-request trigger; it had manual dispatch plus a stale
`v4-rc2-development` push trigger. Phase 2 removed that stale push trigger and
kept manual dispatch.

Two current-documentation issues remain and were not opportunistically edited:

- `ARCHITECTURE.md` lines 194-200 still describe the already-deleted
  `pygame_canvas.py` as present unused code, repeating the false Phase 0 claim
  that Phase 1 disproved; and
- current specs still describe obsolete environment-variable fallbacks and
  predecessor command names, while `AGENTS.md` correctly says `BYTEFRAY_ROOT`
  is the only supported data-root variable.

`docs/ROADMAP.md` also still presents Phase 2B.12 as the immediate next phase,
which was expected to be updated only after final qualification. These are
recorded as documentation debt; the blocker prevents marking Phase 2 complete.

## T. Packaging/payload accounting

Measured simplifications include:

- 235,610 tracked bytes of Redcode/pMARS full-file payload removed;
- 337,050 bytes removed from the two affected Windows frozen trees;
- 38,365 source bytes of obsolete tournament harness plus 5,116 test bytes
  removed;
- VM executor modules and builtin registry removed from distributable code;
- API-v1 templates, seven old starters, and executable reference agents
  removed;
- three obsolete benchmark corpora removed; and
- final package policy narrowed to ten current starters and two API-v2
  templates.

Source-tree byte deletion, package payload reduction, and test-only reduction
are intentionally not combined into a single savings percentage. The committed
2B.12 inspection found all four frozen payloads free of forbidden retired data
and the unified archive free of retired executor modules while retaining
history readers. Fresh post-remediation reproduction remains required.

## U. Historical compatibility ledger

V6 still understands:

- all eight Ruleset IDs and the historical `evaluation-rules-1` alias;
- recorded result provenance and runtime kind;
- replay schemas 1-4, including VM-originated schema-3 and process schema-4;
- trace schemas v1 and v2;
- historical pairwise/group/v4 evaluation methodology and identity data;
- vulnerable-core status for Ruleset-2-family artifacts;
- winner, termination, placement, labels, filters, and entrant identity;
- Replay History indexing and replay handoff; and
- evaluation-history comparison across retained schema generations.

V6 deliberately no longer:

- executes any Ruleset other than `bytefray-rules-4`;
- executes Agent API v1;
- executes VM/blob/builtin agents;
- invokes Redcode/pMARS; or
- regenerates retired benchmark/equivalence evidence.

Historical releases and tags are the reproduction mechanism for old engines.
Current readers must not depend on the executable registry. The Gate-C defect
is precisely a failure to preserve one committed artifact's byte integrity,
not evidence that its retired executor should return.

## V. Phase 1/2 corrections and superseded findings

### Phase 1

- `pygame_canvas.py` was not dead code waiting to be removed; it had already
  been deleted before v1.4. Phase 0 and current `ARCHITECTURE.md` prose were
  stale.
- A sub-audit's tracked-`.pyc` claim was false; no `.pyc` was tracked.
- `bytefray-brand-sheet.png` was initially a deletion candidate based on zero
  runtime references, but the product decision retained it as the visual
  generator master rather than treating functional imports as the only form of
  value.
- The obsolete tournament harness was more than an orphaned folder: it had a
  broken missing-build-script pipeline and coupling to frozen legacy assembler
  fixtures. Phase 2 measured and retired the whole boundary.
- `warriors/` was not coupled to that tournament harness. It belonged to the
  separate pMARS/Redcode path and was audited and retired separately.
- Phase 0's per-directory test file/LOC split was internally inconsistent;
  final accounting uses reproducible Git-path definitions.

### Phase 2A

- 79 V4/V5 reports were moved, not deleted.
- The five pMARS sidecars were exactly 138,681 bytes, not ~276 KB.
- The Linux-package workflow did not run on pull requests; its stale surface
  was one abandoned-branch push trigger, plus manual dispatch.
- The dead exploratory test was exactly one 71-line module containing two
  collected tests; the related CI cleanup was separate.

### Phase 2B.1

- Phase 0's initial 56 failures were not corrupt bundled production starters.
  Production starter refresh already treated empty/cache-only directories as
  absent.
- The real defect was duplicated test bootstrap code using `.is_dir()` instead
  of semantic agent discovery. It was fixed and protected with 34 cases.

### Tournament

- Actual removal: 8 harness files / 982 LOC / 38,365 bytes plus one 161-LOC,
  5,116-byte, 7-test module. The supported Tournament service remained.

### Redcode/pMARS

- Actual removal: 17 full files, 235,610 bytes, 21 tests, 423 net production
  LOC, and a 3,734 -> 3,713 canonical transition.
- Historical Redcode result readability remained; the executable and bundled
  GPL payload did not.

### Ruleset retirement and Scope C

- The audit discovered two unlisted executable identities,
  `bytefray-rules-2-alpha1` and `bytefray-rules-2-alpha11`, making the Phase 0
  registry total eight.
- Scope C's early 830-test estimate was superseded after Scopes A/B by **393 of
  3,440** affected outcomes across 52 files.
- The claim that all of `supervised_runtime.py` would become dead was false;
  Ruleset 4 consumes its diagnostic helpers. It shrank to 89 LOC rather than
  disappearing.
- vulnerable-core helpers remain reader-required, while observable-core live
  execution helpers could retire; the two tables were not equivalent.
- `api_version` is part of deterministic seed material and remains despite
  being single-valued.
- default `bytefray run` used VM `writer`/`runner` and had to be repointed
  before VM removal.
- evaluation preset legal values had drifted from the CLI and would have had
  no legal value after registry narrowing; they were corrected to stable v4.
- the projected Scope-C test range was not a target. Exact selected delta was
  3,440 -> 2,929 (-511), after restoring current/reader coverage that the
  in-progress migration had removed.

## W. Gemini/Codex forensic qualification episode

Claude began the 2B.12 implementation. Gemini continued when Claude usage was
exhausted and made useful conversions, but it also weakened or deleted current
coverage and left runtime boundaries incomplete. Its qualification evidence was
discarded.

Independent Codex review found invalid historical/current hybrids, malformed
fixtures, self-referential assertions, reset tests that no longer reached
`reset()`, current Ruleset-4 artifacts mislabeled as legacy, wrongly deleted
current tests, and incomplete API-v1/VM boundaries. Codex restored or
consolidated reader/current coverage, added permanent boundaries, corrected
packaging, and reran the 2B.12 gates serially. One Codex policy detour—restoring
retired Ruleset-2 corpora and five pinned API-v1 starters—was reversed after
the user clarified their intended retirement.

This episode should not be sensationalized. Its practical lesson is:

> **Large compatibility-retirement phases require independent review of
> changed tests, not merely a green suite.**

This final phase adds a second lesson: qualification must cross the commit
boundary when fixtures carry byte digests. A green dirty-tree run cannot prove
that Git normalization preserves an artifact's recorded hash.

## X. What Phase 2 deliberately did not change

Phase 2 did not redesign Ruleset-4 gameplay, scoring, placement, scheduling,
process disruption, action semantics, seed derivation, result/replay identity,
or schemas. It did not create Ruleset 6, begin Phase 3 decomposition, introduce
new persistence, rewrite `_legacy`, remove historical readers, or normalize
archived terminology. It did not preserve retired executors merely to regenerate
old evidence; Git history and releases serve that purpose.

## Y. Remaining technical debt

### INITIAL BLOCKER — CLOSED BY THE REMEDIATION IN SECTION AC

The schema-6 frozen group fixture had a replay digest for CRLF bytes but was
committed with enforced LF bytes. The initial qualification required the
following separate explicit task; section AC records its completion in the
current working tree:

1. choose and document the canonical byte representation (the repository's
   existing `eol=lf` policy strongly favors the committed LF replay);
2. correct the fixture metadata without changing gameplay events, entrant
   order, match identity, or semantic golden values;
3. rerun the focused four group-fixture verification cases;
4. rerun Gates A-D, exactly one canonical suite, GUI, ruff, both mypy scopes,
   and package-content inspection serially on the new committed tree; and
5. update this report with actual results and a qualified verdict only then.

### PHASE 3 INPUT

- `agent_evaluation.py` remains 5,258 LOC and still combines current execution
  with historical adapters/readers.
- `match_service.py` is 1,126 LOC after three dispatch arms collapsed to one;
  its remaining abstractions should be traced for inert generality, not removed
  speculatively.
- retained shared/history utilities may not live near their actual consumers.
- Ruleset-policy abstractions must be separated into those useful for a future
  Ruleset 6 and those retained solely for history.
- current documentation still contains the `pygame_canvas.py`, old environment
  fallback, and v3-branch-topology inaccuracies recorded above.

### FUTURE PRODUCT WORK

No new product feature, gameplay mechanic, installer lifecycle, or GUI redesign
is required by this phase. Such work remains outside Phase 3 unless separately
justified.

## Z. Phase 3 context-locality handoff

This handoff was blocked during the initial qualification. Closing that blocker
in the current working tree makes the handoff eligible for separate review and
authorization; it neither authorizes nor implements Phase 3.

- **`agent_evaluation.py` (5,258 LOC):** identify the seam between the sole
  current Ruleset-4 evaluation executor and historical v1/v2/group adapters.
- **`match_service.py` (1,126 LOC):** trace branches/generalizations left inert
  after VM, API-v1, and process dispatch became one process path.
- **Runtime modules:** `process_runtime.py` 1,367 LOC; `python_runtime.py` 545;
  `supervised_runtime.py` 89; `vm.py` 77. Ask whether retained diagnostics,
  historical predicates, and arena storage are located near their consumers.
- **Ruleset policy (707 LOC):** preserve future versioned-policy seams while
  distinguishing them from historical recognition tables.
- **Worker protocol:** retain `api_version` until an explicit new seed/protocol
  version permits removal; single-valued does not mean behaviorally inert.

The planned Git-history locality study remains Phase 3: Replay History, Agent
Params, Ruleset defaults, Tournament, Evaluation, Designer export, and one
gameplay mechanic should be traced to answer whether Bytefray is large because
it does many things or because each concept requires too much unrelated context
to change safely.

## AA. Initial repository integrity

At the end of the initial qualification this report was the only working-tree
change. No runtime, test, fixture, roadmap, or packaging file had been modified,
and no commit, push, merge, rebase, tag, upload, installer lifecycle, or
publication had been performed.

The initial qualification's three exact pytest temp roots were validated as
children of the repository and removed. Its final checks found zero
Python/pytest processes, zero `.pytest-tmp*` roots, an empty tracked
`git diff --stat`, a clean `git diff --check`, and exactly one porcelain entry:
this untracked report. `main` remained at `82549f9c...`, and `v6-research`
remained at committed candidate `3caf143e...`, identical to
`origin/v6-research` and 22 commits ahead of `main`.

## AB. Initial Phase 2 closure verdict

### NOT QUALIFIED

The active architecture reached the intended Phase 2 shape and the Ruleset-4
control plus retirement boundary passed. Nevertheless, the committed tree is
not qualified because one required historical fixture fails its authoritative
digest and three historical-reader tests fail as a consequence. Later workflow,
canonical, GUI, static, and package gates were correctly not run after the
blocker.

Phase 2 may be closed only after a separate, reviewable fixture-integrity
remediation is committed and the complete final gate sequence passes on that
exact commit. Phase 3 is not authorized by this report.

## AC. Fixture-integrity remediation and post-remediation qualification

### Root cause and provenance

The blocker was reproduced again before editing from the Git object itself,
not merely from a possibly transformed working-tree file:

| Form | Bytes | SHA-256 |
| --- | ---: | --- |
| Raw `HEAD` replay bytes | 165,919 | `2fbf7c04432467a8ab5b0204871189f8bca98f8a82978b730b6a4837844e6a56` |
| Raw working-tree replay bytes | 165,919 | `2fbf7c04432467a8ab5b0204871189f8bca98f8a82978b730b6a4837844e6a56` |
| In-memory LF -> CRLF transform (101 line endings) | 166,020 | `e9cb516d58de5233d067d4eba94951a75f917b7101648601f32d92b9b95e5504` |
| Initially recorded digest | — | `e9cb516d58de5233d067d4eba94951a75f917b7101648601f32d92b9b95e5504` |

The evidence supports one sequence and no competing byte-level explanation:

1. the retired Ruleset-2 group artifact was copied from the real Beta3 corpus
   into the Phase 2B.12 working tree on Windows;
2. `result.json` recorded the digest of that CRLF working-tree replay;
3. commit `3caf143e` added the replay and result together;
4. the repository's pre-existing `* text=auto eol=lf` policy normalized the
   replay to LF in Git; and
5. the metadata digest was not recomputed from the committed bytes.

This is supported by the exact transformed digest match, the fixture and
metadata sharing the same introducing commit, `.gitattributes` having enforced
LF since commit `b20f52cf`, the pre-commit Scope-C reader gate having passed
while these files were still untracked, and the post-commit gate failing only
after it encountered the LF-normalized replay. The retired fixture has no
maintained generator; its test helper only copies the committed files.

### Repository-wide sibling audit

Every committed fixture metadata field that purports to hash another committed
text fixture was classified. Agent `source_sha256` values were also inspected
but are not entries in this table: they identify historical agent source and
do not describe sibling fixture files.

| Fixture | Recorded digest | Raw-byte digest | CRLF/LF transformed match? | Status |
| --- | --- | --- | --- | --- |
| `v6_scope_c_group_evaluation/.../result.json` -> `replay.jsonl` | `e9cb516d58de5233d067d4eba94951a75f917b7101648601f32d92b9b95e5504` | `2fbf7c04432467a8ab5b0204871189f8bca98f8a82978b730b6a4837844e6a56` | Yes; CRLF transform matches recorded | **NEWLINE-MISMATCH** |
| `perspective_card_knowledge/alpha1_executioner_vs_sleeper_trace.jsonl` -> replay | `ed92659703957efaed66e4b1435f3184494445121443072ecd9af2536545111b` | `ed92659703957efaed66e4b1435f3184494445121443072ecd9af2536545111b` | No; CRLF transform is `fd49848f2aa57e19d7ddfb7e8f300ad00517b191777b795d80720c9698b41de8` | **VALID** |
| `result/battle2_result_v1.json` -> `replay.jsonl` | `cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc` | n/a; no companion replay exists | n/a; intentional schema/parser placeholder | **NOT APPLICABLE** |

The audit found one newline mismatch, one valid cross-file digest, and one
intentional placeholder. It found zero sibling newline mismatches and zero
other unexplained mismatches. This was one bad fixture metadata record, not a
systemic repository capture defect.

### Remediation

The committed LF replay remains the canonical artifact and is byte-for-byte
unchanged. The only fixture edit changes `result.json`'s replay digest from the
stale CRLF-derived value to
`2fbf7c04432467a8ab5b0204871189f8bca98f8a82978b730b6a4837844e6a56`.
No event, outcome, winner, tick, Ruleset ID, entrant identity, core data, or
evaluation semantic changed.

`engine/tests/test_evaluation_history_verification.py` now reads the committed
fixture as raw bytes, asserts its SHA-256 equals the digest read from the paired
`result.json`, asserts the repository fixture contains no CRLF line endings,
and proves an in-memory CRLF transform does not match. This protects the rule
that integrity metadata hashes exact repository bytes rather than host-native
text representations. There is no maintained generator to modify, so the guard
is intentionally colocated with the frozen fixture's real reader tests.

No derived identifier changed. `match_id` hashes execution inputs;
`result_id` hashes `match_id` plus the outcome and entrant records; and
`replay_id` is the match identity. The replay digest is a separate exact-byte
reference added only after replay publication. The fixture's `match_id`,
`result_id`, `replay_id`, evaluation ID, schedule ID, and artifact path remain
unchanged.

### Post-remediation qualification

All pytest gates ran serially. Test temp roots were removed between the targeted
sequence, canonical run, GUI run, and packaging-boundary check.

| Gate | Fresh result |
| --- | ---: |
| Five-case fixture boundary (four prior cases plus raw-byte regression) | 5 passed |
| Historical readers, same module set as initial Gate C | 636 passed, 2 skipped in 26.52 s |
| Stable Ruleset-4 frozen control, exact eight-module set | 152 passed in 8.29 s |
| Scope-C retirement boundary, same module set as initial Gate B | 391 passed, 2 skipped in 46.54 s |
| Final canonical suite | **2,912 passed, 18 skipped, 3 deselected in 254.20 s** |
| Full offscreen root/client GUI selection | 499 passed, 510 deselected in 140.31 s |
| Ruff | `All checks passed!` |
| Engine mypy | success, 90 source files |
| Client mypy | success, 16 source files |
| Focused packaging/frozen-resource boundary | 105 passed, 5 skipped in 0.56 s |

The canonical run discovered 2,933 cases. Three GUI-marked client cases were
deselected by the established default marker, leaving 2,930 selected:
2,912 passed and 18 skipped. There were zero failures and zero errors. The
one-case increase over the initial candidate is exactly the new raw-byte
regression.

The offscreen result is Qt behavioral evidence; it is not a claim of native
visual, UI Automation, or Narrator qualification.

### Packaging disposition

No distributable input changed. Both tracked remediation files are beneath
`engine/tests`; setuptools package discovery is limited to `engine/src`,
`client/src`, and `app`, and `MANIFEST.in` explicitly excludes test suites from
the source distribution. The untracked report is also not a package input.

Accordingly, no wheel, sdist, PyInstaller payload, or installer was rebuilt.
The prior Phase 2B.12 package qualification remains applicable because the
runtime/package input set is byte-identical. The freshly rerun focused
packaging boundary confirms the policy still requires the ten current API-v2
starters and two current scaffold templates while rejecting retired executor
modules, API-v1 resources, benchmark corpora, and bytecode/cache residue. This
is inherited artifact qualification plus fresh boundary verification, not a
claim that a fresh build was performed.

### Final remediation integrity

The intended working-tree changes are limited to:

- the historical group fixture's replay digest metadata;
- the raw-byte regression in its reader test; and
- this final qualification report.

No runtime, gameplay, package configuration, schema, `.gitattributes`, or
replay content changed. No commit, push, merge, rebase, tag, upload, build,
installer lifecycle, or publication was performed. Final process, temp-root,
status, diff, ref, and divergence checks were run after this report update.

## AD. Final closure verdict

### QUALIFIED

The original committed candidate remains historically **NOT QUALIFIED** for
the exact digest defect recorded in sections A, F, Y, and AB. The narrow
remediated working tree is separately **QUALIFIED**: exact committed-byte
provenance is restored, the defect class is isolated and permanently guarded,
historical-reader integrity remains strict, frozen Ruleset-4 behavior and the
Scope-C retirement boundary remain unchanged, and every required fresh gate is
green.

This verdict authorizes review of the remediation; it does not imply a commit,
push, release, tag, upload, or start of Phase 3 was performed.
