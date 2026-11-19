# Publish website research as checked-in snapshots

- **Date:** 2026-11-19
- **Status:** Accepted
- **Deciders:** Lucas Barbosa
- **Area:** Website and report publication

## Context

The [original website decision](collusion-website-transfers-design-without-transferring-findings.md)
used a sync script to project and verify frozen research results. The reviewed
aggregate and PDFs are already checked in. The build-time check still required
restoring private report inputs.

## Decision

Publish the checked-in JSON and PDF snapshots directly. Render the charts
from the same JSON file visitors download. Retain the source paths and hashes
as publication provenance.

## Consequences

The website builds from its own files. An approved revision requires a
review of the evidence and direct edits to the published files and provenance.
Source-hash reconciliation is part of that review.
