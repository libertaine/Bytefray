"""Characterization tests for the ``battle_engine.core`` compatibility facade.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
removed VM/blob execution, including ``core.py``'s re-exports of ``VM``,
``enc``, and the twelve opcode constants (see that module's own retirement
comment) and the opcode-encoding/VM-stepping tests this file used to carry
alongside them. What remains -- the shared, still-current re-exports -- is
exercised the same way.
"""

from __future__ import annotations

from battle_engine import core
from battle_engine.agent_state import Agent
from battle_engine.config import Config, Weights


def test_core_reexports_extracted_objects_by_identity():
    assert core.Config is Config
    assert core.Weights is Weights
    assert core.Agent is Agent


def test_configuration_defaults_and_from_dict_are_preserved():
    assert Config() == Config(
        arena_size=4096,
        instr_per_tick=8,
        seed=1337,
        win_mode="score_fallback",
        weights=Weights(1.0, 5.0, 1.0, 64),
    )
    assert Config.from_dict(
        {
            "arena_size": "32",
            "instr_per_tick": "3",
            "seed": "9",
            "win_mode": "survival",
            "weights": {
                "alive": "2.5",
                "kill": "7",
                "territory": "0.5",
                "territory_bucket": "4",
            },
        }
    ) == Config(32, 3, 9, "survival", Weights(2.5, 7.0, 0.5, 4))
