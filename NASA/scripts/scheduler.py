#!/usr/bin/env python3

import schedule
import time
import logging
from extractor import NasaExtractor

# ==============================
# Configuración de logging
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ==============================
# Función que ejecuta el ETL
# ==============================
def ejecutar_etl_nasa():
    logger.info("🚀 Ejecutando ETL NASA programado...")

    try:
        extractor = NasaExtractor()
        asteroides, apod = extractor.ejecutar_extraccion()

        logger.info(f"Asteroides extraídos: {len(asteroides)}")

        if apod:
            logger.info("APOD extraído correctamente")

        logger.info("✅ ETL NASA finalizado correctamente\n")

    except Exception as e:
        logger.error(f"❌ Error en ETL NASA: {str(e)}\n")


# ==============================
# EJECUCIÓN INICIAL
# ==============================
ejecutar_etl_nasa()

# ==============================
# PROGRAMACIÓN
# ==============================

# 🔁 Cada 1 hora (recomendado)
# schedule.every(1).hours.do(ejecutar_etl_nasa)

# Si quieres pruebas rápidas:
schedule.every(30).seconds.do(ejecutar_etl_nasa)

logger.info("⏰ Scheduler NASA iniciado...")

while True:
    schedule.run_pending()
    time.sleep(1)