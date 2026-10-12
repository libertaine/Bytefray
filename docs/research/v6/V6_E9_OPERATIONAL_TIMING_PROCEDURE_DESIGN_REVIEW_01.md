# Bytefray V6 E9 — Independent Operational Timing Design Review 01

2026-10-09. Study `v6-e9-study-01`; operation `v6-e9-generation-01`.

**Overall result: NOT OPERATIONALLY PROVABLE.** This result applies to the exact
reviewed design and presently demonstrated evidence for the original consumed G.
It is not an impossibility theorem, a protocol amendment decision, an operational
timing verdict, or permission to implement or acquire evidence. Execution remains
**LOCKED**; Requirement C **NOT ESTABLISHED**.

The commissioned question was: “Can a conforming implementation of this design
independently demonstrate that this study's first raw invocation cannot precede
its valid, durably established timing evidence?” The answer on these inputs is
**no demonstrated conforming implementation**. The proposed all-thread debugger
stop offers a plausible conditional prospective gate. The design has not supplied
the historical coverage, exact runtime gate, independent custody and durable
service contract, accepted pre-marker evidence semantics, or I/Q/B/G compatibility
needed to turn that gate into the requested independent demonstration.

## Review provenance and boundary

Reviewer: fresh Codex context `/root/timing_design_reviewer`, commissioned without
an approval target and without inherited author conversation (`fork_turns=none`).
I independently read the actual design, adopted contract/catalogue, original G,
Disposition 09 and its retained lead ruling, timing resolution plan, and frozen
generation/authority/record validation sources. The author's negative assessment
was an assertion to check, not the review's premise. The review commission was
retained administratively by the root; it is not timing evidence.

This is a separate AI design inspection in the same model family and shared
workspace/tool environment as the author. It supplies no independent process or
historical event observation, human witness, external clock authority, operational
Actor appointment, or operational PASS. Source hashes demonstrate bytes inspected,
not the behavior of any past process. No tests, generation import/construction,
AuthorityLog construction, protected action, REAL research entropy request,
first-raw marker, salt, generator package, authority event, commit or push occurred
in this review. Only this report was written. Read-only web access checked primary
Windows documentation; it did not acquire an operational receipt or service.

PowerShell raw-byte hashes and read-only JSON inspection were used. I did not
reproduce the frozen Python canonical body-digest algorithms or the complete
329/1607/1362 preservation maps. The author's reported complete baseline remains
the author's evidence, not my independent reproduction. I verified the three
inspected sealed Python files against their exact I manifest entries, adopted P's
three contract-file raw pins, original G/Disposition 09 raw identities, and a
relevant private authority/producer subset. My entry branch was `v6-research`,
HEAD `569cb9aa15eaf40f4e870840e16fe99b7e40b47b`; tracked/index diffs were empty.
Inherited untracked files were preserved.

The private subset had three ordered event files, ISSUE → ISSUE → CONSUME, exactly
one CONSUME, with final recorded digest
`765e7f4471ab68b4b3f42102bcc07c6764d77fa2024898661cbd6fafca1e3485` (T2).
The original producer registry raw hash matched
`d0349b6938407587cac73d14c09507e52017543324ff65965abbf084be39e548`;
its original study/operation/G matched, its producer contained zero files,
the canonical first-raw marker was absent, and no authority lock was present.
These are bounded present-state observations, not proof that an out-of-band
historical call never occurred. Private locations, values and resolution maps are
not disclosed here.

## Findings retained

Severity describes impact on the requested proof. BLOCKER means the design cannot
currently earn the required timing result; HIGH identifies an unresolved necessary
mechanism or compatibility condition; MEDIUM identifies a material qualification
or interpretation issue. Missing proof is UNAVAILABLE, not an observed early draw.

### TD-R01 — BLOCKER: Historical P5 cannot be obtained from a new observer

Anchors: design lines 148–160, 245–251, 320, 399, 441; resolution plan lines
142–152; original G `body.boundary_procedure`; retained Disposition 09 ruling,
Phase A baseline and outcome; `generation.py:113–155`.

There are two histories consistent with the present empty producer, absent
marker, valid authority records and a clean observer started now: no previous
study acquisition, or an earlier out-of-band study acquisition whose bytes were
discarded or kept outside the original producer. Local source hashes and retained
denied-call counts do not distinguish those histories unless independent coverage
and custody delimit every relevant acquisition route over the earlier interval.
The current timing analysis explicitly records qualifying evidence ABSENT and
independent timing verification UNAVAILABLE; it is not such coverage.

The design appropriately stops at step 3. Merely adding the proposed debugger,
journal, signature or synthetic challenge results cannot make this step pass.
The lower bound “earliest possible authorized acquisition” must also be justified:
authorization order alone does not exclude an unauthorized earlier acquisition
that is relevant to this study's purported first raw. A future procedure needs an
explicit study-input provenance/eligibility boundary and independently authentic
historical coverage or enforcement basis. This concerns this study's first raw;
it must not silently expand into proof of every unrelated OS random byte, or be
confused with the separately accepted incomplete historical match-seed inventory.

Disposition: **UNAVAILABLE / LOCKED**. Earlier activity is not established either
way. Later authentic retained evidence might resolve the gap; neither automatic
cancellation nor a protocol amendment is proved necessary by missing evidence.

### TD-R02 — HIGH: The actual invocation gate is conditional and outside Seal 08

Anchors: design lines 102–110, 260–268, 284–297, 353–359;
`generation.py:164–197`; `authority.py:654–755,789–804`;
`records.py:367–373`; catalogue `records.GenerationBoundary`.

The frozen call authenticates authority and source-file bindings, writes/readbacks
marker, source declaration, boundary and intent, then invokes `source(8)`. Generic
non-null JSON validation for `durable_instant` neither resolves a timing source nor
verifies an independent PASS. No frozen callback tests V1 or V2, and the post-action
authority recheck occurs after the source could already have executed. This is an
operational input/verification obligation left to the surrounding procedure,
not grounds to repair frozen source during this review.

The proposed debugger could provide a genuine gate if an authenticated debug
event stops the actual callable dispatch and only the independent controller can
continue it. Windows documents suspension of all threads of the affected process
until continuation. That supports the conditional mechanism; it does not prove
the particular CPython frame, callable and native instruction mapping used by this
study. [Microsoft debugging events](https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events)

The native gate must precede invocation, not entry to BCryptGenRandom, entry inside
the Python callable, or return of eight bytes. Exact loaded images, code objects,
interpreter specialization/dispatch, thread lifecycle and callable identity need
a supported mapping and independent challenge evidence. A source line number or
breakpoint recipe alone cannot establish it. A controller that accepts signatures
and resumes the wrong stop has failed even if the local audit later looks valid.

Disposition: **gate not qualified**. A conditional prospective proof is possible
under the stated complete-custody assumptions; those assumptions are not supplied
as actual evidence or a complete implementation specification here.

### TD-R03 — HIGH: Study access and every acquisition route remain unconfined

Anchors: design lines 122–139, 170–196, 252–268, 442;
`generation.py:49–72,196–197,256–257`;
`authority.py:78–97,119–129,654–670`.

The two static direct source sites are accurately located: raw `source(8)` and
later salt `source(32)`. They do not enumerate Python/native aliases, previously
captured callables, imported code, callbacks, different process routes or direct
OS RNG access. REAL injection rejection constrains constructor parameters; it
does not attest the runtime `os.urandom` object or make entropy unavailable before
Generator exists. Manifest checks read source files; they do not establish every
loaded image or runtime object has those semantics.

An independently stopped target process does not stop an unrelated process with
study access. The procedure requires prohibition of other study producers, but
does not specify the principals, access controls, enforcement lifetime, administrator
custody or proof of non-use of separately acquired bytes. Calling those routes
“unauthorized” is a rule, not independent prevention or observation of them.
Observer/key administration must be outside recorder control; the shared kernel
and privileged-access trust boundary must be explicitly accepted and verified.

Disposition: **coverage/custody UNAVAILABLE**. A route census, enforced bounded
study-access policy and independent enforcement/observation evidence are needed
before prospective P5 or no-bypass P4 can pass.

### TD-R04 — HIGH: Pre-marker evidence semantics and amendment necessity

Anchors: design lines 269–291, 320–333, 379–385, 485–494, 531–534;
resolution plan lines 239–243, 279–288, 319–326;
PG-R3/PG-R4 at contract lines 100/102; catalogue
`records.GenerationBoundary.required_body_fields.durable_instant`;
Disposition 09 public summary lines 14–17 and retained ruling Phase A outcome.

V1 must be durably complete before marker creation. E1 and V2 are made after the
actual boundary/intent readbacks. A pre-marker C1 merely promising future coverage
is not already authentic proof of an occurred boundary; E1/V2 cannot be backdated
to cure missing V1 evidence or PASS. The proposed DI explicitly has not established
its meaning as the required trustworthy instant. This is a real unclosed conformity
obligation for this candidate.

However, the contract does not state that a verifier before marker must attest
that the not-yet-created boundary already exists. Nor does it forbid every
independently authenticated causal arrangement in which pre-existing trusted
evidence and a qualified enforceable procedure have a credible prospective link,
and later actual observation corroborates execution. The resolution plan itself
distinguishes these in lines 319–326. The hash direction C0→C1→V1→DI→boundary→E1
is acyclic; its defect is unestablished event semantics/authenticity, not a necessary
cryptographic self-reference. A receipt embedded inside the boundary that hashes
that same final boundary would instead be circular.

Accordingly, read “split ... has not been established” as candidate-specific
UNAVAILABLE. Design lines 379–385 and 531–534 must not be used to infer that every
split construction necessarily requires amendment. An explicit waiver of P5,
backdating, treating a bare promise as occurred evidence, or moving the mandatory
Phase-A PASS past marker would change the required claim/order. A valid alternative
causal evidence construction preserving those duties could still be procedural B;
none has been demonstrated in this review.

Disposition: **not established**, rather than **REQUIRES PROTOCOL AMENDMENT**.
This qualification does not make the proposed sequence executable.

### TD-R05 — HIGH: No specified supplier for witness trust and durability

Anchors: design lines 174–201, 278–287, 317–343, 361–377;
catalogue `common.independence`, `records.GenerationBoundary.acceptance_predicates`;
PG-R4 and contract lines 228–240 on independently established prior-use ordering.

A journal signing recorder-submitted bytes attests submission, not the actual
boundary or absence of prior calls. Even an authentic observer submission needs
independently sourced trust roots, observer provenance, authorized signers,
anti-equivocation and replay/session rules, durable acknowledgment semantics,
readback, private resolution and verifiable retention. The design names these
obligations but leaves service, custodians, keys and retention contract unappointed.
The claimed durability cannot be stronger than the actual accepted storage/service
guarantees. Local exclusive write/flush/fsync/readback is not independent custody.

There is a separate temporal-use requirement: a monotonic observer sequence can
prove its own causal order, but cannot order an unrelated historical execution
journal. A valid procedure must provide trustworthy comparable order or time
intervals when prior match-use classification needs that comparison. Pure observer
sequence numbers are not a complete replacement for this linkage.

Disposition: **source/trust/retention/comparability UNAVAILABLE**. Signatures are
one possible mechanism, not a substitute for observations and accepted trust scope.

### TD-R06 — MEDIUM: Paused-lock and observer-exit handling need specification

Anchors: design steps 7–8, failure rows 402–415;
`authority.py:132–145,645–652,789–804`;
`generation.py:170–197`.

At the proposed stopped pre-call dispatch the target is inside the exclusive
raw_draw action and holds `exclusive.lock`. A verifier that tries to re-enter the
public protected/exclusive authority path to prove “active authority recheck” will
fail or wait for the target it refuses to release. Similarly, a compliant formal
HOLD cannot append through that same lock while the target remains stopped. The
design needs a specific independent read-only stopped-state verification path,
lock/custody proof, abort behavior and separately authorized disposition sequence;
it cannot depend on recorder callbacks running in a stopped process.

Observer death also has concrete Windows behavior: the documented default kills
attached targets; an explicit different setting detaches them. The controller must
bind and verify this policy and exclude unsafe automatic continuation/detachment.
Target termination while inside the action can leave the durable lock, marker or
intent, so subsequent handling must preserve the frozen interrupted boundary and
never treat termination as permission to retry. [Microsoft DebugSetProcessKillOnExit](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-debugsetprocesskillonexit)

Disposition: **mandatory feasibility/qualification item**. This is not proof that
an external read-only verifier cannot be built; it is an unresolved implementation
and interruption contract that an ideal event model will not test.

### TD-R07 — HIGH: Unchanged file bytes do not establish consumed-G compatibility

Anchors: design lines 458–513; contract R2/R8/R9 at lines 140/146/147 and lines
372–375; catalogue I/Q predicates; original G dependencies;
`authority.py:78–97,400–471,752–755`.

The proposed controller controls whether scientific acquisition can occur. Its
route checks, runtime mapping and continuation algorithm may be operative
implementation even if outside `v2/` and even if all sealed Python files remain
unchanged. Complete I/Q coverage and certified operational/input effects need an
explicit decision. The old G binds old I/Q/B; new qualification or changed
certified preparation cannot silently inherit it. A future external observation
receipt supplying an already-declared input is not automatically a new I, but a
new execution controller cannot automatically be excluded either.

Consumption itself is not the blocker: frozen `_check` requires original G already
consumed by this exact operation. There is no basis here for a second CONSUME,
replacement G, re-registration, routine B edit, source callback insertion or
transfer of qualification. Seal 08 remains evidence for its original bytes.

Disposition: **I/Q/B/G impact unestablished**. Any changed boundary must return for
explicit scoped review and disposition before implementation or reliance.

### TD-R08 — MEDIUM: Source anchors and tooling feasibility

Anchors: design source table lines 101–112 and feasibility lines 305–310;
inspected `generation.py` and `authority.py` identities below.

Several draft source ranges are offset: actual marker call is generation line
177, source declaration 178–180, protected call 212–213, construction 40–72,
salt action 247–262, and protected authority method 789–804. The report uses these
actual anchors. Hash identity makes the intended source recoverable, so this is
an evidence-navigation defect rather than a source/binding mismatch.

My read-only PATH check did not find `cdb.exe`, `windbg.exe`, `WinDbgX.exe` or
`openssl.exe`; it found `ssh.exe`, `certutil.exe`, `wpr.exe` and `logman.exe`.
This does not prove a debugger cannot be installed or a native controller cannot
be implemented, and a stock debugger alone would not be an E9 observer anyway.
No deployed suitable observer/service was demonstrated. The Windows debug APIs
are a real mechanism, but current implementability of this exact study controller
and service remains unestablished. No installation or capability acquisition
occurred in the review.

Disposition: **documentary corrections and feasibility scope only**; no operative
implementation scope is ready to freeze from the present draft.

## Conditional proof and review decision

The useful constructive part survives adversarial review. Suppose independently
authentic historical coverage establishes no earlier study raw, every permissible
future study acquisition route is confined, actual source dispatch is stopped,
only an independent accountable controller can release it, and valid timing
evidence plus independent PASS are durably established before release. Then that
controlled source dispatch cannot precede the evidence: it cannot execute during
the stop and release depends on already established evidence. This causal proof
does not need a local UTC string. It remains conditional on exact runtime and
custody facts and accepted evidence meaning, not an actual timing verdict.

For this draft, historical coverage fails first, prospective confinement and
native gate mapping are unqualified, service/trust/durability are unspecified,
pre-marker evidence conformity is unresolved, and consumed-G compatibility is
not certified. Hence **NOT OPERATIONALLY PROVABLE**, rather than READY FOR SCOPE
REVIEW. No necessary normative amendment has yet been demonstrated. Waiving these
claims would require separate amendment review, and amendment would not make a
missing historical observation occur retroactively.

The appropriate next documentary decisions are whether independently authentic
retained historical evidence can close TD-R01; whether a precise causal evidence
interpretation preserves Phase A and PG-R4; and what complete runtime/custody,
observer/service, I/Q and B/G boundaries apply. If those cannot be established,
retain UNAVAILABLE and seek disposition of the preserved consumed G. This report
authorizes none of those future actions and creates no operational artifacts.

## Exact reviewed source identities

Raw SHA-256 binds actual file bytes, with no newline normalization. JSON paths
above are semantic locators because catalogue/G/disposition files are compact.
P's three contract-file pins and I's three inspected implementation pins matched
the following current raw bytes. Other rows identify reviewed inputs; they are
not a complete sealed-source or canonical-record qualification reproduction.

| Input | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `V6_E9_OPERATIONAL_TIMING_PROCEDURE_DESIGN_01.md` | 51455 | `4b53bea08d5cf78b4a3094782bf124aed4dba7ad2c1a5196c4f5bf546047eec3` |
| `V6_E9_TIMING_EVIDENCE_RESOLUTION_PLAN_01.md` | 39191 | `73ccf77620d0193f97b12c4d67a9ca54fc337922ce7968fb36d169fe1a1dac83` |
| `V6_E9_AMENDED_RULE_CONTRACT_V2_PROPOSED_02.md` | 95229 | `034758d520e8c9a597daacc06501ddd3de31824b4a102a5411c54879ee3ccbfe` |
| `amended_rule_contract_v2_proposed_02.json` | 108226 | `1c421891e54b9522a6b172ef2d4a5b61e484217b2789115ab954916618b5cc4a` |
| `amended_record_schemas_v2_proposed_02.json` | 26925 | `434635bdfa568050c3486c3ce936ae78ca67aef7a1112fb99a2a8a9c5144feff` |
| `protocol_freeze_v2_adopted_02.json` | 22974 | `63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4` |
| `protocol_adoption_attestation_v2_02.json` | 4475 | `3dc816fa66311a58c92e041ab5acc1b3ce0ec143ceb96ee348bc10b7df92628a` |
| `v2_generation_authorization_study_01.json` | 5376 | `21723c6dd1959479b484c3acf2c411d0fe380faa2f53b0885706548fd65bb6a8` |
| `v2_finding_disposition_09.json` | 6249 | `53261258982fb2c962f0176cda7a0368ed87c50a03ab8b9e7c472c675e2764b5` |
| `V6_E9_V2_FINDING_DISPOSITION_09.md` | 2269 | `407ee3076a3791181fa514d0200e2a54d381c7a6d13ff1afd9a29028852200f1` |
| `v2_identity_authority_declaration_01.json` | 17369 | `769e77844905be3fbda7b66fcde57482fedca30e008191fb8f6ca7e15541e700` |
| `v2_instrument_identity_08.json` | 34094 | `cbdc00bd767179b4353625f4fb10115ec9c45fdcbb01a8c19ced3c3fb2b48fd7` |
| `v2_instrument_qualification_study_01.json` | 78546 | `df9d3a286350404a22aa8c17d52b877bd3e93a80c246fb1d4cc16a7bb9eaa616` |
| `v2/generation.py` | 19378 | `5d61c5bafbf5b49d766418828f003bcb723f9e5fa4a81b4e0e5afd1b38d1d6e9` |
| `v2/authority.py` | 48676 | `8484e589219c32904b3c2ed861d971ee2e9c72adb01216d40501278551fef841` |
| `v2/records.py` | 25281 | `a771bfa9bf1e5c60f091235b2ae8d48007a6bd09216b19570cda81ac43cebbea` |

Private administrative sources additionally inspected: exact Disposition 09 lead
ruling, 12977 bytes, raw
`f9a380367e995ec27e3deb73ae67b45b0af3883ae4a8944d83db004e71674b46`,
especially section 3 and Phase A lines 133–179; timing analysis, 10510 bytes,
raw `d823d82ff430948031e4dede504cd0196cdca49b320f78d9ca2ba5636dcdc721`.
The original CONSUME readback had 6671 bytes, raw
`6c1b60409a9ff29553821774418c5020eb3d6e10742cf1d17c49455b94e046e3`.
These administrative bindings are not a new operational timing receipt.
