"""M1-4 AC5/AC7: native witnesses, hostile prefixes, navigation and isolation."""

from __future__ import annotations

import builtins
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

import pytest
from battle_client.perspective import load_sensing_cursor
from battle_client.player import PhasePlaybackController
from battle_client.sensing import (
    OmniscientView,
    PhasePosition,
    SampleStatus,
    SensingCursor,
    SensingProjectionError,
    SensingView,
)
from battle_client.session import ReplaySession
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.sensing_demo import run_sensing_demo
from battle_engine.sensing_playback import (
    ExchangePhase,
    VerificationStatus,
    reconstruct_sensing_playback,
)


def _pair(tmp_path, a, b=(), *, ticks=3, budget=8, a_processes=1):
    """Script legal product actions; no research harness or evidence input."""
    specs = []
    for name, script, count in (("a", a, a_processes), ("b", b, 1)):
        agent_dir = tmp_path / name
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.yaml").write_text(
            f"name: {name}\nkind: python\napi_version: 2\nentrypoint: agent.py:create_agent\n"
            "capabilities: {version: 1, required: [sense]}\n",
            encoding="utf-8",
        )
        (agent_dir / "agent.py").write_text(
            "from battle_engine.agent_api import AgentV2, ProcessDeclaration, AgentAction, ActionKindV2\n"
            f"SCRIPT = {list(script)!r}\n"
            "class Scripted(AgentV2):\n"
            "    def __init__(self): self.calls = 0\n"
            "    def declare_processes(self):\n"
            f"        return [ProcessDeclaration(id=str(i), reach=128, share=1/{count}) for i in range({count})]\n"
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
            config=Config(arena_size=512, instr_per_tick=budget, seed=0),
            ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
            entrants=(
                MatchEntrant.python("A", "a", 0, specs[0]),
                MatchEntrant.python("B", "b", 91, specs[1]),
            ),
            max_ticks=ticks,
            replay_path=replay,
            trace_path=trace,
        )
    )
    session = ReplaySession()
    session.load(replay)
    playback = reconstruct_sensing_playback(replay, trace)
    return SensingCursor(playback, session), session, playback


def _view(cursor, callback, phase=ExchangePhase.OBSERVATION, tick=1):
    result = cursor.seek(PhasePosition(tick, callback, phase))
    assert isinstance(result, SensingView)
    return result


def _walk(cursor):
    views = [cursor.restart()]
    while not cursor.at_end:
        views.append(cursor.step_forward())
    return views


def test_ac5_no_contact_until_exact_single_shot_receipt(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91), ("move", 64)])
    assert not cursor.current_view.contacts
    assert not _view(cursor, 1).contacts
    action = _view(cursor, 1, ExchangePhase.ACTION)
    assert action.receipt_status == SampleStatus.PENDING
    assert action.events[-1].cost == 1
    assert not action.contacts and not action.samples
    receipt = _view(cursor, 2)
    assert receipt.receipt_status == SampleStatus.POSITIVE
    assert tuple(c.address for c in receipt.contacts) == (91,)
    assert receipt.samples[0].sampled_at.callback == 1
    assert receipt.samples[0].received_at.callback == 2
    later = _view(cursor, 3)
    assert later.receipt_status == SampleStatus.ABSENT
    assert len(later.samples) == 1


@pytest.mark.parametrize(
    "center,status",
    [(91, SampleStatus.POSITIVE), (0, SampleStatus.EMPTY), (256, SampleStatus.REFUSED)],
)
def test_positive_empty_refused_and_absent_remain_distinct(tmp_path, center, status):
    cursor, _, _ = _pair(tmp_path, [("sense", center)])
    assert _view(cursor, 1).receipt_status == SampleStatus.ABSENT
    assert _view(cursor, 2).receipt_status == status
    assert _view(cursor, 3).receipt_status == SampleStatus.ABSENT
    assert len(_view(cursor, 3).samples) == 1


def test_ac5_historical_age_and_no_live_identity_or_core_tracking(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("read", 0), ("sense", 91)], [("move", 8)])
    receipt = _view(cursor, 3)
    assert receipt.contacts[0].address == 91
    assert receipt.contacts[0].age_callbacks == 1
    later = _view(cursor, 9, tick=2)
    assert later.contacts[0].address == 91
    assert later.contacts[0].age_ticks == 1
    assert later.contacts[0].age_callbacks == 7
    assert not any(
        key in asdict(later.contacts[0]) for key in ("entrant_id", "process_id", "core_base")
    )
    assert "'B'" not in repr(asdict(later))
    omni = cursor.switch_view(None).current_view
    assert isinstance(omni, OmniscientView)
    assert ("B", "0", 99) in omni.anchors


def test_empty_scan_only_replaces_inside_window_and_retains_history(tmp_path):
    cursor, _, _ = _pair(
        tmp_path,
        [("sense", 91), ("read", 0), ("sense", 0), ("read", 0), ("sense", 91)],
        [("move", 64)],
    )
    outside = _view(cursor, 4)
    assert outside.samples[-1].status == SampleStatus.EMPTY
    assert outside.contacts[0].not_present_in_newer_sample is None
    inside = _view(cursor, 6)
    assert inside.contacts[0].address == 91
    assert inside.contacts[0].not_present_in_newer_sample.callback == 5
    assert inside.samples[0].addresses == (91,)


def test_refused_scan_and_silent_ticks_do_not_erase_contacts(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91), ("sense", 256)])
    view = _view(cursor, 3)
    assert view.samples[-1].status == SampleStatus.REFUSED
    assert view.contacts[0].not_present_in_newer_sample is None
    boundary = cursor.seek(PhasePosition(1, None, ExchangePhase.TICK_END))
    assert boundary.contacts[0].address == 91


def test_read_value_owner_only_enter_at_delivered_observation(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("read", 91), ("sense", 91)])
    assert not _view(cursor, 1, ExchangePhase.ACTION).reads
    delivered = _view(cursor, 2)
    assert delivered.reads[0].address == 91 and delivered.reads[0].owner == "B"
    assert not delivered.contacts
    assert _view(cursor, 3).contacts[0].address == 91
    assert not hasattr(_view(cursor, 3).contacts[0], "owner")


def test_read_history_is_not_refreshed_after_opponent_write(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("read", 91), ("sense", 91)], [("write", 91, 77)])
    before = _view(cursor, 2).reads[0]
    after = _view(cursor, 3).reads[0]
    assert before == after and before.value != 77


def test_delayed_receipt_across_ticks_and_no_terminal_delivery(tmp_path):
    script = [("read", 0)] * 7 + [("sense", 91)]
    cursor, _, _ = _pair(tmp_path / "late", script, ticks=2)
    assert not _view(cursor, 8, ExchangePhase.ACTION).contacts
    receipt = _view(cursor, 9, tick=2)
    assert receipt.samples[0].sampled_at.tick == 1
    assert receipt.samples[0].received_at.tick == 2
    short, _, _ = _pair(tmp_path / "short", script, ticks=1)
    assert not _walk(short)[-1].contacts
    assert not short.verification_report().teaching_complete
    assert (
        VerificationStatus.NOT_PROVEN in dict(short.verification_report().teaching_steps).values()
    )


def test_sibling_callback_does_not_deliver_pending_sample(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91), ("read", 0)], a_processes=2)
    assert not _view(cursor, 2).contacts
    receipt = _view(cursor, 3)
    assert receipt.samples[0].sampled_at.process_id == "0"
    assert receipt.samples[0].received_at.process_id == "0"


def test_receipt_survives_suppressed_tick_without_invented_callbacks(tmp_path):
    cursor, _, _ = _pair(
        tmp_path,
        [("read", 0)] * 7 + [("sense", 91)],
        [("read", 91)] * 8 + [("write", 0, 17)],
        ticks=3,
    )
    silent = cursor.seek(PhasePosition(2, None, ExchangePhase.TICK_END))
    assert not silent.samples
    assert not any(p.tick == 2 and p.callback is not None for p in cursor.positions)
    receipt = _view(cursor, 9, tick=3)
    assert receipt.samples[0].sampled_at.tick == 1
    assert receipt.samples[0].received_at.tick == 3


def test_ac7_seek_rewind_restart_switch_and_repeat_navigation(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91), ("move", 64), ("write", 91, 221)])
    baseline = _walk(cursor)
    assert _walk(cursor) == baseline
    for position, expected in reversed(list(zip(cursor.positions, baseline))):
        assert cursor.seek(position) == expected
    assert cursor.restart() == baseline[0]
    assert not cursor.current_view.contacts
    _view(cursor, 2)
    omni = cursor.switch_view(None)
    assert isinstance(omni.current_view, OmniscientView)
    back = omni.switch_view("A")
    assert back.current_view == baseline[3]
    back.restart()
    assert not back.current_view.contacts
    assert not back.current_view.reads


def test_ac7_every_tick_end_agrees_with_canonical_session(tmp_path):
    cursor, session, playback = _pair(tmp_path, [("sense", 91), ("move", 64)])
    for world in playback.sub_tick_states:
        if world.phase == ExchangePhase.TICK_END:
            cursor.seek(PhasePosition(world.tick, None, world.phase))
            state = session.current_state
            assert state.arena == world.memory and state.owners == world.owners
            assert {key: p.anchor for key, p in state.processes.items()} == world.anchors
    _view(cursor, 2)
    assert session.current_tick == 0


def test_ac5_identical_permitted_prefixes_have_identical_entire_payloads(tmp_path):
    script = [("read", 0), ("sense", 91), ("move", 64)]
    quiet, _, _ = _pair(tmp_path / "quiet", script)
    moving, _, _ = _pair(tmp_path / "moving", script, [("move", 8)])
    assert quiet.positions == moving.positions
    assert _walk(quiet) == _walk(moving)
    # All rows, labels, receipt times, ages, and pacing are included in equality.
    for position in quiet.positions:
        assert quiet.seek(position) == moving.seek(position)


def test_ac5_hidden_callback_counts_create_no_blank_phases_or_variable_pacing(tmp_path):
    # B overwrites its own core, eliminating itself at tick end, reducing future
    # hidden callbacks without changing A's permitted READ-only prefix.
    quiet, _, _ = _pair(tmp_path / "quiet", [("read", 0)] * 24)
    hidden, _, _ = _pair(
        tmp_path / "hidden", [("read", 0)] * 24, [("write", 91 + i, 0) for i in range(8)]
    )
    left = [v for v in _walk(quiet) if v.position.tick <= 1]
    right = [v for v in _walk(hidden) if v.position.tick <= 1]
    assert left == right
    assert len(left) == 18  # tick zero, eight own observations/actions, tick end
    for view in left:
        assert view.presentation_units == 1
        assert "global_decision_index" not in asdict(view)
    script = [("read", 0), ("read", 0), ("write", 91, 17)]
    one, _, model = _pair(tmp_path / "one", script)
    other, _, other_model = _pair(tmp_path / "other", script, [("move", 8)])
    assert sum(f.actor_id == "B" for f in model.facts) != sum(
        f.actor_id == "B" for f in other_model.facts
    )
    assert one.positions == other.positions
    assert _walk(one) == _walk(other)


def test_phase_controller_pauses_and_paces_only_permitted_steps(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91), ("move", 64)])
    controller = PhasePlaybackController(cursor, phase_interval=1)
    controller.play()
    controller.update(2)
    assert controller.current_view.position == PhasePosition(1, 1, ExchangePhase.ACTION)
    assert not controller.current_view.contacts
    controller.step_forward()
    assert not controller.playing and controller.current_view.contacts
    controller.update(100)
    assert controller.current_view.position == PhasePosition(1, 2, ExchangePhase.OBSERVATION)
    controller.restart()
    controller.set_speed(2)
    controller.play()
    controller.update(0.5)
    assert controller.current_view.position == PhasePosition(1, 1, ExchangePhase.OBSERVATION)
    controller.switch_view(None)
    controller.switch_view("A")
    assert not controller.current_view.contacts and not controller.playing


def test_projection_is_immutable_and_never_exposes_raw_world(tmp_path):
    cursor, _, playback = _pair(tmp_path, [("sense", 91)])
    view = _view(cursor, 2)
    with pytest.raises(FrozenInstanceError):
        view.contacts[0].address = 99
    forbidden = {
        "world_state",
        "binding",
        "memory",
        "owners",
        "facts",
        "decision_index",
        "teaching_steps",
        "teaching_complete",
    }
    assert not forbidden.intersection(asdict(view))
    for fact in playback.facts:
        fact.detail["secret"] = "B core 91"
        if fact.world_state:
            fact.world_state.anchors[("B", "0")] = 333
    assert cursor.current_view == view


def test_invalid_and_incomplete_evidence_fail_with_generic_message(tmp_path):
    cursor, session, playback = _pair(tmp_path, [("sense", 91)])
    with pytest.raises(SensingProjectionError, match="incomplete evidence"):
        SensingCursor(replace(playback, facts=playback.facts[:-1]), session)
    with pytest.raises(SensingProjectionError, match="incomplete evidence"):
        SensingCursor(
            replace(
                playback,
                facts=tuple(
                    f
                    for f in playback.facts
                    if not (f.actor_id == "A" and f.phase == ExchangePhase.ACTION)
                ),
            ),
            session,
        )
    with pytest.raises(SensingProjectionError) as exc:
        load_sensing_cursor(session, tmp_path / "replay.jsonl", tmp_path / "missing.jsonl")
    assert str(exc.value) == "Exchange playback unavailable: evidence could not be verified."
    assert "missing" not in str(exc.value) and "91" not in str(exc.value)
    assert cursor.restart().contacts == ()


def test_integrity_teaching_and_projection_statuses_are_separate(tmp_path):
    cursor, _, _ = _pair(tmp_path / "incomplete", [("sense", 91), ("move", 32)])
    report = cursor.verification_report()
    assert report.artifact_pair_consistent and report.exchange_reconstructed
    assert report.knowledge_projected and not report.teaching_complete
    assert VerificationStatus.NOT_VERIFIED in dict(report.teaching_steps).values()
    demo = tmp_path / "demo"
    run_sensing_demo(output_dir=demo, ticks=2)
    session = ReplaySession()
    session.load(demo / "replay.jsonl")
    complete = load_sensing_cursor(
        session,
        demo / "replay.jsonl",
        demo / "trace.jsonl",
        demo_path=demo,
        result_path=demo / "result.json",
    )
    assert complete.verification_report().teaching_complete
    assert "teaching_complete" not in asdict(complete.current_view)


def test_no_research_imports_private_reads_or_seed_operations(tmp_path, monkeypatch):
    cursor, session, _ = _pair(tmp_path, [("sense", 91)])
    original_import = builtins.__import__
    original_open = Path.open

    def guarded_import(name, *args, **kwargs):
        assert not name.startswith("tools.research")
        return original_import(name, *args, **kwargs)

    def guarded_open(path, *args, **kwargs):
        assert not any(part.startswith(("research_", ".pytest_e9_")) for part in path.parts)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(Path, "open", guarded_open)
    loaded = load_sensing_cursor(session, tmp_path / "replay.jsonl", tmp_path / "trace.jsonl")
    assert _walk(loaded) == _walk(cursor)
    with pytest.raises(SensingProjectionError):
        load_sensing_cursor(
            session,
            tmp_path / "research_private" / "replay.jsonl",
            tmp_path / "research_private" / "trace.jsonl",
        )
    import battle_client.sensing as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert not any(
        token in source
        for token in (
            "AuthorityLog",
            "consume_generation",
            "random.",
            "sensing_demo",
            "tools.research",
        )
    )
