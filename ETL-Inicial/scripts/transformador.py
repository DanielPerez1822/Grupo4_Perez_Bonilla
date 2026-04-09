#!/usr/bin/env python3
"""
transformador.py - Fase Transform del pipeline ETL
Limpia, normaliza y enriquece los datos extraídos del clima.
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


class WeatherstackTransformador:
    def __init__(self, input_csv="data/clima.csv"):
        self.input_csv = input_csv
        self.df = None

    def cargar_datos(self):
        if not os.path.exists(self.input_csv):
            raise FileNotFoundError(
                f"Archivo {self.input_csv} no encontrado. "
                "Ejecuta primero scripts/extractor_api.py"
            )

        self.df = pd.read_csv(self.input_csv)
        logger.info(f"📂 Datos cargados: {len(self.df)} registros desde {self.input_csv}")
        return self

    def limpiar_datos(self):
        filas_antes = len(self.df)

        self.df.drop_duplicates(inplace=True)

        self.df.fillna({
            "region": "N/A",
            "latitud": 0.0,
            "longitud": 0.0,
            "indice_uv": 0,
            "descripcion": "Sin descripción",
            "direccion_viento": "N/A",
            "presion": 0,
            "visibilidad": 0
        }, inplace=True)

        filas_despues = len(self.df)
        logger.info(
            f"🧹 Limpieza: {filas_antes - filas_despues} duplicados eliminados, "
            f"{filas_despues} registros restantes"
        )
        return self

    def normalizar_tipos(self):
        cols_numericas = [
            "temperatura", "sensacion_termica", "humedad",
            "velocidad_viento", "presion", "visibilidad",
            "indice_uv", "latitud", "longitud", "codigo_tiempo"
        ]

        for col in cols_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        if "hora_local" in self.df.columns:
            self.df["hora_local"] = pd.to_datetime(
                self.df["hora_local"], errors="coerce"
            )

        logger.info("🔧 Tipos de datos normalizados")
        return self

    def enriquecer_datos(self):
        def clasificar_temp(t):
            if pd.isna(t):
                return "N/A"
            if t < 10:
                return "Frío"
            elif t < 20:
                return "Templado"
            elif t < 30:
                return "Cálido"
            return "Caluroso"

        def clasificar_viento(v):
            if pd.isna(v):
                return "N/A"
            if v < 1:
                return "Calma"
            elif v < 20:
                return "Brisa ligera"
            elif v < 40:
                return "Viento moderado"
            return "Viento fuerte"

        self.df["categoria_temperatura"] = self.df["temperatura"].apply(clasificar_temp)
        self.df["categoria_viento"] = self.df["velocidad_viento"].apply(clasificar_viento)

        self.df["diferencial_termico"] = (
            self.df["temperatura"] - self.df["sensacion_termica"]
        ).round(1)

        self.df["fecha_procesamiento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info("✨ Datos enriquecidos con columnas calculadas")
        return self

    def guardar_datos(self, output_csv="data/clima_transformado.csv"):
        self.df.to_csv(output_csv, index=False)
        logger.info(f"💾 Datos transformados guardados en {output_csv}")

        output_xlsx = output_csv.replace(".csv", ".xlsx")
        self.df.to_excel(output_xlsx, index=False, sheet_name="Clima")
        logger.info(f"💾 Datos exportados a Excel en {output_xlsx}")

        return self.df

    def mostrar_resumen(self):
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DEL DATASET TRANSFORMADO")
        print("=" * 60)

        cols = ["temperatura", "sensacion_termica", "humedad", "velocidad_viento"]
        disponibles = [c for c in cols if c in self.df.columns]
        print(self.df[disponibles].describe().round(2).to_string())

        if "categoria_temperatura" in self.df.columns:
            print("\nCategorías de temperatura:")
            print(self.df["categoria_temperatura"].value_counts().to_string())

        print("=" * 60)


if __name__ == "__main__":
    try:
        transformador = WeatherstackTransformador()
        df = (
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
        logger.error(f"Error fatal en transformación: {str(e)}")
        raise