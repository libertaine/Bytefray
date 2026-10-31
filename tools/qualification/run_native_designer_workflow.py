"""Native Windows Active Sensing authoring workflow witness.

Executes the current authoring workflow under QT_QPA_PLATFORM=windows with
unmocked Pygame replay launching, complete Win32 input dispatch, and authentic
window grab captures retained with the run's isolated evidence directory.
"""
from __future__ import annotations

import argparse
import ctypes
import os
import pathlib
import sys
import tempfile
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

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
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


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

    from battle_engine.result_model import read_result, verify_result_replay
    from battle_engine.ruleset_names import ACTIVE_SENSING_DISPLAY_NAME
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from app.agent_designer import AgentDesigner
    from app.services.ruleset_options import DESIGNER_RULESET_ID
    from app.views.development import NewAgentDialog

    app = QApplication.instance() or QApplication(sys.argv)
    designer = AgentDesigner()
    designer.show()
    app.processEvents()
    time.sleep(0.3)

    # -------------------------------------------------------------
    # Step 1 & 2: Launch the single-product Designer
    # -------------------------------------------------------------
    print("[Step 1-2] Confirming defaults...")
    assert DESIGNER_RULESET_ID == "bytefray-rules-6-alpha1"
    assert designer.isVisible()
    assert not hasattr(designer.development, "rulesetCombo")
    assert not hasattr(designer.advanced, "ruleset")
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
    # The created sensing agent is runnable under the sole product Ruleset.
    # -------------------------------------------------------------
    assert designer.development.btnTest.isEnabled()

    # -------------------------------------------------------------
    # Step 4 & 6: Validate with Active Sensing
    # -------------------------------------------------------------
    print("[Step 4 & 6] Validating under Active Sensing...")
    app.processEvents()
    assert designer.development.btnTest.isEnabled()
    QTest.mouseClick(designer.development.btnValidate, Qt.LeftButton)
    wait_process(app, designer)
    assert "Last validation: Valid" in designer.development.statusLabel.text()
    p4 = screenshot_dir / "04_alpha1_validated.png"
    designer.grab().save(str(p4))
    print(f"Captured: {p4} ({p4.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # Step 5: Configure parameters in Advanced -> Agent Params
    # -------------------------------------------------------------
    print("[Step 5] Configuring parameters in Advanced -> Agent Params...")
    designer.tabs.setCurrentWidget(designer.advanced)
    advanced = designer.advanced
    assert advanced.agentA.findData("my_window_scout") >= 0
    assert advanced.agentB.findData("v6_watchful_keeper") >= 0
    advanced.agentA.setCurrentIndex(advanced.agentA.findData("my_window_scout"))
    advanced.agentB.setCurrentIndex(advanced.agentB.findData("v6_watchful_keeper"))
    assert advanced.agentA.currentData() == "my_window_scout"
    assert advanced.agentB.currentData() == "v6_watchful_keeper"
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
    assert verify_result_replay(designer._last_result_path)
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
        hwnd = user32.FindWindowW(None, f"Bytefray — {ACTIVE_SENSING_DISPLAY_NAME} replay")
        if hwnd:
            break
        app.processEvents()
        time.sleep(0.1)

    assert hwnd, "Pygame sensing replay window not detected by FindWindowW"

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h_proc = kernel32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    assert h_proc, "Replay process handle unavailable; clean exit cannot be verified"
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

    # Verify the actual viewer's exit; a forced termination is not a pass.
    try:
        assert kernel32.WaitForSingleObject(h_proc, 4000) == 0, "Replay viewer did not exit cleanly"
        exit_code = wintypes.DWORD()
        assert kernel32.GetExitCodeProcess(h_proc, ctypes.byref(exit_code))
        assert exit_code.value == 0, f"Replay viewer exit code: {exit_code.value}"
    finally:
        kernel32.CloseHandle(h_proc)
    print(f"[Step 12] Replay viewer PID {pid.value} exited zero.")

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
    assert verify_result_replay(designer._last_result_path)
    assert res2.ruleset_id == "bytefray-rules-6-alpha1"
    assert res2.result_id != res1.result_id, "Match 2 result_id must differ from Match 1"
    assert res2.entrants[0]["metadata"]["parameters"] == {"search_interval": 3, "move_step": 16}
    print(f"Match 2 Result ID: {res2.result_id}")
    p7 = screenshot_dir / "07_second_match_completed.png"
    designer.grab().save(str(p7))
    print(f"Captured: {p7} ({p7.stat().st_size} bytes)")

    designer.close()
    designer.deleteLater()
    app.processEvents()
    print("[SUCCESS] Current Active Sensing authoring workflow completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, help="new directory for retained native evidence")
    args = parser.parse_args()
    if args.output_dir is None:
        evidence_dir = pathlib.Path(tempfile.mkdtemp(prefix="bytefray_native_workflow_"))
    else:
        evidence_dir = args.output_dir.resolve()
        evidence_dir.mkdir(parents=True, exist_ok=False)
    screenshot_dir = evidence_dir / "screenshots"
    screenshot_dir.mkdir()
    print(f"Evidence: {evidence_dir}", flush=True)
    run_workflow(evidence_dir / "data", screenshot_dir)
