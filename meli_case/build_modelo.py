"""Regenera modelo_km_reales.csv con la misma lógica del notebook (sección 3)."""
import pandas as pd
import numpy as np

PQTS_POR_PALLET = 60
CAP_TRAILER, CAP_TORTON = 28, 14
TARIFA_TRAILER, TARIFA_TORTON = 60, 40
VEL_OP = 55.6   # km/h operativa (mediana de rutas con km real y tránsito en pestaña 2)

# ── Tránsitos triangulados ────────────────────────────────────────────────────
# Grupo A: no están en pestaña 2, triangulados con rutas conocidas o ruta inversa
TRANSITOS_TRIANGULADOS = {
    ("Tepotzotlan", "Playa"):       28.0,  # Tep→Cancún 27h + ~1h
    ("Tepotzotlan", "Chetumal"):    26.0,  # vía Escárcega
    ("Mérida",      "Playa"):        7.0,  # Mérida→Cancún 6.13h + ~1h
    ("Mérida",      "Tuxtla Gutierrez"): 14.0,  # Mérida→Vhsa 9h + Vhsa→Tuxtla 5h
    ("Cancun",      "Playa"):        2.5,  # ruta inversa pestaña 2 (Playa del Carmen→Cancún)
    ("Campeche",    "Playa"):        7.0,  # Sheet3: 5.4h manejo + paradas
    ("Villahermosa","Playa"):       14.0,  # Sheet3: 11.8h manejo + paradas
}

# Grupo B: tienen km real en Sheet3, tránsito inferido = km / VEL_OP
TRANSITOS_INFERIDOS_KM = {
    ("Campeche",         "Cancun"):            round(476.6  / VEL_OP, 1),
    ("Campeche",         "Tuxtla Gutierrez"):  round(625.4  / VEL_OP, 1),
    ("Cancun",           "Chetumal"):          round(384.6  / VEL_OP, 1),
    ("Cancun",           "Ciudad del Carmen"): round(682.3  / VEL_OP, 1),
    ("Cancun",           "Tuxtla Gutierrez"):  round(1101.4 / VEL_OP, 1),
    ("Cancun",           "Villahermosa"):      round(859.6  / VEL_OP, 1),
    ("Tapachula",        "Mérida"):            round(1119.4 / VEL_OP, 1),
    ("Tuxtla Gutierrez", "Chetumal"):          round(817.3  / VEL_OP, 1),
    ("Tuxtla Gutierrez", "Mérida"):            round(802.2  / VEL_OP, 1),
    ("Villahermosa",     "Cancun"):            round(857.3  / VEL_OP, 1),
    ("Villahermosa",     "Chetumal"):          round(575.9  / VEL_OP, 1),
    ("Villahermosa",     "Mérida"):            round(559.5  / VEL_OP, 1),
}

# Grupo C: intra-ciudad sin km ni tránsito — distribución local declarada
INTRACIUDAD = {
    ("Campeche",         "Campeche"):          1.0,   # ~30 km intra-ciudad
    ("Villahermosa",     "Villahermosa"):       1.0,
}
KM_INTRACIUDAD = {
    ("Campeche",         "Campeche"):          30.0,   # intra-ciudad declarado
    ("Villahermosa",     "Villahermosa"):       30.0,   # intra-ciudad declarado
    ("Cancun",           "Cancun"):             60.0,   # consistente con modelo anterior (1h × VEL)
    ("Mérida",           "Mérida"):             40.0,   # consistente con modelo anterior (0.67h × VEL)
    ("Tuxtla Gutierrez", "Tuxtla Gutierrez"):   278.0,  # 5h tránsito × 55.6 km/h (hub regional amplio)
}

# Hora de salida de Campeche: no está en pestaña 3
# Inferida: hub regional del sureste, 30 min antes que Mérida (22:30)
SALIDAS_INFERIDAS = {
    "Campeche": "22:00",
}

# ── Carga del Excel ───────────────────────────────────────────────────────────
tabs = pd.read_excel("caso_real.xlsx", sheet_name=None)
vol = tabs["1.- Volumen"].rename(columns={"Origen_cd":"origen","Destino_cd":"destino",
                                          "Fecha":"fecha","Proceso":"proceso","Envios":"envios"})
tra = tabs["2.- Tiempos Tránsito"].copy(); tra.columns = ["origen","destino","horas_transito"]
sal = tabs["3.- Horas de Salida"].copy();  sal.columns = ["origen","destino","hora_salida"]

for df in (vol, tra, sal):
    for c in ("origen","destino"):
        df[c] = df[c].astype(str).str.strip().replace({"Playa del Carmen":"Playa"})
vol["fecha"] = pd.to_datetime(vol["fecha"])
vol["envios"] = vol["envios"].astype(int)
tra["horas_transito"] = tra["horas_transito"].astype(float)
sal["hora_salida"] = sal["hora_salida"].apply(
    lambda v: v.strftime("%H:%M") if hasattr(v,"strftime") else str(v).strip()[:5])

# ── Agregar tránsitos inferidos ───────────────────────────────────────────────
todos_faltantes = {**TRANSITOS_TRIANGULADOS, **TRANSITOS_INFERIDOS_KM, **INTRACIUDAD}
faltantes_df = pd.DataFrame([{"origen":o,"destino":d,"horas_transito":h}
                              for (o,d),h in todos_faltantes.items()])
tra = pd.concat([tra, faltantes_df], ignore_index=True).drop_duplicates(["origen","destino"], keep="first")

# ── Agregar salida de Campeche a todas sus rutas ──────────────────────────────
origenes_sin_salida = vol[~vol["origen"].isin(sal["origen"].unique())]["origen"].unique()
for origen in origenes_sin_salida:
    if origen in SALIDAS_INFERIDAS:
        destinos = vol[vol["origen"]==origen]["destino"].unique()
        for dest in destinos:
            sal = pd.concat([sal, pd.DataFrame([{"origen":origen,"destino":dest,
                                                  "hora_salida":SALIDAS_INFERIDAS[origen]}])],
                            ignore_index=True)

# ── km reales de Sheet3 ───────────────────────────────────────────────────────
km_real = (tabs["Sheet3"].dropna(subset=["Kilometros"])
           .groupby(["Origen_cd","Destino_cd"])["Kilometros"].first()
           .rename("km_real").reset_index())
km_real.columns = ["origen","destino","km_real"]
km_real["destino"] = km_real["destino"].replace({"Playa del Carmen":"Playa"})

# Agregar km intra-ciudad declarados
km_intra_df = pd.DataFrame([{"origen":o,"destino":d,"km_real":k}
                             for (o,d),k in KM_INTRACIUDAD.items()])
km_real = pd.concat([km_real, km_intra_df], ignore_index=True).drop_duplicates(["origen","destino"], keep="first")

# ── Modelo ────────────────────────────────────────────────────────────────────
def flota(p):
    n_t, rem = divmod(int(p), CAP_TRAILER)
    n_tor = 0
    if rem > CAP_TORTON: n_t += 1
    elif rem > 0: n_tor = 1
    return n_t, n_tor

m = vol.groupby(["fecha","origen","destino"], as_index=False)["envios"].sum()
m["pallets"] = np.ceil(m["envios"]/PQTS_POR_PALLET).astype(int)
m[["trailers","tortons"]] = m["pallets"].apply(lambda p: pd.Series(flota(p)))
m["capacidad"] = m["trailers"]*CAP_TRAILER + m["tortons"]*CAP_TORTON
m["ocupacion"] = m["pallets"]/m["capacidad"]
m = m.merge(tra, on=["origen","destino"], how="left").merge(sal, on=["origen","destino"], how="left")
lleg = (m["fecha"] + pd.to_timedelta(m["hora_salida"]+":00", errors="coerce")
        + pd.to_timedelta(m["horas_transito"], unit="h"))
m["llegada_hora"] = lleg.dt.strftime("%H:%M")
m["llegada_dia"] = (lleg.dt.normalize() - m["fecha"]).dt.days.astype("Int64")
m = m.merge(km_real, on=["origen","destino"], how="left")
m["km_final"] = m["km_real"]   # todos los km ahora son reales o declarados
m["km"] = m["km_final"]
m["costo_real"] = (m["trailers"]*TARIFA_TRAILER + m["tortons"]*TARIFA_TORTON) * m["km_final"]
m["costo"] = m["costo_real"]
m["costo_por_pqt"] = (m["costo_real"]/m["envios"]).where(m["envios"]>0)

m.to_csv("modelo_km_reales.csv", index=False)

sin_lleg = m['llegada_hora'].isna().sum()
sin_km   = m['km_final'].isna().sum()
print(f"ruta-días: {len(m)} · envíos: {m['envios'].sum():,} · pallets: {m['pallets'].sum():,}")
print(f"trailers: {m['trailers'].sum()} · tortons: {m['tortons'].sum()}")
print(f"costo total: ${m['costo_real'].sum():,.0f} · $/pqt: ${m['costo_real'].sum()/m['envios'].sum():.2f}")
print(f"sin llegada: {sin_lleg} ruta-días · sin km: {sin_km} ruta-días")
if sin_lleg == 0 and sin_km == 0:
    print("✅ Modelo completo — cero gaps")
else:
    print("⚠️  Gaps restantes:")
    print(m[m['llegada_hora'].isna() | m['km_final'].isna()][['origen','destino','horas_transito','hora_salida','km_final']].drop_duplicates(['origen','destino']))
