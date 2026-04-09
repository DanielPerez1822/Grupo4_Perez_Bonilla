#!/usr/bin/env python3
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import relationship
from scripts.database import Base


class Ciudad(Base):
    """Modelo para ciudades"""

    __tablename__ = "ciudades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    pais = Column(String(100), nullable=False)

    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activa = Column(Boolean, default=True)

    registros_clima = relationship(
        "RegistroClima",
        back_populates="ciudad",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ciudad(nombre={self.nombre}, pais={self.pais})>"


class RegistroClima(Base):
    """Modelo para datos de clima"""

    __tablename__ = "registros_clima"

    id = Column(Integer, primary_key=True, autoincrement=True)

    ciudad_id = Column(Integer, ForeignKey("ciudades.id"), nullable=False, index=True)

    temperatura = Column(Float, nullable=False)
    sensacion_termica = Column(Float, nullable=True)
    humedad = Column(Float, nullable=False)
    velocidad_viento = Column(Float, nullable=False)

    descripcion = Column(String(255), nullable=False)
    codigo_tiempo = Column(Integer, nullable=True)

    fecha_extraccion = Column(DateTime, default=datetime.utcnow, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    ciudad = relationship("Ciudad", back_populates="registros_clima")

    __table_args__ = (
        Index("idx_ciudad_fecha", "ciudad_id", "fecha_extraccion"),
    )

    def __repr__(self):
        return f"<RegistroClima(ciudad_id={self.ciudad_id}, temp={self.temperatura})>"


class MetricasETL(Base):
    __tablename__ = "metricas_etl"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_ejecucion = Column(DateTime, default=datetime.utcnow, index=True)

    registros_extraidos = Column(Integer, nullable=False)
    registros_guardados = Column(Integer, nullable=False)
    registros_fallidos = Column(Integer, default=0)

    tiempo_ejecucion_segundos = Column(Float, nullable=False)
    estado = Column(String(50), nullable=False)
    mensaje = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<MetricasETL(estado={self.estado}, registros_guardados={self.registros_guardados})>"