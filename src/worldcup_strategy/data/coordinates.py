"""Coordinate and match-time normalization."""

from dataclasses import dataclass

from worldcup_strategy.constants import (
    METRIC_PITCH_LENGTH,
    METRIC_PITCH_WIDTH,
    RAW_PITCH_LENGTH,
    RAW_PITCH_WIDTH,
)


@dataclass(frozen=True)
class CoordinateSet:
    """Raw, metric, and left-to-right attacking coordinates."""

    x_raw: float | None
    y_raw: float | None
    x_105: float | None
    y_68: float | None
    x_normalized: float | None
    y_normalized: float | None


def normalize_location(location: object, *, attacking_left_to_right: bool = True) -> CoordinateSet:
    """Scale a StatsBomb location while preserving missing/invalid values as null.

    StatsBomb event coordinates are provider-standardized to the acting team's attacking
    perspective. The direction flag is explicit so another provider can supply observed
    team-period direction and use the same canonical contract.
    """
    if not isinstance(location, list) or len(location) < 2:
        return CoordinateSet(None, None, None, None, None, None)
    x, y = location[0], location[1]
    if not isinstance(x, int | float) or not isinstance(y, int | float):
        return CoordinateSet(None, None, None, None, None, None)
    raw_x, raw_y = float(x), float(y)
    if not (0.0 <= raw_x <= RAW_PITCH_LENGTH and 0.0 <= raw_y <= RAW_PITCH_WIDTH):
        return CoordinateSet(raw_x, raw_y, None, None, None, None)
    metric_x = raw_x * METRIC_PITCH_LENGTH / RAW_PITCH_LENGTH
    metric_y = raw_y * METRIC_PITCH_WIDTH / RAW_PITCH_WIDTH
    if attacking_left_to_right:
        normalized_x, normalized_y = metric_x, metric_y
    else:
        normalized_x = METRIC_PITCH_LENGTH - metric_x
        normalized_y = METRIC_PITCH_WIDTH - metric_y
    return CoordinateSet(raw_x, raw_y, metric_x, metric_y, normalized_x, normalized_y)


def elapsed_seconds(minute: object, second: object) -> float | None:
    """Convert StatsBomb cumulative minute/second fields to elapsed match seconds."""
    if not isinstance(minute, int | float) or not isinstance(second, int | float):
        return None
    value = float(minute) * 60.0 + float(second)
    return value if value >= 0 else None
