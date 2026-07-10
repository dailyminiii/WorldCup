"""Canonical provider-independent schema contracts."""

from collections.abc import Mapping

import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

CANONICAL_COLUMNS: Mapping[str, tuple[str, ...]] = {
    "competitions": (
        "provider",
        "competition_id",
        "season_id",
        "competition_name",
        "season_name",
        "country_name",
        "gender",
        "is_international",
    ),
    "matches": (
        "provider",
        "competition_id",
        "season_id",
        "match_id",
        "match_date",
        "kickoff_datetime",
        "competition_stage",
        "group_name",
        "match_week",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_score",
        "away_score",
        "status",
        "stadium",
        "referee",
    ),
    "events": (
        "provider",
        "match_id",
        "event_id",
        "event_index",
        "period",
        "minute",
        "second",
        "timestamp",
        "elapsed_seconds",
        "team_id",
        "team_name",
        "player_id",
        "player_name",
        "possession_id",
        "possession_team_id",
        "event_type",
        "event_subtype",
        "outcome",
        "play_pattern",
        "under_pressure",
        "counterpress",
        "start_x_raw",
        "start_y_raw",
        "end_x_raw",
        "end_y_raw",
        "start_x_105",
        "start_y_68",
        "end_x_105",
        "end_y_68",
        "start_x_normalized",
        "start_y_normalized",
        "end_x_normalized",
        "end_y_normalized",
        "body_part",
        "technique",
        "statsbomb_xg",
        "is_goal",
        "is_own_goal",
        "is_penalty",
        "is_penalty_shootout",
        "is_set_piece",
        "raw_event_json",
    ),
    "freeze_frames": (
        "match_id",
        "event_id",
        "frame_player_index",
        "player_id",
        "teammate",
        "actor",
        "keeper",
        "x_raw",
        "y_raw",
        "x_normalized",
        "y_normalized",
    ),
    "visible_areas": (
        "match_id",
        "event_id",
        "polygon_raw",
        "polygon_normalized",
        "polygon_area",
    ),
    "lineups": ("provider", "match_id", "team_id", "team_name", "player_id", "player_name"),
}

EVENT_VALIDATION_SCHEMA = DataFrameSchema(
    {
        "match_id": Column(int, nullable=False),
        "event_id": Column(str, nullable=False),
        "event_index": Column(int, Check.ge(0), nullable=False),
        "period": Column(int, Check.ge(1), nullable=False),
        "minute": Column(int, Check.ge(0), nullable=False),
        "start_x_raw": Column(float, Check.in_range(0, 120), nullable=True),
        "start_y_raw": Column(float, Check.in_range(0, 80), nullable=True),
    },
    strict=False,
    coerce=True,
)


def empty_table(name: str) -> pd.DataFrame:
    """Return an empty table with the exact canonical column order."""
    return pd.DataFrame(columns=CANONICAL_COLUMNS[name])


def enforce_columns(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    """Fail on missing canonical fields and return deterministic column order."""
    expected = CANONICAL_COLUMNS[name]
    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing canonical columns: {sorted(missing)}")
    return frame.loc[:, list(expected)]
