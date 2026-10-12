# Bytefray V6 E8 - Seed Reveal Boundary

**Seed reveal only. Stopped before D8-10, final registered analysis, hypotheses and disposition.**

The research lead approved and closed the immutable blinded boundary at `bc3b435b65e99493720db78df88d1293f45c9dfe` and authorized publication of the existing 32 seeds in their frozen order. The pre-reveal record and all frozen identities remain unchanged. This separate boundary follows the lead's authorized sequence; the frozen runner's `reveal` command was not invoked because it requires analysis and performs D8-10.

The [public reveal record](../../../tools/research/v6/e8/seed_reveal.json) contains all 32 seeds in frozen generation and matrix order. To reproduce the commitment, encode each listed integer as unsigned decimal ASCII followed by LF, including the last line, concatenate in listed order, then compute SHA-256.

| Binding | Value |
|---|---|
| Seed count | 32 |
| Seed commitment | `94a58a002b0e44a14b2e7a41d03b8007484079ead7973618d3d09bce01046dc9` |
| Execution matrix | `v6-e8-exec-v1-34a254752449` |
| Pre-reveal manifest SHA-256 | `c99edbf642be2464f659d34401e41c624e637f6d7c1e827b25c1304ef4f57600` |
| Analysis freeze | `v6-e8-analysis-v1-52e09e5fb422` |

Before exposing any seed, the complete control and treatment corpora were independently rehashed from raw bytes, with exact file inventories and canonical manifest reconstruction. Both matched their committed digests. The original private list passed canonical encoding, count, uniqueness, bounds and commitment checks. Its order matched all eight frozen field provenance records. The execution identity recomputed exactly.

| Corpus | Files | Raw bytes | Recomputed manifest SHA-256 |
|---|---:|---:|---|
| Control | 42,634 | 4,288,542,119 | `adcb7e48e939ad097a84ca6033343cbd633c3607b5821dfdf782e674740696c1` |
| Treatment | 42,634 | 3,981,048,565 | `84ab2f9729401cf06ef60ca6e1b07045c9b9aae51c1a7497972bb3527bb061e6` |

The public JSON was reread and independently encoded to recompute the commitment; it matched exactly and reproduced the original private bytes in order. Treatment gate records and all four trace indexes retain their pre-reveal digests. The unchanged control qualification still binds the C8 strata at 53 neutral / 13 non-neutral; no strata were recomputed.

Seed values are deliberately public. Seed-bearing private filesystem paths, raw diagnostics and private corpus structure remain private. Publication verification checks worktree files, candidate paths, Git index blobs, diff/status output and the commit message under that rule. The focused seed, freeze, parent identity, runner ordering and gate checks use synthetic fixtures; they do not run D8-10 on the E8 corpus.

**No new E8 matches, retries, repairs, analyzer changes, family changes, D8-10, H8 results, KC8 conclusions, four-outcome answer, requirement-C reading, disposition or descriptive interpretation occurred.** Final registered analysis requires separate authorization after this reveal boundary is committed and pushed.
