# Seal-07 cycle stopped for lead disposition

Starting/final HEAD: `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c` on `v6-research`; upstream unchanged, ahead/behind 0/0. No commits or pushes.

**Seal 07 was not created. No final manifests or independent reproduction exist. Execution remains LOCKED, Q absent, Gate-8 acceptance and Requirement C NOT ESTABLISHED.**

The required starting commit changes `.gitattributes`, while the immutable inherited-preservation manifest and unchanged adoption test still require its prior raw bytes. This is a genuine frozen-input/scope conflict. The file is clean at HEAD, and its LF-normalized hash is identical to its raw hash.

| File | Inherited raw pin | Current committed raw bytes |
| --- | --- | --- |
| `.gitattributes` | `d26332b37bbcac74a5e369317df33cbbecd4042f4ca6867770e38a54307bfd86` | `97128feeef25cbe98af6770173d09a809b1c0f626ec2a5ac558236aaf4b99555` |

Failure: `engine/tests/test_v6_e9_v2_independent_bindings.py::test_separate_adoption_attestation_exact_review_and_unchanged_body`, line 70. Focused reproduction: 8 passed, 1 failed. `.gitattributes`, the inherited record and this test are outside the eight-file scope. They were left unchanged. Lead disposition is required before qualification can complete.

## Retained validation

- Candidate 29 focused: 435 passed, 6 Windows skips across 441 tests; exact bytes unchanged.
- WSL native supplement: all 6 skipped cases passed on identical candidate 29 bytes.
- Ruff: PASS. Mypy engine: PASS (97 source files). Mypy client: PASS (16 source files).
- Complete 27-module V2 synthetic run: interrupted after failure observed; no complete counts; NOT PASS. Its logs, snapshots, started/completed evidence and original failure mark remain retained.

Candidate instrument: `v6-e9-instrument-v2-082e7ffd8d16` / `082e7ffd8d165dfda6442e1995c09cd0c777655b99e78973207953deecbd4be4`; unsealed and not independently qualified.

| Candidate 29 manifest | Raw SHA-256 |
| --- | --- |
| `tools/research/v6/e9/v2_implementation_manifest_attempt_29.json` | `5db1bf647b0c65c4e1d83d376000befdb0647b37b20d4ded95925d3d8f2297cf` |
| `tools/research/v6/e9/v2_qualification_manifest_attempt_29.json` | `66b2682fcba6959ab6899525de80d5fa6f952020c503f7ab927d884535a53ca8` |

## Exact source/test changes

- `tools/research/v6/e9/v2/records.py` (modified)
- `tools/research/v6/e9/v2/authority.py` (modified)
- `tools/research/v6/e9/v2/inventory.py` (modified)
- `tools/research/v6/e9/v2/private_verification.py` (modified)
- `engine/tests/test_v6_e9_v2_gate8_seal07.py` (added)
- `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py` (added)
- `engine/tests/test_v6_e9_v2_gate8_seal06.py` (modified)
- `engine/tests/test_v6_e9_v2_independent_gate8_seal06.py` (modified)

Only authorized legacy objects changed: implementer `write_spy`, I1, I3, L2a; independent `Writes`, J1, J3a/J3b/L1/L2b, J4. Every byte outside permitted top-level objects remains identical; all original modules, block hashes and exact diffs are retained. No neighboring test/fixture was edited.

## Attempts

| Attempt | Result |
| --- | --- |
| `e9-v2-seal07-baseline-conflict-reproduction-20261007-01` | 8 passed, 1 failed, 0 skipped; FAILED |
| `e9-v2-seal07-dev-ruff-20261007-01` | FAILED |
| `e9-v2-seal07-dev-ruff-20261007-03` | FAILED |
| `e9-v2-seal07-focused-implementer-20261007-01` | 95 passed, 0 failed, 1 skipped; DEVELOPMENT SOURCE DRIFT; NOT QUALIFICATION |
| `e9-v2-seal07-focused-implementer-20261007-02` | 110 passed, 0 failed, 2 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-focused-independent-tests-20261007-01` | 325 passed, 0 failed, 4 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-implementer-20261007-01` | INTERRUPTED AFTER FAILURE OBSERVED; NO COMPLETE COUNTS; NOT PASS |
| `e9-v2-seal07-independent-author-development-27` | 317 passed, 1 failed, 4 skipped; FAILED |
| `e9-v2-seal07-independent-author-development-28` | 325 passed, 0 failed, 4 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-native-posix-candidate28` | 4 passed, 0 failed, 0 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-native-posix-candidate29` | 4 passed, 0 failed, 0 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-native-posix-development-20261007-01` | PASSED CHECK ONLY |
| `e9-v2-seal07-native-symlinks-candidate29` | 2 passed, 0 failed, 0 skipped; PASSED CHECK ONLY |
| `e9-v2-seal07-static-mypy-client-20261007-01` | PASSED CHECK ONLY |
| `e9-v2-seal07-static-mypy-engine-20261007-01` | PASSED CHECK ONLY |
| `e9-v2-seal07-static-ruff-20261007-01` | PASSED CHECK ONLY |
| `e9-seal07-independent-author-check-01` | None; exploratory/focused evidence, not complete qualification |
| `e9-seal07-independent-author-check-02` | None; exploratory/focused evidence, not complete qualification |
| `e9-seal07-independent-f4-candidate26` | {'collected': 1, 'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0}; exploratory/focused evidence, not complete qualification |

Candidate manifest pairs 25–29 and all unsuccessful/interrupted/development attempts are preserved. The dev-Ruff-02 attempt aborted before checks on source drift; its partial harness directory remains retained and it is not a PASS. Earlier exploratory author runs lack exact startup snapshots; their full console/tool output survives in the retained private transcript.

## Findings and provenance

- S7-DEV-B1: frozen inherited `.gitattributes` pin conflict; lead disposition required.
- S7-DEV-F1: code review found an open typed-unavailability integration edge. `_operational_boundary` catches only `OSError` from `registered_producers`; typed `Unavailable` can mask an independently present marker mismatch. Scope-02 F1 precedence must be preserved. This inference was recorded without a new dynamic qualification case or further source edits after the scope stop.
- Independent author context: `01a117a2-ad1d-7be2-bdba-4998660e8afd`, separately spawned with no inherited turns. Full transcript preserved privately; SHA-256 `1baa616ce9853a89176e4d39c9236773aae70ebe70083a27795d25a1efadc121`. Logs are unsigned/mutable provenance with recorded limits, not independent authentication.

## Final preservation and status

- Current candidate rehash: 327/327; original Seal-06 retained source copies: 325/325; unchanged original live files: 319/319; scope bound inputs: 32/32.
- Inherited tracked-file preservation: 1202/1203, with only the baseline `.gitattributes` mismatch described above.
- Both intentionally untracked review artifacts remain untouched.
- No operational entropy, generation, W, salt, native matches, publication, Q, Gate 7, O/V/A/R/B or real-study stale-lock clearance was exercised.
- Index remains clean; eight source/test files plus append-only evidence are uncommitted.

Complete machine-readable package: [v2_seal07_cycle_report_01.json](v2_seal07_cycle_report_01.json). Final Git status: [v2_seal07_git_status_final_01.txt](v2_seal07_git_status_final_01.txt).
