# Citations

**Owner:** all roles append; 01 checks links and licences

These are the data, software, documents and prior work this project uses, with where each was fetched. Started Sat 14 Nov 2026 and completed during the event.

**Append a row the moment you use a source.** 01 checks every link and licence in hours 30 to 40. Third-party data are linked and credited, never copied into the repository.

## Radar products

| Product | Used for | Fetched from | Owner |
| --- | --- | --- | --- |
| NISAR L2 GUNW, beta (`NISAR_L2_GUNW_BETA_V1`) and provisional (`NISAR_L2_GUNW_PROVISIONAL_V1`), frequency A, HH | Every NISAR layer | ASF, `https://nisar.asf.earthdatacloud.nasa.gov/NISAR/<collection>/`. The 22 granules are in `data/scenes/ocnele_mari_gunw.csv` (CMR, 14 Nov 2026) | 02 |
| Sentinel-1 interferograms, ASF HyP3 `INSAR_GAMMA` | The second-radar check | [HyP3](https://hyp3-docs.asf.alaska.edu/); jobs logged in `docs/validation-log.md` | 05 |

## References and ancillary layers

| Layer | Used for | Fetched from | Owner |
| --- | --- | --- | --- |
| EuVeM2022, Romania grid (0.1°) | The tie | `https://www.lantmateriet.se/geodesi_data/EuVeM2022/country_results/EuVeM2022_Romania.txt` (from the advisor kit; re-verify); [landing page](https://www.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/lantmateriets-doi-objects/euvem2022/) | 04 |
| EGMS GNSS model | Second tie (O-06) | [EGMS](https://egms.land.copernicus.eu/); CSV link still to be found | 04 |
| NGL MIDAS velocities, Eurasia-fixed | Held-out stations | `https://geodesy.unr.edu/velocities/midas.EU.txt` (from the advisor kit; re-verify) | 04 |
| NGL daily series, tenv3, IGS20 | Station screening | `https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/<STATION>.tenv3`. Verified 14 Nov 2026 with STOL (HTTP 200); the old IGS14 path returns 404 | 05 |
| Published station rates, Muntean et al. 2026, Supplement Tables S1 and S3 | VLC2 and HORE | The paper's supplement (*Solid Earth* 17, 747–762). Do not redistribute the table (O-13) | 04 |
| EGMS Ortho L3 Up, 100 m, 2020 to 2024 | Stable-ground check; the bowl's history | [EGMS](https://egms.land.copernicus.eu/), free login; cut to `data/work/<site>/refs/egms_up.csv` | 05 |
| Copernicus GLO-30 DEM | Troposphere slope | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N45_00_E024_00_DEM/…`; [AWS Registry of Open Data](https://registry.opendata.aws/copernicus-dem/) | 02 |
| Basemap | Map context | To be decided (O-09) | 06 |

## Software

| Software | Version | Source |
| --- | --- | --- |
| Python, NumPy, SciPy, pandas, h5py, pyproj, requests, asf_search, hyp3_sdk, rasterio, matplotlib, Pillow | Recorded at hour 2 by each owner | PyPI or conda-forge |
| MintPy | If O-05 picks it | https://github.com/insarlab/MintPy |
| Leaflet | Recorded by 06 | https://leafletjs.com |

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
