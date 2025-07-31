@echo off
REM Batch script for Windows to start the Docker services

echo 🚀 Starting Taxi Duration Predictor with Docker...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Copy environment file if it doesn't exist
if not exist .env (
    echo 📋 Creating environment file...
    copy .env.docker .env
)

REM Build and start services
echo 🔨 Building Docker images...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo.
echo 🎉 Deployment complete!
echo.
echo 📊 Available services:
echo    • FastAPI Server:      http://localhost:8000
echo    • API Documentation:   http://localhost:8000/docs
echo    • Streamlit Dashboard: http://localhost:8501
echo    • MLflow UI:          http://localhost:5000
echo    • PostgreSQL:         localhost:5432
echo.
echo 📋 To view logs: docker-compose logs -f [service-name]
echo 🛑 To stop:      docker-compose down
echo 🗑️  To cleanup:   docker-compose down -v

pause
