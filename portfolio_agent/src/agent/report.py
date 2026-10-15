import os
import datetime
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

def build_pdf_report(output_pdf: str,
                     title: str,
                     metrics: dict,
                     fig_paths: List[str]):
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, height - 2*cm, title)

    # Métricas
    c.setFont("Helvetica", 11)
    y = height - 3.5*cm
    for k, v in metrics.items():
        c.drawString(2*cm, y, f"{k}: {v}")
        y -= 0.6*cm

    # Figuras
    for p in fig_paths:
        y -= 0.8*cm
        try:
            c.drawImage(p, 2*cm, y-10*cm, width=16*cm, height=10*cm, preserveAspectRatio=True, anchor='sw')
            y -= 11*cm
            if y < 5*cm:
                c.showPage()
                y = height - 4*cm
        except Exception:
            continue

    c.showPage()
    c.save()
    return output_pdf

# -------- HTML Report (interativo) --------
from typing import Dict, Any
import plotly.io as pio

def _plotly_script() -> str:
    # embute o plotly.js do pacote Python: relatório auto-contido e compatível
    from plotly.offline import get_plotlyjs
    return "<script>" + get_plotlyjs() + "</script>"

def build_html_report(output_html: str,
                      title: str,
                      metrics: dict,
                      fig_curve=None,
                      fig_weights=None):
    html_parts = []
    html_parts.append(f"""<!doctype html>
<html lang='pt-br'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>{title}</title>
{_plotly_script()}
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Ubuntu, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; margin: 24px; }}
.card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
h1 {{ font-size: 24px; margin-bottom: 8px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
.stat {{ background: #f9fafb; padding: 12px; border-radius: 10px; }}
.footer {{ color: #6b7280; font-size: 12px; margin-top: 24px; }}
</style>
</head>
<body>
<h1>📈 {title}</h1>
<div class='card'>
  <h3>Métricas</h3>
  <div class='grid'>
    {''.join([f"<div class='stat'><b>{k}</b><br>{v}</div>" for k, v in metrics.items()])}
  </div>
</div>
""")
    if fig_curve is not None:
        html_parts.append("<div class='card'><h3>Equity Curve</h3>")
        html_parts.append(pio.to_html(fig_curve, include_plotlyjs=False, full_html=False))
        html_parts.append("</div>")
    if fig_weights is not None:
        html_parts.append("<div class='card'><h3>Pesos por Rebalance</h3>")
        html_parts.append(pio.to_html(fig_weights, include_plotlyjs=False, full_html=False))
        html_parts.append("</div>")
    html_parts.append("""<div class='footer'>Gerado por Portfolio Agent – {}</div></body></html>""".format(datetime.date.today()))
    with open(output_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    return output_html
