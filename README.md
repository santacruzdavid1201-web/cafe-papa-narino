# Café, papa y valor agregado agropecuario en Nariño, 2012–2023

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santacruzdavid1201-web/cafe-papa-narino/blob/main/cafe_papa_narino.ipynb)

Código reproducible del primer borrador del proyecto de **Seminario de Investigación Regional II** (Programa de Economía, Universidad de Nariño). Pregunta: ¿los cambios en el ingreso bruto del café y la papa en Nariño se explican más por las cantidades producidas o por los precios, y cómo se relacionan con el valor agregado agropecuario del departamento?

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
├── requirements.txt
├── datos/
│   ├── FUENTES.md           # URL oficial, filtro aplicado y fecha de consulta de cada archivo
│   └── raw/                 # copias de respaldo de las fuentes oficiales (filtradas a Nariño)
└── salidas/
    ├── figuras/             # Figura_1 … Figura_5
    ├── tablas/              # Tabla_2, 5, 6, 6b, 7, 7b, 8a, 8b (Excel y CSV)
    └── resultados_clave.json
```

## Método en una línea

Ingreso bruto = toneladas (EVA) × precio (FNC para el café; SIPSA-DANE, Pasto, para la papa), en pesos de 2015. Se descompone Δln(ingreso) = Δln(área) + Δln(rendimiento) + Δln(precio) a escala departamental y municipal, se estima la respuesta de la oferta al precio con un panel de efectos fijos de municipio (errores Driscoll-Kraay) y se contrasta el ingreso bruto con el valor agregado agropecuario del DANE.

Para replicar exactamente el PDF aunque las fuentes se actualicen, ponga `INTENTAR_OFICIAL = False` en la sección 1.
