#!/bin/bash

# 🚀 MLOps Dashboard Launcher
# Enhanced Taxi Duration Predictor Dashboard

cd "$(dirname "$0")/.."  # Go to project root

echo "🚀 Starting Enhanced MLOps Dashboard..."
echo "📊 Location: observability/dashboards/enhanced_dashboard.py"
echo "🌐 URL: http://localhost:8503"
echo ""

# Activate conda environment and launch enhanced dashboard
source activate ds_env && streamlit run observability/dashboards/enhanced_dashboard.py --server.port 8503
