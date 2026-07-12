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
            "shots": [1, 2],
            "statsbomb_xg": [0.1, 0.2],
            "passes": [1, 9],
            "completed_passes": [1, 0],
            "pressure_events": [1, 9],
            "pressure_regains_5s": [1, 0],
            "pressure_regain_5s_rate": [1.0, 0.0],
            "substitutions": [0, 0],
            "goalkeeper_substitutions": [0, 0],
            "unknown_substitutions": [0, 0],
            "tactical_shifts": [0, 0],
        }
    )
    summary = summarize_score_state(frame)
    pressure = summary[summary.outcome == "pressure_regain_5s_rate"].iloc[0]
    assert pressure.raw_denominator == 10
    assert pressure.pooled_rate == 0.1
    assert pressure["mean"] == 0.5
