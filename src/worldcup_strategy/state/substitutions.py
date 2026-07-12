# mypy: ignore-errors
"""Provider substitution extraction with conservative classification."""

import json

import pandas as pd


def extract_substitutions(
    events: pd.DataFrame, score: pd.DataFrame, discipline: pd.DataFrame
) -> pd.DataFrame:
    score_lookup = score.set_index(["match_id", "event_id", "team_id"])
    disc_lookup = discipline.set_index(["match_id", "event_id", "team_id"])
    rows = []
    for event in (
        events[events.event_type == "Substitution"]
        .sort_values(["match_id", "team_id", "event_index"])
        .itertuples(index=False)
    ):
        raw = json.loads(event.raw_event_json)
        detail = raw.get("substitution") or {}
        replacement = detail.get("replacement") or {}
        position = (raw.get("position") or {}).get("name")
        key = (event.match_id, event.event_id, event.team_id)
        state = score_lookup.loc[key]
        disc = disc_lookup.loc[key]
        classification = "goalkeeper" if position == "Goalkeeper" else "unknown"
        number = (
            len(
                [
                    r
                    for r in rows
                    if r["match_id"] == event.match_id and r["team_id"] == event.team_id
                ]
            )
            + 1
        )
        rows.append(
            {
                "match_id": event.match_id,
                "event_id": event.event_id,
                "period": event.period,
                "elapsed_seconds": event.elapsed_seconds,
                "team_id": event.team_id,
                "player_out_id": event.player_id,
                "player_in_id": replacement.get("id"),
                "player_out_position": position,
                "player_in_position": None,
                "score_state_before": state.score_state_before,
                "goal_difference_before": state.goal_difference_before,
                "red_card_difference_before": disc.red_card_difference_before,
                "substitution_number": number,
                "substitution_window_id": (
                    f"{event.match_id}-{event.team_id}-{event.period}-"
                    f"{int(event.elapsed_seconds // 180)}"
                ),
                "substitution_classification": classification,
                "substitution_classification_version": "substitution_position_balance_v1",
                "classification_uncertainty_reason": None
                if classification == "goalkeeper"
                else "missing_player_in_position",
            }
        )
    return pd.DataFrame(rows)
