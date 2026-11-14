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
| Sentinel-1 via HyP3 | C-band interferograms for the same months | Yes | Second radar | 05 |
| Copernicus GLO-30 DEM | Elevation | n/a | Troposphere slope | 02 |

**Not available to us:** ROMPOS raw data and daily solutions are closed. Nothing derived from them enters the repository.
