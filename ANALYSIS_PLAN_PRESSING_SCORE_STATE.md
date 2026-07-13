# Locked analysis plan: pressing and score state

Status: **scientifically locked before pressing-specific model estimation**

The lock commit is recorded in the adjacent machine-readable analysis manifest after this file's
first commit. Administrative insertion of that hash does not change the specifications below.

## Research question and scope

How are pressing intensity and pressure-to-regain efficiency conditionally associated with
leading, drawing, and trailing score states in the 2022 FIFA World Cup?

The analysis distinguishes pressing frequency, pressure-to-regain efficiency, and post-regain
attacking value. The first two are confirmatory; post-regain value is secondary or exploratory.
All estimands are observational associations because score state is endogenous.

## Locked hypotheses

- H1: trailing is associated with a higher Pressure-event rate per opponent pass than drawing.
- H2: trailing is associated with a greater high-pressure share than drawing.
- H3: sequence-level five-second regain efficiency differs across score states (two-sided).
- H4: intensity differences need not match regain-efficiency direction or magnitude.

## Outcomes and estimands

The two confirmatory primary outcomes are fixed:

1. `pressure_events`, offset by log `opponent_passes`; report incidence-rate ratios, predicted
   events per 30 opponent passes, and adjusted percentage differences.
2. grouped-binomial `sequence_regains_5s` successes out of `pressure_sequences`; report odds
   ratios, adjusted probabilities, and percentage-point differences.

Secondary outcomes are pressure sequences per opponent possession, classic PPDA components,
high-pressure share, event-level five-second regain, sequence regain at three/eight seconds,
counterpress share, high-regain rate, and post-regain shot/xG/xT outcomes. Goal outcomes and 360
context are exploratory and may be unavailable when evidence is insufficient.

## Unit, exposure, and exclusions

Primary unit: team × match × fixed five-minute window from
`data/processed/state/team_window_features_2022.parquet`.

Primary inclusion requires periods 1–2, valid categorical majority score state, no mixed score
state, numerical equality throughout the window, at least five opponent passes for intensity,
and at least three Pressure sequences for sequence efficiency. Shootouts and extra time are
excluded. All otherwise eligible teams and matches are retained. Drawing is the reference.

Homogeneous team-state segments are the principal alternative unit. Exact goal difference is a
robustness exposure only.

## Covariates, fixed effects, and uncertainty

Both primary formulas include leading/trailing indicators, centered match minute and its square,
competition stage, group matchday where defined, and team fixed effects. Match-clustered robust
standard errors are primary. Team clustering and match fixed effects are prespecified robustness
analyses. Terms are never dropped silently; rank failures and unavailable specifications remain
in outputs.

## Model families

- Intensity: Poisson log-link with log-opponent-pass offset. Pearson overdispersion is reported;
  a negative-binomial sensitivity is attempted only if materially indicated and supported.
- Sequence efficiency: grouped-binomial logit using successes and failures, never OLS on rates.
- Proportions: grouped-binomial logit from raw successes/trials.
- Post-regain xG/xT: match-clustered OLS on opportunity-normalized values, with zero-heavy
  diagnostics; Gamma is prohibited on zero-valued samples.

## Missing data and denominator thresholds

Missing exposures remain missing, zero exposures remain in exclusion counts, and neither is
converted to zero. Primary minimums are five opponent passes and three Pressure sequences.
Sensitivity thresholds are opponent passes 3/5/10 and sequences 1/3/5. Each model records its
own exclusions, totals, teams, and matches.

## Robustness specifications

All 16 named specifications are retained whether executed, failed, non-identifiable, or
unavailable: primary windows; homogeneous segments; mixed-state duration weighting; red-card
exclusion; group stage; knockout; extra-time exclusion; denominator thresholds; opponent
possession count exposure; opponent possession seconds exposure; event-level regain; 3-second
regain; 8-second regain; team clustering; match fixed effects; exact goal difference.

## Interpretation and multiplicity

Both leading-versus-drawing and trailing-versus-drawing contrasts are always reported. Holm
adjustment is applied across the two primary outcome families for each score-state contrast.
Effect sizes and confidence intervals are primary; p-values are secondary. Secondary and
exploratory estimates are labeled and cannot be promoted after inspection. Robustness is judged
by direction, magnitude ratio, interval width, sample change, and convergence—not significance.

## Diagnostics

Every model records observations, teams, matches, outcome and exposure totals, zero-outcome
share, overdispersion or separation, design rank, dropped terms, exclusions, covariance method,
influence diagnostics where available, and convergence.

## Stopping criteria

The analysis stops after all locked primary, secondary, robustness, diagnostic, table, and figure
specifications are executed or explicitly recorded unavailable; deterministic reruns and quality
gates must pass. No model is added, removed, or selected because of an observed estimate.
