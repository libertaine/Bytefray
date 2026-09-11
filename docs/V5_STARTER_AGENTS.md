# The V5 Starter Agents

Bytefray 5.0.0a1 ships four Agent API v2 starter agents. They are a ladder,
not a roster: each one exists to teach exactly one idea, and each is meant to
be read straight through in a couple of minutes.

They run under the stable gameplay ruleset `bytefray-rules-4`, they use only
the public Agent API v2, and they are installed into your writable `agents/`
catalog like every other bundled agent — so `bytefray agents`, the CLI
and the Agent Designer all show them without any extra step.

| Read it | Agent | The one idea | Its parameters |
| --- | --- | --- | --- |
| 1st | `v5_region_attacker` | The objective is a **region**, not a point. | `attacker_reach` |
| 2nd | `v5_scout_striker` | **Search**, remember, then strike. | `contact_memory_ticks`, `search_stride_divisor` |
| 3rd | `v5_core_defender` | You can only defend what you actually **look at**. | `inspections_per_tick` |
| 4th | `v5_dual_team` | An entrant is a **team** of processes, not one robot. | `raider_share` |

Once those make sense, `v4_quorum` is the advanced example: six coordinated
processes, and much harder to read.

All four demonstrate parameters and presets, one or two knobs each. If you
only want to see how that works, read `v5_core_defender`: its single
`inspections_per_tick` is the agent's whole lesson expressed as a number.
The full contract is in
[AGENT_API_V2.md](AGENT_API_V2.md#m-parameters-and-presets); this page just
says what each starter exposes and why.

**Every starter's defaults are exactly the behaviour it had before
parameters existed.** Nothing about how these agents play changed when they
gained a schema, and a test asserts it against digests captured beforehand.

## Setting parameters in the Agent Designer

Select a starter in Advanced's **Agent Params** tab and Bytefray generates a
control for each parameter its manifest declares: a bounded spin box for a
number, a menu for a choice, a checkbox for a switch. Each control carries the
parameter's description, its legal range and its default, and a preset
selector loads a declared preset in one step. A line under the controls always
states the values the match will actually use, so a preset name never hides
what it resolved to, and **Reset to Defaults** returns everything to the
manifest's own values. Leaving every control alone runs the agent exactly as a
bare `bytefray run` would — the Designer sends only values you have changed.

An agent that declares no parameters — every `v4_*` starter, every Agent API
v1 agent, every VM agent — keeps the free-form JSON field it has always had.

## Upgrading an existing installation

Bundled starters are copied into your writable `agents/` catalog the first
time Bytefray runs, and that catalog is yours to edit. When a newer Bytefray
ships a changed starter, it updates your copy **only** if that copy is still
byte-for-byte the version some earlier release installed. If you have edited a
starter, your version is kept and Bytefray tells you which ones it kept and
that deleting or renaming one gets you the bundled version. Line-ending
differences alone do not count as an edit.

This is why an installation created before `5.0.0a1`'s parameter schemas
existed picks the new manifests up automatically, while a starter you have
been working on does not get overwritten from under you.

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

**`attacker_reach`** (integer, 10–64, default 16) is the reach it declares
for its process, and it is the one number here genuinely worth playing with:
reach is simultaneously how far the agent can *sense* and how far it can
*write*. The `far_sighted` preset doubles it to 32. Note what is *not*
adjustable — the sweep is always one core width either side of the contact,
because that is the width of the objective rather than a matter of taste.

### `v5_scout_striker` — one process, reach 40

Movement and search. With nothing in sensor range it strides forward one full
reach per action, so consecutive actions sense adjacent, non-overlapping bands
and the search is a predictable lap of the arena rather than a random walk.

When it detects something it stores the address and the tick, and keeps
attacking that memory for up to 60 ticks after it was last seen — then gives up
and resumes searching. Its strike window is scanned low address to high, which
is a different coverage order from the region attacker's expanding sweep.

It carries no defence at all. That is a deliberate cost, not an oversight.

Both of the numbers that define this strategy are parameters.
**`contact_memory_ticks`** (0–1000, default 60) is how long a sighting stays
worth attacking; set it to 0 and the agent can only ever attack what it can
currently see, set it high and it bombards ground the opponent has left. The
`persistent` preset raises it to 240. **`search_stride_divisor`** (1–8,
default 1) divides the search step: 1 covers adjacent, non-overlapping
sensor bands, larger values re-sense ground already covered.

### `v5_core_defender` — one process, reach 12

The only starter that uses READ. It steps to the middle of its own core, then
reads its cells in rotation; a cell that comes back owned by somebody else is
proof of a loss and goes on a repair queue that is serviced before anything
else.

The important detail is **`inspections_per_tick`** (0–8, default 4), which is
also its one parameter. Inspection is a **reserved duty** that offence may
not spend. The bundled `v4_local_defender` abandons its patrol whenever an
enemy is within reach, which means an opponent can disarm it simply by
standing next to it — a defender that can be talked out of defending is not
a defender.

Setting it to 0 is the clearest demonstration of the lesson in the box: the
agent keeps refreshing its core cells and stops issuing a single `READ`, so
it can no longer tell a cell it still owns from one it has lost. The
`vigilant` preset goes the other way and spends the whole quota looking.

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

Its parameter is **`raider_share`** (number, 0.0–1.0, default 0.5). The
keeper's share is *derived* as `1.0 - raider_share` rather than declared
separately, so the pair can never drift out of the required total of 1.0 —
which is the point. How you divide a fixed eight-action quota between roles
is the decision this whole example exists to show, so it is the thing worth
making adjustable. The `raid_heavy` preset moves it to 0.75, which the
largest-remainder allocation turns into six actions for the raider and two
for the keeper.

## Things worth trying

* Run `v5_region_attacker` against `v5_core_defender` and watch the defender
  hold a core that is being taken apart and put back together.
* Change `attacker_reach` and see the trade-off between sensing and
  striking: `bytefray run --a-type v5_region_attacker --a-param
  attacker_reach=32 --b-type v5_core_defender`.
* Run `v5_core_defender` with `--a-param inspections_per_tick=0` against
  `v5_region_attacker` and watch a defender that can no longer see what it
  is losing.
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
