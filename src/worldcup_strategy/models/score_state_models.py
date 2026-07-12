# mypy: ignore-errors
"""Pre-specified observational score-state model execution."""

import math

import numpy as np
import pandas as pd

from worldcup_strategy.models.continuous_models import fit_clustered_ols
from worldcup_strategy.models.count_models import fit_binomial, fit_poisson
from worldcup_strategy.models.diagnostics import estimable, overdispersion

COUNT_OUTCOMES = ("shots", "pressure_events", "pressure_regains_5s")
CONTINUOUS_OUTCOMES = (
    "xg_per_effective_10min",
    "xt_per_effective_10min",
    "mean_pass_length",
    "pass_directness",
)
PROPORTION_OUTCOMES = (
    "pass_completion_rate",
    "forward_pass_share",
    "long_pass_share",
    "possession_share",
    "high_pressure_share",
    "pressure_regain_5s_rate",
)


def model_specifications() -> list[dict[str, object]]:
    """Create the complete manifest before model fitting."""
    specs = [
        {
            "model_id": f"primary_{outcome}",
            "outcome": outcome,
            "model_family": "poisson",
            "execution_status": "planned",
        }
        for outcome in COUNT_OUTCOMES
    ]
    specs.extend(
        {
            "model_id": f"primary_{outcome}",
            "outcome": outcome,
            "model_family": "ols_clustered",
            "execution_status": "planned",
        }
        for outcome in CONTINUOUS_OUTCOMES
    )
    specs.extend(
        {
            "model_id": f"primary_{outcome}",
            "outcome": outcome,
            "model_family": "fractional_logit"
            if outcome == "possession_share"
            else "grouped_binomial_logit",
            "execution_status": "planned",
        }
        for outcome in PROPORTION_OUTCOMES
    )
    specs.extend(
        [
            {
                "model_id": "attacking_substitution",
                "outcome": "attacking_substitution",
                "model_family": "binomial",
                "execution_status": "unavailable",
                "unavailable_reason": "incoming_positions_not_available",
            },
            {
                "model_id": "defensive_substitution",
                "outcome": "defensive_substitution",
                "model_family": "binomial",
                "execution_status": "unavailable",
                "unavailable_reason": "incoming_positions_not_available",
            },
            {
                "model_id": "goalkeeper_substitution",
                "outcome": "goalkeeper_substitutions",
                "model_family": "binomial",
                "execution_status": "unavailable",
                "unavailable_reason": "insufficient_positive_events",
            },
        ]
    )
    return specs


def _design(frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    minute = (frame.window_start_seconds + frame.window_end_seconds) / 120
    columns = [
        np.ones(len(frame)),
        frame.score_state_majority.eq("leading").astype(float),
        frame.score_state_majority.eq("trailing").astype(float),
        minute / 90,
        (minute / 90) ** 2,
        frame.red_card_difference_start.astype(float),
    ]
    names = [
        "intercept",
        "score_state[leading]",
        "score_state[trailing]",
        "match_minute",
        "match_minute_squared",
        "red_card_difference",
    ]
    for team in sorted(frame.team_id.unique())[1:]:
        columns.append(frame.team_id.eq(team).astype(float))
        names.append(f"team[{team}]")
    design = np.column_stack(columns)
    keep = [0, *[index for index in range(1, design.shape[1]) if np.ptp(design[:, index]) > 0]]
    return design[:, keep], [names[index] for index in keep]


def fit_score_state_models(
    features: pd.DataFrame, cluster_variable: str = "match_id"
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Fit all estimable planned models without significance filtering."""
    eligible = features[
        (features.effective_play_seconds >= 30) & features.score_state_majority.notna()
    ].copy()
    x, names = _design(eligible)
    rows = []
    diagnostics = {}
    for outcome in COUNT_OUTCOMES:
        offset_source = (
            "pressure_events" if outcome == "pressure_regains_5s" else "effective_play_seconds"
        )
        valid = eligible[offset_source] > 0
        xv = x[valid]
        data = eligible.loc[valid]
        if not estimable(xv):
            continue
        offset = np.log(data[offset_source].to_numpy(float))
        fit = fit_poisson(
            data[outcome].to_numpy(float), xv, offset, data[cluster_variable].to_numpy()
        )
        dispersion = overdispersion(data[outcome].to_numpy(float), fit["fitted"], xv.shape[1])
        diagnostics[outcome] = {"overdispersion": dispersion, "converged": fit["converged"]}
        for name in ("score_state[leading]", "score_state[trailing]"):
            index = names.index(name)
            coefficient = float(fit["coefficient"][index])
            standard_error = float(fit["standard_error"][index])
            rows.append(
                {
                    "model_id": f"primary_{outcome}",
                    "outcome": outcome,
                    "model_family": "poisson",
                    "formula": (
                        f"{outcome} ~ score_state + minute + minute2 + "
                        "red_card_difference + team_FE"
                    ),
                    "reference_category": "drawing",
                    "dataset_unit": "team_window_5min",
                    "offset": offset_source,
                    "weights": None,
                    "fixed_effects": "team_id",
                    "cluster_variable": cluster_variable,
                    "coefficient_name": name,
                    "coefficient": coefficient,
                    "standard_error": standard_error,
                    "confidence_interval_lower": coefficient - 1.96 * standard_error,
                    "confidence_interval_upper": coefficient + 1.96 * standard_error,
                    "p_value": None,
                    "incidence_rate_ratio": math.exp(coefficient),
                    "odds_ratio": None,
                    "adjusted_difference": None,
                    "sample_size": len(data),
                    "match_count": data.match_id.nunique(),
                    "team_count": data.team_id.nunique(),
                    "convergence_status": "converged" if fit["converged"] else "warning",
                    "execution_status": "executed",
                    "warning_flags": "",
                    "unavailable_reason": None,
                }
            )
    for outcome in CONTINUOUS_OUTCOMES:
        valid = eligible[outcome].notna()
        data = eligible.loc[valid]
        xv = x[valid]
        if not estimable(xv):
            continue
        fit = fit_clustered_ols(
            data[outcome].to_numpy(float), xv, data[cluster_variable].to_numpy()
        )
        for name in ("score_state[leading]", "score_state[trailing]"):
            index = names.index(name)
            coefficient = float(fit["coefficient"][index])
            standard_error = float(fit["standard_error"][index])
            rows.append(
                _model_row(
                    outcome,
                    "ols_clustered",
                    name,
                    coefficient,
                    standard_error,
                    data,
                    adjusted_difference=coefficient,
                    cluster_variable=cluster_variable,
                )
            )
    for outcome in PROPORTION_OUTCOMES:
        numerator = f"{outcome}_numerator"
        denominator = f"{outcome}_denominator"
        valid = eligible[numerator].notna() & eligible[denominator].gt(0)
        data = eligible.loc[valid]
        xv = x[valid]
        if not estimable(xv):
            continue
        fit = fit_binomial(
            data[numerator].to_numpy(float),
            data[denominator].to_numpy(float),
            xv,
            data[cluster_variable].to_numpy(),
        )
        family = "fractional_logit" if outcome == "possession_share" else "grouped_binomial_logit"
        for name in ("score_state[leading]", "score_state[trailing]"):
            index = names.index(name)
            coefficient = float(fit["coefficient"][index])
            standard_error = float(fit["standard_error"][index])
            rows.append(
                _model_row(
                    outcome,
                    family,
                    name,
                    coefficient,
                    standard_error,
                    data,
                    odds_ratio=math.exp(coefficient),
                    weights=denominator,
                    cluster_variable=cluster_variable,
                )
            )
    for specification in model_specifications():
        if specification["execution_status"] != "unavailable":
            continue
        rows.append(
            {
                "model_id": specification["model_id"],
                "outcome": specification["outcome"],
                "model_family": specification["model_family"],
                "dataset_unit": "team_window_5min",
                "formula": None,
                "reference_category": "drawing",
                "offset": None,
                "weights": None,
                "fixed_effects": "team_id",
                "cluster_variable": cluster_variable,
                "coefficient_name": None,
                "coefficient": None,
                "standard_error": None,
                "confidence_interval_lower": None,
                "confidence_interval_upper": None,
                "p_value": None,
                "incidence_rate_ratio": None,
                "odds_ratio": None,
                "adjusted_difference": None,
                "sample_size": 0,
                "match_count": 0,
                "team_count": 0,
                "convergence_status": "not_run",
                "execution_status": "unavailable",
                "warning_flags": "",
                "unavailable_reason": specification["unavailable_reason"],
            }
        )
    return pd.DataFrame(rows), diagnostics


def _model_row(
    outcome: str,
    family: str,
    coefficient_name: str,
    coefficient: float,
    standard_error: float,
    data: pd.DataFrame,
    *,
    adjusted_difference: float | None = None,
    odds_ratio: float | None = None,
    weights: str | None = None,
    cluster_variable: str = "match_id",
) -> dict[str, object]:
    return {
        "model_id": f"primary_{outcome}",
        "outcome": outcome,
        "model_family": family,
        "dataset_unit": "team_window_5min",
        "formula": f"{outcome} ~ score_state + minute + minute2 + red_card_difference + team_FE",
        "reference_category": "drawing",
        "offset": None,
        "weights": weights,
        "fixed_effects": "team_id",
        "cluster_variable": cluster_variable,
        "coefficient_name": coefficient_name,
        "coefficient": coefficient,
        "standard_error": standard_error,
        "confidence_interval_lower": coefficient - 1.96 * standard_error,
        "confidence_interval_upper": coefficient + 1.96 * standard_error,
        "p_value": None,
        "incidence_rate_ratio": None,
        "odds_ratio": odds_ratio,
        "adjusted_difference": adjusted_difference,
        "sample_size": len(data),
        "match_count": data.match_id.nunique(),
        "team_count": data.team_id.nunique(),
        "convergence_status": "converged",
        "execution_status": "executed",
        "warning_flags": "zero_heavy" if outcome.startswith(("xg_", "xt_")) else "",
        "unavailable_reason": None,
    }
