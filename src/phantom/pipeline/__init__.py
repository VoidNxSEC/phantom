"""
Phantom Pipeline - DAG execution, classification, and sanitization.

Classes:
    DAGPipeline - Directed acyclic graph task execution
    FileClassifier - File type classification
    DataSanitizer - Sensitive data sanitization
"""


def __getattr__(name):
    if name == "DAGPipeline":
        from phantom.pipeline.phantom_dag import PhantomPipeline as DAGPipeline

        return DAGPipeline
    if name == "PhantomPipeline":
        from phantom.pipeline.phantom_dag import PhantomPipeline

        return PhantomPipeline
    if name == "FileClassifier":
        from phantom.pipeline.phantom_dag import ClassificationEngine as FileClassifier

        return FileClassifier
    if name == "DataSanitizer":
        from phantom.pipeline.phantom_dag import SanitizationEngine as DataSanitizer

        return DataSanitizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DAGPipeline",
    "PhantomPipeline",
    "FileClassifier",
    "DataSanitizer",
]
