# Dancing on Salt · NISAR over Ocnele Mari

**NASA Space Apps 2026 · "Dancing with the SARs"** · 14–15 November 2026

We measure how the ground moves above the salt-brine fields of **Ocnele Mari** (Vâlcea, Romania) with **NISAR** L-band radar. We tie the radar to open GNSS velocity models, check it against stations, EGMS and Sentinel-1, and show it on one map that plays through time.

> **Status: skeleton.** The plan, the rules, the run sheets and the pipeline interfaces are in place, and every pipeline step is a stub. There is no app yet. Only two decisions are locked: the site (Ocnele Mari only) and the map behaviour (it opens on Ocnele Mari, with Romania blurred when you zoom out).

## Start here

| Read | For |
|---|---|
| [BUILD.md](BUILD.md) | The plan: what we know going in, architecture, pipeline, the 48 hours, cut lines, guardrails |
| [CLAUDE.md](CLAUDE.md) | Rules for AI assistants and the quickest summary of how we work |
| [roles/](roles/) | Your run sheet |
| [docs/decisions.md](docs/decisions.md) | What is locked and what is still open |
| [docs/contract.md](docs/contract.md) | The files the page reads (DRAFT until hour 2) |
| [INFO.md](INFO.md) | Site context: salt zones, links (in Romanian) |

## Team

| # | Role | Who | Owns |
|---|---|---|---|
| 01 | Lead & story | Mario | scope, cut lines, checkpoints, story, video, submission · `checkpoint.py` |
| 02 | NISAR data | Alexandru & Eric | ASF search, streamed windows, masks, ionosphere · `fetch.py` |
| 03 | InSAR analyst | Alexandru & Eric | time series, rates ± σ, closure, up/east · `stack.py`, `split.py` |
| 04 | Geodesist | Matei | references, frame, tie, model swap · `refs.py`, `calibrate.py` |
| 05 | Validator | Paul | stations, EGMS, Sentinel-1, checks, red team · `validate.py`, `hyp3_order.py` |
| 06 | App developer | Darius | products, map, slider, pins, story mode, phone · `export.py`, `mock_products.py`, page |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python test_skeleton.py          # prints "ok:" when the skeleton is healthy
python mock_products.py          # writes an invented products/mock/ to build the page on
python checkpoint.py mock        # checks it against the contract
```

Real NISAR data need a free [Earthdata](https://urs.earthdata.nasa.gov) account and token. Copy `.env.example` to `.env`, or export `EARTHDATA_TOKEN`. **Never commit it.**

## Repository

```
BUILD.md  CLAUDE.md  README.md  INFO.md  LICENSE
common.py                         shared settings: site, zones, stations, thresholds, helpers
refs.py → fetch.py → stack.py → calibrate.py → split.py → validate.py → export.py    pipeline (stubs)
hyp3_order.py                     Sentinel-1 orders for the second-radar check (stub)
checkpoint.py  run_all.py  mock_products.py  test_skeleton.py                         working tools
roles/                            six run sheets
docs/                             decisions · contract · science notes · data sources · prior work · AI use · story · submission · validation log
products/<site>/                  what the page reads (written by scripts)
data/                             local data, git-ignored
```

## Data, credits, prior work, AI

- **Sources and credits:** [docs/data-sources.md](docs/data-sources.md). The main ones are NISAR (NASA–ISRO, ASF DAAC), EGMS (Copernicus), EuVeM2022 (Lantmäteriet), NGL, Muntean et al. 2026 and Sentinel-1.
- **Prior work and advisor help, declared:** [docs/prior-work.md](docs/prior-work.md).
- **How AI tools were used:** [docs/ai-use.md](docs/ai-use.md).

## License

[MIT](LICENSE). Third-party data are linked and credited, not redistributed.
