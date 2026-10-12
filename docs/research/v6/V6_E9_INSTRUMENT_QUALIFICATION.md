# E9 collection and analysis instrument qualification

**PASS, 2026-10-02.** The [sealed machine record](../../../tools/research/v6/e9/instrument_qualification.json)
binds the implementation and qualification tests to the accepted
[Draft 3 freeze](V6_E9_PROTOCOL_FREEZE.md). This is instrument evidence.
Requirement C remains **NOT ESTABLISHED**. Experimental seed generation and
payoff execution remain **UNAUTHORIZED**.

The protocol boundary is committed as
`6294efc7afea9d576742aaae0572d73ba904ac6b`. The accepted Draft 3 raw SHA-256 is
`fbb9cd39e723362f85e9bc38e67bb348e8e497f8fc8770a2c901dbf173d6855a`.
Its bytes and acceptance evidence are preserved in that commit.

The qualified instrument identity is **`v6-e9-instrument-v1-8ffd87671c00`**,
with digest
`8ffd87671c0057ec3f541dd4b3881820c2d50b33cc2a994ca2492eec59546ef7`.
The qualification record body digest is
`ec87aa3517d38e673da5d70a55a77c3587264049441e495fcdfbc3863910da14`;
the complete serialized record raw SHA-256 is
`01456bdda6a1b6749af2a6c7e81ea82abefcacfabe0b6cab5cc5ee38611d6d0a`.
The machine record was sealed and reproduced before this human companion.

## Validation

| Check | Final evidence |
|---|---|
| Independent instrument fixtures | 69 passed |
| Complete headless suite | 6,981 passed; 18 skipped; 3 deselected |
| Repository Ruff | PASS |
| Engine mypy | PASS; 97 source files |
| Client mypy | PASS; 16 source files |
| Freeze and instrument loader | PASS; execution remains LOCKED |
| Preserved boundaries | 47 E8 pins, 10 qualified E9 pins, 116-file engine manifest and sealed E8 result unchanged |

The independent evidence uses a separately transcribed seven-row decision
table over all 972 abstract combinations, direct hash-stream and empirical
order-statistic calculations, the qualified independent selector oracle,
and existing fixed scripted capability fixtures. No qualification fixture
enters the registered E9 sample.

Coverage includes all sixteen schedules, physical/logical alias accounting,
both seats and self/twin selection, complete block pairing, comparator
reselection and ties, exact margin and timing boundaries, endpoint clipping,
and all four interaction constraints. Identical execution copies require
matching immutable ledger and artifact provenance; different executions
cannot gain sample weight through deduplication.

## Implemented boundary

The [entry point](../../../tools/research/v6/e9/runner.py) constructs the
unchanged effective T8 request and captures result, replay and trace from
one native attempt. Completed evidence is checked against its expected
canonical match identity, recomputed result identity, raw digests, footer,
entrant ordering and terminal outcome. Frozen E8 callback/SENSE rederivation
is reused as a pure reader. Collection does not use E8's completed-cell
trace re-execution path.

Behavioral diagnostics run offline. Receipt identities bind the cell,
entrant, process, issuance callback ordinal, issue tick, normalized target
and delivery callback ordinal. Ordinals refer to the focal entrant's ordered
main-process callbacks. Undelivered verification issuances remain explicit.
Requests retain their causal receipts and disposition; commits cite the
surviving request, selector prestate, budget and cooldown. Detached action
branches share the absorbed tactical state and RNG, hold their allocations
through the registered interval, and stop at their first difference.
They consume no invented divergent feedback.

Attempt events are exclusive, hash chained and durable. An original attempt
and its supervisor evidence remain retained and digest checked. Recovery
requires the exact frozen allowlist and all outcome-blind predicates,
including known absence of completion and proven stopping or fencing.
Eligibility precedes redispatch; at most two attempts can start. Completed
results, integrity markers, uncertain workers, changed partial artifacts,
late completions and exhausted recovery fail closed. Ordinary worker errors
or exit status do not create infrastructure evidence. Missing disposable
diagnostics may be reconstructed once from intact authoritative evidence;
inconsistent diagnostics cannot be replaced.

Finalization requires the complete physical rectangle. An unusable cell
produces NOT EVALUABLE without a remaining-subset payoff analysis. Exact
seed-block arithmetic, the 20,000-resample envelope, guarded row intervals,
classification and independent historical/timing qualifiers follow Draft 3.
The final machine result is published exclusively before any interpretation.

## Audit history and remaining authorization

An earlier focused run had five failures in native request construction:
the live T8 dataclass contained frozensets that the canonical serializer did
not yet support. Sorted set serialization corrected that implementation
defect; the passing final checks include all five cases. The earlier full
suite passed 6,973 tests. Final receipt, request, provenance and corruption
audit refinements were then independently checked and the complete suite
was rerun on the final source bytes. The machine record retains both events
and their evidence digests. Qualification histories were not discarded.

The instrument implementation, tests and qualification records are committed
as a separate boundary from the protocol. The sealed machine record retains
the working-tree status at qualification time; its original bytes are unchanged.

No 900,856-cell workload or real infrastructure failure event was executed.
The recovery checker expects an external supervisor's independently
determined completion, failure and fencing evidence; uncertain or unexplained
faults remain ineligible. This qualification does not estimate infrastructure
failure rates or establish experimental performance.

Persistent study preparation and a complete approved prior-use exclusion
inventory remain prerequisites before later seed-generation approval.
The instrument contains no seed-generation command. Payoff collection and
finalization require a separate explicit execution authorization binding
the protocol, qualified instrument and independently verified seed
commitment. Neither protocol freeze nor this PASS grants that authorization.
