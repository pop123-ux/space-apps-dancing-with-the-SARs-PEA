# Validation log (05, Paul)

**Owner:** 05 · Validator (Paul)

This is the hand-kept side of validation. `validate.py` writes the automatic checks to `products/<site>/checks.md`; this file records what the scripts cannot: station screening, HyP3 orders, red-team notes and the frozen-build re-run.

## Sentinel-1 orders (hyp3_order.py)

| When | Pairs (dates, geometry) | Jobs | Account | Status |
|---|---|---|---|---|
| Not needed so far | The main order (58 HyP3 burst pairs, 029A and 007D) was placed and fitted by 02/03, see `sentinel1/provenance/hyp3_jobs.json` | | | Extra Jan to Jun 2026 pairs stay a Tier 3 option |

## Station screening (before any station is trusted)

| Station | Network / source | Distance from the town | Monument (roof, mast, pillar?) | EGMS on its own building | Series ends | Use (held out / context) | Notes |
|---|---|---|---|---|---|---|---|
| VLC1 | NGL MIDAS; NGL daily tenv3 (IGS20) | 6.4 km from the window centre | Not checked yet | −0.2 mm/yr (median of 79 EGMS cells within 500 m, 2020 to 2025) | 2018-12 (1,048 days from 2012-08) | Held out; pin says "assumes steady motion since 2018" | Linear fit to the daily Up series: −1.0 mm/yr (2012 to 2018, IGS20 frame, not Eurasia-fixed; MIDAS is the number to use). Agrees with EGMS within about 1 mm/yr, but the periods do not overlap. Off the bowl, so it tests stable ground only |
| VLC2 | Muntean et al. 2026 | 6.4 km | Not checked yet | −0.2 mm/yr (same 79 cells as VLC1) | 2025 | | vertical still to be read from Table S3 (04). `common.PUBLISHED` gives VLC2 the same position as VLC1 (45.1074 N, 24.3664 E): check whether they share a building or a mast |
| HORE | NGL MIDAS + Muntean et al. 2026 | 24.5 km | Not checked yet | −0.3 mm/yr (71 cells within 500 m) | 2020-03 (821 days from 2012-10) | Held out; "assumes steady motion since 2020" | Daily Up fit −1.5 mm/yr (2012 to 2020). Agrees with EGMS within about 1.2 mm/yr; no time overlap |
| VLC3 | NGL daily tenv3 | 6.4 km | | | 2020-03 (181 days) | Not used | The Up series jumps by about 14 m: a re-installation or a coordinate change. Unusable without editing |
| STOL | NGL daily tenv3 | 70.5 km, outside the window and the EGMS tile | | No EGMS cells (outside tile E54N25) | 2026-10 (248 days in 2026) | Context only | The nearest open station with 2026 data. Up −4.4 mm/yr over 2020-12 to 2025-11, −0.9 mm/yr over its whole record (2017 to 2026): check for equipment changes before quoting it. Under a year of 2026 data is mostly seasonal motion, so it gives no 2026 rate |
| TIMA | NGL daily tenv3 | 91.3 km | | No EGMS cells | 2026-10 (246 days in 2026) | Context only | Up −0.6 mm/yr over 2020-12 to 2025-11, close to EGMS stable ground in our window (−0.5 mm/yr) but 91 km away |

Station list from the NGL station file (`https://geodesy.unr.edu/NGLStationPages/llh.out`, read 14 Nov 2026): 29 stations within 120 km of the town; only STOL and TIMA have data in 2026. No ROMPOS data was used.

## EGMS

`python egms_cut.py ocnele_mari` writes `data/work/ocnele_mari/refs/egms_up.csv` (lon, lat, v), `egms_east.csv` and `egms_meta.json`, and the figures `docs/figures/05_egms_up_rate.png` and `05_egms_zone_history.png`. The zips stay local in `data/egms/`.

| Tile | Period | Points in the window | Cut by | Notes |
|---|---|---|---|---|
| L3 Ortho Up and East–West, E54N25, release 2020_2025_1 (produced 28 Jul 2026) | 2020-12-09 to 2025-11-25, 303 epochs every 6 days | 28,921 cells of 100 m in the 50 × 50 km window | `egms_cut.py` (05), 14 Nov 2026 | Used instead of the 2020–2024 release named in the build spec, because 2020–2025 is newer and covers the same years plus 2025 (see `DECISIONS.md`). Down to 2025-11, so no overlap with NISAR's 2026 dates: it gives the bowl's history, not a 2026 check |

What EGMS shows per zone (`common.py` zones, cells whose centre is inside the circle; stable = outside the zones plus 3 km), checked 14 Nov 2026:

| Zone | Cells | Up, median | Up, fastest cell | Up, total 2020-12 to 2025-11 | East–West, median |
|---|---|---|---|---|---|
| z1 | 2 | −3.9 mm/yr | −4.3 mm/yr | −21 mm | −4.1 mm/yr |
| z2 | 5 | −2.5 mm/yr | −4.3 mm/yr | −9 mm | −3.3 mm/yr |
| z3 | 6 | −18.9 mm/yr | −22.6 mm/yr | −89 mm | +0.2 mm/yr |
| z4 | 10 | −3.1 mm/yr | −8.1 mm/yr | −15 mm | +4.9 mm/yr |
| stable | 27,972 | −0.5 mm/yr | | −3 mm | −0.1 mm/yr |

- **z3 is the bowl.** It sinks steadily, with no sign of slowing between 2020 and 2025. If that continues, NISAR and Sentinel-1 should see about −19 mm/yr there in 2026; much more means a new event or a processing error.
- z1, z2 and z4 hold only 2 to 10 cells each, so their medians are fragile. Several fast cells lie between z3 and z1 and just north of z1, outside every zone circle: 01 and 03 may want to check the zone positions against this map.
- What this cannot tell us: anything after 2025-11, motion inside 100 m cells, or north–south motion (the Ortho split assumes none). The cell uncertainties EGMS reports (0.0 to 0.1 mm/yr) are rounded and understate the real error.

## Third witness for 2026 (build spec § 05, hour 6 to 18)

Searched 14 Nov 2026 for GNSS or radar with 2026 dates over the town, other than NISAR:

| Candidate | 2026 coverage | Independent of NISAR? | Verdict |
|---|---|---|---|
| Open GNSS (NGL) | Only STOL (70 km) and TIMA (91 km) | Yes | Too far to test the bowl; context only |
| Sentinel-1, ASF catalogue (SLC) | 110 dates, 1 Jan to 10 Nov 2026: track 029A (S1A to Jun, S1C, S1D from Apr) and 007D | Yes | Already the second radar (D-004, check 8). The Jan to Jun 2026 scenes are unused so far and would cover NISAR's 129A gap |
| NISAR | 129A from 18 Jan, 094D from 20 Jun 2026; GUNW, GSLC, GCOV, RSLC and soil moisture | No (it is the data under test) | Listed only so the dates line up |

No open third witness inside the window has 2026 data. The honest statement for the page is that the 2026 bowl rate is checked against Sentinel-1 only, and against EGMS for its 2020 to 2025 history.

## Red team at hours 12 / 24 / 40 (with the advisor)

| Hour | Finding | Owner | Verdict (fix / cut / explain) |
|---|---|---|---|
| | | | |

## Frozen-build re-run (hours 40–48)

| Check | Result on the frozen build | Same as before the freeze? |
|---|---|---|
| | | |
