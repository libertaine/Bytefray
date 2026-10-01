# Bytefray V6 E8 - Seed Commitment (I8-6)

**Status: COMMITTED SEED BOUNDARY; stopped before Q8, reveal or execution.**

The research lead closed I8-5 and authorized exactly one invocation of
`python -m tools.research.v6.e8.run_e8 generate-seeds --confirm-seed-generation`.
The three approved I8-5 commits (`6d3930a`, `8eeaf86`, `0a2e723`) were pushed
first. Local HEAD, `origin/v6-research`, and the live remote agreed at
`0a2e723d5770d9f0c736a8cf81daf2dc03547616`; the working tree was clean.

## Public commitment

| Item | Value |
|---|---|
| Branch | `v6-research` |
| Generated at (UTC) | `2026-10-01T14:45:36.433931Z` |
| Seed count | **32** |
| SHA-256 seed commitment | `94a58a002b0e44a14b2e7a41d03b8007484079ead7973618d3d09bce01046dc9` |
| Execution matrix identity | `v6-e8-exec-v1-34a254752449` |
| Generation boundary | `0a2e723d5770d9f0c736a8cf81daf2dc03547616` |
| Qualified instrument tooling | `6d3930a` |
| Pre-registration freeze | `v6-e8-prereg-v4-0166cdc0b37a` |
| Family freeze | `v6-e8-family-v1-981fc8b12beb` |
| Structural matrix | `v6-e8-matrix-v1-e0d322b597da` |
| Structural digest | `e0d322b597da298686c7a392a7ae495a96ea6a5428b5fb47f15138fa3af26fc7` |
| Analysis freeze | `v6-e8-analysis-v1-52e09e5fb422` |
| Analysis digest | `52e09e5fb422e7f90f912b4ceccf40b137286d2915e5e2a14ec76eb89288b106` |
| Qualified engine manifest | `9323307c4131105a30c94cad16845468937571657b6d354827a26cfbfcff2676` (116 files) |
| Control qualification | **PENDING** |

The machine-readable commitment is the four-field `seed_commitment` block in
[`analysis_freeze.json`](../../../tools/research/v6/e8/analysis_freeze.json).
The seed and control blocks remain outside the analysis digest. The analysis
identity, digest, qualified tooling, engine, preregistration, family and matrix
are unchanged.

## Protocol and verification

The governing [PR8 section 9](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md)
and [implementation plan section 8](V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md)
place control execution and qualification in the separately authorized Q8 phase.
I8-6 used the frozen generator exactly once: 32 unique integers from
`secrets.randbelow(2**53)`, in generation order, with duplicate draws redrawn.
The registered list checks are uniqueness and the interval `[0, 2**53)`;
there is no additional value exclusion or outcome-dependent filtering.

The list was written only to the fixed git-ignored location under
`runs/research_v6_e8/`, outside every agent package. It was not printed.
An immediate private reread passed strict canonical decoding (decimal ASCII,
LF line endings, trailing LF), count, uniqueness and bounds checks. Re-encoding
reproduced the stored bytes and their SHA-256 commitment. The execution identity
independently recomputed from the structural digest and commitment.

The preregistration, family, matrix, analysis freeze, qualified engine and clean
committed tooling were verified before generation. The freeze and engine checks
passed again afterward. Only the public seed block changed in the existing
freeze record; its identity and digest and its PENDING control block did not.

The runner's output passed the frozen value-based seed filter. The operational
capture also applied that filter before saving logs or forwarding output.
Before commit, every generated seed's decimal value was searched as a substring
in staged content, filenames and absolute paths, tracked file content and paths,
private run artifact names and paths, filtered operational logs, and the diff,
status and commit message intended for the public boundary. The pre-stage and staged checks both passed with **zero seed-value matches**.
The pre-stage scan covered 1,132 tracked file contents; the staged scan covered
both public files, 1,138 filenames/paths and four filtered logs/records.
Failure stops the commit without regeneration.
The private seed file's content is excluded from public-content scans and remains
untracked and ignored.

## Stop boundary

No seed reveal, D8-10 reveal record, matrix execution, traced cell, control run
with real seeds, analysis or interpretation occurred. No tooling or engine file
changed after generation. Q8, T8 and all later exposures require separate
authorization. The historical [I8-5 record](V6_E8_ANALYSIS_FREEZE.md) is preserved
as the record of the pre-seed boundary.
