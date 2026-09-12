"""WAL snapshot, read-only ownership and recovery qualification for Phase 7E."""
from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from battle_engine.replay_history import HistoryQuery, ReplayHistoryService
from battle_engine.replay_history.service import HistoryRefreshCancelled

from engine.tests.test_replay_history import _write_run


def _open(root: Path, *, read_only: bool = False) -> ReplayHistoryService:
    return ReplayHistoryService.open(data_root=root, read_only=read_only)


def test_read_only_open_does_not_create_missing_cache(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        _open(tmp_path, read_only=True)
    assert not (tmp_path / "cache").exists()


@pytest.mark.parametrize("damage", ["bytes", "version", "metadata", "root"])
def test_reader_never_recovers_or_relabels_invalid_cache(tmp_path, damage):
    with _open(tmp_path) as writer:
        cache = Path(writer.cache_report.path)
        if damage == "version":
            writer._index.connection.execute("PRAGMA user_version = 987")
        elif damage == "metadata":
            writer._index.connection.execute("DELETE FROM cache_metadata")
        elif damage == "root":
            writer._index.set_metadata("root_identity", "different-root")
    if damage == "bytes":
        cache.write_bytes(b"not sqlite")
    before = cache.read_bytes()
    with pytest.raises((sqlite3.DatabaseError, ValueError)):
        _open(tmp_path, read_only=True)
    assert cache.read_bytes() == before


def test_read_only_service_rejects_maintenance_and_sql_writes(tmp_path):
    _write_run(tmp_path / "runs", "one")
    with _open(tmp_path) as writer:
        writer.refresh()
        with _open(tmp_path, read_only=True) as reader:
            assert reader._index.connection is not writer._index.connection
            assert reader._index.connection.execute("PRAGMA query_only").fetchone() == (1,)
            for operation in (reader.refresh, reader.rebuild, reader.reconcile):
                with pytest.raises(PermissionError, match="read-only"):
                    operation()
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                reader._index.connection.execute("DELETE FROM occurrence")
            assert reader.count() == 1


@pytest.mark.parametrize("outcome", ["commit", "rollback", "cancel"])
@pytest.mark.parametrize("maintenance", ["reconcile", "rebuild"])
def test_real_maintenance_keeps_concurrent_reader_usable(tmp_path, outcome, maintenance):
    _write_run(tmp_path / "runs", "old", seed=1)
    entered, release = threading.Event(), threading.Event()
    with ThreadPoolExecutor(1) as writes, ThreadPoolExecutor(1) as reads:
        writer = writes.submit(_open, tmp_path).result()
        writes.submit(writer.refresh).result()
        reader = reads.submit(_open, tmp_path, read_only=True).result()
        try:
            writer_owner = writes.submit(lambda: (threading.get_ident(), id(writer._index.connection))).result()
            reader_owner = reads.submit(lambda: (threading.get_ident(), id(reader._index.connection))).result()
            assert writer_owner[0] != reader_owner[0] != threading.get_ident()
            assert writer_owner[1] != reader_owner[1]
            assert writes.submit(lambda: writer._index.connection.execute("PRAGMA journal_mode").fetchone()).result() == ("wal",)
            _write_run(tmp_path / "runs", "new", seed=2)
            original = writer._finish_generation

            def finish(generation):
                entered.set()
                assert release.wait(5)
                if outcome == "rollback":
                    raise RuntimeError("controlled writer failure")
                if outcome == "cancel":
                    raise HistoryRefreshCancelled()
                original(generation)

            writer._finish_generation = finish
            refresh = writes.submit(getattr(writer, maintenance))
            assert entered.wait(5)

            def query():
                page, count = reader.fetch_page_with_count()
                assert count == len(page.rows) == 1
                assert reader.fetch_detail(page.rows[0].location_id).occurrence.seed == 1
                assert reader.count(HistoryQuery(seed=2)) == 0
                assert reader.ruleset_facets()
                return reader.resolve_replay(page.rows[0].location_id)

            # A reader queued behind maintenance would hit this deadline.
            reads.submit(query).result(timeout=2)
            assert not refresh.done()
            release.set()
            if outcome == "rollback":
                with pytest.raises(RuntimeError, match="controlled"):
                    refresh.result(timeout=5)
            else:
                assert refresh.result(timeout=5).committed == (outcome == "commit")
            assert reads.submit(reader.count).result() == (2 if outcome == "commit" else 1)
            writer._finish_generation = original
            assert writes.submit(writer.refresh).result().committed
            assert reads.submit(reader.count).result() == 2
        finally:
            release.set()
            reads.submit(reader.close).result()
            writes.submit(writer.close).result()


def test_detail_parent_and_entrants_share_one_snapshot(tmp_path):
    _write_run(tmp_path / "runs", "one", seed=1)
    with ThreadPoolExecutor(1) as writes:
        writer = writes.submit(_open, tmp_path).result()
        writes.submit(writer.refresh).result()
        try:
            with _open(tmp_path, read_only=True) as reader:
                location = reader.fetch_page().rows[0].location_id
                old = reader.fetch_detail(location)
                _write_run(tmp_path / "runs", "one", seed=2,
                           entrants=(("A", "Changed A"), ("B", "Changed B")))
                committed = False

                def commit_between_selects(statement):
                    nonlocal committed
                    if "FROM occurrence_entrant" in statement and not committed:
                        committed = True
                        writes.submit(writer.reconcile).result(timeout=5)

                reader._index.connection.set_trace_callback(commit_between_selects)
                during = reader.fetch_detail(location)
                reader._index.connection.set_trace_callback(None)
                assert committed
                assert during == old
                assert reader.fetch_detail(location).occurrence.seed == 2
        finally:
            writes.submit(writer.close).result()


def test_refresh_after_first_build_reconciles_instead_of_rebuilding(tmp_path):
    _write_run(tmp_path / "runs", "one")
    with _open(tmp_path) as service:
        assert service.refresh().committed
        summary = service.refresh()
        assert summary.unchanged == 1
        assert summary.generation == 2


@pytest.mark.parametrize(
    ("entrants", "winner", "name", "display"),
    [
        ((("A", "Alpha"), ("B", "Beta")), "B", "Beta", "Beta (B)"),
        ((("A", "Same"), ("B", "Same")), "A", "Same", "Same (A)"),
        ((("A", "Alpha"), ("A", "Beta")), "A", None, "A"),
        ((("A", "Alpha"),), "Z", None, "Z"),
        ((("A", "Alpha"),), "tie", None, "Tie"),
    ],
)
def test_winner_projection_keeps_recorded_identity_and_rejects_ambiguous_mapping(
    tmp_path, entrants, winner, name, display
):
    from app.services.replay_history_presentation import format_result

    _write_run(tmp_path / "runs", "one", entrants=entrants, winner=winner)
    with _open(tmp_path) as writer:
        writer.refresh()
        with _open(tmp_path, read_only=True) as reader:
            row = reader.fetch_page().rows[0]
            assert row.winner == winner
            assert row.winner_display_name == name
            assert format_result(row) == display


def test_page_and_count_share_a_snapshot_across_writer_commit(tmp_path):
    _write_run(tmp_path / "runs", "old")
    with ThreadPoolExecutor(1) as writes:
        writer = writes.submit(_open, tmp_path).result()
        writes.submit(writer.refresh).result()
        try:
            with _open(tmp_path, read_only=True) as reader:
                _write_run(tmp_path / "runs", "new")
                committed = False

                def commit_before_count(statement):
                    nonlocal committed
                    if statement == "SELECT COUNT(*) FROM occurrence" and not committed:
                        committed = True
                        writes.submit(writer.reconcile).result(timeout=5)

                reader._index.connection.set_trace_callback(commit_before_count)
                page, count = reader.fetch_page_with_count()
                reader._index.connection.set_trace_callback(None)
                assert committed
                assert len(page.rows) == count == 1
                assert reader.count() == 2
        finally:
            writes.submit(writer.close).result()
