# CLAUDE.md

**Owner:** 01 · Lead and story (Mario); changes agreed by the team

Context for Claude Code sessions in this repo. Six people each run their own session, one per role, so these rules keep six sessions from colliding.

## What this is

This is the team repo for NASA Space Apps 2026 (14 to 15 Nov), challenge "Dancing with the SARs". The project, **Dancing on Salt**, uses two radars, **NISAR** (L-band) and **Sentinel-1** (C-band), to show how the ground moves above the salt-brine fields of **Ocnele Mari**, Romania (D-004). It ties the radar to open GNSS velocity models, and checks it against held-out stations, EGMS Ortho, the other radar and a synthetic stack with a known answer. The output is a static web page: a map that opens on the town, a **satellite switch** (NISAR, Sentinel-1, Compare), several views of the same trend, a time slider with honest gaps, station pins that say whether satellite and ground agree, and story stops. We present it in a **7-slide PowerPoint, with no video** (D-003).

**Status:** skeleton. The plan, the rules, the pipeline interfaces (stubs) and the working tools are in place, and there is no page yet. The advisor's rehearsal showed that the signal (about −25 mm/yr at most) is below NISAR's first-months per-pixel noise (37 to 51 mm/yr), so the story framing is open (O-01). See `STATUS.md` for where things stand right now.

## Read first

1. `STATUS.md`: where the build is, and what is waiting on whom.
2. `docs/schedule.md`: your role's column, hour by hour, with the gates and cut lines.
3. `docs/build-spec.md`: the locked and proposed decisions, the file contracts, **your role's section**, done-criteria, unknowns, open decisions and the change log.
4. `docs/overview.md`: what we build and why, the candidate claims and how each could fail, scope, schedule, risks.
5. `docs/data.md` and `docs/rehearsal.md`: the data, its traps, and what the rehearsal found.
6. `DECISIONS.md`: what was decided without the whole team, and why.

`docs/synopsis.md` is the one-page version, and `prompts/build.md` is the prompt that drives a role's session.

## Who owns what

**Find out which role you work for first:** ask the human, or read the branch name (`r01/…` to `r06/…`). Edit only that role's files. **The full list, file by file, is [OWNERS.md](OWNERS.md)**, and every file says its owner in its first lines (`# Owner:` or `**Owner:**`). When you create a file, add a row to `OWNERS.md` and an owner line to the file in the same PR; `pytest -q` checks both. If a task needs a change in another role's file, write the proposed change for your human to pass on.

| Path | Owner |
| --- | --- |
| `checkpoint.py`, `README.md`, `STATUS.md` (team view), `SUBMISSION.md`, the build spec's change log and open-decisions table | 01 · Lead and story (Mario) |
| `fetch.py`, `data/scenes/` | 02 · NISAR data (Alexandru and Eric) |
| `stack.py`, `split.py` | 03 · InSAR analyst (Alexandru and Eric) |
| `refs.py`, `calibrate.py` | 04 · Geodesist (Matei) |
| `validate.py`, `hyp3_order.py`, `docs/validation-log.md` | 05 · Validator (Paul) |
| `export.py`, `mock_products.py`, `index.html` and the page's assets (not created yet), the Pages workflow when it exists | 06 · App developer (Darius) |
| `common.py`, `run_all.py`, `tests/`, `requirements.txt`, `.github/` | shared: announce changes; 01 reviews |
| `DECISIONS.md`, `CITATIONS.md`, the log in `AI-DISCLOSURE.md`, your row of `STATUS.md` | everyone appends; never rewrite others' lines |
| `products/<site>/` | written by scripts only, never by hand |
| `docs/` other than the above, `prompts/`, `INFO.md`, `LICENSE` | do not edit unasked; report problems instead |

## Hard rules

- **Never commit data or credentials.** That means:
  - nothing under `data/work/` or `data/raw/`;
  - no `.h5`, `.nc`, `.npz` or `.zip` files;
  - no `.env`, `.netrc` or Earthdata token.

  Small committed lists such as `data/scenes/*.csv` are fine. GeoTIFFs and PNGs are allowed only under `products/<site>/`.
- **Scope is Ocnele Mari only (D-001).** `demo` and `mock` are test sites, not sites.
- **The map opens on Ocnele Mari, with Romania blurred when zoomed out (D-002).**
- **The submission is a 7-slide PowerPoint, with no video (D-003).** Each slide has an owner role; see `docs/overview.md`, "The slides".
- **Two radars, one switch (D-004).** Both NISAR and Sentinel-1 are fitted. The page has a satellite switch and the views in `docs/ui.md`. Compare them only on the same months and reference, each in its own line of sight, on one shared legend (`docs/ui.md`, "Honest comparison rules"). Sentinel-1 lives in `sentinel1/` (03).
- **Decisions in `docs/build-spec.md` are frozen after the hour-2 review.** Don't change cuts, thresholds, windows, tests or the file contracts. If one looks wrong, write a proposal with the evidence; the team decides, and 01 logs it in the change log.
- **Honest numbers.**
  - Every number on the page, in the slides and in the submission comes from `products/ocnele_mari/`, written by the pipeline.
  - Never hard-code a number, round it to flatter, or tune it until it looks right.
  - Never flip the phase sign to pass a check.
  - Never quote −250 mm/yr: it was a factor-10 error in the deck.
- **No silent placeholders.** Mock and synthetic outputs carry `synthetic: true` and show "Simulated, not data". Before submitting, `___`, `TODO`, `TBD` and `computing` must appear nowhere in the page, `SUBMISSION.md` or the slides.
- **The validator is independent.** Nobody else edits `validate.py`, and 05 edits no science script.
- **Freeze at hour 40.** After that, nothing that changes a number; only text, styling and the slides.
- **Ask your human before you:**
  - run `sudo` or any system-level install;
  - push to a branch other than your own role branch, or deploy;
  - download more than 5 GB in one session;
  - delete anything outside `data/` and your own files;
  - use any login.

  Never ask for, print or store a password or token. Never use ROMPOS data or anything derived from it.
- **Log as you go:**
  - a line in `DECISIONS.md` for any choice you make without asking;
  - a row in `CITATIONS.md` for any source;
  - a row in the log of `AI-DISCLOSURE.md` for anything substantive you produce;
  - your row in `STATUS.md` at each checkpoint.

## Conventions

| Quantity | Convention |
| --- | --- |
| LOS rate, cumulative LOS | mm/yr, mm; positive = towards the satellite |
| Up, east | mm/yr; up positive (sinking is negative), east positive |
| GNSS and model velocities | Eurasia-fixed, mm/yr |
| Dates | ISO `YYYY-MM-DD`; pair files `YYYYMMDD_YYYYMMDD` (reference_secondary) |
| Tracks | `129A` (ascending), `094D` (descending) |
| Time in fits | years since 2026-01-01 |
| Grid | the product's UTM (EPSG 326xx), 80 m; overlays resampled to lon/lat for the map |
| Colours | RdBu diverging, red = sinking or away from the satellite; never red and green alone |
| Statistics | zone medians, 95 % intervals from 1,000 bootstrap draws over dates, seed 2026 (proposed) |

**Code:**

- **Python and layout:** Python 3.11 or later. One script per step at the repo root, run as `python <step>.py <site>`.
- **Shared settings:** `import common as C`. Paths, sites, zones, stations and thresholds come from `common.py`, never hard-coded.
- **Stubs:** a stub raises `raise C.todo("NN", "what is missing")`. Entry points run through `C.run_cli(main)`, so a stub exits with code 3 and one readable line.
- **Import cost:** keep top-level imports light so `--help` works before the environment is installed.
- **Output:** print one summary line per track. Exit non-zero on failure.
- **Tests:** `pytest -q` (tests in `tests/`) must pass before every push. Notebooks are for exploration under `notebooks/<role>/` with outputs stripped, and are never imported.

## Writing in this repo

Write plain sentences. Don't use em-dashes. Every number carries its unit and, for anything that can change, the date it was checked. Link your sources. Say what a result cannot tell you.

## Git

- **Branches:** one per role and task (`r02/fetch-window`, `r06/slider`). Small PRs to `main`, merged by the owner once `pytest -q` passes. PRs touching `common.py` or the file contracts need 01's review.
- **Keep current:** pull `main` often.
- **Never:** force-push `main`, or rewrite someone else's branch.
