# E9 v2 Gate-8 scope 03 (Seal 07)

Recorded 2026-10-07. Frozen scope for review; implementation is not authorized.

- Scope identity: `v6-e9-v2-gate8-scope-0233e8825a6a`
- Body SHA-256: `0233e8825a6abbef1b76f8eaf4144146f370277fb827fdcd3ccec69077a12f6f`
- Raw SHA-256: `75343cf20cde42796a8ad10405cd475360e6c4e90ef8915add59243114143f98`
- JSON: `tools/research/v6/e9/v2_gate8_scope_03.json`
- Planning: `docs/research/v6/V6_E9_SEAL07_PLAN_03.md`
- Exact ruling bytes: `tools/research/v6/e9/v2_seal07_planning_rulings_01.txt`

The scope freezes four implementation files and four qualification files for
review. No implementation, test editing or operational action is authorized.
Revision 02 remains the accepted working basis; immutable Revision 03 incorporates
the final four user rulings. JSON governs if a readable mirror differs.

## Exact eight-file boundary and F1/F2 necessity

| File | Necessity and limit |
| --- | --- |
| `tools/research/v6/e9/v2/records.py` | Shared regular-read/readback boundary and minimal crash-safe no-overwrite publication helper for W outputs. Own W-reachable reads: catalogue line 48, _field lines 219/274, read_record line 416. Only mapped reads, typed unavailable/read helper and bounded record-publication behavior required by recovery. No general serialization, wire-format or unrelated writer redesign. Preserve write_once signature and unrelated callers; new publication helper used only by W producer-local routines. |
| `tools/research/v6/e9/v2/authority.py` | Protected W entry/recheck and consumers traverse pinned_source_checker, _state, resolve, retention comparisons, read_artifact, registered_producers and durable_bytes readback (S7-R01..R08). Guard mapped reads only; preserve general writers, events, actor/binding decisions and precedence. No automatic stale-lock deletion. |
| `tools/research/v6/e9/v2/inventory.py` | produce_private_verification -> protected(private_verification) -> authority._check (604-645) -> A/R limitations -> inventory.frozen_limitations contract read line 67, before action and at recheck; S7-R12. Only line-67 contract read via shared safe reader. No revealed_lists, inventory, history, membership or coverage computation change. |
| `tools/research/v6/e9/v2/private_verification.py` | F1 mapped operational W producer/consumer reads. F2 complete output/attempt recovery: _verify 332-381 (result retention 361-364), producer 384-428 (W retention, W.json, PASS 406-408). Only mapped reads, deterministic staging/provenance, producer-local retention/publication, complete exact derivation and same-state recovery/classification. Separate full derivation/validation from output publication so infrastructure write faults are interrupted rather than scientific failures. Preserve signatures, complete verifier, scientific inputs and wire shapes; no unrelated Gate-8 cleanup. |
| `engine/tests/test_v6_e9_v2_gate8_seal07.py` |  Expanded S7-R01..R18 and S7-C01..C16 matrix; fixtures in this module. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py` |  Independently authored expanded matrix from governing requirements; fixtures in this module. |
| `engine/tests/test_v6_e9_v2_gate8_seal06.py` |  Only enumerated existing_test_exceptions and write_spy support exception. |
| `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py` |  Only enumerated existing_test_exceptions and Writes/PASS_WRITES support exceptions; implementer must not edit. |

Every other manifested implementation/test file is excluded. Commitment,
generation, integrity, the complete verifier, test helper, conftest, configuration,
guard, harness, reproduction script, schemas, protocol, inputs and prior records
remain unchanged. No new helper module or unbounded platform dependency.

Records supplies minimal common record I/O/readback/publication. Its shared safe
reader and own mapped W-path reads remain part of the accepted Revision 02 design;
the new bounded publication helper is used only by producer-local W outputs.
Authority generic writers retain semantics with mapped safe readback participation.
Private_verification owns deterministic staging, attempt provenance, pure output
derivation, producer-local retention and exact recovery. This supersedes Revision
02's producer-local-only location of the physical publication helper, not unrelated
general write_once semantics. Inventory is required by the exact F1 _check/A/R
contract-read path at line 67; it is not a general inventory-hardening change.

## Four remaining rulings

### D7-01

Resolved by ruling 1 for scope; storage qualification pending

Complete canonical bytes before publication; distinct same-filesystem staging; file flush/fsync and safe readback; atomic no-overwrite installation. Never overwrite a canonical destination. Flush meaningful directory metadata where supported using bounded stdlib/project facilities, including newly created parent entries; record limitations where unavailable.

Same-filesystem atomic hard-link installation with collision refusal/exact comparison, retaining candidates. No overwrite-capable rename/os.replace, direct-write fallback or unbounded dependency; unsupported roots refuse.

After restart each canonical destination is absent or a complete canonical record within the publication model. Bytefray intentionally exposes no half-record. Applies to intent, verification result, retained W, W.json, PASS and non-PASS outcomes.

No arbitrary hardware/controller/filesystem/OS corruption immunity. Kill tests do not prove physical power-loss durability. Record Windows/other roots lacking meaningful directory-flush primitives.

### D7-02

Resolved by ruling 2

Assume no hostile concurrent replacement. Stat-reject non-regular targets before potentially blocking open; Path.open plus fstat regular-file and meaningful identity checks against prechecked/retained object where available. Close on refusal, validate complete bytes/length/digests after reading, fail closed on consumed-object mismatch. No type cache; preserve symlinks to regular targets.

Pre-check plus Path.open does not prevent malicious TOCTOU replacement. Arbitrary hostile concurrent filesystem writes are outside this evidence model. Detect ordinary races where practical.

### D7-03

Resolved by ruling 3

Recover only known qualified interrupted transitions after exact proofs. Retain torn staging unchanged; derive exact outputs into fresh candidates. Legacy torn/malformed canonical destinations without Seal-07 provenance are non-operational and untouched pending separate disposition. No migration, deletion, overwrite or automatic repair.

Controlled artifacts may model exact newly authorized crash points with known provenance. Prefix/hash filename is insufficient. Torn canonical paths violate absent-or-complete model and must not be silently repaired.

### D7-04

Resolved by ruling 4

Enumerated direct conflicts only; retain Seal-06 manifested bytes/evidence and edit ownership. New modules carry expanded matrix. Preserve neighboring, negative-read and lock behavior. Final sweep found no additional conflicts.


## F2 exact recovery and manual stale lock

known newly qualified interrupted transition; same instrument and scientific inputs, S/G/boundary/payload/salt/audit/K and originating bindings; same registered independent verifier; no authority event since producing tip/log, including HOLD, redundant or tuple-extending ISSUE; no contradictory terminal outcome or existing PASS; rerun complete verification; independently rederive canonical result and W; exact byte comparison with every published result, retained W and W.json before missing publication

Only missing continuation/PASS for same scientific state on a new recorded attempt; never rewrite complete W or inputs; retain all old attempts/candidates and exact single-PASS A4 rule.

Exact recovery unavailable; non-terminal refusal alone; study blocked pending separate disposition. Never invent scientific failure solely from the event.

Non-operational, untouched, separate disposition; no migration/repair.

Refuse before calling verifier.

No automatic stale-lock deletion or standing clearance authority. Separate incident authorization requires proven holder death, no legitimate concurrent root user, safely preserved/hash-verified lock bytes and metadata, stale rationale, operator/lead identity and exact clearance action. Non-regular/unreadable lock needs separately specified safe evidence handling. No scientific substitution or generation, and no appended event disguised as an unchanged originating tip. Synthetic clearance models prerequisite only.

The exact 18-row durable-read map (S7-R01..R18) and 15-row crash matrix
(B0..B13 and E1/E2; S7-C01..C16) are retained from Revision 02 in the scope.
Their pending D7 dependencies are resolved for scope by the latest rulings above;
implementation/platform qualification is still required. All new readers use the
same regular-file boundary. Source/resolver callbacks require audited construction;
arbitrary callbacks receive no blanket certification. No direct-write fallback.

## Exact existing sealed-test exceptions

All node IDs are repository-root pytest IDs. The JSON binds exact Seal-06 raw
module and affected block hashes. The implementer edits only its own exceptions;
a new independent test-author context alone edits the independent exceptions
after separate implementation authorization. No author commissioned now.

- **I1**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_w_retention_w_json_and_pass_are_written_under_the_verifying_lease` (Seal-06 lines 283-293). Update write-observer seam/list for local retention, staging and atomic installation; preserve intent-before-lease, result/W/PASS-under-lease, exact tip and one PASS. Basis: Rulings 1 and 4 supersede the complete direct-write observation list.

- **I2**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_an_authority_append_cannot_interleave_before_pass` (Seal-06 lines 296-316). Observe/interleave at corresponding publication seam; preserve busy refusal, unchanged log/tip and subsequent separately appended HOLD. Basis: Rulings 1 and 4 change only observer/fault seam, preserving lease safety.

- **I3**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_a_write_failure_leaves_no_outcome_and_is_listed_as_interrupted` (Seal-06 lines 319-336). Move retention fault injection to producer-local retention/publication; preserve propagated error, no outcome, exception-unwind lock release and retry PASS listing attempt 1 interrupted. Basis: Rulings 1 and 4: AuthorityLog.retain_record hook no longer observes local retention.

- **L2a**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_a_partial_w_file_leaves_no_outcome_and_fails_closed` (Seal-06 lines 339-356). Tear the known staged W write, preserve candidate unchanged, rerun complete verification and derive identical W for recovery to one PASS. Keep separate refusal assertion for unproven partial canonical W. Basis: Rulings 1, 3 and 4 distinguish recoverable staged interruption from unexplained canonical damage.

- **I5-UNAVAILABLE**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_non_pass_outcomes_are_written_after_the_lease[UNAVAILABLE]` (Seal-06 lines 375-390). Adapt observer/direct-write list only for staging/publication; preserve corresponding outcome, no W, and non-PASS publication after lease release. Basis: Rulings 1 and 4 change physical-write observation only.

- **I5-REFUSED_PRECONDITION**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_non_pass_outcomes_are_written_after_the_lease[REFUSED_PRECONDITION]` (Seal-06 lines 375-390). Adapt observer/direct-write list only for staging/publication; preserve corresponding outcome, no W, and non-PASS publication after lease release. Basis: Rulings 1 and 4 change physical-write observation only.

- **I5-FAILED_VERIFICATION**: `engine/tests/test_v6_e9_v2_gate8_seal06.py::test_s6_f3_non_pass_outcomes_are_written_after_the_lease[FAILED_VERIFICATION]` (Seal-06 lines 375-390). Adapt observer/direct-write list only for staging/publication; preserve corresponding outcome, no W, and non-PASS publication after lease release. Basis: Rulings 1 and 4 change physical-write observation only.

- **J1**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_01_W_retention_W_json_and_PASS_are_written_under_the_lease_at_its_tip` (Seal-06 lines 614-635). Observe local retention, staging and installation; preserve logical order and lock/tip checks. PASS, including its publication metadata flush, stays final successful durable transition under lease. Basis: Rulings 1 and 4: opens/replace alone no longer observe atomic installation.

- **J2**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_02_an_append_attempted_before_the_PASS_write_is_refused_as_busy` (Seal-06 lines 638-669). Move logical retention/W.json/PASS interleave hooks to new publication seams; preserve every busy result, exact log/tip and outcome checks. Basis: Rulings 1 and 4 change observer only.

- **J3a**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[W-retention-integrity_error]` (Seal-06 lines 679-714). Move only retention fault injection; preserve exception identity, no outcome and interrupted retry PASS. Preserve earlier attempt in interrupted ledger. Basis: Rulings 1 and 4; L1 additionally F2 exact recovery, L2b additionally ruling 3. Only L1/L2b change operational assertions; other variants change injection seam only.

- **J3b**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[W.json-os_error]` (Seal-06 lines 679-714). Move only W.json OSError injection; preserve exception identity, no outcome and interrupted retry PASS. Preserve earlier attempt in interrupted ledger. Basis: Rulings 1 and 4; L1 additionally F2 exact recovery, L2b additionally ruling 3. Only L1/L2b change operational assertions; other variants change injection seam only.

- **L2b**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[W.json-partial_then_stop]` (Seal-06 lines 679-714). Tear known staged W candidate and preserve it; supersede only this branch permanent refusal with full exact reverified recovery to one PASS. Keep separate unproven partial-canonical refusal. Preserve earlier attempt in interrupted ledger. Basis: Rulings 1 and 4; L1 additionally F2 exact recovery, L2b additionally ruling 3. Only L1/L2b change operational assertions; other variants change injection seam only.

- **L1**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome[outcome-1-stop]` (Seal-06 lines 679-714). Interrupt before PASS publication after complete W; supersede only this branch never-PASS assertion with full re-verification, exact retained-W equality and one PASS. Never rewrite complete W. Preserve earlier attempt in interrupted ledger. Basis: Rulings 1 and 4; L1 additionally F2 exact recovery, L2b additionally ruling 3. Only L1/L2b change operational assertions; other variants change injection seam only.

- **J4**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_04_a_post_action_recheck_failure_after_PASS_propagates_with_one_outcome` (Seal-06 lines 717-731). Move drift hook to successful PASS publication; preserve post-action recheck error and one already-durable PASS with no second outcome. Basis: Rulings 1 and 4 change fault seam only.

- **J5-salt_missing-UNAVAILABLE**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_05_non_pass_outcomes_are_written_after_the_lease_is_released[salt_missing-UNAVAILABLE]` (Seal-06 lines 737-754). Adapt staging/publication observation only; preserve corresponding outcome, no W, intent before lease and outcome after lease release. Basis: Rulings 1 and 4 change observer only.

- **J5-held-REFUSED_PRECONDITION**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_05_non_pass_outcomes_are_written_after_the_lease_is_released[held-REFUSED_PRECONDITION]` (Seal-06 lines 737-754). Adapt staging/publication observation only; preserve corresponding outcome, no W, intent before lease and outcome after lease release. Basis: Rulings 1 and 4 change observer only.

- **J5-tail_consume-FAILED_VERIFICATION**: `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::test_s6_f3_05_non_pass_outcomes_are_written_after_the_lease_is_released[tail_consume-FAILED_VERIFICATION]` (Seal-06 lines 737-754). Adapt staging/publication observation only; preserve corresponding outcome, no W, intent before lease and outcome after lease release. Basis: Rulings 1 and 4 change observer only.

Support exceptions only:

- `engine/tests/test_v6_e9_v2_gate8_seal06.py::write_spy` (Seal-06 lines 263-280): Observe local producer retention, candidate writes/flush/readback, atomic no-overwrite installation and metadata flush. Preserve logical phase hooks, lock/tip checks and negative-read observers; changes apply only to enumerated F3 cases, without weakening neighboring tests.

- `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::Writes` (Seal-06 lines 251-334): Observe local producer retention, candidate writes/flush/readback, atomic no-overwrite installation and metadata flush. Preserve logical phase hooks, lock/tip checks and negative-read observers; changes apply only to enumerated F3 cases, without weakening neighboring tests.

- `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py::PASS_WRITES` (Seal-06 lines 611-611): Observe local producer retention, candidate writes/flush/readback, atomic no-overwrite installation and metadata flush. Preserve logical phase hooks, lock/tip checks and negative-read observers; changes apply only to enumerated F3 cases, without weakening neighboring tests.

There are 17 parameterized cases across ten functions and three named support
objects. Only L1/L2a/L2b supersede operational assertions; other changes move
observer/fault seams and preserve outcomes. Keep names/parameter cases identifiable.
Shared f3_03 assertion changes apply only to L1/L2b; neighboring variants remain
unchanged. Before future edits retain full original modules/source copies under
the established Seal-06 evidence procedure and record editor provenance, exact
line diffs and whole-module/block before/after hashes. No sealed test edited now.

## Final targeted sweep and future qualification

Read-only rg text search plus AST/function/assertion review covered all 25
Seal-06 manifested v2 test modules, the six requested categories and 146 matched
functions/classes/helpers. The scope retains patterns, module hashes, category
line matches and object/block hashes. Result: **no additional direct conflicts
beyond Revision 02**. No sealed test directly modeling a torn PASS candidate,
torn verification-result candidate or torn retained-W candidate was found; new
Seal-07 modules must supply those matrices. This is not qualification evidence.

Unproven partial-canonical W cases, issued-W missing/mismatched PASS, result
corruption/absence consumer refusal, stale-lock refusal, negative-read spies and
the implementer post-PASS recheck remain unchanged. Its existing PASS-exists
source-check hook already observes the complete publication transition.

Future qualification covers S7-R01..R18 and S7-C01..C16: unsupported object types,
stat/open/fstat/identity races and closure, candidate writes/flush/readback,
atomic installation/collisions, directory flush where supported and unsupported
backend refusal; death before/during/after transitions and repeated recovery
death; same instrument and exact scientific material, full verifier invocation,
retained-W/result equality, no W rewrite, one PASS, intervening events including
HOLD/ISSUE, contradictory/terminal outcomes, and no entropy/generation/salt/native
execution/operational publication. Exception unwind is not process-death proof.
Native POSIX FIFO/device tests use bounded subprocesses on a suitable host;
Windows mode injection is not native POSIX or physical power-loss proof.

Future independent authors work from frozen governing requirements, without
implementer control-flow/scenario briefings; retain private transcript provenance,
recording identities/hashes publicly. A later distinct independent qualifier
reproduces exact new manifests/instrument and does not improve sealed state.
Implementer or independent author cannot qualify their own work. Use focused
guarded tests, then required broader guarded qualification, ruff and separate
engine/client mypy. The prior 877/877 result does not qualify Seal 07.

Before and after planning writes, all bound inputs and all 325 Seal-06 manifested
files are rehashed. Actual after-write results are retained in the separate
write-once v2_seal07_scope_verification_01.json. The accepted provenance backup
remains untouched; no new authenticity claim is made.

Status: Seal 06 PASS WITH FINDINGS; S6-IQ-F1 Seal-07 required; S6-IQ-F2 Seal-07
operational blocker; F3-F5 record only; Gate-8 operational acceptance NOT
ESTABLISHED; execution LOCKED; Requirement C / historical coverage NOT ESTABLISHED;
Q absent. Seal-07 implementation, operational W, REAL entropy, generation, salt,
publication, Gate 7 and operational records remain NOT AUTHORIZED. No tests,
scientific producers, native matches, commits, pushes or publication run here.

## Bound inputs

All 32 inputs verified before and after planning writes. Earlier digests
were checked against prior recorded values where available; accepted Revision 02
and exact latest ruling bytes are newly byte-bound by this scope.

| Repository path | Raw SHA-256 |
| --- | --- |
| `docs/research/v6/V6_E9_AMENDED_IMPLEMENTATION_QUALIFICATION_PLAN_02.md` | `003f5e7b3970e10458cc35cab243bbe0097ac28cd5762100baba4d3cad66ac7e` |
| `docs/research/v6/V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md` | `034758d520e8c9a597daacc06501ddd3de31824b4a102a5411c54879ee3ccbfe` |
| `docs/research/v6/V6_E9_GATE8_REVISION_PLAN_01.md` | `7cd50298f993e81b0d1cfe3056f73ab23eb4d28fa8715833dd1911fc3d7bb9f1` |
| `docs/research/v6/V6_E9_SEAL07_PLAN_01.md` | `b0ae22ce15f1e5caa15a167b2f13cb0972eef62f2e0c6bee04ddf92c51821955` |
| `docs/research/v6/V6_E9_SEAL07_PLAN_02.md` | `6c71f7cb4de6f6b274e283ee961b8c42179eebc3fb052aae2762f5d6b9d24f1d` |
| `docs/research/v6/V6_E9_SEAL07_PLAN_03.md` | `49511e2602dc65195ad13bfcda54277702c9ea6773dff3048ee98ec819da73ec` |
| `tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json` | `434635bdfa568050c3486c3ce936ae78ca67aef7a1112fb99a2a8a9c5144feff` |
| `tools/research/v6/e9/amended_rule_contract_v2_proposed_02.json` | `1c421891e54b9522a6b172ef2d4a5b61e484217b2789115ab954916618b5cc4a` |
| `tools/research/v6/e9/e9-v2-seal06-independent-reproduction-20261007-01.json` | `d4b240c997f67a978c007590eeceb3f6e32948bd7f90fef67c8832ac8310ae98` |
| `tools/research/v6/e9/protocol_adoption_attestation_v2_02.json` | `3dc816fa66311a58c92e041ab5acc1b3ce0ec143ceb96ee348bc10b7df92628a` |
| `tools/research/v6/e9/protocol_freeze_v2_adopted_02.json` | `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4` |
| `tools/research/v6/e9/v2_final_manifest_seal_05.json` | `7ecb1195803885e4c1ce06ac076e6d6e1073ad75c77761261193b9ca570f040c` |
| `tools/research/v6/e9/v2_final_manifest_seal_06.json` | `384f1f1e3f70e9a9392143373459e22d2ffd2741b07c693b00a7f60268ab2825` |
| `tools/research/v6/e9/v2_finding_disposition_01.json` | `4e7aa274f74fb3309a5b11e6448a22565c071eeec829483b3812bbc22b957669` |
| `tools/research/v6/e9/v2_finding_disposition_01_lead_confirmation.json` | `69c1460c96b43c35a6b17b4f3add37d64e88c68b4124555dfc1d6a8468767698` |
| `tools/research/v6/e9/v2_finding_disposition_02.json` | `793dd33bb8600bfd232cd3c2b7ac45900fa42c91657fd0d847ba564db45ba59a` |
| `tools/research/v6/e9/v2_finding_disposition_02_lead_confirmation.json` | `f3e17a1929d982a1dbeda781113b5ce792571323bd7eaa350bbb0baeefa7729c` |
| `tools/research/v6/e9/v2_finding_disposition_03.json` | `3c7a21474282c5a9da98871b4736b0d901a2de330dcef1301cd83d5fb8c67171` |
| `tools/research/v6/e9/v2_finding_disposition_04.json` | `d3db6c9bac4271384b933da01fa253a0c64d3249c93efa65a819d43f5ccf0839` |
| `tools/research/v6/e9/v2_gate8_scope_01.json` | `adf4d9c77fcbc377ff14aa46fd354f3a26e41ba779398728634943b65d045cb2` |
| `tools/research/v6/e9/v2_gate8_scope_01_lead_confirmation.json` | `37cfda5e8830541f75dcbc8b70bc5b7a0756ef9e91de61e54a258a4963a84cf6` |
| `tools/research/v6/e9/v2_gate8_scope_02.json` | `75c1b3638d998506dcd78b4a348ac12f866c21364440542b683bad52539046b4` |
| `tools/research/v6/e9/v2_gate8_scope_02_lead_confirmation.json` | `94e3b75af855e2ef5bbdbdc20ea36bb351948d0ebded01e2082c33e779d5d7d6` |
| `tools/research/v6/e9/v2_implementation_manifest_final_05.json` | `40e55187ae5e6e71c1a4533af7a19567e975ec509195dd9bc90f154ad814e34b` |
| `tools/research/v6/e9/v2_implementation_manifest_final_06.json` | `acd3b05c62df94bb93288d214473977924aa0fe19f90830411c04609f1bfefc5` |
| `tools/research/v6/e9/v2_qualification_manifest_final_05.json` | `039a87a4177c00e07b5e70e1d8f5eb9b4005b276601079593059aaf541a39b7f` |
| `tools/research/v6/e9/v2_qualification_manifest_final_06.json` | `97acea54246a3df871aa07eb28648f9f62bbbf04d050d6d321a83bad195948f4` |
| `tools/research/v6/e9/v2_seal07_planning_rulings_01.txt` | `5923fffa9ad1a63c987d5652e56fa2caccfedd52a03bed3a23bbe6661a62441d` |
| `tools/research/v6/e9/v2_synthetic_qualification_evidence_05.json` | `0d8b5acefaefd2d95e81dbe08d7129a51bb54880f3ae12741f42841f40cefa8c` |
| `tools/research/v6/e9/v2_synthetic_qualification_evidence_06.json` | `a1685e502584ad668bfb3f59856faa9df2f42cf04a30da369e16ccb44e1849ca` |
| `tools/research/v6/e9/v2_tooling_attempt_history_02.json` | `280764c62432160671fc16d199b48008b5347e81db311adefe423fe4ac70d2f4` |
| `tools/research/v6/e9/v2_tooling_attempt_history_03.json` | `b6d39352d6bc4b143cd93452e6235fa73835a80ac8042892ea04f3c56f0f8609` |
