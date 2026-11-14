# Dancing on Salt · Ocnele Mari

Sentinel‑1C/D VV Burst InSAR from ASF HyP3 is the measurement source. Contains modified Copernicus Sentinel data 2026, processed via ASF HyP3. All 58 jobs succeeded. Fits use 29 pairs and 16 dates per track. The analysis uses the starter kit's four zone outlines. Check permission before publishing those outlines outside the team.

## Repository layout

- `analysis/` has both tracks' per-epoch displacement grids, LOS slope maps, fit summaries and exploratory geometry outputs.
- `provenance/` has the original 58-job request, product filenames, links to all 58 exact ZIPs, SHA-256 checksums and the source burst catalog. HyP3 links expire. If that happens, regenerate the same job definition in HyP3 or use the team's preserved raw archives.
- `scripts/` downloads/verifies inputs and reproduces the analysis.
- `docs/TEAM_HANDOFF.md` has the work plan and data inventory.

From the repo root, run `python scripts/download.py` with Python 3.11 or newer. Use an environment with GDAL Python bindings, NumPy, pyproj and matplotlib for `python scripts/fit.py raw analysis` and `python scripts/compare.py analysis`. The fit and download scripts run on CPU.

The 58 raw ZIPs total about 3.7 GiB and belong in shared storage. The Git checkout contains their exact retrieval manifest and checksums. The raw folder is ignored by Git. Only browser-ready layers and the zone JSON belong in the UI deployment.

Run commands from the `sentinel1/` directory. To recover the exact original fitted NPZ grids without refitting, run `python scripts/restore_grids.py`. The script validates both reconstructed files against SHA-256 before writing them.
