#!/bin/bash
# Test Execution Script for MLOps Project
# Script para ejecutar tests con diferentes configuraciones

set -e  # Exit on any error

# Go to project root
cd "$(dirname "$0")/.."

echo "🧪 MLOps Project Testing Suite"
echo "================================"

# Activate conda environment
echo "📋 Activating conda environment..."
source activate ds_env

# Create reports directory
mkdir -p tests/reports

# Function to run specific test categories
run_tests() {
    local test_type=$1
    local test_path=$2
    local description=$3

    echo ""
    echo "🔬 Running $description..."
    echo "----------------------------------------"

    if [ "$test_type" = "unit" ]; then
        pytest tests/unit/ -m "unit" --tb=short -v
    elif [ "$test_type" = "integration" ]; then
        pytest tests/integration/ -m "integration" --tb=short -v
    elif [ "$test_type" = "e2e" ]; then
        pytest tests/e2e/ -m "e2e" --tb=short -v
    elif [ "$test_type" = "all" ]; then
        pytest tests/ --tb=short -v
    elif [ "$test_type" = "coverage" ]; then
        pytest tests/ --cov=taxi_duration_predictor --cov-report=html:tests/reports/coverage_html --cov-report=term-missing -v
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "unit")
        run_tests "unit" "tests/unit/" "Unit Tests (Domain Logic)"
        ;;
    "integration")
        run_tests "integration" "tests/integration/" "Integration Tests (Adapters)"
        ;;
    "e2e")
        run_tests "e2e" "tests/e2e/" "End-to-End Tests (Full Pipeline)"
        ;;
    "coverage")
        run_tests "coverage" "tests/" "All Tests with Coverage Report"
        ;;
    "fast")
        echo "🚀 Running fast tests only (excluding slow tests)..."
        pytest tests/ -m "not slow" --tb=short -v
        ;;
    "model")
        echo "🤖 Running ML model tests only..."
        pytest tests/ -m "model" --tb=short -v
        ;;
    "api")
        echo "🌐 Running API tests only..."
        pytest tests/ -m "api" --tb=short -v
        ;;
    "all")
        echo "🔄 Running complete test suite..."
        run_tests "all" "tests/" "Complete Test Suite"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Available test types:"
        echo "  unit        - Domain logic tests (no dependencies)"
        echo "  integration - Adapter tests (with dependencies)"
        echo "  e2e         - End-to-end pipeline tests"
        echo "  coverage    - All tests with coverage report"
        echo "  fast        - Exclude slow tests"
        echo "  model       - ML model tests only"
        echo "  api         - API endpoint tests only"
        echo "  all         - Complete test suite (default)"
        echo "  help        - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 unit"
        echo "  $0 coverage"
        echo "  $0 fast"
        exit 0
        ;;
    *)
        echo "❌ Unknown test type: $1"
        echo "Use '$0 help' to see available options"
        exit 1
        ;;
esac

# Generate test summary
echo ""
echo "📊 Test Execution Complete!"
echo "================================"
echo "📁 Reports generated in: tests/reports/"
echo "   - HTML Coverage: tests/reports/coverage_html/index.html"
echo "   - XML Coverage: tests/reports/coverage.xml"
echo "   - JUnit XML: tests/reports/junit.xml"
echo "   - HTML Report: tests/reports/report.html"
echo ""
echo "🔍 To view coverage report:"
echo "   source activate ds_env && python -m webbrowser tests/reports/coverage_html/index.html"
echo ""
echo "✅ Testing complete! Check reports for detailed results."
