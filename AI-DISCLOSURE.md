# AI disclosure

**Owner:** all roles append to the log; 01 finalises section 1

This file says how we used AI tools to build **Dancing on Salt** for NASA Space Apps 2026 (Cluj-Napoca, 14 to 15 Nov 2026), and what people did and checked. Space Apps allows AI tools (it now calls them "SI"), and the submission must say how they were used. The disclosure below is the text for the project page. The log underneath is the record it is built from.

**Exact wording:** 01 (Mario) checks the required wording and field against the 2026 Project Submission Guide (13 Nov) and the Cluj-Napoca participant's guide, then finalises section 1 in hours 30 to 36.

**Everyone appends to the log** (section 5) when an AI tool produces code, text, figures or analysis that ends up in the project, and says what a person checked. Never rewrite someone else's line.

## 1. Disclosure for the submission

Draft of Sat 14 Nov 2026, 14:30 Europe/Bucharest. 01 finalises it from the log.

> We used AI coding assistants throughout. Each of our six team members ran Claude Code (Anthropic) for their own role, under shared written rules (`CLAUDE.md`, `prompts/build.md`). It set up the repository and its plan documents, wrote and reviewed processing code, and helped draft text. Before the event, one member used ChatGPT (OpenAI) to summarise our advisor's plan and rehearsal material.
>
> AI did not produce any of our data or results. Every number on the page comes from our pipeline running on open data (NISAR, EGMS, EuVeM2022, NGL, Sentinel-1). It is checked against independent references by a team member who does not edit the science code. We used no AI image, video, voice or music generation. People made every team decision, typed every login, and reviewed and merged every change. The full log is in `AI-DISCLOSURE.md` in our repository.

## 2. Tools

| Tool | Maker | Who used it | For what |
| --- | --- | --- | --- |
| Claude Code | Anthropic | All six roles, one session each | Repository and plan documents, pipeline code and stubs, tests, data checks (for example the NISAR catalogue query), drafting text |
| ChatGPT | OpenAI | 02/03 (Alexandru), before the event | A research summary of the advisor's deck and rehearsal kit |

Add a row the moment anyone uses another AI tool.

## 3. What AI was not used for

- **Data and results.** No number on the page, on the slides or in the submission is produced or adjusted by AI. All of them come from `products/ocnele_mari/`, written by the pipeline (`CLAUDE.md`, "Honest numbers").
- **Media.** No generated images, video, voices or music. Map overlays are computed from radar data. Any diagram is drawn from simple shapes and carries the note "Diagram made with AI assistance".
- **Decisions.** Team decisions (the site, the story, the frozen methods) are made by people at the checkpoints and logged in `docs/build-spec.md`. AI sessions record only small working choices, in `DECISIONS.md`, where anyone can see and overturn them.
- **Accounts.** AI never sees passwords or tokens. People log in themselves.

## 4. How people checked AI output

- **Ownership:** each file has one owner (`CLAUDE.md`, "Who owns what"), who reviews and merges the AI-written changes to it.
- **Tests:** `pytest -q` runs before every push and in GitHub Actions on every push.
- **Contract:** `checkpoint.py` checks that the products match the file contracts, at hours 2, 12, 24 and 40.
- **Independent validation:** the validator (05) owns `validate.py`, which no one else edits. It runs the checks nobody tuned: the sign of the motion, held-out GNSS stations, EGMS on stable ground, Sentinel-1 and closure.
- **Known answer:** a synthetic stack with a known truth, including a planted lying station, runs through the same code.
- **Red team:** the advisor red-teams the work at hours 12, 24 and 40.

## 5. Log

One row per substantive use. The "checked" column says what a person verified, not what the tool claimed.

| Date and time (Europe/Bucharest) | Who (role) | Tool | What it produced | What a person checked |
| --- | --- | --- | --- | --- |
| 13 to 14 Nov 2026, before the event | Alexandru (02/03) | ChatGPT | A research summary of the advisor's deck and rehearsal kit | To fill in |
| Sat 14 Nov 2026, about 12:45 | Alexandru (02/03) | Claude Code | The repository skeleton: plan documents, `common.py`, the pipeline stubs (interfaces only, no science), `checkpoint.py`, `run_all.py`, `mock_products.py`, the smoke test. It also ran the NISAR GUNW catalogue query on NASA CMR (22 pairs) | To fill in: each owner reviews the stub and section for their role |
| Sat 14 Nov 2026, about 13:30 | Alexandru (02/03) | Claude Code | Restructured the documents (`STATUS.md`, `DECISIONS.md`, `CITATIONS.md`, `docs/`, `prompts/`); wrote `data/scenes/ocnele_mari_gunw.csv` from CMR | To fill in |
| Sat 14 Nov 2026, about 14:30 | Alexandru (02/03) | Claude Code | `docs/schedule.md` (who does what, hour by hour) and this disclosure file | To fill in: 01 checks the wording against the guides |
| Sat 14 Nov 2026, about 15:00 | Alexandru (02/03) | Claude Code | `OWNERS.md`, an owner line in every file, `tests/test_owners.py`; switched the plan from a video to the 7-slide PowerPoint (D-003) with an owner per slide | To fill in: each role checks its rows in `OWNERS.md` and its slide |
| Sat 14 Nov 2026, about 15:30 | Alexandru (02/03) | Claude Code | D-004 design: `docs/ui.md` (satellite switch, five views, comparison rules); the sensor-aware draft contract in `checkpoint.py` and `mock_products.py` (both radars); D-004 through the plan documents; a Sentinel-1 coverage check on NASA CMR | To fill in: 06 reviews `docs/ui.md`; 03 and 04 review the comparison rules (O-19) |
| Sat 14 Nov, about 13:20 | Matei (04) | Claude Code | `refs.py` (EuVeM2022 and NGL MIDAS download and parsing, distance filter, published rates, synthetic stand-ins with a lying station), `calibrate.py` (model to LOS, tie mask, offset or plane fit with 3σ clipping, model swap, `calib.json`), the VLC2 vertical in `common.PUBLISHED`. Synthetic known-answer runs: offsets −8.81 and −6.02 mm/yr for truths −8.8 and −6.0; plane slope 3.99 for 4.0 mm/yr per 10 km. | To fill in: Matei checks the VLC2 row of Table S3 on the PDF page by eye, and runs `refs.py ocnele_mari` on real data |
| Sat 14 Nov 2026 | R04 integration review | ChatGPT | Cross-checked the cited station rows and reproduced the synthetic calibration with independent inputs. Corrected VLC2 east/north, restored owner headers and integrated the disclosure and status updates. | Pending: Matei reviews real station output and runs T8 with 05. |
| Sat 14 Nov 2026, about 16:40 | Alexandru (02/03), verifier | Claude Code (with a review subagent) | Code review of main; fixes in sentinel1/scripts (group-aware solver, no fixed pair/date counts, compare.py on the common window with the fit's estimator, grid manifest and pack_grids.py); tests/test_sentinel1_fit.py | Regression test: new solver equals the old one exactly on one network; to fill in: 03 reviews the fit changes |
| Sat 14 Nov 2026 | 06 integration handoff | ChatGPT | Prepared and documented the verified Sentinel-1 UI exports and provenance, NISAR coverage, sensitivity controls, pending EGMS history and Claude Code kickoff. | Product contract and overlay checks passed in the handoff. 06 reviews the frontend integration. |
| Sat 14 Nov 2026, about 15:20 | Matei (04) | Claude Code | Checked `common.PUBLISHED` and the NGL MIDAS parsing against the supplement PDF (Tables S1, S3) and the MIDAS readme (E/N order, sign, units, frame, dates); added HORE's dates to `refs.PUBLISHED_SPAN`; first real `refs.py ocnele_mari` run; a synthetic known-answer test of the tie and the EGMS swap path; `logs/04-geodesist.md` | To fill in: Matei compares the station table in `logs/04-geodesist.md` with the PDF, pages 3 to 7 |
| Sat 14 Nov 2026, about 15:14 | Darius (06) | Claude Code, Figma Make | Figma Make: the visual design of the page (dark panels, satellite switch, legend, slider, station card). Claude Code: the page itself, `index.html`, `app/main.js` and `app/style.css` (MapLibre map, satellite and view switches, Change, Rate, Zones, Agreement and Coverage views, Compare swipe, timeline with gaps, station and zone cards, URL state, phone layout), and the 06 rows in `CITATIONS.md` and `DECISIONS.md`. A second pass the same afternoon replaced that layout with a minimal light one (one menu, one dock, sheets on demand) after Darius rejected the first. Checked in a browser on `products/mock/` at 1440 × 900 and 375 × 812. | To fill in: Darius checks every view by hand, on two phones (T9) |
| Sat 14 Nov 2026, about 15:46 | Darius (06) | Claude Code | The 06 handoff in docs/ui.md: `export.py` (Sentinel-1 Jul to Oct overlays, series, processing scenarios and coverage; NISAR catalog coverage; pending files for 04 and 05) and the page's real-data mode (NISAR Coverage by default with pending states, Sentinel-1 Change, Rate and Zones, the processing-choices panel, direction and limited-coverage labels, the EGMS empty state, methods and resident notes). Checked: `checkpoint.py ocnele_mari` contract OK, `pytest -q` 8 passed, zone 4 fitted changes −7.52 and −3.51 mm match the handoff, mock flow, desktop and phone in a browser. | To fill in: Darius reviews the page; 03 checks the zone numbers and labels |
| Sat 14 Nov 2026, about 16:16 | Darius (06) | Claude Code | Sentinel-1 shown as dots (`s1/points_<track>.json` from `export.py`, click for the value); zone markers fixed on hover and pan; the Ocnele Mari town boundary from OpenStreetMap; `docs/ui.md` version 3 with an implementation status table, `products/README.md`, and the new `logs/06-app.md` with proposals for other owners. Checked: `checkpoint.py` contract OK on `ocnele_mari` and `mock`, `pytest -q` 8 passed, browser checks at desktop and phone width. | To fill in: Darius reviews the docs; 01 decides on the proposals in `logs/06-app.md` |
| Sat 14 Nov 2026 | 03 analysis and 06 handoff | ChatGPT | Reran both Sentinel-1 tracks with the group-aware solver, compared all zone fits and investigated local LOS reference sensitivity. Added the Git byte-preservation rule and updated the UI guidance. | Compared both baseline grids and all populated summaries against the prior export. Tested the committed SHA-256 with Git CRLF conversion enabled. |
| 14 Nov 2026 | 06 handoff | ChatGPT | Wired the pinned R05 historical EGMS summary into Agreement and kept cell-level products pending. | Matched every median and cell count against the R05 report. |
| Sat 14 Nov 2026, about 15:45 | Matei (04) | Claude Code | EGMS GNSS model reader in `refs.py` (N/E and lat/lon swap, header check, 150 km cut) writing `model_egms.csv`; checked the model's frame in the EGMS GNSS Calibration Report (ETRF2000; ETRF2000 vs ETRF2020 up from Figure 10); a preliminary real model swap on the rehearsal NISAR stack (0.72 and 0.70 mm/yr); rows in `CITATIONS.md` and `docs/data.md`; log entry | Paul's centre values (ve −0.75, vn −1.18, vu −0.80 mm/yr) reproduced exactly. To fill in: Matei checks the Figure 10 reading (about −0.4 mm/yr at the site) |
| Sat 14 Nov 2026, about 16:10 | Matei (04) | Claude Code | Read 05's EGMS stable-ground results (PR #9) and related them to the tie and the frame; the expected reference offset for check 6 (about +0.6 mm/yr); T8 marked PASS WITH NOTE; `STATUS.md`, `DECISIONS.md`, `logs/04-geodesist.md` | To fill in: Matei and Paul agree on T8's status and the check-6 offset |
| 14 Nov 2026 | 03 / 06 forecast prototype | ChatGPT | Built and ran the retrospective Sentinel-1 predictor and wired it to Zones. | Reproduced the export with the branch solver, checked baseline parity, and tested chart gating. |
| 14 Nov 2026 | 03 / 06 forecast | ChatGPT | Extended the LOS scenario to 1 Jan 2027, exported the three model paths, and added a model selector plus environmental-feature notes. | Regenerated the export from the 29 summer interferograms on CPU. |
