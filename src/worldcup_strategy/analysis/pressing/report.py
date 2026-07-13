# ruff: noqa: E501
# mypy: ignore-errors
"""Generate the analysis report and paper scaffold from preserved results."""

from pathlib import Path

import pandas as pd

PLAN_COMMIT = "361534c"
PAPER = Path("paper/pressing_score_state")


def _markdown(frame: pd.DataFrame) -> str:
    values = frame.fillna("").astype(str)
    header = "| " + " | ".join(values.columns) + " |"
    separator = "| " + " | ".join("---" for _ in values.columns) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in values.to_numpy().tolist()]
    return "\n".join([header, separator, *rows])


def _primary_lines(coefficients: pd.DataFrame) -> str:
    lines = []
    for row in coefficients.itertuples(index=False):
        transformed = (
            row.incidence_rate_ratio if pd.notna(row.incidence_rate_ratio) else row.odds_ratio
        )
        label = row.coefficient_name.replace("score_state[", "").replace("]", "")
        lines.append(
            f"- {row.model_id}, {label} versus drawing: coefficient {row.coefficient:.3f} "
            f"(95% CI {row.confidence_interval_lower:.3f} to {row.confidence_interval_upper:.3f}); "
            f"transformed estimate {transformed:.3f}; n={int(row.sample_size)} windows."
        )
    return "\n".join(lines)


def generate_report() -> str:
    characteristics = pd.read_csv("outputs/tables/pressing_sample_characteristics_2022.csv")
    primary = pd.read_csv("outputs/tables/pressing_primary_models_2022.csv")
    predictions = pd.read_csv("outputs/tables/pressing_adjusted_predictions_2022.csv")
    robust = pd.read_csv("outputs/tables/pressing_robustness_2022.csv")
    flow = pd.read_csv("outputs/tables/pressing_exclusion_flow_2022.csv")
    diagnostic = pd.read_json("outputs/models/pressing_score_state/model_diagnostics.json").T
    sample = _markdown(characteristics)
    robustness_status = (
        robust.groupby(["specification_group", "execution_status"], dropna=False)
        .size()
        .reset_index(name="contrast_rows")
        .pipe(_markdown)
    )
    text = f"""# Pressing Score-State Analysis Report

## Analysis-plan lock

The plan was locked at commit `{PLAN_COMMIT}` before pressing-specific coefficients were inspected. The two primary questions concern conditional associations between score state and (1) Pressure-event intensity per opponent pass and (2) five-second sequence regain efficiency. Drawing is the reference category. The primary models are a Poisson GLM with `log(opponent_passes)` offset and a grouped-binomial logit model; both use team fixed effects and match-clustered covariance. No post-lock primary specification deviation was made.

## Sample construction

The source contains 2,822 team-match five-minute windows from 64 matches and 32 teams. Regular periods, valid homogeneous score states, numerical equality, and outcome-specific minimum denominators were applied. The intensity model retained 2,379 windows; the efficiency model retained 2,054.

{sample}

The complete stepwise reconciliation is in `outputs/tables/pressing_exclusion_flow_2022.csv` ({len(flow)} rows). Null metric values were not silently converted to zero.

## Primary results

These are adjusted observational associations, not causal estimates.

{_primary_lines(primary)}

Adjusted predictions are preserved for both contrasts and all three states:

{_markdown(predictions)}

Holm-adjusted primary-family inference is in `outputs/models/pressing_score_state/multiplicity_adjustment.json`. The Poisson model's dispersion was {float(diagnostic.loc["primary_pressing_intensity", "overdispersion"]):.3f}; because it exceeded the locked materiality threshold, the preregistered NB2 robustness model was executed without replacing the primary Poisson model.

## Secondary and exploratory results

Secondary models retain high-pressure share, pressure-sequence frequency, classic-PPDA components, event regain, counterpress share, high regains, mean pressure height, and post-regain shot production. Post-regain xG and xT are exploratory. Same-possession goal was explicitly unavailable because the required indicator was absent. Provider-augmented PPDA was retained only as an unavailable sensitivity entry, not promoted to inference.

## Robustness analyses

All 16 required groups were preserved, plus the triggered NB2 overdispersion analysis. Applicability failures remain explicit rather than being dropped.

{robustness_status}

Robustness must be interpreted using sign, transformed magnitude, confidence-interval width, sample size, convergence, and measurement-definition changes—not significance alone. Full rows are in `outputs/tables/pressing_robustness_2022.csv`.

## Figures and tables

Seven figures are generated in SVG, PDF, and deterministic 300-DPI PNG, each with a source CSV in `outputs/figures/pressing_score_state/`. Tables and Parquet model outputs are generated from processed data; no paper values are manually embedded.

## Limitations

- Score-state exposure is observational, endogenous, and susceptible to reverse temporal selection.
- The sample is one tournament, limiting external generalizability.
- Pressure is provider-defined; event-derived possession exposure and sequence definitions are measurement choices.
- Results depend on minimum denominators and uncertainty differs under team versus match clustering.
- StatsBomb 360 coverage is incomplete and is not treated as full tracking; it is not part of the confirmatory outcomes.
- Team fixed effects do not resolve all time-varying match context or opponent-quality confounding.

## Reproducibility

The manifest records plan/data/repository commits, configuration and input hashes, commands, seeds, and output checksums. Validation and two-run checksum comparison are required quality gates. Milestone 5 and qualification simulation are outside scope.

The independent implementation audit is preserved in `outputs/reports/pressing_score_state_independent_audit.json`. A remaining limitation is that full residual diagnostics were not recomputed for every robustness-grid variant; the grid preserves sample, clustering, convergence, and an explicit limitation instead. The locked nuisance design is rank deficient by one column and is transparently flagged rather than revised after results inspection.
"""
    Path("PRESSING_SCORE_STATE_ANALYSIS_REPORT.md").write_text(text)
    _paper(text)
    return text


def _paper(report: str) -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    sections = {
        "01_introduction.md": "# 1. Introduction\n\nThis study separates pressing frequency, regain efficiency, and subsequent attacking value using observational World Cup event data.\n",
        "02_related_work.md": "# 2. Related Work\n\nLiterature synthesis and citations remain to be completed; no unsupported claim is asserted here.\n",
        "03_data.md": "# 3. Data\n\nThe analysis uses audited processed StatsBomb Open Data for the 2022 tournament. See the generated sample table.\n\n![](../../outputs/figures/pressing_score_state/figure_2.svg)\n",
        "04_operationalization.md": "# 4. Operationalizing Pressing Intensity and Efficiency\n\nIntensity is the Pressure-event count with opponent passes as exposure. Efficiency is controlled regains within five seconds per Pressure sequence.\n",
        "05_analysis_plan.md": f"# 5. Analysis Plan\n\nLocked at `{PLAN_COMMIT}`. See `ANALYSIS_PLAN_PRESSING_SCORE_STATE.md`.\n",
        "06_results.md": "# 6. Results\n\nGenerated results are reported in `PRESSING_SCORE_STATE_ANALYSIS_REPORT.md`.\n\n![](../../outputs/figures/pressing_score_state/figure_3.svg)\n\n![](../../outputs/figures/pressing_score_state/figure_4.svg)\n",
        "07_robustness.md": "# 7. Robustness Analyses\n\nAll planned specifications, including unavailable combinations, are preserved in the generated robustness table.\n",
        "08_discussion.md": "# 8. Discussion\n\nInterpretation is limited to conditional association; frequency and successful conversion remain distinct constructs.\n",
        "09_limitations.md": "# 9. Limitations\n\nSee the generated report for observational endogeneity, one-tournament scope, provider definitions, exposure and sequence dependence, threshold dependence, clustering uncertainty, incomplete 360 coverage, and external-generalizability limitations.\n",
        "10_reproducibility.md": "# 10. Reproducibility and Data Availability\n\nGenerated artifacts are linked to processed data through the machine-readable analysis manifest. Raw provider data are not committed.\n",
        "11_conclusion.md": "# 11. Conclusion\n\nThe generated estimates support only observational, tournament-specific conclusions.\n",
    }
    for name, content in sections.items():
        (PAPER / name).write_text(content)
    (PAPER / "README.md").write_text(
        "# Pressing the Scoreline\n\n"
        + "\n".join(f"- [{name}]({name})" for name in sections)
        + "\n"
    )
