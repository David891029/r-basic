"""Regenera modelo_km_reales.csv con la misma lógica del notebook (sección 3)."""
import pandas as pd
import numpy as np

PQTS_POR_PALLET = 60
CAP_TRAILER, CAP_TORTON = 28, 14
TARIFA_TRAILER, TARIFA_TORTON = 60, 40
VEL_PROMEDIO = 60

TRANSITOS_FALTANTES = {
    ("Tepotzotlan", "Playa"): 28.0,
    ("Tepotzotlan", "Chetumal"): 26.0,
    ("Mérida", "Playa"): 7.0,
    ("Mérida", "Tuxtla Gutierrez"): 14.0,
    ("Cancun", "Playa"): 2.5,        # ruta inversa: Playa del Carmen->Cancún (pestaña 2)
    ("Campeche", "Playa"): 7.0,      # manejo 5.4h (Sheet3) + paradas
    ("Villahermosa", "Playa"): 14.0, # manejo 11.8h (Sheet3) + paradas
}

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
faltantes = pd.DataFrame([{"origen":o,"destino":d,"horas_transito":h}
                          for (o,d),h in TRANSITOS_FALTANTES.items()])
tra = pd.concat([tra, faltantes], ignore_index=True).drop_duplicates(["origen","destino"], keep="first")

km_real = (tabs["Sheet3"].dropna(subset=["Kilometros"])
           .groupby(["Origen_cd","Destino_cd"])["Kilometros"].first()
           .rename("km_real").reset_index())
km_real.columns = ["origen","destino","km_real"]
km_real["destino"] = km_real["destino"].replace({"Playa del Carmen":"Playa"})

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
m["km_final"] = m["km_real"].fillna(m["horas_transito"]*VEL_PROMEDIO)
m["km"] = m["km_final"]
m["costo_real"] = (m["trailers"]*TARIFA_TRAILER + m["tortons"]*TARIFA_TORTON) * m["km_final"]
m["costo"] = m["costo_real"]
m["costo_por_pqt"] = m["costo_real"]/m["envios"]
m["hora_salida"] = m["hora_salida"]

m.to_csv("modelo_km_reales.csv", index=False)
print(f"ruta-días: {len(m)} · envíos: {m['envios'].sum():,} · pallets: {m['pallets'].sum():,}")
print(f"trailers: {m['trailers'].sum()} · tortons: {m['tortons'].sum()}")
print(f"costo total: ${m['costo_real'].sum():,.0f} · $/pqt: ${m['costo_real'].sum()/m['envios'].sum():.2f}")
print(f"ruta-días sin llegada: {m['llegada_hora'].isna().sum()}")
