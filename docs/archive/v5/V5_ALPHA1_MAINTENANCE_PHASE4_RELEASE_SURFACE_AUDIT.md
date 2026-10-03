# Bytefray V5 Alpha 1 Maintenance — Phase 4: Release Surface & Historical Compatibility Audit

Date: 2026-09-11. **Audit complete; documentation changes only.**
**Elevated installer lifecycle remains OPEN. No publication performed.**

This report records current source behavior separately from recommendations.
No proposed selection, ordering, compatibility, or removal change is implemented.
The eight registered execution identities must all remain available at this
phase boundary. No runtime ruleset qualifies for removal.

## A. Starting state

| Item | Observed value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD | `ce23af74b2f52099792570700b7b9ed8a2c5ae69` |
| Upstream | `origin/v5-research` |
| Ahead / behind | `0 / 0`, from `git rev-list --left-right --count HEAD...@{upstream}`; local tracking ref, no fetch performed |
| Working tree | Clean: `git status --short` empty; nothing staged |
| Product version | `5.0.0a1`, `pyproject.toml` |
| Phase 3 relationship | Already committed as HEAD itself, `chore(v5): harden starter refresh and installer hygiene`; includes its report, starter recovery implementation/tests, and installer/smoke changes |
| Published Alpha 1 | Local annotated `b5.0.0-alpha1` peels to `28a10b8f8fd47bf32ec9281dcc21b0645276962c`, not this maintenance HEAD |

Read the Phase 0 baseline, Phase 1 documentation cleanup, Phase 2 technical
hygiene, and Phase 3 installer qualification reports before editing. Their
measurements are prior-phase evidence, not fresh Phase 4 qualification.
Unrelated local files, ignored agents/artifacts, and `.claude/settings.local.json`
were left untouched. No prior uncommitted Phase 3 work needed separation.

## B. Product/ruleset architecture

Product **5.0.0a1**, gameplay **Ruleset 4**, programming **Agent API v2**,
and replay **schema 4** identify different contracts. V5 Alpha 1 adds authoring,
starter, parameter, and Designer capabilities on permanent V4 gameplay; it does
not introduce a production `bytefray-rules-5`.

`rules.py` owns identity/provenance. `ruleset_policy.py` owns the explicit
eight-entry `_RULESET_POLICIES` execution registry, runtime/API restrictions,
placement and scheduling policies, and omitted-selection candidates.
`NativeMatchService.run` validates composition and policy before dispatching
VM, single-actor Python, or process Python execution. Agent discovery names
and product version do not choose gameplay.

Permanent V4 and alpha2 share seeded core placement, round-robin intra-entrant
process selection, and the same process gameplay. They remain distinct
dispatch, hash, and persisted identities. Alpha1 instead retains seat-spread
placement and priority process selection. All three use API v2 and schema 4.
The permanent promotion is documented in
[V4 RC Phase 2](../v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md), with
`engine/tests/test_v4_stable_ruleset_equivalence.py` as the live equivalence gate.

## C. Complete ruleset inventory

Implementation symbols below are in `engine/src/battle_engine/ruleset_policy.py`.
“Replay” refers to preservation of attribution/interpretation, **not** a claim
that playback executes the policy. See F for the narrower playback requirement.

| Ruleset ID | Implementation / actual runtime | Status and current purpose | User selectable now? | Replay requirement | Live test dependence |
|---|---|---|---|---|---|
| `bytefray-rules-1` | `RULESET_V1`; Kernel/VM or API-v1 `PythonEntrantController` | Frozen historical stable gameplay; sole public VM/blob option, historical Python/evaluation | CLI; Advanced/Development/pairwise Evaluation | Explicit identity and schema-3 missing-ID recovery; legacy adapters | `test_ruleset_v1_equivalence.py`, `test_ruleset_persistence.py`, replay tests |
| `bytefray-rules-2-alpha1` | `RULESET_V2_ALPHA1`; historical Python vulnerable core; VM dispatch is inert with respect to cores | Historical experimental gameplay retained for reproduction | No ordinary CLI/GUI; programmatic execution | Core-family interpretation and original attribution | `test_ruleset_v2_alpha1.py`, `test_replay_status.py`, reference tests |
| `bytefray-rules-2-alpha11` | `RULESET_V2_ALPHA11`; Python adds observable core beacon; historical VM dispatch retained | Historical experimental gameplay, promotion control | No ordinary CLI/GUI; programmatic execution | Core-family interpretation and distinct alpha11 attribution | `test_ruleset_v2_alpha11.py`, `test_ruleset_v2_promotion_equivalence.py`, replay-status tests |
| `bytefray-rules-2` | `RULESET_V2`; API-v1 Python only, seat-spread placement | Permanent single-actor gameplay; current supported API-v1 default and Group evaluation | All four ordinary CLI selectors; all Designer match/test/pairwise selectors; fixed in Group | Original identity and vulnerable/observable-core interpretation | `test_ruleset_v2.py`, promotion/runtime compatibility, Group and benchmark tests |
| `bytefray-rules-3-alpha1` | `RULESET_V3_ALPHA1`; API-v1 Python with bounded-locality runtime gates | Research-only locality hypothesis; no permanent Ruleset 3 | No ordinary CLI/GUI; programmatic research evaluation/execution | Original identity and locality/core recorded state | `test_v3_phase2_locality_runtime.py`, locality agents/evaluation tests |
| `bytefray-rules-4-alpha1` | `RULESET_V4_ALPHA1`; API-v2 `ProcessMatchController`, seat-spread/priority | Frozen historical public alpha; replay, agent and evaluation reproduction | CLI; Advanced/Development/pairwise Evaluation | Original schema-4 process data and identity; recognized by historical core-status helper | `test_ruleset_agent_compatibility.py`, `test_v4_alpha2_integration.py`, process/replay tests |
| `bytefray-rules-4-alpha2` | `RULESET_V4_ALPHA2`; API-v2 process runtime, seeded/round-robin | Frozen historical public alpha; stable-promotion control | CLI; Advanced/Development/pairwise Evaluation | Distinct original identity, schema-4 process data | `test_v4_alpha2_placement.py`, `test_v4_alpha2_scheduler.py`, stable equivalence |
| `bytefray-rules-4` | `RULESET_V4`; API-v2 process runtime, seeded/round-robin | Current permanent process gameplay; V5 ordinary API-v2 default | CLI; all Designer match/test/pairwise selectors | Original identity, schema-4 process data | Stable equivalence, V5 starter/parameter, runtime-default tests |

The old v2 alpha policies intentionally have no API-version restriction in
their policy objects; this does not make them API-v2 execution routes.
They dispatch through historical runtimes, not `PROCESS_RULESET_IDS`. Do not
promote their permissive predicate into a new supported product combination.

Other strings found by the tracked-source/data/test census:

| String(s) | Actual status |
|---|---|
| `evaluation-rules-1` | Persisted historical attribution alias normalized to v1 by `rules.normalize_ruleset_id`; not an executable registry key. Keep alias handling and provenance tests. |
| `bytefray-rules-5-r1-alpha1`, `bytefray-rules-5-r2-alpha1` | Rejected experiments absent from production registry. Retained runner literals explicitly require historical commits `18e5ac6` / `26e0816`; Phase B negative tests assert rejection. Historical evidence, not available product choices. |
| `bytefray-rules-3`, `bytefray-rules-5`, `bytefray-rules-99`, `bytefray-rules-2-alpha2`, `-alpha12`, `-alpha1x`, hypothetical/invalid IDs | Documentation explanations or negative-test inputs, not additional implementations. No permanent Ruleset 3 or 5 exists. |

## D. Recommended compatibility classes

Classes describe proposed product positioning; they do not change current access.

| Ruleset | Class | Reason |
|---|---|---|
| Permanent v4 | **A — Current selectable** | Ordinary API-v2/V5 authoring and matches |
| Permanent v2 | **A — Current selectable, API-v1 lane** | Still the supported default for seven shipped Python starters and the only Group evaluation ruleset; age alone does not make it compatibility-only |
| v1 | **B — Legacy selectable** | Required for new VM/blob matches and intentional historical Python runs |
| v4 alpha2 | **B — Legacy selectable** | Explicit historical reproduction is a documented public capability and live equivalence control |
| v4 alpha1 | **B — Legacy selectable** | Behaviorally distinct frozen contract with reference agents and historical evaluation |
| v2 alpha1 | **C — Compatibility-loadable only in the ordinary product** | Preserve historical execution as well as playback; already excluded from ordinary selectors |
| v2 alpha11 | **C — Compatibility-loadable only in the ordinary product** | Preserve promotion/replay/reference reproduction; already excluded from ordinary selectors |
| v3 alpha1 | **D — Internal/test/research only** | Live locality program and packaged benchmark evidence; retain programmatic access |

**E — Removable candidate: none.** The C designation limits encouragement of
new ordinary matches; it is not permission to delete the original simulator.
Rejected V5 identities are already absent, so are not new removal candidates.

## E. User-visible surface matrix

Abbreviations: S = Simple, A = Advanced, D = Development, E = pairwise
Evaluation, G = Group evaluation. All rows preserve their recorded replay IDs.

| Ruleset | CLI run/tournament/test/evaluate | Designer | Replay load | Agent metadata | Docs/tests | Packaging |
|---|---|---|---|---|---|---|
| v1 | All; test/evaluate are Python-only workflows | A/D/E; sole VM match option in A | Yes; also recovered for absent schema-3 ID | API v1 Python or VM/blob, no manifest ruleset pin | Rules/compatibility, frozen tests | Engine + four VM starters and seven API-v1 starters |
| v2 alpha1 | Not ordinary parser choices | None | Yes | Historical API-v1 reference intent in prose | V2 archive/reference/replay tests | Policy in engine; references in wheel/sdist data |
| v2 alpha11 | Not ordinary parser choices | None | Yes | Same API-v1 family, distinct artifact identity | V2 promotion/equivalence evidence | Same package-data boundary |
| v2 | All | S/A/D/E; G requires it | Yes | API v1; still automatic for that roster | Current API-v1 and Group guides/tests | Seven Python starters plus research benchmark resources |
| v3 alpha1 | Not ordinary parser choices; programmatic evaluation accepts it | None | Yes | API-v1 locality research manifests; intent stronger than metadata predicate | V3 archive/locality tests | Locality agents/benchmarks in wheel/sdist data |
| v4 alpha1 | All | A/D/E | Yes | API v2; no special manifest pin | Frozen design, API/replay tests | Process engine and compatible starters |
| v4 alpha2 | All | A/D/E | Yes | API v2; no special manifest pin | Frozen design, stable equivalence | Same |
| v4 | All | S/A/D/E | Yes | API v2; V4/V5 prefixes do not restrict policy | Current V5/API-v2/rules guide, equivalence | Ten API-v2 starters |

### CLI choices, defaults, validation, and output

`cli.py`, `tournament_cli.py`, `agent_test._parser`, and
`agent_evaluation._parser` all list **v1, v2, v4-alpha1, v4-alpha2, v4**
in that order. Parser default is `None`; it is not “pick the first choice.”
`resolve_omitted_ruleset_for_agents` walks **v2, v4, v1** and selects the first
policy compatible with the entire roster. Consequently API-v1 Python gets
v2, API-v2 Python gets v4, and VM/blob gets v1. An empty resolver roster
falls back to v1; library request defaults are separate compatibility surfaces.
An explicit ID is preserved by this resolver and validated downstream.

Unknown/non-choice IDs fail argparse. Incompatible rosters fail before gameplay
with `ruleset_resolution_failed`, `ruleset_agent_unsupported`,
`ruleset_runtime_unsupported`, or composition diagnostics as applicable.
`run` help mentions a mixed Python/VM v1 resolution, but this describes only
resolution: `NativeMatchService` still rejects mixed execution. Explicit
selection cannot bypass that boundary. `--pygame` remains retained unchanged.

Direct-run diagnostics and JSON output include `ruleset_id`; canonical
result/replay metadata carry the resolved ID. `agents test` prints the
ruleset and retains it in development outcome/summary data. Evaluation prints
`ruleset:` and stores `rules_compatibility_id` in its identity-bearing recipe
and cells. Tournament scheduling threads its requested/resolved identity to
each match; integrity checks compare result and replay IDs. Existing metadata
must not be rewritten merely to show a newer product label.

**Additional restriction:** evaluation preset schema validation in
`evaluation_presets._VALID_RULESETS` accepts only v1/v2. It does not match
the five CLI choices, despite a stale source comment claiming it does.
A V4 preset fails on load before an explicit CLI override can replace its
ruleset. A preset omitting `ruleset` can use API-v2 roster resolution, subject
to V4 methodology constraints such as arena 512. Agent parameter presets are
a different feature and do not select gameplay rulesets.

### Designer population, order, labels, synchronization

`app/services/ruleset_options.py` defines:

- Simple: **v2, v4**.
- Advanced, Development, pairwise Evaluation: **v2, v4, v4-alpha2,
  v4-alpha1, v1**.
- Group: fixed `bytefray-rules-2 (required for group evaluation)`.
- Tools → Run Tournament: no ruleset selector; command builder omits
  `--ruleset` and delegates to tournament CLI roster resolution.

Fresh combo population starts at v2. Simple/Advanced are **ruleset first**:
they filter the agent list to the chosen policy, retain compatible selections,
and disable execution when no compatible agents exist. Their initial v2 choice
therefore exposes API-v1 starters, not the V5 process roster. Advanced additionally
prevents mixed runtime-kind selections through `agent_combo`/launch guards.

Development/pairwise Evaluation are **agent first**: the full catalog remains
available; `sync_ruleset_choices_for_metadata` disables incompatible ruleset
items, preserves a still-compatible selection (including an explicit alpha),
and repairs an incompatible selection to the first compatible offered option.
An API-v2 roster reaches permanent v4 when selection repair is needed. No
compatible choice disables Test/Run; Development explains that API generations
cannot compete together. Pairwise synchronization also considers baseline and
selected opponents. Evaluation presets can select an available preset ruleset.
Launch builders retain engine-backed metadata checks; the live synchronization
function was neither refactored nor renamed.

Labels already distinguish v4 “Current / Recommended (Agent API v2)” from
both “Process-agent preview, historical” alphas and v1 “Compatibility (Python
and VM/blob).” However v2 is also “Current / Recommended” without its API-v1
qualification, and the shared tooltip begins “Ruleset v2 is Bytefray's current
gameplay ruleset.” This is ambiguous V5 onboarding language, not evidence that
the alpha identities are accidentally registered. Labels/order remain unchanged.

### Documentation, examples, and packaging boundary

Reviewed README Quick Start/compatibility, authoring and Agent Lab guides,
V5 starter guide, Rules v1/v2/v4, API/schema references, ROADMAP/FUTURE_PLANS,
PROJECT_HISTORY, archive index, and relevant specs/research. There is no
root `examples/` directory or standalone current `docs/INDEX.md`/`docs/README.md`:
current navigation is README and topic guides; examples are inline, package
templates/starters, and retained historical material. `engine/config/battle.defaults.json`
does not add a new ruleset identity. No current guide was found asserting an
implemented production Ruleset 5; R1/R2 mentions describe historical experiments.

`pyproject.toml` includes `battle_engine/data/**/*`, so wheels/sdists include
research/reference agents and benchmark JSON alongside the 21 user starters
and four API/template combinations. Bundling a resource does not make it
discoverable in the user catalog. Repo-root `agents/` fixtures are excluded
from the wheel; only five agent directories there are Git-tracked.
Frozen specs explicitly collect starters/templates for the relevant launchers;
the existing Phase-3 unified `_internal/battle_engine/data` tree contains
only `agent_template`, `agent_template_annotated`, `agent_template_v2`,
`agent_template_v2_annotated`, and `starter_agents`. Do not claim its research
resource inventory equals the wheel. This directory inspection is not a new
build qualification. Top-level research docs are not an installed user manual;
README supplies package description, while package-local README assets (for
example Quorum) can ship. `MANIFEST.in` also prunes root tests from sdist.

## F. Replay compatibility requirements

`battle_engine.replay.deserialize_record` accepts a string or null ruleset ID;
it checks supported schema (2/3/4) and record shape, not registry membership.
The legacy v0.1 adapter remains. `ReplaySession.load/seek` reconstructs arena,
ownership, entrants and processes from snapshots/diffs; `ReplayPlayer` consumes
records. Neither re-runs agents, scheduling, placement, or scoring.

`resolve_replay_ruleset` returns an explicit ID verbatim with `recorded`
confidence. Absent ID with schema **3 only** recovers v1; absent ID with schema
2 or 4 remains unknown. The viewer's `resolve_match_ruleset_label` shows that
value/confidence. An unavailable ID is still displayed verbatim and does not
itself block loading a supported, well-formed replay. Unknown schemas and
malformed records still fail; unknown identity acceptance is not universal
future-format compatibility.

Interpretation has additional dependencies: `replay_status._core_status`
uses `python_runtime.has_vulnerable_core`, `core_addresses`, and `CORE_SIZE`.
Its historical family includes v2 alphas, v2, v3 alpha1 and v4 alpha1; it
returns no core status for v1, unknown IDs, **v4 alpha2 or permanent v4**.
This last asymmetry was confirmed with equal synthetic stored-state inputs,
not inferred from names. The newer `pygame_renderer.replay_core_addresses`
derives cores directly from tick-zero diffs for capture presentation, so this
is not evidence that stable-V4 playback or every capture visual is broken.
It is a narrower status/HUD coverage issue for follow-up; no fix here.

Evidence includes five tracked early replay JSON fixtures under
`engine/tests/fixtures/replay/` (legacy event, v0.1 header/snapshot, v0.2
header/tick), generated V1/V2 replay
reconstruction/persistence tests, real v2-alpha1/alpha11/v2 matches in
`client/tests/test_replay_status.py`, schema-4 alpha1 process reconstruction
in `client/tests/test_replay_session.py`, and generated alpha2/stable replays
in `test_v4_stable_ruleset_equivalence.py`. The tracked replay-file census
found five early JSON files, not a checked-in full V4 JSONL corpus; later
compatibility evidence is generated by tests. Local ignored replays were not
treated as a versioned fixture inventory.

Phase 4's isolated probe loaded all eight registered IDs plus one unregistered
ID through the same synthetic schema-4 header/tick data, with execution-policy
resolution patched to raise if called. All nine loaded and reconstructed
ownership; three missing-ID provenance probes matched the rules above. These
are reader probes, not nine historically valid gameplay recordings.

**Minimum playback retention:** keep schema/legacy readers, exact recorded
identities and provenance, stored-state reconstruction, and the shared
interpretation helpers/import dependencies. Full original scheduling is not
required merely to play recorded diffs. **Minimum overall compatibility
retention today is stronger:** keep all eight executable policies and their
runtime semantics for replay regeneration, old-agent execution, frozen tests,
and qualification reproduction. Deleting a module just because playback
does not dispatch its policy can still break imports and status interpretation.

## G. Agent compatibility matrix

Manifest census used `yaml.safe_load` on Git-tracked manifests. None of these
agent manifests has an enforced ruleset pin. `kind` and `api_version`, not
`name`, `display`, product prefix, or prose description, drive policy checks.
Benchmark/evaluation metadata may separately pin a ruleset and source revision.

| Agent/group | API | Intended ruleset(s) | Bundled? | User-facing? | Historical only? | Tests/evidence |
|---|---|---|---|---|---|---|
| `runner`, `writer`, `seeker`, `spiral` | VM, no Python API | v1 | All four starter manifests | Catalog; Advanced VM matches | No, supported native VM lane | Starter/CLI/VM characterization |
| `adaptive`, `claimer`, `hunter`, `raider`, `sentinel`, `strider`, `wanderer` | 1 | Permanent v2; legal historical v1 | Seven Python starters | Catalog, Simple/Advanced, Development/Evaluation | No | `test_default_python_agents.py`, v2 benchmark and Group tests |
| `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_scout` | 2 | Permanent v4 today; both V4 alphas technically compatible | Five Python starters | Catalog/current references | No | V4/V5 regression and controlled research |
| `v4_quorum` | 2 | Permanent v4; both V4 alphas legal | Sixth V4 starter, with README | Explicitly Advanced Example | No | Quorum and V5 control/equivalence research |
| `v5_region_attacker`, `v5_scout_striker`, `v5_core_defender`, `v5_dual_team` | 2 | Permanent v4 intended; both V4 alphas legal | Four current starters, version 1.1.0 manifests | Current educational ladder, parameters/presets | No | `test_v5_starter_agents.py`, parameter/default-equivalence/refresh tests |
| `agents/hydra`, `agents/Nemesis`, `agents/viper` | 2 | Original V4/reference context; hydra/Nemesis pre-alpha2 placement assumptions | Tracked repository fixtures, not wheel starters | Discoverable in this source catalog; not bootstrapped for installed users | Primarily research/qualification | Stable equivalence consumes hydra/Nemesis; `tools/v4_alpha2_ecology_study.py` historical roster includes viper |
| `agents/hydra_alpha2`, `agents/nemesis_alpha2` | 2 | Alpha2-adapted visibility/READ target acquisition; permanent v4 legal | Tracked fixtures, not wheel starters | Source catalog when present | Primarily research/qualification | Stable equivalence and adapted ecology roster |
| `core_defender`, `core_seeker`, `reactive_core_defender`, `core_tracker` | 1 | V2 alpha/core-family research and permanent-v2 benchmarks | Package-local resources in wheel/sdist | Internal resource loader, not starter discovery | Historical/reference, still live | `test_v2_alpha1_reference_agents.py`, `test_reference_agents.py`, pinned v2 benchmark |
| Six `local_*` agents under `data/v3_locality_agents` | 1 plus experimental locality actions | v3 alpha1 intended; API field alone cannot express action compatibility | Wheel/sdist resources | Internal research | Yes | Locality runtime/agents/evaluation and frozen population JSON |
| `core_tracker_offset`, `turtle_core_refresher` | 1 | V2 research controls | Wheel/sdist resources under v3 phase7/closeout trees | Internal research, explicitly disposable controls | Yes | Phase7/closeout tests |
| Four blank/annotated scaffold templates | 1 or 2 | v2/v1 for API1; V4 family for API2 | Wheel/sdist and relevant frozen resources | CLI and New Agent dialog | No | `test_agent_scaffold.py`, frozen packaging tests |
| Internal `reference` opponent | 1 or 2 selected by requested process ruleset | Historical API1 template or API2 `v4_claimer` | Uses those existing resources | Development's Reference option; not a catalog agent | No | `test_agent_test.py`, `test_reference_agents.py` |

Total user starter inventory is **21 = 4 VM + 7 API-v1 Python + 6 V4
API-v2 Python + 4 V5 API-v2 Python**. Other built-in VM programs such as
`bomber`/`flooder` are VM assembly support, not additional entries in that
21-manifest starter count. `_legacy` tooling/Redcode examples and local
blob-only directories are distinct from these tracked Python fixtures.
No agent, manifest, source fingerprint, preset, or reference behavior changed.

## H. Match-selection compatibility

| Combination | Actual behavior | Product implication |
|---|---|---|
| Permanent-V4 or V5-named API2 agents + either V4 alpha | Legal; same API, distinct policy identity | Potentially surprising. Alpha1 changes gameplay; alpha2 shares permanent gameplay but hashes/metadata remain distinct. Names do not pin rulesets. |
| API1 Python + permanent V4 or either V4 alpha | Invalid, `ruleset_agent_unsupported`; Designer disables/excludes | Do not relabel an old agent as API2 without implementing that contract |
| V5 starter + v1/v2 | Invalid, API mismatch | “V5” describes source/teaching generation, not backward compatibility with every ruleset |
| API1 + API2 entrants | Invalid in ordinary matches; omitted selection fails | Designer Development/pairwise disables execution; CLI gives structured rejection |
| VM/blob + v2/V4 family | Invalid, runtime restriction | Advanced provides v1 for native VM |
| API1 Python + VM under v1 | Per-agent policy permits each separately; whole match still invalid | Shared ruleset support does not imply mixed-runtime match support; GUI homogeneous guard and match service reject it |
| Two historical API1 Python agents + v1 or v2 | Legal | Same source, different mortality/core mechanics and artifact identity |
| Historical fixed-placement hydra/Nemesis under seeded V4 | API-legal; strategy assumptions may fail | Strategic suitability is not loader compatibility; retain originals and adapted controls |
| V4/API2 pairwise Evaluation | Legal under v4/alpha2 seeded methodology or alpha1's retained methodology | Group is not equivalent to arbitrary multi-entrant engine capability |
| V4/API2 Group Evaluation | Rejected; Group requires v2 | Separate future methodology/product decision |
| Locality research API1 agent under v1/v2 | Metadata may pass; experimental actions do not thereby gain meaning | Internal research intent must remain documented; not a supported user recommendation |

`agents test` and `agents evaluate` accept Python entrants only even though
their v1 policy also supports VM elsewhere. Designer Tournament's homogeneous
kind validation is narrower than API-version validation; mixed Python API
generations can reach the CLI's rejection rather than receiving Development's
early disabled-button behavior. This is a UX mismatch, not a validation bypass.

## I. Development/Evaluation audit

Implemented terminology names **Development test**, **Pairwise evaluation**,
and **Group evaluation** controls. No separate Development or Evaluation
`RulesetPolicy` exists. `evaluation-rules-1` is the historical attribution
alias in C, not a new evaluation game. V5 R4 research's development/evaluation
split concerns disjoint seed sets and freezing agents before held-out tests;
it does not create a second gameplay ruleset.

Evaluation does have a distinct, recorded **methodology**:
permanent V4 and alpha2 use `ruleset_v4_seeded_placements`, arena **512**,
eight deterministic placement samples by default, and paired orientations
using the same seat geometry. Alpha1 retains the older fixed-placement
evaluation path. Group remains permanent-v2-only. Methodology versions and
ruleset identity must remain separate in presentation and artifact comparison.
See [V4 evaluation qualification](../v4/V4_RC1_PHASE1_EVALUATION_METHODOLOGY.md)
and `docs/specs/agent_evaluation.md`.

The present ordering is intentional in code comments and tests, but favors
API-v1 onboarding: both permanent choices are marked recommended, with v2
first. CLI lists chronology, while GUI lists preference. Alphas are already
marked historical, yet intermix with normal choices in the longer menus.
A user can deliberately choose an old alpha; the UI communicates history but
could explain intended reproduction use better. “Evaluation ruleset” should
continue to mean the ruleset used by that evaluation, never an invented
alternative to permanent Ruleset 4.

## J. Alpha-era terminology findings

| Occurrence | Classification | Disposition |
|---|---|---|
| README Ruleset1 = “VM / pMARS Redcode” | Incorrect current-product description | Corrected: native VM/API1 Python; pMARS is separate |
| Authoring guide implies scaffold creates only API1 | Stale current-product capability statement | Corrected: both API versions supported, default remains API1 |
| V5 starter guide `bytefray agents list` | Incorrect current command | Corrected to `bytefray agents` |
| Compatibility reference opens with future 1.0 candidate framing | Historical inventory presented without current boundary | Added current V5 overview and historical scope note; retained section anchor and contract content |
| Designer v2 “Current / Recommended” and shared tooltip | Ambiguous current UI label | Documented only; qualify API1 in a later UX decision |
| V4 alpha “Process-agent preview, historical” | Accurate historical identity, potentially dated “preview” wording | Keep now; consider “Historical reproduction” wording later |
| API-v1 templates, V4-prefixed starters, alpha reference displays | Required compatibility or accurate strategic lineage | Retain; age is not proof of obsolescence |
| Registry docstring says “Exactly one Ruleset”; evaluation guard comments say two choices/no alpha; older architecture starter-copy prose | Stale explanatory source/developer text | Record for scoped follow-up; no executable files or broad architecture rewrite in this phase |
| ROADMAP/FUTURE_PLANS, V4 qualification, V5 R1/R2 reports | Historical planning/evidence with scope framing | Retain original experiments, chronology and results |
| `bytefray-rules-*`, `battle2.*`, API identifiers | Stable runtime/protocol identity | Retain exactly |

## K. CHANGELOG.md

Added the missing **`[5.0.0a1] - 2026-09-10`** entry above 4.0.0, using the
UTC publication date from the committed Phase F publication addendum. Local
tag peeling confirmed its exact source SHA. This was a repository-history
audit, not a fresh remote release or asset verification.

The source range `git log --oneline v4.0.0..b5.0.0-alpha1` contains
`69fc958` (four starters), `3095b3d` (parameter schemas/authoring), `0dde69c`
(Designer parameter workflow, Randomize Seed, starter refresh, results
parameter display), `45ccc34` (API2 templates), `c280798` (frozen bytecode
exclusion), and `bfc8097` (qualification portability fixes). Phase C/D/E
reports and Phase F's publication inventory corroborate those shipped claims.

No new spectator suite or new evaluation methodology is claimed for Alpha 1:
those were V4 features. Phase E's replay-related shipped polish is effective
parameters in the **Designer results view**, not Replay History. The entry
does not promote R1/R2 experiments into release features. It explicitly
excludes post-release parameter-consistency remediation, core-capture
presentation changes, and maintenance Phases 0–4. The original seven-asset
inventory contains no frozen Linux archive. Nothing was rebuilt or published.

## L. Current documentation corrections

| File | Low-risk correction |
|---|---|
| `README.md` | Explicit V5/permanent-V4 relationship, still-supported v2 default, actual historical selectability, separate pMARS backend, Designer/Group scope |
| `docs/AGENT_AUTHORING.md` | API2 scaffold command and API1 default explicitly distinguished; removed false API1-only capability statement; replaced stale README matchup anchor with current Agent Lab evaluation guidance |
| `docs/V5_STARTER_AGENTS.md` | Correct catalog command |
| `docs/COMPATIBILITY.md` | Current V5 boundary and workflow/default summary before retained historical contract inventory; link to this audit |
| `docs/AGENT_LAB.md` | Document evaluation-preset v1/v2 limit, API2 alternative, and Group limit without changing validation |
| `CHANGELOG.md` | Published Alpha1 entry with explicit temporal boundary |

Historical reports, schema documents, screenshots, code labels and fixtures
were not rewritten. No current index link required relocation.

## M. Elevated installer lifecycle

**OPEN — NOT RUN.** The Windows principal's
`IsInRole(WindowsBuiltInRole.Administrator)` returned **False**. Phase 3's
`PrivilegesRequired=admin` installer therefore cannot be lifecycle-qualified
in this session under the task's no-workarounds boundary. No self-elevation,
installer redesign, install, upgrade, or uninstall was attempted.

Required future evidence remains the actual elevated install → installed CLI/GUI
smoke → upgrade/data preservation → uninstall checks in
`tools/smoke_after_install.ps1 -InstallerPath <qualified-installer> -AppDir
<isolated-app-path> -DataRoot <isolated-data-path> -Lifecycle`, including registry,
Start Menu, data preservation, and residue assertions. Phase 3's compiled
installer/frozen execution evidence is not that lifecycle evidence. Sandbox
approval to launch the existing Python runtime for this audit is not Windows
administrator elevation and does not close this gate.

## N. Future presentation recommendation — not implemented

1. **Default:** retain engine metadata-based resolution: API2 → permanent v4,
   API1 → permanent v2, VM → v1. For a future fresh V5 GUI onboarding choice,
   propose permanent v4 first; changing that initial UI default is a separately
   approved UX behavior change, not a Phase 4 cleanup.
2. **Primary order:** v4 “Recommended — process agents, API v2”, then v2
   “Single-actor agents, API v1”. Preserve the API1 lane and its Group workflow.
3. **Advanced/Legacy order:** v1 “Native VM/blob and historical API v1”,
   then v4 alpha2, then v4 alpha1 “Historical reproduction”. In a VM-specific
   workflow v1 must be directly visible, not buried behind a generic legacy gate.
4. **Development/Evaluation:** use the same compatible gameplay identities;
   show evaluation methodology and Group restrictions separately. No new IDs.
5. **CLI versus GUI:** keep the five explicit public CLI IDs accepted, even
   if help groups/reorders their presentation later. Advanced/Development/
   pairwise GUI should retain access to that same historical set; Simple's
   smaller set and Python-only evaluation workflows remain legitimate differences.
6. **Compatibility/internal:** keep v2 alpha1/alpha11 and v3 alpha1 out of
   ordinary new-match menus as today, with their execution and reader support
   intact. No general “show every registered policy” control is warranted.

Must retain: all eight policies, historical identity/provenance helpers,
original agent fixtures and schemas. Should expose: permanent v4/v2 and v1
for its supported VM use. Could hide from **primary** new-match presentation:
V4 alphas, retaining an explicit historical reproduction route. Simple already
does this. Could eventually remove: **none justified by current evidence**.

## O. Removal/hiding impact matrix

| Candidate | Hide from ordinary new matches? | Must remain loadable/executable? | Tests affected by removal | Replay risk | Agent risk | Recommendation |
|---|---|---|---|---|---|---|
| v1 | Only outside VM/history workflows | Yes | V1 equivalence, VM, persistence, legacy provenance, Python evaluation | Break attribution recovery and original reproduction | Four VM starters lose their public runtime; API1 historical behavior lost | B; keep accessible |
| v2 | No | Yes | V2 promotion, runtime, Group, benchmark tests | Lose distinct core-family interpretation/reproduction | Seven current Python starters and Group workflow | A for API1 |
| v4 alpha1 | Could group behind Legacy in a future UX phase | Yes | Process/API gates, alpha2 delta controls, replay tests | Different placement/process semantics cannot be substituted | Historical placement-dependent agents/studies | B, explicit reproduction retained |
| v4 alpha2 | Could group behind Legacy in a future UX phase | Yes | Placement/scheduler and permanent-v4 equivalence | Equal gameplay does not permit rewriting IDs/hashes/evaluation attribution | Adapted hydra/Nemesis studies and saved recipes | B, no alias to permanent v4 |
| v2 alpha1/alpha11 | Already absent from ordinary selectors | Yes | Core/beacon, promotion and real replay-status tests | Removing family membership loses status interpretation; original reruns fail | Four packaged internal reference agents and V2 evidence | C, preserve implementation/imports/data |
| v3 alpha1 | Already absent from ordinary selectors | Yes | Locality runtime/evaluation/agents | Lose research-state interpretation/reproduction | Six locality agents use experimental actions and pinned population | D, preserve research seam |
| V4/reference agent names or files | Not ordinary-menu cleanup by prefix | Yes where currently consumed | Stable equivalence, Quorum, starters/refresh/benchmarks | Recorded source identity and reproducibility broken by rewriting | Break source catalog and old qualification | Retain all; no manifest rewriting |
| Wheel/sdist historical resources | Not catalog-visible today | Yes for live resource loaders/research | V2/V3 resource/benchmark tests | Indirect regeneration loss; no need to load agent code for playback itself | Internal loaders require resources | Packaging separation would require a separately tested distribution contract |
| R1/R2 runner literals and evidence | Already historical, not selectors | Historical source retained; production IDs already unavailable | Negative registration tests and research analysis | Historical replay identity must not be rewritten | Historical reruns require recorded commits | Retain evidence; do not restore rejected mechanics |
| `evaluation-rules-1` alias | Not a menu item | Yes for attribution | Rules/evaluation history comparisons | Incorrect normalization/confidence if removed | No manifest migration needed | Retain alias; never add execution alias |

All candidates were checked against registry/source, parser/UI exposure,
reader/helpers, manifest/benchmark data, tests, historical qualification,
current documentation, and package-data/spec boundaries. No absence-of-reference
argument overrides the explicit frozen-contract and reproduction evidence.

## P. Deferred product decisions and newly confirmed issues

- **P4-01 — Evaluation-preset mismatch:** only v1/v2 preset IDs are accepted,
  although pairwise CLI/GUI supports three V4 IDs. Decide a focused preset
  compatibility extension with methodology validation and identity tests;
  preserve existing presets. Documentation workaround added, no fix implemented.
- **P4-02 — Core-status coverage asymmetry:** equal stored core state yields
  `core is None` under alpha2/permanent v4 but a core status under alpha1.
  Review intended HUD coverage and the separate newer capture renderer before
  deciding a replay-presentation fix. No replay-loading defect or gameplay
  divergence was found by the audit; no equivalence baseline should be rebased.
- **P4-03 — Onboarding/order/labels:** qualify v2 as API1, consider v4-first
  fresh GUI selection and grouped legacy choices after Alpha feedback.
  Selection persistence, metadata repair, keyboard/accessibility paths and
  saved recipes require explicit UX qualification.
- **P4-04 — Validation presentation:** CLI help/resolution diagnostics and
  some policy comments imply wider compatibility than whole-match composition
  allows; Tournament GUI defers API mismatch reporting to CLI. Wording and
  early-feedback improvements belong in a separate focused change.
- Group support for V4 requires a methodology/product decision; it is not
  implied by the engine's ability to run more than two entrants.
- Do not remove research package resources or original reference agents without
  a distribution/migration and reproducibility plan. Current evidence favors retention.
- The real installer lifecycle and human first-user qualification remain open.

## Q. Files changed

Modified: `CHANGELOG.md`, `README.md`, `docs/AGENT_AUTHORING.md`,
`docs/AGENT_LAB.md`, `docs/COMPATIBILITY.md`, `docs/V5_STARTER_AGENTS.md`.
Added: this report,
`docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md`.
Deleted: none. All seven deliverable files are Markdown; no executable
source/configuration, tests, schemas, manifests, or packaging inputs changed.

## R. Validation

Commands ran from `D:\Projects\BATTLE2`. The existing `.venv` Microsoft Store
Python launcher could not start inside the sandbox (`The file cannot be
accessed by the system`); approved execution outside that sandbox used the
same interpreter without changing the environment or installer privileges.

| Check | Exact result |
|---|---|
| Git identity/status/version preflight and registry/manifest census | Clean start, HEAD/Phase3 relationship as A; 8 policies, 21 starters; no enforced manifest ruleset pins |
| `.venv\Scripts\python.exe -m pytest engine/tests/test_ruleset_policy.py engine/tests/test_ruleset_agent_compatibility.py engine/tests/test_designer_ruleset_options.py engine/tests/test_ruleset_persistence.py engine/tests/test_v4_stable_ruleset_equivalence.py client/tests/test_replay_status.py client/tests/test_replay_session.py --basetemp=.pytest-tmp-phase4-surface` | **236 passed in 7.61s**, exit 0; includes permanent V4 equivalence |
| Isolated synthetic reader/provenance probe via Python stdin | **9 replay probes + 3 missing-ID cases passed**, exit 0; all temp files removed by the temporary-directory context |
| Evaluation-preset probe via Python stdin and temporary YAML/JSON files | v1/v2 accepted; v4 alpha1/alpha2/permanent rejected with the documented allowed-set error; exit 0 |
| Documentation/local-link validation via Python stdin | **181 Markdown files, 459 local targets, 8 changed-file anchors, 0 failures**, exit 0; fenced/inline code excluded; external URLs not checked |
| `git diff --check` | **PASS**, exit 0; only existing Windows CRLF-to-LF normalization notices |
| Final diff/status/HEAD inspection | Exactly six modified Markdown files and this untracked report; nothing staged; HEAD unchanged at A's exact SHA |

The local-link sweep found and corrected an existing obsolete README anchor
in the authoring guide. Its first parser also counted two inline example
targets in the historical Phase 1 report; excluding inline code removed those
false positives without modifying historical evidence. The final check above
has no failures. Pytest's task-created temporary directory was moved intact
from `.pytest-tmp-phase4-surface` to ignored `build/phase4-surface-pytest-temp`
after testing; no unrelated temporary files were changed.

Final `git status --short`:

```text
 M CHANGELOG.md
 M README.md
 M docs/AGENT_AUTHORING.md
 M docs/AGENT_LAB.md
 M docs/COMPATIBILITY.md
 M docs/V5_STARTER_AGENTS.md
?? docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md
```

The first synthetic probe completed its nine replay cases but its final
metadata-only setup omitted required `MatchConfiguration.arena_size` and
raised `TypeError`. Correcting the probe input to 64 and rerunning the complete
probe passed; no application fix or test expectation change was made.
No full suite, mypy, ruff, frozen build or installed lifecycle rerun is claimed:
only documentation changed, and the additional focused tests support the audit
findings rather than requalifying a new release artifact.

No ruleset was removed, renamed, hidden, reordered, or default-changed.
Gameplay, ruleset semantics, parameters/presets, Agent APIs, replay schema,
loading and interpretation, starter behavior, CLI/Designer behavior and all
expected gameplay results remain unchanged. No expected result was rebased.
Replay History was not implemented. No commit, push, tag, release or publication
was performed, and the next phase was not begun.

## S. Recommended next phase

**Phase 5: Replay History discovery/design**, without implementation: establish
the run/replay inventory, provenance and missing/corrupt-file behavior, proposed
search/filter metadata, storage/index requirements, selection/handoff contract,
and acceptance tests. Reuse the existing readers and preserve all identities;
do not treat unknown rulesets as unreadable files or re-execute agents to browse.

P4-01 and P4-02 merit separate bounded compatibility/presentation follow-ups;
neither justifies changing gameplay or removing historical support now.
Keep ruleset ordering/grouping as an explicitly approved later UX phase after
Alpha feedback. Close the installer lifecycle in an elevated release-engineering
session independently of Replay History design.
