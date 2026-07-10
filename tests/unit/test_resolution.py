import json
from pathlib import Path

import pytest

from worldcup_strategy.data.statsbomb import resolve_competition


def write_competitions(root: Path, rows: list[dict[str, object]]) -> None:
    data = root / "data"
    data.mkdir()
    (data / "competitions.json").write_text(json.dumps(rows), encoding="utf-8")


def test_resolution_uses_names_then_asserts_ids(tmp_path: Path) -> None:
    write_competitions(
        tmp_path,
        [
            {
                "competition_name": "FIFA World Cup",
                "season_name": "2022",
                "competition_id": 43,
                "season_id": 106,
            }
        ],
    )
    row = resolve_competition(tmp_path, "FIFA World Cup", "2022", 43, 106)
    assert row["season_id"] == 106


def test_resolution_rejects_unexpected_ids(tmp_path: Path) -> None:
    write_competitions(
        tmp_path,
        [
            {
                "competition_name": "FIFA World Cup",
                "season_name": "2022",
                "competition_id": 43,
                "season_id": 999,
            }
        ],
    )
    with pytest.raises(ValueError, match="do not match"):
        resolve_competition(tmp_path, "FIFA World Cup", "2022", 43, 106)
