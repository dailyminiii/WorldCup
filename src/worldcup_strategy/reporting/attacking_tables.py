# mypy: ignore-errors
"""Team attacking summary tables."""

import pandas as pd

from worldcup_strategy.actions.possessions import entry_flags


def team_match_attacking(
    actions: pd.DataFrame, xg: pd.DataFrame, xt: pd.DataFrame, progression: pd.DataFrame
) -> pd.DataFrame:
    enriched = (
        entry_flags(actions)
        .merge(xt[["match_id", "action_id", "xt_added"]], on=["match_id", "action_id"], how="left")
        .merge(
            progression[["match_id", "action_id", "is_progressive"]],
            on=["match_id", "action_id"],
            how="left",
        )
    )
    rows: list[dict[str, object]] = []
    for (match_id, team_id), group in enriched.groupby(["match_id", "team_id"], sort=True):
        x = xg[(xg.match_id == match_id) & (xg.team_id == team_id)].iloc[0]
        possessions = group.possession_id.nunique()
        passes = group.type_name.eq("pass")
        carries = group.type_name.isin(["carry", "dribble"])
        pp = passes & group.is_progressive.fillna(False)
        pc = carries & group.is_progressive.fillna(False)
        row = {
            "match_id": int(match_id),
            "team_id": int(team_id),
            "matches": 1,
            "possessions": possessions,
            "passes": int(passes.sum()),
            "completed_passes": int((passes & group.result_name.eq("success")).sum()),
            "carries": int(carries.sum()),
            "shots": int(x.shots),
            "goals": int(x.goals),
            "statsbomb_xg": x.statsbomb_xg,
            "non_penalty_xg": x.non_penalty_xg,
            "open_play_xg": x.open_play_xg,
            "set_piece_xg": x.set_piece_xg,
            "xt_added": group.xt_added.sum(min_count=1),
            "positive_xt": group.loc[group.xt_added > 0, "xt_added"].sum(min_count=1),
            "negative_xt": group.loc[group.xt_added < 0, "xt_added"].sum(min_count=1),
            "progressive_passes": int(pp.sum()),
            "progressive_carries": int(pc.sum()),
            "final_third_entries": int(group.final_third_entry.sum()),
            "box_entries": int(group.box_entry.sum()),
            "final_third_possession_entries": int(
                group.loc[group.final_third_entry, "possession_id"].nunique()
            ),
            "box_possession_entries": int(group.loc[group.box_entry, "possession_id"].nunique()),
        }
        row.update(_rates(row))
        rows.append(row)
    return pd.DataFrame(rows)


def _rates(row: dict[str, object]) -> dict[str, float | None]:
    def rate(n: str, d: str, multiplier: float = 1) -> float | None:
        denominator = float(row[d])
        return float(row[n]) / denominator * multiplier if denominator else None

    return {
        "xg_per_shot": rate("statsbomb_xg", "shots"),
        "xt_per_possession": rate("xt_added", "possessions"),
        "progressive_passes_per_100_passes": rate("progressive_passes", "passes", 100),
        "progressive_carries_per_100_possessions": rate("progressive_carries", "possessions", 100),
        "final_third_entries_per_possession": rate("final_third_entries", "possessions"),
        "box_entries_per_possession": rate("box_entries", "possessions"),
    }


def team_tournament_attacking(team_match: pd.DataFrame) -> pd.DataFrame:
    rates = {
        "xg_per_shot",
        "xt_per_possession",
        "progressive_passes_per_100_passes",
        "progressive_carries_per_100_possessions",
        "final_third_entries_per_possession",
        "box_entries_per_possession",
    }
    additive = [c for c in team_match.columns if c not in {"match_id", "team_id"} | rates]
    output = team_match.groupby("team_id", as_index=False)[additive].sum(min_count=1)
    for index, row in output.iterrows():
        for key, value in _rates(row.to_dict()).items():
            output.loc[index, key] = value
    return output
