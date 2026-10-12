# Bytefray V6 — M1 Final Technical Acceptance Record 01

2026-10-11, America/Indianapolis.

**Authority: Bytefray Project Lead — formal acceptance decision**

| Decision axis | Recorded disposition |
| --- | --- |
| M1 TECHNICAL ACCEPTANCE | **PASS** |
| M1 MILESTONE STATUS | **CLOSED** |
| BROADER ALPHA 1 DEVELOPMENT | **INCOMPLETE** |
| UNRESTRICTED PUBLIC RELEASE | **NOT AUTHORIZED** |

## 1. Authority, scope and accepted publication baseline

The Project Lead formally accepts **M1 — Verified Sensing Exchange** as
completed under the authoritative [M1 Contract 01](V6_ALPHA_M1_CONTRACT_01.md)
and adopted [Phase 0 Decision Packet 01](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md).
Phase 0 recorded adoption of K1–K4, restrictions C-1 through C-4, and bounded
implementation authorization for M1-1 through M1-6 under AC1–AC11.

Repository: **Bytefray**. Branch: **`v6-research`**. Accepted published baseline:

```text
053e3eb1bc355ac1f4f15cba5d025b70ba418c1d
```

This decision consolidates the existing completed implementation and platform
qualification evidence. It discharges the consolidated Project Lead M1 review
identified by the Linux record. It authorizes no further testing, product
development, research operation or release campaign. Earlier proposal,
staging-only, pending-Linux and pending-consolidation statements remain in the
unchanged historical records; this record establishes the final M1 disposition
at the accepted publication baseline.

## 2. Completed and published milestone records

Each commit below is in the accepted baseline's published ancestry. M1-1
through M1-5 are **COMPLETED AND PUBLISHED**; both platform qualifications are
**CLOSED — PASS**.

| Milestone | Accepted deliverable and record | Published commit |
| --- | --- | --- |
| M1-1 | Policy and capability support; [formal lead closure](V6_ALPHA_M1_1_CLOSURE_01.md) | `b6c9a57fa2a980cc2f6a4f0733046913b8d7e35b` |
| M1-2 | Window Scout teaching demonstration and fixture opponent; [implementation record](V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md) | `36cf5377803d44cf855c9392421953a8bac2734c` |
| M1-3 | Artifact validation and independent sensing-exchange reconstruction; [implementation record](V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md) | `7d98e0a0caf915bd368ce408102c1404215635c7` |
| M1-4 | Filtered knowledge projection and phase cursor; [implementation record](V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md) | `8d06ff17d7cee1a48cfa55aa9ffc71b67969bf91` |
| M1-5 | Designer authoring and interactive filtered playback; [implementation record](V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md) | `ab35b5c35056ad6dbbec4db895017399daaaa998` |
| M1-6A Windows | **CLOSED — PASS**; [Windows Qualification 01][windows] | `5d6fc19e2b84805e0453da2c851f1ab0d7804f2f` |
| M1-6B Linux | **CLOSED — PASS**; [Linux Qualification 01][linux] | `053e3eb1bc355ac1f4f15cba5d025b70ba418c1d` |

Windows qualification exercised native Windows AMD64 Qt/SDL and engine
workflows with Python 3.13.14. Linux qualification exercised native Linux
engine execution and Qt `xcb` / SDL `x11` under X11/Xvfb with Python 3.14.4.
Both retain actual authoring, complete-match, result-associated replay and
control-processing evidence. Automated native interaction does not establish
a human usability study or qualify every desktop environment.

## 3. Consolidated AC1–AC11 acceptance

The following dispositions adopt the existing Windows §2 and Linux §3
acceptance matrices within the bounded M1 contract. The linked platform
records retain the detailed tests, native witnesses and evidence packets;
this table creates no new execution or coverage total.

| Criterion | Accepted behavior and evidence | Platform references | Disposition |
| --- | --- | --- | --- |
| AC1 legality | Operand normalization, reach/window boundaries, rejected/invalid actions and stable-v4 capability rejection are checked before or during the authorized action path. | [Windows][windows], [Linux][linux] | **PASS** |
| AC2 price | SENSE, empty and rejected scans consume one action opportunity without world mutation; quota exhaustion and trace-on/off gameplay agreement are verified. | [Windows][windows], [Linux][linux] | **PASS** |
| AC3 availability | Passive enemy contacts remain empty; samples contain exact sorted unique eligible enemy anchors at the recorded sample point. | [Windows][windows], [Linux][linux] | **PASS** |
| AC4 delivery | Anonymous samples arrive once at the next eligible same-process observation; sibling, empty/refused/absent and terminal non-delivery cases remain distinct. | [Windows][windows], [Linux][linux] | **PASS** |
| AC5 knowledge | Filtered entrant views withhold undelivered/future and hidden opponent state; delivered samples retain historical position and age without live tracking or hidden-navigation leakage. | [Windows][windows], [Linux][linux] | **PASS** |
| AC6 reconstruction | Independent replay/trace reconstruction checks raw binding, result/demo association, samples and every tick's world state; corrupt or missing evidence refuses verified delivered playback. | [Windows][windows], [Linux][linux] | **PASS** |
| AC7 client agreement | Request, receipt, MOVE and WRITE phases agree with canonical replay boundaries; stepping, seeking, restart and perspective transitions preserve permitted prefixes. Native controls are exercised. | [Windows][windows], [Linux][linux] | **PASS** |
| AC8 reproduction | Repeated completed teaching runs agree in canonical logical gameplay, ordered trace facts and terminal identities/outcomes with complete revision capture and source fingerprints. | [Windows][windows], [Linux][linux] | **PASS** |
| AC9 authoring | Personal copy, parameter edits, capability/range validation, native child execution, matching replay reopen and earlier-settings labeling work in qualified native workflows. | [Windows][windows], [Linux][linux] | **PASS** |
| AC10 compatibility | Stable-v4 defaults, historical readers, retired-execution rejection and unchanged golden expectations are preserved; required compatibility supplements and separate historical qualification are retained. | [Windows][windows], [Linux][linux] | **PASS** |
| AC11 research isolation | Product negative boundary checks pass; historical pins remain identifiable and unchanged; qualification performs no private-seed, research-controller, G or operational authority activity. | [Windows][windows], [Linux][linux] | **PASS** |

## 4. Campaign identities, overlap and historical qualification

The retained [Windows evidence packet](evidence/m1_6a_windows/README.md) and
[Linux evidence packet](evidence/m1_6b_linux/README.md) preserve commands,
selections, outcomes and provenance. These are separate campaign results:

| Platform and retained campaign | Original outcome | Evidence |
| --- | --- | --- |
| Windows product complement | 3,199 passed, 19 skipped, 7 GUI deselected; zero failures/errors | [regression.xml](evidence/m1_6a_windows/regression.xml) |
| Windows compatibility supplement | 328 passed; zero failures/errors/skips/deselections | [supplemental_compatibility.xml](evidence/m1_6a_windows/supplemental_compatibility.xml) |
| Windows separate closure client GUI selection | 7 passed, 550 deselected; zero failures/errors/skips | [client_gui.xml](evidence/m1_6a_windows/client_gui.xml) |
| Linux focused M1-1 through M1-5 | 137 passed, 4 GUI deselected; zero failures/errors/skips | [focused.xml](evidence/m1_6b_linux/focused.xml) |
| Linux product complement | 3,207 passed, 11 skipped, 5 GUI deselected; zero failures/errors | [regression.xml](evidence/m1_6b_linux/regression.xml) |
| Linux compatibility supplement | 328 passed; zero failures/errors/skips/deselections | [supplemental.xml](evidence/m1_6b_linux/supplemental.xml) |
| Linux original client + Designer GUI selection | 507 passed, 1 failed, 1 skipped, 556 deselected; zero errors | [gui.xml](evidence/m1_6b_linux/gui.xml) |
| Linux isolated focus reproduction | 1 failed; zero passes/errors/skips | [focus_repro.xml](evidence/m1_6b_linux/focus_repro.xml) |
| Linux same unchanged case with X11 activation | 1 passed; zero failures/errors/skips | [focus_assisted.xml](evidence/m1_6b_linux/focus_assisted.xml) |

Both product complements account for 3,218 executed/skip-accounted cases;
platform skips and deselections differ as documented. Each 328-case supplement
is disjoint from its product complement. Windows earlier focused selections
overlap the broad selection and each other; the Windows closure GUI run remains
separate from its earlier reported GUI run. All 137 Linux focused cases overlap
the Linux product complement. The two Linux focus runs repeat the same node
from the original GUI campaign. Neither screenshots nor native witness steps
are additional pytest cases. No aggregate count combines these runs, platforms
or witnesses, and the original failing Linux GUI invocation remains failed.

The adopted [M1-1 Frozen Baseline Validation Disposition 03](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)
separately qualified **72 unchanged historical nodes** against preserved
baseline `b948540aa9ef34134ff7e3c633c3acfc9f97da96`: **71 passed** in its
ordinary historical process and **one passed** with the existing
entropy-prohibiting qualification plugin in a separate process. This is the
accepted M1-1 historical result, not a new Windows/Linux product-campaign count;
Linux did not rerun it. Current stable-v4 golden and compatibility tests are
distinct from that frozen-instrument qualification.

Research/experiment partitions retain their adopted classifications. No
unpartitioned full-repository suite PASS is inferred. The compatibility
supplements use authorized synthetic characterization inputs, including
existing E8 helpers; they are distinct from product entrypoint isolation and
do not constitute an E8/E9 study, payoff campaign or scientific execution.

## 5. Accepted nonblocking limitations and comparison bounds

| Finding | Accepted disposition and retained limitation | Existing record |
| --- | --- | --- |
| History/footer text overlap | **NONBLOCKING usability limitation requiring post-M1 follow-up.** The shared footer/history layout has inadequate separation; Linux's resolved font visibly overlaps detail text in receipt/history and resized terminal frames. Essential cost, receipt, age, phase, controls and outcome remain available. No layout repair was made. | [Linux][linux] §10, L2; unchanged Windows receipt/history frames |
| Windows Qt COM diagnostic `0x8001010d` | **NONBLOCKING observed platform diagnostic; root cause unresolved.** Qualified processes continued and completed. Reproduction with a bare QWidget without Bytefray imports supports an integration origin but does not identify the COM caller, initiating subsystem or full call chain. No specific upstream defect or measured latency guarantee is asserted. | [Windows][windows] §6 |
| Linux X11 focus prerequisite | **RESOLVED qualification-environment issue; nonblocking.** Bare Xvfb left the keyboard test without a focused widget. Ordinary `xdotool windowfocus --sync` activated the actual window and the same unchanged test passed. Original GUI failure and isolated failure remain recorded; no failing assertion, test or product code was modified. | [Linux][linux] §10, L1; [focus proof](evidence/m1_6b_linux/focus_assist.json) |

The Linux §7 comparison limitation remains: the published Windows packet lacks
the complete original teaching replay/trace bodies. A direct record-by-record
Windows/Linux raw-artifact gameplay comparison is **unverified due to artifact
availability**. Accepted comparisons are limited to published equivalent
inputs, reported exchange facts and canonical Designer result identities.
Windows evidence is not reused as proof of Linux execution.

Windows repeated completed 100-tick teaching runs agree in 103 replay lines and
1,600 logical trace records. Linux repeated completed 1,000-tick teaching runs
agree in 1,003 canonical replay lines and 16,000 logical trace records; Linux
also qualified the Windows-equivalent 100-tick input. Comparisons exclude the
declared timing field `wall_time_ms`, while each raw artifact binding is checked
individually. These are same-build teaching-revision reproduction results;
neither arbitrary editable Python determinism nor cross-platform raw byte
equality is certified. The M1 contract does not require LF/CRLF digest equality.

## 6. Compatibility and historical research preservation

Stable **`bytefray-rules-4` remains the default**. The public experimental
**`bytefray-rules-6-alpha1` requires explicit selection**; stable-v4 continues
to reject SENSE. Frozen historical identities/readers and retired-execution
boundaries remain intact. **Replay4 / trace2 / result2 contracts are unchanged**;
internal package names and stable protocol identifiers remain unchanged.
Capability metadata v1 and demonstration sidecar v1 remain additive, separately
versioned contracts adopted by Phase 0 K3.

The accepted preservation evidence establishes:

- **329 historical pins unchanged:** 293 implementation and 36 qualification
  members match their original raw bytes at historical baseline
  `b948540aa9ef34134ff7e3c633c3acfc9f97da96`, with zero mismatches. The
  [Linux baseline integrity record](evidence/m1_6b_linux/baseline_integrity.json)
  retains the pin verification. Current evolved product source remains a
  distinct instrument; it is not re-blessed as the historical E9 instrument.
- **E9 scientific execution: LOCKED. Requirement C: NOT ESTABLISHED.** No
  research seed generation, private-seed access, payoff study or controller
  execution is authorized by M1 acceptance.
- **No new G consumption or research operational authority events.** Original
  G remains consumed exactly once under retained historical records; M1
  acceptance does not reset, replace or extend that history.
- **Teaching-only seed exception unchanged:** Phase 0 K2 permits deterministic
  inputs exclusively for declared product teaching fixtures with
  machine-checkable provenance. It does not close PR8 §13's public seed
  reconstruction prerequisite or establish hostile-agent seed secrecy. The
  viewer promises faithful engine-delivered knowledge within the contract.
- **Private custody boundaries preserved:** Windows §11 records its verified
  1,384-file study and 1,447-file backup inventories. Linux §9 explicitly did
  not copy, inspect or requalify those private Windows inventories. This
  consolidation adds no private-custody or off-machine recovery claim and
  modifies no historical source, manifest, evidence or backup.

## 7. Outstanding post-M1 work — recorded, not begun

M1 has no remaining technical acceptance or platform campaign blocker. Broader
Alpha 1 remains incomplete. The contract's later scope and accepted platform
limitations leave the following work for separate planning and authorization:

- Resolve the public seed/context/placement threat model and PR8 §13 promotion
  prerequisite; retain the teaching-only exception until separately disposed.
- Address history/footer separation using retained Linux D/G/I and Windows
  receipt/history evidence, preserving filtered knowledge and checking both
  platform fonts. Further COM caller investigation, if undertaken, must retain
  the unresolved root-cause statement until evidence establishes it. Preserve
  the resolved X11 activation prerequisite in future GUI qualification plans.
- Complete later teaching templates and pairings (Watchful Keeper and Roaming
  Reacquirer), multi-process capability/quota UX, broader board/seed/timing
  coverage and the supported Python 3.10–3.14 matrix.
- Qualify broader usability, accessibility, keyboard/reduced-motion behavior
  and human desktop interaction. Wayland and additional Linux distributions
  remain unqualified by this bounded X11/Xvfb evidence.
- Complete wheel assets/clean installs, Windows installer/frozen executable
  acceptance, Linux packaging and remaining alpha-wide release obligations.

These entries initiate no implementation, issue publication, regression rerun
or research work. Scientific authority, payoff superiority, balance and
unrestricted public release readiness are not conferred by M1 technical PASS.

## 8. Recording and publication boundary

This acceptance action creates only this consolidated documentation record.
Accepted product source, Windows/Linux qualification records and historical
research evidence remain unchanged. No regression campaign or native workflow
was repeated to create this record.

Only `docs/v6/V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md` is authorized for staging.
Generated match ZIPs, executed-source snapshots, excluded private-path
screenshots, private research material, backups, local settings and temporary
files remain outside this record's publication scope. Documentation references
and Git hygiene are validated before returning the staged manifest. Commit and
push require separate Project Lead authorization.

[windows]: V6_ALPHA_M1_6_WINDOWS_QUALIFICATION_01.md
[linux]: V6_ALPHA_M1_6_LINUX_QUALIFICATION_01.md
