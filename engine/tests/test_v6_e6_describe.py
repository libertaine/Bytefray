"""V6 E6: the descriptive sections (pre-registration Sec 6.2-6.3).

Alternation reuses E4's cell metrics on real replays of scripted,
non-family agents. Seat and parity reporting runs on hand-built summary
lines. Neither is an input to any hypothesis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService

from tools.research.v6.e6 import describe, family

IDLE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("p", 256, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.WRITE, observation.own_core_base, 0xCE)


def create_agent():
    return Agent()
"""


def test_alternation_reports_e4_cell_metrics_for_every_cell(tmp_path: Path) -> None:
    env = tmp_path / "env"
    for name in ("idle_a", "idle_b"):
        directory = env / "agents" / name
        directory.mkdir(parents=True)
        (directory / "agent.yaml").write_text(json.dumps({"name": name, "kind": "python", "api_version": 2,
                                                          "entrypoint": "agent.py:create_agent",
                                                          "version": "1.0.0"}), encoding="utf-8")
        (directory / "agent.py").write_text(IDLE, encoding="utf-8")
    out = tmp_path / "field" / "00-idle_a"
    EvaluationService().run(EvaluationRequest(
        candidate_id="idle_a", opponent_ids=["idle_b"], seeds=(1,), ticks=30, arena_size=512,
        ruleset_id="bytefray-rules-6-research-sensing-r32", output_dir=out, data_root=env))
    cells = json.loads((out / "evaluation.json").read_text(encoding="utf-8"))["cells"]
    report = describe.alternation(out, cells)
    assert len(report["cells"]) == 2
    for metrics in report["cells"].values():
        assert metrics["fma"]["status"] in ("DEFINED", "DECIDED_EARLY")
        assert metrics["checks"]
    assert sum(report["fma_status"].values()) == 2


def _line(a: str, b: str, **summary: Any) -> dict[str, Any]:
    base = {"saw_first": None, "first_detection_callback": {"A": None, "B": None},
            "first_detection": {"A": None, "B": None}, "first_move": {"A": None, "B": None}}
    return {"seat_a": family.package_id(a), "seat_b": family.package_id(b), "summary": {**base, **summary}}


def test_seat_and_parity() -> None:
    lines = [
        _line("RUSH", "GUARD", saw_first="A", first_detection_callback={"A": 3, "B": None}),
        _line("GUARD", "RUSH", saw_first="B", first_detection_callback={"A": None, "B": 2}),
        _line("SPLIT", "LURK", saw_first=None),
        # EVADER in Seat B, seen by A before its evade MOVE: caught on core.
        _line("RUSH", "EVADER", saw_first="A", first_detection_callback={"A": 1, "B": None},
              first_detection={"A": [1, 0], "B": None}, first_move={"A": None, "B": [1, 2]}),
        # EVADER in Seat A moves first: not caught on core.
        _line("EVADER", "RUSH", first_detection={"A": None, "B": [1, 5]}, first_move={"A": [1, 0], "B": None}),
    ]
    report = describe.seat_and_parity(lines)
    assert report["first_detection_seat"] == {"A": 2, "B": 1, "None": 2}
    assert report["fast_searcher_arrival_parity"]["RUSH"] == {"A:odd": 2, "B:even": 1, "B:none": 1}
    assert report["fast_searcher_arrival_parity"]["SPLIT"] == {"A:none": 1}
    assert report["evader_caught_on_core_by_seat"] == {"A": {"not_caught_on_core": 1}, "B": {"caught_on_core": 1}}
