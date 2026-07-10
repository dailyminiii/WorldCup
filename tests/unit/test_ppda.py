import pandas as pd

from worldcup_strategy.pressure.ppda import compute_ppda


def test_classic_excludes_pressure_and_augmented_adds_it() -> None:
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team_id": 2,
                "event_type": "Pass",
                "play_pattern": "Regular Play",
                "start_x_normalized": 20.0,
                "start_y_normalized": 30.0,
                "raw_event_json": "{}",
                "is_penalty_shootout": False,
            },
            {
                "match_id": 1,
                "team_id": 1,
                "event_type": "Interception",
                "play_pattern": "Regular Play",
                "start_x_normalized": 85.0,
                "start_y_normalized": 38.0,
                "raw_event_json": "{}",
                "is_penalty_shootout": False,
            },
            {
                "match_id": 1,
                "team_id": 1,
                "event_type": "Pressure",
                "play_pattern": "Regular Play",
                "start_x_normalized": 85.0,
                "start_y_normalized": 38.0,
                "raw_event_json": "{}",
                "is_penalty_shootout": False,
            },
        ]
    )
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    row = compute_ppda(events, matches).query("team_id==1").iloc[0]
    assert row.classic_opponent_passes == 1 and row.classic_defensive_actions == 1
    assert row.pressure_events_added == 1 and row.ppda_pressure_augmented == 0.5


def test_zero_denominator_is_null_with_reason() -> None:
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team_id": 2,
                "event_type": "Pass",
                "play_pattern": "Regular Play",
                "start_x_normalized": 20.0,
                "start_y_normalized": 30.0,
                "raw_event_json": "{}",
                "is_penalty_shootout": False,
            }
        ]
    )
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    row = compute_ppda(events, matches).query("team_id==1").iloc[0]
    assert pd.isna(row.ppda_classic)
    assert row.classic_missing_reason == "no_eligible_defensive_actions"
