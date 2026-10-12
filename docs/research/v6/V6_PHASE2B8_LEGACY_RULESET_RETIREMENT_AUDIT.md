# Bytefray V6 — Phase 2B.8: Legacy Ruleset Retirement Audit

**Phase type:** Research-only. No ruleset, registry, policy object, alias,
test, default, package, GUI/CLI surface, or document outside this report was
modified. The only tracked change this phase produces is this file.

**Governing product policy (given, not re-litigated):** during V6 research
Bytefray should have **one currently supported executable baseline ruleset,
`bytefray-rules-4`**, behaviourally frozen as the scientific control; new V6
gameplay semantics belong to a future `bytefray-rules-6` identity, never to
in-place mutation of the control.

This audit determines the **complete dependency surface** and a
**dependency-ordered implementation plan** for reaching that model. It does
not implement any part of it.

---

## A. Executive conclusion

**The architecture is ready for this transition, and the decisive safety
property is proven behaviourally rather than merely argued: executable ruleset
registration and historical-artifact recognition are already fully separate
concerns.** With the executable registry narrowed in memory to
`bytefray-rules-4` alone, real historical artifacts of *every* candidate
identity still decode, attribute, index, label, and fully replay —
tick-by-tick, including per-entrant core integrity and capture ticks (§N). Not
one historical-artifact reader module imports the executable resolver.

**However, the retirement candidate list named in this phase's charter is not
a homogeneous set, and treating it as one would be the single largest risk to
Phase 2B.9.** The evidence splits the candidates into three classes with
radically different costs:

| Class | Identities | What retirement actually costs |
| --- | --- | --- |
| **1 — Free** | `bytefray-rules-2-alpha1`, `bytefray-rules-2-alpha11`, `bytefray-rules-3-alpha1` | Nothing user-visible. None has *ever* been selectable from any CLI, GUI, Designer, or preset surface. Pure registry + closed-research removal. |
| **2 — Cheap, but it costs the control's own proof** | `bytefray-rules-4-alpha1`, `bytefray-rules-4-alpha2` | No unique gameplay code (they are policy-field variants of one shared process runtime), but `bytefray-rules-4-alpha2` must stay executable for the **release-blocking equivalence corpus that is currently the only behavioural proof that `bytefray-rules-4` is what it claims to be**. Retiring alpha2 without replacing that proof weakens the control (§E, §J). |
| **3 — Not a ruleset retirement at all** | `bytefray-rules-1`, `bytefray-rules-2` | Retiring these removes **all Agent API v1 execution and all VM/blob execution** from the product. It strands 11 of 21 bundled starter agents, all 4 reference agents, the default output of `bytefray agents create`, the Agent API v1 reference opponent, both shipped v2 benchmark corpora, and the entire `evaluation_presets` `ruleset` field — whose only two legal values are these two identities. **830 of 3,713 canonical tests (22.4%) fail.** |

The central finding, stated plainly:

> **Retiring `bytefray-rules-1` and `bytefray-rules-2` from execution is not a
> ruleset retirement. It is the retirement of Agent API v1 and the VM/blob
> runtime, wearing a ruleset-retirement costume.** The ruleset identity is
> only the visible handle on a much larger product decision — one this audit
> deliberately does not make on the user's behalf.

This is a technical consequence, not an invented compatibility promise, and
not an argument that old rulesets should stay executable "for compatibility".
The V6 policy direction may well be exactly right. But the policy statement
"one executable baseline ruleset" and the product reality "Bytefray still
ships, scaffolds, and documents Agent API v1 agents" are currently in direct
conflict, and **only the second can be changed by editing a registry.**

**Recommendation:** stage the retirement into three scopes (§V). Land Scope A
in Phase 2B.9 as specified; land Scope B with a mandated replacement for the
equivalence proof; treat Scope C as its own phase, gated on an explicit
Agent-API-v1 product decision. Scope A alone already achieves the audit's
stated goal — *making the active game model obvious* — because the three
Class-1 identities are precisely the ones a reader of the registry cannot
distinguish from supported ones today.

**Precedent worth reusing rather than reinventing:** V5 Alpha 1 Phase B
already performed exactly this operation for two identities
(`bytefray-rules-5-r1-alpha1`, `bytefray-rules-5-r2-alpha1`). Its removal
pattern, its negative test, and its historical-readability guarantee are all
still in the tree and still passing, and 49 of its artifacts are still
readable in this checkout (§D.2, §N). Phase 2B.9 should follow that template.

---

## B. Baseline

Established before investigation began, per §1 of the charter.

| Check | Result |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `c74d6c67faca36f6394cb0a258687a8774dc48b4` |
| Divergence from `origin/v6-research` | **0 ahead, 0 behind** (after `git fetch origin v6-research main`) |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — **untouched** |
| Canonical tests collected | **3,713 across 158 files** (`python -m pytest --collect-only -q`, summed) — exactly matches the Phase 2B.7 baseline |
| Tracked files | 798 (426 `.py`, 188 `test_*.py`, 212 `.md`, 234 under `docs/`) |
| Registered executable ruleset identities | **8** (unchanged since `v5.0.0`) |
| Historical artifacts available for verification | 53,458 `result.json`, 44,547 `replay.jsonl` under `runs/` |
| Working tree at phase start | **One deviation — see B.1** |

### B.1 Precondition deviation (reported, not normalised)

The charter requires that all prior Phase 2B work "must be committed and
synchronized" before this phase begins. It is not:

```
?? docs/research/v6/V6_PHASE2B7_RULESET3_ALPHA1_DISPOSITION.md
```

The Phase 2B.7 report is **present but untracked** — the direct and expected
consequence of Phase 2B.7's own closing instruction ("leave the completed
audit report in the working tree for review"), which this phase inherits
verbatim in its §29. Per the charter's "stop and report rather than stashing,
discarding, or normalizing changes", the file was **left exactly as found**;
nothing was committed, stashed, or modified, and this phase did not commit its
own report either.

This is recorded as a process observation, not a blocker: it has no bearing on
any finding here, because Phase 2B.7's conclusions were re-derived from
current source in this pass rather than trusted (§H).

**Recommended action:** commit `V6_PHASE2B7_…md` alongside this report before
Phase 2B.9 begins, so the audit trail is continuous.

### B.2 The registry is behaviourally identical to the `v5.0.0` release

`git diff v5.0.0..HEAD -- engine/src/battle_engine/rules.py
engine/src/battle_engine/ruleset_policy.py` yields **comment-only changes**
(two Redcode-wording corrections from Phase 2B.6). The executable ruleset
registry in this checkout is behaviourally identical to the one shipped in
`v5.0.0`.

This matters for §O: **`v5.0.0` is the single, precise historical release that
can exactly re-execute all eight identities**, and is therefore the honest
answer to "where did exact old-engine behaviour go".

---

## C. Product policy applied in this audit

Taken as given and not re-argued:

* `bytefray-rules-4` = the frozen V4/V5 control; executable, behaviourally
  immutable for the duration of V6 research.
* `bytefray-rules-6` = the future identity for any materially new V6 game
  semantics. Not created, stubbed, or designed here.
* Older identities lose **new-execution** support; **historical recognition**
  is retained where it is useful and already cheap.
* Absence of a large userbase is a product-policy consideration already
  settled by the user. This audit therefore reports **technical consequences**
  only, and does not invent compatibility promises. Where it reports that
  something breaks (§L, §M, §P), that is a measured fact about this
  repository, not an argument for preservation.

---

## D. Current ruleset inventory

`ruleset_policy._RULESET_POLICIES`
(`engine/src/battle_engine/ruleset_policy.py:487-496`) registers exactly
**8** identities. Policy fields below were read back from the live objects,
not transcribed from comments.

| # | Canonical ID | Policy object | Runtime kinds | Agent API | Placement | Process sel. | Scheduler |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `bytefray-rules-1` | `RULESET_V1` | unrestricted (**VM + Python**) | 1 | `zero` | priority | sequential |
| 2 | `bytefray-rules-2-alpha1` | `RULESET_V2_ALPHA1` | unrestricted | **any** | `zero` | priority | sequential |
| 3 | `bytefray-rules-2-alpha11` | `RULESET_V2_ALPHA11` | unrestricted | **any** | `zero` | priority | sequential |
| 4 | `bytefray-rules-2` | `RULESET_V2` | python | 1 | `seat_spread` | priority | sequential |
| 5 | `bytefray-rules-3-alpha1` | `RULESET_V3_ALPHA1` | python | 1 | `seat_spread` | priority | sequential |
| 6 | `bytefray-rules-4-alpha1` | `RULESET_V4_ALPHA1` | python | 2 | `seat_spread` | priority | chunked/2, rotate |
| 7 | `bytefray-rules-4-alpha2` | `RULESET_V4_ALPHA2` | python | 2 | `seeded` | round_robin | chunked/2, rotate |
| 8 | **`bytefray-rules-4`** | `RULESET_V4` | python | 2 | `seeded` | round_robin | chunked/2, rotate |

Measured agent-compatibility matrix (`RulesetPolicy.supports_agent`):

```
supports_agent(kind='vm'):            rules-1 ✓  rules-2-alpha1 ✓  rules-2-alpha11 ✓   (all others ✗)
supports_agent(python, api=1):        rules-1 ✓  rules-2 ✓  rules-2-alpha1 ✓
                                      rules-2-alpha11 ✓  rules-3-alpha1 ✓              (v4 family ✗)
supports_agent(python, api=2):        rules-4 ✓  rules-4-alpha1 ✓  rules-4-alpha2 ✓
                                      rules-2-alpha1 ✓  rules-2-alpha11 ✓  ← see T-13
```

### D.1 Exposure matrix

| Identity | CLI `--ruleset` (×4) | Designer Simple | Designer Adv./Dev. | Designer Eval. | Eval. preset file | Eval. low-level API | Auto-selected when omitted | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bytefray-rules-1` | **yes** | no | **yes** | **yes** | **yes** | yes | **yes** (VM rosters; empty roster) | LEGACY — Class 3 |
| `bytefray-rules-2-alpha1` | no | no | no | no | no | no | never | LEGACY — Class 1 |
| `bytefray-rules-2-alpha11` | no | no | no | no | no | no | never | LEGACY — Class 1 |
| `bytefray-rules-2` | **yes** | **yes** | **yes** | **yes** | **yes** | yes | **yes** (API v1 rosters) | LEGACY — Class 3 |
| `bytefray-rules-3-alpha1` | no | no | no | no | no | **yes** | never | LEGACY — Class 1 |
| `bytefray-rules-4-alpha1` | **yes** | no | **yes** | **yes** | no | yes | never | LEGACY — Class 2 |
| `bytefray-rules-4-alpha2` | **yes** | no | **yes** | **yes** | no | yes | never | LEGACY — Class 2 |
| **`bytefray-rules-4`** | **yes** | **yes (default)** | **yes (default)** | **yes (default)** | **no** ⚠ | yes | **yes** (API v2 rosters) | **CURRENT CONTROL** |

The four product CLIs (`bytefray run` `cli.py:293-300`; `bytefray tournament`
`tournament_cli.py:59-67`; `agents test` `agent_test.py:1042-1050`;
`agents evaluate` `agent_evaluation.py:4383-4391`) share one **identical
5-item** `choices=` list: `rules-1`, `rules-2`, `rules-4-alpha1`,
`rules-4-alpha2`, `rules-4`. The three Class-1 identities appear on **no**
product surface anywhere.

⚠ **`bytefray-rules-4` is not a legal value in an evaluation preset file.**
`evaluation_presets._VALID_RULESETS = ("bytefray-rules-1", "bytefray-rules-2")`
(`evaluation_presets.py:81`, enforced at `:341`). The control cannot be named
in a preset; only the two Class-3 legacy identities can. This is a
pre-existing product gap surfaced by this audit, and it becomes a hard
breakage under Scope C (§U trap T-7).

### D.2 INVESTIGATE — identities the charter did not anticipate

**Two registered identities are absent from the charter's candidate list:**
`bytefray-rules-2-alpha1` and `bytefray-rules-2-alpha11`. Both are fully
registered, both are executable today, and both are **less** exposed than any
candidate the charter did name — they belong in Class 1 and should be retired
in the same batch as `bytefray-rules-3-alpha1`. Omitting them would leave the
retirement incomplete and the registry still misleading.

Both also carry a **latent policy defect** worth recording (§X.6):
`supported_python_api_versions` is `None` ("any"), so
`supports_agent(kind="python", api_version=2)` returns `True` for both — yet
neither is in `PROCESS_RULESET_IDS`, so an Agent API v2 roster accepted under
them would dispatch to the **Agent API v1** runtime. Unreachable in practice
(no surface offers them), but exactly the kind of inconsistency that retiring
them removes for free.

**Two further identities exist only in persisted data**, discovered via
`replay_history/query.py:225-245`'s own docstring:
`bytefray-rules-5-r1-alpha1` and `bytefray-rules-5-r2-alpha1`. These are
**not** retirement candidates — they were already retired from execution by V5
Alpha 1 Phase B, and they are the working precedent this audit recommends
copying:

* Removed from `_RULESET_POLICIES` entirely; `resolve_ruleset_policy` raises
  `UnknownRulesetError` for both.
* Negative test already in the tree and passing:
  `test_v5_alpha1_phase_b_engine_hygiene.py::test_rejected_rulesets_not_recognized_in_production`.
* Label derivation still tested:
  `test_v5_replay_history_presentation.py:325` pins
  `"bytefray-rules-5-r1-alpha1"` → `"Ruleset v5 r1 alpha1"`.
* Research runners retained with a literal ID plus a comment naming the
  historical commit — `tools/research/v5/r1_runner.py:29-34`:
  *"…were evaluated, rejected, and isolated in Phase B. Rerunning this
  experiment against the original experimental engine requires checking out
  commit 18e5ac6."*
* **49 of their artifacts are still present and still readable in this
  checkout** (§N.2).

---

## E. Ruleset 4 frozen-control definition

> **`bytefray-rules-4` is the immutable V6 research baseline.** Nothing in any
> retirement scope may alter its dispatched, hashed, or persisted behaviour.

### E.1 What defines Ruleset 4 today

| Concern | Location | Note |
| --- | --- | --- |
| Identity constant | `rules.py:95` `BYTEFRAY_RULESET_V4_ID` | Dependency-free module |
| Policy object | `ruleset_policy.py:430-439` `RULESET_V4` | Fields copied verbatim from `RULESET_V4_ALPHA2` |
| Executable registration | `ruleset_policy.py:495` | One line |
| Runtime dispatch gate | `ruleset_policy.py:449-456` `PROCESS_RULESET_IDS` | Selects `ProcessMatchController` |
| Gameplay implementation | `process_runtime.py` (1,367 LOC) | **Contains zero ruleset-ID branching** — only `RULESET_V4` as a default (`:336`, `:639`) |
| Scheduling | `scheduler.run_chunked_quota` via `RulesetPolicy.run_scheduler` | Field-driven (`chunked`, K=2, rotate) |
| Placement | `placement.seeded_seat_starts` via `core_placement="seeded"` | Field-driven |
| Core capture | `python_runtime.apply_core_capture`, called unconditionally at `process_runtime.py:1269` | **Shared** |
| Arena / ownership | `vm.VM` (`_rd32`/`_wr8`/`ownership_counts`) | **Shared** |
| Overlap guard | `match_service._CORE_PLACEMENT_GUARDED_RULESET_IDS` (`:409-429`) | Membership |
| Evaluation methodology | `agent_evaluation._V4_METHODOLOGY_RULESET_IDS` (`:663-665`) | Membership |
| Designer default | `app/services/ruleset_options.py:67` `DEFAULT_DESIGNER_RULESET_ID` | |
| Omitted-selection slot | `ruleset_policy.OMITTED_RULESET_CANDIDATES[1]` (`:625-629`) | API v2 rosters |
| Spectator auto-trace | `app/services/designer_workflows.py:321-323` | Membership |
| Replay schema selection | `match_service.py:1212` — schema **4** iff in `PROCESS_RULESET_IDS` | |

**Aliases pointing to Ruleset 4: none.** `rules._RULESET_ALIASES` has exactly
one entry, and it points at `bytefray-rules-1`.

### E.2 The control is decoupled from every candidate — with one important exception

`bytefray-rules-4` is in **neither** `VULNERABLE_CORE_RULESET_IDS` nor
`OBSERVABLE_CORE_RULESET_IDS` (`python_runtime.py:128-151`), and
`process_runtime.py` never consults them. Verified by execution:

```
bytefray-rules-4    vulnerable=False  observable=False
```

So the entire vulnerable-core / observable-core seeding and beacon machinery
belongs to the *legacy* identities only. The control shares with them only
`apply_core_capture`, `core_addresses`, `CORE_SIZE`, `derive_agent_seed`, the
diagnostics block, and `vm.VM` — **all of which must be retained under every
scope** (§Q.3).

**The exception.** `bytefray-rules-4-alpha2`'s executability is currently
load-bearing *for the control's own proof*:

`engine/tests/test_v4_stable_ruleset_equivalence.py` (27 collected cases,
described in its own module docstring as **release-blocking**) proves the
promotion claim by running the *same* `MatchRequest` twice — once under
`bytefray-rules-4` and once under `bytefray-rules-4-alpha2` — against real
bundled starter agents, then diffing every `TickSnapshot` byte-for-byte. Its
docstring is explicit that this is "the release-blocking behavioral proof of
that claim, not a first search for a difference."

Under a narrowed registry, **23 of its 27 cases fail.** Retiring alpha2
therefore does not merely remove an old identity; it removes the only
executable proof that the frozen control is gameplay-identical to the
prerelease it was promoted from. `test_v4_historical_immutability.py` (4
cases) has the same dependency.

### E.3 Tests that MUST survive every cleanup (they protect the frozen control)

| File | Cases | Protects |
| --- | ---: | --- |
| `test_v4_stable_ruleset_equivalence.py` | 27 | Control ≡ alpha2, byte-for-byte (**release-blocking**) |
| `test_v4_runtime_default_ruleset.py` | 10 | Control is what an omitted API-v2 selection resolves to; no alpha fallback |
| `test_v4_historical_immutability.py` | 4 | Running a control match never mutates state an alpha match reads |
| `test_v4_alpha2_placement.py` | 67 | Seeded placement vectors pinned (partly cross-ruleset — see §P.3) |
| `test_v4_alpha2_scheduler.py` | 18 | K=2 rotating scheduler semantics |
| `test_v4_process_semantics.py` | 5 | Process / quota / disruption semantics |
| `test_v4_trace_equivalence.py` | 2 | Trace schema v2 equivalence |
| `test_v4_production_integration.py` | 24 | End-to-end control execution |
| `test_v5_alpha1_phase_b_engine_hygiene.py` | 9 | Retired identities stay unrecognised; control stays default |
| `test_v5_starter_agents.py` | 54 | Bundled API-v2 starters run under the control |
| `test_v5_agent_parameters.py` | 124 | Parameter plumbing under the control |

Under Scope B or C, `test_v4_stable_ruleset_equivalence.py` and
`test_v4_historical_immutability.py` **cannot simply be deleted** — that would
trade the control's proof for tidiness. §V.B.2 specifies the replacement.

---

## F. Ruleset 1 findings

### F.1 Historical purpose

Introduced by `e535ec1` *"feat(compat): define Bytefray Ruleset v1 contract"*
(2026-08-12, v0.10 cycle) as the first-class gameplay-semantics identity for
behaviour that already existed. Public, stable, permanent; documented in full
by `docs/RULES.md`. Superseded for *current Python gameplay* by
`bytefray-rules-2` (v2.0.0-beta1) and for *current process gameplay* by
`bytefray-rules-4` — but **never superseded for VM/blob entrants**, for which
it remains the only product-selectable executor.

### F.2 Current new-execution reachability — reachable from everywhere

| Surface | Reachable? | Evidence |
| --- | --- | --- |
| CLI (all four) | **Yes**, explicit `choices=` entry | `cli.py:295`, `tournament_cli.py:62`, `agent_test.py:1045`, `agent_evaluation.py:4386` |
| Designer Advanced / Development | **Yes** (`RULESET_V1_OPTION`) | `ruleset_options.py:45-47`, `:110` |
| Designer Evaluation (pairwise) | **Yes** | `ruleset_options.py:99` |
| Designer Simple | No | `SIMPLE_RULESET_OPTIONS` = v2, v4 only |
| Evaluation preset file | **Yes** | `evaluation_presets.py:81` |
| Evaluation low-level API | **Yes** | `agent_evaluation.py:3393` |
| Low-level `MatchRequest` | **Yes** | `match_service.py:197` |
| Research tools | Indirectly — every tool that omits `ruleset_id` | §Q.4 |

### F.3 Dangerous fallback semantics — all confirmed behaviourally

The charter asked specifically for `unknown / missing / first-registered →
Ruleset 1` patterns. **Three exist, and all three survive a narrowed
registry** (verified by executing them with `_RULESET_POLICIES` reduced to
`{bytefray-rules-4}`):

| # | Site | Trigger | Result with registry narrowed |
| --- | --- | --- | --- |
| **F-1** | `match_service._resolve_ruleset_id` (`:514-525`) — `return request.ruleset_id or BYTEFRAY_RULESET_ID` | Any `MatchRequest(ruleset_id=None)` | Dispatches, hashes and persists as `bytefray-rules-1` |
| **F-2** | `ruleset_policy.resolve_omitted_ruleset_for_agents` (`:673`) | **Empty roster** | → `bytefray-rules-1` — retired ID returned |
| **F-3** | `ruleset_policy.resolve_omitted_ruleset_id` (`:768`, `:783`) | Empty kinds, **or** `NoCompatibleRulesetError` swallowed | → `bytefray-rules-1` for *every* input tested |

Measured output with the registry narrowed to the control alone:

```
empty roster      -> 'bytefray-rules-1'   <== RETIRED ID RETURNED
API v2 python     -> 'bytefray-rules-4'
API v1 python     -> NoCompatibleRulesetError (clean)
VM/blob           -> NoCompatibleRulesetError (clean)
kind-only empty   -> 'bytefray-rules-1'   <== RETIRED ID RETURNED
kind-only python  -> 'bytefray-rules-1'   <== RETIRED ID RETURNED
kind-only vm      -> 'bytefray-rules-1'   <== RETIRED ID RETURNED
```

`resolve_omitted_ruleset_id` is **retained only as an out-of-tree
compatibility surface** — it has zero in-tree production callers; all four
CLIs call `resolve_omitted_ruleset_for_agents`. Its
`except NoCompatibleRulesetError: return BYTEFRAY_RULESET_ID` swallow
(`:782-783`) is the worst of the three, because it converts a clean failure
into a silent retired-identity selection.

**There is no "first registered wins" behaviour.** `resolve_ruleset_policy`
(`:681-694`) is a strict dict lookup raising `UnknownRulesetError`; its
docstring explicitly disclaims prefix matching and "latest Ruleset" fallbacks,
and direct execution confirms it.

### F.4 Historical-artifact recognition — required, and correctly independent

`bytefray-rules-1` must remain **recognisable** regardless of execution
disposition, because two readers legitimately *synthesise* it for artifacts
that never recorded it:

* `result_model.resolve_result_ruleset` (`:274-292`): `ruleset_id` absent +
  `mode == "b2"` → `RulesetProvenance("bytefray-rules-1", "recovered")`.
* `replay.resolve_replay_ruleset` (`:684-714`): `ruleset_id` absent +
  `schema_version == 3` → the same.

This is not a stale fallback; it is evidence-backed provenance recovery
documented in `docs/RULES.md`. **In this checkout's own corpus, 673 of 53,458
`result.json` files carry no `ruleset_id` at all** and depend on exactly this
path. Verified live with the registry narrowed:

```
(no ruleset_id)  read_result -> ruleset='bytefray-rules-1' conf='recovered' mode='b2' winner='A'
                 replay HUD  -> 'bytefray-rules-1 (recovered)'   ticks=300
```

**Consequence for Phase 2B.9:** `BYTEFRAY_RULESET_ID`, `normalize_ruleset_id`,
`_RULESET_ALIASES`, and both `resolve_*_ruleset` functions must be retained
**verbatim** under every scope. Only the `_RULESET_POLICIES` entry and the
fallback sites F-1/F-2/F-3 are in scope for change.

### F.5 Current product need — affirmative, and substantial

This is the charter's §4.G question, and for Ruleset 1 the answer is not
"absence of evidence":

* **4 of 21 bundled starter agents are VM/blob agents** — `runner`, `writer`,
  `seeker`, `spiral` (`starters.STARTER_AGENT_NAMES:43-65`; their `agent.yaml`
  files declare neither `kind` nor `api_version`; bytecode assembled by
  `builtins/registry.py:4` `SUPPORTED`). **`bytefray-rules-1` is the only
  product-selectable ruleset that executes them** — `supports_agent(kind="vm")`
  is `True` only for `rules-1`, `rules-2-alpha1` and `rules-2-alpha11`, and
  the latter two appear on no surface.
* `docs/RULES.md` currently presents it as the frozen contract "Bytefray
  intends to carry through the 1.x series"; `ruleset_options.py:137-140` tells
  users in the GUI that "VM/blob agents run under Ruleset v1 only".

Retiring it from execution therefore deletes a shipped, documented product
capability. That may be an acceptable V6 decision — it is not this audit's
call — but it must be made deliberately, not as a side effect.

---

## G. Ruleset 2 findings

### G.1 Why it has persisted

Introduced by `bad448c` *"feat(v2.0-beta1): establish Ruleset v2 semantic
identity"* (2026-08-19), promoting `bytefray-rules-2-alpha11`'s
evidence-backed Vulnerable Core + Consistent Core Observability semantics into
a permanent identity. Stable since `v2.0.0`.

**It is not merely "the last historical stable ruleset carried forward."** It
is the **current, live, default gameplay for every Agent API v1 roster**, and
is first in product-preference order on almost every surface:

* `OMITTED_RULESET_CANDIDATES = (rules-2, rules-4, rules-1)` — `rules-2` is
  **first** (`ruleset_policy.py:625-629`).
* `SIMPLE_RULESET_OPTIONS = (RULESET_V2_OPTION, RULESET_V4_OPTION)` — and
  `RULESET_V2_OPTION`'s label is literally
  **"Ruleset v2 — Current / Recommended"** (`ruleset_options.py:26-28`, `:78`).
* It is first in `EVALUATION_RULESET_OPTIONS` and `DESIGNER_RULESET_OPTIONS`.
* `RULESET_DESCRIPTION` (`:123-133`), shown in the GUI, opens with "Ruleset v2
  is Bytefray's current gameplay ruleset".

So the answer to the charter's question — *"does Ruleset 2 still have any
current execution purpose?"* — is **yes, unambiguously**: it is the current
gameplay contract for one of the two Agent API generations Bytefray still
ships, scaffolds, and documents.

### G.2 The Agent API v1 dependency chain

| Dependency | Count | Detail |
| --- | ---: | --- |
| Bundled Agent API v1 Python starters | **7** | `claimer`, `strider`, `hunter`, `wanderer`, `adaptive`, `raider`, `sentinel` |
| Bundled reference agents (evaluation baselines) | **4** | `core_defender`, `core_seeker`, `reactive_core_defender`, `core_tracker` — `reference_agents.py:79-87` hardcodes `api_version=1` |
| `bytefray agents create` default output | **all** | `agent_scaffold.DEFAULT_API_VERSION = 1` (`:53`) |
| `agents test` reference opponent (non-process path) | 1 | `agent_test._reference_opponent_spec:165-183`, `api_version=1` |
| Shipped benchmark corpora declaring `bytefray-rules-2` | **3** | `data/benchmarks/v2_baseline.json`, `v2_baseline_corpus.json`, `v3_phase1_arena_action_grid.json` |
| Evaluation preset `ruleset` legal values | 2 of 2 | `("bytefray-rules-1", "bytefray-rules-2")` |
| Historical `result.json` in this checkout | **31,053** | 58% of the entire corpus |

Combined with §F.5, retiring `rules-1` **and** `rules-2` strands **11 of 21
bundled starter agents** (7 API-v1 Python + 4 VM) and **all 4 reference
agents**.

`agent_scaffold.py:46-53` deserves direct quotation, because it states the
project's own standing rule against the very change Scope C would force:

> "Deliberately pinned to 1 rather than tracking `agent_api.AGENT_API_VERSION`:
> `bytefray agents create <id>` has always produced an Agent API v1 agent, and
> repointing an established command's default at a newer generation would
> silently change the meaning of every existing script and instruction that
> uses it."

Under Scope C the default output of `bytefray agents create` becomes an agent
that **cannot run at all**. Resolving that requires either overriding that
standing rule or adding an explicit opt-in migration — a decision outside this
phase's remit (§U trap T-6).

### G.3 Unique vs shared implementation

**Unique to the Ruleset-2 family** — dead only if *all* of `rules-2`,
`rules-2-alpha1`, `rules-2-alpha11`, `rules-3-alpha1` **and** `rules-4-alpha1`
lose execution (note the last is a Class-2 identity, so this code does not
become dead under Scope A alone):

| Symbol | Location | LOC |
| --- | --- | ---: |
| `VULNERABLE_CORE_RULESET_IDS` | `python_runtime.py:128-143` | 16 |
| `OBSERVABLE_CORE_RULESET_IDS` | `python_runtime.py:144-151` | 8 |
| `has_observable_core` | `python_runtime.py:244-254` | 11 |
| `core_seed_byte` | `python_runtime.py:255-260` | 6 |
| `_snapshot_core_owners` | `python_runtime.py:268-290` | 23 |
| `seed_core_ownership` | `python_runtime.py:291-322` | 32 |
| `maintain_core_beacons` | `python_runtime.py:323-365` | 43 |
| Gating in `supervised_runtime.py` | `:278-279`, `:393-394`, `:422`, `:433` | ~10 |

**`has_vulnerable_core` is NOT in that list.** It is called by
`client/src/battle_client/replay_status.py:180` to classify **historical
replays** for display, and must be retained permanently regardless of
execution disposition. This is the sharpest execution/recognition boundary in
the codebase and the easiest one to get wrong (§U trap T-9).

**Shared with the control, must be retained:** `apply_core_capture` (called
unconditionally by `process_runtime.py:1269`), `_attribute_core_capture`,
`core_addresses`, `CORE_SIZE`, `derive_agent_seed`, the whole `diagnose_*`
block, `vm.VM`.

### G.4 What Scope C would make execution-dead

| Module | LOC | Status after Scope C |
| --- | ---: | --- |
| `supervised_runtime.py` | 557 | Wholly execution-dead (Agent API v1 supervised runtime) |
| `python_runtime.PythonEntrantController` + state/action machinery (`:705-1563`, less `derive_agent_seed`) | ~850 | Execution-dead (Agent API v1 unsupervised runtime) |
| `match_service._run_vm_match` (`:1318-1383`) | 66 | Execution-dead (VM dispatch) |
| `builtins/registry.py` | 146 | Execution-dead (VM bytecode assembly) |
| `instructions.py` | 14 | Execution-dead (VM opcodes) |
| `vm.VM.load_code` / `VM.step` | ~70 of 148 | Execution-dead — **but the rest of `vm.py` is the shared arena and must stay** |
| Replay schema 3 / trace schema v1 **writing** | — | Write-dead; read support must remain (§U trap T-14) |

---

## H. Ruleset 3 Alpha1 findings

Phase 2B.7's findings were **re-verified against current source** in this pass
rather than trusted, per this repository's standing rule that a prior report
is input to be checked, not a source of truth. Every structural claim
re-checked held:

| 2B.7 claim | Re-verified? |
| --- | --- |
| A single registry line gates all new execution (`ruleset_policy.py:492`) | ✅ Entry present; `resolve_ruleset_policy` is a strict lookup |
| `LOCALITY_RULESET_IDS` has exactly one member | ✅ `python_runtime.py:194` |
| No CLI/GUI/Designer/preset surface offers it | ✅ Absent from all four `choices=` lists and all three `DesignerRulesetOption` tuples |
| Only low-level API paths reach it | ✅ `agent_evaluation.py:3395` allow-list + `MatchRequest` |
| ~262 LOC unique gameplay code | ✅ Consistent with the locality block measured here (250 in `python_runtime.py`) |
| ~156 execution-focused collected cases | ✅ 70 + 22 + 64 = **156** confirmed from `--collect-only` |
| Historical readability independent of registration | ✅ **Proven behaviourally** — below |

New evidence this phase adds, which 2B.7 could not have had:

* **Real corpus scale:** `bytefray-rules-3-alpha1` is the **third-largest**
  identity in this checkout's artifact corpus — **6,984 `result.json` files**
  (13% of all results). Its historical readability is not hypothetical.
* **Behavioural proof of readability with the registry narrowed:**
  ```
  bytefray-rules-3-alpha1  hud=bytefray-rules-3-alpha1  ticks=400
                           cores=[A:8/8, B:8/8, C:0/8 CAPTURED@345]
  ```
  Full 400-tick reconstruction, correct label, correct three-entrant core
  integrity, correct capture tick — with the identity absent from the
  executable registry.
* **It participates in the shared core tables**, so its membership entries in
  `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS` must be
  **retained** even after its policy object is removed — that membership is
  precisely what makes the `A:8/8, B:8/8, C:0/8` derivation above possible.

**Disposition unchanged:** Class 1. Retire from execution in Scope A;
2B.7's §O batches are folded into §V.A.

---

## I. V4 Alpha1 findings

**Canonical identity:** `bytefray-rules-4-alpha1` (`rules.py:53`
`BYTEFRAY_RULESET_V4_ALPHA1_ID`). Introduced `f141521`, released
`v4.0.0-alpha1` (2026-08-31).

* **Unique behaviour: yes, genuinely.** It differs from the control on **two**
  policy fields — `core_placement="seat_spread"` (vs `seeded`) and
  `process_selection="priority"` (vs `round_robin`). Those are exactly the two
  semantics alpha2 changed. An alpha1 match is **not** reproducible under the
  control.
* **Shared implementation: total.** Both run `ProcessMatchController`; the
  difference is entirely policy-field-driven, and `process_runtime.py`
  contains no ruleset-ID branching at all. **Retiring alpha1 removes no
  gameplay code** — only its policy object, its registry entry, and its
  membership in `PROCESS_RULESET_IDS`,
  `_CORE_PLACEMENT_GUARDED_RULESET_IDS`, `_V2_METHODOLOGY_RULESET_IDS` and
  `DESIGNER_AUTO_TRACE_RULESET_IDS` — **plus** its entries in
  `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS`, **which must
  be retained** for historical replay display (§N).
* **Corpus weight: heavy.** **12,782 `result.json` files** — the second-largest
  identity, 24% of all results. Its historical recognition matters more than
  any other candidate except `rules-2`.
* **New-execution reachability:** CLI (all four), Designer
  Advanced/Development/Evaluation, low-level API. Never auto-selected.
* **Historical readability without executable registration: proven.**
  ```
  bytefray-rules-4-alpha1  hud=bytefray-rules-4-alpha1  ticks=7
                           cores=[A:8/8, B:0/8 CAPTURED@7]
  ```
* **Test coupling — the largest surprise in the impact data.** The v4
  *spectator* suites are heavy consumers: `test_v4_spectator_derivation.py`
  (35 failures under a narrowed registry), `test_v4_spectator_perspective.py`
  (23), `test_v4_spectator_fight_night.py` (19),
  `test_v4_spectator_director.py` (11), `test_v4_spectator_multi_entrant.py`
  (7), plus `client/tests/test_perspective.py` (11),
  `client/tests/test_fight_night.py` (7),
  `client/tests/test_replay_session.py` (7). The entire spectator subsystem was
  built during the alpha1 era and still executes its fixtures under that
  identity. This is the main reason Scope B is not as cheap as its
  zero-gameplay-code profile suggests: ~120 test outcomes must be re-pointed
  at the control, not deleted.

---

## J. V4 Alpha2 findings

**Canonical identity:** `bytefray-rules-4-alpha2` (`rules.py:71`
`BYTEFRAY_RULESET_V4_ALPHA2_ID`). Introduced `dec5e5c`, released
`v4.0.0-alpha2` (2026-09-01).

* **Did alpha2 effectively become stable Ruleset 4? Yes — verbatim.**
  `RULESET_V4`'s fields are copied field-for-field from `RULESET_V4_ALPHA2`
  (`ruleset_policy.py:416-439`, whose comment says so explicitly), and
  `placement._placement_draw`'s domain-separation payload is a fixed constant
  rather than the ruleset id — precisely so the two produce byte-identical
  placement. Verified live: both resolve to `seeded` / `round_robin` /
  `chunked/2/rotate=True` / API `{2}` / python-only.
* **Does the distinction survive only in identifiers/tests/history? Almost.**
  The only *intended* difference is compatibility identity. But it is not
  "only identifiers": the distinction is what the **release-blocking
  equivalence corpus measures**, and that corpus needs both executable.
* **Corpus weight: minimal.** **7 `result.json` files** — the smallest of any
  identity. The historical-recognition cost of retiring it is near zero.
* **Retiring alpha2 removes registration and tests, not gameplay code** —
  exactly as the charter's §9 anticipated. Stated plainly: *no gameplay code
  is deleted by retiring either v4 alpha; only policy objects, registry
  entries, table memberships, and tests.*
* **But it is the one candidate whose retirement damages the control's own
  evidence** (§E.2). Any phase that retires alpha2 **must** first convert
  `test_v4_stable_ruleset_equivalence.py` from a live two-identity comparison
  into a frozen-golden comparison (§V.B.2), or the V6 program loses its proof
  that the control is what it claims to be — a self-inflicted wound on the one
  thing this program exists to protect.

---

## K. Alias / fallback topology

**Complete alias inventory — there is exactly one alias in the entire system.**

| Alias | Resolves to | Mechanism | Scope |
| --- | --- | --- | --- |
| `evaluation-rules-1` | `bytefray-rules-1` | `rules._RULESET_ALIASES` (`rules.py:106-108`) via `normalize_ruleset_id` | **Comparison / attribution only.** Never rewrites a stored artifact; never consulted by `resolve_ruleset_policy`. |

Only **two** production call sites consume it: `agent_evaluation.py:607`
(`resolve_evaluation_ruleset_id`) and `evaluation_history/comparison.py:243`
(`_rules_id`). Verified still functional with the registry narrowed:
`normalize_ruleset_id('evaluation-rules-1') -> 'bytefray-rules-1'`.

**Derived alias (not in the alias table, easy to miss):**
`agent_evaluation.EVALUATION_RULES_COMPATIBILITY_ID = BYTEFRAY_RULESET_ID`
(`:166`). This makes `bytefray-rules-1` the **default `rules_compatibility_id`
of any `EvaluationRequest` with `ruleset_id=None`**
(`resolve_evaluation_ruleset_id:595-607`) — a fourth "missing → Ruleset 1"
mapping, at evaluation scope rather than match scope.

**Explicitly searched for and NOT found:** short names, enum values, version
aliases, migration maps, `latest`, `default`-as-an-identity, prefix/pattern
normalisation, and first-registered-wins behaviour. `resolve_ruleset_policy`'s
docstring disclaims all of these and direct execution confirms it.
`rules.py:99-105` states the design intent:

> "a finite, explicit historical-alias table — deliberately not a generic
> 'normalize any evaluation-rules-N-shaped string' function… an unrecognized
> string must never opportunistically normalize."

### K.1 Complete fallback topology

| ID | Site | Input | Output today | Output if target retired |
| --- | --- | --- | --- | --- |
| F-1 | `match_service._resolve_ruleset_id:525` | `MatchRequest(ruleset_id=None)` | `bytefray-rules-1` | unchanged — **still names a retired ID** |
| F-2 | `resolve_omitted_ruleset_for_agents:673` | empty roster | `bytefray-rules-1` | unchanged — **still names a retired ID** |
| F-3a | `resolve_omitted_ruleset_id:768` | empty kinds | `bytefray-rules-1` | unchanged |
| F-3b | `resolve_omitted_ruleset_id:782-783` | any roster no candidate supports | `bytefray-rules-1` (exception swallowed) | unchanged |
| K-1 | `resolve_evaluation_ruleset_id:605` | `EvaluationRequest(ruleset_id=None)` | `bytefray-rules-1` | unchanged |
| — | `OMITTED_RULESET_CANDIDATES` walk | API v1 roster | `bytefray-rules-2` | `NoCompatibleRulesetError` ✅ (clean) |
| — | `OMITTED_RULESET_CANDIDATES` walk | VM roster | `bytefray-rules-1` | `NoCompatibleRulesetError` ✅ (clean) |
| — | `OMITTED_RULESET_CANDIDATES` walk | API v2 roster | `bytefray-rules-4` | unchanged ✅ |

**Post-retirement requirement:** the alias table must **not** be extended or
re-pointed. Specifically — restating the charter's own instruction —
**historical `bytefray-rules-1` or `bytefray-rules-2` requests must never be
silently mapped to `bytefray-rules-4`.** They must fail with
`UnknownRulesetError` (or the cleaner `NoCompatibleRulesetError`), while the
alias continues to resolve historical *metadata* only.

---

## L. Current user-facing ruleset surfaces

| Surface | Source | Offers today | Derived or hardcoded? |
| --- | --- | --- | --- |
| `bytefray run --ruleset` | `cli.py:293-300` | v1, v2, v4a1, v4a2, v4 | **Hardcoded** list |
| `bytefray tournament --ruleset` | `tournament_cli.py:59-67` | identical 5 | **Hardcoded** |
| `bytefray agents test --ruleset` | `agent_test.py:1042-1050` | identical 5 | **Hardcoded** |
| `bytefray agents evaluate --ruleset` | `agent_evaluation.py:4383-4391` | identical 5 | **Hardcoded** |
| Evaluation low-level allow-list | `agent_evaluation.py:3392-3405` | the 5 **+ v3a1** | **Hardcoded** |
| Evaluation preset `ruleset:` field | `evaluation_presets.py:81` | **v1, v2 only** ⚠ | **Hardcoded** |
| Designer Simple | `ruleset_options.py:78` | v2, v4 | Hardcoded tuple |
| Designer Advanced / Development | `ruleset_options.py:106-111` | v2, v4, v4a2, v4a1, v1 | Hardcoded tuple |
| Designer Evaluation (pairwise) | `ruleset_options.py:94-100` | v2, v4, v4a2, v4a1, v1 | Hardcoded tuple |
| Designer pre-agent default | `ruleset_options.py:67` | **v4** | Constant |
| Designer auto-selection | `best_designer_ruleset_for_agents:187-202` | first supporting option — **v2 first** | Derived by walking the tuple |
| GUI explanatory prose | `ruleset_options.py:123-140` | names v2, v4, v4a2, v4a1, v1 | Hardcoded strings |
| Omitted `--ruleset` | `OMITTED_RULESET_CANDIDATES:625-629` | v2 → v4 → v1 | Hardcoded tuple |
| Designer spectator auto-trace | `designer_workflows.py:321-323` | v4a1, v4a2, v4 | Hardcoded frozenset |

**Key structural finding — and it is good news.** *No user-facing surface
derives its choices from the executable registry.* Every one is an explicit,
hand-maintained allow-list. This means:

* Removing a registry entry **cannot** silently change what any surface
  offers — the surfaces must be edited separately and deliberately. There is
  no risk of a registry edit quietly altering the GUI.
* Conversely, a surface left un-edited will keep **offering an identity the
  engine can no longer execute**, producing `UnknownRulesetError` at launch.
  Every surface above must be updated in lockstep (§V, trap T-10).
* Phase 2B.7 recorded the `DesignerRulesetOption` pattern as a *positive*
  finding worth propagating. That assessment holds and generalises: the
  Designer is the only surface whose product preference is expressed as data
  rather than as argparse literals.

The charter's post-retirement goal — *"a normal V6 user should not need to
choose among historical game engines"* — is achieved under Scope A+B by
reducing every list above to a single entry, and is **already true today** for
Designer Simple, which offers only current gameplay.

---

## M. Agent-package compatibility

**Finding: agent packages have zero ruleset coupling. There is nothing to
sever.**

`engine/src/battle_engine/agent_package.py` and `agent_package_cli.py` contain
the substring `ruleset` **zero times** (verified by direct count). The
`.bytefray-agent` manifest schema has no `ruleset_id`, `ruleset`,
`min_ruleset`, `supported_rulesets`, or ruleset-capability field of any kind.

`_check_compatibility` (`agent_package.py:671-698`) enforces exactly two axes:

* `kind` ∈ `SUPPORTED_KINDS`
* `agent_api_version` ∈ `SUPPORTED_AGENT_API_VERSIONS`
  (= `frozenset({1, 2})`, `agent_api.py:25`)

Therefore, for a package whose agent historically ran under a retired ruleset:

| Operation | Behaviour after retirement | Changes needed |
| --- | --- | --- |
| **Import** | Succeeds unchanged — decided by `kind`/`agent_api_version` only | none |
| **Inspect** | Succeeds unchanged | none |
| **Edit** | Succeeds unchanged | none |
| **Execute** | Scope A/B: unaffected. Scope C: an API v1 package raises `NoCompatibleRulesetError` from omitted-ruleset resolution — **a clean, explicit failure naming the agent and its runtime/API** (`ruleset_policy.py:551-583`) | Trim `OMITTED_RULESET_CANDIDATES`, else the error degrades to a less specific `UnknownRulesetError` later |

**V6 can therefore read package metadata, explain the situation, and refuse
execution clearly** — using machinery that already exists.
`NoCompatibleRulesetError` was designed for precisely this case ("fails closed
and says so, rather than selecting one entrant's Ruleset and letting the other
discover the mismatch later").

**No automatic migration to Ruleset 4 should be invented, and none is needed.**
Existing semantics prove *in*compatibility rather than compatibility: an Agent
API v1 agent implements `reset`/`act` against `Observation`, while
`bytefray-rules-4` requires the API v2 `declare_processes` contract. They are
not interchangeable, and a migration would be a rewrite, not a remap.

---

## N. Historical result/replay compatibility

**This is the retirement's principal safety criterion, and it is met —
demonstrated behaviourally against the repository's own corpus, not argued
from structure.**

### N.1 Structural proof: zero reader → registry coupling

Every historical-artifact reader was checked for any reference to
`ruleset_policy`, `resolve_ruleset_policy`, or `UnknownRulesetError`:

| Module | References |
| --- | ---: |
| `engine/src/battle_engine/result_model.py` | **0** |
| `engine/src/battle_engine/replay.py` | **0** |
| `engine/src/battle_engine/replay_history/index.py` | **0** |
| `engine/src/battle_engine/replay_history/query.py` | **0** |
| `engine/src/battle_engine/replay_history/discovery.py` | **0** |
| `app/services/replay_history_presentation.py` | **0** |
| `client/src/battle_client/session.py` | **0** |
| `client/src/battle_client/player.py` | **0** |

And the executable resolver has exactly **four** production call sites, all on
new-execution or pre-launch paths:

| Call site | Class |
| --- | --- |
| `ruleset_policy.py:531` (`agent_supported_by_ruleset`) | new-execution |
| `match_service.py:1419` (`NativeMatchService.run` dispatch) | new-execution |
| `placement.py:266` (`core_placement_mode`) | pre-launch |
| `app/services/ruleset_options.py:156` (`ruleset_supports_runtime_kinds`) | pre-launch (Designer guard) |

### N.2 Behavioural proof against the real corpus

The repository holds **53,458 `result.json`** and **44,547 `replay.jsonl`**
artifacts under `runs/`. Distribution by recorded identity:

| Recorded `ruleset_id` | Results | Share |
| --- | ---: | ---: |
| `bytefray-rules-2` | **31,053** | 58.1% |
| `bytefray-rules-4-alpha1` | **12,782** | 23.9% |
| `bytefray-rules-3-alpha1` | **6,984** | 13.1% |
| `bytefray-rules-4` (the control) | 1,910 | 3.6% |
| *(absent → recovered as `bytefray-rules-1`)* | 673 | 1.3% |
| `bytefray-rules-5-r1-alpha1` *(already retired)* | 42 | 0.1% |
| `bytefray-rules-4-alpha2` | 7 | <0.1% |
| `bytefray-rules-5-r2-alpha1` *(already retired)* | 7 | <0.1% |

Note the shape of this distribution: **the control accounts for 3.6% of the
corpus; retirement candidates and already-retired identities account for
96.4%.** Historical recognition is not a marginal concern here — it is what
almost the entire corpus depends on.

With `_RULESET_POLICIES` narrowed **in memory** to `{bytefray-rules-4}`, one
representative artifact per identity was driven through the complete reader
stack. All passed:

```
result envelope decode + attribution
  bytefray-rules-2             ruleset='bytefray-rules-2'            conf='recorded'  winner='A'
  bytefray-rules-4-alpha1      ruleset='bytefray-rules-4-alpha1'     conf='recorded'  winner='A'
  bytefray-rules-3-alpha1      ruleset='bytefray-rules-3-alpha1'     conf='recorded'  winner='A'
  bytefray-rules-4             ruleset='bytefray-rules-4'            conf='recorded'  winner='B'
  bytefray-rules-4-alpha2      ruleset='bytefray-rules-4-alpha2'     conf='recorded'  winner='A'
  bytefray-rules-5-r1-alpha1   ruleset='bytefray-rules-5-r1-alpha1'  conf='recorded'  winner='tie'
  bytefray-rules-5-r2-alpha1   ruleset='bytefray-rules-5-r2-alpha1'  conf='recorded'  winner='A'
  (no ruleset_id)              ruleset='bytefray-rules-1'            conf='recovered' winner='A'

replay load + FULL tick reconstruction + HUD label + per-entrant core status
  bytefray-rules-2             hud=bytefray-rules-2            ticks= 300  cores=[A:6/8, B:3/8, C:3/8]
  bytefray-rules-4-alpha1      hud=bytefray-rules-4-alpha1     ticks=   7  cores=[A:8/8, B:0/8 CAPTURED@7]
  bytefray-rules-3-alpha1      hud=bytefray-rules-3-alpha1     ticks= 400  cores=[A:8/8, B:8/8, C:0/8 CAPTURED@345]
  bytefray-rules-4             hud=bytefray-rules-4            ticks=  31  cores=[A:none, B:none]
  bytefray-rules-4-alpha2      hud=bytefray-rules-4-alpha2     ticks=   3  cores=[A:none, B:none]
  bytefray-rules-5-r1-alpha1   hud=bytefray-rules-5-r1-alpha1  ticks=1000  cores=[A:none, B:none]
  bytefray-rules-5-r2-alpha1   hud=bytefray-rules-5-r2-alpha1  ticks=  91  cores=[A:none, B:none]
  (no ruleset_id)              hud=bytefray-rules-1 (recovered) ticks= 300 cores=[A:none, B:none]

GUI Replay-History label derivation (shape-derived, no per-identity table)
  bytefray-rules-1         -> 'Ruleset v1'          bytefray-rules-4-alpha1    -> 'Ruleset v4 alpha1'
  bytefray-rules-2         -> 'Ruleset v2'          bytefray-rules-4-alpha2    -> 'Ruleset v4 alpha2'
  bytefray-rules-2-alpha1  -> 'Ruleset v2 alpha1'   bytefray-rules-4           -> 'Ruleset v4'
  bytefray-rules-2-alpha11 -> 'Ruleset v2 alpha11'  bytefray-rules-5-r1-alpha1 -> 'Ruleset v5 r1 alpha1'
  bytefray-rules-3-alpha1  -> 'Ruleset v3 alpha1'   bytefray-rules-5-r2-alpha1 -> 'Ruleset v5 r2 alpha1'

evaluation_history discovery + comparison gate
  evaluation-v2_017737c34addb8bb268d2aef  rules='bytefray-rules-2'  conf=RECORDED  health=HEALTHY
  evaluation-v2_548b34b9e339cab45dddca48  rules='bytefray-rules-2'  conf=RECORDED  health=HEALTHY
```

Note especially the three vulnerable-core rows: correct per-entrant core
integrity **and capture ticks** were derived for `rules-2`, `rules-3-alpha1`
and `rules-4-alpha1` with those identities unregistered — because
`replay_status.py` consults the *membership frozensets*, not the executable
registry. That is the execution/recognition separation working exactly as it
must, and it is also why trap T-9 matters so much.

### N.3 What must be retained for this to keep working

| Retained item | Why |
| --- | --- |
| All eight `BYTEFRAY_RULESET_*_ID` string constants | Referenced by readers, tables and tests as data |
| `rules._RULESET_ALIASES` + `normalize_ruleset_id` | Evaluation attribution |
| `resolve_result_ruleset` / `resolve_replay_ruleset` incl. the `recovered` branches | 673 artifacts depend on them |
| `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS` **memberships** | Replay core-status display |
| `has_vulnerable_core` | Called by `replay_status.py:180` |
| `ActionKind.MOVE` / `LOCAL_READ` / `LOCAL_WRITE`; `Observation.locus` | Historical trace/replay deserialisation (2B.7 §F) |
| `_readable_ruleset` shape-derived labeller | Handles any retired ID without a table |
| Replay schema 3 and trace schema v1 **read** support | Write-dead, read-live |

---

## O. Historical re-execution consequences

The charter's distinction is the right one, and this repository already
satisfies its cheap half.

| Capability | Status after retirement |
| --- | --- |
| **Historical readability** | **Fully preserved** — proven in §N for every candidate, at zero cost, with no shim |
| **Exact historical re-execution** | **Lost** for each retired identity, by design |

Per-candidate consequence, stated plainly as the charter requires:

| Identity | What is lost | Materiality |
| --- | --- | --- |
| `bytefray-rules-2-alpha1` | Re-running a v2.0.0-alpha.1 Vulnerable-Core match | Nil — closed research; never product-selectable |
| `bytefray-rules-2-alpha11` | Re-running a v2.0.0-alpha.11 match | Nil — same |
| `bytefray-rules-3-alpha1` | Re-running a v3 bounded-locality match | Low — closed research (`docs/archive/v3/`); the 6,984 artifacts stay readable |
| `bytefray-rules-4-alpha1` | Re-running a v4.0.0-alpha1 match (genuinely distinct gameplay) | Low–moderate — 12,782 artifacts stay readable; nothing current depends on re-running them |
| `bytefray-rules-4-alpha2` | Re-running a v4.0.0-alpha2 match | Low for users; **high for the control's proof** (§E.2) unless replaced |
| `bytefray-rules-2` | Re-running **any** Agent API v1 Python match, incl. all 31,053 historical ones and all 7 bundled v1 starters | **High — a live capability, not a historical one** |
| `bytefray-rules-1` | Re-running **any** VM/blob match, incl. the 4 bundled VM starters | **High — same** |

**The fallback is precise and worth stating in the changelog:** because the
ruleset registry is behaviourally unchanged since `v5.0.0` (§B.2), **the
`v5.0.0` release — its tag, wheel, and Windows installer — is the exact
historical engine for all eight identities.** No archaeology is required; it
is one `git checkout v5.0.0` or one installer download. This is materially
better than the situation the V5 R1/R2 retirement left behind, where the
research runner has to name a specific intermediate commit (`18e5ac6`).

Per the charter, loss of exact re-execution is **not treated as a blocker** for
Classes 1 and 2. For Class 3 it is not primarily a re-execution question at
all — it is the removal of a currently-shipped capability (§F.5, §G.2), which
is a different kind of decision.

---

## P. Test disposition map

### P.1 Measured impact — three scopes, not estimated

Rather than estimate, the canonical suite was executed **three times** with the
executable registry narrowed, via a **scratchpad-only pytest plugin**
(`-p <plugin>` on `PYTHONPATH`; **no repository file was created or
modified**). Baseline for all three: **3,713 collected across 158 files**.

| Scope | Identities removed from the registry | Passed | Failed | Errors | Skipped | **Execution-dependent outcomes** |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **A** | v2a1, v2a11, v3a1 | 3,533 | 160 | 2 | 20 | **162 (4.4%)** |
| **B** | A + v4a1, v4a2 | 3,342 | 351 | 11 | 20 | **362 (9.8%)** |
| **C (full)** | all but `bytefray-rules-4` | 2,943 | 750 | 80 | 20 | **830 (22.4%)** |

In every run `passed + failed + skipped == 3,713`, confirming the measurement
is complete and no tests were skipped by the plugin itself.

> **Read these numbers correctly.** They measure *execution dependence* — how
> many tests break when an identity stops being executable. They are **not**
> deletion counts. In a defining file, tests that do not themselves execute a
> match still go when the file goes (so the deletion count is *higher*); in a
> mixed file, a failing case is usually re-pointed rather than deleted (so the
> deletion count is *lower*).

### P.2 Scope A — complete per-file breakdown (160 failures + 2 errors)

| File | Collected | Failed | Disposition |
| --- | ---: | ---: | --- |
| `test_v3_phase2_locality_agents.py` | 70 | 57 | **REMOVE (whole file)** |
| `test_ruleset_v2_alpha11.py` | 37 | 24 | **REMOVE (whole file)** |
| `test_v3_phase2_locality_runtime.py` | 64 | 16 | **REMOVE (whole file)** |
| `test_ruleset_v2_promotion_equivalence.py` | 12 | 12 | **REMOVE — but see P.5** |
| `test_ruleset_v2_alpha1.py` | 19 | 12 | **REMOVE (whole file)** |
| `test_v2_alpha2_reactive_defender.py` | 15 | 11 | **REMOVE (whole file)** |
| `test_v3_phase2_locality_evaluation.py` | 22 | 4 | **REMOVE (whole file)** |
| `test_v2_alpha4_multi_entrant.py` | 10 | 3 | **REMOVE (whole file)** |
| `test_v2_alpha1_reference_agents.py` | 9 | 3 | **REMOVE (whole file)** |
| `test_v3_preflight_characterization.py` | 3 | 2 | **REMOVE (whole file)** |
| `test_v2_alpha8_core_tracker.py` | 24 | 2 | **REMOVE (whole file)** |
| `test_v2_alpha4_1_winner_semantics.py` | 12 | 1 | **REMOVE (whole file)** |
| **Defining subtotal** | **297** | **147** | |
| `test_ruleset_v2_runtime_compatibility.py` | 17 | 4 | REVIEW — prune v2a1/v2a11 rows |
| `test_v2_default_placement.py` | 28 | 2 | REVIEW — prune rows |
| `test_ruleset_v2.py` | 16 | 2 | REVIEW — prune rows |
| `client/tests/test_replay_status.py` | 22 | 2 | **REVIEW — re-point, never delete** (historical-readability file) |
| `test_v4_interleaved_scheduler.py` | 14 | 1 | REVIEW — drop one row |
| `test_v4_alpha2_placement.py` | 67 | 1 | REVIEW — drop one row |
| `test_ruleset_policy.py` | 49 | 1 | REVIEW — registry contract test |
| **Review subtotal** | **213** | **13** | |

The 12 defining files are exactly the files whose **entire subject** is a
Class-1 identity, confirmed by identity-usage analysis: each references
`v2a1`/`v2a11`/`v3a1` as its subject and touches `rules-1`/`rules-2` only for
contrast.

### P.3 Scope B delta — dominated by re-pointing, not deletion

The 200 additional outcomes introduced by retiring the two v4 alphas fall
almost entirely into "must be re-pointed at the control", not "can be deleted":

| File | Failed | Disposition |
| --- | ---: | --- |
| `test_v4_spectator_derivation.py` | 35 | **RE-POINT** at `bytefray-rules-4` — tests spectator derivation, not alpha1 |
| `test_v4_spectator_perspective.py` | 23 | **RE-POINT** |
| **`test_v4_stable_ruleset_equivalence.py`** | **23** | **CONVERT — see §V.B.2. Must not be deleted.** |
| `test_v4_spectator_fight_night.py` | 19 | **RE-POINT** |
| `test_agent_evaluation_v4.py` | 15 | REVIEW — prune alpha methodology rows |
| `test_v4_spectator_director.py` | 11 | **RE-POINT** |
| `client/tests/test_perspective.py` | 11 | **RE-POINT** |
| `test_v4_production_integration.py` | 8 | REVIEW — prune alpha rows |
| `test_v4_spectator_multi_entrant.py` | 7 | **RE-POINT** |
| `test_v4_alpha2_integration.py` | 7 of 8 | **REMOVE (whole file)** — the only genuine alpha-defining file |
| `client/tests/test_fight_night.py` | 7 | **RE-POINT** |
| `test_ruleset_agent_compatibility.py` | 4 | REVIEW |
| `test_designer_ruleset_options.py` | 3 | REVIEW — option-tuple assertions |
| `test_v4_trace_equivalence.py` | 2 | **RE-POINT** |
| **`test_v4_historical_immutability.py`** | **2** | **CONVERT — see §V.B.2** |
| `test_designer_workflows.py` | 2 | REVIEW — auto-trace frozenset |
| `client/tests/test_director.py` | 2 | **RE-POINT** |
| `test_agent_test.py` | 1 | REVIEW |
| `client/tests/test_perspective_card_knowledge.py` | 1 | **RE-POINT** |

**~116 of the 200 delta outcomes belong to the spectator subsystem**, which
was built during the alpha1 era and still fixtures its matches under that
identity. None of that is legacy gameplay code — it is current, supported
spectator functionality whose test fixtures happen to name an old ruleset.
**This is why Scope B is migration work, not deletion work**, and why it
should not be bundled into the same batch as Scope A.

### P.4 Classification (charter §15 categories)

**KEEP — Ruleset 4 control:** the eleven files in §E.3 (344 cases).

**KEEP — Historical readability** (must never be deleted; these are the
regression barrier for §N):

| File | Cases | Protects |
| --- | ---: | --- |
| `test_v5_replay_history_presentation.py` | 74 | Labels/filters for **seven** identities incl. already-retired `rules-5-r1-alpha1` |
| `client/tests/test_hud_layout.py` | 111 | HUD ruleset labels |
| `test_replay_history.py` | 89 | Index / query / facets |
| `client/tests/test_playback_controller.py` | 45 | Replay playback |
| `test_evaluation_history_comparison.py` | 47 | `rules_compatibility_id` gating across five identities |
| `client/tests/test_replay_status.py` | 22 | Core-status derivation for v1/v2/v2a1/v2a11 replays |
| `test_result_model.py` | 22 | Result envelope decode |
| `test_ruleset_persistence.py` | 20 | Recorded/recovered attribution |
| `test_rules.py` | 6 | Alias table, provenance vocabulary |

**REMOVE — legacy execution behaviour (Scope A):** the 12 defining files in
§P.2 — **297 cases**.

**REMOVE — closed research (Scope A):** the v3-locality fixtures, corpora and
drivers in §Q.1 (no additional test cases beyond the above).

**REVIEW — mixed purpose (Scope A):** the 7 files in §P.2's review subtotal —
**13 cases** to prune or re-point.

### P.5 A second-order equivalence-proof loss, one level down from T-8

`test_ruleset_v2_promotion_equivalence.py` (12 cases, all 12 failing under
Scope A) is the `bytefray-rules-2-alpha11` → `bytefray-rules-2` analogue of
the v4 equivalence corpus: it proves that the permanent Ruleset 2 identity is
gameplay-identical to the alpha it was promoted from.

Retiring `rules-2-alpha11` deletes that proof **while `bytefray-rules-2`
remains executable** — so under Scope A, Bytefray keeps a supported ruleset
whose promotion provenance is no longer test-backed. This is a milder version
of trap T-8 (the control is unaffected), but it should be a conscious choice:
either accept it and say so in the changelog, or convert the corpus to a
frozen-golden comparison the same way §V.B.2 specifies for v4.

### P.6 Test-count tripwire

| Scope | Expected collected count | Derivation |
| --- | --- | --- |
| Baseline | **3,713** | Measured |
| **A** | **3,403 – 3,416** | 3,713 − 297 (12 defining files) − 0…13 (review-file pruning) |
| B | *not a clean deletion figure* | Only `test_v4_alpha2_integration.py` (8) is deletable; ~200 outcomes are re-pointed, leaving the collected count roughly **3,395 – 3,410** |
| C | not recommended as one step | 830 outcomes affected; count depends on Agent-API-v1 decisions outside this phase |

**The Scope A tripwire to encode in Phase 2B.9 is `3,403 – 3,416`, with
`3,416` expected if no review-file case is removed and `3,403` if all thirteen
are.** The implementer must run `--collect-only` before and after **each
batch** and record the exact delta; a deviation is a finding to explain, not a
number to force.

---

## Q. Source / research-tool removal map

### Q.1 Full files removable

**Scope A — none in `engine/src`.** The three Class-1 identities own no whole
production file. Removable files are research tooling and fixtures only:

| Path | Kind | Reason |
| --- | --- | --- |
| `tools/v3_phase2_locality_corpus.py` | research driver | Only runs new v3a1 evaluations |
| `tools/v3_phase2_locality_rubric.py` | research driver | Same |
| `engine/src/battle_engine/data/v3_locality_agents/` (6 dirs) | fixtures | Consumed only by the deleted locality tests |
| `engine/src/battle_engine/data/benchmarks/v3_phase2_locality.json` | corpus | Declares `ruleset_id: bytefray-rules-3-alpha1` |
| `engine/src/battle_engine/data/benchmarks/v3_phase2_locality_corpus.json` | corpus | Same |

**Scope B additionally:** `tools/v4_alpha2_ecology_study.py`,
`tools/v4_r0c_rotation_qualification.py`, `tools/v4_scheduler_experiment.py`,
`tools/v4_scheduler_grain_sweep.py`.

**Scope C additionally:** `supervised_runtime.py` (557 LOC),
`builtins/registry.py` (146), `instructions.py` (14), plus
`tools/v3_phase1_arena_action_grid.py`,
`tools/v3_phase3_execution_invariance.py`,
`tools/v3_phase4_execution_invariance.py`.

### Q.2 Partial edits (Scope A)

| File | Edit | LOC |
| --- | --- | ---: |
| `ruleset_policy.py` | Remove `RULESET_V2_ALPHA1` (`:259-260`), `RULESET_V2_ALPHA11` (`:282-283`), `RULESET_V3_ALPHA1` (`:351-357`), their 3 `_RULESET_POLICIES` entries and 3 `__all__` entries. **Keep all three ID constants.** | ~35 |
| `python_runtime.py` | Locality block: constants + `has_bounded_locality` (`154-209`), circular helpers (`212-235`), locus state (`760-841`), validation branches (`878-955`), dispatch (`1000-1003`), `_apply_locality_action` (`1026-1073`), `record_locality_tick` (`1076-1108`), `locality_statistics` (`1111-1132`), reach guard (`1185-1192`), tick-loop call (`1459-1462`). **Keep `LOCALITY_ACTIONS`'s definition and its `:928-929` guard use.** | **250** |
| `match_service.py` | `_resolve_locality_reach` body (`475-479`), payload lines (`509-510`, `695`); remove v3a1 from `_CORE_PLACEMENT_GUARDED_RULESET_IDS` (`:412`) | 9 |
| `supervised_runtime.py` | Mirrored locality telemetry call (`434-437`) | 4 |
| `agent_evaluation.py` | Remove v3a1 from `_V2_METHODOLOGY_RULESET_IDS` (`:612-614`) and from the `_validate` allow-list (`:3392-3405`); `locality_reach` guard (`:3431-3438`) | ~20 |

**Scope A production LOC removable: ≈ 318**, of which 250 are in
`python_runtime.py` (~16% of that module) — independently consistent with
Phase 2B.7's measurement of 262 for the v3a1 portion alone.

**Registry/policy objects removable (Scope A):** 3 policy objects, 3 registry
entries, 1 one-member frozenset (`LOCALITY_RULESET_IDS`), 2 research drivers,
6 fixture directories, 2 benchmark corpora.

### Q.3 Shared code that must be retained — do NOT count as removable

* `apply_core_capture`, `_attribute_core_capture`, `core_addresses`,
  `CORE_SIZE` — used by `process_runtime.py:1269` for the control, and by
  `pygame_renderer.py`, `replay_status.py`, `match_service.py`, `placement.py`.
* `derive_agent_seed`, the entire `diagnose_*` block, `RuntimeDiagnostic` —
  imported by `process_runtime.py`.
* `vm.VM` — the **shared arena** (`_rd32`/`_wr8`/`ownership_counts`/memory
  diffs), imported by `process_runtime.py`. Only `VM.load_code`/`VM.step` are
  VM-agent-specific.
* **`VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS` membership
  entries for every retired identity** — required for historical replay
  core-status display (§N.2). **The most commonly mis-scoped item in the whole
  retirement** (trap T-9).
* `has_vulnerable_core` — called from `client/…/replay_status.py:180`.
* `LOCALITY_ACTIONS`'s definition and its rejection-guard use at `:928-929`.
* `ActionKind.MOVE`/`LOCAL_READ`/`LOCAL_WRITE`, `MatchContext.locality_reach`,
  `Observation.locus` — historical deserialisation.
* `spread_seat_starts` — used by `agent_evaluation` independently of any
  ruleset.

### Q.4 Research tools and fixtures (charter §17)

| Tool / fixture | Classification |
| --- | --- |
| `tools/research/v5/*` (`corpus_runner`, `analyzer`, `r3_runner`, `r4_runner`, `r4_population`) | **Required for frozen Ruleset 4 qualification** — all run under `bytefray-rules-4`. Retain. |
| `tools/research/v5/r1_runner.py`, `r2_runner.py` | **Already-retired-identity runners**, carrying literal IDs plus a comment naming the historical commit. **The pattern to copy** (§D.2). Retain as-is. |
| `tools/v3_phase2_locality_{corpus,rubric}.py` | **Obsolete execution-only tooling** — remove in Scope A |
| `tools/v4_alpha2_ecology_study.py`, `v4_r0c_rotation_qualification.py`, `v4_scheduler_experiment.py`, `v4_scheduler_grain_sweep.py` | Obsolete execution-only — Scope B |
| `tools/v3_phase1_arena_action_grid.py`, `v3_phase3_execution_invariance.py`, `v3_phase4_execution_invariance.py` | Obsolete execution-only — Scope C |
| `tools/v3_closeout_*.py`, `v3_phase6_defense_episode.py`, `v3_phase7_confound_isolation.py` | **Mixed** — use shared helpers (`core_addresses`, `apply_core_capture`) and mostly omit `ruleset_id`, thus hitting fallback F-1. Review case-by-case; do not bulk-delete. |
| `data/benchmarks/v2_baseline{,_corpus}.json`, `v3_phase1_arena_action_grid.json` | Declare `bytefray-rules-2`. **Retain under Scopes A/B**; Scope C strands them. |
| `data/benchmarks/v3_phase2_locality{,_corpus}.json` | Remove in Scope A |
| `data/benchmarks/v3_phase5a_*.json`, `v3_phase6_*.json` | Ruleset-neutral (`changes_ruleset: false`). Retain. |
| `data/v3_locality_agents/` (6 agents) | Remove in Scope A — pure test fixtures, no catalogue presence |

Per the charter: *"do not keep a closed research harness solely because it can
still run."* The v3-locality harness is closed research whose evidence is fully
preserved in `docs/archive/v3/` and whose 6,984 artifacts remain readable. It
should go with its identity.

---

## R. Documentation / changelog impact

### R.1 Classification

**KEEP / update for Ruleset 4:**

| Doc | Action |
| --- | --- |
| `docs/COMPATIBILITY.md` | Its "Current V5 product boundary" section enumerates the omitted-ruleset selection table and every Designer offering. **Must be updated in lockstep with §L's surfaces** or it becomes actively wrong. Add a short "Retired from execution / still recognised" table. |
| `docs/RULES_V4.md` | Add a sentence naming it the single executable V6 control and pointing at `bytefray-rules-6` as the future home of new semantics. Do **not** alter its gameplay description. |
| `README.md`, `AGENTS.md`, `SECURITY.md` | Trim retired IDs from "supported" phrasing only. |

**REMOVE the current-support claim** (these present a retired identity as
executable):

| Doc | Current framing | Scope |
| --- | --- | --- |
| `docs/RULES.md` | "the frozen gameplay-semantics contract Bytefray intends to carry through the 1.x series" — presented as current | C |
| `docs/RULES_V2.md` | "**Status: permanent, stable semantic identity**"; "describes the game as it plays today" | C |
| `docs/AGENT_AUTHORING.md`, `docs/AGENT_LAB.md`, `docs/AGENT_API_V2.md` | Reference v1/v2 as selectable | C (spot-check under A/B) |

**Under Scope A, documentation impact is close to nil.** The three Class-1
identities appear in **no** live current-support claim: `docs/RULES.md` and
`docs/COMPATIBILITY.md` contain zero mentions of `bytefray-rules-3-alpha1`
(2B.7 §K, re-confirmed here), and the two v2 alphas appear only in historical
narrative. This is a further argument for Scope A as the safe first step.

**KEEP historical (never erase):** `docs/archive/v1…v5/`, `docs/releases/`,
and all of `docs/research/`. These are the closed evidence record and are
already correctly past-tense.

**KEEP compatibility context:** `docs/RESULT_SCHEMA.md`,
`docs/REPLAY_SCHEMA.md`, `docs/specs/agent_package.md`, and
`docs/COMPATIBILITY.md`'s legacy matrix — these explain old artifact IDs and
become *more* important after retirement, not less.

### R.2 Recommended changelog framing (Scope A)

One `### Removed` entry, mirroring the Redcode/pMARS retirement's shape. No
migration system should be written, and none is needed (§M):

> **Retired from new execution:** `bytefray-rules-2-alpha1`,
> `bytefray-rules-2-alpha11`, and `bytefray-rules-3-alpha1` are no longer
> registered as executable rulesets. None was ever selectable from any CLI,
> Agent Designer, or evaluation-preset surface; they were reachable only
> through the low-level Python API.
>
> **`bytefray-rules-4` remains the supported gameplay baseline**, unchanged.
>
> **Historical results, replays, evaluations, and Replay History entries
> recorded under the retired identities remain fully readable, indexable,
> filterable, and replayable** — their identifiers are still recognised and
> labelled correctly. Only creating *new* matches under them is removed.
>
> **Exact re-execution of the retired engines remains available through the
> `v5.0.0` release** (tag, wheel, and Windows installer), whose ruleset
> registry is behaviourally identical to the one being trimmed here.

---

## S. Ruleset 6 future boundary

**This audit creates no Ruleset 6 code, placeholder, constant, or test.**

### S.1 Can Ruleset 6 be added cleanly after retirement? Yes — and retirement measurably helps

Adding a new executable identity today requires touching **up to 14 separate
tables** across four packages:

| # | Table | File |
| --- | --- | --- |
| 1 | ID constant | `rules.py` **or** `ruleset_policy.py` — *inconsistently* (§X.1) |
| 2 | Policy object + `_RULESET_POLICIES` | `ruleset_policy.py:487` |
| 3 | `PROCESS_RULESET_IDS` | `ruleset_policy.py:449` |
| 4 | `OMITTED_RULESET_CANDIDATES` | `ruleset_policy.py:625` |
| 5 | `_CORE_PLACEMENT_GUARDED_RULESET_IDS` | `match_service.py:409` |
| 6 | `_V2_METHODOLOGY_RULESET_IDS` / `_V4_METHODOLOGY_RULESET_IDS` | `agent_evaluation.py:612`, `:663` |
| 7 | Evaluation `_validate` allow-list | `agent_evaluation.py:3392` |
| 8 | `_VALID_RULESETS` | `evaluation_presets.py:81` |
| 9 | `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS` | `python_runtime.py:128`, `:144` |
| 10 | `LOCALITY_RULESET_IDS` | `python_runtime.py:194` |
| 11 | Four CLI `choices=` lists | `cli.py`, `tournament_cli.py`, `agent_test.py`, `agent_evaluation.py` |
| 12 | Three Designer option tuples + default + two prose strings | `app/services/ruleset_options.py` |
| 13 | `DESIGNER_AUTO_TRACE_RULESET_IDS` | `app/services/designer_workflows.py:321` |
| 14 | Replay-schema selection (via `PROCESS_RULESET_IDS`) | `match_service.py:1212` |

After Scope A, table 10 disappears entirely and tables 6 and 9 shrink; after
Scope A+B, tables 3, 5, 9 and 13 collapse to a single member and tables 11 and
12 become one-entry lists. Adding Ruleset 6 changes from "extend fourteen
heterogeneous allow-lists, several of which encode a superseded product
history" to "add a second entry alongside the control". **That is the
concrete, measurable sense in which this retirement makes Ruleset 6 cleaner.**

### S.2 Couplings that would make Ruleset 6 inherit historical baggage

Recorded for Phase 3, not remediated here:

1. **The four fallbacks in §K.1** would make a Ruleset-6-era omitted selection
   silently resolve to a retired identity if left in place.
2. **`RulesetPolicy.CORE_PLACEMENT_MODES` / `PROCESS_SELECTION_MODES`** are
   `ClassVar` allow-lists validated in `__post_init__`. A Ruleset 6 with new
   placement or selection semantics must extend them — a correct design, but
   it means new gameplay cannot live purely in a new module.
3. **`evaluation_presets._VALID_RULESETS` does not contain the control.** Any
   Ruleset 6 work should fix this rather than inherit it.
4. **The V5 constraint recorded at `ruleset_policy.py:611-624` is exactly
   right and must be honoured for Ruleset 6:** an experimental identity must
   require *explicit* selection and must never be added to
   `OMITTED_RULESET_CANDIDATES`, because silently reassigning the omitted slot
   to an experimental identity would contaminate every comparison against the
   frozen control.
5. **The two-file identity split** (§X.1) means a Ruleset 6 author must know,
   without a rule to guide them, whether the constant belongs in `rules.py` or
   `ruleset_policy.py`.

---

## T. Quantified simplification

### Before (today)

| Dimension | Count |
| --- | ---: |
| Executable ruleset identities | **8** |
| Identities with **zero** product exposure (registry lies about reachability) | **3** |
| Aliases | 1 (+1 derived: `EVALUATION_RULES_COMPATIBILITY_ID`) |
| Fallback mappings to a legacy identity | **4** (F-1, F-2, F-3, K-1) |
| User-visible ruleset choices | **5** (CLI) / **5** (Designer Adv.) / **2** (preset file) |
| Ruleset-ID allow-list tables in production code | **14** |
| `core_placement` modes in use | 3 (`zero`, `seat_spread`, `seeded`) |
| `process_selection` modes in use | 2 |
| Scheduler modes in use | 2 |
| Agent API generations executable | 2 |
| Runtime kinds executable | 2 (`python`, `vm`) |
| Ruleset-specific test clusters | 12 defining files + ~10 mixed |
| Canonical tests | 3,713 |

### After Scope A (recommended for Phase 2B.9)

| Dimension | Count | Δ |
| --- | ---: | --- |
| Executable ruleset identities | **5** | −3 |
| Identities with zero product exposure | **0** | **−3 — the registry stops lying about what is reachable** |
| Ruleset-ID allow-list tables | 13 | −1 (`LOCALITY_RULESET_IDS` gone) |
| Production LOC removed | **≈ 318** | |
| Research drivers / fixture dirs / corpora removed | 2 / 6 / 2 | |
| Canonical tests | **3,403 – 3,416** | −297 to −310 |
| User-visible choices | unchanged (5 / 5 / 2) | the retired three were never offered |
| Execution-dependent tests removed | 162 outcomes | measured |

### After Scope A + B

| Dimension | Count |
| --- | ---: |
| Executable ruleset identities | **3** (`rules-1`, `rules-2`, `rules-4`) |
| CLI choices | **3** |
| Designer Advanced choices | **3** |
| `PROCESS_RULESET_IDS` | **1 member** |
| `DESIGNER_AUTO_TRACE_RULESET_IDS` | **1 member** |
| Tests re-pointed at the control | ~200 outcomes |

### After Scope A + B + C (the charter's stated target)

| Dimension | Count |
| --- | ---: |
| **Executable ruleset identities** | **1 — `bytefray-rules-4`** |
| Aliases reaching an executable identity | **0** |
| Fallbacks reaching an executable identity | **0** (all four must be rewritten) |
| User-visible ruleset choices | **0–1** (the selector becomes vestigial) |
| Agent API generations executable | **1** (v2) |
| Runtime kinds executable | **1** (`python`) |
| Ruleset-ID allow-list tables | ~6 |
| Historically-recognised-only identities | **9** (7 retired + 2 V5 research IDs) |
| Bundled starter agents that still run | **10 of 21** |

The charter is right that the goal "is not merely deleting files; it is making
the active game model obvious." **Scope A delivers most of that clarity for a
fraction of the risk**, because the confusion it removes — three registered,
executable, undocumented identities that no surface offers — is precisely the
gap between what the registry says and what the product does.

---

## U. Compatibility traps

Every trap below is confirmed by direct execution or exact source citation.
All must appear in the Phase 2B.9 work order.

| # | Trap | Evidence | Required mitigation | Scope |
| --- | --- | --- | --- | --- |
| **T-1** | **Empty roster → `bytefray-rules-1`.** `resolve_omitted_ruleset_for_agents` returns the retired ID even with the registry narrowed. | Executed: `empty roster -> 'bytefray-rules-1'` | Change to raise, or return the control, as an explicit decision. Add a test. | C |
| **T-2** | **`resolve_omitted_ruleset_id` returns `bytefray-rules-1` for *every* input**, including `{'python'}` and `{'vm'}`, because it swallows `NoCompatibleRulesetError`. | Executed: all three cases | Rewrite the fallback; zero in-tree callers, so blast radius is out-of-tree only. | C |
| **T-3** | **`MatchRequest(ruleset_id=None)` dispatches, hashes and persists as `bytefray-rules-1`.** | `match_service.py:525` | Re-point `_resolve_ruleset_id` at the control **or** make it raise. **Either change silently re-points every existing `match_id` derivation** — do it deliberately and pin it with a test. | C |
| **T-4** | **Placement silently degrades to `zero` for an unregistered ID.** Measured: `resolve_direct_match_starts(rules-2, 3 seats, 4096)` returns `(0, 1365, 2730)` today and **`(0, 0, 0)`** with the registry narrowed — every core stacked on address 0. | Executed | Currently masked because `NativeMatchService.run` raises first. Add a test pinning that a retired ID never reaches placement, or make `core_placement_mode` fail closed. | A |
| **T-5** | **`tournament_service._place_pair` uses the same fail-safe** (`:449`), so a retired ID silently takes the non-seeded branch. | `tournament_service.py:449` | As T-4. | A |
| **T-6** | **`agent_scaffold.DEFAULT_API_VERSION = 1`** — under Scope C, `bytefray agents create` produces an unrunnable agent by default. The module's own comment forbids repointing an established command's default. | `agent_scaffold.py:53` | **Scope C blocker.** Requires an explicit product decision, not a code edit. | C |
| **T-7** | **`evaluation_presets._VALID_RULESETS = ("bytefray-rules-1", "bytefray-rules-2")`** — the control is not a legal preset value; both legal values are Class-3 legacy. | `evaluation_presets.py:81` | Under Scope C every ruleset-declaring preset breaks. Add the control — a real gap today regardless of scope. | C (fix anytime) |
| **T-8** | **Retiring alpha2 breaks the release-blocking control-equivalence corpus** (23/27 cases). | Measured (Scope B) | Convert to frozen-golden comparison **before** retiring alpha2 (§V.B.2). | B |
| **T-9** | **Removing `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS` memberships would break historical replay core display** for 50,800+ artifacts — **silently**, with no exception: cores would simply render as absent. | §N.2 | **Never** remove membership entries; only the *policy objects* go. Pin with a test. | A, B, C |
| **T-10** | **Surfaces do not derive from the registry**, so any un-edited CLI/Designer list keeps offering an unexecutable identity → `UnknownRulesetError` at launch. | §L | Edit all 14 surfaces in lockstep with the registry. | A, B, C |
| **T-11** | **`EVALUATION_RULES_COMPATIBILITY_ID = BYTEFRAY_RULESET_ID`** — an omitted-ruleset `EvaluationRequest` stamps `rules_compatibility_id: "bytefray-rules-1"`. | `agent_evaluation.py:166`, `:595-607` | Must keep working for historical attribution; must not start meaning "the control". | C |
| **T-12** | **Never map a retired ID to the control.** Forbidden by the charter and by `rules.py`'s own alias-table doctrine. | `rules.py:99-108` | Add a negative test: `resolve_ruleset_policy(<retired>)` raises **and** `normalize_ruleset_id(<retired>)` returns it unchanged. | A, B, C |
| **T-13** | **`rules-2-alpha1`/`-alpha11` claim Agent API v2 support** (`supported_python_api_versions=None`) but are absent from `PROCESS_RULESET_IDS`, so an API v2 roster would dispatch to the API v1 runtime. | Executed | Retiring them in Scope A removes the inconsistency for free. | A |
| **T-14** | **Replay schema 3 and trace schema v1 become write-dead** once non-process rulesets are retired. | `match_service.py:1212`, `:1474` | Read support must remain. Pin with a historical-artifact test. | C |
| **T-15** | **Retiring `rules-2-alpha11` deletes the Ruleset-2 promotion-equivalence proof while `rules-2` stays executable.** | §P.5, measured 12/12 | Accept consciously and note in the changelog, or convert the corpus to frozen-golden. | A |
| **T-16** | **~116 spectator-suite outcomes fixture their matches under `rules-4-alpha1`.** Deleting them instead of re-pointing would silently drop coverage of *current, supported* spectator functionality. | §P.3, measured | Re-point at the control; do not delete. | B |

---

## V. Dependency-ordered Phase 2B.9 implementation plan

The order below is derived from actual dependency direction in this
repository, and follows the batching discipline Phases 2B.5/2B.6 established.

### Scope A — recommended content of Phase 2B.9

| # | Batch | Contents | Why here | Verify |
| --- | --- | --- | --- | --- |
| **A-0** | Snapshot | Record HEAD, `git status`, `--collect-only` = **3,713**, and this report's tripwire (**3,403–3,416**) | Baseline for every later delta | `pytest --collect-only -q` |
| **A-1** | Registry | Remove `RULESET_V2_ALPHA1`, `RULESET_V2_ALPHA11`, `RULESET_V3_ALPHA1` policy objects, their `_RULESET_POLICIES` entries and `__all__` entries. **Keep all three ID string constants. Do not touch `VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS` memberships (T-9).** | The one change that actually retires new execution; everything else already excludes these three | `resolve_ruleset_policy(<each>)` raises `UnknownRulesetError`; CLI/GUI unaffected (they never offered them) |
| **A-2** | Evaluation allow-lists | Remove v3a1 from `agent_evaluation._V2_METHODOLOGY_RULESET_IDS` (`:612-614`) and from the `_validate` allow-list (`:3392-3405`); remove the `locality_reach` guard (`:3431-3438`) | A-1 alone would leave an allow-list naming an unregistered identity, degrading the error message | Construct an `EvaluationRequest` naming a retired ID; confirm `EvaluationConfigurationError` names it explicitly |
| **A-3** | Research drivers | Delete `tools/v3_phase2_locality_corpus.py`, `tools/v3_phase2_locality_rubric.py` | Depends on A-1/A-2; leaving them ships a broken internal tool | Confirm zero remaining importers |
| **A-4** | Tests — defining | Delete the **12 files** in §P.2 (**297 cases**) | Must follow A-1..A-3 or they fail rather than being cleanly removed | `--collect-only` → expect **3,416** |
| **A-5** | Tests — review | Prune the **13 cases** in §P.2's review subtotal. **`client/tests/test_replay_status.py`: re-point at stored fixtures, never delete** (it is historical-readability coverage) | Independent of A-4; these files primarily test other identities | Each file still passes in full; `--collect-only` → **3,403–3,416** |
| **A-6** | Mechanic cleanup | Remove the 250 dead locality lines from `python_runtime.py`, 9 from `match_service.py`, 4 from `supervised_runtime.py` (§Q.2). **Preserve `LOCALITY_ACTIONS`'s definition, the `ActionKind` members, `MatchContext.locality_reach`, `Observation.locus`.** | Depends on A-1 and A-4 — nothing may still call the removed functions | Full suite green; `mypy` clean |
| **A-7** | Fixtures / corpora | Delete `data/v3_locality_agents/` (6 dirs) and `data/benchmarks/v3_phase2_locality{,_corpus}.json` | Depends on A-3/A-4 (their only consumers) | Confirm zero remaining references |
| **A-8** | Safety tests (**additive**) | Add: (a) negative test — each retired ID raises `UnknownRulesetError` **and** `normalize_ruleset_id` returns it unchanged (T-12); (b) a historical-readability test asserting a stored artifact of each retired ID still reads, labels and replays (T-9); (c) a test that a retired ID never reaches `core_placement_mode` (T-4/T-5) | These convert this audit's behavioural proofs into permanent regression barriers | New tests pass; count rises by the number added — **record it explicitly in the tripwire** |
| **A-9** | Docs / changelog | `CHANGELOG.md` entry per §R.2; add the "retired from execution / still recognised" table to `docs/COMPATIBILITY.md` | Records the completed retirement | — |
| **A-10** | Residue scan | `git grep` each retired ID; confirm every surviving hit is a *string constant, historical doc, or recognition test* — never an executable registration | Catches missed surfaces | Manual review of the hit list |
| **A-11** | Qualification | §W | Nothing left to change | §W |

**Two-commit compression if fewer commits are wanted:** (A-1 + A-2 + A-3)
*retire the three identities from new execution*; (A-4 … A-9) *remove the dead
mechanic, its tests and fixtures, and record the change*.

### Scope B — a separate phase, not a batch of Scope A

| # | Batch | Contents |
| --- | --- | --- |
| **B-1** | **Preserve the control's proof first** | Convert `test_v4_stable_ruleset_equivalence.py` (27) and `test_v4_historical_immutability.py` (4) from live two-identity comparisons into **frozen-golden** comparisons: check in the alpha2-side replay/result artifacts produced *before* retirement, and assert the control reproduces them byte-for-byte. **This batch must land and pass before B-2.** (T-8) |
| **B-2** | Re-point spectator fixtures | Change the ~116 spectator outcomes (§P.3) to fixture under `bytefray-rules-4`. **Re-point, do not delete** (T-16). |
| **B-3** | Registry | Remove `RULESET_V4_ALPHA1`, `RULESET_V4_ALPHA2` + entries in `PROCESS_RULESET_IDS`, `_CORE_PLACEMENT_GUARDED_RULESET_IDS`, `_V2_METHODOLOGY_RULESET_IDS`, `_V4_METHODOLOGY_RULESET_IDS`, `DESIGNER_AUTO_TRACE_RULESET_IDS`. **Keep the two `VULNERABLE_CORE`/`OBSERVABLE_CORE` memberships for alpha1** (T-9). |
| **B-4** | Surfaces | Remove both alphas from four CLI `choices=` lists, `EVALUATION_RULESET_OPTIONS`, `DESIGNER_RULESET_OPTIONS`, and the two GUI prose strings (T-10). |
| **B-5** | Tools / tests / docs / qualification | Delete `test_v4_alpha2_integration.py` and the four v4 research tools; prune review cases; changelog; full qualification. |

### Scope C — gated, not scheduled

**Scope C must not be planned as an implementation phase until the product
question it contains is answered.** The decision is not "should old rulesets
be executable" — that is settled — but:

> **Is Agent API v1, and with it the VM/blob runtime, retired from Bytefray V6?**

If yes, Scope C is a coherent phase that should also cover: the 7 API-v1 and 4
VM starter agents, the 4 reference agents, `DEFAULT_API_VERSION` (T-6),
`_VALID_RULESETS` (T-7), the three v2 benchmark corpora, `docs/RULES.md` /
`docs/RULES_V2.md`, and all four fallbacks (T-1, T-2, T-3, T-11).

If no, `bytefray-rules-1` and `bytefray-rules-2` must remain executable, and
the V6 policy should be restated as: **one executable *process-gameplay*
control (`bytefray-rules-4`), plus the frozen Agent API v1 compatibility
rulesets.** That is still a large, real simplification from eight identities
to three, and it is fully delivered by Scopes A + B.

---

## W. Exact qualification plan and test-count tripwire

Success criteria for Phase 2B.9 (Scope A). Each is a check the implementer
must actually run, not assert.

### W.1 New execution

* `resolve_ruleset_policy(id)` raises `UnknownRulesetError` for
  `bytefray-rules-2-alpha1`, `bytefray-rules-2-alpha11`,
  `bytefray-rules-3-alpha1`.
* Each retired ID is absent from `_RULESET_POLICIES`, `PROCESS_RULESET_IDS`,
  `LOCALITY_RULESET_IDS` (which should no longer exist),
  `_V2_METHODOLOGY_RULESET_IDS`, and the evaluation `_validate` allow-list.
* `bytefray-rules-4`, `-1`, `-2`, `-4-alpha1`, `-4-alpha2` still resolve.

### W.2 Ruleset 4 immutability

* `resolve_ruleset_policy("bytefray-rules-4")` returns fields identical to
  today: `seeded` / `round_robin` / `chunked` / chunk 2 / rotate `True` /
  API `{2}` / python-only.
* `test_v4_stable_ruleset_equivalence.py` (27) passes **unmodified**.
* `test_v4_runtime_default_ruleset.py` (10), `test_v4_historical_immutability.py`
  (4), `test_v4_alpha2_scheduler.py` (18), `test_v4_process_semantics.py` (5),
  `test_v4_trace_equivalence.py` (2) all pass unmodified.
* A control match run before and after the change produces a byte-identical
  `replay.jsonl` and identical `match_id`/`result_id`/`replay_id`.

### W.3 Defaults

* `resolve_omitted_ruleset_for_agents(None, [{"kind":"python","api_version":2}])`
  → `bytefray-rules-4`; API v1 → `bytefray-rules-2`; VM → `bytefray-rules-1`
  (all **unchanged** under Scope A).
* `DEFAULT_DESIGNER_RULESET_ID` still `bytefray-rules-4`.
* All four CLI `--help` outputs unchanged (the retired three were never listed).

### W.4 Historical readability

Reproduce this audit's §N proof against the post-change tree:

```
python -m pytest --collect-only -q                      # tripwire
# behavioural readability probe (scratchpad script, not committed):
#   for each retired identity, take one artifact from runs/ and assert
#   read_result / resolve_result_ruleset / iter_replay / ReplaySession.load /
#   get_entrant_statuses / resolve_match_ruleset_label / _readable_ruleset
#   all succeed and return the recorded identity
```

Representative artifacts confirmed present in this checkout:

| Identity | Artifact |
| --- | --- |
| `bytefray-rules-3-alpha1` | `runs/research_v3_phase2/main/results/G_a4096_b2/group/lcamper_ltracker_ldefender/matches/0001-group-…/result.json` |
| `bytefray-rules-2` | `runs/evaluations/evaluation-v2_017737c34addb8bb268d2aef/matches/0001-group-…/result.json` |
| `bytefray-rules-4-alpha1` | `runs/agents_test/hydra_alpha2/20260901T115454765947-74fd58f9-vs-reference/result.json` |
| *(recovered v1)* | `runs/agents_test/claimer/20260811T191229762851-b984d2dc-vs-strider/result.json` |

Expected: **identical output to §N.2** for every row.

### W.5 Explicit failure

* `NativeMatchService.run` with a retired `ruleset_id` raises
  `UnknownRulesetError` **before** any artifact is written to `replay_path`.
* No retired ID is ever silently replaced by `bytefray-rules-4`
  (`normalize_ruleset_id(<retired>)` returns it unchanged) — T-12.

### W.6 Package behaviour

* Import/inspect/edit of any agent package is unchanged (no ruleset coupling
  exists — §M). Under Scope A no package behaviour changes at all.

### W.7 Test count

| Milestone | Expected |
| --- | ---: |
| Before any change | **3,713** |
| After A-4 (12 defining files deleted) | **3,416** |
| After A-5 (review pruning) | **3,403 – 3,416** |
| After A-8 (safety tests added) | 3,403–3,416 **+ N added**, with N recorded explicitly |

Run `--collect-only` **before and after each batch**. Any deviation is a
finding to explain in the Phase 2B.9 report, never a number to force.

### W.8 Quality

* `python -m pytest` → green (expect ~3,393–3,406 passed, 20 skipped, 0 failed).
* `mypy engine/src/battle_engine` → clean; `mypy client/src/battle_client` → clean.
* `ruff check .` → clean. **Delete any custom `--basetemp` directory first** —
  Phase 0 §4 records that `ruff` is not configured to exclude them.

---

## X. Phase 3 findings

Recorded, not remediated — direct input to Phase 3 context-locality research.

1. **Ruleset identity constants are split across two modules with no stated
   rule.** `bytefray-rules-1`, `-4-alpha1`, `-4-alpha2`, `-4` live in
   `rules.py`; `-2`, `-2-alpha1`, `-2-alpha11`, `-3-alpha1` live in
   `ruleset_policy.py`. A Ruleset 6 author has no guidance on where a new
   constant belongs.
2. **Executable registration and historical recognition are conflated in the
   same *kind* of table.** `_RULESET_POLICIES` (execution) and
   `VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS` (execution
   *and* recognition simultaneously, for different identities) are structurally
   identical frozensets serving different lifetimes. This audit found the
   boundary separable by hand, but it is the single highest-risk item in every
   scope (T-9). Phase 3 should consider an explicit
   `historically_recognised_ids` table distinct from the executable registry.
3. **`replay_status.py` reaches into `python_runtime.py`** — a module otherwise
   entirely about live execution — for what is conceptually a *display
   classification* concern. Carried forward from 2B.7 §P.4 and reconfirmed.
4. **Fourteen allow-list tables encode ruleset identity** (§S.1), three of them
   duplicating the same product-preference order (`OMITTED_RULESET_CANDIDATES`,
   `DESIGNER_RULESET_OPTIONS`, `EVALUATION_RULESET_OPTIONS`). No surface
   derives from the registry — deliberate and safe (§L), but the duplication is
   real and unmanaged.
5. **Four independent "missing → Ruleset 1" fallbacks** exist at four different
   layers (§K.1). None shares an implementation with the others.
6. **`rules-2-alpha1`/`-alpha11` advertise Agent API v2 support they cannot
   deliver** (T-13) — a latent defect that only stayed harmless because those
   identities are unreachable from every product surface.
7. **`evaluation_presets._VALID_RULESETS` has not tracked the product since
   v2.0.0-beta2** (T-7): it names only v1/v2 and excludes the current control.
8. **The v4 spectator subsystem's test fixtures are pinned to a prerelease
   identity** (§P.3) — ~116 outcomes that describe current functionality under
   a historical ruleset name.
9. **Equivalence corpora are structurally coupled to the continued
   executability of the superseded identity** — true for v2a11→v2 (§P.5) and
   v4a2→v4 (§E.2). A promotion-proof pattern based on frozen golden artifacts
   rather than live dual execution would decouple the two permanently, and is
   the single most reusable improvement Phase 3 could specify.

---

## Y. Risks / unresolved questions

1. **The Scope A tripwire is a 13-case range (3,403–3,416), not a single
   number.** The exact figure depends on whether review-file cases are pruned
   or re-pointed — a judgement the implementer makes per case. Resolved by
   running `--collect-only` per batch, as §W.7 requires.
2. **The three narrowed-registry measurements are dependence measures, not
   deletion counts** (§P.1). They are exact for what they measure, and this
   report does not use them as removal totals anywhere. Anyone reusing the
   162/362/830 figures must preserve that distinction.
3. **Scope C is not costed here beyond its 830-outcome test impact**, because
   its real cost is a product decision (Agent API v1's future) whose
   consequences — starter-agent portfolio, scaffold default, documentation set
   — extend well past ruleset retirement. Costing it before the decision would
   be speculative.
4. **This report's line-number citations should be re-verified immediately
   before implementation.** No commit landed between evidence-gathering and
   writing in this session, but time may pass. This is the same standing
   caution 2B.7 recorded, and it applies with equal force here.
5. **The V5 R1/R2 precedent was verified as a pattern, not as a full
   equivalence.** Those two identities had no product exposure, no bundled
   agents, and 49 artifacts; `bytefray-rules-1`/`-2` have all three. The
   pattern (registry removal + negative test + readability test + runner
   comment) transfers; the *scale* does not.
6. **Whether to accept the loss of the Ruleset-2 promotion-equivalence proof
   under Scope A (T-15) is an open decision**, deliberately left to the user
   rather than assumed. The cheap option is to accept it and say so; the
   thorough option is a frozen-golden conversion mirroring §V.B.1.
7. **No genuine risk to historical-artifact compatibility was found** — and
   this is an checked-not-assumed conclusion, per this program's evidence
   standard: every reader module was grepped for registry coupling (§N.1) and
   every candidate identity's real artifacts were driven through the full
   reader stack with the registry narrowed (§N.2).
8. **The untracked Phase 2B.7 report (§B.1) remains uncommitted.** It was left
   exactly as found. It has no bearing on any finding here, but the audit trail
   is discontinuous until it is committed.

---

## Appendix: reproduction commands

```bash
git rev-parse --abbrev-ref HEAD                 # v6-research
git rev-parse HEAD                              # c74d6c67faca36f6394cb0a258687a8774dc48b4
git fetch origin v6-research main
git rev-list --left-right --count origin/v6-research...HEAD   # 0  0
git diff v5.0.0..HEAD -- engine/src/battle_engine/rules.py \
                          engine/src/battle_engine/ruleset_policy.py   # comment-only

python -m pytest --collect-only -q              # sums to 3,713 across 158 files

# Registry / policy matrix
python -c "from battle_engine import ruleset_policy as rp; print(sorted(rp._RULESET_POLICIES))"

# Executable-resolver call sites (expect exactly 4 production call sites)
git grep -n 'resolve_ruleset_policy(' -- engine/src client/src app tools

# Reader modules must have zero registry coupling
git grep -c 'ruleset_policy' -- engine/src/battle_engine/result_model.py \
    engine/src/battle_engine/replay.py engine/src/battle_engine/replay_history/ \
    client/src/battle_client/session.py app/services/replay_history_presentation.py

# Corpus distribution by recorded identity
#   (walks runs/**/result.json; 53,458 files in this checkout)

# Scope measurements — scratchpad-only plugin, no repo file created:
#   plugin body:  def pytest_configure(config):
#                     from battle_engine import ruleset_policy as rp
#                     rp._RULESET_POLICIES = {k: v for k, v in rp._RULESET_POLICIES.items()
#                                             if k not in RETIRE}
PYTHONPATH=<scratchpad> python -m pytest -p narrow_A -q --basetemp=.pytest-tmp-2b8A -rf
PYTHONPATH=<scratchpad> python -m pytest -p narrow_B -q --basetemp=.pytest-tmp-2b8B -rf
PYTHONPATH=<scratchpad> python -m pytest -p narrow_plugin -q --basetemp=.pytest-tmp-2b8narrow -rf
#   A: 3,533 passed / 160 failed / 2 errors / 20 skipped
#   B: 3,342 passed / 351 failed / 11 errors / 20 skipped
#   C: 2,943 passed / 750 failed / 80 errors / 20 skipped
#   (delete every .pytest-tmp-* directory afterwards — they are NOT gitignored
#    and ruff does not exclude them)
```
