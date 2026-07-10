import pandas as pd

from worldcup_strategy.pressure.context360 import build_context360


def test_actor_geometry_excludes_actor_from_teammates() -> None:
    events = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "e",
                "team_id": 1,
                "event_type": "Pressure",
                "event_subtype": None,
                "elapsed_seconds": 1.0,
                "start_x_normalized": 50.0,
                "start_y_normalized": 34.0,
            }
        ]
    )
    frames = pd.DataFrame(
        [
            {
                "match_id": 1,
                "event_id": "e",
                "actor": True,
                "teammate": True,
                "keeper": False,
                "x_normalized": 50.0,
                "y_normalized": 34.0,
            },
            {
                "match_id": 1,
                "event_id": "e",
                "actor": False,
                "teammate": False,
                "keeper": False,
                "x_normalized": 53.0,
                "y_normalized": 34.0,
            },
        ]
    )
    areas = pd.DataFrame([{"match_id": 1, "event_id": "e", "polygon_area": 100.0}])
    row = build_context360(events, frames, areas).iloc[0]
    assert row.visible_teammates == 0 and row.opponents_within_3m == 1
    assert row.actor_location_source == "freeze_frame_actor"
