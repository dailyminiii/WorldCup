import pandas as pd

from worldcup_strategy.data.statsbomb import canonical_events, canonical_three_sixty


def shot(period: int = 2) -> dict[str, object]:
    return {
        "id": "event-1",
        "index": 7,
        "period": period,
        "minute": 48,
        "second": 2,
        "timestamp": "00:03:02.000",
        "type": {"name": "Shot"},
        "team": {"id": 1, "name": "A"},
        "player": {"id": 10, "name": "Player"},
        "possession": 3,
        "possession_team": {"id": 1},
        "location": [100, 40],
        "play_pattern": {"name": "Regular Play"},
        "shot": {
            "end_location": [120, 40],
            "statsbomb_xg": 0.3,
            "outcome": {"name": "Goal"},
            "type": {"name": "Penalty"},
        },
    }


def test_event_conversion_preserves_nulls_and_shot_flags() -> None:
    frame = canonical_events(99, [shot()])
    assert frame.loc[0, "statsbomb_xg"] == 0.3
    assert bool(frame.loc[0, "is_goal"])
    assert bool(frame.loc[0, "is_penalty"])
    assert not bool(frame.loc[0, "is_penalty_shootout"])
    assert pd.isna(frame.loc[0, "under_pressure"])


def test_shootout_is_separate_from_regular_penalty() -> None:
    frame = canonical_events(99, [shot(period=5)])
    assert bool(frame.loc[0, "is_penalty_shootout"])
    assert not bool(frame.loc[0, "is_penalty"])


def test_own_goal_is_recognized_without_shot_payload() -> None:
    event = shot()
    event["type"] = {"name": "Own Goal Against"}
    event.pop("shot")
    frame = canonical_events(99, [event])
    assert bool(frame.loc[0, "is_goal"])
    assert bool(frame.loc[0, "is_own_goal"])
    assert pd.isna(frame.loc[0, "statsbomb_xg"])


def test_three_sixty_separates_frames_and_polygon() -> None:
    rows = [
        {
            "event_uuid": "e",
            "freeze_frame": [
                {"location": [60, 40], "teammate": True, "actor": True, "keeper": False}
            ],
            "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
        }
    ]
    frames, areas = canonical_three_sixty(1, rows)
    assert len(frames) == 1
    assert areas.loc[0, "polygon_area"] == 105 * 68
