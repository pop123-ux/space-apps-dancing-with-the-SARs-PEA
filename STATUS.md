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
| 04 Matei | 14 Nov, 17:40: 129A on the team's own stream. First pair verified on the full HDF5 (mask, grid, look vectors target to sensor, LOS sign consistent; phase sign still T3). 13 pairs, two acquisition groups referenced separately, gap 18 Jan to 23 Jun. Real tie: offset −5.80 mm/yr, 347,765 px, scatter 39.2; swap vs EGMS 0.70 mm/yr. `meta.json`, `geom.npz`, `ts.npz`, `cal.npz`, overlays handed to 06; `calib.json` (129A). Next: 094D; T3 with 03/05; frame paragraph. Log: `logs/04-geodesist.md` | [§ 04](docs/build-spec.md#04--geodesist-matei) |
| 05 Paul | EGMS 2020–2025 tile cut (`egms_cut.py`): z3 sinks −18.9 mm/yr, stable ground −0.5 mm/yr. Station screening and the 2026 third-witness search done: no open station within 70 km has 2026 data. T10 done (PASS WITH NOTE). z3 investigated: zone in place, 029A incoherent there, 007D's expected 4 mm is within noise, so 2026 "not detected"; needs the Jan to Oct extension (03). EGMS GNSS model CSV found and passed to 04 for T8. Moisture and rain screen (NISAR SME2, ERA5) for z4 and the control ring: no flags; predeclared 7-day rain fails to beat persistence in the r06 forecast backtest (4.74 against 4.19 mm). OPERA weather-model troposphere: agrees with fit.py's elevation correction on 007D (z4 −2.1 against −2.0 mm); 029A fails the predeclared sign check (z4 range −2.8 to −7.5 mm stays open). Closure vs moisture change (58 HyP3 ZIPs): no link (window ρ 0.19, p 0.42). EGMS stable-ground check done: the tie area sinks −0.6 mm/yr (79 % within ±1.5), small moving patches shift it by only 0.1 mm/yr. Next: monument screening, then check 8 (`docs/validation-log.md`) | [§ 05](docs/build-spec.md#05--validator-paul) |
| 06 Darius | Page merged on `main` (14 Nov, 16:25). Open audit findings for 06 (phone sheet covers the controls, sign convention hidden on phone, Compare mixing time spans, no Pages workflow): see the audit table under Notes. | [§ 06](docs/build-spec.md#06--app-developer-darius) |

## Early tests

The tests are defined in [prompts/early-tests.md](prompts/early-tests.md). Each owner writes the result here: PASS, PASS WITH NOTE, FAIL, PARTIAL or BLOCKED, with the evidence.

| Test | Owner | Result | Evidence |
| --- | --- | --- | --- |
| T0 Environment | everyone | | |
| T1 Venue network | 02 | | |
| T2 Search and mask | 02 | | |
| T3 Phase sign | 03, 05 | | |
| T4 Troposphere | 03 | PASS (15 Nov) | Rate against height on stable ground, NISAR: 094D −14.1 → +0.5 mm/yr per 100 m (r −0.59 → 0.03) with the per-pair height correction; 129A −1.1 → +0.6. Sentinel-1: the ECMWF weather model removes 78 % of 029A's height leakage. NASA's own troposphere screens did not improve 094D. `notebooks/03/t4_troposphere.json`, `docs/data.md` |
| T5 Gap groups (synthetic) | 03 | PASS for the method (15 Nov) | Synthetic stack on the real 129A dates with the January to June gap, one offset per group: noise-free bias 0.0 mm/yr, zones exact. With realistic atmosphere the stable bias stays under 0.7 mm/yr but single-zone rates miss by more than 15 % (zones are a few pixels against about 5 mm of correlated noise per date): zone values are noise-limited, not method-limited. `notebooks/03/t5_t6_synthetic.json` |
| T6 Summer-only bias (synthetic) | 03 | FAIL (15 Nov) | A 5 mm seasonal cycle in the bowls, sampled on 094D's June to October dates and fitted without a seasonal term, shifts the zone rate by 57 % (noise-free). As the rule says, 094D is labelled "summer to autumn only" on the page. A seasonal term on our 0.95-year 129A series works without noise but fails with realistic noise (errors up to 20×), so it stays off. `notebooks/03/t5_t6_synthetic.json` |
| T7 Station hold-out | 05 | | |
| T8 Model swap and EGMS | 04, 05 | PASS WITH NOTE (14 Nov, 16:10) | Swap EuVeM2022 vs EGMS: 0.72 (094D) and 0.70 (129A) mm/yr, under 1 mm/yr (04, on the rehearsal NISAR stack). EGMS stable ground: tie area −0.6 mm/yr, 79 % within ±1.5 mm/yr, moving patches shift it 0.1 mm/yr (05, `docs/validation-log.md`). Rerun on the team's 129A stream (17:40): 0.704 mm/yr, unchanged. Note: 094D still on the rehearsal stack; check 6 is separate. `logs/04-geodesist.md` |
| T9 Phones | 06 | | |
| T10 Sentinel-1 holds up | 05, 03 | PASS WITH NOTE | 14 Nov: sign and spread hold on 029A z1, z2, z4 and 007D z4; not testable on 029A z3 and 007D z1, z2, z3. z4 is the only zone that holds on both tracks. z3 shows no Sentinel-1 signal although EGMS has it sinking −18.9 mm/yr (red flag). Table in `docs/validation-log.md` |

## Notes

- **D-003 (Sat 14 Nov):** the submission is a 7-slide PowerPoint, with no video. Every role supplies one or two slides.
- **D-004 (Sat 14 Nov):** two radars, one switch. NISAR and Sentinel-1 are both fitted, and the page has a satellite switch and five views (`docs/ui.md`).
- **Sentinel-1 covers NISAR's gap.** NASA CMR on 14 Nov 2026 shows Sentinel-1 acquisitions over the town every month from Nov 2025 to Nov 2026, on tracks 029A and 007D. Our current fit uses July to October only. Extending it to January to June 2026 is a Tier 3 option.
- Every file names its owner role in its first lines; the full list is `OWNERS.md`.

- Our copy of the deck says −250 mm/yr on slides 1, 5 and 6. The rehearsal corrects it to about −25 mm/yr. Never quote −250.
- The Space Apps resources page and the 2026 Project Submission Guide returned HTTP 503 from the setup machine on 14 Nov. 01 lists what we use in `CITATIONS.md`.
- The [Cluj-Napoca participant's guide](https://app.notion.com/p/Participant-s-Guide-NASA-Space-Apps-Challenge-Cluj-Napoca-2026-40903dd4dbcc80eab387c2962430efef) (Notion) could not be read from the setup machine. It renders in the browser only, and the Notion connector is not signed in. 01 reads it at hour 0 and copies the kickoff time, the submission deadline and any AI-disclosure wording into `STATUS.md` and `AI-DISCLOSURE.md`.

**15 Nov 10:45 (Sentinel-1 to 10 Nov, 02/03):** six new dates per track processed (24 HyP3 jobs). January to November (55 dates, 107 pairs per track) replaces January to October on the page; July to November (22 dates) added; July to October stays the default. January to October now reproduces from its own products (job list with links in `sentinel1/provenance/`). Zone 4 stays away from the satellite on both tracks in every run over July to November. The 5 Oct forecast held on the six new dates (6 of 6 inside its 80 % range); the forecast is re-issued from 10 Nov: −3.85 mm on 1 Jan 2027, 80 % range −8.49 to +6.17 mm. One 007D date (15 Nov) not fitted yet. [Details](sentinel1/analysis_jan_nov/README.md). **15 Nov 03:00:** Satellite basemap default; EN/RO; table dialog and CSV export; Compare enabled (geometry pairing); NISAR chain rerun with main's stack; 094D tested with NASA's own troposphere screens: still fails T3, now shown flagged; stations: VLC within 2 mm/yr of NISAR 129A, HORE compared, VLC1+VLC2 mean added; checks 5 pass, 10 warn, 4 fail, 5 info; update.py and a weekly data check. **14 Nov 23:30:** NISAR 129A is on the page (passes T3 at −10.1 mm/yr and T8); 094D held as "under review" (unwrapping ruled out; a valley-wide signal, not proven either way); Compare and Agreement stay off. Chronos-2 is the only forecast, with a date slider and an out-of-sample NISAR check (−5.9 against +1.2 mm over 9 to 21 Oct; within NISAR's 6.9 mm noise). Page layout v4 merged. [NISAR](docs/data.md#our-own-nisar-fit-14-nov-2026-2330) · [forecast](docs/forecast.md#chronos-2-is-the-only-forecast-slider-nisar-check-14-nov-2026-2330). **14 Nov 22:30 (NISAR, 02/03):** all 22 pairs streamed (729 MB, windows only) and stacked by our own `fetch.py`/`stack.py`; tied by `calibrate.py` (129A plane −7.78 mm/yr, scatter 28.2; 094D −15.15, scatter 48.4; EGMS swap 0.74/0.70 mm/yr). **T3 NOT PASSED:** zone-median LOS rate 129A −10.1 mm/yr (passes) but 094D +23.5 mm/yr (fails; the rehearsal also had +27.5). The sign is not a global flip: NISAR rate maps correlate positively with Sentinel-1 on both tracks (r 0.39 and 0.32). Per the rules the sign is unchanged and NISAR is not yet on the page; next checks are unwrapping and atmosphere on 094D (`notebooks/03/t3_phase_sign.json`). **14 Nov 21:00:** Matei's first 129A pair (23 Jun to 5 Jul) checked independently from the shared file: every number in his report reproduces (88 % kept, look vector, incidence 41.07°, ionosphere σ 1.83 rad); it is a Level 2 GUNW, PROVISIONAL. Branches `r04/129a-series` and `r05/egms-and-witnesses` (PR #9) merged; no branch holds unmerged work. [Details](docs/data.md#04s-first-129a-pair-checked-independently-14-nov-2026-2100). **14 Nov 20:30:** Chronos-2 is the default January model (team decision): −3.87 mm LOS by 1 Jan 2027, 80 % interval −11.27 to +15.17 mm. Weather covariates (ERA5 rain, ERA5-Land soil moisture) were tested under a predeclared rule and not adopted: they did not lower the error. [Details](docs/forecast.md#chronos-2-is-the-default-weather-covariates-tested-14-nov-2026-2030). **14 Nov 19:30:** January to October Sentinel-1 fit committed (`sentinel1/analysis_jan_oct/`, grids in `assets_jan_oct/`); weather-model troposphere scenario added (removes 78 % of the elevation leakage on 029A; zone 4 029A −30.5 → −23.6 mm/yr); Chronos-2 integrated zero-shot on CPU (best MAE on every long backtest, 88-day 3.81 mm against 4.29 persistence; calibrated 80 % interval). Default January model awaits a team decision. [Details](docs/forecast.md#troposphere-the-january-to-october-fit-and-chronos-2-14-nov-2026-1930). **14 Nov 18:30 (verifier):** the forecast reproduces exactly from the raw data on CPU; a long-term trend model anchored on EGMS 2020–2025 (−5.5 mm/yr LOS, 1 Jan endpoint −9.21 mm) was added because the summer slope (−30.5 mm/yr) is about 5.5 times the long-term rate; Paul's rain test, re-inverted per cutoff, still shows no improvement (MAE 4.80 against persistence 4.19). Details and next steps: [forecast handoff](docs/forecast.md#verification-and-the-january-anchor-14-nov-2026-1830). The 1 January Zone 4 LOS scenario is connected in the frontend. See the [forecast handoff](docs/forecast.md) for its evaluation limits and next checks.

### App audit, 14 Nov 2026, 20:00 (03 verifier, Claude Code; main at 5304f94)

Checked with `pytest -q` (11 passed), `checkpoint.py` (contract OK on both sites), and Playwright on desktop 1280×900 and iPhone 13 (no JS errors, no failed requests). All 45 zone and scenario numbers on the page match `sentinel1/analysis/summary.json` exactly. Fixed in this PR: forecast MAE shown with "+", raw floats in "Show as table", hard-coded "Zone 4" and "029A", "undefined" for unknown model labels, clipped model buttons (they now wrap), and the Chronos-2 80 % interval is stated at the endpoint. Open, by owner:

| Priority | Finding | Owner |
| --- | --- | --- |
| High | Phone: the Coverage sheet (z-index 25, 72 % tall) opens by default and covers the dock and the satellite menu, so clicks on views, tracks and "Sentinel-1" are intercepted (`app/style.css:282`) | 06 |
| High | Phone: the sign convention is hidden (legend caps hidden at `style.css:268`, status line cut by an ellipsis); breaks honest-comparison rule 5 | 06 |
| High | Compare can mix time spans: NISAR "since 2025-11-07" next to Sentinel-1 "since 2026-07-07" on mock; snap the date into `common_window` and start Compare frames there (`main.js` `pickSat`, `export.py`); breaks rule 1 | 06 |
| High | No Pages workflow, no `slides/`, no `SUBMISSION.md` yet | 06, 01 |
| Medium | `docs/build-spec.md` file contracts lag the export (`coverage.json`, `sensitivity.json`, `forecast.json`, `s1/points_*.json`, several manifest keys; `series.json` lacks `up`); `checkpoint.py` checks none of the sidecars | 01, 06 |
| Medium | `manifest.json` still has `story: "TODO(01)…"` | 01 |
| Medium | The sheet is `aria-live="polite"` and re-renders on every slider step, so screen readers re-read it during Play (`index.html:68`) | 06 |
| Medium | PR #9 (05, `r05/egms-and-witnesses`) is not merged, but main cites its EGMS commit and the forecast uses its `z4_screen_inputs.csv` | 05, 01 |
| Medium | Mock site 404s on `coverage.json`, `sensitivity.json`, `forecast.json` (`mock_products.py`) | 06 |
| Low | Stale text: `CLAUDE.md` "no page yet"; this file's header ("skeleton", 14:30, hour 0 blank) and its "r06/page not merged" line; `docs/ui.md` says the page is on `r06/page`; the build-spec change log is empty though MapLibre, the satellite menu, Coverage as default and the forecast default all moved | 01, 06 |
| Low | Checks pill hidden on phone; EGMS table uses "-" not "−"; `#site=` ignored without reload; `#sat=compare` falls back silently; About gives NISAR a EuVeM2022 tie though no NISAR measurement exists | 06 |
| Low | Merged branches that could be deleted: `r03/z3-coverage-and-windows`, `r04/egms-model`, `r04/refs`, `r04/station-check`, `r06/page`, `r06/zone-1-2` | owners |

