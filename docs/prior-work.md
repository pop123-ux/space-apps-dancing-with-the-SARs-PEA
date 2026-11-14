# Prior work and advisor help

The submission must list prior work and advisor help **plainly** (deck, item 07). Everything here existed before the clock started, or came from outside the team. **Append in the same PR in which you reuse something.** The Lead checks this list against the 13 November guide (O-02) before submitting.

## Advisor

- **Miluță Dulea-Flueraș, team advisor.** Prepared the team plan deck (12 Nov 2026) and the rehearsal kit below.
  - Agreed role: points us to open references, checks frame choices, red-teams at hours 12, 24 and 40, and answers geodesy questions.
  - The advisor does not write our code or run our processing.

## Before the event

| What | By | Contents | How we use it |
|---|---|---|---|
| *Dancing on Salt* team plan (19 slides, 12 Nov 2026) | Advisor | Brief, adversarial review, sites, references, pipeline, roles, hour plan, cut lines, judging | Basis of BUILD.md. Our copy still says −250 mm/yr; that is corrected to about −25 mm/yr in deck v10. |
| **Rehearsal kit** `dancing-on-salt` (12 Nov 2026) | Advisor | Working end-to-end pipeline (`fetch`, `refs`, `stack`, `calibrate`, `split`, `validate`, `export`, `checkpoint`, `run_demo`, `test_demo`), static `index.html`, synthetic demo products, a real Ocnele Mari run with checks, GLOSSARY, OPEN_ITEMS, six role sheets | **This skeleton follows its architecture, file names, ownership and products contract, and quotes its findings** (BUILD.md §3, science-notes). **No kit code is copied into this repository.** Whether the team adopts its code is decision O-03. The kit is not committed (it holds data, 207 MB). |
| Salt-events study (EGMS extracts, `egms_extract.py`, `hyp3_plan.py`) | Advisor / earlier study | EGMS L3 Up points for Ocnele Mari 2019–2023 and 2020–2024; HyP3 ordering pattern | Not used yet. If reused, list it here. |
| 2024–2026 Sentinel-1 HyP3 stack (8- vs 16-day bias) | Earlier study | Short-pair bias +20–40 % | Quoted as a lesson only |
| HAR1 station study | Earlier study | Mast motion and frost jacking | Quoted as a lesson only |
| LSTM vs seasonal model (6.6 vs 5.4 mm) | Earlier study | Out-of-sample comparison | Quoted as a lesson only |
| Hârșova 2025 rise | Earlier study | "Possible, not proven" | Quoted as a lesson only |

## Third-party tools

Python, NumPy, SciPy, pandas, h5py, pyproj, asf_search, hyp3_sdk, rasterio, matplotlib, Pillow, Leaflet; MintPy if O-05 picks it. Each is credited under its own license.

## Built during the event

The Lead fills this in at hours 30–40: what is new in the 48 hours, file by file.
