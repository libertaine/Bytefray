# Bytefray V6 — Phase 2B.7: `bytefray-rules-3-alpha1` Disposition Research

**Phase type:** Research-only. No ruleset, registry, test, GUI/CLI choice,
persisted schema, package-validation rule, or other architecture was
modified. The only tracked change produced by this phase is this document.

**Governing question carried over from Phase 1** (`V6_PHASE1_REPOSITORY_DIET_AUDIT.md`
§4.3, its one unresolved ruleset item): whether `bytefray-rules-3-alpha1`'s
coupling boundary can be scoped precisely enough to certify that retiring it
from new execution is safe, and whether historical-artifact recognition can
survive that retirement without an executable registration.

---

## A. Executive conclusion

**Yes — V6 can stop creating new `bytefray-rules-3-alpha1` matches while
fully retaining the ability to read, index, filter, and display every
historical artifact created under it, with no compatibility shim required.**
This is not a close call: three independent evidence passes (implementation
trace, persisted-artifact/package trace, test/history trace), each citing
exact `file:line` source, converge on the same architecture without
contradiction.

The decisive structural fact, mirroring the pattern Phase 2B.5/2B.6 already
established for the (unrelated) Redcode/pMARS retirement:

> **Exactly one line of the executable registry gates all new execution:
> `bytefray-rules-3-alpha1`'s entry in `ruleset_policy._RULESET_POLICIES`
> (`engine/src/battle_engine/ruleset_policy.py:492`). Every read, replay,
> index, and display path for historical artifacts is architecturally
> independent of that registry and would not notice its removal.**

Three findings materially shape the disposition:

1. **New execution is already invisible everywhere except two low-level
   API paths.** No CLI (`bytefray run`, `tournament`, `agents test`,
   `agents evaluate`, `agents evaluation-presets`), no GUI/Designer surface,
   and no starter/reference/preset default has ever offered this identity —
   confirmed both from current source and from `git log -S` across the
   full history of every CLI's argparse table (zero commits ever added it).
   The only two ways to run a *new* match under it today are constructing a
   `MatchRequest`/`EvaluationRequest` directly in Python — reachable only by
   test code and one internal research driver,
   `tools/v3_phase2_locality_corpus.py`.
2. **Historical readability, replay rendering, and history-browser display
   never call the executable resolver at all.** `resolve_result_ruleset`/
   `resolve_replay_ruleset` treat `ruleset_id` as an opaque string;
   `battle_client`'s replay session/player never import `ruleset_policy` or
   the locality mechanic; the one engine dependency replay display has
   (`has_vulnerable_core`/`has_observable_core`/`core_addresses`) is a
   **separate, shared** pair of frozensets this phase's plan explicitly
   preserves.
3. **The locality mechanic itself is genuinely, almost entirely
   self-contained** — a 250-line block in `python_runtime.py` gated by a
   frozenset with exactly one member — but three small pieces of it
   (an enum's members, two optional dataclass fields, and two membership
   entries in *shared* frozensets) must be kept regardless of disposition,
   because they serve historical-artifact reading for this and other
   rulesets, not new execution.

**Recommendation (§N): RETIRE FROM NEW EXECUTION, KEEP READABILITY** (Model
B), with a scoped, dependency-complete implementation plan (§O) that a
future implementation phase can execute directly. **No Opus escalation was
required** (§R) — every one of the five §16 ambiguity criteria resolved
cleanly against source, with no genuine ambiguity remaining.

---

## B. Baseline

Established before any investigation began, per §1's checklist.

| Check | Result |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `c74d6c67faca36f6394cb0a258687a8774dc48b4` |
| Working tree | Clean (`git status --porcelain` empty) at phase start |
| Divergence from `origin/v6-research` | **0 ahead, 0 behind** (`git fetch` + `git rev-list --left-right --count`) |
| Phase 2B.6 committed and synchronized | **Yes** — two commits, `e4bc0b0` (full-file deletions) and `c74d6c6` (partial edits + report), both already on `origin/v6-research` before this phase began |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — untouched |
| Canonical test count (collected) | **3,713**, summed from `pytest --collect-only -q` across all 158 canonical files — **matches the Phase 2B.6 expected post-retirement baseline exactly** |
| Canonical test count (executed) | **3,693 passed, 20 skipped, 0 failed** — one transient `PermissionError: [WinError 5] Access is denied` on `os.replace` in `test_agent_evaluation_behavior.py::test_workers_1_and_workers_2_produce_identical_behavior_profile` (an atomic-write race, not a source defect) reproduced **clean in isolation** immediately afterward, exactly the same flake class Phase 2B.6's own report already documented for a different test on this machine |

No drift from the expected baseline; no explanation of a discrepancy is
needed. The repo-local `.pytest-tmp-phase2b7*` directories created for this
verification were deleted after the run; `git status --porcelain` is empty
again.

---

## C. Current ruleset inventory

`ruleset_policy._RULESET_POLICIES` (`ruleset_policy.py:487-496`) still
registers exactly the same **8 identities** Phase 0/Phase 1 recorded, plus
the one comparison-only alias — Phase 2B.6's Redcode/pMARS retirement did
not touch any ruleset (confirmed directly: `ruleset_policy.py` is not among
the 53 files that retirement changed, and its own §M explicitly says so:
"No ruleset is added, removed, renamed, or re-pointed by this retirement").

| Ruleset ID | Aliases | Impl. mapping | Policy mapping | CLI-selectable | GUI/Designer-selectable | Tests | Docs | Replay/result reader |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bytefray-rules-1` | `evaluation-rules-1` (comparison-only) | VM or Python, shared with nothing else | `RULESET_V1` | Yes, all 4 CLIs | Yes | Extensive | Current | Generic |
| `bytefray-rules-2` | — | Python-only, shared vulnerable/observable-core machinery | `RULESET_V2` | Yes, all 4 CLIs | Yes | Extensive | Current | Generic |
| `bytefray-rules-2-alpha1` | — | Shares v1's scheduler/termination, its own vulnerable-core membership | `RULESET_V2_ALPHA1` | **No** (excluded from every CLI `--ruleset choices=`) | No | Extensive (`test_ruleset_v2_alpha1.py` + 10 more) | Historical | Generic |
| `bytefray-rules-2-alpha11` | — | Same pattern, adds observable-core membership | `RULESET_V2_ALPHA11` | **No** | No | Extensive (`test_ruleset_v2_alpha11.py` + promotion-equivalence corpus) | Historical | Generic |
| `bytefray-rules-3-alpha1` | — | Shares v2's vulnerable/observable-core + scheduler/termination; **owns** the one-member `LOCALITY_RULESET_IDS` locality mechanic | `RULESET_V3_ALPHA1` | **No** (excluded from every CLI `--ruleset choices=`, including `agents evaluate`'s) | **No** (excluded from every `DesignerRulesetOption` tuple) | `test_v3_phase2_locality_{agents,evaluation,runtime}.py` (156 collected cases) + 3 more files (small overlap) | Historical (accurate, non-stale — §K) | Generic |
| `bytefray-rules-4-alpha1` | — | Shares v4's process runtime, own placement/selection fields | `RULESET_V4_ALPHA1` | Yes, all 4 CLIs | Yes | Extensive, incl. immutability pins | Current (historical-reproduction) | Generic |
| `bytefray-rules-4-alpha2` | — | Same, promoted verbatim to stable v4 | `RULESET_V4_ALPHA2` | Yes, all 4 CLIs | Yes | Extensive, incl. **release-blocking** equivalence gate | Current (historical-reproduction) | Generic |
| `bytefray-rules-4` | — | Current default process runtime | `RULESET_V4` | Yes, all 4 CLIs, **default for Agent API v2** | Yes, **default** | Extensive | Current, primary | Generic |

This inventory reconfirms Phase 1's finding without reopening it: seven of
the eight (plus the alias) are zero-cost `KEEP`s because their execution
code is inseparable from a still-supported identity. `bytefray-rules-3-alpha1`
remains the sole item whose *execution* mechanic (not its identity, not its
historical data) is genuinely separable — this phase completes the
coupling-boundary scoping Phase 1 could not close.

---

## D. `bytefray-rules-3-alpha1` reference topology

Every current reference falls into one of the six requested classes. Counts
and representative citations (full detail in §F–§K):

### New-execution support

- `ruleset_policy.py:352-357` (the `RulesetPolicy` object) and `:492` (its
  `_RULESET_POLICIES` entry) — the single fail-closed dispatch gate
  (`resolve_ruleset_policy`, `:681-694`).
- `python_runtime.py:154-1132` (the locality mechanic: constants, state
  fields, action validation/application, telemetry) plus mirrored wiring in
  `supervised_runtime.py` (reach resolution, `locus` seeding, tick-loop
  telemetry call, `apply_action` call).
- `match_service.py` (`MatchRequest.locality_reach` field, `_resolve_locality_reach`,
  conditional reproducibility/metadata payload construction, threading into
  entrant-controller construction).
- `agent_evaluation.py` (`EvaluationRequest.locality_reach`,
  `resolved_locality_reach`, `_V2_METHODOLOGY_RULESET_IDS` membership,
  the explicit allow-list in `_validate` at `:3392-3405`, extensive
  worker/identity-payload threading).
- `agent_worker.py`/`evaluation_worker.py` (`locality_reach` JSON wire-key
  plumbing, no logic).
- `tools/v3_phase2_locality_corpus.py` / `tools/v3_phase2_locality_rubric.py`
  (the one internal research driver that actually exercises the low-level
  API path in practice).

### Persisted-artifact recognition

- `BYTEFRAY_RULESET_V3_ALPHA1_ID` as a literal string appearing in
  historical `result.json`/`replay.jsonl` records and read back generically
  by `resolve_result_ruleset`/`resolve_replay_ruleset` (`result_model.py:274-292`,
  `replay.py:684-714`) with **no special-casing** — the same generic path
  every ruleset ID takes.
- `replay_history/query.py`'s `RulesetFacet` — its own docstring
  (`:225-245`) cites this exact ID as real corpus data it must be able to
  surface in the history browser.
- `app/services/replay_history_presentation.py`'s `_readable_ruleset`
  (`:312-331`) — a pure shape-derived formatter (`"bytefray-rules-3-alpha1"`
  → `"Ruleset v3 alpha1"`) with no per-identity table entry.
- The two **shared** frozensets `VULNERABLE_CORE_RULESET_IDS`/
  `OBSERVABLE_CORE_RULESET_IDS` (`python_runtime.py:128-151`), which include
  this ID alongside `bytefray-rules-2`/`-2-alpha1`/`-2-alpha11`/`-4-alpha1` —
  consumed by `client/src/battle_client/replay_status.py:38` for
  replay-display core-status derivation.

### Test coverage

94 function-level references across 10 files, all under the canonical
`engine/tests/` — full breakdown in §J.

### Documentation/history

`docs/archive/v3/*` (closed research record), `docs/FUTURE_PLANS.md:420-428,922-926`,
`docs/ROADMAP.md:909-934` — all accurate, correctly past-tense, non-stale
(§K).

### Transitional compatibility

**None found.** No code exists whose sole purpose is mapping old
`bytefray-rules-3-alpha1` data onto a newer behavior — unlike, say, the
`evaluation_history` v1/v2 adapters, there is no schema-generation bridge
here because the persisted record shape for this ruleset was never
different from any other native result/replay artifact of its era.

### Dead/stale

**None found in current source or current documentation.** Every reference
that exists today serves one of the five live classes above. (The
`docs/specs/run_match_pmars.md`-style "describes a module that no longer
exists" problem that Phase 2B.5 found for Redcode has no analogue here —
`docs/RULES.md` and `docs/COMPATIBILITY.md` currently contain **zero**
mentions of this ruleset at all, so there is no stale current-support claim
to correct.)

---

## E. Historical purpose

- **Introduced:** commit `ac1102b313bed5d627b31b4aee99aeac86394288`,
  "feat(rules): add the experimental bytefray-rules-3-alpha1 locality
  runtime," 2026-08-25 11:41:16 -0400 — found via `git log -S` on both the
  ID string and its constant name against `ruleset_policy.py` (single,
  unambiguous hit for the introduction). The entire v3 locality research
  program (identity, runtime, three test files, six fixture agents, and the
  closeout documentation) was committed within roughly 24 hours, 2026-08-25
  through 2026-08-26.
- **What it represented:** Ruleset v2's full gameplay (vulnerable core,
  observable-core beacon, identical scheduling/termination) plus one
  additive mechanic: a Python entrant occupies a single **execution
  locus** with a **bounded reach** `R`; three new action kinds (`MOVE`,
  `LOCAL_READ`, `LOCAL_WRITE`) operate relative to that locus, while
  absolute `READ`/`WRITE` are rejected under this identity specifically so
  a v2 agent forfeits loudly rather than silently misbehaving.
- **The research question:** could bounding locality resolve a
  Ruleset-v2 strategic limitation identified in the Beta2 program — that
  dedicated search-offense was the only effective counter to blind
  territorial expansion in a narrow parameter region (`docs/ROADMAP.md:909-918`)?
- **The verdict, stated in the codebase's own words:**
  `docs/archive/v3/V3_PHASE2_LOCALITY_FEASIBILITY.md` §23 —
  *"LOCALITY NOT VALIDATED — ABANDON CURRENT V3 THESIS."* Bounding reach
  forced *contiguous* claiming, which incidentally captured the fixed-size
  core — making blind expansion the **dominant** capture mechanism instead
  of checking it, the exact opposite of the intended effect
  (`docs/FUTURE_PLANS.md:922-926`, `docs/ROADMAP.md:923-926` — both current,
  live documents restate this same past-tense verdict independently, and
  agree word-for-word on the mechanism).
- **Never part of a public stable release as a gameplay identity.**
  The constant is textually present in the source tree at every `v3.0.0-*`
  tag purely because it predates them by one day — but `CHANGELOG.md`'s
  `[3.0.0]` and `[3.0.0-alpha1]` entries state explicitly that
  `bytefray-rules-2` is "v3.0's unchanged active gameplay identity" and
  cite the closed research program **as the reason no Ruleset 3 shipped**.
  `docs/FUTURE_PLANS.md:422-428` is equally explicit: *"It is **not**
  `bytefray-rules-3`... no stable Ruleset 3 exists."* This is the only
  "Ruleset 3" mention in `CHANGELOG.md`, and it is a denial, not a shipment
  record.
- **Always research-only/hidden by design, not by oversight.** `git log -S`
  against every CLI's argparse table (`cli.py`, `tournament_cli.py`,
  `agent_test.py`, `agent_evaluation.py`) returns **zero commits** that ever
  added this ID to a `choices=` list, at any point in this repository's
  history. `docs/archive/v3/V3_PHASE0_PRODUCT_SCOPE.md:34` states the intent
  contemporaneously: "never exposed on any product CLI's `--ruleset`
  choices."
- **Not superseded by v4's process model.** `docs/FUTURE_PLANS.md:282-303`
  is explicit that v4's later "multiple processes per entrant, each with an
  anchor and reach" model is a **different, separately-scoped question**
  the v3 program never addressed — v3's locality was one bounded locus for
  a single-process entrant, not multiple processes. Code-level confirmation:
  `process_agents.py`, `process_containment.py`, and `process_runtime.py`
  contain zero references to `locus`/`locality`.
  `docs/archive/v4/V4_RC1_PHASE3_PRODUCT_COHERENCE_AUDIT.md:339` itself
  calls a stray `FUTURE_PLANS.md` grep hit for this ID "an unrelated
  hypothetical" when auditing v4 documentation — v4's own product team
  treated it as unrelated at the time.
- **Users were never expected to author or retain agents for it.** The six
  `data/v3_locality_agents/` fixtures carry no README, are not in
  `STARTER_AGENT_NAMES` or `REFERENCE_AGENT_NAMES`, and
  `docs/archive/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md:280`'s
  own release-surface compatibility matrix marks them explicitly
  "Internal research," contrasted in the same table against genuinely
  user-facing starters like `v4_quorum` ("Explicitly Advanced Example").

**One documentation/reality nuance recorded, not resolved:**
`docs/ROADMAP.md:911-913` frames the v3 research branches as "never merged"
into `main`; the actual commit graph shows `v3-research-closeout` is a
strict linear ancestor of `main` (no merge commit anywhere). This describes
a rebase/fast-forward workflow the prose doesn't spell out precisely — it
does not change any finding above (the research conclusion and its
non-shipment are unambiguous either way) and is noted here only for
completeness, not as an action item.

---

## F. Implementation uniqueness

### What the ruleset shares vs. owns

`RULESET_V3_ALPHA1` (`ruleset_policy.py:352-357`) is field-for-field
identical to `RULESET_V2` on every axis except `ruleset_id` itself:
`supported_runtime_kinds={"python"}`, `supported_python_api_versions={1}`,
`core_placement="seat_spread"`, and every scheduler field left at the
shared dataclass default (sequential, no chunking, no rotation). Scheduling
and termination are therefore **byte-identical** to Ruleset v1/v2 — neither
reads `self.ruleset_id`. `scheduler.py` has zero references to this ruleset
or to locality at all.

**Confirmed shared with `bytefray-rules-2`/`-2-alpha1`/`-2-alpha11`, and
also `bytefray-rules-4-alpha1`** (broader sharing than a naive
"v3 reuses only v2" assumption would suggest):
`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`
(`python_runtime.py:128-151`) each list this ID alongside those other four
still-live identities, gating shared functions (`apply_core_capture`,
`seed_core_ownership`, `maintain_core_beacons`, `core_addresses`,
`_attribute_core_capture`) that are also called directly by
`process_runtime.py:1269` for the v4 family. **None of this shared
machinery would become dead if `bytefray-rules-3-alpha1` were retired** —
it stays fully live for the other four identities.

**Confirmed unique** — nothing else references it:
`LOCALITY_RULESET_IDS = frozenset({BYTEFRAY_RULESET_V3_ALPHA1_ID})`
(`python_runtime.py:194`) has exactly one member. Every function gated by
`has_bounded_locality()`/`locality_reach is not None` is exclusive to this
one identity.

### Exact implementation boundary (`python_runtime.py`)

| Block | Lines | LOC | Genuinely dead once new execution is retired? |
| --- | --- | --- | --- |
| Locality header/constants/`has_bounded_locality` | 154-209 | 56 | Yes |
| `circular_distance`/`circular_displacement` | 212-235 | 24 | Yes (confirmed: `placement.py`/`spectator_events.py` have their own independent implementations, not imports of these) |
| `PythonEntrantState` locus/telemetry fields + init | 760-841 | 33 | Yes |
| `ABSOLUTE_ADDRESSING_ACTIONS` + `validate_action`'s `if locality:` branch + operand-validation branches | 878-883, 921-927, 940-941, 953-955 | 18 | Yes |
| `apply_action`'s locality dispatch | 1000-1003 | 4 | Yes |
| `_apply_locality_action()` | 1026-1073 | 48 | Yes |
| `record_locality_tick()` | 1076-1108 | 33 | Yes |
| `locality_statistics()` | 1111-1132 | 22 | Yes |
| `reach < 1` validation raise | 1185-1192 | 8 | Yes |
| Tick-loop `record_locality_tick` call | 1459-1462 | 4 | Yes |
| **Subtotal, `python_runtime.py`** | | **250** | of 1,563 (~16%) |
| `supervised_runtime.py` mirrored telemetry call | 434-437 | 4 | Yes |
| `match_service.py` (`_resolve_locality_reach`'s reachable body, conditional payload/metadata lines) | 475-479, 509-510, 695 | 8 | Yes |
| **Total genuinely dead (reachability sense)** | | **262** | |

**Explicitly NOT dead, and must be preserved regardless of disposition:**

- `LOCALITY_ACTIONS` frozenset's **definition** (`python_runtime.py:885-891`)
  — its use as the `elif action.kind in LOCALITY_ACTIONS: raise ...` guard
  (`:928-929`) stays genuinely reachable and exercised by every *other*
  ruleset (an agent under `bytefray-rules-2` that mistakenly emits `MOVE`).
  Only its *other* use-site (the dead dispatch at `:1000-1003`) goes.
- `ActionKind.MOVE`/`LOCAL_READ`/`LOCAL_WRITE` enum members and
  `MatchContext.locality_reach`/`Observation.locus` (`agent_api.py`) —
  vestigial-but-present fields, not unreachable code. Historical
  `trace.jsonl`/replay records for this ruleset's matches persist these
  action-kind strings and the `locus` field; removing the enum members
  would risk breaking `ActionKind(value)` deserialization of that
  historical data. **Recommend keeping these permanently**, exactly as
  Phase 2B.6 kept `ResultEnvelope.backend`/`SCHEMA_VERSION_V1` as
  write-dead-but-read-live fields after Redcode retirement.
- `VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`'s membership
  entries for this ID — needed by `replay_status.py`'s
  `has_vulnerable_core`/`has_observable_core` to keep classifying
  historical replays of this ruleset correctly (§H). **This is the
  coupling-boundary answer Phase 1 flagged as unresolved**: the locality
  mechanic and the vulnerable/observable-core membership are two
  *independent* frozensets, and only the former should be touched.
- The generic parameter-plumbing sites (`agent_worker.py`,
  `evaluation_worker.py`, dozens of `locality_reach`/`resolved_locality_reach`
  threading points in `agent_evaluation.py`) become permanently inert
  (always `None`) rather than strictly unreachable; removing them is a
  larger, separate, lower-value refactor not recommended as part of this
  retirement (see §O).

### Answer to the charter's question

> If new execution under this ruleset disappeared, how much production
> implementation would actually become dead?

**262 lines across 3 files (`python_runtime.py`: 250; `match_service.py`: 8;
`supervised_runtime.py`: 4), out of the roughly 700+ lines that mention
locality/this ruleset ID at all once plumbing and shared-frozenset entries
are excluded.** This is a real, quantified, non-trivial reduction (~16% of
`python_runtime.py`) but it is not the whole surface — most of the
remaining mentions are either shared machinery that must stay for other
rulesets, or historical-compatibility fields that must stay regardless of
execution disposition.

---

## G. New-execution surface

| Surface | Evidence | Verdict |
| --- | --- | --- |
| `bytefray run` | `cli.py:294-300` — 5-item `choices=` list, no v3-alpha1 | **Not selectable at all** |
| `bytefray tournament` | `tournament_cli.py:60-67` — identical list | **Not selectable at all** |
| `agents test` | `agent_test.py:1043-1050` — identical list | **Not selectable at all** |
| `agents evaluate` (CLI) | `agent_evaluation.py:4384-4391` — identical list | **Not selectable at all** |
| `agents evaluate` (low-level `EvaluationRequest`) | `agent_evaluation.py:3392-3405` explicitly allow-lists it for a programmatically constructed request; the module's own comment (`:5315-5323`) states this in code | **Only accepted by low-level API** — used in practice only by `tools/v3_phase2_locality_corpus.py` |
| `agents evaluation-presets` | `evaluation_presets.py:81` — `_VALID_RULESETS = ("bytefray-rules-1", "bytefray-rules-2")`, narrower than the main CLIs (doesn't even include v4) | **Not selectable at all** |
| Low-level `MatchRequest`/`NativeMatchService.run` | `match_service.py:197` (`ruleset_id: str | None`, unrestricted), `:1419` (`resolve_ruleset_policy` succeeds because it's registered) | **Only accepted by low-level API** |
| Agent Designer GUI (`app/`) | `ruleset_options.py`'s three option tuples (`SIMPLE_RULESET_OPTIONS`, `EVALUATION_RULESET_OPTIONS`, `DESIGNER_RULESET_OPTIONS`, lines 78/94-100/106-111) never include it; repo-wide grep of `app/` for the ID returns zero hits; even a hypothetical in-process selection would re-enter `cli.py`'s `choices=` gate on launch (`launchers.py:130`) | **Not selectable at all**, defense-in-depth confirmed |
| `OMITTED_RULESET_CANDIDATES` | `ruleset_policy.py:625-629` — three entries, none experimental | **Cannot be silently reached** by an omitted `--ruleset` |
| Starter/reference agent defaults | `starters.py`'s `STARTER_AGENT_NAMES`, `reference_agents.py`'s `REFERENCE_AGENT_NAMES` | **No agent defaults to it** |
| `data/v3_locality_agents/` (6 fixtures) | Each `agent.yaml` has no `ruleset_id`/`ruleset` field at all — only descriptive prose; not referenced by `starters.py`, `reference_agents.py`, or ordinary agent discovery; consumed only by `test_v3_phase2_locality_agents.py` | **Pure test fixtures, no catalog presence** |

**Summary:** every product-facing surface already independently excludes
this identity via an explicit allow-list that never names it. The only two
live paths that can create a *new* match under it today are the two
low-level API constructions above, and in practice only one internal
research tool (`tools/v3_phase2_locality_corpus.py`) exercises that path
outside the test suite.

---

## H. Persisted-result/replay compatibility

### Readability

`resolve_result_ruleset` (`result_model.py:274-292`) and
`resolve_replay_ruleset` (`replay.py:684-714`) both special-case only
`envelope.mode` values (`"redcode94"`, the native-recoverable modes) —
**never a specific `ruleset_id` string**. A `bytefray-rules-3-alpha1`
record always carries an explicit `ruleset_id` and `mode="b2"`, so it
resolves through the fully generic `"recorded"` branch, exactly like
`bytefray-rules-2` or `bytefray-rules-4`. Neither file imports
`ruleset_policy` at all. `replay_history/discovery.py`, `index.py`, and
`query.py` treat `ruleset_id` as an opaque indexed/filtered string
(`index.py`'s `TEXT` columns, `query.py`'s `Sequence[str | None]` filter
fields) with zero per-identity branching. `evaluation_history/`'s
`rules_compatibility_id` field follows the identical pattern
(`v2_adapter.py`'s type-only check, no value table).

### Replayability

`client/src/battle_client/session.py`'s tick reconstruction
(`ReplaySession._apply`, `:343-367`) is a pure fold over already-computed
`MemoryDiff`/`TickSnapshot` data — **zero references to `ruleset_id`,
`ruleset_policy`, or `python_runtime` locality symbols anywhere in the
file.** `player.py` imports only `ReplayRecord`. The one engine dependency
on this path, `replay_status.py:38`'s `has_vulnerable_core`/
`has_observable_core`/`core_addresses`, is a **separate, shared**
frozenset-membership predicate (§F) — not the locality mechanic itself.
A repo-wide grep for `locus`/`locality` under `client/` returns **zero
hits**: the client never even renders the `locus` field a v3-alpha1 replay
carries. `MemoryDiff` is fully computed and persisted at write time, so
replay reconstruction never needs the locality reach mechanic to render a
tick — architecturally identical to the conclusion Phase 2B.5 reached for
the (unrelated) Redcode case.

### Re-execution

Requires the executable registry entry (`_RULESET_POLICIES` at
`ruleset_policy.py:492`) and the locality mechanic in `python_runtime.py`.
This is the only capability actually lost by retirement.

### The decisive test: what breaks if the registry entry is removed?

Every production caller of `resolve_ruleset_policy` was traced to exactly
four call sites, and every one sits on a new-execution or pre-launch
path — none is reachable from `replay_history/`, `evaluation_history/`,
`result_model.py`, `replay.py`, or `battle_client` (confirmed independently
by grep: zero occurrences of `ruleset_policy`/`resolve_ruleset_policy`/
`UnknownRulesetError` in any of those modules):

| Call site | Reached from | Class |
| --- | --- | --- |
| `ruleset_policy.py:531` (`agent_supported_by_ruleset`) | Omitted-`--ruleset` resolution; Designer pre-launch option filtering | new-execution |
| `app/services/ruleset_options.py:156` (`ruleset_supports_runtime_kinds`) | `validate_designer_ruleset`, the VM/Python launch guard | new-execution |
| `placement.py:266` (`core_placement_mode`) | Start-address resolution for a match about to execute | new-execution |
| `match_service.py:1419` | `NativeMatchService.run`'s dispatch boundary itself, "before either runtime is invoked and before any replay/result artifact exists" (the module's own comment) | new-execution |

**Conclusion: deregistering `bytefray-rules-3-alpha1` from
`_RULESET_POLICIES` while leaving the string constant, the shared
vulnerable/observable-core memberships, and the historical-artifact readers
untouched breaks nothing on any read/replay/display path.** It only makes
`resolve_ruleset_policy("bytefray-rules-3-alpha1")` raise
`UnknownRulesetError` — reachable solely from an explicit new-match/
new-evaluation attempt.

---

## I. Agent/package compatibility

**No agent package can declare or require this ruleset — the schema has no
field for it, at all.** `agent_package.py`'s `.bytefray-agent` manifest
schema (`PACKAGE_SCHEMA`, `_validate_package_fields` at `:625-668`) has no
`ruleset_id`/`ruleset` key; `_check_compatibility` (`:671-698`) checks only
`kind`/`agent_api_version`. Neither `agent_package.py` nor
`agent_package_cli.py` contains the string `"ruleset"` anywhere.

The six `data/v3_locality_agents/` fixtures use a different, older
artifact shape (a raw `agent.yaml`/`agent.py` discovery folder, not a
`.bytefray-agent` package) whose only mention of the ruleset
(e.g. `local_camper/agent.yaml:4` — "Runs only under `bytefray-rules-3-alpha1`")
is human-readable prose in a `description` field, not a machine-checked
declaration.

**If a package or raw-manifest agent naming this ruleset in its
description were imported/opened/run today**, import/inspect succeeds or
fails purely on `kind`/`agent_api_version` compatibility, identically to
any other Agent API v1 Python agent — there is no ruleset-aware code path
to special-case it, and none would need to change under retirement, since
ruleset selection happens at match-construction time, entirely orthogonal
to which package the agent code came from.

**Conclusion: package compatibility imposes zero constraint on this
disposition.** There is no coupling to sever.

---

## J. Test impact

**Canonical scope confirmed:** `pytest.ini`'s `testpaths` is
`_legacy/tests`, `engine/tests`, `client/tests`. All references to this
ruleset are confined to `engine/tests/` — zero hits in `client/tests/`,
`_legacy/tests/`, or the non-canonical root `tests/` (a distinct directory
of GUI/Designer widget tests, deliberately outside `testpaths`).

### Defining files — deleted wholesale if execution is retired

| File | `def test_` | Collected cases | Protects |
| --- | ---: | ---: | --- |
| `test_v3_phase2_locality_agents.py` | 19 | 70 | Population integrity/determinism for the 6 fixture agents against `NativeMatchService`/live evaluation |
| `test_v3_phase2_locality_evaluation.py` | 22 | 22 | Reach validation, evaluation-identity collision-freedom vs. v2, CLI non-disclosure |
| `test_v3_phase2_locality_runtime.py` | 41 | 64 | The runtime mechanic itself (`MOVE`/`LOCAL_READ`/`LOCAL_WRITE`, vocabulary rejection, replay `locus` recording, core-capture-under-locality) |
| **Total** | **82** | **156** | All three run **live** `NativeMatchService`/`EvaluationService` calls under this ruleset — this is what makes them "defining": once the registry entry is gone, every one of these raises `UnknownRulesetError` |

### Files needing a small, targeted edit

| File | Reference | Impact if retired |
| --- | --- | --- |
| `test_v4_alpha2_placement.py` | 2 functions each including one v3-alpha1 row in a cross-ruleset immutability table (calls `resolve_ruleset_policy` directly) | One parametrize row each removed; rest of file (about v4/v4-alpha2 placement) unaffected |
| `test_v4_interleaved_scheduler.py` | 1 function asserting `resolve_ruleset_policy(...).scheduler_mode == "sequential"` for v3-alpha1 among v1/v2/v4 rows | One assertion/row removed; rest unaffected |

### Files needing zero changes

| File | Reference | Why it survives untouched |
| --- | --- | --- |
| `test_agent_test.py`, `test_cli_characterization.py`, `test_tournament_service.py` | One negative `--help` assertion each (`"bytefray-rules-3-alpha1" not in out`) | Becomes *more* true, not less, after retirement |
| `test_v5_replay_history_presentation.py` (4 functions) | Uses the literal string as historical fixture data for the Replay History browser's labeling/filtering — no import of the runtime constant | **This is exactly the readability/replay coverage that must be preserved** — proves the browser correctly labels and filters old recorded runs of this ruleset even though it can't be relaunched |
| `test_ruleset_policy.py` | One docstring-only mention (illustrative prose, not code) | Not a functional reference at all |

### Totals and expected canonical count

94 function-level references across 10 files; 82 functions (156 collected
cases) are wholesale-deletable; 3 functions need a one-line/one-row edit;
8 functions plus one docstring mention need zero changes.

**If the three defining files are removed and the two small edits made**,
the canonical collected count would drop from the current **3,713** by
**156** (the defining files) plus a small number for the two edited
files' removed parametrize rows/cases (exact figure — likely 1-3 — to be
confirmed at implementation time by running `--collect-only` before/after
each edit, per this repository's standing test-count-tripwire discipline).
**Expected canonical count: approximately 3,713 → ~3,556–3,558.** This
phase does not commit to the exact final digit, consistent with its
research-only charter; an implementation phase must re-verify it
empirically, exactly as Phase 2B.6 did for its own predicted count.

**No test file is deleted or edited by this phase.** All figures above are
read from current source, not applied.

---

## K. Documentation impact

Unlike the Redcode/pMARS case, **there is no stale current-support claim to
correct** — this ruleset was never described as currently supported
anywhere live:

### Historical record (accurate, current, no action needed)

- `docs/FUTURE_PLANS.md:420-428` — states plainly it was "never merged,
  never exposed... not `bytefray-rules-3`... no stable Ruleset 3 exists."
- `docs/FUTURE_PLANS.md:922-926` — the rejection mechanism (blind expansion
  became dominant), past tense, accurate.
- `docs/ROADMAP.md:909-934` — the "v3 Ruleset Research — Closed" section,
  same verdict, same mechanism, independently phrased but consistent.
- `docs/archive/v3/*.md` (8 files) — the full closed-research record
  (feasibility study, product scope, closeout, research summary,
  integration/distribution notes, defensive-event design proposal,
  strategy-example ruleset clarity). Correctly archived, not touched.

### Compatibility documentation

**None exists specifically for this ruleset** — `docs/COMPATIBILITY.md`'s
persisted-Ruleset-identity table (`:736`, "current native (VM or Python)")
lists only the identities a *current* CLI path can create
(`bytefray-rules-1`, `-2`, `-4-alpha1`, `-4-alpha2`, `-4`), consistent with
never including `bytefray-rules-2-alpha1`/`-2-alpha11`/`-3-alpha1` either —
this is deliberate current-creation-path framing, not an omission to fix.

### Stale current documentation

**None found.** `docs/RULES.md`, `docs/RULES_V4.md`, `docs/COMPATIBILITY.md`,
and `README.md` were checked directly and contain **zero** mentions of
`bytefray-rules-3-alpha1` in any form — there is nothing in current
supported-product documentation to rewrite, retitle, or reframe.

### Conclusion

Retirement requires **no documentation change at all** to existing live
docs — a marked contrast with the Redcode/pMARS retirement's 18-file
documentation pass. If a future implementation phase adds a
`CHANGELOG.md` "Removed" entry recording the retirement (consistent with
this repository's pattern for the Redcode retirement), that is the only
new documentation this disposition would need.

---

## L. Disposition alternatives

### A. KEEP FULLY

No current user/research need justifies this. The identity has been
invisible on every product surface since the day it was created, over a
full major-version cycle ago; its research question was answered and
closed; nothing in Phase 0 through 2B.6's V6 research has surfaced a reason
to reopen it. **Not recommended.**

### B. RETIRE FROM NEW EXECUTION, KEEP READABILITY — recommended

Proven architecturally sound in §H: readability, replay rendering, and
history-browser display never touch the executable registry. The minimal
change is a single registry-entry removal (`ruleset_policy.py:352-357,492`);
a fuller cleanup can additionally remove the 262 genuinely dead lines
identified in §F, provided the explicitly-preserved items in that section
(string constant, shared frozenset memberships, `LOCALITY_ACTIONS`
definition, the `ActionKind` enum members, the `MatchContext`/`Observation`
optional fields, and the readability test files) are left untouched.
**This is the only alternative that matches the evidence on every axis.**

### C. REMOVE COMPLETELY

Not appropriate: `replay_status.py`'s `has_vulnerable_core`/
`has_observable_core` genuinely need this ID to remain in
`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS` to keep
classifying historical replays correctly, and `ActionKind`'s enum members
are needed to deserialize historical trace records. Removing recognition
entirely would silently degrade V6's compatibility guarantee for real,
already-created historical data — the same class of regression Phase
2B.5's own audit warned against for the analogous Redcode case (its §Q.4:
deleting the reader "would silently reduce V6's guarantee about V0.3–V5
artifacts... a regression, not a saving").

### D. KEEP TEMPORARILY FOR MIGRATION

Not applicable: there is no migration to perform. Historical artifacts
need only *reading*, never re-export or conversion — the persisted record
shape for this ruleset was never different from any other native
result/replay artifact of its era, so no time-boxed migration window is
needed before removing execution support.

---

## M. Quantified benefit/cost

| Dimension | Effect of Model B |
| --- | --- |
| Selectable ruleset identities reduced | **0 → 0 visible reduction** (it was already invisible everywhere); the reduction is in the *executable registry* (8 → 7 entries), not in any user-visible choice list |
| Production LOC removed (minimal registry-only change) | ~6 lines (the `RulesetPolicy` object + its dict entry) |
| Production LOC removed (full mechanic cleanup, recommended alongside) | 262 lines across `python_runtime.py` (250), `match_service.py` (8), `supervised_runtime.py` (4) — ~16% of `python_runtime.py` |
| Tests removed | 3 files, 156 collected cases wholesale; 2 files edited (~1-3 more cases) |
| Fixture data removable alongside (if the defining tests are deleted) | 6 `data/v3_locality_agents/` directories; `data/benchmarks/v3_phase2_locality.json` (loses its only consumer); `data/benchmarks/v3_phase2_locality_corpus.json` and `tools/v3_phase2_locality_corpus.py`/`v3_phase2_locality_rubric.py` (lose their only consumer, once that research driver is retired alongside — see §O) |
| Documentation simplified | None needed — no stale current-doc claims exist (§K) |
| Context-locality improvement | One fewer experimental identity in `ruleset_policy.py`'s registry to reason about when reading it; one fewer genuinely-distinct gameplay mechanic (locality) live in `python_runtime.py`'s already-large tick loop |
| Compatibility cost | **Zero** — no readability, replayability, or package-compatibility capability is lost (§H, §I) |

**Answer to the charter's central quantification question:** this is not
merely "8 identities to 7" cosmetics. It removes a genuinely distinct,
self-contained gameplay mechanic (262 LOC) that has had zero live
consumers for over a year, three test files' worth of execution-path
maintenance burden, and a closed-research fixture/benchmark cluster — while
imposing **no** historical-compatibility cost, because the compatibility
surfaces that matter (replay/result reading, replay rendering, history
browsing) were already generically implemented and never depended on this
ruleset's executable registration in the first place. The benefit is real
and the cost is genuinely near zero — an unusually clean case as these
disposition questions go.

---

## N. Recommendation

**RETIRE FROM NEW EXECUTION, KEEP HISTORICAL RECOGNITION (Model B).**

This is driven entirely by the evidence assembled above, not by the
identifier's "alpha1" label (per §15's instruction not to let that drive
the call) and not merely because historical tests exist (the historical
tests are exactly what justifies *keeping* recognition, while the separate
*defining* tests are what justifies *retiring* execution — the evidence
distinguishes these two claims cleanly rather than conflating them):

1. New execution has been invisible on every product surface since
   creation, over a full major-version cycle ago, and its research question
   was definitively answered and closed (§E).
2. Readability, replayability, and package compatibility are already
   architecturally independent of the executable registry (§H, §I) — there
   is no shim to build; the "keep readability" half of this recommendation
   costs nothing beyond leaving four specific things alone (§F, §O).
3. Retiring it removes a real, quantified, self-contained chunk of gameplay
   implementation (262 LOC) and its dedicated test/fixture cluster (§F, §J,
   §M) with **zero** compatibility cost — the cleanest possible ratio for
   this kind of decision.
4. No current default, CLI choice, GUI option, or package validation rule
   changes as a side effect (§G, confirmed against `OMITTED_RULESET_CANDIDATES`,
   `DEFAULT_DESIGNER_RULESET_ID`, and every option tuple).

---

## O. Dependency-complete implementation plan

*(For a future implementation phase — not executed here, per this phase's
research-only charter.)*

Derived from actual dependency direction, mirroring the batching discipline
Phase 2B.5/2B.6 established for the unrelated Redcode retirement.

| # | Batch | Contents | Why here | Verify |
| --- | --- | --- | --- | --- |
| 0 | Inventory snapshot | Record HEAD, `git status`, canonical count 3,713, and this report's predicted post-retirement count | Baseline for comparison | `pytest --collect-only` |
| 1 | Registry | Remove `RULESET_V3_ALPHA1` (`ruleset_policy.py:352-357`) and its `_RULESET_POLICIES` entry (`:492`). **Do not** remove `BYTEFRAY_RULESET_V3_ALPHA1_ID` the string constant, and **do not** touch `VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`'s membership for it | The single change that actually retires new execution; everything else already excludes it | `resolve_ruleset_policy("bytefray-rules-3-alpha1")` now raises `UnknownRulesetError`; `bytefray run`/GUI unaffected (they never offered it) |
| 2 | Evaluation allow-list coordination | Remove the explicit allow-list entry in `agent_evaluation.py:3392-3405` and the `_V2_METHODOLOGY_RULESET_IDS` membership (`:612-614`) so a stray `EvaluationRequest(ruleset_id=...)` fails with the clean, well-worded `EvaluationConfigurationError` this module already has, rather than a less-specific `UnknownRulesetError` surfacing later inside match construction | Batch 1 alone would leave this allow-list pointing at a now-unregistered identity, producing a worse error message (flagged directly by the persisted-artifact research pass, §H) | Construct an `EvaluationRequest` naming the retired ID; confirm the error message names it explicitly as unsupported |
| 3 | Research driver | Retire `tools/v3_phase2_locality_corpus.py` and `tools/v3_phase2_locality_rubric.py` — their sole purpose was running new evaluations under this identity, which no longer resolves | Depends on Batches 1-2; leaving it would mean shipping a broken internal tool | Confirm no other tool/test imports these two files (already confirmed zero product callers in this research pass) |
| 4 | Tests — defining | Delete `test_v3_phase2_locality_{agents,evaluation,runtime}.py` (156 collected cases) | Must follow Batches 1-3, or these tests fail rather than being cleanly removed | `pytest --collect-only` → confirm the predicted count |
| 5 | Tests — small edits | Remove the one v3-alpha1 row from `test_v4_alpha2_placement.py` (2 functions) and the one assertion from `test_v4_interleaved_scheduler.py` | Independent of Batch 4; these test *other* rulesets primarily | Both files still pass in full |
| 6 | Mechanic cleanup | Remove the 262 genuinely-dead lines identified in §F from `python_runtime.py`/`match_service.py`/`supervised_runtime.py`, explicitly preserving `LOCALITY_ACTIONS`'s definition, the `ActionKind` enum members, and `MatchContext.locality_reach`/`Observation.locus` | Depends on Batches 1 and 4 (nothing should still call the removed functions) | Full suite green; `mypy` clean; a historical v3-alpha1 replay still loads/renders (manual or scripted check, mirroring Phase 2B.6's §N.2/§I behavioral-proof pattern) |
| 7 | Fixture/data cleanup | Delete `data/v3_locality_agents/` (6 dirs) and `data/benchmarks/v3_phase2_locality{,_corpus}.json` | Depends on Batch 4 (their only consumers) and Batch 3 (the corpus file's only remaining consumer) | Confirm zero remaining references before deletion |
| 8 | Changelog | One `CHANGELOG.md` "Removed" entry naming the retirement and confirming historical readability, mirroring the Redcode retirement's entry | Records the completed retirement | — |
| 9 | Qualification | Full canonical suite; `mypy`/`ruff`; a behavioral proof that a historical `bytefray-rules-3-alpha1` result/replay still reads, indexes, and renders correctly with the registry entry gone (the direct analogue of Phase 2B.6's §I) | Nothing left to change | Full suite; targeted historical-readability script |

**A defensible two-commit compression**, if fewer commits are wanted:
(1+2+3) *retire the identity from new execution, including its research
driver*; (4+5+6+7+8) *remove the now-dead mechanic, its tests, and its
fixtures*.

---

## P. Phase 3 findings

Recorded for the later architecture/context-locality audit, per the
charter's instruction to defer anything not required for this disposition
decision.

1. **Execution registration and historical recognition are conflated in
   exactly the way this phase's central question anticipated** —
   `_RULESET_POLICIES` (execution) and `VULNERABLE_CORE_RULESET_IDS`/
   `OBSERVABLE_CORE_RULESET_IDS` (historical-recognition-relevant,
   also execution-relevant for still-live rulesets) are the same *kind* of
   table serving two purposes for different rulesets simultaneously. This
   phase found the boundary is currently clean enough to separate by hand
   (§F, §O), but a future ruleset retirement might not be so lucky; Phase 3
   could consider whether these tables should be split into an explicit
   "executable" set and a separate "historically-recognized" set from the
   start.
2. **`agent_evaluation.py`'s `_V2_METHODOLOGY_RULESET_IDS` allow-list is a
   third, independent place a ruleset identity must be registered** for
   full product-surface consistency, separate from `_RULESET_POLICIES` and
   `LOCALITY_RULESET_IDS`. This three-way duplication (noted as a coupling
   risk by the persisted-artifact research pass, §H) is exactly the kind of
   "registries serving too many responsibilities" pattern Phase 3 should
   examine across all rulesets, not just this one.
3. **GUI ruleset choices are already correctly derived from an explicit
   product-preference tuple (`DesignerRulesetOption`), not from the runtime
   registry directly** — this is a *positive* finding worth carrying
   forward as the pattern other surfaces should follow, since it is exactly
   why retiring this ruleset from `_RULESET_POLICIES` requires zero GUI
   change.
4. **Replay readers depending on executable-ruleset-adjacent frozensets
   (`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`) rather than
   a dedicated historical-classification table** is a real, if currently
   harmless, architectural coupling — `replay_status.py` reaches into
   `python_runtime.py` (a module otherwise entirely about live execution)
   for what is conceptually a display-classification concern. Phase 3
   could consider whether a `historical_core_mechanic_ids`-style table,
   independent of the live-execution module, would better express "this is
   about how old data is interpreted," distinct from "this is about how a
   new match runs."
5. **The `docs/ROADMAP.md` "never merged" vs. actual linear-ancestor git
   topology discrepancy** noted in §E — a documentation-precision item, not
   a disposition-relevant one, but worth a Phase 3 note since it's the kind
   of small factual drift the V6 program has already caught twice before
   (Phase 1's `pygame_canvas.py` and `.pyc`-file findings).

---

## Q. Risks/unresolved questions

- **The exact final canonical test count after Batches 4-5 (§J, §O) is an
  estimate (~3,556–3,558), not a verified figure** — this phase deliberately
  did not modify any test file, per its research-only charter, so the
  precise parametrize-row impact of the two small edits was not measured by
  actually running `--collect-only` before/after those specific edits. An
  implementation phase must re-verify this the same way Phase 2B.6 verified
  its own predicted 3,734 → 3,713.
- **This report's own LOC/line-range citations should be re-verified
  against source immediately before implementation**, consistent with this
  program's standing discipline (Phase 1's explicit lesson from the
  `pygame_canvas.py`/`.pyc` false-claim incidents): no commits landed
  between this phase's evidence-gathering and its writing, but time may
  pass before an implementation phase begins.
- **The `docs/ROADMAP.md` "never merged" framing** (§E, §P item 5) is
  recorded as an open documentation-precision question, not resolved here,
  since resolving it has no bearing on this disposition.
- **No genuine risk to historical-artifact compatibility was found** — this
  is itself worth flagging as a real, checked-not-assumed conclusion (per
  this program's evidence standard) rather than a default assumption: the
  persisted-artifact research pass explicitly traced every call site of
  `resolve_ruleset_policy` and confirmed none is reachable from any
  read/replay/display path (§H).

---

## R. Whether Opus escalation was required

**Not required — and this was verified against all five stated criteria,
not merely assumed:**

1. *Does removing executable registration break historical replay
   rendering?* No — proven architecturally independent, with every call
   site of the executable resolver traced and classified (§H).
2. *Does package compatibility require executable behavior rather than
   recognition?* No — the package schema has no `ruleset_id` field at all;
   there is no coupling to sever (§I).
3. *Do ruleset aliases make current stable behavior depend on alpha1
   implementation?* No — no alias exists for this identity
   (`_RULESET_ALIASES` has zero entries for it), and its unique mechanic
   (`LOCALITY_RULESET_IDS`) has exactly one member; the *shared* machinery
   it participates in (vulnerable/observable-core) primarily serves other,
   still-live rulesets, not the reverse (§F).
4. *Do persisted schemas store implementation details that cannot be read
   independently?* No — the one schema addition this ruleset motivated
   (`AgentState.locus`) is a plain optional field, generically serialized
   and read back with only a type check (§H).
5. *Do current external/user workflows plausibly depend on the identity
   despite lack of UI exposure?* No plausible dependency found — zero
   product CLI/GUI exposure at any point in this repository's history
   (verified via `git log -S` across every CLI's argparse table, not just
   current source), zero starter/reference/preset defaults, zero package
   coupling, and the closed research program's "no Ruleset 3" conclusion
   has been the stable, documented state for over a full major-version
   cycle.

All five resolved cleanly against direct source/history evidence, with no
remaining genuine ambiguity. Per the phase's own escalation criterion, the
investigation is complete at the Sonnet/Gemini tier.
