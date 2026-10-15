# Bytefray V6 — M2 Scope and Contract, Revision 03

2026-10-15, America/Indianapolis. **PROPOSED — NOT ADOPTED.**
M2-1 documentation preparation is authorized. M2-2 implementation and later
slices require separate Project Lead authorization after explicit acceptance of
this scope and [Checkpoint B](V6_ALPHA_M2_CHECKPOINT_B_01.md). Preparation is not
approval. SHALL below describes the proposed contract upon adoption.

## 1. Authority, purpose and exact baseline

The lead accepted the [Review 02](V6_ALPHA_M2_DESIGN_REVIEW_02.md) recommendation
**ACCEPT WITH REQUIRED REVISIONS** and authorized contract preparation only.
M2 completes the three-agent teaching lineup and bounded diagnostic usability
work. It adds no gameplay mechanic and establishes no competitive advantage,
balance, enjoyment, public-release readiness or Requirement C result.

Precedence: [M1 final technical acceptance](V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md),
adopted [Phase 0 decisions K1–K4/C-1–C-4](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md),
and [M1 Contract 01](V6_ALPHA_M1_CONTRACT_01.md) govern retained behavior. M1 is
technically PASS/CLOSED at `053e3eb1bc355ac1f4f15cba5d025b70ba418c1d`;
earlier pending language does not reopen it. M2 extends product teaching content
under those restrictions; it does not expand the teaching-only seed exception.

| Identity | Preparation baseline |
| --- | --- |
| Repository / checkout | `libertaine/Bytefray`; `D:/Projects/BATTLE2/work/v6-m2-clean` |
| Branch / HEAD | `v6-m2-clean`; `f79a74be1d486f042d260bea672305b9abb27aa5` |
| HEAD tree | `d4f2c73cbd3965762e61316567537e173503ff8a` |
| Upstream / locally recorded upstream SHA | `origin/v6-research`; same SHA as HEAD, ahead/behind 0/0 |
| Remote URL | `https://github.com/libertaine/Bytefray.git` |
| Divergent local branch to preserve | `v6-research` at `2fc3c82e115650b515a4efab39afb172b62535ed`; ahead 4 / behind 3 against the recorded upstream |
| Reviewed predecessor | Original-worktree `docs/V6_ALPHA1_M2_SCOPE_PROPOSAL.md`, Revision 02, 20,822 bytes; raw SHA-256 `e97dca6c48f8e1b4e787b44d0870e44836f0ebc716f3ef9f1d1b3955aaddf7f1` |
| New contract identity | This Revision 03 plus Checkpoint B 01; exact input hashes and preparation checks in [Preparation Record 01](V6_ALPHA_M2_1_PREPARATION_RECORD_01.md) |

The predecessor was read in place, not copied or edited. Upon adoption, this
revision replaces its proposed M2 scope/numbering, including its CLI-template
exclusion. The four inherited review changes remain byte-identical to entry.
There is no branch integration or publication permission. Review 02 recorded a
live remote check; this preparation's read-only `git ls-remote` could not connect.
The upstream values above are current local refs, not a new live-remote claim.
Future implementation entry SHALL recheck refs, actual working/index changes,
contract bytes and any newly published source drift before making changes.

## 2. Retained gameplay and information contract

Stable `bytefray-rules-4` SHALL remain the default, including omitted CLI ruleset,
fresh Designer selectors, Simple and Evaluation. Advanced/Development SHALL
require explicit `bytefray-rules-6-alpha1` selection. Selecting a starter SHALL
not switch rulesets. Research identities SHALL stay out of product selectors.

Alpha1 retains API v2, replay4, trace2, result2, capability metadata v1 and demo
sidecar v1. Its independent policy remains: chunk size 2, rotating starting seat,
forward passes, round-robin own processes, seeded core placement and core-base
initial anchors, literal MOVE clamped to ±64, capture hold 1, whole-tick disruption
D=1, active sensing half-width 27, inert detection-radius metadata 32. Core size
is eight. No scheduler overrides, hidden MatchRequest switches or new policy IDs.

Both new starters SHALL use one process `main`, reach 128, share 1.0. The bounded
demo profile is arena 512, Q=8, seed 0, 100-tick limit, default parameters, direct
starts declared in §6. Ordinary Advanced matches retain normal seeded placement;
the agent policies SHALL work relative to their own observed core/anchor.

Agents SHALL check `context.sensing_window` before SENSE, and use only delivered
ObservationV2 fields, own stored actions/receipts/counters and declared parameters.
They SHALL NOT derive placement from context seed/RNG, read host files/time,
import placement/research controllers, observe opponent callbacks, or consume
replay/trace/fixture scripts. Fixture constants are setup inputs, not starter
runtime knowledge. This is the accepted teaching-only threat model, not a hostile
Python sandbox or PR8 §13 seed-secrecy closure.

Every READ, WRITE, MOVE or SENSE costs one ordinary eligible opportunity.
SENSE's legal center is within current reach; its inclusive ±27 window returns
sorted unique anonymous live enemy anchors at action time. It gives no core,
damage, identity or notification. Only the next eligible callback of the same
process receives the sample, even after suppression. Applied empty `()`/`[]`,
refused null/false, absent non-SENSE feedback and terminal non-delivery SHALL
remain distinct. A delivered READ can reveal value and last-writer owner; this
does not identify an anonymous sensed process. WRITE application proves a write,
not a hit, continued target presence, repair success at a later time or victory.
Historical receipts SHALL persist without TTL, live refresh or global negatives.

## 3. Capability, starter registration and personal copies

Both new manifests SHALL declare exactly the existing shape:

```yaml
capabilities:
  version: 1
  required: [sense]
```

Valid alpha1 operation and stable-V4 capability mismatch SHALL be tested
separately from malformed metadata. Unknown versions/names, duplicate requirements
and list-shaped blocks SHALL fail closed. Whole-roster mismatch SHALL precede
agent import/reset and match replay/result/trace creation, including worker,
validation, development-test and direct-controller routes. Legacy manifests
without the optional block retain existing semantics.

Add `v6_watchful_keeper` then `v6_roaming_reacquirer` immediately after
`v6_window_scout` and before terminal `v5_dual_team` in STARTER_AGENT_NAMES;
add only their CURRENT_STARTER_DIGESTS entries. Every old bundled starter byte,
digest, order relationship and customized installed copy SHALL be preserved.
The two internal opponents SHALL NOT become catalog starters or scaffold choices.

Proposed copy-path decision: extend the existing scaffold with exactly
`watchful_keeper` and `roaming_reacquirer` template keys pointing at their bundled
starter directories. This intentionally expands CLI `agents create --template`
choices as well as New Agent. Existing blank/annotated/window_scout defaults and
choices remain. Update the bounded [scaffold specification](../specs/agent_scaffold.md)
and help text during the relevant implementation slice; do not build a framework.

New Agent labels SHALL be “Watchful Keeper — personal copy” and “Roaming
Reacquirer — personal copy”. Reuse exclusive creation/rename and destination
containment; refuse overwrite, invalid IDs and unsafe destinations. Only the
copy's manifest name/display SHALL change; its source, capabilities, parameters
and presets SHALL equal the selected bundled revision. Do not modify bundled
bytes while creating or editing a copy.

Reuse canonical parameter schemas/widgets/resolver. Validate type and range
before execution; capture effective overrides in reset/result/run evidence.
Development Validate remains a supervised dry run bound to source/ruleset;
Development Test remains a full native match using manifest defaults, with visible
guidance directing parameterized full matches to Advanced. Changed source/ruleset
invalidates validation. Parameter/source changes label retained earlier output as
earlier settings/revision; never rewrite its inputs or lose replay association.
For each new starter require actual copy → explicit alpha1 validation → valid
parameter edit → full Advanced match → result-associated reopen, range-invalid
rejection, stable-V4 rejection, overwrite refusal and retained earlier run access.

## 4. Watchful Keeper policy K1

This is a small defensive policy, not an inferred-damage system. Its fixed anchor
SHALL remain at observed `own_core_base`; it never MOVEs. Core addresses are
`(own_core_base + i) % arena_size`, `i=0..7`. Reset clears stored feedback/action,
callback counter and core-read cursor (initial offset 0). Repair/defensive byte is
the constant `0x4b`; repair means an attempted ownership-restoring WRITE, not
restoration of an unknown original value.

| Parameter | Integer default | Inclusive bounds | Meaning |
| --- | ---: | --- | --- |
| `scan_interval` | 4 | 2..16 | Consider perimeter SENSE on eligible callback ordinals divisible by this value, after feedback priorities |
| `perimeter_offset` | 27 | 0..128 | Forward own-core-relative scan center; normalize modularly and recheck current reach |

At each eligible callback increment the own counter, consume the prior action's
feedback once, then choose exactly one action by this priority:

1. If the preceding own action was READ of an own-core cell and its delivered
   feedback is applied with a value and an owner different from own entrant ID
   (including a legitimately read unowned cell), WRITE `0x4b` to that address if
   still in reach. Do not retain a repair retry based on missing/refused feedback.
2. Otherwise, if the preceding action was an applied SENSE with a nonempty
   delivered receipt, choose the smallest sampled address currently in reach
   and WRITE `0x4b` there once. This is a defensive attempt on an old sample.
   Do not keep attacking indefinitely from that receipt. Store it as history.
3. Otherwise, if the cadence is due and active sensing is available, SENSE the
   legal `(own_core_base + perimeter_offset) % arena_size` center.
4. Otherwise READ the next own-core offset and advance the cursor modulo eight
   when issuing the READ. A refused READ is not evidence of ownership loss.

If a candidate in priorities 1–3 is unavailable/illegal, continue down the list.
Repair outranks defensive writing, which outranks scheduled sensing, which
outranks routine inspection. Only one prior-action feedback kind exists at each
callback; these priorities never combine scan/read/repair into one opportunity.
Missing/null feedback cannot trigger a repair/contact claim. Applied empty scan
has no defensive target. Suppression advances neither the own callback counter
nor a synthetic feedback state. After WRITE, inspect again through ordinary
READs; do not treat previous_action_applied as a damage or hit report.

Required witnesses: delivered non-own READ → same-cell repair attempt; delivered
positive SENSE → legal defensive WRITE; no-threat inspection/cadence; empty,
refused, delayed and terminal-undelivered feedback; modular cores and both seats.
Seeded nonzero-core tests SHALL reject any accidental absolute-core-0 policy.

## 5. Roaming Reacquirer policy R1

Reset clears counter, samples, target and wait count; initial mode is SEARCH.
All targets are anonymous addresses. Deterministic shortest signed direction
uses forward on an exact tie; MOVE magnitude never exceeds move_step or 64.
The response byte is `0x52`. The agent never accesses an enemy core.

| Parameter | Integer default | Inclusive bounds | Meaning |
| --- | ---: | --- | --- |
| `search_offset` | 91 | 0..128 | New-search center relative to current own anchor |
| `move_step` | 64 | 1..64 | Forward exploration step and maximum contact-response MOVE |
| `rescan_wait` | 3 | 1..8 | Paid READ actions after a positive receipt before rescan; includes the receipt callback if a READ is issued there |

| State / delivered evidence | Exactly one action and next state |
| --- | --- |
| SEARCH, no pending feedback | SENSE `(self_anchor + search_offset) % arena_size` if legal; await its next same-process receipt. If unavailable, use legal fallback below. |
| SEARCH applied empty receipt | Retain that empty sample, MOVE forward by move_step, then request a new anchor-relative scan on the next callback. There was no prior target, so report no old-address absence or lost-contact event. |
| Initial SEARCH applied positive receipt | Store smallest address as historical target; enter HOLD with rescan_wait READs. Issue the first wait READ now (own_core_base if in reach, otherwise self_anchor); decrement wait after each issued READ. |
| HOLD | Issue remaining wait READs; use own_core_base if in reach, otherwise self_anchor. When none remain, SENSE the stored address if legal and await RESCAN receipt. No live refresh during waits. |
| RESCAN applied receipt contains old address | Record a newer sample of that address, without identity inference; restart HOLD and its paid READ wait. |
| RESCAN applied receipt omits old address | Record only “old address absent in newer sample”; retain prior samples, enter SEARCH_AFTER_ABSENCE and MOVE forward by move_step. No global disappearance or movement claim. Other addresses in the receipt remain separate anonymous samples. |
| SEARCH_AFTER_ABSENCE after MOVE, or after an empty search receipt | Issue a new anchor-relative SENSE after each forward MOVE. Applied empty search alternates with another forward MOVE; it is not a sensor error. |
| SEARCH_AFTER_ABSENCE applied positive receipt | Record “new anonymous contact”; select smallest address. If in reach, WRITE `0x52` once then enter HOLD; otherwise MOVE toward it by at most move_step and enter RESPONSE. Never equate this contact with the old one. |
| RESPONSE | Recheck current reach of remembered address; WRITE once if legal and enter HOLD, otherwise bounded MOVE toward it. This is a response to a historical coordinate, not tracking. |
| Refused/null/absent scan feedback | No absence/positive transition. Drop the pending request only when its actual next callback is handled; resume a fresh anchor-relative search, preserving historical samples. |

When entering HOLD after a response WRITE, start its READ wait on the following
callback. All branches first reconcile the actual previous action and feedback;
an unrelated READ or a suppressed opportunity is not a scan receipt. A delayed
receipt retains its original sample point and is processed once when delivered.
If a target/scan center is illegal, resume anchor-relative search rather than
issue an illegal WRITE. Fallback is READ own_core_base if within current reach,
otherwise MOVE(0), each costing one action. A substituted fallback does not count
as a SENSE, rescan receipt, repair, search MOVE or successful response witness.
Wait READs at self_anchor are ordinary local reads and confer no core knowledge.
No fixed age invalidation, TTL, identity tracking, notification, or research
allocation/heuristic machinery is introduced.

## 6. Declared fixtures and both-seat schedule designs

These tables are static contract schedules, **not executed match evidence**.
They use §2's profile/default parameters, chunk size 2 and tick-1 starting seat
A. `K`, `R`, `F` below identify roles; suffixes count that role's eligible own
callbacks. Reverse seats by moving the whole starter/fixture entrant definition,
including its direct start and parameters; do not exchange only agent names.
Starters start at 0; fixture core/anchor starts at 91. Core windows 0..7 and
91..98 do not overlap. Both fixtures have one main process, reach128/share1.

### 6.1 Keeper / encroaching fixture, predicate `keeper-K1`

`v6_encroaching_opponent`: own callback F1 MOVE(-64), anchor91→27; F2
WRITE(1,0x45); every subsequent callback READ own_core_base91. Target1 is an
explicit fixture constant, not a derived hidden starter location. The fixture
writes once, never writes anchor0 and never captures all eight core cells.
At27, target1 and own core91 are within reach. At0, Keeper can read all its core,
scan27 and write27. Defensive WRITE27 may suppress fixture callbacks that tick;
this requires no fixture notification and does not alter its completed F1/F2.

| Seats / boundary | Required schedule consequence |
| --- | --- |
| K=A, F=B; tick1 first chunks | K1 READ0, K2 READ1; F1 MOVE(-64), F2 WRITE1. K2 sampled before damage, so K3 cannot infer it. |
| K=A; remaining tick1 callbacks | K3 READ2, K4 SENSE27, K5 receives27 and WRITE27; K6 READ3, K7 READ4, K8 SENSE27. F is suppressed after K5. |
| K=A; tick2 / tick3 | Tick2 K9 receives27/WRITE27, K10 READ5, K11 READ6, K12 SENSE27, K13 WRITE27, K14 READ7, K15 READ0, K16 SENSE27. Tick3 K17 WRITE27, K18 READ1 samples F ownership, K19 receives that READ and repairs1. |
| F=A, K=B; tick1 | F1 MOVE(-64), F2 WRITE1; K1 READ0, K2 READ1; F3/F4 READ91; K3 receives F ownership and repairs1, K4 SENSE27; F5/F6 READ91; K5 receives27 and WRITE27, then K6 READ2, K7 READ3, K8 SENSE27. |

Neither role is eliminated by this schedule: F's core91..98 is untouched and
only cell1 of K's core is contested/repaired. Completion is not a victory test.
The validator SHALL independently reconstruct relocation, sampled/delivered
READ owner and SENSE address, legal writes, costs and both surviving prefixes.

### 6.2 Reacquirer / relocating fixture, predicate `reacquirer-R1`

`v6_relocating_opponent`: F1–F3 READ own_core_base91; F4 MOVE(+64),
anchor91→155; F5 onward READ own_core_base91. Relocation depends exclusively on
F's own eligible callback count, never a scan or knowledge of another entrant.
READ91 remains legal at155 (distance64). The fixture never writes or captures.

| Seats | Tick1 role callback order up to response |
| --- | --- |
| R=A, F=B | R1/R2, F1/F2, R3/R4, F3/F4, R5/R6, F5/F6, R7/R8, remaining F offers may be suppressed |
| F=A, R=B | F1/F2, R1/R2, F3/F4, R3/R4, F5/F6, R5/R6, F7/F8, R7/R8 |

For both seats the R actions/observations SHALL be:

| Own callback | Evidence and decision |
| --- | --- |
| R1 | No contact; SENSE91 samples91; spend one action, result withheld. |
| R2 | Receive91; READ0 (first of three paid wait actions). |
| R3 / R4 | READ0 twice; no newer scan evidence; F4 relocation happens after receipt and before R5 in either seat. |
| R5 | SENSE91; window64..118 is now empty, cost1. |
| R6 | Applied empty receipt establishes old address absent in that sample; MOVE(+64), anchor0→64. |
| R7 | SENSE155, center distance91 within reach128; sample155 remains pending. |
| R8 | Receive155; legal WRITE155 (distance91); a new anonymous-contact response. |

WRITE155 does not touch F's core91..98; any suppression occurs after relocation
and the required receipts. No enemy elimination prevents the sequence.
Omniscient reconstruction alone verifies that the fixture moved91→155.
Entrant-facing history never says “the same opponent moved/reacquired”.

## 7. Orchestration, provenance and explicit scenario verification

Reuse NativeMatchService, revision capture, canonical parameter resolution,
pair binding, cost/receipt reconstruction and every-tick world reconciliation.
Use a small explicit product scenario selection at orchestration time, with
three trusted validator choices: unchanged Scout, keeper-K1 and reacquirer-R1.
No narrative sidecar field, arbitrary file path or entrant display/name alone
may select a trusted validator. The two new validators SHALL live beside the
common reconstruction and consume immutable reconstructed facts, approved
inputs, role mapping and independently verified captured source revisions.

Before awarding scenario success, compare both captured full-tree digests with
the reviewed bundled revisions at the implementation candidate, verify capture
completeness and initial/final loaded Python-subset fingerprints, and reconcile
the ordered entrants/starts/parameters with reset/header/result. Materialize the
actual future revision digests at implementation review; do not invent them now.
Edited copies may yield consistent ordinary playback but do not inherit a
bundled-scenario badge. A reviewed source audit plus trace witnesses establishes
the bounded policy lesson; artifacts alone cannot prove arbitrary Python intent.

Proposed schema-safe choice: retain demo.json v1 only for its existing common
provenance/input/source/artifact envelope. Preserve the Scout-specific seven-event
`teaching_exchange` meanings, existing Scout evaluator and recorded evidence.
For the new scenarios omit that optional block and use `status: "unverified"`;
never use existing Scout success fields to assert Keeper/Reacquirer success.
Existing v1 artifact and pair verification may succeed while Scout teaching
verification does not. A separate in-memory scenario result and qualification
Markdown record SHALL report the new predicate findings and evidence points.
Do not route them through `verify_demonstration` as if it verified the new lesson.
No new persisted schema, field, enum, overloaded status or scenario assertion is
approved. If implementation cannot keep these semantics, STOP for schema/version
review before changing wire contracts. Product UI SHALL not imply that v1
`unverified` means the separately tested new scenario completed.

Record separately: artifact consistency, world/cost/receipt reconstruction,
source-capture validity, scenario completion, and entrant-view availability.
Valid incomplete pairs remain viewable; they cannot earn scenario completion.
Negative cases SHALL include a valid pair lacking repair/reacquisition, false
success assertion, wrong archetype/revision, wrong role/input/parameters,
interrupted prefix, drift, corrupt binding and optional-sidecar-only failure.

Each completed teaching run SHALL retain replay, trace, result, common sidecar,
executed source snapshots, full-tree and loaded fingerprints, raw SHA-256 values,
engine commit/dirty diff or source manifest, build/Python/dependency identity,
resolved Config, seed, starts, ordered roles and parameters. Engine/build identity
and scenario findings may be recorded in the qualification Markdown; do not add
wire fields to make the record convenient. Hashes bind the actual evidence;
unsigned local sidecars do not prove protection from malicious filesystem edits.

Outputs SHALL use fresh dedicated product roots such as
`runs/v6_alpha_m2/<campaign>/<scenario>/<seat>/<repeat>/`; apply existing
containment checks, reject research paths/IDs, escapes and private inputs.
Use complete runs to terminal condition or the declared limit, not just a clipped
trace witness. Repeat each new pairing twice per seat on each platform: eight
bounded new teaching runs per platform, four in M2-2 and four in M2-3; reuse those
retained runs in M2-5 when source/inputs remain identical. Re-run only for drift or
a concrete coverage gap. Keep Scout characterization in the regression selection.
Compare same-build canonical logical world/observations/actions/terminal results,
excluding only declared `wall_time_ms` and non-gameplay completion timestamps or
diagnostic path text; hash each raw file independently. Cross-platform comparison
uses equivalent captured inputs and logical facts. Preserve binary artifacts;
do not promise LF/CRLF or cross-engine byte equality.

## 8. Symmetric delivered views and bounded layout work

Reuse SensingCursor and immutable SensingView; SensingPresentation SHALL select
explicit entrant A, entrant B or None for omniscience. No second projection
system. The renderer SHALL receive only the selected filtered view; raw world,
other entrant receipts, hidden moves/cores/results and operator findings cannot
enter its entrant payload. Both roles SHALL get identical boundary guarantees.

Use one compact selector labeled `A | B | Omni`. Reuse V/P perspective cycling
as Omni→A→B→Omni, with existing direct-selection conventions extended to all
three choices. Show full selected labels “Agent A — delivered information”,
“Agent B — delivered information” and “Omniscient — full world state”.
Map existing number-key indices explicitly: 1→Omni, 2→A, 3→B. Preserve existing
pause/step, Home/End, speed, seek and help controls.

Tests SHALL assert A and B payloads, contact/read histories and ages at
observation, action and tick end, before receipt, after movement, backward seek,
scrub, restart and Omni→entrant transitions. Rebuild only the permitted prefix;
clear prior screen/history selection/scroll state when changing entrants. Each
entrant uses its own local callback rows/ordinals, step counts and pacing; no
opponent rows, blank steps or suppressed-opportunity pauses. Hidden-opponent
divergence with identical permitted history SHALL leave that entrant's payload
and presentation navigation unchanged. Gate terminal result on the permitted
recorded-end boundary; do not expose future outcome via navigation metadata.

Missing/corrupt trace or result/replay binding SHALL disable both delivered views
and exchange stepping, and retain labeled “Omniscient — replay only” canonical
viewing. Continue suppressing passive perspective, Director and Fight Night in
alpha1 fallback. An invalid optional sidecar alone SHALL leave a valid ordinary
pair's delivered views available and withhold only dependent verification.

Fix the accepted M1 history/footer overlap by a dedicated wrapped disclaimer row
outside the scrollable history and controls. At 900x650, 1000x700 and 1100x750,
with long READ/scan histories in A/B/Omni and terminal state, assert rectangles
and actual rendered text remain nonoverlapping/unclipped. Essential receipt,
sample-age, cost, phase and control information SHALL remain readable. Exercise
mouse/keyboard switching, scrolling, resize, pause/step, reverse seek and close.
Record Windows/Linux font resolution and rendered evidence; offscreen frames
are supplemental to affected native interactions.

## 9. Observable human-comprehension gate

Provide two short static scenario cards keyed to the reviewed policy revision,
parameters and fixture inputs. Cards explain the policy rule and tasks, not
hidden current state. Keep cards outside the entrant scene; no generic motive
engine or automatic strategy annotations. Any later in-view rule text requires
a separate contract with revision/action checks and mismatch withholding.

After M2-5, an actual human SHALL use the Python-launched Designer to find each
new agent, create/edit/validate/run a copy under explicit alpha1 in both seats,
open its associated replay and reopen it via Replay History. For each of the
four agent/seat tasks, the participant SHALL point to the relevant delivered
evidence, distinguish sampling from receipt, name the competing paid action
opportunity, and explain the observed decision under the card's stated rule:

- Keeper: READ ownership justifies a repair attempt; anonymous SENSE supports
  a perimeter WRITE attempt without proving damage, identity or a hit.
- Reacquirer: a delivered applied rescan omits an old address; a paid MOVE/new
  SENSE finds a new anonymous contact without proving it is the same process.

The ordinary authored match proves the workflow, not a guaranteed teaching
sequence under arbitrary seeded placement. For the explanation task, use that
match only if it exhibits the required witnesses; otherwise open the corresponding
verified §6 fixture pair for that agent/seat. Record both result/artifact IDs and
the transition between them. Do not manufacture demo provenance for the ordinary
run or imply that its editable personal copy has the bundled-scenario badge.

Record participant role/name or declared anonymous ID, platform, exact build,
artifacts/revisions/parameters/seat, task answers, completion, assistance and
misunderstandings. Declare assistance in advance: scenario card, existing help,
then one facilitator explanation followed by the participant's own restatement.
Record answers before/after assistance. Failure to explain either core lesson in
either seat after that help blocks the teaching objective and M2 closure.
Cosmetic issues may be deferred with lead disposition; core misunderstanding
cannot be counted as a pass. One developer participant supplies only a formative
baseline. Automated traces/GUI scripts are technical evidence, not a human study.
M2-6 does not require duplicate human tasks on both platforms; technical native
platform gates do. It makes no general-population comprehension/enjoyment claim.

## 10. Compatibility, qualification and research isolation

Preserve all old starter bytes/digests, safe install/refresh/customization,
`STARTER_AGENT_NAMES[-1] == "v5_dual_team"`, Scout's native sequence/verifier,
historical replay/result/trace readers, retired-execution refusal and stable-V4
equivalence/goldens/defaults. Include the baseline's published capture regression
modules [engine](../../engine/tests/test_v6_alpha_sensing_playback_core_capture.py)
and [client](../../client/tests/test_v6_alpha_sensing_core_capture.py); do not
replace them with the divergent local fixes.

Use the adopted [Disposition 03](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)
and final M1 acceptance partitions. Historical 329 pins (293 implementation/36
qualification) bind `b948540aa9ef34134ff7e3c633c3acfc9f97da96`, not evolved
product bytes. Preserve manifests, original qualified sources, fixture/golden
bytes and existing historical results; verify pins against that preserved
boundary. Historical 72-node qualification remains separately 71 ordinary plus
one entropy-prohibiting-plugin process; no automatic rerun or research campaign.

Before M2-5, enumerate the exact current product complement and compatibility
supplement from the retained [Windows](evidence/m1_6a_windows/README.md) and
[Linux](evidence/m1_6b_linux/README.md) manifests, plus M2 additions and current
capture tests; explicitly account for every new/removed node and marker. Retain
exact selections, commands, JUnit/logs, skips and exclusions with approved reasons.
Unexpected exclusions/source-bound failures require disposition, not ad hoc
deselection. Do not import research helpers into product entrypoints. Existing
authorized synthetic historical/compatibility characterization remains distinct
from a product demo and scientific execution.

Run focused engine/client/Designer tests before appropriate broader product and
compatibility checks, then `ruff check .` and separate
`mypy engine/src/battle_engine` / `mypy client/src/battle_client`. Use the repo's
verified Python; on Windows the original repo environment may be invoked by
explicit executable path. Before pytest, create a fresh disposable basetemp and
cache outside runs/evidence, record absolute paths and confirm no retained data
or reparse traversal. This checkout lacks some original-worktree test-protection
commits: do not assume their guard exists, import them, or launch default-temp
pytest on retained evidence. Do not change pytest.ini to evade an ACL failure.
GUI cases stay marked gui and are invoked explicitly, including root tests/.

Qualify affected engine and full authoring/replay workflows independently on
Windows AMD64 native Qt/SDL and Linux X11/Xvfb Qt xcb/SDL x11. Record OS, Python,
dependencies, display/focus setup, font and effective inputs; retain original
failed attempts and any activation assistance. Screenshots/startup smoke alone
do not qualify controls. Required layout/control coverage is §8; repeated new
scenarios are §7. Known Windows COM `0x8001010d` has unresolved root cause and
remains a qualified nonblocking observation unless new functional evidence
changes that disposition. Preserve the X11 focus prerequisite.

M1's missing complete published Windows replay/trace bodies still prevent its
direct raw-artifact platform comparison; M2 SHALL retain its own complete bodies.
Do not retroactively fill or rewrite M1 evidence. This bounded M2 campaign does
not qualify Wayland, other distributions, all Python3.10–3.14, installers,
frozen executables, packaging, accessibility or unrestricted release. History
seek remains forward reconstruction from the beginning when rewinding; no
performance/checkpoint redesign is included.

No E8/E9 harness/controller calls, private research inputs, entropy/seed-authority
operations, custody changes, resealing, G consumption or scientific execution.
The [project-direction record](V6_PROJECT_DIRECTION_DECISION_20261015.md) remains
in force: original E9 operationally blocked/execution LOCKED, successor work
deferred, Requirement C NOT ESTABLISHED. No new private inventory/preservation
audit is required or claimed by M2-1. Stop rather than alter seals to qualify the
current product tree. Bytefray 5.1 release and Bytefray-Spectator remain separate.

## 11. Acceptance criteria and milestone gates

All criteria below are proposed and **NOT EXECUTED** for M2. Design resolution
in Checkpoint B does not satisfy implementation or qualification acceptance.

| ID | Acceptance criterion / evidence needed |
| --- | --- |
| M2-AC01 | §3 valid capability blocks, malformed/unknown/duplicate rejection, explicit alpha1 success and distinct V4 pre-import/reset/artifact mismatch on all affected routes |
| M2-AC02 | §4 K1 priority/cadence/parameter/core-relative behavior, READ→repair and SENSE→defensive witnesses, seeded/wrap/both-seat and negative feedback cases |
| M2-AC03 | §5–6 R1 full positive→receipt→scheduled relocation→applied absent rescan→MOVE→new positive→response sequence in both seats, with no identity/notification inference |
| M2-AC04 | §2 data-source audit and trace assertions for both agents; no seed inference/hidden data; empty/refused/absent/delayed/terminal feedback and every action cost preserved |
| M2-AC05 | §7 separate consistency/reconstruction/capture/scenario/view verdicts; both trusted predicates, negatives and four repeat runs per new pairing/platform; Scout unchanged |
| M2-AC06 | §3 complete personal-copy/parameter/full-run/reopen/earlier-settings workflows for both starters; overwrite and range/type rejection; safe installation/refresh/customization |
| M2-AC07 | §8 symmetric A/B payload, timing/history/navigation/pacing/terminal/fallback and hidden-divergence checks |
| M2-AC08 | §8 usable text and controls at all three sizes, long histories, all views and both platform fonts, with retained native interaction evidence |
| M2-AC09 | §10 product/compatibility selections, V4/default/reader/retired/starter/capture checks; unchanged historical artifacts and pins verified at their proper baseline |
| M2-AC10 | §7/10 independent affected Windows/Linux execution, retained inputs/bodies/source/environment and bounded same-build/platform logical comparisons; failures retained |
| M2-AC11 | §9 actual human record for both new agents in both seats; each explanation goal met within declared help; limitations and misunderstandings retained |
| M2-AC12 | §1/10 exact source/contract provenance, safe temp/output roots, research isolation and unchanged authority; no publication/release claim |

| Milestone | Entry / dependencies | Deliverables and acceptance | Explicit stop conditions |
| --- | --- | --- | --- |
| M2-1 — Contract and acceptance preparation | Lead's documentation-only grant; Review02 and accepted M1 | This revised scope, finding matrix, both policy/schedule designs and Checkpoint B package; reference/consistency checks. Exit requires lead acceptance of scope and Checkpoint B; preparation alone grants no implementation. | Unavailable knowledge, unachievable schedule, unresolved copy path, required wire/mechanic/research change; stop after package for decision. |
| M2-2 — Watchful Keeper | Explicit acceptance of this scope and B plus specific M2-2 grant; §1 entry recheck | K1 starter, encroaching fixture, minimal common orchestration/provenance plus keeper-K1 validator, Keeper-only registry/digest/scaffold integration and tests. AC01/02/04/05/06/09/12 affected subset and Checkpoint B §4 gates must pass. | Hidden-state/timer substitute for feedback; source/schema drift; unsafe roots; M1 regression; broader work needed outside B boundary. Completion does not start M2-3. |
| M2-3 — Roaming Reacquirer | Accepted M2-2 slice and explicit next-slice grant; common verifier/copy foundation | R1 starter/fixture/validator and its registration/digest/copy tests; AC01/03/04/05/06 and affected compatibility/isolation pass, both-seat sequence demonstrated. | Notification/identity/TTL assumption, opponent eliminated before sequence, unreachable search schedule, new wire meaning or research heuristic. |
| M2-4 — Replay and usability | Accepted agent slices and explicit grant; existing cursor/presentation boundary | A/B/Omni adapter/control, footer/history separation, collective ruleset description and two scenario cards; AC07/08 focused checks plus retained authoring/Scout regressions pass. | Hidden state/pacing leak, renderer raw-world entrant dependency, spectator redesign or generic explanation framework. |
| M2-5 — Technical and platform qualification | Accepted code slices, explicit campaign grant, frozen candidate/source/input/selection manifest and safe roots | AC01–10/12 technical dispositions, approved product/compatibility partitions, integrity evidence and affected native Windows/Linux workflows; no missing required platform gate. | Semantic regression, mutated historical evidence, unknown exclusions, source/input drift, missing source/artifact bodies or unusable controls. |
| M2-6 — Human evaluation and closure | Accepted M2-5 evidence, explicit human-evaluation grant, real participant and declared assistance | AC11 four task records, bounded corrective work separately authorized if needed, final AC dispositions and lead closure review. | Either lesson unexplained after help, open technical/platform gates or required scope expansion; no closure by automation alone. |

Closure, staging, commit, merge, push, release and unrestricted promotion each
remain separate decisions. No gate here authorizes E9 or successor activity.
