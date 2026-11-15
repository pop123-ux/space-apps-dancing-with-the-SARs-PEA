# Dancing on Salt: submission text

**Owner:** 01 · Lead and story (Mario)

The text for the NASA Space Apps 2026 project page, challenge [Dancing with the SARs](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/). Each section below matches one field of the submission form. Every number is from `products/ocnele_mari/`, checked 15 Nov 2026.

## Project name

Dancing on Salt

## High-level summary

Ocnele Mari, a town in Vâlcea county, Romania, sits on salt that has been dissolved and pumped out as brine since the 1950s; the ground above has sunk and collapsed before, most visibly at Lacul Țeica in 2001. We built a public web map that lets anyone see how that ground moves, measured from space by two radar satellites: NASA–ISRO's NISAR (L-band, in its first year) and ESA's Sentinel-1 (C-band). The page plays the ground through time, compares the two radars on the same months, checks them against GPS stations and the European Ground Motion Service, forecasts each part of the town to 2029, and lets a resident drop a pin or pick a house to see how that spot moves against the ground around it. It says plainly where the radar cannot yet see the motion: NISAR's early products are still too noisy for the slow sinking here, while Sentinel-1 sees three of the four salt fields moving away from the satellite by about 5 to 10 mm a year. It is an honest screen of what space radar can and cannot tell a town today, not a warning system.

## Links

- **Project (live page):** https://pea-dancingwiththesars.vercel.app
- **Code and data lists:** https://github.com/pop123-ux/space-apps-dancing-with-the-SARs-PEA
- **Presentation:** a 7-slide PowerPoint, with no video (team decision).

## Project details

**What it does.** The page opens on Ocnele Mari, with its town boundary, the four salt fields (Lacul Țeica, Țeica east, Ocnița · Goruniș, Slătioarele), two GNSS stations (HORE, VLC) and one coloured dot per measured spot. Red means the ground moved away from the satellite, usually sinking; blue means it moved toward it. You can:

- switch between NISAR, Sentinel-1 and Compare, and between each satellite's morning and evening pass;
- play the ground through time, from May 2025 (Sentinel-1) and November 2025 (NISAR) to November 2026;
- select an area, a salt field or a house, and read its trend, its forecast to 1 January 2029, which way the ground moves, and a summary in plain words;
- drop a pin on any spot to see its history and whether it moves differently from the ground 300 m around it, beyond the measured noise;
- see where the satellites are now and when they next pass over the town.

**What we found** (15 Nov 2026).

- **History:** the European Ground Motion Service (Sentinel-1, 2020 to 2025) shows Ocnița · Goruniș sinking about 19 mm a year, and the other three fields 2.5 to 4 mm a year.
- **NISAR:** cannot see that yet. On stable ground its zone rates vary by about ±21 mm a year, more than the motion we are looking for. At the current noise, a 25 mm-a-year sink would become visible around 2029. Its evening pass failed our sign check and is shown flagged.
- **Sentinel-1:** over May 2025 to November 2026, its evening pass shows Lacul Țeica, Țeica east and Slătioarele moving away from the satellite against their surroundings, by about 9.7, 4.9 and 5.9 mm a year.
- **Checks:** 5 pass, 6 warn, 1 fail and 12 for information. The warnings are real limits (noise, few shared dates), not errors.

**Why it matters.** People live and build on this ground. Official surveys are rare and expensive; satellite radar covers the whole town every 6 to 12 days for free. The page turns that into something a resident can read, and is honest about its limits, so it does not give false comfort or false alarms.

**How we built it.**

- **NISAR:** official GUNW interferograms, 22 pairs. We fit a time series with a stable-ground reference and a coherence cut. The result is tied to a European GNSS velocity model (EuVeM2022) and checked by swapping in a second model (EGMS GNSS).
- **Sentinel-1:** 374 burst interferograms ordered on ASF HyP3, fitted on a 40 m grid with six processing variants.
- **Validation:** an independent validator checks the phase sign, held-out GNSS stations, the scatter of the tie, data gaps, and NISAR against Sentinel-1.
- **Forecast:** Chronos-2, a pretrained time-series model used zero-shot, per 240 m cell of the town. Each cell is tested on its last 60 days against a "no change" guess.
- **The page:** a static site with MapLibre GL JS that reads only the products written by our scripts.

**Tools.** Python (NumPy, SciPy, pandas, h5py, pyproj, rasterio, matplotlib, asf_search, hyp3_sdk), Chronos-2 with PyTorch on CPU, JavaScript with MapLibre GL JS, Playwright for testing, GitHub Actions and Vercel.

**Limits.**

- NISAR products are beta and provisional, "not intended for scientific research".
- A radar measures only along its line of sight, and Sentinel-1 here is relative to the surrounding terrain.
- A rate is the slope over the window shown.
- The forecast is indicative: it beat "no change" in 49 % of the town's cells on one pass and 78 % on the other, and 2029 is far beyond anything we could test.
- The page is not a hazard or building assessment. For official notices, follow ISU Vâlcea and the Ocnele Mari town hall; before building, commission a geotechnical study.

## Use of artificial intelligence

- **Claude Code (Anthropic):** each team member ran it for their own role, under shared rules (`CLAUDE.md`). It wrote and reviewed code and documentation, and people checked the results.
- **ChatGPT (OpenAI):** helped summarise material before the event and with some Sentinel-1 and forecast work.
- **Figma Make:** gave a first visual design, which was replaced.
- **Chronos-2 (Amazon):** a pretrained forecasting model, used without retraining for the prediction.

The radar measurements and checks come from our own scripts on open data. Every substantive use of AI, and what a person checked, is logged in `AI-DISCLOSURE.md`.

No AI-generated images, video or audio are used in the page or the slides. The team logo's origin is being confirmed; if it was made with AI, it will carry a visible "AI-generated" label, as the rules require.

## NASA data

| Name | Link |
| --- | --- |
| NISAR mission (NASA JPL) | https://nisar.jpl.nasa.gov |
| NISAR data at the Alaska Satellite Facility | https://asf.alaska.edu/nisar/ |
| NISAR product documentation (GUNW interferograms, GSLC images, SME2 soil moisture) | https://nisar-docs.asf.alaska.edu/ |
| ASF Search API | https://docs.asf.alaska.edu/api/basics/ |
| ASF Search (Vertex) | https://search.asf.alaska.edu/ |
| NASA Common Metadata Repository (CMR) search API | https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html |
| ASF HyP3 on-demand processing | https://hyp3-docs.asf.alaska.edu/ |
| HyP3 Burst InSAR product guide | https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/ |
| OPERA L4 TROPO-ZENITH (NASA JPL) | https://www.jpl.nasa.gov/go/opera/products/tropo-product/ |
| RAiDER weather-delay tool (NASA JPL) | https://github.com/dbekaert/RAiDER |
| ISCE2 processing software (NASA JPL) | https://github.com/isce-framework/isce2 |
| asf_search Python package | https://github.com/asfadmin/Discovery-asf_search |
| hyp3_sdk Python package | https://github.com/ASFHyP3/hyp3-sdk |
| NASA Earthdata login | https://urs.earthdata.nasa.gov |

## Space agency partner and other data

| Name | Link |
| --- | --- |
| Sentinel-1 mission (ESA, Copernicus) | https://sentiwiki.copernicus.eu/web/s1-mission |
| European Ground Motion Service (EGMS) | https://egms.land.copernicus.eu/ |
| EGMS GNSS calibration model | https://land.copernicus.eu/en/technical-library/gnss-calibration-data-2023-csv |
| Copernicus GLO-30 elevation model | https://registry.opendata.aws/copernicus-dem/ |
| EuVeM2022 European velocity model (Lantmäteriet) | https://www.lantmateriet.se/en/geodata/gps-geodesi-och-detaljmatning/referenssystem/euvem2022/ |
| EuVeM2022 paper (Steffen et al. 2025) | https://doi.org/10.1093/gji/ggaf052 |
| Nevada Geodetic Laboratory GNSS velocities | http://geodesy.unr.edu/ |
| Muntean et al. 2026, Solid Earth (station rates) | https://se.copernicus.org/articles/17/747/2026/ |
| ECMWF and ERA5 weather via Open-Meteo | https://open-meteo.com/en/docs/historical-weather-api |
| OpenStreetMap (town boundary, buildings) | https://www.openstreetmap.org/copyright |
| OpenFreeMap vector tiles | https://openfreemap.org |
| Esri World Imagery | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f5a7c08f3e2abd8 |
| MapLibre GL JS | https://maplibre.org |
| Chronos-2 (Amazon, Apache-2.0) | https://huggingface.co/amazon/chronos-2 |
| PyTorch | https://pytorch.org |
| NumPy | https://numpy.org |
| h5py | https://www.h5py.org |
| pyproj | https://pyproj4.github.io/pyproj/ |
| Playwright | https://playwright.dev |
| Inter and Instrument Serif fonts (SIL Open Font License) | https://fonts.google.com |
| Claude Code | https://claude.com/claude-code |
| Repository structure adapted from dmanpark/dancing-with-the-sars | https://github.com/dmanpark/dancing-with-the-sars |

The salt-field outlines come from the team advisor's starter kit (Miluță Dulea-Flueraș, 12 Nov 2026). Full citations, versions and access dates: `CITATIONS.md`.

## Team

Mario (lead and story), Alexandru and Eric (NISAR data and InSAR analysis), Matei (geodesy), Paul (validation), Darius (web app). NASA Space Apps Cluj-Napoca, 14 to 15 November 2026.
