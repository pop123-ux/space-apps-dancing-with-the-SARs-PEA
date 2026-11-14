# Ocnele Mari Sentinel-1 analysis

Inputs are 58 independent ASF HyP3 Sentinel-1 VV Burst InSAR products, 29 each on tracks 029A and 007D. No starter-kit radar observations entered the fit. The four starter-kit zone outlines were used as geographic analysis masks. The two eastern circles overlap.

## Run
Use Python with GDAL, NumPy, pyproj and matplotlib.
Run `python fit.py ZIP_DIRECTORY OUTPUT_DIRECTORY` followed by `python compare.py OUTPUT_DIRECTORY`. Product ZIP filenames should contain the track and both dates as in the job manifest. The manifest is a provenance record and records the ASF product filenames.

## Outputs
- summary.json contains real acquisition dates (YYYYMMDD), displacement referenced to the first epoch, baseline fits, and sensitivity runs.
- Track PNGs show the baseline LOS slope in mm/yr. Negative indicates motion away from Sentinel-1 under the ASF product convention.
- Track NPZs provide 40 m EPSG:32635 grids, bounds ordered xmin, ymin, xmax, ymax, north-up arrays (row 0 is north), epoch displacement, LOS slope, and target-to-sensor east/up look vectors. Unsupported cells are NaN.
- matched_geometry_exploratory.json gives median projections on pixels supported by both tracks. Rates were refit on a common daily interpolation of the two reconstructed time series from July 7 through October 4. Interpolated days are computational samples and carry no independent observations. North motion is assumed zero. The surrounding control drifts, so these components are diagnostic.

## Method
At each pixel and track, solve observed interferogram differences for one displacement per date, with the first date fixed at zero. Use coherence squared as a heuristic weight, filter water and low-coherence observations, keep the connected component shared with the reference pixels for each pair, and require a fully connected date graph. Each pair is zeroed using the median in a surrounding 3–6.5 km reference band. Repeat with a stricter coherence threshold, west/east subsets of the reference band, and a linear elevation correction as a sensitivity test. These historical-geography controls are assumed reference terrain. They are not GNSS-calibrated. The outer 6.5–8 km control drifts and may contain real motion or residual correlated delay.

Linear slopes and Theil–Sen robust slopes are fitted to per-date zone medians. The single-date omission range drops epochs from the trend fit only and is diagnostic, not a confidence interval. Closure diagnostics are summaries across available triplets/pixels; closure cannot exclude atmospheric signals shared by pairs containing the same acquisition. No atmospheric weather-model corrections or external 2026 cross-checks have been applied.

## UI contract
Publish each track independently with dates, units, sign, reference, coverage, and masked values. Plot zone histories from summary.json and show observation-window mm by default. Label mm/yr as an annualized short-window slope. The linear slope times the duration is a fitted change, not the measured endpoint difference. Use explicit no-data states (especially zone 3 on 029A). Show the outer reference comparison alongside zone histories. Keep derived vertical/east rates experimental until the reference and atmosphere sensitivities are resolved.
