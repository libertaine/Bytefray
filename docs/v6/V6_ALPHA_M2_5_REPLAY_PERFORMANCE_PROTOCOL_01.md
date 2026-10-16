# Bytefray V6 — M2-5 Replay Performance Protocol 01

2026-10-15, America/Indianapolis. **Prospective protocol for M2-4 condition D2.
Not executed. M2-5 is NOT AUTHORIZED.** It takes effect only if the M2-5 grant
adopts it; the grant may amend it, but only before the first measured repeat.

## 1. Purpose and authority

[M2-4 Closure 01 §6](V6_ALPHA_M2_4_CLOSURE_01.md#6-decisions-d1d3) accepted the
replay load cost as a limitation and required an M2-5 follow-up:

> The observed approximately 5.7-second additional seat-B projection cost must
> be evaluated during native qualification.

This protocol defines what M2-5 measures, how, and how each result will be
interpreted. The interpretation in §6 is fixed now, before any M2-5
measurement, so it cannot be fitted to the results. It authorizes no product
code change, checkpoint redesign, cache or loading-feedback work. Any such work
needs a separately authorized amendment (§8).

## 2. Facts known before this protocol

These are already observed, and the interpretation below was written with them
in view. They are listed so that the reader can judge whether the thresholds
were chosen to pass them.

| Fact | Source |
| --- | --- |
| On the 200-tick C2 replay, idle Windows, in-process: A projection 6.08 s, seat-B validation 5.72 s, `load_sensing_presentation` total 11.79 s | `load_timing_windows.json` ([M2-4 evidence](evidence/m2_4/README.md)) |
| Native first draw 59–71 s and M2-2A's 40 s include the observer's `sys.setprofile` hook during load, so they are not product timings | [Implementation Record 01 §9.3](V6_ALPHA_M2_4_IMPLEMENTATION_RECORD_01.md#93-load-time-cost-of-the-symmetric-fallback) |
| A freeze-02 first draw of 106 s ran while the Linux campaign shared the host | Same section |
| `load_sensing_presentation` runs in `cli.py` before the viewer window exists, so no window or progress indication is shown while loading | Code reading, `client/src/battle_client/cli.py` and `sensing_renderer.py` `run()` |
| Every perspective change calls `SensingCursor.switch_view`, which constructs a new cursor: deep copy of the playback, replay re-hash, canonical replay reload, every TICK_END boundary checked, all frames rebuilt. It runs synchronously inside the viewer's event loop | Code reading, `client/src/battle_client/sensing.py` |
| The seat-B projection built at load is used only as a validity probe and discarded; the first B selection builds it again, and A→B→A rebuilds A | Code reading, `sensing_presentation.py` |
| Rewind is a forward rebuild from the beginning; this is an accepted limitation with no checkpoint redesign | Scope Revision 03 §10 |

The thresholds in §6 do not come from these numbers. They come from the
response-time limits commonly used in interaction design: about 0.1 s feels
instantaneous, about 1 s keeps the user's flow of thought, and about 10 s is
the limit for keeping attention on a task without progress feedback. By the
facts above, a 200-tick perspective switch is expected to take several seconds,
which §6 classes as a limitation rather than as acceptable.

## 3. Inputs

| ID | Input | Ticks | Identity | Role |
| --- | --- | ---: | --- | --- |
| I1 | Published Keeper `keeper-K1` body, Keeper in seat A | 100 | [`evidence/m2_2/keeper/seat_A/`](evidence/m2_2/README.md), hashes in its index | M2-6-relevant (scenario replay) |
| I2 | Published Reacquirer `reacquirer-R1` body, Reacquirer in seat B | 100 | [`evidence/m2_3/reacquirer/seat_B/`](evidence/m2_3/README.md), hashes in its index | M2-6-relevant (scenario replay) |
| I3 | Fixed C2 Keeper Development Test replay, trace and result | 200 | `98edb90d…`, `47268aa8…`, `62003072…` ([M2-4 Closure 01 §2](V6_ALPHA_M2_4_CLOSURE_01.md#2-accepted-identities)) | M2-6-relevant (Development Test length) |
| I4 | Advanced-match and Development Test artifacts produced by the M2-5 native Designer workflow, per starter and seat | as recorded | Hashed when produced | M2-6-relevant (actual workflow output) |
| I5 | Fresh Scout demonstrations at `--ticks 250`, `500` and `1000` (the default) | 250 / 500 / 1,000 | Hashed when produced, under the M2-5 run root | Scaling characterization only |

I5 uses the existing trusted product scenario (`python -m
battle_engine.sensing_demo --scenario scout --ticks N --output-dir …`). It is a
product demonstration run, not research. M2-6 tasks do not open Scout replays,
so I5 is never gating except for correctness (§6.4).

## 4. Environment controls

- Windows and Linux measurements run **sequentially**, never concurrently.
  WSL2 shares the host CPU, and the 106 s example shows the effect of overlap.
- No other campaign, build or indexing job runs during a measurement. Record
  the host CPU model, core and thread count, RAM, power plan (Windows) or CPU
  governor and WSL2 memory limit (Linux), AC power, OS build, Python,
  pygame-ce/SDL, PySide6, display resolution and scale factor, and the font
  path in use.
- Use the verified repository interpreters (`.venv` on Windows; the retained
  `work/m2_2a_linux_env` with user-local X11 libraries on Linux), with
  `PYTHONDONTWRITEBYTECODE=1`. Record each harness file's SHA-256.
- No observer hook is active during any timed load (§5, P1 and P3). The
  observer may be active only after the viewer's `run()` starts, where it uses
  draw-return monitoring only (P4).
- Each input/operation pair gets **one warm-up repeat plus five measured
  repeats**. The warm-up is retained and reported, and excluded from the
  median. Medians and maxima are over the five measured repeats.

## 5. Measurements

**P1 — In-process load phases (no window, no observer).** A harness in the
style of the retained `load_timing.py` times: `ReplaySession.load`;
`reconstruct_sensing_playback`; seat-A `SensingCursor` construction; the seat-B
validation probe; `restart`; and `load_sensing_presentation` end to end on a
fresh session. Record peak resident memory.

**P2 — Rebuild accounting (in-process).** Wrap, inside the harness process
only, `SensingCursor.__init__`, `reconstruct_sensing_playback` and
`ReplaySession.load` with call counters, and count replay-file reads. Count
each for: one load; first selection of A, B and Omni; A→B→A; re-selecting the
current perspective; and End, Home, one step back from the end, a timeline seek
to the middle and `seek_relative(-10)`. Also confirm that each rebuilt view
equals the view produced by a fresh load at the same position.

**P3 — Native launch (no observer).** Launch `python -m battle_client.cli
--renderer pygame --replay … --trace … --result … --paused` as the Designer
does. Time from process start to the first visible viewer window (Windows:
`EnumWindows` for the viewer PID's visible window; X11: `xdotool search --sync
--onlyvisible --pid`). Record exit status and peak working set or `VmHWM`.
Resolve the real viewer PID behind the `.venv` launcher, which caused
`windows_native_01` to fail.

**P4 — Native interaction and responsiveness (draw-return observer only).**
For each I1–I3 input, from three positions (start, middle, recorded end), time
each perspective change (A→B, B→Omni, Omni→A) and End, Home, step back and a
timeline seek. Measure from input delivery to the first draw that shows the new
state, and the longest gap between consecutive event-loop iterations around the
operation. On Windows, also poll `IsHungAppWindow` every 100 ms and record
whether the window was flagged "Not Responding". Send one additional key during
each stall and confirm it is processed afterwards (no lost or misapplied
input). Use `SendInput` with the viewer focused for modifier keys on Windows,
because `PostMessage` dropped Shift in `windows_native_03`.

**P5 — Designer responsiveness while a viewer loads.** In the native Designer
workflow, while the Designer launches the external viewer on I4 artifacts, run
a 50 ms `QTimer` heartbeat in the Designer process and record the longest gap.
The Designer launches the viewer as a separate process, so a stall here would
be a separate finding.

**P6 — Scaling.** Run P1 and P3 on I1, I3 and I5 (100, 200, 250, 500 and 1,000
ticks) and report time against recorded ticks, with the log-log slope.

## 6. Prospective interpretation

### 6.1 Load (P3 median, observer-free; I1–I4)

| Class | Definition |
| --- | --- |
| L1 — acceptable | ≤ 10 s from launch to visible window |
| L2 — acceptable limitation | > 10 s and ≤ 30 s, viewer opens correctly, exit status 0 |
| L3 — unacceptable | > 30 s, or the viewer fails to open, crashes, exits nonzero or must be killed |

### 6.2 Interactive operations (P4 median; I1–I3)

| Class | Definition |
| --- | --- |
| I1 — acceptable | ≤ 1 s from input to the first draw of the new state |
| I2 — acceptable limitation | > 1 s and ≤ 10 s; the final state is correct; input sent during the stall is neither lost nor misapplied. A Windows "Not Responding" flag inside this class is recorded as a usability limitation, not as I3 |
| I3 — unacceptable | > 10 s, or lost or misapplied input, or a wrong delivered view after the operation, or the viewer must be killed |

A single repeat that exceeds the I3 or L3 bound while the median does not is
recorded and investigated. It becomes class 3 only if it recurs in at least two
of the five measured repeats.

### 6.3 Rebuild accounting (P2)

- **R-a (expected):** counts match the code reading in §2 (for example, two B
  constructions for load plus first B selection, and one trace reconstruction
  per load) and every rebuilt view equals a fresh load. Recorded as an
  optimization opportunity under D2; no new condition.
- **R-b (unexpected):** more work than the code reading predicts (for example,
  the trace reconstructed again on a perspective change), or a navigation
  operation that rebuilds a cursor. A finding that requires lead disposition.
- **R-c (correctness):** a rebuilt view differs from a fresh load at the same
  position. Treated as a semantic defect (§6.4).

### 6.4 Correctness and scaling

Any failure to load a valid product replay of any length, any crash, or any
delivered-view difference is a semantic defect and an M2-5 stop condition,
whatever its timing. P6 has no time threshold; it characterizes scaling for
later planning. Windows/Linux ratios are reported without a threshold.

### 6.5 D2 disposition mapping

| Worst observed class on M2-6-relevant inputs (I1–I4) | D2 disposition | M2-5 effect |
| --- | --- | --- |
| L1 and I1, R-a | D2 closed | None |
| Any L2 or I2, or R-b; no class 3 | D2 remains an accepted limitation, with measured values | PASS WITH CONDITIONS on D2; the M2-6 facilitator script must tell participants about expected waits (a declared condition, not task assistance) |
| Any L3 or I3 | D2 unresolved | **HOLD on D2** pending a lead decision: accept with an explicit M2-6 impact statement, or authorize a performance amendment (§8) |
| R-c or §6.4 failure | Semantic defect | **STOP** (M2-5 stop condition) |

## 7. Outputs and custody

Write to a fresh M2-5 run root, for example
`runs/v6_alpha_m2/m2_5_<date>/performance/`, refusing existing leaves. Retain:
every harness file and its hash; raw per-repeat timings, counts and memory
values (`performance_raw.jsonl`); environment records; native summaries and key
witnesses; and a `performance_report.json` that reports, for each metric, the
median, maximum and class, with the §6.5 disposition. Failed or invalidated
repeats are retained under their original labels. A harness defect is fixed
under a new label; the original stays retained.

## 8. Candidate amendments (identified, not authorized)

If the results call for product work, the lead may consider separately:

- **A-1:** reuse the seat-B projection built at load for the first B selection,
  or keep one validated cursor per perspective for the session;
- **A-2:** show load progress, or create the window before the load;
- **A-3:** move perspective rebuilds off the event-loop thread.

Each would change `sensing_presentation.py`, `sensing.py` or the renderer, and
`sensing.py` and `player.py` are outside the accepted M2-4 boundary. A-1 must
also preserve the rule that no state from one perspective survives a switch to
another. None is part of M2-5 unless authorized.

## 9. Exclusions

This protocol makes no benchmark, hardware-independence or release claim. The
results describe the recorded machines only. It adds no checkpoint redesign and
does not change the accepted rewind-reconstruction limitation. It authorizes no
E8/E9 activity. Original E9 remains operationally blocked with execution
LOCKED, and Requirement C remains NOT ESTABLISHED.
