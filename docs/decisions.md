# Decisions

The Lead (01) maintains this file. Anyone can propose; only the team decides. When an OPEN item is decided, move it to **Locked** with the date, the decision and who was in the room.

## Locked

| ID | Date | Decision | Why |
|---|---|---|---|
| D-001 | 2026-11-14 | **Ocnele Mari is the only site of analysis.** Praid and Slănic (advisor deck and kit) are out of scope. | Our hometown story; one site done well. |
| D-002 | 2026-11-14 | **The map opens zoomed on the Ocnele Mari area** (Google Maps view `45.086281, 24.2704806`, zoom 13; town pin `45.0838382, 24.2859745`). Zooming out shows the Romanian area, deliberately **blurred / de-emphasised**: context only, not data. | Only our area of interest matters on the map. |

## Plan rules adopted from the advisor deck (default; the team may override)

| ID | Rule |
|---|---|
| P-1 | No server, no database: a static page on GitHub Pages that reads `products/` only. |
| P-2 | Raw data stay out of git; one command rebuilds `products/` from open sources. |
| P-3 | The file contract is frozen at hour 2, so the app starts on mock files. |
| P-4 | Numbers freeze at hour 40; after that, only text, captions, styling and video. |
| P-5 | Six roles, one owner per script; the validator is independent. |
| P-6 | Cut lines agreed before the clock starts and never reopened (BUILD.md §9). |
| P-7 | Open references only; no ROMPOS data. |

## Open

| ID | Question | Options (not exhaustive) | Owner | Needed by |
|---|---|---|---|---|
| O-01 | **Story framing at Ocnele Mari**, given that the rehearsal shows the subsidence (≈ −25 mm/yr at most) below NISAR's first-months per-pixel noise (37–51 mm/yr). | (a) "The honest test": what NISAR's first months can and cannot see at a slow salt site, at zone level, with the checks shown. (b) Subsidence story, if zone medians beat their error after the corrections. (c) A backscatter (GCOV) change angle at Ocnele Mari, alone or alongside. | 01 with all | Hour 2 |
| O-02 | Does the 13 November guide allow the advisor's rehearsal kit as prior work, and how must it be declared? | Read the guide aloud at hour 0. | 01 | Hour 1 |
| O-03 | **Adopt the advisor kit's code, or build our own** and use the kit as a reference? | (a) Adopt and declare it, then improve. (b) Rebuild in the stubs and compare against the kit's numbers. (c) Mixed, per role. | All | Hour 1 |
| O-04 | Hour 0 (local time) and the event's submission deadline | Fill into BUILD.md §8. | 01 | Hour 0 |
| O-05 | Time-series method | MintPy (`prep_nisar` + `smallbaselineApp`, as in the deck) or our own small-baseline inversion (as in the rehearsal). Also: do we split up/east on the common June–October 2026 window only? | 03 | Hour 6 |
| O-06 | Second velocity model for the model swap | EGMS GNSS model (CSV link still to be found) against EuVeM2022; fallback "rigid plate". | 04 | Hour 18 |
| O-07 | Closure test (short-pair bias) | Form 24/36-day pairs from GSLC (11 dates on 094D, 15 on 129A) or drop the check and declare it untested. | 02 + 03 | Hour 18 |
| O-08 | **Is there an ML/AI component** in 02/03, and how is it tested? | Only if it beats a simple baseline on held-out checks (stations, EGMS stable ground, synthetic truth). Candidates: learned atmospheric correction against the empirical elevation slope; unwrapping-error / bad-pair detection; uncertainty calibration. | 02 + 03 | Hour 12 |
| O-09 | Basemap and how Romania is blurred when zoomed out (D-002) | Tile source; CSS blur or opacity on zoom < N; a Romania outline only. | 06 | Hour 6 |
| O-10 | Contract freeze: accept docs/contract.md as drafted (advisor kit contract + `view`), or change it | | 01 + 06 | Hour 2 |
| O-11 | Analysis window size | 50 × 50 km (kit; needed for stable ground and stations) vs smaller. The UI focus (D-002) is independent of it. | 02 + 04 | Hour 6 |
| O-12 | Is the HAR1 lesson shown in the app (it is outside the window) or only in the video? | | 01 | Hour 24 |
| O-13 | Can values from the Muntean et al. 2026 supplement be quoted in the app? | Ask the authors (INFP); else show "published rate, see paper". | 01 | Hour 24 |
| O-14 | Why is there no NISAR over Romania from mid-January to late June 2026? | ASF / NISAR forum; the first question a judge asks. | 02 | Hour 24 |
| O-15 | The Praid / Slănic slots freed by D-001 (02 and 03, hours 6–30) | Deeper Ocnele Mari: zone series, GSLC closure, Sentinel-1 comparison, ML track (O-08). | 01 | Hour 6 |
