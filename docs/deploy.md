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
- Preview URLs are protected by Vercel login by default; the production URL is public to anyone with the link. To let teammates open previews without a Vercel account, turn off **Settings → Deployment Protection → Vercel Authentication**, or use the production URL only.

## Rules

- Hosting changes nothing about the honesty rules: the page shows only `products/`, written by the pipeline.
- No secrets go into Vercel: the page needs none.
- Deploying is a team-visible action: announce the URL in the team chat and log it in `DECISIONS.md`.

## The live setup (checked 15 Nov 2026, Matei's session)

Everything the site serves comes from this repository: Vercel clones `main` and serves it with no build step. Checked: the production deployment was built from commit `cdea8e9` (the head of `main` then), and `index.html`, `app/` and `products/ocnele_mari/` on the live site are byte-identical to the repository. What lives only in Vercel is the project's configuration, recorded here so the repository describes it.

| Setting | Value | Where it is set |
| --- | --- | --- |
| Team | **PEA** (`pea-2c204aea`, Pro plan) | Vercel |
| Project | `pea-dancingwiththesars`, production URL https://pea-dancingwiththesars.vercel.app | Vercel |
| Git | `pop123-ux/space-apps-dancing-with-the-SARs-PEA`, production branch `main` | Vercel |
| Build | none: build command empty, output directory `.`, no framework | `vercel.json` (overrides the dashboard, which still says "Python") |
| Files left out | pipeline code, raw grids, notebooks, tests | `.vercelignore` |
| Caching | `app/` and the page: no-cache; `products/`: 5 minutes | `vercel.json` |
| Environment variables | none (the page needs no secrets) | Vercel |
| Deployment protection | previews need a Vercel login; the production URL is public | Vercel |
| Deploy hook | "PEA hook", builds `main`. Its URL is a secret: it is stored only in Vercel and as the GitHub secret `VERCEL_DEPLOY_HOOK`, never in this repository | Vercel and GitHub |

**Why the deploy hook exists.** Vercel blocks a Git deployment when it cannot match the commit author to a team member allowed to deploy ("the commit author doesn't have permission to create deployments for this project"); three pushes by 47Matei were blocked this way on 15 Nov. A build started by the deploy hook is not subject to that check. `.github/workflows/vercel-deploy-hook.yml` calls the hook on every push to `main`. If a push does not go live within a few minutes, check that the GitHub secret is set, or have a team member with the Vercel CLI trigger the hook (`vercel deploy-hooks ls --project pea-dancingwiththesars --scope pea-2c204aea` lists it).

**For each teammate, once:** connect your GitHub login to your Vercel account (Account settings → Authentication). Then your own commits deploy directly, without the hook.
