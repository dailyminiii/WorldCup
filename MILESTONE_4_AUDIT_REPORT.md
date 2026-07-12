# Milestone 4 independent audit report

## Audit conclusion

Milestone 4 satisfies its documented model-ready infrastructure acceptance criteria after the
fixes recorded below. The audit did not select a research question, filter estimates by
statistical significance, or create publication claims. Milestone 5 was not started.

The final validation is `valid: true`. A full Milestone 1 data validation plus Milestone 2–4
reproduction completed successfully. Two subsequent complete Milestone 4 runs produced
byte-identical checksums for all 79 files in the state-data, score-state model, report, and table
scope.

## Requirement-by-requirement evidence

| Requirement | Authoritative evidence | Result |
|---|---|---|
| Window and segment classic PPDA | `window_ppda_validation_2022.json`; 20,682/2,625 raw totals | Passed |
| Pressure excluded from classic PPDA | `CLASSIC_EVENTS`; synthetic regression test; leakage count 0 | Passed |
| Complete rate contract | `rate_contract_validation_2022.json`; missing fields 0 | Passed |
| Undefined rates remain null | final validation: zero-denominator non-null failures 0 | Passed |
| xT assignment and reconciliation | 110,546 eligible; unassigned 0; duplicated 0 | Passed |
| Progression assignment | 2,060 passes and 2,270 carries; unassigned/duplicated 0 | Passed |
| Passing style | 68,515 valid passes; versioned definitions and boundary tests | Passed |
| Descriptive summaries | 54 generated state/metric rows with pooled and unweighted fields | Passed |
| Continuous models | four clustered-OLS outcomes represented and executed | Passed |
| Proportion models | grouped binomial outcomes plus fractional possession logit | Passed |
| Unavailable substitution models | three explicit rows with required reasons | Passed |
| Fourteen robustness specifications | 14 IDs; 326 executed rows; 80 explicit unavailable rows | Passed |
| Match fixed effects where identifiable | two-way team/match design executed for 26 coefficient rows | Passed after fix |
| Deterministic outputs | 79-file checksum comparison, differing files 0 | Passed |
| Raw provider data not tracked | tracked raw path contains only `data/raw/README.md` | Passed |
| Observational wording | generated analysis and descriptive reports inspected | Passed |
| Complete quality gates | Ruff, format, strict Mypy, 53 pytest tests | Passed |

## Findings

### M4-A01 — High — offline reproduction attempted dependency resolution

- Affected file: `Makefile`
- Evidence: the first full reproduction stopped while trying to resolve `hatchling==1.27.0`
  from PyPI even though the pinned environment was already installed.
- Scientific consequence: a nominally local reproduction could fail for network reasons and
  leave only a partially refreshed output set.
- Fix: added `uv run --no-sync` to all non-setup Make targets.
- Fix applied: yes.
- Validation: `make validate-data milestone-2 milestone-3 milestone-4` completed offline.

### M4-A02 — High — robustness applicability and match fixed effects were misrepresented

- Affected files: `src/worldcup_strategy/models/score_state_models.py`,
  `src/worldcup_strategy/models/robustness.py`.
- Evidence: match fixed effects were previously marked unavailable without attempting a
  two-way design; raw-count and exposure-normalized specifications labeled unrelated model
  families as executed.
- Scientific consequence: the robustness matrix overstated execution and omitted an estimable
  adjustment, making its status metadata scientifically misleading.
- Fix: implemented two-way team/match fixed effects, executed identifiable cells, marked
  non-applicable family/specification cells unavailable, and added sign, magnitude-ratio, CI,
  and sample-size comparison fields.
- Fix applied: yes.
- Validation: match-fixed-effect rows now contain 26 executed coefficients; raw-count and
  exposure-normalized cells execute only for applicable families; unavailable cells remain.

### M4-A03 — Medium — reconciliation reports contained literal zero assertions

- Affected file: `src/worldcup_strategy/state/reporting.py`.
- Evidence: Pressure leakage and xT/progression assignment failures were written as literal
  zeros rather than derived from upstream definitions and totals.
- Scientific consequence: a future assignment regression could still produce a reassuring
  validation report.
- Fix: derive PPDA leakage membership and upstream/integrated differences from generated data.
- Fix applied: yes.
- Validation: PPDA totals reconcile 20,682/2,625; xT and progression duplicate/unassigned
  counts are zero against upstream tables.

### M4-A04 — Low — static documentation graphic embeds validated totals

- Affected file: `docs/assets/validated_metrics.svg`.
- Evidence: displayed metric totals are literal SVG text.
- Scientific consequence: the dashboard can become stale even while analytical tables remain
  correct.
- Recommended fix: generate the dashboard from validation JSON before publication work.
- Fix applied: no; this is a documentation asset outside the Milestone 4 analytical pipeline.
- Validation after fix: not applicable.

### M4-A05 — Low — PyArrow emits sandbox-specific hardware-cache warnings

- Affected component: local PyArrow runtime.
- Evidence: repeated `sysctlbyname` warnings during Parquet reads on macOS sandbox execution.
- Scientific consequence: none observed; commands completed and byte-level outputs matched.
- Recommended fix: document or suppress only this known runtime warning in a later tooling pass.
- Fix applied: no.
- Validation after fix: not applicable.

## Independent reconciliation

- SPADL actions: 125,566
- passes/carries/dribbles: 68,515 / 53,764 / 1,793
- regular shots/goals/xG: 1,453 / 172 / 155.8985419302
- xT-eligible actions/total xT: 110,546 / 278.8409161692973
- progressive passes/carries: 2,060 / 2,270
- Pressure events/sequences: 16,554 / 14,066
- event regains 3/5/8 seconds: 2,464 / 3,279 / 4,060
- sequence regains 3/5/8 seconds: 2,161 / 2,801 / 3,469
- substitutions/Tactical Shift: 587 / 243
- team windows/segments: 2,822 / 626

No synthetic rows were added to force these reconciliations.

## Remaining limitations

- Event-derived possession seconds are not tracking-derived ball-in-play time.
- Provider 360 coverage remains incomplete and potentially selective.
- Substitution intent is unavailable for 585 non-goalkeeper records because incoming positions
  are absent.
- Static dashboard values should be generated before any publication milestone.
- Model outputs are observational association infrastructure, not causal estimates.

## Final status

No critical or high-severity findings remain open. The branch may proceed to a separately
specified Milestone 5 only after a new explicit authorization.
