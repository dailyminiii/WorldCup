# ruff: noqa: E501
"""Availability-only adapter for a future StatsBomb Open Data 2026 release."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class StatsBomb2026Availability:
    competition_available: bool
    matches_available: bool
    events_available: bool
    lineups_available: bool
    three_sixty_available: bool
    korea_match_count: int
    competition_id: int | None = None
    season_id: int | None = None
    message: str = ""


def check_statsbomb_2026(
    repository: Path = Path("data/raw/statsbomb-open-data"),
) -> StatsBomb2026Availability:
    """Inspect documented Open Data paths without network access or coverage fabrication."""
    competitions = repository / "data/competitions.json"
    if not competitions.exists():
        return StatsBomb2026Availability(
            False,
            False,
            False,
            False,
            False,
            0,
            message="StatsBomb Open Data checkout not found. Fetch/update the configured checkout, then rerun this command.",
        )
    records = json.loads(competitions.read_text())
    candidates = [
        row
        for row in records
        if row.get("competition_name") == "FIFA World Cup"
        and (row.get("season_name") == "2026" or row.get("season_name") == 2026)
    ]
    if not candidates:
        return StatsBomb2026Availability(
            False,
            False,
            False,
            False,
            False,
            0,
            message="FIFA World Cup 2026 is not present in the configured StatsBomb Open Data checkout.",
        )
    row = candidates[0]
    cid, sid = int(row["competition_id"]), int(row["season_id"])
    match_file = repository / f"data/matches/{cid}/{sid}.json"
    matches = json.loads(match_file.read_text()) if match_file.exists() else []
    korea = [
        m
        for m in matches
        if "Korea" in str(m.get("home_team", {}).get("home_team_name", ""))
        or "Korea" in str(m.get("away_team", {}).get("away_team_name", ""))
    ]
    ids = [int(m["match_id"]) for m in korea]
    return StatsBomb2026Availability(
        True,
        match_file.exists(),
        bool(ids) and all((repository / f"data/events/{mid}.json").exists() for mid in ids),
        bool(ids) and all((repository / f"data/lineups/{mid}.json").exists() for mid in ids),
        bool(ids) and all((repository / f"data/three-sixty/{mid}.json").exists() for mid in ids),
        len(ids),
        cid,
        sid,
        "Coverage flags require every resolved Korea match file.",
    )


def write_availability_report(
    output: Path = Path("outputs/reports/statsbomb_2026_availability.json"),
) -> dict[str, object]:
    report = asdict(check_statsbomb_2026())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
