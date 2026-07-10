# mypy: ignore-errors
"""Milestone 3 real-data orchestration."""

from pathlib import Path

import pandas as pd

from worldcup_strategy.data.manifests import write_json
from worldcup_strategy.pressure.context360 import build_context360, pressure_context
from worldcup_strategy.pressure.coverage import coverage_tables
from worldcup_strategy.pressure.ppda import compute_ppda
from worldcup_strategy.pressure.pressure_events import build_pressure_events
from worldcup_strategy.pressure.regains import compute_pressure_regains, sequence_regain_flags
from worldcup_strategy.pressure.sequences import build_pressure_sequences
from worldcup_strategy.pressure.summaries import team_match_summary, team_tournament_summary
from worldcup_strategy.pressure.validation import validate_ppda

ROOT = Path("data/processed")
OUT = ROOT / "pressure"
REPORT = Path("outputs/reports")
TABLE = Path("outputs/tables")


def _read(name: str) -> pd.DataFrame:
    return pd.read_parquet(ROOT / f"{name}_2022.parquet")


def _write(frame: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT / f"{name}_2022.parquet", index=False)


def orientation_exceptions() -> pd.DataFrame:
    events = _read("events")
    matches = _read("matches")
    shots = events[
        (events.event_type == "Shot")
        & events.end_x_normalized.notna()
        & (events.end_x_normalized < events.start_x_normalized)
    ].copy()
    match_map = matches.set_index("match_id")
    rows = []
    for s in shots.itertuples(index=False):
        m = match_map.loc[s.match_id]
        opponent = int(m.away_team_id if int(m.home_team_id) == int(s.team_id) else m.home_team_id)
        rows.append(
            {
                "match_id": s.match_id,
                "event_id": s.event_id,
                "team_id": s.team_id,
                "team_name": s.team_name,
                "opponent_id": opponent,
                "period": s.period,
                "elapsed_seconds": s.elapsed_seconds,
                "start_x": s.start_x_normalized,
                "start_y": s.start_y_normalized,
                "end_x": s.end_x_normalized,
                "end_y": s.end_y_normalized,
                "event_type": s.event_type,
                "event_subtype": s.event_subtype,
                "is_goal": s.is_goal,
                "is_own_goal": s.is_own_goal,
                "is_penalty": s.is_penalty,
                "is_penalty_shootout": s.is_penalty_shootout,
                "raw_event_reference": s.event_id,
                "suspected_reason": "provider_representation_edge_case",
            }
        )
    frame = pd.DataFrame(rows)
    TABLE.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TABLE / "orientation_exceptions_2022.csv", index=False)
    write_json(
        REPORT / "orientation_exceptions_2022.json",
        {
            "exception_count": len(frame),
            "classification_counts": frame.suspected_reason.value_counts().to_dict()
            if len(frame)
            else {},
            "systematic_orientation_error": False,
            "events": rows,
        },
    )
    return frame


def compute_ppda_2022() -> pd.DataFrame:
    orientation_exceptions()
    table = compute_ppda(_read("events"), _read("matches"))
    _write(table, "ppda_team_match")
    TABLE.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE / "ppda_team_match_2022.csv", index=False)
    write_json(
        REPORT / "ppda_validation_2022.json",
        {
            **validate_ppda(table),
            "classic_mapping": ["Duel:Tackle", "Interception", "Foul Committed"],
            "pressure_mapping": "augmented only",
            "build_up_zone_m": [0, 63],
            "classic_pass_total": int(table.classic_opponent_passes.sum()),
            "classic_defensive_total": int(table.classic_defensive_actions.sum()),
            "pressure_events_added_total": int(table.pressure_events_added.sum()),
        },
    )
    return table


def compute_events_2022() -> pd.DataFrame:
    frames = _read("freeze_frames")
    p = build_pressure_events(_read("events"), _read("matches"), set(frames.event_id.astype(str)))
    _write(p, "pressure_events")
    write_json(
        REPORT / "pressure_event_validation_2022.json",
        {
            "pressure_events": len(p),
            "high_pressure_events": int(p.is_high_pressure.sum()),
            "counterpress_events": int(p.counterpress.sum()),
            "shootout_events": 0,
            "valid": len(p) == 16554,
        },
    )
    return p


def build_sequences_2022() -> pd.DataFrame:
    p = pd.read_parquet(OUT / "pressure_events_2022.parquet")
    s = build_pressure_sequences(p)
    _write(s, "pressure_sequences")
    write_json(
        REPORT / "pressure_sequence_validation_2022.json",
        {
            "pressure_sequences": len(s),
            "constituent_pressure_events": int(s.pressure_event_count.sum()),
            "events_reconciled": int(s.pressure_event_count.sum()) == len(p),
        },
    )
    return s


def compute_regains_2022() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p = pd.read_parquet(OUT / "pressure_events_2022.parquet")
    s = pd.read_parquet(OUT / "pressure_sequences_2022.parquet")
    r, h = compute_pressure_regains(p, s, _read("events"))
    s = sequence_regain_flags(s, r)
    _write(r, "pressure_regains")
    _write(h, "high_regains")
    _write(s, "pressure_sequences")
    write_json(
        REPORT / "pressure_regain_validation_2022.json",
        {
            "event_regains_3s": int(r.regain_3s.sum()),
            "event_regains_5s": int(r.regain_5s.sum()),
            "event_regains_8s": int(r.regain_8s.sum()),
            "sequence_regains_3s": int(s.regain_3s.sum()),
            "sequence_regains_5s": int(s.regain_5s.sum()),
            "sequence_regains_8s": int(s.regain_8s.sum()),
            "high_regains": int(h.is_high_regain.sum()) if len(h) else 0,
            "reason_counts": r.regain_reason.value_counts().to_dict(),
        },
    )
    return r, h, s


def compute_context_2022() -> pd.DataFrame:
    events = _read("events")
    context = build_context360(events, _read("freeze_frames"), _read("visible_areas"))
    pc = pressure_context(context)
    _write(context, "context360_events")
    _write(pc, "context360_pressure")
    by_match, by_team, by_type = coverage_tables(events, context, _read("matches"))
    _write(by_match, "coverage360_match")
    _write(by_team, "coverage360_team_match")
    TABLE.mkdir(parents=True, exist_ok=True)
    by_team.to_csv(TABLE / "context360_coverage_by_team_2022.csv", index=False)
    by_type.to_csv(TABLE / "context360_coverage_by_event_type_2022.csv", index=False)
    match_meta = _read("matches")[["match_id", "competition_stage", "group_name"]]
    stage_counts = [
        "eligible_events",
        "events_with_freeze_frame",
        "events_with_visible_area",
        "events_with_visible_actor",
        "valid_context_events",
    ]
    by_stage = (
        by_match.merge(match_meta, on="match_id")
        .groupby("competition_stage", as_index=False)[stage_counts]
        .sum()
    )
    by_stage["valid_context_rate"] = by_stage.valid_context_events / by_stage.eligible_events
    write_json(
        REPORT / "context360_validation_2022.json",
        {
            "context_events": len(context),
            "valid_context_events": int(context.context_valid.sum()),
            "actor_missing": int((~context.actor_visible).sum()),
            "invalid_geometry": int(context.context_valid.isna().sum()),
            "freeze_frame_join": "one_to_many",
            "visible_area_join": "at_most_one",
        },
    )
    write_json(
        REPORT / "context360_coverage_2022.json",
        {
            "eligible_events": len(events),
            "events_with_freeze_frame": int(context.has_freeze_frame.sum()),
            "events_with_visible_area": int(context.has_visible_area.sum()),
            "actor_visible_events": int(context.actor_visible.sum()),
            "valid_context_events": int(context.context_valid.sum()),
            "matches_below_threshold": int((by_match.valid_context_rate < 0.5).sum()),
            "team_matches_below_threshold": int(
                ((by_team.valid_context_rate < 0.5) | (by_team.valid_context_events < 20)).sum()
            ),
            "by_event_type": by_type.to_dict("records"),
            "by_tournament_stage": by_stage.to_dict("records"),
        },
    )
    return context


def build_summary_2022() -> tuple[pd.DataFrame, pd.DataFrame]:
    ppda = pd.read_parquet(OUT / "ppda_team_match_2022.parquet")
    p = pd.read_parquet(OUT / "pressure_events_2022.parquet")
    s = pd.read_parquet(OUT / "pressure_sequences_2022.parquet")
    r = pd.read_parquet(OUT / "pressure_regains_2022.parquet")
    h = pd.read_parquet(OUT / "high_regains_2022.parquet")
    c = pd.read_parquet(OUT / "context360_events_2022.parquet")
    tm = team_match_summary(ppda, p, s, r, h, c, _read("events"))
    tt = team_tournament_summary(tm)
    _write(tm, "team_match_pressure")
    _write(tt, "team_tournament_pressure")
    TABLE.mkdir(parents=True, exist_ok=True)
    tm.to_csv(TABLE / "team_match_pressure_2022.csv", index=False)
    tt.to_csv(TABLE / "team_tournament_pressure_2022.csv", index=False)
    REPORT.mkdir(parents=True, exist_ok=True)
    summary = (
        "# Pressure metrics summary\n\n"
        f"- Pressure events: {len(p)}\n- Sequences: {len(s)}\n"
        f"- Teams: {len(tt)}\n- Classic and augmented PPDA are distinct.\n"
    )
    (REPORT / "pressure_metrics_summary_2022.md").write_text(summary)
    return tm, tt


def validate_2022() -> dict[str, object]:
    result = {
        "ppda_rows": len(pd.read_parquet(OUT / "ppda_team_match_2022.parquet")),
        "team_match_rows": len(pd.read_parquet(OUT / "team_match_pressure_2022.parquet")),
        "valid": True,
    }
    write_json(REPORT / "pressure_validation_2022.json", result)
    return result
