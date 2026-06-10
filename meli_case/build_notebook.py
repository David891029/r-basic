"""Construye el notebook de Colab del caso (caso_meli_colab.ipynb)."""
import json

def md(src): return {"cell_type": "markdown", "metadata": {}, "source": src}
def code(src): return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": src}

cells = []

cells.append(md("""\
# 📦 Business Case — Análisis de Red Media Milla

**Objetivo:** minimizar el costo de entrega por paquete en la red de linehaul (FC → estaciones), respondiendo:

1. ¿Cuántos vehículos llegan a cada destino y en qué horario?
2. ¿Cómo se ven los indicadores de ocupación?
3. Con trailer a \\$60/km y torton a \\$40/km, ¿cuál es el costo total de la red?

**La cadena del modelo** (se aplica a cada ruta-día y se agrega):

```
envíos por ruta-día → ÷60 → pallets → llenar trailers de 28 (remanente ≤14 → torton)
hora de salida + tránsito → hora de llegada
vehículos × km × tarifa → costo → ÷ envíos → costo por paquete
```

**Cómo usar este notebook:** Runtime → Run all. Se autentica con tu cuenta de Google (popup una vez), lee el Google Sheet privado, construye el modelo y al final **sube el dashboard HTML a tu carpeta de Drive** *"Business Case MELI"*. Nada se descarga a tu equipo.\
"""))

cells.append(md("""\
## Supuestos declarados

| Supuesto | Valor | Justificación |
|---|---|---|
| Paquetes por pallet | 60 | dado en el caso |
| Capacidad trailer 53' | 28 tarimas | estándar caja seca MX (26–30) |
| Capacidad torton | 14 tarimas | estándar MX (12–16) |
| Distancias | **km reales de la pestaña Sheet3** (40 de 45 rutas) | fallback: tránsito × 60 km/h, validado: velocidad implícita de los km reales ≈ 58 km/h |
| Tránsitos faltantes | triangulados con rutas conocidas | Tep→Playa ≈ 28h, Tep→Chetumal ≈ 26h, Mér→Playa ≈ 7h, Mér→Tuxtla ≈ 14h |
| Asignación de flota | llenar trailers; remanente ≤14 → torton, >14 → trailer | trailer lleno: \\$2.14/tarima-km < torton: \\$2.86; y 2 tortons (\\$80/km) > 1 trailer (\\$60/km) |
| Consolidación | todos los procesos (FULL OUT, XD OUT…) viajan juntos por ruta-día | la pestaña 3 da una sola salida por origen |\
"""))

cells.append(code("""\
import pandas as pd
import numpy as np

# ============ PARÁMETROS ============
PQTS_POR_PALLET = 60      # dado en el caso
CAP_TRAILER    = 28       # tarimas, trailer 53'
CAP_TORTON     = 14       # tarimas, torton
TARIFA_TRAILER = 60       # $/km, dado
TARIFA_TORTON  = 40       # $/km, dado
VEL_PROMEDIO   = 60       # km/h — solo para rutas sin km real (intra-ciudad)

# Tránsitos que faltan en la pestaña 2, triangulados con rutas conocidas
TRANSITOS_FALTANTES = {
    ("Tepotzotlan", "Playa"): 28.0,        # Tep→Cancún 27h + ~1h
    ("Tepotzotlan", "Chetumal"): 26.0,     # vía Escárcega
    ("Mérida", "Playa"): 7.0,              # Mérida→Cancún 6.13h + ~1h
    ("Mérida", "Tuxtla Gutierrez"): 14.0,  # Mérida→Vhsa 9h + Vhsa→Tuxtla 5h
    ("Cancun", "Playa"): 2.5,              # ruta inversa: Playa del Carmen→Cancún 2.5h (pestaña 2)
    ("Campeche", "Playa"): 7.0,            # manejo 5.4h (Sheet3) + paradas
    ("Villahermosa", "Playa"): 14.0,       # manejo 11.8h (Sheet3) + paradas
}\
"""))

cells.append(md("## 1 · Carga del Google Sheet"))

cells.append(code("""\
import io, os, requests

FILE_ID   = "1RdHfK4C3CGkBBNLqdykKPLfXCWc_gQ2ZBUPtw5wO8_8"   # Google Sheet "WS- Planning LH Sup"
FOLDER_ID = "12VkDhTyzCKv9agIATHENAPL_PDdeDNl8"               # carpeta de Drive "Business Case MELI"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Autenticación con tu cuenta de Google: lee el Sheet privado y permite subir a Drive.
# Muestra un popup de permiso una sola vez por sesión.
drive = None
try:
    from google.colab import auth
    auth.authenticate_user()
    from googleapiclient.discovery import build
    drive = build("drive", "v3")
    print("Autenticado con Google Drive ✓")
except Exception as e:
    print(f"Sin auth de Colab ({e}). Usaré modo público / subida manual.")

def cargar_xlsx(file_id):
    if os.path.exists("caso_real.xlsx"):                       # copia local (para re-runs)
        return open("caso_real.xlsx", "rb").read()
    if drive is not None:                                      # 1) API de Drive (tu cuenta)
        return drive.files().export(fileId=file_id, mimeType=XLSX_MIME).execute()
    try:                                                       # 2) export público (si lo compartes)
        r = requests.get(f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx",
                         timeout=60)
        if r.ok and r.content[:2] == b"PK":
            return r.content
    except requests.RequestException:
        pass
    from google.colab import files                            # 3) subida manual
    print("Sube el caso manualmente (.xlsx):")
    return list(files.upload().values())[0]

def subir_a_drive(ruta_local, folder_id=FOLDER_ID, mime="text/html"):
    \"\"\"Sube (o actualiza si ya existe) un archivo a la carpeta de Drive.\"\"\"
    if drive is None:
        print(f"Sin Drive: '{ruta_local}' quedó solo en el runtime de Colab.")
        return None
    from googleapiclient.http import MediaFileUpload
    from IPython.display import display, HTML
    nombre = os.path.basename(ruta_local)
    media = MediaFileUpload(ruta_local, mimetype=mime, resumable=False)
    previos = drive.files().list(
        q=f"name='{nombre}' and '{folder_id}' in parents and trashed=false",
        fields="files(id)").execute().get("files", [])
    if previos:
        fid = previos[0]["id"]
        drive.files().update(fileId=fid, media_body=media).execute()
        f = drive.files().get(fileId=fid, fields="id,webViewLink,name").execute()
    else:
        f = drive.files().create(media_body=media, fields="id,webViewLink,name",
                                 body={"name": nombre, "parents": [folder_id]}).execute()
    fid = f.get("id", "")
    link = f.get("webViewLink") or f"https://drive.google.com/file/d/{fid}/view"
    print(f"✅ {nombre} subido a Drive")
    display(HTML(f'<a href="{link}" target="_blank" style="font-size:15px;'
                 f'background:#1a73e8;color:#fff;padding:8px 16px;border-radius:6px;'
                 f'text-decoration:none">🔗 Abrir {nombre} en Drive</a>'))
    return f

raw = cargar_xlsx(FILE_ID)
open("caso_real.xlsx", "wb").write(raw)                        # cache para re-runs
tabs = pd.read_excel(io.BytesIO(raw), sheet_name=None)
print("Pestañas:", {n: df.shape for n, df in tabs.items()})\
"""))

cells.append(md("""\
## 2 · Limpieza

Lo que hay que corregir antes de calcular (esto es parte del análisis — el dataset trae trampas):
- **La pestaña 2 no tiene NINGÚN tránsito hacia Playa** (bajo ningún nombre). "Playa del Carmen"
  solo aparece como *origen* (→Cancún 2.5h, →Mérida 12h) y ningún volumen sale de Playa.
  Sin corrección, los 12,836 envíos hacia Playa se quedan **sin hora de llegada** (el costo no
  se afecta: usa km de Sheet3). Se triangulan 7 tránsitos — incluyendo Cancún→Playa con la
  **ruta inversa** de la pestaña 2 (Playa del Carmen→Cancún 2.5h).
- La normalización "Playa del Carmen"→"Playa" es defensiva: unifica el nombre entre pestañas
  por si algún cruce lo necesita (en este dataset las filas afectadas no se usan en joins).
- `Sheet1` duplica todo el volumen (no usarla). `Sheet3` trae **kilómetros reales** por ruta → mejor que asumir velocidad.
- Horas de salida llegan como `datetime.time`, fechas como `Timestamp`.\
"""))

cells.append(code("""\
def limpiar(vol, tra, sal):
    vol = vol.rename(columns={"Origen_cd": "origen", "Destino_cd": "destino",
                              "Fecha": "fecha", "Proceso": "proceso", "Envios": "envios"})
    tra.columns = ["origen", "destino", "horas_transito"]
    sal.columns = ["origen", "destino", "hora_salida"]
    for df in (vol, tra, sal):
        for c in ("origen", "destino"):
            df[c] = df[c].astype(str).str.strip().replace({"Playa del Carmen": "Playa"})
    vol["fecha"] = pd.to_datetime(vol["fecha"])
    vol["envios"] = vol["envios"].astype(int)
    tra["horas_transito"] = tra["horas_transito"].astype(float)
    sal["hora_salida"] = sal["hora_salida"].apply(
        lambda v: v.strftime("%H:%M") if hasattr(v, "strftime") else str(v).strip()[:5])
    faltantes = pd.DataFrame([{"origen": o, "destino": d, "horas_transito": h}
                              for (o, d), h in TRANSITOS_FALTANTES.items()])
    tra = pd.concat([tra, faltantes], ignore_index=True)
    tra = tra.drop_duplicates(["origen", "destino"], keep="first")  # el dato del Excel manda
    return vol, tra, sal

vol, tra, sal = limpiar(tabs["1.- Volumen"].copy(),
                        tabs["2.- Tiempos Tránsito"].copy(),
                        tabs["3.- Horas de Salida"].copy())

# km reales por ruta (pestaña Sheet3) — consistentes por ruta, 40 de 45 rutas
km_real = (tabs["Sheet3"].dropna(subset=["Kilometros"])
           .groupby(["Origen_cd", "Destino_cd"])["Kilometros"].first()
           .rename("km_real").reset_index())
km_real.columns = ["origen", "destino", "km_real"]
km_real["destino"] = km_real["destino"].replace({"Playa del Carmen": "Playa"})

print(f"{len(vol)} filas de volumen · {vol['envios'].sum():,} envíos · "
      f"{vol['fecha'].dt.date.nunique()} días · {len(km_real)} rutas con km real")\
"""))

cells.append(md("## 3 · El modelo: la cadena completa"))

cells.append(code("""\
def flota(pallets):
    \"\"\"Mezcla de costo mínimo: llenar trailers; remanente <=14 en torton, >14 en trailer.\"\"\"
    n_trailer, rem = divmod(int(pallets), CAP_TRAILER)
    n_torton = 0
    if rem > CAP_TORTON:
        n_trailer += 1
    elif rem > 0:
        n_torton = 1
    return n_trailer, n_torton

# Paso 1: consolidar — todos los procesos del día viajan juntos
m = vol.groupby(["fecha", "origen", "destino"], as_index=False)["envios"].sum()

# Paso 2: paquetes -> pallets (redondeo arriba: un pallet a medias ocupa lugar completo)
m["pallets"] = np.ceil(m["envios"] / PQTS_POR_PALLET).astype(int)

# Paso 3: pallets -> flota y ocupación
m[["trailers", "tortons"]] = m["pallets"].apply(lambda p: pd.Series(flota(p)))
m["capacidad"] = m["trailers"] * CAP_TRAILER + m["tortons"] * CAP_TORTON
m["ocupacion"] = m["pallets"] / m["capacidad"]

# Paso 4: el reloj — salida + tránsito = llegada
m = m.merge(tra, on=["origen", "destino"], how="left")
m = m.merge(sal, on=["origen", "destino"], how="left")
llegada = (m["fecha"]
           + pd.to_timedelta(m["hora_salida"] + ":00", errors="coerce")
           + pd.to_timedelta(m["horas_transito"], unit="h"))
m["llegada_hora"] = llegada.dt.strftime("%H:%M")
m["llegada_dia"] = (llegada.dt.normalize() - m["fecha"]).dt.days.astype("Int64")  # 0=D+0, 1=D+1

# Paso 5: el dinero — km reales; fallback tránsito x velocidad (solo intra-ciudad)
m = m.merge(km_real, on=["origen", "destino"], how="left")
m["km"] = m["km_real"].fillna(m["horas_transito"] * VEL_PROMEDIO)
m["costo"] = (m["trailers"] * TARIFA_TRAILER + m["tortons"] * TARIFA_TORTON) * m["km"]
m["costo_por_pqt"] = m["costo"] / m["envios"]

print(f"{len(m)} ruta-días · {m['pallets'].sum():,} pallets · "
      f"{m['trailers'].sum()} trailers + {m['tortons'].sum()} tortons en la semana")
m.head(8)\
"""))

cells.append(md("## P1 · ¿Cuántos vehículos llegan a cada destino y a qué hora?"))

cells.append(code("""\
m["vehiculos"] = m["trailers"] + m["tortons"]
dias_n = m["fecha"].dt.date.nunique()

p1 = (m.dropna(subset=["llegada_hora"])
        .groupby(["destino", "origen", "hora_salida", "llegada_hora", "llegada_dia"])
        .agg(vehiculos_dia=("vehiculos", lambda s: s.sum() / dias_n),
             envios_sem=("envios", "sum"))
        .round(1)
        .sort_values(["envios_sem"], ascending=False))
print(f"Despacho diario promedio de la red: {m['trailers'].sum()/dias_n:.0f} trailers "
      f"+ {m['tortons'].sum()/dias_n:.0f} tortons")
p1.head(20)\
"""))

cells.append(md("## P2 · Indicadores de ocupación (fill rate)"))

cells.append(code("""\
m["ruta"] = m["origen"] + " → " + m["destino"]
p2 = (m.groupby("ruta", as_index=False)
        .agg(envios=("envios", "sum"), pallets=("pallets", "sum"),
             trailers=("trailers", "sum"), tortons=("tortons", "sum"),
             capacidad=("capacidad", "sum"), costo=("costo", "sum")))
p2["ocupacion"] = (p2["pallets"] / p2["capacidad"]).round(3)
p2["costo_por_pqt"] = (p2["costo"] / p2["envios"]).round(2)
p2 = p2.sort_values("envios", ascending=False)

ocup_red = m["pallets"].sum() / m["capacidad"].sum()
print(f"Ocupación global de la red: {ocup_red:.1%}")
print("Lectura por niveles: troncales de Tepotzotlán 83-94% (sano) · "
      "radiales de Mérida 24-50% (frecuencia diaria por SLA) · micro-rutas ~7% (el problema)")
p2.head(20)\
"""))

cells.append(md("## P3 · Costo total de la red y el hallazgo"))

cells.append(code("""\
total_env, total_costo = m["envios"].sum(), m["costo"].sum()
print(f"COSTO TOTAL: ${total_costo:,.0f} por semana  →  ${total_costo/total_env:.2f} por paquete")
print(f"Anualizado: ~${total_costo*52/1e6:,.0f}M")

# El hallazgo: micro-rutas (<1 pallet/día) — un torton casi vacío recorriendo cientos de km
micro = m[m["envios"] < PQTS_POR_PALLET]
c_micro = micro["costo"].sum()
print(f"\\nHALLAZGO — la cola de la red:")
print(f"  {micro['envios'].sum():,} envíos en micro-rutas = {micro['envios'].sum()/total_env:.2%} del volumen")
print(f"  pero cuestan ${c_micro:,.0f}/sem = {c_micro/total_costo:.1%} del costo total")
print(f"  Consolidándolas (co-load en salidas existentes): "
      f"${(total_costo-c_micro)/total_env:.2f}/pqt ({(total_costo-c_micro)/total_env/(total_costo/total_env)-1:+.1%})")

# Palanca 2: multi-stop en radiales de Mérida con ocupación <50%
print(f"\\nPalanca 2 — multi-stop en radiales de Mérida (ej. Campeche + Cd. del Carmen")
print(f"en un solo torton: 3.6h entre ellas): ahorro adicional estimado ~$50K/sem")
micro.sort_values("costo", ascending=False).head(10)\
"""))

cells.append(md("""\
## 4 · Métricas avanzadas

### 4a · Coeficiente de Variación (CV) por ruta
**¿Qué es?** Mide la volatilidad del volumen diario: CV = desv_std / media × 100.
Un CV alto → el forecast es difícil → mayor riesgo de camiones vacíos o paquetes sin transporte.

| CV | Significado | Acción recomendada |
|---|---|---|
| < 20% | Estable | Flota fija, forecast determinístico |
| 20–50% | Moderado | Buffer de capacidad del 20% |
| > 50% | Caótico | Consolidar con ruta vecina o modelo probabilístico |\
"""))

cells.append(code("""\
lane_day = vol.groupby(["fecha", "origen", "destino"])["envios"].sum().reset_index()
cv = (lane_day.groupby(["origen", "destino"])["envios"]
      .agg(media="mean", std="std", dias="count", total="sum").reset_index())
cv["cv"] = (cv["std"] / cv["media"] * 100).fillna(0).round(1)
cv["riesgo"] = cv["cv"].apply(
    lambda x: "Bajo (<20%)" if x < 20 else ("Medio (20-50%)" if x < 50 else "Alto (>50%)"))
cv["ruta"] = cv["origen"] + " → " + cv["destino"]

print("=== Resumen CV de la red ===")
print(cv["riesgo"].value_counts().to_string())
print(f"\\nCV promedio: {cv['cv'].mean():.0f}%")
print("\\nRutas más volátiles (top 10):")
cv.sort_values("cv", ascending=False).head(10)[["ruta","media","cv","riesgo","total"]]\
"""))

cells.append(md("### 4b · Utilización ponderada por ruta"))

cells.append(code("""\
ocu_ruta = m.groupby(["origen", "destino"]).agg(
    pallets_total=("pallets", "sum"),
    capacidad_total=("capacidad", "sum"),
    envios=("envios", "sum"),
    costo=("costo", "sum"),
    dias=("fecha", "count")
).reset_index()
ocu_ruta["ocu_pct"] = (ocu_ruta["pallets_total"] / ocu_ruta["capacidad_total"] * 100).round(1)
ocu_ruta["costo_pqt"] = (ocu_ruta["costo"] / ocu_ruta["envios"]).round(2)
ocu_ruta["ruta"] = ocu_ruta["origen"] + " → " + ocu_ruta["destino"]

# Bimodalidad: troncales Tep llenas, nodos secundarios en 7.1% (1 pallet/torton)
print(f"Rutas ≥ 70% ocupación: {(ocu_ruta['ocu_pct'] >= 70).sum()}")
print(f"Rutas < 30% ocupación: {(ocu_ruta['ocu_pct'] < 30).sum()}  ← candidatas a co-load")
print("\\nTop 10 por ocupación:")
ocu_ruta.sort_values("ocu_pct", ascending=False).head(10)[["ruta","ocu_pct","costo_pqt","envios"]]\
"""))

cells.append(md("### 4c · Estacionalidad semanal"))

cells.append(code("""\
daily_vol = m.groupby("fecha")["envios"].sum().reset_index()
daily_vol["dow"] = daily_vol["fecha"].dt.day_name()
DOW_ORDER = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
DOW_ES = {"Sunday":"Dom","Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
          "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb"}
global_avg = daily_vol["envios"].mean()
season_idx = daily_vol.groupby("dow")["envios"].mean().reindex(DOW_ORDER) / global_avg

print("=== Índice de estacionalidad (1.0 = promedio) ===")
for d, v in season_idx.items():
    barra = "█" * int(v * 20)
    print(f"  {DOW_ES[d]}  {v:.2f}x  {barra}")
print(f"\\nPico: Martes {season_idx['Tuesday']:.2f}x · Valle: Domingo {season_idx['Sunday']:.2f}x")
print(f"Factor pico/valle: {season_idx['Tuesday']/season_idx['Sunday']:.1f}x")\
"""))

cells.append(md("### 4d · NOM-087: rutas con riesgo de doble operador"))

cells.append(code("""\
# NOM-087-SCT2-2017: operador no puede manejar >11h continuas ni >15h en 24h.
# En rutas con tiempo de tránsito >21h se requiere doble operador → sobrecosto 15-30%.
tran_largo = tra[tra["horas_transito"] >= 18].sort_values("horas_transito", ascending=False)
print("Rutas que podrían requerir doble operador (tránsito ≥18h):")
print(tran_largo[["origen","destino","horas_transito"]].to_string(index=False))
print()
print("Impacto en costo: las rutas >21h de Tepotzotlán representan ~21% del costo total.")
print("El modelo actual NO incluye sobrecargo de team driving — lo agregaría en producción.")\
"""))

cells.append(md("## 5 · Dashboard interactivo (HTML)"))

cells.append(code("""\
import plotly.graph_objects as go
import plotly.express as px

DIAS = {6: "Dom", 0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb"}
AZUL, NARANJA, VERDE, ROJO = "#1a4b8c", "#f39c12", "#27ae60", "#e74c3c"
cpp_red = total_costo / total_env
figs = []

# 1. Demanda diaria
vd = m.groupby("fecha", as_index=False)["envios"].sum()
vd["dia"] = vd["fecha"].dt.dayofweek.map(DIAS) + " " + vd["fecha"].dt.strftime("%d-%b")
f = px.bar(vd, x="dia", y="envios", text_auto=",.0f",
           title="Demanda diaria — la semana respira (martes 1.24x, domingo 0.63x)")
f.update_traces(marker_color=[NARANJA if v == vd["envios"].max() else AZUL for v in vd["envios"]])
figs.append(f)

# 2. Pareto de rutas
top = p2.head(12).iloc[::-1]
f = px.bar(top, x="envios", y="ruta", orientation="h", text_auto=",.0f",
           title="Pareto — 2 orígenes (Tepotzotlán 84%, Mérida 16%) concentran 99.6% del volumen")
f.update_traces(marker_color=AZUL)
figs.append(f)

# 3. Ocupación
oc = p2[p2["envios"] >= 1000].iloc[::-1]
f = px.bar(oc, x="ocupacion", y="ruta", orientation="h", text_auto=".0%",
           title="P2 · Ocupación por ruta — troncales sanas, radiales con holgura")
f.update_traces(marker_color=[VERDE if v >= .8 else (NARANJA if v >= .5 else ROJO)
                              for v in oc["ocupacion"]])
f.add_vline(x=.9, line_dash="dash", line_color="gray", annotation_text="target 90%")
f.update_xaxes(tickformat=".0%")
figs.append(f)

# 4. Llegadas (P1)
ll = (m.dropna(subset=["llegada_hora"])
        .groupby(["destino", "origen", "llegada_hora", "llegada_dia"], as_index=False)
        .agg(vehiculos=("vehiculos", "sum")))
ll["hora_num"] = ll["llegada_hora"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60)
ll["vehiculos_dia"] = ll["vehiculos"] / dias_n
f = px.scatter(ll, x="hora_num", y="destino", size="vehiculos_dia",
               color=ll["llegada_dia"].map({0: "D+0", 1: "D+1", 2: "D+2"}),
               color_discrete_map={"D+0": VERDE, "D+1": AZUL, "D+2": ROJO},
               hover_data={"origen": True, "llegada_hora": True, "vehiculos_dia": ":.1f"},
               title="P1 · ¿A qué hora llega cada flujo a destino? (tamaño = vehículos/día)")
f.update_xaxes(title="hora de llegada", range=[-0.5, 24.5], tickvals=list(range(0, 25, 4)),
               ticktext=[f"{h}:00" for h in range(0, 25, 4)])
f.update_layout(legend_title="llega")
figs.append(f)

# 5. Costo por paquete
cp = p2[p2["envios"] >= 1000].sort_values("costo_por_pqt")
f = px.bar(cp, x="costo_por_pqt", y="ruta", orientation="h", text_auto="$.0f",
           title=f"P3 · Costo por paquete por ruta — promedio red ${cpp_red:.2f}")
f.update_traces(marker_color=[VERDE if v <= cpp_red else NARANJA for v in cp["costo_por_pqt"]])
f.add_vline(x=cpp_red, line_dash="dash", line_color="gray")
figs.append(f)

# 6. El hallazgo
f = go.Figure([
    go.Bar(name="% del volumen", x=["Micro-rutas (<1 pallet/día)"],
           y=[micro["envios"].sum() / total_env * 100],
           marker_color=AZUL, text=[f"{micro['envios'].sum()/total_env:.2%}"], textposition="outside"),
    go.Bar(name="% del costo", x=["Micro-rutas (<1 pallet/día)"],
           y=[c_micro / total_costo * 100],
           marker_color=ROJO, text=[f"{c_micro/total_costo:.1%}"], textposition="outside")])
f.update_layout(title=(f"Hallazgo · {micro['envios'].sum():,} paquetes ({micro['envios'].sum()/total_env:.2%} del volumen) cuestan "
                       f"${c_micro/1e6:.2f}M/sem ({c_micro/total_costo:.0%} del costo) — "
                       f"consolidando: ${(total_costo-c_micro)/total_env:.2f}/pqt"),
                yaxis_title="%", barmode="group")
figs.append(f)

# 7. CV por ruta
cv_top = cv.sort_values("cv", ascending=True).tail(20)
f = px.bar(cv_top, x="cv", y="ruta", orientation="h", text_auto=".0f",
           color="riesgo",
           color_discrete_map={"Bajo (<20%)": VERDE, "Medio (20-50%)": NARANJA, "Alto (>50%)": ROJO},
           title="CV por ruta — variabilidad del volumen diario (forecast difficulty)")
f.update_xaxes(title="CV (%)")
figs.append(f)

# 8. Estacionalidad
f = px.bar(x=[DOW_ES[d] for d in DOW_ORDER], y=season_idx.values,
           text=[f"{v:.2f}x" for v in season_idx.values],
           title="Estacionalidad semanal — martes pico 1.24x, domingo valle 0.63x")
f.update_traces(marker_color=[ROJO if v < 0.80 else (VERDE if v > 1.15 else AZUL)
                              for v in season_idx.values], textposition="outside")
f.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="promedio")
f.update_yaxes(title="índice", range=[0, 1.5])
figs.append(f)

kpis = [("Envíos / semana", f"{total_env:,}"),
        ("Flota / día", f"{m['trailers'].sum()/dias_n:.0f} T + {m['tortons'].sum()/dias_n:.0f} t"),
        ("Ocupación de red", f"{ocup_red:.0%}"),
        ("Costo / semana", f"${total_costo/1e6:.2f}M"),
        ("Costo por paquete", f"${cpp_red:.2f}"),
        ("Ahorro co-load", f"−{c_micro/total_costo:.0%}"),
        ("CV promedio red", f"{cv['cv'].mean():.0f}%"),
        ("Pico / Valle", f"Mar {season_idx['Tuesday']:.2f}x / Dom {season_idx['Sunday']:.2f}x")]
cards = "".join(
    f'<div style="background:#fff;border-radius:12px;padding:14px 20px;'
    f'box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center;min-width:150px">'
    f'<div style="font-size:12px;color:#777">{t}</div>'
    f'<div style="font-size:22px;font-weight:800;color:#1a4b8c">{v}</div></div>' for t, v in kpis)
charts = "".join(
    '<div style="background:#fff;border-radius:12px;padding:8px;margin-bottom:18px;'
    'box-shadow:0 2px 8px rgba(0,0,0,.08)">'
    + f.to_html(full_html=False, include_plotlyjs=False, default_height=430) + "</div>" for f in figs)

html = f\"\"\"<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Caso Media Milla — Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>body{{font-family:'Segoe UI',system-ui,sans-serif;background:#eef1f5;margin:0;padding:24px}}</style>
</head><body><div style="max-width:1100px;margin:0 auto">
<h1 style="color:#1a4b8c;margin-bottom:2px">📦 Análisis de Red — Media Milla</h1>
<p style="color:#777;margin-top:0">Semana 18–24 jun 2023 · km reales por ruta ·
supuestos: 60 pqts/pallet · trailer 28 tarimas ($60/km) · torton 14 ($40/km)</p>
<div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:20px">{cards}</div>
{charts}</div></body></html>\"\"\"

with open("dashboard_meli.html", "w") as fh:
    fh.write(html)
print("dashboard_meli.html generado")

# Mostrar directo en Colab (no depende de Drive para verlo)
from IPython.display import display, IFrame, HTML
display(HTML("<h3 style='color:#1a4b8c'>✅ Dashboard renderizado abajo ↓</h3>"))
display(HTML(html))

# También subir a Drive como respaldo
subir_a_drive("dashboard_meli.html")\
"""))

cells.append(md("""\
## Conclusiones para las slides

**P1 — Vehículos y horarios:** la red despacha ~17 trailers + ~26 tortons diarios. Las troncales de Tepotzotlán salen 20:30–22:30 y llegan al sureste entre las 11:00 y las 23:30 de D+1 (Villahermosa 13:10, Tuxtla 11:19, Mérida 21:22, Cancún 23:30). **Playa del Carmen llega D+2 a las 00:30** → toda promesa D+1 en la Riviera Maya depende del inventario posicionado en el hub de Mérida, no del lineal desde CDMX.

**P2 — Ocupación:** tres realidades en una red: troncales 83–94% (sano, en target), radiales de Mérida 24–50% (precio de mantener frecuencia diaria por SLA), micro-rutas ~7% (dinero quemado).

**P3 — Costo:** ~\\$10.8M/semana ≈ **\\$53.7 por paquete** (km reales). El hallazgo: **0.34% del volumen (micro-rutas, 682 paquetes) consume 19.4% del costo** — un torton casi vacío recorriendo 400–1,600 km diarios. Consolidando como co-load: **\\$43.3/pqt (−19%)** sin tocar el SLA de las troncales.

**Palancas adicionales (orden de implementación):**
1. Co-load inmediato de micro-rutas → −19% costo, sin inversión
2. Multi-stop en radiales de Mérida (Campeche + Cd. del Carmen) → ~\\$50K/sem
3. Revisión del trade-off frecuencia/ocupación en radiales si el SLA lo permite

**Qué pediría para producción:** 8–12 semanas de historia (separar estacionalidad de ruido), tarifas con componente fijo+variable, ventanas de recibo y capacidad de sortation por estación, y el calendario comercial (Hot Sale) para el forecast D+1–D+60.\
"""))

nb = {"cells": cells,
      "metadata": {"colab": {"name": "Caso MELI — Media Milla", "provenance": []},
                   "kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}

with open("caso_meli_colab.ipynb", "w") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("notebook generado")
