import pandas as pd

from worldcup_strategy.actions.spadl import build_spadl_actions, orientation_diagnostics


def test_spadl_preserves_order_and_orientation() -> None:
    events = pd.DataFrame(
        [
            {
                "provider": "statsbomb",
                "match_id": 1,
                "event_id": "b",
                "event_index": 2,
                "period": 1,
                "elapsed_seconds": 2.0,
                "team_id": 1,
                "player_id": 1,
                "event_type": "Shot",
                "outcome": "Goal",
                "is_goal": True,
                "body_part": "Right Foot",
                "start_x_normalized": 90.0,
                "start_y_normalized": 34.0,
                "end_x_normalized": 105.0,
                "end_y_normalized": 34.0,
                "start_x_raw": 103.0,
                "start_y_raw": 40.0,
                "end_x_raw": 120.0,
                "end_y_raw": 40.0,
                "possession_id": 1,
                "play_pattern": "Regular Play",
                "is_penalty_shootout": False,
            }
        ]
    )
    matches = pd.DataFrame(
        [
            {
                "match_id": 1,
                "competition_id": 43,
                "season_id": 106,
                "group_name": "Group A",
                "competition_stage": "Group Stage",
                "match_week": 1,
            }
        ]
    )
    actions = build_spadl_actions(events, matches)
    assert actions.original_event_id.tolist() == ["b"]
    assert orientation_diagnostics(actions)["valid"] is True
