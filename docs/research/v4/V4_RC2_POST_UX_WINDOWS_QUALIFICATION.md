# Bytefray v4 RC2 — Post-UX Windows Qualification Addendum

Recorded: 2026-09-08

- Branch: `v4-rc2-development`
- Version: `4.0.0-rc2`
- Qualified source: `b9e0766fe963dd5579376c082e6a92dbef39b57e`

This addendum records the human completion of the installed-Windows Phase 5
walkthrough after the RC2 → final UX Phases 1–5 and the Phase 5B scoring-default
remediation. The earlier [Windows pygame-ce packaging report](V4_RC2_WINDOWS_PYGAME_CE_PACKAGED_QUALIFICATION.md)
covers a different source revision; its historical results remain unchanged.

## Qualification status

```text
SOURCE QUALIFIED
WINDOWS ARTIFACTS BUILT
INSTALLED WINDOWS INTERACTIVE QUALIFICATION PASSED
Linux packaged qualification required
PUBLICATION NOT PERFORMED
```

**Linux packaged qualification for the current post-UX candidate remains
outstanding.** Older Linux RC1/RC2 qualification predates these UX changes and
does not qualify this source. Bytefray 4.0.0 final is not fully qualified.

## Source provenance

Before this documentation-only update, HEAD exactly matched the qualified
source above. Each commit below was resolved to its full ID and confirmed as
an ancestor of HEAD. Package metadata still declares `4.0.0-rc2`.

| Phase | Full commit ID | Subject |
|---|---|---|
| 1 | `d4a70e5641d1ce5a3bfa3a1b5d8cce47186ef941` | ux(rc2): Phase 1 terminology and inline guidance pass |
| 2 | `8a75469ac98b7f075e8a1a415f8588100103057b` | ux(rc2): Phase 2 ruleset-driven match setup |
| 3 | `ae56c3c2524ecd395a9d69b62b77947fb920f7cb` | ux(rc2): Phase 3 replay workflow cleanup |
| 4 | `9ef89e932c97f374b749954f3713800fb7d23e0d` | ux(rc2): Phase 4 Advanced multi-agent roster |
| 5B | `b9e0766fe963dd5579376c082e6a92dbef39b57e` | fix(designer): defer Advanced scoring to the engine's own defaults |

## Previously reported automated and build evidence

The task supplied these results from the completed qualification of the source
above. They are retained as prior evidence, not new test runs in this
documentation session and not evidence of human interaction.

| Check | Previously reported result |
|---|---|
| Headless | 2966 passed, 14 skipped, 3 deselected |
| GUI | 303 passed, 6 deselected |
| Focused Phase 1–5 | 79 passed |
| Ruleset / compatibility | 49 passed, 1 skipped |
| Replay | 45 passed, 1 deselected |
| Multi-agent + renderer | 358 passed |
| mypy engine | Clean |
| mypy client | Clean |
| ruff | Two pre-existing RUF012 findings only; zero new findings |

The prior qualification reported successful builds of:

- `Bytefray-Setup-4.0.0-rc2.exe`
- `bytefray-4.0.0-rc2-windows.zip`
- `bytefray-4.0.0rc2-py3-none-any.whl`
- `bytefray-4.0.0rc2.tar.gz`

All four artifacts were found under the locally ignored `dist/` directory
during this record update. They are not included in the documentation commit.

## Human operator interactive Windows qualification

**Operator-reported interactive Windows Phase 5 checklist: PASS.**

The operator reports installing the newly built `4.0.0-rc2` candidate from the
qualified source and running through the Phase 5 Windows tests with **no issues
encountered**. The task explicitly establishes that this attestation covers the
checklist items below, including the corrected scoring defaults.

Every PASS below is based on that operator attestation. These checks were not
performed by the coding agent, automated, or inferred from test-suite results.
The recording date above is not a separately established test execution date.

| Gate | Checklist items covered by operator attestation | Result |
|---|---|---|
| Installer / installed application | Packaged installer completed successfully; installed Agent Designer launched normally; installed Replay Viewer shortcut was available | **PASS** |
| Literal Start Menu Replay Viewer | Launched through the installed Windows shortcut; visible no-replay state appeared; application did not flash and disappear; Open Replay workflow and replay playback worked | **PASS** |
| Simple workflow | Match configuration worked; Ruleset-controlled agent filtering behaved correctly; Arena Size terminology appeared correctly; match ran successfully; View Last Match opened the just-completed match | **PASS** |
| Advanced Ruleset-first workflow | Ruleset appeared before Agent A/B; compatible-agent filtering worked; changing Ruleset behaved correctly | **PASS** |
| Advanced scoring/default presentation | Installed candidate displayed canonical defaults: Kill Weight = 5; Territory Bucket Size = 64 | **PASS** |
| Agent Params / Replay Browser | Explanatory presentation was usable; old fabricated speed/aggression examples were absent; Choose Replay..., View Replay, and replay location workflow functioned | **PASS** |
| Three-agent Advanced workflow | Add Agent exposed Agent C; compatible Agent C selection worked; 3-agent match launched successfully; Results represented all three entrants; 3-agent replay opened/rendered; Remove Agent returned Advanced to two entrants; subsequent two-agent workflow remained functional | **PASS** |
| Replay lifecycle | Match A → View Last Match → A; Match B → View Last Match → B | **PASS** |

No deleted/missing-replay test result is asserted: the supplied checklist does
not establish that this additional case was required and performed. No more
detailed observations, screenshots, or machine-specific results were supplied.

## Release boundary

The installed-Windows interactive gate is now satisfied. Fresh Linux packaged
qualification for this post-UX source is still required before final release
preparation or publication. This addendum and the README multi-agent wording
correction change documentation only; the qualified source revision remains
`b9e0766fe963dd5579376c082e6a92dbef39b57e`.

PUBLICATION NOT PERFORMED
