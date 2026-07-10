from worldcup_strategy.pressure.frames import possession_frame, rotate_opponent


def test_opponent_rotation_and_round_trip() -> None:
    assert rotate_opponent(10, 5) == (95, 63)
    assert rotate_opponent(*rotate_opponent(10, 5)) == (10, 5)


def test_possession_frame_rotates_defender() -> None:
    assert possession_frame(95, 63, acting_team_id=2, possession_team_id=1) == (10, 5)
    assert possession_frame(None, None, acting_team_id=2, possession_team_id=1) == (None, None)
