"""
Phantom Pipeline - DAG execution, classification, and sanitization.

Classes:
    DAGPipeline - Directed acyclic graph task execution
    FileClassifier - File type classification
    DataSanitizer - Sensitive data sanitization
"""


def __getattr__(name):
    if name == "DAGPipeline":
        from phantom.pipeline.dag import DAGPipeline

        return DAGPipeline
    if name == "FileClassifier":
        from phantom.pipeline.classifier import FileClassifier

        return FileClassifier
    if name == "DataSanitizer":
        from phantom.pipeline.sanitizer import DataSanitizer

        return DataSanitizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DAGPipeline",
    "FileClassifier",
    "DataSanitizer",
]
