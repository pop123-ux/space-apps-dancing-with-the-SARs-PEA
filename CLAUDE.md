# CLAUDE.md

Guidance for Claude, and any other AI assistant, working in this repository. All six teammates use an assistant the same way, and these rules keep six parallel sessions from colliding. Humans: this is also the shortest correct summary of how we work.

## 1. Before you touch anything

1. **Find out which role you are working for.** Use the branch name (`r01/…` to `r06/…`) or ask the human. See §3 for the roles.
2. Read [BUILD.md](BUILD.md), then the role's run sheet in [roles/](roles/), then [docs/decisions.md](docs/decisions.md).
3. **Only edit files your role owns** (§3). If the task needs a change in someone else's file, don't make it. Write the proposed change (a diff or a precise description) for the human to hand to the owner.
4. **Don't make team decisions.** If something is OPEN in `docs/decisions.md`, lay out the options with their trade-offs and let the human decide. Only the Lead (01) records decisions.

## 2. The project in 60 seconds

- **Team:** NASA Space Apps 2026, challenge *Dancing with the SARs*, 14–15 November 2026, six people.
- **What:** a static, open-source web page showing how the ground moves at **Ocnele Mari, Romania**, where salt-brine extraction causes collapses and subsidence.
- **Main measurement:** NISAR L-band GUNW interferograms (NASA–ISRO, from ASF).
- **Reference frame:** tied to open GNSS velocity models (EuVeM2022, NGL MIDAS, Muntean et al. 2026).
- **Checks:** held-out stations, EGMS Ortho, Sentinel-1 (HyP3) and a synthetic known-answer stack.
- **Page:** a Leaflet map, a time slider, station pins and story stops.

**What the advisor's rehearsal found** (BUILD.md §3): the data cover two windows with a five-month gap, not a year. The real signal is about −25 mm/yr at most, but per-pixel noise is 37–51 mm/yr. The phase sign is not yet confirmed on real data. The story framing is therefore still OPEN.

## 3. Who owns what

| Path | Owner |
|---|---|
| `checkpoint.py`, `README.md`, `BUILD.md`, `docs/story.md`, `docs/decisions.md`, `docs/submission.md` | 01 · Lead & story (Mario) |
| `fetch.py` | 02 · NISAR data (Alexandru & Eric) |
| `stack.py`, `split.py` | 03 · InSAR analyst (Alexandru & Eric) |
| `refs.py`, `calibrate.py` | 04 · Geodesist (Matei) |
| `validate.py`, `hyp3_order.py`, `docs/validation-log.md` | 05 · Validator (Paul) |
| `export.py`, `mock_products.py`, `index.html` and app assets (when created) | 06 · App developer (Darius) |
| `common.py` | shared: announce changes to the team; the Lead approves the PR |
| `run_all.py`, `test_skeleton.py`, `requirements.txt`, `.github/` | shared: small, announced changes only |
| `docs/ai-use.md`, `docs/prior-work.md` | everyone appends; nobody rewrites others' lines |
| `docs/contract.md` | 01 + 06 together (frozen at hour 2) |
| `products/<site>/` | **written by scripts only, never by hand** |
| `data/` | local only, git-ignored, never committed |
| `INFO.md`, `LICENSE` | leave as they are |

## 4. Hard rules

- **Scope (D-001):** Ocnele Mari only. Don't add Praid, Slănic or other sites. `demo` is not a site: it is the synthetic known-answer test.
- **Map (D-002):** the page opens zoomed on Ocnele Mari. Zooming out shows Romania blurred, as context only.
- **Never commit:**
  - anything under `data/`;
  - tokens or passwords (`EARTHDATA_TOKEN`, `.env`, `.netrc`);
  - raw NISAR, EGMS or Sentinel-1 files;
  - anything from ROMPOS;
  - a verbatim copy of the Muntean et al. 2026 supplement table.
- **Numbers are measured, never invented.** Don't tune a number until it "looks right". Anything mock or synthetic carries `synthetic: true` and shows the banner. **Never quote −250 mm/yr**: it was a factor-10 error in the deck.
- **The contract** ([docs/contract.md](docs/contract.md)) is frozen at hour 2. A change to it needs the Lead and the app developer in the same PR, with `checkpoint.py` and the page updated together.
- **After the hour-40 freeze,** make no change that alters any number in `products/`. Only text, captions, styling and video.
- **The validator is independent.** Nobody else edits `validate.py`, and the validator doesn't edit the science scripts.
- **Follow the science guardrails** (BUILD.md §10, [docs/science-notes.md](docs/science-notes.md)). Above all:
  - no rate shown as a number where |rate| < 2σ;
  - compare zones, not pixels;
  - check the phase sign, don't assume it;
  - everything Eurasia-fixed;
  - north is ignored in the up/east split.
- **Log AI use.** For any substantive AI-generated code or text, append a line to [docs/ai-use.md](docs/ai-use.md): who, which tool, what for, and what a human checked. The submission requires this.
- **Declare prior work.** Reusing code or results from the advisor's rehearsal kit, the salt-events study or any earlier work must be recorded in [docs/prior-work.md](docs/prior-work.md) in the same PR. Don't paste kit code into a script until the team has decided O-03.

## 5. Conventions

| Quantity | Convention |
|---|---|
| LOS rate, cumulative LOS | mm/yr, mm; **positive = towards the satellite** |
| Up / east | mm/yr; up positive (sinking is negative), east positive |
| GNSS and model velocities | Eurasia-fixed, mm/yr |
| Dates | ISO `YYYY-MM-DD`; pair files `YYYYMMDD_YYYYMMDD` (reference_secondary) |
| Tracks | `129A` (ascending), `094D` (descending): three digits plus A or D |
| Time in fits | years since 2026-01-01 |
| Colours | RdBu diverging: red = sinking or away from the satellite, blue = rising or towards it, white = 0. Never red/green alone |
| Processing grid | the product's UTM (EPSG 326xx), 80 m pixels; overlays resampled to lon/lat for the map |

**Code:**

- **Python and layout:** Python ≥ 3.11. One script per step, run as `python <step>.py <site>`.
- **Shared settings:** `import common as C`. Paths, sites, thresholds and helpers come from `common.py`; don't hard-code them.
- **Stubs:** a stub raises `raise C.todo("NN", "what is missing")`. Wrap entry points with `C.run_cli(main)` so a stub exits with code 3 and a readable message.
- **Import cost:** keep top-level imports light where possible, so `--help` works before the environment is installed (`test_skeleton.py` checks this).
- **Output:** print one summary line per track. Exit non-zero on failure.
- **Notebooks:** fine for exploration under `notebooks/<role>/`, with outputs stripped. Never import them from the pipeline.

## 6. Commands

```bash
pip install -r requirements.txt
python test_skeleton.py                     # must print "ok:" before every push
python mock_products.py                     # invented products/mock/ for the page
python checkpoint.py mock                   # contract check (01 runs it at hours 2, 12, 24, 40)
python run_all.py demo                      # synthetic known-answer chain; stops at the first stub
python run_all.py ocnele_mari --from stack  # real data, rerun downstream of a step
python fetch.py ocnele_mari --list          # (02) once implemented: list the GUNW pairs
```

## 7. Git workflow

- Branch per task, named after your role: `r02/fetch-window`, `r04/tie-offset`, `r06/slider`, …
- Run `python test_skeleton.py` before every push. Once the synthetic chain runs end to end, the known-answer test joins it.
- Keep PRs small. The owner merges their own PR once the test passes. PRs touching `common.py` or `docs/contract.md` need the Lead's review.
- Pull `main` often. Never force-push `main` or rewrite someone else's branch.
- Fill in the PR template (`.github/pull_request_template.md`): role, contract touched, numbers changed, AI use logged.

## 8. Where things are

```
BUILD.md · CLAUDE.md · README.md · INFO.md (site notes, RO)
common.py                     shared settings and helpers
refs.py fetch.py stack.py calibrate.py split.py validate.py hyp3_order.py export.py   pipeline (stubs)
checkpoint.py run_all.py mock_products.py test_skeleton.py                           working tools
roles/0N_*.md                 one run sheet per role
docs/                         decisions, contract, science notes, data sources, prior work, AI use, story, submission, validation log
products/<site>/              what the page reads (scripts write it)
data/                         local data, git-ignored
```
