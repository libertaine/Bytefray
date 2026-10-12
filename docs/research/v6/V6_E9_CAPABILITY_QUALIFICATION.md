# V6 E9 capability qualification

**Q-C1 through Q-C15: PASS for the declared capability class.** The final
focused run passed **53/53 checks**, including 30 scripted legal matches.
The authorized additional full headless run passed **6,912 tests**, with
**18 skipped, 3 deselected, no failures and no setup errors**, on unchanged
qualified executable/test bytes. All 53 E9 checks passed within that run.
Both earlier full-suite environmental events, development history and lost
opportunities remain documented below. The clean full-suite gate is satisfied.

This record concerns the approved bounded adaptive policy class, not whether
adaptation improves payoff. Requirement **C remains NOT ESTABLISHED**.
E9 preregistration remains unauthorized. The fixed/schedule comparator
selection method still requires a separate design decision.

The approved specification alone was committed and pushed as
`3a2d1292e83d6cd608588d87e6561249905d9ced`,
`docs(v6): specify E9 adaptive policy capability class`.
Before the capability boundary, remote `refs/heads/v6-research` was
independently verified at that exact SHA. Implementation, qualification
tests/tooling and both records form one capability boundary above it; the
commit containing this record identifies that boundary. The specification
preserves its historical preimplementation status language; this record
supplies the subsequent evidence.

## Scope and implementation

The [approved contract](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md)
is implemented under [tools/research/v6/e9](../../../tools/research/v6/e9/README.md).
Initial DENSE, C=2, L=2, B=4, and adaptive cadences 1/4 are unchanged.
OFF/DENSE/MEDIUM/SPARSE fixed variants and their disabled twins share the same
tactical executor. Schedules use the approved opportunity/wall clocks and
precommitted edges. Both independent enumerations give **1,334 canonical
identities**; no schedule was selected for performance.

The tactical copy has the frozen E8 source's exact raw-byte SHA-256:
`369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc`.
Only the allocation wrapper/controller is new. The copied source retains its
original E8 module description for byte identity; the wrapper overrides the
allocation gate and uses repeat/once common tactics as specified. The old
ADAPT8 switch is inactive for these variants.

The controller receives only its pending verification target, issue tick and
target-presence result, plus its declared clocks. Discovery/search results
and READ data remain tactical inputs, not selector evidence. The adapter
checks process/action association, applied/refused shape, circular bounds and
canonical result ordering. It buffers mid-tick receipts and consumes them
only at the first callback boundary. Stale evidence remains available to
the shared executor while becoming selector-NONE.

The reset view exposes the focal seat, arena, sensing window, common RNG and
fixed tactical parameters. It does not expose the match seed, opponent
package identity, arbitrary caller parameters or external artifacts.
The focal seat remains a legitimate frozen tactical input. Neither selector
has RNG access. Diagnostics are detached copies and never feed decisions.

Scratch packages import repository modules; they are qualification fixtures,
not standalone distribution agents or an E9 experiment roster. The wrapper
checks arena/window at reset; the legal harness explicitly selects unchanged
T8, `bytefray-rules-6-research-sensing-active-w27`. This does not claim a new
product registration or general compatibility gate for arbitrary rulesets.

## Evidence and mandatory obligations

Final counts and file hashes are recorded in
[qualification_record.json](../../../tools/research/v6/e9/qualification_record.json).
Its test inventory names the actual passing cases for each obligation.
The focused synthetic/engine checks are distinct from the broader headless
regression result recorded there.

| ID | Actual evidence |
|---|---|
| Q-C1 | OFF/RUSH8 and DENSE/REACQ8 callback equality in both seats; legal trace equality for both entrants, core state and RNG; raw tactical byte identity. |
| Q-C2 | Each of the four fixed allocations equals its disabled twin action-for-action and RNG-for-RNG. |
| Q-C3 | Selector vectors and full callback histories cycle both ways, defer the missing request through cooldown, and consume all four revisions. |
| Q-C4 | Inactive boundary rejection and actual no-discovery callback stays, insufficient/target-changing confirmations, DENSE missing priority, cooldown and exhausted-budget stays; the legal seat-B on-hit case stays DENSE. |
| Q-C5 | Identical prestates/clocks with target CONFIRM versus MISSING give different eligible commands; deferred requests persist without another receipt. |
| Q-C6 | READ/owner perturbation, unrelated returned contacts preserving the target, seed-poison reset view, and circular target renaming leave selector behavior unchanged. |
| Q-C7 | Empty applied versus absent/refused feedback, process/action mismatch, multiple contacts, mid-tick buffering, long-gap expiry, and end without another callback. |
| Q-C8 | Primary DENSE twin agrees before the first revision; a literal deepcopy of the adaptive executor with only commit disabled reproduces the twin's boundary action. |
| Q-C9 | Independent canonical enumeration and command oracle, both clocks, literal two-way sequence, skipped wall boundaries, and receipt-perturbed actual policy callbacks. |
| Q-C10 | At an eligible nonmultiple-of-four epoch, the adaptive fork issues ordinary WRITE/READ while the disabled fork issues paid SENSE; legal saved/restored offers are also asserted. |
| Q-C11 | Revision during an existing search preserves its next center and RNG; full exhaustion retains common ordering; legal third-window search crosses a partial tick and replaces the target exactly as frozen REACQ8. |
| Q-C12 | Both seats, opponent hit offers 1–8, full denial and 2/4/6-callback ticks; repeated full denial preserves opportunity phase. Synthetic long-gap/receipt-boundary cases cover both seats. |
| Q-C13 | No selector RNG/file/seed/identity inputs, poison seed access, restricted reset view, reset state, detached diagnostics, unexpected-process/context rejection. |
| Q-C14 | Static contacts in both seats yield actual saved monitoring offers; seat A's on-hit relocation yields a missing-triggered restoration at a nonmultiple-of-four epoch followed by productive actions. Seat B's lost opportunity is retained below. |
| Q-C15 | Independent functional oracle checks 15,625 six-boundary input histories (93,750 transitions), 1,334 schedules, explicit vectors and every adaptive legal diagnostic boundary. It imports no policy/constants. |

The real-engine evidence uses explicit scripted geometry and the existing
public qualification preset 7, not newly drawn experimental seeds.
The final focused run executes 30 legal qualification matches: 26 new focal
histories and four separate frozen-reference histories. Each match pairs a
policy with a scripted non-family opponent. No focal-versus-frozen-family
payoff tournament or family-versus-family performance field was run.
Normal engine replay/trace recording still writes its ordinary artifacts;
qualification diagnostics and assertions do not select, summarize or compare
scores/outcomes.

## Legal opportunities and limitations

Static qualification uses the existing two-process script: a stationary decoy
and a legal displaced process that cycles own-core repair. This preserves
the E8 mechanics and allows the contact history to continue long enough for
the confirmation gate to act. In both seats, a first-callback SPARSE offer
becomes a productive WRITE rather than verification SENSE.

The on-hit script uses the existing harness's responsive decoy and a fixed
legal MOVE delta. In seat A, the policy downgrades at r=3, discovers the missing
target through sparse verification at r=4, and restores DENSE at r=5.
Its next first-callback verification is at a nonmultiple of four, and further
productive WRITEs occur before termination.

**Seat B does not realize that cycle.** Repeated evasion interrupts the
target-specific confirmation run, and the policy stays DENSE. This is a real
lost opportunity, not a successful adaptation instance. The existing script
also differs from EVADE8 in its first-return-after-tick-1 inference, as already
documented in the frozen harness. These scripts establish legal opportunities
and causal behavior; they do not establish their frequency or payoff in the
unchanged competitive ecology, or fidelity of a new evaluation opponent.

An earlier single-process static script in seat A terminated before downgrade.
That opportunity is absent; the later two-process static case does not erase it.
No capture/disruption/scoring rule or policy constant was changed to prolong
a match. Helpful repair scripts are capability fixtures, not payoff evidence.

Timing fixtures initially scheduled hits after termination or on an opponent
already disrupted by the focal policy. Their precondition assertions failed.
The final conductor legally MOVEs until the named hit offer; all 16 seat/offer
cases assert that the WRITE actually applied at the focal anchor and that
the expected callback count occurred. This adjusts qualification geometry,
not policy behavior or payoff selection. Long gaps are synthetic coverage;
the real repeated-denial case has intervening callback ticks.

## Validation, preservation and stop boundary

Validation commands use the repository Python environment, serial pytest and
fresh ignored repo-local temp roots. Repository lint and separate engine,
client and new E9-module type checks passed. The full headless invocation
completed with **6,908 passed, 2 failed, 18 skipped and 3 deselected**. Both
failures arose because this task placed `--basetemp` under `runs/`: the replay
cache test explicitly forbids `runs` in its path, and the frozen E6 audit
writer correctly refuses output under `runs/`. Both unchanged tests passed
on a separate rerun outside `runs/`. At that stage, the entire full suite had
not been repeated; its original two failures remain visible in the record.
No product or frozen-tool correction was made.

The requested final-tree full headless invocation used the legal ignored
root `.pytest-tmp/e9-capability-final-suite` and completed in 1,115.61 seconds
with **6,901 passed, 0 assertion failures, 11 setup errors, 18 skipped and
3 deselected** (6,930 selected cases; 6,933 including deselected cases).
All **53 E9 capability checks passed** within that invocation and exactly
matched the focused record's case inventory. All ten implementation/test
raw-byte hashes still match the qualified source.

All 11 errors arise from one shared `test_v6_e3_pipeline.py` control fixture:
Windows denied atomic replacement of `evaluation.json` with `WinError 5`
under `e3-control0/C-E2/F2/arena_512/02-e2_repair_guard`. This is a filesystem
permission error during setup, not an E9 assertion failure. Its specific
cause is unconfirmed. The diagnostic rerun of the unchanged affected module
used the fresh ignored root `.pytest-tmp/e9-e3-recheck` and passed **13/13**
in 105.91 seconds, including all 11 affected cases. This supports a transient
Windows filesystem error; it does not establish the particular cause.
No code, policy, fixture geometry or test assertion was changed.

The historical full-suite result and two-test rerun remain separately
attributable in the machine record. That attempt did **not** meet the
requested clean full-suite condition. The passing isolated E3 diagnostic
does not substitute for a clean full-suite invocation.

The research lead authorized **one additional complete invocation** on
2026-10-02, with no code, test or fixture changes and a fresh ignored temp
root outside `runs/`. It used `.pytest-tmp/e9r-20261002` and completed in
**1,242.31 seconds** with **6,912 passed, 18 skipped, 3 deselected, zero
failures and zero errors** (6,930 selected cases; 6,933 including deselected
cases). The exact 53-case E9 inventory passed within this complete run.
All thirteen candidate files remained byte-identical throughout the run,
including all ten qualified executable/test files. Only the qualification
records were updated afterward. No separate 53-case rerun was required.

This clean invocation satisfies the final full-suite gate. The machine
record retains the two earlier full-suite events and their diagnostic
reruns unchanged, with the clean result in `clean_final_headless_regression`.
No infrastructure exception was used, and no further full-suite attempt
was made. Q-C1–Q-C15 remain PASS; Requirement C remains NOT ESTABLISHED.

The final 53-case capability invocation uses `.pytest-tmp/e9-final-02` and
passed with no failures/skips. The earlier development full suite collected 51
capability cases before two exhaustion cases and strengthened assertions were
added; the final focused invocation covers those additions. Logs and legal
diagnostics remain ignored. The machine record carries report digests and
raw implementation/test hashes for the qualified source.

The added exhaustion cases initially expected the target to remain in the
missing queue after exhaustion. That test expectation was incorrect: frozen
RP-3 removes the target when search starts, and termination makes it unknown.
Both policies agreed on every action and RNG draw. Reading the frozen contract
and `_start_search`/`_exhausted` resolved the difference; the final assertion
requires both policies' empty known/missing sets. No policy semantics changed.

An initial nested pytest temp path lacked its parent: 22 cases errored during
fixture setup, while 16 non-fixture cases passed. Creating the ignored parent
resolved that environment setup error. Early probe histories did not issue
qualification passes merely because their weaker assertions passed.

The legal-precondition development runs reported 5 passed/17 failed, then
12 passed/10 failed, before the corrected moving-conductor run passed 22/22.
Those failures include the absent seat-B on-hit cycle now explicitly retained
as a limitation, and hits not reached because the opponent was disrupted or
the match had ended. The intermediate 51-case focused run passed 51/51; the
first expanded exhaustion run passed 51 with the two expectation failures
described above. These are development/fixture evidence, not payoff results.

All 47 LF-normalized pinned E8/reused research files and the frozen manifest
of 116 engine files were independently verified unchanged. The sealed E8
machine result retains raw SHA-256
`9b93c488af11c53220c63dc5407bffbab31fcb64721701a648918c9fd8fd2a3e`.
No tracked runtime, frozen research, approved specification or local settings
file was modified. Before this capability boundary, only the approved
specification had been committed/pushed. After the clean retry, all 47 pins
(governing preregistration, family files, analysis tooling and reused files),
the 116-file engine manifest and sealed E8 result were reverified unchanged.
The machine record retains both preservation checks and the pin inventory.

The capability record stops at implementation/qualification. It creates no
experimental seeds, E9 matrix, statistical threshold, payoff-selection result
or preregistration. The research lead accepted Q-C1–Q-C15 as PASS and determined that policy
redesign is not needed. Implementation, qualification tests/tooling and both
records form the authorized capability commit now that the clean final
full-suite gate is satisfied. Push and live-remote agreement are verified
after commit. The latest instruction, dated 2026-10-02, keeps E9 comparator
and design-review work on hold; none was performed. Preregistration and
execution remain unauthorized.
All original A–G ratings remain unchanged.
