# NISAR data and references for Ocnele Mari

**Owner:** 02 · NISAR data (Alexandru, Eric); the references table with 04 and 05

Checked Sat 14 Nov 2026 against NASA CMR, plus the advisor's rehearsal of 12 Nov 2026 ([rehearsal.md](rehearsal.md)). Every number here carries the date it was checked, because the archive changes.

## What is public, and which part we use

- **The product.** NISAR L2 GUNW, a geocoded unwrapped interferogram: HDF5, about 2.4 GB per pair, 80 m pixels, compressed 512 × 512 chunks. We use frequency A (1229 MHz, λ about 24.4 cm), HH.
- **Collections over the town** (CMR, 14 Nov):
  - `NISAR_L2_GUNW_BETA_V1`: 4 pairs.
  - `NISAR_L2_GUNW_PROVISIONAL_V1`: 18 pairs.
  - `NISAR_L2_GUNW_V1` (validated): 0 pairs.
- **Product status.** Every pair is labelled "not intended for scientific research", and the page says so.
- **Access.** Searching needs no login. Reading needs an Earthdata token. HTTP range reads stream only the chunks over our window: about 58 MB per pair for 50 × 50 km (rehearsal, 12 Nov).

## The pairs

All 22 are in [../data/scenes/ocnele_mari_gunw.csv](../data/scenes/ocnele_mari_gunw.csv) with granule IDs and URLs (CMR, 14 Nov 2026).

| Track | Frame | Pairs | Dates | Lengths |
| --- | --- | --- | --- | --- |
| 129 ascending (`129A`) | 24 | 13 (4 BETA, 9 PROVISIONAL) | 7 Nov 2025 to 18 Jan 2026, then 23 Jun to 21 Oct 2026 | 12 days, plus 24-day pairs where a date is missing |
| 094 descending (`094D`) | 66 | 9 (PROVISIONAL) | 20 Jun to 18 Oct 2026 | 12 days, plus one 24-day pair |

- **No acquisitions from 18 Jan to 23 Jun 2026,** on either track, GSLC included (rehearsal). The cause is unknown (decision O-14).
- **The common window** for up and east is 20 Jun to 21 Oct 2026.
- **The summer 24-day pairs** (129A 17 Jul to 10 Aug, 094D 26 Jul to 19 Aug) bridge the 27 Jul to 10 Aug 2026 instrument data gap that NASA lists.
- **No closure triplets.** The 24-day pairs replace missing 12-day pairs, so there is no 12 + 12 against 24-day triplet. GSLC exists for 11 dates on 094D and 15 on 129A, which allows extra pairs (decision O-07).

## 04's first 129A pair, checked independently (14 Nov 2026, 21:00)

The file Matei shared (Google Drive) is `NISAR_L2_PR_GUNW_023_129_A_024_024_2000_SH_20260623T032016_20260623T032051_20260705T032016_20260705T032051_P05023_N_F_J_001.h5`, 2,399,141,888 bytes. It is row 15 of [the scene list](../data/scenes/ocnele_mari_gunw.csv): a **Level 2** GUNW (the "PR" in the name means PROVISIONAL, not a level), track 129 ascending, frame 24, left-looking, HH, 23 June to 5 July 2026 (12 days), product 1.0.11, specification 1.5.0. Nothing was downloaded in full: [`notebooks/02/verify_nisar_pair.py`](../notebooks/02/verify_nisar_pair.py) read the metadata and the 50 × 50 km window through HTTP range requests (69 MB).

| Item, window of 625 × 625 px at 80 m, EPSG:32635 | 04's log | This check |
| --- | --- | --- |
| Land in both subswaths (mask code under 100) | 99.1 % | 99.1 % (code 12: 97.9 %, code 11: 1.2 %) |
| Anomaly flags (bits 8 to 23) | 0 % | 0 % |
| Bit 24 (ionosphere interpolated) | 98.3 % (99 % in the per-pair table) | 98.35 % |
| Connected components | one | one (384,853 px) |
| Kept: valid, no anomaly, largest component, coherence ≥ 0.35 | 88 % | 88.46 % |
| Ionosphere screen σ in kept pixels | 1.83 rad | 1.831 rad (filled everywhere) |
| Look vector at the site, 500 m, target to sensor | e +0.624, n +0.206, u +0.754 | identical |
| Incidence | 41.07° | 41.068° (= acos u) |
| Wavelength | 0.24393 m | 0.24393 m |

Verdict: **04's first-pair report reproduces.** Two small differences, neither of which changes a number:
- 04's log calls the mask "contiguous". In this file `unwrappedInterferogram/mask` is stored in 512 × 512 gzip chunks like the other layers.
- 04's window corner (x 261720, y 5021320) is the centre of the pixel one column west and one row north of this check's first pixel (edge 261760, 5021280). The window is the same size, shifted by one 80 m pixel.

What this check cannot tell: the phase sign (T3 stays open; no field states the convention), and anything about the other 12 pairs or 04's tie (−5.80 mm/yr), which need the stack.

## Our own NISAR fit (14 Nov 2026, 23:30)

`fetch.py` streamed all 22 pairs (729 MB, windows only; Earthdata token injected by the session proxy, never stored), `stack.py` inverted them, `calibrate.py` tied them to EuVeM2022, `split.py` solved up and east on the common June to October window.

| | 129A (ascending) | 094D (descending) |
| --- | --- | --- |
| Dates, pairs, groups | 15, 13, 2 (gap 18 Jan to 23 Jun) | 10, 9, 1 |
| Pixels with a rate (coherence ≥ 0.35, connected network) | 18 % | 42 % |
| Tie to EuVeM2022 | plane, −7.78 mm/yr at the centre; scatter 28.2 mm/yr; 66,648 tie pixels | offset −15.15 mm/yr; scatter 48.4; 157,186 |
| Model swap vs EGMS (T8, < 1 mm/yr) | 0.74 mm/yr | 0.70 mm/yr |
| T3: zones' median LOS rate (< −2 mm/yr) | **−10.1 mm/yr: passes** (Zone 4 −10.5) | **+23.5 mm/yr: fails** |
| Correlation with Sentinel-1's rate map (same direction) | +0.39 (029A) | +0.32 (007D) |

**094D held off the page.** Checks in `notebooks/03/t3_094d_checks.json`: no 2π unwrapping jump (largest per-pair zone offset 12 mm, a cycle is 122 mm); two pairs (26 Jul to 19 Aug, 12 to 24 Sep) each add about +12 mm to the zones against far stable ground but about 0 against terrain 1 to 3 km away, so the signal covers the whole valley, which lies about 100 m below the stable ground; the ECMWF weather model does not remove it (+22.7 mm/yr); against a local 1 to 3 km reference the zones read −5.1 mm/yr (Zone 4 −10.2), which would pass, but that reference was chosen after seeing the failure, so it is not proof. The positive map correlation with Sentinel-1 rules out a global sign error. The sign stays −1. **On the page:** NISAR 129A (map, rate, dots, zone series, beta/provisional), 094D as a disabled "under review" chip with this reason, Compare and Agreement off until both tracks pass T3 and O-19 settles the shared window and reference. Up/east (12 % of pixels, σ_up about 19 mm/yr) is not exported.



- **`mask` is a 32-bit bitfield** (product spec 1.4), but older pairs store a uint8 code.
  - Bits 0 to 7 are a decimal code for water and the reference and secondary subswaths. Bits 8 to 23 are anomaly flags. Bit 24 means the ionosphere was interpolated there, and the phase is still good. 255 is fill.
  - Cast to uint32 and decode with `mk & 0xFF`, never `mk // 100`. A naive decode dropped 98 % of the 094D window in the rehearsal.
- **`ionospherePhaseScreen` ships but is not applied.** Subtract it. Check per pair whether it is filled.
- **`connectedComponents`:** keep the largest. Other components can be off by a whole cycle, which is 12 cm of LOS.
- **`radarGrid` cube:** LOS unit vectors (`losUnitVectorX`, `losUnitVectorY`) at several heights; we take the height nearest 400 m. It also carries weather-model troposphere layers (Tier 3).
- **The grid** is the product's UTM (EPSG 326xx) at 80 m. The first pair of a track fixes the window; a reprocessed pair on another grid must stop the fetch.
- **Unwrapping.** At about 25 mm/yr the bowls move about 1 mm per 12 days, far from any wrap. A wrong component is the real risk.

## References you can actually get

| Reference | What it gives | Covers our NISAR months? | Use | Owner |
| --- | --- | --- | --- | --- |
| EuVeM2022 (Lantmäteriet) | 3D velocity grid, 0.1°, from the EPN densification, Oct 2008 to Mar 2021 | As a rate | The tie | 04 |
| EGMS GNSS model | East, north and up on a 50 km grid from about 3,770 stations | As a rate | Second tie (O-06). A-EPND 2023, ETRF2000, columns N before E; link in `CITATIONS.md` (found 14 Nov 2026) | 04 |
| NGL MIDAS (`midas.EU.txt`) | Eurasia-fixed station rates; VLC1 to 2018, HORE to 2020 | As a rate | Held-out stations | 04, 05 |
| NGL daily series (tenv3, IGS20) | Daily positions; URL pattern verified 14 Nov (STOL) | Some stations | Screening, plots | 05 |
| Muntean et al. 2026 | Published rates at ROMPOS stations VLC2 (7 km) and HORE (24 km); verticals still to be read from Table S3 | As a rate, to 2025 | Held-out check close to the town | 04 |
| EGMS Ortho L3 Up (100 m) | Vertical rate, 2019 to 2023 and 2020 to 2024 tiles | No, it ends in 2024 | Stable ground; the bowl's history | 05 |
| Sentinel-1 via HyP3 | C-band burst interferograms, July to October 2026 (and January to October on 029A), fitted (`sentinel1/`) | Yes | The second radar (D-004) | 02, 03 |
| Copernicus GLO-30 DEM | Elevation | n/a | Troposphere slope | 02 |
| ECMWF IFS 0.25° pressure levels (Open-Meteo) | Temperature, humidity and height profiles, hourly | Yes | Weather-model troposphere for Sentinel-1 (`sentinel1/scripts/tropo.py`, checked 14 Nov 2026) | 03 |

## Sentinel-1, the second radar (D-004)

Checked Sat 14 Nov 2026 on NASA CMR and in `sentinel1/`.

- **Coverage.** Sentinel-1A, 1C and 1D image the town on two tracks: **029A** (ascending) and **007D** (descending). There are acquisitions every month from Nov 2025 to Nov 2026, including the January to June 2026 months that NISAR missed.
- **What we fitted.** 58 HyP3 `INSAR_ISCE_BURST` pairs (VV, 10x2 looks, water mask), 29 per track, all succeeded. That gives 16 dates per track: 029A from 7 Jul to 5 Oct 2026, 007D from 6 Jul to 4 Oct 2026. The fit is in `sentinel1/analysis/`, with a weather-model troposphere scenario since 14 Nov. A January to October 2026 fit (49 dates and 95 pairs per track, from 132 HyP3 jobs whose download links and checksums are not recorded) is in `sentinel1/analysis_jan_oct/`. The method and caveats are in `sentinel1/analysis/README.md` and `sentinel1/docs/TEAM_HANDOFF.md`.
- **Grid and sign.** 40 m in EPSG:32635, row 0 north. Line-of-sight positive towards the satellite, the same as our convention.
- **Reference.** Relative to surrounding terrain (a 3 to 6.5 km band around the town), not tied to GNSS. The outer band (6.5 to 8 km) drifts. This is why Compare and Agreement use zone minus outer band (O-19).
- **The common window** with NISAR is 7 Jul to 4 Oct 2026. NISAR 094D and 129A both cover it.
- **Geometry.** Sentinel-1 looks right, NISAR looks left, and their incidence angles differ. The same ground motion therefore reads differently in each line of sight, which is why the page never subtracts one LOS from the other directly.

**Not available to us:** ROMPOS raw data and daily solutions are closed. Nothing derived from them enters the repository.
