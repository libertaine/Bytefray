# Classic Ruleset Retirement

**Status: implemented on `feature/retire-classic-ruleset`; PASS WITH CONDITIONS
for development integration. Release qualification remains HOLD.** See the
[final independent approval](CLASSIC_RULESET_RETIREMENT_FINAL_APPROVAL.md) and
[historical qualification report](CLASSIC_RULESET_RETIREMENT_QUALIFICATION.md).
Not merged, not pushed, not released.

After Bytefray 5.1.0-alpha.1, Classic (`bytefray-rules-4`) is retired as an
executable, selectable, supported Ruleset. Active Sensing (Alpha)
(`bytefray-rules-6-alpha1`) is the only Ruleset for new matches, evaluations,
tournaments and agent development. This is a deliberate product
simplification and compatibility break; the retired implementation was not
kept behind a hidden switch.

The published `v5.1.0-alpha.1` release (tag, wheel, sdist, Windows
installer) is the recovery baseline and is unchanged. It is the last release
that runs Classic.

## What changed

### Engine and CLI

- `bytefray-rules-4` is no longer in the executable registry
  (`ruleset_policy._RULESET_POLICIES`). It joins the historical, read-only
  identities: results, replays, traces and evaluations recorded under it stay
  readable and correctly labeled.
- An omitted Ruleset means Active Sensing everywhere: `bytefray run`,
  `agents test`, `agents validate`, `agents evaluate`, `tournament`,
  `NativeMatchService`, the process runtime, the agent worker and placement.
  `OMITTED_RULESET_CANDIDATES` names only Active Sensing. The public
  `resolve_omitted_ruleset_id` compatibility wrapper remains and delegates
  to the authoritative metadata resolver; explicit selectors pass through
  unchanged for downstream validation.
- Naming a retired Ruleset is rejected, never remapped. The CLI reports, for
  example, `Ruleset 'bytefray-rules-4' is retired and cannot run new
  matches. Expected bytefray-rules-6-alpha1. Bytefray 5.1.0-alpha.1 still
  runs it; its recorded artifacts remain readable.` The Python API raises
  `UnknownRulesetError` with the same text, and evaluation presets naming a
  retired Ruleset fail to load with it.
- `agents test`'s internal reference opponent is the bundled Watchful
  Keeper (`v6_watchful_keeper`); `bytefray run` defaults to Window Scout
  against Watchful Keeper.
- Pairwise evaluation under Active Sensing uses the same seeded-placement
  methodology (schema/identity 7, arena pinned to 512) with its own
  alignment label, `ruleset_v6_alpha1_seeded_placements`.
- The identity and semantics of `bytefray-rules-6-alpha1` are unchanged; no
  policy field, golden or fixture of it was edited.

### Designer

Simple, Advanced, Development and Evaluation no longer have a Ruleset
control (`app/widgets/ruleset_combo.py` is deleted). There is no
single-option dropdown in its place. Each launch names
`DESIGNER_RULESET_ID` explicitly rather than relying on the engine default,
and each match requests a trace so its replay opens with delivered
information views and can be exported to Spectator. Agents the Ruleset
cannot run (Agent API v1, VM) are still listed for inspection, are disabled
for execution, and show an explanation. The workflows themselves (Simple,
Advanced, Development, Evaluation, Tournament) are unchanged.

### Agents and packaging

| Starter | Disposition |
| --- | --- |
| `v6_window_scout`, `v6_watchful_keeper`, `v6_roaming_reacquirer` | Installed and packaged; the whole default roster |
| `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`, `v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker` | Not installed, not in the wheel or sdist, not collected into the frozen executables. Sources kept in `battle_engine/data/starter_agents/` as the research benchmark population (`tools/research/...` reads them); identities unchanged |
| Repository `agents/` (`Nemesis`, `hydra`, `hydra_alpha2`, `nemesis_alpha2`, `viper`) | Unchanged. Never packaged; used by research-scale tests |

Packaging is driven from one list, `battle_engine.starters.STARTER_AGENT_NAMES`:
`pyproject.toml` package data, `MANIFEST.in` prunes, `tools/check_wheel.py`'s
forbidden list and `tools/packaging_data.collect_starter_agents` (used by
all three PyInstaller specs). Agents a user already installed from an
earlier release stay in their catalog; Classic agents that declare no
`sense` capability still run under Active Sensing, but they were written
for passive visibility and play poorly without it.

### Replay

Active Sensing replays are created, persisted, indexed by Replay History,
verified, played in the Pygame Replay Viewer and exported to Spectator as
before; the replay, result and trace formats are unchanged. Classic replays
stay readable as historical artifacts; the passive-visibility spectator
modes remain for historical and research replays.

### Tests and documentation

Classic-only live tests were removed (Classic starter, exploit-characterization
and quorum suites). The stable-equivalence and K1 capture suites now preserve
their original 23 and 15 golden records as passive data guards; all 12 Phase-C
digest prefixes and the original historical evaluation identity/planning
expectations are retained separately from current Active Sensing coverage.
tests of shared behavior were retargeted to Active Sensing; research tests
that used Classic as a passive control now use
`bytefray-rules-6-research-scale`, which is field-identical to Classic's
policy. Tests that can only reproduce Classic-era research matrices (E2,
R3 and parts of E3/E8) have explicit retirement skips. All 90 E3 golden
rows remain intact; only the 30 Classic live reproductions skip. The two
Classic SENSE admission cases retain their original identity rather than
being reassigned to another research Ruleset. H1 parameter-forwarding
coverage runs unchanged historical schema probes as temporary user agents
under Active Sensing. README,
ARCHITECTURE, AGENTS, COMPATIBILITY, COMPONENT_VERSIONING, ROADMAP,
FUTURE_PLANS, the authoring guides, schema references, the `agents test`
spec (§8.1 amendment) and CHANGELOG describe the new state. Archived and
research documents, frozen evidence and E9 material are untouched.

## What still runs Classic-identical gameplay

`bytefray-rules-6-research-scale` (and the other research identities) remain
executable for research tooling only, through
`bytefray agents evaluate --ruleset <exact id>` and the Python API. Its
gameplay is field-identical to Classic. It is not a product feature, has no
display name, is offered by no Designer surface, and nothing resolves to it
by default. Some research runners (`tools/research/v6/experiment_harness.py`,
the E2 matrix's Classic arm, V5 research runners) still name
`bytefray-rules-4` as their default and now fail with the retirement error;
reproducing those studies requires 5.1.0-alpha.1, as their frozen records
already pin.

## Recovering Classic

Install Bytefray 5.1.0-alpha.1 (or 5.0.0) from its GitHub release, or check
out `v5.1.0-alpha.1`. Every Classic artifact recorded by any release remains
readable on this line.

## Decisions reserved for the project lead

- **Version number.** [COMPONENT_VERSIONING.md](../COMPONENT_VERSIONING.md)
  §4.1 classes removing an executable stable Ruleset and changing the
  default Ruleset as MAJOR. The proposed
  [development record](BYTEFRAY_DEVELOPMENT_COMPATIBILITY.md) carries
  `6.0.0-alpha.1` only as a placeholder.
- **Installer inputs.** `tools/installer.iss` and `tools/build_win.ps1` still
  name the 5.1 compatibility record and 5.1 product identity; they change
  with the version decision, not before it.

## Measurements

Measured against `development/post-5.1-alpha` at `f127be7` (the commit
tagged `v5.1.0-alpha.1`).

The completed non-E9 headless run reports **7,393 passed, 8 failed,
76 skipped, 13 deselected**. All eight failures also occur in the baseline
and concern E8's frozen source/qualification checks. E9 was not rerun.
Final focused checks after the bounded packaging/test amendments report
**96 passed, 2 explicitly retired Classic cases skipped**; these overlap
the broad run and must not be added to it. All **36 GUI modules** complete
with **576 passed**, with the baseline Windows exception diagnostic still
present in the native module. Ruff, both mypy checks, wheel/sdist contents,
and built-wheel match/replay/Spectator verification pass.

The Linux packaging workflow now uses the current starters and checks
replay/result agreement under Active Sensing. Its shell syntax and embedded
assertions were checked on Windows; no native Linux qualification is claimed.
The full failure ledger, inventory, artifact hashes, and remaining conditions
are recorded in the [qualification report](CLASSIC_RULESET_RETIREMENT_QUALIFICATION.md).

The qualification report above records the October 26 candidate. The subsequent
independent HOLD review and its bounded corrections are tracked in the
[remediation report](CLASSIC_RULESET_RETIREMENT_REMEDIATION.md); the original
qualification evidence is preserved as a separate historical ledger.
