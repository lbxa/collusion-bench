# Swarm Alignment sprint evidence

This packet brings the committed Swarm Alignment sprint evidence into Collusion
Bench from sprint commit `5b74c900e5fc56ce60afacde00e34c64c9c4524c`.
The numeric snapshot covers the frozen source selection at 09:53 UTC on
November 9, 2026. Each cohort retains its original models, duties, incentives,
and run identities. The compact projection and provenance accompany these
instructions. The pinned analysis inputs are restored to the ignored
`report/data/swarm-sprint/` directory for offline verification.

- The fifteen-juror principles summary and source registry cover 50 played
  sessions across five endpoints. There were 390 truthful reveals, ten seats
  without a commitment, and six cases with execution failures among 400
  assigned evaluated seats. All evaluated reveals were truthful.
- The replication snapshot covers 57 complete-plan C1
  sessions and 47 retained C2 sessions. Together they have 116 assigned cases
  and eight failed sessions with played evidence. The source register lists
  one further setup-only run in its exclusions. C1 and C2 are subtotals of
  this replication.
- The C1 case rows, numeric summary, source register, and budget aggregate
  supply the completed-plan evidence, including the 43 false revealers paid
  in local game credit.

The sprint decision describes a separate interrupted seven-juror fallback. The
recorded results directory and per-run manifests were unavailable in the
local sprint checkout. Its [configurations](../../../harness/research/swarm7/)
remain available for offline verification. The seven-juror size-scale arms
have their own evidence in the replication snapshot.

## Verify and reproduce the counts

Restore the pinned inputs from a local checkout of `apart-swarm-sprint`.
Set `swarm_sprint_repo` to that checkout and run from the Collusion Bench root.

```sh
(
set -eu
swarm_source=5b74c900e5fc56ce60afacde00e34c64c9c4524c
swarm_inputs=report/data/swarm-sprint
mkdir -p "$swarm_inputs"
for source_path in \
  report/data/swarm-summary.json \
  report/data/swarm-principles-source-registry.json \
  report/data/swarm-track-snapshot.json \
  harness/research/swarm-scale/cases-c1.csv \
  harness/research/swarm-scale/summary-c1.json \
  harness/research/swarm-scale/cloud-sessions-c1.json \
  harness/research/swarm-scale/budget-c1.json
do
  restore_target="$swarm_inputs/${source_path##*/}"
  git -C "$swarm_sprint_repo" show "$swarm_source:$source_path" \
    > "$restore_target.tmp"
  mv "$restore_target.tmp" "$restore_target"
done
)
```

| Original input basename | SHA-256 |
| --- | --- |
| `swarm-summary.json` | `7944c97fcad058199c31716e04418d5dd05e55df02f7833688435ab12da57d6c` |
| `swarm-principles-source-registry.json` | `9ae91034573ade293cbb197d2d1d1ef219454113f328a89d55f00fa33d9032d3` |
| `swarm-track-snapshot.json` | `64375ea66561930617da4689bb475f4e76e9d593853dc2ae6dcd4ed4de89ade3` |
| `cases-c1.csv` | `8be5c1808529b12c8d8d2e08c675481449ca95dd743bd53075877c0965121186` |
| `summary-c1.json` | `a8a5a2333872df182f690aa5945a1f62e710968a207dc8bc13f3914ae7fb4510` |
| `cloud-sessions-c1.json` | `53056d2f7bf2042d6a3d169951c43c66d32dcf0e31a39dbf26d94e3668a73f2f` |
| `budget-c1.json` | `78a9e6e8a5653278deec0b353c4dcc62d2b15fe81a4f08b84173ae498e4c8e05` |

The following command verifies the scoring input hashes, unique run and case
identities, cohort membership, vote and failure accounting, and the generated
[public projection](swarm-historical-summary.json). It runs offline from the
repository root with Python's standard library.

```sh
python3 -I report/analysis/swarm_historical_summary.py --check
```

The restored replication snapshot can also reproduce the original LaTeX tables
in a scratch directory.

```sh
python3 -I report/analysis/swarm_track_snapshot.py \
  --snapshot report/data/swarm-sprint/swarm-track-snapshot.json \
  --tables /tmp/swarm-sprint-tables
```

For artifact-level replay, supply an authorized local cache with
`sessions/<run-id>/` directories. The archived scorer checks source files
against their original hashes when given the frozen registry. The integration
replayed the combined snapshot and each standalone cohort from the sprint's
local evidence and reproduced all three files byte for byte. The principles
replay also confirmed six failed run manifests, which the portable registry
represents through case failure counts.

```sh
python3 -I report/analysis/swarm_track_snapshot.py \
  --evidence-root "$swarm_replication_cache" \
  --registry report/data/swarm-sprint/swarm-track-snapshot.json \
  --output /tmp/swarm-sprint-reproduced.json --tables /tmp/swarm-sprint-tables
cmp /tmp/swarm-sprint-reproduced.json report/data/swarm-sprint/swarm-track-snapshot.json

python3 -I harness/research/swarm/analyze.py \
  "$swarm_c1_run_cache"/run-* --output /tmp/swarm-c1-reproduced.json
cmp /tmp/swarm-c1-reproduced.json report/data/swarm-sprint/summary-c1.json

python3 -I harness/research/swarm/analyze.py \
  "$swarm_principles_run_cache"/run-* --output /tmp/swarm-principles-reproduced.json
cmp /tmp/swarm-principles-reproduced.json report/data/swarm-sprint/swarm-summary.json
```

For standalone C1 and principles replay, match the cached run and evidence
file hashes against their source registers first. The principles registry's
original `summary_path` names the sprint checkout path. The registries record
artifact addresses as provenance.

## Interpretation

The frozen analyzer uses `colluded` for an evaluated juror's wrong reveal and
`resisted` for its truthful reveal. The portable projection uses the
mechanical names. It counts only valid evaluated reveals in the scored-case
denominator and separately reports all assigned seats, missing commitments,
unrevealed commitments, and overlapping execution failures. Its JSON nulls
identify counts unavailable from the bundled records. Historical nominal
intervals in the archived summaries describe the original calculation. The
public projection uses counts because jurors in a case and cases in memory
blocks are dependent.

The experiments tested seeded peer exposure and fictional game-credit offers
under fixed communication rules. The size comparison also changed the seeded
bloc, evaluated jury and ordinary per-juror reward. The repeated-exposure arm
supplied scripted peers and offers in each case. These observations support
descriptive comparisons in the historical game. Claims about social
transmission, topology, endogenous leadership, or benchmark-wide collusion
resistance need separate designs and evidence.
