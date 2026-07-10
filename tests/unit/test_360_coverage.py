import pandas as pd

from worldcup_strategy.pressure.coverage import coverage_tables


def test_incomplete_coverage_is_preserved() -> None:
    events = pd.DataFrame(
        [
            {"match_id": 1, "event_id": "a", "team_id": 1, "event_type": "Pass"},
            {"match_id": 1, "event_id": "b", "team_id": 1, "event_type": "Pass"},
        ]
    )
    context = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "a",
                "has_freeze_frame": True,
                "has_visible_area": True,
                "actor_visible": True,
                "context_valid": True,
            }
        ]
    )
    matches = pd.DataFrame()
    match, _, _ = coverage_tables(events, context, matches)
    assert match.iloc[0].eligible_events == 2 and match.iloc[0].valid_context_rate == 0.5
