"""Possession and entry helpers."""

import pandas as pd


def entry_flags(actions: pd.DataFrame) -> pd.DataFrame:
    result = actions.copy()
    valid = result[["start_x", "end_x", "end_y"]].notna().all(axis=1)
    result["final_third_entry"] = valid & (result.start_x < 70) & (result.end_x >= 70)
    result["box_entry"] = (
        valid
        & ~((result.start_x >= 88.5) & result.start_y.between(13.84, 54.16))
        & (result.end_x >= 88.5)
        & result.end_y.between(13.84, 54.16)
    )
    return result
