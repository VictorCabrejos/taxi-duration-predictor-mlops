"""
FastAPI Main Application - Taxi Duration Predictor
Aplicación principal FastAPI siguiendo hexagonal architecture
"""

from contextlib import asynccontextmanager
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .controller import create_api_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Log process lifecycle without contacting optional backing services."""
    logger.info("🚀 Iniciando Taxi Duration Predictor API...")
    yield
    logger.info("🛑 Cerrando Taxi Duration Predictor API...")


# Crear aplicación FastAPI
app = FastAPI(
    title="Taxi Duration Predictor API",
    description="""
    API educativa de referencia para explorar predicciones de duración de viajes.

    El repositorio demuestra límites de arquitectura hexagonal, validación de
    coordenadas de ejemplo, adaptadores de modelos y seguimiento opcional con
    MLflow. No incluye un dataset de NYC, un modelo entrenado listo para producción
    ni garantías de servicio. Los endpoints de predicción e información del modelo
    requieren que el operador proporcione una configuración de modelo y MLflow
    utilizable. `GET /health` comprueba únicamente que el proceso API responde.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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


def create_app() -> FastAPI:
    """Factory para crear la aplicación"""
    return app


if __name__ == "__main__":
    # Configuración para desarrollo
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
