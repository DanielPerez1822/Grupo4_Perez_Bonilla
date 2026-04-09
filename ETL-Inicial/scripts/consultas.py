#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

import pandas as pd
from sqlalchemy import func

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

db = SessionLocal()


def temperatura_promedio_por_ciudad():

    registros = db.query(
        Ciudad.nombre,
        func.avg(RegistroClima.temperatura).label("temp_promedio")
    ).join(RegistroClima).group_by(Ciudad.nombre).all()

    df = pd.DataFrame(registros, columns=["Ciudad", "Temperatura Promedio"])

    print("\n📊 TEMPERATURA PROMEDIO POR CIUDAD")
    print(df.to_string(index=False))


def ciudad_mas_humeda():

    registro = db.query(
        Ciudad.nombre,
        RegistroClima.humedad
    ).join(Ciudad).order_by(
        RegistroClima.humedad.desc()
    ).first()

    if registro:
        print(f"\n💧 Ciudad más húmeda: {registro.nombre} ({registro.humedad}%)")


def velocidad_viento_max():

    registro = db.query(
        Ciudad.nombre,
        RegistroClima.velocidad_viento
    ).join(Ciudad).order_by(
        RegistroClima.velocidad_viento.desc()
    ).first()

    if registro:
        print(f"\n💨 Viento máximo: {registro.nombre} ({registro.velocidad_viento} km/h)")


def metricas_etl():

    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(5).all()

    print("\n📈 Últimas ejecuciones ETL")

    for m in metricas:

        print(
            f"{m.fecha_ejecucion} | "
            f"{m.estado} | "
            f"Extraídos:{m.registros_extraidos} | "
            f"Guardados:{m.registros_guardados} | "
            f"Tiempo:{m.tiempo_ejecucion_segundos:.2f}s"
        )


if __name__ == "__main__":

    temperatura_promedio_por_ciudad()
    ciudad_mas_humeda()
    velocidad_viento_max()
    metricas_etl()

    db.close()