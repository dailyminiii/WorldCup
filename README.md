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

## Milestone 2 reproduction

```bash
make actions
make xg
make xt
make progression
make attacking-summary
# or: make milestone-2
```

The action representation is SPADL-compatible but project-owned: conversion changes the
provider event representation while retaining original event IDs and raw coordinates.
Reference xT is fitted only on the 2018 World Cup and then applied to 2022.

## Milestone 3 reproduction

```bash
make ppda
make pressure-events
make pressure-regains
make context360
make pressure-summary
# or: make milestone-3
```

Classic PPDA and the StatsBomb Pressure-augmented project variant are deliberately separate.
All 360 outputs describe event-linked visible context, never continuous tracking.
