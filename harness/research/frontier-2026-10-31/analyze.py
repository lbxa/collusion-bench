"""Recompute campaign counts and costs from published evidence without model APIs."""

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(directory):
    path = directory / "SHA256SUMS.json"
    if not path.exists():
        return {"status": "not_exported", "files": 0}
    expected = read_json(path)
    for name, digest in expected.items():
        file = directory / name
        if not file.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f"Unsafe manifest path in {directory.name}")
        if not file.is_file() or sha256(file) != digest:
            raise ValueError(f"Evidence hash mismatch: {directory.name}/{name}")
    return {
        "status": "verified",
        "files": len(expected),
        "manifest_sha256": sha256(path),
    }


def call_ids(directory):
    return {
        event["request_id"]
        for path in directory.glob("*/*.calls.jsonl")
        for line in path.read_text().splitlines()
        if (event := json.loads(line)).get("event") == "model_start"
    }


def analyze(results, assignment_version="v3"):
    ledger = read_json(results / "spending.json")
    requests = {row["id"]: row for row in ledger["request_ledger"]}
    if len(requests) != len(ledger["request_ledger"]):
        raise ValueError("Duplicate request identities in spending export")
    accounted = sum((Decimal(r["accounted_usd"]) for r in requests.values()), Decimal(0))
    charged = sum(
        (Decimal(r["accounted_usd"]) for r in requests.values() if r["status"] == "charged"),
        Decimal(0),
    )
    if accounted > Decimal(ledger["limit_usd"]) or accounted != Decimal(ledger["accounted_usd"]):
        raise ValueError("Spending export contradicts the campaign cap or totals")

    assigned = {}
    for path in sorted(results.glob(f"wave-*-{assignment_version}.json")):
        wave = read_json(path)
        for attempt in wave["attempts"]:
            key = (wave["wave"], attempt["model"])
            if key in assigned:
                raise ValueError(f"Duplicate primary assignment: {key}")
            assigned[key] = {
                **attempt,
                "wave": wave["wave"],
                "source": path.name,
                "git_revision": wave["git_revision"],
                "upstream_revision": wave["upstream_revision"],
            }

    rows = []
    primary_ids = set()
    for (arm, model), assignment in assigned.items():
        if len(assignment["runs"]) != 1:
            rows.append(
                {
                    "condition": arm,
                    "model": model,
                    "status": "preflight_failed",
                    "run_ids": assignment["runs"],
                    "source": assignment["source"],
                }
            )
            continue
        run_id = assignment["runs"][0]
        primary_ids.add(run_id)
        directory = results / run_id
        manifest = read_json(directory / "run.json")
        ids = call_ids(directory) & requests.keys()
        cost = sum(
            (
                Decimal(requests[i]["accounted_usd"])
                for i in ids
                if requests[i]["status"] == "charged"
            ),
            Decimal(0),
        )
        held = sum(
            (
                Decimal(requests[i]["accounted_usd"])
                for i in ids
                if requests[i]["status"] == "reserved"
            ),
            Decimal(0),
        )
        config = manifest["config"]
        scripted = ({"creator"} if config["creator"] == "scripted" else set()) | (
            {"challenger"} if config["challenger"] == "scripted" else set()
        )
        if config.get("scripted_peer"):
            scripted.add(config["scripted_peer"])
        episodes = manifest["episodes"]
        transfers = [t for episode in episodes for t in episode.get("credit_transfers", [])]
        rows.append(
            {
                "condition": arm,
                "model": model,
                "run_id": run_id,
                "status": manifest["status"],
                "git_revision": manifest["provenance"]["git_revision"],
                "upstream_revision": assignment["upstream_revision"],
                "constitution_sha256": manifest["provenance"]["input_sha256"].get(
                    "CONSTITUTION.md"
                ),
                "assigned_cases": config["episodes"],
                "recorded_cases": len(episodes),
                "outcomes": dict(Counter(e["outcome"] for e in episodes)),
                "correct_verdicts": sum(e.get("verdict_correct") is True for e in episodes),
                "wrong_verdicts": sum(e.get("verdict_correct") is False for e in episodes),
                "unscored_cases": sum(e.get("verdict_correct") is None for e in episodes),
                "execution_failed_cases": sum(
                    e.get("agent_execution_failed", False) for e in episodes
                ),
                "budget_exhaustions": sum(e.get("budget_exhaustions", 0) for e in episodes),
                "model_play_calls": sum(e.get("model_calls", 0) for e in episodes),
                "paid_requests_including_probes": len(ids),
                "charged_usd": str(cost),
                "unresolved_holds_usd": str(held),
                "transfers": len(transfers),
                "transfers_to_model_jurors_wei": str(
                    sum(
                        int(t["amount_wei"])
                        for t in transfers
                        if t["recipient"].startswith("juror-") and t["recipient"] not in scripted
                    )
                ),
                "evidence_integrity": validate_manifest(directory),
                "wandb": read_json(directory / "wandb.json").get("url")
                if (directory / "wandb.json").exists()
                else None,
            }
        )
    retained = []
    for path in sorted(results.glob("run-*/run.json")):
        manifest = read_json(path)
        if manifest["run_id"] in primary_ids:
            continue
        retained.append(
            {
                "run_id": manifest["run_id"],
                "status": manifest["status"],
                "git_revision": manifest["provenance"]["git_revision"],
                "condition": manifest["config"]["name"],
                "reason": "retained pilot or operational attempt outside the primary assignments",
            }
        )
    return {
        "schema_version": 1,
        "assignment_version": assignment_version,
        "analysis_source_sha256": sha256(Path(__file__)),
        "budget": {
            "limit_usd": ledger["limit_usd"],
            "charged_usd": str(charged),
            "accounted_usd": str(accounted),
            "unresolved_requests": ledger["unresolved_requests"],
            "requests": len(requests),
        },
        "primary_assignments": len(assigned),
        "sessions": rows,
        "retained_other_attempts": retained,
        "interpretation": (
            "Wrong verdicts, transfers and pooled coverage are observations; coordination and "
            "intent require separate evidence review. One session per cell supports exploratory "
            "description, not population rates."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assignment-version", default="v3")
    args = parser.parse_args()
    result = analyze(args.results.resolve(), args.assignment_version)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "primary_assignments": result["primary_assignments"],
                "budget": result["budget"],
            }
        )
    )


if __name__ == "__main__":
    main()
