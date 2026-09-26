# V6 E3 Research Fixtures

Tracked, research-only Agent API v2 fixtures for the V6 E3 slot-limited disruption
experiment (`docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md` Sec L and
Sec O-4). They are resolved by `tools/research/v6/e3/fixtures.py`, from this tracked
directory only, never from the ignored runtime `agents/` catalogue. They are **not** product
starter agents: nothing in the wheel, the Designer or `bytefray agents list` ships or lists
them. Every other E3 entrant is an unchanged E2 fixture (`tools/research/v6/e2/fixtures/agents`).

## Rules

The E3 fixtures follow the E2 fixture rules (`tools/research/v6/e2/fixtures/agents/README.md`):
global reach (`arena_size // 2`), public information only (`ObservationV2` and
`MatchContextV2`, importing nothing but `battle_engine.agent_api`), the single-location
enemy-core inference contract, and no global randomness. The twin's `agent.py` is
byte-identical; its manifest differs only in `name` and `display`. The twin exists to make
the jam mirror cell of field F4.

## Agents

| Fixture | Behaviour | Purpose |
|---|---|---|
| `e3_jam_sniper` | One global-reach process. Within each tick it alternates by its own action count: even actions (0, 2, 4, 6) write a visible enemy anchor, cycling through the visible anchors; odd actions (1, 3, 5, 7) write the next enemy core cell, from a cursor over core offsets 1 .. size-1 that continues across ticks (offset 0, the core base, is where every enemy spawns and is covered by the hits). A hit with no visible anchor becomes a core write, a core write before the enemy core is known becomes a hit, and with neither it reads its own core base. Deterministic: it draws no randomness. | The only new agent E3 needs (review Sec L, Sec O-4). Every E2 fixture hits each enemy anchor at most once per tick, so without it the maximal-denial regime -- repeated finite suppression inside one tick -- is never exercised. It is the diagnostic stressor for D6 ("re-disruption recreates control"), not a competitor, and is not tuned to win the field. |
| `e3_jam_sniper_twin` | Byte-identical `agent.py`. | Jam mirror (F4). |

Under whole-tick disruption the repeated hits add nothing after the first (the victim is
already silent for the rest of the tick), so under the E2 parent the jam sniper behaves as a
sniper that spends half its writes on the enemy core base. Under `disruption_slot_limit = 1`
each hit suppresses only the victim's next action offer, so the alternation is exactly the
jam that the design review's Sec G.4 bound is proved against.

## Fingerprints (`agent_revisions.agent_revision_fingerprint`)

These are frozen in `tools/research/v6/e3/matrix.py` (`AGENT_FINGERPRINTS`); an E3 run whose
live fingerprints differ fails closed.

| Fixture | Fingerprint |
|---|---|
| `e3_jam_sniper` | `f92c056e271ce16492119fd57edf7ce10985f3aef88636228f8c7434a1a7ad8e` |
| `e3_jam_sniper_twin` | `6035dd549edf49bbd0a62f5713a797fc268e2edb9e20a7b9e96d71dc159a31e2` |
