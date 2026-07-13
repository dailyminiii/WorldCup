"""Import normalized official summaries without filling missing values."""
# mypy: ignore-errors

from __future__ import annotations

from pathlib import Path

import pandas as pd

from worldcup_strategy.data.official_summary_validation import validate_official_summary


def read_official_summary(directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three canonical official-summary inputs."""
    matches = pd.read_csv(directory / "matches.csv", keep_default_na=True)
    events = pd.read_csv(directory / "match_events.csv", keep_default_na=True)
    statistics = pd.read_csv(directory / "match_statistics.csv", keep_default_na=True)
    for column in ("is_goal", "is_own_goal", "is_penalty", "is_red_card", "is_second_yellow"):
        events[column] = events[column].astype("boolean")
    return matches, events, statistics


def import_official_summary(directory: Path, output: Path, year: int = 2026) -> pd.DataFrame:
    """Create one Korea team-match row per verified match and preserve null statistics."""
    matches, events, statistics = read_official_summary(directory)
    validation = validate_official_summary(matches, events, statistics, year)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))
    rows: list[dict[str, object]] = []
    for match in matches.sort_values("match_date").to_dict("records"):
        korea_home = match["home_team_id"] == "KOR"
        row = dict(match)
        row.update(
            opponent_name=match["away_team_name"] if korea_home else match["home_team_name"],
            goals_for=match["home_score"] if korea_home else match["away_score"],
            goals_against=match["away_score"] if korea_home else match["home_score"],
        )
        values = statistics[
            (statistics["match_id"] == match["match_id"]) & (statistics["team_id"] == "KOR")
        ]
        for item in values.to_dict("records"):
            row[str(item["metric_name"])] = item["metric_value"]
        rows.append(row)
    frame = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    return frame
