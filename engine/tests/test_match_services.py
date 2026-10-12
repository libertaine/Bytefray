"""Characterization tests for shared scoring/winner-resolution helpers.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
removed ``core.Kernel`` (VM match execution) and this file's Kernel-driven
kill-attribution/summary/replay-sink cases along with it. ``resolve_winner``
and ``ScoringPolicy`` are Ruleset-agnostic pure functions with no VM
dependency of their own; their tests survive unchanged.
"""

from __future__ import annotations

from battle_engine.agent_state import Agent
from battle_engine.config import Weights
from battle_engine.results import resolve_winner
from battle_engine.scoring import ScoringPolicy


def test_winner_resolution_preserves_survival_score_fallback_and_ties():
    agents = [Agent("A", 0), Agent("B", 1)]
    assert resolve_winner(agents, {"A": 10, "B": 1}, "survival") == ""
    assert resolve_winner(agents, {"A": 10, "B": 1}, "score_fallback") == "A"
    assert resolve_winner(agents, {"A": 10, "B": 10}, "score_fallback") == ""
    agents[1].alive = False
    assert resolve_winner(agents, {"A": 0, "B": 99}, "survival") == "A"


def test_scoring_policy_preserves_alive_and_territory_buckets():
    agents = [Agent("A", 0), Agent("B", 1, alive=False)]
    score: dict[str, int | float] = {"A": 0, "B": 0}
    policy = ScoringPolicy(Weights(alive=1.5, kill=7, territory=2, territory_bucket=3))
    policy.score_alive(score, agents)
    policy.score_territory(score, agents, {"A": 7, "B": 2})
    assert score == {"A": 5.5, "B": 0}
    policy.score_kill(score, "A")
    assert score["A"] == 12.5
