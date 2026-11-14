# Dancing on Salt

**Owner:** 01 · Lead and story (Mario)

This is the team repo for NASA Space Apps 2026, challenge **Dancing with the SARs**, on 14 to 15 Nov 2026. Six people, one site: **Ocnele Mari**, Romania.

## The project

We're building a web page that shows anyone how the ground moves above the salt-brine fields of Ocnele Mari, in Vâlcea county.

- **Measurement:** NISAR's L-band radar has 22 interferograms over the town, from November 2025 to October 2026.
- **Reference frame:** the radar is tied to open GNSS velocity models.
- **Checks:** every number is checked against GPS stations, the European Ground Motion Service and Sentinel-1.
- **Page:** it opens on the town, plays the ground through time, and says plainly where the radar cannot yet see the motion.

Start here:

- **[docs/synopsis.md](docs/synopsis.md):** the one-page version, to explain the project to the team.
- **[STATUS.md](STATUS.md):** where the build is right now, what waits on whom, and each role's next step.
- **[docs/schedule.md](docs/schedule.md):** who does what, hour by hour: one column per role, with the gates and cut lines.
- **[docs/ui.md](docs/ui.md):** the page's design: the satellite switch (NISAR, Sentinel-1, Compare), the five views, and the honest comparison rules (D-004).
- **[OWNERS.md](OWNERS.md):** every file and its owner role (01 to 06, or shared), grouped by role. Each file also says its owner in its first lines.
- **[docs/overview.md](docs/overview.md):** why it matters, the page, the candidate claims and how each could fail, the 7 slides, scope in tiers, the 48 hours, risks and fallbacks.
- **[docs/build-spec.md](docs/build-spec.md):**
  - the locked and proposed decisions, and the file contracts between roles;
  - **each role's steps**, done-criteria per tier and unknowns;
  - the open team decisions and the change log.
- **[prompts/setup.md](prompts/setup.md):** a Claude Code prompt that sets up a team member's laptop. Open Claude Code in this folder and say "Read prompts/setup.md and carry it out."
- **[prompts/early-tests.md](prompts/early-tests.md):** tests T0 to T10 for the first hours, each with an owner, a timebox and a fallback.
- **[prompts/build.md](prompts/build.md):** the Claude Code prompt each person uses to build their role. Say "Read prompts/build.md. I am role 0N."
- [docs/rehearsal.md](docs/rehearsal.md): what the advisor's rehearsal on real data found, and what it changes.
- [docs/data.md](docs/data.md): the NISAR pairs, the references and the data traps.
- [DECISIONS.md](DECISIONS.md): the decision log. [CITATIONS.md](CITATIONS.md): sources, prior work and advisor help.
- **[AI-DISCLOSURE.md](AI-DISCLOSURE.md):** how we used AI tools: the text for the submission, and the running log everyone appends to.
- [CLAUDE.md](CLAUDE.md): the rules and conventions for Claude Code sessions in this repo.
- [INFO.md](INFO.md): the team's site notes (in Romanian).

## Status (Sat 14 Nov, 13:30 Europe/Bucharest)

**Skeleton.** The plan, the rules, the pipeline interfaces and the working tools are in place. The pipeline steps are stubs, and there is no page yet.

Two decisions are locked:

- **D-001:** Ocnele Mari is the only site.
- **D-002:** the map opens on the town, with Romania blurred when you zoom out.
- **D-003:** the submission is a 7-slide PowerPoint, with no video.
- **D-004:** two radars, one switch. We fit both NISAR and Sentinel-1, and the page switches between them and shows the same trend several ways (`docs/ui.md`). Sentinel-1 is already fitted in `sentinel1/`.

Everything else is proposed until the hour-2 review.

## Team

| # | Role | Who | Owns |
| --- | --- | --- | --- |
| 01 | Lead and story | Mario | scope, cut lines, checkpoints, story, the 7-slide deck, submission; `checkpoint.py` |
| 02 | NISAR data | Alexandru and Eric | search, streamed windows, masks, ionosphere; `fetch.py` |
| 03 | InSAR analyst | Alexandru and Eric | time series, rates with errors, up and east; `stack.py`, `split.py` |
| 04 | Geodesist | Matei | references, frame, tie, model swap; `refs.py`, `calibrate.py` |
| 05 | Validator | Paul | stations, EGMS, Sentinel-1, checks, red team; `validate.py`, `hyp3_order.py` |
| 06 | App developer | Darius | products, the page, map, slider, pins, story mode; `export.py`, `mock_products.py` |

## Layout

```
STATUS.md (01)  OWNERS.md (01)  DECISIONS.md  CITATIONS.md  AI-DISCLOSURE.md (all)  CLAUDE.md (01)  README.md (01)
common.py               shared: site, zones, stations, thresholds, helpers
refs.py (04) fetch.py (02) stack.py (03) calibrate.py (04) split.py (03) validate.py (05) hyp3_order.py (05) export.py (06)
                        the pipeline, one script per owner (stubs with fixed interfaces)
checkpoint.py           01: is products/<site>/ complete? (works)
run_all.py              shared: runs the steps in order and stops cleanly at the first stub (works)
mock_products.py        06: invented products/mock/ on the real acquisition dates (works)
tests/                  shared: smoke test and owner check; must pass before every push
data/scenes/            02: the 22 NISAR pairs over the town (CMR, 14 Nov)
data/work/              local intermediates, git-ignored
products/<site>/        what the page reads (written by scripts only)
prompts/                01: Claude Code prompts: setup, early tests, build
docs/                   01: synopsis, overview, schedule, build spec, rehearsal · 02: data · 05: validation log
slides/                 01: the 7-slide PowerPoint (D-003), not created yet
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                          # the smoke test
python mock_products.py            # writes an invented products/mock/ to build the page on
python checkpoint.py mock          # checks it against the file contracts
```

Searching ASF needs no login. Reading NISAR needs a free [Earthdata](https://urs.earthdata.nasa.gov) token in `.env` (see `.env.example`), and that file never goes in the repo.

## License

[MIT](LICENSE). Space Apps distributes submission content under Apache 2.0, so 01 checks the 2026 guide (O-17). Third-party data are linked and credited, not redistributed.
