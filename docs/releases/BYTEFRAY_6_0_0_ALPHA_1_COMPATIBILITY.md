# Bytefray 6.0.0-alpha.1 — Component Compatibility

**Status: candidate.** This record describes Bytefray 6.0.0-alpha.1, the
first release after `5.1.0-alpha.1`. On this line Classic (`bytefray-rules-4`)
was retired and Active Sensing (`bytefray-rules-6-alpha1`) became Bytefray's
only Ruleset. By [COMPONENT_VERSIONING.md](../COMPONENT_VERSIONING.md) §4.1,
removing an executable stable Ruleset and changing the default Ruleset is a
MAJOR change; the project lead designated `6.0.0-alpha.1` on 2026-11-16. The
Windows 11 AMD64 installer (`Bytefray-6.0.0-alpha.1-Windows-x64-Setup.exe`,
Windows file version `6.0.0.1010`, SHA-256
`ad52c294b64b6a9089dba9d9892e1081d89f6e2547ae313879f153ed39adf1e4`) was built
and qualified from `8e574cb2d2789be18aebfe4196b520b5e131ffca` (gates G1–G8);
the copies of the release notes and compatibility record installed in
`{app}\docs\` inside that installer are the `8e574cb` build-time copies listed
in `bytefray-files.txt`. The published `5.1.0-alpha.1` keeps its own
record,
[`BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md`](BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md),
and remains the release that runs Classic. The Windows installer installs
6 Alpha beside Bytefray 5.0 and 5.1 Alpha and migrates nothing from them.

The authoritative record is
[`BYTEFRAY_6_0_0_ALPHA_1_COMPATIBILITY.json`](BYTEFRAY_6_0_0_ALPHA_1_COMPATIBILITY.json).
`tools/release_compatibility.py` checks every claim in it the code can
confirm and generates the summary below;
`engine/tests/test_release_compatibility_record.py` runs that check. Edit the
JSON, then run:

```bash
python tools/release_compatibility.py docs/releases/BYTEFRAY_6_0_0_ALPHA_1_COMPATIBILITY.json --write
```

The decision and its scope are recorded in
[CLASSIC_RULESET_RETIREMENT.md](CLASSIC_RULESET_RETIREMENT.md).

## Summary

<!-- BEGIN GENERATED: tools/release_compatibility.py -->
| Component | Declaration |
| --- | --- |
| Status | **candidate** — Release-candidate record for Bytefray 6.0.0-alpha.1, the first release after 5.1.0-alpha.1. It retired Classic (bytefray-rules-4) and made Active Sensing the only Ruleset, which docs/COMPONENT_VERSIONING.md section 4.1 classes as MAJOR; the project lead designated 6.0.0-alpha.1 on 2026-11-16. It installs beside Bytefray 5.0 and 5.1 Alpha with its own product identity and data folder, and migrates nothing. Qualified for Windows 11 AMD64 prerelease publication (Windows build 6.0.0.1010 from 8e574cb2d2789be18aebfe4196b520b5e131ffca; gates G1–G8). |
| Application | Bytefray 6.0.0-alpha.1 (Python package `6.0.0a1`, tag `v6.0.0-alpha.1`); previous release 5.1.0-alpha.1; Python 3.11, 3.12, 3.13, 3.14 |
| Default Ruleset | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Offered Rulesets | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) — experimental, the only Ruleset; used when no Ruleset is chosen |
| Research Rulesets | 14, selectable only by `bytefray agents evaluate --ruleset <exact id>` or the Python API. Research reproduction only. Not a product feature; no stability or compatibility promise. |
| Historical Rulesets (readable, not executable) | `bytefray-rules-1`, `bytefray-rules-2`, `bytefray-rules-2-alpha1`, `bytefray-rules-2-alpha11`, `bytefray-rules-3-alpha1`, `bytefray-rules-4`, `bytefray-rules-4-alpha1`, `bytefray-rules-4-alpha2` |
| Agent API | v2 executable; v1 retired from execution; manifest capabilities v1 (`sense`) |
| Replay format | `battle2.replay` writes 4; reads 2, 3, 4 |
| Result format | `battle2.result` writes 2; reads 1, 2 |
| Trace format | `bytefray.agent_trace` writes 2; reads 1, 2 |
| Other persisted formats | `bytefray.evaluation` writes 7 (identity 7); `battle2.tournament` writes 1; `bytefray.agent_package` writes 1 |
| Spectator application | Bytefray Spectator 0.1.0-alpha.1: the build bundled with the 5.1.0-alpha.1 Windows installer; unchanged on this line. Source `libertaine/Bytefray-Spectator` `designer-integration` `14089a7` (tree identical to public `main` `f62b0cb`); Windows build `bytefray-spectator.exe` SHA-256 `8a3bd1a48430a0edd1faf8ca5c5b287ed1ecd06975c4e683f273562d428fd602` (Godot 4.7.2.stable). Pinned by `tools/spectator_companion.json`, as in 5.1.0-alpha.1. `BYTEFRAY_SPECTATOR` overrides it or turns Spectator off. Source and wheel installs find Spectator through `BYTEFRAY_SPECTATOR`, `<data root>/spectator/` or `bytefray-spectator` on `PATH` |
| Spectator presentation protocol | `bytefray.spectator.manifest`: Bytefray writes 2, Spectator reads 1, 2; provenance `bytefray_match`; documents broadcast `bytefray.spectator.broadcast` v1, agent_a `bytefray.spectator.agent_view` v1 |
| Spectator match support | `bytefray-rules-6-alpha1` with entrants A, B; perspectives broadcast, agent_a |
| Designer viewer dispatch | Prefers Spectator: View Last Match, Development test replay, Evaluation replays. Always Pygame: Tournament results, Replay History, Advanced replay file browser |

| Surface | Rulesets offered for new matches |
| --- | --- |
| bytefray run | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents test | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents validate | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray agents evaluate | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| bytefray tournament | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Simple | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Advanced | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Development | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |
| Designer Evaluation | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`) |

| Platform | Bytefray | Spectator |
| --- | --- | --- |
| Windows 11 AMD64 | Primary target. Qualified for 6.0.0-alpha.1 (Windows build 6.0.0.1010 from 8e574cb2d2789be18aebfe4196b520b5e131ffca: automated suites, 135/135 Windows Sandbox installation/isolation/upgrade/uninstall checks and G7 human acceptance passed; distributed as Bytefray-6.0.0-alpha.1-Windows-x64-Setup.exe). | 0.1.0-alpha.1, unchanged. |
| Linux x86_64 | Headless-first wheel. Automated CI (core suites, X11/Xvfb GUI smoke and Ubuntu 24.04 package baseline) passes on this line; native Linux desktop not release-qualified. | Not qualified on this line. |
| macOS | Not qualified. | Not built or qualified. |
| Windows ARM64 | Not supported (AMD64 packaging only). | Not built. |

**Known limitations**

- Active Sensing (Alpha) is the only Ruleset. Classic (`bytefray-rules-4`) is retired: a request for it is rejected as retired, never remapped. Bytefray 5.1.0-alpha.1 still runs Classic.
- Active Sensing requires an arena larger than 64 cells.
- The bundled starter agents are the three Active Sensing starters (Window Scout, Watchful Keeper, Roaming Reacquirer). The V4 and V5 starters are no longer installed; copies already in a data folder are left alone and still run, but their passive contact finding never engages under Active Sensing.
- Bytefray Spectator presents only completed two-entrant (A, B) matches; every other match opens in the Pygame viewer.
- The Pygame viewer's passive Director, Fight Night and perspective modes apply only to historical and research replays; Active Sensing replays use the Agent A, Agent B and Omniscient views.

**Unsupported**

- New Classic (`bytefray-rules-4`) matches, development tests, evaluations or tournaments.
- Executing Agent API v1 agents, VM/blob agents or Redcode/pMARS warriors; their recorded artifacts stay readable.
- New matches under the historical Rulesets listed as readable but not executable. The two retired research Rulesets remain executable for research reproduction only.
- Spectator for three-entrant matches, tournaments or Replay History launches.
<!-- END GENERATED -->
