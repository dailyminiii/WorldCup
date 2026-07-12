# mypy: ignore-errors
"""Diagnose Pressure events assigned to the pressing team's possession."""

import pandas as pd


def diagnose_pressure_possession_alignment(
    events: pd.DataFrame, pressures: pd.DataFrame, sequences: pd.DataFrame, regains: pd.DataFrame
) -> pd.DataFrame:
    ordered = events.sort_values(["match_id", "period", "event_index"])
    previous = ordered.groupby("match_id").shift(1)
    following = ordered.groupby("match_id").shift(-1)
    event_index = ordered.set_index(["match_id", "event_id"])
    previous.index = ordered.index
    following.index = ordered.index
    sequence_events = {}
    for s in sequences.itertuples(index=False):
        members = pressures[
            (pressures.match_id == s.match_id)
            & (pressures.team_id == s.pressing_team_id)
            & (pressures.possession_id == s.possession_id)
            & (pressures.period == s.period)
            & (pressures.elapsed_seconds.between(s.sequence_start_seconds, s.sequence_end_seconds))
        ]
        for i, event_id in enumerate(members.event_id):
            sequence_events[(s.match_id, event_id)] = (
                s.pressure_sequence_id,
                i == 0,
                i == len(members) - 1,
            )
    regain_map = regains.set_index(["match_id", "event_id"])
    rows = []
    affected = pressures[pressures.team_id == pressures.possession_team_id]
    for p in affected.itertuples(index=False):
        raw = event_index.loc[(p.match_id, p.event_id)]
        idx = (
            raw.name
            if isinstance(raw.name, int)
            else ordered[(ordered.match_id == p.match_id) & (ordered.event_id == p.event_id)].index[
                0
            ]
        )
        prev = previous.loc[idx]
        nxt = following.loc[idx]
        prev_change = (
            pd.notna(prev.possession_team_id)
            and prev.possession_team_id != p.possession_team_id
            and p.elapsed_seconds - prev.elapsed_seconds <= 2
        )
        next_change = (
            pd.notna(nxt.possession_team_id)
            and nxt.possession_team_id != p.possession_team_id
            and nxt.elapsed_seconds - p.elapsed_seconds <= 2
        )
        seq = sequence_events.get((p.match_id, p.event_id), (None, False, False))
        regain = (
            regain_map.loc[(p.match_id, p.event_id)]
            if (p.match_id, p.event_id) in regain_map.index
            else None
        )
        classification = (
            "counterpress_after_turnover"
            if p.counterpress and prev_change
            else "provider_possession_boundary"
            if prev_change or next_change
            else "same_timestamp_transition"
            if (pd.notna(prev.elapsed_seconds) and p.elapsed_seconds == prev.elapsed_seconds)
            or (pd.notna(nxt.elapsed_seconds) and p.elapsed_seconds == nxt.elapsed_seconds)
            else "administrative_possession_assignment"
            if prev.event_type in {"Half Start", "Referee Ball-Drop"}
            else "ambiguous_provider_representation"
        )
        rows.append(
            {
                "match_id": p.match_id,
                "event_id": p.event_id,
                "event_index": p.event_index,
                "period": p.period,
                "elapsed_seconds": p.elapsed_seconds,
                "team_id": p.team_id,
                "possession_id": p.possession_id,
                "possession_team_id": p.possession_team_id,
                "counterpress": p.counterpress,
                "play_pattern": p.play_pattern,
                "start_x": p.start_x,
                "start_y": p.start_y,
                "previous_event_id": prev.event_id,
                "previous_event_type": prev.event_type,
                "previous_event_team_id": prev.team_id,
                "previous_possession_id": prev.possession_id,
                "previous_possession_team_id": prev.possession_team_id,
                "previous_event_time_gap_seconds": p.elapsed_seconds - prev.elapsed_seconds,
                "next_event_id": nxt.event_id,
                "next_event_type": nxt.event_type,
                "next_event_team_id": nxt.team_id,
                "next_possession_id": nxt.possession_id,
                "next_possession_team_id": nxt.possession_team_id,
                "next_event_time_gap_seconds": nxt.elapsed_seconds - p.elapsed_seconds,
                "possession_changed_within_previous_2s": bool(prev_change),
                "possession_changed_within_next_2s": bool(next_change),
                "pressure_sequence_id": seq[0],
                "is_sequence_start": seq[1],
                "is_sequence_end": seq[2],
                "regain_3s": bool(regain.regain_3s) if regain is not None else False,
                "regain_5s": bool(regain.regain_5s) if regain is not None else False,
                "regain_8s": bool(regain.regain_8s) if regain is not None else False,
                "diagnostic_classification": classification,
            }
        )
    return pd.DataFrame(rows)
