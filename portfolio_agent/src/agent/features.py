import pandas as pd
import numpy as np

def rolling_return(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    return prices.pct_change(window)

def momentum(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    return prices / prices.shift(window) - 1.0

def volatility(returns: pd.DataFrame, window: int) -> pd.DataFrame:
    return returns.rolling(window).std()

def make_feature_panel(prices: pd.DataFrame, feature_windows: dict) -> dict:
    rets = prices.pct_change().dropna()
    feats = {}
    if "ret_21" in feature_windows:
        feats["ret_21"] = rolling_return(prices, feature_windows["ret_21"])
    if "ret_63" in feature_windows:
        feats["ret_63"] = rolling_return(prices, feature_windows["ret_63"])
    if "mom_126" in feature_windows:
        feats["mom_126"] = momentum(prices, feature_windows["mom_126"])
    if "vol_21" in feature_windows:
        feats["vol_21"] = volatility(rets, feature_windows["vol_21"])
    return feats
