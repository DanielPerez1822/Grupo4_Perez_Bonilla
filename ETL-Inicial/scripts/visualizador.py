#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging
import os

from sqlalchemy import text
from scripts.database import engine  # 👈 usamos tu conexión existente

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/visualizador.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 🔥 CONSULTA A LA BASE DE DATOS
query = """
SELECT DISTINCT ON (c.nombre)
    c.nombre AS ciudad,
    r.temperatura,
    r.sensacion_termica,
    r.humedad,
    r.velocidad_viento
FROM registros_clima r
JOIN ciudades c ON r.ciudad_id = c.id
ORDER BY c.nombre, r.fecha_extraccion DESC;
"""

try:
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    logger.info("✅ Datos cargados desde PostgreSQL")

except Exception as e:
    logger.error("❌ Error cargando datos desde la base")
    logger.error(e)
    exit()

# Crear figura con múltiples gráficas
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Análisis de Clima por Ciudades', fontsize=16, fontweight='bold')

# Gráfica 1: Temperaturas
ax1 = axes[0, 0]
ax1.bar(df['ciudad'], df['temperatura'])
ax1.set_title('Temperatura Actual (°C)')
ax1.set_ylabel('Temperatura (°C)')
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', alpha=0.3)

# Gráfica 2: Humedad
ax2 = axes[0, 1]
ax2.bar(df['ciudad'], df['humedad'])
ax2.set_title('Humedad Relativa (%)')
ax2.set_ylabel('Humedad (%)')
ax2.tick_params(axis='x', rotation=45)
ax2.grid(axis='y', alpha=0.3)

# Gráfica 3: Velocidad del Viento
ax3 = axes[1, 0]
ax3.scatter(df['ciudad'], df['velocidad_viento'], s=200)
ax3.set_title('Velocidad del Viento (km/h)')
ax3.set_ylabel('Velocidad (km/h)')
ax3.tick_params(axis='x', rotation=45)
ax3.grid(alpha=0.3)

# Gráfica 4: Sensación Térmica vs Temperatura
ax4 = axes[1, 1]
x = np.arange(len(df))
width = 0.35
ax4.bar(x - width/2, df['temperatura'], width, label='Temperatura')
ax4.bar(x + width/2, df['sensacion_termica'], width, label='Sensación Térmica')
ax4.set_title('Temperatura vs Sensación Térmica')
ax4.set_ylabel('Temperatura (°C)')
ax4.set_xticks(x)
ax4.set_xticklabels(df['ciudad'], rotation=45)
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('data/clima_analysis.png', dpi=300, bbox_inches='tight')
logger.info("✅ Gráficas guardadas en data/clima_analysis.png")
plt.show()