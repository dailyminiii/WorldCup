# mypy: ignore-errors
"""Homogeneous score and numerical-state segments."""

from itertools import pairwise

import pandas as pd


def build_segments(states: pd.DataFrame, gap_cap: float = 30.0) -> pd.DataFrame:
    """Split each team-period perspective at regular goals and dismissals."""
    rows: list[dict[str, object]] = []
    eligible = states[states.period.isin([1, 2, 3, 4])].sort_values(
        ["match_id", "team_id", "period", "event_index"]
    )
    for (match_id, team_id, period), group in eligible.groupby(
        ["match_id", "team_id", "period"], sort=False
    ):
        group = group.sort_values(["elapsed_seconds", "event_index"])
        start = float(group.elapsed_seconds.min())
        end = float(group.elapsed_seconds.max())
        changes = group[
            (group.goal_difference_after != group.goal_difference_before)
            | (group.red_card_difference_after != group.red_card_difference_before)
        ]
        boundaries = [
            start,
            *sorted({float(value) for value in changes.elapsed_seconds if start < value < end}),
            end,
        ]
        opponent = int(group.opponent_id.iloc[0])
        for index, (segment_start, segment_end) in enumerate(pairwise(boundaries)):
            if segment_end <= segment_start:
                continue
            initial_rows = group[group.elapsed_seconds <= segment_start]
            initial = initial_rows.tail(1).iloc[0] if len(initial_rows) else group.iloc[0]
            score_state = (
                initial.score_state_after if len(initial_rows) else initial.score_state_before
            )
            goal_difference = (
                initial.goal_difference_after
                if len(initial_rows)
                else initial.goal_difference_before
            )
            red_difference = (
                initial.red_card_difference_after
                if len(initial_rows)
                else initial.red_card_difference_before
            )
            numerical_state = (
                initial.numerical_state_after
                if len(initial_rows)
                else initial.numerical_state_before
            )
            interval_events = group[
                (group.elapsed_seconds > segment_start) & (group.elapsed_seconds <= segment_end)
            ]
            gaps = interval_events.elapsed_seconds.diff().dropna().tolist()
            if len(interval_events):
                gaps = [float(interval_events.elapsed_seconds.iloc[0] - segment_start), *gaps]
            last_event = (
                float(interval_events.elapsed_seconds.max())
                if len(interval_events)
                else segment_start
            )
            gaps.append(segment_end - last_event)
            effective = sum(min(max(float(gap), 0.0), gap_cap) for gap in gaps)
            prior = changes[changes.elapsed_seconds == segment_start]
            following = changes[changes.elapsed_seconds == segment_end]

            def trigger(frame: pd.DataFrame, fallback: str) -> str:
                if frame.empty:
                    return fallback
                row = frame.iloc[0]
                if row.goal_difference_after != row.goal_difference_before:
                    return "goal"
                return "red_card"

            rows.append(
                {
                    "match_id": match_id,
                    "team_id": team_id,
                    "opponent_id": opponent,
                    "segment_id": f"{match_id}:{period}:{index}",
                    "period": period,
                    "segment_start_seconds": segment_start,
                    "segment_end_seconds": segment_end,
                    "segment_duration_seconds": segment_end - segment_start,
                    "effective_play_seconds": effective,
                    "score_state": score_state,
                    "goal_difference": goal_difference,
                    "red_card_difference": red_difference,
                    "numerical_state": numerical_state,
                    "start_trigger": trigger(prior, "period_start"),
                    "end_trigger": trigger(following, "period_end"),
                    "state_segment_version": "state_segment_goal_redcard_period_v1",
                }
            )
    return pd.DataFrame(rows)
