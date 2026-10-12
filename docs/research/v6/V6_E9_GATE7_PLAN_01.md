# E9 Gate-7 plan and scope reconstruction (01)

**PROPOSED FOR LEAD REVIEW, 2026-10-08. PLANNING ONLY; NOT AUTHORIZATION.**
Formal planning baseline: `569cb9aa15eaf40f4e870840e16fe99b7e40b47b`, branch `v6-research`.
No write-once Gate-7 scope, Q, operational record, producer, or study material is created by this plan.

## A. Baseline and integrity

The following checks were performed freshly before drafting this document.

| Check | Result |
| --- | --- |
| Branch | `v6-research` |
| Local HEAD | `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Upstream `origin/v6-research` | Same full commit |
| Live remote `refs/heads/v6-research` | Same full commit, verified by `git ls-remote` |
| Ahead/behind | `0/0` |
| Tracked working tree / index at entry | Clean; both diffs empty |
| Existing untracked material | `tools/research/v6/e9/seal07_independent_author_20261007_01/`; preserved untouched |
| Private transcript/provenance backup | Existing directory outside this repository; no backup path or transcript/provenance backup files tracked; local settings not tracked |
| Seal-08 implementation files | **293/293** raw SHA-256 matches |
| Seal-08 qualification files | **36/36** raw SHA-256 matches; total **329/329** |
| Candidate-31 / final-08 pairs | Equal raw digests for both manifest pairs |
| Seal-08 bound file references | **22** path/raw-hash references verified |
| Instrument derivation | Independently recomputed from P digest and complete implementation manifest; matches Seal 08 |
| Disposition 06 | Exact raw digest, 8,140-byte supplied authority text and its digest, P/I identity equality, and **40/40** review-source references verified |
| Fresh inherited/binding tests | `engine/tests/test_v6_e9_v2_independent_bindings.py`: **9 passed**, no failures |

Fresh tests used repository Python and a unique repo-local `--basetemp=.pytest_gate7_baseline_20261008_01`, outside `runs/`, with `-p no:cacheprovider`. That cache override produced one `Unknown config option: cache_dir` warning; no configuration was changed. Sandbox launch/network restrictions were overcome with approved read-only verification commands. No full qualification suite, matches, or bootstrap analysis was rerun.

The nine binding tests verify adoption/archive/scientific pins and all 1,203 inherited tracked-file pins with the exact, already authorized `.gitattributes` supersession. This is not a new preservation exception. Private-backup existence and Git separation were checked; its entire private contents were not recounted or recopied.

| Bound identity/file | Exact identity or raw SHA-256 |
| --- | --- |
| P, adopted envelope | `v6-e9-prereg-v2-539a60806eab`; digest `539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0`; raw `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4` |
| Seal 08 | `v2_final_manifest_seal_08.json`; raw `38c16e330ea1ae1efa2a3a048669961b11fe3cc0f478a7101e0472d30665dfe8` |
| Instrument I | `v6-e9-instrument-v2-3c692f23d2d9`; full digest `3c692f23d2d9a7467e07b36ea97a382c1497511033767b078dc8de057033d8e0` |
| Implementation final_08 | `b91bc866b7d0c8c168dfcf4ed0a04141bbb48e451a42f2a70c6e888d03a66e57` |
| Qualification final_08 | `a2866402b41f4cbc860b41caf518635e489a68ab61ac045f34d3164e39c12b77` |
| Disposition 06 | `02c33887f1edd9ce09838dd4cb580d8d593d413097cbf5d4d197dbaf8e5bb2e6` |
| Scope 04 | `v6-e9-v2-gate8-scope-0f65753151e2`; raw `4232fe1164456fc8109d0f56e03ee12500bc9c5d308578c11586dc4638e103e1` |

Any later baseline/source/binding discrepancy stops progression. This document itself is a new, unsealed planning file outside both final_08 manifests.

## B. Gate-7 definition and governing sources

The authoritative machine contract's `gate_order[6]` is exactly **"Separate generation authorization G"**. The bound qualification plan's ordered-gate row 7 says **"Generation authorization"**, with required evidence **"Separate study/operation-specific G; durable boundary immediately before first raw draw"**. The adopted contract's R9 names **"Generation authorization G"** and binds study ID, P/I/Q/O/V/A/R/B and materialized-artifact digests. Schema G requires N=1412, an exact sampling/boundary procedure, unique operation ID, materialized manifest and active authority tip.

Gate 7 is an **operational authorization gate**. Its prerequisites include completed qualification and independent operational verification. It is not itself another implementation seal or a payoff/Requirement-C finding. Its defining record is G, issued by the research lead for one study and one generation operation. A recorder cannot confer that authority. Completion of the authorization gate means a valid separately authorized G exists and is issued into the exact active authority tuple after every prerequisite passes. That is distinct from consuming G, recording the boundary, completing generation, or obtaining W.

The frozen row also requires the boundary at the first draw. Therefore any later scope that includes *exercising* G must implement that boundary using the accepted instrument. The text does not license treating G issuance, producer registration, consumption, all draws, salt, S, W, publication and collection as one automatically authorized task. Section L requests an explicit action endpoint.

Governing source keys used below:

| Key | Source and precise governing location |
| --- | --- |
| P | [Adopted P](../../../tools/research/v6/e9/protocol_freeze_v2_adopted_02.json), `status=FROZEN`, `body.contract_files`, `body.claim_profile`, `body.excluded_later_instances`; [separate adoption attestation](../../../tools/research/v6/e9/protocol_adoption_attestation_v2_02.json) |
| RC | [Bound rule-contract mirror](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md): PG-R1–R10; §5 R0–R14 table and changes/identity tables; §6 late-history state machine; C-LIMITED reporting table; required-record/encoding sections; inherited P9-2–P9-9; final ordered gates. Machine counterpart: [rule contract](../../../tools/research/v6/e9/amended_rule_contract_v2_proposed_02.json), especially `gate_order`, `normative_rules`, `approval_dependency_graph`, `risk_model`, `exact_interpretation` |
| SC | [Normative schema catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json): `common`, `types.InventoryStatus`, `records.I/Q/T/O/V/A/R/B/G/S/W/U/C/D/F/J/GenerationBoundary` and exact RecordRef maps |
| IQP | [Bound implementation/qualification plan](V6_E9_AMENDED_IMPLEMENTATION_QUALIFICATION_PLAN_02.md): responsibilities; W1–W8 coverage; qualification sequence; changes/reopened gates; scientific preservation; ordered later gates 1–10 |
| GO | [Gate-order disposition 02](V6_E9_V2_FINDING_DISPOSITION_02.md), "Gate ordering", and its [lead confirmation](../../../tools/research/v6/e9/v2_finding_disposition_02_lead_confirmation.json); [Gate-8 revision plan](V6_E9_GATE8_REVISION_PLAN_01.md) §1, §4.1, §5.1, §6.1–6.2; [Scope 01](V6_E9_GATE8_SCOPE_01.md), "Gate ordering and transition" |
| D3 | [Disposition 03](V6_E9_V2_FINDING_DISPOSITION_03.md), N1 resolution and registry/marker availability classification |
| S3 | [Scope 03](V6_E9_GATE8_SCOPE_03.md), "F2 exact recovery and manual stale lock", with preserved amendment/rulings |
| S4 | [Scope 04](V6_E9_GATE8_SCOPE_04.md) and its bound machine record; exact Seal-08 repair boundary |
| D6 | [Disposition 06](V6_E9_V2_FINDING_DISPOSITION_06.md), governed by [machine record](../../../tools/research/v6/e9/v2_finding_disposition_06.json): `status`, `gate_8_effect`, `not_authorized`, `acceptance_basis`, findings and exact authority text |
| E8 | [Seal-08 qualification evidence](../../../tools/research/v6/e9/v2_synthetic_qualification_evidence_08.json), [qualifier report](../../../tools/research/v6/e9/v2_seal08_independent_qualifier_report_01.json), [reproduction](../../../tools/research/v6/e9/e9-v2-seal08-independent-reproduction-20261008-01.json) and final_08 manifests |

### Naming and ordering differences retained explicitly

1. **Two meanings of Gate 8.** GO §1 distinguishes the **Gate-8 instrument revision**, accepted before Gate 7 and before O/V/A/R/B, from **operational Gate 8**, independent W over the real generated payload after generation. D6's `gate_8_operational_acceptance=ESTABLISHED` accepts the instrument/qualification prerequisite; D6 expressly leaves operational W, Q, O/V/A/R/B and Gate-7 execution unauthorized. It cannot mean an operational W already exists. Use D6's status term exactly, with this scope explanation.
2. **Frozen proposed labels remain historical.** RC/SC/IQP retain proposed/preparation headers and pre-adoption status prose. P's separate adopted envelope is FROZEN and binds those exact reviewed bytes. Do not rewrite their headers or infer their historical absence statements are current. IQP is outside P's digest; it is bound review/process evidence, while P's exact RC/SC bindings govern normative records.
3. **Old seal labels remain old.** GO describes the prospective seal-05 producer and Q decision; D3 disallows operational use of seal 05, and D6 accepts Seal 08. Operational bindings must use the accepted Seal-08 identity, not silently cite seal 05 as current qualification.
4. **Summary ordering versus exact record graph.** RC §5's prose groups generation/publication authorization before private verification, but its R11–R13 table, final ordered gates and SC require W before U/C, then D. Retain the prose discrepancy; use the explicit acyclic dependencies. No advance U, no U/C dependency in W.
5. **Overloaded symbols.** Record I and B differ from scientific integrity I and behavioral B; record F/D/S differ from payoff contrasts F/D/S. Primitive commitment `c` differs from published record `C`; neither is Requirement C. Unknown-history size H differs from historical payoff contrast H. R7 is risk-record row R, not Gate 7; R9 is G's row, not Gate 9.

## C. Prerequisite matrix

Statuses concern this exact baseline. Missing operational records are expected, not baseline failures.

| Prerequisite | Status | Current evidence / remaining requirement |
| --- | --- | --- |
| Exact synchronized checkpoint, clean tracked bytes | SATISFIED | Section A |
| Adopted amended P / C-LIMITED | SATISFIED | P plus separate adoption attestation; fresh binding tests; no original Draft-3 freshness-compliance claim |
| Gate-8 instrument acceptance | SATISFIED | D6: ESTABLISHED; no operational authority follows |
| Intact accepted Seal 08 / exact I | SATISFIED | 329/329, independent identity derivation, D6 |
| Independent synthetic qualification evidence | SATISFIED | Accepted retained 1338 collected / 1332 passed / 6 skipped / 0 failed / 0 errors; six WSL passes, static checks and adversarial reproduction. This pass adds only fresh 9/9 bindings |
| Qualified W producer, N2/N6 chain/REAL checks | SATISFIED | GO requirements implemented in accepted Seal 08; synthetic evidence does not demonstrate actual OS draws |
| N1 blocker resolution | SATISFIED | D3: RESOLVED by seal 05; carried exact publication code/coverage into accepted Seal 08 |
| S7-IQ-F1 / S7-IQ-F2 | SATISFIED | D6: resolved by Seal 08; DV8-4/DV8-5 confirmed |
| Older N/F and S8-IQ-F1–F4 | NOT YET APPLICABLE as a new repair prerequisite | Record only; no concrete operational input is being processed. If a required later operation encounters one as a blocker, stop for exact dependency disposition; no cleanup scope |
| Inherited engine/E8/policy/compatibility pins | SATISFIED | Fresh binding tests, preservation supersession, intact implementation manifest |
| Formal schema I record transport | NOT SATISFIED as a consumable RecordRef | Deterministic identity and source manifest exist in Seal 08; no standalone v2 schema I instance found in tracked E9 records. A later exact I envelope must preserve that identity, not invent approval |
| Formal v2 Q and lead acceptance of its exact boundary | NOT SATISFIED | E8 is synthetic qualification evidence, not Q. Historical `instrument_qualification.json` is **version 1**; no v2 Q found; D6 explicitly says Q ABSENT |
| Gate 3: T or explicit lead NOT_APPLICABLE | NOT SATISFIED | No applicable v2 T/disposition established. RC P9-2 requires zero additional equivalence/twin matches; no native-artifact qualification was performed. NA is the proposed route, subject to lead confirmation of Q coverage |
| Gate 4: exact selected K/E/L, custodian inspection attestation, O/V | NOT SATISFIED | No selected operational K, O or V. 157-entry candidate / 163-entry proposal are not adopted; counts are not approval. Preserve all 357 gap IDs and DEP-01–DEP-05 |
| Gate 5: exact A then specific residual-risk R | NOT SATISFIED | Both absent; amendment decision R0 is not R; history remains incomplete, H UNKNOWN, no numeric tolerance selected |
| Materialized evaluation artifacts / operational B | NOT SATISFIED | Prospective wrapper pins and qualified factory exist; no approved complete study materialization or independent B is established. Require 41 packages / 82 files / 41 defaults / complete T8 / aliases |
| Operational admissibility as a whole | NOT SATISFIED | Missing exact Q/T/O/V/A/R/B, accountable role registry, prospective study/operation scope and current authority tuple; synthetic PASS cannot substitute |
| Gate-7 action endpoint and incident/boundary evidence scope | AMBIGUOUS / LEAD DECISION REQUIRED | Normative G is clear; whether a later task issues G only or also exercises it, and the concrete trusted boundary evidence/actors, are not supplied by frozen text. Section L |
| Real payload / S / operational W / U / C / D | NOT YET APPLICABLE | Later than G; absence expected |
| Requirement C established | NOT YET APPLICABLE as an authorization prerequisite | Scientific result remains NOT ESTABLISHED; Gate 7 does not require a positive result in advance |

## D. Record and data-flow map

All new records must use SC's exact schema tag, version 2, actor/authority evidence and case-sensitive roles. RecordRef includes full digest and complete-file raw digest. `body.dependencies` contains actual earlier RecordRefs only; K/E/L, private inputs, manifests, salts and raw evidence use their declared ArtifactRef fields. Public transport uses opaque IDs and hashes, never private values/paths/raw diagnostics. No future-record placeholder digest is valid.

| Role / canonical schema suffix after `bytefray.v6.e9.` | Existence and expected absence | Inputs, exact identity/authority requirements | Reversibility and real-study crossing |
| --- | --- | --- | --- |
| P / `protocol_freeze` | Adopted v2 exists | R0 and unchanged reviewed contract/scientific pins; excludes later instances | Already frozen; retain unchanged |
| I / `instrument_identity` | Identity/manifests exist; standalone schema envelope not found | P RecordRef; all 293 final_08 sources; digest recipe SHA256(canonical({protocol_digest,sources})); deterministic exception, no approval actor | New exact envelope can represent existing I; never edit Seal 08 or change I |
| Q / `instrument_qualification` | Formal v2 absent, expected | P/I; all 36 final_08 qualification sources; complete coverage matrix, reference vectors, compatibility evidence, all attempt/environment history; independent qualifier and explicit lead boundary acceptance | Append-only evidence once issued; no entropy and no execution authority. Study-scoped common fields require an explicit prospective study ID; do not assume automatic reuse in another study |
| T / `match_qualification_receipt` | Absent, expected | P/I/Q and separate match authorization; exact source/input/attempt/consumed-value receipts. If unnecessary, explicit lead NA with reason and evidence in O's custodian attestation | Creating T implies separately authorized real matches; NA consumes no entropy. Qualification after inventory sealing reopens it |
| O / `inventory_seal` | Absent, expected | P/I/Q plus T if applicable; exact K/E/L, K_count, full E6/E8 and evidenced prior-use scope, conservative provenance, custodian actor and inspection evidence | Operational entry before draws. Immutable instance; before generation replace only by append-only renewal and downstream reapproval, never overwrite |
| V / `inventory_verification` | Absent, expected | P/I/Q/O; complete private input manifest, reproduced scope/temporal/default/derivation checks, explicit unreproduced_items; independent verifier of complete bytes | Operational independent receipt; PASS finite membership only. Changed inputs require a new V |
| A / `inventory_approval` | Absent, expected | P/I/Q/O/V and exact K/E/L; exact approved scope and unresolved IDs; research lead | Exact operational authority, revocable/renewable before generation through new records; no generic approval or count adoption |
| R / `operational_risk_acceptance` | Absent, expected | P/I/Q/O/V/A and exact K/E/L; C-LIMITED; accepted limitation; `H UNKNOWN; no useful numeric bound; only worst-case bound 1`; research lead | New specific operational risk decision, not R0. Cannot infer it from instrument acceptance; changed scope/bytes/A require new R |
| B / `pre_generation_verification` | Absent, expected | P/I/Q/O/V/A/R; complete materialized manifest, 41 defaults, full T8/aliases, accounted qualification and active tip; independent verifier | Operational gate 6; immutable receipt, invalidated by any input drift; no draws |
| G / `generation_authorization` | Absent, expected; defining Gate-7 record | Study/unique operation; P/I/Q/O/V/A/R/B, materialized manifest, active tip, boundary procedure, N and sampling; research lead; explicit ISSUE | Authorizes one operation only if separately issued. Before first draw renewal can make unused G unusable; durable CONSUME is nonreplaceable and cannot be undone or reused |
| AuthorityEvent / `authority_event` | No operational chain established | Exact existing tuple, predecessor/sequence/active tip, affected authorities, evidence, actor authorized for ISSUE/CONSUME/HOLD/RELEASE/CONTINUE/REVOKE/TERMINATE/CORRECT | Append-only operational history; no deleting events to recover an earlier state |
| GenerationBoundary / `generation_boundary` | Absent, expected | Existing tuple through G, current tip/fence epoch, unique operation, trustworthy durable instant, original producer/first-raw/REAL declaration evidence | Permanent temporal/scientific boundary before first raw draw; never regenerate/backdate it |
| SeedPayload / `seed_payload`; S / `generation_receipt`; primitive c | Absent, expected; outputs of authorized generation, not prerequisites for G | Exact original tuple/boundary; ordered 1412-position payload; complete accepted/rejected raw audit; 32-byte salt; preceding supplement/continuation tip; original recorder. S binds payload/audit/salt; c is calculated afterward | REAL study material and nonreplaceable records. No replacement list, salt, or payload under the same study |
| W / `private_commitment_verification` | Absent, expected; operational Gate 8 | RecordRefs exactly P/I/Q/O/V/A/R/B/G/S; primitive `body.commitment=c`; private payload/salt; full chain/current tip, original producer and REAL evidence; independent registered verifier, separate W-production authorization | Write-once W/PASS over immutable real bytes; no alternate W after terminal verification failure; no future U/C dependency |
| U / `commitment_publication_authorization`; C / `published_commitment` | Absent, expected; Gate 9 | U adds W to earlier tuple and approves c plus sanitized template/PASS pre-U receipt; C adds U; lead U then authorized publisher | Separate publication consumption and immutable public bytes; no replacement public commitment |
| D / `payoff_authorization`; F / `final_registered_result` | Absent, expected; Gate 10 and later final evidence | D binds through C and current integrity/source pins; F full D tuple, complete rectangle/attempt/diagnostic evidence, independent integrity/final reproduction | Native collection separately authorized; first started cell changes historical-integrity terminal disposition. Final F immutable; late correction append-only |
| J / `integrity_notice`; prefix/history supplements and LeadContinuation | Absent; conditional, expected | Only records actually existing at discovery stage; independent outcome-blind evidence and separate lead release/continuation/revocation | Conditional append-only controls, not routine prerequisites to manufacture. Terminal events never authorize resumption |

The exact sequence is:

```text
adopted P + accepted Seal-08 I/source boundary + independent synthetic evidence
  -> separately authorized I transport / Q decision and formal Q
  -> Gate 3: T or explicit NOT_APPLICABLE
  -> Gate 4: exact private K/E/L + custodian O -> independent V
  -> Gate 5: lead A -> lead R
  -> Gate 6: exact package/default/T8/alias materialization -> independent B
  -> Gate 7: separate study/operation-specific lead G + ISSUE
     [separate action scope required before registering/consuming/exercising G]
  -> original producer registration -> durable CONSUME(G)
  -> first-raw marker + REAL declaration + durable GenerationBoundary
  -> first raw draw -> exact accepted list -> salt -> SeedPayload/S -> c
  -> operational Gate 8: separate W-production authorization, ISSUE(+S), W
  -> ISSUE(+W), clean issuance tail, pre-U template PASS
  -> Gate 9: separate U -> immutable C publication
  -> Gate 10: separate D -> complete collection/integrity/analysis/final F
  -> Requirement C only if valid accepted C-LIMITED row 7
```

This separates nominal gate number from implementation acceptance chronology. It does not add a new numbered gate.

## E. Authorization matrix

Every operational item is forbidden in this planning task by the user's request and D6. A proposed future scope is not an authorization.

| Action | Current status | Exact later authorization/evidence boundary | Does Gate 7 itself change it? |
| --- | --- | --- | --- |
| REAL entropy | LOCKED | Explicit scoped G/action authority after Q/T/O/V/A/R/B, registered original producer, durable CONSUME, protected exact tip/lease and verified boundary before first draw | G can authorize its one operation; issuance alone neither draws nor bypasses boundary |
| Generation | LOCKED | Same exact G plus separately approved action endpoint and complete active tuple | Only that generation operation, never other operations/studies |
| Operational W production | NOT AUTHORIZED | After S, ISSUE(+S), separate lead W-production authorization and independent accepted producer/verifier; operational Gate 8 | No |
| Salt creation | NOT AUTHORIZED | Same authorized generation operation, exactly 1412 accepted positions, complete audit, active unheld tuple, no previous salt attempt, protected `salt_creation` | Only if later action scope explicitly includes completion; never before list completion |
| Native matches | NOT AUTHORIZED | Qualification: separate Gate-3 match authority/T. Payoff: separate D after W/U/C (Gate 10) and per-start/retry checks | No |
| Operational publication | NOT AUTHORIZED | Gate 9: W/PASS, template/PASS receipt, separate U, current active tuple and authorized publisher. Integrity notices have their own actor/event scope | No |
| Q creation | NOT AUTHORIZED | Separate independent qualification-record task and lead acceptance of exact P/I/test/coverage/evidence boundary before Gates 3–7 | No; prerequisite |
| O creation | NOT AUTHORIZED | Separately scoped Gate 4 after Q and T/NA, complete exact private K/E/L and custodian inspection attestation | No; prerequisite |
| V creation | NOT AUTHORIZED | Separately scoped Gate 4 independent complete-input verification after O | No; prerequisite |
| A creation | NOT AUTHORIZED | Gate 5 exact lead approval after O/V | No; prerequisite |
| R creation | NOT AUTHORIZED | Gate 5 separate specific lead uncertainty acceptance after A | No; prerequisite |
| B creation | NOT AUTHORIZED | Gate 6 separately scoped independent complete pre-generation verification | No; prerequisite |
| G creation/issuance | NOT AUTHORIZED | Lead-reviewed scope and separate exact authorization after every prerequisite; existing B/current tuple | This is Gate 7's defining authorization event; cannot self-authorize |
| Execution authorization | LOCKED | Each action's scoped authority: G generation; separate W production; U publication; D payoff. Active tip/lease and source checks at each consumer | Only scoped generation; no global unlock |
| Real stale-lock clearance | NOT AUTHORIZED | S3: separate incident authorization, proven holder death/no legitimate concurrent root user, preserved/hash-verified lock bytes/metadata, stale rationale, operator/lead identity, exact clearance action; special handling if nonregular/unreadable | No standing clearance authority from G or any seal |
| Other irreversible real-study action | NOT AUTHORIZED | Explicit authority for exact identity, actor, operation, inputs and stopping point; no implicit extension from planning, seal or generic gate acceptance | Only actions expressly within a later G scope; Section H |

## F. Requirement C

Requirement C concerns beneficial observation-conditioned **allocation/policy change within a match**, beyond merely executing a fixed reactive algorithm. The [post-E8 requirements review](V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md), §5 row C and §6/§8, distinguishes fixed stateful execution from profitable allocation revision. Draft 3 §1 asks whether legal observation-driven revision supplies practical benefit beyond competent constants and the declared schedule panel on unchanged T8; no repeated-revision requirement is added.

The effective E9 rule is RC **PG-R9**: **"a valid amended-protocol result in registered priority row 7 SHALL establish Requirement C only in the registered bounded scope"**, with the permanent historical non-reuse limitation. RC's exact row 7 condition is **"I and B pass; F/D/S supported; no severe constraint"**. Here I/B are scientific predicates, not the I/B records.

Available evidence: frozen E8 mechanics/ecology, qualified Q-C1–Q-C15 policy capability, the adopted prospective comparisons/predicates, accepted Seal-08 implementation/independent synthetic qualification and inherited pins. E8's adaptive payoff conclusion remains NEITHER; capability and instrument correctness do not supply E9 payoff evidence.

Missing evidence: the entire authorized real-study record chain through D; independently verified payload/W; complete **900,856-cell** rectangle (29 physical rows × 11 opponents × 1412 positions × 2 seats); valid result/replay/trace/attempt and diagnostic integrity; legal causal observation/request/commit/action realization at at least two distinct positions and at least one in each seat; all required F/D/S lower practical-benefit bounds >=1/10 using frozen joint seed-block uncertainty; all interpretation/exposure diagnostics and absence of a severe seat/stall/immunity/phase constraint; independent final machine-record reproduction with no active hold or historical-integrity failure.

H superiority is separate competitive context. It is additionally required for broader "outperforms the best fixed policy" wording, not for replacing the exact F/D/S row-7 condition. It cannot establish exhaustive historical non-reuse. No numeric unknown-history risk bound, new tolerance, or payoff result is inferred.

Earliest establishment is **after Gate-10-authorized collection and complete registered final integrity/analysis/evidence**, if valid row 7 actually occurs. Gate 7 cannot establish C. Rows 1–6, hold, cancellation or historical failure leave it NOT ESTABLISHED. Requirement D/F and product promotion remain separate.

Every valid numerical finding must retain RC's exact permanent limitation:

> E9 used prospectively collected OS-CSPRNG draws, unique within the study and verified disjoint from the approved known-use exclusion inventory. Complete prior qualification history and exhaustive historical non-reuse were NOT ESTABLISHED; reuse of an unrecorded historical match-seed value cannot be ruled out. No useful numerical bound on that unknown-history reuse risk was established.

## G. Q analysis

Q is **`bytefray.v6.e9.instrument_qualification` version 2**, identity prefix `v6-e9-instrument-qualification-v2-`. RC R2 and SC Q require complete independently qualified amended instrument evidence, not an inherited v1 PASS or a preparation check. Q binds adopted P, the exact accepted I, the complete raw qualification-source manifest, coverage matrix, qualified synthetic reference vectors, v1 compatibility evidence and all attempt/environment history. Its independent qualifier is accountable and separate from production of the evidence being verified; the lead accepts the exact qualification boundary (IQP responsibilities, SC common.independence).

Seal-08 evidence is a basis for that later decision. It already includes independent reproduction and accepted findings. **It is not the formal Q record.** This task's 9/9 binding check is baseline verification only and cannot become Q. The accepted reports identify native artifact qualification as NOT PERFORMED and synthetic limits on proving actual OS entropy. Q must retain these limits and authorship/provenance disclosures; do not strengthen them.

A separate authorized Q task can create the exact I transport and assemble complete accepted evidence without new source changes if the lead accepts that coverage. Q's common `study_id` and Actor evidence must be explicit; the source identity is reusable only under valid bindings, not an automatic cross-study Q authority. If additional source/coverage qualification is required, qualify that changed boundary and renew Q before operational records; separately authorize any matches and account their values through T.

Q creation would be premature now, or with no lead boundary acceptance, incomplete source/coverage/attempt manifests, substituted I, an unresolved material qualification blocker, unaccounted matches, or a producing-agent receipt presented as independent reproduction. Gate 7 consumes a prior valid Q; it does not create Q. Q remains **ABSENT** throughout this task.

## H. Irreversibility boundary

There is no single interchangeable notion of "irreversible". Preserve these ordered boundaries:

1. **First operational records and authority history.** Separately authorized I/Q/T-or-NA/O/V/A/R/B/G and ISSUE entries must remain append-only. Before generation the frozen change table permits operational renewal/revocation without changing valid P/I/Q. It does not permit erasing previous versions. These steps bind a prospective study but do not consume REAL entropy or yet make its accepted seed list immutable.
2. **Earliest nonreplaceable producer binding: original producer registration.** Static inspection of accepted `authority.py:register_producer` shows the first durable `producer-roots/<G.digest>.json` fixes the study, exact G/operation, original tuple, root and accountable recorder. A changed root/actor/operation for the same G is refused. `Generator.__init__` performs this registration and writes evidence; **constructing Generator is already operational work**, before `consume` or `draw_one`. Do not construct it in planning. A different approved tuple/G would need the frozen pre-generation renewal process; do not delete the registry to fork the same G.
3. **First nonreplaceable authority consumption: `CONSUME(G)`.** `Generator.consume` calls `AuthorityLog.consume_generation`; the exact G is durably consumed once and its original producer evidence is bound. No resetting the log, unconsuming G, or reusing it for another operation. This happens before any raw draw and requires explicit action authorization.
4. **First scientific first-draw boundary: first-raw marker and GenerationBoundary.** Under the protected raw-draw lease the accepted generator durably marks first raw, records the REAL declaration and trustworthy instant, writes/read-verifies `boundary.json`, then writes the first draw intent **before `os.urandom(8)`**. RC PG-R4's boundary is the durably recorded instant **immediately before the first experimental raw draw**. It is not O seal, G issuance, producer registration, or commitment publication. Marker/boundary/intent interrupted or ambiguous before a completed raw audit is not proof that no entropy was consumed; hold and investigate, never regenerate the boundary or invent an instant.
5. **First actual REAL entropy:** `Generator.draw_one` reaches `source(8)` on the REAL branch. A rejected candidate still consumes/audits raw entropy; only accepted candidates become experimental positions. The list, original K/operation and subsequent salt/payload cannot be redrawn to repair evidence. After N=1412 accepted positions, `complete` may draw a separate **32-byte salt** under its own protected action, then seal payload/S. Operational W is later and consumes no new entropy; Q is earlier and proves qualification, not study generation.

Sections 2–5 are outside the recommended G-issuance-only endpoint. All five are outside this planning task. Any separately authorized Gate-3 matches would be an earlier real execution boundary on a different qualification operation and must finish/account inputs before O; they are not authorized here or automatically needed.

## I. Proposed sequence and stopping points

Steps P0–P2 describe this planning pass. L1–L7 are a future roadmap requiring their own explicit scopes/actors; they are not instructions to execute now. X1–X3 explain the later boundary and remain excluded from the recommended Gate-7 authorization-only scope.

| Step | Proposed work | Success state / mandatory stop |
| --- | --- | --- |
| P0 | Verify exact branch/HEAD/upstream/live remote, cleanliness, private separation, seal/disposition/inherited bindings | Section A passes; any mismatch stops before planning edits |
| P1 | Reconstruct definitions, exact dependency maps, coverage limits, failure semantics and action scope from P/RC/SC/IQP/GO/D6 | This document; no fabricated operational receipt |
| P2 | Return plan and unresolved lead decisions | Stop here. No write-once scope, new records or operations |
| L1 | Lead review/endpoint ruling; later freeze a new Gate-7 scope only after rulings | Exact source baseline, actor roles, write set and stopping point; still no implied operation |
| L2 | Separately authorize exact I envelope and formal Q assembly/independent assessment/lead acceptance | I digest remains Seal 08; Q complete and accepted; stop if missing coverage requires qualification/source changes |
| L3 | Lead explicitly dispositions T as NOT_APPLICABLE, recommended on current frozen zero-additional-match requirement; or separately authorizes required qualification/T | NA with reason/actor evidence, or complete verified T before O; any changed qualification boundary renews Q first |
| L4 | Separately authorize full private evidence preparation, exact K/E/L and custodian O; independent verifier produces V | Both complete revealed lists, all evidenced known prior values and conservative provenance; every limitation retained; finite PASS only; no count selection by this plan |
| L5 | Lead approves exact A, then separately accepts precise R | Exact K/E/L/O/V scope and unknown-history assurance accepted; no generic waiver |
| L6 | Separately authorize deterministic study materialization without matches/draws and complete independent B | 41 packages/82 files/41 defaults, T8/aliases, source/checker/authority and no-intervening-use checks; B PASS; stop for any unexplained binding gap |
| L7 | After complete prerequisites and reviewed action scope, lead issues exact G and ISSUE(+G) into active tuple | **Recommended stopping point:** valid unused G, no Generator registration, CONSUME, first-raw marker, boundary, intent, draw or salt. Authorization-only Gate 7 completed; operational exercise still separately scoped |
| X1 | Only if separately approved: bind original producer then consume exact G | Irreversible registry/CONSUME evidence; stop for any ambiguous interruption; never reconstruct a replacement producer |
| X2 | Only under explicit generation execution scope: boundary, audited draws, accepted list, salt, payload/S/c | Immutable completion or frozen hold/cancellation; stop before W production regardless of generation success |
| X3 | Separately authorize operational W, then separately U/C and D | Independent verification/publication/payoff gates remain distinct; none included merely by authorizing L7 or X2 |

## J. Failure and recovery semantics

Use the frozen classifications at their actual stage. W outcomes are not generic labels for drafting, Q or inventory work. A refused pre-draw operation is not automatically a cancelled generated study. Missing evidence is never proof of non-use/non-overlap.

| Step / condition | Recoverable failure or infrastructure interruption | Terminal scientific failure / lead-disposition stop | Retry, same state and new-material rule |
| --- | --- | --- | --- |
| P0 | Interpreter/network access issue: obtain safe read-only verification; retain honest counts | Any actual baseline integrity mismatch: stop as required by this request | Read-only retry allowed; no remediation, new study material or scope record |
| P1–P2 | Missing reference can be located/read; planning typo can be corrected in this unsealed plan | Governing contradiction or directly blocking finding: record exact dependency and seek disposition | Draft-only revision; no operational material |
| L1 | Lead scope incomplete | No frozen scope until endpoint/actor/evidence rulings are explicit | Reviewable drafts may change; no automatic acceptance |
| L2 | Unavailable retained qualification evidence requires exact restoration; failed/env attempts remain in audit history | Unexplained coverage/source/identity mismatch or changed boundary: stop for qualification/scope decision | No implicit test retry/new qualification; independently authorize required checks. Same-state evidence assembly only; no entropy/native matches |
| L3 | Missing authorization/T/NA blocks gate | Changed source/coverage boundary or required matches not accounted: stop/requalify as specified | No match retry inferred. Any match-producing checks need separate exact authorization and immutable attempts; no experimental replacement material |
| L4 | Missing/unreproduced known-source/private evidence blocks V PASS | Inventory change/new prior use before generation: **INVENTORY_GATE_REOPENED**, renew O/V/A/R/B even if K values stay equal | Append new approved inventory/evidence versions before generation, retain originals; no draw/salt. Unsupported derivation or absent independent proof cannot be waived as complete |
| L5 | Missing A/R, actor evidence, exact scope or unquantified-risk acceptance blocks progression | Revocation/changed O/V/K/E/L/scope requires new A then R | New explicit append-only approvals possible before draws; no scientific material generated |
| L6 | Incomplete materialization/read-back/authority evidence blocks B PASS | Wrong package/default/condition/source/equivalence pins: stop preparation; no expanded rectangle or silent repair | Deterministic pre-study materialization may be repeated only within its separate scope; replace no frozen input, renew B after changes, no matches/entropy |
| L7 | Absent/stale/revoked/mixed tuple, wrong actor, hold or uncertain active tip refuses issuance/use | Exact authority/source failure: lead disposition; no invented G/authority | Before draw, frozen renewal can revoke unused old G and approve a new tuple. Never erase history or consume on a retry |
| X1 | Busy/stale lock or interrupted append fails closed | Uncertain CONSUME/registry state: investigate retained bytes; no second operation/root or implicit lock clearance | Re-read and prove exact state; same G never consumed twice. No new material; S3 incident clearance requires separate authorization |
| X2 | Raw intent/audit mismatch, lost boundary/marker, uncertain entropy consumption or salt intent without valid salt: integrity unresolved | **INTEGRITY_HOLD_PENDING_ADJUDICATION**; unresolved precollection closure **CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY**, result NOT PRODUCED | No redraw/salt retry from assumed absence; no inherited cell-recovery rule for generation. Retain same prefix/audit/tuple; resume only where frozen evidence and separate release permit |
| X2, verified new pre-boundary history | Stop/fence, snapshot retained ordered prefix/count/audit position, independent equality/scope/prior-use/original-K verification | Prefix overlap: **CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP**. Any verified outside-original-K value: **CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K**, even with disjoint prefix | Only all-values-already-in-original-K, intact disjoint prefix/original tuple and separate PG-R8 continuation permit same paused G's remaining draws; no replacement positions, K or N |
| X3, W preconditions/availability | **REFUSED_PRECONDITION** before protected verification; **UNAVAILABLE** during verification; qualified interruption handling under S3 | Present positive registry/marker mismatch: **FAILED_VERIFICATION**, no later attempt for same S. S8-IQ-F2 malformed G: fail closed, investigate retained evidence; no fabricated scientific outcome | Precondition retry only after changed condition; unavailable retry only byte-identical/hash-verified restoration. S3 publication recovery requires identical scientific state/verifier/originating tip, no intervening event, full re-verification and exact byte equality, at most one PASS; no scientific regeneration |
| X3, W interruption/PASS | **INTERRUPTED** retained; missing qualified publication/PASS may be recoverable; unchanged **PASS** is final | Unproven partial canonical W or changed originating authority after interruption blocks exact recovery pending disposition; terminal FAILED_VERIFICATION never retryable | Retain every old attempt/candidate. Restore/publish only missing identical evidence under exact S3 conditions. Never rewrite W, salt/payload or complete outputs |
| Any actual S8-IQ-F1–F4 dependency block | Preserve exact finding and rejected operation | Stop for lead disposition naming the required operation/dependency; no Seal-09 cleanup inferred | No repair/reopen in this task, and no redraw to escape malformed evidence |

RC PG-R5–R10 govern subsequent scientific disposition: before first-cell start, proven overlap cancels with NOT PRODUCED; once **any cell has started**, including a failed first attempt or incomplete collection, overlap/unresolved closure makes the full registered result NOT EVALUABLE. Terminal revocation cannot be released. New study requires PG-R10: outcome-independent lead decision, new study identity, verified approved inventory including retired accepted positions as conservative exclusions, fresh R and separate G/U/D; no automatic restart.

RC P9-9's one additional execution / two started-attempt cap is **cell infrastructure recovery only**, after D. It does not permit generation, salt, Q, inventory, W or publication retries. Its full external-infrastructure allowlist, no terminal completion, identical-cell inputs, outcome blindness, fencing and immutable attempt predicates remain required. Stale-lock clearance remains incident-specific under S3, never automatic.

Operational Gate-8 chain restrictions also remain: after a completed-stage CONTINUE/RELEASE containing S, a merely tuple-extending ISSUE tail can cause REFUSED_PRECONDITION under the frozen verifier; a non-ISSUE tail can produce FAILED_VERIFICATION (Scope 02 F2). Do not manufacture redundant ISSUE/HOLD/CONTINUE events. If a real required transition encounters this boundary, stop for disposition without broadening the instrument.

## K. Implementation and seal impact

**No new source/test change is identified as a frozen Gate-7 requirement.** The defining work is procedural authorization and exact record/evidence assembly plus already qualified consumer operations if separately authorized. Existing accepted modules already provide:

| Existing file | Relevant capability / frozen requirement | Seal-08 membership |
| --- | --- | --- |
| `tools/research/v6/e9/v2/records.py` | SC exact I/Q/O/V/A/R/B/G encoders/readers, conditional T/NA, full RecordRefs and write-once records | Implementation |
| `tools/research/v6/e9/v2/identities.py`, `instrument.py` | RC R2; deterministic I, complete source checks | Implementation |
| `tools/research/v6/e9/v2/inventory.py` | RC R4/R5, PG-R2; complete known-set/revealed-list checks with retained limitations | Implementation |
| `tools/research/v6/e9/v2/commitment.py` | RC R8; exact 41-package/82-file/default/T8/alias materialization verification | Implementation |
| `tools/research/v6/e9/packages.py` | RC P9-2; fixed prospective wrapper factory | Implementation |
| `tools/research/v6/e9/v2/authority.py` | PG-R3/R4, RC R9; ISSUE, original registry, CONSUME, active tip, role/source/fencing checks | Implementation |
| `tools/research/v6/e9/v2/generation.py` | RC R9/R10, PG-R4/PG-R8; durable boundary, REAL branch, exact N/order/audit/salt/S | Implementation |
| `tools/research/v6/e9/v2/private_verification.py` | RC R11; already accepted W producer; later operational Gate 8 | Implementation |
| `tools/research/v6/e9/independent_v2_reproduce.py`, final_08 test/guard/harness sources | Complete accepted independent qualification boundary | Qualification |

All files above remain unchanged. Runtime private records/packages are separately bound operational artifacts, not repository implementation edits. SC record creation through existing code is not a new implementation project merely because operational instances are absent. No CLI convenience command is mandated by the frozen records.

This is a static planning assessment, **not certification of an as-yet-unconstructed operational resolver/source callback, custodian dataset, actor registry, boundary-time evidence or filesystem deployment**. S3 explicitly requires audited callbacks and supplies no blanket certification for arbitrary callbacks. Future preparation must show exact inputs fit the sealed mechanisms. If it requires an unsupported derivation, changed scientific producer/driver/checker, altered retry behavior or new required qualification coverage, stop and scope that change before implementation.

**Another seal is not automatically required.** With P and all implementation/qualification bytes and accepted coverage unchanged, use accepted Seal 08; create formal Q and the later operational records separately. Materialization/inventory/approval changes alone require new O/V/A/R/B and applicable downstream authorities, not new I or another seal (RC changes table; IQP changes section).

If implementation bytes or the complete implementation boundary change, derive a new I and perform an explicitly scoped new seal/independent reproduction cycle before downstream records. Test/verifier/coverage-only changes require new independently qualified Q and downstream bindings even if I stays equal; if they change the sealed qualification manifest, a new seal/reproduction boundary is required rather than editing final_08. Normative changes require new P and affected qualification. None is authorized by this plan. No sealed file has been identified for editing; any such proposal must name the exact file, frozen requirement and new boundary before authorization.

## L. Decisions needed from lead

There is **no unresolved ambiguity in Gate 7's canonical G definition or W-before-U/C/D dependency order**. The complete future action scope is not yet unambiguous. Only these substantive choices remain; missing approvals themselves are ordinary later gates, not interpretations invented by this plan.

1. **Endpoint:** authorize a future task to prepare/issue G only after separately completed Q and Gates 3–6 (recommended), or expressly include producer registration, CONSUME and generation through S/salt/c. If broader, list each irreversible action and the stopping point; W still requires separate authorization. Specify accountable prospective study/operation/actor identities, approved private output root and trustworthy boundary-time evidence in that later scope. Frozen text fixes their roles/bindings, not their concrete values.
2. **Q coverage/T applicability:** accept formal Q assembled from the exact accepted Seal-08 synthetic boundary with its retained limitations and explicit T NOT_APPLICABLE (recommended; RC requires zero additional equivalence/twin executions), or require additional qualification. If additional, state the exact missing coverage and separately authorize any matches/source/qualification-boundary change before operational inventory sealing. Seal acceptance alone cannot silently make this decision or create Q.
3. **Operational inventory/risk selection:** later identify exact private K/E/L and custodian inspection boundary for O/V, then approve exact A and specific R. The records cannot choose K or accept uncertainty on the lead's behalf; neither 157 nor 163 is an operative count by default. This is a required substantive operational decision, not a request to close all historical gaps or reopen record-only findings.

No new gameplay/profile/tolerance/threshold decision, historical cleanup, stronger provenance reconstruction or Seal-09 remedy is requested.

## M. Proposed future scope, not frozen

**Current task write set:** only this new file, `docs/research/v6/V6_E9_GATE7_PLAN_01.md`. Verification may create disposable pytest baseline artifacts; no source/test/configuration/protocol/schema/seal/scope/disposition is modified. No commit/push.

After lead review, proposed repository scope-record filenames are `tools/research/v6/e9/v2_gate7_scope_01.json` and `docs/research/v6/V6_E9_GATE7_SCOPE_01.md`. They would bind the exact planning baseline, P, Seal 08/final_08 and D6, carry the lead rulings and exact action endpoint. **Neither is created now.** They are proposed process records, not G and not a substitute for prerequisite authorizations.

Proposed separately authorized prerequisite write sets, expressed as exact canonical roles rather than fabricated existing evidence:

| Separate stage | Proposed new outputs only |
| --- | --- |
| Q decision | Exact schema I envelope and formal schema Q, their complete qualification-evidence manifests/coverage/attempt/vector refs and separate lead boundary acceptance; proposed repository names `v2_instrument_identity_08.json`, `v2_instrument_qualification_08.json`, and readable `V6_E9_V2_INSTRUMENT_QUALIFICATION_08.md`, all under existing E9 paths. Public transport only after its exact content is reviewed/sanitized |
| Gate 3 | Explicit lead T NOT_APPLICABLE evidence/attestation; T only under separately approved match qualification scope |
| Gate 4 | Private exact K/E/L, inspection/known-use/conservative-provenance evidence, schema O and V and complete independent private-input receipts; retain original candidates/history |
| Gate 5 | Schema A then R bound to those exact O/V/K/E/L bytes and limitations |
| Gate 6 | Private deterministic 41-package/82-file evaluation artifacts, 41 defaults, complete T8/alias manifests, no-intervening-use evidence, audited actor/resolver/source bindings and schema B |
| Gate 7, recommended endpoint | Schema G, exact separate lead authority evidence and associated ISSUE(+G) AuthorityEvent/active-tip publication; previously accepted inputs read-only. Stop with G unused; **no original-producer registry, CONSUME or first-raw writes** |

Operational record locations must be fixed in the reviewed scope beneath the lead-approved private study namespace, with private locations resolved from opaque IDs. Proposed private record layout is `records/O.json`, `V.json`, `A.json`, `R.json`, `B.json`, `G.json` within that `records/` directory; exact names are proposed, not prescribed by RC. The scope must name the actual approved root and every auxiliary evidence/package output before freezing. That root is unresolved here; inventing a seed-bearing path or issuing records to an implicit study would violate this plan. Authority serialization uses the existing sealed layout: `evidence-records/<digest>.json`, `evidence-raw/<raw-hash>.bin`, `event-<sequence>.json`, and `active.json`, with exclusive transaction lock handling as implemented. Only expressly approved record/event types may be added.

If the lead chooses generation execution as well, a **separate explicit operational extension** must name: original `producer-roots/<G.digest>.json` registration/evidence; CONSUME event; `first-raw/<G.digest>.json`; producer `boundary.json`; retained REAL declaration and trustworthy instant; `draw-<ordinal>.intent.json` / `.audit.json`; conditional retained prefix/supplement/continuation evidence; `salt.intent.json` / `salt.bin`; `audit.json`; `payload.json`; `receipt.json` (S); retained ArtifactRefs and primitive c calculation. Scope follows the same G/study/original K and fixed N. These are identified for review and **excluded from the recommended G-only scope**; no call to Generator is allowed in that scope.

W/PASS attempts, operational W production, pre-U receipts, U/C publication, D/native collection, real stale-lock clearance, integrity incident actions, new seals and source/test changes remain separately scoped. No operational write may modify a previous record; only the sealed active-tip/transaction mechanism updates its derived marker. Frozen repository evidence, private backups, prior dispositions/scopes/seals and settings remain preserved.

## Status at return

| Item | Status |
| --- | --- |
| Gate 8 | **ESTABLISHED** (D6's accepted instrument/qualification prerequisite; operational W still absent) |
| Gate 7 | **NOT AUTHORIZED; NOT STARTED** |
| Execution | **LOCKED** |
| Requirement C | **NOT ESTABLISHED** |
| Q | **ABSENT** (formal amended v2 Q) |
| Historical coverage / exhaustive historical non-reuse | **NOT ESTABLISHED** |
| Operational work in this task | **NONE** |
| New scope freeze / source or test edits / new seal / commit / push | **NONE** |

Stop after this plan. Lead review and separate later authorization are required before any proposed operational record or irreversible action.
