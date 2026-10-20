# Bytefray Component Identity and Versioning Policy

**Status:** adopted on the `v6-component-identity` branch on 2026-10-18 as the
project's versioning convention. It takes effect when the project lead accepts
the component-identity milestone. It renames and renumbers nothing: every
identity that exists today keeps its exact spelling and meaning (§5).

This policy says how each part of Bytefray is named and versioned.
[COMPATIBILITY.md](COMPATIBILITY.md) remains the reference for what each
existing identity means and which artifacts stay readable. Release
compatibility records (§6) say which component versions one application
release ships.

## 1. The rule

Every component has its own identity and its own version line. A
component's version changes only when that component changes. An application
release lists the component versions it ships in a compatibility record. The
application's version number never implies them.

- A Bytefray release may ship the same Ruleset, Agent API and formats as an
  earlier release.
- A new Ruleset does not require a new major application version.
- A Spectator release does not require a new Ruleset, and a Bytefray release
  does not require a new Spectator release.
- Research does not acquire application version numbers.
- Supported persisted formats keep their established identities until an
  approved format change.

## 2. Components

| Component | Identity form | On this development line | Defined in | Changes when |
| --- | --- | --- | --- | --- |
| Bytefray application | SemVer `MAJOR.MINOR.PATCH[-PRERELEASE]` | `5.0.0` released; `5.1.0-alpha.1` release candidate (`5.1.0a1`) | `pyproject.toml`, `tools/installer.iss` | a user-visible product change ships (§4.1) |
| Gameplay Ruleset | immutable ID + display name | `bytefray-rules-4` **Classic**; `bytefray-rules-6-alpha1` **Active Sensing (Alpha)** | `battle_engine.rules`, `battle_engine.ruleset_policy`, `battle_engine.ruleset_names` | any gameplay-observable change → a new ID (§4.2) |
| Agent API | integer `api_version` | 2 | `battle_engine.agent_api` | the agent programming contract changes incompatibly (§4.4) |
| Agent manifest capabilities | integer `capabilities.version` | 1 (`sense`) | `battle_engine.agent_capabilities` | the capability block's shape changes |
| Replay format | `battle2.replay` + integer | writes 4; reads 2, 3, 4 | `battle_engine.replay` | wire shape changes (§4.5) |
| Trace format | `bytefray.agent_trace` + integer | writes 2; reads 1, 2 | `battle_engine.agent_trace` | wire shape changes |
| Result format | `battle2.result` + integer | writes 2; reads 1, 2 | `battle_engine.result_model` | wire shape changes |
| Other persisted formats | schema name + integer | §5 | the owning module | wire shape changes |
| Bytefray Spectator application | its own SemVer series | none released | Spectator repository | Spectator ships (§4.6) |
| Spectator presentation protocol | `bytefray.spectator.manifest` + integer; documents + integer | Bytefray writes 2; Spectator reads 1, 2; documents 1 | `battle_client.spectator_export`; Spectator `docs/PRESENTATION_CONTRACT.md` | the presentation contract changes (§4.7) |
| Research | objective-based identifiers | V6 program, E2–E9 (historical names kept) | `docs/research/`, `tools/research/` | a new study is registered (§4.8) |

## 3. What an application version is not

The application version identifies the installable product and nothing else.

- `product_version` in `result.json` records which application produced an
  artifact. It is the installed distribution's version in PEP 440 form
  (`5.0.0`, later `5.1.0a1`). It never identifies gameplay; `ruleset_id`
  does.
- `bytefray --version` prints the application version alongside the Agent
  API, result and replay versions it uses. Those are separate facts on one
  line, not one version.
- "V3", "V4", "V5" and "V6" name research-and-development programs and their
  branches (`v6-research`). "Alpha 1" and the M1/M2 milestones are stages of
  the V6 program. None of them is an application version: the V6 program's
  Active Sensing work is planned for **Bytefray 5.1**, and nothing announces a
  Bytefray 6.0.

## 4. Conventions by component

### 4.1 Bytefray application

Semantic Versioning 2.0.0.

- **MAJOR** — a deliberate break of a promise the previous release line made:
  removing a supported command or workflow, removing an executable stable
  Ruleset, ending execution of a still-supported Agent API version, dropping
  the ability to read a persisted format the previous release could read, or
  changing the default Ruleset.
- **MINOR** — new capability: a new Ruleset (stable or experimental), a new
  Agent API version offered alongside the current one, a new persisted-format
  version written while earlier versions stay readable, a new integration
  such as Spectator, new Designer workflows, or the retirement of an
  experimental or research capability.
- **PATCH** — fixes that change no component identity: no new Ruleset ID, no
  new format version, no Agent API change. Repairing a regression back to an
  identity's frozen characterization is a patch. Changing what a shipped
  identity does needs a new Ruleset ID (§4.2), so it is never a patch.
- **Prerelease** — `-alpha.N` (scope still settling inside the approved
  freeze), `-beta.N` (feature-complete), `-rc.N` (release candidate), using
  the dotted SemVer form so `alpha.10` sorts after `alpha.2`. Each prerelease
  gets its own tag; a published tag is never moved or reused.

Spellings: the SemVer form is canonical for documentation, release titles,
Git tags (`v5.1.0-alpha.1`) and installer file names. Python package metadata
uses the equivalent PEP 440 normal form (`5.1.0a1`), and that is the string
`result.json` records. `tools/release_compatibility.py` derives one from the
other. Historical tags keep their original spellings (`v4.0.0-alpha1`,
`v5.0.0-rc1`, `b5.0.0-alpha1`); they are never re-tagged.

*Transition note.* This policy is adopted after the V6 Phase 2B.9–2B.12
retirements, which ended execution of Agent API v1, VM/blob agents,
Redcode/pMARS and Rulesets 1, 2, 2-alpha1, 2-alpha11, 3-alpha1, 4-alpha1 and
4-alpha2. Bytefray 5.0.0 still executes them. Read strictly, §4.1 classes
ending a still-supported Agent API as MAJOR. The project lead's approved
designation of the next release as 5.1 is recorded here as a one-time
decision taken before this policy existed. Releases after it follow §4.1
as written. Every retired artifact stays readable, and 5.0.0 remains
available for re-execution.

### 4.2 Gameplay Rulesets

A Ruleset ID names one exact set of gameplay semantics, permanently.

- **Immutable.** An identity's behavior is what it shipped with, as pinned by
  its frozen goldens and characterizations. Any intended gameplay-observable
  change (scoring, scheduling, placement, sensing, visibility, capture,
  termination, action semantics) creates a new ID, even when the shipped
  behavior is considered a mistake. A Ruleset has no minor or patch versions.
  The one exception is the existing AGENTS.md rule: code that drifts from an
  identity's frozen goldens is an implementation defect. Restoring the
  goldens repairs that defect under the same ID; it does not re-bless the
  drifted behavior.
- **Lifecycle is a state, not a name.** Stable, experimental, research,
  retired-research and historical-read-only are recorded in
  `battle_engine.ruleset_policy`'s lifecycle sets. Moving an identity between
  states never renames it.
- **Promotion creates a new stable ID.** An experimental ID's artifacts must
  stay honestly attributed, so promoting its semantics registers a separate
  stable ID. This follows the existing precedents
  `bytefray-rules-2-alpha11` → `bytefray-rules-2` and `bytefray-rules-4-alpha2`
  → `bytefray-rules-4`.
- **The number is a Ruleset generation.** Existing numbers once coincided
  with an application major version or a research program. They imply
  nothing about any application version: `bytefray-rules-6-alpha1` ships in
  Bytefray 5.1.
- **Future product IDs** are `bytefray-rules-<G>` (stable) or
  `bytefray-rules-<G>-<stage><N>` (experimental, `alpha` or `beta`), where `G`
  is a generation number. Generations 1–6 are allocated. Promoting Active
  Sensing would register `bytefray-rules-6`. An unrelated new Ruleset takes
  the next unused generation, 7, whatever the application version is then.
- **Future research IDs** use `bytefray-rules-research-…` (§4.8), so no
  research identity looks like a product generation. Existing
  `bytefray-rules-6-research-*` IDs keep their spelling.
- **No aliasing.** The only alias is the finite historical table in
  `battle_engine.rules` (`evaluation-rules-1` → `bytefray-rules-1`). Nothing
  maps a retired ID onto a current one.
- **No speculative registrations.** A Ruleset is registered only by an
  approved gameplay change; this policy registers none.

### 4.3 Ruleset display names

`battle_engine.ruleset_names.RULESET_DISPLAY_NAMES` is the single table of
display names. CLI help, Designer, Replay History, tournament results and
the Active Sensing viewer all read it.

| Ruleset ID | Display name | Stability |
| --- | --- | --- |
| `bytefray-rules-4` | **Classic** | stable; the default everywhere |
| `bytefray-rules-6-alpha1` | **Active Sensing (Alpha)** | experimental; explicit selection only |

Rules:

- **Presentation only.** A display name is never persisted, never accepted as
  input (`--ruleset Classic` is rejected), and never used to decide
  compatibility. Selection, filtering and capability checks run on the
  canonical ID.
- **Product-offered identities only.** Only the public stable and public
  experimental Rulesets have names. Historical, retired and research
  identities never get one; readers show their exact ID or a label derived
  from it (`Ruleset v4 alpha2`). That keeps `bytefray-rules-4-alpha2` from
  ever reading as "Classic".
- **Experimental names carry their stage**, for example "(Alpha)". The stage
  describes the Ruleset's maturity, not the application's prerelease state:
  Active Sensing can stay "(Alpha)" in a final 5.1.0. A promoted Ruleset's
  new stable ID gets the name without the marker.
- **The canonical ID stays visible** wherever someone needs it: Designer
  Ruleset item tooltips, Replay History tooltips and details, CLI help and
  output, the Pygame HUD, Spectator's title and footer, and every artifact.
- **Names may be refined** in any application release, because nothing
  depends on their spelling. A change is a UI change and belongs in the
  CHANGELOG.

### 4.4 Agent API

- Integer generations, declared in agent manifests as `api_version: N`. There
  are no minor, patch or prerelease API versions.
- Bump `N` only when an existing valid agent could behave differently or stop
  loading.
- A feature that leaves existing agents unaffected, such as the
  Ruleset-gated `SENSE` action, is expressed through manifest capabilities
  (`capabilities.version` 1, known names) and Ruleset gating, not through a
  new API version.
- A new API version is added alongside the current one. Ending execution of
  an older version is an application-level change (§4.1).
- Contracts: [AGENT_API_V1.md](AGENT_API_V1.md) (historical, frozen) and
  [AGENT_API_V2.md](AGENT_API_V2.md).

### 4.5 Persisted formats (replay, trace, result and the rest)

- Identity is the pair (schema name, integer `schema_version`). Schema names
  are permanent protocol identifiers; `battle2.*` names stay `battle2.*`.
- A writer writes exactly one version. A reader lists the versions it accepts
  and rejects everything else.
- Bump the version for any change an existing strict reader would reject or
  misread. Optional additive fields are allowed only where that format's spec
  says readers ignore unknown keys.
- There are no minor, patch or prerelease format versions. Experimental
  content goes under a separate schema name or file, never under a stable
  name.
- Specs: [REPLAY_SCHEMA.md](REPLAY_SCHEMA.md), [RESULT_SCHEMA.md](RESULT_SCHEMA.md),
  [specs/agent_lab.md](specs/agent_lab.md) and
  [specs/v4_api_v2_trace.md](specs/v4_api_v2_trace.md) for traces.

### 4.6 Bytefray Spectator application

- Spectator has its own SemVer release series, independent of Bytefray's.
- The project lead set its first distribution version, `0.1.0-alpha.1`, in the
  2026-10-20 Windows installer authorization. That build is bundled with the
  Bytefray 5.1.0-alpha.1 Windows installer candidate and pinned, by source
  commit and executable SHA-256, in Bytefray's `tools/spectator_companion.json`.
  The Spectator source does not embed the number yet: it has no tag, no
  `config/version` and empty export-preset version fields. A version is
  published only together with a qualified build.
- A Spectator release declares the presentation-manifest versions it reads.
  A Bytefray release declares the manifest version it writes and the Spectator
  builds it was verified with (§6).
- Spectator's `bytefray.pin.json` (`bytefray.spectator.pin` v1) pins the
  source of its legacy prototype exporter. It is unchanged.

### 4.7 Spectator presentation protocol

- `bytefray.spectator.manifest` versions: **1** is Spectator's own prototype
  exporter (`teaching_demo`, `showcase_match`); **2** is Bytefray's production
  exporter (`bytefray_match`). Both carry `bytefray.spectator.broadcast` and
  `bytefray.spectator.agent_view` documents at version **1**.
- Writer and reader version independently. Bump the manifest version for a
  manifest-shape change and a document version for a document-shape change. A
  new perspective is a contract change, not a display-name change.
- `EXPORTER_VERSION` (1) identifies the exporter implementation for cache
  reuse. It is not a wire-format version.
- Contracts: [specs/spectator_export.md](specs/spectator_export.md) and
  Spectator's `docs/PRESENTATION_CONTRACT.md`.

### 4.8 Research

Historical research keeps every name. V3–V6 program names, experiment IDs
(E2–E9), phase names, document names and locations, freeze identifiers,
source manifests and research Ruleset IDs are unchanged. **E9 remains LOCKED
and Requirement C remains NOT ESTABLISHED**; this policy does not touch either.

Future research is named for what it investigates, not for a release it might
feed. The areas and examples below are proposals for future studies; this
policy creates no experiment.

| Area | Code | Investigates |
| --- | --- | --- |
| Core mobility | `MOB` | moving cores, relocation costs |
| Core placement and capture | `CAP` | placement, capture conditions, capture holds |
| Visibility and observation | `VIS` | what agents can see, sensing models |
| Multi-agent dynamics | `MAD` | three or more entrants, coalitions |
| Scheduling and response order | `SCH` | pass order, response timing, seat effects |
| Information-cost tradeoffs | `INF` | priced information, action budgets |

- **Study ID:** `<CODE>-<NN>`, for example `VIS-01`. Documents go under
  `docs/research/<area>/`, tools under `tools/research/<area>/`, and outputs
  under `runs/research/<area>/<study-id>/`, with lowercase area slugs such as
  `visibility-observation`.
- **Research Ruleset ID:** `bytefray-rules-research-<code><nn>-<variant>`,
  lowercase, for example `bytefray-rules-research-vis01-active-w27`. A study
  ID never becomes a display name or an application version.
- **Adoption:** a finding may reach any later application release by
  registering a new product Ruleset (§4.2) with its own display name, or it
  may stay research-only.

### 4.9 Agent, starter and milestone names

- Agent IDs and starter IDs (`v4_claimer`, `v5_dual_team`, `v6_window_scout`)
  are recorded in replays and results. Starter manifests, including display
  strings such as "V6 Window Scout (Starter)", are bound by starter content
  digests and scenario-card evidence. They keep their spelling.
- New starters should be named for their behavior, without a version prefix.
  They declare Ruleset requirements through manifest capabilities.
- Designer labels for starter copies use behavior names ("Window Scout —
  personal copy"); the Ruleset requirement is stated by the Ruleset selector.

## 5. Identities that do not change

Verified against the code on this line. `engine/tests/test_component_identity.py`
pins the Ruleset IDs, the wire-format identities and the Spectator contract.

| Identity | Kind | Persisted in | Disposition |
| --- | --- | --- | --- |
| `bytefray-rules-4`, `bytefray-rules-6-alpha1` | product Rulesets | results, replays, traces, evaluations, Spectator manifests, Replay History cache | unchanged; display names added (§4.3) |
| `bytefray-rules-1`, `-2`, `-2-alpha1`, `-2-alpha11`, `-3-alpha1`, `-4-alpha1`, `-4-alpha2` | historical Rulesets | historical artifacts | unchanged; readable, not executable, no display name |
| 14 `bytefray-rules-6-research-*` IDs | research Rulesets | research corpora, freezes, manifests | unchanged; research-only |
| `evaluation-rules-1` | historical alias | old evaluations | unchanged; normalized for comparison only |
| Agent API 2 (1 retired from execution) | programming contract | agent manifests, replays | unchanged |
| capabilities v1 (`sense`) | manifest metadata | agent manifests | unchanged |
| `battle2.replay` 4 (reads 2–4) | wire format | `replay.jsonl` | unchanged |
| `battle2.result` 2 (reads 1–2) | wire format | `result.json` | unchanged |
| `bytefray.agent_trace` 2 (reads 1–2) | wire format | `trace.jsonl` | unchanged |
| `bytefray.evaluation` writes 7 / identity 7 (the Classic and research methodologies); versions 4–6 belong to retired methodologies | wire format | `evaluation.json` | unchanged; historical versions stay readable through evaluation history |
| `battle2.tournament` 1, `bytefray.agent_package` 1, `bytefray.agent_revision` 1, `bytefray.evaluation_preset` 1, `bytefray.benchmark_population` 1 | wire formats | their artifacts | unchanged |
| `bytefray.sensing_demo` 1, `bytefray.sensing_playback` 1 | wire formats | sensing demonstrations | unchanged |
| `bytefray.spectator_*` 1 (events, derivation, director, perspective, aggregates, fight_night) | Pygame/analysis formats | spectator-intelligence outputs | unchanged |
| `bytefray.spectator.manifest` 1 and 2; broadcast/agent_view 1; `bytefray.spectator.cache` | presentation protocol | Spectator presentations, Designer cache | unchanged |
| Replay History cache schema 2, extractor 1 | local cache | `<data root>` cache | unchanged (rebuildable) |
| local source fingerprint 1, agent revision fingerprint 1, starter content digest 1 | hash scopes | manifests, revisions, evidence | unchanged |
| starter agent IDs and manifests | agent identities | replays, results, scenario cards | unchanged byte-for-byte |
| `product_version` values already recorded | application identity | `result.json` | unchanged; never rewritten |

## 6. Release compatibility records

Each planned or published application release has one record:
`docs/releases/BYTEFRAY_<MAJOR>_<MINOR>_<PATCH>[_<STAGE>_<N>]_COMPATIBILITY.json`
(schema `bytefray.release_compatibility` v1). It is the single authoritative
declaration of:

- the application version, its PEP 440 form and tag;
- the default Ruleset, each offered Ruleset with display name and stability,
  and the Rulesets each surface offers;
- research and historical Ruleset handling;
- Agent API, capability and persisted-format versions;
- the Spectator application builds, presentation-protocol versions, supported
  matches and Designer viewer dispatch;
- platform status, known limitations and unsupported combinations.

The companion `.md` summary is generated from the JSON by
`tools/release_compatibility.py --write`. The `--check` mode, run by
`engine/tests/test_release_compatibility_record.py`, verifies every claim the
code can confirm and fails if the summary is stale. Hand-written context such
as qualification status sits outside the generated block.

Lifecycle: **proposed** (planning; no version bump) → **candidate** (the
release-candidate milestone bumps the runtime version) → **released**
(published; then frozen, and corrections go in a dated errata section). Never
create a second manifest for the same release. README, CHANGELOG and release
notes link to the record instead of restating it.

Current record: [5.1.0-alpha.1 (candidate)](releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md).

## 7. Decisions reserved for the project lead

- Confirm the §4.1 transition note: 5.1 as the designation for the first
  release after the execution retirements.
- Choose Spectator's first version number and when to publish it (§4.6).
- Accept or adjust the display names and the future-ID conventions in §4.2
  and §4.8.
