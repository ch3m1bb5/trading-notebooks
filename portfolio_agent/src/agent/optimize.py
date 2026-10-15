from typing import Optional
import numpy as np
import pandas as pd

def _project_to_simplex(v: np.ndarray) -> np.ndarray:
    # Algorithm from Duchi et al. (2008)
    n = v.shape[0]
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, n+1) > (cssv - 1))[0][-1]
    theta = (cssv[rho] - 1) / (rho + 1.0)
    return np.maximum(v - theta, 0)

def optimize_mvo(expected: pd.Series,
                 cov: pd.DataFrame,
                 risk_aversion: float = 5.0,
                 long_only: bool = True,
                 max_weight: float = 0.2) -> pd.Series:
    # closed-form unconstrained: w ~ inv(Sigma)*mu / lambda
    mu = expected.values
    Sigma = cov.values + 1e-6 * np.eye(len(mu))
    try:
        invS = np.linalg.pinv(Sigma)
    except Exception:
        invS = np.linalg.pinv(Sigma + 1e-5*np.eye(len(mu)))
    w = invS @ mu
    if long_only:
        w = np.maximum(w, 0.0)
    w = w / (w.sum() + 1e-12)
    if w.sum() <= 0:
        w = np.ones_like(w) / len(w)
    if max_weight is not None:
        w = _cap_weights(w, max_weight)
    return pd.Series(w, index=expected.index)

def _cap_weights(w: np.ndarray, max_weight: float) -> np.ndarray:
    """Limita cada peso a max_weight redistribuindo o excesso (soma = 1)."""
    w = w.astype(float).copy()
    cap = max(max_weight, 1.0 / len(w))  # impossível respeitar se n * max < 1
    for _ in range(len(w) + 1):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        free = w < cap - 1e-12
        if w[free].sum() > 0:
            w[free] += excess * w[free] / w[free].sum()
        else:
            w[free] += excess / free.sum()
    return w

def portfolio_metrics(weights: pd.Series, mean_returns: pd.Series, cov: pd.DataFrame, periods_per_year: int=252):
    mu = float(weights @ mean_returns)
    vol = float(np.sqrt(weights.values @ cov.values @ weights.values.T))
    sharpe = mu / (vol + 1e-12) * np.sqrt(periods_per_year)
    return {"mu": mu, "vol": vol, "sharpe_annual": sharpe}
