# Owner: 01 · Lead and story (Mario)
"""01 · Lead: is products/<site>/ complete and sane? Run it at hours 2, 12, 24 and 40, and before pushing products.

Status: WORKS (checks the file contracts in docs/build-spec.md).

    python checkpoint.py ocnele_mari
    python checkpoint.py mock                         # the invented set from mock_products.py
    python checkpoint.py mock --products /tmp/prod    # another products folder (tests/test_skeleton.py uses this)

Exit 1 if the contract is broken (the page would fail to load the site). Science WARN/FAIL lines from checks.json are
listed, not fatal: read each aloud and give it an owner and a verdict (fix, cut or explain).
When the contract changes, change this file and the page in the same PR.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import common as C

NEED = ["manifest.json", "series.json", "stations.geojson", "calib.json", "checks.json"]
MANIFEST_KEYS = ("site", "name", "story", "synthetic", "built", "bounds", "center", "view",
                 "layers", "frames", "checks", "credits")
LAYER_KEYS = ("id", "label", "png", "units", "vmin", "vmax")
STATUSES = ("pass", "warn", "fail", "info")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(site: str, root: pathlib.Path) -> tuple[list[str], list[str], dict | None, list]:
    """→ (broken, notes, manifest, checks). `broken` = contract errors; `notes` = things a human should look at."""
    out, bad, notes = root / site, [], []
    if not out.is_dir():
        return [f"no folder {out}"], notes, None, []
    bad += [f"missing {f}" for f in NEED if not (out / f).exists()]
    if bad:
        return bad, notes, None, []

    m = C.load_json(out / "manifest.json")
    bad += [f"manifest has no '{k}'" for k in MANIFEST_KEYS if k not in m]
    b = m.get("bounds")
    if not (isinstance(b, list) and len(b) == 2 and b[0][0] < b[1][0] and b[0][1] < b[1][1]):
        bad.append("manifest.bounds must be [[S, W], [N, E]] with S < N and W < E")
    v = m.get("view") or {}
    if not (isinstance(v.get("center"), list) and len(v["center"]) == 2 and isinstance(v.get("zoom"), int)):
        bad.append("manifest.view needs center [lat, lon] and an integer zoom (D-002)")
    for layer in m.get("layers", []):
        bad += [f"layer {layer.get('id')} has no '{k}'" for k in LAYER_KEYS if k not in layer]
        if "png" in layer and not (out / layer["png"]).exists():
            bad.append(f"layer png missing: {layer['png']}")
    for t, f in m.get("frames", {}).items():
        dates, pngs = f.get("dates", []), f.get("pngs", [])
        if len(dates) != len(pngs):
            bad.append(f"track {t}: {len(dates)} dates but {len(pngs)} pngs")
        if any(not ISO.match(d) for d in dates) or dates != sorted(dates):
            bad.append(f"track {t}: dates must be sorted YYYY-MM-DD")
        if len(dates) < 5:
            notes.append(f"track {t}: only {len(dates)} frames")
        bad += [f"frame missing: {p}" for p in pngs if not (out / p).exists()][:3]
    if m.get("synthetic"):
        notes.append("SYNTHETIC / MOCK site: the page must show the 'simulated, not data' banner")
    if "TODO" in str(m.get("story", "")):
        notes.append("story is still a TODO (01)")

    series = C.load_json(out / "series.json")
    if not isinstance(series, list) or not series:
        bad.append("series.json must be a non-empty list")
    else:
        for p in series:
            miss = [k for k in ("id", "label", "kind", "lat", "lon", "series") if k not in p]
            if miss:
                bad.append(f"series point {p.get('id')} has no {', '.join(miss)}")
                break
    gj = C.load_json(out / "stations.geojson")
    if gj.get("type") != "FeatureCollection":
        bad.append("stations.geojson must be a FeatureCollection")
    checks = C.load_json(out / "checks.json")
    if not isinstance(checks, list) or any(c.get("status") not in STATUSES for c in checks):
        bad.append(f"checks.json must be a list of {{id, status in {STATUSES}, title, detail}}")
        checks = []
    if "tracks" not in C.load_json(out / "calib.json"):
        bad.append("calib.json has no 'tracks'")
    idx = root / "index.json"
    if not idx.exists() or site not in [s.get("site") for s in C.load_json(idx)]:
        notes.append("products/index.json does not list this site (the page's site picker will miss it)")
    return bad, notes, m, checks


def report(site: str, bad: list[str], notes: list[str], m: dict | None, checks: list) -> bool:
    print(f"== checkpoint · {site}")
    if m:
        print(f"   {m.get('name')} · {'SYNTHETIC' if m.get('synthetic') else 'real data'} · built {m.get('built')} · "
              f"{len(m.get('layers', []))} layers · tracks {', '.join(m.get('frames', {})) or 'none'}")
    for b in bad:
        print("   CONTRACT ✘", b)
    for n in notes:
        print("   NOTE      ", n)
    for c in checks:
        if c["status"] in ("fail", "warn"):
            print(f"   {c['status'].upper():5s} {c.get('title')}: {c.get('detail')}")
    if checks:
        n = {k: sum(c["status"] == k for c in checks) for k in STATUSES}
        print(f"   checks: {n['pass']} pass · {n['warn']} warn · {n['fail']} fail · {n['info']} info")
    print("   contract OK" if not bad else "   contract BROKEN: the page will not load this site")
    return not bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", help="folder name under products/, e.g. ocnele_mari, demo, mock")
    ap.add_argument("--products", type=pathlib.Path, default=C.PRODUCTS, help="products folder (default: products/)")
    a = ap.parse_args()
    sys.exit(0 if report(a.site, *check(a.site, a.products)) else 1)


if __name__ == "__main__":
    main()
