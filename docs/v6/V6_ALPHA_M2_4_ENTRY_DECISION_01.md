# Bytefray V6 — M2-4 Replay and Usability Entry Decision Packet 01

2026-10-15, America/Indianapolis. **Read-only readiness review. M2-4 is NOT
AUTHORIZED; no M2-4 code, test, card or layout change has been made.**

**Recommendation: READY FOR AUTHORIZATION WITH CLARIFICATIONS.** The grant
should resolve the four readings in §3 (Q1 and Q2 are required) and confirm
the boundary in §4. M2-3 publication should come first (§8).

## 1. Basis

Governing contract: [Scope Revision 03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md) §8
(symmetric delivered views and bounded layout work), §9 (scenario cards; the
human gate itself is M2-6), §10 (compatibility and qualification) and the §11
M2-4 milestone row:

> A/B/Omni adapter/control, footer/history separation, collective ruleset
> description and two scenario cards; AC07/08 focused checks plus retained
> authoring/Scout regressions pass. Stop on hidden state/pacing leak, renderer
> raw-world entrant dependency, spectator redesign or generic explanation framework.

Design findings: F06 (symmetric views) and F10 (layout) in
[Checkpoint B 01](V6_ALPHA_M2_CHECKPOINT_B_01.md#2-finding-by-finding-resolution-matrix),
both resolved in the contract with implementation pending M2-4/5. Carried
conditions: M2-2 C2 (overlapping sample-marker labels, assigned to M2-4 with a
before/after check in
[M2-2 Closure 01 §7](V6_ALPHA_M2_2_CLOSURE_01.md#7-conditions-carried-forward)),
the accepted M1 history/footer overlap
([M1 final acceptance](V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md)), and M2-3 L1 (seat-B
product view) from [M2-3 Closure 01 §6](V6_ALPHA_M2_3_CLOSURE_01.md#6-conditions-carried-forward).
Predecessors: M2-2 closed and published at `4fd89bb`; M2-3 accepted, with
publication pending.

Purpose: let a viewer replay any Keeper, Reacquirer or Scout lesson from
either entrant's delivered perspective, or omnisciently, with readable history,
controls and markers at the three contract sizes. M2-4 adds no mechanic,
ruleset, wire field, policy change or research heuristic.

## 2. Readiness findings (current code, read-only)

| Area | Finding |
| --- | --- |
| Adapter | [`SensingPresentation`](../../client/src/battle_client/sensing_presentation.py#L108) fixes `self._entrant = "A"`, and `switch(entrant: bool)` toggles only A ↔ Omni. The underlying `PhasePlaybackController.switch_view(entrant_id)` and `SensingCursor.switch_view` already accept `"A"`, `"B"` or `None`, and M2-3 tests use `SensingCursor(entrant_id="B")`. **No second projection system is needed;** the change is confined to the adapter's selection API |
| Selector and keys | [`sensing_renderer.py`](../../client/src/battle_client/renderers/sensing_renderer.py#L146) draws two fixed boxes, "2: Agent A — delivered information" and "1: Omniscient — full world state", with hard-coded mouse regions. V/P cycling toggles A ↔ Omni. [`dispatch_key`](../../client/src/battle_client/renderers/pygame_renderer.py#L806) already emits `select_perspective_index` 0–7 for keys 1–8, but the sensing renderer acts only on indices 0 and 1, so key 3 is ignored. §8 requires one compact `A \| B \| Omni` selector, V/P cycling Omni→A→B→Omni, and keys 1→Omni, 2→A, 3→B |
| CLI | [`cli.py`](../../client/src/battle_client/cli.py#L283) prints "Requested perspective unavailable; showing Agent A delivered information." for any Alpha 1 `--perspective` other than A, `broadcast` or `omniscient`, so `--perspective B` is refused today. The Designer and Development Test launch the viewer with `--trace` and no perspective (`app/agent_designer.py`, `app/services/engine_commands.py`) |
| History/footer layout | `draw_entrant` places the wrapped history column from y=140 down to `height − 155`. Footer help is at `height − 58`/`− 34`, the timeline at `height − 90`, terminal text at `height − 120`, and Omni operator lines at `height − 175..− 135`. All use fixed pixel offsets and a 15-pt Consolas request with a 19-px line pitch, with no font-metric checks. The Linux font produced the accepted M1 overlap. §8 requires a dedicated wrapped disclaimer row outside the scrollable history and the controls |
| Marker labels (C2) | `draw_marker` draws every historical sample label as `sample <address>` at a fixed offset with no collision handling, which causes the terminal-state overlap in long replays. C2's acceptance check (no intersecting or clipped labels at all three sizes, with no delivered fact dropped from history) is fully specified |
| Renderer boundary | `draw_entrant(self, view)` accepts only a `SensingView`, and an existing test asserts that signature (`client/tests/test_v6_alpha_m1_5.py`). Omni operator verification lines are drawn only on the Omni branch. This boundary is reusable as is |
| Fallback | `load_sensing_presentation` already returns "Omniscient — replay only …" for a missing trace or invalid exchange evidence, and keeps the delivered view when only the optional sidecar is invalid. §8 requires both delivered views to share this behavior |
| Existing tests | `client/tests/test_v6_alpha_m1_5.py`, `test_v6_alpha_m1_5_adversarial.py`, `test_v6_alpha_sensing.py`, `test_v6_alpha_sensing_adversarial.py`, `test_v6_alpha_sensing_core_capture.py` and `test_hud_layout.py` (the stable viewer). The published capture regression module must be retained (§10) |
| Fixed inputs available | Published M2-2 Keeper bodies and curated M2-3 Reacquirer bodies (both seats), plus the C2 Keeper Development Test replay `98edb90d…`, which is local and bound by hash in M2-2 Closure 01 §7. Together they give long A/B histories without new runs |

## 3. Clarifications the grant should resolve

- **Q1 — "Collective ruleset description" (required).** It is named only in the
  §11 milestone row and as "collective starter guidance" in Design Review 02.
  No normative text defines its content or location. Proposed reading: one
  short static description of `bytefray-rules-6-alpha1` shared by the three
  sensing starters (Scout, Keeper, Reacquirer). It would state SENSE cost,
  delayed anonymous receipts, no identity or tracking, and that Alpha 1 is
  explicit and experimental. It would appear once where Advanced/Development
  already offer explicit Alpha 1 selection, and would contain no per-match or
  per-agent dynamic text. If the lead intends a different location, such as
  viewer help, that changes the §4 boundary.
- **Q2 — Scenario-card form and location (required).** §9 requires two short
  static cards keyed to the reviewed policy revision, parameters and fixture
  inputs, kept outside the entrant scene. Proposed reading: two static Markdown
  cards under `docs/v6/cards/` (Keeper and Reacquirer), each citing the content
  digest, default parameters, fixture name and the `keeper-K1`/`reacquirer-R1`
  inputs, and stating the policy rule and the M2-6 tasks. In-product display
  would be limited to a link or help reference, with no in-view rule text,
  which §9 reserves for a separate contract.
- **Q3 — CLI perspective values.** Proposed: in the Alpha 1 branch only, accept
  `--perspective A`, `B` and `omniscient` (keeping `broadcast` as an Omni
  alias), and print a clear message for anything else. The stable-V4 spectator
  `PerspectiveManager` path is not changed.
- **Q4 — C2 ownership split.** Proposed: M2-4 implements the label-placement
  correction and an automated rectangle assertion over the fixed C2 replay at
  900x650, 1000x700 and 1100x750 in A, B and Omni. It also retains offscreen
  before/after frames. Native before/after frames on both platforms remain an
  M2-5 obligation, as C2 already states.

## 4. Proposed authorized file boundary (smallest useful slice)

| Path | Permitted change |
| --- | --- |
| `client/src/battle_client/sensing_presentation.py` | Explicit entrant selection (`"A"`, `"B"`, `None`); selected labels; state reset on switch; shared fallback; no new projection |
| `client/src/battle_client/renderers/sensing_renderer.py` | `A \| B \| Omni` selector and mouse regions; V/P cycle and 1/2/3 mapping; dedicated disclaimer row; history/footer/timeline/terminal separation computed from font metrics; non-overlapping marker-label placement (C2) |
| `client/src/battle_client/cli.py` | Alpha 1 `--perspective` acceptance per Q3 only |
| `client/tests/test_v6_alpha_m1_5.py`, `client/tests/test_v6_alpha_m1_5_adversarial.py` | Update the A/Omni-only expectations to A/B/Omni without weakening boundary or fallback assertions |
| `client/tests/test_v6_alpha_m2_4_views.py` (new) | Symmetric payload, navigation, pacing, fallback, hidden-divergence and layout-rectangle tests |
| Q1 location, expected `app/views/development.py` and/or the Designer Advanced help | One static collective description, per Q1 |
| `docs/v6/cards/` (new, per Q2) | Two static scenario cards |
| `tests/test_v6_alpha_m1_5_designer.py` | Only if Q1 adds Designer text that existing GUI assertions read |
| `docs/v6/V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md` (new) | Implementation and focused-qualification record |

Excluded: everything under `engine/` (including `sensing_playback.py`, the
starters, fixtures and verifiers); `client/src/battle_client/sensing.py` and
`player.py` unless a defect is found (stop condition); the stable spectator
modules (`perspective.py`, `director.py`, `fight_night.py`, `hud_layout.py`,
`pygame_renderer.py` beyond reading `dispatch_key`); any demo-v1 schema or
persisted field; Scout, Keeper and Reacquirer sources and digests; research
paths; packaging; README/ROADMAP beyond status lines. Needing any other path is
a stop condition (§7), not a silent widening.

## 5. Acceptance criteria

| ID | Criterion (contract reference) |
| --- | --- |
| R4-01 | M2-AC07: `SensingPresentation` selects A, B or None explicitly; the renderer receives only the selected filtered view; labels are exactly "Agent A — delivered information", "Agent B — delivered information" and "Omniscient — full world state" |
| R4-02 | M2-AC07: A and B payloads, contact/READ histories and ages are asserted at observation, action and tick end; before receipt; after movement; and across backward seek, scrub, restart and Omni→entrant transitions, using the Keeper and Reacquirer bodies in both seats |
| R4-03 | M2-AC07: each entrant has its own callback rows and ordinals, step counts and pacing; there are no opponent rows, blank steps or suppressed-opportunity pauses; switching entrants clears screen, history-selection and scroll state |
| R4-04 | M2-AC07: hidden-opponent divergence with identical permitted history leaves the payload and navigation unchanged; the terminal result is gated at the permitted recorded-end boundary; navigation metadata reveals no future outcome |
| R4-05 | M2-AC07: a missing or corrupt trace, result or replay binding disables both delivered views and exchange stepping, labeled "Omniscient — replay only"; an invalid optional sidecar alone keeps both delivered views; passive perspective, Director and Fight Night stay suppressed in the Alpha 1 fallback |
| R4-06 | M2-AC08 (focused): at 900x650, 1000x700 and 1100x750, with long histories in A, B and Omni and at terminal state, the disclaimer, history, footer, timeline, terminal and selector rectangles and the rendered text do not overlap and are not clipped; receipt, sample-age, cost, phase and control information stays readable |
| R4-07 | C2: no two marker labels intersect and none escapes the arena panel, at all three sizes, for the fixed C2 replay in A, B and Omni; no delivered fact is dropped from history and no undelivered information is added; offscreen before/after frames retained |
| R4-08 | Controls: V/P cycle Omni→A→B→Omni; keys 1/2/3 select Omni/A/B; mouse selector; pause/step, Home/End, speed, seek, scroll, resize and help preserved; CLI `--perspective` per Q3 |
| R4-09 | §9 and Q1/Q2: two static cards keyed to the reviewed revisions and parameters, outside the entrant scene; one static collective description; no generic explanation framework or in-view rule text |
| R4-10 | Regression: retained M1-5 boundary tests, capture regression modules, Scout characterization, Keeper/Reacquirer modules and the authoring GUI nodes pass; Ruff and separate engine/client mypy pass; 329 pins unchanged |
| R4-11 | Lead review of the M2-4 record; no automatic M2-5 entry |

**Focused regression plan.** Use fresh pytest roots outside `runs/`. Run the
new M2-4 client module, then the updated M1-5 modules, the remaining sensing
client modules and `test_hud_layout.py`. Next run the retained 23-module
focused selection and explicit `-m gui` Designer nodes, then Ruff and both mypy
runs. Native Windows and Linux interaction, font and frame evidence for
M2-AC08 belongs to M2-5. M2-4 may record supplementary native observations
without claiming that gate.

## 6. Compatibility requirements

Keep every starter byte and digest, the catalog order and terminal
`v5_dual_team`, the stable-V4 default, historical readers and retired refusal,
and the published capture regression modules. The stable spectator viewer,
perspective projection, Director and Fight Night must not change. M1 sensing
semantics, Scout's seven-event `teaching_exchange` meaning, and the Keeper and
Reacquirer verifiers stay as accepted. Demo-v1 status `unverified` must not be
presented as scenario completion.

## 7. Known risks and stop conditions

| Risk | Handling |
| --- | --- |
| Seat-B view needs a cursor or reconstruction change | **STOP**; record the defect and request a scope decision (`sensing.py`/`player.py` are excluded) |
| Any hidden-state, pacing or future-outcome leak into an entrant view | **STOP** (§11 stop condition) |
| Renderer needs raw world or session data for an entrant view | **STOP** (§11 stop condition) |
| Layout correction requires spectator redesign or a shared stable-viewer layout change | **STOP**; `hud_layout.py` is excluded |
| Q1/Q2 answered with in-view rule text or a generic explanation framework | **STOP**; §9 requires a separate contract |
| Font-metric differences make rectangle assertions platform-specific | Assert on measured rendered text rectangles, not constants; retain both platforms' font resolution in M2-5 |
| C1 End-key non-response recurs during any native check | Treat as a possible product defect; retain the delivered-key witness and exit status |
| Rewind reconstruction cost on long histories | Existing accepted limitation; use bounded waits; no checkpoint redesign |
| Windows COM `0x8001010d` / X11 focus prerequisite | Existing qualified observations; retain diagnostics |

## 8. Entry prerequisites

1. Explicit lead grant for M2-4 that names the §4 boundary and resolves Q1 and
   Q2 (and confirms or amends Q3 and Q4).
2. Recommended: publish the M2-3 closure first
   ([Closure 01 §9](V6_ALPHA_M2_3_CLOSURE_01.md#9-publication-manifest-and-proposal)),
   so M2-4 starts from a clean, published baseline with separately reviewable
   slices.
3. Entry recheck as in M2-2/M2-3: HEAD, branch and index; live remote by
   read-only query; the 329 pins; fresh safe roots.
4. Fixed inputs available locally: the published Keeper and curated
   Reacquirer bodies, and the C2 replay `98edb90d…`.

No E8/E9 activity, sealed-evidence change, M1 semantic change or agent-policy
change is part of this entry. Original E9 remains operationally blocked with
execution LOCKED, and Requirement C remains NOT ESTABLISHED.
