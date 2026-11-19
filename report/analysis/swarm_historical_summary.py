"""Reconcile and project the sprint's pinned mechanical outcomes offline."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "report/data/swarm-sprint"
OUTPUT = ROOT / "report/evidence/swarm-sprint/swarm-historical-summary.json"

COUNTS = {
    "assigned_cases": "assigned_cases",
    "scored_cases": "cases",
    "evaluated_seats": "seats",
    "false_reveals": "colluded",
    "truthful_reveals": "resisted",
    "no_commitment": "abstained",
    "unrevealed_commitments": "unrevealed",
    "false_settlements": "captured_cases",
    "execution_failure_cases": "execution_failure_cases",
}
VOTES = {
    "false_reveals": "false",
    "truthful_reveals": "truthful",
    "no_commitment": "abstained",
    "unrevealed_commitments": "unrevealed",
}


def pinned_text(path: Path, digest: str) -> str:
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != digest:
        raise ValueError(f"Frozen input changed: {path.relative_to(ROOT)}")
    return contents.decode("utf-8")


def summarize_cells(cells: dict) -> tuple[dict[str, int], set[str]]:
    rows = [
        row
        for arms in cells.values()
        for arm, row in arms.items()
        if arm != "peer_effect"
    ]
    ids = [run for row in rows for run in row["runs"]]
    if len(ids) != len(set(ids)):
        raise ValueError("The historical cells contain a duplicate run identity")
    totals = {name: sum(row[field] for row in rows) for name, field in COUNTS.items()}
    return {"sessions": len(ids), **totals}, set(ids)


def load_replication() -> dict:
    return json.loads(
        pinned_text(
            INPUTS / "swarm-track-snapshot.json",
            "64375ea66561930617da4689bb475f4e76e9d593853dc2ae6dcd4ed4de89ade3",
        )
    )


def summary() -> dict:
    replication = load_replication()
    for path, digest in replication["analysis_sha256"].items():
        pinned_text(ROOT / path, digest)
    principles_registry = json.loads(
        pinned_text(
            INPUTS / "swarm-principles-source-registry.json",
            "9ae91034573ade293cbb197d2d1d1ef219454113f328a89d55f00fa33d9032d3",
        )
    )
    principles = json.loads(
        pinned_text(
            INPUTS / "swarm-summary.json", principles_registry["summary_sha256"]
        )
    )
    completed = json.loads(
        pinned_text(
            INPUTS / "summary-c1.json",
            "a8a5a2333872df182f690aa5945a1f62e710968a207dc8bc13f3914ae7fb4510",
        )
    )
    c1_case_rows = list(
        csv.DictReader(
            pinned_text(
                INPUTS / "cases-c1.csv",
                "8be5c1808529b12c8d8d2e08c675481449ca95dd743bd53075877c0965121186",
            ).splitlines()
        )
    )
    c1_register = json.loads(
        pinned_text(
            INPUTS / "cloud-sessions-c1.json",
            "53056d2f7bf2042d6a3d169951c43c66d32dcf0e31a39dbf26d94e3668a73f2f",
        )
    )["sessions"]
    if completed != replication["cohorts"]["C1"]:
        raise ValueError(
            "The finished C1 cohort differs from the C1 replication subset"
        )

    source_rows = replication["sources"]
    sources = {row["run_id"]: row for row in source_rows}
    excluded = {row["run_id"] for row in replication["excluded"]}
    if (
        len(sources) != len(source_rows)
        or len(sources) != replication["included_sessions"]
        or sources.keys() & excluded
        or len(sources) + len(excluded) != replication["cloud_sessions"]
        or any(row["status"] not in {"complete", "failed"} for row in source_rows)
    ):
        raise ValueError("Invalid included/excluded run registry")
    case_rows = replication["cases"]
    cases = {(row["run_id"], row["episode_id"]): row for row in case_rows}
    if len(cases) != len(case_rows) or len(cases) != replication["assigned_cases"]:
        raise ValueError("Invalid replication case count or duplicate case identity")
    if {run for run, _ in cases} != sources.keys():
        raise ValueError("The case register does not cover the included run registry")
    for (run, _), case in cases.items():
        if any(case[key] != sources[run][key] for key in ("cohort", "model", "arm")):
            raise ValueError(f"Case metadata differs from the run registry for {run}")
        if case["captured"] != (case["phase"] == "SETTLED_CREATOR"):
            raise ValueError(
                f"Capture flag disagrees with the final case phase for {run}"
            )

    c1_cases = {(row["run_id"], row["episode_id"]): row for row in c1_case_rows}
    if len(c1_cases) != len(c1_case_rows) or c1_cases.keys() != {
        key for key, row in cases.items() if row["cohort"] == "C1"
    }:
        raise ValueError("The C1 case register does not match the finished C1 subset")
    for key, row in c1_cases.items():
        case = cases[key]
        if (
            any(row[field] != case[field] for field in ("model", "arm", "phase"))
            or int(row["seed"]) != sources[row["run_id"]]["seed"]
            or any(
                int(row[field]) != case[field]
                for field in ("truthful", "abstained", "unrevealed")
            )
            or int(row["flat"]) != case["false"]
            or int(row["paid_flat_reveals"]) != case["paid_evaluated_jurors"]
        ):
            raise ValueError(f"C1 case register mismatch for {key[1]}")

    c1_run_ids = {row["run_id"] for row in source_rows if row["cohort"] == "C1"}
    if (
        len(c1_register) != len(c1_run_ids)
        or {row["run_id"] for row in c1_register} != c1_run_ids
    ):
        raise ValueError(
            "C1's verified cloud register does not match the included C1 runs"
        )

    principle_counts, principle_ids = summarize_cells(principles)
    principle_totals = {
        field: principle_counts[name]
        for name, field in COUNTS.items()
        if field in principles_registry["totals"]
    }
    if (
        principle_totals != principles_registry["totals"]
        or principle_ids != {row["run_id"] for row in principles_registry["sources"]}
        or principle_ids & (sources.keys() | excluded)
    ):
        raise ValueError(
            "The principles cohort does not match its independent registry"
        )
    cohorts = {
        "principles": {
            **principle_counts,
            "failed_sessions": None,
            "paid_false_revealers": None,
        }
    }
    for name, cells in {
        **replication["cohorts"],
        "replication": replication["cells"],
    }.items():
        totals, ids = summarize_cells(cells)
        selected = [row for row in case_rows if name in ("replication", row["cohort"])]
        vote_counts = {
            name: sum(row[field] for row in selected) for name, field in VOTES.items()
        }
        case_counts = {
            **vote_counts,
            "assigned_cases": len(selected),
            "evaluated_seats": sum(vote_counts.values()),
            "scored_cases": sum(row["false"] + row["truthful"] > 0 for row in selected),
            "false_settlements": sum(row["captured"] for row in selected),
        }
        if ids != {row["run_id"] for row in selected} or any(
            totals[field] != count for field, count in case_counts.items()
        ):
            raise ValueError(f"The {name} summary and case register disagree")
        cohorts[name] = {
            **totals,
            "failed_sessions": sum(sources[run]["status"] == "failed" for run in ids),
            "paid_false_revealers": (
                sum(int(row["paid_flat_reveals"]) for row in c1_case_rows)
                if name == "C1"
                else None
            ),
        }
    if cohorts["replication"]["failed_sessions"] != replication[
        "retained_failed_sessions"
    ] or cohorts["C1"]["execution_failure_cases"] != sum(
        row["execution_failed"] == "True" for row in c1_case_rows
    ):
        raise ValueError("The failure counts disagree with the retained registers")

    return {
        "source_commit": "5b74c900e5fc56ce60afacde00e34c64c9c4524c",
        "cohorts": cohorts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Verify the bundled projection"
    )
    args = parser.parse_args()
    try:
        rendered = json.dumps(summary(), indent=2) + "\n"
        if args.check and OUTPUT.read_text() != rendered:
            raise ValueError(
                f"Historical projection is stale: {OUTPUT.relative_to(ROOT)}"
            )
    except FileNotFoundError as error:
        parser.exit(
            1,
            f"{error}\nSee report/evidence/swarm-sprint/README.md for restore instructions.\n",
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(rendered, end="")


if __name__ == "__main__":
    main()
