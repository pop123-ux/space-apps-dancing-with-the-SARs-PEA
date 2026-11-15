# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Order the Sentinel-1 burst pairs that extend the stack to every acquisition ASF holds since May 2025.

    python scripts/order_all.py CATALOG_029.json CATALOG_007.json --plan      # list the pairs, no login
    python scripts/order_all.py CATALOG_029.json CATALOG_007.json --submit    # submit on HyP3 (Earthdata token)
    python scripts/order_all.py --status                                      # job status, writes the CSV rows

The catalogs are ASF searches (output=jsonlite) of the same two bursts the stack already uses (029_060407_IW2 and
007_013694_IW2, VV). Every acquisition date not yet in provenance/hyp3_jobs_jan_nov.csv is paired with the one and two
acquisitions after it, across the joint, so the new dates connect to the existing stack: the 6- and 12-day pattern of
the existing 214 jobs, same job type and parameters (INSAR_ISCE_BURST, 10x2 looks, water mask). Writes
provenance/hyp3_jobs_all.csv (the 214 earlier rows plus the new ones, batch "since_may2025").
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
API = "https://hyp3-api.asf.alaska.edu"
OLD = root / "provenance/hyp3_jobs_jan_nov.csv"
OUT = root / "provenance/hyp3_jobs_all.csv"
ORDER = root / "provenance/hyp3_order_since_may2025.json"
TRACK = {"029": "029A", "007": "007D"}


def api(path, body=None):   # the Earthdata token is added by the network proxy; it never appears here
    req = Request(API + path, data=json.dumps(body).encode() if body else None,
                  headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    with urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def plan(catalogs):
    old = list(csv.DictReader(OLD.open()))
    have = {}
    for r in old:
        have.setdefault(r["track"], set()).update({r["reference_date"], r["secondary_date"]})
    jobs = []
    for path in catalogs:
        res = json.load(open(path))["results"]
        trk = TRACK[res[0]["burst"]["fullBurstID"][:3]] if "burst" in res[0] else TRACK[Path(path).stem.split("_")[1]]
        by_date = {}
        for g in sorted(res, key=lambda g: g["granuleName"]):
            by_date.setdefault(g["startTime"][:10].replace("-", ""), g["granuleName"])
        dates = sorted(by_date)
        for i, d in enumerate(dates):
            for k in (1, 2):
                if i + k >= len(dates):
                    continue
                s = dates[i + k]
                if d in have[trk] and s in have[trk]:
                    continue                     # both dates already in the stack: that pair exists or is not needed
                jobs.append(dict(name=f"ocnele-mari-all-{trk}-{d}-{s}", job_type="INSAR_ISCE_BURST",
                                 job_parameters=dict(granules=[by_date[d], by_date[s]], looks="10x2", apply_water_mask=True)))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalogs", nargs="*")
    ap.add_argument("--plan", action="store_true"); ap.add_argument("--submit", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.plan or a.submit:
        jobs = plan(a.catalogs)
        print(f"{len(jobs)} new pairs:", {t: sum(j['name'].split('-')[3] == t for j in jobs) for t in TRACK.values()})
        if a.plan:
            for j in jobs:
                print(j["name"])
            return
        done = []
        for i in range(0, len(jobs), 100):
            r = api("/jobs", {"jobs": jobs[i:i + 100]})
            done += [dict(job_id=j["job_id"], name=j["name"], granules=j["job_parameters"]["granules"]) for j in r["jobs"]]
            print(f"submitted {len(done)}/{len(jobs)}")
        ORDER.write_text(json.dumps(dict(submitted=time.strftime("%Y-%m-%d"), jobs=done), indent=1) + "\n")
    if a.status:
        order = json.loads(ORDER.read_text())
        rows, states = [], {}
        for j in order["jobs"]:
            info = api(f"/jobs/{j['job_id']}")
            states[info["status_code"]] = states.get(info["status_code"], 0) + 1
            f = (info.get("files") or [{}])[0]
            _, trk, ref, sec = j["name"].rsplit("-", 3)
            rows.append(dict(name=j["name"], track=trk, reference_date=ref, secondary_date=sec, job_id=j["job_id"],
                             filename=f.get("filename", ""), size_kb=round(f["size"] / 1000) if f.get("size") else "",
                             url=f.get("url", ""), batch="since_may2025"))
        print(states)
        if set(states) <= {"SUCCEEDED", "FAILED"}:
            old = list(csv.DictReader(OLD.open()))
            with OUT.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(old[0]))
                w.writeheader(); w.writerows(old + [r for r in rows if r["url"]])
            print(f"wrote {OUT} ({len(old)} earlier + {sum(1 for r in rows if r['url'])} new rows)")
        return 0 if set(states) <= {"SUCCEEDED"} else 1


if __name__ == "__main__":
    sys.exit(main())
