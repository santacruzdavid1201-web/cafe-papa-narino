"""Núcleo del sistema de consulta con recuperación aumentada (RAG) sobre el corpus del proyecto.

Piezas:
  1. construir_corpus(): extrae el texto del artículo (PDF en español e inglés, por página y sección),
     de la documentación del repositorio, de las tablas de resultados y de las fichas de las referencias.
  2. trocear(): divide cada documento en fragmentos de ~170 palabras con solapamiento, conservando
     documento, sección y página para poder citar.
  3. Buscador: recuperación híbrida = BM25 (léxica) + embeddings multilingües (multilingual-e5),
     combinadas por fusión de rangos recíprocos. Si el modelo de embeddings no se puede descargar,
     funciona solo con BM25.
  4. Generador: modelo abierto Qwen2.5-Instruct (3B con GPU; 0.5B en CPU) que responde solo con el
     contexto recuperado y cita [n]. Si no hay modelo, modo extractivo: devuelve las oraciones más
     relevantes de los fragmentos.
  5. evaluar(): exactitud de la recuperación (acierto@k y MRR) con preguntas de control.
"""
import json, math, re, unicodedata
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------------- utilidades
def normalizar(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))

STOP = set("""a al algo ante con contra de del desde el ella en entre era es esa ese eso esta este esto fue ha hay la las le les lo los mas me mi muy no nos o para pero por que se sea ser si sin sobre su sus tambien te tiene un una uno unos y ya
the of and to in for on with by an be is are was were as at from that this these those it its or which into than then their there""".split())

def tokens(t):
    return [w for w in re.findall(r"[a-z0-9ñ]+(?:[.,][0-9]+)?", normalizar(t)) if w not in STOP and len(w) > 1]

# ---------------------------------------------------------------------------------- corpus
ENCABEZADO = re.compile(r"^\s*(\d{1,2}(?:\.\d)?\.?)\s+([A-ZÁÉÍÓÚÑ][^\n]{2,90})$")

def texto_pdf(ruta, nombre_doc):
    """Devuelve una lista de documentos (uno por página) con la sección vigente en cada página."""
    from pypdf import PdfReader
    docs, seccion = [], "Portada"
    for i, pag in enumerate(PdfReader(str(ruta)).pages, start=1):
        txt = pag.extract_text() or ""
        lineas = txt.splitlines()
        sec_pag = seccion
        for l in lineas:
            m = ENCABEZADO.match(l.strip())
            if m and len(l.split()) <= 12 and not re.search(r"\d{4}", m.group(2)):
                seccion = (m.group(1) + " " + m.group(2)).strip()
                if sec_pag == "Portada" or lineas.index(l) < 4:
                    sec_pag = seccion
            elif l.strip() in ("Referencias", "References", "Resumen", "Abstract"):
                seccion = l.strip()
        docs.append({"doc": nombre_doc, "seccion": sec_pag, "pagina": i, "texto": re.sub(r"\s+\n", "\n", txt)})
    return docs

def texto_markdown(ruta, nombre_doc):
    txt = Path(ruta).read_text(encoding="utf-8")
    partes = re.split(r"\n(?=#+ )", txt)
    return [{"doc": nombre_doc, "seccion": (p.splitlines()[0].lstrip("# ").strip() if p.startswith("#") else "Inicio"), "pagina": None, "texto": p}
            for p in partes if p.strip()]

def texto_tabla(ruta, nombre_doc, descripcion):
    import pandas as pd
    df = pd.read_csv(ruta, keep_default_na=False)
    filas = [f"{descripcion}."] + ["; ".join(f"{c}: {v}" for c, v in r.items() if str(v) != "") for _, r in df.iterrows()]
    return [{"doc": nombre_doc, "seccion": descripcion, "pagina": None, "texto": "\n".join(filas)}]

def texto_clave(ruta, glosario, nombre_doc):
    clave = json.loads(Path(ruta).read_text())
    frases = []
    for k, v in clave.items():
        if k in glosario:
            frases.append(f"{glosario[k]}: {v:.3f}." if isinstance(v, float) else f"{glosario[k]}: {v}.")
    return [{"doc": nombre_doc, "seccion": "Cifras clave", "pagina": None, "texto": "\n".join(frases)}]

def construir_corpus(base, config):
    base = Path(base)
    docs = []
    for d in config["documentos"]:
        ruta = base / d["ruta"]
        if not ruta.exists():
            print("  (no encontrado)", d["ruta"])
            continue
        if d["tipo"] == "pdf":
            docs += texto_pdf(ruta, d["nombre"])
        elif d["tipo"] == "markdown":
            docs += texto_markdown(ruta, d["nombre"])
        elif d["tipo"] == "tabla":
            docs += texto_tabla(ruta, d["nombre"], d["descripcion"])
        elif d["tipo"] == "clave":
            docs += texto_clave(ruta, config.get("glosario_clave", {}), d["nombre"])
        elif d["tipo"] == "notebook":
            nb = json.loads(ruta.read_text(encoding="utf-8"))
            md = "\n\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
            docs += [{"doc": d["nombre"], "seccion": p.splitlines()[0].lstrip("# ").strip(), "pagina": None, "texto": p}
                     for p in re.split(r"\n(?=## )", md) if p.strip()]
    extra = base / "rag" / "corpus_extra"                 # PDF adicionales que el usuario quiera indexar
    for ruta in sorted(extra.glob("*.pdf")) if extra.exists() else []:
        docs += texto_pdf(ruta, ruta.stem)
    for r in config.get("referencias", []):
        docs.append({"doc": "Referencias del artículo", "seccion": r["cita"], "pagina": None,
                     "texto": f"{r['cita']}. {r['referencia']}. {r.get('resumen', '')}"})
    return docs

def trocear(docs, palabras=170, solape=40):
    trozos = []
    for d in docs:
        texto = re.sub(r"[ \t]+", " ", d["texto"]).strip()
        pal = texto.split()
        if not pal:
            continue
        paso = max(palabras - solape, 1)
        for i in range(0, max(len(pal) - solape, 1), paso):
            frag = " ".join(pal[i:i + palabras])
            trozos.append({**{k: d[k] for k in ("doc", "seccion", "pagina")}, "texto": frag})
    for i, t in enumerate(trozos):
        t["id"] = i
    return trozos

# ---------------------------------------------------------------------------------- recuperación
class BM25:
    def __init__(self, textos, k1=1.4, b=0.75):
        self.docs = [tokens(t) for t in textos]
        self.N = len(self.docs)
        self.avg = sum(map(len, self.docs)) / max(self.N, 1)
        self.df = Counter(w for d in self.docs for w in set(d))
        self.tf = [Counter(d) for d in self.docs]
        self.k1, self.b = k1, b
    def puntajes(self, consulta):
        q = tokens(consulta)
        out = []
        for d, tf in zip(self.docs, self.tf):
            s = 0.0
            for w in q:
                if w in tf:
                    idf = math.log(1 + (self.N - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += idf * tf[w] * (self.k1 + 1) / (tf[w] + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            out.append(s)
        return out

class Buscador:
    def __init__(self, trozos, modelo_embeddings="intfloat/multilingual-e5-small", usar_embeddings=True):
        self.trozos = trozos
        textos = [f"{t['doc']} · {t['seccion']}. {t['texto']}" for t in trozos]
        self.bm25 = BM25(textos)
        self.modelo = None
        if usar_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                self.np = np
                self.modelo = SentenceTransformer(modelo_embeddings)
                self.emb = self.modelo.encode(["passage: " + t for t in textos], batch_size=32, normalize_embeddings=True, show_progress_bar=True)
                print(f"Embeddings: {modelo_embeddings} · {self.emb.shape[0]} fragmentos")
            except Exception as e:
                print("Sin embeddings (se usa solo BM25):", type(e).__name__, str(e)[:120])
                self.modelo = None

    def buscar(self, consulta, k=5, k_rrf=60):
        bm = self.bm25.puntajes(consulta)
        orden_bm = sorted(range(len(bm)), key=lambda i: -bm[i])
        rrf = Counter()
        for r, i in enumerate(orden_bm[:100]):
            rrf[i] += 1 / (k_rrf + r)
        if self.modelo is not None:
            q = self.modelo.encode(["query: " + consulta], normalize_embeddings=True)[0]
            sim = self.emb @ q
            for r, i in enumerate(self.np.argsort(-sim)[:100]):
                rrf[int(i)] += 1 / (k_rrf + r)
        return [self.trozos[i] for i, _ in rrf.most_common(k)]

# ---------------------------------------------------------------------------------- generación
SISTEMA = ("Eres un asistente de investigación del proyecto descrito en el contexto. Responde SOLO con la información del contexto. "
           "Cita cada afirmación con el número del fragmento entre corchetes, por ejemplo [2]. Si el contexto no contiene la respuesta, "
           "dilo explícitamente. Responde en el idioma de la pregunta, en tercera persona y en un máximo de 180 palabras.")

class Generador:
    def __init__(self, modo="auto"):
        """modo: 'auto' (GPU → Qwen2.5-3B; CPU → extractivo), 'qwen-3b', 'qwen-0.5b' o 'extractivo'."""
        self.modo, self.pipe = modo, None
        try:
            import torch
            gpu = torch.cuda.is_available()
        except ImportError:
            gpu = False
        nombre = {"qwen-3b": "Qwen/Qwen2.5-3B-Instruct", "qwen-0.5b": "Qwen/Qwen2.5-0.5B-Instruct"}.get(modo)
        if modo == "auto":
            nombre = "Qwen/Qwen2.5-3B-Instruct" if gpu else None
        if nombre:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                self.tok = AutoTokenizer.from_pretrained(nombre)
                self.lm = AutoModelForCausalLM.from_pretrained(nombre, torch_dtype=torch.float16 if gpu else torch.float32,
                                                               device_map="auto" if gpu else None)
                self.modo = nombre
                print("Generador:", nombre, "(GPU)" if gpu else "(CPU)")
            except Exception as e:
                print("No se pudo cargar el modelo; modo extractivo:", type(e).__name__)
                self.modo = "extractivo"
        else:
            self.modo = "extractivo"
            print("Generador: modo extractivo (sin GPU). Para respuestas redactadas: Entorno de ejecución → Cambiar tipo → GPU T4.")

    def responder(self, pregunta, fragmentos):
        contexto = "\n\n".join(f"[{i + 1}] ({f['doc']}, {f['seccion']}{', p. ' + str(f['pagina']) if f['pagina'] else ''})\n{f['texto']}"
                               for i, f in enumerate(fragmentos))
        if self.modo == "extractivo":
            return self._extractivo(pregunta, fragmentos)
        import torch
        mensajes = [{"role": "system", "content": SISTEMA},
                    {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}]
        # Se arma el texto con la plantilla de chat y luego se tokeniza: así funciona con cualquier versión de
        # transformers (las recientes devuelven un diccionario y no un tensor en apply_chat_template).
        texto = self.tok.apply_chat_template(mensajes, add_generation_prompt=True, tokenize=False)
        entrada = self.tok(texto, return_tensors="pt").to(self.lm.device)
        with torch.no_grad():
            salida = self.lm.generate(**entrada, max_new_tokens=380, do_sample=False, repetition_penalty=1.05,
                                      pad_token_id=self.tok.eos_token_id)
        n = entrada["input_ids"].shape[1]
        return self.tok.decode(salida[0][n:], skip_special_tokens=True).strip()

    @staticmethod
    def _extractivo(pregunta, fragmentos, n=4):
        q = set(tokens(pregunta))
        candidatas = []
        for i, f in enumerate(fragmentos):
            for o in re.split(r"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚ(])", f["texto"]):
                t = set(tokens(o))
                if len(o.split()) >= 6 and t:
                    candidatas.append((len(q & t) / math.sqrt(len(t)) + 0.15 / (i + 1), o.strip(), i + 1))
        elegidas = sorted(candidatas, key=lambda x: -x[0])[:n]
        if not elegidas:
            return "El corpus no contiene información suficiente para responder."
        return " ".join(f"{o} [{i}]" for _, o, i in elegidas)

# ---------------------------------------------------------------------------------- evaluación
def evaluar(buscador, preguntas, k=5):
    """preguntas: lista de {'pregunta', 'debe_contener'}; un acierto ocurre si algún fragmento recuperado
    contiene la cadena esperada (normalizada). Devuelve acierto@1, acierto@3, acierto@k y MRR."""
    filas, rr = [], []
    for q in preguntas:
        res = buscador.buscar(q["pregunta"], k=k)
        objetivo = normalizar(q["debe_contener"])
        pos = next((i + 1 for i, r in enumerate(res) if objetivo in normalizar(r["texto"])), None)
        rr.append(1 / pos if pos else 0)
        filas.append({"pregunta": q["pregunta"], "esperado": q["debe_contener"], "posición": pos or "—",
                      "fuente top-1": f"{res[0]['doc']} · {res[0]['seccion']}" if res else "—"})
    n = len(preguntas)
    resumen = {"acierto@1": sum(1 for f in filas if f["posición"] == 1) / n,
               "acierto@3": sum(1 for f in filas if isinstance(f["posición"], int) and f["posición"] <= 3) / n,
               f"acierto@{k}": sum(1 for f in filas if isinstance(f["posición"], int)) / n,
               "MRR": sum(rr) / n}
    return filas, resumen
