# mypy: ignore-errors
"""Fixed period-local team windows with transition-overlap state durations."""

import math

import pandas as pd

PERIOD_START = {1: 0.0, 2: 2700.0, 3: 5400.0, 4: 6300.0}


def _majority(durations: dict[str, float], end_state: str) -> tuple[str, bool]:
    maximum = max(durations.values())
    tied = [key for key, value in durations.items() if abs(value - maximum) < 1e-9]
    return (end_state if end_state in tied else sorted(tied)[0], len(tied) > 1)


def build_windows(
    states: pd.DataFrame, window_seconds: float = 300.0, gap_cap: float = 30.0
) -> pd.DataFrame:
    rows = []
    eligible = states[states.period.isin([1, 2, 3, 4])].sort_values(
        ["match_id", "team_id", "period", "event_index"]
    )
    for (match_id, team_id, period), group in eligible.groupby(
        ["match_id", "team_id", "period"], sort=False
    ):
        start = PERIOD_START[int(period)]
        period_end = float(group.elapsed_seconds.max())
        count = max(1, math.ceil((period_end - start) / window_seconds))
        opponent = int(group.opponent_id.iloc[0])
        for index in range(count):
            ws = start + index * window_seconds
            we = (
                period_end
                if index == count - 1
                else min(start + (index + 1) * window_seconds, period_end)
            )
            selected = group[(group.elapsed_seconds > ws) & (group.elapsed_seconds <= we)]
            initial = group[group.elapsed_seconds <= ws].tail(1)
            initial = initial.iloc[0] if len(initial) else group.iloc[0]
            final = group[group.elapsed_seconds <= we].tail(1).iloc[0]
            score = {k: 0.0 for k in ("leading", "drawing", "trailing")}
            numerical = {k: 0.0 for k in ("advantage", "even", "disadvantage", "unknown")}
            effective = 0.0
            capped = 0.0
            cursor = ws
            current_score = (
                initial.score_state_after
                if len(group[group.elapsed_seconds <= ws])
                else initial.score_state_before
            )
            current_num = (
                initial.numerical_state_after
                if len(group[group.elapsed_seconds <= ws])
                else initial.numerical_state_before
            )
            goal_difference_start = (
                initial.goal_difference_after
                if len(group[group.elapsed_seconds <= ws])
                else initial.goal_difference_before
            )
            red_card_difference_start = (
                initial.red_card_difference_after
                if len(group[group.elapsed_seconds <= ws])
                else initial.red_card_difference_before
            )
            transitions = group[(group.elapsed_seconds > ws) & (group.elapsed_seconds < we)]
            for event in transitions.itertuples(index=False):
                duration = event.elapsed_seconds - cursor
                score[current_score] += duration
                bucket = (
                    "advantage"
                    if "advantage" in current_num
                    else "disadvantage"
                    if "disadvantage" in current_num
                    else "unknown"
                    if current_num == "unknown"
                    else "even"
                )
                numerical[bucket] += duration
                effective += min(duration, gap_cap)
                capped += max(0, duration - gap_cap)
                cursor = event.elapsed_seconds
                current_score = event.score_state_after
                current_num = event.numerical_state_after
            duration = we - cursor
            score[current_score] += duration
            bucket = (
                "advantage"
                if "advantage" in current_num
                else "disadvantage"
                if "disadvantage" in current_num
                else "unknown"
                if current_num == "unknown"
                else "even"
            )
            numerical[bucket] += duration
            effective += min(duration, gap_cap)
            capped += max(0, duration - gap_cap)
            score_majority, score_tied = _majority(score, final.score_state_after)
            num_majority, num_tied = _majority(numerical, bucket)
            rows.append(
                {
                    "match_id": match_id,
                    "team_id": team_id,
                    "opponent_id": opponent,
                    "period": period,
                    "window_index": index,
                    "window_start_seconds": ws,
                    "window_end_seconds": we,
                    "wall_clock_seconds": we - ws,
                    "effective_play_seconds": effective,
                    "event_count": len(selected),
                    "team_action_count": int((selected.event_team_id == team_id).sum()),
                    "opponent_action_count": int((selected.event_team_id == opponent).sum()),
                    "possession_seconds": None,
                    "opponent_possession_seconds": None,
                    "goal_difference_start": goal_difference_start,
                    "goal_difference_end": final.goal_difference_after,
                    "red_card_difference_start": red_card_difference_start,
                    "red_card_difference_end": final.red_card_difference_after,
                    "time_leading_seconds": score["leading"],
                    "time_drawing_seconds": score["drawing"],
                    "time_trailing_seconds": score["trailing"],
                    "time_numerical_advantage_seconds": numerical["advantage"],
                    "time_even_strength_seconds": numerical["even"],
                    "time_numerical_disadvantage_seconds": numerical["disadvantage"],
                    "time_numerical_unknown_seconds": numerical["unknown"],
                    "score_state_start": current_score
                    if not len(transitions)
                    else (
                        initial.score_state_after
                        if len(group[group.elapsed_seconds <= ws])
                        else initial.score_state_before
                    ),
                    "score_state_end": final.score_state_after,
                    "score_state_majority": score_majority,
                    "score_state_majority_tied": score_tied,
                    "numerical_state_start": (
                        initial.numerical_state_after
                        if len(group[group.elapsed_seconds <= ws])
                        else initial.numerical_state_before
                    ),
                    "numerical_state_end": final.numerical_state_after,
                    "numerical_state_majority": num_majority,
                    "numerical_state_majority_tied": num_tied,
                    "multiple_score_states": sum(v > 0 for v in score.values()) > 1,
                    "multiple_numerical_states": sum(v > 0 for v in numerical.values()) > 1,
                    "effective_time_method": "event_gap_cap_v1",
                    "effective_time_gap_cap_seconds": gap_cap,
                    "effective_time_capped_seconds": capped,
                    "effective_time_uncertainty": "event_derived_not_tracking",
                }
            )
    return pd.DataFrame(rows)
