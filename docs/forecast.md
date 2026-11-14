# Zone 4 forecast and environmental screening

**Owner:** 03 · InSAR analyst (Alexandru, Eric)

## Current app and model

The entry point is [index.html](../index.html). It imports [app/main.js](../app/main.js), which loads `products/index.json` and the selected site's products. Use **Zones → Sentinel-1 → 029A → July–October → Baseline** for the January scenario. Model selection changes the dashed path and endpoint. NISAR still opens in Coverage until its team displacement products are ready. EGMS appears as reported history in Agreement. A forecast card requires a matching observation series.

- [CPU script](../sentinel1/scripts/forecast.py) and [export](../products/ocnele_mari/forecast.json).
- Zone 4, 029A, 16 epochs, 29 summer interferograms and 34 connected pixels. Latest fitted acquisition 5 October 2026. The requested 1 January 2027 endpoint is 88 days beyond it. Six later catalog dates through 10 November need processing before they can update the fit.
- Thirty-day rolling-cutoff MAE over four overlapping windows: persistence 4.19 mm, Theil–Sen 5.53 mm, Matérn Gaussian process 3.95 mm. These scores rank the models in the experiment and do not validate 88-day extrapolation. January LOS endpoints are −7.89, −15.08 and −13.78 mm respectively. There is no calibrated prediction interval.
- Data and panel checks on this branch: verified static entry paths and real-product overlay references; loaded the actual JSON and rendered the forecast panel in a JavaScript harness, including model switching and scenario gating. Full browser verification remains pending because Chromium was blocked by the workspace runtime.

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

## References

- [Hill et al., Sentinel-1 deformation forecasting](https://doi.org/10.1029/2020JB020176)
- [NASA JPL OPERA TROPO](https://www.jpl.nasa.gov/go/opera/products/tropo-product/)
- [Fattahi and Amelung, DEM error in InSAR time series](https://doi.org/10.1109/TGRS.2012.2227761)
- [De Zan et al., soil moisture and interferometric phase](https://elib.dlr.de/80946/)
- [Ocnele Mari salt mine field case study](https://www.igipz.pan.pl/tl_files/igipz/ZGiHGiW/sgcb/sgcb_40/sgcb_40_08.pdf)
