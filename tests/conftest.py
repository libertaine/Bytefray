"""Isolation shared by the display-backed Designer tests in this directory."""

from __future__ import annotations

import gc
import sys
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _no_installed_spectator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never launch a Bytefray Spectator that happens to be installed on this machine.

    Designer prefers Spectator for supported V6 matches when one is found
    (app/services/spectator_viewer.py). Tests that exercise that path configure
    BYTEFRAY_SPECTATOR themselves; every other test sees it turned off.
    """
    monkeypatch.setenv("BYTEFRAY_SPECTATOR", "off")


def finalize_qt_objects() -> None:
    """Destroy what a test left behind, on the GUI thread, as the application would.

    Tests never run the application's event loop, so ``deleteLater`` (including
    every ``WA_DeleteOnClose`` window) is never processed by ``processEvents``.
    And an ``AgentDesigner`` is kept alive by its own reference cycles after a
    test drops it. Left alone, both survive into later tests until Python's
    cyclic collector frees them -- on whichever thread trips its threshold.
    A Replay History worker ``QThread`` running Python can be that thread, and
    finalizing live widgets there destroys them off the GUI thread: the
    segfault (and occasional hang) of issue #7. Here the deferred deletions
    run and the collector runs on the GUI thread, while no worker is active.
    """

    core = sys.modules.get("PySide6.QtCore")
    if core is not None and core.QCoreApplication.instance() is not None:
        core.QCoreApplication.sendPostedEvents(None, core.QEvent.Type.DeferredDelete)
    gc.collect()


@pytest.fixture(autouse=True)
def _finalize_qt_objects_on_the_gui_thread() -> Iterator[None]:
    """After every test, finalize its Qt objects on the GUI thread (issue #7)."""

    yield
    finalize_qt_objects()
