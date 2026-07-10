# mypy: ignore-errors
"""Pressure sequence construction."""

import pandas as pd


def build_pressure_sequences(pressures: pd.DataFrame, max_gap: float = 2.0) -> pd.DataFrame:
    rows = []
    sequence_id = 0
    for (_match_id, _team_id, _possession_id, _period), group in pressures.sort_values(
        ["match_id", "period", "event_index"]
    ).groupby(["match_id", "team_id", "possession_id", "period"], sort=False):
        current = []
        for pressure in group.itertuples(index=False):
            if current and pressure.elapsed_seconds - current[-1].elapsed_seconds > max_gap:
                rows.append(_sequence(current, sequence_id))
                sequence_id += 1
                current = []
            current.append(pressure)
        if current:
            rows.append(_sequence(current, sequence_id))
            sequence_id += 1
    return pd.DataFrame(rows)


def _sequence(items: list[object], sequence_id: int) -> dict[str, object]:
    first, last = items[0], items[-1]
    return {
        "match_id": first.match_id,
        "pressure_sequence_id": sequence_id,
        "pressing_team_id": first.team_id,
        "opponent_id": first.opponent_id,
        "possession_id": first.possession_id,
        "period": first.period,
        "sequence_start_seconds": first.elapsed_seconds,
        "sequence_end_seconds": last.elapsed_seconds,
        "sequence_duration_seconds": last.elapsed_seconds - first.elapsed_seconds,
        "pressure_event_count": len(items),
        "start_x_pressing_frame": first.x_pressing_team_frame,
        "end_x_pressing_frame": last.x_pressing_team_frame,
        "mean_pressure_height": sum(i.x_pressing_team_frame for i in items) / len(items),
        "max_pressure_height": max(i.x_pressing_team_frame for i in items),
        "is_counterpress_sequence": any(i.counterpress for i in items),
        "ended_in_turnover": False,
        "turnover_seconds": None,
        "turnover_event_id": None,
        "termination_reason": "gap_or_group_end",
    }
