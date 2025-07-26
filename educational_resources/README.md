# 📚 Educational Resources - MLOps Taxi Duration Predictor

Esta carpeta contiene todos los recursos educativos organizados por tipo para facilitar el aprendizaje y enseñanza de MLOps.

## 📁 Estructura

```
educational_resources/
├── notebooks/                    # Notebooks Jupyter para exploración y aprendizaje
│   ├── 01_data_exploration.ipynb      # Exploración inicial de datos
│   ├── 02_database_setup.ipynb        # Configuración de base de datos
│   └── 03_mlflow_training.ipynb       # Entrenamiento con MLflow (referencia)
├── scripts/                      # Scripts educativos numerados
│   ├── 04_streamlit_dashboard.py      # Dashboard original (referencia)
│   └── 05_fastapi_server.py           # Servidor API original (referencia)
├── Testing_with_DDD_Hexagonal_TDD.md  # 🧪 Guía completa de testing con DDD/Hexagonal/TDD
├── Testing_Infrastructure_Files.md # 🧪 Guía de archivos de infraestructura de testing
└── presentation_materials/       # Materiales de presentación
    ├── sesion13.pdf                   # Presentación principal
    ├── sesion13.pptx                  # PowerPoint editable
    ├── aws_info.txt                   # Información de AWS
    └── CONTEXTO_COMPLETO_PARA_CHATGPT.txt  # Contexto completo
```

## 🎯 Propósito de cada recurso

### 📓 Notebooks (notebooks/)

Los notebooks están **numerados secuencialmente** para mostrar el flujo de trabajo:

1. **01_data_exploration.ipynb** - Exploración y análisis de datos
   - Carga y análisis del dataset de taxis NYC
   - Visualizaciones y estadísticas descriptivas
   - Identificación de features importantes
   - Detección de problemas de calidad de datos

2. **02_database_setup.ipynb** - Configuración de infraestructura
   - Migración de datos CSV a PostgreSQL
   - Configuración de conexión a AWS RDS
   - Validación de datos migrados

3. **03_mlflow_training.ipynb** - Entrenamiento de modelos (REFERENCIA)
   - Pipeline de entrenamiento original
   - Comparación de múltiples modelos
   - Tracking con MLflow
   - **Nota:** Ahora esto se hace con `taxi_duration_predictor/pipeline/train.py`

### 🔧 Scripts (scripts/)

Scripts educativos que muestran la evolución hacia producción:

4. **04_streamlit_dashboard.py** - Dashboard original (REFERENCIA)
   - Monitoreo básico de modelos
   - Interfaz de predicciones
   - **Nota:** Ahora se usa `taxi_duration_predictor/monitoring/dashboard.py`

5. **05_fastapi_server.py** - API original (REFERENCIA)
   - Servidor de predicciones básico
   - **Nota:** Ahora se usa la estructura en `taxi_duration_predictor/api/`

6. **create_mlops_structure.py** - Generador automático de estructura de proyectos
   - Script de Python para crear estructura completa de proyectos MLOps
   - Soporte para 4 niveles: beginner, intermediate, advanced, expert
   - Generación automática de archivos de configuración
   - Ideal para iniciar nuevos proyectos rápidamente

### 🧪 Guías de Desarrollo (Documentos Markdown)

**Testing_with_DDD_Hexagonal_TDD.md** - Guía completa de testing
   - Testing con Domain-Driven Design (DDD)
   - Testing con Arquitectura Hexagonal
   - Test-Driven Development (TDD) en MLOps
   - Estrategias específicas para proyectos de Machine Learning
   - Ejemplos prácticos y mejores prácticas

**Testing_Infrastructure_Files.md** - Guía de archivos de infraestructura de testing
   - Explicación de `pytest.ini`, `run_tests.bat`, `run_tests.sh`
   - Por qué estos archivos están en el directorio raíz
   - Cómo usar los scripts de testing
   - Configuración de entornos y ejecución multiplataforma
   - Estándares profesionales de testing en MLOps

**Ultimate_MLOps_Project_Structure_Guide.md** - Guía completa de estructura de proyectos
   - Estructura completa para proyectos MLOps profesionales
   - Explicación de cada carpeta y cuándo usarla
   - Progresión de aprendizaje (beginner → intermediate → advanced → expert)
   - Ejemplos del mundo real y casos de uso
   - Compliance, seguridad, y consideraciones empresariales

### 📊 Materiales de Presentación (presentation_materials/)

- **sesion13.pdf/pptx** - Presentación principal del curso
- **aws_info.txt** - Configuraciones e información de AWS
- **CONTEXTO_COMPLETO_PARA_CHATGPT.txt** - Contexto completo para IA

## 🚀 Flujo de Aprendizaje Recomendado

### Para Estudiantes:

1. **Comenzar con exploración** → `01_data_exploration.ipynb`
2. **Configurar infraestructura** → `02_database_setup.ipynb`
3. **Entender ML pipeline** → `03_mlflow_training.ipynb` (revisar)
4. **Ver dashboard básico** → `04_streamlit_dashboard.py` (revisar)
5. **Ver API básica** → `05_fastapi_server.py` (revisar)
6. **Estudiar arquitectura hexagonal** → `../taxi_duration_predictor/`
7. **🧪 Aprender testing profesional** → `Testing_with_DDD_Hexagonal_TDD.md`
8. **🧪 Entender infraestructura de testing** → `Testing_Infrastructure_Files.md`
9. **🏗️ Conocer estructura de proyectos completa** → `Ultimate_MLOps_Project_Structure_Guide.md`
10. **🚀 Crear nuevos proyectos automáticamente** → `scripts/create_mlops_structure.py`

### Para Instructores:

- Use los notebooks 1-2 en clase para enseñar fundamentos
- Los scripts 4-5 muestran la "versión simple" vs "versión profesional"
- **La guía de testing** es esencial para enseñar desarrollo profesional
- La presentación tiene todo el contexto teórico
- El proyecto principal muestra mejores prácticas de MLOps

## 🔄 Relación con el Código de Producción

| Recurso Educativo | Versión de Producción | Propósito |
|---|---|---|
| `03_mlflow_training.ipynb` | `taxi_duration_predictor/pipeline/train.py` | Mostrar evolución de notebook a script |
| `04_streamlit_dashboard.py` | `taxi_duration_predictor/monitoring/dashboard.py` | Comparar enfoque simple vs arquitecturado |
| `05_fastapi_server.py` | `taxi_duration_predictor/api/` | Mostrar separación de responsabilidades |

## 💡 Consejos para Enseñanza

1. **Comience simple**: Use los notebooks para mostrar conceptos
2. **Muestre la evolución**: Compare scripts educativos con versión profesional
3. **Enfoque en arquitectura**: Use el código de producción para enseñar mejores prácticas
4. **Hands-on**: Los estudiantes pueden ejecutar tanto notebooks como API

## 🔧 Cómo Ejecutar

### Notebooks:
```bash
jupyter notebook educational_resources/notebooks/
```

### Scripts (solo para referencia):
```bash
# Dashboard original (no recomendado para producción)
streamlit run educational_resources/scripts/04_streamlit_dashboard.py

# API original (no recomendado para producción)
python educational_resources/scripts/05_fastapi_server.py
```

### Versión de Producción:
```bash
# API moderna
python main.py

# Dashboard moderno
streamlit run taxi_duration_predictor/monitoring/dashboard.py
```

---

**Nota**: Los recursos educativos se mantienen para enseñanza, pero la versión de producción está en la carpeta principal del proyecto.
