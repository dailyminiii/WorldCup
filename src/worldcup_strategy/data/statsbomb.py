"""StatsBomb Open Data reader and canonical converter."""

import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import pandas as pd

from worldcup_strategy.constants import PROVIDER
from worldcup_strategy.data.coordinates import elapsed_seconds, normalize_location
from worldcup_strategy.data.schemas import empty_table, enforce_columns


def read_json(path: Path) -> Any:
    """Read provider JSON with a path-specific error."""
    if not path.is_file():
        raise FileNotFoundError(f"Required StatsBomb file is missing: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_competition(
    repository: Path,
    competition_name: str,
    season_name: str,
    expected_competition_id: int,
    expected_season_id: int,
) -> dict[str, Any]:
    """Resolve names from competitions.json and assert expected identity."""
    records = cast(list[dict[str, Any]], read_json(repository / "data" / "competitions.json"))
    matches = [
        row
        for row in records
        if row.get("competition_name") == competition_name
        and str(row.get("season_name")) == str(season_name)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {competition_name!r} {season_name!r}; found {len(matches)}"
        )
    row = matches[0]
    actual = (row.get("competition_id"), row.get("season_id"))
    expected = (expected_competition_id, expected_season_id)
    if actual != expected:
        raise ValueError(f"Resolved IDs {actual} do not match expected IDs {expected}")
    return row


def canonical_competition(row: dict[str, Any]) -> pd.DataFrame:
    """Convert one competition-season record."""
    result = {
        "provider": PROVIDER,
        "competition_id": row.get("competition_id"),
        "season_id": row.get("season_id"),
        "competition_name": row.get("competition_name"),
        "season_name": str(row.get("season_name")),
        "country_name": row.get("country_name"),
        "gender": row.get("competition_gender"),
        "is_international": row.get("competition_international"),
    }
    return enforce_columns(pd.DataFrame([result]), "competitions")


def load_matches(repository: Path, competition_id: int, season_id: int) -> list[dict[str, Any]]:
    """Load the match list for a resolved competition-season."""
    return cast(
        list[dict[str, Any]],
        read_json(repository / "data" / "matches" / str(competition_id) / f"{season_id}.json"),
    )


def canonical_matches(rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Convert StatsBomb match records."""
    output: list[dict[str, Any]] = []
    for row in rows:
        stage = (row.get("competition_stage") or {}).get("name")
        home_group = (row.get("home_team") or {}).get("home_team_group")
        away_group = (row.get("away_team") or {}).get("away_team_group")
        provider_group = home_group or away_group
        group_name = (
            f"Group {provider_group}"
            if stage == "Group Stage" and provider_group
            else stage
            if isinstance(stage, str) and stage.startswith("Group ")
            else None
        )
        output.append(
            {
                "provider": PROVIDER,
                "competition_id": row.get("competition", {}).get("competition_id"),
                "season_id": row.get("season", {}).get("season_id"),
                "match_id": row.get("match_id"),
                "match_date": row.get("match_date"),
                "kickoff_datetime": f"{row.get('match_date')}T{row.get('kick_off')}",
                "competition_stage": stage,
                "group_name": group_name,
                "match_week": row.get("match_week"),
                "home_team_id": row.get("home_team", {}).get("home_team_id"),
                "home_team_name": row.get("home_team", {}).get("home_team_name"),
                "away_team_id": row.get("away_team", {}).get("away_team_id"),
                "away_team_name": row.get("away_team", {}).get("away_team_name"),
                "home_score": row.get("home_score"),
                "away_score": row.get("away_score"),
                "status": row.get("match_status"),
                "stadium": (row.get("stadium") or {}).get("name"),
                "referee": (row.get("referee") or {}).get("name"),
            }
        )
    frame = pd.DataFrame(output) if output else empty_table("matches")
    return enforce_columns(frame, "matches")


def _nested_name(event: dict[str, Any], section: str, key: str) -> Any:
    value = event.get(section)
    return value.get(key) if isinstance(value, dict) else None


def _event_end_location(event: dict[str, Any], event_type: str | None) -> object:
    section = event_type.lower().replace(" ", "_") if event_type else ""
    nested = event.get(section)
    return nested.get("end_location") if isinstance(nested, dict) else None


def _name(value: object) -> object:
    return value.get("name") if isinstance(value, dict) else None


def canonical_events(match_id: int, events: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Convert StatsBomb events without zero-imputing absent fields."""
    output: list[dict[str, Any]] = []
    for ordinal, event in enumerate(events):
        event_type = _nested_name(event, "type", "name")
        section = event_type.lower().replace(" ", "_") if isinstance(event_type, str) else ""
        raw_detail = event.get(section)
        detail: dict[str, Any] = raw_detail if isinstance(raw_detail, dict) else {}
        raw_shot = event.get("shot")
        shot: dict[str, Any] = raw_shot if isinstance(raw_shot, dict) else {}
        outcome = detail.get("outcome") if isinstance(detail, dict) else None
        outcome_name = outcome.get("name") if isinstance(outcome, dict) else None
        start = normalize_location(event.get("location"))
        end = normalize_location(_event_end_location(event, event_type))
        shot_outcome = shot.get("outcome") if isinstance(shot, dict) else None
        shot_outcome_name = shot_outcome.get("name") if isinstance(shot_outcome, dict) else None
        shot_type = shot.get("type") if isinstance(shot, dict) else None
        shot_type_name = shot_type.get("name") if isinstance(shot_type, dict) else None
        own_goal = event_type in {"Own Goal Against", "Own Goal For"}
        scoring_own_goal_record = event_type == "Own Goal For"
        period = event.get("period")
        output.append(
            {
                "provider": PROVIDER,
                "match_id": match_id,
                "event_id": event.get("id"),
                "event_index": event.get("index", ordinal),
                "period": period,
                "minute": event.get("minute"),
                "second": event.get("second"),
                "timestamp": event.get("timestamp"),
                "elapsed_seconds": elapsed_seconds(event.get("minute"), event.get("second")),
                "team_id": (event.get("team") or {}).get("id"),
                "team_name": (event.get("team") or {}).get("name"),
                "player_id": (event.get("player") or {}).get("id"),
                "player_name": (event.get("player") or {}).get("name"),
                "possession_id": event.get("possession"),
                "possession_team_id": (event.get("possession_team") or {}).get("id"),
                "event_type": event_type,
                "event_subtype": shot_type_name if event_type == "Shot" else None,
                "outcome": shot_outcome_name if event_type == "Shot" else outcome_name,
                "play_pattern": (event.get("play_pattern") or {}).get("name"),
                "under_pressure": event.get("under_pressure"),
                "counterpress": event.get("counterpress"),
                "start_x_raw": start.x_raw,
                "start_y_raw": start.y_raw,
                "end_x_raw": end.x_raw,
                "end_y_raw": end.y_raw,
                "start_x_105": start.x_105,
                "start_y_68": start.y_68,
                "end_x_105": end.x_105,
                "end_y_68": end.y_68,
                "start_x_normalized": start.x_normalized,
                "start_y_normalized": start.y_normalized,
                "end_x_normalized": end.x_normalized,
                "end_y_normalized": end.y_normalized,
                "body_part": _name(shot.get("body_part") or detail.get("body_part")),
                "technique": _name(shot.get("technique") or detail.get("technique")),
                "statsbomb_xg": shot.get("statsbomb_xg"),
                # StatsBomb emits paired Own Goal For/Against records. Only the beneficiary's
                # Own Goal For record counts as the scoring record, preventing double counts.
                "is_goal": shot_outcome_name == "Goal" or scoring_own_goal_record,
                "is_own_goal": own_goal,
                "is_penalty": event_type == "Shot" and shot_type_name == "Penalty" and period != 5,
                "is_penalty_shootout": period == 5,
                "is_set_piece": event.get("play_pattern", {}).get("name")
                in {"From Corner", "From Free Kick", "From Throw In", "From Goal Kick"},
                "raw_event_json": json.dumps(event, separators=(",", ":"), sort_keys=True),
            }
        )
    frame = pd.DataFrame(output) if output else empty_table("events")
    return enforce_columns(frame, "events")


def canonical_lineups(match_id: int, rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Flatten team lineups while retaining provider IDs."""
    output: list[dict[str, Any]] = []
    for team in rows:
        for player in team.get("lineup", []):
            output.append(
                {
                    "provider": PROVIDER,
                    "match_id": match_id,
                    "team_id": team.get("team_id"),
                    "team_name": team.get("team_name"),
                    "player_id": player.get("player_id"),
                    "player_name": player.get("player_name"),
                }
            )
    frame = pd.DataFrame(output) if output else empty_table("lineups")
    return enforce_columns(frame, "lineups")


def _polygon_area(points: list[float]) -> float | None:
    if len(points) < 6 or len(points) % 2:
        return None
    pairs = list(zip(points[::2], points[1::2], strict=True))
    if any(not math.isfinite(float(value)) for pair in pairs for value in pair):
        return None
    total = sum(
        x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pairs, pairs[1:] + pairs[:1], strict=True)
    )
    return abs(total) * 0.5 * (105.0 / 120.0) * (68.0 / 80.0)


def canonical_three_sixty(
    match_id: int, rows: Iterable[dict[str, Any]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate freeze frames from visible-area polygons."""
    frames: list[dict[str, Any]] = []
    areas: list[dict[str, Any]] = []
    for row in rows:
        event_id = row.get("event_uuid")
        for index, player in enumerate(row.get("freeze_frame") or []):
            location = normalize_location(player.get("location"))
            frames.append(
                {
                    "match_id": match_id,
                    "event_id": event_id,
                    "frame_player_index": index,
                    "player_id": player.get("player", {}).get("id"),
                    "teammate": player.get("teammate"),
                    "actor": player.get("actor"),
                    "keeper": player.get("keeper"),
                    "x_raw": location.x_raw,
                    "y_raw": location.y_raw,
                    "x_normalized": location.x_normalized,
                    "y_normalized": location.y_normalized,
                }
            )
        polygon = row.get("visible_area")
        normalized: list[float] | None = None
        if isinstance(polygon, list) and len(polygon) % 2 == 0:
            normalized = [
                value
                for x, y in zip(polygon[::2], polygon[1::2], strict=True)
                for value in (x * 105.0 / 120.0, y * 68.0 / 80.0)
            ]
        areas.append(
            {
                "match_id": match_id,
                "event_id": event_id,
                "polygon_raw": json.dumps(polygon) if polygon is not None else None,
                "polygon_normalized": json.dumps(normalized) if normalized is not None else None,
                "polygon_area": _polygon_area(polygon) if isinstance(polygon, list) else None,
            }
        )
    frame_table = pd.DataFrame(frames) if frames else empty_table("freeze_frames")
    area_table = pd.DataFrame(areas) if areas else empty_table("visible_areas")
    return enforce_columns(frame_table, "freeze_frames"), enforce_columns(
        area_table, "visible_areas"
    )
