# Bytefray V5 Post-Release Hardening H1 — Parameter Resolution & Supervised Runtime Consistency

**Status:** Remediation Complete
**Target:** Bytefray V5 Alpha 1 (`5.0.0a1`)
**Starting Branch/SHA:** `v5-research` @ `77b68565ea8b264b5dccc9f94085aa82997cd102`
**Date:** 2026-09-10
**Discipline:** Independently-verified remediation of two findings from
`docs/research/v5/V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md` (FIND-01,
FIND-02). Per that audit's own documented history (Section I), a prior
audit's claims must be independently re-verified rather than trusted — this
task followed the same discipline against the audit itself.

---

## A. Baseline and isolation

| Item | Value |
|---|---|
| Starting SHA | `77b68565ea8b264b5dccc9f94085aa82997cd102` |
| Branch | `v5-research` |
| Product version | `5.0.0a1` (`pyproject.toml:10`), unchanged throughout |
| Primary checkout | `D:\Projects\BATTLE2` |
| Isolated worktree | `D:\Projects\BATTLE2-worktrees\v5-h1-param-consistency` on branch `h1-param-consistency-work`, created via `git worktree add ... -b h1-param-consistency-work v5-research` from the primary checkout, then entered as the session's working directory |
| Worktree HEAD at start | `77b68565ea8b264b5dccc9f94085aa82997cd102` (identical to `v5-research`) |
| Git index/lock health | `.git/index.lock` absent; `git status --short` clean at start |
| Isolated venv | `.venv/` created fresh inside the worktree (`python -m venv .venv`) and editable-installed (`pip install -e ".[dev,replay,designer]"`), so `battle_engine.__file__` resolves under the worktree, never the primary checkout |

The primary checkout's own `.venv/` was used only once, read-only, to
bootstrap the worktree's own venv (`.venv/Scripts/python.exe -m venv`); no
file inside `D:\Projects\BATTLE2` was written.

---

## B. FIND-01 reproduction (exact pre-fix behavior)

Reproduced directly against the shipped `v5_region_attacker` / `v5_scout_striker`
starters (real, non-empty schema defaults: `attacker_reach: 16`;
`contact_memory_ticks: 60, search_stride_divisor: 1`).

```
bytefray run resolved params A: {'attacker_reach': 16}
bytefray run resolved params B: {'contact_memory_ticks': 60, 'search_stride_divisor': 1}

tournament entrant A parameters: {}
tournament entrant B parameters: {}

agent_test entrant A parameters: {}          # _resolve_python_entrant + naive construction
agent_evaluation expected match_id: match_21f1b4cad6aaace026131708
RUN match_id:                       match_205ce1cb07143a77d080484a
EVAL MATCHES RUN: False
```

`cli.py::_resolve_entrant_parameters` (via `agent_parameters.resolve_parameters`)
resolved non-empty schema defaults; `tournament_cli._resolve_entrant`,
`agent_test._test_agent`/`_test_agents`, and `agent_evaluation`'s
`_expected_cell_match_id`/`_expected_group_cell_match_id` all constructed
`MatchEntrant` with no `parameters` argument, defaulting to `{}` — confirmed
for all three files named in the audit, plus a fourth internal call site in
`agent_test.py` (`_test_agents`, the multi-entrant group path) not named by
name but covered by the audit's characterization of the file.

**Independent falsification of the audit's own framing.** The audit's
empirical probe (Section F1) compared a raw `bytefray run` `match_id`
against a raw `bytefray tournament` `match_id` and attributed the entire
divergence to the parameter bug. That conflates two independent effects:
`bytefray run` identifies a Python entrant by its CLI slot label (`"A"`/`"B"`,
`cli.py:967-981`), while `bytefray tournament` identifies it by the agent's
own discovered name (`tournament_cli.py:108`, pre-fix, now `:129`) —
`canonical_match_id` hashes `entrant.agent_id` directly
(`match_service.py:1133`), so these two frontends' match IDs were never
going to be byte-identical, with or without the parameter fix. Isolating the
effect (holding `agent_id`/`name`/`start` constant, varying only whether
parameters are resolved) confirms the *real* defect precisely:

```
Tournament match_id WITH resolved schema defaults:      match_677e6d04beb9ebf23ad5b8ca
Tournament match_id if parameters were empty (pre-fix): match_3fac92c9d5605bcf50c6de84
```

`agent_test`/`agent_evaluation`, which *do* share `bytefray run`'s "A"/"B"
slot convention (`TESTED_AGENT_SLOT = "A"`, `OPPONENT_SLOT = "B"`), give the
genuine like-for-like identity-parity comparison, and that is where the fix
is verified byte-for-byte in Section I below.

---

## C. FIND-01 root cause

Every one of `tournament_cli.py`, `agent_test.py`, and `agent_evaluation.py`
constructed a Python `MatchEntrant` by calling `MatchEntrant.python(...)`
with no `parameters` argument, so the dataclass's own default
(`MappingProxyType({})`) applied. `bytefray run` (`cli.py`) was the only
frontend that ever called the canonical resolver
(`agent_parameters.resolve_parameters`, via `cli.py`'s own
`_resolve_entrant_parameters`) before constructing its entrants.

**An additional, independently-discovered sibling instance** (not named by
the audit): `tournament_service.TournamentService._placed_pair` — the
helper that re-places a scheduled pairing's two entrants from their own
per-match derived seed, for every Ruleset whose `core_placement` is
`"seeded"` — rebuilt a fresh `MatchEntrant` from the original's fields but
omitted `.parameters` from the reconstruction call. `core_placement="seeded"`
is not a rare or experimental setting: it is what `RULESET_V4_ALPHA2` *and*
the **permanent, default** `RULESET_V4` both declare
(`ruleset_policy.py:387-439`, copied verbatim from alpha2 for RC1's stable
promotion). Since an Agent API v2 roster with no explicit `--ruleset` flag
resolves to exactly this permanent V4 identity, **this sibling silently
discarded the tournament_cli fix for every real tournament match run under
the default configuration** — reproduced directly:

```
before _placed_pair: {'attacker_reach': 16} {'contact_memory_ticks': 60, 'search_stride_divisor': 1}
after _placed_pair (pre-fix):  {} {}
```

This satisfies the bar for inclusion (§8 of the task brief): directly
analogous (same defect shape — a fresh `MatchEntrant` constructed without
carrying `.parameters` forward), independently reproduced above, covered by
a focused regression test (Section L), and documented here explicitly.

---

## D. FIND-02 reproduction (exact pre-fix supervised behavior)

Reproduced with direct semantic evidence — what a real agent instance,
executing in a real worker subprocess, actually observed on
`context.parameters` inside its own `reset()` — rather than source
inspection alone. A minimal Agent API v2 probe agent's `reset()` wrote
`dict(context.parameters)` to a file; `SupervisedPythonEntrantController`
was constructed directly with a `MatchEntrant` carrying non-empty
parameters:

```
MatchEntrant.parameters (requested/resolved): {'probe_value': 999, 'inspections_per_tick': 0}
DELIVERED (context.parameters seen by agent.reset()):        {}
MATCH: False
```

**Reachability, independently established (not assumed from the audit's
framing).** `supported_python_api_versions` restricts every one of
`RULESET_V1`, `RULESET_V2` (permanent), and `RULESET_V3_ALPHA1` to API v1
only; every Ruleset that accepts API v2 (`RULESET_V4`, `_V4_ALPHA1`,
`_V4_ALPHA2`) is in `PROCESS_RULESET_IDS` and therefore always dispatches to
`process_runtime.ProcessMatchController` — whose own worker branch already
forwarded `parameters=entrant.parameters` correctly
(`process_runtime.py:462`, unmodified by this task). None of the three
product CLIs (`bytefray run`, `bytefray tournament`, `agents test`/
`evaluate`) expose a `--ruleset` choice outside that same five-identity set
(`{v1, v2, v4-alpha1, v4-alpha2, v4}`), confirmed by inspecting all three
parsers' `choices=[...]` lists — so **no CLI-exposed configuration can reach
`SupervisedPythonEntrantController` with a non-empty-parameter Agent API v2
entrant.** It *is* reachable through the underlying engine API
(`battle_engine.match_service.NativeMatchService`/`MatchRequest`, used
directly by embedders and by the test suite) via the two experimental,
non-CLI-exposed Rulesets `bytefray-rules-2-alpha1`/`-alpha11`
(`supported_python_api_versions=None`, i.e. unrestricted, and not in
`PROCESS_RULESET_IDS`) — verified: `resolve_ruleset_policy(alpha1).
supports_agent(kind="python", api_version=2) == True` and
`alpha1 not in PROCESS_RULESET_IDS`. So FIND-02 is real and reachable at the
engine-API layer today, though not through any currently shipped CLI
surface for a schema-enabled agent — a materially more precise severity
statement than the audit's "Agent Lab timeout execution" framing, which
implied a directly user-reachable GUI path.

**A further structural fact, discovered independently during regression-test
construction, worth recording precisely because it bounds what "supervised
parity" can mean for this specific class:** `SupervisedPythonEntrantController`'s
tick loop is an unmodified, Agent-API-v1-shaped loop — it never calls
`declare_processes()` and cannot execute an `ActionKindV2` action. An
attempt to run a declared-API-v2 agent's `act()` through it at all (even to
return a bare NOP) crashes the worker (`agent_worker_exited`). This is
**pre-existing and unrelated to FIND-02's specific scope** (forwarding
`entrant.parameters` into `handle.reset()`); it means this controller could
never have run real V5-starter gameplay even before this fix, and this
task's regression coverage for it is correctly scoped to the `reset()`/
parameter-delivery boundary rather than full multi-tick v2 gameplay (see
Section L).

---

## E. FIND-02 root cause

`supervised_runtime.SupervisedPythonEntrantController._initialize_entrant`
called `handle.reset(match_seed=..., api_version=..., arena_size=...,
tick_limit=..., action_budget=..., locality_reach=..., timeout=...)` with no
`parameters=` keyword. `AgentWorkerHandle.reset` (`agent_worker.py:216-250`)
already accepted and forwarded a `parameters` argument onto the wire
(`"parameters": dict(parameters or {})`), and the worker already rebuilt
`MatchContextV2.parameters` from it (`agent_worker.py:441`,
`MappingProxyType(dict(request.get("parameters") or {}))`) — both sides of
the wire were correct and already used by `process_runtime.py`'s own worker
branch; only this one caller never supplied the argument, so
`request.get("parameters")` was always `None` and the worker built `{}`.

Meanwhile `match_service.py:881-885` (`_build_process_result`) records
`entrant.parameters` into `result.json`'s entrant metadata whenever
non-empty — but that wiring exists **only** on the V4 process-result
builder path (Phase D's own documented scope, confirmed in
`V5_ALPHA1_PHASE_D_AUTHORING_AND_PARAMETERS.md` Section G: "recorded ... on
the v4 process result path"). `_run_python_match_traced`'s own result
construction (the path `SupervisedPythonEntrantController` feeds) was never
given this wiring for *any* agent, before or after Phase D. So the audit's
specific provenance concern ("result/provenance metadata records the
requested resolved values" while the agent got `{}`) does not actually
manifest on this exact controller: pre-fix, both the worker and this
path's own result metadata were silently empty (consistent, if wrong); the
fix corrects worker delivery, and this path's result metadata remains
unwired — a separate, narrower, pre-existing gap, not a provenance
*disagreement*, and out of scope for the "pass parameters into `reset()`"
ask (see Section L's provenance test, which instead confirms parity on the
path that *is* wired: the V4 process worker branch).

---

## F. Architecture decision

No new resolver, context type, or parameter model was introduced — exactly
as the task brief required. The fix adds one function,
`agent_parameters.resolve_entrant_parameters`, that factors out precisely
the two things `cli.py`'s own `_resolve_entrant_parameters` already did
inline: (1) the Agent-API-v2-only gate (`api_version != 2 -> {}`) and (2) a
call to the existing canonical `resolve_parameters`. This is not a second
resolver — it adds zero new precedence logic — it is the one missing
*canonical boundary* every entrant-construction site needed to share, so
that "no explicit overrides" resolves to schema defaults identically on
every frontend rather than to `{}` on three of them. `cli.py` itself was
left untouched (already correct, heavily tested, and its CLI-specific
diagnostics — `SystemExit` messages, "Agent {letter}: ..." warnings — have
no equivalent need in the other three frontends, none of which expose a
per-entrant override/preset flag at all).

For FIND-02, the fix is the minimal one line the audit itself recommended:
forward the value the caller already had (`entrant.parameters`) into the
one call that was missing it, mirroring `process_runtime.py`'s own
already-correct call verbatim.

---

## G. Fix — exact source changes

| File | Change |
|---|---|
| `engine/src/battle_engine/agent_parameters.py` | Added `resolve_entrant_parameters(*, api_version, schema=EMPTY_PARAMETER_SCHEMA, legacy_defaults=None, preset=None, overrides=None, path=None) -> dict[str, Any]`: the API-v2 gate + a call to the existing `resolve_parameters`. Added to `__all__`. |
| `engine/src/battle_engine/tournament_cli.py` | `_resolve_entrant`'s python branch now resolves parameters via `resolve_entrant_parameters` (defaults only — no override/preset surface exists here) and passes them to `MatchEntrant.python(...)`; `AgentValidationError` is converted to `TournamentConfigurationError`, matching this file's existing error convention. |
| `engine/src/battle_engine/agent_test.py` | New private helper `_resolve_default_parameters(spec, *, role)` (defaults-only resolution + `AgentValidationError` -> `AgentTestError` conversion, matching `_resolve_python_entrant`'s adjacent style). Applied to both `MatchEntrant.python(...)` calls in `_test_agent` (tested agent and opponent) and to every seat's construction in `_test_agents` (the multi-entrant group path). |
| `engine/src/battle_engine/agent_evaluation.py` | Imports and reuses `agent_test._resolve_default_parameters` (not a re-derivation) in `_expected_cell_match_id` and `_expected_group_cell_match_id`, so these identity-mirror helpers stay in exact lockstep with what `agent_test`'s real executor now resolves. |
| `engine/src/battle_engine/tournament_service.py` | `TournamentService._placed_pair` now carries `first.parameters`/`second.parameters` forward into the re-placed `MatchEntrant` construction (sibling fix, Section C). |
| `engine/src/battle_engine/supervised_runtime.py` | `_initialize_entrant`'s `handle.reset(...)` call now passes `parameters=entrant.parameters`. |
| `engine/tests/test_v5_post_release_h1_parameter_consistency.py` | New. 19 tests (Section L). |

No change to `agent_parameters.py`'s existing `resolve_parameters`, no
change to `agent.yaml` schema, no change to `MatchContextV2`, no change to
`MatchEntrant`'s field shape, no change to `canonical_match_id`'s hashing
rule.

---

## H. Related-path audit

### `MatchEntrant(...)`/`MatchEntrant.python(...)` construction sites (`engine/src`)

| Site | Classification |
|---|---|
| `cli.py:967-981` (`bytefray run`) | Correctly resolved (pre-existing; unchanged) |
| `tournament_cli.py:129` (`_resolve_entrant`) | **Fixed** (FIND-01) |
| `tournament_cli.py:131/133` (blob/built-in branches) | Irrelevant — VM/blob entrants have no Agent API v2 parameter concept |
| `tournament_service.py:450/466` (`_placed_pair`) | **Fixed** (FIND-01 sibling, Section C) |
| `agent_test.py:482/489` (`_test_agent`) | **Fixed** (FIND-01) |
| `agent_test.py:788` (`_test_agents`, multi-entrant) | **Fixed** (FIND-01) |
| `agent_evaluation.py:1074/1081` (`_expected_cell_match_id`) | **Fixed** (FIND-01, identity-mirror helper) |
| `agent_evaluation.py:1137` (`_expected_group_cell_match_id`) | **Fixed** (FIND-01, identity-mirror helper) |

Live evaluation-cell execution itself constructs no `MatchEntrant` of its
own — `agent_evaluation.py`'s module docstring states it executes only via
`agent_test.test_agent`/`test_agents`, verified by inspection — so fixing
`agent_test.py` was sufficient for real cell execution; the two
`agent_evaluation.py` sites are resume-verification mirrors only, and both
needed the identical fix to stay in sync (Section C explains why leaving
them stale would have newly broken resume verification).

### Worker `reset(...)` call sites (`engine/src`)

| Site | Classification |
|---|---|
| `process_runtime.py:388` (in-process `instance.reset(context)`) | Correctly resolved (pre-existing; unchanged) |
| `process_runtime.py:455-463` (`handle.reset(...)`, V4 worker branch) | Correctly resolved (pre-existing; unchanged) |
| `supervised_runtime.py:284-292` (`handle.reset(...)`) | **Fixed** (FIND-02) |
| `agent_validation.py:518` (`_validate_agent_supervised`) | Irrelevant — a fixed-seed, single-`act()` manifest/contract dry-run with no entrant or resolved-parameter concept at all; its unsupervised sibling (`build_validation_context`, `agent_validation.py:105-131`) also never sets `parameters`, so both sides already agree (both empty, by design — the same generic sanity check for every agent regardless of declared schema) |
| `agent_worker.py:454` (`state.loaded.instance.reset(context)`) | Irrelevant — the worker's own internal dispatch to the loaded agent instance, downstream of the fix, not a construction site |
| `python_runtime.py:1275` (v1 `instance.reset(context)`) | Irrelevant — Agent API v1 has no `parameters` field on `MatchContext` at all |

No other sibling omission was found.

### Tournament-level identity, audited but intentionally left unchanged

`tournament_service._entrant_identity` (feeds `tournament_id`, the
resume-grouping key at `state_path`, distinct from each match's own
`canonical_match_id`) does not include `.parameters`. Per-match resume
verification is unaffected — it already compares each match's own
`canonical_match_id`, which does carry parameters — so this is a narrower
grouping-key granularity question, not a correctness defect, and changing
`tournament_id`'s hash payload would be a breaking identity change for
every historical `tournament.json` unrelated to what FIND-01 asked for.
Documented here as an audited, deliberately-deferred observation, not
fixed.

---

## I. Identity/provenance result: before vs. after

| Question | Before | After |
|---|---|---|
| Tournament entrant parameters for a schema-enabled agent, no override | `{}` | Schema defaults (e.g. `{"attacker_reach": 16}`) |
| Tournament's own `canonical_match_id` sensitivity to resolved parameters | None (always hashed `{}`) | Sensitive — verified two otherwise-identical requests differing only by resolved-vs-empty parameters produce different `match_id`s |
| `agents test` / `agents evaluate` entrant parameters | `{}` | Schema defaults, identically on every seat |
| `agent_test` vs. bare `bytefray run`, same agent/seed/starts (same "A"/"B" identity convention) | Not compared by pre-fix behavior (both empty, coincidentally equal) | **Byte-identical `canonical_match_id`**, verified directly against a real match run |
| `agent_evaluation`'s resume `_expected_cell_match_id` vs. a real `agent_test` run | Diverged (mirror was as stale as the executor, but a real V5-starter cell would have gone through the executor's now-fixed defaults, producing a mismatch) | **Byte-identical**, verified directly |
| `bytefray run` vs. `bytefray tournament`, raw `match_id` | Differ (parameters *and* agent-id convention) | Still differ — by design, solely due to the pre-existing, legitimate agent-id-as-name vs. slot-label convention difference (Section B); this was never a valid identity-parity target |

---

## J. Runtime parity: direct vs. supervised

Real-starter behavioral evidence (`v5_core_defender`, `inspections_per_tick`
governs whether the agent ever issues a `READ` action — Phase D §J),
counted from the actual per-tick decision trace, 15 ticks, seed 42, via
`process_runtime.ProcessMatchController`'s two branches (the branch that is
actually reachable for a schema-enabled agent — see Section D):

| Configuration | READ actions (agent A) |
|---|---|
| Direct (in-process), `inspections_per_tick=4` (default) | 58 |
| Direct (in-process), `inspections_per_tick=0` (override) | 0 |
| Supervised (worker, `agent_call_timeout=10.0`), default | **58** |
| Supervised (worker), override | **0** |

Direct and supervised are byte-identical in both configurations.

At the exact code boundary FIND-02 named
(`SupervisedPythonEntrantController.handle.reset(...)`), direct semantic
proof (Section D) shows the requested/resolved `MatchEntrant.parameters`
now equal what the agent's own `reset()` observes on
`MatchContextV2.parameters`, for both schema defaults and an explicit
override with an extra unrecognized key (`{"inspections_per_tick": 0,
"extra": "value"}` delivered verbatim) — the wire is untyped/tolerant by
design (Phase D), so this is expected and correct.

---

## K. Legacy compatibility

* Agent API v1 agents: `resolve_entrant_parameters` returns `{}`
  unconditionally regardless of `overrides`/`legacy_defaults` whenever
  `api_version != 2` — regression-locked directly
  (`test_non_v2_agent_never_receives_resolved_parameters`, parametrized over
  `1`, `None`, `3`).
* Schema-less Agent API v2 agents (all six `v4_*` starters): fall back to
  the pre-Phase-D free-form `legacy_defaults`/`overrides` passthrough,
  unvalidated, unknown keys allowed — regression-locked directly
  (`test_schemaless_v2_agent_falls_back_to_legacy_defaults_and_overrides`)
  and via `test_schemaless_v4_starter_still_resolves_empty` (tournament,
  real `v4_local_defender`, confirms `{}` — unaffected, since it declares no
  `parameters` section and no legacy `defaults:`).
* `engine/tests/test_ruleset_v1_equivalence.py` and
  `engine/tests/test_default_python_agents.py` (47 tests): 47 passed, 0
  failed, 0 errors.
* No `v4_*` starter source was modified; no `agents/v4_*` catalog file
  appears in `git diff --stat`.

---

## L. Regression coverage

New file: `engine/tests/test_v5_post_release_h1_parameter_consistency.py`
(19 tests).

| Test | User-visible failure it catches |
|---|---|
| `TestResolveEntrantParametersContract` (5 tests) | The new canonical boundary itself regressing: wrong precedence, wrong v1/v2 gate, wrong schema-less fallback |
| `TestTournamentEntrantResolution::test_resolves_schema_defaults_like_bytefray_run` | A schema-enabled tournament entrant silently going back to `{}` |
| `...::test_schemaless_v4_starter_still_resolves_empty` | A `v4_*` starter (or any schema-less agent) starting to receive spurious parameters/identity drift in tournaments |
| `...::test_tournament_own_identity_is_now_sensitive_to_resolved_parameters` | Tournament identity silently going blind to parameters again |
| `...::test_seeded_placement_reassignment_preserves_resolved_parameters` | The `_placed_pair` sibling regressing under the *default* Ruleset — the highest-impact single test in this suite, since it covers the common case |
| `TestAgentTestEntrantResolution` (3 tests) | `agents test` (single or multi-entrant) delivering `{}` again, or diverging from a real bare `bytefray run`'s `canonical_match_id` |
| `TestAgentEvaluationExpectedMatchIdMirrorsAgentTest` | The resume-verification mirror drifting from the real executor — the exact failure mode that would manufacture false `resumed_result_mismatch` corruption for every schema-enabled evaluation cell |
| `TestSupervisedRuntimeParameterForwarding` (4 tests) | `SupervisedPythonEntrantController` silently dropping schema-default or explicit-override parameters again (direct semantic proof at the worker boundary); the real-starter direct-vs-supervised behavioral divergence (Section J); provenance/delivery agreement on the actually-reachable V4 worker path |

Also exercised (unchanged, confirming no regression): `test_v5_agent_parameters.py`,
`test_v5_starter_agents.py`, `test_v5_alpha1_phase_e_starter_refresh.py`,
`test_v5_alpha1_phase_e_designer_services.py`, `test_supervised_runtime.py`,
`test_agent_test.py`, `test_agent_evaluation.py`,
`test_agent_evaluation_multi_entrant.py`, `test_tournament_service.py`,
`test_tournament_btctl.py`.

---

## M. Validation

| Gate | Result |
|---|---|
| Focused suite (parameter/starter/supervised/evaluation/tournament modules + new H1 file) | **418 tests, 0 failed, 0 errors, 0 skipped** |
| Full `python -m pytest` | **3395 tests, 0 failed, 0 errors, 23 skipped** |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues found in 107 source files |
| `mypy client/src/battle_client` | Success: no issues found in 16 source files |
| `test_v4_stable_ruleset_equivalence.py` + `test_v5_alpha1_phase_b_engine_hygiene.py` (R1/R2) + `test_v5_starter_agents.py` | 85 tests, 0 failed, 0 errors |
| API v1 / legacy compatibility (`test_ruleset_v1_equivalence.py`, `test_default_python_agents.py`) | 47 tests, 0 failed, 0 errors |
| GUI suite (`-m gui`, offscreen) | 3 tests, 0 failed — far fewer than Phase E's 338, because this Windows environment has no configured offscreen X11 display; per pytest.ini's own note, display-backed GUI tests are exercised by a dedicated Linux/X11 workflow, not this host. Not claimed as a GUI qualification. |
| Linux/WSL focused subset | **Not run.** WSL access from this session was blocked by the harness's worktree-isolation guard (WSL could reach the primary checkout's filesystem directly, bypassing isolation). Not claimed. |

No flakes were observed on any run.

---

## N. Independent falsification

Explicitly attempted and their outcome:

1. **"Tournament still bypasses defaults somewhere."** Found true, once:
   the `_placed_pair` sibling (Section C) — discovered by an exhaustive
   grep-and-classify audit of every `MatchEntrant(...)` construction site
   in `engine/src`, not by re-reading the audit. Fixed and regression-locked.
2. **"Evaluation/test helpers still diverge."** Found true for the
   *identity-mirror* helpers specifically (they would have newly diverged
   from the real, now-fixed executor had they been left alone) — fixed by
   reusing `agent_test`'s own helper rather than re-deriving the logic, and
   verified byte-identical against a real run.
3. **"Supervised runtime still drops parameters under another worker
   path."** Checked every `handle.reset(...)` call site in `engine/src`
   (Section H); no second omission exists.
4. **"Provenance can disagree with execution."** Checked specifically for
   the path FIND-02 named; found that this path's provenance recording was
   never wired at all (pre-existing, both-sides-empty before the fix, Section
   E) rather than a disagreement, and separately confirmed provenance
   *does* agree with execution on the path that is actually reachable in
   production (Section L/M, V4 worker branch test).
5. **"Legacy agents regress."** 47/47 passed; the new resolver's contract
   is directly regression-locked for `api_version` `1`/`None`/`3` and for
   schema-less v2 agents.
6. **"Defaults-only canonical identity changed unexpectedly."** Not for
   `bytefray run` itself (untouched) or for `agents test`/`evaluate`
   (verified byte-identical to `bytefray run` post-fix). Tournament's *own*
   identity did change for schema-enabled agents — correctly and
   deliberately, since it was previously blind to a genuinely
   gameplay-relevant input; this is the fix working, not a regression (no
   VM or schema-less agent's tournament identity is affected — parameters
   stay `{}` for those, so their `canonical_match_id` hash payload is
   unaffected, matching the same "gated on non-empty" discipline
   `canonical_match_id` already uses).
7. **Audit's own match-ID-divergence attribution**, checked against source
   rather than accepted: found to conflate the parameter bug with a
   separate, pre-existing, legitimate agent-id-convention difference
   between `bytefray run` and `bytefray tournament` (Section B) — corrected
   in this report rather than carried forward uncritically.
8. **`SupervisedPythonEntrantController`'s real v2-gameplay capability**,
   checked rather than assumed reachable exactly as the audit implied:
   found it cannot execute any `ActionKindV2` action at all (crashes the
   worker) and never calls `declare_processes()` — a pre-existing structural
   fact bounding what "supervised parity" can mean for this specific class,
   documented in Section D/J rather than silently worked around.

No initially-suspected HIGH/MEDIUM conclusion failed to survive this pass;
two additional, narrower findings (the `_placed_pair` sibling, and the
resume-mirror drift risk) were newly surfaced and fixed as a direct result
of it.

---

## O. Deferred finding

FIND-03 (interrupted starter refresh can leave a hybrid directory
permanently classified as customized, `starters.py::_mirror_bundled`)
remains **deferred**, per the task's explicit scope boundary. No file under
`engine/src/battle_engine/starters.py`'s refresh implementation was
touched.

---

## P. Verdict

    H1 REMEDIATION COMPLETE — PARAMETER EXECUTION CONSISTENCY RESTORED
