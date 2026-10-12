"""Supply the X11 focus that a desktop window manager normally supplies."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    if item.name != "test_keyboard_navigation_action_tab_order_and_filter_focus":
        return (yield)
    previous = sys.getprofile()

    def focus(frame, event, arg):
        if (
            event == "return"
            and frame.f_code.co_name == "_opened"
            and frame.f_globals.get("__name__") == "test_v5_replay_history_browser"
        ):
            env = frame.f_locals["env"]
            window = arg
            before = env.app.focusWidget()
            subprocess.run(
                ["xdotool", "windowfocus", "--sync", str(int(window.winId()))], check=True
            )
            assert env.until(lambda: window.isActiveWindow())
            proof = {
                "display": os.environ["DISPLAY"],
                "platform": env.app.platformName(),
                "window": int(window.winId()),
                "active": window.isActiveWindow(),
                "focus_before": str(before),
                "focus_after": str(env.app.focusWidget()),
                "stimulus": "xdotool windowfocus --sync",
            }
            (
                Path(os.environ.get("BYTEFRAY_LINUX_QUALIFICATION_DIR", "/tmp/bytefray-m1-6b"))
                / "evidence/final/focus_assist.json"
            ).write_text(json.dumps(proof, indent=2) + "\n")

    sys.setprofile(focus)
    try:
        return (yield)
    finally:
        sys.setprofile(previous)
