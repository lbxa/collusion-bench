import subprocess
import sys
from collections import Counter
from itertools import product

import pytest

from veracity_harness import materials
from veracity_harness.campaign import CampaignPlan, digest, freeze_plan
from veracity_harness.config import load_experiment
from veracity_harness.resistance import V1_ROSTER
from veracity_harness.runner import ROOT

RESEARCH = ROOT / "harness/research"
STUDY = RESEARCH / "swarm-benchmark-v1"
PEER_POLICIES = ("honest", "adverse")
JURY_SIZES = (3, 7, 15)
SEED_LABELS = (901, 902, 903, 904, 905)


@pytest.fixture(scope="module")
def authored_plan(tmp_path_factory):
    output = tmp_path_factory.mktemp("swarm-plan") / "plan.json"
    command = [sys.executable, str(STUDY / "plan.py"), "--output", str(output)]
    subprocess.run(command, cwd=output.parent, check=True, capture_output=True)
    return output


def test_plan_freezes_the_balanced_frame_through_the_campaign_controller(authored_plan):
    plan = CampaignPlan.model_validate_json(authored_plan.read_bytes())
    assert plan.name == "swarm-benchmark-v1"
    assert all(not job.config.is_absolute() for job in plan.assignments)
    assert Counter(job.seed for job in plan.assignments) == dict.fromkeys(SEED_LABELS, 30)
    assert [job.seed for job in plan.assignments] == sorted(job.seed for job in plan.assignments)
    assert {job.id for job in plan.assignments} == {
        f"sbv1-{slot}-n{size}-{policy}-{seed}"
        for slot, size, policy, seed in product(V1_ROSTER, JURY_SIZES, PEER_POLICIES, SEED_LABELS)
    }

    frozen = freeze_plan(authored_plan)
    assert len(frozen.assignments) == 150
    assert sum(job.experiment.episodes for job in frozen.assignments) == 300
    for job in frozen.assignments:
        slot = job.id.split("-")[1]
        provider, _, name = V1_ROSTER[slot]
        assert job.experiment.model.provider == provider
        assert job.experiment.model_names == {name}
        assert set(job.inputs_sha256.values()) == {
            "7df1ed3bb8104a0b0bcf4e48c78b4c598b8533b92623d50f265d91050d6a0227",
            "81e94fabe095e2f81a12d78b14d9fc6b635e19a52cc92fb6847c9d7fd1812648",
        }
        assert job.documents_sha256["CONSTITUTION.md"] == digest(
            (materials.RESOURCES / "constitution-principles.md").read_bytes()
        )


def test_matched_peer_order_alternates_within_each_model_and_jury_size(authored_plan):
    plan = CampaignPlan.model_validate_json(authored_plan.read_bytes())
    for slot, size in product(V1_ROSTER, JURY_SIZES):
        first_policies = []
        for seed in SEED_LABELS:
            pair = [
                job.id.split("-")[3]
                for job in plan.assignments
                if job.seed == seed and job.id.startswith(f"sbv1-{slot}-n{size}-")
            ]
            assert set(pair) == set(PEER_POLICIES)
            first_policies.append(pair[0])
        assert all(one != two for one, two in zip(first_policies, first_policies[1:], strict=False))


@pytest.mark.parametrize("size", JURY_SIZES)
def test_paired_arms_preserve_sources_and_only_change_scripted_peer_policy(size):
    baseline = load_experiment(RESEARCH / "collusion-resistance-v1/paid-false-basic.toml")
    honest = load_experiment(STUDY / f"n{size}-honest-peers.toml")
    adverse = load_experiment(STUDY / f"n{size}-adverse-peers.toml")
    assert honest == adverse.model_copy(
        update={
            "name": honest.name,
            "peer_offers": honest.peer_offers,
            "peer_verdict": "CHALLENGER_SUPPORTED",
        }
    )
    assert adverse.peer_verdict == "CREATOR_SUPPORTED"
    assert set(honest.peer_offers.values()).isdisjoint(adverse.peer_offers.values())
    assert honest.schedule == baseline.schedule
    assert honest.scripted_setup_first and honest.network == "episodic"
    assert not honest.treatment.memory and not honest.treatment.shared_store
    assert honest.constitution == "principles" and honest.objective == "operator"
    majority = size // 2 + 1
    assert honest.peer_jurors == tuple(f"juror-{i}" for i in range(majority + 1, size + 1))

    for case in honest.schedule:
        docs = materials.documents(honest, "juror-1", "case-fixture", case)
        assert docs == materials.documents(adverse, "juror-1", "case-fixture", case)
        assert set(docs) == {
            "CONSTITUTION.md",
            "account.md",
            "case.md",
            "identity.json",
            "interface.md",
            "rules.md",
        }
        assert docs["case.md"] == case.document.read_text()
        assert case.reference_claim not in docs["account.md"]


def test_largest_jury_has_funded_offers_and_positive_ordinary_reward():
    experiment = load_experiment(STUDY / "n15-adverse-peers.toml")
    parameters = experiment.parameters
    beta = int(parameters.beta_wei)
    assert beta == 100 * 10**18
    assert beta * parameters.gamma_bps // 10_000 == 5 * 10**18
    assert beta * parameters.juror_bps // 10_000 == 5 * 10**18
    assert experiment.jury_size * int(experiment.offer_payment_wei) == 150 * 10**18
    assert beta * (10_000 + parameters.winner_bps) // 10_000 == 185 * 10**18
