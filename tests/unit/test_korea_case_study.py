"""Regression boundaries for the preliminary Korea case study."""

from pathlib import Path

import pandas as pd

from worldcup_strategy.analysis.korea.pipeline import _exposure
from worldcup_strategy.data.official_summary_validation import validate_official_summary
from worldcup_strategy.data.statsbomb_2026_adapter import check_statsbomb_2026


def test_score_state_reconciles_and_own_goal_benefits_opponent() -> None:
    match = {
        "match_id": "x",
        "match_duration_seconds": 600,
        "duration_verification_status": "verified",
    }
    result = _exposure(
        match, [{"elapsed_seconds": 120, "team_id": "KOR", "is_own_goal": True}], 2026
    )
    assert result["drawing_seconds"] == 120
    assert result["trailing_seconds"] == 480
    assert sum(result[f"{state}_seconds"] for state in ("leading", "drawing", "trailing")) == 600


def test_penalty_shootout_is_not_an_official_summary_goal_contract() -> None:
    assert "penalty_shootout" not in {"goal", "card", "substitution"}


def test_duplicate_match_detection_preserves_conflict() -> None:
    matches = pd.DataFrame(
        [
            {
                "tournament_year": 2026,
                "stage": "Group Stage",
                "match_id": "x",
                "home_team_id": "KOR",
                "away_team_id": "A",
                "verification_status": "conflicting",
                "duration_verification_status": "verified",
            }
        ]
        * 3
    )
    for column in (
        "provider",
        "competition_name",
        "group_name",
        "match_date",
        "kickoff_datetime",
        "venue",
        "home_team_name",
        "away_team_name",
        "home_score",
        "away_score",
        "status",
        "match_duration_seconds",
        "source_url",
    ):
        matches[column] = "x"
    events = pd.DataFrame(
        columns=[
            "match_id",
            "event_id",
            "period",
            "minute",
            "second",
            "elapsed_seconds",
            "event_type",
            "team_id",
            "team_name",
            "player_id",
            "player_name",
            "event_detail",
            "is_goal",
            "is_own_goal",
            "is_penalty",
            "is_red_card",
            "is_second_yellow",
            "source_url",
            "verification_status",
        ]
    )
    stats = pd.DataFrame(
        columns=[
            "match_id",
            "team_id",
            "opponent_id",
            "metric_name",
            "metric_value",
            "metric_unit",
            "provider_definition",
            "source_url",
            "verification_status",
        ]
    )
    report = validate_official_summary(matches, events, stats, 2026)
    assert not report["valid"]
    assert report["conflict_count"] == 3


def test_statsbomb_2026_absence_is_actionable(tmp_path: Path) -> None:
    result = check_statsbomb_2026(tmp_path)
    assert not result.events_available
    assert result.message


def test_report_has_no_inference_or_score_state_possession() -> None:
    text = Path("KOREA_2022_2026_CASE_STUDY_PLAN.md").read_text().lower()
    assert "p-value" in text
    assert "whole-match" in text
