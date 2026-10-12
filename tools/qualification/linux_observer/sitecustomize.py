"""Qualification-only passive observer; never supplies input or changes playback."""

import json
import os
import sys
import time
from pathlib import Path

out = os.environ.get("BYTEFRAY_LINUX_WITNESS")
last = None


def observe(frame, event, arg):
    global last
    if event != "return" or frame.f_code.co_name != "draw":
        return
    if frame.f_globals.get("__name__") != "battle_client.renderers.sensing_renderer":
        return
    try:
        renderer = frame.f_locals["self"]
        p = frame.f_locals["presentation"]
        view = p.current_view
        pos = p.position
        state = {
            "pid": os.getpid(),
            "argv": sys.argv,
            "index": p.index,
            "tick": pos.tick,
            "callback": pos.callback,
            "phase": pos.phase.value,
            "view": type(view).__name__,
            "label": view.label,
            "playing": p.controller.playing,
            "speed": p.speed,
            "terminal": p.terminal_text,
            "driver": renderer.pg.display.get_driver(),
            "size": renderer.screen.get_size(),
            "contacts": [
                {"address": c.address, "age_ticks": c.age_ticks, "age_callbacks": c.age_callbacks}
                for c in getattr(view, "contacts", ())
            ],
            "own_anchors": [a.anchor for a in getattr(view, "own_processes", ())],
            "receipt_status": getattr(getattr(view, "receipt_status", None), "value", None),
            "lines": list(renderer.last_lines) if type(view).__name__ == "SensingView" else [],
        }
        key = json.dumps(state, sort_keys=True)
        if key != last:
            last = key
            state["monotonic_ns"] = time.monotonic_ns()
            with Path(out).open("a") as f:
                f.write(json.dumps(state) + "\n")
    except Exception as exc:
        with Path(out + ".errors").open("a") as f:
            f.write(repr(exc) + "\n")


if out:
    sys.setprofile(observe)
