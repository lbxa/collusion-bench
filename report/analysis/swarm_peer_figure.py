"""Plot direct peer exposure in the frozen historical swarm replication."""

import argparse
from pathlib import Path
from typing import NamedTuple

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from swarm_historical_summary import VOTES, load_replication

JURY_SIZES = (3, 7, 15)
PEER_POLICIES = (("honest", "Honest"), ("collusion", "Adverse"))
OUTCOMES = (
    ("truthful_reveals", "Correct reveal", "#0072B2", ""),
    ("false_reveals", "False reveal", "#D55E00", "///"),
    ("no_commitment", "No commitment", "#DDDDDD", ""),
    ("unrevealed_commitments", "Unrevealed commitment", "white", "xxx"),
)


class PeerOutcome(NamedTuple):
    peer_policy: str
    votes: tuple[int, ...]
    assigned_cases: int
    false_settlements: int


def peer_outcomes() -> list[PeerOutcome]:
    cases = load_replication()["cases"]
    outcomes = []
    for jury_size in JURY_SIZES:
        evaluated_per_case = (jury_size + 1) // 2
        for policy, label in PEER_POLICIES:
            arm = f"n{jury_size}-{policy}"
            assigned = [case for case in cases if case["arm"] == arm]
            if not assigned or any(
                sum(case[key] for key in VOTES.values()) != evaluated_per_case
                for case in assigned
            ):
                raise ValueError(f"Assigned evaluated seats do not reconcile for {arm}")
            outcomes.append(
                PeerOutcome(
                    peer_policy=label,
                    votes=tuple(
                        sum(case[VOTES[key]] for case in assigned)
                        for key, _, _, _ in OUTCOMES
                    ),
                    assigned_cases=len(assigned),
                    false_settlements=sum(case["captured"] for case in assigned),
                )
            )
    return outcomes


def render(outcomes: list[PeerOutcome], output: Path) -> None:
    pair_centers = (6.5, 4, 1.5)
    positions = [center + offset for center in pair_centers for offset in (0.5, -0.5)]
    seat_counts = [sum(outcome.votes) for outcome in outcomes]
    with plt.rc_context(
        {
            "font.family": "serif",
            "font.serif": ["cmr10"],
            "font.size": 9,
            "axes.formatter.use_mathtext": True,
            "pdf.fonttype": 42,
            "hatch.linewidth": 0.45,
            "text.color": "#222222",
            "axes.labelcolor": "#222222",
        }
    ):
        figure, (votes, settlements) = plt.subplots(
            1,
            2,
            sharey=True,
            figsize=(6.5, 3.5),
            gridspec_kw={"width_ratios": (1.4, 1)},
        )
        figure.subplots_adjust(
            left=0.19, right=0.97, top=0.88, bottom=0.22, wspace=0.36
        )

        left = [0.0] * len(outcomes)
        for index, (_, label, color, hatch) in enumerate(OUTCOMES):
            shares = [
                outcome.votes[index] / seats
                for outcome, seats in zip(outcomes, seat_counts, strict=True)
            ]
            votes.barh(
                positions,
                shares,
                height=0.7,
                left=left,
                color=color,
                edgecolor="#444444",
                linewidth=0.5,
                hatch=hatch,
                label=label,
            )
            left = [start + share for start, share in zip(left, shares, strict=True)]

        votes.set_yticks(positions, [outcome.peer_policy for outcome in outcomes])
        row_coordinates = votes.get_yaxis_transform()
        for size, center in zip(JURY_SIZES, pair_centers, strict=True):
            votes.text(
                -0.46, center, f"{size} jurors", transform=row_coordinates, va="center"
            )
        for y, seats in zip(positions, seat_counts, strict=True):
            votes.text(
                1.035, y, f"n={seats}", transform=row_coordinates, va="center", fontsize=8.5
            )

        rates = [
            outcome.false_settlements / outcome.assigned_cases for outcome in outcomes
        ]
        settlements.scatter(
            rates, positions, s=21, color="#A84700", clip_on=False, zorder=3
        )
        for y, rate, outcome in zip(positions, rates, outcomes, strict=True):
            settlements.annotate(
                f"{outcome.false_settlements}/{outcome.assigned_cases}",
                (rate, y),
                xytext=(6, 0),
                textcoords="offset points",
                va="center",
            )
        settlements.tick_params(axis="y", labelleft=False)

        votes.set_title("(a) Evaluated juror outcomes", loc="left", fontsize=10)
        settlements.set_title("(b) False-claim settlements", loc="left", fontsize=10)
        votes.set_xlabel("Share of evaluated seats")
        settlements.set_xlabel("Share of assigned cases")
        for axis in (votes, settlements):
            axis.set(xlim=(0, 1), ylim=(0.4, 7.6), xticks=(0, 0.25, 0.5, 0.75, 1))
            axis.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
            axis.tick_params(axis="both", length=0)
            axis.set_axisbelow(True)
            axis.grid(axis="x", color="#D8D8D8", linewidth=0.5)
            axis.spines[["left", "right", "top"]].set_visible(False)
            axis.spines["bottom"].set_color("#888888")
            axis.spines["bottom"].set_linewidth(0.6)

        handles, labels = votes.get_legend_handles_labels()
        figure.legend(handles, labels, loc="lower center", ncols=4, frameon=False)
        figure.savefig(output, metadata={"CreationDate": None, "ModDate": None})
        plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(peer_outcomes(), args.output)
