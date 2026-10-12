# Bytefray V5 Alpha 1 — Phase D: Authoring Guidance & Parameter Schemas

**Status:** Phase D Implementation & Qualification Record
**Branch:** `v5-research`
**Starting HEAD:** `69fc95828f6c243331e182217d8cfbfbb4eea15c` (`feat(v5): add educational starter agent population`)
**Project Version:** `5.0.0a1` (unchanged)
**Stable Gameplay Ruleset:** `bytefray-rules-4` (unchanged)

---

## A. Starting baseline

| Precondition | Observed | Required |
|---|---|---|
| Branch | `v5-research` | `v5-research` |
| HEAD | `69fc95828f6c243331e182217d8cfbfbb4eea15c` | — |
| `HEAD == origin/v5-research` | Yes (`origin/v5-research` = `69fc958`) | Yes |
| Working tree | Clean (`git status --short` empty) | Clean |
| `git diff --check` | Clean, no output | Clean |
| `.git/index.lock` | Absent | Absent |
| `.git/index` | 92,243 bytes, `Sep 9 06:52` | Healthy |
| Phase C commit present | Yes (`69fc958`, HEAD itself) | Yes |
| Project version | `5.0.0a1` (`pyproject.toml:10`) | `5.0.0a1` |

`.git/index.corrupt-20260908`, `.git/index.corrupt-backup` and
`.git/index.corrupt-phaseB` are the pre-existing historical recovery
artifacts named in the phase brief and were ignored, not touched.

Two pre-existing entries exist in `git stash list` (`sync_win auto-stash`,
dated 2025-10-05 and 2025-10-01). They predate this phase and were left
untouched.

---

## B. Pre-Phase-D parameter architecture

A full end-to-end trace was performed before any design work. The finding
that determined the whole design:

> **Before Phase D, a Python agent could not receive parameters at all.**
> The mechanism existed, was wired end to end from the Agent Designer, and
> was silently discarded for exactly the agents Agent API v2 is about.

### The path as it actually existed

```
Agent Designer "Agent Params" tab (app/views/advanced.py, JsonEditor)
        │  RunConfig.a_params / b_params / c_params
        ▼
app/agent_designer.py::_on_advanced_run   (and app/services/engine_commands.py)
        │  env BYTEFRAY_AGENT_{A,B,C}_PARAMS_JSON = <JSON object>
        ▼
engine/src/battle_engine/cli.py::_resolve_agent
        │  _parse_env_json(...)  ->  side_env
        ├── kind == "python"  ──►  return spec   ← side_env COMPUTED AND DISCARDED
        ├── blob agent        ──►  side_env["blob_path"] only
        └── built-in VM       ──►  build_agent(name, start, **_merge_params(cli_kwargs, side_env))
```

### Answers to the twelve audit questions

| # | Question | Pre-Phase-D answer |
|---|---|---|
| 1 | Does `agent.yaml` support parameter metadata? | Only a free-form `defaults:` object (`AgentSpec.defaults`). No types, bounds, descriptions or presets. |
| 2 | Do match requests carry agent parameters? | **No.** `MatchRequest`/`MatchEntrant` had no parameter field. |
| 3 | Does the CLI accept overrides? | Only via `$BYTEFRAY_AGENT_{A,B,C}_PARAMS_JSON`. No CLI flag existed. |
| 4 | Does the Designer expose a free-form params field? | Yes — Advanced tab, per slot, validated locally as JSON. |
| 5 | How are values serialized? | A JSON object in an environment variable. |
| 6 | How do values reach an agent instance? | **VM/built-in only**, as `build_agent(..., **kwargs)`. `load_python_agent` calls `factory()` with **no arguments**. |
| 7 | Do API v1 and v2 share a mechanism? | Neither received parameters. Only VM built-ins did. |
| 8 | Do parameters participate in identity / replay / result / evaluation? | **No.** Absent from `canonical_match_id`, `_reproducibility`, replay and result. (VM params participated only transitively, via `code_sha256`.) |
| 9 | Are unknown keys allowed? | Yes — free-form `**kwargs` into `build_agent`, which reads what it recognises and ignores the rest. |
| 10 | Do current agents rely on free-form params? | Only VM/blob agents (`byte`, `offset`, `ptr`, `step`, `delta`, `blob_path`, `aggression`). **Zero Python agents declare `defaults:`** — verified across every manifest in `agents/` and `data/starter_agents/`. |
| 11 | Does ordering affect deterministic identity? | Not applicable — parameters were not in identity. |
| 12 | Do tests define compatibility expectations? | Yes: `test_cli_characterization.py::test_resolve_agent_applies_per_agent_env_json_to_builtin_construction`, `test_designer_third_entrant_command.py`, `tests/test_agent_designer_lifecycle.py`. |

`AgentSpec.defaults` was read in exactly one place in the entire product: a
`params=` preview line printed by `cli.py` before a match. It reached no
agent, VM or Python.

**Consequence for the design.** Because no delivery path for Python agents
existed, Phase D had to create one — but only one, reusing every existing
surface (the environment variable, the manifest, the entrant) rather than
inventing a parallel channel.

---

## C. Schema design

Two new optional top-level `agent.yaml` sections, parsed by one new module,
`engine/src/battle_engine/agent_parameters.py`.

```yaml
parameters:
  <key>:                    # lowercase letter, then [a-z0-9_]
    type: integer           # integer | number | boolean | string | choice
    default: 4              # REQUIRED, validated against its own constraints
    minimum: 0              # integer/number only
    maximum: 8              # integer/number only
    choices: [a, b]         # choice only; non-empty, unique strings
    description: "..."      # optional
presets:
  <name>:                   # same key syntax
    description: "..."      # optional
    values:                 # REQUIRED; only declared keys; schema-validated
      <key>: <value>
```

### Rationale for the five types

Derived from what Bytefray agents actually configure, not from completeness:

| Type | Real product need |
|---|---|
| `integer` | Cell counts and cadences — every V5 starter parameter but one. |
| `number` | Process shares, which are floats summing to 1.0 (`v5_dual_team`). |
| `boolean` | On/off behaviour switches. The phase brief also requires an explicit boolean vocabulary (§11), which presupposes the type. |
| `string` | Free text; the legacy free-form path already carries string values such as `blob_path`. |
| `choice` | A fixed menu of named behaviours — the one shape a bounded integer cannot express. |

Deliberately **not** built: nested objects, arrays, conditional schemas,
expression languages, `$ref`, or any general JSON Schema subset. The module
docstring states this as a standing constraint.

### Why two sections rather than nesting presets under parameters

Presets are a sibling concept, not a property of one parameter: a preset
names a point in the whole parameter space. Keeping them separate also makes
the "a preset may only set declared parameters" rule structural.

---

## D. Compatibility policy

| Manifest | Behaviour |
|---|---|
| No `parameters` section | **Unchanged in every respect.** `EMPTY_PARAMETER_SCHEMA`, legacy free-form passthrough, unknown keys accepted, values unvalidated. |
| Legacy `defaults:` block | Parsed exactly as before into `AgentSpec.defaults`. Untouched. |
| Declares `parameters` | Strict: unknown keys rejected, values coerced and range-checked, presets validated. |

Three fail-closed manifest rules exist so a manifest can never mean two
things at once:

1. `parameters` requires `api_version: 2` — resolved values are delivered on
   `MatchContextV2`, so an agent that could never receive them may not
   declare them.
2. `presets` requires `parameters`.
3. A manifest may declare **either** `parameters` **or** a non-empty legacy
   `defaults:` block, never both.

### The Agent API v1 compatibility correction

An initial implementation raised a hard error whenever parameters were
supplied for a non-v2 agent. **The full test suite caught this as a real
regression**: `test_designer_third_entrant_command.py::test_generated_three_entrant_command_produces_a_real_three_entrant_match`
exercises the Agent Designer exporting `a_params`/`b_params`/`c_params` for
**Agent API v1** agents, which have always ignored them. Failing there would
have broken a working user path to enforce a rule that arrived after it —
precisely what §10 of the phase brief forbids.

Final policy for a non-v2 agent:

- free-form overrides (env JSON or `--*-param`) — **warned about on stderr
  and ignored**, exactly as before Phase D, rather than fatal;
- `--*-preset` — **refused**, because the flag is new in Phase D (so
  refusing breaks nothing) and a silently-ignored preset name is
  indistinguishable from one that worked.

Regression-locked by
`test_v5_agent_parameters.py::test_free_form_params_for_an_api_v1_agent_stay_a_harmless_no_op`.

**No historical agent was retrofitted.** All six `v4_*` starters and every
pre-existing VM/blob agent declare no schema and are byte-for-byte unchanged.

---

## E. Resolution semantics

One canonical rule, implemented once in
`agent_parameters.resolve_parameters` and called by every surface:

```
schema defaults   <   selected preset   <   explicit overrides
```

1. Start from every declared default.
2. Overlay the selected preset's values, if one was named.
3. Overlay explicit per-match values.
4. Validate and coerce the result.

**Deterministic ordering.** The resolved mapping always contains exactly the
declared parameters in **manifest declaration order**, re-imposed after both
overlays, regardless of the order a caller wrote its overrides in. Match
identity therefore cannot depend on a dictionary's iteration order; the
identity payload additionally sorts keys. Locked by
`test_resolved_ordering_is_declaration_order_not_caller_order`.

Within the override layer, an explicit `--*-param` flag beats the ambient
`$BYTEFRAY_AGENT_*_PARAMS_JSON` environment variable.

---

## F. Validation and coercion

### Declaration-time (raises `AgentManifestError`, at agent resolution)

Key syntax; supported type; `default` present; `default` valid against its
*own* declared constraints (validated through the identical coercion path a
user override takes); numeric bounds well-formed and `minimum <= maximum`;
`choices` present, non-empty, unique, and strings, for `choice` only;
`minimum`/`maximum` for numeric types only; unsupported declaration fields;
non-mapping bodies; empty `parameters` section; presets referencing
undeclared keys; preset values failing schema validation; unsupported preset
fields; missing `values`.

### Match-time (raises `AgentParameterError`, before the match runs)

Unknown parameter key; unknown preset name; value of the wrong type; value
outside declared bounds; value outside declared choices.

Both classes inherit `AgentValidationError`, the existing user-presentable
diagnostic base — so no ordinary malformed manifest or bad value produces a
Python traceback on any surface.

### Coercion rules (the single canonical path)

The CLI and the Designer both supply text, so one path does all typing and
never guesses:

| Type | Accepts | Refuses |
|---|---|---|
| `integer` | `int`; base-10 `str` (whitespace stripped) | `bool` (a Python `int` subclass — `true` must not mean `1`); `float`, even integral (`8.0` for a cell count is more likely a units error than intent) |
| `number` | `int`, `float`; `str` parseable by `float()` | `bool`; non-finite (`inf`, `nan`) |
| `boolean` | real `bool`; case-insensitively `true`/`yes`/`on`/`1` and `false`/`no`/`off`/`0` | every other string; bare `int` |
| `string` | `str` | anything else (no silent stringification) |
| `choice` | a declared choice | anything else |

There is no Python truthiness anywhere in this path — `"false"` is a
non-empty string and would otherwise read as `True`.

---

## G. Runtime and provenance integration

### Delivery

```
agent.yaml (parameters/presets)
        │  agents.py::_spec_from_dir -> parse_parameter_schema
        ▼  AgentSpec.parameter_schema
cli.py::_resolve_entrant_parameters
        │  resolve_parameters(schema, legacy_defaults, preset, overrides)   ← fails here on bad input,
        ▼                                                                     before any agent import
MatchEntrant.parameters   (validated, immutable MappingProxyType)
        ▼
process_runtime.ProcessMatchController
        ├── in-process    ──►  MatchContextV2(..., parameters=...)  ──►  agent.reset(context)
        └── supervised    ──►  AgentWorkerHandle.reset(parameters=...)  ──►  worker rebuilds the
                               same MatchContextV2 on the far side of the JSON wire
```

Both Agent API v2 execution paths deliver identically. Resolved values are
scalars by construction, so they cross the supervised worker's JSON wire
unchanged; the worker reads the key through `.get(...)`, keeping that
protocol tolerant in both directions like `locality_reach` before it.

`MatchContextV2.parameters` is additive, last, with a default, and read-only
by construction. **The Agent API version was not bumped**: an agent that
never looks at the field observes and behaves exactly as before, and
existing keyword construction of the context is unaffected.

### Identity

`canonical_match_id` gains a `parameters` key in a Python entrant's metadata
block, **gated on non-empty** — the identical discipline the existing `start`
key already uses, and for the same reason. Before Phase D no Python entrant
could carry parameters, so an empty mapping omits the key entirely and every
historical `match_id`, `result_id` and `replay_id` is byte-for-byte
unchanged. Keys are sorted in the hashed payload.

VM entrants were deliberately left alone: their parameters already
participate transitively through `code_sha256`, because they change the
generated program.

### Artifacts

The **resolved values** are recorded in `result.json`'s entrant metadata,
on the v4 process result path (`_build_process_result`) — the same free-form
seam `entry_point`, the source fingerprints and `processes` already use, and
omitted entirely when empty.

The **authoring schema** — types, bounds, descriptions, presets — is never
copied into a replay or result. It belongs with the agent package.

**The replay schema was not bumped**, and no pre-Phase-D artifact changes.
Asserted by `test_result_metadata_records_effective_values_but_never_the_schema`.

An early implementation attached this to `_build_python_result` (the Agent
API v1, non-process path). That was corrected: API v1 never receives
parameters, so recording them there would have claimed an effect that never
occurred.

---

## H. Starter parameterization

Five parameters across four agents. Each is one of the small number of
constants the agent's lesson is actually made of.

| Starter | Parameter | Type | Default | Range | Why this one |
|---|---|---|---|---|---|
| `v5_region_attacker` | `attacker_reach` | integer | 16 | 10–64 | Reach is simultaneously sensing radius and write radius — the trade-off the whole agent turns on, and the one `docs/V5_STARTER_AGENTS.md` already told readers to experiment with. |
| `v5_scout_striker` | `contact_memory_ticks` | integer | 60 | 0–1000 | How long a sighting stays worth attacking. Both failure modes are real: 0 can never press an advantage, very high bombards empty ground. |
| `v5_scout_striker` | `search_stride_divisor` | integer | 1 | 1–8 | 1 sweeps adjacent non-overlapping sensor bands; larger re-senses covered ground. |
| `v5_core_defender` | `inspections_per_tick` | integer | 4 | 0–8 | The agent's entire lesson as a number: the reserved inspection duty offence may not spend. |
| `v5_dual_team` | `raider_share` | number | 0.5 | 0.0–1.0 | How a fixed 8-action quota is divided between roles — the decision the example exists to show. |

Presets — two each, `standard` plus one meaningful alternative:

| Starter | Presets |
|---|---|
| `v5_region_attacker` | `standard` (16), `far_sighted` (32) |
| `v5_scout_striker` | `standard` (60, 1), `persistent` (memory 240) |
| `v5_core_defender` | `standard` (4), `vigilant` (8) |
| `v5_dual_team` | `standard` (0.5), `raid_heavy` (0.75 → a 6/2 action split) |

### Two design corrections made during the phase

**`v5_dual_team` derives rather than declares the second share.**
`declare_processes` now returns `share=self.raider_share` and
`share=1.0 - self.raider_share`, replacing two independent constants. The
pair cannot drift out of the required total of 1.0 whatever the parameter is
set to — which turns a possible footgun into the clearest statement of the
shares rule in the starter family.

**`v5_region_attacker`'s first parameter was rejected and replaced.** The
initial choice, `sweep_span_cores` (multiplying the sweep width), was
measured and discarded: with `ATTACKER_REACH = 16` and an 8-cell core, a
span of 2 drives the press margin to 0 and a span of 3 names addresses the
engine rejects. Measured against an idle target, span 2 *reduced* distinct
written addresses from 16 to 15. A knob whose only non-default values make
the agent worse is a bad teaching parameter, so it was replaced with
`attacker_reach`. The sweep width remains fixed at one core width, and the
source now says why: that is the width of the objective, not a matter of
taste.

Deliberately **not** parameterized: signature bytes, `MAX_MOVE_DELTA` (an
engine constant the agent restates), the sweep geometry itself, and anything
that would expose engine internals or permit an illegal action.

---

## I. Phase C default-equivalence

The most important result in this phase.

### Method

A semantic baseline was captured **before any Phase D edit existed**, at
`69fc958`, using the Phase C test module's own `gameplay_digest` helper —
which hashes decisions, observations, applied results and process
declarations, and deliberately excludes `wall_time_ms`, so it measures
behaviour rather than file bytes.

24 deterministic matches: 4 starters × 3 purpose-built fixtures
(`fixture_idle_target`, `fixture_drifting_target`, `fixture_core_presser`) ×
2 seeds (11, 4242), arena 512, starts (64, 200), 140 ticks.

### Results

| Configuration | Matches | Digest mismatches vs. Phase C |
|---|---|---|
| Post-change source, **no parameters delivered** | 24 | **0** |
| Post-change source, **schema defaults resolved and delivered** | 24 | **0** |
| Post-change source, **`standard` preset resolved and delivered** | 24 | **0** |

All three configurations reproduce the Phase C gameplay digests exactly.
Declaring a schema did not change how any starter plays; resolving its
defaults through the production path did not change how any starter plays;
and every `standard` preset resolves to precisely the schema defaults.

The twelve digests are recorded in
`engine/tests/test_v5_agent_parameters.py::PHASE_C_DIGEST_PREFIXES` and
asserted by
`test_v5_starter_defaults_reproduce_the_phase_c_gameplay_digest`, which runs
the match through the real resolver rather than bypassing it. The docstring
states the standing rule: if a future change moves one of these, that change
altered how a shipped starter plays — justify it, do not re-baseline it.

---

## J. Representative non-default behaviour

Each parameter was measured, default versus one alternate value, on a
deterministic fixture match. Legality was asserted intact in both runs
(every action status `APPLIED`).

| Starter | Override | Probe | Default | Altered |
|---|---|---|---|---|
| `v5_region_attacker` | `attacker_reach=32` | declared process reach | 16 | 32 |
| `v5_core_defender` | `inspections_per_tick=0` | `READ` actions in the match | 560 | **0** |
| `v5_dual_team` | `raider_share=0.75` | actions per process | keeper 560 / raider 560 | keeper 280 / **raider 840** |
| `v5_scout_striker` | `search_stride_divisor=8` | `MOVE` actions | 3 | 21 |
| `v5_scout_striker` | `contact_memory_ticks=0` | distinct written addresses | 197 | 444 |

The defender and dual-team rows are the two that matter pedagogically: the
first shows the reserved inspection duty collapsing to nothing, the second
shows the largest-remainder allocation turning 0.75/0.25 into exactly the
6/2 action split the documentation claims.

No starter's strength was tuned on the basis of any of this. These are
product-correctness measurements, not balance work.

---

## K. Authoring guide

`docs/AGENT_API_V2.md` was **substantially rewritten** from a 120-line
contract reference into the authoritative authoring guide (807 lines
changed). Rewriting the existing normative document rather than adding a
second file avoids the duplication the phase brief warns about; all
pre-existing normative content is retained, in the "Scheduling and
disruption" and "Artifacts and compatibility" reference sections.

Sections: the mental model (entrant / process / anchor / reach / core, the
`Q=8` budget, `D=1`, and the zero-cells-owned capture condition); the
lifecycle and its ordering; `MatchContextV2`; `ProcessDeclaration`;
`ObservationV2` with an explicit statement of the information boundary;
actions and addressing; entrant-wide sensing versus process-local legality;
**objective geometry** (the longest section — why point-target attack
produces activity without conversion, what legal regional pressure looks
like, the stop-at-maximum-reach trap, and an honest statement of what a
contact-centred attack cannot do); search and target memory; defence and
`previous_read_owner`; multi-process agents; determinism; parameters and
presets; and ten common mistakes drawn from the research record.

Every factual claim was checked against source: `CORE_SIZE = 8`
(`python_runtime.py:73`), the "owns zero cells" capture rule
(`apply_core_capture`), `instr_per_tick = 8` (`config.py:21`),
`disruption_duration = 1` (`process_runtime.py:620`), the `[-64, 64]` MOVE
clamp, and the `1e-12` share tolerance.

Also updated:

- `docs/V5_STARTER_AGENTS.md` — a parameters column in the ladder table,
  what each starter exposes and why, and two runnable experiments. States
  explicitly that defaults are unchanged from Phase C.
- `docs/AGENT_AUTHORING.md` — a new "Optional manifest sections" reference:
  the exact syntax, a worked example, a block of invalid examples with the
  reason each is rejected, the three fail-closed rules, and the
  compatibility statement for manifests without a schema.

---

## L. Phase E readiness

`AgentSpec.parameter_schema` is always present — `EMPTY_PARAMETER_SCHEMA`,
never `None` — so a caller can always ask a spec what it exposes without
first checking whether it exposes anything. Schema parsing lives in the
engine package, not in CLI-specific code.

The Designer can answer all six of its questions programmatically:

| Question | Call |
|---|---|
| What parameters does this agent expose? | `spec.parameter_schema.declaration_order()` |
| What type is each? | `schema.parameters[key].type` |
| What is its default? | `schema.parameters[key].default`, or `schema.defaults()` |
| What range/choices are legal? | `.minimum`, `.maximum`, `.choices`, or `.describe_domain()` for a ready-made label |
| What presets exist? | `schema.preset_names()`, `schema.presets[name].description`/`.values` |
| What are the fully resolved values? | `resolve_parameters(schema, preset=..., overrides=...)` |

`ParameterDeclaration.description` supplies tooltip text and
`describe_domain()` a user-presentable domain string, so Phase E need not
re-derive either. `declaration_order()` exists specifically so a generated
form and the manifest always agree.

Phase E must call the same `resolve_parameters`; it must not re-implement
coercion.

---

## M. Validation

| Gate | Result |
|---|---|
| `python -m pytest` (full) | **3230 passed, 14 skipped, 3 deselected, 0 failed, 0 errors** |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues found in 107 source files |
| `mypy client/src/battle_client` | Success: no issues found in 16 source files |
| `test_v4_stable_ruleset_equivalence.py` | Passed — no golden was changed |
| `test_v5_alpha1_phase_b_engine_hygiene.py` | Passed |
| `test_v5_starter_agents.py` (Phase C suite) | Passed |
| `test_v5_agent_parameters.py` (new, Phase D) | Passed |
| Focused gate group (equivalence + B + C + D) | 209 passed |
| End-to-end CLI smoke | `--a-preset vigilant --b-param attacker_reach=32` resolved, delivered and recorded in `result.json` |

One flake was observed and is reported rather than hidden: on the first full
run, `test_agent_evaluation_v4.py::test_worker_count_does_not_change_schedule_or_outcome`
failed with `PermissionError: [WinError 5]` on an atomic `os.replace` inside
`.pytest-tmp` — a Windows file-lock condition in a test that touches nothing
this phase changed. It passed on re-run in isolation (31 passed) and in a
clean full re-run (3230 passed, 0 failed). The counts reported above are
from the clean full run.

### New test coverage

`engine/tests/test_v5_agent_parameters.py` (121 tests) covers schema parsing
and every rejection case; presets and their rejections; the resolution
precedence rule and its deterministic ordering; the full coercion table
including the boolean vocabulary and its refusals; the unknown-key policy
for both schema-driven and legacy agents; runtime delivery proved from a
replay/trace rather than asserted; identity participation; artifact
recording; the CLI flags end to end through real matches; Agent API v1
compatibility; per-starter declarations, defaults, presets, Phase C digest
equivalence, non-default behavioural effect, legality and determinism under
a preset; and that all six `v4_*` starters declare no schema.

Rejections are asserted through the parser on real on-disk manifests rather
than by matching source strings.

---

## N. Limitations and deferred work

1. **Phase E is not started.** No Designer widgets, sliders, combo boxes,
   preset selectors, Randomize Seed button, layout changes, replay-history
   browser or replay scaling work exists. **No Designer file was modified at
   all** — none was needed, because the existing
   `$BYTEFRAY_AGENT_*_PARAMS_JSON` export is the override layer the new
   resolver already consumes.
2. **Existing installations keep their pre-Phase-D starter copies.**
   `ensure_starter_agents` is deliberately non-destructive (copy-if-missing,
   `open("xb")`), which protects user edits. Verified on this machine: the
   installed catalog at `C:\ProgramData\Bytefray` still holds
   `v5_core_defender` version `1.0.0` with no schema, and `--a-preset
   vigilant` against it correctly reports *"this agent declares no
   'parameters' section"*. A fresh data root installs `1.1.0` and works.
   Existing users must delete the agent directory to pick up the new
   manifest. This is pre-existing product behaviour, not a Phase D
   regression, but Phase E's Designer will show no parameters for those
   installs — a starter-refresh policy is worth deciding before Alpha 1
   ships.
3. **Parameters are Agent API v2 only.** API v1 agents and VM/blob agents
   keep their historical paths untouched. VM `defaults:` remains
   preview-only, exactly as before; wiring it into `build_agent` would
   change existing VM agent behaviour and was out of scope.
4. **Starter versions moved `1.0.0` → `1.1.0`.** The source changed, so
   `source_sha256` — and therefore `match_id` — changes for these four
   agents regardless of the version field; the bump is the honest signal
   rather than an additional break. Gameplay behaviour at defaults is
   unchanged, as measured in §I.
5. **`MatchContextV2` is no longer hashable**, because it now holds a
   mapping. Nothing in the product or test suite hashes it (full suite
   clean), but it is a real, if theoretical, contract narrowing.
6. No new ruleset, no gameplay-mechanic change, and no R1/R2 reintroduction.

---

## O. Repository health

Checked after all edits, tests and processes completed.

| Check | Result |
|---|---|
| `git --no-optional-locks status --short` | 26 modified, 3 untracked (listed in §P) |
| `git --no-optional-locks diff --check` | Clean, no output |
| `git --no-optional-locks diff --stat` | 26 files changed, 1553 insertions(+), 185 deletions(-) |
| `.git/index` | 92,243 bytes — unchanged from phase start |
| `.git/index.lock` | Absent |
| Git inspection | Succeeded throughout; every mid-phase check clean |
| Git mutation commands run | **None** |
| Background/detached processes launched | **None** |
| Task-created processes still running | **None** — every command terminated normally |
| Save/index conflicts, file-newer conflicts, index warnings, tool edit rejections | **None** |
| Product version | `5.0.0a1` — unchanged |
| R1/R2 production residue | Absent — zero matches for the R1/R2 ruleset ids, mortality or oracle symbols in `engine/src`, `client/src` or `app` |
| Existing `v4_*` agents modified | **NO** — zero `v4_` paths in the diff |
| Gameplay engine semantics changed | **NO** |

Git reports `CRLF will be replaced by LF` warnings on twelve files. These
are the repository's normal line-ending normalisation notices on Windows,
not errors.

---

## P. Files changed

**Added (3, untracked):**

```
engine/src/battle_engine/agent_parameters.py     the canonical parameter model
engine/tests/test_v5_agent_parameters.py         the Phase D test suite
docs/research/v5/V5_ALPHA1_PHASE_D_AUTHORING_AND_PARAMETERS.md   this report
```

**Modified (26):**

```
engine/src/battle_engine/agent_api.py            MatchContextV2.parameters
engine/src/battle_engine/agents.py               AgentSpec.parameter_schema
engine/src/battle_engine/agent_worker.py         supervised reset carries parameters
engine/src/battle_engine/process_runtime.py      delivery on both v2 paths
engine/src/battle_engine/match_service.py        MatchEntrant.parameters, identity, artifacts
engine/src/battle_engine/cli.py                  --*-param / --*-preset, resolution, preview

engine/src/battle_engine/data/starter_agents/v5_region_attacker/{agent.py,agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_scout_striker/{agent.py,agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_core_defender/{agent.py,agent.yaml}
engine/src/battle_engine/data/starter_agents/v5_dual_team/{agent.py,agent.yaml}
agents/v5_region_attacker/{agent.py,agent.yaml}          (byte-identical catalog copies)
agents/v5_scout_striker/{agent.py,agent.yaml}
agents/v5_core_defender/{agent.py,agent.yaml}
agents/v5_dual_team/{agent.py,agent.yaml}

docs/AGENT_API_V2.md                             rewritten as the authoring guide
docs/AGENT_AUTHORING.md                          manifest/schema reference
docs/V5_STARTER_AGENTS.md                        parameters per starter
engine/tests/test_v5_starter_agents.py           starter version literal 1.0.0 -> 1.1.0
```

**Deleted:** none.

---

## Q. Verdict

    PHASE D COMPLETE — READY FOR DESIGNER UX & REPLAY POLISH

Bytefray has one authoritative Agent API v2 authoring guide that teaches
objective-capable spatial play rather than API syntax alone. Parameter
schemas are optional, additive and backward compatible; declaration,
resolution, validation and delivery have a single coherent architecture with
one canonical resolver; presets are deterministic and schema-validated;
Phase E can query every piece of parameter metadata programmatically; the
four V5 starters are real, small, working examples; their default behaviour
is measurably identical to Phase C across 24 deterministic matches; the six
`v4_*` agents are untouched; stable `bytefray-rules-4` behaviour is
unchanged; artifact reproducibility is sound with no schema bump; the
version remains `5.0.0a1`; and tests, lint and types are clean.

No Phase E work was begun.
