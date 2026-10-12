"""Legal, non-payoff capability histories through the unchanged E8 engine."""

import pytest
from _e8_family_engine_harness import T8, Plan, agent_stream, callbacks_by_tick, play, sigma_of
from _e9_harness import engine_history
from battle_engine.agent_api import ActionKindV2
from test_v6_e8_family_engine import decoy_opponent, first_mover_tick, other

from tools.research.v6.e8.family import package_id
from tools.research.v6.e9.oracle import Expected, advance


def check_oracle(agent, captures):
    expected = Expected()
    # Reconstruct adapter evidence from callback observations and the actual
    # preceding action, independently of production receipt diagnostics.
    buffered = []
    by_tick = {}
    previous = None
    for capture in captures:
        if previous is not None and previous.purpose == "verify" and previous.action.kind == ActionKindV2.SENSE:
            obs = capture.obs
            assert obs.previous_action_tick == previous.obs.current_tick
            assert obs.previous_action_applied and obs.previous_sense_anchors is not None
            buffered.append((previous.obs.current_tick, previous.action.operand,
                             previous.action.operand in obs.previous_sense_anchors))
        if capture.index == 1:
            by_tick[capture.obs.current_tick] = tuple(buffered)
            buffered = []
        previous = capture
    for row in agent.diagnostics():
        assert tuple(row["before"].values()) == expected
        samples = by_tick[row["tick"]]
        fresh = tuple(s for s in samples if s[0] >= row["tick"] - 1)
        actual = tuple((r["issued_tick"], r["target"], r["present"]) for r in row["receipts"])
        assert fresh == actual
        expected = advance(expected, row["epoch"], row["tick"], samples)
        assert tuple(row["after"].values()) == expected


@pytest.mark.parametrize("seat", ["A", "B"])
def test_qc14_static_and_on_hit_opportunity(tmp_path, seat):
    plan = decoy_opponent(seat, evade=(64 * sigma_of(7, seat),))
    played, agent, captures = engine_history(tmp_path, seat, "Variant()", plan, ticks=32)
    check_oracle(agent, captures)
    rows = agent.diagnostics()
    if seat == "B":
        # Genuine lost opportunity: repeated evasion breaks the confirmation
        # run. Do not alter on-hit timing to manufacture a second success.
        assert rows and all(r["after"]["mode"] == 1 for r in rows)
        assert any(r["receipts"] and not r["receipts"][0]["present"] for r in rows)
        assert all(r["after"]["c"] < 2 for r in rows)
        return
    assert [r["after"]["mode"] for r in rows if r["reason"] != "stay"] == [4, 1]
    saved = [c for c in captures if c.index == 1 and c.mode == 4 and c.action.kind == ActionKindV2.WRITE]
    assert saved
    restored = next(r for r in rows if r["reason"] == "missing")
    assert restored["epoch"] % 4 != 0
    assert any(c.obs.current_tick == restored["tick"] and c.index == 1
               and c.mode == 1 and c.purpose == "verify" for c in captures)
    assert any(c.obs.current_tick >= restored["tick"] and c.action.kind == ActionKindV2.WRITE for c in captures)
    assert played.decisions(seat)


@pytest.mark.parametrize("seat", ["A", "B"])
def test_qc14_static_contact(tmp_path, seat):
    played, agent, captures = engine_history(tmp_path, seat, "Variant()", decoy_opponent(seat), ticks=16)
    check_oracle(agent, captures)
    assert any(r["reason"] == "confirmations" for r in agent.diagnostics())
    assert any(c.index == 1 and c.mode == 4 and c.action.kind == ActionKindV2.WRITE for c in captures)
    assert played.decisions(seat)


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("offer", range(1, 9))
def test_qc12_every_hit_position_partial_ticks_and_full_suppression(tmp_path, seat, offer):
    tick = first_mover_tick(other(seat), 1)
    # Exercise every opponent offer before core capture can end the history.
    moves = {(t, n): 64 * sigma_of(7, seat) for t in range(1, tick + 1) for n in range(1, 9)
             if t < tick or n < offer}
    plan = Plan(moves=moves, hits={(tick, offer): None}, repair=8)
    played, agent, captures = engine_history(tmp_path, seat, 'Variant("fixed", Mode.DENSE)',
                                           plan, ticks=tick + 1, distance=200)
    counts = callbacks_by_tick(played.records, seat)
    expected = 2 * ((offer - 1) // 2)
    assert counts.get(tick, 0) == expected
    assert counts[tick + 1] > 0
    hits = [r for r in played.decisions(other(seat)) if r["observation"]["current_tick"] == tick
            and r["action"]["kind"] == "write" and r["action"]["operand"] == 100]
    assert len(hits) == 1 and hits[0]["applied_result"]["status"] == "APPLIED"
    assert len([c for c in captures if c.obs.current_tick == tick]) == expected
    assert agent.epoch == len(counts) - 1  # suppressed ticks invent no opportunity epochs


@pytest.mark.parametrize("seat", ["A", "B"])
def test_qc12_repeated_suppression_and_phase_preservation(tmp_path, seat):
    tick = first_mover_tick(other(seat), 4)
    plan = decoy_opponent(seat, hits=((tick, 2), (tick + 2, 2), (tick + 4, 2)))
    # Repeat full denial whenever the opponent moves first; intervening
    # ticks still offer callbacks. Long gaps are separately synthetic.
    played, agent, captures = engine_history(tmp_path, seat, "Variant()", plan, ticks=tick + 6)
    check_oracle(agent, captures)
    counts = callbacks_by_tick(played.records, seat)
    assert counts.get(tick, 0) == 0
    assert agent.epoch == len(counts) - 1
    assert captures[-1].obs.current_tick > tick


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("mode,member", [("OFF", "RUSH8"), ("DENSE", "REACQ8")])
def test_qc1_qc11_legal_frozen_twin_search_and_core_fidelity(tmp_path, seat, mode, member):
    rng = agent_stream(7, seat)
    rng.randrange(2)
    rng.randrange(2)
    tau = (-1, 1)[rng.randrange(2)]
    tick = first_mover_tick(other(seat), 2)
    plan = Plan(moves={tick: -46 * tau}, hits={(tick, 3): None}, repair=8)
    current, agent, captures = engine_history(tmp_path / "new", seat, f'Variant("fixed", Mode.{mode})',
                                              plan, ticks=tick + 3)
    roster = (package_id(member), plan) if seat == "A" else (plan, package_id(member))
    frozen = play(tmp_path / "frozen", T8, *roster, starts=current.starts, seed=7, ticks=tick + 3)
    assert current.stream("A") == frozen.stream("A")
    assert current.stream("B") == frozen.stream("B")
    assert agent.rng.getstate() == frozen.agents[seat].rng.getstate()
    assert agent.enemy_core == frozen.agents[seat].enemy_core
    if mode == "DENSE":
        searches = [c for c in captures if c.purpose == "search" and c.action.kind == ActionKindV2.SENSE]
        assert len(searches) >= 2
        assert searches[0].obs.current_tick == tick and searches[1].obs.current_tick == tick + 1
        assert searches[1].search_before == searches[0].search_after
        assert agent.replacements == frozen.agents[seat].replacements and agent.replacements
