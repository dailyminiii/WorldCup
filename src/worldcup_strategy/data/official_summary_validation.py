"""Scientific validation for official match-summary inputs."""

from __future__ import annotations

import pandas as pd

from worldcup_strategy.data.official_summary_schemas import (
    EVENT_COLUMNS,
    MATCH_COLUMNS,
    STAT_COLUMNS,
)


def validate_official_summary(
    matches: pd.DataFrame, events: pd.DataFrame, statistics: pd.DataFrame, year: int
) -> dict[str, object]:
    """Validate structure, provenance, group coverage, conflicts, and goal totals."""
    errors: list[str] = []
    warnings: list[str] = []
    for label, frame, required in (
        ("matches", matches, MATCH_COLUMNS),
        ("events", events, EVENT_COLUMNS),
        ("statistics", statistics, STAT_COLUMNS),
    ):
        missing = sorted(set(required) - set(frame.columns))
        if missing:
            errors.append(f"{label}: missing columns {missing}")
    if matches["match_id"].duplicated().any():
        errors.append("duplicate match_id")
    selected = matches[(matches["tournament_year"] == year) & (matches["stage"] == "Group Stage")]
    if len(selected) != 3:
        errors.append(f"expected exactly three group-stage matches, found {len(selected)}")
    if not ((selected["home_team_id"] == "KOR") | (selected["away_team_id"] == "KOR")).all():
        errors.append("a selected match does not include Korea Republic")
    if matches["verification_status"].eq("conflicting").any():
        warnings.append("source conflicts remain preserved")
    if matches["duration_verification_status"].ne("verified").any():
        warnings.append("some match durations remain approximate")
    goals = events[events["is_goal"].eq(True)]
    if goals["source_url"].isna().any() or goals["verification_status"].isna().any():
        errors.append("every goal must have provenance and verification status")
    return {
        "year": year,
        "match_count": len(selected),
        "goal_count": len(goals),
        "conflict_count": int(matches["verification_status"].eq("conflicting").sum()),
        "approximate_duration_count": int(
            matches["duration_verification_status"].ne("verified").sum()
        ),
        "errors": errors,
        "warnings": warnings,
        "valid": not errors,
    }
