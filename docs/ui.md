# The page: satellite switch and views

**Owner:** 06 · App developer (Darius)

Version 3, Sat 14 Nov 2026, 16:15. This design implements **D-004** (locked): we fit both NISAR and Sentinel-1, and the page lets anyone switch between the two satellites and examine ground motion in several ways. It also keeps D-002 (the map opens on Ocnele Mari; Romania is blurred context).

The page is built: `index.html` and `app/` on branch `r06/page`. Its real data comes from `python export.py ocnele_mari` (see [products/README.md](../products/README.md)). Version 3 replaces version 2's dark, multi-panel sketch with a minimal, light layout at Darius's request; the controls, views and comparison rules are the same. What is built and what is not is in "Implementation status" below; the running log is [logs/06-app.md](../logs/06-app.md).

## The idea in one sentence

**One place, two radars, several ways to look.** A judge can see the same salt zones through NISAR (L-band, 24 cm) and through Sentinel-1 (C-band, 5.5 cm). They can see them as a map that changes over time, a rate map, a chart per zone, a head-to-head comparison, or a timeline of when each satellite actually looked.

## Layout

One title pill and one satellite menu at the top, one dock at the bottom, the map everywhere else. Everything else opens on demand: the legend, the map settings, a sheet on the right for Zones, Agreement, Coverage or a clicked zone or station.

**Laptop:**

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ( Dancing on Salt · Ocnele Mari )                 ( ▲ Sentinel-1 C-band ▼ ) (✔0 !0 ✘0) (i) │
│ ( Simulated, not data )  ← only on mock or demo                                      │
│                                                              ┌ sheet (on demand) ───┐ │
│        MAP · opens on Ocnele Mari (D-002), Romania blurred    │ Where did the ground │ │
│        black line = town boundary · ● 1–4 = salt zones        │ move? zone facts,    │ │
│        dots = Sentinel-1 measurements, one every 80 m         │ charts, processing   │ │
│                                                              │ choices              │ │
│  ┌ legend ──────────────────┐                                 └──────────────────────┘ │
│  │ Change mm since first date│                                                  (layers)│
│  │ −20 ■■■■□□□□■■■■ +20      │                                                         │
│  │ — Ocnele Mari boundary    │                                                         │
│  └───────────────────────────┘                                                         │
│  ┌ dock ──────────────────────────────────────────────────────────────────────────────┐│
│  │ [Change][Rate][Zones][Agreement][Coverage]                          029A ↗  007D ↘  ││
│  │ (▶) Nov 2025 ○ ○ ○ ░░ No NISAR data 18 Jan to 23 Jun 2026 ░░ ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ Oct    ││
│  │ ▲ Sentinel-1 029A ↗ · 2026-10-05 · change since 2026-07-07 · positive = toward      ││
│  └────────────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Phone:** the same pieces stacked. The title and the satellite menu stay at the top; the dock holds the view chips (they scroll), the track chips, the timeline and the status line; the sheet opens from the bottom over the map.

```
┌────────────────────────────┐
│ (Dancing on Salt) (▲ S-1 ▼)(i)│
│                            │
│          MAP               │
│                            │
│ ┌ legend ┐          (layers)│
│ [Change][Rate][Zones][Agr…]│
│ 029A ↗  007D ↘             │
│ (▶) ○○○░░No data░░▲▲▲▲▲ Oct │
│ ▲ Sentinel-1 029A · 10-05  │
└────────────────────────────┘
```

## Layout v4: docked panels (14 Nov 2026, 21:45, team sketch)

The team's sketch ([docs/figures/02_ui_sketch_v4.jpg](figures/02_ui_sketch_v4.jpg)): a **toolbar** with the logo across the top, the **map** in the middle (opening on Ocnele Mari, D-002), a **menu column** on the right that a click on the map opens ("click => deschide meniu": a zone, a station or a view's details, with its chart), and the **timeline** across the full width at the bottom.

- Implemented in `app/style.css` (block "docked layout (v4)"), `index.html` (logo mark) and `app/main.js` (the map resizes to the space left of the menu column; it never sits under a panel).
- Phone: the menu is a drawer above the timeline (at most 55 % of the height); the toolbar and its satellite menu stay above it. This fixes the audit's first high finding (the sheet covered the dock and the satellite menu). The legend's "away from / toward satellite" caps and the full status line now show on phones (audit finding 2, honest-comparison rule 5).
- Checked with Playwright at 1440 × 900 and on an iPhone 13: zone click opens the column, the satellite menu stays clickable, no console errors.

## NISAR on the page and the Chronos-2 panel (14 Nov 2026, 23:30)

- NISAR 129A is measured: change frames (each counted from the first date of its acquisition group, so summer frames read "since 2026-06-23"), a rate map and dots inside the Sentinel-1 box. On first load each satellite opens on its own last date.
- 094D appears as a disabled chip, "094D · under review", whose tooltip gives the T3 reason (`manifest.sensors.nisar.pending`).
- Compare and Agreement stay off with the manifest's `compare.reason` until both NISAR tracks pass T3.
- The forecast block shows Chronos-2 only, with its 80 % range as two light dashed lines, a "Forecast date" slider (keyboard accessible, `aria-valuetext` is the date), the NISAR October check and the baselines in the footnote.

## Sentinel-1 fills NISAR's gap (15 Nov 2026)

NISAR has no acquisitions over the town from 18 Jan to 23 Jun 2026 (NASA CMR; cause unknown, O-14). Sentinel-1 029A imaged it every 6 days through those months, and its January to October fit is now exported as a second Sentinel-1 window (`sensitivity.json` `windows.jan_oct`, frames under `products/<site>/s1/jan_oct/`, `fills_gap` naming the NISAR gap).

- **Timeline:** in NISAR mode the hatched gap carries a "Sentinel-1 covers this →" button. It switches to Sentinel-1, the same direction of flight (129A ascending → 029A ascending), the January to October window, at the acquisition nearest the middle of the gap.
- **Zone charts:** NISAR's zone chart adds the Sentinel-1 January to October line through the gap months, in Sentinel-1's colour, with a note: it is Sentinel-1's own line of sight and reference, so its shape, not its offset from the NISAR line, carries information. The two are never spliced into one line: the geometry (left- vs right-looking) and the reference differ (O-19).
- **Caveats carried over:** the January to October fit cannot be rerun from the repository (job IDs only), has no weather-model scenario, and has no zone series on 007D or for Zone 3.

## Exploration pass: Motion, Coverage, Compare and the Zone 4 flow (15 Nov 2026)

A first-time visitor can open `#preset=zone4` (or press **Investigate Zone 4**) and answer: what was measured, over what dates and relative to what; how the result changes with processing; what the satellites can and cannot compare.

- **Navigation:** Motion (Change, Rate), Coverage, Compare. Internal view keys are unchanged, so old links with `view=coverage`, `view=zones` and `view=agreement` still open (verified).
- **Context strip** under the toolbar: satellite, track, the acquisition and its real baseline date (Change) or the fit window and "Annualized line-of-sight rate (mm/yr)" (Rate), the processing run, the reference area and "Negative means motion away from the satellite along its line of sight."
- **Zones:** chips for Zones 1 to 4 (Zones 1 and 2 overlap at the opening zoom; the chips keep both selectable), a dashed footprint on the map, selection kept across views, satellites and tracks, and in the link (`zone=z4`). **Copy view link** and **Reset to site** sit beside them.
- **Chart and map are linked:** clicking an acquisition on a zone chart moves the map to that date; moving the timeline marks the matching point (dotted line, larger point).
- **Compare processing runs** (Sentinel-1 zone panel): the baseline and one alternative on shared axes, observed points and each run's fitted line, plus a table of every run with fitted change, acquisition count, usable pixels, window and reference. Runs without a series say why (the weather model has no January to October series because those interferograms are not in the repository). A lead line, "Fitted direction changes with processing", appears when stored runs disagree in sign.
- **Regression check (artifacts, 15 Nov 2026):** Zone 4, Sentinel-1 029A, January to October: baseline −4.07 mm, 26 px; elevation correction (fitted to the data) +4.48 mm, 26 px; stricter coherence +1.21 mm, 2 px (flagged "only 2 px"). Same values as the reviewed build; source `sentinel1/analysis_jan_oct/summary.json` via `sensitivity.json`. These are January to October window fits, distinct from the summer zone-minus-outer-ring comparison under Compare.
- **Coverage:** the map shows every pixel with a connected series on the active track and window as a grey dot; the zone panel gives one support row per satellite and track or the reason for none, with buttons to another track or window that has data (Zone 3: none on 029A in either window, 55 px on 007D July to October, 12 px on NISAR 129A; 094D held).
- **Compare:** for a selected zone, parallel line-of-sight observations (zone minus the 6.5 to 8 km ring) over the common window, each labelled with track, direction and look side; the verdict comes from `checks.json` (Zone 4: inconclusive, tolerance too wide); blockers listed (094D, O-19); EGMS under "Historical context".
- **Status pill:** shows the check that matters for the selection (for example the zone's NISAR against Sentinel-1 check) and opens the About panel at that evidence.
- **Legend:** larger; "near 0 (pale dot)" and "no dot = no data" keys. Phone: one-line context, numbered zone chips, one scrolling control row, drawer at most 36 % of the height.

## Round two (15 Nov 2026): satellite basemap, Romanian, tables, Compare, stations

- **Satellite imagery by default**; switching basemaps keeps the measurement dots (the point source is reset on a style change). Coverage dots are white with a dark outline on imagery.
- **Sentinel-1 marks** on the timeline are slim rounded capsules (they read cleanly at 49 dates); NISAR keeps round dots, so the two differ by shape, not only colour. Chart points: diamonds for Sentinel-1, circles for NISAR.
- **Tables:** "Open table" shows the full table in a dialog in front of the page; **Export CSV** downloads it (zone series, compare series, the processing-run table).
- **Language:** EN | RO beside the logo (`app/i18n.js`): tabs, buttons, headings, legend, the sign sentence, context strip, run names. Defaults to Romanian when the browser is Romanian; kept in the link (`lang=ro`). Texts written by the pipeline and the validator stay English.
- **Compare enabled** (satellite menu): tracks paired by viewing geometry (NISAR 129A with Sentinel-1 007D; NISAR 094D with 029A), each in its own line of sight; per-zone verdicts come from the validator.
- **NISAR 094D shown, flagged** (⚠ on its track chip and in the context strip): it failed T3 and stays visible for inspection only.
- **Stations:** one marker per monument; the panel lists every solution (VLC1, VLC2 and their inverse-variance mean) against every radar track covering it, with the GNSS observation period and the radar pixels and radius used.
- **Data freshness** in About, from `products/<site>/updates.json` (update.py).

## Implementation status (r06/page, 14 Nov 2026, 16:15)

| Part | Status | Notes |
| --- | --- | --- |
| Opening view, Romania blurred (D-002) | Built | Opens at the manifest view; below MapLibre zoom 10 the map blurs and a town label flies back |
| Town boundary | Built | Black line from OpenStreetMap relation 9845422 (`app/ocnele_mari_boundary.geojson`), display only |
| Satellite menu: NISAR, Sentinel-1, Compare | Built | One button that opens a menu instead of three always-visible buttons (v3 layout). NISAR stays selectable with "Displacement fit pending"; Compare is disabled with its reason until NISAR is measured |
| Change, Rate (Sentinel-1) | Built | Dots, one every 80 m, coloured RdBu on one fixed scale (±20 mm, ±40 mm/yr); a click shows the value. PNG overlays are the fallback (mock site) |
| Zones | Built | Per zone: fitted change and pixel count per track, "Limited coverage" under 10 pixels, "Direction changes with processing" or "… in all 5 runs", chart with the outer comparison area |
| Processing choices | Built | Window and run selectors over `sensitivity.json`; the map stays the baseline run and says so. Only the July to October window is in the repository |
| Agreement | Built, pending data | "Not testable yet" while NISAR is unmeasured and O-19 is open; EGMS 2020 to 2025 panel in its empty state |
| Coverage | Built | NISAR catalog pairs (hollow marks), Sentinel-1 dates, the January to June gap, the common window, usable pixels per zone |
| 03 zone review labels | Built | Zone 3: "Historically subsiding · 2026 trend inconclusive"; 029A on Zones 1, 2 and 4: "Local reference sensitivity". Text from `manifest.zone_notes` and `track_notes` (written by `export.py`); values unchanged |
| Up and east (experimental) | Disabled | No supported export (O-19) |
| Station pins | Built, no data | `stations.geojson` is an empty pending file until `validate.py` (05) runs |
| URL state | Built | `#site=…&sat=…&track=…&view=…&date=…&exp=…&window=…&scenario=…` |
| Phone layout | Built | Checked at 375 × 812 in a browser; T9 on two real phones is still to do |
| GitHub Pages deploy | Not yet | Needs `.github/workflows/pages.yml` (06) and Pages turned on by the repo owner |
| NISAR measured layers | Waiting on 02, 03, 04 | `export.py` adds them when `ts.npz` exists |
| January to October Sentinel-1 window | Waiting on 03 | Its fit is not in the repository; the page shows it as soon as a products set carries it |

## Control 1: the satellite switch

Three options; exactly one is chosen. In version 3 they sit in one menu button at the top right, which always shows the chosen satellite (it was a three-part segmented control in version 2).

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


### Zone review and historical context

The [group-aware rerun and four-zone review](../sentinel1/docs/TEAM_HANDOFF.md#14-november-2026--group-aware-refit-and-egms-cross-check) confirms the existing bundle's Sentinel-1 numbers. Zone 3 is **Historically subsiding · 2026 trend inconclusive** in the comparison narrative. For January–October show **Insufficient continuous coverage** on both tracks. For July–October show the descending estimate with its processing sensitivity and leave the ascending series empty. Show a local reference sensitivity note for 029A when interpreting Zones 1, 2 or 4. Preserve the exported values.

[R05 PR #9](https://github.com/pop123-ux/space-apps-dancing-with-the-SARs-PEA/pull/9) reports the 2020–2025 historical cut and zone statistics. The current bundle still lacks the EGMS display assets. Keep the history layer pending until the validated products reach 06. Label dates, Up/East direction and cell count when publishing them.

## Forecast and environmental controls

See [the forecasting handoff](forecast.md) for the January endpoint, Paul’s inputs, and the checks required before publishing environmental or vertical scenarios. Since 14 Nov 18:30 the forecast panel offers four model paths (persistence, Theil–Sen, Gaussian process, long-term trend from EGMS 2020–2025) and says that rainfall and soil moisture were tested and not adopted. The model selector must wrap or become a select when four buttons do not fit. Since 19:30 there are five paths (Chronos-2 added, with an 80 % interval in `forecast.json` that the panel should shade), and the processing panel has a sixth scenario, the weather-model troposphere. See [forecast.md](forecast.md#troposphere-the-january-to-october-fit-and-chronos-2-14-nov-2026-1930).

## Compare explains the two radars (15 Nov 2026)

Choosing Compare opens a panel, "How the two radars differ, and how they fill each other's gaps", built from the products: wavelength, look side, the track pair shown (NISAR 129A with Sentinel-1 007D: same east-west sensitivity), number and spacing of acquisitions, period, grid, reference, pixel noise and, for a zone, usable pixels. It then lists what each adds: Sentinel-1 fills NISAR's January to June gap, NISAR adds earlier dates, the opposite look sides together separate up-down from east-west motion, and the two wavelengths behave differently over vegetation and time.

The old "Still inconclusive" list is replaced by **What already agrees** (whether both radars show the zone moving the same way over the common window, with both rates) and **What would settle it** (more dates, larger comparison areas, one stated assumption about the motion being vertical, and the flagged 094D track). The automatic check still says inconclusive where its tolerance is too wide; the page now says that this is noise, not contradiction.

## Layout v5: full remake, front end only (15 Nov 2026)

Alexandru's specification: four elements, cream background (#F4ECDB), very dark brown (#2A1A0F) for text and lines, Bookman Old Style, square corners everywhere, no pop-ups. The pipeline and `products/` are unchanged; the page only reads them.

1. **Toolbar** (6 % of the height): "Dancing on Salt" on the left; a rectangular "Satellite" setting on the right whose options (NISAR, Sentinel-1) open downward on hover, invert on hover and stay inverted when selected.
2. **Map** (70 %): satellite imagery, the town boundary, and the measurement dots of the selected satellite at the selected date (Sentinel-1: the longest series, January to October 2026, the track with the most measured points; NISAR: 129A).
3. **Timeline** (24 %): a toolbar (a quarter) with "Time unit" (Years, Months; options open upward) and a graded line from 2020 to 2026. The selected period is a raspberry rectangle at 70 % opacity; the map shows the last acquisition inside it.
4. **Menu** (right half, only after a click on the map): a graph (half of its height) of the median line-of-sight change of the dots within 500 m of the click, Y from the lowest to the highest value, a faint dashed 0 mm line; a legend (a tenth of its height) with the square colour scale, the area's median rounded down, and "1 cm on screen = … on the map". Escape closes it.

**Not in this front end** (the data and scripts behind them still exist): the context strip and zone chips, Investigate Zone 4, Copy view link, Reset to site, the Coverage and Compare views and the comparison panel, the split-screen Compare map, processing runs and windows, the Chronos-2 forecast and its slider, stations and their panels, the checks and About panel, EGMS context, the track switch (129A/094D, 029A/007D), Romanian, the Rate view, the basemap and opacity settings, acquisition marks on the timeline, the NISAR gap filler, table export, play, and link (hash) state.

**15 Nov 2026, later:** the previous page (before layout v5) is live again at Alexandru's request. Layout v5 was then removed from the repository as well (Alexandru: forget that change).

## The menu: pressing on the map (15 Nov 2026)

Pressing on the map opens **the menu**, a panel on the right that takes the whole map height and half the app's width (the map shrinks to the left half). A zone button opens that zone; anywhere else opens the area around the press, a 1 × 1 km square outlined in blue on the map. The menu holds:

- **Graph** (top half): "How the ground moved here (mm)": the zone's series, or the median of the measured points inside the square, over time. The Y axis runs from the lowest to the highest value; 0 mm is a faint straight line; the line breaks across periods without acquisitions (NISAR's January to June gap, shaded "no data"); the date shown on the map is highlighted. One sentence explains the sign.
- **Legend** (bottom 15 %): the colour gradient with its mm values, and "1 cm on screen = N m on the map" for the current zoom.

The floating legend card and the pop-up on a dot are removed. The close button or Escape closes the menu. The zone chips above the map still open the detailed zone panel.

**Menu as a dashboard (15 Nov 2026, later):** the menu now uses the app's card style. Cards: line-of-sight change (smaller chart, gaps hatched), "What the forecast says" (Chronos-2 with its 80 % range for the one series it is made for, Zone 4 on Sentinel-1 029A; elsewhere it says so and offers a button to that series), and "Which way the ground moves" (experimental up-down and east-west arrows from NISAR's two tracks, `nisar/up_east_points.json`, written by `export.py` from `split.py`'s output), with the uncertainty drawn as a dashed circle, a plain sentence marked unconfirmed (the descending track failed its sign check), and "Not a building-safety assessment". The area outline snaps to the cells of the measured points, so it matches the dots at any zoom. The legend stays at the bottom.
