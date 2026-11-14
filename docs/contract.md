# The products contract · DRAFT

> **DRAFT until hour 2.** The Lead (01) and the app developer (06) freeze it (decision O-10). After that a change needs
> both, in one PR that also updates `checkpoint.py`, `mock_products.py` and the page.
>
> Source: the advisor kit's contract (prior work), plus `view` (D-002) and `frames.<track>.gaps` (honest slider).

The page reads `products/<site>/` and `products/index.json`, **nothing else**. Sites: `ocnele_mari` (real), `demo` (synthetic known answer), `mock` (invented, from `mock_products.py`).

## Files

| File | Content | Written by |
|---|---|---|
| `manifest.json` | Everything the page needs to draw the site (below) | export.py (06) |
| `up.png`, `east.png`, `los_<track>.png` | Rate overlays on a lon/lat grid, RdBu, red = sinking / away; transparent = no data (or \|rate\| < 2σ) | export.py (06) |
| `frames/<track>/<date>.png` | Cumulative change since the track's first date, fixed colour scale per track | export.py (06) |
| `series.json` | Time series at the salt zones and stations | export.py (06) |
| `stations.geojson` | Honest pins: NISAR vs GNSS per track, agree flag, reason | validate.py (05) |
| `checks.json`, `checks.md` | Every check, pass / warn / fail / info | validate.py (05) |
| `calib.json` | The tie per track | calibrate.py (04) |
| `up.tif`, `east.tif` | The same rates on the original UTM grid, for the record | export.py (06) |
| `../index.json` | `[{site, name, synthetic}]` for the site picker | export.py (06), mock_products.py |

## `manifest.json`

```jsonc
{
  "site": "ocnele_mari",
  "name": "Ocnele Mari",
  "story": "one sentence (01)",
  "synthetic": false,                 // true → the page shows "simulated, not data"
  "note": "up and east from 129A + 094D",
  "built": "2026-11-15T10:00:00+00:00",
  "bounds": [[S, W], [N, E]],         // overlay extent (Leaflet order)
  "center": [lat, lon],               // analysis-window centre
  "view": {                           // D-002: where the map opens and how far out it goes
    "center": [45.086281, 24.2704806], "zoom": 13,
    "min_zoom": 6, "context": "romania-blurred"
  },
  "layers": [{"id": "up", "label": "Vertical rate (− = sinking)", "png": "up.png", "units": "mm/yr", "vmin": -20, "vmax": 20}],
  "frames": {
    "129A": {"dates": ["2025-11-07", "…"], "pngs": ["frames/129A/2025-11-07.png", "…"],
             "vmin": -20, "vmax": 20, "units": "mm since first date", "direction": "Ascending",
             "gaps": [["2026-01-18", "2026-06-23"]]}   // no pair spans these: label "no data", never interpolate
  },
  "checks": {"pass": 0, "warn": 0, "fail": 0, "info": 0},
  "credits": "NISAR L2 GUNW (NASA–ISRO, ASF DAAC) · …"
}
```

## `series.json`

```jsonc
[{"id": "z1", "label": "Salt zone …", "kind": "zone",        // or "station"
  "lat": 45.0892, "lon": 24.2872, "up": -4.1,                // mm/yr, null if none
  "series": {"129A": {"dates": ["…"], "mm": [0.0, -1.2, null, "…"], "rate": -3.0}}}]
```

## `stations.geojson`

A FeatureCollection of points. `properties`:

```jsonc
{"station": "VLC1", "source": "NGL MIDAS (EU-fixed)", "t_end": "2018.92", "dist_km": 6.8,
 "tracks": {"129A": {"nisar": -7.4, "gnss": -0.6, "diff": -6.8, "tol": 36.3}},
 "agree": true,                    // true | false | null (not testable, e.g. no vertical rate)
 "reason": "agrees within tolerance; rate from data ending 2018-11, assumes steady motion since",
 "nisar_up": -7.0, "gnss_up": -0.6}
```

## `checks.json`

`[{"id": "sign-129A", "status": "pass|warn|fail|info", "title": "…", "detail": "…", "value": -4.6}]`

## `calib.json`

`{"model": "EuVeM2022 …", "tracks": [{"track": "129A", "direction": "Ascending", "method": "offset|plane", "offset_mm_yr": …, "slope_east_mm_yr_per_10km": …, "slope_north_mm_yr_per_10km": …, "n_tie_pixels": …, "residual_std_mm_yr": …, "residual_mad_mm_yr": …, "model_los_mean_mm_yr": …, "swap_delta_mm_yr": …}]}`

## Conventions

Units are mm/yr for rates and mm for cumulative change. LOS is positive towards the satellite; up is positive (sinking is negative). Dates are ISO. Colours are RdBu with red meaning sinking or away. Every value for a mock or synthetic site is flagged by `synthetic: true`.
