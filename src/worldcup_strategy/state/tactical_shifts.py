# mypy: ignore-errors
"""Provider Tactical Shift extraction."""

import json

import pandas as pd


def extract_tactical_shifts(
    events: pd.DataFrame, score: pd.DataFrame, discipline: pd.DataFrame
) -> pd.DataFrame:
    s = score.set_index(["match_id", "event_id", "team_id"])
    d = discipline.set_index(["match_id", "event_id", "team_id"])
    rows = []
    for event in events[events.event_type == "Tactical Shift"].itertuples(index=False):
        raw = json.loads(event.raw_event_json)
        key = (event.match_id, event.event_id, event.team_id)
        rows.append(
            {
                "match_id": event.match_id,
                "event_id": event.event_id,
                "team_id": event.team_id,
                "period": event.period,
                "elapsed_seconds": event.elapsed_seconds,
                "formation_before": None,
                "formation_after": (raw.get("tactics") or {}).get("formation"),
                "score_state_before": s.loc[key].score_state_before,
                "goal_difference_before": s.loc[key].goal_difference_before,
                "red_card_difference_before": d.loc[key].red_card_difference_before,
            }
        )
    return pd.DataFrame(rows)
