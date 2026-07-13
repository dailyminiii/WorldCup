# Pressing the Scoreline: Pressing Intensity and Regain Efficiency Across Match States in the 2022 FIFA World Cup

Internal complete draft v1. Citation placeholders remain unresolved; this manuscript is not submission-ready.

## Abstract

Pressing frequency, pressure-to-regain efficiency, and post-regain value are different tactical constructs. This observational study separates them in the 2022 FIFA World Cup. The primary unit is a team–match five-minute window. A Poisson model relates score state to Pressure-event counts with opponent passes as exposure, while a grouped-binomial model relates score state to controlled regains within five seconds per Pressure sequence. Both include time, tournament context, and team fixed effects with match-clustered uncertainty. Relative to drawing, trailing was associated with higher Pressure intensity (IRR 1.145) and higher regain odds (OR 1.260). Leading estimates were smaller and negative (IRR 0.968; OR 0.918). These tournament-specific estimates do not identify a mechanism.

## 1. Introduction

Football tactics unfold under time-varying match context. Score state is especially visible, but it emerges from the same competitive process that shapes subsequent behavior. Comparisons of leading, drawing, and trailing are therefore observational. Pressing is multidimensional: many Pressure actions may form fewer episodes, episodes may convert into controlled possession at different rates, and successful regains may create different attacking value.

This study contributes an integrated, denominator-aware operationalization. It separates Pressure-event intensity, sequence-level regain efficiency, and secondary post-regain production; distinguishes provider Pressure from classic PPDA; compares fixed windows with homogeneous segments; and preserves alternative denominators and clustering choices. RQ1 asks how intensity and height are conditionally associated with score state. RQ2 asks how five-second sequence regain efficiency is conditionally associated with state. RQ3, secondary or exploratory, asks how post-regain value varies across states.

## 2. Related work

The structured review covers score state and tactical behavior, PPDA, provider Pressure annotations, regain and counterpressing definitions, game-state endogeneity, event-linked freeze frames, and reproducibility. All eight literature citations remain explicit verification placeholders in `CITATIONS_TO_VERIFY.md`; no author, venue, year, or DOI has been invented.

## 3. Data

StatsBomb Open Data at the recorded provider commit supplies 64 matches, 32 teams, and 234,637 canonical events. There are 203,882 event-linked 360 records; 14,504 of 16,554 Pressure events have linked frames. Freeze frames show visible event-linked context, not continuous tracking. Raw provider JSON is not tracked.

Coordinates are normalized to a provider-independent pitch and attacking-team frame, symmetrically by side and period. Penalty shootouts and extra time are excluded from primary analysis. Own goals update the benefiting team's score while retaining provider identity. The primary source contains 2822 windows. Mixed-state, numerically unequal, extra-time, invalid-state, and unreliable-denominator windows are excluded through a reconciled flow.

## 4. Methods

Intensity uses Pressure-event counts with `log(opponent_passes)` offset in a Poisson model and requires at least five opponent passes. Material dispersion (1.603) triggers a preregistered NB2 robustness model without replacing the primary model. Classic PPDA uses eligible defensive actions and retains its inverse interpretation; it is not treated as a Pressure-event rate.

Efficiency uses two-second Pressure episodes and controlled regains within five seconds. Successes are sequence regains and trials are Pressure sequences, with at least three trials. A grouped-binomial logit model is used. Both primary models adjust for centered minute, its square, stage, group matchday, and team fixed effects, with match-clustered uncertainty and drawing as reference. Holm adjustment covers the two primary families.

Secondary outcomes include high-pressure share, Pressure-sequence frequency, classic PPDA components, event-level regain, three- and eight-second sequence regains, and post-regain shots. xG and xT per successful regain are exploratory. Missing opportunity values remain missing rather than zero.

## 5. Results

The intensity model retains 2379 windows; efficiency retains 2054, covering all 64 matches and 32 teams. Pooled Pressure rates per 30 opponent passes are 7.143, 7.157, and 7.404 for leading, drawing, and trailing. Unweighted means are 7.708, 8.009, and 8.980, demonstrating why pooled and equal-window summaries must remain separate.

Trailing versus drawing has intensity IRR 1.145 (coefficient 0.135, 95% CI 0.042 to 0.229). Predictions are 8.265 versus 7.220 Pressure events per 30 opponent passes. Leading versus drawing has IRR 0.968 (coefficient -0.032, 95% CI -0.103 to 0.038), with predictions 6.992 versus 7.220.

Trailing versus drawing has sequence-regain OR 1.260 (coefficient 0.231, 95% CI 0.080 to 0.382). Predicted probabilities are 0.232 and 0.194. Leading versus drawing has OR 0.918 (coefficient -0.086, 95% CI -0.231 to 0.060), with probabilities 0.181 and 0.194. Holm-adjusted values are 0.005 and 0.005 for trailing and 0.497 and 0.497 for leading.

Secondary event-level and high-pressure-share results provide measurement context but are not promoted to confirmatory findings. Post-regain shots are secondary; xG and xT are exploratory; goal conversion and provider-augmented PPDA remain explicitly unavailable for their stated reasons.

## 6. Robustness

All 16 planned groups are preserved, plus the triggered NB2 model. They cover homogeneous segments, duration-weighted mixed states, complete red-card exclusion, stage subsets, extra-time exclusion, denominator thresholds, possession count and time exposure, event-level regain, three- and eight-second windows, team clustering, match fixed effects, and exact goal difference. Interpretation considers direction, magnitude, interval width, sample change, convergence, and changed estimand. Inapplicable combinations remain unavailable rather than disappearing.

## 7. Discussion

Trailing was conditionally associated with both more frequent Pressure activity and higher estimated sequence conversion. Their coexistence matters because they use different opportunity sets. Tactical urgency, opponent protection, field position, commitment, and opportunity selection are hypotheses, not observed mechanisms. Leading contrasts were smaller and negative, but their uncertainty does not establish equivalence.

For practice, analysts should monitor activity, episode conversion, and subsequent value separately. A frequent press need not be efficient, and an efficient regain need not yield a valuable attack. Future work may study dynamic qualification pressure in the 2026 format, but this draft contains no 2026 simulation or result.

## 8. Limitations

Limitations include observational score-state exposure, endogeneity and reverse temporal ordering, simultaneous opponent response, one-tournament scope, national-team heterogeneity, provider-defined Pressure, two-second sequence and five-second regain choices, event-derived opportunity measures, denominator sensitivity, incomplete 360 coverage, lack of continuous tracking, unobserved tactical context, incomplete within-match control from team fixed effects, 64-match clustered uncertainty, one-column nuisance rank deficiency, non-uniform residual diagnostics across robustness variants, limited external generalization, and weaker effective samples for post-regain outcomes. Secondary analyses are not covered by primary Holm adjustment.

## 9. Conclusion

The study finds tournament-specific conditional associations between trailing and higher pressing activity and regain efficiency, while leading contrasts are smaller and negative. Its principal contribution is a reproducible framework that keeps intensity, conversion, and post-regain value distinct and makes denominator and robustness choices visible.
