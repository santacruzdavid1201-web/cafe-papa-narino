# Fuentes de datos

Los archivos de `raw/` son copias de respaldo de las fuentes oficiales, descargadas el 9 de noviembre de 2026. Los archivos grandes se guardan **filtrados a Nariño** con las mismas funciones del notebook (`filtrar_eva`, `filtrar_sipsa`), que también se aplican cuando el notebook descarga la fuente oficial.

| Archivo en `raw/` | Contenido | Entidad | URL oficial | Filtro |
|---|---|---|---|---|
| `eva_2007_2018_narino.csv` | Evaluaciones Agropecuarias Municipales: área sembrada y cosechada, producción y rendimiento por municipio, cultivo y periodo, 2007–2018 | MinAgricultura – UPRA (datos.gov.co, conjunto 2pnw-mmge) | https://www.datos.gov.co/api/views/2pnw-mmge/rows.csv?accessType=DOWNLOAD | Departamento = Nariño; cultivo = café o papa |
| `eva_2019_2025_narino.csv` | Ídem, 2019–2025 (nueva metodología EVA) | MinAgricultura – UPRA (datos.gov.co, conjunto uejq-wxrr) | https://www.datos.gov.co/api/views/uejq-wxrr/rows.csv?accessType=DOWNLOAD | Ídem |
| `sipsa_papa_pasto_ipiales.csv` | Precios mayoristas mensuales ($/kg) de papa en Pasto (El Potrerillo) e Ipiales, 2013–2024 | DANE – SIPSA, series históricas de precios mayoristas | https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas.xlsx (2013–2017); …-2018.xlsx a …-2022.xlsx; https://www.dane.gov.co/files/operaciones/SIPSA/anex-SIPSA-SerieHistoricaMayorista-Dic2023.xlsx; …-2024.xlsx | Productos que empiezan por «Papa»; mercados de Pasto e Ipiales |
| `fnc_precios_area_produccion.xlsx` | Precio interno de referencia del café (diario y mensual, $/carga de 125 kg CPS), precio externo, área cafetera por departamento | Federación Nacional de Cafeteros | https://federaciondecafeteros.org/wp-content/uploads/2026/09/Precios-area-y-produccion-de-cafe-Noviembre-2026.xlsx | Ninguno (archivo original) |
| `pib_actividad.xlsx` | Valor agregado por actividad económica y departamento, base 2015, 2005–2025pr (corriente y volumen encadenado) | DANE – Cuentas departamentales | https://www.dane.gov.co/files/operaciones/PIB/anex-PIBDep-Activecono-2025pr.xlsx | Ninguno (archivo original) |
| `mapa_municipios_narino.geojson` | Límites municipales del Marco Geoestadístico Nacional 2018 | DANE, vía repositorio público caticoa3/colombia_mapa | https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/co_2018_MGN_MPIO_POLITICO.geojson | Departamento 52 (Nariño) |

## Decisiones de armonización

* **Unidad del café:** la EVA reporta café verde equivalente hasta 2018 y pergamino seco desde 2019. Se convierte a pergamino seco (CPS) con el factor 1 kg verde ≈ 1.25 kg CPS, unidad en la que la FNC publica el precio interno.
* **Papa 2018:** la EVA solo publica el semestre A; el año se trata como faltante.
* **Cambio metodológico EVA 2019:** las variaciones de cantidades 2018→2019 se excluyen de la descomposición y los modelos incluyen una dummy D2019.
* **Precio de la papa:** promedio de las variedades Capiro y Única en Pasto (reportadas sin interrupción 2013–2024); la papa criolla usa «papa criolla sucia». El SIPSA no tiene serie histórica para 2012.
* **Precios reales:** deflactor implícito del valor agregado agropecuario de Nariño (2015 = 100).

## Bases nacionales para el observatorio AGROCOL (`nacional/`)

Copias completas, **sin filtrar**, de las mismas fuentes oficiales, descargadas el 9 de noviembre de 2026. Las lee en línea el notebook `AGROCOL_Observatorio_Datos.ipynb`, que las resume en `observatorio.json`, el archivo que carga la página web del observatorio.

| Archivo en `nacional/` | Contenido | Entidad | URL oficial | Filtro |
|---|---|---|---|---|
| `sipsa_2019.xlsx` … `sipsa_2024.xlsx` | Precios mayoristas mensuales ($/kg) de todos los productos y mercados del país, un anexo por año | DANE – SIPSA, series históricas de precios mayoristas | Las mismas de `sipsa_papa_pasto_ipiales.csv` (tabla de arriba) | Ninguno (anexo original, renombrado) |
| `eva_2019_2025.csv` | Evaluaciones Agropecuarias Municipales de todo el país: área sembrada y cosechada, producción y rendimiento por municipio, cultivo y periodo, 2019–2025 | MinAgricultura – UPRA (datos.gov.co, conjunto uejq-wxrr) | https://www.datos.gov.co/api/views/uejq-wxrr/rows.csv?accessType=DOWNLOAD | Ninguno |
| `observatorio.json` | Resumen que lee la web: precio medio, número de reportes, mínimo y máximo por producto, mes y departamento; producción y áreas EVA por departamento, año y cultivo | Generado por `AGROCOL_Observatorio_Datos.ipynb` con los archivos anteriores | — | Agregado (reproduce exactamente los totales de las bases) |

## Indicadores departamentales para el sistema RAG + multiagente (`departamental/`)

Archivos oficiales del DANE, descargados el 10 de noviembre de 2026 y sin modificar. Los lee en línea el notebook `sistema_rag_multiagente_colombia.ipynb`, que también usa `raw/pib_actividad.xlsx` para el PIB departamental.

| Archivo en `departamental/` | Contenido | Entidad | URL oficial |
|---|---|---|---|
| `anex-PMDepartamental-2025.xlsx` | Pobreza monetaria y extrema, Gini, ingreso per cápita y población, 23 departamentos y Bogotá, 2021–2025 | DANE – Pobreza monetaria (GEIH) | https://www.dane.gov.co/files/operaciones/PM/anex-PMDepartamental-2025.xlsx |
| `anex-GEIHDepartamentos-2025.xls` | Mercado laboral (TGP, ocupación, desocupación), 23 departamentos, 2007–2025 | DANE – GEIH | https://www.dane.gov.co/files/operaciones/GEIH/anex-GEIHDepartamentos-2025.xls |
| `cp-PMDepartamental-2025.pdf` | Comunicado de prensa de pobreza monetaria departamental 2025 (base de conocimiento del RAG) | DANE | https://www.dane.gov.co/files/operaciones/PM/cp-PMDepartamental-2025.pdf |
| `bol-GEIHDepartamentos-2025.pdf` | Boletín técnico de mercado laboral por departamentos 2025 (RAG) | DANE | https://www.dane.gov.co/files/operaciones/GEIH/bol-GEIHDepartamentos-2025.pdf |
| `bol-PIBDep-2025pr.pdf` | Boletín técnico del PIB por departamento 2025pr (RAG) | DANE | https://www.dane.gov.co/files/operaciones/PIB/bol-PIBDep-2025pr.pdf |
| `colombia_departamentos.geojson` | Límites departamentales del MGN 2018, con nombres normalizados (matriz de vecinos y mapa) | DANE, vía caticoa3/colombia_mapa | https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/co_2018_MGN_DPTO_POLITICO.geojson |
| `rag_colombia.json` | Panel, resultados de los modelos, fragmentos del RAG e informe de los agentes; lo lee la web | Generado por el notebook | — |
