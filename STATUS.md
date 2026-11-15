# Status

**Owner:** 01 · Lead and story (Mario); every role updates its own row

Final state, Sun 15 Nov 2026, Europe/Bucharest. The hour-by-hour history of this file is in git; every decision is in [DECISIONS.md](DECISIONS.md).

**Phase:** submitted. Live page: https://pea-dancingwiththesars.vercel.app. Submission text: [SUBMISSION.md](SUBMISSION.md).

## Where each part stands

| Part | State | Where |
| --- | --- | --- |
| NISAR data (02) | 22 GUNW pairs, 129A (15 dates, 7 Nov 2025 to 21 Oct 2026) and 094D (10 dates, 20 Jun to 18 Oct 2026); own GSLC pairs for the 094D sign test | `data/scenes/`, `fetch.py`, `notebooks/02/` |
| NISAR analysis (03) | Time series and rates; 129A passes the sign test, 094D fails it and is shown flagged; experimental up and east | `stack.py`, `split.py`, `notebooks/03/` |
| Sentinel-1 (03) | 374 HyP3 jobs, May 2025 to November 2026: 029A 94 dates, 007D 96 dates; six processing variants | `sentinel1/` |
| Prediction (03) | Chronos-2, zero-shot, per 240 m cell of the town and per salt field, tested on the last 60 days | `sentinel1/scripts/forecast_area.py`, `forecast_zones.py` |
| References and tie (04) | EuVeM2022 tie, EGMS model swap, noise floor of NISAR | `refs.py`, `calibrate.py`, `noise_floor.py` |
| Validation (05) | 5 pass, 6 warn, 1 fail, 12 info; red-team of the pin | `validate.py`, `docs/validation-log.md`, `notebooks/05/` |
| Page and hosting (06) | Live, both radars, timeline, pin, house and area tools, forecast, satellites now, Terms & Conditions | `index.html`, `app/`, `export.py`, `vercel.json` |
| Submission (01) | Text ready; the 7-slide deck is presented by the team | `SUBMISSION.md` |

## Checks at submission

- `pytest -q` passes; `python checkpoint.py ocnele_mari` reports the file contracts OK.
- No `TODO`, `TBD` or blank placeholder in the page, its products or `SUBMISSION.md`.

## Known limits

See [README.md](README.md), "What the page cannot tell you" and "Next steps".
