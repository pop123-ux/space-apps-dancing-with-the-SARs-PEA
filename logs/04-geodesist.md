# 04 · Geodesist · work log

**Owner:** 04 · Geodesist (Matei)

This is the running log for role 04, newest entry first, so the team can follow the references, the tie and the model swap without asking. Each entry says what changed, the evidence, the synthetic and real results kept apart, and what is still open. Times are Europe/Bucharest.

---

## Sun 15 Nov 2026, about 10:30 · How big a motion can the page show, and when will NISAR see the zones?

Branch `r04/noise-floor`. Done with Claude Code (see the `AI-DISCLOSURE.md` log). New script `noise_floor.py` (04); it reads the tied tracks in `data/work/ocnele_mari/` and writes `products/ocnele_mari/noise_floor.json` and `noise_floor.png`. It changes no rate, no tie and no other role's file. Run: `python noise_floor.py ocnele_mari` (about 7 s).

**Inputs.** 129A: the team's own stream (14 Nov, 17:40). 094D: still the advisor's rehearsal stack, which fails the sign check. Rerun when 02/03 land their 094D.

### 1. Zone noise: 1,000 fake zones on stable ground per size and track

| Track | One pixel | One zone, alone | Zone minus 1 to 3 km ring | Zone minus 6.5 to 8 km band | Pin (120 m minus about 300 m) |
| --- | --- | --- | --- | --- | --- |
| 129A | 38.9 | 26.8 to 26.9 | **21.3 to 23.2** | 23.0 to 24.3 | 17.9 |
| 094D | 47.6 | 40.1 to 41.4 | 25.2 to 25.5 | 30.9 to 31.4 | 17.8 |

All in mm/yr, 1σ, robust (1.4826 · MAD). Averaging a zone barely helps, because neighbouring pixels share their noise.

### 2. The real zones are all inside the noise

129A, zone minus 1 to 3 km ring: z1 −12.4 (z = −0.6), z2 −11.3 (−0.5), z3 −3.9 (−0.2), z4 −7.1 (−0.3) mm/yr. No zone reaches 2σ on either track or either reference. The "Salt zones sink on 129A" check passes only because its threshold is "< −2 mm/yr". **Proposal for 05:** require < −2σ, with σ from `noise_floor.json`.

### 3. For 06: the pin

A pin needs to differ from the spots around it by more than **36 mm/yr (2σ)** before the page may say anything. Below that, the honest text is "too little signal to say". Never a green tick.

### 4. Up/east from 129A + 094D is noise

Zone-level 2 × 2 solve, north dropped: σ up 22 to 23, σ east 27 to 28 mm/yr. Every component is within about 1σ of zero (for example z2: up +5.9 ± 23.0, east −25.4 ± 27.8). The page's zone 1 value (east −41.6 ± 19 mm/yr) comes from 03's files, which are not on this machine, but by this test its error bar is too small. **Proposal for 06 and 03:** hide the up/east panel, or show "129A only, assuming no horizontal motion" (z1 −16.5 ± 28.2 mm/yr up).

### 5. When can NISAR see the zones?

Each date is linked to the previous one by a single 12-day pair, so pair errors add up. The zone-to-zone spread of cumulative displacement grows like √(pairs), about 3.0 mm per pair on 129A. A random walk with 2.6 mm per pair reproduces today's zone σ of 21.3 mm/yr, so the two estimates agree. Independent noise per date would explain only about a third of it.

Projected with passes every 12 days and no new gap (129A, zone minus 1 to 3 km ring):

| Steady vertical sink | Needs σ ≤ (LOS) | First date at 2σ, as processed now |
| --- | --- | --- |
| 25 mm/yr (EGMS maximum, 2019 to 2024) | 9.4 mm/yr | about 2 May 2029 |
| 19 mm/yr | 7.2 mm/yr | not before 2031 |
| 10 mm/yr | 3.8 mm/yr | not before 2031 |

**What this cannot tell you.** It assumes no new gap, the same pair network and coherence, a steady rate and no seasonal term. The JSON also holds a `best_case` (independent noise per date, as if redundant longer pairs stopped the errors adding up). It is an upper bound, not a result, and it is not plotted. What it does say is that the chain of pairs, not the radar itself, limits the result. The test to run is open item 6: longer pairs (24 and 36 days) from GSLC. 02 has since built 094D from NISAR's single-look data with redundant pairs (`DECISIONS.md`, 15 Nov, 05:30): rerunning `noise_floor.py` on that stack is the direct test of the chain explanation.

**For the pitch (01).** "Today one zone carries ±21 mm/yr of noise, and the strongest salt zone moves −12: inside the noise. Processed as now, NISAR would see a 25 mm/yr sink by about mid-2029; longer pairs are the way to get there sooner."

---

## Sat 14 Nov 2026, about 17:40 · 129A on the team's own stream: HDF5 verified, 13 pairs, real tie

Branch `r04/129a-series`. Done with Claude Code (see the `AI-DISCLOSURE.md` log). Earthdata: Matei signed in himself; the token sits in `.env` (git-ignored) and was never printed or copied.

**Why 04 ran the stream.** On `main` the real-data paths of `fetch.py` (02) and `stack.py` (03) are still stubs. To tie 129A, 04 used a **local, git-ignored stand-in**, `data/work/ocnele_mari/r04/r04_129a.py`. It is the advisor's rehearsal code, changed to the build-spec rules. Nothing in 02's or 03's files was edited. The proposal for them is in section 5.

### 1. First pair verified on the full HDF5 (2026-06-23 → 2026-07-05)

Downloaded through Chrome: `NISAR_L2_PR_GUNW_023_129_A_024_024_2000_SH_20260623T032016_..._P05023_N_F_J_001.h5`, 2,399,141,888 bytes (the size CMR lists, 14 Nov). Kept in `data/raw/nisar/` (git-ignored). Full report: `data/work/ocnele_mari/r04/verify_129A.json`.

| Item | Found in the file | Consequence |
| --- | --- | --- |
| Product | spec 1.5.0, product 1.0.11, PROVISIONAL, track 129, frame 24, Ascending, **Left**-looking, HH, `Nominal` | as cataloged |
| `unwrappedPhase`, `ionospherePhaseScreen` | float32, radians, NaN fill, 512² chunks | window reads work |
| `coherenceMagnitude` | float32, unit 1 | — |
| `connectedComponents` | uint16, fill 65535 | — |
| `mask` | uint32, contiguous; the description matches the build-spec rule (bits 0 to 7 subswath code, 8 to 23 anomaly flags, bit 24 ionosphere interpolated) | rule confirmed |
| Mask in the window | 99.1 % land in both subswaths, 0 % anomaly flags, bit 24 on 98.3 %, one connected component | **88 % kept** with coherence ≥ 0.35 |
| Grid | EPSG:32635, 80 m, 4437 × 4383; the 50 × 50 km window lies inside the frame | window x0 261720, y0 5021320, 625 × 625 px |
| Look vectors | `losUnitVectorX/Y` described as "from the target to the sensor, ENU". At the site (500 m cube level): e +0.624, n +0.206, u +0.754 | incidence 41.07°, equal to the product's `incidenceAngle` to 10⁻⁶° |
| LOS sign | east > 0 is right: ascending (flying about north) and looking left (west) puts the satellite east of the ground | `C.enu_to_los` (positive = towards the satellite) is consistent with the product |
| Wavelength | 0.24393 m (from `centerFrequency`) | — |

My script's first sanity check of the LOS sign printed "false". The check's expected sign was wrong, not the product; it is fixed and the fix is recorded in `verify_129A.json`.

**T3 (phase sign): still open, for 03 and 05.** No field in the file states the interferogram convention, so the file cannot settle T3. `PHASE_SIGN = −1` stays the draft. What the file does settle is the look-vector half of the sign chain: target to sensor, positive towards the satellite. The zone test below cannot decide it either: zones 1 and 2 read −14.7 and −12.4 mm/yr against a pixel σ of about 16 mm/yr and a stable-ground scatter of 39 mm/yr.

**Cross-check.** My window of this pair equals the advisor's 12 Nov rehearsal file wherever both have data (maximum difference 0.0 rad, same grid). The look vectors agree to 1.3 × 10⁻⁴.

### 2. All 13 cataloged 129A pairs, streamed (window only)

0.78 GB in total, about 60 MB and 90 to 190 s per pair. The per-pair QA is in `129A/qa_pairs.jsonl`.

| Pair | Collection | Kept | Iono σ (rad) | Bit 24 | Mask dtype |
| --- | --- | --- | --- | --- | --- |
| 2025-11-07 → 2025-12-01 (24 d) | BETA | 71 % | 0.48 | 0 % | uint8 |
| 2025-12-01 → 2025-12-13 | BETA | 77 % | 0.54 | 0 % | uint8 |
| 2025-12-13 → 2025-12-25 | BETA | 66 % | 0.56 | 0 % | uint8 |
| 2025-12-25 → 2026-01-18 (24 d) | BETA | **24 %** | 0.29 | 0 % | uint8 |
| 2026-06-23 → 2026-07-05 | PROVISIONAL | 88 % | **1.83** | 99 % | uint32 |
| 2026-07-05 → 2026-07-17 | PROVISIONAL | 96 % | 0.59 | 100 % | uint32 |
| 2026-07-17 → 2026-08-10 (24 d) | PROVISIONAL | 82 % | 0.69 | 99 % | uint32 |
| 2026-08-10 → 2026-08-22 | PROVISIONAL | 96 % | 0.63 | 100 % | uint32 |
| 2026-08-22 → 2026-09-03 | PROVISIONAL | 96 % | 0.31 | 100 % | uint32 |
| 2026-09-03 → 2026-09-15 | PROVISIONAL | 97 % | 0.30 | 100 % | uint32 |
| 2026-09-15 → 2026-09-27 | PROVISIONAL | 98 % | 0.35 | 100 % | uint32 |
| 2026-09-27 → 2026-10-09 | PROVISIONAL | 97 % | 0.25 | 100 % | uint32 |
| 2026-10-09 → 2026-10-21 | PROVISIONAL | 88 % | 0.68 | 99 % | uint32 |

The ionosphere layer was present and subtracted on all 13 pairs. The BETA pairs store the mask as uint8 with no bit 24, as the rehearsal found. Mid-winter 2025-12-25 → 2026-01-18 keeps only 24 % of pixels.

### 3. Time series (`129A/ts.npz`, written by the 04 stand-in)

- **Pairs and dates.** 13 pairs, 15 dates, 2025-11-07 to 2026-10-21, pair lengths 12 and 24 days, 0 triplets.
- **Groups.** **Two acquisition groups, referenced separately:**
  - group 0 (January group): 2025-11-07 to 2026-01-18;
  - group 1 (June group): 2026-06-23 to 2026-10-21.
  - **Gap:** 2026-01-18 to 2026-06-23. No pair spans it, nothing is interpolated across it, and `cum` is 0 at each group's first date.
- **Rate.** One line through the dates with one offset per group, and no annual term.
- **Coverage and corrections.** 94 % of pixels have a series. The elevation slope removed per pair has a median absolute value of 1.5 mm per 100 m and a maximum of 3.4.
- **New fields** (additions to the contract, for 03 to keep or drop): `group` (one per date), `gap_ranges`, `pairs`, `iono_used`, `phase_sign`, `reference`, `made_by`.
- **Rate equal to the rehearsal.** r = 1.000 on 369,010 pixels, median difference 0.00 mm/yr. Referencing the groups separately changes `cum`, not `vel`.

**Terrain-relative** (before the tie; stable ground around the site = 0), LOS, mm/yr:
- stable-ground median −6.7, robust scatter 38.0;
- zones: z1 −20.5, z2 −18.2, z3 −1.6, z4 −8.3;
- median σ about 16 per pixel, a lower bound.

### 4. The real tie (`calibrate.py ocnele_mari --track 129A --plot`)

| Item | 129A |
| --- | --- |
| Model | EuVeM2022 (Eurasia-fixed; horizontals ETRF2000, up IGS14) |
| Method | offset (a plane cut the scatter only from 39.2 to 38.9 mm/yr, under 10 %) |
| Offset | **−5.80 mm/yr** (rehearsal: −6.01) |
| Tie pixels | 347,765 (removed: 25,915 low coherence, 8,184 zones + 3 km, 983 near stations) |
| Residual | std 39.15, MAD 37.07 mm/yr |
| Model in LOS | −0.63 mm/yr mean |
| **Swap vs EGMS A-EPND 2023** | **0.704 mm/yr**: equal to the 16:10 preliminary figure on the rehearsal stack, so **T8 stays PASS WITH NOTE**; the note's "rerun on the team stack" condition is met for 129A |
| Tied zone medians (LOS) | z1 −14.7, z2 −12.4, z3 +4.2, z4 −2.5; all zones −4.8 mm/yr |

The tie residual map (`129A/tie.png`) is centred and symmetric. Its pattern follows slopes and valleys, which is the atmosphere and DEM noise floor, not ground motion.

**Changes to `calibrate.py`:**
- `--track` ties one track and keeps the other tracks' entries in `calib.json`. This stops a run from re-tying the rehearsal's copied 094D files.
- `cum_cal` subtracts the correction from each group's own first date.
- Each `calib.json` entry now carries:
  - `sensor` (named in the contract but missing before);
  - `frame`, `dates`, `gaps`, `ts_made_by` and `phase_sign`, for provenance.

`pytest -q`: 8 passed. `checkpoint.py ocnele_mari`: contract OK.

**`products/ocnele_mari/calib.json` now holds 129A only.** 094D is not tied: its files in `data/work/` are still the rehearsal copies from 15:41.

### 5. Hand-off

**To 02 and 03 (proposal; their files, their call).** `r04_129a.py` `window` and `stack` meet the build spec and could fill the stubs in `fetch.read_pair`, `fetch.write_geometry`, `fetch.write_dem` and the `stack.py` functions:
- **Valid pixels:** the mask read as uint32, the largest connected component, coherence ≥ 0.35.
- **Ionosphere:** subtracted, with its use recorded per pair.
- **Grid:** the run stops if the grid shifts.
- **Groups:** each referenced to its own first date.

When 03's own `ts.npz` lands, rerun `calibrate.py ocnele_mari --track 129A` and compare with the numbers above.

**To Darius (06).**

| What | Value |
| --- | --- |
| Dates (129A) | 2025-11-07, 2025-12-01, 2025-12-13, 2025-12-25, 2026-01-18, 2026-06-23, 2026-07-05, 2026-07-17, 2026-08-10, 2026-08-22, 2026-09-03, 2026-09-15, 2026-09-27, 2026-10-09, 2026-10-21 (verified against the 13 cataloged pairs) |
| Gap | 2026-01-18 to 2026-06-23: no frames, a "no data" label |
| Groups | January group (Nov to Jan) and June group (Jun to Oct), each starting at 0 mm. Never draw a line across the gap. |
| LOS sign | positive = towards the satellite. Look vector target to sensor: e +0.62, n +0.21, u +0.75 at the town; incidence 41°. **Phase sign still draft (T3 open).** |
| Units | LOS rate mm/yr, cumulative LOS mm |
| Reference | `ts.npz`: **terrain-relative** (stable ground outside the zones + 3 km = 0). `cal.npz` `vel_cal` / `cum_cal`: **tied to EuVeM2022, Eurasia-fixed** (offset −5.80 mm/yr). |
| Overlays | `data/work/ocnele_mari/129A/overlays/`: `129A_rate_terrain.png` (labelled terrain-relative, not tied) and `129A_rate_tied.png`, RdBu, symmetric ±105 mm/yr, red = away. `129A_overlays.json` gives the UTM bounds, lon/lat corners, dates, gaps, groups, units and sign. They are on the UTM grid, so `export.py` resamples them. |
| Labels | "NISAR beta/provisional products": the January group is BETA, the June group PROVISIONAL. |

### Still open for 04

1. 094D: stream and tie it the same way.
2. T3 with 03 and 05 (see above).
3. The frame paragraph for the page.
4. Delete `data/raw/nisar/*.h5` (2.4 GB) once 02 has checked it.

---

## Sat 14 Nov 2026, about 16:40 · merged `r04/egms-model` to `main`

`r04/egms-model` (commits 5c9adff and 0bd8ce8) merged into `main` with `--no-ff` at Matei's request.

- **What `main` had gained meanwhile:** 17 commits from 03, 06 and the verifier (PRs #10 to #12).
- **Conflicts:** two, both in append-only logs (`AI-DISCLOSURE.md`, `DECISIONS.md`). Resolved by keeping every row from both sides, `main`'s rows first. No code conflicted.
- **Tests:** `pytest -q` on the merged tree: 8 passed.
- **No PR:** the merge was pushed directly.
- **How it was done:** in a temporary worktree, because another Claude Code session (03's 129A series) had this checkout on `r04/129a-series`. That session's checkout was not touched.

---

## Sat 14 Nov 2026, about 16:10 · 05's EGMS stable-ground check is in: T8 PASS WITH NOTE

Source: `docs/validation-log.md` on 05's branch `r05/egms-and-witnesses` (PR #9), section "EGMS on the stable ground", read 14 Nov 2026. These are 05's numbers, not ours.

### What 05 found (EGMS L3 Ortho Up 2020 to 2025)

| Area | EGMS points | Median Up | Robust scatter | Within ±1.5 mm/yr | Sinking ≥ 5 mm/yr |
| --- | --- | --- | --- | --- | --- |
| Tie area (outside zones + 3 km, more than 1 km from stations) | 27,478 | −0.6 mm/yr | 0.9 mm/yr | 79 % | 1.2 % |
| Check-6 set (\|v\| < 1.5 mm/yr, outside zones + 500 m) | 22,864 | −0.4 mm/yr | 0.6 mm/yr | 100 % | 0 % |

- **Moving patches:** a few small patches move. The nearest is 9.3 km south at −6.8 mm/yr; the fastest is 21.7 km north-west at −19.6 mm/yr.
- **Effect on the level:** dropping every cell that sinks 5 mm/yr or faster moves the tie-area median from −0.60 to −0.50 mm/yr. Our 3σ clipping moves the mean from −0.79 to −0.67 mm/yr.

### What it means for the tie (04)

- **The tie area is stable** to within 0.1 mm/yr of its level. That is ten times under T8's 1 mm/yr limit, and 400 times under NISAR's 39 to 52 mm/yr pixel scatter.
- **No masking of the moving patches.** The tie mask rules are frozen in the build spec, and the patches change the level by 0.1 mm/yr at most. Recorded in `DECISIONS.md`.
- **The level checks out against the frame.** EGMS stable ground (−0.6 mm/yr, ETRF2000) sits next to the EGMS GNSS model at the centre (−0.8 mm/yr, ETRF2000), as it should: EGMS is calibrated to that model. In our frame (EuVeM2022, IGS14 up), the same ground would read about −0.6 + 0.4 = −0.2 mm/yr, using the ETRF2000 offset from Figure 10 (15:45 entry). That is within about 0.3 mm/yr of EuVeM2022's own +0.08 mm/yr there.

### Heads-up for 05: check 6 starts with a reference offset

NISAR's up is tied to EuVeM2022, and EGMS's up to its own A-EPND model. On stable ground each keeps its model's level:

| Level on stable ground | Up (mm/yr) |
| --- | --- |
| NISAR, tied to EuVeM2022 | about +0.1 |
| EGMS, check-6 set | −0.4 |
| EGMS, tie area | −0.6 |

So **NISAR up − EGMS up should come out at about +0.5 to +0.7 mm/yr from the references alone**, before any NISAR error:
- about 0.4 of it is the ETRF2000 vertical frame;
- the rest is the two GNSS models disagreeing.

That uses half of check 6's 1.5 mm/yr budget. A median near +0.6 mm/yr is therefore expected, not a NISAR bias. A value above +1.5 needs a look at NISAR itself.

### T8: PASS WITH NOTE

| Part | Result |
| --- | --- |
| Model swap (04, 15:45) | EuVeM2022 vs EGMS changes calibrated LOS rates by **0.72 (094D) and 0.70 (129A) mm/yr**, under 1 mm/yr |
| EGMS on the stable ground (05) | Tie area at −0.6 mm/yr, 79 % within ±1.5 mm/yr; moving patches shift the level by 0.1 mm/yr |

**Note:**
- **Which stack:** the swap ran on the advisor's rehearsal NISAR stack (real data, not the team's processing). The swap depends on the look vectors and the tie mask, not on the phase, so the team stack should give nearly the same number. **Rerun `calibrate.py ocnele_mari` when 03 hands off `ts.npz` and record the number here.** If it reaches 1 mm/yr, T8 reopens.
- **Check 6** (NISAR up − EGMS up) is a separate check, owned by 05, and waits on 03's `up_east.npz`.

---

## Sat 14 Nov 2026, about 15:45 · EGMS GNSS model in, frame checked, first real model swap (T8, part 1)

Branch `r04/egms-model`. Done with Claude Code (see the `AI-DISCLOSURE.md` log).

### The EGMS GNSS model

05 (Paul) found the link, which needs no login: `EGMS_AEPND_V2023.0.csv`, 3,773 nodes on a 50 km grid (row in `CITATIONS.md`).
- **Columns:** checked on the file: `Latitude, Longitude, N, E, Up, SigmaN, SigmaE, SigmaUP, easting, northing`. **N comes before E.**
- **Reader:** `refs.parse_egms_gnss` swaps both lat/lon and N/E into the `model_euvem.csv` order. It refuses any other header.
- **Output:** `refs.py ocnele_mari` now writes `refs/model_egms.csv` from the 29 nodes within 150 km of the site.
- **Check against Paul:** at the site centre, `load_model("ocnele_mari", "egms")` gives ve −0.75, vn −1.18, vu −0.80 mm/yr, the same as Paul's numbers.

### Frame: confirmed, with one catch in the vertical

The EGMS GNSS Calibration Report (v5.2, section 1.2) says the A-EPND 2023 model, and the EGMS 2020 to 2024 delivery calibrated with it, are in **ETRF2000**. ETRF2000 is the ETRS89 realization fixed to stable Eurasia.
- **Horizontals:** the same frame as EuVeM2022's horizontals (ETRF2000).
- **Vertical:** EuVeM2022's up is IGS14, and ETRF2000's up is not. The report's Figure 10 gives ETRF2000 minus ETRF2020 in up from −0.88 mm/yr in the north to −0.16 mm/yr in the south.
  - **At Ocnele Mari:** about **−0.4 mm/yr**, read by eye from the colour scale, so ±0.1 at best.
  - **ETRF2020 vs IGS14:** ETRF2020's up stays close to ITRF2020 and IGS14. That is my expectation, not a number from the report.
- **Model vs model at the site centre (mm/yr):**

| Model | ve | vn | vu |
| --- | --- | --- | --- |
| EuVeM2022 | −0.74 | −1.06 | +0.08 |
| EGMS | −0.75 | −1.18 | −0.80 |

  - The horizontals agree within 0.12 mm/yr.
  - About −0.4 of the −0.88 mm/yr up difference is the frame; the other ~−0.5 is the models disagreeing.
- **No frame shift applied:** EGMS is used as published. Applying a number read by eye from a figure would be a hard-coded tweak; see `DECISIONS.md`.

### Real model swap, on the rehearsal NISAR stack (PRELIMINARY)

**What the stack is:** 02 and 03 have not handed off `ts.npz` yet, so the real swap ran on the advisor's rehearsal stack of 12 Nov. That is real NISAR GUNW over Ocnele Mari, processed by the advisor's code, not ours. The track files were copied into `data/work/ocnele_mari/` (not committed).
- **Products:** `products/ocnele_mari/calib.json` from this run was deleted, not committed. Products must come from the team's own pipeline.
- **Tie pixels:** 309,198 (094D) and 347,767 (129A).

| Run | 094D | 129A |
| --- | --- | --- |
| Tie to EuVeM2022: offset (scatter) | −8.89 mm/yr (51.6) | −5.80 mm/yr (39.2) |
| Tie to EGMS: offset | −8.17 mm/yr | −5.10 mm/yr |
| **Swap EuVeM2022 vs EGMS** (median absolute change in vel_cal on the tie pixels) | **0.72 mm/yr** | **0.70 mm/yr** |
| Swap EuVeM2022 vs rigid plate | 0.25 mm/yr | 0.63 mm/yr |

- **What the 0.70 to 0.72 includes:** about 0.3 mm/yr of it is the ETRF2000 vertical offset projected onto the line of sight (−0.4 mm/yr × an up component of about 0.78). So the pure model share is nearer 0.4 mm/yr.
- **T8 threshold:** the swap is under 1 mm/yr on both tracks, so the tie does not depend on which GNSS model we pick.
- **Scatter:** the pixel scatter (39 to 52 mm/yr) is about 50 times larger than the swap. The model is not what limits the result.

**Synthetic** (unchanged from 15:20): the swap path recovers a known 0.78/0.79 mm/yr.

### For 05 (Paul): the EGMS Ortho comparison

EGMS Ortho 2020 to 2024 is calibrated to this ETRF2000 model. Our NISAR up is tied to EuVeM2022 (IGS14 up). Near the site, the two frames differ by about 0.4 mm/yr in up, before any real difference: EGMS's up should read about 0.4 mm/yr lower for the same ground. That is small next to a 27 mm/yr scatter, but it belongs in the bias budget of the stable-ground check.

### T8 status: PARTIAL

| Part | Status |
| --- | --- |
| Model swap | Done on real NISAR (rehearsal stack): 0.72 / 0.70 mm/yr, under 1 mm/yr |
| Swap on the team's own stack | Rerun when 03 hands off `ts.npz` |
| EGMS Ortho stable-ground comparison | Recorded by 05 on the team stack |

T8 is complete only when the last two are recorded.

### Proposed for 01 (Mario), not edited

`docs/build-spec.md` row O-06 still says "CSV link still to be found". Suggested text: "EGMS GNSS model A-EPND 2023 (found 14 Nov; ETRF2000); rigid plate stays as the fallback".

---

## Sat 14 Nov 2026, about 15:35 · merged to `main`

`r04/station-check` (commit 56b5e96) merged into `main` with `--no-ff` at Matei's request. `main` had not moved since the branch was cut; `pytest -q` on the merge: 8 passed. No PR was opened: the merge was pushed directly.

---

## Sat 14 Nov 2026, about 15:20 · station check against the original tables, real `refs.py` run, swap hook tested

Branch `r04/station-check`. Done with Claude Code (see the `AI-DISCLOSURE.md` log).

### Station values, checked against the originals

Sources, downloaded 14 Nov 2026 (rows in `CITATIONS.md`):
- the Muntean et al. 2026 supplement PDF, Tables S1 and S3;
- NGL `midas.EU.txt` and `midas.readme.txt`.

**Muntean et al. 2026.** Table S1 columns are `Vlat Vlon Siglat Siglon`, which is **North, East**. The table title says "Eurasia reference frame" (EU14, from ITRF2014), and the units are mm/yr. Table S3 `Vrad` is the vertical.

| Station | Field | In `common.PUBLISHED` | Table | Result |
| --- | --- | --- | --- | --- |
| VLC2 | ve, vn | −0.84, +0.77 | Vlon −0.84, Vlat +0.77 (S1) | ok, E/N order right |
| VLC2 | se, sn | 0.21, 0.19 | Siglon 0.21, Siglat 0.19 | ok |
| VLC2 | vu ± su | +0.86 ± 0.61 | Vrad 0.86, Sigrad 0.61 (S3) | ok |
| VLC2 | dates | 2019-08-02 to 2025.41 | Tstart 19AUG02, Tspan 5.82 yr | ok |
| HORE | ve, vn, se, sn | −0.50, +0.41, 0.09, 0.11 | Vlon −0.50, Vlat +0.41, Siglon 0.09, Siglat 0.11 (S1) | ok |
| HORE | vu | NaN | not in Table S3 | ok: there is no published vertical |
| HORE | dates | none | Tstart 14NOV27, Tspan 10.50 yr (S1) | **added**: 2014-11-27 to 2025.40, in `refs.PUBLISHED_SPAN` |

**NGL MIDAS** (readme: columns 9 to 11 are E, N, U in **m/yr**, 12 to 14 their sigmas, 3 and 4 the first and last epoch, 25 and 26 lat and lon). `refs.parse_midas` reads columns 9 to 14 × 1000 into mm/yr, in E, N, U order. The rows written for HORE and VLC1 match the raw file digit for digit:
- HORE: −0.205, +0.228, −1.355 mm/yr, 2012.80 to 2020.24
- VLC1: −0.049, −0.189, −0.746 mm/yr, 2012.66 to 2018.93

**Sign.** Every value keeps its published sign. Up is positive.

### Real run: `python refs.py ocnele_mari` (first real run; the build machine could not reach the servers)

```
downloaded: EuVeM2022_Romania.txt (0.1 MB)
downloaded: midas.EU.txt (1.9 MB)
dropped MIDAS VLC2 at 43.279, 12.285: 977 km away, a different station with the same name
ocnele_mari: model 2738 grid nodes (46 inside the window) · stations: HORE (NGL, 24.5 km, vu -1.35),
  VLC1 (NGL, 6.4 km, vu -0.75), VLC2 (Muntean, 6.4 km, vu +0.86), HORE (Muntean, 24.5 km, vu +nan)
EGMS Up: not on disk yet (05 writes refs/egms_up.csv); the cross-check will be skipped
```

- **Stations in the window:** VLC1 and VLC2 (6.4 km), and HORE (24.5 km, inside the 35 km half-diagonal). The site list names no other station, and no other open MIDAS station lies inside 35 km.
- **VLC1 and VLC2:** they share coordinates. VLC1 is the NGL series to 2018 and VLC2 the Muntean series from August 2019, so they are probably one site under two names. 05 should not count them as two independent witnesses.
- **HORE's vertical:** NGL MIDAS gives −1.35 ± 0.53 mm/yr from data ending 2020.24. Muntean has none.

### Synthetic known-answer test of `calibrate.py` (simulated, not data)

`fetch.py` and `stack.py` are still stubs on `main`, so a scratch harness (not committed) wrote two synthetic tracks for `demo`. They had the Ocnele Mari geometry, constant look vectors, 3 mm/yr noise and a known tie.

| Check | Truth | Recovered |
| --- | --- | --- |
| 094D tie | plane: −8.8 mm/yr, east +4.0, north −2.0 per 10 km | plane −8.80, +4.00, −2.01 |
| 129A tie | offset −6.0 mm/yr | offset −5.99 |
| Swap against a rigid plate | LOS of the synthetic regional velocity: 0.30 (129A), 0.07 (094D) mm/yr | 0.30, 0.07 |
| Swap against a synthetic `model_egms.csv` (EuVeM grid with up + 1.0 mm/yr) | \|los_u\| × 1.0 = 0.78 (129A), 0.79 (094D) mm/yr | 0.78, 0.79 |

So the EGMS swap path in `calibrate.py` (`second_model` picks `model_egms.csv` when it exists) works as designed. The synthetic `model_egms.csv` was deleted after the test.

### Real tie: not run yet

There is no `geom.npz` or `ts.npz` for `ocnele_mari` on `main` until 02 and 03 hand off.

The advisor's rehearsal copy (a separate folder, not this repository) gives the order of magnitude to expect. Its code is not this repository's, so these are not our numbers:
- **Ties:** −8.80 (094D) and −6.01 (129A) mm/yr.
- **Robust scatter:** 50.6 and 36.9 mm/yr.
- **EuVeM2022's own share:** +0.25 and −0.62 mm/yr.

### Open

1. **T8 is not done.** The EGMS GNSS model CSV (O-06) is still not found. T8 closes only when all of the following are true:
   - `model_egms.csv` is on disk;
   - a real `calibrate.py ocnele_mari` records `swap_delta_mm_yr` against `egms`;
   - the EGMS Ortho stable-ground comparison with 05 is written here.
2. Run `calibrate.py ocnele_mari --plot` as soon as 03 hands off `ts.npz`.
3. Frame paragraph for the page (hour 30 to 40). The draft is the `refs.py` docstring. The error budget will be added once the real tie exists.
4. Tell 05: VLC1 and VLC2 are probably the same site; HORE's vertical comes from NGL only.
