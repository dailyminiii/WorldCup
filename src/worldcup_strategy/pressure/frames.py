"""Explicit spatial frames for opposing teams."""

from enum import StrEnum


class SpatialFrame(StrEnum):
    ACTING_TEAM = "acting_team"
    POSSESSION_TEAM = "possession_team"
    DEFENDING_TEAM = "defending_team"
    HOME_TEAM = "home_team"
    RAW_STATSBOMB = "raw_statsbomb"


FRAME_VERSION = "opponent_rotation_105x68_v1"


def rotate_opponent(x: float | None, y: float | None) -> tuple[float | None, float | None]:
    """Rotate a metric point 180 degrees into the opposing team's frame."""
    if x is None or y is None:
        return None, None
    return 105.0 - x, 68.0 - y


def possession_frame(
    x: float | None, y: float | None, *, acting_team_id: int, possession_team_id: int
) -> tuple[float | None, float | None]:
    """Express an acting-team-normalized point in the possession team's frame."""
    return (x, y) if acting_team_id == possession_team_id else rotate_opponent(x, y)
