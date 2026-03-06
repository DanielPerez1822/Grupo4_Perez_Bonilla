#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# ==============================
# Cargar variables de entorno
# ==============================
load_dotenv()

# ==============================
# Configuración de logging
# ==============================
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NasaExtractor:

    def __init__(self):
        self.api_key = os.getenv("NASA_API_KEY")
        self.base_url = os.getenv("NASA_BASE_URL")

        if not self.api_key:
            raise ValueError("❌ NASA_API_KEY no configurada en .env")

        if not self.base_url:
            raise ValueError("❌ NASA_BASE_URL no configurada en .env")

        # Fechas dinámicas
        hoy = datetime.utcnow().date()
        self.start_date = os.getenv("START_DATE") or hoy.strftime("%Y-%m-%d")
        self.end_date = os.getenv("END_DATE") or (hoy + timedelta(days=7)).strftime("%Y-%m-%d")

        logger.info("✅ Extractor NASA inicializado")
        logger.info(f"📅 Rango: {self.start_date} → {self.end_date}")

    # ==========================================
    # 1️⃣ NEO Feed
    # ==========================================
    def extraer_asteroides(self):
        try:
            url = f"{self.base_url}/neo/rest/v1/feed"

            params = {
                "start_date": self.start_date,
                "end_date": self.end_date,
                "api_key": self.api_key
            }

            response = requests.get(url, params=params, timeout=15)
            logger.info(f"🌍 URL NEO: {response.url}")

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"❌ Error extrayendo asteroides: {str(e)}")
            return None

    # ==========================================
    # 2️⃣ APOD
    # ==========================================
    def extraer_apod(self):
        try:
            url = f"{self.base_url}/planetary/apod"

            params = {
                "api_key": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            logger.info(f"🌌 URL APOD: {response.url}")

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"❌ Error extrayendo APOD: {str(e)}")
            return None

    # ==========================================
    # Procesamiento Asteroides
    # ==========================================
    def procesar_asteroides(self, raw_data):
        registros = []

        try:
            objetos = raw_data.get("near_earth_objects", {})

            for fecha, asteroides in objetos.items():
                for ast in asteroides:

                    acercamiento = ast.get("close_approach_data", [{}])[0]

                    registros.append({
                        "id": ast.get("id"),
                        "nombre": ast.get("name"),
                        "magnitud_absoluta": ast.get("absolute_magnitude_h"),
                        "diametro_min_km": ast["estimated_diameter"]["kilometers"]["estimated_diameter_min"],
                        "diametro_max_km": ast["estimated_diameter"]["kilometers"]["estimated_diameter_max"],
                        "es_peligroso": ast.get("is_potentially_hazardous_asteroid"),
                        "fecha_aproximacion": fecha,
                        "velocidad_km_s": acercamiento.get("relative_velocity", {}).get("kilometers_per_second"),
                        "distancia_km": acercamiento.get("miss_distance", {}).get("kilometers"),
                        "fecha_extraccion": datetime.utcnow().isoformat()
                    })

            logger.info(f"📊 Asteroides procesados: {len(registros)}")
            return registros

        except Exception as e:
            logger.error(f"❌ Error procesando asteroides: {str(e)}")
            return []

    # ==========================================
    # Procesamiento APOD
    # ==========================================
    def procesar_apod(self, raw_data):
        try:
            return {
                "fecha": raw_data.get("date"),
                "titulo": raw_data.get("title"),
                "explicacion": raw_data.get("explanation"),
                "url_imagen": raw_data.get("url"),
                "tipo_media": raw_data.get("media_type"),
                "fecha_extraccion": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error procesando APOD: {str(e)}")
            return None

    # ==========================================
    # Ejecución ETL
    # ==========================================
    def ejecutar_extraccion(self):

        logger.info("🚀 Iniciando ETL NASA...")

        ast_raw = self.extraer_asteroides()
        apod_raw = self.extraer_apod()

        asteroides = self.procesar_asteroides(ast_raw) if ast_raw else []
        apod = self.procesar_apod(apod_raw) if apod_raw else None

        return asteroides, apod


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    extractor = NasaExtractor()
    asteroides, apod = extractor.ejecutar_extraccion()

    # Guardar asteroides
    with open("data/asteroides_raw.json", "w") as f:
        json.dump(asteroides, f, indent=2)

    df = pd.DataFrame(asteroides)
    df.to_csv("data/asteroides.csv", index=False)

    # Guardar APOD
    if apod:
        with open("data/apod.json", "w") as f:
            json.dump(apod, f, indent=2)

    logger.info("📁 Datos guardados correctamente")

    print("\n" + "="*60)
    print("RESUMEN NASA ETL")
    print("="*60)
    print(df.head())
    print("="*60)