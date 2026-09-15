# V5 RC1 Adversarial Findings Intake — Phase 0

Investigation-only intake of the Octave adversarial exercise against Bytefray
5.0.0-rc1's stable `bytefray-rules-4` / Agent API v2 implementation. This
document classifies each reported finding against the canonical engine and
its normative documentation. **No production code was changed to produce
this report.** No gameplay, scheduling, disruption, reach, or scoring
behavior was modified. One disposable reproduction agent was created and
removed during the investigation (see §2.3).

---

## 1. Baseline

| Item | Value |
| --- | --- |
| Branch (at task start) | `main`, HEAD `9131997ec3...` — **not** the RC1 implementation branch; see note below |
| Branch (used for this investigation) | `v5-research`, HEAD `59c55a7cd216b8198b65ef1d6ec915cc1474a4b3` |
| Upstream | `origin/v5-research`, 0 ahead / 0 behind |
| Working tree | Clean (`git status --short` empty) throughout the investigation |
| Stashes | Two pre-existing, unrelated stashes (`sync_win auto-stash 20251001-214422`; `WIP before pulling main`) — inventoried, not touched |
| `.git/index.lock` | Absent |
| Running Bytefray/pytest processes | None found (`tasklist` for `python.exe`/`pytest.exe` empty) at investigation start |

**Branch discrepancy, resolved.** This conversation's opening snapshot
reported the working branch as `v5-research`. The first baseline check in
this session instead found the repository checked out to `main`
(`9131997`), whose only relevant commit is an out-of-band docs commit
("docs: highlight Bytefray v5.0.0-rc1") — `main` does **not** contain the
actual RC1 implementation. The real RC1 development (54 commits including
"complete RC1 blocker remediation and source requalification" and "rc1
windows qualifications") lives on `v5-research`, and `git reflog` showed
HEAD had been moved from `v5-research` to `main` immediately before this
session began. Since the task requires treating the canonical RC1
implementation and its normative docs as authoritative, and `main` does not
carry that implementation, this investigation switched back to
`v5-research` (a safe, reversible `git checkout`, no uncommitted work at
risk) before doing anything else. All findings below were investigated
against `v5-research` @ `59c55a7`.

**Data-root discovery note (environment-specific, not a repo defect).**
This machine has a `BYTEFRAY_ROOT` environment variable pointing at
`C:\ProgramData\Bytefray`, which is the actual directory the installed
`bytefray` CLI resolves custom agents from — not the repository's own
gitignored `agents/` directory (`D:\Projects\BATTLE2\agents\`), which exists
only as a convenience copy per this repo's own `.gitignore` comment
("Source checkouts use root `agents/` as the writable runtime catalogue").
The two Octave copies were verified byte-identical (`diff -rq`) before any
canonical-engine run, so this had no effect on the evidence below, but it is
worth recording: `bytefray run --a-type <name>` on this machine resolves
custom agents through `%ProgramData%\Bytefray\agents`, not the repo
checkout, unless `BYTEFRAY_DATA_ROOT` is set explicitly.

---

## 2. Evidence inventory

### 2.1 Octave (the adversarial agent)

Location: `agents/Octave/` (gitignored; not a tracked repository path —
consistent with `.gitignore:38`'s `/agents/` rule, which reserves that path
for the local runtime catalogue rather than versioned starters). Verified
identical to the copy the installed CLI actually resolves
(`%ProgramData%\Bytefray\agents\Octave`).

| File | Role |
| --- | --- |
| `agent.py` (694 lines) | The entrant: ownership-based core localization, dispersed multi-process anchoring, last-mover-gated atomic 8-cell burst, power-of-two-denominator share arithmetic |
| `agent.yaml` | Manifest: `parameters` (`process_reach`, `process_count`, `guard_actions`, `sighting_window`, `disperse_span`, `burst_on_last_mover_only`, `burst_retries`, `claim_territory`) and `presets` (`standard`, `local`, `reckless`) |
| `README.md` | The report referenced by this task: measured win-rate tables, a full worked explanation of each of the five findings, and a "Known limits" section |
| `arena_bench.py` | Batch win-rate harness — drives the **real** `bytefray run` CLI as a subprocess per match (not an alternate engine; see §2.2) |

No `BUG`/`FIXME`/`TODO`/`XXX`/`HACK` markers exist anywhere in `agents/Octave/`
(grepped). No additional undisclosed findings were hidden in the source.

### 2.2 "Independent harness" — what it actually is

`arena_bench.py` is not an alternate simulator. Every match it runs is a
`subprocess.run(["bytefray", "run", "--a-type", ..., ...])` call against the
same installed CLI used throughout this investigation; it only parses the
CLI's own stdout/`result.json` and tallies win/loss/tie. There is no
second, independently-implemented Ruleset-v4 engine anywhere in the
supplied evidence. This matters for classification: every number in
Octave's README was already produced by the canonical engine, not by a
simulator that could disagree with it — but per the task's instruction not
to trust the harness's own interpretation, every claim below was
independently re-run or independently proven from source rather than
accepted from the README.

### 2.3 Reproduction artifacts created during Phase 0 (disposable, already removed)

One disposable reproduction agent, `phase0_share_probe`, was created solely
to exercise the process-count 3/5/6/7 case of Finding 1 through the real
engine's `ProcessDeclaration`/`Fraction` machinery (`declare_processes()`
returning N equal shares via the exact "derive the final share" pattern
`AGENT_API_V2.md` §D recommends, generalized past two processes). It was
placed under the repository's gitignored `agents/` directory (never
tracked, never committed) and under a session-scratch `BYTEFRAY_DATA_ROOT`
for CLI-level testing, and was **deleted at the end of the investigation**;
`git status --short` is empty and `agents/Octave/` is the only remaining
content under `agents/`. The N=2 case (the task's headline `v5_dual_team
raider_share=0.7` reproduction) needed no scratch agent — it was reproduced
directly against the bundled starter.

---

## 3. Finding ledger

| ID | Finding | Canonical reproduction | Contract status | Classification | RC1 action | Future research |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Process-share validation: tolerant declaration check vs. exact-rational match-construction check disagree | Yes — `bytefray run --a-type v5_dual_team --a-param raider_share=0.7 ...` crashes on the canonical engine; process-count 3/5/6 equal-split also crashes | Violates `AGENT_API_V2.md` §M's "ordinary presentable diagnostics, never a Python traceback" | **CONFIRMED RC1 DEFECT** (see §4.1 for blocker/non-blocking discussion) | Yes — narrow remediation, see §7 | — |
| 2 | Unbounded, zero-cost `process_reach` | Yes — independently re-run, same-seed A/B (`Winner: A` at full reach, `Winner: B` at reach 48) | Matches `RULES_V4.md`: reach "uncapped ... costs nothing," and "no reach cap" is explicitly listed as an inherited alpha1 deferral | **INTENTIONAL RULESET-V4 BEHAVIOR / FUTURE GAMEPLAY-RESEARCH CANDIDATE** | None | Yes — reach caps were already studied and rejected once (v4 alpha2 Phase 4); reopening needs new evidence, which this finding may supply |
| 3 | Last-mover atomic 8-cell capture timing | Yes — scheduler/capture-check order confirmed directly from source | Consequence of documented `K=2` chunked scheduling + "checked once per tick after every action" capture timing, both explicit in `RULES_V4.md` | **LEGITIMATE EMERGENT STRATEGY** | None | Optional — parity-awareness as a strategic dimension |
| 4 | Disruption vs. dispersed processes / quota redistribution | Yes — redistribution mechanism confirmed directly from source (`_effective_process_quotas`) | Matches `RULES_V4.md`: "share is redistributed among the entrant's other eligible positive-share processes, preserving the entrant's total budget whenever any of its processes remains eligible" | **LEGITIMATE RULESET-V4 STRATEGY** | None | Optional — dispersal-vs-disruption tradeoff as a strategic dimension |
| 5 | Ownership-based enemy-core localization from `previous_read_owner` | Yes — confirmed directly from source: cores are pre-seeded as owned by their entrant before tick 1, and `previous_read_owner` is populated from the same ordinary ownership field a `READ` always exposes | Uses only documented `ObservationV2` fields (`AGENT_API_V2.md` §E); no hidden/private engine state | **LEGITIMATE ADVANCED STRATEGY** | None | None needed |
| — | No sixth finding located | Reviewed Octave source/README/manifest/benchmark script in full; no `BUG`/`FIXME`/discrepancy markers found | — | **NOT REPRODUCED (no additional finding exists)** | None | None |

---

## 4. Detailed evidence

### 4.1 Finding 1 — Process-share validation

**Claimed behavior.** Declaration-time validation (`bytefray agents
validate`) accepts a share total the match runtime later rejects with
`ValueError: entrant 'A' process quota shares total ...; expected 1`, using
the bundled `v5_dual_team` starter's `raider_share=0.7` as the flagship
example.

**Where the two checks actually live** (`engine/src/battle_engine/process_runtime.py`):

- **Declaration-time check**, [`process_runtime.py:293`](../../../engine/src/battle_engine/process_runtime.py):
  ```python
  total_share = math.fsum(float(item.share) for item in typed)
  if not math.isclose(total_share, 1.0, rel_tol=0.0, abs_tol=1e-12):
      raise cls._initialization_error(...)
  ```
  This is a **tolerant** floating-point check (absolute tolerance `1e-12`),
  and it is documented as such — `AGENT_API_V2.md` §D states verbatim:
  "All shares must total exactly `1.0` (absolute tolerance `1e-12`)." This
  same function, `ProcessMatchController._validate_declarations`, is what
  both `bytefray agents validate` and ordinary match construction call
  (confirmed: `agent_validation.py` imports and calls it directly in both
  its supervised and unsupervised validate paths).

- **Match-construction check**, [`process_runtime.py:556`](../../../engine/src/battle_engine/process_runtime.py)
  and [`process_runtime.py:646-654`](../../../engine/src/battle_engine/process_runtime.py):
  ```python
  Fraction(str(declaration.share))     # per-process, independently
  ...
  declared_quota = sum(p.quota_share for p in spec.processes)   # exact Fraction sum
  expected_total = Fraction(1) if spec.normalized_shares else config.instr_per_tick
  if declared_quota != expected_total:
      raise ValueError(f"entrant {spec.agent_id!r} process quota shares total "
                        f"{declared_quota}; expected {expected_total}")
  ```
  This is an **exact** equality check on `Fraction` arithmetic, run
  immediately after the tolerant check passes, inside the same
  `from_python_entrants` call that ordinary match startup always goes
  through.

**Why they disagree.** Each process's float `share` is converted to a
`Fraction` **independently**, via `Fraction(str(share))` — the decimal
string of that one float. A single literal like `0.7` converts exactly
(`Fraction("0.7") == 7/10`), which is why the authoring guide's "derive the
last share" trick (`s`, `1.0 - s`) works for exactly two literals in
isolation. But `1.0 - 0.7` is itself a float with its own rounding error
(`0.30000000000000004` in IEEE 754 double precision), and *that* float's
decimal string converts to a *different* fraction than the mathematical
`3/10`. Summed as exact `Fraction`s, the two shares land at
`25000000000000001/25000000000000000` — 1 part in 2.5×10¹⁶ away from `1`,
comfortably inside the documented `1e-12` tolerance, but not equal to
`Fraction(1)`.

**Canonical reproduction — the shipped starter, as claimed.**
```
$ bytefray agents validate v5_dual_team
agent: v5_dual_team
status: valid
api_version: 2
dry_run_action: MOVE operand=32

$ bytefray run --a-type v5_dual_team --a-param raider_share=0.7 --b-type v4_quorum --ticks 20 --seed 1 --quiet
ERROR: V4 match engine failed: ValueError: entrant 'A' process quota shares total 25000000000000001/25000000000000000; expected 1
Agents:
 A: v5_dual_team params=raider_share=0.7
 B: v4_quorum params={}
```
`raider_share` is declared `type: number, minimum: 0.0, maximum: 1.0` in
`v5_dual_team/agent.yaml` — `0.7` is an ordinary, in-bounds value, not an
edge case, and is explicitly modeled by the manifest's own description
("0.75 gives the raider six and the keeper two"). `v5_dual_team` derives
its second share exactly as `AGENT_API_V2.md` §D instructs
(`share=self.raider_share`, `share=1.0 - self.raider_share`) — an agent
author following the documentation to the letter still hits this.

**One precision correction against the reported reproduction.** `bytefray
agents validate` has no `--param`/`--preset` flag today (confirmed from its
own `argparse` parser) — it can only validate an agent at its schema
defaults. So the literal two-command sequence "`validate raider_share=0.7`
→ valid, then `run raider_share=0.7` → crash" is not reproducible as an
external two-command narrative; `validate` never sees the override. The
underlying defect is real regardless: the *identical* tolerant check
`validate` exercises (`_validate_declarations`) also runs, and also passes,
**inside** the single `bytefray run` invocation above, moments before the
exact-`Fraction` check in `ProcessMatchController.__init__` rejects the
same declaration. The inconsistency is intra-command, not merely
cross-command, which if anything is a more precise (and more surprising)
characterization than the reported one.

**Generalization (process counts 3, 5, 6, 7).** Using the engine's own
`math.isclose`/`Fraction(str(...))` calls against the exact "derive the
final share" pattern generalized to N processes (`share = 1.0/N` for N−1
processes, remainder for the last):

| N | float sum | tolerant check (`abs_tol=1e-12`) | exact `Fraction` sum | exact check |
| --- | --- | --- | --- | --- |
| 3 | 1.0 | pass | `99999999999999997/100000000000000000` | **fail** |
| 5 | 1.0 | pass | `24999999999999999/25000000000000000` | **fail** |
| 6 | 1.0 | pass | `25000000000000001/25000000000000000` | **fail** |
| 7 | 1.0 | pass | `1` | pass |

N=3's exact total (`99999999999999997/100000000000000000`) is the precise
figure quoted in the task's reported example — confirming the report's
quoted number is a real artifact of this mechanism, not an invented one.
N=7 happening to pass is not a fix — it is a coincidence of which specific
rounding directions cancel for that particular N; N=1, 2, 4, 8 (every
power-of-two roster) also pass, because `1/2^k` is exactly representable in
binary and cancels perfectly, which is exactly why Octave's own
`declare_processes()` deliberately routes shares through integer
power-of-two-denominator weights instead of the documented pattern (see its
own docstring, quoted in §2.1) — the agent was written specifically to
route around this defect, which is itself corroborating evidence that the
author diagnosed it correctly.

**Diagnostic-contract check.** The `ValueError` is not caught as a
purpose-built parameter diagnostic; it is caught by
`match_service.py`'s generic top-level handler:
```python
except Exception as exc:
    raise PythonMatchExecutionError(RuntimeDiagnostic(
        code="engine_failed", stage="execution",
        message=f"V4 match engine failed: {type(exc).__name__}: {exc}",
        ...))
```
i.e. the same catch-all used for *any* unexpected exception during match
execution — not the `stage="configuration"`/parameter-error path
`AGENT_API_V2.md` §M documents ("A bad value at match time is a parameter
error, reported before the match starts... never a Python traceback").
The user-facing message surfaces raw internal `Fraction` arithmetic
(`25000000000000001/25000000000000000`), which is accurate but not
actionable — nothing about it suggests "lower your `raider_share`
precision" to the person who hit it.

**Classification.** **CONFIRMED RC1 DEFECT.** It is reachable through a
bundled first-party starter's shipped, in-bounds, documentation-endorsed
parameter value with no workaround visible to the user; it manifests as an
uncaught crash rather than the presentable diagnostic the API contract
promises; and it is not a strategy or balance question at all — it is an
internal inconsistency between two share-total checks inside the same code
path. Whether it rises to release-**blocking** severity is a product-scope
call this Phase-0 investigation defers to the maintainer (see §6), but the
combination of "bundled starter" + "in-bounds value" + "uncaught crash, not
diagnostic" argues for treating it as blocker-caliber rather than deferring
it past RC1.

---

### 4.2 Finding 2 — Unbounded, zero-cost `process_reach`

**Claimed behavior.** Reach can be declared large enough to cover the whole
arena, costs nothing, and Octave's win rate collapses when reach is
restricted.

**Contract.** `RULES_V4.md`, "How does READ/WRITE/MOVE work?": "Reach is
declared per process at `[1, arena_size - 1]` (uncapped) and costs
nothing." The same document's "What remains unchanged?" section lists "no
reach cap" explicitly among "Every alpha1 deferral," carried unmodified
into stable v4. Enforcement matches: `_validate_declarations`
(`process_runtime.py:262-276`) only rejects `reach <= 0` or `reach >=
arena_size`; nothing in the tick-execution path (`process_runtime.py`
~lines 990-1258) charges quota, moves, or anything else for a large
`reach` value — the only per-tick cost anywhere is the fixed `Q=8` action
budget, which is entirely independent of any process's declared reach.

**This was deliberately studied and rejected once already**, which is
stronger evidence of intent than a mere absence of a cap.
`docs/V4_ALPHA2_DESIGN.md` §7 ("Explicit alpha2 non-goals"): "any reach cap
(disarms the dominant agents rather than creating graduated local play;
raised the tick-limit rate from 47% to 91%)" — from
`docs/archive/v4/V4_ALPHA2_PHASE4_GAMEPLAY_STUDY.md`'s reach-cap experiment
matrix. A reach cap was tested with real matches and found to make the
game *worse* (far more matches simply timed out without a winner) rather
than producing the graduated, locality-respecting play a cap was meant to
create.

**Independent canonical reproduction** (not taken from Octave's own
README numbers — re-run here with a seed chosen for this investigation):
```
$ bytefray run --a-type Octave --b-type v4_quorum --ticks 400 --seed 1
...  Winner: A   (full/default reach: process_reach=0 -> arena_size // 2)

$ bytefray run --a-type Octave --a-preset local --b-type v4_quorum --ticks 400 --seed 1
...  Winner: B   (process_reach=48, an ordinary locality-respecting value)
```
Same agent, same opponent, same seed, same tick limit — the only variable
changed is reach, and it flips the winner. This corroborates Octave's own
README table (100% → 6.9% win rate across a larger sample) using a fresh,
independently-chosen seed rather than trusting the harness's own numbers.

**Classification.** **INTENTIONAL RULESET-V4 BEHAVIOR / FUTURE
GAMEPLAY-RESEARCH CANDIDATE**, exactly as the task's own expected
classification anticipated — now proven from source and independently
re-run rather than assumed. Reopening reach-cap design requires new
evidence per `V4_ALPHA2_DESIGN.md`'s own closing line ("Adding any of these
requires new evidence, not a preference"); Octave's exercise may constitute
that evidence for a future V6 research proposal, but it does not make
uncapped reach an RC1 defect.

---

### 4.3 Finding 3 — Last-mover / atomic capture timing

**Claimed behavior.** Octave holds an 8-cell burst for a tick it takes the
final action chunk of, because the capture check runs after every action
in the tick, leaving the defender no remaining action to answer.

**Contract and source, confirmed directly.**
- Scheduling: `battle_engine/scheduler.py`'s `run_chunked_quota` computes
  `offset = (tick - 1) % n_states` and reorders
  `state_order = state_list[offset:] + state_list[:offset]` — byte-for-byte
  the formula `RULES_V4.md` documents and the one Octave's
  `_is_last_mover` implements (`(tick - 2) % count == seat_index % count`
  is exactly "the last entrant to act is the one at index
  `(offset - 1) % n`").
- Capture-check timing: in `process_runtime.py`'s main tick loop, the
  entire tick's scheduled action pass —
  `self.ruleset_policy.run_scheduler(self.states, self.config.instr_per_tick,
  execute_entrant_slot, tick=tick)` (line 1245) — completes in full,
  covering every entrant's every chunk, **before**
  `apply_core_capture(...)` is called (line 1249). There is no
  interleaving; capture is checked exactly once per tick, strictly after
  every entrant's every action for that tick has already been applied.
  This is precisely `RULES_V4.md`'s and `AGENT_API_V2.md`'s stated
  contract ("checked once per tick, after every action in that tick has
  run"), not an accidental ordering.

**Spot-check against a symmetric mirror (this investigation's own run,
not from the README).** Toggling only the documented
`burst_on_last_mover_only` parameter (no code change) across six seeds,
both seat orders, Octave (gated) vs. Octave (ungated, same build) on a
400-tick limit produced **ties in all twelve matches** — not the clean
12W/0L/12T split reported in Octave's README for its own gated-vs-ungated
comparison. Inspecting one match's tick-by-tick output showed both
entrants eliminated simultaneously around tick 7-8 (mutual kill, not a
tick-limit stall). This does not contradict the underlying mechanism,
which is proven directly from source above, but it means this
investigation's own spot sample does not cleanly reproduce the specific
12W/0L/12T magnitude the README reports for the Octave-mirror control;
mirror matches are an explicitly acknowledged degenerate case in Octave's
own "Known limits" section ("each correctly waits for its own last-mover
parity and each successfully defends the other's burst"), and the
asymmetric advantage the finding actually describes is against
parity-unaware opponents (the 240-0-0 table against thirteen non-Octave
opponents), not against a mirror of itself.

**Classification.** **LEGITIMATE EMERGENT STRATEGY**, proven directly from
canonical source (both the scheduler formula and the capture-check
ordering), exactly as the task's expected classification anticipated. It
is a mechanical, intended consequence of documented, unmodified scheduling
and capture-timing rules — not a scheduler defect. The magnitude
discrepancy against the mirror-match control is noted above for
completeness but does not change this classification.

---

### 4.4 Finding 4 — Disruption vs. dispersed processes

**Claimed behavior.** Stacking processes on one address lets a single enemy
write disrupt the whole roster; dispersing them means only a fraction of
throughput is lost per enemy write, because quota redistributes to
still-eligible siblings.

**Contract and source, confirmed directly.** `RULES_V4.md`: "A legal enemy
`WRITE` landing exactly on a live process's anchor disrupts every enemy
process co-located there for the remainder of that tick... When disruption
makes a process ineligible, its share is redistributed among the
entrant's other eligible positive-share processes, preserving the
entrant's total budget whenever any of its processes remains eligible."
Source, `process_runtime.py`:
- Disruption is address-exact and hits every co-located enemy process
  (lines 1216-1230): a `WRITE`'s target address is compared against every
  other entrant's every process's current `position`; every match gets
  `disrupted_until_tick = tick + disruption_duration`.
- Redistribution (`_effective_process_quotas`, lines 756-794):
  `eligible = [p for p in spec.processes if not p.is_disrupted(tick)]`;
  the full `Q=8` (`config.instr_per_tick`) is allocated by largest-remainder
  rounding **only across `eligible`** — a disrupted process is simply
  excluded from the weight sum, so its share flows to its still-eligible
  siblings automatically. `eligible == []` (all processes disrupted) is the
  only case that returns `{}`, i.e. the only case where the entrant
  genuinely loses its whole tick.

This is exactly the mechanism the reported stacked-vs-dispersed numbers
require: throughput is preserved whenever at least one process remains
eligible, and lost only when every process is simultaneously disrupted —
which single-address stacking makes trivial to achieve with one enemy
write, and dispersal makes require as many simultaneous enemy writes as
there are distinct anchors.

**Classification.** **LEGITIMATE RULESET-V4 STRATEGY**, proven directly
from source, exactly as the task's expected classification anticipated.
Nothing here is unintended: the redistribution rule is explicitly
documented, and dispersal is simply an agent choosing to pay a small,
disclosed one-time `MOVE` cost against a rule that already exists on paper.

---

### 4.5 Finding 5 — Ownership-based core localization

**Claimed behavior.** An agent can combine early sightings, `READ`
ownership feedback, and the fact that a core is owned by its entrant from
match start to prove an enemy core window without ever being told its
address.

**Contract and source, confirmed directly.**
- Initial ownership: at match construction (`process_runtime.py`, "Seed
  core ownership (0xCE beacon)"), every entrant's eight core cells are
  written with `self.vm._wr8(cell, 0xCE, owner=spec.agent_id)` before tick
  1 — i.e. an entrant genuinely owns its own core cells, in the engine's
  actual ownership ledger, before any agent code runs.
- The only ownership channel exposed to agents: `previous_read_owner` is
  populated as `owner = self.vm.writer[target_addr]` on every `READ`
  (`process_runtime.py` ~line 1187) — the identical field the engine itself
  uses for core-ownership bookkeeping, exposed through the ordinary `READ`
  action documented in `AGENT_API_V2.md` §E/§F. There is no separate,
  privileged, or undocumented channel; Octave's technique reads exactly
  what any agent can read.
- Co-location at start: `AGENT_API_V2.md` §D and `RULES_V4.md` both
  document "every declared process starts co-located at its entrant's own
  core base" as an unconditional, unchanged rule — the "bearing from first
  sighting" half of Octave's technique follows directly from a documented
  guarantee, not an inference about hidden state.

**Classification.** **LEGITIMATE ADVANCED STRATEGY**, proven directly from
source, exactly as the task's expected classification anticipated. No
hidden or private engine state is touched; every fact Octave's core-finder
relies on is either an explicit `AGENT_API_V2.md` guarantee or the ordinary
`previous_read_owner` field every `READ` already returns.

---

## 5. Additional findings discovered during Phase 0

None. Octave's `agent.py`, `agent.yaml`, `README.md`, and `arena_bench.py`
were read in full; no `BUG`/`FIXME`/`TODO`/`XXX`/`HACK` markers or
undisclosed discrepancies were found beyond the five findings the task
already named and the self-acknowledged "Known limits" in Octave's own
README (dense-arena conversion difficulty against Quorum, no hold-tracking
on repeated bursts, mirror-match ties/mutual-kills, and a two-entrant-only
`_is_last_mover` heuristic) — all of which are properties of Octave's own
strategy code, not of the engine, and require no engine-side classification.

---

## 6. RC1 remediation recommendation

Only **Finding 1** (process-share validation) identifies an implementation
defect eligible for RC1 remediation. Findings 2-5 are intentional Ruleset-v4
behavior or legitimate strategy and require **no code change** — attempting
to fix any of them would itself violate this phase's explicit scope
boundary (§J of the task) and would be rebalancing, not defect
remediation.

Recommended disposition of Finding 1: **remediate before RC1 ships.**
Rationale: it is a crash, not a diagnostic; it is reachable through a
bundled first-party starter's documented, in-bounds parameter value with
no way for an ordinary user to anticipate it; and it contradicts an
explicit, already-published Agent API v2 promise
("...never a Python traceback"). The final blocker/non-blocking label is
the maintainer's call — it depends on how central `v5_dual_team`'s
`raider_share` parameter (and multi-process agents generally) are expected
to be in RC1's supported surface — but the technical facts point toward
blocker-caliber rather than deferrable.

---

## 7. Proposed Phase 1 scope (description only — not implemented here)

**Narrow remediation boundary.** Make the two share-total checks agree,
without changing what "close enough to 1.0" means for a human-authored
agent. The natural remediation seam is the exact-`Fraction` conversion at
`process_runtime.py:556` (`Fraction(str(declaration.share))`, consumed at
line 646's `declared_quota = sum(...)`): converting each share
independently and then demanding an *exact* sum is what manufactures a
mismatch out of values that were already within the documented tolerance.
A fix should make the match-construction check accept anything the
declaration-time check already accepted — for example, normalizing shares
against their declared total once (so the runtime works from the same
tolerant total the declaration check validated) rather than re-deriving
each share's fraction independently and demanding their exact sum. This
phase should not pre-select the exact code shape of that fix; it should
only confirm the remediation seam, which this report does.

**Required regression coverage**, at minimum:
- `v5_dual_team` with `raider_share=0.7` (and a small representative set of
  other in-bounds non-power-of-two-friendly values) must complete a match
  rather than raising.
- The N=3/5/6/7 equal-split cases characterized in §4.1's table must not
  regress once fixed.
- A genuinely invalid share total (e.g. summing to 0.5 or 1.5) must still
  be rejected — the fix must narrow the false-rejection gap without
  widening true-acceptance.
- `bytefray agents validate` and `bytefray run` must agree on every case in
  the above three bullets — the point of the fix is removing the
  disagreement, not moving it around.
- The existing `engine/tests/test_v4_stable_ruleset_equivalence.py`
  corpus (cited in `RULES_V4.md` as proving `bytefray-rules-4` is
  gameplay-identical to `bytefray-rules-4-alpha2`) must still pass, since
  Ruleset v4's identity depends on it.

---

## 8. Deferred research inventory (not designed here)

Recorded as candidates for a future V6 research backlog, per this task's
explicit instruction not to design V6 now:

- **Reach cost/cap redesign.** Already studied once (v4 alpha2 Phase 4)
  and rejected because a flat cap made matches worse, not better
  (tick-limit rate 47% → 91%). Octave's own numbers (100% → 6.9% at a
  single restrictive value) are new evidence that a *graduated* cost model
  (rather than the flat cap already rejected) may be worth studying, but
  that is a full research program, not an RC1 patch.
- **Parity-awareness as a strategic dimension.** Whether "last-mover
  atomic capture" should be treated as a first-class strategic axis (like
  offense/defense/scouting) worth building starter agents or evaluation
  scenarios around.
- **Dispersal-vs-disruption as a strategic dimension**, similarly — whether
  future starter agents or evaluation harnesses should exercise this
  tradeoff explicitly.
- **Octave itself** as a candidate reference/advanced agent for a future
  starter roster, subject to normal design review — explicitly out of
  scope to decide in this document.

---

## 9. Exit criteria check

- Every finding named in the task has an evidence-backed classification: **yes** (§3).
- The share-validation issue has a canonical minimal reproduction: **yes** (§4.1, both the shipped-starter case and the N=3/5/6 generalization).
- No result relies solely on the alternate/external harness: **yes** — every classification above cites engine source line-level evidence, and Findings 2 and 3 were independently re-run with fresh seeds rather than trusting Octave's own numbers.
- Intentional Ruleset-v4 behavior is separated from implementation defects: **yes** (Findings 2-5 vs. Finding 1).
- All RC1 blockers/defects requiring remediation are explicitly listed: **yes** — Finding 1 only.
- Future gameplay questions are explicitly deferred: **yes** (§8).
- No production gameplay or engine behavior was changed: **confirmed** — only a disposable, non-tracked reproduction agent was created and then deleted; `git status --short` is empty.
- Repository state is accounted for: **yes** (§1).
