"""R4 population definition, preregistration manifest, and seed discipline.

V5 research Phase R4 asks one question
(docs/research/v5/V5_R4_COMPETENCE_CONTROLLED_POPULATION.md):

    Does a competence-controlled, strategically diverse population still
    exhibit Phase 0's high timeout / tie / stagnation / failed-post-contact
    conversion behaviour under unchanged stable ``bytefray-rules-4``?

The experimental factor is the AGENT POPULATION and nothing else. Ruleset,
arena size, tick limit, quota, slot-order policy, scoring and seed set are
Phase 0's, reused rather than re-chosen.

**Seed discipline (R4 charter Section 10).** Two disjoint seed sets exist
and this module is the single place either is defined:

* :data:`DEVELOPMENT_SEEDS` -- used for debugging, archetype development and
  competence qualification. Deliberately outside Phase 0's canonical set.
* :data:`EVALUATION_SEEDS` -- Phase 0's own seeds, used once, after the
  population is frozen. No agent's gameplay behaviour may be edited after
  evaluation on these begins; if it is, the evaluation is invalidated,
  fingerprints are re-frozen, and the corpus restarts from the beginning.

Nothing here writes to the ``agents/`` catalog, the starter list, the GUI,
the installer, or any product surface. The R4 research agents are resolved
only through the explicit research directory, exactly as R3's were.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from battle_engine.agent_revisions import agent_revision_fingerprint
from battle_engine.agents import AgentSpec, agent_spec_from_dir

RESEARCH_AGENTS_DIR = Path(__file__).resolve().parent / "r4_agents"
CANONICAL_AGENTS_DIR = REPO_ROOT / "agents"

# -- seed discipline ------------------------------------------------------

#: Qualification / development only. Disjoint from Phase 0's evaluation set
#: by construction; asserted disjoint by ``test_v5_research_r4_population``.
DEVELOPMENT_SEEDS: tuple[int, ...] = (101, 102, 103, 104, 105, 106, 107, 108)

#: Phase 0's canonical evaluation seeds, reproduced exactly.
EVALUATION_SEEDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8)

# -- frozen match configuration (Phase 0's, unchanged) --------------------

RULESET_ID = "bytefray-rules-4"
ARENA_SIZE = 512
MAX_TICKS = 1000
INSTR_PER_TICK = 8
SLOT_ORDER_POLICY = "full ordered round robin, both slot orders enumerated"

# -- the population -------------------------------------------------------

#: Every R4 evaluation population member, in a fixed order.
#:
#: ``source`` is ``"research"`` for agents resolved from
#: ``tools/research/v5/r4_agents/`` and ``"canonical"`` for a bundled V4 agent
#: retained unchanged. ``v4_quorum`` is retained rather than imitated per
#: R4 charter Section 6F: it is the population's existing multi-process
#: coordinated strategy and its source is the one in-repository existence
#: proof that stable V4 permits region-aligned objective play.
R4_POPULATION: tuple[dict[str, Any], ...] = (
    {
        "identifier": "v5r4_siege_regional",
        "source": "research",
        "archetype": "A - regional pressure attacker",
        "targeting": "first-contact core-base hypothesis, READ-verified",
        "movement": "station-keeping; drifts only while unacquired",
        "write_geometry": "core-width burst cycling base..base+7",
        "defense": "none",
        "legal_information": (
            "visible_enemy_anchor_addresses, previous_read_owner, "
            "own_core_size, self_anchor, self_reach, arena_size"
        ),
    },
    {
        "identifier": "v5r4_recon_striker",
        "source": "research",
        "archetype": "B - mobile reconnaissance attacker",
        "targeting": "READ-derived ownership evidence; longest enemy-held run",
        "movement": "high - crosses the arena in reach-sized strides",
        "write_geometry": "core-width window anchored on the evidence run",
        "defense": "none",
        "legal_information": (
            "visible_enemy_anchor_addresses, previous_read_owner, "
            "previous_action_applied, own_core_base/size, self_anchor, "
            "self_reach, arena_size"
        ),
    },
    {
        "identifier": "v5r4_core_warden",
        "source": "research",
        "archetype": "C - objective-capable defender",
        "targeting": "own core cells by READ inspection; opportunistic contact",
        "movement": "minimal - holds a station covering its own core",
        "write_geometry": "repair of own core cells; local counter-pressure",
        "defense": "primary - inspects and repairs all eight own cells",
        "legal_information": (
            "own_core_base, own_core_size, previous_read_owner, "
            "visible_enemy_anchor_addresses, self_anchor, self_reach, arena_size"
        ),
    },
    {
        "identifier": "v5r4_dual_operator",
        "source": "research",
        "archetype": "D - balanced generalist",
        "targeting": "remembered nearest contact address (no core inference)",
        "movement": "moderate - raider pursues, keeper holds",
        "write_geometry": "two-core-width sweep centred on the contact",
        "defense": "secondary - blind rotation repair of own core",
        "legal_information": (
            "self_process_id, visible_enemy_anchor_addresses, "
            "own_core_base/size, self_anchor, self_reach, arena_size"
        ),
    },
    {
        "identifier": "v5r4_territory_expander",
        "source": "research",
        "archetype": "E - territory / exploration strategy",
        "targeting": "nearest contact, bounded press window only",
        "movement": "high - strides between claim blocks",
        "write_geometry": "contiguous claim blocks; bounded contact sweep",
        "defense": "incidental (territory only)",
        "legal_information": (
            "visible_enemy_anchor_addresses, own_core_base/size, "
            "self_anchor, self_reach, current_tick, arena_size"
        ),
    },
    {
        "identifier": "v4_quorum",
        "source": "canonical",
        "archetype": "F - multi-process coordinated strategy (unchanged bundled agent)",
        "targeting": "contact memory, first-contact core candidates, READ evidence",
        "movement": "role-dependent deployment and patrol",
        "write_geometry": "16-offset siege order, core-aligned first eight",
        "defense": "guardian role repairs own core; adaptive reserve",
        "legal_information": (
            "visible_enemy_anchor_addresses, previous_read_owner, "
            "own_core_base/size, temporal observation fields, rng"
        ),
    },
)

R4_POPULATION_IDS: tuple[str, ...] = tuple(
    member["identifier"] for member in R4_POPULATION
)

#: Qualification fixtures (R4 charter Section 13). These are bundled V4
#: agents used ONLY as development-seed opponents to demonstrate that each
#: archetype's intended mechanism functions. None of them is a member of the
#: R4 evaluation population, so qualification cannot contaminate evaluation.
#: No fixture was written for this phase and no fixture is aligned to any
#: R4 agent's attack pattern.
QUALIFICATION_FIXTURES: tuple[str, ...] = (
    "v4_local_defender",
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_scout",
)


def load_research_agent_specs() -> dict[str, AgentSpec]:
    """Resolve every research-only agent directly from the research tree.

    Deliberately not ``battle_engine.agents.resolve_agent``: these agents are
    kept out of the writable ``agents/`` catalog precisely so that no product
    code path can reach them (see ``r4_agents/README.md``).

    R4's agents live in their own directory rather than alongside R3's so
    that each phase's instrument set stays exactly what its own phase froze:
    R3's containment test asserts its research directory holds precisely the
    three agents R3 created, and that assertion must keep holding unchanged.
    """

    specs: dict[str, AgentSpec] = {}
    for child in sorted(RESEARCH_AGENTS_DIR.iterdir()):
        if not child.is_dir():
            continue
        spec = agent_spec_from_dir(child)
        if spec is not None:
            specs[spec.name] = spec
    return specs


def source_path(identifier: str) -> Path:
    """Repository-relative directory backing one population member."""

    for member in R4_POPULATION:
        if member["identifier"] == identifier:
            if member["source"] == "research":
                return RESEARCH_AGENTS_DIR / identifier
            return CANONICAL_AGENTS_DIR / identifier
    raise KeyError(f"not an R4 population member: {identifier!r}")


def population_fingerprints() -> dict[str, str]:
    """Frozen source fingerprint for every population member."""

    return {
        member["identifier"]: agent_revision_fingerprint(
            source_path(member["identifier"])
        )
        for member in R4_POPULATION
    }


def declared_processes(identifier: str) -> list[dict[str, Any]]:
    """Read back what an agent actually declares, by instantiating it.

    Phase 0's published reach table was wrong for all six canonical agents
    (R3 Section C.1) because it was transcribed rather than executed. R4's
    manifest is therefore generated from ``declare_processes()`` return
    values, never from documentation.
    """

    import random

    from battle_engine.agent_api import MatchContextV2, load_python_agent

    spec = agent_spec_from_dir(source_path(identifier))
    if spec is None:
        raise ValueError(f"could not resolve an agent spec for {identifier!r}")
    loaded = load_python_agent(spec)
    instance = loaded.instance
    context = MatchContextV2(
        agent_id="A",
        seed=0,
        arena_size=ARENA_SIZE,
        tick_limit=MAX_TICKS,
        rng=random.Random(0),
    )
    instance.reset(context)  # type: ignore[arg-type]
    declarations = instance.declare_processes()  # type: ignore[union-attr]
    return [
        {"process_id": d.id, "reach": d.reach, "share": d.share} for d in declarations
    ]


def build_population_manifest() -> dict[str, Any]:
    """The preregistered R4 population manifest.

    Written BEFORE any evaluation seed is executed and never altered on the
    basis of an evaluation outcome (R4 charter Section 11).
    """

    entrants = []
    for member in R4_POPULATION:
        identifier = member["identifier"]
        processes = declared_processes(identifier)
        entrants.append(
            {
                **member,
                "source_path": str(
                    source_path(identifier).relative_to(REPO_ROOT)
                ).replace("\\", "/"),
                "source_fingerprint": agent_revision_fingerprint(
                    source_path(identifier)
                ),
                "api_version": 2,
                "process_count": len(processes),
                "processes": processes,
                "total_declared_reach": sum(p["reach"] for p in processes),
            }
        )

    return {
        "phase": "V5 R4 - competence-controlled population",
        "ruleset_id": RULESET_ID,
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "instr_per_tick": INSTR_PER_TICK,
        "slot_order_policy": SLOT_ORDER_POLICY,
        "development_seeds": list(DEVELOPMENT_SEEDS),
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "process_mortality": False,
        "objective_target_oracle": False,
        "scoring": "stable V4: alive + territory + kill, score fallback at tick limit",
        "corpus_shape": {
            "population_size": len(R4_POPULATION),
            "ordered_pairings": len(R4_POPULATION) ** 2,
            "seeds": len(EVALUATION_SEEDS),
            "total_matches": len(R4_POPULATION) ** 2 * len(EVALUATION_SEEDS),
            "self_play_included": True,
        },
        "qualification_fixtures": list(QUALIFICATION_FIXTURES),
        "entrants": entrants,
    }


# -- preregistered interpretation gate -----------------------------------

#: R4 charter Section 17. Declared BEFORE any evaluation seed is run, and
#: justified against Phase 0's measured baseline rather than chosen to fit an
#: outcome. Each dimension names the Phase 0 value it is compared against.
#:
#: The gate is deliberately multi-factor and deliberately does not require
#: every metric to improve: a healthier strategic population may well produce
#: longer, more interactive matches (charter Section 17), so duration and
#: even tie rate are read as context, not as pass/fail criteria on their own.
INTERPRETATION_GATE: dict[str, Any] = {
    "comparison_baseline": "Phase 0 canonical bundled population, 288 matches",
    "primary_axis": "post-contact conversion",
    "criteria": {
        "C1_capture_rate": {
            "metric": "matches with >= 1 core capture, as a share of all matches",
            "phase0_value_pct": 39.58,
            "strong_threshold_pct": 55.0,
            "partial_threshold_pct": 45.0,
            "justification": (
                "Phase 0's decisive rate was 39.58%. A +15pp absolute rise "
                "(to 55%) makes core capture the modal outcome rather than "
                "the minority one, which is the qualitative change the "
                "population-confound hypothesis predicts. +5pp (45%) is the "
                "smallest rise that exceeds the spread Phase 0 already shows "
                "between its own matchups."
            ),
        },
        "C2_contacted_no_capture": {
            "metric": "share of contact matches that never reach a core capture",
            "phase0_value_pct": 55.47,
            "strong_threshold_pct": 40.0,
            "partial_threshold_pct": 48.0,
            "justification": (
                "This is the charter's central 'failed post-contact "
                "conversion' quantity. Phase 0 leaves 55.47% of contact "
                "matches unconverted. Falling below 40% means a competent "
                "population converts most of the contact it generates."
            ),
        },
        "C3_timeout_rate": {
            "metric": "share of matches reaching the tick limit",
            "phase0_value_pct": 60.42,
            "strong_threshold_pct": 45.0,
            "partial_threshold_pct": 55.0,
            "justification": (
                "Timeout is the pathology Phase 0 named. A drop below 45% "
                "makes decisive resolution the majority outcome."
            ),
        },
        "C4_max_simultaneous_deficit": {
            "metric": "mean of the per-match maximum simultaneous core deficit",
            "phase0_value": 4.125,
            "strong_threshold": 5.5,
            "partial_threshold": 4.6,
            "justification": (
                "Simultaneity, not coverage, is what capture requires "
                "(R3 Section H.2). Phase 0's mean best deficit is 4.125 of 8."
            ),
        },
        "C5_stagnation": {
            "metric": "mean stagnation ticks per match",
            "phase0_value": 432.1,
            "strong_threshold": 300.0,
            "partial_threshold": 380.0,
            "justification": (
                "Phase 0 spends 63.5% of match time in >=50-tick intervals "
                "with zero core damage. A fall below 300 ticks (30% of the "
                "cap) means matches are substantively interactive."
            ),
        },
        "C6_diversity_of_winners": {
            "metric": "number of distinct population members with >= 1 win, "
            "and the top member's share of all decisive wins",
            "phase0_value": "5 of 6 members won; v4_quorum took 84 of 162 wins (51.9%)",
            "dominance_threshold_pct": 60.0,
            "justification": (
                "Charter Section 22 Outcome C: conversion may improve because "
                "one design overwhelms the population. A single member taking "
                ">= 60% of all wins is treated as dominance and routes the "
                "verdict to the balance outcome regardless of C1-C5."
            ),
        },
    },
    "decision_rule": {
        "strong_population_confound": (
            "C1, C2 and C3 all meet their STRONG thresholds, AND at least one "
            "of C4/C5 meets its STRONG threshold, AND C6 shows no dominance."
        ),
        "partial_population_confound": (
            "At least C1 and C2 meet their PARTIAL thresholds but the strong "
            "conjunction fails; repeatable post-contact stalls remain visible "
            "across multiple competent archetypes."
        ),
        "balance_is_primary": (
            "C1 meets a threshold but C6 shows dominance (>= 60% of wins to "
            "one member)."
        ),
        "search_is_primary": (
            "Conversion among contact matches meets C2's strong threshold "
            "while the no-contact share rises materially above Phase 0's "
            "11.11%."
        ),
        "mechanical_concern_remains": (
            "C1 fails its partial threshold and C2 fails its partial "
            "threshold while contact is at least as frequent as Phase 0's, "
            "i.e. competent archetypes reach the core region and still do not "
            "convert."
        ),
    },
}
