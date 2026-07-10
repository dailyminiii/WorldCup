# mypy: ignore-errors
"""Classic and provider-specific augmented PPDA."""

from typing import Any

import pandas as pd

from worldcup_strategy.pressure.frames import FRAME_VERSION, possession_frame

EXCLUDED_PATTERNS = {
    "From Corner",
    "From Free Kick",
    "From Throw In",
    "From Goal Kick",
    "From Kick Off",
}
CLASSIC_EVENTS = {"Interception", "Foul Committed"}


def _opponent(match: pd.Series, team_id: int) -> int:
    return int(match.away_team_id if int(match.home_team_id) == team_id else match.home_team_id)


def compute_ppda(
    events: pd.DataFrame, matches: pd.DataFrame, build_up_x: float = 63.0
) -> pd.DataFrame:
    """Compute both PPDA variants in a common possession-team physical frame."""
    rows: list[dict[str, Any]] = []
    for match in matches.itertuples(index=False):
        match_events = events[(events.match_id == match.match_id) & ~events.is_penalty_shootout]
        for team_id in (int(match.home_team_id), int(match.away_team_id)):
            opponent_id = int(
                match.away_team_id if team_id == int(match.home_team_id) else match.home_team_id
            )
            passes = match_events[
                (match_events.team_id == opponent_id)
                & (match_events.event_type == "Pass")
                & ~match_events.play_pattern.isin(EXCLUDED_PATTERNS)
            ].copy()
            passes["zone_x"] = [
                possession_frame(x, y, acting_team_id=opponent_id, possession_team_id=opponent_id)[
                    0
                ]
                for x, y in zip(passes.start_x_normalized, passes.start_y_normalized, strict=True)
            ]
            numerator = int(passes.zone_x.between(0, build_up_x).sum())
            defending = match_events[match_events.team_id == team_id].copy()
            defending["zone_x"] = [
                possession_frame(x, y, acting_team_id=team_id, possession_team_id=opponent_id)[0]
                for x, y in zip(
                    defending.start_x_normalized, defending.start_y_normalized, strict=True
                )
            ]
            duel_tackle = (defending.event_type == "Duel") & defending.raw_event_json.str.contains(
                '"type":{"id":11,"name":"Tackle"}', regex=False
            )
            classic_mask = (
                defending.event_type.isin(CLASSIC_EVENTS) | duel_tackle
            ) & defending.zone_x.between(0, build_up_x)
            pressure_mask = (defending.event_type == "Pressure") & defending.zone_x.between(
                0, build_up_x
            )
            classic = int(classic_mask.sum())
            pressure = int(pressure_mask.sum())
            augmented = classic + pressure
            rows.append(
                {
                    "match_id": int(match.match_id),
                    "team_id": team_id,
                    "opponent_id": opponent_id,
                    "classic_opponent_passes": numerator,
                    "classic_defensive_actions": classic,
                    "ppda_classic": numerator / classic if classic else None,
                    "pressure_events_added": pressure,
                    "augmented_defensive_actions": augmented,
                    "ppda_pressure_augmented": numerator / augmented if augmented else None,
                    "classic_missing_reason": None if classic else "no_eligible_defensive_actions",
                    "augmented_missing_reason": None
                    if augmented
                    else "no_eligible_defensive_actions",
                    "spatial_frame_version": FRAME_VERSION,
                    "ppda_definition_version": (
                        "ppda_classic_statsbomb_v1|ppda_pressure_augmented_statsbomb_v1"
                    ),
                }
            )
    return pd.DataFrame(rows)
