from __future__ import annotations

import pytest


@pytest.mark.gui
def test_agent_designer_window_starts_and_closes(monkeypatch, tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QEvent, QTimer
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    application = QApplication.instance() or QApplication([])
    window = AgentDesigner()
    window.show()
    assert window.isVisible()
    QTimer.singleShot(50, window.close)
    safety_quit = QTimer()
    safety_quit.setSingleShot(True)
    safety_quit.timeout.connect(application.quit)
    safety_quit.start(60)
    try:
        assert application.exec() == 0
    finally:
        # Closing the last window posts a Quit of its own, which the explicit
        # quit can overtake. Left queued, it would be delivered in whichever
        # later test next pumps events, and every QEventLoop.exec() after that
        # returns at once.
        safety_quit.stop()
        application.removePostedEvents(application, QEvent.Type.Quit)
    assert not window.isVisible()
