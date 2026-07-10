# mypy: ignore-errors
"""Disk orchestration for Milestone 2 actions."""

import importlib.metadata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from worldcup_strategy.actions.progression import compute_progression
from worldcup_strategy.actions.spadl import build_spadl_actions, orientation_diagnostics
from worldcup_strategy.actions.validation import validate_xt_grid
from worldcup_strategy.actions.xg import build_shot_xg, team_match_xg
from worldcup_strategy.actions.xt import (
    XTConfig,
    apply_xt,
    configuration_hash,
    fit_xt_grid,
    save_xt_model,
)
from worldcup_strategy.config import load_data_config
from worldcup_strategy.data.manifests import source_commit, write_json
from worldcup_strategy.data.statsbomb import (
    canonical_events,
    canonical_matches,
    load_matches,
    read_json,
    resolve_competition,
)
from worldcup_strategy.reporting.attacking_tables import (
    team_match_attacking,
    team_tournament_attacking,
)

ACTION_DIR = Path("data/processed/actions")


def _tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root = Path("data/processed")
    return tuple(
        pd.read_parquet(root / f"{name}_2022.parquet")
        for name in ("events", "matches", "teams", "players")
    )  # type: ignore[return-value]


def build_spadl_2022() -> pd.DataFrame:
    events, matches, teams, players = _tables()
    actions = build_spadl_actions(events, matches, teams, players)
    ACTION_DIR.mkdir(parents=True, exist_ok=True)
    actions.to_parquet(ACTION_DIR / "spadl_actions_2022.parquet", index=False)
    diagnostic = orientation_diagnostics(actions)
    write_json(Path("outputs/reports/spadl_orientation_validation_2022.json"), diagnostic)
    if not diagnostic["valid"]:
        raise ValueError("SPADL orientation validation failed")
    return actions


def compute_xg_2022() -> pd.DataFrame:
    events, matches, _, _ = _tables()
    shots = build_shot_xg(events)
    ACTION_DIR.mkdir(parents=True, exist_ok=True)
    shots.to_parquet(ACTION_DIR / "shot_xg_2022.parquet", index=False)
    tm = team_match_xg(shots, matches)
    missing = int(shots.loc[~shots.is_own_goal, "statsbomb_xg"].isna().sum())
    write_json(
        Path("outputs/reports/xg_validation_2022.json"),
        {
            "regular_shot_count": int((~shots.is_own_goal).sum()),
            "scoring_own_goals": int((shots.is_own_goal & shots.is_goal).sum()),
            "missing_shot_xg": missing,
            "shootout_attempts_excluded": int(
                ((events.event_type == "Shot") & events.is_penalty_shootout).sum()
            ),
            "valid": missing == 0,
        },
    )
    return tm


def _reference_actions() -> tuple[pd.DataFrame, dict[str, Any]]:
    cfg = load_data_config()
    repo = cfg.raw_repository
    competition = resolve_competition(repo, "FIFA World Cup", "2018", 43, 3)
    raw_matches = load_matches(repo, 43, 3)
    matches = canonical_matches(raw_matches)
    frames = [
        canonical_events(int(mid), read_json(repo / "data/events" / f"{int(mid)}.json"))
        for mid in matches.match_id
    ]
    events = pd.concat(frames, ignore_index=True)
    actions = build_spadl_actions(events, matches)
    return actions, competition


def fit_xt(mode: str = "reference") -> dict[str, Any]:
    config_payload = yaml.safe_load(Path("configs/xt.yaml").read_text())
    cfg = XTConfig(
        config_payload["grid_width"],
        config_payload["grid_height"],
        config_payload["smoothing"]["alpha"],
        config_payload["seed"],
    )
    if mode == "reference":
        actions, competition = _reference_actions()
        season = 2018
        suffix = "reference_2018"
    elif mode == "tournament_only":
        actions = pd.read_parquet(ACTION_DIR / "spadl_actions_2022.parquet")
        competition = {"competition_id": 43, "season_id": 106}
        season = 2022
        suffix = "tournament_2022"
    else:
        raise ValueError(f"Unsupported xT mode: {mode}")
    grid = fit_xt_grid(actions, cfg)
    metadata = {
        "training_competition": "FIFA World Cup",
        "training_season": season,
        "competition_id": competition["competition_id"],
        "season_id": competition["season_id"],
        "source_commit_sha": source_commit(load_data_config().raw_repository),
        "training_action_count": int(
            (
                actions.type_name.isin(["pass", "carry", "dribble", "shot"])
                & actions.start_x.notna()
                & ~actions.is_penalty_shootout
            ).sum()
        ),
        "source_action_count": len(actions),
        "grid_width": cfg.width,
        "grid_height": cfg.height,
        "smoothing_configuration": config_payload["smoothing"],
        "seed": cfg.seed,
        "dependency_versions": {
            name: importlib.metadata.version(name) for name in ("numpy", "pandas")
        },
        "configuration_hash": configuration_hash(config_payload),
        "in_sample_exploratory": mode == "tournament_only",
        "training_mode": mode,
    }
    save_xt_model(grid, metadata, Path(f"outputs/models/xt_grid_{suffix}"))
    write_json(Path(f"outputs/reports/xt_model_validation_{suffix}.json"), validate_xt_grid(grid))
    return metadata


def compute_xt_2022(model: str = "reference") -> pd.DataFrame:
    suffix = "reference_2018" if model == "reference" else "tournament_2022"
    grid = np.load(Path(f"outputs/models/xt_grid_{suffix}.npy"))
    actions = pd.read_parquet(ACTION_DIR / "spadl_actions_2022.parquet")
    output = apply_xt(actions, grid, model)
    output.to_parquet(ACTION_DIR / "action_xt_2022.parquet", index=False)
    write_json(
        Path("outputs/reports/xt_validation_2022.json"),
        {
            **validate_xt_grid(grid),
            "eligible_actions": int(output.eligible_for_xt.sum()),
            "missing_reason_counts": {
                str(key) if pd.notna(key) else "eligible": int(value)
                for key, value in output.xt_missing_reason.value_counts(dropna=False).items()
            },
            "training_mode": model,
        },
    )
    return output


def compute_progression_2022() -> pd.DataFrame:
    actions = pd.read_parquet(ACTION_DIR / "spadl_actions_2022.parquet")
    output = compute_progression(actions)
    output.to_parquet(ACTION_DIR / "progression_actions_2022.parquet", index=False)
    write_json(
        Path("outputs/reports/progression_validation_2022.json"),
        {
            "progressive_passes": int(
                ((output.action_type == "pass") & output.is_progressive).sum()
            ),
            "progressive_carries": int(
                (output.action_type.isin(["carry", "dribble"]) & output.is_progressive).sum()
            ),
            "exclusion_reason_counts": {
                str(key) if pd.notna(key) else "eligible": int(value)
                for key, value in output.progression_exclusion_reason.value_counts(
                    dropna=False
                ).items()
            },
        },
    )
    return output


def build_attacking_2022() -> tuple[pd.DataFrame, pd.DataFrame]:
    actions = pd.read_parquet(ACTION_DIR / "spadl_actions_2022.parquet")
    events, matches, _, _ = _tables()
    shots = pd.read_parquet(ACTION_DIR / "shot_xg_2022.parquet")
    xg = team_match_xg(shots, matches)
    xt = pd.read_parquet(ACTION_DIR / "action_xt_2022.parquet")
    progression = pd.read_parquet(ACTION_DIR / "progression_actions_2022.parquet")
    tm = team_match_attacking(actions, xg, xt, progression)
    tt = team_tournament_attacking(tm)
    tm.to_parquet(ACTION_DIR / "team_match_attacking_2022.parquet", index=False)
    tt.to_parquet(ACTION_DIR / "team_tournament_attacking_2022.parquet", index=False)
    Path("outputs/tables").mkdir(parents=True, exist_ok=True)
    tm.to_csv("outputs/tables/team_match_attacking_2022.csv", index=False)
    tt.to_csv("outputs/tables/team_tournament_attacking_2022.csv", index=False)
    pd.DataFrame(
        [
            {
                "metric_name": "statsbomb_xg",
                "implementation_version": "statsbomb_provider_xg_v1",
                "unit": "expected goals",
            },
            {
                "metric_name": "xt_added",
                "implementation_version": "xt_markov_v1",
                "unit": "expected possession goals",
            },
            {
                "metric_name": "progressive_passes",
                "implementation_version": "progressive_goal_distance_v1",
                "unit": "actions",
            },
            {
                "metric_name": "progressive_carries",
                "implementation_version": "progressive_goal_distance_v1",
                "unit": "actions",
            },
            {
                "metric_name": "final_third_entries",
                "implementation_version": "entry_geometry_v1",
                "unit": "actions",
            },
            {
                "metric_name": "box_entries",
                "implementation_version": "entry_geometry_v1",
                "unit": "actions",
            },
        ]
    ).to_csv("outputs/tables/metric_definitions_2022.csv", index=False)
    summary = (
        "# Attacking metrics summary\n\n"
        f"- Teams: {len(tt)}\n- Team-match rows: {len(tm)}\n"
        f"- Actions: {len(actions)}\n"
        "- xT mode: reference (2018; out-of-sample for 2022)\n"
    )
    Path("outputs/reports/attacking_metrics_summary_2022.md").write_text(summary)
    return tm, tt
