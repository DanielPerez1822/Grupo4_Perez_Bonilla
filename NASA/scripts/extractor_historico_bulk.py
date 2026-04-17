#!/usr/bin/env python3
"""
extractor_historico_bulk.py

Extrae datos históricos de la API NASA NeoWs por bloques de hasta 7 días
y los carga en bulk a PostgreSQL/Supabase.

Requiere en .env:
- NASA_API_KEY
- NASA_BASE_URL
- DATABASE_URL

Opcionales en .env:
- START_DATE=2025-01-01
- END_DATE=2025-03-31
- CHUNK_DAYS=7
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

from scripts.database import SessionLocal
from scripts.models import Asteroide, NeoWsRegistro, MetricasETL

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/etl_historico.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NasaHistoricalBulkETL:
    def __init__(self) -> None:
        self.api_key = os.getenv("NASA_API_KEY")
        self.base_url = os.getenv("NASA_BASE_URL", "https://api.nasa.gov")
        self.start_date = os.getenv("START_DATE")
        self.end_date = os.getenv("END_DATE")
        self.chunk_days = int(os.getenv("CHUNK_DAYS", "7"))

        if not self.api_key:
            raise ValueError("❌ NASA_API_KEY no configurada en .env")

        if not self.start_date or not self.end_date:
            raise ValueError("❌ Debes definir START_DATE y END_DATE en .env")

        self.start_dt = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        self.end_dt = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        if self.start_dt > self.end_dt:
            raise ValueError("❌ START_DATE no puede ser mayor que END_DATE")

        if self.chunk_days < 1:
            raise ValueError("❌ CHUNK_DAYS debe ser >= 1")

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "nasa-historical-etl/1.0"})

        self.tiempo_inicio = time.time()
        self.registros_insertados = 0
        self.errores = 0
        self.registros_extraidos = 0

        logger.info("✅ ETL histórico NASA inicializado")
        logger.info(f"📅 Rango histórico: {self.start_date} → {self.end_date}")
        logger.info(f"🧩 Tamaño de bloque: {self.chunk_days} días")

    def _date_ranges(self):
        current = self.start_dt
        while current <= self.end_dt:
            chunk_end = min(current + timedelta(days=self.chunk_days - 1), self.end_dt)
            yield current, chunk_end
            current = chunk_end + timedelta(days=1)

    def extraer_bloque(self, start_date: str, end_date: str) -> Dict[str, Any] | None:
        url = f"{self.base_url}/neo/rest/v1/feed"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            logger.info(f"🌍 GET {response.url}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.errores += 1
            logger.error(f"❌ Error extrayendo bloque {start_date} → {end_date}: {e}")
            return None

    def procesar_asteroides(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        registros: List[Dict[str, Any]] = []

        try:
            objetos = raw_data.get("near_earth_objects", {})
            for fecha, asteroides in objetos.items():
                for ast in asteroides:
                    acercamiento = ast.get("close_approach_data", [{}])[0]

                    registros.append({
                        "nasa_id": str(ast.get("id", "")).strip(),
                        "nombre": ast.get("name"),
                        "magnitud_absoluta": ast.get("absolute_magnitude_h"),
                        "diametro_min_km": ast.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min"),
                        "diametro_max_km": ast.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max"),
                        "es_peligroso": ast.get("is_potentially_hazardous_asteroid"),
                        "fecha_aproximacion": fecha,
                        "velocidad_km_s": acercamiento.get("relative_velocity", {}).get("kilometers_per_second"),
                        "distancia_km": acercamiento.get("miss_distance", {}).get("kilometers"),
                        "fecha_extraccion": datetime.now(UTC).isoformat()
                    })

            return registros
        except Exception as e:
            self.errores += 1
            logger.error(f"❌ Error procesando bloque: {e}")
            return []

    def extraer_historico(self) -> List[Dict[str, Any]]:
        todos_los_registros: List[Dict[str, Any]] = []

        for start_dt, end_dt in self._date_ranges():
            start_s = start_dt.strftime("%Y-%m-%d")
            end_s = end_dt.strftime("%Y-%m-%d")

            logger.info(f"🚀 Extrayendo bloque {start_s} → {end_s}")
            raw_data = self.extraer_bloque(start_s, end_s)
            if not raw_data:
                continue

            registros = self.procesar_asteroides(raw_data)
            self.registros_extraidos += len(registros)
            todos_los_registros.extend(registros)

            logger.info(f"📦 Registros del bloque: {len(registros)}")

            # Pausa breve para ser amable con la API
            time.sleep(0.25)

        logger.info(f"📊 Total registros extraídos: {self.registros_extraidos}")
        return todos_los_registros

    def transformar(self, registros: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(registros)

        if df.empty:
            return df

        # Tipos
        numeric_cols = [
            "magnitud_absoluta",
            "diametro_min_km",
            "diametro_max_km",
            "velocidad_km_s",
            "distancia_km"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["fecha_aproximacion"] = pd.to_datetime(df["fecha_aproximacion"], errors="coerce").dt.date
        df["fecha_extraccion"] = pd.to_datetime(df["fecha_extraccion"], errors="coerce").dt.tz_localize(None)
        df["es_peligroso"] = df["es_peligroso"].astype(bool)

        # Limpieza
        df.dropna(subset=["nasa_id", "fecha_aproximacion"], inplace=True)
        df.drop_duplicates(subset=["nasa_id", "fecha_aproximacion"], inplace=True)

        # Enriquecimiento opcional
        df["diametro_promedio_km"] = (df["diametro_min_km"] + df["diametro_max_km"]) / 2
        df["fecha_procesamiento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"🧹 Registros listos para cargar: {len(df)}")
        return df

    def guardar_archivos(self, df: pd.DataFrame) -> None:
        if df.empty:
            logger.warning("⚠️ No hay datos para guardar en archivos")
            return

        raw_path = "data/asteroides_historico_raw.json"
        csv_path = "data/asteroides_historico.csv"
        xlsx_path = "data/asteroides_historico.xlsx"

        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, indent=2, ensure_ascii=False, default=str)

        df.to_csv(csv_path, index=False)
        df.to_excel(xlsx_path, index=False, sheet_name="AsteroidesHistorico")

        logger.info(f"💾 JSON guardado en {raw_path}")
        logger.info(f"💾 CSV guardado en {csv_path}")
        logger.info(f"💾 XLSX guardado en {xlsx_path}")

    def guardar_metricas(self, db, estado: str) -> None:
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

    def bulk_load(self, df: pd.DataFrame) -> bool:
        if df.empty:
            logger.warning("⚠️ DataFrame vacío, no se hará carga")
            return False

        with SessionLocal() as db:
            try:
                payload = df[[
                    "nasa_id",
                    "nombre",
                    "magnitud_absoluta",
                    "diametro_min_km",
                    "diametro_max_km",
                    "es_peligroso",
                    "fecha_aproximacion",
                    "velocidad_km_s",
                    "distancia_km",
                    "fecha_extraccion",
                ]].to_dict(orient="records")

                stmt_asteroides = insert(Asteroide).values(payload)
                stmt_asteroides = stmt_asteroides.on_conflict_do_nothing(
                    index_elements=["nasa_id", "fecha_aproximacion"]
                )
                result_ast = db.execute(stmt_asteroides)

                stmt_neows = insert(NeoWsRegistro).values(payload)
                stmt_neows = stmt_neows.on_conflict_do_nothing(
                    index_elements=["nasa_id", "fecha_aproximacion"]
                )
                db.execute(stmt_neows)

                db.commit()

                self.registros_insertados = (
                    result_ast.rowcount if result_ast.rowcount and result_ast.rowcount > 0 else 0
                )

                logger.info(f"✅ Bulk insert completado: {self.registros_insertados} registros nuevos")
                self.guardar_metricas(db, "SUCCESS" if self.errores == 0 else "PARTIAL")
                return True

            except Exception as e:
                db.rollback()
                self.errores += len(df)
                logger.error(f"❌ Error en bulk insert histórico: {e}")
                self.guardar_metricas(db, "FAILED")
                return False

    def run(self) -> bool:
        registros = self.extraer_historico()
        df = self.transformar(registros)
        self.guardar_archivos(df)
        return self.bulk_load(df)


if __name__ == "__main__":
    etl = NasaHistoricalBulkETL()
    ok = etl.run()
    raise SystemExit(0 if ok else 1)