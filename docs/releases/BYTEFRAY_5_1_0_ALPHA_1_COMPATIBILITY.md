# Bytefray 5.1.0-alpha.1 — Proposed Component Compatibility

**Status: proposed.** This is the planning record for the next application
release. It is not a release, not a qualification result and not a version
bump. The installed package still reports `5.0.0`; the separately authorized
*5.1 Alpha Release Candidate Preparation* milestone decides whether and when
that changes.

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
- **M2-5 technical and platform qualification** reported PASS WITH CONDITIONS
  on a separate local lineage (`v6-alpha1-m2-5-qualified`, `bb6c4b8`). That
  lineage is not merged into the Spectator integration line, and the report
  awaits lead acceptance.
- **Spectator integration** has automated verification and a real Designer
  end-to-end launch on Windows. It has no human GUI qualification and no
  native Linux desktop run. No Spectator version has been released.
- **5.1.0-alpha.1 as a whole** has not been qualified. Release-candidate
  qualification is a later, separately authorized milestone.

## Summary

<!-- BEGIN GENERATED: tools/release_compatibility.py -->
| Component | Declaration |
| --- | --- |
| Status | **proposed** — Planning record for the next application release. It is not a release, not a qualification result and not a version bump: the installed package still reports 5.0.0 until the separately authorized release-candidate milestone changes it. |
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
| Spectator application | unreleased and unversioned; no published build. Compatible development source: `libertaine/Bytefray-Spectator` `designer-integration` `14089a7`. Separate application, not bundled; Designer finds it through `BYTEFRAY_SPECTATOR`, `<data root>/spectator/` or `bytefray-spectator` on `PATH` |
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
| Windows 11 AMD64 | Primary target. M1 qualified (M1-6A). M2-5 technical/platform qualification reported PASS WITH CONDITIONS on a separate, unmerged lineage and awaits lead acceptance. | Executable built from tracked presets; automated self-checks and a real Designer end-to-end launch pass. No human GUI qualification. |
| Linux x86_64 | Headless-first wheel. Designer qualified on X11/Xvfb for M1 (M1-6B). | Executable built; headless checks only (WSL Ubuntu 24.04). No native desktop run. |
| macOS | Not qualified. | Not built or qualified. |
| Windows ARM64 | Not supported (AMD64 packaging only). | Not built. |

**Known limitations**

- Bytefray Spectator presents only completed two-entrant (A, B) Active Sensing (Alpha) matches; every other match opens in the Pygame viewer.
- Spectator offers two perspectives: Broadcast and Agent A delivered information.
- The Pygame viewer remains available for every supported workflow. Designer opens it instead of Spectator when Spectator is absent or turned off, does not support the match, or fails to export or launch; if Spectator starts and then exits at once, Designer shows a warning but does not reopen the match in Pygame.
- The Pygame Active Sensing views (Agent A, Agent B, Omniscient) are a separate capability from Spectator's perspectives; entrant C has no delivered-information view.
- Three-entrant or larger Spectator presentation is deferred.
- Human comprehension evaluation of Active Sensing is deferred to 5.2.
- Classic (`bytefray-rules-4`) stays the default on every surface; Active Sensing (Alpha) is never chosen automatically, including when a sensing starter is selected.
- Spectator export time grows with the square of match length (about 40 s for 477 ticks); Designer prepares exports in the background.
- The frozen (PyInstaller) Bytefray build has not yet been verified with `bytefray spectator`.

**Unsupported**

- Active Sensing (Alpha) in Designer Simple, in evaluation (CLI and Designer) or in tournaments.
- Executing Agent API v1 agents, VM/blob agents or Redcode/pMARS warriors; their recorded artifacts stay readable, and Bytefray 5.0.0 still runs them.
- New matches under any historical or retired Ruleset identity.
- Spectator for Classic matches, three-entrant matches, tournaments or Replay History launches.
<!-- END GENERATED -->
