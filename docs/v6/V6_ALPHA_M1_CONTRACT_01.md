# Bytefray V6 — Alpha M1 Contract 01

2026-10-09, America/Indianapolis. **Contract proposal; documentation only.
No implementation, match execution or publication authorized.**

The current lead instruction adopts the feature direction in the
[alpha scope proposal](../research/v6/V6_ALPHA_SCOPE_PROPOSAL_01.md) as the
product-planning baseline. It does not amend that proposal's historical bytes
or [administrative Disposition 11](../research/v6/V6_E9_V2_FINDING_DISPOSITION_11.md).
This contract recommends one bounded **M1 — Verified Sensing Exchange**.
All new identity, capability and presentation choices below remain proposals.

## A. Approved alpha scope

The alpha emphasizes experimental explicit sensing, complete bounded matches,
three teaching agents, parameter-first authoring, understandable decision
feedback, perspective-correct replay, readable pacing, and Windows/Linux.
Adaptive payoff superiority is not an acceptance requirement. E9 is deferred;
Requirement C remains **NOT ESTABLISHED**.

M1 delivers one actual engine-run teaching match, its result/replay/trace, and
a viewer that pauses and steps through an incomplete-information → SENSE →
receipt → legal subsequent action exchange. One writable starter and one
teaching opponent suffice for M1. The other two authoring choices belong to
later alpha integration. No tournament/evaluation redesign, visual language,
new scoring system, research controller, cinematic layer or E9 execution.

## B. Existing architecture and reusable components

Read against the current [architecture](../../ARCHITECTURE.md), not historical
release descriptions. Product matches use the API-v2 process controller; the
retained VM instruction interpreter and Kernel are not alternative match paths.

| Existing module, relative to repository root | Reuse and bounded delta |
| --- | --- |
| `engine/src/battle_engine/process_runtime.py` | Reuse scheduling, quotas, movement, READ/WRITE, disruption, capture and existing SENSE implementation. No second simulator. |
| `engine/src/battle_engine/agent_api.py`, `agent_worker.py` | Reuse immutable context/observation, SENSE enum and worker transport. Runtime API v2 remains unchanged for this proposal. |
| `engine/src/battle_engine/match_service.py`, `placement.py` | Reuse NativeMatchService, seeded placement, canonical identity, artifact finalization and worker supervision. Add the new product identity/capability guard; no new MatchRequest mechanic overrides. |
| `engine/src/battle_engine/rules.py`, `ruleset_policy.py` | Add one independent literal policy and identity registration after approval; retain all stable/research policies and omitted-rule defaults. |
| `engine/src/battle_engine/replay.py`, `telemetry.py`, `result_model.py`, `replay_integrity.py` | Reuse world serialization, result association and raw-byte digest checks unchanged. |
| `engine/src/battle_engine/agent_trace.py` | Reuse trace v2 and E8 optional sensing fields unchanged, including absent/null/empty distinctions. |
| `engine/src/battle_engine/spectator_derivation.py` | Reuse `verify_pair` and existing world/trace consistency checks. Current derivation handles READ/WRITE/MOVE but produces no SENSE exchange; it is insufficient by itself. |
| `engine/src/battle_engine/spectator_perspective.py` | Retain the existing passive perspective unchanged. Its projection reads passive visibility and READ feedback, not sensing receipts. Do not treat an empty passive set as an empty active scan. |
| `client/src/battle_client/session.py`, `player.py`, `analysis.py` | Reuse canonical tick reconstruction, playback controls and existing analysis. Add a parallel callback cursor; do not change ReplaySession into an agent executor. |
| `client/src/battle_client/perspective.py`, `renderers/pygame_renderer.py`, `cli.py` | Reuse perspective selection/lifecycle, viewer and launch route; route this explicit new identity to the proposed sensing adapter. |
| `engine/src/battle_engine/agent_parameters.py`, `agent_scaffold.py`, `agent_validation.py`, `agent_test.py`, `starters.py` | Reuse parameter parsing, personal-copy creation, validation/test flow and safe starter installation. Add mechanic-aware preflight and one M1 teaching template. |
| `app/widgets/agent_parameters.py`, `ruleset_combo.py`; `app/views/development.py`; `app/services/ruleset_options.py`, `agent_workflows.py`, `engine_commands.py`, `designer_workflows.py` | Reuse parameter controls, subprocess orchestration and result/stale-run handling; add explicit experimental selection and matching diagnostics. |
| `engine/src/battle_engine/agent_revisions.py`, `launchers.py`, `paths.py` | Reuse source revisions, external replay launch and resource/data-root separation. |

E8 already supplies the entire paid sensing operation, callback reflection,
worker parity and trace fields. The authoritative mechanic references are
[PR8 revision 5 §§2.1–2.3, 10, 13](../research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md)
and the current controller. Frozen E8 family search/verification algorithms,
seed protocols, matrices, analysis and E9 allocation controllers are not
product dependencies. Missing product work is identity/capability integration,
receipt-aware knowledge projection, sub-tick presentation and teaching content.

## C. Proposed experimental ruleset identity

**Recommend `bytefray-rules-6-alpha1`.** A distinct identity is necessary:
paid active sensing changes gameplay relative to stable v4, and a public
experiment has a different selection/persistence identity from frozen T8.
Never alias it to `bytefray-rules-6-research-sensing-active-w27` or mutate T8.

Propose independently stated gameplay fields matching T8: Python/API v2;
chunked scheduler, chunk size 2, rotating start, forward passes;
round-robin processes; seeded cores; `core_base` initial anchors;
`fixed_64` movement with literal displacement; capture hold 1;
whole-tick disruption (`disruption_slot_limit=None`); `sensing_mode="active"`;
window half-width 27. T8's `detection_radius=32` is retained as inert context
metadata, not an extra passive channel. Core size 8, D=1, READ/WRITE and
terminal resolution follow [Ruleset v4](../RULES_V4.md).

The **M1 run profile**, separately from Ruleset identity, fixes two entrants,
arena 512, action budget Q=8, limit 1,000 ticks, normal seeded placement and
no scheduler overrides. A direct fixture may supply starts using the existing
start inputs. No slot1 denial, mirrored passes, multi-tick capture,
before-core anchors, movement scaling or configurable sensing mode is imported.
These defaults come from PR8's primary condition, not a claim of optimal play.

Offer an explicit Designer/Development option **“V6 alpha1 — Experimental
sensing”** and explicit CLI `--ruleset bytefray-rules-6-alpha1`. Preserve
the stable v4 initial/default selection and omitted-rule behavior. A sensing
starter prompts explicit selection; it must not silently change the Ruleset.
Replay title and result presentation carry the experimental label and exact
recorded identity. Research identities remain outside product selectors.

Classify the new identity in a separate **public experimental** lifecycle set,
outside `PUBLIC_STABLE_RULESET_IDS` and `ACTIVE_RESEARCH_RULESET_IDS`.
The existing E8 policy-inventory tests assume those are the only active sets;
their current assertions cannot pass after public active sensing is registered.
K4 requires explicit disposition of those inventory expectations, while
preserving their original frozen revisions and all mechanic/golden evidence.

### Capability proposal (A3)

Retain API v2 callbacks and existing wire shapes. Add a separately versioned,
optional manifest block, proposed exact form:

```yaml
capabilities:
  version: 1
  required: [sense]
```

`required` is a unique list of known capability names; v1 initially recognizes
only `sense`. Unknown versions/names, malformed lists and duplicate entries
fail validation. Absent block means no extra required capability, preserving
old manifests. Policy-owned available capabilities expose `sense` only for
active sensing; use the same predicate in engine, validate/test and Designer.
Capability mismatch fails **before reset/import of agent code and before
match artifacts**. All new sensing starters declare it and check
`context.sensing_window` before use. Existing research compatibility gates
and frozen research manifests keep their established behavior.

An undeclared agent that later returns SENSE under v4 still forfeits under the
existing invalid-action contract; declaration is compatibility metadata, not
a Python sandbox or proof about arbitrary code. A declared sensing agent is
not selectable under v4. Existing v2 READ/WRITE/MOVE agents can run under the
new identity but receive no passive contacts there; explain this behavioral
difference. Old executable identities are not revived; historical artifacts
retain their readers. Older installations reject the unknown new Ruleset.

### Seed information boundary — unresolved product decision

PR8 §13 explicitly requires A3 and product-level closure of seed reconstruction
before promotion. API-v2 context still exposes a deterministic seed/RNG, and
placement is reproducible; removing a displayed seed alone is not closure.
Arbitrary Python also has host access. No secrecy guarantee is established.

**Recommend a narrowly approved M1 teaching-only exception**, retaining API v2
and deterministic inputs while prohibiting seed/placement inference in the
reviewed demo agents. The viewer promises faithful *engine-delivered*
knowledge, not all knowledge a hostile Python agent can derive. This makes
M1 a local engineering demonstration, not unrestricted public promotion.
Lead decision K2 must expressly dispose of the standing prerequisite for this
bounded scope; approval of the alpha feature direction alone did not do so.
If the lead requires closure now, first specify the seed/context/placement
threat model and version any incompatible Agent API change. Do not improvise
a v3 interface or claim this contract already solves that problem.

## D. Exact sensing interaction

The following operation is proposed for the new identity by reusing PR8's
engine mechanics unchanged. It does not adopt E8 family strategy or findings.

| Boundary | Exact behavior |
| --- | --- |
| Before acting | Reset provides arena, limit, own identity, local RNG/seed, parameters and sensing half-width. Each callback provides own process anchor/reach/core and prior-action feedback. `visible_enemy_anchor_addresses=()` always. SENSE reveals no enemy identity/core; a prior legal READ can deliver a cell's value and last-writer owner ID. That ID does not identify a spatial contact. No enemy core field, live position list, score or unseen memory is delivered. |
| Request/legal form | `AgentAction(ActionKindV2.SENSE, operand=t)`; integer absolute target, no `value`. Booleans/nonintegers/missing operand/non-WRITE value fail existing action validation. Normalize `t % A`; legal iff circular distance to acting anchor ≤ declared reach. The *center* must be in reach; the ±27 window may extend beyond it. |
| Price | One executed callback consumes one process quota opportunity and increments entrant/process action counts, whether applied or out-of-reach. No retry/refund, bonus READ/MOVE/WRITE, byte change, territory, move or disruption. A malformed action charges its attempted callback and forfeits; it is not a free failed scan. |
| Order/sample | Execute immediately in normal scheduler order, after that callback's observation and before the next callback/action. Sample actual anchors then, not end-of-tick anchors. Earlier MOVE/WRITE effects count; later actions do not. Live enemy processes remain detectable while disrupted. |
| Result | Sorted unique addresses of every other live entrant's anchors at inclusive circular distance ≤27 from target; co-located anchors appear once. No identity, multiplicity, core, ownership or opponent notification. Applied empty result is `()`, serialized `[]`. |
| Delivery | Retain result for the same `(entrant_id, process_id)`. Its next eligible callback receives `previous_sense_anchors`, even later after suppression; `previous_action_applied` reflects application and READ feedback is None. Out-of-reach yields None/false. No later callback before elimination/limit means no delivery. Another process's callback does not fulfill the obligation. |
| Lifetime | The receipt is an instant historical sample, not continuing vision. It appears in that process's next observation only; a subsequent non-SENSE action replaces the feedback. Agent code may remember it indefinitely. No engine TTL, automatic refresh, global negative inference or sensing alert is added. |
| Next decision | Agent chooses one ordinary validated action using the delivered observation and its own stored state; recheck reach at its current anchor. Shared Python instance may copy received data between own processes, but sibling callbacks do not acquire an undelivered result. |

### M1 teaching witness

The future test/demo fixture uses existing direct-start inputs: A core/anchor
0, B core/anchor 91, arena 512, each one process with reach 128 and share 1,
Q=8. A receives the first chunk at tick 1; B initially stays at its anchor
by legally reading its own core. Use explicit product-development inputs;
no research family or corpus. The fixture is a disclosed teaching setup,
not a hidden competitive seed selection or production placement default.

| Step | Engine fact | A-perspective display |
| --- | --- | --- |
| Tick 1, A callback 1 observation | Own anchor 0/reach128/core0; no prior SENSE, no passive contacts. | Enemy contacts unknown. “Search window centered at 91” explains the starter's scheduled search rule; no enemy marker. |
| A action 1 | SENSE(91), in reach; quota used1; window64..118 samples `(91,)`; no world mutation. | Request ring and “1 action spent; result pending.” Do not show `(91,)` yet. |
| A callback 2 observation, same chunk | `previous_sense_anchors=(91,)`, previous action applied; sample tick1/action1. | Anonymous sampled contact91 appears. Receipt explicitly identifies sample and delivery points. |
| A action 2 | MOVE(+64), anchor0→64, action count2. | Applied own movement arrow; old contact remains a historical sample. |
| Later A callback/action | Remembered91 is27 from current64, so legal WRITE(91,value) is possible; ordinary scheduler/opponent actions intervene. | Requested/applied write and1-action cost. Do not claim a disruption hit, current enemy presence or core ownership without delivered evidence. |

The full native match runs to the existing authoritative terminal condition
or limit, with a real result. The fixture's exchange is required; winning or
demonstrating adaptive advantage is not. Add a separate boundary scenario in
tests where A first READs its own core, then SENSEs91 as its second action
in the chunk; B MOVEs+8 before A's next chunk. A's next callback still
receives91, while only omniscient view shows B's actual anchor99.

## E. Engine/artifact/replay responsibilities

**Authority:** replay4 supplies tick-boundary world bytes/ownership/processes,
progression and result; trace2 supplies ordered callback observations,
requested actions and applied outcomes. Use
[replay schema](../REPLAY_SCHEMA.md), [API-v2 trace](../specs/v4_api_v2_trace.md)
and PR8 §10 together; the older trace spec alone does not describe E8 fields.

No new replay/result/trace generation is needed for the proposed exchange.
Existing `ResetRecord.sensing_window`, `action.kind="sense"`,
`applied_result.sensed_anchors` and `observation.previous_sense_anchors`
already encode it. Preserve trace2's absent/null/empty semantics exactly:
non-SENSE outcomes omit sensed fields; applied empty is `[]`; ordinary
out-of-reach is explicit null; the next same-process callback reflects it
exactly once. Status distinguishes rejection from forfeit/exception.
Suppressed opportunities produce no decision record. Never synthesize them.

Proposed additions are isolated interfaces, not edits to persisted research
derivation/perspective schemas:

- `engine/src/battle_engine/agent_capabilities.py`: parse/version the manifest
  extension and provide compatibility checks used by existing callers.
- `engine/src/battle_engine/sensing_playback.py`: validate a bound pair and
  derive immutable product exchange facts with `tick`, global trace decision
  index, phase (`OBSERVATION`, `ACTION`, `TICK_END`), actor/process,
  request/status/normalized address, cost, sample point, optional delivery
  point and audience. No sensing result enters an agent audience until receipt.
- `client/src/battle_client/sensing.py`: sensing knowledge projection and a
  steppable/seekable callback cursor over those validated facts. Pass a
  perspective-filtered view model to the renderer; no world-state fallback.
- `engine/src/battle_engine/sensing_demo.py`: bounded product demo orchestration
  through NativeMatchService and run-input capture, not a research harness.

For M1, a small **new** `demo.json` sidecar uses proposed schema
`bytefray.sensing_demo`, version1: exact Ruleset ID, effective Config/limit,
ordered entrants and effective starts, resolved parameters, complete agent
revision references/digests, engine revision/build identity, match/result IDs,
and replay/trace filenames with
raw SHA-256. It records deterministic inputs and binds the actual trace body;
it carries no invented decision motives. Reuse revision storage and atomic
JSON writing. Execute the captured complete teaching revision snapshot;
verify the full-tree digest against that snapshot and record capture
completeness. Compare its Python-subset fingerprint with the actual loaded
initial/final source fingerprints using the same fingerprint version.
Incomplete capture or drift cannot earn a reproducible/verified-demo badge;
retain the actual match artifacts and explain the failure. This is a versioned
new product record; core wire schemas and
existing result IDs remain unchanged. Binding/digests detect inconsistency,
not malicious forgery. Missing/invalid sidecar disables version-specific rule
explanations; missing/invalid trace disables entrant exchange playback.

Validate before presentation: result/replay association; trace footer identity
and raw replay digest; existing pair consistency; active reset/window and empty
passive visibility; legal target/cost; sampled anchors independently reconstructed
from tick-zero state plus ordered trace MOVE/WRITE/forfeit facts; and receipt
presence/value on the next same-process callback. Reconcile reconstructed
tick-end bytes, ownership, anchors and lifecycle with every canonical snapshot.
If costs/quotas cannot be verified for a supplied pairing, reject exchange
verification rather than label it verified. M1's single-process full-share
profile makes the cost witness explicit; later multi-process qualification
must cover redistribution and round-robin selection.

### Projection and seeking

Use `(tick, global decision index, phase)` order. The observation phase occurs
before that action; a receipt is available there, not at its earlier sample.
An applied SENSE creates a pending action explanation, not an instant entrant
contact. An applied READ's memory value/owner similarly enters knowledge only
at its later delivered feedback. Applied own moves/writes may be displayed as
recorded own action facts, without importing their hidden consequences.

Show contacts as **“sampled at …, received at …”**, never as live tracked enemies.
No fabricated certainty/confidence or arbitrary TTL. A later delivered scan
replaces the remembered occupancy claim inside that scan window as of its
sample point: positives add anonymous samples; previously seen addresses absent
there become “not present in newer sample.” Outside-window samples persist
with their age. Empty local scan establishes only that window's sample-time
absence. Preserve older samples in the inspectable history. Failed scans and
unobserved ticks do not erase knowledge. READ ownership does not identify a
spatial contact. The projection represents the union of delivered entrant
information, not the private variables of arbitrary agent code.

Backward seek/restart rebuilds only the prefix through the selected phase;
later receipts, opponent actions and future terminal facts cannot enter it.
Switching from omniscient back to entrant view cannot carry world state,
contacts, hidden event text, statistics or opponent decision reasons across.
In entrant view, enemy behavior is “unobserved” except actual delivered samples.
Roster identity is public; identity-to-contact mapping is not.

The global trace index is internal ordering metadata, not entrant-visible
knowledge. Entrant stepping exposes only that entrant's observation/action
phases and tick boundaries, with entrant-local ordinals. Hidden opponent
callbacks create no rows, counters, blank steps, variable pauses or tooltips;
otherwise their count/timing could disclose scheduling or disruption. Sample
and receipt labels use tick plus own process/local callback ordinal. Repeated
“unobserved opponent action” rows are prohibited. Omniscient mode may expose
the full sequence; switching back selects the corresponding permitted prefix.

Omniscient mode is clearly labeled **“Omniscient — full world state”** and may
show actual anchors/cores and actions. At sub-tick steps it uses validated
ordered world reconstruction, not the end-of-tick ReplaySession snapshot.
ReplaySession remains the unchanged tick cursor; the parallel exchange cursor
must agree at every TICK_END. Never interpolate a gameplay fact. If the pair
is absent/corrupt, retain labeled replay-only omniscient viewing, disable
exchange/perspective steps with a reason, and never show a success badge.

## F. Agent authoring and three teaching agents

Use existing **create personal copy → change parameters → validate for selected
Ruleset → run complete match → open matching replay → edit/repeat**. Validation
checks declared capabilities, parameter types/ranges, declarations and a legal
dry-run action; it does not certify all future behavior. Run the real match
with the displayed resolved parameters and separate result directory. Label
earlier results when source/settings change. Retain current timeout/subprocess
behavior; arbitrary Python is not sandboxed.

| Proposed starter | Learning purpose / legal behavior | Small parameters |
| --- | --- | --- |
| **Window Scout** (M1) | Periodic search windows, then bounded MOVE toward a received sample and optional in-reach WRITE/READ; distinguish anchor discovery from core confirmation. Single process, reach128/share1 for M1; own-relative search does not read seed/placement. Sense on callback1, use its receipt on callback2; subsequent search cadence yields to this pending receipt/action sequence. | Search interval in eligible callbacks (1..16, proposed default4); move step (1..64, default64). No-callback ticks do not increment cadence. |
| **Watchful Keeper** (later alpha) | Alternate READ/repair of own fixed core with infrequent legal scans; teach that sensing reveals anchors while READ inspects ownership. | Scan interval (1..32, default8); repair byte (0..255). |
| **Roaming Reacquirer** (later alpha) | Fixed cadence scans and moves; retain old samples, reacquire rather than assume they track moving enemies. No E9 adaptive allocation or research EVADE8 hit-inference policy. | Scan interval (1..16, default4); move step (1..64, default32). |

These parameter defaults are proposed teaching settings, not frozen research
values or competitive recommendations. All three use only legal actions,
normalize targets, recheck reach, declare `sense`, check context, and handle
empty/rejected/delayed results. M1's opponent can simply READ its own core;
it is a disclosed teaching fixture, not a fourth advertised alpha starter.

For known immutable teaching revisions, a panel may explain a documented rule
from the recorded observation and captured parameters (“scheduled search,”
“move toward received address”). Label this **starter rule explanation**,
validate that the expected action matches the trace, and withhold it on drift
or mismatch. Arbitrary agents receive facts only; do not infer their intent.

## G. Player-visible M1 experience

The player chooses the experimental sensing exercise, copies Window Scout,
changes a scan interval, validates and runs. A compact circular board, an
action list and a terminal panel show a complete match. Playback begins in
**“Agent A — delivered information”**, with own core/anchor and unknown enemy
space. Pause/step and speed controls remain familiar.

Stepping shows “Search centered at91;1 action spent; result pending.” The next
eligible observation shows “Sample received: anonymous anchor91,” including
sample/receipt times. The next action moves the scout64 cells. A later WRITE
is explained as applied at an in-reach address, without an invented hit.
If the opponent moved since sampling, the contact remains an aged sample.
In entrant view the opponent's current activity is explicitly unobserved;
the separately labeled omniscient view explains its actual actions.

Use rings for requests, a receipt symbol for delivery, arrows for actual MOVE,
cell marks for WRITE, and text for cost/status/age. Shapes and text carry the
meaning without color. Reveal no opponent position through tooltips, event
lists, cameras or totals. Pacing is presentation only; both slow and fast
playback step through the same ordered facts. Display the engine's recorded
termination/outcome when the viewer reaches the end.

## H. Implementation work breakdown (not authorized now)

| Task / order | Bounded work and exact owners | Boundary test before proceeding |
| --- | --- | --- |
| M1-1 | Resolve K1–K4; document new product Rule/API capability block and sidecar schemas. Add literal identity/policy and experimental lifecycle classification in `rules.py`/`ruleset_policy.py`; available capability query and `agent_capabilities.py`; guard `match_service.py`, `agents.py`, `agent_validation.py` and worker initialization routes. Apply only the approved current-inventory test disposition in K4. | Explicit dispatch/persistence identity, mismatch before code execution, unchanged stable default and T8 fields; malformed capability records fail closed. |
| M1-2 | Window Scout under `engine/src/battle_engine/data/starter_agents/v6_window_scout/`; registration/scaffold in `starters.py`/`agent_scaffold.py`; `sensing_demo.py` builds ordinary native requests, captures revisions/inputs and writes version1 sidecar. | Real native fixture yields request→receipt→MOVE and complete terminal output; parameter/source capture agrees; no seed inference or research imports. |
| M1-3 | `sensing_playback.py` consumes replay4/trace2 using existing binding/world validators, adds independent SENSE/result/delivery checks and ordered sub-tick world states. | Tampered sample, dropped/refused receipt, wrong trace digest, invalid cost and replay disagreement are rejected. |
| M1-4 | `client/sensing.py`, narrow integration in `client/perspective.py` and `player.py`; separate phase cursor and knowledge view model. | No pre-receipt contact, no future knowledge after seek, delayed/terminal delivery correct, tick-end agreement. |
| M1-5 | Experimental Development selection/run route in `app/services/ruleset_options.py`, `engine_commands.py`, `app/views/development.py`; viewer/CLI wiring in `client/cli.py` and `renderers/pygame_renderer.py`. Reuse existing parameter controls and result handoff. | Create/edit/validate/run/reopen flow, exact selected identity, pause/step UI, perspective label and fallback. No Qt execution engine. |
| M1-6 | Focused engine/client coverage followed by normal broader checks and Windows/Linux exercise. Record M1 acceptance evidence separately from this proposal. | Every M1 criterion below passes; platform gaps are reported, never implied passed. |

Keep new tests in focused `engine/tests/test_v6_alpha_m1_*.py` and
`client/tests/test_v6_alpha_sensing*.py`. Reuse existing test conventions and
extend existing entrypoint/Designer tests where appropriate. Do not amend
frozen E8/E9 golden files or re-bless a failing historical vector. Do not extend
evaluation methodology or tournament selection as a dependency of M1.

## I. Test and compatibility plan

These are future acceptance tests, **not test results from this document task**.

| ID | Concrete M1 acceptance criterion |
| --- | --- |
| AC1 legality | Integer normalization, wraparound, inclusive reach boundary and ±27 boundary pass; center one cell beyond reach rejects, consumes1 and yields null/false. Invalid kinds/operands/value forfeit with existing diagnostics. Stable v4 refuses SENSE. |
| AC2 price | Compare controller action counters/quota exhaustion to recorded decisions: SENSE/empty/rejected scan each uses1; no mutation, movement, territory or disruption from sensing. Single-process budget8 permits no ninth action. Trace on/off leaves gameplay identical. |
| AC3 availability | No passive contacts; exact sorted/deduplicated enemy sample including disrupted-but-live anchors, excluding own/dead processes. Test sample after an earlier MOVE and before a later MOVE. |
| AC4 delivery | Next same-process callback in chunk/later tick/after suppression receives exact result once; another process does not satisfy delivery; empty/refused/absent remain distinct. Elimination or limit before next callback creates no receipt. |
| AC5 knowledge | Before receipt, positive results and READ values remain unavailable; old samples remain historical after enemy movement; local empty scans do not clear other windows. No missing-callback “lost contact,” inferred contact identity/core, future result, or hidden event tooltip. Two executions differing only in undelivered opponent callbacks produce identical entrant rows, step counts and presentation pacing for the same permitted tick/observation/action prefix. |
| AC6 reconstruction | Native output passes result association, trace binding/body digest, sample re-derivation and each tick's world agreement. Mismatch, truncated trace, dropped field, wrong Ruleset/window, malformed order or altered sample refuses verified playback. Replay-only fallback is visibly limited. |
| AC7 client agreement | Headless cursor exposes exact request, observation receipt, MOVE and optional WRITE in file order. Every TICK_END agrees with ReplaySession. Pause and next-step reveal one phase at a time; reverse seek/restart and view switching reproduce the same prefix without leakage. |
| AC8 reproduction | For the deterministic M1 teaching revisions, the same engine build and captured Config/starts/order/Ruleset/agent bytes/parameters/input seed yield identical canonical logical world records, action/observation records and terminal result in repeated completed runs. Verify complete capture and initial/final source fingerprints; drift withholds the badge. Arbitrary editable Python using host time/filesystem is not certified deterministic. Exclude declared timing/diagnostic text; validate each raw binding individually. Cross-platform LF/CRLF digest equality is not required; move existing pairs as binary. |
| AC9 authoring | Validated personal copy runs and reopens; range/type errors and capability mismatch produce clear errors before execution. Changed parameter appears in reset/result/run record, and old output is labeled earlier revision. A successful dry run is not presented as full-match validation. |
| AC10 compatibility | Existing stable-v4 fixtures/IDs/defaults and historical readers pass unchanged; retired execution remains refused. Run `test_v4_historical_immutability.py`, `test_v4_stable_ruleset_equivalence.py`, `test_native_match_service.py`, `test_agent_validation.py`, `test_designer_ruleset_options.py`, existing replay/session/trace/perspective tests. E8 parent-byte and sensing/context/trace tests retain their pinned expectations. |
| AC11 research isolation | No M1 import/call of `tools/research/v6/e8` or `e9`, no private research paths/seeds, no operational authority/entropy/generation operations. New product output uses its own directory; E8/E9 instruments/manifests/evidence remain untouched and independently identifiable at their frozen revisions. |

After focused checks, run the ordinary headless suite using repo Python with a
fresh repo-local basetemp if Windows ACLs require it; `ruff check .`; separate
`mypy engine/src/battle_engine` and `mypy client/src/battle_client`.
`engine/tests/test_ruleset_v6_research_sensing_active.py` currently asserts
that active policies are exactly E8's two IDs (lines222–227), exhaustively
partitions policy identities into stable/research/retired (276–281), and
expects every non-E8 identity to refuse SENSE (434–451). New product tests
alone cannot make those assertions pass. Under K4, propose a separately
reviewed revision of **current product-inventory assertions** to include the
experimental lifecycle set and the explicitly approved active product ID;
retain original test/source bytes at the pinned historical baseline. Preserve
E8 field equality, parent bytes, scientific fixtures/results and mechanic
expectations. Any genuine shared-mechanic regression must be fixed. If that
inventory disposition is not authorized, M1 remains blocked; do not bypass
or silently exclude failing tests or claim the full suite passes.

**M1 now:** run focused headless native/worker/artifact/client acceptance and
deterministic repeated-run checks on Windows AMD64 and Linux, plus a display
exercise on Windows and Linux X11/Xvfb for launch, parameter edit, complete
match, replay reopen, pause/phase-step, both perspectives and clean close.
Mark display-dependent automated tests `gui`; a startup smoke alone does not
establish interaction. M1 acceptance requires exercised controls on both
platforms; documentation today asserts no such platform result.

**Later alpha-wide:** all three templates/pairings, multi-process capability
and quota UX, full supported Python3.10–3.14 matrix, broader board/seed/timing
cases, usability/accessibility/keyboard/reduced-motion checks, complete wheel
assets/clean installs, Windows installer/frozen executables and Linux packaging.
No M1 pass implies release readiness, balance, enjoyment or research payoff.

## J. Research isolation and baseline verification

Live local inspection: branch `v6-research`; HEAD and local upstream both
`b948540aa9ef34134ff7e3c633c3acfc9f97da96`; tracked and index diffs empty.
No live remote query or Git publication was needed. Existing untracked scope,
administrative records and independent-author/test directories were inspected
for inventory and preserved; local-only settings remain untouched.

Pre-draft read-only checks matched both Seal-08 manifest hashes and their
293 implementation + 36 qualification members (**329/329**), Disposition11's
exact JSON digest and all 8 source pins, all 43 checkpoint-candidate pins,
and exact membership/length/SHA-256 for the retained 1,384-file original private
namespace. Nine HOLD records remain preserved. A3/seed design issues concern
product behavior; no E9 operational assurance gate is imposed on M1.

Disposition11's current instruction history remains distinguishable: that
record permitted planning without adoption; the present instruction adopts
the planning direction. Neither authorizes code or alters scientific state.
E9 remains **OPERATIONALLY BLOCKED**, scientific execution **LOCKED**,
Requirement C **NOT ESTABLISHED**; original G remains consumed exactly once
under retained records. No new study, controller, authority event, timing
attempt or replacement generation. Off-machine evidence recovery remains
**NOT ESTABLISHED**, a separate outstanding preservation risk.

Future product source evolution must retain access to the original sealed
source revisions/pins; it cannot make an altered checkout the original
qualified E9 instrument. Do not edit seal manifests, historical authority,
consumed G or private evidence to accommodate product work. No blanket E9
resealing campaign is a prerequisite for this separate M1.

## K. Remaining decisions before coding

| Decision | Single recommended choice / approval needed |
| --- | --- |
| K1 identity/mechanics | Approve `bytefray-rules-6-alpha1`, the T8-equivalent explicit policy,512/Q8/1,000 M1 profile, API-v2 capability extension v1, explicit experimental selection and unchanged stable default. |
| K2 promotion/seed boundary | Explicitly authorize the narrow teaching-only M1 exception in C, with no unrestricted public promotion or seed-secrecy claim; retain the seed-closure issue for the later public-alpha contract. Alternatively require closure first, which needs a separate concrete API/threat-model decision before M1 coding. |
| K3 knowledge/artifacts/scope | Approve historical samples with no engine TTL, receipt-only projection, isolated phase cursor, unchanged replay4/trace2/result2, new demo sidecar v1 and Window Scout/one fixture opponent as the M1 authoring slice. Other two teaching agents are later alpha work. |
| K4 current inventory expectations | Approve a public-experimental lifecycle classification and narrowly version the three current-checkout E8 product-inventory assertions identified in I. Preserve original qualified bytes at the frozen baseline and all scientific/mechanic/golden checks. This is a product-surface disposition, not a research rerun or silent test exclusion. |

No approval of competitive optimality, research execution or Git publication
is sought. After these decisions, a separate instruction must authorize the
bounded M1 implementation. Parameter labels and graphical styling can be
routine implementation choices within the approved contract.

## L. Implementation readiness

**Independent review classification: BLOCKED ON CONTRACT DECISIONS.** K1–K4 are presented
as a concrete approval bundle; K2 and K4 are substantive unresolved promotion
and compatibility boundaries. No further experiment or research-grade
qualification campaign is requested. The
[independent M1 design review01](V6_ALPHA_M1_DESIGN_REVIEW_01.md) found the
revised milestone bounded and testable. Review corrections clarify READ
owner feedback, suppress hidden-opponent navigation cues, identify the
inventory-test conflict, bound determinism to teaching revisions and require
complete source capture. None authorizes coding.

Stop after contract and focused review. No source/test changes, staging,
commit, push, match run or scientific execution belongs to this task.
