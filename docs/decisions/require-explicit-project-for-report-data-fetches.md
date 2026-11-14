# Require an explicit project for report data fetches

- **Date:** 2026-11-14
- **Status:** Accepted
- **Deciders:** Project maintainer (user instruction)
- **Area:** report, documentation

## Context

The project now targets the AI x Epistemics Research Sprint. The maintainer
requested removal of earlier event branding throughout the checkout. Historical
results must remain attributable without implying they were collected for the
current sprint or inventing a replacement hosting location.

## Decision

Require an explicit `--project` when fetching report data from W&B. Remove old
event URLs while retaining historical run IDs, artifact paths, source hashes,
dates, and numeric observations. Keep preexisting-work disclosures for the
current sprint.

## Consequences

Offline snapshot rendering continues to work without a W&B project. Live fetches
need both `--project` and `--since`; no replacement remote project is assumed.
Historical run dashboards are no longer linked from the checkout. See
[the analysis script](../../report/analysis/model_benchmark.py),
[report reproduction](../../report/README.md), and
[current disclosure](../epistemics-2026-disclosure.md).
