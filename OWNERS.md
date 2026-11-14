# Owners

**Owner:** 01 · Lead and story (Mario); every role adds its new files

Every file in this repository has an owner role, 01 to 06, or is shared. The owner does the work in it, and others propose changes to them. Each file also says its owner in its first lines (`# Owner:` in code and config, `**Owner:**` under the title in Markdown), except the licence, the team's site notes and CSV data. `pytest -q` fails if a tracked file is missing from this list or its owner line disagrees.

**When you create a file:** add a row here and an owner line at the top of the file, in the same PR.

## 01 · Lead and story (Mario)

| File | Owner | What to do with it |
| --- | --- | --- |
| `README.md` | 01 · Lead and story (Mario) | Keep the status line, team table and layout current |
| `STATUS.md` | 01 · Lead and story (Mario); every role updates its own row | Hour 0, deadline, gates, what waits on whom; each role writes its row and early-test results |
| `OWNERS.md` | 01 · Lead and story (Mario); every role adds its new files | This list. Add a row here, and an owner line in the file, whenever you create a file |
| `CLAUDE.md` | 01 · Lead and story (Mario); changes agreed by the team | The rules every Claude Code session follows |
| `checkpoint.py` | 01 · Lead and story (Mario) | Run at hours 2, 12, 24 and 40; read every WARN and FAIL aloud; keep it in line with the file contracts |
| `docs/synopsis.md` | 01 · Lead and story (Mario) | The one-page version for the team |
| `docs/overview.md` | 01 · Lead and story (Mario) | Why, the page, the claims, the 7 slides and their owners, scope, risks |
| `docs/schedule.md` | 01 · Lead and story (Mario); each role checks its own column | Who does what, hour by hour; approved at the hour-2 review |
| `docs/build-spec.md` | 01 · Lead and story (Mario); each role checks its own section | Decisions, file contracts, each role's steps; 01 keeps the open decisions and the change log |
| `docs/rehearsal.md` | 01 · Lead and story (Mario) | What the advisor's rehearsal found; read-only after hour 2 |
| `prompts/setup.md` | 01 · Lead and story (Mario) | The laptop setup prompt every member runs once |
| `prompts/early-tests.md` | 01 · Lead and story (Mario); each test names its owner | Tests T0 to T10; owners write results in STATUS.md |
| `prompts/build.md` | 01 · Lead and story (Mario) | The prompt each role's Claude Code session runs |
| `ocnele-mari-geography.md` | 01 · Lead and story (Mario) | Site geography research (14 Nov 2026), for slide 2 and the story stops |
| `LICENSE` | 01 · Lead and story (Mario) | MIT; check against the 2026 guide (O-17). No owner line inside the licence text |

## 02 · NISAR data (Alexandru, Eric)

| File | Owner | What to do with it |
| --- | --- | --- |
| `fetch.py` | 02 · NISAR data (Alexandru, Eric) | Search ASF, stream the site window from each GUNW, mask, ionosphere, DEM, synthetic stack |
| `data/scenes/ocnele_mari_gunw.csv` | 02 · NISAR data (Alexandru, Eric) | The 22 pairs from CMR; check it in T2. No owner line (it is a CSV) |
| `data/README.md` | 02 · NISAR data (Alexandru, Eric) | The layout of the local data folders |
| `docs/data.md` | 02 · NISAR data (Alexandru, Eric); the references table with 04 and 05 | Data notes and traps; 04 and 05 keep the references table |

## 03 · InSAR analyst (Alexandru, Eric)

| File | Owner | What to do with it |
| --- | --- | --- |
| `stack.py` | 03 · InSAR analyst (Alexandru, Eric) | Pairs to displacement per date to rate with σ; closure |
| `split.py` | 03 · InSAR analyst (Alexandru, Eric) | Ascending + descending to up and east on the common window |

## 04 · Geodesist (Matei)

| File | Owner | What to do with it |
| --- | --- | --- |
| `refs.py` | 04 · Geodesist (Matei) | EuVeM2022, NGL MIDAS, published rates; synthetic stand-ins |
| `calibrate.py` | 04 · Geodesist (Matei) | The tie to the GNSS frame; calib.json; the model swap |
| `logs/04-geodesist.md` | 04 · Geodesist (Matei) | Running log of role 04: checks, real and synthetic results, what is open |

## 05 · Validator (Paul)

| File | Owner | What to do with it |
| --- | --- | --- |
| `validate.py` | 05 · Validator (Paul) | Checks 1 to 8, stations.geojson, checks.json; nobody else edits it |
| `hyp3_order.py` | 05 · Validator (Paul) | Order and fetch Sentinel-1 on HyP3 (hour 0 to 1) |
| `docs/validation-log.md` | 05 · Validator (Paul) | HyP3 orders, station screening, red-team notes, frozen-build rerun |

## 06 · App developer (Darius)

| File | Owner | What to do with it |
| --- | --- | --- |
| `export.py` | 06 · App developer (Darius) | Write products/<site>/ for the page |
| `mock_products.py` | 06 · App developer (Darius) | Invented products/mock/ to build the page on; keep it in line with the file contracts |
| `products/README.md` | 06 · App developer (Darius) | What the page reads |
| `docs/ui.md` | 06 · App developer (Darius) | The page's design: satellite switch, views, comparison rules (D-004) |
| `logs/06-app.md` | 06 · App developer (Darius) | Running log of role 06: what the page does, evidence, proposals for other owners |

## Shared (announce changes; 01 reviews)

| File | Owner | What to do with it |
| --- | --- | --- |
| `common.py` | shared · announce changes; 01 reviews | Shared settings: site, zones, stations, thresholds; every change is announced |
| `run_all.py` | shared · announce changes; 01 reviews | Runs the steps in order |
| `tests/test_skeleton.py` | shared · announce changes; 01 reviews | Smoke test; must pass before every push |
| `tests/test_owners.py` | shared · announce changes; 01 reviews | Checks that every file is in this list and carries the same owner line |
| `tests/test_sentinel1_fit.py` | shared · announce changes; 01 reviews | Checks the Sentinel-1 solver and rate estimators, gaps included |
| `requirements.txt` | shared · announce changes; 01 reviews | Python packages; each owner adds what their script needs |
| `.gitignore` | shared · announce changes; 01 reviews | Keeps data and secrets out of git |
| `.gitattributes` | shared · announce changes; 01 reviews | Preserves exact bytes for checksum-tracked files |
| `.env.example` | shared · announce changes; 01 reviews | Template for the Earthdata token; the real .env is never committed |
| `.github/workflows/tests.yml` | shared · announce changes; 01 reviews | Runs pytest on every push |
| `.github/pull_request_template.md` | shared · announce changes; 01 reviews | The checklist on every PR |

## Everyone

| File | Owner | What to do with it |
| --- | --- | --- |
| `DECISIONS.md` | all roles append; 01 reviews at checkpoints | One line per decision taken without the whole team |
| `CITATIONS.md` | all roles append; 01 checks links and licences | A row for every source and every piece of prior work |
| `AI-DISCLOSURE.md` | all roles append to the log; 01 finalises section 1 | The AI disclosure for the submission and the running log |
| `INFO.md` | all roles · the team's site notes, in Romanian | Leave as is. No owner line (it is the team's own note) |
| `products/` | 04, 05, 06 · written by their scripts only, never by hand | calibrate.py (04), validate.py (05), export.py and mock_products.py (06) |

## Not created yet

Whoever creates these adds the owner line from this table.

| File | Owner | What it is |
| --- | --- | --- |
| `slides/` | 01 · Lead and story (Mario); each slide's owner supplies its content | The 7-slide PowerPoint (D-003): slides/dancing-on-salt.pptx |
| `SUBMISSION.md` | 01 · Lead and story (Mario) | The project page text, from hour 30 |
| `index.html` | 06 · App developer (Darius) | The page |
| `app/` | 06 · App developer (Darius) | The page's scripts, styles and images, if they get a folder |
| `.github/workflows/pages.yml` | 06 · App developer (Darius) | The GitHub Pages deploy |
| `docs/figures/` | all roles · name each figure with your role number first, e.g. 03_rate_129A.png | Figures for the team and the slides, PNG under 1 MB |
| `notebooks/01/` | 01 · Lead and story (Mario) | Exploration only, outputs stripped, never imported |
| `notebooks/02/` | 02 · NISAR data (Alexandru, Eric) | Exploration only, outputs stripped, never imported |
| `notebooks/03/` | 03 · InSAR analyst (Alexandru, Eric) | Exploration only, outputs stripped, never imported |
| `notebooks/04/` | 04 · Geodesist (Matei) | Exploration only, outputs stripped, never imported |
| `notebooks/05/` | 05 · Validator (Paul) | Exploration only, outputs stripped, never imported |
| `notebooks/06/` | 06 · App developer (Darius) | Exploration only, outputs stripped, never imported |

## Sentinel-1 handoff

| File | Owner | What to do with it |
| --- | --- | --- |
| `sentinel1/` | 03 · InSAR analyst (Alexandru, Eric) | Sentinel-1 data manifest, fitted results, and team handoff |
