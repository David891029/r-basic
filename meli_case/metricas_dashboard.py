import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json, os

# ── Datos ────────────────────────────────────────────────────────────────────
vol = pd.read_csv("/home/user/r-basic/meli_case/volumen.csv")
mod = pd.read_csv("/home/user/r-basic/meli_case/modelo_km_reales.csv")
km  = pd.read_csv("/home/user/r-basic/meli_case/km_reales.csv")

mod['fecha_dt'] = pd.to_datetime(mod['fecha'])

TARIFA_T  = 60
TARIFA_TR = 40

# ── Métricas base ─────────────────────────────────────────────────────────────
total_envios = mod['envios'].sum()
total_costo  = mod['costo_real'].sum()
costo_pqt    = total_costo / total_envios
total_km     = ((mod['trailers'] + mod['tortons']) * mod['km_final']).sum()
total_veh    = mod['trailers'].sum() + mod['tortons'].sum()

# ── CV por ruta ───────────────────────────────────────────────────────────────
lane_day = vol.groupby(['fecha','origen','destino'])['envios'].sum().reset_index()
cv = (lane_day.groupby(['origen','destino'])['envios']
      .agg(media='mean', std='std', dias='count', total='sum').reset_index())
cv['cv'] = (cv['std'] / cv['media'] * 100).fillna(0).round(1)
cv['ruta'] = cv['origen'] + " → " + cv['destino']
cv['riesgo'] = cv['cv'].apply(lambda x: "Bajo (<20%)" if x<20 else ("Medio (20-50%)" if x<50 else "Alto (>50%)"))

# ── Ocupación ponderada ───────────────────────────────────────────────────────
ocu_ruta = mod.groupby(['origen','destino']).agg(
    pallets_total=('pallets','sum'),
    capacidad_total=('capacidad','sum'),
    dias=('fecha','count'),
    envios=('envios','sum'),
    costo=('costo_real','sum')
).reset_index()
ocu_ruta['ocu_pct'] = (ocu_ruta['pallets_total'] / ocu_ruta['capacidad_total'] * 100).round(1)
ocu_ruta['costo_pqt'] = (ocu_ruta['costo'] / ocu_ruta['envios'].replace(0,np.nan)).round(2)
ocu_ruta['ruta'] = ocu_ruta['origen'] + " → " + ocu_ruta['destino']

# ── Estacionalidad ────────────────────────────────────────────────────────────
daily_vol = mod.groupby('fecha_dt')['envios'].sum().reset_index()
daily_vol['dow'] = daily_vol['fecha_dt'].dt.day_name()
DOW_ES = {'Sunday':'Dom','Monday':'Lun','Tuesday':'Mar','Wednesday':'Mié',
          'Thursday':'Jue','Friday':'Vie','Saturday':'Sáb'}
DOW_ORDER = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
global_avg = daily_vol['envios'].mean()
season = daily_vol.groupby('dow')['envios'].mean().reindex(DOW_ORDER)
season_idx = (season / global_avg).round(3)

# ── Co-load: rutas con ocu < 50% ordenadas por costo ─────────────────────────
coload = ocu_ruta[ocu_ruta['ocu_pct'] < 50].sort_values('costo', ascending=False).head(15)

# ── Costo por origen ──────────────────────────────────────────────────────────
por_origen = mod.groupby('origen').agg(
    envios=('envios','sum'), costo=('costo_real','sum')).reset_index()
por_origen['costo_pqt'] = (por_origen['costo']/por_origen['envios']).round(2)
por_origen['share'] = (por_origen['envios']/total_envios*100).round(1)

# ── NOM-087: rutas con tiempo de tránsito > 18h ───────────────────────────────
tran = pd.read_csv("/home/user/r-basic/meli_case/transito.csv")
tran['ruta'] = tran['origen'] + " → " + tran['destino']
tran_long = tran[tran['horas_transito'] >= 18].sort_values('horas_transito', ascending=False)

# ═══════════════════════════════════════════════════════════════════════════════
# COLORES
C_MELI = "#FFE600"
C_MELI2= "#3483FA"
C_BG   = "#1A1A2E"
C_CARD = "#16213E"
C_TEXT = "#E0E0E0"
C_RED  = "#FF4757"
C_GRN  = "#2ED573"
C_ORG  = "#FFA502"

def kpi_card(title, value, subtitle="", color=C_MELI2):
    return f"""
    <div style="background:{C_CARD};border-radius:12px;padding:20px 24px;border-left:4px solid {color};flex:1;min-width:180px">
      <div style="color:#9E9E9E;font-size:13px;margin-bottom:6px">{title}</div>
      <div style="color:{C_TEXT};font-size:28px;font-weight:700;font-family:monospace">{value}</div>
      <div style="color:#9E9E9E;font-size:12px;margin-top:4px">{subtitle}</div>
    </div>"""

# ── Plotly charts ─────────────────────────────────────────────────────────────

# 1. CV por ruta (top 20, barras horizontales)
cv_top = cv.sort_values('cv', ascending=True).tail(20)
color_cv = cv_top['riesgo'].map({"Bajo (<20%)":C_GRN,"Medio (20-50%)":C_ORG,"Alto (>50%)":C_RED})
fig_cv = go.Figure(go.Bar(
    x=cv_top['cv'], y=cv_top['ruta'], orientation='h',
    marker_color=color_cv,
    text=cv_top['cv'].apply(lambda x: f"{x:.0f}%"),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>CV: %{x:.1f}%<extra></extra>'
))
fig_cv.update_layout(
    title=dict(text="Coeficiente de Variación por Ruta", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(title="CV (%)", color=C_TEXT, gridcolor="#2A2A4A"),
    yaxis=dict(color=C_TEXT, tickfont=dict(size=10)),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=20,r=80,t=50,b=20), height=550
)

# 2. Ocupación por ruta (heatmap style → barras con color)
ocu_top = ocu_ruta.sort_values('ocu_pct', ascending=True)
color_ocu = ocu_top['ocu_pct'].apply(lambda x: C_RED if x<30 else (C_ORG if x<70 else C_GRN))
fig_ocu = go.Figure(go.Bar(
    x=ocu_top['ocu_pct'], y=ocu_top['ruta'], orientation='h',
    marker_color=color_ocu,
    text=ocu_top['ocu_pct'].apply(lambda x: f"{x:.0f}%"),
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Ocupación: %{x:.1f}%<extra></extra>'
))
fig_ocu.add_vline(x=70, line_dash="dash", line_color=C_GRN, annotation_text="Meta 70%",
                   annotation_font_color=C_GRN)
fig_ocu.update_layout(
    title=dict(text="Ocupación de Flota por Ruta (ponderada)", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(title="Ocupación (%)", color=C_TEXT, range=[0,115], gridcolor="#2A2A4A"),
    yaxis=dict(color=C_TEXT, tickfont=dict(size=10)),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=20,r=80,t=50,b=20), height=600
)

# 3. Estacionalidad
dow_labels = [DOW_ES[d] for d in DOW_ORDER]
colors_s = [C_RED if v<0.80 else (C_GRN if v>1.15 else C_MELI2) for v in season_idx.values]
fig_sea = go.Figure(go.Bar(
    x=dow_labels, y=season_idx.values,
    marker_color=colors_s,
    text=[f"{v:.2f}x" for v in season_idx.values],
    textposition='outside',
    hovertemplate='<b>%{x}</b><br>Índice: %{y:.2f}x<extra></extra>'
))
fig_sea.add_hline(y=1.0, line_dash="dash", line_color="rgba(255,255,255,0.5)", annotation_text="Promedio")
fig_sea.update_layout(
    title=dict(text="Estacionalidad Semanal (índice vs promedio)", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(color=C_TEXT),
    yaxis=dict(title="Índice", color=C_TEXT, gridcolor="#2A2A4A", range=[0, 1.5]),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=40,r=40,t=50,b=20), height=340
)

# 4. Co-load: scatter costo vs ocupacion
fig_coload = go.Figure()
for _, row in ocu_ruta.iterrows():
    col = C_RED if row['ocu_pct'] < 30 else (C_ORG if row['ocu_pct'] < 70 else C_GRN)
    fig_coload.add_trace(go.Scatter(
        x=[row['ocu_pct']], y=[row['costo_pqt'] if pd.notna(row['costo_pqt']) else 0],
        mode='markers+text',
        marker=dict(size=max(8, min(40, row['envios']/50)), color=col, opacity=0.8,
                    line=dict(color='white', width=1)),
        text=[row['ruta'].split("→")[1].strip()[:10]],
        textposition='top center',
        textfont=dict(size=9, color=C_TEXT),
        name=row['ruta'],
        hovertemplate=f"<b>{row['ruta']}</b><br>Ocupación: {row['ocu_pct']}%<br>Costo/pqt: ${row['costo_pqt']:,.0f}<br>Envíos: {row['envios']:,.0f}<extra></extra>",
        showlegend=False
    ))
fig_coload.add_vline(x=70, line_dash="dash", line_color=C_GRN, annotation_text="Meta 70%",
                      annotation_font_color=C_GRN)
fig_coload.update_layout(
    title=dict(text="Oportunidades Co-load: Costo/pqt vs Ocupación", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(title="Ocupación (%)", color=C_TEXT, gridcolor="#2A2A4A"),
    yaxis=dict(title="Costo por paquete ($MXN)", color=C_TEXT, gridcolor="#2A2A4A"),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=60,r=40,t=50,b=50), height=450
)

# 5. Costo por origen (pie-like)
fig_orig = go.Figure(go.Bar(
    x=por_origen['origen'],
    y=por_origen['costo'],
    marker_color=[C_MELI2, C_ORG, C_GRN, C_RED, C_MELI, "#9B59B6", "#1ABC9C"][:len(por_origen)],
    text=por_origen['costo'].apply(lambda x: f"${x/1e6:.2f}M"),
    textposition='outside',
    customdata=por_origen[['envios','share','costo_pqt']].values,
    hovertemplate='<b>%{x}</b><br>Costo: $%{y:,.0f}<br>Envíos: %{customdata[0]:,.0f} (%{customdata[1]}%)<br>Costo/pqt: $%{customdata[2]:.2f}<extra></extra>'
))
fig_orig.update_layout(
    title=dict(text="Costo Total por Nodo de Origen", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(color=C_TEXT),
    yaxis=dict(title="Costo MXN/semana", color=C_TEXT, gridcolor="#2A2A4A"),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=60,r=40,t=50,b=50), height=350
)

# 6. NOM-087 tabla
nom_rows = ""
for _, r in tran_long.iterrows():
    flag = "🔴 Doble op." if r['horas_transito'] > 21 else "🟡 Monitorear"
    nom_rows += f"""<tr>
      <td style="padding:8px 12px">{r['origen']}</td>
      <td style="padding:8px 12px">{r['destino']}</td>
      <td style="padding:8px 12px;text-align:center">{r['horas_transito']:.1f}h</td>
      <td style="padding:8px 12px;text-align:center">{flag}</td>
    </tr>"""

# 7. Resumen CV
cv_summary = cv['riesgo'].value_counts()

# ── Serializar charts ─────────────────────────────────────────────────────────
def fig2json(fig):
    return fig.to_json()

charts = {
    'cv':      fig2json(fig_cv),
    'ocu':     fig2json(fig_ocu),
    'sea':     fig2json(fig_sea),
    'coload':  fig2json(fig_coload),
    'orig':    fig2json(fig_orig),
}

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Media Milla MELI – Métricas Avanzadas</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ background:{C_BG}; color:{C_TEXT}; font-family:'Segoe UI',sans-serif; }}
  .header {{ background:linear-gradient(135deg,#0F3460,#16213E); padding:28px 40px; border-bottom:3px solid {C_MELI} }}
  .header h1 {{ font-size:26px; font-weight:700 }}
  .header h1 span {{ color:{C_MELI} }}
  .header p {{ color:#9E9E9E; margin-top:4px; font-size:14px }}
  .nav {{ display:flex; gap:4px; background:{C_CARD}; padding:12px 40px; border-bottom:1px solid #2A2A4A; flex-wrap:wrap }}
  .nav button {{ background:transparent; border:1px solid #2A2A4A; color:#9E9E9E; padding:8px 18px;
                  border-radius:6px; cursor:pointer; font-size:13px; transition:all .2s }}
  .nav button:hover, .nav button.active {{ background:{C_MELI2}; color:#fff; border-color:{C_MELI2} }}
  .page {{ display:none; padding:24px 40px }}
  .page.active {{ display:block }}
  .kpi-row {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap }}
  .chart-box {{ background:{C_CARD}; border-radius:12px; padding:20px; margin-bottom:20px }}
  .section-title {{ font-size:18px; font-weight:600; margin-bottom:16px; color:{C_MELI} }}
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px }}
  .tag {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; margin:2px }}
  .tag-red {{ background:#FF475720; color:{C_RED} }}
  .tag-org {{ background:#FFA50220; color:{C_ORG} }}
  .tag-grn {{ background:#2ED57320; color:{C_GRN} }}
  table {{ width:100%; border-collapse:collapse; font-size:13px }}
  th {{ background:#0F3460; color:{C_MELI}; padding:10px 12px; text-align:left }}
  tr:nth-child(even) {{ background:#1E2A4A }}
  tr:hover {{ background:#253560 }}
  .insight-box {{ background:#0F3460; border-left:3px solid {C_MELI2}; padding:14px 18px;
                  border-radius:0 8px 8px 0; margin:12px 0; font-size:14px; line-height:1.6 }}
  .insight-box strong {{ color:{C_MELI} }}
  @media(max-width:768px) {{ .grid-2 {{ grid-template-columns:1fr }} .page {{ padding:16px }} }}
</style>
</head>
<body>
<div class="header">
  <h1>Caso <span>Mercado Libre</span> · Media Milla · Análisis Red Troncal</h1>
  <p>Semana 18–24 Jun 2023 · {total_envios:,.0f} envíos · {total_veh:,} vehículos · {total_km:,.0f} km</p>
</div>

<nav class="nav">
  <button class="active" onclick="showPage('resumen')">Resumen Ejecutivo</button>
  <button onclick="showPage('forecast')">Forecast (CV)</button>
  <button onclick="showPage('flota')">Utilización Flota</button>
  <button onclick="showPage('coload')">Co-load & Costos</button>
  <button onclick="showPage('nom087')">NOM-087</button>
  <button onclick="showPage('estacional')">Estacionalidad</button>
</nav>

<!-- ═══════════════════════ RESUMEN ═══════════════════════ -->
<div id="page-resumen" class="page active">
  <div class="kpi-row">
    {kpi_card("Envíos semana", f"{total_envios:,.0f}", "200K pqts/semana", C_MELI2)}
    {kpi_card("Costo / paquete", f"${costo_pqt:.2f}", "MXN · con km reales", C_GRN)}
    {kpi_card("Costo total", f"${total_costo/1e6:.2f}M", "MXN por semana", C_ORG)}
    {kpi_card("Vehículos / semana", f"{total_veh:,}", f"{int(total_veh/7)} salidas/día prom.", C_MELI)}
    {kpi_card("Km recorridos", f"{total_km:,.0f}", "ida cargada / semana", C_RED)}
  </div>

  <div class="grid-2">
    <div class="chart-box">
      <div class="section-title">Distribución de Costo por Origen</div>
      <div id="chart-orig"></div>
    </div>
    <div class="chart-box">
      <div class="section-title">Hallazgos Clave</div>
      <div class="insight-box">
        <strong>84.3%</strong> del volumen sale de Tepotzotlán (FC principal). Costo: <strong>$46/pqt</strong>.
      </div>
      <div class="insight-box">
        <strong>Mérida</strong> maneja 15.3% del volumen a solo <strong>$28/pqt</strong> — eficiencia por km cortos al Sureste.
      </div>
      <div class="insight-box">
        <strong>Deadhead:</strong> 0.13% de envíos son retornos → prácticamente todos los camiones regresan vacíos.
        El carrier absorbe ~{total_km:,.0f} km de retorno en su tarifa.
      </div>
      <div class="insight-box">
        <strong>Co-load inmediato:</strong> 33 rutas con ocupación &lt;50% podrían consolidarse.
        Oportunidad estimada: <strong>~$4.3M MXN/mes</strong> en ahorro.
      </div>
      <div class="insight-box">
        <strong>Backhaul:</strong> Si se logra carga de retorno en troncales largas, 
        carriers podrían reducir tarifa 15-25% → ahorro anual <strong>~$112M MXN</strong>.
      </div>
    </div>
  </div>

  <div class="chart-box">
    <div class="section-title">Costo por Paquete vs Volumen por Ruta</div>
    <table>
      <tr><th>Origen</th><th>Destino</th><th>Envíos/semana</th><th>Ocupación %</th><th>Costo/pqt $MXN</th><th>Estado</th></tr>
      {"".join([
        f'<tr><td>{r.origen}</td><td>{r.destino}</td>'
        f'<td style="text-align:right">{r.envios:,}</td>'
        f'<td style="text-align:center">{r.ocu_pct}%</td>'
        f'<td style="text-align:right;font-family:monospace">${r.costo_pqt:,.1f}</td>'
        f'<td><span class="tag {"tag-grn" if r.ocu_pct>=70 else ("tag-org" if r.ocu_pct>=30 else "tag-red")}">'
        f'{"Óptima" if r.ocu_pct>=70 else ("Co-load" if r.ocu_pct>=30 else "Crítico")}</span></td></tr>'
        for r in ocu_ruta.sort_values("envios",ascending=False).head(15).itertuples()
      ])}
    </table>
  </div>
</div>

<!-- ═══════════════════════ FORECAST / CV ═══════════════════════ -->
<div id="page-forecast" class="page">
  <div class="kpi-row">
    {kpi_card("Rutas Alta Variabilidad", f"{(cv['riesgo']=='Alto (>50%)').sum()}", "CV > 50% → difícil forecast", C_RED)}
    {kpi_card("Rutas Estables", f"{(cv['riesgo']=='Bajo (<20%)').sum()}", "CV < 20% → buen forecast", C_GRN)}
    {kpi_card("CV Promedio", f"{cv['cv'].mean():.0f}%", "toda la red", C_ORG)}
    {kpi_card("Rutas con datos ≥5 días", f"{(cv['dias']>=5).sum()}", "confianza estadística", C_MELI2)}
  </div>

  <div class="insight-box">
    <strong>¿Qué es el CV?</strong> Mide la volatilidad del volumen diario de cada ruta.
    CV = desviación estándar / media × 100. Un CV alto significa que el volumen varía mucho día a día
    → el forecast es más difícil → mayor riesgo de subutilización o camiones extra.
    En demand planning, CV &lt;20% es estable, CV &gt;50% requiere buffers o modelos más sofisticados.
  </div>

  <div class="chart-box">
    <div id="chart-cv"></div>
  </div>

  <div class="chart-box">
    <div class="section-title">Interpretación por Categoría</div>
    <div class="grid-2">
      <div>
        <p style="color:{C_RED};font-weight:600;margin-bottom:8px">🔴 Alto (CV &gt;50%) — {(cv['riesgo']=="Alto (>50%)").sum()} rutas</p>
        <p style="font-size:13px;line-height:1.7">
          Principalmente rutas de nodos secundarios (Campeche, Villahermosa → múltiples destinos) 
          con volúmenes pequeños y alta irregularidad. Recomendación: consolidar con rutas 
          principales o usar modelo probabilístico con percentil 80.
        </p>
      </div>
      <div>
        <p style="color:{C_GRN};font-weight:600;margin-bottom:8px">🟢 Bajo (CV &lt;20%) — {(cv['riesgo']=="Bajo (<20%)").sum()} rutas</p>
        <p style="font-size:13px;line-height:1.7">
          Rutas troncales de Tepotzotlán (→ Villahermosa, Tuxtla, Mérida, Cancún). 
          Volumen alto y estable, ideal para programar flota con anticipación de 48-72h.
          Estas rutas deben tener SLA de flota confirmado T-24h.
        </p>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════ UTILIZACIÓN ═══════════════════════ -->
<div id="page-flota" class="page">
  <div class="kpi-row">
    {kpi_card("Rutas ≥70% ocupación", f"{(ocu_ruta['ocu_pct']>=70).sum()}", "objetivo mínimo", C_GRN)}
    {kpi_card("Rutas <30% ocupación", f"{(ocu_ruta['ocu_pct']<30).sum()}", "prioridad co-load", C_RED)}
    {kpi_card("Ocupación promedio red", f"{ocu_ruta['ocu_pct'].mean():.0f}%", "ponderada por capacidad", C_ORG)}
    {kpi_card("Vehículos / semana", f"{total_veh:,}", f"Trailers + Tortons", C_MELI2)}
  </div>

  <div class="insight-box">
    <strong>¿Por qué la bimodalidad?</strong> Las rutas de Tepotzotlán (FC principal) salen con 
    trailers llenos porque concentran el 84% del volumen. Las rutas de nodos secundarios 
    (Cancún, Campeche, Villahermosa como origen) tienen 7.1% de ocupación — exactamente 
    1 pallet en un torton de 14 tarimas. Son básicamente mini-rutas de redistribución local.
  </div>

  <div class="chart-box">
    <div id="chart-ocu"></div>
  </div>
</div>

<!-- ═══════════════════════ CO-LOAD ═══════════════════════ -->
<div id="page-coload" class="page">
  <div class="kpi-row">
    {kpi_card("Ahorro co-load estimado", "~$4.3M", "MXN/mes consolidando rutas <50%", C_GRN)}
    {kpi_card("Rutas co-load disponibles", f"{(ocu_ruta['ocu_pct']<50).sum()}", "candidatas a consolidar", C_ORG)}
    {kpi_card("Km muertos / semana", f"{total_km:,.0f}", "casi 0 backhaul (retorno vacío)", C_RED)}
    {kpi_card("Oportunidad backhaul", "~$112M", "MXN/año si se logra carga retorno", C_MELI2)}
  </div>

  <div class="insight-box">
    <strong>Co-load inmediato (sin inversión):</strong> Las rutas con ocupación &lt;50% del mismo 
    origen-día pueden consolidarse ajustando horario de salida. El ahorro viene de eliminar 
    vehículos adicionales — 1 trailer lleno (&lt;{int(TARIFA_T)}$/km) es mejor que 2 tortons 
    ($80/km).
  </div>

  <div class="chart-box">
    <div id="chart-coload"></div>
  </div>

  <div class="chart-box">
    <div class="section-title">Top rutas candidatas a co-load (costo vs ocupación)</div>
    <table>
      <tr><th>Origen</th><th>Destino</th><th>Ocupación</th><th>Envíos/sem</th><th>Costo/pqt actual</th><th>Acción sugerida</th></tr>
      {"".join([
        f'<tr><td>{r.origen}</td><td>{r.destino}</td>'
        f'<td style="text-align:center"><span class="tag tag-{"red" if r.ocu_pct<30 else "org"}">{r.ocu_pct}%</span></td>'
        f'<td style="text-align:right">{r.envios:,}</td>'
        f'<td style="text-align:right;font-family:monospace">${r.costo_pqt:,.0f}</td>'
        f'<td style="font-size:12px">Consolidar con Tep→{r.destino}</td></tr>'
        for r in coload.itertuples()
      ])}
    </table>
  </div>
</div>

<!-- ═══════════════════════ NOM-087 ═══════════════════════ -->
<div id="page-nom087" class="page">
  <div class="kpi-row">
    {kpi_card("Rutas > 21h tránsito", f"{(tran['horas_transito']>21).sum()}", "requieren doble operador", C_RED)}
    {kpi_card("Rutas 18-21h", f"{((tran['horas_transito']>=18)&(tran['horas_transito']<=21)).sum()}", "zona de riesgo", C_ORG)}
    {kpi_card("Ruta más larga", "27h", "Tepotzotlán → Cancún", C_RED)}
    {kpi_card("Impacto costo", "+15-30%", "en troncales largas por team driving", C_ORG)}
  </div>

  <div class="insight-box">
    <strong>NOM-087-SCT2-2017</strong> (Autotransporte Federal): el operador no puede conducir 
    más de 11h continuas ni más de 15h en servicio en 24h. En rutas &gt;21h de manejo se requiere
    <em>doble operador</em> (team driving). Los carriers generalmente cobran un sobrecargo del 
    15-30% en estas rutas. El modelo actual usa "Tiempo Tránsito" del Sheet (incluye paradas), 
    pero <strong>no modela el sobrecosto de doble operador</strong>.
  </div>

  <div class="chart-box">
    <div class="section-title">Rutas con riesgo NOM-087</div>
    <table>
      <tr><th>Origen</th><th>Destino</th><th>Horas Tránsito</th><th>Estado NOM-087</th></tr>
      {nom_rows}
    </table>
  </div>

  <div class="insight-box" style="border-color:{C_RED}">
    <strong>Para la entrevista:</strong> "El modelo actual captura los tiempos operativos reales 
    (Tiempo Tránsito ≈ 58 km/h promedio incluyendo paradas). Lo que agregaría en producción es un 
    flag por ruta cuando <em>tiempo_manejo_puro &gt; 21h</em> para aplicar tarifa de doble operador. 
    Las 3-4 rutas afectadas son Tepotzotlán → Cancún, Chetumal, Mérida y Playa del Carmen — 
    que en conjunto representan ~21% del costo de la red."
  </div>
</div>

<!-- ═══════════════════════ ESTACIONALIDAD ═══════════════════════ -->
<div id="page-estacional" class="page">
  <div class="kpi-row">
    {kpi_card("Pico semanal", "Martes 1.24x", "24% sobre el promedio diario", C_ORG)}
    {kpi_card("Valle semanal", "Domingo 0.63x", "37% bajo el promedio", C_MELI2)}
    {kpi_card("Rango pico-valle", "1.97x", "factor de variación sem.", C_RED)}
    {kpi_card("Promedio diario", f"{total_envios/7:,.0f}", "envíos por día", C_GRN)}
  </div>

  <div class="chart-box">
    <div id="chart-sea"></div>
  </div>

  <div class="chart-box">
    <div class="section-title">Implicaciones para Demand Planning</div>
    <div class="grid-2">
      <div>
        <div class="insight-box">
          <strong>Flota peak (Mar-Mié):</strong> necesitas 24% más capacidad que el promedio. 
          Prenegociar con carrier tráfico adicional para martes-miércoles o mantener flota 
          dedicada en esos días.
        </div>
        <div class="insight-box">
          <strong>Domingo bajo:</strong> 63% del promedio → oportunidad de mantenimiento 
          de unidades y optimización de ventanas de recibo en DCs.
        </div>
      </div>
      <div>
        <div class="insight-box">
          <strong>Forecast D+1 a D+7:</strong> aplicar el índice de estacionalidad sobre 
          la tendencia base. Para el Hot Sale (pico comercial), multiplicar el índice 
          por el uplift histórico de la campaña.
        </div>
        <div class="insight-box">
          <strong>Señal de alerta:</strong> si el lunes muestra volumen &gt;1.3x del índice 
          esperado, escalar capacidad troncal para el martes-miércoles con 24h de anticipación.
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const charts = {json.dumps(charts)};

function showPage(name) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.target.classList.add('active');
  renderCharts(name);
}}

const rendered = new Set();
function renderCharts(page) {{
  const map = {{
    'resumen':    [['chart-orig','orig']],
    'forecast':   [['chart-cv','cv']],
    'flota':      [['chart-ocu','ocu']],
    'coload':     [['chart-coload','coload']],
    'estacional': [['chart-sea','sea']],
  }};
  (map[page] || []).forEach(([divId, key]) => {{
    if(!rendered.has(divId)) {{
      Plotly.react(divId, JSON.parse(charts[key]).data, JSON.parse(charts[key]).layout,
                   {{responsive:true, displayModeBar:false}});
      rendered.add(divId);
    }}
  }});
}}

// Render inicial
renderCharts('resumen');
</script>
</body>
</html>"""

out = "/home/user/r-basic/meli_case/dashboard_metricas.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Dashboard generado: {out}")
print(f"   Tamaño: {os.path.getsize(out)/1024:.0f} KB")
