from typing import Tuple, Dict
import pandas as pd
import numpy as np

from .config import PipelineConfig
from .data import load_prices, compute_returns
from .features import make_feature_panel
from .models import train_predict_expected_returns
from .optimize import portfolio_metrics
from .backtest import backtest
from .visualize import plot_equity_curve, plot_weights
from .report import build_pdf_report

def run_pipeline(cfg: PipelineConfig):
    prices = load_prices(cfg.data.tickers, cfg.data.start, cfg.data.end, cfg.data.interval, cfg.data.cache_dir)
    daily_rets = prices.pct_change().dropna()

    # Feature panel
    feats = make_feature_panel(prices, cfg.model.feature_windows)

    # Futuros retornos (horizonte)
    fut = prices.pct_change(cfg.model.horizon_days).shift(-cfg.model.horizon_days)

    # Datas de rebalance
    # Último pregão de cada período ('M' mensal, 'W' semanal) — compatível com pandas >= 2.2
    freq = {"M": "ME", "W": "W-FRI"}.get(cfg.optimize.rebalance, cfg.optimize.rebalance)
    rebalance = list(prices.index.to_series().resample(freq).last().dropna())
    cov_roll = {}
    expected_next = {}
    for dt in rebalance:
        # previsão esperada por ticker (pula datas sem histórico suficiente)
        try:
            mu_pred = train_predict_expected_returns(feats, fut, as_of_date=dt,
                                                     lookback_days=cfg.model.lookback_days,
                                                     model_type=cfg.model.model_type)
        except ValueError:
            continue
        # rolling covariance dos últimos lookback dias
        cov_roll[dt] = daily_rets.loc[:dt].tail(cfg.model.lookback_days).cov()
        expected_next[dt] = mu_pred
    if not expected_next:
        raise ValueError("Histórico insuficiente: aumente o período ou reduza o lookback.")
    rebalance = list(expected_next.keys())
    expected_next = pd.DataFrame(expected_next).T

    curve, weights_hist = backtest(prices,
                                   expected_next=expected_next,
                                   cov_roll=cov_roll,
                                   rebalance_dates=rebalance,
                                   long_only=cfg.optimize.long_only,
                                   max_weight=cfg.optimize.max_weight,
                                   tc_bps=cfg.optimize.transaction_cost_bps)

    # Métricas
    port_rets = curve.pct_change().dropna()
    ann_factor = 252
    mu_ann = (1 + port_rets.mean())**ann_factor - 1
    vol_ann = port_rets.std() * np.sqrt(ann_factor)
    dd = (curve / curve.cummax() - 1).min()
    sharpe = (mu_ann - 0.0) / (vol_ann + 1e-12)
    metrics = {
        "Retorno anualizado": f"{mu_ann:.2%}",
        "Vol anualizada": f"{vol_ann:.2%}",
        "Sharpe": f"{sharpe:.2f}",
        "Max Drawdown": f"{dd:.2%}"
    }

    # Gráficos interativos
    fig_curve = plot_equity_curve(curve)
    fig_w = plot_weights(weights_hist)

    return {
        "prices": prices,
        "equity_curve": curve,
        "weights_hist": weights_hist,
        "metrics": metrics,
        "fig_curve": fig_curve,
        "fig_weights": fig_w
    }

def _matplotlib_figures(results: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    curve = results["equity_curve"]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(curve.index, curve.values, color="#2563eb", lw=1.4)
    ax.set_title("Evolução do Portfólio (NAV)"); ax.set_ylabel("NAV"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig("curve.png", dpi=150); plt.close(fig); paths.append("curve.png")
    w = pd.DataFrame(results["weights_hist"]).T.sort_index()
    if not w.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.stackplot(w.index, w.T.values, labels=w.columns, step="post", alpha=.9)
        ax.set_title("Pesos por Rebalance"); ax.set_ylabel("Peso"); ax.set_ylim(0, 1)
        ax.legend(loc="upper left", ncol=len(w.columns)); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig("weights.png", dpi=150); plt.close(fig); paths.append("weights.png")
    return paths

def generate_pdf_report(results: dict, cfg: PipelineConfig):
    # salva figuras temporariamente como PNG via plotly.kaleido
    fig_paths = []
    try:
        import plotly.io as pio
        p1 = "curve.png"; pio.write_image(results["fig_curve"], p1, width=1200, height=600, scale=2)
        p2 = "weights.png"; pio.write_image(results["fig_weights"], p2, width=1200, height=600, scale=2)
        fig_paths = [p1, p2]
    except Exception:
        # fallback sem kaleido/Chrome: desenha os gráficos com matplotlib
        fig_paths = _matplotlib_figures(results)

    output_pdf = cfg.report.output_pdf
    build_pdf_report(output_pdf, cfg.report.title, results["metrics"], fig_paths)
    return output_pdf

def generate_html_report(results: dict, cfg: PipelineConfig):
    from .report import build_html_report
    out = cfg.report.output_pdf.replace(".pdf", ".html")
    build_html_report(out, cfg.report.title, results["metrics"],
                      fig_curve=results.get("fig_curve"),
                      fig_weights=results.get("fig_weights"))
    return out
