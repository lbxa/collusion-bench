# Use collusion-bench project defaults

- **Date:** 2026-11-19
- **Status:** Accepted
- **Deciders:** Lucas Barbosa
- **Area:** repository identity, experiment tracking, website deployment

## Context

The project was copied to `lbxa/collusion-bench`. Historical run URLs and
private artifact receipts identify the W&B project used to collect the data.
Existing upload intents and campaign markers also use that scope for retries.

## Decision

Use `collusion-bench` for the workspace and website Worker. Default new
tracking to `lbxa-corp/collusion-bench` on `https://api.wandb.ai`. Read-only
access to the new W&B project was verified on 2026-11-19.

## Consequences

- An authorized resume uses the scope recorded by the original run or campaign.
  Historical evidence and artifact names continue to point to their source.
- The [earlier private audit approval](archive-authorized-collusion-trajectories-in-private-wandb.md)
  covers its original destination. A release to another project needs its own
  authorization.
- The repository's Wrangler configuration targets `collusion-bench`.
  The [deployment guide](../../website/README.md#cloudflare-workers) records
  the matching Worker and GitHub repository for Workers Builds setup.
