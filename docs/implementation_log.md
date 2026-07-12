# Implementation log

## 2026-07-10 — Milestone 1 start

- Confirmed workspace-local uv 0.11.28 and uv-managed CPython 3.12.13.
- Updated the implementation plan to reflect the ready environment and authorized scope.
- Began repository contracts, dependency configuration, ingestion, validation, and tests.

## 2026-07-10 — Milestone 1 real-data validation

- Synced the pinned environment with `UV_CACHE_DIR=.uv-cache ./.tools/uv/uv sync`.
- Fetched official StatsBomb Open Data at commit
  `b0bc9f22dd77c206ddedc1d742893b3bbe64baec`.
- Resolved FIFA World Cup 2022 by name and asserted IDs 43/106.
- Built canonical competitions, matches, events, lineups, freeze-frame, and visible-area
  Parquet tables plus distinct team and player identity tables. Raw provider JSON and bulk
  generated tables remain Git-ignored.
- Observed 64 matches (48 group stage), 234,637 events, 64 lineup files, and 64 360 files.
  The 360 files link 203,882 events; coverage is stratified by match, team, event type, and
  tournament stage because missingness is not assumed random.
- Corrected group extraction after observing that the competition stage is `Group Stage`
  while group letters live under team metadata.
- Corrected paired StatsBomb own-goal handling: both provider records are flagged
  `is_own_goal`, but only `Own Goal For` is a scoring record, avoiding double counting.
- The PyArrow runtime emitted harmless sandbox `sysctlbyname` cache-detection warnings while
  reading Parquet. Reads and validation completed successfully.
- Final Milestone 1 quality gate: Ruff check passed, Ruff format check passed, strict Mypy
  passed for 11 source files, and all 16 pytest tests passed under CPython 3.12.13.

## 2026-07-10 — Milestone 2

- Added a project-owned SPADL-compatible action adapter over canonical StatsBomb events.
- Preserved original event IDs, provider raw coordinates, and normalized metric endpoints.
- Added provider xG extraction with shootout exclusion and paired-own-goal de-duplication.
- Added deterministic reference/tournament-only xT fitting, action valuation, provenance,
  and explicit null reasons. Reference mode resolves and trains only on World Cup 2018.
- Added `progressive_goal_distance_v1`, entry geometry, possession/count rates, and attacking
  summaries. No Milestone 3 functionality was introduced.

## 2026-07-10 — Milestone 3

- Added explicit possession/defending spatial frames with 180-degree opponent rotation.
- Implemented separately versioned classic and Pressure-augmented PPDA with raw components.
- Built StatsBomb Pressure events, two-second sequences, 3/5/8-second regain outcomes,
  provider counterpress labels, high-pressure and high-regain indicators.
- Built actor-aware event-linked 360 geometry and coverage tables without player identity
  requirements or off-camera imputation.
- Investigated three wrong-direction shot endpoints; all were isolated provider endpoint edge
  cases, so Milestone 1 orientation logic was not changed.

## 2026-07-13 — Milestone 4 continuation

- Built 2,822 period-local five-minute team windows. The right-closed boundary convention
  assigns an event at exactly 300 seconds once, to the preceding window; period-start events
  enter the first interval.
- Built 626 homogeneous team-perspective state segments (313 paired match segments), with
  172 goal, 3 red-card, and 138 period-start splits and no interval mismatch.
- Reconciled timestamp-assigned window and segment totals to 68,515 passes, 53,764 carries,
  1,793 dribbles, 1,453 regular shots, 172 goals, 155.8985419302 xG, 16,554 Pressure events,
  14,066 Pressure sequences, 587 substitutions, and 243 Tactical Shift events.
- Added non-causal pooled and unweighted score-state summaries.
- Added deterministic primary Poisson association models with match-clustered standard errors.
  The complete continuous-outcome and robustness grid remains pending and is reported as a
  limitation rather than represented as complete.
- The executable CLI reproduction completed for windows, segments, features, summaries,
  models, and validation. Ruff, strict Mypy, and 43 tests passed under Python 3.12.13.

## 2026-07-13 — Milestone 4 completion

- Extended both windows and segments with classic PPDA using the authoritative physical frame;
  totals reconcile to 20,682 opponent passes and 2,625 defensive actions, with zero provider
  Pressure leakage.
- Integrated 110,546 out-of-sample xT-eligible actions from the 2018 reference model, total xT
  278.8409161692973, 2,060 progressive passes, and 2,270 progressive carries.
- Added versioned passing direction, length, directness, possession-time, and complete
  numerator/denominator/reliability/reason contracts without zero-filling undefined rates.
- Executed 13 primary observational model families/outcomes: Poisson counts, clustered OLS,
  grouped binomial logits, and fractional logit. Three substitution specifications remain
  explicitly unavailable for evidence or estimability reasons.
- Represented all 14 robustness specifications. Estimable cells executed; match fixed effects
  are retained as unavailable because they are not identifiable with the paired team-window
  design and existing team effects.
- Generated the Milestone 4 completion and validation reports. Milestone 5 was not started.

## 2026-07-13 — Independent Milestone 4 audit

- Reproduced Milestone 1 data validation and the complete Milestone 2–4 pipeline offline.
- Fixed Make targets that incorrectly attempted dependency resolution during pinned local runs.
- Replaced literal zero validation assertions with upstream-versus-integrated reconciliation.
- Corrected the robustness matrix: two-way match fixed effects now execute where identifiable,
  and non-applicable raw-count/exposure-normalized model-family cells remain explicit rather
  than being mislabeled as executed.
- Added a synthetic end-to-end state-feature integration test spanning classic PPDA, Pressure,
  xT, progression, substitutions, Tactical Shift, and a right-closed boundary.
- Compared 79 generated state/model/report/table files across two complete Milestone 4 runs;
  every checksum matched.
- Recorded two low-severity open limitations: a static dashboard SVG contains literal display
  totals, and sandboxed PyArrow emits harmless hardware-cache detection warnings.
