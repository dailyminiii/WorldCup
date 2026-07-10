import pandas as pd

from worldcup_strategy.actions.progression import ProgressionConfig, compute_progression


def action(
    start: float, end: float, kind: str = "pass", pattern: str = "Regular Play"
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 1,
                "action_id": 0,
                "original_event_id": "e",
                "team_id": 1,
                "player_id": 1,
                "type_name": kind,
                "result_name": "success",
                "is_penalty_shootout": False,
                "play_pattern": pattern,
                "start_x": start,
                "start_y": 34.0,
                "end_x": end,
                "end_y": 34.0,
            }
        ]
    )


def test_threshold_equality_is_progressive() -> None:
    assert bool(compute_progression(action(10, 40)).iloc[0].is_progressive)


def test_below_threshold_is_not_progressive() -> None:
    assert not bool(compute_progression(action(10, 39.999)).iloc[0].is_progressive)


def test_crossing_and_opponent_thresholds() -> None:
    assert bool(compute_progression(action(40, 55)).iloc[0].is_progressive)
    assert bool(compute_progression(action(70, 80)).iloc[0].is_progressive)


def test_set_piece_and_short_carry_exclusions() -> None:
    assert (
        compute_progression(action(10, 50, pattern="From Corner"))
        .iloc[0]
        .progression_exclusion_reason
        == "excluded_set_piece"
    )
    short = compute_progression(action(10, 10.5, kind="carry"), ProgressionConfig(minimum_carry=1))
    assert short.iloc[0].progression_exclusion_reason == "carry_below_minimum_length"
