import streamlit as st
from datetime import date
from agent.config import PipelineConfig, DataConfig, ModelConfig, OptimizeConfig, ReportConfig
from agent.pipeline import run_pipeline, generate_pdf_report

st.set_page_config(page_title="Agente Preditivo de Portfólio", layout="wide")

st.title("📈 Agente Preditivo de Portfólio – Bolsa Americana")

with st.sidebar:
    st.header("Parâmetros")
    tickers = st.text_input("Tickers (separados por espaço)", "AAPL MSFT AMZN GOOGL META").split()
    start = st.date_input("Data inicial", value=date(2018,1,1))
    end = st.date_input("Data final", value=date.today())
    model_type = st.selectbox("Modelo", ["ridge","random_forest"])
    lookback = st.number_input("Lookback (dias)", min_value=126, max_value=1260, value=252, step=21)
    horizon = st.number_input("Horizonte (dias)", min_value=5, max_value=63, value=21, step=1)
    rebalance = st.selectbox("Rebalance", ["M","W"])
    max_w = st.slider("Peso máximo por ativo", 0.05, 1.0, 0.2, 0.05)
    tc = st.slider("Custos (bps por rebalance)", 0, 50, 2, 1)
    pdf_name = st.text_input("Nome do PDF", "relatorio_portfolio.pdf")
    run_btn = st.button("🚀 Rodar Pipeline")

if run_btn:
    with st.spinner("Executando..."):
        cfg = PipelineConfig(
            data=DataConfig(tickers=tickers, start=str(start), end=str(end)),
            model=ModelConfig(model_type=model_type, lookback_days=int(lookback), horizon_days=int(horizon)),
            optimize=OptimizeConfig(rebalance=rebalance, max_weight=float(max_w), transaction_cost_bps=float(tc)),
            report=ReportConfig(output_pdf=pdf_name)
        )
        try:
            # guarda na sessão: o Streamlit re-executa o script a cada clique
            st.session_state["results"] = run_pipeline(cfg)
            st.session_state["cfg"] = cfg
            st.session_state.pop("pdf", None)
        except Exception as e:
            st.session_state.pop("results", None)
            st.error(f"Falha na pipeline: {e}")

results = st.session_state.get("results")
if results:
    st.success("Pipeline concluída!")

    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Equity Curve")
        st.plotly_chart(results["fig_curve"], use_container_width=True)
    with c2:
        st.subheader("Métricas")
        st.json(results["metrics"])

    st.subheader("Pesos por Rebalance")
    st.plotly_chart(results["fig_weights"], use_container_width=True)

    if st.button("🧾 Gerar PDF"):
        st.session_state["pdf"] = generate_pdf_report(results, st.session_state["cfg"])
    if st.session_state.get("pdf"):
        with open(st.session_state["pdf"], "rb") as f:
            st.download_button("Baixar Relatório PDF", f, file_name=st.session_state["pdf"])
