# E9 v2 inherited-preservation supersession 01 (`.gitattributes`)

Recorded 2026-10-07 from the research lead's S7-DEV-B1 disposition. The
write-once machine record governs this mirror and grants no authority of its own.

- Identity: `v6-e9-v2-preservation-supersession-a82d0caccf3b`
- Body SHA-256: `a82d0caccf3b131d4ee853bac1174868db338b6b71d032be33c2677178dd4e9f`
- Raw SHA-256: `319528a4d7e29266a680e198acea9769229cef41aaf86693607e5044852b4661`
- JSON: `tools/research/v6/e9/v2_inherited_preservation_supersession_01.json`
- Lead ruling (implementer transcription): `tools/research/v6/e9/v2_seal07_lead_disposition_b1_f1_01.txt`,
  raw `820b8895cc556463292a4bd0d0eb5b0ed1f25764a0b67b2eb1dd31ad0e463065`

## What is superseded

Exactly one adoption-time pin: `.gitattributes`.

| | Commit | Git blob | Raw SHA-256 |
| --- | --- | --- | --- |
| Adoption pin | `2dd8f69c5c6feb5f3a7d8fc0eb81b0c06802dee2` | `7064b0bb9d533b312b45f0c368610a64777ec8b6` | `d26332b37bbcac74a5e369317df33cbbecd4042f4ca6867770e38a54307bfd86` |
| Superseding value | `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c` | `89bba2ee71b70188107be24fd918c078b0b6ae76` | `97128feeef25cbe98af6770173d09a809b1c0f626ec2a5ac558236aaf4b99555` |

The checkpoint commit's parent is `2dd8f69`. The change only appends lines:
it adds 14 lines (two blank, three comments and nine `-text` path attributes)
and alters no prior line. The record holds the full prior and superseding bytes
and the exact `git diff --full-index` output, whose raw SHA-256 is
`6a0642bf4d7f2056a4e0b914b17638b524d9ffaa8687cc30f99ca332d404c6d2`.

**Why it changed.** Checkpoint commit `e035def` deliberately added narrow `-text`
attributes so that Git preserves the exact CRLF working-tree bytes that E9
scientific records and Seal 06 bind by raw hash. It covers four E9 evidence,
planning-ruling and recovery-test paths, plus five Seal-06 CRLF tracked files.
This changed how the repository preserves bytes. It changed no scientific input,
implementation byte or qualification byte. The record binds the commit object
hash and message, together with the Seal-07 baseline, the continuation
verification and the cycle-report records that found and described S7-DEV-B1.

## What is not changed

`tools/research/v6/e9/v2_inherited_preservation_manifest_01.json` keeps raw
`b1f86c1d9b59be0f8841bf1b587b7a88d3ffb7bed34cffa476ef582606660147`. It has not
been modified, regenerated or invalidated. It correctly recorded the repository
at adoption, and it remains authoritative for every path except `.gitattributes`.

At recording time:

- 1202 of 1203 inherited pins matched;
- `.gitattributes` was the only mismatch;
- the live `.gitattributes` bytes equalled the checkpoint blob.

Scope 03 (`v6-e9-v2-gate8-scope-0233e8825a6a`, raw `75343cf2…`) and
Disposition 04 (raw `d3db6c9b…`) are bound unchanged.

## Narrow semantics

- The record names one path and one superseding SHA-256.
- It defines no exception list, wildcard, discovery rule or record family that
  would let later records or later bytes be trusted automatically.
- Any further `.gitattributes` change must fail until the lead separately
  dispositions it, and so must a mismatch on any other inherited path.

## Historical claim

All adoption-time inherited pins remain unchanged except one: the explicitly
authorized and cryptographically recorded post-adoption `.gitattributes`
supersession. `.gitattributes` did change. That change is authorized and
recorded; it is not an unexplained integrity failure.

## Status

S7-DEV-B1 is dispositioned by this supersession. The narrow Scope-03
qualification amendment follows separately.

- Candidate 29 stays preserved, unsealed and not independently qualified.
- Execution is LOCKED.
- Gate-8 operational acceptance and Requirement C are NOT ESTABLISHED.
- Q is absent.
- No operational authorization exists.
