# E9 pre-G preparation and decision record (01)

2026-10-08. **PREPARATION STOPPED BEFORE FORMAL Q: required concrete study/actor bindings are not supplied.**
This is a decision document, not Q, O, V, A, R, B, G or an authority event.
The accepted Gate-7 plan is preserved unchanged. The current request accepts the Seal-08 basis for Q (R2), authorizes pre-G preparation, and fixes future Gate 7 to G issuance plus ISSUE only, stopping with G unused (R1).

## A. Baseline

All required integrity checks passed freshly before writing preparation evidence.

| Check | Result |
| --- | --- |
| Branch / required HEAD | `v6-research` / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b` |
| Upstream / live remote | Both equal required HEAD; live `git ls-remote --heads origin v6-research` returned exit 0 |
| Ahead / behind | `0/0` |
| Tracked tree / index | Clean; both diffs empty |
| Entry untracked | Gate-7 planning document and previously documented `seal07_independent_author_20261007_01/`; preserved |
| Seal-08 implementation / qualification | `293/293` and `36/36`; **329/329** raw hashes match |
| Candidate 31 / final 08 | Both manifest pairs byte-identical |
| Seal / disposition bound path-raw references | `22/22` and `40/40` match |
| Disposition-06 authority | 8,140 UTF-8 bytes; raw SHA-256 `e868a56a5845146bef9d68b69acee6b37c3eb15764b3c5428fc678a5f6e63a55` |
| P/I identity and complete source checker | PASS; instrument independently rederived; adopted review bindings verify |
| Fresh independent-binding tests | **9 passed**, 0 failed, 0 skipped; exit 0, 8.26 s |

Tests used the repository interpreter, `-B`, and a fresh repo-local `--basetemp=.pytest_pre_g_baseline_20261008_01`, outside `runs/`. Initial sandbox network/interpreter restrictions were resolved with approved read-only invocations. No complete qualification, full headless suite, matches or statistical analysis was rerun; those could cross the explicitly excluded execution boundary. No source/test change warrants new lint/type/qualification runs.

| Bound artifact | Raw SHA-256 |
| --- | --- |
| Adopted P | `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4` |
| Seal 08 | `38c16e330ea1ae1efa2a3a048669961b11fe3cc0f478a7101e0472d30665dfe8` |
| Implementation final 08 | `b91bc866b7d0c8c168dfcf4ed0a04141bbb48e451a42f2a70c6e888d03a66e57` |
| Qualification final 08 | `a2866402b41f4cbc860b41caf518635e489a68ab61ac045f34d3164e39c12b77` |
| Disposition 06 | `02c33887f1edd9ce09838dd4cb580d8d593d413097cbf5d4d197dbaf8e5bb2e6` |

P is `v6-e9-prereg-v2-539a60806eab`, full body digest `539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0`.
I is `v6-e9-instrument-v2-3c692f23d2d9`, full recipe digest `3c692f23d2d9a7467e07b36ea97a382c1497511033767b078dc8de057033d8e0`.

New write-once evidence, canonical UTF-8 JSON with one trailing LF and verified readback:

| Artifact | Identity | Raw SHA-256 |
| --- | --- | --- |
| [Exact current authority text](../../../tools/research/v6/e9/v2_pre_g_authority_01.json) | `v6-e9-pre-g-authority-4d6b36891140` | `871a56202785de2c08c612e6a17bedebd1462cba24056fae295a2276eaab6821` |
| [Baseline verification](../../../tools/research/v6/e9/v2_pre_g_baseline_verification_01.json) | `v6-e9-pre-g-baseline-0a0f0a878b21` | `3a93110128a890a1ddfbbab15518b271da809cd4dadee99ea8b4d2848dc40886` |
| [Deterministic I envelope](../../../tools/research/v6/e9/v2_instrument_identity_08.json) | Existing I above | `cbdc00bd767179b4353625f4fb10115ec9c45fdcbb01a8c19ced3c3fb2b48fd7` |
| [Q assembly dossier](../../../tools/research/v6/e9/v2_pre_g_q_assembly_01.json) | `v6-e9-pre-g-q-assembly-0e5f4cd6e6c5` | `5a9ffed7c2e2cc346264070135fac74217bc23a38c07c216e0b1b0bdee12002e` |

The three process-evidence records use descriptive preparation schemas, not invented formal protocol roles or approvals. I alone uses its existing frozen schema and digest exception; its recipe digest is not the ordinary digest of the complete I body. Its exact P RecordRef resolves and its raw digest verifies. No existing record was overwritten.

## B. Formal Q

**Q: ABSENT. No formal Q identity or raw hash exists.** The dossier identity/hash above must never be supplied as a Q RecordRef.

R2 accepts the exact Seal-08 synthetic qualification basis. The dossier binds both complete final manifests, Seal 08, accepted Disposition 06, independent qualifier report and reproduction, retained reference vectors, all W1-W8 coverage requirements, all 29 accepted test-module sources, compatibility/preservation evidence and retained attempt/environment histories. Earlier failed seals/attempts remain historical failures. Static test-function enumeration is an index, not proof of parametrized execution; the accepted run records establish actual counts.

Q certifies only the complete amended instrument under this accepted synthetic boundary. It does not certify actual OS entropy, native match/artifact qualification, physical-power-loss robustness, stronger human/model-family independence, exhaustive history, experimental payoff, Requirement C or execution authority. S8-IQ-F1-F4 remain NOTE / RECORD ONLY. The retained independent qualifier is the separate Claude Code context `ab5ed985a387178b1` (session `2c539e95`), resumed after its recorded API-limit interruption. This recorder assembles accepted evidence and does not impersonate that qualifier or claim a new independent reproduction. Original raw logs/private backups remain in place; this task does not claim a fresh comprehensive rehash of those external stores.

The stopping requirement is concrete. [Frozen catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json) `common.body_common_fields` requires `study_id` and Actor evidence; [accepted plan](V6_E9_GATE7_PLAN_01.md) section G says Q's study and Actor evidence must be explicit. Its section M says the private study namespace is unresolved and forbids issuing to an implicit study or inventing a seed-bearing root. The request supplies none of the concrete study ID, custodian ID, research-lead ID or approved private namespace. Those details were requested during this task; no answer has been received at writing.

No stronger scientific certification or code change was found necessary. Missing contextual bindings prevent issuance; R2's coverage acceptance is preserved and does not need to be requested again. Final Q can be assembled from these exact retained inputs after the contextual bindings are supplied and validated.

## C. T determination

**Route: NOT_APPLICABLE explicitly supported for the accepted synthetic-only configuration. Formal study-bound determination: NOT RECORDED. T artifact: ABSENT.**

Exact governing text in [frozen rule contract](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md), encoding/dependency paragraph at lines 195-196: "If no match-producing qualification is required, bind an explicit not-applicable T disposition." Inherited P9-2, Counts and weighting, line 518 fixes additional required equivalence/twin match executions at **0**. Existing qualification plus exact artifact binding supplies those obligations. R2 accepts that retained synthetic boundary and does not require new matches. WSL filesystem probes are not arena matches. Therefore no new T execution artifact is required for this route. Existing evidenced historical qualification uses must still be inventoried; NOT_APPLICABLE is not proof of no prior use.

The formal mechanism is the frozen catalogue's `O.dependencies` together with `common.absent_records`, as implemented by unchanged `records.py:_T_disposition`: `O.body.custodian_attestation.T_disposition` has exactly `actor`, `disposition`, `evidence`, `reason`; actor role must be `research_lead`, decision `NOT_APPLICABLE`, and evidence an exact ArtifactRef. No standalone T waiver record/schema is invented. The eventual O must carry the stage-bound determination and read back its exact evidence, not merely shape-check a digest. Q, study/actor binding and O's exact inputs are pending, so this supported route is not represented as an already issued formal determination.

## D. O

**O: ABSENT; identity/hash: none.** Frozen role is `bytefray.v6.e9.inventory_seal` v2, a custodian seal of exact K/E/L bytes, inspection boundary, complete E6/E8 inclusion, evidenced in-scope known use and separate conservative provenance. Inputs are P/I/Q and T if applicable, otherwise the explicit determination in section C. K count never selects or approves an inventory.

No private inventory was written. O cannot be created with missing Q or implicit study/actor/root bindings. This is a prerequisite stop, not a failed O or permission to create placeholders. No existing K/E/L was promoted.

## E. V

**V: ABSENT; identity/hash/result: none; independent inventory verification NOT PERFORMED.** It requires exact final O/P/I/Q plus all private bytes and provenance. A separate independent context must read O's actual bytes, reproduce membership/default/derivation/temporal/scope checks and list every unreproduced item. It must not repair O. The original qualification reviewer is not automatically a new inventory reviewer. No O exists, so no verifier was invoked and no independent receipt fabricated.

## F. K/E/L and inspection

**Operational candidate set: NOT MATERIALIZED; exact operational K/E/L identities/hashes: unavailable.** Read-only source metadata is insufficient to call it an exact private candidate set. The following are retained reference boundaries, not selected operational K:

| Existing artifact described by retained metadata | Recorded raw SHA-256 | Disposition |
| --- | --- | --- |
| Original candidate (157 entries) | `9b9ff94fef00b0cef329c421591006b3b98409d7b21e49f02fdec69ad8b7b103` | Unadopted historical candidate |
| Additive proposal (163 entries) | `2940fd95d2ddbcc70ded7ad96b6ea811582cc30d2a61f754a4fc6f564ce9eb99` | `UNAPPROVED_ADDITIVE_CANDIDATE` |

These hashes were read from preserved `preparation_record.json` and `historical_targeted_evidence_index.json`; the corresponding private candidate bytes were not freshly read back here. They are not newly verified operational identities. Neither count is an abstract lead choice. Full future inspection must retain every member's exact bytes/hash, source, P/I/study scope, inclusion or exclusion basis, E9 role, limitations, visibility, reversibility and boundary analysis. Preserve all 357 gap IDs and DEP-01-DEP-05; unresolved coverage remains explicit.

Objective verification in this task: baseline, I transport and bound Q inputs. Observation: retained candidate metadata exists and historical coverage remains incomplete. Residual risk: unknown historical-use set; provenance/membership do not prove exhaustive execution coverage. Lead judgment: exact inventory selection/approval and specific residual acceptance are still future decisions. No operational K/E/L inspection PASS or new blocking scientific defect is claimed. No missing member was created with scientific generation or REAL entropy.

## G. A recommendation

**A: ABSENT. Recommendation: defer the decision until exact K/E/L/O/V exist and independent V is complete.**

A's frozen body requires P/I/Q/O/V plus exact K/E/L ArtifactRefs and an approved scope retaining all limitation IDs. An exact proposed A cannot currently be encoded honestly: the required material is unavailable. No generic "current inventory" approval or placeholders are offered. After exact material exists, return the fully bound proposed A to the lead; do not write a final approval on the lead's behalf.

## H. R recommendation

**R: ABSENT. Recommendation: defer final risk acceptance and its exact proposed record until A and affected material exist.** Frozen R is mandatory on this C-LIMITED route; R0 and instrument acceptance do not replace it. Its dependencies are P/I/Q/O/V/A and exact K/E/L.

| Residual identifier | Affected material and nature | Origin / interpretation effect | Mitigation / rejection consequence |
| --- | --- | --- | --- |
| Preserved 357 gap IDs and DEP-01-DEP-05 | Future exact K/E/L/O/V/A; incomplete historical execution evidence | Inherited; unknown prior reuse can affect interpretation and disallows exhaustive non-reuse assurance | Include all evidenced known uses, preserve unresolved ledger, independent verification and late-history rules; rejection keeps study locked |
| Unknown-history size H | Future exact approved inventory and its narrowed assurance; no useful numeric bound, worst-case bound 1 | Inherited; risk cannot be replaced with a count or newly selected tolerance | Permanent frozen limitation and specific lead decision; rejection prevents generation authorization |

Future proposed R text must state the exact narrowed known-history assurance, preserved unresolved scope and **"H UNKNOWN; no useful numeric bound; only worst-case bound 1"**, bound to final A/O/V/K/E/L. This paragraph is a drafting requirement, not an exact proposed record or acceptance. S8-IQ-F1-F4 remain the already dispositioned instrument notes; this task does not silently turn them into new R acceptances or claim they require fresh repair. Exact inspection may discover further residuals, which must be returned individually before proceeding.

## I. B readiness

**B: NOT READY; no candidate/final B record issued.** Catalogue B requires final P/I/Q/O/V/A/R. Final A/R are absent, so B cannot be finalized in this task.

The complete eventual checklist is:

1. Read and validate exact canonical P/I/Q/O/V/A/R, full body/recipe digests and raw RecordRefs; reject stale, mixed, revoked or changed inputs.
2. Independently reproduce exact K/E/L, full source/provenance/inspection evidence, complete E6/E8 inclusion and every limitation ID; verify formal T/NOT_APPLICABLE and all in-scope qualification accounting.
3. Read the exact materialized artifact manifest: 41 packages, 82 package files, 41 resolved defaults, full T8, logical aliases and source pins, against the current accepted P/I/Q boundary. Historical v1 artifact-binding metadata is context, not a v2 B substitute.
4. Verify no unaccounted intervening match use and all actual known uses; missing evidence is not evidence of non-use.
5. Verify exact current active authority tip, actor/resolver evidence and complete consistent state immediately before future G issuance. Do not fabricate a tip or initialize a log merely to make B shape-valid.
6. Preserve independent context/provenance and limitations. Any input drift reopens affected prerequisites; do not rewrite failed receipts.

No study package materialization or authority-log initialization was performed after the Q stop. Such deterministic preparation must use the approved private namespace and existing frozen factory; it must not execute matches or create experimental values. Source/test change would stop for disposition and potentially a new seal, not be included here.

## J. G readiness

**G: ABSENT; NOT READY; Gate 7 NOT AUTHORIZED.** Future G must bind one explicit study and unique generation operation, P/I/Q/O/V/A/R/B, exact materialized manifest, active tip, N=1412, frozen uint64 OS-CSPRNG/eight-byte big-endian sampling with exact K and duplicate rejection, accepted order and the durable boundary procedure.

R1 fixes the future endpoint: create/issue exact separately authorized G, record corresponding ISSUE, stop with G unused and inspectable. This task creates neither G nor ISSUE, does not register an original producer, and supplies no surrogate G record.

## K. Irreversibility

The next permitted work after clarification is still preparatory: final Q, formal T determination through exact O, exact inventory and independent V, then return exact A/R proposals. It is not a draw.

The later Gate-7 action is append-only G issuance plus ISSUE, requiring separate authorization after every prerequisite. **The first nonreplaceable producer-binding action after unused G is original producer registration**, which pins G/operation/root/actor. Constructing `Generator` performs it and is excluded. Later durable CONSUME is also nonreplaceable. The first scientific boundary is the durable first-raw marker/GenerationBoundary/draw intent immediately before the first `source(8)` REAL draw. Registration, CONSUME, marker, boundary, intent, draw, generated payload, W, salt, native execution and publication all remain excluded.

I transport and preparation evidence merely represent accepted inputs and provenance. They bind no producer, issue no operational authority and make no scientific sample irreversible. They remain write-once; future changes require additive records, not erasure.

## L. Decisions needed and return status

Only immediate missing context: **exact prospective study ID, approved private evidence namespace, and accountable custodian/research-lead actor IDs with their authority evidence**. The qualifier's retained identity/provenance is already bound. Do not ask the lead to reaccept R1/R2 or to authorize matches/source changes without a demonstrated need. After inventory preparation, exact A/R will require genuine later lead decisions; their bytes do not exist now.

The source of this stop is explicit in the accepted plan section M: "That root is unresolved here; inventing a seed-bearing path or issuing records to an implicit study would violate this plan." Section G and frozen common fields separately require explicit study/Actor evidence. This is a missing-binding stop, not an automatic approval-review rejection or a new scientific blocker.

| Required return item | Status |
| --- | --- |
| Baseline | PASS, exact required HEAD; fresh 329/329 plus 9/9 binding tests |
| Formal Q identity/hash/status | None / none / ABSENT; exact preparatory I and Q dossier above |
| T | NOT_APPLICABLE route supported; formal study-bound determination not recorded |
| O / V | ABSENT / ABSENT; no identity/hash or inventory verification result |
| Operational K/E/L / inspection | Not materialized or selected; no exact operational hashes/inspection PASS |
| Proposed A / R | Deferred for missing exact material; no final lead decision fabricated |
| B / G readiness | NOT READY / NOT READY |
| Next irreversible action | Future separately authorized G+ISSUE; subsequent first nonreplaceable producer binding is separately authorized registration |
| Gate 8 | **ESTABLISHED**; Seal 08 and independent reproduction PASS WITH FINDINGS |
| Gate 7 | **NOT AUTHORIZED** |
| Execution | **LOCKED** |
| Requirement C | **NOT ESTABLISHED** |
| G issuance / consumption | **NONE; G ABSENT** |
| REAL entropy / generation / operational W / salt / native execution / publication | **NONE OCCURRED** |
| Source/test/seal modification / commit / push | **NONE** |

Expected Git change set is this new document and four new preparation/I JSON files, all untracked; the two entry untracked items remain. Tracked tree and index remain clean. No private evidence root was created, no private values/paths were copied into these outputs, and local-only settings remain untouched. Final readback verification is required before returning these artifacts.
