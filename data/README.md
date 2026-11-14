# data/ (local only, never committed)

Everything here is git-ignored except this file. Scripts create the layout below; nobody writes here by hand except the
EGMS file (05).

```
data/work/<site>/
  refs/                  refs.py (04): model_euvem.csv, stations.csv · egms_up.csv (05, from the EGMS L3 Up tile)
  <track>/               fetch.py (02): meta.json, geom.npz, dem.npz, <ref>_<sec>.npz per pair
                         stack.py (03): ts.npz · calibrate.py (04): cal.npz
  up_east.npz            split.py (03)
  s1/                    hyp3_order.py (05): jobs.json and Sentinel-1 products
  truth.npz              synthetic site only (fetch.py --synthetic)
```

Ocnele Mari is about 1.3 GB for both tracks (58 MB per pair). Third-party data stay here; the repository links and
credits them (docs/data-sources.md).
