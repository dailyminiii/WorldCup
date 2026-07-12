# mypy: ignore-errors
"""Integrated symmetric team-event state table."""

import pandas as pd


def build_team_event_states(
    events: pd.DataFrame, matches: pd.DataFrame, score: pd.DataFrame, discipline: pd.DataFrame
) -> pd.DataFrame:
    event_fields = events[["match_id", "event_id", "team_id", "possession_team_id"]].rename(
        columns={"team_id": "event_team_id"}
    )
    meta = matches[["match_id", "competition_stage", "group_name", "match_week"]]
    disc_cols = [
        "match_id",
        "event_id",
        "team_id",
        "red_cards_for_before",
        "red_cards_against_before",
        "red_card_difference_before",
        "numerical_state_before",
        "red_cards_for_after",
        "red_cards_against_after",
        "red_card_difference_after",
        "numerical_state_after",
    ]
    out = (
        score.merge(
            discipline[disc_cols], on=["match_id", "event_id", "team_id"], validate="one_to_one"
        )
        .merge(event_fields, on=["match_id", "event_id"], validate="many_to_one")
        .merge(meta, on="match_id", validate="many_to_one")
    )
    out["team_is_event_actor"] = out.team_id == out.event_team_id
    out["team_in_possession"] = out.team_id == out.possession_team_id
    return out


def validate_event_states(states: pd.DataFrame, event_count: int) -> dict[str, int | bool]:
    duplicate = int(states.duplicated(["match_id", "event_id", "team_id"]).sum())
    groups = states.groupby(["match_id", "event_id"])
    symmetry = 0
    for _, g in groups:
        if (
            len(g) != 2
            or g.iloc[0].goals_for_before != g.iloc[1].goals_against_before
            or g.iloc[0].goal_difference_before != -g.iloc[1].goal_difference_before
            or g.iloc[0].red_card_difference_before != -g.iloc[1].red_card_difference_before
        ):
            symmetry += 1
    return {
        "team_event_rows": len(states),
        "expected_rows": event_count * 2,
        "duplicate_rows": duplicate,
        "events_without_two_perspectives": int((groups.size() != 2).sum()),
        "symmetry_failures": symmetry,
        "valid": len(states) == event_count * 2 and duplicate == 0 and symmetry == 0,
    }
