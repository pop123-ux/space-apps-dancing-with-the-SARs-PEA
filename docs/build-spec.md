# Dancing on Salt: Build spec and plan

Version 1, Sat 14 Nov 2026. This is the companion to [overview.md](overview.md). The evidence it rests on is the advisor's rehearsal, summarised in [rehearsal.md](rehearsal.md), and the data notes in [data.md](data.md).

It covers what each of the six roles builds, in what format, with which fixed numbers, and when it hands off. It exists so the hours go to building, not debating. It contains no code. Every role's Claude Code session works from it through [../prompts/build.md](../prompts/build.md). The same steps laid out hour by hour, one column per role, are in [schedule.md](schedule.md).

**How decisions work here.** Only D-001 and D-002 are locked. Everything else in "Decisions to fix by hour 2" is **proposed**. The team reviews it at the hour-2 checkpoint, and from then on it is frozen: nobody changes a cut, threshold, window or test after seeing a result. Any later change goes in the change log at the end of this file, with a reason that comes from a test, not from a result. Day-to-day choices go in [../DECISIONS.md](../DECISIONS.md).

## Decisions

### Locked

| ID | Decision | Why |
| --- | --- | --- |
| D-001 | **Ocnele Mari is the only site.** Praid and Slănic, from the advisor's deck and kit, are out of scope. | Our hometown story, done well at one site. |
| D-002 | **The map opens zoomed on the Ocnele Mari area:** the Google Maps view at 45.086281° N, 24.2704806° E, zoom 13. When the user zooms out, Romania shows as deliberately blurred, de-emphasised context, not data. | Only our area of interest matters on the map. |

### To fix by hour 2 (proposed)

**Data and grid** (02, 03)

| Decision | Proposed value | Why |
| --- | --- | --- |
| Product | NISAR L2 GUNW, frequency A, HH, from the `NISAR_L2_GUNW_BETA_V1` and `NISAR_L2_GUNW_PROVISIONAL_V1` collections, keeping the newest processing of each pair. | These are the only collections with pairs over the town: 4 BETA and 18 PROVISIONAL (CMR, 14 Nov 2026). The 4 BETA pairs are 129A's winter pairs, so mixing collections cannot be avoided; it is stated on the page. |
| Pair list | The 22 pairs in [../data/scenes/ocnele_mari_gunw.csv](../data/scenes/ocnele_mari_gunw.csv). | Checked against CMR on 14 Nov 2026. |
| Analysis window | 50 × 50 km centred on 45.088° N, 24.290° E, on each track's own 80 m UTM grid. | It needs room for stable ground and the stations (VLC1 is 7 km away, HORE 24 km). |
| Valid pixel | The mask is read as uint32. A pixel is kept when bits 0 to 7 say land in both subswaths and bits 8 to 23 are zero; bit 24 (ionosphere interpolated) does not reject. It must also lie in the largest connected component and have coherence ≥ 0.35 in that pair. | A naive decode dropped 98 % of the 094D window in the rehearsal. Other components can be off by 2π, which is 12 cm. |
| Ionosphere | Subtract `ionospherePhaseScreen` wherever it is present, and record per pair whether it was used. | It ships in the product but is not applied. |
| Troposphere | One elevation slope per pair, fitted on stable ground against Copernicus GLO-30, then removed. | Without it, 094D's rate tracked elevation at −8.6 mm/yr per 100 m in the rehearsal. |
| Phase to millimetres | mm = −phase · λ / 4π, so positive means towards the satellite. **The sign is tested (T3), never assumed.** | The sign is not yet confirmed on real data. |
| Salt zones | The four circles in `common.py`, radius 250 to 300 m, from the advisor kit, named after the INFO.md sub-zones by 03 with 01. Stable ground lies outside the zones plus 3 km. | They are the units we report. |

**Time series and rates** (03)

| Decision | Proposed value | Why |
| --- | --- | --- |
| Method | Decision O-05: MintPy, or our own small-baseline inversion. Either one writes the same `ts.npz`. | The rehearsal used its own inversion; the deck proposed MintPy. |
| Rate | A straight line through the dates, with one offset per group of connected dates and no annual term below 1.5 years of span. | A line fitted to the pairs counts each date's atmosphere many times: in the rehearsal's synthetic test the error went from 2.8 to 14.6 mm/yr. A free annual term moved a synthetic bowl from −105 to −130 mm/yr. |
| Windows | 129A is one fit with two groups (7 Nov 2025 to 18 Jan 2026, and 23 Jun to 21 Oct 2026). 094D covers 20 Jun to 18 Oct 2026. Up and east are solved only on the common window, 20 Jun to 21 Oct 2026. | Mixing different months into one 2 × 2 solve mixes seasons. |
| Uncertainty | σ from the fit, reported as a lower bound. Zone medians get a 95 % interval from 1,000 bootstrap draws that resample dates, with seed 2026. | The atmosphere is the dominant error, and it lives per date. |
| What gets a number | A zone rate is shown as a number only when its 95 % interval excludes zero. Pixels with \|rate\| < 2σ are greyed out. | The per-pixel scatter was 37 to 51 mm/yr in the rehearsal, against a signal of about −25 mm/yr at most. |

**Tie and checks** (04, 05)

| Decision | Proposed value | Why |
| --- | --- | --- |
| Frame | Eurasia-fixed for the model, the stations and the tie. | 25 mm/yr of plate motion can show up as about 10 mm/yr in a line of sight if frames are mixed. |
| Tie | NISAR minus EuVeM2022 projected to LOS, on stable pixels with coherence ≥ 0.4, outside the zones plus 3 km and more than 1 km from any station. One offset, or a plane if it cuts the scatter by more than 10 %. 3σ outliers removed twice. | The way EGMS calibrates its own product. The 0.1° model fixes level and slopes only. |
| Model swap | EuVeM2022 against the EGMS GNSS model; the difference between the two ties is the model's share of the error. | Decision O-06; "rigid plate" is the fallback second model. |
| Sign check | The zone median LOS rate is below −2 mm/yr on every track. | Positive means a sign error. |
| Station check | \|NISAR − GNSS\| ≤ max(2 mm/yr, 2σ combined), per LOS. The tolerance is shown in every pin. | The rehearsal's tolerances were 35 to 60 mm/yr: an "agree" that big must be visible. |
| EGMS check | The median of NISAR up minus EGMS up is below 1.5 mm/yr in absolute value, on EGMS points with \|v\| < 1.5 mm/yr outside the zones plus 500 m. | The rehearsal reached +6.4 mm/yr after the troposphere fix, so this check is a real test. |
| Closure | Ratio of 12-day to 24-day rates between 0.8 and 1.2 if triplets exist; otherwise reported as "not tested". | There are 0 triplets in the GUNW stack (decision O-07). |
| Second radar | The Sentinel-1 zone rate over the same months agrees with NISAR's within the errors. | It is the independent check the deck promised. |

**The page** (06, 01)

| Decision | Proposed value | Why |
| --- | --- | --- |
| Opening view | D-002. | Locked. |
| Slider | One frame per acquisition date per track. No frames across gaps: 18 Jan to 23 Jun 2026 shows "no data". | We never interpolate data we do not have. |
| Colours | RdBu diverging, red = sinking or moving away, with a fixed symmetric scale per layer. Never red and green alone. | Colour-blind safe. |
| Pins | NISAR against GNSS per track, with the tolerance, an agree flag and a reason. A red pin means they disagree. | Honest pins, as the deck promised. |
| Labels | "Simulated, not data" whenever `synthetic` is true. "NISAR beta/provisional products" always. | Judges trust a map that names its limits. |
| Numbers | Every number on the page, in the video and in the submission comes from `products/ocnele_mari/`. Before submitting, `___`, `TODO`, `TBD` and `computing` appear nowhere in the page, `SUBMISSION.md` or the captions. | Honest numbers, no silent placeholders. |

## File contracts

Roles hand each other files, never notebooks. Internal hand-offs live in `data/work/ocnele_mari/` (git-ignored). The page reads only `products/<site>/`, which is committed. "Ready by" is in hours after hour 0, and is proposed.

| File | Made by | Used by | Contents | Ready by |
| --- | --- | --- | --- | --- |
| `data/scenes/ocnele_mari_gunw.csv` | done (CMR, 14 Nov) | 02 | The 22 pairs: collection, track, frame, dates, days, granule, URL | done |
| `refs/model_euvem.csv`, `refs/stations.csv` | 04 (`refs.py`) | 04, 05 | Model grid (lon, lat, ve, vn, vu, se, sn, su) and station rates, Eurasia-fixed, mm/yr | 6 |
| `refs/egms_up.csv` | 05 | 04, 05 | EGMS L3 Ortho Up points (lon, lat, v) cut to the window, period recorded | 6 |
| `<track>/meta.json`, `geom.npz`, `dem.npz` | 02 (`fetch.py`) | 03, 04, 05 | Grid; LOS unit vectors (target to sensor); elevation | 4 |
| `<track>/<ref>_<sec>.npz` | 02 (`fetch.py`) | 03 | Phase in radians (ionosphere removed, NaN = masked), coherence, QA fields | 6 |
| `<track>/ts.npz` | 03 (`stack.py`) | 04, 05, 06 | dates, cum (mm), vel, vel_sig, rate12/rate24, gaps, pair_days, coh_mean | 14 |
| `<track>/cal.npz` | 04 (`calibrate.py`) | 03, 05, 06 | vel_cal, cum_cal, model_los, tie mask | 20 |
| `up_east.npz` | 03 (`split.py`) | 05, 06 | up, east, sig_up, sig_east on the common window, with a note | 26 |
| `s1/` | 05 (`hyp3_order.py`) | 05 | Sentinel-1 HyP3 products and `jobs.json` | ordered at 1, ready about 8 |
| `products/<site>/calib.json` | 04 | 05, 06 | The tie per track and the model-swap number | 20 |
| `products/<site>/checks.json`, `checks.md`, `stations.geojson` | 05 (`validate.py`) | 06, 01 | Every check (pass, warn, fail or info) and the honest pins | 28 |
| `products/<site>/manifest.json`, `*.png`, `frames/`, `series.json`, `up.tif`, `east.tif`, `products/index.json` | 06 (`export.py`) | the page, 01 | Below | first real set 18, final 40 |
| `products/mock/` | 06 (`mock_products.py`) | the page | Invented values in the same shape | done |

**`manifest.json`:**

- `site`, `name`, `story` (01's sentence), `synthetic`, `note`, `built`.
- `bounds` `[[S, W], [N, E]]` and `center`.
- `view` `{center, zoom, min_zoom, context: "romania-blurred"}`, which carries D-002.
- `layers` `[{id, label, png, units, vmin, vmax}]`.
- `frames` `{track: {dates, pngs, vmin, vmax, units, direction, gaps: [[from, to]]}}`.
- `checks` `{pass, warn, fail, info}`, and `credits`.

**`series.json`:** `[{id, label, kind: zone|station, lat, lon, up, series: {track: {dates, mm, rate}}}]`.

**`stations.geojson`:** a FeatureCollection of points. Each has `station`, `source`, `t_end`, `dist_km`, `tracks {track: {nisar, gnss, diff, tol}}`, `agree` (true, false or null), `reason`, `nisar_up` and `gnss_up`.

**`checks.json`:** `[{id, status: pass|warn|fail|info, title, detail, value}]`.

**`calib.json`:** `{model, tracks: [{track, direction, method, offset_mm_yr, slope_east_mm_yr_per_10km, slope_north_mm_yr_per_10km, n_tie_pixels, residual_std_mm_yr, residual_mad_mm_yr, model_los_mean_mm_yr, swap_delta_mm_yr}]}`.

`checkpoint.py` enforces this contract, and `mock_products.py` writes it. Once frozen at hour 2, a change needs 01 and 06 and goes into `checkpoint.py`, `mock_products.py` and the page in the same PR.

## Machines

Everyone works on their own laptop. 02 streams the window on one machine: about 58 MB per pair and 1.3 GB in total. 02 shares `data/work/ocnele_mari/` with the team through a shared folder, or each person streams their own copy in about 30 minutes (decision O-16). Raw files never go in git. Nothing needs a GPU, and nothing heavier than NumPy runs.

## 01 · Lead and story (Mario)

01 owns scope, the cut lines, the checkpoints, the story, the video and the submission. Files: `checkpoint.py`, `README.md`, `STATUS.md` (the team view), this spec's change log, and `SUBMISSION.md` (created at hour 30).

1. **Hour 0 to 2.**
   - Set hour 0 and `EVENT_TZ` in `STATUS.md` (O-04).
   - Read the 13 Nov guide aloud: prior work, format, judging. Settle O-02 and O-03.
   - Run the hour-2 review of the proposed decisions above with the team, and freeze the contract with 06.
   - Check that everyone has an Earthdata login and has run `pytest -q`.
2. **Hour 2 to 6.** Settle the story framing (O-01). Write the story stops, one sentence each, and the first ten seconds of the video. Reassign the freed Praid slots (O-15).
3. **Checkpoints at hours 12 and 24.**
   - Run `python checkpoint.py ocnele_mari` and read every WARN and FAIL aloud.
   - Give each one an owner and a verdict (fix, cut or explain), and write them in `STATUS.md`.
   - The advisor joins.
4. **Hour 18 to 30.** Video script, then a rough cut on the mock or demo site with the banner visible.
5. **Hour 30 to 40.** `SUBMISSION.md`: name, summary, demo link, details, data, AI use (section 1 of [../AI-DISCLOSURE.md](../AI-DISCLOSURE.md)), prior work and credits (from [../CITATIONS.md](../CITATIONS.md)).
6. **Hour 40.** Freeze: no number changes after this. Then the final video, the project page, and the submission (a person clicks).

Watch out: our copy of the deck still says −250 mm/yr. Never quote it.

## 02 · NISAR data (Alexandru and Eric)

02 gets every pair over the town onto disk, cut to the window, with the ionosphere removed and bad pixels masked. File: `fetch.py`.

1. **Hour 0 to 2.**
   - Earthdata token into `.env` (prompts/setup.md).
   - `search()`, then `python fetch.py ocnele_mari --list` must list the 22 pairs in `data/scenes/ocnele_mari_gunw.csv` (T2).
2. **Hour 0 to 1.** T1: stream one pair on the venue network and record MB and seconds.
3. **Hour 2 to 6.**
   - `read_pair()`: HTTP range reads, the mask rule, the ionosphere subtraction and the largest connected component.
   - Fetch both tracks and write a QA line per pair: `valid_share`, `iono_used`, `iono_std`, `iono_interp`.
   - Open one pair and show it to the team.
4. **Hour 6 to 12.** `write_dem()`. Then `synthetic()`, the known-answer stack with the real date pattern and its gap, for T5 and T6.
5. **Tier 3.** GSLC pairs for closure, if O-07 keeps it.
6. **Hour 30 to 40.** Help 06 with frame sizes.

Watch out: the mask layer is a bitfield (see [data.md](data.md)). The first pair fixes the grid, so if ASF reprocesses a pair onto another grid, stop. The token goes to ASF only.

## 03 · InSAR analyst (Alexandru and Eric)

03 turns the pairs into displacement and rates, honestly, then up and east. Files: `stack.py` and `split.py`.

1. **Hour 0 to 4.** O-05, the method. Read 02's hand-off. Look at the first real pairs as soon as they exist.
2. **Hour 6 to 14.** `stack.py`: the troposphere slope, the stable-ground reference, the inversion, the rate with group offsets, and σ. Run T3 (the sign) with 05 and T4 (the troposphere) on the first rate map.
3. **Hour 14 to 20.** Zone medians with bootstrap intervals. Name the zones with 01.
4. **Hour 20 to 26.** `split.py` on the common window.
5. **Hour 26 to 40.** Grey out \|rate\| < 2σ with 06. Error maps. Freeze at hour 40.
6. **Tier 3.**
   - The GUNW `radarGrid` weather-model troposphere against the elevation slope.
   - Closure from GSLC pairs.
   - An ML/AI component (O-08), only if it beats a simple baseline on held-out checks.

Watch out:

- The tracks disagreed in the rehearsal: −4.6 mm/yr on 129A against +27.5 mm/yr on 094D in the zones. Find out why before trusting either.
- North is ignored in the split.
- σ is a lower bound.

## 04 · Geodesist (Matei)

04 puts the radar into a real frame, using open references only, and keeps the stations out of the tie. Files: `refs.py` and `calibrate.py`.

1. **Hour 0 to 6.**
   - `refs.py`: the EuVeM2022 Romania grid, NGL MIDAS (`midas.EU.txt`) and the published rates.
   - Fill the NaN verticals in `common.PUBLISHED` (VLC2, HORE) from Muntean et al. 2026 Table S3, by eye.
   - `synthetic()` stand-ins, including one station that lies (+6 mm/yr up).
2. **Hour 14 to 20.** `calibrate.py`: the model to LOS, the tie mask, offset or plane, and `calib.json`. Plot NISAR minus model on the tie pixels.
3. **Hour 18 to 30.** The model swap with the EGMS GNSS model (O-06), and the EGMS stable-ground cross-check with 05 (T8).
4. **Hour 30 to 40.** The final tie and the frame paragraph for the page. Freeze at hour 40.

Watch out:

- EuVeM2022 data end in 2021 and NGL MIDAS near the town in 2018 to 2020; both assume steady motion since.
- A plane hints at residual ionosphere: compare runs with and without the layer.
- No ROMPOS data.

## 05 · Validator (Paul)

05 proves or disproves the numbers with things nobody tuned. Nobody else edits `validate.py`, and 05 edits no science script. Files: `validate.py`, `hyp3_order.py` and [validation-log.md](validation-log.md).

1. **Hour 0 to 1.** Order Sentinel-1 on HyP3 for 1 Nov 2025 to 31 Jan 2026 and 15 Jun to 31 Oct 2026, both geometries, short and long pairs. It queues for hours. Log the jobs.
2. **Hour 1 to 6.**
   - Cut the EGMS L3 Ortho Up 2020 to 2024 tile to `refs/egms_up.csv`.
   - Screen every station: roof, mast or pillar? What does EGMS show on its own building?
3. **Hour 6 to 18.** The Sentinel-1 zone rates for the same months.
4. **Hour 18 to 30.** `validate.py`, checks 1 to 8 (see the table above and the docstring). Explain every WARN.
5. **Hour 30 to 40.** Final agree flags; red team with the advisor.
6. **Hour 40 to 48.** Rerun every check on the frozen build and log it.

Watch out: HAR1's mast swings 38 mm a year, so stations can lie. A station series that ended in 2018 to 2020 assumes steady motion since; say so in the pin.

## 06 · App developer (Darius)

06 builds one page anyone can open on a phone. Files: `export.py`, `mock_products.py` (works) and the page (`index.html` and its assets, which 06 creates).

1. **Hour 0 to 2.** `python mock_products.py`, then start the page on `products/mock/`. Freeze the contract with 01.
2. **Hour 2 to 6.**
   - The page live on GitHub Pages with the mock site, so the first deploy is not the last.
   - The basemap and the Romania blur (O-09).
3. **Hour 6 to 18.** Map (D-002), slider with honest gaps, legend, units, both labels. `export.py` as soon as `up_east.npz` exists.
4. **Hour 18 to 30.** Pins, story mode, phone layout, keyboard use, a colour-blind check (T9).
5. **Hour 30 to 40.** Captions, accessibility, the demo link.

Watch out: Leaflet image overlays are axis-aligned, so resample to lon/lat for the PNGs. The GeoTIFFs keep the UTM grid.

## Done means

A tier is done when every box is ticked, not when the code runs. Tick them during the event.

**Tier 1 (a complete submission; numbers by hour 30, frozen at hour 40)**

- [ ] Both tracks streamed, with a QA line per pair (02).
- [ ] `ts.npz` per track; T3's sign result written down (03).
- [ ] The tie per track in `calib.json` (04).
- [ ] `checks.json` covers every check, and every WARN and FAIL is explained (05).
- [ ] `products/ocnele_mari/` passes `checkpoint.py`. The page is live with the D-002 view, the slider with honest gaps, the pins and both labels, and it works on two phones (06).
- [ ] Story stops, video, project page, AI use, prior work and credits (01).

**Tier 2**

- [ ] Up and east on the common window (03).
- [ ] Zone medians with bootstrap intervals in `series.json` (03, 06).
- [ ] The Sentinel-1 comparison in `checks.json` (05).
- [ ] The model swap number in `calib.json` (04).
- [ ] Story mode and phone polish (06).

**Tier 3**

- [ ] GSLC closure pairs (02, 03).
- [ ] The weather-model troposphere (03).
- [ ] An ML/AI component that beats its baseline on held-out checks (02, 03, O-08).
- [ ] A GCOV backscatter angle (O-01).

## Unknowns to settle in the first hours

Each maps to a test in [../prompts/early-tests.md](../prompts/early-tests.md), and each has a fallback that keeps the plan intact.

| Assumption | Test | If it is wrong |
| --- | --- | --- |
| The venue network streams a track in under 10 min | T1 | Cut line at hour 6: download one track in full |
| Our search finds the same 22 pairs | T2 | Use `data/scenes/ocnele_mari_gunw.csv` directly |
| The mask rule keeps most of the window (the rehearsal kept 85 to 94 %) | T2 | Recheck the bit decode before anything else |
| The phase sign: the zones sink on 129A | T3 | Investigate (sign, unwrapping, atmosphere). Never flip the sign to make a check pass. Report it |
| The troposphere slope brings NISAR to within a few mm/yr of EGMS on stable ground | T4 | Weather-model cubes (Tier 3); say so on the page |
| Group offsets across the gap recover a synthetic truth | T5 | Fit each window separately and say so |
| Summer-only data bias the rate by under 20 % | T6 | Report 094D as "summer to autumn only" |
| Holding stations out of the tie makes a measurable difference | T7 | Report it either way |
| The model swap changes LOS rates by under 1 mm/yr | T8 | Report the model's share as an error term |
| The page works on two phones | T9 | Collapse to map, slider and one card |
| HyP3 jobs finish within about 8 hours | T10 | Sentinel-1 moves to Tier 3 |

## Open team decisions

| ID | Question | Options | Owner | By hour |
| --- | --- | --- | --- | --- |
| O-01 | The story framing, given the rehearsal verdict | (a) "The honest test": what NISAR's first months can and cannot see at a slow salt site, at zone level. (b) A subsidence story, if zone intervals exclude zero. (c) A GCOV backscatter angle at Ocnele Mari, alone or alongside | 01, all | 2 |
| O-02 | Does the 13 Nov guide allow the advisor kit as prior work, and how is it declared? | Read the guide | 01 | 1 |
| O-03 | Adopt the kit's code, or rebuild in the stubs? | Adopt and declare; rebuild and compare; mixed per role | all | 1 |
| O-04 | Hour 0, `EVENT_TZ`, the submission deadline | Fill into `STATUS.md` | 01 | 0 |
| O-05 | The time-series method | MintPy or our own inversion | 03 | 4 |
| O-06 | The second velocity model | EGMS GNSS model (CSV link still to be found) or a rigid plate | 04 | 18 |
| O-07 | Closure test | GSLC pairs (11 dates on 094D, 15 on 129A), or declare it untested | 02, 03 | 18 |
| O-08 | An ML/AI component, and how it is tested | Learned troposphere, bad-pair or unwrapping detection, uncertainty calibration; only if it beats the baseline | 02, 03 | 12 |
| O-09 | Basemap and the Romania blur | Tile source; CSS blur or opacity below a zoom; an outline only | 06 | 6 |
| O-10 | Accept the file contracts above as written | | 01, 06 | 2 |
| O-11 | Window size | 50 km (kit) or smaller; the D-002 view is independent | 02, 04 | 6 |
| O-12 | HAR1 in the app, or only in the video | | 01 | 24 |
| O-13 | May the app quote Muntean et al. 2026 supplement values? | Ask INFP; else "see paper" | 01 | 24 |
| O-14 | Why is there no NISAR over Romania from mid-January to late June 2026? | ASF or NISAR forum | 02 | 24 |
| O-15 | The slots freed by dropping Praid (02 and 03, hours 6 to 30) | Zone series, closure, Sentinel-1, O-08 | 01 | 6 |
| O-16 | How `data/work/` is shared | A shared folder, or everyone streams their own | 02 | 4 |
| O-17 | Licence | MIT now (repo owner); Space Apps distributes submissions under Apache 2.0, so check the 2026 guide | 01 | 30 |

## Change log

The Lead (01) records here every change to a decision above after the hour-2 review. The reason must come from a test, not from a result.

| Date and time | Decision changed | From | To | Test and reason |
| --- | --- | --- | --- | --- |
