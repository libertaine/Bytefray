# Bytefray V6 — E9 Observation-Driven Allocation Preregistration Draft

**Revision:** Draft 3, 2026-10-02. **P9-1–P9-9: ACCEPTED.**
**Freeze readiness: READY FOR PREREGISTRATION FREEZE.**
**Preregistration: NOT FROZEN. Analysis instrument: NOT IMPLEMENTED /
NOT QUALIFIED. Payoff execution: UNAUTHORIZED. Requirement C: NOT ESTABLISHED.**

This pass incorporates the research lead's complete P9 proposal with Q1/Q2,
checks it against the current capability boundary, and records the formal
acceptance already authorized by the research lead. Acceptance includes the
explicit recovery cap and allowlist in §11. It does not issue a protocol
freeze identity, implement an instrument, materialize evaluation packages,
generate experimental seeds or authorize matches.

Draft 3 supersedes Drafts 1/2 and their missing-proposal freeze holds.
The [D9 design directions](V6_E9_DESIGN_DECISIONS_AND_PREREGISTRATION_READINESS.md)
remain unchanged. All prospective rules are in §§3–11; the check and
remaining boundaries are recorded in §13. No field may be filled from E9
outcomes or changed during implementation without a reviewed protocol revision.

## 1. Question, scope and existing evidence

The question is whether legally observation-driven within-match allocation
revision provides practical benefit beyond competent constant allocations
and the declared precommitted schedule panel on unchanged T8 mechanics.
A policy merely behaving differently does not answer that question.

The claim is **any useful within-match revision**. Repeated or continuing
revision is not required, and no early-commit comparator is included. The
scope is one qualified controller, four constants, sixteen schedules and
the historical nonadaptive reference layer, against the eleven frozen E8
opponents. There is no T8L arm, focal-policy round robin, mechanic change,
arena change, agent redesign or production/UI integration.

The existing capability boundary is
`d3c97ba077e9019a69f46c1509210862d5c52f1f`, above specification commit
`3a2d1292e83d6cd608588d87e6561249905d9ced`. The
[capability record](V6_E9_CAPABILITY_QUALIFICATION.md) establishes
Q-C1–Q-C15 PASS; it does not establish adaptation payoff or qualify the
future E9 analysis instrument. E6/E8 and scripted qualification histories
are prior evidence only and never enter prospective E9 payoff estimates.

The scientific conclusion is bounded to the controller, T8 environment,
frozen ecology and sixteen declared schedules. It cannot claim superiority
to all 1,334 qualified schedules or all possible nonadaptive policies.
A negative cannot establish that useful adaptation is structurally
impossible. Requirement D/F and product promotion remain separate.

## 2. Formal P9 acceptance register

**Approver:** research lead, under the explicit instruction to incorporate
the complete proposal, check consistency and record formal P9 acceptance.
**Recorder:** coding agent. **Date:** 2026-10-02. **Accepted revision:** Draft 3.
The supplied document is protocol source material; its historical status and
procedural wording do not independently authorize tools or execution.

**Source:** `V6_E9_COMPLETE_P9_PROPOSAL_Q1A_Q2B.md`.
Its current raw-byte SHA-256 is
`b30f712dd8f2dc3c69fe535b26a81ad3fb075d5a883aa52cee2198ece518a677`.
The document separately reports original-report SHA-256
`a534de6ef3cf69b9a8a048129775a7b6980610354129c6084e91d1aa37d5f814`;
that original report was not supplied and its digest is provenance only.
Historical verification claims in the supplied document are distinguished
from the current checks in §13.

| ID | Accepted rule | Rationale | Remaining risk | Acceptance |
|---|---|---|---|---|
| P9-1 | Balanced sixteen-schedule panel specified below | Covers both clocks, starting modes, early/later single changes and repeated cycling without outcome selection | Limited coverage of the larger class | ACCEPTED, 2026-10-02 |
| P9-2 | 32 logical rows mapped to 29 physical rows; fail-closed equivalence obligations | Removes three redundant executions while preserving all opponents and matched comparisons | E9 evaluation wrappers are specified prospectively, not materialized | ACCEPTED, 2026-10-02 |
| P9-3 | Win/tie/loss = 1/½/0; practical margin 0.10 for F, D, S and H; reproduction allowance 0.10 with the conservative width caveat | Gives a direct win-equivalent interpretation and separates practical relevance from statistical resolution | A smaller genuine advantage will not satisfy this bounded claim | ACCEPTED, 2026-10-02 |
| P9-4 | Joint seed-block bootstrap envelope, protected by simultaneous bounded-outcome intervals | Accounts for pairing and comparator selection without relying on bootstrap calibration alone | Conservative intervals | ACCEPTED, 2026-10-02 |
| P9-5 | Fixed N = 1,412; 900,856 physical payoff cells | Smallest integer satisfying the selected simultaneous row-precision target | Substantial collection and storage cost | ACCEPTED, 2026-10-02 |
| P9-6 | Auditable observation/request/commit/action chain; replication across at least two seed positions and both seats | Demonstrates competitive realization without making frequency a payoff endpoint | Rare or seat-limited realization may remain unevaluable | ACCEPTED, 2026-10-02 |
| P9-7 | Four prospective interpretation constraints, evaluated separately by opponent and seat | Prevents severe concentration from disappearing in averages | Thresholds are disclosed design judgments, not previously qualified empirical cutoffs | ACCEPTED, 2026-10-02 |
| P9-8 | Ordered, exhaustive table with independent historical and timing qualifiers | Separates behavior, benefit, timing alternatives and competitive context | Wording must preserve the qualified scope | ACCEPTED, 2026-10-02 |
| P9-9 | Complete rectangle; resume provably unstarted cells; at most one automatic infrastructure-only recovery attempt per eligible cell | Prohibits discretionary replacement and favorable-subset analysis while preserving the fixed rectangle after independently evidenced infrastructure interruption | Recovery machinery requires qualification; one unrecoverable required cell still invalidates the registered result | ACCEPTED, 2026-10-02 |


All nine acceptances bind the exact identities, recipes, inequalities,
diagnostic rules and recovery predicates incorporated below. Q1 retains
N=1,412 and guarded simultaneous row intervals, with rho=0.10 and the
interval-width caveat. Q2 selected the recovery direction; this formal P9
record additionally accepts the supplied one-recovery/two-start cap,
complete external-infrastructure allowlist and operational predicates.

The freeze-readiness predicate is satisfied only when every rule is
explicit, the schedule/alias identities agree with the qualified scope,
the ordered table assigns a unique primary label and the cross-decision
checks pass. Acceptance and a passing readiness check are separate from
issuing the protocol freeze identity/digest.

## 3. Environment, logical rows and identity/alias ledger — P9-2

Use unchanged T8, `bytefray-rules-6-research-sensing-active-w27`: arena 512,
1,000-tick limit, Q=8, chunk=2, rotating forward order, capture hold K=1,
active sensing half-width 27 and whole-tick disruption. Preserve the
[E8 family freeze](V6_E8_FAMILY_FREEZE.md) and
[approved tactical/controller contract](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md).

The adaptive row A retains initial DENSE, C=2, L=2, B=4 and cadences 1/4.
The selectors gain no seed, identity, artifact, terminal-outcome or hidden
engine-state input. Fixed, disabled and scheduled variants retain the common
tactical executor, contact memory, legal observations and RNG ordering.

The matched constant set F is OFF, DENSE, MEDIUM and SPARSE. D is the
initial-DENSE adaptation-disabled control; S is S01–S16; H is the ten
historical nonadaptive focal rows. ADAPT8 is an opponent, never a member
of F or H.

### Existing implementation and prospective package binding

The current repository contains qualified modules and a [scratch-package factory](../../../tools/research/v6/e9/packages.py). It does **not** contain a materialized, frozen E9 evaluation roster.

Use those existing modules without behavior changes. Bind them by the capability commit and these verified raw hashes:

| Source | SHA-256 |
|---|---|
| `policy.py` | `1e30b4b985fd726c4ffa13e424fbc795a05171d44e8b8c7c5fd381fc13516b81` |
| `selectors.py` | `541fa6fd31b874c8a48a4fa1a26ecd6988a3c36edd8a4b1a45e40da198ca2cd8` |
| `packages.py` | `a87090ec6fdda53c376ce4231af1694e3f7f6327a9e11b24128fc519845ad314` |
| `tactics.py` | `369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc` |

The prospective E9 wrappers use the existing factory’s exact template: UTF-8 without BOM, Windows CRLF, its existing import lines, manifest fields and factory body. Package names and configuration expressions are fixed below. No parameter overrides are permitted.

For schedules, the exact configuration expression is:

```text
Variant(kind="schedule", schedule=Schedule(Mode.<INITIAL>, <TUPLE>, "<CLOCK>"))
```

Use the ledger’s initial mode and clock, Python tuple formatting with a trailing comma for singletons, and spaces after tuple commas. This fixes prospective bytes without creating packages now. Materialization must reproduce these bytes and record raw hashes before execution.

### Logical-to-physical mapping

| Logical row | Qualified configuration or historical identity | Physical evaluation artifact |
|---|---|---|
| A | `Variant()` | Prospective `e9_a` wrapper |
| OFF | `Variant(kind="fixed", mode=Mode.OFF)` | Frozen RUSH8 primary, `e8_q21` |
| DENSE | `Variant(kind="fixed", mode=Mode.DENSE)` | Frozen REACQ8 primary, `e8_q19` |
| MEDIUM | `Variant(kind="fixed", mode=Mode.MEDIUM)` | Prospective `e9_medium` wrapper |
| SPARSE | `Variant(kind="fixed", mode=Mode.SPARSE)` | Prospective `e9_sparse` wrapper |
| D | `Variant(kind="disabled", mode=Mode.DENSE)` | Same physical REACQ8 row as DENSE |
| S01–S16 | Exact ledger configurations | Prospective `e9_s01`–`e9_s16` wrappers |
| Ten H rows | Frozen historical primaries below | Their unchanged historical packages |

A retains initial DENSE, C=2, L=2, B=4 and cadences 1/4. New matched variants retain the qualified tactical defaults: spatial-fast acquisition, attack posture, evasion off, stress false, one `main` process, share 1 and reach 256.

Historical artifacts are bound to the complete entries in `family_fingerprints.json`, their manifest-resolved defaults and the frozen family identity `v6-e8-family-v1-981fc8b12beb`.

### Historical references and opponents

All eleven members remain opponents, each weighted **1/11**. The H column identifies the ten nonadaptive focal reference rows.

| Member | Primary | Twin | H row? | Frozen defaults: acquire / reacquire / posture / evade / processes / stress |
|---|---|---|---|---|
| RUSH8 | `e8_q21` | `e8_q10` | Yes | spatial-fast / once / attack / off / 1 / false |
| REACQ8 | `e8_q19` | `e8_q03` | Yes | spatial-fast / repeat / attack / off / 1 / false |
| PACED8 | `e8_q09` | `e8_q05` | Yes | spatial-paced / once / attack / off / 1 / false |
| STEALTH8 | `e8_q04` | `e8_q20` | Yes | ownership / once / attack / off / 1 / false |
| LURK8 | `e8_q08` | `e8_q11` | Yes | none / none / attack / off / 1 / false |
| SPLIT8 | `e8_q07` | `e8_q17` | Yes | spatial-fast / once / attack / off / 2 / false |
| GUARD8 | `e8_q13` | `e8_q18` | Yes | spatial-fast / once / guard / off / 1 / false |
| EVADE8 | `e8_q15` | `e8_q02` | Yes | spatial-fast / once / guard / on-hit / 1 / false |
| GREED8 | `e8_q01` | `e8_q06` | Yes | none / none / paint / off / 1 / false |
| STRESS8 | `e8_q22` | `e8_q12` | Yes | none / none / guard / off / 1 / true |
| ADAPT8 | `e8_q16` | `e8_q14` | No | spatial-fast / adaptive / attack / off / 1 / false |

For historical focal h against opponent j:

- Use h’s primary as focal.
- Use j’s primary when `h ≠ j`.
- Use h’s twin as opponent when `h = j`.
- Execute both focal seat orientations.
- Apply this same self/twin mapping to OFF/RUSH8 and DENSE/D/REACQ8 aliases.

New A, MEDIUM, SPARSE and schedule rows face opponent primaries throughout. There is no focal ADAPT8 row.

Entrant IDs are the stable seat IDs A and B. Package names must not alter RNG derivation or enter selectors. SPLIT8 retains its frozen `sensor`/`striker` declarations and shares.

### Equivalence obligations

| Equivalence | Required evidence | Type | Failure disposition |
|---|---|---|---|
| OFF ↔ RUSH8 | Qualified Q-C1 evidence, unchanged source pins, correct once/repeat configuration, exact declarations, action and RNG agreement under equivalent legal histories | Behavioral; package bytes differ | Stop preparation; no payoff collection |
| DENSE ↔ REACQ8 | Same obligations, including verification delivery, search, core handling and RNG order | Behavioral; package bytes differ | Stop preparation |
| D ↔ DENSE | Qualified Q-C2 evidence; shadow requests never change actions, tactics, RNG or cadence | Behavioral; selector diagnostics differ | Stop preparation |

Byte identity of the tactical copy is necessary evidence, but does not alone establish wrapper equivalence.

The current capability evidence is reusable only because its exact source hashes match. Prospective wrapper binding must be checked against that evidence. The disabled shadow state may be reconstructed as detached diagnostics; it cannot affect the physical REACQ8 execution.

Consolidation is fixed prospectively. An equivalence failure does **not** silently switch the experiment to 32 physical rows. Resolving such a failure would require a reviewed protocol revision before seeds.

### Counts and weighting

- Logical rows: `1 + 4 + 1 + 16 + 10 = 32`.
- Alias reductions: OFF/RUSH8, DENSE/REACQ8, D/DENSE.
- Physical rows: **29**.
- Prospective new physical packages: **19**.
- Historical physical focal packages: **10**.
- Additional required equivalence/twin **match executions: 0**; existing qualified evidence plus exact artifact binding supplies these obligations. No new qualification match is authorized here.

Aliases share observations; they do not multiply opponent weight, bootstrap coordinates or independent sample count. Separately planned reciprocal cells may also duplicate deterministic trajectories; report that duplication without treating it as additional independent evidence.

### Prospective wrapper byte commitments

The following raw-byte SHA-256 commitments were calculated in memory from
the pinned factory template, accepted configuration expressions and explicit
Windows CRLF encoding. No package was materialized. Future materialization
must match both this table and the recipe; these are prospective byte
commitments, not qualification of an evaluation roster.

| Package | agent.py SHA-256 | agent.yaml SHA-256 |
|---|---|---|
| `e9_a` | `c0f92445825d2a64e0691aa5d1417ba9964d35da22a43b5be8f4844749b62c58` | `977b2292e2373b15c5fd4abc6b8fc1fa372407d1ac18a2446705238e9a0e9a70` |
| `e9_medium` | `a1d95b8dcfa097bd368693d61548b9ee87444da7f489138cdb3bb22fef9cc318` | `22b46c2cab9d856cf46cc76427b6027aacec375e806d5c0422accba0c6fd9d6b` |
| `e9_sparse` | `257498af3187f415437e34552d8883298562fa0b22b705a2f81086e1390bfd6b` | `7161118a0cee2cd5ab01111b7316f0b9b8f9dbadb2daf6cb0d00a46511d68ec3` |
| `e9_s01` | `70c5b4bf205ab5569eb93529fd48f4908d93989f830cf8da905bf214f69af672` | `3061ba77a50304719f1daf0bfea46634f3fbc0500c3f812d7a643c7b1fe1e123` |
| `e9_s02` | `83ccabef1c5c20ce46209503b8819087d19b7869d920daac3869cafaf3448099` | `346710e746f103ea149226e1a324db45ba1277d9424ea3d4afd5b2051040c265` |
| `e9_s03` | `7c09e9e7f37a76c3386e960194d54d881a9ec4e9961733855fd440ea40aa7c09` | `7d86564d82964f9fa5e81bb0d361e40572544b3b9b5855dd0a01ec63e13761a5` |
| `e9_s04` | `304e1fdb6c07c8db492a5db926035f2d1ac67253c3c03e10fa4b3e7ef907180e` | `4dcea7c2b19f16f4f2b428ca3e6c78eceb056d8de0c6e65ee43d01f9fccee0b2` |
| `e9_s05` | `2c4d3743961ee69cdfe34f49fd053ccdf9b5d90259c96047552414925b0c58ef` | `46c6eab0debd009113f6f45e9450ccf4b96af787225aeaeeb458880749e52e9f` |
| `e9_s06` | `f4469452e341dd163f20798c703fc8d3600e661fe5fc14d7cd332672a86d735c` | `3e5d055b4ecadceb17ecb84d51dde03e0ccc0d0595444f16dd27a691c16f662f` |
| `e9_s07` | `72f11ba958187d9bdc27c4c741ce7a92bdebc65596e9c9251ffc6c5b093cfc33` | `37bfb877600519b457628a44ed91216feeb7cc4cc1494d26744faa2380d53ee7` |
| `e9_s08` | `4e24f75c1a01a9a4796a5874834451c0f1b45b07471b028ce17b536c0a6af616` | `c02797e9bec107a9fc2c8cf549b1a91815ef4b88869fe6c3fd0e36410e5bb0ca` |
| `e9_s09` | `b80d21160dddedbcfeff950d89fb3d14908f40a486ecdfef89fc017b40b456b3` | `70877114fb97f01a8b92b9afa18f70d20cc4f0478c051491af9ddbf9d84fa941` |
| `e9_s10` | `bbc329d6737bc67750d21c45c2df36c894dc27766f8a419253f787b6f04c5061` | `7283cee9bbe96ee543aaef3850c545cc55cb33448375b841b246a95890a205cd` |
| `e9_s11` | `7bf3efe173e9a767d2234b99a4cacf5dfa269b000a6d9a2d25272dc4d7f2be92` | `ece545f1ce73bf402c69477bcea7946363b5c15bc27be04d08a69fa3f18b2856` |
| `e9_s12` | `2569256be84551f68f68d482a074c12db6afb9bc91598de9f0dfe56e439e4f7a` | `6307286d13e28168fbc2a0b6607b38ecc63c68af710d13bdfee2746812d7e91f` |
| `e9_s13` | `e9c81903307f225c7733a879baa205b8e01878cd4f7e76ff9187b48fd6a17da7` | `2ef595b71388ef680395007ddbbccb69ef76dac3d5d0ee0bc5a5858655f6ae48` |
| `e9_s14` | `8c431fc8dec0d3e82fc7d1c3454eda96da461d5d95d764ed6d03df818113a7c5` | `77c1dcb539b59f6c9a384f34a81f7a688837f63eb2d08b39016d8866344adb8e` |
| `e9_s15` | `981c816467530625fbee7a7354974c60817231b35faf4e7615e632e04588fe5f` | `cb92c4a0b854ccfe20313517a10ac3dae566f8804448a6d30e8138a9f6ee76e5` |
| `e9_s16` | `4eff7e70925a52b758ecf32005b0a359a40d0acfd58438ac99479c6011a17a7e` | `d76a89af8f3c0cca67826d28b0343be8c95394a6977cc9f0d179238ee4cd0202` |

## 4. The sixteen-schedule identity ledger — P9-1

Times are relative to activation, using the selected clock. Boundaries specify **planned toggles**, not guaranteed realized revisions.

| ID | Clock | Initial mode | Complete boundary tuple | Planned revisions | Inclusion rationale |
|---|---|---|---|---:|---|
| S01 | opportunity | DENSE | `(2,)` | 1 | Earliest permitted one-way downgrade |
| S02 | opportunity | DENSE | `(128,)` | 1 | Later one-way downgrade |
| S03 | opportunity | DENSE | `(2,4,6,8)` | 4 | Earliest rapid repeated cycling |
| S04 | opportunity | DENSE | `(16,24,27,35)` | 4 | Delayed cycling with unequal dwell times |
| S05 | opportunity | SPARSE | `(2,)` | 1 | Earliest permitted one-way promotion |
| S06 | opportunity | SPARSE | `(128,)` | 1 | Later one-way promotion |
| S07 | opportunity | SPARSE | `(2,4,6,8)` | 4 | Rapid cycling with reversed initial allocation |
| S08 | opportunity | SPARSE | `(16,19,27,30)` | 4 | Unequal-dwell cycling with reversed initial allocation |
| S09 | wall | DENSE | `(2,)` | 1 | Absolute-time counterpart of S01 |
| S10 | wall | DENSE | `(128,)` | 1 | Absolute-time counterpart of S02 |
| S11 | wall | DENSE | `(2,4,6,8)` | 4 | Rapid wall-time cycling |
| S12 | wall | DENSE | `(16,24,27,35)` | 4 | Delayed unequal-dwell wall cycling |
| S13 | wall | SPARSE | `(2,)` | 1 | Absolute-time counterpart of S05 |
| S14 | wall | SPARSE | `(128,)` | 1 | Absolute-time counterpart of S06 |
| S15 | wall | SPARSE | `(2,4,6,8)` | 4 | Rapid wall cycling with reversed initial allocation |
| S16 | wall | SPARSE | `(16,19,27,30)` | 4 | Unequal-dwell wall cycling with reversed initial allocation |

Membership witnesses under the [qualified schedule contract](../../../tools/research/v6/e9/selectors.py):

- Single-change plans use `a=2` or `a=128`, `k=1`.
- Rapid plans use `a=2`, `h=l=2`, `k=4`.
- Unequal-dwell plans use `a=16`, `h=3`, `l=8`, `k=4`.
- All clocks, initial modes, starts, dwells and revision counts belong to the approved domains.

The enumeration check returned **16 identities, 16 unique identities, all qualified**.

The panel includes a non-power-of-four dwell, reducing exclusive reliance on cadence-aligned timing. Opportunity and wall schedules can diverge under suppression; they remain distinct identities even when particular matches produce identical trajectories.

This is a balanced, prospectively chosen panel. It supplies credible timer alternatives, but does not cover every dwell, start time, revision count or qualified schedule. No conclusion may claim that all 1,334 schedules were beaten.

## 5. Payoffs, estimands and practical benefit — P9-3

### Per-match payoff

For a valid, fully bound terminal record:

\[
Y=\begin{cases}
1 & \text{focal entrant is the authoritative winner}\\
1/2 & \text{authoritative outcome is a tie}\\
0 & \text{opponent is the authoritative winner}.
\end{cases}
\]

This encoding is selected explicitly because its mean measures win-equivalent success. A win contributes twice a tie. It is not adopted merely because E8 used it.

| Terminal class | Handling |
|---|---|
| `last_agent_standing` | Encode its validated authoritative winner |
| `tick_limit` | Encode the unchanged T8 score-resolution outcome; tick limit does not automatically mean tie |
| `all_agents_dead` | Encode the validated authoritative terminal outcome; do not infer payoff from the reason string alone |
| Valid `normal_halt` entrant metadata | Use the resulting validated match outcome |
| Invalid action, exception, malformed forfeit or containment failure | Integrity rejection, outside payoff encoding |
| Unknown termination class, inconsistent winner, corrupt or incomplete artifacts | Integrity rejection |

Preserve the [existing result/winner contract](../../RESULT_SCHEMA.md). No E9-specific scoring or winner override is introduced.

### Objective and gaps

\[
X_{p,s}=\frac1{22}\sum_{j=1}^{11}\sum_{z\in\{A,B\}}Y_{p,j,s,z},
\qquad
U_p=\frac1N\sum_{s=1}^{N}X_{p,s}.
\]

\[
\begin{aligned}
g_F&=U_A-\max_{f\in F}U_f,\\
g_D&=U_A-U_D,\\
g_S&=U_A-\max_{q\in S}U_q,\\
g_H&=U_A-\max_{h\in H}U_h.
\end{aligned}
\]

There is no per-opponent hindsight selector in these primary estimands.

| Contrast | Role |
|---|---|
| F and D | Required matched evidence for attribution to allocation revision |
| S | Required exclusion of the declared timing alternatives |
| H | Separate competitive context; required additionally for broader “outperforms the best fixed policy” wording |

### Practical benefit

Choose a common margin:

\[
\delta_F=\delta_D=\delta_S=\delta_H=0.10.
\]

Units are mean win-equivalent payoff points. A 0.10 increase corresponds, for example, to one additional loss-to-win conversion per ten equally weighted matches, or two loss-to-tie conversions.

This is a substantive threshold for the bounded benefit claim. Smaller effects remain reportable but cannot establish that claim.

For each simultaneous interval \([L_g,U_g]\):

| Status | Exact rule |
|---|---|
| Practical benefit supported | \(L_g\ge0.10\) |
| Practical benefit refuted | \(U_g<0.10\) |
| Unresolved | Otherwise |

Thus:

- Positive statistical separation from zero does not establish practical benefit.
- A precisely estimated positive gain below 0.10 refutes this specified practical claim.
- `U = 0.10` remains unresolved unless `L ≥ 0.10`.
- `L = 0.10` supports the margin.

### Timing reproduction

Choose a noninferiority allowance \(\rho=0.10\), equal to the benefit margin, as accepted in Q1.

Schedule q reproduces or improves on A’s fixed-control gain only when:

\[
L\!\left(U_q-\max_{f\in F}U_f\right)\ge0.10
\quad\text{and}\quad
U(U_A-U_q)\le0.10.
\]

Apply **timing explanation unresolved** when F and D benefit are supported and at least one schedule satisfies both conditions.

This requires a practically beneficial schedule and an uncertainty bound establishing that it is within 0.10 of A or better. Failure to reject a difference is insufficient. Equality at either boundary qualifies.

**Accepted width caveat:** This remains a conservative interval test, not a test of observed-payoff proximity. For equal observed A/schedule means and unclipped row intervals, the upper contrast bound is 2r. Thus equal observed means satisfy the reproduction bound only at r=0.05; bootstrap widening prevents that result. Clipping at payoff endpoints can reduce effective widths, so the actual clipped bounds in §6 always govern. No exception or post-hoc widening of rho is allowed.

## 6. Joint seed-block uncertainty — P9-4

Use a **joint seed-block bootstrap envelope with a finite-sample bounded-outcome guard**.

The guard avoids treating bootstrap behavior near tied comparator maxima—or a degenerate empirical sample—as sufficient justification for narrow confidence intervals.

1. Construct the 29 physical row vectors \(X_{p,s}\) from the complete rectangle.
2. Use **20,000 resamples**, each containing N seed positions sampled with replacement.
3. Within a resample, use the same sampled position multiset for every row, opponent and seat.
4. Recompute every row mean and the strongest F, S and H comparators in every resample. Recompute D and every schedule-reproduction quantity too.
5. For resample b, calculate:
   \[
   e_b=\max_{p\in P_{\rm physical}}|U_p^{*(b)}-\widehat U_p|.
   \]
6. Sort these 20,000 values. Set c to the **19,000th value**, using one-based indexing. No quantile interpolation.
7. Set the common row half-width:
   \[
   r=\max(0.05,c).
   \]
8. Form row intervals:
   \[
   \ell_p=\max(0,\widehat U_p-r),\qquad
   u_p=\min(1,\widehat U_p+r).
   \]
9. Derive all contrast intervals from those same simultaneous row intervals.

For comparator set G:

\[
L_g=\ell_A-\max_{p\in G}u_p,\qquad
U_g=u_A-\max_{p\in G}\ell_p.
\]

For a single comparator, use ordinary interval subtraction. For schedule q’s benefit over F:

\[
L_{q-F}=\ell_q-\max_{f\in F}u_f,\qquad
U_{q-F}=u_q-\max_{f\in F}\ell_f.
\]

These bounds accommodate uncertainty in which comparator is strongest. They do not condition on the observed winner.

The bounded guard supplies simultaneous coverage of at least 95% for the 29 row means under the specified uniform seed sampling:

\[
\Pr\{\exists p:|\widehat U_p-U_p|>0.05\}
\le58e^{-2N(0.05)^2}.
\]

The underlying bounded-mean result also applies conservatively to uniform sampling without replacement. [Hoeffding’s original paper](https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830)

The bootstrap can widen these bands; it cannot remove the guard. Consequently, the decision-level guarantee does not depend on claiming exact finite-sample coverage for an ordinary bootstrap percentile interval.

### Deterministic analysis randomization

After instrument qualification, define:

```text
K = SHA256(
    UTF8("bytefray-e9-analysis-bootstrap-v1\n")
    || UTF8(protocol_digest_hex + "\n")
    || UTF8(qualified_instrument_digest_hex + "\n")
)
```

For a global counter starting at zero:

- Hash `K || uint64_be(counter)`.
- Interpret its first eight bytes as an unsigned 64-bit integer v.
- Accept when `v < floor(2^64/N) × N`; otherwise increment the counter and reject that draw.
- The accepted position is `v mod N`, indexed from zero.
- Consume accepted draws in resample-major, then draw-major order.
- Counter exhaustion is an analysis failure.

No payoff digest, experimental seed value or analyst-selected random seed enters this derivation.

### Ties and arithmetic

- Comparator maxima retain **all exactly tied members**.
- Display one representative only by ascending registered ID; this never changes estimates or decisions.
- Payoffs, means, bootstrap errors, interval bounds and inequalities use exact rational arithmetic.
- Alias rows resolve to the same rational value.
- Display decimals to six places using round-half-even; displayed rounding never controls a decision.

The independent evidence count remains **N seed positions**. Matches, callbacks, revisions, both seats and repeated trajectories are not additional independent draws.

## 7. Fixed sample, fresh seeds and exposure — P9-5

### Fixed sample

Choose **N = 1,412**.

The prospective precision target is a simultaneous bounded-outcome row half-width of 0.05 across 29 physical rows. The minimum integer satisfying the selected bound is:

\[
N=\left\lceil
\frac{\log(58/0.05)}{2(0.05)^2}
\right\rceil=1412.
\]

At this N, the family error bound is approximately **0.0498091**.

This is design-stage arithmetic using bounded outcomes. No historical variance estimate, E9 outcome or synthetic payoff simulation was used. The bootstrap may widen the final bands.

| Accounting item | Count |
|---|---:|
| Physical rows | 29 |
| Opponents | 11 |
| Focal orientations | 2 |
| Fresh seed positions | 1,412 |
| Physical payoff cells | **900,856** |
| Logical cells before alias deduplication | 994,048 |
| A payoff cells / behavioral match denominator | 31,064 |
| Explicit historical primary/twin cells, included above | 28,240 |
| Additional equivalence/twin matches | 0 |

This N is minimal for the stated bounded-precision criterion, not a claim that no cheaper approximate procedure exists. Its main risk is collection cost.

### Generation and exclusion

After the later authorization boundary:

- Draw unsigned 64-bit candidates from the operating system CSPRNG.
- Interpret eight bytes in big-endian order.
- Domain: integers from 0 through \(2^{64}-1\).
- Reject previously accepted values and values in the frozen prior-use exclusion inventory.
- Assign positions in accepted draw order; do not sort by value.
- Continue until exactly 1,412 unique accepted values exist.

The exclusion inventory must cover E6 and E8 experimental match seeds and all prior qualification **match seeds**, including harness defaults and derived match-seed selections. Policy RNG substream values are not match seeds.

Build and verify this inventory before generation. Its provenance must identify the source records and qualification coverage. If completeness cannot be established, generation stays locked.

### Commitment and private storage

Use a canonical private JSON payload containing:

- protocol and instrument digests;
- domain and generation specification;
- exclusion-inventory digest;
- positions 1–1,412 and their values encoded as sixteen lowercase hexadecimal digits.

Canonical serialization is UTF-8 without BOM, sorted object keys, compact separators and one final LF.

Generate a separate 32-byte CSPRNG salt at the authorized generation boundary. Publish:

\[
C=\operatorname{SHA256}
(\text{UTF8("bytefray-e9-seed-commitment-v1\n")}
\Vert \text{salt}
\Vert \text{canonical payload bytes}).
\]

The public commitment record contains C, N, generation rules, exclusion provenance commitments and the bound protocol/instrument identities. It contains no literal seeds or private corpus paths.

Use one ignored private root beneath repository `runs/`; determine its directory name from a domain-separated hash of the protocol and instrument digests. Record its resolved path only privately. Verify ignore status and absence from tracked/staged/exported files before writing values.

An independent verifier checks the canonical payload, commitment, count, uniqueness, domain, exclusion and ordering privately. Public verification records expose only status, counts and commitments.

### Unlock sequence

1. Record acceptance of P9-1–P9-9.
2. Freeze the complete protocol.
3. Implement and independently qualify the analysis/collection instrument.
4. Bind materialized evaluation artifacts and complete the exclusion inventory.
5. Obtain explicit seed-generation authorization.
6. Generate, privately verify and publish the commitment.
7. Obtain the applicable payoff-execution authorization.
8. Unlock the committed list to the runner; selectors remain unable to access it.
9. Complete the fixed rectangle or apply P9-9.

No extension, optional stopping, replacement positions or sample-size adjustment is permitted. No seed values are generated by this decision pass.

## 8. Realized adaptation gate — P9-6

### Legal causal evidence

A triggering observation must originate from an authoritative applied **verification** SENSE:

- Correct entrant/process and pending-action association.
- Issued target normalized modulo 512.
- Canonical returned anchor tuple.
- Delivered through the corresponding callback.
- Consumed once at the qualified first-callback revision boundary.
- Freshness exactly as qualified: issue tick is the boundary tick or immediately preceding tick.

Target present gives CONFIRM; target absent, including an empty tuple, gives MISSING. Refused sensing, absent callbacks, nonverification sensing and stale selector evidence do not create a trigger.

A downgrade cites the same-target confirmations that establish C=2. A promotion cites the MISSING that establishes the pending high request.

### Request and delayed-commit identity

Assign each reconstructed request:

```text
(cell identity, request ordinal, requested mode, causal receipt identities)
```

Receipt identities include entrant, process, issuance callback ordinal, issue tick, target and delivery callback ordinal.

A request remains associated with its causal evidence while waiting for cooldown. Reconstruct cancellation, supersession and satisfaction from the qualified transition contract. A commit must cite the surviving request, its selector prestate, budget and cooldown state.

A timer expiration without such provenance cannot count as observation-driven behavior.

### Action-consequence diagnostic

For each actual committed revision:

1. Clone the focal state after common observation absorption and immediately before the mode commit.
2. Preserve identical tactics, contact/search state, callback bookkeeping and RNG state.
3. In one detached branch apply the committed mode; in the other retain the precommit mode.
4. Hold those allocations while replaying the authoritative callback history.
5. Stop at the first normalized action difference, before the next actual committed revision, or at termination.
6. Before a difference, both branches must reproduce the shared actual actions; the committed branch must reproduce the actual execution.
7. Count realization only when a legal eligible action differs because of allocation: action kind, normalized operand/value or action availability.

This is an offline diagnostic. It executes no new live match and supplies no information to the policy. Once the branches choose different actions, stop; do not feed the divergent branch invented future feedback.

The horizon is the revision’s complete holding interval: the committing callback, inclusive, through the callback before the next commit or termination. The existing 1,000-tick match limit supplies the outer bound. There is no additional arbitrary short horizon.

Revision intervals are disjoint. The first qualifying difference belongs to that interval’s revision; an action cannot realize two revisions.

An independent selector reconstruction must also verify that the request follows the causal receipt sequence. A diagnostic withholding of the triggering receipt sequence must remove that request while clocks and other selector inputs remain fixed. This intervention establishes selector dependence; it is not claimed to be another legal live-world trajectory.

### Counts and threshold

Report:

- realized revisions / all committed revisions;
- realized-match count / **31,064 A matches**;
- distinct seed positions with at least one realized revision / **1,412**;
- all counts by opponent and seat.

Let K be the distinct realized seed-position count and \(K_A,K_B\) the seat-specific counts.

The registered gate is:

\[
K\ge2,\qquad K_A\ge1,\qquad K_B\ge1.
\]

This requires minimal replication and realization in both seat orientations. It does not require repeated revisions in a match, multiple opponents or a payoff-dependent realization rate.

| Case | Treatment |
|---|---|
| No discovery | Match remains in the full incidence denominator; no realization |
| No eligible request or revision | Same; report reason |
| Search or tactical priority masks revision | Not realized unless a later action differs within its holding interval |
| Callback suppression | No invented action, observation or opportunity |
| Termination before consequence | Committed but unrealized |
| Repeated revisions | Audit separately; unique ownership by holding interval |
| Selector-state change without action difference | Unrealized |
| No committed revisions | Revision fraction is not applicable; full match/seed incidence remains zero |
| Incomplete diagnostic evidence | Integrity failure, never denominator exclusion |

Complete valid data with zero realized revisions follow the explicit refutation path in §10. Positive realization that fails the replication/seat threshold follows the insufficient-coverage path.

## 9. Interaction constraints — P9-7

These are prospective **interpretation constraints**, not new mechanics or tests that diagnose engine defects.

Evaluate each opponent/seat stratum and the equal-weight aggregates. Any qualifying stratum flag survives aggregate averaging. Report denominators and insufficient exposure.

For local payoff diagnostics, the strongest F comparator may be selected within the specified stratum. This is a registered interpretation diagnostic, not a replacement primary objective. Evaluate all tied strongest comparators.

| Constraint | Metric, denominator and comparator | Severe threshold | Minimum evidence | Consequence |
|---|---|---|---|---|
| Seat dependence | For each opponent and for the whole ecology, \(g_z=\bar Y_{A,z}-\max_F\bar Y_{f,z}\). Each opponent/seat mean uses N cells | One seat has \(g_z\ge0.10\), the other \(g_{z'}\le-0.10\) | Complete N in both seats | Block aggregate support; identify seat restriction |
| Stalling/tick-limit concentration | A tick-limit proportion τ; paired difference to strongest local F. Decompose that gap into contributions from A tick-limit and other cells, both divided by the full stratum denominator | τ≥½, gap≥0.10, and non-tick-limit contribution≤0 | Complete stratum; the majority condition supplies at least half its observations | Block support; qualify gain as tick-limit-dependent |
| Immunity/capture pathology | For each victim direction, exposed seed positions receive at least two applied hostile writes to each of the eight fixed core cells during the match. Compare capture outcomes with matched F executions at those positions | No victim captures among exposed A cells; at least half end at tick limit; some F comparator captures the corresponding victim in at least half the same positions | At least 30 distinct exposed seed positions within an opponent/seat stratum | Block support; identify pressure-resistant interaction |
| Callback/phase concentration | Count local allocation-caused action differences by activation-relative phase `r mod 4`, using detached same-prestate mode interventions. Compare exposure and positive paired payoff contributions to strongest local F | At least 95% of action differences occupy one eligible phase, and at least 95% of positive paired payoff contribution comes from cells whose differences occupy only that phase; local gap≥0.10 | At least 30 distinct contributing seed positions in the dominant phase and 30 exposed positions in each other eligible phase | Block support; identify phase-concentrated scope |

Additional binding definitions:

- **Eligible phases are 1, 2 and 3.** Phase 0 is excluded from the concentration comparison because DENSE and SPARSE are both due there.
- Phase counts use **all local action differences**, not just the first realization witness. Otherwise earliest-witness attribution could manufacture phase concentration.
- A phase exposure is an actual first callback satisfying the common verification preconditions where a same-prestate DENSE/SPARSE intervention changes the action.
- For phase diagnostics, intervene locally at each actual prestate and discard the branches after action comparison. Never continue a divergent counterfactual history.
- Positive paired payoff contribution is `max(Y_A − Y_f, 0)`; zero total positive contribution cannot satisfy the concentration rule.
- Immunity checks cover both focal-victim and opponent-victim directions. The comparison is an interaction pattern, not proof that mechanics created immunity.
- Any actual violation of K=1 capture semantics or observation/action ordering belongs to integrity rejection, not a valid pathology flag.

Thirty exposed seed positions are a minimum opportunity requirement: with zero events, the ordinary one-sided 95% binomial upper limit is below 0.10. It does not establish universal immunity.

Warning and scope rules:

- Tick-limit proportion ≥½ without the severe gain-concentration conjunction: **report-only warning**.
- Immunity exposure below 30: **insufficient exposure**, restricting any “no immunity” assertion.
- Phase concentration without sufficient alternative-phase exposure: **scope restriction**, not a demonstrated artifact.
- Ordinary opponent payoff heterogeneity alone: report it; no pathology label.
- Malformed callback attribution or missing required diagnostics: **NOT EVALUABLE**.

The 0.10 seat boundary is tied to the practical payoff scale; opposing practical effects define severe seat dependence. A majority defines dominance by stalled endings. Zero capture despite repeated complete-core pressure defines the immunity concern. The 95% phase threshold defines near exclusivity. These are explicit prospective judgments, not inherited E8 pathology conventions.

## 10. Exhaustive interpretation table — P9-8

Define:

- **I:** all required integrity and analysis conditions pass.
- **Z:** zero realized revisions in complete valid diagnostics.
- **B:** behavioral threshold passes.
- **C:** any of F, D or S practical benefit is refuted.
- **P:** all F, D and S practical benefit results are supported.
- **V:** any severe §9 interpretation constraint triggers.

Apply the first matching row:

| Priority | Condition | Primary label |
|---:|---|---|
| 1 | I fails | **NOT EVALUABLE** |
| 2 | I passes and Z is true | **REFUTED bounded benefit claim** |
| 3 | I passes, realization is positive, but B fails | **NOT EVALUABLE** |
| 4 | I and B pass; C is true | **REFUTED bounded benefit claim** |
| 5 | I and B pass; C is false; P is false | **Behavior demonstrated; benefit NEITHER** |
| 6 | I and B pass; P is true; V is true | **Behavior demonstrated; benefit NEITHER** |
| 7 | I and B pass; P is true; V is false | **SUPPORTED beneficial adaptation** |

Required qualifiers:

- Row 2: “No realized observation-driven action revision in the registered sample.” This refutes the demonstrated-benefit conjunction for this study, not the possibility of adaptation elsewhere.
- Row 3: “Positive realization, insufficient registered replication or seat coverage.” Integrity may be intact.
- Row 4: identify every refuted contrast and retain interpretation flags.
- Row 6: “Payoff gates pass; registered interaction constraint blocks aggregate attribution.” Do not imply the numerical payoff results were unresolved.

Historical H is an independent finding:

| H result | Competitive statement |
|---|---|
| Supported | Practical superiority over the declared historical nonadaptive set established |
| Refuted | Specified historical practical superiority refuted |
| Unresolved | Historical practical superiority unresolved |

Broader “outperforms the best fixed policy” wording requires **primary support and H support**. H cannot rescue a failed causal gate or independently refute the matched attribution finding.

Timing qualifier:

- Apply **timing explanation unresolved** only through §5’s reproduction rule.
- Also report schedule uncertainty separately when S is unresolved.
- Schedule uncertainty alone does not trigger reproduction.

A reproduced schedule has `U(A−q)≤0.10`, so the upper bound for \(g_S\) is at most 0.10. This no longer guarantees strict practical refutation:

- If `U(g_S)<0.10`, S is refuted and row 4 applies when I/B pass.
- If `U(g_S)=0.10` and `L(g_S)<0.10`, S is unresolved and row 5 applies when F/D are supported, I/B pass, and no other required contrast is refuted.
- The hypothetical zero-width `L=U=0.10` case would meet support under the stated inequalities; the positive guarded row widths rule that case out for timing reproduction here.

Attach the timing qualifier in every case satisfying its rule; never force a primary label merely because reproduction was established. Integrity and behavioral precedence remain unchanged.

Explicit edge cases:

| Case | Resolution |
|---|---|
| Valid data, no realized revision | Row 2 |
| Strong payoff without behavioral gate | Row 2 or 3; never support |
| Behavior present, benefit unresolved | Row 5 |
| Fixed/disabled support, S unresolved | Row 5; schedule exclusion unresolved |
| Schedule reproduces the gain | Row 4 if S is strictly refuted; row 5 at the unresolved 0.10 upper-bound boundary, subject to earlier precedence; append timing qualifier |
| Any required contrast practically refuted | Row 4 after behavioral coverage |
| Historical-reference failure | Separate H finding; no broader fixed-policy superiority claim |
| All causal payoffs supported, severe pathology | Row 6 |
| Bound equals practical margin | Apply §5’s exact inequalities |

The table is total: integrity first; then zero/positive realization; then behavioral coverage; then refutation versus no refutation; then all-supported versus unresolved; finally severe constraint versus none.

## 11. Integrity and deviations — P9-9

### Pipeline

Before collection:

1. Bind protocol, instrument, engine, packages, defaults, aliases and seeds.
2. Bind the **complete effective T8 conditions**, including scheduler fields, scoring, placement, limits and unset overrides. Existing product identity hashes alone are insufficient.
3. Create the complete 900,856-cell manifest keyed by physical row, opponent, seed position and focal seat.
4. Bind historical primary/twin selection and logical aliases.
5. Verify the seed commitment and exclusion inventory privately.

For every completed cell:

- Verify unique cell identity and package/default stability.
- Bind result, replay, trace and diagnostic artifacts through raw-byte digests.
- Verify result/replay identity and terminal agreement.
- Verify trace footer, replay digest and entrant ordering.
- Verify callback ordering, requested/applied actions and authoritative observation reflection.
- Reconstruct selector state and realization diagnostics independently.
- Check sensing semantics and completeness.

Missing callbacks are legitimate when suppressed. They are not empty sensing observations. Applied empty tuples, refused sensing, null values and absent fields retain their distinct schema meanings.

### Disposition and recovery

**Maximum recovery scope: one additional execution per eligible cell, two total started attempts.** This cap and the complete allowlist below are accepted operational details under the formal P9-9 acceptance recorded in §2. Resume of a provably unstarted cell does not consume a started attempt. Preserve every original artifact and append-only collection/attempt record.

An automatic recovery is eligible only when **all** of these mechanically checked conditions hold:

1. No authoritative completed terminal result exists, either in the durable attempt record or in any retained result artifact. Any evidence that a terminal result was completed blocks recovery even if subsequent publication or digest binding failed.
2. An external supervisor record identifies host/worker loss, platform eviction, an externally initiated infrastructure shutdown, or an infrastructure storage/I/O interruption before result completion. This is the complete allowlist. Agent/runtime exceptions, crashes of unexplained origin, wall-time limits, match timeouts, resource exhaustion, containment events and semantic failures are not infrastructure recovery evidence. Exit status or absence of an output file alone is insufficient.
3. The recovery checker uses only dispatch/attempt identity, external failure records, completion status and integrity status. It cannot read payoff, scores, winner fields, tactical traces or behavior summaries. It may reject a cell on an independently produced semantic-integrity failure flag.
4. The original worker is proven stopped or fenced from publishing further output. An uncertain live worker or late conflicting result blocks recovery.
5. Physical row, opponent primary/twin, entrant seats, seed position and value, protocol, engine, instrument, package/default bytes and effective configuration remain identical. A fresh worker may start the cell from its original initial state; no partial-state continuation is permitted.
6. All partial artifacts, supervisor evidence and attempt identities are retained without overwrite. Each attempt has a separate immutable directory and identifier.
7. Eligibility is recorded durably before redispatch. Every eligible failure is retried automatically once; there is no analyst choice, payoff inspection, seed replacement or additional retry.
8. The recovery attempt satisfies every ordinary result/replay/trace/diagnostic validation. If it fails, or a conflicting completion appears from the original attempt, the seed block is unusable and the full registered result is NOT EVALUABLE.

The recovery state machine, durable completion detection, worker fencing, failure allowlist, attempt cap and outcome-blind eligibility must be independently qualified before collection. Recovery yields one payoff observation for the planned cell; it adds no seed or sample weight.

The pipeline's completed-cell validation applies to completed candidate
evidence. An eligible interruption's retained partial attempt is not supplied
as a completed cell: its incompleteness alone does not negate the recovery
route. Any indication of terminal completion or an independently determined
semantic, containment or diagnostic failure still blocks recovery. This
distinction does not permit replacing a completed result with a missing
footer, corrupt evidence or inconsistent diagnostics.

| Failure class | Detection point | Halt? | Unusable scope | Recovery and eligibility |
|---|---|---|---|---|
| Wrong protocol, instrument or source hash | Preflight / before each dispatch | Yes | Execution locked; if discovered later, affected blocks and full result fail | Correct preparation only before collection; post-start identity changes require a new boundary |
| Package/default/ruleset/effective-condition drift | Preflight and cell finalization | Yes | Affected seed block; full registered result fails | No replacement execution |
| Seed commitment, domain, uniqueness or exclusion failure | Before unlock | Yes | Entire seed protocol | No execution; no discretionary redraw after exposure |
| Identical filesystem copy of the same execution artifact | Ingestion | No | None after provenance verification | Deduplicate the copy; one observation remains |
| Multiple started attempts for one planned cell | Attempt ledger / ingestion | Yes unless exactly the registered recovery pair | None for one eligible failed original plus one validated recovery; otherwise whole seed block/full result fail | Accept only the registered recovery attempt when the original has no completed terminal result; any conflicting completion or third start rejects the block |
| Cell never started after infrastructure interruption | Resume audit / final census | Pause | None if start status is proven | Resume the same unstarted cell under unchanged identities |
| Started cell interrupted before completion; allowlisted external infrastructure evidence present | Supervisor / attempt audit | Pause affected dispatch | None if the one automatic recovery validates; otherwise whole seed block/full result fail | Apply all recovery predicates above, retain the original and count one final observation |
| Started cell incomplete, interrupted or missing without sufficient infrastructure evidence; recovery exhausted | Finalization / census | Yes | Whole seed block; full result fails | No rerun or replacement |
| Corrupt result/replay/trace or raw digest mismatch | Cell validation | Yes | Whole seed block; full result fails | No regeneration by replay re-encoding or rerun |
| Required trace footer or callback records missing | Trace validation | Yes | Whole seed block; full result fails | Canonical replay cannot replace callback evidence |
| Observation/action, pending feedback or selector mismatch | Semantic audit | Yes | Whole seed block; full result fails | No imputation or controller repair |
| Applied SENSE with no canonical tuple; refused sensing with a result | Semantic audit | Yes | Whole seed block; full result fails | Not converted to MISSING, NONE or empty tuple |
| Valid SENSE with no later callback before termination | Semantic audit | No | None | Keep issuance record; invent no delivery or revision |
| Invalid action, agent/runtime exception, semantic crash, containment breach, unexplained crash, timeout or resource exhaustion | Collection / trace audit | Yes | Whole seed block; full result fails | No payoff encoding or retry; these cannot be reclassified through the infrastructure allowlist |
| Missing disposable derived diagnostic output, authoritative trace intact | Diagnostic finalization | Pause finalization | None if reconstruction succeeds | Reconstruct once using the unchanged qualified algorithm; preserve the original absence and derived provenance |
| Incomplete authoritative evidence needed for diagnostics | Diagnostic audit | Yes | Whole seed block; full result fails | No reconstruction from assumed knowledge |
| Analysis RNG, arithmetic or qualified-instrument conformance failure | Analysis validation | Yes | Entire registered analysis | No analyst-selected alternative method |
| Valid seat/stall/immunity/phase pattern | Interpretation | No | None | Apply §9; retain all observations |

Resume conditions require a durable attempt ledger proving the cell was never started. Absence of an output file alone is insufficient.

An unusable block makes the **full registered result NOT EVALUABLE**. No remaining-block payoff analysis may be promoted as the registered result. Report actual planned, started, completed, validated, duplicate, missing and failed counts.

No corrupt or missing cell becomes a tie or loss. A recovered cell is analysis-eligible only after complete ordinary validation and recovery-ledger validation. Report eligible failures, recovery starts, recovered completions and exhausted recoveries separately. No original artifact is overwritten or discarded.

## 12. Reporting and future analysis-instrument qualification

The frozen reporting contract must expose complete cell accounting, all row
payoffs, selected comparators/ties, paired gaps with joint uncertainty,
realized/masked/absent revision counts and denominators, seat/opponent
decompositions, distinct trajectories, constraint flags, primary label,
timing qualifier and the separate historical competitive conclusion.
Seal the eventual machine result before writing its human interpretation;
report the full registered record without editing outcome rules.

After protocol freeze, the future instrument requires independent synthetic
qualification of schedule identities/aliases, complete-block pairing,
comparator reselection/ties, resampling reproduction, action-consequence
attribution, both-seat and self/twin accounting, missing/corrupt rejection,
every decision-table boundary and qualifier/constraint precedence. Include
fixtures where the strongest comparator changes between resamples, and
where identical selector revisions have masked versus realized consequences.
No future qualification fixture contributes fresh experimental payoff data.

These are future instrument obligations. This procedural acceptance pass does
not implement or execute that instrument and does not rerun capability
qualification.

## 13. Acceptance, freeze readiness and execution ledger

### Current verification — 2026-10-02

Baseline branch `v6-research`, HEAD
`d3c97ba077e9019a69f46c1509210862d5c52f1f`.
The current check used only source/artifact hashes, canonical schedule
enumeration and deterministic rule arithmetic. It ran no live match, seed
generation, payoff analysis or bootstrap. It did not rerun capability
qualification or qualify the future analysis/collection instrument.

| Check | Current result |
|---|---|
| Complete proposal incorporation | PASS; P9-1–P9-9 rules incorporated in §§3–11; no unresolved protocol choice |
| E9 qualified executable/test pins | PASS, 10/10 raw-byte hashes match the capability record |
| Frozen E8 pins | PASS, 47/47 LF-normalized hashes match the recorded inventory |
| Engine source | PASS, 116-file LF-normalized manifest digest `9323307c4131105a30c94cad16845468937571657b6d354827a26cfbfcff2676` |
| Historical packages | PASS, all 22 primary/twin package source and manifest raw hashes match; member/role/default mapping agrees |
| Sealed E8 result | PASS, unchanged recorded raw digest; no E8 payoff values entered this check |
| Schedule ledger | PASS, 16 unique identities, all members of the 1,334-member qualified class; both clocks, starts and single/repeated changes covered |
| Wrapper byte recipes | PASS, 19 prospective recipe pairs calculated without creating packages; materialized artifact verification remains a later gate |
| Aliases and counts | PASS, 32 logical / 29 physical rows; 900,856 physical cells, 31,064 A matches, 28,240 included historical self/twin cells; zero additional equivalence matches |
| Guard/sample arithmetic | PASS, N=1,412 is minimal for the stated bound; family error bound approximately 0.04980912945; no variance or outcome estimate used |
| Ordered classification | PASS over 972 abstract integrity/realization/F/D/S/constraint/H-status combinations; all seven priority rows covered, exactly one primary label per case |
| Timing boundary | PASS with exact rational arithmetic: reproduction can coexist with strict S refutation or S unresolved at upper bound 0.10; equal observed interior payoffs qualify at r=0.05 but can fail with wider bands |
| Recovery consistency | PASS by rule review: at most two starts; allowlisted external evidence, no completed terminal result, outcome-blind checker, stopped/fenced original worker, immutable attempts, identical inputs; semantic/corrupt/containment/diagnostic failures are non-retryable |
| Diagnostic reconstruction | Missing disposable derived output may be reconstructed once from intact authoritative evidence; inconsistency or incomplete authoritative evidence fails integrity and cannot be repaired by rerunning a match |
| Human judgments / formal acceptance | Q1/Q2 closed; P9-1–P9-9 formally recorded under research-lead authorization |

The classification combinations and rational boundary examples are checks
of the written predicates, not synthetic instrument qualification or evidence
about the ecology. Recovery review does not qualify a state machine that has
not been implemented.

### Freeze-readiness result and remaining boundaries

**READY FOR PREREGISTRATION FREEZE — NOT FROZEN.**
The absent-proposal hold from Draft 2 is closed. No materialized evaluation
roster, seed inventory, analysis instrument or collection state machine is
claimed by this documentation result.

| Boundary | Current state | Required next step |
|---|---|---|
| D9 design directions | ACCEPTED | Preserve D9-1–D9-10 |
| Formal P9-1–P9-9 acceptance | ACCEPTED, Draft 3, 2026-10-02 | Preserve the exact accepted rules, including recovery cap/allowlist |
| Protocol freeze identity/digest | NOT ISSUED; protocol NOT FROZEN | Separately freeze this accepted protocol and its bound prospective recipes/source inventory |
| Analysis/collection instrument | NOT IMPLEMENTED / NOT QUALIFIED | Implement only after freeze; independently qualify the complete pipeline, including recovery and every classification boundary |
| Materialized evaluation artifacts and prior-use exclusion inventory | NOT CREATED BY THIS PASS | Bind/check before seed authorization, as required by §7 |
| Seed generation and commitment | UNAUTHORIZED; no values generated | Explicit authorization after preceding gates, then private independent verification |
| Payoff execution | UNAUTHORIZED; no cells started | Applicable separate research authorization after commitment/unlock gates |
| Requirement C | NOT ESTABLISHED | Only eventual registered evidence may change it |

The sequence remains **record accepted P9 decisions → freeze protocol →
implement and independently qualify the instrument → bind artifacts/exclusion
inventory → separately authorize seed generation and payoff execution**.

This pass leaves documentation uncommitted. Frozen E8 evidence, qualified
E9 executable/test bytes, capability/specification records and local settings
are preserved. No outcome rule was selected using experimental evidence.

## 14. Governing sources

| Source | Authority in this draft |
|---|---|
| Research lead's 2026-10-02 acceptance and drafting instruction | Authorizes prospective documentation and explicit decision resolution only |
| Research lead's 2026-10-02 Q1/Q2 selection and procedural instruction, followed by the complete supplied proposal | Authorizes incorporation, consistency checks and formal P9-1–P9-9 acceptance recording, including the supplied recovery cap/allowlist; does not authorize protocol freeze or payoff execution |
| [Design decisions/readiness addendum](V6_E9_DESIGN_DECISIONS_AND_PREREGISTRATION_READINESS.md) | Binding D9-1–D9-10 and §4 freeze inputs |
| [Approved policy specification](V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md), [capability record](V6_E9_CAPABILITY_QUALIFICATION.md), [machine qualification record](../../../tools/research/v6/e9/qualification_record.json) | Qualified behavior, containment, clocks and capability limits |
| [Branch A′ review](V6_E9_BRANCH_A_ADAPTATION_DESIGN_REVIEW.md) | Original causal/comparator rationale |
| [E8 family freeze](V6_E8_FAMILY_FREEZE.md), [E8 preregistration](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) | Frozen environment/opponents; historical conventions are not E9 numerical defaults |
| [API v2](../../AGENT_API_V2.md), [trace specification](../../specs/v4_api_v2_trace.md), [replay schema](../../REPLAY_SCHEMA.md), [architecture](../../../ARCHITECTURE.md) | Legal evidence, callback semantics, binding and unchanged implementation boundaries |
