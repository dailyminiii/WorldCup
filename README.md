# World Cup Strategy Lab

Reproducible research infrastructure for the 2022 FIFA World Cup using StatsBomb Open
Data. Milestone 1 covers acquisition, provenance, canonical provider-independent tables,
coordinate/time normalization, validation, and coverage reporting. It intentionally does
not implement tactical metrics, qualification simulation, figures, or paper results.

```bash
UV_CACHE_DIR=.uv-cache ./.tools/uv/uv sync
make fetch-data
make build-data
make validate-data
make coverage
```

StatsBomb data is used under its published open-data terms and must be attributed as
described in [DATA_SOURCES.md](DATA_SOURCES.md). Raw data is local-only and Git-ignored.

