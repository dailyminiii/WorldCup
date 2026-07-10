import pandas as pd

from worldcup_strategy.actions.xg import build_shot_xg


def test_xg_excludes_shootouts_and_keeps_one_own_goal() -> None:
    frame = pd.DataFrame(
        [
            {
                "event_type": "Shot",
                "is_own_goal": False,
                "is_goal": True,
                "is_penalty_shootout": False,
                "event_subtype": "Penalty",
                "play_pattern": "From Free Kick",
                "statsbomb_xg": 0.76,
                "is_penalty": True,
                "is_set_piece": True,
            },
            {
                "event_type": "Shot",
                "is_own_goal": False,
                "is_goal": True,
                "is_penalty_shootout": True,
                "event_subtype": "Penalty",
                "play_pattern": "Other",
                "statsbomb_xg": 0.76,
                "is_penalty": False,
                "is_set_piece": False,
            },
            {
                "event_type": "Own Goal For",
                "is_own_goal": True,
                "is_goal": True,
                "is_penalty_shootout": False,
                "event_subtype": None,
                "play_pattern": "Regular Play",
                "statsbomb_xg": None,
                "is_penalty": False,
                "is_set_piece": False,
            },
            {
                "event_type": "Own Goal Against",
                "is_own_goal": True,
                "is_goal": False,
                "is_penalty_shootout": False,
                "event_subtype": None,
                "play_pattern": "Regular Play",
                "statsbomb_xg": None,
                "is_penalty": False,
                "is_set_piece": False,
            },
        ]
    ).assign(
        match_id=1,
        event_id=["a", "b", "c", "d"],
        team_id=1,
        player_id=None,
        period=[1, 5, 1, 1],
        elapsed_seconds=1,
        body_part=None,
        technique=None,
    )
    shots = build_shot_xg(frame)
    assert shots.event_id.tolist() == ["a", "c"]
    assert shots.statsbomb_xg.notna().sum() == 1
