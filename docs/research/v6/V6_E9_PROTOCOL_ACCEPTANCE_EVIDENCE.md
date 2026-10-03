# E9 protocol acceptance and freeze authority

**Date:** 2026-10-02. **Authority:** research lead's messages in this session.
This records acceptance and freeze/implementation authorization. It authorizes
neither experimental seed generation nor payoff execution.

The research lead selected Q1: retain N=1,412 and simultaneous guarded row
intervals, use rho=0.10, and preserve the interval-width caveat. Q2 permits
strictly automatic, outcome-blind infrastructure-only recovery of the same
cell/seed/configuration, with retained failed attempts and no completed result.
Semantic, containment, invalid-action, completed-corrupt and diagnostic
failures remain non-retryable.

The research lead then instructed: “incorporate these two decisions into the
full P9 proposal, verify the decision table and recovery rules remain
consistent, record formal P9 acceptance, then perform the preregistration
freeze-readiness check.”

The complete supplied proposal, including its expressly proposed recovery cap
and allowlist, is preserved byte-for-byte as
[the supplied Q1A/Q2B proposal](V6_E9_COMPLETE_P9_PROPOSAL_Q1A_Q2B.md).
Its raw SHA-256 is
`b30f712dd8f2dc3c69fe535b26a81ad3fb075d5a883aa52cee2198ece518a677`.
Formal P9-1–P9-9 acceptance is recorded in
[Draft 3](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md).
Its unchanged raw SHA-256 is
`fbb9cd39e723362f85e9bc38e67bb348e8e497f8fc8770a2c901dbf173d6855a`.

After incorporation and the reported checks, the research lead explicitly
closed the decisions and authorized this next boundary:

> **E9’s protocol decisions are now closed.** With P9-1–P9-9 accepted and the reported freeze-readiness checks passing, no further design decision is currently blocking preregistration freeze.
> The next step is to freeze Draft 3: record its exact digest and governing identities, preserve the acceptance evidence, and commit the protocol boundary. Then implement and independently qualify the collection/analysis instrument, including recovery handling and classification boundaries.
> **Freeze does not authorize seed generation or payoff execution.** Those remain separate later approvals.
> Current status: **ready to freeze; NOT FROZEN**. Requirement C remains **NOT ESTABLISHED**.

The supplied proposal and Draft 3 retain their historical pre-freeze status
wording. The separate protocol freeze record supplies the subsequent state;
neither snapshot is rewritten to erase that acceptance history.
