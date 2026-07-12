# mypy: ignore-errors
"""Complete Milestone 4 interval feature and reliability contract."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from worldcup_strategy.pressure.frames import possession_frame
from worldcup_strategy.pressure.ppda import CLASSIC_EVENTS, EXCLUDED_PATTERNS, FRAME_VERSION

RATE_VERSION = "interval_rate_reliability_v1"
PASS_STYLE_VERSION = "pass_style_metric_coordinates_v1"
PPDA_VERSION = "ppda_classic_statsbomb_v1"


def assign_right_closed(records: pd.DataFrame, intervals: pd.DataFrame) -> pd.DataFrame:
    """Assign each eligible timestamp once; include period start in the first interval."""
    candidates = records.merge(
        intervals[
            ["match_id", "team_id", "period", "interval_start", "interval_end", "interval_key"]
        ],
        on=["match_id", "team_id", "period"],
        how="inner",
    )
    first = candidates.groupby(["match_id", "team_id", "period"])["interval_start"].transform("min")
    selected = candidates[
        (
            (candidates.elapsed_seconds > candidates.interval_start)
            | (
                candidates.interval_start.eq(first)
                & candidates.elapsed_seconds.eq(candidates.interval_start)
            )
        )
        & (candidates.elapsed_seconds <= candidates.interval_end)
    ]
    return selected.drop(columns=["interval_start", "interval_end"])


def _aggregate(result: pd.DataFrame, assigned: pd.DataFrame, column: str, values=None) -> None:
    grouped = (
        assigned.groupby("interval_key").size()
        if values is None
        else assigned.assign(_value=values).groupby("interval_key")._value.sum(min_count=1)
    )
    result[column] = result.interval_key.map(grouped).fillna(0)


def _rate(
    result: pd.DataFrame,
    metric: str,
    numerator,
    denominator,
    minimum: float,
    low_reason: str,
    multiplier: float = 1.0,
) -> None:
    numerator = pd.Series(numerator, index=result.index, dtype="float64")
    denominator = pd.Series(denominator, index=result.index, dtype="float64")
    result[f"{metric}_numerator"] = numerator
    result[f"{metric}_denominator"] = denominator
    result[metric] = (numerator / denominator * multiplier).where(denominator > 0)
    missing = denominator.isna()
    zero = denominator.eq(0)
    low = denominator.lt(minimum) & ~zero & ~missing
    result[f"{metric}_reliable"] = ~(missing | zero | low)
    result[f"{metric}_unreliable_reason"] = np.select(
        [missing, zero, low], ["missing_denominator", "zero_denominator", low_reason], default=None
    )


def _passing(result: pd.DataFrame, events: pd.DataFrame) -> None:
    passes = events[(events.event_type == "Pass") & events.period.isin([1, 2, 3, 4])].copy()
    passes["delta_x"] = passes.end_x_normalized - passes.start_x_normalized
    passes["pass_length"] = np.hypot(
        passes.end_x_normalized - passes.start_x_normalized,
        passes.end_y_normalized - passes.start_y_normalized,
    )
    assigned = assign_right_closed(passes, result)
    valid = assigned.pass_length.notna()
    masks = {
        "forward_passes": assigned.delta_x > 1.0,
        "backward_passes": assigned.delta_x < -1.0,
        "lateral_passes": assigned.delta_x.between(-1.0, 1.0, inclusive="both"),
        "long_passes": assigned.pass_length >= 30.0,
        "short_medium_passes": assigned.pass_length < 30.0,
    }
    for name, mask in masks.items():
        _aggregate(result, assigned[mask & valid], name)
    result["incomplete_passes"] = result.passes - result.completed_passes
    _aggregate(result, assigned[valid], "pass_length_sum", assigned.loc[valid, "pass_length"])
    _aggregate(result, assigned[valid], "pass_length_valid_count")
    median = assigned[valid].groupby("interval_key").pass_length.median()
    result["median_pass_length"] = result.interval_key.map(median)
    result["mean_pass_length"] = result.pass_length_sum / result.pass_length_valid_count.where(
        result.pass_length_valid_count > 0
    )
    forward_distance = assigned.loc[valid, "delta_x"].clip(lower=0)
    _aggregate(result, assigned[valid], "forward_distance_sum", forward_distance)
    result["pass_directness"] = result.forward_distance_sum / result.pass_length_sum.where(
        result.pass_length_sum > 0
    )
    result["pass_style_version"] = PASS_STYLE_VERSION


def _actions(result: pd.DataFrame, root: Path) -> None:
    spadl = pd.read_parquet(root / "actions/spadl_actions_2022.parquet")
    base = spadl.rename(columns={"period_id": "period", "time_seconds": "elapsed_seconds"})[
        ["match_id", "team_id", "period", "elapsed_seconds", "action_id"]
    ]
    xt = pd.read_parquet(root / "actions/action_xt_2022.parquet").merge(
        base, on=["match_id", "team_id", "action_id"], how="left", validate="one_to_one"
    )
    xa = assign_right_closed(xt[xt.period.isin([1, 2, 3, 4])], result)
    _aggregate(result, xa[xa.eligible_for_xt], "xt_eligible_actions")
    _aggregate(result, xa[~xa.eligible_for_xt], "xt_missing_actions")
    _aggregate(result, xa[xa.xt_missing_reason.eq("failed_action")], "xt_failed_actions")
    reason_counts = xa.groupby("interval_key").xt_missing_reason.apply(
        lambda values: json.dumps(
            values.fillna("eligible").value_counts().sort_index().to_dict(), sort_keys=True
        )
    )
    result["xt_missing_reason_counts"] = result.interval_key.map(reason_counts).fillna("{}")
    eligible = xa[xa.eligible_for_xt & xa.xt_added.notna()]
    _aggregate(result, eligible, "xt_added", eligible.xt_added)
    _aggregate(
        result,
        eligible[eligible.xt_added > 0],
        "positive_xt",
        eligible.loc[eligible.xt_added > 0, "xt_added"],
    )
    _aggregate(
        result,
        eligible[eligible.xt_added < 0],
        "negative_xt",
        eligible.loc[eligible.xt_added < 0, "xt_added"],
    )
    result["xt_model_version"] = xt.xt_model_version.dropna().iloc[0]
    result["xt_training_mode"] = xt.xt_training_mode.dropna().iloc[0]
    progression = pd.read_parquet(root / "actions/progression_actions_2022.parquet").merge(
        base, on=["match_id", "team_id", "action_id"], how="left", validate="one_to_one"
    )
    progressive = assign_right_closed(
        progression[progression.period.isin([1, 2, 3, 4]) & progression.is_progressive], result
    )
    for name, action_types in {
        "progressive_passes": ["pass"],
        "progressive_carries": ["carry"],
        "progressive_dribbles": ["dribble"],
    }.items():
        _aggregate(result, progressive[progressive.action_type.isin(action_types)], name)
    result["progressive_actions"] = (
        result.progressive_passes + result.progressive_carries + result.progressive_dribbles
    )
    result["progressive_definition_version"] = progression.progression_definition.dropna().iloc[0]


def _ppda(result: pd.DataFrame, events: pd.DataFrame) -> None:
    eligible = events[events.period.isin([1, 2, 3, 4])].copy()
    eligible["attacking_zone_x"] = [
        possession_frame(x, y, acting_team_id=int(team), possession_team_id=int(team))[0]
        if pd.notna(x) and pd.notna(y) and pd.notna(team)
        else np.nan
        for x, y, team in zip(
            eligible.start_x_normalized,
            eligible.start_y_normalized,
            eligible.team_id,
            strict=True,
        )
    ]
    passes = eligible[
        (eligible.event_type == "Pass")
        & ~eligible.play_pattern.isin(EXCLUDED_PATTERNS)
        & eligible.attacking_zone_x.between(0, 63)
    ].copy()
    passes["team_id"] = passes.apply(
        lambda row: int(
            result.loc[
                (result.match_id == row.match_id) & (result.team_id != row.team_id), "team_id"
            ].iloc[0]
        ),
        axis=1,
    )
    pa = assign_right_closed(passes, result)
    _aggregate(result, pa, "ppda_opponent_passes")
    duel_tackle = eligible.event_type.eq("Duel") & eligible.raw_event_json.str.contains(
        '"type":{"id":11,"name":"Tackle"}', regex=False
    )
    defensive = eligible[eligible.event_type.isin(CLASSIC_EVENTS) | duel_tackle].copy()
    opponents = result[["match_id", "team_id", "opponent_id"]].drop_duplicates()
    defensive = defensive.merge(opponents, on=["match_id", "team_id"], how="left")
    defensive["defending_zone_x"] = [
        possession_frame(x, y, acting_team_id=int(team), possession_team_id=int(opponent))[0]
        if pd.notna(x) and pd.notna(y) and pd.notna(team) and pd.notna(opponent)
        else np.nan
        for x, y, team, opponent in zip(
            defensive.start_x_normalized,
            defensive.start_y_normalized,
            defensive.team_id,
            defensive.opponent_id,
            strict=True,
        )
    ]
    defensive = defensive[defensive.defending_zone_x.between(0, 63)]
    da = assign_right_closed(defensive, result)
    _aggregate(result, da, "ppda_defensive_actions")
    _rate(
        result,
        "ppda_classic",
        result.ppda_opponent_passes,
        result.ppda_defensive_actions,
        1,
        "below_minimum_defensive_actions",
    )
    low_pass = result.ppda_opponent_passes < 5
    result.loc[low_pass & result.ppda_classic_reliable, "ppda_classic_reliable"] = False
    result.loc[low_pass & result.ppda_classic.notna(), "ppda_classic_unreliable_reason"] = (
        "below_minimum_opponent_passes"
    )
    result["ppda_missing_reason"] = result.ppda_classic_unreliable_reason.where(
        result.ppda_classic.isna()
    )
    result["ppda_reliable"] = result.ppda_classic_reliable
    result["ppda_definition_version"] = f"{PPDA_VERSION}|{FRAME_VERSION}"


def _possession_time(result: pd.DataFrame, events: pd.DataFrame) -> None:
    ordered = events[events.period.isin([1, 2, 3, 4])].sort_values(
        ["match_id", "period", "elapsed_seconds", "event_index"]
    )
    records = ordered[["match_id", "period", "elapsed_seconds", "possession_team_id"]].copy()
    next_time = ordered.groupby(["match_id", "period"]).elapsed_seconds.shift(-1)
    records["duration"] = (next_time - records.elapsed_seconds).clip(lower=0, upper=30)
    records = records.dropna(subset=["possession_team_id", "duration"]).rename(
        columns={"possession_team_id": "team_id"}
    )
    assigned = assign_right_closed(records, result)
    _aggregate(result, assigned, "possession_seconds", assigned.duration)


def complete_feature_contract(result: pd.DataFrame, root: Path) -> pd.DataFrame:
    """Add PPDA, action values, passing style, and versioned rate contracts."""
    result = result.drop(
        columns=["possession_seconds", "opponent_possession_seconds"], errors="ignore"
    )
    events = pd.read_parquet(root / "events_2022.parquet")
    _passing(result, events)
    _actions(result, root)
    _ppda(result, events)
    _possession_time(result, events)
    opponent = result[
        [
            "match_id",
            "team_id",
            "period",
            "interval_start",
            "interval_end",
            "passes",
            "possessions",
            "possession_seconds",
        ]
    ].rename(
        columns={
            "team_id": "opponent_id",
            "passes": "opponent_passes",
            "possessions": "opponent_possessions",
            "possession_seconds": "opponent_possession_seconds",
        }
    )
    result = result.merge(
        opponent,
        on=["match_id", "opponent_id", "period", "interval_start", "interval_end"],
        how="left",
        validate="one_to_one",
    )
    rate_specs = {
        "shots_per_effective_10min": (
            result.shots,
            result.effective_play_seconds,
            30,
            "below_minimum_effective_seconds",
            600,
        ),
        "xg_per_effective_10min": (
            result.statsbomb_xg,
            result.effective_play_seconds,
            30,
            "below_minimum_effective_seconds",
            600,
        ),
        "xt_per_effective_10min": (
            result.xt_added,
            result.effective_play_seconds,
            30,
            "below_minimum_effective_seconds",
            600,
        ),
        "xt_per_possession": (
            result.xt_added,
            result.possessions,
            2,
            "below_minimum_possessions",
            1,
        ),
        "progressive_passes_per_100_passes": (
            result.progressive_passes,
            result.passes,
            5,
            "below_minimum_passes",
            100,
        ),
        "progressive_carries_per_100_possessions": (
            result.progressive_carries,
            result.possessions,
            2,
            "below_minimum_possessions",
            100,
        ),
        "pass_completion_rate": (
            result.completed_passes,
            result.passes,
            5,
            "below_minimum_passes",
            1,
        ),
        "forward_pass_share": (
            result.forward_passes,
            result.pass_length_valid_count,
            5,
            "below_minimum_passes",
            1,
        ),
        "backward_pass_share": (
            result.backward_passes,
            result.pass_length_valid_count,
            5,
            "below_minimum_passes",
            1,
        ),
        "long_pass_share": (
            result.long_passes,
            result.pass_length_valid_count,
            5,
            "below_minimum_passes",
            1,
        ),
        "pressure_events_per_30_opponent_passes": (
            result.pressure_events,
            result.opponent_passes,
            5,
            "below_minimum_opponent_passes",
            30,
        ),
        "pressure_events_per_opponent_possession": (
            result.pressure_events,
            result.opponent_possessions,
            2,
            "below_minimum_possessions",
            1,
        ),
        "high_pressure_share": (
            result.high_pressure_events,
            result.pressure_events,
            3,
            "below_minimum_pressure_events",
            1,
        ),
    }
    result = result.copy()
    for index, (metric, spec) in enumerate(rate_specs.items(), start=1):
        _rate(result, metric, *spec)
        if index % 4 == 0:
            result = result.copy()
    _rate(
        result,
        "possession_share",
        result.possession_seconds,
        result.possession_seconds + result.opponent_possession_seconds,
        30,
        "below_minimum_effective_seconds",
    )
    for prefix, denominator in (
        ("pressure", result.pressure_events),
        ("sequence", result.pressure_sequences),
    ):
        for seconds in (3, 5, 8):
            _rate(
                result,
                f"{prefix}_regain_{seconds}s_rate",
                result[f"{prefix}_regains_{seconds}s"],
                denominator,
                3,
                "below_minimum_pressure_events",
            )
        result = result.copy()
    result["any_substitution"] = result.substitutions.gt(0).astype(int)
    result["rate_contract_version"] = RATE_VERSION
    return result
