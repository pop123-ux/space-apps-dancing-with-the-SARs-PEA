# Owner: 02 · NISAR data (Alexandru, Eric)
"""Exploration only (never imported). Independent check of one NISAR L2 GUNW pair over the Ocnele Mari window.

    python notebooks/02/verify_nisar_pair.py URL_OR_PATH [--size BYTES]

Reads only the metadata and the 50 x 50 km window (about 70 MB of a 2.4 GB file) through HTTP range requests, or
from a local file. Needs h5py, numpy, pyproj, requests. Prints the product identity, the grid and window, the mask
breakdown (decimal code in bits 0 to 7, anomaly flags in bits 8 to 23, bit 24 = ionosphere interpolated), connected
components, the kept fraction (valid, no anomaly, largest component, coherence >= MIN_COH), the ionosphere screen's
spread, and the look vector and incidence at the site. Used on 14 Nov 2026 to check 04's first-pair report
(logs/04-geodesist.md, section 1); results in docs/data.md.
"""
import argparse
import io

import numpy as np

LAT, LON, HALF_M, MIN_COH = 45.088, 24.290, 25000, 0.35   # as common.SITES['ocnele_mari'] and common.MIN_COH


class RangeFile(io.RawIOBase):
    """Read-only file over HTTP range requests, cached in 1 MiB blocks."""
    B = 1 << 20

    def __init__(self, url, size):
        import requests
        self.url, self.size, self.pos, self.cache, self.fetched = url, size, 0, {}, 0
        self.s = requests.Session()

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def _block(self, k):
        if k not in self.cache:
            a = k * self.B
            b = min(a + self.B, self.size) - 1
            for t in range(5):
                try:
                    r = self.s.get(self.url, headers={'Range': f'bytes={a}-{b}'}, timeout=120)
                    r.raise_for_status()
                    break
                except Exception:
                    if t == 4:
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
            p = self.pos + len(out); k = p // self.B; o = p - k * self.B
            out += self._block(k)[o:o + n - len(out)]
        buf[:n] = out
        self.pos += n
        return n


def main():
    import h5py
    from pyproj import Transformer
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('src')
    ap.add_argument('--size', type=int, help='file size in bytes (HTTP only; read from Content-Range if omitted)')
    a = ap.parse_args()
    rf = None
    if a.src.startswith('http'):
        size = a.size
        if not size:
            import requests
            size = int(requests.get(a.src, headers={'Range': 'bytes=0-0'}, timeout=60).headers['Content-Range'].split('/')[-1])
        rf = RangeFile(a.src, size)
        f = h5py.File(io.BufferedReader(rf, 1 << 20), 'r')
    else:
        f = h5py.File(a.src, 'r')
    idn = f['science/LSAR/identification']
    for k in ('productType', 'productLevel', 'productVersion', 'productSpecificationVersion', 'trackNumber', 'frameNumber',
              'orbitPassDirection', 'lookDirection', 'referenceZeroDopplerStartTime', 'secondaryZeroDopplerStartTime'):
        v = idn[k][()]
        print(f'{k}: {v.decode() if isinstance(v, bytes) else v}')
    g = f['science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram']
    x, y = g['xCoordinates'][()], g['yCoordinates'][()]
    epsg = int(g['projection'][()])
    E, N = Transformer.from_crs(4326, epsg, always_xy=True).transform(LON, LAT)
    c0, c1 = int(np.searchsorted(x, E - HALF_M)), int(np.searchsorted(x, E + HALF_M))
    r0, r1 = int(np.searchsorted(-y, -(N + HALF_M))), int(np.searchsorted(-y, -(N - HALF_M)))
    dx = x[1] - x[0]
    print(f'grid EPSG:{epsg}, {dx:.0f} m, {len(x)} x {len(y)}; window rows {r0}:{r1}, cols {c0}:{c1} '
          f'({r1 - r0} x {c1 - c0} px; pixel-edge corner x {x[c0] - dx / 2:.0f}, y {y[r0] + dx / 2:.0f})')
    sl = np.s_[r0:r1, c0:c1]
    mk = g['mask'][sl].astype(np.uint32)
    ph, coh = g['HH/unwrappedPhase'][sl], g['HH/coherenceMagnitude'][sl]
    cc, ion = g['HH/connectedComponents'][sl], g['HH/ionospherePhaseScreen'][sl]
    print(f"mask: {g['mask'].dtype}, chunks {g['mask'].chunks}")
    code, anom, b24 = mk & 0xFF, (mk >> 8) & 0xFFFF, (mk >> 24) & 1
    valid = code != 255
    codes = {int(k): round(v / code.size, 4) for k, v in zip(*np.unique(code, return_counts=True))}
    print(f'mask codes (fraction of window): {codes}; land in both subswaths (code < 100): '
          f'{sum(v for k, v in codes.items() if 0 < k < 100):.3f}')
    print(f'anomaly flags: {float((anom > 0)[valid].mean()):.4f}; bit 24: {float(b24[valid].mean()):.4f}')
    comps, n = np.unique(cc[(cc != 65535) & (cc != 0)], return_counts=True)
    print(f'connected components: {dict(zip(comps.tolist(), n.tolist()))}')
    keep = valid & (anom == 0) & (cc == comps[np.argmax(n)]) & (coh >= MIN_COH) & np.isfinite(ph)
    print(f'kept: {float(keep.mean()):.4f}; ionosphere screen filled {float(np.isfinite(ion).mean()):.4f}, '
          f'sigma {float(np.nanstd(ion[keep])):.3f} rad')
    rg = f['science/LSAR/GUNW/metadata/radarGrid']
    hz = rg['heightAboveEllipsoid'][()]
    k = int(np.argmin(abs(hz - 500)))
    i = int(np.argmin(abs(rg['yCoordinates'][()] - N))); j = int(np.argmin(abs(rg['xCoordinates'][()] - E)))
    le, ln = float(rg['losUnitVectorX'][k, i, j]), float(rg['losUnitVectorY'][k, i, j])
    lu = float(np.sqrt(1 - le ** 2 - ln ** 2))
    print(f'look vector at the site, {hz[k]:.0f} m (target to sensor): e {le:+.3f}, n {ln:+.3f}, u {lu:+.3f}; '
          f"incidence {float(rg['incidenceAngle'][k, i, j]):.3f} deg (acos u {np.degrees(np.arccos(lu)):.3f})")
    wl = 299792458 / f['science/LSAR/GUNW/grids/frequencyA/centerFrequency'][()]
    print(f'wavelength {float(wl):.5f} m')
    if rf:
        print(f'fetched {rf.fetched / 1e6:.0f} MB')


if __name__ == '__main__':
    main()
