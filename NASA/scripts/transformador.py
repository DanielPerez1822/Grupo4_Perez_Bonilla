#!/usr/bin/env python3
"""
transformador.py - Fase Transform del pipeline ETL NASA
Limpia, normaliza y enriquece los datos extraídos de la API NeoWs.
"""

import pandas as pd
import os
import logging
from datetime import datetime

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


class NasaTransformador:
    def __init__(self, input_csv="data/asteroides.csv"):
        self.input_csv = input_csv
        self.df = None

    def cargar_datos(self):
        if not os.path.exists(self.input_csv):
            raise FileNotFoundError(
                f"Archivo {self.input_csv} no encontrado. "
                "Ejecuta primero scripts/extractor.py"
            )

        self.df = pd.read_csv(self.input_csv)
        logger.info(f"📂 Datos cargados: {len(self.df)} registros desde {self.input_csv}")
        return self

    def limpiar_datos(self):
        filas_antes = len(self.df)

        # Evitar duplicados por nasa_id + fecha_aproximacion
        self.df.drop_duplicates(subset=["nasa_id", "fecha_aproximacion"], inplace=True)

        self.df.fillna({
            "nombre": "N/A",
            "magnitud_absoluta": 0,
            "diametro_min_km": 0,
            "diametro_max_km": 0,
            "es_peligroso": False,
            "velocidad_km_s": 0,
            "distancia_km": 0
        }, inplace=True)

        filas_despues = len(self.df)
        logger.info(
            f"🧹 Limpieza: {filas_antes - filas_despues} duplicados eliminados, "
            f"{filas_despues} registros restantes"
        )
        return self

    def normalizar_tipos(self):
        cols_numericas = [
            "magnitud_absoluta",
            "diametro_min_km",
            "diametro_max_km",
            "velocidad_km_s",
            "distancia_km"
        ]

        for col in cols_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        if "fecha_aproximacion" in self.df.columns:
            self.df["fecha_aproximacion"] = pd.to_datetime(
                self.df["fecha_aproximacion"], errors="coerce"
            ).dt.date

        if "fecha_extraccion" in self.df.columns:
            self.df["fecha_extraccion"] = pd.to_datetime(
                self.df["fecha_extraccion"], errors="coerce"
            ).dt.tz_localize(None)

        self.df["es_peligroso"] = self.df["es_peligroso"].astype(bool)

        logger.info("🔧 Tipos de datos normalizados")
        return self

    def enriquecer_datos(self):
        self.df["diametro_promedio_km"] = (
            self.df["diametro_min_km"] + self.df["diametro_max_km"]
        ) / 2

        def clasificar_tamano(d):
            if pd.isna(d):
                return "N/A"
            if d < 0.05:
                return "Pequeño"
            elif d < 0.25:
                return "Mediano"
            return "Grande"

        self.df["categoria_tamano"] = self.df["diametro_promedio_km"].apply(clasificar_tamano)
        self.df["fecha_procesamiento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info("✨ Datos enriquecidos con columnas calculadas")
        return self

    def guardar_datos(self, output_csv="data/asteroides_transformado.csv"):
        self.df.to_csv(output_csv, index=False)
        logger.info(f"💾 Datos transformados guardados en {output_csv}")

        output_xlsx = output_csv.replace(".csv", ".xlsx")
        self.df.to_excel(output_xlsx, index=False, sheet_name="Asteroides")
        logger.info(f"💾 Datos exportados a Excel en {output_xlsx}")

        return self.df

    def mostrar_resumen(self):
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DEL DATASET NASA TRANSFORMADO")
        print("=" * 60)

        cols = [
            "magnitud_absoluta",
            "diametro_min_km",
            "diametro_max_km",
            "velocidad_km_s",
            "distancia_km"
        ]
        print(self.df[cols].describe().round(2).to_string())

        print("\nDistribución por peligrosidad:")
        print(self.df["es_peligroso"].value_counts().to_string())

        if "categoria_tamano" in self.df.columns:
            print("\nCategorías de tamaño:")
            print(self.df["categoria_tamano"].value_counts().to_string())

        print("=" * 60)


if __name__ == "__main__":
    try:
        transformador = NasaTransformador()
        (
            transformador
            .cargar_datos()
            .limpiar_datos()
            .normalizar_tipos()
            .enriquecer_datos()
            .guardar_datos()
        )
        transformador.mostrar_resumen()

    except FileNotFoundError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"❌ Error fatal en transformación: {str(e)}")
        raise