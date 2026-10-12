# E9 v2 Seal-06 disposition and Seal-07 planning rulings (04)

Recorded 2026-10-07 from the research lead's supplied rulings. The write-once
machine record is
`tools/research/v6/e9/v2_finding_disposition_04.json`, raw SHA-256
`d3db6c9bac4271384b933da01fa253a0c64d3249c93efa65a819d43f5ccf0839`.
The JSON contains the complete supplied ruling text and governs this mirror.
This transcription grants no authority of its own.

| Item | Disposition |
| --- | --- |
| Seal 06 | PASS WITH FINDINGS |
| Seal-06 independent reproduction | PASS, 877/877; historical sealed result, not a new run |
| S6-IQ-F1 | Seal 07 required before operational W |
| S6-IQ-F2 | Seal-07 operational blocker |
| S6-IQ-F3, F4, F5 | Record only |
| Seal-06 transcript-provenance backup | Accepted as complete for transcript-provenance purpose; preserve untouched |
| Gate-8 operational acceptance | NOT ESTABLISHED |
| Execution | LOCKED |
| Requirement C; historical coverage | NOT ESTABLISHED |
| Q | Absent |

All 325 Seal-06 manifested files were rehashed and unchanged before recording:
293 implementation files and 32 qualification files. Seal 06, its evidence,
prior records and planning revision 01 remain unchanged. No new qualification
or stronger transcript-authenticity claim is made here.

| Ruling | Recorded requirement |
| --- | --- |
| Q1 | Expand F1 to every durable regular-file read held by, or required to enter, the operational W protection. Include reachable authority reads and identify exact functions, lines and exercising tests. Authority semantics may change only for durable-file safety. |
| Q2 | Promptly reject pre-existing unsupported objects without a potentially blocking read. Preserve sealed negative-read observation. The mechanism is not yet frozen. A stat/Path.open/fstat design must explicitly retain the path-swap TOCTOU limitation and establish that concurrent hostile replacement is outside the existing threat model. A lower-level alternative needs precise observer coverage changes. |
| Q3 | No automatic stale-lock repair. Manual recovery is a separately authorized incident action after holder death/no other legitimate ownership is established, lock bytes and metadata are retained/hashed, and rationale, authorization and exact clearance are recorded. No scientific substitution or regeneration accompanies clearance. |
| Q4 | Include PASS-write interruption/torn writes. Incomplete bytes are never PASS. Recovery or prevention must respect scientific immutability and write-once rules. Return generic write-infrastructure dependencies before scope freeze. |
| Q5 | Include interrupted W-associated retention and interrupted/torn verification-result writes with F2 as one bounded producer crash-consistency problem. Enumerate every durable write boundary and retry rule. Infrastructure interruption must not become terminal scientific verification failure. |
| Q6 | Precisely supersede independent `test_s6_f3_03[outcome-1-stop]` only after eventual frozen-scope inclusion, using a new independent test-author context. Preserve Seal-06 bytes; record exact before/after bytes or hashes. Identify additional Q4/Q5 conflicts without editing them. |
| Q7 | Disposition 04 and this mirror may be written now. Create a new planning revision and return the expanded exact boundary. Do not create/freeze the Seal-07 scope record yet. |

When canonical W is complete and PASS is absent because of interruption,
recovery requires the same scientific inputs and instrument, the complete
verification, independent canonical W re-derivation and byte-for-byte equality
with retained W. It also requires no contradictory/terminal retained outcome
and **no intervening authority event, including HOLD**. Only the missing
durable continuation/PASS may then be completed. W is never rewritten, deleted
or replaced, and recovery never creates a second W or new scientific material.

An intervening event disables this exact recovery path. It does not by itself
prove scientific failure. The proposed plan applies the existing non-terminal
`REFUSED_PRECONDITION` classification; it does not invent a scientific failure
or a new outcome type.

Manual stale-lock clearance remains a future operational runbook requirement.
There is no standing permission to clear a future lock. Synthetic lock removal
does not authorize operational removal.

The revised boundary and conflict/dependency return are in
[planning revision 02](V6_E9_SEAL07_PLAN_02.md). Neither this disposition nor
that plan authorizes Seal-07 implementation, source/test edits, operational W,
REAL entropy, generation, salt, publication, Q, Gate 7, O/V/A/R/B, or any
irreversible real-study action. The Seal-07 scope record remains held.
