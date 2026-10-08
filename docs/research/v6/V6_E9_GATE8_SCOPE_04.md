# E9 v2 Gate-8 scope 04 (Seal 08)

FROZEN 2026-10-08. This is the readable mirror of the write-once record
`tools/research/v6/e9/v2_gate8_scope_04.json`:

- identity `v6-e9-v2-gate8-scope-0f65753151e2`;
- body digest `0f65753151e226f168105e511d4c14ea05e15f82a0ffe064770306a37dadcca3`;
- raw SHA-256 `4232fe1164456fc8109d0f56e03ee12500bc9c5d308578c11586dc4638e103e1`.

The JSON governs this mirror. Neither grants authority of its own. The authority is the
research lead's Seal-08 scope rulings, transcribed verbatim in
`tools/research/v6/e9/v2_seal08_lead_scope_rulings_01.txt` (raw `d3a1b028…`), under
[Disposition 05](V6_E9_V2_FINDING_DISPOSITION_05.md) (raw `5bf0c83b…`). The full design
is in [Plan 02](V6_E9_SEAL08_PLAN_02.md), which adds to [Plan 01](V6_E9_SEAL08_PLAN_01.md)
without editing it.

Freezing this scope is not a seal. Scope 03 and its amendment are unchanged.

## Baseline

- HEAD `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c`, empty index, nothing committed.
- Seal 07 is `v6-e9-instrument-v2-3c2bda92b3c0` (seal raw `fe2e9a4b…`): CREATED,
  INDEPENDENT REPRODUCTION FAIL. Candidate 30 = final_07 is immutable.
- All 327 Seal-07 manifested files (293 + 34) were rehashed unchanged before and after
  this record was written.
- The next candidate is 31.

## Rulings

| ID | Ruling |
| --- | --- |
| D8-01 | Option C approved, option N rejected. Qualification must not exclude the other-entry masking case. |
| D8-02 | Exactly E8-1 (implementer, C1–C3) and E8-2 (new independent author, C4) are authorized. |
| D8-03 | DV8-1 and DV8-2 confirmed. DV8-3 confirmed as a scope constraint: no new registry read. |

## Implementation boundary

| File | Function (Seal-07 lines) | Permitted change |
| --- | --- | --- |
| `tools/research/v6/e9/v2/authority.py` | `AuthorityLog.registered_producers` (274–304) | Remember the first mapped `ProducerRegistryUnavailable` instead of stopping, skip only the checks that depend on it, continue every other existing read and check, let a positive mismatch raise at once, and raise the remembered error after a complete scan. No new read site, no changed check or message, no other method or caller. |
| `tools/research/v6/e9/v2/private_verification.py` | `_operational_boundary` (254–302) | Compare this G's own registry entry before the scan and independently of it. Keep the scan, its deferral and the marker's sealed position. When this G's entry is unavailable, run the unchanged scan after the marker check (DV8-5). |
| same | `produce_private_verification` outcome mapping (518–529) | `Unavailable` before `phase == "verification"` → `REFUSED_PRECONDITION`. A verification-phase `Unavailable` stays `UNAVAILABLE`. |

## Required semantics

**F1 ordering.**

1. A current-G registry mismatch is `FAILED_VERIFICATION`.
2. A marker mismatch is `FAILED_VERIFICATION`.
3. Any other available registry-entry consistency mismatch is `FAILED_VERIFICATION`.
4. Unavailability with no available positive mismatch is `UNAVAILABLE`.
5. Otherwise processing continues normally.

**Scan contract.** With no mapped read unavailable, the scan is identical to Seal 07. With
one unavailable, the result is Seal 07's unless a positive mismatch is found later, in
which case that mismatch raises. Single-condition semantics are preserved.

**F2.** Protected-entry and `_preconditions` unavailability is `REFUSED_PRECONDITION`.
Verification-phase unavailability stays `UNAVAILABLE`. The write phase and the post-PASS
recheck are unchanged.

**Recovery.** A pure availability condition recovers only when the exact evidence
returns. A discovered positive mismatch stays terminal.

## Derived readings

- **DV8-1, DV8-2 and DV8-3** were confirmed by the lead.
- **DV8-4 (implementer-derived; the lead may strike it).** After a deferral, an error that
  is not positive mismatch evidence ends the scan with the first deferred error, where
  Seal 07 stopped. Without this, "deferred + later catalogue `Unavailable` + marker
  mismatch" would move from `FAILED_VERIFICATION` to `UNAVAILABLE`.
- **DV8-5 (implementer-derived placement of approved option C; the lead may strike it).**
  The current-G-unavailable scan runs after the marker comparison. It ignores only its
  deferred or `OSError` unavailability and adds no read site.

## Legacy qualification exceptions

| ID | Node(s) | Before (module / block raw) | Permitted change | Editor |
| --- | --- | --- | --- | --- |
| E8-1 | `test_v6_e9_v2_gate8_seal07.py::test_s7_operational_durable_objects_are_unavailable_without_read[event\|active\|retained]` | `09a7082a…` / `e0988ff2…` (lines 87–129) | Line 126 only, at most two lines: `REFUSED_PRECONDITION` for event, active and retained; `UNAVAILABLE` otherwise. | implementer |
| E8-2 | `test_v6_e9_v2_independent_gate8_seal07.py::test_R01_audited_source_checker_rejects_at_both_protected_checks[entry]` | `7861a563…` / `d4c857c7…` (lines 431–456) | Line 456 only: the `pass_number == 1` label becomes `REFUSED_PRECONDITION`. | a new independent test-author context |

The prefix and suffix hashes of both modules are in the JSON and must stay identical.

## New qualification

- `engine/tests/test_v6_e9_v2_gate8_seal08.py` (implementer).
- `engine/tests/test_v6_e9_v2_independent_gate8_seal08.py` (a new independent author). It
  derives its expectations from Disposition 05, the rulings, Planning Revision 02 §3 and
  this scope, never from the implementer's module.

Both must cover the D8-01 minimum list, both recovery distinctions, and the F2 distinction.

## Validation, sealing, stop conditions

**Validation.** All runs go through `qualification_run`, sequentially. They cover:

- both Seal-08 focus runs;
- all prior Gate-8 modules;
- the full 29-module V2 suite;
- the WSL native supplement;
- Ruff, mypy engine and mypy client;
- the bindings checks.

**Sealing.** Only on one exact, fully passing candidate pair. The final_08 manifests are
byte-identical to that pair. A fresh independent qualifier then probes combined
unavailability + later positive mismatch, including the other-entry case.

**Stop conditions.** Work stops and returns to the lead if:

- another implementation file becomes necessary;
- another sealed test must change;
- a frozen requirement conflicts with the rulings;
- option C needs a new read or a different set of consulted registry objects.

## Status

- Seal 07: INDEPENDENT REPRODUCTION FAIL.
- S7-IQ-F1: Seal-08 blocker. S7-IQ-F2: Seal-08 repair. S7-IQ-F3–F10: record only.
- Gate-8 operational acceptance, Requirement C and historical coverage: NOT ESTABLISHED.
- Execution: LOCKED. Q: absent.

Not authorized: REAL entropy, operational generation, operational W, salt, native
matches, operational publication, Q, Gate 7, operational O/V/A/R/B, real-study
stale-lock clearance, commit and push.
