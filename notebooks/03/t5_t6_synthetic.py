# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Exploration only (never imported). Early tests T5 (gap groups) and T6 (summer-only bias) on the synthetic stack,
plus whether the annual term can be used on a series shorter than 1.5 years.

    python notebooks/03/t5_t6_synthetic.py

Rules as written in prompts/early-tests.md (before any run):
  T5  real 129A date pattern with the 18 Jan to 23 Jun 2026 gap, rate with one offset per group: passes with stable
      ground bias under 1 mm/yr and every zone within 15 % of the truth.
  T6  a 5 mm annual term in the truth, sampled on 094D's June to October dates, fitted without an annual term:
      passes if the zone rate error is under 20 %. If not, 094D is labelled "summer to autumn only".
  Short-span annual term (added 15 Nov 2026, same standard as T5): the 129A pattern with a 5 mm annual term, fitted
      with the annual term forced on (span 0.95 years). Allowed on the page only if it meets the T5 standard AND does
      better than the plain line on the same data.
Seeds 7, 8, 9 (three noise draws); a test passes only if every seed passes. Writes notebooks/03/t5_t6_synthetic.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

import common as C  # noqa: E402
import export  # noqa: E402
import fetch  # noqa: E402
import stack  # noqa: E402

SEEDS = (7, 8, 9)


def score(track, annual_fit):
    meta = C.load_json(C.WORK / "demo" / track / "meta.json")
    stack.run("demo", track, out_name="ts_test.npz", annual=annual_fit)
    vel = np.load(C.WORK / "demo" / track / "ts_test.npz")["vel"]
    truth = np.load(C.WORK / "demo" / track / "truth.npz")["los_rate"]
    masks = export.nisar_zone_masks(C.SITES["demo"], meta)
    stable = stack.stable_mask("demo", meta) & np.isfinite(vel)
    bias = float(np.median(vel[stable] - truth[stable]))
    zones = {}
    for z in ("z1", "z2", "z3", "z4"):
        m = masks[z] & np.isfinite(vel)
        if m.sum() < 5:
            continue
        got, want = float(np.median(vel[m])), float(np.median(truth[m]))
        zones[z] = dict(fitted=round(got, 2), truth=round(want, 2), rel_error=round(abs(got - want) / abs(want), 3))
    return dict(stable_bias_mm_yr=round(bias, 2), zones=zones)


def run_set(noise):
    out = {"T5": [], "T6": [], "annual_short": [], "line_same_data": []}
    for seed in (SEEDS if noise else SEEDS[:1]):
        fetch.synthetic("demo", seed=seed, annual_mm=0.0, noise=noise)
        out["T5"].append(score("129A", None))
        fetch.synthetic("demo", seed=seed, annual_mm=5.0, noise=noise)
        out["T6"].append(score("094D", False))
        out["annual_short"].append(score("129A", True))
        out["line_same_data"].append(score("129A", False))
    worst = lambda runs: max((z["rel_error"] for r in runs for z in r["zones"].values()), default=float("nan"))
    maxbias = lambda runs: max(abs(r["stable_bias_mm_yr"]) for r in runs)
    out["verdict"] = dict(
        T5=dict(pass_=bool(maxbias(out["T5"]) < 1 and worst(out["T5"]) <= 0.15), max_bias=maxbias(out["T5"]), worst_zone=worst(out["T5"])),
        T6=dict(pass_=bool(worst(out["T6"]) < 0.20), worst_zone=worst(out["T6"])),
        annual_short=dict(allowed=bool(maxbias(out["annual_short"]) < 1 and worst(out["annual_short"]) <= 0.15
                                       and worst(out["annual_short"]) < worst(out["line_same_data"])),
                          max_bias=maxbias(out["annual_short"]), worst_zone=worst(out["annual_short"]),
                          plain_line_worst_zone=worst(out["line_same_data"])))
    return out


def main():
    # noise-free tests the method (gap groups, summer sampling, annual term); realistic noise tests what our zone
    # sizes can resolve. Both are reported; the method verdict is the one the early tests ask about.
    out = {"method_noise_free": run_set(False), "realistic_noise": run_set(True)}
    (ROOT / "notebooks" / "03" / "t5_t6_synthetic.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v["verdict"] for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
