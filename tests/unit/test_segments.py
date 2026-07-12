"""Tests for homogeneous state segments."""

import pandas as pd

from worldcup_strategy.state.segments import build_segments


def test_goal_splits_inverse_team_segments() -> None:
    rows = []
    for team, opponent, sign, before_state, after_state in (
        (10, 20, 1, "drawing", "leading"),
        (20, 10, -1, "drawing", "trailing"),
    ):
        for index, seconds in enumerate((0.0, 120.0, 300.0)):
            changed = seconds == 120
            rows.append(
                {
                    "match_id": 1,
                    "team_id": team,
                    "opponent_id": opponent,
                    "period": 1,
                    "event_index": index,
                    "elapsed_seconds": seconds,
                    "goal_difference_before": 0 if seconds <= 120 else sign,
                    "goal_difference_after": sign if changed or seconds > 120 else 0,
                    "score_state_before": before_state if seconds <= 120 else after_state,
                    "score_state_after": after_state if changed or seconds > 120 else before_state,
                    "red_card_difference_before": 0,
                    "red_card_difference_after": 0,
                    "numerical_state_before": "even_11v11",
                    "numerical_state_after": "even_11v11",
                }
            )
    segments = build_segments(pd.DataFrame(rows))
    assert len(segments) == 4
    paired = segments.pivot(index="segment_id", columns="team_id", values="goal_difference")
    assert (paired[10] == -paired[20]).all()
    assert (segments.segment_duration_seconds > 0).all()
