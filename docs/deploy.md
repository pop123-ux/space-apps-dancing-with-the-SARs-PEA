# Hosting the page on Vercel

**Owner:** 06 · App developer (Darius)

The page is static: `index.html`, `app/` and `products/<site>/`, with no build step. `vercel.json` tells Vercel exactly that, and `.vercelignore` leaves out the pipeline code, the raw grids and the notebooks (the page never reads them). Added 14 Nov 2026.

## One-time setup (one person, about 3 minutes)

1. Sign in at [vercel.com](https://vercel.com) with GitHub.
2. **Add New → Project →** import `pop123-ux/space-apps-dancing-with-the-SARs-PEA`. If the repository is not listed, grant the Vercel GitHub app access to it.
3. Framework preset **Other**; leave the build command empty and the output directory `.` (both come from `vercel.json`). **Deploy.**
4. Share the production URL (`https://<project>.vercel.app`) with the team.

## What the team gets

- Every merge to `main` redeploys the production URL in about a minute.
- Every pull request gets its own preview URL in a comment, so a change can be checked on phones before merging.
- On the Hobby plan, preview URLs are protected by Vercel login by default; the production URL is public to anyone with the link. To let teammates open previews without a Vercel account, turn off **Settings → Deployment Protection → Vercel Authentication**, or use the production URL only.

## Rules

- Hosting changes nothing about the honesty rules: the page shows only `products/`, written by the pipeline.
- No secrets go into Vercel: the page needs none.
- Deploying is a team-visible action: announce the URL in the team chat and log it in `DECISIONS.md`.
