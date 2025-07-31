"""
Pipeline Package
Training and prediction pipelines
"""

from .train import TrainingPipeline
from .predict import PredictionPipeline

__all__ = ["TrainingPipeline", "PredictionPipeline"]
