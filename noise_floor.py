# Owner: 04 · Geodesist (Matei)
"""04 · Geodesist: how big a motion can the tied NISAR rates show, and when will they show the salt zones?

Status: WORKING on the real tied tracks in data/work/<site>/ (129A: team stream; 094D: rehearsal copy until 02/03 land
theirs). Analysis only: it changes no rate, no tie and no other role's file.

    python noise_floor.py ocnele_mari
    python noise_floor.py ocnele_mari --draws 1000 --until 2029-01-01

Reads per track: meta.json, geom.npz, ts.npz, cal.npz (calibrate.py). Writes products/<site>/noise_floor.json and
products/<site>/noise_floor.png (hand-off to 01, 05 and 06).

What it does:
1. Zone noise floor. Random "fake zones" on the tie pixels (stable ground, outside the salt zones + C.EXCLUDE_KM and away
   from stations), each the size of a real zone. The robust spread (1.4826 · MAD) of their median rates is the noise a
   zone median carries. Three versions: the zone alone, the zone minus a 1 to 3 km ring, and the zone minus the
   6.5 to 8 km band the page's Compare view uses. Real zones get z = rate / σ; |z| ≥ 2 is called significant.
2. Pin noise. The same for the page's "pin" (points within 120 m minus spots about 300 m away, 260 to 340 m here):
   the motion a pin needs before the page may say anything.
3. Up/east check. Zone-level 2 × 2 solve with both tracks (north dropped), and 129A alone assuming no horizontal
   motion. Diagnostic only: the tracks cover different months, and 094D fails the sign check.
4. Detection horizon, a rough estimate. On NASA's interferograms the zone-to-zone spread of cumulative displacement
   grows with the number of pairs, roughly like √(pairs), so the noise is modelled as a random walk ("chain"): the
   per-pair noise is set so that a least-squares rate (one offset per acquisition group) reproduces the measured zone
   σ, and is cross-checked against the spread growth. The rate σ is projected for passes every 12 days after the last
   date, next to an optimistic bound with independent noise per date ("best_case"). It reports the first date a
   steady vertical sink of 10, 19 or 25 mm/yr reaches 2σ.

What it cannot tell you: the projection assumes passes every 12 days with no new gap, the same coherence and
processing, a steady rate and no seasonal term. A seasonal signal or another gap makes the dates later. The cause of
the noise is not the chain of pairs: on 094D raw single-look data (notebooks/04/gslc_chain_vs_network.py, 15 Nov), a
redundant network of 12-, 24- and 36-day pairs was no quieter than a chain (11.7 against 12.5 mm/yr on the same
pixels), while the same data processed from the single-look files was quieter than NASA's interferograms (12.5 against
19.5 mm/yr, same box and ring). More pairs alone will not bring the dates earlier.
"""
from __future__ import annotations

import argparse
import datetime as dt
import warnings

import common as C

RINGS = {"ring_1_3km": (1000.0, 3000.0), "ring_6p5_8km": (6500.0, 8000.0)}
PIN = dict(r_m=120.0, ring=(260.0, 340.0))
SINKS_MM_YR = (10.0, 19.0, 25.0)     # vertical sinks tested: EGMS shows up to about 25 mm/yr (2019 to 2024)
REVISIT_DAYS = 12


def robust_sigma(a):
    import numpy as np
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return float(1.4826 * np.median(np.abs(a - np.median(a)))) if a.size else float("nan")


class Grid:
    """A track's grid with fast disc and ring medians around a point (in the track's UTM metres)."""

    def __init__(self, meta: dict, vel):
        import numpy as np
        self.m, self.v = meta, vel
        self.ny, self.nx = vel.shape

    def ij(self, x, y):
        return int(round((y - self.m["y0"]) / self.m["dy"])), int(round((x - self.m["x0"]) / self.m["dx"]))

    def window(self, x, y, r_out):
        import numpy as np
        i, j = self.ij(x, y)
        k = int(np.ceil(r_out / abs(self.m["dx"]))) + 1
        i0, i1, j0, j1 = i - k, i + k + 1, j - k, j + k + 1
        if i0 < 0 or j0 < 0 or i1 > self.ny or j1 > self.nx:
            return None
        yy = (self.m["y0"] + np.arange(i0, i1) * self.m["dy"])[:, None]
        xx = (self.m["x0"] + np.arange(j0, j1) * self.m["dx"])[None, :]
        return (slice(i0, i1), slice(j0, j1)), np.hypot(xx - x, yy - y)

    def disc_ring(self, x, y, r, ring, arr=None):
        """(median in the disc, pixel count, median in the ring) for arr (default: the rate) or an array stack."""
        import numpy as np
        w = self.window(x, y, ring[1])
        if w is None:
            return float("nan"), 0, float("nan")
        sl, d = w
        a = (self.v if arr is None else arr)[sl] if arr is None or arr.ndim == 2 else arr[(slice(None),) + sl]
        ok = np.isfinite(self.v[sl])
        disc, rg = ok & (d <= r), ok & (d > ring[0]) & (d <= ring[1])
        if disc.sum() < 5 or rg.sum() < 20:
            return float("nan"), int(disc.sum()), float("nan")
        if a.ndim == 2:
            return float(np.median(a[disc])), int(disc.sum()), float(np.median(a[rg]))
        return np.nanmedian(a[:, disc], axis=1), int(disc.sum()), np.nanmedian(a[:, rg], axis=1)


def steps_in_group(group):
    """Pairs between each date and its group's first date, for a single chain of pairs (one pair per new date)."""
    out, seen = [], {}
    for g in group:
        seen[g] = seen.get(g, -1) + 1
        out.append(seen[g])
    return out


def rate_sigma_factor(t, group, chain: bool):
    """Rate σ for unit noise, from a least-squares line with one offset per acquisition group.

    chain=True: each pair adds independent unit noise, so a date's error is the sum of the pairs before it in its
    group (a random walk: Cov(i, j) = min(k_i, k_j) within a group). chain=False: independent unit noise per date."""
    import numpy as np
    t, group = np.asarray(t, float), np.asarray(group)
    groups = sorted(set(group.tolist()))
    A = np.column_stack([t] + [(group == g).astype(float) for g in groups])
    P = np.linalg.inv(A.T @ A) @ A.T
    if chain:
        k = np.asarray(steps_in_group(group.tolist()), float)
        cov = np.where(group[:, None] == group[None, :], np.minimum(k[:, None], k[None, :]), 0.0)
    else:
        cov = np.eye(len(t))
    return float(np.sqrt((P @ cov @ P.T)[0, 0]))


def chain_step_sigma(group, series):
    """Per-pair noise from how fast the zone-to-zone spread of cumulative displacement grows (spread_k ≈ σ·√k)."""
    import numpy as np
    S = np.asarray(series, float)
    k = np.asarray(steps_in_group(list(group)), float)
    est = []
    for i in range(S.shape[1]):
        if k[i] >= 1 and np.isfinite(S[:, i]).sum() >= 30:
            est.append(robust_sigma(S[:, i]) / np.sqrt(k[i]))
    return float(np.median(est)) if est else float("nan")


def track_floor(site: str, track: str, draws: int, until: str, rng) -> dict:
    import numpy as np
    w = C.site_dir(site, track)
    meta = C.load_json(w / "meta.json")
    ts, cal, geom = (np.load(w / f"{f}.npz") for f in ("ts", "cal", "geom"))
    vel, tie, cum = cal["vel_cal"], cal["tie"], cal["cum_cal"]
    G = Grid(meta, vel)
    S = C.SITES[site]
    dates = [str(d) for d in ts["dates"]]
    t = np.asarray(C.years(dates), float)
    group = [int(g) for g in ts["group"]]

    # 1. fake zones on the tie pixels
    ys, xs = np.nonzero(tie & np.isfinite(vel))
    radii = sorted({float(z["r_m"]) for z in S["zones"]})
    fake = {}
    resid = []
    for r in radii:
        vals = {"zone_alone": [], **{k: [] for k in RINGS}}
        for n_try, idx in enumerate(rng.choice(len(ys), size=min(len(ys), draws * 3), replace=False)):
            x = meta["x0"] + xs[idx] * meta["dx"]
            y = meta["y0"] + ys[idx] * meta["dy"]
            row = {}
            for k, ring in RINGS.items():
                md, n, rg = G.disc_ring(x, y, r, ring)
                if n < 10 or not np.isfinite(rg):
                    row = None
                    break
                row[k] = md - rg
                row["zone_alone"] = md
            if row is None:
                continue
            for k in vals:
                vals[k].append(row[k])
            if r == radii[-1] and len(resid) < 600:
                sd, _, sr = G.disc_ring(x, y, r, RINGS["ring_1_3km"], arr=cum)
                resid.append(np.asarray(sd) - np.asarray(sr))
            if len(vals["zone_alone"]) >= draws:
                break
        fake[f"r{int(r)}m"] = dict(n_draws=len(vals["zone_alone"]),
                                   **{f"sigma_{k}_mm_yr": round(robust_sigma(v), 2) for k, v in vals.items()})

    # 2. pin
    pin = []
    for idx in rng.choice(len(ys), size=min(len(ys), draws * 3), replace=False):
        md, n, rg = G.disc_ring(meta["x0"] + xs[idx] * meta["dx"], meta["y0"] + ys[idx] * meta["dy"],
                                PIN["r_m"], PIN["ring"])
        if n >= 3 and np.isfinite(rg):
            pin.append(md - rg)
        if len(pin) >= draws:
            break
    pin_sig = robust_sigma(pin)

    # real zones
    zones = []
    for z in S["zones"]:
        x, y = C.to_xy(meta["epsg"], z["lon"], z["lat"])
        sig = fake[f"r{int(z['r_m'])}m"]
        row = dict(id=z["id"], r_m=z["r_m"])
        for k, ring in RINGS.items():
            md, n, rg = G.disc_ring(x, y, z["r_m"], ring)
            rel = md - rg
            s = sig[f"sigma_{k}_mm_yr"]
            row.update({"n_px": n, "median_mm_yr": round(md, 2), f"rel_{k}_mm_yr": round(rel, 2),
                        f"z_{k}": round(rel / s, 2), f"significant_{k}": bool(abs(rel / s) >= 2)})
        i, j = G.ij(x, y)
        row["los_e"], row["los_u"] = round(float(geom["los_e"][i, j]), 4), round(float(geom["los_u"][i, j]), 4)
        zones.append(row)

    # 4. detection horizon (zone minus 1 to 3 km ring, the largest zone size)
    sig_zone = fake[f"r{int(radii[-1])}m"]["sigma_ring_1_3km_mm_yr"]
    step_from_rate = sig_zone / rate_sigma_factor(t, group, chain=True)
    step_from_spread = chain_step_sigma(group, resid)
    last = dt.date.fromisoformat(dates[-1])
    end = dt.date.fromisoformat(until)
    proj_dates, chain_sig, best_sig = [dates[-1]], [sig_zone], [step_from_spread * rate_sigma_factor(t, group, False)]
    d, tt, gg = last, list(t), list(group)
    while d < end:
        d += dt.timedelta(days=REVISIT_DAYS)
        tt.append(C.years([d.isoformat()])[0])
        gg.append(group[-1])
        proj_dates.append(d.isoformat())
        chain_sig.append(step_from_rate * rate_sigma_factor(tt, gg, chain=True))
        best_sig.append(step_from_spread * rate_sigma_factor(tt, gg, chain=False))
    u_site = float(np.median([z["los_u"] for z in zones]))

    def first_dates(sig):
        out = {}
        for s in SINKS_MM_YR:
            need = s * u_site / 2.0
            hit = next((dd for dd, sg in zip(proj_dates, sig) if sg <= need), None)
            out[f"vertical_{int(s)}_mm_yr"] = dict(los_signal_mm_yr=round(s * u_site, 1),
                                                   sigma_needed_mm_yr=round(need, 1), first_date=hit)
        return out
    return dict(
        track=track, direction=meta.get("direction"), dates=len(dates), first=dates[0], last=dates[-1],
        groups=len(set(group)), stack_source=meta.get("made_by", "unknown"),
        pixel_sigma_mm_yr=round(robust_sigma(vel[tie & np.isfinite(vel)]), 2),
        zone_sigma=fake, pin_sigma_mm_yr=round(pin_sig, 2), pin_threshold_2sigma_mm_yr=round(2 * pin_sig, 1),
        pin_draws=len(pin), zones=zones,
        detection=dict(basis="zone minus 1 to 3 km ring, zone radius %d m" % int(radii[-1]),
                       sigma_now_mm_yr=round(sig_zone, 2),
                       sigma_per_pair_from_rate_mm=round(step_from_rate, 2),
                       sigma_per_pair_from_spread_growth_mm=round(step_from_spread, 2),
                       los_u_site=round(u_site, 3), revisit_days=REVISIT_DAYS, dates=proj_dates,
                       chain=dict(meaning="rough estimate: noise modelled as a random walk along the 12-day pairs "
                                          "(fits the spread growth on NASA's interferograms), per-pair σ set to "
                                          "reproduce today's zone σ. The cause is not the pair chain itself: see "
                                          "notebooks/04/gslc_chain_vs_network.json",
                                  sigma_mm_yr=[round(x, 2) for x in chain_sig], first_2sigma=first_dates(chain_sig)),
                       best_case=dict(meaning="optimistic bound, not a result: independent noise per date equal to "
                                              "the measured per-pair σ. Redundant longer pairs did not reach it on "
                                              "094D (notebooks/04/gslc_chain_vs_network.json)",
                                      sigma_mm_yr=[round(x, 2) for x in best_sig],
                                      first_2sigma=first_dates(best_sig))),
    )


def up_east(res: dict) -> list:
    import numpy as np
    if not {"129A", "094D"} <= set(res):
        return []
    out = []
    a, d = res["129A"], res["094D"]
    for za, zd in zip(a["zones"], d["zones"]):
        k = "rel_ring_1_3km_mm_yr"
        A = np.array([[za["los_e"], za["los_u"]], [zd["los_e"], zd["los_u"]]])
        sa = a["zone_sigma"][f"r{int(za['r_m'])}m"]["sigma_ring_1_3km_mm_yr"]
        sd = d["zone_sigma"][f"r{int(zd['r_m'])}m"]["sigma_ring_1_3km_mm_yr"]
        Ai = np.linalg.inv(A)
        e, u = Ai @ np.array([za[k], zd[k]])
        cov = Ai @ np.diag([sa ** 2, sd ** 2]) @ Ai.T
        out.append(dict(id=za["id"], los_129A_mm_yr=za[k], los_094D_mm_yr=zd[k],
                        east_mm_yr=round(float(e), 1), sig_east_mm_yr=round(float(np.sqrt(cov[0, 0])), 1),
                        up_mm_yr=round(float(u), 1), sig_up_mm_yr=round(float(np.sqrt(cov[1, 1])), 1),
                        up_129A_only_mm_yr=round(za[k] / za["los_u"], 1),
                        sig_up_129A_only_mm_yr=round(sa / za["los_u"], 1)))
    return out


def plot(res: dict, path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    blue, gray = "#2a78d6", "#888780"
    for tr, r in res.items():
        det = r["detection"]
        x = [dt.date.fromisoformat(d) for d in det["dates"]]
        if tr == "129A":
            ax.plot(x, det["chain"]["sigma_mm_yr"], color=blue, lw=2, label="NISAR 129A, pairs as processed now")
            ax.plot(x[0], det["chain"]["sigma_mm_yr"][0], "o", color=blue, ms=6)
        else:
            ax.plot(x, det["chain"]["sigma_mm_yr"], color=gray, lw=1.3, ls="--",
                    label=f"NISAR {tr}, as processed (fails the sign check; rehearsal stack)")
    ref = res.get("129A") or next(iter(res.values()))
    x0 = dt.date.fromisoformat(ref["detection"]["dates"][0])
    x_end = dt.date.fromisoformat(ref["detection"]["dates"][-1])
    for k, f in ref["detection"]["chain"]["first_2sigma"].items():
        ax.axhline(f["sigma_needed_mm_yr"], color="#c3c2b7", lw=1)
        s = k.split("_")[1]
        when = f["first_date"] or f"not before {x_end.year}"
        ax.text(x0 + dt.timedelta(days=200), f["sigma_needed_mm_yr"] - 0.25,
                f"a {s} mm/yr sink clears 2σ on 129A: {when}", va="top", ha="left", fontsize=8, color="#52514e")
    ax.set_ylabel("Noise on a zone's rate, 1σ (mm/yr)")
    ax.set_title("When could NISAR see the salt zones? A rough estimate if passes continue every 12 days", fontsize=10)
    ax.set_ylim(0, max(r["detection"]["sigma_now_mm_yr"] for r in res.values()) * 1.2)
    ax.grid(axis="y", color="#e1e0d9", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.text(0.01, 0.01, "Dot: today's measured zone noise (zone minus 1 to 3 km ring, 1,000 fake zones on stable "
             "ground; noise_floor.py, 04).\nRough estimate: noise modelled as adding up pair by pair, as on NASA's "
             "interferograms. Assumes no new gap, the same processing, no seasonal term, a steady rate.", fontsize=7,
             color="#898781")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def run(site: str, draws: int, until: str) -> None:
    import numpy as np
    warnings.filterwarnings("ignore", message="All-NaN slice")
    rng = np.random.default_rng(2026)
    trs = [t for t in C.tracks(site) if (C.site_dir(site, t) / "cal.npz").exists()]
    if not trs:
        raise C.todo("04", f"no tied tracks under data/work/{site}/: run calibrate.py first")
    res = {t: track_floor(site, t, draws, until, rng) for t in trs}
    import pathlib
    out = pathlib.Path(__file__).resolve().parent / "products" / site
    out.mkdir(parents=True, exist_ok=True)
    doc = dict(
        site=site, made_by="noise_floor.py (04)", made=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        synthetic=False, status="analysis, not reviewed by 05",
        method="fake zones on tie pixels (seed 2026), robust σ = 1.4826·MAD; see the docstring of noise_floor.py",
        sinks_tested_mm_yr=list(SINKS_MM_YR),
        sink_source="EGMS Ortho shows up to about 25 mm/yr of sinking at Ocnele Mari, 2019 to 2024 (docs/synopsis.md)",
        tracks=res, up_east_check=up_east(res),
        notes=["094D in data/work/ is the advisor's rehearsal stack and fails the sign check: read it as a diagnostic.",
               "The up/east solve mixes windows (129A Nov 2025 to Oct 2026 with a gap, 094D Jun to Oct 2026).",
               "The detection dates assume passes every 12 days, no new gap, no seasonal term and a steady rate."])
    C.save_json(out / "noise_floor.json", doc)
    plot(res, out / "noise_floor.png")
    for t, r in res.items():
        det = r["detection"]
        best = max(abs(z["z_ring_1_3km"]) for z in r["zones"])
        fd = lambda sc, s: det[sc]["first_2sigma"][f"vertical_{s}_mm_yr"]["first_date"]
        print(f"{t}: pixel σ {r['pixel_sigma_mm_yr']} · zone σ {det['sigma_now_mm_yr']} mm/yr · per pair "
              f"{det['sigma_per_pair_from_rate_mm']} mm (spread growth {det['sigma_per_pair_from_spread_growth_mm']}) "
              f"· pin needs > {r['pin_threshold_2sigma_mm_yr']} mm/yr · best zone |z| {best:.1f} · 2σ for 25/19 "
              f"mm/yr sinks: chain {fd('chain', 25)} / {fd('chain', 19)}, best case {fd('best_case', 25)} / "
              f"{fd('best_case', 19)}")
    print(f"wrote {out / 'noise_floor.json'} and noise_floor.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--draws", type=int, default=1000, help="fake zones per zone size and per track (default 1000)")
    ap.add_argument("--until", default="2031-01-01", help="last date of the detection projection (ISO)")
    a = ap.parse_args()
    run(a.site, a.draws, a.until)


if __name__ == "__main__":
    C.run_cli(main)
