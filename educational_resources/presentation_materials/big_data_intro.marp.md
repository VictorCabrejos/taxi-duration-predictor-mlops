---
marp: true
theme: default
paginate: true
header: 'Machine Learning y Big Data - UNMSM'
footer: 'Sesiones 14-15: Introducción a Big Data'
---

# Big Data: From MLOps to Scalable Data Processing 🚀

**Sesiones 14-15**
**Machine Learning y Big Data - UNMSM**

**Profesor:** Victor M. Cabrejos Jr.
**Tema:** Transición de MLOps tradicional a procesamiento distribuido

---

# ¿Qué es Big Data?

**Los 6 Vs del Big Data moderno:**

- **Volume (Volumen) 📊**
  - Terabytes, petabytes de datos
  - Más allá de la capacidad de una sola máquina

- **Velocity (Velocidad) ⚡**
  - Datos generados en tiempo real
  - Streaming de datos continuo

---

# Los 6 Vs del Big Data (Parte 2)

- **Variety (Variedad) 🔄**
  - Datos estructurados, semi-estructurados, no estructurados
  - Múltiples formatos: JSON, CSV, imágenes, texto

- **Veracity (Veracidad) ✅**
  - Calidad y confiabilidad de los datos
  - Manejo de datos incompletos o incorrectos

---

# Los 6 Vs del Big Data (Parte 3)

- **Value (Valor) 💎**
  - Capacidad de extraer insights valiosos
  - ROI del procesamiento de datos

- **Variability (Variabilidad) 🌊**
  - Inconsistencia en flujos de datos
  - Patrones cambiantes en el tiempo

**Nivel master:** Estas dimensiones son críticas para proyectos empresariales

---

# Ejemplos de Big Data

**Casos reales:**

- **Volume:** Millones de viajes de taxi por día en NYC
- **Velocity:** Transacciones bancarias en tiempo real
- **Variety:** Logs + datos de usuarios + métricas

**¿Por qué importa?**
- Los métodos tradicionales no escalan
- Necesitamos procesamiento distribuido

---

# Pandas vs. Big Data - Problema

**❌ Limitaciones con Pandas:**

```python
# Esto NO funciona con datasets grandes:
df = pd.read_csv("10TB_dataset.csv")  # Memory Error!
df.groupby('category').sum()  # Single-threaded
```

**El problema:** Una sola máquina, memoria limitada

---

# Pandas vs. Big Data - Solución

**✅ Solución con PySpark:**

```python
# PySpark distribuye el trabajo:
df = spark.read.csv("10TB_dataset.csv")  # Distributed!
df.groupBy('category').sum()  # Multi-node processing
```

**La diferencia clave:**
Pandas = una máquina | PySpark = cluster de máquinas

---

# ¿Qué es Apache Spark?

**Motor de procesamiento distribuido para Big Data:**

- **In-memory computing** → 100x más rápido que Hadoop
- **Unified Analytics Engine** → Batch + Streaming + ML + SQL
- **Fault-tolerant** → Recuperación automática de errores

**¿Por qué PySpark?**
- Python API para Apache Spark
- Sintaxis familiar similar a pandas

---

# Arquitectura Distribuida de Spark

```
Driver Program → Cluster Manager → Worker Nodes
     ↓               ↓                 ↓
   PySpark        YARN/Mesos      Executors
```

**Ventajas:**
- **Escalabilidad horizontal** (más máquinas = más poder)
- **Procesamiento paralelo** automático
- **Cloud-ready** (AWS, GCP, Azure, Databricks)

---

# ¿Qué es Databricks? 🏗️

**Plataforma unificada para analytics y ML:**

- **Apache Spark optimizado** en la nube
- **Collaborative notebooks** para equipos
- **Auto-scaling clusters** según demanda
- **Integrated MLflow** para MLOps

**¿Por qué es importante?**
- Elimina la complejidad de configuración
- Perfecto para equipos de data science

---

# Databricks Community Edition

**🆓 GRATIS para aprender:**

- **15GB storage** incluido
- **Single-node cluster** automático
- **Notebooks interactivos** pre-configurados
- **Conectividad con AWS/Azure**
- **Ideal para proyectos educativos**

**Perfecto para nuestro curso** ✅

---

# Workflow típico en Databricks

**Proceso paso a paso:**

1. **Upload data** → Databricks FileStore
2. **Create cluster** → Auto-configured Spark
3. **Process data** → PySpark notebooks
4. **Deploy models** → MLflow integration

**Todo en una plataforma integrada** 🚀

---

# Evolución: Traditional MLOps → Big Data MLOps

**Pipeline tradicional:**
```
pandas → sklearn → MLflow → FastAPI → Docker
```

**Pipeline Big Data:**
```
PySpark → MLlib → MLflow → Databricks → Cloud
```

**La diferencia:** Escalabilidad automática

---

# Ventajas de Big Data para ML

**🤖 Scalable Feature Engineering**
- Procesar millones de features en paralelo
- Feature stores distribuidos

**📈 Distributed Model Training**
- Hyperparameter tuning en cluster
- Ensemble models en paralelo

**⚡ Real-time Predictions**
- Streaming ML pipelines
- Sub-second inference at scale

---

# Sesión 14: Databricks Setup + PySpark Basics

**Objetivos prácticos:**

- Configurar Databricks Community Edition
- Migrar nuestro dataset de taxis a PySpark
- Comparar performance: pandas vs. PySpark

**Resultado:** Entender las diferencias en la práctica

---

# Sesión 15: Big Data MLOps Pipeline

**Construcción del pipeline distribuido:**

- Feature engineering distribuido
- Model training con MLlib
- Integration con nuestro MLOps stack existente

**Objetivo final:**
Convertir **taxi-duration-predictor** en un sistema que maneje **millones de viajes** 🚀
