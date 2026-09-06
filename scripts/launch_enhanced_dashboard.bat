@echo off
REM Use the active Python environment installed per README.
cd /d "%~dp0\.."
python -m streamlit run observability/dashboards/enhanced_dashboard.py --server.port 8506 --server.address 127.0.0.1
exit /b %errorlevel%
