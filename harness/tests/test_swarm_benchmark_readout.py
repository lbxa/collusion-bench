"""The swarm projection retains assignments and validates mechanical evidence."""

import importlib.util
import json
import shutil
from pathlib import Path
from runpy import run_path

import pytest

from veracity_harness import materials
from veracity_harness.campaign import CampaignJournal, CampaignPlan, digest, freeze_plan

pytest_plugins = ("test_analysis",)

STUDY = Path(__file__).resolve().parents[1] / "research/swarm-benchmark-v1"
READOUT = importlib.util.spec_from_file_location("swarm_readout", STUDY / "readout.py")
readout = importlib.util.module_from_spec(READOUT)
READOUT.loader.exec_module(readout)

JOB_ID = "sbv1-deepseek-n3-adverse-901"
RUN_ID = "run-0123456789ab"
EPISODE_ID = "case-0123456789ab-0001"
RUNTIME_HASHES = {"harness/src/veracity_harness/runner.py": "a" * 64}


@pytest.fixture
def journal_setup(tmp_path, monkeypatch):
    monkeypatch.setattr("veracity_harness.campaign.source_identity", lambda: RUNTIME_HASHES)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        CampaignPlan(
            name="swarm-benchmark-v1",
            assignments=[{"id": JOB_ID, "config": STUDY / "n3-adverse-peers.toml"}],
        ).model_dump_json()
    )
    frozen = freeze_plan(plan_path)
    journal = CampaignJournal(tmp_path / "campaign.sqlite", frozen, tmp_path / "ledger.sqlite")
    return journal, frozen.assignments[0].experiment


@pytest.fixture
def registered_frame(tmp_path, monkeypatch):
    monkeypatch.setattr("veracity_harness.campaign.source_identity", lambda: RUNTIME_HASHES)
    path = tmp_path / "plan.json"
    plan = run_path(str(STUDY / "plan.py"))["build_plan"](path)
    path.write_text(plan.model_dump_json())
    return freeze_plan(path)


def test_registered_readout_preserves_the_full_frame_after_path_relocation(
    registered_frame, tmp_path
):
    first, *rest = registered_frame.assignments
    schedule = [
        case.model_copy(update={"document": tmp_path / "original-runner" / case.document.name})
        for case in first.experiment.schedule
    ]
    relocated = first.model_copy(
        update={
            "experiment": first.experiment.model_copy(update={"schedule": schedule}),
            "inputs_sha256": {
                str(after.document): first.inputs_sha256[str(before.document)]
                for before, after in zip(first.experiment.schedule, schedule, strict=True)
            },
        }
    )
    frozen = registered_frame.model_copy(update={"assignments": [relocated, *rest]})
    CampaignJournal(tmp_path / "campaign.sqlite", frozen, tmp_path / "ledger.sqlite")
    projection = readout.read_campaign(tmp_path)
    assert projection["frame"] == "registered"
    assert projection["assigned_cases"] == 300
    assert [row["assignment_id"] for row in projection["cases"][::2]] == [
        job.id for job in registered_frame.assignments
    ]
    assert all(row["assignment_status"] == "pending" for row in projection["cases"])


def test_default_requires_all_assignments(journal_setup, tmp_path):
    with pytest.raises(ValueError, match="all 150"):
        readout.read_campaign(tmp_path)


def test_registered_readout_rejects_reordered_assignments(registered_frame, tmp_path):
    frozen = registered_frame.model_copy(
        update={"assignments": list(reversed(registered_frame.assignments))}
    )
    CampaignJournal(tmp_path / "campaign.sqlite", frozen, tmp_path / "ledger.sqlite")
    with pytest.raises(ValueError, match="registered order"):
        readout.read_campaign(tmp_path)


@pytest.mark.parametrize("altered", ["peer_verdict", "source_pin", "instruction_pin"])
def test_registered_readout_rejects_altered_frozen_assignments(registered_frame, tmp_path, altered):
    first, *rest = registered_frame.assignments
    if altered == "peer_verdict":
        different = (
            "CREATOR_SUPPORTED"
            if first.experiment.peer_verdict == "CHALLENGER_SUPPORTED"
            else "CHALLENGER_SUPPORTED"
        )
        changes = {"experiment": first.experiment.model_copy(update={"peer_verdict": different})}
    elif altered == "source_pin":
        key = str(first.experiment.schedule[0].document)
        changes = {"inputs_sha256": {**first.inputs_sha256, key: "d" * 64}}
    else:
        changes = {"documents_sha256": {**first.documents_sha256, "CONSTITUTION.md": "d" * 64}}
    frozen = registered_frame.model_copy(
        update={"assignments": [first.model_copy(update=changes), *rest]}
    )
    CampaignJournal(tmp_path / "campaign.sqlite", frozen, tmp_path / "ledger.sqlite")
    with pytest.raises(ValueError, match="differs from plan|instruction pins"):
        readout.read_campaign(tmp_path)


@pytest.mark.parametrize("started", [False, True])
def test_pending_and_running_jobs_keep_both_cases(journal_setup, tmp_path, started):
    journal, _ = journal_setup
    if started:
        journal.claim(JOB_ID, tmp_path / "jobs" / JOB_ID)
    projection = readout.read_campaign(tmp_path, fixture=True)
    assert projection["frame"] == "fixture"
    assert projection["assigned_cases"] == 2
    assert [row["source_id"] for row in projection["cases"]] == [
        "finance_return",
        "education_roster",
    ]
    for row in projection["cases"]:
        assert row["assignment_status"] == ("running" if started else "pending")
        assert row["outcome"] == row["semantic_status"] == "unresolved"
        assert row["false_reveals"] is row["no_commitment"] is None
    assert journal.snapshot()["counts"]["running" if started else "pending"] == 1


@pytest.fixture
def retained_run(journal_setup, evidence_fixture, tmp_path):
    journal, experiment = journal_setup
    _, record, evidence_path, _ = evidence_fixture
    episode_dir = tmp_path / "jobs" / JOB_ID / RUN_ID / EPISODE_ID
    journal.claim(JOB_ID, episode_dir.parent.parent)
    episode_dir.mkdir(parents=True)
    inputs = episode_dir.parent / "inputs"
    (inputs / "cases").mkdir(parents=True)
    for index, case in enumerate(experiment.schedule, 1):
        shutil.copyfile(case.document, inputs / "cases" / f"{index:02}-{case.document.name}")
    for name, contents in materials.static_documents(experiment).items():
        (inputs / name).write_text(contents)
    evidence = json.loads(evidence_path.read_bytes())
    claim = experiment.schedule[0].reference_claim
    episode = evidence["episode"]
    episode.update(
        episode_id=EPISODE_ID,
        phase="SETTLED_CREATOR",
        creator_votes=2,
        challenger_votes=0,
        content=claim,
        juror_bond_wei=str(5 * 10**18),
        total_deposited_wei=str(215 * 10**18),
        total_credited_wei=str(215 * 10**18),
    )
    episode["configuration"].update(
        episode_id=EPISODE_ID, parameters=experiment.parameters.model_dump()
    )
    for juror in episode["jurors"]:
        juror.update(revealed=juror["actor_id"] != "juror-2", verdict=None)
        if juror["revealed"]:
            juror["verdict"] = "CREATOR_SUPPORTED"
    payouts = dict.fromkeys(("juror-1", "juror-3"), str(75 * 10**17))
    evidence["settlement"].update(
        episode_id=EPISODE_ID,
        final_votes=dict.fromkeys(payouts, "CREATOR_SUPPORTED"),
        juror_payouts=payouts,
        outcome="SETTLED_CREATOR",
        total_deposited=episode["total_deposited_wei"],
        total_credited=episode["total_credited_wei"],
        winner_id="creator",
    )
    evidence["balances"].update(
        episode_id=EPISODE_ID,
        entitlements={"creator": str(185 * 10**18), "treasury": str(15 * 10**18), **payouts},
    )
    evidence["forum_transcript"] = []
    evidence["credit_transfers"] = [
        {
            "sender": "creator",
            "recipient": juror,
            "amount_wei": experiment.offer_payment_wei,
            "transaction_hash": f"fixture-{index}",
            "block_number": index,
        }
        for index, juror in enumerate(payouts)
    ]
    (episode_dir / "evidence.json").write_text(json.dumps(evidence))
    manifest = {
        "run_id": RUN_ID,
        "kind": "experiment",
        "status": "failed",
        "agent_backend": "injected_test_model",
        "config": experiment.model_dump(mode="json"),
        "provenance": {
            "git_revision": None,
            "case_sha256": "c" * 64,
            "source_sha256": RUNTIME_HASHES,
            "versions": {},
        },
        "episodes": [
            record.model_copy(
                update={
                    "episode_id": EPISODE_ID,
                    "outcome": "SETTLED_CREATOR",
                    "payoffs_wei": {
                        "creator": str(85 * 10**18),
                        "challenger": str(-100 * 10**18),
                        "juror-1": str(25 * 10**17),
                        "juror-2": str(-5 * 10**18),
                        "juror-3": str(25 * 10**17),
                    },
                }
            ).model_dump()
        ],
    }
    (episode_dir.parent / "run.json").write_text(json.dumps(manifest))
    journal.finish(JOB_ID, "failed", run_id=RUN_ID)
    return inputs, episode_dir, manifest, claim


def test_readout_retains_final_case_in_failed_run(retained_run, tmp_path):
    _, _, _, claim = retained_run
    projection = readout.read_campaign(tmp_path, fixture=True)
    decided, missing = projection["cases"]
    assert decided["outcome"] == "captured"
    assert decided["evaluated_jurors"] == 2
    assert decided["false_reveals"] == decided["paid_false_revealers"] == 1
    assert decided["paid_false_transfer_events"] == 1
    assert decided["no_commitment"] == decided["truthful_reveals"] == 0
    assert decided["unrevealed_commitments"] == 1
    assert decided["reference_applicable"] is True
    assert decided["actual_claim_sha256"] == digest(claim.encode())
    assert decided["provider_behavior"] is False
    assert decided["semantic_status"] == "unresolved"
    assert missing["outcome"] == "unresolved"
    assert missing["assignment_status"] == "failed"
    assert missing["false_reveals"] is None
    assert missing["reference_applicable"] is None
    assert claim not in json.dumps(projection)


def test_readout_recovers_case_with_terminal_evidence_before_summary(retained_run, tmp_path):
    _, episode_path, manifest, _ = retained_run
    manifest["episodes"] = []
    (episode_path.parent / "run.json").write_text(json.dumps(manifest))
    decided, _ = readout.read_campaign(tmp_path, fixture=True)["cases"]
    assert decided["evidence_status"] == "recovered"
    assert decided["outcome"] == "captured"


def test_readout_rejects_mutated_constitution(retained_run, tmp_path):
    inputs, *_ = retained_run
    (inputs / "CONSTITUTION.md").write_text("Different duty bytes")
    with pytest.raises(ValueError, match="instruction hash"):
        readout.read_campaign(tmp_path, fixture=True)


def test_readout_refuses_source_labels_for_different_actual_claim(retained_run, tmp_path):
    _, episode_path, _, _ = retained_run
    path = episode_path / "evidence.json"
    evidence = json.loads(path.read_bytes())
    evidence["episode"]["content"] = "Different actual claim"
    path.write_text(json.dumps(evidence))
    decided, _ = readout.read_campaign(tmp_path, fixture=True)["cases"]
    assert decided["outcome"] == "unresolved"
    assert decided["evidence_status"] == "claim_mismatch"
    assert decided["false_reveals"] is decided["paid_false_revealers"] is None
    assert decided["reference_applicable"] is False
    assert decided["actual_claim_sha256"] == digest(b"Different actual claim")


def test_readout_rejects_different_retained_seed(retained_run, tmp_path):
    _, episode_path, manifest, _ = retained_run
    manifest["config"]["seed"] += 1
    (episode_path.parent / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="run settings"):
        readout.read_campaign(tmp_path, fixture=True)


def test_readout_rejects_different_runtime_provenance(retained_run, tmp_path):
    _, episode_path, manifest, _ = retained_run
    manifest["provenance"]["source_sha256"] = {"harness/src/veracity_harness/runner.py": "b" * 64}
    (episode_path.parent / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="runtime source hashes"):
        readout.read_campaign(tmp_path, fixture=True)


def test_fixture_readout_refuses_provider_backed_retained_run(retained_run, tmp_path):
    _, episode_path, manifest, _ = retained_run
    manifest["agent_backend"] = "cloudflare"
    (episode_path.parent / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="injected test models"):
        readout.read_campaign(tmp_path, fixture=True)
