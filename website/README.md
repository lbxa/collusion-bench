# Collusion Resistance research companion

This top-level `website/` folder is a Bun/Astro project following
the approved Epistemics companion's light palette, ruled header, compact shadcn
controls and centred resource links. Its data and author roster come from the
collusion research project.

```sh
bun install --frozen-lockfile
bun run build:report
bun run dev -- --port 4330
```

Local report builds use `make` and a TeX Live or MacTeX installation with
`latexmk`, `pdflatex` and the packages used by the manuscript. `bun run dev`
starts Astro directly for site development.

## Evidence and updates

`public/data/research.json` is the checked-in aggregate snapshot used by the page
and offered as the JSON download. [Publication provenance](data-sources.json)
records the inputs and hashes for the aggregate data and the October case study PDF.

The November readout includes five models, six conditions and a separate
recovery cohort. Assigned outcomes include aborts and unresolved cases.
Resistance estimates and confidence intervals remain unavailable pending
independent review. October keeps its original labels and assignments. The
[swarm aggregate](../report/evidence/swarm-sprint/) records votes and settlements
from the principles and scale campaigns under their original conditions.

Review changes to the current manuscript before merging them to `main`. Each
production build compiles the manuscript from the deployed commit. Update the
checked-in evidence snapshots and their provenance directly after review. The
report owns stratified means and uncertainty.

## Boundaries and checks

Astro renders prose, counts and links into static HTML. One React island
hydrates the Base UI condition select. The Astro script switches between
pre-rendered outcome panels while the coverage table remains visible. The
historical figure reveals once on scroll and respects reduced motion. Static
charts remain readable without JavaScript. No fonts, images or videos block the
initial page render. Workers serves the static build at `collusion.lbxa.net`.

```sh
bun run lint
bun run typecheck
bun test
bun run build
```

The repository gate is `bash scripts/verify.sh`; it does not validate this site's
build. Browser review should cover narrow and wide layouts, filter changes,
unavailable values, download links, no-JavaScript and reduced-motion views.
The first draft's checks and remaining gaps are recorded in [REVIEW.md](REVIEW.md).

## Cloudflare Workers

`wrangler.jsonc` names the Worker `collusion-bench` and serves `dist/` through
Workers Static Assets. Wrangler runs `bun run build` before uploading assets.
That command uses `make -C ../report agentic`, copies the resulting PDF to
`public/files/collusion-resistance-paper.pdf`, and then builds Astro. A failed
report build stops deployment. Compilation uses the checked-in paper sources,
figures and tables from the same checkout.

The custom `src/pages/404.astro` builds to `dist/404.html`; Workers serves it
with a 404 status for missing paths, including nested URLs.

From this folder:

```sh
bun run deploy:check
bun run deploy
```

The first command validates and builds without uploading. The second publishes
using Wrangler's authenticated account. Keep credentials in Wrangler's local
authentication or CI secrets.

For Cloudflare Git integration, select `lbxa/collusion-bench`, set the root
directory to `website`, and use `bun run deploy` as the deploy command. Use
`collusion-bench` as the Worker name. Install dependencies with
`bun install --frozen-lockfile`. The build installs a checksum-pinned TinyTeX
2025.11 distribution and the manuscript packages from the frozen TeX Live 2025
archive in a temporary directory. Keep the default repository-wide build watch
paths or include `website/*` and `report/*` so paper-only commits trigger a
deployment.

## Changelog

- 2026-11-20: Compile the current paper during website deployment. The download
  uses the same commit as the site and its PDF is generated at build time.
  [Publication decision](../docs/decisions/build-the-current-paper-with-the-website.md).
- 2026-11-19: Rename the current PDF to `collusion-resistance-paper.pdf` and
  redirect previously shared download links to it.
- 2026-11-19: Keep one checked-in research snapshot for rendering and download.
  The site builds from its own files. Update published evidence and provenance
  directly after review. See the [publication decision](../docs/decisions/publish-website-research-as-checked-in-snapshots.md).
- 2026-11-19: Add the historical swarm aggregates and display the principles
  and scale cohorts alongside the current benchmark. Seat counts retain
  missing commitments, and C1/C2 remain subtotals of the scale replication.
- 2026-11-19: Set the Worker name to `collusion-bench` to match the GitHub
  repository used by Workers Builds.

- 2026-11-18: Publish the latest paper at the existing download URL.
  Pin its approved build in `data-sources.json` and keep the October paper
  available for the historical cohort.
- 2026-11-18: The current chart uses assigned-case counts from the frozen
  November report. Keep the recovery cohort separate and preserve aborts and
  unresolved cases so coverage gaps cannot appear as resistance.
- 2026-11-17: Added a static 404 page matching the research site's typography,
  palette and rules, with a home link using the existing shadcn button. It
  needs no client JavaScript and uses Workers' existing 404 routing.
- 2026-11-17: Added a pinned Wrangler CLI and static-assets deployment config.
  Deployments build the site and validate the pinned evidence first; a dry-run
  command checks that path without publishing.
- 2026-11-17: Author metadata confirmed by Lucas: Lucas Barbosa, Sravika Linga,
  Muskaan Kumar and Jake Fogel are affiliated with NYU; Stefan Gazzana (two z's)
  is affiliated with Roundarc. The website uses the corrected spelling even
  while its pinned paper snapshot retains the earlier author metadata.
- 2026-11-17: Created the top-level website using the approved research-page
  recipe. Transfer layout and components while preserving Collusion's authors,
  prospective status, independent evidence sources and historical boundaries.
  See [the decision](../docs/decisions/collusion-website-transfers-design-without-transferring-findings.md).
