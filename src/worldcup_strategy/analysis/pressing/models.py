# mypy: ignore-errors
"""Locked pressing score-state models, predictions, and diagnostics."""

import math
from typing import Any

import numpy as np
import pandas as pd

from worldcup_strategy.models.continuous_models import fit_clustered_ols
from worldcup_strategy.models.count_models import fit_binomial, fit_negative_binomial, fit_poisson
from worldcup_strategy.models.diagnostics import overdispersion

CONTRASTS = ("score_state[leading]", "score_state[trailing]")


def _normal_p_value(coefficient: float, standard_error: float) -> float | None:
    if not np.isfinite(standard_error) or standard_error <= 0:
        return None
    z = abs(coefficient / standard_error)
    return math.erfc(z / math.sqrt(2))


def design_matrix(
    frame: pd.DataFrame,
    *,
    include_match_effects: bool = False,
    exact_goal_difference: bool = False,
) -> tuple[np.ndarray, list[str]]:
    """Create the locked design with drawing and reference categories omitted."""
    columns: list[np.ndarray] = [np.ones(len(frame))]
    names = ["intercept"]
    if exact_goal_difference:
        columns.append(frame.goal_difference_start.to_numpy(float))
        names.append("goal_difference")
    else:
        columns.extend(
            [
                frame.score_state_majority.eq("leading").to_numpy(float),
                frame.score_state_majority.eq("trailing").to_numpy(float),
            ]
        )
        names.extend(CONTRASTS)
    columns.extend(
        [
            frame.match_minute_centered.to_numpy(float) / 45,
            frame.match_minute_centered_squared.to_numpy(float) / (45**2),
        ]
    )
    names.extend(["match_minute_centered", "match_minute_centered_squared"])
    for stage in sorted(frame.competition_stage.dropna().unique())[1:]:
        columns.append(frame.competition_stage.eq(stage).to_numpy(float))
        names.append(f"competition_stage[{stage}]")
    for matchday in sorted(frame.group_matchday.dropna().unique())[1:]:
        columns.append(frame.group_matchday.eq(matchday).to_numpy(float))
        names.append(f"group_matchday[{matchday}]")
    for team in sorted(frame.team_id.unique())[1:]:
        columns.append(frame.team_id.eq(team).to_numpy(float))
        names.append(f"team[{team}]")
    if include_match_effects:
        for match in sorted(frame.match_id.unique())[1:]:
            columns.append(frame.match_id.eq(match).to_numpy(float))
            names.append(f"match[{match}]")
    design = np.column_stack(columns)
    keep = [0, *[i for i in range(1, design.shape[1]) if np.ptp(design[:, i]) > 0]]
    return design[:, keep], [names[i] for i in keep]


def _marginal_prediction(
    design: np.ndarray,
    names: list[str],
    coefficients: np.ndarray,
    covariance: np.ndarray,
    state: str,
    family: str,
    multiplier: float = 1.0,
) -> tuple[float, float, float]:
    modified = design.copy()
    for contrast in CONTRASTS:
        if contrast in names:
            modified[:, names.index(contrast)] = float(contrast == f"score_state[{state}]")
    eta = modified @ coefficients
    if family == "poisson":
        values = np.exp(np.clip(eta, -20, 20)) * multiplier
        gradients = values[:, None] * modified
    else:
        probabilities = 1 / (1 + np.exp(-np.clip(eta, -20, 20)))
        values = probabilities
        gradients = (probabilities * (1 - probabilities))[:, None] * modified
    estimate = float(values.mean())
    gradient = gradients.mean(axis=0)
    standard_error = float(np.sqrt(max(0.0, gradient @ covariance @ gradient)))
    lower = max(0.0, estimate - 1.96 * standard_error)
    upper = estimate + 1.96 * standard_error
    if family != "poisson":
        upper = min(1.0, upper)
    return estimate, lower, upper


def _base_diagnostics(
    data: pd.DataFrame,
    outcome: np.ndarray,
    exposure: np.ndarray,
    design: np.ndarray,
    fitted: np.ndarray,
    converged: bool,
    covariance_estimator: str,
) -> dict[str, Any]:
    residual = outcome - fitted
    scale = np.sqrt(np.maximum(fitted, 1e-12))
    return {
        "observations": len(data),
        "teams": int(data.team_id.nunique()),
        "matches": int(data.match_id.nunique()),
        "outcome_total": float(outcome.sum()),
        "exposure_total": float(exposure.sum()),
        "zero_outcome_proportion": float(np.mean(outcome == 0)),
        "fixed_effect_rank": int(np.linalg.matrix_rank(design)),
        "design_columns": int(design.shape[1]),
        "collinearity_warning": bool(np.linalg.matrix_rank(design) < design.shape[1]),
        "maximum_absolute_pearson_residual": float(np.max(np.abs(residual / scale))),
        "influential_observation_warning": bool(np.max(np.abs(residual / scale)) > 4),
        "convergence": bool(converged),
        "covariance_estimator": covariance_estimator,
        "dropped_terms": [],
    }


def fit_intensity(
    frame: pd.DataFrame,
    *,
    minimum_passes: int = 5,
    exposure_column: str = "opponent_passes",
    cluster_variable: str = "match_id",
    include_match_effects: bool = False,
    exact_goal_difference: bool = False,
    model_id: str = "primary_pressing_intensity",
    outcome_column: str = "pressure_events",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit the locked Pressure-event count model."""
    eligible = (
        frame.common_primary_eligible
        & frame[exposure_column].notna()
        & frame[exposure_column].ge(minimum_passes)
    )
    data = frame.loc[eligible].copy()
    design, names = design_matrix(
        data,
        include_match_effects=include_match_effects,
        exact_goal_difference=exact_goal_difference,
    )
    outcome = data[outcome_column].to_numpy(float)
    exposure = data[exposure_column].to_numpy(float)
    fit = fit_poisson(
        outcome,
        design,
        np.log(exposure),
        data[cluster_variable].to_numpy(),
    )
    dispersion = overdispersion(outcome, fit["fitted"], design.shape[1])
    rows = []
    coefficient_names = ["goal_difference"] if exact_goal_difference else list(CONTRASTS)
    for name in coefficient_names:
        if name not in names:
            continue
        index = names.index(name)
        coefficient = float(fit["coefficient"][index])
        standard_error = float(fit["standard_error"][index])
        rows.append(
            {
                "model_id": model_id,
                "analysis_role": "primary"
                if model_id == "primary_pressing_intensity"
                else "robustness",
                "outcome": outcome_column,
                "model_family": "poisson",
                "coefficient_name": name,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "confidence_interval_lower": coefficient - 1.96 * standard_error,
                "confidence_interval_upper": coefficient + 1.96 * standard_error,
                "p_value": _normal_p_value(coefficient, standard_error),
                "incidence_rate_ratio": math.exp(coefficient),
                "odds_ratio": None,
                "sample_size": len(data),
                "match_count": data.match_id.nunique(),
                "team_count": data.team_id.nunique(),
                "outcome_total": int(outcome.sum()),
                "exposure_total": float(exposure.sum()),
                "offset": f"log({exposure_column})",
                "reference_category": "drawing" if not exact_goal_difference else None,
                "fixed_effects": "team_id + match_id" if include_match_effects else "team_id",
                "cluster_variable": cluster_variable,
                "convergence_status": "converged" if fit["converged"] else "warning",
                "execution_status": "executed",
                "warning_flags": "overdispersion" if dispersion and dispersion > 1.5 else "",
                "unavailable_reason": None,
            }
        )
    predictions = []
    if not exact_goal_difference:
        for state in ("leading", "drawing", "trailing"):
            estimate, lower, upper = _marginal_prediction(
                design,
                names,
                fit["coefficient"],
                fit["covariance"],
                state,
                "poisson",
                30,
            )
            predictions.append(
                {
                    "model_id": model_id,
                    "score_state": state,
                    "predicted_value": estimate,
                    "confidence_interval_lower": lower,
                    "confidence_interval_upper": upper,
                    "scale": "pressure_events_per_30_exposure_units",
                }
            )
    diagnostics = _base_diagnostics(
        data,
        outcome,
        exposure,
        design,
        fit["fitted"],
        bool(fit["converged"]),
        f"cluster_robust:{cluster_variable}",
    )
    diagnostics.update(
        {
            "model_id": model_id,
            "overdispersion": dispersion,
            "missing_data_exclusions": int(len(frame) - len(data)),
            "minimum_denominator": minimum_passes,
            "exposure_column": exposure_column,
        }
    )
    return pd.DataFrame(rows), pd.DataFrame(predictions), diagnostics


def fit_negative_binomial_intensity(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit the preregistered NB2 robustness model when Poisson is overdispersed."""
    data = frame.loc[
        frame.common_primary_eligible & frame.opponent_passes.notna() & frame.opponent_passes.ge(5)
    ].copy()
    design, names = design_matrix(data)
    outcome = data.pressure_events.to_numpy(float)
    exposure = data.opponent_passes.to_numpy(float)
    poisson = fit_poisson(outcome, design, np.log(exposure), data.match_id.to_numpy())
    numerator = np.sum((outcome - poisson["fitted"]) ** 2 - poisson["fitted"])
    denominator = np.sum(np.asarray(poisson["fitted"]) ** 2)
    alpha = max(1e-8, float(numerator / denominator))
    fit = fit_negative_binomial(outcome, design, np.log(exposure), data.match_id.to_numpy(), alpha)
    rows = []
    for name in CONTRASTS:
        index = names.index(name)
        coefficient = float(fit["coefficient"][index])
        standard_error = float(fit["standard_error"][index])
        rows.append(
            {
                "model_id": "robust_intensity:negative_binomial",
                "analysis_role": "robustness",
                "outcome": "pressure_events",
                "model_family": "negative_binomial_nb2",
                "coefficient_name": name,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "confidence_interval_lower": coefficient - 1.96 * standard_error,
                "confidence_interval_upper": coefficient + 1.96 * standard_error,
                "p_value": _normal_p_value(coefficient, standard_error),
                "incidence_rate_ratio": math.exp(coefficient),
                "odds_ratio": None,
                "sample_size": len(data),
                "match_count": data.match_id.nunique(),
                "team_count": data.team_id.nunique(),
                "outcome_total": int(outcome.sum()),
                "exposure_total": float(exposure.sum()),
                "offset": "log(opponent_passes)",
                "reference_category": "drawing",
                "fixed_effects": "team_id",
                "cluster_variable": "match_id",
                "convergence_status": "converged" if fit["converged"] else "warning",
                "execution_status": "executed",
                "warning_flags": "",
                "unavailable_reason": None,
            }
        )
    diagnostics = {
        "model_id": "robust_intensity:negative_binomial",
        "observations": len(data),
        "matches": int(data.match_id.nunique()),
        "teams": int(data.team_id.nunique()),
        "alpha": alpha,
        "convergence": bool(fit["converged"]),
        "covariance_estimator": "cluster_robust:match_id",
    }
    return pd.DataFrame(rows), diagnostics


def fit_continuous(
    frame: pd.DataFrame,
    outcome_column: str,
    eligibility: pd.Series,
    model_id: str,
    *,
    cluster_variable: str = "match_id",
    analysis_role: str = "secondary",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit match-clustered OLS for zero-heavy opportunity-normalized secondary values."""
    data = frame.loc[eligibility & frame[outcome_column].notna()].copy()
    design, names = design_matrix(data)
    outcome = data[outcome_column].to_numpy(float)
    fit = fit_clustered_ols(outcome, design, data[cluster_variable].to_numpy())
    rows = []
    fitted = design @ fit["coefficient"]
    for name in CONTRASTS:
        if name not in names:
            continue
        index = names.index(name)
        coefficient = float(fit["coefficient"][index])
        standard_error = float(fit["standard_error"][index])
        rows.append(
            {
                "model_id": model_id,
                "analysis_role": analysis_role,
                "outcome": outcome_column,
                "model_family": "ols_clustered",
                "coefficient_name": name,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "confidence_interval_lower": coefficient - 1.96 * standard_error,
                "confidence_interval_upper": coefficient + 1.96 * standard_error,
                "p_value": _normal_p_value(coefficient, standard_error),
                "incidence_rate_ratio": None,
                "odds_ratio": None,
                "adjusted_difference": coefficient,
                "sample_size": len(data),
                "match_count": data.match_id.nunique(),
                "team_count": data.team_id.nunique(),
                "outcome_total": float(outcome.sum()),
                "exposure_total": len(data),
                "offset": None,
                "reference_category": "drawing",
                "fixed_effects": "team_id",
                "cluster_variable": cluster_variable,
                "convergence_status": "converged",
                "execution_status": "executed",
                "warning_flags": "zero_heavy" if float((outcome == 0).mean()) > 0.5 else "",
                "unavailable_reason": None,
            }
        )
    diagnostics = _base_diagnostics(
        data,
        outcome,
        np.ones(len(data)),
        design,
        fitted,
        True,
        f"cluster_robust:{cluster_variable}",
    )
    diagnostics.update(
        {
            "model_id": model_id,
            "overdispersion": None,
            "separation": None,
            "missing_data_exclusions": int(len(frame) - len(data)),
        }
    )
    return pd.DataFrame(rows), diagnostics


def fit_efficiency(
    frame: pd.DataFrame,
    *,
    successes_column: str = "sequence_regains_5s",
    trials_column: str = "pressure_sequences",
    minimum_trials: int = 3,
    cluster_variable: str = "match_id",
    include_match_effects: bool = False,
    exact_goal_difference: bool = False,
    model_id: str = "primary_sequence_regain_5s",
    analysis_role: str = "primary",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit a grouped-binomial Pressure-to-regain model."""
    valid_trials = (
        frame[trials_column].notna()
        & frame[trials_column].ge(minimum_trials)
        & frame[successes_column].ge(0)
        & frame[successes_column].le(frame[trials_column])
    )
    data = frame.loc[frame.common_primary_eligible & valid_trials].copy()
    design, names = design_matrix(
        data,
        include_match_effects=include_match_effects,
        exact_goal_difference=exact_goal_difference,
    )
    successes = data[successes_column].to_numpy(float)
    trials = data[trials_column].to_numpy(float)
    fit = fit_binomial(successes, trials, design, data[cluster_variable].to_numpy())
    rows = []
    coefficient_names = ["goal_difference"] if exact_goal_difference else list(CONTRASTS)
    for name in coefficient_names:
        if name not in names:
            continue
        index = names.index(name)
        coefficient = float(fit["coefficient"][index])
        standard_error = float(fit["standard_error"][index])
        rows.append(
            {
                "model_id": model_id,
                "analysis_role": analysis_role,
                "outcome": f"{successes_column}/{trials_column}",
                "model_family": "grouped_binomial_logit",
                "coefficient_name": name,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "confidence_interval_lower": coefficient - 1.96 * standard_error,
                "confidence_interval_upper": coefficient + 1.96 * standard_error,
                "p_value": _normal_p_value(coefficient, standard_error),
                "incidence_rate_ratio": None,
                "odds_ratio": math.exp(coefficient),
                "sample_size": len(data),
                "match_count": data.match_id.nunique(),
                "team_count": data.team_id.nunique(),
                "outcome_total": int(successes.sum()),
                "exposure_total": int(trials.sum()),
                "offset": None,
                "reference_category": "drawing" if not exact_goal_difference else None,
                "fixed_effects": "team_id + match_id" if include_match_effects else "team_id",
                "cluster_variable": cluster_variable,
                "convergence_status": "converged" if fit["converged"] else "warning",
                "execution_status": "executed",
                "warning_flags": "",
                "unavailable_reason": None,
            }
        )
    predictions = []
    if not exact_goal_difference:
        for state in ("leading", "drawing", "trailing"):
            estimate, lower, upper = _marginal_prediction(
                design,
                names,
                fit["coefficient"],
                fit["covariance"],
                state,
                "binomial",
            )
            predictions.append(
                {
                    "model_id": model_id,
                    "score_state": state,
                    "predicted_value": estimate,
                    "confidence_interval_lower": lower,
                    "confidence_interval_upper": upper,
                    "scale": "probability",
                }
            )
    fitted_successes = fit["fitted"] * trials
    diagnostics = _base_diagnostics(
        data,
        successes,
        trials,
        design,
        fitted_successes,
        bool(fit["converged"]),
        f"cluster_robust:{cluster_variable}",
    )
    diagnostics.update(
        {
            "model_id": model_id,
            "separation": bool(
                np.any(data.groupby("score_state_majority")[successes_column].sum() == 0)
                or np.any(
                    data.groupby("score_state_majority")[successes_column].sum()
                    == data.groupby("score_state_majority")[trials_column].sum()
                )
            ),
            "overdispersion": None,
            "missing_data_exclusions": int(len(frame) - len(data)),
            "minimum_denominator": minimum_trials,
            "successes_column": successes_column,
            "trials_column": trials_column,
        }
    )
    return pd.DataFrame(rows), pd.DataFrame(predictions), diagnostics


def holm_adjust(primary: pd.DataFrame) -> pd.DataFrame:
    """Holm-adjust the two primary outcome p-values within each contrast."""
    rows = []
    for contrast, group in primary.groupby("coefficient_name"):
        valid = group.dropna(subset=["p_value"]).sort_values(["p_value", "model_id"])
        running = 0.0
        count = len(valid)
        for rank, row in enumerate(valid.itertuples(index=False), start=1):
            adjusted = min(1.0, (count - rank + 1) * float(row.p_value))
            running = max(running, adjusted)
            rows.append(
                {
                    "coefficient_name": contrast,
                    "model_id": row.model_id,
                    "raw_p_value": row.p_value,
                    "holm_adjusted_p_value": running,
                    "family_size": count,
                }
            )
    return pd.DataFrame(rows)
