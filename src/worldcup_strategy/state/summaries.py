# mypy: ignore-errors
"""Non-causal descriptive summaries of score-state windows."""

import pandas as pd

OUTCOMES = (
    "shots",
    "statsbomb_xg",
    "passes",
    "completed_passes",
    "pressure_events",
    "pressure_regain_5s_rate",
    "substitutions",
    "goalkeeper_substitutions",
    "unknown_substitutions",
    "tactical_shifts",
)


def summarize_score_state(features: pd.DataFrame) -> pd.DataFrame:
    """Return transparent long-form statistics by majority score state."""
    rows = []
    for state, group in features.groupby("score_state_majority", dropna=False):
        for outcome in OUTCOMES:
            values = group[outcome].dropna()
            if outcome == "pressure_regain_5s_rate":
                numerator = float(group.pressure_regains_5s.sum())
                denominator = float(group.pressure_events.sum())
            elif outcome == "completed_passes":
                numerator = float(group.completed_passes.sum())
                denominator = float(group.passes.sum())
            else:
                numerator = float(values.sum())
                denominator = float(group.effective_play_seconds.sum())
            rows.append(
                {
                    "score_state": state,
                    "outcome": outcome,
                    "observation_count": len(values),
                    "raw_numerator": numerator,
                    "raw_denominator": denominator,
                    "pooled_rate": numerator / denominator if denominator > 0 else None,
                    "effective_time_exposure": float(group.effective_play_seconds.sum()),
                    "possession_exposure": float(group.possessions.sum()),
                    "team_count": int(group.team_id.nunique()),
                    "match_count": int(group.match_id.nunique()),
                    "mean": float(values.mean()) if len(values) else None,
                    "standard_deviation": float(values.std()) if len(values) > 1 else None,
                    "median": float(values.median()) if len(values) else None,
                    "q1": float(values.quantile(0.25)) if len(values) else None,
                    "q3": float(values.quantile(0.75)) if len(values) else None,
                    "minimum": float(values.min()) if len(values) else None,
                    "maximum": float(values.max()) if len(values) else None,
                    "interpretation": "descriptive association; not causal",
                }
            )
    return pd.DataFrame(rows)
