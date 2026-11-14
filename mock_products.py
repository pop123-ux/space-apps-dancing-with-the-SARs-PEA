# Owner: 06 · App developer (Darius)
"""06 · App developer: write an INVENTED products/mock/ in the contract's shape, so the page can be built right away.

Status: WORKS. Standard library only (no numpy, no Pillow).

    python mock_products.py                        # → products/mock/ and an entry in products/index.json
    python mock_products.py --out /tmp/products    # anywhere else (tests/test_skeleton.py does this)
    python mock_products.py --size 400             # bigger overlays (default 200 px)

Every value is made up: four small bowls at the draft salt zones, some smooth "atmosphere", and two station pins (one
agreeing, one not). Every file says synthetic: true, so the page must show the "simulated, not data" banner. The dates are
the real NISAR acquisition dates over Ocnele Mari (CMR, 14 Nov 2026), so the slider already has to cope with the real
18 Jan → 23 Jun 2026 gap on 129A. When the file contracts in docs/build-spec.md change, change this file too.
"""
from __future__ import annotations

import argparse
import datetime
import math
import pathlib
import random
import struct
import zlib

import common as C

SITE = "mock"
DATES = {   # real acquisition dates over Ocnele Mari (NASA CMR, 14 Nov 2026)
    "129A": ["2025-11-07", "2025-12-01", "2025-12-13", "2025-12-25", "2026-01-18", "2026-06-23", "2026-07-05",
             "2026-07-17", "2026-08-10", "2026-08-22", "2026-09-03", "2026-09-15", "2026-09-27", "2026-10-09", "2026-10-21"],
    "094D": ["2026-06-20", "2026-07-02", "2026-07-14", "2026-07-26", "2026-08-19", "2026-08-31", "2026-09-12",
             "2026-09-24", "2026-10-06", "2026-10-18"],
}
GAPS = {"129A": [["2026-01-18", "2026-06-23"]], "094D": []}
LOS = {"129A": dict(e=0.62, u=0.77, direction="Ascending"), "094D": dict(e=-0.60, u=0.78, direction="Descending")}
BOWL_MM_YR = (-18.0, -10.0, -14.0, -6.0)   # invented, one per draft zone


# ----------------------------------------------------------------------------------------------- tiny PNG writer
def write_png(path: pathlib.Path, w: int, h: int, rgba: bytearray) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def rdbu(v: float) -> tuple[int, int, int]:
    """v in [-1, 1] → RdBu-like colour: red = negative (sinking / away), blue = positive, near-white = 0."""
    stops = [(-1.0, (103, 0, 31)), (-0.5, (214, 96, 77)), (0.0, (247, 247, 247)), (0.5, (67, 147, 195)), (1.0, (5, 48, 97))]
    v = max(-1.0, min(1.0, v))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            f = (v - a) / (b - a)
            return tuple(round(x + (y - x) * f) for x, y in zip(ca, cb))
    return stops[-1][1]


def overlay(path: pathlib.Path, field: list[list[float]], vmax: float) -> None:
    h, w = len(field), len(field[0])
    px = bytearray(w * h * 4)
    for r, row in enumerate(field):
        for c, v in enumerate(row):
            i = (r * w + c) * 4
            if v is None or math.isnan(v):
                continue
            px[i:i + 3] = bytes(rdbu(v / vmax))
            px[i + 3] = 217
    write_png(path, w, h, px)


# ----------------------------------------------------------------------------------------------- invented fields
def make_fields(site: dict, n: int):
    rng = random.Random(7)
    dlat = site["half_km"] / 111.2
    dlon = site["half_km"] / (111.2 * math.cos(math.radians(site["lat"])))
    S, N, W, E = site["lat"] - dlat, site["lat"] + dlat, site["lon"] - dlon, site["lon"] + dlon
    lats = [N - (N - S) * (r + 0.5) / n for r in range(n)]
    lons = [W + (E - W) * (c + 0.5) / n for c in range(n)]
    kx = 111.2 * math.cos(math.radians(site["lat"]))   # km per degree of longitude

    def bowls(lat, lon):
        up = east = 0.0
        for z, amp in zip(site["zones"], BOWL_MM_YR):
            dx, dy = (lon - z["lon"]) * kx, (lat - z["lat"]) * 111.2
            sig = 0.9   # km: wider than the real zones, so the mock is visible at zoom 13
            g = math.exp(-(dx * dx + dy * dy) / (2 * sig * sig))
            up += amp * g
            east += -0.3 * amp * dx / sig * g
        return up, east

    blobs = [(rng.uniform(S, N), rng.uniform(W, E), rng.uniform(3, 9), rng.uniform(-1, 1)) for _ in range(14)]

    def atmos(lat, lon):
        return sum(a * math.exp(-(((lon - bl) * kx) ** 2 + ((lat - bt) * 111.2) ** 2) / (2 * s * s)) for bt, bl, s, a in blobs)

    up = [[0.0] * n for _ in range(n)]
    east = [[0.0] * n for _ in range(n)]
    noise = [[0.0] * n for _ in range(n)]
    for r, la in enumerate(lats):
        for c, lo in enumerate(lons):
            up[r][c], east[r][c] = bowls(la, lo)
            noise[r][c] = atmos(la, lo)
    return dict(bounds=[[S, W], [N, E]], lats=lats, lons=lons, up=up, east=east, noise=noise, bowls=bowls, atmos=atmos)


def years_since(d0: str, d: str, gaps: list[list[str]]) -> float:
    """Years from d0 to d, holding still across gaps (no pair spans them, so the real series is flat there)."""
    p = lambda s: datetime.date.fromisoformat(s)
    days = (p(d) - p(d0)).days
    for a, b in gaps:
        if p(d) >= p(b):
            days -= (p(b) - p(a)).days
    return days / 365.25


# ----------------------------------------------------------------------------------------------- the contract
def build(root: pathlib.Path, n: int) -> None:
    site = C.SITES["ocnele_mari"]
    out = root / SITE
    F = make_fields(site, n)
    rng = random.Random(11)
    layers = []

    def layer(id_, label, field, vmax):
        overlay(out / f"{id_}.png", field, vmax)
        layers.append(dict(id=id_, label=label, png=f"{id_}.png", units="mm/yr", vmin=-vmax, vmax=vmax))

    layer("up", "Vertical rate (− = sinking) · MOCK", F["up"], 20)
    layer("east", "East–west rate (+ = east) · MOCK", F["east"], 10)
    frames, los_rate = {}, {}
    for t, g in LOS.items():
        lr = [[g["u"] * u + g["e"] * e for u, e in zip(ru, re)] for ru, re in zip(F["up"], F["east"])]
        los_rate[t] = lr
        layer(f"los_{t}", f"Line of sight, track {t} (+ = towards satellite) · MOCK", lr, 20)
        dates, pngs = DATES[t], []
        for k, d in enumerate(dates):
            yr = years_since(dates[0], d, GAPS[t])
            amp = 0.0 if k == 0 else rng.uniform(-4, 4)   # invented atmosphere of the day, mm
            cum = [[v * yr + amp * a for v, a in zip(rv, ra)] for rv, ra in zip(lr, F["noise"])]
            png = f"frames/{t}/{d}.png"
            overlay(out / png, cum, 20)
            pngs.append(png)
        frames[t] = dict(dates=dates, pngs=pngs, vmin=-20, vmax=20, units="mm since first date",
                         direction=g["direction"], gaps=GAPS[t])

    # series at the zones and the stations
    pts = [dict(id=z["id"], label=f"Salt zone {z['id']} · MOCK", kind="zone", lat=z["lat"], lon=z["lon"])
           for z in site["zones"]]
    stations = {s: C.PUBLISHED[s][:2] for s in ("VLC2", "HORE")}
    pts += [dict(id=s, label=f"{s} · MOCK", kind="station", lat=la, lon=lo) for s, (la, lo) in stations.items()]
    for p in pts:
        up, east = F["bowls"](p["lat"], p["lon"])
        p["up"] = round(up, 1)
        p["series"] = {}
        for t, g in LOS.items():
            rate = g["u"] * up + g["e"] * east
            dates = DATES[t]
            mm = [round(rate * years_since(dates[0], d, GAPS[t]) + (0 if k == 0 else rng.uniform(-3, 3)), 1)
                  for k, d in enumerate(dates)]
            p["series"][t] = dict(dates=dates, mm=mm, rate=round(rate, 1))
    C.save_json(out / "series.json", pts)

    feats = []
    for (s, (la, lo)), agree in zip(stations.items(), (True, False)):
        tr = {}
        for t in LOS:
            nis = round(rng.uniform(-3, 3), 2)
            gn = round(nis + (rng.uniform(-1, 1) if agree else 9.5), 2)
            tr[t] = dict(nisar=nis, gnss=gn, diff=round(nis - gn, 2), tol=4.0)
        feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[lo, la]), properties=dict(
            station=s, source="MOCK", t_end="2020", dist_km=round(C.haversine_km(site["lat"], site["lon"], la, lo), 1),
            tracks=tr, agree=agree, nisar_up=round(rng.uniform(-2, 2), 2), gnss_up=None,
            reason="MOCK · agrees within tolerance" if agree else
                   "MOCK · disagrees: check the monument (rooftop mast?) before blaming the radar")))
    C.save_json(out / "stations.geojson", dict(type="FeatureCollection", features=feats))

    checks = [
        dict(id="sign-129A", status="pass", title="Salt zones sink on track 129A (MOCK)", detail="invented", value=-8.0),
        dict(id="sign-094D", status="fail", title="Salt zones sink on track 094D (MOCK)", detail="invented", value=3.0),
        dict(id="tie-129A", status="warn", title="Model tie on track 129A (MOCK)", detail="invented", value=12.0),
        dict(id="gaps-129A", status="warn", title="Chain gaps, 129A (MOCK)", detail="no pair spans 2026-01-18 → 2026-06-23",
             value=None),
        dict(id="pairs-129A", status="info", title="Closure, 12- vs 24-day pairs (MOCK)", detail="no triplets", value=None),
    ]
    C.save_json(out / "checks.json", checks)
    icon = {"pass": "✔", "warn": "!", "fail": "✘", "info": "·"}
    (out / "checks.md").write_text("# Checks · MOCK (invented)\n\n" + "\n".join(
        f"- {icon[c['status']]} **{c['title']}**: {c['detail']}" for c in checks) + "\n", encoding="utf-8")
    C.save_json(out / "calib.json", dict(model="MOCK", tracks=[
        dict(track=t, direction=g["direction"], method="offset", offset_mm_yr=round(rng.uniform(-9, -5), 2),
             slope_east_mm_yr_per_10km=0.0, slope_north_mm_yr_per_10km=0.0, n_tie_pixels=0,
             residual_std_mm_yr=None, residual_mad_mm_yr=None, model_los_mean_mm_yr=None, swap_delta_mm_yr=None)
        for t, g in LOS.items()]))

    C.save_json(out / "manifest.json", dict(
        site=SITE, name="Ocnele Mari · MOCK (invented values)",
        story="Invented values to build the page on. Simulated, not data.",
        synthetic=True, note="mock_products.py: every number is made up",
        built=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        bounds=F["bounds"], center=[site["lat"], site["lon"]],
        view=dict(site["view"], min_zoom=6, context="romania-blurred"),
        layers=layers, frames=frames,
        checks={k: sum(c["status"] == k for c in checks) for k in ("pass", "warn", "fail", "info")},
        credits="MOCK: no data. Real credits come from export.py (CITATIONS.md)."))

    idx = root / "index.json"
    sites = C.load_json(idx) if idx.exists() else []
    sites = [s for s in sites if s.get("site") != SITE] + [dict(site=SITE, name="Ocnele Mari · MOCK", synthetic=True)]
    C.save_json(idx, sorted(sites, key=lambda s: (s["synthetic"], s["site"])))
    n_frames = sum(len(f["dates"]) for f in frames.values())
    print(f"{out}: {len(layers)} layers, {n_frames} frames, {len(pts)} series points, {len(feats)} stations · ALL INVENTED")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=pathlib.Path, default=C.PRODUCTS, help="products folder (default: products/)")
    ap.add_argument("--size", type=int, default=200, help="overlay size in pixels")
    a = ap.parse_args()
    build(a.out, a.size)


if __name__ == "__main__":
    main()
