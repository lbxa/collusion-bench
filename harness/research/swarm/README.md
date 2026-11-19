# Run the historical swarm designs on the current harness

These presets use the original Swarm Alignment Sprint conditions, source claim,
model IDs, and seeds for fresh runs. The campaign fingerprint binds the current
runtime, case, configuration, and delivered-instruction hashes.
Use the [historical evidence register](../../../report/evidence/swarm-sprint/)
for the original results and their deployment and rule identities.

| Preset | Inputs | Planned sessions | Planned cases |
| --- | --- | ---: | ---: |
| `principles` | 15-juror honest/colluding peer arms, five historical endpoints, seeds 811–815 | 50 | 50 |
| `seven-juror` | 7-juror honest/colluding peer arms, same endpoints and seeds | 50 | 50 |
| `scale` | Three original C1 endpoints, [19 entries per endpoint](../swarm-scale/plan.txt), and 3/7/15-juror arms and contrasts | 57 | 63 |

The seven-juror preset prepares a standalone follow-up. The sprint tried a
partial fallback after the 15-juror campaign, then stopped it. The scale
preset includes one three-case repeated-exposure session per model.

From the repository root, choose a fresh directory for the generated plans.
Each plan's TOML paths are relative to the plan file, so keep that relationship
when moving it to a worker. Both steps below are offline.

```sh
mkdir -p harness/results/swarm-plans
for preset in principles seven-juror scale; do
  swarm_plan="harness/results/swarm-plans/${preset}.json"
  uv run --project harness --locked python harness/research/swarm/plan.py "$preset" \
    --output "$swarm_plan" || break
  uv run --project harness --locked veracity-harness-campaign validate --plan "$swarm_plan"
done
```

Live runs require an explicitly selected cloud worker with Docker and the
engine, an authorized cap, and the campaign's shared spending ledger. Use the
[campaign run and status commands](../../README.md#campaign-dispatch-and-recovery)
with the same plan, cap, output directory, and ledger on resume. Each plan
preserves the original planned order within each model. The current journal
retains every started assignment and its terminal disposition.

Use the offline [`analyze.py`](analyze.py) on one cohort at a time. For retained
sprint artifacts stored in a directory named `swarm-runs`, for example,

```sh
python3 -I harness/research/swarm/analyze.py swarm-runs/run-* \
  --output swarm-vote-summary.json
```

For a current campaign, run directories live under `jobs/<assignment-id>/` in
its output directory. Use its plan and journal for the assignment denominator,
including missing jobs. The historical scorer's `colluded` field counts
source-adverse reveals. Apply the [benchmark evidence rules](../../../docs/benchmark.md)
separately when classifying knowing coordination or delivered-duty violations.
