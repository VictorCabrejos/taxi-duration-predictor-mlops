#!/usr/bin/env python3
"""
Ultimate MLOps Project Structure Generator

This script creates a comprehensive, production-ready project structure
for Machine Learning and GenAI applications following industry best practices.

Usage:
    python create_mlops_structure.py --project-name my-project --level beginner
    python create_mlops_structure.py --project-name my-project --level intermediate
    python create_mlops_structure.py --project-name my-project --level advanced
    python create_mlops_structure.py --project-name my-project --level expert

Author: Created for MLOps Education & Professional Development
"""

import os
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set
import json


class MLOpsStructureGenerator:
    def __init__(self, project_name: str, level: str = "beginner"):
        self.project_name = project_name
        self.level = level
        self.project_path = Path(project_name)

        # Define folder structures by experience level
        self.folder_structures = {
            "beginner": self._get_beginner_structure(),
            "intermediate": self._get_intermediate_structure(),
            "advanced": self._get_advanced_structure(),
            "expert": self._get_expert_structure(),
        }

    def _get_beginner_structure(self) -> Dict[str, List[str]]:
        """Basic structure for ML beginners"""
        return {
            f"{self.project_name}/": [
                "domain/",
                "adapters/",
                "api/",
                "pipeline/",
                "monitoring/",
                "config.py",
                "__init__.py",
                "README.md",
            ],
            "tests/": [
                "unit/",
                "integration/",
                "e2e/",
                "fixtures/",
                "reports/",
                "conftest.py",
            ],
            "educational_resources/": [
                "notebooks/",
                "scripts/",
                "presentation_materials/",
                "README.md",
            ],
            "data/": ["raw/", "processed/", "models/", "README.md"],
            "deployment/": [
                "docker-compose.yml",
                "Dockerfile.api",
                "Dockerfile.dashboard",
                ".env.docker",
                "start-docker.sh",
                "start-docker.bat",
            ],
            "DOCS/": ["project_development/", "testing/", "README.md"],
            ".github/": [
                "workflows/",
                "ISSUE_TEMPLATE/",
                "PULL_REQUEST_TEMPLATE.md",
                "copilot-instructions.md",
            ],
        }

    def _get_intermediate_structure(self) -> Dict[str, List[str]]:
        """Intermediate structure adding modern frontend and cloud basics"""
        structure = self._get_beginner_structure()

        # Add frontend development
        structure.update(
            {
                "frontend/": [
                    "web/src/components/",
                    "web/src/pages/",
                    "web/src/hooks/",
                    "web/src/services/",
                    "web/src/stores/",
                    "web/src/utils/",
                    "web/src/styles/",
                    "web/public/",
                    "web/package.json",
                    "web/tailwind.config.js",
                    "web/next.config.js",
                    "web/.env.local",
                    "shared/components/",
                    "shared/types/",
                    "shared/constants/",
                    "README.md",
                ],
                "infrastructure/": [
                    "terraform/environments/dev/",
                    "terraform/environments/staging/",
                    "terraform/environments/prod/",
                    "terraform/modules/database/",
                    "terraform/modules/compute/",
                    "terraform/modules/storage/",
                    "terraform/variables.tf",
                    "terraform/main.tf",
                    "kubernetes/namespaces/",
                    "kubernetes/deployments/",
                    "kubernetes/services/",
                    "scripts/",
                    "README.md",
                ],
                "environments/": [
                    "local/.env",
                    "local/docker-compose.yml",
                    "local/README.md",
                    "development/.env.dev",
                    "development/configs/",
                    "staging/.env.staging",
                    "staging/configs/",
                    "production/.env.prod",
                    "production/configs/",
                    "shared/base_configs/",
                    "shared/policies/",
                ],
                "mlops/": [
                    "feature_store/definitions/",
                    "feature_store/transformations/",
                    "feature_store/serving/",
                    "model_registry/versioning/",
                    "model_registry/staging/",
                    "drift_detection/data_drift/",
                    "drift_detection/model_drift/",
                    "drift_detection/alerts/",
                    "README.md",
                ],
                "api_contracts/": [
                    "openapi/v1/",
                    "openapi/shared/",
                    "schemas/request_schemas/",
                    "schemas/response_schemas/",
                    "examples/curl_examples/",
                    "examples/python_examples/",
                    "versioning/migration_guides/",
                    "testing/contract_tests/",
                ],
            }
        )

        return structure

    def _get_advanced_structure(self) -> Dict[str, List[str]]:
        """Advanced structure for production-ready systems"""
        structure = self._get_intermediate_structure()

        # Add advanced MLOps and data engineering
        structure.update(
            {
                "data_engineering/": [
                    "pipelines/ingestion/apis/",
                    "pipelines/ingestion/databases/",
                    "pipelines/ingestion/files/",
                    "pipelines/ingestion/streaming/",
                    "pipelines/transformation/cleaning/",
                    "pipelines/transformation/feature_engineering/",
                    "pipelines/validation/schema_validation/",
                    "pipelines/validation/quality_checks/",
                    "streaming/kafka/",
                    "streaming/kinesis/",
                    "batch/spark/",
                    "batch/airflow/",
                    "batch/dbt/",
                    "quality/profiling/",
                    "quality/monitoring/",
                    "catalog/schemas/",
                    "catalog/lineage/",
                ],
                "observability/": [
                    "logging/application/",
                    "logging/model/",
                    "logging/data/",
                    "logging/security/",
                    "metrics/business/",
                    "metrics/technical/",
                    "metrics/model_performance/",
                    "tracing/jaeger/",
                    "tracing/opentelemetry/",
                    "alerting/rules/",
                    "alerting/channels/",
                    "dashboards/grafana/",
                    "dashboards/custom/",
                    "sli_slo/definitions/",
                    "sli_slo/monitoring/",
                ],
                "performance/": [
                    "benchmarks/model_inference/",
                    "benchmarks/api_endpoints/",
                    "benchmarks/database_queries/",
                    "load_testing/locust/",
                    "load_testing/scenarios/",
                    "profiling/cpu_profiling/",
                    "profiling/memory_profiling/",
                    "profiling/gpu_profiling/",
                    "optimization/model_optimization/",
                    "optimization/caching/",
                    "capacity_planning/predictions/",
                    "capacity_planning/scaling_policies/",
                ],
                "security/": [
                    "policies/data_protection.md",
                    "policies/access_control.md",
                    "policies/incident_response.md",
                    "secrets/vault/",
                    "secrets/aws_secrets/",
                    "secrets/k8s_secrets/",
                    "compliance/gdpr/",
                    "compliance/hipaa/",
                    "compliance/soc2/",
                    "audit/logs/",
                    "audit/reports/",
                    "certificates/",
                    "penetration_testing/",
                ],
                "integrations/": [
                    "openai/client/",
                    "openai/models/",
                    "openai/error_handling/",
                    "cloud_providers/aws/s3/",
                    "cloud_providers/aws/rds/",
                    "cloud_providers/gcp/storage/",
                    "cloud_providers/azure/blob_storage/",
                    "databases/postgresql/",
                    "databases/mongodb/",
                    "databases/redis/",
                    "analytics/google_analytics/",
                    "notifications/slack/",
                    "notifications/email/",
                    "monitoring_services/datadog/",
                ],
            }
        )

        # Enhance MLOps for advanced level
        structure["mlops/"].extend(
            [
                "ab_testing/experiments/",
                "ab_testing/metrics/",
                "ab_testing/analysis/",
                "retraining/triggers/",
                "retraining/pipelines/",
                "retraining/validation/",
                "serving/batch/",
                "serving/real_time/",
                "serving/streaming/",
                "governance/lineage/",
                "governance/documentation/",
            ]
        )

        return structure

    def _get_expert_structure(self) -> Dict[str, List[str]]:
        """Complete structure for enterprise-grade systems"""
        structure = self._get_advanced_structure()

        # Add enterprise features
        structure.update(
            {
                "backup/": [
                    "strategies/data_backup.md",
                    "strategies/model_backup.md",
                    "strategies/infrastructure_backup.md",
                    "scripts/database_backup.py",
                    "scripts/model_backup.py",
                    "scripts/schedule_backups.sh",
                    "recovery/procedures/",
                    "recovery/runbooks/",
                    "recovery/automation/",
                    "testing/restore_tests/",
                    "testing/dr_drills/",
                    "monitoring/backup_health/",
                    "monitoring/alerts/",
                ],
                ".gitflow/": [
                    "config",
                    "hooks/pre-commit",
                    "hooks/pre-push",
                    "hooks/post-merge",
                    "workflows/feature_workflow.md",
                    "workflows/release_workflow.md",
                    "workflows/hotfix_workflow.md",
                    "templates/commit_template.txt",
                    "templates/pr_template.md",
                ],
            }
        )

        # Add mobile frontend
        structure["frontend/"].extend(
            [
                "mobile/src/",
                "mobile/android/",
                "mobile/ios/",
                "mobile/package.json",
                "design_system/tokens/",
                "design_system/components/",
                "design_system/documentation/",
            ]
        )

        # Add advanced CI/CD
        structure[".github/"].extend(
            [
                "workflows/ci.yml",
                "workflows/cd.yml",
                "workflows/security-scan.yml",
                "workflows/performance-test.yml",
                "CODEOWNERS",
            ]
        )

        return structure

    def create_structure(self) -> None:
        """Create the complete project structure"""
        print(
            f"🚀 Creating {self.level} MLOps project structure for '{self.project_name}'..."
        )

        if self.project_path.exists():
            response = input(
                f"⚠️  Project '{self.project_name}' already exists. Overwrite? (y/N): "
            )
            if response.lower() != "y":
                print("❌ Cancelled.")
                return

        # Create project root
        self.project_path.mkdir(exist_ok=True)
        os.chdir(self.project_path)

        # Get structure for this level
        structure = self.folder_structures[self.level]

        # Create all folders and files
        total_items = sum(len(items) for items in structure.values())
        created_count = 0

        for folder, items in structure.items():
            self._create_folder_structure(folder, items)
            created_count += len(items)
            self._print_progress(created_count, total_items)

        # Create essential files
        self._create_essential_files()

        print(f"\n✅ Successfully created {self.level} MLOps project structure!")
        print(f"📁 Project location: {self.project_path.absolute()}")
        print(f"📊 Created {created_count} folders/files")

        # Print next steps
        self._print_next_steps()

    def _create_folder_structure(self, base_folder: str, items: List[str]) -> None:
        """Create folder structure with items"""
        base_path = Path(base_folder)
        base_path.mkdir(parents=True, exist_ok=True)

        for item in items:
            item_path = base_path / item

            if item.endswith("/"):
                # It's a directory
                item_path.mkdir(parents=True, exist_ok=True)
                # Create empty __init__.py for Python packages
                if any(
                    item.startswith(pkg) for pkg in [f"{self.project_name}/", "tests/"]
                ):
                    (item_path / "__init__.py").touch()
            else:
                # It's a file
                item_path.parent.mkdir(parents=True, exist_ok=True)
                if not item_path.exists():
                    item_path.touch()

    def _create_essential_files(self) -> None:
        """Create essential configuration files"""

        # Root level files
        essential_files = {
            "README.md": self._get_readme_content(),
            "requirements.txt": self._get_requirements_content(),
            ".gitignore": self._get_gitignore_content(),
            "pytest.ini": self._get_pytest_config(),
            "main.py": self._get_main_py_content(),
        }

        # Add level-specific files
        if self.level in ["intermediate", "advanced", "expert"]:
            essential_files.update(
                {
                    "run_tests.bat": self._get_run_tests_bat(),
                    "run_tests.sh": self._get_run_tests_sh(),
                }
            )

        for filename, content in essential_files.items():
            file_path = Path(filename)
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    def _get_readme_content(self) -> str:
        return f"""# {self.project_name.replace('_', ' ').title()}

MLOps project following hexagonal architecture and modern best practices.

## 🏗️ Project Structure ({self.level.title()} Level)

This project follows the **Ultimate MLOps Project Structure** designed for {self.level}-level development.

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\\Scripts\\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run Tests**:
   ```bash
   pytest tests/  # or ./run_tests.sh
   ```

3. **Start Application**:
   ```bash
   python main.py
   ```

## 📚 Documentation

- See `educational_resources/` for learning materials
- See `DOCS/` for detailed documentation
- See `.github/copilot-instructions.md` for AI development setup

## 🎯 Learning Path

This is a **{self.level}-level** project structure. To advance:

- **Beginner → Intermediate**: Add frontend/ and infrastructure/
- **Intermediate → Advanced**: Add data_engineering/ and observability/
- **Advanced → Expert**: Add complete enterprise features

## 🤝 Contributing

Follow the Git Flow methodology:
1. Create feature branch: `git flow feature start feature-name`
2. Develop and test
3. Create pull request
4. Merge to develop → staging → main

---

*Generated by Ultimate MLOps Structure Generator*
"""

    def _get_requirements_content(self) -> str:
        base_requirements = """# Core ML Requirements
pandas>=2.0.0
numpy>=1.21.0
scikit-learn>=1.3.0
mlflow>=2.7.0

# API Framework
fastapi>=0.104.0
uvicorn>=0.24.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0

# Development
python-dotenv>=1.0.0
pydantic>=2.4.0
"""

        if self.level in ["intermediate", "advanced", "expert"]:
            base_requirements += """
# Advanced MLOps
dvc>=3.0.0
great-expectations>=0.17.0

# Cloud & Infrastructure
boto3>=1.29.0
psycopg2-binary>=2.9.0

# Monitoring
prometheus-client>=0.18.0
structlog>=23.1.0
"""

        if self.level in ["advanced", "expert"]:
            base_requirements += """
# Data Engineering
apache-airflow>=2.7.0
kafka-python>=2.0.0

# Performance
locust>=2.17.0
memory-profiler>=0.61.0

# Security
cryptography>=41.0.0
"""

        return base_requirements

    def _get_gitignore_content(self) -> str:
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Environment Variables
.env
.env.local
.env.*.local

# Data
data/raw/
data/processed/
*.csv
*.parquet
*.h5

# Models
models/
mlruns/
*.pkl
*.joblib

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# Cloud
.terraform/
*.tfstate
*.tfstate.*

# Docker
docker-compose.override.yml

# Node.js (if using frontend)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.next/
"""

    def _get_pytest_config(self) -> str:
        return """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests for domain logic (no external dependencies)
    integration: Integration tests with external systems
    e2e: End-to-end tests for complete workflows
    slow: Tests that take longer to execute
    model: Tests specifically for ML model functionality
    api: Tests for API endpoints

addopts =
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov={project_name}
    --cov-report=html:tests/reports/coverage_html
    --cov-report=xml:tests/reports/coverage.xml
    --cov-report=term-missing
""".format(
            project_name=self.project_name
        )

    def _get_main_py_content(self) -> str:
        return f'''"""
{self.project_name.replace('_', ' ').title()} - Main Application Entry Point

This is the main entry point for the MLOps application following
hexagonal architecture principles.
"""

from {self.project_name}.config import Config
from {self.project_name}.api.controller import create_app

def main():
    """Main application entry point"""
    config = Config()
    app = create_app(config)

    print(f"🚀 Starting {{config.APP_NAME}} v{{config.APP_VERSION}}")
    print(f"📊 MLOps Level: {self.level.title()}")
    print(f"🌍 Environment: {{config.ENVIRONMENT}}")

    # Start the application based on configuration
    if config.ENVIRONMENT == "development":
        import uvicorn
        uvicorn.run(
            app,
            host=config.HOST,
            port=config.PORT,
            reload=True
        )
    else:
        import uvicorn
        uvicorn.run(
            app,
            host=config.HOST,
            port=config.PORT
        )

if __name__ == "__main__":
    main()
'''

    def _get_run_tests_bat(self) -> str:
        return """@echo off
REM Test Execution Script for Windows
echo 🧪 MLOps Testing Suite
echo ================================

REM Parse command line arguments
set test_type=%1
if "%test_type%"=="" set test_type=all

echo Running %test_type% tests...

if "%test_type%"=="unit" (
    pytest tests/unit/ -m "unit" --tb=short -v
) else if "%test_type%"=="integration" (
    pytest tests/integration/ -m "integration" --tb=short -v
) else if "%test_type%"=="e2e" (
    pytest tests/e2e/ -m "e2e" --tb=short -v
) else if "%test_type%"=="coverage" (
    pytest tests/ --cov --cov-report=html:tests/reports/coverage_html --tb=short -v
) else if "%test_type%"=="all" (
    pytest tests/ --tb=short -v
) else (
    echo Usage: run_tests.bat [unit^|integration^|e2e^|coverage^|all]
)
"""

    def _get_run_tests_sh(self) -> str:
        return """#!/bin/bash
# Test Execution Script for Unix/Linux/Mac
echo "🧪 MLOps Testing Suite"
echo "================================"

test_type=${1:-all}
echo "Running $test_type tests..."

case "$test_type" in
    "unit")
        pytest tests/unit/ -m "unit" --tb=short -v
        ;;
    "integration")
        pytest tests/integration/ -m "integration" --tb=short -v
        ;;
    "e2e")
        pytest tests/e2e/ -m "e2e" --tb=short -v
        ;;
    "coverage")
        pytest tests/ --cov --cov-report=html:tests/reports/coverage_html --tb=short -v
        ;;
    "all")
        pytest tests/ --tb=short -v
        ;;
    *)
        echo "Usage: ./run_tests.sh [unit|integration|e2e|coverage|all]"
        ;;
esac
"""

    def _print_progress(self, current: int, total: int) -> None:
        """Print progress bar"""
        percent = int((current / total) * 100)
        bar_length = 30
        filled = int((current / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(
            f"\r📁 Progress: [{bar}] {percent}% ({current}/{total})", end="", flush=True
        )

    def _print_next_steps(self) -> None:
        """Print next steps for the user"""
        print(f"\n\n🎯 Next Steps:")
        print(f"1. cd {self.project_name}")
        print(f"2. python -m venv venv")
        print(f"3. source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
        print(f"4. pip install -r requirements.txt")
        print(f"5. pytest tests/  # Run tests")
        print(f"6. python main.py  # Start application")

        print(f"\n📚 Educational Resources:")
        print(f"- See educational_resources/Ultimate_MLOps_Project_Structure_Guide.md")
        print(f"- See DOCS/ for detailed documentation")
        print(f"- See .github/copilot-instructions.md for AI development")

        if self.level == "beginner":
            print(f"\n🚀 Ready to advance? Run:")
            print(
                f"python create_mlops_structure.py --project-name {self.project_name}-v2 --level intermediate"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Generate Ultimate MLOps Project Structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_mlops_structure.py --project-name taxi-predictor --level beginner
  python create_mlops_structure.py --project-name fraud-detector --level intermediate
  python create_mlops_structure.py --project-name recommendation-engine --level advanced
  python create_mlops_structure.py --project-name ai-platform --level expert

Levels:
  beginner     - Core ML structure (domain, API, tests, deployment)
  intermediate - Add frontend, infrastructure, environments, basic MLOps
  advanced     - Add data engineering, observability, performance, security
  expert       - Complete enterprise structure with all features
        """,
    )

    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project (e.g., taxi-predictor)",
    )

    parser.add_argument(
        "--level",
        choices=["beginner", "intermediate", "advanced", "expert"],
        default="beginner",
        help="Project complexity level (default: beginner)",
    )

    parser.add_argument(
        "--list-structure",
        action="store_true",
        help="List the folder structure for specified level without creating",
    )

    args = parser.parse_args()

    generator = MLOpsStructureGenerator(args.project_name, args.level)

    if args.list_structure:
        print(f"📁 {args.level.title()} MLOps Project Structure:")
        structure = generator.folder_structures[args.level]
        for folder, items in structure.items():
            print(f"\n{folder}")
            for item in items:
                print(f"  ├── {item}")
    else:
        generator.create_structure()


if __name__ == "__main__":
    main()
"""

Auto-generated MLOps project structure script.
Created for educational purposes and professional development.
"""
