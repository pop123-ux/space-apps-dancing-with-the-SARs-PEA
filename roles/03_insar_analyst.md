# 03 · InSAR analyst — Alexandru & Eric

**Mission.** Turn the pairs into displacement over time and a rate per pixel, honestly. Then combine the two looks into vertical and east–west.

**You own:** `stack.py` (stub) → `<track>/ts.npz`, and `split.py` (stub) → `up_east.npz`. You share 02 and 03 with each other; split them as you like.

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| 0–6 | Settle the method (O-05: MintPy or our own inversion). Read the hand-off from 02. As soon as two real pairs exist, look at them. | Method chosen; you can explain every step |
| 6–18 | `stack.py`: first real rate map. Check the sign: the bowls must sink (red) on both tracks. Check the gaps and the pair lengths it prints. | First real rate map, sign checked |
| 18–30 | `split.py` for up/east. Decide with 01 whether to split on the common June–October 2026 window only. Run the closure check if GSLC pairs exist (O-07). *(Former Praid slot, free: O-15.)* | Up/east maps |
| 30–40 | Uncertainty: where is the rate smaller than 2σ? Grey it out with 06. Zone medians for the story. **Freeze at hour 40.** | Zone table with ± |
| 40–48 | Captions, support; no number changes. | — |

## Method in six lines (starting points from the rehearsal; see science-notes)

1. **To millimetres:** `mm = PHASE_SIGN · phase · λ/4π`. The sign is checked (validate.py check 1), not assumed. It is **not confirmed on real data yet**.
2. **Troposphere:** fit one elevation slope per pair against the DEM on stable ground and remove it. Without it, 094D showed −8.6 mm/yr per 100 m. An upgrade worth trying is the GUNW `radarGrid` weather-model cubes.
3. **Reference:** reference each pair to stable ground, outside the zones + 3 km.
4. **Inversion:** small-baseline inversion, pairs → displacement per date. The January–June gap splits 129A into two groups.
5. **Rate:** fit a straight line **through the dates**, with one offset per group, and **no annual term under 1.5 years**.
6. **Uncertainty:** σ assumes independent dates, so report it as a lower bound.

## Watch out

- **The signal is small:** about −25 mm/yr at most (EGMS) against 37–51 mm/yr of per-pixel scatter in the rehearsal. **Work at zone level.**
- **The tracks disagree:** in the rehearsal the zone medians were 129A −4.6 against 094D +27.5 mm/yr. Find out why (atmosphere? unwrapping? sign?) before trusting either.
- **Short-pair bias:** 8-day pairs read 20–40 % high in a Sentinel-1 stack. The Ocnele Mari GUNW stack has **0 closure triplets**.
- **North is ignored** in the split (|n| ≈ 0.1). Say so.
- **The two tracks cover different months.** Combining their rates mixes windows.

## Optional research track: ML/AI (O-08, not decided)

Only if the core is green, and only if the model beats a simple baseline on things nobody tuned: held-out stations, EGMS stable ground and the synthetic truth. Remember that our LSTM once lost to a seasonal model (6.6 against 5.4 mm). Candidates:

- a learned atmospheric correction against the elevation slope;
- detection of bad pairs or unwrapping errors;
- uncertainty calibration.

Log any AI use in `docs/ai-use.md`.

## Decisions you drive or feed

O-05 method · O-07 closure · O-08 ML/AI · O-01 story (what the data can support).

## Questions to answer during the event

- What is the real pixel scatter on stable ground after your corrections (the rehearsal had 37/51)?
- Is the 2025–26 rate in the zones faster or slower than EGMS 2019–2023/2024, and does it beat its error at zone level?
- Do the GUNW pairs give any closure triplets? If not, are GSLC pairs worth the 3–4 h?

## Done when

`ts.npz` and `up_east.npz` exist for Ocnele Mari, the sign check passes or is explained, and every rate shown on the page beats 2σ or is greyed out.
