# Pressing Score-State Analysis Report

## Analysis-plan lock

The plan was locked at commit `361534c` before pressing-specific coefficients were inspected. The two primary questions concern conditional associations between score state and (1) Pressure-event intensity per opponent pass and (2) five-second sequence regain efficiency. Drawing is the reference category. The primary models are a Poisson GLM with `log(opponent_passes)` offset and a grouped-binomial logit model; both use team fixed effects and match-clustered covariance. No post-lock primary specification deviation was made.

## Sample construction

The source contains 2,822 team-match five-minute windows from 64 matches and 32 teams. Regular periods, valid homogeneous score states, numerical equality, and outcome-specific minimum denominators were applied. The intensity model retained 2,379 windows; the efficiency model retained 2,054.

| score_state | all_windows | common_eligible_windows | intensity_eligible_windows | efficiency_eligible_windows | matches | teams | score_state_exposure_seconds | opponent_passes | pressure_events | pressure_sequences | sequence_regains_5s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leading | 686 | 632 | 585 | 498 | 54 | 28 | 192722.0 | 15405 | 3668 | 2972 | 559 |
| drawing | 1450 | 1260 | 1213 | 1068 | 61 | 32 | 413502.0 | 32605 | 7779 | 6424 | 1268 |
| trailing | 686 | 632 | 581 | 488 | 54 | 31 | 192722.0 | 14384 | 3550 | 2891 | 599 |

The complete stepwise reconciliation is in `outputs/tables/pressing_exclusion_flow_2022.csv` (15 rows). Null metric values were not silently converted to zero.

## Primary results

These are adjusted observational associations, not causal estimates.

- primary_pressing_intensity, leading versus drawing: coefficient -0.032 (95% CI -0.103 to 0.038); transformed estimate 0.968; n=2379 windows.
- primary_pressing_intensity, trailing versus drawing: coefficient 0.135 (95% CI 0.042 to 0.229); transformed estimate 1.145; n=2379 windows.
- primary_sequence_regain_5s, leading versus drawing: coefficient -0.086 (95% CI -0.231 to 0.060); transformed estimate 0.918; n=2054 windows.
- primary_sequence_regain_5s, trailing versus drawing: coefficient 0.231 (95% CI 0.080 to 0.382); transformed estimate 1.260; n=2054 windows.

Adjusted predictions are preserved for both contrasts and all three states:

| model_id | score_state | predicted_value | confidence_interval_lower | confidence_interval_upper | scale | adjusted_difference_from_drawing | adjusted_percentage_difference_from_drawing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary_pressing_intensity | leading | 6.991688776193475 | 6.588951965552768 | 7.394425586834181 | pressure_events_per_30_exposure_units | -0.2282132255576092 | -3.160890902705593 |
| primary_pressing_intensity | drawing | 7.219902001751084 | 6.879230818403608 | 7.56057318509856 | pressure_events_per_30_exposure_units | 0.0 | 0.0 |
| primary_pressing_intensity | trailing | 8.264586524183928 | 7.606836975089426 | 8.92233607327843 | pressure_events_per_30_exposure_units | 1.0446845224328438 | 14.469511112193366 |
| primary_sequence_regain_5s | leading | 0.1813451549368041 | 0.1650634285634844 | 0.1976268813101238 | probability | -0.0128890892806157 |  |
| primary_sequence_regain_5s | drawing | 0.1942342442174199 | 0.1819325884860951 | 0.2065358999487446 | probability | 0.0 |  |
| primary_sequence_regain_5s | trailing | 0.2323801824942066 | 0.2105760574545919 | 0.2541843075338214 | probability | 0.0381459382767867 |  |

Holm-adjusted primary-family inference is in `outputs/models/pressing_score_state/multiplicity_adjustment.json`. The Poisson model's dispersion was 1.603; because it exceeded the locked materiality threshold, the preregistered NB2 robustness model was executed without replacing the primary Poisson model.

## Secondary and exploratory results

Secondary models retain high-pressure share, pressure-sequence frequency, classic-PPDA components, event regain, counterpress share, high regains, mean pressure height, and post-regain shot production. Post-regain xG and xT are exploratory. Same-possession goal was explicitly unavailable because the required indicator was absent. Provider-augmented PPDA was retained only as an unavailable sensitivity entry, not promoted to inference.

## Robustness analyses

All 16 required groups were preserved, plus the triggered NB2 overdispersion analysis. Applicability failures remain explicit rather than being dropped.

| specification_group | execution_status | contrast_rows |
| --- | --- | --- |
| alternative_minimum_denominators | executed | 12 |
| event_level_regain | executed | 2 |
| event_level_regain | unavailable | 1 |
| exact_goal_difference | executed | 2 |
| exclude_extra_time | executed | 4 |
| exclude_red_card_affected | executed | 4 |
| group_stage_only | executed | 4 |
| homogeneous_state_segments | executed | 4 |
| knockout_only | executed | 4 |
| match_fixed_effects | executed | 4 |
| mixed_state_duration_proportions | executed | 4 |
| negative_binomial_overdispersion | executed | 2 |
| opponent_possession_count_exposure | executed | 2 |
| opponent_possession_count_exposure | unavailable | 1 |
| opponent_possession_seconds_exposure | executed | 2 |
| opponent_possession_seconds_exposure | unavailable | 1 |
| primary_five_minute_windows | executed | 4 |
| sequence_regain_3s | executed | 2 |
| sequence_regain_3s | unavailable | 1 |
| sequence_regain_8s | executed | 2 |
| sequence_regain_8s | unavailable | 1 |
| team_clustered_uncertainty | executed | 4 |

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
