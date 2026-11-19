import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from veracity_harness.campaign import CampaignPlan, freeze_plan

RESEARCH = Path(__file__).resolve().parents[1] / "research"
SCRIPT = RESEARCH / "swarm" / "plan.py"
SCALE_MODELS = {
    "@cf/deepseek-ai/deepseek-v4-pro-0813",
    "@cf/moonshotai/kimi-k2.6",
    "@cf/moonshotai/kimi-k2.7-code",
}
PEER_MODELS = SCALE_MODELS | {
    "@cf/deepseek-ai/deepseek-v4.1-flash-1017",
    "@cf/zai-org/glm-5.3",
}


@pytest.mark.parametrize(
    ("preset", "directory", "models", "assignment_count", "case_count"),
    [
        ("principles", "swarm", PEER_MODELS, 50, 50),
        ("seven-juror", "swarm7", PEER_MODELS, 50, 50),
        ("scale", "swarm-scale", SCALE_MODELS, 57, 63),
    ],
)
def test_emitted_legacy_assignment_matrix_freezes_offline(
    tmp_path, preset, directory, models, assignment_count, case_count
):
    target = tmp_path / f"{preset}.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), preset, "--output", str(target)],
        check=True,
        capture_output=True,
        text=True,
    )
    plan = CampaignPlan.model_validate_json(target.read_bytes())
    assert plan.name == f"legacy-swarm-{preset}"
    assert len(plan.assignments) == assignment_count
    assert {job.model for job in plan.assignments} == models
    assert {job.provider for job in plan.assignments} == {"cloudflare"}
    assert all(not job.config.is_absolute() for job in plan.assignments)
    assert {(target.parent / job.config).resolve().parent for job in plan.assignments} == {
        RESEARCH / directory
    }

    if preset == "scale":
        expected_order = []
        for line in (RESEARCH / directory / "plan.txt").read_text().splitlines():
            if line and not line.startswith("#"):
                config, seed = line.split()
                expected_order.append((config, int(seed)))
    else:
        expected_order = [
            (f"{condition}-peers.toml", seed)
            for seed in range(811, 816)
            for condition in (("honest", "collusion") if seed % 2 else ("collusion", "honest"))
        ]
    for model in models:
        assert [
            (job.config.name, job.seed) for job in plan.assignments if job.model == model
        ] == expected_order

    frozen = freeze_plan(target)
    assert sum(job.experiment.episodes for job in frozen.assignments) == case_count
    assert {job.experiment.model.name for job in frozen.assignments} == models
    assert {job.experiment.model.provider for job in frozen.assignments} == {"cloudflare"}
    assert [job.experiment.seed for job in frozen.assignments] == [
        job.seed for job in plan.assignments
    ]
    expected_sizes = {
        "principles": {15: 50},
        "seven-juror": {7: 50},
        "scale": {3: 33, 7: 15, 15: 9},
    }
    assert Counter(job.experiment.jury_size for job in frozen.assignments) == expected_sizes[preset]
    assert all(job.documents_sha256 and job.inputs_sha256 for job in frozen.assignments)


def test_cli_preserves_an_existing_plan(tmp_path):
    target = tmp_path / "plan.json"
    existing = b"{}\n"
    target.write_bytes(existing)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "principles", "--output", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "File exists" in result.stderr
    assert target.read_bytes() == existing
