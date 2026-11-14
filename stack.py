"""03 · InSAR analyst — pairs → displacement time series and rate ± σ, per track.

Owner: 03 · InSAR analyst (Alexandru & Eric). Status: STUB (interfaces only).

    python stack.py ocnele_mari            # every fetched track
    python stack.py ocnele_mari --track 129A

Reads data/work/<site>/<track>/ from fetch.py (meta.json, <ref>_<sec>.npz, dem.npz).
Writes data/work/<site>/<track>/ts.npz. This is the DRAFT hand-off to 04, 05 and 06; agree any change with them:
    dates (str), cum (date, y, x) mm towards the satellite, vel / vel_sig (mm/yr), annual_amp (mm, only ≥ 1.5 years),
    rate12 / rate24 (closure triplets), n_triplets, coh_mean, valid_share, gaps (str), n_pairs, pair_days,
    tropo_mm_per_100m

Method is OPEN (decision O-05): MintPy (prep_nisar + smallbaselineApp, as the deck proposes) or our own small-baseline
inversion (as the advisor's rehearsal did). Either way the hand-off above is what downstream reads.

Starting points (advisor rehearsal + our own earlier studies; see docs/science-notes.md):
1. mm = PHASE_SIGN · phase · λ/4π. The sign is checked (validate.py check 1), not assumed.
2. Remove the elevation-correlated troposphere per pair (slope against the DEM on stable ground). Without it 094D showed
   −8.6 mm/yr per 100 m. Then reference each pair to stable ground (outside the zones + C.EXCLUDE_KM).
3. Small-baseline inversion: pairs → displacement at every date. Dates no pair connects form separate groups.
4. Rate = straight line THROUGH THE DATES, one offset per group. Never fit the line to the pairs: pairs share dates, so
   one date's atmosphere counts many times (synthetic test: 14.6 mm/yr error instead of 2.8).
5. No annual term under C.ANNUAL_TERM_MIN_YEARS (a free annual term moved a synthetic bowl from −105 to −130 mm/yr).
6. σ assumes independent dates: report it as a lower bound.
"""
from __future__ import annotations

import argparse

import common as C

PHASE_SIGN = -1   # DRAFT: LOS mm (towards satellite) = PHASE_SIGN · phase · λ/4π. NOT confirmed on real data yet.


def load_pairs(site: str, track: str):
    """→ (meta, pairs [(ref, sec)], phase cube, coherence cube, dem or None) for one track."""
    raise C.todo("03", "load the pair files written by fetch.py")


def to_mm_and_clean(site: str, track: str, data):
    """Phase → LOS mm; mask low coherence (C.MIN_COH); remove the elevation slope; reference to stable ground."""
    raise C.todo("03", "phase → mm, coherence mask, troposphere slope, stable-ground reference")


def invert(pairs, dates, data):
    """Small-baseline inversion: pairs → cumulative displacement per date (+ group labels across gaps)."""
    raise C.todo("03", "small-baseline inversion (or MintPy, decision O-05)")


def fit_rate(dates, cum, groups):
    """Line through the dates with one offset per group → vel, vel_sig (lower bound), annual_amp if span ≥ 1.5 years."""
    raise C.todo("03", "rate through the dates, offsets per group, σ")


def closure(pairs, dates, data):
    """Triplets (two 12-day pairs + the 24-day pair over the same dates) → rate12, rate24, n_triplets.

    Ocnele Mari's GUNW stack has 0 triplets: either GSLC pairs (decision O-07) or report 'not tested'.
    """
    raise C.todo("03", "triplet closure for the short-pair bias")


def run(site: str, track: str) -> None:
    meta, pairs, data = load_pairs(site, track)[:3]
    data = to_mm_and_clean(site, track, data)
    dates, cum, groups = invert(pairs, None, data)
    fit_rate(dates, cum, groups)
    closure(pairs, dates, data)
    raise C.todo("03", f"write data/work/{site}/{track}/ts.npz and print one summary line")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--track", help="only this track")
    a = ap.parse_args()
    trs = [a.track] if a.track else C.tracks(a.site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{a.site}/: run fetch.py first")
    for tr in trs:
        run(a.site, tr)


if __name__ == "__main__":
    C.run_cli(main)
