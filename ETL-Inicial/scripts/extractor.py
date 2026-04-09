#!/usr/bin/env python3
import os
import time
import logging
from dotenv import load_dotenv
import requests

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class WeatherstackETL:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("WEATHERSTACK_BASE_URL")
        self.ciudades = [c.strip() for c in os.getenv("CIUDADES", "").split(",") if c.strip()]

        if not self.api_key:
            raise ValueError("API_KEY no está configurada en el archivo .env")

        if not self.base_url:
            raise ValueError("WEATHERSTACK_BASE_URL no está configurada en el archivo .env")

        if not self.ciudades:
            raise ValueError("CIUDADES no está configurado en el archivo .env")

        self.db = SessionLocal()
        self.tiempo_inicio = time.time()

        self.registros_extraidos = 0
        self.registros_guardados = 0
        self.registros_fallidos = 0

    def extraer_clima(self, ciudad):
        url = f"{self.base_url}/current"
        params = {
            "access_key": self.api_key,
            "query": ciudad
        }

        try:
            response = requests.get(url, params=params, timeout=10)

            # Intentar leer JSON aunque venga error HTTP
            try:
                data = response.json()
            except Exception:
                data = {}

            if response.status_code == 429:
                logger.error(f"⚠️ Límite de solicitudes excedido para {ciudad}")
                self.registros_fallidos += 1
                return None

            if response.status_code == 400:
                logger.error(f"❌ Bad Request para {ciudad}: {data}")
                self.registros_fallidos += 1
                return None

            response.raise_for_status()

            if "error" in data:
                logger.error(f"❌ Error de API para {ciudad}: {data['error']}")
                self.registros_fallidos += 1
                return None

            logger.info(f"✅ Datos extraídos para {ciudad}")
            self.registros_extraidos += 1
            return data

        except requests.exceptions.Timeout:
            logger.error(f"⏱ Timeout al consultar {ciudad}")
            self.registros_fallidos += 1
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error HTTP para {ciudad}: {e}")
            self.registros_fallidos += 1
            return None

        except Exception as e:
            logger.error(f"❌ Error inesperado para {ciudad}: {e}")
            self.registros_fallidos += 1
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
            "latitud": float(location["lat"]) if location.get("lat") is not None else None,
            "longitud": float(location["lon"]) if location.get("lon") is not None else None,
            "temperatura": current.get("temperature"),
            "sensacion_termica": current.get("feelslike"),
            "humedad": current.get("humidity"),
            "velocidad_viento": current.get("wind_speed"),
            "descripcion": descripcion,
            "codigo_tiempo": current.get("weather_code")
        }

    def guardar(self, datos):
        try:
            ciudad = self.db.query(Ciudad).filter_by(
                nombre=datos["ciudad"]
            ).first()

            if not ciudad:
                ciudad = Ciudad(
                    nombre=datos["ciudad"],
                    pais=datos["pais"],
                    latitud=datos["latitud"],
                    longitud=datos["longitud"]
                )
                self.db.add(ciudad)
                self.db.flush()

            registro = RegistroClima(
                ciudad_id=ciudad.id,
                temperatura=datos["temperatura"],
                sensacion_termica=datos["sensacion_termica"],
                humedad=datos["humedad"],
                velocidad_viento=datos["velocidad_viento"],
                descripcion=datos["descripcion"],
                codigo_tiempo=datos["codigo_tiempo"]
            )

            self.db.add(registro)
            self.db.commit()

            self.registros_guardados += 1
            logger.info(f"💾 Registro guardado para {datos['ciudad']}")

        except Exception as e:
            self.db.rollback()
            self.registros_fallidos += 1
            logger.error(f"❌ Error guardando datos para {datos.get('ciudad')}: {e}")

    def guardar_metricas(self):
        try:
            tiempo = time.time() - self.tiempo_inicio
            estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"

            metricas = MetricasETL(
                registros_extraidos=self.registros_extraidos,
                registros_guardados=self.registros_guardados,
                registros_fallidos=self.registros_fallidos,
                tiempo_ejecucion_segundos=tiempo,
                estado=estado,
                mensaje=(
                    f"Extraídos: {self.registros_extraidos}, "
                    f"Guardados: {self.registros_guardados}, "
                    f"Fallidos: {self.registros_fallidos}"
                )
            )

            self.db.add(metricas)
            self.db.commit()
            logger.info("📊 Métricas guardadas correctamente")

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error guardando métricas: {e}")

    def ejecutar(self):
        try:
            logger.info(f"🚀 Iniciando ETL para {len(self.ciudades)} ciudades...")

            for ciudad in self.ciudades:
                data = self.extraer_clima(ciudad)

                if data:
                    datos = self.procesar(data)
                    self.guardar(datos)

                time.sleep(2)

            self.guardar_metricas()

        finally:
            self.db.close()


if __name__ == "__main__":
    etl = WeatherstackETL()
    etl.ejecutar()