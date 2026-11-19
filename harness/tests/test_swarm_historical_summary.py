import json
from pathlib import Path

PROJECTION = (
    Path(__file__).resolve().parents[2]
    / "report/evidence/swarm-sprint/swarm-historical-summary.json"
)


def test_portable_swarm_projection_preserves_all_historical_cohorts():
    cohorts = json.loads(PROJECTION.read_text())["cohorts"]
    assert set(cohorts) == {"principles", "C1", "C2", "replication"}
    for name, expected in {
        "principles": (50, 50, 400, 0, 390, 10, 0, 0, None),
        "C1": (57, 63, 216, 45, 77, 94, 0, 20, 43),
        "C2": (47, 53, 173, 52, 65, 55, 1, 19, None),
        "replication": (104, 116, 389, 97, 142, 149, 1, 39, None),
    }.items():
        assert (
            tuple(
                cohorts[name][key]
                for key in (
                    "sessions",
                    "assigned_cases",
                    "evaluated_seats",
                    "false_reveals",
                    "truthful_reveals",
                    "no_commitment",
                    "unrevealed_commitments",
                    "false_settlements",
                    "paid_false_revealers",
                )
            )
            == expected
        )
    assert cohorts["replication"]["scored_cases"] == 96
    assert cohorts["replication"]["failed_sessions"] == 8
