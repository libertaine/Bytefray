# V6 E6 Matched Family

Research-only Agent API v2 packages for the V6 E6 priced-sensing experiment
([pre-registration](../../../../../docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md) §3;
[implementation plan](../../../../../docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) §5).
They are not product starter agents. Nothing in the wheel, the Designer or `bytefray agents list` ships or lists them.

## Layout

- `agents/e6_q01` … `agents/e6_q18`: 18 packages, one primary and one twin for each of the nine members. The twins are used only in mirrors.
- Every `agent.py` is **byte-identical**. A package is nothing but its manifest's parameter defaults (`search`, `posture`, `evade`, `processes`, `adaptive`), which reach the agent on `context.parameters`.
- Package IDs are opaque. `../family.py` holds the member table, the ID assignment and the manifest text. `../family_fingerprints.json` records every file's SHA-256.
- `../discipline.py` is the static D-5 gate. Every package imports only `battle_engine.agent_api` and whitelisted standard-library modules, never reads a `seed` attribute, calls none of the forbidden builtins, and contains no package ID.

| Member | `search` | `posture` | `evade` | `processes` | `adaptive` |
|---|---|---|---|---|---|
| RUSH | fast | attack | false | 1 | false |
| PACED | paced | attack | false | 1 | false |
| SPLIT | fast | attack | false | 2 | false |
| STEALTH | read | attack | false | 1 | false |
| LURK | none | attack | false | 1 | false |
| GUARD | none | guard | false | 1 | false |
| EVADER | none | guard | true | 1 | false |
| GREED | none | paint | false | 1 | false |
| ADAPT | none | paint | false | 1 | true (overrides the three before it; starts as GREED) |

## Details fixed at I-3 where plan §5.2 is silent

Each of these was fixed before any E6 data existed, and each is pinned by a behavior test in `engine/tests/test_v6_e6_family.py`. Items 2, 3, 4 and 7 are as corrected by [amendment 1](../../../../../docs/research/v6/V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (C-2 and C-3), before any seed existed.

1. **The last-known anchor.** When several enemy anchors are visible, the last-known anchor is the lowest address.
2. **Verification order.** Probes go outward from the cell one past the last-known anchor *a*: *a* + 1, *a* + 1 − 8, *a* + 1 + 8, …, *a* + 1 − 64, *a* + 1 + 64 (17 READs, covering [*a* − 63, *a* + 65]). A disruption of an anchor on core cell 0 therefore never erases the one sampled core cell.
3. **An exhausted window.** If all 17 probes miss, or find no confirmable core, the anchor is forgotten, so search resumes when nothing else is known. If the anchor is seen again, the window starts over. A run that ends unconfirmed does not exhaust the window: the next probe follows.
4. **Base finding.** A hit starts a run of contiguous enemy beacons. The run grows downward until a cell is not a beacon, then upward until a cell is not a beacon, and stops at eight cells.
   - **Eight** beacons are the core, and the lowest is the base.
   - **Seven** are the core only if the cell just below them is an enemy anchor address this entrant has written, and a READ shows its own applied write there. That anchor stands in for core cell 0 and is the base.
   - **Anything else** leaves the core unconfirmed.
5. **A hit.** A hit is an applied READ returning `0xCE` whose owner is neither the entrant itself nor `None`. This is the same test as the information event. A stand-in anchor is not a hit and is not an information event.
6. **Once known, the core is never revised**, including a core adopted without verification.
7. **The next core cell.** The attack's "next cell of the enemy core not yet written this tick" is the cell at a cyclic cursor over cells 0–7. The cursor is carried across ticks, advances past a cell only when that cell's WRITE is chosen, and skips cells already written this tick. A disruption still costs one of the eight offers; the cell it displaces rotates from tick to tick.
8. **Values.** Repairs write `0xCE`. Every other write (disruption, core attack, paint) writes `0x01`.
9. **Cycling.** The paint sequence covers all 504 non-core cells, then starts over. The READ search restarts at *m* = 0 after *m* = 48.
10. **Result timing.** A process's pending READ result is read at that process's next callback, since observation feedback is per process.
11. **ADAPT's damage check.** The own-core READ issued at a tick's first callback is judged at the next callback. An owner other than itself counts as damage; the rule is read literally, so `None` counts, though a core cell always has an owner in practice.
12. **ADAPT's timing.** "By tick 16" means the switch takes effect at the first callback of tick 17. A mode held "8 ticks after" an event lasts while the current tick is less than that event's tick + 8. In hunt mode ADAPT runs fast search and attack and makes no own-core checks.
13. **SPLIT's idle.** Both SPLIT roles idle by painting, from one entrant-wide paint cursor.
14. **Missing parameters.** Without parameters, which happens only in a validation dry run, a package behaves as GREED.
15. **Reset draws.** The four reset draws are `(-1, 1)[rng.randrange(2)]`, `rng.randrange(2)`, `(-1, 1)[rng.randrange(2)]` and `rng.randint(8, 64)`, in that order, and nothing else is drawn.

## P-6 (unverified adoption), as refined by amendment 1 (C-1)

Unverified adoption happens only at the **tick-1 first callback of the entrant scheduled to move first**, before the opponent could have acted. Under every E6 Ruleset that is Seat A. There, one visible anchor at least 64 cells from the entrant's own core base is adopted as the enemy core base.

As first approved, the rule applied at any entrant's first callback. Under a control, an attacker whose first callback came after an EVADER's first-callback MOVE adopted the moved anchor, 8–64 cells off the real core, and never revised it. The refinement keeps the parent's Seat A tick-1 forced line exactly and stays inert under a treatment. EVADER still evades immediately.
