# products/

**Owner:** 06 · App developer (Darius)

`products/<site>/` is what the page reads, and nothing else. Scripts write it, never people: `export.py` (06), `validate.py` (05) and `calibrate.py` (04). The file contracts are in [docs/build-spec.md](../docs/build-spec.md#file-contracts); the files added for the real-data page are listed below and proposed for the contract in [logs/06-app.md](../logs/06-app.md).

| Folder | What | Written by |
| --- | --- | --- |
| `ocnele_mari/` | Real data (D-001): Sentinel-1 July to October 2026, NISAR catalog coverage | `python export.py ocnele_mari` |
| `demo/` | The synthetic known-answer run (not built yet) | the pipeline on the `demo` site |
| `mock/` | Invented values for building the page | `python mock_products.py` |
| `index.json` | Sites for the page; the page opens the first real site | `export.py`, `mock_products.py` |

Check a folder with `python checkpoint.py <site>`. Anything with `synthetic: true` shows "Simulated, not data" on the page.

## `ocnele_mari/` file by file

Rebuilt in about 10 s by `python export.py ocnele_mari` (needs `numpy`, `pyproj` and `Pillow` from `requirements.txt`). Its inputs are committed: `sentinel1/analysis/summary.json` and the grid chunks in `sentinel1/assets/` (03), and `data/scenes/ocnele_mari_gunw.csv` (02). Last built Sat 14 Nov 2026, about 16:00.

| File | Contents | Notes |
| --- | --- | --- |
| `manifest.json` | Sensors (NISAR pending, Sentinel-1 measured), views, default (NISAR Coverage on 129A), bounds, D-002 view, windows, methods, EGMS pending state, credits | `story` still comes from `common.py` and is a TODO (01); the page hides it |
| `s1/frames/<track>/<date>.png` | Cumulative line-of-sight change since the first date, 16 dates per track, RdBu ±20 mm, lon/lat grid of about 55 m | Fallback and slide images; the page draws the dots below |
| `s1/los_<track>.png` | Line-of-sight rate, the fitted annualized slope over the window, RdBu ±40 mm/yr | Fallback |
| `s1/points_<track>.json` | The same values as dots: one every 80 m (the top-left 40 m pixel of each 2 × 2 block, sampled, not averaged), change per date and rate, in 0.1 mm | About 1.3 MB per track; about 16,000 to 18,000 dots |
| `series.json` | Zones 1 to 4 and the outer comparison area: per-date mm, fitted change, rate, pixel count, keyed `s1:<track>` | Zone 3 has no series on 029A (no connected pixels) |
| `sensitivity.json` | Per window: frames, layers, points, and every processing run (baseline, stricter coherence, west and east reference, elevation correction) per track and zone | Only the July to October window so far |
| `coverage.json` | NISAR: 22 catalog pairs, dates and the 18 Jan to 23 Jun 2026 gap per track. Sentinel-1: dates, pair counts, usable pixels per zone | |
| `stations.geojson`, `calib.json`, `checks.json` | Explicit "pending" files: no stations, no tie, one info check "Validation not run yet" | Written only if missing; `validate.py` (05) and `calibrate.py` (04) replace them |

Values beyond a layer's scale are drawn at full colour and the legend says so. A pixel with no data has no dot and is transparent in the PNGs.

## Zone 4 retrospective predictor

`ocnele_mari/forecast.json` is an optional sidecar for the Zones view, tied to Sentinel-1 029A, July–October baseline and Zone 4. The UI checks that the exported observation dates and values match the active series. The dashed forecast stops 30 days after the final acquisition, on 4 November 2026 for this build. The interval is unavailable because the four overlapping backtest windows are insufficient to calibrate it.

Rebuild on CPU using NumPy, SciPy, pyproj and GDAL:

```sh
python sentinel1/scripts/forecast.py RAW_HYP3_ZIP_DIRECTORY products/ocnele_mari/forecast.json --as-of 2026-11-14
```

The script reconstructs training observations from pairs ending at each cutoff and scores against changes reconstructed from pairs wholly within the later evaluation window. Each fold scores on pixels supported on both sides. It ranks persistence, Theil–Sen and a Matérn Gaussian process by 30-day MAE. The same four overlapping windows rank the models and report their errors. Treat the ranking as exploratory. See [Hill et al.](https://doi.org/10.1029/2020JB020176) and [rolling-origin evaluation](https://otexts.com/fpp3/tscv.html).
