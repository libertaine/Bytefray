"""Unit coverage for the standalone Replay Viewer's empty-state directory
browser (Phase 3, UX-20..UX-23).

``ReplayPicker``'s navigation logic (list/select/enter/up) is pure Python
with no Pygame display dependency, so it is covered here without the
``gui`` marker; only the thin event-loop shell in ``run_empty_state`` needs
a real (or dummy) display, covered separately by
``test_replay_viewer_empty_state.py``.
"""

from __future__ import annotations

import os

from battle_client.renderers.replay_picker import ReplayPicker, _list_directory


def _make_tree(tmp_path):
    (tmp_path / "sub_a").mkdir()
    (tmp_path / "sub_b").mkdir()
    (tmp_path / "replay_b.jsonl").write_text("{}")
    (tmp_path / "replay_a.jsonl").write_text("{}")
    (tmp_path / "notes.txt").write_text("not a replay")
    return tmp_path


def test_list_directory_lists_subdirs_first_then_jsonl_only_alphabetically(tmp_path):
    _make_tree(tmp_path)

    entries = _list_directory(tmp_path)

    assert [e.path.name for e in entries] == ["sub_a", "sub_b", "replay_a.jsonl", "replay_b.jsonl"]
    assert [e.is_dir for e in entries] == [True, True, False, False]


def test_list_directory_ignores_non_jsonl_files(tmp_path):
    _make_tree(tmp_path)

    entries = _list_directory(tmp_path)

    assert "notes.txt" not in [e.path.name for e in entries]


def test_list_directory_on_unreadable_or_missing_path_returns_empty(tmp_path):
    missing = tmp_path / "does-not-exist"

    assert _list_directory(missing) == []


def test_picker_move_clamps_to_entry_bounds(tmp_path):
    _make_tree(tmp_path)
    picker = ReplayPicker(tmp_path)

    picker.move(-5)
    assert picker.selected == 0

    picker.move(100)
    assert picker.selected == len(picker.entries) - 1


def test_picker_move_on_empty_directory_is_a_safe_no_op(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    picker = ReplayPicker(empty)

    picker.move(1)  # must not raise
    assert picker.selected == 0


def test_picker_activate_on_directory_descends_and_returns_none(tmp_path):
    _make_tree(tmp_path)
    picker = ReplayPicker(tmp_path)

    result = picker.activate(0)  # sub_a, first entry (dirs sort first)

    assert result is None
    assert picker.directory == tmp_path / "sub_a"
    assert picker.entries == []  # sub_a is empty


def test_picker_activate_on_file_returns_its_path(tmp_path):
    _make_tree(tmp_path)
    picker = ReplayPicker(tmp_path)
    file_index = next(i for i, e in enumerate(picker.entries) if not e.is_dir)

    result = picker.activate(file_index)

    assert result == tmp_path / "replay_a.jsonl"
    # Activating a file does not change the browsed directory.
    assert picker.directory == tmp_path


def test_picker_go_up_moves_to_parent_directory(tmp_path):
    _make_tree(tmp_path)
    picker = ReplayPicker(tmp_path / "sub_a")

    moved = picker.go_up()

    assert moved is True
    assert picker.directory == tmp_path


def test_picker_go_up_at_filesystem_root_switches_to_drive_or_root_list(tmp_path):
    root = tmp_path.anchor  # e.g. "D:\\" on Windows, "/" elsewhere
    picker = ReplayPicker(type(tmp_path)(root))

    moved = picker.go_up()

    assert moved is True
    assert picker.at_roots is True
    assert len(picker.entries) >= 1
    assert all(entry.is_dir for entry in picker.entries)


def test_picker_activating_a_root_entry_navigates_into_that_drive(tmp_path):
    root = tmp_path.anchor
    picker = ReplayPicker(type(tmp_path)(root))
    picker.go_up()  # now showing the root/drive list
    # Find the entry corresponding to this same root among the listed roots.
    index = next(
        i for i, e in enumerate(picker.entries) if os.path.normcase(str(e.path)) == os.path.normcase(root)
    )

    result = picker.activate(index)

    assert result is None
    assert picker.at_roots is False
    assert os.path.normcase(str(picker.directory)) == os.path.normcase(root)


def test_set_directory_resets_selection_and_scroll(tmp_path):
    _make_tree(tmp_path)
    picker = ReplayPicker(tmp_path)
    picker.selected = 2
    picker.scroll = 5

    picker.set_directory(tmp_path / "sub_a")

    assert picker.selected == 0
    assert picker.scroll == 0
    assert picker.at_roots is False
