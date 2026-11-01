# Development Python support and CI qualification

Owner-approved Model B, November 2026. This governs new development after
5.1.0-alpha.1; published tags and compatibility/qualification records remain
immutable. No application, Ruleset, Agent API or format version changes here.

Minimum supported Python is **3.11**. Primary development and build Python is
**3.13**. Other qualified versions are **3.12 and 3.14**. Stable **3.15 is
advisory/unqualified**, with no package upper bound absent demonstrated
incompatibility. Python 3.10 is retired from new development support. These
are support/qualification tiers, not a claim that a particular candidate has
passed: consult its actual workflow results. Windows local runs do not prove
Linux qualification, and Xvfb does not prove native desktop qualification.

| Event | Linux product tests | Quality/package | Windows | Linux X11 |
| --- | --- | --- | --- | --- |
| Every PR | 3.13 full, qualified pins + replay; 3.11 reduced, normally resolved + replay | Ruff, engine/client/helper mypy, wheel, sdist, rebuilt-wheel inspection, clean installed-wheel smoke | 3.13 existing containment/worker/junction selection; pinned EXEs + notices | 3.13 Pygame; 3.13 Designer + PySide6 6.11.2 |
| main/development push | PR checks plus 3.12 reduced and 3.14 full | Same | Same | Same |
| Weekly Monday 05:41 UTC | Full 3.11–3.14; stable 3.15 advisory; 3.13 latest-dependency full + quality advisory | Same | 3.11/3.13 subsets, 3.13 EXEs | Pygame 3.13/3.14, advisory 3.15; qualified Designer 3.11/3.13; unpinned Designer advisory |
| Manual pre-release | Full 3.11–3.14 | Same, compatibility record and evidence guard | 3.11/3.13 subsets, 3.13 EXEs | Pygame 3.11/3.14; qualified Designer 3.11/3.13/3.14 |

Product and GUI workflows run on PRs and pushes to main/development/**;
ordinary feature pushes have no redundant push workflow. Concurrency groups
include workflow, event and PR/ref; non-PR groups additionally include run ID
to prevent GitHub from replacing pending push/manual/release runs. Only
superseded PR runs are canceled.
Push, schedule and manual/release qualification are never canceled by PRs.
GUI checks run on every PR, including workflow-only changes. Manual CI `full`
uses the full supported matrix without advisory jobs. Weekly checks and
advisories are not required for every PR. Advisory failures produce visible
step failures, warnings and retained reports; they do not block supported
qualification. They are not hidden by retries or treated as successful tests.

## Exact reduced selection

The primary job always runs the entire current product/headless suite,
including E2–E8. `tools/ci_product.py --reduced` omits only the **61 exact
module paths** in `tools/ci_reduced_inventory.json`, inventoried at f5d4683
in the completed CI simplification review. No glob is passed to pytest.
`test_ci_policy.py` verifies inventory completeness and that ordinary E2–E6
semantics, compatibility/runtime tests and the evidence guard remain selected.
No tests or expected results were changed. Weekly/release jobs use no such
exclusions. Every product checkout has full Git history.

Root conftest.py, the frozen E9 transfer inventory, the historical test
inventories and constraints, the 795-file guard, and frozen-science.yml are
unchanged. Full-suite frozen deselection remains exactly as established;
reduced jobs omit some E8 modules before collection and therefore report a
different frozen deselection count. Ignored research modules are reported
separately from pytest pass/skip/deselection counts. Never sum overlapping
ledgers. E9 remains LOCKED. Requirement C remains NOT ESTABLISHED. No E9
research is executed.

## Environments and diagnostics

`tools/product-ci-constraints.txt` pins the qualified primary Linux tools and
runtime dependencies, independently of Windows release pins. It does not
install Windows-only packages. Runtime and isolated build backends are both
constrained. Floor/other-version user resolution and weekly newest-dependency
jobs deliberately omit constraints. Production dependency declarations are
not upgraded. Windows keeps `tools/windows-build-constraints.txt` and the
canonical build's strict third-party notice verification. Linux executable
qualification uses the primary 3.13 interpreter and product constraints on
the existing Ubuntu 24.04 baseline.

Product runs use `-ra` with pytest.ini's single `-q` and upload JUnit; failures,
passes, skips and deselections remain visible. Designer keeps the complete
`-m gui tests/` selection, Qt XCB diagnostics, faulthandler (300 seconds),
the 60-minute timeout and saved output. **Issue #7 remains unresolved**:
an intermittent passing run is not proof the crash/hang was fixed.

## Release procedure and annual review

Dispatch `release-qualification.yml` on the exact candidate ref. It reuses
the full product/Windows and GUI workflows and the canonical Linux package
workflow; it publishes nothing. Separately dispatch unchanged
`frozen-science.yml` on the **same SHA** and retain the guard and historical
qualification results. The Actions UI manual/schedule definitions become
available from the default branch; before merge, verify workflows using
PR checks/static validation and dispatch candidate refs where GitHub permits.
A manual `ci.yml` run with `full: true` verifies weekly supported-matrix
selection; it does not substitute for the first real scheduled execution.

Before release, additionally require native Linux desktop qualification,
Windows installer qualification, the retained **0x8001010d** diagnostic,
version/release compatibility review and project-lead approval. Automated
CI replaces none of these. A green workflow is not release authorization.

Review Python support **annually in October**: retire EOL versions (or review
earlier if required binary wheels disappear), add the newest stable version
as advisory, and promote only after dependency-wheel availability and full
product/Designer qualification. Prefer roughly four supported versions.
Review primary/build Python at the release-version decision with qualified
PySide6/PyInstaller, constraints and notices; do not silently change release
inputs. No prerelease CPython job is required.

The review projected **264 → 34 runner-minutes per PR update**, about 87%
less, by eliminating duplicate events and redundant interpreter execution.
This is a projection from the prior review, not a measured result of this
change. Report actual job durations and summed runner-minutes separately
from workflow wall time, frozen-science runs and manual release work.
