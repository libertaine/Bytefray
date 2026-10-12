"""Independent hostile review of the M1-4 client projection boundary."""

from dataclasses import replace

import pytest
from battle_client.perspective import load_sensing_cursor
from battle_client.sensing import PhasePosition, SensingCursor, SensingProjectionError
from battle_client.session import ReplaySession
from battle_engine.replay import TickSnapshot, iter_replay, write_replay
from battle_engine.sensing_playback import ExchangePhase
from test_v6_alpha_sensing import _pair, _view, _walk


def test_late_older_sibling_receipt_cannot_replace_newer_sample(tmp_path):
    script = [("sense", 91), ("move", 64), ("sense", 91)]
    cursor, _, _ = _pair(tmp_path, script, [("write", 0, 77)], a_processes=2, ticks=3)
    views = _walk(cursor)
    final = views[-1]
    assert len(final.samples) == 2
    assert [s.sampled_at.callback for s in final.samples] == [3, 1]
    assert final.contacts[0].sampled_at.callback == 3
    for view in views:
        if len(view.samples) == 1:
            assert view.contacts[0].sampled_at.callback == 3


def test_existing_cursor_snapshot_survives_future_fact_mutation(tmp_path):
    cursor, _, playback = _pair(tmp_path, [("sense", 91)])
    expected = _view(cursor, 1)
    for fact in playback.facts:
        if fact.phase == ExchangePhase.OBSERVATION and fact.actor_id == "A":
            fact.world_state.anchors[("A", "0")] = 333
    assert _view(cursor, 1) == expected


def test_switch_view_preserves_verified_snapshot_after_input_mutation(tmp_path):
    cursor, _, playback = _pair(tmp_path, [("sense", 91)])
    expected = _view(cursor, 1)
    for fact in playback.facts:
        if fact.phase == ExchangePhase.OBSERVATION and fact.actor_id == "A":
            fact.world_state.anchors[("A", "0")] = 333
    switched = cursor.switch_view(None).switch_view("A")
    assert switched.current_view == expected


def test_factory_rejects_session_with_unbound_own_reach(tmp_path):
    _pair(tmp_path, [("sense", 91)])
    records = tuple(
        replace(
            record,
            processes=tuple(
                replace(process, reach=1) if process.entrant_id == "A" else process
                for process in record.processes
            ),
        )
        if isinstance(record, TickSnapshot)
        else record
        for record in iter_replay(tmp_path / "replay.jsonl")
    )
    alternate = tmp_path / "unbound.jsonl"
    write_replay(alternate, records)
    session = ReplaySession()
    session.load(alternate)
    with pytest.raises(SensingProjectionError):
        load_sensing_cursor(session, tmp_path / "replay.jsonl", tmp_path / "trace.jsonl")


def test_silent_boundary_does_not_reset_or_refresh_history(tmp_path):
    cursor, _, _ = _pair(tmp_path, [("sense", 91)], [("write", 0, 77)], ticks=3)
    delivered = _view(cursor, 2)
    at_end = cursor.seek(PhasePosition(1, None, ExchangePhase.TICK_END))
    assert at_end.samples == delivered.samples
    assert at_end.contacts[0].sampled_at == delivered.contacts[0].sampled_at
    assert at_end.contacts[0].received_at == delivered.contacts[0].received_at


def test_preverified_model_rejects_replay_changed_after_reconstruction(tmp_path):
    _, _, playback = _pair(tmp_path, [("sense", 91)])
    replay = tmp_path / "replay.jsonl"
    records = tuple(
        replace(record, processes=tuple(
            replace(process, reach=1) if process.entrant_id == "A" else process
            for process in record.processes
        )) if isinstance(record, TickSnapshot) else record
        for record in iter_replay(replay)
    )
    write_replay(replay, records)
    session = ReplaySession()
    session.load(replay)
    with pytest.raises(SensingProjectionError):
        SensingCursor(playback, session)


def test_failed_projection_build_restores_loaded_session_exactly(tmp_path):
    _, session, playback = _pair(tmp_path, [("sense", 91)])
    expected = session.seek(2)
    facts = tuple(
        replace(fact, world_state=None)
        if fact.actor_id == "A" and fact.phase == ExchangePhase.OBSERVATION
        else fact
        for fact in playback.facts
    )
    with pytest.raises(SensingProjectionError, match="incomplete evidence"):
        SensingCursor(replace(playback, facts=facts), session)
    assert session.current_state == expected


def test_direct_constructor_rejects_private_path_before_read(tmp_path, monkeypatch):
    _, session, playback = _pair(tmp_path, [("sense", 91)])
    expected = session.seek(2)
    private = tmp_path / "research_private" / "missing.jsonl"
    binding = replace(playback.binding, replay_path=private)
    reads = []

    def forbidden_read(path):
        reads.append(path)
        raise AssertionError(f"Unexpected read of {path}")

    monkeypatch.setattr(type(private), "read_bytes", forbidden_read)
    with pytest.raises(SensingProjectionError) as exc:
        SensingCursor(replace(playback, binding=binding), session)
    assert str(exc.value) == "Exchange playback unavailable: evidence could not be verified."
    assert reads == []
    assert session.current_state == expected
