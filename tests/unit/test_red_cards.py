import json

import pandas as pd

from worldcup_strategy.state.discipline import reconstruct_discipline


def event(i: int, card: str, position: str = "Center Back", period: int = 1) -> dict[str, object]:
    raw = {"foul_committed": {"card": {"name": card}}, "position": {"name": position}}
    return {
        "match_id": 1,
        "event_id": str(i),
        "event_index": i,
        "period": period,
        "elapsed_seconds": float(i),
        "team_id": 1,
        "player_id": 10,
        "is_penalty_shootout": period == 5,
        "raw_event_json": json.dumps(raw),
    }


def test_yellow_does_not_reduce_and_second_yellow_does_once() -> None:
    events = pd.DataFrame([event(1, "Yellow Card"), event(2, "Second Yellow")])
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    states = reconstruct_discipline(events, matches)
    home = states[states.team_id == 1]
    assert home.iloc[0].red_cards_for_after == 0 and home.iloc[-1].red_cards_for_after == 1


def test_substitute_and_shootout_red_do_not_reduce() -> None:
    events = pd.DataFrame([event(1, "Red Card", "Substitute"), event(2, "Red Card", period=5)])
    matches = pd.DataFrame([{"match_id": 1, "home_team_id": 1, "away_team_id": 2}])
    states = reconstruct_discipline(events, matches)
    assert states.red_cards_for_after.max() == 0
