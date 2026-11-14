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
| VLC2 | Muntean et al. 2026 | 6.4 km | Not checked yet | −0.2 mm/yr (same 79 cells as VLC1) | 2025 | | vertical still to be read from Table S3 (04). `common.PUBLISHED` gives VLC2 the same position as VLC1 (45.1074 N, 24.3664 E): check whether they share a building or a mast. Until that is confirmed, VLC1 and VLC2 count as one witness, not two (raised by 04, 14 Nov 2026) |
| HORE | NGL MIDAS + Muntean et al. 2026 | 24.5 km | Not checked yet | −0.3 mm/yr (71 cells within 500 m) | 2020-03 (821 days from 2012-10) | Held out; "assumes steady motion since 2020" | Its vertical rate comes from NGL MIDAS only (Muntean et al. 2026 Table S3 has no HORE), so it rests on one solution; the pin should say so (raised by 04, 14 Nov 2026). Daily Up fit −1.5 mm/yr (2012 to 2020). Agrees with EGMS within about 1.2 mm/yr; no time overlap |
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

## T10: Sentinel-1 holds up (05 with 03)

Read from `sentinel1/analysis/summary.json` on 14 Nov 2026: the July to October fit, 16 dates and 29 pairs per track (029A 2026-07-07 to 10-05, 007D 2026-07-06 to 10-04). The January to October extension in the handoff is not in `summary.json` yet, so it is not tested here.

Rule (prompts/early-tests.md): a zone **passes** where the sign of its fitted change holds in all five runs (baseline, strict coherence, west reference, east reference, elevation correction) and the spread (largest minus smallest) is smaller than the baseline change. Otherwise it is "not testable" in the Agreement view. Values are the fitted change over the window (`window_fit_mm`), line of sight, mm, negative = away from the satellite, relative to the 3 to 6.5 km reference band.

| Track | Zone | Baseline | Strict coh. | West ref. | East ref. | Elev. corr. | Spread | Result | Why |
|---|---|---|---|---|---|---|---|---|---|
| 029A | z1 | −8.6 (21 px) | −6.0 (3 px) | −7.1 | −8.6 | −8.0 | 2.6 | **Pass** | Strict coherence keeps only 3 pixels |
| 029A | z2 | −6.8 (43 px) | −7.8 (26 px) | −6.0 | −6.8 | −6.4 | 1.8 | **Pass** | |
| 029A | z3 | no connected series | | | | | | Not testable | No pixel spans the dates |
| 029A | z4 | −7.5 (34 px) | −8.6 (6 px) | −6.9 | −8.0 | −2.8 | 5.8 | **Pass** (narrow) | The elevation correction removes about 60 % of the change |
| 007D | z1 | −5.2 (79 px) | +0.3 (2 px) | −4.0 | −6.1 | −6.0 | 6.3 | Not testable | Sign flips under strict coherence (2 pixels) |
| 007D | z2 | −1.4 (48 px) | −3.9 (2 px) | +0.3 | −2.3 | −2.5 | 4.2 | Not testable | Sign flips with the west reference; spread larger than the change |
| 007D | z3 | +0.2 (55 px) | −0.1 (3 px) | +1.6 | −1.0 | +3.4 | 4.4 | Not testable | No consistent sign |
| 007D | z4 | −3.5 (76 px) | −2.8 (33 px) | −2.2 | −4.4 | −2.0 | 2.4 | **Pass** | |

Closure (`fits.quality`): median absolute misclosure 1.6 mm (029A) and 1.3 mm (007D) over 14 triangles each, 95th percentile 9.4 mm and 6.2 mm. The 95th percentile is as large as the zone changes on 029A, so single pixels are noisy even where the zone medians hold.

**T10 result: PASS WITH NOTE.** Four zone and track combinations hold (029A z1, z2, z4; 007D z4); four are not testable (029A z3; 007D z1, z2, z3). z4 is the only zone that holds on both tracks, which agrees with the handoff's choice of z4 for the demo.

What this cannot tell us:
- The reference band moves too: the outer control drifts +3.9 mm (029A) and +3.3 mm (007D) over the window, so zone changes are relative, not absolute.
- The sensitivity runs share the same pairs and atmosphere, so a pass shows the result is not fragile to these choices; it does not prove it is ground motion.

**Red flag for the team (01, 03, 04): z3.** EGMS shows z3 as the fastest-sinking zone in 2020 to 2025 (median −18.9 mm/yr Up, 6 cells). If that continued, Sentinel-1 should see roughly −3 to −4 mm of line-of-sight change over the 90 days. It sees no connected series on 029A and about 0 mm (+0.2, no consistent sign) on 007D. Possible reasons: low coherence over the bowl, the motion stopped or slowed, or the zone circle sits off the moving cells. This is a finding to explain, not an error to tune away; it goes to the red team below.

### z3 investigation (05, 14 Nov 2026)

Done on the committed Sentinel-1 grids (`sentinel1/assets`, checksums verified) and `refs/egms_up.csv` / `egms_east.csv`, with `notebooks/05/z3_check.py`. Nothing in `sentinel1/` was changed.

1. **The zone is in the right place.** 6 of the 31 EGMS cells sinking faster than −10 mm/yr lie inside the z3 circle, 11 within 1 km. The centre of the fast cells within 1.5 km is 214 m from the z3 centre, inside its 300 m radius.
2. **What Sentinel-1 should see if 2020 to 2025 continued.** EGMS z3 cells move −18.9 mm/yr Up and +0.2 mm/yr east. Projected on each track's look vector (029A east −0.63, up 0.77; 007D east +0.64, up 0.76) that is −13.8 mm/yr on 029A and −16.4 mm/yr on 007D in line of sight, so about **−3.4 mm and −4.1 mm over the 90-day window**.
3. **029A cannot see z3: coherence loss.** 0 of 177 pixels inside the circle have a series, 3 % in the 300 to 600 m ring, 21 % at 600 to 1,000 m. None of the 11 fast EGMS cells has a Sentinel-1 value. Not testable, as T10 says.
4. **007D sees z3 but not the sinking.** 55 of 177 pixels (31 %) have a series. At the 10 fast EGMS cells it covers, Sentinel-1 reads +8.8 mm/yr (towards the satellite) where EGMS predicts −6.5 mm/yr. On stable EGMS cells 1.5 to 3 km away the two agree (+0.8 against −0.4 mm/yr, 113 cells). The zone median over 90 days is about 0 mm against an expected −4 mm.
5. **But the expected signal is at the noise level.** −4 mm over 90 days is smaller than 007D's 95th-percentile misclosure (6.2 mm) and inside the spread of its sensitivity runs (−1.0 to +3.4 mm). So the honest reading is "**not detected**", not "contradicted". Sentinel-1's July to October window cannot tell whether z3 kept sinking or stopped.
6. **Side finding on 029A (for 03).** Stable EGMS cells 1.5 to 3 km from z3 read −19.3 mm/yr on 029A where EGMS has them at about 0 (70 cells). Pixels around z3 read −33 to −42 mm/yr. A broad negative signal on the west side of town, from the reference band, the atmosphere or real motion, may inflate 029A's z1, z2 and z4 rates (−27 to −35 mm/yr) as well. 007D does not show it.

**What would settle it:** the January to October extension (49 dates per track, already processed by 02/03). Over 9 months EGMS predicts about −10 to −12 mm on z3, well above the noise. The handoff says no descending salt-zone pixel spans all 49 dates under the current connectivity rule, so 03 would need to relax it or use the new group-aware solver.

**Suggested wording for the page (01 decides):** "z3 sank about 19 mm a year from 2020 to 2025 (EGMS). Sentinel-1 cannot confirm 2026 here: the ascending track loses coherence over the bowl, and on the descending track the expected 4 mm over July to October is within the noise."

## Red team at hours 12 / 24 / 40 (with the advisor)

| Hour | Finding | Owner | Verdict (fix / cut / explain) |
|---|---|---|---|
| Before hour 12 (T10) | z3 is the fastest-sinking zone in EGMS 2020 to 2025 (−18.9 mm/yr) but Sentinel-1 shows no usable 2026 signal there (029A no series; 007D about 0 mm) | 03 with 05 | **Explain** (05 investigated, see "z3 investigation"): zone position is fine; 029A has no coherent pixels there; on 007D the expected 4 mm is within the noise. Ask 03 for the Jan to Oct extension on z3, and to look at 029A's negative bias around z3 |
| Before hour 12 | `sentinel1/scripts/restore_grids.py` refuses to run on Windows: git turns `summary.json` into CRLF line endings, so its SHA-256 no longer matches `MANIFEST.json` (the file in git is unchanged) | 03 | Fix: hash the file with `\r\n` turned back into `\n`, or add `sentinel1/analysis/summary.json -text` to a `.gitattributes` |

## Frozen-build re-run (hours 40–48)

| Check | Result on the frozen build | Same as before the freeze? |
|---|---|---|
| | | |
