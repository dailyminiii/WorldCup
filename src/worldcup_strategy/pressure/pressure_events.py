# mypy: ignore-errors
"""Canonical StatsBomb Pressure-event table."""

import pandas as pd

from worldcup_strategy.pressure.frames import possession_frame


def build_pressure_events(
    events: pd.DataFrame, matches: pd.DataFrame, frame_event_ids: set[str] | None = None
) -> pd.DataFrame:
    frame_event_ids = frame_event_ids or set()
    match_map = matches.set_index("match_id")
    rows: list[dict[str, object]] = []
    for row in events[(events.event_type == "Pressure") & ~events.is_penalty_shootout].itertuples(
        index=False
    ):
        match = match_map.loc[row.match_id]
        opponent = int(
            match.away_team_id
            if int(match.home_team_id) == int(row.team_id)
            else match.home_team_id
        )
        px, py = possession_frame(
            row.start_x_normalized,
            row.start_y_normalized,
            acting_team_id=int(row.team_id),
            possession_team_id=int(row.possession_team_id),
        )
        press_x, press_y = row.start_x_normalized, row.start_y_normalized
        rows.append(
            {
                "match_id": row.match_id,
                "event_id": row.event_id,
                "event_index": row.event_index,
                "period": row.period,
                "elapsed_seconds": row.elapsed_seconds,
                "team_id": row.team_id,
                "opponent_id": opponent,
                "possession_id": row.possession_id,
                "possession_team_id": row.possession_team_id,
                "play_pattern": row.play_pattern,
                "counterpress": bool(row.counterpress) if pd.notna(row.counterpress) else False,
                "start_x": row.start_x_normalized,
                "start_y": row.start_y_normalized,
                "x_possession_frame": px,
                "y_possession_frame": py,
                "x_pressing_team_frame": press_x,
                "y_pressing_team_frame": press_y,
                "pressure_zone": "high" if press_x >= 63 else "other",
                "is_high_pressure": press_x >= 63,
                "has_360": row.event_id in frame_event_ids,
            }
        )
    return pd.DataFrame(rows)
