# 02 · NISAR data — Alexandru & Eric

**Mission.** Get every NISAR interferogram over Ocnele Mari onto disk, cut to the site window, with the ionosphere removed and bad pixels masked. Do it fast and repeatably.

**You own:** `fetch.py` (stub) → `data/work/<site>/<track>/`. You share 02 and 03 with each other; split them as you like.

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| 0–2 | Earthdata login → *Generate Token* → `EARTHDATA_TOKEN` (`.env`, never committed). Build `search()`, then run `python fetch.py ocnele_mari --list`. | You see 22 pairs: 129A ×13, 094D ×9 |
| 2–6 | `read_pair()` with HTTP range reads, the mask decode, ionosphere subtraction and the largest connected component. Test the speed on the **venue Wi-Fi** (T6). Open one pair and show it to the team. | Both tracks on disk; one picture shown |
| 6–18 | QA per pair: `valid_share`, `iono_used`, `iono_std`, `iono_interp`. DEM (`write_dem`). Help 03 read the masks. *(Former Praid slot, free: O-15.)* `synthetic()` for the known-answer test, if 03/05 need it. | QA table per pair; synthetic stack exists |
| 18–30 | GSLC pairs (24/36-day) for the closure test, if O-07 keeps it. | — |
| 30–40 | Help 06 with slider frames and sizes. | — |
| 40–48 | Captions, support; no number changes. | — |

## Your hand-off (DRAFT; agree changes with 03)

`meta.json` (grid, wavelength, direction, look, polarization) · `geom.npz` (los_e, los_n, los_u, target → sensor) · `<ref>_<sec>.npz` (phase in radians with the ionosphere removed and NaN = masked; coh; QA fields) · `dem.npz`. Details are in the `fetch.py` docstring.

## Starting points (CMR on 14 Nov; advisor rehearsal on 12 Nov)

- **Inventory:**
  - 129A, frame 24: 13 pairs, 7 Nov 2025 → 21 Oct 2026, nothing 18 Jan → 23 Jun 2026.
  - 094D, frame 66: 9 pairs, 20 Jun → 18 Oct 2026.
  - Collections `NISAR_L2_GUNW_BETA_V1` + `NISAR_L2_GUNW_PROVISIONAL_V1`. Keep the newest processing of each pair.
- **Streaming works:** about 58 MB per pair for a 50 km window, and all 22 pairs in about 30 min with 6 workers on a home line.
- **Layers:** `unwrappedPhase`, `ionospherePhaseScreen`, `coherenceMagnitude`, `connectedComponents` and `mask`, plus the `radarGrid` cube for the LOS vectors. That cube also holds weather-model troposphere layers, which may help 03.

## Watch out

- **`mask` is a 32-bit bitfield** (spec 1.4), but older pairs store a uint8 code.
  - Bits 0–7: water/subswath code. Bits 8–23: anomaly flags. Bit 24: ionosphere interpolated (the phase is still good).
  - Cast to uint32 and decode with `mk & 0xFF`, **never** `mk // 100`. A naive decode dropped 98 % of the 094D window.
- **The ionosphere screen is in the product but not applied.** Subtract it, and record per pair whether it was available.
- **Keep the largest connected component only.** Other components may be off by 2π, which is 12 cm of LOS.
- **The first pair of a track fixes the grid.** If ASF reprocesses a pair onto another grid, stop.
- **The tokens:** send the token to ASF only. The redirected S3 URL gets none.
- **The products are beta/provisional.** Say so.

## Decisions you drive or feed

O-07 GSLC closure pairs · O-08 an ML/AI component (with 03) · O-11 window size (with 04) · O-14 why there's no data from January to June.

## Questions to answer during the event

- How many MB and seconds per pair on the venue Wi-Fi? Is 6 workers right?
- Is `ionospherePhaseScreen` filled for every pair, or NaN for some?
- Do 129A and 094D share a UTM zone? (split.py should cope either way; write it down.)

## Done when

Both tracks are on disk with a QA line per pair, `stack.py` reads them without questions, and the synthetic stack exists for the known-answer test.

## Reference image (from the original README, 02 & 03)

<img width="2553" height="989" alt="02 & 03 reference" src="https://github.com/user-attachments/assets/38800064-da21-4e08-9c28-09cb83797c1a" />
