# mypy: ignore-errors
"""Construct locked pressing-analysis datasets and exclusion flows."""

import json
from pathlib import Path

import pandas as pd

from worldcup_strategy.state.feature_contract import assign_right_closed

ANALYSIS = Path("data/processed/analysis")
MODEL_ROOT = Path("outputs/models/pressing_score_state")
TABLES = Path("outputs/tables")
ALLOWED_STATES = {"leading", "drawing", "trailing"}


def _interval_view(frame: pd.DataFrame, unit: str) -> pd.DataFrame:
    if unit == "window":
        return frame.rename(
            columns={
                "window_start_seconds": "interval_start",
                "window_end_seconds": "interval_end",
            }
        )
    return frame.rename(
        columns={
            "segment_start_seconds": "interval_start",
            "segment_end_seconds": "interval_end",
            "score_state": "score_state_majority",
        }
    )


def _augment_pressure(frame: pd.DataFrame, unit: str) -> pd.DataFrame:
    intervals = _interval_view(frame, unit).copy()
    intervals["interval_key"] = range(len(intervals))
    pressure = pd.read_parquet("data/processed/pressure/pressure_events_2022.parquet")
    assigned = assign_right_closed(pressure, intervals)
    for column, function in (
        ("mean_pressure_height", "mean"),
        ("median_pressure_height", "median"),
    ):
        values = assigned.groupby("interval_key").x_pressing_team_frame.agg(function)
        intervals[column] = intervals.interval_key.map(values)
    high = pd.read_parquet("data/processed/pressure/high_regains_2022.parquet").rename(
        columns={"pressure_seconds": "elapsed_seconds"}
    )
    high_assigned = assign_right_closed(high, intervals)
    aggregations = {
        "high_regains": ("is_high_regain", "sum"),
        "shots_after_pressure_regain_10s": ("resulted_in_shot_10s", "sum"),
        "shots_after_pressure_regain_15s": ("resulted_in_shot_15s", "sum"),
        "xg_after_pressure_regains": ("same_possession_xg", "sum"),
        "xt_after_pressure_regains": ("same_possession_xt", "sum"),
    }
    for target, (source, function) in aggregations.items():
        values = high_assigned.groupby("interval_key")[source].agg(function)
        intervals[target] = intervals.interval_key.map(values).fillna(0)
    intervals["counterpress_share"] = (
        intervals.counterpress_events
        / intervals.pressure_events.where(intervals.pressure_events > 0)
    )
    intervals["high_regain_rate"] = intervals.high_regains / intervals.pressure_regains_5s.where(
        intervals.pressure_regains_5s > 0
    )
    return intervals.drop(columns="interval_key")


def _metadata(frame: pd.DataFrame) -> pd.DataFrame:
    matches = pd.read_parquet("data/processed/matches_2022.parquet")
    metadata = matches[["match_id", "competition_stage", "match_week", "group_name"]]
    output = frame.merge(metadata, on="match_id", how="left", validate="many_to_one")
    if "multiple_score_states" not in output:
        output["multiple_score_states"] = False
    if "multiple_numerical_states" not in output:
        output["multiple_numerical_states"] = False
    output["group_matchday"] = output.match_week.where(
        output.competition_stage.eq("Group Stage"), 0
    )
    output["stage_group"] = output.competition_stage.where(
        output.competition_stage.eq("Group Stage"), "Knockout"
    )
    output["match_minute"] = (output.interval_start + output.interval_end) / 120
    output["match_minute_centered"] = output.match_minute - 45
    output["match_minute_centered_squared"] = output.match_minute_centered**2
    output["valid_score_state"] = output.score_state_majority.isin(ALLOWED_STATES)
    output["regular_period"] = output.period.isin([1, 2])
    output["numerically_equal"] = (
        (
            output.red_card_difference_start.eq(0)
            & output.red_card_difference_end.eq(0)
            & ~output.multiple_numerical_states
        )
        if "red_card_difference_start" in output
        else (
            output.red_card_difference.eq(0)
            & output.numerical_state.astype(str).str.startswith("even")
        )
    )
    output["common_primary_eligible"] = (
        output.regular_period
        & output.valid_score_state
        & output.numerically_equal
        & ~output.multiple_score_states
    )
    output["intensity_primary_eligible"] = (
        output.common_primary_eligible
        & output.opponent_passes.notna()
        & output.opponent_passes.ge(5)
    )
    output["efficiency_primary_eligible"] = (
        output.common_primary_eligible
        & output.pressure_sequences.notna()
        & output.pressure_sequences.ge(3)
        & output.sequence_regains_5s.le(output.pressure_sequences)
    )
    return output


def _flow(frame: pd.DataFrame, outcome: str) -> list[dict[str, object]]:
    current = pd.Series(True, index=frame.index)
    rows = [{"outcome": outcome, "step": "initial_windows", "excluded": 0, "remaining": len(frame)}]
    rules = [
        ("exclude_extra_time", frame.regular_period),
        ("exclude_invalid_score_state", frame.valid_score_state),
        ("exclude_numerical_inequality", frame.numerically_equal),
        ("exclude_mixed_score_state", ~frame.multiple_score_states),
    ]
    if outcome == "pressing_intensity":
        rules.extend(
            [
                ("exclude_missing_opponent_passes", frame.opponent_passes.notna()),
                ("exclude_opponent_passes_below_5", frame.opponent_passes.ge(5)),
            ]
        )
    else:
        rules.extend(
            [
                ("exclude_invalid_sequence_trials", frame.pressure_sequences.notna()),
                ("exclude_sequences_below_3", frame.pressure_sequences.ge(3)),
                (
                    "exclude_successes_above_trials",
                    frame.sequence_regains_5s.le(frame.pressure_sequences),
                ),
            ]
        )
    for step, keep in rules:
        excluded = int((current & ~keep.fillna(False)).sum())
        current &= keep.fillna(False)
        rows.append(
            {
                "outcome": outcome,
                "step": step,
                "excluded": excluded,
                "remaining": int(current.sum()),
            }
        )
    return rows


def prepare_analysis() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build analysis-ready windows, segments, secondary features, and flow artifacts."""
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    windows = _metadata(
        _augment_pressure(
            pd.read_parquet("data/processed/state/team_window_features_2022.parquet"),
            "window",
        )
    )
    segments = _metadata(
        _augment_pressure(
            pd.read_parquet("data/processed/state/team_segment_features_2022.parquet"),
            "segment",
        )
    )
    windows.to_parquet(ANALYSIS / "pressing_primary_windows_2022.parquet", index=False)
    segments.to_parquet(ANALYSIS / "pressing_primary_segments_2022.parquet", index=False)
    windows.to_parquet(ANALYSIS / "pressing_secondary_2022.parquet", index=False)
    flow = pd.DataFrame(
        [*_flow(windows, "pressing_intensity"), *_flow(windows, "sequence_regain_efficiency")]
    )
    flow.to_csv(TABLES / "pressing_exclusion_flow_2022.csv", index=False)
    (MODEL_ROOT / "exclusion_flow.json").write_text(
        json.dumps(flow.to_dict("records"), indent=2) + "\n"
    )
    return windows, segments, flow
