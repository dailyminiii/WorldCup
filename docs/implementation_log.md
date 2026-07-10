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
