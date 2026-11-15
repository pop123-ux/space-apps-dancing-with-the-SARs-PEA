# Handoff for roles 02 and 03, end of day 1

**Owner:** 02 · NISAR data and 03 · InSAR analyst (Alexandru, Eric)

Written 15 Nov 2026, 00:50 Europe/Bucharest, at the end of the 02/03 Claude Code session, for whoever continues 02/03 (Alexandru in Matei's session for now). Everything below is on `main`.

## Where things stand

| Area | State | Where |
| --- | --- | --- |
| Page | Layout v4 from the team sketch: toolbar, map, right menu column, full-width timeline. Phone: drawer above the timeline | `index.html`, `app/`, [ui.md](ui.md) |
| Sentinel-1 | Jul to Oct fitted on 029A and 007D (16 dates each; 7 processing scenarios incl. weather-model troposphere). Jan to Oct (49 dates) exported as a second window and offered inside NISAR's gap | `sentinel1/`, [forecast.md](forecast.md) |
| NISAR | Own pipeline works end to end: `fetch.py` (range reads, 22 pairs), `stack.py`, `calibrate.py` (04), `split.py`. 129A on the page (T3 pass, −10.1 mm/yr zones). 094D held "under review" (T3 fail, +23.5 mm/yr, valley-wide signal, not unwrapping) | [data.md](data.md), `notebooks/03/t3_*.json` |
| Gap Jan to Jun 2026 | NISAR has none; Sentinel-1 029A covers it side by side (never spliced: different geometry and reference) | [ui.md](ui.md) |
| Forecast | Chronos-2 only (zero-shot, CPU), date slider to 1 Jan 2027: −3.9 mm LOS, 80 % range −11.3 to +15.2. Other four models kept only as backtest baselines. NISAR Oct check −5.9 vs +1.2 mm, within NISAR noise | [forecast.md](forecast.md), `sentinel1/scripts/forecast_chronos.py` |
| Validator | `validate.py` merged (written by 02/03, approved by Alexandru): 5 pass, 5 warn, 3 fail, 6 info | `products/ocnele_mari/checks.md` |
| Hosting | Vercel config in the repo; the project import is done by a person | [deploy.md](deploy.md) |

## How to rebuild the products (data are git-ignored, so a new machine starts empty)

1. `python fetch.py ocnele_mari` (needs an Earthdata token: `EARTHDATA_TOKEN`, or the cloud session's proxy credential for `nisar.asf.earthdatacloud.nasa.gov`; about 730 MB).
2. `python refs.py ocnele_mari`, `python stack.py ocnele_mari`, `python calibrate.py ocnele_mari`, `python split.py ocnele_mari`.
3. `python export.py ocnele_mari`, then `python validate.py ocnele_mari`, then `python export.py ocnele_mari` again (it copies the check counts into the manifest).
4. Forecast: `cd sentinel1/scripts`, `python forecast.py RAW029A ../../products/ocnele_mari/forecast.json --as-of 2026-11-14 --end-date 2027-01-01 --rain-csv ../../notebooks/05/z4_screen_inputs.csv` (RAW029A = the summer HyP3 ZIPs, see `sentinel1/provenance/`), then in an environment with `chronos-forecasting` and CPU torch: `python forecast_chronos.py ../../products/ocnele_mari/forecast.json --janoct ../analysis_jan_oct/summary.json --default --weather ../analysis/chronos_weather.json --nisar ../../products/ocnele_mari/series.json`.
5. `export.py` rewrites the Sentinel-1 PNGs byte-differently but pixel-identically: restore them with `git checkout -- products/ocnele_mari/s1/` if only those changed.

## Open, in priority order

1. **094D:** decide whether a local (1 to 3 km) reference is acceptable for T3, or test another way. Until then Compare and Agreement stay off (`manifest.compare`).
2. **Stations:** VLC1/VLC2 disagree with NISAR 129A (+3.9 vs −0.6/+0.3 mm/yr); the tolerance treats neighbouring pixels as independent, so it is too tight. Revisit with a correlated-noise σ.
3. **Sentinel-1:** done 15 Nov: six new dates per track to 10 Nov, forecast horizon 52 days, Jan to Oct job links and checksums recovered ([sentinel1/analysis_jan_nov/README.md](../sentinel1/analysis_jan_nov/README.md)). Next date: 007D 15 Nov; rerun with `.github/workflows/sentinel1-refit.yml` after adding jobs to `sentinel1/provenance/hyp3_jobs_jan_nov.csv`.
4. **Zone 3:** no continuous series on either radar.
5. **Stale branches:** eight merged branches still need deleting by a person (this session could not delete branches).
6. **Slides and SUBMISSION.md** (01) and the story sentence (`manifest.story` is still TODO(01)).
