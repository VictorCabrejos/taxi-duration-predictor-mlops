#!/bin/bash
# 🚀 Enhanced MLOps Dashboard Launcher
# Launch script for the improved Taxi Duration Predictor Dashboard

echo "🚕 Starting Enhanced MLOps Dashboard..."
echo "================================================="
echo ""
echo "🎯 Dashboard Features:"
echo "  ✅ Role-based user guidance"
echo "  ✅ Interactive help system"
echo "  ✅ Comprehensive troubleshooting"
echo "  ✅ Business-friendly explanations"
echo "  ✅ Enhanced prediction interface"
echo ""
echo "👥 Designed for:"
echo "  📈 Executives (Overview)"
echo "  🧪 Data Scientists (Model Comparison)"
echo "  📊 Analysts (Data Insights)"
echo "  ⚙️ DevOps (API Monitoring)"
echo "  👤 End Users (Prediction Simulator)"
echo ""
echo "================================================="
echo "🌐 Dashboard will open at: http://localhost:8501"
echo "📚 Documentation: UX_Enhancement_Guide.md"
echo "================================================="
echo ""

# Launch the enhanced dashboard
streamlit run enhanced_dashboard.py --server.port 8501 --server.headless false
