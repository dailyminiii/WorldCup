"""Regression tests for interval assignment and rate reliability."""

import numpy as np
import pandas as pd

from worldcup_strategy.state.feature_contract import _rate, assign_right_closed


def test_right_closed_assignment_and_period_start() -> None:
    intervals = pd.DataFrame(
        {
            "match_id": [1, 1],
            "team_id": [10, 10],
            "period": [1, 1],
            "interval_start": [0.0, 300.0],
            "interval_end": [300.0, 600.0],
            "interval_key": [0, 1],
        }
    )
    records = pd.DataFrame(
        {
            "match_id": [1, 1, 1],
            "team_id": [10, 10, 10],
            "period": [1, 1, 1],
            "elapsed_seconds": [0.0, 300.0, 301.0],
        }
    )
    assigned = assign_right_closed(records, intervals)
    assert assigned.interval_key.tolist() == [0, 0, 1]
    assert len(assigned) == len(records)


def test_rate_contract_distinguishes_missing_zero_and_low() -> None:
    frame = pd.DataFrame(index=range(4))
    _rate(
        frame,
        "metric",
        pd.Series([1, 1, 1, 5]),
        pd.Series([np.nan, 0, 2, 5]),
        5,
        "below_minimum_passes",
    )
    assert frame.metric.isna().tolist() == [True, True, False, False]
    assert frame.metric_reliable.tolist() == [False, False, False, True]
    assert frame.metric_unreliable_reason.tolist() == [
        "missing_denominator",
        "zero_denominator",
        "below_minimum_passes",
        None,
    ]


def test_pressure_is_not_a_classic_ppda_action() -> None:
    from worldcup_strategy.pressure.ppda import CLASSIC_EVENTS

    assert "Pressure" not in CLASSIC_EVENTS
