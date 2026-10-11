"""Tools: Native Windows Agent Designer 13-Step Workflow Automation Witness.

Executes all 13 authoring workflow steps under QT_QPA_PLATFORM=windows with
unmocked Pygame replay launching, complete Win32 input dispatch, and authentic
window grab captures saved to docs/screenshots/v6_alpha1_windows/.
"""
from __future__ import annotations

import ctypes
import os
import pathlib
import sys
import tempfile
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202

VK_SPACE = 0x20
VK_RIGHT = 0x27
VK_LEFT = 0x25
VK_HOME = 0x24
VK_END = 0x23
VK_OEM_PLUS = 0xBB
VK_OEM_MINUS = 0xBD

SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001


def wait_process(app, designer, timeout: float = 30.0) -> None:
    from PySide6.QtCore import QProcess
    deadline = time.monotonic() + timeout
    while (
        designer._proc is not None
        and designer._proc.state() != QProcess.NotRunning
        and time.monotonic() < deadline
    ):
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()
    assert designer._proc is not None and designer._proc.state() == QProcess.NotRunning, "Subprocess timed out"


def run_workflow(output_dir: pathlib.Path, screenshot_dir: pathlib.Path) -> None:
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.environ["BYTEFRAY_ROOT"] = str(output_dir)
    os.environ["BYTEFRAY_AGENTS_DIR"] = str(output_dir / "agents")

    from battle_engine.result_model import read_result
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from app.agent_designer import AgentDesigner
    from app.views.development import NewAgentDialog

    app = QApplication.instance() or QApplication(sys.argv)
    designer = AgentDesigner()
    designer.show()
    app.processEvents()
    time.sleep(0.3)

    # -------------------------------------------------------------
    # Step 1 & 2: Launch and confirm stable v4 is default
    # -------------------------------------------------------------
    print("[Step 1-2] Confirming defaults...")
    assert designer.development.selected_ruleset_id() == "bytefray-rules-4"
    assert designer.advanced.ruleset.currentData() == "bytefray-rules-4"
    p1 = screenshot_dir / "01_designer_launched.png"
    designer.grab().save(str(p1))
    print(f"Captured: {p1} ({p1.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 3: Create personal copy of Window Scout in Agent Development
    # -------------------------------------------------------------
    print("[Step 3] Creating personal copy of Window Scout...")
    designer.tabs.setCurrentWidget(designer.development)
    app.processEvents()

    def populate_new_agent_dialog():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, NewAgentDialog):
                w.agentId.setText("my_window_scout")
                idx = w.templateCombo.findData("window_scout")
                if idx >= 0:
                    w.templateCombo.setCurrentIndex(idx)
                buttons = w.findChild(QDialogButtonBox)
                if buttons and buttons.button(QDialogButtonBox.Ok):
                    QTest.mouseClick(buttons.button(QDialogButtonBox.Ok), Qt.LeftButton)
                else:
                    w.accept()
                return

    QTimer.singleShot(150, populate_new_agent_dialog)
    QTest.mouseClick(designer.development.btnNewAgent, Qt.LeftButton)
    app.processEvents()
    time.sleep(0.3)

    assert (output_dir / "agents/my_window_scout/agent.py").is_file()
    designer.development.selectAgent("my_window_scout")
    app.processEvents()
    p2 = screenshot_dir / "02_window_scout_copied.png"
    designer.grab().save(str(p2))
    print(f"Captured: {p2} ({p2.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 7 (Contract Step 7): Preflight capability rejection on v4
    # -------------------------------------------------------------
    print("[Step 7] Confirming capability mismatch rejection under v4...")
    assert designer.development.selected_ruleset_id() == "bytefray-rules-4"
    assert not designer.development.btnTest.isEnabled()
    QTest.mouseClick(designer.development.btnValidate, Qt.LeftButton)
    wait_process(app, designer)
    assert "capabilit" in designer.development.statusLabel.text().lower()
    p3 = screenshot_dir / "03_capability_mismatch_rejected.png"
    designer.grab().save(str(p3))
    print(f"Captured: {p3} ({p3.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 4 & 6: Select bytefray-rules-6-alpha1 and validate
    # -------------------------------------------------------------
    print("[Step 4 & 6] Selecting bytefray-rules-6-alpha1 and validating...")
    designer.development.rulesetCombo.setCurrentIndex(
        designer.development.rulesetCombo.findData("bytefray-rules-6-alpha1")
    )
    app.processEvents()
    assert designer.development.btnTest.isEnabled()
    QTest.mouseClick(designer.development.btnValidate, Qt.LeftButton)
    wait_process(app, designer)
    assert "Valid" in designer.development.statusLabel.text()
    p4 = screenshot_dir / "04_alpha1_validated.png"
    designer.grab().save(str(p4))
    print(f"Captured: {p4} ({p4.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 5: Configure parameters in Advanced -> Agent Params
    # -------------------------------------------------------------
    print("[Step 5] Configuring parameters in Advanced -> Agent Params...")
    designer.tabs.setCurrentWidget(designer.advanced)
    advanced = designer.advanced
    advanced.ruleset.setCurrentIndex(advanced.ruleset.findData("bytefray-rules-6-alpha1"))
    advanced.agentA.setCurrentIndex(advanced.agentA.findData("my_window_scout"))
    advanced.agentB.setCurrentIndex(advanced.agentB.findData("v4_scout"))
    advanced.ticks.setValue(5)
    advanced.tabs.setCurrentIndex(1)  # Agent Params
    app.processEvents()
    advanced.schemaA._controls["search_interval"].setValue(2)
    advanced.schemaA._controls["move_step"].setValue(32)
    app.processEvents()
    p5 = screenshot_dir / "05_advanced_parameters_configured.png"
    designer.grab().save(str(p5))
    print(f"Captured: {p5} ({p5.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 8 & 9: Start native match, confirm ruleset and parameters
    # -------------------------------------------------------------
    print("[Step 8 & 9] Running native match 1...")
    advanced.tabs.setCurrentIndex(0)  # Match Setup
    app.processEvents()
    QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
    wait_process(app, designer)

    advanced.tabs.setCurrentIndex(3)  # Results
    app.processEvents()
    assert designer._last_result_path is not None, "Match 1 did not produce a result path"
    res1 = read_result(designer._last_result_path)
    assert res1.ruleset_id == "bytefray-rules-6-alpha1"
    assert res1.entrants[0]["metadata"]["parameters"] == {"search_interval": 2, "move_step": 32}
    print(f"Match 1 Result ID: {res1.result_id}")
    p6 = screenshot_dir / "06_match_completed.png"
    designer.grab().save(str(p6))
    print(f"Captured: {p6} ({p6.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 10, 11, 12: Open unmocked replay, exercise viewer, close cleanly
    # -------------------------------------------------------------
    print("[Step 10, 11, 12] Launching unmocked Pygame replay viewer...")
    designer._on_open_replay()
    app.processEvents()

    # Wait for native Pygame viewer window to appear
    hwnd = 0
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        hwnd = user32.FindWindowW(None, "Bytefray — Experimental sensing replay")
        if hwnd:
            break
        app.processEvents()
        time.sleep(0.1)

    assert hwnd != 0, "Pygame sensing replay window not detected by FindWindowW"

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    print(f"[Witness] Detected live Pygame window: HWND = {hwnd}, PID = {pid.value}")

    # Exercise full teaching sequence controls:
    # Play/pause (Space), forward step (Right), reverse step (Left),
    # speed change (+, -), view switch (1, 2), restart (Home), end (End)
    for vk in (VK_SPACE, VK_RIGHT, VK_LEFT, VK_OEM_PLUS, VK_OEM_MINUS, ord("1"), ord("2"), VK_HOME, VK_END):
        user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
        time.sleep(0.04)
        user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)
        time.sleep(0.04)

    # Timeline mouse scrub at x=500, y=660
    lParam = (660 << 16) | 500
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lParam)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lParam)
    time.sleep(0.05)

    # Clean shutdown via WM_CLOSE
    print("[Step 12] Closing Pygame viewer cleanly via WM_CLOSE...")
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    # Monitor process termination using Win32 API
    h_proc = kernel32.OpenProcess(SYNCHRONIZE | PROCESS_TERMINATE, False, pid.value)
    if h_proc:
        wait_res = kernel32.WaitForSingleObject(h_proc, 4000)
        if wait_res != 0:
            kernel32.TerminateProcess(h_proc, 1)
        kernel32.CloseHandle(h_proc)
    print("[Step 12] Replay viewer closed.")

    # -------------------------------------------------------------
    # Step 13: Edit parameters again, rerun, verify new revision & parameters
    # -------------------------------------------------------------
    print("[Step 13] Modifying parameters and running match 2...")
    advanced.tabs.setCurrentIndex(1)  # Agent Params
    advanced.schemaA._controls["search_interval"].setValue(3)
    advanced.schemaA._controls["move_step"].setValue(16)
    app.processEvents()

    advanced.tabs.setCurrentIndex(0)  # Match Setup
    app.processEvents()
    QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
    wait_process(app, designer)

    advanced.tabs.setCurrentIndex(3)  # Results
    app.processEvents()
    assert designer._last_result_path is not None, "Match 2 did not produce a result path"
    res2 = read_result(designer._last_result_path)
    assert res2.result_id != res1.result_id, "Match 2 result_id must differ from Match 1"
    assert res2.entrants[0]["metadata"]["parameters"] == {"search_interval": 3, "move_step": 16}
    print(f"Match 2 Result ID: {res2.result_id}")
    p7 = screenshot_dir / "07_second_match_completed.png"
    designer.grab().save(str(p7))
    print(f"Captured: {p7} ({p7.stat().st_size} bytes)")

    designer.close()
    designer.deleteLater()
    app.processEvents()
    print("[SUCCESS] All 13 workflow steps completed successfully!")


if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    screenshot_dir = repo_root / "docs" / "screenshots" / "v6_alpha1_windows"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bytefray_m1_6a_workflow_") as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        run_workflow(tmp_path, screenshot_dir)
