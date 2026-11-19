"""Build the fixed, unpaid swarm assignment plan for the campaign controller."""

import argparse
from os.path import relpath
from pathlib import Path

from veracity_harness.campaign import Assignment, CampaignPlan, digest
from veracity_harness.config import load_experiment
from veracity_harness.resistance import (
    CONFIRMATION_CASES,
    STUDY_DIRECTORY,
    V1_ROSTER,
    ScenarioRegistry,
)

DIRECTORY = Path(__file__).resolve().parent
SEEDS = (901, 902, 903, 904, 905)
JURY_SIZES = (3, 7, 15)
PEER_VERDICTS = {
    "honest": "CHALLENGER_SUPPORTED",
    "adverse": "CREATOR_SUPPORTED",
}
ARM_IDS = tuple(f"n{size}-{policy}" for size in JURY_SIZES for policy in PEER_VERDICTS)


def validated_arms() -> dict[str, Path]:
    """Reject source drift and unregistered differences between experimental arms."""
    baseline = load_experiment(STUDY_DIRECTORY / "paid-false-basic.toml")
    registry = ScenarioRegistry.model_validate_json(
        (STUDY_DIRECTORY / "scenario-bank.json").read_bytes()
    )
    sources = {source.scenario_id: source for source in registry.scenarios}
    for source_id, case in zip(CONFIRMATION_CASES, baseline.schedule, strict=True):
        source = sources.get(source_id)
        if (
            source is None
            or case.document != (STUDY_DIRECTORY / source.document).resolve()
            or case.reference_claim != source.false_claim
            or case.expected_verdict != "CHALLENGER_SUPPORTED"
            or digest(case.document.read_bytes()) != source.source_sha256
        ):
            raise ValueError(f"Source or reference mismatch for {source_id}")

    parameters = baseline.parameters.model_copy(
        update={
            "beta_wei": "100000000000000000000",
            "gamma_bps": 500,
            "winner_bps": 8500,
            "juror_bps": 500,
        }
    )
    paths = {}
    peer_messages: dict[str, set[str]] = {}
    for size in JURY_SIZES:
        peers = tuple(f"juror-{i}" for i in range(size // 2 + 2, size + 1))
        for policy, verdict in PEER_VERDICTS.items():
            arm = f"n{size}-{policy}"
            path = DIRECTORY / f"{arm}-peers.toml"
            experiment = load_experiment(path)
            expected = baseline.model_copy(
                update={
                    "name": f"sbv1-{arm}",
                    "seed": SEEDS[0],
                    "jury_size": size,
                    "peer_verdict": verdict,
                    "peer_offers": experiment.peer_offers,
                    "constitution": "principles",
                    "parameters": parameters,
                }
            )
            if experiment != expected or experiment.peer_jurors != peers:
                raise ValueError(f"Unexpected experimental settings for {arm}")
            messages = set(experiment.peer_offers.values())
            if len(messages) != 1 or messages != peer_messages.setdefault(policy, messages):
                raise ValueError(f"Peer messages vary within the {policy} policy")
            paths[arm] = path
    if peer_messages["honest"] == peer_messages["adverse"]:
        raise ValueError("The peer policies must deliver different messages")
    return paths


def build_plan(path: Path) -> CampaignPlan:
    relative_arms = {
        arm: Path(relpath(config, path.parent.resolve()))
        for arm, config in validated_arms().items()
    }
    slots = tuple(V1_ROSTER)
    policies = tuple(PEER_VERDICTS)
    assignments = []
    for seed_index, seed in enumerate(SEEDS):
        for round_index in range(len(JURY_SIZES)):
            for offset in range(len(slots)):
                model_index = (seed_index + offset) % len(slots)
                slot = slots[model_index]
                provider, _, model = V1_ROSTER[slot]
                size_index = (round_index + model_index + seed_index) % len(JURY_SIZES)
                size = JURY_SIZES[size_index]
                order = policies[::-1] if (seed_index + model_index + size_index) % 2 else policies
                for policy in order:
                    arm = f"n{size}-{policy}"
                    assignments.append(
                        Assignment(
                            id=f"sbv1-{slot}-{arm}-{seed}",
                            config=relative_arms[arm],
                            model=model,
                            provider=provider,
                            seed=seed,
                        )
                    )
    return CampaignPlan(name="swarm-benchmark-v1", assignments=assignments)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON plan path")
    args = parser.parse_args()
    if args.output.suffix.casefold() != ".json":
        parser.error("The campaign plan path must end with .json")
    try:
        plan = build_plan(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            output.write(plan.model_dump_json(indent=2) + "\n")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Wrote {len(plan.assignments)} assignments to {args.output}")


if __name__ == "__main__":
    main()
