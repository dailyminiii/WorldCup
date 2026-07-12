# mypy: ignore-errors
"""Deterministic Poisson IRLS for observational count associations."""

import numpy as np


def fit_poisson(
    y: np.ndarray,
    x: np.ndarray,
    offset: np.ndarray,
    clusters: np.ndarray,
    iterations: int = 100,
) -> dict[str, object]:
    """Fit a log-link Poisson model using fixed-iteration-tolerance IRLS."""
    beta = np.zeros(x.shape[1])
    converged = False
    for _ in range(iterations):
        eta = np.clip(x @ beta + offset, -20, 20)
        mu = np.exp(eta)
        working = eta + (y - mu) / mu - offset
        weighted_x = x * np.sqrt(mu)[:, None]
        updated = np.linalg.pinv(weighted_x) @ (working * np.sqrt(mu))
        if np.max(np.abs(updated - beta)) < 1e-9:
            converged = True
            beta = updated
            break
        beta = updated
    bread = np.linalg.pinv(x.T @ (mu[:, None] * x))
    meat = np.zeros_like(bread)
    for cluster in np.unique(clusters):
        selected = clusters == cluster
        score = x[selected].T @ (y[selected] - mu[selected])
        meat += np.outer(score, score)
    standard_error = np.sqrt(np.diag(bread @ meat @ bread))
    return {
        "coefficient": beta,
        "standard_error": standard_error,
        "converged": converged,
        "fitted": mu,
    }
