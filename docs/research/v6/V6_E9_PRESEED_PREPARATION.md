# E9 committed instrument and pre-seed preparation

**2026-10-02: instrument committed and verified; evaluation artifact binding
PASS; prior-use exclusion inventory NOT COMPLETE.** The protocol is FROZEN.
Seed generation and payoff execution remain UNAUTHORIZED. Requirement C
remains NOT ESTABLISHED.

The research lead authorized committing the qualified instrument and binding
evaluation artifacts/checking exclusions, with separate later authorization
boundaries for seed generation and payoff execution.

## Committed instrument

Commit **`514f4e22e9300d92ce23afaa418e39b06dac277e`** contains exactly the
16 reviewed implementation, test and qualification files. All 14 source/test
raw digests match the original sealed qualification record in both the commit
and working tree. The complete qualification record reproduces byte for byte,
with raw SHA-256
`01456bdda6a1b6749af2a6c7e81ea82abefcacfabe0b6cab5cc5ee38611d6d0a`.

The 69 focused qualification tests passed again using a fresh serial temporary
root. The post-commit freeze/instrument loader and repository Ruff passed.
The unchanged source hashes preserve the recorded full-suite and type-check
evidence in the [instrument qualification](V6_E9_INSTRUMENT_QUALIFICATION.md).
No new full-suite result is claimed by this preparation pass.

## Evaluation artifact binding

The [preparation record](../../../tools/research/v6/e9/preparation_record.json)
binds 41 materialized packages, their 82 raw files, 41 resolved parameter
defaults, the effective T8 conditions, aliases, 29 physical rows and the
11 historical members with their primary/twin identities. The binding digest is
`d655be27a4771cb58f013404621675d1282d21803df119738401c1f1c8e6d7dc`.

The artifacts are retained in the ignored private root derived by the frozen
runner. The [verification record](../../../tools/research/v6/e9/preparation_verification.json)
confirms package/default/environment and committed source bindings.

## Exclusion audit and open coverage gate

The private candidate contains **157 unique entries** from verified E6/E8
reveals, retained match metadata, current literal seed-reference candidates
and harness defaults. The candidate is canonical, domain checked and explicitly
marked `complete: false`. It is not the final inventory consumed by the runner.

| Audit finding | Count/status |
|---|---|
| E6 committed reveal list | 32 entries; commitment and inclusion PASS |
| E8 committed reveal list | 32 entries; commitment and inclusion PASS |
| Retained metadata records examined | 464,207 |
| Records with decoded match-seed evidence | 462,553; independent raw hash and membership read-back PASS |
| Records without decoded match-seed evidence | 1,491 |
| Unreadable metadata records | 163 |
| Inaccessible directories | 10 |
| Current literal seed-argument sites | 320 |
| Current nonliteral seed-argument sites | 158 |
| Literal harness defaults recorded | 25 |
| All prior qualification match-seed coverage | NOT ESTABLISHED |

The source census includes current tracked tests and research tooling. It
records nonliteral call sites for call-chain/derived-selection attribution;
site counts do not establish executed-match counts. The relationship of the
inaccessible/unreadable entries to qualification coverage remains unresolved.
Five unreadable entries have readable sibling seed evidence; that evidence
does not establish the identity of those unreadable artifacts. No inaccessible
directory is assumed seed-free.

The independent [read-back verifier](../../../tools/research/v6/e9/verify_preparation.py)
uses a separate JSON/hex/membership implementation and recomputes raw hashes.
Its [source/evidence binding](../../../tools/research/v6/e9/preparation_verifier.json)
is preserved. Seed values and resolved provenance paths remain private;
public records contain counts, status and digests.

One serial census and one serial read-back were interrupted to replace serial
I/O with bounded parallel reads. Their audit records and the original artifact
binding were retained. These were seed-free preparation operations. The
complete parallel census and independent read-back passed for included evidence.

The remaining prerequisite is a complete historical qualification coverage
ledger or equivalent source evidence, including harness defaults and derived
match-seed selections, with attribution of the recorded access/metadata gaps.
The accepted [Draft 3 §7](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md)
requires: “If completeness cannot be established, generation stays locked.”

## Authorization ledger

| Requested step | Current result |
|---|---|
| Commit and verify the qualified instrument | COMPLETE |
| Bind evaluation artifacts and verify exclusion inventory | Binding PASS; included exclusions verified; full inventory coverage NOT COMPLETE |
| Separately authorize seed generation; generate, verify and publish commitment | PENDING; exclusion coverage must pass first |
| Separately authorize payoff execution | PENDING; no execution grant issued |

No experimental seed payload, salt, execution boundary or cell attempts exist
in the prepared private root. No E9 commitment was generated or published.
The preparation helpers and records are uncommitted; the qualified instrument
and protocol have separate committed boundaries.
