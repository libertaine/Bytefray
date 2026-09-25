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

Each of these was fixed before any E6 data existed, and each is pinned by a behavior test in `engine/tests/test_v6_e6_family.py`.

1. **The last-known anchor.** When several enemy anchors are visible, the last-known anchor is the lowest address.
2. **Verification order.** Probes go outward from the last-known anchor *a*: *a*, *a* − 8, *a* + 8, …, *a* − 64, *a* + 64 (17 READs).
3. **An exhausted window.** If all 17 probes miss, the anchor is forgotten, so search resumes when nothing else is known. If the anchor is seen again, the window starts over.
4. **Base finding.** A hit starts a downward scan that ends at the first miss, or after the eighth cell (seven below the first hit). The base is the lowest cell that hit.
5. **A hit.** A hit is an applied READ returning `0xCE` whose owner is neither the entrant itself nor `None`. This is the same test as the information event.
6. **Once known, the core is never revised**, including a core adopted without verification.
7. **The next core cell.** The attack's "next cell of the enemy core not yet written this tick" is the first cell, in base order, not yet written this tick.
8. **Values.** Repairs write `0xCE`. Every other write (disruption, core attack, paint) writes `0x01`.
9. **Cycling.** The paint sequence covers all 504 non-core cells, then starts over. The READ search restarts at *m* = 0 after *m* = 48.
10. **Result timing.** A process's pending READ result is read at that process's next callback, since observation feedback is per process.
11. **ADAPT's damage check.** The own-core READ issued at a tick's first callback is judged at the next callback. An owner other than itself counts as damage; the rule is read literally, so `None` counts, though a core cell always has an owner in practice.
12. **ADAPT's timing.** "By tick 16" means the switch takes effect at the first callback of tick 17. A mode held "8 ticks after" an event lasts while the current tick is less than that event's tick + 8. In hunt mode ADAPT runs fast search and attack and makes no own-core checks.
13. **SPLIT's idle.** Both SPLIT roles idle by painting, from one entrant-wide paint cursor.
14. **Missing parameters.** Without parameters, which happens only in a validation dry run, a package behaves as GREED.
15. **Reset draws.** The four reset draws are `(-1, 1)[rng.randrange(2)]`, `rng.randrange(2)`, `(-1, 1)[rng.randrange(2)]` and `rng.randint(8, 64)`, in that order, and nothing else is drawn.

## Known consequence of approved decision P-6 (unverified adoption)

Under a **control** Ruleset, an attacker whose first callback comes after an EVADER's first-callback MOVE sees one anchor. If that anchor is at least 64 cells from its own core, the attacker adopts it as the enemy core base, though it is 8–64 cells off the evader's real core, and never revises it. This follows directly from the approved rule, and it is the E2–E5 fixture convention. It is listed here so that the Checkpoint A review sees it before any seed exists. It never fires under a treatment, because at a first callback nothing farther than 32 cells can be visible.
