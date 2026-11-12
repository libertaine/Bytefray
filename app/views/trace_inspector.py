"""Trace Inspector dialog: read-only, tick-indexed view of a development trace.

Agent Lab v0.5 (``docs/specs/agent_lab.md`` §11). Deliberately modest --
no source editor, no general debugger, just tick/agent navigation over an
already-written ``bytefray.agent_trace`` file of schema 1 or schema 2
(:mod:`battle_engine.agent_trace`; schema-2 decision blocks also name the
entrant process and its per-tick callback number). Parsing and formatting are entirely
delegated to that Qt-free module (reusing the same formatting functions
:mod:`battle_engine.agent_inspect` uses for the CLI, so the GUI and CLI
never drift into two descriptions of the same record) -- this module only
wires widgets to already-parsed data. No agent code is ever executed by
opening this dialog: it only reads a JSONL file already on disk, so unlike
Validate/Test it needs no QProcess and can run directly on the GUI thread.
"""

from __future__ import annotations

from pathlib import Path

from battle_engine.agent_inspect import (
    DecisionView,
    decision_views,
    format_reset,
    trace_tick_range,
)
from battle_engine.agent_trace import (
    AnyTraceDocument,
    ResetRecord,
    TraceDocumentV2,
    TraceFormatError,
    read_any_trace,
)
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class TraceInspectorDialog(QDialog):
    """Modal, read-only viewer over one trace file's decisions."""

    def __init__(self, trace_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Inspect Trace — {trace_path.name}")
        self.resize(640, 480)

        self._document: AnyTraceDocument | None = None
        self._views: tuple[DecisionView, ...] = ()
        self._error: str | None = None
        try:
            self._document = read_any_trace(trace_path)
            self._views = decision_views(self._document)
        except TraceFormatError as exc:
            self._error = str(exc)

        layout = QVBoxLayout(self)

        if self._document is None:
            layout.addWidget(QLabel(f"Could not read trace: {self._error}"))
            return

        header_text = (
            f"seed={self._document.header.match_seed}  "
            f"supervised={self._document.header.supervised}  "
            f"agents={', '.join(f'{slot}={name}' for slot, name in sorted(self._document.header.agents.items()))}"
        )
        if isinstance(self._document, TraceDocumentV2):
            processes = ", ".join(
                f"{d.agent_id}/{d.process_id}" for d in self._document.declarations
            )
            header_text = f"schema=v2  {header_text}  processes={processes or 'none'}"
        header_label = QLabel(header_text)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)

        controls = QHBoxLayout()
        self.tickLabel = QLabel("Tick")
        self.tickSpin = QSpinBox()
        self.tickLabel.setBuddy(self.tickSpin)
        tick_range = trace_tick_range(self._views)
        low, high = tick_range if tick_range is not None else (0, 0)
        self.tickSpin.setRange(low, high)
        self.tickSpin.setValue(low)
        controls.addWidget(self.tickLabel)
        controls.addWidget(self.tickSpin)

        self.agentLabel = QLabel("Agent")
        self.agentCombo = QComboBox()
        self.agentLabel.setBuddy(self.agentCombo)
        for slot, name in sorted(self._document.header.agents.items()):
            self.agentCombo.addItem(f"{slot} ({name})", slot)
        controls.addWidget(self.agentLabel)
        controls.addWidget(self.agentCombo, 1)

        self.failuresOnlyCheck = QCheckBox("Failures only")
        controls.addWidget(self.failuresOnlyCheck)
        layout.addLayout(controls)

        nav = QHBoxLayout()
        self.prevButton = QPushButton("◀ Prev")
        self.nextButton = QPushButton("Next ▶")
        nav.addWidget(self.prevButton)
        nav.addWidget(self.nextButton)
        nav.addStretch(1)
        layout.addLayout(nav)

        self.detailText = QPlainTextEdit()
        self.detailText.setReadOnly(True)
        self.detailText.setAccessibleName("Trace decision details")
        self.detailText.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        layout.addWidget(self.detailText, 1)

        self.tickSpin.valueChanged.connect(self._refresh)
        self.agentCombo.currentIndexChanged.connect(self._refresh)
        self.failuresOnlyCheck.toggled.connect(self._refresh)
        self.prevButton.clicked.connect(self._go_previous)
        self.nextButton.clicked.connect(self._go_next)

        self._refresh()

    # ---- Internal ----
    def _current_agent_slot(self) -> str | None:
        return self.agentCombo.currentData()

    def _matching_decisions(self) -> tuple[DecisionView, ...]:
        assert self._document is not None
        agent = self._current_agent_slot()
        views = tuple(v for v in self._views if v.agent_id == agent) if agent else self._views
        if self.failuresOnlyCheck.isChecked():
            views = tuple(v for v in views if v.failure)
        return views

    def _refresh(self) -> None:
        assert self._document is not None
        tick = self.tickSpin.value()
        decisions = [d for d in self._matching_decisions() if d.tick == tick]
        resets: tuple[ResetRecord, ...] = ()
        if self._current_agent_slot():
            resets = tuple(
                r for r in self._document.resets if r.agent_id == self._current_agent_slot()
            )
        if not decisions and not resets:
            self.detailText.setPlainText(f"No decisions recorded at tick {tick}.")
            return
        blocks = [format_reset(self._document, r) for r in resets] + [d.format() for d in decisions]
        self.detailText.setPlainText("\n\n".join(blocks))

    def _go_previous(self) -> None:
        ticks = sorted({d.tick for d in self._matching_decisions() if d.tick < self.tickSpin.value()})
        if ticks:
            self.tickSpin.setValue(ticks[-1])

    def _go_next(self) -> None:
        ticks = sorted({d.tick for d in self._matching_decisions() if d.tick > self.tickSpin.value()})
        if ticks:
            self.tickSpin.setValue(ticks[0])


__all__ = ["TraceInspectorDialog"]
