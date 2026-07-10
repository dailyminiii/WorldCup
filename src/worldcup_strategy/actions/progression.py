# mypy: ignore-errors
"""Versioned progressive pass and carry definition."""

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ProgressionConfig:
    own_half: float = 30.0
    crossing: float = 15.0
    opponent_half: float = 10.0
    minimum_carry: float = 1.0
    maximum_carry: float = 60.0
    excluded_patterns: tuple[str, ...] = (
        "From Corner",
        "From Free Kick",
        "From Throw In",
        "From Goal Kick",
        "From Kick Off",
    )


DEFAULT_PROGRESSION_CONFIG = ProgressionConfig()


def compute_progression(
    actions: pd.DataFrame, cfg: ProgressionConfig = DEFAULT_PROGRESSION_CONFIG
) -> pd.DataFrame:
    """Apply inclusive goal-distance thresholds in normalized metric coordinates."""
    rows: list[dict[str, Any]] = []
    for row in actions.itertuples(index=False):
        reason: str | None = None
        if row.type_name not in {"pass", "carry", "dribble"}:
            reason = "ineligible_action_type"
        elif row.result_name != "success":
            reason = "unsuccessful_action"
        elif bool(row.is_penalty_shootout):
            reason = "penalty_shootout"
        elif (
            pd.isna(row.start_x) or pd.isna(row.start_y) or pd.isna(row.end_x) or pd.isna(row.end_y)
        ):
            reason = "missing_coordinates"
        elif row.type_name == "pass" and row.play_pattern in cfg.excluded_patterns:
            reason = "excluded_set_piece"
        start_d = end_d = reduction = threshold = None
        start_half = end_half = None
        if reason is None:
            length = math.hypot(row.end_x - row.start_x, row.end_y - row.start_y)
            if row.type_name in {"carry", "dribble"} and length < cfg.minimum_carry:
                reason = "carry_below_minimum_length"
            elif row.type_name in {"carry", "dribble"} and length > cfg.maximum_carry:
                reason = "carry_above_maximum_length"
            start_d = math.hypot(105 - row.start_x, 34 - row.start_y)
            end_d = math.hypot(105 - row.end_x, 34 - row.end_y)
            reduction = start_d - end_d
            start_half = "own" if row.start_x < 52.5 else "opponent"
            end_half = "own" if row.end_x < 52.5 else "opponent"
            threshold = (
                cfg.own_half
                if end_half == "own"
                else cfg.crossing
                if start_half == "own"
                else cfg.opponent_half
            )
        rows.append(
            {
                "match_id": row.match_id,
                "action_id": row.action_id,
                "original_event_id": row.original_event_id,
                "team_id": row.team_id,
                "player_id": row.player_id,
                "action_type": row.type_name,
                "start_goal_distance": start_d,
                "end_goal_distance": end_d,
                "goal_distance_reduction": reduction,
                "start_half": start_half,
                "end_half": end_half,
                "progressive_threshold": threshold,
                "is_progressive": bool(
                    reason is None
                    and reduction is not None
                    and threshold is not None
                    and reduction >= threshold
                ),
                "progression_definition": "progressive_goal_distance_v1",
                "progression_exclusion_reason": reason,
            }
        )
    return pd.DataFrame(rows)
