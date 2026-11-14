# Zone 4 forecast and environmental screening

**Owner:** 03 · InSAR analyst (Alexandru, Eric)

## Current app and model

The entry point is [index.html](../index.html). It imports [app/main.js](../app/main.js), which loads `products/index.json` and the selected site's products. Use **Zones → Sentinel-1 → 029A → July–October → Baseline** for the January scenario. Model selection changes the dashed path and endpoint. NISAR still opens in Coverage until its team displacement products are ready. EGMS appears as reported history in Agreement. A forecast card requires a matching observation series.

- [CPU script](../sentinel1/scripts/forecast.py) and [export](../products/ocnele_mari/forecast.json).
- Zone 4, 029A, 16 epochs, 29 summer interferograms and 34 connected pixels. Latest fitted acquisition 5 October 2026. The requested 1 January 2027 endpoint is 88 days beyond it. Six later catalog dates through 10 November need processing before they can update the fit.
- Thirty-day rolling-cutoff MAE over four overlapping windows: persistence 4.19 mm, Theil–Sen 5.53 mm, Matérn Gaussian process 3.95 mm, long-term trend (EGMS-anchored, added 14 Nov 18:30) 3.97 mm. These scores rank the models in the experiment and do not validate 88-day extrapolation. January LOS endpoints are −7.89, −15.08, −13.78 and −9.21 mm respectively. There is no calibrated prediction interval. See "Verification and the January anchor" below.
- Data and panel checks on this branch: verified static entry paths and real-product overlay references; loaded the actual JSON and rendered the forecast panel in a JavaScript harness, including model switching and scenario gating. Browser verification with Playwright passed on 14 Nov (desktop and iPhone 13; see the audit note in `STATUS.md`).

## What to investigate while moisture and rainfall are in progress

| Priority | Input | Test and interpretation |
|---|---|---|
| 1 | Acquisition-time tropospheric delay, from OPERA TROPO where available or another documented meteorological delay estimate | Project to each radar LOS and apply a reference consistent with the radar stack. Compare before/after over Zone 4, an elevation-matched stable sample, and the existing outer ring. Inspect closure and whether the difference persists across tracks. This is a measurement correction. |
| 2 | Perpendicular baseline and elevation/DEM residuals | Extract per-pair baseline metadata where available. Screen residual phase versus perpendicular baseline on stable pixels, controlling for elevation and acquisition date. A relationship suggests a measurement correction to test. |
| 3 | Surface temperature and land cover | Compare built, bare and vegetated subsets, with matched stable pixels. Check if temperature or seasonal effects are concentrated on built surfaces or associated with changing radar support. The summer series alone is too short to establish an annual cycle. |
| 4 | Dated groundwater levels, brine pressure and extraction/operations | Ask the team to check local availability. Compare dated changes and plausible lags near the mine and stable controls. These are candidate physical inputs. Their availability and useful predictive effects are unverified. |

Initial diagnostic using stored summer 029A fits: Zone 4 minus the outer comparison area's fitted window change was **−11.41 mm baseline**, **−12.91 mm west reference**, **−11.99 mm east reference**, **−13.06 mm strict coherence** and **−4.63 mm elevation correction**. This subtracts two fitted summaries with scenario-specific support. It is a diagnostic of reference and correction sensitivity, with no causal attribution. Strict coherence leaves only six Zone 4 pixels. The elevation test therefore has the highest priority for validating the measurement.

## Paul / 05 handoff

The forecast already exists on this branch in the script and export linked above. Finish the July–October Zone 4 plus control-ring screening. Return acquisition dates, track, products and footprint, matched pixel counts, feature units, lags, missing values and the per-date LOS and moisture/rain inputs for both Zone 4 and the control. Report raw and detrended screening results with support and sensitivity to removing individual dates. The roughly |r| = 0.6–0.8 thresholds from 5–12 dates are screening flags. Serial dependence, shared seasonal trends, and trying several lags can make chance associations look strong.

Start an exogenous feature model only after alignment. Try one predeclared lag or rainfall window with regularized regression, using the same forecast cutoffs and persistence/trend/GP on matched eligible cases. Train and fit preprocessing inside each cutoff. Evaluate with information that would have been available at issuance, or label the supplied future covariates as conditional scenarios. Add controls only after credible held-out improvement and keep sliders within the observed input range. A vertical change control needs a validated vertical target. One NISAR granule supports checks on a pair and its geometry.

Record each result in the relevant Markdown log with settings, source, support, and outcome. Record decisions and reversals in [DECISIONS.md](../DECISIONS.md), update [STATUS.md](../STATUS.md) for milestones and blockers, and update [ui.md](ui.md) whenever the displayed meaning or behavior changes.

## Verification and the January anchor (14 Nov 2026, 18:30)

Claude Code took over from the ChatGPT ("Sol") sessions as builder and verifier. Everything below was run on CPU in this repository; nothing needs RunPod.

### Reproduction

- **Inputs:** the 29 summer 029A HyP3 ZIPs from `sentinel1/provenance/asf_downloads.json`, with all 29 SHA-256 checksums matching `raw_SHA256SUMS` (1.91 GB; the links expire about 29 Nov 2026).
- **Reader:** `fit.read_product` now falls back to rasterio (bundled GDAL) when the GDAL Python bindings are missing. Refitting 029A with it reproduces `sentinel1/analysis/summary.json`: 60 rates across 5 scenarios and 5 areas, all pixel counts identical, worst difference 1.8e-6 mm, and the same grid NaN pattern. It takes 11 s.
- **Forecast:** `forecast.py` reproduces `products/ocnele_mari/forecast.json` exactly (0.0 difference in every path, metric and observed value) in 6 s.

### Finding: the summer slope is not the long-term rate

| Source | Zone 4, 029A line of sight | Window |
| --- | --- | --- |
| Sentinel-1 summer fit (what the GP and Theil-Sen extrapolate) | **−30.5 mm/yr** (Theil-Sen −29.8) | 7 Jul to 5 Oct 2026, 16 dates |
| Same, elevation-corrected scenario | −11.5 mm/yr | same |
| EGMS Ortho 2020–2025, Up −3.1 and East +4.9 mm/yr (05, 10 cells), projected with Zone 4's 029A look vector (e −0.634, u 0.765; north ignored) | **−5.5 mm/yr** | 2020 to 2025 |
| Sentinel-1 January to October 2026 fit (−4.07 mm over 277 days; handoff text, outputs not yet in the repository) | **−5.4 mm/yr** | 1 Jan to 5 Oct 2026 |

Two independent long-term records agree within 0.1 mm/yr. The summer-only slope is about 5.5 times larger, and elevation correction alone removes about two thirds of it. A summer slope extrapolated 88 days into winter therefore most likely overstates the January change. This is a measurement and seasonality effect, not a finding about the mine.

### New model: long-term trend

`forecast.py` adds `long_term`: a fixed line-of-sight rate of −5.48 mm/yr (the EGMS rate above), set before every 2026 cutoff, so it has no look-ahead. It joins the same backtest.

| Model | 30-day MAE (4 cutoffs) | 1 Jan 2027 LOS, mm, relative to 7 Jul 2026 |
| --- | --- | --- |
| Persistence | 4.19 | −7.89 |
| Theil–Sen trend (summer) | 5.53 | −15.08 |
| Gaussian process (summer) | 3.95 | −13.78 |
| **Long-term trend (EGMS 2020–2025)** | **3.97** | **−9.21** |

The 30-day scores of the GP and the long-term trend are a tie (0.02 mm on four overlapping cutoffs whose truths range from −6.9 to +5.7 mm). The export still selects the GP by the predeclared rule (lowest 30-day MAE). For the 88-day January horizon the long-term trend is the better-supported default; switching the default is a team decision (see `DECISIONS.md`, 18:30).

### Paul's moisture and rainfall screen (05, PR #9), and the re-inverted rain test

05's findings (translated from Romanian, from `notebooks/05/` and `docs/validation-log.md` on `r05/egms-and-witnesses`):

1. No input is flagged for Zone 4 or the control ring on either track. The largest detrended |r| is 0.44, against a threshold of about 0.50 to 0.53, and the larger values depend on single dates.
2. Zone 4 has no NISAR SME2 soil-moisture pixel marked "recommended", so moisture is a sensitivity test only (10 non-recommended pixels).
3. The predeclared input (7-day rain, lag 0, ridge λ = 1, no future data) scored 4.74 mm MAE at 30 days on the same four cutoffs, against 4.19 for persistence and 3.90 for the GP. No improvement.
4. That run trained on the final reconstruction cut at each cutoff, a small look-ahead.
5. The only correlation above threshold in any zone is 029A zone 1 with moisture, r = −0.70. With this many tests that is about what chance gives, so it is a candidate to recheck on the January to October extension.

Rerun inside `forecast.py` with a fresh inversion at every cutoff (point 4 removed), using 05's ERA5 7-day rain from `z4_screen_inputs.csv`: **issuance MAE 4.80 mm, conditional 5.49 mm** (05: 4.74 and 5.42). The look-ahead barely mattered, and the conclusion holds: rain does not improve the forecast. Results are in `forecast.json` under `covariate_tests`.

### Decision on the scenario controls

The app's nice-to-have controls ("tweak a parameter and the predicted change follows the observed trend") need an input that improves held-out forecasts. Neither rainfall nor soil moisture does. So the only control today is the **model** selector (four forecast paths), and the panel says that weather inputs were tested and not adopted. Any future control must beat persistence and the long-term trend on held-out cutoffs, stay within the observed input range, and say it is a line-of-sight scenario. A slider labelled vertical change needs a validated vertical target.

### What this cannot tell you

- Whether Zone 4 is sinking faster in 2026 than in 2020–2025: the summer excess may be seasonal atmosphere, as the elevation test suggests.
- How wrong the 1 January value will be: there is no 88-day backtest and no calibrated interval. The four paths show the model spread, not a confidence range.
- Anything about vertical motion or safety: this is line-of-sight change relative to nearby terrain.

### Next steps (owners)

1. **03/02:** process the six Sentinel-1 029A acquisitions after 5 Oct (through 10 Nov). This shortens the January horizon from 88 to 52 days and gives the first backtest that crosses into autumn.
2. **03:** commit the January to October fit (job list with ZIP checksums, `sentinel1/analysis_jan_oct/summary.json`, then `python scripts/pack_grids.py analysis_jan_oct`). It is the cross-check behind the long-term trend, and it is still only in a ChatGPT-hosted ZIP.
3. **03:** acquisition-time troposphere correction (OPERA TROPO or ERA5-based), the first measurement check in the table above.
4. **03:** a zone-level network inversion, so Zone 3 and the descending January to October series get values despite pixel-level gaps.
5. **05:** recheck 029A zone 1 moisture (r = −0.70) on the January to October fit.
6. **04/02:** verify Matei's NISAR file (the product name given was "NISAR_L4_PR_GUNW"; GUNW is a Level 2 product, so confirm the type, dates, track and geometry first).
7. **06 (Darius):** see the handoff below.

### Handoff to 06 (Darius)

- `products/ocnele_mari/forecast.json` has a fourth path `model_paths_mm.long_term`, `metrics.long_term`, and new blocks `long_term` (rate, EGMS inputs, look vector, source) and `covariate_tests.rain7`. The default `model` is unchanged (`gaussian_process`).
- `app/main.js` got two minimal edits: the label "Long-term trend (EGMS 2020–2025)" and the sentence "Rainfall and soil moisture were tested and did not improve the forecast, so there is no weather control yet". Restyle freely.
- Browser check (Playwright, Chromium, 1280 × 900): the four buttons render, the long-term button shows the −9.21 mm endpoint, and there are no console errors. **Layout:** with four buttons the model selector overflows its row ("Gaussian process" is cut off); wrap it or use a select on narrow panels.
- If the team makes the long-term trend the default, change `model` in the export (one argument), not in the page.

## Troposphere, the January to October fit, and Chronos-2 (14 Nov 2026, 19:30)

### The January to October fit is in the repository (next step 2, done)

- `sentinel1/analysis_jan_oct/`: Sol's fit (49 dates and 95 pairs per track, 47 closure triangles each; zone 4 029A −4.07 mm over the window at baseline, +4.48 mm with the DEM-slope correction; no descending zone series), with its grids packed in `sentinel1/assets_jan_oct/` (`python scripts/restore_grids.py` restores both windows).
- `sentinel1/provenance/hyp3_jobs_jan_oct_status.json`: the 132 job names and IDs, all SUCCEEDED. **Limitation:** it has no granule names, download links or ZIP checksums, unlike the July to October provenance, so this fit cannot be re-run from the repository alone. The HyP3 job IDs can recover the links (Earthdata login) until the products expire.
- It confirms that 1-day pairs from near-duplicate Sentinel-1A and 1D acquisitions were kept (for example 25 to 26 April on 029A).

### Weather-model troposphere (next step 3, done for July to October)

`sentinel1/scripts/tropo.py` computes, for every acquisition, the zenith delay versus height from the ECMWF IFS 0.25° pressure-level profile at the acquisition hour (029A 16:16 UTC, 007D 04:29 UTC; Open-Meteo historical-forecast API). `fit.py --tropo` adds a sixth scenario, **weather_model**, that removes each interferogram's differential slant delay at every pixel's DEM height. The delays are stored in `sentinel1/analysis/tropo.json`. Between 200 and 800 m the zenith delay differs by 166 to 204 mm depending on the date.

| Summer 2026, stable ground 3 to 8 km from the zones | Baseline | DEM-slope (fitted) | Weather model (independent) |
| --- | --- | --- | --- |
| 029A rate leaking from elevation, mm/yr per 100 m | −19.2 | −8.9 | **−4.2** |
| 007D, same | −15.3 | −1.9 | −7.8 |
| 029A stable median drift, mm/yr | +10.1 | +3.8 | +4.7 |
| 029A per-pixel scatter (MAD), mm/yr | 26.1 | 24.5 | 25.9 |
| Zone 4 029A rate, mm/yr | −30.5 | −11.6 | **−23.6** |
| Zone 4 007D rate, mm/yr | −14.2 | −8.1 | −11.2 |

The weather model removes most of the elevation-correlated delay without fitting the data (so it cannot absorb real motion that happens to follow elevation). It does not reduce the per-pixel scatter: that is turbulent atmosphere, which one profile per date cannot model. Zone 4 029A stays far above the long-term −5.5 mm/yr, so stratified delay explains only part of the summer excess. The scenario is in `sentinel1/analysis/summary.json` and in the app's "Explore processing choices" (via `export.py`). It is not applied to the January to October fit, whose raw ZIPs are not in the repository.

Forecasting the weather-corrected series (`forecast.py --tropo`): 30-day MAE persistence 4.01, Theil-Sen 5.21, GP 3.31, long-term 3.97, rain 4.25 mm; 1 January endpoints GP −9.74, long-term −7.28, Theil-Sen −10.83 mm. Correcting the atmosphere brings the summer models closer to the long-term anchor. (These MAEs use corrected truths too, so they compare within this scenario, not with the baseline.) The app still shows the baseline forecast, because `forecast.json` holds one scenario; a per-scenario forecast is a 06 option.

### Chronos-2 (amazon/chronos-2), zero-shot on CPU

`sentinel1/scripts/forecast_chronos.py` (after `forecast.py`, in a separate environment with `chronos-forecasting>=2` and CPU torch, about 1.4 GB) adds a fifth path, `chronos2`, with an 80 % interval, to `forecast.json`. It loads in 8 s and runs in about 7 s. Nothing in the page or the pipeline depends on torch.

| Backtest, Zone 4 029A, MAE in mm | Chronos-2 | Persistence | Theil-Sen | GP | Long-term | Chronos-2 80 % interval holds the truth |
| --- | --- | --- | --- | --- | --- | --- |
| Summer, 30 days, 4 re-inverted cutoffs | **3.77** | 4.19 | 5.53 | 3.95 | 3.97 | 4 of 4 |
| Summer weather-corrected, 30 days | 3.38 | 4.01 | 5.21 | **3.31** | 3.97 | 4 of 4 |
| January to October, 30 days, 32 cutoffs | **3.49** | 5.00 | 5.13 | 4.80 | 5.04 | 78 % |
| January to October, **88 days**, 22 cutoffs | **3.81** | 4.29 | 4.64 | 4.39 | 4.29 | 77 % |

- This is the first real 88-day backtest (the January horizon). The January to October cutoffs read their truth off the final reconstruction (a small look-ahead) and overlap, so they are not independent, and they cover one zone on one track.
- Chronos-2 is the only model here with an interval that behaves as calibrated (77 to 78 % of truths inside an 80 % band).
- Its 1 January path is a partial rebound: **−3.87 mm** relative to 7 July (+4.0 mm from 5 October), 80 % interval −11.3 to +15.2 mm. From the January to October context it gives +3.6 mm from 5 October (80 %: −2.9 to +12.3). It extrapolates the shape of the series; it knows nothing about salt, weather or the mine.

### Current 1 January 2027 paths in the app (baseline, relative to 7 July 2026)

| Model | 30-day MAE (4 summer cutoffs) | 1 January |
| --- | --- | --- |
| Persistence | 4.19 | −7.89 |
| Theil–Sen | 5.53 | −15.08 |
| Gaussian process (default by the predeclared rule) | 3.95 | −13.78 |
| Long-term trend (EGMS 2020–2025) | 3.97 | −9.21 |
| Chronos-2 (zero-shot) | 3.77 | −3.87 (80 %: −11.27 to +15.17) |

By the predeclared rule (lowest 30-day MAE) Chronos-2 would now be the default; the export keeps the GP until the team decides (`DECISIONS.md`, 19:30). On the 88-day evidence the candidates for the January default are Chronos-2 (best MAE, calibrated interval) and the long-term trend (independent physical anchor); the GP and Theil-Sen extrapolate the summer slope and score worst at 88 days.

### Handoff to 06 (update)

- `forecast.json` has a fifth path `chronos2`, `intervals.chronos2` (`q10`, `q90`, `level` 0.8) and a `chronos2` block with the backtests. `app/main.js` got the label "Chronos-2 (zero-shot)". The page does not draw the interval yet: shade it between `q10` and `q90` when Chronos-2 is selected, labelled "80 % interval (backtested)".
- Five buttons overflow the model selector even more: use a select or wrapping chips.
- `sensitivity.json` has a sixth scenario `weather_model` ("Weather-model troposphere (ECMWF IFS, acquisition time)"); the elevation scenario is relabelled "Elevation correction (fitted to the data)". `export.py` now treats explicit empty zones from `fit.py` as no series.

### Next steps (updated)

1. Process the six 029A acquisitions after 5 October (through 10 November): shortens the January horizon to 52 days.
2. Commit the January to October raw provenance (granules, links, checksums) from the HyP3 job IDs.
3. Apply the weather model to the January to October fit (needs its raw ZIPs) and recheck the long-term rate and Chronos-2 on it.
4. Zone-level network inversion for Zone 3 and the descending January to October series.
5. Team decision: the default January model.
6. 04/02: Matei's NISAR file (uploading to Google Drive).

## References

- [Hill et al., Sentinel-1 deformation forecasting](https://doi.org/10.1029/2020JB020176)
- [EGMS 2020–2025 release](https://land.copernicus.eu/en/news/product-update-european-ground-motion-service-2025)
- [ERA5 via the Open-Meteo archive API](https://open-meteo.com/en/docs/historical-weather-api)
- [ECMWF IFS pressure levels via the Open-Meteo historical-forecast API](https://open-meteo.com/en/docs/historical-forecast-api)
- [Chronos-2 model card](https://huggingface.co/amazon/chronos-2) and [chronos-forecasting](https://github.com/amazon-science/chronos-forecasting)
- [NASA JPL OPERA TROPO](https://www.jpl.nasa.gov/go/opera/products/tropo-product/)
- [Fattahi and Amelung, DEM error in InSAR time series](https://doi.org/10.1109/TGRS.2012.2227761)
- [De Zan et al., soil moisture and interferometric phase](https://elib.dlr.de/80946/)
- [Ocnele Mari salt mine field case study](https://www.igipz.pan.pl/tl_files/igipz/ZGiHGiW/sgcb/sgcb_40/sgcb_40_08.pdf)
