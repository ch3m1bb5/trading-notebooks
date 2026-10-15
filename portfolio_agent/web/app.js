function val(id){ return document.getElementById(id).value.trim(); }
function setStatus(msg){ document.getElementById('status').textContent = msg; }
function renderMetrics(m){
  const el = document.getElementById('metrics');
  el.innerHTML = '';
  Object.entries(m).forEach(([k,v])=>{
    const d = document.createElement('div');
    d.className = 'stat';
    d.innerHTML = `<b>${k}</b><br>${v}`;
    el.appendChild(d);
  });
}

async function runPipeline(){
  setStatus('Executando...');
  const payload = {
    tickers: val('tickers').split(/\s+/),
    start: val('start'),
    end: val('end') || new Date().toISOString().slice(0,10),
    interval: "1d",
    model_type: val('model_type'),
    lookback_days: parseInt(val('lookback')),
    horizon_days: parseInt(val('horizon')),
    long_only: true,
    max_weight: parseFloat(val('max_weight')),
    risk_aversion: 5.0,
    rebalance: val('rebalance'),
    transaction_cost_bps: parseFloat(val('tc')),
    output_pdf: val('pdf')
  };
  try{
    const res = await fetch('/run_full', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(!res.ok){ throw new Error(await res.text()); }
    const data = await res.json();
    renderMetrics(data.metrics);
    Plotly.react('curve', JSON.parse(data.fig_curve).data, JSON.parse(data.fig_curve).layout);
    Plotly.react('weights', JSON.parse(data.fig_weights).data, JSON.parse(data.fig_weights).layout);
    setStatus('Concluído ✓');
  }catch(e){
    setStatus('Erro: ' + e.message);
  }
}

async function exportHTML(){
  setStatus('Gerando HTML...');
  const payload = {
    tickers: val('tickers').split(/\s+/),
    start: val('start'),
    end: val('end') || new Date().toISOString().slice(0,10),
    interval: "1d",
    model_type: val('model_type'),
    lookback_days: parseInt(val('lookback')),
    horizon_days: parseInt(val('horizon')),
    long_only: true,
    max_weight: parseFloat(val('max_weight')),
    risk_aversion: 5.0,
    rebalance: val('rebalance'),
    transaction_cost_bps: parseFloat(val('tc')),
    output_pdf: val('pdf')
  };
  try{
    const res = await fetch('/report_html', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(!res.ok){ throw new Error(await res.text()); }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = payload.output_pdf.replace('.pdf','.html') || 'report.html';
    document.body.appendChild(a);
    a.click(); a.remove();
    window.URL.revokeObjectURL(url);
    setStatus('HTML baixado ✓');
  }catch(e){
    setStatus('Erro: ' + e.message);
  }
}

document.getElementById('run').addEventListener('click', runPipeline);
document.getElementById('export_html').addEventListener('click', exportHTML);
document.getElementById('today').textContent = new Date().toISOString().slice(0,10);
document.getElementById('end').value = new Date().toISOString().slice(0,10);
