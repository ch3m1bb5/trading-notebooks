from typing import Dict, Tuple
import pandas as pd
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

def _prepare_xy(feats: Dict[str, pd.DataFrame], target: pd.DataFrame, as_of_date: pd.Timestamp, lookback_days: int):
    # stack features cross-sectionally across tickers and time within lookback
    X_list, y_list = [], []
    dates = target.index[target.index < as_of_date][-lookback_days:]
    tickers = target.columns
    for dt in dates:
        row = []
        ok = True
        for name, df in feats.items():
            if dt not in df.index:
                ok = False
                break
            row.append(df.loc[dt, tickers].values.reshape(1,-1))
        if not ok:
            continue
        X = np.concatenate(row, axis=1)  # shape (1, n_tickers * n_features)
        y = target.loc[dt, tickers].values.reshape(1, -1)
        if np.isnan(X.astype(float)).any() or np.isnan(y.astype(float)).any():
            continue  # janela ainda sem histórico suficiente
        X_list.append(X)
        y_list.append(y)
    if not X_list:
        raise ValueError("Sem dados suficientes para treinar.")
    X = np.vstack(X_list)  # (n_dates, n_tickers * n_features)
    y = np.vstack(y_list)  # (n_dates, n_tickers)
    # Média do target entre tickers (retorno médio) para problema univariado
    y = y.mean(axis=1)
    return X, y

def train_predict_expected_returns(feats: Dict[str, pd.DataFrame],
                                   future_returns: pd.DataFrame,
                                   as_of_date: pd.Timestamp,
                                   lookback_days: int,
                                   model_type: str="ridge") -> pd.Series:
    X, y = _prepare_xy(feats, future_returns, as_of_date, lookback_days)
    if model_type == "ridge":
        mdl = Ridge(alpha=10.0)
    elif model_type == "random_forest":
        mdl = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42)
    else:
        raise ValueError("model_type inválido.")
    mdl.fit(X, y)
    # Previsão cross-seccional: usamos as features na data atual para cada ticker
    tickers = future_returns.columns
    row = []
    for name, df in feats.items():
        if as_of_date not in df.index:
            raise ValueError(f"Features indisponíveis para {as_of_date}.")
        row.append(df.loc[as_of_date, tickers].values.reshape(1,-1))
    X_t = np.concatenate(row, axis=1)
    if np.isnan(X_t.astype(float)).any():
        raise ValueError(f"Features incompletas em {as_of_date}.")
    # Previsão do retorno médio de mercado e, como heurística, escalamos por momentum relativo de cada ticker
    mean_pred = float(mdl.predict(X_t)[0])
    mom = feats.get("mom_126")
    if mom is not None and as_of_date in mom.index:
        rel = mom.loc[as_of_date]
        rel = (rel - rel.mean()) / (rel.std() + 1e-9)
        pred_each = mean_pred + 0.5 * rel
    else:
        pred_each = pd.Series(mean_pred, index=tickers)
    return pd.Series(pred_each, index=tickers).astype(float)
