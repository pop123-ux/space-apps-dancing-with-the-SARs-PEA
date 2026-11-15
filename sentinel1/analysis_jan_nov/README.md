# Sentinel-1 fits to 10 November 2026

**Owner:** 03 · InSAR analyst (Alexandru, Eric)

Written 15 Nov 2026. Two fits, both from ASF HyP3 Burst InSAR (IW2, VV, 10×2 looks, water mask), by the group-aware `scripts/fit.py`, with the same six processing runs as the July to October fit (baseline, stricter coherence, west and east reference, fitted elevation correction, weather-model troposphere).

| Folder | Window | Pairs and dates per track | Use on the page |
| --- | --- | --- | --- |
| `analysis_jan_nov/` (this folder) | 1 Jan to 10 Nov 2026 (029A), 6 Jan to 9 Nov (007D) | 107 pairs, 55 dates | Replaces January to October in the window menu and inside NISAR's January to June gap |
| `analysis_jul_nov/` | 7 Jul to 10 Nov (029A), 6 Jul to 9 Nov (007D) | 41 pairs, 22 dates | The summer pair design plus the six new dates; the forecast's window |

## What was added

Six new acquisitions per track after the January to October fit: 029A on 11, 17, 23 and 29 Oct and 4 and 10 Nov; 007D on 10, 16, 22 and 28 Oct and 3 and 9 Nov. Each new date was paired with the one and two acquisitions before it (6- and 12-day pairs, the pattern of the existing stack), so 12 jobs per track. All 24 were ordered on HyP3 on 15 Nov 2026 and succeeded.

## Reproducible from the repository

`../provenance/hyp3_jobs_jan_nov.csv` lists all 214 jobs (190 earlier, 24 new): job ID, granule dates, product file name, size and download link. `../provenance/raw_SHA256SUMS_jan_nov` has the SHA-256 of every product as downloaded. The 58 summer links match `asf_downloads.json`. The links expire on 29 and 30 Nov 2026; after that, resubmit the same job definitions on HyP3.

The workflow `.github/workflows/sentinel1-refit.yml` downloads the products on a GitHub runner (`scripts/fetch_jobs.py`), refits, packs the grids and commits the results. Before fitting the new dates, it refits the 190 January to October products and compares the result with the committed `analysis_jan_oct/` (`reproduce_jan_oct.json`): same dates and pixels, zone values equal to 1e-15 mm, grids equal to 2e-6 mm on both tracks. So the earlier fit, which came from an outside bundle, is now reproduced from its own products.

The weather-model delays (`tropo.json`) cover all 110 acquisition dates. For the 98 dates already in `analysis/tropo.json` they are identical (0.0 mm difference).

## Results, change over the window in mm (line of sight, positive toward the satellite)

July to November 2026 (`analysis_jul_nov/`). The range is across the six processing runs.

| Zone | 029A baseline (pixels) | 029A range | 007D baseline (pixels) | 007D range |
| --- | ---: | --- | ---: | --- |
| 1 | −5.9 (20) | −5.8 to −6.6 | −5.1 (31) | −2.6 to −6.8 |
| 2 | −5.9 (44) | −5.9 to −7.1 | −1.4 (31) | −3.3 to +1.7 |
| 3 | no series | | −1.6 (39) | −3.5 to +1.5 |
| 4 | −6.6 (31) | −4.4 to −9.1 | −5.3 (67) | −2.6 to −7.1 |
| Outer comparison area | +3.3 | +1.5 to +3.3 | +5.5 | +3.6 to +8.2 |

January to November 2026 (this folder).

| Zone | 029A baseline (pixels) | 029A range | 007D |
| --- | ---: | --- | --- |
| 1 | −9.4 (5) | −13.0 to −0.2 | no series |
| 2 | −7.9 (38) | −11.5 to −3.0 | no series |
| 3 | no series | | no series |
| 4 | −4.5 (26) | −10.3 to +4.2 | no series |

What this says:

- Zone 4 keeps the summer reading with six more dates: away from the satellite on both tracks in every run from July to November. Six dates in October and November do not change that a short-window slope is not a long-term velocity.
- Over January to November, Zone 4 on 029A still changes direction with processing: the fitted elevation correction gives +4.2 mm and the weather-model run −10.3 mm. Not a settled finding.
- 007D still has no salt-zone pixel connected through all 55 dates (winter decorrelation), so the long window shows "Insufficient continuous coverage" there, as before.
- Zone 3 has a 007D series in July to November, but its direction changes with the reference area. It stays "trend inconclusive".

## The forecast

`analysis_jul_nov/forecast_check.json` scores the Chronos-2 forecast the page showed until 15 Nov (issued from data to 5 Oct) against the six new 029A dates, re-inverted with the same summer pair design (31 Zone 4 pixels). Measured change since 5 Oct: +8.0, +4.5, +5.2, +2.4, +4.8 and +3.5 mm. Chronos-2 expected +1.6 to +2.7 mm. All six fell inside its 80 % range, and its average error was 2.5 mm against 4.8 to 6.5 mm for the four simple models. It is one forecast on six dates that share a reference, so it is a check, not a skill score.

`analysis_jul_nov/forecast_from_10nov.json` is the forecast re-issued from data to 10 Nov (`scripts/forecast.py --last-date 2026-11-10`, then `forecast_chronos.py --default`), now on the page: 52 days to 1 Jan 2027 instead of 88. Chronos-2 median −3.85 mm on 1 Jan 2027 relative to 7 Jul 2026, 80 % range −8.49 to +6.17 mm. The backtests on the January to October series are unchanged (30 days 3.49 mm, 88 days 3.81 mm).
