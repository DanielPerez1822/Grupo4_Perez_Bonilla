import schedule
import time
import logging
from scripts.extractor import WeatherstackExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def ejecutar_etl():
    logging.info("Iniciando ETL...")
    try:
        extractor = WeatherstackExtractor()
        extractor.ejecutar_extraccion()
        logging.info("ETL finalizado correctamente")
    except Exception as e:
        logging.error(f"Error en ETL: {e}")

# Ejecutar inmediatamente
ejecutar_etl()

# Ejecutar cada 10 segundos
schedule.every(10).seconds.do(ejecutar_etl)

logging.info("Scheduler iniciado (cada 10 segundos)...")

while True:
    schedule.run_pending()
    time.sleep(1)