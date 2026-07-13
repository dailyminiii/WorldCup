# mypy: ignore-errors
"""Locked robustness grid for the pressing score-state analysis."""

import pandas as pd

from worldcup_strategy.analysis.pressing.models import (
    fit_efficiency,
    fit_intensity,
    fit_negative_binomial_intensity,
)

SPECIFICATION_GROUPS = (
    "primary_five_minute_windows",
    "homogeneous_state_segments",
    "mixed_state_duration_proportions",
    "exclude_red_card_affected",
    "group_stage_only",
    "knockout_only",
    "exclude_extra_time",
    "alternative_minimum_denominators",
    "opponent_possession_count_exposure",
    "opponent_possession_seconds_exposure",
    "event_level_regain",
    "sequence_regain_3s",
    "sequence_regain_8s",
    "team_clustered_uncertainty",
    "match_fixed_effects",
    "exact_goal_difference",
)


def _mixed_state_rows(windows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    count_columns = [
        "pressure_events",
        "opponent_passes",
        "pressure_sequences",
        "sequence_regains_3s",
        "sequence_regains_5s",
        "sequence_regains_8s",
        "pressure_regains_5s",
    ]
    for state, duration_column in (
        ("leading", "time_leading_seconds"),
        ("drawing", "time_drawing_seconds"),
        ("trailing", "time_trailing_seconds"),
    ):
        selected = windows[
            windows.regular_period & windows.numerically_equal & windows[duration_column].gt(0)
        ].copy()
        weight = selected[duration_column] / selected.wall_clock_seconds
        selected["score_state_majority"] = state
        selected["multiple_score_states"] = False
        selected["common_primary_eligible"] = True
        for column in count_columns:
            selected[column] = selected[column] * weight
        rows.append(selected)
    return pd.concat(rows, ignore_index=True)


def _unavailable(
    specification_group: str,
    specification_id: str,
    model_id: str,
    reason: str,
) -> dict[str, object]:
    return {
        "specification_group": specification_group,
        "specification_id": specification_id,
        "model_id": model_id,
        "execution_status": "unavailable",
        "coefficient_name": None,
        "coefficient": None,
        "standard_error": None,
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "transformed_effect": None,
        "sample_size": 0,
        "match_count": 0,
        "team_count": 0,
        "convergence_status": "not_run",
        "warning_flags": "",
        "unavailable_reason": reason,
    }


def _annotate(
    table: pd.DataFrame, specification_group: str, specification_id: str
) -> list[dict[str, object]]:
    rows = []
    for row in table.itertuples(index=False):
        transformed = (
            row.incidence_rate_ratio if pd.notna(row.incidence_rate_ratio) else row.odds_ratio
        )
        rows.append(
            {
                "specification_group": specification_group,
                "specification_id": specification_id,
                "model_id": row.model_id,
                "execution_status": row.execution_status,
                "coefficient_name": row.coefficient_name,
                "coefficient": row.coefficient,
                "standard_error": row.standard_error,
                "confidence_interval_lower": row.confidence_interval_lower,
                "confidence_interval_upper": row.confidence_interval_upper,
                "transformed_effect": transformed,
                "sample_size": row.sample_size,
                "match_count": row.match_count,
                "team_count": row.team_count,
                "convergence_status": row.convergence_status,
                "warning_flags": row.warning_flags,
                "unavailable_reason": row.unavailable_reason,
            }
        )
    return rows


def execute_robustness(windows: pd.DataFrame, segments: pd.DataFrame) -> pd.DataFrame:
    """Execute every estimable preregistered robustness specification."""
    rows: list[dict[str, object]] = []

    def both(
        frame: pd.DataFrame,
        group: str,
        specification_id: str,
        *,
        minimum_passes: int = 5,
        minimum_sequences: int = 3,
        cluster: str = "match_id",
        match_effects: bool = False,
        exact_goal_difference: bool = False,
    ) -> None:
        intensity, _, _ = fit_intensity(
            frame,
            minimum_passes=minimum_passes,
            cluster_variable=cluster,
            include_match_effects=match_effects,
            exact_goal_difference=exact_goal_difference,
            model_id=f"robust_intensity:{specification_id}",
        )
        efficiency, _, _ = fit_efficiency(
            frame,
            minimum_trials=minimum_sequences,
            cluster_variable=cluster,
            include_match_effects=match_effects,
            exact_goal_difference=exact_goal_difference,
            model_id=f"robust_efficiency:{specification_id}",
            analysis_role="robustness",
        )
        rows.extend(_annotate(intensity, group, specification_id))
        rows.extend(_annotate(efficiency, group, specification_id))

    both(windows, "primary_five_minute_windows", "primary")
    negative_binomial, _ = fit_negative_binomial_intensity(windows)
    rows.extend(
        _annotate(
            negative_binomial,
            "negative_binomial_overdispersion",
            "negative_binomial",
        )
    )
    both(segments, "homogeneous_state_segments", "segments")
    both(
        _mixed_state_rows(windows),
        "mixed_state_duration_proportions",
        "mixed_duration_weighted",
    )
    red_free = windows[
        windows.red_card_difference_start.eq(0) & windows.red_card_difference_end.eq(0)
    ]
    both(red_free, "exclude_red_card_affected", "red_card_free")
    both(
        windows[windows.competition_stage.eq("Group Stage")],
        "group_stage_only",
        "group_stage",
    )
    knockout = windows[~windows.competition_stage.eq("Group Stage")]
    both(knockout, "knockout_only", "knockout")
    both(windows[windows.period.isin([1, 2])], "exclude_extra_time", "regular_periods")
    for minimum in (3, 5, 10):
        intensity, _, _ = fit_intensity(
            windows,
            minimum_passes=minimum,
            model_id=f"robust_intensity:passes_{minimum}",
        )
        rows.extend(
            _annotate(
                intensity,
                "alternative_minimum_denominators",
                f"opponent_passes_{minimum}",
            )
        )
    for minimum in (1, 3, 5):
        efficiency, _, _ = fit_efficiency(
            windows,
            minimum_trials=minimum,
            model_id=f"robust_efficiency:sequences_{minimum}",
            analysis_role="robustness",
        )
        rows.extend(
            _annotate(
                efficiency,
                "alternative_minimum_denominators",
                f"pressure_sequences_{minimum}",
            )
        )
    for exposure, group, minimum in (
        ("opponent_possessions", "opponent_possession_count_exposure", 1),
        ("opponent_possession_seconds", "opponent_possession_seconds_exposure", 30),
    ):
        intensity, _, _ = fit_intensity(
            windows,
            minimum_passes=minimum,
            exposure_column=exposure,
            model_id=f"robust_intensity:{group}",
        )
        rows.extend(_annotate(intensity, group, group))
        rows.append(
            _unavailable(
                group,
                group,
                "primary_sequence_regain_5s",
                "intensity_exposure_specification_not_applicable",
            )
        )
    for successes, trials, group, minimum in (
        ("pressure_regains_5s", "pressure_events", "event_level_regain", 3),
        ("sequence_regains_3s", "pressure_sequences", "sequence_regain_3s", 3),
        ("sequence_regains_8s", "pressure_sequences", "sequence_regain_8s", 3),
    ):
        efficiency, _, _ = fit_efficiency(
            windows,
            successes_column=successes,
            trials_column=trials,
            minimum_trials=minimum,
            model_id=f"robust_efficiency:{group}",
            analysis_role="robustness",
        )
        rows.extend(_annotate(efficiency, group, group))
        rows.append(
            _unavailable(
                group,
                group,
                "primary_pressing_intensity",
                "regain_definition_specification_not_applicable",
            )
        )
    both(
        windows,
        "team_clustered_uncertainty",
        "team_clustered",
        cluster="team_id",
    )
    both(windows, "match_fixed_effects", "match_fixed_effects", match_effects=True)
    both(
        windows,
        "exact_goal_difference",
        "exact_goal_difference",
        exact_goal_difference=True,
    )
    output = pd.DataFrame(rows)
    baseline = output[
        (output.specification_group == "primary_five_minute_windows")
        & (output.execution_status == "executed")
    ][["coefficient_name", "model_id", "coefficient", "sample_size"]].copy()
    baseline["primary_family"] = baseline.model_id.str.extract(r"robust_(intensity|efficiency)")
    baseline = baseline.rename(
        columns={"coefficient": "baseline_coefficient", "sample_size": "baseline_sample_size"}
    )[["coefficient_name", "primary_family", "baseline_coefficient", "baseline_sample_size"]]
    output["primary_family"] = output.model_id.str.extract(
        r"(?:robust_|primary_)(intensity|efficiency)"
    )
    output = output.merge(baseline, on=["coefficient_name", "primary_family"], how="left")
    output["coefficient_sign"] = output.coefficient.apply(
        lambda value: None
        if pd.isna(value)
        else "positive"
        if value > 0
        else "negative"
        if value < 0
        else "zero"
    )
    output["sign_consistent_with_primary"] = (
        output.coefficient * output.baseline_coefficient >= 0
    ).where(output.coefficient.notna() & output.baseline_coefficient.notna())
    output["magnitude_ratio_to_primary"] = (
        output.coefficient.abs() / output.baseline_coefficient.abs()
    ).where(output.baseline_coefficient.notna() & output.baseline_coefficient.ne(0))
    output["confidence_interval_width"] = (
        output.confidence_interval_upper - output.confidence_interval_lower
    )
    output["sample_size_change"] = output.sample_size - output.baseline_sample_size
    return output
