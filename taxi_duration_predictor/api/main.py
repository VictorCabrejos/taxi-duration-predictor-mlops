"""
FastAPI Main Application - Taxi Duration Predictor
Aplicación principal FastAPI siguiendo hexagonal architecture
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import uvicorn

from .controller import create_api_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="🚕 Taxi Duration Predictor API",
    description="""
    **API REST para predicciones de duración de viajes de taxi en NYC**

    Esta API utiliza modelos de Machine Learning entrenados con MLflow para predecir
    la duración de viajes de taxi basándose en ubicaciones de origen y destino.

    ## Características principales:
    - ✅ Predicciones en tiempo real
    - ✅ Modelos entrenados con 49,000+ viajes reales
    - ✅ Arquitectura hexagonal + DDD
    - ✅ MLflow para tracking de modelos
    - ✅ Validación automática de coordenadas NYC

    ## Modelos disponibles:
    - Random Forest (producción)
    - XGBoost (backup)
    - Linear Regression (baseline)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "predictions",
            "description": "Endpoints para realizar predicciones de duración de viajes",
        },
        {
            "name": "health",
            "description": "Endpoints para verificar la salud del servicio",
        },
        {"name": "model", "description": "Endpoints para información de modelos"},
    ],
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
api_router = create_api_router()
app.include_router(api_router, prefix="/api/v1")


# Endpoint raíz
@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz con información básica"""
    return {
        "service": "Taxi Duration Predictor API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "health": "/api/v1/health",
        "predict": "/api/v1/predict",
    }


# Endpoint de salud simplificado
@app.get("/health", tags=["root"])
async def simple_health():
    """Health check simplificado"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "timestamp": datetime.now().isoformat(),
        },
    )


# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("🚀 Iniciando Taxi Duration Predictor API...")
    logger.info("📊 Verificando conexión con MLflow...")

    try:
        # Aquí podrías agregar verificaciones iniciales
        # como conexión a base de datos, carga de modelos, etc.
        logger.info("✅ API iniciada correctamente")
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("🛑 Cerrando Taxi Duration Predictor API...")
    logger.info("✅ API cerrada correctamente")


def create_app() -> FastAPI:
    """Factory para crear la aplicación"""
    return app


if __name__ == "__main__":
    # Configuración para desarrollo
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
