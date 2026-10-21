"""Designer reads its child commands' output as UTF-8 and asks them to write it.

An installed 5.1 Alpha keeps its data under the user's profile folder, so the
paths a child command prints (``agents test``'s ``replay:`` line, which
Designer parses to enable Open Replay) can contain characters the Windows ANSI
code page cannot encode. Designer sets PYTHONIOENCODING=utf-8 for every child
(battle_engine.command applies it in frozen builds too) and decodes each stream
incrementally, so no character -- not even one split across two reads -- is lost.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _designer(monkeypatch, tmp_path: Path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    return AgentDesigner()


@pytest.mark.gui
def test_every_child_command_is_asked_for_utf8_output(monkeypatch, tmp_path):
    from PySide6.QtCore import QProcessEnvironment

    designer = _designer(monkeypatch, tmp_path)
    try:
        env = QProcessEnvironment.systemEnvironment()
        env.remove("PYTHONIOENCODING")
        proc = designer._start_process(["no-such-program"], env, tmp_path, label="Probe")
        assert proc.processEnvironment().value("PYTHONIOENCODING") == "utf-8"
    finally:
        designer._dispose_process()
        designer.deleteLater()


class _ChunkedProcess:
    """Hands out pre-split stdout chunks, one per readyRead, like a pipe may."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    def readAllStandardOutput(self) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""

    def readAllStandardError(self) -> bytes:
        return b""


@pytest.mark.gui
def test_a_character_split_across_reads_reaches_the_parser_intact(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    try:
        line = "replay: C:\\Users\\Ωmega\\AppData\\Local\\Bytefray 5.1 Alpha\\runs\\replay.jsonl\n".encode()
        split = line.index("Ω".encode()) + 1  # between the two bytes of Ω
        proc = _ChunkedProcess([line[:split], line[split:]])
        designer._proc = proc
        designer._active_workflow = "validate"
        designer._validate_stdout = ""
        designer._validate_stderr = ""
        designer._pipe_proc_output(proc)
        designer._pipe_proc_output(proc)
        assert designer._validate_stdout == line.decode()
    finally:
        designer._proc = None
        designer.deleteLater()
