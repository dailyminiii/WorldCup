from pathlib import Path

import pandas as pd
import pytest


def test_observed_own_goal_pairing_at_pinned_source() -> None:
    path = Path("data/processed/events_2022.parquet")
    if not path.exists():
        pytest.skip("real processed data is intentionally absent in CI")
    events = pd.read_parquet(path)
    own_goals = events[events.is_own_goal]
    assert len(own_goals) == 6
    assert int(own_goals.is_goal.sum()) == 3
