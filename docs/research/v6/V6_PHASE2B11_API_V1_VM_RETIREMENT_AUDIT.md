# Bytefray V6 — Phase 2B.11: Agent API v1 / VM Runtime Retirement Audit

**Phase type:** Research-only. No ruleset, runtime, registry, starter agent,
reference agent, scaffold, test, package, CLI/GUI surface, or document outside
this report was modified. The only tracked change this phase produces is this
file.

**Governing product direction (given, not re-litigated):** Bytefray intends to
retire Agent API v1 execution and VM/blob execution from the V6 runtime,
leaving `bytefray-rules-4` as the sole currently executable control ruleset
before Ruleset 6 research begins. The eventual model is **one active agent
architecture, one active baseline ruleset, historical artifacts still
readable**.

This audit determines whether that transition is technically safe, exactly what
must be removed, and what historical-reader behaviour must remain. It
implements none of it.

**Evidence standard applied.** Prior phase reports were treated as input to be
re-verified, not as truth. Every structural claim below was re-derived from
current source at HEAD `551cf5a`, and every behavioural claim was produced by
executing code in this checkout. Where a prior report's claim did not survive
re-verification, §A.2 says so explicitly and this report follows the measured
evidence.

---

## A. Executive conclusion

**Scope C is technically safe, and the decisive safety property is proven
behaviourally: with the executable registry narrowed to `bytefray-rules-4`
alone, every class of historical artifact in this checkout still decodes,
attributes, labels and fully replays — including real VM/blob-executed matches
and real Agent API v1 matches that never recorded a `ruleset_id` at all
(§Q).** Not one historical-reader module imports the executable resolver, and
the executable resolver has exactly four production call sites, all on
new-execution or pre-launch paths.

**The transition is also materially cheaper than Phase 2B.8 projected, and the
reason is that Phases 2B.9 and 2B.10 already paid most of the cost.** Measured
on the current tree rather than estimated:

| Measure | Phase 2B.8 (pre-Scope-A/B) | **This phase (post-2B.10)** |
| --- | ---: | ---: |
| Canonical tests collected | 3,713 | **3,440** |
| Scope-C execution-dependent outcomes | 830 | **393** |
| Share of suite affected | 22.4% | **11.4%** |
| Files where *every* case fails | not measured | **5 of 52** |

**Scope C is conversion work, not deletion work.** The 393 affected cases are
spread across 52 files holding 1,467 collected cases; only 5 files (37 cases)
fail in their entirety. The dominant failure shape is not "this test is about
Agent API v1" — it is **"this test produces its fixture by running a live
v1/VM match, then asserts on a reader or a subsystem that is entirely
current"** (§Z). Deleting those files would silently drop coverage of
supported V6 behaviour. This is the same trap Phase 2B.10 §F.1 hit once; at
Scope C it is the majority case.

**However, four defects are hard blockers that must be fixed as *required*
retirement edits rather than deferred as cleanup.** Each was verified by
execution:

| # | Blocker | Evidence |
| --- | --- | --- |
| **B-1** | **`bytefray run` with no agent arguments is a VM match.** `--a-type` defaults to `writer` and `--b-type` to `runner` — both VM builtins. Run live in this checkout, it records `ruleset_id: bytefray-rules-1`, replay schema 3. Under Scope C the product's flagship command fails by default. | §W.1 |
| **B-2** | **`bytefray agents create` defaults to Agent API v1** (`agent_scaffold.DEFAULT_API_VERSION = 1`), so V6 would scaffold, by default, an agent its own runtime cannot execute. | §H |
| **B-3** | **`evaluation_presets._VALID_RULESETS = ("bytefray-rules-1", "bytefray-rules-2")` — under Scope C it contains *no* legal value at all.** Every ruleset-declaring preset breaks, and no correct value can be written. Its own comment claims it "mirrors `agent_evaluation`'s own `--ruleset` choices exactly", which is **already false today**. | §K.4 |
| **B-4** | **All four "missing → Ruleset 1" fallbacks survive a narrowed registry and return a retired identity.** Measured, not inferred. One is worse than Phase 2B.8 recorded: `resolve_omitted_ruleset_id(None, {"python"})` returns `bytefray-rules-2` today but **`bytefray-rules-1`** under Scope C — a silent downgrade, not a clean failure. | §T |

**Recommended strategy: Strategy A — full Scope C, implemented atomically as
one phase in dependency-ordered batches (§AE).** Staging VM and Agent API v1
apart was evaluated and rejected on measured evidence: they are not separable
without leaving the product in a state where `bytefray run`'s own defaults are
broken (§AD).

**Two prior-audit claims did not survive re-verification (§A.2), and one of
them would have caused a real regression if implemented as written.**

### A.1 What Scope C actually is

Stated precisely, because the ruleset framing understates it:

> Retiring `bytefray-rules-1` and `bytefray-rules-2` removes **all Agent API
> v1 execution and all VM/blob execution**. It strands 11 of 21 bundled
> starter agents, all 4 reference agents, both non-process scaffold template
> pairs, the non-process `agents test` reference opponent, three shipped
> benchmark corpora, and the default invocation of `bytefray run`.

That is a real product decision, and this audit takes it as already made. What
follows is its cost, its order, and its traps.

### A.2 Prior-audit claims corrected by this phase

Recorded prominently because Phase 2B.12 will be implemented from this
document.

| # | Prior claim | Status | Correct finding |
| --- | --- | --- | --- |
| **C-1** | Phase 2B.8 §G.4: **`supervised_runtime.py` (557 LOC) becomes "wholly execution-dead"** under Scope C. | **FALSE — would have caused a regression** | The file is 543 LOC today, and `diagnostic_for_worker_result` + `_diagnostic_from_payload` (lines 105–161) are imported by **`process_runtime.py:448`** — *Ruleset 4's own worker path* — and by `agent_validation.py:71`. Deleting the file breaks the retained runtime. Correct disposition: **PARTIAL REMOVE** — `SupervisedPythonEntrantController` + `_NullAgentInstance` (lines 86–104, 162–543 ≈ 401 LOC) are dead; ~104 LOC must stay (§P). |
| **C-2** | Phases 2B.8/2B.9/2B.10 treat `VULNERABLE_CORE_RULESET_IDS` and `OBSERVABLE_CORE_RULESET_IDS` as an inseparable pair that must **never** lose members (trap T-9). | **Was correct then; asymmetric now** | `has_vulnerable_core` is called by `client/src/battle_client/replay_status.py:180` (a reader) → the vulnerable table **must be kept**. `has_observable_core`/`OBSERVABLE_CORE_RULESET_IDS` have **no reader consumer at all** — their only call site is `supervised_runtime.py:384` → both become genuinely dead under Scope C (§P.2). `seed_core_ownership` appears in `replay_status.py` only inside a **docstring**, never as a call. |
| **C-3** | Phase 2B.8 §P.1: Scope C affects **830 of 3,713** collected cases. | **Superseded** | Re-measured on the post-2B.10 tree: **393 of 3,440**. Phases 2B.9/2B.10 removed the v2-alpha/v3 suites and re-pointed ~200 spectator outcomes at `bytefray-rules-4`, which now pass under a narrowed registry. Anyone reusing "830" would overstate the remaining work by ~2×. |

### A.3 New traps this phase found

Not present in any prior audit or in the charter's own enumerated lists.

| # | Trap | Evidence |
| --- | --- | --- |
| **N-1** | **`api_version` is hashed into every Python entrant's RNG seed.** `derive_agent_seed`'s material is `f"battle2-python-v1\0{match_seed}\0{slot}\0{agent_id}\0{api_version}"`. Removing the API-version field from the worker wire protocol, from `AgentMetadata`, or from this hash **changes every Ruleset 4 entrant seed** and therefore changes the frozen control's gameplay. Proven: dropping the field from the material yields a different seed for an unchanged v2 entrant. | §V.1 |
| **N-2** | **`bytefray run`'s default agents are VM builtins** (`writer`/`runner`). The default invocation of the product's primary command is a Ruleset-1 VM match. | §W.1 |
| **N-3** | **`evaluation_presets._VALID_RULESETS` has already drifted** from the CLI choices it claims to mirror, and under Scope C is left with zero legal values. | §K.4 |
| **N-4** | **`agent_test.py`'s `--ruleset` help text is stale since Phase 2B.10** — it still tells users "both v4 alphas support Agent API v2" and "v4 alpha1/alpha2 remain selectable by name". Both claims are false today. | §W.4 |

---

## B. Baseline

Established before any investigation, per the charter's §2. Nothing was
modified during baseline establishment.

| Check | Result |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `551cf5a2c3c557906e80d4349e73fca765a914ae` |
| Phase 2B.10 committed | **Yes** — HEAD is commit `551cf5a` "Phase 2B.10" (touches `ruleset_policy.py`, `ruleset_options.py`, the four CLIs, the frozen fixtures, and the 2B.10 report) |
| Working tree at phase start | **Clean** (`git status --porcelain` empty) |
| Divergence from `origin/v6-research` | **0 ahead, 0 behind** (after `git fetch origin --prune`) |
| `main` | **0 ahead, 0 behind** `origin/main` — untouched throughout |
| Canonical tests collected | **3,440** across **147** reporting files |
| Test files on disk (`testpaths`) | **148** — `client/tests/test_linux_pygame_smoke.py` collects 0 under `-m "not gui"` |
| Tracked files | 780 (404 `.py`, 178 `test_*.py`, 216 `.md`) |
| Total tracked Python LOC | **167,709** |
| Historical artifacts available | **53,458** `result.json` under `runs/` |

### B.1 Executable ruleset registry, read from live objects

```
REGISTERED: ['bytefray-rules-1', 'bytefray-rules-2', 'bytefray-rules-4']
PROCESS_RULESET_IDS: ['bytefray-rules-4']
OMITTED_RULESET_CANDIDATES: ('bytefray-rules-2', 'bytefray-rules-4', 'bytefray-rules-1')
```

| Canonical ID | Runtime kinds | Agent API | Placement | Process sel. | Scheduler |
| --- | --- | --- | --- | --- | --- |
| `bytefray-rules-1` | **unrestricted (VM + Python)** | {1} | `zero` | priority | sequential |
| `bytefray-rules-2` | python | {1} | `seat_spread` | priority | sequential |
| **`bytefray-rules-4`** | python | **{2}** | `seeded` | round_robin | chunked/2, rotate |

Exactly the registry the charter expected after Phase 2B.10. Confirmed from
source, not assumed.

### B.2 Runtime module LOC

| Module | LOC | | Module | LOC |
| --- | ---: | --- | --- | ---: |
| `agent_evaluation.py` | 5,443 | | `agent_worker.py` | 667 |
| `match_service.py` | 1,498 | | `supervised_runtime.py` | **543** |
| `agent_package.py` | 1,444 | | `agent_api.py` | 478 |
| `process_runtime.py` | 1,367 | | `evaluation_worker.py` | 433 |
| `python_runtime.py` | 1,268 | | `agent_scaffold.py` | 299 |
| `ruleset_policy.py` | 778 | | `agents.py` | 275 |
| `core.py` | 151 | | `vm.py` | 148 |
| `builtins/registry.py` | 146 | | `match.py` | 126 |
| `agent_state.py` | 57 | | `instructions.py` | 14 |

`supervised_runtime.py` is **543**, not the 557 Phase 2B.8 recorded — Phase
2B.9 removed its locality telemetry call.

### B.3 Bundled agent inventory, parsed from real manifests

Built by running every bundled manifest through `agents.agent_spec_from_dir`,
not by reading comments.

| Class | Count | Names |
| --- | ---: | --- |
| **VM/blob starters** (`kind="builtin"`, no `api_version`) | **4** | `runner`, `writer`, `seeker`, `spiral` |
| **Agent API v1 Python starters** | **7** | `claimer`, `strider`, `hunter`, `wanderer`, `adaptive`, `raider`, `sentinel` |
| **Agent API v2 Python starters** | **10** | `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_scout`, `v4_quorum`, `v5_region_attacker`, `v5_scout_striker`, `v5_core_defender`, `v5_dual_team` |
| **Total bundled starters** | **21** | |
| **Reference agents** (all `api_version=1`, hardcoded) | **4** | `core_defender`, `core_seeker`, `reactive_core_defender`, `core_tracker` |
| **Scaffold template pairs** | **4 dirs** | `agent_template` (v1), `agent_template_annotated` (v1), `agent_template_v2` (v2), `agent_template_v2_annotated` (v2) |
| **Other bundled API v1 fixtures** | **2** | `data/v3_closeout_agents/turtle_core_refresher`, `data/v3_phase7_agents/core_tracker_offset` |

The charter's expected counts (4 VM, 7 API v1, 10 API v2) are **confirmed
exactly**.

### B.4 Historical corpus distribution, re-measured

Independently re-walked (53,458 files); matches Phase 2B.8's figures exactly.

| Recorded `ruleset_id` | Results | Share |
| --- | ---: | ---: |
| `bytefray-rules-2` | **31,053** | 58.09% |
| `bytefray-rules-4-alpha1` | 12,782 | 23.91% |
| `bytefray-rules-3-alpha1` | 6,984 | 13.06% |
| `bytefray-rules-4` (the control) | 1,910 | 3.57% |
| *(absent → recovered as `bytefray-rules-1`)* | **673** | 1.26% |
| `bytefray-rules-5-r1-alpha1` | 42 | 0.08% |
| `bytefray-rules-4-alpha2` | 7 | 0.01% |
| `bytefray-rules-5-r2-alpha1` | 7 | 0.01% |

**59.35% of the entire corpus belongs to the two identities Scope C retires.**
Historical-reader retention is therefore the dominant correctness requirement
of this phase, not a side concern.

---

## C. Scope-C product policy applied

Taken as given:

* `bytefray-rules-4` is the frozen V6 control — executable, behaviourally
  immutable. Nothing in Scope C may alter its dispatched, hashed or persisted
  behaviour.
* `bytefray-rules-1` and `bytefray-rules-2` lose **new-execution** support.
  Their identities remain **recognisable** forever.
* Agent API v1 and VM/blob execution are retired with them.
* `bytefray-rules-6` is where new gameplay will be developed. Not created here.
* A retired identity must **never** be silently normalised to
  `bytefray-rules-4`. It must fail explicitly.

This audit reports technical consequences and does not re-argue the direction.

---

## D. Agent API generation map

### D.1 Surface-by-surface comparison

| Surface | **Agent API v1** | **Agent API v2** (retained) |
| --- | --- | --- |
| Manifest | `kind: python`, `api_version: 1`, `entrypoint` | `kind: python`, `api_version: 2`, `entrypoint` |
| Agent contract | `reset(context)` + `act(observation) -> AgentAction` | `reset(context)` + **`declare_processes() -> list[ProcessDeclaration]`** + `act(obs, action_slot)` |
| Action enum | `ActionKind` | **`ActionKindV2`** |
| Observation | `Observation` | **`ObservationV2`** |
| Action validation | `python_runtime.validate_action` | **`ProcessMatchController._validate_v2_action`** |
| Controller | `PythonEntrantController` (unsupervised) / `SupervisedPythonEntrantController` (worker-per-entrant) | **`ProcessMatchController`** |
| Process model | one action per entrant per tick | **multiple declared processes**, quota-shared, round-robin slots |
| Match dispatch | `match_service._run_python_match_traced` | **`match_service._run_v4_process_match`** |
| Subprocess worker | `agent_worker.AgentWorkerHandle` (shared) | same handle, `declare_processes` command added |
| Replay schema written | **3** | **4** |
| Trace schema written | **1** (`TRACE_SCHEMA_VERSION`) | **2** (`TRACE_SCHEMA_VERSION_V2`) |
| Compatible rulesets | `bytefray-rules-1`, `bytefray-rules-2` | `bytefray-rules-4` |
| Evaluation methodology | v1 (default) / v2 (`_V2_METHODOLOGY_RULESET_IDS`) | v4 (`_V4_METHODOLOGY_RULESET_IDS`) |
| `agents test` reference opponent | `data/agent_template` (API v1) | `data/starter_agents/v4_claimer` (API v2) |
| Scaffold templates | `agent_template`, `agent_template_annotated` | `agent_template_v2`, `agent_template_v2_annotated` |
| Bundled starters | 7 | 10 |
| Designer/CLI ruleset offering | v1, v2 | v4 |

### D.2 Runtime dispatch topology

`NativeMatchService.run` (`match_service.py:1352-1477`) is the **single**
dispatch point. It resolves one policy and then branches exactly three ways:

```
NativeMatchService.run
├── homogeneity/uniqueness validation      (kinds ⊆ {vm, python}, len == 1)
├── resolve_ruleset_policy(_resolve_ruleset_id(request))     ← fails closed
├── unsupported_runtime_kinds / supports_agent gates
├── _validate_v2_core_placement            (rules-2 and rules-4)
└── if "python" in kinds:
    ├── is_v4_process_match = ruleset_id in PROCESS_RULESET_IDS
    ├── TRUE  -> _run_v4_process_match      (API v2, trace v2, replay 4)  ← RETAINED
    └── FALSE -> _run_python_match_traced   (API v1, trace v1, replay 3)  ← RETIRED
    else:
    └── _run_vm_match                        (VM/blob, replay 3)           ← RETIRED
```

**Under Scope C two of the three arms disappear and the branch collapses**:
`is_v4_process_match` is unconditionally true, the `else` arm goes, and the
trailing `_run_vm_match` call goes. `PROCESS_RULESET_IDS` already has exactly
one member.

### D.3 Abstractions that exist only because v1 and v2 coexist

Recorded as **post-retirement simplification opportunities**. Not to be
refactored in Phase 2B.12 beyond what retirement requires (§V).

| # | Abstraction | Location | Post-Scope-C status |
| --- | --- | --- | --- |
| 1 | Three-way runtime dispatch | `match_service.py:1437-1476` | Collapses to one path |
| 2 | `is_v4_process_match` gate | `match_service.py:1437` | Always true |
| 3 | Replay-schema selection `4 if … else 3` | `match_service.py:1177` | Always 4 |
| 4 | Trace-schema selection v2/v1 | `match_service.py:1440` | Always v2 |
| 5 | Dual action validators | `agent_validation.py:401-404`, `:630-633` | One validator |
| 6 | `ActionKind` vs `ActionKindV2` | `agent_api.py` | v1 enum kept **for replay/trace reading only** |
| 7 | `Observation` vs `ObservationV2` | `agent_api.py` | as above |
| 8 | Worker `api_version` branching | `agent_worker.py:434, 507, 553` | **Field must stay — see N-1** |
| 9 | Ruleset-kind compatibility (`supported_runtime_kinds`) | `ruleset_policy.py` | `None`-means-unrestricted case disappears with Ruleset 1 |
| 10 | Three evaluation methodology generations | `agent_evaluation.py` | New evaluations become v4-only; **historical predicates stay** |
| 11 | `resolve_omitted_ruleset_for_agents` candidate walk | `ruleset_policy.py:602` | One candidate |
| 12 | `agent_runtime_label` `[Python]`/`[VM]` | `agents.py:47` | Single-valued |

---

## E. VM/blob execution topology

Traced from user selection through to artifact.

### E.1 The complete path

| Stage | Location | Scope-C status |
| --- | --- | --- |
| CLI selection | `cli.py:317` `--a-type` / `:323` `--b-type`, **defaulting to `writer`/`runner`** | **REQUIRED EDIT (B-1)** |
| Builtin name check | `cli.py:501` `agent_name not in SUPPORTED` | Dead |
| Bytecode assembly | `builtins/registry.py` — `SUPPORTED = ("runner","writer","bomber","flooder","spiral","seeker")`, six `assemble_*`, `build_agent` | **DEAD — whole file (146 LOC)** |
| Opcode definitions | `instructions.py` — 12 opcodes + `enc` | **DEAD — whole file (14 LOC)** |
| Manifest/kind detection | `agents.py:_spec_from_dir` → `kind ∈ {builtin, blob, python}` | `builtin`/`blob` branches dead |
| Runtime label | `agents.py:agent_runtime_label` → `[VM]` | Single-valued |
| Entrant construction | `MatchEntrant(kind="vm", code=bytes)` | `code` field dead |
| Composition gate | `match_service.py:1353-1361` | VM arm dead |
| Dispatch | `match_service._run_vm_match` (1283–1348, **66 LOC**) | **DEAD** |
| Kernel | `core.Kernel` (`core.py:85-151`) | **DEAD** — but see E.3 |
| Tick loop | `match.MatchRunner` (`match.py`, 126 LOC) — **only consumer is `core.Kernel`** | **DEAD — whole file** |
| Instruction execution | `vm.VM.step` (~65 LOC) | **DEAD** |
| Initial code placement | `vm.VM.load_code` (~20 LOC) | **DEAD** |
| Arena / ownership | `vm.VM.__init__`, `_rd32`, `_wr8`, `clear_tick_diffs`, `arena`, `writer`, `ownership_counts`, `tick_diffs` | **KEEP — shared with `process_runtime.py`** |
| VM result build | `match_service._build_result` (530–598, 69 LOC) | **DEAD** |
| Agent state | `agent_state.Agent` | **KEEP** — shared typing with `results`/`scoring`/`statistics`/`telemetry`, all used by the process path |
| Tournament identity | `tournament_service._entrant_identity` `kind == "vm"` → `code_sha256` | Branch dead |
| Designer | `VM_RULESET_EXPLANATION`, `[VM]` labels, mixed-kind guard | Dead (§N) |
| Starters | `runner`, `writer`, `seeker`, `spiral` | Remove (§I) |

### E.2 `vm.py` is NOT removable — confirmed

The charter's caution is correct. `process_runtime.py:59` imports `VM` and
uses `self.vm.arena`, `self.vm.writer`, `self.vm.ownership_counts`,
`self.vm._wr8`, `self.vm.clear_tick_diffs` at lines 676, 714, 993, 1000, 1004,
1206, 1207, 1229, 1271, 1283, 1289, 1297, 1358. It never calls `load_code` or
`step`.

**Disposition: `vm.py` is PARTIAL REMOVE** — delete `load_code` and `step`
(~85 of 148 LOC, which also removes the module's only use of
`instructions.py`); keep the arena. `telemetry.py` and `match.py` also import
`VM`; the latter goes with the VM path.

### E.3 `core.py` is a declared compatibility facade — handle deliberately

`core.py`'s own comment (lines 37–46) states it is *"a deliberate compatibility
facade (see AGENTS.md's 'Compatibility surfaces are deliberate, not
accidental')"* and that `__all__` exists so *"an 'unused import' auto-fix will
not silently delete a supported public import path."* Its `__all__` re-exports
12 VM opcode names, `enc`, `VM`, `Agent`, `Kernel`, `MatchRunner`, and shared
names.

`Kernel` itself becomes dead, but **removing the facade entries is a
compatibility decision, not a dead-code cleanup**, and this repository's own
rules require checking such a surface before pruning it. Two in-tree test
files still import through it (`client/tests/test_analysis.py:175`,
`client/tests/test_replay_session.py:9`). Recorded as an explicit disposition
item for Phase 2B.12 (§P), not a mechanical deletion.

---

## F. Ruleset 1 findings

### F.1 Current execution reachability

| Surface | Reachable today? | Evidence |
| --- | --- | --- |
| `bytefray run --ruleset` | **Yes** | `cli.py:293` |
| `bytefray run` **with no `--ruleset` and no agents** | **Yes — this is the default** | `cli.py:317,323`; verified live (§W.1) |
| `bytefray tournament --ruleset` | **Yes** | `tournament_cli.py:60` |
| `bytefray agents test --ruleset` | **Yes** | `agent_test.py:1043` |
| `bytefray agents evaluate --ruleset` | **Yes** | `agent_evaluation.py:4371` |
| Evaluation low-level allow-list | **Yes** | `agent_evaluation.py:3383` |
| Evaluation preset `ruleset:` | **Yes** — one of only two legal values | `evaluation_presets.py:81` |
| Designer Advanced/Development | **Yes** (`RULESET_V1_OPTION`) | `ruleset_options.py:38`, `:100` |
| Designer Evaluation | **Yes** | `ruleset_options.py:90` |
| Designer Simple | No | `SIMPLE_RULESET_OPTIONS` = (v2, v4) |
| Omitted resolution — VM roster | **Yes, auto-selected** | `OMITTED_RULESET_CANDIDATES[2]` |
| Omitted resolution — empty roster | **Yes, auto-selected** | `resolve_omitted_ruleset_for_agents:643` |
| Low-level `MatchRequest(ruleset_id=None)` | **Yes, auto-selected** | `match_service.py:513` |

### F.2 Unique runtime dependencies

`bytefray-rules-1` is the **only registered ruleset with
`supported_runtime_kinds=None`** (unrestricted), and therefore the only
executor for VM/blob entrants. It is also API v1 (`{1}`), placement `zero`,
scheduler `sequential`.

It is **not** a member of `VULNERABLE_CORE_RULESET_IDS` or
`OBSERVABLE_CORE_RULESET_IDS` — the vulnerable-core mechanic is a Ruleset-2
family feature. Its unique execution surface is exactly the VM topology of §E
plus API v1 Python execution shared with Ruleset 2.

### F.3 Historical recognition — required, and independent of execution

Two readers **synthesise** `bytefray-rules-1` for artifacts that never
recorded it:

* `result_model.resolve_result_ruleset` — `ruleset_id` absent + `mode == "b2"`
  → `RulesetProvenance("bytefray-rules-1", "recovered")`
* `replay.resolve_replay_ruleset:712` — `ruleset_id` absent +
  `schema_version == 3` → the same

**673 `result.json` files in this checkout depend on this path** (§B.4), and
this phase confirmed it covers *both* historical execution families. Measured
with the registry narrowed to `bytefray-rules-4`:

```
API v1 python, no ruleset_id     ruleset='bytefray-rules-1' conf='recovered' winner='A'
VM/blob executed, no ruleset_id  ruleset='bytefray-rules-1' conf='recovered' winner='tie'
VM/blob executed (phase3)        ruleset='bytefray-rules-1' conf='recovered' winner='B'
```

**The distinction the charter asks for holds exactly:**

> `bytefray-rules-1` must remain **identifiable** — yes, permanently, and it
> already is, at zero cost.
> `bytefray-rules-1` must remain **executable** — no.

---

## G. Ruleset 2 findings

### G.1 Why retiring it is the larger half of Scope C

`bytefray-rules-2` is not a dormant historical identity. It is the **current
default gameplay for every Agent API v1 roster** and is first in
product-preference order almost everywhere:

* `OMITTED_RULESET_CANDIDATES = (rules-2, rules-4, rules-1)` — **first**.
* `SIMPLE_RULESET_OPTIONS` includes it, labelled
  **"Ruleset v2 — Current / Recommended"** (`ruleset_options.py:25`).
* `RULESET_DESCRIPTION` opens: *"Ruleset v2 is Bytefray's current gameplay
  ruleset…"*
* It is first in `EVALUATION_RULESET_OPTIONS` and `DESIGNER_RULESET_OPTIONS`.
* `docs/RULES_V2.md` — *"**Status: permanent, stable semantic identity**"*,
  *"describes the game as it plays today"*.
* **58.09% of the entire artifact corpus** (31,053 results).

### G.2 Dependency chain

| Dependency | Count |
| --- | ---: |
| Bundled Agent API v1 Python starters | 7 |
| Bundled reference agents (`api_version=1` hardcoded) | 4 |
| Scaffold template pairs producing API v1 | 2 |
| `bytefray agents create` default output | **all** |
| `agents test` non-process reference opponent | 1 |
| Shipped benchmark corpora declaring `bytefray-rules-2` | **3** (`v2_baseline.json`, `v2_baseline_corpus.json`, `v3_phase1_arena_action_grid.json`) |
| Other bundled API v1 fixture agents | 2 |
| Evaluation preset legal `ruleset` values | 2 of 2 |

### G.3 Unique vs shared implementation

**Unique to the Ruleset-2 family — dead under Scope C:**

| Symbol | Location | LOC |
| --- | --- | ---: |
| `OBSERVABLE_CORE_RULESET_IDS` | `python_runtime.py:144-151` | 8 |
| `has_observable_core` | `python_runtime.py:176-186` | 11 |
| `core_seed_byte` | `python_runtime.py:187-192` | 6 |
| `_snapshot_core_owners` | `python_runtime.py:200-222` | 23 |
| `seed_core_ownership` | `python_runtime.py:223-254` | 32 |
| `maintain_core_beacons` | `python_runtime.py:255-297` | 43 |

**NOT dead — reader dependency (this is the T-9 boundary):**

| Symbol | Reader | Why |
| --- | --- | --- |
| `VULNERABLE_CORE_RULESET_IDS` | `replay_status.py` | consulted by `_core_status` |
| `has_vulnerable_core` | `replay_status.py:180` | gates per-entrant core derivation |
| `core_addresses`, `CORE_SIZE` | `replay_status.py`, `pygame_renderer.py`, `placement.py`, `match_service.py` | shared |

**Shared with the control — must be retained:** `apply_core_capture` (called
unconditionally by `process_runtime.py:1269`), `_attribute_core_capture`,
`derive_agent_seed`, the whole `diagnose_*` block, `RuntimeDiagnostic`,
`vm.VM`'s arena.

---

## H. `bytefray agents create` disposition

### H.1 Current behaviour and why the pin no longer works

`agent_scaffold.DEFAULT_API_VERSION = 1`, with this standing rule in the
module's own comment:

> "Deliberately pinned to 1 rather than tracking `agent_api.AGENT_API_VERSION`:
> `bytefray agents create <id>` has always produced an Agent API v1 agent, and
> repointing an established command's default at a newer generation would
> silently change the meaning of every existing script and instruction that
> uses it."

That reasoning was sound while both generations executed. Under Scope C it
inverts: keeping the pin means **V6 scaffolds, by default, an agent its own
runtime cannot execute.**

### H.2 The migration is far cheaper than Phase 2B.8 assumed

**Agent API v2 scaffold templates already exist and are already wired end to
end.** Verified from source:

```
TEMPLATE_DIRECTORIES_BY_API_VERSION = {
    1: {"blank": "agent_template",     "annotated": "agent_template_annotated"},
    2: {"blank": "agent_template_v2",  "annotated": "agent_template_v2_annotated"},
}
```

All four directories exist with correct manifests (`api_version: 1` / `2`).
`validate_api_version` already derives its accepted set from
`SUPPORTED_AGENT_API_VERSIONS`, and
`test_scaffold_templates_cover_every_supported_api_version` already fails
loudly if a generation lacks a template. The PyInstaller specs already iterate
`TEMPLATE_DIRECTORIES_BY_API_VERSION` to bundle template data, so narrowing it
propagates to frozen builds automatically.

**`bytefray agents create --api-version 2` works today.** The change is the
default, not the machinery.

### H.3 Options evaluated

| Option | Assessment |
| --- | --- |
| **A. Repoint default to Agent API v2** | **RECOMMENDED.** One constant (`DEFAULT_API_VERSION = 2`) plus narrowing `TEMPLATE_DIRECTORIES_BY_API_VERSION` to `{2: …}` and removing the two v1 template dirs. Every user gets a runnable agent by default. The standing rule it overrides was explicitly premised on both generations executing. |
| **B. Require explicit `--api-version`** | Rejected. Turns the single most common first-run command into an error for no benefit once only one generation exists; contradicts the charter's "users should not need to choose an engine generation". |
| **C. Replace scaffold with a process-oriented template** | **Already satisfied by A.** `agent_template_v2` *is* the process-oriented template (`reset`/`declare_processes`/`act`). No new authoring work. |
| **D. Retain legacy generation, mark unexecutable** | Rejected, honestly assessed: it preserves a command whose output cannot run, keeps two template pairs and the v1 loader alive for documentation value only, and directly violates the guiding requirement. |

### H.4 Recommendation

> **Option A.** Set `DEFAULT_API_VERSION = 2`; narrow
> `TEMPLATE_DIRECTORIES_BY_API_VERSION` to `{2: {...}}`; delete
> `data/agent_template/` and `data/agent_template_annotated/`; update
> `docs/specs/agent_scaffold.md`, `docs/AGENT_AUTHORING.md` and the CLI help.
> Record it in `CHANGELOG.md` as a deliberate default change with its reason,
> because it does change the meaning of existing scripts — which is exactly
> what the original comment asked a future editor to do consciously rather
> than silently.

**Coupling that must be handled in the same batch:** `data/agent_template/` is
**also** the `agents test` non-process reference opponent
(`agent_test._reference_opponent_spec:163`). Deleting it without §M's change
breaks Agent Test.

---

## I. Starter-agent disposition

### I.1 Complete table

| # | Name | Kind | API | Role | Ruleset dep. | **Disposition** |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | `runner` | builtin (VM) | — | `bytefray run --b-type` **default** | rules-1 | **REMOVE** |
| 2 | `writer` | builtin (VM) | — | `bytefray run --a-type` **default** | rules-1 | **REMOVE** |
| 3 | `seeker` | builtin (VM) | — | starter | rules-1 | **REMOVE** |
| 4 | `spiral` | builtin (VM) | — | starter | rules-1 | **REMOVE** |
| 5 | `claimer` | python | 1 | starter; **v2 benchmark member** | rules-1/2 | **HISTORICAL ONLY** |
| 6 | `strider` | python | 1 | starter; **v2 benchmark member** | rules-1/2 | **HISTORICAL ONLY** |
| 7 | `hunter` | python | 1 | starter; **v2 benchmark member** | rules-1/2 | **HISTORICAL ONLY** |
| 8 | `wanderer` | python | 1 | starter; **v2 benchmark member** | rules-1/2 | **HISTORICAL ONLY** |
| 9 | `adaptive` | python | 1 | starter; **v2 benchmark member** | rules-1/2 | **HISTORICAL ONLY** |
| 10 | `raider` | python | 1 | vulnerable-core **attack** demo | rules-2 | **REMOVE** — archetype already covered by `v4_concentrated_attacker` / `v5_region_attacker` |
| 11 | `sentinel` | python | 1 | vulnerable-core **defence** demo | rules-2 | **REMOVE** — covered by `v5_core_defender` / `v4_local_defender` |
| 12–21 | the ten `v4_*`/`v5_*` starters | python | 2 | current ladder | rules-4 | **KEEP unchanged** |

### I.2 Reasoning, applying the charter's test

> *Does each old starter teach or demonstrate something still useful in current
> Bytefray?*

* **The 4 VM starters: no.** They demonstrate hand-assembled bytecode against
  an instruction set V6 no longer executes. Nothing in the API v2 model is
  illustrated by them. They are the four whose removal also removes
  `builtins/registry.py` and `instructions.py` outright.
* **`claimer`/`strider`/`hunter`/`wanderer`/`adaptive`: HISTORICAL ONLY, not
  REMOVE.** `starters.py`'s own comment records that these five are
  **content-addressed pinned members of the frozen v2 benchmark population**
  in `data/benchmarks/v2_baseline.json` and "must never be edited". Their
  strategies (sweep, stride, hunt, wander, adapt) are already represented in
  the v4/v5 ladder, so they need not be ported; but their **source must remain
  byte-identical on disk** for the shipped corpora to stay verifiable. They
  should leave `STARTER_AGENT_NAMES` (so they are no longer installed into a
  user's catalogue as runnable starters) while their directories remain as
  frozen benchmark fixtures. *See §AI risk R-2 — whether the corpora are
  retained at all is a product call this audit flags rather than makes.*
* **`raider`/`sentinel`: REMOVE.** `starters.py` explicitly records that these
  two are **deliberately not benchmark members** and "stay freely maintainable
  precisely because they carry no benchmark identity". They exist to
  demonstrate the Ruleset-2 vulnerable-core mechanic, which Scope C retires
  outright. Nothing depends on their bytes.

**Do not port any of the seven.** Each archetype already has a v2 equivalent,
and porting would produce agents whose only justification is name continuity —
precisely what the charter warns against.

### I.3 Resulting counts

| | Before | After |
| --- | ---: | ---: |
| `STARTER_AGENT_NAMES` entries | 21 | **10** |
| Installed into a user's catalogue | 21 | **10** |
| Directories remaining on disk | 21 | **15** (10 starters + 5 frozen benchmark fixtures) |

---

## J. Reference-agent disposition

All four are `kind="python", api_version=1`, hardcoded in
`reference_agents.py:79-87`, loaded from package resources and never installed
into the user catalogue.

| Agent | Methodology using it | v2 equivalent exists? | **Disposition** |
| --- | --- | --- | --- |
| `core_defender` | v2 evaluation (vulnerable-core defence baseline) | `v5_core_defender`, `v4_local_defender` | **Replace with existing v2 reference** |
| `reactive_core_defender` | v2 evaluation (reactive defence, alpha.2) | `v5_core_defender` | **Replace with existing v2 reference** |
| `core_seeker` | characterization fixture for the alpha.6/alpha.7 timing studies | — (its value is its *fixed, placement-dependent* schedule) | **Retain as historical fixture only** |
| `core_tracker` | v2 reference **offense benchmark** (beta1) | `v4_concentrated_attacker`, `v5_region_attacker` | **Replace with existing v2 reference** |

**Key determination:** every methodology that consumes these agents is the
**v2 evaluation methodology**, which under Scope C can no longer run a new
evaluation at all — `_V2_METHODOLOGY_RULESET_IDS = {bytefray-rules-2,
bytefray-rules-4-alpha1}` and neither is executable. **Historical evaluation
artifacts referencing these agents need only their recorded metadata, not live
execution** (proven in §Q.3). So:

> **No Agent API v1 runtime should be retained to preserve any reference
> agent.** Three are already superseded by shipped API v2 starters; the fourth
> is a frozen characterization fixture whose worth is its recorded past
> behaviour, not its ability to run again.

`REFERENCE_AGENT_NAMES` and `reference_agent_spec` become unreachable from any
executable path. Recommended: remove `core_defender`,
`reactive_core_defender` and `core_tracker`; retain `core_seeker`'s directory
as an archived fixture with a comment naming `v5.0.0` as the release that can
still execute it.

---

## K. Evaluation impact

`agent_evaluation.py` (5,443 LOC) is the largest single module and a declared
Phase 3 context-locality hotspot. **This audit recommends no refactor of it in
Phase 2B.12.**

### K.1 The three methodology generations

| Generation | Selector | Members |
| --- | --- | --- |
| v1 (implicit default) | neither predicate true | `bytefray-rules-1` via `EVALUATION_RULES_COMPATIBILITY_ID` |
| v2 | `_V2_METHODOLOGY_RULESET_IDS` | `bytefray-rules-2`, `bytefray-rules-4-alpha1` |
| v4 | `_V4_METHODOLOGY_RULESET_IDS` | `bytefray-rules-4-alpha2`, **`bytefray-rules-4`** |

The `resolved_is_v2` / `resolved_is_v4` pair is computed at **five** sites
(`:1771`, `:2955`, `:3491`, `:4193`, `:5236`) and threaded into
`resolved_schema_version`, `resolved_identity_version` and
`resolved_arena_alignment_mode` (`:669-699`), plus the `request.is_v2/v4`
properties (`:1472-1477`).

### K.2 The split the charter asks for

| Class | Under Scope C |
| --- | --- |
| **New evaluation execution** | Becomes **v4-only**. `resolved_is_v4` is always true, `resolved_is_v2` always false, the v1 default unreachable. Every `if v4 / elif v2 / else v1` becomes a straight line. |
| **Historical evaluation reading/comparison** | **Must keep both predicates and both tables.** `is_ruleset_v2_methodology` is called from `evaluation_history/cli.py:140`, `app/services/evaluation_history_workflows.py:105` and `app/services/designer_workflows.py:943`; `is_ruleset_v4_methodology` from `evaluation_history/verification.py:475`. All read a **persisted** `rules_compatibility_id`. |
| **Historical compatibility attribution** | `EVALUATION_RULES_COMPATIBILITY_ID = bytefray-rules-1` must keep meaning *"the historical v1 methodology"*. It must **never** be repointed at `bytefray-rules-4` (§S). |

This confirms and extends Phase 2B.10's §D.1 finding: the methodology tables
are **dual-use** and must not be narrowed. Phase 2B.10 established this for
the two v4 alphas; it holds a fortiori at Scope C.

### K.3 Quantified

* **Execution-dead:** the v1/v2 arms of 5 three-way branches, the three
  `resolved_*` helpers' non-v4 returns (`:669-699`, ~31 LOC), the
  `_validate` allow-list's v1/v2 entries, and the group-mode path gated on
  `request.group and resolved_is_v2` (`:1780`, `:2957`, `:3493`, `:4195`).
* **Retained for history:** both membership tables, both predicates, both
  schema/identity version constants, the compatibility-ID constant, and every
  `evaluation_history/` reader.
* **Net:** a modest LOC reduction (low hundreds) but a **large branching
  reduction**. The module does not shrink dramatically; it becomes far
  shallower. That is the honest characterization.

### K.4 `evaluation_presets._VALID_RULESETS` — blocker B-3

```python
# v2.0.0-beta2 Phase 1: mirrors battle_engine.agent_evaluation's own
# --ruleset choices exactly (...)
_VALID_RULESETS = ("bytefray-rules-1", "bytefray-rules-2")
```

Two independent defects:

1. **The comment is already false.** `agent_evaluation`'s choices are
   `(rules-1, rules-2, rules-4)`. The tuple has not tracked the product since
   `v2.0.0-beta2` and **has never contained the current control.**
2. **Under Scope C it contains no legal value.** Both members become retired.
   Every preset file with a `ruleset:` key raises `EvaluationPresetError`
   (`:341-344`), and no value a user could write would be accepted.

**Required change:** `_VALID_RULESETS = (BYTEFRAY_RULESET_V4_ID,)`. No preset
files ship in-tree (verified), so the blast radius is user-authored presets
under the data root only. This is a real defect today and may be fixed at any
time.

---

## L. Tournament impact

`tournament_service.py` already rejects mixed rosters
(`_division_kind:371-377`: "Tournament divisions must be all VM or all
Python").

| Concern | Today | Under Scope C |
| --- | --- | --- |
| VM divisions | Supported; `bytefray-rules-1` auto-selected | Gone; `kinds <= {"vm","python"}` collapses to `{"python"}` |
| API v1 divisions | Supported; `bytefray-rules-2` auto-selected | Gone — `NoCompatibleRulesetError` |
| `_entrant_identity` VM branch (`:126` → `code_sha256`) | Live | **Dead** |
| Omitted `--ruleset` | v2 / v4 / v1 by roster | Always `bytefray-rules-4` |
| `--ruleset` choices | 3 | 1 (or removed) |
| `_place_pair` seeded guard (`:449`) | Conditional | Unconditional — `bytefray-rules-4` is always `seeded` |
| Compatibility validation | Runtime-kind + API-version | API version only |

**Caution for `_place_pair`:** it calls `core_placement_mode(request.ruleset_id)`,
which **fails *safe* to `"zero"`** for an unregistered ID rather than raising
(the T-4 family). Simplifying it to "always seeded" is correct *only* if
`request.ruleset_id` is guaranteed resolved before this point. Verify, don't
assume — Phase 2B.10 §K found a third member of this family
(`resolve_v4_seed_geometry`) only by running the tests.

Identified as simplification; **not to be implemented beyond what retirement
requires.**

---

## M. Agent Test impact

`agent_test._reference_opponent_spec` (`:124-182`) selects the opponent by
ruleset:

```python
if ruleset_id in PROCESS_RULESET_IDS:
    -> starter_agent_resource_dir("v4_claimer")   # API v2
else:
    -> template_resource_dir(resources)            # data/agent_template, API v1
```

Confirmed: the non-process reference opponent **is** Agent API v1, and it is
**the same `agent_template` directory `bytefray agents create` copies** — so
§H and §M are one coupled change, not two.

| Concern | Under Scope C |
| --- | --- |
| Reference opponent | Always `v4_claimer` (API v2) |
| The `else` branch and the `ruleset_id in PROCESS_RULESET_IDS` call-site guard (`:415-419`) | Dead |
| Ruleset 2 fallback | Gone |
| VM behaviour | `agents test` entrants were always Python; no VM path to remove |
| `--ruleset` choices | 3 → 1 |
| `agent_test.py:990` `{"kind":"python","api_version":1}` projection | Must become 2 |

**Recommended retained testing model:** `bytefray agents test <agent>` runs the
agent against `v4_claimer` under `bytefray-rules-4`, with no ruleset choice
required. `v4_claimer` is the right baseline — it is the simplest complete
API v2 starter, already bundled, already the process-path reference, and
already covered by `test_v5_starter_agents.py`.

> Do **not** retain the Agent API v1 runtime to keep the old reference
> opponent. The v2 baseline already exists and is already wired.

---

## N. Designer / GUI impact

Retirement cleanup only; no redesign.

### N.1 `app/services/ruleset_options.py`

| Item | Today | Under Scope C |
| --- | --- | --- |
| `RULESET_V2_OPTION` ("Ruleset v2 — Current / Recommended") | defined | **Delete** |
| `RULESET_V1_OPTION` ("Ruleset v1 — Compatibility (Python and VM/blob)") | defined | **Delete** |
| `RULESET_V4_OPTION` | defined | Keep; drop "(Agent API v2)" qualifier as it is no longer distinguishing |
| `SIMPLE_RULESET_OPTIONS` | (v2, v4) | **(v4,)** |
| `EVALUATION_RULESET_OPTIONS` | (v2, v4, v1) | **(v4,)** |
| `DESIGNER_RULESET_OPTIONS` | (v2, v4, v1) | **(v4,)** |
| `DEFAULT_DESIGNER_RULESET_ID` | v4 | unchanged |
| `RULESET_DESCRIPTION` | names v1, v2, v4 | **Rewrite** — its "Ruleset v2 is Bytefray's current gameplay ruleset" is the single most stale product claim in the GUI |
| `VM_RULESET_EXPLANATION` | "VM/blob agents run under Ruleset v1 only…" | **Delete entirely** |
| `ruleset_supports_runtime_kinds` | real guard | Near-trivial; retained as the launch guard seam |
| `best_designer_ruleset_for_agents` | walks a 3-tuple | Walks a 1-tuple |

### N.2 Other GUI surfaces

| Surface | Change |
| --- | --- |
| `app/widgets/ruleset_combo.py` | Single-item combo — consider hiding, but that is a UX decision, not retirement |
| `app/widgets/agent_combo.py` | `[Python]`/`[VM]` decoration becomes single-valued |
| `designer_workflows.RUNTIME_LABELS = {"python": "Python", "vm": "VM"}` (`:132`) | `vm` entry dead |
| `designer_workflows` mixed-kind message (`:302`) | Unreachable |
| `designer_workflows.agent_api_version` / `:221` `== 2` predicate | Always true |
| `DESIGNER_AUTO_TRACE_RULESET_IDS` | Already `{bytefray-rules-4}` — **no change** |
| Validation messaging | "VM/blob agents run under Ruleset v1 only" must go |

**Controls that disappear:** the Ruleset selector's meaningful choice, the VM
explanation label, the mixed-runtime warning. **Defaults that simplify:**
every surface already defaults to `bytefray-rules-4`.

### N.3 GUI test coverage

The four `@pytest.mark.gui` files under root `tests/` are outside the canonical
`testpaths` and were **not** exercised by this phase's measurements. Phase
2B.10 ran them (82 cases, `QT_QPA_PLATFORM=offscreen`). Phase 2B.12 must do
the same — they will need lockstep edits and are invisible to the canonical
tripwire.

---

## O. Agent-package compatibility

**Finding: agent packages have zero ruleset coupling, and the behaviour the
charter prefers is available for a one-line change.**

`agent_package.py` and `agent_package_cli.py` contain the substring `ruleset`
**zero times** (verified by count). `_check_compatibility` (`:671-698`) gates
on exactly two axes: `kind ∈ SUPPORTED_KINDS = ("python","blob")` and, for
Python, `agent_api_version ∈ SUPPORTED_AGENT_API_VERSIONS = {1,2}`.

### O.1 Behavioural proof

A real Agent API v1 package was exported from the bundled `claimer` starter and
inspected twice — once as shipped, once with `SUPPORTED_AGENT_API_VERSIONS`
narrowed to `{2}` in memory:

```
[CURRENT: {1,2}]
   valid=True  compatible=True   agent_id='claimer' kind='python' api=1
   import -> OK claimer

[SCOPE C: {2}]
   valid=True  compatible=False  agent_id='claimer' kind='python' api=1
   compatibility_notes=('package requires unsupported Agent API v1; this
                         installation supports Agent API versions 2.',)
   import -> PackageCompatibilityError: Package is not compatible with this
             Bytefray installation: package requires unsupported Agent API v1;
             this installation supports Agent API versions 2.
```

Every metadata field survives: `agent_id`, `display_name`, `kind`,
`agent_version`, `entry_point`, `agent_api_version`, `agent_revision_id`,
`revision_complete`, `file_count`, `exported_at`, `bytefray_version`,
`integrity_verified`.

### O.2 Disposition

| Operation | Behaviour under Scope C | Change needed |
| --- | --- | --- |
| **Inspect** | Succeeds; reports `compatible=False` with an intelligible note naming the API generation | none beyond O.3 |
| **Import** | Refused with `PackageCompatibilityError` naming the reason | none beyond O.3 |
| **Execute** | Unreachable (never imported) | — |
| **Migrate** | **Do not invent one.** API v1 implements `reset`/`act` against `Observation`; `bytefray-rules-4` requires the `declare_processes` contract. That is a rewrite, not a remap. | — |

### O.3 Required change

`SUPPORTED_AGENT_API_VERSIONS = frozenset({2})` in `agent_api.py`. Its own
docstring already defines it as *"the authoritative set of Python Agent API
generations this installation's loader/runtime can actually execute"*, so
narrowing it is the definitionally correct edit, and `_check_compatibility`
consumes it rather than maintaining its own list — exactly as designed.

`SUPPORTED_KINDS` keeps `"blob"`: a blob package should still be
**inspectable**. A blob package's execution already fails at
`NoCompatibleRulesetError`.

**Minor wording defect found:** with a single supported version the message
reads *"supports Agent API versions 2"*.
`describe_supported_agent_api_versions` returns a bare `"2"` for the
one-element case while the caller's template says "versions". A one-word fix,
worth doing in the same batch.

---

## P. Runtime module disposition

Function/file-level classification. LOC are measured spans in this checkout.

### P.1 REMOVE WHOLE FILE

| File | LOC | Justification |
| --- | ---: | --- |
| `engine/src/battle_engine/instructions.py` | **14** | 12 VM opcodes + `enc`. Only importers are `vm.py` (inside `step`, itself removed), `builtins/registry.py` (removed) and `core.py`'s facade. |
| `engine/src/battle_engine/builtins/registry.py` | **146** | VM bytecode assembly. `SUPPORTED` + six `assemble_*` + `build_agent`. |
| `engine/src/battle_engine/builtins/__init__.py` | **3** | Package shim for the above. |
| `engine/src/battle_engine/match.py` | **126** | `MatchRunner`, the VM tick loop. **Only consumer is `core.Kernel`.** |
| **Subtotal** | **289** | |

### P.2 PARTIAL REMOVE

| File | Total | Dead | Retained — and why |
| --- | ---: | ---: | --- |
| `supervised_runtime.py` | 543 | **~401** (`_NullAgentInstance` 86–104; `SupervisedPythonEntrantController` 162–543) | **`_diagnostic_from_payload` + `diagnostic_for_worker_result` (105–161) — imported by `process_runtime.py:448` and `agent_validation.py:71`.** Corrects prior claim C-1. |
| `python_runtime.py` | 1,268 | **~495** (`PythonEntrantController` 897–1268 = 372; `OBSERVABLE_CORE_RULESET_IDS` 8; `has_observable_core` 11; `core_seed_byte` 6; `_snapshot_core_owners` 23; `seed_core_ownership` 32; `maintain_core_beacons` 43) | `apply_core_capture`, `_attribute_core_capture`, `core_addresses`, `CORE_SIZE`, `derive_agent_seed`, all `diagnose_*`, `RuntimeDiagnostic`, `PythonEntrantState`, `PythonRuntimeResult`, **`VULNERABLE_CORE_RULESET_IDS` + `has_vulnerable_core` (reader)**. `validate_action`/`apply_action`/`forfeit_entrant`/`_observation` become dead *if and only if* `agent_validation`'s v1 arm also goes. |
| `match_service.py` | 1,498 | **~328** (`_build_result` 69; `_build_python_result` 84; `_run_python_match_traced` 96; `_run_vm_match` 66; `_resolve_locality_reach` 13) + dispatch/schema branches | `_validate_v2_core_placement` + `OverlappingCoreError` **stay** — `_CORE_PLACEMENT_GUARDED_RULESET_IDS` retains `bytefray-rules-4`. |
| `vm.py` | 148 | **~85** (`load_code`, `step`) | Arena: `__init__`, `_rd32`, `_wr8`, `clear_tick_diffs`, `tick_diffs`. **Used by `process_runtime.py`.** |
| `core.py` | 151 | `Kernel` (85–151, **67**) | **Facade `__all__` is a declared compatibility surface** — see §E.3. Disposition decision, not mechanical deletion. |
| `agents.py` | 275 | small | `kind ∈ {builtin, blob}` branches; `agent_runtime_label`'s `[VM]` arm. |
| `agent_validation.py` | — | v1 arms at `:401-404`, `:630-633` | Everything else. |
| `agent_worker.py` | 667 | v1 arms at `:434`, `:507`, `:553` | **The `api_version` field itself must stay — trap N-1.** |
| `agent_scaffold.py` | 299 | v1 template mapping | Everything else. |
| `agent_evaluation.py` | 5,443 | v1/v2 methodology arms (§K.3) | Both tables, both predicates, all history readers. |
| `cli.py` / `tournament_cli.py` / `agent_test.py` | — | VM selection, `--ruleset` choices, v1 opponent | — |
| `ruleset_policy.py` | 778 | `RULESET_V1`, `RULESET_V2` objects + registry entries; unrestricted-kinds case | **All ID constants**, `OMITTED_RULESET_CANDIDATES` (rewritten), `NoCompatibleRulesetError`. |
| `tournament_service.py` | — | VM identity branch | — |
| `app/services/ruleset_options.py` | — | v1/v2 options + VM prose | — |

### P.3 KEEP FOR HISTORICAL READ (never remove)

`rules.py` in full (all ID constants, `_RULESET_ALIASES`,
`normalize_ruleset_id`); `result_model.resolve_result_ruleset` incl. the
`recovered` branch; `replay.resolve_replay_ruleset` incl. `schema_version == 3`
→ recovered; `SUPPORTED_SCHEMA_VERSIONS = (2,3,4)` readers;
`agent_trace`'s v1 reader; `VULNERABLE_CORE_RULESET_IDS` + `has_vulnerable_core`;
`_V2_METHODOLOGY_RULESET_IDS` + `is_ruleset_v2_methodology`;
`EVALUATION_RULES_COMPATIBILITY_ID`; `ActionKind`, `Observation`,
`ActionKind.MOVE/LOCAL_READ/LOCAL_WRITE`, `LOCALITY_ACTIONS`,
`MatchContext.locality_reach`, `Observation.locus`; `_readable_ruleset`;
`replay_history/` in full; `evaluation_history/` in full.

### P.4 Quantified production LOC

| Category | LOC |
| --- | ---: |
| Whole files removed | **289** |
| `supervised_runtime.py` partial | ~401 |
| `python_runtime.py` partial | ~495 |
| `match_service.py` partial | ~328 |
| `vm.py` partial | ~85 |
| `core.py` `Kernel` | ~67 |
| Scattered (CLI, Designer, evaluation, tournament, scaffold, workers) | ~250–400 |
| **Estimated total execution-dead production LOC** | **≈ 1,900 – 2,100** |
| **Historical-reader code deliberately retained** | **≈ 700–900** (rules/result/replay/trace readers, both core-status/methodology tables, `replay_history/`, `evaluation_history/`) |

Ranges are given where the exact figure depends on implementation choices
(§AH); the whole-file and measured-span figures are exact.

---

## Q. Historical replay/result compatibility

**This is Scope C's hard requirement, and it is met — proven behaviourally
against this checkout's real corpus, not argued from structure.**

### Q.1 Structural proof: zero reader → registry coupling

Every historical-reader module was counted for
`resolve_ruleset_policy` / `UnknownRulesetError` / `_RULESET_POLICIES` /
`PROCESS_RULESET_IDS`:

| Module | Refs |
| --- | ---: |
| `result_model.py` | **0** |
| `replay.py` | **0** |
| `replay_history/index.py`, `query.py`, `discovery.py` | **0** |
| `app/services/replay_history_presentation.py` | **0** |
| `client/src/battle_client/session.py`, `player.py`, `replay_status.py` | **0** |
| `evaluation_history/comparison.py` | **0** |

And the executable resolver has exactly **four** production call sites — all
new-execution or pre-launch:

```
match_service.py:1384      NativeMatchService.run dispatch
placement.py:266           core_placement_mode
ruleset_policy.py:501      agent_supported_by_ruleset
app/services/ruleset_options.py:145  Designer launch guard
```

### Q.2 Behavioural proof with the registry narrowed to `bytefray-rules-4`

Ten representative artifacts — one per recorded identity, plus the two
provenance-recovery classes — driven through the complete reader stack:

```
executable registry narrowed to: ['bytefray-rules-4']

=== result envelope decode + provenance attribution ===
  bytefray-rules-2                   ruleset='bytefray-rules-2'           conf='recorded'  winner='A'
  bytefray-rules-3-alpha1            ruleset='bytefray-rules-3-alpha1'    conf='recorded'  winner='A'
  bytefray-rules-4                   ruleset='bytefray-rules-4'           conf='recorded'  winner='B'
  bytefray-rules-4-alpha1            ruleset='bytefray-rules-4-alpha1'    conf='recorded'  winner='A'
  bytefray-rules-4-alpha2            ruleset='bytefray-rules-4-alpha2'    conf='recorded'  winner='A'
  bytefray-rules-5-r1-alpha1         ruleset='bytefray-rules-5-r1-alpha1' conf='recorded'  winner='tie'
  bytefray-rules-5-r2-alpha1         ruleset='bytefray-rules-5-r2-alpha1' conf='recorded'  winner='A'
  API v1 python, no ruleset_id       ruleset='bytefray-rules-1'           conf='recovered' winner='A'
  VM/blob executed, no ruleset_id    ruleset='bytefray-rules-1'           conf='recovered' winner='tie'
  VM/blob executed (phase3)          ruleset='bytefray-rules-1'           conf='recovered' winner='B'

=== replay: header + FULL tick reconstruction + core status + HUD label ===
  bytefray-rules-2          hdr='bytefray-rules-2'        recorded  ticks= 301  label='bytefray-rules-2'
                            cores=[A:8/8, B:8/8, C:8/8]
  bytefray-rules-3-alpha1   hdr='bytefray-rules-3-alpha1' recorded  ticks= 401  label='bytefray-rules-3-alpha1'
                            cores=[A:8/8, B:8/8, C:8/8]
  bytefray-rules-4          hdr='bytefray-rules-4'        recorded  ticks=  32  label='bytefray-rules-4'
                            cores=[A:None, B:None]
  bytefray-rules-4-alpha1   hdr='bytefray-rules-4-alpha1' recorded  ticks=   8  label='bytefray-rules-4-alpha1'
                            cores=[A:8/8, B:8/8]
  bytefray-rules-4-alpha2   hdr='bytefray-rules-4-alpha2' recorded  ticks=   4  label='bytefray-rules-4-alpha2'
                            cores=[A:None, B:None]
  bytefray-rules-5-r1-alpha1 hdr='bytefray-rules-5-r1-alpha1' recorded ticks=1001 label='bytefray-rules-5-r1-alpha1'
  bytefray-rules-5-r2-alpha1 hdr='bytefray-rules-5-r2-alpha1' recorded ticks=  92 label='bytefray-rules-5-r2-alpha1'
  API v1 python, no ruleset_id      hdr='bytefray-rules-1' recovered ticks= 301
                            label='bytefray-rules-1 (recovered)'
  VM/blob executed, no ruleset_id   hdr='bytefray-rules-1' recovered ticks= 301
                            label='bytefray-rules-1 (recovered)'
```

Every row: correct decode, correct attribution and confidence, full
tick-by-tick reconstruction, correct HUD label, correct per-entrant core
status — **with `bytefray-rules-1` and `bytefray-rules-2` absent from the
executable registry**.

Note the core-status column is *correctly asymmetric*: `rules-2`,
`rules-3-alpha1` and `rules-4-alpha1` derive real `CoreStatus` (they are
`VULNERABLE_CORE_RULESET_IDS` members); `rules-4`, `alpha2` and the two V5
research identities return `None` (they never were). That asymmetry is the
execution/recognition boundary working, and it is exactly what §P.2's
retention of the vulnerable table protects.

**This is the first phase to prove readability for a genuine VM-executed
match**, which Scope C's predecessors never needed to test.

### Q.3 Evaluation-history readability

`is_ruleset_v2_methodology` / `is_ruleset_v4_methodology` operate on a
persisted `rules_compatibility_id` guarded by `FieldConfidence.RECORDED`, and
their consumers (`evaluation_history/verification.py:475`,
`evaluation_history/cli.py:140`,
`app/services/evaluation_history_workflows.py:105`,
`app/services/designer_workflows.py:943`) never touch the executable registry.
Historical evaluations therefore need **metadata only, not live execution** —
which is the finding that lets §J retire the reference agents.

### Q.4 Every historical-reader dependency on runtime code

| Reader | Depends on | Must be retained |
| --- | --- | --- |
| `client/.../replay_status.py` | `python_runtime.CORE_SIZE`, `core_addresses`, `has_vulnerable_core` | **Yes** |
| `client/.../renderers/pygame_renderer.py` | `python_runtime.core_addresses`, `apply_core_capture` | **Yes** |
| `evaluation_history/verification.py` | `agent_evaluation.is_ruleset_v4_methodology` | **Yes** |
| `evaluation_history/cli.py`, `app/services/*` | `is_ruleset_v2_methodology` | **Yes** |
| `app/services/replay_history_presentation.py` | nothing — shape-derived | — |

`replay_status.py` reaching into `python_runtime.py` (a module otherwise about
live execution) for a *display* concern is carried forward to Phase 3 (§AB),
unremediated.

> **The goal is met: delete execution, not history.**

---

## R. Replay / trace schema impact

### R.1 Replay schema

`replay.SCHEMA_VERSION = 4`; `SUPPORTED_SCHEMA_VERSIONS = (2, 3, 4)`.
Selection: `match_service.py:1177` —
`replay_schema_version = 4 if resolved_ruleset_id in PROCESS_RULESET_IDS else 3`.

| Schema | Writing under Scope C | Reading |
| ---: | --- | --- |
| **2** | already write-dead (pre-ruleset legacy shape; `adapt_v01_record` adapts it) | **MUST REMAIN** |
| **3** | **becomes write-dead** — no non-process ruleset remains | **MUST REMAIN** — and it is load-bearing: schema 3 + absent `ruleset_id` is exactly the Ruleset-1 recovery trigger (`replay.py:712`) |
| **4** | the only schema written | remains |

The selection expression collapses to the constant `4`. **`SUPPORTED_SCHEMA_VERSIONS`
must not be narrowed.**

### R.2 Trace schema

`TRACE_SCHEMA_VERSION = 1`, `TRACE_SCHEMA_VERSION_V2 = 2`. Selection:
`match_service.py:1440` — v2 for a process match, v1 otherwise.

| Schema | Writing | Reading |
| ---: | --- | --- |
| **v1** | **becomes write-dead** | **MUST REMAIN** (`agent_trace.py:458`) |
| **v2** | the only one written | remains |

### R.3 Rule

> Remove the **writers'** branch selection; keep every **reader**. Never update
> a historical artifact in place.

---

## S. Ruleset provenance recovery

Special attention, per the charter, to Ruleset 1.

| Item | Location | Disposition |
| --- | --- | --- |
| `BYTEFRAY_RULESET_ID` and every other `BYTEFRAY_RULESET_*_ID` constant | `rules.py`, `ruleset_policy.py` | **KEEP verbatim** |
| `normalize_ruleset_id` | `rules.py` | **KEEP verbatim** |
| `_RULESET_ALIASES` — exactly one entry, `evaluation-rules-1` → `bytefray-rules-1` | `rules.py:106` | **KEEP.** Must not be extended or re-pointed. |
| `resolve_result_ruleset` incl. `mode == "b2"` → recovered | `result_model.py` | **KEEP** — 673 artifacts |
| `resolve_replay_ruleset` incl. `schema_version == 3` → recovered | `replay.py:712` | **KEEP** — same |
| `EVALUATION_RULES_COMPATIBILITY_ID = BYTEFRAY_RULESET_ID` | `agent_evaluation.py:161` | **KEEP meaning "the v1 methodology"** — must never come to mean the control |
| `_readable_ruleset` (shape-derived labeller) | `replay_history_presentation.py` | **KEEP** — needs no per-identity table |

Verified with the registry narrowed:

```
normalize_ruleset_id('bytefray-rules-1')   -> 'bytefray-rules-1'    (unchanged)
normalize_ruleset_id('bytefray-rules-2')   -> 'bytefray-rules-2'    (unchanged)
normalize_ruleset_id('evaluation-rules-1') -> 'bytefray-rules-1'    (historical alias intact)
resolve_ruleset_policy('bytefray-rules-1') -> UnknownRulesetError
resolve_ruleset_policy('bytefray-rules-2') -> UnknownRulesetError
```

> **No retired historical identity is silently normalised to
> `bytefray-rules-4`.** That property holds today and must be pinned by a
> permanent negative test in Phase 2B.12.

---

## T. Fallback / default cleanup

All four "missing → Ruleset 1" fallbacks were **re-verified against current
source and then executed** with `_RULESET_POLICIES` narrowed to
`{bytefray-rules-4}`.

### T.1 Measured behaviour under Scope C

```
--- resolve_omitted_ruleset_for_agents ---
empty roster      -> 'bytefray-rules-1'      <== RETIRED ID RETURNED
API v2 python     -> 'bytefray-rules-4'                              OK
API v1 python     -> NoCompatibleRulesetError                        clean
VM/blob           -> NoCompatibleRulesetError                        clean
builtin kind      -> NoCompatibleRulesetError                        clean
python api=None   -> NoCompatibleRulesetError                        clean
mixed v1+v2       -> NoCompatibleRulesetError                        clean

--- resolve_omitted_ruleset_id (kind-only) ---
kinds=[]                 -> 'bytefray-rules-1'   <== RETIRED
kinds=['python']         -> 'bytefray-rules-1'   <== RETIRED  (today: 'bytefray-rules-2')
kinds=['vm']             -> 'bytefray-rules-1'   <== RETIRED
kinds=['python','vm']    -> 'bytefray-rules-1'   <== RETIRED
kinds=['builtin']        -> 'bytefray-rules-1'   <== RETIRED

--- match_service._resolve_ruleset_id ---
MatchRequest(ruleset_id=None) -> 'bytefray-rules-1'   <== RETIRED

--- agent_evaluation ---
EVALUATION_RULES_COMPATIBILITY_ID = 'bytefray-rules-1'
resolve_evaluation_ruleset_id(None) -> 'bytefray-rules-1'   <== RETIRED for new requests
```

### T.2 Classification and required post-retirement behaviour

| ID | Site | Class | Required change |
| --- | --- | --- | --- |
| **F-1** | `match_service._resolve_ruleset_id:513` — `request.ruleset_id or BYTEFRAY_RULESET_ID` | **MUST CHANGE** | Re-point at `BYTEFRAY_RULESET_V4_ID`. **This silently re-points every `match_id`/`result_id`/`replay_id` derivation for ruleset-omitting callers** — it is threaded into `canonical_match_id` and `_finalize_native_artifacts` by design. Do it deliberately and pin it with a test. |
| **F-2** | `resolve_omitted_ruleset_for_agents:643` — empty roster → `BYTEFRAY_RULESET_ID` | **MUST CHANGE** | **Fail closed** (raise) — an empty roster cannot produce a match anyway, and returning a retired ID is strictly worse than an explicit error. |
| **F-3a/b** | `resolve_omitted_ruleset_id:738` (empty kinds) and `:752-753` (`except NoCompatibleRulesetError: return BYTEFRAY_RULESET_ID`) | **MUST CHANGE — out-of-tree compatibility surface** | Zero in-tree production callers (all four CLIs use the API-aware resolver). The exception swallow is the worst of the four: it converts a clean failure into a silent retired-identity selection, and under Scope C it does so for **every** input including plain `{"python"}`. Recommended: delete the swallow and let `NoCompatibleRulesetError` propagate; keep the function as a thin delegating shim projecting Python as **API v2**. |
| **K-1** | `EVALUATION_RULES_COMPATIBILITY_ID` / `resolve_evaluation_ruleset_id:601` | **HISTORICAL CONSTANT + partial change** | The **constant** must stay `bytefray-rules-1` for historical attribution. The **new-request default** must become `bytefray-rules-4`. These are two different uses of one symbol and must be separated, not repointed together (trap). |
| — | `OMITTED_RULESET_CANDIDATES` | Must change | `('bytefray-rules-4',)` |

### T.3 Desired post-retirement pattern

* API v2 / process agents → `bytefray-rules-4`
* API v1 or VM/blob agents → **explicit `NoCompatibleRulesetError`** (already
  the behaviour; verified above)
* empty / ambiguous roster → **fail closed**
* **never** fall back to `bytefray-rules-1`

Everything except the four fallback sites already behaves correctly.

### T.4 Placement fail-safe (T-4 family) persists

```
core_placement_mode('bytefray-rules-1') -> 'zero'   (masked default, not an error)
core_placement_mode('bytefray-rules-2') -> 'zero'
core_placement_mode('bytefray-rules-4') -> 'seeded'
```

`placement.core_placement_mode` fails **safe**, not closed, for an
unregistered ID — by documented design, because real dispatch rejects first.
Phase 2B.10 §K found a third family member (`resolve_v4_seed_geometry`) only
by running tests. Phase 2B.12 should pin, not repair, this behaviour, and
should expect further members to surface only under execution.

---

## U. Mixed-roster behaviour

Investigated rather than assumed.

| Combination | Today | Under Scope C |
| --- | --- | --- |
| VM + Python | **Rejected** — `NativeMatchService.run:1353` `len(kinds) != 1` → `UnsupportedMatchCompositionError`; `tournament_service._division_kind:372` likewise | Unreachable — only one kind exists |
| API v1 + API v2 (both Python) | **Reaches dispatch**; rejected by `supports_agent` → `RulesetAgentUnsupportedError`. Omitted resolution raises `NoCompatibleRulesetError` (verified: `mixed v1+v2 -> NoCompatibleRulesetError`) | Unreachable |
| process + non-process | Same as above | Unreachable |

**No mixed-runtime execution machinery exists to remove.** What exists is
*rejection* machinery, and Scope C makes several rejection paths unreachable
rather than requiring new ones:

* `UnsupportedMatchCompositionError` and its "Mixed VM/Python matches are not
  supported" message → unreachable
* `kinds <= {"vm","python"}` and `len(kinds) != 1` checks → collapse
* `"Every VM entrant requires bytecode"` guard → dead
* `RulesetRuntimeUnsupportedError` → largely unreachable (only Ruleset 4
  remains, and it is Python-only)
* `designer_workflows.py:302` mixed-kind Designer message → dead

Tests asserting mixed-roster rejection become tests of an impossible state.
They should be pruned, not converted — but only after confirming each one is
not also covering the *entrant-uniqueness* or *empty-roster* guards in the
same function, which remain live.

---

## V. Configuration / request-model cleanup

The charter's own instruction — *avoid turning Phase 2B.12 into a broad
refactor* — is the operative constraint here.

### V.1 DO NOT REMOVE — trap N-1

**`api_version` is hashed into every Python entrant's RNG seed.**

```python
def derive_agent_seed(match_seed, slot, agent_id, api_version=AGENT_API_VERSION):
    material = f"battle2-python-v1\0{match_seed}\0{slot}\0{agent_id}\0{api_version}"
```

Demonstrated:

```
api=2 : 86762955828953501306682288691529971840
api=1 : 210707880586807825146836723747762358070
no api: 55502168643938182187801941078931631860
api version IS part of the seed material:        True
dropping the field from the hash changes v2 seed: True
```

Therefore the API-version field must be retained in `derive_agent_seed`'s hash
material, in `AgentMetadata`, in the `agent_worker` wire protocol
(`agent_worker.py:116, 220, 232, 398, 417, 432`), and in persisted entrant
metadata. Removing it as "obsolete now that only v2 exists" would change every
Ruleset 4 entrant's seed and therefore the frozen control's gameplay.

**Hardcoding the literal `2` at the call sites is safe; removing the field from
the hash is not.**

### V.2 Classification

| Field / parameter | Class |
| --- | --- |
| `MatchEntrant.code` (VM bytecode) | **Immediately removable** |
| `MatchEntrant.kind` | **Deferred** — still distinguishes `python` from nothing; removing cascades through identity, tournament, Designer, and persisted metadata |
| `MatchRequest.ruleset_id` | **Still needed** — explicit selection and provenance |
| `MatchRequest.locality_reach` | Already permanently inert (Phase 2B.9); **deferred to Phase 3** |
| `MatchRequest.scheduler_chunk_size` / `scheduler_rotate_start` | **Keep** — live Ruleset 4 overrides |
| `api_version` anywhere | **KEEP — V.1** |
| Trace-format selection | Immediately removable (collapses to v2) |
| Replay-schema selection | Immediately removable (collapses to 4) |
| `entrant.python_spec` | Keep |
| `SUPPORTED_AGENT_API_VERSIONS` | Narrow to `{2}` (§O.3) |
| `SUPPORTED_KINDS` (packages) | **Keep `blob`** — inspection must still work |
| `EvaluationRequest.ruleset_id` | Keep |
| `_V2_METHODOLOGY_RULESET_IDS` etc. | **Keep — historical readers** |

**Required retirement edits vs attractive cleanup:** only the rows marked
*Immediately removable* plus §T's fallbacks, §H, §M, §K.4 and §O.3 are
required. Everything else is Phase 3 input.

---

## W. CLI surface

### W.1 `bytefray run` — blocker B-1, verified live

```
$ python -m battle_engine.cli --ticks 3 --arena 64 --replay <path> --quiet
Agents:
 A: writer params={}
 B: runner params={}
exit=0
recorded ruleset_id: bytefray-rules-1
replay header:       bytefray-rules-1   schema 3
```

`--a-type` defaults to `"writer"` and `--b-type` to `"runner"`
(`cli.py:317-327`) — both VM builtins resolved through
`builtins.SUPPORTED`. **The default invocation of Bytefray's primary command
is a VM match under Ruleset 1.**

**Required change:** repoint the defaults at bundled Agent API v2 starters
(`v4_claimer` / `v4_scout` are the natural pair — both bundled, both simple,
both already covered by `test_v5_starter_agents.py`), and remove the
`--a-blob` / `--b-blob` / `SUPPORTED`-fallback resolution path
(`cli.py:498-509`).

### W.2 Post-retirement surface per command

| Command | Today | Under Scope C |
| --- | --- | --- |
| `bytefray run --ruleset` | v1, v2, v4 | **v4 only** — recommend removing the flag from the default help and accepting `bytefray-rules-4` for scripts |
| `bytefray run --a-type/--b-type` | any agent **or VM builtin**; defaults VM | Python agents only; **defaults repointed** |
| `bytefray run --a-blob/--b-blob` | blob path | **Remove** |
| `bytefray tournament --ruleset` | v1, v2, v4 | v4 only |
| `bytefray agents test --ruleset` | v1, v2, v4 | v4 only |
| `bytefray agents evaluate --ruleset` | v1, v2, v4 | v4 only |
| `bytefray agents create --api-version` | 1 (default), 2 | **2 only; becomes the default** (§H) |
| evaluation preset `ruleset:` | v1, v2 **only** | **v4** (§K.4) |

All four `--ruleset` lists are hardcoded, identical, and do **not** derive from
the registry — so each must be edited in lockstep or it will keep offering an
unexecutable identity.

### W.3 Recommended UX

> A V6 user runs, creates, tests and evaluates current Bytefray agents without
> choosing an engine generation.

Retaining `--ruleset bytefray-rules-4` as an accepted single-value flag is the
low-risk choice: existing scripts that pass it keep working, and Ruleset 6 has
an obvious place to appear. Removing the flag entirely is **not** recommended —
it would need re-adding for Ruleset 6.

### W.4 Stale help text — trap N-4

`agent_test.py:1053-1057` still says *"`bytefray-rules-4` and both v4 alphas
support Agent API v2"* and *"v4 alpha1/alpha2 remain selectable by name to
reproduce historical prerelease matches."* Both became false at Phase 2B.10.
A pre-existing defect, fixable now.

---

## X. Documentation impact

### X.1 Must stop claiming current support

| Doc | Current framing | Action |
| --- | --- | --- |
| `docs/RULES.md` | *"the frozen gameplay-semantics contract Bytefray intends to carry through the 1.x series"* | Restate as **retired from execution, historically recognised**; keep the gameplay description |
| `docs/RULES_V2.md` | *"**Status: permanent, stable semantic identity**"*; *"describes the game as it plays today"* | Same |
| `docs/AGENT_API_V1.md` | *"describes the implemented Bytefray Python Agent API v1. The current runtime supports…"* | Reframe as a historical contract; note `v5.0.0` as the last release that executes it |
| `docs/AGENT_AUTHORING.md` | API v1 authoring guidance, scaffold defaults | Repoint at API v2 |
| `docs/AGENT_LAB.md` | supervised v1 development matches | Update |
| `docs/specs/agent_scaffold.md` | documents `DEFAULT_API_VERSION = 1` and both template sets | Update with §H |
| `docs/specs/agent_test.md` | v1 reference opponent | Update with §M |
| `docs/specs/agent_evaluation.md` | v1/v2 methodology as current | Scope to historical |
| `ARCHITECTURE.md` | VM + Python runtime families | Single process runtime |
| `README.md`, `AGENTS.md`, `SECURITY.md`, `app/README.md` | trim "supported" phrasing | Minor |
| `docs/COMPATIBILITY.md` | already carries a "Retired from execution / still recognised" table from 2B.9/2B.10 | **Extend** with Ruleset 1/2, Agent API v1, VM/blob |
| `CHANGELOG.md` | — | New `### Removed` entry |

### X.2 Preserve unchanged

`docs/archive/**`, `docs/releases/**`, `docs/research/**` — the closed evidence
record, already past-tense. **Do not rewrite historical records in place**
(the standing rule Phase 2B.10 applied to `docs/ROADMAP.md`'s release-note
entries).

### X.3 Becomes more important, not less

`docs/RESULT_SCHEMA.md`, `docs/REPLAY_SCHEMA.md`,
`docs/specs/agent_package.md`, `docs/specs/evaluation_history.md`, and
`docs/COMPATIBILITY.md`'s legacy matrix — these explain artifact identities
that are now history-only, so they carry more weight after retirement.

### X.4 Changelog framing

> **Retired from execution:** Agent API v1 and VM/blob execution, and with them
> `bytefray-rules-1` and `bytefray-rules-2`. `bytefray-rules-4` is the sole
> executable gameplay ruleset; Agent API v2 is the sole agent contract.
> `bytefray agents create` now produces an Agent API v2 agent by default.
>
> **Historical results, replays, evaluations and Replay History entries
> recorded under the retired identities remain fully readable, indexable,
> filterable and replayable.** Agent packages containing Agent API v1 or
> VM/blob agents remain **inspectable** and report their incompatibility
> explicitly; importing one is refused with a clear message.
>
> **Exact re-execution of the retired engines remains available through the
> `v5.0.0` release** (tag, wheel and Windows installer).

### X.5 The `v5.0.0` fallback still holds

Phase 2B.8 established that `v5.0.0`'s ruleset registry was behaviourally
identical to the then-current tree. Phases 2B.9/2B.10 have since narrowed the
registry, but **`v5.0.0` itself is unchanged** and remains the exact
historical engine for all eight identities, Agent API v1 and the VM runtime.
It is one `git checkout v5.0.0` or one installer download.

---

## Y. Packaging / licensing impact

**Good news: almost no packaging file needs editing, because every relevant
declaration is a glob or derives from a Python constant.**

| Surface | Mechanism | Edit needed? |
| --- | --- | --- |
| `pyproject.toml` `package-data` | `battle_engine = ["data/**/*"]` | **No** — removed agent dirs drop out automatically |
| `MANIFEST.in` | only `prune tests` + bytecode excludes | **No** |
| `tools/bytefray.spec`, `bytefray_cli.spec`, `agent_designer.spec` | `collect_data_tree(starter_agents_dir, …)` — whole-tree | **No** |
| Same specs — templates | iterate **`TEMPLATE_DIRECTORIES_BY_API_VERSION`** | **No** — narrowing the dict in `agent_scaffold.py` (§H) propagates automatically |
| All four specs — hidden imports | `collect_submodules("battle_engine")` | **No** — removed modules drop out |
| `tools/installer.iss` | — | Review only |
| Licences | No third-party VM/bytecode dependency exists; `builtins/registry.py` and `instructions.py` are first-party | **None** |
| Windows smoke checks | Must not invoke `bytefray run` with default agents (§W.1) | **Review** |

**Artifact reduction:** 4 VM starter dirs + 2 v1 template dirs + up to 3
reference-agent dirs + 2 v1 fixture agent dirs leave the wheel, sdist and every
frozen build. With §I's HISTORICAL-ONLY decision, 5 benchmark-pinned agent
dirs remain on disk. Together with ~289 LOC of whole-file module removal and
~1,600 LOC of partial removal, the payload shrinks modestly; **the real
reduction is in reachable code paths, not bytes.**

**The one packaging trap to respect:** bundled starter content is
**content-hash-pinned** (`CURRENT_STARTER_DIGESTS`) and mirrored at
`agents/<name>/`. Phase 2B.10 §Q.1 broke this by editing a starter README.
Removing a starter requires updating the digest tables and the root-level
mirror **in lockstep** — this is a required edit for §I, not an optional one.

---

## Z. Test-suite disposition

### Z.1 Measured impact

Canonical suite run with a **scratchpad-only** pytest plugin narrowing
`_RULESET_POLICIES` to `{bytefray-rules-4}` at `pytest_configure`. No
repository file was created or modified; the isolated `--basetemp` was deleted
afterwards.

```
collected: 3,440
passed:    3,027
failed:      393
skipped:      20
errors:        0
   (3,027 + 393 + 20 = 3,440 — measurement complete)
```

**393 of 3,440 = 11.4% execution-dependent**, versus Phase 2B.8's
830 of 3,713 = 22.4% pre-Scope-A/B (§A.2 C-3).

> **Read these correctly.** They measure *execution dependence* — how many
> tests break when the identities stop being executable. They are **not**
> deletion counts.

### Z.2 Shape of the impact

393 failures spread across **52 files holding 1,467 collected cases**. Only
**5 files fail in their entirety**:

| File | Fail/Total | Nature | **Disposition** |
| --- | ---: | --- | --- |
| `test_ruleset_v2_promotion_equivalence.py` | 12/12 | The frozen-golden Ruleset-2 promotion proof **converted by Phase 2B.9** — still executes live under `bytefray-rules-2` | **DECISION REQUIRED** (§Z.4) |
| `test_ruleset_v1_equivalence.py` | 8/8 | The Ruleset-1 equivalence golden — the precedent the other two goldens copied | **DECISION REQUIRED** (§Z.4) |
| `test_output_paths.py` | 7/7 | Output-path handling, driven via `--a-type writer` (VM) | **CONVERT** — re-point at a Python agent; the subject is paths, not VM |
| `test_agent_evaluation_behavior.py` | 6/6 | Evaluation behaviour under API v1 | **CONVERT** — re-point at API v2 |
| `test_agent_lab_integration.py` | 4/4 | Agent Lab supervised-runtime integration | **REVIEW** — supervised v1 controller is retired, but the worker/diagnostic seam it covers is retained (§P.2) |

### Z.3 The dominant pattern

Sampled directly from source:

* `test_replay_reconstruction.py` (16/18) — its docstring states it exists *"to
  prove that the canonical `battle2.replay` stream is sufficient to
  reconstruct engine-observable match state at any tick using only the public
  typed reader API, without rerunning any agent."* It builds its replays with
  `build_agent("writer")` / `build_agent("runner")` — **VM builtins**. The
  *subject* is the reader and is fully current; only the fixture-production
  step is retired. → **CONVERT.**
* `test_evaluation_history_verification.py` (24/33) — its fixture declares
  `{"kind":"python","api_version":1}` and one test pins
  `ruleset_id: BYTEFRAY_RULESET_V2_ID`; it *runs* live evaluations and then
  verifies the persisted artifacts. The verification logic is historical-reader
  code that **must** survive. → **CONVERT.**
* `client/tests/test_replay_session.py` (7/50),
  `test_replay_history.py` (6/89), `client/tests/test_replay_status.py` (2/22),
  `test_ruleset_persistence.py` (2/20) — historical-readability files whose
  few failing cases produce their artifact live. → **CONVERT to frozen
  fixtures; never delete.**

> **The majority of Scope C's 393 failures are tests whose subject is current
> V6 behaviour and whose fixture-production step is retired.** Deleting by
> failure count would silently drop coverage of supported functionality. This
> is Phase 2B.10 §F.1's trap, now the common case.

### Z.4 The two equivalence goldens — an explicit decision

Phases 2B.9 and 2B.10 each converted a promotion-equivalence corpus to a
frozen-golden characterization rather than delete it, on the principle that a
promotion proof must not be traded for tidiness. Both still execute **one
live side**:

* `test_ruleset_v2_promotion_equivalence.py` runs live under `bytefray-rules-2`
* `test_ruleset_v1_equivalence.py` runs live under `bytefray-rules-1`

Under Scope C neither can run at all. Two honest options:

| Option | Assessment |
| --- | --- |
| **Fully freeze both sides** | Preserves the historical record as pure data. But the result no longer *proves* anything about executable behaviour — it becomes a digest comparing two frozen constants, which cannot regress. Low value, non-zero maintenance. |
| **Delete both, recording the loss in the changelog** | **Recommended.** These corpora prove that a *retired* identity was gameplay-identical to another *retired* identity. Once neither executes, the claim is unfalsifiable and unactionable. The evidence is preserved in `docs/archive/` and in the phase reports, and `v5.0.0` can still re-execute both sides. |

Either way this must be a **conscious, recorded decision**, not a silent
deletion — the same standard Phases 2B.9/2B.10 applied.

### Z.5 Classification summary

| Class | Content |
| --- | --- |
| **KEEP — Ruleset 4 / API v2** | `test_v4_*`, `test_v5_starter_agents.py` (54), `test_v5_agent_parameters.py` (124), `test_v5_alpha1_phase_b_engine_hygiene.py`, the process-runtime suites — the 3,027 that already pass under a narrowed registry |
| **KEEP — Historical readability** | `test_v5_replay_history_presentation.py`, `client/tests/test_hud_layout.py`, `test_replay_history.py`, `client/tests/test_playback_controller.py`, `test_evaluation_history_comparison.py`, `test_result_model.py`, `test_rules.py`, `test_ruleset_persistence.py` — **never delete; convert failing cases to fixtures** |
| **REMOVE — API v1 execution** | `test_python_runtime.py`'s v1 controller cases, `test_agent_evaluation_v2*.py`'s execution cases, `test_ruleset_v2*.py`'s execution cases, `test_default_python_agents.py`'s v1 starter cases |
| **REMOVE — VM execution** | `test_replay_reconstruction.py`'s VM-specific cases (not the file), VM-composition cases in `test_native_match_service.py`, `test_tournament_service.py` |
| **CONVERT** | The §Z.3 pattern — the bulk |
| **REVIEW** | `test_agent_test.py` (34/54), `test_agent_evaluation.py` (19/68), `test_designer_ruleset_options.py` (9/35), `test_ruleset_policy.py` (9/47), `test_agent_evaluation_presets.py` (14/21) |
| **NEW (additive)** | `test_v6_phase2b12_scope_c_retirement.py` — negative-execution + recognition-preserved coverage, mirroring the 2B.9/2B.10 pattern |

### Z.6 Test-count dependency table

An exact tripwire cannot honestly be given, because the final count depends on
four decisions the implementer makes on evidence. A dependency table is given
instead, per the charter's instruction to avoid false precision.

| Decision | Δ cases |
| --- | --- |
| Baseline (post-2B.10) | **3,440** |
| (a) Delete both equivalence goldens (§Z.4) | −20 |
| (a′) Freeze both instead | 0 |
| (b) Remove 4 VM + 2 API-v1-demo starters, keep 5 benchmark fixtures (§I) | −15 to −35 |
| (c) Remove 3 reference agents, retain `core_seeker` (§J) | −10 to −25 |
| (d) Convert vs delete the §Z.3 fixture-producing tests | −40 (convert-most) to −200 (delete-most) |
| (e) Prune mixed-roster rejection tests (§U) | −10 to −20 |
| (f) New Scope-C boundary test file | +15 to +25 |
| **Projected post-Scope-C collection** | **≈ 3,150 – 3,360** |

**The recommended path (convert-most, delete the two goldens) lands near
3,300–3,360.** The implementer must run `--collect-only` before and after
**each batch** and record the exact delta; a deviation is a finding to explain,
never a number to force.

---

## AA. Quantified simplification

### Before Scope C (current tree, measured)

| Dimension | Value |
| --- | ---: |
| Executable ruleset identities | **3** |
| Active agent API generations | **2** |
| Runtime families | **2** (VM, Python) — 3 controllers (`PythonEntrantController`, `SupervisedPythonEntrantController`, `ProcessMatchController`) + `core.Kernel` |
| Runtime dispatch arms in `NativeMatchService.run` | **3** |
| Replay schemas written | **2** (3 and 4) |
| Trace schemas written | **2** (v1 and v2) |
| Bundled starter agents | **21** (4 VM / 7 v1 / 10 v2) |
| Reference agents | **4** (all API v1) |
| Scaffold template pairs | **4** (2 v1 / 2 v2) |
| `bytefray agents create` default | **API v1** |
| `bytefray run` default agents | **2 VM builtins** |
| CLI `--ruleset` choices | **3** × 4 commands |
| Designer ruleset options | 1 / 3 / 3 (Simple / Advanced / Evaluation) |
| Evaluation methodology generations reachable | **3** |
| "Missing → Ruleset 1" fallbacks | **4** |
| Ruleset-ID allow-list tables in production | **13** |
| Canonical tests | **3,440** |
| Tracked Python LOC | 167,709 |

### After Scope C (projected)

| Dimension | Value | Δ |
| --- | ---: | --- |
| Executable ruleset identities | **1** | −2 |
| Active agent API generations | **1** | −1 |
| Runtime families | **1** (Python process) — 1 controller | −1 family, −3 controllers |
| Runtime dispatch arms | **1** | −2 |
| Replay schemas written | **1** (4) | −1 |
| Trace schemas written | **1** (v2) | −1 |
| Bundled starter agents | **10** | −11 |
| Reference agents | **0 executable** (1 archived fixture) | −4 |
| Scaffold template pairs | **2** | −2 |
| `bytefray agents create` default | **API v2** | fixed |
| `bytefray run` default agents | **2 API v2 starters** | fixed |
| CLI `--ruleset` choices | **1** × 4 | −8 |
| Designer ruleset options | 1 / 1 / 1 | −4 |
| Evaluation methodology generations reachable *for new runs* | **1** | −2 |
| "Missing → Ruleset 1" fallbacks | **0** | −4 |
| Ruleset-ID allow-list tables | **≈ 6 active + 3 historical-read-only** | −4 active |
| Canonical tests | **≈ 3,150 – 3,360** | −80 to −290 |
| Execution-dead production LOC removed | **≈ 1,900 – 2,100** | |
| **Historical-reader code deliberately retained** | **≈ 700–900 LOC** | **0** |

### The honest summary

> Scope C removes roughly **1,900–2,100 LOC of production code and 11 of 21
> bundled agents**, but its real value is structural: **one dispatch arm
> instead of three, one agent contract instead of two, one schema writer
> instead of two per format, and zero fallbacks that can select a retired
> identity.** It deliberately retains 700–900 LOC of historical-reader code —
> that retention is the point, not a shortfall. This measures **active
> complexity reduction**, not maximised deletion.

---

## AB. Phase 3 implications

Recorded, not implemented.

1. **`agent_evaluation.py` (5,443 LOC) can be split by lifetime.** After Scope
   C the module contains a **current-execution** half (v4 methodology only,
   straight-line) and a **historical-reader** half (both methodology tables,
   both predicates, all `evaluation_history/` adapters). The seam is already
   visible at the five `resolved_is_v2`/`resolved_is_v4` sites. This is the
   single largest context-locality win Scope C creates.
2. **Runtime dispatch disappears.** `NativeMatchService.run`'s three-arm branch
   collapses; `match_service.py` sheds ~328 LOC and its hardest-to-follow
   control flow.
3. **Ruleset negotiation becomes trivial.** `OMITTED_RULESET_CANDIDATES` has
   one member; `resolve_omitted_ruleset_for_agents` degenerates to a single
   compatibility check.
4. **Package validation simplifies** to a single API generation (§O).
5. **Worker protocols retain a compatibility field that must not be removed**
   (§V.1) — Phase 3 should document *why*, so a future reader does not
   rediscover it as dead weight.
6. **The execution/recognition table conflation is now proven asymmetric.**
   Phase 2B.8 recommended an explicit `historically_recognised_ids` table
   separate from the executable registry; Phases 2B.9 and 2B.10 each hit the
   ambiguity, and this phase found the two core-status tables **diverge** under
   Scope C (§A.2 C-2). That recommendation is now supported by four independent
   instances and should be treated as Phase 3's highest-value structural fix.
7. **`replay_status.py` imports from `python_runtime.py`** for a display
   concern — carried forward unchanged from 2B.7/2B.8.
8. **The two-file identity-constant split** (`rules.py` vs
   `ruleset_policy.py`) — unchanged, same recommendation.
9. **`core.py`'s compatibility facade needs an explicit policy** once `Kernel`
   and the opcodes are gone (§E.3).
10. **The T-4 fail-safe family may have further members.** Phase 2B.10 found
    `resolve_v4_seed_geometry` only by execution. A narrow repository-wide
    audit of every ruleset-ID-keyed placement/geometry resolver for
    fail-safe-vs-fail-closed behaviour is a well-scoped Phase 3 task.

---

## AC. Ruleset 6 readiness

**Scope C materially improves the path to `bytefray-rules-6`. It is not
created, stubbed or designed here.**

### AC.1 How Ruleset 6 would be registered

Today a new executable identity must be threaded through **13** tables:

| # | Table | File |
| ---: | --- | --- |
| 1 | ID constant | `rules.py` **or** `ruleset_policy.py` (no rule) |
| 2 | Policy object + `_RULESET_POLICIES` | `ruleset_policy.py` |
| 3 | `PROCESS_RULESET_IDS` | `ruleset_policy.py:415` |
| 4 | `OMITTED_RULESET_CANDIDATES` | `ruleset_policy.py:595` |
| 5 | `_CORE_PLACEMENT_GUARDED_RULESET_IDS` | `match_service.py:415` |
| 6 | `_V2_/_V4_METHODOLOGY_RULESET_IDS` | `agent_evaluation.py:613,651` |
| 7 | Evaluation `_validate` allow-list | `agent_evaluation.py:3383` |
| 8 | `_VALID_RULESETS` | `evaluation_presets.py:81` |
| 9 | `VULNERABLE_/OBSERVABLE_CORE_RULESET_IDS` | `python_runtime.py:128,144` |
| 10 | Four CLI `choices=` lists | 4 modules |
| 11 | Three Designer option tuples + default + 2 prose strings | `ruleset_options.py` |
| 12 | `DESIGNER_AUTO_TRACE_RULESET_IDS` | `designer_workflows.py:327` |
| 13 | Replay/trace schema selection (via `PROCESS_RULESET_IDS`) | `match_service.py:1177,1440` |

After Scope C: table 9's observable half disappears and its vulnerable half
becomes **historical-read-only** (a new ruleset never joins it); table 6's v2
half becomes historical-read-only; tables 3, 5, 12 hold one member; tables 10
and 11 become one-entry lists; table 8 is **fixed** (§K.4) and finally contains
the control. Adding Ruleset 6 changes from *"extend thirteen heterogeneous
allow-lists, several of which encode a superseded product history"* to
*"add a second entry alongside the control."*

### AC.2 Which runtime it should inherit

**`ProcessMatchController` / Agent API v2, unambiguously.** After Scope C it is
the only runtime, `process_runtime.py` contains **zero ruleset-ID branching**,
and all gameplay variation is policy-field-driven (`core_placement`,
`process_selection`, scheduler mode/chunk/rotate). A Ruleset 6 that needs new
placement or selection semantics must extend
`RulesetPolicy.CORE_PLACEMENT_MODES` / `PROCESS_SELECTION_MODES` — correct by
design, but worth knowing in advance.

### AC.3 Baggage Scope C removes from Ruleset 6's path

* Four fallbacks that would otherwise let a Ruleset-6-era omitted selection
  resolve to a retired identity (§T).
* Runtime-kind negotiation — Ruleset 6 never has to answer "does this support
  VM?".
* API-generation negotiation — one generation.
* Two dead schema-writer branches that a new ruleset would otherwise have to
  be classified against.
* `evaluation_presets._VALID_RULESETS`'s inability to name the control.

### AC.4 The constraint to honour

`ruleset_policy.py:611-624`'s V5 constraint remains exactly right and must be
carried into Ruleset 6: **an experimental identity must require *explicit*
selection and must never be added to `OMITTED_RULESET_CANDIDATES`**, because
silently reassigning the omitted slot would contaminate every comparison
against the frozen control.

**Answer: yes — after Scope C, future gameplay experimentation can stay
entirely within Agent API v2 / process execution.**

---

## AD. Retirement-strategy comparison

| Strategy | Content | Assessment |
| --- | --- | --- |
| **A — Full Scope C** | Retire Rulesets 1/2 + Agent API v1 + VM together | **RECOMMENDED.** They are one dependency graph, not three. Ruleset 1 is the only VM executor, so retiring VM without Ruleset 1 leaves a registered ruleset whose defining capability is gone. Retiring Ruleset 2 without Agent API v1 leaves an API generation with no executable ruleset. Measured cost is 393 outcomes across 52 files — large but tractable, and **half** what Phase 2B.8 projected. |
| **B — Retire VM first, API v1 later** | VM/blob only | **Rejected.** Does not reduce risk and creates an incoherent interim: `bytefray-rules-1` would remain registered as "unrestricted runtime kinds" while no VM entrant can exist, and `bytefray run`'s defaults (§W.1) break in *this* step anyway. The interim state needs the same CLI/scaffold/starter work as A, then a second pass. |
| **C — Retire API v1 first, VM later** | Agent API v1 only | **Rejected, and technically incoherent.** Ruleset 1 is API v1 **and** the only VM executor. Retiring API v1 while keeping VM means Ruleset 1 must stay registered for VM, so `agents create`, the reference opponent, the v1 starters and the fallbacks all stay — i.e. nearly none of the benefit, all of the churn. |
| **D — Keep runtime, hide rulesets** | Remove surfaces, keep code executable | **Rejected, contrary to V6 goals.** Retains ~1,900–2,100 LOC of unreachable runtime, all 3 controllers, both schema writers, 11 stranded starters and 4 reference agents — the entire Phase 3 context-locality problem — while removing the ability to test any of it. Strictly worse than either keeping or removing. |
| **E — Compatibility-only frozen runtime** | Keep an internal executable old engine, remove product surfaces | **Rejected on honest maintenance cost.** Every future change to shared code (`vm.VM`'s arena, `apply_core_capture`, `derive_agent_seed`, the worker protocol, replay/trace writers) would have to be validated against a second runtime nobody uses. It would also require *retaining* the v1 starters and reference agents purely as its test corpus — the full Scope-C agent inventory, minus the user-visible benefit. **`v5.0.0` already is the frozen compatibility runtime**, at zero ongoing cost (§X.5), which makes E strictly redundant. |

---

## AE. Recommended strategy

> **Strategy A — full Scope C, implemented as one phase (2B.12) in
> dependency-ordered batches with explicit resumable checkpoints.**

Justification, in order of weight:

1. **The identities are one dependency graph.** Ruleset 1 ≡ VM executor; Ruleset
   2 ≡ the API v1 ruleset. Neither can be retired meaningfully alone (§AD B/C).
2. **The blockers must be fixed in any strategy.** `bytefray run`'s defaults,
   `agents create`'s default, `_VALID_RULESETS`, and the four fallbacks all
   break in the *first* stage of any staged plan, so staging buys no safety and
   doubles the surface work.
3. **Historical safety is proven, not projected** (§Q), and it is independent
   of how the retirement is sequenced.
4. **The cost is half what was projected** (§Z.1), and the failures are
   concentrated in conversion work whose per-file decisions do not interact.
5. **Atomic retirement is the only way to reach the stated boundary** — "V6
   executes only the current process-agent model" is not partially true in any
   useful sense.

**Caveat honestly stated:** Scope C is materially larger than 2B.9 or 2B.10 —
393 affected outcomes across 52 files, versus 2B.9's 269-case net change and
2B.10's 4. That is why §AG defines checkpoints rather than assuming one
sitting.

---

## AF. Dependency-ordered Phase 2B.12 implementation plan

Order derived from actual dependency direction in this repository.

| # | Batch | Contents | Why here | Verify |
| --- | --- | --- | --- | --- |
| **C-0** | Snapshot | Record HEAD, `git status`, `--collect-only` = **3,440**, and §Z.6's dependency table. Re-verify every line citation in this report. | Baseline for every delta | `pytest --collect-only -q` |
| **C-1** | **Freeze historical-reader characterization** | Before any removal: capture frozen replay/result/trace/evaluation fixtures for every artifact class in §Q.2, including a **VM-executed** and an **API-v1** match, committed via `.gitignore` negation (the 2B.9/2B.10 pattern). Add a historical-readability test asserting each still decodes, attributes, labels and replays. | Must exist while the old runtime can still produce artifacts | New tests pass on the **unmodified** tree |
| **C-2** | **Establish API v2 replacements** | Confirm `v4_claimer`/`v4_scout` as the new `bytefray run` defaults and `v4_claimer` as the Agent Test reference opponent. No removals yet. | C-3…C-5 depend on these existing | Targeted runs green |
| **C-3** | **Fix `agents create`** (§H) | `DEFAULT_API_VERSION = 2`; narrow `TEMPLATE_DIRECTORIES_BY_API_VERSION` to `{2: …}`. **Do not delete v1 template dirs yet** — Agent Test still uses `agent_template`. | Independent of the registry | Scaffold produces a runnable API v2 agent |
| **C-4** | **Repoint Agent Test** (§M) | `_reference_opponent_spec` always returns the v4 reference; drop the `else` arm and the call-site guard; fix `agent_test.py:990`'s `api_version: 1` projection and the stale help text (N-4). | Frees `agent_template` | `test_agent_test.py` green |
| **C-5** | **Repoint `bytefray run` defaults** (§W.1, B-1) | `--a-type`/`--b-type` → API v2 starters; remove `--a-blob`/`--b-blob` and the `SUPPORTED` fallback. | Must precede VM removal or the CLI breaks mid-phase | `bytefray run` with no agent args succeeds under `bytefray-rules-4` |
| **C-6** | **Fix `_VALID_RULESETS`** (§K.4, B-3) | `(BYTEFRAY_RULESET_V4_ID,)` | Independent; fixes a live defect | Preset with `ruleset: bytefray-rules-4` loads |
| **C-7** | **Remove user-facing Ruleset 1/2 choices** | Four CLI `choices=` → `[v4]`; Designer: delete `RULESET_V1_OPTION`/`RULESET_V2_OPTION`, narrow all three tuples, rewrite `RULESET_DESCRIPTION`, delete `VM_RULESET_EXPLANATION`. **Update the four `@pytest.mark.gui` files in lockstep.** | Surfaces don't derive from the registry — must be edited deliberately | `--help` shows one choice; GUI suite green |
| **C-8** | **Rewrite fallback/default resolution** (§T, B-4) | F-1 → control; F-2 → fail closed; F-3 → drop the swallow, project API v2; K-1 → split constant from default; `OMITTED_RULESET_CANDIDATES = ('bytefray-rules-4',)`. | Must precede deregistration, or errors degrade | Re-run §T.1's probe; **pin `match_id` stability explicitly** |
| **C-9** | **Deregister Ruleset 1 and 2** | Remove `RULESET_V1`/`RULESET_V2` objects and `_RULESET_POLICIES` entries. **Keep both ID constants.** Remove `bytefray-rules-2` from `_CORE_PLACEMENT_GUARDED_RULESET_IDS`. **Do not touch `VULNERABLE_CORE_RULESET_IDS`, `_V2_METHODOLOGY_RULESET_IDS`.** | The actual retirement | `resolve_ruleset_policy` raises for both |
| **C-10** | **Retire Agent API v1 runtime** (§P.2) | Remove `PythonEntrantController`, `SupervisedPythonEntrantController`, `_NullAgentInstance`, `match_service._run_python_match_traced`/`_build_python_result`, `agent_validation`'s v1 arms, `agent_worker`'s v1 arms, the v1 core-seeding block. **Keep `diagnostic_for_worker_result` (C-1 correction), `validate_action` only if a reader needs it, `VULNERABLE_CORE_RULESET_IDS`, `has_vulnerable_core`.** **Never touch `derive_agent_seed`'s hash material (N-1).** | Depends on C-9 | Engine mypy clean; Ruleset 4 suites green |
| **C-11** | **Retire VM execution** (§E) | Delete `instructions.py`, `builtins/`, `match.py`; remove `vm.VM.load_code`/`step`, `core.Kernel`, `match_service._run_vm_match`/`_build_result`, tournament VM identity branch. **Keep `vm.VM`'s arena.** Decide `core.py`'s facade explicitly (§E.3). | Depends on C-5 and C-9 | Import graph clean; process suites green |
| **C-12** | **Remove/retain starters and reference agents** (§I, §J) | Narrow `STARTER_AGENT_NAMES` to 10; delete 4 VM dirs + `raider` + `sentinel`; retain 5 benchmark-pinned dirs as fixtures; remove 3 reference agents, archive `core_seeker`; delete the two v1 template dirs. **Update `CURRENT_STARTER_DIGESTS` and the `agents/` mirror in lockstep (§Y).** | Depends on C-3/C-4 releasing them | `test_v5_alpha1_phase_e_starter_refresh.py` green |
| **C-13** | **Prune Evaluation / Tournament / Agent Test branches** (§K, §L, §M) | Collapse the v1/v2 methodology arms for **new** runs. **Keep both tables and both predicates.** Remove tournament VM handling. | Depends on C-9/C-10 | Evaluation + history suites green |
| **C-14** | **Remove legacy writers, keep readers** (§R) | Replay schema → constant 4; trace schema → constant v2. **`SUPPORTED_SCHEMA_VERSIONS` unchanged; v1 trace reader unchanged.** | Depends on C-10/C-11 | C-1's fixtures still read |
| **C-15** | **Package compatibility** (§O) | `SUPPORTED_AGENT_API_VERSIONS = frozenset({2})`; fix the "versions 2" wording. Keep `SUPPORTED_KINDS`'s `blob`. | Independent | Reproduce §O.1's two-state probe as a test |
| **C-16** | **Test conversion sweep** (§Z) | Work the 52-file list: convert fixture-producing tests, prune true v1/VM-execution cases, decide §Z.4. | Depends on C-9…C-14 | `--collect-only` per file; record deltas |
| **C-17** | **Add Scope-C boundary tests** (additive) | Negative execution for both retired IDs; `normalize_ruleset_id` unchanged; recognition preserved; no fallback reaches a retired ID; package inspect-vs-import. | Converts this audit's proofs into permanent barriers | New tests pass |
| **C-18** | **Packaging** (§Y) | Verify wheel/sdist/PyInstaller shrink automatically; review `installer.iss` and Windows smoke checks for VM-default invocations. | Depends on C-11/C-12 | Build inspection |
| **C-19** | **Docs / changelog** (§X) | Reframe `RULES.md`, `RULES_V2.md`, `AGENT_API_V1.md`; update authoring/spec/architecture docs; extend `COMPATIBILITY.md`'s retirement table; changelog per §X.4. **Do not touch `docs/archive/`, `docs/releases/`, `docs/research/`.** | Records the completed retirement | Review |
| **C-20** | **Residue scan** | `git grep` `bytefray-rules-1`, `bytefray-rules-2`, `api_version.*1`, `kind.*vm`, `build_agent`, `Kernel`. Every surviving hit must be a string constant, historical doc, reader, or negative test. | Catches missed surfaces | Manual classification |
| **C-21** | **Qualification** | §AH | Nothing left to change | §AH |

---

## AG. Safe implementation checkpoints

Scope C will not fit one model session. Each checkpoint below is a state where
work can stop and resume unambiguously.

| After | May temporarily fail | Must already be green | Must NOT yet be removed | Freeze before proceeding |
| --- | --- | --- | --- | --- |
| **C-1** | nothing | whole suite (3,440) | anything | **The historical fixtures — this is the phase's insurance policy.** Commit them. |
| **C-2** | nothing | whole suite | anything | — |
| **C-5** | a few `bytefray run` CLI characterization tests | scaffold, Agent Test, whole engine suite | registry, runtimes, starters | New `bytefray run` default output |
| **C-7** | CLI-help and Designer-option tests | engine execution suites; **all four GUI files** | registry, runtimes | GUI suite result (82 cases) |
| **C-8** | fallback and default-resolution tests | all Ruleset 4 suites | registry entries | **`match_id`/`result_id`/`replay_id` for a ruleset-omitting request, before and after** |
| **C-9** | **large** — most of the 393 | Ruleset 4 suites; C-1 fixtures | runtime code, starters, readers | Collection count at this point |
| **C-11** | VM tests | all process/Ruleset 4 suites; C-1 fixtures | readers, `vm.VM` arena | Import-graph listing |
| **C-12** | starter/reference tests | digest tests **must pass before and after** | readers | `CURRENT_STARTER_DIGESTS` before/after |
| **C-14** | none expected | everything except C-16's backlog | any reader, `SUPPORTED_SCHEMA_VERSIONS` | C-1 fixtures re-read |
| **C-16** | shrinking backlog | everything else | — | Per-file `--collect-only` log |
| **C-21** | nothing | **everything** | — | Full qualification record |

**Hard rules for any resumption:**

1. **C-1 must be committed before C-9.** Once Rulesets 1/2 are deregistered, no
   new historical fixture of any retired kind can be produced from the tree —
   only from `v5.0.0`.
2. **Never leave C-8 and C-9 split across sessions.** Between them the
   fallbacks name an identity the registry still has; after C-9 alone they
   would name one it does not.
3. **C-3/C-4 must both land before C-12** deletes `agent_template`.
4. **Record `--collect-only` after every batch**, with the delta explained.
5. **Re-verify this report's line citations** at resume — Phase 2B.8 §Y.4's
   standing caution applies with equal force here.

---

## AH. Qualification plan and expected test-count reconciliation

### AH.1 Ruleset 4 — unchanged

* `resolve_ruleset_policy("bytefray-rules-4")` returns fields identical to
  today: `seeded` / `round_robin` / `chunked` / chunk 2 / rotate `True` /
  API `{2}` / python-only.
* `test_v4_stable_ruleset_equivalence.py` (27, frozen-golden) passes
  **unmodified**.
* `test_v4_runtime_default_ruleset.py` (10), `test_v4_historical_immutability.py`
  (5), `test_v4_alpha2_placement.py` (67), `test_v4_alpha2_scheduler.py` (18),
  `test_v4_process_semantics.py` (5), `test_v4_trace_equivalence.py` (2),
  `test_v4_production_integration.py` (24) pass.
* **A control match run before and after Scope C produces a byte-identical
  `replay.jsonl` and identical `match_id`/`result_id`/`replay_id`.** This is
  the single most important check, because §T.2 F-1 and §V.1 both touch
  identity derivation.

### AH.2 Agent API v2 — full lifecycle

Creation (default, no flag) → execution → Agent Test → Evaluation →
Tournament → Designer → packaging (export/inspect/import round-trip), all
under `bytefray-rules-4` with no ruleset choice made.

### AH.3 Historical Ruleset 1/2 artifacts

Reproduce §Q.2 against the post-change tree for all ten artifact classes:
decode, provenance (`recorded` **and** `recovered`), replay index/filter/
display, tick reconstruction, core status, winner/termination, and
evaluation-history comparison.

### AH.4 Retired execution fails explicitly

```
resolve_ruleset_policy('bytefray-rules-1')          -> UnknownRulesetError
resolve_ruleset_policy('bytefray-rules-2')          -> UnknownRulesetError
NativeMatchService.run(ruleset_id='bytefray-rules-2') -> raises BEFORE any artifact write
omitted resolution, API v1 roster                   -> NoCompatibleRulesetError
omitted resolution, VM roster                       -> NoCompatibleRulesetError
omitted resolution, empty roster                    -> raises (no longer rules-1)
normalize_ruleset_id('bytefray-rules-1')            -> 'bytefray-rules-1'  (unchanged)
normalize_ruleset_id('bytefray-rules-2')            -> 'bytefray-rules-2'  (unchanged)
import_package(<API v1 package>)                    -> PackageCompatibilityError
inspect_package(<API v1 package>)                   -> valid=True, compatible=False, metadata intact
```

**No fallback to `bytefray-rules-4` anywhere.**

### AH.5 Packaging

No `builtins`/`instructions`/`match` module in the wheel or any frozen build;
no VM starter or v1 template directory in `data/`; starter digests consistent
with the `agents/` mirror.

### AH.6 Quality

* `python -m pytest` → green, 0 failed, 0 errors, **20 skipped** (the skip
  count must not change — it has held across 2B.9 and 2B.10).
* `mypy engine/src/battle_engine` → clean; `mypy client/src/battle_client` →
  clean.
* `ruff check .` → clean. **Delete every `.pytest-tmp*` directory first** —
  they are neither gitignored nor ruff-excluded.
* The four `@pytest.mark.gui` files run separately under
  `QT_QPA_PLATFORM=offscreen`.

### AH.7 Test-count reconciliation

Per §Z.6, the expectation is a **dependency table, not a single tripwire**:

| Milestone | Expected |
| --- | --- |
| Before any change | **3,440** |
| After C-9 (deregistration, before conversion) | ~3,440 collected, **≈393 failing** |
| After C-16 (conversion sweep) | **≈ 3,150 – 3,360**, 0 failing |
| After C-17 (boundary tests) | above **+15 to +25**, recorded explicitly |

Run `--collect-only` **before and after each batch**. Any deviation is a
finding to explain in the Phase 2B.12 report, never a number to force. The
2B.9 and 2B.10 precedent — deviating from a pre-computed range and reconciling
it line by line — is the expected discipline.

---

## AI. Risks / unresolved questions

| # | Risk / question | Status |
| ---: | --- | --- |
| **R-1** | **Scope C is materially larger than 2B.9 or 2B.10** — 393 affected outcomes across 52 files. §AG's checkpoints mitigate but do not remove this. The single biggest schedule risk is C-16, whose size depends on per-file judgement. | Mitigated, not eliminated |
| **R-2** | **The three shipped `bytefray-rules-2` benchmark corpora** (`v2_baseline.json`, `v2_baseline_corpus.json`, `v3_phase1_arena_action_grid.json`) are content-addressed against five API v1 starters. §I recommends retaining those five directories as frozen fixtures — but **whether the corpora themselves should be retained at all is a product decision this audit deliberately does not make.** If they are retired, five more agent directories go and §Z.6 row (b) shifts. | **Open — user decision** |
| **R-3** | **The two equivalence goldens** (§Z.4) — freeze or delete. Recommendation given; decision is the user's. | **Open — user decision** |
| **R-4** | **F-1's re-pointing silently changes `match_id` derivation** for every caller that omits `ruleset_id`, including research tools under `tools/`. Must be done deliberately and pinned. Several `tools/v3_closeout_*` scripts omit `ruleset_id` and would change identity. | Flagged; mitigation in C-8 |
| **R-5** | **The T-4 fail-safe family may have undiscovered members.** Two are known (`core_placement_mode`, `resolve_v4_seed_geometry`); both were found only by execution. Expect more to surface during C-16 rather than by inspection. | Expected; not blocking |
| **R-6** | **GUI-marked tests are invisible to the canonical tripwire.** The four root `tests/` files (82 cases in 2B.10) need lockstep edits in C-7 and a separate run. Forgetting them is the most likely silent breakage. | Flagged in C-7 and AH.6 |
| **R-7** | **`core.py`'s compatibility facade** — removing the VM re-exports is a compatibility decision, not dead-code cleanup, and two in-tree test files import through it. Left as an explicit disposition item rather than resolved here. | **Open — flagged for C-11** |
| **R-8** | **`validate_action`'s final disposition is conditional.** It is v1-only in execution, but `agent_validation.py` branches on API version and `ActionKind` must survive for replay/trace deserialization. Whether the function itself can go depends on C-10's exact shape. | Determinate at implementation time |
| **R-9** | **No genuine risk to historical-artifact compatibility was found** — and this is a checked, not assumed, conclusion: every reader module was counted for registry coupling (§Q.1) and ten real artifact classes, including VM-executed matches, were driven through the full reader stack with the registry narrowed (§Q.2). | **Closed** |
| **R-10** | **This report's line citations should be re-verified immediately before implementation.** No commit landed during this session, but time may pass. Standing caution from 2B.7/2B.8. | Standing |

---

## Appendix: reproduction commands

```bash
git rev-parse --abbrev-ref HEAD                     # v6-research
git rev-parse HEAD                                  # 551cf5a2c3c557906e80d4349e73fca765a914ae
git fetch origin --prune
git rev-list --left-right --count origin/v6-research...HEAD   # 0  0
git rev-list --left-right --count origin/main...main          # 0  0

python -m pytest --collect-only -q                  # sums to 3,440 across 147 reporting files

# Registry, read from live objects
python -c "from battle_engine import ruleset_policy as rp; print(sorted(rp._RULESET_POLICIES))"

# Bundled agent inventory, parsed from real manifests
python -c "
from pathlib import Path
from battle_engine.agents import agent_spec_from_dir
from battle_engine.starters import STARTER_AGENT_NAMES
base = Path('engine/src/battle_engine/data/starter_agents')
for n in STARTER_AGENT_NAMES:
    s = agent_spec_from_dir(base/n); print(n, s.kind, s.api_version)"
#   -> 4 builtin/None, 7 python/1, 10 python/2

# Executable-resolver call sites (expect exactly 4 production sites)
git grep -n 'resolve_ruleset_policy(' -- engine/src client/src app tools

# Reader modules must have zero registry coupling (expect all 0)
git grep -c 'resolve_ruleset_policy\|UnknownRulesetError\|_RULESET_POLICIES\|PROCESS_RULESET_IDS' -- \
  engine/src/battle_engine/result_model.py engine/src/battle_engine/replay.py \
  engine/src/battle_engine/replay_history/ client/src/battle_client/session.py \
  client/src/battle_client/replay_status.py app/services/replay_history_presentation.py

# `bytefray run`'s default agents are VM builtins (blocker B-1)
python -m battle_engine.cli --ticks 3 --arena 64 --replay <tmp>/replay.jsonl --quiet
#   -> "A: writer  B: runner"; result.json ruleset_id == bytefray-rules-1, replay schema 3

# api_version participates in the entrant seed (trap N-1)
python -c "
from battle_engine.python_runtime import derive_agent_seed
print(derive_agent_seed(12345,0,'A',2) != derive_agent_seed(12345,0,'A',1))"   # True

# Scope-C measurement: scratchpad-only plugin, no repo file created
#   plugin body:  def pytest_configure(config):
#                     from battle_engine import ruleset_policy as rp
#                     from battle_engine.rules import BYTEFRAY_RULESET_V4_ID
#                     rp._RULESET_POLICIES = {k: v for k, v in rp._RULESET_POLICIES.items()
#                                             if k == BYTEFRAY_RULESET_V4_ID}
PYTHONPATH=<scratchpad> python -m pytest -p narrow_c -q --basetemp=.pytest-tmp-2b11c -rf
#   -> 3,027 passed / 393 failed / 20 skipped / 0 errors  (sums to 3,440)
#   (delete .pytest-tmp-2b11c afterwards -- NOT gitignored, NOT ruff-excluded)

# Corpus distribution (walks runs/**/result.json; 53,458 files)
#   -> rules-2 31,053 (58.09%) | rules-4-alpha1 12,782 | rules-3-alpha1 6,984
#      rules-4 1,910 | absent->recovered 673 | r1-alpha1 42 | alpha2 7 | r2-alpha1 7
```
