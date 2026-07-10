import pandas as pd

from worldcup_strategy.pressure.regains import compute_pressure_regains


def test_regain_within_three_seconds_and_same_period() -> None:
    pressures = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "p",
                "event_index": 1,
                "team_id": 1,
                "opponent_id": 2,
                "period": 1,
                "elapsed_seconds": 10.0,
            }
        ]
    )
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "p",
                "event_index": 1,
                "team_id": 1,
                "possession_team_id": 2,
                "possession_id": 1,
                "period": 1,
                "elapsed_seconds": 10.0,
                "event_type": "Pressure",
                "outcome": None,
                "start_x_normalized": 60.0,
                "start_y_normalized": 30.0,
                "statsbomb_xg": None,
            },
            {
                "match_id": 1,
                "event_id": "r",
                "event_index": 2,
                "team_id": 1,
                "possession_team_id": 1,
                "possession_id": 2,
                "period": 1,
                "elapsed_seconds": 12.0,
                "event_type": "Pass",
                "outcome": None,
                "start_x_normalized": 70.0,
                "start_y_normalized": 30.0,
                "statsbomb_xg": None,
            },
        ]
    )
    sequences = pd.DataFrame(columns=["match_id", "pressing_team_id", "sequence_end_seconds"])
    regains, high = compute_pressure_regains(pressures, sequences, events)
    assert bool(regains.iloc[0].regain_3s)
    assert regains.iloc[0].regain_reason == "successful_regain"
    assert bool(high.iloc[0].is_high_regain)
