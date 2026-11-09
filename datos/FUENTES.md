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
