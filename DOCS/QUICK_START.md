# 🚀 Quick Start Guide - Taxi Duration Predictor

## For Users Who Just Downloaded the Repo

### 📊 **Option 1: Just the Dashboard (Fastest)**

**Windows:**
1. Double-click `start.bat`
2. Wait for dashboard to open at http://localhost:8506

**Linux/Mac:**
1. Double-click `start.sh` or run `./start.sh`
2. Wait for dashboard to open at http://localhost:8506

**Any OS:**
```bash
python start.py
```

### 🏗️ **Option 2: Full MLOps Stack**

```bash
python main.py
```

This starts:
- 🚀 **API Server**: http://localhost:8000
- 📊 **Dashboard**: http://localhost:8506
- 🔬 **MLflow UI**: http://localhost:5000

## 🎯 What You Get

### The Dashboard Includes:
- ✅ **Real-time predictions** with interactive map
- ✅ **Model comparison** and performance metrics
- ✅ **Data analysis** with business insights
- ✅ **API monitoring** and health checks
- ✅ **Intelligent trip analysis** with contextual insights

### Sample Prediction Test:
- **Pickup**: Times Square (40.7580, -73.9855)
- **Dropoff**: JFK Airport (40.6413, -73.7781)
- **Expected**: ~45-60 minutes depending on traffic

## 🔧 Troubleshooting

**Error: "streamlit not found"**
```bash
pip install -r requirements.txt
```

**Error: Python path issues**
```bash
conda activate ds_env
python start.py
```

**Dashboard won't load**
- Check if port 8506 is available
- Try different port: `streamlit run observability/dashboards/enhanced_dashboard.py --server.port 8507`

## 📋 Requirements

- Python 3.9+
- Dependencies in `requirements.txt`
- Optional: Conda environment `ds_env`

The scripts automatically detect and use the right Python environment.
