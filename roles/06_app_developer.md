# 06 · App developer — Darius

**Mission.** One page anyone can open on a phone: a map that dances, pins that tell the truth, and story stops. Build it on mock products from hour 0; the real numbers slot in underneath.

**You own:** `export.py` (stub) → `products/<site>/`; `mock_products.py` (works); and the page: `index.html` and app assets, which you create. Nothing for the page exists yet. You hold `docs/contract.md` jointly with 01.

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| 0–2 | `python mock_products.py`, then start the page on `products/mock/`. Serve it with `python -m http.server 8790`. **Agree and freeze the contract with 01 at hour 2** (O-10). | The page loads the mock site |
| 2–6 | GitHub Pages with the mock site live at a public link. Basemap and the Romania blur (O-09). | Public demo link |
| 6–18 | Map (D-002), slider, legend, units, synthetic banner. `export.py` for the real rates as soon as `up_east.npz` exists. | Real site loads |
| 18–30 | Pins, story mode, phone layout, keyboard use, colour-blind check. **An honest slider gap.** | Works on a phone |
| 30–40 | Captions, accessibility, the demo link in the submission. | — |
| 40–48 | Polish only; no number changes. | — |

## The map (D-002, locked)

- **Opening view:** zoomed on the Ocnele Mari area. Use `manifest.view`: center `[45.086281, 24.2704806]`, zoom 13, the Google Maps view from the brief.
- **Zooming out:** the Romanian area appears, **blurred and de-emphasised**. It is context, not data. How to do it is yours (O-09): CSS blur or opacity below a zoom level, a muted tile style, or only a Romania outline.
- **Analysis window vs view:** the overlays cover the 50 km analysis window (`manifest.bounds`). The view focuses on the town.

## The contract (summary; full detail in [docs/contract.md](../docs/contract.md))

`manifest.json` · `up.png` · `east.png` · `los_<track>.png` · `frames/<track>/<date>.png` · `series.json` · `stations.geojson` · `checks.json` · `checks.md` · `calib.json` · `up.tif` · `east.tif` · `../index.json`.

The page reads these files and nothing else. If a file changes shape, the change goes into `checkpoint.py`, `mock_products.py` and the page in the same PR.

## Starting points

- **Overlays:** Leaflet image overlays are axis-aligned, so overlays are resampled to a lon/lat grid (about 100 m). The GeoTIFFs keep the original UTM grid.
- **The 129A gap:** 129A has **no data from 18 Jan to 23 Jun 2026**. `manifest.frames.129A.gaps` says so. Show "no data" and never interpolate.
- **The two tracks cover different months:** 129A Nov 2025 – Oct 2026 with the gap, 094D Jun – Oct 2026.
- **Colours:** RdBu diverging (red = sinking or away from the satellite). Never red/green alone.
- **Uncertainty:** grey out where |rate| < 2σ (decided with 03).

## Watch out

- **The synthetic banner** ("simulated, not data") must show whenever `manifest.synthetic` is true. Never screenshot mock or demo for the video without it.
- **Beta/provisional NISAR** must be stated on the page.
- **OSM tiles** are fine for a demo; heavy traffic needs another tile source.

## Decisions you drive or feed

O-09 basemap and blur · O-10 contract freeze (with 01).

## Questions to answer during the event

- Does the slider stay smooth on a phone with about 15 frames per track? If not, shrink the frames in `export.py`.
- Can someone who has never heard of radar understand the first screen in ten seconds?

## Done when

The public link works on two phones, the slider plays honestly across the gap, the pins explain themselves, and story mode walks the stops.
