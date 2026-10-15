from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
from .config import PipelineConfig, DataConfig, ModelConfig, OptimizeConfig, ReportConfig
from .pipeline import run_pipeline, generate_pdf_report

app = FastAPI(title="Portfolio Predictive Agent API")

class RunRequest(BaseModel):
    tickers: List[str]
    start: str
    end: str
    interval: str = "1d"
    model_type: str = "ridge"
    lookback_days: int = 252
    horizon_days: int = 21
    long_only: bool = True
    max_weight: float = 0.2
    risk_aversion: float = 5.0
    rebalance: str = "M"
    transaction_cost_bps: float = 2.0
    output_pdf: Optional[str] = "report.pdf"

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run")
def run(req: RunRequest):
    cfg = PipelineConfig(
        data=DataConfig(tickers=req.tickers, start=req.start, end=req.end, interval=req.interval),
        model=ModelConfig(model_type=req.model_type, lookback_days=req.lookback_days, horizon_days=req.horizon_days),
        optimize=OptimizeConfig(long_only=req.long_only, max_weight=req.max_weight, risk_aversion=req.risk_aversion,
                                rebalance=req.rebalance, transaction_cost_bps=req.transaction_cost_bps),
        report=ReportConfig(output_pdf=req.output_pdf)
    )
    results = run_pipeline(cfg)
    pdf_path = generate_pdf_report(results, cfg)
    # Retorna métricas + caminhos dos artefatos
    return {
        "metrics": results["metrics"],
        "pdf": pdf_path
    }


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import plotly.io as pio
import os

app.mount("/web", StaticFiles(directory="web", html=True), name="web")

@app.get("/plotly.min.js")
def plotly_js():
    # plotly.js embutido no pacote Python -> sempre compatível com as figuras geradas
    from fastapi.responses import Response
    from plotly.offline import get_plotlyjs
    return Response(get_plotlyjs(), media_type="application/javascript")

@app.get("/")
def root():
    return RedirectResponse(url="/web/")

@app.post("/run_full")
def run_full(req: RunRequest):
    cfg = PipelineConfig(
        data=DataConfig(tickers=req.tickers, start=req.start, end=req.end, interval=req.interval),
        model=ModelConfig(model_type=req.model_type, lookback_days=req.lookback_days, horizon_days=req.horizon_days),
        optimize=OptimizeConfig(long_only=req.long_only, max_weight=req.max_weight, risk_aversion=req.risk_aversion,
                                rebalance=req.rebalance, transaction_cost_bps=req.transaction_cost_bps),
        report=ReportConfig(output_pdf=req.output_pdf or "report.pdf")
    )
    results = run_pipeline(cfg)
    # Serialize figures for client-side Plotly
    fig_curve_json = pio.to_json(results["fig_curve"])
    fig_weights_json = pio.to_json(results["fig_weights"])
    return {
        "metrics": results["metrics"],
        "fig_curve": fig_curve_json,
        "fig_weights": fig_weights_json
    }

@app.post("/report_html")
def report_html(req: RunRequest):
    cfg = PipelineConfig(
        data=DataConfig(tickers=req.tickers, start=req.start, end=req.end, interval=req.interval),
        model=ModelConfig(model_type=req.model_type, lookback_days=req.lookback_days, horizon_days=req.horizon_days),
        optimize=OptimizeConfig(long_only=req.long_only, max_weight=req.max_weight, risk_aversion=req.risk_aversion,
                                rebalance=req.rebalance, transaction_cost_bps=req.transaction_cost_bps),
        report=ReportConfig(output_pdf=req.output_pdf or "report.pdf")
    )
    results = run_pipeline(cfg)
    from .pipeline import generate_html_report
    html_path = generate_html_report(results, cfg)
    return FileResponse(html_path, media_type="text/html", filename=os.path.basename(html_path))
