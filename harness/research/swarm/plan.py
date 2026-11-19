"""Generate legacy swarm designs as plans for the current campaign controller."""

import argparse
from os.path import relpath
from pathlib import Path

from veracity_harness.campaign import Assignment, CampaignPlan

RESEARCH = Path(__file__).resolve().parents[1]
PRESET_DIRECTORIES = {
    "principles": "swarm",
    "seven-juror": "swarm7",
    "scale": "swarm-scale",
}
SCALE_MODELS = (
    ("deepseek-pro", "@cf/deepseek-ai/deepseek-v4-pro-0813"),
    ("kimi", "@cf/moonshotai/kimi-k2.6"),
    ("kimi-code", "@cf/moonshotai/kimi-k2.7-code"),
)
PEER_MODELS = (
    *SCALE_MODELS,
    ("deepseek-flash", "@cf/deepseek-ai/deepseek-v4.1-flash-1017"),
    ("glm", "@cf/zai-org/glm-5.3"),
)


def legacy_plan(preset: str, output: Path) -> CampaignPlan:
    directory = RESEARCH / PRESET_DIRECTORIES[preset]
    plan_directory = output.parent.resolve()
    if preset == "scale":
        models = SCALE_MODELS
        schedule = []
        for line in (directory / "plan.txt").read_text(encoding="utf-8").splitlines():
            fields = line.partition("#")[0].split()
            if fields:
                config, seed = fields
                schedule.append((config, int(seed)))
    else:
        models = PEER_MODELS
        schedule = [
            (f"{arm}-peers.toml", seed)
            for index, seed in enumerate(range(811, 816))
            for arm in (("collusion", "honest") if index % 2 else ("honest", "collusion"))
        ]

    assignments = []
    for filename, seed in schedule:
        config = Path(relpath(directory / filename, plan_directory))
        for slot, model in models:
            assignments.append(
                Assignment(
                    id=f"{slot}-{config.stem}-{seed}",
                    config=config,
                    model=model,
                    provider="cloudflare",
                    seed=seed,
                )
            )
    return CampaignPlan(name=f"legacy-swarm-{preset}", assignments=assignments)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preset", choices=PRESET_DIRECTORIES)
    parser.add_argument("--output", type=Path, required=True, help="New campaign plan JSON path")
    args = parser.parse_args()
    if args.output.suffix.casefold() != ".json":
        parser.error("--output must end in .json")
    try:
        data = legacy_plan(args.preset, args.output).model_dump_json(indent=2)
        with args.output.open("x", encoding="utf-8") as output:
            output.write(data + "\n")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
