import os
from typing import List, Tuple
import pandas as pd
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

def _cache_path(cache_dir: str, ticker: str, start: str, end: str, interval: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    key = f"{ticker}_{start}_{end}_{interval}".replace(":", "-")
    return os.path.join(cache_dir, key + ".parquet")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def download_ohlc(ticker: str, start: str, end: str, interval: str="1d", cache_dir: str=".cache") -> pd.DataFrame:
    path = _cache_path(cache_dir, ticker, start, end, interval)
    if os.path.exists(path):
        return pd.read_parquet(path)
    if yf is None:
        raise RuntimeError("yfinance não disponível no ambiente de execução.")
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise RuntimeError(f"Sem dados para {ticker}.")
    df = df.rename(columns=str.title)
    df["Ticker"] = ticker
    df.to_parquet(path)
    return df

def load_prices(tickers: List[str], start: str, end: str, interval: str="1d", cache_dir: str=".cache") -> pd.DataFrame:
    data = []
    for t in tickers:
        df = download_ohlc(t, start, end, interval, cache_dir)
        data.append(df[["Close"]].assign(Ticker=t))
    allc = pd.concat(data).reset_index().rename(columns={"Date":"Date"})
    prices = allc.pivot(index="Date", columns="Ticker", values="Close").sort_index()
    return prices.dropna(how="all")

def compute_returns(prices: pd.DataFrame, horizon_days: int=1) -> pd.DataFrame:
    return prices.pct_change(horizon_days).dropna(how="all")
