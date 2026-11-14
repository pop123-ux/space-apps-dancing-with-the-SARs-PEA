"""Shared: run the pipeline end to end, one command. Each step is the script one team member owns.

Status: WORKS (stops cleanly at the first step that is still a stub).

    python run_all.py demo                        # synthetic known-answer chain (offline once fetch/refs synthetic exist)
    python run_all.py ocnele_mari                 # real NISAR (EARTHDATA_TOKEN set)
    python run_all.py ocnele_mari --from stack    # rerun downstream of a step, e.g. after a new tie
    python run_all.py ocnele_mari --to split      # stop after a step

hyp3_order.py (05) is not in the chain: it orders Sentinel-1 jobs that take hours, so the validator runs it separately.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

import common as C

STEPS = [("refs", "04"), ("fetch", "02"), ("stack", "03"), ("calibrate", "04"),
         ("split", "03"), ("validate", "05"), ("export", "06"), ("checkpoint", "01")]


def main() -> None:
    names = [s for s, _ in STEPS]
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--from", dest="start", default=names[0], choices=names)
    ap.add_argument("--to", dest="stop", default=names[-1], choices=names)
    a = ap.parse_args()
    extra = {"fetch": ["--synthetic"]} if C.SITES[a.site].get("synthetic") else {}
    for step, role in STEPS[names.index(a.start):names.index(a.stop) + 1]:
        t = time.time()
        print(f"\n▶ {step}.py  ({role} · {C.ROLES[role]})", flush=True)
        r = subprocess.run([sys.executable, f"{step}.py", a.site] + extra.get(step, []), cwd=C.ROOT,
                           env=dict(os.environ, PYTHONUNBUFFERED="1"))
        if r.returncode == C.STUB_EXIT:
            print(f"⏳ stopped: {step}.py (or a step it needs) is still a stub", file=sys.stderr)
            sys.exit(C.STUB_EXIT)
        if r.returncode:
            sys.exit(f"✘ {step}.py failed (exit {r.returncode})")
        print(f"  {time.time() - t:.0f} s")
    print(f"\nDone. products/{a.site}/ is ready for the page.")


if __name__ == "__main__":
    main()
