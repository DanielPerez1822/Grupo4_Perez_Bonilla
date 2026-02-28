#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
import time
from datetime import datetime
from dotenv import load_dotenv
import logging

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

# Cargar variables de entorno
load_dotenv()

# Crear carpetas necesarias
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WeatherstackExtractor:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.base_url = os.getenv('WEATHERSTACK_BASE_URL')
        self.ciudades = os.getenv('CIUDADES').split(',')

        if not self.api_key:
            raise ValueError("API_KEY no configurada en .env")

        if not self.base_url:
            raise ValueError("WEATHERSTACK_BASE_URL no configurada en .env")

    def extraer_clima(self, ciudad):
        try:
            url = f"{self.base_url}/current"
            params = {
                'access_key': self.api_key,
                'query': ciudad.strip()
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"❌ Error en API para {ciudad}: {data['error']['info']}")
                return None

            logger.info(f"✅ Datos extraídos para {ciudad}")
            return data

        except Exception as e:
            logger.error(f"❌ Error extrayendo datos para {ciudad}: {str(e)}")
            return None

    def procesar_respuesta(self, response_data):
        try:
            current = response_data.get('current', {})
            location = response_data.get('location', {})

            return {
                'ciudad': location.get('name'),
                'pais': location.get('country'),
                'latitud': location.get('lat'),
                'longitud': location.get('lon'),
                'temperatura': current.get('temperature'),
                'sensacion_termica': current.get('feelslike'),
                'humedad': current.get('humidity'),
                'velocidad_viento': current.get('wind_speed'),
                'descripcion': current.get('weather_descriptions', ['N/A'])[0],
                'fecha_extraccion': datetime.now(),
                'codigo_tiempo': current.get('weather_code')
            }

        except Exception as e:
            logger.error(f"❌ Error procesando respuesta: {str(e)}")
            return None

    def guardar_en_bd(self, datos):
        db = SessionLocal()
        try:
            ciudad_db = db.query(Ciudad).filter_by(
                nombre=datos['ciudad']
            ).first()

            if not ciudad_db:
                ciudad_db = Ciudad(
                    nombre=datos['ciudad'],
                    pais=datos['pais']
                )
                db.add(ciudad_db)
                db.commit()
                db.refresh(ciudad_db)
                logger.info(f"🏙 Ciudad creada: {datos['ciudad']}")

            nuevo_registro = RegistroClima(
                ciudad_id=ciudad_db.id,
                temperatura=datos['temperatura'],
                sensacion_termica=datos['sensacion_termica'],
                humedad=datos['humedad'],
                velocidad_viento=datos['velocidad_viento'],
                descripcion=datos['descripcion'],
                fecha_extraccion=datos['fecha_extraccion']
            )

            db.add(nuevo_registro)
            db.commit()

            logger.info(f"💾 Registro guardado para {datos['ciudad']}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando en BD: {str(e)}")
            return False

        finally:
            db.close()

    def ejecutar_extraccion(self):

        inicio = time.time()

        ciudades_procesadas = 0
        registros_insertados = 0
        errores = 0

        datos_extraidos = []

        logger.info(f"🚀 Iniciando extracción para {len(self.ciudades)} ciudades...")

        for ciudad in self.ciudades:

            ciudades_procesadas += 1

            response = self.extraer_clima(ciudad)

            if response:
                datos_procesados = self.procesar_respuesta(response)

                if datos_procesados:
                    datos_extraidos.append(datos_procesados)

                    if self.guardar_en_bd(datos_procesados):
                        registros_insertados += 1
                    else:
                        errores += 1
                else:
                    errores += 1
            else:
                errores += 1

        tiempo_total = round(time.time() - inicio, 2)

        # Determinar estado
        if errores == 0:
            estado = "SUCCESS"
        elif registros_insertados > 0:
            estado = "PARTIAL_SUCCESS"
        else:
            estado = "FAILED"

        # Guardar métricas
        db = SessionLocal()
        try:
            metricas = MetricasETL(
                ciudades_procesadas=ciudades_procesadas,
                registros_insertados=registros_insertados,
                errores=errores,
                tiempo_ejecucion=tiempo_total,
                estado=estado
            )

            db.add(metricas)
            db.commit()

            logger.info("📊 Métricas ETL guardadas correctamente")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando métricas: {str(e)}")

        finally:
            db.close()

        logger.info(f"⏱ Tiempo total ejecución: {tiempo_total} segundos")

        return datos_extraidos


if __name__ == "__main__":
    try:
        extractor = WeatherstackExtractor()
        datos = extractor.ejecutar_extraccion()

        with open('data/clima_raw.json', 'w') as f:
            json.dump(
                [dict(d, fecha_extraccion=d['fecha_extraccion'].isoformat()) for d in datos],
                f,
                indent=2
            )

        df = pd.DataFrame(datos)
        df.to_csv('data/clima.csv', index=False)

        print("\n" + "="*50)
        print("RESUMEN DE EXTRACCIÓN")
        print("="*50)
        print(df.to_string())
        print("="*50)

    except Exception as e:
        logger.error(f"❌ Error general en extracción: {str(e)}")