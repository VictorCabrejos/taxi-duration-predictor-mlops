# 📊 MLOps Dashboard with Streamlit + MLflow
# FASE 4A: Dashboard Programático para Monitoreo de Modelos

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mlflow
from mlflow.tracking import MlflowClient
import asyncio
import asyncpg
from datetime import datetime, timedelta
import requests
import json
import warnings

warnings.filterwarnings("ignore")

# 🔧 Configuración de página
st.set_page_config(
    page_title="🚕 Taxi Duration Predictor - MLOps Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🎨 CSS personalizado
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .error-metric {
        border-left-color: #dc3545;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 🚀 Funciones utilitarias
@st.cache_data
def load_mlflow_experiments():
    """Carga experimentos desde MLflow programáticamente"""
    try:
        # Configurar MLflow
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        client = MlflowClient()

        # Obtener experimento
        experiment = client.get_experiment_by_name("taxi_duration_prediction")
        if not experiment:
            return None, "No se encontró el experimento taxi_duration_prediction"

        # Obtener todas las runs
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id], order_by=["start_time DESC"]
        )

        # Convertir a DataFrame
        runs_data = []
        for run in runs:
            run_data = {
                "run_id": run.info.run_id,
                "run_name": run.data.tags.get("mlflow.runName", "Unnamed"),
                "model_type": run.data.params.get("model_type", "Unknown"),
                "rmse": float(run.data.metrics.get("rmse", 0)),
                "mae": float(run.data.metrics.get("mae", 0)),
                "r2_score": float(run.data.metrics.get("r2_score", 0)),
                "training_time": float(
                    run.data.metrics.get("training_time_seconds", 0)
                ),
                "start_time": pd.to_datetime(run.info.start_time, unit="ms"),
                "status": run.info.status,
                "train_size": int(run.data.params.get("train_size", 0)),
                "test_size": int(run.data.params.get("test_size", 0)),
            }
            runs_data.append(run_data)

        df = pd.DataFrame(runs_data)
        return df, None

    except Exception as e:
        return None, f"Error cargando MLflow: {str(e)}"


@st.cache_data
def get_best_model():
    """Obtiene el mejor modelo automáticamente"""
    df, error = load_mlflow_experiments()
    if error:
        return None, error

    if df.empty:
        return None, "No hay experimentos disponibles"

    # Ordenar por RMSE (menor es mejor)
    best_run = df.loc[df["rmse"].idxmin()]
    return best_run, None


async def get_database_stats():
    """Obtiene estadísticas actuales de la base de datos"""
    try:
        conn = await asyncpg.connect(
            host="taxi-duration-db.ckj7uy651uld.us-east-1.rds.amazonaws.com",
            port=5432,
            database="postgres",
            user="taxiuser",
            password="TaxiDB2025!",
        )

        # Estadísticas generales
        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_trips,
                AVG(trip_duration_seconds) as avg_duration,
                MIN(pickup_datetime) as earliest_trip,
                MAX(pickup_datetime) as latest_trip,
                COUNT(DISTINCT vendor_id) as unique_vendors
            FROM taxi_trips
        """
        )

        # Distribución por hora
        hourly_stats = await conn.fetch(
            """
            SELECT
                EXTRACT(HOUR FROM pickup_datetime) as hour,
                COUNT(*) as trip_count,
                AVG(trip_duration_seconds) as avg_duration
            FROM taxi_trips
            GROUP BY EXTRACT(HOUR FROM pickup_datetime)
            ORDER BY hour
        """
        )

        await conn.close()

        return {
            "general": dict(stats),
            "hourly": [dict(row) for row in hourly_stats],
        }, None

    except Exception as e:
        return None, f"Error conectando a base de datos: {str(e)}"


# � Funciones para monitoreo del FastAPI
FASTAPI_BASE_URL = "http://localhost:8000"

@st.cache_data(ttl=30)  # Cache por 30 segundos
def check_api_health():
    """Verifica el estado del API FastAPI"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API respondió con código {response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "API no disponible - ¿Está ejecutándose en puerto 8000?"
    except requests.exceptions.Timeout:
        return None, "Timeout conectando al API"
    except Exception as e:
        return None, f"Error verificando API: {str(e)}"

@st.cache_data(ttl=60)  # Cache por 1 minuto
def get_api_model_info():
    """Obtiene información del modelo desde el API"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/model/info", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error obteniendo info del modelo: {response.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def make_api_prediction(prediction_data):
    """Hace una predicción usando el API FastAPI"""
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/predict",
            json=prediction_data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error en predicción: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Error haciendo predicción: {str(e)}"

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_api_database_stats():
    """Obtiene estadísticas de la base de datos desde el API"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/stats/database", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error obteniendo estadísticas: {response.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# �📊 Header principal
st.markdown(
    '<h1 class="main-header">🚕 MLOps Dashboard - Taxi Duration Predictor</h1>',
    unsafe_allow_html=True,
)

# 🔄 Sidebar para controles
st.sidebar.markdown("## 🎛️ Controles del Dashboard")

# Botón de refresh
if st.sidebar.button("🔄 Actualizar Datos", type="primary"):
    st.cache_data.clear()
    st.rerun()

# Selector de vista
view_mode = st.sidebar.selectbox(
    "📊 Seleccionar Vista",
    [
        "📈 Overview General",
        "🤖 Comparación de Modelos",
        "📊 Análisis de Datos",
        "🚀 API Status & Monitoring",
        "🎯 Monitoreo en Tiempo Real",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Información del Sistema")
st.sidebar.info(
    f"""
**Última actualización:** {datetime.now().strftime('%H:%M:%S')}
**MLflow URI:** sqlite:///mlflow.db
**Base de datos:** AWS PostgreSQL
**Estado:** 🟢 Activo
"""
)

# 📊 Vista Overview General
if view_mode == "📈 Overview General":
    st.markdown("## 📈 Resumen Ejecutivo")

    # Cargar datos de MLflow
    experiments_df, mlflow_error = load_mlflow_experiments()

    if mlflow_error:
        st.error(f"❌ Error con MLflow: {mlflow_error}")
    else:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                '<div class="metric-card success-metric">', unsafe_allow_html=True
            )
            st.metric(
                label="🤖 Experimentos Totales",
                value=len(experiments_df) if experiments_df is not None else 0,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            if experiments_df is not None and not experiments_df.empty:
                best_rmse = experiments_df["rmse"].min()
                st.markdown(
                    '<div class="metric-card success-metric">', unsafe_allow_html=True
                )
                st.metric(label="🏆 Mejor RMSE", value=f"{best_rmse:.2f} min")
                st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            if experiments_df is not None and not experiments_df.empty:
                best_r2 = experiments_df["r2_score"].max()
                st.markdown(
                    '<div class="metric-card success-metric">', unsafe_allow_html=True
                )
                st.metric(label="📊 Mejor R²", value=f"{best_r2:.3f}")
                st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            if experiments_df is not None and not experiments_df.empty:
                avg_training_time = experiments_df["training_time"].mean()
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(label="⏱️ Tiempo Promedio", value=f"{avg_training_time:.1f}s")
                st.markdown("</div>", unsafe_allow_html=True)

        # Mejor modelo actual
        best_model, best_error = get_best_model()

        if not best_error and best_model is not None:
            st.markdown("## 🏆 Modelo en Producción (Recomendado)")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.success(
                    f"""
                **🤖 Modelo:** {best_model['model_type']}
                **📊 RMSE:** {best_model['rmse']:.2f} minutos
                **📈 MAE:** {best_model['mae']:.2f} minutos
                **🎯 R²:** {best_model['r2_score']:.3f}
                **⏱️ Tiempo de entrenamiento:** {best_model['training_time']:.1f}s
                **📅 Entrenado:** {best_model['start_time'].strftime('%Y-%m-%d %H:%M')}
                """
                )

            with col2:
                # Gráfico de métricas del mejor modelo
                metrics_data = {
                    "Métrica": ["RMSE", "MAE", "R²"],
                    "Valor": [
                        best_model["rmse"],
                        best_model["mae"],
                        best_model["r2_score"],
                    ],
                    "Objetivo": ["Minimizar", "Minimizar", "Maximizar"],
                }
                metrics_df = pd.DataFrame(metrics_data)

                fig = px.bar(
                    metrics_df,
                    x="Métrica",
                    y="Valor",
                    color="Objetivo",
                    title="Métricas del Mejor Modelo",
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

# 🤖 Vista Comparación de Modelos
elif view_mode == "🤖 Comparación de Modelos":
    st.markdown("## 🤖 Comparación Detallada de Modelos")

    experiments_df, error = load_mlflow_experiments()

    if error:
        st.error(f"❌ Error: {error}")
    elif experiments_df is None or experiments_df.empty:
        st.warning(
            "⚠️ No hay experimentos disponibles. Ejecuta primero el notebook de entrenamiento."
        )
    else:
        # Tabla de comparación
        st.markdown("### 📊 Tabla de Resultados")

        # Formatear tabla para mostrar
        display_df = experiments_df[
            ["model_type", "rmse", "mae", "r2_score", "training_time", "start_time"]
        ].copy()
        display_df["start_time"] = display_df["start_time"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        display_df = display_df.sort_values("rmse")

        # Colorear la tabla
        st.dataframe(
            display_df,
            column_config={
                "model_type": "🤖 Modelo",
                "rmse": st.column_config.NumberColumn("📊 RMSE", format="%.2f"),
                "mae": st.column_config.NumberColumn("📈 MAE", format="%.2f"),
                "r2_score": st.column_config.NumberColumn("🎯 R²", format="%.3f"),
                "training_time": st.column_config.NumberColumn(
                    "⏱️ Tiempo (s)", format="%.1f"
                ),
                "start_time": "📅 Fecha",
            },
            use_container_width=True,
        )

        # Gráficos de comparación
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico RMSE vs MAE
            fig1 = px.scatter(
                experiments_df,
                x="rmse",
                y="mae",
                color="model_type",
                size="r2_score",
                title="📊 RMSE vs MAE por Modelo",
                hover_data=["training_time"],
            )
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Gráfico de barras R²
            fig2 = px.bar(
                experiments_df,
                x="model_type",
                y="r2_score",
                color="model_type",
                title="🎯 R² Score por Modelo",
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

        # Análisis de performance
        st.markdown("### 🏁 Análisis de Performance")

        best_model = experiments_df.loc[experiments_df["rmse"].idxmin()]
        worst_model = experiments_df.loc[experiments_df["rmse"].idxmax()]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.success(
                f"""
            **🏆 MEJOR MODELO**
            **Tipo:** {best_model['model_type']}
            **RMSE:** {best_model['rmse']:.2f} min
            **R²:** {best_model['r2_score']:.3f}
            """
            )

        with col2:
            st.error(
                f"""
            **❌ PEOR MODELO**
            **Tipo:** {worst_model['model_type']}
            **RMSE:** {worst_model['rmse']:.2f} min
            **R²:** {worst_model['r2_score']:.3f}
            """
            )

        with col3:
            improvement = (
                (worst_model["rmse"] - best_model["rmse"]) / worst_model["rmse"]
            ) * 100
            st.info(
                f"""
            **📈 MEJORA**
            **Reducción RMSE:** {improvement:.1f}%
            **Diferencia:** {worst_model['rmse'] - best_model['rmse']:.2f} min
            **Impacto:** Predicciones más precisas
            """
            )

# 📊 Vista Análisis de Datos
elif view_mode == "📊 Análisis de Datos":
    st.markdown("## 📊 Análisis de Datos de Producción")

    # Cargar estadísticas de la base de datos
    with st.spinner("Cargando datos de la base de datos..."):
        db_stats, db_error = asyncio.run(get_database_stats())

    if db_error:
        st.error(f"❌ Error conectando a la base de datos: {db_error}")
    else:
        # Estadísticas generales
        st.markdown("### 📋 Estadísticas Generales")

        general_stats = db_stats["general"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="🚕 Total de Viajes", value=f"{general_stats['total_trips']:,}"
            )

        with col2:
            avg_duration_min = general_stats["avg_duration"] / 60
            st.metric(label="⏱️ Duración Promedio", value=f"{avg_duration_min:.1f} min")

        with col3:
            st.metric(label="🏢 Vendors Únicos", value=general_stats["unique_vendors"])

        with col4:
            date_range = (
                general_stats["latest_trip"] - general_stats["earliest_trip"]
            ).days
            st.metric(label="📅 Rango de Datos", value=f"{date_range} días")

        # Distribución por hora
        st.markdown("### 📈 Distribución de Viajes por Hora")

        hourly_data = pd.DataFrame(db_stats["hourly"])
        hourly_data["avg_duration_min"] = hourly_data["avg_duration"] / 60

        col1, col2 = st.columns(2)

        with col1:
            fig1 = px.bar(
                hourly_data,
                x="hour",
                y="trip_count",
                title="🚕 Número de Viajes por Hora del Día",
            )
            fig1.update_xaxes(title="Hora del Día")
            fig1.update_yaxes(title="Número de Viajes")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.line(
                hourly_data,
                x="hour",
                y="avg_duration_min",
                title="⏱️ Duración Promedio por Hora del Día",
                markers=True,
            )
            fig2.update_xaxes(title="Hora del Día")
            fig2.update_yaxes(title="Duración Promedio (minutos)")
            st.plotly_chart(fig2, use_container_width=True)

        # Insights automáticos
        st.markdown("### 🧠 Insights Automáticos")

        busiest_hour = hourly_data.loc[hourly_data["trip_count"].idxmax()]
        longest_duration_hour = hourly_data.loc[
            hourly_data["avg_duration_min"].idxmax()
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.info(
                f"""
            **🚦 Hora Más Ocupada**
            **Hora:** {int(busiest_hour['hour'])}:00
            **Viajes:** {int(busiest_hour['trip_count']):,}
            **Duración promedio:** {busiest_hour['avg_duration_min']:.1f} min
            """
            )

        with col2:
            st.warning(
                f"""
            **🐌 Hora con Mayor Duración**
            **Hora:** {int(longest_duration_hour['hour'])}:00
            **Duración promedio:** {longest_duration_hour['avg_duration_min']:.1f} min
            **Viajes:** {int(longest_duration_hour['trip_count']):,}
            """
            )

# 🚀 Vista API Status & Monitoring
elif view_mode == "🚀 API Status & Monitoring":
    st.markdown("## 🚀 API Status & Monitoring")
    st.markdown("*Monitor del FastAPI Server y métricas de rendimiento*")

    # Health Check del API
    st.markdown("### � Estado del API")

    api_health, health_error = check_api_health()

    if health_error:
        st.error(f"❌ API No Disponible: {health_error}")
        st.info("💡 **Para activar el API:** `source activate ds_env && python 05_fastapi_server.py`")
    else:
        # Mostrar estado del API
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="🟢 API Status",
                value=api_health["status"].upper()
            )

        with col2:
            st.metric(
                label="🤖 Model Loaded",
                value="✅ YES" if api_health["model_loaded"] else "❌ NO"
            )

        with col3:
            st.metric(
                label="🗄️ Database",
                value=api_health["database_status"].upper()
            )

        with col4:
            st.metric(
                label="🕒 Last Check",
                value=datetime.fromisoformat(api_health["timestamp"].replace('Z', '+00:00')).strftime("%H:%M:%S")
            )

        # Información del modelo en el API
        if api_health["model_loaded"]:
            st.markdown("### 🤖 Modelo en Producción (API)")

            model_info, model_error = get_api_model_info()

            if not model_error and model_info:
                col1, col2 = st.columns([2, 1])

                with col1:
                    metadata = model_info["model_metadata"]
                    st.success(f"""
                    **🤖 Modelo:** {metadata['model_type']}
                    **📊 RMSE:** {metadata['rmse']:.2f} minutos
                    **📈 MAE:** {metadata['mae']:.2f} minutos
                    **�🎯 R²:** {metadata['r2_score']:.3f}
                    **🔧 Run ID:** {metadata['run_id'][:12]}...
                    **📅 Cargado:** {metadata['loaded_at'][:16]}
                    **💾 Train Size:** {metadata['train_size']:,} registros
                    """)

                with col2:
                    # Features requeridas
                    st.markdown("**📋 Features Requeridas:**")
                    features_df = pd.DataFrame({
                        "Feature": model_info["features_required"],
                        "Tipo": ["Numérico"] * len(model_info["features_required"])
                    })
                    st.dataframe(features_df, hide_index=True, use_container_width=True)

        # Test de predicción usando el API
        st.markdown("### 🧪 Test de Predicción API")

        with st.expander("🚀 Probar Predicción via API", expanded=False):
            with st.form("api_prediction_form"):
                col1, col2 = st.columns(2)

                with col1:
                    pickup_lat = st.number_input("📍 Pickup Latitude", value=40.7589, format="%.6f")
                    pickup_lon = st.number_input("📍 Pickup Longitude", value=-73.9851, format="%.6f")
                    dropoff_lat = st.number_input("📍 Dropoff Latitude", value=40.7505, format="%.6f")
                    dropoff_lon = st.number_input("📍 Dropoff Longitude", value=-73.9934, format="%.6f")

                with col2:
                    passenger_count = st.selectbox("👥 Passengers", [1,2,3,4,5,6], index=1)
                    vendor_id = st.selectbox("🏢 Vendor ID", [1,2])
                    pickup_hour = st.slider("🕐 Pickup Hour", 0, 23, 14)
                    day_of_week = st.slider("📅 Day of Week", 0, 6, 2)
                    month = st.slider("📆 Month", 1, 12, 7)

                submitted = st.form_submit_button("🚀 Predecir via API", type="primary")

                if submitted:
                    prediction_data = {
                        "pickup_latitude": pickup_lat,
                        "pickup_longitude": pickup_lon,
                        "dropoff_latitude": dropoff_lat,
                        "dropoff_longitude": dropoff_lon,
                        "passenger_count": passenger_count,
                        "vendor_id": vendor_id,
                        "pickup_hour": pickup_hour,
                        "day_of_week": day_of_week,
                        "month": month
                    }

                    prediction_result, pred_error = make_api_prediction(prediction_data)

                    if pred_error:
                        st.error(f"❌ Error en predicción: {pred_error}")
                    else:
                        # Mostrar resultado
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "🎯 Duración Predicha",
                                f"{prediction_result['predicted_duration_minutes']:.1f} min"
                            )

                        with col2:
                            st.metric(
                                "📏 Distancia",
                                f"{prediction_result['distance_km']:.2f} km"
                            )

                        with col3:
                            st.metric(
                                "🎲 Confianza",
                                f"{prediction_result['confidence_score']:.1%}"
                            )

                        # Detalles de la predicción
                        st.markdown("**📊 Detalles de la Predicción:**")
                        details_data = []
                        for feature, value in prediction_result['features_used'].items():
                            details_data.append({"Feature": feature, "Valor": value})

                        details_df = pd.DataFrame(details_data)
                        st.dataframe(details_df, hide_index=True, use_container_width=True)

                        # JSON Response
                        with st.expander("📄 Respuesta JSON completa"):
                            st.json(prediction_result)

        # Estadísticas via API
        st.markdown("### 📊 Estadísticas de la Base de Datos (via API)")

        api_stats, stats_error = get_api_database_stats()

        if stats_error:
            st.warning(f"⚠️ No se pudieron obtener estadísticas: {stats_error}")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "🚕 Total Viajes",
                    f"{api_stats['total_trips']:,}"
                )

            with col2:
                st.metric(
                    "⏱️ Duración Promedio",
                    f"{api_stats['avg_duration_minutes']:.1f} min"
                )

            with col3:
                st.metric(
                    "📅 Última Actualización",
                    api_stats['last_updated'][:16]
                )

        # URLs útiles
        st.markdown("### 🔗 Enlaces Útiles")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📖 [Swagger Docs](http://localhost:8000/docs)**")
            st.caption("Documentación interactiva del API")

        with col2:
            st.markdown("**📚 [ReDoc](http://localhost:8000/redoc)**")
            st.caption("Documentación alternativa")

        with col3:
            st.markdown("**🏥 [Health Check](http://localhost:8000/health)**")
            st.caption("Status del API en JSON")

# 🎯 Vista Monitoreo en Tiempo Real
elif view_mode == "🎯 Monitoreo en Tiempo Real":
    st.markdown("## 🎯 Simulador de Predicciones en Tiempo Real")

    # Obtener mejor modelo
    best_model, error = get_best_model()

    if error:
        st.error(f"❌ Error: {error}")
    else:
        st.success(
            f"🤖 Usando modelo: **{best_model['model_type']}** (RMSE: {best_model['rmse']:.2f} min)"
        )

        st.markdown("### 🎮 Simulador de Predicción")

        # Formulario de entrada
        with st.form("prediction_form"):
            col1, col2 = st.columns(2)

            with col1:
                pickup_lat = st.number_input(
                    "📍 Latitud Pickup", value=40.7589, format="%.6f"
                )
                pickup_lon = st.number_input(
                    "📍 Longitud Pickup", value=-73.9851, format="%.6f"
                )
                dropoff_lat = st.number_input(
                    "📍 Latitud Dropoff", value=40.7505, format="%.6f"
                )
                dropoff_lon = st.number_input(
                    "📍 Longitud Dropoff", value=-73.9934, format="%.6f"
                )

            with col2:
                passenger_count = st.selectbox(
                    "👥 Número de Pasajeros", [1, 2, 3, 4, 5, 6]
                )
                vendor_id = st.selectbox("🏢 Vendor ID", [1, 2])
                pickup_hour = st.slider("🕐 Hora de Pickup", 0, 23, 12)
                day_of_week = st.selectbox(
                    "📅 Día de la Semana",
                    [
                        "Lunes",
                        "Martes",
                        "Miércoles",
                        "Jueves",
                        "Viernes",
                        "Sábado",
                        "Domingo",
                    ],
                )

            submitted = st.form_submit_button("🚀 Predecir Duración", type="primary")

        if submitted:
            # Simular predicción (en un caso real, cargarías el modelo desde MLflow)

            # Calcular distancia
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371
                lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = (
                    np.sin(dlat / 2) ** 2
                    + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
                )
                return 2 * R * np.arcsin(np.sqrt(a))

            distance = haversine_distance(
                pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
            )

            # Features simuladas
            day_mapping = {
                "Lunes": 0,
                "Martes": 1,
                "Miércoles": 2,
                "Jueves": 3,
                "Viernes": 4,
                "Sábado": 5,
                "Domingo": 6,
            }
            day_num = day_mapping[day_of_week]
            is_weekend = 1 if day_num >= 5 else 0
            is_rush_hour = 1 if pickup_hour in [7, 8, 9, 17, 18, 19] else 0

            # Predicción simulada (basada en el patrón del mejor modelo)
            base_time = distance * 2.5  # ~2.5 min por km
            time_factor = 1.2 if is_rush_hour else 1.0
            weekend_factor = 0.9 if is_weekend else 1.0
            passenger_factor = 1 + (passenger_count - 1) * 0.05

            predicted_duration = (
                base_time * time_factor * weekend_factor * passenger_factor
            )
            confidence = 0.85 if not is_rush_hour else 0.75

            # Mostrar resultados
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="🎯 Duración Predicha", value=f"{predicted_duration:.1f} min"
                )

            with col2:
                st.metric(label="📏 Distancia", value=f"{distance:.2f} km")

            with col3:
                st.metric(label="🎲 Confianza", value=f"{confidence:.0%}")

            # Detalles adicionales
            st.markdown("### 📊 Detalles de la Predicción")

            details_data = {
                "Feature": [
                    "Distancia (km)",
                    "Pasajeros",
                    "Vendor",
                    "Hora",
                    "Día de Semana",
                    "Es Fin de Semana",
                    "Es Hora Pico",
                ],
                "Valor": [
                    f"{distance:.2f}",
                    passenger_count,
                    vendor_id,
                    f"{pickup_hour}:00",
                    day_of_week,
                    "Sí" if is_weekend else "No",
                    "Sí" if is_rush_hour else "No",
                ],
            }

            details_df = pd.DataFrame(details_data)
            st.dataframe(details_df, use_container_width=True, hide_index=True)

            # Mapa simulado
            st.markdown("### 🗺️ Ruta Simulada")

            map_data = pd.DataFrame(
                {
                    "lat": [pickup_lat, dropoff_lat],
                    "lon": [pickup_lon, dropoff_lon],
                    "tipo": ["Pickup", "Dropoff"],
                }
            )

            st.map(map_data[["lat", "lon"]], zoom=12)

# 📋 Footer
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666;'>
    🚕 <strong>Taxi Duration Predictor</strong> |
    MLOps Dashboard con Streamlit + MLflow |
    Arquitectura Hexagonal + DDD |
    Desarrollado para curso MLOps 2025
</div>
""",
    unsafe_allow_html=True,
)
