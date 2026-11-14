# Sentinel-1 full-window fit

**Owner:** 03 · InSAR analyst (Alexandru, Eric)

All 132 new ASF HyP3 jobs succeeded. This fit combines those products with the 58 original interferograms (95 pairs and 49 acquisition dates per track). The all-date per-pixel connectivity rule is identical to the July–October baseline.

Zone 4 ascending is sensitive to processing in the extended window. The baseline trend is negative, the elevation-corrected trend is positive, and the strict run has only two pixels. No descending salt-zone pixels connect across every acquisition. Do not interpret missing zones as zero motion. The matched-geometry diagnostic uses the July–October common window but requires pixels surviving the full-window inversion; no salt zone qualifies. Use the original July–October fit for the documented shorter-window result and do not silently substitute it on the extended timeline.

## In this repository (14 Nov 2026)

Committed from the ChatGPT-hosted bundle `Ocnele_Mari_Sentinel1_Jan_Oct_Fit.zip`. Grids are packed in `../assets_jan_oct/` (`python scripts/restore_grids.py`). Job provenance is in `../provenance/hyp3_jobs_jan_oct_status.json`: 132 job names and IDs, all SUCCEEDED, but no granule names, links or ZIP checksums, so this fit cannot be rerun from the repository alone. The summary was written by the single-network version of `fit.py` (one date group, so the numbers match the group-aware version; empty zones are absent rather than marked). The weather-model scenario has not been applied to this window.
