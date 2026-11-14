# The advisor's rehearsal (12 Nov 2026)

Before the event, our advisor ran a full pipeline on real NISAR data over Ocnele Mari: the *dancing-on-salt* rehearsal kit. It is **prior work**, and it is declared in [../CITATIONS.md](../CITATIONS.md#prior-work-and-advisor-help). Whether we adopt its code is decision O-03.

This file records what it found, because those findings shape our plan. **These are its numbers, not ours.** Our own numbers come from our pipeline during the event.

## Verdict

The pipeline works end to end on real NISAR data. All eight steps ran, and 22 pairs streamed in 28 min on a home line with 6 workers.

But **Ocnele Mari's subsidence, about −25 mm/yr at most, is below what NISAR's first months resolve per pixel**: 37 to 51 mm/yr of scatter on stable ground, from 4 to 6 months in two windows. Before building on any rate, we need zone-level statistics, better corrections, or a different framing (decision O-01).

## What it found

| What | Result (12 Nov 2026) | What it means for us |
| --- | --- | --- |
| How fast the ground moves | EGMS 2019 to 2024: L3 Up minimum −23.8 mm/yr, L2b LOS minimum −17 to −26, zone medians −0.4 to −10. The deck's "−250 mm/yr" was a factor-10 error, corrected in deck v10 | Never quote −250. Our copy of the deck still has it on slides 1, 5 and 6 |
| Coverage | 129A: 13 pairs, 15 dates, with a gap from 18 Jan to 23 Jun 2026 (two groups). 094D: 9 pairs, 10 dates, from June to October only. No triplets on either | "A winter window and a summer-to-autumn window", not "a year" |
| Pixels with a series | 94 % (129A), 85 % (094D) | The mask rule works once it is decoded correctly |
| Troposphere | Before the correction, 094D's rate tracked elevation at −8.6 mm/yr per 100 m (r = −0.43) over 175 to 1,970 m of relief. The per-pair slope came out at a median of 0.8 to 1.5 mm per 100 m, at most 3.7 | The elevation slope is in the proposed decisions |
| NISAR up − EGMS up, stable ground | +34 mm/yr before the troposphere correction, **+6.4** after (5,790 points), with 27 mm/yr scatter | Claim A is a real test |
| The tie | Offsets −8.8 (094D) and −6.0 (129A) mm/yr. The model's own share is only +0.25 and −0.62 mm/yr in a 50 km window | The model fixes the level; the scatter is atmospheric |
| Pixel scatter, stable ground | **37 (129A), 51 (094D) mm/yr.** Theory, with about 1 cm of atmosphere per date over 4 months, gives about 33 mm/yr | The data limit it; it is not a bug. Hence zones, not pixels |
| Salt zones, LOS median | −4.6 (129A, passes the sign check) and **+27.5** mm/yr (094D, fails). EGMS Up in the same zones: −2.0 mm/yr | The phase sign is not confirmed on real data (T3) |
| Stations | VLC1 (NGL, data to 2018): NISAR − GNSS −6.1 and −6.8 mm/yr. HORE (NGL, to 2020): +33 and +17. Both "agree" only because the tolerance is huge. The VLC2 and HORE published rows have no vertical yet | Show the tolerance in every pin; 04 fills Table S3 |
| Rate from pairs vs from dates (synthetic) | Fitting the pairs inflated the error from 2.8 to 14.6 mm/yr | Rates are fitted through dates |
| Annual term below 1.5 years (synthetic) | A free annual term moved the bowl from −105 to −130 mm/yr | No annual term |
| Synthetic end to end | Passes: bias +0.13 mm/yr, zones within 2 % | A known-answer test is worth keeping |

## What it changes in our plan

1. The story is honest about two windows and a gap, and leads with zones, not pixels.
2. The sign, the troposphere and the EGMS stable-ground check are early tests (T3, T4, T8), not afterthoughts.
3. Station pins show their tolerance, so a 35 to 60 mm/yr "agree" cannot pass as agreement.
4. Closure needs GSLC pairs or is declared untested.
5. The products contract follows the kit's, so both paths of O-03 stay open.

## Still open after the rehearsal

These are the kit's own open questions, adapted to D-001.

- **The phase sign on real data:** check T3.
- **Why 094D's zones read +27.5 mm/yr:** atmosphere, unwrapping or sign?
- **Do the GUNW weather-model cubes beat the elevation slope?** (Tier 3)
- **Does Sentinel-1 over the same months see the bowl?** (T10, 05)
- **Why is there no NISAR from January to June 2026?** (O-14)
- **The EGMS GNSS model CSV link,** for the model swap (O-06).
- **May the Muntean et al. 2026 supplement values be quoted in the app?** (O-13)

## What the rehearsal did not check

- Praid, which is out of scope here (D-001).
- A model swap against the EGMS GNSS model. It compared against a rigid plate only.
- The 2020 to 2024 EGMS tile. It used 2019 to 2023.
- The page on phones.
