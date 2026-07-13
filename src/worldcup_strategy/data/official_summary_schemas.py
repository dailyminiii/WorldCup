"""Column contracts for manually verified official match summaries."""

from dataclasses import dataclass

MATCH_COLUMNS = (
    "provider",
    "tournament_year",
    "competition_name",
    "stage",
    "group_name",
    "match_id",
    "match_date",
    "kickoff_datetime",
    "venue",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
    "home_score",
    "away_score",
    "status",
    "match_duration_seconds",
    "source_url",
    "verification_status",
    "duration_verification_status",
)
EVENT_COLUMNS = (
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
)
STAT_COLUMNS = (
    "match_id",
    "team_id",
    "opponent_id",
    "metric_name",
    "metric_value",
    "metric_unit",
    "provider_definition",
    "source_url",
    "verification_status",
)


@dataclass(frozen=True)
class OfficialSummaryPaths:
    """Resolved input files for one official-summary directory."""

    matches: str
    events: str
    statistics: str
