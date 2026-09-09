# Bytefray Agent API v2 — Authoring Guide

This is the authoritative guide to writing a Bytefray agent against Agent
API v2: both the frozen programming contract and how to use it to build an
agent that can actually win. It is written to be read in order the first
time and used as a reference afterwards.

Agent API v2 is the stable Python contract for the permanent
`bytefray-rules-4` identity and, unchanged, for the two v4 prerelease
identities that preceded it (`bytefray-rules-4-alpha1` and
`bytefray-rules-4-alpha2`). It is separate from
[Agent API v1](AGENT_API_V1.md), which remains the contract for Ruleset
v1/v2 Python entrants. No field, action kind, or semantic below changed at
promotion — see [COMPATIBILITY.md](COMPATIBILITY.md)'s "Ruleset v4" section
for what the promotion actually changed.

Companion documents: [RULES_V4.md](RULES_V4.md) is the normative gameplay
contract, [V5_STARTER_AGENTS.md](V5_STARTER_AGENTS.md) introduces the four
bundled examples this guide teaches from, and
[AGENT_AUTHORING.md](AGENT_AUTHORING.md) covers scaffolding, validation and
the Agent Designer.

---

## A. The mental model

Five words carry almost the whole game. Get these straight before writing
any code, because most beginner agents fail on a confusion between them.

| Term | What it is |
| --- | --- |
| **entrant** | You. One competitor in the match, identified by a slot (`A`, `B`, …). |
| **process** | One of your workers. It has a position in the arena and a radius. An entrant has one or more, declared once, before the match starts. |
| **anchor** | A process's current address in the arena. Its position. |
| **reach** | A process's radius, in cells, around its anchor. |
| **core** | An 8-cell region of the arena that belongs to an entrant. Yours is at a fixed address for the whole match. |

The arena is a circular array of cells. Every cell is *owned* by whoever
wrote to it last, or by nobody if nobody has.

**The victory condition.** An entrant is eliminated the moment it owns
**zero** of the eight cells of its own core. That check happens once per
tick, after every action in that tick has run.

Read that again, because it is the single most important sentence in this
document, and the reason the pre-V5 bundled agents almost never converted a
fight into a win:

> Taking one cell of the opponent's core achieves nothing. Taking seven
> achieves nothing. You must own **all eight at once**.

The defender only has to hold **one** cell to stay alive, and it can rewrite
a cell you took as soon as it notices. So offence is not "hit the enemy" —
it is "own an entire eight-cell region simultaneously, faster than the
opponent can take any single cell of it back."

**The budget.** Each entrant gets `Q = 8` actions per tick, in total, no
matter how many processes it declared. Two processes do not get sixteen
actions; they get four each. Declaring more processes buys you *positions
and roles*, never more actions.

**Disruption.** `D = 1`. If an opponent lands a legal `WRITE` on the exact
address where one of your processes is anchored, every process of yours
sitting on that address is suppressed for the rest of that tick. They are
eligible again on the next tick. There is no attack action, no recovery
action, and no notification that it happened.

---

## B. The agent lifecycle

A manifest selects v2 explicitly:

```yaml
kind: python
api_version: 2
entrypoint: agent.py:create_agent
version: 1.0.0
```

Your entrypoint names a factory. The engine calls it with no arguments and
expects a fresh object with three methods:

```python
def reset(context: MatchContextV2) -> None: ...
def declare_processes() -> list[ProcessDeclaration]: ...
def act(observation: ObservationV2) -> AgentAction: ...
```

They run in exactly this order:

1. **factory** — once, at load. Build the object; do not do match setup here,
   because you do not yet know the arena size or the seed.
2. **`reset(context)`** — once, before the match. This is where match setup
   belongs. Store what you need off `context`.
3. **`declare_processes()`** — once, after `reset` and before tick 0. The
   roster it returns is fully validated; an invalid declaration fails the
   match with no replay and no result. Because it runs after `reset`, it may
   use anything you computed there — including your parameters.
4. **`act(observation)`** — once per action, for the rest of the match. One
   call, one action. Every eligible process's turn arrives here.

The loader validates all three methods before the match begins.

---

## C. `MatchContextV2`

Handed to `reset` once.

| Field | Meaning |
| --- | --- |
| `agent_id` | Your slot: `"A"`, `"B"`, … Compare `previous_read_owner` against this to tell your own cells from someone else's. |
| `seed` | Your entrant-local deterministic seed, derived by the engine. |
| `arena_size` | Number of cells. Every address you compute must be taken modulo this. |
| `tick_limit` | The tick the match stops at if nobody has been eliminated. |
| `rng` | A `random.Random` seeded deterministically for you. |
| `parameters` | Your resolved parameters — see [§M](#m-parameters-and-presets). Empty unless you declared some. |

**Use `context.rng`, never `random.random()` or `time`.** The engine derives
that generator from the match seed so the same match replays identically.
Module-global randomness is seeded from somewhere else entirely and will
make your agent unreproducible — which also makes it undebuggable.

---

## D. `ProcessDeclaration`

`declare_processes()` returns your fixed roster. Each entry is
`ProcessDeclaration(id, reach, share)`.

- **`id`** — a non-empty string, unique within your entrant. You will see it
  again as `observation.self_process_id`.
- **`reach`** — an integer from `1` through `arena_size - 1`.
- **`share`** — finite and non-negative. **All shares must total exactly
  `1.0`** (absolute tolerance `1e-12`), and at least one must be positive.

Rules worth knowing:

- At least one process is required.
- Declarations carry **no starting address**. Every process starts
  co-located at your entrant's start, which is also your core's base. Being
  somewhere else is earned with `MOVE`.
- The roster is **fixed for the whole match**. There is no spawn, no
  retirement, and no destruction in v2.
- Shares become whole actions by deterministic largest-remainder allocation
  of the `Q = 8` budget; ties break on the stable process id. `0.5/0.5`
  gives `4/4`; `0.75/0.25` gives `6/2`.
- If disruption makes a process ineligible, its share is redistributed among
  the eligible positive-share processes, so your entrant total is preserved
  whenever any process is eligible at all.

A float trap worth avoiding: derive the last share rather than writing two
literals that you believe add up. `v5_dual_team` declares
`share=self.raider_share` and `share=1.0 - self.raider_share` for exactly
this reason — the pair cannot drift out of total, whatever the first is set
to.

---

## E. `ObservationV2`

Every `act` call receives an immutable observation.

**Time**

| Field | Meaning |
| --- | --- |
| `current_tick` | The tick this action belongs to. |
| `last_callback_tick` | The tick you were last called on. |
| `previous_action_tick` | The tick your previous action ran on. |

A gap between these is how you infer that you were disrupted; there is no
`was_disrupted` flag.

**The acting process**

| Field | Meaning |
| --- | --- |
| `self_process_id` | Which of your processes is being asked. |
| `self_anchor` | Its current address. |
| `self_reach` | Its declared reach. |

**Your own core**

| Field | Meaning |
| --- | --- |
| `own_core_base` | The first of your eight core cells. |
| `own_core_size` | How many cells it is. `8` under stable V4. |

**What you can currently see**

| Field | Meaning |
| --- | --- |
| `visible_enemy_anchor_addresses` | Sorted, unique addresses of enemy process anchors currently within the reach of **any** eligible process of yours. |

**Feedback from your last action**

| Field | Meaning |
| --- | --- |
| `previous_action_applied` | Whether it took effect. |
| `previous_read_value` | The byte your last `READ` returned. |
| `previous_read_owner` | The entrant that last wrote that cell, or `None`. |

### The information boundary

This is what you are **not** told, and no amount of cleverness will get it:

- **Where the enemy core is.** There is no `enemy_core_base`. None.
- How wide the enemy core is, or which of its cells it currently owns.
- Enemy process ids, roles, shares, or reaches.
- Whether an enemy process is disrupted.
- Any last-known position of an enemy you can no longer see.
- Who attacked you, or whether your own write disrupted anything.

Detection is **entrant-shared but current-only**: you see what any of your
processes can see *right now*, and the moment it leaves reach it is gone
from the observation. If you want a memory, you build one yourself — see
[§I](#i-search-and-target-memory).

---

## F. Actions

`act()` must return exactly one `AgentAction` whose `kind` is an
`ActionKindV2`.

| Kind | Operand | Notes |
| --- | --- | --- |
| `READ` | **Absolute** address | Applies only if the normalized address is within circular `self_reach`. Otherwise the feedback reports not applied. |
| `WRITE` | **Absolute** address, plus an integer `value` | Applies only within circular `self_reach`. A legal write reports ordinary application — never whether it disrupted anything. |
| `MOVE` | **Signed delta** from `self_anchor` | Moves only the acting process. The engine clamps displacement to `[-64, 64]` and wraps in the circular arena. |

`READ` and `WRITE` are absolute; `MOVE` is relative. Mixing these up is a
common first bug. Compute an absolute target, then either write it or
subtract your anchor to move toward it.

A `value` on a non-`WRITE` action is invalid, as are v1-only action kinds.

**Rejection costs you the action.** An out-of-reach write is not retried and
not refunded — it consumes one of your eight actions for the tick and
changes nothing. Check reach *before* choosing an address:

```python
def _distance(self, a: int, b: int) -> int:
    """Circular distance -- the arena wraps, so 1 and arena-1 are close."""
    delta = abs((a - b) % self.arena)
    return min(delta, self.arena - delta)

def _within_reach(self, observation, address: int) -> bool:
    return self._distance(observation.self_anchor, address) <= observation.self_reach
```

Every V5 starter carries those two helpers. Copy them.

---

## G. Entrant-wide sensing, process-local action

`visible_enemy_anchor_addresses` is fused across your whole entrant: if your
scout with reach 40 sees something, your keeper with reach 12 is told about
it too, on the far side of the arena.

**Seeing an address does not mean the acting process can write it.**

Sensing is entrant-wide. Legality is strictly local to the process being
asked — its own anchor, its own reach. This is the single most common
source of wasted actions in a multi-process agent: the keeper is handed a
sighting it has no hope of touching, tries anyway, and burns its quota on
rejections.

The fix is the reach check above, applied by whichever process is acting,
not by the one that did the seeing. In `v5_dual_team` both processes record
every sighting into one shared memory, and then each one independently
checks whether *it* can act on it.

---

## H. Objective geometry — the most important section

> **Seeing one enemy anchor is not the same as capturing the enemy
> objective.**

Suppose you detect an enemy process at address 300 and write to 300 for the
rest of the match. What happens?

You will produce thousands of writes. Traces will look busy. The replay will
look like a fight. And you will not win, because address 300 is at most
*one* cell of an eight-cell core, and the defender only has to hold one cell
to survive. It may not even be a core cell — you detected a process anchor,
which is where a worker is standing, not where the core is.

This is not hypothetical. It is what five of the six original `v4_*`
starters did, and it is why matches used to time out at 60% with a 1.77%
conversion rate. The V5 research program (Phases R1–R4, under
`docs/research/v5/`) tried changing the *engine* twice before establishing
that the mechanics were never the problem: a plain region sweep captures
cores in tens of ticks under completely unmodified `bytefray-rules-4`.

### What legal pressure looks like

You cannot aim at the enemy core, because you are never told where it is.
What you *can* do is press a bounded **region** around a contact you
legitimately sensed, and assume the opponent is built like you are.

That last assumption is the honest one available to you: you know your own
core is `own_core_size` cells wide, and you can reason that a symmetric
opponent's is too. That is a guess about the rules, not secret knowledge —
and it is why `v5_region_attacker` sizes its sweep from `own_core_size`
rather than from a literal `8`.

`v5_region_attacker` is the smallest complete example. Once a contact is in
reach it writes an expanding sweep around it — `0, +1, -1, +2, -2, …` out to
one core width either side — so the region grows outward and covers the
opponent's core whichever side of the contact it lies on:

```python
def _sweep_offsets(self, core_size: int) -> list[int]:
    offsets = [0]
    for step in range(1, core_size + 1):
        offsets.append(step)
        offsets.append(-step)
    return offsets
```

### Close enough for the whole region, not just the target

Here is the mistake that looks correct and is not.

If you stop moving the instant the contact enters reach, you are sitting at
maximum range. The contact is touchable — but the far half of the region you
meant to press is still outside your reach. Your sweep will name those
addresses, the engine will reject every one of them, and you will quietly
skip half the objective for the entire match while your action counter
climbs.

Close until **every address of your intended window** is inside reach:

```python
def _press_margin(self, observation) -> int:
    """How far from the contact we may sit and still cover the region."""
    return max(0, observation.self_reach - max(1, observation.own_core_size))
```

and keep moving while `distance(target, anchor) > press_margin`. This is why
a region attacker's reach must be comfortably larger than a core width;
below that there is no margin left at all.

### What this honestly cannot do

A contact-centred attack converts when the opponent is standing **on its own
core**, and does not when it has wandered away from it. In Phase C
qualification all three offensive starters take all eight cells against
`v4_local_defender`, which sits on its core — and none against `v4_scout`,
which roams.

That is not a defect in the starters. It is the real cost of having no legal
way to locate the objective, and finding a better answer to it is the most
interesting problem the API leaves open to you.

---

## I. Search and target memory

With reach 40 on a 512-cell arena, an agent that never moves usually never
meets anybody. `v5_scout_striker` is the example here.

**Search.** With nothing in sensor range it strides one full reach per
action, always in the same direction, so consecutive actions sense adjacent
non-overlapping bands and the search is a predictable lap of the arena
rather than a random walk.

**Remember.** The moment it detects something it stores the address *and the
tick*:

```python
self.last_contact = min(visible, key=lambda a: (self._distance(a, observation.self_anchor), a))
self.last_contact_tick = observation.current_tick
```

Note the tie-break on the raw address. `visible_enemy_anchor_addresses` is
sorted by address, not by distance, so taking element `0` sometimes chases
the far one; including the address in the sort key keeps the choice
deterministic when two are equidistant.

**Let it go stale.** Knowledge has a shelf life. The observation only ever
tells you where an enemy is *now*, so a remembered address is a claim about
the past that decays:

```python
if tick - self.last_contact_tick > self.contact_memory_ticks:
    return None   # we genuinely do not know where the enemy is any more
```

A memory that never expires is an agent that bombards empty ground for the
rest of the match. A memory of zero is an agent that can never press an
advantage. Both are real failure modes, which is why this is one of the
starter's declared parameters.

---

## J. Defence

Defence is the one place where you *are* told what you need:
`own_core_base` and `own_core_size` describe your own core exactly. There is
no equivalent for the opponent, which is precisely why a defender can be
written simply and an attacker cannot.

`v5_core_defender` is the only starter that uses `READ`, and that is the
lesson:

> **You can only defend damage you actually inspect.**

Rewriting your core cells blindly keeps them refreshed but tells you nothing.
`READ` is how you learn the truth. The answer arrives on your *next*
callback, so you must remember what you asked about:

```python
# ...on the inspecting action:
self.pending_read = address
return AgentAction(kind=ActionKindV2.READ, operand=address)

# ...at the start of the next callback:
if observation.previous_action_applied and self.pending_read is not None:
    taken = observation.previous_read_owner != self.context.agent_id
    if taken:
        self.repair_queue.append(self.pending_read)
```

`previous_read_owner` is the entrant that wrote the cell last. Anything that
is not your own `agent_id` is proof the cell has been taken, and proof is
what turns a blind refresh into a repair.

### Inspection must be a reserved duty

The bundled `v4_local_defender` abandons its patrol whenever an enemy is
within reach. That means an opponent can disarm it by *standing next to it*.
A defender that can be talked out of defending is not a defender.

`v5_core_defender` reserves a fixed number of actions per tick for
inspection that offence may never spend, and orders its priorities:

1. repair a cell it has proof it lost;
2. spend the reserved inspection budget;
3. push an intruder off (a write onto a live enemy anchor disrupts it);
4. otherwise blindly refresh a core cell.

It rarely wins — against territory-expanding opponents it loses on score
while never losing its core. That is a perfectly good teaching example: a
pure defender's job is not to win, it is not to lose.

---

## K. Multi-process agents

`v5_dual_team` is the smallest example of specialisation: a `raider` with
reach 32 and a `keeper` with reach 12, half the quota each.

Both are served by **the same `act` method on the same object**, so two
facts do all the work:

```python
def act(self, observation: ObservationV2) -> AgentAction:
    self._share_contact(observation)                 # ordinary attribute = shared memory
    if observation.self_process_id == "keeper":      # who is asking
        return self._act_keeper(observation)
    return self._act_raider(observation)
```

- **`observation.self_process_id` tells you which process is asking.** Branch
  on it to give each a role.
- **Ordinary attributes on `self` are shared memory between them.** This is
  your only inter-process channel, and it is enough: whichever process sees
  the opponent first writes the sighting where the other can read it.

Keep the shared state small and the role logic process-local. Shared
*knowledge* (a contact memory) is cooperation; shared *cursors* would just be
two processes tripping over each other, which is why `v5_dual_team` keeps
`raid_cursor` and `keep_cursor` separate.

Remember that the quota is fixed. Adding a third process makes each one
poorer, not your entrant stronger. Add a process when you need a second
*position* or a genuinely different *reach* — not for more throughput.

Once this makes sense, `v4_quorum` is the advanced reference: six
coordinated processes, and much harder to read.

---

## L. Determinism

Bytefray matches must replay bit-for-bit. Your agent is part of that
guarantee.

- **Use `context.rng`.** Never `random.*` at module scope, never a fresh
  `Random()` with no seed.
- **Never branch on wall-clock time**, `time.time()`, or anything derived
  from how long something took.
- **Never depend on set iteration order** or on `id()`/`hash()` of objects.
  Sorting a set before iterating it costs nothing and is what
  `v5_core_defender` does: `for address in sorted(set(...))`.
- **Do not read the filesystem, the network, or environment variables** from
  inside `act`.
- The same inputs must produce the same decisions. If a match does not
  reproduce, `bytefray agents diverge <run-a> <run-b>` will find the first
  tick where two traces disagree.

---

## M. Parameters and presets

*(New in 5.0.0a1, V5 Alpha 1 Phase D. Entirely optional.)*

An agent may declare which of its numbers are configurable. The engine then
resolves concrete values and hands them to `reset` on
`context.parameters`, already validated and coerced.

An agent that declares nothing behaves exactly as it always did.

### Declaring

Two optional top-level sections in `agent.yaml`. Both require
`api_version: 2` — resolved parameters travel on `MatchContextV2`, so an
agent that could never receive them may not declare them.

```yaml
kind: python
api_version: 2
entrypoint: agent.py:create_agent
version: 1.1.0

parameters:
  inspections_per_tick:
    type: integer
    default: 4
    minimum: 0
    maximum: 8
    description: >-
      Actions per tick reserved for READing our own core, out of the
      entrant's eight.

presets:
  standard:
    description: Half the quota inspects, half stays free for repair.
    values:
      inspections_per_tick: 4
  vigilant:
    description: Every action inspects when there is nothing to repair.
    values:
      inspections_per_tick: 8
```

### Supported types

| `type` | Accepts | Constraints |
| --- | --- | --- |
| `integer` | an integer, or text denoting one (`"8"`) | `minimum`, `maximum` |
| `number` | an integer or float, or text denoting one (`"0.25"`) | `minimum`, `maximum` |
| `boolean` | a real boolean, or one of the words below | — |
| `string` | a string | — |
| `choice` | one of the declared `choices` | `choices` (required, non-empty, unique strings) |

Every parameter requires a `type` and a `default`. `description` is optional
but worth writing — it is what a user reads when deciding what to set.

Keys and preset names are lowercase `snake_case`: a lowercase letter
followed by lowercase letters, digits or underscores.

### Coercion, exactly

The CLI and the Agent Designer both hand values over as text, so one
canonical path does all typing. It never guesses:

- `integer` accepts an `int` or a base-10 string. It refuses `8.0` — an
  integral float where a cell count was declared is more likely a units
  mistake than an intent — and refuses `True`, which is a Python `int`
  subclass and would otherwise silently mean `1`.
- `number` accepts `int`, `float`, or a string `float()` parses. Infinities
  and NaN are refused.
- `boolean` accepts a real boolean, or exactly these words, case-insensitively:
  **true** — `true`, `yes`, `on`, `1`; **false** — `false`, `no`, `off`, `0`.
  Anything else is an error. There is no Python truthiness anywhere in this
  path, because `"false"` is a non-empty string and would otherwise read as
  `True`.
- `string` accepts only a string; a number is not stringified for you.
- `choice` accepts only a declared choice.

### Resolution order

One rule, applied everywhere:

```
schema defaults  <  selected preset  <  explicit overrides
```

Start from every declared default, overlay the chosen preset, overlay any
explicit values, then validate the result. The resolved mapping always
contains exactly the declared parameters in **declaration order**, whatever
order the caller supplied overrides in — so two callers passing the same
values always produce the same result, and match identity can never depend
on a dictionary's iteration order.

### Validation is fail-closed

A malformed declaration is a manifest error, reported when the agent is
resolved and before any of its code is imported. A bad value at match time
is a parameter error, reported before the match starts. Both are ordinary
presentable diagnostics, never a Python traceback:

```
Parameter 'inspections_per_tick' (override): 12 is above the declared maximum 8.
Unknown parameter 'inspectons_per_tick'. This agent declares: 'inspections_per_tick'.
Unknown parameter preset 'reckless'. Declared presets: 'standard', 'vigilant'.
```

**For an agent that declares a schema, an unknown parameter name is an
error.** A schema-driven surface must not silently accept a typo — a
misspelled override that does nothing is far worse than one that complains.

**For an agent that declares no schema, nothing changes.** Values pass
through as they always did, unvalidated, unknown keys allowed. A manifest
written before Phase D does not start failing because a stricter system
arrived around it. (A manifest may declare *either* a `parameters` schema or
the legacy free-form `defaults:` block, not both — two incompatible ways to
say the same thing are refused rather than silently resolved.)

### Presets

A preset is a name, an optional description, and a partial or complete set
of declared parameter values. Presets are pure data: they contain no code,
never modify a source file, may only mention declared parameters, and are
validated against the schema when the manifest is parsed.

Presets are optional, and there is no reason to add them just because the
schema supports them. Where a starter does declare one called `standard`,
its values equal the schema defaults exactly — a `standard` preset that
quietly meant something else would be a trap.

### Reading them in your agent

```python
def reset(self, context: MatchContextV2) -> None:
    # Already validated and coerced against the schema in agent.yaml, so
    # there is nothing to check here. The fallback is the manifest's own
    # declared default, so the file still runs correctly without one.
    self.inspections_per_tick = int(
        context.parameters.get("inspections_per_tick", INSPECTIONS_PER_TICK)
    )
```

Because `declare_processes()` runs after `reset()`, a parameter may
determine your roster — `v5_region_attacker` declares its process reach from
one, and `v5_dual_team` derives both its shares from one.

### Setting them from the CLI

```bash
# One value. Repeat --a-param for more; -b-/-c- for the other slots.
bytefray run --a-type v5_core_defender --b-type v5_region_attacker \
    --a-param inspections_per_tick=8

# A declared preset.
bytefray run --a-type v5_core_defender --b-type v5_region_attacker \
    --a-preset vigilant

# A preset with one value overridden -- the override wins.
bytefray run --a-type v5_scout_striker --b-type v5_core_defender \
    --a-preset persistent --a-param search_stride_divisor=2
```

The pre-existing `BYTEFRAY_AGENT_A_PARAMS_JSON` environment variable (a JSON
object, which the Agent Designer already exports) is also honoured and sits
at the same override layer; an explicit `--a-param` flag beats it.

`bytefray run` prints the values it resolved for each entrant before the
match starts.

### What ends up in the artifacts

The **resolved values** are recorded in the match's `result.json` entrant
metadata and participate in `match_id`, so two matches differing only by
parameters are never confused for one another. The **schema** — types,
bounds, descriptions, presets — stays with the agent package and is never
copied into a replay or result. An entrant with no parameters records
nothing at all, which is why every artifact produced before Phase D is
unchanged.

---

## N. Common mistakes

Each of these has actually happened, most of them in the bundled agents this
guide replaced.

1. **Attacking one address forever.** The objective is an eight-cell region
   and the defender survives on one cell. Press a region. ([§H](#h-objective-geometry--the-most-important-section))
2. **Assuming a visible target is a reachable target.** Sensing is
   entrant-wide; legality is local to the acting process. Check reach in the
   process that is about to act. ([§G](#g-entrant-wide-sensing-process-local-action))
3. **Stopping at maximum reach.** If your sweep window is wider than the
   margin you left, the far half of it is unwritable and you will skip it
   silently for the whole match. Close by `reach - core_size`.
4. **Spending every action on offence.** If you never inspect your own core
   you cannot tell you are losing it, and you will be eliminated mid-attack.
5. **Letting an enemy talk your defender out of defending.** Make inspection
   a reserved budget rather than something offence may consume.
6. **Assuming you know where the enemy core is.** You do not, and there is
   no field that will tell you. Anything that appears to work by "knowing"
   it is reading a coincidence.
7. **Using module-global randomness or wall-clock time.** Your agent stops
   being reproducible, and therefore stops being debuggable.
8. **Declaring shares that do not total 1.0.** Derive the last one instead of
   writing literals you believe add up.
9. **Declaring more processes for more throughput.** The `Q = 8` budget is
   per entrant. More processes means each gets fewer actions.
10. **Trying to teach or use multi-process behaviour with one process.**
    Roles need positions; one process has one anchor.

---

## Scheduling and disruption (reference)

Production v4 uses deterministic `K = 2` chunked scheduling, with the
starting seat rotating by tick against immutable original seat order.
Multiple processes never multiply an entrant's `Q = 8` total.

A legal enemy `WRITE` to an exact live process anchor disrupts every enemy
process co-located there. A hit during tick `N` suppresses the affected
processes for the remainder of tick `N`; they are eligible again at tick
`N + 1`. Friendly co-located processes are unaffected. There is no explicit
attack, recovery, or disruption action, and no confirmation that your write
landed one.

---

## Artifacts and compatibility (reference)

Ruleset-v4 production matches — stable `bytefray-rules-4` and both
prerelease alphas alike — write `battle2.replay` schema 4 with process state
on tick and terminal records. Ruleset-v1/v2 matches continue using Agent API
v1 and replay schema 3. Historical identities and bytes are not upgraded or
reinterpreted as v4.

See [COMPATIBILITY.md](COMPATIBILITY.md),
[REPLAY_SCHEMA.md](REPLAY_SCHEMA.md), [RESULT_SCHEMA.md](RESULT_SCHEMA.md),
and the gameplay contracts: [stable Ruleset v4](RULES_V4.md),
[v4 alpha2 design](V4_ALPHA2_DESIGN.md) (the frozen delta this stable
contract's placement/process-selection semantics were promoted from), and
[v4 alpha1 design](V4_ALPHA1_DESIGN.md).
