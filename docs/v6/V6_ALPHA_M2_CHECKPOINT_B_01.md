# Bytefray V6 — M2 Checkpoint B Decision Package 01

2026-10-15, America/Indianapolis. **PREPARED FOR LEAD DECISION — NOT APPROVED.**

Recommendation: **PASS WITH CONDITIONS**, for adoption of the proposed design
and consideration of a separately authorized M2-2 slice. This is a documentation
recommendation, not a technical qualification PASS or permission to implement.
The lead accepted Review02's recommendation and authorized M2-1 preparation;
neither acceptance of this package nor authorization of M2-2 is recorded here.

## 1. Decision inputs and conditions

The decision bundle is [Scope/Contract Revision03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md),
the resolution matrix below and [Preparation Record01](V6_ALPHA_M2_1_PREPARATION_RECORD_01.md).
It addresses the exact [Review02](V6_ALPHA_M2_DESIGN_REVIEW_02.md) and unchanged
local Revision02 proposal identified by Scope §1. Accepted M1 behavior and final
technical acceptance remain authoritative; no M1 gate is reopened.

The lead is asked to accept these concrete choices:

1. K1/R1 policies, exact parameter ranges and both-seat fixture schedules in
   Scope §§4–6, under unchanged alpha1 mechanics and teaching-only restrictions.
2. Exactly two additional scaffold/CLI template choices, delivered one per agent
   slice, using exclusive personal-copy creation (Scope §3). This explicitly
   replaces Revision02's CLI-template exclusion.
3. Shared reconstruction plus separate, revision-bound in-memory scenario
   validators. New scenarios use only common demo v1 fields with no Scout
   success assertion; Scout's seven-event contract stays unchanged (Scope §7).
4. Symmetric A/B/Omni delivered projection, bounded layout work and an actual
   four-task human comprehension gate; platform and historical evidence stay
   partitioned (Scope §§8–11).
5. M2-1 through M2-6 order and stop conditions. Each subsequent slice needs an
   explicit grant. Any M2-2 grant is limited to §3 below.

Conditions before first code change: explicit lead acceptance of the revised
scope and Checkpoint B **and** explicit M2-2 implementation authorization;
baseline/ref/contract recheck; confirmation of safe disposable roots. A live
remote refresh remains pending after the local network connection failure. If
the published baseline has moved, assess the diff and bind a reviewed replacement
baseline before implementation; do not merge/reset/rebase another branch.

Runtime proof of schedules, new source-revision digests and scenario validators
are M2-2/M2-3 closure obligations. If a schedule or v1 representation cannot be
implemented under this contract, HOLD the affected slice and return for design
decision. No elapsed time or conditional recommendation satisfies an approval.

## 2. Finding-by-finding resolution matrix

“RESOLVED IN PROPOSED CONTRACT” means the normative correction, measurable gate
and verification design are supplied below. It does **not** mean adopted,
implemented, independently qualified or human-tested. Every implementation gate
is pending. No finding is closed just by acknowledging its subject. References
are to exact sections of Scope Revision03; M2-AC IDs are its §11 criteria.

| Review ID / severity | Required normative correction and exact proposed text/reference | Acceptance criterion | Proposed verification | Disposition |
| --- | --- | --- | --- | --- |
| F01 / HIGH | Scope §3's exact YAML object `capabilities: {version: 1, required: [sense]}` replaces the invalid list. §3 requires whole-roster mismatch before import/reset and match artifacts; §2 preserves explicit alpha1/stable defaults. | M2-AC01, AC04: valid manifests succeed under alpha1; stable V4 produces capability mismatch; malformed/unknown/duplicate cases produce metadata errors separately. | Manifest parser cases; sentinel import/reset and absent-artifact assertions across match/direct/worker/validate/test; explicit selector/default regression. | RESOLVED IN PROPOSED CONTRACT; executable verification pending M2-2/3. |
| F02 / HIGH | Scope §3 expressly adds `watchful_keeper`/`roaming_reacquirer` to the existing scaffold and CLI, one in each slice; exclusive copy, only name/display substitution, protected bundled bytes and manifest-default Development Test semantics are normative. Exact bounds are §§4/5. | M2-AC06 and AC01: copy, refusal, preserved capabilities/parameters, valid and invalid edits, explicit validation, full Advanced run/reopen, earlier-settings access. | Compare copy source/manifest to bundled revision; duplicate/unsafe destination probes; real Qt copy/parameter/native child workflow; inspect recorded reset/result and correct replay association. | RESOLVED IN PROPOSED CONTRACT; lead must accept the explicit CLI scope revision; workflows pending. |
| F03 / HIGH | Scope §4 K1 fixes own_core_base, eight modular offsets, single-process priorities, cadence and two parameter bounds. Delivered non-own READ triggers same-cell repair; delivered SENSE can trigger one in-reach WRITE. Missing feedback never triggers either. §6.1 fixes fixture setup only at core0. | M2-AC02/04/05: READ→repair and SENSE→defensive choice, no-threat/empty/refused/delayed/terminal cases, nonzero/wrapped cores and both seats; one action per choice. | Source data-access audit; supplied-observation decision cases; native bound trace witnesses and independent reconstruction; both-seat fixture schedule, no victory/hit claim. | RESOLVED IN PROPOSED CONTRACT; static schedule only, runtime proof pending M2-2. |
| F04 / HIGH | Scope §5 R1 defines receipt-driven HOLD/RESCAN/search/response, parameters and legal fallbacks; §6.2 fixture relocates on F4 only. Exact both-seat order yields R1 sample, R2 receipt, F4 relocation, R5 rescan, R6 absent receipt/MOVE, R7 new sample, R8 response. | M2-AC03/04/05: full sequence both seats, live fixture prefix, no notification/identity/core/TTL inference; receipt states/history remain distinct. | Trace phase/order and cost assertions; omniscient reconstruction confirms fixture relocation separately; entrant payload wording/history probes; false-empty/refused/missing/terminal variants. | RESOLVED IN PROPOSED CONTRACT; runtime proof pending M2-3. |
| F05 / HIGH | Scope §7 explicitly separates common reconstruction, source capture, scenario predicates and delivered-view availability. `keeper-K1`/`reacquirer-R1` use reviewed captured revisions and approved inputs, never sidecar narrative/name dispatch. New v1 envelopes omit Scout teaching_exchange and use status unverified; new completion exists only in a separate in-memory result/qualification record. New wire semantics require STOP. | M2-AC05/12: independent behavior witnesses and four repeats/new pairing/platform, complete captured inputs; valid-but-incomplete, false assertion, wrong archetype/revision and interrupted cases withhold completion. Scout semantics/evidence unchanged. | Compare approved/captured/loaded source fingerprints; recompute each bound digest and replay/trace state; run explicit predicates and negative variants; inspect existing v1 field meanings and absence of new fields; retain all bodies. | RESOLVED IN PROPOSED CONTRACT via bounded no-new-wire choice; implementation must prove it fits or HOLD for schema review. |
| F06 / HIGH | Scope §8: “SensingPresentation SHALL select explicit entrant A, entrant B or None for omniscience.” Reuse cursor/SensingView, filter upstream, clear prior view/history state; both delivered views share safe fallback and terminal gating. | M2-AC07: symmetric payload/age/local-row/step/pacing assertions at receipt/action/end/movement and every navigation/switch boundary; invalid optional sidecar alone preserves ordinary pair. | A/B mirrored tests; hidden-world divergence with identical permitted histories; backward seek/restart/scrub/Omni transitions; corrupt/missing trace/result and sidecar-only cases. | RESOLVED IN PROPOSED CONTRACT; implementation and native verification pending M2-4/5. |
| F07 / HIGH | Scope §9 defines exact two scenario cards, participant/assistance record and four agent/seat tasks. Participant must identify delivered evidence, sample vs receipt, paid alternative and the policy decision. Unexplained core lesson after declared help blocks closure. | M2-AC11: actual human completes and explains both lessons in both seats; assistance/misunderstandings retained. Developer participation supports only formative claims. | Human walkthrough record tied to artifact/revision/parameter identities, original answers then one-help restatement; technical scripts cannot substitute; lead evaluates deferred cosmetic issues separately. | RESOLVED IN PROPOSED CONTRACT; actual human evidence pending M2-6. |
| F08 / HIGH | Scope §10 binds 329 historical pins to preserved b948540..., keeps the adopted 72-node historical context separate, and requires approved product/compatibility selections, unchanged old starter digests/terminal order and capture regressions. No reseal, private input or product research call. | M2-AC09/12: product and historical evidence correctly partitioned; old bytes/manifests/fixtures unchanged, both new digests only, V4/default/reader/refresh/customization gates pass. | Candidate diff/digest audit; historical pin verification at preserved boundary; manifest/node selection reconciliation; focused→broader checks, Ruff and separate engine/client mypy; product isolation negatives. | RESOLVED IN PROPOSED CONTRACT; future candidate integrity/qualification evidence pending. |
| F09 / MEDIUM | Scope §1 replaces stale 5971966 input with full f79a74b HEAD/tree, exact Revision02 hash and divergent-branch SHA. §§10/11 require fresh disposable roots and account for absent original-worktree protection commits; integration is separately authorized. | M2-AC12 plus AC09: correct capture modules retained; exact refs/contracts/work/index and four inherited files preserved; drift stops entry. | Entry/exit Git and raw hash checks in Preparation Record01; read-only proposal hash; future pre-test absolute-root safety check and source identity manifest. | RESOLVED IN PROPOSED CONTRACT; local entry verified, current live remote refresh remains an explicit implementation-entry condition. |
| F10 / MEDIUM | Scope §8 fixes compact A/B/Omni controls and dedicated disclaimer/history rows at 900x650, 1000x700, 1100x750; §10 specifies native Windows AMD64 and Linux X11/Xvfb controls/fonts/evidence and COM/focus/comparison limits. | M2-AC08/10: all views, long histories, sizes and actual text/rectangles usable; affected controls and full native authoring/replay exercised independently on both platforms. | Layout assertions plus retained native frames and keyboard/mouse/resize/scroll/pause/step/reverse/close records, font resolution and original failed attempts; bounded logical comparison. | RESOLVED IN PROPOSED CONTRACT; native platform/layout proof pending M2-4/5. |

No contract correction is intentionally left unspecified. The pending approval,
implementation proofs, platform runs and human evidence are open gates, not
resolved runtime findings. A failed future gate reopens the affected finding;
this matrix cannot be used to waive it.

## 3. Exact M2-2 implementation boundary to consider for approval

Deliver the Keeper vertical slice only. Normal gameplay/API/policy modules are
consumed unchanged; no simulation changes are within this proposed grant.

| Proposed path/surface | Permitted delta in M2-2 |
| --- | --- |
| `engine/src/battle_engine/data/starter_agents/v6_watchful_keeper/agent.py`, `agent.yaml` | Implement only K1 policy/parameters/capability block and teaching comments. |
| `engine/src/battle_engine/data/teaching_fixtures/v6_encroaching_opponent/agent.py`, `agent.yaml` | Implement only §6.1 fixed callback script and ordinary manifest. Not a public starter. |
| `engine/src/battle_engine/starters.py` | Add Keeper adjacent to Scout plus Keeper's computed digest; retain all old entries/digests and terminal v5_dual_team. Reacquirer is added only in M2-3. |
| `engine/src/battle_engine/agent_scaffold.py`, `app/views/development.py` | Add Keeper template/label and personal-copy name/display substitution using existing exclusive-create route; adjust affected help/guidance only. |
| `engine/src/battle_engine/sensing_demo.py` | Small explicit Keeper role/scenario selection, seat reversal, approved captured inputs, common v1 provenance and complete output/source retention; preserve Scout defaults/path/verification. No generic scenario builder. |
| `engine/src/battle_engine/sensing_playback.py` | Add keeper-K1 validator and separate internal result consuming common immutable reconstructed facts; existing Scout evaluator/result/wire meanings remain unchanged. No new persisted format. |
| `engine/tests/test_v6_alpha_m2_keeper.py` (proposed new module) | Focused K1 observations/native trace/fixture/provenance/scenario/cost/negative cases. |
| Existing engine starter/scaffold/capability and `tests/test_v6_alpha_m1_5_designer.py` coverage | Extend affected tests for Keeper copy, parameter/default/stale-result/native-run behavior and invariant protection; GUI additions remain marked gui. |
| `docs/specs/agent_scaffold.md`, `docs/AGENT_AUTHORING.md`, a bounded M2-2 implementation record | Document Keeper template addition, explicit alpha1, manifest-default Test, parameters, verification evidence and exact candidate identities. |

This is a proposed reviewable surface allowlist, not staging or write permission.
If implementation requires another production path, record why and obtain scope
decision before widening it. Existing tests may be extended only for this slice's
behavior, never to weaken historical/golden/preservation assertions.

Excluded from M2-2: Reacquirer code/fixture/template/digest, A/B UI changes,
history/footer layout, collective ruleset description, scenario cards/human
evaluation, general CLI redesign, generic verification frameworks, wire/policy/API
changes, research paths, Spectator, packaging and release. Do not change existing
Scout source/manifest/digest. M2-2 must prove the Keeper workflow with the accepted
M1 viewer even while its known layout limitation awaits M2-4.

## 4. Required evidence before M2-2 can close

These are future checks; none ran during M2-1. Close only after a reviewed
implementation record maps exact test nodes and retained artifacts to each gate.

| Gate | Required evidence / failure rule |
| --- | --- |
| B2-01 capability/entry | Scope M2-AC01 affected routes; valid versioned object succeeds explicitly under alpha1, stable V4 mismatch precedes import/reset/artifacts, metadata errors separate; baseline/contract entry recheck passes. |
| B2-02 K1 behavior | Source audit plus supplied-observation and native tests verify exact priorities, cadence, both parameter bounds, eight modular core offsets at nonzero/wrapped starts, one action per decision, and legitimately delivered READ→repair/SENSE→defensive traces. No hidden/timer-driven repair. |
| B2-03 feedback negatives | No-threat, empty, refused/null, absent, delayed after suppression, terminal-undelivered and stale-coordinate cases; costs truthful, no hit/damage/core-identity claim. Consistent incomplete sequence cannot pass. |
| B2-04 both-seat scenario and reproduction | §6.1 executed through NativeMatchService to declared terminal/100-tick limit; two runs per seat on Windows and Linux (four each). Independent keeper-K1 witnesses; captured sources/inputs and loaded fingerprints agree; same-build logical comparison passes under declared timing exclusions. |
| B2-05 provenance and false-success resistance | Separate common artifact, reconstruction, source capture, Keeper completion and view results. Reject wrong source/archetype/inputs, false success, missing behavior, truncation, drift, corrupt binding; optional bad sidecar does not invalidate a valid ordinary pair. Preserve Scout teaching semantics. |
| B2-06 authoring | Actual New Agent exclusive Keeper copy/overwrite refusal, source/capability/parameter retention; explicit alpha1 Validate; valid and range-invalid edits; full Advanced execution and correct reopen, manifest-default Development Test and earlier-settings labels. Native affected workflow on each platform, not startup alone. |
| B2-07 compatibility | Focused existing modules below plus affected broader approved product/compatibility selection pass. Old starter bytes/digests, safe install/refresh/customization, V4 defaults/equivalence, historical readers/retired refusal, Scout and current capture tests preserved. |
| B2-08 engineering/preservation | Ruff and separate engine/client mypy pass after focused/broader checks; exact candidate diff/source manifest and safe roots retained; historical pins checked at preserved baseline, no sealed or private artifact changes or research activity. |
| B2-09 slice review | Lead accepts Keeper slice evidence and unresolved limitations; failure/missing platform gate holds closure. No automatic M2-3 entry, M2-wide technical PASS, human PASS, commit or publication. |

Focused existing regression anchors (extend, do not replace) are:

- Engine: `test_v6_alpha_m1_policy_capabilities.py`,
  `test_v6_alpha_m1_2_window_scout.py`, `test_v6_alpha_m1_3_sensing_playback.py`,
  `test_v6_alpha_sensing_playback_core_capture.py`, `test_agent_scaffold.py`,
  `test_starter_agents.py`, `test_starter_directory_validity.py`,
  `test_v5_alpha1_phase_e_starter_refresh.py`, `test_native_match_service.py`,
  `test_agent_validation.py`, `test_designer_ruleset_options.py`,
  `test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`.
- Client: `test_v6_alpha_sensing.py`, `test_v6_alpha_sensing_adversarial.py`,
  `test_v6_alpha_sensing_core_capture.py`, `test_v6_alpha_m1_5.py`,
  `test_v6_alpha_m1_5_adversarial.py`, existing replay/session/perspective cases.
- Designer: explicitly invoke affected GUI nodes under root `tests/`, including
  `test_v6_alpha_m1_5_designer.py` and `test_v6_alpha_m1_5_adversarial_designer.py`;
  pytest.ini's default testpaths do not include that directory.

The exact selection ledger must reconcile these with Scope §10's adopted
partitions and any additions. Avoid summing overlapping focused, broad, GUI,
supplemental, historical or platform counts. No unrestricted full-repository
pytest PASS is a substitute for that accounting.

## 5. Open risks, accepted-baseline limitations and nonclaims

| Item | Present disposition / gate |
| --- | --- |
| Lead acceptance and M2-2 grant | OPEN; mandatory before implementation. This preparation records no approval. |
| Current live remote state | OPEN entry verification; local upstream verified, network read unavailable. Drift requires review, not branch integration. |
| Static schedule feasibility and exact future revisions | OPEN implementation proof; tables are reasoned schedules, not engine-run witnesses. Capture actual candidate revisions and demonstrate both seats before slice closure. |
| v1 envelope fit and consumer clarity | Proposed common-envelope-only choice avoids changing Scout success semantics. Verify exact compatibility in M2-2; any new field/meaning requires HOLD and separate version review. New scenario result must not be advertised as existing demo-v1 teaching success. |
| New parameter combinations | Bounds fixed in contract; core policy behavior/range rejection must be tested. Exact teaching-sequence success is required for declared defaults, not promised for every edited combination/seed. |
| Hostile Python/seed reconstruction | Accepted M1 teaching-only limitation retained, public promotion prerequisite unresolved; no secrecy or arbitrary-Python determinism claim. |
| History/footer overlap | Accepted nonblocking M1 limitation; required M2-4 correction/M2-5 coverage. It remains present during Keeper slice. |
| Windows COM / Linux focus | COM caller/root cause unresolved; X11 activation prerequisite retained. Keep diagnostic/failure evidence; actual functional failure cannot be waived by the old nonblocking disposition. |
| M1 raw cross-platform artifact availability | Original published Windows complete pair unavailable; no retrospective record comparison claim. Retain complete new bodies for M2 comparisons. |
| Historical/private evidence | Preservation/instrument identity distinct from product source. M2-1 makes no fresh private inventory/backup claim. No source-pin reseal or altered authority record. |
| Human understanding | OPEN M2-6 gate; formative participant may need help. Record it and block closure on either unlearned lesson. No general enjoyment/balance/Requirement C inference. |
| Platform/release breadth | Only affected Windows AMD64 and Linux X11/Xvfb workflows are planned; Wayland, other distributions, full supported Python matrix, installers and unrestricted release remain outside this scope. |
| Replay performance and spectator scope | Existing rewind reconstruction cost remains. No checkpoint optimization, spectator redesign, Director/Fight Night, additional visual language or companion-project changes. |

## 6. Decision record — awaiting the Project Lead

| Decision | Recorded state |
| --- | --- |
| Review02 recommendation | ACCEPT WITH REQUIRED REVISIONS accepted by lead |
| M2-1 preparation | Authorized; this package is the documentation deliverable |
| Revised Scope Revision03 adoption | **AWAITING EXPLICIT ACCEPTANCE** |
| Checkpoint B | **AWAITING EXPLICIT ACCEPTANCE**; preparation recommendation PASS WITH CONDITIONS |
| M2-2 Keeper implementation | **NOT AUTHORIZED** |
| M2-3 through M2-6 | **NOT AUTHORIZED** |
| Commit/merge/push/release | **NOT AUTHORIZED** |
| Original E9 / successor / Requirement C | OPERATIONALLY BLOCKED and execution LOCKED / further successor work deferred / NOT ESTABLISHED |

Stop here for explicit lead acceptance of Scope Revision03 and Checkpoint B,
and a separate explicit M2-2 implementation grant within §3. Do not infer
approval from acceptance of the earlier review recommendation.
