# Bytefray V6 M2-5 qualified source: public summary

2026-10-17. **M2-5: PASS WITH CONDITIONS.** Project-lead acceptance and
publication authorization preserve the technical candidate for independent
native Ubuntu confirmation. **M2-6 remains paused/HOLD pending actual human
evaluation. Native Ubuntu is not yet qualified.** This is neither unrestricted
Linux qualification, M2 completion, nor a V6 stable release or version promotion.

This is a public derivative of the retained M2-5H Qualification Report 01,
not the full evidence package. The original report and local evidence remain
unchanged and are not published here. Its raw SHA-256 is
`e65131403bad5b9de8e9616f106ab6f718d4f43ff51f8da176cc91475252e208`.
The summary omits machine paths, private/local evidence links and disposable
harnesses. Earlier committed planning/entry documents describe their historical
authorization state; the current acceptance is the one stated here.

The parent is published M2-4 `10c3530f035335b89716d5bda7ce138440767a71`.
The accepted candidate is that parent plus exactly two corrected files:

| File | Accepted raw SHA-256 |
| --- | --- |
| `app/views/replay_history.py` | `6994479d4256dd49dc74750d705ddc3a12917c469a839eb6b557ed1391c7df10` |
| `tests/test_v5_replay_history_qualification.py` | `b786ebcce71915f267cf1fa9df518b79319d46a1c89370b113dd358e1741f340` |

PD-1 extends the existing Qt date-bound fallback to catch `ValueError` as well
as `OSError` and `OverflowError`; six regression cases cover both bounds and
all three exceptions. The fixture correction uses explicit local noon for
local-calendar range expectations and retains the original UTC-midnight-crossing
instant in two independent cases. It changes no production timezone semantics.
No other source correction is omitted.

The [source manifest](V6_ALPHA_M2_5_SOURCE_MANIFEST_01.json) binds all 1,249
retained source/test identities and the four inherited curated replay bodies.
The original qualification source map was rehashed before transfer; the complete
source map also matches this isolated checkout. Five inherited PowerShell files
have CRLF working bytes and LF Git blobs under the existing attributes; no
normalization or gameplay changes were made. The two corrected files have exact
accepted bytes in both checkout and Git blobs.

Retained qualification includes the corrected 25-case date/calendar matrix on
Windows and Linux default, Tokyo and Indianapolis; Windows root GUI 539 passing
identities; Linux 538 passing identities and one standing Windows-only skip;
client GUI 13 per platform; and broader product/compatibility partitions.
These partitions overlap and must not be summed. Existing failures and corrective
passes retain separate dispositions. This publication does not rerun the full
campaign or claim new native Ubuntu results.

M2-5H completed the remaining Designer, History handoff, guide, native capture,
cross-platform replay and performance checks on Windows and WSL2/WSLg X11.
All nine compared workflow replay pairs were byte-identical. All 396 rebuilt
views matched fresh loads; all 90 rebuild-operation records were R-a. Measured
performance was class 2 for the specified workloads, with no class-3 result.
Authoring widget steps used QTest; History, guides and viewers used native input.
Technical support covers AC01-10 and AC12 under the stated conditions; AC11
requires M2-6 human evaluation.

Conditions remain explicit:

- Windows replay loading is approximately 12.2 seconds for selected workloads.
- Selected perspective switches take approximately 6 seconds on Windows and
  4 seconds on WSL Linux; Windows displayed "Not Responding" during measured
  C2 perspective switching. No performance optimization is included.
- History scroll, Help scroll and arbitrary timeline seek lack keyboard
  alternatives. Return does not activate the ordinary non-default guide button.
- WSLg focus required a Windows-host caption click. Linux evidence covers
  WSL2/WSLg X11 only; this is no native Ubuntu desktop qualification.
- Historical Linux crash/shutdown observations remain unresolved. The separately
  captured watchdog-thread SIGSEGV implicated periodic faulthandler dumping;
  that result does not explain or close the other historical incidents.
- Windows displays varied during qualification: earlier captures were limited
  to 1080-wide displays; later captures used 2560x1440 at 125% with pygame DPI
  virtualization. No general display-scale or accessibility certification.
- Earlier M2-3 L1-L5, M2-4 D1 and COM/tooling conditions remain as recorded in
  their committed closure documents.
- Native Ubuntu, the runtime-version matrix, packaging/installers and other
  distributions are not qualified by this branch. M2-6 human evaluation is
  incomplete and remains paused/HOLD.

All 329 frozen historical pins were verified read-only at their original
baseline; their manifests and historical bodies were not changed. Stable
`bytefray-rules-4` remains the default; Alpha 1 requires explicit selection.
No E9 activity or authority change is included.

Follow the [native Ubuntu confirmation instructions](V6_ALPHA_M2_5_UBUNTU_CONFIRMATION_01.md).

Publication validation re-ran only the focused Windows date/calendar selection:
25 passed, 11 deselected. Qt used its offscreen test default; this is regression
evidence, not a new native workflow claim. The first attempt lacked the fresh
checkout temp-parent directory and produced 16 setup errors and 9 passes; the
second attempt created that directory and passed without source changes. Both
receipts remain local, outside the published tree.
Changed-source Ruff and whitespace checks pass. The 365 retained Linux debugger
file hashes and 10 symlink targets also verify read-only; no diagnostic campaign
was executed.
