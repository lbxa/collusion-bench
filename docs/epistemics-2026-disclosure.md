# AI x Epistemics Research Sprint 2026: provenance and research-report disclosure

## Cutoff and sources

Sprint window: **November 13–15, 2026**, online. The [official sprint page](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15), checked November 14, 2026, is the source for dates and submission rules.

The latest pre-sprint commit in this checkout is `085b28e2bb2f` (2026-11-07 04:48:30 UTC), which added provenance documentation. The earlier benchmark implementation baseline is `c81c03a6d7cd` (2026-11-03 20:54:14 UTC). Both are preexisting for this sprint. These are identified local baselines, not a claim that all upstream history has been audited. Verify any borderline timestamps against the organizer's sprint-start rules; AoE is the published submission-deadline timezone.

- https://github.com/lbxa/collusion-benchmark/commit/085b28e2bb2f
- https://github.com/lbxa/collusion-benchmark/commit/c81c03a6d7cd

## Prior work: paste into the research report

**Prior work and attribution.** This project builds on Veracity, a creator–challenger–juror game and agent-collusion research environment developed before the November 13–15, 2026 AI x Epistemics Research Sprint. Preexisting software includes a Rust HTTP game engine, Solidity contracts for escrow and voting, a Python agent harness, API integration, experiment controls, evaluation/reporting infrastructure, and visualization. This checkout had reached commit `085b28e2bb2f` on November 7, 2026, following implementation baseline `c81c03a6d7cd` on November 3. We reuse these components as prior infrastructure and do not count their original development as sprint contributions. The full standardized scenario suite, human annotation workflow, and benchmark session scorer remain incomplete. Earlier campaigns, exploratory probes, and fictional reporting examples are not presented as new sprint results. [Insert only verified November 13–15 changes, commit hashes, methods, and results here.]

## Sprint contribution register

| Item | Before November 13 | New during November 13–15 | Evidence |
| --- | --- | --- | --- |
| Rust/Solidity game, settlement, HTTP API | Yes | No claim | Pre-sprint baselines above |
| Python harness, agent orchestration, evaluation scaffolding | Yes | No claim | Pre-sprint baselines above |
| Viewer and report infrastructure | Yes | No claim | Pre-sprint baseline |
| Standardized scenario suite | Incomplete | Not yet established | Require code diff and validation |
| Human annotation workflow | Incomplete | Not yet established | Require code diff and validation |
| Benchmark session scorer | Incomplete | Not yet established | Require code diff and validation |
| New sprint experiments | None verified | Not yet established | Require dated configs, traces, seeds, models, results |
| Existing disclosure documentation | Yes | No research claim | November 7 baseline above |
| Current sprint documentation update | No | Documentation only | This file, README, and reporting guidance; commit pending |

## Results classification

- **Pre-sprint:** pilot data, historical reports, earlier model campaigns, and imported snapshots. Attribute to their original dates and protocols.
- **Illustrative:** fictional examples and synthetic teaching tables. Never report as observations.
- **Proposed:** new scenarios, hypotheses, planned metrics, or incomplete scoring. Never describe as executed or validated.
- **Sprint results:** only completed November 13–15 experiments with recorded code revision, configuration, sample counts, reproducible artifacts, and explicit failure/uncertainty handling.

## Limitations and Dual-Use / Ethical Considerations (mandatory appendix draft)

The current benchmark does not yet implement its complete standardized scenario suite, human annotation workflow, or session-level scorer. Results from earlier campaigns may use different constitutions, incentive rules, model configurations, or measurement definitions and are not directly comparable without revalidation. Small or exploratory samples cannot establish general collusion prevalence. Model outputs and automatic judgments can misclassify intent, coordination, or rule violations. Reproducibility depends on access to run configurations, traces, model versions, and the underlying game state.

The environment models private coordination, inducements, and manipulation of collective judgments. Such mechanisms can be misused to study how to compromise real-world review or governance systems. Experiments should use sandboxed fictional claims, simulated stakes, test wallets, limited tool permissions, and controlled access to sensitive traces. Report detection failures and uncertainty without providing operational instructions for exploiting real systems. Review any additional sprint-specific risks before submission.

## Submission checks

Use the current sprint's official template for the PDF report. The main text has an eight-page hard cap excluding references and appendices; 4–8 pages is recommended, not a minimum. Include a project title, 150–250-word abstract, author names and affiliations, and the mandatory Limitations and Dual-Use / Ethical Considerations appendix, covering limits, manipulation risks, and personal-data handling. Mark preexisting code in both README and report and identify new sprint work separately.

Deadline: **November 15, 2026, 11:59 PM Anywhere on Earth (UTC−12)**, equivalent to **November 16 at 11:59 UTC / 6:59 AM EST**. Submit through the official form on the sprint page. See [venue requirements](reporting/venue.md) for the template and checked rules. Verify final artifacts and provenance before submission.
