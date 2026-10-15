from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class DataConfig:
    tickers: List[str]
    start: str
    end: str
    interval: str = "1d"
    cache_dir: str = ".cache"

@dataclass
class ModelConfig:
    model_type: str = "ridge"  # 'ridge' | 'random_forest'
    lookback_days: int = 252
    horizon_days: int = 21
    feature_windows: Dict[str, int] = field(default_factory=lambda: {
        "ret_21": 21,
        "ret_63": 63,
        "mom_126": 126,
        "vol_21": 21
    })

@dataclass
class OptimizeConfig:
    long_only: bool = True
    max_weight: float = 0.2
    risk_aversion: float = 5.0  # maior => mais avesso ao risco
    rebalance: str = "M"  # 'M' mensal, 'W' semanal
    transaction_cost_bps: float = 2.0

@dataclass
class ReportConfig:
    output_pdf: str = "report.pdf"
    title: str = "Relatório de Portfólio – Agente Preditivo"

@dataclass
class PipelineConfig:
    data: DataConfig
    model: ModelConfig = field(default_factory=ModelConfig)
    optimize: OptimizeConfig = field(default_factory=OptimizeConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
