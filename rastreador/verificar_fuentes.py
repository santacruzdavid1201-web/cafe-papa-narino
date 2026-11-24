"""Rastreador de fuentes oficiales.

Revisa cada fuente listada en rastreador/fuentes.json y deja constancia de su estado:
  * archivo  -> encabezados HTTP (estado, Last-Modified, ETag, tamaño) y, si el archivo es pequeño,
                huella SHA-256 del contenido remoto frente a la copia de datos/raw/.
  * socrata  -> fecha de última actualización de filas del conjunto en datos.gov.co (API de metadatos).
  * pagina   -> enlaces a archivos de datos publicados en una página índice (detecta versiones nuevas).
  * api      -> respuesta de una API JSON (último año disponible).
Resultados:
  rastreador/registro.csv          historial (una fila por fuente y ejecución)
  rastreador/estado_fuentes.json   último estado, comparado con el anterior
  docs/estado_fuentes.json         copia para el observatorio web
Uso:  python rastreador/verificar_fuentes.py
"""
import csv, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests

BASE = Path(__file__).resolve().parents[1]
CFG = json.loads((BASE / "rastreador" / "fuentes.json").read_text(encoding="utf-8"))
ESTADO = BASE / "rastreador" / "estado_fuentes.json"
REGISTRO = BASE / "rastreador" / "registro.csv"
AHORA = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
CABECERAS = {"User-Agent": "Mozilla/5.0 (rastreador academico Universidad de Narino)"}
LIMITE_DESCARGA = 40 * 1024 * 1024        # solo se descarga completo si pesa menos de 40 MB

def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()

def revisar_archivo(f):
    r = {"estado_http": None, "ultima_modificacion": None, "etag": None, "tamano": None, "huella_remota": None}
    try:
        resp = requests.head(f["url"], headers=CABECERAS, timeout=40, allow_redirects=True)
        if resp.status_code >= 400 or resp.status_code == 405:
            resp = requests.get(f["url"], headers=CABECERAS, timeout=60, stream=True)
        r.update(estado_http=resp.status_code, ultima_modificacion=resp.headers.get("Last-Modified"),
                 etag=resp.headers.get("ETag"), tamano=resp.headers.get("Content-Length"))
        if resp.status_code == 200 and f.get("comparar_huella") and int(resp.headers.get("Content-Length") or 0) < LIMITE_DESCARGA:
            cont = requests.get(f["url"], headers=CABECERAS, timeout=120).content
            r["huella_remota"] = hashlib.sha256(cont).hexdigest()
    except requests.RequestException as e:
        r["error"] = type(e).__name__
    return r

def revisar_socrata(f):
    try:
        meta = requests.get(f"https://www.datos.gov.co/api/views/{f['id_conjunto']}.json", headers=CABECERAS, timeout=40)
        meta.raise_for_status()
        m = meta.json()
        ts = m.get("rowsUpdatedAt") or m.get("viewLastModified")
        return {"estado_http": 200, "ultima_modificacion": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d") if ts else None,
                "nombre_conjunto": m.get("name")}
    except (requests.RequestException, ValueError) as e:
        return {"estado_http": None, "error": type(e).__name__}

def revisar_pagina(f):
    try:
        resp = requests.get(f["url"], headers=CABECERAS, timeout=40)
        enlaces = sorted({urljoin(f["url"], a) for a in re.findall(r'href="([^"]+)"', resp.text) if re.search(f["patron"], a, re.I)})
        return {"estado_http": resp.status_code, "enlaces": enlaces[:40], "huella_enlaces": hashlib.sha256("\n".join(enlaces).encode()).hexdigest()[:16]}
    except requests.RequestException as e:
        return {"estado_http": None, "error": type(e).__name__}

def revisar_api(f):
    try:
        resp = requests.get(f["url"], headers=CABECERAS, timeout=40)
        datos = resp.json()
        filas = datos[1] if isinstance(datos, list) and len(datos) > 1 else []
        anios = [int(x["date"]) for x in filas if x.get("value") is not None]
        return {"estado_http": resp.status_code, "ultimo_dato": max(anios) if anios else None}
    except (requests.RequestException, ValueError) as e:
        return {"estado_http": None, "error": type(e).__name__}

REVISORES = {"archivo": revisar_archivo, "socrata": revisar_socrata, "pagina": revisar_pagina, "api": revisar_api}

def clasificar(f, nuevo, viejo):
    if nuevo.get("estado_http") != 200:
        return "no accesible desde el servidor" if nuevo.get("estado_http") in (401, 403, None) else f"error HTTP {nuevo.get('estado_http')}"
    if f["tipo"] == "archivo" and nuevo.get("huella_remota") and f.get("archivo_local"):
        local = BASE / "datos" / "raw" / f["archivo_local"]
        if local.exists():
            return "sin cambios frente a la copia" if sha256_archivo(local) == nuevo["huella_remota"] else "versión nueva publicada"
    if not viejo:
        return "primera revisión"
    claves = {"archivo": ["ultima_modificacion", "etag", "tamano"], "socrata": ["ultima_modificacion"],
              "pagina": ["huella_enlaces"], "api": ["ultimo_dato"]}[f["tipo"]]
    return "versión nueva publicada" if any(nuevo.get(k) != viejo.get(k) for k in claves if nuevo.get(k)) else "sin cambios"

def main():
    previo = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    viejos = {x["id"]: x for x in previo.get("fuentes", [])}
    salida = []
    for f in CFG["fuentes"]:
        nuevo = REVISORES[f["tipo"]](f)
        nuevo["estado"] = clasificar(f, nuevo, viejos.get(f["id"]))
        nuevo.update(id=f["id"], nombre=f["nombre"], entidad=f["entidad"], tipo=f["tipo"], url=f["url"], revisado=AHORA)
        salida.append(nuevo)
        print(f"{f['id']:<28} {str(nuevo.get('estado_http')):<5} {nuevo['estado']}")
    estado = {"proyecto": CFG["proyecto"], "revisado": AHORA, "fuentes": salida}
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    (BASE / "docs").mkdir(exist_ok=True)
    (BASE / "docs" / "estado_fuentes.json").write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    nuevo_archivo = not REGISTRO.exists()
    with open(REGISTRO, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo_archivo:
            w.writerow(["revisado", "id", "tipo", "estado_http", "estado", "ultima_modificacion", "tamano", "detalle"])
        for x in salida:
            w.writerow([AHORA, x["id"], x["tipo"], x.get("estado_http"), x["estado"], x.get("ultima_modificacion") or x.get("ultimo_dato") or "",
                        x.get("tamano") or "", x.get("error") or x.get("huella_enlaces") or ""])
    cambios = [x["id"] for x in salida if x["estado"] == "versión nueva publicada"]
    print("Fuentes con versión nueva:", cambios or "ninguna")
    if "--falla-si-cambia" in sys.argv and cambios:
        sys.exit(78)

if __name__ == "__main__":
    main()
