import pytest

from worldcup_strategy.data.coordinates import elapsed_seconds, normalize_location


def test_scales_statsbomb_coordinates() -> None:
    point = normalize_location([120, 80])
    assert point.x_105 == pytest.approx(105)
    assert point.y_68 == pytest.approx(68)


def test_direction_flip_is_two_dimensional() -> None:
    point = normalize_location([24, 20], attacking_left_to_right=False)
    assert point.x_normalized == pytest.approx(84)
    assert point.y_normalized == pytest.approx(51)


@pytest.mark.parametrize("location", [None, [], [1], [None, 2], [121, 20]])
def test_invalid_locations_are_not_zero_imputed(location: object) -> None:
    point = normalize_location(location)
    assert point.x_normalized is None


def test_cumulative_elapsed_time_preserves_stoppage_time() -> None:
    assert elapsed_seconds(47, 15) == 2835
