"""Designer objects a test leaves behind are destroyed on the GUI thread (issue #7).

An ``AgentDesigner`` stays alive through its own reference cycles after a test
drops it, and tests never run the event loop that would process its closed
Replay History window's ``deleteLater``. Python's cyclic collector used to
free such leftovers later, on whichever thread tripped its threshold; when
that was a Replay History worker ``QThread`` it destroyed live widgets off the
GUI thread and the run segfaulted (occasionally hung). ``tests/conftest.py``
now finalizes every test's Qt objects on the GUI thread at teardown.

The two tests below run in order, with automatic collection disabled for the
module so that only that teardown can free the first test's designer.
"""

from __future__ import annotations

import gc
import threading
import time
import weakref
from collections.abc import Iterator

import pytest

pytestmark = pytest.mark.gui

_LEFT_BEHIND: list[weakref.ref] = []
_DESTROYED_ON: list[int] = []
_GUI_THREAD: list[int] = []


@pytest.fixture(scope="module")
def _no_automatic_collection() -> Iterator[None]:
    enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if enabled:
            gc.enable()


def test_a_closed_designer_survives_only_through_reference_cycles(
    _no_automatic_collection, monkeypatch, tmp_path
) -> None:
    from PySide6.QtCore import Qt
    from test_v5_replay_history_browser import _make_app

    app = _make_app()
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    from app.agent_designer import AgentDesigner

    designer = AgentDesigner()
    designer._on_replay_history()
    window = designer._replay_history
    deadline = time.perf_counter() + 15
    while not (window._reader_ready and not window._refreshing):
        assert time.perf_counter() < deadline, "Replay History never became ready"
        app.processEvents()
        time.sleep(0.002)
    window.shutdownWorker()
    designer.close()
    _GUI_THREAD.append(threading.get_ident())
    designer.destroyed.connect(
        lambda *_: _DESTROYED_ON.append(threading.get_ident()), Qt.DirectConnection
    )
    _LEFT_BEHIND.append(weakref.ref(designer))
    del designer, window
    # Nothing references it any more, yet it is still alive: only the cyclic
    # collector can free it, which is exactly the hazard.
    assert _LEFT_BEHIND[0]() is not None


def test_the_previous_tests_designer_was_destroyed_on_the_gui_thread(_no_automatic_collection) -> None:
    if not _LEFT_BEHIND:
        pytest.skip("runs after test_a_closed_designer_survives_only_through_reference_cycles")
    assert _LEFT_BEHIND[0]() is None, "a closed Designer survived into the next test"
    assert _DESTROYED_ON == _GUI_THREAD, "the Designer was destroyed off the GUI thread"
