# V5 Research-Only Agents (Phase R4)

**These agents are research instruments, not part of Bytefray's product.**

Nothing in this directory is a bundled starter, a shipped example, a GUI
default, an evaluation default, an installer asset, or a member of the
canonical V4 agent population. This directory is deliberately *not*
`agents/` (the writable agent catalog `battle_engine.agents.resolve_agent`
searches) and is not listed in `battle_engine.starters.STARTER_AGENT_NAMES`,
so no normal CLI, Designer, GUI, tournament, or evaluation code path can
reach these agents. They are loaded only by `tools/research/v5/r4_runner.py`
(and the R4 tests), which resolves each directory explicitly through the
public `battle_engine.agents.agent_spec_from_dir`.

They are kept separate from `tools/research/v5/agents/` (R3's directory) so
that each phase's instrument set remains exactly what that phase froze:
R3's containment test asserts its research directory holds precisely the
three agents R3 created, and that assertion still holds unchanged.

They exist to answer exactly one question, posed by
`docs/research/v5/V5_R4_COMPETENCE_CONTROLLED_POPULATION.md`:

> Under unchanged stable `bytefray-rules-4`, does a population of legal
> Agent API v2 agents that can actually express the game's victory
> objective still show Phase 0's combat-to-victory conversion deficit?

All five are ordinary, fully legal Agent API v2 entrants running under the
permanent stable Ruleset `bytefray-rules-4`. None receives privileged engine
state, enemy core coordinates, the R2 objective oracle, R1 process
integrity, extra actions, extra reach, or any observation field an ordinary
bundled entrant does not also receive. This is proven from trace and replay
by `engine/tests/test_v5_research_r4_agents.py`, not asserted here.

| Agent | Archetype | Procs | Reach | Distinguishing behaviour |
|---|---|:--:|---|---|
| `v5r4_siege_regional` | A — regional pressure attacker | 1 | 24 | Infers a core base from first contact, READ-verifies it, and cycles writes across a whole core-width region. No defence at all. |
| `v5r4_recon_striker` | B — mobile reconnaissance attacker | 1 | 40 | Crosses the arena probing with READs; strikes the longest contiguous run of *READ-derived* enemy-held cells. No defence. |
| `v5r4_core_warden` | C — objective-capable defender | 1 | 12 | Holds a station covering all eight of its own core cells, inspects them on a reserved duty cycle, and repairs what it finds lost. Never searches. |
| `v5r4_dual_operator` | D — balanced generalist | 2 | 32 / 12 | A pursuing `raider` sweeping a region around the contact plus a `keeper` blind-refreshing its own core. Half the quota each. |
| `v5r4_territory_expander` | E — territory / exploration | 1 | 16 | Claims contiguous blocks of ground, and presses a region around a contact for a bounded window before returning to expansion. |

The sixth member of the R4 evaluation population is the **unchanged bundled
`v4_quorum`**, retained rather than imitated (R4 charter Section 6F). It is
not copied into this directory, and its source was not modified.

Do not add these to `agents/`, to `STARTER_AGENT_NAMES`, to any benchmark
population, or to any documentation that implies they are a V5 feature.
Whether any of them should ever inform a shipped example is a separate
product decision that R4 does not make.
