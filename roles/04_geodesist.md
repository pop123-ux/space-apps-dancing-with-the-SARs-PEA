# 04 · Geodesist — Matei

**Mission.** Put the radar's relative rates into a real reference frame using open references only, the way EGMS does it. Keep the stations out of it, so the validator can test you.

**You own:** `refs.py` (stub) → `data/work/<site>/refs/`, and `calibrate.py` (stub) → `<track>/cal.npz` and `products/<site>/calib.json`.

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| 0–6 | `refs.py`: EuVeM2022 Romania grid, NGL MIDAS Eurasia-fixed, published rates. Read the EuVeM2022 and NGL MIDAS READMEs. **Fill the NaN verticals in `common.PUBLISHED`** (VLC2, HORE) from Muntean et al. 2026 Table S3, by eye: the PDF table does not extract cleanly. `synthetic()` for the known-answer test. | Station table complete |
| 6–18 | `calibrate.py`: model → LOS, the tie mask, offset or plane. Plot NISAR − model on the tie pixels. | First tie |
| 18–30 | Second model: the EGMS GNSS model as `model_egms.csv` (O-06). The difference between the two ties is the model's share of the error. EGMS stable-ground cross-check with 05. | Model swap number in `calib.json` |
| 30–40 | Final tie. Write the frame paragraph for the write-up. **Freeze at hour 40.** | Paragraph written |
| 40–48 | Captions, support; no number changes. | — |

## The frame, in one paragraph

All rates are **Eurasia-fixed**: EuVeM2022 (horizontals ETRF2000, up IGS14), NGL MIDAS `midas.EU.txt` (IGS14-based) and Muntean et al. 2026 (Eurasia-fixed). NISAR measures relative to its orbits. Plate motion is nearly uniform across a 50 km window, so it goes into the tie's offset. Mixing frames between the model and the stations would not cancel, though: 25 mm/yr of plate motion can show up as about 10 mm/yr in a line of sight. Hence one frame for everything.

## The tie (DRAFT, from the rehearsal)

- **What is fitted:** `NISAR − model` on pixels with coherence ≥ 0.4, outside the salt zones + 3 km, and more than 1 km from any station.
- **The fit:** one offset, or a plane if that cuts the scatter by more than 10 %, with 3σ outliers removed twice.
- **What the model can do:** it is a 0.1° grid. It fixes the frame-wide level and slopes only, and **cannot** say anything about a 2 km salt bowl.
- **Rehearsal numbers:** offsets −8.8 (094D) and −6.0 (129A) mm/yr; robust scatter 51 and 37 mm/yr; the model's own share only +0.25 and −0.62 mm/yr.

## Watch out

- **The references are old.** EuVeM2022 data run to 2021, and NGL MIDAS for the stations near the town to 2018–2020. They assume steady motion into 2025–2026: fine for tectonics at the 1 mm/yr level, not for a station on a moving building.
- **A plane hints at residual ionosphere.** Compare runs with and without the ionosphere layer (ask 02).
- **No ROMPOS data.** Don't ask for it, and put nothing derived from it in the repository.
- **Cite Muntean et al. 2026; don't copy the table** (O-13).

## Decisions you drive or feed

O-06 second model · O-11 window size (with 02).

## Questions to answer during the event

- Is a plane needed on either track?
- How big is the offset per track, and does it make sense given the model's LOS value?
- What is VLC2's published vertical rate (Table S3)?
- Where is the EGMS GNSS model CSV download?

## Done when

`calib.json` holds the tie per track and the model-swap number, and the frame paragraph is written.
