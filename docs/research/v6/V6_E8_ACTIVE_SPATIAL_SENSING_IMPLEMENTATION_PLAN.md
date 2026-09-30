# Bytefray V6 E8 — Active Spatial Sensing: Implementation Plan

**Status: DRAFT for the research lead's review**, at the stop before any engine or agent code.
- **What it does.** It maps every item of the registered pre-registration to an implementation obligation or a test obligation, and orders the work into phases and stops.
- **What exists at this commit.** Only phase I8-0: the machine-readable pre-registration, the registered decision logic, their tests, and the pre-registration freeze. No Ruleset field, action, agent, package, seed, match or probe exists.
- **What it may not do.** It never changes a registered item. Where the registered text leaves an implementation detail open, this plan names a **plan decision** (P8-n, §9) for review. Where transcription or mapping found something the research lead should decide, it is listed in §10.

**Branch:** `v6-research` at `00fb420` (pre-registration revision 3).
**Date:** 2026-09-30
**Governing records:**
- [`V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md`](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) (**PR8**), **revision 3**, registered at `00fb420`, SHA-256 `a822bd15d9be8f968facb2f7b9c7e228d0e59b65ce34b790ae2a9e3538583a5a`. Revisions 1 (`28925fd`) and 2 (`090d11e`) are historical provenance.
- [`V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md`](V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md) (**E8-DR**), including its §F.3 ruling on the Agent API (A1 containment).
- [`V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md`](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**E6-IP**) §5.2 and [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (**E6-A1**), whose posture, verification and core-cursor semantics PR8 §3.2 reuses.
- AGENTS.md: architecture boundaries, testing and compatibility requirements.

---

## 0. Ground Rules

- **PR8 governs.** Its markdown is the authoritative wording. The JSON transcription, `tools/research/v6/e8/preregistration.json`, is its machine-readable form, and the loader refuses to run unless the two agree (§2).
- **No implementation-driven edits to the pre-registration.** If an implementation phase finds that a registered item cannot be implemented as written, it stops and reports. The pre-registration is then corrected, or not, by the research lead, before any seed exists.
- **Every phase is separately authorized.** Each ends at a stop for review, and each commit reports exact test counts. Nothing is pushed without the research lead's approval, except where a ruling says to push.
- **No gameplay probe.** Family behavior is verified by engine-level tests against scripted, non-family opponents, asserting actions and never an outcome (PR8 §3.2; SYN6 §H, item 4). Treatment semantics are verified by scripted, non-family agents only.
- **Forbidden changes** (the E-series pattern):
  - `scheduler.py`, `placement.py` and the capture and disruption rules;
  - the replay and result schemas;
  - every existing fixture, Ruleset literal and golden;
  - all E2–E7 tooling, freezes, pre-registrations and corpora;
  - `client/` and `app/`.
- **Additive-only surfaces.** The engine changes of §4 are additive and defaulted. Every existing Ruleset reproduces byte for byte (D8-6).

---

## 1. Phases, Commits and Stops

| Phase | Content | Ends with |
|---|---|---|
| **I8-0** (this commit set) | The machine-readable pre-registration; the loader and its equivalence checks; the registered decision logic; totality and invariant tests; this plan; the pre-registration freeze `v6-e8-prereg-v2-<12 hex>`, which supersedes v1 before any exposure | **Stop for review** before any engine or agent code |
| **I8-1** | **Parent byte-identity goldens** for C8 and C8L, committed before any engine file changes (D8-6) | The goldens commit |
| **I8-2** | The engine surface of §4: `RulesetPolicy.sensing_mode`, SENSE, the observation, context and trace fields, the two provisional Rulesets, and A1 containment. Engine tests, including the delivery tests of PR8 §10. | Focused tests pass; parent goldens unchanged. **Stop.** |
| **I8-3** | The family of §5: one policy source, 22 packages, behavior tests (ADAPT8's freeze tests included), the D8-9 static gate, fingerprints | **Stop.** |
| **I8-4** | The static census (§3.5) from the frozen packages; the structural matrix identity `v6-e8-matrix-v1-<12 hex>`, committed with the census and the seat strata inputs (PR8 §9, step 1) | The family freeze. **Stop.** |
| **I8-5** | The runner, trace capture and indexing, gates (D8-1 to D8-15), re-derivation, telemetry and the analyzer, built on the I8-0 decision logic; the analysis freeze `v6-e8-analysis-v1-<12 hex>`, which carries the pre-registration freeze identity | **Stop.** |
| **I8-6** | Seed generation, exactly once; commitment; the execution identity | A separately authorized step |
| **Q8** | The controls; CQ8-1 to CQ8-5; the strata committed before any treatment cell | A separately authorized step |
| **T8** | The treatment; its gates; the frozen analysis; the reveal and D8-10; E8-D's final status; interpretation, disposition and the results record, in PR8 §9's order | A separately authorized step |

---

## 2. What I8-0 Froze

| Artifact | Role |
|---|---|
| `tools/research/v6/e8/preregistration.json` | The transcription of PR8 revision 3. Every value under a key named `text` is registered wording, verbatim with only emphasis removed. It pins the markdown's SHA-256 and registration commit, and records revisions 1 and 2 as history. |
| `tools/research/v6/e8/preregistration.py` | The loader. It fails closed unless the JSON digest is the pinned one, the markdown digest is the registered revision's, the JSON is internally consistent, and the JSON equals the markdown. The loaded registration is deeply immutable. |
| `tools/research/v6/e8/decision.py` | The registered decision logic. It reads every registered value from the loaded registration and supplies only the predicates, in the registered orders. |
| `engine/tests/test_v6_e8_preregistration.py` | The transcription tests |
| `engine/tests/test_v6_e8_decision.py` | The totality and invariant tests |
| `tools/research/v6/e8/preregistration_freeze.py` and `preregistration_freeze_v2.json` | The operative freeze record and its identity: every artifact above and this plan, pinned by SHA-256 at the tooling commit |
| `tools/research/v6/e8/preregistration_freeze.json` | Freeze v1, `v6-e8-prereg-v1-116c9ed83400`, kept byte for byte as superseded before any exposure. It pinned revision 2 and no longer loads. |

**The research lead's seven required showings**, and the tests that make each:

| Required | Tests |
|---|---|
| **The JSON matches the markdown** | `test_the_transcription_is_internally_consistent_and_equals_the_markdown`; `test_every_registered_text_is_verbatim_in_the_markdown` (all 357 registered texts); 30 markdown-drift and 18 internal-drift cases, each of which must be reported; a disagreeing but self-consistent file must fail to load |
| **The interpretation rows cover every combination exactly once** | `test_every_triple_maps_to_exactly_one_row` (all 18 triples); an overlapping or a missing row fails closed; the JSON's own coverage check (`internal_problems`) |
| **The four-outcome logic is exhaustive and ordered** | `test_the_core_answer_is_exhaustive_and_ordered` (all 72 combinations): each outcome's definition is evaluated independently, at least one always holds, and the answer is the first in the registered order; `test_the_order_decides_the_overlaps`; a reordered implementation fails closed |
| **The KC8 mappings are deterministic** | Every one of the 1,023 non-empty universal subsets of Π_F gets exactly one KC8-1 label, and every one of the 31 of A8 exactly one KC8-6 label, each equal to an independent reading of the registered rule and unchanged under every input order. An empty or out-of-set universal set fails closed. |
| **H8-SEAT's bootstrap is joint** | A recording source shows that, in each of the 1,000 draws, control and treatment are recomputed from the **same** seed-position tuple. A paired-shift example is stable under the joint draws and not under independent ones. |
| **"stab ≥ 9/10" means ≥ 900/1000** | `stable(k)` holds exactly for k = 900 to 1000; malformed counts and any other resample count fail closed; the draws equal E6's `payoff.resample_positions` |
| **No registered set can be mutated after the freeze** | The loaded registration is read-only at every depth; every registered set in the decision logic is a tuple or frozenset; results are frozen; and the freeze record pins every file's digest |

---

## 3. The Registered-Item Map

Every registered item appears once. **Done** means the item is implemented and tested at I8-0. **JSON** means it is transcribed and checked against the markdown, but it is a record, not an executable rule.

### 3.1 Boundaries, decisions and the question (PR8 header, §0, §1)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| B-1 to B-12 | Transcribed; each is implemented where its section is (below) | JSON `boundaries` | Table equality with the markdown | Done |
| R-1 identity, tooling path | Tooling under `tools/research/v6/e8/`; identities `v6-e8-*` | this package | Freeze record | Done |
| R-2 *w* = 27, R-3 coverage and traversal | The engine's SENSE window (§4.2); the family's traversal (§5.3); D8-1's re-derivation | `process_runtime.py`; policy source; `rederive.py` | Engine tests; behavior tests; the JSON's A.1 and A.3 recomputation | I8-2, I8-3, I8-5 |
| R-4 ε, R-5 bootstrap, R-6 tick bound, R-7 seeds | Constants read from the registration | `decision.py` | Stability and draw tests | Done |
| R-8 k = 2, consecutive verification observations | The family's ADAPT8 rule (§5.4); ADAPT8's freeze tests | policy source | §5.6 | I8-3 |
| R-9 no magnitude floor | H8-SEAT by sign and stability only | `decision.seat_layers` | Seat tests; `seat_magnitude_floor` is null | Done |
| R-10 eleven members, R-11 *m* on [8, 64] | The family's packages and evasion draws | policy source, manifests | Behavior tests; fingerprints | I8-3 |
| R-12 trace field names | The engine's trace fields (§4.3) | `agent_trace.py`, `agent_api.py` | Engine tests | I8-2 |
| §1 question, conjunction, requirement C separate | The core answer over H8-SUB, H8-CHANNEL and H8-REPEAT; H8-ADAPT separate | `decision.core_answer`, `decision.adapt_reading` | Exhaustive mapping tests | Done |
| §1 scope sentence | Carried verbatim with every H8-REPEAT reading and the YES answer | `decision.repeat_reading`, `decision.core_answer` | Reading tests | Done |

### 3.2 Treatment, conditions and the sensing action (§2)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| §2.1 `sensing_mode`, `"passive"` default, byte identity | An additive, defaulted Ruleset field | `ruleset_policy.py` | Parent goldens (D8-6); every existing Ruleset's policy unchanged | I8-1, I8-2 |
| §2.1 under `"active"`: empty visibility | Visibility suppressed at the observation boundary | `process_runtime.py` | Engine test; D8-2 | I8-2 |
| §2.2 C8 and C8L, unchanged | Reused Ruleset identities, no edit | `rules.py` (read only) | D8-6 provenance | I8-2 |
| §2.2 T8 and T8L, provisional identifiers | Two research Rulesets, each its parent plus `sensing_mode = "active"` | `rules.py`, `ruleset_policy.py` | One-field-difference test; identifiers fixed in the freeze record before any seed | I8-2 |
| §2.2 fixed across conditions | No change to arena, ticks, quota, chunk, rotation, K, placement, spawn, pass order | — | A policy-equality test over every field except `sensing_mode` | I8-2 |
| §2.2 no T8+ | No Ruleset with passive visibility and SENSE together | — | The pre-match gate refuses it | I8-2 |
| §2.3 form, normalization, reach, result, distance, price, no effect, no exposure, delivery, passive refusal, suppression | The SENSE action (§4.2) | `agent_api.py`, `process_runtime.py` | Engine tests, one per property (§4.6) | I8-2 |
| §2.4 coverage, 55 cells | The window predicate *d*(*x*, *c*) ≤ 27 | `process_runtime.py`; `rederive.py` | Engine tests at distances 27 and 28; the JSON's recomputation | I8-2, I8-5 |
| §2.5 discovery and re-acquisition traversals; verification | Member semantics (§5.3) | policy source | Behavior tests | I8-3 |
| §2.5 knowledge updates and matching (KU-1 to KU-9) | Member semantics (§5.2) | policy source | Behavior tests, one per rule | I8-3 |

### 3.3 Population (§3)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| §3.1 the eleven members and their parameters | Manifests with those parameters | `tools/research/v6/e8/fixtures/agents/` | Parameter-table test against the JSON | I8-3 |
| §3.1 Π_F, Π, A8; phase-sensitive members | Sets read from the registration | `decision.py` | Set tests | Done |
| §3.1 no purpose-built relocator | No member beyond the eleven | — | Package-count test | I8-3 |
| §3.2 initial acquisition ends once the enemy core is confirmed, and re-acquisition is a separate state [Revision 3] | Discovery also requires an unconfirmed enemy core (§5.3) | policy source | §5.6's initial-acquisition tests | I8-3 |
| §3.2 the order of an offer; acquisition-eligibility; known sets; the channel difference; re-acquisition precedence; the callback index; E6's semantics as corrected by E6-A1; every parameter row | The policy specification of §5 | policy source | §5.6 | I8-3 |
| §3.2 no SENSE when `sensing_window` is `None` | A context guard on every SENSE path | policy source | D8-9 statically; CQ8-1 dynamically | I8-3, Q8 |
| §3.2 ADAPT8's freeze tests | Engine-level tests in every registered case | `engine/tests/` | §5.6 | I8-3 |
| §3.3 packages, opaque IDs, one source, seat labels, static class | 22 packages, one byte-identical `agent.py` | fixtures | Byte-identity and discipline tests | I8-3 |
| §3.4 F1, F2, counts | The matrix definition | `matrix.py` | Count tests: 3,520 + 704 = 4,224 per condition, 16,896 in all | I8-4 |
| §3.5 the census | `decision.census` applied to the frozen manifests' parameters; committed with the structural identity | `decision.py`; freeze record | Census tests (it gives `("EVADE8",)` on the transcription and follows the parameters) | Done (rule); I8-4 (commit) |

### 3.4 Operationalizations (§4)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| O-VALUE, O-PAYOFF, O-EPS, O-BR | PR6 §4 reused, with E8's sets | `payoff.py` (E8) | Unit tests against E6's on shared fixtures | I8-5 |
| O-BOOT: 1,000 draws from `random.Random(42)`, joint | `decision.DRAWS`; every stability uses them | `decision.py` | Equal to E6's `payoff.resample_positions`; joint-draw tests | Done |
| stab ≥ 9/10 as ≥ 900 of 1,000 | `decision.stable` | `decision.py` | Exhaustive over 0 to 1,000 | Done |
| O-CLASS, O-EARLY, O-SEAT, O-CONTACT, O-EVIDENCE | E3's and E4's analyzers reused, pinned in the analysis freeze | `analyze_e8.py` | Reused qualification | I8-5 |
| O-NEUTRAL | `decision.neutral` | `decision.py` | Boundary tests | Done |
| O-ACQ, O-REACQ, O-VERIF (descriptive) | Trace extractors | `telemetry.py` (E8) | Scripted-trace tests | I8-5 |

### 3.5 Gates and hypotheses (§5)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| D8-1 sensing exactness | An independent re-derivation of every applied SENSE's tuple | `rederive.py` | Scripted scenarios; a planted mutation must fail | I8-5 |
| D8-2 no free sensing | A trace scan | `gates.py` | A planted leak must fail | I8-5 |
| D8-3 no-information identity | Record equality over `decision.d8_3_matched_pairs()`: 576 per T-condition | `gates.py` | A planted divergence must fail | Done (pairs); I8-5 (gate) |
| D8-4 charging, D8-5 no state change | Trace and replay scans | `gates.py` | Planted violations must fail | I8-5 |
| D8-6 parent identity | Goldens before any engine change | `engine/tests/test_v6_e8_parent_byte_identity.py` | Goldens | I8-1 |
| D8-7 initial invisibility | Tick-0 distances | `gates.py` | Seeded-layout unit test | I8-5 |
| D8-8 no early blind strike | A ticks-1-to-2 trace scan | `gates.py` | A planted leak must fail | I8-5 |
| D8-9 discipline and containment | The static gate, plus the SENSE guard check | `discipline.py` | Negative controls must fail | I8-3 |
| D8-10 seed commitment | Reveal-time verification | `seeds.py` | Seed tests | I8-6 |
| D8-11 mirror relabeling | E4's relabel gate, reused | `gates.py` | Reused tests | I8-5 |
| D8-12 trace completeness | Per-cell trace and binding checks | `traces.py` | Missing or mis-bound traces must fail | I8-5 |
| D8-13 delivery consistency | The next-record reflection check, over later ticks | `gates.py` | The delivery tests' traces; a planted mismatch must fail | I8-2, I8-5 |
| D8-14 no invalid action | A forfeit scan | `gates.py` | A planted forfeit must fail | I8-5 |
| D8-15 window fidelity | `ResetRecord.sensing_window` per condition, with D8-1 | `gates.py` | Planted wrong windows must fail | I8-5 |
| E8-D = PASS iff every clause passes; final after D8-10 | The gate aggregator; the runner's order | `gates.py`, `run_e8.py` | Order tests (§8) | I8-5 |
| CQ8-1 to CQ8-5 | Control qualification; CQ8-4 by `decision.control_against_control` | `gates.py`, `run_e8.py` | Planted failures; CQ8-4's own test | Done (CQ8-4 rule); Q8 |
| H8-SUB, H8-PAR, H8-CHANNEL | `decision.complement_status` over P_none and Q_none | `decision.py`; predicates in `analyze_e8.py` | Exhaustive status tests | Done (rule); I8-5 |
| H8-LESS, H8-REPEAT, H8-ADAPT | `decision.bootstrap_status`; `decision.repeat_status` | as above | Status tests; NOT EVALUABLE iff 𝒞 is empty | Done (rule); I8-5 |
| H8-FL, H8-TAX | `decision.fl_status`, `decision.tax_status` | `decision.py` | Boundary tests; no empty-denominator convention | Done |
| H8-SEAT | `decision.seat_layers` | `decision.py` | Joint-draw tests | Done |
| Definitions (BR^A, L8, Δ^R, U, FL, A and B) | Predicates over u and cells | `analyze_e8.py` | Unit tests | I8-5 |

### 3.6 Flags, the seat criterion, reporting and the companion (§6)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| PF8-1 to PF8-3 | Shares and captures on the primary arm's F1 | `analyze_e8.py` | Unit tests | I8-5 |
| PF8-4 (unit layer), PF8-5 and H8-SEAT (family layer) | `decision.seat_layers`, with the 66 units of `decision.SEAT_UNITS` | `decision.py` | Unit-layer and joint-draw tests | Done |
| ΔG's 2.5, 50 and 97.5% points | `decision.quantile`: indices 25, 500, 974 | `decision.py` | Quantile test | Done |
| C8-neutral and C8-non-neutral strata | Computed on control data, committed before treatment (CQ8-5) | `analyze_e8.py`, `run_e8.py` | Order tests | Q8 |
| §6.3 phase-sensitive stratum, decisive-tick parity, mechanism tables | Reporting | `analyze_e8.py`, `telemetry.py` | Unit tests | I8-5 |
| §6.4 payoff tables; §6.5 telemetry | Reporting | `analyze_e8.py` | Unit tests | I8-5 |
| §6.6 companion: identical code, primary census, reading, expectation, never a verdict | `decision.companion_reading`; the analyzer runs one code path per arm | `decision.py`, `analyze_e8.py` | Companion tests | Done (reading); I8-5 |

### 3.7 Interpretation, kills and disposition (§7, §8)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| §7.1 rows and their totality | `decision.row_for` | `decision.py` | All 18 triples; fail-closed tests | Done |
| R8-NO-CHOICE's H8-TAX qualifier; §7.2 qualifiers | `decision.qualifiers`, `decision.no_choice_qualifier` | `decision.py` | Qualifier tests | Done |
| §7.3 H8-REPEAT readings | `decision.repeat_reading` | `decision.py` | Reading tests | Done |
| §7.3 H8-ADAPT interpretability, the allocation check, S | `decision.adapt_reading`, `decision.allocation_check`, `decision.static_set` | `decision.py` | Every (H8-SUB, H8-REPEAT, check, H8-ADAPT) combination | Done |
| §7.4 core answer | `decision.core_answer` | `decision.py` | All 72 combinations | Done |
| §7.4 the channel difference beside every reading | The results record's template | `run_e8.py` | Record test | T8 |
| §8 KC8-1 to KC8-6 and labels | `decision.kill_criteria`, `kc8_1_label`, `kc8_6_label` | `decision.py` | Exhaustive label tests; impossible records fail closed | Done |
| §8 disposition | `decision.disposition` | `decision.py` | Exhaustive disposition test | Done |

### 3.8 Protocol, traces, rules, stops and containment (§9 to §13)

| PR8 item | Obligation | Where | Verified by | Phase |
|---|---|---|---|---|
| §9 steps 1 to 8 | E6's seed tooling, with E8's names; the runner's unlock chain and order | `seeds.py`, `matrix.py`, `run_e8.py` | E6's seed and order tests, ported | I8-4 to T8 |
| §10 trace fields and roles | §4.3 | `agent_api.py`, `agent_trace.py`, `process_runtime.py` | Engine tests | I8-2 |
| §10 delivery tests | Engine-level, scripted non-family agents, both parents | `engine/tests/test_v6_e8_sensing_semantics.py` | The five registered cases | I8-2 |
| §11 rules 1 to 8 | The analyzer and the runner | `analyze_e8.py`, `run_e8.py` | Unit and order tests | I8-5 |
| §12 hard stops | The unlock chain | `run_e8.py` | Runner tests | I8-5 |
| §13 A1 containment | §4.5 | engine and harness | Containment tests | I8-2 |
| §13 promotion prerequisites | None implemented: research only | — | — | — |
| §14, §15, Appendix A | Records. A.1, A.2 (17 READs, Revision 3) and A.3 are recomputed by the loader. | JSON | Loader | Done |

---

## 4. The Engine Surface (I8-2)

### 4.1 `RulesetPolicy.sensing_mode` (`ruleset_policy.py`)

- A string field, `"passive"` or `"active"`, defaulting to `"passive"`. Any other value is refused when the policy is constructed.
- Under `"active"` the half-width is the Ruleset constant 27 (PR8 §2.1). No other field changes. `detection_radius` keeps its value, and is inert under `"active"`.
- **Byte identity.** Under `"passive"` every existing Ruleset reproduces byte for byte (§2.1). If a policy is ever serialized into an artifact, the field must not change a passive artifact's bytes. The goldens of I8-1 prove it (D8-6).

### 4.2 The sensing action (`agent_api.py`, `process_runtime.py`)

Each row below is PR8 §2.3's, implemented exactly:
- **Form.** `ActionKindV2.SENSE`, wire value `"sense"`, one integer operand, no `value`.
- **Acceptance.** Accepted only when the match's Ruleset has `sensing_mode = "active"`. Under `"passive"` it is an invalid v2 action, which forfeits as every invalid action does. **In the matrix it cannot occur**, because the pre-match gate (§4.5) refuses every pairing in which it could.
- **Normalization and reach.** *t* mod 512. Applied if and only if *d*(*t*, the acting process's anchor) is at most that process's declared reach. Otherwise the status is `REJECTED_OUT_OF_REACH`, with `previous_action_applied` false, as for READ.
- **Result.** At the instant it executes: the ascending tuple of distinct positions *p* of the processes of every other live entrant with *d*(*p*, *t*) ≤ 27. Co-located anchors appear once.
- **Price.** One offer, charged in the quota exactly as a READ.
- **No effect and no exposure.** No memory write, position change, disruption or territory. The sensed entrant's observation is unchanged.
- **Delivery.** At the acting process's next callback, `previous_sense_anchors` holds the tuple, and `previous_read_value` and `previous_read_owner` are `None`. Otherwise `previous_sense_anchors` is `None`.
- **Suppression.** No new rule.

### 4.3 Observation, context and trace fields

All are additive, optional and defaulted. The trace schema version stays 2, whose readers ignore unknown keys (`agent_trace.py`).

| Surface | Field | Default |
|---|---|---|
| `ObservationV2` | `previous_sense_anchors: tuple[int, ...] \| None` | `None` |
| `MatchContextV2` | `sensing_window: int \| None` | `None`; 27 under `"active"` |
| `TraceObservationV2` | `previous_sense_anchors` | `null` |
| `TraceResultV2` | `sensed_anchors` | `null`; the tuple for an applied SENSE; `null` if refused |
| `TraceActionV2` | `kind` = `"sense"` | — |
| `ResetRecord` | `sensing_window` | the match's value, recorded at each entrant's `reset()` |

The worker boundary carries the new action kind by value and the new observation field by name, as it carries READ's and `detection_radius` today.

### 4.4 The two research Rulesets

- T8 and T8L are their parents, C8 and C8L, with `sensing_mode = "active"` and nothing else changed. The provisional identifiers are `bytefray-rules-6-research-sensing-active-w27` and `bytefray-rules-6-research-disruption-slot1-sensing-active-w27`. Whatever identifiers are finally registered are recorded in the family freeze record before any seed exists (PR8 §2.2).
- They are registered wherever E6's research Rulesets were (E6-IP §3.3). C8 and C8L are T-E6's and T-E6L's Rulesets, reused without edit.

### 4.5 A1 containment (PR8 §13; E8-DR §F.3)

- **The version decision, recorded explicitly.** Under A1, `SENSE` is a research-only, Ruleset-gated extension within v2. `AGENT_API_VERSION` stays 2 and `SUPPORTED_AGENT_API_VERSIONS` stays {2}. This rests on E8-DR §F.3's criteria (i) to (v), not on the earlier unbumped context fields as precedent.
- **Only T8 and T8L accept SENSE.** A Ruleset-policy test covers every registered Ruleset (E8-DR S-5).
- **The pre-match gate** in the E8 harness classifies each package statically:
  - a *context-gated SENSE* package passes only on C8, T8, C8L or T8L;
  - an *ungated SENSE* package passes only on T8 or T8L;
  - every other SENSE pairing is refused before execution.
- **Ordinary v2 agents.** The existing Agent API tests are unchanged and must pass.
- **Documentation.** `docs/AGENT_API_V2.md` records SENSE only as a research-only extension, with the criteria. No product Ruleset, starter agent or Designer path offers it.
- **If implementation reveals an actually incompatible contract**, not an additive action, work stops and is reported for an A2 decision (E8-DR K-5).

### 4.6 Engine tests (I8-2)

Every test uses scripted, non-family agents and asserts semantics, never an outcome.
- **One test per §2.3 property**, including windows at distances 27 (inside) and 28 (outside), wraparound across address 0, co-located anchors appearing once, out-of-reach refusal, no state change and no exposure.
- **The delivery tests** (PR8 §10), under both parents:
  1. sense, then the next offer in the same chunk;
  2. sense, then the next tick;
  3. sense, then suppressed for the remainder of the tick, then a later callback, whose record must reflect the authoritative result;
  4. sense as the process's last callback before its entrant is eliminated;
  5. sense as the process's last callback before the match ends at the tick limit.
- **Context and trace fields**, their defaults, and their JSON forms.
- **A1:** SENSE refused under every Ruleset except T8 and T8L; the pre-match gate's three classes; the existing Agent API suite unchanged.
- **The one-field difference** between each treatment and its parent.
- **The parent goldens** unchanged (D8-6).

---

## 5. The Family (I8-3): The Policy Specification

PR8 §3.2 requires this plan to transcribe E6's posture, verification and core-cursor semantics as corrected by E6-A1, and E8's new semantics, **without change**. This section is that transcription. Where it states an implementation detail that the registration leaves open, it cites a plan decision (§9).

### 5.1 Packages

- **Twenty-two packages:** each of the eleven members of PR8 §3.1 as a primary and a twin, with opaque IDs `e8_q01` to `e8_q22` [P8-10]. They are assigned to (member, role) at I8-3 and recorded in the freeze record. At runtime every entrant is its seat label.
- **One policy source.** Every `agent.py` is byte-identical, and a test asserts it.
- **Parameters**, as manifest defaults: `acquire`, `reacquire`, `posture`, `evade`, `processes` and `stress`, with PR8 §3.1's values.
- **Declarations.** Every process declares reach `arena // 2`. SPLIT8 declares `sensor` (share 1/4) and `striker` (share 3/4). Every other member declares one process with share 1.

### 5.2 State

One agent instance serves all of an entrant's processes, so knowledge is entrant-wide (E6-IP §5.2).

- **The known set** (PR8 §3.2), which is family-policy knowledge, not engine visibility:
  - under `"passive"`, the current callback's `visible_enemy_anchor_addresses`;
  - under `"active"`, the remembered results of applied SENSE actions, updated by KU-1 to KU-4 at delivery.
- **The tracked set** (KU-5), under `"passive"` only: the visible set at the entrant's previous callback.
- **Missing addresses** (KU-3, KU-5), serviced in ascending numeric order (KU-6).
- **The last-known anchor**, kept separate from the known set, and set from it in the same circumstances in which E6 set it from visibility: at each callback whose known set is nonempty, it becomes that set's lowest address; it is kept when the set empties; it is cleared when the verification READ window is exhausted without an enemy core cell.
- **E6's state, unchanged:** the confirmed enemy core base; the scan run; the verification window; the addresses this entrant has written as enemy anchors; each process's pending READ; the per-tick written set; the core cursor (E6-A1 C-3), the guard cursor, the paint cursor and side, and the READ-search index.
- **The callback index:** 1-based, entrant-wide, reset when `current_tick` changes.
- **E8's new state:**
  - the discovery index *k* and the direction σ;
  - whether first discovery has happened;
  - for `repeat` and `adaptive`, the re-acquisition search: its missing address *a*, the next window, and τ;
  - for ADAPT8, the count of consecutive confirming verification observations, and whether it has switched to `once`;
  - for EVADE8, `last_callback_tick` and the number of callbacks in the most recent tick in which it received any;
  - for STRESS8, the pending repair cell.

### 5.3 The procedure at each callback

1. **Tick bookkeeping.** If `current_tick` changed: the callback index restarts and the written set clears. Then the callback index advances.
2. **The previous action's result**, for this process:
   - a READ, as E6 (E6-A1 C-2): verification, probe, scan, or STRESS8's check;
   - an applied SENSE: KU-1 to KU-4 over its window, then KU-7's replacements; the search and ADAPT8's count update (§5.4).
3. **Observation.**
   - Under `"passive"`, the known set is the visible set. Tracked addresses absent from it become missing, and are replaced under KU-7 by the nearest visible address, if any. The tracked set for the next callback is this visible set.
   - In both modes, the last-known anchor is updated (§5.2). E6-A1 C-1's unverified adoption is evaluated on the known set.
4. **The action: the first applicable of these.**
   1. **Member-level steps.** EVADE8's evasion on an inferred hit. STRESS8's check READ at callback index 1, then its pending repair.
   2. **A re-acquisition search in progress** (`repeat` and `adaptive` before any switch): its next action, before the posture steps (RP-1, RP-2).
   3. **Verification** (`repeat` and `adaptive` before any switch, under `"active"`): at the first callback of a tick after first discovery, with an address known and no search in progress. A SENSE centered on the lowest known address (KU-8).
   4. **The posture steps** (E6's, with E8's acquisition):
      - **attack:** disrupt a known enemy anchor not yet written this tick, lowest first; write the enemy core at the cyclic cursor; a verification READ; acquisition, if eligible; paint.
      - **guard:** disrupt a known enemy anchor not yet written this tick; acquisition, if eligible; repair its own core with the core beacon at the cyclic guard cursor.
      - **paint:** paint.
      - **SPLIT8:** the sensor takes acquisition if eligible, else disrupts a known anchor, else paints. The striker takes the attack posture with no acquisition.
   - **Acquisition** is eligible when the step is reached, no enemy anchor is known, and the entrant has not confirmed the enemy core (discovery) [Revision 3]. Initial acquisition therefore ends at core confirmation, and loss of passive visibility alone does not restart it. Re-acquisition is the separate state of step 4.2:
     - `spatial-fast`: under `"passive"`, MOVE 64 · σ; under `"active"`, a SENSE at *c_k*. *k* advances with each discovery SENSE and restarts at 0 after seven empty results.
     - `spatial-paced`: the same, but only on odd callback indexes; paint on even ones.
     - `ownership`: E6's READ stride search.
     - `none`: never. The next step applies.

### 5.4 The parameter rows

| Parameter | Procedure |
|---|---|
| `reacquire` = once | No verification and no search. Disrupts known anchors only: under `"passive"` the visible ones; under `"active"` the remembered ones, which it never re-senses. |
| `reacquire` = repeat, `"active"` | Verification as in step 4.3. If the result contains *a*, it is confirmed. If *a* is missing and the result shows another enemy anchor, KU-7 replaces it and no search starts. If the result is empty, a search starts: τ is drawn [P8-2], then SENSE at *a* + τ · 46, then at *a* − τ · 46, each before the posture steps. The first result showing an enemy anchor replaces *a* and ends the search. If the third is empty, *a* is unknown, and the member continues with its no-anchor behavior. |
| `reacquire` = repeat, `"passive"` | When a tracked address becomes missing and the visible set gives no replacement, a search starts. τ is drawn [P8-2], then the member MOVEs toward *a*, *a* + τ · 46 and *a* − τ · 46, in order, at most 64 per MOVE [P8-3], before the posture steps. Each callback's visible set is a result. The first showing an enemy anchor replaces *a* under KU-7. The search is exhausted when the visible set on reaching the last center shows none. |
| `reacquire` = adaptive | As `repeat` until two consecutive verification observations confirm *a* with no observed relocation; then as `once` for the rest of the match. An observed relocation, *a* found missing at a verification or at any other callback, sets the count to 0. A tick with no applicable verification callback leaves it unchanged. Under `"active"` the observation is the verification SENSE's result. Under `"passive"` it is the visible set at the first callback of a tick, which confirms the lowest tracked address if it contains it. A first callback during a search, or with nothing known, is not applicable. |
| `evade` = on-hit | At its first callback of a tick, it infers a hit if (i) `current_tick` > `last_callback_tick` + 1, or (ii) it received fewer than 8 callbacks in the most recent tick in which it received any [P8-5]. On an inferred hit, that callback is a MOVE of σ_e · *m*, with σ_e and *m* on [8, 64] drawn fresh [P8-2]. It repeats on every inferred hit. |
| `stress` | At callback index 1, before anything else, it READs own-core cell (*t* − 1) mod 8. If the result shows an owner other than itself, its next action repairs that cell with the core beacon, exactly as the guard posture's repair write [P8-6]. Otherwise it follows the guard posture. |
| No `sensing_window` | Never SENSE: every SENSE path is guarded by `sensing_window is not None` (D8-9). |

### 5.5 Consequences of the registered text

These follow from PR8 as written. **None is a choice made here.** Each is listed for the research lead in §10.

- **K-1, SPLIT8's sensor under C8 and C8L: corrected by Revision 3.** Under revision 2, the sensor resumed sweeping whenever the entrant's visible set was empty, even after the entrant knew the enemy core. E6's SPLIT did not. Revision 3 ends initial acquisition at core confirmation. SPLIT8's `reacquire` is `once`, so after confirmation its sensor never moves again.
  - **What remains, as registered.** Before confirmation, initial acquisition has not ended, so the sensor still sweeps whenever the visible set is empty (PR8 §3.2). E6's sensor also paused while an anchor was remembered, that is, between first sighting and confirmation (E6-IP §5.2). The two differ only in that window.
  - Attack-posture members are unaffected. In their order, acquisition is reached only when the core is unknown and no verification READ is due. Guard-posture members confirm no enemy core, so K-4 stands.
  - The engine's visible set is entrant-wide: the union over the entrant's unsuppressed processes, in ascending order.
- **K-2, passive replacement.** Under `"passive"`, a tracked anchor that disappears while any enemy anchor is visible is replaced by the nearest visible one (KU-7), so no search starts. REACQ8 and ADAPT8 search under C8 only when nothing is visible.
- **K-3, unverified adoption.** E6-A1 C-1's rule, evaluated on the known set, never fires under `"active"`: no SENSE result has been delivered at a first callback. Every T8 attacker confirms the core by READ.
- **K-4, the registered channel difference**, restated: under `"passive"`, GUARD8 and EVADE8 resume sweeping when they lose sight of the opponent.

### 5.6 Behavior tests (I8-3)

These are engine-level tests against scripted, non-family opponents, asserting actions and never an outcome:
- **E6 parity:** E6's family behavior tests (E6-A1 §2), ported, for the posture, verification, core-cursor and adoption semantics under `"passive"`.
- **Discovery:** the centers *c_k* for both σ, the stop, the restart after seven empty results, and PACED8's odd-index pacing.
- **Knowledge:** one test per rule, KU-1 to KU-9, with scripted anchors inside and outside windows.
- **Initial acquisition** (Revision 3), under `"passive"`:
  - SPLIT8's sensor sweeps while the enemy core is unconfirmed and nothing is visible;
  - it never moves again once its entrant confirms the core, including after the visible set empties;
  - its striker never moves;
  - GUARD8 and EVADE8 still resume sweeping when they lose sight (K-4);
  - attack-posture actions are unchanged.
- **Precedence:** RP-1 to RP-7. That covers:
  - verification, then the second and third windows, before any posture step;
  - continuation across a suppressed tick (RP-2);
  - termination by replacement and by exhaustion;
  - the passive MOVE search.
- **ADAPT8's freeze tests** (PR8 §3.2), in every registered case:
  - Seat A and Seat B;
  - a scripted static opponent and a scripted responsive evader;
  - both parents;
  - hits at every chunk position of both seat orders;
  - ticks in which ADAPT8 receives no callback.

  They assert the count, that an unobserved tick neither advances nor resets it, the reset on relocation, and the switch at the second consecutive confirmation.
- **EVADE8 and STRESS8:** hit inference (i) and (ii); fresh draws per evasion; repetition on every hit; the check READ and the beacon repair.
- **The context guard:** no SENSE when `sensing_window` is `None`.
- **Registered identities:**
  - RUSH8 and REACQ8 identical until the first trigger, and GUARD8 and EVADE8 until the first inferred hit, under both controls (CQ8-2);
  - LURK8 and GREED8 records identical under T8 and T8L (D8-3).

### 5.7 The static discipline gate (D8-9)

This is E6's gate: allowed imports only, no read of `context.seed`, no package-ID literal, and no call to `open`, `exec`, `eval`, `compile` or `__import__`. It adds one check: **every path that returns SENSE is guarded by `sensing_window is not None`.** Negative controls for each rule must fail.

### 5.8 The family freeze (I8-4)

- **Fingerprints** of every package.
- **The census:** `decision.census` applied to the frozen manifests' parameters. Its output is the frozen census, whatever it is. If it is empty, the pre-seed halt applies (PR8 §12).
- **The seat strata inputs.**
- **The final Ruleset identifiers.**
- **The structural matrix identity** `v6-e8-matrix-v1-<12 hex>`, with no seed value (PR8 §9, step 1).

---

## 6. The Runner, Traces and the Analysis Instrument (I8-5)

**Modules** (`tools/research/v6/e8/`), following E6's layout:

| Module | Role | Registered items |
|---|---|---|
| `matrix.py` | Conditions, fields, pairings; structural and execution identities | §2.2, §3.4, §9 |
| `seeds.py` | E6's seed tooling, with E8's names | §9 steps 2 to 5, D8-10 |
| `run_e8.py` | The unlock chain, execution, the pre-match gate, the order of §9 step 7 | §9, §12, §13 |
| `traces.py` | Per-cell schema-2 traces, binding checks, indexing | §10, D8-12 |
| `rederive.py` | D8-1's independent re-derivation of every applied SENSE's tuple, from tick-0 anchors, normalized MOVE results and disruption hits under the condition's λ | D8-1, D8-15 |
| `gates.py` | D8-2 to D8-15 and CQ8-1 to CQ8-5 | §5.1, §5.2 |
| `telemetry.py` | O-ACQ, O-REACQ, O-VERIF; mechanism tables | §4, §6.3, §6.5 |
| `payoff.py` | O-VALUE, O-PAYOFF, BR_ε, BR^A_ε, universality, Δ, Δ^R, U | §4, §5.3 |
| `analyze_e8.py` | Every registered quantity, per arm, with identical code | §5 to §6 |
| `decision.py` (I8-0) | Every registered status, reading and outcome | §5 to §8 |
| `analysis_freeze.py` | `v6-e8-analysis-v1-<12 hex>`, which carries the pre-registration freeze identity and the structural matrix identity | §11 rule 7 |

- **Reuse.** E3's `outcome_class`, E4's `pairing_seat_metrics`, `mirror_seat_metrics` and relabel gate, and E6's analyzers where PR8 reuses PR6. Each is pinned, and checked on every load, as E6's analysis freeze pinned E2 to E5 (E6 `analysis_freeze.py`).
- **The analyzer calls the I8-0 decision logic.** It never restates a threshold, set, row, text or order.
- **Traces.** D8-12 requires a schema-2 trace for every one of the 16,896 cells. The storage form is a decision for I8-5, made with a measured size estimate and before any seed exists [P8-11]. That decision can never drop a cell's trace.
- **Seed blindness.** Every printed or saved output before the reveal passes the value-based seed filter (PR8 §9, step 6; E6-R §I.1).

---

## 7. Seeds, Qualification and Execution (separately authorized)

- **I8-6, seeds.** 32 unique integers from `secrets.randbelow(2**53)`, exactly once. They are encoded canonically and committed by SHA-256. The execution identity is `v6-e8-exec-v1-<12 hex>`. **Only the commitment and the identity are committed before the first cell.**
- **Q8, the controls.** C8 and C8L. Then CQ8-1 to CQ8-5, with the seat strata committed before any treatment cell. Any failure halts before the treatment.
- **T8, the treatment.** T8 and T8L. Then the treatment gates, the frozen analysis, the reveal and D8-10, E8-D's final status, the interpretation and disposition, and the results record, in that order. The results record states the registered channel difference beside every reading (PR8 §7.4).

---

## 8. The Unlock Chain (run_e8.py)

Each step refuses to run unless the previous one is recorded:
1. The pre-registration freeze loads (I8-0).
2. The family freeze, the census and the structural identity (I8-4).
3. The analysis freeze (I8-5).
4. The seed commitment and the execution identity (I8-6).
5. Control execution, then CQ8, then the stratum commitment (Q8).
6. Treatment execution, then the treatment gates, the frozen analysis, the reveal and D8-10, and the interpretation (T8).

Every hard stop of PR8 §12 is a refusal in this chain. A clean tree and an unchanged source manifest are checked before each execution step.

---

## 9. Plan Decisions, for Review

These are implementation details that PR8 leaves open. **None changes a registered item.** Each is fixed before any E8 data exists.

| # | Decision | Proposed | Why |
|---|---|---|---|
| **P8-1** | Draws at reset | Every package draws, in this fixed order: σ, then the paint side. Nothing else is drawn at reset. | One fixed order for every package keeps D8-3's and CQ8-2's identities true by construction (PR6 §3.2). |
| **P8-2** | Draws during play | τ, once, **when a re-acquisition search starts**. σ_e, then *m*, at each evading callback. | PR8 says τ is drawn "per traversal", and σ_e and *m* "fresh for each evasion". A search that ends at its first window never needs τ. Drawing at the search's start fixes one draw per search in both modes. |
| **P8-3** | A passive MOVE "toward" a center | The shortest signed circular displacement, clamped to ±64. A center is reached when the anchor equals it. | PR8 says "at most 64 per MOVE". The distance-256 tie is unreachable: the member saw *a* within 32 cells, so the next center is never more than 92 cells from its anchor during a search. |
| **P8-4** | SENSE operands | The registered center, mod 512 | The engine normalizes anyway. This keeps the trace's operand equal to the registered center. |
| **P8-5** | EVADE8's first callback of the match | No inferred hit | No earlier tick exists for (i) or (ii) to compare with. |
| **P8-6** | STRESS8's repair obligation | Carried to its next callback. If that is a new tick's callback index 1, the check READ comes first and the stale obligation is dropped. | That case is unreachable. With chunk 2 and one process, callbacks 1 and 2 of a tick share a chunk, so no opponent action can fall between them. A test pins the chunk premise. |
| **P8-7** | Order of named members in labels | The registered member order (PR8 §3.1) | It is deterministic, and independent of input order (tested). |
| **P8-8** | The form of a named label | Structured: the label and the member tuple | No sentence is invented. The record prints both. |
| **P8-9** | Substituting {𝒞} in a reading | The census members, in registered order, inside braces | The registered text writes {𝒞}. |
| **P8-10** | Package IDs | `e8_q01` to `e8_q22`, assigned at I8-3 | E6's convention |
| **P8-11** | Trace storage | Decided at I8-5, from a measured size estimate, before any seed | D8-12 fixes that every cell has a trace. Only the storage form is open. |

---

## 10. Items for the Research Lead

**Resolved by Revision 3** (the research lead, 2026-09-30):
- **TN-1.** DR is now defined in PR8's governing records as [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md).
- **TN-2.** Appendix A.2 now says 17 READs under E6's verification order. The loader recomputes the 17 and its worst-case displacements, 58 to 64 cells.
- **K-1.** Initial acquisition ends once the enemy core is confirmed (§5.5).

**Left as registered** (the research lead, 2026-09-30). Each follows from PR8 as written, and the plan implements it as written:
- **K-2:** under `"passive"`, a vanished anchor is replaced by any visible one, so REACQ8 and ADAPT8 search only when nothing is visible.
- **K-3:** unverified adoption never fires under `"active"`.
- **K-4:** the registered channel difference: GUARD8 and EVADE8 resume sweeping under the controls.

**One point to note, not a new question.** In the window between first sighting and core confirmation, SPLIT8's sensor still resumes sweeping when the visible set empties. E6's did not (K-1). Revision 3's rule sets that behavior, and the plan implements it as written.
