# Build your role: Claude Code prompt

**Owner:** 01 · Lead and story (Mario)

## How to use this (for the team)

**When.** From hour 0, on your own laptop, after `prompts/setup.md`.

**Start it** in the repo folder, on your role branch:

```bash
git switch main && git pull && git switch -c r0N/<task>
claude
```

Then say: **"Read prompts/build.md. I am role 0N."** (01 Mario, 02 or 03 Alexandru and Eric, 04 Matei, 05 Paul, 06 Darius.)

**If it stops or the window closes:** `claude --continue`, then say **"Continue prompts/build.md for role 0N from STATUS.md."**

**What only a person does.** Logins and tokens; anything needing `sudo`; publishing outside GitHub (uploading the slides, the Space Apps form); team decisions; merging into `main` after review.

---

## Your job

Build **your role's part** of Dancing on Salt exactly as your section of `docs/build-spec.md` describes. Use the files, formats and fixed numbers it gives, and hand off on time to the roles that read your files. Six people are doing the same thing at the same time, each with their own session. Stay inside your role.

## Don't stall: take the recommended option

When you would ask your human a question that is not a team decision, choose the option you would have labelled "(Recommended)". Write one line to `DECISIONS.md` (`HH:MM | role | decision | options considered | why`) and keep going. When the recommended option isn't obvious, decide in this order:

1. A decision or file contract in `docs/build-spec.md`.
2. A change logged at the end of `docs/build-spec.md`, or a fallback named in `docs/overview.md` (risks, cut ladder) or `prompts/early-tests.md`.
3. Whatever keeps Tier 1 on schedule.
4. The simpler option.
5. The option that is easier to undo.

**Team decisions are not yours.** For the open decisions (O-01 to O-17 in the build spec), present the options with their trade-offs to your human, who takes them to 01.

## Hard stops: the only times you wait

Send one short message saying exactly what the person must do, then wait. Keep working on anything that doesn't depend on the answer.

1. **A login, password or token.** Never ask for one in the chat.
2. **`sudo` or administrator rights.**
3. **Publishing outside GitHub,** or merging to `main`.
4. **Destroying what you can't recreate,** or force-pushing.
5. **Another role's file or a frozen decision needs to change.** Write the proposal; the owner or the team decides.

## Rules that override everything else

1. **Prior work.** No code from the advisor's rehearsal kit or earlier studies goes in unless the team decided O-03 that way. Whatever is reused gets a row in `CITATIONS.md` (Prior work) in the same commit.
2. **Honest numbers.**
   - Every number on the page, on the slides and in the submission comes from `products/ocnele_mari/`, written by the pipeline.
   - Never hard-code a number, round it to flatter, or invent one.
   - Never flip a sign or drop data to pass a check.
   - A failed check is reported as failed, with the reason.
   - If a real bug forces a change after a result exists, fix it, mark it "changed after results" in `DECISIONS.md`, and rerun everything downstream (`python run_all.py ocnele_mari --from <step>`).
3. **No silent placeholders.** Mock and synthetic outputs carry `synthetic: true`. Before submitting there must be zero matches for `___`, `TODO`, `TBD` or `computing` in the page, `SUBMISSION.md` and the slides.
4. **Data and credentials.**
   - Never commit `data/work/`, `.h5`, `.nc`, `.npz`, `.zip`, `.env` or tokens.
   - Before every push, run `pytest -q` and `git ls-files | xargs du -k | sort -n | tail -3`, so nothing over 50 MB goes in.
   - Grep the diff for `EARTHDATA_TOKEN=`, `password` and `token=`.
5. **AI disclosure.** Add a row to the log in `AI-DISCLOSURE.md` for anything substantive you produce. No generative image or video models.
6. **Writing.** Plain sentences, no em-dashes, units on every number, and dates on anything that can change.
7. **Leave the plan alone.** Don't edit `docs/overview.md`, `docs/build-spec.md` (apart from 01's change log), `prompts/`, `INFO.md` or another role's files.

## Read first

1. `CLAUDE.md`.
2. `STATUS.md`: hour 0, the gates, what is waiting on whom. If your role's row shows work in progress, you are resuming. Read `DECISIONS.md` and `git log -10`, then continue from the first unfinished step.
3. `docs/schedule.md`: **your role's column**, hour by hour, and the gates.
4. `docs/build-spec.md`: the decisions, the file contracts, and **your role's section**.
5. `docs/data.md` and `docs/rehearsal.md`.
6. Your script's docstring: its inputs, outputs and the known traps.
7. `prompts/early-tests.md`: the tests you own.

## The clock

- Hour 0 and `EVENT_TZ` are in `STATUS.md`. Use `TZ=$EVENT_TZ date` for every time check.
- **Gates:**
  - **Hour 2:** decisions and contract frozen.
  - **Hour 12:** first real rate map and checkpoint.
  - **Hour 24:** checkpoint; Tier 1 numbers exist.
  - **Hour 40:** numbers frozen.
  - **Submit** at least 3 hours before the deadline.
- At each gate, update your row in `STATUS.md` with evidence (file paths, test output, numbers with units).
- If your part slips by more than an hour, tell your human. 01 cuts from the top of the ladder in `docs/overview.md` (Scope and The 48 hours).

## How to work

- **Steps in your section's order.** Run the early tests you own as soon as they can run.
- **Long jobs** (streaming, HyP3) run in the background, logging to `data/work/logs/`. Check on them, and don't sit idle.
- **Commit after each step** on your role branch, and open a PR to `main` when a step's output is ready for others. The owner merges once `pytest -q` passes. 01 reviews PRs touching `common.py` or the contracts.
- **Show evidence:** paste the command output or file path in `STATUS.md`. A claim without evidence is not done.
- **Pull `main` often.** Another role's output may have landed.

## Per role, the first hour

| Role | First hour |
| --- | --- |
| 01 | Hour 0 and `EVENT_TZ` in `STATUS.md`; the guide (O-02); O-03; prepare the hour-2 review |
| 02 | T1 on the venue network; `search()` and T2 |
| 03 | O-05 proposal; read the GUNW notes in `docs/data.md`; prepare `stack.py` against 02's hand-off |
| 04 | `refs.py` downloads; read Table S3 for VLC2 and HORE |
| 05 | Order HyP3 (`hyp3_order.py` or by hand) and log it; start the EGMS tile |
| 06 | `python mock_products.py`; the page shell on `products/mock/` with the D-002 view; Pages |
