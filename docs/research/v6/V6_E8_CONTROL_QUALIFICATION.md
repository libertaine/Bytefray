# Bytefray V6 E8 - Control Qualification (Checkpoint B)

**Checkpoint B: approved PASS. Controls complete: 8,448 / 8,448 cells and 8,448 / 8,448 bound traces. Stop before treatment.**

The research lead authorized blinded C8/C8L control qualification under the clarified private/public boundary. The frozen planner, E6 trace-storage scheme, E8 instrument, family, engine and analysis identity were used unchanged. No seed was regenerated.

| Boundary | Value |
|---|---|
| Recorded at (UTC) | `2026-10-01T17:35:50.274699Z` |
| Execution source | `0e53a4e40b14c34c237209489d2e75252a9051c7` |
| C8 identity (primary control) | `bytefray-rules-6-research-sensing-r32` |
| C8L identity (companion control) | `bytefray-rules-6-research-disruption-slot1-sensing-r32` |
| Governing preregistration freeze | `v6-e8-prereg-v4-0166cdc0b37a` |
| Preregistration freeze record SHA-256 | `bf4a409a782f1d3ae08dc4b26b710b37fb8d3e14c6fb76a6904adb9519de31ea` |
| Structural matrix | `v6-e8-matrix-v1-e0d322b597da` |
| Structural matrix digest | `e0d322b597da298686c7a392a7ae495a96ea6a5428b5fb47f15138fa3af26fc7` |
| Execution matrix | `v6-e8-exec-v1-34a254752449` |
| Seed commitment | `94a58a002b0e44a14b2e7a41d03b8007484079ead7973618d3d09bce01046dc9` |
| Analysis freeze | `v6-e8-analysis-v1-52e09e5fb422` |
| Analysis identity digest | `52e09e5fb422e7f90f912b4ceccf40b137286d2915e5e2a14ec76eb89288b106` |
| Qualified instrument tooling | `6d3930a` |
| Family freeze | `v6-e8-family-v1-981fc8b12beb` |
| Family freeze record SHA-256 | `4ec253d4b84469cdb90b91d68b2236310ecd0bb8e0f5c8f63a19e709cc3afbeb` |
| Qualified engine source manifest | `9323307c4131105a30c94cad16845468937571657b6d354827a26cfbfcff2676` (116 files) |
| Private qualification record SHA-256 | `559cc4b04f9408b663cda4ed83420e12f9bac840d1e46643200aa20a2f3b0afe` |

## Execution and qualification

The focused preflight passed **209 tests, zero failures**: parent byte identity, runner ordering, gates, seed protocol and analysis freeze. Four evaluation workers ran each control field; the frozen serial trace pass then re-executed every cell. Each stored trace reproduced the evaluated replay SHA-256, match ID and result ID, and its binding named the canonical replay. Rows and descriptive telemetry were retained for every cell. Source and family checks passed before and after every field.

| Condition | Field | Evaluated cells | Bound traces |
|---|---|---:|---:|
| C8 | F1 | 3,520 | 3,520 |
| C8 | F2 | 704 | 704 |
| C8L | F1 | 3,520 | 3,520 |
| C8L | F2 | 704 | 704 |
| **Total / registered requirement** | | **8,448 / 8,448** | **8,448 / 8,448** |

The frozen `qualify` command re-ran the parent goldens, checked control provenance, evaluated both control arms and computed the registered C8 seat strata. Gate evidence is aggregated below; raw samples and diagnostics remain private.

| Gate | Status | Checked | Failures |
|---|---|---:|---:|
| D8-6 | PASS | — | — |
| CQ8-1 | PASS | 8448 | 0 |
| CQ8-2 | PASS | 2304 | 0 |
| CQ8-3 | PASS | — | — |
| CQ8-4:primary | PASS | — | — |
| CQ8-4:companion | PASS | — | — |
| CQ8-5 | PASS | — | — |
| C8/D8-1 | PASS | 4224 | 0 |
| C8/D8-11 | PASS | 352 | 0 |
| C8/D8-12 | PASS | 4224 | 0 |
| C8/D8-13 | PASS | 4224 | 0 |
| C8/D8-14 | PASS | 4224 | 0 |
| C8/D8-15 | PASS | 4224 | 0 |
| C8/D8-7 | PASS | 4224 | 0 |
| C8/D8-8 | PASS | 4224 | 0 |
| C8L/D8-1 | PASS | 4224 | 0 |
| C8L/D8-11 | PASS | 352 | 0 |
| C8L/D8-12 | PASS | 4224 | 0 |
| C8L/D8-13 | PASS | 4224 | 0 |
| C8L/D8-14 | PASS | 4224 | 0 |
| C8L/D8-15 | PASS | 4224 | 0 |
| C8L/D8-7 | PASS | 4224 | 0 |
| C8L/D8-8 | PASS | 4224 | 0 |

The frozen P8-11 size record measured 3,520 C8/F1 traces: 8,811,963,632 LF-normalized bytes and 232,867,285 gzip bytes. Its projection to all 16,896 registered matrix cells is 1,117,762,968 gzip bytes. This is the frozen projection from that field, not a measurement of the complete matrix. Every control trace is retained.

## Control corpus and unlock binding

The frozen control block in [`analysis_freeze.json`](../../../tools/research/v6/e8/analysis_freeze.json) contains exactly `status: PASS` and `record_sha256: 559cc4b04f9408b663cda4ed83420e12f9bac840d1e46643200aa20a2f3b0afe`. The digest is over the exact private qualification-record bytes, including every gate result and the CQ8-5 strata. The later treatment unlock must load that same record and verify this digest and the strata; the public Markdown record is not substituted for it.

| Immutable control boundary | SHA-256 |
|---|---|
| Complete private control corpus manifest | `adcb7e48e939ad097a84ca6033343cbd633c3607b5821dfdf782e674740696c1` |
| Qualification record | `559cc4b04f9408b663cda4ed83420e12f9bac840d1e46643200aa20a2f3b0afe` |
| P8-11 trace-size record | `c89d981c13eece3449119ea3eda7bcb8d1847d61441f5a41475ee6d654b0e00f` |
| C8/F1 trace index | `837541a7ee433040668560f6819cc0bed08cd50740cea2b3b3c882e3a1528c5d` |
| C8/F2 trace index | `91160b79c8ec3016a830e27e9e9849b38258285504bf1e0919caf245940f54d1` |
| C8L/F1 trace index | `3793ebb6812826c775d2e8a2726cc446abc05561bb8c251f5ff91a1bd87bcec0` |
| C8L/F2 trace index | `3203c8437c16f39d16be013756a30b5d9a97e01b893c3d98059bd1ce75a4eaf6` |

The manifest covers **42,634 files, 4,288,542,119 raw bytes**: every file in the four completed control fields (evaluation artifacts, copied packages, provenance, traces, rows, summaries and telemetry), plus the qualification and trace-size records. It excludes operational scripts, logs and scratch directories outside those fields. Reproduction sorts every file by its POSIX relative path from the structural-matrix corpus root, then writes one UTF-8 JSON object per line with the exact keys `path`, `bytes` and `sha256`, sorted keys, compact separators, `ensure_ascii=False` and a trailing LF. Each file hash covers its raw bytes without normalization. The published corpus digest is SHA-256 of those manifest bytes. The manifest and its seed-bearing relative paths stay private. No registered instrument or analysis identity changed.

Finalization independently reconciled all 8,448 completed cells with the trace indexes, checked match/result/seed/Ruleset identities and canonical replay paths, and confirmed that every indexed compressed trace is present with its recorded size. Qualification and trace-size bytes were preserved.

## CQ8-5 seat strata

Computed on C8 only using the frozen O-NEUTRAL point-estimate rule. These seed-free unit labels are the reviewable strata for the next boundary.

**C8-neutral: 53 units.**

- `pairing|RUSH8|REACQ8`
- `pairing|RUSH8|GUARD8`
- `pairing|RUSH8|EVADE8`
- `pairing|RUSH8|GREED8`
- `pairing|RUSH8|ADAPT8`
- `pairing|RUSH8|STRESS8`
- `pairing|REACQ8|GUARD8`
- `pairing|REACQ8|EVADE8`
- `pairing|REACQ8|GREED8`
- `pairing|REACQ8|ADAPT8`
- `pairing|REACQ8|STRESS8`
- `pairing|PACED8|STEALTH8`
- `pairing|PACED8|LURK8`
- `pairing|PACED8|SPLIT8`
- `pairing|PACED8|GUARD8`
- `pairing|PACED8|EVADE8`
- `pairing|PACED8|GREED8`
- `pairing|PACED8|STRESS8`
- `pairing|STEALTH8|LURK8`
- `pairing|STEALTH8|SPLIT8`
- `pairing|STEALTH8|GUARD8`
- `pairing|STEALTH8|EVADE8`
- `pairing|STEALTH8|GREED8`
- `pairing|STEALTH8|STRESS8`
- `pairing|LURK8|SPLIT8`
- `pairing|LURK8|GUARD8`
- `pairing|LURK8|EVADE8`
- `pairing|LURK8|GREED8`
- `pairing|LURK8|STRESS8`
- `pairing|SPLIT8|GUARD8`
- `pairing|SPLIT8|EVADE8`
- `pairing|SPLIT8|GREED8`
- `pairing|SPLIT8|STRESS8`
- `pairing|GUARD8|EVADE8`
- `pairing|GUARD8|GREED8`
- `pairing|GUARD8|ADAPT8`
- `pairing|GUARD8|STRESS8`
- `pairing|EVADE8|GREED8`
- `pairing|EVADE8|ADAPT8`
- `pairing|EVADE8|STRESS8`
- `pairing|GREED8|ADAPT8`
- `pairing|GREED8|STRESS8`
- `pairing|ADAPT8|STRESS8`
- `mirror|RUSH8`
- `mirror|REACQ8`
- `mirror|PACED8`
- `mirror|STEALTH8`
- `mirror|LURK8`
- `mirror|SPLIT8`
- `mirror|GUARD8`
- `mirror|GREED8`
- `mirror|ADAPT8`
- `mirror|STRESS8`

**C8-non-neutral: 13 units.**

- `pairing|RUSH8|PACED8`
- `pairing|RUSH8|STEALTH8`
- `pairing|RUSH8|LURK8`
- `pairing|RUSH8|SPLIT8`
- `pairing|REACQ8|PACED8`
- `pairing|REACQ8|STEALTH8`
- `pairing|REACQ8|LURK8`
- `pairing|REACQ8|SPLIT8`
- `pairing|PACED8|ADAPT8`
- `pairing|STEALTH8|ADAPT8`
- `pairing|LURK8|ADAPT8`
- `pairing|SPLIT8|ADAPT8`
- `mirror|EVADE8`

## Source and post-write verification

Every control field's provenance records `git_dirty: false` and execution source `0e53a4e40b14c34c237209489d2e75252a9051c7`. The engine manifest, family freeze, preregistration, structural matrix and complete analysis instrument load without drift. The tooling and reused-file hashes are checked against qualified commit `6d3930a`; no executable, tooling or qualification-test file changed. Only this public record and the analysis record's control block are included in the checkpoint candidate.

The analysis identity object, digest, freeze ID and existing seed-commitment block are byte-for-byte unchanged in their recorded values. The control block is deliberately outside the analysis identity digest. The private 32-seed list still verifies against its existing commitment; no value is published or regenerated.

Post-write verification passed the same five focused modules against the completed PASS block: `test_v6_e8_parent_byte_identity.py`, `test_v6_e8_runner.py`, `test_v6_e8_gates.py`, `test_v6_e8_seed_protocol.py` and `test_v6_e8_analysis_freeze.py`. **Result: 209 passed; zero failures, errors or skips.** The exact private qualification record additionally passed `require_control_qualification`, verifying its digest and committed strata. Fresh ignored repository-local test directories keep raw diagnostics private. The same focused check is repeated against the final record bytes, including this result, before staging and publication; a failure stops without instrument repair. A new full repository run is not required for these record-only changes.

## Private/public boundary

The ignored private corpus retains seed-bearing filenames, directories, trace bindings, match paths, summaries and raw diagnostics produced by the frozen tooling. Operational TEMP/TMP were placed under that root for transient trace work. The public record uses condition/field labels, seed-free unit labels, aggregate counts and digests. No private summary or diagnostic is copied verbatim.

Before creating this record, the value-based scan checked all 32 decimal seed values against 1,183 tracked/public candidate files and exported logs, paths, all index blobs, diff/status output and the latest commit message. It also checked 354,816 actual seed-bearing private path strings in absolute, relative, slash and JSON-escaped forms. **Zero matches occurred outside the ignored private corpus.** The draft candidate bytes were checked before writing and the full boundary scan was repeated afterward. Raw scan locations remain private.

**Final public leakage result: PASS; zero matches outside the ignored private corpus.** The finalization scan covered all 32 decimal seed values, 354,816 actual seed-bearing private-path patterns, and 1,184 tracked/public candidate files and paths, including exported logs and every index blob. Staged/unstaged diffs and status are included; the intended commit message independently passed the value-based filter. The same boundary scan is repeated over the exact two staged candidate files and all public/index content immediately before commit. Any nonzero result stops publication. No raw private path or diagnostic is staged. The two finalized files are the single checkpoint commit/push candidate; publication is followed by clean-tree/source verification and agreement of local HEAD, `origin/v6-research` and the live remote.

## Stop boundary

T8 and T8L artifacts are absent. **No T8/T8L treatment execution, seed reveal, treatment analysis or interpretation occurred.** No treatment gates, full experiment analysis, D8-10 or disposition occurred. CQ8-4 used the controls in both slots solely for control qualification. This Q8 result is not final E8-D or a gameplay verdict.

The research lead approved the control qualification as PASS and authorized finalization, focused verification, the final staged/public leakage scan, and a single commit and push containing this record and the PASS block together. This checkpoint stops before treatment. Treatment execution requires separate authorization after the pushed boundary. Treatment completion must subsequently be pinned in an immutable, committed pre-reveal corpus/gate boundary for review before any public seed reveal or final registered analysis and interpretation.
