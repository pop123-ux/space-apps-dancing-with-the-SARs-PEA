# Owner: 06 · App developer (Darius)
"""06 · App developer: write an INVENTED products/mock/ in the contract's shape, so the page can be built right away.

Status: WORKS. Standard library only (no numpy, no Pillow).

    python mock_products.py                        # → products/mock/ and an entry in products/index.json
    python mock_products.py --out /tmp/products    # anywhere else (tests/test_skeleton.py does this)
    python mock_products.py --size 400             # bigger overlays (default 200 px)

Every value is made up: four small bowls at the draft salt zones, some smooth "atmosphere", the outer reference band
as a control point, and two station pins (one agreeing, one not). Every file says synthetic: true, so the page must show
the "simulated, not data" banner. Both satellites are written (D-004), so the satellite switch can be built now:
- NISAR on its real acquisition dates over Ocnele Mari (CMR, 14 Nov 2026), with the real 18 Jan to 23 Jun 2026 gap;
- Sentinel-1 on the real fit dates in sentinel1/analysis/summary.json (029A and 007D, 6 Jul to 5 Oct 2026).
When the file contracts in docs/build-spec.md change, change this file too.
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
_S1A = ["2026-07-07", "2026-07-13", "2026-07-19", "2026-07-25", "2026-07-31", "2026-08-06", "2026-08-12", "2026-08-18",
        "2026-08-24", "2026-08-30", "2026-09-05", "2026-09-11", "2026-09-17", "2026-09-23", "2026-09-29", "2026-10-05"]
_S1D = ["2026-07-06", "2026-07-12", "2026-07-18", "2026-07-24", "2026-07-30", "2026-08-05", "2026-08-11", "2026-08-17",
        "2026-08-23", "2026-08-29", "2026-09-04", "2026-09-10", "2026-09-16", "2026-09-22", "2026-09-28", "2026-10-04"]
# sensor → track → real dates, gaps, and an invented line-of-sight geometry (target-to-sensor east and up components).
# NISAR looks left and Sentinel-1 looks right, so their ascending tracks see east motion with opposite signs.
TRACKS = {
    "nisar": {
        "129A": dict(dates=["2025-11-07", "2025-12-01", "2025-12-13", "2025-12-25", "2026-01-18", "2026-06-23",
                            "2026-07-05", "2026-07-17", "2026-08-10", "2026-08-22", "2026-09-03", "2026-09-15",
                            "2026-09-27", "2026-10-09", "2026-10-21"],
                     gaps=[["2026-01-18", "2026-06-23"]], e=0.62, u=0.77),
        "094D": dict(dates=["2026-06-20", "2026-07-02", "2026-07-14", "2026-07-26", "2026-08-19", "2026-08-31",
                            "2026-09-12", "2026-09-24", "2026-10-06", "2026-10-18"], gaps=[], e=-0.60, u=0.78),
    },
    "s1": {
        "029A": dict(dates=_S1A, gaps=[], e=-0.61, u=0.77),
        "007D": dict(dates=_S1D, gaps=[], e=0.60, u=0.78),
    },
}
BOWL_MM_YR = (-18.0, -10.0, -14.0, -6.0)   # invented, one per draft zone
CONTROL = dict(id="outer_control", label="Outer reference band (6.5 to 8 km) · MOCK", kind="control",
               lat=45.0838, lon=24.2860 + 7.2 / 78.6)   # a point in the band, for the chart; invented


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
    sensors = {}

    for sn, tracks in TRACKS.items():
        meta = C.SENSORS[sn]
        layers, frames = [], {}

        def layer(id_, label, field, vmax, track=None, experimental=False):
            png = f"{sn}/{id_}.png"
            overlay(out / png, field, vmax)
            layers.append(dict(id=id_, label=f"{label} · MOCK", png=png, units="mm/yr", vmin=-vmax, vmax=vmax,
                               track=track, experimental=experimental))

        for t, g in tracks.items():
            lr = [[g["u"] * u + g["e"] * e for u, e in zip(ru, re)] for ru, re in zip(F["up"], F["east"])]
            layer(f"los_{t}", f"{meta['label']} {t}: line-of-sight rate (+ = towards the satellite)", lr, 20, track=t)
            pngs = []
            for k, d in enumerate(g["dates"]):
                yr = years_since(g["dates"][0], d, g["gaps"])
                amp = 0.0 if k == 0 else rng.uniform(-4, 4)   # invented atmosphere of the day, mm
                cum = [[v * yr + amp * a for v, a in zip(rv, ra)] for rv, ra in zip(lr, F["noise"])]
                png = f"{sn}/frames/{t}/{d}.png"
                overlay(out / png, cum, 20)
                pngs.append(png)
            frames[t] = dict(dates=g["dates"], pngs=pngs, vmin=-20, vmax=20, units="mm since first date",
                             direction=meta["tracks"][t], gaps=g["gaps"])
        layer("up", f"{meta['label']}: vertical rate (− = sinking), experimental", F["up"], 20, experimental=True)
        layer("east", f"{meta['label']}: east–west rate (+ = east), experimental", F["east"], 10, experimental=True)
        sensors[sn] = dict({k: meta[k] for k in ("label", "agency", "band", "wavelength_cm", "status", "reference",
                                                    "credit")}, layers=layers, frames=frames)

    # series at the zones, the outer reference band and the stations, keyed "<sensor>:<track>"
    pts = [dict(id=z["id"], label=f"Salt zone {z['id']} · MOCK", kind="zone", lat=z["lat"], lon=z["lon"])
           for z in site["zones"]] + [dict(CONTROL)]
    stations = {s: C.PUBLISHED[s][:2] for s in ("VLC2", "HORE")}
    pts += [dict(id=s, label=f"{s} · MOCK", kind="station", lat=la, lon=lo) for s, (la, lo) in stations.items()]
    for p in pts:
        up, east = F["bowls"](p["lat"], p["lon"])
        p["up"] = {sn: round(up + rng.uniform(-1.5, 1.5), 1) for sn in TRACKS}
        p["series"] = {}
        for sn, tracks in TRACKS.items():
            for t, g in tracks.items():
                rate = g["u"] * up + g["e"] * east
                mm = [round(rate * years_since(g["dates"][0], d, g["gaps"]) + (0 if k == 0 else rng.uniform(-3, 3)), 1)
                      for k, d in enumerate(g["dates"])]
                p["series"][f"{sn}:{t}"] = dict(dates=g["dates"], mm=mm, rate=round(rate, 1), n_pixels=rng.randint(2, 60))
    C.save_json(out / "series.json", pts)

    feats = []
    for (s, (la, lo)), agree in zip(stations.items(), (True, False)):
        tr = {}
        for sn, tracks in TRACKS.items():
            for t in tracks:
                v = round(rng.uniform(-3, 3), 2)
                gn = round(v + (rng.uniform(-1, 1) if agree else 9.5), 2)
                tr[f"{sn}:{t}"] = dict(radar=v, gnss=gn, diff=round(v - gn, 2), tol=4.0)
        feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[lo, la]), properties=dict(
            station=s, source="MOCK", t_end="2020", dist_km=round(C.haversine_km(site["lat"], site["lon"], la, lo), 1),
            tracks=tr, agree=agree, gnss_up=None,
            reason="MOCK · agrees within tolerance" if agree else
                   "MOCK · disagrees: check the monument (rooftop mast?) before blaming the radar")))
    C.save_json(out / "stations.geojson", dict(type="FeatureCollection", features=feats))

    checks = [
        dict(id="sign-nisar-129A", status="pass", title="Salt zones sink, NISAR 129A (MOCK)", detail="invented", value=-8.0),
        dict(id="sign-nisar-094D", status="fail", title="Salt zones sink, NISAR 094D (MOCK)", detail="invented", value=3.0),
        dict(id="agree-zone4", status="warn", title="NISAR and Sentinel-1 agree in zone 4, common window (MOCK)",
             detail="invented", value=4.2),
        dict(id="gaps-nisar-129A", status="warn", title="Chain gaps, NISAR 129A (MOCK)",
             detail="no pair spans 2026-01-18 → 2026-06-23", value=None),
        dict(id="pairs-nisar-129A", status="info", title="Closure, 12- vs 24-day pairs (MOCK)", detail="no triplets",
             value=None),
    ]
    C.save_json(out / "checks.json", checks)
    icon = {"pass": "✔", "warn": "!", "fail": "✘", "info": "·"}
    (out / "checks.md").write_text("# Checks · MOCK (invented)\n\n" + "\n".join(
        f"- {icon[c['status']]} **{c['title']}**: {c['detail']}" for c in checks) + "\n", encoding="utf-8")
    C.save_json(out / "calib.json", dict(model="MOCK", tracks=[
        dict(sensor=sn, track=t, direction=C.SENSORS[sn]["tracks"][t], method="offset",
             offset_mm_yr=round(rng.uniform(-9, -5), 2), slope_east_mm_yr_per_10km=0.0, slope_north_mm_yr_per_10km=0.0,
             n_tie_pixels=0, residual_std_mm_yr=None, residual_mad_mm_yr=None, model_los_mean_mm_yr=None,
             swap_delta_mm_yr=None)
        for sn, tracks in TRACKS.items() for t in tracks]))

    C.save_json(out / "manifest.json", dict(
        site=SITE, name="Ocnele Mari · MOCK (invented values)",
        story="Invented values to build the page on. Simulated, not data.",
        synthetic=True, note="mock_products.py: every number is made up",
        built=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        bounds=F["bounds"], center=[site["lat"], site["lon"]],
        view=dict(site["view"], min_zoom=6, context="romania-blurred"),
        sensors=sensors, views=list(C.VIEWS), common_window=list(C.COMMON_WINDOW),
        default=dict(sat="nisar", view="change", track="129A"),
        checks={k: sum(c["status"] == k for c in checks) for k in ("pass", "warn", "fail", "info")},
        credits="MOCK: no data. Real credits come from export.py (CITATIONS.md)."))

    idx = root / "index.json"
    sites = C.load_json(idx) if idx.exists() else []
    sites = [s for s in sites if s.get("site") != SITE] + [dict(site=SITE, name="Ocnele Mari · MOCK", synthetic=True)]
    C.save_json(idx, sorted(sites, key=lambda s: (s["synthetic"], s["site"])))
    n_layers = sum(len(v["layers"]) for v in sensors.values())
    n_frames = sum(len(f["dates"]) for v in sensors.values() for f in v["frames"].values())
    print(f"{out}: {', '.join(sensors)} · {n_layers} layers, {n_frames} frames, {len(pts)} series points, "
          f"{len(feats)} stations · ALL INVENTED")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=pathlib.Path, default=C.PRODUCTS, help="products folder (default: products/)")
    ap.add_argument("--size", type=int, default=200, help="overlay size in pixels")
    a = ap.parse_args()
    build(a.out, a.size)


if __name__ == "__main__":
    main()
