# mypy: ignore-errors
"""Pre-specified observational score-state model execution."""

import math

import numpy as np
import pandas as pd

from worldcup_strategy.models.count_models import fit_poisson
from worldcup_strategy.models.diagnostics import estimable, overdispersion

COUNT_OUTCOMES = ("shots", "pressure_events", "pressure_regains_5s")


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
                "unavailable_reason": "only_two_events_not_estimable",
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
    return np.column_stack(columns), names


def fit_score_state_models(features: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
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
        fit = fit_poisson(data[outcome].to_numpy(float), xv, offset, data.match_id.to_numpy())
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
                    "offset": offset_source,
                    "fixed_effects": "team_id",
                    "cluster_variable": "match_id",
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
    return pd.DataFrame(rows), diagnostics
