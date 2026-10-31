# Classic retirement final independent approval — 2026-10-27

**Decision before staging: PASS WITH CONDITIONS for development integration.**
All five identified development issue areas are closed. The branch is ready
for controlled local commits and subsequent PR review against
`development/post-5.1-alpha`. Release qualification remains **HOLD**.

This review independently inspected the inherited implementation and reran
bounded checks after the final diagnostic correction. It did not restart
implementation, execute E9, or repeat the full headless, GUI, packaging or
native platform campaigns. Earlier reports remain historical evidence with
their original scopes and limitations.

## Reviewed baseline and scope

- Worktree: `D:\Projects\BATTLE2\work\bytefray-post-alpha`.
- Branch: `feature/retire-classic-ruleset`, without an upstream.
- Original HEAD and local development baseline:
  `f127be70e7ed88449c1b737f4675e1453ec8de45`.
- Before staging, the working patch, staged patch, index entries and flags,
  status, HEAD and refs were captured externally. The inherited meaningful
  staged changes are retirement deletions/renames; intent-to-add entries and
  the two restored golden modules were inventoried explicitly. No unrelated
  staged change belongs in these commits.
- All 1,947 captured source/data files match the latest diagnostic-remediation
  baseline plus its five final snapshots, with zero mismatches. The explicit
  reviewed inventory excludes experimental agents, protected research data,
  fixtures, archives and generated build artifacts.

## Findings closed

1. **Historical evaluation identity.** Schema-7 payloads retain their original
   identities. Seed 1 in arena 512 reconstructs **(380, 263)** independently of
   executable registration. Historical reconstruction does not authorize a
   new Classic evaluation; invalid reconstruction remains an explicit error.
2. **Frozen integrity coverage.** Original literal tables compare equal to
   the original HEAD: **15 K1**, **23 promotion**, **12 Phase-C** and **90 E3**
   records. Independent in-memory mutations are rejected by the actual K1,
   promotion and Phase-C passive guards. No golden data was regenerated.
3. **Native qualification dependencies.** Both maintained native scripts
   compile and use current Designer interfaces and Active Sensing starters.
   The direct negative helper used by the Linux workflow and its real module
   entry point both pass. This is Windows/helper and static evidence; the
   Linux GUI workflow was not executed.
4. **Public compatibility wrapper.** `resolve_omitted_ruleset_id` remains
   exported with its positional calling contract. Generator/duplicate input,
   explicit selector passthrough and fail-closed unsupported omitted rosters
   are covered. Omission selects Active Sensing.
5. **Expected configuration diagnostic.** Only resolver
   `UnknownRulesetError` becomes `ruleset_unavailable / configuration`.
   The original message and chained exception are preserved. Unexpected
   resolver errors and an unexpected preflight `UnknownRulesetError` remain
   `validation_internal_error / internal`. Rejection precedes capability
   preflight, import, worker startup and trace opening. CLI rejection exits
   **2**, creates no execution artifacts and preserves existing trace bytes.
   Tests and helper assertions now enforce the documented diagnostic contract.

Active Sensing is the sole product Ruleset; Classic is unregistered and
explicit requests remain rejected. All 15 retained policy-constructor ASTs,
including Active Sensing, match the original baseline. Research identities
remain separate from product choices.

## Fresh independent verification

| Check | Result |
| --- | --- |
| Diagnostic regressions | **11 passed**, 44 deselected |
| Bounded regression collection | **397 passed**, no failures, errors or skips |
| Direct negative helper | Passed |
| Determinism/negative module entry point | Passed; identical replay SHA-256, 103 replay lines, 1,600 logical trace records |
| Ruff | Passed |
| Engine / client / helper mypy | Passed: 107 / 20 / 1 source files |
| Original tables and corruption tripwires | Passed |
| Retained evidence manifest verification | Zero mismatches: 723 diagnostic-remediation, 629 preceding independent-review, 716 helper-remediation, 316 earlier remediation and 2,527 continuation entries |

The 11 diagnostic cases overlap the 397-case collection; do not add these
totals. The bounded collection is the one enumerated in the final diagnostic
addendum of
[the correction report](CLASSIC_RULESET_RETIREMENT_FINAL_QUALIFICATION_FIX.md).
The E3 cases are passive metadata checks; E9 and live E3 research were not run.
Whitespace checks honor the history adapter's existing `-text` CRLF format
using command-scoped `core.whitespace=cr-at-eol`; no Git configuration or line
endings were changed.

## Controlled commit handoff

The reviewed changes are grouped as three local commits: the integrated
engine/CLI, Designer, catalog/packaging and historical-regression migration;
the shared/native qualification helpers; then documentation and qualification
records. These groups keep the interdependent product migration together.
Each group requires explicit reviewed paths, staged patch and name-status
inspection, and a staged whitespace check before committing. The external
commit ledger records exact SHAs and post-commit verification.

This review corrects stale statements in the retirement overview and changelog
that incorrectly said the compatibility wrapper was removed. It adds this
approval record; the approved implementation is unchanged.

## Remaining conditions

Native Linux/X11 execution, a new Windows installer, the retained Windows
`0x8001010d` diagnostic and the project-lead version decision remain open
release gates. Prior baseline E8 freeze failures and stale shared-environment
package metadata retain their documented dispositions. The proposed
development compatibility version remains a placeholder; the application
version and published Alpha release inputs are unchanged.

**E9 remains LOCKED. Requirement C remains NOT ESTABLISHED.**
No push, merge, tag, publication or PR creation is authorized by this approval.

Fresh baseline snapshots, reviewed file inventory, logs, JUnit, integrity
audit, commit ledger and final verification are retained outside the repository:

`C:\Users\rasat\AppData\Local\Temp\bytefray-final-approval-qv2hgynb`
