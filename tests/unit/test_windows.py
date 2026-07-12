"""Regression tests for fixed state windows."""

import pandas as pd

from worldcup_strategy.state.windows import build_windows


def _row(index: int, seconds: float, before: int, after: int) -> dict[str, object]:
    state_before = "drawing" if before == 0 else "leading"
    state_after = "drawing" if after == 0 else "leading"
    return {
        "match_id": 1,
        "team_id": 10,
        "opponent_id": 20,
        "period": 1,
        "event_index": index,
        "event_id": str(index),
        "elapsed_seconds": seconds,
        "event_team_id": 10,
        "goal_difference_before": before,
        "goal_difference_after": after,
        "score_state_before": state_before,
        "score_state_after": state_after,
        "red_card_difference_before": 0,
        "red_card_difference_after": 0,
        "numerical_state_before": "even_11v11",
        "numerical_state_after": "even_11v11",
    }


def test_right_closed_boundary_event_is_counted_once() -> None:
    states = pd.DataFrame([_row(1, 0, 0, 0), _row(2, 300, 0, 1), _row(3, 600, 1, 1)])
    windows = build_windows(states)
    assert windows.event_count.tolist() == [1, 1]
    assert windows.event_count.sum() == 2
    assert windows.iloc[0].score_state_end == "leading"
    assert windows.iloc[1].score_state_start == "leading"


def test_transition_overlap_durations_reconcile() -> None:
    states = pd.DataFrame([_row(1, 0, 0, 0), _row(2, 120, 0, 1), _row(3, 300, 1, 1)])
    window = build_windows(states).iloc[0]
    assert window.time_drawing_seconds == 120
    assert window.time_leading_seconds == 180
    assert window.time_drawing_seconds + window.time_leading_seconds == window.wall_clock_seconds
