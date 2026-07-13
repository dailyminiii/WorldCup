# ruff: noqa: E501
# mypy: ignore-errors
"""Deterministic figures for the Korea preliminary case study."""

from pathlib import Path

import pandas as pd

from worldcup_strategy.analysis.korea.pipeline import FIGURES, compare, reconstruct_score_state
from worldcup_strategy.analysis.pressing.figures import _pdf, _png


def _render(number: int, title: str, labels: list[str], values: list[float], note: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    stem = FIGURES / f"figure_{number}"
    pd.DataFrame({"label": labels, "value": values}).to_csv(
        stem.with_name(stem.name + "_source.csv"), index=False
    )
    maximum = max(values or [1.0]) or 1.0
    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        height = 330 * max(0, value) / maximum
        x = 80 + index * (740 / max(1, len(values)))
        bars.append(
            f'<rect x="{x:.1f}" y="{480 - height:.1f}" width="70" height="{height:.1f}" fill="#31688e"/><text x="{x + 35:.1f}" y="510" text-anchor="middle" font-size="11">{label}</text><text x="{x + 35:.1f}" y="{465 - height:.1f}" text-anchor="middle" font-size="11">{value:.2f}</text>'
        )
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600"><rect width="900" height="600" fill="white"/><style>text{{font-family:Arial;fill:#222}}</style><text x="40" y="40" font-size="23">Figure {number}. {title}</text><line x1="50" y1="480" x2="860" y2="480" stroke="#333"/>{"".join(bars)}<text x="40" y="575" font-size="11">{note}</text></svg>\n'
    stem.with_suffix(".svg").write_text(svg)
    _png(stem.with_suffix(".png"), values)
    _pdf(stem.with_suffix(".pdf"), f"Figure {number}. {title}", values)


def generate_figures() -> list[Path]:
    match, tournament = compare()
    exposure = reconstruct_score_state()
    timeline = exposure.sort_values(["tournament_year", "match_id"])
    _render(
        1,
        "Group-stage match timelines",
        [str(x) for x in timeline.match_id],
        [float(x) for x in timeline.score_state_changes],
        "Goal-driven score-state changes; cards/substitutions are absent where not verified.",
    )
    values, labels = [], []
    for row in tournament.to_dict("records"):
        for state in ("leading", "drawing", "trailing"):
            labels.append(f"{row['tournament_year']} {state[0].upper()}")
            values.append(float(row[f"{state}_minutes"]))
    _render(
        2,
        "Score-state exposure",
        labels,
        values,
        "Minutes include stoppage; two 2026 durations are approximate.",
    )
    _render(
        3,
        "Match outcomes",
        [f"{y} {m}" for y in (2022, 2026) for m in ("Pts", "GF", "GA", "GD")],
        [
            float(tournament.set_index("tournament_year").loc[y, c])
            for y in (2022, 2026)
            for c in ("points", "goals_for", "goals_against", "goal_difference")
        ],
        "Raw three-match group-stage totals.",
    )
    _render(
        4,
        "Comparable whole-match metrics",
        [f"{r.tournament_year}-{r.opponent_name}" for r in match.itertuples()],
        [float(r.points) for r in match.itertuples()],
        "Only verified common match-level points are plotted; incomplete statistics are excluded.",
    )
    _render(
        5,
        "Data-availability boundary",
        ["Summary", "Event", "360"],
        [1, 0, 0],
        "2026 Event/360 tactical metrics await complete validated data.",
    )
    return sorted(FIGURES.glob("figure_*"))
