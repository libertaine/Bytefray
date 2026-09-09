# The V5 Starter Agents

Bytefray 5.0.0a1 ships four Agent API v2 starter agents. They are a ladder,
not a roster: each one exists to teach exactly one idea, and each is meant to
be read straight through in a couple of minutes.

They run under the stable gameplay ruleset `bytefray-rules-4`, they use only
the public Agent API v2, and they are installed into your writable `agents/`
catalog like every other bundled agent — so `bytefray agents list`, the CLI
and the Agent Designer all show them without any extra step.

| Read it | Agent | The one idea |
| --- | --- | --- |
| 1st | `v5_region_attacker` | The objective is a **region**, not a point. |
| 2nd | `v5_scout_striker` | **Search**, remember, then strike. |
| 3rd | `v5_core_defender` | You can only defend what you actually **look at**. |
| 4th | `v5_dual_team` | An entrant is a **team** of processes, not one robot. |

Once those make sense, `v4_quorum` is the advanced example: six coordinated
processes, and much harder to read.

## Why the objective is a region

An entrant loses when it owns **none** of the cells of its own core. Under
stable V4 a core is eight contiguous cells, so taking one cell and holding it
forever achieves nothing — the defender still owns seven. To win you must own
every cell of the opponent's core *at the same time*.

That single rule is why the five original `v4_*` starters converted so rarely:
most of them pick one enemy address and write to it for the rest of the match.
The V5 starters are built the other way round: they press a bounded region.

## The two limits that shape every strategy

**Reach is both your arm and your eyes.** A process's declared `reach` is the
radius within which its READs and WRITEs are applied, *and* the radius within
which it can sense enemy anchors. Widening it to cover more of a region also
widens what you can see; narrowing it makes you blind. A write outside reach is
rejected and the wasted action still counts against your quota.

**Get close enough for the whole region, not just the target.** This is the
mistake the V5 offensive starters are written to avoid. If you stop moving the
moment the contact enters reach, you are sitting at maximum range and the far
half of the region you meant to press is still unreachable — you will sweep it
forever and quietly skip half the addresses. Close until every address of your
intended window is inside reach.

## What you are and are not told

`ObservationV2` gives you `own_core_base` and `own_core_size` — **your own**
core. There is no equivalent for the opponent. You are never told where the
enemy core is, how wide it is, or which cells it owns.

So an offensive agent cannot aim at the enemy objective directly. What it can
do is press a bounded region around a contact it legitimately sensed, and
assume the opponent is built the same way it is — which is why the V5 attackers
size their sweep from `own_core_size` rather than from a literal `8`.

A direct consequence, visible in the qualification data: **a contact-centred
attack converts when the opponent is standing on its own core, and does not
when the opponent has wandered away from it.** Against `v4_local_defender`,
which sits on its core, all three offensive starters take all eight cells.
Against `v4_scout`, which roams, they take none. That is not a bug in the
starters; it is the honest cost of having no legal way to locate the objective,
and it is the problem more advanced target acquisition exists to solve.

## The four starters

### `v5_region_attacker` — one process, reach 16

The simplest offensive agent. No memory at all: it re-reads the nearest visible
enemy anchor on every single action, closes until its whole sweep window is in
reach, then writes the next address of an expanding sweep — `0, +1, -1, +2,
-2, …` out to one core width either side of the contact.

Its only state is a cursor into that sweep.

### `v5_scout_striker` — one process, reach 40

Movement and search. With nothing in sensor range it strides forward one full
reach per action, so consecutive actions sense adjacent, non-overlapping bands
and the search is a predictable lap of the arena rather than a random walk.

When it detects something it stores the address and the tick, and keeps
attacking that memory for up to 60 ticks after it was last seen — then gives up
and resumes searching. Its strike window is scanned low address to high, which
is a different coverage order from the region attacker's expanding sweep.

It carries no defence at all. That is a deliberate cost, not an oversight.

### `v5_core_defender` — one process, reach 12

The only starter that uses READ. It steps to the middle of its own core, then
reads its cells in rotation; a cell that comes back owned by somebody else is
proof of a loss and goes on a repair queue that is serviced before anything
else.

The important detail is `INSPECTIONS_PER_TICK`. Inspection is a **reserved
duty** that offence may not spend. The bundled `v4_local_defender` abandons its
patrol whenever an enemy is within reach, which means an opponent can disarm it
simply by standing next to it — a defender that can be talked out of defending
is not a defender.

It rarely wins. Against territory-expanding opponents it loses on score while
never losing its core. That is a perfectly good teaching example.

### `v5_dual_team` — two processes, reach 32 and 12, half the quota each

The smallest example of process specialisation. `declare_processes` returns two
declarations whose shares total exactly `1.0`, so each gets four of the eight
actions per tick.

Both processes are served by the same `act` method on the same object, so:

* `observation.self_process_id` tells you which one is asking, and
* ordinary attributes on `self` are shared memory between them.

The `raider` fights and the `keeper` holds the core, and whichever of them
sees the opponent first writes that sighting into one shared contact memory the
other can use. The keeper never READs — unlike `v5_core_defender` it cannot
tell a cell it still owns from one it has lost, and simply refreshes all of
them. Cheaper, less informed, and a useful contrast.

## Things worth trying

* Run `v5_region_attacker` against `v5_core_defender` and watch the defender
  hold a core that is being taken apart and put back together.
* Change `ATTACKER_REACH` and see the trade-off between sensing and striking.
* Run `v5_region_attacker` against **itself**. Two identical agents drifting at
  the same speed in the same direction preserve their separation forever and
  never make contact, so nothing happens for the whole match. It is the
  clearest demonstration in the box that a constant-velocity search cannot
  catch an identical searcher — and `v5_dual_team`, whose two processes have
  different reaches, does not have the problem.

## Where the design came from

The V5 research program (Phases 0 and R1–R4, under `docs/research/v5/`)
established that stable V4's mechanics were never the reason matches failed to
convert — the bundled agent population was. Phase R3 proved that a plain region
sweep captures cores in tens of ticks under unmodified `bytefray-rules-4`, and
Phase R4 measured a competent, diverse population turning 39.6% decisive
captures into 64.6%.

These starters are a fresh, beginner-oriented implementation of those lessons.
The research agents themselves stay in `tools/research/v5/`; none of them was
renamed and shipped. The six `v4_*` agents are unchanged and still available —
the research corpora and existing replays refer to those IDs by name.

Full implementation and qualification record:
`docs/research/v5/V5_ALPHA1_PHASE_C_STARTER_AGENTS.md`.
