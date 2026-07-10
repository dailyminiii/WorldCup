"""Pressure validation helpers."""

import pandas as pd


def validate_ppda(table: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": len(table),
        "classic_denominator_zero_rows": int((table.classic_defensive_actions == 0).sum()),
        "augmented_denominator_zero_rows": int((table.augmented_defensive_actions == 0).sum()),
        "pressure_in_classic_denominator": False,
        "raw_components_complete": bool(
            table[["classic_opponent_passes", "classic_defensive_actions", "pressure_events_added"]]
            .notna()
            .all()
            .all()
        ),
        "valid": len(table) > 0,
    }
