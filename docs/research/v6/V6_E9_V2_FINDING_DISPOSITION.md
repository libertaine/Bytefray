# E9 v2 finding disposition and final remediation scope

**Recorded 2026-10-05.** This page summarizes the write-once record
`tools/research/v6/e9/v2_finding_disposition_01.json`
(raw SHA-256 `4e7aa274f74fb3309a5b11e6448a22565c071eeec829483b3812bbc22b957669`).
If the two ever differ, the JSON record governs.

The record covers seal 03 (`v6-e9-instrument-v2-f109f1afc904`; seal raw SHA-256
`4110b46e…2c6df3`) and reviews 01–03. Prior reports were treated as untrusted
input. H1 and M1–M7 were re-checked against the seal-03 source and the frozen
contract, schema and plan. H1, M1, M2, M3 and M5 were also reproduced read-only,
with no entropy draws and no matches.

## Rulings

| ID | Finding | Disposition | Authority |
| --- | --- | --- | --- |
| H1 | No release after conclusive disproval or post-boundary-only first use | **FIX REQUIRED** | Lead ruling |
| M1 | Proven overlap downgraded to SUSPICION by an uncertain proof in the same batch | **FIX REQUIRED** | Lead ruling |
| M2 | Final sealer does not re-derive Z, B, or the row 6/7 severe-constraint split | **FIX REQUIRED** | Lead ruling |
| M5 | Entropy source (real vs synthetic) not recorded; synthetic is the default | **FIX REQUIRED** | Lead ruling |
| M3 | Public sanitization is a marker list, not a comparison with actual private values | **ACCEPTED FOR CORRECTION** | Lead's stated inclination |
| M6 | No explicit NOT_APPLICABLE disposition for T | **FIX REQUIRED** | Lead criterion met: schema O says "otherwise explicit NOT_APPLICABLE" |
| M7 | Complete E6/E8 inclusion reduced to presence | **FIX REQUIRED** | Lead criterion met: "both complete E6/E8 revealed lists" |
| M4 | No W producer; consumers never recompute c | **RULED, NO CHANGE** | See below |

**M4, who is authoritative for c.** The producer's completion path computes c
over the exact payload and salt. W, the independent private verifier, is the
only authoritative recomputation (R11: "Recompute all private bytes and c").
U, C and D take c by exact equality with W (R12/R13), and that equality is
already enforced. The frozen protocol does not require consumers to recompute
c, so that half of the finding is nullified. A dedicated W-record producer stays
with gate 8, as recorded for review-02 M-3. It is a declared limitation of the
qualification boundary.

**M6 representation.** The frozen schema has no typed slot for this, and no
frozen field is added or retyped. The disposition goes in
`O.body.custodian_attestation.T_disposition` as NOT_APPLICABLE, with a reason,
the research-lead actor and an evidence ArtifactRef. It is required exactly when
O binds no T and is forbidden when O does bind T.

**M7 reference lists.** These are the tracked public reveal files for E6 and
E8, whose digests are already pinned in
`v2_inherited_preservation_manifest_01.json`. The instrument pins the same
digests, and each E6/E8-labelled source union must equal its complete list.

**H1 boundary.** The fix covers PARTIAL_GENERATION through FINAL_PUBLIC. A
conclusive disproval must be explicit and corroborated by the authoritative
execution receipt. A false or unverified field on its own stays SUSPICION. A
hold during BEFORE_GENERATION is not terminal and keeps the existing renewal
route.

Lower-severity and older open items are not in scope. Most are accepted
fail-closed limitations or test-depth deferrals; the JSON record gives each
basis. IQ-17 (a hold between the 1412th acceptance and salt creation) is in
the same failure class as H1 but confined to one operator action, so it is
left out unless the lead promotes it.

## Final remediation scope (frozen)

> HIGH release semantics, M1, M2, M5, plus only those already-reported findings
> explicitly accepted for correction in this record. No newly discovered
> non-blocking finding opens another implementation cycle.

The items accepted for correction are H1, M1, M2, M3, M5, M6 and M7. The
sequence is:

1. Implement them.
2. Write new write-once manifests and seal 04.
3. Run an independent reproduction of seal 04.
4. Record any newly discovered findings without remediation, unless a finding
   is a BLOCKER or shows the seal is invalid.

The formal Q record is not created. It is considered only for the instrument
that seal 04 covers, after that seal has been independently reproduced.
Execution remains LOCKED. Requirement C and historical coverage remain NOT
ESTABLISHED. Native-artifact qualification was not performed.
