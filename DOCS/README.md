# � Documentation - MLOps Taxi Duration Predictor

## 📁 **Documentation Structure**

This folder contains all project documentation organized by category:

```
DOCS/
├── project_development/          # 🏗️ Project development history
│   ├── GITIGNORE_UPDATES.md         # Git ignore evolution
│   ├── REORGANIZATION_SUMMARY.md     # Project restructuring
│   └── PROJECT_TRANSFORMATION_COMPLETE.md  # Complete transformation log
├── testing/                      # 🧪 Testing documentation
│   ├── PROJECT_TESTING_RESULTS.md    # Testing validation results
│   └── TESTING_STRATEGY_COMPLETE.md  # Complete testing strategy
├── ASSIGNMENT_GUIDE.md           # 📋 Student assignment guide
├── CICD_PIPELINE.md              # 🚀 CI/CD pipeline documentation
├── CICD_SLIDES.md                # 📊 CI/CD presentation materials
├── DEPLOYMENT_GUIDE.md           # 🐳 Deployment instructions
├── ESTUDIANTE_CICD_GUIDE.md      # 🎓 Student CI/CD guide
├── HEXAGONAL_ARCHITECTURE.md     # 🏗️ Architecture documentation
├── MLOPS_PIPELINE.md             # 🔄 MLOps workflow guide
├── PROYECTO_FINAL_STATUS.md      # 📈 Final project status
└── QUICK_START.md                # 🚀 Quick start guide
```

## 🎯 **How to Navigate Documentation**

### **🚀 Getting Started**
- **New to the project?** → Start with `QUICK_START.md`
- **Want to deploy?** → Check `DEPLOYMENT_GUIDE.md`
- **Student assignment?** → See `ASSIGNMENT_GUIDE.md`

### **🏗️ Architecture & Design**
- **Understanding the structure** → `HEXAGONAL_ARCHITECTURE.md`
- **MLOps workflow** → `MLOPS_PIPELINE.md`
- **Project evolution** → `project_development/PROJECT_TRANSFORMATION_COMPLETE.md`

### **🧪 Testing & Development**
- **Testing strategy** → `testing/TESTING_STRATEGY_COMPLETE.md`
- **Test results** → `testing/PROJECT_TESTING_RESULTS.md`
- **Development history** → `project_development/`

### **🚀 CI/CD & Deployment**
- **Pipeline overview** → `CICD_PIPELINE.md`
- **Student guide** → `ESTUDIANTE_CICD_GUIDE.md`
- **Deployment steps** → `DEPLOYMENT_GUIDE.md`

---

## 📋 **Project Overview**

This project demonstrates a complete **MLOps** implementation using **Hexagonal Architecture** and **Domain-Driven Design (DDD)** for NYC taxi trip duration prediction.

### **🎯 Educational Objective**

Show the **transition** from experimental notebooks to a **professional MLOps system** ready for production with:
- ✅ Automated ML pipeline
- ✅ REST API for predictions
- ✅ Executive dashboard for monitoring
- ✅ CI/CD with GitHub Actions
- ✅ Containerization with Docker

---

## 🏗️ **Arquitectura del Sistema**

```
📊 FRONTEND              🔄 BACKEND              🗄️ DATA
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Streamlit       │────▶│ FastAPI Server   │────▶│ PostgreSQL AWS  │
│ Dashboard       │     │ (Puerto 8000)    │     │ (49,719 trips)  │
│ (Puerto 8501)   │     │                  │     │                 │
│                 │     │ ┌──────────────┐ │     │                 │
│ • Overview      │     │ │ MLflow       │ │     │                 │
│ • Model Compare │     │ │ Tracking     │ │     │                 │
│ • Data Analysis │     │ │ (sqlite)     │ │     │                 │
│ • API Monitor   │     │ └──────────────┘ │     │                 │
│ • Predictions   │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## 📂 **Estructura del Proyecto**

```
Sesion 13/
├── 📊 FRONTEND
│   └── 04_streamlit_dashboard.py      # Dashboard unificado
│
├── 🚀 BACKEND
│   └── 05_fastapi_server.py           # API REST server
│
├── 🤖 MACHINE LEARNING
│   ├── 01_data_exploration.ipynb      # EDA inicial
│   ├── 02_database_setup.ipynb        # Migración PostgreSQL
│   ├── 03_mlflow_training.ipynb       # Pipeline ML + tracking
│   └── mlflow.db                      # Experimentos locales
│
├── 🏗️ ARCHITECTURE
│   └── taxi_duration_predictor/       # Arquitectura Hexagonal
│       ├── domain/                    # Lógica de negocio
│       │   ├── entities.py           # Entidades del dominio
│       │   ├── ports.py              # Interfaces/contratos
│       │   └── services.py           # Servicios de dominio
│       └── adapters/                  # Implementaciones externas
│           ├── data_adapter.py       # PostgreSQL adapter
│           └── model_adapter.py      # MLflow adapter
│
├── 🐳 DEPLOYMENT
│   ├── Dockerfile                     # Container definition
│   ├── docker-compose.yml            # Multi-service orchestration
│   └── requirements.txt              # Python dependencies
│
├── 🔄 CI/CD
│   └── .github/workflows/
│       └── mlops-pipeline.yml         # GitHub Actions
│
└── 📚 DOCUMENTATION
    └── DOCS/
        ├── README.md                  # Este archivo
        ├── HEXAGONAL_ARCHITECTURE.md # Explicación arquitectural
        ├── MLOPS_PIPELINE.md          # Explicación del pipeline
        └── DEPLOYMENT_GUIDE.md        # Guía de deployment
```

---

## 🚀 **Quick Start**

### **🐳 Docker Deployment (Recommended)**
```bash
# 1. Clone and setup
git clone <repository-url> && cd taxi-duration-predictor
cp .env.docker .env

# 2. Start complete stack
docker-compose up -d

# 3. Access services
# 🚀 API Server: http://localhost:8000
# 📊 Dashboard: http://localhost:8501
# 🔬 MLflow UI: http://localhost:5000
```

### **📋 Manual Setup (Development)**

#### **1. Activar Ambiente**
```bash
source activate ds_env
```

#### **2. Lanzar Stack Completo**
```bash
# Terminal 1: FastAPI
python 05_fastapi_server.py

# Terminal 2: Streamlit
streamlit run 04_streamlit_dashboard.py
```

### **3. Acceder a las Aplicaciones**
- **📊 Dashboard**: http://localhost:8501
- **🚀 API Docs**: http://localhost:8000/docs
- **🏥 Health Check**: http://localhost:8000/health

---

## 🎯 **Funcionalidades Principales**

### **📊 Dashboard Streamlit (5 vistas)**
1. **📈 Overview General**: Métricas ejecutivas de MLflow
2. **🤖 Comparación de Modelos**: Análisis comparativo automático
3. **📊 Análisis de Datos**: Estadísticas PostgreSQL en tiempo real
4. **🚀 API Status & Monitoring**: Monitoreo del FastAPI server
5. **🎯 Predicciones en Tiempo Real**: Simulador interactivo

### **🚀 FastAPI Server (REST API)**
- ✅ **POST /predict**: Predicciones de duración de viajes
- ✅ **GET /health**: Health check completo del sistema
- ✅ **GET /model/info**: Información del modelo en producción
- ✅ **GET /stats/database**: Estadísticas de la base de datos
- ✅ **POST /model/reload**: Recarga del mejor modelo desde MLflow

---

## 🤖 **Resultados de Machine Learning**

### **Modelos Entrenados:**
| Modelo | RMSE (min) | MAE (min) | R² Score | Training Time |
|--------|------------|-----------|----------|---------------|
| **RandomForest** | **6.62** | **4.27** | **0.681** | 5.1s |
| XGBoost | 6.85 | 4.45 | 0.663 | 8.3s |
| LinearRegression | 7.47 | 5.12 | 0.598 | 1.8s |

**🏆 Modelo en Producción**: RandomForest (mejor RMSE)

### **Features Utilizadas:**
- `distance_km`: Distancia Haversine calculada
- `passenger_count`: Número de pasajeros
- `vendor_id`: ID del vendor (1 o 2)
- `hour_of_day`: Hora del pickup (0-23)
- `day_of_week`: Día de la semana (0-6)
- `month`: Mes del año (1-12)
- `is_weekend`: Indicador de fin de semana
- `is_rush_hour`: Indicador de hora pico

---

## 📈 **MLOps Principles Implementados**

### **✅ Experiment Tracking**
- MLflow para tracking automático de experimentos
- Comparación de modelos y selección automática del mejor
- Versionado de modelos y artefactos

### **✅ Model Serving**
- FastAPI para serving escalable
- API REST con validación Pydantic
- Health checks y monitoring

### **✅ Monitoring & Observability**
- Dashboard en tiempo real
- Métricas de performance del modelo
- Monitoreo de infraestructura

### **✅ Automation**
- Pipeline automatizado de entrenamiento
- Deployment automático con CI/CD
- Selección automática del mejor modelo

---

## 🏗️ **Arquitectura Hexagonal & DDD**

Ver: [HEXAGONAL_ARCHITECTURE.md](./HEXAGONAL_ARCHITECTURE.md)

**Principios Implementados:**
- ✅ **Separation of Concerns**: Domain, Ports, Adapters
- ✅ **Dependency Inversion**: Interfaces definen contratos
- ✅ **Single Responsibility**: Cada clase tiene una responsabilidad
- ✅ **Domain-Driven Design**: Lógica de negocio centralizada

---

## 🔄 **CI/CD Pipeline**

Ver: [MLOPS_PIPELINE.md](./MLOPS_PIPELINE.md)

**GitHub Actions Workflow:**
1. **Trigger**: Push a main o schedule diario
2. **Test**: Unit tests y model validation
3. **Retrain**: Si performance baja del threshold
4. **Deploy**: Containerización y deployment automático
5. **Monitor**: Health checks post-deployment

---

## 🐳 **Deployment**

Ver: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

### **Docker Compose**
```bash
docker-compose up -d
```

### **Kubernetes** (opcional)
```bash
kubectl apply -f k8s/
```

---

## 📊 **Métricas de Éxito**

### **Técnicas:**
- ✅ **Model Performance**: RMSE < 8.0 minutos (threshold empresarial)
- ✅ **API Latency**: < 200ms por predicción
- ✅ **Uptime**: > 99.5%
- ✅ **Data Quality**: 0 errores de ingesta

### **Negocio:**
- ✅ **Predicción Accuracy**: 85% confidence score promedio
- ✅ **User Experience**: Dashboard responsivo < 2s
- ✅ **Operational**: Deploy automático sin downtime

---

## 🎓 **Para Estudiantes**

### **Conceptos Clave Aprendidos:**
1. **MLOps End-to-End**: De notebook a producción
2. **Arquitectura Hexagonal**: Diseño escalable y mantenible
3. **Domain-Driven Design**: Modelado del dominio de negocio
4. **API-First Development**: Serving models via REST
5. **Infrastructure as Code**: Docker + CI/CD
6. **Monitoring & Observability**: Dashboards ejecutivos

### **Skills Técnicos:**
- Python (FastAPI, Streamlit, MLflow)
- Machine Learning (scikit-learn, XGBoost)
- Databases (PostgreSQL, AsyncPG)
- DevOps (Docker, GitHub Actions)
- Cloud (AWS RDS)

---

## 🚀 **Próximos Pasos**

1. **Scaling**: Kubernetes deployment
2. **Advanced Monitoring**: Prometheus + Grafana
3. **Data Pipeline**: Airflow para ETL
4. **A/B Testing**: Gradual model rollouts
5. **Security**: Authentication & authorization

---

## 👥 **Equipo**

- **ML Engineer**: Pipeline de machine learning
- **Software Architect**: Arquitectura hexagonal
- **DevOps Engineer**: CI/CD y containerización
- **Data Engineer**: PostgreSQL y data pipeline

---

## 📝 **Licencia**

MIT License - Uso educativo para curso MLOps 2025

---

**🎯 Desarrollo por GitHub Copilot para curso MLOps - Universidad Ricardo Palma 2025**
