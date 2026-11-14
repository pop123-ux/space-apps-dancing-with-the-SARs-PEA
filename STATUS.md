# Status

**Owner:** 01 · Lead and story (Mario); every role updates its own row

Updated Sat 14 Nov 2026, 14:30 Europe/Bucharest. Event: NASA Space Apps Cluj-Napoca, ClujHUB, 14 to 15 Nov 2026, so `EVENT_TZ=Europe/Bucharest`.

**Hour 0:** `____` (01 fills this in, O-04). **Submission deadline:** `____` (01, from the 13 Nov guide).

**Phase:** skeleton on `main`. The hour-2 review has not happened yet.

## Done, with evidence

- **Skeleton on `main`.** The plan, rules, stubs and tools are in [pop123-ux/space-apps-dancing-with-the-SARs-PEA#1](https://github.com/pop123-ux/space-apps-dancing-with-the-SARs-PEA/pull/1), the documents were restructured in [pop123-ux/space-apps-dancing-with-the-SARs-PEA#2](https://github.com/pop123-ux/space-apps-dancing-with-the-SARs-PEA/pull/2), and `docs/schedule.md` (hour by hour, per role) and `AI-DISCLOSURE.md` were added after it.
- **Smoke test.** `pytest -q` passes: every script answers `--help`, the mock products pass `checkpoint.py`, and nothing under `data/work/` is tracked.
- **NISAR inventory.** NASA CMR on 14 Nov 2026, 10:40 UTC: 22 GUNW pairs over the town, written to `data/scenes/ocnele_mari_gunw.csv`.
  - 129A has 13 pairs: 4 BETA and 9 PROVISIONAL, from 7 Nov 2025 to 21 Oct 2026, with nothing between 18 Jan and 23 Jun 2026.
  - 094D has 9 pairs, all PROVISIONAL, from 20 Jun to 18 Oct 2026.
- **Sentinel-1 fitted** (02/03, Sat 14 Nov 13:37, `sentinel1/`). 58 HyP3 burst pairs, all succeeded. Tracks 029A (7 Jul to 5 Oct 2026) and 007D (6 Jul to 4 Oct), 16 dates each. 40 m grids, zone histories and sensitivity runs; see `sentinel1/docs/TEAM_HANDOFF.md`.
- **Sentinel-1 extension and UI handoff.** All 132 added HyP3 jobs succeeded. The combined January–October fit uses 190 pairs in total, 95 pairs and 49 dates per track. Its outputs are not in the repository yet (only in a ChatGPT-hosted ZIP); see the verifier note in DECISIONS.md. Extended Zone 4 ascending changes sign under alternate processing, and no full-window descending salt-zone series is supported. See [the 06 implementation handoff](docs/ui.md#06-implementation-handoff--14-november-2026) for the verified data and pending NISAR/EGMS states.
- **Mock products, both radars (D-004).** `python mock_products.py` writes `products/mock/`: NISAR and Sentinel-1, 8 layers, 57 frames, 7 series points including the outer reference band, 2 stations, all invented. It runs in about 5 s, and `checkpoint.py mock` reports "contract OK".

## Waiting on a person

- **01:** the 7-slide outline with one owner per slide (D-003, see `docs/overview.md`); hour 0 and `EVENT_TZ` (O-04); read the 13 Nov guide aloud (O-02); O-03 (adopt or rebuild); the hour-2 review of the proposed decisions in `docs/build-spec.md`.
- **05:** the Sentinel-1 jobs are done (02/03). Start the EGMS 2020 to 2025 tile E54N25, and review the Sentinel-1 sensitivity runs (T10).
- **03 and 04:** O-19, the shared quantity for Compare and Agreement (`docs/build-spec.md`).
- **06:** the satellite switch and views (`docs/ui.md`) on `products/mock/`.
- **Everyone:** an Earthdata login, and `prompts/setup.md` run on their laptop.
- **Repo owner:** set the Drive copy of the rehearsal kit back to Restricted, if it isn't already.

## Next, per role

The full plan, hour by hour, is [docs/schedule.md](docs/schedule.md).

| Role | Next step | Section |
| --- | --- | --- |
| 01 Mario | Hour 0, the guide, the hour-2 review, the contract freeze | [build-spec.md § 01](docs/build-spec.md#01--lead-and-story-mario) |
| 02 Alexandru and Eric | Token; T1 (venue network); T2 (`fetch.py --list` gives 22 pairs) | [§ 02](docs/build-spec.md#02--nisar-data-alexandru-and-eric) |
| 03 Alexandru and Eric | O-05 (method); read 02's hand-off | [§ 03](docs/build-spec.md#03--insar-analyst-alexandru-and-eric) |
| 04 Matei | 14 Nov, 16:10: T8 PASS WITH NOTE (swap 0.72 / 0.70 mm/yr; 05's EGMS stable ground −0.6 mm/yr). EGMS GNSS model (A-EPND 2023, ETRF2000) in `refs.py`. Told 05 to expect NISAR − EGMS of about +0.6 mm/yr from the references alone in check 6. Next: rerun the tie and swap on 03's `ts.npz`; frame paragraph. Log: `logs/04-geodesist.md` | [§ 04](docs/build-spec.md#04--geodesist-matei) |
| 05 Paul | Zone 4 and control-ring moisture/rainfall screening in progress. Use the [forecast handoff](docs/forecast.md#paul--05-handoff) for the model and inputs. | [§ 05](docs/build-spec.md#05--validator-paul) |
| 06 Darius | Page pushed on `r06/page` (14 Nov, 16:16; not merged): NISAR Coverage by default, Sentinel-1 Jul to Oct as dots with Zones, processing choices and the town boundary; mock still works. `checkpoint.py ocnele_mari` contract OK, `pytest -q` 8 passed. Log and proposals for 01: [logs/06-app.md](logs/06-app.md). Next: Pages deploy, T9 on two phones, the Jan to Oct window when 03 commits it | [§ 06](docs/build-spec.md#06--app-developer-darius) |

## Early tests

The tests are defined in [prompts/early-tests.md](prompts/early-tests.md). Each owner writes the result here: PASS, PASS WITH NOTE, FAIL, PARTIAL or BLOCKED, with the evidence.

| Test | Owner | Result | Evidence |
| --- | --- | --- | --- |
| T0 Environment | everyone | | |
| T1 Venue network | 02 | | |
| T2 Search and mask | 02 | | |
| T3 Phase sign | 03, 05 | | |
| T4 Troposphere | 03 | | |
| T5 Gap groups (synthetic) | 03 | | |
| T6 Summer-only bias (synthetic) | 03 | | |
| T7 Station hold-out | 05 | | |
| T8 Model swap and EGMS | 04, 05 | PASS WITH NOTE (14 Nov, 16:10) | Swap EuVeM2022 vs EGMS: 0.72 (094D) and 0.70 (129A) mm/yr, under 1 mm/yr (04, on the rehearsal NISAR stack). EGMS stable ground: tie area −0.6 mm/yr, 79 % within ±1.5 mm/yr, moving patches shift it 0.1 mm/yr (05, `docs/validation-log.md`). Note: rerun the swap on 03's stack; check 6 is separate. `logs/04-geodesist.md` |
| T9 Phones | 06 | | |
| T10 Sentinel-1 holds up | 05, 03 | | |

## Notes

- **D-003 (Sat 14 Nov):** the submission is a 7-slide PowerPoint, with no video. Every role supplies one or two slides.
- **D-004 (Sat 14 Nov):** two radars, one switch. NISAR and Sentinel-1 are both fitted, and the page has a satellite switch and five views (`docs/ui.md`).
- **Sentinel-1 covers NISAR's gap.** NASA CMR on 14 Nov 2026 shows Sentinel-1 acquisitions over the town every month from Nov 2025 to Nov 2026, on tracks 029A and 007D. Our current fit uses July to October only. Extending it to January to June 2026 is a Tier 3 option.
- Every file names its owner role in its first lines; the full list is `OWNERS.md`.

- Our copy of the deck says −250 mm/yr on slides 1, 5 and 6. The rehearsal corrects it to about −25 mm/yr. Never quote −250.
- The Space Apps resources page and the 2026 Project Submission Guide returned HTTP 503 from the setup machine on 14 Nov. 01 lists what we use in `CITATIONS.md`.
- The [Cluj-Napoca participant's guide](https://app.notion.com/p/Participant-s-Guide-NASA-Space-Apps-Challenge-Cluj-Napoca-2026-40903dd4dbcc80eab387c2962430efef) (Notion) could not be read from the setup machine. It renders in the browser only, and the Notion connector is not signed in. 01 reads it at hour 0 and copies the kickoff time, the submission deadline and any AI-disclosure wording into `STATUS.md` and `AI-DISCLOSURE.md`.

The 1 January Zone 4 LOS scenario is connected in the frontend branch. See the [forecast handoff](docs/forecast.md) for its evaluation limits and next checks.
