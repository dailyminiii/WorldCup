import numpy as np

from worldcup_strategy.actions.progression import compute_progression
from worldcup_strategy.actions.spadl import build_spadl_actions
from worldcup_strategy.actions.xg import build_shot_xg, team_match_xg
from worldcup_strategy.actions.xt import apply_xt
from worldcup_strategy.data.statsbomb import canonical_events, canonical_matches
from worldcup_strategy.reporting.attacking_tables import team_match_attacking


def test_synthetic_match_action_pipeline() -> None:
    base = {
        "period": 1,
        "minute": 1,
        "second": 0,
        "timestamp": "00:01:00",
        "team": {"id": 1, "name": "A"},
        "player": {"id": 10, "name": "P"},
        "possession": 1,
        "possession_team": {"id": 1},
        "play_pattern": {"name": "Regular Play"},
    }
    events = canonical_events(
        1,
        [
            {
                **base,
                "id": "p",
                "index": 1,
                "type": {"name": "Pass"},
                "location": [20, 40],
                "pass": {"end_location": [80, 40]},
            },
            {
                **base,
                "id": "c",
                "index": 2,
                "type": {"name": "Carry"},
                "location": [80, 40],
                "carry": {"end_location": [100, 40]},
            },
            {
                **base,
                "id": "s",
                "index": 3,
                "type": {"name": "Shot"},
                "location": [100, 40],
                "shot": {
                    "end_location": [120, 40],
                    "statsbomb_xg": 0.5,
                    "outcome": {"name": "Goal"},
                    "type": {"name": "Open Play"},
                },
            },
        ],
    )
    matches = canonical_matches(
        [
            {
                "match_id": 1,
                "match_date": "2022-01-01",
                "kick_off": "00:00:00",
                "competition": {"competition_id": 43},
                "season": {"season_id": 106},
                "competition_stage": {"name": "Group Stage"},
                "match_week": 1,
                "home_team": {"home_team_id": 1, "home_team_name": "A", "home_team_group": "A"},
                "away_team": {"away_team_id": 2, "away_team_name": "B"},
                "home_score": 1,
                "away_score": 0,
            }
        ]
    )
    actions = build_spadl_actions(events, matches)
    shots = build_shot_xg(events)
    match_xg = team_match_xg(shots, matches)
    xt = apply_xt(actions, np.tile(np.linspace(0, 0.2, 16), (12, 1)), "reference")
    progression = compute_progression(actions)
    summary = team_match_attacking(actions, match_xg, xt, progression)
    assert len(actions) == 3
    assert summary.iloc[0].goals == 1
    assert summary.iloc[0].progressive_passes == 1
