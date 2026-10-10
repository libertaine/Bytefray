# E9 v2 Gate-8 scope 03 amendment 01 (S7-DEV-B1 qualification exception)

Recorded 2026-10-07 from the research lead's S7-DEV-B1 disposition. The
write-once machine record governs this mirror and grants no authority of its own.
Scope 03 itself is not edited.

- Identity: `v6-e9-v2-gate8-scope-amendment-4088826751d2`
- Body SHA-256: `4088826751d2da39056360e3a0dd1fad3b372693f0de8614a213c6b0292ecfad`
- Raw SHA-256: `3e5c1a4945a7b2f534d58a106cba7c6ed25d710edeffa877f1b3136564261961`
- JSON: `tools/research/v6/e9/v2_gate8_scope_03_amendment_01.json`

## Bound inputs

| Input | Identity / raw SHA-256 |
| --- | --- |
| Scope 03 (unchanged) | `v6-e9-v2-gate8-scope-0233e8825a6a` / `75343cf20cde42796a8ad10405cd475360e6c4e90ef8915add59243114143f98` |
| Preservation supersession 01 | `v6-e9-v2-preservation-supersession-a82d0caccf3b` / `319528a4d7e29266a680e198acea9769229cef41aaf86693607e5044852b4661` |
| Seal 06 (`v6-e9-instrument-v2-29f12a833a09`) | `384f1f1e3f70e9a9392143373459e22d2ffd2741b07c693b00a7f60268ab2825` |
| Disposition 04 | `d3db6c9bac4271384b933da01fa253a0c64d3249c93efa65a819d43f5ccf0839` |
| Lead ruling (transcription) | `820b8895cc556463292a4bd0d0eb5b0ed1f25764a0b67b2eb1dd31ad0e463065` |

## Exception B1-Q1

The exception covers exactly one function:
`engine/tests/test_v6_e9_v2_independent_bindings.py::test_separate_adoption_attestation_exact_review_and_unchanged_body`.

Before modification, the module's raw SHA-256 is
`6b91043e6e75024d56d86b00a7748c55bbf69f5c44d28d719cab850d1fc5b594`. Those bytes
are identical in four places: the Seal-06 manifest, the candidate-29 manifest,
the HEAD blob and the working tree. The function spans lines 48–70, and its
block SHA-256 is `cd7287cf…`.

**Permitted change.** Only the body of this one function may be replaced. Its
`def` line stays unchanged. The prefix (lines 1–47, `53ecc502…`) and the suffix
(the original lines 71–146, `ed1c74b5…`) must stay byte-identical.

**Editor.** A fresh independent test-author context makes this edit. The
implementer does not. Its provenance is retained.

**Why the old assertion is no longer sufficient.** Lines 68–70 require every
adoption-time pin to equal the current bytes. Checkpoint `e035def` made an
authorized change to `.gitattributes`, so that literal loop now fails even
though the change is dispositioned. The loop also cannot verify the supersession.
The test must therefore prove the original manifest, the historical pin and the
single recorded supersession together, while still rejecting any other change.
Every other assertion in the function keeps its present strength.

**Required semantics.** The test must prove all of the following:

1. The original manifest is unchanged, with raw SHA-256 `b1f86c1d…`.
2. Its `.gitattributes` pin is exactly `d26332b3…`.
3. That pin corresponds to commit `2dd8f69` and blob `7064b0bb…`.
4. The current `.gitattributes` bytes equal the single superseding hash `97128fee…`.
5. The current bytes correspond to commit `e035def` and blob `89bba2ee…`.
6. The supersession record verifies. It is pinned by its exact raw hash, and its
   canonical bytes, digest and identity check out. It names exactly one path,
   and its values match those above.
7. Every inherited pin other than `.gitattributes` still matches.
8. No second unrecorded mismatch is tolerated.

**Prohibited.** The edit must not:

- ignore or skip `.gitattributes`;
- use a generic exception list, wildcard or name-pattern discovery of records;
- trust any record that is not pinned by its exact raw hash;
- accept any other `.gitattributes` value.

As a result, a future `.gitattributes` change fails until the lead separately
dispositions it.

## Unchanged boundary

The Scope-03 eight-file boundary is unchanged. The S7-DEV-F1 correction and its
regression cases stay inside `private_verification.py` and the two new Seal-07
test modules.

This amendment does not touch any of the following:

- `.gitattributes`;
- the inherited-preservation manifest;
- any other byte of the bindings module;
- any file outside Scope 03.

The module edit yields a new candidate pair, expected to be attempt 30.

## Status

- Candidate 29 stays preserved, unsealed and superseded as a prospective final candidate.
- Execution is LOCKED.
- Gate-8 operational acceptance and Requirement C are NOT ESTABLISHED.
- Q is absent.
- No operational authorization exists.
