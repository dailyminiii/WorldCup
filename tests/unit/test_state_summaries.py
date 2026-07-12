"""Tests for pooled and unweighted score-state summaries."""

import pandas as pd

from worldcup_strategy.state.summaries import summarize_score_state


def test_pooled_rate_preserves_raw_denominator() -> None:
    frame = pd.DataFrame(
        {
            "score_state_majority": ["drawing", "drawing"],
            "team_id": [1, 2],
            "match_id": [1, 1],
            "effective_play_seconds": [100.0, 200.0],
            "possessions": [2, 3],
            "shots_per_effective_10min": [6.0, 6.0],
            "shots_per_effective_10min_numerator": [1, 2],
            "shots_per_effective_10min_denominator": [100, 200],
            "shots_per_effective_10min_reliable": [True, True],
            "shots_per_effective_10min_unreliable_reason": [None, None],
            "pressure_regain_5s_rate": [1.0, 0.0],
            "pressure_regain_5s_rate_numerator": [1, 0],
            "pressure_regain_5s_rate_denominator": [1, 9],
            "pressure_regain_5s_rate_reliable": [False, True],
            "pressure_regain_5s_rate_unreliable_reason": ["below_minimum_pressure_events", None],
        }
    )
    for outcome in summarize_score_state.__globals__["OUTCOMES"]:
        if outcome not in frame:
            frame[outcome] = 0.0
    summary = summarize_score_state(frame)
    pressure = summary[summary.outcome == "pressure_regain_5s_rate"].iloc[0]
    assert pressure.raw_denominator == 10
    assert pressure.pooled_rate == 0.1
    assert pressure["mean"] == 0.5
