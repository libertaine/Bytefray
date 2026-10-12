# Bytefray V5 Alpha 1 — Phase 1: Corrective UX Cleanup

Date: 2026-09-12. Branch `v5-research`. Starting HEAD
`7201feaba40a4162b6ed0c895b8ef04a538c0ffa` (clean working tree at start).
Final HEAD unchanged (nothing committed this phase per instruction); working
tree carries the changes below, uncommitted.

Scope: a focused corrective pass on the six first-user UX issues found while
testing the packaged Windows V5 Alpha 1 build. No gameplay, simulation,
ruleset semantics, replay data format, tournament architecture, or agent
package format change is included.

## 1. Ruleset default correction

**Root cause.** `app/services/ruleset_options.py` defines the Designer's
offered-Ruleset tuples (`SIMPLE_RULESET_OPTIONS`, `DESIGNER_RULESET_OPTIONS`,
`EVALUATION_RULESET_OPTIONS`), each listing `bytefray-rules-2` first — a
deliberate, still-correct ordering for a different purpose (it mirrors the
engine's own `OMITTED_RULESET_CANDIDATES` compatibility-preference order, used
by `best_designer_ruleset_for_agents`/`sync_ruleset_choices_for_metadata` to
repair an *incompatible* selection). `app/widgets/ruleset_combo.py`'s
`populate_ruleset_combo()` populated a `QComboBox` from that order and never
called `setCurrentIndex` explicitly, so Qt's own "item 0" default applied —
conflating "compatibility-repair preference order" with "fresh-session
default" were two different concerns that happened to share one list. Simple,
Advanced, and Development all populate through this same function, so all
three silently opened on `bytefray-rules-2` before any agent was known.

This was already a known, named gap:
`docs/research/v5/V5_ALPHA1_CONSOLIDATION_AND_PLAN.md`'s task list item 3,
"UI Ruleset Synchronization: Simplify ruleset selection in Designer and CLI
to default cleanly to stable V4", and
`docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md`
already documents `bytefray-rules-4` as "V5 ordinary API-v2 default." No
persisted user Ruleset preference exists anywhere in the Designer (`QSettings`
is not used for this) — there was nothing to preserve.

**Canonical default chosen.** `bytefray-rules-4` (`BYTEFRAY_RULESET_V4_ID`) —
the permanent, non-alpha process-agent identity, gameplay-identical to the
frozen alpha2 contract, and the identity an omitted `--ruleset` already
resolves an Agent API v2 roster to (`resolve_omitted_ruleset_for_agents`,
`OMITTED_RULESET_CANDIDATES`). V5's own starter catalog additions
(`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`,
`v5_scout_striker`) are all Agent API v2 (`declare_processes`), confirming
this is the intended "current V5 experience," not `bytefray-rules-2`.

**Fix.** Added `DEFAULT_DESIGNER_RULESET_ID = BYTEFRAY_RULESET_V4_ID` to
`ruleset_options.py` as the single source of truth, and gave
`populate_ruleset_combo()` a `default_ruleset_id` parameter (defaulting to
that constant) that explicitly selects it after populating, falling back to
item 0 only if a narrower `options` tuple omits it. The compatibility-repair
*order* (`DESIGNER_RULESET_OPTIONS` etc.) is untouched — this only changes
which item is selected before any real agent is known. Development's and
Evaluation's own compatibility-repair passes (`sync_ruleset_choices_for_
metadata`) are unaffected: an empty/no-agent metadata list is vacuously
"compatible" with anything, so they simply keep whatever `populate_ruleset_
combo` set, and once a real agent is known they resolve exactly as before.

**Regression coverage.**
`engine/tests/test_designer_ruleset_options.py::test_designer_default_ruleset_is_stable_v4_not_v2`
(headless, runs in the normal `python -m pytest`) pins the constant's value
and that it is present in every offered-options tuple.
`tests/test_v5_alpha1_phase1_corrective_cleanup.py` adds GUI-level pins for
Simple, Advanced, Development, and the full `AgentDesigner` window agreeing
on `bytefray-rules-4` before any agent selection.

## 2. Replay terminal winner presentation

Added an always-on (not opt-in, unlike Fight Night) terminal-outcome banner
to `battle_client`'s Pygame replay renderer:

- `client/src/battle_client/hud_layout.py`: `format_replay_terminal_banner`
  (pure text: `"<NAME> WINS"` or `"DRAW"`, from `ReplaySession.winner` — the
  same already-authoritative field `format_terminal_state_line`/Fight Night's
  result card read, never recomputed) and `terminal_banner_rect` (pure
  geometry: a shallow band across the top of the arena viewport, skipped
  entirely below a minimum viewport height).
- `client/src/battle_client/renderers/pygame_renderer.py`:
  `PygameRenderer._draw_terminal_banner`, called every `_redraw` right after
  the top band. Gated on `session.result is not None and session.at_end` —
  `at_end` is the session's own live cursor-vs-final-tick check, so scrubbing
  away hides the banner and returning to the end restores it with no cached
  state. Rendered with a new larger `banner_font` (24pt vs. the HUD's
  13-14pt), falling back to `hud_font` if a test double never set it, in a
  semi-transparent bordered band that leaves the rest of the arena visible.

Deliberately independent of the existing Fight Night system (opt-in, timed,
depends on a `SpectatorDerivation` not always available for group matches):
this is the always-on, straightforward presentation the phase asked for.

**Tests.** `client/tests/test_hud_layout.py` (text/geometry, headless).
`client/tests/test_pygame_renderer.py`: a scrub-away-and-back test proving
the banner appears only at the final recorded tick and a draw-from-canonical-
data test, both against a real `MatchResult`-bearing replay built with
`write_replay`.

## 3. Numeric parameter range guidance

Audited Arena Size, Ticks, Survival/Kill/Territory Weight, Territory Bucket
Size (Advanced Match Setup) and Ticks (Evaluation dialog) against the actual
engine constraints (`process_runtime.py`'s
`if config.instr_per_tick <= 0 or config.arena_size <= 1 or max_ticks <= 0:
raise ValueError(...)` is the authoritative boundary check; the CLI's own
`argparse` flags for these carry no `type`-level bound at all).

- **Hard constraints surfaced:** Arena Size already correctly stated its true
  engine minimum ("`> 1` cell") in its tooltip — left unchanged. Ticks'
  tooltip now states the engine's real minimum (`>= 1`) explicitly, which it
  previously omitted entirely.
- **No established maximum — disclosed, not invented:** none of
  Ticks/Survival Weight/Kill Weight/Territory Weight/Territory Bucket Size
  have an engine- or schema-level maximum. Their existing GUI ceilings
  (pre-dating this phase) are now honestly labeled in their tooltips as
  practical UI bounds ("GUI limit: X–Y … not a gameplay rule"), not
  restated as if they were engine policy. No numeric range (`setRange`
  call) was changed — only the explanatory text. Evaluation's `Ticks` field
  had no tooltip at all before this phase; it now states the same honest
  minimum-only constraint.
- **Deliberately left alone:** the Random Seed field's range is already
  documented in `AdvancedPanel.randomize_seed`'s own docstring as
  self-referential ("the field's own range is the source of truth for what
  is legal"), a considered existing design this phase did not touch.
  Evaluation's `Workers` spin box (subprocess concurrency, not a gameplay
  parameter) was left as-is.

**Tests.** `tests/test_advanced_panel_ux_labels.py::
test_advanced_panel_numeric_tooltips_disclose_gui_limits_honestly` and
`tests/test_agent_evaluation_dialog.py::
test_evaluation_dialog_ticks_tooltip_states_its_range_honestly`. The
pre-existing `test_advanced_panel_numeric_ranges_match_engine_defaults` (pins
every `minimum()`/`maximum()`/`value()` triple) was left unmodified and still
passes, confirming no bound values changed.

## 4. Evaluation History empty-state explanation

`app/views/evaluation_history.py`'s `EvaluationHistoryDialog.refresh()`
previously showed only `"No evaluations found. Run \"Evaluate…\" from the
Agent Development tab first."` on an empty listing. Replaced with
`_EMPTY_HISTORY_EXPLANATION`, a short paragraph stating what an evaluation is
(runs one agent, optionally against a baseline, through many opponents/seeds),
that results accumulate here automatically for review/comparison (win rate,
survival, captures, behavior), that none have run yet, and the existing
canonical action that creates the first one (`Agent Development` tab's
`"Evaluate…"` button — confirmed to be the real, currently-wired action, not
invented). No new persistence, workflow, or navigation was added; the
populated-history view (list/detail/cells/compare/revision) is untouched.

**Tests.**
`tests/test_agent_evaluation_history_dialog.py::test_history_dialog_shows_friendly_message_when_no_evaluations`
updated for the new text; a new
`test_history_dialog_empty_state_explains_what_an_evaluation_is_and_how_to_start`
pins every required element (what/why/none-yet/how-to-start).

## 5. "Open Last Output Folder" clarification

Traced `AgentDesigner._on_open_output_folder`'s actual behavior: it opens
`self._tournament_output` if any tournament has run this session — set once
by `_on_tournament` and **never reset**, so it outranks a *later* single
match's output folder, not merely "whichever is more recent" — else
`self._result_path.parent` (the last single match's folder, set by both
Simple and Advanced on every run), else `data_root / "runs"` before either
has run.

Least-invasive fix per the phase's own guidance: kept the action's name and
wiring unchanged (`Tools > Open Last Output Folder`, same handler), added
`tools.setToolTipsVisible(True)` to the Tools menu (Qt menus show no tooltip
by default), and gave the stored `self.openOutputFolderAction` a tooltip that
states the real fallback chain precisely, including the tournament-output-
persists-over-a-later-match nuance — never claiming it "contains
tournament/evaluation/replay output" in general, which the implementation
does not guarantee.

**Tests.**
`tests/test_v5_alpha1_phase1_corrective_cleanup.py::test_open_last_output_folder_tooltip_matches_actual_fallback_behavior`.

## 6. Agent Params regression verification

Primarily verification, per the phase task: `tests/test_phase4_advanced_
multi_agent_roster.py` (roster add/remove, stale-state clearing, order
preservation into `RunConfig`), `tests/test_v5_alpha1_phase_e_designer_ux.py`
(parameter-edit preservation across Ruleset/agent changes), and
`tests/test_agent_combo_runtime_labels.py` already provide the coverage the
phase asked for (two-agent sync, adding a third agent, removing/changing
entrants, schema-driven descriptions). All pass unmodified in behavior (only
the Ruleset-default-dependent setup lines described under "Files changed"
below were touched, to keep these tests' actual subject — roster mechanics,
not Ruleset defaults — pinned against an explicit Ruleset rather than an
implicit one). No defect was found; Agent Params itself was not touched.

## Files changed

Source: `app/services/ruleset_options.py`, `app/widgets/ruleset_combo.py`,
`app/views/advanced.py`, `app/views/evaluation.py`,
`app/views/evaluation_history.py`, `app/agent_designer.py`,
`client/src/battle_client/hud_layout.py`,
`client/src/battle_client/renderers/pygame_renderer.py`.

Tests: `engine/tests/test_designer_ruleset_options.py`,
`client/tests/test_hud_layout.py`, `client/tests/test_pygame_renderer.py`,
`tests/test_v5_alpha1_phase1_corrective_cleanup.py` (new),
`tests/test_advanced_panel_ux_labels.py`,
`tests/test_agent_combo_runtime_labels.py`,
`tests/test_agent_designer_lifecycle.py`,
`tests/test_agent_designer_presentation.py`,
`tests/test_agent_development_panel.py`,
`tests/test_agent_evaluation_dialog.py`,
`tests/test_agent_evaluation_dialog_presets.py`,
`tests/test_agent_evaluation_history_dialog.py`,
`tests/test_phase4_advanced_multi_agent_roster.py`.

Every test file besides the new one was touched only to either (a) add
coverage for a Phase 1 item, or (b) pin an existing Ruleset-v1-only/API-v1
agent scenario against an *explicit* Ruleset selection instead of an implicit
one that is no longer `bytefray-rules-2` — never to change what the test was
actually verifying.

## Test results

- Focused (per-item) suites: all passed during development; see individual
  sections above.
- Full GUI-marked suite: `python -m pytest tests/ client/tests/ -m gui` —
  **450 passed** (final run), 0 failed.
- Canonical full suite: `python -m pytest` — **3620 passed, 21 skipped, 3
  deselected**, 0 failed (final run).
- Lint: `python -m ruff check .` — all checks passed.
- Type-check: `python -m mypy engine/src/battle_engine` and
  `python -m mypy client/src/battle_client` — both report no issues.
  `app/` is not part of either project mypy invocation (unchanged by this
  phase).

## Manual GUI smoke verification

This environment has no interactive display; verification was performed
through the same offscreen-Qt (`QT_QPA_PLATFORM=offscreen`) GUI test harness
the project's own `gui`-marked suite uses for every other Designer behavior,
which does construct real `PySide6` widgets and exercise real signal/slot
wiring — not a mock. It does **not** constitute a human looking at rendered
pixels. In particular, item 2's banner placement/legibility and item 5's
tooltip's actual on-hover appearance were checked structurally (text content,
geometry, `toolTipsVisible`), not visually. A sighted interactive pass on a
real Windows build is recommended before treating this phase as fully
qualified, per this repo's own "type checking and test suites verify code
correctness, not feature correctness" standard.

## Deferred / out of scope

Nothing from the explicit out-of-scope list (menu restructuring, Exit
command, Export Agent Package, Replay Browser relocation, Tournament
Results/History redesign, ruleset/agent behavior changes, new V5 ruleset
semantics, replay schema changes, evaluation architecture changes) was
touched. No concrete Agent Params defect was found requiring a fix under
item 6.

## Final state

HEAD unchanged (`7201feaba40a4162b6ed0c895b8ef04a538c0ffa`, branch
`v5-research`); nothing committed per instruction. Working tree carries the
20 files listed above (19 modified, 1 new, all tracked/untracked as
expected) and no other changes.
