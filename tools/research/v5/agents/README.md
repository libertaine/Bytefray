# V5 Research-Only Agents (Phase R3)

**These agents are research instruments, not part of Bytefray's product.**

Nothing in this directory is a bundled starter, a shipped example, a GUI
default, an evaluation default, or a member of the canonical V4 agent
population. This directory is deliberately *not* `agents/` (the writable
agent catalog `battle_engine.agents.resolve_agent` searches) and is not
listed in `battle_engine.starters.STARTER_AGENT_NAMES`, so no normal CLI,
Designer, GUI, tournament, or evaluation code path can reach these agents.
They are loaded only by `tools/research/v5/r3_runner.py` (and the R3 tests),
which resolves each directory explicitly through the public
`battle_engine.agents.agent_spec_from_dir`.

They exist to answer exactly one question, posed by
`docs/research/v5/V5_R3_AGENT_COMPETENCE.md`:

> Is Phase 0's combat-to-victory conversion deficit a property of stable V4
> mechanics, or of the bundled V4 agent population?

All three are ordinary, fully legal Agent API v2 entrants running under the
permanent stable Ruleset `bytefray-rules-4`. None receives privileged engine
state, enemy core coordinates, the R2 objective oracle, or any observation
field an ordinary bundled entrant does not also receive.

| Agent | Role |
|---|---|
| `v5r3_point_control` | Behavioural clone of the bundled `v4_concentrated_attacker`, used as the paired-construction control (proves the research directory/loader path itself changes no gameplay). |
| `v5r3_region_sweeper` | **The R3 experimental agent.** Identical to the clone except that, where the baseline repeatedly writes one target address `T`, it enumerates a deterministic expanding local sweep around `T` — address selection only, no movement change. |
| `v5r3_region_sweeper_mobile` | Secondary variant: the same sweep, but it repositions (using the baseline's own MOVE formula) to reach a sweep address that is out of reach, instead of skipping it. |

Do not add these to `agents/`, to `STARTER_AGENT_NAMES`, to any benchmark
population, or to any documentation that implies they are a V5 feature.
