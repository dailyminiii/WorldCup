# mypy: ignore-errors
"""Model estimability and diagnostic checks."""

import numpy as np


def estimable(design: np.ndarray) -> bool:
    """Check that the design has full column rank."""
    return bool(len(design) and np.linalg.matrix_rank(design) == design.shape[1])


def overdispersion(observed: np.ndarray, fitted: np.ndarray, parameters: int) -> float | None:
    """Pearson dispersion for count-model diagnostics."""
    degrees = len(observed) - parameters
    if degrees <= 0 or np.any(fitted <= 0):
        return None
    return float(np.sum((observed - fitted) ** 2 / fitted) / degrees)
