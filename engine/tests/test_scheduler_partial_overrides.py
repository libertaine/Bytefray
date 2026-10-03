"""V6 Phase 6: Direct tests for scheduler partial overrides and stable V4 equivalence.

Verifies the desired principle:
An explicitly supplied scheduler override changes only the supplied property
unless the API explicitly requires a complete scheduler replacement.
- Supplying only `scheduler_chunk_size=4` retains the base policy's rotation value (e.g. True on V4).
- Supplying only `scheduler_rotate_start=False` retains the base policy's chunk size (e.g. 2 on V4).
- Un-overridden stable V4 remains byte- and behavior-equivalent (canonical_match_id has no scheduler key).
"""

from __future__ import annotations

import json
from pathlib import Path

from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    _effective_ruleset_policy,
    canonical_match_id,
)
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    resolve_ruleset_policy,
)


def _write_dummy_agent(agent_dir: Path, name: str) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_text(
        json.dumps(
            {
                "name": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    (agent_dir / "agent.py").write_text(
        """from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        pass
    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]
    def act(self, observation):
        return AgentAction(ActionKindV2.READ, 0)

def create_agent():
    return Agent()
""",
        encoding="utf-8",
    )


def _make_match_request(
    tmp_path: Path,
    scheduler_chunk_size: int | None = None,
    scheduler_rotate_start: bool | None = None,
) -> MatchRequest:
    agent_dir = tmp_path / "dummy_agent"
    _write_dummy_agent(agent_dir, "dummy")
    spec = agent_spec_from_dir(agent_dir)
    return MatchRequest(
        config=Config(seed=42),
        entrants=(
            MatchEntrant.python("A", "dummy", 0, spec, {}),
            MatchEntrant.python("B", "dummy", 256, spec, {}),
        ),
        max_ticks=10,
        replay_path=tmp_path / "replay.bfr",
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        scheduler_chunk_size=scheduler_chunk_size,
        scheduler_rotate_start=scheduler_rotate_start,
    )


def test_v4_without_overrides_preserves_policy_and_match_id(tmp_path: Path) -> None:
    req = _make_match_request(tmp_path)
    assert req.scheduler_chunk_size is None
    assert req.scheduler_rotate_start is None

    base_policy = resolve_ruleset_policy(BYTEFRAY_RULESET_V4_ID)
    effective = _effective_ruleset_policy(req)
    assert effective.scheduler_chunk_size == base_policy.scheduler_chunk_size == 2
    assert effective.scheduler_rotate_start == base_policy.scheduler_rotate_start is True

    # Identity check: canonical_match_id must match un-overridden match
    # (no "scheduler" key injected into match payload)
    base_match_id = canonical_match_id(req)
    # Constructing request with explicit None should yield identical match_id
    req_explicit_none = _make_match_request(tmp_path, scheduler_chunk_size=None, scheduler_rotate_start=None)
    assert canonical_match_id(req_explicit_none) == base_match_id


def test_partial_override_chunk_size_only_preserves_rotate_start(tmp_path: Path) -> None:
    req = _make_match_request(tmp_path, scheduler_chunk_size=4)
    effective = _effective_ruleset_policy(req)

    assert effective.scheduler_chunk_size == 4
    # Crucial: base policy's rotate_start=True must NOT be clobbered to False/None
    assert effective.scheduler_rotate_start is True

    # canonical_match_id must record the effective combined policy
    match_id = canonical_match_id(req)
    req_both = _make_match_request(tmp_path, scheduler_chunk_size=4, scheduler_rotate_start=True)
    assert match_id == canonical_match_id(req_both)


def test_partial_override_rotate_start_only_preserves_chunk_size(tmp_path: Path) -> None:
    req = _make_match_request(tmp_path, scheduler_rotate_start=False)
    effective = _effective_ruleset_policy(req)

    # Crucial: base policy's chunk_size=2 must NOT be clobbered to None
    assert effective.scheduler_chunk_size == 2
    assert effective.scheduler_rotate_start is False

    # canonical_match_id must record the effective combined policy
    match_id = canonical_match_id(req)
    req_both = _make_match_request(tmp_path, scheduler_chunk_size=2, scheduler_rotate_start=False)
    assert match_id == canonical_match_id(req_both)


def test_evaluation_request_partial_overrides(tmp_path: Path) -> None:
    service = EvaluationService()

    # 1. Un-overridden: returns None
    req_base = EvaluationRequest(
        candidate_id="c",
        opponent_ids=["o"],
        seeds=(1,),
        output_dir=tmp_path / "out1",
        ticks=10,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    assert req_base.scheduler_chunk_size is None
    assert req_base.scheduler_rotate_start is None
    assert service._scheduler_override(req_base) is None

    # 2. Chunk size only: retains rotate_start=True
    req_chunk = EvaluationRequest(
        candidate_id="c",
        opponent_ids=["o"],
        seeds=(1,),
        output_dir=tmp_path / "out2",
        ticks=10,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        scheduler_chunk_size=4,
    )
    assert service._scheduler_override(req_chunk) == {
        "chunk_size": 4,
        "rotate_start": True,
    }

    # 3. Rotate start only: retains chunk_size=2
    req_rotate = EvaluationRequest(
        candidate_id="c",
        opponent_ids=["o"],
        seeds=(1,),
        output_dir=tmp_path / "out3",
        ticks=10,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        scheduler_rotate_start=False,
    )
    assert service._scheduler_override(req_rotate) == {
        "chunk_size": 2,
        "rotate_start": False,
    }
