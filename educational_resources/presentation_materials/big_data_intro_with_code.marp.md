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

---

# Código Python: Pandas vs. PySpark

**Carga de datos tradicional (Pandas):**

```python
import pandas as pd

# Pandas - Single machine
df = pd.read_csv('taxi_data.csv')
df['duration'] = df['dropoff_time'] - df['pickup_time']
result = df.groupby('borough').mean()
```

**Limitación:** Memory Error con datasets grandes

---

# Código PySpark: Distributed Computing

**Misma operación en PySpark:**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg

# PySpark - Distributed
spark = SparkSession.builder.appName("TaxiAnalysis").getOrCreate()
df = spark.read.csv('taxi_data.csv', header=True)
df = df.withColumn('duration', col('dropoff_time') - col('pickup_time'))
result = df.groupBy('borough').agg(avg('duration'))
```

---

# SQL en Databricks: Spark SQL

**Análisis con SQL distribuido:**

```sql
-- Create temporary view
CREATE OR REPLACE TEMPORARY VIEW taxi_trips AS
SELECT *,
       (dropoff_datetime - pickup_datetime) AS trip_duration
FROM delta.`/databricks-datasets/nyctaxi/tables/nyctaxi_yellow`;

-- Aggregate analysis
SELECT borough,
       AVG(trip_duration) as avg_duration,
       COUNT(*) as total_trips
FROM taxi_trips
GROUP BY borough
ORDER BY avg_duration DESC;
```

---

# MLlib: Machine Learning Distribuido - Parte 1

**Feature Engineering:**

```python
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml import Pipeline

# Feature assembly
assembler = VectorAssembler(
    inputCols=['distance', 'hour', 'day_of_week'],
    outputCol='features'
)
```

---

# MLlib: Machine Learning Distribuido - Parte 2

**Model Training:**

```python
# Distributed ML model
rf = RandomForestRegressor(featuresCol='features', labelCol='duration')

# Pipeline for scalability
pipeline = Pipeline(stages=[assembler, rf])
model = pipeline.fit(train_data)
```

---

# Databricks Notebook: Data Processing

**End-to-end workflow - Parte 1:**

```python
# 1. Data ingestion
df = spark.read.format("delta").load("/mnt/taxi-data/")

# 2. Feature engineering
from pyspark.sql.functions import hour, dayofweek
df_features = df.withColumn("pickup_hour", hour("pickup_datetime")) \
               .withColumn("pickup_dayofweek", dayofweek("pickup_datetime"))
```

---

# Databricks Notebook: MLflow Integration

**End-to-end workflow - Parte 2:**

```python
# 3. MLflow integration
import mlflow
import mlflow.spark

with mlflow.start_run():
    model = pipeline.fit(train_data)
    mlflow.spark.log_model(model, "taxi-duration-model")
```

---

# Docker + Spark: Setup - Parte 1

**docker-compose.yml para desarrollo:**

```yaml
version: '3.8'
services:
  spark-master:
    image: bitnami/spark:3.4
    environment:
      - SPARK_MODE=master
    ports:
      - "8080:8080"
      - "7077:7077"
```

---

# Docker + Spark: Setup - Parte 2

**docker-compose.yml para desarrollo:**

```yaml
  spark-worker:
    image: bitnami/spark:3.4
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
    depends_on:
      - spark-master
```

---

# Bash Scripts: Cluster Setup - Parte 1

**Automated cluster setup:**

```bash
#!/bin/bash
# start-spark-cluster.sh

echo "🚀 Starting Spark Cluster..."

# Start master node
$SPARK_HOME/sbin/start-master.sh

# Start worker nodes
$SPARK_HOME/sbin/start-worker.sh spark://localhost:7077
```

---

# Bash Scripts: Job Submission - Parte 2

**Automated cluster setup:**

```bash
# Submit job
spark-submit \
  --master spark://localhost:7077 \
  --py-files taxi_analysis.py \
  main.py

echo "✅ Cluster started successfully!"
```

---
