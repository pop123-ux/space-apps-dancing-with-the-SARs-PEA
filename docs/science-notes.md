# Science notes

These are the reasons behind the guardrails in BUILD.md §10. Everyone can append; keep each note short and sourced.
The sources are: **[deck]** the advisor's team plan; **[kit]** the advisor's rehearsal kit, 12 Nov 2026 (prior work); **[CMR]** our NASA CMR query, 14 Nov 2026.

## The site, in numbers

- Ocnele Mari subsides from brine extraction. **EGMS 2019–2024: at most about −25 mm/yr**. L3 Up minimum −23.8, L2b line-of-sight minimum −17 to −26, salt-zone medians −0.4 to −10. **[kit]**
- The deck's "bowls to −250 mm/yr" was a **factor-10 error**, corrected in deck version 10. Older copies of the PDF still show it. **Never quote it.** **[kit]**
- Sub-zones (site notes, [INFO.md](../INFO.md)): Țeica / Socon-Țeica (collapses since 2001), Câmpul II de sonde (cavern collapse 2001), Câmpul I de sonde (collapse 2009), and Lunca and Ocnița (risk zones). The draft zone polygons in `common.py` still need these names (03 with 01).

## The data

- **GUNW coverage over the town:** 22 pairs. **[CMR]**
  - 129A ascending, frame 24: 13 pairs, 15 dates, 7 Nov 2025 → 21 Oct 2026, with **no acquisitions 18 Jan → 23 Jun 2026**.
  - 094D descending, frame 66: 9 pairs, 10 dates, 20 Jun → 18 Oct 2026.
  - Pairs are mostly 12 days long, plus 24-day pairs where an acquisition is missing. The two summer 24-day pairs (129A 17 Jul → 10 Aug, 094D 26 Jul → 19 Aug) bridge the 27 Jul – 10 Aug 2026 instrument data gap that NASA lists.
- **Collections:** `NISAR_L2_GUNW_BETA_V1` (4 pairs) and `NISAR_L2_GUNW_PROVISIONAL_V1` (18). The validated `NISAR_L2_GUNW_V1` is empty. All are labelled "not intended for scientific research". **[CMR]**
- **The mask layer** is a 32-bit bitfield: bits 0–7 water/subswath code, 8–23 anomaly flags, 24 "ionosphere interpolated". Older pairs store a uint8 code. **[kit]**
- **The ionosphere screen** ships in the product but is not applied. **[kit]**

## What the rehearsal measured at Ocnele Mari

These are the kit's numbers, quoted as a baseline, not as our results. **[kit]**

| Quantity | Value |
|---|---|
| Pixels with a series | 94 % (129A), 85 % (94D) |
| Troposphere before correction | 094D rate tracked elevation at −8.6 mm/yr per 100 m (r = −0.43) |
| NISAR up − EGMS up, stable ground | +34 → **+6.4** mm/yr after the elevation-slope correction; scatter 27 mm/yr |
| Tie offsets | −8.8 (094D), −6.0 (129A) mm/yr; the model's own share is only +0.25 / −0.62 mm/yr |
| Pixel scatter on stable ground | **37 (129A), 51 (094D) mm/yr**. Theory, with ~1 cm of atmosphere per date over 4 months: ~33 mm/yr. The data limit it; it is not a bug. |
| Salt zones, LOS median | −4.6 (129A) against **+27.5** (094D) mm/yr. EGMS Up in the same zones: −2.0 mm/yr. |
| Stations | VLC1: NISAR − GNSS −6.1 / −6.8 mm/yr; HORE: +33 / +17. Both "agree" only because the tolerance is huge. |
| Closure triplets | 0 on both tracks |

**Verdict [kit]:** the pipeline works, but Ocnele Mari's subsidence is below what NISAR's first months resolve **per pixel**. Zone-level medians, longer stacks or a different angle are the ways forward (decision O-01).

## Lessons from our own Romanian studies [deck]

1. **The ground truth can lie.** HAR1's rooftop mast swings about 38 mm between January and July and jumped 2.4–5.5 cm on the coldest nights; the building did not move. Look at EGMS on the station's own building before trusting it.
2. **Short pairs bias rates.** In our 2024–2026 HyP3 stack, 8-day pairs read 20–40 % higher than 16-day pairs. Real motion would not.
3. **A year is not a rate.** Fit the yearly cycle before quoting mm/yr. We have under 1.5 years, so we fit no annual term: a free one moved a synthetic bowl from −105 to −130 mm/yr. **[kit]**
4. **Compare zones, not pixels.** Single pixels scatter by mm/yr; medians over blocks and towns hold up.
5. **Simple models first.** Our LSTM forecast lost to a three-year seasonal model out of sample: 6.6 mm against 5.4 mm.
6. **Say "possible, not proven".** At Hârșova a 2025 rise stays open until new EGMS data can test it. Judges trust a map that names its limits.

## Method facts worth keeping [kit]

- **Fit the rate through the dates, not the pairs.** Fitting the pairs as independent observations inflated the error from 2.8 to 14.6 mm/yr in the synthetic test.
- **The gap splits a track into groups.** Give each group its own offset in the rate fit. The slider is flat across the gap: never interpolate it.
- **North is ignored** in the up/east split. Both looks are nearly blind to it (|n| ≈ 0.1).
- **σ assumes independent dates,** so treat it as a lower bound.
- **One frame for everything:** Eurasia-fixed. Plate motion is nearly uniform across a 50 km window, so it goes into the tie offset, but mixing frames would not cancel.
- **The velocity model** (0.1° grid) fixes the frame-wide level and slopes only. It says nothing about a 2 km bowl.
- **Unwrapping:** a 2π jump is 12 cm of LOS. At −25 mm/yr the bowl moves about 1 mm per 12 days, far from any wrap. A wrong connected component is the real risk.

## Conventions

These match CLAUDE.md §5:

- **LOS:** mm/yr or mm, positive towards the satellite.
- **Up and east:** up positive, east positive.
- **Reference frame:** Eurasia-fixed.
- **Dates:** ISO.
- **Fits:** time in years since 2026-01-01.
- **Colours:** RdBu, red = sinking or away from the satellite.
- **Processing grid:** UTM, 80 m pixels.

## Open science questions

The phase sign on real data (T2) · whether 094D's +27.5 mm/yr in the zones is atmosphere, an unwrapping error or the sign · whether the weather-model cubes in the GUNW `radarGrid` beat the elevation slope · whether Sentinel-1 over the same months sees the bowl · why there is no NISAR data from January to June 2026 (O-14).
