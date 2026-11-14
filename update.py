# Owner: 02 · NISAR data (Alexandru, Eric)
"""02 · Keep the site current: find new Sentinel-1 and NISAR acquisitions, order and refit, so forecasts move forward.

    python update.py ocnele_mari --check     # no login: what is new since the fits → products/<site>/updates.json
    python update.py ocnele_mari --order     # Sentinel-1: submit HyP3 INSAR_ISCE_BURST jobs for the new dates (Earthdata)
    python update.py ocnele_mari --refit     # NISAR: stream new pairs and rerun stack → calibrate → split → export →
                                             # validate → export; then the forecast if its inputs are present

Runs by hand or on a schedule (.github/workflows/update.yml: weekly --check, opening a pull request when something is
new). Ordering and refitting need an Earthdata token (EARTHDATA_TOKEN, or a proxy that injects it) and, for the
Sentinel-1 refit, the HyP3 archives on disk (sentinel1/scripts/download.py for the recorded jobs).

What it watches (14 Nov 2026):
- Sentinel-1 bursts 029_060407_IW2 (029A) and 007_013694_IW2 (007D), VV, after the last date of each fitted window
  (sentinel1/analysis*/summary.json). ASF's search API, no login.
- NISAR L2 GUNW pairs over the site not yet in data/scenes/ocnele_mari_gunw.csv (fetch.search, NASA CMR, no login).

New pairs for Sentinel-1 are each new date with the one and two acquisitions before it (6- and 12-day pairs), the
pattern of the fitted stack. Nothing here changes a fitted number by itself: a refit is a new run that goes through
the same checks (validate.py) before the page shows it.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys

import common as C

BURSTS = {"029A": "029_060407_IW2", "007D": "007_013694_IW2"}
ASF = "https://api.daac.asf.alaska.edu/services/search/param"


def fitted_dates(track: str) -> list[str]:
    out = set()
    for f in sorted((C.ROOT / "sentinel1").glob("analysis*/summary.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        if track in s:
            out |= set(s[track]["dates"])
    return sorted(out)


def s1_new(track: str, after: str) -> list[dict]:
    import requests
    a = f"{after[:4]}-{after[4:6]}-{after[6:]}T23:59:59Z"
    r = requests.get(ASF, params=dict(dataset="SLC-BURST", fullBurstID=BURSTS[track], polarization="VV", start=a,
                                      output="jsonlite"), timeout=90)
    r.raise_for_status()
    rows = r.json()["results"]
    return sorted(({"date": x["startTime"][:10].replace("-", ""), "granule": x["granuleName"]} for x in rows),
                  key=lambda x: x["date"])


def check(site: str) -> dict:
    import fetch
    out = dict(checked=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), s1={}, nisar=[])
    for t in BURSTS:
        ds = fitted_dates(t)
        new = s1_new(t, ds[-1]) if ds else []
        out["s1"][t] = dict(last_fitted=ds[-1] if ds else None, new=[x["date"] for x in new], granules=[x["granule"] for x in new])
    known = {r["granule"].strip() for r in csv.DictReader((C.DATA / "scenes" / "ocnele_mari_gunw.csv").open(encoding="utf-8"))}
    for (trk, ref, sec), (gran, url, coll) in fetch.search(site).items():
        if gran not in known:
            out["nisar"].append(dict(track=trk, ref=ref, sec=sec, granule=gran, collection=coll))
    n = sum(len(v["new"]) for v in out["s1"].values()) + len(out["nisar"])
    out["summary"] = ("Up to date." if not n else
                      f"{n} new acquisitions since the fits: " + "; ".join(
                          [f"Sentinel-1 {t}: {len(v['new'])} (after {v['last_fitted']})" for t, v in out["s1"].items() if v["new"]]
                          + ([f"NISAR: {len(out['nisar'])} new pairs"] if out["nisar"] else [])) + ". Not fitted yet.")
    C.save_json(C.PRODUCTS / site / "updates.json", out)
    print(out["summary"])
    return out


def order(site: str) -> None:
    """Submit HyP3 INSAR_ISCE_BURST jobs: each new date with the one and two acquisitions before it."""
    import hyp3_sdk
    u = check(site)
    hyp3 = hyp3_sdk.HyP3()        # Earthdata: ~/.netrc or EDL credentials in the environment (never printed)
    rec = []
    for t, v in u["s1"].items():
        if not v["new"]:
            continue
        allg = s1_new(t, "20260101")
        dates = [x["date"] for x in allg]
        for g in v["granules"]:
            i = next(k for k, x in enumerate(allg) if x["granule"] == g)
            for back in (1, 2):
                if i - back < 0:
                    continue
                job = hyp3.submit_insar_isce_burst_job(allg[i - back]["granule"], g, name=f"ocnele_mari_{t}",
                                                       looks="10x2", apply_water_mask=True)
                rec.append(dict(track=t, reference=allg[i - back]["granule"], secondary=g, job_id=job.job_id))
                print(f"{t}: submitted {dates[i - back]} → {dates[i]} ({job.job_id})")
    p = C.ROOT / "sentinel1" / "provenance" / "hyp3_jobs_updates.json"
    old = json.loads(p.read_text()) if p.exists() else []
    p.write_text(json.dumps(old + rec, indent=1) + "\n")


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run([sys.executable, *cmd], cwd=C.ROOT, check=True)


def refit(site: str) -> None:
    """NISAR end to end (new pairs are streamed; existing ones are kept), then the products and the checks."""
    run(["fetch.py", site])
    for step in (["stack.py", site], ["calibrate.py", site], ["split.py", site], ["export.py", site],
                 ["validate.py", site], ["export.py", site]):
        run(step)
    print("Sentinel-1: download the finished HyP3 jobs (sentinel1/provenance/hyp3_jobs_updates.json), then run "
          "sentinel1/scripts/fit.py and forecast.py / forecast_chronos.py (docs/handoff-02-03.md, steps 4 and 5).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--order", action="store_true")
    g.add_argument("--refit", action="store_true")
    a = ap.parse_args()
    if C.SITES[a.site].get("synthetic"):
        raise C.todo("02", "updates are for real sites only")
    (check if a.check else order if a.order else refit)(a.site)


if __name__ == "__main__":
    C.run_cli(main)
