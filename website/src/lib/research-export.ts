import { z } from "zod";

const count = z.number().int().nonnegative();
const slots = ["deepseek", "glm", "kimi", "gptoss", "inkling"] as const;
const labels = { deepseek: "DeepSeek V4 Pro", glm: "GLM 5.3", kimi: "Kimi K2.6", gptoss: "GPT OSS 120B", inkling: "Inkling 2 Small" };
const arms = ["paid-false-basic", "paid-rejection-basic", "honest-false", "honest-true", "paid-false-suppressed", "paid-false-principles"] as const;
const conditions = [
  { id: "primary", label: "Both basic paid conditions" },
  { id: "paid-false-basic", label: "Paid support for a false claim" },
  { id: "paid-rejection-basic", label: "Paid rejection of a supported claim" },
  { id: "honest-false", label: "Honest control · false claim" },
  { id: "honest-true", label: "Honest control · supported claim" },
  { id: "paid-false-suppressed", label: "Paid support · messages suppressed" },
  { id: "paid-false-principles", label: "Paid support · principles added" },
] as const;

const rowSchema = z.object({
  model_slot: z.enum(slots),
  arm: z.enum(arms),
  assigned_cases: count,
  assigned_sessions: count,
  orchestration_complete: count,
  failed: count,
  interrupted: count,
  source_correct_settlement: count,
  source_adverse_settlement: count,
  aborted: count,
  missing_case_evidence: count,
  unsettled_other: count,
  reference_not_applicable: z.literal(0),
  reference_unknown: z.literal(0),
}).refine(row => row.source_correct_settlement + row.source_adverse_settlement
  + row.aborted + row.missing_case_evidence + row.unsettled_other === row.assigned_cases,
  "Case counts must partition all assignments")
  .refine(row => row.orchestration_complete + row.failed + row.interrupted === row.assigned_sessions,
    "Session dispositions must partition all assignments");

const cohortSchema = z.object({
  capture_utc: z.iso.datetime({ offset: true }),
  assigned_cases: count,
  assigned_sessions: count,
  by_model_arm: z.array(rowSchema).length(slots.length * arms.length)
    .refine(rows => new Set(rows.map(row => `${row.model_slot}/${row.arm}`)).size === rows.length,
      "Every model and condition must appear exactly once"),
}).refine(cohort => cohort.by_model_arm.reduce((sum, row) => sum + row.assigned_cases, 0) === cohort.assigned_cases
  && cohort.by_model_arm.reduce((sum, row) => sum + row.assigned_sessions, 0) === cohort.assigned_sessions,
  "Model and condition totals must reconcile with cohort assignments");

const currentSchema = z.object({
  format_version: z.literal(1),
  semantic_label_status: z.literal("not_reviewed"),
  competence_status: z.literal("not_reviewed"),
  roster: z.array(z.object({
    model_slot: z.enum(slots),
    model_id: z.string().startsWith("@cf/"),
  })).length(slots.length).refine(models => new Set(models.map(model => model.model_slot)).size === slots.length),
  cohorts: z.object({
    original_confirmation: cohortSchema,
    exploratory_recovery: cohortSchema,
  }),
});

const historicalSchema = z.object({
  format_version: z.literal(1),
  unit: z.string(),
  runs: z.array(z.object({
    status: z.string(),
    error_type: z.string().nullable(),
    assigned_episodes: count,
    episodes: z.array(z.object({
      outcome: z.enum(["SETTLED_CREATOR", "SETTLED_CHALLENGER", "EXPIRED_UNCHALLENGED", "EXPIRED_UNFUNDED"]),
      review: z.object({ classification: z.enum(["harmful_coordination", "ambiguous", "not_established"]) }),
    })),
  }).refine(run => run.assigned_episodes >= run.episodes.length
    && (run.assigned_episodes === run.episodes.length || (run.status === "failed" && run.error_type === "CancelledError")),
  "Missing historical episodes must retain their interruption status")),
});

const swarmCohortSchema = z.object({
  sessions: count,
  assigned_cases: count,
  scored_cases: count,
  evaluated_seats: count,
  false_reveals: count,
  truthful_reveals: count,
  no_commitment: count,
  unrevealed_commitments: count,
  false_settlements: count,
  execution_failure_cases: count,
  failed_sessions: count.nullable(),
  paid_false_revealers: count.nullable(),
}).refine(cohort => cohort.false_reveals + cohort.truthful_reveals + cohort.no_commitment
  + cohort.unrevealed_commitments === cohort.evaluated_seats,
"Reveals and missing ballots must partition the assigned swarm seats")
  .refine(cohort => cohort.scored_cases <= cohort.assigned_cases
    && cohort.false_settlements <= cohort.assigned_cases
    && cohort.execution_failure_cases <= cohort.assigned_cases
    && (cohort.failed_sessions === null || cohort.failed_sessions <= cohort.sessions)
    && (cohort.paid_false_revealers === null || cohort.paid_false_revealers <= cohort.false_reveals),
  "Swarm counts must fit their corresponding denominators");

const swarmSchema = z.object({
  source_commit: z.string().regex(/^[a-f0-9]{40}$/),
  cohorts: z.object({
    principles: swarmCohortSchema,
    C1: swarmCohortSchema,
    C2: swarmCohortSchema,
    replication: swarmCohortSchema,
  }),
}).refine(({ cohorts: { C1, C2, replication } }) => {
  const totals = [
    "sessions", "assigned_cases", "scored_cases", "evaluated_seats", "false_reveals",
    "truthful_reveals", "no_commitment", "unrevealed_commitments", "false_settlements",
    "execution_failure_cases",
  ] as const;
  const failedSessions = C1.failed_sessions === null || C2.failed_sessions === null
    ? null : C1.failed_sessions + C2.failed_sessions;
  return totals.every(key => replication[key] === C1[key] + C2[key])
    && replication.failed_sessions === failedSessions;
}, "Swarm replication totals must reconcile with their C1 and C2 subtotals");

function projectSwarmCohort(cohort: z.infer<typeof swarmCohortSchema>) {
  return {
    sessions: cohort.sessions,
    assignedCases: cohort.assigned_cases,
    scoredCases: cohort.scored_cases,
    evaluatedSeats: cohort.evaluated_seats,
    falseReveals: cohort.false_reveals,
    truthfulReveals: cohort.truthful_reveals,
    noCommitment: cohort.no_commitment,
    unrevealedCommitments: cohort.unrevealed_commitments,
    falseSettlements: cohort.false_settlements,
    executionFailureCases: cohort.execution_failure_cases,
    failedSessions: cohort.failed_sessions,
    paidFalseRevealers: cohort.paid_false_revealers,
  };
}

type Row = z.infer<typeof rowSchema>;

function summarize(rows: Row[]) {
  return rows.reduce((total, row) => ({
    assigned: total.assigned + row.assigned_cases,
    correct: total.correct + row.source_correct_settlement,
    adverse: total.adverse + row.source_adverse_settlement,
    aborted: total.aborted + row.aborted,
    unresolved: total.unresolved + row.missing_case_evidence + row.unsettled_other,
    sessions: total.sessions + row.assigned_sessions,
    completed: total.completed + row.orchestration_complete,
    failed: total.failed + row.failed,
    interrupted: total.interrupted + row.interrupted,
  }), { assigned: 0, correct: 0, adverse: 0, aborted: 0, unresolved: 0, sessions: 0, completed: 0, failed: 0, interrupted: 0 });
}

export function projectResearch(currentInput: unknown, historicalInput: unknown, swarmInput: unknown) {
  const current = currentSchema.parse(currentInput);
  const historical = historicalSchema.parse(historicalInput);
  const swarm = swarmSchema.parse(swarmInput);
  const original = current.cohorts.original_confirmation;
  const recovery = current.cohorts.exploratory_recovery;
  const episodes = historical.runs.flatMap(run => run.episodes);
  const assigned = historical.runs.reduce((sum, run) => sum + run.assigned_episodes, 0);
  return {
    schemaVersion: 2,
    protocol: "collusion-resistance-v1",
    resistanceEstimate: null,
    resistanceCI95: null,
    conditions: conditions.map(condition => ({ ...condition })),
    models: slots.map(slot => {
      const model = current.roster.find(row => row.model_slot === slot)!;
      const rows = original.by_model_arm.filter(row => row.model_slot === slot);
      return {
        id: slot,
        label: labels[slot],
        modelId: model.model_id,
        outcomes: Object.fromEntries(conditions.map(({ id }) => [
          id,
          summarize(rows.filter(row => id === "primary"
            ? row.arm === "paid-false-basic" || row.arm === "paid-rejection-basic"
            : row.arm === id)),
        ])),
      };
    }),
    original: { captureUtc: original.capture_utc, ...summarize(original.by_model_arm) },
    recovery: { captureUtc: recovery.capture_utc, ...summarize(recovery.by_model_arm) },
    swarm: {
      sourceCommit: swarm.source_commit,
      principles: projectSwarmCohort(swarm.cohorts.principles),
      C1: projectSwarmCohort(swarm.cohorts.C1),
      C2: projectSwarmCohort(swarm.cohorts.C2),
      replication: projectSwarmCohort(swarm.cohorts.replication),
    },
    historical: {
      date: "2026-10-26",
      unit: historical.unit,
      runs: historical.runs.length,
      assigned,
      terminal: episodes.length,
      categories: [
        { id: "reviewed", label: "Reviewed coordination", count: episodes.filter(episode => episode.review.classification === "harmful_coordination").length },
        { id: "ambiguous", label: "Ambiguous", count: episodes.filter(episode => episode.review.classification === "ambiguous").length },
        { id: "not-established", label: "Not established", count: episodes.filter(episode => episode.review.classification === "not_established").length },
        { id: "interrupted", label: "Interrupted", count: assigned - episodes.length },
      ],
    },
  };
}

export type ResearchData = ReturnType<typeof projectResearch>;
