# E9 v2 Seal-07 expanded boundary and dependency return (02)

PROPOSED, 2026-10-07. Planning only; no source/test edits or implementation
authorized. This additive revision applies Disposition 04, raw SHA-256
`d3db6c9bac4271384b933da01fa253a0c64d3249c93efa65a819d43f5ccf0839`.
It supersedes revision 01 as a proposal, while preserving revision 01's bytes
and evidentiary history. Revision 01 raw SHA-256:
`b0ae22ce15f1e5caa15a167b2f13cb0972eef62f2e0c6bee04ddf92c51821955`.

Baseline: HEAD `2dd8f69c5c6feb5f3a7d8fc0eb81b0c06802dee2`, branch
`v6-research`; no tracked staged/unstaged diff, substantial inherited untracked
work. All 293 implementation and 32 qualification files match the Seal-06
manifests. No test suite was run for this planning revision. Line numbers refer
to those unchanged Seal-06 bytes.

Seal 06 remains PASS WITH FINDINGS; its sealed independent reproduction is
PASS, 877/877. F1 requires Seal 07; F2 blocks operational W. F3-F5 remain
record-only. Gate-8 operational acceptance, Requirement C and historical
coverage remain NOT ESTABLISHED; execution is LOCKED; Q is absent. The accepted
provenance backup is untouched. No Seal-07 scope record may be written yet.

## 1. Proposed exact file boundary

The selected planning candidate uses a shared regular-file read boundary and
producer-local staged publication. It does not change generic write-once
semantics. The candidate is subject to the dependencies in section 7 and to
approval of the additional exact legacy-test changes below.

| File | Permitted proposed change |
| --- | --- |
| `tools/research/v6/e9/v2/records.py` | Add a typed durable-read-unavailable exception and shared `read_regular_bytes`; route only the W-reachable existing reads listed in section 2 through it. No record, schema, digest or `write_once` change. |
| `tools/research/v6/e9/v2/authority.py` | Route the exact reads in section 2 through that helper. Preserve validation, locking, actor/binding/event decisions, resolver precedence and all writer semantics. |
| `tools/research/v6/e9/v2/inventory.py` | Route `frozen_limitations`' contract read, line 67, through the helper. No inventory/history/membership computation change. |
| `tools/research/v6/e9/v2/private_verification.py` | Guard the exact reads below; producer-local publication of intents, outcomes, verification results, retained W and W.json; exact same-state recovery and interruption accounting. Preserve all public signatures, scientific verification and wire shapes. |
| `engine/tests/test_v6_e9_v2_gate8_seal07.py` | New implementer qualification for the expanded read/write boundary and recovery. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py` | New qualification by a fresh independent test-author context after scope freeze. |
| `engine/tests/test_v6_e9_v2_gate8_seal06.py` | Only the exact F3 observer/fixture changes returned in section 5; additional approval required. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py` | L1 plus the exact F3 observer/fixture changes returned in section 5; a new independent author alone edits this qualification file after frozen-scope inclusion. |

Every other implementation and sealed test file is excluded. In particular,
`commitment.py`, `generation.py`, `integrity.py`, adoption/identity code, the
test helper, conftest, configuration, guard, harness and reproduction script
stay unchanged. All protocols, contracts, schemas, scientific inputs, prior
seals/manifests/evidence/dispositions/confirmations remain immutable. New
manifests, qualification records and the later scope are separate future
records, not permissions to edit an old record.

`inventory.revealed_lists` belongs to the inventory-verification gate, not the
traced W verifier call graph. It is excluded. No generic transaction framework,
automatic lock repair, standalone admissibility oracle or unrelated E9
crash-hardening is proposed. An additional file needed by a different read or
publication mechanism must be returned before freeze, not silently added.

## 2. Expanded durable-file read map

The operational W boundary includes protected W production and the existing
protected consumers that validate the producer's W. It also includes attempt
reads and the production source callback required to enter that operation.
The authority's supplied resolver/source callbacks remain explicit dependencies:
an arbitrary callback cannot be certified safe merely by changing AuthorityLog.
Operational construction must use the audited production source checker and a
resolver whose filesystem reads use this boundary; an additional reader in
such a callback is a scope conflict.

| Module/function and baseline lines | Durable path/read | Reachability and proposed exercising tests |
| --- | --- | --- |
| `authority.pinned_source_checker` 61-80, read 78 | Every I/Q source-manifest file | `_check` before action and post-action recheck; S7-R01 tests a rejected file in both passes. Its adopted-P read calls `records.read_record`, below. |
| `authority.durable_bytes` 83-91, read 90 only | Newly written file readback | W-local staging uses the unchanged exclusive writer; S7-R02 guards readback. The write/flush/fsync and collision rules do not change. |
| `authority._state` 130-197, reads 139, 190 | All event files; active.json | `protected` entry/recheck, including historical tuple validation; S7-R03 rejects each without open/read and proves the action is not entered. |
| `authority.resolve` 204-218, read 208 | Retained record JSON, including earlier tuple records and supplements | `_state`, `_check`, `_resolver`, full verification and W consumers; S7-R04 covers retained hits and audited fallback resolution. |
| `authority.retain_record` 220-229, read 225 | An existing retained record | Reachable through existing W-consuming operations; S7-R05 tests immutable comparison with guarded reads. Writer semantics unchanged. |
| `authority.retain_artifact` 231-240, read 236 | An existing retained artifact | Existing protected W consumers; S7-R06 tests guarded immutable comparison. Writer semantics unchanged. |
| `authority.read_artifact` 242-250, read 245 | Referenced private evidence | Historical state checks and W-consuming private-value reads; S7-R07 tests refusal/unavailability before content is read. |
| `authority.registered_producers` 255-281, reads 259, 276 | Every registry entry, including another G; event reads inside its scan | `_operational_boundary` and W-consuming private-value checks; S7-R08 includes a non-regular other-G entry. |
| `records.catalogue` 47-48, read 48 | Frozen schema catalogue | Repeated record/ref validation in `_state`, `_check`, verification and record derivation; S7-R09 tests entry and verification phases. |
| `records._field` 156-283, reads 219, 274 | Frozen contract for InventoryStatus/permanent limitation | A/R/O/V/W validation paths; S7-R10 tests both branches. Only these read expressions change. |
| `records.read_record` 415-423, read 416 | Adopted P through production source callback | Before action and recheck; S7-R11 proves prompt rejection and unchanged raw/body validation. |
| `inventory.frozen_limitations` 66-68, read 67 | Frozen contract | `_check`'s A/R limitations checks; S7-R12 proves this read is guarded. |
| `private_verification._outcomes` 74-75, read 75 | Published attempt outcomes | `_preconditions` and A4; S7-R13 covers non-regular outcomes and staging exclusion. |
| `private_verification._reader` 100-112, read 106 | Payload, salt, audit, K, boundary and retained history/execution evidence; verification-result read by A5 | Complete W verification and admissibility; S7-R14 parameterizes all roles. |
| `private_verification._durable_log` 115-116, read 116 | Authority events | Preconditions, derivation and A6 after authority's own read; S7-R15 proves the repeated read is also guarded. |
| `private_verification._durable` 178-183, read 181 | Registry, first-raw marker, W.json and PASS intent | `_operational_boundary`, exact recovery and A3/A4; S7-R16 tests each path. |
| `private_verification._frozen_limitation` 431-433, read 432 | Frozen contract text | Protected pre-U template validation; S7-R17 covers this repeated contract read. |
| New producer-local publication/recovery readers | Pending candidates, published intent/result/W/outcome comparisons | S7-R18 tests every new reader through the same helper; no unchecked read is introduced. |

`register_producer`, `assert_producer`, `mark_first_raw`, generation's direct
reads and integrity-service event reads are not called on the traced W path.
Their separate operations are excluded. `_state`'s renewal-receipt branch uses
`read_artifact` and `resolve`, already included; do not ignore historical
pre-generation events just because W runs after generation.

Existing regressions exercise the core paths: both Seal-06 F1 modules, W-01
through W-14 in both producer modules, the independent authority tests
(including `test_faulted_durable_state_retained_and_never_repaired[crash_lock]`),
both publication modules, and the records tests. Those tests do not themselves
prove FIFO/device rejection; the new per-read S7-R tests must do so.

## 3. Read mechanism and classifications

Candidate: stat the target, reject a non-regular mode before opening, use
`Path.open('rb')`, confirm `fstat` regular-file mode before reading, then read
and preserve existing byte/hash validation. Follow symlinks to regular targets
as the existing reader does; reject non-regular targets. Catch failures with a
distinguishable durable-read-unavailable exception so content mismatch and
filesystem unavailability are not conflated. Do not cache file-type results.

This rejects a pre-existing FIFO, socket, device, directory or unsupported
object without attempting its open. It does **not** prevent an external actor
replacing the stat-checked regular path before open; open itself can then block
before fstat runs. Post-open confirmation cannot cure that TOCTOU gap.

The old scope states that an actor able to forge every on-disk artifact is out
of scope. That sentence alone does not establish exclusion of a single hostile
concurrent path swap. The candidate therefore returns D7-02: the exact
concurrent-writer threat-model boundary must be confirmed before this mechanism
is frozen. No protection against arbitrary filesystem tampering is claimed.

The sealed negative-read observers remain effective: independent Seal-05
`private_read_spy` at lines 767-785 observes `Path.open` and
`AuthorityLog.read_artifact`; its W-06 cases at 1087-1121 and 1124-1132 prove
refusal before private reads. Seal-06 `block_reads`, lines 139-153, observes
io/builtin/os opens. New tests must also fail on *any* open of each stat-rejected
path, and on *any* content read after an fstat rejection. Descriptor closure
must be checked.

If D7-02 cannot be satisfied, do not switch quietly to `os.open`: return a
revised boundary including the precise Seal-05 observer update and its affected
W-06 cases. Non-blocking POSIX opening alone is not a demonstrated Windows
solution. Preserve the observation guarantee on every supported backend.

Classification applies at the existing caller boundary:

- Registry/marker/retained scientific evidence unavailable during verification:
  UNAVAILABLE. Exact restoration can retry; substituted bound bytes remain
  FAILED_VERIFICATION. Keep F1's mismatch precedence and F5's recorded ordering.
- Unavailable authority/source state that prevents protected entry:
  REFUSED_PRECONDITION; the action and private verification do not run.
- Non-regular W, PASS intent/outcome or other unprovable continuation state:
  existing non-terminal refusal/admissibility denial. Never read it as content
  or reinterpret incomplete bytes as an affirmative record.
- The new typed error is mapped by phase and provenance; it does not turn
  arbitrary exceptions or content-integrity failures into recoverable outages.

## 4. Bounded producer crash-consistency design

Selected candidate: keep the complete verifier and its inputs unchanged, but
publish each producer output only after its full canonical bytes have been
written to a fresh candidate, flushed/fsynced, safely read back and compared.
Install the candidate at its canonical destination with a same-filesystem,
atomic, **no-overwrite** publication primitive. An existing canonical destination
is compared with re-derived bytes; it is never replaced. Do not use ordinary
POSIX rename/replace if it can overwrite an existing destination.

Candidate storage is inside the private authority root, under an opaque
per-S/per-attempt staging namespace. Attempt ordinals derive from the union of
published intents and retained allocated staging attempts, so a death before
intent publication cannot cause ordinal reuse or an unexplained gap. No random
name, entropy source or scientific generator is needed. Retain incomplete
candidates and attempt evidence. A later attempt writes a fresh candidate for
the same re-derived output; it never repairs arbitrary bytes in place.

Introduce producer-local result/W retention functions in `private_verification`
that compute the same ArtifactRef/RecordRef and perform the same validation and
immutable comparison, using the local publication helper. Replace only the
W producer's calls at `_verify` 361-364 and `produce_private_verification`
406-408. Generic AuthorityLog retention/write functions and
`records.write_once` keep their writer semantics. Preserve the observable
`pv.durable_bytes(path, raw)` logical publication seam for intent/W/outcomes;
the actual staging and publication must additionally be observed by qualification.
No temporary monkeypatch of an authority/global writer is a production design.

Process-death candidate backend: same-filesystem hard-link installation with
existing-destination refusal, retaining the candidate. This is a proposal,
not a qualified storage guarantee. Atomic namespace installation and file fsync
alone do not establish directory-entry durability after power loss, and all
candidate names/inodes are immutable once published. D7-01 holds the exact
Windows/POSIX power-loss publication mechanism and filesystem preconditions
open. There is no direct-write or overwrite fallback on an unsupported root.

Before retry publication, rerun the complete verifier, independently re-derive
the verification result and canonical W, and compare every existing published
result/retained W/W.json with those exact bytes. Any complete conflicting
destination, contradictory outcome or scientific-input mismatch disables
recovery. A hash-filename mismatch or a byte-prefix match alone is not proof
of interruption and does not authorize mutation.

For canonical W already present with PASS absent, additionally require:

1. Exact same tuple through S, scientific inputs and instrument, registered
   independent verifier, and the originating attempt bindings.
2. No later issued role, terminal/contradictory outcome, or existing PASS.
3. No authority event since the protected producing state, including HOLD or
   an otherwise permitted redundant/tuple-extending ISSUE. Compare the durable
   tip/log and originating intent; do not rely only on epoch or W-04 categories.
4. Full re-verification and independent W re-derivation; retained W bytes must
   equal re-derived bytes byte for byte before any missing publication.

A changed verifier or authority state gives REFUSED_PRECONDITION. That event
alone is not a scientific failure. Exact complete material mismatch is an
integrity failure under existing verification semantics, not an opportunity
to substitute outputs. Recovery writes PASS for the new separately recorded
attempt; earlier incomplete attempts remain INTERRUPTED. The new intent binds
the same S, verifier and W-producing tip. Preserve outcome keys and A4's exact
single-PASS rule. Recovery does not republish W.json when it is complete.

The following table enumerates the whole producer sequence. At each candidate
write/publication pair, a process death can leave no canonical destination or
the exact complete canonical destination; a partial candidate is not canonical
evidence. This claim is conditional on D7-01's storage guarantee. A torn final
destination under the old direct writer cannot be inferred to be a crash just
from its bytes; it is a returned migration/durability dependency, not an
accepted operational residual.

| Boundary; state before | Possible durable state after death | Retry classification; exact recovery and permitted writes | Never mutate/delete; substitution check |
| --- | --- | --- | --- |
| B0: allocate attempt; prior ledger only | Allocated attempt directory, no or incomplete candidate intent | INTERRUPTED allocation; new ordinal, new canonical intent. Derive ordinal from retained allocation plus published ledger. | Keep previous allocations/attempts; unexplained forks/gaps refuse. |
| B1: intent candidate; allocated ordinal | Missing/partial/complete uncommitted intent candidate | INTERRUPTED; keep candidate and record next attempt. No private read is needed to classify allocation. | Never accept a partial intent; complete published intent must be canonical and bound. |
| B2: intent publication; exact candidate readback | No canonical intent or exact complete canonical intent | INTERRUPTED if no completed outcome; new attempt. Do not reuse the old ordinal. | No overwritten intent, silent re-encoding or invented prior outcome. |
| B3: lock acquisition / protected checks / full verification; published intent | Stale lock; intent only, no outputs | No automatic lock recovery. After separate incident clearance, repeat checks and complete verification. Authority refusal remains non-terminal; actual scientific failure remains terminal. | Preserve lock evidence and all scientific inputs; no generation/salt calls. |
| B4: verification-result candidate; successful complete verification | Partial/complete unpublished result candidate | INTERRUPTED infrastructure write, not FAILED_VERIFICATION; reverify and re-derive exact result, write a fresh candidate. | No modification of bound payload/salt/audit/K; do not use an uncommitted candidate as verification evidence. |
| B5: result publication; exact result candidate | No published result or exact complete hash-named blob | Repeat complete verification; reuse identical published blob, otherwise publish re-derived exact blob once. | Published wrong bytes are not recoverable interruption; no collision deletion/regeneration. |
| B6: retained W candidate; result already published | Partial/complete unpublished W record candidate | INTERRUPTED; repeat full verification and independently derive identical W; write fresh candidate if needed. | No second scientific state; result must remain identical. |
| B7: retained W publication; exact validated W candidate | No retained W or complete canonical retained W | Reuse only exact re-derived record; complete missing retention once. | Never overwrite retained W; full raw/body/actor/tuple/tip equality. |
| B8: W.json candidate; retained W complete | Partial/complete unpublished W.json candidate | INTERRUPTED; reverify, compare retained result/W, write fresh candidate for same W. | Unpublished partial bytes are not W; no W substitution. |
| B9: W.json publication; complete candidate | W.json absent or exact complete W.json, PASS absent | F2 exact recovery: full re-verification and W re-derivation; same authority state; publish only missing continuation. | Complete W.json is immutable and never written again; exact raw comparison. |
| B10: PASS candidate; complete matching W and retained evidence | Partial/complete unpublished PASS candidate | INTERRUPTED, never PASS or scientific failure. New attempt fully reverifies/re-derives; publish its missing PASS only after all checks. | Keep partial candidate; incomplete bytes never satisfy A4; no second W. |
| B11: PASS publication; exact candidate | PASS absent or exactly one canonical complete PASS | If absent, same-state exact recovery. If complete, ordinary repeat refusal before verifier call. | Do not overwrite a PASS, contradict it or add a second PASS; bind its own intent and exact W. |
| B12: protected post-action source/authority recheck; complete W/PASS | Complete W/PASS but caller did not return, or source check raised | Preserve existing propagated error/no second outcome. Resolve the source/authority issue before lead ISSUE(+W); no recovery bypass. | Keep W/PASS; no success inferred solely from returned/absent process status. |
| B13: producer return; recheck passed | Complete outputs even if caller loses response | Ordinary repeat refusal; read-only consumer validation after separately authorized W issuance. | No further scientific write or duplicate PASS. |
| E1/E2: non-PASS outcome candidate/publication after lock release | Missing/partial candidate or full refusal/unavailable/failure outcome | Repeat the same checks on a new attempt. A prior interrupted diagnostic write alone is not terminal; genuine scientific faults must fail again. Existing complete FAILED_VERIFICATION remains terminal. | Preserve prior evidence; do not convert or suppress a complete terminal outcome. |

This includes C1-C10 of revision 01, and separates candidate-write and
publication boundaries. It closes future torn result/W/PASS writes by
prevention, rather than by trusting crash-shaped prefixes. An unknown torn
canonical destination must remain fail-closed without automatic deletion,
rewriting or a claim that infrastructure caused a scientific failure. If the
lead requires automatic completion of legacy torn canonical artifacts, return
D7-03 before freeze: it needs an authenticated interrupted-write distinction
or a separately specified preservation/recovery mechanism. No operational
W has been authorized, and no such real-study artifact is presumed to exist.

## 5. Targeted sealed-test conflict sweep and exact proposed edits

Read-only search/AST sweep covered all **25** `test_v6_e9_v2_*` modules in the
Seal-06 qualification manifest, plus their producer fixtures/observers. It
selected 52 test functions mentioning outcomes, partial/torn writes, collisions,
retention or write observers. No qualification was run and no test was edited.
No sealed test directly injecting a torn PASS file, torn verification-result
blob or torn retained W record was found. Their new guarantees need new tests;
that absence is not qualification evidence.

L1 is the already authorized semantic supersession:

- `test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[outcome-1-stop]`,
  function 679-714, shared retry assertion block 702-709. Replace only this
  branch's never-PASS expectation with exact reverified recovery to a single
  PASS; W bytes remain identical. A new independent author edits after freeze.

Additional semantic/fixture conflicts returned for explicit scope inclusion:

- L2a: implementer
  `test_v6_e9_v2_gate8_seal06.py::test_s6_f3_a_partial_w_file_leaves_no_outcome_and_fails_closed`,
  339-356. It currently injects partial bytes into the canonical W destination
  and expects permanent refusal. A test of the new writer's actual interruption
  must tear the staged write and prove same-state recovery without modifying
  that torn candidate. Preserve a separate refusal assertion for unproven
  partial canonical W, rather than silently accepting those bytes.
- L2b: independent
  `test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[W.json-partial_then_stop]`,
  fixture write at 692-693, shared assertions 702-709. The same staging/final
  distinction applies. This additional case is **not** authorized by Q6's L1
  permission. It must be included/approved before a new independent author
  changes it.

The staged writer also changes observation, not the under-lease safety
property. The exact observer/fixture boundary returned is:

| Existing module | Exact observer and affected F3 cases | Proposed narrowly scoped change |
| --- | --- | --- |
| Implementer Seal-06 | `write_spy` 263-280; `test_s6_f3_w_retention_w_json_and_pass_are_written_under_the_verifying_lease` 283-293; `test_s6_f3_an_authority_append_cannot_interleave_before_pass` 296-316; `test_s6_f3_a_write_failure_leaves_no_outcome_and_is_listed_as_interrupted` 319-336; partial-W case 339-356; `test_s6_f3_non_pass_outcomes_are_written_after_the_lease` 375-390, all three outcome variants | Observe the producer-local W-retention helper, physical candidate writes and no-overwrite publication; inject retention/staging failures at their actual seams; retain logical order, lock/tip checks, non-PASS placement and exact interrupted ledger assertions. The exact direct-write name list cannot stand as the complete physical-write list. |
| Independent Seal-06 | `Writes` 251-334 and `PASS_WRITES` 611; `test_s6_f3_01_W_retention_W_json_and_PASS_are_written_under_the_lease_at_its_tip` 614-635; `test_s6_f3_02_an_append_attempted_before_the_PASS_write_is_refused_as_busy` 638-669; `test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome` 679-714, all four variants; `test_s6_f3_04_a_post_action_recheck_failure_after_PASS_propagates_with_one_outcome` 717-731; `test_s6_f3_05_non_pass_outcomes_are_written_after_the_lease_is_released` 737-754, all three variants | Add observation of local retention and publication (the current spy watches opens/replace, not hard-link installation). Preserve failure/interleave injection at the logical phases; add physical-stage faults. PASS publication remains the final successful durable producer transition under the verifying tip. |

All four f3_03 variants are explicitly returned because the observer seam
changes, although only L1 and L2b change their operational assertions. The
post-action recheck test keeps its outcome property; only its fault seam moves.
These are proposed changes, not a standing permission to edit every assertion
inside the functions or to weaken any existing refusal/lock/negative-read check.

Unproven partial canonical W remains refused in Seal-05 implementer W-09
(578-593) and independent `test_w09_partial_w_file_fails_closed` (1226-1234).
Those tests inject arbitrary canonical bytes, not a writer-produced staged
interruption, and stay unchanged for this candidate. Existing issued-W
missing/mismatched-PASS and verification-result corruption cases also remain
unchanged: consumers are read-only and never perform recovery. No conflicting
generic collision test was found that needs modification for producer-local
publication.

Preserve the complete Seal-06 modules and manifests in the future Seal-07
evidence before editing; immutable prior manifests continue describing their
original bytes. Record whole-module and exact changed-block before/after raw
hashes and retain their source copies. Baseline function hashes below cover
raw lines from `def` through the last AST statement, including original line
endings, excluding decorators; they are identification aids, not after hashes.

| Function | Baseline raw SHA-256 |
| --- | --- |
| Implementer under-lease write case, 283-293 | `e7be769ea5435d3bb55c910a611f0c5780f5ea05b492b79749e1309adbbe2cbb` |
| Implementer partial-W case, 339-356 | `d96f86cbbe0dbccd94617c0ecf8094400e8ae2f47b1346bc1085832381aa275d` |
| Independent f3_03, 679-714 | `f5262cfc34a4b7a62f36d63c39470645447e21dfdbf518e71c7c2b501e298258` |

## 6. Qualification and manual incident runbook requirements

For every S7-R read case, inject FIFO, socket, character/block device, directory
and unsupported mode at the exact path. Assert bounded completion and zero
open/read of the rejected path, including entry and recheck. Exercise stat/open
errors, fstat rejection/descriptor closure, symlink targets, repeated event
reads and another G's registry. Keep sealed negative-read spies active. POSIX
native FIFO/device confirmation must run in a bounded subprocess on a suitable
host; Windows mode injection alone must not be described as native POSIX proof.
Report any platform limits/skips honestly.

S7-C01 through S7-C16 must cover B0-B13 and E1/E2 respectively: death before,
during and after candidate write/fsync/readback/publication, plus repeated death
during recovery. Use fresh synthetic roots and explicit process-death tests
where supported. An exception unwinding `finally` is not a stale-lock crash.
Power-loss qualification is separate from process kill and cannot be inferred
from it. Test the selected filesystem's no-overwrite publication and namespace
durability contract once D7-01 is resolved.

Cross-boundary recovery cases must prove unchanged S/G/boundary/payload/salt/
audit/K/instrument, complete verifier invocation on every recovery, independent
raw W equality, immutable retained result/W, no W.json rewrite, exactly one
PASS, and no generation/entropy/salt/publication calls. Cover different verifier,
changed scientific bytes, complete substituted outputs, missing/unreadable
required inputs, contradictory and terminal outcomes, and every intervening
authority event including HOLD and redundant ISSUE. An intervening event gives
non-terminal refusal. Keep all bytes/tree deltas as private synthetic evidence.

After recovery, later retries must refuse before calling the verifier. Only
separately issued W may progress through unchanged A1-A6 and the pre-U/U
consumer checks. F3's helper-context limits and F5's ordering observation remain.

The future stale-lock runbook must require all of:

1. Establish the original holder process is no longer running.
2. Establish no other legitimate process owns or uses the authority root.
3. Retain/hash lock bytes and relevant filesystem metadata before removal;
   an unsupported/unreadable lock needs a separately specified safe incident
   evidence action, not a blocking read.
4. Record the evidence and reason for declaring the lock stale.
5. Record operator/lead authorization and the exact clearance action.
6. Perform no scientific-data substitution, deletion or regeneration as part
   of clearance. Do not append an authority event and then attempt to pretend
   the interrupted W transition had no intervening event.

There is no standing clearance authorization and no automatic recovery code.
Synthetic stale-lock removal proves only the qualification scenario.

After eventual scope/implementation authorization: focused guarded qualification,
then the required broader guarded run and static checks under the established
manifest procedure. All unchanged sealed tests remain regressions; only
explicitly approved supersessions may change. Rehash before/after; append new
attempt records/manifests; no rerun claim based on the old 877 result. A distinct
independent qualifier must reproduce the new seal; neither the implementer nor
the new independent author qualifies their own work. Retain private transcripts
and record only their identities/hashes publicly. No new author is commissioned
to edit tests during this planning turn.

## 7. Dependencies returned before scope freeze

| ID | Unresolved boundary/guarantee | Required disposition before freeze |
| --- | --- | --- |
| D7-01 | The exact no-overwrite publication primitive and namespace durability after power loss on the intended Windows/POSIX filesystem are not established. Direct writes plus file fsync leave torn destinations; atomic linking without metadata durability is not sufficient proof. | Establish a bounded producer-local backend/storage contract and its qualification. If a generic record/write-once infrastructure change is required, stop and return that additional exact file/function dependency. No power-loss safety claim or direct-write fallback. |
| D7-02 | The existing scope's all-artifact-forgery exclusion does not explicitly settle a concurrent single-path replacement between stat and open. | Confirm the candidate's concurrent-writer threat boundary, or return the lower-level non-blocking design and its additional precise sealed-observer boundary. No inferred threat-model expansion. |
| D7-03 | Prevention covers future qualified producer writes; it cannot authenticate a legacy torn canonical destination as a crash rather than substitution. | Explicitly establish that this is a prospective crash-safe producer boundary, or specify the bounded authenticated recovery/migration mechanism. Do not accept a stranded valid study as a residual or infer recoverability from a prefix/hash-name alone. |
| D7-04 | Q6 authorized L1, while staged publication also needs L2a/L2b and the exact F3 observer changes in section 5. | Approve their precise eventual frozen-scope inclusion and independent edit ownership. Do not silently edit them now. |

The proposed exact candidate is **four implementation files and four test
files**. These dependencies and returned legacy cases prevent presenting it as
a frozen, fully qualified scope. Disposition 04 and this revision are the only
new planning records; `v2_gate8_scope_03.json`, any Seal-07 source/tests, new
scientific records and real-study actions remain unauthorized.
