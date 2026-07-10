# mypy: ignore-errors
"""Team-match and tournament defensive-pressure summaries."""

import pandas as pd


def team_match_summary(
    ppda: pd.DataFrame,
    pressures: pd.DataFrame,
    sequences: pd.DataFrame,
    regains: pd.DataFrame,
    high_regains: pd.DataFrame,
    context: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for base in ppda.itertuples(index=False):
        p = pressures[(pressures.match_id == base.match_id) & (pressures.team_id == base.team_id)]
        s = sequences[
            (sequences.match_id == base.match_id) & (sequences.pressing_team_id == base.team_id)
        ]
        r = regains[(regains.match_id == base.match_id) & (regains.team_id == base.team_id)]
        h = high_regains[
            (high_regains.match_id == base.match_id) & (high_regains.team_id == base.team_id)
        ]
        c = context[
            (context.match_id == base.match_id)
            & (context.team_id == base.team_id)
            & (context.event_type == "Pressure")
        ]
        opponent_actions = len(
            events[
                (events.match_id == base.match_id)
                & (events.team_id == base.opponent_id)
                & ~events.is_penalty_shootout
            ]
        )
        opponent_possessions = events[
            (events.match_id == base.match_id) & (events.possession_team_id == base.opponent_id)
        ].possession_id.nunique()
        opponent_events = events[
            (events.match_id == base.match_id)
            & (events.possession_team_id == base.opponent_id)
            & ~events.is_penalty_shootout
        ]
        possession_durations = opponent_events.groupby(["period", "possession_id"])[
            "elapsed_seconds"
        ].agg(lambda values: min(float(values.max() - values.min()), 30.0))
        opponent_seconds = float(possession_durations.sum())
        row = {
            "match_id": base.match_id,
            "team_id": base.team_id,
            "opponent_id": base.opponent_id,
            "pressure_events": len(p),
            "pressure_sequences": len(s),
            "counterpress_events": int(p.counterpress.sum()),
            "high_pressure_events": int(p.is_high_pressure.sum()),
            "pressure_events_per_30_opponent_passes": len(p) / base.classic_opponent_passes * 30
            if base.classic_opponent_passes
            else None,
            "pressure_events_per_100_opponent_actions": len(p) / opponent_actions * 100
            if opponent_actions
            else None,
            "pressure_events_per_opponent_possession": len(p) / opponent_possessions
            if opponent_possessions
            else None,
            "eligible_opponent_possession_seconds": opponent_seconds,
            "pressure_events_per_opponent_possession_minute": (
                len(p) / (opponent_seconds / 60) if opponent_seconds > 0 else None
            ),
            "mean_pressure_height": p.x_pressing_team_frame.mean(),
            "median_pressure_height": p.x_pressing_team_frame.median(),
            "pressure_regain_3s_rate": r.regain_3s.mean() if len(r) else None,
            "pressure_regain_5s_rate": r.regain_5s.mean() if len(r) else None,
            "pressure_regain_8s_rate": r.regain_8s.mean() if len(r) else None,
            "sequence_regain_3s_rate": s.regain_3s.mean() if len(s) and "regain_3s" in s else None,
            "sequence_regain_5s_rate": s.regain_5s.mean() if len(s) and "regain_5s" in s else None,
            "sequence_regain_8s_rate": s.regain_8s.mean() if len(s) and "regain_8s" in s else None,
            "high_regains": int(h.is_high_regain.sum()) if len(h) else 0,
            "shots_after_pressure_regain_10s": int(h.resulted_in_shot_10s.sum()) if len(h) else 0,
            "shots_after_pressure_regain_15s": int(h.resulted_in_shot_15s.sum()) if len(h) else 0,
            "xg_after_pressure_regains": h.same_possession_xg.sum(min_count=1) if len(h) else None,
            "xt_after_pressure_regains": h.same_possession_xt.sum(min_count=1) if len(h) else None,
            "valid_pressure_360_events": int(c.context_valid.sum()) if len(c) else 0,
            "pressure_360_coverage_rate": c.context_valid.mean() if len(p) and len(c) else 0.0,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def team_tournament_summary(team_match: pd.DataFrame) -> pd.DataFrame:
    count_cols = [
        "pressure_events",
        "pressure_sequences",
        "counterpress_events",
        "high_pressure_events",
        "high_regains",
        "shots_after_pressure_regain_10s",
        "shots_after_pressure_regain_15s",
        "valid_pressure_360_events",
    ]
    out = team_match.groupby("team_id", as_index=False)[count_cols].sum(min_count=1)
    out.insert(1, "matches", team_match.groupby("team_id").size().to_numpy())
    return out
