# Data sources

## StatsBomb Open Data

- Source: <https://github.com/statsbomb/open-data>
- Primary competition: FIFA World Cup, male, 2022
- Expected resolved identifiers: competition 43, season 106
- Optional future xT reference: FIFA World Cup 2018, competition 43, season 3
- Access date and source commit: recorded at fetch time in `data/manifests/source.json`
- Transformations: canonical tables preserve provider identifiers, raw coordinates, metric
  coordinates, provider-normalized attacking coordinates, and selected nested attributes.
- Redistribution: raw JSON is not committed by default. Consult the source repository's
  licence and attribution language before redistribution.
- 360 limitation: event-linked freeze frames and visible-area polygons have incomplete and
  potentially selective coverage; they are not continuous tracking.
- Milestone 2 reference sample: FIFA World Cup 2018, resolved as competition 43/season 3 at
  the same pinned source revision. It trains reference xT and excludes every 2022 action.
