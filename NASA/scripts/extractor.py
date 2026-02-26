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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================
# Clase Extractor NASA
# ==============================
class NasaExtractor:

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("NASA_BASE_URL")

        if not self.api_key:
            raise ValueError("API_KEY no configurada en .env")

        # ==============================
        # Fechas dinámicas
        # ==============================
        hoy = datetime.utcnow().date()

        self.start_date = os.getenv("START_DATE") or hoy.strftime("%Y-%m-%d")
        self.end_date = os.getenv("END_DATE") or (hoy + timedelta(days=7)).strftime("%Y-%m-%d")

        logger.info("Extractor NASA inicializado correctamente")
        logger.info(f"Rango de fechas: {self.start_date} → {self.end_date}")

    # ==========================================
    # 1️⃣ Extracción de Asteroides (NEO)
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
            response.raise_for_status()

            data = response.json()
            logger.info("✅ Datos de asteroides extraídos correctamente")
            return data

        except Exception as e:
            logger.error(f"❌ Error extrayendo asteroides: {str(e)}")
            return None

    # ==========================================
    # 2️⃣ Imagen Astronómica del Día (APOD)
    # ==========================================
    def extraer_apod(self):
        try:
            url = f"{self.base_url}/planetary/apod"
            params = {
                "api_key": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info("✅ APOD extraído correctamente")
            return data

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
                for asteroide in asteroides:
                    registros.append({
                        "id": asteroide.get("id"),
                        "nombre": asteroide.get("name"),
                        "magnitud_absoluta": asteroide.get("absolute_magnitude_h"),
                        "diametro_min_km": asteroide["estimated_diameter"]["kilometers"]["estimated_diameter_min"],
                        "diametro_max_km": asteroide["estimated_diameter"]["kilometers"]["estimated_diameter_max"],
                        "es_peligroso": asteroide.get("is_potentially_hazardous_asteroid"),
                        "fecha_aproximacion": fecha,
                        "velocidad_km_s": asteroide["close_approach_data"][0]["relative_velocity"]["kilometers_per_second"],
                        "distancia_km": asteroide["close_approach_data"][0]["miss_distance"]["kilometers"],
                        "fecha_extraccion": datetime.now().isoformat()
                    })

            return registros

        except Exception as e:
            logger.error(f"Error procesando asteroides: {str(e)}")
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
                "fecha_extraccion": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error procesando APOD: {str(e)}")
            return None

    # ==========================================
    # Ejecución Principal ETL
    # ==========================================
    def ejecutar_extraccion(self):

        logger.info("🚀 Iniciando proceso ETL NASA")

        asteroides_raw = self.extraer_asteroides()
        apod_raw = self.extraer_apod()

        asteroides = self.procesar_asteroides(asteroides_raw) if asteroides_raw else []
        apod = self.procesar_apod(apod_raw) if apod_raw else None

        return asteroides, apod


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    try:
        extractor = NasaExtractor()
        asteroides, apod = extractor.ejecutar_extraccion()

        # Guardar asteroides
        with open("data/asteroides_raw.json", "w") as f:
            json.dump(asteroides, f, indent=2)

        df_asteroides = pd.DataFrame(asteroides)
        df_asteroides.to_csv("data/asteroides.csv", index=False)

        # Guardar APOD
        if apod:
            with open("data/apod.json", "w") as f:
                json.dump(apod, f, indent=2)

        logger.info("📁 Datos guardados correctamente")

        print("\n" + "="*60)
        print("RESUMEN DE EXTRACCIÓN NASA")
        print("="*60)
        print(df_asteroides.head())
        print("="*60)

    except Exception as e:
        logger.error(f"Error general en ETL: {str(e)}")