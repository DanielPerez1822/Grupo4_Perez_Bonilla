#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os

# ==============================
# FIX IMPORTS SEGÚN TU ESTRUCTURA
# ==============================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_PATH = os.path.join(ROOT_DIR, "ETL-Inicial")
sys.path.append(SCRIPTS_PATH)

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima

# ==============================
# CONFIG STREAMLIT
# ==============================

st.set_page_config(
    page_title="Dashboard de Clima ETL",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 Dashboard de Clima - ETL Weatherstack")
st.markdown("---")

db = SessionLocal()

try:
    # ==============================
    # CONSULTA
    # ==============================
    registros = db.query(
        RegistroClima,
        Ciudad.nombre
    ).join(
        Ciudad
    ).order_by(
        RegistroClima.fecha_extraccion.desc()
    ).all()

    if not registros:
        st.warning("No hay datos en la base de datos.")
        st.stop()

    # ==============================
    # DATAFRAME
    # ==============================
    data = []
    for registro, ciudad_nombre in registros:
        data.append({
            'Ciudad': ciudad_nombre,
            'Temperatura': registro.temperatura,
            'Sensación Térmica': registro.sensacion_termica,
            'Humedad': registro.humedad,
            'Viento': registro.velocidad_viento,
            'Descripción': registro.descripcion,
            'Fecha': registro.fecha_extraccion
        })

    df = pd.DataFrame(data)

    # ==============================
    # SIDEBAR FILTROS
    # ==============================

    st.sidebar.title("🔧 Filtros")

    ciudades_unicas = df['Ciudad'].unique()

    ciudades_filtro = st.sidebar.multiselect(
        "Selecciona Ciudades:",
        options=ciudades_unicas,
        default=ciudades_unicas
    )

    if not ciudades_filtro:
        st.warning("Selecciona al menos una ciudad.")
        st.stop()

    df_filtrado = df[df['Ciudad'].isin(ciudades_filtro)]

    if df_filtrado.empty:
        st.warning("No hay datos para las ciudades seleccionadas.")
        st.stop()

    # ==============================
    # MÉTRICAS
    # ==============================

    st.subheader("📈 Métricas Principales")
    col1, col2, col3, col4 = st.columns(4)

    temp_promedio = df_filtrado['Temperatura'].mean()
    humedad_promedio = df_filtrado['Humedad'].mean()
    viento_maximo = df_filtrado['Viento'].max()
    total_registros = len(df_filtrado)

    with col1:
        st.metric(
            label="🌡️ Temp. Promedio",
            value=f"{temp_promedio:.1f}°C"
        )

    with col2:
        st.metric(
            label="💧 Humedad Promedio",
            value=f"{humedad_promedio:.1f}%"
        )

    with col3:
        ciudad_viento = df_filtrado.loc[
            df_filtrado['Viento'].idxmax()
        ]['Ciudad']

        st.metric(
            label="💨 Viento Máximo",
            value=f"{viento_maximo:.1f} km/h",
            delta=f"en {ciudad_viento}"
        )

    with col4:
        st.metric(
            label="📊 Total Registros",
            value=total_registros
        )

    st.markdown("---")

    # ==============================
    # VISUALIZACIONES
    # ==============================

    st.subheader("📉 Visualizaciones")

    col1, col2 = st.columns(2)

    # Temperatura por Ciudad
    with col1:
        fig_temp = px.bar(
            df_filtrado.sort_values('Temperatura', ascending=False),
            x='Ciudad',
            y='Temperatura',
            title="Temperatura por Ciudad",
            color='Temperatura',
            color_continuous_scale='RdYlBu_r'
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    # Humedad por Ciudad
    with col2:
        fig_humid = px.bar(
            df_filtrado,
            x='Ciudad',
            y='Humedad',
            title="Humedad Relativa",
            color='Humedad',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_humid, use_container_width=True)

    # Scatter
    col1, col2 = st.columns(2)

    with col1:
        fig_scatter = px.scatter(
            df_filtrado,
            x='Temperatura',
            y='Humedad',
            size='Viento',
            color='Ciudad',
            title="Temperatura vs Humedad",
            hover_data=['Descripción']
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Viento
    with col2:
        fig_wind = px.bar(
            df_filtrado.sort_values('Viento', ascending=False),
            x='Ciudad',
            y='Viento',
            title="Velocidad del Viento",
            color='Viento',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_wind, use_container_width=True)

    st.markdown("---")

    # ==============================
    # TABLA
    # ==============================

    st.subheader("📋 Datos Detallados")

    st.dataframe(
        df_filtrado.sort_values('Fecha', ascending=False),
        use_container_width=True,
        height=400
    )

finally:
    db.close()