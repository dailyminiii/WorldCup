# mypy: ignore-errors
"""Deterministic grid-based Expected Threat fitting and application."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class XTConfig:
    width: int = 16
    height: int = 12
    alpha: float = 1.0
    seed: int = 20262022


def _zones(frame: pd.DataFrame, x: str, y: str, cfg: XTConfig) -> tuple[np.ndarray, np.ndarray]:
    zx = np.minimum((frame[x].to_numpy(float) / 105 * cfg.width).astype(int), cfg.width - 1)
    zy = np.minimum((frame[y].to_numpy(float) / 68 * cfg.height).astype(int), cfg.height - 1)
    return zx, zy


DEFAULT_XT_CONFIG = XTConfig()


def fit_xt_grid(actions: pd.DataFrame, cfg: XTConfig = DEFAULT_XT_CONFIG) -> np.ndarray:
    """Fit a smoothed absorbing Markov xT surface from successful moves and shots."""
    valid = actions.dropna(subset=["start_x", "start_y"]).copy()
    move_attempts = valid[
        valid.type_name.isin(["pass", "carry", "dribble"]) & ~valid.is_penalty_shootout
    ]
    moves = move_attempts[
        move_attempts.end_x.notna()
        & move_attempts.end_y.notna()
        & (move_attempts.result_name == "success")
    ]
    shots = valid[(valid.type_name == "shot") & ~valid.is_penalty_shootout]
    cells = cfg.width * cfg.height
    move_counts = np.zeros((cells, cells), dtype=float)
    sx, sy = _zones(moves, "start_x", "start_y", cfg)
    ex, ey = _zones(moves, "end_x", "end_y", cfg)
    for start, end in zip(sy * cfg.width + sx, ey * cfg.width + ex, strict=True):
        move_counts[start, end] += 1
    shot_counts = np.zeros(cells)
    goal_counts = np.zeros(cells)
    if len(shots):
        x, y = _zones(shots, "start_x", "start_y", cfg)
        indices = y * cfg.width + x
        for index, goal in zip(indices, shots.result_name.eq("success"), strict=True):
            shot_counts[index] += 1
            goal_counts[index] += bool(goal)
    move_totals = move_counts.sum(axis=1)
    attempt_counts = np.zeros(cells)
    if len(move_attempts):
        ax, ay = _zones(move_attempts, "start_x", "start_y", cfg)
        for index in ay * cfg.width + ax:
            attempt_counts[index] += 1
    totals = attempt_counts + shot_counts
    p_move = np.divide(move_totals, totals, out=np.zeros_like(totals), where=totals > 0)
    p_score = np.divide(
        goal_counts + cfg.alpha,
        shot_counts + 2 * cfg.alpha,
        out=np.zeros_like(shot_counts),
        where=shot_counts > 0,
    )
    transition = np.divide(
        move_counts + cfg.alpha / cells,
        move_totals[:, None] + cfg.alpha,
        out=np.zeros_like(move_counts),
        where=move_totals[:, None] > 0,
    )
    matrix = np.eye(cells) - p_move[:, None] * transition
    values = np.linalg.solve(matrix, (1 - p_move) * p_score)
    return np.clip(values.reshape(cfg.height, cfg.width), 0.0, 1.0)


def apply_xt(
    actions: pd.DataFrame, grid: np.ndarray, mode: str, version: str = "xt_markov_v1"
) -> pd.DataFrame:
    """Value actions with explicit eligibility and missing reasons."""
    height, width = grid.shape
    rows: list[dict[str, Any]] = []
    for row in actions.itertuples(index=False):
        reason: str | None = None
        if bool(row.is_penalty_shootout):
            reason = "penalty_shootout"
        elif row.type_name not in {"pass", "carry", "dribble"}:
            reason = "ineligible_action_type"
        elif row.result_name != "success":
            reason = "failed_action"
        elif pd.isna(row.start_x) or pd.isna(row.start_y):
            reason = "missing_start_location"
        elif pd.isna(row.end_x) or pd.isna(row.end_y):
            reason = "missing_end_location"
        elif not (
            0 <= row.start_x <= 105
            and 0 <= row.end_x <= 105
            and 0 <= row.start_y <= 68
            and 0 <= row.end_y <= 68
        ):
            reason = "invalid_coordinates"
        eligible = reason is None
        if eligible:
            sx = min(int(row.start_x / 105 * width), width - 1)
            sy = min(int(row.start_y / 68 * height), height - 1)
            ex = min(int(row.end_x / 105 * width), width - 1)
            ey = min(int(row.end_y / 68 * height), height - 1)
            start_xt = float(grid[sy, sx])
            end_xt = float(grid[ey, ex])
            added = end_xt - start_xt
        else:
            sx = sy = ex = ey = None
            start_xt = end_xt = added = None
        rows.append(
            {
                "match_id": row.match_id,
                "action_id": row.action_id,
                "original_event_id": row.original_event_id,
                "team_id": row.team_id,
                "player_id": row.player_id,
                "action_type": row.type_name,
                "start_x": row.start_x,
                "start_y": row.start_y,
                "end_x": row.end_x,
                "end_y": row.end_y,
                "start_zone_x": sx,
                "start_zone_y": sy,
                "end_zone_x": ex,
                "end_zone_y": ey,
                "start_xt": start_xt,
                "end_xt": end_xt,
                "xt_added": added,
                "xt_training_mode": mode,
                "xt_model_version": version,
                "eligible_for_xt": eligible,
                "xt_missing_reason": reason,
            }
        )
    return pd.DataFrame(rows)


def configuration_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def save_xt_model(grid: np.ndarray, metadata: dict[str, Any], prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    np.save(prefix.with_suffix(".npy"), grid)
    prefix.with_suffix(".json").write_text(json.dumps(grid.tolist(), indent=2) + "\n")
    prefix.with_name(prefix.name.replace("grid", "metadata")).with_suffix(".json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
