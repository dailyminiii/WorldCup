"""Regression tests for the locked pressing score-state analysis."""

import hashlib

import numpy as np
import pandas as pd

from worldcup_strategy.analysis.pressing.describe import descriptive_by_state
from worldcup_strategy.analysis.pressing.figures import generate_figures
from worldcup_strategy.analysis.pressing.models import (
    _marginal_prediction,
    design_matrix,
    holm_adjust,
)
from worldcup_strategy.analysis.pressing.pipeline import _per_success
from worldcup_strategy.analysis.pressing.prepare import _flow
from worldcup_strategy.analysis.pressing.robustness import SPECIFICATION_GROUPS
from worldcup_strategy.models.diagnostics import overdispersion


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "score_state_majority": ["drawing", "leading", "trailing"],
            "goal_difference_start": [0, 1, -1],
            "match_minute_centered": [-5.0, 0.0, 5.0],
            "match_minute_centered_squared": [25.0, 0.0, 25.0],
            "competition_stage": ["Group Stage"] * 3,
            "group_matchday": [1, 2, 3],
            "team_id": [1, 2, 3],
            "match_id": [10, 11, 12],
        }
    )


def test_drawing_is_reference_and_team_effects_present() -> None:
    _, names = design_matrix(_frame())
    assert "score_state[drawing]" not in names
    assert {"score_state[leading]", "score_state[trailing]"} <= set(names)
    assert any(name.startswith("team[") for name in names)


def test_exclusion_flow_reconciles_filters() -> None:
    frame = pd.DataFrame(
        {
            "regular_period": [True, False, True],
            "valid_score_state": [True, True, True],
            "numerically_equal": [True, True, False],
            "multiple_score_states": [False, False, False],
            "opponent_passes": [5.0, 8.0, 9.0],
            "pressure_sequences": [3, 3, 3],
            "sequence_regains_5s": [1, 1, 1],
        }
    )
    flow = _flow(frame, "pressing_intensity")
    assert flow[-1]["remaining"] == 1
    assert sum(row["excluded"] for row in flow) == len(frame) - 1


def test_sequence_success_cannot_exceed_trials() -> None:
    frame = pd.DataFrame(
        {
            "regular_period": [True],
            "valid_score_state": [True],
            "numerically_equal": [True],
            "multiple_score_states": [False],
            "pressure_sequences": [3],
            "sequence_regains_5s": [4],
        }
    )
    assert _flow(frame, "sequence_regain_efficiency")[-1]["remaining"] == 0


def test_holm_adjustment_is_monotone() -> None:
    table = pd.DataFrame(
        {
            "model_id": ["a", "a", "b", "b"],
            "coefficient_name": ["l", "t", "l", "t"],
            "p_value": [0.01, 0.04, 0.02, 0.2],
        }
    )
    adjusted = holm_adjust(table)
    assert (adjusted.holm_adjusted_p_value >= adjusted.raw_p_value).all()


def test_overdispersion_detection() -> None:
    outcome = np.array([0.0, 0.0, 20.0, 20.0])
    fitted = np.full(4, 10.0)
    assert overdispersion(outcome, fitted, 1) > 1.5


def test_all_robustness_groups_are_declared() -> None:
    assert len(SPECIFICATION_GROUPS) == 16
    assert "event_level_regain" in SPECIFICATION_GROUPS
    assert "homogeneous_state_segments" in SPECIFICATION_GROUPS


def test_pooled_and_unweighted_rates_are_distinct() -> None:
    frame = pd.DataFrame(
        {
            "score_state_majority": ["drawing", "drawing"],
            "intensity_primary_eligible": [True, True],
            "efficiency_primary_eligible": [True, True],
            "pressure_events": [1, 9],
            "opponent_passes": [1, 99],
            "pressure_sequences": [1, 9],
            "sequence_regains_5s": [1, 0],
            "match_id": [1, 2],
            "team_id": [1, 2],
        }
    )
    result = descriptive_by_state(frame)
    result = result[
        result.score_state.eq("drawing") & result.outcome.eq("pressing_intensity")
    ].iloc[0]
    assert result.pooled_rate != result.unweighted_mean


def test_figures_are_deterministic() -> None:
    first = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in generate_figures()
    }
    second = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in generate_figures()
    }
    assert first == second


def test_poisson_prediction_interval_is_not_capped_at_multiplier() -> None:
    design = np.ones((2, 1))
    estimate, _, upper = _marginal_prediction(
        design,
        ["intercept"],
        np.array([1.0]),
        np.array([[1.0]]),
        "drawing",
        "poisson",
        30,
    )
    assert estimate > 30
    assert upper > estimate


def test_post_regain_values_use_correct_denominator_and_keep_missing() -> None:
    result = _per_success(pd.Series([0.4, 0.3]), pd.Series([2, 0]))
    assert result.iloc[0] == 0.2
    assert pd.isna(result.iloc[1])
