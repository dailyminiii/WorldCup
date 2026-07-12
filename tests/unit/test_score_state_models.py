"""Tests for pre-specified observational models."""

import numpy as np

from worldcup_strategy.models.continuous_models import fit_clustered_ols
from worldcup_strategy.models.count_models import fit_binomial
from worldcup_strategy.models.robustness import SPECIFICATIONS
from worldcup_strategy.models.score_state_models import _design, model_specifications


def test_reference_and_unavailable_substitution_specs() -> None:
    specs = model_specifications()
    unavailable = [spec for spec in specs if spec["execution_status"] == "unavailable"]
    assert {spec["outcome"] for spec in unavailable} == {
        "attacking_substitution",
        "defensive_substitution",
        "goalkeeper_substitutions",
    }
    assert all(spec["unavailable_reason"] for spec in unavailable)


def test_all_robustness_specifications_are_declared() -> None:
    assert len(SPECIFICATIONS) == 14
    assert len(set(SPECIFICATIONS)) == 14


def test_clustered_ols_and_grouped_binomial_are_deterministic() -> None:
    x = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    clusters = np.array([1, 1, 2, 2])
    first = fit_clustered_ols(np.array([0.0, 1.0, 0.2, 1.2]), x, clusters)
    second = fit_clustered_ols(np.array([0.0, 1.0, 0.2, 1.2]), x, clusters)
    np.testing.assert_allclose(first["coefficient"], second["coefficient"])
    fitted = fit_binomial(
        np.array([1.0, 8.0, 2.0, 7.0]),
        np.array([10.0] * 4),
        x,
        clusters,
    )
    assert np.isfinite(fitted["coefficient"]).all()


def test_match_fixed_effect_design_is_constructed_when_requested() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "window_start_seconds": [0, 300, 0, 300, 0, 300],
            "window_end_seconds": [300, 600, 300, 600, 300, 600],
            "score_state_majority": [
                "drawing",
                "leading",
                "drawing",
                "trailing",
                "drawing",
                "leading",
            ],
            "red_card_difference_start": [0] * 6,
            "team_id": [1, 1, 2, 2, 3, 3],
            "match_id": [10, 11, 10, 12, 11, 12],
        }
    )
    design, names = _design(frame, include_match_effects=True)
    assert any(name.startswith("match[") for name in names)
    assert design.shape[1] > _design(frame, include_match_effects=False)[0].shape[1]
