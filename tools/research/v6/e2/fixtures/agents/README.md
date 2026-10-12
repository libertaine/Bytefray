# V6 E2 Research Fixtures

Tracked, research-only Agent API v2 fixtures for the V6 E2 capture-hold experiment
(`docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md` Sec G). They are resolved by
`tools/research/v6/experiment_harness.py` through `TRACKED_BENCHMARK_SOURCE_DIRS`, never from
the ignored runtime `agents/` catalogue, and they are **not** product starter agents: nothing
in the wheel, the Designer or `bytefray agents list` ships or lists them.

## Rules every fixture follows

- **Global reach** (`arena_size // 2`) for every process. Reach is free, so a local-reach
  agent would be incompetent rather than strategically distinct (Sec G.1).
- **Public information only.** Each fixture reads `ObservationV2` and `MatchContextV2` and
  imports nothing but `battle_engine.agent_api`. The enemy core base is never read from the
  engine: the inferring fixtures (`e2_sniper`, `e2_min_guard`, `e2_counter`,
  `e2_spread_sniper`, `e2_spread_defender`) adopt it at the first callback in which every
  visible enemy anchor is at one address, and never revise it. `capture_analyzer.py` audits
  that inference against each replay.
- **Seeds.** Only fixtures whose hypothesis involves spatial variation draw from
  `context.rng` (painting side, spread offsets); the others are deliberately deterministic, and
  the analysis counts distinct trajectories rather than seeds. No fixture uses global randomness.
- **Twins.** Each agent has a `*_twin` whose `agent.py` is byte-identical and whose manifest
  differs only in `name` and `display`. Twins exist to make true mirror cells (field F2).

## Agents

| Fixture | Archetype | Behaviour | Purpose |
|---|---|---|---|
| `v4_probe` | V4 exploit probe | Exact copy of the frozen `CompetentGlobalSniperProbe` (writes `anchor[0] + step`, step cycling 0-7). | Continuity with the V4 exploit characterization; H0 for non-defending play. |
| `e2_sniper` | Global Sniper (1) | Each visible enemy anchor once per tick, then every enemy core cell not yet written this tick. Never repairs. | Does E2 only delay the dominant attack? As Seat B, the naive counterattacker. |
| `e2_repair_guard` | Pure Repair Guard (2a) | Rewrites its own core cells, cycling. Never disrupts. | Nominal window versus meaningful defense (Sec D.4); H0 control for defense. |
| `e2_disrupt_guard` | Disrupt-First Guard (2b) | Each visible enemy anchor once per tick, then its own core cells. | Canonical H1 defender (Sec D.5); H3a/H3b. |
| `e2_min_guard` | Minimal Guard (2c) | Disrupts anchors, rewrites exactly one own core cell, attacks the enemy core with the rest. | Is a one-cell reclaim too cheap? |
| `e2_greedy_painter` | Greedy Painter (3a) | Paints a frontier outward from its own core, alternating sides (first side from `context.rng`). Never disrupts or repairs. | Opportunity-cost pole (H2). |
| `e2_guarded_painter` | Guarded Painter (3b) | Disrupts anchors, rewrites one own core cell, paints the rest. | H2 defensive opportunity cost; the exploratory mirror inversion (H3c). |
| `e2_counter` | Counterattacker (4) | Paints until its process misses a whole tick of callbacks (`last_callback_tick < current_tick - 1`), then snipes permanently without repairing. | Races and mutual threats. |
| `e2_spread_sniper` | Spread Sniper (1') | Three processes; `p1`/`p2` move once by `context.rng` offsets of magnitude 16-64 and opposite sign, then all disrupt and attack. | Does location count close the response window (Sec D.6, H3e)? |
| `e2_spread_defender` | Spread Defender (2') | Three processes, movers declared first; `s1`/`s2` move once by `context.rng` offsets, then disrupt, rewrite one own core cell, attack. | Is spreading the dominant response (H3d)? |

## Fingerprints (`agent_revisions.agent_revision_fingerprint`)

These are frozen in `tools/research/v6/e2/matrix.py` (`AGENT_FINGERPRINTS`); an E2 run whose
live fingerprints differ fails closed.

| Fixture | Fingerprint |
|---|---|
| `v4_probe` | `b82bc724f25806b05936bf1d720c22c04461a535adaede6c29f1de0049f29481` |
| `v4_probe_twin` | `aafd37631d00860f5d141b977342828648f51e183ff91d9b3ce623af88713ef6` |
| `e2_sniper` | `eecafc0cae4f34e3e9cbc8b75a0eab6e27297dc7b90d45086e22a7478ecc8362` |
| `e2_sniper_twin` | `f93b3a0375b894c2b754ee0e55f9512f60295f9c67c794096a9baa5f352c1ffa` |
| `e2_repair_guard` | `c105311e7e3ad91a9a4bb9d93926fd980aa50ce535c0fd2709faffb3b7cd5554` |
| `e2_repair_guard_twin` | `a980718222abcbed2e53700d1b9a3075124025ec0436514cebf355fec94a8b85` |
| `e2_disrupt_guard` | `11ae6de4490e3c7cf6a208103d6d7625a636ea64a05a56630d3758f53dbd643c` |
| `e2_disrupt_guard_twin` | `c7e26b0d0d949c46f103c2fe37ab042e642b8fe8b24bbc4f729e36547c654773` |
| `e2_min_guard` | `e99f2245378aa5a21cfa49016ad7908ad521746ce93d1796b4426034f2ab768b` |
| `e2_min_guard_twin` | `3a82910b46177ba129c0ddd9247903120d6aaa45b0e95d307fa634e50861007d` |
| `e2_greedy_painter` | `cafd8340920d0ebdf4d602bd0a797958f9e4d8ed5528a5c0f0f476dc463a70ed` |
| `e2_greedy_painter_twin` | `0765e65a42923f526fac9b24c73a834c9f6832e5b658dbaefc84bfefec4e6780` |
| `e2_guarded_painter` | `2b1ccd067cdba08e8691e3eab0125bb8188162f74cae6df42087b10cc46e7abf` |
| `e2_guarded_painter_twin` | `8eb24d11b0e56d8df8c944a62209bfc89a8cc61adb59fef3037d9c015d896438` |
| `e2_counter` | `fce2b5969bd2332e0b527cd63ace7973104710a98d85bb51225b0a497fcaeb79` |
| `e2_counter_twin` | `ba5e8d9f773b13eb294fa048659404e532dde9472249be8ebe4eedda4bb9f1eb` |
| `e2_spread_sniper` | `f44b4dd24635903559a61d7bcf1cadb58074db2b153a28742e274bbcb5d52995` |
| `e2_spread_sniper_twin` | `816f193b16b2b40d016b515f0e28be77cc93456f730d24b4f82f1fef96679979` |
| `e2_spread_defender` | `95a115243ecc9980cffc6517af1e0f72fc24890c42b2578812eea42f832930c0` |
| `e2_spread_defender_twin` | `a5d65adacf515e94e0d0ecc36149710f136a882ead94d3ab489073eda480a09b` |
