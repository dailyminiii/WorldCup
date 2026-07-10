# Metric definitions

## `statsbomb_xg`

- Implementation version: `statsbomb_provider_xg_v1`
- Definition/formula: provider-supplied shot probability; team totals are sums over regular
  match shots. This repository does not train the model.
- Unit: expected goals.
- Eligible events: StatsBomb `Shot`; scoring `Own Goal For` records enter goal counts only.
- Exclusions: penalty shootouts and paired `Own Goal Against`; own goals have null xG.
- Coordinates/time: provider-normalized metric coordinates; cumulative match seconds.
- Source fields: `statsbomb_xg`, shot type/outcome, period, play pattern.
- Limitations: proprietary provider model and provider-specific event definition.
- Implementation/tests: `actions.xg`; `test_xg.py`, own-goal regression test.

## `xt_markov_v1`

- Definition/formula: probability of a possession eventually scoring from a 16 × 12 zone,
  estimated by a smoothed absorbing Markov move/shot model; action value is end xT minus
  start xT.
- Unit: expected possession goals.
- Eligible actions: successful passes, carries, and dribbles with valid endpoints.
- Exclusions: failed moves, shots, shootouts, and missing/invalid coordinates receive null
  with a reason code.
- Coordinates: acting team attacks left-to-right on 105 × 68 metres.
- Training: reference mode uses 2018 World Cup only and is out-of-sample for 2022.
  Tournament-only mode is explicitly `in_sample_exploratory: true`.
- Smoothing: documented Laplace smoothing, alpha 1.0. xT is not xG.
- Limitations: grid/smoothing/training-sample sensitivity and no defensive action value.
- Implementation/tests: `actions.xt`; `test_xt.py`.

## `progressive_goal_distance_v1`

- Formula: Euclidean distance reduction to `(105, 34)`. Inclusive (`>=`) thresholds are 30m
  within own half, 15m crossing halfway, and 10m within opponent half.
- Unit: action count; intermediate reduction in metres.
- Pass inclusion: successful open-play passes with valid endpoints.
- Pass exclusions: corners, throw-ins, free kicks, kick-offs, and goalkeeper restarts.
- Carry inclusion: successful carries/dribbles of 1–60 metres with valid endpoints.
- Limitations: thresholds are definition-dependent; representation changes under SPADL.
- Implementation/tests: `actions.progression`; `test_progression.py`.

## Entries and rates

- Final-third entry: action crosses from `x < 70` to `x >= 70` metres.
- Box entry: action ends at `x >= 88.5` and `13.84 <= y <= 54.16`, having started outside.
- Action counts count repeated entries; possession entry counts de-duplicate possession IDs.
- Rates retain explicit denominators. Counts and possession-normalized rates answer different
  questions and are never given interchangeable names.

