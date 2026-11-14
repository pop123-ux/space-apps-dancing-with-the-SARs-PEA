# products/ (what the page reads)

`products/<site>/` is written **by scripts only**: export.py (06), validate.py (05) and calibrate.py (04).
The page reads these files and nothing else. The field-level contract is [docs/contract.md](../docs/contract.md),
which is DRAFT until the Lead and the app developer freeze it at hour 2.

| Folder | What | Written by |
|---|---|---|
| `ocnele_mari/` | real data (D-001) | the pipeline |
| `demo/` | synthetic known-answer run | the pipeline on the `demo` site |
| `mock/` | invented values for building the page | `python mock_products.py` |
| `index.json` | sites for the picker | export.py / mock_products.py |

Check a folder with `python checkpoint.py <site>`. Anything with `synthetic: true` must show the
"simulated, not data" banner on the page.
