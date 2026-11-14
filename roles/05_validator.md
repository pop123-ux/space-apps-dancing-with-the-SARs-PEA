# 05 · Validator — Paul

**Mission.** Prove or disprove the numbers with things the team never tuned. You are the team's own red team: nobody else edits `validate.py`, and you never edit the science scripts.

**You own:** `validate.py` (stub) → `products/<site>/checks.json`, `checks.md` and `stations.geojson`; `hyp3_order.py` (stub); and [docs/validation-log.md](../docs/validation-log.md).

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| **0–1** | **Order Sentinel-1 on HyP3 now: it queues for hours.** Pairs over Ocnele Mari for Nov 2025 – Jan 2026 and Jun – Oct 2026, both geometries, short and longer pairs (`hyp3_order.py`, or by hand first). Log the jobs. | Jobs submitted and logged |
| 1–6 | EGMS: download the L3 Ortho **Up** tile (2020–2024) from egms.land.copernicus.eu (free login) and write `data/work/ocnele_mari/refs/egms_up.csv` (lon, lat, v). **Screen the stations:** roof, mast or pillar? What does EGMS show on the station's own building? | Screening table in the validation log |
| 6–18 | Sentinel-1 rate over the bowl for the same months, against NISAR's. | Second-radar number |
| 18–30 | `validate.py`, then chase every warning: why does a station disagree? | Every WARN explained |
| 30–40 | Final agree flags. Red-team the map with the advisor at hour 40. | `checks.md` final |
| 40–48 | **Re-run every check on the frozen build** and log it. | Re-run logged |

## The checks (DRAFT thresholds; yours to own)

| # | Check | Pass when |
|---|---|---|
| 1 | Salt zones sink, every track | median LOS rate in the zones < −2 mm/yr (otherwise the phase sign is wrong) |
| 2 | Held-out stations, each LOS | \|NISAR − GNSS\| ≤ max(2 mm/yr, 2σ combined) |
| 3 | Model tie scatter | robust scatter < 6 mm/yr per pixel |
| 4 | Closure: 12 + 12 against 24-day pairs | ratio 0.8–1.2 (Ocnele Mari GUNW: 0 triplets → info) |
| 5 | Gaps in the chain | none, or listed (129A: 18 Jan → 23 Jun 2026) |
| 6 | EGMS Ortho, stable ground | median difference < 1.5 mm/yr; the bowl then and now is reported, not judged |
| 7 | Synthetic truth (demo only) | bias < 1 mm/yr, zones within 15 %; a planted lying station must be caught |
| 8 | Sentinel-1, same months | same zone rate within the errors |

## Starting points (rehearsal results to beat)

| Check | Rehearsal result |
|---|---|
| Sign | ✔ on 129A (−4.6), ✘ on 094D (+27.5 mm/yr) |
| Tie scatter | 37 / 51 mm/yr (WARN) |
| EGMS stable ground | +6.4 mm/yr median, 27 scatter (WARN) |
| Stations VLC1 / HORE | "agree" only because the tolerance is huge (35–60 mm/yr). **Say so.** |

## Watch out

- **Stations can lie.** HAR1's rooftop mast swings about 38 mm a year and frost-jacks up to 5.5 cm. Before calling NISAR wrong, look at EGMS on the station's own building.
- **Old station rates** (series ending 2018–2020) assume steady motion since. Say so in the pin popup.
- **EGMS covers 2019/2020–2024; NISAR covers 2025–2026.** On stable ground they must agree. In the bowl, a difference is the story, not an error.
- **The HyP3 monthly credit limit** is per Earthdata account. Plan the orders.

## Decisions you drive or feed

O-07 closure (whether "untested" is acceptable) · O-12 HAR1 in the app.

## Questions to answer during the event

- How many stations fall inside the window, and how many have all three components?
- Over the bowl in the same months, does Sentinel-1 give the same rate as NISAR within the errors?
- Do the 2019–2023 and 2020–2024 EGMS tiles differ on stable ground?

## Done when

Every check has a status and a sentence, every WARN or FAIL is explained, and the frozen-build re-run is logged.
