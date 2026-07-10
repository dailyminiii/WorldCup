import pandas as pd

from worldcup_strategy.pressure.sequences import build_pressure_sequences


def test_two_second_boundary_clusters_and_larger_gap_splits() -> None:
    p = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team_id": 1,
                "opponent_id": 2,
                "possession_id": 3,
                "period": 1,
                "event_index": i,
                "elapsed_seconds": t,
                "x_pressing_team_frame": 60.0,
                "counterpress": False,
            }
            for i, t in enumerate([1.0, 3.0, 5.01])
        ]
    )
    result = build_pressure_sequences(p)
    assert result.pressure_event_count.tolist() == [2, 1]
