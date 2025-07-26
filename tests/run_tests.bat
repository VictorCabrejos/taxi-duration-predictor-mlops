@echo off
REM Test Execution Script for Windows
REM Script para ejecutar tests en Windows con conda

REM Go to project root
cd /d "%~dp0\.."

echo 🧪 MLOps Project Testing Suite
echo ================================

REM Activate conda environment
echo 📋 Activating conda environment...
call conda activate ds_env

REM Create reports directory
if not exist "tests\reports" mkdir tests\reports

REM Parse command line arguments
set test_type=%1
if "%test_type%"=="" set test_type=all

echo.
echo 🔬 Running %test_type% tests...
echo ----------------------------------------

if "%test_type%"=="unit" (
    pytest tests/unit/ -m "unit" --tb=short -v
) else if "%test_type%"=="integration" (
    pytest tests/integration/ -m "integration" --tb=short -v
) else if "%test_type%"=="e2e" (
    pytest tests/e2e/ -m "e2e" --tb=short -v
) else if "%test_type%"=="coverage" (
    pytest tests/ --cov=taxi_duration_predictor --cov-report=html:tests/reports/coverage_html --cov-report=term-missing -v
) else if "%test_type%"=="fast" (
    pytest tests/ -m "not slow" --tb=short -v
) else if "%test_type%"=="all" (
    pytest tests/ --tb=short -v
) else if "%test_type%"=="help" (
    echo Usage: run_tests.bat [test_type]
    echo.
    echo Available test types:
    echo   unit        - Domain logic tests (no dependencies)
    echo   integration - Adapter tests (with dependencies)
    echo   e2e         - End-to-end pipeline tests
    echo   coverage    - All tests with coverage report
    echo   fast        - Exclude slow tests
    echo   all         - Complete test suite (default)
    echo   help        - Show this help
    goto end
) else (
    echo ❌ Unknown test type: %test_type%
    echo Use 'run_tests.bat help' to see available options
    goto end
)

echo.
echo 📊 Test Execution Complete!
echo ================================
echo 📁 Reports generated in: tests\reports\
echo    - HTML Coverage: tests\reports\coverage_html\index.html
echo    - XML Coverage: tests\reports\coverage.xml
echo    - JUnit XML: tests\reports\junit.xml
echo    - HTML Report: tests\reports\report.html
echo.
echo ✅ Testing complete! Check reports for detailed results.

:end
