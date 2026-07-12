"""Tests for pre-specified observational models."""

from worldcup_strategy.models.score_state_models import model_specifications


def test_reference_and_unavailable_substitution_specs() -> None:
    specs = model_specifications()
    unavailable = [spec for spec in specs if spec["execution_status"] == "unavailable"]
    assert {spec["outcome"] for spec in unavailable} == {
        "attacking_substitution",
        "defensive_substitution",
        "goalkeeper_substitutions",
    }
    assert all(spec["unavailable_reason"] for spec in unavailable)
