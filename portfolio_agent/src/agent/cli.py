import argparse
from .config import PipelineConfig, DataConfig, ModelConfig, OptimizeConfig, ReportConfig
from .pipeline import run_pipeline, generate_pdf_report

def main():
    p = argparse.ArgumentParser(description="Agente Preditivo de Portfólio")
    p.add_argument("--tickers", nargs="+", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--interval", default="1d")
    p.add_argument("--model_type", default="ridge", choices=["ridge","random_forest"])
    p.add_argument("--lookback_days", type=int, default=252)
    p.add_argument("--horizon_days", type=int, default=21)
    p.add_argument("--long_only", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--max_weight", type=float, default=0.2)
    p.add_argument("--rebalance", default="M")
    p.add_argument("--transaction_cost_bps", type=float, default=2.0)
    p.add_argument("--output_pdf", default="report.pdf")
    args = p.parse_args()

    cfg = PipelineConfig(
        data=DataConfig(tickers=args.tickers, start=args.start, end=args.end, interval=args.interval),
        model=ModelConfig(model_type=args.model_type, lookback_days=args.lookback_days, horizon_days=args.horizon_days),
        optimize=OptimizeConfig(long_only=args.long_only, max_weight=args.max_weight, rebalance=args.rebalance,
                                transaction_cost_bps=args.transaction_cost_bps),
        report=ReportConfig(output_pdf=args.output_pdf)
    )
    results = run_pipeline(cfg)
    pdf = generate_pdf_report(results, cfg)
    print("Métricas:", results["metrics"])
    print("PDF gerado em:", pdf)

if __name__ == "__main__":
    main()
