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
    inputs: dict[str, tuple[pd.DataFrame, str, bool]] = {
        "fixed_five_minute_windows": (windows, "match_id", False),
        "homogeneous_state_segments": (_segment_model_frame(segments), "match_id", False),
        "exclude_red_card_affected": (
            windows[
                windows.red_card_difference_start.eq(0) & windows.red_card_difference_end.eq(0)
            ],
            "match_id",
            False,
        ),
        "group_stage_only": (
            windows.merge(stages, on="match_id").query("competition_stage == 'Group Stage'"),
            "match_id",
            False,
        ),
        "exclude_low_effective_time": (
            windows[windows.effective_play_seconds >= 30],
            "match_id",
            False,
        ),
        "team_fixed_effects": (windows, "match_id", False),
        "match_fixed_effects": (windows, "match_id", True),
        "match_clustered_errors": (windows, "match_id", False),
        "team_clustered_errors": (windows, "team_id", False),
        "alternative_effective_time_gap_cap": (alternative_gap_windows, "match_id", False),
        "raw_count_models_with_offsets": (windows, "match_id", False),
        "exposure_normalized_outcomes": (windows, "match_id", False),
        "exclude_extra_time": (windows[windows.period.isin([1, 2])], "match_id", False),
        "exclude_mixed_score_state": (windows[~windows.multiple_score_states], "match_id", False),
    }
    rows = []
    for specification_id in SPECIFICATIONS:
        frame, cluster, match_effects = inputs[specification_id]
        fitted, _ = fit_score_state_models(
            frame,
            cluster_variable=cluster,
            include_match_effects=match_effects,
        )
        for row in fitted.itertuples(index=False):
            applicable = True
            if specification_id == "raw_count_models_with_offsets":
                applicable = row.model_family == "poisson" or row.execution_status == "unavailable"
            if specification_id == "exposure_normalized_outcomes":
                applicable = (
                    row.model_family == "ols_clustered" or row.execution_status == "unavailable"
                )
            rows.append(
                {
                    "specification_id": specification_id,
                    "model_id": row.model_id,
                    "coefficient_name": row.coefficient_name,
                    "execution_status": row.execution_status if applicable else "unavailable",
                    "sample_size": row.sample_size,
                    "match_count": row.match_count,
                    "team_count": row.team_count,
                    "coefficient": row.coefficient if applicable else None,
                    "standard_error": row.standard_error if applicable else None,
                    "confidence_interval": (
                        f"[{row.confidence_interval_lower}, {row.confidence_interval_upper}]"
                    )
                    if applicable
                    else None,
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
                    )
                    if applicable
                    else None,
                    "convergence_status": row.convergence_status if applicable else "not_run",
                    "warning_flags": row.warning_flags,
                    "unavailable_reason": row.unavailable_reason
                    if applicable
                    else "specification_not_applicable_to_model_family",
                }
            )
    output = pd.DataFrame(rows)
    baseline = output[
        (output.specification_id == "fixed_five_minute_windows")
        & (output.execution_status == "executed")
    ][["model_id", "coefficient_name", "coefficient", "sample_size"]].rename(
        columns={"coefficient": "baseline_coefficient", "sample_size": "baseline_sample_size"}
    )
    output = output.merge(baseline, on=["model_id", "coefficient_name"], how="left")
    output["coefficient_sign"] = output.coefficient.apply(
        lambda value: (
            None
            if pd.isna(value)
            else "positive"
            if value > 0
            else "negative"
            if value < 0
            else "zero"
        )
    )
    output["sign_consistent_with_baseline"] = (
        output.coefficient * output.baseline_coefficient >= 0
    ).where(output.coefficient.notna() & output.baseline_coefficient.notna())
    output["magnitude_ratio_to_baseline"] = (
        output.coefficient.abs() / output.baseline_coefficient.abs()
    ).where(output.baseline_coefficient.notna() & output.baseline_coefficient.ne(0))
    output["sample_size_change"] = output.sample_size - output.baseline_sample_size
    return output
