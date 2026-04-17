#!/usr/bin/env python3

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from datetime import datetime
# ==============================
# Base Declarativa
# ==============================
from scripts.database import Base

# ==============================
# Tabla 1: Asteroides (principal ETL)
# ==============================
class Asteroide(Base):
    __tablename__ = "asteroides"

    id = Column(Integer, primary_key=True, index=True)
    nasa_id = Column(String, index=True)
    nombre = Column(String)
    magnitud_absoluta = Column(Float)
    diametro_min_km = Column(Float)
    diametro_max_km = Column(Float)
    es_peligroso = Column(Boolean)
    fecha_aproximacion = Column(Date)
    velocidad_km_s = Column(Float)
    distancia_km = Column(Float)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Asteroide(nombre={self.nombre}, fecha={self.fecha_aproximacion})>"


# ==============================
# Tabla 2: NeoWs Registros (datos crudos del endpoint)
# ==============================
class NeoWsRegistro(Base):
    __tablename__ = "neows_registros"

    id = Column(Integer, primary_key=True, index=True)
    nasa_id = Column(String, index=True)
    nombre = Column(String)
    magnitud_absoluta = Column(Float)
    diametro_min_km = Column(Float)
    diametro_max_km = Column(Float)
    es_peligroso = Column(Boolean)
    fecha_aproximacion = Column(Date)
    velocidad_km_s = Column(Float)
    distancia_km = Column(Float)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NeoWsRegistro(nombre={self.nombre}, fecha={self.fecha_aproximacion})>"


# ==============================
# Tabla 3: Métricas ETL
# ==============================
class MetricasETL(Base):
    __tablename__ = "metricas_etl"

    id = Column(Integer, primary_key=True, index=True)
    registros_insertados = Column(Integer)
    errores = Column(Integer)
    tiempo_ejecucion = Column(Float)
    estado = Column(String)
    fecha_ejecucion = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MetricasETL(estado={self.estado}, registros={self.registros_insertados})>"