"""Verified sensing playback of a native alpha1 match that ends in core capture."""

from __future__ import annotations

import json

from battle_client.sensing import OmniscientView, PhasePosition, SensingCursor, SensingView
from battle_client.session import ReplaySession
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.sensing_playback import ExchangePhase

B_CORE = tuple(range(91, 99))


def _capture_match(tmp_path):
    """A at 0 WRITEs every cell of B's core at 91; B only READs its own core."""
    specs = []
    for name, script in (("a", [("write", address, 0xDD) for address in B_CORE]), ("b", [])):
        agent_dir = tmp_path / name
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.yaml").write_text(
            f"name: {name}\nkind: python\napi_version: 2\nentrypoint: agent.py:create_agent\n",
            encoding="utf-8",
        )
        (agent_dir / "agent.py").write_text(
            "from battle_engine.agent_api import AgentV2, ProcessDeclaration, AgentAction, ActionKindV2\n"
            f"SCRIPT = {script!r}\n"
            "class Scripted(AgentV2):\n"
            "    def __init__(self): self.calls = 0\n"
            "    def declare_processes(self):\n"
            "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
            "    def act(self, obs):\n"
            "        item = SCRIPT[self.calls] if self.calls < len(SCRIPT) else ('read', obs.own_core_base)\n"
            "        self.calls += 1\n"
            "        return AgentAction(ActionKindV2(item[0]), operand=item[1], value=item[2] if len(item)>2 else None)\n"
            "def create_agent(): return Scripted()\n",
            encoding="utf-8",
        )
        spec = agent_spec_from_dir(agent_dir)
        assert spec is not None
        specs.append(spec)
    replay, trace = tmp_path / "replay.jsonl", tmp_path / "trace.jsonl"
    NativeMatchService().run(
        MatchRequest(
            config=Config(arena_size=512, instr_per_tick=8, seed=0),
            ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
            entrants=(
                MatchEntrant.python("A", "a", 0, specs[0]),
                MatchEntrant.python("B", "b", 91, specs[1]),
            ),
            max_ticks=20,
            replay_path=replay,
            trace_path=trace,
        )
    )
    return replay, trace, tmp_path / "result.json"


def test_core_capture_match_opens_verified_and_agrees_at_every_tick_end(tmp_path):
    replay, trace, result = _capture_match(tmp_path)
    assert json.loads(result.read_text(encoding="utf-8"))["termination_reason"] == (
        "last_agent_standing"
    )
    session = ReplaySession()
    session.load(replay)
    omni = SensingCursor.from_paths(session, replay, trace, None, result_path=result)

    tick_ends = [p for p in omni.positions if p.phase == ExchangePhase.TICK_END]
    for position in tick_ends:
        view = omni.seek(position)
        assert isinstance(view, OmniscientView)
        state = session.current_state
        assert state.arena == view.memory and state.owners == view.owners
        assert {key: p.anchor for key, p in state.processes.items()} == {
            (e, p): a for e, p, a in view.anchors
        }
        assert set(view.alive_entrants) == {aid for aid, a in state.agents.items() if a.alive}
    final = omni.seek(tick_ends[-1])
    assert isinstance(final, OmniscientView)
    assert final.alive_entrants == ("A",)
    assert all(final.owners[address] == "A" for address in B_CORE)


def test_entrant_views_of_capture_match_deliver_no_unsensed_knowledge(tmp_path):
    replay, trace, result = _capture_match(tmp_path)
    for entrant in ("A", "B"):
        session = ReplaySession()
        session.load(replay)
        cursor = SensingCursor.from_paths(session, replay, trace, entrant, result_path=result)
        last = cursor.seek(cursor.positions[-1])
        assert isinstance(last, SensingView)
        assert last.contacts == () and last.samples == ()
        assert last.opponent_activity == "Unobserved"
    assert cursor.seek(PhasePosition(0, None, ExchangePhase.TICK_END)).position.tick == 0
