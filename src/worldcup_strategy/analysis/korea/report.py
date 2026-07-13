# ruff: noqa: E501
"""Generate the preliminary case-study narrative from generated tables."""
# mypy: ignore-errors

from pathlib import Path

from worldcup_strategy.analysis.korea.pipeline import compare


def generate_report() -> str:
    _, tournament = compare()
    rows = tournament.set_index("tournament_year")
    text = f"""# Korea Republic Across Two World Cups: A Reproducible Preliminary Comparison

## 1. Purpose

This descriptive case study compares Korea Republic's three group matches in 2022 and 2026.
It contains no causal claims, p-values, or inferential tests.

## 2. Data Sources

The 2022 layer uses the repository's pinned StatsBomb Open Data canonical tables. The 2026
layer uses official FIFA match articles and available official reports; secondary sources
are used only to cross-check two match-duration values.

## 3. Verification Process

Every normalized 2026 goal and result carries a source URL and verification status. No
source conflicts remain. Two match durations are marked approximate, and missing detailed
statistics remain null rather than zero.

## 4. Match Inventory

Both tournament samples contain exactly three group-stage matches. Korea recorded
{int(rows.loc[2022, "points"])} points in 2022 and {int(rows.loc[2026, "points"])} in 2026;
goal records were {int(rows.loc[2022, "goals_for"])}-{int(rows.loc[2022, "goals_against"])}
and {int(rows.loc[2026, "goals_for"])}-{int(rows.loc[2026, "goals_against"])}, respectively.

## 5. Score-State Exposure

| Year | Leading min | Drawing min | Trailing min | Leading share | Drawing share | Trailing share |
|---:|---:|---:|---:|---:|---:|---:|
| 2022 | {rows.loc[2022, "leading_minutes"]:.1f} | {rows.loc[2022, "drawing_minutes"]:.1f} | {rows.loc[2022, "trailing_minutes"]:.1f} | {rows.loc[2022, "leading_share"]:.3f} | {rows.loc[2022, "drawing_share"]:.3f} | {rows.loc[2022, "trailing_share"]:.3f} |
| 2026 | {rows.loc[2026, "leading_minutes"]:.1f} | {rows.loc[2026, "drawing_minutes"]:.1f} | {rows.loc[2026, "trailing_minutes"]:.1f} | {rows.loc[2026, "leading_share"]:.3f} | {rows.loc[2026, "drawing_share"]:.3f} | {rows.loc[2026, "trailing_share"]:.3f} |

## 6. Comparable Match-Level Metrics

The primary intersection contains results, goals, points, and goal-timestamp-derived
score-state exposure. Detailed official 2026 statistics are not complete across all three
matches and are excluded from tournament-level comparison.

## 7. Descriptive Comparison

The official summary data show different raw outcome and score-state profiles. These
descriptive differences should not be interpreted as causal or tactical efficiency estimates.

## 8. Metrics Not Yet Comparable

This preliminary comparison does not evaluate score-state-specific pressing intensity or
regain efficiency in 2026 because matching event-level data are not currently available in
the validated data source. Pressure events, pressure sequences, PPDA, regain efficiency,
xG, xT, progression, and StatsBomb 360 context are unavailable.

## 9. Limitations

The sample is three matches per tournament. Provider definitions are not assumed equivalent.
Two 2026 final-whistle durations rely on documented secondary cross-checks, so corresponding
exposure estimates are explicitly approximate. Whole-match statistics are never allocated
to leading, drawing, or trailing periods.

## 10. Future Event-Level Extension

The availability adapter can detect a future StatsBomb 2026 release and fails actionably
until matches, events, lineups, and 360 coverage can be validated.
"""
    Path("KOREA_2022_2026_PRELIMINARY_CASE_STUDY.md").write_text(text)
    return text
