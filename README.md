# ETL Weatherstack - Mineria de datos G1
## Perez - Bonilla - Grupo 4

Pipeline ETL para extracción, transformación y análisis de datos meteorológicos
utilizando la API de Weatherstack. Proyecto didáctico orientado a prácticas
profesionales de ingesta y tratamiento de datos.

## Resumen

Este repositorio contiene un pipeline sencillo pero completo que muestra cómo:

- Extraer datos desde una API externa.
- Normalizar y transformar los datos con pandas.
- Guardar resultados en CSV/JSON y generar visualizaciones.
- Registrar ejecuciones y manejar configuraciones mediante variables de
entorno.

## Características clave

- Modular: scripts separados para extracción, transformación y visualización.
- Reproducible: uso de virtualenv y archivo `requirements.txt`.
- Observabilidad: logging configurado en `logs/`.
- Salidas en formatos comunes: CSV, JSON y gráficos PNG.

## Requisitos

- Python 3.11 o superior
- pip
- Acceso a Internet (para consultar la API de Weatherstack)

## Instalación rápida

1. Clona el repositorio:

```bash
git clone https://github.com/tu_usuario/etl-weatherstack.git
cd etl-weatherstack
```

2. Crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Configura la API key en un fichero `.env` (no incluir en el control de versiones):

```bash
echo "API_KEY=tu_api_key_aqui" > .env
```

## Uso

Ejecuta el extractor para iniciar el pipeline:

```bash
python scripts/extractor.py
```

Dependiendo de la implementación, los scripts pueden generar la salida en
`data/` y registros en `logs/`.

## Salidas esperadas

- `data/clima.csv` — Datos procesados en formato tabular (CSV).
- `data/clima_raw.json` — Respuesta original de la API (JSON).
- `data/clima_analysis.png` — Gráficas de análisis generadas.
- `logs/etl.log` — Archivo de logging con información de la ejecución.

## Estructura del proyecto

```
etl-weatherstack/
├── scripts/            # Extraer, transformar y visualizar
│   ├── extractor.py
│   ├── transformador.py
│   └── visualizador.py
├── data/               # Salida: CSV, JSON, PNG
├── logs/               # Archivos de log
├── .env                # Variables de entorno (excluded from VCS)
├── requirements.txt
└── README.md
```

## Configuración de la API (Weatherstack)

1. Regístrate en https://weatherstack.com y obtén una Access Key.
2. Añade la clave a `.env` como `API_KEY=tu_clave`.

Nota: revisa los límites del plan gratuito de Weatherstack antes de automatizar
llamadas a gran escala.

## Buenas prácticas y recomendaciones

- No subir la `.env` al repositorio. Añádela a `.gitignore` si no está ya.
- Manejar errores de red y límites de tasa (rate limiting) en `extractor.py`.
- Añadir tests unitarios para transformaciones críticas.
- Instrumentar métricas y alertas si se pone en producción.

## Contribuciones

Se agradecen mejoras. Flujo recomendado:

1. Haz fork del repositorio.
2. Crea una rama con un nombre descriptivo.
3. Abre un Pull Request explicando los cambios.

---
**Última actualización:** Febrero 2026
**Estado:** En desarrollo

