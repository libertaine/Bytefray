# Bytefray V6 — Independent M1 Design Review 01

2026-10-09, America/Indianapolis. **BLOCKED ON CONTRACT DECISIONS.**

Review commissioned under section11 of the current lead instruction, after
drafting [M1 contract01](V6_ALPHA_M1_CONTRACT_01.md). Independent reviewer:
Codex subagent `/root/m1_contract_review`; contract author/recorder: root
Codex context. This is a product design review, not a scientific authority
appointment or an independent human review. The reviewer read the contract
and checked relevant source/specification boundaries; no files were edited,
matches/tests/research tools executed or Git mutations performed by the reviewer.

## Findings and dispositions

| Challenge | Independent finding | Contract disposition |
| --- | --- | --- |
| Unapproved research mechanics | The proposed T8-equivalent policy is bounded: no slot1 denial, mirrored passes, multi-tick capture or E9 controller. E8 identity and scientific state remain separate. | C explicitly lists inherited fields and excluded variants; new identity remains proposed. |
| Sensing cost and timing | Current controller consumes one action on applied/empty/out-of-reach requests and attempted invalid-action forfeits. Next-same-process receipt, delayed suppression and terminal cases match PR8. | D and AC1–AC4 make each boundary explicit. No cost-semantic blocker remains. |
| READ identity wording | Initial draft overstated that no enemy identity could be delivered: a valid READ supplies `previous_read_owner`. This does not identify an anonymous sensed contact. | D corrected to distinguish READ owner feedback from SENSE anonymity. |
| Observation leakage | A global callback step cursor could disclose hidden opponent callback counts, scheduling or disruption through rows, blank steps or pauses even if coordinates were hidden. | E now exposes only own phases/tick boundaries and local ordinals in entrant view. Hidden opponent rows/counters/pauses are prohibited; AC5 tests equivalence under an identical permitted prefix. |
| World/replay agreement | Existing binding and tick agreement are useful but do not verify SENSE results, receipt obligations or costs. Current passive projection cannot serve as a sensing projection unchanged. | Separate `sensing_playback.py`/client sensing projection adds the required checks and sub-tick cursor; canonical replay4/trace2/result2 and research consumers remain intact. |
| Teaching witness | Starts0/91, reach128, chunk2 support SENSE91 → next callback receipt → MOVE64. WRITE91 is legal later; no hit or core attribution follows merely from the write. Moving an opponent between sample and receipt needs a different action schedule. | D keeps the first witness and specifies a second scenario: A READ then SENSE at chunk end, B MOVE8, A receives old91. |
| Compatibility/lifecycle | Current E8 tests assert active policies are exactly E8's IDs, partition all policies into the existing lifecycle sets, and reject SENSE on every non-E8 ID. New product tests alone cannot make the full suite pass. | C proposes a public-experimental set; I identifies exact conflicting assertions; K4 requires lead-approved current-inventory evolution while retaining original qualified revisions and scientific/mechanic/golden expectations. No test bypass. |
| Seed reconstruction | PR8 §13's promotion prerequisite has not been closed. A teaching-only engineering exception does not follow automatically from alpha-direction approval and cannot imply unrestricted public information security. | K2 expressly requires lead disposition. No new scientific qualification campaign is demanded. |
| Determinism/source capture | Arbitrary editable Python is not certified deterministic. Incomplete or drifting source capture cannot support reproducible claims. | AC8 restricted to deterministic teaching revisions/same engine build. E requires complete revision capture, full-tree digest and initial/final Python fingerprint comparison; withhold badge on drift/incomplete capture. |
| Scope/platforms | The proposed native exchange, matching artifacts, isolated projection and viewer form a bounded testable slice. Later templates, multi-process UX, packaging and broader accessibility can remain later work. | M1 retains one starter/opponent and ordinary engine/client checks plus Windows/Linux interaction exercises. No research-scale assurance gate. |

Source checks: [controller scheduling/feedback](../../engine/src/battle_engine/process_runtime.py),
[SENSE semantics and trace fields](../research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md),
[pair/world validation](../../engine/src/battle_engine/spectator_derivation.py),
[passive projection](../../engine/src/battle_engine/spectator_perspective.py),
and [E8 policy-inventory tests](../../engine/tests/test_ruleset_v6_research_sensing_active.py)
(active-set assertion at222–227, lifecycle partition276–281,
non-E8 refusal434–451).

The reviewer re-read the READ/navigation corrections and C/I/K4 inventory
disposition before returning the classification. Its final response recommended
the determinism/source-capture clarifications and the separate moving-opponent
schedule; the root incorporated these into the final contract and this record.
No additional reviewer execution or scientific evidence is implied.

## Exact blockers before coding

Lead disposition of **K1–K4** in the contract is required. K2 (bounded seed
exception versus closure first) and K4 (explicit product-inventory evolution)
are substantive blockers. K1 approves the precise identity/mechanics/capability
proposal; K3 approves knowledge/artifact/M1 scope choices. Once resolved,
request a separate bounded implementation authorization.

**No remaining design-level cost, leakage, world-consistency or scope blocker
was found in the corrected proposal.** This conclusion is a design assessment;
the future acceptance tests have not been run. No source/test implementation,
new E9 study, scientific execution, staging, commit, push or publication is
authorized. Stop after this contract and review.
