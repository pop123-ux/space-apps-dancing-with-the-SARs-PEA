# Owner: 02 · NISAR data (Alexandru, Eric)
"""02 · NISAR data: find the GUNW pairs over the site and stream only the site window out of each ~2.4 GB file.

Status: WORKING on real data (14 Nov 2026): search, window streaming, geometry and DEM. The synthetic stack is still a stub.

    python fetch.py ocnele_mari --list           # search only: pairs per track, pair lengths
    python fetch.py ocnele_mari                  # stream every pair's window (Earthdata token, see below)
    python fetch.py ocnele_mari --track 094D     # one track

Earthdata: set EARTHDATA_TOKEN, or run where a network proxy injects the token for nisar.asf.earthdatacloud.nasa.gov
(this repo's cloud sessions do; then nothing needs setting). The token is never printed or stored.

Writes data/work/<site>/<track>/ (never committed). The hand-off to 03:
    meta.json            window grid: epsg, x0, y0 (pixel CENTRES), dx, dy, nx, ny; wavelength (m), direction, look,
                         polarization, synthetic, height_m, granules {pair: granule}
    geom.npz             line-of-sight unit vectors los_e, los_n, los_u (target → sensor, ENU) on the window grid,
                         from the radarGrid cube at C.SITES[site]["height_m"] (linear in height), and incidence (deg)
    <ref>_<sec>.npz      one per pair (YYYYMMDD_YYYYMMDD): phase (rad, ionosphere removed, NaN = masked), coh,
                         and QA fields: iono_used, iono_std, valid_share, main_share, iono_interp, collection
    dem.npz              elevation (m, Copernicus GLO-30, EGM2008) on the window grid, for the troposphere step

Masking (docs/data.md): mask cast to uint32; code = mk & 0xFF must be 1 to 99 (land, imaged by both subswaths; 0 =
no subswath, >= 100 = water, 255 = fill); anomaly flags (bits 8 to 23) must be 0; bit 24 (ionosphere interpolated)
keeps the pixel and is counted. Only the largest connected component is kept. Coherence is kept, not thresholded:
stack.py applies C.MIN_COH. The ionospherePhaseScreen is subtracted where it is finite.

Known going in (CMR, 14 Nov 2026; advisor rehearsal, 12 Nov 2026):
- 22 pairs over Ocnele Mari: 129A (13 pairs, 7 Nov 2025 → 21 Oct 2026, nothing 18 Jan → 23 Jun 2026) and 094D (9 pairs,
  20 Jun → 18 Oct 2026). Collections NISAR_L2_GUNW_BETA_V1 + NISAR_L2_GUNW_PROVISIONAL_V1; keep the newest processing.
- HTTP range reads: about 55 to 70 MB per pair for the 50 km window.
- Products are beta/provisional ("not intended for scientific research").
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import common as C

GUNW_GRID = "science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram"   # checked on spec 1.5.0 (14 Nov 2026)
RADAR_GRID = "science/LSAR/GUNW/metadata/radarGrid"
COLLECTIONS = ["NISAR_L2_GUNW_BETA_V1", "NISAR_L2_GUNW_PROVISIONAL_V1", "NISAR_L2_GUNW_V1"]
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
NAME = re.compile(r"NISAR_L2_(?P<lvl>\w\w)_GUNW_\d{3}_(?P<track>\d{3})_(?P<dir>[AD])_\d{3}_\d{3}_\d{4}_\w\w_"
                  r"(?P<ref>\d{8})T\d{6}_\d{8}T\d{6}_(?P<sec>\d{8})T\d{6}_\d{8}T\d{6}_(?P<crid>\w\d+)_\w_\w_\w_(?P<ctr>\d{3})")
BLOCK = 1 << 19        # range-read block, bytes


# ------------------------------------------------------------------------------------------------------------ search
def search(site: str) -> dict:
    """ASF/CMR search over the site → {(track, ref, sec): (granule, url, collection)}, newest processing of each pair.

    Track as '129A' / '094D', dates as 'YYYYMMDD'. Searching needs no login.
    """
    import requests
    s = C.SITES[site]
    found = {}
    for coll in COLLECTIONS:
        page = 1
        while True:
            r = requests.get(CMR, params=dict(short_name=coll, point=f"{s['lon']},{s['lat']}", page_size=200,
                                              page_num=page, temporal=f"{C.NISAR_START}T00:00:00Z,"), timeout=60)
            r.raise_for_status()
            entries = r.json()["feed"]["entry"]
            for e in entries:
                m = NAME.search(e["title"])
                if not m:
                    continue
                url = next((l["href"] for l in e.get("links", []) if l["href"].endswith(".h5")
                            and l["href"].startswith("https://") and "s3credentials" not in l["href"]), None)
                if not url:
                    continue
                key = (m["track"] + m["dir"], m["ref"], m["sec"])
                rank = (COLLECTIONS.index(coll), m["crid"], m["ctr"])
                if key not in found or rank > found[key][3]:
                    found[key] = (e["title"], url, coll, rank)
            if len(entries) < 200:
                break
            page += 1
    return {k: v[:3] for k, v in sorted(found.items())}


# ---------------------------------------------------------------------------------------------------- range reading
class RangeFile(io.RawIOBase):
    """Read-only file over HTTP range requests, cached in BLOCK-sized pieces; counts the bytes fetched.

    The ASF URL answers with a redirect to a signed download link; it is resolved once and again if it expires.
    """

    def __init__(self, url: str, token: str | None):
        import requests
        self.url, self.pos, self.cache, self.fetched = url, 0, {}, 0
        self.s = requests.Session()
        self.auth = {"Authorization": f"Bearer {token}"} if token else {}
        self._resolve()

    def _resolve(self):
        r = self.s.get(self.url, headers={**self.auth, "Range": "bytes=0-0"}, allow_redirects=False, timeout=60)
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers["Location"]
            if "urs.earthdata.nasa.gov" in loc:
                raise SystemExit("Earthdata login needed: set EARTHDATA_TOKEN or the proxy credential")
            self.signed = loc
            r = self.s.get(loc, headers={"Range": "bytes=0-0"}, timeout=60)
        else:
            self.signed = self.url
        r.raise_for_status()
        self.size = int(r.headers["Content-Range"].split("/")[-1])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def _block(self, k):
        if k not in self.cache:
            a = k * BLOCK
            b = min(a + BLOCK, self.size) - 1
            for t in range(6):
                try:
                    r = self.s.get(self.signed, headers={"Range": f"bytes={a}-{b}"}, timeout=120)
                    if r.status_code in (401, 403):
                        self._resolve()
                        continue
                    r.raise_for_status()
                    break
                except Exception:
                    if t == 5:
                        raise
            self.cache[k] = r.content
            self.fetched += len(r.content)
        return self.cache[k]

    def readinto(self, buf):
        n = min(len(buf), self.size - self.pos)
        if n <= 0:
            return 0
        out = bytearray()
        while len(out) < n:
            p = self.pos + len(out)
            k = p // BLOCK
            o = p - k * BLOCK
            out += self._block(k)[o:o + n - len(out)]
        buf[:n] = out
        self.pos += n
        return n


def open_h5(url: str, token: str | None):
    import h5py
    rf = RangeFile(url, token)
    return h5py.File(io.BufferedReader(rf, BLOCK), "r"), rf


# ------------------------------------------------------------------------------------------------------- the window
def window_grid(site: str, h5) -> dict:
    """Window grid snapped to the product's lattice: pixel centres within ±half_km of the site centre."""
    import numpy as np
    s = C.SITES[site]
    g = h5[GUNW_GRID]
    x, y = g["xCoordinates"][()], g["yCoordinates"][()]
    epsg = int(g["projection"][()])
    E, N = C.to_xy(epsg, s["lon"], s["lat"])
    half = s["half_km"] * 1000
    c0, c1 = int(np.searchsorted(x, E - half)), int(np.searchsorted(x, E + half))
    r0, r1 = int(np.searchsorted(-y, -(N + half))), int(np.searchsorted(-y, -(N - half)))
    return dict(epsg=epsg, x0=float(x[c0]), y0=float(y[r0]), dx=float(x[1] - x[0]), dy=float(y[1] - y[0]),
                nx=c1 - c0, ny=r1 - r0)


def slices(meta: dict, h5):
    """Row and column slices of meta's window in this product; stop if the product sits on another lattice."""
    import numpy as np
    g = h5[GUNW_GRID]
    x, y = g["xCoordinates"][()], g["yCoordinates"][()]
    if int(g["projection"][()]) != meta["epsg"] or abs((x[1] - x[0]) - meta["dx"]) > 1e-6:
        raise SystemExit(f"grid changed (EPSG or spacing): stop, 02 re-fixes the window")
    c0 = int(np.argmin(abs(x - meta["x0"])))
    r0 = int(np.argmin(abs(y - meta["y0"])))
    if abs(x[c0] - meta["x0"]) > 1 or abs(y[r0] - meta["y0"]) > 1:
        raise SystemExit("product lattice is offset from the window grid: stop, 02 re-fixes the window")
    if c0 + meta["nx"] > len(x) or r0 + meta["ny"] > len(y):
        raise SystemExit("window runs off this product's frame")
    return np.s_[r0:r0 + meta["ny"], c0:c0 + meta["nx"]]


def read_pair(site: str, track: str, ref: str, sec: str, url: str, token: str | None, collection: str = "") -> int:
    """Stream the window of one pair over HTTP range requests and write <ref>_<sec>.npz. Returns bytes read.

    The first pair of a track fixes the window grid (meta.json, snapped to the product's 80 m lattice) and writes
    geom.npz; later pairs must land on the same grid (stop if ASF reprocessed onto another one).
    """
    import numpy as np
    tdir = C.site_dir(site, track)
    out = tdir / f"{ref}_{sec}.npz"
    if out.exists():
        return 0
    h5, rf = open_h5(url, token)
    mpath = tdir / "meta.json"
    if mpath.exists():
        meta = C.load_json(mpath)
    else:
        idn = h5["science/LSAR/identification"]
        meta = window_grid(site, h5)
        f0 = float(h5["science/LSAR/GUNW/grids/frequencyA/centerFrequency"][()])
        meta.update(wavelength=C.LIGHT / f0, direction=idn["orbitPassDirection"][()].decode(),
                    look=idn["lookDirection"][()].decode(), polarization="HH", synthetic=False,
                    height_m=C.SITES[site]["height_m"], centre="x0, y0 are pixel centres", granules={})
        write_geometry(h5, meta, tdir)
    sl = slices(meta, h5)
    g = h5[GUNW_GRID]
    ph = g["HH/unwrappedPhase"][sl].astype("f4")
    coh = g["HH/coherenceMagnitude"][sl].astype("f4")
    cc = g["HH/connectedComponents"][sl]
    mk = g["mask"][sl].astype(np.uint32)
    ion = g["HH/ionospherePhaseScreen"][sl].astype("f4") if "ionospherePhaseScreen" in g["HH"] else None
    code, anom, b24 = mk & 0xFF, (mk >> 8) & 0xFFFF, (mk >> 24) & 1
    valid = (code >= 1) & (code <= 99) & (anom == 0) & np.isfinite(ph)
    ccv = cc[valid & (cc != 0) & (cc != 65535)]
    main = np.zeros_like(valid)
    if ccv.size:
        comps, n = np.unique(ccv, return_counts=True)
        main = valid & (cc == comps[np.argmax(n)])
    iono_used = ion is not None and bool(np.isfinite(ion[main]).mean() > 0.99) if main.any() else False
    if iono_used:
        ph = ph - np.where(np.isfinite(ion), ion, np.nan)
    phase = np.where(main, ph, np.nan).astype("f4")
    qa = dict(iono_used=iono_used, iono_std=float(np.nanstd(ion[main])) if iono_used else np.nan,
              valid_share=float(valid.mean()), main_share=float(main.mean()),
              iono_interp=float(b24[main].mean()) if main.any() else np.nan, collection=collection)
    np.savez_compressed(out, phase=phase, coh=coh, **qa)
    meta["granules"][f"{ref}_{sec}"] = url.rsplit("/", 1)[-1]
    C.save_json(mpath, meta)
    print(f"{track} {ref}_{sec}: kept {qa['main_share']:.0%}, iono {'σ %.2f rad' % qa['iono_std'] if iono_used else 'not used'}, "
          f"{rf.fetched / 1e6:.0f} MB", flush=True)
    return rf.fetched


def write_geometry(h5, meta: dict, tdir) -> None:
    """LOS unit vectors (target → sensor, ENU) from the radarGrid cube at the site's height → geom.npz."""
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator
    rg = h5[RADAR_GRID]
    hz = rg["heightAboveEllipsoid"][()]
    rx, ry = rg["xCoordinates"][()], rg["yCoordinates"][()]
    X = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
    Y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    k = int(np.searchsorted(hz, meta["height_m"]))
    k0, k1 = max(k - 1, 0), min(k, len(hz) - 1)
    w = 0.0 if k1 == k0 else (meta["height_m"] - hz[k0]) / (hz[k1] - hz[k0])
    yy, xx = np.meshgrid(Y, X, indexing="ij")
    pts = np.stack([yy.ravel(), xx.ravel()], -1)
    out = {}
    for name, key in (("los_e", "losUnitVectorX"), ("los_n", "losUnitVectorY"), ("incidence", "incidenceAngle")):
        cube = rg[key]
        layer = (1 - w) * cube[k0] + w * cube[k1]
        f = RegularGridInterpolator((ry[::-1], rx), layer[::-1], bounds_error=False, fill_value=None)
        out[name] = f(pts).reshape(meta["ny"], meta["nx"]).astype("f4")
    out["los_u"] = np.sqrt(np.clip(1 - out["los_e"] ** 2 - out["los_n"] ** 2, 0, 1)).astype("f4")
    np.savez_compressed(tdir / "geom.npz", **out)


def write_dem(tdir) -> None:
    """Copernicus GLO-30 DEM (open, AWS) averaged onto the window grid → dem.npz."""
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT
    from rasterio.transform import from_origin
    out = tdir / "dem.npz"
    if out.exists():
        return
    meta = C.load_json(tdir / "meta.json")
    X0, Y0 = meta["x0"] - meta["dx"] / 2, meta["y0"] - meta["dy"] / 2
    lon, lat = C.to_lonlat(meta["epsg"], [X0, X0 + meta["nx"] * meta["dx"]] * 2,
                           [Y0, Y0, Y0 + meta["ny"] * meta["dy"], Y0 + meta["ny"] * meta["dy"]])
    import math
    tiles = [(la, lo) for la in range(math.floor(min(lat)), math.floor(max(lat)) + 1)
             for lo in range(math.floor(min(lon)), math.floor(max(lon)) + 1)]
    dem = np.full((meta["ny"], meta["nx"]), np.nan, "f4")
    tr = from_origin(X0, Y0, meta["dx"], -meta["dy"])
    for la, lo in tiles:
        name = f"Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM"
        url = f"https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif"
        with rasterio.open(url) as src, WarpedVRT(src, crs=f"EPSG:{meta['epsg']}", transform=tr, width=meta["nx"],
                                                   height=meta["ny"], resampling=Resampling.average) as vrt:
            a = vrt.read(1, masked=True).filled(np.nan).astype("f4")
        dem = np.where(np.isfinite(a) & (a != 0), a, dem)
    np.savez_compressed(out, dem=dem)
    print(f"{tdir.name}: DEM {np.nanmin(dem):.0f} to {np.nanmax(dem):.0f} m, {np.isfinite(dem).mean():.0%} filled")


CORR_LAYERS = {"tropo_rad": ("hydrostaticTroposphericPhaseScreen", "wetTroposphericPhaseScreen"),
               "set_rad": ("slantRangeSolidEarthTidesPhase",)}


def read_corrections(site: str, track: str, ref: str, sec: str, url: str, token: str | None) -> int:
    """Add NASA's own corrections to <ref>_<sec>.npz: tropo_rad (hydrostatic + wet troposphere phase screen) and
    set_rad (solid-earth tides), each from the product's radarGrid cube, interpolated to every window pixel at its DEM
    height. Units are radians, the interferogram's own convention (stack.py --gunw-corrections subtracts them; the sign
    is checked on stable ground, see notebooks/03/t3_094d_checks.json). The DEM is EGM2008 orthometric and the cube
    heights are ellipsoidal; the geoid (about 40 m here) shifts a whole frame almost uniformly and is ignored."""
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator
    tdir = C.WORK / site / track
    f = tdir / f"{ref}_{sec}.npz"
    z = dict(np.load(f))
    if "tropo_rad" in z:
        return 0
    meta = C.load_json(tdir / "meta.json")
    dem = np.load(tdir / "dem.npz")["dem"]
    h5, rf = open_h5(url, token)
    rg = h5[RADAR_GRID]
    hz, rx, ry = rg["heightAboveEllipsoid"][()], rg["xCoordinates"][()], rg["yCoordinates"][()]
    X = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
    Y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    c0 = max(int(np.searchsorted(rx, X.min())) - 2, 0); c1 = min(int(np.searchsorted(rx, X.max())) + 3, len(rx))
    r0 = max(int(np.searchsorted(-ry, -Y.max())) - 2, 0); r1 = min(int(np.searchsorted(-ry, -Y.min())) + 3, len(ry))
    yy, xx = np.meshgrid(Y, X, indexing="ij")
    h = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    k = np.clip(np.searchsorted(hz, h) - 1, 0, len(hz) - 2)
    w = (h - hz[k]) / (hz[k + 1] - hz[k])
    for name, layers in CORR_LAYERS.items():
        cube = sum(rg[L][:, r0:r1, c0:c1].astype("f8") for L in layers)
        lv = np.empty((len(hz),) + X.shape[:0] + yy.shape)
        for i in range(len(hz)):
            fi = RegularGridInterpolator((ry[r0:r1][::-1], rx[c0:c1]), cube[i][::-1], bounds_error=False, fill_value=None)
            lv[i] = fi(np.stack([yy.ravel(), xx.ravel()], -1)).reshape(yy.shape)
        ii, jj = np.indices(yy.shape)
        z[name] = ((1 - w) * lv[k, ii, jj] + w * lv[k + 1, ii, jj]).astype("f4")
    np.savez_compressed(f, **z)
    print(f"{track} {ref}_{sec}: corrections added (troposphere {np.nanstd(z['tropo_rad']):.2f} rad spread, "
          f"tides {np.nanstd(z['set_rad']):.3f} rad), {rf.fetched / 1e6:.0f} MB", flush=True)
    return rf.fetched


def synthetic(site: str, seed: int = 7) -> None:
    """Offline known-answer stack in exactly the real file shapes: truth.npz + per-track meta/geom/pairs.

    Use the real date pattern (including the January–June gap) so the gap handling is tested too.
    """
    raise C.todo("02", "write a synthetic stack with known up/east, atmosphere, ionosphere and a planted gap")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--list", action="store_true", help="search only")
    ap.add_argument("--synthetic", action="store_true", help="offline known-answer stack")
    ap.add_argument("--track", help="only this track, e.g. 129A")
    ap.add_argument("--workers", type=int, default=4, help="parallel streams (tune on the venue Wi-Fi)")
    ap.add_argument("--corrections", action="store_true",
                    help="add NASA's troposphere and solid-earth-tide screens to pairs already on disk")
    a = ap.parse_args()
    if a.synthetic or C.SITES[a.site].get("synthetic"):
        return synthetic(a.site)
    pairs = search(a.site)
    if a.track:
        pairs = {k: v for k, v in pairs.items() if k[0] == a.track}
    for tr in sorted({k[0] for k in pairs}):
        ks = [k for k in pairs if k[0] == tr]
        from datetime import date
        days = sorted({(date.fromisoformat(f"{q[:4]}-{q[4:6]}-{q[6:]}") - date.fromisoformat(f"{r[:4]}-{r[4:6]}-{r[6:]}")).days
                       for _, r, q in ks})
        print(f"{tr}: {len(ks)} pairs, {ks[0][1]} → {ks[-1][2]}, lengths {days} days")
    if a.list:
        return
    token = os.environ.get("EARTHDATA_TOKEN")            # None: the session proxy injects it
    if a.corrections:
        with ThreadPoolExecutor(a.workers) as ex:
            n = sum(ex.map(lambda k: read_corrections(a.site, *k, pairs[k][1], token), list(pairs)))
        print(f"corrections: {n / 1e6:.0f} MB")
        return
    total = 0
    for tr in sorted({k[0] for k in pairs}):
        ks = [k for k in pairs if k[0] == tr]
        total += read_pair(a.site, *ks[0], pairs[ks[0]][1], token, pairs[ks[0]][2])   # first pair fixes the grid
        with ThreadPoolExecutor(a.workers) as ex:
            total += sum(ex.map(lambda k: read_pair(a.site, *k, pairs[k][1], token, pairs[k][2]), ks[1:]))
        write_dem(C.site_dir(a.site, tr))
    print(f"streamed {total / 1e6:.0f} MB")


if __name__ == "__main__":
    C.run_cli(main)
