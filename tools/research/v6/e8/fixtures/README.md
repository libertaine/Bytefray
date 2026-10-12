# V6 E8 Family

Research-only Agent API v2 packages for the V6 E8 active spatial sensing experiment
([pre-registration](../../../../../docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md), PR8, revision 5, §3;
[implementation plan](../../../../../docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md) §5).
They are not product starter agents. Nothing in the wheel, the Designer or `bytefray agents list` ships or lists them.

## Layout

- `agents/e8_q01` … `agents/e8_q22`: 22 packages, a primary and a twin for each of the eleven members. The twins are used only in mirrors.
- Every `agent.py` is **byte-identical**. A package is nothing but its manifest's parameter defaults (`acquire`, `reacquire`, `posture`, `evade`, `processes`, `stress`), which reach the agent on `context.parameters`.
- Package IDs are opaque (plan decision P8-10). `../family.py` holds the member table, the ID assignment and the manifest text. `../family_fingerprints.json` records every file's SHA-256.
- `../discipline.py` is the static D8-9 gate: E6's D-5 rules, E8's package-ID pattern, and the added rule that every SENSE lies under a `sensing_window is not None` guard. It also gives each package's static class for the pre-match compatibility gate, `../compatibility.py`. Every family package is **context-gated**.

| Member | `acquire` | `reacquire` | `posture` | `evade` | `processes` | `stress` |
|---|---|---|---|---|---|---|
| RUSH8 | spatial-fast | once | attack | off | 1 | false |
| REACQ8 | spatial-fast | repeat | attack | off | 1 | false |
| PACED8 | spatial-paced | once | attack | off | 1 | false |
| STEALTH8 | ownership | once | attack | off | 1 | false |
| LURK8 | none | none | attack | off | 1 | false |
| SPLIT8 | spatial-fast (sensor) | once | attack | off | 2 (sensor 1/4, striker 3/4) | false |
| GUARD8 | spatial-fast | once | guard | off | 1 | false |
| EVADE8 | spatial-fast | once | guard | on-hit | 1 | false |
| GREED8 | none | none | paint | off | 1 | false |
| ADAPT8 | spatial-fast | adaptive | attack | off | 1 | false |
| STRESS8 | none | none | guard | off | 1 | true |

A8, H8-CHANNEL's frozen candidate set, is {RUSH8, REACQ8, PACED8, STEALTH8, LURK8}. The static H8-REPEAT census, applied to these manifests' parameters, is {EVADE8}.

## The registration's semantics

The policy is the plan's §5.3 procedure: tick bookkeeping; the previous action's result (E6's READ handling, or an applied SENSE's KU-1 to KU-4, then KU-7, the search and ADAPT8's count); observation (under passive, the known set is the visible set, with KU-5's tracked set); then the first applicable action of: member-level steps (EVADE8's evasion, STRESS8's check and repair), a re-acquisition search in progress, verification (repeat and adaptive, active), and the posture steps. The posture, verification-READ, core-cursor and adoption code is the E6 family's as corrected by E6's amendment 1, carried over unchanged, and E6's fixed details 1 to 10 and 13 hold as written there (11 and 12 concern E6's ADAPT, which E8 does not have). Under C8 and C8L, RUSH8, PACED8, STEALTH8, LURK8 and GREED8 reproduce E6's RUSH, PACED, STEALTH, LURK and GREED decision for decision (`engine/tests/test_v6_e8_family_engine.py`).

## Details fixed at I8-3 where PR8 and the plan are silent

Each was fixed before any E8 seed, matrix cell or outcome existed, and each is pinned by a test in `engine/tests/test_v6_e8_family*.py` or `test_v6_e8_adapt8_freeze.py`. Items 3, 4 and 7 are judgment calls on registered wording; the rest are encodings or unreachable cases.

1. **The manifest encoding.** A manifest parameter is a scalar, so a registered `reacquire` of "—" (`null` in the transcription) is the choice `none`, which behaves as "never re-acquires", and a member the table gives no `stress` has `stress: false`. A test checks the table against the transcription under exactly this encoding. String values are quoted, since YAML 1.1 reads `off` as a boolean.
2. **The draws.** At reset, sigma is `(-1, 1)[rng.randrange(2)]` and the paint side is `rng.randrange(2)`, in that order (P8-1, E6's forms). In play, tau is `(-1, 1)[rng.randrange(2)]`, drawn when a search starts; at each evasion, sigma_e is `(-1, 1)[rng.randrange(2)]` and then m is `rng.randint(8, 64)` (P8-2). Nothing else is drawn.
3. **A later discovery traversal starts at c_0.** The index k advances when a discovery SENSE is issued, and wraps after c_6. When any applied SENSE result contains an enemy anchor, the traversal stops, and if discovery applies again later (only for REACQ8 and ADAPT8, after a search is exhausted with the core unconfirmed), it starts again at k = 0. The reading: "while no enemy anchor is known, the member's successive sensing actions are centered on c_k … for k = 0, 1, …, 6" (PR8 §2.5) describes each period with nothing known.
4. **"After first discovery".** First discovery has happened once any applied SENSE result has contained an enemy anchor (the plan's state "whether first discovery has happened"). Verification then applies at every first callback of a tick with an address known and no search in progress, including a first callback whose delivered result is itself the first discovery.
5. **The active search's windows.** After the observation that found a missing, the search senses a + tau·46, then a − tau·46 (plan §5.4). A queued missing address (KU-6) is searched the same way. Queues need two known anchors missing at once, which the frozen family cannot produce under active: there only EVADE8's single anchor moves.
6. **Replacement.** When a result returns any enemy anchor, every missing address, the searched one included, is replaced by its nearest returned address, the lower on a tie (KU-7), and the search ends. The replacement map is policy state; the known set already holds the returned addresses.
7. **ADAPT8's address a.** The address a verification is about is the lowest known address under active, and the lowest tracked address under passive (KU-8). An observed relocation is that address found missing; another known address found missing does not reset the count. The two readings differ only against SPLIT8's two anchors.
8. **ADAPT8's passive observation.** A first callback of a tick is an applicable verification observation when ADAPT8 has not switched and its tracked set is not empty. Under passive a search in progress implies an empty tracked set, since any visible anchor ends the search.
9. **STRESS8's repair** writes the core beacon to the checked cell and does not advance the guard cursor. An owner of `None` counts as damage, read literally, as E6 ADAPT's check was (E6 fixed detail 11).
10. **EVADE8's bookkeeping.** The tick of the previous callback and that tick's callback count are policy state. At the first callback of the match there is none, so no hit is inferred (P8-5).
11. **A passive MOVE toward a center** is the shortest signed circular displacement clamped to ±64 (P8-3); a displacement of exactly 256 is taken as +256, then clamped. That case is unreachable.
12. **A refused SENSE** changes no knowledge, and the window it was to sense is sensed next: the discovery index and the search index do not advance. This is unreachable, since every process declares reach `arena // 2`, the largest circular distance; it keeps a frozen agent from failing on it.
13. **No SENSE without a window.** The one place that builds a SENSE is guarded by `sensing_window is not None`, and raises if ever reached without one. No path reaches it under passive (tested for every member).
14. **Missing parameters.** Without parameters, which happens only in a validation dry run, a package behaves as GREED8.

## Characterizations observed in the engine tests

These are properties of the registered semantics and the engine, recorded so that nobody mistakes them for implementation choices. None changes a registered item.

- **P8-6's premise holds only under whole-tick disruption.** Under C8 and T8, STRESS8's callbacks 1 and 2 of a tick always share a chunk. Under C8L and T8L, a hit before STRESS8's first chunk costs it its first offer, so an opponent decision falls between them. P8-6's conclusion holds under all four conditions: the check's result always reaches the same tick's second callback, so the stale obligation never arises (`test_p8_6_the_checks_result_always_reaches_the_same_ticks_second_callback`).
- **A hit after the victim's last offer of a tick costs nothing**, under either parent: the disruption window ends with the tick (as PA §8's table implies).
- **Under T8L, RP-2's cross-tick continuation cannot arise** for a search started by a verification: a member receives at least four callbacks a tick, so its two remaining windows fall in the same tick. Under T8 it arises after a hit that follows the member's first chunk (`test_rp2_reacq8s_search_reaches_its_third_window`).
- **Under passive, a search's first center is the missing anchor's last address** (PR8 §2.5). For an anchor that sat on its core base, the searcher parks its own anchor on the opponent's core cell 0, where the opponent's core repairs disrupt it (RP-7's chase, observed in `test_v6_e8_adapt8_freeze.py`).
- **ADAPT8 counts only observed relocations.** A scripted evader whose alternating evasions returned it to the same address between two verifications was confirmed twice, and ADAPT8 switched. The freeze tests' scripted evader therefore never revisits an address.
- **Start-up.** A scripted evader whose first evasion came only after ADAPT8's second verification (it lost tick 1 to ADAPT8's first-chunk hit, under whole-tick) let ADAPT8 switch at tick 3. EVADE8 has the same first-callback rule (P8-5); whether this start-up arises against EVADE8 was not probed, since this phase plays no family member against another.
