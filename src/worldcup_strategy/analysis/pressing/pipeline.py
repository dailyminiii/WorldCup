# mypy: ignore-errors
"""Deterministic pipeline for the locked pressing score-state study."""

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from worldcup_strategy.analysis.pressing.describe import (
    descriptive_by_state,
    sample_characteristics,
)
from worldcup_strategy.analysis.pressing.models import (
    fit_continuous,
    fit_efficiency,
    fit_intensity,
    holm_adjust,
)
from worldcup_strategy.analysis.pressing.prepare import (
    ANALYSIS,
    MODEL_ROOT,
    TABLES,
    prepare_analysis,
)
from worldcup_strategy.analysis.pressing.robustness import SPECIFICATION_GROUPS, execute_robustness

REPORTS = Path("outputs/reports")
FIGURES = Path("outputs/figures/pressing_score_state")
PLAN_COMMIT = "361534c"


def _read_windows() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS / "pressing_primary_windows_2022.parquet")


def _read_segments() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS / "pressing_primary_segments_2022.parquet")


def prepare() -> pd.DataFrame:
    windows, _, _ = prepare_analysis()
    return windows


def describe() -> tuple[pd.DataFrame, pd.DataFrame]:
    windows = _read_windows()
    descriptive = descriptive_by_state(windows)
    characteristics = sample_characteristics(windows)
    descriptive.to_csv(TABLES / "pressing_descriptive_by_score_state_2022.csv", index=False)
    characteristics.to_csv(TABLES / "pressing_sample_characteristics_2022.csv", index=False)
    return descriptive, characteristics


def _prediction_contrasts(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _model_id, group in predictions.groupby("model_id"):
        drawing = float(group.loc[group.score_state == "drawing", "predicted_value"].iloc[0])
        for row in group.itertuples(index=False):
            record = row._asdict()
            if row.scale == "probability":
                record["adjusted_difference_from_drawing"] = row.predicted_value - drawing
                record["adjusted_percentage_difference_from_drawing"] = None
            else:
                record["adjusted_difference_from_drawing"] = row.predicted_value - drawing
                record["adjusted_percentage_difference_from_drawing"] = (
                    (row.predicted_value / drawing - 1) * 100 if drawing else None
                )
            rows.append(record)
    return pd.DataFrame(rows)


def fit_primary() -> tuple[pd.DataFrame, pd.DataFrame]:
    windows = _read_windows()
    intensity, intensity_predictions, intensity_diagnostics = fit_intensity(windows)
    efficiency, efficiency_predictions, efficiency_diagnostics = fit_efficiency(windows)
    coefficients = pd.concat([intensity, efficiency], ignore_index=True)
    predictions = _prediction_contrasts(
        pd.concat([intensity_predictions, efficiency_predictions], ignore_index=True)
    )
    multiplicity = holm_adjust(coefficients)
    coefficients.to_parquet(MODEL_ROOT / "primary_model_coefficients.parquet", index=False)
    coefficients.to_csv(TABLES / "pressing_primary_models_2022.csv", index=False)
    predictions.to_csv(TABLES / "pressing_adjusted_predictions_2022.csv", index=False)
    (MODEL_ROOT / "multiplicity_adjustment.json").write_text(
        json.dumps(multiplicity.to_dict("records"), indent=2) + "\n"
    )
    diagnostics = {
        intensity_diagnostics["model_id"]: intensity_diagnostics,
        efficiency_diagnostics["model_id"]: efficiency_diagnostics,
    }
    (MODEL_ROOT / "model_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    return coefficients, predictions


def fit_secondary() -> pd.DataFrame:
    windows = _read_windows()
    tables = []
    diagnostics_path = MODEL_ROOT / "model_diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text()) if diagnostics_path.exists() else {}
    specifications = [
        ("secondary_high_pressure_share", "high_pressure_events", "pressure_events", 3),
        ("secondary_event_regain_5s", "pressure_regains_5s", "pressure_events", 3),
        ("secondary_counterpress_share", "counterpress_events", "pressure_events", 3),
        ("secondary_high_regain_rate", "high_regains", "pressure_regains_5s", 1),
        (
            "secondary_post_regain_shot_10s",
            "shots_after_pressure_regain_10s",
            "pressure_regains_5s",
            1,
        ),
    ]
    for model_id, successes, trials, minimum in specifications:
        table, _, diagnostic = fit_efficiency(
            windows,
            successes_column=successes,
            trials_column=trials,
            minimum_trials=minimum,
            model_id=model_id,
            analysis_role="secondary" if "post_regain" not in model_id else "exploratory",
        )
        tables.append(table)
        diagnostics[model_id] = diagnostic
    for model_id, outcome, exposure, minimum in (
        ("secondary_pressure_sequence_frequency", "pressure_sequences", "opponent_possessions", 1),
        (
            "secondary_classic_defensive_action_rate",
            "ppda_defensive_actions",
            "ppda_opponent_passes",
            5,
        ),
    ):
        table, _, diagnostic = fit_intensity(
            windows,
            outcome_column=outcome,
            exposure_column=exposure,
            minimum_passes=minimum,
            model_id=model_id,
        )
        table["analysis_role"] = "secondary"
        tables.append(table)
        diagnostics[model_id] = diagnostic
    windows = windows.copy()
    for source, target in (
        ("xg_after_pressure_regains", "post_regain_xg_per_success"),
        ("xt_after_pressure_regains", "post_regain_xt_per_success"),
    ):
        windows[target] = windows[source] / windows.pressure_regains_5s.where(
            windows.pressure_regains_5s > 0
        )
        table, diagnostic = fit_continuous(
            windows,
            target,
            windows.common_primary_eligible & windows.pressure_regains_5s.ge(1),
            f"exploratory_{target}",
            analysis_role="exploratory",
        )
        tables.append(table)
        diagnostics[f"exploratory_{target}"] = diagnostic
    for outcome in ("mean_pressure_height",):
        table, diagnostic = fit_continuous(
            windows,
            outcome,
            windows.common_primary_eligible & windows.pressure_events.ge(3),
            f"secondary_{outcome}",
        )
        tables.append(table)
        diagnostics[f"secondary_{outcome}"] = diagnostic
    unavailable = pd.DataFrame(
        [
            {
                "model_id": "exploratory_same_possession_goal_after_regain",
                "analysis_role": "exploratory",
                "outcome": "same_possession_goal",
                "model_family": "grouped_binomial_logit",
                "execution_status": "unavailable",
                "unavailable_reason": "goal_indicator_not_available_in_high_regain_table",
                "reference_category": "drawing",
            },
            {
                "model_id": "sensitivity_pressure_augmented_ppda",
                "analysis_role": "sensitivity",
                "outcome": "pressure_augmented_ppda",
                "model_family": "not_primary_or_secondary",
                "execution_status": "unavailable",
                "unavailable_reason": "provider_specific_metric_excluded_from_inferential_scope",
                "reference_category": "drawing",
            },
        ]
    )
    output = pd.concat([*tables, unavailable], ignore_index=True, sort=False)
    output.to_parquet(MODEL_ROOT / "secondary_model_coefficients.parquet", index=False)
    output.to_csv(TABLES / "pressing_secondary_models_2022.csv", index=False)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    return output


def robustness() -> pd.DataFrame:
    results = execute_robustness(_read_windows(), _read_segments())
    results.to_parquet(MODEL_ROOT / "robustness_results.parquet", index=False)
    results.to_csv(TABLES / "pressing_robustness_2022.csv", index=False)
    diagnostics_path = MODEL_ROOT / "model_diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text()) if diagnostics_path.exists() else {}
    for (group, specification, model), rows in results.groupby(
        ["specification_group", "specification_id", "model_id"], dropna=False
    ):
        first = rows.iloc[0]
        key = f"robustness::{group}::{specification}::{model}"
        diagnostics[key] = {
            "model_id": model,
            "specification_group": group,
            "specification_id": specification,
            "observations": int(first.sample_size),
            "teams": int(first.team_count),
            "matches": int(first.match_count),
            "outcome_total": None,
            "exposure_total": None,
            "zero_outcome_proportion": None,
            "overdispersion": None,
            "separation": None,
            "collinearity_warning": None,
            "influential_observation_warning": None,
            "convergence": first.convergence_status == "converged",
            "covariance_estimator": (
                "cluster_robust:team_id"
                if group == "team_clustered_uncertainty"
                else "cluster_robust:match_id"
            ),
            "fixed_effect_rank": None,
            "dropped_terms": [],
            "missing_data_exclusions": None,
            "execution_status": first.execution_status,
            "diagnostic_limitation": "grid_summary_fields_not_recomputed",
        }
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    return results


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(commands: list[str]) -> dict[str, object]:
    inputs = [
        Path("data/processed/state/team_window_features_2022.parquet"),
        Path("data/processed/state/team_segment_features_2022.parquet"),
        Path("data/processed/pressure/pressure_events_2022.parquet"),
        Path("data/processed/pressure/high_regains_2022.parquet"),
        Path("configs/pressing_score_state_analysis.yaml"),
    ]
    outputs = sorted(
        [
            *MODEL_ROOT.glob("*"),
            *TABLES.glob("pressing_*"),
            *FIGURES.glob("*"),
            *Path("paper/pressing_score_state").glob("*.md"),
            Path("PRESSING_SCORE_STATE_ANALYSIS_REPORT.md"),
            REPORTS / "pressing_score_state_validation_2022.json",
            REPORTS / "pressing_score_state_independent_audit.json",
        ],
        key=lambda path: str(path),
    )
    outputs = [path for path in outputs if path.name != "analysis_manifest.json"]
    source = json.loads(Path("data/manifests/source.json").read_text())
    manifest = {
        "analysis_plan_commit": PLAN_COMMIT,
        "data_source_commit": source.get("source_commit_sha"),
        "repository_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "input_checksums": {str(path): _sha256(path) for path in inputs},
        "configuration_hash": _sha256(Path("configs/pressing_score_state_analysis.yaml")),
        "model_versions": {
            "intensity": "poisson_cluster_robust_v1",
            "efficiency": "grouped_binomial_cluster_robust_v1",
        },
        "random_seeds": {"analysis_seed": 20220713},
        "commands_executed": commands,
        "output_checksums": {str(path): _sha256(path) for path in outputs if path.is_file()},
    }
    (MODEL_ROOT / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def validate() -> dict[str, object]:
    windows = _read_windows()
    primary = pd.read_parquet(MODEL_ROOT / "primary_model_coefficients.parquet")
    secondary = pd.read_parquet(MODEL_ROOT / "secondary_model_coefficients.parquet")
    robust = pd.read_parquet(MODEL_ROOT / "robustness_results.parquet")
    report = {
        "analysis_plan_commit": PLAN_COMMIT,
        "initial_windows": len(windows),
        "primary_model_ids": sorted(primary.model_id.unique().tolist()),
        "both_primary_contrasts_present": all(
            set(group.coefficient_name) == {"score_state[leading]", "score_state[trailing]"}
            for _, group in primary.groupby("model_id")
        ),
        "sequence_success_above_trials": int(
            (windows.sequence_regains_5s > windows.pressure_sequences).sum()
        ),
        "robustness_specification_groups": int(robust.specification_group.nunique()),
        "missing_robustness_groups": sorted(
            set(SPECIFICATION_GROUPS) - set(robust.specification_group)
        ),
        "unavailable_secondary_models": int((secondary.execution_status == "unavailable").sum()),
        "reference_categories": sorted(primary.reference_category.dropna().unique().tolist()),
    }
    report["valid"] = all(
        (
            report["initial_windows"] == 2822,
            report["both_primary_contrasts_present"],
            report["sequence_success_above_trials"] == 0,
            report["robustness_specification_groups"] >= 16,
            not report["missing_robustness_groups"],
            report["reference_categories"] == ["drawing"],
        )
    )
    (REPORTS / "pressing_score_state_validation_2022.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    return report
