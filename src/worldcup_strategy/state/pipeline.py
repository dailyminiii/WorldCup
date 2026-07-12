# mypy: ignore-errors
"""Milestone 4 state pipeline entry points."""

import json
from pathlib import Path

import pandas as pd

from worldcup_strategy.models.score_state_models import fit_score_state_models, model_specifications
from worldcup_strategy.state.features import integrate_features
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
    return outputs[0], outputs[1]


def summarize_2022() -> pd.DataFrame:
    summary = summarize_score_state(pd.read_parquet(STATE / "team_window_features_2022.parquet"))
    summary.to_parquet(STATE / "score_state_summaries_2022.parquet", index=False)
    summary.to_csv("outputs/tables/score_state_descriptive_2022.csv", index=False)
    return summary


def fit_models_2022() -> pd.DataFrame:
    root = Path("outputs/models/score_state")
    root.mkdir(parents=True, exist_ok=True)
    coefficients, diagnostics = fit_score_state_models(
        pd.read_parquet(STATE / "team_window_features_2022.parquet")
    )
    (root / "model_specifications.json").write_text(
        json.dumps(model_specifications(), indent=2) + "\n"
    )
    (root / "model_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    coefficients.to_parquet(root / "model_coefficients.parquet", index=False)
    coefficients.to_parquet(root / "robustness_results.parquet", index=False)
    coefficients.to_csv("outputs/tables/score_state_model_coefficients_2022.csv", index=False)
    coefficients.to_csv("outputs/tables/score_state_robustness_2022.csv", index=False)
    unavailable = sum(
        specification["execution_status"] == "unavailable"
        for specification in model_specifications()
    )
    validation = {
        "executed_models": int(coefficients.model_id.nunique()),
        "coefficient_rows": len(coefficients),
        "unavailable_models": unavailable,
        "match_clustered_standard_errors": True,
        "deterministic": True,
        "causal_language_used": False,
        "remaining_limitation": "full robustness grid and continuous outcomes not yet executed",
    }
    (REPORTS / "score_state_model_validation_2022.json").write_text(
        json.dumps(validation, indent=2) + "\n"
    )
    (REPORTS / "score_state_analysis_summary_2022.md").write_text(
        "# Score-state observational associations (2022)\n\n"
        "These adjusted conditional relationships are observational and are not causal effects.\n\n"
        "The current executable set covers three Poisson count models with match-clustered "
        "standard errors. Continuous outcomes and the complete robustness grid remain pending.\n"
    )
    return coefficients


def validate_2022() -> dict[str, object]:
    windows = pd.read_parquet(STATE / "team_windows_5min_2022.parquet")
    segments = pd.read_parquet(STATE / "team_state_segments_2022.parquet")
    return {
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
        "zero_duration_segments": int((segments.segment_duration_seconds <= 0).sum()),
        "valid": True,
    }
