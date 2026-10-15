import pandas as pd
import numpy as np
import plotly.graph_objs as go

def plot_equity_curve(curve: pd.Series):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve.index, y=curve.values, mode="lines", name="Portfólio"))
    fig.update_layout(title="Evolução do Portfólio (NAV)", xaxis_title="Data", yaxis_title="NAV")
    return fig

def plot_weights(weights_hist: dict):
    # Construir DataFrame alinhado
    dates = sorted(weights_hist.keys())
    if not dates:
        return go.Figure()
    tickers = sorted({t for w in weights_hist.values() for t in w.index})
    df = pd.DataFrame(index=dates, columns=tickers, data=0.0)
    for dt, w in weights_hist.items():
        df.loc[dt, w.index] = w.values
    df = df.sort_index()
    fig = go.Figure()
    for t in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[t], name=t, mode="lines",
                                 stackgroup="w", line=dict(width=0.5, shape="hv")))
    fig.update_layout(title="Pesos por Rebalance", xaxis_title="Data", yaxis_title="Peso",
                      yaxis=dict(range=[0, 1]))
    return fig
