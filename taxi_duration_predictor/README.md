# Taxi Duration Predictor - MLOps Pipeline

## 🎯 Objetivo del Proyecto

Predecir la duración de viajes de taxi en NYC usando un pipeline MLOps completo con arquitectura hexagonal y DDD.

## 🏗️ Arquitectura

### Arquitectura Hexagonal Simple
```
taxi_duration_predictor/
├── domain/
│   ├── entities.py      # TaxiTrip, Location, Prediction (DDD Entities)
│   ├── ports.py         # Interfaces/Puertos
│   └── services.py      # Business Logic
├── adapters/
│   ├── data_adapter.py  # PostgreSQL Adapter
│   ├── ml_adapter.py    # MLflow + Sklearn Adapter
│   └── api_adapter.py   # FastAPI Adapter
├── api/
│   └── main.py          # FastAPI Application
├── pipeline/
│   ├── train.py         # Training Pipeline
│   └── predict.py       # Prediction Pipeline
└── monitoring/
    └── dashboard.py     # Streamlit Dashboard
```

### Stack Tecnológico
- **Framework**: FastAPI
- **ML Tracking**: MLflow
- **Base de Datos**: PostgreSQL (AWS RDS)
- **Containerización**: Docker
- **Monitoreo**: Streamlit
- **CI/CD**: GitHub Actions

## 📋 Fases del Proyecto

### ✅ FASE 1 COMPLETADA: Setup Base
- [x] Exploración del dataset NYC Taxi
- [x] Estructura hexagonal creada
- [x] Entidades del dominio definidas (DDD)
- [x] Puertos y adaptadores especificados

### 🚧 FASE 2: AWS PostgreSQL
- [ ] Crear RDS PostgreSQL Free Tier
- [ ] Migrar CSV a PostgreSQL
- [ ] Conexión desde Python

### 🚧 FASE 3: Pipeline Básico
- [ ] Feature engineering
- [ ] Modelo RandomForest con MLflow
- [ ] API básica con FastAPI

### 🚧 FASE 4: Docker & Monitoring
- [ ] Dockerfile
- [ ] Dashboard Streamlit

## 🎯 Entidades del Dominio (DDD)

### Entidades Principales
- **`TaxiTrip`**: Viaje de taxi (entidad raíz)
- **`Location`**: Ubicación geográfica (value object)
- **`TripDuration`**: Duración del viaje (value object)
- **`Prediction`**: Predicción del modelo
- **`TripFeatures`**: Features para ML

### Servicios del Dominio
- **`TripPredictionService`**: Orquesta predicciones
- **`ModelTrainingService`**: Maneja entrenamiento
- **`DataValidationService`**: Valida y limpia datos
- **`MonitoringService`**: Monitorea performance

## 🔌 Puertos (Interfaces)

- **`TripRepository`**: Acceso a datos de viajes
- **`PredictionRepository`**: Acceso a predicciones
- **`MLModelService`**: Servicios de ML
- **`FeatureEngineering`**: Extracción de features
- **`NotificationService`**: Notificaciones
- **`MetricsService`**: Métricas y monitoreo

## 🎓 Propósito Educativo

Este proyecto demuestra:
1. **Arquitectura Hexagonal** sin over-engineering
2. **Domain Driven Design (DDD)** aplicado a ML
3. **MLOps** end-to-end pipeline
4. **Buenas prácticas** de desarrollo
5. **Deployment real** con Docker y AWS

## 🚀 Próximos Pasos

1. Ejecutar notebook de exploración: `01_data_exploration.ipynb`
2. Crear base de datos PostgreSQL en AWS
3. Implementar adaptadores
4. Crear pipeline de entrenamiento
5. Deploy con Docker

---

**Nota**: Este proyecto está diseñado para ser simple pero profesional, evitando complejidad innecesaria mientras mantiene las mejores prácticas de MLOps.
