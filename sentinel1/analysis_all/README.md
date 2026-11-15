# Sentinel-1 fit, May 2025 to November 2026

**Owner:** 03 · InSAR analyst (Alexandru, Eric)

Written 15 Nov 2026. Every acquisition ASF's catalogue holds on the two bursts the stack uses (029_060407_IW2 and 007_013694_IW2, VV) from May 2025 to 15 Nov 2026. That is 374 HyP3 Burst InSAR jobs: the 214 earlier ones plus 160 ordered on 15 Nov 2026 by `../scripts/order_all.py` (6- and 12-day pairs, same job type and parameters, 10×2 looks, water mask). All 160 new jobs succeeded.

| Track | Pairs | Dates | First to last | Date groups | Town covered |
| --- | ---: | ---: | --- | ---: | ---: |
| 029A | 185 | 94 | 6 May 2025 to 10 Nov 2026 | 1 | 11 % |
| 007D | 189 | 96 | 5 May 2025 to 15 Nov 2026 | 1 | 0 % |

Fitted by `../scripts/fit.py` on the same grid with the processing runs baseline, stricter coherence, west and east reference, and fitted elevation correction. **There is no weather-model run in this window.** The weather service (Open-Meteo) was not reachable from the machine that ran the fit, so `tropo.json` is missing. Earlier windows keep their weather-model runs.

Zone change over the whole window, 029A baseline, mm (line of sight, positive toward the satellite), with pixel counts: Zone 1 −9.7 (4), Zone 2 −4.9 (36), Zone 3 no series, Zone 4 −5.9 (22). 007D: no zone pixel stays connected through both winters, so the page shows "Insufficient continuous coverage" there, as in January to November.

Reproducible from the repository: `../provenance/hyp3_jobs_all.csv` lists every job with its link (links expire about 30 days after processing; after that, resubmit the same definitions), and `../provenance/raw_SHA256SUMS_all` has the SHA-256 of every product as downloaded. The grids are in `../assets_all/` (`scripts/restore_grids.py`). The Chronos-2 predictions were not rerun on this window: the forecast is indicative for the demo.
