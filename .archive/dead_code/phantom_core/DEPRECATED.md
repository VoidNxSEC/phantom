# DEPRECATED

This directory (`phantom_core/`) is **deprecated** and will be removed in a future release.

## Migration Guide

All functionality from `phantom_core` has been migrated to the new modular structure under `src/phantom/`.

### Old vs New Imports

```python
# OLD (deprecated)
from phantom_core.phantom_classifier import PhantomClassifier

# NEW (use this instead)
from phantom.core import CortexProcessor
from phantom.pipeline import FileClassifier, DAGPipeline
```

### Equivalent Classes

| Deprecated (`phantom_core`)   | New Location (`phantom.*`)           |
|-------------------------------|--------------------------------------|
| `PhantomClassifier`           | `phantom.core.CortexProcessor`       |
| Classification logic          | `phantom.pipeline.FileClassifier`    |
| Pipeline orchestration        | `phantom.pipeline.DAGPipeline`       |

## Timeline

- **v2.0.0**: Deprecated, still available
- **v3.0.0**: Will be removed entirely

Please update your imports to use the new `phantom.*` modules.
