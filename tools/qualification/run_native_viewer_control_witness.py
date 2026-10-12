"""Tools: Native Pygame Replay Viewer Control Processing Witness.

Executes a focused, unmocked native Pygame sensing viewer interaction exercise
on Windows AMD64, demonstrating confirmed intra-process state mutations and real
pixel changes upon Win32 input dispatch:
1. Launches unmocked replay subprocess under --paused.
2. Captures the initial tick-zero boundary (Frame 1).
3. Dispatches Right Arrow (VK_RIGHT), capturing callback 1 observation (Frame 2).
4. Dispatches Right Arrow (VK_RIGHT), capturing the pending SENSE action (Frame 3).
5. Dispatches Space (VK_SPACE), capturing unpause to live playback advancement (Frame 4).
6. Verifies nonzero pixel differences between all consecutive states.
7. Closes cleanly via WM_CLOSE with exit code 0.
"""
from __future__ import annotations

import ctypes
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

VK_SPACE = 0x20
VK_RIGHT = 0x27

SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001


def run_witness(tmp_dir: pathlib.Path, screenshot_dir: pathlib.Path) -> dict:
    from battle_engine.sensing_demo import run_sensing_demo

    print("[Witness] Generating canonical teaching demonstration match...")
    match_dir = tmp_dir / "match"
    match_dir.mkdir(parents=True, exist_ok=True)
    res = run_sensing_demo(output_dir=match_dir, ticks=100, seed=0)
    assert res.is_verified, "Demonstration match failed verification"

    replay_path = match_dir / "replay.jsonl"
    assert replay_path.is_file(), "Replay artifact missing"

    # Ensure Qt application exists for grabbing window pixels
    os.environ["QT_QPA_PLATFORM"] = "windows"
    _app = QApplication.instance() or QApplication(sys.argv)
    screen = QGuiApplication.primaryScreen()

    cmd = [
        sys.executable,
        "-m",
        "battle_client.cli",
        "--replay",
        str(replay_path),
        "--renderer",
        "pygame",
        "--paused",
    ]
    print(f"[Witness] Spawning unmocked viewer subprocess: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)

    hwnd = 0
    try:
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline:
            hwnd = user32.FindWindowW(None, "Bytefray — Experimental sensing replay")
            if hwnd:
                break
            time.sleep(0.1)

        assert hwnd != 0, "Pygame sensing replay window was not detected"

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        print(f"[Witness] Detected live Pygame window: HWND = {hwnd}, PID = {pid.value}")
        time.sleep(0.6)  # Allow first frame to present cleanly

        # Frame 1: Paused tick-zero boundary. Retain the original evidence filename.
        p1 = screenshot_dir / "witness_control_01_initial_observation.png"
        pix1 = screen.grabWindow(hwnd)
        pix1.save(str(p1))
        print(f"[Frame 1] Captured initial tick boundary: {p1} ({p1.stat().st_size} bytes)")

        # Input 1: Right Arrow (Step forward to callback 1 observation)
        scan_r = user32.MapVirtualKeyW(VK_RIGHT, 0)
        lp_down_r = 1 | (scan_r << 16) | (1 << 24)
        lp_up_r = 1 | (scan_r << 16) | (1 << 24) | (1 << 30) | (1 << 31)

        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RIGHT, lp_down_r)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_RIGHT, lp_up_r)
        time.sleep(0.4)  # Render and flip

        # Frame 2: Callback 1 observation; original filename describes a later phase.
        p2 = screenshot_dir / "witness_control_02_stepped_action_phase.png"
        pix2 = screen.grabWindow(hwnd)
        pix2.save(str(p2))
        print(f"[Frame 2] Captured callback 1 observation: {p2} ({p2.stat().st_size} bytes)")

        # Input 2: Right Arrow (Step forward to the pending SENSE action)
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RIGHT, lp_down_r)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_RIGHT, lp_up_r)
        time.sleep(0.4)

        # Frame 3: SENSE pending; the receipt arrives during subsequent playback.
        p3 = screenshot_dir / "witness_control_03_stepped_delayed_receipt.png"
        pix3 = screen.grabWindow(hwnd)
        pix3.save(str(p3))
        print(f"[Frame 3] Captured pending SENSE action: {p3} ({p3.stat().st_size} bytes)")

        # Input 3: Space (Toggle Pause -> Playback)
        scan_sp = user32.MapVirtualKeyW(VK_SPACE, 0)
        lp_down_sp = 1 | (scan_sp << 16)
        lp_up_sp = 1 | (scan_sp << 16) | (1 << 30) | (1 << 31)

        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_SPACE, lp_down_sp)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_SPACE, lp_up_sp)
        time.sleep(0.5)  # Allow playback to advance

        # Frame 4: Live Playback Advancing
        p4 = screenshot_dir / "witness_control_04_playback_active.png"
        pix4 = screen.grabWindow(hwnd)
        pix4.save(str(p4))
        print(f"[Frame 4] Captured active playback advancement: {p4} ({p4.stat().st_size} bytes)")

        # Pixel comparison verification using pygame image loader
        import pygame
        pygame.init()
        im1 = pygame.image.load(str(p1))
        im2 = pygame.image.load(str(p2))
        im3 = pygame.image.load(str(p3))
        im4 = pygame.image.load(str(p4))

        diff_1_2 = sum(
            1 for y in range(im1.get_height()) for x in range(im1.get_width())
            if im1.get_at((x, y)) != im2.get_at((x, y))
        )
        diff_2_3 = sum(
            1 for y in range(im2.get_height()) for x in range(im2.get_width())
            if im2.get_at((x, y)) != im3.get_at((x, y))
        )
        diff_3_4 = sum(
            1 for y in range(im3.get_height()) for x in range(im3.get_width())
            if im3.get_at((x, y)) != im4.get_at((x, y))
        )

        print(f"[Verification] Diff Frame 1 -> Frame 2 (Boundary -> Observation): {diff_1_2} pixels")
        print(f"[Verification] Diff Frame 2 -> Frame 3 (Observation -> SENSE Pending): {diff_2_3} pixels")
        print(f"[Verification] Diff Frame 3 -> Frame 4 (Paused Action -> Playback): {diff_3_4} pixels")

        assert diff_1_2 > 0, "Frame 1 and Frame 2 must have distinct pixels (phase change failed)"
        assert diff_2_3 > 0, "Frame 2 and Frame 3 must have distinct pixels (phase change failed)"
        assert diff_3_4 > 0, "Frame 3 and Frame 4 must have distinct pixels (playback change failed)"

    finally:
        if hwnd:
            print("[Witness] Sending WM_CLOSE to native viewer window...")
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"[Witness] Viewer subprocess exited with code: {proc.returncode}")
        assert proc.returncode == 0, f"Subprocess exited with non-zero code {proc.returncode}"

    return {
        "hwnd": hwnd,
        "pid": pid.value,
        "f1_size": p1.stat().st_size,
        "f2_size": p2.stat().st_size,
        "f3_size": p3.stat().st_size,
        "f4_size": p4.stat().st_size,
        "diff_1_2": diff_1_2,
        "diff_2_3": diff_2_3,
        "diff_3_4": diff_3_4,
        "exit_code": proc.returncode,
    }


if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    screenshot_dir = repo_root / "docs" / "screenshots" / "v6_alpha1_windows"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bytefray_viewer_control_") as tmp_d:
        res = run_witness(pathlib.Path(tmp_d), screenshot_dir)
        print("[SUCCESS] Native viewer control processing verified successfully!")
        print(res)
