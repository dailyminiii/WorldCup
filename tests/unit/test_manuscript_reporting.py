"""Regression tests for manuscript numerical insertion and audit."""

from worldcup_strategy.reporting.manuscript_audit import audit
from worldcup_strategy.reporting.manuscript_build import build_markdown
from worldcup_strategy.reporting.manuscript_validation import validate_and_generate


def test_manuscript_values_validate() -> None:
    report = validate_and_generate()
    assert report["valid"]
    assert report["numerical_validation_failures"] == 0


def test_manuscript_reports_both_primary_contrasts_without_causal_phrases() -> None:
    report = audit()
    assert report["claim_audit"]["both_primary_contrasts_reported"]
    assert report["causal_language_audit"]["finding_count"] == 0


def test_markdown_build_has_no_unresolved_value_macros() -> None:
    target = build_markdown()
    text = target.read_text()
    assert "{{" not in text
    assert "trailing" in text.lower()
    assert "leading" in text.lower()
