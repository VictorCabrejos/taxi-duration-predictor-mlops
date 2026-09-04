#!/bin/bash
# Script para iniciar el sistema completo con Docker

echo "🚀 Starting Taxi Duration Predictor with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Require a local environment file and copy it for Docker Compose
if [ ! -f .env.docker ]; then
    echo "Missing .env.docker. Copy .env.docker.example to .env.docker and replace the placeholders."
    exit 1
fi

if [ ! -f .env ]; then
    echo "📋 Creating environment file..."
    cp .env.docker .env
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check MLflow
if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ MLflow is ready"
else
    echo "❌ MLflow is not ready"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI is ready"
else
    echo "❌ FastAPI is not ready"
fi

# Check Dashboard
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Streamlit Dashboard is ready"
else
    echo "❌ Streamlit Dashboard is not ready"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 Available services:"
echo "   • FastAPI Server:      http://localhost:8000"
echo "   • API Documentation:   http://localhost:8000/docs"
echo "   • Streamlit Dashboard: http://localhost:8501"
echo "   • MLflow UI:          http://localhost:5000"
echo "   • PostgreSQL:         localhost:5432"
echo ""
echo "📋 To view logs: docker-compose logs -f [service-name]"
echo "🛑 To stop:      docker-compose down"
echo "🗑️  To cleanup:   docker-compose down -v"
