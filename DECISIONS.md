# Decisions

This file has one line per decision taken without the whole team, by a person or by their Claude Code session. The format is `HH:MM | role | decision | options considered | why`. Times are `Europe/Bucharest` (assumed; 01 confirms `EVENT_TZ` in `STATUS.md`).

Team decisions, and any change to a decision in `docs/build-spec.md`, go in the build spec's open-decisions table and change log instead.

A decision recorded here is not a question. Nobody blocks on one. If a line looks wrong, raise it at the next checkpoint.

## Sat 14 Nov 2026

12:45 | 02/03 (Claude Code) | Mirror the advisor kit's script names, one-owner-per-script split and products contract, with stubs instead of its code | copy the kit's code in; a new layout; mirror with stubs | O-03 (adopt or rebuild) is open; stubs keep both paths open and nothing undeclared enters the repo
12:45 | 02/03 (Claude Code) | Keep the advisor kit out of the repository | commit it as `reference/`; commit only its docs; leave it out | It is 207 MB with data; it is prior work, declared in `CITATIONS.md`; the team decides on O-03
12:45 | 02/03 (Claude Code) | `mock_products.py` writes invented values on the real NISAR acquisition dates, with the January to June gap | made-up dates; real dates | The page has to handle the real gap from the start
12:45 | 02/03 (Claude Code) | Every decision beyond D-001 and D-002 is written as "proposed" until the hour-2 review | write them as fixed; proposed | The user asked for no final decisions; the build spec's freeze rule takes over at hour 2
13:30 | 02/03 (Claude Code) | Restructure the documents into the style of `dmanpark/dancing-with-the-sars`: `STATUS.md`, `DECISIONS.md`, `CITATIONS.md`, `docs/{synopsis,overview,build-spec,data,rehearsal,AI_USE}.md`, `prompts/{setup,early-tests,build}.md` | keep `BUILD.md` and `roles/`; restructure | The user asked to follow that style. Per-role run sheets became sections of `docs/build-spec.md`, so there is one source of truth
13:30 | 02/03 (Claude Code) | Keep the pipeline as one script per owner at the repository root, not a Python package | a package as in the reference repo; flat scripts as in the advisor kit | Six owners, one file each; drop-in with the kit if O-03 adopts it
13:30 | 02/03 (Claude Code) | Commit `data/scenes/ocnele_mari_gunw.csv`, the 22 pairs from CMR | keep it in docs only; commit the list | A small query output, like the reference repo's `data/scenes/`; 02 checks it in T2
13:30 | 02/03 (Claude Code) | Propose up and east only on the common window (20 Jun to 21 Oct 2026) | mix the windows; common window only | Mixing different months in one solve mixes seasons; proposed, 03 confirms at hour 2
13:30 | 02/03 (Claude Code) | Add a GitHub Actions workflow that runs `pytest -q` on every push and PR, with no Pages deploy yet | no CI; CI plus a Pages placeholder; CI only | The user said no `index.html` yet; 06 adds Pages when the page exists
