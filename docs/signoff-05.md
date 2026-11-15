# Validator sign-off (05, Paul)

**Owner:** 05 · Validator (Paul)

One page for 01 and 06: which claims the page and slides may make, which need a caveat, and which to drop. Sources are `products/ocnele_mari/checks.md` (written by `validate.py`) and `docs/validation-log.md`. Rule: no claim larger than its noise. Written 15 Nov 2026, before the 2:30 freeze.

## Keep (signed off)

| Claim | Evidence | Say it like this |
|---|---|---|
| The salt zones sink on NISAR 129A | Check 1 pass: −11.3 mm/yr median over 130 zone pixels; against ground at the same height, all four zones sink (−5.7 to −18.6 mm/yr) | "NISAR's ascending track sees the salt zones sinking relative to the ground around them." |
| The bowl (Ocnița · Goruniș, z3) sank about 19 mm a year in 2020 to 2025 | EGMS Ortho Up, 6 cells, −18.9 mm/yr median, −89 mm total; zone position checked (fast cells 214 m from the centre) | "Europe's ground-motion service shows this spot sinking about 2 cm a year from 2020 to 2025." |
| The ground around the town is stable | EGMS tie area: 27,478 cells, median −0.6 mm/yr, 79 % within ±1.5 mm/yr | "The surrounding ground barely moves, so the zones stand out against it." |
| The GNSS model choice does not matter | T8 model swap 0.70 mm/yr (< 1) on both NISAR tracks | Not needed on the page; Q&A only. |
| Slătioarele (z4) moves away from the satellite on Sentinel-1, both tracks | T10: passes on 029A and 007D; on 007D, the weather model (OPERA) and the elevation correction agree within 0.1 mm (about −2 mm over 90 days, −4.4 mm relative to the control ring) | "Both Sentinel-1 tracks agree on Slătioarele." |
| Rain and soil moisture do not explain the z4 signal | Predeclared screen: no flag on either track; rain does not beat persistence in the forecast (4.74 against 4.19 mm); closure does not follow moisture (ρ +0.19, p 0.42) | "We checked rain and soil moisture; they don't explain it." |

## Keep with a caveat (the caveat must be on the page or in the notes)

| Claim | Caveat |
|---|---|
| NISAR and Sentinel-1 agree on the zones (129A with 007D) | All four are **warn**, not pass: both show sinking, but the 2σ tolerance is 46 to 57 mm/yr, so agreeing is not proof. Say "point the same way", never "confirm". |
| Per-pixel dots on the map | Tie scatter is 39 mm/yr per pixel on 129A (target < 6). Read zones and areas, not single dots. The info button should say so. |
| Any 2026 rate for z3 (the bowl) | Sentinel-1 can't confirm 2026 there: 029A has no coherent pixels, and on 007D the expected 4 mm is inside the noise. Wording: "not detected", never "stopped". |
| GNSS stations agree | Every station check is **warn**: a station-sized box scatters 38 to 79 mm/yr, so the check cannot decide. Don't show a station tick as validation. |
| The forecast | Only z4 on 029A is backtested (4 overlapping cutoffs, GP 3.90 against persistence 4.19 mm, not significant). The other zones reuse the method untested. Label it as a scenario, show the 80 % band, no single date. |
| 029A numbers after the troposphere correction | The OPERA sign check fails narrowly on 029A (13 of 29 pairs). Quote z4 on 029A as a range, −2.8 to −7.5 mm. |

## Drop (do not claim)

| Claim | Why |
|---|---|
| Anything from NISAR 094D on the page | Check 1 **fails** (+23.5 mm/yr, the zones "rise"). That's a valley-floor troposphere effect, not a sign error. Keep 094D off, or show it flagged for inspection only. |
| NISAR 094D against Sentinel-1 029A | Three zones **fail** (the satellites disagree in direction); the fourth is untestable. |
| A green tick or "validated" on any single spot or pin | Nothing at pin scale passes above the noise. Use the 2σ rule (Darius's pin task): show a value only where it beats 2σ, otherwise say "not measurable here". |
| An independent third witness for 2026 | None exists inside the window: the only open GNSS stations with 2026 data are 70 and 91 km away. The 2026 cross-check is Sentinel-1 only. |
| Moisture or rain effects at z1 or z2 | 029A z1 r = −0.70 is one hit among many tries; at that count, about what chance gives. Leave it as a recheck candidate. |

## Open (not blocking the freeze)

- The `checks.md` header still says "Validator draft, pending 05's review". This page is the review. Once 01 agrees, 05 changes that line in `validate.py`.
- Frozen-build rerun (validation log): rerun `validate.py` on the frozen build after 2:30 and confirm the verdicts above don't change.
- The January to October Sentinel-1 extension is the real test for z3 and the z1 moisture candidate. It comes after the hackathon.
