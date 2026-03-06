#!/usr/bin/env python3

import schedule
import time
import logging
from extractor import extraer_datos  # función simple

# ==============================
# Logging
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ==============================
# Job ETL
# ==============================
def ejecutar_etl_nasa():
    logger.info("🚀 Ejecutando ETL NASA programado...")

    try:
        extraer_datos()  # guarda en PostgreSQL
        logger.info("✅ ETL NASA finalizado correctamente\n")

    except Exception as e:
        logger.error(f"❌ Error en ETL NASA: {str(e)}\n")


# ==============================
# EJECUCIÓN INICIAL
# ==============================

if __name__ == "__main__":

    ejecutar_etl_nasa()  # ejecuta una vez al iniciar

    # 🔁 Producción
    schedule.every(1).hours.do(ejecutar_etl_nasa)

    # 🧪 Pruebas rápidas
    # schedule.every(30).seconds.do(ejecutar_etl_nasa)

    logger.info("⏰ Scheduler NASA iniciado...")

    while True:
        schedule.run_pending()
        time.sleep(1)