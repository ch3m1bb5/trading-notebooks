# Portfolio Agent – Modelagem Preditiva de Portfólios (Bolsa Americana)

Um agente completo (back-end + front-end) para:
- **Coletar dados** de ações americanas (`yfinance`)
- **Criar features** (momentum, volatilidade, retornos)
- **Treinar modelos de ML** (Ridge/RandomForest) para **prever retornos esperados**
- **Otimizar carteiras** (Markowitz com `cvxpy`) com restrições
- **Backtesting** com custos de transação e rebalanceamento
- **Relatórios em PDF** com métricas e gráficos
- **Dashboard interativo** via **Streamlit**
- **API** via **FastAPI**

> ⚠️ Este projeto é educacional. Não é recomendação de investimento.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

## Execução rápida

**Dashboard (Streamlit)**:
```bash
streamlit run app_streamlit/app.py
```

**API (FastAPI)**:
```bash
uvicorn agent.api_fastapi:app --reload
```

**CLI**:
```bash
python -m agent.cli --tickers AAPL MSFT GOOGL --start 2018-01-01 --end 2025-01-01
```

## Estrutura

```
.
├── requirements.txt
├── README.md
├── src/agent
│   ├── __init__.py
│   ├── config.py
│   ├── data.py
│   ├── features.py
│   ├── models.py
│   ├── optimize.py
│   ├── backtest.py
│   ├── visualize.py
│   ├── report.py
│   ├── pipeline.py
│   ├── api_fastapi.py
│   └── cli.py
├── app_streamlit
│   └── app.py
├── tests
│   └── test_smoke.py
└── examples
    └── example_config.yaml
```

## Notas

- O Streamlit chama diretamente a pipeline do pacote `agent`.
- A otimização usa `cvxpy`; se houver dificuldades de instalação, a pipeline cai para um solver **sem restrições** (weights ≥ 0, soma=1) com projeção no simplex.
- Para relatórios em PDF, as figuras são salvas como imagens temporárias e inseridas via `reportlab`.

Boa sorte & bons trades! ✨


## UI HTML (FastAPI + estático)

1. Inicie a API:
```bash
uvicorn agent.api_fastapi:app --reload
```

2. Acesse o front-end HTML:
```
http://localhost:8000/
```

- Botão **Rodar** chama `POST /run_full` e desenha os gráficos diretamente no navegador.
- Botão **Exportar HTML** chama `POST /report_html` e baixa um relatório HTML interativo (auto-contido).
