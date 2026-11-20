# Keep Stop hooks fast

- **Date:** 2026-11-19
- **Status:** Accepted
- **Deciders:** Lucas Barbosa requested the split. Codex selected the fast checks and timeout.
- **Area:** Developer tooling

## Context

The [Docker verification split](./run-docker-acceptance-in-ci-and-explicit-verification.md)
removed Docker from routine handoffs. Stop still waited for Foundry, Rust
builds, real Anvil, and the Python suite. That cost repeated at every handoff.

## Decision

Use `scripts/verify-fast.sh` for Stop. It runs the shell integration fixtures
with mocked tools and checks the generated decision index. Both hook runners
cap the command at 30 seconds. Fixture tests pin the hook routing and the cap
and detect heavyweight tools entering the fast path. The full gate reuses the
fast checks and continues through all runtime suites in CI. Developers can run
the full gate or its `--no-docker` mode explicitly.

## Consequences

Local handoffs verify the hook contract in seconds. Runtime regressions surface
in explicit verification and CI. The first Stop failure still requests one
repair and records a log, and the repeat reports any unresolved failure.
