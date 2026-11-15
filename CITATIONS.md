# Citations

**Owner:** all roles append; 01 checks links and licences

These are the data, software, documents and prior work this project uses, with where each was fetched. Started Sat 14 Nov 2026 and completed during the event.

**Append a row the moment you use a source.** 01 checks every link and licence in hours 30 to 40. Third-party data are linked and credited, never copied into the repository.

## Radar products

| Product | Used for | Fetched from | Owner |
| --- | --- | --- | --- |
| NISAR L2 GUNW, beta (`NISAR_L2_GUNW_BETA_V1`) and provisional (`NISAR_L2_GUNW_PROVISIONAL_V1`), frequency A, HH | Every NISAR layer | ASF, `https://nisar.asf.earthdatacloud.nasa.gov/NISAR/<collection>/`. The 22 granules are in `data/scenes/ocnele_mari_gunw.csv` (CMR, 14 Nov 2026) | 02 |
| Sentinel-1C/D VV burst interferograms, ASF HyP3 `INSAR_ISCE_BURST` (10x2 looks), 58 pairs on tracks 029A and 007D, 6 Jul to 5 Oct 2026 | The second radar (D-004): its own view in the app, and check 8 | [HyP3](https://hyp3-docs.asf.alaska.edu/); jobs, product names and checksums in `sentinel1/provenance/`; earlier note: jobs logged in `docs/validation-log.md` | 05 |

## References and ancillary layers

| Layer | Used for | Fetched from | Owner |
| --- | --- | --- | --- |
| EuVeM2022, Romania grid (0.1°) | The tie | `https://www.lantmateriet.se/geodesi_data/EuVeM2022/country_results/EuVeM2022_Romania.txt` (from the advisor kit; re-verify); [landing page](https://www.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/lantmateriets-doi-objects/euvem2022/) | 04 |
| EGMS GNSS model A-EPND 2023 (`EGMS_AEPND_V2023.0.csv`, 50 km grid, 3,773 nodes, ETRF2000) | Second tie (O-06), T8 | `https://land.copernicus.eu/en/technical-library/gnss-calibration-data-2023-csv/@@download/file`, no login; found by 05 (Paul), downloaded and checked by 04 on 14 Nov 2026. Columns are Latitude, Longitude, **N, E**, Up, SigmaN, SigmaE, SigmaUP (mm/yr); `refs.py` swaps them | 04 |
| EGMS GNSS Calibration Report, v5.2 (28 Sep 2026) | The EGMS model's frame: A-EPND 2023 is in ETRF2000; ETRF2000 − ETRF2020 Up is −0.88 to +0.01 mm/yr across Europe (section 1.2, section 3.3, Figure 10) | `https://land.copernicus.eu/en/technical-library/gnss-calibration-report/@@download/file`, read 14 Nov 2026 | 04 |
| NGL MIDAS velocities, Eurasia-fixed | Held-out stations | `https://geodesy.unr.edu/velocities/midas.EU.txt` (from the advisor kit; re-verify) | 04 |
| NGL daily series, tenv3, IGS20 | Station screening | `https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/<STATION>.tenv3`. Verified 14 Nov 2026 with STOL (HTTP 200); the old IGS14 path returns 404 | 05 |
| Published station rates, Muntean et al. 2026, Supplement Tables S1 and S3 | VLC2 and HORE | [The paper's supplement](https://se.copernicus.org/articles/17/747/2026/se-17-747-2026-supplement.pdf) (*Solid Earth* 17, 747–762; [article](https://se.copernicus.org/articles/17/747/2026/)), read 14 Nov 2026: Table S3 has VLC2 and no HORE. Do not redistribute the table (O-13) | 04 |
| EGMS Ortho L3 Up and East–West, 100 m, release 2020 to 2025 (tile E54N25, produced 28 Jul 2026) | Stable-ground check; the bowl's history | [EGMS](https://egms.land.copernicus.eu/), free login; downloaded 14 Nov 2026, cut by `egms_cut.py` to `data/work/<site>/refs/egms_up.csv`. Credit: Copernicus Land Monitoring Service, European Ground Motion Service | 05 |
| NGL station list (`llh.out`) | Finding open stations near the town | `https://geodesy.unr.edu/NGLStationPages/llh.out`, read 14 Nov 2026 | 05 |
| ASF Search API, Sentinel-1 SLC and NISAR catalogues | The 2026 third-witness search | `https://api.daac.asf.alaska.edu/services/search/param`, point 45.08846 N 24.29666 E, from 2026-01-01, queried 14 Nov 2026 | 05 |
| NISAR L3 SME2 soil moisture, beta and provisional (`NISAR_L3_SME2_BETA_V1`, `NISAR_L3_SME2_PROVISIONAL_V1`), 200 m | Red-team screen: does the Sentinel-1 signal follow soil moisture | ASF, `https://nisar.asf.earthdatacloud.nasa.gov/NISAR/<collection>/`, Earthdata login; 25 granules over the town found with the ASF Search API, 14 Nov 2026. NISAR products are beta/provisional, not intended for scientific research | 05 |
| ERA5 daily precipitation via the Open-Meteo historical weather API | Red-team screen and the predeclared rain forecast test | `https://archive-api.open-meteo.com/v1/archive`, 45.088 N 24.290 E, 1 May to 31 Oct 2026, read 14 Nov 2026. Hersbach et al. 2020, *QJRMS*, doi:10.1002/qj.3803; Open-Meteo, CC BY 4.0 | 05 |
| OPERA L4 TROPO-ZENITH v1 (NASA JPL, ECMWF HRES through RAiDER), zenith wet and hydrostatic delay | Independent weather-model troposphere check of the Sentinel-1 stack | ASF, `https://cumulus.asf.earthdatacloud.nasa.gov/OPERA/OPERA_L4_TROPO-ZENITH_V1/`, Earthdata login with the OPERA data licence accepted; 64 maps around the July to October 2026 acquisitions, read 14 Nov 2026. [Product page](https://www.jpl.nasa.gov/go/opera/products/tropo-product/) | 05 |
| Copernicus GLO-30 DEM | Troposphere slope | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N45_00_E024_00_DEM/…`; [AWS Registry of Open Data](https://registry.opendata.aws/copernicus-dem/) | 02 |
| ERA5 daily precipitation via the Open-Meteo archive API (7- and 30-day sums at 45.088 N, 24.290 E) | 05's rainfall screen; the forecast covariate test (`forecast.py --rain-csv`) | https://open-meteo.com/en/docs/historical-weather-api (05, PR #9) | 05 |
| NISAR L3 SME2 soil moisture, provisional and beta, 200 m | 05's moisture screen | ASF, `NISAR_L3_SME2_PROVISIONAL_V1` (05, PR #9) | 05 |
| EGMS Ortho L3 2020 to 2025, Zone 4 cell medians (Up −3.1, East +4.9 mm/yr, 10 cells) | The forecast's long-term trend model | [EGMS 2020–2025 release](https://land.copernicus.eu/en/news/product-update-european-ground-motion-service-2025); 05's cut (PR #9) | 05, 03 |
| ECMWF IFS 0.25° pressure-level temperature, humidity and geopotential, hourly, via the Open-Meteo historical-forecast API | The weather-model troposphere scenario (`sentinel1/scripts/tropo.py`) | https://open-meteo.com/en/docs/historical-forecast-api (`models=ecmwf_ifs025`); delays stored in `sentinel1/analysis/tropo.json` | 03 |
| ERA5 daily precipitation and ERA5-Land hourly 0 to 7 cm soil moisture via the Open-Meteo archive API | Chronos-2 weather-covariate backtest (`sentinel1/scripts/chronos_weather.py`) | https://open-meteo.com/en/docs/historical-weather-api; results in `sentinel1/analysis/chronos_weather.json` | 03 |
| Basemap, light (default): OpenFreeMap "positron" style, OpenMapTiles schema, OpenStreetMap data | The page's default map background | `https://tiles.openfreemap.org/styles/positron` ([openfreemap.org](https://openfreemap.org)); free, no API key; credited on the map and in About. Checked 14 Nov 2026 | 06 |
| Basemap, satellite: Sentinel-2 cloudless 2020 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2020) | The page's optional "Satellite" background | `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/…` ([s2maps.eu](https://s2maps.eu)); credited on the map and in About. The 2018 and later layers are licensed CC BY-NC-SA 4.0, as we understand it: 06 confirms on s2maps.eu before submitting | 06 |
| Ocnele Mari town boundary: OpenStreetMap relation 9845422 (admin_level 8, the town with its villages) | The black outline on the map | Nominatim, `https://nominatim.openstreetmap.org/details?osmtype=R&osmid=9845422&polygon_geojson=1`, fetched 14 Nov 2026, saved as `app/ocnele_mari_boundary.geojson`; © OpenStreetMap contributors, ODbL 1.0, credited on the map | 06 |

## Software

| Software | Version | Source |
| --- | --- | --- |
| Python, NumPy, SciPy, pandas, h5py, pyproj, requests, asf_search, hyp3_sdk, rasterio, matplotlib, Pillow | Recorded at hour 2 by each owner | PyPI or conda-forge |
| Chronos-2 (`amazon/chronos-2`), chronos-forecasting, PyTorch CPU | 2.3.2, torch 2.15 CPU | https://huggingface.co/amazon/chronos-2 (Apache-2.0); used zero-shot by `sentinel1/scripts/forecast_chronos.py` |
| MintPy | If O-05 picks it | https://github.com/insarlab/MintPy |
| MapLibre GL JS | 6.15.0 (loaded from unpkg) | https://maplibre.org |
| Fonts: Instrument Serif and Inter (SIL Open Font License) | Loaded from Google Fonts | https://fonts.google.com |

## Documents

| Document | Link |
| --- | --- |
| NISAR documentation at ASF, including open-source tools | https://nisar-docs.asf.alaska.edu/ |
| NISAR GUNW product specification (mask bitfield, spec 1.4) | Linked from the ASF NISAR docs; 02 records the exact version |
| EuVeM2022 README and paper | doi:10.23701/euvem2022; Steffen et al. 2025, *GJI*, doi:10.1093/gji/ggaf052 |
| NGL MIDAS | Blewitt, Hammond and Kreemer 2018, *Eos* 99 |
| NASA Space Apps Cluj-Napoca 2026, participant's guide | https://app.notion.com/p/Participant-s-Guide-NASA-Space-Apps-Challenge-Cluj-Napoca-2026-40903dd4dbcc80eab387c2962430efef (Notion; 01 reads it at hour 0) |
| Cluj-Napoca event at ClujHUB, 14 to 15 Nov 2026 | https://www.romania-insider.com/nasa-space-apps-challenge-registrations-romania-2026 |
| Space Apps challenge and resources | https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources (unreachable from the setup machine on 14 Nov; 01 adds what we use) |

## Prior work and advisor help

The submission must list these plainly. Append a row in the same PR in which you reuse something.

| What | By | Contents | How we use it |
| --- | --- | --- | --- |
| *Dancing on Salt* team plan, 19 slides, 12 Nov 2026 | Miluță Dulea-Flueraș, team advisor | Brief, adversarial review, sites, references, pipeline, roles, hour plan, cut lines, judging | The basis of the plan. Our copy still says −250 mm/yr, which deck v10 corrects to about −25 mm/yr |
| *dancing-on-salt* rehearsal kit, 12 Nov 2026 | The advisor | A working pipeline (`fetch`, `refs`, `stack`, `calibrate`, `split`, `validate`, `export`, `checkpoint`), a static page, synthetic and real Ocnele Mari products, glossary, open items, role sheets | We follow its architecture, script names, ownership and products contract, and we quote its findings in `docs/rehearsal.md`. **No kit code is in this repository**; adopting it is O-03. Not committed (207 MB with data) |
| *dmanpark/dancing-with-the-sars* | Another Space Apps 2026 team (public repo) | Repository and document style: status and decision logs, build spec, Claude Code prompts | We copied its document structure and conventions, but none of its content or code |
| Salt-events study (EGMS extracts, `egms_extract.py`, `hyp3_plan.py`) | Earlier study | EGMS points for Ocnele Mari; a HyP3 ordering pattern | Not used yet |
| HAR1 station study; 2024 to 2026 Sentinel-1 short-pair study; LSTM vs seasonal-model study; Hârșova 2025 | Earlier studies | Lessons | Quoted as lessons only |

The advisor points us to open references, checks our frame choices, red-teams at hours 12, 24 and 40, and answers geodesy questions. The advisor does not write our code or run our processing.

## Credits block for the page and the submission

> NISAR L2 GUNW (NASA–ISRO, ASF DAAC; beta and provisional products, not intended for scientific research) · EuVeM2022 (Lantmäteriet, CC BY 4.0) · NGL MIDAS (Blewitt et al. 2018) · Muntean et al. 2026, *Solid Earth* · EGMS (Copernicus Land Monitoring Service, funded by the European Union) · Copernicus Sentinel-1 data, processed by ASF HyP3 · Copernicus DEM GLO-30 (© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA).
| OpenStreetMap, Primăria Ocnele Mari (node 5947938076) | https://www.openstreetmap.org/node/5947938076 | Town hall marker position on the map; ODbL 1.0 | 06 |
| OpenStreetMap building outlines via OpenFreeMap vector tiles (tiles.openfreemap.org, OpenMapTiles schema, 'building' layer) | https://openfreemap.org, https://www.openstreetmap.org/copyright | Experimental building outlines on the map; ODbL 1.0 | 06 |
