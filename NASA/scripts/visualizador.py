import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import logging
import os

# ==============================
# Configuración logging
# ==============================
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

# ==============================
# Cargar datos
# ==============================
try:
    df = pd.read_csv('data/asteroides.csv')
    logger.info("✅ Datos de asteroides cargados correctamente")
except Exception as e:
    logger.error(f"❌ Error cargando datos: {str(e)}")
    exit()

# Convertir columnas numéricas
df['magnitud_absoluta'] = pd.to_numeric(df['magnitud_absoluta'], errors='coerce')
df['velocidad_km_s'] = pd.to_numeric(df['velocidad_km_s'], errors='coerce')
df['distancia_km'] = pd.to_numeric(df['distancia_km'], errors='coerce')

# ==============================
# Crear figura con múltiples gráficas
# ==============================
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('Análisis de Asteroides Cercanos a la Tierra (NASA NEO)', 
             fontsize=16, fontweight='bold')

# ==========================================
# 1️⃣ Cantidad de asteroides por fecha
# ==========================================
ax1 = axes[0, 0]
conteo_fecha = df.groupby('fecha_aproximacion').size()
ax1.bar(conteo_fecha.index, conteo_fecha.values)
ax1.set_title('Asteroides por Fecha de Aproximación')
ax1.set_ylabel('Cantidad')
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', alpha=0.3)

# ==========================================
# 2️⃣ Distribución de magnitud absoluta
# ==========================================
ax2 = axes[0, 1]
ax2.hist(df['magnitud_absoluta'].dropna(), bins=15)
ax2.set_title('Distribución de Magnitud Absoluta')
ax2.set_xlabel('Magnitud')
ax2.set_ylabel('Frecuencia')
ax2.grid(alpha=0.3)

# ==========================================
# 3️⃣ Velocidad vs Distancia
# ==========================================
ax3 = axes[1, 0]
ax3.scatter(df['velocidad_km_s'], df['distancia_km'])
ax3.set_title('Velocidad vs Distancia')
ax3.set_xlabel('Velocidad (km/s)')
ax3.set_ylabel('Distancia (km)')
ax3.grid(alpha=0.3)

# ==========================================
# 4️⃣ Proporción de asteroides peligrosos
# ==========================================
ax4 = axes[1, 1]
peligrosos = df['es_peligroso'].value_counts()
ax4.pie(peligrosos.values, labels=peligrosos.index, autopct='%1.1f%%')
ax4.set_title('Proporción de Asteroides Potencialmente Peligrosos')

# ==============================
# Guardar gráfico
# ==============================
plt.tight_layout()
plt.savefig('data/nasa_asteroides_analysis.png', dpi=300, bbox_inches='tight')
logger.info("✅ Gráficas guardadas en data/nasa_asteroides_analysis.png")

plt.show()