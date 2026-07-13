# Pressing score-state manuscript audit

## Scope and checkpoints

The first complete internal manuscript draft was reviewed against `milestone-4`, `pressing-score-state-v1`, and locked plan commit `361534c`. The audit did not alter the research question, primary outcomes, primary specifications, or generated estimates. Milestone 5 was not started.

## Evidence integrity

- Claim-ledger entries: 15
- Claims linked to generated evidence: 15
- Unsupported empirical claims: 0
- Primary contrasts omitted: 0
- Numerical validation failures: 0
- Prohibited causal-language findings: 0
- Unsupported novelty claims: 0
- Unverified citation placeholders: 8, all explicitly recorded

Both leading-versus-drawing and trailing-versus-drawing contrasts appear for both confirmatory outcomes. Secondary, exploratory, and unavailable analyses retain those labels. Interpretation uses estimates, intervals, predictions, and robustness properties rather than p-values alone.

## Findings and fixes

### High severity: empirical prose initially risked manual number duplication

**Consequence:** prose and generated model outputs could diverge during regeneration.

**Fix:** empirical LaTeX values are generated in `macros.tex`; the readable Markdown draft is built from a value-placeholder template. Table files are generated directly from machine-readable outputs. A validation program checks model samples, teams, matches, sequence denominators, robustness groups, primary predictions, and figure-source values.

During audit, the first macro implementation was found to express the intensity difference using
the absolute event-rate difference multiplied by 100 rather than the generated percentage field.
That manuscript-only scale error was corrected before release; model outputs were unchanged.

**Validation:** programmed consistency checks pass with zero numerical failures.

### High severity: literature claims lacked verified sources

**Consequence:** invented or weakly supported bibliographic claims could enter a draft.

**Fix:** eight structured citation placeholders are recorded in `CITATIONS_TO_VERIFY.md` and represented as clearly unverified BibTeX placeholders. No author, DOI, venue, or year was fabricated.

**Validation:** the claim audit finds all placeholder keys documented. The manuscript is explicitly not submission-ready.

### Medium severity: no TeX engine is installed in the offline environment

**Consequence:** the arXiv-compatible `main.tex` could not be compiled with `pdflatex`, `xelatex`, `lualatex`, `tectonic`, or `latexmk` in this environment.

**Disposition:** unresolved environment limitation. A deterministic three-page internal-review PDF was generated twice from the validated Markdown using the system CUPS PDF filter; both SHA-256 checksums were identical. This PDF verifies readable delivery, not TeX compilation. LaTeX compilation remains a pre-submission TODO.

### Existing scientific limitations retained

The manuscript explicitly includes observational score-state endogeneity, reverse temporal ordering, simultaneous opponent response, one-tournament scope, national-team heterogeneity, provider-defined Pressure, sequence and regain-window dependence, event-derived opportunities, threshold sensitivity, incomplete 360 coverage, lack of continuous tracking, unobserved context, team-fixed-effect limitations, 64-match clustered uncertainty, nuisance rank deficiency, non-uniform robustness residual diagnostics, and limited generalizability.

## Audit conclusion

Critical findings: 0. High findings: 2; both fixed. The claim, numerical, selective-reporting, labeling, causal-language, novelty, unavailable-result, figure-source, table-source, limitation, and fabricated-reference audits pass. The manuscript is a complete internal draft but is not submission-ready until citations are verified and `main.tex` is compiled and visually inspected with a real TeX engine.
