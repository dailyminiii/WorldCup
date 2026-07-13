# mypy: ignore-errors
"""Preregistered descriptive summaries for pressing outcomes."""

import pandas as pd


def _distribution(values: pd.Series) -> dict[str, float | int | None]:
    clean = values.dropna()
    return {
        "unweighted_mean": float(clean.mean()) if len(clean) else None,
        "median": float(clean.median()) if len(clean) else None,
        "q1": float(clean.quantile(0.25)) if len(clean) else None,
        "q3": float(clean.quantile(0.75)) if len(clean) else None,
    }


def descriptive_by_state(windows: pd.DataFrame) -> pd.DataFrame:
    """Keep pooled opportunity rates distinct from unweighted window rates."""
    rows = []
    for state in ("leading", "drawing", "trailing"):
        group = windows[windows.score_state_majority == state]
        intensity = group[group.intensity_primary_eligible]
        intensity_rate = intensity.pressure_events / intensity.opponent_passes * 30
        rows.append(
            {
                "score_state": state,
                "outcome": "pressing_intensity",
                "eligible_windows": len(intensity),
                "matches": intensity.match_id.nunique(),
                "teams": intensity.team_id.nunique(),
                "numerator": int(intensity.pressure_events.sum()),
                "denominator": int(intensity.opponent_passes.sum()),
                "pooled_rate": (
                    float(intensity.pressure_events.sum() / intensity.opponent_passes.sum() * 30)
                    if intensity.opponent_passes.sum() > 0
                    else None
                ),
                **_distribution(intensity_rate),
            }
        )
        efficiency = group[group.efficiency_primary_eligible]
        efficiency_rate = efficiency.sequence_regains_5s / efficiency.pressure_sequences
        rows.append(
            {
                "score_state": state,
                "outcome": "sequence_regain_efficiency_5s",
                "eligible_windows": len(efficiency),
                "matches": efficiency.match_id.nunique(),
                "teams": efficiency.team_id.nunique(),
                "numerator": int(efficiency.sequence_regains_5s.sum()),
                "denominator": int(efficiency.pressure_sequences.sum()),
                "pooled_rate": (
                    float(
                        efficiency.sequence_regains_5s.sum() / efficiency.pressure_sequences.sum()
                    )
                    if efficiency.pressure_sequences.sum() > 0
                    else None
                ),
                **_distribution(efficiency_rate),
            }
        )
    return pd.DataFrame(rows)


def sample_characteristics(windows: pd.DataFrame) -> pd.DataFrame:
    """Summarize score-state exposure and primary opportunities."""
    rows = []
    duration_columns = {
        "leading": "time_leading_seconds",
        "drawing": "time_drawing_seconds",
        "trailing": "time_trailing_seconds",
    }
    for state in ("leading", "drawing", "trailing"):
        group = windows[windows.score_state_majority == state]
        rows.append(
            {
                "score_state": state,
                "all_windows": len(group),
                "common_eligible_windows": int(group.common_primary_eligible.sum()),
                "intensity_eligible_windows": int(group.intensity_primary_eligible.sum()),
                "efficiency_eligible_windows": int(group.efficiency_primary_eligible.sum()),
                "matches": group.loc[group.common_primary_eligible, "match_id"].nunique(),
                "teams": group.loc[group.common_primary_eligible, "team_id"].nunique(),
                "score_state_exposure_seconds": float(windows[duration_columns[state]].sum()),
                "opponent_passes": int(
                    group.loc[group.intensity_primary_eligible, "opponent_passes"].sum()
                ),
                "pressure_events": int(
                    group.loc[group.intensity_primary_eligible, "pressure_events"].sum()
                ),
                "pressure_sequences": int(
                    group.loc[group.efficiency_primary_eligible, "pressure_sequences"].sum()
                ),
                "sequence_regains_5s": int(
                    group.loc[group.efficiency_primary_eligible, "sequence_regains_5s"].sum()
                ),
            }
        )
    return pd.DataFrame(rows)
