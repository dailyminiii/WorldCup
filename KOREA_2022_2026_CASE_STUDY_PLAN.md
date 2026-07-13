# Locked plan: Korea Republic 2022–2026 preliminary case study

## Scope and questions

This descriptive case study compares Korea Republic's three FIFA World Cup group-stage matches in 2022 with its three group-stage matches in 2026, subject to official-source verification. It asks about tournament outcomes, score-state exposure, comparable whole-match summaries, and the boundary of currently available tactical data. It contains no hypothesis test or causal estimand.

## Source hierarchy and verification

FIFA Match Centre, match reports, official timelines, official lineups, and official FIFA data records are primary. A national federation or documented reputable public data source may cross-check but never silently replace FIFA. Each imported field records source name, URL, UTC access time, source type, authority level, raw and normalized value, verification status, cross-check, and notes. Conflicts remain `conflicting`; absent fields remain null. Search snippets and undocumented/private endpoints are inadmissible final evidence.

## Locked common-metric rule

The primary comparison is the intersection of verified, definition-compatible whole-match or tournament outcomes. Candidate metrics are matches, wins, draws, losses, goals for/against, goal difference, points, score-state minutes/shares, shots, shots on target, possession, passes, pass completion, corners, fouls, cards, and substitutions. A candidate is included only when all six matches have verified values and definitions are sufficiently compatible. Metric selection is not changed according to which tournament looks stronger.

Pressure events/sequences, regain rates, PPDA, xG, xT, progressive actions, high-pressure share, post-regain value, and 360 context are unavailable for 2026 unless complete event-level sources are actually obtained and validated. Whole-match summaries are never allocated to score states.

## Inclusion and score-state reconstruction

Only Korea's three group-stage matches per tournament are eligible; the 2022 round-of-16 match is excluded. Score state is reconstructed from verified goal events using elapsed seconds and pre-event/post-event scores. A goal changes state once at its timestamp; own goals credit the benefiting team; shootout events are excluded. Regulation and observed stoppage time define match duration. Approximate timestamps remain flagged. Leading, drawing, and trailing seconds must sum to duration within one second.

## Missingness and source requirements

No missing value becomes zero. Unavailable official fields remain null and are excluded from complete aggregates. A statistic is verified only with a retrievable official URL or a permitted manually imported official record; secondary agreement is recorded separately. No raw copyrighted page is redistributed.

## Outputs and interpretation

Outputs comprise source inventories, canonical summaries, score-state exposure, metric-availability and unavailable-tactics tables, descriptive match/tournament comparisons, five deterministic figures, validation reports, a preliminary report, and a future StatsBomb 2026 availability adapter. Results are totals, per-match means, defensible per-90 values, ranges, and missingness. No p-values or inferential models are permitted. Wording is restricted to official summaries and descriptive differences; the extension cannot evaluate 2026 score-state-specific pressing or regain efficiency.

## Stopping rule

If three official 2026 group matches, final scores, and all goal timestamps cannot be verified, the pipeline stops at a source-audited partial template. It must not fabricate a complete comparison.
