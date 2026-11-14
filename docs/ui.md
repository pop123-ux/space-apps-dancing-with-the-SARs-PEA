# The page: satellite switch and views

**Owner:** 06 · App developer (Darius)

Version 1, Sat 14 Nov 2026. This design implements **D-004** (locked): we fit both NISAR and Sentinel-1, and the page lets anyone switch between the two satellites and look at the same subsidence in several ways. It also keeps D-002 (the map opens on Ocnele Mari; Romania is blurred context).

The layout and labels below are a design for 06 to build. The data each control needs is in the file contracts in [build-spec.md](build-spec.md#file-contracts), and `python mock_products.py` already writes both satellites, so the switch can be built now.

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
| **NISAR** (default, the brief asks for NISAR first) | NISAR layers for the chosen track | NASA–ISRO · L-band, 24 cm · 12-day repeat · beta/provisional |
| **Sentinel-1** | Sentinel-1 layers for the chosen track | ESA / Copernicus · C-band, 5.5 cm · 6-day repeat · contains modified Copernicus Sentinel data 2026, processed by ASF HyP3 |
| **⇆ Compare** | Both at once: a swipe divider on the map (left NISAR, right Sentinel-1), both series overlaid on the charts | "Same months only: 7 Jul to 4 Oct 2026" |

- **Track buttons** change with the satellite: NISAR `129A ↗` / `094D ↘`; Sentinel-1 `029A ↗` / `007D ↘`. In Compare, each side keeps its own track, ascending with ascending by default.
- **The view and the date stay** when you switch satellites. If the other satellite has no data at that date, the map shows "No Sentinel-1 acquisition on this date: nearest is 2026-08-24" and snaps only when the user agrees. It never snaps silently.
- **A button for a satellite with no products yet** is disabled with a one-line reason ("Sentinel-1 layers not exported yet"). It is never hidden.

## Control 2: the view switch

Five views of the same problem. Each works for one satellite, and each except Coverage works in Compare.

| View | What you see | One satellite | Compare | Reads |
| --- | --- | --- | --- | --- |
| **Change** (default) | Cumulative line-of-sight change since the track's first date, played with the slider | Frames for that track | Swipe; each side shows its acquisition nearest the slider date, and names that date | `sensors.<s>.frames` |
| **Rate** | Line-of-sight slope in mm/yr, labelled "annualized short-window slope". Pixels with \|rate\| < 2σ greyed out | The track's rate layer | Swipe | `sensors.<s>.layers` (`los_<track>`) |
| **Zones** | One chart per salt zone: median mm per date with contributing-pixel counts. The outer reference band is drawn as a grey line, and null dates are gaps | That satellite's tracks | Both satellites on one chart, colour plus marker shape per satellite | `series.json` (`kind: zone` and `control`) |
| **Agreement** | Per zone, NISAR next to Sentinel-1 over the common window, with intervals, plus the station pins and EGMS history as context. Each zone is marked "agree", "disagree" or "not testable", with the reason | Not available (needs both) | The home of this view | `series.json`, `checks.json` (check 8), `stations.geojson` |
| **Coverage** | A timeline: one row per satellite and track, one dot per acquisition. The NISAR gap (18 Jan to 23 Jun 2026) is hatched and the common window highlighted | Always shows both, so the gap is visible | Same | `sensors.<s>.frames.<t>.dates`, `gaps` |

**Up and east (experimental).** A checkbox, off by default. When on, the map shows the vertical and east–west layers flagged `experimental: true`, with a banner: "Derived assuming no north motion; reference and atmosphere not resolved." It follows the Sentinel-1 handoff rule to keep derived components out of the main view.

## Honest comparison rules

Compare only shows two satellites side by side when what it shows means the same thing. 03, 04 and 05 own the numbers; the page enforces the labels.

1. **Same months.** Compare and Agreement use only the common window, 7 Jul to 4 Oct 2026 (`manifest.common_window`). Dates outside it are dimmed.
2. **Same reference.** NISAR is tied to a GNSS model (04) and Sentinel-1 to surrounding terrain. Until the references match, Agreement compares **zone minus outer reference band** for both, and says so. Decision O-19 sets the final rule.
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
#sat=nisar|s1|compare&track=129A&view=change|rate|zones|agreement|coverage&date=2026-08-22&exp=0|1
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

- **If a satellite's products aren't ready:** its button is disabled with the reason, and the page works with the other one.
- **If Compare isn't ready by hour 36:** keep the switch (one satellite at a time) and the Coverage view, and drop the swipe.
- **Never cut:** the switch itself, the gap labels or the comparison rules above.
