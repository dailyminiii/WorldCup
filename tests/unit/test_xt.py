import numpy as np
import pandas as pd

from worldcup_strategy.actions.xt import XTConfig, apply_xt, fit_xt_grid


def sample_actions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 1,
                "action_id": 0,
                "original_event_id": "a",
                "team_id": 1,
                "player_id": 1,
                "type_name": "pass",
                "result_name": "success",
                "is_penalty_shootout": False,
                "start_x": 10.0,
                "start_y": 34.0,
                "end_x": 90.0,
                "end_y": 34.0,
            },
            {
                "match_id": 1,
                "action_id": 1,
                "original_event_id": "b",
                "team_id": 1,
                "player_id": 1,
                "type_name": "shot",
                "result_name": "success",
                "is_penalty_shootout": False,
                "start_x": 90.0,
                "start_y": 34.0,
                "end_x": 105.0,
                "end_y": 34.0,
            },
        ]
    )


def test_xt_grid_is_deterministic() -> None:
    first = fit_xt_grid(sample_actions(), XTConfig(4, 3))
    second = fit_xt_grid(sample_actions(), XTConfig(4, 3))
    np.testing.assert_array_equal(first, second)


def test_xt_missing_coordinates_are_null_with_reason() -> None:
    actions = sample_actions().iloc[:1].copy()
    actions.loc[0, "end_x"] = np.nan
    valued = apply_xt(actions, np.arange(12).reshape(3, 4) / 12, "reference")
    assert not bool(valued.iloc[0].eligible_for_xt)
    assert valued.iloc[0].xt_missing_reason == "missing_end_location"
    assert pd.isna(valued.iloc[0].xt_added)
