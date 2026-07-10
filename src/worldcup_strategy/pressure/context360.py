# mypy: ignore-errors
# ruff: noqa: B023
"""Coverage-aware event-linked StatsBomb 360 geometry."""

import math

import pandas as pd


def build_context360(
    events: pd.DataFrame, frames: pd.DataFrame, areas: pd.DataFrame, actor_fallback: bool = False
) -> pd.DataFrame:
    event_lookup = events.set_index(["match_id", "event_id"])
    area_lookup = areas.drop_duplicates(["match_id", "event_id"]).set_index(
        ["match_id", "event_id"]
    )
    frame_groups = {
        key: group for key, group in frames.groupby(["match_id", "event_id"], sort=False)
    }
    keys = set(frame_groups) | set(zip(areas.match_id, areas.event_id, strict=True))
    rows = []
    for key in sorted(keys):
        if key not in event_lookup.index:
            continue
        event = event_lookup.loc[key]
        group = frame_groups.get(key, frames.iloc[0:0])
        actors = group[group.actor]
        source = (
            "freeze_frame_actor"
            if len(actors)
            else "event_location_fallback"
            if actor_fallback and pd.notna(event.start_x_normalized)
            else None
        )
        ax = (
            float(actors.iloc[0].x_normalized)
            if len(actors)
            else float(event.start_x_normalized)
            if source
            else None
        )
        ay = (
            float(actors.iloc[0].y_normalized)
            if len(actors)
            else float(event.start_y_normalized)
            if source
            else None
        )
        teammates = group[group.teammate & ~group.actor]
        opponents = group[~group.teammate]

        def distances(frame: pd.DataFrame) -> list[float]:
            return [
                math.hypot(float(r.x_normalized) - ax, float(r.y_normalized) - ay)
                for r in frame.itertuples()
                if ax is not None and ay is not None
            ]

        td, od = distances(teammates), distances(opponents)
        keepers = distances(opponents[opponents.keeper])
        area = area_lookup.loc[key] if key in area_lookup.index else None
        rows.append(
            {
                "match_id": key[0],
                "event_id": key[1],
                "team_id": event.team_id,
                "event_type": event.event_type,
                "event_subtype": event.event_subtype,
                "elapsed_seconds": event.elapsed_seconds,
                "has_360_file": True,
                "has_freeze_frame": len(group) > 0,
                "has_visible_area": area is not None and pd.notna(area.polygon_area),
                "actor_visible": len(actors) > 0,
                "actor_location_source": source,
                "visible_teammates": len(teammates),
                "visible_opponents": len(opponents),
                "visible_goalkeepers": int(group.keeper.sum()),
                "nearest_teammate_distance_m": min(td) if td else None,
                "nearest_opponent_distance_m": min(od) if od else None,
                "nearest_opponent_goalkeeper_distance_m": min(keepers) if keepers else None,
                "opponents_within_3m": sum(d <= 3 for d in od),
                "opponents_within_5m": sum(d <= 5 for d in od),
                "opponents_within_10m": sum(d <= 10 for d in od),
                "teammates_within_3m": sum(d <= 3 for d in td),
                "teammates_within_5m": sum(d <= 5 for d in td),
                "teammates_within_10m": sum(d <= 10 for d in td),
                "visible_area_m2": area.polygon_area if area is not None else None,
                "event_inside_visible_area": None,
                "context_valid": ax is not None and ay is not None and len(group) > 0,
                "context_missing_reason": None
                if ax is not None and ay is not None and len(group) > 0
                else "actor_not_visible"
                if len(group) > 0
                else "missing_freeze_frame",
            }
        )
    return pd.DataFrame(rows)


def pressure_context(context: pd.DataFrame) -> pd.DataFrame:
    output = context[context.event_type == "Pressure"].copy()
    output["nearest_opponent_distance"] = output.nearest_opponent_distance_m
    output["nearest_teammate_support_distance"] = output.nearest_teammate_distance_m
    output["local_numerical_balance_5m"] = output.teammates_within_5m - output.opponents_within_5m
    output["local_numerical_balance_10m"] = (
        output.teammates_within_10m - output.opponents_within_10m
    )
    output["visible_opponent_count"] = output.visible_opponents
    output["visible_teammate_count"] = output.visible_teammates
    return output
