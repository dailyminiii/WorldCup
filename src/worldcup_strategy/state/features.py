# mypy: ignore-errors
"""Timestamp-based tactical feature integration for state intervals."""

from pathlib import Path

import numpy as np
import pandas as pd

from worldcup_strategy.state.feature_contract import complete_feature_contract

COUNT_COLUMNS = (
    "possessions",
    "passes",
    "completed_passes",
    "carries",
    "dribbles",
    "shots",
    "goals",
    "pressure_events",
    "pressure_sequences",
    "counterpress_events",
    "high_pressure_events",
    "pressure_regains_3s",
    "pressure_regains_5s",
    "pressure_regains_8s",
    "sequence_regains_3s",
    "sequence_regains_5s",
    "sequence_regains_8s",
    "substitutions",
    "goalkeeper_substitutions",
    "unknown_substitutions",
    "tactical_shifts",
)

VALUE_COLUMNS = ("statsbomb_xg", "non_penalty_xg", "open_play_xg", "set_piece_xg")


def _assign(records: pd.DataFrame, intervals: pd.DataFrame) -> pd.DataFrame:
    """Assign records by match, team, period, and right-closed timestamp."""
    candidates = records.merge(
        intervals[
            [
                "match_id",
                "team_id",
                "period",
                "interval_start",
                "interval_end",
                "interval_key",
            ]
        ],
        on=["match_id", "team_id", "period"],
        how="inner",
    )
    first_start = candidates.groupby(["match_id", "team_id", "period"])["interval_start"].transform(
        "min"
    )
    return candidates[
        (
            (candidates.interval_start < candidates.elapsed_seconds)
            | (
                candidates.interval_start.eq(first_start)
                & candidates.elapsed_seconds.eq(candidates.interval_start)
            )
        )
        & (candidates.elapsed_seconds <= candidates.interval_end)
    ].drop(columns=["interval_start", "interval_end"])


def integrate_features(
    intervals: pd.DataFrame, root: Path = Path("data/processed")
) -> pd.DataFrame:
    """Integrate auditable event features without match-only allocation."""
    result = intervals.copy()
    result["interval_key"] = np.arange(len(result))
    for column in COUNT_COLUMNS:
        result[column] = 0
    for column in VALUE_COLUMNS:
        result[column] = 0.0
    events = pd.read_parquet(root / "events_2022.parquet")
    event_records = events[
        [
            "match_id",
            "team_id",
            "period",
            "elapsed_seconds",
            "event_type",
            "outcome",
            "is_goal",
            "statsbomb_xg",
            "is_penalty",
            "is_set_piece",
            "possession_id",
        ]
    ].copy()
    assigned = _assign(event_records, result)
    definitions = {
        "passes": assigned.event_type.eq("Pass"),
        "completed_passes": assigned.event_type.eq("Pass") & assigned.outcome.isna(),
        "carries": assigned.event_type.eq("Carry"),
        "dribbles": assigned.event_type.eq("Dribble"),
        "shots": assigned.event_type.eq("Shot"),
        "goals": assigned.is_goal.fillna(False),
    }
    for name, mask in definitions.items():
        counts = assigned.loc[mask].groupby("interval_key").size()
        result[name] = result.interval_key.map(counts).fillna(0).astype(int)
    possession_counts = (
        assigned.dropna(subset=["possession_id"]).groupby("interval_key").possession_id.nunique()
    )
    result["possessions"] = result.interval_key.map(possession_counts).fillna(0).astype(int)
    shots = assigned[assigned.event_type.eq("Shot")]
    for name, mask in {
        "statsbomb_xg": pd.Series(True, index=shots.index),
        "non_penalty_xg": ~shots.is_penalty.fillna(False),
        "open_play_xg": ~shots.is_set_piece.fillna(False),
        "set_piece_xg": shots.is_set_piece.fillna(False),
    }.items():
        totals = shots.loc[mask].groupby("interval_key").statsbomb_xg.sum(min_count=1)
        result[name] = result.interval_key.map(totals).fillna(0.0)
    pressure = pd.read_parquet(root / "pressure/pressure_events_2022.parquet")
    pressure = pressure.rename(columns={"counterpress": "is_counterpress"})
    pa = _assign(pressure, result)
    for name, mask in {
        "pressure_events": pd.Series(True, index=pa.index),
        "counterpress_events": pa.is_counterpress.fillna(False),
        "high_pressure_events": pa.is_high_pressure.fillna(False),
    }.items():
        counts = pa.loc[mask].groupby("interval_key").size()
        result[name] = result.interval_key.map(counts).fillna(0).astype(int)
    regains = pd.read_parquet(root / "pressure/pressure_regains_2022.parquet").rename(
        columns={"pressure_seconds": "elapsed_seconds"}
    )
    ra = _assign(regains, result)
    for seconds in (3, 5, 8):
        counts = ra.loc[ra[f"regain_{seconds}s"]].groupby("interval_key").size()
        result[f"pressure_regains_{seconds}s"] = (
            result.interval_key.map(counts).fillna(0).astype(int)
        )
    sequences = pd.read_parquet(root / "pressure/pressure_sequences_2022.parquet").rename(
        columns={"pressing_team_id": "team_id", "sequence_start_seconds": "elapsed_seconds"}
    )
    sa = _assign(sequences, result)
    result["pressure_sequences"] = (
        result.interval_key.map(sa.groupby("interval_key").size()).fillna(0).astype(int)
    )
    for seconds in (3, 5, 8):
        counts = sa.loc[sa[f"regain_{seconds}s"]].groupby("interval_key").size()
        result[f"sequence_regains_{seconds}s"] = (
            result.interval_key.map(counts).fillna(0).astype(int)
        )
    for path, kind in (
        ("state/substitutions_2022.parquet", "sub"),
        ("state/tactical_shifts_2022.parquet", "shift"),
    ):
        records = pd.read_parquet(root / path)
        ca = _assign(records, result)
        if kind == "shift":
            counts = ca.groupby("interval_key").size()
            result["tactical_shifts"] = result.interval_key.map(counts).fillna(0).astype(int)
        else:
            for name, mask in {
                "substitutions": pd.Series(True, index=ca.index),
                "goalkeeper_substitutions": ca.substitution_classification.eq("goalkeeper"),
                "unknown_substitutions": ca.substitution_classification.eq("unknown"),
            }.items():
                counts = ca.loc[mask].groupby("interval_key").size()
                result[name] = result.interval_key.map(counts).fillna(0).astype(int)
    for seconds in (3, 5, 8):
        denominator = result.pressure_events.where(result.pressure_events > 0)
        result[f"pressure_regain_{seconds}s_rate"] = (
            result[f"pressure_regains_{seconds}s"] / denominator
        )
    return complete_feature_contract(result, root).drop(columns="interval_key")
