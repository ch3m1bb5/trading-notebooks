import numpy as np
import pandas as pd


def test_smoke_imports():
    import agent  # noqa: F401
    from agent.config import PipelineConfig, DataConfig  # dataclass defaults must import on Python 3.11+
    PipelineConfig(data=DataConfig(tickers=["A"], start="2020-01-01", end="2021-01-01"))


def test_cap_weights_respects_max_and_sums_to_one():
    from agent.optimize import _cap_weights
    w = _cap_weights(np.array([0.7, 0.2, 0.1, 0.0]), 0.4)
    assert w.max() <= 0.4 + 1e-9
    assert abs(w.sum() - 1) < 1e-9


def test_pipeline_offline(tmp_path, monkeypatch):
    """Runs the full pipeline on synthetic prices (no internet needed)."""
    import agent.pipeline as pl
    from agent.config import PipelineConfig, DataConfig, OptimizeConfig

    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2015-01-01", "2018-12-31")
    tickers = ["AAA", "BBB", "CCC", "DDD"]
    prices = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, (len(idx), 4)), axis=0)),
                          index=idx, columns=tickers)
    monkeypatch.setattr(pl, "load_prices", lambda *a, **k: prices)

    cfg = PipelineConfig(data=DataConfig(tickers=tickers, start="2015-01-01", end="2018-12-31"),
                         optimize=OptimizeConfig(max_weight=0.4))
    res = pl.run_pipeline(cfg)
    w = pd.DataFrame(res["weights_hist"]).T
    assert len(res["equity_curve"]) > 250
    assert w.max().max() <= 0.4 + 1e-9
    assert np.allclose(w.sum(axis=1), 1.0)
