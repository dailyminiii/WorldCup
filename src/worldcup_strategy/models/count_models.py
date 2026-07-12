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
    standard_error = np.sqrt(np.clip(np.diag(bread @ meat @ bread), 0, None))
    return {
        "coefficient": beta,
        "standard_error": standard_error,
        "converged": converged,
        "fitted": mu,
    }


def fit_binomial(
    successes: np.ndarray,
    trials: np.ndarray,
    x: np.ndarray,
    clusters: np.ndarray,
    iterations: int = 100,
) -> dict[str, object]:
    """Fit grouped-binomial logit with cluster-robust covariance."""
    beta = np.zeros(x.shape[1])
    converged = False
    proportions = successes / trials
    for _ in range(iterations):
        eta = np.clip(x @ beta, -20, 20)
        probability = 1 / (1 + np.exp(-eta))
        weights = trials * probability * (1 - probability)
        working = eta + (proportions - probability) / (probability * (1 - probability))
        weighted_x = x * np.sqrt(weights)[:, None]
        updated = np.linalg.pinv(weighted_x) @ (working * np.sqrt(weights))
        if np.max(np.abs(updated - beta)) < 1e-9:
            beta = updated
            converged = True
            break
        beta = updated
    bread = np.linalg.pinv(x.T @ (weights[:, None] * x))
    meat = np.zeros_like(bread)
    residual = successes - trials * probability
    for cluster in np.unique(clusters):
        selected = clusters == cluster
        score = x[selected].T @ residual[selected]
        meat += np.outer(score, score)
    return {
        "coefficient": beta,
        "standard_error": np.sqrt(np.clip(np.diag(bread @ meat @ bread), 0, None)),
        "converged": converged,
        "fitted": probability,
    }
