"""Genera el dashboard HTML del caso — mismo código que irá en el Colab."""
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import get_plotlyjs_version

PLOTLY_JS = get_plotlyjs_version()  # el CDN debe coincidir con la versión que serializa
PQTS_POR_PALLET = 60
DIAS = {6: "Dom", 0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb"}
AZUL, NARANJA, VERDE, ROJO = "#1a4b8c", "#f39c12", "#27ae60", "#e74c3c"

def generar_dashboard(modelo, archivo="dashboard_meli.html"):
    m = modelo.copy()
    m["ruta"] = m["origen"] + " → " + m["destino"]
    total_env, total_costo = m["envios"].sum(), m["costo"].sum()
    cpp_red = total_costo / total_env
    ocup_red = m["pallets"].sum() / m["capacidad"].sum()
    dias_n = m["fecha"].nunique()

    # --- agregado semanal por ruta ---
    rutas = (m.groupby("ruta", as_index=False)
               .agg(envios=("envios", "sum"), pallets=("pallets", "sum"),
                    trailers=("trailers", "sum"), tortons=("tortons", "sum"),
                    capacidad=("capacidad", "sum"), costo=("costo", "sum")))
    rutas["ocupacion"] = rutas["pallets"] / rutas["capacidad"]
    rutas["cpp"] = rutas["costo"] / rutas["envios"]
    rutas = rutas.sort_values("envios", ascending=False)

    # --- hallazgo: micro-rutas (<1 pallet/día) ---
    micro = m[m["envios"] < PQTS_POR_PALLET]
    costo_micro = micro["costo"].sum()
    cpp_sin_micro = (total_costo - costo_micro) / total_env

    figs = []

    # 1. Volumen diario
    vd = m.groupby("fecha", as_index=False)["envios"].sum()
    vd["dia"] = vd["fecha"].dt.dayofweek.map(DIAS) + " " + vd["fecha"].dt.strftime("%d-%b")
    f = px.bar(vd, x="dia", y="envios", text_auto=",.0f", title="Demanda diaria de la red — la semana respira (martes 1.24x, domingo 0.63x)")
    f.update_traces(marker_color=[NARANJA if v == vd["envios"].max() else AZUL for v in vd["envios"]])
    figs.append(f)

    # 2. Pareto de rutas
    top = rutas.head(12).iloc[::-1]
    f = px.bar(top, x="envios", y="ruta", orientation="h", text_auto=",.0f",
               title="Pareto de rutas — 2 orígenes concentran 99.6% del volumen")
    f.update_traces(marker_color=AZUL)
    figs.append(f)

    # 3. Ocupación por ruta
    oc = rutas[rutas["envios"] >= 1000].iloc[::-1]
    f = px.bar(oc, x="ocupacion", y="ruta", orientation="h", text_auto=".0%",
               title="Ocupación por ruta (fill rate) — troncales sanas, radiales de Mérida con holgura")
    f.update_traces(marker_color=[VERDE if v >= .8 else (NARANJA if v >= .5 else ROJO) for v in oc["ocupacion"]])
    f.add_vline(x=.9, line_dash="dash", line_color="gray", annotation_text="target 90%")
    f.update_xaxes(tickformat=".0%")
    figs.append(f)

    # 4. Llegadas a destino (pregunta 1)
    ll = (m.dropna(subset=["llegada_hora"])
            .groupby(["destino", "origen", "llegada_hora", "llegada_dia"], as_index=False)
            .agg(vehiculos=("trailers", "sum")))
    ll["vehiculos"] += m.groupby(["destino", "origen", "llegada_hora", "llegada_dia"])["tortons"].sum().values
    ll["hora_num"] = ll["llegada_hora"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60)
    ll["vehiculos_dia"] = ll["vehiculos"] / dias_n
    f = px.scatter(ll, x="hora_num", y="destino", size="vehiculos_dia",
                   color=ll["llegada_dia"].map({0: "D+0", 1: "D+1", 2: "D+2"}),
                   color_discrete_map={"D+0": VERDE, "D+1": AZUL, "D+2": ROJO},
                   hover_data={"origen": True, "llegada_hora": True, "vehiculos_dia": ":.1f"},
                   title="P1 · ¿A qué hora llegan los vehículos a cada destino? (tamaño = vehículos/día)")
    f.update_xaxes(title="hora de llegada", range=[-0.5, 24.5], tickvals=list(range(0, 25, 4)),
                   ticktext=[f"{h}:00" for h in range(0, 25, 4)])
    f.update_layout(legend_title="llega")
    figs.append(f)

    # 5. Costo por paquete por ruta
    cp = rutas[rutas["envios"] >= 1000].sort_values("cpp", ascending=True)
    f = px.bar(cp, x="cpp", y="ruta", orientation="h", text_auto="$.0f",
               title=f"P3 · Costo por paquete por ruta — promedio red ${cpp_red:.2f}")
    f.update_traces(marker_color=[VERDE if v <= cpp_red else NARANJA for v in cp["cpp"]])
    f.add_vline(x=cpp_red, line_dash="dash", line_color="gray")
    figs.append(f)

    # 6. Hallazgo de la cola
    f = go.Figure(data=[
        go.Bar(name="% del volumen", x=["Micro-rutas (<1 pallet/día)"], y=[micro["envios"].sum() / total_env * 100], marker_color=AZUL, text=[f"{micro['envios'].sum()/total_env:.2%}"], textposition="outside"),
        go.Bar(name="% del costo", x=["Micro-rutas (<1 pallet/día)"], y=[costo_micro / total_costo * 100], marker_color=ROJO, text=[f"{costo_micro/total_costo:.1%}"], textposition="outside"),
    ])
    f.update_layout(title=f"Hallazgo · la cola: {micro['envios'].sum():,} paquetes generan ${costo_micro:,.0f}/sem — consolidando: ${cpp_sin_micro:.2f}/pqt (−{1-cpp_sin_micro/cpp_red:.1%})",
                    yaxis_title="%", barmode="group")
    figs.append(f)

    # 7. CV por ruta
    cv = (m.groupby(["origen", "destino"])["envios"]
            .agg(media="mean", std="std", dias="count").reset_index())
    cv["cv"] = (cv["std"] / cv["media"] * 100).fillna(0).round(1)
    cv["riesgo"] = cv["cv"].apply(
        lambda x: "Bajo (<20%)" if x < 20 else ("Medio (20-50%)" if x < 50 else "Alto (>50%)"))
    cv["ruta"] = cv["origen"] + " → " + cv["destino"]
    cv_top = cv.sort_values("cv", ascending=True).tail(20)
    f = px.bar(cv_top, x="cv", y="ruta", orientation="h", text_auto=".0f",
               color="riesgo",
               color_discrete_map={"Bajo (<20%)": VERDE, "Medio (20-50%)": NARANJA, "Alto (>50%)": ROJO},
               title="CV por ruta — variabilidad del volumen diario (forecast difficulty)")
    f.update_xaxes(title="CV (%)")
    figs.append(f)

    # 8. Estacionalidad
    DOW_ORDER = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    DOW_ES = {"Sunday":"Dom","Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
              "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb"}
    daily_vol = m.groupby("fecha")["envios"].sum().reset_index()
    daily_vol["dow"] = daily_vol["fecha"].dt.day_name()
    season_idx = daily_vol.groupby("dow")["envios"].mean().reindex(DOW_ORDER) / daily_vol["envios"].mean()
    f = px.bar(x=[DOW_ES[d] for d in DOW_ORDER], y=season_idx.values,
               text=[f"{v:.2f}x" for v in season_idx.values],
               title="Estacionalidad semanal — martes pico 1.24x, domingo valle 0.63x")
    f.update_traces(marker_color=[ROJO if v < 0.80 else (VERDE if v > 1.15 else AZUL)
                                  for v in season_idx.values], textposition="outside")
    f.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="promedio")
    f.update_yaxes(title="índice", range=[0, 1.5])
    figs.append(f)

    # 9. Volumen + flota por día (doble eje)
    from plotly.subplots import make_subplots
    DOW_NUM = {6:"Dom",0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb"}
    m["dia_lbl"] = m["fecha"].dt.dayofweek.map(DOW_NUM) + " " + m["fecha"].dt.day.astype(str)
    por_dia = m.groupby(["fecha","dia_lbl"], as_index=False).agg(
        envios=("envios","sum"), trailers=("trailers","sum"),
        tortons=("tortons","sum")).sort_values("fecha")
    por_dia["veh"] = por_dia.trailers + por_dia.tortons
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_trace(go.Bar(x=por_dia["dia_lbl"], y=por_dia["envios"], name="Envíos",
                       marker_color=AZUL, text=[f"{v/1000:.1f}K" for v in por_dia["envios"]],
                       textposition="outside"), secondary_y=False)
    f.add_trace(go.Scatter(x=por_dia["dia_lbl"], y=por_dia["veh"], name="Vehículos",
                           mode="lines+markers+text", line=dict(color=NARANJA, width=3),
                           text=por_dia["veh"], textposition="top center"), secondary_y=True)
    f.update_layout(title=(f"Día a día — la flota oscila {por_dia.veh.max()/por_dia.veh.min():.1f}x "
                           f"({por_dia.veh.min()} → {por_dia.veh.max()} vehículos)"),
                    legend=dict(orientation="h", y=1.12))
    f.update_yaxes(title_text="envíos/día", secondary_y=False, range=[0, por_dia.envios.max()*1.25])
    f.update_yaxes(title_text="vehículos/día", secondary_y=True, showgrid=False,
                   range=[0, por_dia.veh.max()*1.35])
    figs.append(f)

    # 10. Heatmap ocupación ruta × día (top 10 volumen + 4 de la cola)
    vol_r = m.groupby("ruta")["envios"].sum()
    ocu_r = m.groupby("ruta")["ocupacion"].mean()
    top_r = vol_r.nlargest(10).index.tolist() + ocu_r[vol_r >= 10].nsmallest(4).index.tolist()
    heat = (m[m["ruta"].isin(top_r)]
            .pivot_table(index="ruta", columns="dia_lbl", values="ocupacion", aggfunc="first") * 100)
    heat = heat.reindex(index=top_r, columns=por_dia["dia_lbl"].tolist())
    f = go.Figure(go.Heatmap(
        z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
        colorscale=[[0, ROJO], [0.5, NARANJA], [1, VERDE]], zmin=0, zmax=100,
        text=[[f"{v:.0f}%" if pd.notna(v) else "—" for v in row] for row in heat.values],
        texttemplate="%{text}", colorbar=dict(title="ocup %")))
    f.update_layout(title="Ocupación ruta × día — la troncal respira, la cola nunca despega",
                    yaxis=dict(autorange="reversed"), xaxis=dict(side="top"))
    figs.append(f)

    # --- ensamblar HTML ---
    kpis = [
        ("Envíos / semana", f"{total_env:,}"),
        ("Flota despachada / día", f"{m['trailers'].sum()/dias_n:.0f} trailers + {m['tortons'].sum()/dias_n:.0f} tortons"),
        ("Ocupación de red", f"{ocup_red:.0%}"),
        ("Costo total / semana", f"${total_costo/1e6:.2f}M"),
        ("Costo por paquete", f"${cpp_red:.2f}"),
        ("Ahorro identificado", f"−{1-cpp_sin_micro/cpp_red:.1%}"),
    ]
    cards = "".join(
        f'<div style="background:#fff;border-radius:12px;padding:14px 20px;box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center;min-width:150px">'
        f'<div style="font-size:12px;color:#777">{t}</div>'
        f'<div style="font-size:22px;font-weight:800;color:#1a4b8c">{v}</div></div>'
        for t, v in kpis)

    # Serializar con to_json() para que Plotly.js 3.x decodifique el formato binario correctamente
    chart_keys = [f"c{i}" for i in range(len(figs))]
    chart_data = {k: fig.to_json() for k, fig in zip(chart_keys, figs)}

    charts_html = "".join(
        f'<div style="background:#fff;border-radius:12px;padding:8px;margin-bottom:18px;box-shadow:0 2px 8px rgba(0,0,0,.08)">'
        f'<div id="{k}" style="height:450px"></div></div>'
        for k in chart_keys)

    render_calls = "\n    ".join(
        f'Plotly.react("{k}", JSON.parse(charts["{k}"]).data, JSON.parse(charts["{k}"]).layout, {{responsive:true, displayModeBar:false}});'
        for k in chart_keys)

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Caso Media Milla — Dashboard</title>
<script src="https://cdn.plot.ly/plotly-{PLOTLY_JS}.min.js"></script>
<style>body{{font-family:'Segoe UI',system-ui,sans-serif;background:#eef1f5;margin:0;padding:24px}}</style></head>
<body><div style="max-width:1100px;margin:0 auto">
<h1 style="color:#1a4b8c;margin-bottom:2px">📦 Análisis de Red — Media Milla</h1>
<p style="color:#777;margin-top:0">Semana 18–24 jun 2023 · km reales por ruta · supuestos: 60 pqts/pallet · trailer 28 tarimas ($60/km) · torton 14 ($40/km)</p>
<div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:20px">{cards}</div>
{charts_html}
</div>
<script>
const charts = {json.dumps(chart_data)};
document.addEventListener('DOMContentLoaded', function() {{
    {render_calls}
}});
</script>
</body></html>"""
    with open(archivo, "w") as fh:
        fh.write(html)
    print(f"Dashboard generado: {archivo}")
    return rutas

# === regeneración local desde el modelo canónico (km reales) ===
if __name__ == "__main__":
    modelo = pd.read_csv("modelo_km_reales.csv", parse_dates=["fecha"])
    generar_dashboard(modelo)
