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
- **Project demo (7 slides, no video):** https://canva.link/9mkh75wjai0h8zn

## Project details

**What it does.** The page opens on Ocnele Mari, with its town boundary, the four salt fields (Lacul Țeica, Țeica east, Ocnița · Goruniș, Slătioarele), two GNSS stations (HORE, VLC) and one coloured dot per measured spot. Red means the ground moved away from the satellite, usually sinking; blue means it moved toward it. You can:

- switch between NISAR, Sentinel-1 and Compare, and between each satellite's morning and evening pass;
- play the ground through time, from May 2025 (Sentinel-1) and November 2025 (NISAR) to November 2026;
- select an area, a salt field or a house, and read its trend, its forecast to 1 January 2029, which way the ground moves, and a summary in plain words;
- drop a pin on any spot to see its history and whether it moves differently from the ground 300 m around it, beyond the measured noise;
- see where the satellites are now and when they next pass over the town.

**What we found** (15 Nov 2026).

- **History:** the European Ground Motion Service (Sentinel-1, 2020 to 2025) shows Ocnița · Goruniș sinking about 19 mm a year, and the other three fields 2.5 to 4 mm a year.
- **NISAR:** cannot see that yet. On stable ground its zone rates vary by about ±21 mm a year, more than the motion we are looking for. At the current noise, a 25 mm-a-year sink would become visible around 2029 (a rough estimate). Its evening pass failed our sign check and is shown flagged.
- **Sentinel-1:** over May 2025 to November 2026, its evening pass shows Lacul Țeica, Țeica east and Slătioarele moving away from the satellite against their surroundings, by about 9.7, 4.9 and 5.9 mm a year in our baseline fit (4, 36 and 22 pixels). Other processing choices change this: with a fitted elevation correction Slătioarele reads +0.2 mm a year, with only the western reference Lacul Țeica reads −4.0, and a stricter coherence cut keeps only Țeica east. Țeica east is the most robust result.
- **Checks:** 5 pass, 6 warn, 1 fail and 12 for information. The warnings are real limits (noise, few shared dates), not errors.

**Why it matters.** People live and build on this ground. Official surveys are rare and expensive; satellite radar covers the whole town every 6 to 12 days for free. The page turns that into something a resident can read, and is honest about its limits, so it does not give false comfort or false alarms.

**How we built it.**

- **NISAR:** official GUNW interferograms, 22 pairs. We fit a time series with a stable-ground reference and a coherence cut. The result is tied to a European GNSS velocity model (EuVeM2022) and checked by swapping in a second model (EGMS GNSS).
- **Sentinel-1:** 374 burst interferograms ordered on ASF HyP3, fitted on a 40 m grid with six processing variants.
- **Validation:** a separate validation script, owned by the team's validator, checks the phase sign, held-out GNSS stations, the scatter of the tie, data gaps, and NISAR against Sentinel-1. The validator also red-teamed the pin, and the pin was changed as a result.
- **Forecast:** Chronos-2, a pretrained time-series model used zero-shot, per 240 m cell of the town. Each Sentinel-1 cell is tested on its last 60 days against a "no change" guess; NISAR has too few dates to test yet, so its forecast is shown untested.
- **The page:** a static site with MapLibre GL JS that reads only the products written by our scripts.

**Tools.** Python (NumPy, SciPy, pandas, h5py, pyproj, rasterio, matplotlib, asf_search, hyp3_sdk), Chronos-2 with PyTorch on CPU, JavaScript with MapLibre GL JS, Playwright for testing, GitHub Actions and Vercel.

**Limits.**

- NISAR products are beta and provisional, "not intended for scientific research".
- A radar measures only along its line of sight, and Sentinel-1 here is relative to the surrounding terrain.
- A rate is the slope over the window shown.
- The forecast is indicative: it beat "no change" in 49 % of the town's cells on one pass and 78 % on the other, and 2029 is far beyond anything we could test.
- The page is not a hazard or building assessment. For official notices, follow ISU Vâlcea and the Ocnele Mari town hall; before building, commission a geotechnical study.

## Use of artificial intelligence (the form's "Use of SI" field)

- **Claude Code and Claude in Chrome (Anthropic):** each team member ran Claude Code for their own role, under shared rules (`CLAUDE.md`). It wrote and reviewed code and documentation, and people checked the results. Claude in Chrome helped look up sources in the browser.
- **ChatGPT (OpenAI):** helped summarise material before the event and with some Sentinel-1 and forecast work. Its image model (gpt-image) generated the team logo on 14 Nov 2026.
- **Figma Make:** gave a first visual design, which was replaced.
- **Chronos-2 (Amazon):** a pretrained machine-learning forecasting model, used without retraining for the prediction.

The radar measurements and checks come from our own scripts on open data. Every substantive use of AI, and what a person checked, is logged in `AI-DISCLOSURE.md`.

The team logo is AI-generated (ChatGPT's image model) and is labelled "AI-generated" wherever it appears on the page and in the repository. No other AI-generated images, video or audio are used. No AI-generated content uses NASA branding.

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
| EuVeM2022 European velocity model (Lantmäteriet) | https://www.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/lantmateriets-doi-objects/euvem2022/ |
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

Attribution: contains modified Copernicus Sentinel data 2025–2026, processed by ASF HyP3. NISAR data courtesy of NASA and ISRO, via ASF DAAC (beta and provisional products, not intended for scientific research). EGMS: Copernicus Land Monitoring Service, funded by the European Union.

The salt-field outlines (centres and radii) come from the team advisor's starter kit (Miluță Dulea-Flueraș, 12 Nov 2026). Full citations, versions and access dates: `CITATIONS.md`.

## References

- Ene, M., Osaci-Costache, G., Tîrlă, L. (2009). The caving-ins at Ocnele Mari in the Vâlcea Subcarpathians, Romania. *Geografia Fisica e Dinamica Quaternaria* 32(1), 67–72. https://gfdq.glaciologia.it/index.php/GFDQ/article/download/284/298/919
- Mesescu, A.A. (2011). The Ocnele Mari salt mine collapsing sinkhole: a NATECH breakdown in the Romanian Sub-Carpathians. *Carpathian Journal of Earth and Environmental Sciences* 6(1), 215–220. https://www.cjees.ro/actions/actionDownload.php?fileId=153
- Poenaru, V. et al. (2011). Land degradation monitoring in the Ocnele Mari salt mining area using satellite imagery. *Proc. SPIE* 8181.
- Rădutu, A., Vlad-Sandru, M.-I. (2023). Review on the use of satellite-based radar interferometry for monitoring mining subsidence in urban areas. *Mining Revue* 29(1). https://reference-global.com/article/10.2478/minrv-2023-0004
- Muntean, A. et al. (2026). *Solid Earth* 17, 747. https://se.copernicus.org/articles/17/747/2026/
- Steffen, R. et al. (2025). EuVeM2022. *Geophysical Journal International*. https://doi.org/10.1093/gji/ggaf052
- Blewitt, G., Hammond, W.C., Kreemer, C. (2018). Harnessing the GPS data explosion for interdisciplinary science. *Eos* 99.
- Hersbach, H. et al. (2020). The ERA5 global reanalysis. *QJRMS*. https://doi.org/10.1002/qj.3803
- Ansari, A.F. et al. Chronos: learning the language of time series (Amazon). https://github.com/amazon-science/chronos-forecasting
- Adevărul: Ocnele Mari five years after the brine flooded part of the town. https://adevarul.ro/stiri-locale/ramnicu-valcea/cum-arata-ocnele-mari-la-cinci-ani-de-cand-1464718.html
- The team advisor's plan and rehearsal kit (Miluță Dulea-Flueraș, 12 Nov 2026), not public.

## Team

Mario (lead and story), Alexandru and Eric (NISAR data and InSAR analysis), Matei (geodesy), Paul (validation), Darius (web app). NASA Space Apps Cluj-Napoca, 14 to 15 November 2026.
