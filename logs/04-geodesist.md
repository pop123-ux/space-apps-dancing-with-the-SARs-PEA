# 04 · Geodesist · work log

**Owner:** 04 · Geodesist (Matei)

This is the running log for role 04, newest entry first, so the team can follow the references, the tie and the model swap without asking. Each entry says what changed, the evidence, the synthetic and real results kept apart, and what is still open. Times are Europe/Bucharest.

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
