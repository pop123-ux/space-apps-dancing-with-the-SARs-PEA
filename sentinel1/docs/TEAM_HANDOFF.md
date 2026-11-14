# Team handoff

## Scientific baseline

The ascending track 029A spans 7 July–5 October 2026. Descending track 007D spans 6 July–4 October. These values are fitted 90-day line-of-sight changes in mm relative to surrounding reference terrain. Negative means away from the satellite.

| Zone | Ascending | Descending | Interpretation |
|---|---:|---:|---|
| 1 | −8.6 | −5.2 | Away in both baseline fits. Only two descending pixels pass the strict mask and their fit changes sign. |
| 2 | −6.8 | −1.4 | Weak descending result changes sign with reference choice. |
| 3 | No connected series | +0.2 | No dual-track interpretation. |
| 4 | −7.5 | −3.5 | Both signs persist across tested configurations. Magnitudes vary. |
| Outer comparison area | +3.9 | +3.3 | Drift limits the absolute-motion interpretation. |

Zone 4 is the strongest candidate for the demo. Use “line-of-sight motion consistent with localized subsidence relative to nearby terrain.” The vertical/east decomposition is exploratory. The reference was terrain-based and residual atmospheric delay may contribute. No hazard forecast or causal claim follows from this fit.

## Sprint work

| Role | Owner and action | Handoff |
|---|---|---|
| 01 · Lead/story | Freeze the scientific claim and attribution. Prepare a short demo from Zone 4 through the track and coverage controls. Confirm permission to publish the starter-kit zone outlines or replace them with team-defined outlines and rerun. | Approved wording, source credits, demo path. |
| 02 · Data engineering | Alex leads. Mirror all 58 ASF products in shared storage before links expire. Verify checksums and metadata. Record burst, platform, acquisition dates and missing support. | Reproducible raw inventory with exact checksums. |
| 03 · InSAR analysis | Alex owns pipeline implementation and any modeling. Eric leads EDA and interpretation. Review closure residual maps, track overlap, and reference/coherence sensitivity. Refit the inversion after dropping influential acquisitions if the graph remains connected. | Two track stacks, zone and comparison histories, and a statement of how results change under each check. |
| 04 · Geodesy | Confirm LOS convention and look-vector directions. Check candidate reference areas and quantify the effect of moving the reference. Review the east/up projection and its assumption of negligible north motion. | Signed units, reference rationale, and a decision on whether to expose the derived components. |
| 05 · Validation | Compare EGMS Ortho Up and East–West for historical context. Then look for GNSS or another SAR mission with comparable 2026 dates and geometry. Compare aligned areas and periods. | Evidence table with source, dates, coverage, agreement and limits. |
| 06 · App | Convert rasters to web map assets with correct georeferencing. Display tracks separately with shared legends, real acquisition dates and explicit coverage gaps. Show zone histories and outer comparison in mm. | Testable map, slider and charts wired to the science outputs. |

Start with 02, 03, 04 and 05 in parallel. Role 06 can build against the current JSON immediately. Freeze the UI numbers after the geodesy and validation reviews. For charts, use ISO dates, contributing-pixel counts and explicit nulls for unsupported cells. Keep the first acquisition reference and positive-toward convention visible. Optional annualized mm/yr values need a short-window label. Keep provisional vertical/east outputs out of the main UI.

## Data inventory

- Official Sentinel‑1 inputs: all 58 ZIPs downloaded and indexed in the raw manifest. The live workspace also contains the files under `s1/`.
- Current analysis: both track grids and maps, zone histories, sensitivity fits, and exploratory matched geometry are all included.
- Latest EGMS: the official 2020–2025 Ortho Up and East–West ZIPs for tile E54N25 were located. No completed downloads or fits were verified. Search EGMS Explorer for the tile after signing in.
- Historical EGMS: the 2019–2023 Up extract is available inside the private rehearsal material. Its previously calculated baseline had medians of −5.0 mm/yr in the zones (18 points) and −0.9 mm/yr nearby (5,174 points). Use this as background and retrieve a fresh official extract for a published comparison.
- Private starter-kit material: the planning PDF, original ZIP with rehearsal radar data and scripts, and derived NISAR overlap map remain a team reference. The NISAR observations did not enter the Sentinel‑1 fit.
- No independent same-period confirmation has been fitted.

## January–October extension and frontend

A further 132 HyP3 jobs succeeded. The combined fit has 95 pairs and 49 acquisition dates per track. In the extended ascending Zone 4, the fitted change is −4.07 mm at baseline and +4.48 mm with elevation correction. No descending salt-zone pixel spans all 49 dates under the fit’s connectivity rule. The shorter-window results above describe July–October. The [06 implementation handoff](../../docs/ui.md#06-implementation-handoff--14-november-2026) links the verified overlays, time series, job receipts and checksums. It records the pending NISAR displacement and EGMS historical extract.
