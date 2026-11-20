# Build the current paper with the website

- **Date:** 2026-11-20
- **Status:** Accepted
- **Deciders:** Lucas Barbosa
- **Area:** Website and report publication

## Context

The checked-in PDF workflow allowed the website download to lag behind main
manuscript revisions. The public manuscript has all its LaTeX inputs in Git.

## Decision

The website build runs the report's existing `agentic` Make target and packages
the result at `/files/collusion-resistance-paper.pdf`. This supersedes the
[snapshot decision](publish-website-research-as-checked-in-snapshots.md) for the
current PDF. The October case studies and aggregate data are pinned snapshots.

## Consequences

The deployed commit determines the current paper. Build failures prevent a new
deployment. Workers Builds provisions the pinned TeX tooling during the build.
Manuscript merges to `main` now publish the compiled paper, so approval of the
public content belongs in manuscript review before merge.
