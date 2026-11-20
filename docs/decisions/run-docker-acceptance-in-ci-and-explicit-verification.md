# Run Docker acceptance in CI and explicit verification

- **Date:** 2026-11-19
- **Status:** Accepted
- **Deciders:** Lucas Barbosa requested the redesign. Codex selected the verification boundaries.
- **Area:** Developer tooling and harness

## Context

Every local Stop hook previously launched the full Docker suite. Multiple
projects shared Docker Desktop, and tests allocated a private bridge for each
participant. An Engine endpoint-cache race blocked network removal, and
accumulated networks exhausted the available subnets during a swarm test.

## Decision

Run the hook, Foundry, Rust, and non-Docker Python checks automatically at
local Stop. Keep real Docker acceptance in the default verification command
and Linux CI. Run one Docker integration case at a time and preserve the
production isolation topology in those cases.

## Consequences

Routine handoffs launch no test sandboxes. Local Docker failures surface during
explicit full verification, and CI still exercises the integrated protocol on
pull requests. Serial execution trades wall time for a lower peak number of
networks and containers per invocation. Docker Engine updates own the permanent
endpoint-cache repair.
