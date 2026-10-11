# M1-6A Windows closure evidence

The report is [Windows Qualification 01](../../V6_ALPHA_M1_6_WINDOWS_QUALIFICATION_01.md).
Project Lead accepted the functional qualification; the closure audit reconciled
the inventory and executed the missing compatibility coverage separately.

| Record | Exact selection | Outcome |
| --- | --- | --- |
| `regression.xml` | `regression_nodes.txt`; modules in `regression_modules.txt`; default `not gui` marker | 3,199 passed, 19 skipped; 7 GUI deselected in the original log; 380.624s |
| `supplemental_compatibility.xml` | `supplemental_nodes.txt`; 15 modules; no historical partition nodes | 328 passed; separate closure run |
| `client_gui.xml` | `gui_nodes.txt`; `client/tests -m gui`, native Windows SDL | 7 passed, 550 deselected; separate closure run |

No total combines overlapping focused qualification runs. The original broad
campaign was not rerun. The 72 Disposition 03 historical nodes remain a separate
M1-1 qualification: 71 passed in its retained baseline JUnit, plus one passed in
the existing entropy-prohibiting plugin process as recorded in adopted
[Disposition 03](../../V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md).

`inventory.json` lists the 21 modules accounting for the exact 906 difference,
all 123 excluded engine modules, their historical partition and supplemental
counts, every broad module, every skip reason category and all seven GUI nodes.
Counts for omitted research cases come from the retained M1-1 current JUnit;
those modules have no test-source changes between M1-1 and the closure HEAD.
The 4,124 figure reproduces 3,218 plus those 906 cases, but is not a valid
uniform product-scope count. No surviving original 4,124 collection command is
claimed. Required inventory and E8 compatibility cases embedded in excluded
modules were an actual coverage gap, resolved by the supplemental selection.

XML exports preserve original suite totals, timestamps, case identities,
outcomes and timings. They omit workstation hostnames and captured streams;
skip text containing local filesystem paths is replaced by its documented
reason category. Deliberate malicious-input vectors such as `C:/evil.py` remain
unchanged test names. `evidence_hashes.json` binds exports to original local
XML/log hashes and lists all 19 original screenshot digests. Raw logs/XML,
pre-closure report, earlier unsuccessful witnesses and private evidence remain
local and unchanged. Re-export with:

```powershell
& '.\.venv\Scripts\python.exe' -B tools/qualification/reconcile_windows_inventory.py
```

The original completed-match screenshots `06` and `07` contain the local user's
temporary path and are preserved locally without staging. The other 17 images
are authentic original captures. None was generated, edited or recaptured for
staging. Misleading original control-witness filenames remain unchanged:
frame 1 is tick-zero TICK_END, frame 2 callback 1 OBSERVATION, frame 3 callback 1
SENSE ACTION (pending), and frame 4 active playback at callback 7 with delivered
historical knowledge. These captures prove forward stepping and unpause;
other controls are supported by separate automated controller/SDL evidence.

The seven GUI-marked cases include four native-window loop checks using test
event injection, two surface-level checks and one mocked fallback integration
check. They are not seven independent manual GUI interactions. The separate
unmocked viewer subprocess witness supplies the external window evidence.

Both closure test runs retained the expected `Unknown config option: cache_dir`
warning caused by disabling the cacheprovider plugin for evidence preservation.
There were no failures, errors, skips or xfails in either closure run.
