"""Action-layer validation summaries."""

import numpy as np
import numpy.typing as npt


def validate_xt_grid(grid: npt.NDArray[np.float64]) -> dict[str, object]:
    finite = bool(np.isfinite(grid).all())
    bounded = bool(((grid >= 0) & (grid <= 1)).all())
    danger = float(grid[:, -2:].mean())
    defensive = float(grid[:, :2].mean())
    return {
        "all_finite": finite,
        "bounded_zero_one": bounded,
        "danger_zone_mean": danger,
        "defensive_zone_mean": defensive,
        "danger_exceeds_defensive": danger > defensive,
        "valid": finite and bounded and danger > defensive,
    }
