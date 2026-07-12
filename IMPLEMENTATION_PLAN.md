# World Cup Strategy Lab implementation plan

## Current-state inspection

- Inspection date: 2026-07-10 (Asia/Seoul).
- The workspace began with this implementation plan and environment configuration; there is no prior analytical implementation to preserve.
- Git 2.50.1 is available and the repository is initialized on `main`.
- A workspace-local `uv` 0.11.28 executable provisions CPython 3.12.13. Project commands set `UV_CACHE_DIR=.uv-cache`; the system Python 3.9 is never used.
- No StatsBomb Open Data checkout is present. Dataset counts and coverage must therefore be discovered after the environment and source data are available; they will not be fabricated.

## Assumptions

1. StatsBomb Open Data is the only provider used for the 2022 implementation.
2. Competition and season are resolved from `competitions.json`; IDs 43/106 (2022) and 43/3 (2018 reference) are assertions, not lookup keys.
3. Raw provider files remain local and Git-ignored. Only small, legally redistributable synthetic fixtures are committed by default.
4. All stochastic workflows use seed `20262022` unless configuration explicitly overrides it.
5. Null analytical values remain null and carry a reason code where a metric cannot be computed.
6. The 2018 reference xT mode is the default publishable mode. A 2022-only fit is labelled exploratory and in-sample in every derived artifact.
7. StatsBomb 360 is event-linked freeze-frame context, not continuous tracking.
8. Qualification snapshots use only information observable at the snapshot timestamp. Final-matchday matches with the same kickoff are advanced jointly.

## Unresolved choices

- Exact StatsBomb Open Data source commit SHA and actual Event/360 coverage (requires a local checkout or network fetch).
- Whether derived aggregate outputs may be committed under the user's intended distribution policy.
- Effective-play-time convention for team windows beyond the supplied defaults.
- Pre-tournament strength prior source; the baseline will use a documented neutral prior until an external provider is configured.
- Future-card model calibration when pre-snapshot samples are sparse.
- LaTeX engine availability in the target environment.

## Risks and safeguards

| Risk | Safeguard |
|---|---|
| Future-information leakage | Timestamp-bounded strength updates, immutable completed/current states, and counterfactual regression tests. |
| Incorrect FIFA tiebreak recursion | Criterion-block implementation with partially resolved multi-team regression cases. |
| Goal-event off-by-one | Separate before/after state and synthetic own-goal, penalty, and shootout tests. |
| Direction errors | Explicit team-period direction map with null preservation and involution tests. |
| In-sample xT mislabelling | Required training-mode metadata propagated to models, actions, tables, and captions. |
| PPDA construct conflation | Versioned mappings; `Pressure` excluded from classic and included only in the named augmented variant. |
| Biased 360 analysis | Match/team/type/stage coverage tables and complete-case reason codes; no off-camera imputation. |
| Missing values becoming zero | Nullable schemas and validation tests at every aggregation boundary. |
| Non-determinism | Explicit NumPy generators, stable sorting, seed/config manifests, and byte-level regression checks where practical. |
| Manual paper results | Generated tables/macros and figure manifests tied to processed source files. |
| Raw data committed | `.gitignore`, provenance docs, and tracked-file validation. |

## Milestones

1. **Milestone 1 — repository, contracts, and ingestion** — metadata, dependency lock, configuration, provider-independent schemas, provenance documents, CLI, source resolution, checksums/manifests, canonical Event/360 conversion, coverage reports, schema validation, and unit/integration tests.
2. **Milestone 2 — action metrics** — xG aggregation, SPADL adapter, reference/tournament-only xT, progression, and metric definitions.
3. **Milestone 3 — pressure and context** — classic and augmented PPDA, pressure/regain metrics, and coverage-aware 360 features.
4. **Milestone 4 — state reconstruction** — event before/after score and discipline state, team windows, and observational association models.
5. **Milestone 5 — qualification engine** — official 2022 rules, leak-free snapshots, seeded joint simulations, fair-play/lot diagnostics, and final-table validation.
6. **Milestone 6 — reporting** — generated figures/tables/manifests and a claim-conservative LaTeX scaffold.
7. **Final reproduction and audit** — unit/integration/regression tests, Ruff, Mypy, data validation, reduced simulation, complete reproduction, tracked-raw-data scan, and audit artifacts.

## Validation cadence

After each milestone, run the narrow tests for changed modules, followed by `ruff check`, `ruff format --check`, and `mypy src` when those tools become available. Before completion run `make test`, `make lint`, `make typecheck`, `make validate-data`, a reduced qualification simulation, `make reproduce`, and the paper build. Every command and failure is recorded in `docs/implementation_log.md` and the run manifest.

## Completion rule

No acceptance criterion is reported as complete without a generated artifact or test result. Environment, source-data, dependency, or coverage gaps remain explicit limitations.

## Milestone 2 implementation (authorized 2026-07-10)

1. Add versioned action, shot-xG, xT, progression, and attacking-summary contracts.
2. Convert canonical StatsBomb events through a project-owned SPADL-compatible adapter,
   retaining provider IDs/coordinates and validating team-period orientation empirically.
3. Aggregate provider-supplied StatsBomb xG with shootout exclusion and paired-own-goal
   de-duplication.
4. Fit deterministic 16 × 12 Markov xT grids in reference (2018) and explicitly exploratory
   tournament-only modes; persist training provenance and null reason codes.
5. Apply `progressive_goal_distance_v1` with inclusive threshold boundaries and configurable
   set-piece/carry exclusions.
6. Produce count and rate-separated team-match and tournament attacking summaries.
7. Run synthetic unit/integration tests, real 2018/2022 CLI reproduction, artifact inspection,
   and the full Milestone 1 quality gate before committing generated small reports.

Milestone 2 explicitly excludes pressure/PPDA, score-state models, qualification simulation,
publication figures, and paper results.

## Milestone 3 implementation (authorized 2026-07-10)

1. Investigate every shot-orientation exception without changing normalization absent a
   demonstrated systematic error.
2. Add explicit acting, possession, and defending-team spatial frames using 180-degree
   opponent rotation on the 105 × 68 pitch.
3. Implement `ppda_classic_statsbomb_v1` and separately labeled
   `ppda_pressure_augmented_statsbomb_v1` with raw components and null reasons.
4. Build provider Pressure events, two-second same-possession sequences, 3/5/8-second regain
   outcomes, provider counterpress labels, and high-regain indicators.
5. Derive event-linked 360 geometry without player identities or off-camera imputation, and
   report coverage/eligibility rather than treating freeze frames as tracking.
6. Produce team-match/tournament summaries, validation reports, tests, and CLI reproduction.

Milestone 3 excludes score-state models, qualification simulation, publication figures, and
paper results.

## Milestone 4 continuation status (2026-07-13)

- [x] Symmetric event-level score and discipline state.
- [x] Period-local right-closed five-minute windows with stoppage and extra time.
- [x] Goal/red-card/period homogeneous state segments.
- [x] Timestamp-based core attacking, Pressure, regain, substitution, and Tactical Shift joins.
- [x] Pooled and unweighted non-causal descriptive summaries.
- [x] Deterministic primary Poisson count associations with match-clustered uncertainty.
- [x] CLI and Make entry points for the executable state pipeline.
- [x] Complete the full feature/rate contract, including interval PPDA, xT, progression, and style.
- [x] Execute continuous, proportion, unavailable-substitution, and all robustness specifications.
- [x] Add boundary, reliability, passing-style, model-family, and determinism regression tests.

Milestone 4 completed on 2026-07-13 after generated-data reconciliation, 14-specification
robustness execution, full quality gates, and an explicit unavailable-model audit. Milestone 5
was not started.
