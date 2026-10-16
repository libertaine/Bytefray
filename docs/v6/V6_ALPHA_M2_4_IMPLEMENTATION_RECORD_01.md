# Bytefray V6 — M2-4 Replay and Usability implementation record 01

2026-10-15, America/Indianapolis. **Technical-acceptance package for project-lead
review. Recommendation: PASS WITH CONDITIONS (§12).**

M2-3 was published as two fast-forward commits. M2-4 then added a symmetric
`A | B | Omni` replay selector, a font-measured layout with a dedicated
disclaimer row, collision-free arena labels (M2-2 C2), and one static Alpha 1
guide with two scenario cards. The guide is shown in replay Help and in a
Designer sensing-guide window. All changes are inside the entry-review file
boundary and remain unstaged and uncommitted. M2-5 and M2-6 were not started.

Qualification found and fixed three platform-font layout defects, all exposed
by Linux font metrics (§9.2). It also found and removed a redundant load-time
rebuild that this change had introduced (§9.3). The retained first-pass failures are kept.

## 1. Authority and entry

The project lead approved: M2-3 technical closure (PASS WITH CONDITIONS); the
two-commit publication proposal; the curated 32-file M2-3 evidence package;
M2-4 implementation after successful publication; and explicit Q1/Q2
resolutions. M2-5 and M2-6 remain unauthorized. This record transcribes that
grant. It carries no signature and no new research authority.

| Question | Resolution used |
| --- | --- |
| Q1 — collective ruleset description | **Lead resolution.** One concise, shared, informational Alpha 1 explanation, reachable from existing help and information surfaces. It covers paid sensing, sample versus delayed receipt, anonymous locations and age, competing action opportunities, and delivered versus omniscient information. No normative rules, wire fields, motives or strategy annotations |
| Q2 — scenario cards | **Lead resolution.** Exactly two short static cards (Watchful Keeper, Roaming Reacquirer), one shared definition per reviewed policy and fixture configuration, shown in a lightweight Designer help surface and in replay Help, outside the arena scene |
| Q3 — CLI perspective values | Not amended by the grant, so implemented as the entry review proposed: the Alpha 1 branch accepts `A`, `B`, `omniscient` and `broadcast` |
| Q4 — C2 ownership | Not amended, so implemented as proposed: M2-4 corrects labels and adds automated rectangle assertions plus offscreen before/after frames. Native before/after frames on both platforms stay an M2-5 obligation (supplementary native frames are retained here, §8) |

**Boundary check for Q1/Q2.** The entry review proposed static Markdown cards
under `docs/v6/cards/` with only a link from the product. The lead's
resolution instead puts the cards in two product surfaces with one shared
definition. That definition must be importable by both the Designer (`app/`)
and the viewer (`battle_client`). It is placed in
`client/src/battle_client/sensing_presentation.py`, a boundary file whose
module already holds the presentation primitives. No new path was needed and no
Markdown card copy was created, since a second copy would break "one shared
definition". **The lead should confirm this placement** (§12, condition D1).
The alternative is a dedicated module, which would need a targeted scope review
because it is a new path.

## 2. M2-3 publication (Phases A–B)

| Check | Result |
| --- | --- |
| Manifest | `runs/v6_alpha_m2/m2_3_closure_20261015/publication_manifest_v02.json`, SHA-256 `f48b83007fcde0eab05796e93de65d28260bf15541e9653bbf8458fca9c58d95` (matches the approved value); 56 paths (2 + 54), 3,086,036 bytes |
| Fresh pre-publication validation | `closure_validate.py v03`: 27/27 gates PASS, including 329 pins, both evidence indexes, the 237-link check and dirty set = manifest. Its regenerated `publication_manifest_v03.json` is byte-identical to v02 |
| Independent recheck | Every manifest path matched by bytes and SHA-256; the only git-ignored paths were the four curated `.jsonl` bodies; no private or local absolute paths in the package (one generic `/mnt/d/…` WSL mention in a failure ledger) |
| Commit 1 | `0ead52a5147b985c157c3004c4f5abd6e329e6b5` `docs(v6): correct M2-2 evidence line-ending description`, parent `4fd89bb…`, exactly the two M2-2 erratum files, blobs equal to the manifest |
| Commit 2 | `e7c0f9de1f08f7c6494c36f2b4cc77850fad912f` `feat(v6-alpha1): complete M2-3 Roaming Reacquirer`, parent `0ead52a…`, exactly 54 paths. The 50 ordinary paths were staged from the manifest list; the four `.jsonl` bodies were named individually in one `git add -f --` command. No directory was force-added and `.gitignore` is unchanged |
| Two-commit tree | `git diff 4fd89bb e7c0f9d` = the 56 manifest paths; every blob matches the manifest; no overlap between commits |
| `git diff --cached --check` (commit 2) | Flags only CR bytes in the nine pure-CRLF evidence bodies (traces, comparison/relocation/scenario reports, source freezes, preservation report, R3-07 diff). These are the raw bytes the package's `* -text` attribute preserves, as the package README states |
| Push | Remote re-queried immediately before the push: `refs/heads/v6-research` = `4fd89bb…`. Normal fast-forward `4fd89bb..e7c0f9d`, no force |
| After fetch | `origin/v6-research` = `e7c0f9d…` (also by `ls-remote`); ahead/behind 0/0; all 56 published blobs match the manifest |
| Divergent local branch | `v6-research` still at `2fc3c82e115650b515a4efab39afb172b62535ed`; not merged or rebased |

The commit subjects follow the lead's suggested wording, not the manifest's
working titles (`docs(v6-m2): …`, `… milestone`). The manifest binds paths and
bytes, not titles. A first attempt at commit 1 passed its message incorrectly
from PowerShell. Git rejected it and created no commit, and the staged set was
unchanged. The message was then supplied from a file.

## 3. M2-4 implementation manifest

Baseline: published `e7c0f9d…`. The candidate is uncommitted working-tree
content (source freeze 05, `runs/v6_alpha_m2/m2_4_20261015/source_freeze_05.json`).

| Path | Bytes | Raw SHA-256 | Change |
| --- | ---: | --- | --- |
| `client/src/battle_client/sensing_presentation.py` | 19926 | `445f677b63571eddf068724189688f56b71f3a5fb044ba918bafdd165b319bf2` | Explicit A/B/None selection, cycle, labels; symmetric fallback; static guide and cards |
| `client/src/battle_client/renderers/sensing_renderer.py` | 25062 | `1526b5003ea75716c47853508af625b218b74dc2e7a52132bd33679a0e8e40ab` | Selector, keys and mouse; measured layout; disclaimer row; Help page; C2 label placement |
| `client/src/battle_client/cli.py` | 17133 | `b37c41c922c639397d0cfdaf97183ba9af9b08bbffde1dc71aac24dfe7b77667` | Q3: Alpha 1 accepts `--perspective B` (one line) |
| `app/views/development.py` | 42720 | `dbb4c9ac19850968449c5832a5cb4c37b65d76edc08d87b85a3c8b2ed6c22e40` | Q1/Q2: "V6 alpha1 sensing guide…" button and read-only dialog |
| `client/tests/test_v6_alpha_m2_4_views.py` (new) | 29218 | `15a3c210a111127bf478e47101c454d44a42d9ef2f1707c70da0ec8a20d2e212` | 37 nodes (31 headless, 6 `gui`) |
| `client/tests/test_v6_alpha_m1_5.py` | 10537 | `46b9e7737e41cc2e3ea1ad4956809ee3e507bd5df87f3635148ab31209ba0b50` | Timeline click uses the measured rectangle |
| `client/tests/test_v6_alpha_m1_5_adversarial.py` | 8441 | `08f52080edd766796eabcef74defb433182291bbc12dfdea8e2e4bdfd7d36c4b` | Scroll test at 900x650 with a 24-px bundled font so the history still overflows |
| `tests/test_v6_alpha_m1_5_designer.py` | 24969 | `b003347df64617cca2dc28f02d648f126fa6cb553c14dcb3c8ae6d299755d80d` | One `gui` node for the Designer guide |
| `docs/v6/V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md` (new) | — | — | This record (cannot contain its own hash) |

Unchanged, as audited by `preservation_m2_4.py` (all PASS): the whole `engine/`
tree (byte-identical to `e7c0f9d`); `sensing.py`, `player.py`, `session.py`,
`perspective.py`, `director.py`, `fight_night.py`, `hud_layout.py` and
`pygame_renderer.py`; README, ROADMAP, packaging and pytest configuration;
research and evidence paths; every starter digest; the catalog suffix
`…, v6_watchful_keeper, v6_roaming_reacquirer, v5_dual_team`. The 329
historical pins were verified at preserved `b948540…` with zero mismatches.
HEAD is `e7c0f9d…`, nothing is staged, and local `v6-research` is unchanged.

The existing M1-5 test edits only follow the new measured geometry. Neither
weakens a boundary or fallback assertion. The timeline click still requires the
recorded end. The scroll test still requires that the oldest scan and the READ
history are hidden before scrolling and reachable with the wheel.

## 4. Symmetric views (Scope 03 §8, M2-AC07)

**Adapter.** `SensingPresentation.select(entrant_id)` accepts `"A"`, `"B"` or
`None` and rebuilds the existing `SensingCursor` through
`PhasePlaybackController.switch_view`. There is no second projection system.
`selected` reports the choice. `cycle()` follows Omni→A→B→Omni. `switch(bool)`
is kept as a compatibility toggle between Omni and the last delivered entrant.
Labels are exactly "Agent A — delivered information", "Agent B — delivered
information" and "Omniscient — full world state".

**Renderer boundary.** `draw_entrant(self, view)` and `entrant_scene(view)`
keep their one-argument signatures, as the existing M1-5 test asserts. Operator
verification lines are drawn only in Omni, in the side column, labelled "not
delivered to either agent". Help and card text are drawn by `draw()`, never by
`draw_entrant`. The only new marker field, `sampled_callback`, is the entrant's
own callback ordinal from its own delivered contact. It orders map labels.

**Controls.** `dispatch_key` indices map as 0→Omni, 1→A, 2→B (keys 1/2/3). V/P
cycles. The selector shows `Perspective: A | B | Omni` with the current choice
filled, and the hint "keys 2 / 3 / 1". Clicking a segment selects it. Every
change resets scroll, scrubbing and the drawn history and markers. Pause/step,
Home/End, speed, seek, scroll, resize and Help are unchanged.

**Fallback.** A missing trace, a corrupt trace, or a wrong result or replay
binding still returns no presentation. The stable viewer then shows
"Omniscient — replay only … delivered perspectives disabled", and passive
perspective, Director and Fight Night stay cleared. Load now also builds seat
B's projection, so **a projection failure for either seat disables both delivered
views**. An invalid optional `demo.json` alone keeps both delivered views.

| Requirement | Evidence (all in `test_v6_alpha_m2_4_views.py` unless noted) |
| --- | --- |
| Explicit A/B/None, labels, cycle, keys | `test_selector_order_labels_and_number_key_mapping`, `test_explicit_selection_cycle_and_compatibility_toggle`, `test_selector_keys_cycle_mouse_and_state_reset` (`gui`) |
| No receipt or history crosses seats (both seats) | `test_no_receipt_or_history_crosses_seats[A,B]`: the non-sensing seat never shows a sample or contact, and its READs are only its own core |
| Receipt, age and history at observation, action and tick end; before receipt; after MOVE (both seats) | `test_receipt_age_and_history_at_observation_action_and_tick_end[A,B]`, including "1 action spent" and consecutive own callback ordinals |
| Backward seek, scrub, restart, Omni→entrant (both seats) | `test_backward_seek_scrub_restart_and_omni_transitions_rebuild_only_the_prefix[A,B]`: every revisited view equals the forward walk; Omni→entrant never lands later than the Omni tick; switching seats keeps no earlier receipts |
| Hidden-opponent divergence (both seats) | `test_hidden_opponent_divergence_keeps_payload_navigation_and_pacing[A,B]`: three different hidden opponent scripts give identical positions, identical scenes at every phase, identical play-through index, and a terminal result only at the recorded end |
| No blank steps or suppressed-opportunity pauses | `test_suppressed_opportunities_add_no_blank_steps_or_pauses` (one seat's core written every callback) |
| Identical delivered information presents identically | `test_reacquirer_seats_with_identical_delivered_information_present_identically`: the published Reacquirer seat-A body (A view) and seat-B body (B view) give 18 equal scenes through R8. The only difference is the delivered READ owner, which is each seat's own ID. No "same/moved/reacquired/identity" wording appears |
| Published bodies, both starters and seats | `test_published_bodies_keep_fixture_seat_free_of_starter_receipts[keeper/reacquirer × A/B]` |
| Fallback | `test_either_seat_projection_failure_disables_both_delivered_views[A,B]`, `test_required_binding_failures_disable_both_views_without_details[4]`, `test_invalid_optional_sidecar_keeps_both_delivered_views`; existing M1-5 fallback tests unchanged and passing |
| CLI Q3 | `test_cli_alpha_perspective_values[A,B,omniscient,broadcast,C]`; real SDL loop starting in B (`test_real_sdl_loop_initial_b_perspective_and_queued_switches`, `gui`) |

No hidden state, pacing leak or renderer raw-world dependency was found, so no
§11 stop condition was met. No cursor or reconstruction change was needed,
because `sensing.py` and `player.py` already supported `"B"`.

## 5. Layout and C2 (Scope 03 §8, M2-AC08 focused, M2-2 C2)

**Layout.** Each frame is stacked from the active font's measured row pitch (the
measured height of every glyph the viewer draws) and measured text widths:
title, phase, selector, content (arena caption and map beside the scrollable
history, or the Help page), a dedicated wrapped disclaimer row,
the terminal row, the timeline and the wrapped footer. The disclaimer ("Markers
are delivered facts only…; Historical samples stay at their recorded address;
they do not track opponents.") now sits outside the history and the controls.
This fixes the accepted M1 history/footer overlap. The Omni operator lines
moved from fixed bottom offsets into the side column. Assertions use measured
rendered rectangles, never constants.

**C2 labels.** Glyphs for every marker are drawn as before. Labels are then
placed request first, then historical samples newest first, each beside its
own marker. A label takes the first of eight adjacent positions that stays
inside the map and touches no placed label and no glyph. A label with no free
position is left off the map only, and a reserved strip shows "N more map
labels not shown; see history". The history list stays the complete delivered
record, and no marker, fact or text is added.

**Fixed C2 input.** `98edb90ddda6d5d28b3ff76431d6c1ed9e4b7f792b48144173408fc17d9305de`
(Keeper Development Test replay, `match_2b6f25a5…`, 200 ticks), with its retained
trace and result, at recorded end, through `layout_probe.py`. "Pairs" counts
intersecting map-label pairs.

| Run | Font | A 900 / 1000 / 1100 | B | Omni | Facts |
| --- | --- | --- | --- | --- | --- |
| Before, Windows (`before_windows`) | Consolas | 23 labels; **81 / 81 / 58 pairs**; 4 escape the map at each size; the under-map disclaimer runs into a history line at 1000 and 1100 | unavailable | — | 395 samples, 23 contacts |
| Before, Linux (`linux_before`, published `e7c0f9d` renderer) | DejaVu Sans Mono | **96 / 81 / 81 pairs**; 5 / 4 / 4 escape; disclaimer runs into history at 1000 and 1100 | unavailable | operator line clipped at 900; notice overlaps the terminal row at every size | 395, 23 |
| After, Windows (`after_windows_final_05`) | Consolas | 6 / 8 / 10 labelled, 17 / 15 / 13 counted as not shown; **0 pairs, 0 escapes, 0 on glyphs** | clean | 2 anchor labels, clean | 395, 23 (unchanged) |
| After, Linux (`linux_after_final_05`) | DejaVu Sans Mono | 6 / 6 / 8 labelled, 17 / 17 / 15 counted as not shown; **0 pairs, 0 escapes, 0 on glyphs** | clean | 2 anchor labels, clean | 395, 23 (unchanged) |

Every "after" frame also has zero overlapping text, zero clipped text, zero
intersecting layout regions and zero text outside its region. Both platforms'
`--assert` mode reports PASS. Frames, including Help pages at 900x650, are
retained. Native frames are in §8.

Automated tests cover the same properties without local evidence:
`test_long_history_layout_all_sizes_views_and_terminal_state` (published
Keeper/Reacquirer bodies; A, B and Omni; mid-match and terminal; three sizes;
three fonts) and `test_dense_sample_labels_never_intersect_and_history_keeps_every_fact`.
The second checks that labelled plus omitted labels equal contacts plus
requests, and that every contact is still listed in the history.

## 6. Q1/Q2 implementation and card provenance

**Shared definition.** `ALPHA1_SENSING_GUIDE` (Q1), `SCENARIO_CARDS` (Q2,
`ScenarioCard`, frozen) and `sensing_guide_lines()` in
`sensing_presentation.py`. They are module constants that never read a replay,
view or session, so neither surface can state current or hidden match state,
and no viewer selects, badges or verifies a card.

**Surfaces.** Replay Help (`?`) replaces the arena and history with a scrollable
Help page: controls, then the guide, then both cards. It is identical in A, B
and Omni (`test_help_page_shows_the_shared_cards_outside_the_arena_in_every_view`).
In the Designer, the Development tab has a "V6 alpha1 sensing guide…" button
beside the existing Alpha 1 workflow hint. It opens a non-modal read-only
dialog with exactly the same lines (`test_development_sensing_guide_shows_the_shared_static_cards`,
native on Windows and Linux X11).

**Q1 text (verbatim title and topics).** "V6 alpha1 experimental sensing:
reading these replays (informational summary)". It has five paragraphs: paid
active sensing; sample and delayed receipt; anonymous locations and
information age; competing action opportunities; delivered versus omniscient.
It closes with "This summary is informational. The Ruleset and the recorded
artifacts remain authoritative; stable Ruleset v4 stays the default and V6
alpha1 must be selected explicitly."

**Q2 cards.** Each card has these sections: reviewed inputs, policy rule,
evidence it receives, paid action alternative, what its observations do not
prove, what to look for, and a scope note. The scope note says a personal copy,
edited parameters or an ordinary seeded match can differ, and that opening a
replay does not verify the scenario.

| Card | Starter (content digest) | Defaults | Fixture (content digest) | Predicate / profile |
| --- | --- | --- | --- | --- |
| Watchful Keeper | `v6_watchful_keeper` `35b945ad…c8016e` | `scan_interval=4`, `perimeter_offset=27` | `v6_encroaching_opponent` `42763e70…f24456` | `keeper-K1`; bytefray-rules-6-alpha1, arena 512, 8 actions/tick, seed 0, 100 ticks |
| Roaming Reacquirer | `v6_roaming_reacquirer` `65866988…697f21` | `search_offset=91`, `move_step=64`, `rescan_wait=3` | `v6_relocating_opponent` `d5331833…9a6ddd` | `reacquirer-R1`; same profile |

**Provenance controls** (`test_exactly_two_static_cards_bound_to_reviewed_inputs`,
`test_cards_and_guide_cover_required_topics_without_state_or_verification_claims`,
`test_help_content_never_enters_the_entrant_payload`):

- Each starter digest equals `CURRENT_STARTER_DIGESTS` and the bundled
  `starter_content_digest`.
- Each fixture digest equals the bundled fixture.
- Defaults equal the manifest, in order.
- The profile, ruleset and entrant names equal the published `demo.json` of
  each scenario.
- Exactly two cards exist; the guide is static, deterministic and free of
  placeholders.
- No card text ever enters an entrant scene, in either seat.

A drifted starter or fixture therefore fails the suite rather than leaving a
stale card. The cards describe policy rules and lessons, never hidden state, and
add no wire field, persisted field, motive or strategy annotation.

## 7. Acceptance matrix (entry review §5)

| ID | Disposition | Evidence |
| --- | --- | --- |
| R4-01 (AC07) | **PASS** | §4: explicit selection; renderer gets only the selected view; exact labels |
| R4-02 (AC07) | **PASS** | §4 rows 2–4 and 7–8, both seats, Keeper and Reacquirer bodies |
| R4-03 (AC07) | **PASS** | Own ordinals, constant pacing, no opponent rows or blank steps; switching clears state |
| R4-04 (AC07) | **PASS** | Hidden divergence in both seats; terminal only at the recorded end |
| R4-05 (AC07) | **PASS** | Shared fallback including seat-specific failure; sidecar-only failure keeps both views; passive features stay cleared |
| R4-06 (AC08 focused) | **PASS** | §5: three sizes; A, B and Omni; mid-match and terminal; long histories; Consolas, DejaVu Sans Mono and bundled fonts |
| R4-07 (C2) | **PASS** | §5 table; automated tests; offscreen before/after frames on both platforms |
| R4-08 | **PASS** | Keys, cycle, mouse, pause/step, Home/End, speed, seek, scroll, Help, resize (offscreen, SDL loop and native, §8); CLI Q3 |
| R4-09 | **PASS**, placement for confirmation (D1) | §6 |
| R4-10 | **PASS** | §9 |
| R4-11 | **Pending** | This record, for lead review; no automatic M2-5 entry |

M2-AC07 is satisfied for the M2-4 slice. M2-AC08 is satisfied at the focused
M2-4 level only: its native both-platform interaction and font gate stays with
M2-5 (§10). No M2-wide criterion is closed.

## 8. Native replay observations (supplementary)

`native_viewer.py` launches the real viewer process on the C2 replay and drives
it with native input only: Win32 window messages on Windows, XTest via xdotool
with explicit `windowfocus` on X11. A passive observer records each drawn state,
the delivered key events and the measured label and text geometry. These are
technical observations, not the M2-5 gate and not a human result.

| Run | Result |
| --- | --- |
| `windows_native_01` | **Harness failure**, retained. The `.venv` `python.exe` is a launcher, so the viewer PID differed from the launched PID. The viewer had drawn A correctly |
| `windows_native_02` (freeze 02) | End, `3`/`1`/`2`, the V/P cycle (B→Omni→A) and selector clicks passed natively. Then **harness/display failure**, retained: after a smaller size, the window could not return to 1100 wide (client 1084), because this display is a portrait 1080x1920 screen. Sizes are now visited in descending order from the 1100x750 launch size |
| `linux_native_01` (freeze 02, WSLg X11, DejaVu Sans Mono) | **PASS.** First draw 60 s; End; keys; cycle; clicks; all nine terminal frames (A, B, Omni × three sizes) clean; wheel scroll; Help on/off (clean); Home, Right/Left, speed, timeline seek; Escape exit 0; 27 delivered key events; no observer errors |
| `linux_native_03` (freeze 04) | **PASS**, same sequence and results as `linux_native_01`; first draw 60 s; nine clean terminal frames; Help on/off; exit 0 |
| `windows_native_03` (freeze 04, no concurrent load) | **PASS**: first draw 70.6 s; End; `3`/`1`/`2`; V/P cycle; selector clicks; nine clean terminal frames (descending sizes); wheel scroll; Help on (clean frame retained); Home, Right/Left, speed, timeline seek; Escape exit 0. The second Shift+/ (Help off) reached the viewer as a plain `/` (`mod=4096`, no Shift): synthetic `PostMessage` input did not carry the posted Shift, and the viewer correctly ignored a plain `/`. Help off was confirmed natively on Linux and in the offscreen and SDL-loop tests |
| `linux_native_04` (freeze 05, final) | **PASS**: first draw 59.5 s; End; keys; cycle; clicks; all nine terminal frames clean; wheel scroll; Help on/off; Home, Right/Left, speed, timeline seek; Escape exit 0; 27 delivered key events; no observer errors |

## 9. Qualification

Evidence root: git-ignored `runs/v6_alpha_m2/m2_4_20261015/`. Each campaign
keeps its log, JUnit and `*_command.json` (argv, interpreter, environment, exit
code, duration). Each uses fresh `.pytest-tmp/<label>` and `.pytest-cache/<label>`
roots and the retained `run.py` (copied unchanged from M2-3). Windows: Windows
11 AMD64, Python 3.13.7, pygame-ce 2.5.8 (SDL 2.32.10), Consolas
(`C:\Windows\Fonts\consola.ttf`). Linux: Ubuntu on WSL2 (kernel
6.6.87.2), Python 3.12.3, pygame-ce 2.5.8, PySide6 6.12.0 xcb, WSLg `DISPLAY=:0`.
There, `SysFont("consolas")` resolves to DejaVu Sans Mono
(`/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`).

### 9.1 Final candidate (source freeze 05)

| Campaign | Selection | Windows | Linux |
| --- | --- | --- | --- |
| `m2_4_views_05` | New module, `-m "gui or not gui"` | **37 passed** | **37 passed** |
| `m2_4_client_sensing_05` | M1-5, M1-5 adversarial, sensing, sensing adversarial, core-capture, `test_hud_layout.py`; gui included | **163 passed** | **163 passed** |
| `m2_4_focused_05` | `test_agent_test.py` + retained 22-module focused list + Reacquirer module + new module + `test_hud_layout.py` | **824 passed**, 10 `gui` deselected | **824 passed**, 10 deselected; 387 s |
| `m2_4_broad_05` | Published 138-module M2-3 broad list + new module | **3,472 passed, 21 skipped**, 11 `gui` deselected; 307 s | not run (as M2-3) |
| `m2_4_windows_gui_05` | `tests/test_v6_alpha_m1_5_designer.py -m gui` | **8 passed**: native window smoke, Scout copy/run, Keeper A/B, Reacquirer A/B, Scout Test, sensing guide | Guide node: **1 passed** (Qt xcb) |
| `m2_4_ruff_05` | `ruff check .` | **All checks passed** | — |
| `m2_4_mypy_client_05` / `m2_4_mypy_engine_05` | Separate client and engine runs | **No issues** (19 / 106 files) | — |
| C2 probe `--assert` | §5 | **PASS** | **PASS** |
| Preservation (`source_freeze_05.json`) | §3 | **PASS**, 329 pins | — |

Broad arithmetic: 3,441 (M2-3) + 31 new headless nodes = 3,472. The 11
deselected nodes are M2-3's 5 plus the new module's 6 `gui` nodes, which run
explicitly above. **The 21 skipped node IDs are identical to M2-3's**, so
M2-4 adds no skip. The engine is byte-identical to `e7c0f9d` at every freeze.

Reuse, permitted by Scope 03 §7/§10: M2-2/M2-3 scenario runs, the Keeper and
Reacquirer native demonstrations, and the 328-node compatibility supplement
were not repeated. Every engine source is byte-identical to `e7c0f9d`, and the
supplement exercises only engine research-semantics modules. The Keeper and
Reacquirer modules ran inside the focused selection.

### 9.2 Retained failures and corrections

| Attempt | Outcome | Disposition |
| --- | --- | --- |
| `m2_4_dev_existing_01` (development) | 2 failed: the M1-5 timeline click used the old fixed position `(1080,660)`; the adversarial scroll precondition no longer held because the measured layout fits all 17 lines with a 15-px font | Tests follow the measured geometry, with assertions kept (§3) |
| `m2_4_dev_new_01` (development) | 2 failed: dense-label fixture too sparse; Help equality compared scroll windows, which differ legitimately by disclaimer height | Fixture made denser; the test compares the full ordered Help text |
| Linux `m2_4_linux_views` and `linux_after_final` (freeze 01) | **3 failed / probe FAIL.** DejaVu Sans Mono is wider than Consolas: the arena caption (486 px) ran into the history header at 900x650 | **Product defect, fixed**: captions and the side header wrap to their region. A wider bundled stand-in font (26 px, 483 px caption) was added so a Windows-only run also catches this |
| Linux `m2_4_linux_views_02` (freeze 02) | **3 failed.** With the bundled 15-px font on Linux, the phase text measures 12 px on an 11-px line pitch, so its one-line region was too short | **Product defect.** Freeze 04 measured one probe string (`Ag|`) |
| Linux `m2_4_linux_views_04` (freeze 04) | **Same 3 failed.** On this platform the measured text height varies by string (`Ag|` 10 px, the phase text 12 px, `Éj` 13 px), so one probe string cannot bound it | **Fixed in freeze 05**: the row pitch is the measured height of every glyph the viewer draws (all printable ASCII plus `—` and `É`), which bounds any string made from them. Windows heights do not vary, which is why only Linux exposed this |
| Native runs | §8 | Harness-only and display-only failures, retained |

### 9.3 Load-time cost of the symmetric fallback

Building seat B's projection at load makes the fallback symmetric, but it costs
one extra cursor build. On the 200-tick C2 replay, the freeze-02 load also
rebuilt A redundantly. First draw then took 106 s on Windows (with the Linux
campaign running concurrently), against about 40 s for the same replay in
M2-2A. Freeze 03 removed the redundant A rebuild. Measured in-process on an
idle Windows machine (`load_timing_windows.json`), the A projection build takes
6.1 s and the added seat-B validation 5.7 s, so a load takes about 11.8 s in
total. The native first-draw times in §8 (59–71 s) and M2-2A's 40 s include
the passive observer's `sys.setprofile` hook, which is active throughout the
load, so they are not product timings. Perspective
switches keep the accepted M2-2 rewind-reconstruction cost; no checkpoint
redesign was made.

## 10. Conditions carried forward

| Condition | Status after M2-4 |
| --- | --- |
| M1 history/footer overlap | **Resolved** by the dedicated disclaimer row and measured layout (§5); native confirmation on both platforms belongs to M2-5 |
| M2-2 C1 (intermittent Linux End-key non-response) | Not reproduced: End responded in every native Linux run here (`linux_native_01`, `_03`, `_04`). Remains an M2-5 obligation with delivered-key witness and exit status |
| M2-2 C2 (sample-marker labels) | **Corrected and verified offscreen and natively** (§5, §8). The native before/after frame obligation on both platforms remains M2-5 per Q4 |
| M2-2 C3 / M2-3 L3 (qualification limits) | Unchanged. Linux evidence is WSL2/WSLg X11 only; no Wayland, Xvfb, bare Xorg, other distribution, full Python matrix, packaging or installer claim |
| M2-3 L1 (seat-B product view) | **Resolved**: interactive B selection by key, cycle, mouse and CLI |
| M2-3 L2 (external viewer controls) | Exercised natively here (End, seek, resize, keys, exit); formal requalification remains M2-5 |
| M2-3 L4 / L5 | L4 as above; no new skip (L5 unchanged) |

New conditions:

- **D1:** lead confirmation of the shared card definition's placement in
  `sensing_presentation.py` (§1).
- **D2:** eager seat-B validation adds about 5.7 s to each load of the
  200-tick C2 replay, roughly doubling the projection build (§9.3). M2-5
  should judge whether this is acceptable natively.
- **D3:** the Help page and the Designer guide are English-only and not
  assessed for accessibility, matching existing limitations.

## 11. Exclusions

No engine, starter, fixture, verifier, wire, schema, persisted-field, ruleset or
policy change. No stable spectator, perspective, Director, Fight Night or
`hud_layout` change, and no new renderer or Spectator application. No README or
ROADMAP status edit (status lines are a closure task). No staging, commit or
push of M2-4. M2-5 and M2-6 were not started. Scripted GUI and native
interactions are technical evidence only and are not a human-comprehension
result (M2-AC11 remains M2-6). No E8/E9 harness, private input, entropy or
authority operation, reseal or scientific execution occurred. Original E9
remains operationally blocked with execution LOCKED, and Requirement C remains
NOT ESTABLISHED.

## 12. Recommendation

**PASS WITH CONDITIONS** (D1–D3, plus the carried M2-5 obligations in §10).

M2-AC07 is met for both seats with symmetric guarantees. The focused M2-AC08
layout and the C2 correction pass on both platforms' fonts, with offscreen and
native evidence. Q1/Q2 are implemented as one static shared definition with
provenance tests. All regressions pass with no new skip. The two defects found
by Linux qualification were fixed, and their failures are retained.
