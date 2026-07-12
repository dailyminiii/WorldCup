# mypy: ignore-errors
"""Cluster-robust uncertainty helpers."""

import numpy as np


def clustered_covariance(x: np.ndarray, residuals: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    """Return a deterministic CR0 sandwich covariance matrix."""
    bread = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    for cluster in np.unique(clusters):
        score = x[clusters == cluster].T @ residuals[clusters == cluster]
        meat += np.outer(score, score)
    return bread @ meat @ bread
