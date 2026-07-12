"""Regression checks over tracked Milestone 4 analytical outputs."""

from pathlib import Path

import pandas as pd


def test_robustness_matrix_preserves_all_specs_and_unavailable_cells() -> None:
    matrix = pd.read_csv("outputs/models/score_state/robustness_matrix.csv")
    assert matrix.specification_id.nunique() == 14
    assert {"executed", "unavailable"}.issubset(set(matrix.execution_status))
    match = matrix[matrix.specification_id == "match_fixed_effects"]
    assert (match.execution_status == "executed").sum() == 26
    raw_non_count = matrix[
        (matrix.specification_id == "raw_count_models_with_offsets")
        & ~matrix.model_id.isin(
            ["primary_shots", "primary_pressure_events", "primary_pressure_regains_5s"]
        )
    ]
    assert not (raw_non_count.execution_status == "executed").any()


def test_generated_analysis_reports_do_not_make_causal_claims() -> None:
    reports = (
        Path("outputs/reports/score_state_analysis_summary_2022.md"),
        Path("outputs/reports/score_state_descriptive_2022.md"),
        Path("outputs/reports/milestone_4_completion_2022.md"),
    )
    prohibited = (" causes ", " caused by ", " causal effect of ", " leads to ")
    combined = "\n".join(path.read_text().lower() for path in reports)
    assert not any(phrase in combined for phrase in prohibited)
