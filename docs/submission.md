# Submission checklist · owner 01 (Mario)

**Deadline:** before our event closes (O-04: fill in the exact time). Registration closes 15 November. Check everything against the 13 November guide.

## The eight things the submission must carry

- [ ] 1. Team and event registered before registration closes on 15 November
- [ ] 2. Project page on spaceappschallenge.org, submitted before our event ends
- [ ] 3. Open repository with a licence (MIT ✔); third-party data linked, not copied ([data-sources.md](data-sources.md))
- [ ] 4. A working demo link: the static site on GitHub Pages
- [ ] 5. Video or slides in the format the 13 November guide sets
- [ ] 6. How AI ("SI") tools were used: required ([ai-use.md](ai-use.md))
- [ ] 7. Prior work and advisor help, listed plainly ([prior-work.md](prior-work.md))
- [ ] 8. Data credits: NISAR (NASA–ISRO, ASF DAAC), EGMS, EuVeM2022, NGL, Muntean et al. 2026, Sentinel-1 ([data-sources.md](data-sources.md))

## The score sheet, line by line

These are past years' criteria; check the 2026 sheet.

| Criterion | What we show |
|---|---|
| Impact | Safer salt towns, and a check anyone can rerun from open data |
| Creativity | Satellite and stations checking each other; the ground dancing on a time slider |
| Validity | Rates only where they beat their error; stations held out of the tie; EGMS history |
| Relevance | NISAR first, interactive, open source, hometown context, a human driver |
| Presentation | Story stops, one map, numbers second; a hook in the first ten seconds |

## On the frozen build (hour 40+)

- [ ] `python checkpoint.py ocnele_mari`: contract OK; every WARN and FAIL explained on the page or in `checks.md`
- [ ] The validator has re-run every check on the frozen build ([validation-log.md](validation-log.md))
- [ ] The page works on two phones (slider plays, text readable)
- [ ] The synthetic banner shows on any synthetic or mock site; the video never shows the demo without it
- [ ] "Beta / provisional NISAR products" is stated on the page and in the video
