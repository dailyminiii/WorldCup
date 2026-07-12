"""Synthetic end-to-end Milestone 4 feature integration without network data."""

from pathlib import Path

import pandas as pd

from worldcup_strategy.state.features import integrate_features


def _write(frame: pd.DataFrame, root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def test_synthetic_interval_feature_integration(tmp_path: Path) -> None:
    intervals = pd.DataFrame(
        {
            "match_id": [1, 1],
            "team_id": [10, 20],
            "opponent_id": [20, 10],
            "period": [1, 1],
            "interval_start": [0.0, 0.0],
            "interval_end": [300.0, 300.0],
            "effective_play_seconds": [120.0, 120.0],
        }
    )
    events = pd.DataFrame(
        {
            "match_id": [1, 1, 1, 1, 1],
            "event_id": ["def", "pass-boundary", "pass", "carry", "pressure"],
            "event_index": range(5),
            "team_id": [10, 20, 10, 10, 10],
            "possession_team_id": [20, 20, 10, 10, 20],
            "period": [1] * 5,
            "elapsed_seconds": [100.0, 300.0, 120.0, 130.0, 200.0],
            "event_type": ["Interception", "Pass", "Pass", "Carry", "Pressure"],
            "outcome": [None] * 5,
            "is_goal": [False] * 5,
            "statsbomb_xg": [None] * 5,
            "is_penalty": [False] * 5,
            "is_set_piece": [False] * 5,
            "possession_id": [1, 1, 2, 2, 3],
            "play_pattern": ["Regular Play"] * 5,
            "start_x_normalized": [95.0, 10.0, 20.0, 25.0, 80.0],
            "start_y_normalized": [34.0] * 5,
            "end_x_normalized": [None, 20.0, 60.0, 45.0, None],
            "end_y_normalized": [None, 34.0, 34.0, 34.0, None],
            "raw_event_json": ["{}"] * 5,
        }
    )
    _write(events, tmp_path, "events_2022.parquet")
    _write(
        pd.DataFrame(
            {
                "match_id": [1],
                "team_id": [10],
                "period": [1],
                "elapsed_seconds": [200.0],
                "counterpress": [False],
                "is_high_pressure": [True],
            }
        ),
        tmp_path,
        "pressure/pressure_events_2022.parquet",
    )
    _write(
        pd.DataFrame(
            {
                "match_id": [1],
                "team_id": [10],
                "period": [1],
                "pressure_seconds": [200.0],
                "regain_3s": [True],
                "regain_5s": [True],
                "regain_8s": [True],
            }
        ),
        tmp_path,
        "pressure/pressure_regains_2022.parquet",
    )
    _write(
        pd.DataFrame(
            {
                "match_id": [1],
                "pressing_team_id": [10],
                "period": [1],
                "sequence_start_seconds": [200.0],
                "regain_3s": [True],
                "regain_5s": [True],
                "regain_8s": [True],
            }
        ),
        tmp_path,
        "pressure/pressure_sequences_2022.parquet",
    )
    _write(
        pd.DataFrame(
            {
                "match_id": [1],
                "team_id": [10],
                "period": [1],
                "elapsed_seconds": [250.0],
                "substitution_classification": ["unknown"],
            }
        ),
        tmp_path,
        "state/substitutions_2022.parquet",
    )
    _write(
        pd.DataFrame({"match_id": [1], "team_id": [10], "period": [1], "elapsed_seconds": [260.0]}),
        tmp_path,
        "state/tactical_shifts_2022.parquet",
    )
    spadl = pd.DataFrame(
        {
            "match_id": [1, 1],
            "team_id": [10, 10],
            "action_id": [1, 2],
            "period_id": [1, 1],
            "time_seconds": [120.0, 130.0],
        }
    )
    _write(spadl, tmp_path, "actions/spadl_actions_2022.parquet")
    _write(
        pd.DataFrame(
            {
                "match_id": [1, 1],
                "team_id": [10, 10],
                "action_id": [1, 2],
                "eligible_for_xt": [True, True],
                "xt_added": [0.2, -0.1],
                "xt_missing_reason": [None, None],
                "xt_model_version": ["test", "test"],
                "xt_training_mode": ["reference", "reference"],
            }
        ),
        tmp_path,
        "actions/action_xt_2022.parquet",
    )
    _write(
        pd.DataFrame(
            {
                "match_id": [1, 1],
                "team_id": [10, 10],
                "action_id": [1, 2],
                "action_type": ["pass", "carry"],
                "is_progressive": [True, True],
                "progression_definition": ["progressive_goal_distance_v1"] * 2,
            }
        ),
        tmp_path,
        "actions/progression_actions_2022.parquet",
    )
    features = integrate_features(intervals, tmp_path)
    team = features[features.team_id == 10].iloc[0]
    assert team.ppda_opponent_passes == 1
    assert team.ppda_defensive_actions == 1
    assert team.pressure_events == 1
    assert team.xt_eligible_actions == 2
    assert team.xt_added == 0.1
    assert team.positive_xt == 0.2 and team.negative_xt == -0.1
    assert team.progressive_passes == 1 and team.progressive_carries == 1
    assert team.substitutions == 1 and team.tactical_shifts == 1
