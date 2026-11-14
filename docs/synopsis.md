# Synopsis for the team

Version 1, Sat 14 Nov 2026. The full plan is in [overview.md](overview.md). The build details, per role, are in [build-spec.md](build-spec.md).

**Dancing on Salt**

Under Ocnele Mari, in Vâlcea, salt is dissolved out of the ground as brine. The caverns it leaves behind have collapsed before: Țeica and Câmpul II in 2001, and Câmpul I in 2009. Today the ground still sinks slowly. Europe's ground-motion service, EGMS, puts it at up to about 25 mm a year from 2019 to 2024.

NISAR, the new NASA–ISRO satellite, carries an L-band radar. It passes over every 12 days, and its data are free. Over Ocnele Mari it has given us 22 pairs of images: a winter window from November 2025 to January 2026, and a summer-to-autumn window from June to October 2026. Nothing was recorded in between, so there are five months with no data.

We're building a web page that shows anyone what NISAR sees there. It opens on the town. Zoom out, and Romania appears as a blurred background, because only this place is data. A slider plays the ground through time, one frame per pass, and the five-month gap says "no data" rather than pretending. Pins on the map show what NISAR says, what nearby GPS stations say, and whether the two agree. A red pin says why they don't.

The honest part matters most. Our advisor's dress rehearsal on 12 November ran a full pipeline on the real data. It worked, but it found that one pixel on its own is too noisy, at 37 to 51 mm a year, to see a 25 mm a year signal. So we work with whole zones rather than single pixels. We show a rate only where it beats its error, and we check everything against EGMS, the stations and a second radar, Sentinel-1. If the zones still don't beat their error, the story becomes "what NISAR's first months can and cannot see": that is honest and useful.

**The six roles:**

- **01, Mario:** story, video, submission and checkpoints.
- **02 and 03, Alexandru and Eric:** fetch the radar data and turn it into rates.
- **04, Matei:** ties the radar to a real reference frame.
- **05, Paul:** checks everything and is our own red team.
- **06, Darius:** builds the page.

**Still to decide** (by hour 2): the story framing, whether we reuse the advisor's code, and the frozen file formats. They are listed in [build-spec.md](build-spec.md#open-team-decisions).
