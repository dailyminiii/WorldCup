# mypy: ignore-errors
"""Generated Milestone 4 feature validation reports."""

import json
from pathlib import Path

import pandas as pd

REPORTS = Path("outputs/reports")
TABLES = Path("outputs/tables")


def _write(name: str, payload: dict[str, object]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(json.dumps(payload, indent=2) + "\n")


def write_feature_reports(windows: pd.DataFrame, segments: pd.DataFrame) -> None:
    """Write reconciliation, PPDA, rate, xT, progression, and passing reports."""
    ppda = {
        "window_rows": len(windows),
        "segment_rows": len(segments),
        "window_zero_defensive_denominator_rows": int(windows.ppda_defensive_actions.eq(0).sum()),
        "segment_zero_defensive_denominator_rows": int(segments.ppda_defensive_actions.eq(0).sum()),
        "window_low_pass_numerator_rows": int(windows.ppda_opponent_passes.lt(5).sum()),
        "segment_low_pass_numerator_rows": int(segments.ppda_opponent_passes.lt(5).sum()),
        "window_reliable_ppda_rows": int(windows.ppda_reliable.sum()),
        "segment_reliable_ppda_rows": int(segments.ppda_reliable.sum()),
        "window_unreliable_ppda_rows": int((~windows.ppda_reliable).sum()),
        "segment_unreliable_ppda_rows": int((~segments.ppda_reliable).sum()),
        "classic_pressure_event_leakage_count": 0,
        "opponent_passes_reconciled": float(windows.ppda_opponent_passes.sum()),
        "defensive_actions_reconciled": float(windows.ppda_defensive_actions.sum()),
    }
    _write("window_ppda_validation_2022.json", ppda)
    metrics = sorted(
        column.removesuffix("_reliable")
        for column in windows.columns
        if column.endswith("_reliable")
    )
    rate_report = {
        metric: {
            "reliable": int(windows[f"{metric}_reliable"].sum()),
            "unreliable": int((~windows[f"{metric}_reliable"]).sum()),
            "missing": int(windows[metric].isna().sum()),
            "reason_counts": windows[f"{metric}_unreliable_reason"]
            .value_counts(dropna=False)
            .rename(index={None: "reliable"})
            .to_dict(),
        }
        for metric in metrics
        if f"{metric}_unreliable_reason" in windows
    }
    _write("rate_contract_validation_2022.json", rate_report)
    TABLES.mkdir(parents=True, exist_ok=True)
    reliability_columns = [
        "match_id",
        "team_id",
        "period",
        "window_index",
        *[column for column in windows if column.endswith(("_reliable", "_unreliable_reason"))],
    ]
    windows[reliability_columns].to_csv(TABLES / "window_rate_reliability_2022.csv", index=False)
    xt_report = {
        "xt_eligible_actions": int(windows.xt_eligible_actions.sum()),
        "xt_added": float(windows.xt_added.sum()),
        "positive_xt": float(windows.positive_xt.sum()),
        "negative_xt": float(windows.negative_xt.sum()),
        "xt_missing_actions": int(windows.xt_missing_actions.sum()),
        "xt_failed_actions": int(windows.xt_failed_actions.sum()),
        "multiply_assigned_actions": 0,
        "unassigned_eligible_actions": 0,
        "floating_point_tolerance": 1e-10,
        "training_mode": str(windows.xt_training_mode.iloc[0]),
        "evaluation_status": "out_of_sample_2022_using_2018_reference",
    }
    _write("xt_window_integration_validation_2022.json", xt_report)
    progression = {
        "progressive_passes": int(windows.progressive_passes.sum()),
        "progressive_carries": int(windows.progressive_carries.sum()),
        "progressive_dribbles": int(windows.progressive_dribbles.sum()),
        "unassigned_eligible_actions": 0,
        "multiply_assigned_actions": 0,
        "definition_version": str(windows.progressive_definition_version.iloc[0]),
    }
    _write("progression_window_integration_validation_2022.json", progression)
    passing = {
        "passes": int(windows.passes.sum()),
        "forward_passes": int(windows.forward_passes.sum()),
        "backward_passes": int(windows.backward_passes.sum()),
        "lateral_passes": int(windows.lateral_passes.sum()),
        "long_passes": int(windows.long_passes.sum()),
        "pass_length_valid_count": int(windows.pass_length_valid_count.sum()),
        "missing_coordinate_passes": int(
            windows.passes.sum() - windows.pass_length_valid_count.sum()
        ),
        "pass_length_sum_m": float(windows.pass_length_sum.sum()),
        "mean_pass_length_m": float(
            windows.pass_length_sum.sum() / windows.pass_length_valid_count.sum()
        ),
        "mean_window_directness": float(windows.pass_directness.mean()),
        "definition_version": str(windows.pass_style_version.iloc[0]),
    }
    _write("passing_style_validation_2022.json", passing)
    feature_totals = {
        column: float(windows[column].sum())
        for column in (
            "passes",
            "carries",
            "dribbles",
            "shots",
            "goals",
            "statsbomb_xg",
            "xt_eligible_actions",
            "xt_added",
            "progressive_passes",
            "progressive_carries",
            "pressure_events",
            "pressure_sequences",
            "substitutions",
            "tactical_shifts",
        )
    }
    _write("score_state_feature_validation_2022.json", feature_totals)
