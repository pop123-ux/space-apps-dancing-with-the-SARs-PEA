# The page: satellite switch and views

**Owner:** 06 · App developer (Darius)

Version 2, Sat 14 Nov 2026. This design implements **D-004** (locked): we fit both NISAR and Sentinel-1, and the page lets anyone switch between the two satellites and examine ground motion in several ways. It also keeps D-002 (the map opens on Ocnele Mari; Romania is blurred context).

The layout below shows the intended product. The current real-data build starts on NISAR Coverage and offers a direct switch to Sentinel-1 measurements. Use the [file contracts](build-spec.md#file-contracts) and the implementation handoff below.

## The idea in one sentence

**One place, two radars, several ways to look.** A judge can see the same salt zones through NISAR (L-band, 24 cm) and through Sentinel-1 (C-band, 5.5 cm). They can see them as a map that changes over time, a rate map, a chart per zone, a head-to-head comparison, or a timeline of when each satellite actually looked.

## Layout

**Laptop:**

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ Dancing on Salt · Ocnele Mari                                    [About] [Checks ✔ 4] │
│                                                                                      │
│ Satellite  ( ● NISAR  L-band 24 cm ) ( Sentinel-1  C-band 5.5 cm ) ( ⇆ Compare )      │
│ Track      ( ● 129A ↗ ascending ) ( 094D ↘ descending )                               │
│ View       [ Change ] [ Rate ] [ Zones ] [ Agreement ] [ Coverage ]   ☐ Up/east (exp.) │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                    MAP · opens on Ocnele Mari (D-002), Romania blurred                │
│                    salt zones outlined · station pins · reference band                │
│                                                                                      │
│   ┌ legend ────────────────────────┐                                                 │
│   │ −20 ■■■■■□□□□□■■■■■ +20 mm      │  shared by both satellites                      │
│   │ red: away from the satellite   │                                                 │
│   └────────────────────────────────┘                                                 │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ ▶  Nov 2025 ●─●─●─●─● ░░░░░░░ no NISAR data 18 Jan to 23 Jun 2026 ░░░░░ ●─●─●─●─●─● Oct │
│    NISAR 129A ↗ · 2026-08-22 · since 2025-11-07 · beta/provisional · positive = toward │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Phone:** the satellite switch stays pinned at the top as one three-part control. The view switch is a row of chips above the slider. Track, legend and labels sit in a pull-up sheet.

```
┌────────────────────────────┐
│ ( NISAR )(Sentinel-1)( ⇆ ) │
│                            │
│          MAP               │
│                            │
│ [Change][Rate][Zones][ › ] │
│ ▶ ●─●─●░░░░░●─●─●─●  Oct   │
│ ︿ NISAR 129A · 2026-08-22  │
└────────────────────────────┘
```

## Control 1: the satellite switch

A segmented button group with three options. It is always visible, and exactly one option is pressed.

| Button | Shows | Label under the button |
| --- | --- | --- |
| **NISAR** (default, the brief asks for NISAR first) | Catalog coverage now and measured layers after the fresh fit is validated | NASA–ISRO · L-band, 24 cm · 12-day repeat · beta/provisional |
| **Sentinel-1** | Sentinel-1 layers for the chosen track | ESA / Copernicus · C-band, 5.5 cm · 6-day repeat · contains modified Copernicus Sentinel data 2026, processed by ASF HyP3 |
| **⇆ Compare** | Both at once: a swipe divider on the map (left NISAR, right Sentinel-1), both series overlaid on the charts | "Same months only: 7 Jul to 4 Oct 2026" |

- **Track buttons** change with the satellite: NISAR `129A ↗` / `094D ↘`; Sentinel-1 `029A ↗` / `007D ↘`. In Compare, each side keeps its own track, ascending with ascending by default.
- **The view and the date stay** when you switch satellites. If the other satellite has no data at that date, the map shows "No Sentinel-1 acquisition on this date: nearest is 2026-08-24" and snaps only when the user agrees. It never snaps silently.
- **A satellite with catalog coverage stays selectable.** Disable its measurement views with a one-line reason. Keep the Compare control visible with its pending state.

## Control 2: the view switch

Five views of the same problem. Measurement views activate when their inputs are available. Coverage works from the catalog.

| View | What you see | One satellite | Compare | Reads |
| --- | --- | --- | --- | --- |
| **Change** (default after NISAR validation) | Cumulative line-of-sight change since the track's first date, played with the slider | Frames for that track | Swipe; each side uses an explicitly selected acquisition and names that date | `sensors.<s>.frames` |
| **Rate** | Line-of-sight slope in mm/yr, labelled "annualized short-window slope". Apply a 2σ mask only when a validated uncertainty layer exists | The track's rate layer | Swipe | `sensors.<s>.layers` (`los_<track>`) |
| **Zones** | One chart per salt zone: median mm per date with contributing-pixel counts. The outer comparison area is drawn as a grey line, and null dates are gaps | That satellite's tracks | Both satellites on one chart, colour plus marker shape per satellite | `series.json` (`kind: zone` and `control`) |
| **Agreement** | Per zone, NISAR next to Sentinel-1 over the common window, with validated intervals when available, plus verified station pins and EGMS history as context. Keep the historical panel available independently of the paired-radar verdict. Each zone is marked "agree", "disagree" or "not testable", with the reason | Not available (needs both) | The home of this view | `series.json`, `checks.json` (check 8), `stations.geojson` |
| **Coverage** | A timeline: one row per satellite and track, one dot per acquisition. The NISAR gap (18 Jan to 23 Jun 2026) is hatched and the common window highlighted | Always shows both, so the gap is visible | Same | `coverage.json`, with verified frame dates from `manifest.json` |

**Up and east (experimental).** A checkbox, off by default. When on, the map shows the vertical and east–west layers flagged `experimental: true`, with a banner: "Derived assuming no north motion; reference and atmosphere not resolved." It follows the Sentinel-1 handoff rule to keep derived components out of the main view.

## Honest comparison rules

Compare only shows two satellites side by side when what it shows means the same thing. 03, 04 and 05 own the numbers; the page enforces the labels.

1. **Same months.** Compare and Agreement use only the common window, 7 Jul to 4 Oct 2026 (`manifest.common_window`). Dates outside it are dimmed.
2. **Same reference.** NISAR’s GNSS tie is pending. Sentinel-1 is terrain-relative. Zone minus outer comparison area is a proposed spatial contrast. O-19 sets the common quantity and measurement geometry before Agreement reports a verdict.
3. **Line of sight is not the same quantity across satellites.** The two satellites look from different angles, and NISAR looks left while Sentinel-1 looks right. Compare therefore shows each satellite in its own line of sight, with its geometry named. A single shared quantity (vertical-equivalent, or up and east) appears only under the experimental toggle until 03 and 04 sign it off (O-19).
4. **Same scale.** One fixed, symmetric legend per quantity, shared by both satellites. It never auto-scales per satellite.
5. **Say what each one is.** Every view names the satellite, band and wavelength, track and direction, dates, reference, sign ("positive = toward the satellite") and status.
6. **No silent gaps.** Missing dates, masked pixels and unsupported zones show as "no data" with the reason, as with zone 3 on Sentinel-1 029A.
7. **Synthetic banner.** On `mock` or `demo`, "Simulated, not data" covers every view.

## The slider

- **One calendar axis** from Nov 2025 to Oct 2026, with real acquisition dates as ticks. It snaps to the selected satellite and track.
- **Play** steps through acquisitions, about 0.6 s each, never through days without data.
- **The date label** always reads: satellite, track, date, "since <first date>".

## State in the URL

Every view is a link, so story stops, slides and judges can jump straight to it:

```
#sat=nisar|s1|compare&track=129A&view=change|rate|zones|agreement|coverage&date=2026-08-22&exp=0|1&window=jul_oct|jan_oct&scenario=baseline
```

01's story stops are lists of these links, and each slide screenshot (slide 5) carries its link.

## Accessibility

- **Buttons:** every control is a real `<button>` with `aria-pressed`, inside a `role="group"` labelled "Satellite", "Track" or "View".
- **Keyboard:** arrow keys move within a group, and focus is always visible.
- **Colour:** satellites are told apart by colour **and** marker shape **and** text. The map uses RdBu; never red and green alone.
- **Charts:** every chart has a "Show as table" option.
- **Motion:** respect `prefers-reduced-motion`; play does not autostart.

## What each role supplies

| Role | For the switch and the views |
| --- | --- |
| 02 | NISAR inputs. Sentinel-1 raw products mirrored with checksums (`sentinel1/provenance/`) |
| 03 | NISAR `ts.npz` and the Sentinel-1 fit (`sentinel1/analysis/`); zone and outer-band histories for both |
| 04 | The NISAR tie; the line-of-sight convention for both satellites; O-19 (the shared quantity) |
| 05 | Check 8, "NISAR and Sentinel-1 agree", per zone over the common window; the coverage facts |
| 06 | `export.py` writes `products/ocnele_mari/<sensor>/…` for both, then builds this page |
| 01 | The default state and the story-stop links; which view goes on slide 5 |

## Fallbacks

- **If measurements are pending:** show catalog coverage if available and link to the other satellite’s measured views.
- **If Compare isn't ready by hour 36:** keep the switch (one satellite at a time) and the Coverage view, and drop the swipe.
- **Never cut:** the switch itself, the gap labels or the comparison rules above.

## 06 implementation handoff · 14 November 2026

Download [Ocnele_Mari_UI_Handoff.zip](https://chatgpt.com/library?file_id=libfile_29db7ee872a88191bb4e3cda0163c275&account_id=personal) and serve its `products/` folder over HTTP. Start with `products/index.json` and `products/ocnele_mari/manifest.json`. The bundle passed the repo product checker and includes 130 acquisition overlays, four baseline rate maps, zone and outer-area series, the fitted stacks, exporters, and provenance. Treat this ZIP as the snapshot behind the values below. The group-aware solver on main supports disconnected acquisition groups. A replacement export needs the regression check and must carry group boundaries and reference epochs through to the UI.

| View or control | Source and behavior |
| --- | --- |
| **NISAR** | Default to Coverage on 129A. `coverage.json.nisar` contains 22 public NASA Earthdata/ASF Level-2 GUNW beta/provisional pairs. 129A has 13 pairs and the 18 January–23 June gap. 094D has nine pairs. Keep an explicit **Displacement fit pending** state. Authenticated HDF5 download, independent fit and LOS sign check are pending. Promote Change after validation and label calibration separately. |
| **Sentinel-1** | Start with `jul_oct`. 029A runs 7 July–5 October and 007D runs 6 July–4 October. Each track has 16 dates and 29 pairs. `jan_oct` adds 132 completed HyP3 jobs, 95 pairs and 49 dates per track in the combined fit. 029A starts 1 January and 007D starts 6 January. |
| **Change / Rate** | Read `manifest.json` for the default frames, bounds and layers. For either window use `sensitivity.json.windows[window].frames` and `.layers`. Use the aligned web overlays and manifest bounds. Transparent pixels are missing. Red is away and blue is toward. Label saturation and keep the date, reference date and units visible. Rate is a fitted annualized slope over the selected window. There is no validated per-pixel sigma layer in this bundle. |
| **Zones** | `series.json` gives the summer baseline. For both windows and alternate scenarios read `sensitivity.json.windows[window].variants[track][scenario][zone]`. Use `mm` for the sample-date chart, `fitted_change_mm` for the fitted window change, and `n_pixels` for support. `endpoint_change_mm` is a different statistic. Preserve nulls and break the line at gaps. Plot the outer comparison area with its own label. |
| **Coverage** | Show acquisition ticks and usable zone pixel counts as two distinct indicators. NISAR’s catalog gap offers **View Sentinel-1** with its actual dates. Retain the date on switches and offer the nearest acquisition as an explicit choice. On the extended 007D fit, say **No continuous zone series across all 49 dates**. |
| **Agreement / Compare** | Keep the proposed common window, 7 July–4 October 2026. Use the same spatial support, documented reference and a geometry-aware quantity before a verdict. NISAR and Sentinel-1 view from different sides. Show separate LOS labels and **Not testable yet** while the fit or O-19 is pending. `checks.json` is the source for validation status. |
| **Historical ground motion** | Reserve a panel in Agreement for **EGMS Ortho · 2020–2025 · 100 m**, with Up and East–West controls and their own legend. Paul’s E54N25 extracts are pending verification, so show the empty state. After validation show cell count, median and quartiles for the same zones and reference masks. A recurring footprint establishes historical context. The longer historical window cannot verify a 2026 rate. EGMS is derived from Sentinel-1, and the Ortho layer is distinct from the GNSS model used in calibration. |

### Explore processing choices

Use a disclosure panel with window and scenario selectors. Keep the default at July–October / baseline. The five computed scenarios are baseline (coherence ≥ 0.35), stricter coherence (≥ 0.55), west reference, east reference, and an elevation-correction run. Selecting a scenario updates the chart, fitted change, pixel count and interpretation together. The supplied rasters are baseline for each window, so retain a **Baseline map** label or hide the map for alternate scenarios. The sliders and selectors choose stored results. Leave-one-date-out ranges describe fit sensitivity.

- **Summer Zone 4** is the demo example. Fitted LOS changes are −7.52 mm ascending and −3.51 mm descending, both negative across all five runs. The pattern is consistent with localized subsidence relative to nearby terrain.
- **Extended Zone 4 ascending** shows **Direction changes with processing**. Baseline −4.07 mm with 26 pixels, elevation correction +4.48 mm with 26 pixels, and strict coherence +1.21 mm with two pixels. The extended descending salt-zone series is unsupported. Leave its values null.
- Show **Limited coverage** with the count wherever the result relies on few pixels. Keep experimental Up/East layers disabled when there is no supported export.

### Resident view, methods and credits

Lead with **Where did the ground move?**, the observation window, and a short support label. Provide a source and methods drawer with the sensor, track, component, sign, window, reference, quality filters, and links to the data and code. For preparedness, explain what the map can tell residents and link to official notices. Use the indicators for observation quality and coverage. Hazard forecasts, evacuation guidance, and building safety determinations require official sources.

Sentinel-1 was acquired on IW2 VV bursts `029_060407_IW2` and `007_013694_IW2`, processed through ASF HyP3 with 10×2 looks and water masking, and inverted on a 40 m grid using coherence-squared weights. The terrain reference band is 3–6.5 km from zone edges. The outer comparison area is 6.5–8 km. The bundle includes pair manifests, job IDs, and SHA-256 digests. Credit Copernicus Sentinel-1, ASF HyP3, NASA–ISRO NISAR, and Copernicus Land Monitoring Service EGMS where each appears. Confirm publishing permission for the advisor-kit zone circles or update the zone definitions and rerun before publication.

- [Sentinel-1 team handoff](../sentinel1/docs/TEAM_HANDOFF.md)
- [NASA Space Apps challenge resources](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources)
- [ASF NISAR Data User Guide](https://nisar-docs.asf.alaska.edu/)
- [EGMS 2020–2025 release](https://land.copernicus.eu/en/news/product-update-european-ground-motion-service-2025)

### Claude Code kickoff for Darius

> Sync to current main. Read `CLAUDE.md`, `docs/ui.md`, `docs/build-spec.md` and `OWNERS.md`. Build the 06 frontend in the repo using the real UI handoff, with NISAR Coverage as the default, working Sentinel-1 Change/Rate/Zones, and the processing scenario panel. Preserve missing values, label baseline maps and keep pending NISAR/EGMS states honest. Add accessible keyboard controls and a phone layout, then test the summer Zone 4 story, the extended sign flip, the descending coverage gap, and the existing mock flow. Run `python checkpoint.py ocnele_mari --products <bundle>/products` and `pytest -q`, log substantive AI use in `AI-DISCLOSURE.md`, and open the 06 PR. Keep raw archives and credentials out of the app.

