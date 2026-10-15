# Bytefray V6 — M2 Scope Design Review 02

2026-10-15, America/Indianapolis. **Verdict: ACCEPT WITH REQUIRED REVISIONS.**
M2 is a suitable next product milestone. Revision 02 is not ready to function as
an implementation contract. The corrections below must be incorporated and the
revised scope and Checkpoint B designs accepted before implementation.

## Review scope, provenance and verified baseline

This is a critical static design review of the existing local M2 proposal.
The reviewer is the Codex context that performed the preceding E9
successor-feasibility assessment. It shares the user's repository, host and
supplied evidence. Proposal authorship and the independence of its earlier
Review 01 were not independently established. No organizational independence,
appointed operational-verifier role or independent observation of execution is
claimed. No agent, match, test campaign or human evaluation ran for this review.

| Baseline item | Verified observation |
| --- | --- |
| Reviewed checkout | `v6-m2-clean`; entry HEAD `f79a74be1d486f042d260bea672305b9abb27aa5`; clean tracked/index/untracked state |
| Upstream and live GitHub branch | `origin/v6-research` and read-only live `refs/heads/v6-research` both equal that HEAD; checkout ahead/behind 0/0 |
| Original worktree | Local `v6-research` at `2fc3c82e115650b515a4efab39afb172b62535ed`, ahead 4 / behind 3 relative to the live/tracking branch |
| Local-only commits | `9c81718` capture-verification fix; `b673b28` pytest-basetemp protection; `4e0e21e` retained-evidence restoration record; `2fc3c82` Spectator closure / Designer-test maintenance record |
| Published-side commits absent from that local branch | `4850310`, `19bdac3`, `f79a74b`; the published capture fix has overlapping source scope with local `9c81718`, not permission to merge either branch |
| Original worktree changes | Modified README; untracked M2 proposal, earlier alpha proposal, local research records, screenshots and retained qualification material; two research temp/cache directories could not be enumerated due to ACLs |
| Reviewed M2 proposal | Local-only `docs/V6_ALPHA1_M2_SCOPE_PROPOSAL.md`, **REVISION 02 — PROPOSED, NOT ADOPTED**, dated 2026-10-12, 20,822 bytes |
| Proposal raw SHA-256 | `e97dca6c48f8e1b4e787b44d0870e44836f0ebc716f3ef9f1d1b3955aaddf7f1` |

The proposal exists in the original worktree, not in this checkout or the
published baseline. References below to its sections/line numbers identify those
exact local bytes. They are not links to a purported published contract. No local
proposal, README edit, commit or excluded record was transplanted, overwritten or
discarded. This review makes no complete inventory claim about ACL-inaccessible
research directories and does not require access to their contents.

Governing sources are the [M1 final acceptance](V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md),
[M1 contract](V6_ALPHA_M1_CONTRACT_01.md), adopted
[Phase 0 packet](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md), historical
[recommendations](V6_ALPHA_M1_RECOMMENDATIONS_01.md), and M1 implementation records
[M1-2](V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md),
[M1-3](V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md),
[M1-4](V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md) and
[M1-5](V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md). Later adoption/final acceptance
controls their earlier proposal or pending-qualification language. Relevant
architecture and existing feature specifications were checked; no adopted M2
specification was located under `docs/specs/`.

## Findings requiring revision

HIGH means a contract, evidence, information-boundary or essential user-workflow
gap that blocks implementation acceptance. MEDIUM means a bounded acceptance or
scope correction required before adopting the implementation plan. These are
design findings, not reproduced runtime failures or new M1 defects.

### F01 — HIGH: Capability declaration contradicts the accepted schema

**Sources:** local REV02 §§3.1, 3.2 and 3.5.2, lines 55, 77 and 148;
[capability parser](../../engine/src/battle_engine/agent_capabilities.py#L18);
M1 contract §C and the existing Window Scout manifest.

The proposal repeatedly specifies `capabilities: ["sense"]`. The parser requires
the versioned object below; a list fails manifest validation before the intended
ruleset-mismatch test. AC1/AC3 would test the wrong failure if implemented literally.

```yaml
capabilities:
  version: 1
  required: [sense]
```

**Correction/gate:** use this existing shape without changing API or schema.
Check valid manifests, malformed/unknown metadata, explicit alpha1 success, and
stable-V4 mismatch before agent import/reset or creation of match artifacts.

### F02 — HIGH: Personal-copy workflow is missing under the scaffold exclusion

**Sources:** local REV02 §§3.5.1, 3.5.3 and §5, lines 145 and 153;
M1 contract §F; M1-5 §Designer and native player workflow;
[New Agent dialog](../../app/views/development.py#L110) and
[scaffold templates](../../engine/src/battle_engine/agent_scaffold.py#L44).

Registering the new starters makes them discoverable but does not supply a New
Agent personal-copy path. That dialog calls the scaffold's fixed template set.
Preserving that set while requiring the established authoring loop leaves the
user without a specified safe copy operation for the two new agents.

**Correction/gate:** the simplest revision is to permit two additional starting
points through the existing scaffold/copy machinery, with explicit acknowledgement
that CLI template names would also expand. This is a proposed scope revision,
not permission to make it now. If the CLI prohibition is retained, specify a
bounded Designer-only copy path at Checkpoint B instead. Do not introduce a
general plugin/template framework. For each starter, require exclusive copy
creation, overwrite refusal, retained parameters/capabilities, protected bundled
bytes, valid/range-invalid parameter edits, explicit ruleset validation, full
Advanced execution, correct replay association, and earlier-settings labeling.
Keep Development Test's manifest-default semantics and guidance explicit.

### F03 — HIGH: Keeper's defensive choices need an information-valid contract

**Sources:** local REV02 §3.1, lines 54–66 and AC2/AC5; M1 contract §§D and F;
M1 final acceptance AC4/AC5.

“Core base 0” is a teaching-coordinate choice, not a valid general starter rule:
ordinary seeded placement and reversed seats need the agent's own core base.
SENSE reveals anonymous anchors, not core ownership or damage. A WRITE marked
applied does not establish that a sampled opponent is still there or was disrupted.

**Correction/gate:** remain at `own_core_base`, address its eight cells by modular
own-relative offsets, and define one small single-process state machine. Specify
how delivered READ ownership triggers a repair attempt, when legal perimeter
SENSE is worth its action, and when a delivered address justifies an attempted
disruption WRITE. Define priority, cadence, pending-feedback handling and parameter
bounds before coding. Require a trace witness of delivered READ -> repair and
delivered SENSE -> defensive choice, plus no-threat and empty/refused/delayed cases.
Every action consumes an ordinary opportunity; there is no combined scan/repair
action, guaranteed hit, omniscient damage alert or match-victory requirement.
Use fixed core 0 only in the declared fixture setup.

### F04 — HIGH: Reacquisition cannot depend on scan notification or target identity

**Sources:** local REV02 §§3.2 and 3.3.1, especially line 99; M1 contract §§D/E;
[receipt/history projection](../../client/src/battle_client/sensing.py).

The relocating fixture is described as moving “after being scanned.” SENSE does
not notify its opponent. A positive old contact plus a later empty window also
does not establish which anonymous process moved or why it disappeared. Receipt
absence, failed scans and suppressed callbacks are not empty scans.

**Correction/gate:** script the fixture from its own deterministic callback count
or other permitted input, never from the other entrant's scan event. Checkpoint B
must give an achievable chunk-size-2 schedule for both seats: positive sample ->
delayed delivery -> fixture relocation -> delivered applied rescan with the old
address absent -> purposeful legal search/MOVE -> a new positive receipt -> legal
response. The opponent must survive long enough to exhibit the sequence. Verify
the fixture's relocation independently in omniscient reconstruction; entrant text
says only “old address absent in newer sample” and “new anonymous contact.” Do
not identify it as the same enemy, infer a new core, add TTL, refresh historical
coordinates, or import E8/E9 controller heuristics. Preserve old samples/history.

### F05 — HIGH: A successful reconstruction is not an archetype verification

**Sources:** local REV02 §3.3.2, AC6 and Checkpoint B item 3;
[demo producer](../../engine/src/battle_engine/sensing_demo.py#L489),
[teaching evaluator](../../engine/src/battle_engine/sensing_playback.py#L1557),
and M1-3/M1-5 verification distinctions.

The current demo runner resolves Window Scout and its stationary opponent; the
teaching evaluator recognizes Scout and the 91/+64 exchange. Valid replay/trace
reconstruction alone, or absence of `ExchangeReconstructionError`, cannot verify
Keeper repair or Reacquirer loss/reacquisition. Arbitrary sidecar narrative cannot
select a trusted strategy verifier.

**Correction/gate:** retain common binding, cost, receipt and world reconstruction;
add only small explicit scenario validators over reconstructed facts, using
digest-bound entrant revisions and approved inputs. Preserve the existing Scout
validator and its historical artifacts. Keep artifact consistency, scenario
completion, source capture and entrant-view availability as separate results.
Negative cases must include a valid pair with a missing required behavior, a
false success assertion, wrong archetype/revision, and an interrupted sequence.
Use the existing v1 envelope only where its actual field semantics suffice. Any
required new field or changed wire meaning must stop for separately authorized
schema/version review. Preserve Scout starter bytes and existing evidence;
do not promise byte-identical newly generated artifacts across engine revisions.

### F06 — HIGH: Agent B support needs symmetric knowledge and navigation gates

**Sources:** local REV02 §3.4.2 and AC8;
[presentation adapter](../../client/src/battle_client/sensing_presentation.py#L108),
[cursor switching](../../client/src/battle_client/sensing.py#L574), and M1-4/M1-5.

The adapter currently fixes entrant A and exposes a boolean A/omniscient switch.
The underlying cursor already accepts a valid entrant ID. This is a small adapter
and UI extension, but acceptance currently names only the existence of three views.

**Correction/gate:** reuse the cursor and existing `SensingView`; select A/B/None
explicitly without a second projection system. Test A and B symmetrically before
receipt, at receipt/action/tick end, after relocation, backward seek, restart,
scrub, and omniscient -> entrant transitions. Assert payloads, contact ages,
entrant-local rows/step counts/pacing, cleared screen/history state and terminal
gating. Hidden-opponent divergence with identical permitted history must leave
each entrant's presentation unchanged. Missing/corrupt trace/result binding must
retain labeled replay-only omniscience and disable both delivered views. A broken
optional sidecar must not invalidate an otherwise valid ordinary pair.

### F07 — HIGH: “Explain why” lacks a human acceptance rule

**Sources:** local REV02 §4 and AC11; M1 contract §F;
[presentation notice](../../client/src/battle_client/sensing_presentation.py#L112);
M1-5 §§Replay association and Renderer boundary.

The current viewer intentionally provides factual events and withholds strategy
motives. Recording that someone clicked both perspectives does not show they can
understand a defensive choice or the cost of reacquisition. Machine traces and
automated GUI interaction are insufficient evidence of human comprehension.

**Correction/gate:** use a short scenario card tied to the exact teaching revision
and parameters before adding any explanation framework. Have an actual human
identify the delivered evidence, distinguish sample time from receipt time, state
the competing action opportunity, and explain one Keeper repair/defensive choice
and one Reacquirer rescan/MOVE choice, across both seat configurations. Record
identity/role or declared anonymous participant ID, platform, inputs, assistance,
task completion and misunderstandings. A walkthrough can be assisted, but record
the assistance. Inability to explain either core lesson after the declared help
blocks the M2 teaching objective; cosmetic issues may be deferred explicitly.
One developer participant establishes only a formative baseline, not general user
comprehension, enjoyment, balance or Requirement C. Any in-view starter-rule text
must be separately specified, revision/action checked and withheld on mismatch;
never infer motives for arbitrary agents or expose omniscient answers in entrant UI.

### F08 — HIGH: Regression and historical-pin obligations are conflated

**Sources:** local REV02 §§6–8, AC9/AC12, lines 205 and 225–228;
M1 final acceptance §§4/6; [Disposition 03](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md).

The 329 historical pins bind a historical instrument. Shared product files have
already evolved. Demanding they match the current product tree, or treating an
unpartitioned repository pytest run as the sole gate, repeats the incompatibility
the accepted M1 evidence explicitly separates. New starter registration will also
change product source identity intentionally.

**Correction/gate:** retain unchanged manifests, goldens and historical sources;
verify their pins against the preserved historical boundary. Qualify evolved
product behavior separately with focused engine/client/Designer cases, stable-V4
equivalence, historical readers, starter install/refresh/customization and current
capture reconstruction. Preserve `v5_dual_team` terminal order and every old
starter digest; add only the two new starters/digests. Use approved M1 product,
compatibility and historical partitions with explicit selections and provenance,
not ad hoc exclusions of failures. Run Ruff and separate engine/client mypy after
focused validation. No current-tree research-instrument PASS, summed overlapping
counts, reseal, private evidence read, research-controller call or new E9 run is
needed for M2 acceptance.

### F09 — MEDIUM: Update the input baseline and preserve branch divergence

**Sources:** REV02 header baseline `5971966`; verified Git observations above;
published `f79a74b` capture fix and its engine/client regression modules.

The proposal predates the published capture reconstruction fix. The original
worktree's local fixes and maintenance/protection commits are also not all in the
published branch. “Continue v6-research” cannot mean silently overwriting either
side or assuming every local document/test guard is published.

**Correction/gate:** bind the revised scope to a named reviewed commit and exact
proposal bytes. Include the current published capture tests and retained M1
semantics. Handle any later branch integration as a separate reviewed action;
never reset/rebase/switch as a side effect of scope acceptance. Before any future
test campaign, use a fresh disposable test root and account for retained-evidence
protection without importing or restoring private E9 material in this worktree.

### F10 — MEDIUM: Layout and platform gates need specific exercised coverage

**Sources:** local REV02 §§3.4.1/3.4.2, AC7/AC10;
[sensing renderer](../../client/src/battle_client/renderers/sensing_renderer.py#L129);
M1 final acceptance §5.

Adding a third perspective control competes with the existing header layout.
“Windows/Linux passes” does not define required controls, retained evidence,
fonts or Linux display assumptions.

**Correction/gate:** use one compact selector or three short controls, reusing
existing keyboard conventions. Specify minimum 900x650, default 1100x750 and at
least one intermediate resize, with long scan/READ history and each perspective.
Require disclaimer/history/control rectangles and actual rendered text to remain
nonoverlapping and usable on Windows AMD64 and Linux X11/Xvfb with recorded font
resolution. Exercise keyboard/mouse switching, scrolling, resize, pause/step,
reverse seek and close; headless rendering is supplemental to native interaction.
Retain X11 focus prerequisites and any failed attempts. Keep the unresolved Windows
COM diagnostic qualified as such. Do not claim Wayland, other distributions,
installer acceptance or the full Python-version matrix from this bounded campaign.

## Proposed acceptance gates replacing vague expectations

These are review recommendations, not adopted contracts or executed checks.

| Proposal criterion | Required measurable gate before closure |
| --- | --- |
| AC1/AC3 | Versioned capability manifests; explicit alpha1 success; stable-V4 rejection before import/reset/artifacts; malformed metadata is a distinct error |
| AC2 | Delivered READ supports a core-relative repair attempt; delivered SENSE supports a legal defensive choice; costs, priority and negative cases match the accepted Keeper state machine |
| AC4 | Recorded positive receipt, scheduled relocation, delivered applied rescan absence, search/MOVE, new positive receipt and response; both seats; no entrant inference of hidden movement/identity |
| AC5 | Static data-source audit plus trace/payload assertions; no seed/placement inference or hidden callbacks; absent/refused/empty/terminal-undelivered states remain distinct |
| AC6 | All three declared scenarios verify against their own approved predicates; valid incomplete and tampered variants withhold success; repeat each new pairing twice per seat on the same build with captured sources/inputs and declared timing exclusions |
| AC7/AC8 | Nonoverlapping layout at minimum/default/intermediate sizes; full A/B/omniscient controls; safe navigation/fallback; both new personal-copy/parameter/run/reopen workflows |
| AC9/AC12 | Approved product/compatibility selections and historical preservation checked separately; old starter bytes/digests and frozen evidence remain unchanged; no scientific authority effects |
| AC10 | Actual affected Windows and Linux X11 workflows with retained commands, inputs, outputs and interaction evidence; cross-platform comparison uses equivalent inputs/logical facts, not assumed raw-byte equality |
| AC11 | Human attempts and explanations of both learning goals in both seat configurations recorded with assistance and limitations; unresolved core misunderstanding prevents teaching-objective acceptance |

Parameter ranges/defaults, fixed fixture starts, callback schedules and predicate
identities must be explicit Checkpoint B outputs. Two repeats for two new pairings
in both seats mean eight bounded product teaching runs per environment, not a
research sample or a competitive benchmark. Existing Scout characterization stays
in the regression selection. Further runs require a concrete coverage gap.

## Bounded proposed M2 implementation sequence

This proposed numbering replaces the proposal's workstream numbering only if the
lead adopts it. It does not itself authorize any work below. Keep Checkpoint B as
the strict design hold before coding; split Checkpoint C into reviewable slices.

| Slice | Deliverable | Acceptance and stop condition |
| --- | --- | --- |
| M2-1 — Contract and scenario preparation | Corrected scope; two small single-process behavior/parameter contracts; fixture schedules for both seats; bounded scenario-validator plan; copy-path decision; A/B UI sketch; exact AC/platform/human plan | Lead accepts revised scope and Checkpoint B package. Stop on unavailable information, unachievable schedule, schema change, new mechanic, research dependency or unresolved personal-copy path. Documentation only. |
| M2-2 — Keeper vertical slice | Keeper + internal encroaching fixture; minimal scenario orchestration/validator; registration/digest and approved copy integration for this agent | Capability rejection, core-relative READ/repair and SENSE/defensive trace witnesses, captured input/source repeatability and safe authoring loop pass focused checks. Stop if a scripted timer or hidden state substitutes for delivered evidence. |
| M2-3 — Reacquirer vertical slice | Reacquirer + internal relocating fixture; its explicit scenario validator; registration/digest and approved copy integration | Both-seat observation/absence/search/reacquisition sequence and negative cases pass; costs/age/reach remain truthful; Scout characterization preserved. Stop on scan notification, implicit identity tracking, TTL or new wire semantics. |
| M2-4 — Delivered-view and usability slice | Reuse cursor for A/B/omniscient selection; fix footer/history separation; collective starter guidance and concise scenario cards | Symmetric payload/navigation/fallback tests and minimum-size layout checks pass. Stop on hidden-state/pacing leakage, raw-world entrant inputs, or a need for spectator redesign/new explanation framework. |
| M2-5 — Technical qualification | Focused and appropriate broader checks, exact integrity/compatibility evidence, Windows/Linux native workflows and declared-repeat comparison | Every technical AC has bounded evidence; failures and unresolved platform gaps retained. Stop on semantic regression, historical pin/evidence mutation, unsafe temp root or unaccounted source/input drift. |
| M2-6 — Human evaluation and closure review | Actual human walkthrough record, corrected blocking defects within approved scope, final AC dispositions and limitations | Lead assesses comprehension and technical evidence together. Stop if core lessons remain unexplained or required platform gates are open. Closure is separate from any later publication or release authorization. |

**First code-bearing milestone to consider after revised scope and Checkpoint B
acceptance: M2-2, the Keeper vertical slice.** It is the smallest end-to-end way
to validate meaningful defense and the shared demo/copy path before mobile
reacquisition and broader replay changes. No coding is authorized by this review;
even M2-1 preparation beyond the present report needs a subsequent scope decision.

## Simplifications and retained boundaries

Keep the existing ruleset, native match service, single-process teaching profiles,
parameter widgets, revision capture, common reconstructor and cursor. Use fixed
product fixture inputs and two small behavior validators. Defer scenario builders,
policy DSLs, generic strategy explanations, new telemetry, tournaments, rankings,
multi-process UX and spectator redesign. The internal opponents remain fixtures,
not fourth/fifth advertised starters. Advanced/Development retain explicit alpha1
selection; Simple/Evaluation retain stable V4. The Version 5 About dialog needs
no M2 change.

E9 feasibility acceptance, deferral and unchanged authority are recorded in the
[project-direction decision](V6_PROJECT_DIRECTION_DECISION_20261015.md). M2 must
not acquire E9 custody infrastructure, entropy protocols, bootstrap/payoff
analysis, authority records or private research inputs as dependencies. Product
demonstrations do not establish Requirement C, balance or human enjoyment.
Bytefray 5.1 packaging/release remains a separate unapproved scope, and
Bytefray-Spectator remains a separate project.

## Present documentation change set and validation boundary

The exact intended repository file set for this task is:

- `README.md` — potential-release wording and current M2/E9 direction.
- `docs/ROADMAP.md` — current status, E8 completion, E9 deferral, M1 closure and M2 priority; historical results retained.
- `docs/v6/V6_PROJECT_DIRECTION_DECISION_20261015.md` — new non-normative lead-decision record.
- `docs/v6/V6_ALPHA_M2_DESIGN_REVIEW_02.md` — this review and proposed sequence.

Documentation validation checked 49 added local links (including source-line
anchors), with no failures; tracked and new-document whitespace checks passed.
The changed path set is exactly the four files above, the index is unchanged,
and HEAD remains `f79a74be1d486f042d260bea672305b9abb27aa5`. The local proposal's
raw hash still matches the reviewed identity. Research, engine, client, app and
test paths have no diff; unrelated original-worktree work was not changed.
This is not a fresh per-file private-evidence preservation audit. No tests, match runs,
source changes, research operations, staging, commit, merge, push or release
occurred. This report supplies no new technical PASS. Stop for lead review.
