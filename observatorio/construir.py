"""Construye los datos del observatorio web (docs/datos.json) a partir de las salidas del notebook.
Uso: python observatorio/construir.py   (después de ejecutar cafe_papa_narino.ipynb)"""
import json, shutil
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
S, DOCS = BASE / "salidas", BASE / "docs"
DOCS.mkdir(exist_ok=True)
lim = lambda v: None if pd.isna(v) else round(float(v), 3)

panel = pd.read_csv(S / "datos" / "panel_municipal.csv", dtype={"cod_mpio": str})
precios = pd.read_csv(S / "datos" / "precios_mensuales.csv")
dep = pd.read_csv(S / "datos" / "serie_departamental.csv")
VARS = ["area_cos", "prod", "rend", "p_real", "ib_real"]
datos = {
    "meta": {"generado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
             "repositorio": "https://github.com/santacruzdavid1201-web/cafe-papa-narino"},
    "municipios": panel[["cod_mpio", "municipio"]].drop_duplicates("cod_mpio").sort_values("municipio").to_dict("records"),
    "panel": {prod: {m: {"anio": g.anio.tolist(), **{v: [lim(x) for x in g[v]] for v in VARS}} for m, g in gp.groupby("cod_mpio")}
              for prod, gp in panel.groupby("producto")},
    "departamental": {prod: {"anio": g.anio.tolist(), **{v: [lim(x) for x in g[v]] for v in ["area_cos", "prod", "rend", "p_real", "ib_real"]}}
                      for prod, g in dep.groupby("producto")},
    "precios": {s: {"fecha": g.fecha.tolist(), "precio": [lim(x) for x in g.precio]} for s, g in precios.groupby("serie")},
    "clave": json.loads((S / "resultados_clave.json").read_text()),
    "descomposicion": pd.read_csv(S / "tablas" / "Tabla_6_descomposicion.csv", keep_default_na=False).to_dict("records"),
    "acumulada": pd.read_csv(S / "tablas" / "Tabla_6b_descomposicion_acumulada.csv").to_dict("records"),
    "metodos": pd.read_csv(S / "tablas" / "Tabla_9_confrontacion.csv").round(3).to_dict("records"),
    "transmision": pd.read_csv(S / "tablas" / "Tabla_8c_transmision.csv").round(3).to_dict("records"),
}
(DOCS / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
shutil.copy(BASE / "datos" / "raw" / "mapa_municipios_narino.geojson", DOCS / "mapa.geojson")
print("docs/datos.json:", round((DOCS / "datos.json").stat().st_size / 1024), "KB")
