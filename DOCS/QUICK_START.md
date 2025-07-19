# 🎯 Quick Start Guide - Docker Deployment

## 🚀 **Inicio Rápido con Docker**

### **Prerequisitos**
- ✅ Docker Desktop instalado y ejecutándose
- ✅ Git para clonar el repositorio
- ✅ 4GB RAM libre para los contenedores

### **🔥 Despliegue en 3 comandos**

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd taxi-duration-predictor

# 2. Configurar entorno
cp .env.docker .env

# 3. Iniciar todo el stack
docker-compose up -d
```

### **🌐 URLs de Acceso**
Una vez desplegado, accede a:
- 🚀 **API Server**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 📊 **Dashboard**: http://localhost:8501
- 🔬 **MLflow UI**: http://localhost:5000
- 🗄️ **PostgreSQL**: localhost:5432

### **📋 Comandos Útiles**

```bash
# Ver estado de servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Logs de servicio específico
docker-compose logs -f api
docker-compose logs -f dashboard

# Detener servicios
docker-compose down

# Limpiar todo (incluyendo volúmenes)
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache
```

### **🔧 Configuración de Entorno**

Archivo `.env` personalizable:
```bash
POSTGRES_PASSWORD=taxi_predictor_2025
DATABASE_URL=postgresql://postgres:taxi_predictor_2025@postgres:5432/taxi_duration
MLFLOW_TRACKING_URI=http://mlflow:5000
API_BASE_URL=http://api:8000
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
```

### **🏥 Health Checks**

Verificar que todos los servicios estén saludables:
```bash
# Health check automático
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
curl http://localhost:5000
```

### **📊 Arquitectura de Contenedores**

```
🌐 Frontend Layer:
├── 📊 Streamlit Dashboard (8501)
└── 🌐 FastAPI Server (8000)

🧠 Application Layer:
├── 🤖 MLflow Tracking (5000)
└── 🏗️ Hexagonal Architecture

🗄️ Data Layer:
└── 🗄️ PostgreSQL (5432)
```

### **🎯 Demo Completo**

El sistema incluye:
- ✅ **49,719 registros** de NYC Taxi trips
- ✅ **3 modelos ML** pre-entrenados (RandomForest ganador: 6.62 min RMSE)
- ✅ **API REST** completa con documentación OpenAPI
- ✅ **Dashboard interactivo** con 5 vistas de MLOps
- ✅ **Monitoreo en tiempo real** de modelo y sistema
- ✅ **Arquitectura hexagonal** con DDD

### **🚀 Para Producción**

```bash
# Usar configuración de producción
docker-compose -f docker-compose.prod.yml up -d

# Con SSL y balanceador
docker-compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d
```

---

**🎓 Sistema completo listo para demostración en clase**
**🏗️ Arquitectura Hexagonal + DDD + MLOps**
**🐳 Completamente containerizado y portable**
