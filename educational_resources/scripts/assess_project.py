#!/usr/bin/env python3
"""
MLOps Project Assessment Tool

Analyzes existing ML projects against modern MLOps standards and provides
upgrade recommendations for portfolio optimization.

Usage:
    python assess_project.py --project-path ./my-old-project
    python assess_project.py --project-path ./my-old-project --detailed
    python assess_project.py --workspace-path ./MLOps-Portfolio --assess-all

Author: Created for MLOps Portfolio Management
"""

import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class ProjectTier(Enum):
    SHOWCASE = "showcase"  # Interview-ready, production-grade
    DEVELOPMENT = "development"  # Good foundation, needs structure
    LEARNING = "learning"  # Educational value, archive
    OBSOLETE = "obsolete"  # Single notebook, incomplete


@dataclass
class AssessmentResult:
    project_name: str
    current_tier: ProjectTier
    recommended_tier: ProjectTier
    score: int  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    missing_components: List[str]
    upgrade_effort: str  # Low, Medium, High
    business_value: str  # Low, Medium, High
    learning_value: str  # Low, Medium, High


class MLOpsProjectAssessor:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.name

        # Assessment criteria weights
        self.weights = {
            "architecture": 25,  # Hexagonal, DDD, clean structure
            "testing": 20,  # Unit, integration, e2e tests
            "mlops": 20,  # MLflow, monitoring, pipelines
            "deployment": 15,  # Docker, CI/CD, scalability
            "documentation": 10,  # README, API docs, guides
            "code_quality": 10,  # Clean code, error handling
        }

    def assess_project(self) -> AssessmentResult:
        """Perform comprehensive project assessment"""

        scores = {
            "architecture": self._assess_architecture(),
            "testing": self._assess_testing(),
            "mlops": self._assess_mlops(),
            "deployment": self._assess_deployment(),
            "documentation": self._assess_documentation(),
            "code_quality": self._assess_code_quality(),
        }

        # Calculate weighted score
        total_score = sum(
            score * self.weights[category] / 100 for category, score in scores.items()
        )

        # Determine tiers and recommendations
        current_tier = self._determine_current_tier(scores)
        recommended_tier = self._determine_recommended_tier(scores, total_score)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(scores)
        weaknesses = self._identify_weaknesses(scores)
        missing_components = self._identify_missing_components()

        # Estimate efforts
        upgrade_effort = self._estimate_upgrade_effort(current_tier, recommended_tier)
        business_value = self._estimate_business_value()
        learning_value = self._estimate_learning_value()

        return AssessmentResult(
            project_name=self.project_name,
            current_tier=current_tier,
            recommended_tier=recommended_tier,
            score=int(total_score),
            strengths=strengths,
            weaknesses=weaknesses,
            missing_components=missing_components,
            upgrade_effort=upgrade_effort,
            business_value=business_value,
            learning_value=learning_value,
        )

    def _assess_architecture(self) -> int:
        """Assess architectural quality (0-100)"""
        score = 0

        # Check for hexagonal architecture
        if (self.project_path / "domain").exists():
            score += 30
        if (self.project_path / "adapters").exists():
            score += 20
        if (self.project_path / "api").exists():
            score += 15

        # Check for clean separation
        python_files = list(self.project_path.rglob("*.py"))
        if len(python_files) > 5:  # Has substantial code
            score += 10

        # Check for config management
        if any(
            (self.project_path / f).exists()
            for f in ["config.py", ".env", "settings.py"]
        ):
            score += 10

        # Check for dependency injection patterns
        if self._has_dependency_injection():
            score += 15

        return min(score, 100)

    def _assess_testing(self) -> int:
        """Assess testing coverage and quality (0-100)"""
        score = 0

        # Check for test directory
        test_dir = self.project_path / "tests"
        if test_dir.exists():
            score += 30

            # Check test structure
            if (test_dir / "unit").exists():
                score += 20
            if (test_dir / "integration").exists():
                score += 20
            if (test_dir / "e2e").exists():
                score += 15

            # Check for test configuration
            if (self.project_path / "pytest.ini").exists():
                score += 10
            if (self.project_path / "conftest.py").exists() or (
                test_dir / "conftest.py"
            ).exists():
                score += 5

        # Check for test files
        test_files = list(self.project_path.rglob("test_*.py"))
        if test_files:
            score = max(score, 20)  # At least some tests exist

        return min(score, 100)

    def _assess_mlops(self) -> int:
        """Assess MLOps practices and tooling (0-100)"""
        score = 0

        # Check for MLflow integration
        if self._has_mlflow():
            score += 30

        # Check for model artifacts management
        if any((self.project_path / d).exists() for d in ["models", "mlruns", "data"]):
            score += 20

        # Check for training pipeline
        if (self.project_path / "pipeline").exists():
            score += 25

        # Check for monitoring
        if (self.project_path / "monitoring").exists():
            score += 15

        # Check for requirements management
        if (self.project_path / "requirements.txt").exists():
            score += 10

        return min(score, 100)

    def _assess_deployment(self) -> int:
        """Assess deployment readiness (0-100)"""
        score = 0

        # Check for containerization
        if (self.project_path / "Dockerfile").exists():
            score += 30
        if (self.project_path / "docker-compose.yml").exists():
            score += 20

        # Check for deployment configs
        deployment_dir = self.project_path / "deployment"
        if deployment_dir.exists():
            score += 25

        # Check for CI/CD
        github_dir = self.project_path / ".github"
        if github_dir.exists() and (github_dir / "workflows").exists():
            score += 15

        # Check for main entry point
        if (self.project_path / "main.py").exists() or (
            self.project_path / "app.py"
        ).exists():
            score += 10

        return min(score, 100)

    def _assess_documentation(self) -> int:
        """Assess documentation quality (0-100)"""
        score = 0

        # Check for README
        readme_files = list(self.project_path.glob("README*"))
        if readme_files:
            readme_content = readme_files[0].read_text(
                encoding="utf-8", errors="ignore"
            )
            if len(readme_content) > 500:  # Substantial README
                score += 40
            elif len(readme_content) > 100:  # Basic README
                score += 20

        # Check for documentation directory
        if (self.project_path / "docs").exists() or (
            self.project_path / "DOCS"
        ).exists():
            score += 25

        # Check for API documentation
        if self._has_api_docs():
            score += 20

        # Check for educational resources
        if (self.project_path / "educational_resources").exists():
            score += 15

        return min(score, 100)

    def _assess_code_quality(self) -> int:
        """Assess code quality and organization (0-100)"""
        score = 0

        # Check for proper Python package structure
        python_files = list(self.project_path.rglob("*.py"))
        if python_files:
            score += 20

            # Check for __init__.py files
            init_files = list(self.project_path.rglob("__init__.py"))
            if init_files:
                score += 15

        # Check for configuration files
        config_files = [".gitignore", "requirements.txt", "setup.py", "pyproject.toml"]
        existing_configs = sum(
            1 for f in config_files if (self.project_path / f).exists()
        )
        score += existing_configs * 10

        # Check for error handling patterns
        if self._has_error_handling():
            score += 15

        # Check for logging
        if self._has_logging():
            score += 10

        return min(score, 100)

    def _determine_current_tier(self, scores: Dict[str, int]) -> ProjectTier:
        """Determine current project tier based on scores"""
        avg_score = sum(scores.values()) / len(scores)

        # Check for minimal viability
        python_files = list(self.project_path.rglob("*.py"))
        jupyter_files = list(self.project_path.rglob("*.ipynb"))

        if len(python_files) <= 1 and len(jupyter_files) <= 1:
            return ProjectTier.OBSOLETE

        if avg_score >= 70:
            return ProjectTier.SHOWCASE
        elif avg_score >= 40:
            return ProjectTier.DEVELOPMENT
        else:
            return ProjectTier.LEARNING

    def _determine_recommended_tier(
        self, scores: Dict[str, int], total_score: int
    ) -> ProjectTier:
        """Determine recommended tier based on potential"""

        # Consider business value and technical foundation
        has_ml_model = self._has_ml_model()
        has_api = scores["deployment"] > 30
        has_good_architecture = scores["architecture"] > 50

        if has_ml_model and (has_api or has_good_architecture) and total_score > 30:
            return ProjectTier.SHOWCASE
        elif has_ml_model and total_score > 20:
            return ProjectTier.DEVELOPMENT
        else:
            return ProjectTier.LEARNING

    def _identify_strengths(self, scores: Dict[str, int]) -> List[str]:
        """Identify project strengths"""
        strengths = []

        if scores["architecture"] >= 60:
            strengths.append("Strong architectural foundation")
        if scores["testing"] >= 60:
            strengths.append("Comprehensive testing suite")
        if scores["mlops"] >= 60:
            strengths.append("Good MLOps practices")
        if scores["deployment"] >= 60:
            strengths.append("Deployment-ready")
        if scores["documentation"] >= 60:
            strengths.append("Well-documented")
        if scores["code_quality"] >= 60:
            strengths.append("High code quality")

        if self._has_ml_model():
            strengths.append("Contains working ML model")
        if self._has_real_data():
            strengths.append("Uses realistic datasets")
        if self._has_business_value():
            strengths.append("Clear business application")

        return strengths

    def _identify_weaknesses(self, scores: Dict[str, int]) -> List[str]:
        """Identify project weaknesses"""
        weaknesses = []

        if scores["architecture"] < 40:
            weaknesses.append("Lacks proper architectural structure")
        if scores["testing"] < 30:
            weaknesses.append("Missing comprehensive testing")
        if scores["mlops"] < 40:
            weaknesses.append("Limited MLOps integration")
        if scores["deployment"] < 30:
            weaknesses.append("Not deployment-ready")
        if scores["documentation"] < 40:
            weaknesses.append("Insufficient documentation")
        if scores["code_quality"] < 40:
            weaknesses.append("Code quality needs improvement")

        return weaknesses

    def _identify_missing_components(self) -> List[str]:
        """Identify missing MLOps components"""
        missing = []

        required_folders = {
            "domain": "Domain entities and business logic",
            "adapters": "Infrastructure adapters",
            "api": "API endpoints and controllers",
            "tests": "Testing framework",
            "deployment": "Deployment configurations",
        }

        for folder, description in required_folders.items():
            if not (self.project_path / folder).exists():
                missing.append(f"{description} ({folder}/)")

        required_files = {
            "requirements.txt": "Dependency management",
            "Dockerfile": "Containerization",
            "README.md": "Project documentation",
            "pytest.ini": "Testing configuration",
        }

        for file, description in required_files.items():
            if not (self.project_path / file).exists():
                missing.append(f"{description} ({file})")

        return missing

    def _estimate_upgrade_effort(
        self, current: ProjectTier, recommended: ProjectTier
    ) -> str:
        """Estimate effort required for upgrade"""
        tier_values = {
            ProjectTier.OBSOLETE: 0,
            ProjectTier.LEARNING: 1,
            ProjectTier.DEVELOPMENT: 2,
            ProjectTier.SHOWCASE: 3,
        }

        gap = tier_values[recommended] - tier_values[current]

        if gap <= 0:
            return "None"
        elif gap == 1:
            return "Low"
        elif gap == 2:
            return "Medium"
        else:
            return "High"

    def _estimate_business_value(self) -> str:
        """Estimate business/interview value"""
        if self._has_ml_model() and self._has_api() and self._has_real_data():
            return "High"
        elif self._has_ml_model() and (self._has_api() or self._has_real_data()):
            return "Medium"
        else:
            return "Low"

    def _estimate_learning_value(self) -> str:
        """Estimate educational value"""
        if self._has_educational_resources() or self._has_notebooks():
            return "High"
        elif self._has_ml_model():
            return "Medium"
        else:
            return "Low"

    # Helper methods for detecting project features
    def _has_dependency_injection(self) -> bool:
        """Check for dependency injection patterns"""
        # Look for constructor injection or factory patterns
        python_files = list(self.project_path.rglob("*.py"))
        for file in python_files[:10]:  # Check first 10 files
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(
                    pattern in content
                    for pattern in ["__init__(self,", "inject", "container", "factory"]
                ):
                    return True
            except:
                continue
        return False

    def _has_mlflow(self) -> bool:
        """Check for MLflow integration"""
        return (self.project_path / "mlruns").exists() or any(
            "mlflow" in f.read_text(encoding="utf-8", errors="ignore")
            for f in self.project_path.rglob("*.py")
            if f.is_file()
        )

    def _has_api_docs(self) -> bool:
        """Check for API documentation"""
        python_files = list(self.project_path.rglob("*.py"))
        for file in python_files:
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(
                    pattern in content
                    for pattern in ["FastAPI", "@app.", "swagger", "openapi"]
                ):
                    return True
            except:
                continue
        return False

    def _has_error_handling(self) -> bool:
        """Check for error handling patterns"""
        python_files = list(self.project_path.rglob("*.py"))
        for file in python_files[:5]:  # Check first 5 files
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(
                    pattern in content
                    for pattern in ["try:", "except", "raise", "Exception"]
                ):
                    return True
            except:
                continue
        return False

    def _has_logging(self) -> bool:
        """Check for logging implementation"""
        python_files = list(self.project_path.rglob("*.py"))
        for file in python_files[:5]:  # Check first 5 files
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(
                    pattern in content
                    for pattern in ["import logging", "logger", "log."]
                ):
                    return True
            except:
                continue
        return False

    def _has_ml_model(self) -> bool:
        """Check for ML model implementation"""
        # Check for model files
        model_extensions = [".pkl", ".joblib", ".h5", ".pb", ".onnx"]
        for ext in model_extensions:
            if list(self.project_path.rglob(f"*{ext}")):
                return True

        # Check for ML libraries in code
        python_files = list(self.project_path.rglob("*.py"))
        ml_libraries = ["sklearn", "tensorflow", "torch", "xgboost", "lightgbm"]

        for file in python_files:
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(lib in content for lib in ml_libraries):
                    return True
            except:
                continue

        return False

    def _has_api(self) -> bool:
        """Check for API implementation"""
        python_files = list(self.project_path.rglob("*.py"))
        for file in python_files:
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                if any(
                    pattern in content
                    for pattern in ["FastAPI", "flask", "@app.", "uvicorn"]
                ):
                    return True
            except:
                continue
        return False

    def _has_real_data(self) -> bool:
        """Check for realistic datasets"""
        data_files = list(self.project_path.rglob("*.csv")) + list(
            self.project_path.rglob("*.json")
        )
        return len(data_files) > 0

    def _has_business_value(self) -> bool:
        """Check for clear business application"""
        # Look for business-relevant naming or documentation
        business_keywords = [
            "prediction",
            "recommendation",
            "fraud",
            "customer",
            "sales",
            "revenue",
            "optimization",
            "classification",
            "regression",
        ]

        # Check project name
        if any(keyword in self.project_name.lower() for keyword in business_keywords):
            return True

        # Check README content
        readme_files = list(self.project_path.glob("README*"))
        if readme_files:
            try:
                content = (
                    readme_files[0].read_text(encoding="utf-8", errors="ignore").lower()
                )
                if any(keyword in content for keyword in business_keywords):
                    return True
            except:
                pass

        return False

    def _has_educational_resources(self) -> bool:
        """Check for educational materials"""
        return (self.project_path / "educational_resources").exists()

    def _has_notebooks(self) -> bool:
        """Check for Jupyter notebooks"""
        return len(list(self.project_path.rglob("*.ipynb"))) > 0


class PortfolioAnalyzer:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def analyze_all_projects(self) -> List[AssessmentResult]:
        """Analyze all projects in workspace"""
        results = []

        # Find all project directories
        project_dirs = [
            d
            for d in self.workspace_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        for project_dir in project_dirs:
            try:
                assessor = MLOpsProjectAssessor(str(project_dir))
                result = assessor.assess_project()
                results.append(result)
            except Exception as e:
                print(f"⚠️  Error assessing {project_dir.name}: {e}")

        return results

    def generate_portfolio_report(self, results: List[AssessmentResult]) -> str:
        """Generate comprehensive portfolio report"""

        # Sort by score (highest first)
        results.sort(key=lambda x: x.score, reverse=True)

        # Count by tier
        tier_counts = {}
        for tier in ProjectTier:
            tier_counts[tier] = len([r for r in results if r.recommended_tier == tier])

        report = f"""
# 📊 MLOps Portfolio Assessment Report

## 🎯 Executive Summary

**Total Projects Analyzed**: {len(results)}
**Average Portfolio Score**: {sum(r.score for r in results) / len(results):.1f}/100

### 📈 Recommended Portfolio Structure:
- 🏆 **Showcase Projects**: {tier_counts[ProjectTier.SHOWCASE]} (Interview-ready)
- 🚧 **Development Projects**: {tier_counts[ProjectTier.DEVELOPMENT]} (Active development)
- 📚 **Learning Projects**: {tier_counts[ProjectTier.LEARNING]} (Educational/archive)
- 🗑️ **Obsolete Projects**: {tier_counts[ProjectTier.OBSOLETE]} (Consider removing)

---

## 📋 Individual Project Assessments

"""

        for result in results:
            tier_emoji = {
                ProjectTier.SHOWCASE: "🏆",
                ProjectTier.DEVELOPMENT: "🚧",
                ProjectTier.LEARNING: "📚",
                ProjectTier.OBSOLETE: "🗑️",
            }

            report += f"""
### {tier_emoji[result.recommended_tier]} {result.project_name}

**Score**: {result.score}/100 | **Current**: {result.current_tier.value} | **Recommended**: {result.recommended_tier.value}
**Upgrade Effort**: {result.upgrade_effort} | **Business Value**: {result.business_value} | **Learning Value**: {result.learning_value}

**Strengths**:
{chr(10).join('- ' + s for s in result.strengths)}

**Missing Components**:
{chr(10).join('- ' + s for s in result.missing_components[:5])}  # Show top 5

---
"""

        # Add recommendations
        report += f"""
## 🚀 Portfolio Optimization Recommendations

### Immediate Actions (Next 2 weeks):
1. **Archive/Remove** {tier_counts[ProjectTier.OBSOLETE]} obsolete projects
2. **Upgrade** top {min(3, tier_counts[ProjectTier.DEVELOPMENT])} development projects to showcase level
3. **Create** portfolio README highlighting your best work

### Development Focus (Next month):
1. **Refactor** {tier_counts[ProjectTier.DEVELOPMENT]} development projects with hexagonal architecture
2. **Add testing** to projects missing test coverage
3. **Document** business value and technical decisions

### Long-term Strategy:
1. **Maintain** 3-5 showcase projects for different ML domains
2. **Archive** learning projects with clear educational value
3. **Continuous improvement** of existing showcase projects

---

*Generated by MLOps Portfolio Assessment Tool*
"""

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Assess MLOps projects for portfolio optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--project-path", help="Path to individual project to assess")

    parser.add_argument(
        "--workspace-path", help="Path to workspace containing multiple projects"
    )

    parser.add_argument(
        "--assess-all", action="store_true", help="Assess all projects in workspace"
    )

    parser.add_argument(
        "--detailed", action="store_true", help="Show detailed assessment breakdown"
    )

    parser.add_argument("--output", help="Output file for assessment report")

    args = parser.parse_args()

    if args.project_path:
        # Assess single project
        assessor = MLOpsProjectAssessor(args.project_path)
        result = assessor.assess_project()

        print(f"🔍 Assessment Results for '{result.project_name}':")
        print(f"📊 Score: {result.score}/100")
        print(f"🎯 Current Tier: {result.current_tier.value}")
        print(f"🚀 Recommended Tier: {result.recommended_tier.value}")
        print(f"⚡ Upgrade Effort: {result.upgrade_effort}")

        if result.strengths:
            print(f"\n✅ Strengths:")
            for strength in result.strengths:
                print(f"  - {strength}")

        if result.missing_components:
            print(f"\n❌ Missing Components:")
            for component in result.missing_components[:10]:  # Show top 10
                print(f"  - {component}")

        if args.detailed:
            print(f"\n📋 Detailed Assessment:")
            print(f"  Business Value: {result.business_value}")
            print(f"  Learning Value: {result.learning_value}")
            print(f"  Weaknesses: {', '.join(result.weaknesses[:3])}")

    elif args.workspace_path:
        # Assess all projects in workspace
        analyzer = PortfolioAnalyzer(args.workspace_path)
        results = analyzer.analyze_all_projects()

        if args.assess_all:
            report = analyzer.generate_portfolio_report(results)

            if args.output:
                Path(args.output).write_text(report)
                print(f"📄 Portfolio report saved to: {args.output}")
            else:
                print(report)
        else:
            # Quick summary
            print(f"📊 Portfolio Summary ({len(results)} projects):")
            for result in sorted(results, key=lambda x: x.score, reverse=True):
                tier_emoji = {
                    "showcase": "🏆",
                    "development": "🚧",
                    "learning": "📚",
                    "obsolete": "🗑️",
                }
                print(
                    f"  {tier_emoji.get(result.recommended_tier.value, '📁')} {result.project_name} - {result.score}/100"
                )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
