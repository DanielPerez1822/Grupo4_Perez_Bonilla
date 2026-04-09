#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import sys
import os

# ==============================
# IMPORTS SEGUN TU ESTRUCTURA
# ==============================
# Ejemplo esperado:
# proyecto/
# ├── ETL-Inicial/
# │   └── scripts/
# │       ├── database.py
# │       └── models.py
# └── ETL-StreamLit-Prueba/
#     └── dashboard_advanced.py

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_PATH = os.path.join(ROOT_DIR, "ETL-Inicial")
sys.path.append(SCRIPTS_PATH)

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

# ==============================
# CONFIG STREAMLIT
# ==============================
st.set_page_config(
    page_title="Dashboard Avanzado Clima",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌍 Dashboard Avanzado - Análisis de Clima")
st.markdown("---")

db = SessionLocal()

try:
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Vista General", "📈 Histórico", "🔍 Análisis", "📋 Métricas ETL"]
    )

    # ==========================================================
    # TAB 1 - VISTA GENERAL
    # ==========================================================
    with tab1:
        st.subheader("Datos Actuales")

        col1, col2, col3 = st.columns(3)

        with col1:
            ciudades_count = db.query(func.count(Ciudad.id)).scalar() or 0
            st.metric("🏙️ Ciudades", ciudades_count)

        with col2:
            registros_count = db.query(func.count(RegistroClima.id)).scalar() or 0
            st.metric("📊 Registros Totales", registros_count)

        with col3:
            ultima_fecha = db.query(func.max(RegistroClima.fecha_extraccion)).scalar()
            if ultima_fecha:
                st.metric("⏰ Última Actualización", ultima_fecha.strftime("%Y-%m-%d %H:%M"))
            else:
                st.metric("⏰ Última Actualización", "Sin datos")

        st.markdown("---")

        # Último registro por ciudad
        subquery = db.query(
            RegistroClima.ciudad_id,
            func.max(RegistroClima.fecha_extraccion).label("max_fecha")
        ).group_by(RegistroClima.ciudad_id).subquery()

        registros_actuales = db.query(
            Ciudad.nombre,
            RegistroClima.temperatura,
            RegistroClima.humedad,
            RegistroClima.velocidad_viento,
            RegistroClima.descripcion
        ).join(
            RegistroClima,
            Ciudad.id == RegistroClima.ciudad_id
        ).join(
            subquery,
            and_(
                RegistroClima.ciudad_id == subquery.c.ciudad_id,
                RegistroClima.fecha_extraccion == subquery.c.max_fecha
            )
        ).order_by(Ciudad.nombre.asc()).all()

        if registros_actuales:
            df_actual = pd.DataFrame(
                registros_actuales,
                columns=["Ciudad", "Temperatura", "Humedad", "Viento", "Descripción"]
            )

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    df_actual,
                    x="Ciudad",
                    y="Temperatura",
                    title="Temperatura Actual",
                    color="Temperatura",
                    color_continuous_scale="RdYlBu_r"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.pie(
                    df_actual,
                    values="Humedad",
                    names="Ciudad",
                    title="Distribución de Humedad"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.dataframe(df_actual, use_container_width=True)
        else:
            st.warning("No hay registros disponibles.")

    # ==========================================================
    # TAB 2 - HISTÓRICO
    # ==========================================================
    with tab2:
        st.subheader("Análisis Histórico")

        col1, col2 = st.columns(2)

        with col1:
            fecha_inicio = st.date_input(
                "Desde:",
                value=datetime.now() - timedelta(days=7),
                key="fecha_inicio"
            )

        with col2:
            fecha_fin = st.date_input(
                "Hasta:",
                value=datetime.now(),
                key="fecha_fin"
            )

        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())

        registros_historicos = db.query(
            RegistroClima,
            Ciudad.nombre
        ).join(Ciudad).filter(
            and_(
                RegistroClima.fecha_extraccion >= fecha_inicio_dt,
                RegistroClima.fecha_extraccion <= fecha_fin_dt
            )
        ).order_by(RegistroClima.fecha_extraccion.asc()).all()

        if registros_historicos:
            data = []

            for registro, ciudad_nombre in registros_historicos:
                data.append({
                    "Fecha": registro.fecha_extraccion,
                    "Ciudad": ciudad_nombre,
                    "Temperatura": registro.temperatura,
                    "Humedad": registro.humedad,
                    "Viento": registro.velocidad_viento
                })

            df_historico = pd.DataFrame(data)

            fig = px.line(
                df_historico,
                x="Fecha",
                y="Temperatura",
                color="Ciudad",
                title="Temperatura en el Tiempo",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.dataframe(df_historico, use_container_width=True)
        else:
            st.warning("No hay datos en ese rango de fechas")

    # ==========================================================
    # TAB 3 - ANÁLISIS ESTADÍSTICO
    # ==========================================================
    with tab3:
        st.subheader("Análisis Estadístico")

        ciudades = db.query(Ciudad).order_by(Ciudad.nombre.asc()).all()

        if not ciudades:
            st.info("No hay ciudades registradas.")
        else:
            for ciudad in ciudades:
                with st.expander(f"📍 {ciudad.nombre}"):
                    registros = db.query(RegistroClima).filter_by(ciudad_id=ciudad.id).all()

                    if registros:
                        temps = [r.temperatura for r in registros if r.temperatura is not None]
                        humeds = [r.humedad for r in registros if r.humedad is not None]
                        vientos = [r.velocidad_viento for r in registros if r.velocidad_viento is not None]

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🌡️ Temp Prom.",
                                f"{sum(temps)/len(temps):.1f}°C" if temps else "N/A"
                            )

                        with col2:
                            st.metric(
                                "💧 Humedad Prom.",
                                f"{sum(humeds)/len(humeds):.1f}%" if humeds else "N/A"
                            )

                        with col3:
                            st.metric(
                                "💨 Viento Prom.",
                                f"{sum(vientos)/len(vientos):.1f} km/h" if vientos else "N/A"
                            )

                        with col4:
                            st.metric("📊 Registros", len(registros))
                    else:
                        st.info("Sin registros")

    # ==========================================================
    # TAB 4 - MÉTRICAS ETL
    # ==========================================================
    with tab4:
        st.subheader("Métricas de Ejecución ETL")

        metricas = db.query(MetricasETL).order_by(
            MetricasETL.fecha_ejecucion.desc()
        ).limit(20).all()

        if metricas:
            data = []

            for m in metricas:
                data.append({
                    "Fecha": m.fecha_ejecucion,
                    "Estado": m.estado,
                    "Extraídos": m.registros_extraidos,
                    "Guardados": m.registros_guardados,
                    "Fallidos": m.registros_fallidos,
                    "Tiempo (s)": float(m.tiempo_ejecucion_segundos or 0),
                    "Mensaje": m.mensaje
                })

            df_metricas = pd.DataFrame(data)

            # Columna visual amigable para tabla
            df_metricas_tabla = df_metricas.copy()
            df_metricas_tabla["Tiempo (s)"] = df_metricas_tabla["Tiempo (s)"].map(lambda x: f"{x:.2f}")

            st.dataframe(df_metricas_tabla, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    df_metricas,
                    x="Fecha",
                    y="Guardados",
                    title="Registros Guardados por Ejecución",
                    color="Estado"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.scatter(
                    df_metricas,
                    x="Fecha",
                    y="Tiempo (s)",
                    size="Guardados",
                    title="Duración de Ejecuciones",
                    color="Estado"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay métricas registradas aún")

finally:
    db.close()