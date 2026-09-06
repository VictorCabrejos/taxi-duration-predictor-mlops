#!/usr/bin/env bash
set -euo pipefail
# Use the active Python environment installed per README.
cd "$(dirname "$0")/.."
exec python -m streamlit run observability/dashboards/enhanced_dashboard.py --server.port 8506 --server.address 127.0.0.1
