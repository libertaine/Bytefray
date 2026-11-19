"""Match configuration models extracted from the v0.1 core."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Weights:
    alive: float = 1.0
    kill: float = 5.0
    territory: float = 1.0
    territory_bucket: int = 64


#: The arena size of a newly created normal product match (6.0.0-alpha.1):
#: ``bytefray run``, ``bytefray agents test``, ``bytefray tournament``, the
#: ``agents validate`` dry run, and every Designer surface, matching the
#: 512-cell arena ``agents evaluate`` pins for Active Sensing. An explicit
#: ``--arena`` always wins. ``Config.arena_size`` below keeps its historical
#: 4096 default, which saved matches, recorded evaluations, research protocols
#: and fixtures rely on; product surfaces pass this value explicitly instead.
PRODUCT_ARENA_SIZE: int = 512


@dataclass
class Config:
    arena_size: int = 4096
    instr_per_tick: int = 8
    seed: int = 1337
    win_mode: str = "score_fallback"
    weights: Weights = field(default_factory=Weights)

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> Config:
        w = d.get("weights", {})
        return Config(
            arena_size=int(d.get("arena_size", 4096)),
            instr_per_tick=int(d.get("instr_per_tick", 8)),
            seed=int(d.get("seed", 1337)),
            win_mode=str(d.get("win_mode", "score_fallback")),
            weights=Weights(
                alive=float(w.get("alive", 1.0)),
                kill=float(w.get("kill", 5.0)),
                territory=float(w.get("territory", 1.0)),
                territory_bucket=int(w.get("territory_bucket", 64)),
            ),
        )
