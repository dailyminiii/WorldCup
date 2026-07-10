import json
import subprocess
from pathlib import Path

import pandas as pd

from worldcup_strategy.config import DataConfig
from worldcup_strategy.data.pipeline import build_canonical, validate_data, write_coverage


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_small_source_builds_all_tables(tmp_path: Path) -> None:
    raw = tmp_path / "source"
    raw.mkdir()
    subprocess.run(["git", "init", "-q", str(raw)], check=True)
    subprocess.run(["git", "-C", str(raw), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(raw), "config", "user.name", "Test"], check=True)
    dump(
        raw / "data/competitions.json",
        [
            {
                "competition_id": 43,
                "season_id": 106,
                "competition_name": "FIFA World Cup",
                "season_name": "2022",
                "country_name": "International",
                "competition_gender": "male",
                "competition_international": True,
            }
        ],
    )
    match = {
        "match_id": 1,
        "match_date": "2022-11-20",
        "kick_off": "10:00:00.000",
        "competition": {"competition_id": 43},
        "season": {"season_id": 106},
        "competition_stage": {"name": "Group A"},
        "match_week": 1,
        "home_team": {"home_team_id": 1, "home_team_name": "A", "home_team_group": "A"},
        "away_team": {"away_team_id": 2, "away_team_name": "B"},
        "home_score": 0,
        "away_score": 0,
        "match_status": "available",
    }
    dump(raw / "data/matches/43/106.json", [match])
    event = {
        "id": "e",
        "index": 1,
        "period": 1,
        "minute": 0,
        "second": 1,
        "timestamp": "00:00:01",
        "type": {"name": "Pass"},
        "team": {"id": 1, "name": "A"},
        "possession": 1,
        "possession_team": {"id": 1},
        "location": [1, 2],
        "pass": {"end_location": [3, 4]},
        "play_pattern": {"name": "Regular Play"},
    }
    dump(raw / "data/events/1.json", [event])
    dump(raw / "data/lineups/1.json", [{"team_id": 1, "team_name": "A", "lineup": []}])
    dump(raw / "data/three-sixty/1.json", [])
    subprocess.run(["git", "-C", str(raw), "add", "data"], check=True)
    subprocess.run(["git", "-C", str(raw), "commit", "-qm", "fixture"], check=True)
    config = DataConfig(
        competition_name="FIFA World Cup",
        season_name="2022",
        expected_competition_id=43,
        expected_season_id=106,
        expected_match_count=1,
        expected_group_match_count=1,
        raw_repository=raw,
        processed_directory=tmp_path / "processed",
        manifest_directory=tmp_path / "manifests",
        report_directory=tmp_path / "reports",
        table_directory=tmp_path / "tables",
        source_url="fixture",
    )
    counts = build_canonical(config)
    assert counts["events"] == 1
    matches = pd.read_parquet(tmp_path / "processed/matches_2022.parquet")
    assert matches.loc[0, "group_name"] == "Group A"
    assert write_coverage(config)["three_sixty_match_count"] == 1
    assert validate_data(config)["valid"] is True
