#!/usr/bin/env python3
"""
extractor_api.py - Fase Extract del pipeline ETL
Extrae datos reales desde la API de Weatherstack y los guarda en data/clima.csv
"""

import os
import time
import logging
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeatherstackExtractorAPI:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("WEATHERSTACK_BASE_URL")
        self.ciudades = [c.strip() for c in os.getenv("CIUDADES", "").split(",") if c.strip()]
        self.registros = []

        if not self.api_key:
            raise ValueError("API_KEY no está configurada en el archivo .env")

        if not self.base_url:
            raise ValueError("WEATHERSTACK_BASE_URL no está configurada en el archivo .env")

        if not self.ciudades:
            raise ValueError("CIUDADES no está configurado en el archivo .env")

    def extraer_clima(self, ciudad):
        url = f"{self.base_url}/current"
        params = {
            "access_key": self.api_key,
            "query": ciudad
        }

        try:
            response = requests.get(url, params=params, timeout=15)

            try:
                data = response.json()
            except Exception:
                data = {}

            if response.status_code == 429:
                logger.error(f"⚠️ Límite de solicitudes excedido para {ciudad}")
                return None

            if response.status_code == 400:
                logger.error(f"❌ Bad Request para {ciudad}: {data}")
                return None

            response.raise_for_status()

            if "error" in data:
                logger.error(f"❌ Error de API para {ciudad}: {data['error']}")
                return None

            logger.info(f"✅ Datos extraídos para {ciudad}")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"⏱ Timeout al consultar {ciudad}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error HTTP para {ciudad}: {e}")
            return None

        except Exception as e:
            logger.error(f"❌ Error inesperado para {ciudad}: {e}")
            return None

    def procesar(self, data):
        location = data.get("location", {})
        current = data.get("current", {})

        descripcion = "N/A"
        weather_descriptions = current.get("weather_descriptions")
        if isinstance(weather_descriptions, list) and weather_descriptions:
            descripcion = weather_descriptions[0]

        return {
            "ciudad": location.get("name"),
            "pais": location.get("country"),
            "region": location.get("region"),
            "latitud": location.get("lat"),
            "longitud": location.get("lon"),
            "temperatura": current.get("temperature"),
            "sensacion_termica": current.get("feelslike"),
            "humedad": current.get("humidity"),
            "velocidad_viento": current.get("wind_speed"),
            "direccion_viento": current.get("wind_dir"),
            "presion": current.get("pressure"),
            "visibilidad": current.get("visibility"),
            "indice_uv": current.get("uv_index"),
            "descripcion": descripcion,
            "codigo_tiempo": current.get("weather_code"),
            "hora_local": location.get("localtime"),
            "timestamp": datetime.utcnow().isoformat()
        }

    def guardar_csv(self, output_csv="data/clima.csv"):
        if not self.registros:
            logger.warning("⚠️ No hay datos para guardar")
            return False

        df = pd.DataFrame(self.registros)
        df.to_csv(output_csv, index=False)
        logger.info(f"💾 Datos guardados en {output_csv} ({len(df)} registros)")
        return True

    def ejecutar(self):
        logger.info(f"🚀 Iniciando extracción para {len(self.ciudades)} ciudades...")

        for ciudad in self.ciudades:
            data = self.extraer_clima(ciudad)

            if data:
                self.registros.append(self.procesar(data))

            time.sleep(1)

        return self.guardar_csv()


if __name__ == "__main__":
    extractor = WeatherstackExtractorAPI()
    exito = extractor.ejecutar()
    raise SystemExit(0 if exito else 1)