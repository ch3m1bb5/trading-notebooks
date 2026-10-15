import pandas as pd
import numpy as np

from .optimize import optimize_mvo

def backtest(prices: pd.DataFrame,
             expected_next: pd.DataFrame,
             cov_roll: dict,
             rebalance_dates,
             long_only=True,
             max_weight=0.2,
             tc_bps=2.0):
    equity_curve = pd.Series(dtype=float)
    weights_hist = {}
    nav = 1.0
    last_w = None

    rebalance_dates = [d for d in rebalance_dates if d in prices.index and d in cov_roll]
    for i, dt in enumerate(rebalance_dates):
        # otimiza usando expectativa e covariância da data
        mu = expected_next.loc[dt].dropna()
        cov = cov_roll[dt].loc[mu.index, mu.index]
        w = optimize_mvo(mu, cov, long_only=long_only, max_weight=max_weight)
        # custo de transação (turnover x bps)
        tc = 0.0 if last_w is None else float(np.abs(w - last_w).sum()) * (tc_bps / 10000.0)
        last_w = w
        weights_hist[dt] = w

        # mantém os pesos até o próximo rebalance (NAV diário)
        end_dt = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else prices.index[-1]
        window = prices.loc[dt:end_dt, w.index]
        if len(window) < 2:
            continue
        rets = window.pct_change().iloc[1:].fillna(0.0)
        port_rets = (rets @ w).clip(-0.5, 0.5)
        port_rets.iloc[0] -= tc  # aplica custo no primeiro dia
        path = nav * (1 + port_rets).cumprod()
        if equity_curve.empty:
            equity_curve = pd.Series([nav], index=[window.index[0]])
        equity_curve = pd.concat([equity_curve, path])
        nav = float(path.iloc[-1])

    equity_curve = equity_curve.sort_index()
    return equity_curve, weights_hist
