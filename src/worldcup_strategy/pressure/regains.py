# mypy: ignore-errors
# ruff: noqa: B023
"""Pressure-to-regain outcomes and high regains."""

import pandas as pd

DEAD_BALL = {
    "Half End",
    "Half Start",
    "Injury Stoppage",
    "Referee Ball-Drop",
    "Player Off",
    "Player On",
}
CONTROLLED = {"Pass", "Carry", "Ball Receipt*", "Dribble", "Shot", "Ball Recovery"}


def compute_pressure_regains(
    pressures: pd.DataFrame, sequences: pd.DataFrame, events: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = events.sort_values(["match_id", "period", "event_index"])
    rows = []
    for pressure in pressures.itertuples(index=False):
        future = events[
            (events.match_id == pressure.match_id)
            & (events.period == pressure.period)
            & (events.event_index > pressure.event_index)
            & (events.elapsed_seconds <= pressure.elapsed_seconds + 8)
        ]
        regain = future[
            (future.possession_team_id == pressure.team_id)
            & (future.team_id == pressure.team_id)
            & future.event_type.isin(CONTROLLED)
        ].head(1)
        dead = future[future.event_type.isin(DEAD_BALL)].head(1)
        foul = future[future.event_type == "Foul Committed"].head(1)
        out = future[(future.event_type == "Pass") & future.outcome.eq("Out")].head(1)
        boundary = pd.concat([dead, foul, out]).sort_values("event_index").head(1)
        if len(boundary) and (
            not len(regain) or boundary.iloc[0].event_index < regain.iloc[0].event_index
        ):
            regain = regain.iloc[0:0]
            if len(foul) and boundary.iloc[0].event_index == foul.iloc[0].event_index:
                reason = "foul_restart"
            elif len(out) and boundary.iloc[0].event_index == out.iloc[0].event_index:
                reason = "out_of_play"
            else:
                reason = "dead_ball_before_regain"
        elif len(regain):
            reason = "successful_regain"
        else:
            reason = "no_possession_change"
        delta = (
            float(regain.iloc[0].elapsed_seconds - pressure.elapsed_seconds)
            if len(regain)
            else None
        )
        rows.append(
            {
                "match_id": pressure.match_id,
                "event_id": pressure.event_id,
                "team_id": pressure.team_id,
                "opponent_id": pressure.opponent_id,
                "period": pressure.period,
                "pressure_seconds": pressure.elapsed_seconds,
                "regain_event_id": regain.iloc[0].event_id if len(regain) else None,
                "regain_seconds": regain.iloc[0].elapsed_seconds if len(regain) else None,
                "regain_delta_seconds": delta,
                "regain_3s": bool(delta is not None and delta <= 3),
                "regain_5s": bool(delta is not None and delta <= 5),
                "regain_8s": bool(delta is not None and delta <= 8),
                "regain_reason": reason,
                "regain_x_team_frame": regain.iloc[0].start_x_normalized if len(regain) else None,
                "regain_y_team_frame": regain.iloc[0].start_y_normalized if len(regain) else None,
            }
        )
    event_regains = pd.DataFrame(rows)
    high = (
        event_regains[event_regains.regain_8s]
        .drop_duplicates(["match_id", "regain_event_id"])
        .copy()
    )
    high["regain_type"] = "controlled_possession_change"
    high["is_high_regain"] = high.regain_x_team_frame >= 63
    high["preceded_by_pressure_3s"] = high.regain_3s
    high["preceded_by_pressure_5s"] = high.regain_5s
    high["preceded_by_pressure_8s"] = high.regain_8s
    high["preceded_by_pressure_sequence"] = high.apply(
        lambda r: bool(
            (
                (sequences.match_id == r.match_id)
                & (sequences.pressing_team_id == r.team_id)
                & (sequences.sequence_end_seconds <= r.regain_seconds)
                & (sequences.sequence_end_seconds >= r.regain_seconds - 8)
            ).any()
        ),
        axis=1,
    )

    event_lookup = {(row.match_id, row.event_id): row for row in events.itertuples(index=False)}
    possession_groups = {
        key: group
        for key, group in events.groupby(
            ["match_id", "period", "possession_id", "team_id"], sort=False
        )
    }

    def post_shot(row: pd.Series, seconds: float) -> bool:
        regained = event_lookup.get((row.match_id, row.regain_event_id))
        if regained is None:
            return False
        group = possession_groups.get(
            (row.match_id, row.period, regained.possession_id, row.team_id)
        )
        return bool(
            group is not None
            and (
                (group.event_type == "Shot")
                & (group.elapsed_seconds >= row.regain_seconds)
                & (group.elapsed_seconds <= row.regain_seconds + seconds)
            ).any()
        )

    high["resulted_in_shot_10s"] = high.apply(lambda row: post_shot(row, 10), axis=1)
    high["resulted_in_shot_15s"] = high.apply(lambda row: post_shot(row, 15), axis=1)

    def possession_xg(row: pd.Series) -> float | None:
        regained = event_lookup.get((row.match_id, row.regain_event_id))
        if regained is None:
            return None
        group = possession_groups.get(
            (row.match_id, row.period, regained.possession_id, row.team_id)
        )
        if group is None:
            return None
        values = group[group.event_type == "Shot"].statsbomb_xg
        return values.sum(min_count=1)

    high["same_possession_xg"] = high.apply(possession_xg, axis=1)
    high["same_possession_xt"] = pd.NA
    return event_regains, high


def sequence_regain_flags(sequences: pd.DataFrame, event_regains: pd.DataFrame) -> pd.DataFrame:
    output = sequences.copy()
    for window in (3, 5, 8):
        output[f"regain_{window}s"] = output.apply(
            lambda r: bool(
                (
                    (event_regains.match_id == r.match_id)
                    & (event_regains.team_id == r.pressing_team_id)
                    & (event_regains.regain_seconds >= r.sequence_end_seconds)
                    & (event_regains.regain_seconds <= r.sequence_end_seconds + window)
                ).any()
            ),
            axis=1,
        )
    return output
