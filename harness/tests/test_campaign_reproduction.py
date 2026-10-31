import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[1] / "research/frontier-2026-10-31/analyze.py"
spec = importlib.util.spec_from_file_location("frontier_analysis", SOURCE)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_published_evidence_hashes_detect_changed_raw_bytes(tmp_path):
    raw = tmp_path / "calls.jsonl"
    raw.write_text('{"response": "fixture"}\n')
    manifest = {raw.name: hashlib.sha256(raw.read_bytes()).hexdigest()}
    (tmp_path / "SHA256SUMS.json").write_text(json.dumps(manifest))
    assert analysis.validate_manifest(tmp_path)["status"] == "verified"
    raw.write_text('{"response": "changed"}\n')
    with pytest.raises(ValueError, match="Evidence hash mismatch"):
        analysis.validate_manifest(tmp_path)


def test_reproduction_uses_primary_registry_and_counts_probes_and_retained_holds(tmp_path):
    requests = [
        {"id": "play", "accounted_usd": "0.50", "status": "charged"},
        {"id": "probe", "accounted_usd": "0.25", "status": "charged"},
        {"id": "unknown", "accounted_usd": "1.25", "status": "reserved"},
    ]
    (tmp_path / "spending.json").write_text(
        json.dumps(
            {
                "request_ledger": requests,
                "limit_usd": "500",
                "accounted_usd": "2.00",
                "unresolved_requests": 1,
            }
        )
    )
    wave = {
        "wave": "baseline",
        "git_revision": "revision",
        "upstream_revision": "upstream",
        "attempts": [{"model": "fixture/model", "runs": ["run-primary"]}],
    }
    (tmp_path / "wave-baseline-v3.json").write_text(json.dumps(wave))
    run = tmp_path / "run-primary"
    (run / "case").mkdir(parents=True)
    for request, suffix in (("play", "trace"), ("probe", "probe"), ("unknown", "failed")):
        (run / "case" / f"juror.{suffix}.calls.jsonl").write_text(
            json.dumps(
                {
                    "event": "model_start",
                    "request_id": request,
                }
            )
            + "\n"
        )
    manifest = {
        "run_id": run.name,
        "status": "complete",
        "provenance": {"git_revision": "revision", "input_sha256": {}},
        "config": {
            "name": "frontier-baseline",
            "episodes": 1,
            "creator": "scripted",
            "challenger": "scripted",
        },
        "episodes": [{"outcome": "SETTLED_CHALLENGER", "verdict_correct": True, "model_calls": 2}],
    }
    (run / "run.json").write_text(json.dumps(manifest))
    pilot = tmp_path / "run-pilot"
    pilot.mkdir()
    (pilot / "run.json").write_text(
        json.dumps({**manifest, "run_id": pilot.name, "status": "failed"})
    )
    result = analysis.analyze(tmp_path)
    assert result["primary_assignments"] == 1
    assert result["sessions"][0]["charged_usd"] == "0.75"
    assert result["sessions"][0]["unresolved_holds_usd"] == "1.25"
    assert result["sessions"][0]["correct_verdicts"] == 1
    assert [p["run_id"] for p in result["retained_other_attempts"]] == [pilot.name]
    assert result["budget"]["accounted_usd"] == "2.00"
