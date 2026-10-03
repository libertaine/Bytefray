# Bytefray V6 E8 — Active Spatial Sensing: Family Freeze (I8-4)

**Status: FROZEN, awaiting the research lead's review of I8-4.** Phase I8-4 of the [implementation plan](V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md) turned the implemented E8 family into an immutable experimental input. It froze:
- the structural matrix identity, with the census and the seat strata inputs inside its digest (PR8 §9, step 1);
- the family freeze record, which pins the packages, parameters, sets, census, compatibility classification, final Ruleset identifiers, RNG and behavior invariants and qualification evidence.

- **What does not exist:** no seed, no seed commitment, no execution identity, no matrix cell, no analysis instrument, and no match in which one family member played another. Every family match so far was a behavior test against a scripted, non-family opponent.
- **What remains:** I8-5 (the runner, traces, gates and the analysis freeze), then I8-6 (seeds), Q8 and T8. Each needs separate authorization.

**Branch:** `v6-research`
**Date:** 2026-10-01
**Governing records:**
- [pre-registration](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) (**PR8**), revision 5, frozen as `v6-e8-prereg-v4-0166cdc0b37a`;
- [implementation plan](V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md) (**plan**), pinned by that freeze and not edited;
- [design review](V6_E8_ACTIVE_SPATIAL_SENSING_DESIGN_REVIEW.md) (**E8-DR**).

---

## 1. Identities

| Identity | Value | Phase |
|---|---|---|
| Pre-registration freeze | `v6-e8-prereg-v4-0166cdc0b37a` (unchanged) | I8-0 |
| **Structural matrix** | **`v6-e8-matrix-v1-e0d322b597da`**. Structural digest `e0d322b597da298686c7a392a7ae495a96ea6a5428b5fb47f15138fa3af26fc7`. No seed value. | I8-4 |
| **Family freeze** | **`v6-e8-family-v1-981fc8b12beb`**, record `tools/research/v6/e8/family_freeze.json`, digest `981fc8b12beb399e139289b5b56b29c0b75fba967fe2267c19f7d654c95ac841`, tooling commit `2ba2487` | I8-4 |
| Analysis freeze | `v6-e8-analysis-v1-<12 hex>`: **does not exist** | I8-5 |
| Seed commitment, execution identity | `v6-e8-exec-v1-<12 hex>`: **do not exist** | I8-6 |

The plan names the family freeze (§5.8, §8 step 2) but not an identity for it. I8-4 gives the record one, `v6-e8-family-v1-<first 12 hex of its body digest>`, in the pre-registration freeze's form, so that the I8-5 analysis freeze can carry it.

## 2. Phases and Commits

| Phase | Commits | Content |
|---|---|---|
| I8-0 | `664c332`, `83ae0c6` and earlier | The transcription, the decision logic, the plan, the pre-registration freeze v4 |
| I8-1 | `3f3f709`, `2cfd4e8` | The C8 and C8L parent byte-identity goldens (D8-6), before any engine change |
| I8-2 | `e170895`, `230fe71` | The engine surface: `sensing_mode`, SENSE, the E8 fields, T8 and T8L, A1 containment |
| I8-3 | `4b58d27`, `621c95d` | The family: one policy source, 22 packages, D8-9, the compatibility gate, 755 behavior tests |
| I8-4 | `2ba2487`, `ac14855`, this commit | The structural matrix, the family freeze, three pin tests; this record |

## 3. What the Freeze Pins

### 3.1 The packages

Twenty-two packages, `e8_q01` to `e8_q22`, a primary and a twin for each member, assigned by the documented shuffle `random.Random("v6-e8-package-ids")` (P8-10). Every `agent.py` is byte-identical: SHA-256 `369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc`. A package is nothing but its manifest's parameter defaults.

| Member | Primary | Twin | `acquire` | `reacquire` | `posture` | `evade` | `processes` | `stress` |
|---|---|---|---|---|---|---|---|---|
| RUSH8 | `e8_q21` | `e8_q10` | spatial-fast | once | attack | off | 1 | false |
| REACQ8 | `e8_q19` | `e8_q03` | spatial-fast | repeat | attack | off | 1 | false |
| PACED8 | `e8_q09` | `e8_q05` | spatial-paced | once | attack | off | 1 | false |
| STEALTH8 | `e8_q04` | `e8_q20` | ownership | once | attack | off | 1 | false |
| LURK8 | `e8_q08` | `e8_q11` | none | none | attack | off | 1 | false |
| SPLIT8 | `e8_q07` | `e8_q17` | spatial-fast | once | attack | off | 2 | false |
| GUARD8 | `e8_q13` | `e8_q18` | spatial-fast | once | guard | off | 1 | false |
| EVADE8 | `e8_q15` | `e8_q02` | spatial-fast | once | guard | on-hit | 1 | false |
| GREED8 | `e8_q01` | `e8_q06` | none | none | paint | off | 1 | false |
| ADAPT8 | `e8_q16` | `e8_q14` | spatial-fast | adaptive | attack | off | 1 | false |
| STRESS8 | `e8_q22` | `e8_q12` | none | none | guard | off | 1 | true |

- **The registered encoding.** A registered `reacquire` of "—" is the manifest choice `none`, and a member the table gives no `stress` has `stress: false`.
- **The parameters are read from disk.** The record holds each package's parameters as a match resolves them from its manifest, and each member's primary and twin agree.
- **Declarations.** At arena 512 every process declares reach 256. SPLIT8 declares `sensor` (share 1/4) and `striker` (share 3/4); every other member one process, share 1.
- **Fingerprints.** Every `agent.py` and `agent.yaml` digest, equal to `family_fingerprints.json` and to the files at the tooling commit.

### 3.2 Sets, census and compatibility

- **Π** is all eleven members, **Π_F** all but ADAPT8, and the phase-sensitive members are PACED8, EVADE8, ADAPT8 and STRESS8.
- **A8, H8-CHANNEL's frozen candidate set**, is {RUSH8, REACQ8, PACED8, STEALTH8, LURK8}. It is frozen with the family and never changes after outcomes exist (PR8 §3.1).
- **The census** is `decision.census` applied to the parameters the manifests on disk declare, re-derived for the primary and the twin packages separately. Both give **{EVADE8}**, which equals the prediction (PR8 §3.5). It is not empty, so §12's pre-seed halt does not apply. CQ8-3 is satisfied: the census is committed before any seed exists.
- **Compatibility.** All 22 packages are statically **context-gated**, and D8-9 finds no violation. A context-gated package passes the pre-match gate on C8, T8, C8L and T8L only; an ungated SENSE package would pass on T8 and T8L only.
- **The final Ruleset identifiers** are the provisional ones of PR8 §2.2, unchanged:

| Condition | Ruleset | Registered as |
|---|---|---|
| C8 | `bytefray-rules-6-research-sensing-r32` | T-E6's Ruleset, unchanged |
| T8 | `bytefray-rules-6-research-sensing-active-w27` | provisional, now final |
| C8L | `bytefray-rules-6-research-disruption-slot1-sensing-r32` | T-E6L's Ruleset, unchanged |
| T8L | `bytefray-rules-6-research-disruption-slot1-sensing-active-w27` | provisional, now final |

Each treatment differs from its parent in `sensing_mode` alone, and the four share arena 512, 1,000 ticks, Q = 8, chunk 2, rotation, K = 1, seeded placement, `core_base` spawn and the forward pass order.

### 3.3 The structural matrix

`matrix.py` is the matrix definition, with no seed value:
- **F1:** the 55 unordered pairs of primary packages, in both orientations (110 ordered pairs), × 32 seed positions = 3,520 cells per condition.
- **F2:** the 11 twin mirrors, in both orientations, × 32 = 704.
- **Per condition** 4,224, and **16,896** over the four conditions, as registered.
- **The parent freeze** (D8-6): the I8-1 commits, the 72 golden cases and the golden record's digest.
- **The census** above.
- **The seat strata inputs** (PR8 §6.2, §6.3):
  - the 66 units, which are the 55 F1 pairings and the 11 F2 mirrors;
  - their partition by the phase-sensitive members, **38** units containing one and **28** not;
  - O-NEUTRAL (SDom < 9/10 and |GSB| ≤ 1/10).
  The C8-neutral and C8-non-neutral strata need control data. They are computed at the C8 point estimate and committed before any treatment cell (CQ8-5), at Q8.

`verify_frozen_matrix` fails closed if the digest drifts, if the count is not 16,896, if the census is empty or differs by role, or if a condition's Ruleset no longer resolves as registered. The seed protocol is recorded as registered (§9, steps 2 to 4). The seed tooling and the execution identity belong to I8-5 and I8-6.

### 3.4 RNG and behavior invariants

Each invariant names the tests that pin it, and the loader fails if any of those tests is missing from its pinned file. There are 27 invariants with 131 pins.

| ID | Invariant | Pinned in |
|---|---|---|
| RNG-1 | At reset every package draws exactly two values from context.rng, in this order: sigma = (-1, 1)[rng.randrange(2)], then the paint side = rng.randrange(2). Nothing else. | `test_v6_e8_family.py` (1) |
| RNG-2 | During play, tau = (-1, 1)[rng.randrange(2)] is drawn once, when a re-acquisition search starts, in both modes. | `test_v6_e8_family_policy.py` (2) |
| RNG-3 | At each evasion, sigma_e = (-1, 1)[rng.randrange(2)], then m = rng.randint(8, 64), drawn fresh for every evasion. | `test_v6_e8_family_policy.py` (1); `test_v6_e8_family_engine.py` (1) |
| RNG-4 | One policy source and one fixed draw order: a member's primary and twin packages consume the stream identically and act identically, and no draw is made outside RNG-1 to RNG-3. | `test_v6_e8_family.py` (1); `test_v6_e8_family_engine.py` (1) |
| RNG-5 | No package reads context.seed: randomness reaches the policy only through context.rng. | `test_v6_e8_family.py` (2) |
| BEH-1 | Every process declares reach arena // 2. SPLIT8 declares a sensor (share 1/4) and a striker (share 3/4); every other member one process, share 1. | `test_v6_e8_family.py` (2) |
| BEH-2 | No member returns SENSE when sensing_window is None. | `test_v6_e8_family.py` (2) |
| BEH-3 | Under active, only an inferred hit moves an anchor: EVADE8's evasion is the family's only MOVE. | `test_v6_e8_family.py` (1) |
| BEH-4 | Discovery senses c_k = own_core_base + sigma(91 + 55k), k = 0..6, stops at the first result with an enemy anchor, and restarts at c_0 after seven empty results. Each later return to nothing known is a new episode that restarts at c_0. PACED8 acquires on odd callback indexes only. Under passive, acquisition is E6's MOVE 64 * sigma sweep. | `test_v6_e8_family_policy.py` (6); `test_v6_e8_family_engine.py` (2) |
| BEH-5 | First discovery happens on the callback that delivers the SENSE result, never on the one that issued it. If that is the entrant's first callback of a tick, repeat and adaptive members verify there (under active, a SENSE centered on the lowest known address); otherwise verification waits for the next tick's first callback. once members never verify. | `test_v6_e8_family_fixed_details.py` (6) |
| BEH-6 | Knowledge: under passive the known set is the current visible set; under active, remembered SENSE results updated only inside the sensed window; missing addresses are serviced in ascending order and replaced by the nearest returned address, the lower on a tie; a refused SENSE changes nothing. | `test_v6_e8_family_policy.py` (11) |
| BEH-7 | Initial acquisition ends once the entrant confirms the enemy core; SPLIT8's sensor never moves again after confirmation, and its striker never moves. | `test_v6_e8_family_policy.py` (5); `test_v6_e8_family_engine.py` (1) |
| BEH-8 | Under passive, GUARD8 and EVADE8 resume sweeping when they lose sight; under active, a remembered anchor is never re-sensed by a once member. | `test_v6_e8_family_policy.py` (3); `test_v6_e8_family_engine.py` (1) |
| BEH-9 | A re-acquisition search in progress takes precedence over the posture steps until replacement or exhaustion, continues on a later tick's first offer, and never overrides a member-level step. Under active its windows are a, a + 46 tau, a - 46 tau; under passive it MOVEs toward them, at most 64 per MOVE. | `test_v6_e8_family_policy.py` (8); `test_v6_e8_family_engine.py` (3) |
| BEH-10 | ADAPT8 switches to once at the second consecutive verification observation confirming its selected address a, the lowest known (active) or tracked (passive) address. An unobserved tick neither advances nor resets the count; a found missing at any callback resets it; another known address found missing does not, unless it is a. | `test_v6_e8_family_policy.py` (8); `test_v6_e8_adapt8_freeze.py` (2); `test_v6_e8_family_fixed_details.py` (5) |
| BEH-11 | EVADE8 infers a hit at its first callback of a tick if a whole tick passed without a callback or it received fewer than 8 callbacks in its most recent tick with any; never at its first callback of the match. It evades on every inferred hit. | `test_v6_e8_family_policy.py` (4); `test_v6_e8_family_engine.py` (1) |
| BEH-12 | STRESS8 READs own-core cell (t - 1) mod 8 at callback index 1 of each tick and repairs a damaged cell with the core beacon at its next action, without moving the guard cursor; the check's result reaches the same tick's second callback under both parents. | `test_v6_e8_family_policy.py` (5); `test_v6_e8_family_engine.py` (2) |
| BEH-13 | Under the controls RUSH8 and REACQ8 act identically until REACQ8's first re-acquisition trigger, and GUARD8 and EVADE8 until EVADE8's first inferred hit. | `test_v6_e8_family_policy.py` (2); `test_v6_e8_family_engine.py` (2) |
| BEH-14 | Without information LURK8 and GREED8 act identically, and members without acquisition never move or sense. | `test_v6_e8_family_policy.py` (2); `test_v6_e8_family_engine.py` (1) |
| BEH-15 | E6's posture, verification-READ, core-cursor and adoption semantics, as corrected by E6-A1, are carried over unchanged; under C8 and C8L, RUSH8, PACED8, STEALTH8, LURK8 and GREED8 reproduce E6's members decision for decision. | `test_v6_e8_family_policy.py` (8); `test_v6_e8_family_engine.py` (1) |
| BEH-16 | A package given no parameters, which only a validation dry run produces, behaves as GREED8. | `test_v6_e8_family_fixed_details.py` (1) |
| BEH-17 | Every member plays legally under all four conditions; a context-gated package is refused before the match off C8, T8, C8L and T8L; an ungated SENSE package plays only under T8 and T8L. | `test_v6_e8_family_engine.py` (3); `test_v6_e8_family.py` (3) |
| BEH-18 | Seat A moves first on tick 1 under every E8 condition. | `test_v6_e8_family_engine.py` (1) |
| ENG-1 | SENSE's window is inclusive at 27 and covers 55 cells across the wrap; its result is the ascending, distinct tuple of other live entrants' anchors; it costs one offer and changes nothing in the match. | `test_v6_e8_sensing_semantics.py` (9) |
| ENG-2 | A SENSE result is delivered at the acting process's next callback, after suppression included; with no later callback, the authoritative record stands. | `test_v6_e8_sensing_semantics.py` (6) |
| ENG-3 | The E8 trace fields are present exactly where registered, absent and null are distinct, and a non-SENSE or control record's bytes are unchanged. | `test_v6_e8_sensing_semantics.py` (3); `test_v6_e8_sensing_context.py` (1) |
| ENG-4 | C8 and C8L reproduce their pre-E8 parent goldens byte for byte. | `test_v6_e8_parent_byte_identity.py` (1) |

### 3.5 Engine source

The record holds a manifest digest of the 116 tracked files under `engine/src` the family was qualified against: `9323307c4131105a30c94cad16845468937571657b6d354827a26cfbfcff2676`. As in E6's analysis freeze, it is a recorded fact, not checked on every load, because later experiments share the engine. The E8 runner must call `family_freeze.verify_engine_source` before execution (I8-5).

## 4. Qualification Evidence

### 4.1 The pinned test files

| Phase | File | Tests |
|---|---|---|
| I8-1 | `test_v6_e8_parent_byte_identity.py` | 99 |
| I8-2 | `_e8_sensing_harness.py` | harness |
| I8-2 | `test_v6_e8_sensing_semantics.py` | 58 |
| I8-2 | `test_ruleset_v6_research_sensing_active.py` | 68 |
| I8-2 | `test_v6_e8_sensing_context.py` | 42 |
| I8-3 | `_e8_family_harness.py` | harness |
| I8-3 | `_e8_family_engine_harness.py` | harness |
| I8-3 | `test_v6_e8_family.py` | 174 |
| I8-3 | `test_v6_e8_family_policy.py` | 106 |
| I8-3 | `test_v6_e8_family_engine.py` | 330 |
| I8-3 | `test_v6_e8_adapt8_freeze.py` | 145 |
| I8-4 | `test_v6_e8_family_fixed_details.py` | 27 |
| I8-4 | `test_v6_e8_matrix.py` | 14 |
| | **Total** | **1,063** |

The transcription, decision-logic and pre-registration-freeze tests of I8-0 are pinned by the pre-registration freeze.

### 4.2 The I8-4 run

At commit `ac14855` (the record commit, which contains the tooling commit `2ba2487`), under the qualification integrity protocol:
- **The full repository suite** (`python -m pytest`, all three `testpaths`): **6,699 passed, 18 skipped, 3 deselected**, in 15 min 17 s.
  - I8-2's full suite gave 5,885 passed. I8-3 added 755, giving 6,640, and I8-4 adds 59: 27 pin tests, 14 matrix tests and 18 freeze-record tests.
- **The focused E8 set** at `2ba2487` gave 1,236 passed:
  - I8-0: 173;
  - I8-1: 99;
  - I8-2: 168;
  - I8-3: 755;
  - I8-4's 27 pin and 14 matrix tests: 41.

  The 18 freeze-record tests and the 14 matrix tests then gave 32 passed at `ac14855`.
- **`mypy`** is clean on `engine/src/battle_engine` (97 files) and `client/src/battle_client` (16 files). **`ruff check .`** passes.
- **Integrity.** Before the suite I recorded HEAD, an empty `git status --short`, and the SHA-256 of 196 phase-critical files: every E8 tooling, fixture and test file, and the tracked `engine/src`. After the suite, HEAD was unchanged, the tree was clean, and all 196 digests were identical.
- **No outcome was recorded.** No test in this run plays one family member against another, and none asserts an outcome.

## 5. Implementation Record Notes

N8-1 to N8-13 record what the research lead approved, or asked to have recorded, at the I8-2 and I8-3 closes (2026-09-30). N8-8 is the research lead's wording, verbatim. N8-14 is I8-4's own. The machine record (`implementation_notes`) carries each note's text exactly as below, inside its digest.

- **N8-1** (I8-2, 2026-09-30). The arena check ProcessMatchController._sensing_window_problem (2 x 27 < arena_size) is defensive validation introduced by I8-2. It is not a registered mechanic and not an E8 finding, and it applies only under sensing_mode = "active". E8 runs at arena 512, so no registered cell is affected. The pre-registration is not reopened for it.
- **N8-2** (I8-2, 2026-09-30). A forfeit record keeps previous_sense_anchors: the reflection was delivered before the action failed.
- **N8-3** (I8-2, 2026-09-30). Under T8 and T8L, detection_radius = 32 is still delivered but is inert. sensing_window is the authoritative indicator of active sensing.
- **N8-4** (I8-2, 2026-09-30). Hand-built test entrants get a separate controller rejection of an unavailable SENSE.
- **N8-5** (I8-3, judgment call 1, 2026-09-30). Each return to nothing known, with discovery required, is a new discovery episode: its traversal restarts at c_0, and no cursor is carried over from an earlier, exhausted episode.
- **N8-6** (I8-3, judgment call 2, 2026-09-30). "After first discovery" includes the discovering callback, which is the callback on which the prior SENSE result is delivered to the agent through previous_sense_anchors, not the callback that issued the SENSE. When that delivery callback is the entrant's first callback of a tick, a repeat or adaptive member verifies there; under active, the verification is a SENSE centered on the lowest known address (PR8 Sec 3.2, KU-8). At any other delivery callback the posture steps apply.
- **N8-7** (I8-3, judgment call 3, 2026-09-30). ADAPT8 tracks the lowest selected address a. Its quiet count is about the persistence of that selected anchor: another SPLIT8 anchor moving does not reset it unless it becomes the selected a. This scope is to be stated when ADAPT8 is interpreted against SPLIT8. The family is not changed.
- **N8-8** (I8-3, P8-6 finding, 2026-09-30). P8-6's same-chunk rationale applies to whole-tick disruption but not universally to λ=1. Qualification establishes the intended same-tick result-delivery behavior under both parents, so no registered family behavior changes.
- **N8-9** (I8-3, 2026-09-30). tools/research/v6/e8/__init__.py still describes the package as it stood at I8-0. The pre-registration freeze pins it, so it is left untouched. Its wording is stale descriptive text, not family semantics.
- **N8-10** (I8-3, accepted without action, 2026-09-30). A possible EVADE8 start-up effect (a scripted evader whose first evasion came after ADAPT8's second verification let ADAPT8 switch at tick 3) remains unprobed against EVADE8. The frozen experiment may discover it. Neither EVADE8 nor ADAPT8 is tuned around it.
- **N8-11** (I8-3, accepted without action, 2026-09-30). A passive searcher whose first center is an anchor's last address can park on the opponent's core cell 0. That is a consequence of the registered chase geometry, not something to repair.
- **N8-12** (I8-3, accepted without action, 2026-09-30). A disruption after the victim's last offer of a tick costs nothing, and under T8L a search started by a verification does not carry into another tick. Both follow from the parent scheduler and disruption semantics.
- **N8-13** (I8-3, 2026-09-30). The pre-match compatibility gate is compatibility.require_compatible. Calling it before every matrix match is owed by the I8-5 runner (run_e8.py).
- **N8-14** (I8-4, 2026-10-01). The fixtures README says each fixed detail is pinned by a test. At the family freeze, judgment call 2's first-of-tick delivery case, judgment call 3's two-anchor case and fixed detail 14 had no test of their own. test_v6_e8_family_fixed_details.py pins them. The policy source is unchanged.

**On judgment call 2's wording.** The approval said that on the delivery callback "immediately choosing the verification READ is correct". Under active, the registered verification of a `repeat` or `adaptive` member is a **SENSE centered on the lowest known address** (PR8 §3.2), and that is what the policy chooses on a first-of-tick delivery callback. E6's core-verification READ is a later attack-posture step, reached only once the known anchor has been disrupted this tick. N8-6 records the SENSE. This is a wording point for the research lead, and no behavior was changed.

## 6. Settled at I8-4, for Review

1. **The census and the seat strata inputs are inside the structural digest**, not only committed beside it. PR8 §9, step 1 asks for them to be "committed with" the structural identity. Putting them inside binds them to the later execution identity as well, so a census changed after the seeds would change that identity.
2. **The family freeze has its own identity**, `v6-e8-family-v1-*` (§1).
3. **The engine source is recorded, not checked on load** (§3.5).
4. **Three pin tests were added** (N8-14), in a new file. The I8-3 test files and the policy source are unchanged. The fixtures README said every fixed detail was pinned by a test. That was true only in part for judgment calls 2 and 3, and not at all for fixed detail 14:
   - **Judgment call 2:** a first discovery delivered on an entrant's first callback of a tick had no test. Five synthetic tests now pin it, and so does an engine-level test under T8 and T8L, in both seats, for REACQ8, ADAPT8 and RUSH8 against a scripted opponent. The engine test first asserts that the trace contains the case: the discovering SENSE is the entrant's last callback of tick 1, and its result is delivered at callback index 1 of tick 2.
   - **Judgment call 3:** the case of two known anchors had no test.
   - **Fixed detail 14:** a package given no parameters had no test.
5. **No seed tooling.** `seeds.py` and the execution-identity function are left to I8-5 and I8-6, where the plan's module table places them.

## 7. What Does Not Exist, and What Comes Next

No seed, seed list, commitment or execution identity. No matrix cell, no analysis instrument, no runner, and no match of one family member against another. No outcome of any kind was recorded or read.

**Next is the research lead's review of I8-4.** I8-5 (the runner, traces, the D8 gates, re-derivation, telemetry, the analyzer and the analysis freeze) needs separate authorization. It must:
- call `compatibility.require_compatible` before every match (N8-13);
- call `family_freeze.verify_engine_source` and `family_freeze.load_freeze` before execution;
- decide the trace storage and line endings (P8-11, P8-13).
