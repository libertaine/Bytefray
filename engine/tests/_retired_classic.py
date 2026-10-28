"""The retired Classic policy (``bytefray-rules-4``), frozen for research tests.

Classic's ``RulesetPolicy`` was removed when Active Sensing became Bytefray's
only product Ruleset. Several research identities are documented, and were
verified, as independent literal copies of it; those checks now compare
against this frozen record of its field values instead of a live policy.
Nothing here is registered, resolvable or executable.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from battle_engine.ruleset_policy import RulesetPolicy

#: Every ``RulesetPolicy`` field the retired ``RULESET_V4`` object held, other
#: than its ``ruleset_id``, exactly as Bytefray 5.1.0-alpha.1 shipped it.
RETIRED_CLASSIC_POLICY_FIELDS: dict[str, Any] = {
    "supported_runtime_kinds": frozenset({"python"}),
    "supported_python_api_versions": frozenset({2}),
    "scheduler_mode": "chunked",
    "scheduler_chunk_size": 2,
    "scheduler_rotate_start": True,
    "core_placement": "seeded",
    "process_selection": "round_robin",
    "movement_stride": "fixed_64",
    "movement_displacement": "literal",
    "capture_hold_ticks": 1,
    "disruption_slot_limit": None,
    "scheduler_pass_order": "forward",
    "initial_anchor_placement": "core_base",
    "detection_radius": None,
    "sensing_mode": "passive",
}


def policy_fields(policy: RulesetPolicy) -> dict[str, Any]:
    """Every field of ``policy`` except its ``ruleset_id``."""

    return {f.name: getattr(policy, f.name) for f in fields(policy) if f.name != "ruleset_id"}
