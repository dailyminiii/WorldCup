# mypy: ignore-errors
"""Project-owned SPADL-compatible action conversion."""

from typing import Any

import pandas as pd

ACTION_TYPES = {"Pass": 0, "Carry": 21, "Dribble": 1, "Shot": 11}
BODY_PARTS = {"foot": 0, "head": 1, "other": 2}


def _result(event_type: str, outcome: object, is_goal: bool) -> tuple[int, str]:
    if event_type == "Shot":
        return (1, "success") if is_goal else (0, "fail")
    failure = outcome in {"Incomplete", "Out", "Pass Offside", "Lost", "Incomplete Saved"}
    return (0, "fail") if failure else (1, "success")


def build_spadl_actions(
    events: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame | None = None,
    players: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Convert canonical events to a stable SPADL-compatible project table.

    The canonical StatsBomb coordinates are already expressed from the acting team's
    left-to-right perspective. This adapter deliberately owns the public schema rather than
    exposing socceraction internals, whose provider loader expects raw-data objects.
    """
    del teams, players
    selected = events[events["event_type"].isin(ACTION_TYPES)].copy()
    selected = selected.sort_values(["match_id", "period", "event_index"], kind="stable")
    match_meta = matches.set_index("match_id")
    rows: list[dict[str, Any]] = []
    for match_id, group in selected.groupby("match_id", sort=False):
        meta = match_meta.loc[match_id]
        for action_id, row in enumerate(group.itertuples(index=False)):
            event_type = str(row.event_type)
            result_id, result_name = _result(event_type, row.outcome, bool(row.is_goal))
            body = str(row.body_part).lower() if pd.notna(row.body_part) else "other"
            body_name = "head" if "head" in body else "foot" if "foot" in body else "other"
            rows.append(
                {
                    "provider": row.provider,
                    "competition_id": int(meta.competition_id),
                    "season_id": int(meta.season_id),
                    "match_id": int(match_id),
                    "game_id": int(match_id),
                    "action_id": action_id,
                    "period_id": int(row.period),
                    "time_seconds": float(row.elapsed_seconds),
                    "team_id": int(row.team_id),
                    "player_id": row.player_id,
                    "start_x": row.start_x_normalized,
                    "start_y": row.start_y_normalized,
                    "end_x": row.end_x_normalized,
                    "end_y": row.end_y_normalized,
                    "type_id": ACTION_TYPES[event_type],
                    "type_name": event_type.lower(),
                    "result_id": result_id,
                    "result_name": result_name,
                    "bodypart_id": BODY_PARTS[body_name],
                    "bodypart_name": body_name,
                    "original_event_id": row.event_id,
                    "group_name": meta.group_name,
                    "competition_stage": meta.competition_stage,
                    "match_week": int(meta.match_week),
                    "source_start_x_raw": row.start_x_raw,
                    "source_start_y_raw": row.start_y_raw,
                    "source_end_x_raw": row.end_x_raw,
                    "source_end_y_raw": row.end_y_raw,
                    "possession_id": int(row.possession_id),
                    "play_pattern": row.play_pattern,
                    "is_penalty_shootout": bool(row.is_penalty_shootout),
                }
            )
    return pd.DataFrame(rows)


def orientation_diagnostics(actions: pd.DataFrame) -> dict[str, Any]:
    """Validate normalized shot direction by team and period."""
    shots = actions[actions["type_name"] == "shot"]
    rows: list[dict[str, Any]] = []
    wrong = 0
    meaningful = 0
    for (team_id, period), group in shots.groupby(["team_id", "period_id"], sort=True):
        valid = group.dropna(subset=["start_x", "end_x"])
        toward = valid["end_x"] >= valid["start_x"]
        if len(valid) >= 3:
            meaningful += len(valid)
            wrong += int((~toward).sum())
        rows.append(
            {
                "team_id": int(team_id),
                "period": int(period),
                "shot_count": len(group),
                "median_shot_start_x": valid["start_x"].median() if len(valid) else None,
                "median_shot_end_x": valid["end_x"].median() if len(valid) else None,
                "proportion_shots_toward_right_goal": toward.mean() if len(valid) else None,
                "invalid_coordinate_count": len(group) - len(valid),
            }
        )
    proportion_wrong = wrong / meaningful if meaningful else 0.0
    return {
        "definition": "acting_team_attacks_left_to_right",
        "shot_count": len(shots),
        "meaningful_shot_count": meaningful,
        "wrong_direction_count": wrong,
        "wrong_direction_proportion": proportion_wrong,
        "valid": proportion_wrong <= 0.10,
        "by_team_period": rows,
    }
