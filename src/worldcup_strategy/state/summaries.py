# mypy: ignore-errors
"""Non-causal descriptive summaries of score-state windows."""

import pandas as pd

OUTCOMES = (
    "shots_per_effective_10min",
    "xg_per_effective_10min",
    "xt_per_effective_10min",
    "progressive_passes_per_100_passes",
    "progressive_carries_per_100_possessions",
    "possession_share",
    "pass_completion_rate",
    "forward_pass_share",
    "long_pass_share",
    "pass_directness",
    "mean_pass_length",
    "ppda_classic",
    "pressure_events_per_30_opponent_passes",
    "high_pressure_share",
    "pressure_regain_5s_rate",
    "sequence_regain_5s_rate",
    "any_substitution",
    "tactical_shifts",
)


def summarize_score_state(features: pd.DataFrame) -> pd.DataFrame:
    """Return transparent long-form statistics by majority score state."""
    rows = []
    for state, group in features.groupby("score_state_majority", dropna=False):
        for outcome in OUTCOMES:
            values = group[outcome].dropna()
            numerator_column = f"{outcome}_numerator"
            denominator_column = f"{outcome}_denominator"
            if numerator_column in group and denominator_column in group:
                numerator = float(group[numerator_column].sum(min_count=1))
                denominator = float(group[denominator_column].sum(min_count=1))
            else:
                numerator = float(values.sum())
                denominator = float(len(values))
            reliable_column = f"{outcome}_reliable"
            reliable = (
                group[reliable_column]
                if reliable_column in group
                else pd.Series(True, index=group.index)
            )
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
                    "unweighted_window_mean": float(values.mean()) if len(values) else None,
                    "unweighted_window_sd": float(values.std()) if len(values) > 1 else None,
                    "mean": float(values.mean()) if len(values) else None,
                    "standard_deviation": float(values.std()) if len(values) > 1 else None,
                    "median": float(values.median()) if len(values) else None,
                    "q1": float(values.quantile(0.25)) if len(values) else None,
                    "q3": float(values.quantile(0.75)) if len(values) else None,
                    "minimum": float(values.min()) if len(values) else None,
                    "maximum": float(values.max()) if len(values) else None,
                    "reliable_observation_count": int(reliable.sum()),
                    "unreliable_observation_count": int((~reliable).sum()),
                    "missing_observation_count": int(group[outcome].isna().sum()),
                    "interpretation": "descriptive association; not causal",
                }
            )
    return pd.DataFrame(rows)
