# Bytefray V5 Alpha 1 — Phase E: Starter Refresh, Designer UX, Seed Controls & Targeted Replay Polish

**Status:** Phase E Implementation & Qualification Record
**Branch:** `v5-research`
**Starting HEAD:** `3095b3dd9d5e0e64cb284cdefe103505aa284c93` (`feat(v5): add agent parameter schemas and authoring guidance`)
**Project Version:** `5.0.0a1` (unchanged)
**Stable Gameplay Ruleset:** `bytefray-rules-4` (unchanged)

---

## A. Starting baseline

| Precondition | Observed | Required |
|---|---|---|
| Branch | `v5-research` | `v5-research` |
| HEAD | `3095b3dd9d5e0e64cb284cdefe103505aa284c93` | — |
| `HEAD == origin/v5-research` | Yes (both `3095b3d`) | Yes |
| Working tree | Clean (`git status --short` empty) | Clean |
| `git diff --check` | Clean, no output | Clean |
| `.git/index.lock` | Absent | Absent |
| `.git/index` | 92,587 bytes, `Sep 9 08:04:44` | Healthy |
| Phase D commit present | Yes (`3095b3d`, HEAD itself) | Yes |
| Project version | `5.0.0a1` (`pyproject.toml:10`) | `5.0.0a1` |

---

## B. The existing-install starter problem, exactly as it was

`ensure_starter_agents` copied each bundled starter file with `open("xb")` —
exclusive create. A file already in the catalog was skipped, forever. There
was no version comparison, no content comparison and no upgrade path of any
kind: **an installed starter was never updated, only ever completed.**

That was a deliberate and correct protection for user edits. It was also the
only policy, so it applied equally to a copy nobody had ever touched.

The consequence Phase D recorded and Phase E had to fix:

> A fresh installation gets `v5_region_attacker` **1.1.0** with a `parameters`
> section. An installation created during Phase C keeps **1.0.0**, which has
> none — permanently. Phase E's Designer would generate no controls for it,
> and the user would have no way to tell that from the feature not existing.

Verified on this machine before any change: the real catalog at
`C:\ProgramData\Bytefray\agents` held all four `v5_*` starters at version
`1.0.0` with no schema.

Three further facts came out of the audit and shaped the design.

**1. The installer never touches starters.** `tools/installer.iss` creates
`{DataRoot}\agents` and sets `BYTEFRAY_ROOT`; the catalog is populated at
first run by `ensure_starter_agents`, called from `cli.py` (two sites),
`tournament_cli.py` and `AgentDesigner.__init__`. Upgrading the installed
product therefore could not refresh a starter even in principle.

**2. Bundled bytes are not platform-stable.** `.gitattributes` stores `.py`
as LF; this machine has `core.autocrlf=true`, so the working tree holds CRLF.
Both are the same release. Any byte-exact fingerprint would classify a Windows
install as modified. Measured: all 21 bundled starters fingerprint identically
LF vs CRLF under the normalizing digest, and would not have byte-for-byte.

**3. `__pycache__` leaked into user catalogs.** `_validate_starter` enumerated
`rglob("*")`, so a source-checkout run copied `v4_*/__pycache__/*.pyc` into the
catalog — five stale `.pyc` files. `pyproject.toml`'s `exclude-package-data`
already keeps bytecode out of the wheel, so a dev-tree install and a wheel
install of one release genuinely differed. Fixed as part of E0; the runtime
copy now matches the packaging boundary.

---

## C. Starter refresh policy

### The distinguishing evidence

One content digest per starter directory, `starter_content_digest`:

* versioned (`STARTER_CONTENT_DIGEST_VERSION = 1`), the same discipline
  `agent_api.LOCAL_SOURCE_FINGERPRINT_VERSION` already uses;
* every file the starter ships, including `agent.yaml` — the point, since
  Phase D changed manifests, not just implementations;
* ordered by POSIX relative path, so it is stable across platforms;
* `__pycache__` excluded, so a starter that has *run* is not thereby modified;
* symlinks resolving outside the directory skipped, matching
  `local_source_fingerprint`'s containment rule;
* text content normalized to LF before hashing (§B fact 2). Two files
  differing only in line endings are deliberately equal: whoever converted
  them changed no agent behaviour.

`SUPERSEDED_STARTER_DIGESTS` maps a starter name to the digests of bundled
releases this repository has superseded. **It is an allowlist for automatic
upgrades, and absence is the safe answer.** Content that is neither current
nor a recorded past release can only ever be preserved — which is why the
`v4_*` and v0.6.1 starters need no entries at all.

`CURRENT_STARTER_DIGESTS` pins what each starter ships today, so changing one
is deliberate: `test_current_bundled_content_matches_its_pinned_digest` fails
with a message naming the old and new digests and telling the author to carry
the old one into the allowlist first.

### Why not the alternatives

| Considered | Rejected because |
|---|---|
| Install receipt written at install time | Existing installations — the entire problem — have no receipt. A receipt would still need this registry to bootstrap, so it is pure addition. |
| Version-field comparison alone | A user who edits an agent without touching its `version` would be silently overwritten. Version says what the author intended, not what the bytes are. |
| Byte-exact comparison | Classifies every Windows install as modified (§B fact 2). |
| A migration database | Explicitly warned against by the phase brief, and unnecessary: the answer is a constant in one module. |

### The four outcomes

| Installed state | Action | Result field |
|---|---|---|
| **Absent** | install current bundled version | `installed` (per file) |
| **Digest == current bundled** | nothing written at all | — |
| **Digest ∈ superseded allowlist** | mirror current bundled content exactly | `refreshed` |
| **Anything else** | preserve; restore only *missing* files | `customized` |

Two details worth stating.

**The digest is computed before anything is written.** Restoring a missing
file would change the very content being classified.

**The customized path keeps the pre-Phase-E contract verbatim.** It still runs
copy-if-missing, so a user who deleted `agent.py` still gets it back — that
overwrites nothing, and a starter missing its implementation is simply broken.
The only behaviour that changed for a modified starter is that it is now
*reported*.

**Refresh mirrors rather than merges.** A recognised pristine copy contains
only files from that release, so removing one a newer release dropped is
correct; an upgraded install and a fresh one are then the same agent. Files
whose bytes already match are left untouched, so a one-file refresh does not
churn the rest.

### Telling the user

`describe_starter_refresh()` returns `None` when there is nothing to say.
Otherwise it names what was updated, and — separately — which starters were
kept because they are edited, and that renaming or deleting one gets the
bundled version.

* `bytefray --list-agents` prints it as `NOTE:` on stderr. Deliberately not on
  `bytefray run`: a customized starter is a standing condition, so the hot
  path would repeat it forever, while listing agents is exactly where a user
  is asking what their catalog contains.
* The Agent Designer writes it into the Advanced engine log once the panels
  exist. Not a modal: an upgraded catalog is normal, and a dialog on every
  launch for a permanent condition is noise.

---

## D. Migration and refresh results

### On this machine's real installation (read-only inspection)

| Starter | Installed digest | Classification |
|---|---|---|
| `v5_region_attacker` | `f09d7fd5…` | **Pristine Phase C 1.0.0 → refreshes** |
| `v5_scout_striker` | `2324bbf1…` | **Pristine Phase C 1.0.0 → refreshes** |
| `v5_dual_team` | `2088e6b1…` | **Pristine Phase C 1.0.0 → refreshes** |
| `v5_core_defender` | `435c77e9…` | **Customized → preserved** |

The fourth is the policy working, not failing. Its `agent.py` differs from the
Phase C commit by a semantically equivalent refactor of the repair-queue
guard, and that exact content exists at **no commit in this repository** — it
is an uncommitted mid-Phase-C dev state that was installed at the time. It was
never a bundled release, so it is not in the allowlist, so it is preserved and
reported. Deleting that one directory is the documented way to take the
bundled version.

### Under test, on temporary data roots

| Case | Result |
|---|---|
| Fresh install | all 21 starters at their current digest; nothing reported as refreshed or customized |
| Untouched Phase C 1.0.0 (all four, reconstructed from Git) | all four → 1.1.0, byte-identical to bundled, schemas discoverable |
| Already current | zero files written; every `st_mtime_ns` unchanged |
| Edited old starter | edit verbatim, manifest still 1.0.0, reported as customized |
| Starter written from scratch by the user | preserved (never a bundled release) |
| Edited starter missing a file | file restored, edit untouched |
| `v4_*` historical starters, edited | never rewritten, never refreshed |
| Second run of any of the above | nothing written; a customized starter stays reported |

---

## E. Designer parameter architecture

```
agent.yaml  (parameters / presets)
      │  agents.py::_spec_from_dir -> parse_parameter_schema     [Phase D]
      ▼  AgentSpec.parameter_schema
AgentCatalog.list_agents -> AgentRow.parameter_schema            [Phase E, new field]
      ▼
app/services/designer_workflows.py       ← Qt-free, headlessly testable
      │  resolve_agent_parameters   -> agent_parameters.resolve_parameters
      │  parameter_launch_overrides -> the non-default subset
      │  validate_entrant_parameters-> resolve_parameters, as a gate
      ▼
app/widgets/agent_parameters.py::AgentParameterForm   ← renders answers only
      ▼  launch_overrides()
RunConfig.a_params / b_params / c_params
      ▼
BYTEFRAY_AGENT_{A,B,C}_PARAMS_JSON       ← the pre-existing export, unchanged
      ▼
cli.py::_resolve_entrant_parameters -> resolve_parameters -> MatchContextV2
```

**No second parameter system exists.** The Designer implements no coercion, no
bounds check and no precedence rule; every answer comes from Phase D's
`resolve_parameters`. `test_resolution_matches_the_canonical_resolver_exactly`
asserts that directly.

**No new plumbing.** Values travel on the environment variable the Designer
has exported since before Phase D and which the Phase D resolver already
consumes as its override layer. No new CLI flag, no `RunConfig` field, no
launcher change.

**Manifest inspection only** (§28). Discovering what an agent exposes reads
its parsed manifest. No agent code is imported or executed to populate a
control; the UI/runtime boundary is untouched.

### Only non-default values are sent

`parameter_launch_overrides` exports a value only when it differs from the
agent's declared default — the identical policy Advanced already applies to
scoring weights (`_weight_override`, Phase 5B), for the identical reason: a
run left at defaults produces a command byte-identical to a bare
`bytefray run`, and therefore the same match identity.

This is safe because the child CLI applies the *same* schema's defaults
underneath, reading the same manifest from the same installed directory. Both
properties are asserted:
`test_exported_overrides_reproduce_the_same_effective_values`, and end to end
in §M — a defaults-only Designer run and a bare invocation produce the same
`match_id`.

---

## F. Control mapping

| Declared type | Control | Constraints applied |
|---|---|---|
| `integer` | `QSpinBox` | `minimum`/`maximum` become the control's range |
| `number` | `QDoubleSpinBox`, 6 decimals | declared bounds; 6 decimals represents every shipped default and preset exactly |
| `boolean` | `QCheckBox` | — |
| `choice` | `QComboBox` | populated from `choices`, in declared order |
| `string` | `QLineEdit` | — |

Controls appear in `schema.declaration_order()`, so the form and the manifest
cannot disagree. Each control and its label carry a tooltip assembled from the
declaration's own `description`, `describe_domain()` and `default` — Phase D
supplies both helpers precisely so a generated form need not re-derive them.

A control is normally *incapable* of producing an invalid value, which is
better than rejecting one. Where a declared domain is wider than Qt can
express — an integer bound outside 32 bits — the control clamps and the
canonical resolver reports the shortfall, blocking launch. That path is
covered by `test_a_value_the_schema_rejects_blocks_the_run_button`.

---

## G. Preset UX and state model

The model, chosen so a user never has to reason about hidden state:

> **The controls are the effective values. A preset is a load action, not a
> layer.**

| Action | Behaviour |
|---|---|
| Select a preset | resolve `defaults < preset` and load the result into every control |
| Edit a field afterwards | ordinary edit; it differs from the default, so it is exported as an explicit override |
| Change preset while edited | replaces every value with the new preset's resolution — documented, and the only rule that stays predictable |
| **Reset to Defaults** | every control back to its declared default; preset selector back to `Agent defaults` |

The preset selector is hidden for an agent that declares none; **Reset stays
available for any schema agent**. Because there is no hidden layer, the
summary can state the truth in one sentence — "Using preset 'far_sighted' with
1 edited value" — instead of a name that conceals what it resolved to.

Selecting a preset never touches the agent's source or manifest: presets are
data, resolved per match.

---

## H. Validation UX

Two gates, both calling `resolve_parameters`, neither inventing a rule.

**Continuous, in the panel.** `AgentParameterForm.validation_error()` runs the
resolver over the current controls. The summary line becomes
`Cannot run: attacker_reach must be…` and `AdvancedPanel._update_run_enabled`
disables **Run**. The user sees the problem before reaching for the button.

**At launch, authoritatively.** `_emit_run` refuses to emit and shows the
resolver's own message. `AgentDesigner._on_advanced_run` additionally calls
`validate_entrant_parameters` for every resolved entrant, so a programmatic
`RunConfig` cannot start a subprocess either.

Messages are the engine's, e.g.:

```
Agent B: Parameter 'reach' (override): 2 is below the declared minimum 10.
Agent A: Unknown parameter 'nonsense'. This agent declares: 'mode', 'reach', 'share'.
```

Both derive from `AgentValidationError`, so no user input produces a
traceback on any surface.

Coverage: typed fields, presets, explicit overrides, unknown keys, and the
legacy free-form editor's own pre-existing JSON validation, which is
unchanged.

**Stale input cannot travel.** Exactly one surface per slot is authoritative,
so switching a slot from a legacy agent to a schema agent does not smuggle the
old JSON into a schema-validated match
(`test_stale_free_form_json_never_travels_with_a_schema_agent`).

---

## I. Randomize Seed

`designer_workflows.random_match_seed(minimum=1, maximum=1_000_000)`.

* **Explicit only.** Nothing randomizes on its own. The generated value lands
  in the visible seed field and from that moment is an ordinary typed seed.
* **Never 0.** Advanced reads 0 as "use the engine's own default seed", so
  generating 0 would mean the opposite of randomizing. The floor is the
  field's own minimum raised to 1.
* **Range is the field's.** The generated value is always one the user could
  have typed, and can type again.
* **`secrets`, not `random`.** Choosing a seed has no reproducibility
  requirement of its own, and drawing from the process-wide `random` module
  would perturb other consumers of that stream. This is unrelated to a match's
  deterministic `MatchContextV2.rng`, and the docstring says so.

Added in two places: Advanced's **Random Seed** row, and the Agent Lab test
panel's seed — the two single-seed match-configuration surfaces. Engine seed
semantics are untouched.

Reproducibility is proven end to end in §M: a randomized seed reaches the
match exactly, and rerunning with the displayed value reproduces the same
`match_id` and `result_id`.

---

## J. Ruleset synchronization

Two dead functions removed, narrowly, and nothing else.

**`ruleset_combo.sync_ruleset_choices`** — the named cleanup item. Zero
references anywhere: not in `app/`, not in tests, not in docs. Simple and
Advanced both drive the *opposite* direction (the Ruleset is the controlling
selector and the roster is filtered by it), and the three surfaces that do
synchronize a Ruleset combo call `sync_ruleset_choices_for_metadata` directly.

**`ruleset_options.best_designer_ruleset`** — no production caller; kept alive
only by its own tests, and actively wrong. It chose from the runtime kind
alone, and every Python-only Ruleset looks identical on that axis, so it
answered `bytefray-rules-2` for an Agent API v2 agent — a Ruleset that agent
cannot run under. Its own docstring described the trap. The two tests that
used it now assert the metadata-aware `best_designer_ruleset_for_agents` that
every Designer surface actually uses, including the v2 case the old helper got
wrong.

Verified unchanged: the offered set is exactly v2, v4, v4-alpha2, v4-alpha1,
v1; no R1/R2 identity appears; an Agent API v2 roster resolves to stable
`bytefray-rules-4`; and changing entrants cannot leave an incompatible Ruleset
selected — asserted exhaustively over every Ruleset × every slot × every
offered agent in
`test_changing_entrants_cannot_leave_an_incompatible_ruleset_selected`.

---

## K. Replay polish — implemented and deferred

### Implemented: effective parameters in the results view

`EntrantResultPresentation` gained a `parameters` field, read defensively from
the entrant metadata Phase D already writes to `result.json`. Advanced's
Results table adds one row per entrant that actually had parameters. The
values a user chose before a run are now visible after it, in the same table
they read the outcome from.

**No schema change of any kind.** No replay bump, no result bump. A result
written before Phase D reads back with an empty mapping, and a malformed
`parameters` block is ignored rather than fatal — both asserted.

### Deferred: scaling and layout (§22A) — with evidence, not assumption

The audit found this work already done in an earlier phase, so there was
nothing to fix:

* `choose_initial_window_scale` picks an initial integer scale from a
  preferred viewport, capped by a display-safety bound;
* the window is created `RESIZABLE`; `_handle_window_resize` honours an
  ordinary OS resize without snapping, `_fit_to_display` and `_rescale`
  provide deliberate fit/zoom;
* `hud_layout.calculate_layout` recomputes responsive HUD/arena/footer
  geometry on configure and resize, never per frame;
* 199 tests already cover this (`client/tests/test_pygame_renderer.py` 118,
  `test_hud_layout.py` 81), all passing.

Inventing changes here would have been churn against working, well-covered
code.

### Deferred: replay-history browser and metadata search (§23)

Not started, as the phase brief directs. It is not small: it needs a scan of
the run tree, an index or filter model, a list UI and a selection contract.
Carried to the backlog (§Q).

---

## L. `MatchContextV2` hashability

**Audit result: no contract exists, no use exists. Recorded, no action** —
exactly the disposition §25 prescribes for that finding.

| Question | Answer |
|---|---|
| Does documentation promise hashability? | **No.** No Bytefray document mentions it. `docs/AGENT_API_V2.md:499` says the opposite — agents must "never depend on … `id()`/`hash()` of objects". |
| Do tests depend on hashing it? | **No.** Full suite clean, 3279 passed. |
| Does product or plugin code use it as a key or set member? | **No.** No occurrence in `engine/src`, `client/src` or `app`. |

Mechanism, for the record: `MatchContextV2` is a frozen dataclass, so `hash()`
hashes its field tuple. `parameters` is a `MappingProxyType`, which is
unhashable, so the context is unhashable even when it carries no parameters.
Before Phase D it was *incidentally* hashable because every field happened to
be — `random.Random` hashes by identity. Incidental, undocumented, unused.

Restoring it would mean a custom `__hash__`, a hashable parameter
representation, or dropping the field's immutability — machinery in service of
nothing. Not built.

---

## M. First-user workflows

Three journeys, executed against temporary data roots through the real product
path — the real installer, the real catalog, the real parameter form, the real
exported environment variable, and real `bytefray run` subprocesses. The
developer's own `BYTEFRAY_ROOT` was never written to. **39 checks, all
passed.**

### 1. Fresh user

| Step | Result |
|---|---|
| Starters install into an empty root | 39 files, no errors, nothing reported as refreshed/customized |
| Designer discovers `v5_region_attacker`'s schema | yes |
| Typed control generated with declared bounds | `QSpinBox`, range 10–64 |
| Presets listed | `Agent defaults`, `standard`, `far_sighted` |
| Select `far_sighted` | resolves to `{attacker_reach: 32}` through the canonical resolver |
| Exported to the match | `{attacker_reach: 32}` — only the non-default value |
| Summary shows the effective value | `far_sighted` **and** `attacker_reach=32` |
| Randomize Seed | `122812`, visible in the field, within range |
| Match runs | exit 0, replay written |
| Effective parameters recorded in `result.json` | `{"attacker_reach": 32}` |
| Randomized seed reached the match exactly | `122812` in `_reproducibility` |
| Results view reports the parameters used | `{attacker_reach: 32}` |
| Rerun with the displayed seed and settings | same `match_id` (`match_5e4d3b0906…`), same `result_id` |
| Defaults-only run vs. bare CLI invocation | **identical `match_id`** |
| Parameterized run vs. default run | different `match_id`, as it must be |

### 2. Upgraded user

Data root seeded with all four starters as Phase C (`69fc958`) actually
shipped them, read out of Git rather than hand-written.

| Step | Result |
|---|---|
| Before refresh | Designer can show no parameters at all |
| Refresh | all four upgrade; **zero** misclassified as customized |
| Version | `1.0.0` → `1.1.0` |
| Content | byte-identical to the bundled starter |
| After refresh | Designer exposes parameters **and** presets (`far_sighted`) |
| User informed | summary names the updated starters |
| Second refresh | nothing installed, refreshed or customized |
| Real parameterized match on the upgraded starter | exit 0 |

### 3. Customized user

| Step | Result |
|---|---|
| Edit `agent.py`, then refresh | edit survives **verbatim** |
| Classification | reported as customized, not refreshed |
| Manifest | still `1.0.0` — not replaced |
| Untouched sibling in the same root | upgraded normally to `1.1.0` |
| User informed | summary names it and says deleting it gets the bundled version |
| Designer | keeps the free-form surface, correctly |
| Match still runs | exit 0 |
| Repeated refresh | writes nothing; keeps reporting the standing condition |

---

## N. Compatibility

| Surface | Status |
|---|---|
| Agent API v1 agents in the Designer | Unchanged. Free-form params still exported and still ignored by `cli.py` with a warning. `validate_entrant_parameters` deliberately does not validate a non-v2 agent — the exact Phase D regression, guarded at the Designer boundary too. |
| VM/blob agents | Unchanged. Free-form editor, no validation, no schema. |
| Agent API v2 agents without a schema (all six `v4_*`) | Unchanged. Empty schema → free-form passthrough, as Phase D's resolver already specifies. The Designer is never stricter than the engine. |
| Legacy free-form JSON editor | Retained in full, per slot, with its existing validation and placeholder. |
| Third entrant (Agent C) | Full parity — generated controls, presets, validation and export, tested in slot C and mixed with legacy agents. |
| `AgentRow` construction | `parameter_schema` defaulted last; every positional construction in existing tests and callers is unaffected. |
| `StarterBootstrapResult` | `refreshed`/`customized` defaulted; every existing reader of `installed`/`errors` is unaffected. |
| Replay schema | **Not touched.** |
| Result schema | **Not touched.** Pre-Phase-D results still open, with empty parameters. |
| Gameplay engine | **Zero changes.** No edit to `process_runtime.py`, `rules.py`, `ruleset_policy.py`, `vm.py`, `scoring.py` or `scheduler.py`. |
| `v4_*` historical agents | **Untouched** — zero `v4_` paths in the diff. |
| Phase C starter behaviour | **Unchanged** — no starter source or manifest was edited this phase. |
| Product version | `5.0.0a1`. |

---

## O. Validation

| Gate | Result |
|---|---|
| `python -m pytest` (full headless) | **3279 passed, 14 skipped, 3 deselected, 0 failed, 0 errors** (324s) |
| GUI suite (`-m gui`, offscreen) | **338 passed, 0 failed** |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues found in 107 source files |
| `mypy client/src/battle_client` | Success: no issues found in 16 source files |
| `test_v4_stable_ruleset_equivalence.py` | Passed — no golden changed |
| `test_v5_alpha1_phase_b_engine_hygiene.py` | Passed — no R1/R2 residue |
| `test_v5_starter_agents.py` (Phase C) | Passed |
| `test_v5_agent_parameters.py` (Phase D) | Passed — including the Phase C gameplay-digest equivalence |
| Focused gate group (equivalence + B + C + D + E) | 314 passed |
| `client/tests` (replay/renderer) | 478 passed, 3 deselected |
| Headless dependency invariant | Core engine imports with `PySide6`/`pygame` blocked at `sys.meta_path`; **neither ever imported** |
| `bytefray --list-agents` on a fresh temporary root | exit 0, catalog listed |
| First-user workflows (§M) | 39/39 passed |

Phase D's baseline was 3230 passed; Phase E adds 49 tests and changes no
existing expectation except the two noted below.

**No flakes were observed.** The full suite ran clean on the first attempt.

### New test coverage

| Module | Tests | Covers |
|---|---|---|
| `engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` | 24 | the digest's properties; the pinned-digest maintenance gate; all four refresh outcomes; idempotence; `v4_*` immunity; bytecode exclusion; the reporting summary; the upgraded install proved through `discover_agents` |
| `engine/tests/test_v5_alpha1_phase_e_designer_services.py` | 25 | the catalog carrying parsed schemas; resolution equivalence with the canonical resolver; precedence; the non-default export rule and its round-trip; the launch gate; v1/VM/schema-less v2 compatibility; the shipped starters' presets; seed generation; result-presentation parameters and pre-Phase-D compatibility |
| `tests/test_v5_alpha1_phase_e_designer_ux.py` | 35 (gui) | type→control mapping; defaults, bounds, order, help text; presets, overrides, reset; validation blocking launch; legacy/mixed/three-slot behaviour; edits surviving a refilter; Randomize Seed; ruleset invariants; the results-table parameter row |

### Two existing tests changed, both correctly

* `test_starter_agents.py::_expected_starter_files` now enumerates through
  `starter_content_files`, so it excludes `__pycache__` — matching the
  packaging boundary and the installer's new behaviour. Without this it
  asserted that stale `.pyc` files *should* be copied into a user's catalog.
* `test_designer_ruleset_options.py` replaces its two `best_designer_ruleset`
  assertions with `best_designer_ruleset_for_agents` ones, covering the Agent
  API v2 case the removed helper answered wrongly.

---

## P. Repository health

Checked after all edits, tests and processes completed.

| Check | Result |
|---|---|
| `git --no-optional-locks status --short` | 14 modified, 4 untracked (listed in §R) |
| `git --no-optional-locks diff --check` | Clean, no output |
| `git --no-optional-locks diff --stat` | 14 files changed, 918 insertions(+), 71 deletions(-) |
| `.git/index` | 92,587 bytes — unchanged from phase start |
| `.git/index.lock` | Absent |
| Git inspection | Succeeded throughout; every mid-phase check clean |
| Git mutation commands run | **None** |
| Background/detached processes launched | **None** |
| Task-created processes still running | **None** — every command terminated normally |
| Save/index conflicts, tool edit rejections | **None** |
| Product version | `5.0.0a1` — unchanged |

Git reports the usual `CRLF will be replaced by LF` normalisation notices on
Windows. Those are notices, not errors.

---

## Q. Deferred backlog

1. **Replay-history browser and metadata search** — not started (§23). The
   backlog item stands as written: a scan of the run tree, an index/filter
   model, a list UI and a selection contract. Not small, and not required for
   Alpha 1.
2. **Replay high-DPI/scaling work** — deferred with evidence, not assumption
   (§K). The renderer is already responsive, resizable, display-capped and
   covered by 199 passing tests.
3. **`MatchContextV2` hashability** — audited, no contract and no use found;
   no action, by §25's own instruction (§L).
4. **VM `defaults:`** — still preview-only, as Phase D left it. Wiring it into
   `build_agent` would change existing VM agent behaviour.
5. **Starter refresh across future releases** — the allowlist mechanism is in
   place and enforced by a failing test, but only the Phase C 1.0.0 digests
   exist so far. Every future bundled-starter change must append its
   predecessor.
6. **A contextual "this starter is customized" note in the parameter panel** —
   the information is reported (log, `--list-agents`) but not shown at the
   moment a user wonders why an agent has no controls. Small, and deliberately
   not built inside this phase's scope.

---

## R. Files changed

**Added (4):**

```
app/widgets/agent_parameters.py                          schema-driven controls
engine/tests/test_v5_alpha1_phase_e_starter_refresh.py   E0 suite
engine/tests/test_v5_alpha1_phase_e_designer_services.py E1-E4 Qt-free suite
tests/test_v5_alpha1_phase_e_designer_ux.py              E1-E4 GUI suite
docs/research/v5/V5_ALPHA1_PHASE_E_DESIGNER_UX.md        this report
```

**Modified (14):**

```
engine/src/battle_engine/starters.py          content digest, allowlist, refresh policy
engine/src/battle_engine/cli.py               refresh NOTE on --list-agents
app/services/agent_catalog.py                 AgentRow.parameter_schema
app/services/designer_workflows.py            seed generation, parameter adapters,
                                              launch gate, result parameters
app/services/ruleset_options.py               removed dead best_designer_ruleset
app/widgets/ruleset_combo.py                  removed dead sync_ruleset_choices
app/views/advanced.py                         parameter surfaces, Randomize Seed,
                                              launch validation, results row
app/views/development.py                      Randomize Seed on the Agent Lab test
app/agent_designer.py                         refresh notice, launch parameter gate
engine/tests/test_starter_agents.py           __pycache__ exclusion
engine/tests/test_designer_ruleset_options.py metadata-aware chooser assertions
ARCHITECTURE.md                               starter lifecycle description
docs/V5_STARTER_AGENTS.md                     Designer parameter UX, upgrade policy
docs/specs/agent_designer_workflow.md         refresh reporting in Designer startup
```

**Deleted:** none.

---

## S. Verdict

    PHASE E COMPLETE — READY FOR ALPHA 1 QUALIFICATION & PACKAGING

An upgraded installation now receives current bundled starters when — and only
when — its copy is provably untouched, so the Phase D parameter schemas reach
existing users while an edited starter is preserved and the user is told why.
The refresh is deterministic, idempotent, platform-stable across the
CRLF/LF checkout difference, and fail-safe by construction: absence from the
allowlist can only ever preserve.

Schema-enabled agents render typed, bounded, documented controls with presets,
defaults and a reset, resolved exclusively by Phase D's canonical resolver;
invalid values block launch at both the panel and the launch site with the
engine's own diagnostics; legacy, Agent API v1, VM and schema-less v2 agents
keep exactly the surfaces they had. Randomize Seed is explicit, visible and
reproducible. Two genuinely dead ruleset helpers are gone, one of which
answered wrongly for Agent API v2. Replay polish is one small, schema-free
addition, with the scaling and history work deferred on evidence.

Stable `bytefray-rules-4` semantics, the `v4_*` agents, Phase C starter
behaviour, replay and result compatibility, and the headless core's freedom
from GUI dependencies are all intact. The version remains `5.0.0a1`, and
tests, lint and types are clean.

Phase F was not begun.
