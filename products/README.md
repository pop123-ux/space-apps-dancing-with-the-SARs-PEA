# products/

**Owner:** 06 · App developer (Darius)

`products/<site>/` is what the page reads, and nothing else. Scripts write it, never people: `export.py` (06), `validate.py` (05) and `calibrate.py` (04). The file contracts are in [docs/build-spec.md](../docs/build-spec.md#file-contracts), and 01 and 06 freeze them at hour 2.

| Folder | What | Written by |
| --- | --- | --- |
| `ocnele_mari/` | Real data (D-001) | the pipeline |
| `demo/` | The synthetic known-answer run | the pipeline on the `demo` site |
| `mock/` | Invented values for building the page | `python mock_products.py` |
| `index.json` | Sites for the picker | `export.py`, `mock_products.py` |

Check a folder with `python checkpoint.py <site>`. Anything with `synthetic: true` shows "Simulated, not data" on the page.

For the current real-data integration snapshot, follow the [06 implementation handoff](../docs/ui.md#06-implementation-handoff--14-november-2026). Its exported products include Sentinel-1 measurement overlays and series for both fitted windows, NISAR catalog coverage and pending states for NISAR displacement and EGMS history. Use the supplied exporter to reproduce the snapshot.
