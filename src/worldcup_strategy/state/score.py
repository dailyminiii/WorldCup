# mypy: ignore-errors
"""Own-goal-safe regular score reconstruction."""

import pandas as pd


def reconstruct_score(events: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Create two symmetric team-perspective rows per event with before/after scores."""
    rows = []
    match_map = matches.set_index("match_id")
    for match_id, group in events.sort_values(["match_id", "period", "event_index"]).groupby(
        "match_id", sort=False
    ):
        match = match_map.loc[match_id]
        home = int(match.home_team_id)
        away = int(match.away_team_id)
        score = {home: 0, away: 0}
        for event in group.itertuples(index=False):
            before = score.copy()
            scoring = None
            if not event.is_penalty_shootout and bool(event.is_goal):
                scoring = int(event.team_id)
                score[scoring] += 1
            for team, opponent in ((home, away), (away, home)):
                diff_before = before[team] - before[opponent]
                diff_after = score[team] - score[opponent]
                state = lambda d: "leading" if d > 0 else "trailing" if d < 0 else "drawing"
                rows.append(
                    {
                        "match_id": match_id,
                        "event_id": event.event_id,
                        "event_index": event.event_index,
                        "period": event.period,
                        "elapsed_seconds": event.elapsed_seconds,
                        "team_id": team,
                        "opponent_id": opponent,
                        "goals_for_before": before[team],
                        "goals_against_before": before[opponent],
                        "goal_difference_before": diff_before,
                        "score_state_before": state(diff_before),
                        "goals_for_after": score[team],
                        "goals_against_after": score[opponent],
                        "goal_difference_after": diff_after,
                        "score_state_after": state(diff_after),
                        "scoring_event": scoring is not None,
                        "scoring_team_id": scoring,
                        "conceding_team_id": opponent
                        if scoring == team
                        else team
                        if scoring == opponent
                        else None,
                        "score_change": 1 if scoring is not None else 0,
                        "score_event_type": "own_goal"
                        if scoring is not None and event.is_own_goal
                        else "penalty"
                        if scoring is not None and event.is_penalty
                        else "regular_goal"
                        if scoring is not None
                        else None,
                        "score_reconstruction_version": "event_score_own_goal_safe_v1",
                    }
                )
    return pd.DataFrame(rows)


def validate_final_scores(states: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    last = (
        states.sort_values("event_index").groupby(["match_id", "team_id"], as_index=False).tail(1)
    )
    lookup = {(r.match_id, r.team_id): r.goals_for_after for r in last.itertuples()}
    rows = []
    for m in matches.itertuples(index=False):
        rows.append(
            {
                "match_id": m.match_id,
                "metadata_home_score": m.home_score,
                "metadata_away_score": m.away_score,
                "reconstructed_home_score": lookup[(m.match_id, m.home_team_id)],
                "reconstructed_away_score": lookup[(m.match_id, m.away_team_id)],
                "matches": lookup[(m.match_id, m.home_team_id)] == m.home_score
                and lookup[(m.match_id, m.away_team_id)] == m.away_score,
            }
        )
    return pd.DataFrame(rows)
