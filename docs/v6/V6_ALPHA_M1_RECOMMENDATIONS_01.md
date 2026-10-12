# Bytefray V6 — M1 Conditional GO Recommendations 01

2026-10-09, America/Indianapolis. **RECOMMENDATIONS RECORDED; FORMAL
DECISIONS AND IMPLEMENTATION AUTHORIZATION OUTSTANDING.**

This separate note records the user's support for a conditional GO and checks
it against the complete [M1 contract01](V6_ALPHA_M1_CONTRACT_01.md) and
[independent design review01](V6_ALPHA_M1_DESIGN_REVIEW_01.md). The user expressly
described these as recommended decisions and did not claim formal authorization
or independent review of the local documents. Consequently, this note adopts
no K decision, changes no readiness classification and authorizes no coding.
It is a product decision-preparation note, not an E9 disposition or authority event.

## Recommended decisions and contract correspondence

| Decision | User recommendation | Verification against the full contract |
| --- | --- | --- |
| K1 identity/mechanics | APPROVE | Consistent with C/K1: distinct `bytefray-rules-6-alpha1`, independently stated T8-equivalent policy, explicit experimental selection and unchanged stable default. No undocumented mechanic changes or E8 alias. |
| K2 teaching seed exception | APPROVE WITH RESTRICTIONS | Consistent with C/K2 and J: deterministic teaching fixtures only; no E9 execution, evidence/seed reuse, G consumption or implied public seed-secrecy guarantee. Formal lead disposition of the PR8 promotion prerequisite for this bounded exception is still required. |
| K3 knowledge/artifacts | APPROVE | Consistent with E/K3: capability metadata v1 and demo sidecar v1; replay4/trace2/result2 remain unchanged. Samples enter knowledge at receipt, remain historical, and never refresh from omniscient truth. |
| K4 policy inventory | APPROVE WITH RESTRICTIONS | Consistent with C/I/K4: narrowly version current allowed-identity/lifecycle expectations while retaining original qualified revisions, scientific goldens, mechanic expectations and integrity checks. No test exclusion or re-blessing historical failures. |

These recommendations do not replace the detailed scope in K1–K4. In particular,
formal adoption should bind the reviewed contract and expressly address K2/K4;
the table above must not be treated as approval inferred from selected wording.

## Condition 1 — enforce knowledge before rendering

The contract already places sensing validation in `sensing_playback.py` and
knowledge projection in `client/sensing.py`. Keep the renderer downstream of
the filtered entrant view model. It must receive no hidden enemy position,
undelivered sample, future receipt, refreshed contact, hidden opponent event
or global callback-count metadata in entrant mode. Omniscient reconstruction
remains a separate explicitly selected view.

Recommended acceptance clarification for AC5–AC7: assert the projection/view-model
payload itself at request, receipt, post-movement, backward-seek and perspective
switch boundaries, without relying on drawing visibility. For identical permitted
entrant histories, changing hidden world facts or hidden opponent callbacks
must leave entrant payloads, rows, step counts and pacing unchanged. A renderer
that hides forbidden values already present in its payload does not pass.

## Condition 2 — machine-check product/research separation

Recommended supplement to the proposed demo-sidecar v1 specification:
record an explicit fixed purpose `product_teaching_demo` and input origin
`declared_product_fixture`. These are proposed product metadata, not scientific
authorization tokens. The M1 orchestration boundary should allow only the approved
alpha identity/profile, declared fixture inputs and a dedicated product output
root such as `runs/v6_alpha_m1/`, with resolved path containment checks.

Extend AC11 with negative tests that reject research Ruleset IDs, research
artifact inputs and output destinations outside the product root. Assert that
M1 entrypoints cannot import/call E8/E9 harnesses or operational controllers,
read private research seed/evidence inputs, emit authority events, consume G,
or perform research generation. Check preserved scientific inventories before
and after the fixture run; execution must create only product outputs.

A purpose label alone is insufficient: validation, call boundaries and isolation
tests must enforce it. Numeric seed equality does not transfer authority between
domains; provenance and the permitted execution path distinguish a declared
product fixture from registered scientific data. These tests verify ordinary
product isolation, without creating a new research assurance campaign.

The supplement remains a proposal for the eventual implementation scope;
it does not silently amend the independently reviewed contract or its schemas.

## Teaching priority and preservation

Prioritize the visible causal sequence: incomplete knowledge → spend one action
on SENSE → receive the historical sample at the next eligible callback → take
an informed legal action. Show the forgone action opportunity and pending receipt
clearly. Additional teaching agents and visual polish remain later work. This
demonstrates gameplay behavior; it does not establish competitive superiority
or human enjoyment. Research findings retain their scoped interpretations.

Live local baseline: `v6-research`, HEAD/upstream
`b948540aa9ef34134ff7e3c633c3acfc9f97da96`, tracked/index diffs empty.
Read-only checks matched both Seal-08 manifest pins and all 329 members, plus
exact membership, lengths and hashes for the 1,384-file original private namespace.
The reviewed documents are unchanged, with raw SHA-256:

- Contract: `504ed85c8ef2445bbab1e385dfe63d27fb35cf7a23199f1b9c50724a2f75a399`.
- Review: `f54a7fcc561aa50cc9c20967e696926b69a91d69472bb1317d8e0d7324d7f2ba`.

Future authorized changes to shared product source must retain the exact frozen
revisions and evidence; an evolved product checkout is not the original qualified
E9 instrument. No seal, authority record, consumed G or private evidence may be
altered to make product changes appear scientifically qualified.

E9 remains OPERATIONALLY BLOCKED, scientific execution LOCKED and Requirement C
NOT ESTABLISHED. Off-machine evidence recovery remains a separately outstanding
preservation risk. The contract's readiness remains **BLOCKED ON CONTRACT DECISIONS**
until explicit lead adoption of K1–K4 and separate bounded implementation authorization.

Only this recommendation note is created. No source/test changes, match execution,
scientific execution, staging, commit, push or publication.
