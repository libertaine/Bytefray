# Octave

An Agent API v2 entrant for `bytefray-rules-4`, organised around one idea:
**own all eight at once.**

Ruleset v4 eliminates an entrant the moment it owns zero of the eight cells of
its own core, checked once per tick after every action in that tick has run.
Partial damage is worth exactly nothing, so Octave spends the whole match
working toward a single tick on which it can take a complete eight-cell window
it has *proved* belongs to the opponent.

## Measured results

Default parameters, arena 4096, 400-tick limit, 8 seeds in both seat orders
(16 matches per opponent):

| Opponent | W | L | T | avg ticks to kill |
| --- | ---: | ---: | ---: | ---: |
| `v4_quorum` | 16 | 0 | 0 | 7.5 |
| `viper` | 16 | 0 | 0 | 6.5 |
| `hydra` / `hydra_alpha2` | 32 | 0 | 0 | 8.4 |
| `Nemesis` / `nemesis_alpha2` | 32 | 0 | 0 | 6.8 |
| `v4_claimer` | 16 | 0 | 0 | 5.5 |
| `v4_concentrated_attacker` | 16 | 0 | 0 | 29.0 |
| `v4_defender_scout` | 16 | 0 | 0 | 6.5 |
| `v4_local_defender` | 16 | 0 | 0 | 6.5 |
| `v4_scout` | 16 | 0 | 0 | 29.4 |
| `v5_core_defender` | 16 | 0 | 0 | 5.5 |
| `v5_dual_team` | 16 | 0 | 0 | 6.5 |
| `v5_region_attacker` | 16 | 0 | 0 | 135.8 |
| `v5_scout_striker` | 16 | 0 | 0 | 74.6 |
| **Total** | **240** | **0** | **0** | |

For comparison, `v4_quorum` scores 98.2% against the same field.

Matches are reproducible: the same seed produces the same `match_id` and the
same tick count on repeat runs.

## Read this before using the numbers

Most of that table is **not** strategy. It is `process_reach`.

Reach is declared per process in `[1, arena_size - 1]`, is explicitly uncapped
under Ruleset v4, and costs nothing. The greatest circular distance between
two cells in the arena is `arena_size // 2`, so a process declaring that reach
can READ or WRITE *any* address from wherever it happens to stand. Octave
declares it on every process and therefore never spends an action on travel,
never fails a reach check, and senses every enemy anchor from tick one.

The `local` preset holds Octave to an ordinary agent's locality cost
(`process_reach: 48`). Same code, same six opponents, 6 seeds both seats:

| | W | L | T | win rate |
| --- | ---: | ---: | ---: | ---: |
| default (full reach) | 72 | 0 | 0 | **100%** |
| `local` (reach 48) | 5 | 46 | 21 | **6.9%** |

100% to 6.9% from one declared integer. Octave is best read as evidence about
that rule rather than as a claim about play: uncapped free reach collapses the
spatial game, and `docs/RULES_V4.md` already lists "no reach cap" as an
explicit alpha1 deferral.

## How it works

### Processes are anchors, not roles

All processes are identical — same reach, one shared world model, one shared
per-tick priority cascade. Whichever process is handed the next action slot
takes the next-highest-priority task.

This is deliberate. A role-bound process has to wait its turn even when its job
is the least urgent thing on the board; a shared cascade guarantees the most
valuable work gets the *earliest* slots of a tick. Processes still earn their
keep, because disruption is per-address: a legal enemy WRITE suppresses every
process anchored on that exact cell. Quota freed by a suppressed process is
redistributed to its eligible siblings, so an entrant only truly loses actions
when **all** of its processes are suppressed. Four distinct anchors means an
opponent needs four separate writes to silence Octave for a tick, and Octave
moves off its own core base at the start so that an attack on its core does not
double as a disruption of its whole roster.

### Finding the objective

There is no `enemy_core_base` and nothing that will tell you where it is. There
are two legal channels, and Octave uses both.

**A bearing, from sightings.** Every process starts co-located at its entrant's
own core base, so an early sighting points at the objective. But by the time
you are first called some of those workers may already have deployed, and no
field says which is which. READ settles it: a deployed worker stands on ground
nobody has written, which reads back with no owner, while one still at home
stands on a cell of its own core, which reads back owned by it. So Octave
probes every early sighting and lets the one that comes back enemy-owned anchor
its sweep.

Choosing among sightings by address instead would be a bug — the arena is
circular, so "lowest address" is not "nearest", and a sighting either side of
the wrap wins it by accident. That bug cost several arena sizes' worth of win
rate before it was found.

**Proof, from ownership.** `previous_read_owner` is the one channel that
identifies ground as enemy-held. Before an opponent writes anything the only
cells it owns are the eight of its core, so an early foreign owner is evidence
rather than a guess. A core is eight *contiguous* cells, so a sweep at stride
`core_size` cannot step over one: it is guaranteed to land inside after at most
`arena_size / core_size` reads. Octave orders that sweep outward from its
bearing (centre, +stride, −stride, +2·stride, …), so the cheapest reads go
nearest the only lead it has while the guarantee still covers the whole arena
if that lead was wrong.

Two things the ownership map gets right that are easy to get wrong:

- **A cell read as *unowned* is disproof, not absence of evidence.** A core
  cell is owned by its entrant from match start, so a core can never contain
  blank ground. Treating an unowned cell as merely "compatible" lets the agent
  lock onto windows that are five parts empty ground, which it then bursts
  forever.
- **Your own writes destroy your evidence.** A strike makes *you* the owner, so
  a later read of a true core cell reports you and the window can never be
  re-derived. Octave keeps the first, uncontaminated observation of every
  address.

### Committing, and being wrong

A window is committed only when every cell in it is proven enemy-held. After a
burst has failed once, the bar rises: the window must also be *bounded* — both
edge cells read and belonging to someone else. A real core is exactly eight
owned cells with something else either side; a patch of ground the opponent
merely happens to have written over usually is not. The strict test costs two
reads and is worth them only after a cheap commit has actually misfired, so it
is off until then — paying for rigour up front costs about eighty ticks against
sparse opponents and buys nothing.

With two entrants, still being called on the tick after a full eight-cell burst
is proof the opponent survived it. Octave counts that as a failure against the
window and, after `burst_retries`, strikes it off and resumes searching. It
also keeps one action a tick on the sweep while a committed window has any
failures against it — without that, a wrong lock starves the search that would
replace it, and the agent looks busy for four hundred ticks while learning
nothing.

### Timing the kill

Ruleset v4 schedules entrants in `K = 2` chunks with the starting seat rotating
by tick against immutable original seat order: the order for a tick is
`states[offset:] + states[:offset]` with `offset = (tick - 1) % n`, so the last
entrant to act is the one at index `(tick - 2) % n`.

That matters because the capture check runs at the *end* of the tick. Writes
made in the final chunk are the only ones a defender has no remaining action to
answer, so a burst launched on any other tick is one the defender is still
entitled to undo. Octave holds its burst for a tick it takes the final chunk
of, and spends the intervening ticks refreshing its own core and writing live
enemy anchors to suppress them.

This is measurable, not theoretical. Against an otherwise identical build that
bursts as soon as it knows the window, the gated version went 12W / 0L / 12T
over 24 matches — it never loses to the version that bursts blindly.

Within a burst, cells that coincide with a live enemy anchor are written first:
that WRITE claims the cell *and* suppresses every process standing on it for
the rest of the tick, which is exactly the budget the opponent would otherwise
spend taking the other seven back. The remainder is rotated by tick so no
single cell is systematically written first and therefore systematically the
easiest to reclaim.

### A float trap the authoring guide does not cover

Shares are validated as an exact total of `1.0` and read by the engine as exact
rationals. The guide's advice — write `s` and `1.0 - s` rather than two
literals — only actually holds for **two** processes. With three,
`1/3 + 1/3 + (1.0 - 2/3)` does not sum to one in binary floating point and the
roster is rejected before the match starts:

```
entrant 'A' process quota shares total 99999999999999997/100000000000000000; expected 1
```

Three equal shares have no exact binary representation at all. Octave splits in
integers over a power-of-two denominator and converts at the end: every
`weight / 1024` is exactly representable and the weights sum to 1024 by
construction, so the total is exactly 1.0 for any roster size from 1 to 8.

## Parameters

| Parameter | Default | What it does |
| --- | --- | --- |
| `process_reach` | `0` | Reach for every process. `0` means `arena_size // 2` — full coverage. A literal default cannot express this; it would be silently short on a larger arena. |
| `process_count` | `4` | Roster size, equal shares. Buys distinct anchors, never throughput. |
| `guard_actions` | `2` | Actions reserved at the *end* of a tick to rewrite our own core. |
| `sighting_window` | `2` | How long a sighting is still treated as a bearing on the opponent's core base. |
| `disperse_span` | `48` | How far to spread anchors from our own core base. `0` leaves the roster stacked. |
| `burst_on_last_mover_only` | `true` | Hold the burst for a tick we take the final chunk of. |
| `burst_retries` | `2` | Completed bursts a window may survive before it is struck off. |
| `claim_territory` | `true` | Spend genuinely spare actions claiming ground, for the score fallback. |

Presets: `standard` (the declared defaults), `local` (locality-respecting — see
above), `reckless` (everything into the burst, no reserved core refresh).

## Known limits

These are measured, not suspected.

- **Dense arenas.** Against `v4_quorum`, 12 seeds both seats: 100% at 4096 and
  16384, 95.8% at 2048 and 8192, but 83.3% / 87.5% / 79.2% at 256 / 512 / 1024.
  The failure at 1024 is not a stall — Octave resolves a window, fails to
  convert it against Quorum's repairing guardian, and loses the attrition war
  around tick 60. Small arenas make the opponent's ordinary writes dense enough
  that owned runs merge with its core, which costs bursts.
- **No hold-tracking.** Octave rewrites all eight cells on every burst, even
  cells it already owns from a previous one. Against an opponent that repairs
  slowly this wastes actions that could have gone to defence. Tracking held
  cells and bursting only the remainder is the most obvious improvement left.
- **Mirror matches stall.** Two Octaves reach a stable tie at the tick limit:
  each correctly waits for its own last-mover parity and each successfully
  defends the other's burst. That is arguably the correct equilibrium, but it
  means no territory edge decides it either.
- **`_is_last_mover` assumes it can infer the entrant count** from its own slot
  letter and the owners it has read. That is exact for two entrants and a
  heuristic beyond.

## Reproducing

```bash
bytefray agents validate octave
bytefray run --a-type octave --b-type v4_quorum --ticks 400

# the fairness comparison
bytefray run --a-type octave --b-type v4_quorum --ticks 400 --a-preset local

# batch win rates, both seat orders
python3 tools/arena_bench.py octave v4_quorum,viper,hydra_alpha2 --seeds 12
```
