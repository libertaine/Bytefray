# Bytefray V6 — M1-5 Implementation Record 01

2026-10-11, America/Indianapolis.

**M1-5 CLOSED — FINAL ACCEPTANCE PASSED; AUTHORIZED FOR STAGING ONLY**

The Project Lead's 2026-10-11 **CONDITIONAL GO FOR CLOSURE AND STAGING** is
discharged by the final review below: no unresolved M1-5 blocker remains.
Only the exact 26-file manifest is authorized for staging. Commit, push and
publication are not authorized. M1-6 has not begun.

## Authorization and verified baseline

The lead authorized bounded M1-5 implementation and independent adversarial
review, following the adopted [M1 contract](V6_ALPHA_M1_CONTRACT_01.md),
[Phase 0 decision packet](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md), and closed
[M1-3](V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md) and
[M1-4](V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md) records.

Before writes, branch `v6-research`, local HEAD, `origin/v6-research`, and the
live remote branch all matched
`8d06ff17d7cee1a48cfa55aa9ffc71b67969bf91`.
Remote: `https://github.com/libertaine/Bytefray.git`. Tracked and index diffs
were empty. Inherited untracked private research files and test directories
were preserved, rather than staged or removed.

Read-only checks before implementation and after qualification verified:

| Preservation set | Result |
| --- | --- |
| Original external backup/source manifest | 1,442 files unchanged |
| Append-only ignored-cache supplement | 5 files unchanged |
| Complete source and backup union | **1,447/1,447 files each; 968,508,794 bytes; zero failures** |
| Original private E9 study membership | **1,384 files** |
| Retained final-08 historical implementation/qualification pins | **329/329 unchanged** |
| Local `.claude/settings.local.json` | Unchanged against the retained local preservation digest |
| External backup ACL | Still protected |

Both manifest hashes match the M1-4 custody record:
`b14afef092cb621494fa7a1ad38c9c0d38aafca0e58205f7c75a91048ec481f7`
and `f599c0c5dc7b3c4cccbc6870e32bc6341bb1f38e1ee6c85a6d55c16914fd56df`.
Source lengths, SHA-256 values and source last-write timestamps match. The
existing external backup was read only; no backup, manifest or custody record
was rewritten. Private paths and inventories are excluded from this report's
proposed public staging manifest.

These checks establish current preservation, not historical completeness or
research execution authority. E9 scientific execution remains **LOCKED**;
Requirement C remains **NOT ESTABLISHED**.

## Plan, discovered seams and actual file scope

The preliminary plan covered Designer selection/validation/trace wiring,
client CLI routing, a trusted presentation adapter, dedicated Pygame sensing
drawing, focused tests and this record. Architecture, existing specifications,
parameter widgets, subprocess launchers, result-backed replay preflight,
ReplaySession, M1-3 reconstruction and M1-4 cursors were inspected first.

The real workflow exposed two missing seams: New Agent had only Blank and
Annotated templates, and the native engine CLI accepted only stable v4.
The bounded implementation therefore adds a Window Scout personal-copy
scaffold choice and the already registered public alpha1 CLI choice. Associated
product inventory/help expectations were updated. No M1-3/M1-4 semantics or
historical research assertions were changed.

| Files | Final change |
| --- | --- |
| `app/services/ruleset_options.py` | Exact experimental label in Advanced/Development; stable defaults; product allowlist for programmatic launches |
| `app/widgets/ruleset_combo.py` | Never automatically repair selection into experimental alpha1; explain explicit selection and disable incompatible Test |
| `app/views/development.py` | Personal-copy label, workflow guidance, ruleset feedback, source/ruleset verdict invalidation and revision signal |
| `app/views/advanced.py` | Label recorded results and earlier source/settings while preserving their replay/result access |
| `app/agent_designer.py` | Explicit selected Ruleset and timeout on validation; source-change/result-label integration |
| `app/services/designer_workflows.py` | Automatic companion trace for alpha1 native matches |
| `app/services/engine_commands.py` | Alpha1 trace on the direct engine command route |
| `engine/src/battle_engine/agent_scaffold.py` | Existing exclusive-create workflow copies Window Scout, assigning personal name/display; bundled starter unchanged |
| `engine/src/battle_engine/cli.py` | Explicit public alpha1 choice and accurate ASCII help/catalog guidance |
| `client/src/battle_client/cli.py` | Alpha1 route, result/demo companions, sanitized feature fallback and perspective feedback |
| `client/src/battle_client/sensing_presentation.py` | Trusted artifact/navigation adapter; receipt-only scene; separate operator verdict and end-gated terminal state |
| `client/src/battle_client/renderers/sensing_renderer.py` | Dedicated Pygame phase view, symbols/text, histories, playback/perspective controls |
| `client/src/battle_client/renderers/pygame_renderer.py` | Route verified sensing to dedicated drawing; enforce labeled canonical fallback for direct alpha1 callers |
| `client/tests/test_v6_alpha_m1_5.py` | Native artifacts, UI adapter, complete/incomplete teaching, fallback and real SDL event loop |
| `client/tests/test_v6_alpha_m1_5_adversarial.py` | Independent hostile presentation, noninterference, fallback, scrolling and switching probes |
| `tests/test_v6_alpha_m1_5_designer.py` | Actual Qt copy/validate/edit/native run/replay/repeat plus separate native Windows window smoke |
| `tests/test_v6_alpha_m1_5_adversarial_designer.py` | Independent ruleset/source/settings revision probes using real widgets/native matches |
| `engine/tests/test_agent_scaffold.py`, `engine/tests/test_cli_agent_listing.py`, `engine/tests/test_cli_characterization.py`, `engine/tests/test_designer_ruleset_options.py` | Narrow expected public template/Ruleset/help inventory changes |
| `tests/test_agent_development_panel.py`, `tests/test_agent_development_validate.py`, `tests/test_designer_ruleset_compatibility.py`, `tests/test_v5_alpha1_phase_e_designer_ux.py` | Narrow GUI expectations for explicit alpha1, capability-filtered stable roster and validation flags |
| This record | Baseline, implementation, evidence, review, limits and exact manifest |

## Designer and native player workflow

Advanced and Development offer **V6 alpha1 — Experimental sensing** with
identity `bytefray-rules-6-alpha1`. Every fresh selector remains on stable v4.
Simple and Evaluation retain their stable-v4 scope. Research identities never
appear in these product selectors. Selecting Window Scout does not select
alpha1 automatically. The existing engine compatibility predicate includes
manifest capability preflight; no duplicate capability implementation is added.

New Agent offers a clearly named Window Scout personal-copy starting point.
It uses the existing scaffold's temporary directory and exclusive destination
rename, with the existing overwrite refusal. Only the copy's name/display are
changed. Its parameters, capability metadata and Python implementation come
from the bundled starter; the starter's qualified bytes remain untouched.

Validation remains the existing separate supervised subprocess dry run, now
explicitly bound to the selected Ruleset and timeout. The Advanced parameter
widgets still use the existing schema, bounds and canonical resolver. The
native match subprocess carries their effective overrides through the existing
environment/NativeMatchService path, with Ruleset identity persisted in
canonical replay/result output. There is no Qt execution engine.

The complete Qt workflow test exercises:

1. Create `my_window_scout` using the actual New Agent dialog button.
2. Stay on stable v4; Test is disabled. Validate reports capability mismatch.
3. Explicitly choose alpha1; Validate succeeds in a real child process.
4. Select the personal copy in Advanced, edit interval **2** and move step
   **32** through the existing bounded controls, and click Run.
5. Complete a bounded native **three-tick, 512-cell** match; verify selected
   Ruleset and effective parameters in `result.json`, then load its associated
   replay/trace/result into the filtered sensing adapter.
6. Exercise the actual result-backed replay launch request and verify the exact
   replay selected. This test intercepts process launch; real SDL playback is
   exercised separately below.
7. Change parameters to interval **3**, step **16** and run again. The second
   completed result has a different result ID and directory, retains the new
   effective parameters, and Open Replay selects that second result. The first
   result remains available.

Development Test remains a complete native test using manifest defaults; the
visible guidance directs parameterized full matches to Advanced. Changing the
Ruleset or reloading changed source invalidates the earlier validation verdict.
Advanced labels earlier results when settings or source change without editing
their recorded parameters/artifacts. This is not a qualification claim for a
1,000-tick manual or cross-platform acceptance campaign.

## Replay association, verification and failure behavior

The existing result-backed preflight remains authoritative for Designer replay
launch. Unique native run directories associate `replay.jsonl`, `trace.jsonl`
and `result.json`; the client discovers their companions and optional
`demo.json`, with explicit `--trace`, `--result` and `--demo` overrides.
No sidecar is manufactured for an ordinary match.

The trusted loader uses M1-4 `SensingCursor.from_paths`, which invokes accepted
M1-3 binding/reconstruction checks. It distinguishes artifact consistency,
independent sensing reconstruction, complete teaching exchange, filtered
perspective availability, and optional sidecar validation. A consistent pair
can project safely without completing the teaching sequence. Complete-demo
operator verdicts never enter the entrant scene. All explanations remain
factual; starter motivation/strategy explanations are withheld, including when
source-revision evidence is unavailable or incompatible.

An invalid optional sidecar is refused and reported separately while a valid
ordinary pair remains usable. Missing/invalid trace or result binding disables
entrant/exchange features and leaves explicitly labeled **Omniscient — replay
only** viewing of the canonical replay. The alpha1 fallback suppresses passive
perspective, Director and Fight Night managers, including direct renderer
callers. It cannot silently supply omniscient state as entrant knowledge.
Messages omit evidence paths and hidden contradiction details. Existing stable
and historical replay routes remain intact.

## Renderer boundary and phase playback

`draw_entrant(view: SensingView)` and `entrant_scene(view: SensingView)` receive
only M1-4's validated immutable filtered payload. They have no ReplaySession,
raw reconstruction, opponent rows, ownership map, hidden action counters,
camera targets, tooltips or operator verdict input. Dedicated sensing playback
bypasses the existing raw-world HUD/effects/territory caches. Every redraw
starts with a blank surface; view changes rebuild through M1-4 and reset the
history scroll position. There is no renderer calculation of entrant knowledge.

The scene provides unknown-arena text, own core/anchors, a request ring/window,
one-action cost and pending status, a distinct receipt cross, anonymous
historical sample diamonds with tick/callback ages, applied MOVE arrows and
WRITE markers with actual recorded status/value. Empty, positive, refused,
absent and pending states remain distinct. Samples never follow opponents.
An address absent in a later delivered scan is labeled as such. READ feedback
shows only delivered value/owner, expressly without joining ownership to an
anonymous contact. Wheel scrolling exposes the complete delivered scan/read
history, including old empty scans and both sample/receipt process/time points.

Initial verified alpha1 playback uses **Agent A — delivered information**.
Explicit **Omniscient — full world state** uses verified sub-tick state.
Keyboard and mouse perspective controls remain unmistakably labeled.
The existing Space, arrow, Shift-arrow, Home, End and speed conventions apply
to M1-4's ordered OBSERVATION/ACTION/TICK_END cursor; timeline dragging seeks
permitted phases. Playback uses one constant interval per permitted phase;
speed affects timing only. Opponent callbacks, wall-clock trace times and
hidden event salience never control entrant pacing. Seeks/restarts rebuild the
permitted prefix. Terminal outcome is gated until the recorded final phase.
M1-4 continues to check canonical ReplaySession agreement at tick boundaries.

## Independent adversarial review

The reviewer was spawned after implementation in a fresh context without the
implementation conversation. It inspected the code/contracts independently
and authored only the two adversarial test files in the manifest. Six findings
were independently reproduced as failing tests, then reproduced by the primary
implementer before correction:

| Finding | Reproduction | Resolution |
| --- | --- | --- |
| F1, P2: delivered READ omitted | WRITE 0=237, READ 0, next observation | Show delivered value/owner history |
| F2, P2: older scans inaccessible | Positive, empty, positive scans; later observation | Preserve all delivered scans and add reachable wheel scrolling |
| F3, P3: receipt points incomplete | SENSE at callback 8, receipt in next tick | Label sample/delivery tick, callback and process |
| F4, P2: Ruleset verdict drift | Valid alpha1 SENSE verdict, then select v4 | Invalidate previous validation on Ruleset change |
| F5, P2: source verdict drift | Validate personal copy, edit source, Reload | Invalidate cached evidence on changed source |
| F6, P2: result/settings drift | Complete interval-2 match, then edit interval to 3 | Label recorded result as earlier settings; preserve artifact access |

Preventive follow-up probes also cover source changes across Development and
Advanced, and mouse/keyboard scroll-reset parity. The independent final run
passed **12/12 probes**, including real native Designer matches and real
Pygame Surface event handling. Independent test-file Ruff passed. Final reviewer
disposition: **PASS after fixes; no remaining reproduced blocker**.

No correction changed accepted M1-3/M1-4 semantics, gameplay, or wire formats.

## Qualification and graphical evidence

All Python checks use the repository `.venv`, Python **3.13.14**, with `-B`.
Pytest runs use fresh product-only basetemp roots under `.pytest-tmp/` and
`-p no:cacheprovider`; disabling that provider produces the known non-failing
`Unknown config option: cache_dir` warning. No collection configuration,
frozen research test, schema or authority guard was changed.

| Check | Final result |
| --- | --- |
| Focused M1-5 client tests, including real SDL/surface probes and independent client probes | **21 passed** |
| Independent complete adversarial selection | **12 passed** |
| Relevant existing Designer GUI tests plus complete native authoring and independent revision probes | **170 passed; zero failures/errors/skips** |
| Supported existing and M1-5 client GUI interaction tests | **7 passed; zero failures/errors/skips** |
| Current client/product/Designer CLI/native/historical regression selection | **857 passed; zero failures/errors/skips** |
| M1-3 regressions within that selection | **30 passed** |
| M1-4 acceptance/adversarial regressions within that selection | **29 passed** |
| M1-2 and M1-1 capability regressions within that selection | **19 and 42 passed** |
| Stable v4 historical/equivalence checks within that selection | **5 and 27 passed** |
| Existing Pygame renderer contract tests within that selection | **157 passed** |
| Separate native Windows Qt window exercise | **1 passed; handled diagnostic noted below** |
| Repository Ruff | Passed |
| Engine mypy / client mypy | Passed, **102 / 19 source files** |
| Tracked/index diff formatting and new-file whitespace checks | Passed |
| Final historical/private preservation | **329 pins; 1,447 source and backup files each unchanged** |

Counts overlap; they must not be added into a unique total. The focused final
selection includes one complete-sidecar test added after the 857-test matrix;
it passed in the focused final run. JUnit evidence:
`.pytest-tmp/m1_5_regression_final_01.xml`,
`.pytest-tmp/m1_5_designer_regression_final_01.xml`,
`.pytest-tmp/m1_5_client_gui_final_01.xml`, and
`.pytest-tmp/m1_5_focused_final_01.xml`.
Independent final run root: `.pytest-tmp/m1_5_independent_final_01`.

The broad current selection is all `client/tests` plus engine tests for M1-3,
M1-2, M1-1 capabilities, historical immutability, stable equivalence, runtime
default, native match service, validation, Designer ruleset/workflows/third
entrant, scaffold, CLI characterization and CLI agent listing. This is a
bounded product qualification matrix, not an unpartitioned whole-repository
PASS. The adopted [separate historical-baseline disposition](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)
remains intact. Its earlier accepted 72-node execution was not rerun here;
the 329 retained raw pins were reverified read only.

The actual Windows SDL window ran through the real client CLI and Pygame loop,
with queued step, play/pause, speed, seek, restart and perspective events. It
saved request, receipt and WRITE frames, visually inspected during this task.
The separate native Windows Qt window exercise showed Designer, changed the
Ruleset through a real key event, selected Window Scout and edited parameters;
its captured native screenshot was also inspected. That run exited **0** and
passed, but emitted Windows diagnostic **0x8001010d**. A bare native Qt QWidget
without any Bytefray imports reproduced the same diagnostic and also completed
with exit **0**. This is documented as an environment/native-Qt limitation,
not a clean platform acceptance claim. The full copy/match/repeat Qt tests use
offscreen widgets and real child processes; they are not proof of manual
graphical interaction. No human usability session or full Linux/Windows
platform campaign is claimed.

## Usability review and remaining boundaries

The option and personal-copy template are explicitly named; Development gives
the path to Advanced's existing parameter controls and explains test defaults.
Parameter descriptions/ranges remain authored by the starter's manifest.
One-action cost, pending request and delayed receipt have separate symbols and
text. Historical contacts retain sample location/age. Both perspectives have
explicit permanent labels and visible mouse/keyboard choices. Old requests are
identified as recorded history. Full histories are scrollable; source/settings
changes label or clear obsolete evidence; invalid sidecars/traces have safe,
sanitized recovery paths.

All reproduced in-scope usability/review issues were corrected. No in-scope
implementation blocker remains. Rich starter-strategy explanations would need
immutable teaching-revision validation and are intentionally withheld here.
Broader novice testing, platform/accessibility acceptance, packaged execution
and the native-Qt diagnostic belong in the later platform acceptance campaign.
No unrelated redesign, agent family, animation system or M1-6 work was added.

E9 execution, entropy/seed generation for research, payoff execution, G
consumption and authority events did not occur. No E8/E9 harness was imported
by new product routes. Private evidence, manifests, backups, frozen bytes and
schemas replay4/trace2/result2 remain unchanged. Product teaching fixtures
retain their separate declared product role and establish no scientific claim.

## Exact authorized staging manifest

The final acceptance instruction authorizes staging these 26 files, including
this closure record. **Do not commit or push.**

```text
app/agent_designer.py
app/services/designer_workflows.py
app/services/engine_commands.py
app/services/ruleset_options.py
app/views/advanced.py
app/views/development.py
app/widgets/ruleset_combo.py
client/src/battle_client/cli.py
client/src/battle_client/renderers/pygame_renderer.py
client/src/battle_client/renderers/sensing_renderer.py
client/src/battle_client/sensing_presentation.py
client/tests/test_v6_alpha_m1_5.py
client/tests/test_v6_alpha_m1_5_adversarial.py
docs/v6/V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md
engine/src/battle_engine/agent_scaffold.py
engine/src/battle_engine/cli.py
engine/tests/test_agent_scaffold.py
engine/tests/test_cli_agent_listing.py
engine/tests/test_cli_characterization.py
engine/tests/test_designer_ruleset_options.py
tests/test_agent_development_panel.py
tests/test_agent_development_validate.py
tests/test_designer_ruleset_compatibility.py
tests/test_v5_alpha1_phase_e_designer_ux.py
tests/test_v6_alpha_m1_5_adversarial_designer.py
tests/test_v6_alpha_m1_5_designer.py
```

Inherited private/untracked research, local settings, ignored product test
outputs/screenshots, retained historical work directories and external custody
records are excluded. Final disposition is **M1-5 CLOSED — FINAL ACCEPTANCE
PASSED**, with the explicit graphical/platform limits above and below.

## Final acceptance review and formal closure — 2026-10-11

The complete implementation record, all 26 implementation/review files,
adopted M1 boundaries, relevant architecture/specifications, retained final
JUnit reports, native artifacts/screenshots, and original implementation and
independent-review tool evidence were reviewed. This is a closure review of
existing qualification evidence. No broad development/regression cycle, new
test, gameplay change or M1-6 work was needed or performed.

Branch and parent HEAD are `v6-research` and
`8d06ff17d7cee1a48cfa55aa9ffc71b67969bf91`. The index was empty at review
entry; upstream `origin/v6-research` has that same locally recorded commit.
There are exactly **19 tracked modifications and seven authorized new files**
in the manifest. All tracked modifications belong to M1-5; the 58 inherited
untracked file entries are excluded and preserved. No unrelated tracked
change, hidden research dependency, wire-schema change or scope expansion
was found. The engine CLI/scaffold additions are necessary product workflow
seams for the already registered alpha1 identity and existing Window Scout.

### File-by-file responsibility classification

Every row was inspected against the actual diff or, for a new file, its
complete contents. Responsibilities can span categories; all listed
responsibilities are authorized M1-5 work.

| File | Authorized responsibility | Review |
| --- | --- | --- |
| `app/agent_designer.py` | Parameter editing and validation; Designer/Development workflow; selected Ruleset/timeout and source-revision wiring | PASS |
| `app/services/designer_workflows.py` | Match/replay launch routing; alpha1 companion trace | PASS |
| `app/services/engine_commands.py` | Match/replay launch routing; direct alpha1 trace command | PASS |
| `app/services/ruleset_options.py` | Explicit experimental Ruleset selection; public product allowlist and stable defaults | PASS |
| `app/views/advanced.py` | Parameter editing and validation; recorded-result revision labels | PASS |
| `app/views/development.py` | Designer/Development workflow; copy guidance and validation/source invalidation | PASS |
| `app/widgets/ruleset_combo.py` | Explicit experimental Ruleset selection; no automatic experimental repair | PASS |
| `client/src/battle_client/cli.py` | Client CLI integration; associated evidence and sanitized fallback | PASS |
| `client/src/battle_client/renderers/pygame_renderer.py` | Filtered Pygame phase playback; verified route and labeled direct-call fallback | PASS |
| `client/src/battle_client/renderers/sensing_renderer.py` | Filtered Pygame phase playback; drawing and interaction | PASS |
| `client/src/battle_client/sensing_presentation.py` | Filtered Pygame phase playback; trusted adapter and receipt-only scene | PASS |
| `client/tests/test_v6_alpha_m1_5.py` | Focused/regression tests; native artifacts, SDL and verification boundaries | PASS |
| `client/tests/test_v6_alpha_m1_5_adversarial.py` | Focused/regression tests; independent client probes | PASS |
| `docs/v6/V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md` | Implementation and acceptance documentation; formal closure and exact manifest | PASS |
| `engine/src/battle_engine/agent_scaffold.py` | Designer/Development workflow; exclusive-create Window Scout personal copy | PASS |
| `engine/src/battle_engine/cli.py` | Explicit experimental Ruleset selection; native match launch choice/help | PASS |
| `engine/tests/test_agent_scaffold.py` | Focused/regression tests; public template inventory | PASS |
| `engine/tests/test_cli_agent_listing.py` | Focused/regression tests; public catalog/capability expectations | PASS |
| `engine/tests/test_cli_characterization.py` | Focused/regression tests; explicit CLI Ruleset inventory | PASS |
| `engine/tests/test_designer_ruleset_options.py` | Focused/regression tests; bounded product selection | PASS |
| `tests/test_agent_development_panel.py` | Focused/regression tests; capability-filtered selectors | PASS |
| `tests/test_agent_development_validate.py` | Focused/regression tests; selected validation Ruleset/timeout | PASS |
| `tests/test_designer_ruleset_compatibility.py` | Focused/regression tests; Development compatibility | PASS |
| `tests/test_v5_alpha1_phase_e_designer_ux.py` | Focused/regression tests; unchanged research exclusion with explicit public alpha1 | PASS |
| `tests/test_v6_alpha_m1_5_adversarial_designer.py` | Focused/regression tests; independent revision/verdict probes | PASS |
| `tests/test_v6_alpha_m1_5_designer.py` | Focused/regression tests; complete authoring workflow and bounded native Qt window | PASS within recorded limits |

### Information-boundary acceptance

Confirmed: `entrant_scene` and `draw_entrant` accept only the approved M1-4
`SensingView`; omniscient reconstruction has a separately labeled drawing
route. Neither raw ReplaySession/world state nor operator verification enters
the entrant scene. Perspective switches rebuild the permitted prefix, pause
playback, reset scrolling and redraw a blank surface; rewind removes future
receipts. Hidden-write/movement noninterference and pixel round-trip evidence
support the boundary. No opponent camera, tooltip, event total, ownership
cache, Director or Fight Night pacing input is used by the entrant renderer.
Timeline positions and constant phase intervals come from the permitted
M1-4 cursor, without blank opponent callbacks or hidden salience.

Artifact consistency, independent reconstruction, teaching completion,
filtered projection availability and optional sidecar verification remain
separate facts. Missing/invalid exchange evidence uses the explicitly labeled
omniscient replay-only fallback with delivered perspective disabled; it
claims neither verified sensing nor teaching completion. Invalid optional
demo evidence is separately refused while an ordinary consistent pair remains
usable. Terminal outcome is withheld until the recorded final phase.
Sample age, action cost, pending status, sample/receipt tick-callback-process,
applied MOVE and actual WRITE status/value have factual labels. Anonymous
contacts remain historical; delivered READ ownership is not joined to them.

### Authoring and native-interaction acceptance

The complete retained authoring test passed using **offscreen Qt widgets and
real native child processes**. It created the personal copy through New Agent,
confirmed stable-v4 refusal, explicitly selected alpha1, validated, edited
bounded parameters, completed two three-tick native matches, verified their
distinct results and effective parameters, loaded the matching artifacts and
checked result-backed Open Replay selection. Open Replay process launch was
intercepted in that test. It does not establish a single manual native-window
copy/edit/match/replay session.

The recorded completed results retain alpha1, `tick_limit`, interval/step
**2/32** and **3/16**, distinct result IDs/directories and matching replay
digests. Separate actual SDL CLI/window playback exercised queued phase steps,
play/pause, speed, restart, end seek and perspective switching. Surface/event
tests exercised timeline seeking and rewind. Retained request/receipt/WRITE
frames and the Windows Designer screenshot were inspected during final
review. Missing/invalid evidence and stable/historical viewer compatibility
are supported by the focused and existing regression evidence. None of this
is human usability or full platform acceptance.

### Complete Qt diagnostic disposition

The first native Windows Qt smoke attempt exited **1**: a subprocess-wait
assertion had been placed in the window-only test, which launched no match.
That test-helper placement was corrected during implementation. The failed
attempt remains failed evidence; it is not counted as a full GUI PASS.

The corrected `m1_5_native_qt_02` exercise emitted the diagnostic
**`Windows fatal exception: code 0x8001010d`** at window display, continued,
completed the intended bounded operations and exited **0**, with one passing
test. It showed Designer, selected alpha1 through an actual Qt key event,
selected Window Scout, set interval/step controls to 2/32, checked visibility,
saved the native screenshot and closed. Other control changes were
programmatic; this was not a human authoring session or full native match
workflow. No functionality failure was observed within those operations.

The independent minimal reproduction ran only:

```python
from PySide6.QtWidgets import QApplication, QWidget
app = QApplication([])
window = QWidget()
window.show()
app.processEvents()
window.close()
app.processEvents()
print("Bare native Qt window completed without Bytefray imports")
```

With native Windows Qt and Python faulthandler enabled, it emitted the same
diagnostic, printed the completion marker and exited **0**, without any
Bytefray import. External reproducibility supports a **nonblocking native
Qt/environment limitation for M1-5**, without claiming a proven root cause.
Clean native Qt/platform qualification, the full manual native workflow,
Linux/Windows interaction, accessibility/usability and packaged execution
remain reserved for M1-6. M1-6 has not begun.

### Independent review and validation confirmation

The complete six-finding table above and all corrective dispositions remain
preserved. The original independent final command selected both adversarial
files with `-m 'gui or not gui'`; its retained result is **12 probes, exit 0**.
The independent reviewer concluded **PASS after fixes; no remaining reproduced
blocker**. Its Qt probes used offscreen widgets; native matches and Pygame
Surface handling were real. Final review confirmed each probe's disposition:

| Probe (test function) | Finding/boundary | Final result |
| --- | --- | --- |
| `test_delivered_read_value_and_owner_reach_the_display` | F1 delivered READ | PASS |
| `test_old_delivered_scan_samples_remain_inspectable` | F2 complete scan history | PASS |
| `test_cross_tick_receipt_labels_identify_both_ticks_and_own_process` | F3 receipt timing/process | PASS |
| `test_hidden_opponent_writes_do_not_change_entrant_scene_or_pacing` | Hidden-write noninterference and switching | PASS |
| `test_invalid_trace_cli_fallback_disables_all_passive_perspectives` | Invalid-trace fallback | PASS |
| `test_unavailable_alpha_perspective_has_sanitized_feedback` | Sanitized unavailable perspective | PASS |
| `test_direct_alpha_fallback_clears_untrusted_legacy_managers` | Direct renderer fallback | PASS |
| `test_scroll_reaches_recorded_histories_and_rewind_removes_future_receipts` | Reachable histories, switch reset and rewind | PASS |
| `test_validation_verdict_is_scoped_when_selected_ruleset_changes` | F4 Ruleset verdict drift | PASS |
| `test_changed_parameters_label_completed_match_as_earlier_settings` | F6 result/settings drift | PASS |
| `test_reloaded_external_source_change_scopes_previous_validation` | F5 source verdict drift | PASS |
| `test_reloaded_source_labels_completed_advanced_match_as_earlier_revision` | Cross-panel source/result follow-up | PASS |

The four retained final JUnit reports were parsed: **857 product regressions,
170 Designer GUI tests, 21 focused client tests and seven client GUI tests**,
each with zero failures/errors/skips. The focused 21 share **16** cases with
the 857 and **four** GUI cases with the seven. The remaining focused case is
the complete-demo-sidecar check added after the 857 matrix. All eight client
adversarial probes occur in the focused 21; all four Designer adversarial
probes occur in the 170. Thus the independent 12 overlap these selections;
no aggregate total is claimed. Existing M1/historical subsets remain subsets
of the bounded matrix, not a whole-repository qualification claim.

Retained final tool exits confirm repository Ruff and engine/client mypy
passed, **102/19 source files** respectively. The separate historical-baseline
validation disposition remains intact; no frozen suite was rerun. Fresh
read-only closure checks reproduced **329/329 retained historical pins**,
**1,447/1,447 source and backup members each**, **968,508,794 bytes**, matching
manifest hashes, unchanged source timestamps, 1,384 study members, unchanged
local settings and protected backup ACL, with **zero failures**. No custody
record or private payload was rewritten. These are current preservation checks,
not historical-completeness or E9 execution-authority evidence.

### Closure and index boundary

**Formal M1-5 closure is recorded under the Project Lead's conditional
authorization: final acceptance PASS, no unresolved M1-5 blocker.** The Qt
limitation above is retained as a later platform gate. The independent review
findings, dispositions, failed initial smoke and bounded final evidence remain
visible. Product replay4/trace2/result2 contracts, M1-3/M1-4 implementations,
stable-v4 default, private research authority and historical bytes are intact.

Staging is restricted to the exact 26-file manifest above. The authorized
staging operation completed; index inspection matched **26 files, 19 M / 7 A**,
and `git diff --cached --check` passed. There were no unstaged tracked changes
and parent HEAD remained the required baseline. Private E9 evidence, custody/backup data,
generated matches/screenshots, retained historical work, temporary files,
local settings and unrelated changes are excluded. This verification entry
is included in the final closure record and the same exact-manifest and
whitespace checks apply after its staging. No commit or push is authorized;
stop after staging verification and return for local commit authorization.
No M1-6 work is included or begun.
