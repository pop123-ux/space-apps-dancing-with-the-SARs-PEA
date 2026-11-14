# Early tests: Claude Code prompt

## How to use this

These tests check the plan in `docs/build-spec.md` against the real data in the first hours of the event, before the team leans on it. Each test has one owner. The owner's Claude Code session runs it when they say **"Read prompts/early-tests.md and run T<n>."**

Every result goes in the "Early tests" table in `STATUS.md`: PASS, PASS WITH NOTE, FAIL, PARTIAL or BLOCKED, with evidence (file paths, numbers with units, command output). A test that fails clearly, with the reason written down, is a good result. A test that passes because the method was quietly changed is a bad one.

---

## Ground rules

1. **Don't tune.** The cuts, thresholds, windows and checks in `docs/build-spec.md` stay as written. Where the spec leaves a value to be read from the files (dataset paths, mask bits, dates), read it and record it.
2. **Don't fix a result.** Never flip the phase sign, drop pairs or move a zone to make a check pass. Describe what you see instead.
3. **Timeboxes are real.** At the timebox, write down where the test stands, mark it PARTIAL or BLOCKED, and move on.
4. **Data stay local,** in `data/work/` (git-ignored). Figures for the team go in `docs/figures/` as PNGs under 1 MB each.
5. **Proposals, not edits.** If a test shows a spec value is wrong, write a proposal in `DECISIONS.md` (`HH:MM | role | proposal | evidence`). 01 takes it to the team.

## T0. Environment (everyone; timebox 30 min)

`prompts/setup.md` has run. Check that `pytest -q` passes, the role's script answers `--help`, and (02 to 05) `.env` holds a token. Record the Python version.

## T1. Venue network (02; timebox 30 min; at hour 0)

Stream one 129A pair's window with `fetch.py` (or a minimal range-read script, if `read_pair()` isn't ready yet). Record MB, seconds and the number of workers. **Passes** if one pair takes under 1 min and a track under 10 min. **If not:** the hour-6 cut line, which is to download one track in full.

## T2. Search and mask (02; timebox 1 h)

- `python fetch.py ocnele_mari --list` must list the same 22 pairs as `data/scenes/ocnele_mari_gunw.csv` (track, dates, collection).
- On the first pair, record the dataset paths, the mask dtype, the share of pixels kept by the mask rule (the rehearsal kept 85 to 94 % after the series step), whether `ionospherePhaseScreen` is filled, and the share of bit 24.
- **Passes** if the list matches and most of the window survives. **If not:** recheck the bit decode (`mk & 0xFF`) before anything else.

## T3. Phase sign (03 with 05; timebox 1 h; on the first rate map)

Take the zone-median LOS rate on 129A, and on 094D once it exists. **Passes** if both are below −2 mm/yr. The rehearsal had −4.6 on 129A and +27.5 mm/yr on 094D. **If not:** check sign, unwrapping (connected components) and atmosphere in that order, and write what you find. The sign stays as the spec says until the team decides.

## T4. Troposphere (03; timebox 1 h)

Compare the rate against elevation on stable ground, with and without the per-pair elevation slope. Record the slope (mm/yr per 100 m) and r, and NISAR up − EGMS up on stable ground if 05's EGMS file exists. The rehearsal went from −8.6 mm/yr per 100 m, and +34 mm/yr against EGMS, to +6.4 mm/yr after the slope. **Passes** if the slope removes the elevation dependence. **If not:** weather-model cubes become a Tier 3 item, stated on the page.

## T5. Gap groups (03; synthetic; timebox 45 min)

On the synthetic stack, with the real date pattern including 18 Jan to 23 Jun 2026, the rate with one offset per group must recover the truth. **Passes** with bias under 1 mm/yr and zones within 15 %. **If not:** fit each window separately and say so.

## T6. Summer-only bias (03; synthetic; timebox 45 min)

Add a 5 mm annual term to the synthetic truth, sample it on 094D's real dates (June to October only), and fit without an annual term. **Passes** if the rate error in the zones is under 20 %. **If not:** label 094D "summer to autumn only" wherever its rate appears.

## T7. Station hold-out (05; timebox 30 min; after the first tie)

Rerun the tie with `STATION_HOLDOUT_M = 0` on a scratch copy, without committing. Record how station agreement changes. If agreement improves slightly, that proves the hold-out mattered. Either way, report it.

## T8. Model swap and EGMS stable ground (04 with 05; timebox 1 h)

Tie with EuVeM2022, then with the second model (O-06), or a rigid plate if its CSV is still missing. Record the change in LOS rate on the tie pixels. **Passes** if it is under 1 mm/yr. Record NISAR up − EGMS up on stable ground, with its median and scatter, for claim A.

## T9. Phones (06; timebox 30 min; once the page is on Pages)

Open the Pages link on two phones. **Passes** if the map opens on the town (D-002), the slider plays with the gap labelled, the text is readable, and the synthetic banner shows on `mock`. **If not:** collapse to the map, the slider and one card.

## T10. HyP3 queue (05; check every 2 h after the order)

Record the job count, status and time in queue. **Passes** if the products are back by about hour 8. **If not:** Sentinel-1 moves to Tier 3.
