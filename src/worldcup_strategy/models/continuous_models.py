# mypy: ignore-errors
"""Cluster-robust linear association models."""

import numpy as np

from worldcup_strategy.models.uncertainty import clustered_covariance


def fit_clustered_ols(y: np.ndarray, x: np.ndarray, clusters: np.ndarray) -> dict[str, np.ndarray]:
    """Fit OLS and return match-clustered standard errors."""
    coefficients = np.linalg.pinv(x) @ y
    residuals = y - x @ coefficients
    covariance = clustered_covariance(x, residuals, clusters)
    return {
        "coefficient": coefficients,
        "standard_error": np.sqrt(np.clip(np.diag(covariance), 0, None)),
    }
