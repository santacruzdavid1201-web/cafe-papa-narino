# Café, papa y valor agregado agropecuario en Nariño, 2012–2023

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santacruzdavid1201-web/cafe-papa-narino/blob/main/cafe_papa_narino.ipynb)
[![Asistente RAG en Colab](https://img.shields.io/badge/Asistente_RAG-Colab-eb6834?logo=googlecolab)](https://colab.research.google.com/github/santacruzdavid1201-web/cafe-papa-narino/blob/main/rag/consulta_rag.ipynb)
[![Observatorio](https://img.shields.io/badge/Observatorio-web-2a78d6)](https://santacruzdavid1201-web.github.io/cafe-papa-narino/)

Código reproducible del artículo final del proyecto de **Seminario de Investigación Regional II** (Programa de Economía, Universidad de Nariño). Pregunta: ¿los cambios en el ingreso bruto del café y la papa en Nariño se explican más por las cantidades producidas o por los precios, y cómo se relacionan con el valor agregado agropecuario del departamento?

## Cómo ejecutarlo

1. Haga clic en **Abrir en Colab** (arriba).
2. En Colab: **Entorno de ejecución → Ejecutar todas**. Tarda unos 2 minutos.
3. No hay que subir archivos: el notebook descarga cada fuente oficial y, si alguna rechaza la conexión (el DANE bloquea los servidores de Google), usa la copia guardada en `datos/raw/` de este repositorio. La tabla de la sección 1 muestra qué fuente se usó.
4. La sección 9 abre la **aplicación interactiva** (filtros por cultivo, municipio, años y tipo de precio; pestañas de panorama, mapa, descomposición, modelo y datos).
5. La sección 10 descarga `salidas.zip` con las figuras y tablas, numeradas igual que en el PDF.

**En un computador propio** (Python 3.10+):

```bash
git clone https://github.com/santacruzdavid1201-web/cafe-papa-narino.git
cd cafe-papa-narino
pip install -r requirements.txt
jupyter notebook cafe_papa_narino.ipynb
```

## Estructura

```
├── cafe_papa_narino.ipynb   # notebook único: datos → análisis → figuras/tablas → app
├── articulo/                # artículo final en español e inglés (PDF)
├── docs/                    # observatorio web (GitHub Pages)
├── observatorio/construir.py
├── rastreador/              # verificación semanal de fuentes oficiales y registro
├── rag/                     # asistente de consulta: núcleo, configuración y notebook de Colab
├── config/                  # traducción de las figuras al inglés
├── requirements.txt
├── datos/
│   ├── FUENTES.md           # URL oficial, filtro aplicado y fecha de consulta de cada archivo
│   ├── raw/                 # copias de respaldo de las fuentes oficiales (filtradas a Nariño)
│   ├── nacional/            # SIPSA y EVA completos (todo el país) para el observatorio AGROCOL
│   └── departamental/       # pobreza, mercado laboral y boletines DANE para el sistema RAG + multiagente
└── salidas/
    ├── figuras/             # Figura_1 … Figura_6 (y Figura_4b)
    ├── figuras_en/          # las mismas figuras con textos en inglés
    ├── tablas/              # Tablas 2, 5, 6, 6b, 7, 7b, 7c, 8a, 8b, 8c, 9 (Excel y CSV)
    ├── datos/               # bases armonizadas (CSV) que usan el observatorio y el RAG
    └── resultados_clave.json
```

## Cuatro métodos sobre la misma pregunta

| Método | Qué responde | Sección del notebook |
|---|---|---|
| Descomposición de la varianza Δln(ingreso) = Δln(área) + Δln(rendimiento) + Δln(precio), con bootstrap de municipios | ¿Cantidades o precios, y a qué escala? | 5 |
| Panel de respuesta de la oferta con efectos fijos de municipio (errores Driscoll-Kraay) | ¿Responde la oferta al precio del año anterior? | 6 |
| Panel espacial SAR y SEM (contigüidad tipo reina; robustez con k = 4 vecinos) | ¿Se propagan los choques entre municipios vecinos? | 6b |
| ARDL y prueba de límites para los precios de la papa en Pasto e Ipiales | ¿Están integrados los mercados regionales? | 7b |

La relación con el valor agregado agropecuario del DANE se evalúa en la sección 7, y la Figura 6 confronta las elasticidades de los métodos 2 y 3.

## Productos tecnológicos

| Producto | Dónde | Qué hace |
|---|---|---|
| Código reproducible | `cafe_papa_narino.ipynb` | Descarga, armoniza, estima los cuatro métodos, genera cada tabla y figura del artículo (también en inglés) y abre una aplicación interactiva. |
| Observatorio estadístico | `docs/` · https://santacruzdavid1201-web.github.io/cafe-papa-narino/ | Sitio web con series por municipio, mapa, precios mensuales, descomposición, confrontación de métodos, estado de las fuentes y descargas. |
| Rastreador de datos | `rastreador/` + `.github/workflows/rastreador.yml` | Cada lunes revisa las fuentes oficiales (API de datos.gov.co, encabezados HTTP, huellas SHA-256, páginas índice), registra el resultado en `rastreador/registro.csv`, vuelve a ejecutar el notebook y actualiza el observatorio. |
| Asistente de consulta (RAG) | `rag/consulta_rag.ipynb` | Chat en Colab sobre el corpus del proyecto (artículo ES/EN, documentación, tablas, referencias) con recuperación híbrida BM25 + embeddings multilingües, modelo abierto Qwen2.5 y citas por documento, sección y página; incluye evaluación de la recuperación. |

Para replicar exactamente el PDF aunque las fuentes se actualicen, ponga `INTENTAR_OFICIAL = False` en la sección 1.
