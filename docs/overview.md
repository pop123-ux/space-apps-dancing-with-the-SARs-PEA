# Dancing on Salt

**Owner:** 01 · Lead and story (Mario)

Version 1, Sat 14 Nov 2026. Methods, file formats and done-criteria per role are in [build-spec.md](build-spec.md). The evidence behind the plan is in [rehearsal.md](rehearsal.md) and [data.md](data.md).

We're building a web page that shows anyone how the ground moves above the salt-brine fields of Ocnele Mari, in Vâlcea county, Romania. The measurement is NISAR's L-band radar: 22 interferograms from November 2025 to October 2026, tied to open GNSS velocity models. Every number is checked against stations, the European Ground Motion Service (EGMS) and Sentinel-1. The page opens on the town and plays the ground through time. Where the radar cannot yet see the motion, it says so. Built by six people in the 48 hours of NASA Space Apps, 14 to 15 Nov 2026.

## Why it matters

**The place.** At Ocnele Mari, salt is extracted as brine from wells (the advisor's deck: "brine extraction"), which leaves caverns under the town and its edges. The team's site notes ([../INFO.md](../INFO.md)) list where the ground has given way or is at risk:

- Țeica (Socon-Țeica), with collapses since 2001.
- Câmpul II de sonde, where a cavern collapsed in 2001 and damaged homes and land.
- Câmpul I de sonde, with a cavern collapse in 2009.
- Lunca and Ocnița, where land is classed as at risk from salt extraction.

**The motion.** EGMS, which is built from Sentinel-1, shows the ground there sinking by up to about 25 mm/yr from 2019 to 2024, with salt-zone medians of 0.4 to 10 mm/yr (rehearsal, 12 Nov 2026). That is slow, steady and easy to miss.

**Why now.** NISAR (NASA–ISRO) carries the first free L-band radar that images all land every 12 days. Its interferograms over Romania became public in its first months of operations, and they are still labelled beta or provisional. Nobody has shown what they can see at a slow salt site like this one.

**Who it's for.** People in Ocnele Mari and the county, teachers, and anyone curious what a radar satellite can and cannot see. Also local authorities and the people who build ground-motion maps, who need to know when NISAR adds to Sentinel-1 and EGMS.

## The page

One page. The map fills the screen, and a card at the bottom (side on a laptop) carries the story stops. The page is static files on GitHub Pages: no login, no server.

| Part | What you see | What it tells you | Behind it |
| --- | --- | --- | --- |
| **Opening view** | The town at zoom 13 (D-002). Zoom out and Romania appears, blurred | Where we are, and that only this place is data | `manifest.view` |
| **The slider** | Cumulative change since the first date, one frame per pass, per track. A "no data" card from 18 Jan to 23 Jun 2026 | The ground moving, and the honest gap | `frames/` |
| **The rates** | Vertical and east–west rates; pixels with \|rate\| < 2σ greyed out | Where the motion beats its error, and where it does not | `up.png`, `east.png`, `los_*.png` |
| **Honest pins** | Each station: what NISAR says, what GNSS says, the tolerance, and whether they agree. A red pin means they do not, with the reason | The satellite and the stations checking each other | `stations.geojson` |
| **Story stops** | Three stops chosen by 01 (O-01) | The place, what the radar sees, the check | `manifest.story`, `series.json` |
| **The checks** | Every check, pass, warn, fail or info, in plain words | What to believe and what not to | `checks.json` |

## What we will show

Which claim leads is decision O-01. Each candidate has a test that could come out against us, and each is reported either way.

| Claim | Test | It fails if |
| --- | --- | --- |
| **A. The frame holds.** NISAR, tied to EuVeM2022, agrees with EGMS on stable ground. | Median of NISAR up minus EGMS up on stable EGMS points outside the zones | The absolute median is 1.5 mm/yr or more. The rehearsal got +6.4 mm/yr, so this is a real test |
| **B. The salt zones sink.** At zone level, NISAR sees the subsidence on both tracks. | Zone-median LOS rate with a 95 % bootstrap interval, per track | The interval includes zero, or the two tracks disagree in sign (the rehearsal had −4.6 on 129A against +27.5 mm/yr on 094D) |
| **C. A second radar agrees.** Sentinel-1 over the same months gives the same zone rate. | Sentinel-1 HyP3 zone rate against NISAR's, same dates | They differ by more than their combined errors |
| **D. The stations agree.** Held-out GNSS stations match NISAR in each line of sight. | \|NISAR − GNSS\| ≤ max(2 mm/yr, 2σ combined), tolerance shown | Any station disagrees after screening. A huge tolerance counts as "not tested", not "agrees" |

If B fails, the story becomes "the honest test": what NISAR's first months can and cannot see at a slow salt site. The page uses the same layers and states the numbers.

## The data

There are 22 NISAR GUNW pairs over the town: 13 on 129A ascending and 9 on 094D descending, with no acquisitions from 18 Jan to 23 Jun 2026. The references are EuVeM2022, NGL MIDAS, Muntean et al. 2026, EGMS Ortho and Sentinel-1 via HyP3. Details and traps are in [data.md](data.md); sources are in [../CITATIONS.md](../CITATIONS.md).

## The slides

The submission is a **7-slide PowerPoint, with no video** (D-003, locked).

- **The file:** 01 assembles the deck at `slides/dancing-on-salt.pptx`.
- **Owners:** each slide has an owner role who supplies its content and checks its numbers.
- **The outline below is proposed;** 01 confirms it at the hour-2 review.
- **Rules:**
  - Screenshots come from the live page. A mock or demo screenshot always shows the "Simulated, not data" banner.
  - Every number comes from the frozen build.
  - No AI-generated images.

| Slide | Content | Owner | Source |
| --- | --- | --- | --- |
| 1 | **Title and hook:** Dancing on Salt; the town, and what lies under it, in one sentence | 01 | 01's story stops (O-01) |
| 2 | **The place and the problem:** Ocnele Mari, brine extraction, the collapses of 2001 and 2009, who lives there | 01 | `INFO.md`, local reports (Q6) |
| 3 | **The data:** NISAR L-band, 22 pairs, the winter and summer-to-autumn windows, the January to June gap, beta/provisional | 02 | `docs/data.md`, `data/scenes/ocnele_mari_gunw.csv` |
| 4 | **The method:** pairs to rates (03), tied to a GNSS frame the way EGMS does it (04), up and east | 03, 04 | `ts.npz`, `calib.json`, `up_east.npz` |
| 5 | **The map:** screenshots of the live page, the opening view (D-002), the slider with the gap, a red pin; the demo link | 06 | the live page |
| 6 | **What holds up, and what NISAR cannot see yet:** the checks, the honest pins, the zone rates with their intervals | 05, 03 | `checks.json`, `stations.geojson`, `series.json` |
| 7 | **Team, credits, AI use, prior work, links** | 01 | `CITATIONS.md`, `AI-DISCLOSURE.md` |

## Why the results will hold up

- **Rates only where they beat their error.** Zone medians with intervals; greyed pixels below 2σ.
- **Rates through dates, not pairs; no annual term below 1.5 years.** Both choices come from the rehearsal's synthetic tests.
- **One frame for everything, and a tie that keeps the stations out,** so the stations can test it.
- **Stations are screened first.** In our earlier HAR1 study, the station's rooftop mast swung 38 mm a year and frost-jacked by up to 5.5 cm while the building stayed put.
- **Short pairs can bias rates.** In our 2024 to 2026 Sentinel-1 stack, 8-day pairs read 20 to 40 % higher than 16-day pairs. We test it where we can and say where we cannot.
- **Simple models first.** In an earlier study our LSTM lost to a seasonal model out of sample (6.6 against 5.4 mm). Any ML here must beat its baseline on held-out checks.
- **"Possible, not proven"** where the data cannot decide (as at Hârșova).
- **A synthetic stack with a known answer** runs through the same code, and it includes a planted lying station that the checks must catch.

## How it scores

These are past years' criteria; 01 checks the 2026 sheet.

| Criterion | What we show |
| --- | --- |
| Impact | Safer salt towns, and a check anyone can rerun from open data |
| Creativity | Satellite and stations checking each other; the ground moving on a slider |
| Validity | Rates only where they beat their error; stations held out of the tie; EGMS history; Sentinel-1 |
| Relevance | NISAR first, interactive, open source, hometown context |
| Presentation | Seven slides and one live map; numbers second; the hook on slide 1 |

## Scope

Tier 1 alone is a complete submission. Everything after it raises the ceiling without risking the floor.

| Tier | What | Owner |
| --- | --- | --- |
| 1 | Both tracks streamed and QA'd | 02 |
| 1 | Rates per track, sign checked | 03 |
| 1 | The tie | 04 |
| 1 | Every check written and explained | 05 |
| 1 | The page on real files: view, slider, pins, labels | 06 |
| 1 | Story, the 7 slides, page, AI use, credits | 01, with each slide's owner |
| 2 | Up and east on the common window; zone intervals | 03 |
| 2 | Sentinel-1 comparison | 05 |
| 2 | Model swap | 04 |
| 2 | Story mode, phone polish | 06 |
| 3 | GSLC closure; weather-model troposphere; an ML/AI component (O-08); a GCOV angle | 02, 03 |

**Out of scope:** other sites (D-001), damage claims about individual buildings, forecasts, and any ROMPOS data.

## The 48 hours

Hour 0 is the kickoff, set by 01 in `STATUS.md`. **Hour by hour, per role: [schedule.md](schedule.md).** The steps behind each cell are in [build-spec.md](build-spec.md). The summary:

| Role | 0 to 6 | 6 to 18 | 18 to 30 | 30 to 40 | 40 to 48 |
| --- | --- | --- | --- | --- | --- |
| 01 Lead | Hour 0, guide, hour-2 review, contract freeze, slide outline | Story, checkpoint at 12, slides 1 and 2 | Checkpoint at 24, slides first draft | `SUBMISSION.md`, credits, AI use, slide 7 | Freeze, final slides, submit |
| 02 Data | Token, T1, T2, both tracks on disk | DEM, synthetic stack, QA | GSLC pairs (Tier 3) | Frames with 06, slide 3 | Check slide 3 against the frozen build |
| 03 InSAR | Method, first pairs | Rates, T3, T4, zones | Up and east | Grey-out, errors, freeze, slides 4 and 6 | Check slides 4 and 6 |
| 04 Geodesist | `refs.py`, Table S3 | The tie | Model swap, T8 | Final tie, frame paragraph, slide 4 | Check slide 4 |
| 05 Validator | HyP3 order (hour 0 to 1), EGMS, screening | Sentinel-1 rates | `validate.py`, every WARN | Agree flags, red team, slide 6 | Rerun on the frozen build; check slide 6 |
| 06 App | Mock site, Pages, blur | Map, slider, `export.py` | Pins, story mode, phone | Accessibility, slide 5 screenshots | Polish (no numbers) |

**Gates:**

- **Hour 2:** decisions and contract frozen.
- **Hour 12:** first real rate map.
- **Hour 24:** Tier 1 numbers exist.
- **Hour 40:** numbers frozen.
- **Submit** at least 3 hours before the deadline.

If a gate slips by more than an hour, cut from the top of this ladder:

1. Tier 3, all of it.
2. Story mode polish (keep the stops as cards).
3. The model swap.
4. Sentinel-1.
5. Up and east (keep LOS per track).

Never cut the sign check, the honest pins, the gap label, the slides or the submission text.

## Risks and fallbacks

| Risk | When we know | Fallback |
| --- | --- | --- |
| Venue network too slow to stream | Hour 1 (T1) | Download one track in full; Ocnele Mari only |
| The phase sign looks wrong | Hour 14 (T3) | Investigate sign, unwrapping and atmosphere; report; never flip to pass |
| The time series does not run | Hour 14 | Show the cumulative sum of the 12-day pairs, labelled as such |
| The tie fails | Hour 20 | One constant per track on EGMS stable ground; say so |
| The zones do not beat their error | Hour 24 | "The honest test" framing (O-01 a) |
| HyP3 is late | Hour 8 (T10) | Sentinel-1 moves to Tier 3 |
| The page does not work on a phone | Hour 30 (T9) | Map, slider and one card |
| The interactive page fails | Hour 36 | Static story map plus screenshots on the slides |
| Anything changes numbers after hour 40 | Hour 40 | Freeze; text, styling and slides only |

## At kickoff

- [ ] Everyone registered at the same local event, on the Members tab (teams are 1 to 6 people).
- [ ] Everyone has an Earthdata login and has run [../prompts/setup.md](../prompts/setup.md).
- [ ] 01 has read the 13 Nov submission and judging guides aloud (O-02), and asked the local lead whether the advisor kit counts as declared prior work.
- [ ] 05 has ordered the Sentinel-1 jobs.
- [ ] The hour-2 review is done, and the decisions and contract are frozen.

## After Space Apps

1. Rerun on NISAR's validated reprocessing when `NISAR_L2_GUNW_V1` fills.
2. Extend the stack past October 2026. A full year of dates lets the annual term in, and closure triplets may appear.
3. Add Praid and Slănic, the sites D-001 left out.
4. Publish the zone series and the checks as a small open benchmark for salt-mining subsidence.

## Sources

- Space Apps challenge: [Dancing with the SARs](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/) and its [Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources) (unreachable from the setup machine on 14 Nov; 01 lists what we use).
- NISAR data and docs: [ASF](https://search.asf.alaska.edu), [NISAR docs](https://nisar-docs.asf.alaska.edu/).
- EGMS: [egms.land.copernicus.eu](https://egms.land.copernicus.eu/).
- EuVeM2022: [Lantmäteriet](https://www.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/lantmateriets-doi-objects/euvem2022/).
- Every data source with its credit line: [../CITATIONS.md](../CITATIONS.md).
