# Prior work and what is new

**Owner:** 05 · Validator (Paul)

For the slides and the judges' Creativity question: what others already measured at Ocnele Mari and similar salt sites, and what this project adds. Search done 15 Nov 2026. "Read" means we opened the source; "abstract only" means we quote its abstract or catalogue entry and did not check the full text.

## Ocnele Mari itself

| Work | What it did | What it could not do | Status |
|---|---|---|---|
| Ene et al. 2009; Mesescu 2011, *Carpathian J. Earth Env. Sci.* 6(1) | The 2001 to 2005 collapses, salt geology, people affected (113 households, 209 persons per Mesescu) | No satellite motion data; ground surveys and reports | Read (summarised in `ocnele-mari-geography.md`) |
| *Land degradation monitoring in the Ocnele Mari salt mining area using satellite imagery*, SPIE 2011 ([ResearchGate](https://www.researchgate.net/publication/235888900)) | TerraSAR-X and optical monitoring after 2007; snippets report centimetre to 2 m subsidence | Commercial radar, a few years, no public products | Abstract only |
| ASRC / Terrasigna 2012 ([PDF](https://www.terrasigna.com/uploads/Events/Monitorizare_CO2_ASRC_2012.pdf)) | An InSAR subsidence map of Ocnele Mari for 2010 | One map, one period | Read (map only) |
| Rădutu and Vlad-Sandru 2023, *Mining Revue* 29(1) ([link](https://reference-global.com/article/10.2478/minrv-2023-0004)) | Review of radar interferometry for mining subsidence; says sudden collapse from water inflow can't be caught with InSAR, but slow subsidence can | A review, no new measurement | Abstract only |
| EGMS Ortho 2020 to 2025 (Copernicus) | Continent-wide Sentinel-1 ground motion, 100 m cells; z3 sinks −18.9 mm/yr | Ends Nov 2025, yearly update, no 2026, no forecast, nobody looks at this town specifically | Used (05, `egms_cut.py`) |
| Muntean et al. 2026, *Solid Earth* 17, 747 ([article](https://se.copernicus.org/articles/17/747/2026/)) | 20 years of Romanian GNSS, vertical rates incl. VLC2 | Regional tectonics, not the salt field | Used (stations) |

## Other salt and mine sites (methods we lean on)

| Work | Site | Relevance |
|---|---|---|
| Solari et al. 2020, *Remote Sensing* 12, 3919, [doi:10.3390/rs12233919](https://doi.org/10.3390/rs12233919) | Saline di Volterra, Italy (salt solution mining, like Ocnele Mari) | Shows fast salt-mining motion breaks standard persistent-scatterer InSAR and needs detail-scale processing: the same coherence loss we see over the bowl on 029A |
| *InSAR analysis of partially coherent targets: Maceió*, *Remote Sensing* 16, 3806 (2024), [mdpi](https://www.mdpi.com/2072-4292/16/20/3806) | Maceió, Brazil (salt mine collapse, Dec 2023) | Up to −1,750 mm before the Mine 18 collapse, seen on Sentinel-1. Not Ocnele Mari; quote only as "this is what a precursor can look like elsewhere" (abstract only) |

## What is new here (one line for the slide)

**The first look at Ocnele Mari with NISAR, cross-checked against two Sentinel-1 tracks in the same 2026 months, every claim tested against its noise, and turned into a page residents can read.**

In detail:
1. **NISAR, 2026.** No published work uses NISAR over the town; the data is months old. Earlier radar here was TerraSAR-X (commercial, to about 2012) and EGMS (to Nov 2025).
2. **Two radars, same months.** NISAR L-band and Sentinel-1 C-band over July to October 2026, paired by geometry so east-west motion cancels (`validate.py`, O-19).
3. **The noise is published with the answer.** Predeclared tests, 2σ rule, troposphere checked with a weather model (OPERA) and the zones checked against rain and soil moisture (NISAR SME2). Earlier site work gives maps, not error bars.
4. **A forecast, labelled as one.** A backtested 30-day outlook for Slătioarele with its band, not a date of collapse.
5. **For residents, not specialists.** Zone names people use (Lacul Țeica, Ocnița · Goruniș, Slătioarele), plain wording, open code and data links.

## What we do not claim

- Not the first InSAR at Ocnele Mari (TerraSAR-X and EGMS came first).
- Not a collapse warning: like the 2023 review says, sudden collapse from water inflow is not something InSAR catches.
- NISAR products are beta or provisional and "not intended for scientific research"; we say so on the page.
