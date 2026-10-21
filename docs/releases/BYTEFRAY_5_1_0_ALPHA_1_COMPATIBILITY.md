# Bytefray 5.1.0-alpha.1 — Component Compatibility

**Status: candidate.** This is the record for the 5.1.0-alpha.1 release
candidate: the package reports `5.1.0a1`, and a Windows installer candidate
bundles Bytefray Spectator `0.1.0-alpha.1`. It is not a published release.
Publication needs separate project-lead approval, and only then does this
record become **released**.

Links on this page are relative to `docs/releases/` in the Bytefray
repository. The Windows installer copies only this page and its JSON record
into `<install>\docs`.

The authoritative record is
[`BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json`](BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json).
The summary below is generated from it by `tools/release_compatibility.py`,
which also checks every claim the code can confirm: Ruleset exposure on each
surface, display names, Agent API and format versions, and the Spectator
presentation contract. `engine/tests/test_release_compatibility_record.py`
runs that check, so the record, this page and the code cannot silently
disagree. Edit the JSON, then run:

```bash
python tools/release_compatibility.py docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json --write
```

Versioning rules for every component are in
[COMPONENT_VERSIONING.md](../COMPONENT_VERSIONING.md).

## Qualified and unqualified claims

The code confirms the component versions and the Ruleset exposure below.
That makes them accurate descriptions of this development line. It does not
make them qualified for release. Qualification evidence today:

- **M1 (Verified Sensing Exchange)** is technically accepted: Windows AMD64
  and Linux X11/Xvfb qualification
  ([final acceptance](../v6/V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md)).
- **M2-2, M2-3 and M2-4** (Watchful Keeper, Roaming Reacquirer, Replay and
  Usability) are technically accepted with conditions.
- **M2-5 technical and platform qualification** is accepted — PASS WITH
  CONDITIONS — for the published `bb6c4b8` source, now merged into this line
  ([closure](../v6/V6_ALPHA_M2_5_CLOSURE_01.md)). It covers Windows, Linux
  WSL2/WSLg X11 and an Ubuntu Wayland session through XWayland. Native Ubuntu
  on Xorg is not qualified. M2-6 human evaluation is deferred to 5.2.
- **Spectator integration** has automated verification and a real Designer
  end-to-end launch on Windows. It has no native Linux desktop run.
  Spectator `0.1.0-alpha.1` is bundled with the Windows installer candidate
  and is not separately published.
- **The 5.1.0-alpha.1 Windows installer candidate** is qualified separately;
  the results and any conditions are in the repository's
  `docs/releases/5_1_ALPHA1_WINDOWS_INSTALLER_QUALIFICATION.md`.
  Linux distribution of 5.1.0-alpha.1 has its own, separate qualification.

## Summary

<!-- BEGIN GENERATED: tools/release_compatibility.py -->
| Component | Declaration |
| --- | --- |
| Status | **candidate** — Release-candidate record. The package version is 5.1.0a1, and a local Windows installer candidate has been built from this line. It is not a published release: publication needs separate project-lead approval. |
| Application | Bytefray 5.1.0-alpha.1 (Python package `5.1.0a1`, tag `v5.1.0-alpha.1`); previous release 5.0.0; Python 3.10, 3.11, 3.12, 3.13, 3.14 |
| Default Ruleset | Classic (`bytefray-rules-4`) |
| Offered Rulesets | Classic (`bytefray-rules-4`) — stable, default when no Ruleset is chosen; Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) — experimental, explicit only; never selected automatically |
| Research Rulesets | 14, selectable only by `bytefray agents evaluate --ruleset <exact id>` or the Python API. Research reproduction only. Not a product feature; no stability or compatibility promise. |
| Historical Rulesets (readable, not executable) | `bytefray-rules-1`, `bytefray-rules-2`, `bytefray-rules-2-alpha1`, `bytefray-rules-2-alpha11`, `bytefray-rules-3-alpha1`, `bytefray-rules-4-alpha1`, `bytefray-rules-4-alpha2` |
| Agent API | v2 executable; v1 retired from execution; manifest capabilities v1 (`sense`) |
| Replay format | `battle2.replay` writes 4; reads 2, 3, 4 |
| Result format | `battle2.result` writes 2; reads 1, 2 |
| Trace format | `bytefray.agent_trace` writes 2; reads 1, 2 |
| Other persisted formats | `bytefray.evaluation` writes 7 (identity 7); `battle2.tournament` writes 1; `bytefray.agent_package` writes 1 |
| Spectator application | Bytefray Spectator 0.1.0-alpha.1: proposed first distribution version, bundled with the 5.1.0-alpha.1 Windows installer candidate; not separately tagged or published. Source `libertaine/Bytefray-Spectator` `designer-integration` `14089a7`; Windows build `bytefray-spectator.exe` SHA-256 `8a3bd1a48430a0edd1faf8ca5c5b287ed1ecd06975c4e683f273562d428fd602` (Godot 4.7.2.stable). The Windows installer bundles this build in `<install>\bin\bytefray-spectator\`, pinned by `tools/spectator_companion.json`, and Designer finds it there automatically. `BYTEFRAY_SPECTATOR` still overrides it or turns Spectator off. Source and wheel installs find Spectator through `BYTEFRAY_SPECTATOR`, `<data root>/spectator/` or `bytefray-spectator` on `PATH` |
| Spectator presentation protocol | `bytefray.spectator.manifest`: Bytefray writes 2, Spectator reads 1, 2; provenance `bytefray_match`; documents broadcast `bytefray.spectator.broadcast` v1, agent_a `bytefray.spectator.agent_view` v1 |
| Spectator match support | `bytefray-rules-6-alpha1` with entrants A, B; perspectives broadcast, agent_a |
| Designer viewer dispatch | Prefers Spectator: View Last Match, Development test replay, Evaluation replays. Always Pygame: Tournament results, Replay History, Advanced replay file browser |

| Surface | Rulesets offered for new matches |
| --- | --- |
| bytefray run | Classic (`bytefray-rules-4`); Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents test | Classic (`bytefray-rules-4`); Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents validate | Classic (`bytefray-rules-4`); Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents evaluate | Classic (`bytefray-rules-4`) |
| bytefray tournament | Classic (`bytefray-rules-4`) |
| Designer Simple | Classic (`bytefray-rules-4`) |
| Designer Advanced | Classic (`bytefray-rules-4`); Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Development | Classic (`bytefray-rules-4`); Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Evaluation | Classic (`bytefray-rules-4`) |

| Platform | Bytefray | Spectator |
| --- | --- | --- |
| Windows 11 AMD64 | Primary target. M1 qualified (M1-6A). M2-5 technical/platform qualification accepted PASS WITH CONDITIONS (published bb6c4b8, merged into this line). Distributed as a per-user Inno Setup installer (`Bytefray-5.1.0-alpha.1-Windows-x64-Setup.exe`) that installs beside Bytefray 5.0; its qualification is recorded in docs/releases/5_1_ALPHA1_WINDOWS_INSTALLER_QUALIFICATION.md. | 0.1.0-alpha.1, built from tracked presets and bundled with the Windows installer; automated self-checks run on every Windows build. |
| Linux x86_64 | Headless-first wheel. Designer qualified on X11/Xvfb for M1 (M1-6B). M2-5 accepted PASS WITH CONDITIONS on WSL2/WSLg X11 and an Ubuntu Wayland session through XWayland; native Ubuntu on Xorg not qualified. | Executable built; headless checks only (WSL Ubuntu 24.04). No native desktop run. |
| macOS | Not qualified. | Not built or qualified. |
| Windows ARM64 | Not supported (AMD64 packaging only). | Not built. |

**Known limitations**

- Bytefray Spectator presents only completed two-entrant (A, B) Active Sensing (Alpha) matches; every other match opens in the Pygame viewer.
- Spectator offers two perspectives: Broadcast and Agent A delivered information.
- In Spectator 0.1.0-alpha.1, Tab moves keyboard focus between controls instead of switching perspective, although the on-screen key hint lists it, and Space presses a focused button instead of playing or pausing. The perspective list and the playback buttons work.
- The Pygame viewer remains available for every supported workflow. Designer opens it instead of Spectator when Spectator is absent or turned off, does not support the match, or fails to export or launch. Once Spectator has started, Designer never reopens the match in Pygame; an immediate nonzero Spectator exit shows a warning.
- The Pygame Active Sensing views (Agent A, Agent B, Omniscient) are a separate capability from Spectator's perspectives; entrant C has no delivered-information view.
- Three-entrant or larger Spectator presentation is deferred.
- Human comprehension evaluation of Active Sensing is deferred to 5.2.
- Classic (`bytefray-rules-4`) stays the default on every surface; Active Sensing (Alpha) is never chosen automatically, including when a sensing starter is selected.
- Spectator export time grows with the square of match length (about 40 s for 477 ticks); Designer prepares exports in the background, and a prepared presentation is reused from the data root's cache.
- The Windows installer and executables are not code-signed, so Windows SmartScreen may warn before the first run.
- The Windows installer installs for one Windows account (no all-users option) and supports AMD64 only.
- The Windows installation folder's path must stay under about 150 characters: the deepest installed file lies 107 characters below it, and Setup stops and rolls back when a path would exceed the Windows 260-character limit.
- A Windows application that finds its installation record missing or damaged, or its data folder overlapping its program folder, refuses to start: the command-line programs print the explanation, and the windowed applications show it in a generic "Unhandled exception in script" dialog.
- Agent Designer's entrant C selector has no accessible name for screen readers; accessibility has not been reviewed for this Alpha.
- Bytefray Spectator keeps its own settings and logs in `%APPDATA%\Godot\app_userdata\Bytefray Spectator`, outside the Bytefray data root; uninstalling leaves them, as it leaves the data root.
- The standalone sensing demonstration generators (`sensing_demo` and the keeper/reacquirer scenario verifiers) remain source-only.

**Unsupported**

- Active Sensing (Alpha) in Designer Simple, in evaluation (CLI and Designer) or in tournaments.
- Executing Agent API v1 agents, VM/blob agents or Redcode/pMARS warriors; their recorded artifacts stay readable, and Bytefray 5.0.0 still runs them.
- New matches under the historical Rulesets listed as readable but not executable. The two retired research Rulesets remain executable for research reproduction only.
- Spectator for Classic matches, three-entrant matches, tournaments or Replay History launches.
<!-- END GENERATED -->
