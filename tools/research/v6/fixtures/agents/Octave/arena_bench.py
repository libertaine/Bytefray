#!/usr/bin/env python3
"""Batch win-rate harness: run A vs B over N seeds, both seat orders.

Usage:
  python3 tools/arena_bench.py <agent> <opponent>[,<opponent>...] [--seeds 12] [--ticks 400]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

WINNER_RE = re.compile(r"Winner: (\S*?);")


def run_one(args):
    a, b, seed, ticks, arena = args
    with tempfile.TemporaryDirectory() as td:
        cmd = [
            "bytefray", "run",
            "--a-type", a, "--b-type", b,
            "--seed", str(seed), "--ticks", str(ticks),
            "--arena", str(arena),
            "--replay", os.path.join(td, "r.jsonl"),
            "--quiet",
        ]
        env = dict(os.environ)
        env["BYTEFRAY_DATA_ROOT"] = td
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
        out = proc.stdout + proc.stderr
        m = WINNER_RE.search(out)
        winner = m.group(1) if m else "?"
        ticks_run = None
        found = False
        rp = os.path.join(td, "result.json")
        for cand in (rp, os.path.join(td, "runs", "_loose", "result.json")):
            if os.path.exists(cand):
                try:
                    d = json.load(open(cand))
                    ticks_run = d.get("ticks")
                    winner = d.get("winner") or "tie"
                    found = True
                except Exception:
                    pass
                break
        if not found and winner == "?":
            return (a, b, seed, "ERR", ticks_run, out[-400:])
        return (a, b, seed, winner, ticks_run, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("opponents")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--arena", type=int, default=4096)
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()

    opponents = [o for o in a.opponents.split(",") if o]
    jobs = []
    for opp in opponents:
        for seed in range(1, a.seeds + 1):
            jobs.append((a.agent, opp, seed * 101 + 7, a.ticks, a.arena))   # as A
            jobs.append((opp, a.agent, seed * 101 + 7, a.ticks, a.arena))   # as B

    results = []
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for r in ex.map(run_one, jobs):
            results.append(r)

    tally = {}
    errs = []
    for (pa, pb, seed, winner, ticks_run, err) in results:
        me_slot = "A" if pa == a.agent else "B"
        opp = pb if pa == a.agent else pa
        t = tally.setdefault(opp, {"w": 0, "l": 0, "t": 0, "e": 0, "ticks": []})
        if winner == "ERR":
            t["e"] += 1
            errs.append(err)
        elif winner == me_slot:
            t["w"] += 1
        elif winner in ("", "tie"):
            t["t"] += 1
        else:
            t["l"] += 1
        if ticks_run:
            t["ticks"].append(ticks_run)

    total_w = total_l = total_t = total_e = 0
    print(f"{'opponent':28s} {'W':>4s} {'L':>4s} {'T':>4s} {'E':>3s}  {'win%':>6s}  {'avg_ticks':>9s}")
    for opp in sorted(tally):
        t = tally[opp]
        n = t["w"] + t["l"] + t["t"]
        wp = 100.0 * t["w"] / n if n else 0.0
        at = sum(t["ticks"]) / len(t["ticks"]) if t["ticks"] else 0
        print(f"{opp:28s} {t['w']:4d} {t['l']:4d} {t['t']:4d} {t['e']:3d}  {wp:6.1f}  {at:9.1f}")
        total_w += t["w"]; total_l += t["l"]; total_t += t["t"]; total_e += t["e"]
    n = total_w + total_l + total_t
    print("-" * 70)
    print(f"{'TOTAL':28s} {total_w:4d} {total_l:4d} {total_t:4d} {total_e:3d}  "
          f"{100.0*total_w/n if n else 0:6.1f}")
    if errs:
        print("\nfirst error:\n", errs[0][:800], file=sys.stderr)


if __name__ == "__main__":
    main()
