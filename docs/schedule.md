# Schedule: who does what, hour by hour

**Owner:** 01 · Lead and story (Mario); each role checks its own column

Version 1, Sat 14 Nov 2026. The event is NASA Space Apps Cluj-Napoca, at ClujHUB, 14 to 15 Nov 2026 ([Romania Insider](https://www.romania-insider.com/nasa-space-apps-challenge-registrations-romania-2026)). The exact kickoff and submission times come from the Cluj-Napoca participant's guide (Notion), which 01 reads at hour 0 and copies into `STATUS.md`.

**Hours count from hour 0, the kickoff.** Local time = hour 0 + N, in `Europe/Bucharest`.

This plan is **proposed**. Each owner adjusts their own column, and 01 approves it at the hour-2 review. What each step means in detail, with files and fixed numbers, is in your role's section of [build-spec.md](build-spec.md). Gates and cut lines (in **bold** rows) apply to everyone.

| Hours | 01 Lead (Mario) | 02 NISAR data (Alexandru, Eric) | 03 InSAR (Alexandru, Eric) | 04 Geodesist (Matei) | 05 Validator (Paul) | 06 App (Darius) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 to 1 | Set hour 0, deadline and `EVENT_TZ` in `STATUS.md`. Read the participant's guide and the 13 Nov submission guide aloud (O-02). Everyone runs `prompts/setup.md` | Earthdata token; **T1** venue network | O-05 method proposal; read the GUNW notes in `docs/data.md` | Start `refs.py` downloads (EuVeM2022, NGL MIDAS) | EGMS 2020 to 2025 tile E54N25 (Sentinel-1 jobs already done by 02/03) | `python mock_products.py` (both radars); page shell on `products/mock/` |
| 1 to 2 | O-03 (adopt the kit or rebuild); prepare the hour-2 review | `search()`; **T2** (22 pairs, mask) | Prepare `stack.py` against 02's hand-off | Muntean Table S3 verticals for VLC2 and HORE | EGMS L3 Up tile download | D-002 view (map opens on the town); contract review with 01 |
| **2** | **Gate: the hour-2 review, everyone.** Proposed decisions and file contracts frozen (O-10); story framing (O-01) | | | | | |
| 2 to 6 | Story stops, one sentence each; the 7-slide outline with one owner per slide (D-003); reassign the freed Praid slots (O-15) | `read_pair()`: mask, ionosphere, largest component. Both tracks streamed, QA line per pair; one pair shown to the team | `stack.py`: troposphere slope, stable-ground reference, inversion on the first pairs | `refs.py` done; synthetic stand-ins with one lying station | `refs/egms_up.csv`; station screening table | GitHub Pages live with the mock site; basemap and Romania blur (O-09) |
| **6** | **Cut line:** streaming not working → download one track in full | | | | | |
| 6 to 12 | Watch the gates; collect `STATUS.md` rows; slides 1 and 2 draft | `write_dem()`; `synthetic()` known-answer stack; QA table | First real rate map (129A); **T3** sign with 05; **T4** troposphere; **T5** gap groups | `calibrate.py` on the first `ts.npz`: tie mask, offset or plane | **T10** Sentinel-1 sensitivity review; **T3** with 03; `validate.py` checks 1 and 2 | **Satellite switch and view switch** (D-004, `docs/ui.md`); slider with the honest gap; legend; units; labels |
| **12** | **Checkpoint 1:** `python checkpoint.py ocnele_mari`; every WARN and FAIL gets an owner and a verdict; the advisor red-teams | | | | | |
| 12 to 18 | Story text, first version | Freed slot (O-15): help 03; O-14 question to the ASF forum | Zone medians with bootstrap intervals; zone names with 01; **T6** | First tie; plot NISAR − model; `calib.json` | Check 8: NISAR against Sentinel-1 per zone, common window | `export.py`: Sentinel-1 first (`sentinel1/analysis/`), then NISAR |
| **14** | **Cut line:** time series not working → cumulative sum of the 12-day pairs, labelled as such | | | | | |
| 18 to 24 | Collect slide content from each owner; screenshots from the mock or demo site, banner visible | GSLC pairs, if O-07 keeps closure (Tier 3) | `split.py` on the common window (20 Jun to 21 Oct 2026) | Model swap with the EGMS GNSS model (O-06); **T8** with 05 | `validate.py` checks 1 to 8; explain every WARN; **T7** | Real site loads; Compare (swipe); Agreement and Coverage views; station pins |
| **20** | **Cut line:** tie not working → one constant per track on EGMS stable ground; say so | | | | | |
| **24** | **Checkpoint 2:** Tier 1 numbers exist; the advisor red-teams | | | | | |
| 24 to 30 | `SUBMISSION.md` skeleton; local human context (Q6); slides first full draft | Frame sizes with 06; **slide 3** content (the data) | Grey out \|rate\| < 2σ with 06; error maps; **slides 4 and 6** content (rates, what NISAR can and cannot see) | EGMS stable-ground cross-check with 05; **slide 4** content (the frame) | Agree flags, first version; **slide 6** content (the checks) | Story mode; phone layout; keyboard; colour-blind check; **T9**; **slide 5** screenshots |
| 30 to 36 | Write-up; credits; `AI-DISCLOSURE.md` summary; prior work; **slide 7** | Review slides 3 and 4 | Zone table final | Frame paragraph for the page | Red-team the map and the slides | Accessibility; slide 5 from the real site |
| **36** | **Cut line:** interactive page not working → static story map plus screenshots on the slides | | | | | |
| 36 to 40 | Final story text; slides ready except the frozen numbers | Support | Final numbers check | Final tie | Pre-freeze run of every check | Demo link into `SUBMISSION.md` |
| **40** | **Freeze:** no number changes after this. The advisor red-teams | | | | | |
| 40 to 45 | Final slides with the frozen numbers; project page fields | Check slide 3 against the frozen build | Check slides 4 and 6 | Check slide 4 | **Rerun every check on the frozen build** and log it | Polish (no numbers) |
| **45** | **Submit**, at least 3 h before the deadline (a person clicks) | | | | | |
| 45 to 48 | Open every link in a private window; buffer | | | | | |

**Sleep in shifts.** Nobody codes 48 hours straight. 02 and 03 are the same two people, so Alexandru and Eric alternate: one stays on the running jobs while the other sleeps. Each other role picks a 4 to 6 h block between checkpoints 1 and 2 and writes it in `STATUS.md`, so nobody is surprised.

**If a gate slips by more than an hour,** 01 cuts from the top of the ladder in [overview.md](overview.md#the-48-hours):

1. Tier 3.
2. Story-mode polish.
3. The model swap.
4. Compare's swipe and the Agreement view (keep the switch).
5. Up and east.

Never cut the sign check, the honest pins, the satellite switch, the gap label, the slides or the submission text.
