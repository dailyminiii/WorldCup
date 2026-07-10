"""Milestone 1 build, validation, and coverage orchestration."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from worldcup_strategy.config import DataConfig
from worldcup_strategy.data.manifests import build_match_manifest, write_json
from worldcup_strategy.data.schemas import EVENT_VALIDATION_SCHEMA
from worldcup_strategy.data.statsbomb import (
    canonical_competition,
    canonical_events,
    canonical_lineups,
    canonical_matches,
    canonical_three_sixty,
    load_matches,
    read_json,
    resolve_competition,
)


def _identity(config: DataConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    competition = resolve_competition(
        config.raw_repository,
        config.competition_name,
        config.season_name,
        config.expected_competition_id,
        config.expected_season_id,
    )
    matches = load_matches(
        config.raw_repository, config.expected_competition_id, config.expected_season_id
    )
    return competition, matches


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def build_canonical(config: DataConfig) -> dict[str, int]:
    """Build all Milestone 1 canonical tables and per-match manifests."""
    competition, matches_raw = _identity(config)
    match_table = canonical_matches(matches_raw)
    all_events: list[pd.DataFrame] = []
    all_lineups: list[pd.DataFrame] = []
    all_frames: list[pd.DataFrame] = []
    all_areas: list[pd.DataFrame] = []
    manifests: list[dict[str, Any]] = []
    for match_id_value in match_table["match_id"]:
        match_id = int(match_id_value)
        event_path = config.raw_repository / "data" / "events" / f"{match_id}.json"
        lineup_path = config.raw_repository / "data" / "lineups" / f"{match_id}.json"
        three_path = config.raw_repository / "data" / "three-sixty" / f"{match_id}.json"
        all_events.append(canonical_events(match_id, read_json(event_path)))
        all_lineups.append(canonical_lineups(match_id, read_json(lineup_path)))
        if three_path.is_file():
            frames, areas = canonical_three_sixty(match_id, read_json(three_path))
            all_frames.append(frames)
            all_areas.append(areas)
        manifests.append(
            build_match_manifest(
                config.raw_repository,
                config.expected_competition_id,
                config.expected_season_id,
                match_id,
            )
        )
    tables = {
        "competitions": canonical_competition(competition),
        "matches": match_table,
        "events": pd.concat(all_events, ignore_index=True),
        "lineups": pd.concat(all_lineups, ignore_index=True),
        "freeze_frames": pd.concat(all_frames, ignore_index=True)
        if all_frames
        else canonical_three_sixty(0, [])[0],
        "visible_areas": pd.concat(all_areas, ignore_index=True)
        if all_areas
        else canonical_three_sixty(0, [])[1],
    }
    for name, table in tables.items():
        _write_parquet(table, config.processed_directory / f"{name}_2022.parquet")
    manifest_path = config.manifest_directory / "matches_2022.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in manifests), encoding="utf-8"
    )
    return {name: len(table) for name, table in tables.items()}


def coverage_report(config: DataConfig) -> dict[str, Any]:
    """Compute actual Event/lineup/360 coverage from source and processed tables."""
    _, matches = _identity(config)
    match_ids = [int(row["match_id"]) for row in matches]
    group_matches = sum(
        str((row.get("competition_stage") or {}).get("name", "")).startswith("Group ")
        for row in matches
    )
    event_count = 0
    lineup_count = 0
    three_matches = 0
    linked_events = 0
    events_with_locations = 0
    shots = 0
    shots_with_xg = 0
    malformed_polygons = 0
    missing_team_ids = 0
    missing_player_ids = 0
    event_ids: list[str] = []
    event_types_total: dict[str, int] = {}
    event_types_360: dict[str, int] = {}
    for match_id in match_ids:
        events = read_json(config.raw_repository / "data" / "events" / f"{match_id}.json")
        lineups = read_json(config.raw_repository / "data" / "lineups" / f"{match_id}.json")
        event_by_id = {row.get("id"): row for row in events}
        event_count += len(events)
        lineup_count += sum(len(team.get("lineup", [])) for team in lineups)
        for event in events:
            event_id = event.get("id")
            if isinstance(event_id, str):
                event_ids.append(event_id)
            name = (event.get("type") or {}).get("name", "Unknown")
            event_types_total[name] = event_types_total.get(name, 0) + 1
            events_with_locations += event.get("location") is not None
            missing_team_ids += (event.get("team") or {}).get("id") is None
            missing_player_ids += (
                event.get("player") is not None and event["player"].get("id") is None
            )
            if name == "Shot":
                shots += 1
                shots_with_xg += (event.get("shot") or {}).get("statsbomb_xg") is not None
        three_path = config.raw_repository / "data" / "three-sixty" / f"{match_id}.json"
        if three_path.is_file():
            three_matches += 1
            rows = read_json(three_path)
            linked_events += len(rows)
            for row in rows:
                event = event_by_id.get(row.get("event_uuid"), {})
                name = (event.get("type") or {}).get("name", "Unknown")
                event_types_360[name] = event_types_360.get(name, 0) + 1
                polygon = row.get("visible_area")
                malformed_polygons += (
                    not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2
                )
    coverage_by_type = [
        {
            "event_type": name,
            "events": total,
            "three_sixty_linked": event_types_360.get(name, 0),
            "coverage_proportion": event_types_360.get(name, 0) / total,
        }
        for name, total in sorted(event_types_total.items())
    ]
    return {
        "competition_id": config.expected_competition_id,
        "season_id": config.expected_season_id,
        "match_count": len(matches),
        "group_stage_match_count": group_matches,
        "knockout_match_count": len(matches) - group_matches,
        "event_count": event_count,
        "lineup_player_records": lineup_count,
        "three_sixty_match_count": three_matches,
        "three_sixty_linked_event_count": linked_events,
        "events_with_locations": events_with_locations,
        "shots": shots,
        "shots_with_xg": shots_with_xg,
        "missing_team_ids": missing_team_ids,
        "missing_player_ids": missing_player_ids,
        "duplicated_event_ids": len(event_ids) - len(set(event_ids)),
        "malformed_visible_area_polygons": malformed_polygons,
        "coverage_by_event_type": coverage_by_type,
    }


def write_coverage(config: DataConfig) -> dict[str, Any]:
    """Write JSON, Markdown, and CSV coverage artifacts."""
    report = coverage_report(config)
    write_json(config.report_directory / "data_coverage_2022.json", report)
    headline = {key: value for key, value in report.items() if key != "coverage_by_event_type"}
    markdown = "# StatsBomb 2022 coverage\n\n"
    markdown += "StatsBomb 360 is event-linked freeze-frame context, not tracking.\n\n"
    markdown += "| Measure | Observed |\n|---|---:|\n"
    markdown += "".join(f"| {key} | {value} |\n" for key, value in headline.items())
    path = config.report_directory / "data_coverage_2022.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    config.table_directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report["coverage_by_event_type"]).to_csv(
        config.table_directory / "data_coverage_2022.csv", index=False
    )
    return report


def validate_data(config: DataConfig) -> dict[str, Any]:
    """Validate identity, completeness, and canonical event constraints."""
    report = coverage_report(config)
    errors: list[str] = []
    if report["match_count"] != config.expected_match_count:
        errors.append(
            f"expected {config.expected_match_count} matches, observed {report['match_count']}"
        )
    if report["group_stage_match_count"] != config.expected_group_match_count:
        errors.append(
            "expected "
            f"{config.expected_group_match_count} group matches, "
            f"observed {report['group_stage_match_count']}"
        )
    if report["duplicated_event_ids"]:
        errors.append(f"observed {report['duplicated_event_ids']} duplicate event IDs")
    event_path = config.processed_directory / "events_2022.parquet"
    if event_path.is_file():
        EVENT_VALIDATION_SCHEMA.validate(pd.read_parquet(event_path), lazy=True)
    report["validation_errors"] = errors
    report["valid"] = not errors
    write_json(config.report_directory / "data_validation_2022.json", report)
    if errors:
        raise ValueError("; ".join(errors))
    return report
