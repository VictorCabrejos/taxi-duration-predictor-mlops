@echo off
REM 🚀 MLOps Dashboard Launcher - Windows
REM Enhanced Taxi Duration Predictor Dashboard

cd /d "%~dp0\.."

echo 🚀 Starting Enhanced MLOps Dashboard...
echo 📊 Location: observability/dashboards/enhanced_dashboard.py
echo 🌐 URL: http://localhost:8503
echo.

REM Activate conda environment and launch enhanced dashboard
call conda activate ds_env && streamlit run observability/dashboards/enhanced_dashboard.py --server.port 8503
