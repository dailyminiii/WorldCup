# mypy: ignore-errors
"""Provider-supplied StatsBomb xG extraction and aggregation."""

import pandas as pd


def build_shot_xg(events: pd.DataFrame) -> pd.DataFrame:
    """Build regular-play shot and scoring-own-goal records; exclude shootouts."""
    records = events[
        ((events["event_type"] == "Shot") | (events["is_own_goal"] & events["is_goal"]))
        & ~events["is_penalty_shootout"]
    ].copy()
    records["shot_type"] = records["event_subtype"].where(
        records["event_type"] == "Shot", "Own Goal"
    )
    records["is_open_play"] = records["play_pattern"].eq("Regular Play")
    records.loc[records["is_own_goal"], "statsbomb_xg"] = pd.NA
    columns = [
        "match_id",
        "event_id",
        "team_id",
        "player_id",
        "period",
        "elapsed_seconds",
        "shot_type",
        "play_pattern",
        "body_part",
        "technique",
        "statsbomb_xg",
        "is_goal",
        "is_own_goal",
        "is_penalty",
        "is_penalty_shootout",
        "is_open_play",
        "is_set_piece",
    ]
    return records[columns].reset_index(drop=True)


def team_match_xg(shots: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Aggregate xG without converting missing provider values to zero."""
    team_rows = pd.concat(
        [
            matches[["match_id", "home_team_id"]].rename(columns={"home_team_id": "team_id"}),
            matches[["match_id", "away_team_id"]].rename(columns={"away_team_id": "team_id"}),
        ],
        ignore_index=True,
    )
    true_shots = shots[~shots["is_own_goal"]]
    grouped: list[dict[str, object]] = []
    for row in team_rows.itertuples(index=False):
        team = shots[(shots.match_id == row.match_id) & (shots.team_id == row.team_id)]
        attempts = true_shots[
            (true_shots.match_id == row.match_id) & (true_shots.team_id == row.team_id)
        ]
        xg = attempts["statsbomb_xg"]
        total_xg = xg.sum(min_count=1)
        grouped.append(
            {
                "match_id": int(row.match_id),
                "team_id": int(row.team_id),
                "shots": len(attempts),
                "goals": int(team["is_goal"].sum()),
                "statsbomb_xg": total_xg,
                "non_penalty_xg": attempts.loc[~attempts.is_penalty, "statsbomb_xg"].sum(
                    min_count=1
                ),
                "open_play_xg": attempts.loc[attempts.is_open_play, "statsbomb_xg"].sum(
                    min_count=1
                ),
                "set_piece_xg": attempts.loc[attempts.is_set_piece, "statsbomb_xg"].sum(
                    min_count=1
                ),
                "penalty_xg": attempts.loc[attempts.is_penalty, "statsbomb_xg"].sum(min_count=1),
                "xg_per_shot": total_xg / len(attempts)
                if len(attempts) and pd.notna(total_xg)
                else None,
                "goals_minus_xg": int(team["is_goal"].sum()) - total_xg
                if pd.notna(total_xg)
                else None,
            }
        )
    return pd.DataFrame(grouped).sort_values(["match_id", "team_id"]).reset_index(drop=True)


def team_tournament_xg(team_match: pd.DataFrame) -> pd.DataFrame:
    """Aggregate team-match xG to tournament totals."""
    additive = [
        "shots",
        "goals",
        "statsbomb_xg",
        "non_penalty_xg",
        "open_play_xg",
        "set_piece_xg",
        "penalty_xg",
    ]
    output = team_match.groupby("team_id", as_index=False)[additive].sum(min_count=1)
    output.insert(1, "matches", team_match.groupby("team_id").size().to_numpy())
    output["xg_per_shot"] = output["statsbomb_xg"] / output["shots"].replace(0, pd.NA)
    output["goals_minus_xg"] = output["goals"] - output["statsbomb_xg"]
    return output
