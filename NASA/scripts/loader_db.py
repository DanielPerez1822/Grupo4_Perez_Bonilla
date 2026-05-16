#!/usr/bin/env python3
"""
loader_db.py - Fase Load del pipeline ETL NASA
Lee data/asteroides_transformado.csv y lo carga a PostgreSQL/Supabase.
"""

import sys
sys.path.insert(0, '.')

import os
import time
import logging
from datetime import datetime, UTC

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

from scripts.database import SessionLocal
from scripts.models import Asteroide, NeoWsRegistro, MetricasETL

load_dotenv()

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NasaLoaderDB:
    def __init__(self, input_csv="data/asteroides_transformado.csv"):
        self.input_csv = input_csv
        self.tiempo_inicio = time.time()
        self.registros_insertados = 0
        self.errores = 0

    def cargar_csv(self):
        if not os.path.exists(self.input_csv):
            raise FileNotFoundError(
                f"No se encontró {self.input_csv}. "
                "Ejecuta primero scripts/transformador.py"
            )

        df = pd.read_csv(self.input_csv)
        logger.info(f"📂 {len(df)} registros leídos desde {self.input_csv}")
        return df

    def guardar_metricas(self, db, estado):
        try:
            tiempo = round(time.time() - self.tiempo_inicio, 2)

            metricas = MetricasETL(
                registros_insertados=self.registros_insertados,
                errores=self.errores,
                tiempo_ejecucion=tiempo,
                estado=estado
            )
            db.add(metricas)
            db.commit()
            logger.info(f"📈 Métricas guardadas — estado: {estado}")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando métricas: {e}")

    def ejecutar(self):
        df = self.cargar_csv()

        with SessionLocal() as db:
            try:
                payload_asteroides = []
                payload_neows = []

                for _, fila in df.iterrows():
                    try:
                        nasa_id = str(fila.get("nasa_id", "")).strip()
                        if not nasa_id:
                            self.errores += 1
                            continue

                        fecha_aproximacion = pd.to_datetime(
                            fila.get("fecha_aproximacion")
                        ).date() if pd.notna(fila.get("fecha_aproximacion")) else None

                        fecha_extraccion = pd.to_datetime(
                            fila.get("fecha_extraccion")
                        ).to_pydatetime() if pd.notna(fila.get("fecha_extraccion")) else datetime.now(UTC)

                        registro = {
                            "nasa_id": nasa_id,
                            "nombre": str(fila.get("nombre", "N/A")),
                            "magnitud_absoluta": float(fila.get("magnitud_absoluta", 0)),
                            "diametro_min_km": float(fila.get("diametro_min_km", 0)),
                            "diametro_max_km": float(fila.get("diametro_max_km", 0)),
                            "es_peligroso": bool(fila.get("es_peligroso", False)),
                            "fecha_aproximacion": fecha_aproximacion,
                            "velocidad_km_s": float(fila.get("velocidad_km_s", 0)),
                            "distancia_km": float(fila.get("distancia_km", 0)),
                            "fecha_extraccion": fecha_extraccion,
                        }

                        payload_asteroides.append(registro.copy())
                        payload_neows.append(registro.copy())

                    except Exception as e:
                        logger.warning(f"⚠️ Fila omitida: {e}")
                        self.errores += 1

                if payload_asteroides:
                    stmt_asteroides = insert(Asteroide).values(payload_asteroides)
                    stmt_asteroides = stmt_asteroides.on_conflict_do_nothing(
                        index_elements=["nasa_id", "fecha_aproximacion"]
                    )
                    result_ast = db.execute(stmt_asteroides)

                    stmt_neows = insert(NeoWsRegistro).values(payload_neows)
                    stmt_neows = stmt_neows.on_conflict_do_nothing(
                        index_elements=["nasa_id", "fecha_aproximacion"]
                    )
                    db.execute(stmt_neows)

                    db.commit()

                    self.registros_insertados = result_ast.rowcount if result_ast.rowcount and result_ast.rowcount > 0 else 0
                    logger.info(f"✅ Bulk insert completado: {self.registros_insertados} registros en asteroides")

                estado = "SUCCESS" if self.errores == 0 else "PARTIAL"
                self.guardar_metricas(db, estado)

                logger.info(
                    f"✅ LOAD NASA completado — Insertados: {self.registros_insertados} | "
                    f"Errores: {self.errores}"
                )
                return True

            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error en bulk insert NASA: {e}")
                self.errores += len(df)
                self.guardar_metricas(db, "FAILED")
                return False

a
if __name__ == "__main__":
    loader = NasaLoaderDB()
    exito = loader.ejecutar()
    raise SystemExit(0 if exito else 1)