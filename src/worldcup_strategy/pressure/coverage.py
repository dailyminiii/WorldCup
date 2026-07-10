# mypy: ignore-errors
"""StatsBomb 360 coverage summaries."""

import pandas as pd


def coverage_tables(
    events: pd.DataFrame, context: pd.DataFrame, matches: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    linked = context.set_index(["match_id", "event_id"])
    rows = []
    for event in events.itertuples(index=False):
        key = (event.match_id, event.event_id)
        c = linked.loc[key] if key in linked.index else None
        rows.append(
            {
                "match_id": event.match_id,
                "team_id": event.team_id,
                "event_type": event.event_type,
                "eligible_events": 1,
                "events_with_360_file": int(c is not None),
                "events_with_freeze_frame": int(c is not None and c.has_freeze_frame),
                "events_with_visible_area": int(c is not None and c.has_visible_area),
                "events_with_visible_actor": int(c is not None and c.actor_visible),
                "valid_context_events": int(c is not None and c.context_valid),
            }
        )
    detail = pd.DataFrame(rows)

    def aggregate(keys: list[str]) -> pd.DataFrame:
        counts = [
            "eligible_events",
            "events_with_360_file",
            "events_with_freeze_frame",
            "events_with_visible_area",
            "events_with_visible_actor",
            "valid_context_events",
        ]
        out = detail.groupby(keys, as_index=False)[counts].sum()
        out["freeze_frame_coverage_rate"] = out.events_with_freeze_frame / out.eligible_events
        out["visible_area_coverage_rate"] = out.events_with_visible_area / out.eligible_events
        out["actor_visible_rate"] = out.events_with_visible_actor / out.eligible_events
        out["valid_context_rate"] = out.valid_context_events / out.eligible_events
        return out

    by_match = aggregate(["match_id"])
    by_team_match = aggregate(["match_id", "team_id"])
    by_type = aggregate(["event_type"])
    return by_match, by_team_match, by_type
