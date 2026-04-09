#!/usr/bin/env python3
"""
loader_db.py - Fase Load del pipeline ETL
Lee data/clima_transformado.csv y lo carga a PostgreSQL/Supabase en bloque.
"""

import sys
sys.path.insert(0, '.')

import os
import time
import logging
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

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


class WeatherstackLoaderDB:
    def __init__(self, input_csv="data/clima_transformado.csv"):
        self.input_csv = input_csv
        self.tiempo_inicio = time.time()
        self.registros_extraidos = 0
        self.registros_guardados = 0
        self.registros_fallidos = 0

    def cargar_csv(self):
        if not os.path.exists(self.input_csv):
            raise FileNotFoundError(
                f"No se encontró {self.input_csv}. "
                "Ejecuta primero scripts/transformador.py"
            )

        df = pd.read_csv(self.input_csv)
        self.registros_extraidos = len(df)
        logger.info(f"📂 {self.registros_extraidos} registros leídos desde {self.input_csv}")
        return df

    def guardar_metricas(self, db, estado):
        try:
            tiempo = round(time.time() - self.tiempo_inicio, 2)

            metricas = MetricasETL(
                registros_extraidos=self.registros_extraidos,
                registros_guardados=self.registros_guardados,
                registros_fallidos=self.registros_fallidos,
                tiempo_ejecucion_segundos=tiempo,
                estado=estado,
                mensaje=(
                    f"{self.registros_guardados} registros guardados de "
                    f"{self.registros_extraidos} en {tiempo}s"
                )
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
                # 1. Insertar ciudades únicas
                ciudades_unicas = df["ciudad"].dropna().astype(str).str.strip().unique()

                ciudades_payload = []
                for nombre in ciudades_unicas:
                    fila_ciudad = df[df["ciudad"].astype(str).str.strip() == nombre].iloc[0]

                    ciudades_payload.append({
                        "nombre": nombre,
                        "pais": str(fila_ciudad.get("pais", "N/A")),
                        "latitud": float(fila_ciudad["latitud"]) if pd.notna(fila_ciudad.get("latitud")) else None,
                        "longitud": float(fila_ciudad["longitud"]) if pd.notna(fila_ciudad.get("longitud")) else None,
                    })

                if ciudades_payload:
                    stmt_ciudades = insert(Ciudad).values(ciudades_payload)
                    stmt_ciudades = stmt_ciudades.on_conflict_do_nothing(
                        index_elements=["nombre"]
                    )
                    db.execute(stmt_ciudades)
                    db.commit()

                # 2. Mapear ciudades a ids
                rows = db.execute(
                    select(Ciudad.id, Ciudad.nombre).where(Ciudad.nombre.in_(list(ciudades_unicas)))
                ).all()
                ciudad_map = {nombre: id_ for id_, nombre in rows}

                # 3. Construir carga bulk de registros
                registros_payload = []

                for _, fila in df.iterrows():
                    try:
                        nombre_ciudad = str(fila.get("ciudad", "")).strip()
                        ciudad_id = ciudad_map.get(nombre_ciudad)

                        if not ciudad_id:
                            self.registros_fallidos += 1
                            continue

                        fecha_extraccion = fila.get("hora_local")
                        if pd.notna(fecha_extraccion):
                            fecha_extraccion = pd.to_datetime(fecha_extraccion).to_pydatetime()
                        else:
                            fecha_extraccion = datetime.utcnow()

                        registros_payload.append({
                            "ciudad_id": ciudad_id,
                            "temperatura": float(fila.get("temperatura", 0)),
                            "sensacion_termica": float(fila.get("sensacion_termica", fila.get("temperatura", 0))),
                            "humedad": float(fila.get("humedad", 0)),
                            "velocidad_viento": float(fila.get("velocidad_viento", 0)),
                            "descripcion": str(fila.get("descripcion", "N/A"))[:255],
                            "codigo_tiempo": int(fila["codigo_tiempo"]) if pd.notna(fila.get("codigo_tiempo")) else None,
                            "fecha_extraccion": fecha_extraccion,
                        })

                    except Exception as e:
                        logger.warning(f"⚠️ Fila omitida: {e}")
                        self.registros_fallidos += 1

                # 4. Insertar en bloque
                if registros_payload:
                    stmt_registros = insert(RegistroClima).values(registros_payload)
                    stmt_registros = stmt_registros.on_conflict_do_nothing(
                        index_elements=["ciudad_id", "fecha_extraccion"]
                    )

                    result = db.execute(stmt_registros)
                    db.commit()

                    self.registros_guardados = result.rowcount if result.rowcount and result.rowcount > 0 else 0
                    duplicados = len(registros_payload) - self.registros_guardados
                    self.registros_fallidos += max(0, duplicados)

                    logger.info(f"✅ Bulk insert completado: {self.registros_guardados} registros")
                    if duplicados:
                        logger.info(f"⚠️ Registros duplicados omitidos: {duplicados}")

                estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"
                self.guardar_metricas(db, estado)

                logger.info(
                    f"✅ LOAD completado — Guardados: {self.registros_guardados} | "
                    f"Fallidos: {self.registros_fallidos}"
                )
                return True

            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error en bulk insert: {e}")
                self.registros_fallidos += self.registros_extraidos
                self.guardar_metricas(db, "FAILED")
                return False


if __name__ == "__main__":
    loader = WeatherstackLoaderDB()
    exito = loader.ejecutar()
    raise SystemExit(0 if exito else 1)