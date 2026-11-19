import { describe, expect, test } from "bun:test";
import data from "../../public/data/research.json";

describe("public research snapshot", () => {
  test("retains the assigned denominator and outcomes for all five models", () => {
    expect(data.conditions).toHaveLength(7);
    const conditionIds = data.conditions.map(({ id }) => id).sort();
    for (const model of data.models) {
      expect(Object.keys(model.outcomes).sort()).toEqual(conditionIds);
    }
    expect(data.models.map(({ id, outcomes: { primary: row } }) =>
      [id, row.assigned, row.correct, row.adverse, row.aborted, row.unresolved])).toEqual([
      ["deepseek", 20, 4, 0, 10, 6],
      ["glm", 20, 12, 0, 8, 0],
      ["kimi", 20, 17, 0, 3, 0],
      ["gptoss", 20, 14, 2, 4, 0],
      ["inkling", 20, 20, 0, 0, 0],
    ]);
    expect(data.resistanceEstimate).toBeNull();
    expect(data.resistanceCI95).toBeNull();
  });

  test("keeps recovery separate even when an original assignment is unresolved", () => {
    expect(data.original).toMatchObject({ assigned: 300, correct: 122, adverse: 2, aborted: 26, unresolved: 150 });
    expect(data.recovery).toMatchObject({ assigned: 150, correct: 43, adverse: 0, aborted: 3, unresolved: 104, sessions: 75, completed: 19, failed: 51, interrupted: 5 });
  });

  test("retains the separate October denominator and ambiguous cases", () => {
    expect(data.historical.runs).toBe(13);
    expect(data.historical.assigned).toBe(19);
    expect(data.historical.terminal).toBe(18);
    expect(data.historical.categories.map(category => category.count)).toEqual([7, 3, 8, 1]);
  });

  test("retains the original swarm cohort boundaries, vote counts and missing values", () => {
    const { swarm } = data;
    expect(swarm.principles).toMatchObject({
      sessions: 50, assignedCases: 50, evaluatedSeats: 400,
      truthfulReveals: 390, falseReveals: 0, noCommitment: 10, failedSessions: null,
    });
    expect(swarm.replication).toMatchObject({
      sessions: 104, assignedCases: 116, evaluatedSeats: 389, truthfulReveals: 142,
      falseReveals: 97, noCommitment: 149, unrevealedCommitments: 1, falseSettlements: 39,
      failedSessions: 8, paidFalseRevealers: null,
    });
    expect(swarm.C1.paidFalseRevealers).toBe(43);
    expect(swarm.C1.sessions + swarm.C2.sessions).toBe(swarm.replication.sessions);
  });
});
