# Data sources and credits

All sources are open. **Link and credit them; don't copy them into the repository.** For each source the table gives the owner, how to get it, what it is used for and the credit line. "Verified" means somebody checked that the link answers, with the date.

| Source | Owner | Access | Used for | Credit line |
|---|---|---|---|---|
| **NISAR L2 GUNW**: CMR `NISAR_L2_GUNW_BETA_V1`, `NISAR_L2_GUNW_PROVISIONAL_V1` (and `NISAR_L2_GUNW_V1` once filled) | 02 | [ASF](https://search.asf.alaska.edu) · `asf_search` / `earthaccess`; Earthdata login + token. Verified via CMR 2026-11-14: 22 pairs over the town | The measurement | NISAR data: NASA–ISRO, ASF DAAC. Beta/provisional products, not intended for scientific research |
| NISAR docs: product specs, [open-source tools](https://nisar-docs.asf.alaska.edu/using-open-source/) | 02/03 | public | Layer names, mask bits, MintPy `prep_nisar` | — |
| **EuVeM2022**, the European GNSS velocity model (Romania grid, 0.1°) | 04 | [Lantmäteriet](https://www.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/lantmateriets-doi-objects/euvem2022/) · `https://www.lantmateriet.se/geodesi_data/EuVeM2022/country_results/EuVeM2022_Romania.txt` (from the kit; re-verify) | The tie | Steffen et al., Lantmäteriet, CC BY 4.0, doi:10.23701/euvem2022; Steffen et al. 2025, GJI, doi:10.1093/gji/ggaf052 |
| **EGMS GNSS model** (50 km grid, about 3,770 stations) | 04 | [EGMS](https://egms.land.copernicus.eu/) (CSV link still to be found, O-06) | Second tie (model swap) | Copernicus Land Monitoring Service, EGMS, funded by the EU |
| **NGL MIDAS velocities**, Eurasia-fixed | 04 | `https://geodesy.unr.edu/velocities/midas.EU.txt` (from the kit; re-verify) | Held-out station rates | Blewitt, Hammond & Kreemer 2018, Eos 99 (NGL) |
| **NGL daily series** (tenv3, IGS20) | 05 | `https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/<STATION>.tenv3`. Verified 2026-11-14 (STOL: 200; the old IGS14 path is 404) | Station plots, screening | NGL, University of Nevada, Reno |
| **Published station rates** | 04 | Muntean et al. 2026, *Solid Earth* 17, 747–762, supplement Tables S1/S3 | Rates at VLC2, HORE | Cite the paper; **don't redistribute the table** (O-13) |
| **EGMS Ortho L3 Up** (100 m; 2020–2024 tile, 2019–2023 also exists) | 05 | [EGMS](https://egms.land.copernicus.eu/), free login; cut to the window as `data/work/<site>/refs/egms_up.csv` | Stable-ground cross-check; the bowl's history | Copernicus Land Monitoring Service, EGMS, funded by the EU |
| **Sentinel-1** interferograms via **HyP3** | 05 | [HyP3](https://hyp3-docs.asf.alaska.edu/) · `hyp3_sdk`, INSAR_GAMMA jobs, Earthdata login, monthly credits | Second radar, same months | Contains modified Copernicus Sentinel data 2025–2026, processed by ASF HyP3 |
| **Copernicus GLO-30 DEM** | 02 | AWS open data `copernicus-dem-30m` (COG tiles) | Troposphere (elevation slope) | Copernicus DEM © DLR / Airbus, provided under COPERNICUS by the EU and ESA |
| **Basemap** | 06 | TBD (O-09); OSM tiles are fine for a demo | Map context | © OpenStreetMap contributors (if used) |
| **Space Apps challenge resources** | 01 | [Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources). It was unreachable from the setup machine on 14 Nov, so **01 lists what we use from it here.** | Brief, extra datasets | As the page requires |

**Not used, by design:** ROMPOS raw data or daily solutions, which are closed. Nothing derived from them enters the repository.

## Credits block for the page and the submission

> NISAR L2 GUNW (NASA–ISRO, ASF DAAC; beta/provisional) · EuVeM2022 (Lantmäteriet, CC BY 4.0) · NGL MIDAS (Blewitt et al. 2018) · Muntean et al. 2026, Solid Earth · EGMS (Copernicus Land Monitoring Service, funded by the EU) · Copernicus Sentinel-1 via ASF HyP3 · Copernicus DEM GLO-30.
