# Seal-08 cycle: Seal 08 created, independent qualification PASS WITH FINDINGS

Recorded 2026-10-08 under the lead's Seal-08 scope rulings, which are transcribed verbatim in
`v2_seal08_lead_scope_rulings_01.txt` (raw `d3a1b028…`). The machine record
`v2_seal08_cycle_report_01.json` (`v6-e9-v2-seal08-cycle-report-4656ba246fdd`, raw `998d0cfb…`) binds every
file below by hash and governs this mirror.

All the authorized steps ran:

- The scope was frozen.
- Candidate 31 passed every required check.
- Seal 08 was created.
- A fresh independent qualifier reproduced it: every run passed, the result is **PASS WITH FINDINGS**, and
  there are no blockers and no non-blocking findings, only four notes.

Nothing was fixed after sealing. Gate-8 operational acceptance needs the lead's disposition.

## Records and identities

| Item | Identity | Raw SHA-256 |
| --- | --- | --- |
| Scope 04 (`v2_gate8_scope_04.json`), mirror `docs/research/v6/V6_E9_GATE8_SCOPE_04.md` | `v6-e9-v2-gate8-scope-0f65753151e2` | `4232fe11…` |
| Plan revision 02 (`docs/research/v6/V6_E9_SEAL08_PLAN_02.md`) | — | `87ea8620…` |
| Scope verification 01 | `v6-e9-v2-seal08-scope-verification-a605e5c67a3f` | `1bbe3937…` |
| Edit provenance 01 | `v6-e9-v2-seal08-edit-provenance-28ecec00f2cf` | `a6bcba20…` |
| Candidate 31 implementation manifest (293 files) | attempt_31 = final_08 | `b91bc866…` |
| Candidate 31 qualification manifest (36 files) | attempt_31 = final_08 | `a2866402…` |
| **Seal 08** (`v2_final_manifest_seal_08.json`) | instrument `v6-e9-instrument-v2-3c692f23d2d9` | `38c16e33…` |
| Auditor reproduction output | same instrument | `54d7b967…` |
| Independent qualifier report 01 | PASS WITH FINDINGS | `0458f20e…` |
| Tooling attempt history (Seal 08) | `v6-e9-v2-attempt-history-a77b91c74b50` | `77ae26e3…` |
| Qualification evidence 08 | `v6-e9-v2-qualification-evidence-2c0b9fffc93f` | `c13fe1d4…` |

The instrument digest is `3c692f23d2d9a7467e07b36ea97a382c1497511033767b078dc8de057033d8e0`. The qualifier and
the auditor script each re-derived it independently.

## What changed against Seal 07

**Implementation.** Only two files changed, and only the authorized functions in them:

- `authority.py`: `AuthorityLog.registered_producers`. The prefix and suffix around it are byte-identical.
- `private_verification.py`: `_operational_boundary` and the outcome mapping.

Semantics:

- **D8-01 option C.** A mapped registry read that is unavailable is deferred, not final. Every readable entry,
  G record and event is still checked, a positive mismatch raises at once, and only a scan that finds no
  mismatch raises the first deferred error.
- **S7-IQ-F1.** This G's own registry bytes are compared before the scan and independently of it.
- **S7-IQ-F2 / DV8-1.** `Unavailable` before protected verification is entered (protected entry and
  `_preconditions`) is recorded `REFUSED_PRECONDITION`. Verification-phase unavailability stays `UNAVAILABLE`.
  The caller still receives the typed `Unavailable`.
- **DV8-4 and DV8-5** are the implementer-derived readings recorded in scope 04; the lead may strike them.

**Qualification.**

- E8-1 (implementer): `test_v6_e9_v2_gate8_seal07.py` line 126 now expects `REFUSED_PRECONDITION` for
  `event`, `active` and `retained`. Module `09a7082a…` became `21abd191…`, and the prefix and suffix are
  unchanged.
- E8-2 (new independent editor): `test_v6_e9_v2_independent_gate8_seal07.py` line 456 changed only the
  `entry` label. Module `7861a563…` became `192e1e82…`, and the prefix and suffix are unchanged.
- New implementer module `test_v6_e9_v2_gate8_seal08.py`: 59 cases.
- New independent module `test_v6_e9_v2_independent_gate8_seal08.py`: 42 cases. A fresh author wrote it from
  Disposition 05, the rulings, scope 04 and Planning Revision 02. Its transcript audit found no forbidden read
  and no pytest run. It disclosed reading the working-tree implementation for mechanics.

The exact diffs and every before/after hash are in the edit provenance record.

## Validation (candidate 31 = final_08)

| Check | Implementer | Independent qualifier |
| --- | --- | --- |
| Seal-08 focus | implementer module 59/59; independent module 42/42 | in the full run |
| Prior Gate-8 modules (8) | 655 collected, 649 passed, 6 skipped (native) | in the full run |
| Full 29-module suite | 1338 collected, 1332 passed, 6 skipped, 0 failed, 0 errors (53:34) | 1338 collected, 1332 passed, 6 skipped, 0 failed, 0 errors (53:16) |
| WSL native supplement (the 6 Windows skips) | 4/4 + 2/2 | 6/6 |
| Ruff; mypy engine; mypy client | pass; pass (97 files); pass (16 files) | pass; pass (97 files); pass (16 files) |
| Bindings / inherited preservation | 9/9 | in the full run |

**Qualifier probes.** The qualifier ran 92 adversarial plain-Python probes on Seal 08 and on an in-process
rebuild of Seal 07. Every probe that carried an expected result gave it, and every single-condition state
behaves exactly as in Seal 07. In 31 combined states, Seal 07 records `UNAVAILABLE` and later reaches `PASS`;
Seal 08 records `FAILED_VERIFICATION` and refuses every retry. Those states include:

- the other-entry masking case;
- up to five simultaneous unavailable sources;
- this G's own entry unavailable;
- wrong current-G bytes with each source.

## Findings (independent qualifier report 01; all NOTE)

- **S8-IQ-F1.** S7-IQ-F3 persists unchanged, as ruled. An unmapped catalogue `Unavailable` inside the scan
  still masks positive evidence, both with no earlier deferral and, through DV8-4, after one. Seal 07 behaves
  identically.
- **S8-IQ-F2 (needs the lead's attention).** A registry entry that parses but has a malformed `G` field makes
  the scan raise an uncaught `TypeError`. No outcome is recorded, so the attempt fails closed and never
  reaches PASS while the entry exists.
  - When the entry is alone, Seal 07 already behaved this way.
  - Through DV8-5 the same crash is now also reachable when this G's own entry is unavailable, provided the
    malformed entry sorts before any deferred read. There Seal 07 recorded `UNAVAILABLE`.
  - The qualifier rates this a NOTE: the malformed entry has no existing `FAILED_VERIFICATION`
    classification to preserve, so no frozen precedence rule is broken.
  - The implementer notes that it is still a combined-state behavior change outside the positive-mismatch
    class that D8-01 names.
  - Whether it is record only or a later remedy is the lead's call.
- **S8-IQ-F3.** Positive-mismatch precedence is confined to the registry/marker boundary. A changed
  retained partial-generation supplement plus this G's unavailable entry gives `UNAVAILABLE`, then `PASS`
  once both are restored, on both seals. This is outside the frozen F1 scope.
- **S8-IQ-F4.** Provenance notes: the independent author's disclosures, and the private backup that was
  pending at the time of the report (it now exists; see below).

## Decisions requested

1. Disposition of Seal 08 (PASS WITH FINDINGS) and of Gate-8 operational acceptance.
2. Confirm or strike **DV8-4**. The qualifier recommends confirming it.
3. Confirm or strike **DV8-5**, with S8-IQ-F2 in view. The qualifier recommends confirming it.
4. Disposition of S8-IQ-F1–F4. F1 and F3 restate behavior that is already ruled record only or is outside
   the F1 scope.

## Preservation, status and confirmation

- **Seal 07.** Its records are unchanged: seal, final and attempt-30 manifests, evidence 07, qualifier
  report 01, cycle report 02, Scope 03, its amendment, Disposition 05, Plan 01 and the scope-drafting record
  are all rehashed equal. The only Seal-07 module changes are E8-1 and E8-2. Their Seal-07 bytes remain in
  final_07, in the Seal-07 run snapshots and in the private backup.
- **Final rehash.** All 329 final_08 manifested files match after the reproduction.
- **Git.** HEAD is `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c`, the index is empty, and nothing was committed
  or pushed. The status snapshot is `v2_seal08_git_status_final_01.txt` (117 lines, `9fb48016…`).
- **Private backup** (a new, separate directory):
  - path: `D:\Projects\BATTLE2-private-evidence\v6-e9-seal08-transcript-provenance\`;
  - size: 816,675 files, 397,940,524 bytes;
  - verification: every copied file matches its source. The only listed failure is the verification script
    itself, which was written after the copy;
  - contents: the implementer session snapshot, the E8-2 editor, author and qualifier transcripts, the
    implementer scripts and diffs, the probes, and the qualifier's work, including its synthetic probe
    roots;
  - there is no off-machine copy.
- **Interruptions.** One development probe aborted on a probe-script defect and was rerun. The qualifier
  context hit an API usage limit after its full run and resumed in the same context. No harness attempt was
  interrupted.
- **No operational E9 work occurred:**
  - no REAL entropy, operational generation, operational W or salt;
  - no native matches or operational publication;
  - no Q, Gate 7 or operational O/V/A/R/B;
  - no real-study stale-lock clearance.

Execution remains LOCKED. Gate-8 operational acceptance and Requirement C remain NOT ESTABLISHED, and Q is
absent.
