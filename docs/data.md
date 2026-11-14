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

## Product notes and traps

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
| EGMS GNSS model | East, north and up on a 50 km grid from about 3,770 stations | As a rate | Second tie (O-06; CSV link still to be found) | 04 |
| NGL MIDAS (`midas.EU.txt`) | Eurasia-fixed station rates; VLC1 to 2018, HORE to 2020 | As a rate | Held-out stations | 04, 05 |
| NGL daily series (tenv3, IGS20) | Daily positions; URL pattern verified 14 Nov (STOL) | Some stations | Screening, plots | 05 |
| Muntean et al. 2026 | Published rates at ROMPOS stations VLC2 (7 km) and HORE (24 km); verticals still to be read from Table S3 | As a rate, to 2025 | Held-out check close to the town | 04 |
| EGMS Ortho L3 Up (100 m) | Vertical rate, 2019 to 2023 and 2020 to 2024 tiles | No, it ends in 2024 | Stable ground; the bowl's history | 05 |
| Sentinel-1 via HyP3 | C-band burst interferograms, July to October 2026, fitted (`sentinel1/`) | Yes | The second radar (D-004) | 02, 03 |
| Copernicus GLO-30 DEM | Elevation | n/a | Troposphere slope | 02 |

## Sentinel-1, the second radar (D-004)

Checked Sat 14 Nov 2026 on NASA CMR and in `sentinel1/`.

- **Coverage.** Sentinel-1A, 1C and 1D image the town on two tracks: **029A** (ascending) and **007D** (descending). There are acquisitions every month from Nov 2025 to Nov 2026, including the January to June 2026 months that NISAR missed.
- **What we fitted.** 58 HyP3 `INSAR_ISCE_BURST` pairs (VV, 10x2 looks, water mask), 29 per track, all succeeded. That gives 16 dates per track: 029A from 7 Jul to 5 Oct 2026, 007D from 6 Jul to 4 Oct 2026. The fit is in `sentinel1/analysis/`, and the method and caveats are in `sentinel1/analysis/README.md` and `sentinel1/docs/TEAM_HANDOFF.md`.
- **Grid and sign.** 40 m in EPSG:32635, row 0 north. Line-of-sight positive towards the satellite, the same as our convention.
- **Reference.** Relative to surrounding terrain (a 3 to 6.5 km band around the town), not tied to GNSS. The outer band (6.5 to 8 km) drifts. This is why Compare and Agreement use zone minus outer band (O-19).
- **The common window** with NISAR is 7 Jul to 4 Oct 2026. NISAR 094D and 129A both cover it.
- **Geometry.** Sentinel-1 looks right, NISAR looks left, and their incidence angles differ. The same ground motion therefore reads differently in each line of sight, which is why the page never subtracts one LOS from the other directly.

**Not available to us:** ROMPOS raw data and daily solutions are closed. Nothing derived from them enters the repository.
