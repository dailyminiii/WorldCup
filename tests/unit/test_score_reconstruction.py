import pandas as pd

from worldcup_strategy.state.score import reconstruct_score


def test_goal_uses_pre_event_drawing_and_shootout_is_excluded() -> None:
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "g",
                "event_index": 1,
                "period": 1,
                "elapsed_seconds": 1.0,
                "team_id": 1,
                "is_goal": True,
                "is_own_goal": False,
                "is_penalty": False,
                "is_penalty_shootout": False,
            },
            {
                "match_id": 1,
                "event_id": "s",
                "event_index": 2,
                "period": 5,
                "elapsed_seconds": 6000.0,
                "team_id": 2,
                "is_goal": True,
                "is_own_goal": False,
                "is_penalty": False,
                "is_penalty_shootout": True,
            },
        ]
    )
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    states = reconstruct_score(events, matches)
    home = states[states.team_id == 1]
    assert (
        home.iloc[0].score_state_before == "drawing" and home.iloc[0].score_state_after == "leading"
    )
    assert home.iloc[-1].goals_for_after == 1 and home.iloc[-1].goals_against_after == 0


def test_own_goal_companion_changes_score_once() -> None:
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "for",
                "event_index": 1,
                "period": 1,
                "elapsed_seconds": 1.0,
                "team_id": 1,
                "is_goal": True,
                "is_own_goal": True,
                "is_penalty": False,
                "is_penalty_shootout": False,
            },
            {
                "match_id": 1,
                "event_id": "against",
                "event_index": 2,
                "period": 1,
                "elapsed_seconds": 1.0,
                "team_id": 2,
                "is_goal": False,
                "is_own_goal": True,
                "is_penalty": False,
                "is_penalty_shootout": False,
            },
        ]
    )
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    states = reconstruct_score(events, matches)
    assert states.scoring_event.sum() == 2
