# V5 RC1 Process-Share Remediation — Phase 1

Phase 1 repairs the one release-blocking implementation defect confirmed by
[`V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md`](V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md):
Agent API v2 declaration validation accepted some floating-point share totals
that Ruleset-v4 construction then rejected under a second exact-rational rule.
No other Phase 0 finding or gameplay rule was changed.

## 1. Baseline

| Item | Value |
| --- | --- |
| Branch | `v5-research` |
| Starting HEAD | `2414be9fd977555ea205b372820b6f0bd0c69ed1` |
| Upstream | `origin/v5-research`; 0 ahead / 0 behind |
| Tracked worktree | Clean at task start |
| Stashes | Two pre-existing stashes; inventoried and untouched |
| `.git/index.lock` | Absent |
| Running pytest / Bytefray processes | None at task start |

The repository-local `agents/` catalog initially lacked the bundled starter
files expected by several existing tests (some directories contained only
ignored `__pycache__` data). Bytefray's own non-destructive
`ensure_starter_agents` bootstrap later materialized the current bundled files
there for qualification. It did not alter tracked files or existing custom
agents.

## 2. Confirmed defect

The public declaration contract in `docs/AGENT_API_V2.md` accepts a finite,
non-negative set of shares whose `math.fsum` total is within absolute tolerance
`1e-12` of `1.0`. Both supervised and unsupervised `agents validate` call
`ProcessMatchController._validate_declarations` directly
([`agent_validation.py`](../../../engine/src/battle_engine/agent_validation.py)).

Before this repair, Ruleset-v4 construction then converted each accepted share
independently with `Fraction(str(share))`. The controller constructor summed
those exact fractions and separately required equality with `Fraction(1)`.

Current-baseline reproduction before editing:

```text
bytefray agents validate v5_dual_team
status: valid
exit: 0

bytefray run --a-type v5_dual_team --a-param raider_share=0.7 \
  --b-type v4_quorum --ticks 20 --seed 1 --quiet
ERROR: V4 match engine failed: ValueError: entrant 'A' process quota shares
total 25000000000000001/25000000000000000; expected 1
exit: 2
```

The additional schema-valid value `raider_share=0.33` failed the same way with
exact converted total `9999999999999999/10000000000000000`.

## 3. Root cause

The two semantic seams were in
[`process_runtime.py`](../../../engine/src/battle_engine/process_runtime.py):

1. `_validate_declarations` made the documented tolerant validity decision.
2. `from_python_entrants` converted each float independently, after which
   `ProcessMatchController.__init__` made a stricter exact-total decision.

For `v5_dual_team`, `0.7` is converted exactly to `7/10`, while
`1.0 - 0.7` is the float `0.30000000000000004`. Their independent exact
fractions therefore do not sum to exactly one even though the public tolerant
check correctly accepts them. Replacing one `Fraction` constructor form would
only change the representation of the mismatch, not eliminate the duplicated
contract.

Bundled declarations mostly avoided the defect because their established
shares use exactly representable dyadic values such as `1.0`, `0.5`, `0.25`,
`0.125`, and `0.375`. Those converted fractions already sum exactly to one.

## 4. Repair

Changed files:

- `engine/src/battle_engine/process_runtime.py`
- `engine/tests/test_v4_production_integration.py`
- `docs/AGENT_API_V2.md`
- this report

`_validate_declarations` remains the one public validity decision. After it
accepts a declaration, `_runtime_quota_shares` converts the shares to exact
fractions and divides each by their exact converted total. The resulting
internal weights sum to exactly `Fraction(1)` and feed the existing
largest-remainder allocator unchanged.

The constructor's exact check remains as an internal representation invariant;
it no longer reinterprets public input under a stricter numerical contract.
Genuinely invalid totals still fail in `_validate_declarations` before
normalization and retain the existing typed declaration diagnostic.

For any previously constructible declaration, the converted total was already
exactly one, so normalization divides every weight by one. Its quota
allocation, remainder ordering, process ordering, chunking, and deterministic
gameplay are unchanged.

The Agent API authoring text was narrowed to describe the actual tolerant
validation plus exact internal normalization. No Ruleset or schema contract was
changed.

## 5. Regression coverage

Permanent coverage in `test_v4_production_integration.py` now proves:

- exact internal totals for accepted N=1 through N=8 declarations;
- unchanged converted weights for dyadic N=1, N=2, N=4, and N=8 cases;
- real stable-Ruleset-v4 construction and execution for N=3, N=5, N=6, and
  N=7 declarations using the documented derived-remainder authoring pattern;
- schema resolution, public agent validation, stable-v4 construction, and
  execution of the actual bundled `v5_dual_team` at `0.7` and `0.33`;
- rejection of a true `0.6 + 0.3 = 0.9` invalid total through both agent
  validation and the normal CLI run path; and
- the intended `agent_process_declaration_invalid` / `declaration` diagnostic,
  without a raw `ValueError` or traceback.

All runtime entry points inherit the repair at the common seam:

- direct `bytefray run` calls `NativeMatchService`;
- `TournamentService` calls the same service for each match;
- development testing and evaluation call `NativeMatchService` (evaluation via
  the development-test machinery);
- the Designer delegates its run, tournament, validation, test, and evaluation
  workflows to those same CLI/services; and
- `agents validate` continues to call the canonical declaration validator
  directly.

No redundant entry-point-specific fix was required.

## 6. Verification and non-regression evidence

| Gate | Result |
| --- | --- |
| New focused process-share set | **17 passed**, 7 deselected in 0.82 s |
| Broader runtime/scheduler/validation/parameter/starter set | First attempt: 273 passed / 7 failed solely because repo-local starter files were absent; after non-destructive starter bootstrap: **280 passed** in 29.34 s |
| Stable-v4/alpha2 and trace equivalence | **25 passed** in 7.44 s |
| Full headless `pytest` | **3,682 passed, 22 skipped, 3 deselected** in 391.33 s |
| `ruff check .` | **PASS** |
| `mypy engine/src/battle_engine` | **PASS**, 114 source files |
| `mypy client/src/battle_client` | **PASS**, 16 source files |
| Native-Windows GUI suite (`pytest tests/ -m gui`) | **507 passed, 6 deselected** in 183.60 s |
| Isolated Designer startup/close smoke | **1 passed** in 0.89 s |
| `git diff --check` | **PASS** |

The GUI suite and isolated Designer smoke both emitted Windows diagnostic
`0x8001010d` from `test_linux_designer_smoke.py` while continuing to a zero-exit
pytest pass. This is recorded as native Qt/COM evidence noise, not treated as
either silent clean evidence or a process-share failure. No GUI code was
changed in this phase.

No established equivalence or deterministic vector changed, and no golden data
was updated.

## 7. Fixed-seed adversarial smoke

All smoke runs used stable `bytefray-rules-4` and completed with exit 0.

| Match | Seed / ticks | Result | Replay SHA-256 |
| --- | --- | --- | --- |
| Quorum vs Core Defender, run 1 | 101 / 40 | A, last agent standing at tick 23 | `b797438db75a7fe076b8e132ff663fc71f7064cee2753e4ac73ab75c7910503e` |
| Quorum vs Core Defender, run 2 | 101 / 40 | identical match/result | same hash |
| Dual Team default vs Quorum, run 1 | 202 / 40 | tie, tick limit | `6754675f1786fd95626743040fa6bd9c98997b58f4d612520fc595122d0dbdc6` |
| Dual Team default vs Quorum, run 2 | 202 / 40 | identical match/result | same hash |
| local Octave vs Quorum | 1 / 40 | A, last agent standing at tick 8 | `0f8723f14aefbea819206790296bddac07edc2663b9f00b568055cb3a63b294d` |
| Dual Team `raider_share=0.7` vs Quorum | 202 / 40 | tie, tick limit | `c2b761097d662e8ee3aea4fa42d6306d505780e54388980956a75aef0cfc13cf` |
| Three entrants, Dual Team `0.33` / Quorum / Core Defender | 303 / 40 | A, tick limit | `9a8a194774b857e56e516cc7f719b1954b9372b49d1001a6042ebba17ab93d23` |

The repeated established/default cases had identical match IDs and replay
hashes.

## 8. Remaining known issues and scope boundary

Phase 0 findings 2 through 5 remain intentionally unchanged:

- uncapped, zero-cost process reach remains a future gameplay-research topic;
- last-mover atomic capture timing remains documented emergent behavior;
- disruption against dispersed processes and quota redistribution remain
  documented emergent behavior; and
- ownership-based localization through `previous_read_owner` remains a
  legitimate Agent API strategy.

No reach, disruption, movement, scheduler, capture, observation, core-seeding,
starter-balance, or V6 design work was performed. Phase 0 identified no other
RC1 implementation defect requiring remediation.

## 9. Final repository state

HEAD remains `2414be9fd977555ea205b372820b6f0bd0c69ed1`; no commit was created.
The tracked worktree contains only the three implementation/test/documentation
changes listed above plus this report. The two pre-existing stashes and
`.claude/settings.local.json` remain untouched. Ignored qualification output
under `.pytest-tmp/` and the non-destructively bootstrapped local starter
catalog are not release-source changes.

**Recommendation: proceed to the next RC1 phase after maintainer review of
this uncommitted Phase 1 diff.**
