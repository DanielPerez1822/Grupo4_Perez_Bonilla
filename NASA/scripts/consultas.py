#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

import pandas as pd
from sqlalchemy import func

from scripts.database import SessionLocal
from scripts.models import Asteroide, NeoWsRegistro, MetricasETL

db = SessionLocal()


def cantidad_asteroides_por_fecha():
    registros = db.query(
        Asteroide.fecha_aproximacion,
        func.count(Asteroide.id).label("total_asteroides")
    ).group_by(
        Asteroide.fecha_aproximacion
    ).order_by(
        Asteroide.fecha_aproximacion.asc()
    ).all()

    if registros:
        df = pd.DataFrame(registros, columns=["Fecha Aproximación", "Total Asteroides"])
        print("\n☄️ CANTIDAD DE ASTEROIDES POR FECHA")
        print(df.to_string(index=False))
    else:
        print("\n⚠️ No hay datos en la tabla asteroides")


def asteroide_mas_rapido():
    registro = db.query(
        Asteroide.nombre,
        Asteroide.velocidad_km_s,
        Asteroide.fecha_aproximacion
    ).order_by(
        Asteroide.velocidad_km_s.desc()
    ).first()

    if registro:
        print(
            f"\n🚀 Asteroide más rápido: {registro.nombre} "
            f"({registro.velocidad_km_s:.2f} km/s) "
            f"- fecha aproximación: {registro.fecha_aproximacion}"
        )
    else:
        print("\n⚠️ No hay datos para calcular el asteroide más rápido")


def asteroide_mas_cercano():
    registro = db.query(
        Asteroide.nombre,
        Asteroide.distancia_km,
        Asteroide.fecha_aproximacion
    ).order_by(
        Asteroide.distancia_km.asc()
    ).first()

    if registro:
        print(
            f"\n📏 Asteroide más cercano: {registro.nombre} "
            f"({registro.distancia_km:,.0f} km) "
            f"- fecha aproximación: {registro.fecha_aproximacion}"
        )
    else:
        print("\n⚠️ No hay datos para calcular el asteroide más cercano")


def asteroides_peligrosos():
    total = db.query(
        func.count(Asteroide.id)
    ).filter(
        Asteroide.es_peligroso == True
    ).scalar()

    print(f"\n⚠️ Asteroides potencialmente peligrosos: {total}")


def promedio_magnitud_absoluta():
    promedio = db.query(
        func.avg(Asteroide.magnitud_absoluta)
    ).scalar()

    if promedio is not None:
        print(f"\n🌌 Magnitud absoluta promedio: {promedio:.2f}")
    else:
        print("\n⚠️ No hay datos para calcular magnitud promedio")


def total_registros_neows():
    total = db.query(func.count(NeoWsRegistro.id)).scalar()
    print(f"\n🛰️ Total registros en NeoWs crudo: {total}")


def metricas_etl():
    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(5).all()

    print("\n📈 ÚLTIMAS EJECUCIONES ETL")

    if not metricas:
        print("No hay métricas registradas")
        return

    for m in metricas:
        print(
            f"{m.fecha_ejecucion} | "
            f"{m.estado} | "
            f"Insertados:{m.registros_insertados} | "
            f"Errores:{m.errores} | "
            f"Tiempo:{m.tiempo_ejecucion:.2f}s"
        )


if __name__ == "__main__":
    cantidad_asteroides_por_fecha()
    asteroide_mas_rapido()
    asteroide_mas_cercano()
    asteroides_peligrosos()
    promedio_magnitud_absoluta()
    total_registros_neows()
    metricas_etl()

    db.close()