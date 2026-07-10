"""Validated project configuration."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class DataConfig(BaseModel):
    """Settings for a StatsBomb competition-season ingestion."""

    model_config = ConfigDict(extra="forbid")

    provider: str = "statsbomb"
    competition_name: str
    season_name: str
    expected_competition_id: int
    expected_season_id: int
    expected_match_count: int = Field(gt=0)
    expected_group_match_count: int = Field(gt=0)
    raw_repository: Path
    processed_directory: Path
    manifest_directory: Path
    report_directory: Path
    table_directory: Path
    source_url: str


def load_data_config(season: int = 2022, path: Path | None = None) -> DataConfig:
    """Load and validate the configured season."""
    config_path = path or Path(f"configs/data_{season}.yaml")
    with config_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return DataConfig.model_validate(payload)
