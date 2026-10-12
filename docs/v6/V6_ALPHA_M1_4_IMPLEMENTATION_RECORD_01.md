# BYTEFRAY V6 — M1-4 IMPLEMENTATION AND VALIDATION REPORT

2026-10-11, America/Indianapolis.

**FORMALLY CLOSED — final lead acceptance recorded 2026-10-11 (see final acceptance below).**

The implementation report below is retained as submitted. The final acceptance
section supersedes its earlier readiness, closure-pending and unstaged statements.
Authorization is the lead's M1-4 authorization and continuation request,
following the adopted [Phase 0 packet](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md),
[M1 contract](V6_ALPHA_M1_CONTRACT_01.md), and accepted
[M1-3 verification semantics](V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md).

## Baseline and Part A preservation

Before product writes, local branch `v6-research`, HEAD, local upstream, and
live `origin/v6-research` all matched
`7d98e0a0caf915bd368ce408102c1404215635c7`. Tracked/index diffs were empty.
An initial sandbox inventory could not read two ACL-restricted research test
directories; the complete elevated read-only inventory resolved that limitation.

| Required source set | Files | Bytes |
| --- | ---: | ---: |
| Existing untracked research inventory | 58 | 900,519 |
| Original private E9 v2 study | 1,384 | 967,603,996 |
| Original source manifest / backup | 1,442 | 968,504,515 |
| Additional Git-ignored private test cache members | 5 | 4,279 |
| Final preserved union | **1,447** | **968,508,794** |

The original 1,442-file backup was created and independently verified before
product implementation began. The later recursive audit identified five
Git-ignored cache/log members beneath the private test directory; these were
preserved in an append-only supplemental manifest and copy, without rewriting
the original manifests. No required member of the 58 + 1,384 sets was excluded.

The destination is a private local NTFS directory outside the checkout on
physical disk 2 (C:); sources are on physical disk 1 (D:). Its leaf directory
is `M1-4_20261011_7d98e0a0`. The full local path is retained in the external
copy receipt. Its ACL has inheritance disabled and grants access to the local
user, SYSTEM and Administrators. No connected cloud service was used. This is
a separate-disk local backup; it does not establish off-machine recovery.

Files retain checkout-relative directory structure and exact bytes. Relative
paths and source ancestors were checked for traversal and reparse points;
final destination ancestors were also checked. No links/junctions, unsafe
paths, changing files, or hash failures were found in the selected sources.
A directory copy was used, so there are no archive extraction entries.
The supplement also retains the ignored cache directory structure.

External custody records:

- `source_manifest.json`: complete path/length/SHA-256/last-write inventory for
  the original 1,442 files; SHA-256
  `b14afef092cb621494fa7a1ad38c9c0d38aafca0e58205f7c75a91048ec481f7`.
- `untracked_inventory.txt`, `directory_manifest.json`, `copy_receipt.json`.
- `independent_verification_receipt.json`: **1,442/1,442** backed-up files and
  968,504,515 bytes independently reread with PowerShell `Get-FileHash`, against
  the persisted manifest, following the source's separate streaming SHA-256 pass.
- `ignored_cache_source_manifest.json`: the five supplemental members; SHA-256
  `f599c0c5dc7b3c4cccbc6870e32bc6341bb1f38e1ee6c85a6d55c16914fd56df`;
  `ignored_cache_verification_receipt.json` records their checks.
- `final_preservation_verification.json`: **1,447/1,447 source files** and
  **1,447/1,447 backup files**, exact lengths/hashes and unchanged source
  last-write values, **0 failures**, 1,384 study members, protected backup ACL,
  and zero destination reparse ancestors.

Manifests, private file inventories and backup payload remain outside public
Git. The optional published E9 ZIP disclosure inventory was not undertaken;
that ZIP was not modified or removed.

## Actual deliverables

| File | Change | Purpose |
| --- | --- | --- |
| `client/src/battle_client/sensing.py` | New | Frozen entrant views, historical sample/read models, verified phase cursor and separate operator verification summary |
| `client/src/battle_client/perspective.py` | Modified | Explicit `load_sensing_cursor` integration seam |
| `client/src/battle_client/player.py` | Modified | Phase playback controller using existing speed/pause conventions |
| `client/tests/test_v6_alpha_sensing.py` | New | 21 focused native acceptance and negative tests |
| `client/tests/test_v6_alpha_sensing_adversarial.py` | New | Eight independently authored hostile probes |
| `docs/v6/V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md` | New | This report and exact staging manifest |

No engine, ReplaySession, schema, historical fixture, research, renderer,
Designer, Qt, CLI routing, or gameplay file was changed.

## Knowledge projection contract

`SensingCursor.from_paths` invokes M1-3 artifact validation and ordered exchange
reconstruction. It accepts only the explicit product alpha1 identity and
rejects private research input paths before reading them. A constructor supplied
with an already verified M1-3 model remains a trusted adapter entry point.

The cursor retains a deep private copy because M1-3's frozen dataclasses contain
mutable dictionaries. Session metadata used in projection (including initial
reach and own region) must agree with the canonical bound replay. SHA-256 checks
bracket that metadata reread. Every tick boundary must agree with the verified
reconstruction; invalid construction restores the existing ReplaySession cursor.

Entrant presentation receives only `SensingView`, whose fields are frozen
dataclasses, primitive values, enums and immutable tuples. It has no world
record, replay state, binding/path, global decision index, hidden statistics,
opponent positions/core, or future teaching verdict. Own initial core/process
metadata comes from the checked canonical initial state; the eight-cell core is
the fixed alpha1 contract. Subsequent self samples use only the acting process's
validated observation; applied own MOVE may update its recorded own anchor.

An action-time SENSE emits a request, cost and pending explanation, never the
sampled contacts. Only the actual delayed OBSERVATION receipt adds the anonymous
addresses. `ABSENT`, `PENDING`, `REFUSED`, `EMPTY`, and `POSITIVE` are distinct.
A sibling callback cannot deliver another process's pending sample. Suppressed
ticks do not invent observations or empty scans. A terminal pending request
creates no receipt. READ value/owner enters history only through the actual
later same-process observation, correlated to the prior own READ.

Each delivered scan retains center, half-width, addresses and local sample and
receipt points. Contacts retain sample age and never track later opponent
movement. New occupancy claims affect only the inclusive circular scan window;
an empty scan marks previously sampled addresses there as absent in a newer
sample. Outside-window knowledge persists. Refusals do not clear knowledge.
Sample-time chronology governs replacement when sibling receipts arrive out of
order; an older late receipt cannot supersede a newer delivered sample. Complete
delivered scan history remains inspectable. READ owner never identifies a
spatial contact, and no hit, motivation, confidence or TTL is inferred.

## Phase cursor and reconstruction rules

Internal order is `(tick, global_decision_index, phase)`, with OBSERVATION before
ACTION and TICK_END after a tick's actions. Entrant navigation contains only
that entrant's recorded observation/action phases and canonical tick boundaries.
Labels use one-based entrant-local callback ordinals and the entrant's own
process identifier. Opponent callbacks create no rows, counters, blank phases,
status flags or pauses. The trusted navigation controller may enumerate the
entrant's recorded phases; that schedule is not execution knowledge in the view.

Forward/backward steps, exact permitted-phase seek and restart fold only the
selected permitted prefix. They reproduce identical immutable views regardless
of navigation history. Switching views maps the internal global order to the
last corresponding permitted prefix and rebuilds independently. Omniscient
mode has a separate payload labeled **Omniscient — full world state** and uses
M1-3's sub-tick world state. Entrant mode never receives that payload.

ReplaySession remains the canonical tick cursor. At sub-tick phases it is placed
at the preceding tick boundary; each TICK_END checks bytes, owners, anchors,
disruption and live entrants against canonical ReplaySession state. The adapter
also checks complete boundary membership and ordered observation/action pairs.
No suppressed callback or missing gameplay fact is interpolated.

`PhasePlaybackController` reuses the existing speed constants and pause/step
conventions. Each permitted phase takes a constant presentation interval. It
never uses opponent callbacks, trace wall times, diagnostics or event salience
for pacing. Discrete navigation/view switching pauses and clears accumulated
time. Invalid loading reports a constant sanitized message and leaves canonical
replay-only viewing available; the caller must label that fallback explicitly.

## Verification separation and M1-3 compatibility

`VerificationSummary` is a separate operator report containing artifact-pair
consistency, independent reconstruction, M1-3 teaching step statuses, complete
teaching success, and whether an entrant projection was constructed. It is
absent from entrant payloads and controller presentation output.

M1-3's `VERIFIED`, `NOT_VERIFIED`, and `NOT_PROVEN` are carried unchanged. A
consistent pair without the required receipt-consistent MOVE may project safely
while teaching completion remains false. A request without terminal delivery
keeps missing steps `NOT_PROVEN`. Pair-mode success is not teaching success.
No descriptions claim an agent's reason for acting. No M1-3 evaluator or wire
contract was modified.

## AC5/AC7 and independent adversarial review

The independent reviewer started in a fresh context after implementation and
authored hostile tests separately. Two medium findings were reproduced:

| Finding | Reproduction | Resolution |
| --- | --- | --- |
| F1: session metadata insufficiently bound | Rewritten replay with identical match/world state but own reach 128→1 supplied reach 1 while reporting consistency | Compare session header, initial process records and regions with the canonical bound replay; bracket reread with raw digest checks |
| F2: view switch reused mutable evidence | After construction, caller mutated an A observation's anchor dictionary; A→omniscient→A changed anchor 0→333 | Deep private snapshot of the verified model; every view switch consumes that snapshot |

The reviewer independently reran **29 focused tests**, including eight hostile
probes, and confirmed **PASS**, both findings closed, no remaining blocker in
the authorized scope. Additional probes cover replay drift after reconstruction,
failed construction preserving the prior complete session state, private paths
rejected before any read, and older sibling receipt ordering `[sample 3, sample 1]`
retaining sample 3 as the newest evidence.

AC5 is explicitly exercised by whole-view equality across native executions
with different undelivered movement and different hidden callback counts. The
comparison includes rows/order, local phases, sample/receipt labels and ages,
messages and pacing units. Early SENSE/READ values, live tracking, identity/core
joins, empty-versus-absent confusion, global counters, research imports/private
reads and research seed operations are negatively tested.

AC7 is explicitly exercised by sequential versus direct/reverse seeking,
restart, repeated navigation, perspective switching, one-phase stepping,
pause/speed handling, suppressed-tick delivery and every canonical tick boundary.

## Validation evidence

All runs used repository `.venv` Python with `-B`, fresh product-only basetemp
directories under `.pytest-tmp/`, and `-p no:cacheprovider`. The resulting
`Unknown config option: cache_dir` warning is caused by disabling that provider;
there were no test failures in the final runs.

| Final validation scope | Result |
| --- | --- |
| M1-4 focused/native suite | **21 passed** |
| Independent hostile suite | **8 passed** |
| Existing client headless tests | **504 passed** |
| M1-3 verifier regressions | **30 passed** |
| M1-2 teaching runner regressions | **19 passed** |
| M1-1 policy/capability regressions | **42 passed** |
| Historical v4 immutability | **5 passed** |
| Stable-v4 equivalence | **27 passed** |
| Native match service | **6 passed** |
| Agent validation | **44 passed** |
| Designer ruleset options (existing headless scope) | **23 passed** |
| Combined requested current regression selection | **729 passed, 3 GUI tests deselected** |
| `ruff check .` | **Passed** |
| `mypy engine/src/battle_engine` | **Passed, 102 source files** |
| `mypy client/src/battle_client` | **Passed, 17 source files** |
| Git diff formatting and new-file whitespace checks | **Passed** |
| Retained historical Seal-08 baseline raw pins | **329/329 unchanged** |
| Final private preservation check | **1,447/1,447 source and backup files unchanged** |

The combined regression invocation selects all `client/tests` plus
`test_v6_alpha_m1_3_sensing_playback.py`, `test_v6_alpha_m1_2_window_scout.py`,
`test_v6_alpha_m1_policy_capabilities.py`, `test_v4_historical_immutability.py`,
`test_v4_stable_ruleset_equivalence.py`, `test_native_match_service.py`,
`test_agent_validation.py`, and `test_designer_ruleset_options.py` under
`engine/tests`. Final JUnit evidence is
`.pytest-tmp/m1_4_regression_review_final.xml`; independent focused run roots
include `.pytest-tmp/m1_4_review_recheck_final_01` and
`.pytest-tmp/m1_4_review_recheck_guard_01`.

The adopted [two-context historical disposition](V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md)
is preserved. Current product checks above do not qualify the checkout as the
original research instrument. The 329 raw pins were rechecked read-only in
`work/m1_1_frozen_baseline_20261010/`, with zero failures. Its previously accepted
72-node historical test execution was not rerun in this assignment. No full
unpartitioned repository-suite or cross-platform acceptance pass is claimed.
No frozen assertion, manifest, authority record, research golden or artifact
was rewritten, resealed or regenerated. No research process, G consumption,
research entropy/seed generation, or payoff execution was performed.

## Exact file-by-file staging manifest and remaining boundary

This is a review manifest only. **Nothing is staged, committed or pushed.**

```text
client/src/battle_client/sensing.py
client/src/battle_client/perspective.py
client/src/battle_client/player.py
client/tests/test_v6_alpha_sensing.py
client/tests/test_v6_alpha_sensing_adversarial.py
docs/v6/V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md
```

Pre-existing private/untracked research, local settings, backup/manifests,
ignored test outputs and retained historical work directories are excluded.
No engine file belongs in this staging manifest.

Recommendation: accept the bounded M1-4 implementation for lead review. There
is no outstanding in-scope blocker after independent corrections. Formal closure
remains the lead's decision. M1-5 renderer/Designer/Qt/CLI routing and display
interaction have not begun; broader M1 platform and release qualification remain
separate. Future UI wiring must keep raw replay/world state, the operator
verification report and future navigation metadata out of entrant knowledge
payloads. This report grants no implementation, research or publication authority
beyond the completed assignment.

## Final acceptance and formal M1-4 closure (2026-10-11)

The project lead provisionally accepted the implementation and qualification
results, then explicitly authorized formal closure if the five acceptance
boundaries were established without unresolved blockers. The complete record,
including independent findings F1/F2, corrections and acceptance evidence, was
read before the final checks. All five boundaries are confirmed:

| Acceptance boundary | Final evidence and disposition |
| --- | --- |
| AC5 noninterference | Confirmed: native witnesses with identical permitted prefixes but different hidden movement/callback counts have equal complete entrant views and permitted phase lists. Equality includes rows, event counts/order, receipt/sample points, ages, labels/messages and constant pacing metadata. Opponent/global indices are absent from entrant payloads. |
| Deterministic seeking, rewind and restart | Confirmed: sequential, repeated, direct and reverse navigation reproduce the same prefix; restart removes later contacts/reads; omniscient-to-entrant switching reproduces the permitted prefix. Deep-copied evidence prevents caller mutation from changing a later switch, and failed construction restores the prior complete ReplaySession state. |
| Verification separation | Confirmed: artifact consistency, independent reconstruction, complete teaching verification and entrant projection remain distinct. Consistent incomplete/unverified exchanges do not earn teaching success. M1-3 statuses remain unchanged; operator verdicts are absent from entrant execution payloads. |
| Private backup and original-source preservation | Confirmed: both manifest hashes match the submitted record; 1,442 original plus five supplemental members total 1,447 files and 968,508,794 bytes. Every source and backup member was reread and matched for hash/length, with unchanged source last-write values and zero failures. Exact study membership remains 1,384 files / 967,603,996 bytes. Destination remains outside the checkout on C: disk 2, distinct from D: disk 1, with protected local-user/SYSTEM/Administrators ACL and no reparse ancestors. The exact local destination remains recorded in the external copy receipt. |
| Prior milestones, historical preservation and scope | Confirmed: no engine, prior M1 closure record, research, ReplaySession, renderer, Designer, Qt or CLI-routing change relative to required HEAD. All 329 retained frozen-baseline pins match; historical checks retain the adopted separate environment. M1-5 was not started. |

The final acceptance regression run passed **729 tests**, including **21 M1-4
acceptance tests**, **eight independent hostile probes**, **30 M1-3 verifier
tests**, **19 M1-2 tests**, **42 M1-1 policy/capability tests**, and **32 stable-v4
historical/equivalence tests**. Three display-backed GUI tests were deselected
by the unchanged headless configuration; no failures, errors or skips occurred.
The cache-provider warning described above remains non-failing. Fresh JUnit:
`.pytest-tmp/m1_4_acceptance_20261011_01.xml`. Repository Ruff, engine mypy
(102 files), client mypy (17 files) and tracked diff formatting also passed.

The five source/test files match the exact byte digests verified at the end of
implementation; this acceptance task changes only this existing implementation
record. F1 remains corrected by canonical session metadata comparison and
bracketing raw replay digest checks; F2 remains corrected by the deep private
playback snapshot consumed across view switches. Both hostile reproductions
pass. There are no unresolved in-scope findings or acceptance blockers.

**Under the lead's explicit conditional final-acceptance authorization,
Milestone M1-4 is formally CLOSED.** Qualification disposition: **ACCEPTED —
bounded M1-4 implementation and final acceptance checks passed.** This closes
M1-4 only; broader M1 platform/display and release qualification remain separate.

The unchanged six-file manifest above is authorized for staging. Staging must
include both independent-review corrections and their regression tests, pass
`git diff --cached --check`, and contain no private E9 evidence, backup payload,
manifest, archive, ignored test output or unrelated change. Commit and push are
not authorized. M1-5 remains unstarted and unauthorized by this closure.

Proposed commit message:

```text
feat(client): add verified sensing projection and phase playback (M1-4)
```
