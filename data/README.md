# data/

**Owner:** 02 · NISAR data (Alexandru, Eric)

Everything here stays local and git-ignored, except this file and the small query lists in `data/scenes/`. Scripts create the layout below. Nobody writes here by hand, except 05 for the EGMS file.

```
data/scenes/ocnele_mari_gunw.csv   committed: the 22 NISAR GUNW pairs over the town (NASA CMR, 14 Nov 2026)
data/work/<site>/
  refs/                  refs.py (04): model_euvem.csv, stations.csv. egms_up.csv comes from 05 (EGMS L3 Up tile)
  <track>/               fetch.py (02): meta.json, geom.npz, dem.npz, <ref>_<sec>.npz per pair
                         stack.py (03): ts.npz. calibrate.py (04): cal.npz
  up_east.npz            split.py (03)
  s1/                    hyp3_order.py (05): jobs.json and Sentinel-1 products
  truth.npz              synthetic site only (fetch.py --synthetic)
  logs/                  logs of long jobs
```

Ocnele Mari is about 1.3 GB for both tracks, at about 58 MB per pair (rehearsal, 12 Nov 2026). Third-party data stay here; the repository links and credits them in `CITATIONS.md`.
