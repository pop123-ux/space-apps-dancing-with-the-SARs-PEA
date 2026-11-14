# Dancing on Salt

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
- **[docs/overview.md](docs/overview.md):** why it matters, the page, the candidate claims and how each could fail, the video, scope in tiers, the 48 hours, risks and fallbacks.
- **[docs/build-spec.md](docs/build-spec.md):**
  - the locked and proposed decisions, and the file contracts between roles;
  - **each role's steps**, done-criteria per tier and unknowns;
  - the open team decisions and the change log.
- **[prompts/setup.md](prompts/setup.md):** a Claude Code prompt that sets up a team member's laptop. Open Claude Code in this folder and say "Read prompts/setup.md and carry it out."
- **[prompts/early-tests.md](prompts/early-tests.md):** tests T0 to T10 for the first hours, each with an owner, a timebox and a fallback.
- **[prompts/build.md](prompts/build.md):** the Claude Code prompt each person uses to build their role. Say "Read prompts/build.md. I am role 0N."
- [docs/rehearsal.md](docs/rehearsal.md): what the advisor's rehearsal on real data found, and what it changes.
- [docs/data.md](docs/data.md): the NISAR pairs, the references and the data traps.
- [DECISIONS.md](DECISIONS.md): the decision log. [CITATIONS.md](CITATIONS.md): sources, prior work and advisor help. [docs/AI_USE.md](docs/AI_USE.md): how AI was used.
- [CLAUDE.md](CLAUDE.md): the rules and conventions for Claude Code sessions in this repo.
- [INFO.md](INFO.md): the team's site notes (in Romanian).

## Status (Sat 14 Nov, 13:30 Europe/Bucharest)

**Skeleton.** The plan, the rules, the pipeline interfaces and the working tools are in place. The pipeline steps are stubs, and there is no page yet.

Two decisions are locked:

- **D-001:** Ocnele Mari is the only site.
- **D-002:** the map opens on the town, with Romania blurred when you zoom out.

Everything else is proposed until the hour-2 review.

## Team

| # | Role | Who | Owns |
| --- | --- | --- | --- |
| 01 | Lead and story | Mario | scope, cut lines, checkpoints, story, video, submission; `checkpoint.py` |
| 02 | NISAR data | Alexandru and Eric | search, streamed windows, masks, ionosphere; `fetch.py` |
| 03 | InSAR analyst | Alexandru and Eric | time series, rates with errors, up and east; `stack.py`, `split.py` |
| 04 | Geodesist | Matei | references, frame, tie, model swap; `refs.py`, `calibrate.py` |
| 05 | Validator | Paul | stations, EGMS, Sentinel-1, checks, red team; `validate.py`, `hyp3_order.py` |
| 06 | App developer | Darius | products, the page, map, slider, pins, story mode; `export.py`, `mock_products.py` |

## Layout

```
STATUS.md  DECISIONS.md  CITATIONS.md  CLAUDE.md  README.md  INFO.md  LICENSE
common.py               shared settings: site, zones, stations, thresholds, helpers
refs.py fetch.py stack.py calibrate.py split.py validate.py hyp3_order.py export.py
                        the pipeline, one script per owner (stubs with fixed interfaces)
checkpoint.py           01: is products/<site>/ complete? (works)
run_all.py              runs the steps in order and stops cleanly at the first stub (works)
mock_products.py        06: invented products/mock/ on the real acquisition dates (works)
tests/                  pytest smoke test; must pass before every push
data/scenes/            committed query output: the 22 NISAR pairs over the town (CMR, 14 Nov)
data/work/              local intermediates, git-ignored
products/<site>/        what the page reads (written by scripts only)
prompts/                Claude Code prompts: setup, early tests, build
docs/                   synopsis, overview, build spec, data, rehearsal, AI use, validation log
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
