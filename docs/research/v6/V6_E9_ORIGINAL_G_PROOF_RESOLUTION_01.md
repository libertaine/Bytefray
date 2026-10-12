# Bytefray V6 E9 — Original-G Historical Proof Resolution 01

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**Determination: HISTORICAL PROOF NOT ESTABLISHED.** No already-existing,
independently trustworthy evidence establishes the complete pre-first-draw timing
and no-earlier-invocation requirements for the original consumed G. The decisive
failure is P5. No retained source independently observed, confined or durably
recorded this study's entropy-capable execution over any part of the required
historical interval, including the narrowest interval anyone could argue for. P3
and P4 concern an event that has not occurred, so historical evidence cannot
satisfy them. P1 and P2 are established only at the level of identity and recorded
state.

This is a read-only evidence-sufficiency assessment. It is **not** a scientific
result, **not** evidence that an earlier draw occurred, **not** an instrument failure
and **not** a protocol amendment. Seal 08 remains accepted. G remains consumed exactly
once at T2. Execution remains **LOCKED**; Requirement C remains **NOT ESTABLISHED**.

## A. Baseline and existing G status

### Research-lead ruling applied

The lead accepted the adversarial review classification **NOT OPERATIONALLY PROVABLE**
for the proposed candidate and the original-G evidence then available
([design](V6_E9_OPERATIONAL_TIMING_PROCEDURE_DESIGN_01.md),
[review](V6_E9_OPERATIONAL_TIMING_PROCEDURE_DESIGN_REVIEW_01.md)). That classification
is not an instrument failure. The proposed Windows debugger gate is **not authorized**
for implementation. This assessment answers one question:

> Does any already-existing independently trustworthy evidence establish the complete
> pre-first-draw timing and no-earlier-invocation requirements for the original consumed G?

It uses only material that existed before the relevant events or was retained at the
time they happened. No prospective evidence was created and presented as historical proof.

### Fresh integrity verification

The audit finished shortly before 2026-10-09 12:38 −04:00 (local clock; administrative
only). It used the
repository interpreter, non-elevated, with `-B`/`PYTHONDONTWRITEBYTECODE`, so no bytecode
was written. `os.urandom` and `os.getrandom` were replaced with denying, counting stubs
**before** any repository import. The audit imported only the frozen `records`,
`authority` (`pinned_source_checker`) and `adoption` readers. It did not import
`generation`, did not construct Generator or AuthorityLog, took no lock, entered no
protected action and wrote nothing under the repository or the private root.

The procedure is the retained design-completion audit (`completion_audit_procedure.txt`,
6487 bytes, raw `2c5478e118db0f89fd4361cd7ba45e1c4ac1330042f4bb274c1b4cf80b2e8d6e`) plus
these checks:

- raw pins for G, Disposition 09, CONSUME and the producer registry;
- the first-raw directory is absent;
- no boundary, `draw-*`, salt-intent, salt, audit, payload or receipt filename exists
  anywhere in the private root;
- the design-administration file set equals its completion provenance;
- the total private file count is exact.

The script is 8423 bytes, raw `508cda88f9c4d4dc5370ab76fad284d7480ff16c12bd8695fb13a1806bf253f8`.
Its output is raw `b2dfab2626a785c58fd67865fa7650d719e840839aa3291fc5f9a6bb044362c7`.
Both are held in this session's scratchpad. They were deliberately **not** added to the
private root, because this task forbids changing existing records. They are
administrative receipts, not timing evidence.

| Check | Result |
| --- | --- |
| Branch / HEAD / upstream / live remote | `v6-research` / `569cb9aa15eaf40f4e870840e16fe99b7e40b47b`, identical on all four; ahead/behind 0/0 |
| Tracked tree / index | Empty diffs; inherited untracked work untouched |
| Seal 08 | **329/329 unchanged** (293 implementation + 36 qualification; both manifest raw pins) |
| Preservation (AR/B map) | **1607/1607 unchanged** |
| Inherited private evidence (multi-draw 01 entry map) | **1362/1362 unchanged** |
| Original private evidence (design entry census, raw `a6dd9efb…3432`) | **1374/1374 unchanged**; current set outside design administration is exactly equal |
| Design administration (10 files) | 9 match completion provenance; `completion_provenance.json` present (2522 bytes, raw `ee357b566d79ba525984dc610e71cf7777836b5687ecd1e0c3021fe0e9f1c668`; no earlier record binds it). Total private files **1384** = 1374 + 10 |
| Public entry files / design documents / local-only receipt | 1638/1638; both design documents match completion provenance; 1/1 |
| P/I/Q/O/V/A/R/B/G | Exact RecordRefs reproduced and validated; pinned sources and adoption review verified |
| Authority | ISSUE → ISSUE → CONSUME; sequences 1–3 from genesis; **exactly one CONSUME**; active tip **T2**; no `exclusive.lock` |
| Producer | One registry (raw `d0349b69…e548`); original G and operation; producer root exists, **empty** |
| First-raw marker / retained copy | **ABSENT / ABSENT** (no first-raw directory) |
| Boundary / intents / audits / salt / package / W | **ABSENT** |
| This audit's research entropy calls / attempts | **0 / 0**; generation not imported |

### Existing G status and record order

Hash dependency gives a real creation order: a record that binds another record's
digest was created after those bytes existed. That order holds only **among records**.
It cannot place a record relative to an execution that left no record. Local
modification times and embedded `recorded_at_utc` strings are local assertions,
written by the same producing context. They are shown below only to locate intervals,
and are not evidence.

| # | Event | Identity (raw SHA-256 unless noted) | Local metadata only |
| ---: | --- | --- | --- |
| 1 | Study identity first appears in a retained repository artifact | `V6_E9_IDENTITY_AUTHORITY_BINDINGS_01.md` (planning) | 2026-10-08 20:11 |
| 2 | Identity/authority declaration (bound by G as actor evidence) | `v2_identity_authority_declaration_01.json`, 17369 B, `769e7784…e700` | 20:33 |
| 3 | O sealed; V PASS; A approved; R accepted | O `59f70171…`, V `81de4da3…`, A `b709a9fd…`, R `27c03763…` | 20:54–21:39 |
| 4 | Event 1 ISSUE (genesis; tuple P–R), **T0** | 4999 B, `907d4d5d3ea551c0e42a1b58c7f950e46b987bc6c9f689882d5e3bc6379087a4`; T0 `f0da08f5…c986` | 21:43 |
| 5 | B independent verification PASS; B record | B `411c227e…`, body `434684981dbc…` | 2026-10-08 22:04 (report) / 2026-10-09 08:45 (record) |
| 6 | G issued; event 2 ISSUE, **T1** | G 5376 B, `21723c6d…b6a8`; event 6503 B, `a2bc466c59843729915bd006431caa149818943b764563c5eaf6a246e4727020`; T1 `50fe7d74…16d0` | 09:13 |
| 7 | Original producer registered | Registry 3331 B, `d0349b6938407587cac73d14c09507e52017543324ff65965abbf084be39e548` | 09:55 (`13:55:34Z` string) |
| 8 | Event 3 CONSUME by recorder `v6-e9-producer-01`, **T2** | 6671 B, `6c1b60409a9ff29553821774418c5020eb3d6e10742cf1d17c49455b94e046e3`; T2 `765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485` | 10:24 (`14:24:32Z`) |
| 9 | First-raw return 01: stop before entropy | `first_raw_generation_01/` (5 files) | 10:40–10:45 |
| 10 | Multi-draw return 01: stop before entropy | `multi_draw_generation_01/` (5 files) | 10:57–11:01 |
| 11 | Multi-draw return 02; Disposition 09; Phase A UNAVAILABLE | `multi_draw_generation_02/` (7 files); Disposition 09 6249 B, `53261258…64b5` | 11:12–11:19 (`15:19:53Z`) |
| 12 | Timing plan; design 01; independent review 01 | `timing_procedure_design_01/` (10 files); review `c5ac6ff5…bb8` | 11:44–12:08 |
| 13 | This assessment | This document only | 2026-10-09, after item 12 |

| Item | State |
| --- | --- |
| Instrument | `v6-e9-instrument-v2-3c692f23d2d9` (Seal 08), ACCEPTED |
| G | `v6-e9-generation-authorization-v2-0ea6d2043fbd`, body `0ea6d2043fbd7619ea724da15b6a4e106ffeaa3c929b43b9bcb3ff354c668175`; **CONSUMED exactly once** |
| Producer / authority | REGISTERED, empty root / **T2**, epoch 0, sequence 3, unheld, unrevoked, nonterminal |
| REAL entropy calls / attempts in retained execution evidence | 0 / 0 (counting boundary in D) |
| Marker / transcript / salt / package / W | ABSENT |
| Timing prerequisite / Execution / Requirement C | UNAVAILABLE / **LOCKED** / **NOT ESTABLISHED** |

## B. Frozen proof obligations

The governing sources are:

- adopted P `v6-e9-prereg-v2-539a60806eab` and its pinned
  [rule contract](V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md) and
  [catalogue](../../../tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json);
- inherited [Draft 3](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md);
- the original G `body.boundary_procedure` and `body.sampling`;
- Disposition 09 `rulings.timing`.

Disposition 09 is binding operational direction. It is not a change to P.

| Obligation | Governing clauses | Minimum evidence | Required trust properties |
| --- | --- | --- | --- |
| **P1** Original operation and consumed-G identity | R9 (G binds B and the declared procedure; reuse for another operation rejects); rule text line 391, "Required versioned records and encoding" ("Consuming G is durable and single-operation"); catalogue `GenerationBoundary.dependencies` ("existing tuple through G") and `operation_id` ("G operation"); RecordRef rules (full digests decide identity); `authority.py:752–755` | Exact RecordRefs P–G; a single CONSUME binding the original G, operation and producer registry; registry binding the same G, operation, root and recorder | Byte integrity and repeatable canonical digests; identified actors with authority evidence. **No temporal authenticity** is needed for identity itself |
| **P2** Verified inventory and authority state | PG-R3 (complete pre-generation state independently verified and separately authorized); PG-R4 ("after the active inventory gate is sealed and verified"); R4–R8; catalogue acceptance ("verified inventory/authority before first raw draw"); G (verify full tuple, K/E/L, sources, unheld/unrevoked chain before any raw draw) | O sealed; V and B PASS by identified independent verifiers; A/R lead records; T0→T1→T2 unheld and unrevoked; re-check at entry under the authority lock | `common.independence` (verifier independent of production; reproduces bound inputs); fresh re-check at the protected action |
| **P3** Durable boundary evidence in the required window | PG-R4 ("durably recorded instant immediately before the first experimental raw draw"); catalogue `durable_instant` = "trustworthy pre-first-raw-draw evidence", acceptance "Durable write … before first raw draw; uncertain ordering is a hold"; G ("Independently verifiable trustworthy pre-first-raw-draw instant evidence is mandatory"; ordered marker → source → boundary → intent inside the protected action); Disposition 09 (evidence and independent PASS before **marker creation** or any entropy; no local timestamp, no retroactive construction) | Qualifying evidence and an independent Phase-A PASS, both after CONSUME and before the marker; then the actual durable GenerationBoundary immediately before `os.urandom(8)` | Independently verifiable, trustworthy (not supplied by the recorder), durable, verified before the marker; never backdated |
| **P4** Boundary precedes the first entropy invocation | PG-R4 ("immediately before"); catalogue ("uncertain ordering is a hold"); G (ordering ambiguity stops without redraw or backdating); contract overlap evidence ("a trustworthy recorded execution boundary establishes use strictly before generation"; "Simultaneous/uncertain temporal ordering stays suspected"); Disposition 09 ("independently verifiable … ordering evidence") | Independent evidence that the actual invocation (`generation.py:196–197`) began only after the durable boundary and intent; no bypass route | Independent of the recorder; covers the actual invocation, not returned bytes; ordering comparable with historical-use timing for PG-R4 classification |
| **P5** No earlier raw invocation | Entailed by PG-R4 and the catalogue ("**first** experimental raw draw"; positions "in this study"), together with G ("independently verifiable … pre-first-raw-draw"; "without redraw, replacement or backdating"), PG-R5 (no redraw, replacement or restart), Draft 3 (no discretionary redraw after exposure), PG-R7 ("Missing evidence SHALL NOT be treated as non-overlap") and Disposition 09 | Evidence covering the whole interval defined below: either independent observation of every relevant acquisition route, or independent enforcement that made the routes unable to acquire study entropy | Independent of the producing context; complete over routes and time; durable and tamper-evident; contemporaneous, not reconstructed; binds study, operation, G and producer |

No frozen sentence states P5 as a separate duty. It is entailed. Evidence cannot verify
that a boundary precedes the *first* experimental raw draw without also verifying that
no experimental raw draw of this study came before it. This matches claim 5 of the
accepted [resolution plan](V6_E9_TIMING_EVIDENCE_RESOLUTION_PLAN_01.md).

### How far back P5 must extend

The frozen text fixes three things:

1. **The object is identity-defined.** It is any invocation that was, could have
   become, or could have been discarded in favour of an experimental raw draw of
   `v6-e9-study-01` / `v6-e9-generation-01`. The route is irrelevant: authorized or
   not, sealed path or not.
2. **There is no truncation at an authorization event.** Draft 3 ("After the later
   authorization boundary"), PG-R3, G and `_check` (`authority.py:752–755`) say when
   draws are *permitted*. None says earlier unauthorized draws need not be excluded.
   Treating authorization order as proof would make missing evidence exonerating.
   That contradicts PG-R7, the catalogue's hold rule and G's
   "absent or ambiguous temporal/ordering evidence prevents the first draw".
   Starting coverage at CONSUME, G ISSUE, producer registration, or the design's
   "earliest possible authorized acquisition" (design §F step 3) therefore
   **narrows** the requirement without frozen authority. TD-R01 reached the same
   conclusion independently.
3. **There is no extension beyond this study.** PG-R4 scopes positions to "this
   study". None of the following is an experimental raw draw of this study:
   - interpreter hash seeds and OS-internal randomness;
   - draws by other studies;
   - v1 E9 and E8 qualification history.

   Demanding proof about them **broadens** the requirement without frozen authority.
   Bytes obtained before the study existed could reach study positions only by
   substitution. That is a P1/P4 binding and instrument-integrity question, which
   REAL mode's rejection of injected streams addresses (`generation.py:49–50`). It is
   not an "earlier draw".

**Resulting extent (derived from the frozen text; the lead may strike it):** P5 must
cover the continuous interval from the **first existence of the study identity
`v6-e9-study-01`** to the actual first source invocation. Its earliest point is no later
than order item 1 above, the earliest retained repository artifact naming the study. The
authority-bearing declaration (item 2) follows it. Earlier mentions in AI conversation
logs, if any, could only move the anchor earlier. Their contents were not inspected
because the decision does not depend on them. No trustworthy time exists for any of
these points, so the anchor is defined by **event**, not by clock. The historical part
runs from that event to this assessment. The rest is prospective and remains open.

The determination does not depend on which anchor is chosen:

| Candidate anchor (earliest → narrowest) | Frozen standing | Independent coverage from the anchor to now |
| --- | --- | --- |
| P adoption | Broadens (pre-study) | None |
| **Study identity (derived anchor)** | Supported by PG-R4 "this study" | **None** |
| O sealed (K fixed) | Narrows (authorization/inventory event) | None |
| T0 / T1 / registration | Narrows (authorization events) | None |
| T2 CONSUME | Narrows (authorization event; design step 3, rejected by TD-R01) | None. Even this interval contains unguarded time between processes and an unguarded process (D) |
| Start of this assessment | Not a candidate; included to bound the analysis | None. No observer existed then either |

## C. Historical evidence inventory

Every candidate source found is listed. "Custodian" means a trust source independent
of the producing context. Unless stated otherwise, the producing context is the series
of Codex root contexts that executed the study steps, on this host and user account.

| ID | Source | Original creation time provable? | Current identity | Independent custodian | Scope of observation | Retention chain |
| --- | --- | --- | --- | --- | --- | --- |
| E-01 | G record and event 2 (G ISSUE) | No; hash order only (after B, before CONSUME) | G `21723c6d…b6a8`; event 2 `a2bc466c…7020` | None; local untracked or ignored files; never pushed | Records an authorization decision | Single local copy; re-hashed in several later returns (local) |
| E-02 | Event 3 (original CONSUME) | No; hash order only (after G and registry) | `6c1b6040…46e3`; T2 `765e7f44…3485` | None (local, ignored) | Records consumption by the recorder | Single local copy; pinned by Disposition 09 and later local records |
| E-03 | Authority chain and `active.json` | No; events carry no clock field (`body` keys checked) | events 1–3 above; `active.json` 88 B, `9e763e46fa1f221e1fcbaf6a302b2d2dab63d87ac81281019f37ba8f034a1beb` | None | Sequence and prior-tip chain of appended events | Local only; 1200 retained evidence copies, all local |
| E-04 | Producer registry and empty producer root | No | Registry `d0349b69…e548`; root empty | None | Registration state; emptiness at each inspection instant | Local only |
| E-05 | Retained guarded process records: `g_consume_01/` (procedure 27409 B, `97ceaf75e7bc04d43f95f2154dac7e4ff51399f66536693553c3a7979e0b1651`); first-raw 01 (procedure `72b38976…`); multi-draw 01 (procedure `c8b1396a…`); multi-draw 02 (procedure `a82ac815…`); design audits (`2091d1e6…`, `2c5478e1…`) | No | Raw hashes as given; counts 0/0 in each recorded output | None. Written and reported by the producing context | In-process Python stubs on `os.urandom`/`os.getrandom`, each process's own lifetime only | Local only; later returns re-hash earlier receipts (local) |
| E-06 | Producer-registration process record (`registration_verification.json`, 10814 B, `0b0756f50a7e2573255bae4a2a130d93f6bafa01381292ca663f95279dd03f76`; `pre_registration_review.json`) | No | As given | None | A **method statement** ("no … entropy source … invoked"). No retained guard procedure or attempt counter | Local only |
| E-07 | Five retained private-root census maps (pre-consumption 1351, first-raw 1357, multi-draw 01 1362, multi-draw 02 1367, design entry 1374 files) plus two full-equality verifications (design completion, this audit) | No | e.g. design entry census `a6dd9efb…3432`; multi-draw 02 baseline `326ffda4…f6b5` | None | File set and bytes **at each census instant** | Local; each census checks the previous one |
| E-08 | Independent AI inspections: V and B verifiers; Phase-A timing review (14772 B, `f51ec6c8…2800`); design review (`c5ac6ff5…bb8`) | No | As given | Separate AI contexts, not event observers. Disposition 09: AI endorsement is insufficient | Reading of retained records and source | Local reports |
| E-09 | Native Windows audit facilities (configuration inspected read-only, non-elevated) | Log retention windows: Windows PowerShell/Operational from 2025-05-24; PowerShellCore/Operational from 2026-09-29; Defender/Operational from 2026-02-01; CodeIntegrity/Operational from 2025-02-17 (event-log timestamps) | No Sysmon service; Defender for Endpoint sensor (`Sense`) stopped, manual start; AppLocker logs empty; no PowerShell script-block, module or transcription policy configured (177 PowerShell 7 event-4104 script-block records since 2026-10-08 exist anyway; contents not exported); Security log and audit policy unreadable without elevation; **NTFS change journal on D: not active**; Crypto-DPAPI log covers DPAPI only | OS Event Log service, local and administrator-clearable | PowerShell script compilation, Defender detections, image-signing events. **None observes Python-level or BCrypt RNG invocations** | Circular local logs; no export retained |
| E-10 | Codex rollout logs (AI conversation logs) | No; local file metadata only | 2026-10-08: 20 files, 20,893,619 B; 2026-10-09: 20 files, 12,233,232 B (aggregates over sorted `name\tsha256` lines: `6d043e2e…1452`, `bcacad46…557d`, current bytes) | None. Produced by the AI system whose actions are in question | Commands and outputs issued by those agent sessions | Local, mutable; no earlier record binds them |
| E-11 | Claude Code transcripts for this project | n/a | None spans the study interval. The last earlier session wrote at 2026-10-08 14:58, before the study identity; the only later one is this assessment | None | — | — |
| E-12 | GitHub remote `origin/v6-research` | Commit dates are author-asserted; server push records were neither retained nor consulted | `569cb9aa…` (2026-10-08 15:30 −04:00 commit) | **Yes, but only for public bytes** | Committed P, catalogue, Seal-08 manifests and source. **No file naming `v6-e9-study-01` is committed**; I-identity 08, G, Disposition 09 and the private root are local only | External |
| E-13 | Out-of-checkout private-evidence backups | n/a | Latest backup directory 2026-10-08 14:55 (Seal-08 transcripts); **no backup of the v2 study root exists** | n/a | — | — |
| E-14 | Filesystem timestamps and embedded `recorded_at_utc` strings | No | — | None | Local clock assertions | Mutable |
| E-15 | External timestamp tokens, signed receipts, witness logs or attestations | — | **None exists** (the plan's census found no `.tsr/.tst/.p7s/.pem/.crt/.cer`; none was created since) | — | — | — |

## D. Evidence trust and coverage

The eight tests from the task brief, applied to each candidate. **Y** = established from
retained evidence; **P** = partial or bounded; **N** = not established; **—** = not
applicable. Nothing is inferred from the fact that monitoring *could have* been enabled.

| ID | 1 Active before anchor | 2 Observed the entropy-capable boundary | 3 All invocation paths | 4 No way around its boundary | 5 Durable and independently verifiable | 6 Missing or altered observations detectable | 7 Binds G, producer, operation | 8 Order without retroactive assumption |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E-01–E-03 | N | N | N | N | P (reproducible digests; local, recorder-produced) | P (chain detects edits to bound bytes, not a consistent rewrite or unrecorded activity) | **Y** | P (creation order among records only) |
| E-04 | N | N (state, not execution) | N | N | P | P | **Y** | N |
| E-05 | N (no process ran continuously) | P (own process, two Python attributes) | N | N (other processes, ctypes/native, captured aliases, gaps between processes) | N (self-reported) | N | P | N |
| E-06 | N | N | N | N | N | N | P | N |
| E-07 | N | N (snapshots) | N | N | P | P (changes between census instants; not erase-and-restore between them) | P | N |
| E-08 | N | N | N | N | P | N | P | N |
| E-09 | P (logs predate the anchor) | **N** | N | N | N (local, administrator-clearable) | N | N | P (within one log, local clock) |
| E-10 | P (sessions started earlier, not continuous) | N (records agent text, not API calls) | N | N (user shells, other tools, other processes) | N | N | P | N |
| E-11, E-13, E-15 | — | — | — | — | — | — | — | — |
| E-12 | Y | N | N | N | Y for public bytes only | Y for public bytes only | **N** (no study record committed) | N for private events |
| E-14 | N | N | N | N | N | N | N | N |

**No candidate passes tests 2–4.** Without them, nothing can establish P5 whatever its
durability. E-12 is the only independent custodian, and it holds no study-specific
record. The inactive change journal on D: means no kernel-maintained file-change
history exists for the private root. Even a file-level trace of an erased marker,
boundary or audit is therefore unavailable. Each guarded process could observe only
itself. Nothing at all observed the time between processes or the registration process.

### Distinguishing the negative claims (task §7)

| Claim | Status | Basis | Limits |
| --- | --- | --- | --- |
| 1. No entropy call **recorded** | **ESTABLISHED for the retained study record** | No marker or copy, boundary, intent, audit, salt, payload or receipt; producer root empty; five successive census maps and two later equality verifications agree; every retained guarded procedure reports 0 | These are the records the sealed path *would* write. An invocation outside that path, or one whose traces were removed between censuses, leaves no record. The records are recorder-produced and locally held |
| 2. No entropy call **observed** | **PARTIAL; self-reported; process-local** | E-05 stubs were installed before repository imports and counted 0 attempts | Covers only each guarded process's lifetime and those two Python attributes. Does not cover E-06, the gaps between processes, other processes, `ctypes`/native BCrypt calls, aliases bound before patching, or the hours between T0 and T1 |
| 3. No entropy call **possible** outside the observed boundary | **NOT ESTABLISHED** | No access-control, confinement or enforcement record for the study root or the entropy APIs; no OS observer (E-09) | Every process on the host could call `os.urandom`, and administrator access was unbounded |
| 4. **Independently verified absence** of an earlier raw invocation | **NOT ESTABLISHED** | Needs claim 3 plus independent, durable, complete observation | E-08 re-read records; it observed no execution |

The phrase "REAL entropy calls/attempts: 0/0 in the retained execution evidence" is the
sum of per-process counters from E-05. Its counting boundary is two Python module
attributes, inside processes started by the producing context, for their lifetimes
only. No independent party established that boundary or its completeness. It supports
claim 1, contributes to claim 2, and **does not satisfy P5**.

Two histories therefore remain consistent with every retained byte, as TD-R01 described:

- no study acquisition has occurred; or
- an earlier out-of-band acquisition occurred and its bytes were discarded or kept
  outside the producer root.

No retained evidence distinguishes them. That is an absence of proof. It is **not**
evidence that a draw occurred.

## E. P1–P5 sufficiency matrix

| Obligation | Existing evidence | Trust achieved | Status | Can historical evidence ever satisfy it? |
| --- | --- | --- | --- | --- |
| P1 Identity | E-01–E-04; fresh RecordRef and raw reproduction (A) | Repeatable canonical identity; local custody, no external anchor (E-12 holds no study record) | **ESTABLISHED (identity only)** | Yes. Identity needs no trusted time |
| P2 Verified state | V and B independent PASS; T0→T1→T2 verified now; Gate 7 and producer verified | `common.independence` satisfied for V and B as recorded. The at-entry re-check is the sealed protected-action check, which is prospective | **ESTABLISHED (retained state at T2)**; the at-entry re-check stays prospective | Partly. The state can be; the re-check at the boundary cannot |
| P3 Durable boundary in the window | None: no evidence, no Phase-A PASS, no boundary | — | **NOT ESTABLISHED** | **No.** The boundary has not occurred, and Disposition 09 forbids retroactive construction |
| P4 Boundary before invocation | Reviewed program order only (`generation.py:177–197`) | Code review shows the order of the reviewed path, not what a process executed (plan §H) | **NOT ESTABLISHED** | **No.** It concerns a future invocation |
| P5 No earlier invocation | Claim 1 established; claim 2 partial | No independent observation or confinement of any interval from any anchor (B, D) | **NOT ESTABLISHED** | In principle, only if independent coverage had existed from the anchor. **None did** |

Even a sufficient historical P5 could not have produced HISTORICAL PROOF SUFFICIENT
for the full P1–P5 obligation. P3 and P4 need evidence created at and before the
future boundary. Historical P5 was the one component that existing evidence *could*
have closed. It did not.

## F. Reconciliation of the eight adversarial findings

Each finding was checked against the inventory above, not taken on the review's word.
None is resolved here.

| Finding | Failed or unestablished obligation | Existing evidence able to resolve it | Prevents use of original G? | Only the proposed controller? | Affects a future prospective study? |
| --- | --- | --- | --- | --- | --- |
| **TD-R01** BLOCKER: historical P5 cannot come from a new observer | P5 (historical) | **None** (C, D) | **Yes. Decisive, and unresolvable without new qualifying *historical* evidence, which the inventory did not find** | No. It is about original-G history whatever the mechanism | Only in form: a future study can avoid the gap by establishing coverage *before* its anchor |
| **TD-R02** HIGH: invocation gate is conditional and outside Seal 08 | P4, plus the P3 link | None. Seal-08 synthetic fixtures do not qualify a native gate | Yes, independently, but it is a prospective obligation and moot behind TD-R01 | The native mapping is specific to the debugger; the underlying P4 duty applies to any mechanism | Yes. Any future gate needs qualified evidence that it acts before invocation |
| **TD-R03** HIGH: study access and acquisition routes unconfined | P5 (historical and prospective); P4 no-bypass | **None.** No confinement records; E-09 does not observe; change journal inactive | Yes. The historical routes were unconfined, which is the same fact behind TD-R01 | No | Yes. Route census and enforced study-access policy are needed from the anchor |
| **TD-R04** HIGH: pre-marker evidence semantics | P3 (Disposition 09 Phase A before marker) | None. No pre-marker evidence exists | Yes, as a separate unmet prospective obligation. It is not shown to need an amendment | The split certificate is candidate-specific; the duty is general | Yes. Fix the evidence semantics before the study begins |
| **TD-R05** HIGH: no supplier for witness trust, durability, comparability | P3/P4 trust; P5 and PG-R4 comparable ordering | **None** (E-15 absent; E-12 holds no study record) | Yes, prospectively | No. It applies to any witness design | Yes. Appoint custodian, trust roots and retention contract before the anchor |
| **TD-R06** MEDIUM: paused lock and observer exit | P4 feasibility (stopped target holds `exclusive.lock`; `authority.py:789–804`) | n/a (implementation contract) | Not independently decisive | **Yes**, for stopped-process gates | Only if the future design uses a stopped-process gate |
| **TD-R07** HIGH: unchanged files do not prove consumed-G compatibility | P1 compatibility under R2/R8/R9 | Seal-08 I/Q, B and G certify the boundary *without* a controller; nothing certifies a controller | Yes, for any controller-based route | Yes, for execution-controlling designs | Resolved by design: a future study binds its controller into its own I/Q from the start |
| **TD-R08** MEDIUM: source anchors and tooling | None. Navigation (corrected in the design) plus a P4 feasibility note | n/a | No | **Yes** | Feasibility check only |

TD-R01 and TD-R03 are the historical findings that existing evidence could
conceivably have resolved, and the inventory resolves neither. The others are
prospective. They do not count as resolved merely because parts of the design are
sound (the conditional causal proof in review §"Conditional proof").

## G. Original-G compatibility

No sufficient evidence was found, so this section is conditional and mostly moot.

- **If** qualifying retained historical evidence for P5 had existed, binding it would
  have been an *evidence input*. G already declares that independently verifiable
  evidence is mandatory. The evidence could have been bound forward through the
  existing `durable_instant` field. That field accepts generic JSON, and the design
  proposed using it for opaque PRIVATE ArtifactRefs. None of the following would
  have changed:
  - the G identity or the CONSUME (`authority.py:752–755` expects the original G
    already consumed by this operation);
  - T2 and the producer registration;
  - the Seal-08 bytes;
  - the first-raw marker recipe and its semantics;
  - K/E/L or any scientific input.

  TD-R07 agrees that an external receipt supplying an already-declared input "is not
  automatically a new I".
- That conditional compatibility would not have extended to P3/P4 mechanisms. Any
  execution-controlling gate stays subject to TD-R07, and its I/Q/B/G impact is
  unestablished.
- **As found:** nothing exists to bind. No replacement G was issued, no CONSUME was
  repeated, no history was amended, and no record was rewritten. G remains preserved,
  consumed at T2, for its original operation only.

## H. Final proof determination

**HISTORICAL PROOF NOT ESTABLISHED.**

Consequences, as the decision rule requires:

1. The existing G stays **consumed exactly once at T2**. Authority, producer, Seal 08
   and every record are preserved unchanged.
2. The study stays **operationally blocked**: execution LOCKED, Phase A UNAVAILABLE.
3. No timing evidence was manufactured. None may be constructed for the past
   interval. Disposition 09 forbids retroactive construction, and new observation
   cannot cover time before it started.
4. The missing proof is **not** evidence that a draw occurred. There is no positive
   finding of an earlier invocation, and no FAIL or INTEGRITY_HOLD follows from this
   assessment.
5. The state is **not a scientific result**. No experimental claim, payoff or
   Requirement C eligibility follows.
6. **No further controller should be attempted for this G** unless new qualifying
   historical evidence appears. The inventory found no candidate that could become
   such evidence: none observed the boundary.

Recommendation: pursue study generation only through a **new, separately authorized
prospective study**, using the frozen protocol and authority process (J). Its
trustworthy boundary and observation coverage must exist **before its earliest
relevant operation**, not be added afterwards.

## I. Implications for prospective study design

These are minimum requirements, not a design. Nothing here authorizes design,
implementation or acquisition.

1. **Fix the P5 anchor first.** Name the event that starts the no-earlier-draw interval
   (section B's study-identity anchor or another one the lead fixes). Establish the
   independent observer and custodian **before** that event, so the interval is never
   unobserved.
2. **Confine every entropy-capable path.** Enumerate every route that could acquire or
   substitute study entropy: processes, threads, aliases, native calls, privileged
   principals. Enforce a bounded study-access policy whose lifetime and administration
   sit outside recorder control. Recording a rule is not enforcing it.
3. **Durable boundary acknowledgment** from a separately administered custodian with a
   specified retention contract, independently controlled read-back, and verifiable
   acknowledgment *before* release. Local flush, fsync and read-back is not
   independent custody.
4. **Independently verifiable ordering** that covers the actual invocation, plus time
   or order comparable with historical match use for PG-R4 classification.
5. **Explicit no-earlier-draw coverage** from the anchor to the first invocation,
   under claim levels 3 and 4 of D, not only levels 1 and 2.
6. **Synthetic adversarial qualification** of the whole architecture under a fresh
   independent qualifier. Cover at least the design §J challenges, the TD-R06 cases
   and an undetected-earlier-invocation shadow case. Use synthetic fixtures only, with
   OS entropy denied.
7. **Exact instrument and protocol impact.** An execution-controlling observer is
   operative implementation, so a new I/Q is required. Seal 08 does **not** cover a
   changed execution architecture. Separately determine whether fixing the P5 anchor
   and the pre-marker evidence semantics (TD-R04) can be procedural (B) or needs
   normative amendment (a new P). This assessment does not decide that.
8. **Separate study, authority and G decisions.** PG-R10 requires, "after
   cancellation or invalidation":
   - a new prospective study identity;
   - an outcome-independent lead design decision;
   - a verified and newly approved inventory including all known prior values;
   - fresh risk acceptance;
   - separate generation, publication and payoff authorizations. Under the frozen
     order this means a new B and G, then a new producer registration and CONSUME.

   Prior observations must not select values, and the old study never resumes under
   the new identity.

## J. Exact research-lead decisions required

1. **Accept or reject** the determination HISTORICAL PROOF NOT ESTABLISHED.
2. **Confirm or strike** the derived P5 anchor (first existence of the study identity).
   The determination holds under every candidate anchor, so this matters for the
   record and for the future study, not for the outcome.
3. **Decide the disposition of the existing study and its consumed G.** G's
   `boundary_procedure` routes absent timing evidence to "lead disposition". There are
   two options:
   - **(a)** Keep it **BLOCKED**: G consumed at T2, execution LOCKED, reopened only
     by new qualifying historical evidence, which the inventory suggests does not
     exist.
   - **(b)** **Close it formally** through a frozen authority event. The frozen kinds
     include REVOKE and TERMINATE. However, none of the named terminal statuses
     (`CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP`,
     `…_LATE_HISTORY_OUTSIDE_APPROVED_K`, `…_UNRESOLVED_INTEGRITY`) describes "timing
     prerequisite unavailable before first raw". The last is defined for unresolved
     overlap adjudication under PG-R7. Mapping this condition onto it, or onto any
     status, requires an explicit lead ruling, and amendment review if no frozen
     status applies. None is proposed or created here.
4. **Decide whether to authorize planning only** of a new prospective study under
   PG-R10. Because PG-R10 applies "after cancellation or invalidation", this depends
   on decision 3(b). Also decide whether the planning must first settle the B-or-C
   question in I.7.
5. **Confirm no controller work for this G.** The debugger gate is already ruled not
   authorized. No other controller, evidence acquisition, appointment or entropy
   request for the original G is sought.

This assessment authorizes none of these actions.

### Assessment provenance and boundary

This assessment was performed by Claude Code session `7a7b65bc` (model Claude Opus
5.5). That is a different model family and tool from the Codex contexts that produced
the operational records, but it shares their host, workspace and user account. It is
an evidence-sufficiency inspection. It is not an event observer, witness, appointed
Actor, operational verifier or timing PASS, and its separation supplies no clock or
observation authority.

The assessment read public and private records in place. It read native audit
configuration non-elevated: no event contents were exported, and the Security log
was not readable. It counted and hashed AI-log files without relying on their
contents. It used read-only `git` operations, including one live `ls-remote`.

| Final preserved state | Result |
| --- | --- |
| Seal 08 / preservation / inherited private / original private | 329/329 / 1607/1607 / 1362/1362 / 1374/1374 unchanged |
| G / CONSUME / authority | Consumed exactly once / one original event / T2 |
| Producer / first-raw marker / transcript | Registered, empty / ABSENT / ABSENT |
| Salt / generation package / W | ABSENT / ABSENT / ABSENT |
| REAL research entropy in this assessment | 0 calls / 0 attempts |
| Historical proof / timing prerequisite | **NOT ESTABLISHED** / UNAVAILABLE |
| Execution / Requirement C | **LOCKED** / **NOT ESTABLISHED** |

Only this document was added. No source, test, seal, authority record, private file,
producer registration, G issuance or consumption, timing evidence, attestation,
controller, marker, entropy, salt, W, native match, publication, commit or push
occurred. **STOP.**
