# 01 · Lead & story — Mario

**Mission.** Keep the team on one story and one map, and hand in on time. You own scope, the cut lines and the checkpoints, plus the story, the video and the submission.

**You own:** `checkpoint.py` (works), `README.md`, `BUILD.md`, `docs/story.md`, `docs/decisions.md`, `docs/submission.md`, the video and the project page. You hold `docs/contract.md` jointly with 06.

## Hour by hour (DRAFT)

| Hours | Do | Done when |
|---|---|---|
| 0–2 | Fill in hour 0 and the deadline (O-04). Read the 13 Nov guide aloud: prior work, format, judging (O-02). Settle O-03 (adopt the kit or rebuild). Make sure everyone has an Earthdata login and has run `python test_skeleton.py`. **Freeze the contract with 06 at hour 2** (O-10). | Everyone has seen `ok:`; the contract is frozen; O-02/O-03/O-04 are recorded |
| 2–6 | Decide the story framing with the team (O-01). Write `docs/story.md`: one sentence per stop. Draft the first ten seconds of the video. Reassign the freed Praid slots (O-15). | The story fits on one screen |
| 6–18 | **Checkpoint at hour 12**: `python checkpoint.py ocnele_mari`, read every WARN/FAIL aloud, give each an owner and a verdict (fix, cut, explain). The advisor joins. Video script. | Each warning has an owner |
| 18–30 | **Checkpoint at hour 24**: same procedure. Rough cut of the video on the mock or demo site, with the banner visible. | Rough cut exists |
| 30–40 | Write-up, credits, AI-use note ([ai-use.md](../docs/ai-use.md)), prior-work list ([prior-work.md](../docs/prior-work.md)). | Text final |
| 40–48 | **Freeze at hour 40**: no number changes. Final video, project page, submit ([submission.md](../docs/submission.md)). | Submitted before the event closes |

## Commands

```bash
python test_skeleton.py                 # everyone, before every push
python checkpoint.py ocnele_mari        # hours 2, 12, 24, 40; exit 1 = the page would break
python checkpoint.py mock               # the invented set (python mock_products.py first)
python run_all.py ocnele_mari --from calibrate   # rerun downstream after someone changes the tie
```

## Starting points

- The rehearsal verdict (BUILD.md §3) shapes the story. Ocnele Mari moves at about −25 mm/yr at most, while per-pixel noise is 37–51 mm/yr. Zone-level, honest framing is the safe ground. **Never quote −250 mm/yr**: our copy of the deck still has it.
- The data are "a winter window and a summer–autumn window", not "a year". The deck and story must say so.
- The products are beta/provisional. Say so on the page and in the video.

## Decisions you drive

O-01 story · O-02 guide · O-03 kit · O-04 hour 0 · O-10 contract · O-12 HAR1 in the app · O-13 quoting Muntean · O-15 freed slots. Record each one in `docs/decisions.md`.

## You must be able to answer

- What is new in 48 hours, and what is prior work? List every reused file.
- Which AI tools were used, for what, and what did a person check by hand?
- Why should a non-specialist care, in one sentence?

## Done when

The submission checklist is ticked, the frozen build passes the checkpoint, and the video is under the guide's limit with the hook in the first ten seconds.
