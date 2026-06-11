import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs_version
import plotly.express as px
import json, os

PLOTLY_JS = get_plotlyjs_version()  # el CDN debe coincidir con la versión que serializa

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

# ── Vista día a día ───────────────────────────────────────────────────────────
por_dia = mod.groupby('fecha_dt').agg(
    envios=('envios','sum'), trailers=('trailers','sum'), tortons=('tortons','sum'),
    costo=('costo_real','sum')).reset_index()
por_dia['veh'] = por_dia['trailers'] + por_dia['tortons']
por_dia['cpp'] = (por_dia['costo'] / por_dia['envios']).round(2)
por_dia['dia_lbl'] = por_dia['fecha_dt'].dt.day_name().map(DOW_ES) + " " + por_dia['fecha_dt'].dt.day.astype(str)

# Heatmap ocupación: top rutas por volumen × día
mod['ruta'] = mod['origen'] + " → " + mod['destino']
mod['dia_lbl'] = mod['fecha_dt'].dt.day_name().map(DOW_ES) + " " + mod['fecha_dt'].dt.day.astype(str)
vol_ruta = mod.groupby('ruta')['envios'].sum()
ocu_media = mod.groupby('ruta')['ocupacion'].mean()
top_rutas = (vol_ruta.nlargest(10).index.tolist()
             + ocu_media[vol_ruta >= 10].nsmallest(4).index.tolist())  # contraste: 4 de la cola
heat = (mod[mod['ruta'].isin(top_rutas)]
        .pivot_table(index='ruta', columns='dia_lbl', values='ocupacion', aggfunc='first') * 100)
heat = heat.reindex(index=top_rutas, columns=por_dia['dia_lbl'].tolist()).round(0)

# Vehículos por ruta-día (para hover del heatmap)
heat_veh = (mod[mod['ruta'].isin(top_rutas)]
            .assign(flota=lambda d: d['trailers'].astype(str)+"T+"+d['tortons'].astype(str)+"t")
            .pivot_table(index='ruta', columns='dia_lbl', values='flota', aggfunc='first')
            .reindex(index=top_rutas, columns=por_dia['dia_lbl'].tolist()))

# Peores ruta-día
peores = mod.nlargest(8, 'costo_por_pqt')[
    ['dia_lbl','ruta','envios','tortons','km_final','costo_real','costo_por_pqt']]

# CV con/sin domingo (troncales Tep)
sin_dom = mod[mod['fecha_dt'].dt.dayofweek != 6]
cv_comp = []
for dest in ['Villahermosa','Tuxtla Gutierrez','Mérida','Cancun']:
    full = mod[(mod.origen=='Tepotzotlan') & (mod.destino==dest)]['envios']
    part = sin_dom[(sin_dom.origen=='Tepotzotlan') & (sin_dom.destino==dest)]['envios']
    cv_comp.append((f"Tep → {dest}",
                    round(full.std()/full.mean()*100), round(part.std()/part.mean()*100)))

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

# ── P1: vehículos que llegan a cada destino y horario ────────────────────────
mod['veh_total'] = mod['trailers'] + mod['tortons']
p1_flujos = (mod.groupby(['destino','origen','hora_salida','llegada_hora','llegada_dia'], as_index=False)
             .agg(veh=('veh_total','sum'), dias=('fecha','count'), envios=('envios','sum')))
p1_flujos['veh_dia'] = (p1_flujos['veh'] / p1_flujos['dias']).round(1)
p1_diarios = p1_flujos[p1_flujos['dias'] >= 6].sort_values('veh', ascending=False)
p1_resto = p1_flujos[p1_flujos['dias'] < 6]
p1_dest = (mod.groupby('destino')
           .agg(veh=('veh_total','sum'), envios=('envios','sum'))
           .sort_values('veh', ascending=False).reset_index())
p1_dest['veh_dia'] = (p1_dest['veh'] / 7).round(1)

# ── P2: ocupación por segmento de red ─────────────────────────────────────────
seg = mod.groupby(['origen','destino']).agg(
    pallets=('pallets','sum'), capacidad=('capacidad','sum'),
    envios=('envios','sum'), costo=('costo_real','sum')).reset_index()
seg['ocu'] = seg['pallets'] / seg['capacidad'] * 100
seg['bucket'] = pd.cut(seg['envios'], bins=[-1, 1000, 10000, 1e9],
                       labels=["Cola / micro-rutas (<1K pqts/sem)",
                               "Secundarias (1K–10K pqts/sem)",
                               "Troncales (≥10K pqts/sem)"])
p2_seg = seg.groupby('bucket', observed=True).agg(
    rutas=('ocu','count'), ocu_min=('ocu','min'), ocu_max=('ocu','max'),
    pallets=('pallets','sum'), capacidad=('capacidad','sum'),
    envios=('envios','sum'), costo=('costo','sum')).reset_index()
p2_seg['ocu_pond'] = p2_seg['pallets'] / p2_seg['capacidad'] * 100
ocu_red = mod['pallets'].sum() / mod['capacidad'].sum() * 100

# ── P3: costo total y hallazgo de la cola ─────────────────────────────────────
micro_dias = mod[mod['envios'] < 60]          # ruta-día con menos de 1 pallet
costo_micro = micro_dias['costo_real'].sum()
cpp_coload = (total_costo - costo_micro) / total_envios

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

# 3b. Día a día: envíos (barras) + vehículos (línea, eje secundario)
fig_dia = make_subplots(specs=[[{"secondary_y": True}]])
fig_dia.add_trace(go.Bar(
    x=por_dia['dia_lbl'], y=por_dia['envios'], name="Envíos",
    marker_color=C_MELI2, opacity=0.85,
    text=por_dia['envios'].apply(lambda x: f"{x/1000:.1f}K"), textposition='outside',
    hovertemplate='<b>%{x}</b><br>Envíos: %{y:,.0f}<extra></extra>'), secondary_y=False)
fig_dia.add_trace(go.Scatter(
    x=por_dia['dia_lbl'], y=por_dia['veh'], name="Vehículos",
    mode='lines+markers+text', line=dict(color=C_MELI, width=3),
    marker=dict(size=9), text=por_dia['veh'], textposition='top center',
    textfont=dict(color=C_MELI, size=11),
    hovertemplate='<b>%{x}</b><br>Vehículos: %{y}<extra></extra>'), secondary_y=True)
fig_dia.update_layout(
    title=dict(text="Volumen y Flota por Día", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(color=C_TEXT),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    legend=dict(font=dict(color=C_TEXT), orientation='h', y=1.12),
    margin=dict(l=50,r=50,t=70,b=20), height=380
)
fig_dia.update_yaxes(title_text="Envíos/día", color=C_TEXT, gridcolor="#2A2A4A",
                     secondary_y=False, range=[0, por_dia['envios'].max()*1.25])
fig_dia.update_yaxes(title_text="Vehículos/día", color=C_MELI, showgrid=False,
                     secondary_y=True, range=[0, por_dia['veh'].max()*1.35])

# 3c. Heatmap ocupación ruta × día
hover_txt = [[f"{r}<br>{c}: " +
              (f"ocup {heat.loc[r,c]:.0f}% · {heat_veh.loc[r,c]}" if pd.notna(heat.loc[r,c]) else "sin salida")
              for c in heat.columns] for r in heat.index]
fig_heat = go.Figure(go.Heatmap(
    z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
    colorscale=[[0,'#FF4757'],[0.5,'#FFA502'],[1,'#2ED573']],
    zmin=0, zmax=100,
    text=[[f"{v:.0f}%" if pd.notna(v) else "—" for v in row] for row in heat.values],
    texttemplate="%{text}", textfont=dict(size=10),
    customdata=hover_txt, hovertemplate='%{customdata}<extra></extra>',
    colorbar=dict(title=dict(text="Ocup %", font=dict(color=C_TEXT)),
                  tickfont=dict(color=C_TEXT))
))
fig_heat.update_layout(
    title=dict(text="Ocupación por Ruta × Día (top 14 rutas por volumen)", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(color=C_TEXT, side='top'),
    yaxis=dict(color=C_TEXT, tickfont=dict(size=10), autorange='reversed'),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=20,r=20,t=90,b=20), height=520
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

# ── Chart: business case de las 4 recomendaciones ────────────────────────────
saving_coload      = costo_micro * 52
saving_coload_real = saving_coload * 0.70
saving_multistop   = total_costo * 0.04 * 52
saving_cv          = total_costo * 0.05 * 52
saving_carriers    = total_costo * 0.08 * 52

recs = [
    ("1. Co-load\n(micro-rutas → troncales)",     saving_coload_real / 1e6, "Sin inversión, solo coordinación", C_GRN, 1),
    ("2. Multi-stop\n(Riviera Maya / Campeche)",   saving_multistop   / 1e6, "Cambio de ruteamiento",            C_GRN, 1),
    ("3. Planeación diferenciada\npor CV",          saving_cv          / 1e6, "Proceso + herramienta",            C_ORG, 2),
    ("4. Negociación tarifaria\n(NOM-087 + picos)", saving_carriers    / 1e6, "Contrato + datos Hot Sale",        C_ORG, 2),
]
rec_labels = [r[0] for r in recs]
rec_vals   = [r[1] for r in recs]
rec_colors = [r[3] for r in recs]

fig_rec = go.Figure(go.Bar(
    x=rec_vals[::-1], y=rec_labels[::-1], orientation='h',
    marker_color=rec_colors[::-1],
    text=[f"${v:.0f}M/año" for v in rec_vals[::-1]],
    textposition='outside',
    customdata=[[r[2], f"Ola {r[4]}"] for r in recs[::-1]],
    hovertemplate='<b>%{y}</b><br>Ahorro: $%{x:.0f}M MXN/año<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>'
))
fig_rec.update_layout(
    title=dict(text="Potencial de ahorro anual por recomendación (MXN)", font=dict(color=C_TEXT, size=16)),
    xaxis=dict(title="Ahorro anual estimado (M MXN)", color=C_TEXT, gridcolor="#2A2A4A"),
    yaxis=dict(color=C_TEXT, tickfont=dict(size=11)),
    paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
    margin=dict(l=20, r=120, t=50, b=30), height=320
)

# ── Serializar charts ─────────────────────────────────────────────────────────
def fig2json(fig):
    return fig.to_json()

charts = {
    'cv':      fig2json(fig_cv),
    'ocu':     fig2json(fig_ocu),
    'sea':     fig2json(fig_sea),
    'coload':  fig2json(fig_coload),
    'orig':    fig2json(fig_orig),
    'dia':     fig2json(fig_dia),
    'heat':    fig2json(fig_heat),
    'rec':     fig2json(fig_rec),
}

# Tabla peores ruta-día
peores_rows = "".join([
    f'<tr><td>{r.dia_lbl}</td><td>{r.ruta}</td>'
    f'<td style="text-align:right">{r.envios:,}</td>'
    f'<td style="text-align:right">{r.km_final:,.0f}</td>'
    f'<td style="text-align:right;font-family:monospace">${r.costo_real:,.0f}</td>'
    f'<td style="text-align:right;font-family:monospace;color:{C_RED};font-weight:700">${r.costo_por_pqt:,.0f}</td></tr>'
    for r in peores.itertuples()])

# Tabla CV con/sin domingo
cvdom_rows = "".join([
    f'<tr><td>{ruta}</td><td style="text-align:center">{full}%</td>'
    f'<td style="text-align:center;color:{C_GRN};font-weight:600">{part}%</td></tr>'
    for ruta, full, part in cv_comp])

# Tablas P1: resumen por destino + flujos diarios
DIA_LLEGA = {0: "mismo día", 1: "D+1", 2: "D+2"}
p1_dest_rows = "".join([
    f'<tr><td>{r.destino}</td>'
    f'<td style="text-align:center;font-family:monospace;font-weight:700">{r.veh_dia:.1f}</td>'
    f'<td style="text-align:right">{r.envios:,}</td></tr>'
    for r in p1_dest.itertuples()])
p1_flujo_rows = "".join([
    f'<tr{" style=background:#3d1f2e" if r.llegada_dia == 2 else ""}>'
    f'<td>{r.origen} → {r.destino}</td>'
    f'<td style="text-align:center;font-family:monospace">{r.veh_dia:.1f}</td>'
    f'<td style="text-align:center">{r.hora_salida}</td>'
    f'<td style="text-align:center;font-weight:600">{r.llegada_hora}</td>'
    f'<td style="text-align:center;color:{C_RED if r.llegada_dia == 2 else (C_GRN if r.llegada_dia == 0 else C_TEXT)}">'
    f'{DIA_LLEGA[r.llegada_dia]}</td></tr>'
    for r in p1_diarios.itertuples()])

# Tabla P2: ocupación por segmento
p2_rows = "".join([
    f'<tr><td>{r.bucket}</td>'
    f'<td style="text-align:center">{r.rutas}</td>'
    f'<td style="text-align:right">{r.envios:,}</td>'
    f'<td style="text-align:center;font-family:monospace;font-weight:700;'
    f'color:{C_GRN if r.ocu_pond >= 70 else (C_ORG if r.ocu_pond >= 30 else C_RED)}">{r.ocu_pond:.0f}%</td>'
    f'<td style="text-align:center">{r.ocu_min:.0f}%–{r.ocu_max:.0f}%</td>'
    f'<td style="text-align:right;font-family:monospace">${r.costo/1e6:.2f}M</td></tr>'
    for r in p2_seg.sort_values('envios', ascending=False).itertuples()])

# Tabla P3: desglose del costo
p3_rows = "".join([
    f'<tr><td>{c}</td><td style="text-align:right;font-family:monospace;font-weight:600">{v}</td><td style="color:#9E9E9E">{d}</td></tr>'
    for c, v, d in [
        ("Envíos totales / semana", f"{total_envios:,.0f}", "7 días, 18–24 jun"),
        ("Costo total / semana", f"${total_costo:,.0f}", "km reales × tarifa por vehículo"),
        ("Costo por paquete (as-is)", f"${costo_pqt:.2f}", "costo total ÷ envíos"),
        ("· del cual: micro-rutas (<1 pallet/día)", f"${costo_micro:,.0f}",
         f"{costo_micro/total_costo:.1%} del costo con {micro_dias['envios'].sum()/total_envios:.2%} del volumen"),
        ("Costo por paquete consolidando (co-load)", f"${cpp_coload:.2f}",
         f"−{1-cpp_coload/costo_pqt:.1%} vs as-is, sin tocar SLA de troncales"),
    ]])

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Media Milla MELI – Métricas Avanzadas</title>
<script src="https://cdn.plot.ly/plotly-{PLOTLY_JS}.min.js"></script>
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
  <button onclick="showPage('diadia')">Día a Día</button>
  <button onclick="showPage('recs')" style="border-color:{C_MELI};color:{C_MELI}">⚡ Recomendaciones</button>
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

  <div class="chart-box">
    <div class="section-title">P3 · ¿Cuál es el costo total de la red y el costo por paquete?</div>
    <table>
      <tr><th>Concepto</th><th>Valor</th><th>Detalle</th></tr>
      {p3_rows}
    </table>
    <div class="insight-box" style="margin-top:14px">
      <strong>Respuesta:</strong> la red cuesta <strong>${total_costo/1e6:.2f}M MXN/semana ≈
      ${costo_pqt:.2f} por paquete</strong> (con km reales por ruta). El hallazgo:
      <strong>{micro_dias['envios'].sum()/total_envios:.2%} del volumen (micro-rutas) consume
      {costo_micro/total_costo:.1%} del costo</strong> — tortons casi vacíos recorriendo 400–1,600 km.
      Consolidando esa cola como co-load el costo baja a <strong>${cpp_coload:.2f}/pqt
      (−{1-cpp_coload/costo_pqt:.1%})</strong>.
    </div>
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

  <div class="chart-box">
    <div class="section-title">P1 · ¿Cuántos vehículos estarían llegando al destino y en qué horario?</div>
    <div class="grid-2">
      <div>
        <p style="font-weight:600;margin-bottom:10px;color:{C_TEXT}">Vehículos que recibe cada destino (promedio diario)</p>
        <table>
          <tr><th>Destino</th><th>Vehículos / día</th><th>Envíos / sem</th></tr>
          {p1_dest_rows}
        </table>
      </div>
      <div>
        <p style="font-weight:600;margin-bottom:10px;color:{C_TEXT}">Flujos diarios: salida, llegada y día de arribo</p>
        <table>
          <tr><th>Flujo</th><th>Veh/día</th><th>Sale</th><th>Llega</th><th>Día</th></tr>
          {p1_flujo_rows}
        </table>
      </div>
    </div>
    <div class="insight-box" style="margin-top:14px">
      <strong>Respuesta:</strong> la red recibe <strong>~{p1_dest['veh_dia'].sum():.0f} vehículos/día</strong>
      en 8 destinos. Las troncales de Tepotzotlán salen 20:30–22:30 y llegan al sureste en
      <strong>D+1 entre 11:19 (Tuxtla) y 23:30 (Cancún)</strong>; las radiales de Mérida salen 22:30 y
      llegan de madrugada. <strong>Playa del Carmen es la excepción: llega D+2 a las 00:30</strong> —
      toda promesa D+1 en la Riviera Maya depende del inventario posicionado en el hub de Mérida.
      Los {len(p1_resto)} flujos restantes son micro-rutas esporádicas (1 torton, 1–5 días/sem)
      con {p1_resto['envios'].sum():,} envíos en total (&lt;0.3% del volumen).
    </div>
  </div>

  <div class="chart-box">
    <div class="section-title">P2 · ¿Qué indicadores de ocupación tiene la red?</div>
    <table>
      <tr><th>Segmento</th><th>Rutas</th><th>Envíos / sem</th><th>Ocupación ponderada</th><th>Rango</th><th>Costo / sem</th></tr>
      {p2_rows}
    </table>
    <div class="insight-box" style="margin-top:14px">
      <strong>Respuesta:</strong> la ocupación de red ponderada es <strong>{ocu_red:.0f}%</strong>, pero el
      promedio esconde tres realidades: <strong>troncales 83–94%</strong> (sanas, en target),
      <strong>secundarias 24–50%</strong> (precio de mantener frecuencia diaria por SLA) y
      <strong>cola a ~7%</strong> (1 pallet en un torton de 14 — dinero quemado).
      La métrica accionable no es el promedio: es <em>cuántos pallets de holgura tiene cada salida</em>,
      porque esa holgura es la capacidad disponible para co-load.
    </div>
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

<!-- ═══════════════════════ DÍA A DÍA ═══════════════════════ -->
<div id="page-diadia" class="page">
  <div class="kpi-row">
    {kpi_card("Pico de flota", f"{por_dia['veh'].max()} veh", f"{por_dia.loc[por_dia['veh'].idxmax(),'dia_lbl']} · {por_dia['envios'].max():,.0f} envíos", C_ORG)}
    {kpi_card("Valle de flota", f"{por_dia['veh'].min()} veh", f"{por_dia.loc[por_dia['veh'].idxmin(),'dia_lbl']} · {por_dia['envios'].min():,.0f} envíos", C_MELI2)}
    {kpi_card("Oscilación intra-semana", f"{por_dia['veh'].max()/por_dia['veh'].min():.1f}x", "la flota no es constante", C_RED)}
    {kpi_card("Peor $/pqt del día", f"${por_dia['cpp'].max():.1f}", f"{por_dia.loc[por_dia['cpp'].idxmax(),'dia_lbl']} — cae volumen, persiste la cola", C_RED)}
  </div>

  <div class="chart-box">
    <div id="chart-dia"></div>
  </div>

  <div class="insight-box">
    <strong>La flota oscila {por_dia['veh'].max()/por_dia['veh'].min():.1f}x dentro de la semana</strong>
    ({por_dia['veh'].min()} → {por_dia['veh'].max()} vehículos). La planeación no puede ser por promedio:
    se programa <strong>por día de semana</strong>. Incluso Tep→Villahermosa va de 3 trailers el domingo a 7 el martes.
  </div>

  <div class="chart-box">
    <div id="chart-heat"></div>
  </div>

  <div class="grid-2">
    <div class="chart-box">
      <div class="section-title">Peores ruta-día ($/paquete)</div>
      <table>
        <tr><th>Día</th><th>Ruta</th><th>Envíos</th><th>Km</th><th>Costo</th><th>$/pqt</th></tr>
        {peores_rows}
      </table>
      <div class="insight-box" style="margin-top:14px">
        El ejemplo más citables: <strong>1 paquete de Tapachula a Mérida = $44,776</strong> —
        un torton de 14 tarimas recorriendo 1,119 km por un solo paquete. Pasó 2 veces en la semana.
      </div>
    </div>
    <div class="chart-box">
      <div class="section-title">CV troncales: efecto domingo</div>
      <table>
        <tr><th>Troncal</th><th>CV 7 días</th><th>CV sin domingo</th></tr>
        {cvdom_rows}
      </table>
      <div class="insight-box" style="margin-top:14px">
        El CV crudo de troncales (20–31%) está <strong>inflado por el valle del domingo</strong> (0.63x) —
        patrón semanal predecible, no ruido. Excluyéndolo, todas quedan bajo 20%.
        En producción, el CV se mide sobre el <strong>residual del forecast</strong>, no sobre la demanda cruda.
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════ RECOMENDACIONES ═══════════════════════ -->
<div id="page-recs" class="page">
  <div class="kpi-row">
    {kpi_card("Ahorro total identificado", f"${(saving_coload_real+saving_multistop+saving_cv+saving_carriers)/1e6:.0f}M", "MXN/año · 4 iniciativas", C_GRN)}
    {kpi_card("Sin inversión (Ola 1)", f"${(saving_coload_real+saving_multistop)/1e6:.0f}M", "MXN/año · co-load + multi-stop", C_MELI)}
    {kpi_card("Costo actual/pqt", f"${costo_pqt:.2f}", "MXN · as-is", C_RED)}
    {kpi_card("Objetivo/pqt", f"${costo_pqt*(1-(saving_coload_real+saving_multistop+saving_cv+saving_carriers)/(total_costo*52)):.2f}", "MXN · con las 4 iniciativas", C_GRN)}
  </div>

  <div class="chart-box">
    <div id="chart-rec"></div>
  </div>

  <!-- REC 1: CO-LOAD -->
  <div class="chart-box">
    <div class="section-title" style="color:{C_GRN}">Recomendación 1 · Co-load (Ola 1 — 0–8 semanas)</div>
    <div class="grid-2">
      <div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>¿Qué?</strong> Las micro-rutas (&lt;1 pallet/día) despachan tortons casi vacíos.
          En lugar de salida propia, el paquete espera el vehículo troncal de Tepotzotlán del mismo día
          (<strong>cutoff 20:30 o 22:30</strong>) y viaja como carga adicional.
          No toca el SLA de las troncales porque éstas salen con holgura del 6–17%.
        </div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Evidencia del modelo:</strong><br>
          · {micro_dias['envios'].sum():,} paquetes/semana en micro-rutas = {micro_dias['envios'].sum()/total_envios:.2%} del volumen<br>
          · Generan <strong>${costo_micro:,.0f}</strong>/semana = {costo_micro/total_costo:.1%} del costo total<br>
          · CPP as-is: <strong>${costo_pqt:.2f}</strong> → con co-load: <strong>${cpp_coload:.2f}</strong> (−{1-cpp_coload/costo_pqt:.1%})
        </div>
      </div>
      <div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Cómo implementar:</strong><br>
          1. Identificar paquetes con destino coincidente con troncal del mismo día<br>
          2. Verificar espacio disponible (holgura = {(1-ocu_red/100)*100:.0f}% promedio red)<br>
          3. Ajustar cutoff de recepción en FC para incluir esos paquetes antes de las 20:30<br>
          4. Medir: paquetes consolidados / paquetes elegibles como KPI semanal
        </div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Ahorro estimado:</strong><br>
          ${saving_coload_real/1e6:.0f}M MXN/año (captura conservadora del 70% de la oportunidad)<br>
          <strong>Riesgo:</strong> paquetes que llegan al FC después del cutoff quedan para el día siguiente.
          Mitigar con regla: si cutoff se pierde, se activa torton local <em>solo si hay ≥0.5 pallet</em>.
        </div>
      </div>
    </div>
  </div>

  <!-- REC 2: MULTI-STOP -->
  <div class="chart-box">
    <div class="section-title" style="color:{C_GRN}">Recomendación 2 · Multi-stop Riviera Maya (Ola 1 — 0–8 semanas)</div>
    <div class="grid-2">
      <div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>¿Qué?</strong> Cancún, Playa del Carmen y Chetumal están en el mismo corredor
          (Hwy 307). Hoy salen 3 vehículos separados desde Tepotzotlán. Un trailer con
          <strong>primer stop Cancún, segundo Playa, tercero Chetumal</strong> reduciría de 3 a 1 unidad
          (o 2 si el volumen lo justifica).
        </div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Evidencia:</strong><br>
          · Tep→Cancún: 13 veh/sem, {ocu_ruta[ocu_ruta['ruta']=='Tepotzotlan → Cancun']['ocu_pct'].values[0]:.0f}% ocup<br>
          · Tep→Playa: 10 veh/sem, {ocu_ruta[ocu_ruta['ruta']=='Tepotzotlan → Playa']['ocu_pct'].values[0]:.0f}% ocup<br>
          · Tep→Chetumal: 7 veh/sem, {ocu_ruta[ocu_ruta['ruta']=='Tepotzotlan → Chetumal']['ocu_pct'].values[0]:.0f}% ocup<br>
          Volumen total Riviera Maya: {int(ocu_ruta[ocu_ruta['ruta'].isin(['Tepotzotlan → Cancun','Tepotzotlan → Playa','Tepotzotlan → Chetumal'])]['envios'].sum()):,} pqts/sem
        </div>
      </div>
      <div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Cómo implementar:</strong><br>
          1. Secuenciar carga en el trailer: el último destino se carga primero (Chetumal abajo)<br>
          2. Ajustar ventanas de entrega en los 3 DCs para el mismo horario de arribo<br>
          3. Negociar con carrier la tarifa por km total de ruta multi-stop vs 3 rutas directas<br>
          4. Monitorear tiempo de ciclo del vehículo (retorno más tarde = ¿afecta siguiente día?)
        </div>
        <div class="insight-box" style="border-color:{C_GRN}">
          <strong>Ahorro estimado:</strong><br>
          ${saving_multistop/1e6:.0f}M MXN/año (~4% del costo total)<br>
          <strong>Restricción:</strong> si Playa llega actualmente D+2, el multi-stop <em>no empeora</em>
          ese SLA. Cancún y Chetumal sí necesitan validación de ventana de entrega.
        </div>
      </div>
    </div>
  </div>

  <!-- REC 3: CV -->
  <div class="chart-box">
    <div class="section-title" style="color:{C_ORG}">Recomendación 3 · Planeación diferenciada por CV (Ola 2 — 8–16 semanas)</div>
    <div class="grid-2">
      <div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>¿Qué?</strong> Hoy se planea flota con el mismo modelo para todas las rutas.
          Las troncales (CV 20–31%, predecible) pueden programarse con T−48h.
          Las rutas de cola (CV 66–99%) necesitan un modelo diferente:
          <em>confirmar flota T−4h con umbral mínimo de consolidación</em>.
        </div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Evidencia:</strong><br>
          · Troncales sin domingo: CV &lt;20% → forecast preciso, flota dedicada<br>
          · CV del domingo infla el crudo a 20–31% → no es ruido, es patrón semanal<br>
          · Rutas cola: CV 66–99% → 1 semana de datos no alcanza para forecast confiable
        </div>
      </div>
      <div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Cómo implementar:</strong><br>
          1. Segmentar rutas en 3 categorías: alta frecuencia (≥6 días), media (3–5 días), esporádica<br>
          2. Modelo 1 (troncales): SARIMA semanal con índice estacionalidad día de semana<br>
          3. Modelo 2 (intermitentes): regresión con variables proxy (ventas D−1, promociones)<br>
          4. Regla (cola): no despachar torton propio si &lt;0.5 pallet → co-load automático
        </div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Ahorro estimado:</strong><br>
          ${saving_cv/1e6:.0f}M MXN/año (~5% costo total)<br>
          <strong>Prerequisito:</strong> 8–12 semanas de histórico (mín.) para calibrar modelos +
          datos de pico Hot Sale para separar tendencia de estacionalidad promotional.
        </div>
      </div>
    </div>
  </div>

  <!-- REC 4: CARRIERS -->
  <div class="chart-box">
    <div class="section-title" style="color:{C_ORG}">Recomendación 4 · Negociación tarifaria con carriers (Ola 2 — 8–16 semanas)</div>
    <div class="grid-2">
      <div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>¿Qué?</strong> Con datos de NOM-087 (doble operador en 4 rutas largas),
          volumen consolidado por co-load y comportamiento de pico Hot Sale se puede presentar
          un caso de negociación: <em>mayor volumen garantizado + mejor previsibilidad = tarifa menor</em>.
          Objetivo: −8–10% en troncales largas.
        </div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Evidencia:</strong><br>
          · {(tran['horas_transito']>21).sum()} rutas &gt;21h requieren doble operador (costo NOM no modelado)<br>
          · La red concentra 84% del volumen en Tepotzotlán → poder de negociación alto<br>
          · Flota oscila {por_dia['veh'].max()/por_dia['veh'].min():.1f}x intrasemanal → carrier absorbe riesgo hoy;<br>
            con forecast diferenciado, MELI puede ofrecer mayor predictibilidad
        </div>
      </div>
      <div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Cómo implementar:</strong><br>
          1. Levantar datos reales de doble operador por ruta (gap actual del modelo)<br>
          2. Conseguir histórico de Hot Sale/Buen Fin (al menos 1 ciclo) para modelar picos<br>
          3. Preparar cuadro de volumen garantizado semanal por ruta como argumento<br>
          4. Negociar tarifa diferenciada: troncal dedicada ($55/km) vs spot ($60/km)
        </div>
        <div class="insight-box" style="border-color:{C_ORG}">
          <strong>Ahorro estimado:</strong><br>
          ${saving_carriers/1e6:.0f}M MXN/año (~8% costo total)<br>
          <strong>Condición:</strong> requiere datos de al menos 2 meses para argumento estadístico sólido.
          Mientras tanto, usar 1 semana para detectar rutas con sobrecosto NOM-087 no declarado.
        </div>
      </div>
    </div>
  </div>

  <!-- Resumen de implementación -->
  <div class="chart-box">
    <div class="section-title">Hoja de ruta de implementación</div>
    <table>
      <tr><th>#</th><th>Iniciativa</th><th>Ola</th><th>Semanas</th><th>Inversión</th><th>Ahorro/año estimado</th><th>Prerequisito</th></tr>
      <tr>
        <td>1</td><td>Co-load micro-rutas</td>
        <td><span class="tag tag-grn">Ola 1</span></td><td>0–8</td><td>Sin inversión</td>
        <td style="font-family:monospace;font-weight:700;color:{C_GRN}">${saving_coload_real/1e6:.0f}M MXN</td>
        <td>Coordinación FC + carrier</td>
      </tr>
      <tr>
        <td>2</td><td>Multi-stop Riviera Maya</td>
        <td><span class="tag tag-grn">Ola 1</span></td><td>0–8</td><td>Acuerdo tarifario</td>
        <td style="font-family:monospace;font-weight:700;color:{C_GRN}">${saving_multistop/1e6:.0f}M MXN</td>
        <td>Validar ventanas de entrega DC</td>
      </tr>
      <tr>
        <td>3</td><td>Planeación diferenciada por CV</td>
        <td><span class="tag tag-org">Ola 2</span></td><td>8–16</td><td>Herramienta + proceso</td>
        <td style="font-family:monospace;font-weight:700;color:{C_ORG}">${saving_cv/1e6:.0f}M MXN</td>
        <td>8–12 semanas de histórico</td>
      </tr>
      <tr>
        <td>4</td><td>Negociación tarifaria carriers</td>
        <td><span class="tag tag-org">Ola 2</span></td><td>8–16</td><td>Datos Hot Sale + legal</td>
        <td style="font-family:monospace;font-weight:700;color:{C_ORG}">${saving_carriers/1e6:.0f}M MXN</td>
        <td>Histórico picos + datos NOM-087</td>
      </tr>
    </table>
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
    'diadia':     [['chart-dia','dia'],['chart-heat','heat']],
    'recs':       [['chart-rec','rec']],
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
