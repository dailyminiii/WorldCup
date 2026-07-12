# mypy: ignore-errors
"""Pre-declared robustness-grid execution without significance selection."""

import pandas as pd

from worldcup_strategy.models.score_state_models import fit_score_state_models

SPECIFICATIONS = (
    "fixed_five_minute_windows",
    "homogeneous_state_segments",
    "exclude_red_card_affected",
    "group_stage_only",
    "exclude_low_effective_time",
    "team_fixed_effects",
    "match_fixed_effects",
    "match_clustered_errors",
    "team_clustered_errors",
    "alternative_effective_time_gap_cap",
    "raw_count_models_with_offsets",
    "exposure_normalized_outcomes",
    "exclude_extra_time",
    "exclude_mixed_score_state",
)


def _segment_model_frame(segments: pd.DataFrame) -> pd.DataFrame:
    frame = segments.copy()
    frame["window_start_seconds"] = frame.segment_start_seconds
    frame["window_end_seconds"] = frame.segment_end_seconds
    frame["score_state_majority"] = frame.score_state
    frame["red_card_difference_start"] = frame.red_card_difference
    frame["multiple_score_states"] = False
    return frame


def execute_robustness(
    windows: pd.DataFrame,
    segments: pd.DataFrame,
    alternative_gap_windows: pd.DataFrame,
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Execute all estimable grid cells and retain unavailable cells explicitly."""
    stages = matches[["match_id", "competition_stage"]]
    inputs: dict[str, tuple[pd.DataFrame | None, str]] = {
        "fixed_five_minute_windows": (windows, "match_id"),
        "homogeneous_state_segments": (_segment_model_frame(segments), "match_id"),
        "exclude_red_card_affected": (
            windows[
                windows.red_card_difference_start.eq(0) & windows.red_card_difference_end.eq(0)
            ],
            "match_id",
        ),
        "group_stage_only": (
            windows.merge(stages, on="match_id").query("competition_stage == 'Group Stage'"),
            "match_id",
        ),
        "exclude_low_effective_time": (windows[windows.effective_play_seconds >= 30], "match_id"),
        "team_fixed_effects": (windows, "match_id"),
        "match_fixed_effects": (None, "match_id"),
        "match_clustered_errors": (windows, "match_id"),
        "team_clustered_errors": (windows, "team_id"),
        "alternative_effective_time_gap_cap": (alternative_gap_windows, "match_id"),
        "raw_count_models_with_offsets": (windows, "match_id"),
        "exposure_normalized_outcomes": (windows, "match_id"),
        "exclude_extra_time": (windows[windows.period.isin([1, 2])], "match_id"),
        "exclude_mixed_score_state": (windows[~windows.multiple_score_states], "match_id"),
    }
    primary, _ = fit_score_state_models(windows)
    model_ids = sorted(primary.model_id.unique())
    rows = []
    for specification_id in SPECIFICATIONS:
        frame, cluster = inputs[specification_id]
        if frame is None:
            for model_id in model_ids:
                rows.append(
                    {
                        "specification_id": specification_id,
                        "model_id": model_id,
                        "execution_status": "unavailable",
                        "sample_size": 0,
                        "match_count": 0,
                        "team_count": 0,
                        "coefficient": None,
                        "standard_error": None,
                        "confidence_interval": None,
                        "transformed_effect": None,
                        "convergence_status": "not_run",
                        "warning_flags": "",
                        "unavailable_reason": (
                            "match_fixed_effects_not_identifiable_with_team_perspectives"
                        ),
                    }
                )
            continue
        fitted, _ = fit_score_state_models(frame, cluster_variable=cluster)
        for row in fitted.itertuples(index=False):
            rows.append(
                {
                    "specification_id": specification_id,
                    "model_id": row.model_id,
                    "coefficient_name": row.coefficient_name,
                    "execution_status": row.execution_status,
                    "sample_size": row.sample_size,
                    "match_count": row.match_count,
                    "team_count": row.team_count,
                    "coefficient": row.coefficient,
                    "standard_error": row.standard_error,
                    "confidence_interval": (
                        f"[{row.confidence_interval_lower}, {row.confidence_interval_upper}]"
                    ),
                    "transformed_effect": next(
                        (
                            value
                            for value in (
                                row.incidence_rate_ratio,
                                row.odds_ratio,
                                row.adjusted_difference,
                            )
                            if pd.notna(value)
                        ),
                        None,
                    ),
                    "convergence_status": row.convergence_status,
                    "warning_flags": row.warning_flags,
                    "unavailable_reason": row.unavailable_reason,
                }
            )
    return pd.DataFrame(rows)
