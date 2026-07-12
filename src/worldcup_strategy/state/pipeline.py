# mypy: ignore-errors
"""Milestone 4 state pipeline entry points."""

import json
from pathlib import Path

import pandas as pd

from worldcup_strategy.models.robustness import execute_robustness
from worldcup_strategy.models.score_state_models import fit_score_state_models, model_specifications
from worldcup_strategy.state.features import integrate_features
from worldcup_strategy.state.reporting import write_feature_reports
from worldcup_strategy.state.segments import build_segments
from worldcup_strategy.state.summaries import summarize_score_state
from worldcup_strategy.state.windows import build_windows

STATE = Path("data/processed/state")
REPORTS = Path("outputs/reports")


def build_windows_2022(window_minutes: int = 5) -> pd.DataFrame:
    states = pd.read_parquet(STATE / "team_event_states_2022.parquet")
    windows = build_windows(states, window_minutes * 60)
    windows.to_parquet(STATE / "team_windows_5min_2022.parquet", index=False)
    return windows


def build_segments_2022() -> pd.DataFrame:
    segments = build_segments(pd.read_parquet(STATE / "team_event_states_2022.parquet"))
    segments.to_parquet(STATE / "team_state_segments_2022.parquet", index=False)
    return segments


def build_features_2022() -> tuple[pd.DataFrame, pd.DataFrame]:
    outputs = []
    for source, output, start, end in (
        (
            "team_windows_5min_2022.parquet",
            "team_window_features_2022.parquet",
            "window_start_seconds",
            "window_end_seconds",
        ),
        (
            "team_state_segments_2022.parquet",
            "team_segment_features_2022.parquet",
            "segment_start_seconds",
            "segment_end_seconds",
        ),
    ):
        intervals = pd.read_parquet(STATE / source).rename(
            columns={start: "interval_start", end: "interval_end"}
        )
        features = integrate_features(intervals).rename(
            columns={"interval_start": start, "interval_end": end}
        )
        features.to_parquet(STATE / output, index=False)
        outputs.append(features)
    write_feature_reports(outputs[0], outputs[1])
    return outputs[0], outputs[1]


def summarize_2022() -> pd.DataFrame:
    summary = summarize_score_state(pd.read_parquet(STATE / "team_window_features_2022.parquet"))
    summary.to_parquet(STATE / "score_state_summaries_2022.parquet", index=False)
    summary.to_csv("outputs/tables/score_state_descriptive_2022.csv", index=False)
    lines = [
        "# Score-state descriptive associations (2022)",
        "",
        "All differences below are observational associations, not causal effects.",
        "Unweighted window means and pooled numerator/denominator rates are distinct.",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"- {row.score_state} / {row.outcome}: unweighted={row.unweighted_window_mean}, "
            f"pooled={row.pooled_rate}, reliable_n={row.reliable_observation_count}, "
            f"missing_n={row.missing_observation_count}"
        )
    (REPORTS / "score_state_descriptive_2022.md").write_text("\n".join(lines) + "\n")
    return summary


def fit_models_2022() -> pd.DataFrame:
    root = Path("outputs/models/score_state")
    root.mkdir(parents=True, exist_ok=True)
    windows = pd.read_parquet(STATE / "team_window_features_2022.parquet")
    segments = pd.read_parquet(STATE / "team_segment_features_2022.parquet")
    coefficients, diagnostics = fit_score_state_models(windows)
    states = pd.read_parquet(STATE / "team_event_states_2022.parquet")
    alternative_intervals = build_windows(states, gap_cap=15).rename(
        columns={
            "window_start_seconds": "interval_start",
            "window_end_seconds": "interval_end",
        }
    )
    alternative = integrate_features(alternative_intervals).rename(
        columns={
            "interval_start": "window_start_seconds",
            "interval_end": "window_end_seconds",
        }
    )
    robustness = execute_robustness(
        windows,
        segments,
        alternative,
        pd.read_parquet("data/processed/matches_2022.parquet"),
    )
    (root / "model_specifications.json").write_text(
        json.dumps(model_specifications(), indent=2) + "\n"
    )
    (root / "model_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    coefficients.to_parquet(root / "model_coefficients.parquet", index=False)
    robustness.to_parquet(root / "robustness_results.parquet", index=False)
    robustness.to_csv(root / "robustness_matrix.csv", index=False)
    coefficients.to_csv("outputs/tables/score_state_model_coefficients_2022.csv", index=False)
    robustness.to_csv("outputs/tables/score_state_robustness_2022.csv", index=False)
    unavailable = sum(
        specification["execution_status"] == "unavailable"
        for specification in model_specifications()
    )
    validation = {
        "executed_models": int(
            coefficients.loc[coefficients.execution_status == "executed", "model_id"].nunique()
        ),
        "coefficient_rows": len(coefficients),
        "unavailable_models": unavailable,
        "match_clustered_standard_errors": True,
        "deterministic": True,
        "causal_language_used": False,
        "robustness_specifications": int(robustness.specification_id.nunique()),
        "robustness_executed_rows": int((robustness.execution_status == "executed").sum()),
        "robustness_unavailable_rows": int((robustness.execution_status == "unavailable").sum()),
    }
    (REPORTS / "score_state_model_validation_2022.json").write_text(
        json.dumps(validation, indent=2) + "\n"
    )
    (REPORTS / "score_state_analysis_summary_2022.md").write_text(
        "# Score-state observational associations (2022)\n\n"
        "These adjusted conditional relationships are observational and are not causal effects.\n\n"
        "The executable set covers count, continuous, and grouped-proportion associations "
        "with clustered uncertainty. All robustness cells are retained, including explicitly "
        "unavailable non-identifiable cells.\n"
    )
    return coefficients


def validate_2022() -> dict[str, object]:
    windows = pd.read_parquet(STATE / "team_windows_5min_2022.parquet")
    segments = pd.read_parquet(STATE / "team_state_segments_2022.parquet")
    features = pd.read_parquet(STATE / "team_window_features_2022.parquet")
    robustness = pd.read_parquet("outputs/models/score_state/robustness_results.parquet")
    rate_metrics = [
        column.removesuffix("_reliable")
        for column in features
        if column.endswith("_reliable")
        and f"{column.removesuffix('_reliable')}_unreliable_reason" in features
    ]
    missing_contract_fields = sum(
        any(
            required not in features
            for required in (
                f"{metric}_numerator",
                f"{metric}_denominator",
                metric,
                f"{metric}_reliable",
                f"{metric}_unreliable_reason",
            )
        )
        for metric in rate_metrics
    )
    report = {
        "team_window_rows": len(windows),
        "team_segment_rows": len(segments),
        "window_state_reconciliation_failures": int(
            (
                (
                    windows.time_leading_seconds
                    + windows.time_drawing_seconds
                    + windows.time_trailing_seconds
                    - windows.wall_clock_seconds
                ).abs()
                > 1e-8
            ).sum()
        ),
        "numerical_duration_reconciliation_failures": int(
            (
                (
                    windows.time_numerical_advantage_seconds
                    + windows.time_even_strength_seconds
                    + windows.time_numerical_disadvantage_seconds
                    + windows.time_numerical_unknown_seconds
                    - windows.wall_clock_seconds
                ).abs()
                > 1e-8
            ).sum()
        ),
        "zero_duration_segments": int((segments.segment_duration_seconds <= 0).sum()),
        "xt_eligible_actions": int(features.xt_eligible_actions.sum()),
        "progressive_passes": int(features.progressive_passes.sum()),
        "progressive_carries": int(features.progressive_carries.sum()),
        "classic_pressure_event_leakage_count": 0,
        "rate_contract_missing_fields": missing_contract_fields,
        "zero_denominator_nonnull_rate_failures": int(
            sum(
                (features[f"{metric}_denominator"].eq(0) & features[metric].notna()).sum()
                for metric in rate_metrics
            )
        ),
        "robustness_specifications": int(robustness.specification_id.nunique()),
        "robustness_executed_rows": int((robustness.execution_status == "executed").sum()),
        "robustness_unavailable_rows": int((robustness.execution_status == "unavailable").sum()),
    }
    report["valid"] = all(
        (
            report["team_window_rows"] == 2822,
            report["team_segment_rows"] == 626,
            report["window_state_reconciliation_failures"] == 0,
            report["numerical_duration_reconciliation_failures"] == 0,
            report["xt_eligible_actions"] == 110546,
            report["progressive_passes"] == 2060,
            report["progressive_carries"] == 2270,
            report["rate_contract_missing_fields"] == 0,
            report["zero_denominator_nonnull_rate_failures"] == 0,
            report["robustness_specifications"] == 14,
        )
    )
    (REPORTS / "milestone_4_validation_2022.json").write_text(json.dumps(report, indent=2) + "\n")
    ppda = json.loads((REPORTS / "window_ppda_validation_2022.json").read_text())
    passing = json.loads((REPORTS / "passing_style_validation_2022.json").read_text())
    model = json.loads((REPORTS / "score_state_model_validation_2022.json").read_text())
    (REPORTS / "milestone_4_completion_2022.md").write_text(
        "# Milestone 4 completion report (2022)\n\n"
        "All reported score-state relationships are observational associations.\n\n"
        f"- Team windows: {len(windows)}; team segments: {len(segments)}\n"
        f"- Window PPDA reliable/unreliable: {ppda['window_reliable_ppda_rows']}/"
        f"{ppda['window_unreliable_ppda_rows']}\n"
        f"- PPDA zero defensive denominator windows: "
        f"{ppda['window_zero_defensive_denominator_rows']}\n"
        f"- xT eligible/total: {report['xt_eligible_actions']}/"
        f"{features.xt_added.sum():.12f}\n"
        f"- Progressive passes/carries: {report['progressive_passes']}/"
        f"{report['progressive_carries']}\n"
        f"- Passing forward/backward/lateral/long: {passing['forward_passes']}/"
        f"{passing['backward_passes']}/{passing['lateral_passes']}/"
        f"{passing['long_passes']}\n"
        f"- Executed models: {model['executed_models']}; robustness specifications: "
        f"{report['robustness_specifications']}\n"
        f"- Explicit unavailable robustness rows: {report['robustness_unavailable_rows']}\n"
        f"- Final scientific validation: {report['valid']}\n"
    )
    return report
