"""Definition-boundary tests for passing style."""

import numpy as np
import pandas as pd

from worldcup_strategy.state.feature_contract import _passing


def test_direction_long_pass_missing_and_directness() -> None:
    result = pd.DataFrame(
        {
            "match_id": [1],
            "team_id": [10],
            "period": [1],
            "interval_start": [0.0],
            "interval_end": [300.0],
            "interval_key": [0],
            "passes": [5],
            "completed_passes": [5],
        }
    )
    events = pd.DataFrame(
        {
            "match_id": [1] * 5,
            "team_id": [10] * 5,
            "period": [1] * 5,
            "elapsed_seconds": [1, 2, 3, 4, 5],
            "event_type": ["Pass"] * 5,
            "start_x_normalized": [0, 5, 5, 0, 0],
            "start_y_normalized": [0] * 5,
            "end_x_normalized": [2, 3, 6, 30, np.nan],
            "end_y_normalized": [0] * 5,
        }
    )
    _passing(result, events)
    row = result.iloc[0]
    assert (row.forward_passes, row.backward_passes, row.lateral_passes) == (2, 1, 1)
    assert row.long_passes == 1
    assert row.pass_length_valid_count == 4
    assert row.pass_directness == 33 / 35
