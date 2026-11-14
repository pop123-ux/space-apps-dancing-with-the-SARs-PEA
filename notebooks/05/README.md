# 05 · Validator notebooks

**Owner:** 05 · Validator (Paul)

Exploration only: nothing here is imported by the pipeline. The full write-up, with settings and caveats, is in [docs/validation-log.md](../../docs/validation-log.md) ("Moisture and rainfall screen, and the forecast test").

## Handoff to 03: Zone 4 and control-ring moisture and rain screen

This answers the "Paul / 05 handoff" in `docs/forecast.md` on `r06/page`.

| File | What it is |
|---|---|
| [z4_screen_inputs.csv](z4_screen_inputs.csv) | One row per Sentinel-1 date, track and area: the date-aligned inputs (64 rows: 16 dates × 029A and 007D × z4 and control) |
| [z4_screen_results.json](z4_screen_results.json) | The screen per track, area and input, and the forecast backtest per cutoff with the MAE table |
| [z4_screen.py](z4_screen.py) | Makes both files: `python notebooks/05/z4_screen.py <forecast.json>` after `soil_moisture.py` |
| [soil_moisture.py](soil_moisture.py) | Reads NISAR SME2 over HTTP (needs `EARTHDATA_TOKEN` in `.env`) into `data/work/ocnele_mari/sm/` |
| [sm_vs_s1.py](sm_vs_s1.py) | The same screen for every zone; writes `docs/figures/05_soil_moisture_vs_s1.png` |
| [z3_check.py](z3_check.py) | The z3 investigation (EGMS against the Sentinel-1 grids) |

### Columns of `z4_screen_inputs.csv`

| Column | Unit | Meaning |
|---|---|---|
| `date` | ISO date | Sentinel-1 acquisition (`sentinel1/analysis/summary.json`) |
| `track` | | `029A` or `007D` |
| `area` | | `z4` (zone circle from `common.py`) or `control` (outer ring 6.5 to 8 km from the nearest zone edge, as in `fit.py`) |
| `los_mm` | mm | Baseline-fit zone median, LOS, positive towards the satellite, relative to the 3 to 6.5 km reference band, first date = 0. For 029A z4 this is the series `forecast.json` uses |
| `s1_pixels` | count | Sentinel-1 pixels behind `los_mm` (z4: 34 on 029A, 76 on 007D) |
| `nisar_date`, `nisar_track` | | The NISAR SME2 granule matched to this date (nearest, at most 2 days; all July to September matches are 1 day off). Empty = none |
| `moist_rec` | m3/m3 | Area minus reference-band soil moisture, recommended retrievals only (`retrievalQualityFlag` bit 0 = 0). Empty = no recommended pixel |
| `moist_rec_px` | count | 200 m moisture pixels behind `moist_rec` in the area (z4: 0 on 15 of 16 dates) |
| `moist_all`, `moist_all_px` | m3/m3, count | The same with every retrieval, including those NISAR does not recommend (sensitivity only) |
| `lag1_rec`, `lag1_all` | m3/m3 | The same on the previous NISAR date (3 to 9 days before the matched one) |
| `rain7_mm`, `rain30_mm` | mm | ERA5 precipitation at 45.088 N, 24.290 E summed over the 7 and 30 days ending on `date` (Open-Meteo archive) |

Products: Sentinel-1 HyP3 `INSAR_ISCE_BURST` fit (03); NISAR `NISAR_L3_SME2_PROVISIONAL_V1` (and `BETA_V1` for 18 Jan), 200 m EASE-Grid 2.0, tracks 129A and 094D; ERA5 daily via Open-Meteo. Footprint: the Sentinel-1 window, 16.4 km square on 45.088 N, 24.290 E. Missing values are empty cells and are left out of each correlation.

### Results in one paragraph

No input is flagged for Zone 4 or the control ring on either track (detrended |r| at most 0.44, needed about 0.50 to 0.53, and the largest values depend on single dates). Zone 4 has no recommended NISAR moisture retrievals. The predeclared input (7-day rain, lag 0, ridge λ = 1, issuance with rain returning to its training mean) scores 4.74 mm MAE at 30 days on the four `forecast.json` cutoffs, against 4.19 mm for persistence and 3.90 mm for the reproduced GP: no improvement. The training series is the final reconstruction truncated at each cutoff, not a per-cutoff re-inversion (the raw ZIPs are not on 05's machine); the reproduced baselines match the export within 0.09 mm.
