# Dancing on Salt

**Owner:** 01 · Lead and story (Mario)

<img width="474" height="145" alt="Logo" src="https://github.com/user-attachments/assets/dd8b923a-0575-47a9-9471-942fd5a546a3" />

**AI-Disclosure:** https://docs.google.com/spreadsheets/d/124X3eaWHZTHrb_MgZriIy63Y4Zvm6VaW4JnVFfrDwhg/edit?usp=sharing

*Our submission to NASA Space Apps 2026, challenge [Dancing with the SARs](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/). The submission text is in [SUBMISSION.md](SUBMISSION.md).*

This is the team repo for NASA Space Apps 2026, challenge **Dancing with the SARs**, on 14 to 15 Nov 2026 in Cluj-Napoca. Six people, one site: **Ocnele Mari**, in Vâlcea county, Romania, where salt has been extracted by dissolving it with water through wells since the 1950s and 1960s, and where the ground above the brine fields has sunk and collapsed before, most visibly in September 2001 at Lacul Țeica ([docs/geography.md](docs/geography.md)).

**Live app: https://pea-dancingwiththesars.vercel.app** (deployed from `main` by Vercel).

## The project in one paragraph

We built a web page that shows anyone how the ground moves around Ocnele Mari, as seen from space by two radar satellites: **NISAR** (NASA and ISRO, L-band, 24.4 cm wavelength, its first year of data) and **Sentinel-1** (ESA and Copernicus, C-band, 5.55 cm). The page opens on the town, plays the ground through time, compares the two radars on the same months, checks them against GPS stations and the European Ground Motion Service (EGMS), and says plainly where the radar cannot yet see the motion. Every number on the page comes from `products/ocnele_mari/`, written by our scripts from open data.

## What we found

Checked 15 Nov 2026 against `products/ocnele_mari/`.

- **The ground has moved here before.** EGMS (Sentinel-1, 2020 to 2025, 100 m cells) shows Zone 3, Ocnița · Goruniș, sinking about 18.9 mm/yr (6 cells). Zones 1, 2 and 4 sink 2.5 to 3.9 mm/yr, and stable ground about 0.5 mm/yr.
- **NISAR cannot see it yet.** On stable ground a salt zone's NISAR rate varies by about ±21 mm/yr (morning pass, 129A), so the zones' rates against the ground around them (−3.9 to −12.4 mm/yr) are all inside the noise. As processed now, a 25 mm/yr sink would become visible around May 2029 (a rough estimate, `noise_floor.json`). The evening pass (094D) failed the phase-sign test and is shown only for inspection.
- **Sentinel-1 sees part of it.** Over May 2025 to November 2026, the evening pass (029A) shows Zones 1, 2 and 4 moving away from the satellite relative to their surroundings, by 9.7, 4.9 and 5.9 mm/yr (4, 36 and 22 pixels). Zone 3 has no connected series there. The morning pass (007D) keeps no zone pixel connected through both winters.
- **Checks:** 5 pass, 6 warn, 1 fail, 12 info (`checks.json`, 15 Nov). The warnings are real limits, not errors: NISAR scatters about 39 mm/yr per pixel on stable ground, and only 6 NISAR dates fall in the months both satellites cover (7 Jul to 4 Oct 2026).

So the page is an honest screen of what the two radars can and cannot see today, not a warning system.

## What the page does

What is live on https://pea-dancingwiththesars.vercel.app, checked 15 Nov 2026, about 15:40.

| Part | What it does |
| --- | --- |
| **Map** | Opens on Ocnele Mari with the town boundary, the four salt zones (1 Lacul Țeica, 2 Țeica east, 3 Ocnița · Goruniș, 4 Slătioarele), the GNSS stations HORE and VLC with their own motion, and one coloured dot per measured spot. The background is a light map or satellite imagery, with adjustable overlay opacity. A click on a dot shows its value |
| **Satellite menu** | NISAR, Sentinel-1, or Compare (side by side, same months only: 7 Jul to 4 Oct 2026), each with its pass times over Romania |
| **Views** | Motion (change since the first date, or the yearly rate), Coverage (when each satellite looked and how many usable pixels each zone has), Compare (the two radars side by side, paired by viewing geometry) |
| **Morning and evening passes** | NISAR 129A (morning, from the east) and 094D (evening, from the west, flagged); Sentinel-1 007D (morning) and 029A (evening) |
| **Timeline** | Every acquisition, gaps marked; Play steps through the dates. Sentinel-1 fills NISAR's January to June 2026 gap |
| **Side buttons** | Zoom. The pin: drop it on a spot to see that spot's history and how it moves against the ground 300 m around; it says "below the noise" unless the difference is larger than the measured noise floor. The compass: the map rotates, and the compass resets north. The house picker: press a building outline. The area tool: drag a rectangle, or press once for a 1 km square |
| **Side menu** | Opens when you press a zone, a building or an area. It shows the trend over time, the prediction (Chronos-2 to 1 Jan 2029, with the result of its 60-day test), "Which way the ground moves" (an experimental up-down and east-west estimate) and "In plain words", a short summary written from the area's own numbers |
| **Arrows and Buildings** | An arrow field inside the selection, and building outlines from zoom 14 |
| **Satellites now** | A globe with estimated satellite positions and the next passes over Ocnele Mari |
| **Terms & Conditions** | What the page is and is not, how to read red and blue, pass times, official sources, credits, and the validation checks |
| **Header and zone row** | Reset to site, the main check for the current view, the zone buttons, Copy view link, and a one-line note on what the dots mean |

Red means the ground moved away from the satellite (usually sinking), blue toward it.

**Words used here.** *Line of sight:* a radar measures motion only along the line from the ground to the satellite, not straight up and down. *Interferogram:* the difference between two radar images of the same place, which shows how far the ground moved between the two dates. *Morning and evening pass:* each satellite sees the town from the east in the morning and from the west in the evening; the codes (129A, 094D, 029A, 007D) are the orbit tracks. *Phase-sign test:* a check that the salt zones come out sinking, as they should; a track that fails it is not trusted. *Noise floor:* how much the numbers vary on ground that does not move; anything smaller cannot be told apart from no motion.

## Data

Every source below was checked on 15 Nov 2026 (`logs/06-app.md`, the data audit).

| Data | What we use | Where it comes from |
| --- | --- | --- |
| NISAR L2 GUNW interferograms (beta and provisional) | 22 pairs: 129A, 13 pairs over 15 dates, 7 Nov 2025 to 21 Oct 2026, with no pair from 18 Jan to 23 Jun 2026; 094D, 9 pairs over 10 dates, 20 Jun to 18 Oct 2026 | NASA CMR and ASF DAAC (`data/scenes/ocnele_mari_gunw.csv`); all 22 found in NASA's catalog |
| Sentinel-1 burst interferograms | 374 jobs: 029A, 94 dates, 6 May 2025 to 10 Nov 2026; 007D, 96 dates, 5 May 2025 to 15 Nov 2026 | ASF HyP3 (`sentinel1/provenance/`, with a checksum for every product); every acquisition on the two bursts since May 2025 |
| GNSS velocities | HORE (2012 to 2020) and VLC1 (2012 to 2018) from NGL MIDAS; VLC2 (2019 to 2025) from Muntean et al. 2026 | HORE and VLC1 match NGL's public file to 0.01 mm/yr |
| GNSS velocity model | EuVeM2022, to tie NISAR to a Eurasia-fixed frame; EGMS's model as the swap test | `refs.py` (04) |
| EGMS Ortho, 2020 to 2025 | The zones' history and the stable-ground check | Copernicus Land Monitoring Service; cut by `egms_cut.py` (05) |
| Chronos-2 (`amazon/chronos-2`) | The prediction, used zero-shot | Hugging Face, Apache 2.0 |
| Maps | OpenFreeMap (OpenStreetMap data), Esri World Imagery, OpenStreetMap buildings and the town boundary | Credited on the map and in Terms |

Full list with links and licences: [CITATIONS.md](CITATIONS.md).

## How it works

One script per step, run as `python <step>.py ocnele_mari`. Settings, zones and stations come from `common.py`.

| Step | Script (owner) | What it does |
| --- | --- | --- |
| NISAR search and download | `fetch.py` (02) | Streams the town window from each NISAR interferogram, decodes the mask, subtracts the ionosphere screen |
| NISAR time series | `stack.py` (03) | Coherence 0.35 or more, removes elevation slope and a stable-ground reference per pair, small-baseline inversion with one group per side of the January to June gap |
| GNSS references | `refs.py` (04) | EuVeM2022, NGL MIDAS and the published station rates |
| Tie | `calibrate.py` (04) | Ties each NISAR track to EuVeM2022 on stable ground (offset −9.09 mm/yr on 129A, −15.15 on 094D) |
| Up and east | `split.py` (03) | Experimental combination of the two NISAR passes |
| Noise floor | `noise_floor.py` (04) | 1,000 fake zones and pins on stable ground: how big a motion NISAR can show |
| Validation | `validate.py` (05) | Phase sign, held-out stations, tie scatter, model swap, gaps, NISAR against Sentinel-1. Nobody else edits it |
| Sentinel-1 | `sentinel1/scripts/` (03) | Order and download HyP3 jobs, fit each window on a 40 m grid (`fit.py`), weather-model troposphere, forecasts |
| Prediction | `sentinel1/scripts/forecast_area.py`, `forecast_zones.py` (03) | Chronos-2 per 240 m cell of the town and per zone, each tested on its last 60 days |
| Page products | `export.py` (06) | Writes `products/ocnele_mari/`: map layers, dots, frames, zone series, coverage, manifest |
| The page | `index.html`, `app/` (06) | MapLibre GL JS; reads only `products/<site>/` |
| Checks | `checkpoint.py` (01), `tests/` | File contracts and the smoke test |

Still stubs: the synthetic known-answer site (`demo`), the EGMS stable-ground check inside `validate.py`, and `hyp3_order.py` (Sentinel-1 jobs were ordered with `sentinel1/scripts/order_all.py` instead).

## What the page cannot tell you

- **NISAR is beta and provisional,** "not intended for scientific research" (NASA and ISRO). Read zones and areas, not single dots.
- **Line of sight only.** The up and east card combines both NISAR passes, and the evening one failed its sign test: treat it as unconfirmed.
- **Sentinel-1 is relative** to the terrain 3 to 6.5 km around the zones, not tied to GNSS.
- **A rate is the slope over the window shown,** not a long-term velocity. A few summer months can read several times faster than the 2020 to 2025 history.
- **The prediction is indicative.** On its last 60 days Chronos-2 beat a "no change" guess in 49 % of the town's 029A cells and 78 % of the 007D cells; 2029 is much further ahead than anything tested, and NISAR has too few dates to test at all.
- **It is not a hazard or building assessment.** For official notices: the emergency inspectorate (ISU Vâlcea, part of IGSU) and the Ocnele Mari town hall. Before building, a geotechnical study.

## Run it yourself

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                                   # must pass before every push
python export.py ocnele_mari                # rebuilds products/ocnele_mari/ (about 2 minutes)
python checkpoint.py ocnele_mari            # checks the products against the file contracts
python -m http.server 8000                  # then open http://localhost:8000
```

- **Sentinel-1** rebuilds exactly from what is committed (checked 15 Nov 2026: all 192 images pixel for pixel, all numbers).
- **NISAR** needs a free [Earthdata](https://urs.earthdata.nasa.gov) token in `.env` (see `.env.example`) and the intermediate stacks in `data/work/`, which are not in git. That file and folder never go in the repo.
- **The prediction** needs `chronos-forecasting` 2 or later and PyTorch on CPU; a run takes about 15 seconds.
- **Hosting:** [docs/deploy.md](docs/deploy.md).

## Team

| # | Role | Who | Owns |
| --- | --- | --- | --- |
| 01 | Lead and story | Mario | Scope, story, the 7-slide deck, the submission; `checkpoint.py` |
| 02 | NISAR data | Alexandru and Eric | Search, streamed windows, masks, ionosphere; `fetch.py`, `update.py` |
| 03 | InSAR analyst | Alexandru and Eric | Time series, rates, up and east, Sentinel-1 fits and forecasts; `stack.py`, `split.py`, `sentinel1/` |
| 04 | Geodesist | Matei | References, frame, tie, model swap, noise floor; `refs.py`, `calibrate.py`, `noise_floor.py` |
| 05 | Validator | Paul | Stations, EGMS, checks, red team; `validate.py`, `egms_cut.py`, `hyp3_order.py` |
| 06 | App developer | Darius | The page, products and hosting; `index.html`, `app/`, `export.py`, `mock_products.py` |

Every file says its owner in its first lines; the full list is [OWNERS.md](OWNERS.md).

## Decisions the whole team made

- **One site:** Ocnele Mari only (decision D-001).
- **The map opens on the town,** with Romania blurred when you zoom out (D-002).
- **The submission is a 7-slide PowerPoint,** with no video (D-003).
- **Two radars, one switch:** NISAR and Sentinel-1 are both fitted, and the page switches between them, comparing them only on the same months, each in its own line of sight (D-004).

Smaller choices are logged with their reasons in [DECISIONS.md](DECISIONS.md).

## Repository layout

```
README.md  SUBMISSION.md  STATUS.md  OWNERS.md  CLAUDE.md   overview, submission text, status, owners, rules
DECISIONS.md  CITATIONS.md  AI-DISCLOSURE.md                logs everyone appends to
common.py                                                   site, zones, stations, thresholds, helpers
fetch.py stack.py refs.py calibrate.py split.py             the NISAR pipeline
noise_floor.py validate.py egms_cut.py update.py            noise, checks, EGMS, new-data check
export.py mock_products.py checkpoint.py run_all.py         products, mock site, contract check, runner
index.html  app/                                            the page (MapLibre GL JS)
products/<site>/                                            what the page reads, written by scripts only
sentinel1/                                                  Sentinel-1 provenance, fits, grids and scripts
data/scenes/                                                the 22 NISAR pairs (data/work/ stays local)
docs/  logs/  notebooks/  prompts/  tests/  .github/        documents, role logs, exploration, prompts, tests, CI
vercel.json  .vercelignore                                  hosting
```

## Documents

- [STATUS.md](STATUS.md): where each role is.
- [docs/overview.md](docs/overview.md) and [docs/synopsis.md](docs/synopsis.md): why it matters, the claims and how each could fail.
- [docs/ui.md](docs/ui.md): the page's design and the honest comparison rules.
- [docs/data.md](docs/data.md), [docs/rehearsal.md](docs/rehearsal.md), [docs/validation-log.md](docs/validation-log.md), [docs/forecast.md](docs/forecast.md): data, traps, validation and the prediction.
- [SUBMISSION.md](SUBMISSION.md): the Space Apps submission text, with every NASA and partner source.
- [docs/handoff-15nov-session.md](docs/handoff-15nov-session.md): a compact summary of the 15 Nov session.
- `logs/`: each role's running log. [products/README.md](products/README.md): every product file and who writes it.
- [CLAUDE.md](CLAUDE.md) and `prompts/`: the rules and prompts for Claude Code. [INFO.md](INFO.md): site notes in Romanian.

## How we used AI

Each of the six of us ran Claude Code (Anthropic) for our own role, under shared rules in [CLAUDE.md](CLAUDE.md). ChatGPT (OpenAI) helped summarise the advisor's material before the event and with some Sentinel-1 and forecast work; Figma Make gave a first visual design that was replaced. The prediction comes from Chronos-2, a pretrained forecasting model, used without retraining. The radar measurements and checks come from our scripts on open data. The validator (05) owns the checks and edits no science code; the current check results were run by the 02/03 session and are marked as a draft until 05 reviews them. Every substantive use, and what a person checked, is logged in [AI-DISCLOSURE.md](AI-DISCLOSURE.md).

## Next steps

- **More NISAR passes.** Each new pass, every 12 days, narrows the noise. At the current rate a 25 mm-a-year sink becomes visible to NISAR around 2029 (`noise_floor.json`).
- **The evening NISAR pass (094D)** failed the phase-sign test; the "Which way the ground moves" card still uses it, so read that card as unconfirmed.
- **Reproducibility.** The NISAR stacks in `data/work/` are not in git, so only Sentinel-1 can be rebuilt from the repository alone.
- **Hosting.** Vercel's Hobby plan blocks commits by anyone but the account owner. `.github/workflows/vercel-deploy-hook.yml` deploys every push to `main` once the `VERCEL_DEPLOY_HOOK` secret is set ([docs/handoff-15nov-session.md](docs/handoff-15nov-session.md)).

## License

[MIT](LICENSE). Space Apps distributes submission content under Apache 2.0, so 01 checks the 2026 guide. Third-party data are linked and credited, not redistributed: contains modified Copernicus Sentinel data 2025 to 2026, processed by ASF HyP3; NISAR data courtesy of NASA and ISRO, via ASF DAAC.
