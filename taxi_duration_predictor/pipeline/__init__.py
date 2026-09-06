"""
Pipeline Package
Training and prediction pipelines
"""

__all__ = ["TrainingPipeline", "PredictionPipeline"]


def __getattr__(name):
    if name == "TrainingPipeline":
        from .train import TrainingPipeline

        return TrainingPipeline
    if name == "PredictionPipeline":
        from .predict import PredictionPipeline

        return PredictionPipeline
    raise AttributeError(name)
