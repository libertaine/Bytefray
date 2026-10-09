# E9 Gate-7 completion and marker-transition disposition (07)

Recorded 2026-10-09T09:41:21.291392-04:00 (America/Indianapolis), following the supplied lead disposition. Study `v6-e9-study-01`; operation `v6-e9-generation-01`. **Gate 7: ESTABLISHED. G: ISSUED / UNUSED. Execution: LOCKED. Requirement C: NOT ESTABLISHED.**

The write-once machine record is [Disposition 07](../../../tools/research/v6/e9/v2_finding_disposition_07.json), raw SHA-256 `086d5c13ae31b4bb59a5301d0ba99a25cbbf7cfcbff09ff6f23241ba0a949d09`. It retains the exact supplied ruling (6551 UTF-8 bytes, raw SHA-256 `ea9a1dcd4479581afe6a0c935a2d82980b018f98147d3fb140eb4f18bb08531e`), the verification result, complete read-only procedure and attempt history. This is a documentary disposition; it appends no authority event and issues no operational action permission.

The [prior G return](V6_E9_GATE7_G_RETURN_01.md) remains byte-identical: 20020 bytes, raw SHA-256 `8a3777a2619ac61eee70f45429a718c44209fc0986184951b1ed89257cad6c88`. Its real marker difference, assertion and stop remain historical evidence. No B, G, ISSUE or prior disposition was rewritten.

## A. B marker

Exact historical authority tip **T0**: `f0da08f5ce538d3a56ddab2c06495a19bccab0f37f8df6e63b6b3897fcbbc986`.

B is `v6-e9-pre-generation-verification-v2-434684981dbc`, full body SHA-256 `434684981dbc014e096f97b1b1d4e6f29eeb3303e13b743fe50a8d23b966754c`, raw SHA-256 `411c227e4808ac566ad60af52828f4925fdc14c4d7ac5381d5e23720435c96aa`. Its `active_authority_tip`, unchanged B input manifest and unchanged B01-AUTHORITY-STATE all bind T0. Canonical/schema/body/raw/dependency readback passed.

B01-AUTHORITY-STATE remains 3194 bytes with raw SHA-256 `3e48dffaafba62cd8d85a42f6c60973f8755d0f1a519bd58ab839ff9c82f4c81`. Its original embedded marker is exactly sequence 1 / T0. Canonical encoding plus LF reproduces the original 88-byte marker, SHA-256 `3dc1e2cfd498963dac8fd7aea7275d777d88982a81e53c9124bb0a207d711537`, exactly matching B01-ACTIVE-MARKER. No historical marker file was created or substituted.

## B. G

Existing [G](../../../tools/research/v6/e9/v2_generation_authorization_study_01.json): `v6-e9-generation-authorization-v2-0ea6d2043fbd`; full body SHA-256 `0ea6d2043fbd7619ea724da15b6a4e106ffeaa3c929b43b9bcb3ff354c668175`; raw SHA-256 `21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8`; 5376 bytes. It remains byte-identical.

G binds exactly P/I/Q/O/V/A/R/B, with full schema/version/identity/body/raw RecordRefs. It binds B above and T0 through `active_authority_tip`, the correct study and unique operation, N=1412, exact B01-MANIFEST, sampling and declared later boundary procedure. Instrument, Q, O/V, A/R and authority identities resolve to the exact original bytes. T remains the original explicit NOT_APPLICABLE determination through O.

B01-MANIFEST remains 65125 bytes, raw SHA-256 `025bbfe6887615564f837d64a04ef730ca970df5302172f39589cca2774552df`. The research-lead Actor is `v6-e9-research-lead-01`, role `research_lead`, with original declaration raw SHA-256 `769e77844905be3fbda7b66fcde57482fedca30e008191fb8f6ca7e15541e700`. All dependencies are freshly reverified below.

| Role | Identity | Full body digest | Full raw SHA-256 |
| --- | --- | --- | --- |
| P | `v6-e9-prereg-v2-539a60806eab` | `539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0` | `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4` |
| I | `v6-e9-instrument-v2-3c692f23d2d9` | `3c692f23d2d9a7467e07b36ea97a382c1497511033767b078dc8de057033d8e0` | `cbdc00bd767179b4353625f4fb10115ec9c45fdcbb01a8c19ced3c3fb2b48fd7` |
| Q | `v6-e9-instrument-qualification-v2-488ef8dc9d0b` | `488ef8dc9d0bcf93a3b930857b88aed0f205b226cda0d45bc75514c9115011c1` | `df9d3a286350404a22aa8c17d52b877bd3e93a80c246fb1d4cc16a7bb9eaa616` |
| O | `v6-e9-inventory-seal-v2-6344fc060ac3` | `6344fc060ac3d93619017960dc582ee55a06c743e9f64b72a571865c0992c50d` | `59f70171a3a5d9202603a6c191bd419513274fb3fde8857a6d5ef77235f64bf2` |
| V | `v6-e9-inventory-verification-v2-f32e22658e77` | `f32e22658e770bd1ff1374d8c283706a9f3efa6e2f00dd988d6c094bdb5ef04f` | `81de4da3c5a0fa6d0bcba27de7ec9233a6fe1a02cc61dad3d13cb0fb8e4d9b2c` |
| A | `v6-e9-inventory-approval-v2-156cc77b127d` | `156cc77b127dc488f8aa64bf44ce3bb55c4c0061dceab3dac988a0a50bd0c5aa` | `b709a9fd8065f573b7406ee3125d727028b323e9b74397f4a25d103e105bcb7b` |
| R | `v6-e9-operational-risk-acceptance-v2-a15e275304b0` | `a15e275304b0f5558045bf148aa0b64600feb63bf910f0e011a8d30994cfd88e` | `27c0376bb79e1cdbd91b6ac9d23c43a3b6aa14d7afc050caabe53e5720238dbd` |
| B | `v6-e9-pre-generation-verification-v2-434684981dbc` | `434684981dbc014e096f97b1b1d4e6f29eeb3303e13b743fe50a8d23b966754c` | `411c227e4808ac566ad60af52828f4925fdc14c4d7ac5381d5e23720435c96aa` |
| G | `v6-e9-generation-authorization-v2-0ea6d2043fbd` | `0ea6d2043fbd7619ea724da15b6a4e106ffeaa3c929b43b9bcb3ff354c668175` | `21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8` |

## C. ISSUE

Existing sequence-2 event, ROOT-relative `authority/event-00000002.json`: `v6-e9-authority-event-v2-50fe7d74d8a9`; raw SHA-256 `a2bc466c59843729915bd006431caa149818943b764563c5eaf6a246e4727020`; 6503 bytes. ISSUE binds the exact G in its full P/I/Q/O/V/A/R/B/G tuple and `affected_authorizations=[G]`, with the same study, operation and lead Actor.

Its `prior_tip` is exactly **T0**, `f0da08f5ce538d3a56ddab2c06495a19bccab0f37f8df6e63b6b3897fcbbc986`. Its deterministic resulting tip **T1** is `50fe7d74d8a97be1ef5f08f01d93469193c48afffff306e4e351e827cf7616d0`: SHA-256 of the canonical ISSUE body without LF, also the event full body digest. Identity is the frozen prefix plus the first 12 digest characters. No self-referential resulting-tip field is invented.

The issuer was valid at T0: the original declaration grants this Actor `research_lead`; unchanged B01-AUTHORITY-STATE retains the same role map; sealed `EVENT_ROLES[ISSUE]` requires that role; all actor evidence bytes resolve. Sequence 1 was unheld, unterminated, unrevoked and unconsumed. ISSUE preserves every already-active P/I/Q/O/V/A/R binding and adds the already-written exact B/G. The frozen ISSUE rule permits this extension and checks every record and earlier dependency. Exact G01-LEAD-RULING (8406 bytes, raw SHA-256 `f8f2199a163d9cb68fb48fb9bc00a0ede1a8e45cb76bf4b389a39cc3f74047ec`) is shared by G and ISSUE and retained unchanged.

## D. Current authority

Current `authority/active.json` is exactly canonical `{"sequence":2,"tip":"50fe7d74d8a97be1ef5f08f01d93469193c48afffff306e4e351e827cf7616d0"}` plus LF: 88 bytes, raw SHA-256 `c7490f70dd6354537c7a60d51195582d9494f3eceaaee353dc9929e45b77569d`. Its tip is T1, and the sealed complete-chain reader independently reproduces that exact marker. Epoch 0; held false; terminal false; revoked empty; consumed empty.

## E. Chain

The entire chain contains exactly two canonical events: sequence 1 `v6-e9-authority-event-v2-f0da08f5ce53` (prior `genesis`, resulting T0), then sequence 2 `v6-e9-authority-event-v2-50fe7d74d8a9` (prior T0, resulting T1). Sequence 1 remains raw SHA-256 `907d4d5d3ea551c0e42a1b58c7f950e46b987bc6c9f689882d5e3bc6379087a4`. Event file numbering, body sequences, exact studies, tuples, Actor roles, all evidence and hashes verify. There is no intervening event and no later event.

**B / T0 → exact existing G → exact existing G ISSUE → T1 current authority tip.** No pending marker, exclusive lock, HOLD, REVOKE, TERMINATE, CORRECT or CONSUME exists.

## F. Interpretation and lead disposition

**G7-MARKER-F1: RESOLVED — incorrect post-ISSUE equality expectation.** The prior check observed a real byte difference. That difference is the authorized T0 → T1 authority transition. Direct historical B-marker/current-marker equality is not the correct post-ISSUE invariant. The correct transition invariant was independently reverified against the unchanged evidence and frozen readers in this continuation.

B remains valid as certification of the complete pre-G state at T0. The later authorized ISSUE does not retrospectively invalidate B. B need not be regenerated because a later event advances the authority log; it must not be rewritten to appear to certify T1. The historical T0 binding is part of its evidentiary value.

This reading agrees with the [adopted rule-contract text](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md), section 5 R8/R9 and the dependency/identity-consequence/active-chain paragraphs, the [frozen B/G catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json), and the unchanged [authority implementation](../../../tools/research/v6/e9/v2/authority.py). B certifies the pre-generation inputs and precedes G. The catalogue requires a SHA-256 authority tip in B/G; it imposes no equality between B’s stored predecessor and a later current marker. `_append` records `prior_tip`, then advances the derived marker to the new event digest; `_state` verifies that transition; `_check` validates the current active tuple without equating historical B/G tips to current tip. No frozen rule requiring the contrary invariant was found.

R8’s input/identity/qualification/operational-change invalidation guards the certified pre-G inputs and authority binding. Here those bytes and bindings are unchanged; the authorized next ISSUE extends the chain. Treating its prescribed derived-marker update as requiring a replacement B would discard the predecessor evidence and make the required B → G → ISSUE order circular.

Verification was fresh read-only computation in the current root AI context, independent of the prior checker’s equality assumption. No separate agent, human principal or model-family independence is claimed. A scratch caller initially compared G’s newly retained ruling to the older pre-G preparation request. It stopped without changing evidence; the corrected caller bound the raw artifact to actual G01-LEAD-RULING and shared ISSUE evidence, and passed. The final procedure additionally checked original role assignment and repository operational-record absence. All attempts are disclosed in the machine record.

## G. G-unused proof

No CONSUME exists for G or any authorization; both chain events are ISSUE. The frozen producer reader returns empty. No producer-roots or first-raw directory exists, and no first-raw marker exists. Exact private-file accounting permits only the already-authorized G additions and existing marker transition; no unaccounted scientific output exists. The top-level E9 record store contains no GenerationBoundary/S/W/U/C/D/F record for this study.

**No producer registration, G consumption, first-raw marker, REAL entropy, generation output, operational W, salt, native execution or publication exists/occurred in this retained study scope or was performed by this task.** The approved study root is fully accounted for; no global external-host-history claim is made. The read-only `_check("raw_draw", T1, operation, unconsumed=True)` passed without exercising its operation. No Generator, producer, protected lease, consume, source-draw, native-match or publication API was invoked.

## H. Integrity

| Check | Fresh result |
| --- | --- |
| Seal 08 | **329/329 unchanged**: 293 implementation + 36 qualification files; manifest raw SHA-256 `38c16e330ea1ae1efa2a3a048669961b11fe3cc0f478a7101e0472d30665dfe8` |
| Static preservation set | **1607/1607 unchanged** against the exact original static map in ARB01-ENTRY-BASELINE, 197257 bytes, raw SHA-256 `01e9f4c4dcea3a74e64432bcbbc32319a830fa656b0a16a0813e9d8d2e565b5f` |
| Q/O/V/A/R/B/G and both ISSUE events | Canonical full body/raw digests, identities, dependencies and actual bytes unchanged |
| B live-path rows | **4391/4392** live matches; sole difference is historical authority_marker; its original **88/88 bytes** reproduce from unchanged B state |
| Bound ArtifactRefs | **2416 occurrences**, **1870 distinct evidence-ID/content bindings**, freshly resolved/hashed |
| Private files | **1345/1345 accounted for**; 1340 pre-G immutable files unchanged, one prescribed derived marker transition, four already-authorized G authority additions; zero unexpected files |
| This task’s private/authority mutations | **Zero**; complete private file map identical before/after audit |
| Source/test/seal changes | **None**; tracked working tree and index empty |
| Branch / HEAD / upstream / live remote | `v6-research` / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b`; upstream and live `origin/v6-research` match |

The four existing G authority additions remain the B/G exact copies under `authority/evidence-records`, G01-LEAD-RULING under `authority/evidence-raw`, and sequence-2 ISSUE. They were created in the prior issuance, not this task. No preservation exception or new authority state was introduced. The fixed B manifest remains unchanged; this disposition does not misreport all 4392 live rows as matching.

Original K/E/L, all 357 gap identities/dispositions and DEP-01–DEP-05 remain unchanged. K=163 closes no historical gap. Complete historical coverage and exhaustive historical non-reuse remain NOT ESTABLISHED; the retained assurance is known-history non-reuse only, with H UNKNOWN and only worst-case bound 1.

Only this new Markdown mirror and its sequence-7 JSON disposition are added. Existing untracked work and local-only settings are preserved. No commit, push, source/test/seal repair, replacement G or replacement ISSUE occurred. Interpreter/live-remote reads used approved execution after restricted launcher/network failures; no auto-review rejection occurred. No new full pytest, lint, mypy, native suite or qualification run is performed or claimed; this documentary continuation used frozen schema/source/adoption/hash/chain checks.

## I. Gate status

| State | Status |
| --- | --- |
| Gate 8 | **ESTABLISHED** |
| Q | **ESTABLISHED** |
| O | **ESTABLISHED** |
| V | **PASS** |
| A | **APPROVED** |
| R | **ACCEPTED** |
| B | **PASS / ESTABLISHED** |
| Gate 7 | **ESTABLISHED** |
| G | **ISSUED / UNUSED** |
| Execution | **LOCKED** |
| Requirement C | **NOT ESTABLISHED** |

**The existing G is the valid Gate-7 authorization. No replacement G or ISSUE is needed.** Stop after this Gate-7 disposition. The next nonreplaceable action, original producer registration, remains outside this authorization; G consumption, REAL entropy, generation, W, salt, native execution and publication remain excluded.
