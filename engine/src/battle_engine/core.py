# core.py — compatibility facade for shared match-support types
from __future__ import annotations

from battle_engine.agent_state import Agent
from battle_engine.config import Config, Weights
from battle_engine.results import build_summary, resolve_winner
from battle_engine.scoring import ScoreMap, ScoringPolicy
from battle_engine.statistics import StatisticsCollector, StatisticsMap
from battle_engine.telemetry import (
    JSONLSink,
    JSONSummarySink,
    LegacyRendererObserver,
    ReplayPublisher,
    ReplaySink,
    SummarySink,
    build_snapshot,
)

# `core` is a deliberate compatibility facade (see AGENTS.md's "Compatibility
# surfaces are deliberate, not accidental"): these imports exist so
# `from battle_engine.core import ...` keeps working for names now defined in
# extracted modules. __all__ tells static tools (ruff's F401 among them) that
# every name below is intentionally re-exported, not dead -- without it, an
# "unused import" auto-fix will silently delete a supported public import
# path. Don't collapse or prune this list without checking who still imports
# through it.
#
# V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
# removed this facade's VM-execution-only re-exports -- the ``Kernel`` class
# that used to live in this module, ``MatchRunner``, the twelve VM opcode
# constants, and ``enc`` -- as a deliberate, recorded public-API break, not
# an oversight: ``Kernel``'s own default `ruleset_policy` was
# `RULESET_V1`, an identity Scope C retired from executable registration
# entirely, and `MatchRunner`/opcode execution depend on `vm.VM.step`/
# `load_code`, themselves removed alongside VM/blob execution (see
# `vm.py`). Keeping these importable would have meant retaining real VM
# execution machinery solely so the name still resolved -- exactly what
# this repository's own compatibility-facade policy says not to do.
# Anything still genuinely shared with the retained process runtime (scoring,
# statistics, telemetry, config, the plain `Agent` state type) remains
# re-exported below, unchanged.
__all__ = [
    "Agent",
    "Config",
    "JSONLSink",
    "JSONSummarySink",
    "LegacyRendererObserver",
    "ReplayPublisher",
    "ReplaySink",
    "ScoreMap",
    "ScoringPolicy",
    "StatisticsCollector",
    "StatisticsMap",
    "SummarySink",
    "Weights",
    "build_snapshot",
    "build_summary",
    "resolve_winner",
]
