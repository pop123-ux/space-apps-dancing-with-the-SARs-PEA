# AI use

This file records which AI tools this project used, before and during NASA Space Apps 2026, and for what. The submission requires it (Space Apps writes "SI"). **Everyone keeps it current:** add a line when an AI tool produces code, text, figures or analysis that ends up in the project, and say what a person checked by hand. 01 turns it into the submission note.

## Tools

- **Claude Code** (Anthropic): repository skeleton, documents and code, run by each team member on their own role (see `prompts/build.md`).
- **ChatGPT** (OpenAI): pre-event research summary by 02/03.

We use no generative image, video or audio models. Any diagram is a simple drawing coded from basic shapes, and carries a visible note "Diagram made with AI assistance".

## Before the event (to hour 0)

- **Research summary**, 13 to 14 Nov 2026 (Alexandru, 02/03, ChatGPT). A summary of the advisor's deck and rehearsal kit. Checked by: to fill in.

## During the event

| Date and time | Who (role) | Tool | What it produced | What a person checked |
| --- | --- | --- | --- | --- |
| Sat 14 Nov, about 12:45 | Alexandru (02/03) | Claude Code | The repository skeleton: plan documents, role run sheets, `common.py`, the pipeline stubs (interfaces only, no science), `checkpoint.py`, `run_all.py`, `mock_products.py`, the smoke test. It also checked the NISAR GUNW inventory on NASA CMR. | To fill in: each owner reviews the stub and section for their role |
| Sat 14 Nov, about 13:30 | Alexandru (02/03) | Claude Code | Restructured the documents into the style of a public reference repository (`STATUS.md`, `DECISIONS.md`, `CITATIONS.md`, `docs/`, `prompts/`), and wrote `data/scenes/ocnele_mari_gunw.csv` from CMR. | To fill in |
| Sat 14 Nov, about 13:20 | Matei (04) | Claude Code | `refs.py` (EuVeM2022 and NGL MIDAS download and parsing, distance filter, published rates, synthetic stand-ins with a lying station), `calibrate.py` (model to LOS, tie mask, offset or plane fit with 3σ clipping, model swap, `calib.json`), the VLC2 vertical in `common.PUBLISHED`. Synthetic known-answer runs: offsets −8.81 and −6.02 mm/yr for truths −8.8 and −6.0; plane slope 3.99 for 4.0 mm/yr per 10 km. | To fill in: Matei checks the VLC2 row of Table S3 on the PDF page by eye, and runs `refs.py ocnele_mari` on real data |
